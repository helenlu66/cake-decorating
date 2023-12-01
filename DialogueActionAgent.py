import os
from pprint import pprint
from pathlib import Path
from ConfigUtil import get_args, load_experiment_config
from DialogueUtility import DialogueUtility
from llmConstraintsExtraction import ConstraintExtractor
from prompts import *


class DialogueActionAgent:
    def __init__(self, task_setup:dict, user_name='user', api_key=os.environ['OPENAI_API_KEY'] if 'OPENAI_API_KEY' in os.environ else None) -> None:
        self.dialogue_util = DialogueUtility(user_name=user_name, api_key=api_key)
        self.constraint_extractor = ConstraintExtractor(prompts_setup=prompts_setup, task_setup=task_setup)
        
        
        self.objects_name_var_mapping = {
            'candle0':'first candle',
            'candle1':'second candle',
            'candle2':'third candle'
        }
        if task_setup['num_candles'] > 3:
            for idx in range(4, task_setup['num_candles']):
                self.objects_name_var_mapping[f'candle{idx}'] = f'{idx}th candle'

    def ask_and_listen(self, robot_question:str) -> str:
        """prompt the human for answer and listen

        Args:
            robot_question (str): the question to ask the human
        """
        self.dialogue_util.text_to_speech(robot_question)
        human_speech_filepath = self.dialogue_util.record_human_speech()
        human_speech_text = self.dialogue_util.speech_to_text(human_speech_filepath)
        return human_speech_text
    
    def get_constraints_for_obj(self, obj_name:str) -> list:
        """get the spatial constraints for the placement of the object

        Args:
            obj_name (str): the name of the object
        """
        robot_question = f'where should I place {obj_name}'
        human_speech_text = self.ask_and_listen(robot_question=robot_question)
        can_extract = self.constraint_extractor.classify(human_speech_text)
        
        while not can_extract:
            # redirect
            robot_question = self.constraint_extractor.redirect(robot_question=robot_question, human_answer=human_speech_text)
            human_speech_text = self.ask_and_listen(robot_question=robot_question)
            can_extract = self.constraint_extractor.classify(human_answer=human_speech_text)
        constraints_list = self.constraint_extractor.extract_constraints(robot_question=robot_question, human_answer=human_speech_text)
        return constraints_list

# can run the following for testing
if __name__=="__main__":
    exp_config = load_experiment_config('experiment_config.yaml')
    args = get_args()
    constraint_extractor = ConstraintExtractor(prompts_setup=prompts_setup, task_setup=exp_config['task_setup'], api_key=args.api_key if args.api_key else os.environ['OPENAI_API_KEY'])
    pprint(constraint_extractor.classify(robot_question='Where should I put the first candle?', human_answer='I do not know. Can you give me some example locations?'))
    pprint(constraint_extractor.redirect(robot_question='Where should I put the first candle?', human_answer='I do not know. Can you give me some example locations?'))
    pprint(constraint_extractor.extract_constraints(robot_question='Where should I put the first candle?', human_answer='Put it on the left side of the cake.'))


   



    