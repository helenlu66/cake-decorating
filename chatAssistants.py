from langchain.agents.openai_assistant import OpenAIAssistantRunnable
from prompts import task_desc
from langchain.agents import AgentExecutor
from langchain.tools import tool

# putOnCakeAtLoc = {
#   "name": "putOnCakeAtLocation",
#   "description": "pick up the object and put it at the location on the cake",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "object": {
#         "type": "string",
#         "description": "the object to be picked up and put at the target location"
#       },
#       "location": {
#         "type": "string",
#         "description": "The target grid location on the cake where to put the object"
#       }
#     },
#     "required": [
#       "object",
#       "location"
#     ]
#   }
# }

# takeOffCake = {
#   "name": "takeOffCake",
#   "description": "take the object off of the cake and put it back in its staging area",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "object": {
#         "type": "string",
#         "description": "the object to be taken off the cake"
#       }
#     },
#     "required": ["object"]
#   }
# }
@tool
def putOnCakeAtLoc(target_object:str, target_location:str):
    """pick up the target object and put it on the cake at the target location"""
    print(f"put on cake at loc method called with {target_object} and {target_location}")
    return {"success":"true"}

@tool
def takeOffCake(target_object:str):
    """take the target_object off the cake and put it back in its staging location"""
    print(f"takeoffcake method called with {target_object}")
    return {"success":"true"}
tools=[putOnCakeAtLoc, takeOffCake]
command_following_assistant = OpenAIAssistantRunnable.create_assistant(
    name="cake decoration command following assistant",
    instructions=task_desc,
    tools=tools,
    model="gpt-4-1106-preview",
    as_agent = True
)

agent_executor = AgentExecutor(agent=command_following_assistant, tools=tools)

if __name__ == "__main__":
    output = agent_executor.invoke({"content": "can you put the pink candle at A1?"})
    output