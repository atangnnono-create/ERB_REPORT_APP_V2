import streamlit as st
from services.api_client import APIClient


def login_ui(api: APIClient):
    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password")
            return

        with st.spinner("Logging in..."):
            success = api.login(username, password)
            if success:
                # ✅ Get user profile to store role and other info
                user_success, user_info = api.get_current_user()

                # DEBUG: Show what we're getting from the backend
                st.info(f"DEBUG: User info received: {user_info}")

                if user_success and user_info:
                    # Store ALL user information properly
                    st.session_state.user_role = user_info.get("role", "candidate")
                    st.session_state.user_email = user_info.get("email", "")
                    st.session_state.full_name = user_info.get("full_name", "")
                    st.session_state.user_id = user_info.get("id")
                    st.session_state.is_verified = user_info.get("is_verified", False)
                    st.session_state.is_active = user_info.get("is_active", True)

                    st.success(f"✅ Login successful! Role: {st.session_state.user_role}")
                else:
                    # Fallback if user info can't be retrieved
                    st.session_state.user_role = "candidate"
                    st.warning("⚠️ Logged in but couldn't retrieve user details")

                st.session_state.token = api.token
                st.session_state.username = username
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Login failed: Invalid username or password")

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

            # Show loading state
            with st.spinner("Creating your account..."):
                success, res = api.register(username, email, password, full_name)

                # Debug information
                with st.expander("Debug Information"):
                    st.write(f"API Base URL: {api.base_url}")
                    st.write(f"Full Endpoint: {api.base_url}/api/v1/auth/register")
                    st.write(f"Success: {success}")
                    st.write(f"Response: {res}")

                if success:
                    if res and res.get("username"):
                        st.success(f"🎉 Registered {res['username']} successfully!")
                        st.info("📧 A verification email has been sent to your email address.")
                        st.info("You can now login with your credentials.")
                    else:
                        st.success("✅ Registration request sent successfully!")
                        st.info("Please check your email for verification.")
                else:
                    detail = res.get("detail", "Unknown error")
                    st.error(f"❌ Registration failed: {detail}")

                    # Show helpful error messages
                    if "already registered" in detail.lower():
                        st.info("💡 This username or email is already taken. Please try a different one.")
                    elif "connection" in detail.lower():
                        st.error("🔌 Cannot connect to the server. Please check if the backend is running.")
                    elif "not found" in detail.lower():
                        st.error("🌐 Endpoint not found. Please check the API URL configuration.")