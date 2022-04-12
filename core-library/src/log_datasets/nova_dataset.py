from os import mkdir
from os.path import exists

import gdown
import pandas as pd

from log_datasets.dataset import Dataset


class NovaDataset(Dataset):
    def __init__(self, data_folder_path="../data"):
        Dataset.__init__(self, data_folder_path)

    def load_logs(self):
        output_path = f'{self.data_folder_path}/nova/logs.csv'
        url = 'https://drive.google.com/uc?id=19BIXVfWmyGcGUG9eVLOIFLldaL4dxKjb'
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
        url = 'https://drive.google.com/uc?id=1AhImrZ2wLProAHzmAp_M9C3dGnfOZWRo'
        if not exists(output_path):
            gdown.download(url, output_path, quiet=False)

    def assign_event_id_to_logs(self):
        """
        This dataset already has event IDs attached to the logs
        :return:
        """
        pass


if __name__ == '__main__':
    dataset = NovaDataset()
    dataset.load_logs()
    dataset.load_event_templates()
    print(dataset.create_graphs("tumbling", 6000, 0, 1))
