#!/usr/bin/python3

#from streamlit import cache as st_cache
import sys
import os
import streamlit as st
import pandas as pd
import time
import re
from altair_saver import save
from threading import Thread
from streamlit import cache as st_cache
from streamlit.report_thread import add_report_ctx
from config import Config
import sql_stuff
import download as dow


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

@st.cache(allow_output_mutation=True)
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

st.cache(allow_output_mutation=True)
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
        if len(header.split()) > 1:
            search_strings = header.split()
        else:
            search_strings = header.split()
        alias = sql_stuff.get_header_prop(search_strings, 'alias')
        if alias:
            aliases[header] = alias
        else:
            aliases[header] = header

    return aliases

def translate_aliases(field):
    '''
    takes a list of aliases and returns the related headers
    as a dictionary {alias:header,...}
    '''
    headers = {}
    for alias in field:
        header = sql_stuff.get_header_from_alias(alias)
        if not header:
            header = alias
        
        # refurbish whitespaces in db
        header = " ".join(header.split())
        headers[alias] = header
    return headers


###################################################
# Helpers regarding app organization
def get_selected_header(select_box_title, headers, col=None):
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

    selected = ph.selectbox(select_box_title, selected_sorted,)

    
    #retransform
    for key in aliases:
        if aliases[key] == selected:
            selected = key
            break
    return (selected, ph)


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
    #   print(f'{metric}:   {" ".join(mh_dict[metric]).rstrip()}')
        yield (metric, " ".join(mh_dict[metric]).rstrip())
    #return mh_dict

def metric_expander(prop, expand=False):
    description = sql_stuff.ret_metric_description(prop)
    exp_desc = f"{prop}"

    ph_expander = st.empty()
    my_expander = ph_expander.beta_expander(
        exp_desc, expanded=expand)
    with my_expander:
        if description:
            st.write(description)
        else:
            st.write(f'metric {prop} has no description at the moment')


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

def prepare_pd_data(data):
    threads = []
    pd_dict = {}
    for x in data:
        t = Thread(target=prepare_pd_threaded, args=(x, pd_dict))
        add_report_ctx(t)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
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
    ph_sel = col.empty()
    if col:
        ph_sel = col.empty()
        selection = ph_sel.selectbox('sar files', sar_files)
    else:
        selection = st.selectbox('sar files', sar_files)

    return selection


def diagram_expander(default_width, default_hight, text1, text2):
    st.markdown('___')
    dia_expander = st.beta_expander('Change Size')
    st.markdown('')
    with dia_expander:
        width = st.slider(text1,
            400, 1600, (1000), 200)
        hight = st.slider(text2,
            400, 1600, (600), 200)

        return width, hight

def rename_sar_file(file_path):
    os_details = extract_os_details(file_path)
    hostname = os_details[2].strip("(|)")
    date = os_details[3]
    date = date.replace('/','-')
    fshort_name = file_path.split("/")[-1]
    short_rename_name = f'{fshort_name}_{hostname}_{date}'
    try:
        renamed_name = f'{file_path}_{hostname}_{date}'
        os.system(f'mv {file_path} {renamed_name}')
        st.markdown(f'{fshort_name} has been renamed to {short_rename_name}')
        return short_rename_name
    except:
        print(f'file {file_path} could not be renamed to {renamed_name}')


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
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

if __name__ == '__main__':
    pass
