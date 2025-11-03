import streamlit as st
from services.enhanced_api_client import EnhancedAPIClient


def set_professional_style():
    """Enhanced CSS with professional visual design"""
    st.markdown(
        """
        <style>
        /* Main background with subtle gradient */
        .stApp {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }

        /* Professional container for forms */
        .form-container {
            background: white;
            border-radius: 12px;
            padding: 0;  /* Remove padding from container */
            margin: 2rem auto;
            max-width: 420px;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06),
                0 0 0 1px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            overflow: hidden;  /* Ensure content stays within rounded corners */
        }

        /* Form content area with proper padding */
        .form-content {
            padding: 0.5rem;
        }

        /* Enhanced button styling with gradient */
        .stButton button {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.875rem 1.5rem;
            font-weight: 600;
            width: 100%;
            font-size: 1rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 
                0 8px 25px -8px #007bff,
                0 4px 12px -4px rgba(0, 123, 255, 0.3);
        }

        .stButton button:active {
            transform: translateY(0);
        }

        /* Enhanced input field styling */
        .stTextInput>div>div>input {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 0.875rem 1rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #ffffff;
        }

        .stTextInput>div>div>input:focus {
            border-color: #007bff;
            box-shadow: 
                0 0 0 3px rgba(0, 123, 255, 0.1),
                0 2px 8px rgba(0, 123, 255, 0.1);
            background: #ffffff;
        }

        .stTextInput>div>div>input:hover {
            border-color: #adb5bd;
        }

        /* Professional header styling - FIXED */
        .form-header {
            text-align: center;
            margin-bottom: 0;  /* Remove bottom margin */
            padding: 1.0rem 1.0rem 0.5rem 1.0rem;  /* Add proper padding */
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }

        .form-header h2 {
            color: #2d3748;
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.1rem;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .form-header p {
            color: #718096;
            font-size: 1rem;
            margin: 0;
        }

        /* Enhanced footer styling */
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: white;
            text-align: center;
            padding: 1.25rem;
            font-size: 0.875rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Professional alert styling */
        .stAlert {
            border-radius: 8px;
            border: 1px solid;
            padding: 1rem;
        }

        .stAlert [data-testid="stMarkdownContainer"] {
            font-weight: 500;
        }

        /* Success state enhancements */
        .success-animation {
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Loading state improvements */
.custom-spinner {
    text-align: center;
    padding: 2rem;
}

.spinner-circle {
    width: 40px;
    height: 40px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Enhanced Streamlit spinner styling */
.stSpinner > div {
    border-color: #007bff transparent transparent transparent !important;
}
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}

        /* Responsive improvements */
        @media (max-width: 768px) {
            .form-container {
                margin: 1rem;
                max-width: calc(100% - 2rem);
            }
            .form-header {
                padding: 0.5rem 0.5rem 0.5rem 05rem;
            }
            .form-content {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def show_footer():
    """Display the enhanced copyright footer"""
    st.markdown(
        """
        <div class="footer">
            <strong>Developed by TurtleTEC Solutions Africa</strong><br>
            © 2025. ALL RIGHTS RESERVED.
        </div>
        """,
        unsafe_allow_html=True
    )


def show_loading_state(message="Processing..."):
    """Use Streamlit's native spinner with custom message"""
    with st.spinner(message):
        # This will automatically clear when the context exits
        pass


def show_success_message(message, user_name=None):
    """Enhanced success message with animation"""
    if user_name:
        message = f"🎉 Welcome back, {user_name}!"

    st.markdown(f"""
    <div class="success-animation">
        <div style="
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            text-align: center;
            margin: 1rem 0;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
            <div style="font-weight: 600; font-size: 1.1rem;">{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def login_ui(api: EnhancedAPIClient):
    """Enhanced login UI with professional styling"""
    set_professional_style()

    # Use columns to center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        # Professional header - NOW WITH PROPER BACKGROUND
        st.markdown("""
        <div class="form-header">
            <h2>Welcome Back</h2>
            <p>Sign in to your Engineering Report Deck account</p>
        </div>
        """, unsafe_allow_html=True)

        # Form content area
        st.markdown('<div class="form-content">', unsafe_allow_html=True)

        # Login Form
        with st.form("login_form", clear_on_submit=False):
            # Username field
            username = st.text_input(
                "Username",
                placeholder="Enter your username"
            )

            # Password field
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            # Enhanced SIGN IN button
            login_submitted = st.form_submit_button("🚀 SIGN IN", use_container_width=True)

            if login_submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    handle_login(api, username, password)

        st.markdown('</div>', unsafe_allow_html=True)  # Close form-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close form-container

    show_footer()


def register_ui(api: EnhancedAPIClient):
    """Enhanced registration UI with professional styling"""
    set_professional_style()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        # Professional header
        st.markdown("""
        <div class="form-header">
            <h2>Create Account</h2>
            <p>Join the Engineering Report Deck platform</p>
        </div>
        """, unsafe_allow_html=True)

        # Form content area
        st.markdown('<div class="form-content">', unsafe_allow_html=True)

        with st.form("register_form", clear_on_submit=False):
            # Form fields
            username = st.text_input(
                "Username *",
                placeholder="Choose a username"
            )

            email = st.text_input(
                "Email Address *",
                placeholder="your.email@example.com"
            )

            full_name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name"
            )

            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Create a strong password"
            )

            # Enhanced CREATE ACCOUNT button
            register_submitted = st.form_submit_button("📝 CREATE ACCOUNT", use_container_width=True)

            if register_submitted:
                handle_registration(api, username, email, full_name, password)

        st.markdown('</div>', unsafe_allow_html=True)  # Close form-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close form-container

    show_footer()


def forgot_password_ui(api: EnhancedAPIClient):
    """Enhanced forgot password UI with professional styling"""
    set_professional_style()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        # Professional header
        st.markdown("""
        <div class="form-header">
            <h2>Reset Password</h2>
            <p>We'll help you regain access to your account</p>
        </div>
        """, unsafe_allow_html=True)

        # Form content area
        st.markdown('<div class="form-content">', unsafe_allow_html=True)

        st.info("Enter your email address and we'll send you a password reset link.")

        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com"
        )

        # Enhanced SEND RESET LINK button
        if st.button("📧 SEND RESET LINK", use_container_width=True):
            handle_forgot_password(api, email)

        st.markdown('</div>', unsafe_allow_html=True)  # Close form-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close form-container

    show_footer()


def handle_login(api: EnhancedAPIClient, username: str, password: str):
    """Enhanced login logic with professional loading states - FIXED DUPLICATE SPINNER"""
    # Use our custom loading state instead of st.spinner
    show_loading_state("Authenticating your credentials...")

    success = api.login(username, password)

    if success:
        # Get user profile to store role and other info
        user_success, user_info = api.get_current_user()

        if user_success and user_info:
            # Store ALL user information properly
            st.session_state.user_role = user_info.get("role", "candidate")
            st.session_state.user_email = user_info.get("email", "")
            st.session_state.full_name = user_info.get("full_name", "")
            st.session_state.user_id = user_info.get("id")
            st.session_state.is_verified = user_info.get("is_verified", False)
            st.session_state.is_active = user_info.get("is_active", True)

            show_success_message("Login successful!", st.session_state.full_name or username)
        else:
            # Fallback if user info can't be retrieved
            st.session_state.user_role = "candidate"
            st.warning("⚠️ Logged in but couldn't retrieve user details")

        st.session_state.token = api.token
        st.session_state.username = username
        st.session_state.logged_in = True

        # Small delay to show success message before rerun
        import time
        time.sleep(1.5)
        st.rerun()
    else:
        st.error("❌ Login failed: Invalid username or password")


def handle_registration(api: EnhancedAPIClient, username: str, email: str, full_name: str, password: str):
    """Enhanced registration logic - FIXED DUPLICATE SPINNER"""
    if not username or not email or not password or not full_name:
        st.error("⚠️ Please fill in all required fields (*)")
        return

    # Use our custom loading state
    show_loading_state("Creating your account...")

    success, res = api.register(username, email, password, full_name)

    if success:
        if res and res.get("username"):
            st.balloons()
            show_success_message(f"Account created for {res['username']}!")
            st.info("📧 A verification email has been sent to your email address.")
            st.info("You can now login with your credentials.")
        else:
            show_success_message("Registration request sent successfully!")
            st.info("Please check your email for verification.")
    else:
        detail = res.get("detail", "Unknown error")
        st.error(f"❌ Registration failed: {detail}")


def handle_forgot_password(api: EnhancedAPIClient, email: str):
    if not email:
        st.error("⚠️ Please enter your email address")
        return

    with st.spinner("Sending reset link..."):
        success, result = api.forgot_password(email)

    if success:
        show_success_message("Check your email for the reset link!")
        st.info("💡 **Tip:** Check your spam folder if you don't see the email within a few minutes.")
    else:
        st.error(f"❌ {result.get('detail', 'Failed to send reset email')}")

def reset_password_ui(api: EnhancedAPIClient):
    """Reset password UI - handle token from URL and set new password"""
    st.header("🔄 Set New Password")

    # Check for reset token in URL (support both parameter names)
    query_params = st.query_params
    token = None

    # First check for the new reset_token parameter
    if 'reset_token' in query_params:
        token_param = query_params['reset_token']
        token = token_param[0] if isinstance(token_param, list) else token_param
        print(f"=== DEBUG: Using reset_token: {token} ===")
    # Fallback to token parameter for backward compatibility
    elif 'token' in query_params:
        token_param = query_params['token']
        token = token_param[0] if isinstance(token_param, list) else token_param
        print(f"=== DEBUG: Using token: {token} ===")

    if not token:
        st.error("❌ Invalid or missing reset token")
        st.info("Please use the password reset link from your email.")
        return

    # Validate token first
    with st.spinner("Validating reset link..."):
        success, validation_result = api.validate_reset_token(token)

        if not success:
            st.error("❌ Invalid or expired reset link")
            st.info("Please request a new password reset link.")
            return

    # Password reset form
    st.success("✅ Reset link validated! Please enter your new password.")

    password_reset_success = False  # Track if reset was successful

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
                    password_reset_success = True

                    # Clear token from URL
                    st.query_params.clear()
                else:
                    st.error(f"❌ {result.get('detail', 'Failed to reset password')}")

    # Show login button OUTSIDE the form, only after successful reset
    if password_reset_success:
        st.markdown("---")
        if st.button("🔑 Go to Login", use_container_width=True):
            st.rerun()