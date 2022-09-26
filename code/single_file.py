import streamlit as st
import alt
import sar_data_crafter as sdc
import helpers
import layout_helper as lh
from config import Config

sar_structure = []
file_chosen = ""
os_details = ""
def single_f(config_obj, username):
    global sar_structure, file_chosen, os_details
    upload_dir = config_obj['upload_dir']
    pdf_dir = f'{Config.upload_dir}/{username}/pdf'
    pdf_name = f'{pdf_dir}/{Config.pdf_name}'
    col1, col2, col3, col4 = st.columns([1,1,1, 1])
    des_text = 'Show a Summary of the chosen header or Details of the chosen metric in the left frame'
    selected_content = col1.selectbox(
            des_text, ['Summary', 'Details'], key='diagr')
    col2.write('')
    selection = helpers.get_sar_files(username, col=col3)
    st.sidebar.markdown('---')
    # parse data from file
    sar_file = f'{upload_dir}/{selection}'
    if sar_file != file_chosen:
        sar_structure = sdc.get_data_frames(sar_file, username)
        file_chosen = sar_file
        os_details = sar_structure.pop('os_details')
    headers = [header for header in sar_structure.keys()]
    restart_headers = helpers.extract_restart_header(headers)

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

    col3.write(f"Operating System Details: {os_details}")
    aitem = helpers.translate_headers([selected])
    if sub_item:
        header_add = sub_item
    else:
        header_add =''

    title = f"{aitem[selected]} {sub_item}" if sub_item else aitem[selected]
    if selected_content == 'Summary':
        col1, col2, col3, col4 = st.columns(4)
        df_displ = df.copy()
        x_list = []
        y_list = []
        for metric in df.columns.to_list():
            x_list.append(df[metric].idxmin())
            y_list.append(df[metric].idxmax())

        helpers.restart_headers(df, os_details, restart_headers=restart_headers, display=False)
        df = df.reset_index().melt('date', var_name='metrics', value_name='y')
        tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page"])
        with tab1:
            cols = st.columns(8)
            width, height = helpers.diagram_expander(1200, 400, 'Diagram Width', 'Diagram Hight', cols[0])
            font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1])
            chart = alt.overview_v1(df, restart_headers, os_details, font_size=font_size, width=width, 
                height=height, title=title)
            st.altair_chart(chart)
            lh.pdf_download(pdf_name, chart)
        with tab2:
            st.markdown(f'###### Dataset for {aitem[selected]} {header_add}')
            helpers.restart_headers(df_displ, os_details, restart_headers=restart_headers)
            st.markdown(f'###### Statistics for {aitem[selected]} {header_add}')
            st.text('')
            st.write(df_displ.describe())
        with tab3:
            metrics = df['metrics'].drop_duplicates().tolist()
            lh.show_metrics(metrics, checkbox="off")

    elif selected_content == 'Details':
        prop = st.sidebar.selectbox('metrics', [
            col for col in df.columns])
        try:
            x = sub_item
        except NameError:
            sub_item = ''
        df = df.rename(columns={'index':'date'})
        df_part = df[[prop]].copy()
        df_displ = df_part.copy()
        helpers.restart_headers(
            df_part, os_details, restart_headers=restart_headers, display=None)

        df_part['file'] = os_details.split()[2].strip('()')
        df_part['date'] = df_part.index
        df_part['metric'] = prop

        tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", " 📔 man page"])
        with tab1:
            cols = st.columns(8)
            width, hight = helpers.diagram_expander(1200, 400, 'Diagram Width', 'Diagram Hight', cols[0])
            font_size = helpers.font_expander(12, "Change Axis Font Size", "font size", cols[1])
            chart = alt.draw_single_chart_v1(
                df_part, prop, restart_headers, os_details, width, hight, font_size=font_size, title=title)
            st.altair_chart(chart)
            lh.pdf_download(pdf_name, chart)
        with tab2:
            st.markdown(f'###### Dataset for {aitem[selected]} {header_add} {prop}')
            helpers.restart_headers(df_displ, os_details, restart_headers=restart_headers)
            st.markdown(f'###### Statistics for {aitem[selected]} {header_add} {prop}')
            st.dataframe(df_displ.describe())
        with tab3:
            col1, col2 = st.columns(2)
            lh.show_metrics([prop], checkbox="off", col=col1)

