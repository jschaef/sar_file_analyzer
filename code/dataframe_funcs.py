#!/usr/bin/python3

import re
import pandas as pd

def format_date(os_details):
    # presume format 2020-XX-XX for sar operating system details
    date_reg = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')
    date_reg2 = re.compile('[0-9]{2}/[0-9]{2}/[0-9]{2}')
    date_str = ''
    for item in os_details.split():
        if date_reg.search(item):
            date_str = item
            format='%Y-%m-%d'
            break
        elif date_reg2.search(item):
            date_str = item
            format='%m/%d/%y %H:%M:%S'
            break
        else:
            # add fake item
            format='%Y-%m-%d'
            date_str = '2000-01-01'
    return(date_str, format)

def df_reset_date(df, os_details):
    new_index = []
    date_str, format = format_date(os_details)
    for x in range(len(df.index)):
        old_val = df.index[x]
        z = pd.to_datetime(
            f'{date_str} {old_val}', format=format)
        #z = z.strftime('%H:%M')
        new_index.append(z)
    df['date'] = new_index
    df.set_index('date', new_index, inplace=True,
                verify_integrity=False)
    
    return df

def extract_hours_for_labels(df):
    measures = len(df) -1
    start_time = df['date'][0]
    end_time = df['date'][measures]
    x_hours = [x for x in df['date'] if x.minute == 0]
    return x_hours


def set_unique_date(dataframe, time_obj):
    """
    Extracts the date from the first entry. Looks if it is
    different from the current dataFrame.
    If yes sets year, month, day to the first value -> dataFrame
    """
    year, month, day = time_obj.year, time_obj.month, time_obj.day
    new_index = [date.replace(year, month, day) for date in dataframe.index]
    dataframe.index = new_index
    dataframe.index.name = 'date'
    
    return dataframe
    
def translate_dates_into_list(df):
    hours = [date for date in df.index if date.minute == 0]
    hours.append(df.index[-1])
    return hours

def insert_restarts_into_df(os_details, df, restart_headers):
    # date_str like 2020-09-17
    date_str, format = format_date(os_details)
    new_rows = []
    for header in restart_headers:
        # restart_headers have time of restart appended as last string
        # hour time, e.g.: 10:13:47
        h_time = header.split()[-1]
        z = pd.to_datetime(f'{date_str} {h_time}', format=format)
        ind = 0
        for x in range(len(df.index)):
            # check if date - z is the minimum
            if (z - df.index[x]).total_seconds() >= 0:
                continue
            else:
                ind = x - 1
                break
        # Reboot is last entry
        if len(df.index) > 0:
            if ind == 0:
                ind = len(df.index) -1
            # restart row date first entry
            elif ind < 0:
                ind = 0
            rind = df.index[ind]
            # copy last line before restart, reindex it and insert the reboot str
            reset_row = df.loc[[rind]]
            reset_row = reset_row.reindex([z])
            reset_row.loc[z] = 0.00
            new_rows.append(reset_row)
            df = insert_row(ind, df, reset_row)
    return df, new_rows 

# example from https://pythoninoffice.com/insert-rows-into-a-dataframe/
def insert_row(row_num, orig_df, row_to_add):
    if row_num == 0:
        df_final = row_to_add.append(orig_df)
    elif len(orig_df.index) -1 > row_num:
        # split original data frame into two parts and insert the restart pd.series
        row_num= min(max(0, row_num), len(orig_df))
        df_part_1 = orig_df[orig_df.index[0]: orig_df.index[row_num]]
        df_part_2 = orig_df[orig_df.index[row_num +1]: orig_df.index[-1]]
        df_final = df_part_1.append(row_to_add, ignore_index = False)
        df_final = df_final.append(df_part_2, ignore_index = False)
    else:
        df_final = orig_df.append(row_to_add, ignore_index = False)
    return df_final
