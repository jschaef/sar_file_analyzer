#!/usr/bin/python3
import os
from matplotlib.pyplot import axis

from pyparsing import col
import alt
import streamlit as st
from threading import Thread
import sar_data_crafter as sdc
import helpers
import dataframe_funcs as dff
import layout_helper as lh
import metric_page_helpers as mph
from config import Config

def single_multi(config_dict, username):
    upload_dir = config_dict['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    display_field = []
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

    col1, col2, col3, col4 = st.columns(4)
    col2.write('')
    col3.write('')
    col4.write('')
    answer = col1.checkbox('Show')
    if answer:
        if sel_field:
            multi_sar_dict = {}
            threads = []
            for file in sel_field:
                file = f'{upload_dir}/{file}'
                th = Thread(target=sdc.data_cooker_multi, args=(file, multi_sar_dict, username))
                st.script_run_context.add_script_run_ctx(th)
                th.start()
                threads.append(th)
            for th in threads:
                th.join()

                #sanity + get_file_info
            x = []

            # merge headers of all sar files to be able to compare them
            all_headers = []
            os_field = []
            reboot_headers = []
            for sar_file in multi_sar_dict.keys():
                os_details = multi_sar_dict[sar_file].pop('os_details')
                os_field.append(os_details)
                f_headers = [header for header in multi_sar_dict[sar_file]]
                restart_headers = helpers.extract_restart_header(f_headers)
                reboot_headers.append([restart_headers, os_details])
                all_headers.append(f_headers)

            headers = helpers.merge_headers(all_headers)
            headers = helpers.check_sub_items(headers, multi_sar_dict)

            st.sidebar.markdown('---')
            selected, ph_1 = helpers.get_selected_header('Sar Headings', headers)
            aitem = helpers.translate_headers([selected])


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
                header_add = ''

            if not generic_items:
                sub_item = st.sidebar.selectbox(
                    'Choose devices', [key for key in sub_items], key='sub')
                header_add = sub_item

            for sar_data in multi_sar_dict:
                #if "generic" in multi_sar_dict[sar_data][selected].keys():
                if generic_items:
                    df = multi_sar_dict[sar_data][selected]['generic']
                else:
                    df = multi_sar_dict[sar_data][selected][sub_item]

                x.append({sar_data: df})

            prop_box = st.sidebar.empty()
            prop = prop_box.selectbox(
                'metric', [col for col in df.columns], key='prop')


            # choose diagram size
            if multi_sar_dict:
                chart_field = []
                pd_or_dia = col1.selectbox('', ['Diagram', 'Summary'], index=0)
                collect_field = []
                dia_collect_field = []
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
                        sum_field.append({file: [df1]})
                        # for diamgram statistics
                        dia_collect_field.append([file, df1])
                        # for diagram
                        df1 = df1.reset_index().melt('date', var_name='metrics', value_name='y')
                        collect_field.append({file: [df1]})

                if pd_or_dia == 'Summary':
                    prop_box.empty()
                    for data in sum_field:
                        for key in data:
                            st.text('')
                            filename = (f'{key.split("/")[-1]}')
                            reboot_header = []
                            for header in reboot_headers:
                                hostname = header[1].split()[2].strip("()")
                                if hostname in filename:
                                    reboot_header = header[0]
                                    os_details = header[1]
                            df = data[key][0]
                            ds = df.describe()
                            df_display = df.copy()
                            display_field.append([key, df_display, ds, aitem, selected, header_add])
                            helpers.restart_headers(df, os_details, restart_headers=reboot_header, display=False)
                    st.write(f'Diagram Overview for selected files and selected heading')

                    st.markdown('___')
                    cols = st.columns(8)
                    font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[0], 
                        key=f"slider_{key}")
                    for data in collect_field:
                        for key in data:
                            st.text('')
                            st.markdown(f'##### {key}')
                            restart_headers = []
                            df = data[key][0]
                            for event in reboot_headers:
                                hostname = event[1].split()[2].strip("()")
                                date = event[1].split()[3]
                                if hostname in key and date in key:
                                    restart_headers = event[0]
                                    os_details = event[1]
                                    break

                            chart = alt.overview_v1(df, restart_headers, os_details, font_size)
                            st.altair_chart(chart)
                            col1, col2, col3, col4 = st.columns(4)
                            col2.write(''); col3.write(''), col4.write()
                            lh.pdf_download(pdf_name, chart, col=col1, key=key)
                            if lh.show_checkbox('Show Statistical Data and Raw Sar Data',col=col1,key=key ):
                                for entry in display_field:
                                    if entry[0] == key:
                                        df_display = entry[1]
                                        ds         = entry[2]
                                        aitem      = entry[3]
                                        selected   = entry[4]
                                        header_add = entry[5]
                                        st.markdown(f'###### Data for {aitem[selected]} {header_add}')
                                        helpers.restart_headers(df_display, os_details, restart_headers=reboot_header)
                                        st.markdown(f'###### Statistics for {aitem[selected]} {header_add}')
                                        st.write(ds)
                            for entry in display_field:
                                if entry[0] == key:
                                    df_display = entry[1]
                                    lh.show_metrics(list(df_display.columns), key=key, col=col1)

                elif pd_or_dia == 'Diagram':
                    if chart_field:
                        date_collect_field = []
                        col1, col2, col3, col4 = st.columns(4)
                        col3.write(''), col4.write()

                        st.markdown('___')
                        cols = st.columns(8)
                        font_size = helpers.font_expander(
                            12, "Change Axis Font Size", "font size", cols[1])
                        width, hight = helpers.diagram_expander(
                             800, 400, 'Diagram Width', 'Diagram Hight', col=cols[0])
                        img = alt.overview_v3(chart_field, reboot_headers,width, hight, 'file', font_size)
                        img = img.configure_axisY(labelLimit=400)

                        st.write(img)
                        col1, col2, col3, col4 = lh.create_columns(4,[0,1,1,1])
                        lh.pdf_download(pdf_name, img, col=col1)
                        if lh.show_checkbox('Show Statistical Data and Raw Sar Data', col=col1):
                            object_field = []
                            if chart_field:
                                prop = chart_field[0][1]
                            
                                for index in dia_collect_field:
                                    filename = index[0]
                                    df_stat = index[1]
                                    df_new = df_stat[[prop]].copy()
                                    date_collect_field.append(df_new)

                                    for event in reboot_headers:
                                        hostname = event[1].split()[2].strip("()")
                                        date = event[1].split()[3]
                                        if hostname in filename and date in filename:
                                            restart_headers = event[0]
                                            os_details = event[1]
                                            break
                                    stats = df_new.describe()
                                    table = helpers.restart_headers(df_new, os_details, restart_headers=restart_headers, display=False)
                                    header = filename
                                    object_field.append([table, stats, header])
                            lh.arrange_grid_entries(object_field, 4)
                        lh.show_metrics([prop],)
