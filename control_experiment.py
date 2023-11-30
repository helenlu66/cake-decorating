# this file runs the control experiment
import pandas as pd
from interface import CakeDecorator
from rest_server import load_experiment_config

if __name__=="__main__":
    # read experiment config
    exp_config = load_experiment_config('experiment_config.yaml')
    
    # record 5 examples to csv
    gui = CakeDecorator()
    cakes = gui.run()
    gui.write_to_csv()
    filename = 'interface_results.csv'

    # get average
    df = pd.read_csv(filename, usecols=['avg_x{candle_index}'.format(candle_index=exp_config['experiment_num']), 'avg_y{candle_index}'.format(candle_index=exp_config['experiment_num'])])
    
    # TODO: send the average coords to DIARC's goal manager, there should be 3 sets of coords