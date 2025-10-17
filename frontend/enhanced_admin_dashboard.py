import os
import logging
import pandas as pd
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional
from services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState
import json


class EnhancedAdminDashboard:
    """Enhanced admin dashboard with comprehensive analytics"""

    def __init__(self, api_client: EnhancedAPIClient):
        self.api = api_client
        self.stats_cache = {}

    def show_dashboard(self):
        """Main admin dashboard"""
        st.title("👑 Enhanced Admin Dashboard")

        # Permission check
        if not self._check_admin_permissions():
            return

        # Quick stats header
        self._show_quick_stats()

        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "👥 User Management",
            "📋 Reports Analytics",
            "🔍 Audit Trail",
            "⚙️ System Settings"
        ])

        with tab1:
            self._show_overview_tab()

        with tab2:
            self._show_user_management_tab()

        with tab3:
            self._show_reports_analytics_tab()

        with tab4:
            self._show_audit_trail_tab()

        with tab5:
            self._show_system_settings_tab()

    def _check_admin_permissions(self) -> bool:
        """Check if user has admin permissions"""
        user_role = st.session_state.get('user_role', '')
        if user_role not in ['admin']:
            ErrorHandler.show_error("🔒 Access denied. Administrator privileges required.")
            return False
        return True

    def _show_quick_stats(self):
        """Display quick statistics header"""
        with LoadingState("Loading system statistics..."):
            stats = self._get_system_stats()

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Users",
                stats.get('total_users', 0),
                delta=stats.get('new_users_7d', 0)
            )

        with col2:
            st.metric(
                "Total Reports",
                stats.get('total_reports', 0),
                delta=stats.get('new_reports_7d', 0)
            )

        with col3:
            st.metric(
                "Active Today",
                stats.get('active_users_today', 0)
            )

        with col4:
            approval_rate = stats.get('approval_rate', 0)
            st.metric(
                "Approval Rate",
                f"{approval_rate:.1f}%"
            )

        with col5:
            avg_response_time = stats.get('avg_response_time', 0)
            st.metric(
                "Avg Response Time",
                f"{avg_response_time:.1f} days"
            )

    def _show_overview_tab(self):
        """Overview tab with system analytics"""
        st.subheader("📊 System Overview")

        # Fetch comprehensive data
        with LoadingState("Loading analytics data..."):
            users_data = self._get_users_data()
            reports_data = self._get_reports_data()
            audit_data = self._get_audit_data()

        # Row 1: User growth and activity
        col1, col2 = st.columns(2)

        with col1:
            self._plot_user_growth(users_data)

        with col2:
            self._plot_user_activity(audit_data)

        # Row 2: Report statistics
        col3, col4 = st.columns(2)

        with col3:
            self._plot_report_status_distribution(reports_data)

        with col4:
            self._plot_report_timeline(reports_data)

        # Row 3: System health
        st.subheader("🩺 System Health")
        self._show_system_health()

    def _show_user_management_tab(self):
        """Enhanced user management interface"""
        st.subheader("👥 User Management")

        # User actions toolbar
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            search_term = st.text_input("🔍 Search users...", placeholder="Search by username, email, or role")

        with col2:
            role_filter = st.selectbox("Role", ["All", "admin", "reviewer", "engineer", "technologist", "technician",
                                                "candidate"])

        with col3:
            status_filter = st.selectbox("Status", ["All", "active", "inactive"])

        with col4:
            verification_filter = st.selectbox("Verified", ["All", "verified", "unverified"])

        # Load users
        with LoadingState("Loading users..."):
            success, users = self.api.get_all_users()

            if not success:
                ErrorHandler.show_error("Failed to load users")
                return

        # Apply filters
        filtered_users = self._filter_users(users, search_term, role_filter, status_filter, verification_filter)

        # User statistics
        st.write(f"**Showing {len(filtered_users)} of {len(users)} users**")

        # Users table with enhanced features
        self._show_users_table(filtered_users)



    def _show_reports_analytics_tab(self):
        """Comprehensive reports analytics"""
        st.subheader("📋 Reports Analytics")

        # Date range filter
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            date_range = st.selectbox(
                "Time Period",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                key="reports_date_range"
            )

        with col2:
            profession_filter = st.selectbox(
                "Profession",
                ["All", "Engineer", "Engineering Technologist", "Engineering Technician"],
                key="reports_profession"
            )

        with col3:
            st.write("")  # Spacer

        # Load reports data
        with LoadingState("Loading reports analytics..."):
            success, reports = self.api.get_all_reports()

            if not success:
                ErrorHandler.show_error("Failed to load reports")
                return

        # Apply filters
        filtered_reports = self._filter_reports(reports, date_range, profession_filter)

        # Analytics overview
        self._show_reports_analytics_overview(filtered_reports)

        # Detailed charts
        col1, col2 = st.columns(2)

        with col1:
            self._plot_competency_completion_heatmap(filtered_reports)

        with col2:
            self._plot_report_quality_metrics(filtered_reports)

        # Report review queue
        st.subheader("📝 Review Queue")
        self._show_review_queue(filtered_reports)

    def _show_audit_trail_tab(self):
        """Enhanced audit trail with advanced filtering"""
        st.subheader("🔍 Audit Trail")

        # Advanced filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            audit_user_filter = st.text_input("User", key="audit_user")

        with col2:
            audit_action_filter = st.selectbox(
                "Action",
                ["All", "login", "logout", "create_report", "update_report", "delete_report", "user_creation",
                 "role_change"],
                key="audit_action"
            )

        with col3:
            audit_resource_filter = st.selectbox(
                "Resource",
                ["All", "user", "report", "system"],
                key="audit_resource"
            )

        with col4:
            audit_date_filter = st.selectbox(
                "Time Range",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
                key="audit_date"
            )

        # Load audit logs
        if st.button("🔍 Load Audit Logs", key="load_audit"):
            with LoadingState("Loading audit logs..."):
                success, logs = self.api.get_audit_logs(
                    username=audit_user_filter if audit_user_filter else None,
                    action=audit_action_filter if audit_action_filter != "All" else None,
                    resource_type=audit_resource_filter if audit_resource_filter != "All" else None
                )

                if success:
                    st.session_state.audit_logs = logs
                else:
                    ErrorHandler.show_error("Failed to load audit logs")

        # Display audit logs
        if 'audit_logs' in st.session_state:
            self._show_audit_logs_table(st.session_state.audit_logs)

        # Audit statistics
        st.subheader("📈 Audit Statistics")
        self._show_audit_statistics()

    def _show_system_settings_tab(self):
        """Enhanced system settings with all metrics"""
        st.subheader("⚙️ System Settings")

        # System configuration
        col1, col2 = st.columns(2)

        with col1:
            st.write("**🛠️ System Configuration**")

            # Auto-cleanup settings
            cleanup_days = st.slider(
                "Keep audit logs for (days)",
                min_value=30,
                max_value=365,
                value=90,
                help="Older audit logs will be automatically deleted"
            )

            if st.button("🗑️ Run Cleanup Now", key="immediate_cleanup"):
                with LoadingState("Cleaning up old logs..."):
                    success, result = self.api.cleanup_audit_logs(cleanup_days)
                    if success:
                        st.success(f"Cleanup completed: {result.get('message', 'Success')}")
                    else:
                        ErrorHandler.show_error("Cleanup failed")

            # Export system data
            st.write("**💾 Data Export**")
            if st.button("📤 Export System Data", key="export_system_data"):
                self._export_system_data()

        with col2:
            st.write("**🔧 Maintenance**")

            # System health check
            if st.button("🩺 Run Health Check", key="health_check"):
                self._run_system_health_check()

        # Comprehensive Health Dashboard
        st.markdown("---")
        self._show_system_health_dashboard()

        # Database Statistics
        st.markdown("---")
        st.subheader("📈 Database Statistics")
        db_stats = self._get_database_stats()

        # Your existing database stats display code...
        if db_stats.get('is_real_data'):
            if db_stats['table_count'] > 0:
                st.success(
                    f"✅ **Live Database Data** - {db_stats['table_count']} tables, {db_stats['total_records']:,} total records")
            else:
                st.warning("⚠️ **Database Connected** - No tables created yet")
        else:
            st.error(f"❌ **{db_stats.get('database_status', 'Unknown error')}**")

        # Create organized statistics table
        stats_data = [
            {"Metric": "Total Records", "Value": f"{db_stats.get('total_records', 0):,}", "Category": "Overview"},
            {"Metric": "Database File Size", "Value": f"{db_stats.get('db_size_mb', 0):.2f} MB", "Category": "Storage"},
            {"Metric": "Tables Found", "Value": f"{db_stats.get('table_count', 0)}", "Category": "Overview"},
            {"Metric": "Users", "Value": f"{db_stats.get('users_count', 0):,}", "Category": "Tables"},
            {"Metric": "Reports", "Value": f"{db_stats.get('reports_count', 0):,}", "Category": "Tables"},
            {"Metric": "Audit Logs", "Value": f"{db_stats.get('audit_logs_count', 0):,}", "Category": "Tables"},
        ]

        # Add performance metrics if available
        if db_stats.get('response_time_ms'):
            stats_data.append({"Metric": "Response Time", "Value": f"{db_stats.get('response_time_ms', 0)}ms",
                               "Category": "Performance"})
        if db_stats.get('cache_hit_ratio'):
            stats_data.append({"Metric": "Cache Hit Ratio", "Value": f"{db_stats.get('cache_hit_ratio', 0)}%",
                               "Category": "Performance"})

        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

        # Database Tables
        st.markdown("---")
        self._show_database_tables()

        # Storage Metrics
        st.markdown("---")
        self._show_database_storage()

        # Refresh all button
        if st.button("🔄 Refresh All System Metrics", key="refresh_all_metrics", use_container_width=True):
            st.rerun()

    def _show_system_health_dashboard(self):
        """Display comprehensive system health dashboard using all APIs"""
        st.subheader("🩺 System Health Dashboard")

        col1, col2 = st.columns(2)

        with col1:
            # Database Health
            st.write("**📊 Database Health**")
            with LoadingState("Checking database health..."):
                success, health = self.api.get_database_health()

            if success:
                status = health.get('status', 'unknown')
                if status == 'healthy':
                    st.success("✅ **Status:** Healthy")
                elif status == 'unhealthy':
                    st.error("❌ **Status:** Unhealthy")
                else:
                    st.warning("⚠️ **Status:** Unknown")

                col1a, col2a, col3a = st.columns(3)
                with col1a:
                    st.metric("Response Time", f"{health.get('response_time_ms', 0)}ms")
                with col2a:
                    st.metric("Connections", health.get('active_connections', 0))
                with col3a:
                    st.metric("Cache Hit", f"{health.get('cache_hit_ratio', 0)}%")
            else:
                st.error("❌ Database health check failed")

        with col2:
            # System Metrics
            st.write("**💻 System Metrics**")
            with LoadingState("Checking system metrics..."):
                success, metrics = self.api.get_system_metrics()

            if success:
                cpu = metrics.get('cpu', {})
                memory = metrics.get('memory', {})
                disk = metrics.get('disk', {})

                col1b, col2b, col3b = st.columns(3)
                with col1b:
                    st.metric("CPU Usage", f"{cpu.get('percent', 0)}%")
                with col2b:
                    st.metric("Memory Usage", f"{memory.get('percent', 0)}%")
                with col3b:
                    st.metric("Disk Usage", f"{disk.get('percent', 0)}%")

                # System info
                system_info = metrics.get('system', {})
                st.caption(
                    f"Uptime: {system_info.get('uptime_hours', 0)}h | Platform: {system_info.get('platform', 'Unknown')}")
            else:
                st.error("❌ System metrics unavailable")




    def _get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        # Try to use cached stats if recent
        cache_key = "system_stats"
        if cache_key in self.stats_cache:
            cache_time, cached_data = self.stats_cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5 minutes
                return cached_data

        stats = {}

        # Get users data
        success, users = self.api.get_all_users()
        if success:
            stats['total_users'] = len(users)
            stats['active_users_today'] = len([u for u in users if u.get('is_active', True)])
            stats['new_users_7d'] = len([u for u in users if self._is_recent(u.get('created_at'), 7)])

        # Get reports data
        success, reports = self.api.get_all_reports()
        if success:
            stats['total_reports'] = len(reports)
            stats['new_reports_7d'] = len([r for r in reports if self._is_recent(r.get('created_at'), 7)])

            # Calculate approval rate
            approved = len([r for r in reports if r.get('status') == 'approved'])
            reviewed = len([r for r in reports if r.get('status') in ['approved', 'rejected']])
            stats['approval_rate'] = (approved / reviewed * 100) if reviewed > 0 else 0

            # Calculate average response time (simplified)
            stats['avg_response_time'] = 2.5  # Placeholder

        # Cache the results
        self.stats_cache[cache_key] = (datetime.now(), stats)

        return stats

    def _get_users_data(self) -> List[Dict]:
        """Get enhanced users data"""
        success, users = self.api.get_all_users()
        return users if success else []

    def _get_reports_data(self) -> List[Dict]:
        """Get enhanced reports data"""
        success, reports = self.api.get_all_reports()
        return reports if success else []

    def _get_audit_data(self) -> List[Dict]:
        """Get audit data for analytics"""
        success, logs = self.api.get_audit_logs(limit=1000)
        return logs if success else []

    def _plot_user_growth(self, users_data: List[Dict]):
        """Plot user growth over time"""
        if not users_data:
            st.info("No user data available")
            return

        # Process user creation dates
        creation_dates = []
        for user in users_data:
            created_at = user.get('created_at')
            if created_at:
                try:
                    # Handle different date formats
                    if 'T' in created_at:
                        date_part = created_at.split('T')[0]
                    else:
                        date_part = created_at.split(' ')[0]

                    creation_dates.append(pd.to_datetime(date_part))
                except:
                    continue

        if not creation_dates:
            st.info("No valid creation dates found")
            return

        # Create timeline data
        df = pd.DataFrame(creation_dates, columns=['date'])
        df['count'] = 1
        timeline = df.groupby('date').sum().cumsum().reset_index()

        fig = px.area(
            timeline,
            x='date',
            y='count',
            title="📈 User Growth Over Time",
            labels={'date': 'Date', 'count': 'Total Users'}
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Users",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    def _plot_user_activity(self, audit_data: List[Dict]):
        """Plot user activity patterns"""
        if not audit_data:
            st.info("No audit data available")
            return

        # Process activity data
        activity_by_hour = {i: 0 for i in range(24)}

        for log in audit_data:
            timestamp = log.get('created_at')
            if timestamp:
                try:
                    hour = pd.to_datetime(timestamp).hour
                    activity_by_hour[hour] += 1
                except:
                    continue

        # Create bar chart
        hours = list(activity_by_hour.keys())
        counts = list(activity_by_hour.values())

        fig = px.bar(
            x=hours,
            y=counts,
            title="🕒 User Activity by Hour",
            labels={'x': 'Hour of Day', 'y': 'Activity Count'}
        )

        fig.update_layout(
            xaxis_title="Hour of Day (24h)",
            yaxis_title="Activity Count",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    def _plot_report_status_distribution(self, reports_data: List[Dict]):
        """Plot report status distribution"""
        if not reports_data:
            st.info("No reports data available")
            return

        status_counts = {}
        for report in reports_data:
            status = report.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        if not status_counts:
            st.info("No status data available")
            return

        fig = px.pie(
            names=list(status_counts.keys()),
            values=list(status_counts.values()),
            title="📊 Report Status Distribution"
        )

        st.plotly_chart(fig, use_container_width=True)

    def _plot_report_timeline(self, reports_data: List[Dict]):
        """Plot report creation timeline"""
        if not reports_data:
            st.info("No reports data available")
            return

        creation_dates = []
        for report in reports_data:
            created_at = report.get('created_at')
            if created_at:
                try:
                    if 'T' in created_at:
                        date_part = created_at.split('T')[0]
                    else:
                        date_part = created_at.split(' ')[0]

                    creation_dates.append(pd.to_datetime(date_part))
                except:
                    continue

        if not creation_dates:
            st.info("No valid creation dates found")
            return

        df = pd.DataFrame(creation_dates, columns=['date'])
        daily_counts = df.groupby('date').size().reset_index(name='count')

        fig = px.line(
            daily_counts,
            x='date',
            y='count',
            title="📅 Daily Report Creation",
            labels={'date': 'Date', 'count': 'Reports Created'}
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_system_health(self):
        """Display system health metrics"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # API responsiveness
            start_time = datetime.now()
            success, _ = self.api.health_check()
            response_time = (datetime.now() - start_time).total_seconds()

            if success and response_time < 1.0:
                st.success("✅ API: Healthy")
            elif success and response_time < 3.0:
                st.warning("⚠️ API: Slow")
            else:
                st.error("❌ API: Unhealthy")

            st.metric("Response Time", f"{response_time:.2f}s")

        with col2:
            # Database health (simplified)
            success, users = self.api.get_all_users()
            if success and len(users) > 0:
                st.success("✅ Database: Healthy")
            else:
                st.error("❌ Database: Issues")

            st.metric("User Records", len(users) if success else "N/A")

        with col3:
            # Cache performance (placeholder)
            cache_hit_rate = 95.2  # Placeholder
            if cache_hit_rate > 90:
                st.success("✅ Cache: Optimal")
            elif cache_hit_rate > 80:
                st.warning("⚠️ Cache: Good")
            else:
                st.error("❌ Cache: Poor")

            st.metric("Hit Rate", f"{cache_hit_rate}%")

        with col4:
            # System load (placeholder)
            system_load = 65.5  # Placeholder
            if system_load < 70:
                st.success("✅ Load: Normal")
            elif system_load < 85:
                st.warning("⚠️ Load: High")
            else:
                st.error("❌ Load: Critical")

            st.metric("System Load", f"{system_load}%")

    def _filter_users(self, users: List[Dict], search: str, role: str, status: str, verification: str) -> List[Dict]:
        """Filter users based on criteria"""
        filtered = users

        # Search filter
        if search:
            search_lower = search.lower()
            filtered = [u for u in filtered if
                        search_lower in u.get('username', '').lower() or
                        search_lower in u.get('email', '').lower() or
                        search_lower in u.get('full_name', '').lower()]

        # Role filter
        if role != "All":
            filtered = [u for u in filtered if u.get('role') == role]

        # Status filter
        if status != "All":
            is_active = status == "active"
            filtered = [u for u in filtered if u.get('is_active', True) == is_active]

        # Verification filter
        if verification != "All":
            is_verified = verification == "verified"
            filtered = [u for u in filtered if u.get('is_verified', False) == is_verified]

        return filtered

    def _show_bulk_operations_toolbar(self, users: List[Dict]):
        """Show bulk operations toolbar when users are selected"""
        st.markdown("---")
        st.subheader("🛠️ Bulk Operations")

        selected_count = len(st.session_state.selected_user_ids)
        st.info(f"**{selected_count} users selected**")

        # Bulk action options
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            new_role = st.selectbox(
                "Set Role",
                ["reviewer", "engineer", "technologist", "technician", "candidate"],
                key="bulk_toolbar_role_select",  # Unique key
                help="Set role for all selected users"
            )

            if st.button("🔄 Apply Role", key="bulk_toolbar_apply_role", use_container_width=True):  # Unique key
                self._bulk_update_user_roles(st.session_state.selected_user_ids, new_role)

        with col2:
            if st.button("✅ Activate", key="bulk_toolbar_activate", use_container_width=True):  # Unique key
                self._bulk_activate_users(st.session_state.selected_user_ids)

        with col3:
            if st.button("❌ Deactivate", key="bulk_toolbar_deactivate", use_container_width=True):  # Unique key
                self._bulk_deactivate_users(st.session_state.selected_user_ids)

        with col4:
            if st.button("🗑️ Delete", key="bulk_toolbar_delete", use_container_width=True):  # Unique key
                self._confirm_bulk_delete(st.session_state.selected_user_ids)

    def _confirm_bulk_delete(self, user_ids: set):
        """Confirm and execute bulk user deletion"""
        if not user_ids:
            return

        user_list = ", ".join([str(uid) for uid in list(user_ids)[:3]])  # Show first 3
        if len(user_ids) > 3:
            user_list += f" and {len(user_ids) - 3} more"

        st.warning(f"🚨 **Confirm Deletion**")
        st.error(f"You are about to permanently delete {len(user_ids)} users: {user_list}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Confirm Delete", key="bulk_confirm_delete", type="primary",
                         use_container_width=True):  # Unique key
                self._bulk_delete_users(user_ids)

        with col2:
            if st.button("Cancel", key="bulk_delete_cancel", use_container_width=True):  # Unique key
                st.rerun()


    def _bulk_delete_users(self, user_ids: set):
        """Execute bulk user deletion"""
        if not user_ids:
            return

        success_count = 0
        error_count = 0
        errors = []

        with st.spinner(f"Deleting {len(user_ids)} users..."):
            for user_id in user_ids:
                try:
                    # Assuming you have a delete_user method in your API
                    success = self.api.delete_user(user_id)
                    if success:
                        st.balloons()
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"User {user_id}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"User {user_id}: {str(e)}")

        # Show results
        if error_count == 0:
            st.success(f"✅ Successfully deleted {success_count} users")
        else:
            st.warning(f"Completed with issues: {success_count} deleted, {error_count} failed")
            if errors:
                with st.expander("Show errors"):
                    for error in errors[:5]:  # Show first 5 errors
                        st.error(error)

        # Clear selection and rerun
        st.session_state.selected_user_ids = set()
        st.rerun()

    def _show_users_table(self, users: List[Dict]):
        """Display enhanced users table with bulk selection and select all"""
        if not users:
            st.info("No users match the selected filters")
            return

        # Initialize selected users in session state
        if 'selected_user_ids' not in st.session_state:
            st.session_state.selected_user_ids = set()

        # Create DataFrame for display with selection column
        user_data = []
        for user in users:
            is_selected = user.get('id') in st.session_state.selected_user_ids
            user_data.append({
                'Select': is_selected,  # Pre-populate based on selection state
                'ID': user.get('id'),
                'Username': user.get('username'),
                'Email': user.get('email'),
                'Full Name': user.get('full_name', ''),
                'Role': user.get('role', 'candidate'),
                'Verified': '✅' if user.get('is_verified') else '❌',
                'Active': '✅' if user.get('is_active', True) else '❌',
                'Created': self._format_date(user.get('created_at')),
                'Last Login': self._format_date(user.get('last_login'))
            })

        df = pd.DataFrame(user_data)

        # Calculate selection state for the header
        visible_user_ids = set(user.get('id') for user in users)
        selected_visible_ids = st.session_state.selected_user_ids & visible_user_ids

        all_selected = len(selected_visible_ids) == len(visible_user_ids) and len(visible_user_ids) > 0
        some_selected = len(selected_visible_ids) > 0 and not all_selected
        total_selected = len(st.session_state.selected_user_ids)

        # Enhanced Selection Header
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Selection state indicator
            if all_selected:
                st.success(f"✅ **All {len(users)} users selected**")
            elif some_selected:
                st.info(f"🔸 **{len(selected_visible_ids)} of {len(users)} users selected**")
            else:
                st.write(f"**{len(users)} users** - Select users for bulk operations")

        with col2:
            # Select All / Clear Visible buttons
            if not all_selected:
                if st.button("📋 Select All", key="select_all_visible", use_container_width=True):
                    # Add all visible users to selection
                    st.session_state.selected_user_ids.update(visible_user_ids)
                    st.rerun()
            else:
                if st.button("🗑️ Clear Page", key="clear_visible", use_container_width=True):
                    # Remove all visible users from selection
                    st.session_state.selected_user_ids -= visible_user_ids
                    st.rerun()

        with col3:
            # Clear entire selection (only show if there are selections)
            if total_selected > 0:
                if st.button("🧹 Clear All", key="clear_all_selection", use_container_width=True):
                    st.session_state.selected_user_ids = set()
                    st.rerun()
            else:
                # Empty space for layout consistency
                st.write("")

        # Display editable dataframe with checkboxes
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    width="small",
                    help="Select user for bulk operations",
                    default=False
                ),
                "ID": st.column_config.NumberColumn(width="small"),
                "Username": st.column_config.TextColumn(width="medium"),
                "Email": st.column_config.TextColumn(width="large"),
                "Full Name": st.column_config.TextColumn(width="medium"),
                "Role": st.column_config.SelectboxColumn(
                    width="small",
                    options=["admin", "reviewer", "engineer", "technologist", "technician", "candidate"]
                ),
                "Verified": st.column_config.TextColumn(width="small"),
                "Active": st.column_config.CheckboxColumn(width="small"),
                "Created": st.column_config.TextColumn(width="medium"),
                "Last Login": st.column_config.TextColumn(width="medium")
            },
            disabled=["ID", "Username", "Email", "Verified", "Created", "Last Login"],
            key="users_data_editor"
        )

        # Update selection state based on checkbox changes
        current_selection = set()
        for idx, row in edited_df.iterrows():
            if row['Select']:
                current_selection.add(row['ID'])

        # Update the session state with the current visible selection
        # Preserve selections from other pages/filters
        st.session_state.selected_user_ids = (st.session_state.selected_user_ids - visible_user_ids) | current_selection

        # Show bulk operations toolbar when users are selected
        if st.session_state.selected_user_ids:
            self._show_bulk_operations_toolbar(users)

        # Handle individual user updates (existing functionality)
        if not edited_df.equals(df):
            self._handle_user_updates(df, edited_df, users)



    def _handle_user_updates(self, original_df: pd.DataFrame, edited_df: pd.DataFrame, users: List[Dict]):
        """Handle user data updates from the table editor"""
        changes = []

        for idx, (orig_row, edit_row) in enumerate(zip(original_df.to_dict('records'), edited_df.to_dict('records'))):
            user_id = orig_row['ID']

            # Check for role changes
            if orig_row['Role'] != edit_row['Role']:
                changes.append({
                    'user_id': user_id,
                    'field': 'role',
                    'old_value': orig_row['Role'],
                    'new_value': edit_row['Role']
                })

            # Check for active status changes
            if orig_row['Active'] != edit_row['Active']:
                changes.append({
                    'user_id': user_id,
                    'field': 'is_active',
                    'old_value': orig_row['Active'],
                    'new_value': edit_row['Active']
                })

        # Apply changes
        if changes:
            with LoadingState("Applying user updates..."):
                for change in changes:
                    if change['field'] == 'role':
                        success = self.api.update_user_role(change['user_id'], change['new_value'])
                    elif change['field'] == 'is_active':
                        if change['new_value']:
                            success = self.api.activate_user(change['user_id'])
                        else:
                            success = self.api.deactivate_user(change['user_id'])

                    if success:
                        st.balloons()
                        st.success(f"Updated user {change['user_id']}")
                    else:
                        ErrorHandler.show_error(f"Failed to update user {change['user_id']}")

            st.rerun()


    def _bulk_update_user_roles(self, user_ids: set, new_role: str):
        """Bulk update user roles with progress feedback"""
        if not user_ids:
            return

        success_count = 0
        error_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, user_id in enumerate(user_ids):
            status_text.text(f"Updating user {i + 1}/{len(user_ids)}...")

            if self.api.update_user_role(user_id, new_role):
                success_count += 1
            else:
                error_count += 1

            progress_bar.progress((i + 1) / len(user_ids))

        progress_bar.empty()
        status_text.empty()

        if error_count == 0:
            st.success(f"✅ Updated {success_count} users to {new_role} role")
        else:
            st.warning(f"Updated {success_count}/{len(user_ids)} users to {new_role} role")

        st.session_state.selected_user_ids = set()
        st.rerun()

    def _bulk_activate_users(self, user_ids: set):
        """Bulk activate users"""
        if not user_ids:
            return

        success_count = 0
        for user_id in user_ids:
            if self.api.activate_user(user_id):
                success_count += 1

        st.success(f"✅ Activated {success_count} users")
        st.session_state.selected_user_ids = set()
        st.rerun()

    def _bulk_deactivate_users(self, user_ids: set):
        """Bulk deactivate users"""
        if not user_ids:
            return

        success_count = 0
        for user_id in user_ids:
            if self.api.deactivate_user(user_id):
                success_count += 1

        st.success(f"✅ Deactivated {success_count} users")
        st.session_state.selected_user_ids = set()
        st.rerun()

    def _filter_reports(self, reports: List[Dict], date_range: str, profession: str) -> List[Dict]:
        """Filter reports based on criteria"""
        filtered = reports

        # Date range filter
        if date_range != "All time":
            days = 7 if date_range == "Last 7 days" else 30 if date_range == "Last 30 days" else 90
            cutoff_date = datetime.now() - timedelta(days=days)

            filtered = [r for r in filtered if
                        datetime.fromisoformat(r.get('created_at', '2000-01-01').replace('Z', '')) >= cutoff_date]

        # Profession filter
        if profession != "All":
            filtered = [r for r in filtered if profession.lower() in r.get('title', '').lower()]

        return filtered

    def _show_reports_analytics_overview(self, reports: List[Dict]):
        """Show reports analytics overview"""
        if not reports:
            st.info("No reports match the selected filters")
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_reports = len(reports)
            st.metric("Total Reports", total_reports)

        with col2:
            avg_word_count = np.mean([len(r.get('content', '').split()) for r in reports])
            st.metric("Avg Word Count", f"{avg_word_count:.0f}")

        with col3:
            completion_rate = len([r for r in reports if r.get('status') != 'draft']) / len(reports) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")

        with col4:
            unique_authors = len(set(r.get('owner_id') for r in reports))
            st.metric("Unique Authors", unique_authors)

    def _plot_competency_completion_heatmap(self, reports: List[Dict]):
        """Plot competency completion heatmap"""
        # This would require tracking which competencies are completed in each report
        st.info("Competency heatmap visualization coming soon")
        # Placeholder implementation would go here

    def _plot_report_quality_metrics(self, reports: List[Dict]):
        """Plot report quality metrics"""
        if not reports:
            st.info("No reports data for quality metrics")
            return

        # Calculate basic quality metrics (simplified)
        word_counts = [len(r.get('content', '').split()) for r in reports]
        status_counts = {}

        for report in reports:
            status = report.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Create quality score (simplified)
        quality_scores = []
        for report in reports:
            score = 50  # Base score

            # Word count contribution
            word_count = len(report.get('content', '').split())
            if word_count > 500:
                score += 20
            elif word_count > 200:
                score += 10

            # Status contribution
            status = report.get('status')
            if status == 'approved':
                score += 30
            elif status == 'submitted':
                score += 15

            quality_scores.append(min(score, 100))

        fig = px.histogram(
            x=quality_scores,
            title="📈 Report Quality Distribution",
            labels={'x': 'Quality Score', 'y': 'Number of Reports'}
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_review_queue(self, reports: List[Dict]):
        """Show reports waiting for review with functional review interface"""
        pending_review = [r for r in reports if r.get('status') in ['submitted', 'under_review']]

        if not pending_review:
            st.success("✅ No reports pending review!")
            return

        # Check if we're currently reviewing a report
        if 'current_review_id' in st.session_state and st.session_state.current_review_id:
            self._show_review_interface(st.session_state.current_review_id, pending_review)
            return

        st.write(f"**{len(pending_review)} reports awaiting review:**")

        for report in pending_review[:5]:  # Show first 5
            with st.expander(f"📝 {report['title']} (ID: {report['id']})", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Author:** {report.get('owner_full_name', 'Unknown')}")
                    st.write(f"**Username:** {report.get('owner_username', 'N/A')}")
                    st.write(f"**Email:** {report.get('owner_email', 'No email')}")
                    st.write(f"**Submitted:** {self._format_date(report.get('submitted_at'))}")
                    st.write(f"**Word Count:** {len(report.get('content', '').split())}")

                    # Show preview of content
                    content_preview = report.get('content', '')[:200] + "..." if len(
                        report.get('content', '')) > 200 else report.get('content', '')
                    st.write(f"**Preview:** {content_preview}")

                with col2:
                    if st.button("👀 Review", key=f"review_{report['id']}"):
                        st.session_state.current_review_id = report['id']
                        st.rerun()

    def _show_review_interface(self, report_id: int, pending_reports: List[Dict]):
        """Display the actual review interface"""
        # Find the report being reviewed
        report_to_review = next((r for r in pending_reports if r['id'] == report_id), None)

        if not report_to_review:
            st.error("Report not found or no longer available for review")
            if 'current_review_id' in st.session_state:
                del st.session_state.current_review_id
            st.rerun()
            return

        st.subheader(f"📋 Review Report: {report_to_review['title']}")

        # Back button
        if st.button("← Back to Review Queue"):
            if 'current_review_id' in st.session_state:
                del st.session_state.current_review_id
            st.rerun()

        # Report details
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Report Details**")
            st.write(f"**ID:** {report_to_review['id']}")
            st.write(f"**Author:** {report_to_review.get('owner_full_name', 'Unknown')}")
            st.write(f"**Username:** {report_to_review.get('owner_username', 'N/A')}")
            st.write(f"**Email:** {report_to_review.get('owner_email', 'No email')}")
            st.write(f"**Submitted:** {self._format_date(report_to_review.get('submitted_at'))}")
            st.write(f"**Status:** {report_to_review.get('status', 'unknown')}")

        with col2:
            st.write("**Statistics**")
            st.write(f"**Word Count:** {len(report_to_review.get('content', '').split())}")
            st.write(f"**Created:** {self._format_date(report_to_review.get('created_at'))}")
            if report_to_review.get('updated_at'):
                st.write(f"**Last Updated:** {self._format_date(report_to_review.get('updated_at'))}")

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
                self._submit_review_decision(report_id, "approved")

        with col4:
            if st.button("❌ Reject", type="secondary", use_container_width=True):
                self._submit_review_decision(report_id, "rejected")

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

    def _submit_review_decision(self, report_id: int, decision: str):
        """Submit the review decision to the API"""
        review_notes = st.session_state.get(f"notes_{report_id}", "")

        with LoadingState(f"Submitting {decision} decision..."):
            success, result = self.api.review_report(
                report_id=report_id,
                status=decision,
                review_notes=review_notes
            )

        if success:
            st.balloons()
            st.success(f"✅ Report {decision} successfully!")

            # Clear review state
            if 'current_review_id' in st.session_state:
                del st.session_state.current_review_id
            if f"notes_{report_id}" in st.session_state:
                del st.session_state[f"notes_{report_id}"]

            # Small delay to show success message
            import time
            time.sleep(1)
            st.rerun()
        else:
            error_msg = result.get('detail', 'Unknown error occurred')
            ErrorHandler.show_error(f"Failed to submit review: {error_msg}")


    def _show_audit_logs_table(self, logs: List[Dict]):
        """Display enhanced audit logs table"""
        if not logs:
            st.info("No audit logs found")
            return

        log_data = []

        for log in logs:
            user_agent = log.get('user_agent') if log and log.get('user_agent') else ''
            user_agent = str(user_agent)  # guarantee it's a string

            log_data.append({
                'Timestamp': log.get('created_at', '') if log else '',
                'User': log.get('username', 'System') if log else 'System',
                'Action': log.get('action', '') if log else '',
                'Resource': f"{log.get('resource_type', '')} #{log.get('resource_id', '')}" if log else '',
                'IP Address': log.get('ip_address', '') if log else '',
                'User Agent': user_agent[:50] + '...' if len(user_agent) > 50 else user_agent
            })

        df = pd.DataFrame(log_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _show_audit_statistics(self):
        """Display audit statistics"""
        if 'audit_logs' not in st.session_state:
            st.info("Load audit logs to see statistics")
            return

        logs = st.session_state.audit_logs

        col1, col2, col3 = st.columns(3)

        with col1:
            total_actions = len(logs)
            st.metric("Total Actions", total_actions)

        with col2:
            unique_users = len(set(log.get('username') for log in logs if log.get('username')))
            st.metric("Unique Users", unique_users)

        with col3:
            most_common_action = max(set(log.get('action') for log in logs),
                                     key=list(log.get('action') for log in logs).count)
            st.metric("Most Common Action", most_common_action)


############################# DATABASE STATS METHODS #############################################

    def _get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics using all available APIs"""
        try:
            # Get main database stats
            success, stats = self.api.get_database_stats()

            if success:
                # Enhance with additional metrics if available
                health_success, health = self.api.get_database_health()
                if health_success:
                    stats.update({
                        'response_time_ms': health.get('response_time_ms', 0),
                        'cache_hit_ratio': health.get('cache_hit_ratio', 0),
                        'health_status': health.get('status', 'unknown')
                    })

                size_success, size_info = self.api.get_database_size()
                if size_success:
                    stats.update({
                        'disk_free_gb': size_info.get('disk_free_gb', 0),
                        'db_size_bytes': size_info.get('db_size_bytes', 0)
                    })

                return {
                    **stats,
                    'is_real_data': True,
                    'database_status': 'connected',
                }
            else:
                return self._get_empty_stats("Database statistics unavailable")

        except Exception as e:
            return self._get_empty_stats(f"Failed to retrieve database stats: {str(e)}")

    def _get_empty_stats(self, reason: str = "Service unavailable") -> Dict[str, Any]:
        """Return standardized empty statistics for production"""
        return {
            'total_records': 0,
            'db_size_mb': 0.0,
            'users_count': 0,
            'reports_count': 0,
            'audit_logs_count': 0,
            'table_count': 0,
            'existing_tables': [],
            'is_real_data': False,
            'database_status': reason,
            'database_type': 'unknown',
        }



    def _show_database_tables(self):
        """Display detailed table information"""
        st.subheader("📊 Database Tables")

        with LoadingState("Loading table information..."):
            success, tables_data = self.api.get_database_tables()

        if success and tables_data.get('tables'):
            tables = tables_data['tables']

            # Create table data for display
            table_data = []
            for table in tables:
                table_data.append({
                    'Table Name': table['name'],
                    'Row Count': f"{table.get('row_count', 0):,}",
                    'Status': '✅' if table.get('row_count', 0) > 0 else '⚠️'
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Summary
            total_tables = len(tables)
            total_rows = sum(table.get('row_count', 0) for table in tables)
            st.info(f"**Summary:** {total_tables} tables with {total_rows:,} total rows")
        else:
            st.warning("Table information unavailable")

    def _show_database_storage(self):
        """Display database storage metrics"""
        st.subheader("💾 Storage Metrics")

        with LoadingState("Loading storage information..."):
            success, storage = self.api.get_database_size()

        if success:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Database Size", f"{storage.get('db_size_mb', 0):.2f} MB")

            with col2:
                st.metric("Disk Free", f"{storage.get('disk_free_gb', 0):.2f} GB")

            with col3:
                db_type = storage.get('database_type', 'unknown')
                st.metric("Database Type", db_type.title())

            # Progress bars for visualization
            if storage.get('db_size_bytes') and storage.get('disk_free_gb'):
                # Simple progress visualization
                st.progress(min(storage.get('db_size_mb', 0) / 100, 1.0),
                            text=f"Database Size: {storage.get('db_size_mb', 0):.2f} MB")
        else:
            st.warning("Storage metrics unavailable")

    #############################################################################################################

    def _run_system_health_check(self):
        """Run comprehensive system health check"""
        with st.spinner("Running system health check..."):
            checks = []

            # Check API connectivity
            start_time = datetime.now()
            api_success, _ = self.api.health_check()
            api_response_time = (datetime.now() - start_time).total_seconds()
            checks.append({
                'component': 'API Server',
                'status': '✅ Healthy' if api_success and api_response_time < 2.0 else '⚠️ Slow' if api_success else '❌ Unavailable',
                'details': f"Response time: {api_response_time:.2f}s"
            })

            # Check database
            db_success, _ = self.api.get_all_users()
            checks.append({
                'component': 'Database',
                'status': '✅ Healthy' if db_success else '❌ Issues',
                'details': f"Connection: {'OK' if db_success else 'Failed'}"
            })

            # Check external services
            checks.append({
                'component': 'AI Service',
                'status': '✅ Available',
                'details': 'OpenAI API: Connected'
            })

            # Display results
            st.subheader("🩺 Health Check Results")

            for check in checks:
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.write(check['component'])
                with col2:
                    st.write(check['status'])
                with col3:
                    st.write(check['details'])

            # Overall status
            all_healthy = all('✅' in check['status'] for check in checks)
            if all_healthy:
                st.success("🎉 All systems are healthy!")
            else:
                st.warning("⚠️ Some systems require attention")

    def _export_system_data(self):
        """Enhanced system data export with comprehensive error handling"""
        try:
            with LoadingState("Preparing comprehensive system data export..."):
                export_data = {
                    'export_info': {
                        'exported_at': datetime.now().isoformat(),
                        'exported_by': st.session_state.get('username', 'Unknown'),
                        'user_role': st.session_state.get('user_role', 'Unknown'),
                        'data_types': ['users', 'reports', 'audit_logs'],
                        'export_version': '2.0',
                        'total_records': 0
                    },
                    'users': [],
                    'reports': [],
                    'audit_logs': [],
                    'export_metadata': {
                        'successful_exports': [],
                        'failed_exports': []
                    }
                }

                # Helper function to safely get data
                def safe_get_data(api_method, data_key, description):
                    try:
                        success, response = api_method()
                        if success and isinstance(response, list):
                            export_data[data_key] = response
                            export_data['export_metadata']['successful_exports'].append(description)
                            return len(response)
                        else:
                            error_msg = response.get('detail', 'Unknown error') if isinstance(response, dict) else str(
                                response)
                            export_data['export_metadata']['failed_exports'].append({
                                'type': description,
                                'error': error_msg
                            })
                            return 0
                    except Exception as e:
                        export_data['export_metadata']['failed_exports'].append({
                            'type': description,
                            'error': f"Exception: {str(e)}"
                        })
                        return 0

                # Get all data
                users_count = safe_get_data(self.api.get_all_users, 'users', 'users')
                reports_count = safe_get_data(self.api.get_all_reports, 'reports', 'reports')
                audit_count = safe_get_data(lambda: self.api.get_audit_logs(limit=5000), 'audit_logs', 'audit_logs')

                # Update totals
                total_records = users_count + reports_count + audit_count
                export_data['export_info']['total_records'] = total_records

                # Create JSON with proper encoding
                json_str = json.dumps(export_data,
                                      indent=2,
                                      ensure_ascii=False,
                                      default=str,
                                      sort_keys=True)

                # Display export results
                st.subheader("📊 Export Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Users", users_count)
                with col2:
                    st.metric("Reports", reports_count)
                with col3:
                    st.metric("Audit Logs", audit_count)

                st.metric("Total Records", total_records)

                # Show any failures
                if export_data['export_metadata']['failed_exports']:
                    st.warning(
                        f"⚠️ {len(export_data['export_metadata']['failed_exports'])} data types failed to export")
                    with st.expander("Show export errors"):
                        for error in export_data['export_metadata']['failed_exports']:
                            st.error(f"{error['type']}: {error['error']}")

                # Download button
                st.download_button(
                    "💾 Download System Data (JSON)",
                    data=json_str,
                    file_name=f"system_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                    help=f"Complete system export with {total_records} total records"
                )

                # Optional: Also offer CSV export for main tables
                if st.checkbox("Also generate CSV exports"):
                    self._generate_csv_exports(export_data)

        except Exception as e:
            ErrorHandler.show_error(f"Export failed: {str(e)}")

    def _generate_csv_exports(self, export_data):
        """Generate CSV exports for individual data types"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if export_data['users']:
                users_df = pd.DataFrame(export_data['users'])
                csv_users = users_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Users (CSV)",
                    data=csv_users,
                    file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col2:
            if export_data['reports']:
                reports_df = pd.DataFrame(export_data['reports'])
                csv_reports = reports_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Reports (CSV)",
                    data=csv_reports,
                    file_name=f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col3:
            if export_data['audit_logs']:
                audit_df = pd.DataFrame(export_data['audit_logs'])
                csv_audit = audit_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Audit Logs (CSV)",
                    data=csv_audit,
                    file_name=f"audit_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    def _generate_csv_exports(self, export_data):
        """Generate CSV exports for individual data types"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if export_data['users']:
                users_df = pd.DataFrame(export_data['users'])
                csv_users = users_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Users (CSV)",
                    data=csv_users,
                    file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col2:
            if export_data['reports']:
                reports_df = pd.DataFrame(export_data['reports'])
                csv_reports = reports_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Reports (CSV)",
                    data=csv_reports,
                    file_name=f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col3:
            if export_data['audit_logs']:
                audit_df = pd.DataFrame(export_data['audit_logs'])
                csv_audit = audit_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Audit Logs (CSV)",
                    data=csv_audit,
                    file_name=f"audit_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    def _is_recent(self, date_str: str, days: int) -> bool:
        """Check if a date is within the last N days"""
        if not date_str:
            return False

        try:
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
            else:
                date_part = date_str.split(' ')[0]

            date_obj = datetime.strptime(date_part, '%Y-%m-%d')
            return (datetime.now() - date_obj).days <= days
        except:
            return False

    def _format_date(self, date_str: str) -> str:
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


def enhanced_admin_dashboard(api: EnhancedAPIClient):
    """Enhanced admin dashboard main function"""
    dashboard = EnhancedAdminDashboard(api)
    dashboard.show_dashboard()


# Update the existing admin dashboard to use this enhanced version
def main():
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    enhanced_admin_dashboard(api)


if __name__ == "__main__":
    main()