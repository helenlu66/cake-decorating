import logging
from preferenceModel import get_args
from flask import Flask, request, jsonify
from flask_restful import Resource, Api

logger = logging.getLogger("rest_server")

class PreferenceModel(Resource):
    def __init__(self, **kwargs):
        self.model = kwargs['preference model']

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
        api.add_resource(PreferenceModel, '/preference', resource_class_kwargs={'preference model': self.model})
        
        app.run(debug=True, port=self.port, host="0.0.0.0", threaded=True)

# run this to test rest server setup
if __name__=='__main__':
    args = get_args()   
    
    preference_model = PreferenceModel()
    server = Server(args.port, preference_model)
    server.run()