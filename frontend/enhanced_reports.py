import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState, with_loading


def enhanced_reports_ui(api: EnhancedAPIClient):
    """Enhanced reports management with bulk operations"""

    st.set_page_config(page_title="Reports Management", layout="wide")

    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to view reports.")
        return

    st.title("📋 Enhanced Reports Management")

    # Check user permissions
    user_role = st.session_state.get('user_role', '')
    can_view_all = user_role in ['admin', 'reviewer']
    can_manage = user_role in ['admin']

    # Tabs for different views
    if can_view_all:
        tab1, tab2, tab3 = st.tabs(["📊 My Reports", "👀 All Reports", "⚡ Bulk Operations"])
    else:
        tab1, tab2 = st.tabs(["📊 My Reports", "⚡ Bulk Operations"])

    with tab1:
        show_my_reports(api)

    if can_view_all:
        with tab2:
            show_all_reports(api)

    with tab3 if can_view_all else tab2:
        show_bulk_operations(api, can_manage)


def show_my_reports(api: EnhancedAPIClient):
    """Display user's own reports with enhanced features"""
    st.subheader("My Reports")

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search reports...", placeholder="Search by title or content")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "draft", "submitted", "under_review", "approved", "rejected"]
        )

    with col3:
        date_filter = st.selectbox(
            "Time Range",
            ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"]
        )

    # Fetch reports
    with LoadingState("Loading your reports..."):
        success, reports = api.fetch_reports()

        if not success:
            ErrorHandler.show_error("Failed to load reports")
            return

        # Apply filters
        filtered_reports = apply_report_filters(reports, search_term, status_filter, date_filter)

        if not filtered_reports:
            st.info("No reports found matching your criteria.Go to the Create Report page to start creating reports")

            return

    # Display reports in an enhanced table
    display_reports_table(filtered_reports, api, show_actions=True)


def show_all_reports(api: EnhancedAPIClient):
    """Display all reports (admin/reviewer view)"""
    st.subheader("All System Reports")

    # Enhanced filters for admin view
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search all reports...", key="admin_search")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "draft", "submitted", "under_review", "approved", "rejected"],
            key="admin_status"
        )

    with col3:
        user_filter = st.text_input("User", placeholder="Filter by username")

    with col4:
        date_filter = st.selectbox(
            "Time Range",
            ["All Time", "Today", "Last 7 days", "Last 30 days"],
            key="admin_date"
        )

    # Fetch all reports
    with LoadingState("Loading all reports..."):
        success, reports = api.get_all_reports()

        if not success:
            ErrorHandler.show_error("Failed to load reports")
            return

        # Apply filters
        filtered_reports = apply_report_filters(reports, search_term, status_filter, date_filter, user_filter)

        if not filtered_reports:
            st.info("No reports found matching your criteria.")
            return

    # Statistics
    show_reports_statistics(filtered_reports)

    # Display reports table
    display_reports_table(filtered_reports, api, show_actions=True, show_user=True)


