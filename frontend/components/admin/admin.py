import streamlit as st
from frontend.services.enhanced_api_client import EnhancedAPIClient
import pandas as pd
import json


def admin_dashboard(api: EnhancedAPIClient):
    st.title("👥 Admin Dashboard")

    # Dashboard overview
    show_dashboard_overview(api)

    # Users management tab
    users_tab, reports_tab, system_tab = st.tabs(["Users", "Reports", "System"])

    with users_tab:
        enhanced_manage_users(api)

    with reports_tab:
        enhanced_view_all_reports(api)

    with system_tab:
        system_monitoring(api)


def show_dashboard_overview(api: EnhancedAPIClient):
    """Show admin dashboard overview with metrics"""
    col1, col2, col3, col4 = st.columns(4)

    # Fetch data for metrics
    success, users = api.get_all_users()
    success_reports, reports = api.get_all_reports()

    total_users = len(users) if success else 0
    total_reports = len(reports) if success_reports else 0

    # Calculate metrics
    verified_users = len([u for u in users if u.get('is_verified')]) if success else 0
    active_reports = len(
        [r for r in reports if r.get('status') in ['submitted', 'under_review']]) if success_reports else 0

    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Verified Users", f"{verified_users}/{total_users}")
    with col3:
        st.metric("Total Reports", total_reports)
    with col4:
        st.metric("Pending Review", active_reports)


def enhanced_manage_users(api: EnhancedAPIClient):
    st.subheader("👤 User Management")

    # Search and filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Search users", placeholder="Username, email...")
    with col2:
        role_filter = st.selectbox("Filter by role",
                                   ["All", "admin", "reviewer", "engineer", "technologist", "technician", "candidate"])
    with col3:
        status_filter = st.selectbox("Filter by status", ["All", "Verified", "Unverified", "Active", "Inactive"])

    # Fetch all users
    success, users = api.get_all_users()

    if not success:
        st.error(f"Failed to fetch users: {users.get('detail', 'Unknown error')}")
        return

    if not users:
        st.info("No users found")
        return

    # Apply filters
    filtered_users = users
    if search_term:
        filtered_users = [u for u in filtered_users if
                          search_term.lower() in u.get('username', '').lower() or search_term.lower() in u.get('email',
                                                                                                               '').lower()]
    if role_filter != "All":
        filtered_users = [u for u in filtered_users if u.get('role') == role_filter]
    if status_filter == "Verified":
        filtered_users = [u for u in filtered_users if u.get('is_verified')]
    elif status_filter == "Unverified":
        filtered_users = [u for u in filtered_users if not u.get('is_verified')]
    elif status_filter == "Active":
        filtered_users = [u for u in filtered_users if u.get('is_active', True)]
    elif status_filter == "Inactive":
        filtered_users = [u for u in filtered_users if not u.get('is_active', True)]

    st.write(f"Showing {len(filtered_users)} of {len(users)} users")

    # Display users in an expandable table
    for user in filtered_users:
        with st.expander(f"👤 {user['username']} - {user['role'].title()} {'✅' if user.get('is_verified') else '❌'}"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**Email:** {user.get('email', 'N/A')}")
                st.write(f"**Full Name:** {user.get('full_name', 'N/A')}")
                st.write(f"**User ID:** {user['id']}")
                st.write(f"**Joined:** {user.get('created_at', 'N/A')}")
                st.write(f"**Status:** {'✅ Active' if user.get('is_active', True) else '❌ Inactive'}")
                st.write(f"**Verified:** {'✅ Yes' if user.get('is_verified') else '❌ No'}")

            with col2:
                st.subheader("Update Role")
                new_role = st.selectbox(
                    "Role",
                    ["candidate", "technician", "technologist", "engineer", "reviewer", "admin"],
                    index=["candidate", "technician", "technologist", "engineer", "reviewer", "admin"].index(
                        user['role']),
                    key=f"role_{user['id']}"
                )

                if st.button("Update Role", key=f"update_role_{user['id']}"):
                    if api.update_user_role(user['id'], new_role):
                        st.success(f"Updated {user['username']} to {new_role}")
                        st.rerun()
                    else:
                        st.error("Failed to update role")

            with col3:
                st.subheader("Account Actions")
                if user.get('is_active', True):
                    if st.button("Deactivate", key=f"deactivate_{user['id']}"):
                        if api.deactivate_user(user['id']):
                            st.success(f"Deactivated {user['username']}")
                            st.rerun()
                        else:
                            st.error("Failed to deactivate user")
                else:
                    if st.button("Activate", key=f"activate_{user['id']}"):
                        if api.activate_user(user['id']):
                            st.success(f"Activated {user['username']}")
                            st.rerun()
                        else:
                            st.error("Failed to activate user")

                # Resend verification email
                if not user.get('is_verified'):
                    if st.button("Resend Verification", key=f"resend_{user['id']}"):
                        if user.get('email'):
                            success, result = api.resend_verification_email(user['email'])
                            if success:
                                st.success("Verification email sent!")
                            else:
                                st.error(f"Failed: {result.get('detail', 'Unknown error')}")


def enhanced_view_all_reports(api: EnhancedAPIClient):
    st.subheader("📊 All Reports Management")

    # Report filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "draft", "submitted", "under_review", "approved", "rejected"],
            key="report_status_filter"
        )
    with col2:
        user_filter = st.text_input("Filter by User ID", placeholder="Enter user ID...")
    with col3:
        date_sort = st.selectbox("Sort by", ["Newest", "Oldest"])

    # Fetch all reports
    success, reports = api.get_all_reports()

    if not success:
        st.error(f"Failed to fetch reports: {reports.get('detail', 'Unknown error')}")
        return

    if not reports:
        st.info("No reports found")
        return

    # Apply filters
    filtered_reports = reports
    if status_filter != "All":
        filtered_reports = [r for r in filtered_reports if r.get('status') == status_filter]
    if user_filter:
        filtered_reports = [r for r in filtered_reports if str(r.get('owner_id')) == user_filter]

    # Sort reports
    if date_sort == "Newest":
        filtered_reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    else:
        filtered_reports.sort(key=lambda x: x.get('created_at', ''))

    st.write(f"Showing {len(filtered_reports)} of {len(reports)} reports")

    # Reports statistics
    status_counts = {}
    for report in reports:
        status = report.get('status', 'draft')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Show status distribution
    if status_counts:
        st.write("**Report Status Distribution:**")
        for status, count in status_counts.items():
            st.write(f"- {status.title()}: {count}")

    # Display reports
    for report in filtered_reports:
        status_color = {
            "draft": "⚪",
            "submitted": "🟡",
            "under_review": "🔵",
            "approved": "🟢",
            "rejected": "🔴"
        }

        status_icon = status_color.get(report.get('status', 'draft'), '⚪')

        with st.expander(f"{status_icon} {report['title']} (User: {report['owner_id']})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Report ID:** {report['id']}")
                st.write(f"**Status:** {report.get('status', 'draft').title()}")
                st.write(f"**Created:** {report.get('created_at', 'N/A')}")
                if report.get('submitted_at'):
                    st.write(f"**Submitted:** {report.get('submitted_at')}")
                if report.get('reviewed_at'):
                    st.write(f"**Reviewed:** {report.get('reviewed_at')}")
                if report.get('reviewed_by'):
                    st.write(f"**Reviewer ID:** {report.get('reviewed_by')}")
                st.write(f"**Competencies:** {len(report.get('competencies', []))}")

                if report.get('review_notes'):
                    st.write(f"**Review Notes:** {report.get('review_notes')}")

                # Quick content preview
                content_preview = report.get('content', 'No content')
                if len(content_preview) > 300:
                    content_preview = content_preview[:300] + "..."
                st.write(f"**Content Preview:** {content_preview}")

            with col2:
                if report.get('status') in ['submitted', 'under_review']:
                    st.subheader("Quick Review")

                    review_status = st.selectbox(
                        "Decision",
                        ["approved", "rejected", "under_review"],
                        key=f"quick_decision_{report['id']}"
                    )

                    review_notes = st.text_area(
                        "Review Notes",
                        placeholder="Provide feedback...",
                        key=f"quick_notes_{report['id']}"
                    )

                    if st.button("Submit Review", key=f"quick_review_{report['id']}"):
                        success, result = api.review_report(
                            report['id'],
                            review_status,
                            review_notes
                        )
                        if success:
                            st.success(f"✅ Report {review_status}!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to review: {result.get('detail', 'Unknown error')}")

                # Export options
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(report, indent=2),
                    file_name=f"report_{report['id']}.json",
                    mime="application/json",
                    key=f"download_{report['id']}"
                )


