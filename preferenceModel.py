import uuid
import ast
import dill
from pathlib import Path
from constraint import Domain, Problem, Unassigned, MinConflictsSolver, Constraint, InSetConstraint
from copy import deepcopy
import random
class PreferenceModel:
    def __init__(self, user_name:str) -> None:
        self.model:Problem = Problem(MinConflictsSolver())
        self.id = uuid.uuid4()
        self.save_path = Path(__file__).parent / 'user_models' / user_name
        self.user_name = user_name
        self.constraints:list[str] = [] # save a list of string repr of the constraints
        self.candle_locs = {} # coordinates that already have candles in them

    
    def set_up_model(self, task_setup:dict):
        """ set up the base model with constraints that will generalize across task specifications
        """
        self.model = Problem(MinConflictsSolver())
        self.surface_width = task_setup['surface_width']
        self.surface_height = task_setup['surface_height']
        self.num_objs = task_setup['num_candles']
       
        # add the variables here with range of values based on cake surface dimensions
        # adding an x and y variable for each candle
        x_dom = Domain([i for i in range(self.surface_width)])
        y_dom = Domain([i for i in range(self.surface_height)])

        # candle location x, y vars and surface_width, surface_height as vars
        vars = []
        for n in range(self.num_objs):
            vars.append(f'x{n}')
            vars.append(f'y{n}')
            self.model.addVariable(f'x{n}', x_dom)
            self.model.addVariable(f'y{n}', y_dom)
        self.model.addVariable('surface_width', [self.surface_width])
        self.model.addVariable('surface_height', [self.surface_height])
        # adding constraint that no two candles can have the same position
        self.model.addConstraint(PairwiseDiffConstraint(), vars)

        return self.id
    
    
    def change_setup(self, task_setup:dict):
        """Change the cake dimension

        Args:
            task_setup (dict): task setup up specification
        """
        # set up a new model
        self.set_up_model(task_setup=task_setup)

        # forget previously set candle positions
        self.reset_locations()

        # go through stored constraints and apply each to the new self.model
        for constraint in self.constraints:
            self._update_model(constraint)
        
    def record_and_apply_constraint(self, constraint:str):
        """record the constraint and update the preference model based on constraint""" 
        
        try:
            self._update_model(constraint=constraint)
            self.constraints.append(constraint)
        except:
            # ignore this constraint
            print("something went wrong in update_model")
  
        return self.id
    
    def _update_model(self, constraint:str):
        """update the preference model based on constraints. I recommend looking at python libraries
        for constraint satisfaction problems such as https://pypi.org/project/python-constraint/ 

        Args:
            constraint string: a logic expression such as x0 == x1 == x2 meaning that the 3 candles are on the same horizontal line, 
            x0 < surface_width / 2 meaning that the first candle is to the left
        """

        def extract_parameters(lambda_str):
            try:
                # Parse the lambda function string into an AST (Abstract Syntax Tree)
                tree = ast.parse(lambda_str)

                # Extract parameters from the arguments of the lambda function
                parameters = [arg.arg for arg in tree.body[0].value.args.args]

                return parameters
            except SyntaxError as e:
                print(f"Error parsing lambda function: {e}")
                return None
        
        try:
            lambda_func = eval(constraint)
            vars = extract_parameters(constraint)
            self.model.addConstraint(lambda_func, vars)
        except:
            # ignore this constraint
            print("preferenceModel update_constraint constraint didn't parse: " + constraint)
  
        
    
    def propose(self, candle_num:int):
        """propose a target location (x, y) for the candle_num'th candle

        Args:
            candle_num int: the index (0-based) of the candle
        Returns: (x, y)
        """

        # get solution
        sln = self.model.getSolution()
        if sln is None:
            # propose random loc
            print("proposing random location")
            return (random.randint(0, self.surface_width), random.randint(0, self.surface_height))
    
        loc = (sln[f'x{candle_num}'], sln[f'y{candle_num}'])
        return loc
    
    def record_loc(self, candle_num:int, loc:tuple):
        """record the location for the given candle. Usually called when the human user accepts the proposed location.

        Args:
            candle_num (int): the index (0-based) of the candle
            loc (tuple): (x, y) of candle
        """
        # store candle location in candle locs
        self.candle_locs[candle_num] = loc

        # add the constraint to exclude configurations in which candle_num is not in loc
        self.model.addConstraint(InSetConstraint([loc[0]]), [f'x{candle_num}'])
        self.model.addConstraint(InSetConstraint([loc[1]]), [f'y{candle_num}'])

    
    def reset_locations(self):
        """forget previously proposed candle locations

        Args:
            candle_nums int list: the indices (0-based) of the candles to 
                forget placements of. defaults to all candles.
        Returns: (x, y)
        """

        self.candle_locs = {}
    
    def remove_constraint(self, obj):
        for i in range(len(self.base_model._constraints) - 1, -1, -1):
            if self.base_model._constraints[i][0] == obj:
                self.base_model._constraints.pop(i)
                break
    
    def save_to_dill(self):
        """Save the PreferenceModel object to a pickle file.

        Args:
            filename (str): The filename for the pickle file.
        """
        with open(self.save_path, 'wb') as file:
            dill.dump(self, file)
        return self.save_path


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