def show_bulk_operations(api: EnhancedAPIClient, can_manage: bool):
    """Bulk operations interface"""
    st.subheader("⚡ Bulk Operations")

    # Fetch reports for selection
    with LoadingState("Loading reports..."):
        if can_manage:
            success, reports = api.get_all_reports()
        else:
            success, reports = api.fetch_reports()

        if not success or not reports:
            st.info("No reports available for bulk operations.")
            return

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([{
        'id': r['id'],
        'title': r['title'],
        'status': r.get('status', 'draft'),
        'user': r.get('owner_username', 'N/A'),
        'created': r.get('created_at', ''),
        'words': len(r.get('content', '').split())
    } for r in reports])

    # Bulk selection interface
    st.write("### Select Reports for Bulk Actions")

    # Multi-select with filters
    col1, col2 = st.columns(2)

    with col1:
        status_select = st.multiselect(
            "Filter by Status",
            options=df['status'].unique(),
            default=df['status'].unique()
        )

    with col2:
        if can_manage:
            user_select = st.multiselect(
                "Filter by User",
                options=df['user'].unique(),
                default=df['user'].unique()
            )
        else:
            user_select = [st.session_state.username]

    # Apply filters
    filtered_df = df[
        (df['status'].isin(status_select)) &
        (df['user'].isin(user_select))
    ].copy()  # Use copy to avoid warnings

    if filtered_df.empty:
        st.info("No reports match the selected filters.")
        return

    # Reset index to ensure positional indexing works correctly
    filtered_df = filtered_df.reset_index(drop=True)

    # Report selection
    st.write(f"**Found {len(filtered_df)} reports**")

    # Enhanced selection with checkboxes
    selected_indices = []
    with st.container():
        st.write("### Select Reports")
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            with col1:
                selected = st.checkbox(
                    "Select",
                    key=f"select_{row['id']}",
                    label_visibility="collapsed"
                )
                if selected:
                    selected_indices.append(idx)  # Now idx is 0, 1, 2, ... matching iloc positions
            with col2:
                st.write(f"**{row['title']}**")
            with col3:
                st.write(f"Status: {row['status']}")
            with col4:
                st.write(f"User: {row['user']}")

    if not selected_indices:
        st.info("Please select at least one report to perform bulk operations.")
        return

    # Safe selection with bounds checking
    try:
        selected_reports = filtered_df.iloc[selected_indices]
        selected_ids = selected_reports['id'].tolist()
        st.success(f"✅ {len(selected_ids)} reports selected")
    except IndexError as e:
        st.error(f"Error selecting reports: {str(e)}")
        st.info("Please refresh the page and try again.")
        return

    # Bulk actions
    st.write("### Bulk Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Submit for Review", use_container_width=True):
            bulk_update_status(api, selected_ids, "submitted")

    with col2:
        if st.button("🔄 Set to Draft", use_container_width=True):
            bulk_update_status(api, selected_ids, "draft")

    with col3:
        if st.button("🗑️ Delete Reports", use_container_width=True):
            bulk_delete_reports(api, selected_ids)

    # Advanced bulk operations for admins
    if can_manage:
        st.write("### Admin Bulk Operations")

        col1, col2 = st.columns(2)

        with col1:
            new_status = st.selectbox(
                "Set Status",
                ["under_review", "approved", "rejected"]
            )
            if st.button("🔄 Update Status", use_container_width=True):
                bulk_update_status(api, selected_ids, new_status)

        with col2:
            if st.button("📥 Export Selected", use_container_width=True):
                bulk_export_reports(selected_reports.to_dict('records'))
def apply_report_filters(reports: List[Dict], search_term: str, status_filter: str,
                         date_filter: str, user_filter: str = None) -> List[Dict]:
    """Apply filters to reports list"""
    filtered = reports

    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [r for r in filtered if
                    search_lower in r.get('title', '').lower() or
                    search_lower in r.get('content', '').lower()]

    # Status filter
    if status_filter != "All":
        filtered = [r for r in filtered if r.get('status') == status_filter]

    # User filter (for admin view)
    if user_filter:
        filtered = [r for r in filtered if
                    user_filter.lower() in r.get('owner_username', '').lower()]

    # Date filter
    if date_filter != "All Time":
        now = datetime.now()
        if date_filter == "Last 7 days":
            cutoff = now - timedelta(days=7)
        elif date_filter == "Last 30 days":
            cutoff = now - timedelta(days=30)
        elif date_filter == "Last 90 days":
            cutoff = now - timedelta(days=90)
        elif date_filter == "Today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            cutoff = now - timedelta(days=1)  # Default to yesterday

        filtered = [r for r in filtered if
                    datetime.fromisoformat(r.get('created_at', '2000-01-01').replace('Z', '')) >= cutoff]

    return filtered


def display_reports_table(reports: List[Dict], api: EnhancedAPIClient,
                          show_actions: bool = True, show_user: bool = False):
    """Display reports in an enhanced table format"""

    # Create DataFrame for better display
    report_data = []
    for report in reports:
        row = {
            'ID': report['id'],
            'Title': report['title'],
            'Status': report.get('status', 'draft').title(),
            'Created': format_date(report.get('created_at')),
            'Words': len(report.get('content', '').split()),
            'Competencies': len(report.get('competencies', []))
        }
        if show_user:
            row['User'] = report.get('owner_username', 'N/A')
        report_data.append(row)

    df = pd.DataFrame(report_data)

    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Title": st.column_config.TextColumn(width="large"),
            "Status": st.column_config.TextColumn(width="small"),
            "Created": st.column_config.TextColumn(width="medium"),
            "Words": st.column_config.NumberColumn(width="small"),
            "Competencies": st.column_config.NumberColumn(width="small"),
            "User": st.column_config.TextColumn(width="medium") if show_user else None
        }
    )

    # Individual report actions
    if show_actions:
        st.write("### Individual Report Actions")

        selected_id = st.selectbox(
            "Select report for actions:",
            options=[r['id'] for r in reports],
            format_func=lambda x: f"ID {x}: {next(r['title'] for r in reports if r['id'] == x)}"
        )

        if selected_id:
            show_report_actions(selected_id, reports, api)


