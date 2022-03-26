import datetime
import re
import time
from os import mkdir
from os.path import exists
from os.path import join

import gdown
import pandas as pd
from datasets.dataset import Dataset


class HDFSDataset(Dataset):
    def __init__(self):
        Dataset.__init__(self)

    @staticmethod
    def __find(params):
        for x in eval(params):
            if "blk" in x:
                match = re.search("(.*)(blk_(.+))(.*)", x)
                return match.group(2)
        return None

    def load_logs(self):
        output_path = "../data/hdfs/logs.csv"
        # https://drive.google.com/file/d/1CPoIS5-ICN_lXUKv-adcY977A_AN4B3u/view?usp=sharing
        url = 'https://drive.google.com/uc?id=1CPoIS5-ICN_lXUKv-adcY977A_AN4B3u'
        if not exists(output_path):
            mkdir(join("../data/hdfs"))
            gdown.download(url, output_path, quiet=False)

        self.logs = pd.read_csv(output_path)
        self.logs = self.logs.iloc[1:, :]
        dates = {81109: "2008-11-9", 81110: "2008-11-10", 81111: "2008-11-11"}
        self.logs['Date'] = self.logs['Date'].apply(lambda x: dates[x])
        self.logs['Time'] = self.logs['Time'].apply(
            lambda x: datetime.datetime.strptime(str(x).zfill(6), "%H%M%S").strftime("%H:%M:%S"))
        self.logs['timestamp'] = pd.to_datetime(self.logs['Date'] + " " + self.logs['Time'])
        self.logs['EncodedEvent'] = self.logs['EncodedEvent'].astype('str')
        self.logs['block_id'] = self.logs['ParameterList'].apply(lambda x: self.__find(x))
        self.logs.sort_values(['timestamp'], inplace=True)

        self.logs = self.logs[['timestamp', 'block_id', 'EncodedEvent']]
        self.logs.rename(columns={'timestamp': 'timestamp', 'block_id': 'session_id', 'EncodedEvent': 'event_id'},
                         inplace=True)
        print(self.logs.head())
        print(len(self.logs))

    def load_event_templates(self):
        output_path = r'D:\finki\log2graph\core\datasets\temps.csv'
        url = 'https://drive.google.com/uc?id=1v9t126uUxcfKKlGihw5OaxWurdKZcK70'
        if not exists(output_path):
            gdown.download(url, output_path, quiet=False)

    def assign_event_id_to_logs(self):
        """
        This dataset already has event IDs attached to the logs
        :return:
        """
        pass


if __name__ == '__main__':
    dataset = HDFSDataset()
    dataset.load_logs()
    dataset.load_event_templates()
    start = time.time()
    print(dataset.create_graphs("tumbling", 600000, 0, 1))
    end = time.time()
    print(end - start)
