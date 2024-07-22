import pandas as pd
from datetime import timedelta
from nilmtk.tests.testingtools import data_dir
from os.path import join
import itertools
from collections import OrderedDict
import numpy as np
from nilmtk.consts import JOULES_PER_KWH
from nilmtk.measurement import measurement_columns, AC_TYPES
from nilmtk.utils import flatten_2d_list

from nilm_metadata import convert_yaml_to_hdf5
from os.path import join

MAX_SAMPLE_PERIOD = 30

MEASUREMENTS = [('power', 'active')]


TEST_METER = {'manufacturer': 'Test Manufacturer',
              'model': 'Random Meter',
              'sample_period': 1,
              'max_sample_period': MAX_SAMPLE_PERIOD,
              'measurements': []}

for col in MEASUREMENTS:
    TEST_METER['measurements'].append({
        'physical_quantity': col[0], 'type': col[1],
        'lower_limit': 0, 'upper_limit': 50000})

def create_smartme_hdf5(csv_filename, output_filename):
    N_METERS = 1

    store = pd.HDFStore(output_filename, 'w', complevel=9, complib='zlib')
    elec_meter_metadata = {}
    for meter in range(1, N_METERS + 1):
        key = 'building1/elec/meter{:d}'.format(meter)
        print("Saving", key)
        store.put(key, csv_filename, format='table')
        # elec_meter_metadata[meter] = {
        #     'device_model': TEST_METER['model'],
        #     'site_meter': True,
        #     'data_location': key
        # }

    # # Save dataset-wide metadata
    # store.root._v_attrs.metadata = {
    #     'dataset': {
    #         'contact': 'wenfei.huang@st.oth-regensburg.de/',
    #         'creators': "Wenfei, Huang",
    #         'description': 'A month of power data for 1 home.',
    #         'institution': 'Ostbayerische Technische Hochschule Regensburg',
    #         'long_name': 'The Reference Energy Disaggregation Data set',
    #         'name': 'SMARTME',
    #         'number_of_buildings': 1,
    #         'publication_date': 2023,
    #         'schema': 'https://github.com/nilmtk/nilm_metadata/tree/v0.2',
    #         'subject': 'Disaggregated power demand from domestic buildings.',
    #         'timezone': 'Europe/Berlin'
    #     },
    #     'meter_devices': {TEST_METER['model']: TEST_METER},
    # }
    # print(store.root._v_attrs.metadata)

    # # Building metadata
    # add_building_metadata(store, elec_meter_metadata)
    convert_yaml_to_hdf5('/Users/ken/Desktop/oth-regensburg-v1/metadata', store)

    

    store.flush()
    store.close()

def add_building_metadata(store, elec_meters, key='building1', appliances=[]):
    node = store.get_node(key)
    md = {
        'instance': 1,
        'elec_meters': elec_meters,
        'appliances': appliances
    }
    node._f_setattr('metadata', md)    
