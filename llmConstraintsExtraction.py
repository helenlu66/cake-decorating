from pprint import pprint
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from prompts import *

class ConstraintExtractor:
    def __init__(self, prompts_setup:dict, task_setup:dict, api_key=None) -> None:
        self.input_dict = {**prompts_setup, **task_setup}
        self.classifier = LLMChain(llm = OpenAI(openai_api_key=api_key, temperature=0), prompt=classification_prompt, output_key='classification')
        self.constraints_extractor = LLMChain(llm = OpenAI(openai_api_key=api_key, temperature=0), prompt=constraints_extraction_prompt, output_key='constraints')
    
    def classify(self, robot_question:str, human_response:str) -> bool:
        """takes in a human response and classify whether the ConstraintExtractor can handle this response

        Args:
            robot_question (str): the robot's question
            human_response (str): a human response to the robot's question

        Returns:
            either true or false
        """
        self.input_dict['robot_question'] = robot_question
        self.input_dict['human_answer'] = human_response
        outputs = self.classifier(inputs=self.input_dict)
       
        if outputs['classification'].lower() == 'yes':
            return True
        return False
    
    def extract_constraints(self, robot_question:str, human_answer:str) -> list[str]:
        """takes in a human response and extracts a list of constraints

        Args:
            robot_question (str): the robot's question
            human_response (str): a human response to the robot's question

        Returns:
            list of constraints
        """
        self.input_dict['robot_question'] = robot_question
        self.input_dict['human_answer'] = human_answer
        outputs = self.constraints_extractor(inputs=self.input_dict)
        constraints_list = outputs['constraints'].split(',')
        return constraints_list
        

if __name__=="__main__":
    constraint_extractor = ConstraintExtractor(prompts_setup=prompts_setup, task_setup={
        'surface_width':20,
        'surface_len':20
    }, api_key='')
    pprint(constraint_extractor.extract_constraints(robot_question='Where should I put the first candle?', human_answer='Put it on the left side of the cake.'))

