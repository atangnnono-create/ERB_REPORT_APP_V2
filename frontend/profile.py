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
    # Try to load from assets folder first
    assets_path = "assets"
    default_avatar_path = os.path.join(assets_path, "default_avatar.png")

    if os.path.exists(default_avatar_path):
        try:
            # Read and convert to base64 for consistent display
            with open(default_avatar_path, "rb") as f:
                img_data = f.read()
                img_str = base64.b64encode(img_data).decode()
                return f"data:image/png;base64,{img_str}"
        except Exception as e:
            ErrorHandler.show_warning(f"Could not load default avatar: {e}")

    # Fallback to SVG avatar
    username = st.session_state.get('username', 'U')
    initials = username[0].upper() if username else 'U'

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    color_index = hash(username) % len(colors) if username else 0
    bg_color = colors[color_index]

    svg = f'''
    <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="100" fill="{bg_color}"/>
        <text x="100" y="110" font-family="Arial, sans-serif" font-size="80" font-weight="bold" 
              fill="white" text-anchor="middle" alignment-baseline="middle">{initials}</text>
    </svg>
    '''
    return svg


def display_profile_picture(image_data, width=200):
    """Display profile picture with fallback to default avatar"""
    try:
        if image_data:
            # If it's base64 encoded image
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                st.markdown(
                    f'<div style="display: flex; justify-content: center;">'
                    f'<img src="{image_data}" width="{width}" style="border-radius:50%; border: 3px solid #f0f2f6;">'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                # Assume it's PIL Image or file-like object
                st.image(image_data, width=width, use_column_width=False)
        else:
            # Show default avatar
            st.markdown(
                f'<div style="display: flex; justify-content: center;">'
                f'{get_default_avatar()}'
                f'</div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        ErrorHandler.show_error(f"Error displaying profile picture: {e}")
        # Fallback to default avatar
        st.markdown(
            f'<div style="display: flex; justify-content: center;">'
            f'{get_default_avatar()}'
            f'</div>',
            unsafe_allow_html=True
        )


@with_loading("Processing image...")
def handle_image_upload(uploaded_file):
    """Process uploaded image and convert to base64"""
    try:
        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        if uploaded_file.size > max_size:
            ErrorHandler.show_error("File too large. Please choose an image under 5MB.")
            return None

        # Open image with PIL
        image = Image.open(uploaded_file)

        # Validate image format
        if image.format not in ['JPEG', 'PNG', 'GIF']:
            ErrorHandler.show_error("Unsupported image format. Please use JPG, PNG, or GIF.")
            return None

        # Resize image to reasonable size (400x400 max for better quality)
        image.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P', 'LA'):
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                # Paste the image onto the background using the alpha channel as mask
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            image = background

        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        ErrorHandler.show_success("Image processed successfully!")
        return f"data:image/jpeg;base64,{img_str}"

    except Exception as e:
        ErrorHandler.show_error(f"Error processing image: {str(e)}")
        return None


def user_profile(api: EnhancedAPIClient):
    st.title("👤 Your Profile")

    # Initialize profile picture in session state if not exists
    if 'profile_picture' not in st.session_state:
        st.session_state.profile_picture = None

    # Track if we need to refresh
    if 'refresh_profile' not in st.session_state:
        st.session_state.refresh_profile = False

    # Fetch current user data
    success, user_data = api.get_current_user()

    if not success:
        ErrorHandler.show_error("Failed to load profile data")
        return

    # Use a 40/60 split to give more space to the profile picture
    col1, col2 = st.columns([40, 60])

    with col1:
        st.subheader("Profile Picture")

        # Display current profile picture with larger size
        current_picture = st.session_state.profile_picture or user_data.get('profile_picture')
        display_profile_picture(current_picture, width=200)

        # Compact file upload
        uploaded_file = st.file_uploader(
            "📁 Choose profile picture",
            type=['jpg', 'jpeg', 'png'],
            help="JPG, PNG up to 5MB",
            label_visibility="collapsed",
            key="profile_pic_uploader"
        )

        if uploaded_file is not None:
            # Process the uploaded image
            processed_image = handle_image_upload(uploaded_file)
            if processed_image:
                st.session_state.profile_picture = processed_image
                st.success("✅ Profile picture updated! Click 'Update Profile' to save.")
                # Don't auto-refresh - let user click update button

        # Compact remove button
        if st.session_state.profile_picture or user_data.get('profile_picture'):
            if st.button("🗑️ Remove Picture", use_container_width=True, help="Remove profile picture"):
                st.session_state.profile_picture = None
                # Also clear from user_data if it exists there
                if 'profile_picture' in user_data:
                    user_data['profile_picture'] = None
                st.success("Profile picture removed! Click 'Update Profile' to save.")

    with col2:
        st.subheader("Profile Information")

        with st.form("profile_form", clear_on_submit=False):
            username = st.text_input("Username", value=user_data.get('username', ''), disabled=True)
            email = st.text_input("Email Address", value=user_data.get('email', ''))
            full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))
            role = st.text_input("Role", value=user_data.get('role', 'candidate').title(), disabled=True)

            # Add profile picture to update data if changed
            profile_picture_changed = (st.session_state.profile_picture != user_data.get('profile_picture'))

            # Update button with better styling
            submit_button = st.form_submit_button("💾 Update Profile", use_container_width=True)

            if submit_button:
                update_data = {}
                changes_made = False

                if email != user_data.get('email'):
                    update_data['email'] = email
                    changes_made = True

                if full_name != user_data.get('full_name'):
                    update_data['full_name'] = full_name
                    changes_made = True

                if profile_picture_changed:
                    if st.session_state.profile_picture:
                        update_data['profile_picture'] = st.session_state.profile_picture
                    else:
                        update_data['profile_picture'] = None
                    changes_made = True

                if changes_made:
                    with st.spinner("Updating profile..."):
                        success, result = api.update_profile(update_data)
                        if success:
                            st.success("Profile updated successfully!")
                            # Clear the temporary profile picture state
                            if 'profile_picture' in st.session_state:
                                del st.session_state.profile_picture
                            # Set flag to refresh
                            st.session_state.refresh_profile = True
                        else:
                            ErrorHandler.show_error(
                                f"Failed to update profile: {result.get('detail', 'Unknown error')}")
                else:
                    st.info("No changes made to save")

    # Account Status Section
    st.markdown("---")

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        st.subheader("Account Status")
        st.write(f"**Username:** {user_data.get('username', 'N/A')}")
        st.write(f"**Role:** {user_data.get('role', 'candidate').title()}")

        # Enhanced verification status
        is_verified = user_data.get('is_verified', False)
        verification_status = "✅ Verified" if is_verified else "❌ Not Verified"
        st.write(f"**Email Verified:** {verification_status}")

        st.write(f"**Account Active:** {'✅ Yes' if user_data.get('is_active', True) else '❌ No'}")
        st.write(f"**Member Since:** {user_data.get('created_at', 'N/A')}")

    with status_col2:
        st.subheader("Quick Tips")
        st.info("""
        **Profile Picture:**
        • Square images work best
        • JPG or PNG format
        • Clear, professional photo

        **Need help?** Contact support if you have issues uploading.
        """)

    # Show verification section if not verified
    if not is_verified:
        st.markdown("---")
        st.subheader("Email Verification")
        verification.verification_ui(api)

    # Handle refresh if needed
    if st.session_state.get('refresh_profile', False):
        st.session_state.refresh_profile = False
        st.rerun()


