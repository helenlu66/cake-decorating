import os
import warnings
import logging
from ActionAgent import ActionAgent
from ConfigUtil import get_args, load_experiment_config
from DialogueUtility import DialogueUtility
from LLMNLUHelper import LLMNLUHelper
from preferenceModel import PreferenceModel
from prompts import *


logging.basicConfig(filename='DialogueActions.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
# Filter out ALSA warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ALSA")
##logger = logging.get##logger('DialogueActionAgent')

class DialogueActionAgent:
    def __init__(self, task_setup:dict, user_name='user', api_key=os.environ['OPENAI_API_KEY'] if 'OPENAI_API_KEY' in os.environ else None) -> None:
        self.dialogue_util = DialogueUtility(user_name=user_name, api_key=api_key)
        self.nlu = LLMNLUHelper(prompts_setup=prompts_setup, task_setup=task_setup, api_key=api_key)
        self.user_name = user_name

        self.user_preference = PreferenceModel(user_name=user_name)
        self.user_preference.set_up_model(task_setup=task_setup)
        self.objects_name_var_mapping = {
            'first candle':'candle0',
            'second candle':'candle1',
            'third candle':'candle2'
        }
        
        self.actionAgent = ActionAgent(server_host=exp_config['server_host'], server_port=exp_config['server_port'])
        self.actions = {
            'left': (-1, 0),
            'right': (+1, 0),
            'up': (0, +1),
            'down': (0, -1)
        }
        if task_setup['num_candles'] > 3:
            for idx in range(4, task_setup['num_candles']):
                self.objects_name_var_mapping[f'candle{idx}'] = f'{idx}th candle'

    def ask_and_listen(self, robot_question:str, wait_len:float=0) -> str:
        """prompt the human for answer and listen

        Args:
            robot_question (str): the question to ask the human
        """
        self.dialogue_util.text_to_speech(robot_question)
        human_speech_filepath = self.dialogue_util.record_human_speech(wait_len=wait_len)
        human_speech_text = self.dialogue_util.speech_to_text(human_speech_filepath)
        return human_speech_text
    
    def greet(self):
        self.dialogue_util.text_to_speech(f'Hi, {self.user_name}!')
    
    def get_constraints_for_obj(self, obj_name:str, greet:bool=False) -> list:
        """get the spatial constraints for the placement of the object

        Args:
            obj_name (str): the name of the object
        """
        if greet:
            robot_question = f'Hi, {self.user_name}. Let us decorate a cake. Where should I place the {obj_name}?'
        else:
            robot_question = f'Where should I place the {obj_name}?'
        ##logger.info('robot said: ' + robot_question)
        print('robot said: ' + robot_question)
        # wait the default amount of time
        human_speech_text = self.ask_and_listen(robot_question=robot_question)
        ##logger.info('human said: ' + human_speech_text)
        print('human said: ' + human_speech_text)
        can_extract = self.nlu.classify(robot_question=robot_question, human_answer=human_speech_text)
        
        while not can_extract:
            # can't extract spatial constraint from human answer, redirect them back to the question
            robot_question = self.nlu.redirect(robot_question=robot_question, human_answer=human_speech_text)
            ##logger.info('robot said: ' + robot_question)
            print('robot said: ' + robot_question)
            human_speech_text = self.ask_and_listen(robot_question=robot_question)
            ##logger.info('human said: ' + human_speech_text)
            print('human said: ' + human_speech_text)
            can_extract = self.nlu.classify(robot_question=robot_question, human_answer=human_speech_text)
        constraints_list = self.nlu.extract_constraints(robot_question=robot_question, human_answer=human_speech_text)
        
        return constraints_list
    
    def update_user_preference_constraints(self, constraints:list[str]):
        """Update the user's preference model by adding the constraints

        Args:
            constraints (list[str]): list of constraints    

        Returns:
            bool: whether constraints are updated 
        """
    
        try:
            for constraint in constraints:
                self.user_preference.record_and_apply_constraint(constraint)
            return True
        except:
            print('Something went wrong when updating the user preference model')
            return False
    
    
    def get_initial_proposed_loc(self, obj_name:str) -> tuple:
        """get a proposed location for the object"""
        obj_var = self.objects_name_var_mapping[obj_name]
        idx = obj_var[-1]
        loc = self.user_preference.propose(candle_num=idx)
        return loc
    
    
    def pickUp(self, obj_name:str):
        pass

    def moveTo(self, loc:tuple):
        pass

    def release(self):
        pass

    def local_adjusment(self, obj_name:str, loc:tuple) -> tuple:
        """locally adjust the object's placement through user instructions

        Args:
            obj_name (str): the name of the object whose location is being adjusted
        """
        self.actionAgent.pickUp(obj=self.objects_name_var_mapping[obj_name])
        
        self.actionAgent.moveToBoardCoords(coords=loc)
        robot_question = "Is this a good location? (You can say either yes, no, or move to the left, to the right, move up or move down)"
        ##logger.info('robot said: ' + robot_question)
        human_speech_text = self.ask_and_listen(robot_question=robot_question, wait_len=5)
        ##logger.info('human said: ' + human_speech_text)
        print('robot said: ' + robot_question)
        print('human said: ' + human_speech_text)
        related = self.nlu.classify(robot_question=robot_question, human_answer=human_speech_text)
        
        # keep clarifying until human starts saying something related to the question
        while not related:
            #robot_question = 'Is this a good location? You can say either yes, or move to the left, to the right, move up or move down.'
            #logger.info('robot said: ' + robot_question)
            robot_question = self.nlu.redirect(robot_question=robot_question, human_answer=human_speech_text)
            human_speech_text = self.ask_and_listen(robot_question=robot_question, wait_len=6)
            #logger.info('human said: ' + human_speech_text)
            print('robot said: ' + robot_question)
            print('human said: ' + human_speech_text)
            related = self.nlu.classify(robot_question=robot_question, human_answer=human_speech_text)
        
        # keep adjusting until the human is satisfied with the location
        human_intent = self.nlu.classify_human_accept(robot_question=robot_question, human_answer=human_speech_text)
        while not human_intent == 'accept':
            if human_intent != 'no accept':
                # need to move as well as speak
                # adjust the location
                loc = tuple([sum(i) for i in zip(loc, self.actions[human_intent])])
                # move the object to new_loc
                dir_map = {
                    'up':'forward',
                    'down':'backward',
                    'left':'left',
                    'right':'right'
                }
                self.actionAgent.moveToRelative(dir=dir_map[human_intent])
                robot_question = "Is this a good location?"
                human_speech_text = self.ask_and_listen(robot_question=robot_question, wait_len=5)
                print('robot said: ' + robot_question)
                print('human said: ' + human_speech_text)
                human_intent = self.nlu.classify_human_accept(robot_question=robot_question, human_answer=human_speech_text)
                #logger.info('human said: ' + human_speech_text)
            else:
                # clarify the things the human can say
                robot_question = "Is this a good location (You can say either yes, no, or move to the left, to the right, move up or move down)?" 
                #logger.info('robot said: ' + robot_question)
                human_speech_text = self.ask_and_listen(robot_question=robot_question, wait_len=5)
                print('robot said: ' + robot_question)
                print('human said: ' + human_speech_text)
                human_intent = self.nlu.classify_human_accept(robot_question=robot_question, human_answer=human_speech_text)
                #logger.info('human said: ' + human_speech_text)
        
        # human accepted, put down object and record loc
        self.release()
        obj_var = self.objects_name_var_mapping[obj_name]
        obj_idx = obj_var[-1]
        self.actionAgent.putDown()
        self.user_preference.record_loc(candle_num=obj_idx, loc=loc)
        return loc

    def main_dialogue(self):
        """carry out the main dialogue with the user
        """
        ##logger.info(msg=f'dialogue with {self.user_name}')
        for i, name in enumerate(self.objects_name_var_mapping):
            if i == 0:
            # skips the first 2 
            #if i <= 1:
                # continue
                # a hack to greet the user properly
                constraints_list = self.get_constraints_for_obj(obj_name=name, greet=True)
            else:
                constraints_list = self.get_constraints_for_obj(obj_name=name)
            ##logger.info(msg=constraints_list)
            print('constraints extracted: ', constraints_list)
            self.update_user_preference_constraints(constraints=constraints_list)
            loc = self.get_initial_proposed_loc(obj_name=name)
            print(f'initial loc for {name}, {loc}')
            final_loc = self.local_adjusment(obj_name=name, loc=loc)
            ##logger.info(msg=f'loc for {name}: {final_loc}')
            print(f'loc for {name}', final_loc)
        

    def easier_dialogue(self):
        """carry out an easier dialogue with the user (without local adjustments)
        """
        ##logger.info(msg=f'dialogue with {self.user_name}')
        for i, name in enumerate(self.objects_name_var_mapping.keys()):
            if i == 0:
                # a hack to greet the user properly
                constraints_list = self.get_constraints_for_obj(obj_name=name, greet=True)
            else:
                constraints_list = self.get_constraints_for_obj(obj_name=name)
            
            ##logger.info(msg=constraints_list)
            print(constraints_list)
            self.update_user_preference_constraints(constraints=constraints_list)
            loc = self.get_initial_proposed_loc(obj_name=name)
            self.actionAgent.pickAndPlaceObjAtBoardCoords(obj=self.objects_name_var_mapping[name], coords=loc)
            ##logger.info(msg=f'loc for {name}: {loc}')
            print(f'loc for {name}', loc)

# can run the following for testing
if __name__=="__main__":
    exp_config = load_experiment_config('experiment_config.yaml')
    args = get_args()
    agent = DialogueActionAgent(task_setup=exp_config['task_setup'], user_name=exp_config['user_name'], api_key=args.api_key)
    agent.main_dialogue()
    agent.user_preference.save_to_dill()

   



    