#!/usr/bin/python3
import os
import multiprocessing
import alt
import streamlit as st
import sar_data_crafter as sdc
import helpers
import dataframe_funcs as dff
import layout_helper as lh
from config import Config

def goto_top(key, value):
    st.session_state[key] = value
    
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

    sel_all = st.checkbox('Select All')
    st.write('\n')
    has_clicked = True if sel_all else False
    for file in sar_files:
        sel = st.checkbox(sar_files[sar_files.index(
            file)], key=f'sel_{sar_files.index(file)}', value=has_clicked)
        if sel == True:
            sel_field.append(sar_files[sar_files.index(file)])

    col1, col2 = st.columns([0.3,0.7])
    col1.markdown('___')

    col1, col2, col3, col4 = st.columns(4)
    col2.write('')
    col3.write('')
    col4.write('')
    ph_show = col1.empty()
    if sel_field:
        multi_sar_dict = {}
        def gather_results(result_field):
            file, pds = result_field[0], result_field[1]
            multi_sar_dict[file] = pds
        # compute all files at once    
        pool = multiprocessing.Pool()
        for file in sel_field:
            file = f'{upload_dir}/{file}'
            pool.apply_async(sdc.data_cooker_multi, args=(
                file, multi_sar_dict, username), callback=gather_results)
        pool.close()
        pool.join()

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
        main_title = aitem[selected]


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
            sub_item = None

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
        title = f"{main_title} {sub_item}" if sub_item else main_title
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
                        tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page"])
                        with tab1:
                            cols = st.columns(8)
                            width, height = helpers.diagram_expander(
                                 800, 400, 'Diagram Width', 'Diagram Hight', col=cols[0], key=key)
                            font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1], 
                                key=f"slider_{key}")
                            chart = alt.overview_v1(df, restart_headers, os_details, font_size, 
                                width=width, height=height, title=title)
                            st.altair_chart(chart)
                            lh.pdf_download(pdf_name, chart, key=f"{key}_pdf")
                        with tab2:
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
                        with tab3:
                            for entry in display_field:
                                if entry[0] == key:
                                    df_display = entry[1]
                                    lh.show_metrics(list(df_display.columns), checkbox='off')

            elif pd_or_dia == 'Diagram':
                if chart_field:
                    start_list = [chart_field[x][0].index[0] for x in range(len(chart_field))]
                    end_list = [chart_field[x][0].index[-1] for x in range(len(chart_field))]
                    start = helpers.get_start_end_date(start_list, "start")
                    end   = helpers.get_start_end_date(end_list, "end")
                    col1, col2, col3, col4, *_ = st.columns(8)
                    start, end = helpers.create_start_end_time_list(start, end, col1, col2)
                    for item in range(len(chart_field)):
                        df_date = helpers.get_df_from_start_end(chart_field[item][0], start, end)
                        chart_field[item][0] = df_date
                    col1, col2, col3, col4 = st.columns(4)
                    col3.write(''), col4.write()
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 Chart", "🗃 Data", "🧮 Statistics", " 📔 man page"])
                    with tab1:
                        cols = st.columns(8)
                        font_size = helpers.font_expander(
                            12, "Change Axis Font Size", "font size", cols[1])
                        width, hight = helpers.diagram_expander(
                             800, 400, 'Diagram Width', 'Diagram Hight', col=cols[0])
                        img = alt.overview_v3(chart_field, reboot_headers,width, hight, 'file', font_size, title=title)
                        img = img.configure_axisY(labelLimit=400)
                        st.write(img)
                        lh.pdf_download(pdf_name, img, key=key)
                    with tab2:
                        date_collect_field = []
                        object_field = []
                        if chart_field:
                            prop = chart_field[0][1]
                            for index in dia_collect_field:
                                restart_headers = []
                                os_details = ""
                                filename = index[0]
                                df_stat = index[1]
                                df_new = df_stat[[prop]].copy()
                                df_time = helpers.get_df_from_start_end(df_new.copy(), start, end)
                                date_collect_field.append(df_time)
                                for event in reboot_headers:
                                    hostname = event[1].split()[2].strip("()")
                                    date = event[1].split()[3]
                                    if hostname in filename:
                                        if date in filename:
                                            restart_headers = event[0]
                                            os_details = event[1]
                                            break
                                stats = df_time.describe()
                                table = helpers.restart_headers(df_time, os_details, restart_headers=restart_headers, display=False)
                                header = filename
                                object_field.append([table, stats, header])
                        lh.arrange_grid_entries(object_field, 4)
                    with tab3:
                        prop = chart_field[0][1]
                        lh.display_averages(dia_collect_field, prop, main_title, sub_item)
                    with tab4:
                        col1,col2 = st.columns([0.6,0.4])
                        lh.show_metrics([prop], checkbox='off', col=col1)
                #if st.button('back to top', on_click=goto_top, args=('show',False)):
                #    st.experimental_rerun()