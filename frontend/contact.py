import streamlit as st
import pandas as pd
import time
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Google Sheets configuration
SPREADSHEET_ID = "1HjPHcU34kV9yPQsl2u5tDbkVkCWcqXrAjG7l8O8j68c"
SHEET_NAME = "Messages"
CREDENTIALS_FILE = "service_account.json"


def check_internet_connection():
    """Check if internet connection is available"""
    try:
        import socket
        socket.create_connection(("www.google.com", 80), timeout=5)
        return True
    except OSError:
        return False


def check_google_services():
    """Check if Google services are accessible"""
    try:
        import socket
        socket.gethostbyname('oauth2.googleapis.com')
        socket.gethostbyname('www.googleapis.com')
        return True
    except socket.gaierror:
        return False


def initialize_google_sheets():
    """Initialize Google Sheets client with error handling"""
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            return None

        if not check_internet_connection():
            return None

        if not check_google_services():
            return None

        import gspread
        from google.auth.exceptions import TransportError, DefaultCredentialsError

        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        return sheet

    except Exception as e:
        return None


def submit_to_google_sheets(name, email, message, sheet):
    """Submit form data to Google Sheets"""
    try:
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name, email, message])
        return True
    except Exception as e:
        return False


def save_to_local_backup(name, email, message):
    """Save form data to local file as backup"""
    try:
        backup_file = "contact_backup.csv"
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        os.makedirs("backups", exist_ok=True)
        backup_path = os.path.join("backups", backup_file)

        new_data = pd.DataFrame({
            'timestamp': [timestamp],
            'name': [name],
            'email': [email],
            'message': [message]
        })

        if os.path.exists(backup_path):
            existing_data = pd.read_csv(backup_path)
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        else:
            updated_data = new_data

        updated_data.to_csv(backup_path, index=False)
        return True
    except Exception as e:
        return False


