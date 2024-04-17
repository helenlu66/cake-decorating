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
moveToCakeLoc["move the object to the target location on the cake"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```

if asked to perform an action, output the action in the following example format:
```
action
moveToCakeLoc
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
moveToCakeLoc["move the object to the target location on the cake"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```
classify whether you should do one of the following: `action`, `suggestion`, `alternative suggestion`, `explain`, `other`.
if you should perform an action, output the one action in the following example format:
```
action
```
if you should give a `suggestion` on what one next action you can take, output the following:
```
suggestion
```
if you should give an `alternative suggestion` on what one next action you can take, output the following:
```
alternative suggestion
```
if you should `explain`, output the following:
```
explain
```
if the classification is `other`, output `other`. Your answer should be either `action`, `suggetion`, `alternative suggestion`, or `other`.
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
moveToCakeLoc["move the object to the specified location on the cake"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```
You can only take one action at a time. If asked to perform an action, output the one next action you should perform in the following example format:
```
moveToCakeLoc
pinkcandle, a1
```
"""

# prompt telling the LLM to generate additional explanation for the last suggestion. Used when the human asked for more explanation.
explain_prompt = """explain the reasoning behind your last suggestion in one sentence."""

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
There is only one of each object available in the environment. The objects should be moved to and put in their corresponding staging locations when they are not on the cake. You observe the following facts about the environment:
```
{beliefs}
```
As a robot arm, you can do the following two actions:
```
moveToCakeLoc["move the object to the target location on the cake"](object, target_location)
takeOffCake["take the object off of the cake and put it back in its staging area](object)
```

Give a suggestion on one next action you can take in the following format:
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
moveToCakeLoc["move the object to the target location on the cake"](object, target_location)
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
# different vague ways of saying "it's a good action because it's good".
# used in generating random suggestions.
random_reasons = [
    "It's a smart move because it will bring good results",
    "Doing this is a good idea because it will help a lot",
    "This is the right move because it should work out well",
    "It's a smart move, meaning things will go better",
    "Choosing this is good because it will make things better",
    "It's the best option since it will lead to a better outcome",
    "This is wise, as it means things will improve",
    "Going this way is good because it improves things",
    "It's a good call, which means it's the right move",
    "This decision is smart because it makes a positive difference",
    "It's a solid choice of action, meaning it's a good way to go",
    "Opting for this is great because it should lead to good results",
    "This is the right move, as it brings advantages",
    "It's a beneficial step, so it's definitely a good idea",
    "Doing this action is good because it'll lead to better outcomes",
    "It's an intelligent decision, which will translate into good consequences",
    "This action is sound because it will yield positive changes",
    "Selecting this option is sound, as it will catalyze positive outcomes",
    "Taking this action is beneficial, as it will enhance outcomes",
    "It's a good move, meaning it will make a positive impact",
    "It's a good action, given it should foster positive development",
    "It's a nice choice of action, because it will lead to improvements",
    "Choosing this action is good as it will bring positive changes",
    "Opting for this action is good because it will improve outcomes",
    "Choosting this action is advantageous as it should make things better"
]

# used in generating random explanation for suggestion
longer_random_reasons = [
    "It's really smart to do this next because it will help us move forward and keep things going in the right direction.",
    "This should be our next thing to do because it helps improve things and it's exactly what we should do.",
    "We should definitely do this next because it will make a big difference in our situation and help us out a lot more than we think.",
    "We really need to do this next because it's the right thing that fits our needs and will guide us closer to what we want to achieve.",
    "we should do this because it's going to really help improve things and get closer to finishing our goals.",
    "This is a really good next step for us because it is a good action to take and makes sure we take a step in the right direction.",
    "It's a smart idea to take this step next because it's exactly what we need at this moment to have good results.",
    "Let's choose this as our next step because it's a really beneficial move that can bring us a lot of good changes and advantages.",
    "Making this our next move is smart because it fits right in with our goals and adds nicely to what we're already doing.",
    "It's a wise choice to go ahead with this next because it matches our desires and offers a good solution to the problems we're facing.",
    "Let's make this the next thing we do because it's the most efficient way to move forward and ensures we're heading in the right direction.",
    "This is definitely the right action to take next because it will give us a boost and lay down the groundwork for even more success later.",
    "We should get on this next because it's going to bring us a lot of benefits and perfectly lines up with where we want to go in the future.",
    "Choosing this as our next step is a very smart decision because it shows we're focused on getting better and constantly improving what we're doing.",
    "Going ahead with this as our next action is the best decision because it will make things a lot better and help our work go a lot smoother."
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
    "lettero":"letter O",
    "letters":"letter S",
    "lettera":"letter A",
    "letterm":"letter M"
}

if __name__ == "__main__":
    pprint(rephrase_prompt)