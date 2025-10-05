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
            # ✅ Get user profile to store role and other info
            user_success, user_info = api.get_current_user()
            if user_success:
                st.session_state.user_role = user_info.get("role", "candidate")
                st.session_state.user_email = user_info.get("email", "")
                st.session_state.full_name = user_info.get("full_name", "")
            else:
                st.session_state.user_role = "candidate"

            st.session_state.token = api.token
            st.session_state.username = username
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Login failed: Invalid username or password")

    # ✅ Return nothing - the function handles session state internally
    return None

def register_ui(api: APIClient):
    st.header("📝 Register")

    with st.form("registration_form"):
        username = st.text_input("Username *")
        email = st.text_input("Email Address *")
        full_name = st.text_input("Full Name")
        password = st.text_input("Password *", type="password")

        submitted = st.form_submit_button("Register")

        if submitted:
            if not username or not email or not password:
                st.error("Please fill in all required fields (*)")
                return

            success, res = api.register(username, email, password, full_name)

            if success and res.get("username"):
                st.success(f"🎉 Registered {res['username']} successfully!")
                st.info("You can now login with your credentials.")
            else:
                detail = res.get("detail", "Unknown error")
                st.error(f"❌ Registration failed: {detail}")