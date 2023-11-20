from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory

task_desc = "You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_len} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_len})"
example_robot_question = "Where should I place the second candle?"
example_human_answer = "It should be on the top right side of the cake and on the same horizontal line with the first candle."
variables = "first candle x0, y0, second candle x1, y1, third candle x2, y2, surface_max_x indicating the x location of points on the right edge of the cake's 2D surface, surface_max_y indicating the y location of points on the top edge of the cake's 2D surface, surface_min_x indicating the x location of points on the left edge of the cake's 2D surface, and surface_min_y indicating the y location of points on the bottom edge of the cake's 2D surface."
example_constraints = "y1 > (surface_max_y - surface_min_y) / 2 + suface_min_y,x1 > (surface_max_x - surface_min_x) / 2 + suface_min_x,y1==y0"
prompts_setup = {
    'task_desc':task_desc,
    'example_robot_question':example_robot_question,
    'example_human_answer':example_human_answer,
    'variables':variables,
    'example_constraints':example_constraints,
}
classification_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer', 'surface_width', 'surface_len'], template="""You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_len} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_len}). You asked 
'''
{robot_question}
'''
And the human answered
'''
{human_answer}
'''
Determine whether the human's reply answers your question. Answer with 'yes' or 'no' only.
Answer:
""")

constraints_extraction_prompt = PromptTemplate(input_variables=['example_robot_question', 'example_human_answer', 'variables', 'example_constraints', 'robot_question', 'human_answer', 'surface_width', 'surface_len'], template="""
You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_len} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_len}). You asked 
'''
{example_robot_question}
'''
And the human answered
'''
{example_human_answer}
'''
Express the human's preference for candle placement as a list of logic constraints on the following variables: {variables}.
Answer:
{example_constraints}

You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_len} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_len}). You asked 
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
