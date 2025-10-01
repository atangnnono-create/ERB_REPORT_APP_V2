import streamlit as st
import pandas as pd
import time
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Google Sheets configuration
SPREADSHEET_ID = "1HjPHcU34kV9yPQsl2u5tDbkVkCWcqXrAjG7l8O8j68c"  # Replace with your actual Google Sheet ID
SHEET_NAME = "Messages"
CREDENTIALS_FILE = "service_account.json"  # Path to your Google Service Account credentials


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
        # Test DNS resolution for Google APIs
        socket.gethostbyname('oauth2.googleapis.com')
        socket.gethostbyname('www.googleapis.com')
        return True
    except socket.gaierror:
        return False


def initialize_google_sheets():
    """Initialize Google Sheets client with error handling"""
    try:
        # Check prerequisites first
        if not os.path.exists(CREDENTIALS_FILE):
            st.warning("🔐 Google Sheets credentials not found")
            st.info(f"Please ensure '{CREDENTIALS_FILE}' exists in your project directory")
            return None

        if not check_internet_connection():
            st.error("🌐 No internet connection detected")
            return None

        if not check_google_services():
            st.error("🔧 Google services are currently unavailable")
            st.info("This may be due to network restrictions or DNS issues")
            return None

        # Import gspread only when needed
        import gspread
        from google.auth.exceptions import TransportError, DefaultCredentialsError

        # Initialize client
        gc = gspread.service_account(filename=CREDENTIALS_FILE)

        # Test connection
        sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        st.success("✅ Connected to Google Sheets")
        return sheet

    except TransportError as e:
        st.error("🚫 Network error connecting to Google Services")
        st.info("""
        **Common causes:**
        - No internet connection
        - Firewall blocking Google APIs
        - DNS resolution issues
        - Corporate network restrictions
        """)
        return None

    except gspread.exceptions.APIError as e:
        st.error("❌ Google Sheets API error")
        st.info(f"Error details: {str(e)}")
        return None

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("📄 Spreadsheet not found")
        st.info(f"Please check if the spreadsheet ID '{SPREADSHEET_ID}' is correct and accessible")
        return None

    except gspread.exceptions.WorksheetNotFound:
        st.error("📊 Worksheet not found")
        st.info(f"Please ensure worksheet '{SHEET_NAME}' exists in the spreadsheet")
        return None

    except DefaultCredentialsError:
        st.error("🔑 Google authentication failed")
        st.info("Please check your service account credentials file")
        return None

    except Exception as e:
        st.error(f"💥 Unexpected error: {str(e)}")
        st.info("Please try again later or contact support")
        return None


def submit_to_google_sheets(name, email, message, sheet):
    """Submit form data to Google Sheets"""
    try:
        # Get current timestamp
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append the new row
        sheet.append_row([timestamp, name, email, message])
        return True

    except Exception as e:
        st.error(f"Failed to save to Google Sheets: {str(e)}")
        return False


def save_to_local_backup(name, email, message):
    """Save form data to local file as backup"""
    try:
        backup_file = "contact_backup.csv"
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create backup directory if it doesn't exist
        os.makedirs("backups", exist_ok=True)
        backup_path = os.path.join("backups", backup_file)

        # Append to backup file
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
        st.error(f"Backup failed: {str(e)}")
        return False


def show():
    st.set_page_config(page_title="Contact - Engineering Report Deck")

    st.title("📞 Contact Us")
    st.write(
        "Have questions, feedback, or need support? We'd love to hear from you! "
        "Fill out the form below and we'll get back to you as soon as possible."
    )

    # Initialize Google Sheets connection
    sheet = initialize_google_sheets()

    # Show connection status
    if sheet is None:
        st.warning("⚠️ Google Sheets integration is currently unavailable")
        st.info("""
        **You can still submit your message - it will be saved locally and synchronized when Google Services become available.**

        Common solutions:
        - Check your internet connection
        - Verify network can access Google services
        - Ensure credentials.json file exists
        - Try again in a few minutes
        """)

    # Contact form
    with st.form("contact_form", clear_on_submit=True):
        st.subheader("Send us a Message")

        name = st.text_input("Your Name *", placeholder="Enter your full name")
        email = st.text_input("Your Email *", placeholder="Enter your email address")
        message = st.text_area("Your Message *",
                               placeholder="Tell us how we can help you...",
                               height=150)

        submitted = st.form_submit_button("Send Message")

        if submitted:
            # Basic validation
            if not name or not email or not message:
                st.error("❌ Please fill in all required fields (*)")
                return

            if "@" not in email or "." not in email:
                st.error("❌ Please enter a valid email address")
                return

            # Show loading spinner
            with st.spinner("Sending your message..."):
                time.sleep(1)  # Simulate processing

                success = False
                submission_method = ""

                # Try Google Sheets first
                if sheet:
                    success = submit_to_google_sheets(name, email, message, sheet)
                    submission_method = "Google Sheets"

                # If Google Sheets fails or unavailable, use local backup
                if not success:
                    success = save_to_local_backup(name, email, message)
                    submission_method = "local backup"

                if success:
                    st.success(f"✅ Thank you {name}! Your message has been received and saved to {submission_method}.")
                    st.balloons()

                    if submission_method == "local backup":
                        st.info("""
                        **Your message has been saved locally.**
                        It will be synchronized with our main system when Google Services become available.
                        """)
                else:
                    st.error("❌ Sorry, we couldn't save your message. Please try again or contact us directly.")

    # Alternative contact methods
    st.markdown("---")
    st.subheader("Other Ways to Reach Us")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📧 Direct Email**")
        st.write("lefa.molokwe@example.com")  # Replace with actual email
        st.write("_Typically respond within 24 hours_")

    with col2:
        st.write("**📱 Phone/WhatsApp**")
        st.write("+267 7144 1429")
        st.write("_Available during business hours_")

    # Technical information (collapsible)
    with st.expander("🔧 Technical Information"):
        st.write("**Connection Status:**")

        internet_status = "✅ Connected" if check_internet_connection() else "❌ No internet"
        google_status = "✅ Available" if check_google_services() else "❌ Unavailable"
        sheets_status = "✅ Connected" if sheet else "❌ Disconnected"

        st.write(f"- Internet: {internet_status}")
        st.write(f"- Google Services: {google_status}")
        st.write(f"- Google Sheets: {sheets_status}")

        if sheet is None:
            st.info("""
            **Why Google Sheets might be unavailable:**
            - No internet connection
            - Network firewall blocking Google APIs
            - DNS resolution issues
            - Invalid or missing credentials
            - Spreadsheet access permissions
            - Google service outage
            """)


if __name__ == "__main__":
    show()