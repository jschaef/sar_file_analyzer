#!/usr/bin/python3

import sys
import os
import streamlit as st
import pandas as pd
import time
import re
import asyncio
from datetime import datetime
#from streamlit.script_runner.script_run_context import add_script_run_ctx
from altair_saver import save
from threading import Thread
from config import Config
import sql_stuff
import download as dow
import dataframe_funcs as dff
import layout_helper as lh

reg_linux_restart = re.compile('LINUX RESTART', re.IGNORECASE)

class configuration(object):
    def __init__(self, config_d):
        self.conf_d = config_d
    def set_conf(self,key,val):
        self.conf_d[key]=val
    def get_conf(self,key):
        return self.conf_d[key]
    def update_conf(self, upd_d):
        self.conf_d.update(upd_d)
    def get_dict(self):
        return self.conf_d

def extract_os_details(file):
    with open(file, 'r') as sar_file:
        for nr, line in enumerate(sar_file):
            if "Linux" in line:
                return line.split()

def get_osdetails(file):
    os_details = " ".join(extract_os_details(file))
    return os_details

def merge_headers(header_field):
    # initialize with first field
    first = set(header_field[0])
    def f(x, y):
        return x.intersection(y)
    for field in header_field[1:]:
        res = f(first, field)
        first = res

    arr = sorted([x for x in first])
    if 'all' in arr:
        arr.remove('all')
        # sort numeric values
        tmp_arr = [int(x) for x in arr if str(x).isnumeric()]
        if tmp_arr:
            tmp_arr.sort()
            arr = [str(x) for x in tmp_arr]
        arr.insert(0,'all')
    return(arr)


def check_sub_items(headers, multi_sarfile_dict):
    '''
    If provided fields of headers have subitems check if there 
    are empty sets of unions for these subitems (resulting from
    merge_headers). If yes remove these headers from headers list 
    '''
    items_dict = {}
    for sar_file in multi_sarfile_dict.keys():
        items_dict[sar_file] = {}
        for header in headers:
            items_dict[sar_file][header] = []
            for item in multi_sarfile_dict[sar_file][header].keys():
                if item != 'generic':
                    items_dict[sar_file][header].append(item)
                else:
                    items_dict[sar_file].pop(header)

    # transfer to list
    items_field = [ items_dict[key] for key in items_dict.keys()]

    for header in items_field[0].keys():
        for field in items_field[1:]:
            f_index = items_field.index(field)
            # compare is empty, remove header
            if not merge_headers([items_field[0][header], items_field[f_index][header]]):
                if header in headers:
                    headers.remove(header)
    
    return headers

def translate_headers(field):
    '''
    takes list of headers , db lookup for the aliases
    search for header belonging to aliases
    returns dictionary {header:alias, header:alias, ..., n}
    if header not in db, put the original header as key and value
    '''
    aliases = {}
    for header in field:
        if reg_linux_restart.search(header):
            continue
        search_strings = header.split()
        alias = sql_stuff.get_header_prop(search_strings, 'alias')
        if alias:
            aliases[header] = alias
        else:
            aliases[header] = header

    return aliases

#@st.cache(allow_output_mutation=True)
def translate_aliases(alias_field, sar_headers):
    '''
    takes a list of aliases and returns the related headers
    as a dictionary {alias:header,...}
    '''
    headers = {}
    for alias in alias_field:
        header = sql_stuff.get_header_from_alias(alias)
        if not header:
            header = alias
        if header not in sar_headers: 
            header = aliases_2_header(sar_headers, header)      
        # refurbish whitespaces in db
        header = " ".join(header.split())
        headers[alias] = header
    return headers

# In case there is no alias because header differs a little bit
# from headers saved in DB
def aliases_2_header(header_field, alias_header):
    result_dict = {}
    result_header = ""
    for header in header_field:
        result_dict[header] = 0
        for metric in alias_header.split():
            if metric in header.split():
                result_dict[header] += 1 
    tmp_count = 0
    for header in result_dict.keys():
        if result_dict[header] > tmp_count:
           tmp_count = result_dict[header]
           result_header = header
    return result_header
