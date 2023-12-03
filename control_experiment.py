# this file runs the control experiment
import pandas as pd
from interface import CakeDecorator
from rest_server import load_experiment_config

if __name__=="__main__":
    #%%
    # read experiment config
    exp_config = load_experiment_config('experiment_config.yaml')
    user_name = exp_config['user_name']
    filename = f'user_interface_results/{user_name}.csv'
   
    #%%
    # record 5 examples to csv
    gui = CakeDecorator()
    cakes = gui.run()
    gui.write_to_csv(fp=filename)

    #%%
    # get average
    
    df = pd.read_csv(filename)
    avg_columns = [col for col in df.columns if col.startswith('avg')]
    
    print(df[avg_columns])
    # TODO: send the average coords to DIARC's goal manager, there should be 3 sets of coords
# %%
