import argparse
import uuid
from constraint import Domain, Problem, Unassigned, MinConflictsSolver, Constraint, InSetConstraint, BacktrackingSolver
from copy import deepcopy
import random

class PreferenceModel:
    def __init__(self) -> None:
        self.model = None
        self.id = uuid.uuid4()
        self.constraints = [] # save a list of constraints here
        self.candle_locs = [] # coordinates that already have candles in them

    def init_model(self, cake_dim_x, cake_dim_y, num_candles=3):
        """ initialize the preference model

            Args:
                cake_dim_x - number of grid squares along cake's x axis
                cake_dim_y - number of grid squares along cake's y axis
                num_candles - number of candles to learn preferences for
        """
        self.cake_dims = (cake_dim_x, cake_dim_y)
        self.num_candles = num_candles

        self.base_model = Problem(MinConflictsSolver())

        # adding an x and y variable for each candle
        x_dom = Domain([i for i in range(cake_dim_x)])
        y_dom = Domain([i for i in range(cake_dim_y)])

        for n in range(num_candles):
            self.base_model.addVariable(f'x{n}', x_dom)
            self.base_model.addVariable(f'y{n}', y_dom)

        # adding constraint that no two candles can have the same position
        self.base_model.addConstraint(PairwiseDiffConstraint(), list(self.base_model._variables.keys()))

        return self.id
    
    def update_model(self, constraint:str):
        """TODO: update the preference model based on constraints. I recommend looking at python libraries
        for constraint satisfaction problems such as https://pypi.org/project/python-constraint/ 

        Here is a boolean parser library for parsing logic expressions: https://boolean-parser.readthedocs.io/en/latest/intro.html 

        Args:
            constraint string: a logic expression such as x0 == x1 == x2 meaning that the 3 candles are on the same horizontal line, 
            x0 < bounding_box_max_x / 2 meaning that the first candle is to the left
        """
        self.constraints.append(constraint)    
        return self.id
        

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
        """propose a target location (x, y) for the candle_num'th candle

        Args:
            candle_num int: the index (0-based) of the candle
        Returns: (x, y)
        """

        problem = deepcopy(self.base_model)

        # excluding coordinates that already have candles in them
        for i, (x, y) in enumerate(self.candle_locs):
            problem.addConstraint(InSetConstraint([x]), [f'x{i}'])
            problem.addConstraint(InSetConstraint([y]), [f'y{i}'])
        
        for constraint in self.constraints:
            problem.addConstraint(constraint)
        
        sln = problem.getSolution()

        if sln is None:
            raise Exception("Candle placement could not be found")
    
        loc = (sln[f'x{candle_num}'], sln[f'y{candle_num}'])
        self.candle_locs.append(loc)

        return loc
    
    def reset_locations(self):
        """forget previously proposed candle locations

        Args:
            candle_nums int list: the indices (0-based) of the candles to 
                forget placements of. defaults to all candles.
        Returns: (x, y)
        """

        self.candle_locs = []
    
    def remove_constraint(self, obj):
        for i in range(len(self.base_model._constraints) - 1, -1, -1):
            if self.base_model._constraints[i][0] == obj:
                self.base_model._constraints.pop(i)
                break


# constraint for ensuring pairs of variables are not equal. for example, a 
# PairwiseDiffConstraint on variables [a, b, c, d] would ensure that
# (a,b) != (c,d) in the final solution
class PairwiseDiffConstraint(Constraint):
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        v_pairs = [(variables[i - 1], variables[i]) for i in range(1, len(variables), 2)]

        seen = set()
        for v1, v2 in v_pairs:
            val1 = assignments.get(v1, Unassigned)
            val2 = assignments.get(v2, Unassigned)
    
            if val1 is not Unassigned and val2 is not Unassigned:
                prev_len = len(seen)
                seen.add((val1, val2))

                if prev_len == len(seen):
                    return False

            if forwardcheck:
                for v_pair in v_pairs:
                    i = -1
                    if v_pair[0] not in assignments and v_pair[1] in assignments:
                        i = 0
                    elif v_pair[0] in assignments and v_pair[1] not in assignments:
                        i = 1

                    if i != -1:
                        domain = domains[v_pair[i]]
                        for vals in seen:
                            if assignments[v_pair[1 - i]] == vals[1 - i] and vals[i] in domain:
                                domain.hideValue(vals[i])
                                if not domain:
                                    return False
        
        return True


# can run this to test preference model
if __name__=="__main__":
    # FORGETTING TEST - make sure locations can be remembered/forgotten such 
    #   that a candle cnanot be placed in a spot where a remembered candle 
    #   already has been
    model = PreferenceModel()
    cake_size = (random.randint(5, 25), random.randint(5, 25))
    print("creating  cake of size", cake_size)
    model.init_model(*cake_size)

    l0 = model.propose(0)
    l1 = model.propose(1)
    print("candle 0 at", l0, "candle 1 at", l1)

    # forcing a conflict by constraining 2 to be in 1s spot
    print("forcing candle 2 to go in candle 1's spot")
    model.candle_locs.append(([l1[0]], [l1[1]]))

    try:
        model.propose(2)
    except:
        print("could not place candle 2")

    print("forgetting location of candle 1")
    model.reset_locations()
    print("putting candle 2 at", model.propose(2))
    print("putting candle 1 at", model.propose(1))
    