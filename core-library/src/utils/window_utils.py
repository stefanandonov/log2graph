from datetime import datetime, timedelta

import pandas as pd


def generate_time_windows(wtype, size, slide, min_logs_timestamp, max_logs_timestamp) -> pd.DataFrame:
    """
    Method that generates the needed tumbling/sliding time windows for logs based
    on the min and max timestamps of the logs.
    :param wtype: the type of the window, acceptable values are tumbling and sliding
    :param size: the size of the window in milliseconds
    :param slide: the size of the slide of the window in milliseconds, used only when wtype=='sliding'
    :param min_logs_timestamp: the minimum timestamp extracted from the logs. Should be a datetime object
    :param max_logs_timestamp: the maximum timestamp extracted from the logs. Should be a datetime object
    :return:
    windows_df (pandas DataFrame): A dataframe with two columns: 'start' and 'end' of the time windows
    """
    frequency = f"{size}L" if wtype == 'tumbling' else f"{slide}L"
    if wtype == "tumbling":
        start = int(int(min_logs_timestamp.timestamp() * 1000) / size) * size
    else:
        start = int(int(min_logs_timestamp.timestamp() * 1000 - size + slide) / slide) * slide
    start = datetime.utcfromtimestamp(int(start / 1000))
    print(start)
    windows = pd.date_range(start=start, end=datetime.now(), freq=frequency)
    windows_df = pd.DataFrame(windows, columns=['start'])
    windows_df = windows_df.drop(windows_df[windows_df['start'] + timedelta(milliseconds=1) > max_logs_timestamp].index)
    windows_df['end'] = windows_df.apply(lambda row: row['start'] + timedelta(milliseconds=size), axis=1)
    return windows_df


def generate_session_windows(logs: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(columns=['session_id'])
    if 'session_id' in logs.columns:
        unique_session_ids = logs['session_id'].unique()
        df['session_id'] = unique_session_ids
        df['session_id'] = df['session_id'].astype('str')
    return df