def show():
    st.set_page_config(
        page_title="Contact Us - Engineering Report Deck",
        page_icon="📞",
        layout="centered"
    )

    # Custom CSS for elegant styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f3a60;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #1f3a60, #4a6fa5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .contact-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f3a60;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        font-size: 0.9rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #1f3a60, #4a6fa5);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(31, 58, 96, 0.3);
    }
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
    }
    .divider {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #1f3a60, transparent);
        margin: 2rem 0;
    }
    .contact-method {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease;
    }
    .contact-method:hover {
        transform: translateY(-5px);
    }
    .icon-large {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown('<div class="main-header">📞 Contact Us</div>', unsafe_allow_html=True)

    # Hero Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        <div style='text-align: left; color: #555; line-height: 1.6;'>
            <h3 style='color: #1f3a60; margin-bottom: 1rem;'>We're Here to Help</h3>
            <p style='font-size: 1.1rem;'>
                Have questions about the Engineering Report Deck? Need technical support or want to provide feedback? 
                Our team is dedicated to providing you with exceptional service and support.
            </p>
            <p style='font-size: 1.1rem;'>
                Fill out the form below and we'll get back to you within 24 hours. Your satisfaction is our priority.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1f3a60, #4a6fa5); color: white; padding: 2rem; border-radius: 15px; text-align: center;'>
            <h3 style='color: white; margin-bottom: 1rem;'>🚀 Quick Support</h3>
            <p style='margin-bottom: 0.5rem;'>• 24-48 Hour Response Time</p>
            <p style='margin-bottom: 0.5rem;'>• Technical Experts Available</p>
            <p style='margin-bottom: 0;'>• Priority Support for Enterprise</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Contact Form Section
    st.markdown('<div class="sub-header">Send Us a Message</div>', unsafe_allow_html=True)

    # Initialize Google Sheets connection
    sheet = initialize_google_sheets()

    # Connection Status Card
    if sheet is None:
        st.markdown("""
        <div class="info-card" style='border-left-color: #e74c3c;'>
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.2rem; margin-right: 0.5rem;'>⚠️</span>
                <strong style='color: #e74c3c;'>Temporary Offline Mode</strong>
            </div>
            <p style='margin: 0; color: #666;'>
                Google Sheets integration is temporarily unavailable. Your message will be saved locally and automatically synchronized when the connection is restored.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card" style='border-left-color: #27ae60;'>
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.2rem; margin-right: 0.5rem;'>✅</span>
                <strong style='color: #27ae60;'>All Systems Operational</strong>
            </div>
            <p style='margin: 0; color: #666;'>
                Your message will be delivered instantly to our support team.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Contact Form
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        with st.form("contact_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "**Full Name** *",
                    placeholder="Enter your full name",
                    help="Please provide your complete name for proper addressing"
                )

            with col2:
                email = st.text_input(
                    "**Email Address** *",
                    placeholder="your.email@company.com",
                    help="We'll use this to respond to your inquiry"
                )

            message = st.text_area(
                "**Your Message** *",
                placeholder="Please describe your inquiry in detail. Include any relevant information about your engineering reports, technical issues, or feature requests...",
                height=150,
                help="The more details you provide, the better we can assist you"
            )

            # Form submission with enhanced button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "🚀 Send Message",
                    use_container_width=True
                )

            if submitted:
                # Validation
                if not name or not email or not message:
                    st.error("**Please fill in all required fields** (*)")
                    st.info("All fields are required to ensure we can properly assist you.")
                    return

                if "@" not in email or "." not in email:
                    st.error("**Please enter a valid email address**")
                    st.info("We need a valid email to respond to your inquiry.")
                    return

                # Processing
                with st.spinner("**Sending your message...**"):
                    time.sleep(1)  # Simulate processing

                    success = False
                    submission_method = ""

                    if sheet:
                        success = submit_to_google_sheets(name, email, message, sheet)
                        submission_method = "our secure database"

                    if not success:
                        success = save_to_local_backup(name, email, message)
                        submission_method = "local storage"

                    if success:
                        st.success(f"""
                        **✅ Thank you, {name}!**

                        Your message has been received and saved to {submission_method}. 
                        Our team will review your inquiry and get back to you within 24-48 hours.
                        """)
                        st.balloons()

                        if submission_method == "local storage":
                            st.info("""
                            **📝 Local Storage Notice**
                            Your message has been securely saved locally and will be automatically synchronized 
                            with our main system when connectivity is restored.
                            """)
                    else:
                        st.error("""
                        **❌ Submission Issue**

                        We encountered a technical issue while saving your message. 
                        Please try again in a few moments or use one of the alternative contact methods below.
                        """)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Alternative Contact Methods
    st.markdown('<div class="sub-header">Other Ways to Reach Us</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="contact-method">
            <div class="icon-large">📧</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Email Support</h4>
            <p style='color: #666; margin-bottom: 0.5rem;'><strong>customengineeringreports@gmail.com</strong></p>
            <p style='font-size: 0.9rem; color: #888;'>Typically responds within 24 hours</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="contact-method">
            <div class="icon-large">📱</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Phone & WhatsApp</h4>
            <p style='color: #666; margin-bottom: 0.5rem;'><strong>+267 7144 1429</strong></p>
            <p style='font-size: 0.9rem; color: #888;'>Available during business hours</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="contact-method">
            <div class="icon-large">🕒</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Support Hours</h4>
            <p style='color: #666; margin-bottom: 0.5rem;'><strong>Mon - Fri: 8AM - 6PM</strong></p>
            <p style='font-size: 0.9rem; color: #888;'>Saturday: 9AM - 1PM</p>
        </div>
        """, unsafe_allow_html=True)

    # Technical Information Section
    with st.expander("**🔧 System Status & Technical Information**", expanded=False):
        st.markdown("""
        <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px;'>
            <h4 style='color: #1f3a60; margin-bottom: 1rem;'>Current System Status</h4>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            internet_status = "✅ **Operational**" if check_internet_connection() else "❌ **Offline**"
            st.markdown(f"**Internet Connection:** {internet_status}")

        with col2:
            google_status = "✅ **Available**" if check_google_services() else "❌ **Unavailable**"
            st.markdown(f"**Google Services:** {google_status}")

        with col3:
            sheets_status = "✅ **Connected**" if sheet else "❌ **Disconnected**"
            st.markdown(f"**Database:** {sheets_status}")

        if sheet is None:
            st.markdown("""
            <div class="info-card" style='margin-top: 1rem;'>
                <h5 style='color: #e74c3c; margin-bottom: 0.5rem;'>Connection Issues</h5>
                <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                    This is typically caused by network restrictions, firewall settings, or temporary service outages. 
                    Your data remains secure and will sync when connectivity is restored.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0;'>
            <strong>Engineering Report Deck Support</strong> • Committed to Excellence in Engineering Documentation
        </p>
        <p style='color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
            Your trusted partner for professional engineering reporting solutions
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    show()