def load_from_dill(filepath) -> PreferenceModel:
    """Load a PreferenceModel object from a pickle file.

    Args:
        filename (str): The filename of the pickle file.

    Returns:
        PreferenceModel: The loaded PreferenceModel object.
    """
    with open(filepath, 'rb') as file:
        return dill.load(file)
        
# can run this to test preference model
if __name__=="__main__":
# TESTING SQUARE CAKE SETUP
    model = PreferenceModel(user_name='Helen')
    model.set_up_model(task_setup = {
        'surface_width':20,
        'surface_height':20,
        'num_candles':3
    })
    model.record_and_apply_constraint('lambda x0, x1, x2: x0 == x1 == x2')
    proposed = model.propose(0)
    model.record_loc(0, proposed)
    proposed = model.propose(1)
    proposed = model.propose(1)
    model.record_loc(1, proposed)
    proposed = model.propose(2)
# TEST CHANGING SETUP
    model.change_setup(task_setup={
        'surface_width':10,
        'surface_height':30,
        'num_candles':3
    })
    proposed = model.propose(0)
    model.record_loc(0, proposed)
    proposed = model.propose(1)
    proposed = model.propose(1)
    model.record_loc(1, proposed)
    proposed = model.propose(2)
# TEST SAVING AND LOADING
    model.reset_locations()
    filepath = save_to_dill(model, Path(__file__).parent / 'user_models' / 'Helen')
    new_model = load_from_dill(filepath=filepath)
    proposed = new_model.propose(0)
    new_model.record_loc(0, proposed)
    proposed = new_model.propose(1)
    new_model.record_loc(1, proposed)
    proposed = new_model.propose(2)
    new_model.record_loc(2, proposed)
# FORGETTING TEST - make sure locations can be remembered/forgotten such 
    #   that a candle cnanot be placed in a spot where a remembered candle 
    #   already has been
    model = PreferenceModel()
    cake_size = (random.randint(5, 25), random.randint(5, 25))
    print("creating  cake of size", cake_size)
    task_setup = {
        'surface_width':cake_size[0],
        'surface_height':cake_size[1],
        'num_candles':3
    }


    l0 = model.propose(0)
    model.record_loc(candle_num=0, loc=l0)
    l1 = model.propose(1)
    model.record_loc(candle_num=1, loc=l1)
    print("candle 0 at", l0, "candle 1 at", l1)

    # forcing a conflict by constraining 2 to be in 1s spot
    print("forcing candle 2 to go in candle 1's spot")
    model.record_loc(candle_num=2, loc=l1)

    try:
        model.propose(2)
    except:
        print("could not place candle 2")

    print("forgetting location of candle 1")
    model.reset_locations()
    print("putting candle 2 at", model.propose(2))
    print("putting candle 1 at", model.propose(1))
    