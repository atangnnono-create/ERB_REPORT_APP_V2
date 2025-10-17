import streamlit as st
from services.enhanced_api_client import EnhancedAPIClient
import verification
import base64
from io import BytesIO
from PIL import Image
import os
from utilities.error_handling import ErrorHandler, with_loading


def get_default_avatar():
    """Get default avatar from assets folder or generate SVG fallback"""
    assets_path = "assets"
    default_avatar_path = os.path.join(assets_path, "default_avatar.png")

    if os.path.exists(default_avatar_path):
        try:
            with open(default_avatar_path, "rb") as f:
                img_data = f.read()
                img_str = base64.b64encode(img_data).decode()
                return f"data:image/png;base64,{img_str}"
        except Exception as e:
            ErrorHandler.show_warning(f"Could not load default avatar: {e}")

    username = st.session_state.get('username', 'U')
    initials = username[0].upper() if username else 'U'
    colors = ['#1f3a60', '#4a6fa5', '#3498db', '#2c3e50']
    color_index = hash(username) % len(colors) if username else 0
    bg_color = colors[color_index]

    svg = f'''
    <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="{bg_color}" />
                <stop offset="100%" stop-color="#2c3e50" />
            </linearGradient>
        </defs>
        <circle cx="100" cy="100" r="95" fill="url(#gradient)" stroke="#ffffff" stroke-width="3"/>
        <text x="100" y="115" font-family="Arial, sans-serif" font-size="70" font-weight="bold" 
              fill="white" text-anchor="middle" alignment-baseline="middle">{initials}</text>
    </svg>
    '''
    return svg


def display_profile_picture(image_data, width=200):
    """Display profile picture with elegant styling"""
    try:
        if image_data and isinstance(image_data, str) and image_data.startswith('data:image'):
            st.markdown(
                f'''
                <div style="display: flex; justify-content: center;">
                    <div style="width: {width}px; height: {width}px; border-radius: 50%; 
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              padding: 4px; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                        <img src="{image_data}" width="100%" height="100%" 
                             style="border-radius:50%; object-fit: cover; border: 3px solid white;">
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'''
                <div style="display: flex; justify-content: center;">
                    <div style="width: {width}px; height: {width}px; border-radius: 50%; 
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              padding: 4px; box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                              display: flex; align-items: center; justify-content: center;">
                        {get_default_avatar()}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )
    except Exception as e:
        ErrorHandler.show_error(f"Error displaying profile picture: {e}")


