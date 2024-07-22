import pandas as pd
import numpy as np
from functools import reduce
from copy import deepcopy
import os
from os.path import join, isdir, isfile
from os import listdir
import re
import os
import glob
from sys import stdout
from nilmtk.utils import get_datastore
from nilmtk.datastore import Key
from nilmtk.timeframe import TimeFrame
from nilmtk.measurement import LEVEL_NAMES
from nilmtk.utils import get_module_directory, check_directory_exists
from nilm_metadata import convert_yaml_to_hdf5, save_yaml_to_datastore

"""
TODO:
* The bottleneck appears to be CPU.  So could be sped up by using
  multiprocessing module to use multiple CPU cores to load SMART channels in
  parallel.
"""


def convert_smartme(smartme_path, output_filename, format='HDF'):
    """
    Parameters
    ----------
    smart_path : str
        The root path of the SmartMe low_freq dataset.
    output_filename : str
        The destination filename (including path and suffix).
    format : str
        format of output. Either 'HDF' or 'CSV'. Defaults to 'HDF'
    """

    # def measurement_mapping():
    #     return [('power', 'active')]

    # Open DataStore
    store = get_datastore(output_filename, format, mode='w')

    # Convert raw data to DataStore
    _convert(smartme_path, store, 'Europe/Berlin')

    s = '/Users/ken/Desktop/oth-regensburg-v1/metadata'

    # Add metadata
    save_yaml_to_datastore(s, store)
    store.close()

    print("Done converting SMART to HDF5!")


def _convert(input_path, store, tz, sort_index=True):
    """
    Parameters
    ----------
    input_path : str
        The root path of the SmartMe dataset.
    store : DataStore
        The NILMTK DataStore object.
    tz : str
        Timezone e.g. 'Europe/Berlin'
    sort_index : bool
    """


    check_directory_exists(input_path)

    houses = _find_all_houses(input_path)
    months = []

    # Iterating though all Homes
    b_cnt = 0
    for house_id in houses:
        print("b_cnt", b_cnt)
        b_cnt = b_cnt + 1
        print('Loading Home:', house_id, end='... ')
        stdout.flush()
        months = _find_month(input_path, house_id)
        meters_paths_csv = []
        df_all_months = pd.DataFrame()

        for m in months:
            mains_df = pd.DataFrame()
            meters_paths_csv = _find_all_csv_paths(input_path, house_id, m)
            data_frames = []
            if not meters_paths_csv:
                continue
            else:
                # k = 1

                for path in meters_paths_csv:
                    # 1.Concat csv files of all meters in each year, to get all
                    # appliances in 1 dataframe per year
                    temp_df = pd.read_csv(path, index_col=0)
                    # if k == 1:
                    #     k = 0
                    #     if 'use [kW]' in temp_df.columns:
                    #         mains_df = temp_df['use [kW]']
                    #     elif 'Usage [kW]' in temp_df.columns:
                    #         mains_df = temp_df['Usage [kW]']
                    #     if 'Date & Time' in temp_df.columns:
                    #         date_time_df = temp_df['Date & Time']

                   # Preprocess/clean dataframe by removing unusabe columns
                    # temp_df = _preprocess_csv(temp_df)
                    data_frames.append(temp_df)

                df_month = reduce(
                    lambda left,
                    right: left.join(
                        right,
                        lsuffix='_1',
                        rsuffix='_2'),
                    data_frames)
                # Add columns 'Date & Time' and 'use [kW]'
                # df_year.insert(0, 'Date & Time', date_time_df)
                # df_year.insert(1, 'use', mains_df)
                # Append all years data to 1 dataframe
                df_all_months = df_all_months.append(
                    df_month, ignore_index=True, sort=False)
        # Change index to datetime format
        df_all_months['ValueDate'] = pd.to_datetime(
            df_all_months['ValueDate'], utc=True)
        # df_all_years.set_index('Date & Time', inplace=True)
        df_all_months.set_index('ValueDate', inplace=True)
        df_all_months = df_all_months.tz_convert(tz)
        df_all_months.index.name = None

        # Append key value pairs to DataStore
        chan_id = 0
        for col in df_all_months.columns:
            chan_id += 1
            print(chan_id, end=' ')
            stdout.flush()
            key = Key(building=b_cnt, meter=chan_id)
            chan_df = pd.DataFrame(df_all_months[col])
            chan_df.columns = pd.MultiIndex.from_tuples([('power', 'active')])
            chan_df.columns.set_names(LEVEL_NAMES, inplace=True)

            store.put(str(key), chan_df)
        print()


def _preprocess_csv(temp_df):
    """
    Returns
    -------
    preprocessed/cleaned dataframe
    """
    if 'Solar [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='Solar [kW]')
    if 'Grid [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='Grid [kW]')
    if 'Usage [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='Usage [kW]')
    if 'use [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='use [kW]')
    if 'gen [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='gen [kW]')
    if 'Generation [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='Generation [kW]')
    if 'grid [kW]' in temp_df.columns:
        temp_df = temp_df.drop(columns='grid [kW]')
    if 'Date & Time' in temp_df.columns:
        temp_df = temp_df.drop(columns='Date & Time')
    return temp_df


def _find_all_houses(input_path):
    """
    Returns
    -------
    list of characters (house instances)
    """
    '''dir_names = [p for p in listdir(input_path) if isdir(join(input_path, p))]
    return _matching_str(dir_names, r'^Home(\D)$')'''

    items = os.listdir(input_path)
    subfolders = [item for item in items if os.path.isdir(os.path.join(input_path, item))]
    subfolders_cnt = len(subfolders)

    temp = []

    for i in range(1, subfolders_cnt+1):
        temp.append(str(i))

    return temp


def _find_month(input_path, house_id):
    """
    Returns
    -------
    list of months (per Home)
    """
    month_names = [
        p for p in listdir(
            input_path +
            '/' +
            'Wohnung' +
            house_id) if isdir(
            join(
                input_path +
                '/' +
                'Wohnung' +
                house_id,
                p))]
    return month_names


def _find_all_csv_paths(input_path, house_id, month):
    """
    Returns
    -------
    list of csv paths of data (with respect to a house and a particular month )
    """
    house_month_path = (input_path + '/' + 'Wohnung' + house_id + '/' + month)
    extension = 'csv'
    os.chdir(house_month_path)
    csv_paths = glob.glob(house_month_path + '/*.csv')

    # txt_paths = glob.glob(house_month_path + '/*.txt')

    paths = []
    # Take only those csv files which have 30 minutes as sample period
    for csv_path in csv_paths:
        paths.append(csv_path)
        # f = open(txt_path, "r")
        # lines = f.readlines()
        # f.close()
        # if '30' in lines[-2]:
        #     name_temp = lines[0].strip('\n')
        #     paths.append(
        #         house_year_path +
        #         '/' +
        #         name_temp +
        #         '_' +
        #         year +
        #         '.csv')

    return paths


'''def _matching_str(strings, regex):
    """Uses regular expression to select and then extract an integer from
    strings.

    Parameters
    ----------
    strings : list of strings
    regex : string
        Regular Expression.  Including one group.  This group is used to
        extract the integer from each string.

    Returns
    -------
    list of ints
    """
    strs = []
    p = re.compile(regex)
    for string in strings:
        m = p.match(string)
        if m:
            str_temp = m.group(1)
            strs.append(str_temp)
    strs.sort()
    return strs'''
