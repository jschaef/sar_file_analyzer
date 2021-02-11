#!/usr/bin/python3

import re
import pandas as pd

def df_reset_date(df, os_details):
    new_index = []

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
    #date_str = os_details[3]
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

