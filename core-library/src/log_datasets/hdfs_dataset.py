import datetime
import re
import time
from os import mkdir
from os.path import exists
from os.path import join

import gdown
import pandas as pd

from log_datasets.dataset import Dataset
from utils.Drain import LogParser


class HDFSDataset(Dataset):
    def __init__(self, data_folder_path = "../data"):
        Dataset.__init__(self, data_folder_path)

    @staticmethod
    def __find(params):
        for x in eval(params):
            if "blk" in x:
                match = re.search('(.*)(blk_(.+))(.*)', x)
                return match.group(2)
        return None

    def load_logs(self):

        # download raw logs
        output_path = f"{self.data_folder_path}/hdfs/HDFS.log"
        url = 'https://drive.google.com/uc?id=1yVWq065qjyKM7TcAF1aIkfc5jVyPPcQM'
        if not exists(output_path):
            mkdir(join(f"{self.data_folder_path}/hdfs"))
            gdown.download(url, output_path, quiet=False)

        if not exists(f"{self.data_folder_path}/hdfs/HDFS.log_structured.csv"):
            input_dir = f"{self.data_folder_path}/hdfs/"
            output_dir = f"{self.data_folder_path}/hdfs/"
            log_file = 'HDFS.log'
            log_format = "<Date> <Time> <Pid> <Level> <Component>: <Content>"

            # Regular expression list for optional preprocessing (default: [])
            regex = [
                r'blk_(|-)[0-9]+',  # block id
                r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)',  # IP
                r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$',  # Numbers
            ]
            st = 0.5  # Similarity threshold
            depth = 2  # Depth of all leaf nodes

            parser = LogParser(log_format, indir=input_dir, outdir=output_dir, depth=depth, st=st, rex=regex)
            parser.parse(log_file)

        self.logs = pd.read_csv(f"{self.data_folder_path}/hdfs/HDFS.log_structured.csv")
        self.logs = self.logs.iloc[1:, :]
        dates = {81109: "2008-11-9", 81110: "2008-11-10", 81111: "2008-11-11"}
        self.logs['Date'] = self.logs['Date'].apply(lambda x: dates[x])
        self.logs['Time'] = self.logs['Time'].apply(
            lambda x: datetime.datetime.strptime(str(x).zfill(6), "%H%M%S").strftime("%H:%M:%S"))
        self.logs['timestamp'] = pd.to_datetime(self.logs['Date'] + " " + self.logs['Time'])
        self.logs['EventId'] = self.logs['EventId'].astype('str')
        self.logs['block_id'] = self.logs['ParameterList'].apply(lambda x: self.__find(x))
        self.logs['block_id'] = self.logs['block_id'].astype('str')
        self.logs.sort_values(['timestamp'], inplace=True)

        self.logs = self.logs[['timestamp', 'EventId', 'block_id']]
        self.logs.rename(columns={'timestamp': 'timestamp', 'EventId': 'event_id', 'block_id': 'session_id'}, inplace=True)

    def load_event_templates(self):
        output_path = f'{self.data_folder_path}/hdfs/HDFS.log_templates.csv'
        self.templates = pd.read_csv(output_path)

    def assign_event_id_to_logs(self):
        """
        This dataset already has event IDs attached to the logs
        :return:
        """
        pass

    def print_sample(self):
        print(self.logs.head(20))



if __name__ == '__main__':
    dataset = HDFSDataset()
    start = time.time()
    dataset.load_logs()
    dataset.load_event_templates()
    dataset.print_sample()
    end = time.time()
    print(f"The HDFS dataset needs {end-start} seconds to load up")
    start = time.time()
    print(dataset.create_graphs_for_session_windows())
    end = time.time()
    print(f"The HDFS dataset needs {end-start} seconds to create session windows")
