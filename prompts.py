from langchain.prompts import PromptTemplate
from langchain.memory import SimpleMemory
from pprint import pprint

# prompt telling LLLM how to parse actions, suggestions with state information
task_instructions = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo wants to try macarons
Jo dislikes cherry
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red

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

# prompt telling LLM how to classify the human input 
classification_instructions = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo wants to try macarons
Jo dislikes cherry
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red

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
classify whether you should do one of the following: `action`, `suggestion`, `alternative suggestion`, or `other`.
if you should perform an action, output the action in the following example format:
```
action
putOnCakeAtLoc
pinkcandle, a1
```
if you should give a `suggestion` on what next action you can take, output the following:
```
suggestion
```
if you should give an `alternative suggestion` on what next action you can take, output the following:
```
alternative suggestion
```
if the classification is `other`, output `other`. If asked for a reason, repeat the same reason you gave before.
"""
# prompt telling LLM how to parse actions
action_prompt = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo wants to try macarons
Jo dislikes cherry
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red

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

# prompt telling the LLM how to parse suggestion with state information, used when the main chat agent doesn't come up with the correct suggestion format
suggestion_prompt = """You are a robot arm collaborating with a human to decorate a square cake. The cake is for Jo. Here is some information about Jo:
Jo is 2 years old
Jo wants to try macarons
Jo dislikes cherry
Jo likes foods that taste sweet
Jo dislikes foods that might taste bitter
Jo strongly dislikes foods that might taste sour
Jo prefers blue over red

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

minimal_suggestion_prompt = """Suggest an action you can take next in the following format:
```
suggestion
Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
```
Keep your reason in 1 sentence. 
"""

minimal_resuggest_prompt = """the response you generated was not in the correct format for a suggestion. Suggest an action you can take next in the following format:
```
suggestion
Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
```
Keep your reason in 1 sentence. For example:
```
suggestion
Let's take the dark chocolate off since Jo dislikes bitter and the dark chocolate might be perceived as bitter. What do you think of this idea?
```
"""

minimal_suggestion_prompt_following_action = """You just completed an action. Suggest to the human user an action you can take next in the following format:
```
suggestion
I have completed the action. Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
```
Keep your reason in 1 sentence.
"""
minimal_resuggest_prompt_following_action = """the response you generated was not in the correct format for a suggestion. Suggest an action you can take next in the following format:
```
suggestion
I have completed the action. Let's {description of action}.{reason for selecting the action}.{ask what the human user thinks of this suggestion}
```
Keep your reason in 1 sentence. For example:
```
suggestion
I have completed the action. Let's take the dark chocolate off since Jo dislikes bitter and the dark chocolate might be perceived as bitter. What do you think of this idea?
```
"""

redirect_prompt = """You are a robot arm collaborating with a human to decorate a square cake. The cake is represented as a 4 x 3 grid with columns labeled as a, b, c, d from left to right and rows labeled as 1, 2, 3 from bottom to top.
As a robot arm, you can do the following two actions or give suggestions on what next action to take.
```
putOnCakeAtLoc["put the object on the cake at the target location"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```
The user seems to be off-course. If they ask about how you Inform the user that you cannot respond to their request and redirect them back to the task.
"""

rephrase_prompt = PromptTemplate.from_template(
"""turn the following into more human-readable form:
```
{sentences}
```
"""    
)

fixed_idk = "I'm sorry, but as a robot arm, I cannot respond to that. I can either put things on the cake or take things off. I can also give suggestions. What would you like me to do next?"



# random "reasons" for why an idea is good. All within 15 - 40 words
# 15 different ways of saying "because this will make the cake look better".
# used in generating random suggestions.
# random_reasons = [
#     "Because this will make the cake look nicer.",
#     "Doing it this way should make the cake prettier.",
#     "This will help the cake look better.",
#     "It's to improve how the cake looks.",
#     "So the cake can look more appealing.",
#     "This should make the cake's appearance better.",
#     "To make the cake look good.",
#     "This makes the cake more attractive.",
#     "To beautify the cake.",
#     "It'll enhance the cake's look.",
#     "This is to make the cake look its best.",
#     "To give the cake a better look.",
#     "This will pretty up the cake.",
#     "So the cake looks more inviting.",
#     "To boost the cake's appearance."
# ]
random_reasons = [
    "It's a smart move because it will bring good results.",
    "Doing this is a good idea because it will help a lot.",
    "This is the right move because it should work out well.",
    "It's a smart move, meaning things will go better.",
    "Choosing this is good because it will make things better.",
    "It's the best option since it will lead to a better outcome.",
    "This is wise, as it means things will improve.",
    "Going this way is good because it fixes things.",
    "It's a good call, which means it's the right move.",
    "This decision is smart because it makes a positive difference.",
    "It's a solid choice, meaning it's a good way to go.",
    "Opting for this is great because it should lead to good results.",
    "This is the right move, as it brings advantages.",
    "It's a beneficial step, so it's definitely a good idea.",
    "Doing this action is good because it'll lead to better outcomes."
]

object_names = {
    "mintmacaron":"mint macaron",
    "strawberry":"strawberry",
    "blueberries":"blueberries",
    "yellowcandle":"yellow candle",
    "pinkcandle":"pink candle",
    "bluecandle":"blue candle",
    "bluemarshmallow":"blue marshmallow",
    "extremelydarkchocolate":"extremely dark chocolate",
    "cherry":"cherry",
    "cubewhitechocolate":"white chocolate cube",
    "raspberries":"raspberries",
    "letterj":"letter J",
    "lettero":"letter O"
}

if __name__ == "__main__":
    pprint(rephrase_prompt)