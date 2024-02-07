import itertools
import random
import re
from langchain.agents.openai_assistant import OpenAIAssistantRunnable
from prompts import task_instructions
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from ConfigUtil import load_experiment_config
from prompts import *
from DIARCInterface import DIARCInterface
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


class ChatAgent:
    def __init__(self) -> None:
        self.exp_config = load_experiment_config('experiment_config.yaml')
        self.response_enabled = self.exp_config['exp_condition'] != 'base'
        self.max_retries = 5
        self.messages = [SystemMessage(content=task_instructions)]
    

        if self.response_enabled:
            self.messages.append(AIMessage(content=f"Hello {self.exp_config['user_name']}, let's decorate a cake together. What would you like me to do first?"))

        self.chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.suggestion_chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.suggestion_messages = [SystemMessage(content=suggestion_prompt)]
        
        self.random_suggestion_rephraser = LLMChain(
            prompt=rephrase_prompt,
            llm=ChatOpenAI(model='gpt-4')
        )
        self.diarc = DIARCInterface(server_host='localhost', server_port='8080')
        self.should_proactively_suggest_next_action = True

    def process_human_input(self, human_message:str):
        """generate a response to the human message and append it to messages"""
        self.messages.append(HumanMessage(content=human_message))
        # introspect on beliefs about the environment
        self.update_prompt_with_beliefs()
        # extract important information from the chat messages according to instructions in the system prompt
        ai_message:AIMessage = self.chat.invoke(self.messages)
        print(ai_message)
        # process the extracted information into a response to the human
        self.messages.append(ai_message)
        ai_message:AIMessage | str = self.post_process_ai_message(ai_message)
        if not self.response_enabled:
            return ai_message.content
        
        print(ai_message)
        return ai_message.content
    
    def update_prompt_with_beliefs(self) -> ChatPromptTemplate:
        """update the system messages with current beliefs"""
        observable_objects = self.introspect('object(X, physobj)')
        beliefs = self.introspect('canpickup(X)')
        beliefs += self.introspect('at(X, Y)')
        beliefs += self.introspect('on(X, cake)')
        self.messages[0].content=self.messages[0].content.format(
            observable_objects=str(observable_objects), 
            beliefs=str(beliefs),
            # action="{action}",
            # action_parameters="{action parameters}",
            description_of_action="{description_of_action}",
            reason_for_selecting_the_action="{reason_for_selecting_the_action}",
            ask_what_the_human_user_thinks_of_this_idea="{ask_what_the_human_user_thinks_of_this_idea}"
        )
        self.suggestion_messages[0].content = self.messages[0].content.format(
            observable_objects=str(observable_objects), 
            beliefs=str(beliefs),
            # action="{action}",
            # action_parameters="{action parameters}",
            description_of_action="{description_of_action}",
            reason_for_selecting_the_action="{reason_for_selecting_the_action}",
            ask_what_the_human_user_thinks_of_this_idea="{ask_what_the_human_user_thinks_of_this_idea}"
        )

    
    def classify_ai_message(self, ai_message:AIMessage) -> str:
        """classify the ai message as one of `action`, `suggestion` or `other`

        Args:
            ai_message (AIMessage): the ai's message
        """
        parsed_message = ai_message.content.split('\n')
        if parsed_message[0].lower() not in ('action', 'suggestion'):
            return 'other'
        return parsed_message[0]

    def post_process_ai_message(self, ai_message:AIMessage):
        """need processing to get action status, generate proper response, and then append ai_message
        if action status is success, generate a suggestion for next step
        if action status is failure, say that there's a problem
        if ai_message is a suggestion, can directly append
        ai_message format for action:
        ```
        action
        {action}
        {action parameter(s)}
        ```

        ai_message format for suggestion:
        ```
        suggestion
        Let's {description of action}
        {reason for selecting the action}
        {ask what the human user thinks of this idea}
        ```
        Args:
            ai_message (AIMessage): the raw ai_message

        Returns:
            AIMessage: response to be sent to the human
        """
        if self.exp_config['exp_condition'] == 'base':
            self.should_proactively_suggest_next_action = False
        parsed_message = ai_message.content.split('\n')
        if parsed_message[0].lower() == 'action':
            action = parsed_message[1]
            action_args = parsed_message[2]
            action_success = self.act(action, action_args)
            # if action status is success, generate a suggestion for the next step
            print("action status: ", action_success)
            if action_success and self.should_proactively_suggest_next_action:
                ai_message = self.generate_suggestion(following_an_action=True)
                self.should_proactively_suggest_next_action = False
                return ai_message
            # action status is success, ask the human what they like to do next
            elif action_success and not self.should_proactively_suggest_next_action:
                if not self.response_enabled: # robot not allowed to talk. Return a system status message
                    return AIMessage(content="The robot has successfully completed the action")
                self.messages.append(SystemMessage(content="You have successfully completed the action. Ask what action the human would like you to take next."))
                ai_message = self.chat.invoke(self.messages)
                self.messages.append(ai_message)
                # the next human input is expected to be a command, the ai should proactively suggest an action after carrying out the command
                self.should_proactively_suggest_next_action = True
                return ai_message
            # action status is failure, ask to try another action
            else:
                if not self.response_enabled: # robot not allowed to talk. Return a system status message
                    return AIMessage(content="The robot has failed to complete the action")
                self.messages.append(SystemMessage(
                        content="You didn't successfully complete the action. Ask the human to double-check their request or try some other action."
                    ))
                ai_message = self.chat.invoke(self.messages)
                self.messages.append(ai_message)
                self.should_proactively_suggest_next_action = True
                return ai_message
        elif parsed_message[0].lower() == 'suggestion': #this happens if the user asks for suggestions
            self.should_proactively_suggest_next_action = False
            if self.exp_config['exp_condition'].lower() == 'random':
                ai_message = self.generate_random_suggestion()
                return ai_message
            if not self.response_enabled: #should not be giving suggestions
                return AIMessage(content="The robot cannot respond to your request")
            self.messages.append(ai_message)
            return AIMessage(content=self.remove_first_line(ai_message.content))
        else: # ai message is a regular response. Display it directly to the human.
            if not self.response_enabled: #should not be giving suggestions
                return AIMessage(content="The robot cannot respond to your request")
            self.messages.append(ai_message)
            return ai_message
        
    
    def generate_suggestion(self, following_an_action=False):
        """suggest the next step to take based on the kind of condition. Either `random` or `reasonable`.
        """
        if self.exp_config['exp_condition'] == 'random':
            # randomly suggest a valid next move
            ai_message = self.generate_random_suggestion(following_an_action=following_an_action)
            self.should_proactively_suggest_next_action = False
            return ai_message
        
        # otherwise make sure to generate a reasonable suggestion
        if following_an_action:
            self.messages.append(SystemMessage(content=
                    """You just completed an action. Suggest to the human user an action you can take next in the following format:
                    ```
                    suggestion
                    I have completed the action. Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
                    ```
                    Keep your reason in 1 sentence.
                    """
                ))
            ai_message = self.suggestion_chat.invoke(self.messages)
            i = 0
            while self.classify_ai_message(ai_message=ai_message) != 'suggestion':
                self.messages.append(ai_message)
                self.messages.append(SystemMessage(content=
                    """the response you generated was not in the correct format for a suggestion. Suggest an action you can take next in the following format:
                    ```
                    suggestion
                    I have completed the action. Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
                    ```
                    Keep your reason in 1 sentence. For example:
                    ```
                    suggestion
                    I have completed the action. Let's take the dark chocolate off since Jo dislikes bitter and the dark chocolate might be perceived as bitter. What do you think of this idea?
                    ```
                    """
                ))
                print("inside suggestion loop", ai_message)
                if i >= self.max_retries:
                    ai_message = self.generate_random_suggestion(following_an_action=following_an_action)
                    break
                elif i >= self.max_retries // 2:
                    ai_message:AIMessage = self.suggestion_chat(self.suggestion_messages)
                    ai_message.content = "I have completed the action. " + ai_message.content
                else:
                    ai_message:AIMessage = self.chat.invoke(self.messages)
                i += 1
        else:
            self.messages.append(SystemMessage(content=
                    """Suggest an action you can take next in the following format:
                    ```
                    suggestion
                    Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
                    ```
                    Keep your reason in 1 sentence. 
                    """
                ))
            ai_message = self.chat.invoke(self.messages)
            i = 0
            while self.classify_ai_message(ai_message=ai_message) != 'suggestion' and i < self.max_retries:
                self.messages.append(ai_message)
                self.messages.append(SystemMessage(content=
                    """the response you generated was not in the correct format for a suggestion. Suggest an action you can take next in the following format:
                    ```
                    suggestion
                    Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
                    ```
                    Keep your reason in 1 sentence. For example:
                    ```
                    suggestion
                    Let's take the dark chocolate off since Jo dislikes bitter and the dark chocolate might be perceived as bitter. What do you think of this idea?
                    ```
                    """
                ))
                print("inside suggestion loop", ai_message)
                if i >= self.max_retries:
                    ai_message = self.generate_random_suggestion(following_an_action=following_an_action)
                    break
                elif i >= self.max_retries // 2:
                    ai_message:AIMessage = self.suggestion_chat(self.suggestion_messages)
                    ai_message.content = "I have completed the action. " + ai_message.content
                else:
                    ai_message:AIMessage = self.chat.invoke(self.messages)
                i += 1
        self.messages.append(ai_message)
        ai_message = AIMessage(content=self.remove_first_line(ai_message.content))
        self.should_proactively_suggest_next_action = False 
        return ai_message

    def generate_random_suggestion(self, following_an_action=False):
        """generate a random suggestion on next action given the current beliefs about the environment"""
        canpickup_items_beliefs = self.introspect(predicate='canpickup(X)')
        free_cake_locs_beliefs = self.introspect(predicate='freecakeloc(Y)')

        def get_var_binding(filledin_predicate):
            match = re.search(r'\((.*?)\)', filledin_predicate)

            if match:
                value_of_x = match.group(1)
                return value_of_x
            else:
                print("No match found")
        
        suggestions = []
        for decorative_item, free_cake_loc in list(itertools.product(canpickup_items_beliefs, free_cake_locs_beliefs)):
            # suggest putting a random item at a random location on the cake
            random_reason = random.choice(random_reasons)
            decorative_item = get_var_binding(decorative_item)
            free_cake_loc = get_var_binding(free_cake_loc)
            random_suggestion = """Let's put the {decorative_item} at location {free_cake_loc}.{random_reason}.{ask_what_the_human_user_thinks_of_this_idea}.""".format(
                decorative_item=decorative_item,
                free_cake_loc=free_cake_loc,
                random_reason=random_reason,
                ask_what_the_human_user_thinks_of_this_idea="{ask what the human user thinks of this idea}"
            )
            suggestions.append(random_suggestion)
        
        on_cake_decorative_items_beliefs = self.introspect(predicate='on(X, cake)')
        for decorative_item in on_cake_decorative_items_beliefs:
            # suggest taking a random item off the cake
            random_reason = random.choice(random_reasons)
            decorative_item = get_var_binding(decorative_item)
            random_suggestion = """Let's take the {decorative_item} off the cake.{random_reason}.{ask_what_the_human_user_thinks_of_this_idea}.""".format(
                decorative_item=decorative_item,
                random_reason=random_reason,
                ask_what_the_human_user_thinks_of_this_idea="{ask what the human user thinks of this idea}"
            )
            suggestions.append(random_suggestion)
        
        # select a suggestion out of all possible random suggestions
        suggestion = random.choice(suggestions)
        if following_an_action:
            suggestion = "I have completed the action. " + suggestion
        suggestion = self.random_suggestion_rephraser.invoke({'sentences':suggestion})['text']
        ai_message = AIMessage(content=suggestion)
        self.messages.append(ai_message)
        return ai_message
        
    
    def remove_first_line(self, paragraph):
        lines = paragraph.split('\n')  # Split the paragraph into a list of lines
        if len(lines) > 1:  # Check if there is more than one line
            return '\n'.join(lines[1:])  # Join the lines back together, omitting the first line
        return paragraph
    

    def introspect(self, predicate:str):
        """introspect on current beliefs and fill in the task instructions with information about the enviornment"""
        beliefs = self.diarc.queryBelief(predicate=predicate)
        return beliefs
    
    def act(self, action:str, action_args:str):
        """take the action with the action arguments"""
        goal_predicate = f'{action}(self,{action_args.lower()})'
        return self.diarc.submit_DIARC_goal(goal=goal_predicate)



if __name__ == "__main__":
    chatAgent = ChatAgent()
    # observable_objects = chatAgent.introspect('object(X, physobj)')
    # beliefs = chatAgent.introspect('canpickup(X)')
    # beliefs += chatAgent.introspect('at(X, Y)')
    # beliefs += chatAgent.introspect('on(X, cake)')
    #messages = SystemMessage(content=task_instructions.format(observable_objects=str(observable_objects), beliefs=str(beliefs)))
    #messages = chatAgent.messages.partial(observable_objects=str(observable_objects), beliefs=str(beliefs))
    # new_messages = (messages + AIMessage(content=f"Hello, let's decorate a cake together. What would you like me to do first?"))
    # new_messages.format_messages(observable_objects=str(observable_objects), beliefs=str(beliefs))
    # pprint(new_messages)
    # chatAgent.messages.format_messages(observable_objects=str(observable_objects), beliefs=str(beliefs))
    chatAgent.process_human_input("can you give a suggestion?")

    # human_input = input()
    # while human_input != "done":
    #     #ai_response=chatAgent.random_suggestion_rephraser.run(sentences=human_input)
    #     ai_response = chatAgent.process_human_input(human_input)
    #     human_input = input('\n' + ai_response + '\n')