def show_report_actions(report_id: int, reports: List[Dict], api: EnhancedAPIClient):
    """Show actions for a specific report"""
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return

    import time
    unique_suffix = str(hash(f"{report_id}_{time.time()}"))

    # Add extra column for Continue Editing - now 5 columns
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        current_status = report.get('status', 'draft')
        if current_status == 'draft':
            if st.button("📤 Submit for Review", key=f"submit_{unique_suffix}", use_container_width=True):
                # Debug: Print everything we know
                st.write("## 🐛 DEBUG - Submit for Review")
                st.write(f"**Report ID:** {report_id}")
                st.write(f"**Report Title:** {report.get('title')}")
                st.write(f"**Current Status:** {current_status}")
                st.write(f"**User ID:** {st.session_state.get('user_id')}")
                st.write(f"**User Role:** {st.session_state.get('user_role')}")
                st.write(f"**Report Owner ID:** {report.get('owner_id')}")
                st.write(f"**API Base URL:** {api.base_url}")

                # Test if API method exists and is callable
                st.write("### API Method Check")
                if hasattr(api, 'submit_report_for_review'):
                    st.success("✅ api.submit_report_for_review method exists")
                    try:
                        # Call the method and capture everything
                        with LoadingState("Calling API..."):
                            st.write("### Making API Call...")
                            success, result = api.submit_report_for_review(report_id)

                            st.write("### API Response:")
                            st.write(f"**Success:** {success}")
                            st.write(f"**Result Type:** {type(result)}")
                            st.write(f"**Result:** {result}")

                            if success:
                                st.success("🎉 API Call SUCCESSFUL!")
                                st.balloons()
                                # Wait a moment to see the success
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("💥 API Call FAILED!")
                                # Show detailed error
                                if isinstance(result, dict):
                                    st.write("**Error Details:**")
                                    for key, value in result.items():
                                        st.write(f"- {key}: {value}")
                                else:
                                    st.write(f"**Raw Error:** {result}")
                    except Exception as e:
                        st.error(f"🚨 EXCEPTION during API call: {str(e)}")
                        st.write("**Exception Type:**", type(e).__name__)
                        import traceback
                        st.write("**Traceback:**")
                        st.code(traceback.format_exc())
                else:
                    st.error("❌ api.submit_report_for_review method NOT FOUND")
    with col2:
        # Download - FIXED VERSION
        try:
            # Transform backend format to frontend format
            role = determine_role_from_report(report)

            # Build the frontend-compatible structure
            frontend_format = {
                role: {}
            }

            # Transform competencies
            for competency in report.get('competencies', []):
                key = competency['competency_key']
                response_text = competency['user_response'] or ""

                frontend_format[role][key] = {
                    "title": competency['competency_title'],
                    "response": response_text,
                    "word_count": len(response_text.split()) if response_text else 0
                }

            json_str = json.dumps(frontend_format, indent=2, ensure_ascii=False)

            st.download_button(
                "📥 Download JSON",
                data=json_str,
                file_name=f"report_{report['id']}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key=f"download_{unique_suffix}",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Error preparing download: {str(e)}")

    with col3:
        # Delete
        if st.button("🗑️ Delete", key=f"delete_{unique_suffix}", use_container_width=True):
            if st.session_state.get('user_role') in ['admin'] or report.get('owner_id') == st.session_state.get(
                    'user_id'):
                with LoadingState("Deleting report..."):
                    success, result = api.delete_report(report_id)
                    if success:
                        st.success("Report deleted!")
                        st.rerun()
                    else:
                        ErrorHandler.show_error(f"Failed to delete: {result.get('detail', 'Unknown error')}")
            else:
                ErrorHandler.show_error("You don't have permission to delete this report")

    with col4:
        # View details
        if st.button("👁️ View Details", key=f"view_{unique_suffix}", use_container_width=True):
            show_report_details(report)


def show_report_details(report: Dict):
    """Show detailed report information"""
    with st.expander(f"📋 Report Details: {report['title']}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Information**")
            st.write(f"**ID:** {report['id']}")
            st.write(f"**Status:** {report.get('status', 'draft').title()}")
            st.write(f"**Created:** {format_date(report.get('created_at'))}")
            st.write(f"**Submitted:** {format_date(report.get('submitted_at'))}")
            st.write(f"**Reviewed:** {format_date(report.get('reviewed_at'))}")

        with col2:
            st.write("**Statistics**")
            st.write(f"**Word Count:** {len(report.get('content', '').split())}")
            st.write(f"**Competencies:** {len(report.get('competencies', []))}")
            st.write(f"**Owner:** {report.get('owner_username', 'N/A')}")

            if report.get('review_notes'):
                st.write("**Review Notes:**")
                st.info(report['review_notes'])

        # Content preview
        st.write("**Content Preview:**")
        content = report.get('content', 'No content')
        if len(content) > 500:
            st.text_area("", value=content[:500] + "...", height=150, disabled=True)
        else:
            st.text_area("", value=content, height=150, disabled=True)


