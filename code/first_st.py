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
import help
import info
import self_service as ss

st.set_page_config(
    page_title="Happy SAR Analyzer",
    layout='wide',
    page_icon="wiki_pictures/kisspng-penguin-download-ico-icon-penguin-5a702cc04e5fc1.8432243315173009283211.png",
)

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
                upload_dir = f'{Config.upload_dir}/{username}'
                os.system(f'mkdir -p {upload_dir}')
                sar_files = os.listdir(upload_dir)
                st.sidebar.success(f"Logged in as {username}")
                
                col1, col2 = st.columns(2)
                config_c.update_conf({'username': username, 'upload_dir': upload_dir,
                    'sar_files':sar_files, 'cols':[col1, col2]})
                if sql_stuff.get_role(username) == "admin":
                    task = st.sidebar.selectbox("Tasks", ["Analyze Data", "Manage Sar Files", "DB Management",
                    "Redis Management", "TODO", "Self Service", "User Management", "Info"])
                else:
                    task = st.sidebar.selectbox("Tasks", ["Analyze Data", "Manage Sar Files", "Self Service", "Info"])

                if task == "Manage Sar Files":
                    mng_sar.file_mng(upload_dir, col2, username)
                elif task == "Analyze Data":
                    analyze.analyze(upload_dir, config_c, username)
                elif task == "DB Management":
                    db_mng.db_mgmt()
                elif task == "TODO":
                    todo.todo()
                elif task == "Redis Management":
                    try:
                        redis_mng.redis_tasks(col2)
                    except:
                        #st.markdown('Redis server seeems to be offline')
                        ''
                elif task == "Info":
                    info.info()
                    info.usage()
                    info.code()

                elif task == 'Self Service':
                    ss.self_service(username)
                elif task == 'User Management':
                    ss.admin_service() 

            else:
                st.warning("You don't exist or your password does not match")
        else:
            st.header("Please login to use this app")
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
