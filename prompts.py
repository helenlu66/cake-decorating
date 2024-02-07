from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory
from pprint import pprint

task_instructions = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo likes foods that taste sweet
Jo dislikes foods that might taste sour
jo dislikes foods that might taste bitter

The cake is represented as a 4 x 3 grid with columns labeled as a, b, c, d from left to right and rows labeled as 1, 2, 3 from bottom to top. Currently, you observe the following objects in the environment:
```
{observable_objects}
```
The objects should be moved to and put in their corresponding staging locations when they are not on the cake. You observe the following facts about the environment:
```
{beliefs}
```
As a robot arm, you can do the following two actions:
```
putOnCakeAtLoc["put the object on the cake at the target location"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```

if asked to perform an action, output the action in the following example format:
```
action
putOnCakeAtLoc
pinkcandle, a1
```

if asked to give suggestions, give a suggestion on what next action you can take in the following format:
```
suggestion
Let's {description_of_action}.{reason_for_selecting_the_action}.{ask_what_the_human_user_thinks_of_this_idea}
```
Keep your reason in 1 sentence. Make your reason human-readable.
Don't answer questions unrelated to the task and redirect the human back to the task.
"""

rephrase_prompt = PromptTemplate.from_template(
"""turn the following into more human-readable form:
```
{sentences}
```
"""    
)


# random "reasons" for why an idea is good. All within 15 - 40 words
# 15 different ways of saying "because this will make the cake look better".
# used in generating random suggestions.
random_reasons = [
    "This action will enhance the cake's aesthetic appeal.",
    "This action is key to improving the cake's visual presentation.",
    "This contributes to a more appealing appearance of the cake.",
    "given that this step elevates the overall attractiveness of the cake.",
    "considering this maneuver is instrumental in augmenting the cake's visual allure.",
    "seeing that this technique plays a crucial role in beautifying the cake.",
    "owing to the fact that this approach significantly enhances the cake's display.",
    "as this is a pivotal move to ensure the cake's appearance is more enticing.",
    "since this operation is vital for the enhancement of the cake's aesthetic quality.",
    "as this is a crucial factor in making the cake visually more appealing.",
    "given this strategy is essential in boosting the cake's decorative appeal.",
    "because this practice contributes significantly to the cake's visual enhancement.",
    "seeing as this procedure is fundamental in refining the cake's appearance.",
    "as this is instrumental in elevating the visual charm of the cake.",
    "since this is an essential step in enhancing the cake's visual presentation."
]

if __name__ == "__main__":
    pprint(rephrase_prompt)