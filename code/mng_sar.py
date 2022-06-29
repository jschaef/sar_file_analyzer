#!/usr/bin/python3
import os
import pandas as df
import streamlit as st
from magic import Magic
from datetime import datetime
import redis_mng
import helpers
from config import Config
import visual_funcs as visf


def file_mng(upload_dir, col, username):
    col1, col2, col3, col4 = visf.create_columns(4,[0,1,1,1])
    manage_files = ['Show Sar Files','Add Sar Files', 'Delete Sar Files']
    sar_files = [ x for x in os.listdir(upload_dir) if os.path.isfile(f'{upload_dir}/{x}')]
    sar_files_uploaded =[x for x in sar_files if not x.endswith(('.df'))]
    sar_files = [x.rstrip('\.df') for x in sar_files if x.endswith(('.df'))]
    sar_files.extend(sar_files_uploaded)

    managef_options = col1.selectbox(
        'Show/Add/Delete', manage_files)

    st.markdown('___')
    if managef_options == 'Add Sar Files':
        st.set_option(
            'deprecation.showfileUploaderEncoding', False)
        sar_files = [col1.file_uploader(
            "Please upload your SAR files, (Posix format, decimal seperator must be '.')", key='sar_uploader',
            accept_multiple_files=True)]
        if col1.button('Submit'):
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
                                col1.warning(
                                    f'File is not a valid sar ASCII data file. Instead {res}')
                                continue
                            else:
                                #TODO check if Linux Header is present and if sar sections are present
                                col1.write(
                                    f"Sar file is valid. Renaming {u_file.name}")
                                with open(f'{upload_dir}/{u_file.name}', 'wb') as targetf:
                                    targetf.write(bytes_data)
                                #remove name
                                col1, col2 = visf.create_columns(2,[0,1])
                                renamed_name = helpers.rename_sar_file(f'{upload_dir}/{u_file.name}', col=col1)
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
            dfiles_ph = col1.empty()
            dfiles = dfiles_ph.multiselect(
                'Choose your Files to delete', sar_files)
            if col1.button('Delete selected Files'):
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
            col1.write("You currently have no sar files")

    elif managef_options == 'Show Sar Files':
        col1.empty()
        col1.write(df.DataFrame(sar_files, columns=['Files']))
