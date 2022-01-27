import streamlit as st

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
