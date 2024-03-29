#!/usr/bin/python3
import sys
import pickle
import os
from pathlib import Path
import redis_mng
import streamlit as st
import asyncio
from datetime import datetime
from sar_explore_threading import return_main
from config import Config
from helpers import prepare_pd_data
import dataframe_funcs as ddf

def data_cooker(file):
    sar_data = return_main(file)
    os_details = sar_data.pop()
    pds = asyncio.run(prepare_pd_data(sar_data))
    # replace index (strings) by datetime objects 
    for key in pds.keys():
        for df in pds[key].keys():
            final_df = ddf.df_reset_date(pds[key][df], os_details)
            pds[key][df] = final_df
    pds['os_details'] = os_details
    return(pds)

def data_cooker_multi(file, sar_data_dict, username):
    pds = get_data_frames(file, username)
    sar_data_dict[file] = pds
    return [file, pds]

def set_data_frames(file_name, user_name, sar_structure):
    """
    Write structure containing data frames to pickle and redis
    Replaces the further pickle/redis data 
    """
    base_name = os.path.basename(file_name)
    st.info(f'It might be the first time that {base_name} has been opened.\n\
        Such it needs some time to serialize the data. Next time will be much faster.')
    # save to pickle
    real_path = Path(file_name)
    pickle_file = Path(f'{file_name}.df')
    if not pickle_file.exists():
        pickle.dump(sar_structure, open(pickle_file, 'wb'))
    
    # save to redis
    rs = redis_mng.get_redis_conn()
    if rs:
        r_item = f"{Config.rkey_pref}:{user_name}"
        file_name_df = f'{base_name}_df'
        p_obj = redis_mng.get_redis_val(
            r_item, decode=False, property=file_name_df)
        if not p_obj:
            try:
                redis_mng.set_redis_key(pickle.dumps(sar_structure), r_item, property=file_name_df,
                                        decode=False)
                print(
                    f'{r_item}, {file_name_df} saved to redis at {datetime.now().strftime("%m/%d/%y %H:%M:%S")}')
            except:
                print(f'could not connect to redis server or save {file_name_df} to redis server')
    os.system(f'rm -rf {real_path}')


def get_data_frames(file_name, user_name):
    """
    Load structure containing data frames from redis or pickle
    """
    # load from redis
    rs = redis_mng.get_redis_conn(decode=False)
    pickle_file = Path(f'{file_name}.df')
    full_path = file_name
    basename = os.path.basename(file_name)
    if rs:
        r_item = f"{Config.rkey_pref}:{user_name}"
        file_name_df = f'{basename}_df'
        p_obj = redis_mng.get_redis_val(
            r_item, decode=False, property=file_name_df)
        if p_obj:
            sar_structure = pickle.loads(p_obj)
            print(f'{r_item}, {file_name_df} loaded from redis at {datetime.now().strftime("%m/%d/%y %H:%M:%S")}')
        elif  pickle_file.exists():
            sar_structure = pickle.load(open(pickle_file, 'rb'))
            try:
                redis_mng.set_redis_key(pickle.dumps(sar_structure), r_item, property=file_name_df,
                                        decode=False)
                print(f'{r_item}, {file_name_df} saved to redis at {datetime.now().strftime("%m/%d/%y %H:%M:%S")}')
            except:
                print(
                    f'could not connect to redis server or save {file_name_df} to redis server')

        else:
            sar_structure = data_cooker(full_path)
            if sar_structure:
                set_data_frames(full_path, user_name, sar_structure)
    elif pickle_file.exists():
        sar_structure = pickle.load(open(pickle_file, 'rb'))
    else:
        st.info('no redis server configured, hence data will be saved/retrieved to/from disk')
        sar_structure = data_cooker(full_path)
        if sar_structure:
            set_data_frames(full_path, user_name, sar_structure)

    return sar_structure


if __name__ == '__main__':    
    try:
        sf = sys.argv[1]
    except(IndexError):
        print(f'Please specify a sar file')
        sys.exit(1)
        sf = 'sar31'

    sar_data = return_main(sf)
    pds = asyncio.run(prepare_pd_data(sar_data))
    print(pds)
