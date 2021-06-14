#!/usr/bin/python3
import streamlit as st
import alt
import sar_data_crafter as sdc
import helpers
from config import Config

def diff_metrics(config_dict, username):
    upload_dir = config_dict['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col1 = config_dict['cols'][0]
    col2 = config_dict['cols'][1]
    st.subheader('Compare different metrics on same Sar File')
    os_field = []
    sel_field = []
    sel_file = helpers.get_sar_files(username, col=col2)
    multi_sar_dict = {}
    os_field = []

    col3, col4 = st.beta_columns(2)
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
        col3, col4 = st.beta_columns(2)

        rand_file = "".join([key for key in multi_sar_dict.keys()])
        headers = sorted(
                [header for header in multi_sar_dict[rand_file].keys()])

        restart_headers = helpers.extract_restart_header(headers)

        selected_1, ph_1 = helpers.get_selected_header('Header1', headers, col=col3)
        selected_2, ph_2 = helpers.get_selected_header('Header2', headers, col=col4)

        if not "generic" in multi_sar_dict[rand_file][selected_1].keys():
            sub_item_1 = col3.selectbox('Coose devices', [key for key in
                                                            multi_sar_dict[rand_file][selected_1].keys()], key='sub1')
        if not "generic" in multi_sar_dict[rand_file][selected_2].keys():
            sub_item_2 = col4.selectbox('Coose devices', [key for key in
                                                            multi_sar_dict[rand_file][selected_2].keys()], key='sub2')

        for sar_data in multi_sar_dict:
            if "generic" in multi_sar_dict[sar_data][selected_1].keys():
                df1 = multi_sar_dict[sar_data][selected_1]['generic']
            else:
                df1 = multi_sar_dict[sar_data][selected_1][sub_item_1]

            if "generic" in multi_sar_dict[sar_data][selected_2].keys():
                df2 = multi_sar_dict[sar_data][selected_2]['generic']
            else:
                df2 = multi_sar_dict[sar_data][selected_2][sub_item_2]

            x.append([{sar_data: df1}, 'df1'])
            x.append([{sar_data: df2}, 'df2'])
        prop_1 = col3.selectbox(
            'metric', [col for col in df1.columns], key='prop_1')
        prop_2 = col4.selectbox(
            'metric', [col for col in df2.columns], key='prop_2')

        chart_field = []

        width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
         'Diagram Hight')
        
        props = [x[1] for x in x]
        x = [[x[0]] for x in x]
        x[0].append(prop_1)
        x[1].append(prop_2)

        tmp_map = [x for x in range(len(x))]
        for key in x:
            prop = key[1]

            for item in key[0].keys():
                df = key[0][item]
                file = item.split('/')[-1]
                df_part = df[[prop]].reset_index()
                df_part['file'] = prop
                df_part['metric'] = prop

                if len(tmp_map) > 1:
                    factor = 0
                else:
                    factor = 1
                tmp_map.pop(0)

                chart_field.append(alt.draw_single_chart_v1(
                    df_part, prop, restart_headers, os_details,  width, hight, ylabelpadd=0, xlabelpadd=factor * 40,))

        if chart_field:
            chart = alt.draw_multi_chart(chart_field,
                                            x_shared='shared', title=f'Compare {prop_1} vs {prop_2}')
            st.write(chart)
            if pdf_saving:
                helpers.pdf_download(pdf_name, chart)

            if man_check:
                helpers.metric_expander(prop_1, expand=True)
                helpers.metric_expander(prop_2, expand=True)