###################################################
# Helpers regarding app organization
def get_selected_header(select_box_title, headers, col=None, key=None):
    '''
    select_box_title -> title for the selectbox
    headers -> field with headers
    '''
    # convert headers into aliases
    aliases = translate_headers(headers)
    selected_sorted = [a for a in aliases.values()]
    selected_sorted.sort()

    if not col:
        ph = st.sidebar.empty()
    else:
        ph = col.empty()

    selected = ph.selectbox(select_box_title, selected_sorted,key=key)

    
    #retransform
    for key in aliases:
        if aliases[key] == selected:
            selected = key
            break
    return (selected, ph)

@st.experimental_singleton
def get_metric_desc_from_manpage():
    metric_reg = re.compile('^\.IP\s+(.*$)')
    content = re.compile('^[^\.].*$')

    with open('sar.1', 'r') as mfile:
        mh_dict = {}
        m_hit = 0
        metric = ''
        linefield = mfile.readlines()

        for line in linefield[129:]:
            if metric_reg.search(line):
                hit = metric_reg.match(line)
                metric = hit.group(1)
                if metric:
                    mh_dict[metric] = []
                    m_hit = 1
            elif m_hit == 1 and content.search(line):
                mh_dict[metric].append(line)
            elif not content.search(line):
                m_hit= 0

    for metric in mh_dict.keys():
        yield (metric, " ".join(mh_dict[metric]).rstrip())

def metric_expander(prop, expand=False, col=None):
    col = col if col else st
    description = sql_stuff.ret_metric_description(prop)
    exp_desc = f"{prop}"

    ph_expander = st.empty()
    my_expander = ph_expander.expander(
        exp_desc, expanded=expand)
    with my_expander:
        if description:
            col.write(description)
        else:
            col.write(f'metric {prop} has no description at the moment')


def create_data_frame(data, index, heading):
    df = pd.DataFrame(data, index, heading)
    empty_cols = [col for col in df.columns if df[col].isnull().all()]
    # Drop these columns from the dataframe
    df.drop(empty_cols,
            axis=1,
            inplace=True)
    return(df)

def prepare_pd_threaded(x, pd_dict):
    # x comes from (for x in data)
    # multithreading could be done here
    # generic counts as multitype also in this loop
    multi_types = x[1].keys()
    for mtype in multi_types:
        mtype_dict = {}
        row_indexes = []
        df_data = []
        if mtype != 'generic':
            headings = x[0].split()[1:]
        else:
            headings = x[0].split()
        for measure in x[1][mtype]:
            row_index = measure[0]
            row_data = measure[1:]
            #some times there are more columns as expected due to some wrong sar insertions
            if len(headings) != len(row_data):
                print(row_index, "XXXX", headings)
                sys.exit(1)
            row_indexes.append(row_index)
            #row_data = map(float,row_data)
            for index in range(len(row_data)):
                try:
                    row_data[index] = float(row_data[index])
                except ValueError:
                    # need a correct error handling here
                    None

            df_data.append(row_data)

        pd_id = (" ".join(headings))
        my_pd = create_data_frame(df_data, row_indexes, headings)
        # a mapping between the different measure types (headers) and the qualifier for the web interface needs to be done
        mtype_dict = my_pd
        if not pd_dict.get(pd_id, None):
            pd_dict[pd_id] = {}
        pd_dict[pd_id][mtype] = mtype_dict

