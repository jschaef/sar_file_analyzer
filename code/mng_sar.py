#!/usr/bin/python3
import os
import pandas as df
import streamlit as st
from magic import Magic
from datetime import datetime
import redis_mng
import helpers
from config import Config


def file_mng(upload_dir, col, username):
    manage_files = ['Show Sar Files','Add Sar Files', 'Delete Sar Files']
    #sar_files = os.listdir(upload_dir)
    sar_files = [ x for x in os.listdir(upload_dir) if os.path.isfile(f'{upload_dir}/{x}')]
    sar_files_uploaded =[x for x in sar_files if not x.endswith(('.df'))]
    sar_files = [x.rstrip('\.df') for x in sar_files if x.endswith(('.df'))]
    sar_files.extend(sar_files_uploaded)

    managef_options = col.selectbox(
        'Add/Delete', manage_files)

    st.markdown('___')
    if managef_options == 'Add Sar Files':
        st.set_option(
            'deprecation.showfileUploaderEncoding', False)
        sar_files = [st.file_uploader(
            "Please upload your SAR files", key='sar_uploader',
            #accept_multiple_files=False)]
            accept_multiple_files=True)]
        if st.button('Submit'):
            if sar_files:
                for multi_files in sar_files:
                    for u_file in multi_files:
                        if u_file is not None:
                            #st.write(dir(sar_file))
                            f_check = Magic()
                            #stringio = io.StringIO(sar_file.decode("utf-8"))
                            bytes_data = u_file.read()
                            res = f_check.from_buffer(bytes_data)
                            if not "ASCII text" in res:
                                st.warning(
                                    f'File is not a valid sar ASCII data file. Instead {res}')
                                continue
                            else:
                                #TODO check if Linux Header is present and if sar sections are present
                                st.write(
                                    f"Sar file is valid. Renaming {u_file.name}")
                                with open(f'{upload_dir}/{u_file.name}', 'wb') as targetf:
                                    targetf.write(bytes_data)
                                #remove name
                                renamed_name = helpers.rename_sar_file(f'{upload_dir}/{u_file.name}')
                            # remove old redis data
                            r_hash = f"{Config.rkey_pref}:{username}"
                            r_key = f"{renamed_name}_df"

                            try:
                                redis_mng.delete_redis_key(r_hash, r_key)
                            except:
                                print(f'{renamed_name} key not in redis db or redis db offline')
                            # remove old pickle from disk
                            df_file = f'{upload_dir}/{renamed_name}.df'
                            os.system(f'rm -rf {df_file}')
    elif managef_options == 'Delete Sar Files':
        if sar_files:
            dfiles_ph = st.empty()
            dfiles = dfiles_ph.multiselect(
                'Choose your Files to delete', sar_files)
            if st.button('Delete selected Files'):
                for file in dfiles:
                    r_item = f'{file}_df'
                    df_file = f'{upload_dir}/{file}.df'
                    fs_file = f'{upload_dir}/{file}'
                    os.system(f'rm -f {df_file}')
                    os.system(f'rm -f {fs_file}')
                    try:
                        rkey = f"{Config.rkey_pref}:{username}"
                        print(
                            f'delete {rkey}, {r_item} from redis at {datetime.now().strftime("%m/%d/%y %H:%M:%S")}')
                        redis_mng.del_redis_key_property(rkey, r_item)
                    except:
                        print(f'{rkey}, {r_item} not available in redis db or redis \
                            db not online')

                sar_files = os.listdir(upload_dir)
                sar_files = [x.rstrip('.df') for x in sar_files if x.endswith('.df')]
                dfiles = dfiles_ph.multiselect(
                    'Choose your Files to delete', sar_files, default=None)
        else:
            st.write("You currently have no sar files")

    elif managef_options == 'Show Sar Files':
        st.empty()
        st.write(df.DataFrame(sar_files, columns=['Files']))
