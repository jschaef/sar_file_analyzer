#!/usr/bin/python3
import streamlit as st
import pandas as pd
import redis_mng
import random
import datetime
import time
import alt
import sar_data_crafter as sdc
import download as dow
from config import Config
from altair_saver import save

def beta():
    st.markdown("Content follows")
    rs = redis_mng.get_redis_conn(decode=False)
    if rs:
        st.write(str(rs.keys()))
        r_dict = {'user:jschaef': {
            "file_name1": "pckle0",
            "file_name2": "pckle1",
            "file_name3": "pckle2",
        }
        }
        if st.button('submit'):
            for user, values in r_dict.items():
                rs.hmset(user, values)

            # delete one key in hash user:jschaef
            rs.hdel("user:jschaef", "file_name2")
            st.write(rs.hkeys("user:jschaef"))
            # write all keys, vals for a hash
            #st.write(rs.hscan("user:jschaef"))
            # write val for a key in hash , two different methods
            #st.write(rs.hget("user:jschaef", "file_name1"))
            #st.write(rs.hscan("user:jschaef")[1]["file_name3"])
            # append key to hash


        redis_mng.set_redis_key('irgendwelche Daten', 'user:banana',
            property='data', decode=True)
        st.write(str(rs.keys()))
        time.sleep(3) 
        redis_mng.delete_redis_key('user:banana', 'irgendwelche Daten')
        st.write(str(rs.keys()))
        st.write(redis_mng.show_redis_hash_keys('user:jschaef'))

def test_dia():
    row_vls = ['2020-10-30 00:01:00', '2020-10-30 00:02:00', '2020-10-30 00:03:00',
     '2020-10-30 00:04:00', '2020-10-30 00:05:00', '2020-10-30 00:06:00',
     '2020-10-30 00:07:00', '2020-10-30 00:08:00', '2020-10-30 00:09:00',
     '2020-10-30 00:10:00', ]
    col_vls = ['%usr', '%sys']
    usr = [0.36,
           0.18,
           0.18,
           0.18,
           0.18,
           0.34,
           0.17,
           0.16,
           0.18,
           0.18
           ]

    sys = [0.7,
           0.5,
           0.47,
           0.74,
           0.48,
           0.68,
           0.71,
           0.51,
           0.48,
           0.46]

    data = [[usr[x], sys[x]] for x in range(len(usr))]
    df = pd.DataFrame(data, index=row_vls, columns=col_vls)
    new_index = []
    for x in range(len(df.index)):
        old_val = df.index[x]
        z = pd.to_datetime(
            old_val)
        #z = z.strftime('%H:%M')
        new_index.append(z)
    df['date'] = new_index
    df.set_index('date', new_index, inplace=True,
                 verify_integrity=False)

    df = df.reset_index().melt('date', var_name='metrics', value_name='y')
    st.write(alt.overview_v1(df))
    

    def pdf_download():
        if st.checkbox('Save as PDF'):
            my_file = "pdf/chart.pdf"
            save(alt.overview_v1(df), my_file)


            filename = "chart.pdf"
            rfile = "pdf/chart.pdf"


            # Load selected file
            with open(rfile, 'rb') as f:
                s = f.read()


            download_button_str = dow.download_button(
                s, filename, f'Click here to download PDF')
            st.markdown(download_button_str, unsafe_allow_html=True)

    pdf_download()


    st.write(df)
    
    st.time_input('Set an alarm for', datetime.time(8, 45))



