from re import sub
import helpers
import streamlit as st
from config import Config as config
import layout_helper as lh
import dataframe_funcs as dff
from config import Config
def create_metric_menu(cols, multi_sar_dict, rand_file, headers, os_details, reboot_headers):
    """ 
    Creates ...
    """
    collect_field = []
    chart_field = []
    key_pref = 's_metrics'
    col_2 = cols[1]
    col_3 = cols[2]
    col_1 = cols.pop(0)
    sub_item_list = []
    counter = 0
    selected_1, ph_1 = helpers.get_selected_header(
            'Header', headers, col=col_1, key=f'{key_pref}{counter}')
    number_cols = len(multi_sar_dict[rand_file][selected_1].keys())
    #max_cols = config.max_metric_header
    max_cols = config.max_metric_header if number_cols >= config.max_metric_header else number_cols
    number_cols_display = number_cols 
    # reduce the maximal number of selectboxes
    if number_cols > max_cols:
        number_cols = max_cols
    index = int(number_cols/2)
    device_count = col_3.selectbox(f'How many devices to compare? Max {max_cols} of {number_cols_display}',[x for x in range(1,number_cols +1)], index=index)
    if number_cols >= device_count:
        number_cols = device_count
    cols_per_line = config.cols_per_line
    # check if there are selectboxes < cols_per_line left
    even_lines = int(number_cols/cols_per_line) 
    remaining_cols = number_cols % cols_per_line
    empty_cols = cols_per_line - remaining_cols
    if even_lines == 0:
        even_lines = 1
        remaining_cols = 0
    # handle first selectbox
    st.markdown('___')
    pcols = st.columns(cols_per_line)
    col_1 = pcols[0]
    sub_item_1 = col_1.selectbox('Choose devices', [key for key in
             multi_sar_dict[rand_file][selected_1].keys()], key=f'sub{key_pref}')
    
    # for layout indentation
    if number_cols == 1:
        for index in range(1, cols_per_line):
            pcols[index].write('')
        
    properties = list(multi_sar_dict[rand_file][selected_1][sub_item_1].columns)
    prop = col_2.selectbox(
        'metric', properties)
    
    collect_field, chart_field = build_device_dataframes(headers, multi_sar_dict, selected_1, 
        sub_item_1, prop, chart_field, collect_field, stats=1, os_details=os_details, reboot_headers=reboot_headers)

    sub_item_list.append(sub_item_1)
    for line in range(even_lines):
        # cols_per_line -1 in line 0 because first column has been used above
        if line == 0:
            pcols.pop(0)
        else:
            pcols = st.columns(cols_per_line)
        # more than cols_per_line found
        if  number_cols >= cols_per_line:
            for index in range(len(pcols)):
                col=pcols[index]
                counter += 1
                sub_item = display_select_boxes(col, multi_sar_dict, rand_file, selected_1, sub_item_list, key_pref, counter)
                collect_field, chart_field = build_device_dataframes(headers, multi_sar_dict, selected_1, 
                    sub_item, prop, chart_field, collect_field, stats=1, os_details=os_details, reboot_headers=reboot_headers)
        # less than cols_per_line found
        elif number_cols < cols_per_line and number_cols >1:
            pcols.append(st.columns(1)[0])
            for index in range(number_cols -1):
                sub_item = display_select_boxes(pcols[index], multi_sar_dict, rand_file, selected_1, sub_item_list, key_pref, counter)
                collect_field, chart_field = build_device_dataframes(headers, multi_sar_dict, selected_1, 
                    sub_item, prop, chart_field, collect_field, stats=1, os_details=os_details, 
                    reboot_headers=reboot_headers)
                for nindex in range(1, empty_cols +1):
                    nindex = cols_per_line - nindex -1
                    # for layout indentation
                    pcols[nindex].write('')

    if remaining_cols:
        pcols = st.columns(cols_per_line)
        for col in range(remaining_cols):
            counter += 1
            wcol = pcols[col]
            sub_item = display_select_boxes(wcol, multi_sar_dict, rand_file, selected_1, sub_item_list, key_pref, counter)
            collect_field, chart_field = build_device_dataframes(headers, multi_sar_dict, selected_1, 
                sub_item, prop, chart_field, collect_field, stats=1, os_details=os_details, reboot_headers=reboot_headers)
            # for layout indentation
            for nindex in range(1, empty_cols +1):
                nindex = cols_per_line - nindex
                pcols[nindex].write('')

    
    return chart_field, collect_field, prop

