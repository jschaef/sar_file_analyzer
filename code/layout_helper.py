from email import header
import streamlit as st
import helpers
def pdf_download(pdf_name, chart, col=None, key=None):
    col = col if col else st
    if key:
        if col.checkbox('Enable PDF download', key=key):
            helpers.pdf_download(pdf_name, chart)
    else:
        if col.checkbox('Enable PDF download',):
            helpers.pdf_download(pdf_name, chart)

def show_metrics(prop_list, col=None, key=None):
    col = col if col else st
    if key:
        if col.checkbox('Show Metric descriptions from man page', key=key):
            for metric in prop_list:
                helpers.metric_expander(metric, col=col)
    else:
        if col.checkbox('Show Metric descriptions from man page'):
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
                pcols[index].write(stats)


    # remaining tables
    if remaining_cols:
        collect_field = []
        for index in range(remaining_cols):
            if object_field:
                object = object_field.pop()
                collect_field.append(object)
        for index in range(len(collect_field)): 
            #pcols[index].markdown('___')
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
            pcols[index].write(stats)
        

