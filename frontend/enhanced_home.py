import streamlit as st
from datetime import datetime
from typing import List, Dict
import enhanced_admin_dashboard
from services.enhanced_api_client import EnhancedAPIClient
import about, contact, create_report, auth, enhanced_reports, user_profile
from enhanced_admin_dashboard import enhanced_admin_dashboard
from frontend import verification
from utilities.error_handling import ErrorHandler, LoadingState, display_network_status
import functools



# Initialize enhanced API client
if "api" not in st.session_state:
    st.session_state.api = EnhancedAPIClient()

api = st.session_state.api



def get_user_permissions(role: str) -> set:
    """Enhanced permission system"""
    permissions = {
        "admin": {"manage_users", "view_all_reports", "system_settings", "audit_access", "export_data", "ai_features"},
        "reviewer": {"review_reports", "export_reports", "ai_features"},
        "engineer": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "technologist": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "technician": {"create_reports", "view_own_reports", "export_reports", "ai_feedback", "ai_features"},
        "candidate": {"view_own_reports", "create_reports", "ai_features"}
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

    selected_role = st.session_state.get("selected_role", "Engineer")

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

########################## REPORT REVIEW ###################################
def review_dashboard():
    """Review dashboard for reviewers - using the review queue from admin dashboard"""
    st.title("👀 Review Dashboard")

    # Permission check for reviewers
    user_role = st.session_state.get('user_role', '')
    if user_role not in ['admin', 'reviewer']:
        ErrorHandler.show_error("🔒 Access denied. Reviewer privileges required.")
        return

    # Create a minimal version of the review functionality from admin dashboard
    _show_reviewer_dashboard()


@functools.lru_cache(maxsize=1)
def get_cached_reports_for_review(api, user_id):
    """Cache reports for review to prevent repeated API calls"""
    return api.get_reports_for_review()


def _show_reviewer_dashboard():
    """Show the review queue interface for reviewers"""
    st.subheader("📝 Reports Pending Review")

    # Load reports for review with caching
    with LoadingState("Loading reports for review..."):
        # Use cached version if available
        cache_key = f"reports_for_review_{st.session_state.user_id}"
        if cache_key not in st.session_state:
            success, reports = st.session_state.api.get_reports_for_review()
            if success:
                st.session_state[cache_key] = reports
            else:
                st.session_state[cache_key] = []

        reports = st.session_state[cache_key]

        if not reports:
            st.success("🎉 No reports pending review!")
            return

        # Filter pending review reports
        pending_review = [r for r in reports if r.get('status') in ['submitted', 'under_review']]

        if not pending_review:
            st.success("✅ All reports have been reviewed!")
            return

        # Check if we're currently reviewing a report - use a container to prevent rerun
        review_container = st.container()

        with review_container:
            if 'current_review_id' in st.session_state and st.session_state.current_review_id:
                _show_review_interface(st.session_state.current_review_id, pending_review)
                return

        # Display review queue outside the container to prevent unnecessary reruns
        st.write(f"**{len(pending_review)} reports awaiting your review:**")

        # Use forms for better button handling
        for report in pending_review:
            with st.expander(f"📝 {report['title']} (ID: {report['id']})", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Author:** {report.get('owner_full_name', 'Unknown')}")
                    st.write(f"**Username:** {report.get('owner_username', 'N/A')}")
                    st.write(f"**Email:** {report.get('owner_email', 'No email')}")
                    st.write(f"**Submitted:** {_format_date(report.get('submitted_at'))}")
                    st.write(f"**Word Count:** {len(report.get('content', '').split())}")

                    # Show preview of content
                    content_preview = report.get('content', '')[:200] + "..." if len(
                        report.get('content', '')) > 200 else report.get('content', '')
                    st.write(f"**Preview:** {content_preview}")

                with col2:
                    # Use form submission for smoother transitions
                    if st.button("👀 Review", key=f"review_{report['id']}", use_container_width=True):
                        st.session_state.current_review_id = report['id']
                        # Clear cache to force refresh when returning
                        cache_key = f"reports_for_review_{st.session_state.user_id}"
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.rerun()



def _show_review_interface(report_id: int, pending_reports: List[Dict]):
    """Display the actual review interface"""
    # Find the report being reviewed
    report_to_review = next((r for r in pending_reports if r['id'] == report_id), None)

    if not report_to_review:
        st.error("Report not found or no longer available for review")
        if 'current_review_id' in st.session_state:
            del st.session_state.current_review_id
        # Clear cache to refresh data
        cache_key = f"reports_for_review_{st.session_state.user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        st.rerun()
        return

    st.subheader(f"📋 Review Report: {report_to_review['title']}")

    # Back button with form
    if st.button("← Back to Review Queue", use_container_width=True):
        if 'current_review_id' in st.session_state:
            del st.session_state.current_review_id
        # Clear cache to refresh data
        cache_key = f"reports_for_review_{st.session_state.user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        st.rerun()

    # Report details
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Report Details**")
        st.write(f"**ID:** {report_to_review['id']}")
        st.write(f"**Author:** {report_to_review.get('owner_full_name', 'Unknown')}")
        st.write(f"**Username:** {report_to_review.get('owner_username', 'N/A')}")
        st.write(f"**Email:** {report_to_review.get('owner_email', 'No email')}")
        st.write(f"**Submitted:** {_format_date(report_to_review.get('submitted_at'))}")
        st.write(f"**Status:** {report_to_review.get('status', 'unknown')}")

    with col2:
        st.write("**Statistics**")
        st.write(f"**Word Count:** {len(report_to_review.get('content', '').split())}")
        st.write(f"**Created:** {_format_date(report_to_review.get('created_at'))}")
        if report_to_review.get('updated_at'):
            st.write(f"**Last Updated:** {_format_date(report_to_review.get('updated_at'))}")

    # Report content
    st.markdown("---")
    st.subheader("Report Content")
    st.text_area("Content", report_to_review.get('content', ''), height=300, key="review_content", disabled=True)

    # Review actions
    st.markdown("---")
    st.subheader("Review Decision")

    col3, col4, col5 = st.columns([1, 1, 2])

    with col3:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            _submit_review_decision(report_id, "approved")

    with col4:
        if st.button("❌ Reject", type="secondary", use_container_width=True):
            _submit_review_decision(report_id, "rejected")

    with col5:
        review_notes = st.text_area("Review Notes (Optional)",
                                    placeholder="Add any feedback or notes for the author...",
                                    key=f"notes_{report_id}")

    # Competencies section (if available)
    if report_to_review.get('competencies'):
        st.markdown("---")
        st.subheader("Competencies")
        for comp in report_to_review['competencies']:
            with st.expander(f"🔧 {comp.get('competency_title', 'Competency')}"):
                st.write(f"**Response:** {comp.get('user_response', 'No response')}")


def _submit_review_decision(report_id: int, decision: str):
    """Submit the review decision to the API"""
    review_notes = st.session_state.get(f"notes_{report_id}", "")

    with LoadingState(f"Submitting {decision} decision..."):
        success, result = st.session_state.api.review_report(
            report_id=report_id,
            status=decision,
            review_notes=review_notes
        )

    if success:
        st.balloons()
        st.success(f"✅ Report {decision} successfully!")

        # Clear review state and cache
        if 'current_review_id' in st.session_state:
            del st.session_state.current_review_id
        if f"notes_{report_id}" in st.session_state:
            del st.session_state[f"notes_{report_id}"]

        # Clear cache to force refresh
        cache_key = f"reports_for_review_{st.session_state.user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

        # Use success message without delay
        st.balloons()
        # Let the user see the success message before continuing
        if st.button("← Back to Review Queue", key="success_back"):
            st.rerun()

    else:
        error_msg = result.get('detail', 'Unknown error occurred')
        ErrorHandler.show_error(f"Failed to submit review: {error_msg}")

def _format_date(date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return "N/A"

    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

##############################################################################

def ai_assistant_page():
    """AI Assistant main page"""
    st.title("🤖 AI Assistant")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea, #764ba2); padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h3 style="margin:0; color: white;">AI-Powered Report Enhancement</h3>
        <p style="margin:0.5rem 0 0 0; color: white; opacity: 0.9;">
            Smart templates, gap analysis, and quality improvement for your engineering reports
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

def handle_authentication():
    """Handle login/registration flow"""
    login_tab, register_tab, forgot_tab = st.tabs(["🔑 Login", "📝 Register", "😉 Forgot Password"])

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
    main_pages = ["📊 Dashboard", "📝 Create Report", "📋 My Reports", "👤 Profile"]

    # Role-specific pages
    if "ai_features" in permissions:
        main_pages.append("🤖 AI Assistant")
    if "review_reports" in permissions:
        main_pages.append("👀 Review Dashboard")
    if "view_all_reports" in permissions:
        main_pages.append("📈 All Reports")
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
        "📊 Dashboard": show_dashboard,
        "📝 Create Report": create_report_page,
        "📋 My Reports": reports_page,
        "👤 Profile": profile_page,
        "🤖 AI Assistant": ai_assistant_page,
        "👀 Review Dashboard": review_dashboard,
        "📈 All Reports": all_reports_page,
        "👥 User Management": user_management_page,  # ← Now uses enhanced_admin_dashboard
        "⚙️ Admin Settings": admin_settings_page,  # ← Now uses enhanced_admin_dashboard
        "👑 Admin Dashboard": lambda: enhanced_admin_dashboard(api),  # If using single entry
        "📊 Analytics Dashboard": lambda: enhanced_admin_dashboard(api),  # Alternative name
        "ℹ️ About": about_page,
        "📞 Contact": contact_page
    }

    # Execute selected page
    page_function = page_map.get(selected_page, show_dashboard)
    page_function()


def show_dashboard():
    """Enhanced dashboard with overview"""
    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.subheader("📝 Reports")
            success, reports_data = api.fetch_reports()
            if success:
                st.metric("Total Reports", len(reports_data))
                draft_count = sum(1 for r in reports_data if r.get('status') == 'draft')
                st.metric("Drafts", draft_count)
            else:
                st.write("No reports")

    with col2:
        with st.container(border=True):
            st.subheader("🎯 Progress")
            # Add progress visualization here
            st.info("Progress tracking coming soon")

    with col3:
        with st.container(border=True):
            st.subheader("🤖 AI Features")
            if "ai_features" in get_user_permissions(st.session_state.user_role):
                st.success("AI Assistant Available")
                if st.button("Try AI Assistant"):
                    st.session_state.current_page = "🤖 AI Assistant"
                    st.rerun()
            else:
                st.info("Upgrade for AI features")


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


def all_reports_page():
    """All reports view for admins/reviewers"""
    enhanced_admin_dashboard(api)


def user_management_page():
    """User management for admins"""
    enhanced_admin_dashboard(api)


def admin_settings_page():
    """Admin settings"""
    enhanced_admin_dashboard(api)


def audit_dashboard_page():
    """Audit dashboard"""
    from admin_audit_dashboard import audit_dashboard
    audit_dashboard(api)


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

    # App header
    st.markdown("""
        <div style="background: linear-gradient(90deg, #2c3e50, #3498db); padding: 2rem; border-radius: 10px; text-align: center; color: white; margin-bottom: 2rem;">
            <h1 style="margin:0; font-size: 2.5rem;">🏭 Engineering Report Deck</h1>
            <p style="margin:0; font-size: 1.2rem;">AI Revolution Driving Engineering Evolution ✨</p>
            <p style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
                <b>Version:</b> 2.0 — Tsodilo Edition
            </p>
        </div>
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