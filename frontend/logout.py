import streamlit as st

def logout_ui():
    if st.sidebar.button("Logout", key="sidebar_logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.token = None
        st.rerun()