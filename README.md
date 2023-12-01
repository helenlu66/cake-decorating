# cake-decorating-preference
## Install requirements with pip
```pip install -r requirements.txt```


##  Start a rest server at e.g. 8080
```python rest_server.py --port 8080```


## Running the control condition
```python control_experiment.py```

## Running the interactive preference learning condition
first, check `experiment_config.yaml` to change `user_name` to the participant's name. Sign up for an OpenAI account and get an OpenAI api key here: `https://platform.openai.com/api-keys`.

Set your `OPENAI_API_KEY` environment variable by running this in the command line in any terminal: `export OPENAI_API_KEY={your api key}`.

At last, navigate to this project's directory and run in the command line:
```python dialogue_experiment.py``` 