import streamlit as st
import altair
import alt
import pandas as pd
import sar_data_crafter as sdc
import helpers
from config import Config

def single_f(config_obj, username):
    upload_dir = config_obj['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col1 = config_obj['cols'][0]
    col2 = config_obj['cols'][1]
    selection = helpers.get_sar_files(username, col=col2)

    if st.sidebar.checkbox('Show'):
        st.sidebar.markdown('---')
        col3, col4 = st.beta_columns(2)
        # parse data from file
        sar_file = f'{upload_dir}/{selection}'
        st.subheader("Operating System Details")
        sar_structure = sdc.get_data_frames(sar_file, username)
        os_details = sar_structure.pop('os_details')
        st.text(os_details)
        headers = [header for header in sar_structure.keys()]

        selected, _ = helpers.get_selected_header('Sar Headings', headers)
        # find data frames
        if "generic" in sar_structure[selected].keys():
            df = sar_structure[selected]['generic']
            sub_item = None
        else:
            sub_list = [
                key for key in sar_structure[selected].keys()]
            sub_list = helpers.merge_headers([sub_list,sub_list])
            sub_item = st.sidebar.selectbox('Choose devices', sub_list)
            df = sar_structure[selected][sub_item]

        st.subheader('Selections')
        selected_content = st.selectbox(
                'Sumary/Details', ['Summary', 'Details'], key='diagr')

        aitem = helpers.translate_headers([selected])
        if sub_item:
            header_add = sub_item
        else:
            header_add =''

        if selected_content == 'Summary':
            st.subheader(f'Statistics for {aitem[selected]} {header_add}')
            st.text('')
            st.write(df.describe())
            st.markdown("Min/Max at Time")
            x_list = []
            y_list = []
            for metric in df.columns.to_list():
                x_list.append(df[metric].idxmin())
                y_list.append(df[metric].idxmax())

            stat_df = pd.DataFrame(data=[x_list,y_list], index=['min', 'max'],
                columns=[m for m in df.columns.to_list()])

            st.write(stat_df)
            st.text('')

            st.subheader('Dataset')
            st.write(helpers.set_stile(df))
            df = df.reset_index().melt('date', var_name='metrics', value_name='y')
            st.text('')
            st.subheader('Graphical overview')
            st.altair_chart(alt.overview_v1(df))
            helpers.pdf_download(pdf_name, alt.overview_v1(df))


            metrics = df['metrics'].drop_duplicates().tolist()
            for metric in metrics:
                helpers.metric_expander(metric)

        elif selected_content == 'Details':

            prop = st.sidebar.selectbox('metrics', [
                col for col in df.columns])
            try:
                x = sub_item
            except NameError:
                sub_item = ''


            #df = df.reset_index()
            df = df.rename(columns={'index':'date'})
            df_part = df[[prop]].copy()
            col5, col6 = st.beta_columns(2)
            alias = aitem[selected]
            col5.subheader(f'Statistics for {aitem[selected]} {header_add} {prop}')
            col6.subheader(f'Dataset for {aitem[selected]} {header_add} {prop}')
            col5.dataframe(df_part.describe())
            col6.dataframe(helpers.set_stile(df_part))

            df_part['file'] = os_details.split()[2].strip('()')
            df_part['date'] = df_part.index
            df_part['metric'] = prop
            # choose diagram size
            width, hight = helpers.diagram_expander(800, 400, 'Diagram Width', 'Diagram Hight')

            chart = alt.draw_single_chart(
                df_part, prop, width, hight)

            st.altair_chart(chart)
            helpers.pdf_download(pdf_name, chart)

            helpers.metric_expander(prop)
