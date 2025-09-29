import streamlit as st
from api_client import APIClient

api = APIClient()


def login_ui(api: APIClient):
    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success = api.login(username, password)
        if success:
            st.session_state.token = api.token
            st.session_state.username = username
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()  # Forces redirect to main app
        else:
            st.error("❌ Login failed: Invalid username or password")


def register_ui(api: APIClient):
    st.header("📝 Register")

    username = st.text_input("New Username", key="register_username")
    password = st.text_input("New Password", type="password", key="register_password")

    if st.button("Register", key="register_button"):
        success, res = api.register(username, password)

        # Make sure res is always a dict
        if not isinstance(res, dict):
            st.error("⚠️ Unexpected server response.")
            return

        if success and res.get("username"):
            st.success(f"🎉 Registered {res['username']} successfully!")

            # Auto-login immediately after registration
            if api.login(username, password):
                st.session_state.token = api.token
                st.session_state.username = username
                st.session_state.logged_in = True
                st.rerun()
        else:
            detail = res.get("detail", "Unknown error")
            st.error(f"❌ Registration failed: {detail}")