import time
from os import makedirs
from os.path import exists

import gdown
import pandas as pd

from log_datasets.dataset import Dataset
from utils import Drain


class BGLDataset(Dataset):
    def __init__(self, data_folder="../data"):
        Dataset.__init__(self, data_folder)

    def load_logs(self):
        output_file = f'{self.data_folder_path}/bgl/unparsed/logs.log'
        # 'https://drive.google.com/uc?id=1CtUwkOA_flGk7IaHQIL_bPalURdKMzTR'
        url = 'https://drive.google.com/uc?id=1DBEppXnGACcvEKJ018mUTRREMILyYPCV'

        if not exists(f'{self.data_folder_path}/bgl/'):
            makedirs(f'{self.data_folder_path}/bgl/')

        if not exists(f'{self.data_folder_path}/bgl/unparsed'):
            makedirs(f'{self.data_folder_path}/bgl/unparsed')
            gdown.download(url, output_file, quiet=False)

        # Replace the commas with semicolons
        # commas cause problems with DRAIN and writing to csv 
        log_file = f'{self.data_folder_path}/bgl/unparsed/processed_logs.log'

        lf = open(log_file, 'a')

        with open(output_file) as of:
            for line in of:
                lf.write(line.replace(',', ';'))

        lf.close()

        # Parse the logs with DRAIN
        log_file = 'processed_logs.log'
        input_dir = f'{self.data_folder_path}/bgl/unparsed/'
        output_dir = f'{self.data_folder_path}/bgl/'
        log_format = "<Label> <Timestamp> <Date> <Node> <Time> <NodeRepeat> <Type> <Component> <Level> <Content>"

        parser = Drain.LogParser(log_format, indir=input_dir, outdir=output_dir)
        parser.parse(log_file)

        self.logs = pd.read_csv(output_dir + 'processed_logs.log_structured.csv')
        self.logs['Time'] = pd.to_datetime(self.logs['Time'], format='%Y-%m-%d-%H.%M.%S.%f')
        self.logs.sort_values(['Time'])

        self.logs = self.logs[['Time', 'EventId']]
        self.logs.rename(columns={'Time': 'timestamp', 'EventId': 'event_id'}, inplace=True)
        print(self.logs.head())
        print(len(self.logs))

    def load_event_templates(self):
        """
        Drain has already extracted the event templates, do nothing.
        """
        pass

    def assign_event_id_to_logs(self):
        """
        BGL already has event ids, do nothing.
        """
        pass

if __name__ == '__main__':
    dataset = BGLDataset()
    start = time.time()
    dataset.load_logs()
    end = time.time()
    print (f"{end-start} seconds for loading the dataset")
    dataset.load_event_templates()

    start = time.time()
    print(dataset.create_graphs("tumbling", 3600000, 0, 1)) # one hour time window
    end = time.time()
    print(f"{end-start} seconds for creation of the time windows")
