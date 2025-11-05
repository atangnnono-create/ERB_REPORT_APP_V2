import streamlit as st
import time
from services.enhanced_api_client import EnhancedAPIClient


def contact_page(api: EnhancedAPIClient):
    """Enhanced contact form with pre-filled user data and email delivery"""

    # Check authentication status
    is_logged_in = st.session_state.get('logged_in', False)
    user_name = st.session_state.get('full_name', '')
    user_email = st.session_state.get('user_email', '')
    user_role = st.session_state.get('user_role', '')

    st.set_page_config(
        page_title="Contact Us - Engineering Report Deck",
        page_icon="📞",
        layout="wide"
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
    .user-info-card {
        background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
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
            <p style='margin-bottom: 0.5rem;'>• 24 Hour Response Time</p>
            <p style='margin-bottom: 0.5rem;'>• Technical Experts Available</p>
            <p style='margin-bottom: 0;'>• Direct Email Delivery</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # User Context Display
    if is_logged_in:
        st.markdown(f"""
        <div class="user-info-card">
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.5rem; margin-right: 0.5rem;'>👤</span>
                <div>
                    <strong style='color: #2c3e50; font-size: 1.2rem;'>Welcome, {user_name}!</strong>
                    <div style='color: #3498db; font-size: 0.9rem;'>Role: {user_role}</div>
                </div>
            </div>
            <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                Your account email will be used for the response. This field is pre-filled and read-only.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card">
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-size: 1.2rem; margin-right: 0.5rem;'>🔐</span>
                <strong style='color: #1f3a60;'>Guest Mode</strong>
            </div>
            <p style='margin: 0; color: #666;'>
                Please provide your contact information. 
                <a href="/?page=Login" style='color: #3498db; text-decoration: none;'>Sign in</a> to pre-fill your details automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Contact Form Section
    st.markdown('<div class="sub-header">Send Us a Message</div>', unsafe_allow_html=True)

    # Contact Form
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        with st.form("contact_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "**Full Name** *",
                    value=user_name if is_logged_in else "",
                    placeholder="Enter your full name",
                    help="Please provide your complete name for proper addressing"
                )

            with col2:
                email = st.text_input(
                    "**Email Address** *",
                    value=user_email if is_logged_in else "",
                    placeholder="your.email@company.com",
                    disabled=is_logged_in,  # Make read-only for logged-in users
                    help="We'll use this to respond to your inquiry"
                )

                if is_logged_in:
                    st.caption("🔒 Using your verified account email")

            subject = st.text_input(
                "**Subject** *",
                placeholder="Brief description of your inquiry",
                help="What is this message about?"
            )

            message = st.text_area(
                "**Your Message** *",
                placeholder="""Please describe your inquiry in detail. Include any relevant information about your engineering reports, technical issues, or feature requests...""",
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
                if not all([name, email, subject, message]):
                    st.error("**Please fill in all required fields** (*)")
                    st.info("All fields are required to ensure we can properly assist you.")
                elif not is_logged_in and ("@" not in email or "." not in email):
                    st.error("**Please enter a valid email address**")
                    st.info("We need a valid email to respond to your inquiry.")
                elif len(message.strip()) < 10:
                    st.error("**Please provide a more detailed message**")
                    st.info("Your message should be at least 10 characters long.")
                else:
                    # Processing
                    with st.spinner("**📤 Sending your message...**"):
                        # Submit to backend API
                        success, result = api.submit_contact_form({
                            "name": name.strip(),
                            "email": email.strip(),
                            "subject": subject.strip(),
                            "message": message.strip()
                        })

                    if success:
                        st.success(f"""
                        **✅ Thank you, {name}!**

                        Your message has been delivered directly to our support team. 
                        We'll review your inquiry and get back to you within 24 hours.
                        """)
                        st.balloons()

                        # Show confirmation details
                        with st.expander("📋 Message Summary", expanded=True):
                            st.write(f"**From:** {name}")
                            st.write(f"**Email:** {email}")
                            st.write(f"**Subject:** {subject}")
                            st.write(f"**Sent:** {time.strftime('%Y-%m-%d %H:%M:%S')}")

                            if is_logged_in:
                                st.write(f"**User Role:** {user_role}")
                                st.write("**Status:** ✅ Sent from verified account")
                    else:
                        error_msg = result.get('detail', 'Unknown error occurred')
                        st.error(f"""
                        **❌ Failed to send message**

                        Error: {error_msg}

                        Please try again in a few moments, or contact us directly at 
                        **customengineeringreports@gmail.com**
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

    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0;'>
            <strong>Engineering Report Deck</strong> • Confidence with Clarity
        </p>
        <p style='color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
            TurtleTEC Solutions Africa
            © 2025. ALL RIGHTS RESERVED.
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    from services.enhanced_api_client import api_client

    contact_page(api_client)