def build_diff_metrics_menu(multi_sar_dict, headers, rand_file,  cols, os_details, reboot_headers):
    counter = 0
    collect_field = []
    chart_field = []
    key_pref = 'd_metrics'
    max_cols = config.max_header_count
    cols_per_line = config.cols_per_line
    h_aliases_dict = helpers.translate_headers(headers)
    alias_dict = {v: k for k, v in h_aliases_dict.items()}
    col1, col2, col3, col4 = lh.create_columns(4, [0,0,1,1]) 
    st.markdown('___')
    max_cols = config.max_header_count if len(alias_dict) > max_cols else len(alias_dict)
    index = int(max_cols/2)
    # if we have only a few headers to show
    
    col1.write('Choose until 6 different metrics below to compare')
    header_count = col2.selectbox(f'How many header to compare? Max {max_cols} of {len(alias_dict)}', [
                   x for x in range(1, max_cols + 1)], index=index)
    header_cols = header_count

    # check if there are selectboxes < cols_per_line left
    even_lines = int(header_cols/cols_per_line)
    remaining_cols = header_cols % cols_per_line
    rcols = remaining_cols
    empty_cols = cols_per_line - rcols
    if even_lines == 0:
        even_lines = 1
        remaining_cols = 0

    pcols = st.columns(cols_per_line)
    for line in range(even_lines):
        sub_item_dict = {}
        prop_item_dict = {}
        if header_cols >= cols_per_line:
            for col in range(len(pcols)):
                selected_h, selected_sub, prop = display_diff_sboxes(col, pcols, counter, alias_dict, multi_sar_dict, rand_file, 
                        sub_item_dict, prop_item_dict, key_pref)
                collect_field, chart_field = build_metric_dataframes(headers, multi_sar_dict, selected_h, selected_sub, 
                            prop, chart_field, collect_field, col=pcols[col], os_details=os_details, restart_headers=reboot_headers)
                counter += 1
        elif header_cols < cols_per_line:
            for col in range(header_cols):
                selected_h, selected_sub, prop = display_diff_sboxes(col, pcols, counter, alias_dict, multi_sar_dict, rand_file, 
                        sub_item_dict, prop_item_dict, key_pref)
                for nindex in range(1, empty_cols +1):
                    nindex = cols_per_line - nindex
                    pcols[nindex].write('')
                collect_field, chart_field = build_metric_dataframes(headers, multi_sar_dict, selected_h, selected_sub, 
                            prop, chart_field, collect_field, col=pcols[col], os_details=os_details, restart_headers=reboot_headers)
                counter += 1

    if remaining_cols:
        pcols = st.columns(cols_per_line)
        for col in range(remaining_cols):
            pcols[col].markdown('___')
            selected_h, selected_sub, prop = display_diff_sboxes(col, pcols, counter, alias_dict, multi_sar_dict, rand_file, 
                    sub_item_dict, prop_item_dict, key_pref)
            for nindex in range(1, empty_cols + 1):
                nindex = cols_per_line - nindex
                pcols[nindex].write('')
            collect_field, chart_field = build_metric_dataframes(headers, multi_sar_dict, selected_h, selected_sub, 
                        prop, chart_field, collect_field, col=pcols[col], os_details=os_details, restart_headers=reboot_headers)
            counter += 1
    return collect_field, chart_field


def display_select_boxes(st_col, multi_sar_dict, rand_file, selected, sub_item_list, key_pref, counter):
    sub_item = st_col.selectbox('Choose devices', [key for key in
                                                   multi_sar_dict[rand_file][selected].keys() if key not in sub_item_list],
                                key=f'{key_pref}{counter}')
    sub_item_list.append(sub_item)
    return sub_item

def display_diff_sboxes(col, pcols, counter, alias_dict, multi_sar_dict, rand_file, sub_item_dict, 
            prop_item_dict, key_pref):
    sub_item = 0
    r_col = pcols[col]
    s_header = r_col.selectbox('Choose Header', alias_dict.keys(), key=f'{key_pref}{counter}')
    s_header_heading = alias_dict[s_header]

    if not "generic" in multi_sar_dict[rand_file][s_header_heading].keys():
        if not sub_item_dict.get(s_header, None):
            sub_item = r_col.selectbox('Coose devices', [key for key in
                multi_sar_dict[rand_file][s_header_heading].keys()], key=f'sub{counter}')
            sub_item_dict[s_header] = [sub_item]

        else:
            sub_item = r_col.selectbox('Coose devices', [sub_item_dict[s_header][0]], key=f'sub{counter}')
        if not prop_item_dict.get(sub_item, None):
            prop = r_col.selectbox(
                'metric', [x for x in s_header_heading.split()], key=f'prop_{counter}')
            prop_item_dict[sub_item] = [prop]
        else:
            prop = r_col.selectbox(
                'metric', [x for x in s_header_heading.split() if x not in 
                           prop_item_dict[sub_item]], key=f'prop_{counter}')
            prop_item_dict[sub_item].append(prop)
    else:
        if not prop_item_dict.get(sub_item, None):
            prop = r_col.selectbox(
                'metric', [x for x in s_header_heading.split()], key=f'prop_{counter}')
            prop_item_dict[sub_item] = [prop]
        else:
            prop = r_col.selectbox(
                'metric', [x for x in s_header_heading.split() if x not in 
                           prop_item_dict[sub_item]], key=f'prop_{counter}')
            prop_item_dict[sub_item].append(prop)

    return s_header, sub_item, prop


