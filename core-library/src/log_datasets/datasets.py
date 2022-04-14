import datetime
import re
from os import mkdir, makedirs
from os.path import exists, join

import gdown
import pandas as pd

from log_datasets.dataset import Dataset
from utils.Drain import LogParser


class HDFSDataset(Dataset):
    def __init__(self, data_folder_path="../data"):
        Dataset.__init__(self, data_folder_path)

    @staticmethod
    def __find(params):
        for x in eval(params):
            if "blk" in x:
                match = re.search('(.*)(blk_(-*\d*))(.*)', x)
                return match.group(2)
        return None

    def load_logs(self):

        # download raw logs
        output_path = f"{self.data_folder_path}/hdfs/HDFS.log"
        # 189R1qzhTMLQYo2llwse5F-InsFxBbxr-
        url = 'https://drive.google.com/uc?id=189R1qzhTMLQYo2llwse5F-InsFxBbxr-'
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
        self.logs.rename(columns={'timestamp': 'timestamp', 'EventId': 'event_id', 'block_id': 'session_id'},
                         inplace=True)

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


class BGLDataset(Dataset):
    def __init__(self, data_folder_path="../data"):
        Dataset.__init__(self, data_folder_path)

    def load_logs(self):
        output_file = f'{self.data_folder_path}/bgl/unparsed/logs.log'
        url = 'https://drive.google.com/uc?id=1qlYZB26biKt7jlxL8YmIXHlqqeMDv-iX'

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

        parser = LogParser(log_format, indir=input_dir, outdir=output_dir)
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


class NovaDataset(Dataset):
    def __init__(self, data_folder_path="../data"):
        Dataset.__init__(self, data_folder_path)

    def load_logs(self):
        output_path = f'{self.data_folder_path}/nova/logs.csv'
        url = 'https://drive.google.com/uc?id=1Lf-kmpf6OP1WpKT_KkZeUT745CV168gb'
        if not exists(output_path):
            mkdir(f"{self.data_folder_path}/nova")
            gdown.download(url, output_path, quiet=False)

        self.logs = pd.read_csv(output_path)
        self.logs = self.logs.iloc[1:, :]
        self.logs['test_id'] = self.logs['test_id'].astype('int')
        self.logs['time_hour'] = pd.to_datetime(self.logs['time_hour'])
        self.logs.sort_values(['time_hour'])

        self.logs = self.logs[['test_id', 'time_hour', 'EventId']]
        self.logs.rename(columns={'time_hour': 'timestamp', 'EventId': 'event_id'}, inplace=True)
        print(self.logs.head())
        print(len(self.logs))

    def load_event_templates(self):
        output_path = f'{self.data_folder_path}/nova/event_templates.csv'
        url = 'https://drive.google.com/uc?id=1SZqgSvUhvwZTofKslo21U3z2VEBbU17w'
        if not exists(output_path):
            gdown.download(url, output_path, quiet=False)

    def assign_event_id_to_logs(self):
        """
        This dataset already has event IDs attached to the logs
        :return:
        """
        pass


if __name__ == '__main__':
    dataset = BGLDataset("../../data")
    dataset.initialize_dataset()
    graphs = dataset.create_graphs(window_type='sliding', window_size=60000, window_slide=30000, test_id=1, include_last=False)
    for graph in graphs:
        print (graph)
