import os
import argparse
import yaml
from utils.agent_configurations import AgentConfigurationBuilder
from utils.rest_server import Server
from MetacognitiveAgent import MetacognitiveQAAgent

def get_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--server', type=str, required=True, help='choose VERA, SAMI, or Skillsync server to start')
    parser.add_argument('--port', type=str, required=True, help='Port of the rest server')
    parser.add_argument('--request_api_key', type=str, required=True, help='api key used to verify the received requests')
    parser.add_argument('--llm_api_key', type=str, required=False, help='api key for the llm used in chains')
    parser.add_argument('--embeddings_api_key', type=str, required=False, help='api key for the embeddings used in docsearch, fill if not in config file')
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction, required=False, help='change verbosity of the chain')
    args = parser.parse_args()

    return args

def get_config(filename):
    with open(filename) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

if __name__=="__main__":
    args = get_args()

    curr_file_path = os.path.abspath(__file__)
    file_path = os.path.join(os.path.dirname(curr_file_path), f'configs/{args.server}_config.yaml')
    
    agentConfigurationBuilder = AgentConfigurationBuilder(file_path, llm_api_key=args.llm_api_key, embeddings_api_key=args.embeddings_api_key, verbose=args.verbose)
    mcqa_config = agentConfigurationBuilder.build_config()    
    
    mcqa_agent = MetacognitiveQAAgent(mcqa_config, args.embeddings_api_key)
    server = Server(args.server, args.port, mcqa_agent, api_key=args.request_api_key)
    server.run()
    