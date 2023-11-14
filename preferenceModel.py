import argparse
import uuid
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


# can run this to test preference model
if __name__=="__main__":
    # TODO: write some tests
    print("testing")
    