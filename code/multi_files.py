#!/usr/bin/python3
import os
import alt
import streamlit as st
from streamlit.report_thread import add_report_ctx
from threading import Thread
import sar_data_crafter as sdc
import helpers
import dataframe_funcs as dff
from config import Config

def single_multi(config_dict, username):
    upload_dir = config_dict['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col1 = config_dict['cols'][0]
    col2 = config_dict['cols'][1]
    st.subheader('Compare same metric on multiple Sar Files')
    sel_field = []
    sar_files = [ x for x in os.listdir(upload_dir) if os.path.isfile(f'{upload_dir}/{x}')]
    # exclude pickle files
    sar_files_pre = [x for x in sar_files if not x.endswith('.df')]
    sar_files = [x.rstrip('.df') for x in sar_files if x.endswith('.df')]
    sar_files.extend(sar_files_pre)

    for file in sar_files:
        sel = st.checkbox(sar_files[sar_files.index(
            file)], key=f'sel_{sar_files.index(file)}')
        if sel == True:
            sel_field.append(sar_files[sar_files.index(file)])

    st.markdown('___')
    answer = st.checkbox('Proceed')
    if answer:
        if sel_field:
            multi_sar_dict = {}
            col3, col4 = st.beta_columns(2)

            threads = []
            for file in sel_field:
                file = f'{upload_dir}/{file}'
                th = Thread(target=sdc.data_cooker_multi, args=(file, multi_sar_dict, username))
                add_report_ctx(th)
                th.start()
                threads.append(th)
            for th in threads:
                th.join()

                #sanity + get_file_info
            x = []

            # merge headers of all sar files to be able to compare them
            all_headers = []
            os_field = []
            for sar_file in multi_sar_dict.keys():
                os_details = multi_sar_dict[sar_file].pop('os_details')
                os_field.append(os_details)
                f_headers = [header for header in multi_sar_dict[sar_file]]
                all_headers.append(f_headers)

            headers = helpers.merge_headers(all_headers)
            headers = helpers.check_sub_items(headers, multi_sar_dict)

            selected, ph_1 = helpers.get_selected_header('Sar Headings', headers)

            # find data frames
            sub_item_field = []
            generic_item_field = []
            for sar_data in multi_sar_dict:
                if "generic" in multi_sar_dict[sar_data][selected].keys():
                    generic_item_field.append(
                        [f for f in multi_sar_dict[sar_data][selected]['generic']])
                else:
                    sub_item_field.append(
                        [f for f in multi_sar_dict[sar_data][selected].keys()])

            #merge device selections for different devices, etc. br102
            if sub_item_field:
                sub_items = helpers.merge_headers(sub_item_field)
                generic_items = []
            else:
                generic_items = helpers.merge_headers(generic_item_field)

            if not generic_items:
                sub_item = st.sidebar.selectbox(
                    'Choose devices', [key for key in sub_items], key='sub')

            for sar_data in multi_sar_dict:
                #if "generic" in multi_sar_dict[sar_data][selected].keys():
                if generic_items:
                    df = multi_sar_dict[sar_data][selected]['generic']
                else:
                    df = multi_sar_dict[sar_data][selected][sub_item]

                x.append({sar_data: df})

            prop = st.sidebar.selectbox(
                'metric', [col for col in df.columns], key='prop')


            # choose diagram size
            if multi_sar_dict:
                chart_field = []
                pd_or_dia = st.selectbox('', ['Diagram', 'Summary'])
                count = len(x)
                column_table = st.beta_columns(len(x))
                collect_field = []
                sum_field = []
                time_obj_field = []

                for key in x:
                    for item in key.keys():
                        df = key[item]
                        # this df1 copy is for the summary page
                        df1 = df.copy(deep=True)
                        # fake the same date to have
                        # graphs compareable
                        if x.index(key) == 0:
                            time_obj_field.append(df.index[0])
                        else:
                            df = dff.set_unique_date(df, time_obj_field[0])
                        file = item.split('/')[-1]
                        index = x.index(key)
                        # we must use the same date here for the dia
                        # else different dates will be displayed one
                        # graph beside the other

                        df_part = df[[prop]].copy()
                        df_part['file'] = file
                        df_part['date'] = df_part.index

                        # append  df[prop] to chart_field
                        chart_field.append(
                            [df_part, prop])
                        collect_field.append({file: [df]})
                        sum_field.append({file: [df1]})

                        # whole df to dia
                        df = df.reset_index().melt('date', var_name='metrics', value_name='y')
                        collect_field[len(
                            collect_field)-1][file].append(alt.overview_v1(df))

                if pd_or_dia == 'Summary':
                    st.subheader('Dataset Overview')
                    for data in sum_field:
                        for key in data:
                            st.text('')
                            st.subheader(f'{key.split("/")[-1]}')
                            df = data[key][0]
                            ds = df.describe()
                            st.markdown('Statistics')
                            st.write(ds)
                            st.markdown('Raw Data')
                            st.write(df)
                    st.subheader('Diagram Overview')

                    for data in collect_field:
                        for key in data:
                            st.text('')
                            st.subheader(f'{key.split("/")[-1]}')
                            st.altair_chart(data[key][1])
                            helpers.pdf_download(pdf_name, data[key][1])

                elif pd_or_dia == 'Diagram':
                    if chart_field:

                        multi_chart = []
                        width, hight = helpers.diagram_expander(
                            800, 400, 'Diagram Width', 'Diagram Hight')

                        tmp_map = [x for x in range(len(chart_field))]
                        for item in chart_field:
                            while len(tmp_map) < len(chart_field) - len(chart_field) - 2:
                                xfactor = 1
                                yfactor = 1
                            else:
                                factor = tmp_map.pop(0)
                                xfactor = factor * 2.7
                                yfactor = factor * 6

                            chart = alt.draw_single_chart(
                                item[0], item[1], width, hight,  yfactor * 5, xfactor * 20)
                            multi_chart.append(chart)
                        layer = alt.draw_multi_chart(multi_chart,
                                                            y_shared='shared', title='Compare Files', x_shared='shared')
                        st.write(layer)
                        helpers.pdf_download(pdf_name, layer) 
                    
                        if st.sidebar.checkbox('Show Metric description'):
                            helpers.metric_expander(prop, expand=True)
