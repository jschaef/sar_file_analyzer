#!/usr/bin/python3
import streamlit as st
import alt
import sar_data_crafter as sdc
import helpers
from config import Config

def same_metrics(config_dict, username):
    upload_dir = config_dict['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col2 = config_dict['cols'][1]
    st.subheader('Compare same metrics on same Sar File but different devices')
    os_field = []
    sel_file = helpers.get_sar_files(username, col=col2)
    multi_sar_dict = {}
    os_field = []

    col3, col4 = st.columns(2)
    pdf_check = col3.empty()
    man_check_box = col4.empty()
    man_check = man_check_box.checkbox('Show Metric description from man page')

    if pdf_check.checkbox('Enable PDF saving'):
        pdf_saving = 1
    else:
        pdf_saving = 0


    answer = st.checkbox('Show')
    if answer:
        st.markdown('___')

        file = f'{upload_dir}/{sel_file}'
        sdc.data_cooker_multi(file, multi_sar_dict, username)
        os_details = multi_sar_dict[file].pop('os_details')
        os_field.append({file: os_details})
        x = []
        col3, col4 = st.columns(2)

        rand_file = "".join([key for key in multi_sar_dict.keys()])
        headers = sorted(
                [header for header in multi_sar_dict[rand_file].keys()])

        reboot_headers = helpers.extract_restart_header(headers)
        restart_headers = [[reboot_headers]]
        restart_headers[0].append(os_details)

        not_wanted = ['MHz']
        for key in multi_sar_dict[rand_file].keys():
            if 'generic' in multi_sar_dict[rand_file][key].keys():
                index = headers.index(key)
                headers.pop(index)
            for nw in not_wanted:
                if nw in key:
                    index = headers.index(key)
                    headers.pop(index)
            
        selected_1, ph_1 = helpers.get_selected_header('Header1', headers, col=col3)
        selected_2_boxval = helpers.translate_headers([selected_1])[selected_1]
        col4.selectbox('Header2',[selected_2_boxval])
        selected_2 = selected_1

        sub_item_1 = col3.selectbox('Coose devices', [key for key in
                         multi_sar_dict[rand_file][selected_1].keys()], key='sub1')
        sub_item_2 = col4.selectbox('Coose devices', [key for key in
                        multi_sar_dict[rand_file][selected_1].keys() if key != sub_item_1], key='sub1')


        for sar_data in multi_sar_dict:
            df1 = multi_sar_dict[sar_data][selected_1][sub_item_1]
            df2 = multi_sar_dict[sar_data][selected_2][sub_item_2]
            df1['device'] = sub_item_1
            df2['device'] = sub_item_2

            x.append([{sar_data: df1}, 'df1'])
            x.append([{sar_data: df2}, 'df2'])
        prop_1 = col3.selectbox(
            'metric', [col for col in df1.columns], key='prop_1')
        prop_2 = col4.selectbox('metric', [prop_1])

        chart_field = []

        width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
         'Diagram Hight')
        
        x = [[x[0]] for x in x]
        x[0].append(prop_1)
        x[1].append(prop_2)

        tmp_map = [x for x in range(len(x))]
        for key in x:
            prop = key[1]

            for item in key[0].keys():
                df = key[0][item]
                file = item.split('/')[-1]
                df_part = df[[prop,'device']].copy()
                df_part['file'] = file
                tmp_map.pop(0)
                chart_field.append([df_part, prop])

        if chart_field:
            chart= alt.overview_v5(chart_field, restart_headers, width, hight, 'device')
            st.write(chart)
            if pdf_saving:
                helpers.pdf_download(pdf_name, chart)

            if man_check:
                helpers.metric_expander(prop_1, expand=True)
                helpers.metric_expander(prop_2, expand=True)
