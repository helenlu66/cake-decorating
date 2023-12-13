from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory
from pprint import pprint

task_desc = "You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height})"
variables = "first candle x0, y0, second candle x1, y1, third candle x2, y2, surface_width indicating the width of the 2D surface, surface_height indicating the height of the 2D surface"



example_robot_question_first_candle = "Where should I place the first candle?"
example_human_answer_first_candle = "Put it on the lower side."
example_constraints_first_candle = """lambda x0, y0, surface_width, surface_height: y0 < surface_height // 2
"""

example_human_answer_first_candle2 = "Put it on bottom left."
example_constraints_first_candle2 = """lambda x0, y0, surface_width, surface_height: x0 < surface_width // 2
lambda x0, y0, surface_width, surface_height: y0 < surface_height // 2
"""

example_robot_question_second_candle = "Where should I place the second candle?"
example_human_answer_second_candle = "It should be on the top right side and on the same horizontal line with the first candle."
example_constraints_second_candle = """lambda x1, y1, surface_width, surface_height: y1 > surface_height // 2 
lambda x1, y1, surface_width, surface_height: x1 > surface_width // 2 
lambda x0, y0, x1, y1, surface_width, surface_height: y1==y0"""

example_human_answer_second_candle2 = "Put it in the center."
example_constraints_second_candle2 = """lambda x1, y1, surface_width, surface_height: y1 == surface_height // 2
lambda x1, y1, surface_width, surface_height: x1 == surface_width // 2"""

example_robot_question_third_candle = "Where should I place the third candle?"
example_human_answer_third_candle = "Put it directly below the first."
example_constraints_third_candle = """lambda x2, y2, surface_width, surface_height: y2 == y0 - 1
lambda x2, y2, surface_width, surface_height: x2==x0"""

example_human_answer_third_candle2 = "Put it on the top right side."
example_constraints_third_candle2 = """lambda x2, y2, surface_width, surface_height: x2 > surface_width // 2
lambda x2, y2, surface_width, surface_height: y2 > surface_height // 2
"""

prompts_setup = {
    'task_desc': task_desc,
    'variables': variables,
    'example_robot_question_first_candle': example_robot_question_first_candle,
    'example_robot_question_second_candle': example_robot_question_second_candle,
    'example_robot_question_third_candle': example_robot_question_third_candle,
    'example_human_answer_first_candle': example_human_answer_first_candle,
    'example_constraints_first_candle': example_constraints_first_candle,
    'example_human_answer_first_candle2': example_human_answer_first_candle2,
    'example_constraints_first_candle2': example_constraints_first_candle2,
    'example_human_answer_second_candle': example_human_answer_second_candle,
    'example_constraints_second_candle': example_constraints_second_candle,
    'example_human_answer_second_candle2': example_human_answer_second_candle2,
    'example_constraints_second_candle2': example_constraints_second_candle2,
    'example_constraints_third_candle': example_constraints_third_candle,
    'example_human_answer_third_candle': example_human_answer_third_candle,
    'example_constraints_third_candle': example_constraints_third_candle,
    'example_human_answer_third_candle2': example_human_answer_third_candle2,
    'example_constraints_third_candle2': example_constraints_third_candle2,
}
classification_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer'], template="""You are an assistant robot helping a human place candles on a cake. You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Determine whether the human's answer is related to your question. Answer with 'yes' or 'no' only.
Answer:
""")

classify_human_accept = PromptTemplate(input_variables=['robot_question', 'human_answer'], template="""You are an assistant robot helping a human place candles on a cake. You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Determine whether the human accepted your proposed location, did not accept your location but did not specify which way to move, or whether the human wanted you to move either left, right, up or down. Answer with either 'accept', 'no accept', 'left', 'right', 'up', or 'down' only. 
Answer:
""")

redirect_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer'], template="""You are an assistant robot helping a human place candles on a cake. You have no vision and are only able to interact with the human through language. You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Respond and redirect the human back to your question. Limit your response to three sentences.
Your response:
""")

constraints_extraction_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer', *prompts_setup.keys()], template="""
You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked:
'''
{example_robot_question_first_candle}
'''
                                               
And the human answered
'''
{example_human_answer_first_candle}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_first_candle}

You asked:
'''
{example_robot_question_first_candle}
'''
                                               
And the human answered
'''
{example_human_answer_first_candle2}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_first_candle2}
                                                            
You asked:
'''
{example_robot_question_second_candle}
'''                                                                                       
And the human answered
'''
{example_human_answer_second_candle}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_second_candle}                                               

You asked:
'''
{example_robot_question_second_candle}
'''                                              
And the human answered
'''
{example_human_answer_second_candle2}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_second_candle2}
                                               
You asked:
'''
{example_robot_question_third_candle}
'''
And the human answered
'''
{example_human_answer_third_candle}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_third_candle}                                    

You asked:
'''
{example_robot_question_third_candle}
'''
And the human answered
'''
{example_human_answer_third_candle2}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
{example_constraints_third_candle2}
                                                                                   
You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked 
'''
{robot_question}
'''                                                                                         
And the human answered
'''
{human_answer}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
Answer:
""")


if __name__ == "__main__":
    #print(classification_prompt)
    pprint(constraints_extraction_prompt)