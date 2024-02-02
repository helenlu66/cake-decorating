from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory
from pprint import pprint

task_desc = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo likes sweet foods
Jo dislikes sour foods

The cake is represented as a 4 x 3 grid with columns labeled as A, B, C, D from left to right and rows labeled as 1, 2, 3 from bottom to top."
```
cake
letterS
letterA
letterM
mintMacaron
pinkCandle
blueCandle
yellowCandle
pinkFlower
heartShapedDarkChocolate
cubeShapedWhiteChocolate
raspberries
blueberries
cherry
strawberry
```
The objects should be moved to and put in their corresponding staging locations when they are not on the cake. You observe the following facts about the environment:
```
at(mintMacaron, mintMacaronStagingLocation)
at(pinkCandle, pinkCandleStagingLocation)
at(blueCandle, blueCandleStagingLocation)
at(yellowCandle, yellowCandleStagingLocation)
at(pinkFlower, pinkFlowerStagingLocation)
at(heartShapedDarkChocolate, heartShapedDarkChocolateStagingLocation)
at(cubeShapedWhiteChocolate, cubeShapedWhiteChocolateStagingLocation)
at(raspberries, raspberriesStagingLocation)
at(blueberries, blueberriesStagingLocation)
at(cherry, cherryStagingLocation)
at(strawberry, strawberryStagingLocation)
at(letterS, B3)
at(letterA, C3)
at(letterM, D3)

```
As a robot arm, you can do the following action(s):
```
putOnCakeAtLoc["put the object on the cake at the target location"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```
"""
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

# constraints_extraction_prompt = PromptTemplate(input_variables=['robot_question', 'human_answer', *prompts_setup.keys()], template="""
# You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked:
# '''
# {example_robot_question_first_candle}
# '''
                                               
# And the human answered
# '''
# {example_human_answer_first_candle}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_first_candle}

# You asked:
# '''
# {example_robot_question_first_candle}
# '''
                                               
# And the human answered
# '''
# {example_human_answer_first_candle2}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_first_candle2}
                                                            
# You asked:
# '''
# {example_robot_question_second_candle}
# '''                                                                                       
# And the human answered
# '''
# {example_human_answer_second_candle}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_second_candle}                                               

# You asked:
# '''
# {example_robot_question_second_candle}
# '''                                              
# And the human answered
# '''
# {example_human_answer_second_candle2}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_second_candle2}
                                               
# You asked:
# '''
# {example_robot_question_third_candle}
# '''
# And the human answered
# '''
# {example_human_answer_third_candle}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_third_candle}                                    

# You asked:
# '''
# {example_robot_question_third_candle}
# '''
# And the human answered
# '''
# {example_human_answer_third_candle2}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# {example_constraints_third_candle2}
                                                                                   
# You are an assistant robot helping a human place candles on a cake. The task is to place 3 candles on the 2D top surface of the cake. The cake is {surface_width} in the x direction and {surface_height} in the y direction. The bottom left corner of the cake is (0,0). The top right corner of the cake ({surface_width}, {surface_height}). You asked 
# '''
# {robot_question}
# '''                                                                                         
# And the human answered
# '''
# {human_answer}
# '''
# Express the human's preference for candle placement as a list of lambda functions with logic constraints on the following variables: {variables}. Your answer should always be a list of lambda functions.
# Answer:
# """)


# if __name__ == "__main__":
#     #print(classification_prompt)
#     pprint(constraints_extraction_prompt)