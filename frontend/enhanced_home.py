import streamlit as st
from datetime import datetime
from typing import List, Dict
import enhanced_admin_dashboard
from services.enhanced_api_client import EnhancedAPIClient
import about, contact, create_report, auth, enhanced_reports, user_profile
from enhanced_admin_dashboard import enhanced_admin_dashboard
from frontend import verification
from utilities.error_handling import ErrorHandler, LoadingState, display_network_status
from regular_user_dashboard import show_dashboard
import functools
from report_review_separate import review_dashboard
from resources_marketplace import resources_marketplace



# Initialize enhanced API client
if "api" not in st.session_state:
    st.session_state.api = EnhancedAPIClient()

api = st.session_state.api



def get_user_permissions(role: str) -> set:
    """Enhanced permission system"""
    permissions = {
        "admin": {"create_reports", "view_own_reports","export_reports",  "ai_feedback", "ai_features", "view_all_reports","review_reports",
                  "manage_users", "system_settings", "audit_access", "export_data", },
        "reviewer": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features", "view_all_reports", "review_reports",},
        "engineer": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "technologist": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "technician": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "candidate": {"create_reports", "view_own_reports", "export_reports", "ai_feedback","ai_features"}
    }
    return permissions.get(role, set())


def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "logged_in": False,
        "token": None,
        "username": "",
        "user_role": "candidate",
        "user_id": None,
        "user_email": "",
        "full_name": "",
        "is_verified": False,
        "is_active": True,
        "debug_mode": False,
        "last_activity": None,
        "ai_context": {},
        "current_review_id": None,  # Add this
        "review_data_loaded": False  # Add loading state tracking
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_user_profile_sidebar():
    """Enhanced user profile in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 User Profile")

    # User info with status

    st.sidebar.success(f"👋 Logged in as **{st.session_state.username}**")
    st.sidebar.info(f"🎯 Role: {st.session_state.user_role.title()}")

    # Verification status
    if st.session_state.is_verified:
        st.sidebar.success("✅ Email Verified")
    else:
        st.sidebar.warning("📧 Verify Email")

    # Quick stats
    with LoadingState("Loading stats...", use_container=False):
        success, user_data = api.fetch_reports()
        if success:
            st.sidebar.metric("Reports", len(user_data))




def get_competency_sections_for_ai():
    """Get competency sections based on user role for AI features"""
    from utilities.comps import engineer_competencies, technician_competencies, technologist_competencies

    selected_role = st.session_state.get("selected_role")

    if selected_role == "Engineering Technologist":
        return technologist_competencies
    elif selected_role == "Engineering Technician":
        return technician_competencies
    else:
        return engineer_competencies  # Default to Engineer


def get_current_responses_for_ai():
    """Get current responses for AI analysis with proper structure handling"""
    try:
        selected_role = st.session_state.get("selected_role", "Engineer")
        responses_data = st.session_state.get("responses", {})

        current_responses = {}

        # Extract responses for the selected role in the expected format
        if isinstance(responses_data, dict) and selected_role in responses_data:
            role_responses = responses_data[selected_role]

            if isinstance(role_responses, dict):
                # Convert from create_report.py format to AI service expected format
                for competency_key, response_data in role_responses.items():
                    # Skip the _status key and ensure we have proper response data
                    if competency_key != '_status' and isinstance(response_data, dict):
                        current_responses[competency_key] = {
                            'response': response_data.get('response', ''),
                            'title': response_data.get('title', 'Unknown Title')
                        }

        return current_responses

    except Exception as e:
        print(f"Error getting responses for AI: {e}")
        return {}

def ai_assistant_page():
    """AI Assistant main page"""
    st.title("🤖 AI Assistant")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea, #764ba2); padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h3 style="margin:0; color: white;">AI-Powered Report Enhancement</h3>
        <p style="margin:0.5rem 0 0 0; color: white; opacity: 0.9;">
            Smart templates, gap analysis, and quality improvement for your ERB reports
        </p>
    </div>
    """, unsafe_allow_html=True)

    selected_role = st.session_state.get("selected_role", "Engineer")
    user_role = st.session_state.get("user_role", "engineer")

    st.info(f"**Professional Role:** {selected_role} | **System Role:** {user_role.title()}")

    # FIX: Get current responses with proper structure handling
    current_responses = {}
    try:
        responses_data = st.session_state.get("responses", {})


        # Extract responses for the selected role in the expected format
        if isinstance(responses_data, dict) and selected_role in responses_data:
            role_responses = responses_data[selected_role]

            if isinstance(role_responses, dict):
                # Convert from create_report.py format to AI service expected format
                for competency_key, response_data in role_responses.items():
                    # Skip the _status key and ensure we have proper response data
                    if competency_key != '_status' and isinstance(response_data, dict):
                        current_responses[competency_key] = {
                            'response': response_data.get('response', ''),
                            'title': response_data.get('title', 'Unknown Title')
                        }


    except Exception as e:
        st.error(f"Error loading response data: {str(e)}")
        current_responses = {}

    competency_sections = get_competency_sections_for_ai()

    if not current_responses:
        st.warning("""
        **Start creating a report to unlock full AI features!**

        To get the most out of the AI Assistant:
        1. Go to **Create Report** and start working on your competencies
        2. Return here for AI-powered enhancements
        3. Use smart templates and gap analysis
        """)

        # Quick start buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Start New Report", use_container_width=True):
                st.session_state.current_page = "Create Report"
                st.rerun()
        with col2:
            if st.button("🚀 Explore AI Templates Anyway", use_container_width=True):
                st.info("You can still use templates, but personalized analysis requires report data")
                # Pass empty responses for template-only access
                current_responses = {}

    # Import and show AI templates UI
    try:
        from ai_templates_ui import show_ai_templates_ui
        show_ai_templates_ui(competency_sections, selected_role, current_responses)
    except ImportError as e:
        st.error(f"AI Features temporarily unavailable: {str(e)}")
        st.info("""
        **To enable AI Features:**
        1. Ensure `ai_templates.py` is in your `frontend` directory
        2. Make sure `enhanced_ai_service.py` is in your `services` directory
        3. Check that all dependencies are installed
        """)
    except Exception as e:
        st.error(f"Error loading AI features: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

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

def handle_authentication():
    """Handle login/registration flow"""
    login_tab, register_tab, forgot_tab = st.tabs(["🔑 Login", "📝 Register", "😉 Forgot Password?"])

    with register_tab:
        auth.register_ui(api)

    with login_tab:
        auth.login_ui(api)

    with forgot_tab:
        # Check if we have a reset token in URL
        query_params = st.query_params
        if 'token' in query_params:
            auth.reset_password_ui(api)  # Show reset password form
        else:
            auth.forgot_password_ui(api)  # Show forgot password form



def main_app():
    """Main application after authentication"""
    user_role = st.session_state.get("user_role", "candidate")
    permissions = get_user_permissions(user_role)

    # Enhanced navigation
    st.sidebar.title("🧭 Navigation")

    # Main pages for all users
    main_pages = ["📊 Dashboard", "📝 Create Report", "📋 My Reports", "👤 Profile", "🛍️ Resources"]

    # Role-specific pages
    if "ai_features" in permissions:
        main_pages.append("🤖 AI Assistant")
    if "review_reports" in permissions:
        main_pages.append("👀 Review Dashboard")
    #if "view_all_reports" in permissions:
    #    main_pages.append("📈 All Reports")
    if "manage_users" in permissions or "system_settings" in permissions:
        main_pages.append("👑 Admin Dashboard")  # Single entry point

    # Always available
    main_pages.extend(["ℹ️ About", "📞 Contact"])

    # Page selection
    selected_page = st.sidebar.radio("Go to", main_pages, index=0)

    # User profile section
    show_user_profile_sidebar()

    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        api.logout()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Page routing
    page_map = {
        "📊 Dashboard": all_users_dashboard,
        "📝 Create Report": create_report_page,
        "📋 My Reports": reports_page,
        "👤 Profile": profile_page,
        "🛍️ Resources": resources_page,
        "🤖 AI Assistant": ai_assistant_page,
        "👀 Review Dashboard": lambda: review_dashboard(api),
        "👑 Admin Dashboard": admin_dashboard_wrapper,  # Single admin entry point
        "ℹ️ About": about_page,
        "📞 Contact": contact_page
    }

    # Execute selected page
    page_function = page_map.get(selected_page, all_users_dashboard)
    page_function()


def admin_dashboard_wrapper():
    """Wrapper function to ensure API client is properly authenticated before calling admin dashboard"""
    # Ensure API client has the current token
    if 'token' in st.session_state and st.session_state.token:
        api.set_token(st.session_state.token)
        print(f"🔍 ADMIN WRAPPER: Token set successfully for user {st.session_state.username}")
    else:
        st.error("❌ Authentication error: No token found. Please login again.")
        return

    # Check if user has admin permissions
    user_role = st.session_state.get("user_role", "")
    if user_role not in ['admin']:
        st.error("🔒 Access denied. Administrator privileges required.")
        return

    # Call the enhanced admin dashboard
    enhanced_admin_dashboard(api)


def all_users_dashboard():
    """Enhanced dashboard with overview"""
    show_dashboard(api)

def resources_page():
    """Resources & Marketplace page"""
    resources_marketplace()

def create_report_page():
    """Enhanced create report with verification check"""
    if not verification.check_verification_status(api):
        verification.verification_required_message()
    else:
        create_report.main_ui()


def reports_page():
    """Reports page with error handling"""
    try:
        enhanced_reports.enhanced_reports_ui(api)
    except Exception as e:
        ErrorHandler.show_error("Failed to load reports", str(e))


def profile_page():
    """Profile page"""
    user_profile.profile_page(api)



def about_page():
    """About page"""
    about.show()


def contact_page():
    """Contact page"""
    contact.show()


def main():
    # ===== EMAIL VERIFICATION HANDLER=====
    query_params = st.query_params
    if 'token' in query_params:
        # FIX: Properly extract the full token
        token_param = query_params['token']
        print(f"=== DEBUG: Raw token param: {token_param} ===")
        print(f"=== DEBUG: Type: {type(token_param)} ===")

        if isinstance(token_param, list) and len(token_param) > 0:
            verification_token = token_param[0]
        else:
            verification_token = str(token_param)

        print(f"=== DEBUG: Final token: {verification_token} ===")
        print(f"=== DEBUG: Token length: {len(verification_token)} ===")

        # Set page config for verification page - FIRST Streamlit command
        st.set_page_config(
            page_title="Verify Email - Engineering Report Deck",
            layout="centered"
        )

        st.markdown("""
             <div style="background: linear-gradient(90deg, #2c3e50, #3498db); padding: 2rem; border-radius: 10px; text-align: center; color: white; margin-bottom: 2rem;">
                 <h1 style="margin:0; font-size: 2.5rem;">🏭 Engineering Report Deck</h1>
                 <p style="margin:0; font-size: 1.2rem;">AI Revolution Driving Engineering Evolution ✨</p>
                 <p style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
                     <b>Version:</b> 2.0 — Tsodilo Edition
                 </p>
             </div>
         """, unsafe_allow_html=True)

        with st.spinner("Verifying your email address..."):
            try:
                print(f"=== FRONTEND DEBUG: Calling API with token: {verification_token} ===")
                success, result = api.verify_email(verification_token)
                print(f"=== FRONTEND DEBUG: API response - Success: {success}, Result: {result} ===")

                if success:
                    st.success("🎉 Email verified successfully!")
                    st.balloons()
                    st.markdown("""
                    **Your email has been verified! You can now:**

                    - ✅ **Login** to your account
                    - 📝 **Create** professional engineering reports  
                    - 🤖 **Use** AI-powered features
                    - 📊 **Track** your progress and history
                    """)

                    # Clear token from URL and show options
                    st.query_params.clear()

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🚀 Go to Login", use_container_width=True):
                            st.rerun()
                    with col2:
                        if st.button("📝 Create Report", use_container_width=True):
                            st.session_state.current_page = "Create Report"
                            st.rerun()

                else:
                    error_msg = result.get('detail', 'Unknown error')
                    st.error(f"❌ Verification failed: {error_msg}")

            except Exception as e:
                st.error(f"🚨 Error during verification: {str(e)}")
                st.info("Please check the console for detailed error information.")

        # Stop execution - don't show normal app
        st.stop()
    # ===== END VERIFICATION HANDLER =====

    # ===== PASSWORD RESET HANDLER =====
    if 'reset_token' in query_params:
        # Extract reset token
        reset_token_param = query_params['reset_token']
        print(f"=== DEBUG: Raw reset token param: {reset_token_param} ===")

        if isinstance(reset_token_param, list) and len(reset_token_param) > 0:
            reset_token = reset_token_param[0]
        else:
            reset_token = str(reset_token_param)

        print(f"=== DEBUG: Final reset token: {reset_token} ===")
        print(f"=== DEBUG: Reset token length: {len(reset_token)} ===")

        # Set page config for password reset page
        st.set_page_config(
            page_title="Reset Password - Engineering Report Deck",
            layout="centered"
        )

        st.markdown("""
               <div style="background: linear-gradient(90deg, #2c3e50, #3498db); padding: 2rem; border-radius: 10px; text-align: center; color: white; margin-bottom: 2rem;">
                   <h1 style="margin:0; font-size: 2.5rem;">🏭 Engineering Report Deck</h1>
                   <p style="margin:0; font-size: 1.2rem;">AI Revolution Driving Engineering Evolution ✨</p>
                   <p style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
                       <b>Version:</b> 2.0 — Tsodilo Edition
                   </p>
               </div>
           """, unsafe_allow_html=True)

        # Call the reset password UI
        from frontend import auth
        auth.reset_password_ui(api)
        st.stop()


    ################################################################
    st.set_page_config(
        page_title="🏭 Engineering Report Deck",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* Semi-sticky banner styles */
        .main-header-banner {
            position: sticky;
            top: 0;
            z-index: 999;
            transition: all 0.3s ease;
            background: linear-gradient(90deg, #2c3e50, #3498db);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }

        .main-header-banner.compact {
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .main-header-banner.compact h1 {
            font-size: 1.8rem !important;
            margin: 0 !important;
        }

        .main-header-banner.compact p {
            font-size: 1rem !important;
            margin: 0.2rem 0 0 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Semi-sticky app header
    st.markdown("""
        <div class="main-header-banner" id="mainBanner">
            <h1 style="margin:0; font-size: 2.5rem;">🏭 Engineering Report Deck</h1>
            <p style="margin:0; font-size: 1.2rem;">AI Revolution Driving Engineering Evolution ✨</p>
            <p style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
                <b>Version:</b> 2.0 — Tsodilo Edition
            </p>
        </div>

        <script>
        // Semi-sticky banner behavior
        let lastScrollTop = 0;
        const banner = document.getElementById('mainBanner');
        const scrollThreshold = 100;

        window.addEventListener('scroll', function() {
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop > scrollThreshold) {
                // Scrolling down - hide/compact
                if (scrollTop > lastScrollTop) {
                    banner.classList.add('compact');
                } 
                // Scrolling up - show
                else {
                    banner.classList.remove('compact');
                }
            } else {
                // Near top - always show full banner
                banner.classList.remove('compact');
            }

            lastScrollTop = scrollTop;
        });
        </script>
    """, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Authentication check
    if not st.session_state.logged_in:
        handle_authentication()
    else:
        main_app()


if __name__ == "__main__":
    main()