import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services.enhanced_api_client import EnhancedAPIClient


def audit_dashboard(api: EnhancedAPIClient):
    st.title("📊 Audit Dashboard")

    # Check permissions
    user_role = st.session_state.get('user_role', '')
    if user_role not in ['admin']:
        st.error("🔒 Access denied. Admin privileges required.")
        return

    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Log Explorer", "User Activity", "System Stats"])

    with tab1:
        show_audit_overview(api)

    with tab2:
        show_log_explorer(api)

    with tab3:
        show_user_activity(api)

    with tab4:
        show_system_stats(api)


def show_audit_overview(api: EnhancedAPIClient):
    st.subheader("📈 Audit Overview")

    # Get audit stats
    success, stats = api.get_system_stats()  # You'll need to add this endpoint
    if not success:
        st.error("Failed to load audit statistics")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Logs", stats.get('total_logs', 0))
    with col2:
        st.metric(f"Last 30 Days", stats.get('recent_logs', 0))
    with col3:
        st.metric("Top User", list(stats.get('top_users', {}).keys())[0] if stats.get('top_users') else "N/A")
    with col4:
        st.metric("Most Common Action",
                  list(stats.get('actions_breakdown', {}).keys())[0] if stats.get('actions_breakdown') else "N/A")

    # Actions breakdown chart
    if stats.get('actions_breakdown'):
        st.subheader("Actions Breakdown")
        actions_df = pd.DataFrame(
            list(stats['actions_breakdown'].items()),
            columns=['Action', 'Count']
        ).sort_values('Count', ascending=True)

        fig = px.bar(
            actions_df,
            y='Action',
            x='Count',
            orientation='h',
            title="Activity by Action Type"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Timeline chart
    if stats.get('timeline'):
        st.subheader("Activity Timeline")
        timeline_df = pd.DataFrame(stats['timeline'])
        fig = px.line(
            timeline_df,
            x='date',
            y='count',
            title="Daily Activity (Last 7 Days)"
        )
        st.plotly_chart(fig, use_container_width=True)


def show_log_explorer(api: EnhancedAPIClient):
    st.subheader("🔍 Log Explorer")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        user_filter = st.text_input("Filter by Username")
    with col2:
        action_filter = st.selectbox("Filter by Action", ["All"] + get_available_actions(api))
    with col3:
        resource_filter = st.selectbox("Filter by Resource", ["All", "user", "report", "system"])

    # Search
    search_term = st.text_input("🔍 Search logs")

    # Load logs
    if st.button("Load Logs"):
        with st.spinner("Loading audit logs..."):
            success, logs = api.get_audit_logs(
                username=user_filter if user_filter else None,
                action=action_filter if action_filter != "All" else None,
                resource_type=resource_filter if resource_filter != "All" else None
            )

            if success:
                display_logs_table(logs)
            else:
                st.error("Failed to load audit logs")


def show_user_activity(api: EnhancedAPIClient):
    st.subheader("👥 User Activity")

    # Get all users
    success, users = api.get_all_users()
    if not success:
        st.error("Failed to load users")
        return

    # User selector
    selected_user = st.selectbox(
        "Select User",
        [f"{user['username']} (ID: {user['id']})" for user in users]
    )

    if selected_user and st.button("View User Activity"):
        user_id = int(selected_user.split("(ID: ")[1].rstrip(")"))

        success, user_logs = api.get_user_audit_logs(user_id)
        if success:
            display_user_activity(user_logs)
        else:
            st.error("Failed to load user activity")


def show_system_stats(api: EnhancedAPIClient):
    st.subheader("⚙️ System Statistics")

    # Cleanup options
    st.info("Database Maintenance")

    col1, col2 = st.columns(2)

    with col1:
        days_to_keep = st.slider("Keep logs from last (days)", 30, 1095, 365)

    with col2:
        st.write("")  # Spacer
        if st.button("🔄 Cleanup Old Logs", type="secondary"):
            with st.spinner("Cleaning up old logs..."):
                success, result = api.cleanup_audit_logs(days_to_keep)
                if success:
                    st.success(result.get('message', 'Cleanup completed'))
                else:
                    st.error("Cleanup failed")


def display_logs_table(logs):
    if not logs:
        st.info("No logs found matching your criteria")
        return

    # Convert to DataFrame for better display
    log_data = []
    for log in logs:
        log_data.append({
            'Timestamp': log.get('created_at', ''),
            'User': log.get('username', 'System'),
            'Action': log.get('action', ''),
            'Resource': f"{log.get('resource_type', '')} #{log.get('resource_id', '')}",
            'IP Address': log.get('ip_address', ''),
            'Details': str(log.get('details', {}))
        })

    df = pd.DataFrame(log_data)
    st.dataframe(df, use_container_width=True)


def display_user_activity(logs):
    if not logs:
        st.info("No activity found for this user")
        return

    # Activity summary
    st.subheader("Activity Summary")

    # Count actions
    action_counts = {}
    for log in logs:
        action = log.get('action', '')
        action_counts[action] = action_counts.get(action, 0) + 1

    if action_counts:
        summary_df = pd.DataFrame(
            list(action_counts.items()),
            columns=['Action', 'Count']
        ).sort_values('Count', ascending=False)

        st.dataframe(summary_df, use_container_width=True)

    # Recent activity
    st.subheader("Recent Activity")
    display_logs_table(logs[:20])  # Show last 20 activities


def get_available_actions(api: EnhancedAPIClient):
    """Get available audit actions from API"""
    success, response = api.get_audit_actions()
    if success:
        return response.get('available_actions', [])
    return []


def main():
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    audit_dashboard(api)


if __name__ == "__main__":
    main()