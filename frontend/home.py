import os
import streamlit as st
from services.enhanced_api_client import EnhancedAPIClient
from services.api_client import APIClient
import profile, about, contact, create_report,auth, reports, enhanced_reports
from components.admin import admin
from services import verification
from enhanced_admin_dashboard import enhanced_admin_dashboard

st.set_page_config(page_title="🏭 Engineering Report Deck", layout="centered")
# ================== APP BANNER ==================
APP_VERSION = "v1.1 — Hypothesis Prime"
st.markdown(
    f"""
    <div style="
        position: relative;
        background: linear-gradient(90deg, #2c3e50, #3498db);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    ">
    <h1 style="margin:0;">🏭 Engineering Report Deck</h1>
    <p style="margin:0; font-size:1.1rem;"> AI Revolution Driving Engineering Evolution ✨ </p>
    <p style="margin-top:0.5rem; font-size:0.9rem; opacity:0.85;">
        <b>Version:</b> {APP_VERSION}
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)


def get_user_permissions(role: str) -> set:
    """Map roles to frontend permissions (Phase 1)"""
    permissions = {
        "admin": {"manage_users", "view_all_reports", "system_settings"},
        "reviewer": {"review_reports", "view_all_reports"},
        "engineer": {"create_reports", "view_own_reports", "export_reports"},
        "technologist": {"create_reports", "view_own_reports", "export_reports"},
        "technician": {"create_reports", "view_own_reports", "export_reports"},
        "candidate": {"view_own_reports"}
    }
    return permissions.get(role, set())


API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# ----------------- Session Init ----------------- #
if "api" not in st.session_state:
    #st.session_state.api = APIClient()
    st.session_state.api = EnhancedAPIClient()


api = st.session_state.api

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = "candidate"  # ✅ Initialize user_role

# ----------------- Auth Gate ----------------- #
if not st.session_state.logged_in:
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with register_tab:
        auth.register_ui(api)

    with login_tab:
        # ✅ Fix: login_ui returns success and sets session state internally
        auth.login_ui(api)

    st.stop()  # Stop rendering until logged in

# ----------------- Main App Navigation ----------------- #
if st.session_state.logged_in:
    user_role = st.session_state.get("user_role", "candidate")
    permissions = get_user_permissions(user_role)

#########################TEMPORARY USER ROLE DEBUG############################################################
# In frontend/home.py, add this after the login check
if st.session_state.logged_in:
    # Debug information
    with st.sidebar.expander("🔍 Debug Info"):
        st.write(f"Username: {st.session_state.username}")
        st.write(f"User Role: {st.session_state.user_role}")
        st.write(f"User ID: {st.session_state.get('user_id', 'N/A')}")
        st.write(f"Email: {st.session_state.get('user_email', 'N/A')}")
###########################################################################################
    # ✅ Start with basic navigation options
    nav_options = ["Reports", "Create Report", "Profile", "About", "Contact"]

    # ✅ Add role-based options
    if "view_all_reports" in permissions:
        nav_options.append("All Reports")
    if "manage_users" in permissions:
        nav_options.append("User Management")
    if "system_settings" in permissions:
        nav_options.append("Admin Settings")
        nav_options.append("Audit Dashboard")


    # ✅ Extended navigation menu
    page = st.sidebar.radio("📑 Navigation", nav_options)

    # ✅ Display user info in sidebar
    st.sidebar.success(f"👋 Logged in as {st.session_state.username}")
    st.sidebar.info(f"🎯 Role: {st.session_state.user_role.title()}")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.token = None
        st.session_state.user_role = "candidate"
        st.rerun()  # Forces redirect to login

    # ✅ Page routing
    if page == "Reports":
        #reports.reports_ui(api)
        enhanced_reports.enhanced_reports_ui(api)
    elif page == "Create Report":
        # Check if user is verified before allowing report creation
        if not verification.check_verification_status(api):
            verification.verification_required_message()
        else:
            create_report.main_ui()
    elif page == "About":
        about.show()
    elif page == "Contact":
        contact.show()
    elif page == "All Reports":
        admin.admin_reports_view(api)  # ✅ New admin reports view
    elif page == "User Management":
        admin.admin_dashboard(api)  # ✅ New admin dashboard
    # You can expand this later
    elif page == "Profile":
        profile.profile_page(api)
    elif page == "User Management":
        admin.admin_dashboard(api)  # ✅ Use the actual admin dashboard
        #enhanced_admin_dashboard(api)
    elif page == "Admin Settings":
        # ✅ Replace placeholder with actual system monitoring
        admin.system_monitoring(api)
    elif page == "Audit Dashboard":
        from audit_dashboard import audit_dashboard

        audit_dashboard(api)

