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

    radio_result = col4.radio('Choose, what to compare', ['Compare Different Metrics',
        'Compare same Metrics on Different Devices'], horizontal=True)
    if radio_result == 'Compare Different Metrics':
        col3.subheader('Compare Different Metrics')
        op_ph = col3.empty()
        op_ph1 = col3.empty()
    elif radio_result == 'Compare same Metrics on Different Devices':
        col3.subheader('Compare Same Metrics on Different Devices')
        op_ph = col3.empty()
        op_ph1 = col3.empty()
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
        title = f"{collect_field[0][3]} {collect_field[0][4]}"
        st.markdown('___')
        tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page"])
        with tab1:
            cols = st.columns(8)
            width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
              'Diagram Hight', cols[0])
            font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1])
            chart= alt.overview_v5(chart_field, restart_headers, width, hight, 'device', font_size, title=title)
            st.markdown(f'###### {filename}')
            st.altair_chart(chart, theme=None)
            lh.pdf_download(pdf_name, chart)

        with tab2:
            mph.display_stats_data(collect_field)

        with tab3:
                helpers.metric_expander(prop, expand=False)

    elif radio_result == 'Compare Different Metrics':
        cols = st.columns(4)
        collect_field, chart_field = mph.build_diff_metrics_menu(multi_sar_dict, 
                                     headers, rand_file, cols, os_details, reboot_headers)
        st.markdown('___')
        cols = st.columns(8)
        cols[7].write("\n")
        tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page"])
        with tab1:
            cols = st.columns(8)
            width, hight = helpers.diagram_expander(800, 400, 'Diagram Width',
                          'Diagram Hight', cols[0])
            font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1])
            chart = alt.overview_v4(chart_field, restart_headers, width, hight, font_size )
            st.markdown(f'###### {filename}')
            st.altair_chart(chart, theme=None)
            lh.pdf_download(pdf_name, chart)
        with tab2:
            mph.display_stats_data(collect_field)
        with tab3:
            for field in collect_field:
                metric = field[2]
                helpers.metric_expander(metric, expand=False)