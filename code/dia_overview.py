#!/usr/bin/python3

import streamlit as st
#import multiprocessing
import multiprocessing_on_dill as multiprocessing
import sar_data_crafter as sdc
import dataframe_funcs as dff
import helpers
import mp5
import layout_helper as lh
from config import Config
#from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

sar_structure = []
os_details = ""
file_chosen = ""
def show_dia_overview(username, sar_file_col):
    collect_list = []
    global sar_structure, os_details, file_chosen
    sar_file = helpers.get_sar_files(username, col=sar_file_col, key="dia_overview")
    st.subheader('Overview of important metrics from SAR data')
    col1, col2, col3 = lh.create_columns(3, [0.7, 0.1, 0.4])
    op_ph = col1.empty()
    op_ph3= col3.empty()
    pdf_check = col3.empty()
    col1, col2, col3, col4 = lh.create_columns(4, [0, 1, 1, 1])
    st.write('')
    if sar_file != file_chosen:
        sar_structure = []
        file_chosen = sar_file

    sar_file = f'{Config.upload_dir}/{username}/{sar_file}'
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    if not sar_structure:
        sar_structure = sdc.get_data_frames(sar_file, username)
        os_details = sar_structure.pop('os_details')
    sar_file_col.text(f"Operating System Details: {os_details}")
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
   
    op_ph3.markdown("**Choose if you need to save your diagrams as PDF**")
    if pdf_check.checkbox('Enable PDF saving'):
        enable_pdf = 1
    else:
        enable_pdf = 0
    show_metric = 1
    statistics = 1

    def collect_results(result):
        collect_list.append(result)
    
    col1, col2, col3, col4 = lh.create_columns(4, [0, 0, 1, 1])
    st.markdown("**Select which metrics to display**")
    h_expander = st.expander(label='Choose SAR Metrics',expanded=False)
    with h_expander:
        col5, col6 = st.columns(2)
        ph_col3 = col5.empty()
        ph_col4 = col6.empty()
        if ph_col3.checkbox('Select All'):
            initial_aliases = full_alias_l[:]
        elif ph_col4.checkbox('Deselect All'):
            initial_aliases = []
        st.markdown('***')
        for line in range(count_lines):
            cols = st.columns(boxes_per_line)
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

    headers = helpers.translate_aliases(sel_field, sar_structure.keys())

    # pick time frame
    st.markdown("**Change Start/End Time**")
    time_expander = st.expander(label='Choose Time',expanded=False)
    with time_expander:
        df_len = 0
        tmp_dict = {}
        col1, col2, col3, col4 = lh.create_columns(4, [0, 0, 1, 1])
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
                start_box = col1.empty()
                end_box = col2.empty()
                hours = dff.translate_dates_into_list(date_df)
                start = start_box.selectbox('Choose Start Time', hours, index=0)
                time_len = len(hours) - hours.index(start) -1
                end = end_box.selectbox('Choose End Time',hours[hours.index(start):], index=time_len)
            break
        
    with st.form(key='main_section'):
        wanted_sub_devices = ['IFACE', 'Block Devices', 'Fibrechannel', 'IFACE Errors', \
            'IFACE older distributions', 'Block Devices (older SAR versions)']

        st.markdown("**Customize Diagrams**")
        cols = st.columns(8)
        width, height = helpers.diagram_expander(800, 400, 'Diagram Width',
            'Diagram Hight', cols[0])
        font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1])

        if st.checkbox('Show diagrams on submit', value=True):
            show_diagrams = 1
        else:
            show_diagrams = 0
        submitted = st.form_submit_button('Submit')
        st.markdown("___")
        if submitted:
            with st.spinner(text='Please be patient until all graphs are constructed ...'):
                # doing multiprocessing
                pool = multiprocessing.Pool()
                for entry in sel_field:
                    pool.apply_async(mp5.final_overview, args=(sar_structure, headers, entry,
                        wanted_sub_devices, start, end, statistics, os_details, restart_headers,
                        font_size, width, height, show_metric), callback=collect_results)
                pool.close()
                pool.join()
                counter = 0
                for item in collect_list:

                    header = item[0]['header']
                    device = item[0]['title']
                    device_count = item[0]['device_num']

                    if len(item) == 1:
                        st.markdown(f'#### {header}')
                        if show_diagrams:
                            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page", " 📊 PDF", " 📃 grid-table"])
                        else:
                            tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["✌️", "📈 Chart", "🗃 Data", " 📔 man page", " 📊 PDF", " 📃 grid-table"])
                        with tab1:
                            chart = item[0]['chart']
                            if device == 'all':
                                st.markdown(f'###### all of {device_count}')
                            st.altair_chart(chart, use_container_width=True)
                        with tab2:
                            if statistics:
                                dup_bool = item[0]['dup_bool']
                                dup_check = item[0]['dup_check']
                                df_describe = item[0]['df_describe']
                                df_stat  = item[0]['df_stat']
                                df_display       = item[0]['df_display']

                                col1, col2, col3, col4 = lh.create_columns(
                                    4, [0, 0, 1, 1])
                                
                                col1.markdown(f'###### Sar Data for {header}')
                                st.write(df_stat)
                                if dup_bool:
                                   col1.warning('Be aware that your data contains multiple indexes')
                                   col1.write('Multi index table:')
                                   col1.write(dup_check)
                                st.markdown(f'###### Statistics for {header}')
                                st.write(df_describe)
                        with tab3:
                            if show_metric:
                                metrics =  item[0]['metrics']
                                for metric in metrics:
                                    helpers.metric_expander(metric)
                        with tab4:
                            if enable_pdf:
                                helpers.pdf_download(pdf_name, chart)
                            else:
                                st.write("You have to enable the PDF checkbox on the top. It is disabled\
                                         by default because the current implementation is quite performance intensive")
                        with tab5:
                            lh.use_aggrid(df_display, restart_headers, f'generic_{counter}')
                        counter += 1
                    else:
                        st.markdown(f'#### {header}')
                        counter = 0
                        for subitem in item:
                            chart = subitem['chart']
                            if show_diagrams:
                                tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page", " 📊 PDF", " 📃 grid-table"])
                            else:
                                tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["✌️", "📈 Chart", "🗃 Data", " 📔 man page", " 📊 PDF", " 📃 grid-table"])
                            with tab1:
                                tab1.altair_chart(chart)
                            with tab2:
                                if statistics:
                                    dup_bool = subitem['dup_bool']
                                    dup_check = subitem['dup_check']
                                    df_describe = subitem['df_describe']
                                    df_stat  = subitem['df_stat']
                                    df_display = subitem['df_display']
                                    title = subitem['title']

                                    col1, col2, col3, col4 = lh.create_columns(
                                        4, [0, 0, 1, 1])

                                    col1.markdown(f'###### Sar Data for {title}')
                                    st.write(df_stat)
                                    if dup_bool:
                                       col1.warning(
                                           'Be aware that your data contains multiple indexes')
                                       col1.write('Multi index table:')
                                       col1.write(dup_check)
                                    st.markdown(f'###### Statistics for {title}')
                                    st.write(df_describe)
                            with tab3:
                                if show_metric:
                                    metrics =  subitem['metrics']
                                    for metric in metrics:
                                        helpers.metric_expander(metric)
                            with tab4:
                                if enable_pdf:
                                    helpers.pdf_download(pdf_name, chart)
                                else:
                                    st.write("You have to enable the PDF checkbox on the top. It is disabled\
                                             by default because the current implementation is quite performance intensive")
                            with tab5:
                                lh.use_aggrid(df_display, restart_headers, f"{counter}")
                            counter +=1
                    st.markdown("___")
        # if st.button('Back to top'):
            if st.form_submit_button('Back to top'):
                st.experimental_rerun()