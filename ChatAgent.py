import itertools
import random
from langchain.agents.openai_assistant import OpenAIAssistantRunnable
from prompts import task_instructions
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI, OpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from ConfigUtil import load_experiment_config
from prompts import *
from DIARCInterface import DIARCInterface


class ChatAgent:
    def __init__(self) -> None:
        self.exp_config = load_experiment_config('experiment_config.yaml')
        self.response_enabled = self.exp_config['exp_condition'] != 'base'
 
        self.messages = [
            SystemMessage(
                content=task_instructions
            ),
        ]

        if self.response_enabled:
            self.messages.append(AIMessage(content=f"Hello {self.exp_config['user_name']}, let's decorate a cake together. What would you like me to do first?"))

        self.chat = ChatOpenAI(model="gpt-4")
        self.random_suggestion_rephraser = LLMChain(
            prompt=rephrase_prompt,
            llm=ChatOpenAI(model='gpt-4')
        )
        self.action_agent = DIARCInterface(server_host='localhost', server_port='8080')
        self.should_proactively_suggest_next_action = False

    def process_human_input(self, human_message:str):
        """generate a response to the human message and append it to messages"""
        self.messages.append(HumanMessage(content=human_message))
        # introspect on beliefs about the environment
        self.introspect()
        # extract important information from the chat messages according to instructions in the system prompt
        ai_message:AIMessage = self.chat(self.messages)
        # process the extracted information into a response to the human
        ai_message:AIMessage = self.post_process_ai_message(ai_message)
        self.messages.append(ai_message)
        return ai_message.content
    
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
        parsed_message = ai_message.content.split('\n')
        if parsed_message[0].lower() == 'action':
            action = parsed_message[1]
            action_args = parsed_message[2]
            action_success = self.act(action, action_args)
            # if action status is success, generate a suggestion for the next step
            if action_success and self.should_proactively_suggest_next_action:
                ai_message = self.generate_suggestion()
                self.should_proactively_suggest_next_action = False
                return ai_message
            # action status is success, ask the human what they like to do next
            elif action_success and not self.should_proactively_suggest_next_action:
                self.messages.append(SystemMessage(
                    content="You have successfully completed the action. Ask what action the human would like you to take next."
                ))
                ai_message = self.chat(self.messages)
                # the next human input is expected to be a command, the ai should proactively suggest an action after carrying out the command
                self.should_proactively_suggest_next_action = True
                return ai_message
            # action status is failure, ask to try another action
            else:
                self.messages.append(
                    SystemMessage(
                        content="You didn't successfully complete the action. Ask the human to double-check their request or try some other action."
                    )
                )
                ai_message = self.chat(self.messages)
                return ai_message
        elif parsed_message[0].lower() == 'suggestion':
            if self.exp_config['exp_condition'].lower() == 'random':
                self.generate_suggestion()
            self.should_proactively_suggest_next_action = False
            return AIMessage(content=self.remove_first_line(ai_message.content))
        else: # ai message is a regular response. Display it directly to the human.
            return ai_message
        
    
    def generate_suggestion(self):
        """suggest the next step to take based on the kind of condition. Either `random` or `reasonable`.
        """
        if self.exp_config['exp_condition'] == 'random':
            # randomly suggest a valid next move
            ai_message = self.generate_random_suggestion()
            return ai_message
        
        # otherwise make sure to generate a reasonable suggestion
        ai_message = self.chat(self.messages)
        while self.classify_ai_message(ai_message=ai_message) != 'suggestion':
            self.messages.append(SystemMessage(
                content=
                """the response you generated was not in the correct format for a suggestion. Suggest an action you can take next in the following format:
                ```
                suggestion
                Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
                ```
                Keep your reason in 1 sentence.
                """
            ))
            ai_message:AIMessage = self.chat(self.messages)
        ai_message = AIMessage(content=self.remove_first_line(ai_message.content))
        return ai_message

    def generate_random_suggestion(self):
        """generate a random suggestion on next action given the current beliefs about the environment"""
        decorative_items_beliefs = self.introspect(predicate='decorativeitem(X)')
        free_cake_locs_beliefs = self.introspect(predicate='freecakeloc(Y)')

        suggestions = []
        for decorative_item, free_cake_loc in list(itertools.product(decorative_items_beliefs, free_cake_locs_beliefs)):
            # suggest putting a random item at a random location on the cake
            random_reason = random.choice(random_reasons)
            random_suggestion = """Let's put the {decorative_item} at location {free_cake_loc}.{random_reason}.{ask the human what they think of this suggestion}.""".format(
                decorative_item=decorative_item,
                free_cake_loc=free_cake_loc,
                random_reason=random_reason
            )
            suggestions.append(random_suggestion)
        
        on_cake_decorative_items_beliefs = self.introspect(predicate='on(X, cake)')
        for decorative_item in on_cake_decorative_items_beliefs:
            # suggest taking a random item off the cake
            random_reason = random.choice(random_reasons)
            random_suggestion = """Let's take the {decorative_item} off the cake.{random_reason}.{ask the human what they think of this suggestion}.""".format(
                decorative_item=decorative_item,
                random_reason=random_reason
            )
            suggestions.append(random_suggestion)
        
        # select a suggestion out of all possible random suggestions
        suggestion = random.choice(suggestions)
        suggestion = self.random_suggestion_rephraser.run({'sentences':suggestion})['text']
        return AIMessage(content=suggestion)
        
    
    def remove_first_line(self, paragraph):
        lines = paragraph.split('\n')  # Split the paragraph into a list of lines
        if len(lines) > 1:  # Check if there is more than one line
            return '\n'.join(lines[1:])  # Join the lines back together, omitting the first line
        return paragraph
    

    def introspect(self, predicate:str):
        """introspect on current beliefs and fill in the task instructions with information about the enviornment"""
        #TODO: implement this
        pass
    
    def act(self, action:str, action_args:str):
        """take the action with the action arguments"""
        goal_predicate = f'{action}({action_args})'
        return self.action_agent.submit_DIARC_goal(goal=goal_predicate)



if __name__ == "__main__":
    chatAgent = ChatAgent()
    human_input = input()
    while human_input != "done":
        ai_response=chatAgent.random_suggestion_rephraser.run(sentences=human_input)
        # ai_response = chatAgent.process_human_input(human_input)
        human_input = input('\n' + ai_response + '\n')