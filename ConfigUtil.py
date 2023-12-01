import argparse
import yaml

def get_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--port', type=str, required=False, help='Port of the rest server')
    parser.add_argument('--api_key', type=str, required=False, help='api key for llm')
    args = parser.parse_args()
    return args

def load_experiment_config(filename):
    with open(filename, 'r') as yaml_file:
        yaml_data = yaml_file.read()
    yaml_config = yaml.safe_load(yaml_data)
    return yaml_config