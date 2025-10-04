import os
import streamlit as st
from api_client import APIClient
import auth, reports, create_report
import about, contact

st.set_page_config(page_title="🏭 Engineering Report Deck", layout="centered")
# ================== APP BANNER ==================
APP_VERSION = "v1.1 — Hypothesis Prime"
st.markdown(
    f"""
    <div style="
        position: relative;
        background: linear-gradient(90deg, #2c3e50, #3498db);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    ">
    <h1 style="margin:0;">🏭 Engineering Report Deck</h1>
    <p style="margin:0; font-size:1.1rem;"> AI Revolution Driving Engineering Evolution ✨ </p>
    <p style="margin-top:0.5rem; font-size:0.9rem; opacity:0.85;">
        <b>Version:</b> {APP_VERSION}
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)

API_BASE_URL = os.environ.get("API_BASE_URL", "https://erb-backend.onrender.com")

# ----------------- Session Init ----------------- #
if "api" not in st.session_state:
    st.session_state.api = APIClient()

api = st.session_state.api

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = ""

# ----------------- Auth Gate ----------------- #
if not st.session_state.logged_in:
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        auth.login_ui(api)
    with register_tab:
        auth.register_ui(api)
    st.stop()  # Stop rendering until logged in

# ----------------- Main App Navigation ----------------- #
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.token = None
    st.rerun()  # Forces redirect to login

st.sidebar.success(f"👋 Logged in as {st.session_state.username}")

# ✅ Extended navigation menu
page = st.sidebar.radio(
    "📑 Navigation",
    ["Reports", "Create Report", "About", "Contact"]
)

if page == "Reports":
    reports.reports_ui(api)
elif page == "Create Report":
    create_report.main_ui()
elif page == "About":
    about.show()
elif page == "Contact":
    contact.show()
