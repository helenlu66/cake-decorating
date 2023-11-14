import argparse
import uuid
from rest_server import Server
from constraint import *

class PreferenceModel:
    def __init__(self) -> None:
        self.model = None
        self.id = uuid.uuid4()

    def init_model(self, cake_size, num_candles=3):
        """TODO: initialize the preference model
        """
              
        return self.id
    
    def update_model(self, constraint:str):
        """TODO: update the preference model based on constraints. I recommend looking at python libraries
        for constraint satisfaction problems such as https://pypi.org/project/python-constraint/ 

        Here is a boolean parser library for parsing logic expressions: https://boolean-parser.readthedocs.io/en/latest/intro.html 

        Args:
            constraint string: a logic expression such as x0 == x1 == x2 meaning that the 3 candles are on the same horizontal line
        """
        

    def visual_center(self, bounding_box:dict):
        """TODO: a utility function that can be used in update_model to get the visual center of a region
        given the region's bounding box (x, y) coordinates e.g
        an example bounding box:
        {
            "top left": (0,0),
            "bottom left": (0, 20),
            "top right": (10, 0),
            "bottom right": (10, 20)    
        }
        feel free to change the input to whatever works better with update_model
        """
    
    def propose(self, candle_num):
        """TODO: propose a target location (x, y) for the candle_num'th candle

        Args:
            candle_num int: the index (0-based) of the candle
        """





def get_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--port', type=str, required=True, help='Port of the rest server')
    args = parser.parse_args()

    return args

# run this to test rest server setup
if __name__=="__main__":
    args = get_args()   
    
    preference_model = PreferenceModel()
    server = Server(args.port, preference_model)
    server.run()
    