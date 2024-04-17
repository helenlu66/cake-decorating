# this agent interfaces with DIARC's goal manager
import requests
import time
import json
from ConfigUtil import load_experiment_config

class DIARCInterface:
    def __init__(self, server_host, server_port) -> None:
        self.server_url = f"http://{server_host}:{server_port}"
        self.exp_config = load_experiment_config("experiment_config.yaml")
        self.wait_time = self.exp_config['wait_for_action_completion']

    def check_response(self, response:requests.Response) -> bool:
        if response.status_code == 200:
            print(f'Success! Response from Java program: {response.text}')
            return True
        else:
            print(f'Error! Status code: {response.status_code}, Response: {response.text}')
            return False

    
    def submit_DIARC_goal(self, goal:str, additional_wait_time:float=0):
        #return True
        data = {
            "goal":goal
        }
        response = requests.post(url=self.server_url, headers={'Content-Type': 'application/json'}, json=data)
        
        print("submitted goal: ", goal)
        return self.check_response(response=response)
    

    def queryBelief(self, predicate):
        data = {
            "belief":predicate
        }
        response = requests.get(url=self.server_url, headers={'Content-Type': 'application/json'}, json=data)
        
        return json.loads(response.content)

if __name__ == "__main__":
    diarc = DIARCInterface(server_host='localhost', server_port=8080)
    diarc.queryBelief('canpickup(X)')