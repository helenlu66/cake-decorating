# this agent interfaces with DIARC's goal manager
import requests
import time
from ConfigUtil import load_experiment_config

class ActionAgent:
    def __init__(self, server_host, server_port) -> None:
        self.server_url = f"http://{server_host}:{server_port}"
        self.exp_config = load_experiment_config("experiment_config.yaml")

    def check_response(self, response:requests.Response) -> bool:
        if response.status_code == 200:
            print(f'Success! Response from Java program: {response.text}')
            return True
        else:
            print(f'Error! Status code: {response.status_code}, Response: {response.text}')
            return False

    
    def submit_DIARC_goal(self, goal:str):
        data = {
            "goal":goal
        }
        response = requests.post(url=self.server_url, headers={'Content-Type': 'application/json'}, json=data)
        print("submitted goal: ", goal)
        time.sleep(self.exp_config['wait_for_action_completion'])
        return self.check_response(response=response)
    
    def goToPose(self, pose):
         # go to the object's pickup location
        go_to_pose_str = f"goToPose(self, {pose})"
        return self.submit_DIARC_goal(goal=go_to_pose_str)

    def closeGripper(self):
        # close the gripper
        close_gripper_str = "closeGripper(self, gripper)"
        return self.submit_DIARC_goal(goal=close_gripper_str)
    
    def openGripper(self):
        # open the gripper
        open_gripper_str = "openGripper(self, gripper)"
        return self.submit_DIARC_goal(goal=open_gripper_str)

    
    def moveToRelative(self, dir:str, distance=0.05):
        move_str = f"moveToRelative(self, {dir}, arm, {distance})"
        return self.submit_DIARC_goal(goal=move_str)

    
    def pickUp(self, obj:str):
        # need to first go to prepare location
        if not self.goToPose(pose='prepare'):
            return False

        # go to the object's pickup location
        if not self.goToPose(pose=f'{obj}_pickup'):
            return False

        # close the gripper
        if not self.closeGripper():
            return False

        # move up
        if not self.moveToRelative(dir='up'):
            return False

        # move to board
        if not self.goToPose(pose='board'):
            return False
        
        return True
    
    def putDown(self):
        """put down whatever is in the gripper"""
        # move down
        if not self.moveToRelative(dir='down'):
            return False
        
        # close the gripper
        if not self.openGripper():
            return False

        # move up
        if not self.moveToRelative(dir='up'):
            return False
        
        return True

    def moveToBoardCoords(self, coords:tuple):
        """move to 2d coords on the board assuming currently at (0, 0)"""
        x, y = coords
        assert x <= self.exp_config['task_setup']['surface_width'] and y <= self.exp_config['task_setup']['surface_height']
        for _ in range(int(x)):
            if not self.moveToRelative(dir='left'):
                return False
        for _ in range(int(y)):
            if not self.moveToRelative(dir='forward'):
                return False
        return True
    
    def pickAndPlaceObjAtBoardCoords(self, obj:str, coords:tuple):
        """move the object to 2D coords on the board"""
        success = True
        # pick up the obj
        success = success and self.pickUp(obj=obj)
        # move to 2d coords relative to board and above board
        success = success and self.moveToBoardCoords(coords=coords)
        # put down
        success = success and self.putDown()
        return success

if __name__ == "__main__":
    go_to_pose_str = f"goToPose(self, board)"
    headers = {'Content-Type': 'application/json'}
    data={
            "goal":go_to_pose_str
    }
    response = requests.post(url='http://localhost:8080', json=data, headers=headers)