import streamlit as st
from services.api_client import APIClient
from services import verification  # ✅ Add import


def user_profile(api: APIClient):
    st.title("👤 Your Profile")

    # Fetch current user data
    success, user_data = api.get_current_user()

    if not success:
        st.error("Failed to load profile data")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Profile Information")

        with st.form("profile_form"):
            username = st.text_input("Username", value=user_data.get('username', ''), disabled=True)
            email = st.text_input("Email Address", value=user_data.get('email', ''))
            full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))
            role = st.text_input("Role", value=user_data.get('role', 'candidate').title(), disabled=True)

            if st.form_submit_button("Update Profile"):
                update_data = {}
                if email != user_data.get('email'):
                    update_data['email'] = email
                if full_name != user_data.get('full_name'):
                    update_data['full_name'] = full_name

                if update_data:
                    success, result = api.update_profile(update_data)
                    if success:
                        st.success("Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update profile: {result.get('detail', 'Unknown error')}")
                else:
                    st.info("No changes made")

    with col2:
        st.subheader("Account Status")
        st.write(f"**Username:** {user_data.get('username', 'N/A')}")
        st.write(f"**Role:** {user_data.get('role', 'candidate').title()}")

        # ✅ Enhanced verification status
        is_verified = user_data.get('is_verified', False)
        verification_status = "✅ Verified" if is_verified else "❌ Not Verified"
        st.write(f"**Email Verified:** {verification_status}")

        st.write(f"**Account Active:** {'✅ Yes' if user_data.get('is_active', True) else '❌ No'}")
        st.write(f"**Member Since:** {user_data.get('created_at', 'N/A')}")

    # ✅ Show verification section if not verified (outside columns)
    if not is_verified:
        st.markdown("---")
        st.subheader("Email Verification")
        verification.verification_ui(api)


def profile_page(api: APIClient):
    """Main profile page function"""
    user_profile(api)