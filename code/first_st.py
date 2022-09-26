#!/usr/bin/python3

import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
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


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">',
                unsafe_allow_html=True)

def icon(icon_name):
    st.markdown(
        f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)

local_css("style.css")
remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')

def start():
    """Sar analyzeer App"""
    st.title = "SAR Analyzer"
    with st.sidebar:
        choice = option_menu("Menu", ["Login", "Signup", "Help", "Logout"],
                             icons=['arrow-right-circle-fill',
                                    'pencil', 'question-square', 'arrow-left-circle-fill'],
                             menu_icon="app-indicator", default_index=0,
                             styles={
            "container": {"padding": "5!important", "background-color": "#91cfec",},
            "icon": {"color": "orange", "font-size": "25px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee",
                         "background-color": "#91cfe"},
            "nav-link-selected": {"background-color": "#1a7c78"},
        }
        )
        
    sql_stuff.create_tables()
    config_c = helpers.configuration({})

    if choice == "Help":
        help.help()
    elif choice == "Logout":
        choice = "Login"
    elif choice == "Login":
        ph_username = st.sidebar.empty()
        ph_password = st.sidebar.empty()
        ph_login = st.sidebar.empty()
        username = ph_username.text_input("Username")
        password = ph_password.text_input("Password", type='password')
        if ph_login.checkbox("Login"):
            if sql_stuff.login_user(username, password):
                ph_username.empty()
                ph_password.empty()
                ph_login.empty()
                upload_dir = f'{Config.upload_dir}/{username}'
                os.system(f'mkdir -p {upload_dir}')
                sar_files = os.listdir(upload_dir)
                st.sidebar.success(f"Logged in as {username}")
                
                col1, col2 = st.columns(2)
                config_c.update_conf({'username': username, 'upload_dir': upload_dir,
                    'sar_files':sar_files, 'cols':[col1, col2]})
                if sql_stuff.get_role(username) == "admin":
                    top_choice = option_menu("Tasks",  ["Analyze Data", "Manage Sar Files", "DB Management",
                        "Redis Management", "TODO", "Self Service", "User Management", "Info"],
                             icons=['calculator', 'receipt', 'bank', 'hdd-stack','clipboard','person', 
                                'people', 'info-circle', ],
                             menu_icon="yin-yang", default_index=0, orientation="horizontal",
                        styles={
                            "container": {"padding": "4!important", "background-color": "#91cfec", 
                                "margin-top" : 0,
                                },
                            "icon": {"color": "orange", "font-size": "12px"},
                            "nav-link": {"font-size": "12px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                            "nav-link-selected": {"background-color": "#1a7c78"},
                        }
                    )
                else:
                    top_choice = option_menu("Tasks",  ["Analyze Data", "Manage Sar Files",
                        "Self Service", "Info"],
                             icons=['calculator', 'receipt', 'person', 'info-circle', ],
                             menu_icon="yin-yang", default_index=0, orientation="horizontal",
                        styles={
                            "container": {"padding": "4!important", "background-color": "#91cfec", "margin-top" : 0},
                            "icon": {"color": "orange", "font-size": "12px"},
                            "nav-link": {"font-size": "12px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                            "nav-link-selected": {"background-color": "#1a7c78"},
                        }
                    )
                if top_choice == "Manage Sar Files":
                    mng_sar.file_mng(upload_dir, col2, username)
                elif top_choice == "Analyze Data":
                    analyze.analyze(upload_dir, config_c, username)
                elif top_choice == "DB Management":
                    db_mng.db_mgmt()
                elif top_choice == "TODO":
                    todo.todo()
                elif top_choice == "Redis Management":
                    try:
                        redis_mng.redis_tasks(col2)
                    except:
                        #st.markdown('Redis server seeems to be offline')
                        ''
                elif top_choice == "Info":
                    info.info()
                    info.usage()
                    info.code()
                elif top_choice == 'Self Service':
                    ss.self_service(username)
                elif top_choice == 'User Management':
                    ss.admin_service() 
            else:
                st.warning("You don't exist or your password does not match")
        else:
            st.markdown("## Please login to use this app")
    elif (choice) == "Signup":
        st.subheader("Create an Account")
        col1, col2 = st.columns([0.2, 0.8])
        new_user = col1.text_input("Username")
        new_password = col1.text_input("Password", type='password')
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
