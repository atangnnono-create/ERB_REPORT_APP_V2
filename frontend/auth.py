import streamlit as st
from services.enhanced_api_client import EnhancedAPIClient


def login_ui(api: EnhancedAPIClient):
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

def register_ui(api: EnhancedAPIClient):
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

                if success:
                    if res and res.get("username"):
                        st.balloons()
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


def forgot_password_ui(api: EnhancedAPIClient):
    """Forgot password UI - request reset email"""
    st.header("🔒 Reset Your Password")

    st.info("Enter your email address and we'll send you a password reset link.")

    email = st.text_input("📧 Email Address", placeholder="your.email@example.com")

    if st.button("📨 Send Reset Link", type="primary", use_container_width=True):
        if not email:
            st.error("Please enter your email address")
            return

        with st.spinner("Sending reset link..."):
            success, result = api.forgot_password(email)

            if success:
                st.success("✅ Check your email! If an account exists, you'll receive a password reset link shortly.")
                st.info("💡 **Tip:** Check your spam folder if you don't see the email within a few minutes.")
            else:
                st.error(f"❌ {result.get('detail', 'Failed to send reset email')}")


def reset_password_ui(api: EnhancedAPIClient):
    """Reset password UI - handle token from URL and set new password"""
    st.header("🔄 Set New Password")

    # Check for reset token in URL
    query_params = st.query_params
    if 'token' not in query_params:
        st.error("❌ Invalid or missing reset token")
        st.info("Please use the password reset link from your email.")
        return

    token = query_params['token'][0] if isinstance(query_params['token'], list) else query_params['token']

    # Validate token first
    with st.spinner("Validating reset link..."):
        success, validation_result = api.validate_reset_token(token)

        if not success:
            st.error("❌ Invalid or expired reset link")
            st.info("Please request a new password reset link.")
            return

    # Password reset form
    st.success("✅ Reset link validated! Please enter your new password.")

    with st.form("reset_password_form"):
        new_password = st.text_input("🔑 New Password", type="password",
                                     help="Password must be at least 8 characters with uppercase, lowercase, and numbers")
        confirm_password = st.text_input("✅ Confirm New Password", type="password")

        submitted = st.form_submit_button("🔄 Reset Password", use_container_width=True)

        if submitted:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields")
                return

            if new_password != confirm_password:
                st.error("Passwords do not match")
                return

            # Additional client-side validation
            if len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
                return

            with st.spinner("Resetting password..."):
                success, result = api.reset_password(token, new_password)

                if success:
                    st.success("🎉 Password reset successfully!")
                    st.balloons()
                    st.info("You can now login with your new password.")

                    # Clear token from URL
                    st.query_params.clear()

                    if st.button("🔑 Go to Login", use_container_width=True):
                        st.rerun()
                else:
                    st.error(f"❌ {result.get('detail', 'Failed to reset password')}")