def build_metric_dataframes(headers, multi_sar_dict, selected, sub_item, prop, chart_field,
            collect_field, os_details=None, col=None, restart_headers=None):
    counter = 0
    for sar_data in multi_sar_dict:
        counter += counter
        header = helpers.translate_aliases([selected], headers)[selected]
        if sub_item:
            df = multi_sar_dict[sar_data][header][sub_item]
        else:
            df = multi_sar_dict[sar_data][header]['generic']
        file = sar_data.split('/')[-1]
        df_part = df[[prop]].copy()
        df_part['file'] = file
        if col:
            df_displ = df_part.copy()
            df_displ = df_displ.drop(columns='file')
            df_ds = df_displ.describe()
            collect_field.append([helpers.restart_headers_v1(df_displ, os_details,
                    restart_headers=restart_headers), df_ds, prop])
        chart_field.append([df_part, prop])
    return collect_field, chart_field


def build_device_dataframes(headers, multi_sar_dict, selected, sub_item, prop, chart_field, 
        collect_field, os_details=None, reboot_headers=None,  stats=None):
    counter = 0
    for sar_data in multi_sar_dict:
        counter += counter
        header = helpers.translate_aliases([selected], headers)[selected]
        df = multi_sar_dict[sar_data][header][sub_item]
        df['device'] = sub_item
        file = sar_data.split('/')[-1]
        df_part = df[[prop, 'device']].copy()
        df_part['file'] = file
        if stats:
            df_displ = df_part.copy()
            df_displ = df_displ.drop(columns='file')
            df_displ = df_displ.drop(columns='device')
            df_ds = df_displ.describe()
            collect_field.append([helpers.restart_headers_v1(df_displ, os_details,
                restart_headers=reboot_headers), df_ds, sub_item])
        chart_field.append([df_part, prop])
    return collect_field, chart_field

def display_stats_data(collect_field):
     if st.checkbox('Show Raw Sar Data'):
        cols_per_line = Config.cols_per_line
        cols = st.columns(cols_per_line)
        even_lines = int(len(collect_field)/cols_per_line)
        remaining_cols = len(collect_field) % cols_per_line
        empty_cols = cols_per_line - remaining_cols

        for line in range(even_lines):
            for col in cols:
                f_index = cols.index(col)
                col.markdown(f'###### {collect_field[f_index][2]}')
                #col.markdown(f'###### {collect_field[f_index][0].columns[0]}')
                col.write(collect_field[f_index][0])
                col.write(collect_field[f_index][1])
        if remaining_cols and not even_lines:
            for index in range(remaining_cols):
                col = cols[index]
                col.markdown(f'###### {collect_field[index][2]}')
                #col.markdown(f'###### {collect_field[index][0].columns[0]}')
                col.write(collect_field[index][0])
                for nindex in range(1, empty_cols + 1):
                    nindex = cols_per_line - nindex
                    cols[nindex].write('')
                col.write(collect_field[index][1])
        elif remaining_cols and even_lines:
            for index in range(1, remaining_cols + 1):
                col = cols[index - 1]
                col.markdown(f'___ ')
                f_index = len(collect_field) - index
                col.markdown(f'###### {collect_field[f_index][2]}')
                #col.markdown(f'###### {collect_field[f_index][0].columns[0]}')
                col.write(collect_field[f_index][0])
                col.write(collect_field[f_index][1])

# for future usage
def change_start_end(df_list, col1, col2):
    time_expander = st.expander(
        label='Change Start and End Time', expanded=False)
    with time_expander:
        df_len = 24
        tmp_dict = {}
        col1, col2, col3, col4 = lh.create_columns(4, [0, 0, 1, 1])
        # findout shortest hour range 
        for item in df_list:
            hours = dff.translate_dates_into_list(item)
            if len(hours) <= df_len:
                tmp_dict[df_len] = item
                df_len = len(hours)
        start_box = col1.empty()
        end_box = col2.empty()
        hours = dff.translate_dates_into_list(tmp_dict[df_len])
        start = start_box.selectbox('Choose Start Time', hours, index=0)
        time_len = len(hours) - hours.index(start) -1
        end = end_box.selectbox('Choose End Time',hours[hours.index(start):], index=time_len)
        return(start, end)

