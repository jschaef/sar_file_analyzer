#!/usr/bin/python3
import os
import streamlit as st
import sql_stuff
import pandas as pd
from config import Config

def self_service(username):
    menu_items = ['Password Change']
    choice = st.selectbox('Take your Choice',menu_items)
    if choice == 'Password Change':
        st.header('Change your Password')
        password = st.text_input("Type your new password:", type='password')
        re_password = st.text_input("Retype your new password:", type='password')
        if st.button('Submit'):
            if password == re_password:
                sql_stuff.change_password(username, password)
                st.info('Your Password has been Changed')
            else:
                st.warning("your password does not match")

def admin_service():
    st.header('User Management')
    menu_items = ['Show Users', 'User Password Change', 'Roles Management', 'Delete User']
    choice = st.selectbox('Take your Choice',menu_items)
    if choice == 'Show Users':
         st.write(pd.DataFrame(sql_stuff.view_all_users('show'), columns=["Username", "Role"]))    
    else:
        user = st.selectbox('Choose User', sql_stuff.view_all_users(kind=None))
    if choice == 'User Password Change':
        st.subheader(f'Change Password of {user}')
        password = st.text_input("Type the new password:", type='password')
        re_password = st.text_input("Retype your new password:", type='password')
        if st.button('Submit'):
            if password == re_password:
                sql_stuff.change_password(user, password)
                st.info(f'Password of {user} has been Changed')
            else:
                st.warning("The passwords do not match") 
    elif choice == 'Roles Management':
        st.subheader(f'Change Role of {user}')
        r_content = st.selectbox('Choose role', sql_stuff.ret_all_roles())
        if st.button('Submit'):
            sql_stuff.modify_user(user, r_content)
            st.info(f'Role {r_content} for {user} has been set')
    elif choice == 'Delete User':
        upload_dir = f'{Config.upload_dir}/{user}'
        st.subheader(f'Delete User {user}')
        if st.button('Submit'):
            sql_stuff.delete_user(user)
            if user in upload_dir:
                os.system(f'rm -rf {upload_dir}')
            st.info(f'User {user} has been deleted')

        