def show_reports_statistics(reports: List[Dict]):
    """Display reports statistics"""
    if not reports:
        return

    st.write("### 📈 Reports Statistics")

    col1, col2, col3, col4 = st.columns(4)

    # Basic stats
    total_reports = len(reports)
    status_counts = {}
    total_words = 0

    for report in reports:
        status = report.get('status', 'draft')
        status_counts[status] = status_counts.get(status, 0) + 1
        total_words += len(report.get('content', '').split())

    with col1:
        st.metric("Total Reports", total_reports)

    with col2:
        st.metric("Total Words", f"{total_words:,}")

    with col3:
        avg_words = total_words // total_reports if total_reports > 0 else 0
        st.metric("Avg Words/Report", avg_words)

    with col4:
        draft_count = status_counts.get('draft', 0)
        st.metric("Draft Reports", draft_count)

    # Status distribution
    st.write("**Status Distribution:**")
    for status, count in status_counts.items():
        percentage = (count / total_reports) * 100
        st.progress(percentage / 100, text=f"{status.title()}: {count} ({percentage:.1f}%)")


@with_loading("Updating report status...")
def bulk_update_status(api: EnhancedAPIClient, report_ids: List[int], new_status: str):
    """Bulk update report status"""
    success_count = 0
    failed_reports = []

    for report_id in report_ids:
        # For draft -> submitted, use submit endpoint
        if new_status == "submitted":
            success, result = api.submit_report_for_review(report_id)

        else:
            # For other status changes, use review endpoint (admin/reviewer only)
            success, result = api.review_report(report_id, new_status, "Bulk status update")

        if success:
            success_count += 1
        else:
            failed_reports.append((report_id, result.get('detail', 'Unknown error')))

    if success_count == len(report_ids):
        ErrorHandler.show_success(f"✅ Successfully updated {success_count} reports")
    else:
        ErrorHandler.show_warning(f"Updated {success_count}/{len(report_ids)} reports")
        if failed_reports:
            with st.expander("Failed reports"):
                for report_id, error in failed_reports:
                    st.write(f"Report {report_id}: {error}")

    st.rerun()


@with_loading("Deleting reports...")
def bulk_delete_reports(api: EnhancedAPIClient, report_ids: List[int]):
    """Bulk delete reports"""
    if not st.session_state.get('user_role') in ['admin']:
        ErrorHandler.show_error("Only admins can perform bulk deletions")
        return

    success_count = 0
    failed_reports = []

    for report_id in report_ids:
        success, result = api.delete_report(report_id)
        if success:
            success_count += 1
        else:
            failed_reports.append((report_id, result.get('detail', 'Unknown error')))

    if success_count == len(report_ids):
        ErrorHandler.show_success(f"✅ Successfully deleted {success_count} reports")
    else:
        ErrorHandler.show_warning(f"Deleted {success_count}/{len(report_ids)} reports")
        if failed_reports:
            with st.expander("Failed deletions"):
                for report_id, error in failed_reports:
                    st.write(f"Report {report_id}: {error}")

    st.rerun()


def bulk_export_reports(reports: List[Dict]):
    """Bulk export selected reports in create_report.py compatible format"""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "total_reports": len(reports),
        "reports": []
    }

    for report in reports:
        # Transform each report to frontend format
        role = determine_role_from_report(report)
        frontend_report = {
            role: {}
        }

        for competency in report.get('competencies', []):
            key = competency['competency_key']
            response_text = competency['user_response'] or ""

            frontend_report[role][key] = {
                "title": competency['competency_title'],
                "response": response_text,
                "word_count": len(response_text.split()) if response_text else 0
            }

        export_data["reports"].append(frontend_report)

    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

    st.download_button(
        "💾 Download Export",
        data=json_str,
        file_name=f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key="bulk_export"
    )
#################################################################################################


def determine_role_from_report(report: Dict) -> str:
    """Determine role from report title"""
    title = report.get('title', '').lower()

    if 'technician' in title:
        return "Engineering Technician"
    elif 'technologist' in title:
        return "Engineering Technologist"
    else:
        return "Engineer"  # Default

######################################################################################
def format_date(date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return "N/A"

    try:
        # Handle both with and without timezone
        if 'Z' in date_str:
            date_str = date_str.replace('Z', '+00:00')

        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def main():
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    enhanced_reports_ui(api)


if __name__ == "__main__":
    main()