import streamlit as st
from api_client import APIClient
from datetime import datetime


def verification_ui(api: APIClient):
    """Enhanced email verification interface"""
    st.title("📧 Email Verification")

    # Check if user is verified
    success, user_data = api.get_current_user()

    if not success:
        st.error("Failed to load user data")
        return

    user_email = user_data.get('email')
    is_verified = user_data.get('is_verified', False)
    username = user_data.get('username', '')

    if is_verified:
        show_verified_status(username)
        return

    # User is not verified - show verification flow
    show_verification_flow(api, user_email, username)


def show_verified_status(username: str):
    """Show verified status with congratulations"""
    st.success("🎉 **Email Verified Successfully!**")

    st.balloons()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"### Welcome aboard, {username}!")
        st.write("Your email address has been verified and your account is now fully activated.")

        st.info("""
        **You now have access to all features:**
        - ✅ Create and submit engineering reports
        - ✅ Receive AI-powered feedback on your work
        - ✅ Track your progress across all competencies
        - ✅ Export your reports in multiple formats
        """)

    with col2:
        st.image("🔓", width=100)  # You can add a proper image here
        st.write("")
        st.write("**Ready to get started?**")
        if st.button("🚀 Create Your First Report"):
            st.switch_page("pages/create_report.py")


def show_verification_flow(api: APIClient, user_email: str, username: str):
    """Show verification required flow"""
    st.warning("⚠️ **Email Verification Required**")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"**Email Address:** {user_email}")
        st.write(f"**Username:** {username}")
        st.write("**Status:** ❌ Not Verified")

        st.write("")
        st.write("**To access all features, please verify your email address:**")

        st.info("""
        **Why verify your email?**
        - 🔐 Secure your account
        - 📧 Receive important notifications
        - 📊 Submit reports for review
        - 🤖 Get AI feedback on your work
        """)

    with col2:
        st.markdown("""
        <div style="text-align: center; font-size: 80px;">
            📧
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.write("### Verification Steps")
        st.write("1. Check your inbox for verification email")
        st.write("2. Click the verification link")
        st.write("3. Return here to continue")

    st.markdown("---")

    # Resend verification section
    st.subheader("📨 Need a new verification email?")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🔄 Resend Verification Email", key="resend_verification_main", use_container_width=True):
            with st.spinner("Sending verification email..."):
                success, result = api.resend_verification_email(user_email)
                if success:
                    st.success("✅ Verification email sent! Please check your inbox.")
                    st.info("📋 **Don't forget to check your spam folder if you don't see it.**")
                else:
                    st.error(f"❌ Failed to send email: {result.get('detail', 'Unknown error')}")

    # Check verification status
    st.markdown("---")
    st.write("### 🔍 Check Verification Status")
    if st.button("🔄 Refresh Status", key="refresh_status"):
        st.rerun()


def verification_required_message():
    """Show message when verification is required for a feature"""
    st.warning("🔐 **Verification Required**")

    st.write("""
    This feature requires email verification to ensure the security and integrity of your account.

    **Please verify your email address to:**
    - Submit reports for official review
    - Receive status notifications  
    - Access advanced AI features
    - Ensure your work is properly saved
    """)

    st.info("💡 **Go to your Profile page to resend the verification email or check your status.**")


def check_verification_status(api: APIClient) -> bool:
    """Check if current user is verified - returns True if verified"""
    success, user_data = api.get_current_user()
    if success:
        return user_data.get('is_verified', False)
    return False


def get_verification_info(api: APIClient, email: str):
    """Get detailed verification information"""
    # You would implement an API endpoint for this
    return {
        "is_verified": False,
        "can_resend": True,
        "last_sent": None
    }