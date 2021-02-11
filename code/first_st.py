#!/usr/bin/python3

import streamlit as st
import os
import time
import sql_stuff
from config import Config
import mng_sar
import analyze
import db_mng
import helpers
import todo
import redis_mng
import beta
import help
import info

start_time = time.perf_counter()

def start():
    """Sar analyzeer App"""
    st.title = "SAR Analyzer"
    menu = ["Login", "Signup", "Help"]
    choice = st.sidebar.selectbox("Menu", menu)
    sql_stuff.create_tables()
    config_c = helpers.configuration({})

    if choice == "Help":
        help.help()

    elif choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            if sql_stuff.login_user(username, password):
                userl = username
                upload_dir = f'{Config.upload_dir}/{username}'
                os.system(f'mkdir -p {upload_dir}')
                sar_files = os.listdir(upload_dir)
                st.sidebar.success("Logged in as {}".format(username))
                
                col1, col2 = st.beta_columns(2)
                config_c.update_conf({'username': username, 'upload_dir': upload_dir,
                    'sar_files':sar_files, 'cols':[col1, col2]})
                if sql_stuff.get_role(username) == "admin":
                    task = st.sidebar.selectbox("Tasks", ["Analyze Data", "Manage Sar Files", "DB Management",
                    "Redis Management", "Beta", "TODO", "Self Service", "Info"])
                else:
                    task = st.sidebar.selectbox("Tasks", ["Analyze Data", "Manage Sar Files", "Info"])

                if task == "Manage Sar Files":
                    mng_sar.file_mng(upload_dir, col2, username)
                elif task == "Analyze Data":
                    analyze.analize(upload_dir, config_c, username)
                elif task == "DB Management":
                    db_mng.db_mgmt(username, col2)
                elif task == "TODO":
                    todo.todo()
                elif task == "Redis Management":
                    try:
                        redis_mng.redis_tasks(col2)
                    except:
                        #st.markdown('Redis server seeems to be offline')
                        ''
                elif task == "Beta":
                    beta.test_dia()
                elif task == "Info":
                    info.info()
                    info.usage()


            else:
                st.warning("You don't exist or your password does not match")

    elif (choice) == "Signup":
        st.subheader("Create an Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')

        if st.button("Signup"):
            if sql_stuff.add_userdata(new_user,new_password):
                st.success("You have successfully created an valid Account")
                st.info("Goto Login Menu to login")
            else:
                st.warning(f'User {new_user} already exists')
    

if __name__ == "__main__":
    start()
    end = time.perf_counter()
    st.write(f'process_time: {round(end-start_time, 4)}')