@with_loading("Processing image...")
def handle_image_upload(uploaded_file):
    """Process uploaded image and convert to base64"""
    try:
        max_size = 5 * 1024 * 1024
        if uploaded_file.size > max_size:
            ErrorHandler.show_error("File too large. Please choose an image under 5MB.")
            return None

        image = Image.open(uploaded_file)
        if image.format not in ['JPEG', 'PNG', 'GIF']:
            ErrorHandler.show_error("Unsupported image format. Please use JPG, PNG, or GIF.")
            return None

        image.thumbnail((400, 400), Image.Resampling.LANCZOS)

        if image.mode in ('RGBA', 'P', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            image = background

        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return f"data:image/jpeg;base64,{img_str}"

    except Exception as e:
        ErrorHandler.show_error(f"Error processing image: {str(e)}")
        return None


def user_profile(api: EnhancedAPIClient):
    """Main profile page function - SAFE STYLING VERSION"""

    # MINIMAL CSS - Only essential styles that won't break anything
    st.markdown("""
    <style>
    .profile-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f3a60;
        text-align: center;
        margin-bottom: 2rem;
    }
    .profile-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .profile-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f3a60;
    }
    </style>
    """, unsafe_allow_html=True)

    # Simple Header
    st.markdown('<div class="profile-header">👤 Your Profile</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'profile_picture' not in st.session_state:
        st.session_state.profile_picture = None
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0

    # Fetch user data
    success, user_data = api.get_current_user()
    if not success:
        ErrorHandler.show_error("Failed to load profile data")
        return

    # Profile Management Section - PRESERVE EXACT WORKING CODE
    with st.container():
        st.markdown("### 📝 Manage Your Profile")

        with st.container():
            col1, col2 = st.columns([40, 60])

            with col1:
                # Profile Picture Section - EXACT WORKING CODE
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown("**🎯 Profile Picture**")

                # Get current picture
                current_picture = st.session_state.profile_picture or user_data.get('profile_picture')
                display_profile_picture(current_picture, width=180)

                # Upload section
                uploaded_file = st.file_uploader(
                    "📸 Upload New Photo",
                    type=['jpg', 'jpeg', 'png'],
                    help="JPG or PNG, up to 5MB",
                    key=f"uploader_{st.session_state.uploader_key}"
                )

                # Process uploaded file
                processed_image = None
                if uploaded_file is not None:
                    processed_image = handle_image_upload(uploaded_file)
                    if processed_image:
                        st.session_state.temp_profile_picture = processed_image
                        st.success("✅ Image processed! Click 'Save Profile Picture' to apply.")

                        # Show preview
                        st.markdown("**Preview:**")
                        display_profile_picture(processed_image, width=120)

                # Action Buttons - PRESERVE EXACT LOGIC
                col_save, col_revert = st.columns(2)
                with col_save:
                    if st.button("💾 Save Profile Picture", use_container_width=True,
                                 disabled=not hasattr(st.session_state, 'temp_profile_picture')):
                        with st.spinner("🔄 Saving profile picture..."):
                            update_data = {
                                'email': user_data.get('email', ''),
                                'full_name': user_data.get('full_name', ''),
                                'profile_picture': st.session_state.temp_profile_picture
                            }
                            success, result = api.update_profile(update_data)
                            if success:
                                st.success("✅ Profile picture updated successfully!")
                                st.session_state.profile_picture = st.session_state.temp_profile_picture
                                del st.session_state.temp_profile_picture
                                st.session_state.uploader_key += 1
                                st.rerun()
                            else:
                                st.error(f"Failed to save: {result.get('detail', 'Unknown error')}")

                with col_revert:
                    if st.button("↩️ Revert", use_container_width=True,
                                 disabled=not hasattr(st.session_state, 'temp_profile_picture')):
                        if hasattr(st.session_state, 'temp_profile_picture'):
                            del st.session_state.temp_profile_picture
                        st.session_state.uploader_key += 1
                        st.rerun()

                # Remove picture button
                if current_picture and not hasattr(st.session_state, 'temp_profile_picture'):
                    if st.button("🗑️ Remove Picture", use_container_width=True):
                        with st.spinner("🔄 Removing profile picture..."):
                            update_data = {
                                'email': user_data.get('email', ''),
                                'full_name': user_data.get('full_name', ''),
                                'profile_picture': None
                            }
                            success, result = api.update_profile(update_data)
                            if success:
                                st.success("✅ Profile picture removed successfully!")
                                st.session_state.profile_picture = None
                                if 'profile_picture' in user_data:
                                    user_data['profile_picture'] = None
                                st.rerun()
                            else:
                                st.error(f"Failed to remove: {result.get('detail', 'Unknown error')}")

                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                # Profile Information Form - EXACT WORKING CODE
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown("**📋 Profile Information**")

                with st.form("profile_form", clear_on_submit=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        username = st.text_input(
                            "**Username**",
                            value=user_data.get('username', ''),
                            disabled=True
                        )
                    with col_b:
                        role = st.text_input(
                            "**Role**",
                            value=user_data.get('role', 'candidate').title(),
                            disabled=True
                        )

                    email = st.text_input(
                        "**Email Address** *",
                        value=user_data.get('email', ''),
                        placeholder="your.email@example.com"
                    )

                    full_name = st.text_input(
                        "**Full Name**",
                        value=user_data.get('full_name', ''),
                        placeholder="Enter your full name"
                    )

                    submit_button = st.form_submit_button("💾 Update Profile", use_container_width=True)

                    if submit_button:
                        # Validate required fields
                        if not email.strip():
                            st.error("Email address is required")
                        else:
                            update_data = {
                                'email': email,
                                'full_name': full_name or ""
                            }

                            # Check if changes were made
                            changes_made = (
                                    email != user_data.get('email') or
                                    full_name != user_data.get('full_name', '')
                            )

                            if changes_made:
                                with st.spinner("🔄 Updating profile..."):
                                    success, result = api.update_profile(update_data)
                                    if success:
                                        st.success("✅ Profile updated successfully!")
                                        user_data['email'] = email
                                        user_data['full_name'] = full_name
                                        st.rerun()
                                    else:
                                        error_message = result.get('detail', 'Unknown error occurred')
                                        error_code = result.get('error_code', '')

                                        # ✅ Handle duplicate email error specifically
                                        if error_code == "EMAIL_EXISTS" or "email already registered" in error_message.lower():
                                            st.error("""
                                            ❌ **Email Already Registered**

                                            The email address **`{}`** is already associated with another account. 

                                            Please use a different email address.
                                            """.format(email.strip()))
                                        else:
                                            st.error(f"❌ Failed to update profile: {error_message}")

                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Account Status Section
    with st.container():
        st.markdown("### 📊 Account Overview")

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown("**🔐 Account Status**")
                st.write(f"**👤 Username:** {user_data.get('username', 'N/A')}")
                st.write(f"**🎯 Role:** {user_data.get('role', 'candidate').title()}")
                st.write(
                    f"**📧 Email Verified:** {'✅ Verified' if user_data.get('is_verified', False) else '❌ Not Verified'}")
                st.write(f"**🟢 Account Active:** {'✅ Active' if user_data.get('is_active', True) else '❌ Inactive'}")
                st.write(f"**📅 Member Since:** {user_data.get('created_at', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown("**💡 Profile Tips**")
                st.write("**🎯 Professional Image:**")
                st.write("• Use a clear, professional headshot")
                st.write("• Square images work best")
                st.write("• Well-lit, high-quality photos")
                st.markdown('</div>', unsafe_allow_html=True)

    # Email Verification Section
    if not user_data.get('is_verified', False):
        st.markdown("---")
        with st.container():
            st.markdown("### 📧 Email Verification")
            verification.verification_ui(api)

    # Simple Footer
    st.markdown("---")
    with st.container():
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
            <h4 style='color: #1f3a60; margin-bottom: 1rem;'>Engineering Report Deck Profile</h4>
            <p style='color: #666; margin: 0;'>
                Your Professional Identity • Built for Engineering Excellence
            </p>
        </div>
        """, unsafe_allow_html=True)


def profile_page(api: EnhancedAPIClient):
    """Main profile page function"""
    user_profile(api)