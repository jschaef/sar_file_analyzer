#!/usr/bin/python3

import streamlit as st
import redis
from config import Config



def get_redis_conn(decode=True):
    try:
        rs = redis.StrictRedis(host=Config.redis_host, port=Config.redis_port,
                               encoding="utf-8", decode_responses=decode)
        rs.ping()
        return rs
    except:
        return None

rs = get_redis_conn()
# for pickled connections we need connect with decode False
rs_b = get_redis_conn(decode=False)

def show_keys():
    klist = []
    for key in rs.scan_iter('*'):
        klist.append(key)
    return klist

def show_hash_keys(hash):
    return rs.hkeys(hash)

def delete_redis_keys():
    hash = st.selectbox('Select hash', show_keys())
    hash_keys = st.multiselect('Select n keys', show_hash_keys(hash))
    if st.button('Submit'):
        for hkey in hash_keys:
            rs.hdel(hash, hkey)

def delete_redis_key(rhash, rkey):
    try:
        rs.hdel(rhash, rkey)
    except:
        print(f'could not delete {rkey} from {rhash} on Redis server')

def redis_tasks(col):
    redis_actions = ['Delete Redis Keys']
    r_ph = col.empty()
    redis_sel = r_ph.selectbox('Redis Tasks', redis_actions, key="m_redis")
    if redis_sel == 'Delete Redis Keys':
        delete_redis_keys()
    redis_sel = r_ph.selectbox('Redis Tasks', redis_actions, default=None, key="m_redis")

def get_redis_val(rkey, decode=False, property=None):
    rs = get_redis_conn(decode=decode)
    if property:
        try:
            return rs.hget(rkey, property)
        except:
            return None
    else:
        try:
            return rs.get(rkey)
        except:
            return None

def set_redis_key(data, rkey, property=None, decode=False):
    """data -> dict or value
       key_pref, e.g user
       key, e.g jschaef -> compounds to user:jschaef
       bytes -> None or something, sets decode to False
    """
    rs = get_redis_conn(decode=decode)

    try:
        t_dict = {property:data}
        rs.hmset(rkey ,t_dict) 
    except:
        st.markdown(f'Could not write {rkey}')
    

def del_redis_key_property(rkey, property, decode=False):
    rs = get_redis_conn(decode=decode)
    if rs.exists(rkey, property):
        rs.hdel(rkey, property)

def show_redis_hash_keys(rkey):
    rs = get_redis_conn()
    return rs.hkeys(rkey)

    