def profile_page(api: EnhancedAPIClient):
    """Main profile page function"""
    user_profile(api)


# Helper function to get profile picture for display in other parts of the app
def get_profile_picture(api: EnhancedAPIClient, size=40):
    """Get user's profile picture for display in sidebar or other components"""
    # Check session state first
    if 'profile_picture' in st.session_state and st.session_state.profile_picture:
        return f'<img src="{st.session_state.profile_picture}" width="{size}" style="border-radius:50%; border: 1px solid #ddd;">'

    # Try to get from user data via API
    try:
        success, user_data = api.get_current_user()
        if success and user_data.get('profile_picture'):
            return f'<img src="{user_data.get("profile_picture")}" width="{size}" style="border-radius:50%; border: 1px solid #ddd;">'
    except:
        pass

    # Return default avatar
    return get_default_avatar_for_sidebar(size)


def get_default_avatar_for_sidebar(size=40):
    """Get smaller default avatar for sidebar"""
    # Try assets folder first
    assets_path = "assets"
    default_avatar_path = os.path.join(assets_path, "default_avatar.png")

    if os.path.exists(default_avatar_path):
        try:
            with open(default_avatar_path, "rb") as f:
                img_data = f.read()
                img_str = base64.b64encode(img_data).decode()
                return f'<img src="data:image/png;base64,{img_str}" width="{size}" style="border-radius:50%;">'
        except:
            pass

    # Fallback to SVG
    username = st.session_state.get('username', 'U')
    initials = username[0].upper() if username else 'U'
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    color_index = hash(username) % len(colors) if username else 0
    bg_color = colors[color_index]

    svg = f'''
    <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="50" fill="{bg_color}"/>
        <text x="50" y="58" font-family="Arial, sans-serif" font-size="40" font-weight="bold" 
              fill="white" text-anchor="middle" alignment-baseline="middle">{initials}</text>
    </svg>
    '''
    return svg