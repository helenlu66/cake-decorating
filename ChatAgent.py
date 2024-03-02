import logging
import itertools
import random
import re
import time
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
logging.basicConfig(filename='chat_agent.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ChatAgent:
    def __init__(self) -> None:
        self.exp_config = load_experiment_config('experiment_config.yaml')
        self.response_enabled = self.exp_config['exp_condition'] != 'base'
        self.max_retries = 5
        self.messages = [SystemMessage(content=classification_instructions)]
        # if self.exp_config['exp_condition'] != 'reasonable':
        #     self.messages = [SystemMessage(content=classification_instructions)]
        # else:
        #     self.messages = [SystemMessage(content=task_instructions)]
    

        if self.response_enabled:
            self.messages.append(AIMessage(content=f"Hello {self.exp_config['user_name']}, let's decorate a cake together. What would you like me to do first?"))

        self.chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.suggestion_chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.action_chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.explain_chat = ChatOpenAI(model="gpt-4", temperature=0)
        self.suggestion_messages = [SystemMessage(content=suggestion_prompt)]
        
        self.random_suggestion_rephraser = LLMChain(
            prompt=rephrase_prompt,
            llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
        )
        self.diarc = DIARCInterface(server_host='localhost', server_port='8080')
        self.should_proactively_suggest_next_action = True
        self.log_file = open(f"experiment_log/{self.exp_config['user_name']}_{self.exp_config['exp_condition']}_prompts.log", "a")
        


    def process_human_input(self, human_message:str):
        """generate a response to the human message and append it to messages"""
        self.messages.append(HumanMessage(content=human_message))
        # introspect on beliefs about the environment for better reasonable suggestions
        self.update_prompt_with_beliefs()
        # extract important information from the chat messages according to instructions in the system prompt
        print(self.messages)
        ai_message:AIMessage = self.chat.invoke(self.messages)
        # Log the human message and AI message

        print('classification: ', ai_message)
        # process the extracted information into a response to the human
        self.messages.append(ai_message)
        ai_message:AIMessage | str = self.post_process_ai_message(ai_message, human_message)
        if not self.response_enabled:
            return ai_message.content
        
        print(ai_message)
        self.log_file.write(str(self.messages) + "\n")
        self.log_file.flush()
        return ai_message.content
    
    
    def update_prompt_with_beliefs(self) -> ChatPromptTemplate:
        """update the system messages with current beliefs"""
        observable_objects_desc = []
        observable_objects_pred = self.introspect('object(X, physobj)')
        # translate predicates into NL descriptions for LLM
        for pred in observable_objects_pred:
            observable_object_binding = self.get_X_var_binding(filledin_predicate=pred)
            observable_object_desc = self.translate_pred(pred='object(X, physobj)', bindings=observable_object_binding)
            observable_objects_desc.append(observable_object_desc)
        
        beliefs_pred = self.introspect('canpickup(X)')
        beliefs_desc = []
        # translate beliefs predicates into NL descriptions for LLM
        for pred in beliefs_pred:
            belief_binding = self.get_X_var_binding(filledin_predicate=pred)
            belief_desc = self.translate_pred(pred='canpickup(X)', bindings=belief_binding)
            beliefs_desc.append(belief_desc)
    
        beliefs_pred = self.introspect('at(X, Y)')
        for pred in beliefs_pred:
            belief_binding = self.get_X_Y_var_binding(filledin_predicate=pred)
            belief_desc = self.translate_pred(pred='at(X, Y)', bindings=belief_binding)
            beliefs_desc.append(belief_desc)
        
        beliefs_pred = self.introspect('on(X, cake)')
        for pred in beliefs_pred:
            belief_binding = self.get_X_var_binding(filledin_predicate=pred)
            belief_desc = self.translate_pred(pred='on(X, cake)', bindings=belief_binding)
            beliefs_desc.append(belief_desc)
        
        beliefs_pred = self.introspect('freecakeloc(X)')
        for pred in beliefs_pred:
            belief_binding = self.get_X_var_binding(filledin_predicate=pred)
            belief_desc = self.translate_pred(pred='freecakeloc(X)', bindings=belief_binding)
            beliefs_desc.append(belief_desc)

        # fill in the prompt with observable objects and beliefs
        self.messages[0].content=self.messages[0].content.format(
            observable_objects=str(observable_objects_desc), 
            beliefs=str(beliefs_desc),
            # action="{action}",
            # action_parameters="{action parameters}",
            description_of_action="{description_of_action}",
            reason_for_selecting_the_action="{reason_for_selecting_the_action}",
            ask_what_the_human_user_thinks_of_this_idea="{ask_what_the_human_user_thinks_of_this_idea}",
            inform_the_user_that_you_cannot_respond_to_this="{inform_the_user_that_you_cannot_respond_to_this}",
            redirect_the_user_back_to_task="{redirect_the_user_back_to_task}"
        )
        self.suggestion_messages[0].content = self.messages[0].content.format(
            observable_objects=str(observable_objects_desc), 
            beliefs=str(beliefs_desc),
            # action="{action}",
            # action_parameters="{action parameters}",
            description_of_action="{description_of_action}",
            reason_for_selecting_the_action="{reason_for_selecting_the_action}",
            ask_what_the_human_user_thinks_of_this_idea="{ask_what_the_human_user_thinks_of_this_idea}",
            inform_the_user_that_you_cannot_respond_to_this="{inform_the_user_that_you_cannot_respond_to_this}",
            redirect_the_user_back_to_task="{redirect_the_user_back_to_task}"
        )
        print(self.suggestion_messages[0].content)


    def get_X_var_binding(self, filledin_predicate):
        # Updated regex to match any string after X, separated by a comma
        match = re.search(r'\(([^,)]*)', filledin_predicate)

        if match:
            value_of_x = match.group(1)
            return {'X': value_of_x}
        else:
            print("No X match found")
            return {'X':filledin_predicate}

    
    def get_X_Y_var_binding(self, filledin_predicate):
        # Regular expression to extract X and Y
        match = re.search(r"\w+\s*\(\s*(.*?)\s*,\s*(.*?)\s*\)", filledin_predicate)

        if match:
            x, y = match.groups()
            result = {"X": x, "Y": y}
            return result
        else:
            print("No X, Y match found")
            return {"X": filledin_predicate, "Y": filledin_predicate}

    def translate_pred(self, pred:str, bindings:dict):
        pred_translations = {
            'object(X, physobj)':"there is a {X}.",
            'canpickup(X)':"you have the capability of picking up {X}.",
            'at(X, Y)':"{X} is at location {Y}.",
            'on(X, cake)':"{X} is on the cake.",
            'freecakeloc(X)':"the location {X} on the cake is not occupied."
        }
        translation = pred_translations[pred]
        filledin_translation = translation.format(**bindings)
        return filledin_translation
        

    def classify_ai_message(self, ai_message:AIMessage) -> str:
        """classify the ai message as one of `action`, `suggestion`, `alternative suggestion` or `other`

        Args:
            ai_message (AIMessage): the ai's message
        """
        parsed_message = ai_message.content.split('\n')
        if parsed_message[0].lower() not in ('action', 'suggestion', 'alternative suggestion', 'other'):
            return 'incorrect format'
        return parsed_message[0].lower().strip()

    def post_process_ai_message(self, ai_message:AIMessage, human_message:HumanMessage):
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
        #parsed_message = ai_message.content.split('\n')
        classification = self.classify_ai_message(ai_message=ai_message)
        if classification == 'action':
            self.messages.append(SystemMessage(content=action_prompt))
            action_msg = self.action_chat.invoke(self.messages)
            print(action_msg)
            parsed_message = action_msg.content.split("\n")
            action = parsed_message[0]
            action_args = parsed_message[1]
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
                #self.messages.append(SystemMessage(content="You have successfully completed the action. Ask what action the human would like you to take next."))
                ai_message = AIMessage(content="I have successfully completed the action. What action would you like me to take next?")
                self.messages.append(ai_message)
                # the next human input is expected to be a command, the ai should proactively suggest an action after carrying out the command
                self.should_proactively_suggest_next_action = True
                return ai_message
            # action status is failure, ask to try another action
            else:
                if not self.response_enabled: # robot not allowed to talk. Return a system status message
                    return AIMessage(content="The robot has failed to complete the action")
                # self.messages.append(SystemMessage(
                #         content="You didn't successfully complete the action. Ask the human to double-check their request or try some other action."
                #     ))
                ai_message = AIMessage(content="I didn't successfully complete the action. Could you double-check your request or try some other action?")
                self.messages.append(ai_message)
                self.should_proactively_suggest_next_action = True
                return ai_message
        elif classification in {'suggestion', 'alternative suggestion', 'alternativesuggestion'}: #this happens if the user asks for a suggestion
            # and the robot needs to respond with a suggestion instead of proactive giving one
            self.should_proactively_suggest_next_action = False
            if self.exp_config['exp_condition'].lower() != 'base':
                ai_message = self.generate_suggestion(following_an_action=False)
            if not self.response_enabled: #should not be giving suggestions
                time.sleep(2)
                return AIMessage(content="The robot cannot respond to your request")
            
            return AIMessage(content=self.remove_first_line(ai_message.content))
        elif classification=='explain': # human is asking for more explanation to a suggestion
            if not self.response_enabled: #should not be giving explanations
                time.sleep(2)
                return AIMessage(content="The robot cannot respond to your request")
            ai_message = self.explain()
            self.messages.append(ai_message)
            return ai_message
        elif classification=='other': # human is off course, need to redirect
            if not self.response_enabled: #should not be giving responses
                return AIMessage(content="The robot cannot respond to your request")
            ai_message = self.redirect(human_message=human_message)
            self.messages.append(ai_message)
            return ai_message
        else: # message is a direct response
            if not self.response_enabled: #should not be giving suggestions
                return AIMessage(content="The robot cannot respond to your request")
            self.messages.append(ai_message)
            return ai_message
        

    def explain(self) -> AIMessage:
        """human is asking for additional explanation. Explain the reasoning behind the last suggestion."""
        
        if self.exp_config['exp_condition'] == 'random':
            random_explanation = random.choice(longer_random_reasons)
            ai_message = AIMessage(content=random_explanation)
        else:
            self.messages.append(SystemMessage(content=explain_prompt))
            ai_message = self.explain_chat.invoke(self.messages)
        return AIMessage(content=ai_message.content + " What would you like me to do next?")
    
    def generate_suggestion(self, following_an_action=False):
        """suggest the next step to take based on the kind of condition. Either `random` or `reasonable`.
        """
        if self.exp_config['exp_condition'] == 'random':
            # randomly suggest a valid next move
            ai_message = self.generate_random_suggestion(following_an_action=following_an_action)
            self.should_proactively_suggest_next_action = False
            self.messages.append(ai_message)
            return ai_message
        
        # otherwise make sure to generate a reasonable suggestion
        if following_an_action:
            self.messages.append(SystemMessage(content=minimal_suggestion_prompt_following_action))
            ai_message = self.suggestion_chat.invoke(self.messages)
            i = 0
            while self.classify_ai_message(ai_message=ai_message) not in {'suggestion', 'alternative suggestion'}:
                self.messages.append(ai_message)
                self.messages.append(SystemMessage(content=minimal_resuggest_prompt_following_action))
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
            self.messages.append(SystemMessage(content=minimal_suggestion_prompt))
            ai_message = self.chat.invoke(self.messages)
            i = 0
            while self.classify_ai_message(ai_message=ai_message) not in {'suggestion', 'alternative suggestion'} and i < self.max_retries:
                self.messages.append(ai_message)
                self.messages.append(SystemMessage(content=minimal_resuggest_prompt))
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
        free_cake_locs_beliefs = self.introspect(predicate='freecakeloc(X)')
        free_cake_locs = set(self.get_X_var_binding(x)['X'] for x in free_cake_locs_beliefs)
        canpickup_items = set(object_names[self.get_X_var_binding(x)['X']] for x in canpickup_items_beliefs)
        
        suggestions = []
        for decorative_item, free_cake_loc in list(itertools.product(canpickup_items, free_cake_locs)):
            # suggest putting a random item at a random location on the cake
            random_reason = random.choice(random_reasons)
            random_suggestion = """Let's move the {decorative_item} to location {free_cake_loc}. {random_reason}. What do you think of this idea?""".format(
                decorative_item=decorative_item,
                free_cake_loc=free_cake_loc,
                random_reason=random_reason,
                #ask_what_the_human_user_thinks_of_this_idea="{ask what the human user thinks of this idea}"
            )
            suggestions.append(random_suggestion)
        
        on_cake_decorative_items_beliefs = self.introspect(predicate='on(X, cake)')
        on_cake_decorative_items = set(object_names[self.get_X_var_binding(x)['X']] for x in on_cake_decorative_items_beliefs)
        on_cake_canpickup_decorative_items = canpickup_items.intersection(on_cake_decorative_items)
        print("currently on cake: ", on_cake_canpickup_decorative_items)
        for decorative_item in on_cake_canpickup_decorative_items:
            # suggest taking a random item off the cake
            random_reason = random.choice(random_reasons)
            random_suggestion = """Let's take the {decorative_item} off the cake. {random_reason}. What do you think of this idea?""".format(
                decorative_item=decorative_item,
                random_reason=random_reason,
                #ask_what_the_human_user_thinks_of_this_idea="{ask what the human user thinks of this idea}"
            )
            suggestions.append(random_suggestion)
        
        # select a suggestion out of all possible random suggestions
        suggestion = random.choice(suggestions)
        if following_an_action:
            suggestion = "I have completed the action. " + suggestion
        #suggestion = self.random_suggestion_rephraser.invoke({'sentences':suggestion})['text']
        ai_message = AIMessage(content=suggestion)
        #self.messages.append(ai_message)
        # self.messages.append(SystemMessage(content="rephrase your last suggestion according to the human's message and make it human readable."))
        # print('raw suggestion': suggestion)
        # ai_message = self.chat.invoke(self.messages)
        return ai_message
        
    def redirect(self, human_message:HumanMessage):
        """redirect the user back to the task"""
        # ai_message:AIMessage = self.chat.invoke([human_message, SystemMessage(content=
        #     redirect_prompt
        # )])
        return AIMessage(content="I'm sorry, but as a robot arm, I cannot respond to that. I can either put things on the cake or take things off.")

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
    
    def __del__(self):
        # Close the log file when the ChatAgent object is destroyed
        if self.log_file:
            self.log_file.close()



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