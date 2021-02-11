#!/usr/bin/python3
import sys
import pickle
import os
from pathlib import Path
import redis_mng
import streamlit as st
from sar_explore_threading import initialize, create_data_collection
from config import Config
from helpers import prepare_pd_data
import dataframe_funcs as ddf


def data_cooker(file, username):
    content = initialize(file)
    sar_data = create_data_collection(content, file, username)
    os_details = sar_data.pop()
    pds = prepare_pd_data(sar_data)
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

def set_data_frames(file_name, user_name):
    """
    Write structure containing data frames to pickle and redis
    Replaces the further pickle/redis data 
    """
    st.info('It might be the first time that this file has been opened.\n\
        Such it needs some time to serialize the data. Next time will be much faster.')
    sar_structure = data_cooker(file_name, user_name)
    # save to pickle
    real_path = Path(file_name)
    pickle_file = Path(f'{file_name}.df')
    if not pickle_file.exists():
        pickle.dump(sar_structure, open(pickle_file, 'wb'))
    
    # save to redis
    rs = redis_mng.get_redis_conn()
    if rs:
        r_item = f"{Config.rkey_pref}:{user_name}"
        file_name = file_name.split('/')[-1]
        file_name_df = f'{file_name}_df'
        p_obj = redis_mng.get_redis_val(
            r_item, decode=False, property=file_name_df)
        if not p_obj:
            try:
                redis_mng.set_redis_key(pickle.dumps(sar_structure), r_item, property=file_name_df,
                                        decode=False)
                print(f'{r_item}, {file_name_df} saved to redis')
            except:
                print(f'could not connect to redis server or save {file_name_df} to redis server')
    #JS!
    os.system(f'rm -rf {real_path}')


def get_data_frames(file_name, user_name):
    """
    Load structure containing data frames from redis or pickle
    """
    # load from redis
    rs = redis_mng.get_redis_conn(decode=False)
    pickle_file = Path(f'{file_name}.df')
    full_path = file_name
    if rs:
        r_item = f"{Config.rkey_pref}:{user_name}"
        file_name = file_name.split('/')[-1]
        file_name_df = f'{file_name}_df'
        p_obj = redis_mng.get_redis_val(
            r_item, decode=False, property=file_name_df)
        if p_obj:
            sar_structure = pickle.loads(p_obj)
            print(f'{r_item}, {file_name_df} loaded from redis')
        elif  pickle_file.exists():
            sar_structure = pickle.load(open(pickle_file, 'rb'))
            try:
                redis_mng.set_redis_key(pickle.dumps(sar_structure), r_item, property=file_name_df,
                                        decode=False)
                print(f'{r_item}, {file_name_df} saved to redis')
            except:
                print(
                    f'could not connect to redis server or save {file_name_df} to redis server')

        else:
            sar_structure = data_cooker(full_path, user_name)
            if sar_structure:
                set_data_frames(full_path, user_name)
                #os.system(f'rm -rf {full_path}')
    elif pickle_file.exists():
        sar_structure = pickle.load(open(pickle_file, 'rb'))
    else:
        sar_structure = data_cooker(full_path, user_name)
        if sar_structure:
            set_data_frames(full_path, user_name)
            #os.system(f'rm -rf {full_path}')

    return sar_structure


if __name__ == '__main__':    
    try:
        sf = sys.argv[1]
    except(IndexError):
        print(f'Please specify a sar file')
        sys.exit(1)
        sf = 'sar31'

    content = initialize(sf)
    sar_data = create_data_collection(content, sf)
    # dictionary
    pds = prepare_pd_data(sar_data)
    print(pds)