async def prepare_pd_threaded_v1(x, pd_dict):
    # x comes from (for x in data)
    # multithreading could be done here
    # generic counts as multitype also in this loop
    multi_types = x[1].keys()
    for mtype in multi_types:
        mtype_dict = {}
        row_indexes = []
        df_data = []
        if mtype != 'generic':
            headings = x[0].split()[1:]
        else:
            headings = x[0].split()
        for measure in x[1][mtype]:
            row_index = measure[0]
            row_data = measure[1:]
            #some times there are more columns as expected due to some wrong sar insertions
            if len(headings) != len(row_data):
                print(row_index, "XXXX", headings)
                sys.exit(1)
            row_indexes.append(row_index)
            #row_data = map(float,row_data)
            for index in range(len(row_data)):
                try:
                    row_data[index] = float(row_data[index])
                except ValueError:
                    # need a correct error handling here
                    None

            df_data.append(row_data)

        pd_id = (" ".join(headings))
        my_pd = create_data_frame(df_data, row_indexes, headings)
        # a mapping between the different measure types (headers) and the qualifier for the web interface needs to be done
        mtype_dict = my_pd
        if not pd_dict.get(pd_id, None):
            pd_dict[pd_id] = {}
        pd_dict[pd_id][mtype] = mtype_dict

async def prepare_pd_data(data):
    pd_dict = {}
    tasks = []
    for x in data:
        if not isinstance(x, str):
            tasks.append(asyncio.create_task(prepare_pd_threaded_v1(x, pd_dict)))
    for t in tasks:
        await t
    return(pd_dict)

def measure_time(prop='start', start_time=None):
    if prop == 'start':
        start_time = time.perf_counter()
        return(start_time)
    else:
        end = time.perf_counter()
        st.write(f'process_time: {round(end-start_time, 4)}')

def get_sar_files(user_name, col=None):
    sar_files = [x for x in os.listdir(f'{Config.upload_dir}/{user_name}') \
        if os.path.isfile(f'{Config.upload_dir}/{user_name}/{x}') ]
    sar_files_pre = [x for x in sar_files if not x.endswith('.df') ]
    sar_files = [x.rstrip('.df') for x in sar_files if x.endswith('.df')]
    sar_files.extend(sar_files_pre)
    if not col:
        col1, col2, col3 = st.columns([2,1, 1])
        col1.write(''), col3.write('')
        selection = col2.selectbox('sar files', sar_files)
    else:
        selection = col.selectbox('sar files', sar_files)
    return selection


def diagram_expander(default_width, default_hight, text1, text2, col=None):
    st.markdown('___')
    col = col if col else st
    dia_expander = col.expander('Change Diagram Size')
    st.markdown('')
    with dia_expander:
        width = st.slider(text1,
            400, 1600, (1200), 200)
        hight = st.slider(text2,
            400, 1600, (400), 200)

        return width, hight

def font_expander(default_size, title, description, col=None, key=None):
    col = col if col else st
    font_expander = col.expander(title)
    st.markdown('')
    with font_expander:
        size = st.select_slider(description,
                          range(8,25), value=default_size, key=key)

        return size

def rename_sar_file(file_path, col=None):
    col = col if col else st
    os_details = extract_os_details(file_path)
    hostname = os_details[2].strip("(|)")
    date = os_details[3]
    date = date.replace('/','-')
    today = datetime.today().strftime("%Y-%m-%d")
    base_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)
    rename_name = f'{today}_{hostname}_{date}'
    renamed_name = f'{dir_name}/{rename_name}'
    try:
        os.system(f'mv {file_path} {dir_name}/{rename_name}')
        col.info(f'{base_name} has been renamed to {rename_name}\n    \
            which means: <date_of_upload>\_<hostname>\_<sar file creation date>')
        return rename_name
    except:
        col.warning(f'file {file_path} could not be renamed to {renamed_name}')

# - not possible @st.experimental_memo
def pdf_download(file, dia):
    my_file = file
    save_dir = os.path.dirname(file)
    if not os.path.exists(save_dir):
        os.system(f'mkdir -p {save_dir}')
    if os.path.exists(my_file):
        os.system(f'rm {my_file}')

    save(dia, my_file)
    filename = Config.pdf_name
    with open(my_file, 'rb') as f:
        s = f.read()
    download_button_str = dow.download_button(
        s, filename, f'Click here to download PDF')
    st.markdown(download_button_str, unsafe_allow_html=True)

