import logging
import argparse
import yaml
from preferenceModel import PreferenceModel
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from llmConstraintsExtraction import ConstraintExtractor
from prompts import *
logger = logging.getLogger("rest_server")

class PreferenceModelQuery(Resource):
    def __init__(self, **kwargs):
        self.model = kwargs['preference_model']

    def post(self):
        """call the responsible methods for initializing preference model
        or for updating preference model

        Returns:
            json: the ID of the user's preference model
        """        
        request_content = request.get_json(force=True)
        command = self.find_field(request_content, 'command')
        if command == 'init':
            cake_dim_x = self.find_field(request_content, 'cake_dim_x')
            cake_dim_y = self.find_field(request_content, 'cake_dim_y')
            num_candles = self.find_field(request_content, 'num_candles')
            preference_model_id = self.model.init_model(cake_dim_x, cake_dim_y, num_candles)
            return jsonify({'preference model id':preference_model_id})
        else:
            constraint = self.find_field(request_content, 'constraint')
            preference_model_id = self.model.update_model(constraint)
            return jsonify({'preference model id':preference_model_id})
       
    
    def get(self):
        """call the responsible methods for getting the location for the current candle
        given the current candle's index

        Returns:
            json: the (x, y) of the current candle
        """        
        request_content = request.get_json(force=True)
        candle_idx = self.find_field(request_content, "candle_index")
        x, y = self.model.propose(candle_idx)
        result = jsonify({'x':x, 'y': y})
        return result
    
    def find_field(self, content, field):
        value = None
        try:
            value = content[field]
        except KeyError:
            logger.exception("MissingRequiredFieldException: ", field)
        return value
    
class ConstraintExtractorQuery(Resource):
    def __init__(self, **kwargs):
        self.model:ConstraintExtractor = kwargs['constraint_extractor']

    def post(self):
        """call the constraint extractor to extract a list of constraints
        Returns:
            json: the ID of the user's preference model
        """        
        request_content = request.get_json(force=True)
        
        robot_question = self.find_field(request_content, 'robot_question')
        human_answer = self.find_field(request_content, 'human_answer')
        # first classify whether human response is valid
        if not self.model.classify(robot_question=robot_question, human_answer=human_answer):
            return jsonify({"next_action":"redirect"})
        constraints_list = self.model.extract_constraints(robot_question=robot_question, human_answer=human_answer)
        return jsonify({"constraints":constraints_list})
    
    def find_field(self, content, field):
        value = None
        try:
            value = content[field]
        except KeyError:
            logger.exception("MissingRequiredFieldException: ", field)
        return value
    

class Server:
    def __init__(self, port, preference_model:PreferenceModel, constraint_extractor:ConstraintExtractor):
        self.port = port
        self.preference_model = preference_model
        self.constraint_extractor = constraint_extractor
        
    def run(self):
        app = Flask(__name__)
        api = Api(app)
        api.add_resource(PreferenceModelQuery, '/preference', resource_class_kwargs={'preference_model': self.preference_model})
        api.add_resource(PreferenceModelQuery, '/constraint', resource_class_kwargs={'constraint_extractor': self.constraint_extractor})
        app.run(debug=True, port=self.port, host="0.0.0.0", threaded=True)

def get_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--port', type=str, required=True, help='Port of the rest server')
    parser.add_argument('--api_key', type=str, required=True, help='api key for llm')
    args = parser.parse_args()
    return args

def load_experiment_config(filename):
    with open(filename, 'r') as yaml_file:
        yaml_data = yaml_file.read()
    yaml_config = yaml.safe_load(yaml_data)
    return yaml_config

# run this to test rest server setup
if __name__=="__main__":
    args = get_args()   
    exp_config = load_experiment_config('experiment_config.yaml')
    preference_model = PreferenceModel()
    preference_model.init_model(cake_dim_x=exp_config['surface_width'], cake_dim_y=exp_config['surface_len'], num_candles=exp_config['num_candles'])
    constraint_extractor = ConstraintExtractor(prompts_setup=prompts_setup, task_setup=exp_config, api_key=args.api_key)
    server = Server(args.port, preference_model= preference_model, constraint_extractor=constraint_extractor)
    server.run()