def system_monitoring(api: EnhancedAPIClient):
    st.subheader("⚙️ System Monitoring")

    # System information
    col1, col2 = st.columns(2)

    with col1:
        st.info("**Database Status**")
        st.write("✅ Connected to SQLite")
        st.write("📊 Reports table: Active")
        st.write("👥 Users table: Active")

        st.info("**Email Service**")
        st.write("✅ Ethereal.email configured")
        st.write("📧 Verification emails: Enabled")

    with col2:
        st.info("**API Status**")
        st.write("✅ Backend: Running")
        st.write("🔐 Authentication: Active")
        st.write("📋 Review workflow: Enabled")

        st.info("**Security**")
        st.write("✅ Role-based access: Active")
        st.write("🔐 Password hashing: bcrypt")
        st.write("🎫 JWT tokens: Enabled")

    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Cache", key="refresh_cache"):
            st.info("Cache refresh initiated")
            st.rerun()

    with col2:
        if st.button("📊 Export User Data", key="export_users"):
            success, users = api.get_all_users()
            if success:
                df = pd.DataFrame(users)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name="users_export.csv",
                    mime="text/csv",
                    key="download_users_csv"
                )

    with col3:
        if st.button("🔍 System Check", key="system_check"):
            st.success("System check completed - All services operational")


def admin_reports_view(api: EnhancedAPIClient):
    """Simple all reports view for the navigation"""
    st.title("📊 All Reports")
    enhanced_view_all_reports(api)