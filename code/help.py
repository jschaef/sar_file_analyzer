import streamlit as st
from config import Config

def help():
    st.header("SAR Analyzer")
    st.markdown(f'Please register first. \
        If you have forgotten your password reregister a new user or \
        ask {Config.admin_email} :email: to reset your account.')

    st.markdown('__Left pane__ :arrow_right: __Menu__ :arrow_right: __Signup__.')