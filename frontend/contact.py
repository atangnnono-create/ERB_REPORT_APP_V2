import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime



def show():
    st.set_page_config(page_title="Contact - Engineering Report Deck")

    st.title("📬 Contact")

    st.write("We’d love to hear from you! Whether you have feedback, feature requests, or questions, feel free to reach out:")

    # Replace with your real details
    EMAIL = "fluidair2010@gmail.com"
    LINKEDIN = "https://www.linkedin.com/in/your-profile/"
    GITHUB = "https://github.com/your-username"  # optional

    st.markdown(f"📧 **Email:** [{EMAIL}](mailto:{EMAIL})")
    st.markdown(f"💼 **LinkedIn:** [View Profile]({LINKEDIN})")
    st.markdown(f"🌐 **GitHub:** [Projects]({GITHUB})")

    st.markdown("---")
    st.subheader("📩 Send a Message")

    # ------------------- GOOGLE SHEETS SETUP -------------------
    # 1. Create a Google Cloud Project
    # 2. Enable Google Sheets API
    # 3. Create a Service Account & download credentials.json
    # 4. Share your Google Sheet with the service account email
    # 5. Store credentials.json securely (e.g., in Streamlit secrets)

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SPREADSHEET_ID = "1HjPHcU34kV9yPQsl2u5tDbkVkCWcqXrAjG7l8O8j68c"  # Google Sheet ID
    SHEET_NAME = "Messages"  # Google Sheet Tab Name

    # Load credentials from Streamlit secrets
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    # ------------------- FORM -------------------
    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        message = st.text_area("Your Message")

        submitted = st.form_submit_button("Send 📤")

        if submitted:
            if not name or not email or not message:
                st.warning("⚠️ Please fill in all fields before submitting.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([timestamp, name, email, message])
                st.success("✅ Your message has been sent successfully!")


