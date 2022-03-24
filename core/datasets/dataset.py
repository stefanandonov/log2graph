import datetime
from abc import abstractmethod, ABC
from typing import Mapping, Union, List

import pandas as pd

from utils.graphs_util import create_graph_as_dict
from utils.window_utils import generate_time_windows


class Dataset(ABC):
    """
    Class for representation of a Dataset. The Dataset should be stored as a Pandas Data Frame
    with the following 4 columns:
    - timestamp
    - session_id (probably only possible in the HDFS dataset)
    - test_id (probably applicable only for the NOVA dataset)
    - event_id (string)
    """

    def __init__(self):
        self.logs = pd.DataFrame()

    @abstractmethod
    def load_logs(self):
        """
        Method that will load the corresponding logs dataset and store it into self.logs
        This method should be able to download the dataset from some line (on the first run of the application) i.e
        check first if we currently have the dataset in some location, and if we don't, download it.
        :return: void
        """
        pass

    @abstractmethod
    def load_event_templates(self):
        """
        Method that will perform the DRAIN events extraction
        :return:
        """
        pass

    @abstractmethod
    def assign_event_id_to_logs(self):
        """
        Method that will assign an event_id
        :return:
        """
        pass

    def create_graphs(self, window_type, window_size, window_slide, test_id, include_last=True) \
            -> List[Mapping[str, Union[datetime.datetime, Mapping[str, Mapping[str, int]]]]]:
        # TODO add support for session windows as well
        """
        :param window_type: string that represents the window type, possible values are: session, tumbling, sliding
        :param window_size: the size of the window in milliseconds
        :param window_slide: the size of the slide of the window in milliseconds
        :param test_id: an integer that represent the test_id of a experiment. applicable only for the nova dataset
        :param include_last: A bool value that represents whether the last event ID should be included in the graph generation
        :return: result: list of dictionaries where each dictionary represents the data for one graph created by this
        method. Each dictionary has three key,value pairs. The first two (str,datetime.datetime) represent the start
        and the end of the window for which the graph was generated and the third one `graph_dic` represents the dictionary
        representation of the graph as obtained from the create_graph_as_dict method.
        """
        logs = self.logs[self.logs['test_id'] == test_id] if 'test_id' in self.logs.columns else self.logs
        min_timestamp = logs['timestamp'].min()
        max_timestamp = logs['timestamp'].max()
        windows_df = generate_time_windows(window_type, window_size, window_slide, min_timestamp, max_timestamp)
        windows_df['event_ids'] = windows_df.apply(lambda window: get_events_ids_for_window(logs, window), axis=1)
        print(windows_df.head())

        result = []
        for index, row in windows_df.iterrows():
            result.append({
                'start': row['start'],
                'end': row['end'],
                'graph_dict': create_graph_as_dict(event_ids=row['event_ids'].split(','), include_last=include_last)
            })

        return result


def get_events_ids_for_window(logs_df, window):
    return ",".join(list(logs_df[
                             (logs_df['timestamp'] >= window['start'])
                             & (logs_df['timestamp'] < window['end'])
                             ]['event_id']))
