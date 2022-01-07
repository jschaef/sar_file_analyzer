#!/usr/bin/python3
import streamlit as st
import os
import single_file
import multi_files
import different_metrics
import dia_overview

def analyze(upload_dir, config_c, username):
    config = config_c.get_dict()
    col1 = config['cols'][0]
    col2 = config['cols'][1]
    upload_dir = config ['upload_dir']
    #present existing files, default latest uploaded
    #TODO do sanity checks for size or number of files
    sar_files = os.listdir(upload_dir)
    # exclude pickle files
    #sar_files = [x for x in sar_files if x.endswith('.df')]
    single_multi = col2.selectbox('Analyze/Compare', ['Graphical Overview',
     'Detailed Metrics View', 'Multiple Sar Files', 'Compare Different Metrics'])

    st.markdown('___')

    files_exists = 0
    for entry in sar_files:
        if os.path.isfile(f"{upload_dir}/{entry}"):
            files_exists = 1
            break
    if not len(sar_files) or not files_exists:
        st.write('')
        st.warning('Nothing to analyze at the moment. You currently have no sar file uploaded.\n\
                   Upload a file in the "Manage Sar Files" menu on the right frame')
    else:
        if single_multi == 'Graphical Overview':
            dia_overview.show_dia_overview(username)

        elif single_multi == 'Detailed Metrics View':
            single_file.single_f(config, username)

        elif single_multi == 'Multiple Sar Files':
            multi_files.single_multi(config, username)


        elif single_multi == 'Compare Different Metrics':
            different_metrics.diff_metrics(config, username)
