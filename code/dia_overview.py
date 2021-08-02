#!/usr/bin/python3

import streamlit as st
import alt
import sar_data_crafter as sdc
import dataframe_funcs as dff
import helpers
import time
from config import Config

sar_structure = []
os_details = ""
file_chosen = ""
def show_dia_overview(username):
    global sar_structure, os_details, file_chosen
    st.subheader('Overview of important metrics from SAR data')

    col1, col2 = st.beta_columns(2)
    sar_file = helpers.get_sar_files(username, col=col2)
    if sar_file != file_chosen:
        sar_structure = []
        file_chosen = sar_file

    sar_file = f'{Config.upload_dir}/{username}/{sar_file}'
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    if not sar_structure:
        sar_structure = sdc.get_data_frames(sar_file, username)
        os_details = sar_structure.pop('os_details')
    headers = [header for header in sar_structure.keys()]
    restart_headers = helpers.extract_restart_header(headers)

    initial_aliases = ['CPU', 'Kernel tables', 'Load', 'Memory utilization',
    'Swap utilization']

    full_alias_d = helpers.translate_headers(headers)

    full_alias_l = list(full_alias_d.values())
    full_alias_l.sort(reverse=True)
    sel_field = []

    length =  len(headers)
    boxes_per_line = 5
    count_lines = length / boxes_per_line
    if count_lines > 0:
        count_lines = int(count_lines + 1)
    
    h_expander = st.beta_expander(label='Select SAR Metrics to display',expanded=False)
    with h_expander:
        col3, col4 = st.beta_columns(2)
        ph_col3 = col3.empty()
        ph_col4 = col4.empty()
        if ph_col3.checkbox('Select All'):
            initial_aliases = full_alias_l[:]
        elif ph_col4.checkbox('Deselect All'):
            initial_aliases = []
        st.write('  \n')
        st.markdown('***')
        for line in range(count_lines):
            cols = st.beta_columns(boxes_per_line)
            for x in range(len(cols)):
                if len(full_alias_l) > 0:
                    label = full_alias_l.pop()
                    if label in initial_aliases:
                        value = True
                    else:
                        value = False

                    ph_sel = cols[x].empty()
                    index = range(len(cols)).index(x)
                    selected = ph_sel.checkbox(label, value=value)
                    if selected:
                        sel_field.append(label)

    if st.checkbox('Show Metric descriptions from man page'):
        show_metric = 1
    else:
        show_metric = 0
    st.markdown('___')                
    headers = helpers.translate_aliases(sel_field, sar_structure.keys())

    # pick time frame
    time_expander = st.beta_expander(label='Change Start and End Time',expanded=False)
    with time_expander:
        df_len = 0
        tmp_dict = {}
        col5, col6 = st.beta_columns(2)
        for entry in headers:
            skey = headers[entry]
            if sar_structure.get(skey, None):
                device_l = list(sar_structure.get(skey).keys())
            # findout longest hour range if in rare cases it
            # differs since a new device occured after reboot (persistent
            # rules network device)
            for item in device_l:
                date_df = sar_structure.get(skey).get(item, None) 
                hours = dff.translate_dates_into_list(date_df)
                if len(hours) >= df_len:
                    tmp_dict[df_len] = item
                    df_len = len(hours)
            if len(device_l) > 1:
                date_df = sar_structure.get(skey).get(tmp_dict[df_len], None) 
            if date_df is not None:
                start_box = col5.empty()
                end_box = col5.empty()
                hours = dff.translate_dates_into_list(date_df)
                start = start_box.selectbox('Choose Start Time', hours, index=0)
                time_len = len(hours) - hours.index(start) -1
                end = end_box.selectbox('Choose End Time',hours[hours.index(start):], index=time_len)
            break


    st.markdown('___')                
    if st.checkbox('Enable PDF saving'):
        pdf_saving = 1
    else:
        pdf_saving = 0
        
    with st.form(key='main_section'):
        wanted_sub_devices = ['IFACE', 'Block Devices', 'Fibrechannel', 'IFACE Errors', \
            'IFACE older distributions', 'Block Devices (older SAR versions)']

        st.markdown('')
        submitted = st.form_submit_button('Submit')
        if submitted:
            for entry in sel_field:
                df_field = []
                if sar_structure.get(headers[entry], None):
                    st.subheader(entry)
                    if 'generic' in sar_structure[headers[entry]].keys():
                        df = sar_structure[headers[entry]]['generic']
                        df_field.append([df,0])
                    else:
                        device_list = list(sar_structure[headers[entry]].keys())
                        device_list.sort()
                        if entry in wanted_sub_devices:
                            for device in device_list:
                                df = sar_structure[headers[entry]][device]
                                df_field.append([df, device])

                        elif 'all' in device_list:
                            device = 'all'
                            st.write(f'all of {len(device_list) -1}')
                            df = sar_structure[headers[entry]][device]
                            df_field.append([df, device])
                        else:
                            device = device_list[0]
                            df = sar_structure[headers[entry]][device]
                            df_field.append([df, device])

                    for df_tuple in df_field:
                        if df_tuple[1]:
                            st.write(df_tuple[1])
                        df = df_tuple[0]
                        if start in df.index and end in df.index:
                            df = df[start:end]
                        helpers.restart_headers(df, os_details, restart_headers=restart_headers)
                        df = df.reset_index().melt('date', var_name='metrics', value_name='y')
                        st.altair_chart(alt.overview(df, restart_headers, os_details))
                        if pdf_saving:
                            helpers.pdf_download(pdf_name, alt.overview(df, restart_headers, os_details))

                        metrics = df['metrics'].drop_duplicates().tolist()
                        if show_metric:
                            for metric in metrics:
                                helpers.metric_expander(metric)
