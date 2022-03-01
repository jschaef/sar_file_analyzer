#!/usr/bin/python3
import streamlit as st
import alt
import sar_data_crafter as sdc
import helpers
from config import Config
import metric_page_helpers as mph
import layout_helper as lh

def do_metrics(config_dict, username):
    upload_dir = config_dict['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col1, col2, col3, col4 = lh.create_columns(4,[1,1,0,1])
    sel_file = helpers.get_sar_files(username, col=col3)
    multi_sar_dict = {}
    os_field = []

    col3, col4 = st.columns(2)

    radio_result = col4.radio('Choose, what to compare', ['Compare Different Metrics','Compare same Metrics on Different Devices'])
    if radio_result == 'Compare Different Metrics':
        col3.subheader('Compare Different Metrics')
        op_ph = col3.empty()
        op_ph1 = col3.empty()
    elif radio_result == 'Compare same Metrics on Different Devices':
        col3.subheader('Compare Same Metrics on Different Devices')
        op_ph = col3.empty()
        op_ph1 = col3.empty()
    check_bx = st.checkbox('Show')
    if check_bx:
        st.markdown('___')

        file = f'{upload_dir}/{sel_file}'
        filename = file.split('/')[-1]
        sdc.data_cooker_multi(file, multi_sar_dict, username)
        os_details = multi_sar_dict[file].pop('os_details')
        op_ph.write('Operating System Details:')
        op_ph1.write(os_details)
        os_field.append({file: os_details})
        x = []
        col3, col4 = st.columns(2)

        rand_file = "".join([key for key in multi_sar_dict.keys()])
        headers = sorted(
                [header for header in multi_sar_dict[rand_file].keys()])

        reboot_headers = helpers.extract_restart_header(headers)
        restart_headers = [[reboot_headers]]
        restart_headers[0].append(os_details)

        if radio_result == 'Compare same Metrics on Different Devices':
            not_wanted = ['MHz']
            for key in multi_sar_dict[rand_file].keys():
                if 'generic' in multi_sar_dict[rand_file][key].keys():
                    index = headers.index(key)
                    headers.pop(index)
                for nw in not_wanted:
                    if nw in key:
                        index = headers.index(key)
                        headers.pop(index)
            col3.write('Compare until 6 devices below')    
            cols = st.columns(4)
            chart_field, collect_field, prop = mph.create_metric_menu(cols, multi_sar_dict, rand_file, 
                headers, os_details=os_details, reboot_headers=reboot_headers)

            width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
              'Diagram Hight')
            chart= alt.overview_v5(chart_field, restart_headers, width, hight, 'device')
            st.write(chart)
            if st.checkbox('Enable PDF saving'):
                helpers.pdf_download(pdf_name, chart)

            mph.display_stats_data(collect_field)

            if st.checkbox('Show Metric descriptions from man page'):
                helpers.metric_expander(prop, expand=False)

        elif radio_result == 'Compare Different Metrics':
            cols = st.columns(4)
            collect_field, chart_field = mph.build_diff_metrics_menu(multi_sar_dict, 
                                         headers, rand_file, cols, os_details, reboot_headers)
            width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
                          'Diagram Hight')
            chart = alt.overview_v4(chart_field, restart_headers, width, hight)
            st.markdown(f'###### {filename}')
            st.write(chart)

            if st.checkbox('Enable PDF saving'):
                helpers.pdf_download(pdf_name, chart)

            mph.display_stats_data(collect_field)

            if st.checkbox('Show Metric descriptions from man page'):
                for field in collect_field:
                    metric = field[2]
                    helpers.metric_expander(metric, expand=False)
                    

                