def set_stile(df, restart_rows=None):
    def color_null_bg(val):
        is_null = val == 0
        return ['background-color: "",' if v else '' for v in is_null]
    
    def color_null_fg(val):
        is_null = val == 0
        return ['color: "",' if v else '' for v in is_null]

    if restart_rows:
        multi_index = [ x.index[0] for x in restart_rows ]
    else:
        multi_index = []
    sub_index = [ x for x in df.index if x not in multi_index ]
    df = df.style.apply(highlight_ind, dim='min',
        subset=pd.IndexSlice[sub_index, :]).apply(highlight_ind,
         subset=pd.IndexSlice[sub_index,:]).\
         apply(highlight_min_ind, subset=pd.IndexSlice[sub_index, :]).\
        apply(highlight_max_ind, subset=pd.IndexSlice[sub_index, :]).\
        apply(color_null_bg, subset=pd.IndexSlice[sub_index, :]).\
        apply(color_null_fg, subset=pd.IndexSlice[sub_index, :]).\
        format(precision=4)
    if restart_rows:
        df = df.apply(color_restart, subset=pd.IndexSlice[multi_index, :])
   
    return(df)

def highlight_ind(data,  dim='max', color='black'):
    '''
    highlight the maximum in a Series or DataFrame
    '''
    attr = f'color: {color}'
    if data.ndim == 1:

        if dim == 'max':
            quant = data == data.max()

        elif dim == 'min':
            quant = data == data.min()
        
        return [attr if v else '' for v in quant]


def highlight_max_ind(data, color='lightblue'):
    '''
    highlight the maximum in a Series yellow.
    '''
    is_max = data == data.max()
    return [f'background-color: {color}' if v else '' for v in is_max]


def highlight_min_ind(data, color='yellow'):
    '''
    highlight the minimum in a Series yellow.
    '''
    is_min = data == data.min()

    return [f'background-color: {color}' if v else '' for v in is_min]

def color_restart(data):
    result = data == 0.00
    return ['color: red'  for v in result]

def extract_restart_header(headers):
    return [header for header in headers if reg_linux_restart.search(
        header) ]

def restart_headers(df, os_details, restart_headers=None, display=True):

    # check and remove duplicates
    dup_check = df[df.index.duplicated()]
    if not dup_check.empty:
        df = df[~df.index.duplicated(keep='first')].copy()

    if restart_headers:
        rdf = df.copy()
        rdf, new_rows = dff.insert_restarts_into_df(os_details, rdf,
            restart_headers)
        if display:
            st.write(set_stile(rdf, restart_rows=new_rows))
            col1, *_ = lh.create_columns(6, [1, 1, 0, 0,0,0])
            code1 = '''max:\tlightblue\nmin:\tyellow'''
            code2 = f'''\nreboot:\t{" ,".join([restart.split()[-1] for restart in restart_headers])}'''
            col1.code(code1 + code2)
        else:
            return(set_stile(rdf, restart_rows=new_rows))
    else:
        if display:
            st.write(set_stile(df))
            code2 = ""
            code1 = '''max:\tlightblue\nmin:\tyellow'''
            col1, *_ = lh.create_columns(6, [1, 1, 0, 0,0,0])
            col1.code(code1 + code2)
            col1.text('')
            col1.text('')
        else:
            return(set_stile(df))


def restart_headers_v1(df, os_details, restart_headers=None):
    if restart_headers:
        rdf = df.copy()
        rdf, new_rows = dff.insert_restarts_into_df(os_details, rdf,
                      restart_headers)
        return set_stile(rdf, restart_rows=new_rows)
        #code1 = f'''\nreboot:\t{" ,".join([restart.split()[-1] for restart in restart_headers])}'''
    else:
        return set_stile(df)



if __name__ == '__main__':
    pass
