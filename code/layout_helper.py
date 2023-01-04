import streamlit as st
import os
import helpers
import pandas as pd
from random import random
from altair_saver import save
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

global fobject

def create_pdf(file: str, chart: object) -> list:
   if not st.session_state.get('download'):
        mimetype = 'text/plain'
        return ['dummy', mimetype]
   else:
        global fobject
        mimetype = 'application/x-binary'
        save(chart, file)
        fobject = open(file, 'rb')
        st.session_state.download = False
        return [fobject, mimetype]


def pdf_download(file: str, chart: object,key=None):
    """creates a download button and a checkbox. Using function create_pdf()
    to create the file for download if the checkbox has been enabled.

    Args:
        file (str): filepath where to save the pdf
        chart (altair object): image/chart created from the altair library
        key (widget key, optional): widget key for streamlit api. Defaults to None.
    """
    disabled=True
    st.session_state.download = False
    col1, col2, *_ = st.columns([0.1,0.1,0.8])
    col2 = col2 if col2 else st
    save_dir = os.path.dirname(file)
    if not os.path.exists(save_dir):
        os.system(f'mkdir -p {save_dir}')
    dkey = f"pdf_{random()}_d"
    clicked = col2.checkbox('*Enable Download*', key=key)
    if clicked:
        st.session_state.download = True
        disabled = False

    col1.download_button(label='Download PDF', file_name='sar_chart.pdf', data=create_pdf(file, chart)[0],
        mime='application/x-binary',key=dkey, disabled=disabled)
    try:
        fobject
    except NameError:
        pass
    else:
        fobject.close()

def show_metrics(prop_list, col=None, key=None, checkbox=None):
    col = col if col else st
    if key:
        if col.checkbox('Show Metric descriptions from man page', key=key):
            for metric in prop_list:
                helpers.metric_expander(metric, col=col)
    elif checkbox != "off":
        if col.checkbox('Show Metric descriptions from man page'):
            for metric in prop_list:
                helpers.metric_expander(metric, col=col)
    else:
        for metric in prop_list:
            helpers.metric_expander(metric, col=col)

def show_checkbox(text, col=None, key=None):
    col = col if col else st
    if key:
        return True if col.checkbox(text, key=key) else False
    else:
        return True if col.checkbox(text, ) else False

def create_columns(number, write_field=None):
    """Create columns and write empty string into them
       if the column index in write_field is True
    Args:
        number (integer): number of columns
        write_field (list): 
    """
    cols = st.columns(number)
    if write_field:
        for entry in range(len(write_field)):
            if write_field[entry]:
                col = cols[entry]
                col.write('')
    return(cols)

def arrange_grid_entries(object_field, cols_per_line):
    # check if there are selectboxes < cols_per_line left
    total_columns = len(object_field)
    even_lines = int(total_columns/cols_per_line) 
    remaining_cols = total_columns % cols_per_line
    rcols = remaining_cols
    empty_cols = cols_per_line - rcols
    if even_lines == 0:
        even_lines = 1
        remaining_cols = 0
    st.markdown('___')
    pcols = st.columns(cols_per_line)

    for line in range(even_lines):
        collect_field = []
        # more than cols_per_line found
        if total_columns >= cols_per_line:
            for index in range(cols_per_line): 
                if object_field:
                    object = object_field.pop(0)
                    collect_field.append(object)
            for index in range(len(collect_field)): 
                object = collect_field[index][0]
                stats = collect_field[index][1]
                header = collect_field[index][2]
                if header:
                    pcols[index].markdown(f'###### {header}')
                pcols[index].write(object)
                pcols[index].markdown(f'###### statistics')
                pcols[index].write(stats)

        # less than cols_per_line found
        else:
            for index in range(cols_per_line):
                if object_field:
                    object = object_field.pop(0)
                    collect_field.append(object)
            for index in range(len(collect_field)): 
                object = collect_field[index][0]
                stats = collect_field[index][1]
                header = collect_field[index][2]
                if header:
                    pcols[index].markdown(f'###### {header}')
                    for nindex in range(1,empty_cols +1):
                        nindex = cols_per_line - nindex
                        pcols[nindex].write('')
                pcols[index].write(object)
                pcols[index].markdown(f'###### statistics')
                pcols[index].write(stats)


    # remaining tables
    if remaining_cols:
        collect_field = []
        for index in range(remaining_cols):
            if object_field:
                object = object_field.pop()
                collect_field.append(object)
        for index in range(len(collect_field)): 
            object = collect_field[index][0]
            stats = collect_field[index][1]
            header = collect_field[index][2]
            if header:
                pcols[index].markdown('___')
                pcols[index].markdown(f'###### {header}')
                for nindex in range(1,rcols+1):
                    nindex = cols_per_line - nindex
                    pcols[nindex].write('')
            pcols[index].write(object)
            pcols[index].markdown(f'###### statistics')
            pcols[index].write(stats)

def display_averages(dia_field, prop, main_title, sub_item):
    final_dfs = []
    final_dfs_sum = []
    col1, col2 = st.columns([0.3,0.7])
    if sub_item:
        col1.markdown(f'##### Average statistics for {main_title}/{sub_item}/{prop}')
        col2.markdown(f'##### Average statistics for {main_title}/{sub_item}')
    else:
        col1.markdown(f'##### Average statistics for {main_title}/{prop}')
        col2.markdown(f'##### Average statistics for {main_title}')

    st.write("\n")
    
    for entry in range(len(dia_field)):
        st.markdown(f'- {dia_field[entry][0]}')

    st.write("\n")
    
    for entry in range(len(dia_field)):
        df = dia_field[entry][1][prop]
        df_sum = dia_field[entry][1]
        df = df.reset_index()
        df_sum = df_sum.reset_index()
        final_dfs.append(df)
        final_dfs_sum.append(df_sum)
    final_df = pd.concat(final_dfs)
    final_dfs_sum = pd.concat(final_dfs_sum)
    col1, col2 = st.columns([0.3,0.7])
    col1.write(final_df.describe())
    col2.write(final_dfs_sum.describe())

def use_aggrid(df, restart_headers, key):
    key = f"{key}_{random()}"
    df =  df.reset_index()
    for col in df.columns:
        max = f"{col}_max"
        min = f"{col}_min"
        df[max] = df[col].max()
        df[min] = df[col].min()


    cellstyle_jscode = JsCode("""
        function(params) {
            var max = params.column.colDef.headerName + '_max'; 
            var min = params.column.colDef.headerName + '_min';
            if (params.value == params.data[max]) {
                return {
                    'color': 'black',
                    'backgroundColor': 'lightblue',
                }
            }
            else if (params.value == params.data[min]) {
                return {
                    'color': 'black',
                    'backgroundColor': 'yellow',
                }
            } else {
                return {
                    'color': 'black',
                    'backgroundColor': 'white'
                }
            }
        };
        """)
    
    gb = GridOptionsBuilder.from_dataframe(df)
    #gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
    #gb.configure_pagination(paginationPageSize=20)  # Add pagination
    #gb.configure_side_bar()  # Add a sidebar
    gb.configure_selection('multiple', use_checkbox=False,
        groupSelectsChildren="Group checkbox select children")  # Enable multi-row selection

    for column in df:
        if "_max" in column or "_min" in column:
            gb.configure_column(column, hide=True)
        gb.configure_column(column, cellStyle=cellstyle_jscode)
        #gb.configure_column(column, cellRenderer=cellrenderer_jscode)
            
    gridOptions = gb.build()
    return df, gridOptions, key

