import logging
import argparse
from PreferenceModel import PreferenceModel
from flask import Flask, request, jsonify
from flask_restful import Resource, Api

logger = logging.getLogger("rest_server")

class PreferenceModelQuery(Resource):
    def __init__(self, **kwargs):
        self.model = kwargs['preference_model']

    def post(self):
        """Helen TODO: call the responsible methods for initializing preference model
        or for updating preference model

        Returns:
            json: the ID of the user's preference model
        """        
        request_content = request.get_json(force=True)
        result = jsonify({'response':None})
        return result
    
    def get(self):
        """Helen TODO: call the responsible methods for getting the location for the current candle
        given the current candle's index

        Returns:
            json: the (x, y) of the current candle
        """        
        request_content = request.get_json(force=True)
        result = jsonify({'response':None})
        return result
    

    
    def find_field(self, content, field):
        value = None
        try:
            value = content[field]
        except KeyError:
            logger.exception("MissingRequiredFieldException: ", field)
        return value
    

class Server:
    def __init__(self, port, model:PreferenceModel):
        self.port = port
        self.model = model
        
    def run(self):
        app = Flask(__name__)
        api = Api(app)
        api.add_resource(PreferenceModelQuery, '/preference', resource_class_kwargs={'preference_model': self.model})
        
        app.run(debug=True, port=self.port, host="0.0.0.0", threaded=True)

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