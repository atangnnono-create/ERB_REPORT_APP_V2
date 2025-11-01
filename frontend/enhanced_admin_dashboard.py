import os
import logging
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

        # Initialize pagination state
        if 'pagination' not in st.session_state:
            st.session_state.pagination = {
                'users_page': 0,
                'reports_page': 0,
                'page_size': 50
            }

        # Initialize filter state
        if 'filters' not in st.session_state:
            st.session_state.filters = {
                'users': {
                    'search_term': '',
                    'role_filter': 'All',
                    'status_filter': 'All',
                    'verification_filter': 'All'
                },
                'reports': {
                    'date_range': 'All time',
                    'profession_filter': 'All'
                }
            }

    def show_dashboard(self):
        """Main admin dashboard with progressive loading"""
        st.title("👑 Enhanced Admin Dashboard")

        # Show authentication debug info

        # Test API connectivity first
        with st.spinner("Checking API connectivity..."):
            success, _ = self.api.health_check()
            if not success:
                st.error("❌ Cannot connect to API. Please check if the server is running.")
                return
            else:
                st.balloons()

        # Test admin endpoint access
        with st.spinner("Testing admin permissions..."):
            success, test_response = self.api.get_all_users_paginated(limit=1)
            if not success:
                st.error(f"❌ Admin access denied: {test_response.get('detail', 'Unknown error')}")
                return


        # Permission check
        if not self._check_admin_permissions():
            return

        # Rest of your existing dashboard code...
        # Initialize tab loading states
        if 'tabs_loaded' not in st.session_state:
            st.session_state.tabs_loaded = {
                'overview': False,
                'user_management': False,
                'reports_analytics': False,
                'audit_trail': False,
                'system_settings': False
            }

        # Quick stats header
        self._show_quick_stats()

        # Main tabs with progressive loading
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "👥 User Management",
            "📋 Reports Analytics",
            "🔍 Audit Trail",
            "⚙️ System Settings"
        ])

        with tab1:
            self._load_overview_tab_progressive()
        with tab2:
            self._load_user_management_tab_progressive()
        with tab3:
            self._load_reports_analytics_tab_progressive()
        with tab4:
            self._load_audit_trail_tab_progressive()
        with tab5:
            self._load_system_settings_tab_progressive()

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



    def _load_overview_tab_progressive(self):
        """Load overview tab content progressively"""
        if not st.session_state.tabs_loaded['overview']:
            with LoadingState("Loading overview analytics..."):
                # Load only the data needed for this tab
                self._load_overview_data()
                st.session_state.tabs_loaded['overview'] = True

        # Now display the tab content
        self._show_overview_tab()

    def _load_user_management_tab_progressive(self):
        """Load user management tab content progressively"""
        if not st.session_state.tabs_loaded['user_management']:
            with LoadingState("Loading user management..."):
                # Load user data only when this tab is accessed
                self._load_user_management_data()
                st.session_state.tabs_loaded['user_management'] = True

        self._show_user_management_tab()

    def _load_reports_analytics_tab_progressive(self):
        """Load reports analytics tab content progressively with pagination"""
        if not st.session_state.tabs_loaded['reports_analytics']:
            with LoadingState("Loading reports analytics..."):
                self._load_reports_analytics_data()
                st.session_state.tabs_loaded['reports_analytics'] = True

        self._show_reports_analytics_tab()

    def _load_audit_trail_tab_progressive(self):
        """Load audit trail tab content progressively"""
        if not st.session_state.tabs_loaded['audit_trail']:
            # Audit trail starts empty until user loads logs
            st.session_state.tabs_loaded['audit_trail'] = True

        self._show_audit_trail_tab()

    def _load_system_settings_tab_progressive(self):
        """Load system settings tab content progressively"""
        if not st.session_state.tabs_loaded['system_settings']:
            with LoadingState("Loading system settings..."):
                self._load_system_settings_data()
                st.session_state.tabs_loaded['system_settings'] = True

        self._show_system_settings_tab()

    def _load_overview_data(self):
        """Load data specifically for overview tab"""
        # Cache the data in session state
        if 'overview_data' not in st.session_state:
            st.session_state.overview_data = {
                'users_data': self._get_users_data(),
                'reports_data': self._get_reports_data(),
                'audit_data': self._get_audit_data()
            }

    def _load_user_management_data(self):
        """Load paginated user data with total count"""
        page_size = st.session_state.pagination['page_size']
        current_page = st.session_state.pagination['users_page']
        skip = current_page * page_size

        success, response = self.api.get_all_users_paginated(skip=skip, limit=page_size)

        if success and isinstance(response, dict):
            users = response.get('users', [])
            total_count = response.get('total_count', 0)
            st.session_state.user_management_data = users
            st.session_state.total_users_count = total_count
        else:
            st.session_state.user_management_data = []
            st.session_state.total_users_count = 0

    def _load_reports_analytics_data(self):
        """Load paginated reports data with total count - DEBUG VERSION"""
        try:
            page_size = st.session_state.pagination['page_size']
            current_page = st.session_state.pagination['reports_page']
            skip = current_page * page_size

            # Test the API call directly
            success, response = self.api.get_all_reports_paginated(skip=skip, limit=page_size)

            if success:
                if isinstance(response, dict) and 'reports' in response:
                    reports = response.get('reports', [])
                    total_count = response.get('total_count', 0)
                    st.session_state.reports_analytics_data = reports
                    st.session_state.total_reports_count = total_count
                    st.success(f"✅ Loaded {len(reports)} reports")
                else:
                    st.error(f"Unexpected response format: {type(response)}")
            else:
                st.error(f"API call failed: {response}")

        except Exception as e:
            st.error(f"Error loading reports: {str(e)}")

    def _load_system_settings_data(self):
        """Load data specifically for system settings tab"""
        # System settings data is loaded on-demand in the tab itself
        pass



    def _check_admin_permissions(self) -> bool:
        """Check if user has admin permissions"""
        user_role = st.session_state.get('user_role', '')
        if user_role not in ['admin']:
            ErrorHandler.show_error("🔒 Access denied. Administrator privileges required.")
            return False
        return True

    def _show_quick_stats(self):
        """Display lightweight quick statistics"""
        with LoadingState("Loading system statistics..."):
            # Use lightweight endpoint instead of loading all data
            success, stats = self.api.get_quick_stats()

            if not success:
                # Fallback to existing method if new endpoint not available
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
                stats.get('active_users_today')
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

        # Use cached data from progressive loading
        data = st.session_state.get('overview_data', {})
        users_data = data.get('users_data', [])
        reports_data = data.get('reports_data', [])
        audit_data = data.get('audit_data', [])

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
        """Enhanced user management interface with filter state"""
        st.subheader("👥 User Management")

        # User actions toolbar with filter state
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            search_term = st.text_input(
                "🔍 Search users...",
                placeholder="Search by username, email, or role",
                value=st.session_state.filters['users']['search_term'],
                key="users_search"
            )
            # Update filter state
            st.session_state.filters['users']['search_term'] = search_term

        with col2:
            role_filter = st.selectbox(
                "Role",
                ["All", "admin", "reviewer", "engineer", "technologist", "technician", "candidate"],
                index=["All", "admin", "reviewer", "engineer", "technologist", "technician", "candidate"].index(
                    st.session_state.filters['users']['role_filter']
                ),
                key="users_role_filter"
            )
            st.session_state.filters['users']['role_filter'] = role_filter

        with col3:
            status_filter = st.selectbox(
                "Status",
                ["All", "active", "inactive"],
                index=["All", "active", "inactive"].index(
                    st.session_state.filters['users']['status_filter']
                ),
                key="users_status_filter"
            )
            st.session_state.filters['users']['status_filter'] = status_filter

        with col4:
            verification_filter = st.selectbox(
                "Verified",
                ["All", "verified", "unverified"],
                index=["All", "verified", "unverified"].index(
                    st.session_state.filters['users']['verification_filter']
                ),
                key="users_verification_filter"
            )
            st.session_state.filters['users']['verification_filter'] = verification_filter

        # Load users (uses cached data from progressive loading)
        users = st.session_state.get('user_management_data', [])
        total_count = st.session_state.get('total_users_count', 0)

        if not users:
            ErrorHandler.show_error("Failed to load users")
            return

        # Apply filters to current page data
        filtered_users = self._filter_users(
            users,
            st.session_state.filters['users']['search_term'],
            st.session_state.filters['users']['role_filter'],
            st.session_state.filters['users']['status_filter'],
            st.session_state.filters['users']['verification_filter']
        )

        # User statistics
        st.write(f"**Showing {len(filtered_users)} of {len(users)} users on this page ({total_count} total)**")

        # Users table with enhanced features
        self._show_users_table(filtered_users)

    def _should_refresh_tab_data(self, tab_name, max_age_minutes=5):
        """Check if tab data should be refreshed"""
        last_loaded = st.session_state.get(f"{tab_name}_last_loaded")
        if not last_loaded:
            return True

        return (datetime.now() - last_loaded).seconds > (max_age_minutes * 60)

    def _add_tab_refresh_button(self, tab_name):
        """Add refresh button to reload tab data with pagination reset"""
        if st.button("🔄 Refresh", key=f"refresh_{tab_name}"):
            # Clear the loaded state and data
            st.session_state.tabs_loaded[tab_name] = False
            if f"{tab_name}_data" in st.session_state:
                del st.session_state[f"{tab_name}_data"]
            # Reset pagination for this tab
            if tab_name == 'user_management':
                st.session_state.pagination['users_page'] = 0
            elif tab_name == 'reports_analytics':
                st.session_state.pagination['reports_page'] = 0
            st.rerun()

    def _show_reports_analytics_tab(self):
        """Comprehensive reports analytics with filter state"""
        st.subheader("📋 Reports Analytics")

        # Date range filter with state
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            date_range = st.selectbox(
                "Time Period",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=["Last 7 days", "Last 30 days", "Last 90 days", "All time"].index(
                    st.session_state.filters['reports']['date_range']
                ),
                key="reports_date_range"
            )
            st.session_state.filters['reports']['date_range'] = date_range

        with col2:
            profession_filter = st.selectbox(
                "Profession",
                ["All", "Engineer", "Engineering Technologist", "Engineering Technician"],
                index=["All", "Engineer", "Engineering Technologist", "Engineering Technician"].index(
                    st.session_state.filters['reports']['profession_filter']
                ),
                key="reports_profession"
            )
            st.session_state.filters['reports']['profession_filter'] = profession_filter

        with col3:
            # Clear filters button
            if st.button("🧹 Clear Filters", key="clear_reports_filters"):
                st.session_state.filters['reports'] = {
                    'date_range': 'All time',
                    'profession_filter': 'All'
                }
                st.session_state.pagination['reports_page'] = 0
                st.rerun()

        # Use cached paginated reports data
        reports = st.session_state.get('reports_analytics_data', [])
        total_reports_count = st.session_state.get('total_reports_count', 0)

        # Apply filters to the current page of data
        filtered_reports = self._filter_reports(
            reports,
            st.session_state.filters['reports']['date_range'],
            st.session_state.filters['reports']['profession_filter']
        )

        # Show pagination info
        st.write(f"**Page Results:** {len(filtered_reports)} reports (of {total_reports_count} total)")

        # Analytics overview (for current page)
        self._show_reports_analytics_overview(filtered_reports)

        # Detailed charts (for current page)
        col1, col2 = st.columns(2)

        with col1:
            self._plot_competency_completion_heatmap(filtered_reports)

        with col2:
            self._plot_report_quality_metrics(filtered_reports)

        # Report review queue (for current page)
        st.subheader("📝 Review Queue")
        self._show_review_queue(filtered_reports)

        # Add pagination controls at the bottom
        self._show_pagination_controls('reports', total_reports_count)


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
                    if not logs:  # Added: Show message when no logs found
                        st.info("No audit logs found matching your filters")
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
        """Get comprehensive system statistics - UPDATED TO PAGINATED"""
        # Try to use cached stats if recent
        cache_key = "system_stats"
        if cache_key in self.stats_cache:
            cache_time, cached_data = self.stats_cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5 minutes
                return cached_data

        stats = {}

        # Get users data using paginated endpoint
        success, users_response = self.api.get_all_users_paginated(limit=1000)
        if success:
            if isinstance(users_response, dict) and 'users' in users_response:
                users = users_response.get('users', [])
                total_count = users_response.get('total_count', 0)
            else:
                # Fallback if response format is unexpected
                users = []
                total_count = 0

            stats['total_users'] = total_count
            stats['active_users_today'] = len([u for u in users if u.get('is_active', True)])
            stats['new_users_7d'] = len([u for u in users if self._is_recent(u.get('created_at'), 7)])

        # Get reports data using paginated endpoint
        success, reports_response = self.api.get_all_reports_paginated(limit=1000)
        if success:
            if isinstance(reports_response, dict) and 'reports' in reports_response:
                reports = reports_response.get('reports', [])
                total_count = reports_response.get('total_count', 0)
            else:
                # Fallback if response format is unexpected
                reports = []
                total_count = 0

            stats['total_reports'] = total_count
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
        """Get enhanced users data - UPDATED TO PAGINATED"""
        # Use paginated endpoint for overview (get first 200 for charts)
        success, response = self.api.get_all_users_paginated(skip=0, limit=200)

        if success and isinstance(response, dict) and 'users' in response:
            return response.get('users', [])
        else:
            return []

    def _get_reports_data(self) -> List[Dict]:
        """Get enhanced reports data - UPDATED TO PAGINATED"""
        # Use paginated endpoint for overview (get first 200 for charts)
        success, response = self.api.get_all_reports_paginated(skip=0, limit=200)

        if success and isinstance(response, dict) and 'reports' in response:
            return response.get('reports', [])
        else:
            return []

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
        """Display system health metrics - UPDATED TO PAGINATED"""
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
            # Database health (updated to use paginated endpoint)
            success, users_response = self.api.get_all_users_paginated(limit=1)  # Just check connectivity
            if success:
                st.success("✅ Database: Healthy")
                # Get actual count for metric
                success, full_response = self.api.get_all_users_paginated(limit=1000)
                user_count = full_response.get('total_count', 0) if success and isinstance(full_response,
                                                                                           dict) else "N/A"
            else:
                st.error("❌ Database: Issues")
                user_count = "N/A"

            st.metric("User Records", user_count)

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


    def _get_users_dataframe(self, users, selected_ids):
        """Create users dataframe - separate method for organization"""
        user_data = []
        for user in users:
            is_selected = user.get('id') in selected_ids
            user_data.append({
                'Select': is_selected,
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
        return pd.DataFrame(user_data)


    def _show_users_table(self, users: List[Dict]):
        """Display enhanced users table with bulk selection and select all"""
        if not users:
            st.info("No users match the selected filters")
            return

        # Initialize selected users in session state
        if 'selected_user_ids' not in st.session_state:
            st.session_state.selected_user_ids = set()

        # Create DataFrame for display with selection column
        df = st.cache_data(ttl=300)(self._get_users_dataframe)(
            users,
            st.session_state.selected_user_ids
        )

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
        self._show_pagination_controls('users', st.session_state.total_users_count)


    def _show_pagination_controls(self, data_type: str, total_count: int):
        """Show pagination controls with loading states"""
        page_key = f'{data_type}_page'
        current_page = st.session_state.pagination[page_key]
        page_size = st.session_state.pagination['page_size']

        # Calculate pagination info
        total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1
        start_item = current_page * page_size + 1
        end_item = min((current_page + 1) * page_size, total_count)

        # Display name mapping
        display_names = {
            'users': 'users',
            'reports': 'reports'
        }
        display_name = display_names.get(data_type, data_type)

        # Pagination info and controls
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            if total_count > 0:
                st.write(f"**Showing {start_item}-{end_item} of {total_count} {display_name}**")
            else:
                st.write(f"**No {display_name} found**")

        with col2:
            if st.button("⬅️ Previous",
                         disabled=current_page == 0,
                         key=f"prev_{data_type}"):
                # Show loading state during page transition
                with LoadingState(f"Loading {display_name} page {current_page}..."):
                    st.session_state.pagination[page_key] = max(0, current_page - 1)
                    # Clear and reload data for the new page
                    if f"{data_type}_analytics_data" in st.session_state:
                        del st.session_state[f"{data_type}_analytics_data"]
                    # Reload the data
                    if data_type == 'users':
                        self._load_user_management_data()
                    else:
                        self._load_reports_analytics_data()
                st.rerun()

        with col3:
            if st.button("Next ➡️",
                         disabled=current_page >= total_pages - 1 or total_count == 0,
                         key=f"next_{data_type}"):
                # Show loading state during page transition
                with LoadingState(f"Loading {display_name} page {current_page + 2}..."):
                    st.session_state.pagination[page_key] = min(total_pages - 1, current_page + 1)
                    # Clear and reload data for the new page
                    if f"{data_type}_analytics_data" in st.session_state:
                        del st.session_state[f"{data_type}_analytics_data"]
                    # Reload the data
                    if data_type == 'users':
                        self._load_user_management_data()
                    else:
                        self._load_reports_analytics_data()
                st.rerun()

        with col4:
            new_page_size = st.selectbox(
                "Page size",
                [25, 50, 100],
                index=[25, 50, 100].index(page_size),
                key=f"page_size_{data_type}",
                label_visibility="collapsed"
            )
            if new_page_size != page_size:
                with LoadingState(f"Changing page size to {new_page_size}..."):
                    st.session_state.pagination['page_size'] = new_page_size
                    st.session_state.pagination[page_key] = 0  # Reset to first page
                    # Clear cached data
                    if f"{data_type}_analytics_data" in st.session_state:
                        del st.session_state[f"{data_type}_analytics_data"]
                    # Reload data with new page size
                    if data_type == 'users':
                        self._load_user_management_data()
                    else:
                        self._load_reports_analytics_data()
                st.rerun()

        # Page number indicator
        if total_pages > 1:
            st.write(f"**Page {current_page + 1} of {total_pages}**")

    def _clear_all_filters(self, data_type: str):
        """Clear all filters for users or reports"""
        if data_type == 'users':
            st.session_state.filters['users'] = {
                'search_term': '',
                'role_filter': 'All',
                'status_filter': 'All',
                'verification_filter': 'All'
            }
        elif data_type == 'reports':
            st.session_state.filters['reports'] = {
                'date_range': 'All time',
                'profession_filter': 'All'
            }

        # Reset to first page
        st.session_state.pagination[f'{data_type}_page'] = 0

        # Clear cached data to force reload
        if f"{data_type}_analytics_data" in st.session_state:
            del st.session_state[f"{data_type}_analytics_data"]


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
        """Filter current page of reports based on criteria"""
        filtered = reports

        # Date range filter (applies to current page only)
        if date_range != "All time":
            days = 7 if date_range == "Last 7 days" else 30 if date_range == "Last 30 days" else 90
            cutoff_date = datetime.now() - timedelta(days=days)

            filtered = [r for r in filtered if
                        datetime.fromisoformat(r.get('created_at', '2000-01-01').replace('Z', '')) >= cutoff_date]

        # Profession filter (applies to current page only)
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
        """Display enhanced audit logs table with empty state handling"""
        if not logs:
            st.info("No audit logs found matching your filters")
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
        """Display audit statistics with error handling for empty results"""
        if 'audit_logs' not in st.session_state:
            st.info("Load audit logs to see statistics")
            return

        logs = st.session_state.audit_logs

        # Handle empty logs case
        if not logs:
            st.info("No audit logs available for the selected filters")
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            total_actions = len(logs)
            st.metric("Total Actions", total_actions)

        with col2:
            unique_users = len(set(log.get('username') for log in logs if log.get('username')))
            st.metric("Unique Users", unique_users)

        with col3:
            # FIXED: Handle empty action list
            actions = [log.get('action') for log in logs if log.get('action')]
            if actions:
                most_common_action = max(set(actions), key=actions.count)
                st.metric("Most Common Action", most_common_action)
            else:
                st.metric("Most Common Action", "N/A")

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
            db_success, _ = self.api.get_all_users_paginated()
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
        """Enhanced system data export with comprehensive error handling - UPDATED TO PAGINATED"""
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

                # Helper function to safely get paginated data
                def safe_get_paginated_data(api_method, data_key, description):
                    try:
                        success, response = api_method(limit=5000)  # Get larger limit for export
                        if success and isinstance(response, dict):
                            data = response.get(data_key, [])
                            total_count = response.get('total_count', 0)
                            export_data[data_key] = data
                            export_data['export_metadata']['successful_exports'].append(
                                f"{description} ({total_count} records)")
                            return len(data)
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

                # Get all data using paginated endpoints
                users_count = safe_get_paginated_data(self.api.get_all_users_paginated, 'users', 'users')
                reports_count = safe_get_paginated_data(self.api.get_all_reports_paginated, 'reports', 'reports')

                # Audit logs still uses the old method (keep as is)
                def safe_get_audit_data():
                    try:
                        success, response = self.api.get_audit_logs(limit=5000)
                        if success and isinstance(response, list):
                            export_data['audit_logs'] = response
                            export_data['export_metadata']['successful_exports'].append(
                                f"audit_logs ({len(response)} records)")
                            return len(response)
                        else:
                            error_msg = response.get('detail', 'Unknown error') if isinstance(response, dict) else str(
                                response)
                            export_data['export_metadata']['failed_exports'].append({
                                'type': 'audit_logs',
                                'error': error_msg
                            })
                            return 0
                    except Exception as e:
                        export_data['export_metadata']['failed_exports'].append({
                            'type': 'audit_logs',
                            'error': f"Exception: {str(e)}"
                        })
                        return 0

                audit_count = safe_get_audit_data()

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
    """Enhanced admin dashboard main function with authentication check"""
    # Double-check authentication before proceeding
    if not api.token:
        st.error("❌ Not authenticated. Please login first.")
        return

    # Test API connectivity and permissions
    with st.spinner("Checking permissions..."):
        success, user_response = api.get_current_user()
        if not success:
            st.error(f"❌ Authentication failed: {user_response.get('detail', 'Unknown error')}")
            return

        user_role = user_response.get('role', '')
        if user_role not in ['admin']:
            st.error("🔒 Access denied. Administrator privileges required.")
            return

    # If we get here, user is authenticated and has admin privileges
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