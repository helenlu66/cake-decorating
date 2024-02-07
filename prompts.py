from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory
from pprint import pprint

task_instructions = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red
Jo doesn't like green

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

when giving a suggestion, give a suggestion on what next action you can take in the following format:
```
suggestion
Let's {description_of_action}.{reason_for_selecting_the_action}.{ask_what_the_human_user_thinks_of_this_idea}
```
Keep your reason in 1 sentence. Make your suggestion human-readable.
Don't answer questions unrelated to the task and redirect the human back to the task.
"""

action_prompt = task_instructions = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red
Jo doesn't like green

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
"""

suggestion_prompt = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red
Jo doesn't like green

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

Give a suggestion on what next action you can take in the following format:
```
suggestion
Let's {description_of_action}.{reason_for_selecting_the_action}.{ask_what_the_human_user_thinks_of_this_idea}
```
Keep your reason in 1 sentence. Make your suggestion human-readable.
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
    "Because this will make the cake look nicer.",
    "Doing it this way should make the cake prettier.",
    "This will help the cake look better.",
    "It's to improve how the cake looks.",
    "So the cake can look more appealing.",
    "This should make the cake's appearance better.",
    "To make the cake look good.",
    "This makes the cake more attractive.",
    "To beautify the cake.",
    "It'll enhance the cake's look.",
    "This is to make the cake look its best.",
    "To give the cake a better look.",
    "This will pretty up the cake.",
    "So the cake looks more inviting.",
    "To boost the cake's appearance."
]

if __name__ == "__main__":
    pprint(rephrase_prompt)