import logging
import argparse
import sys
import os
from flask import Flask, request, jsonify
from flask_restful import Resource, Api

logger = logging.getLogger("rest_server")

class QA(Resource):
    def __init__(self, **kwargs):
        self.api_key = kwargs['api_key']
        self.name = kwargs['agent_name']
        self.mcqa_agent.MetacognitiveQAAgent = kwargs['mcqa_agent']

    def post(self):
        request_content = request.get_json(force=True)
        
        # verify api key if one was set
        if self.api_key and self.api_key != self.find_field(request_content, 'api_key'):
            return {'message':'access denied due to api key mismatch'}, 403

        # pull required documents from request content and assign them to mcqa agent
        episodic_knowledge = self.find_field(request_content, 'Episodic_Knowledge')
        self.update_mc_agent_episodic_knowledge(episodic_knowledge)
        
        # construct input dictionary to mcqa agent
        input_variables_dicts = self.mcqa_agent.get_input_variables()
        for input_variables_dict in input_variables_dicts:
            for key in input_variables_dict['input_variables']:
                # ignore 'input_documents' since these are handled by docsearch
                if key == 'input_documents':
                    continue
                input_variables_dict['input_variables'][key] = self.find_field(request_content, key)
        
        # get answer
        reply = self.mcqa_agent.run()
        result = jsonify({'response':reply})
        return result
    
    def update_mc_agent_episodic_knowledge(self, episodic_knowledge):
        self.mcqa_agent.add_episodic_knowledge(episodic_knowledge)

    
    def find_field(self, content, field):
        value = None
        try:
            value = content[field]
        except KeyError:
            logger.exception("MissingRequiredFieldException: ", field)
        return value
    
class VERA(QA):
    def __init__(self, **kwargs):
        kwargs['agent_name'] = 'VERA'
        super().__init__(**kwargs)
    
    def update_mc_agent_episodic_knowledge(self, episodic_knowledge):
        self.mcqa_agent.add_episodic_knowledge(episodic_knowledge['graph model'])

class SAMI(QA):
    def __init__(self, **kwargs):
        kwargs['agent_name'] = 'SAMI'
        super().__init__(**kwargs)

class Skillsync(QA):
    def __init__(self, **kwargs):
        kwargs['agent_name'] = 'Skillsync'
        super().__init__(**kwargs)
class Server:
    def __init__(self, server, port, mcqa_agent, api_key=None):
        self.server = server
        self.port = port
        self.mcqa_agent = mcqa_agent
        self.api_key = api_key
        
    def run(self):
        app = Flask(__name__)
        api = Api(app)
        
        if self.server.lower() == 'vera':
            api.add_resource(VERA, '/vera/ask_question', resource_class_kwargs={'api_key': self.api_key, 'mcqa_agent': self.mcqa_agent})
        if self.server.lower() == 'sami':    
            api.add_resource(SAMI, '/sami/ask_question', resource_class_kwargs={'api_key': self.api_key, 'mcqa_agent': self.mcqa_agent})
        if self.server.lower() == 'skillsync':
            api.add_resource(Skillsync, '/skillsync/ask_question', resource_class_kwargs={'api_key': self.api_key, 'mcqa_agent': self.mcqa_agent})
        app.run(debug=True, port=self.port, host="0.0.0.0", threaded=True)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--server', type=str, required=True, help='choose VERA, SAMI, or Skillsync server to start')
    parser.add_argument('--port', type=str, required=True, help='Port of the rest server')
    parser.add_argument('--request_api_key', type=str, required=True, help='api key used to verify the received requests')
    parser.add_argument('--llm_api_key', type=str, required=False, help='api key for the llm used in chains')
    args = parser.parse_args()

    curr_file_path = os.path.abspath(__file__)
    file_path = os.path.join(os.path.dirname(curr_file_path), f'../configs/{args.server}_config.yaml')

    agentConfigurationBuilder = AgentConfigurationBuilder(file_path, llm_api_key=args.llm_api_key, embeddings_api_key=args.embeddings_api_key, verbose=args.verbose)
    mcqa_config = agentConfigurationBuilder.build_config()     
    
    mcqa_agent = MetacognitiveQAAgent(mcqa_config)
    server = Server(args.server, args.port, mcqa_agent, api_key=args.request_api_key)
    server.run()