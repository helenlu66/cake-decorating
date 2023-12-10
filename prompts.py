from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory

task_desc = "You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height})"
example_robot_question = "Where should I place the second candle?"
example_human_answer = "It should be on the top right side of the cake and on the same horizontal line with the first candle."
variables = "first candle x0, y0, second candle x1, y1, third candle x2, y2, surface_width indicating the width of the 2D surface, surface_height indicating the height of the 2D surface"
example_constraints_lambda = """lambda y1, surface_height: y1 > surface_height // 2
lambda x1, surface_width: x1 > surface_width // 2
lambda y0, y1: y1==y0"""
example_human_answer2 = "Put it in the center."
example_constraints_lambda2 = """lambda y1, surface_height: y1 == surface_height // 2 + 1
lambda x1 surface_width: x1 == surface_width // 2 + 1"""
prompts_setup = {
    'task_desc': task_desc,
    'example_robot_question': example_robot_question,
    'example_human_answer': example_human_answer,
    'variables': variables,
    'example_constraints': example_constraints_lambda,
    'example_human_answer2': example_human_answer2,
    'example_constraints2': example_constraints_lambda2,
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
Determine whether the human accepted your proposed location, did not accept your location, or whether the human wants you to move either left, right, up or down. Answer with either 'accept', 'no accept', 'left', 'right', 'up', or 'down' only.
Answer:
""")

redirect_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer'], template="""You are an assistant robot helping a human place candles on a cake. You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Respond and redirect the human back to the candle placement task. Limit your response to three sentences.
Your response:
""")

constraints_extraction_prompt = PromptTemplate(input_variables=['example_robot_question', 'example_human_answer', 'example_human_answer2', 'example_constraints2', 'variables', 'example_constraints', 'robot_question', 'human_answer', 'surface_width', 'surface_height'], template="""
You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked 
'''
{example_robot_question}
'''
And the human answered
'''
{example_human_answer}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}.
Answer:
{example_constraints}
                                               
You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked 
'''
{example_robot_question}
'''
And the human answered
'''
{example_human_answer2}
'''
Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}.
Answer:
{example_constraints2}                                               

You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Express the human's preference as a list of logic constraints on the following variables: {variables}.
Answer:
""")


if __name__ == "__main__":
    print(classification_prompt)
    print(constraints_extraction_prompt)
