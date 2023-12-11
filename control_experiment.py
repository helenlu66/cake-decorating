# this file runs the control experiment
#%%
import pandas as pd
from ActionAgent import ActionAgent
from interface import CakeDecorator
from rest_server import load_experiment_config

if __name__=="__main__":
    
    # read experiment config
    #%%
    exp_config = load_experiment_config('experiment_config.yaml')
    user_name = exp_config['user_name']
    filename = f'user_interface_results/{user_name}.csv'
   
    # #%%
    # record 3 examples to csv
    gui = CakeDecorator()
    cakes = gui.run()
    gui.write_to_csv(fp=filename)

    #%%
    # get average
    
    df = pd.read_csv(filename)
    avg_columns = [col for col in df.columns if col.startswith('avg')]
    
    print(df[avg_columns])
    print(df[avg_columns].iloc[-1])
    # Get the last row as tuples of (avg_x, avg_y)
    last_row_tuples = [(df.loc[df.index[-1], f'avg_x{i}'], df.loc[df.index[-1], f'avg_y{i}']) for i in range(len(avg_columns)//2)]
    print(last_row_tuples)
    agent = ActionAgent(server_host=exp_config['server_host'], server_port=exp_config['server_port'])
    for i in range(exp_config['task_setup']['num_candles']):
        agent.pickAndPlaceObjAtBoardCoords(obj=f'candle{i}', coords=last_row_tuples[i])
    agent.goToPose(pose='prepare')
        
# %%