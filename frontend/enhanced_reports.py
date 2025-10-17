import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta, time
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

    # Check user permissions - FIXED ROLE LOGIC
    user_role = st.session_state.get('user_role', '')

    # Define role permissions
    can_view_all = user_role in ['admin', 'reviewer']  # Admin + Reviewer can see all reports
    can_manage = user_role in ['admin']  # Only admins can do bulk operations

    # Initialize tabs for all cases to avoid reference errors
    tab1 = None
    tab2 = None
    tab3 = None

    # Tabs for different views - FIXED TAB LOGIC
    if can_manage:  # Admin - 3 tabs
        tab1, tab2, tab3 = st.tabs(["📊 My Reports", "👀 All Reports", "⚡ Bulk Operations"])
    elif can_view_all:  # Reviewer - 2 tabs
        tab1, tab2 = st.tabs(["📊 My Reports", "👀 All Reports"])
    else:  # Regular users - 1 tab
        tab1, = st.tabs(["📊 My Reports"])

    # Always show My Reports tab
    with tab1:
        show_my_reports(api)

    # Only show All Reports tab if user has permission and tab exists
    if can_view_all and tab2 is not None:
        with tab2:
            show_all_reports(api)

    # Only show Bulk Operations tab if admin and tab exists
    if can_manage and tab3 is not None:
        with tab3:
            show_bulk_operations(api, can_manage)



def show_my_reports(api: EnhancedAPIClient):
    """Display user's own reports with enhanced features"""
    st.subheader("My Reports")

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search reports...", placeholder="Search by title or content", key="my_reports_search")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "draft", "submitted", "under_review", "approved", "rejected"],
            key="my_reports_status"
        )

    with col3:
        date_filter = st.selectbox(
            "Time Range",
            ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"],
            key="my_reports_date"
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
            st.info("No reports found matching your criteria. Go to the Create Report page to start creating reports")
            return

    # Display reports in an enhanced table with unique context
    display_reports_table(filtered_reports, api, show_actions=True, context="my_reports")


def show_all_reports(api: EnhancedAPIClient):
    """Display all reports (admin/reviewer view)"""
    st.subheader("All System Reports")

    # Enhanced filters for admin view
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search all reports...", key="all_reports_search")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "draft", "submitted", "under_review", "approved", "rejected"],
            key="all_reports_status"
        )

    with col3:
        user_filter = st.text_input("User", placeholder="Filter by username", key="all_reports_user")

    with col4:
        date_filter = st.selectbox(
            "Time Range",
            ["All Time", "Today", "Last 7 days", "Last 30 days"],
            key="all_reports_date"
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

    # Display reports table with unique context
    display_reports_table(filtered_reports, api, show_actions=True, show_user=True, context="all_reports")


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
        ].copy()

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
                    selected_indices.append(idx)
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
            cutoff = now - timedelta(days=1)

        filtered = [r for r in filtered if
                    datetime.fromisoformat(r.get('created_at', '2000-01-01').replace('Z', '')) >= cutoff]

    return filtered

def display_reports_table(reports: List[Dict], api: EnhancedAPIClient,
                          show_actions: bool = True, show_user: bool = False, context: str = ""):
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
            format_func=lambda x: f"ID {x}: {next(r['title'] for r in reports if r['id'] == x)}",
            key=f"{context}_report_select"  # ✅ UNIQUE KEY for selectbox
        )

        if selected_id:
            show_report_actions(selected_id, reports, api, context)  # ✅ PASS CONTEXT


def show_report_actions(report_id: int, reports: List[Dict], api: EnhancedAPIClient, context: str = ""):
    """Show actions for a specific report - WITH UNIQUE KEYS PER CONTEXT"""
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return

    st.write("### 🛠️ Report Actions")
    st.write("---")

    # Create action buttons with unique keys using context
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Only show Submit button for draft reports
        current_status = report.get('status', 'draft')
        if current_status == 'draft':
            st.write("**Submit for Review**")
            if st.button("📤 Submit", key=f"{context}_submit_{report_id}", use_container_width=True):
                with st.spinner("🔄 Submitting report for review..."):
                    success, result = api.submit_report_for_review(report_id)

                    if success:
                        # Update the report status in the local list for immediate UI update
                        st.balloons()
                        report['status'] = 'submitted'
                        # Also update submitted_at timestamp if available in response
                        if 'submitted_at' in result:
                            report['submitted_at'] = result['submitted_at']

                        st.success("✅ Report submitted for review!")
                        st.rerun()
                    else:
                        error_msg = result.get('detail', 'Unknown error')
                        st.error(f"❌ Submit failed: {error_msg}")
        else:
            # Show status for non-draft reports
            status_display = current_status.replace('_', ' ').title()
            st.write(f"**Current Status:** {status_display}")
            if current_status == 'submitted':
                st.info("📋 Report is under review")
            elif current_status == 'approved':
                st.success("✅ Report approved")
            elif current_status == 'rejected':
                st.error("❌ Report rejected")
            elif current_status == 'under_review':
                st.warning("🔍 Report is being reviewed")

    with col2:
        st.write("**Download**")
        try:
            role = determine_role_from_report(report)
            frontend_format = {role: {}}

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
                "📥 Download",
                data=json_str,
                file_name=f"report_{report['id']}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key=f"{context}_download_{report_id}",  # ✅ UNIQUE KEY
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Download error: {str(e)}")

    with col3:
        st.write("**Delete Report**")
        # Only allow deletion for draft reports or admins
        current_status = report.get('status', 'draft')
        can_delete = (
                st.session_state.get('user_role') in ['admin'] or
                (report.get('owner_id') == st.session_state.get('user_id') and current_status == 'draft')
        )

        if can_delete:
            if st.button("🗑️ Delete", key=f"{context}_delete_{report_id}", use_container_width=True, type="secondary"):
                with st.spinner("🔄 Deleting report..."):
                    success, result = api.delete_report(report_id)

                    if success:
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Delete failed: {result.get('detail', 'Unknown error')}")
        else:
            if current_status != 'draft':
                st.info("🔒 Submitted reports cannot be deleted")

    # Show report details section
    st.write("---")
    st.subheader("📋 Report Details")

    # Check current view state
    is_full_details = st.session_state.get(f'{context}_show_details_{report_id}', False)

    # SINGLE TOGGLE BUTTON - placed prominently above the details
    toggle_col1, toggle_col2 = st.columns([1, 4])

    with toggle_col1:
        if is_full_details:
            button_label = "📖 Show Basic Details"
            button_type = "secondary"
        else:
            button_label = "📖 Show Full Details"
            button_type = "primary"

        if st.button(button_label, key=f"{context}_toggle_{report_id}",
                     use_container_width=True, type=button_type):
            # Toggle the state
            st.session_state[f'{context}_show_details_{report_id}'] = not is_full_details
            st.rerun()

    with toggle_col2:
        # Show current view status
        if is_full_details:
            st.success("🔍 **Full Details View** - Complete report information")
        else:
            st.info("📊 **Basic Details View** - Summary information")

    # Display the appropriate view based on toggle state
    if is_full_details:
        show_report_details(report, context)
    else:
        show_basic_report_details(report, context)


def show_basic_report_details(report: Dict, context: str = ""):
    """Show basic report information"""
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Basic Information**")
        st.write(f"**ID:** {report['id']}")
        st.write(f"**Title:** {report['title']}")
        st.write(f"**Status:** {report.get('status', 'draft').title()}")
        st.write(f"**Created:** {format_date(report.get('created_at'))}")

    with col2:
        st.write("**Statistics**")
        st.write(f"**Word Count:** {len(report.get('content', '').split())}")
        st.write(f"**Competencies:** {len(report.get('competencies', []))}")

        author_name = report.get('owner_full_name') or report.get('owner_username', 'Unknown')
        st.write(f"**Author:** {author_name}")
        st.write(f"**Email:** {report.get('owner_email', 'No email')}")

    # Quick content preview
    st.write("**Content Preview:**")
    content = report.get('content', 'No content available')
    preview_length = 300
    if len(content) > preview_length:
        preview = content[:preview_length] + "..."
    else:
        preview = content

    st.text_area("Content Preview", value=preview, height=100, disabled=True,
                 key=f"{context}_preview_{report['id']}", label_visibility="collapsed")


def show_report_details(report: Dict, context: str = ""):
    """Show detailed report information (enhanced version)"""
    # NO TOGGLE BUTTON HERE - only one toggle in the main actions area

    with st.expander(f"📋 Detailed Report: {report['title']}", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Information**")
            st.write(f"**ID:** {report['id']}")
            st.write(f"**Status:** {report.get('status', 'draft').title()}")
            st.write(f"**Created:** {format_date(report.get('created_at'))}")
            st.write(f"**Submitted:** {format_date(report.get('submitted_at'))}")
            st.write(f"**Reviewed:** {format_date(report.get('reviewed_at'))}")

        with col2:
            st.write("**Author Information**")
            author_name = report.get('owner_full_name') or report.get('owner_username', 'Unknown')
            st.write(f"**Author:** {author_name}")
            st.write(f"**Email:** {report.get('owner_email', 'No email')}")
            st.write(f"**Username:** {report.get('owner_username', 'N/A')}")

            st.write("**Statistics**")
            st.write(f"**Word Count:** {len(report.get('content', '').split())}")
            st.write(f"**Competencies:** {len(report.get('competencies', []))}")

            if report.get('review_notes'):
                st.write("**Review Notes:**")
                st.info(report['review_notes'])

        # Full content
        st.write("**Full Content:**")
        content = report.get('content', 'No content available')
        st.text_area("", value=content, height=200, disabled=True, key=f"{context}_full_content_{report['id']}")

        # Competencies section
        if report.get('competencies'):
            st.write("**Competencies:**")
            for comp in report['competencies']:
                with st.expander(f"🔧 {comp.get('competency_title', 'Competency')}"):
                    st.write(f"**Response:** {comp.get('user_response', 'No response')}")

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
            st.balloons()
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
            st.balloons()
            success_count += 1
        else:
            failed_reports.append((report_id, result.get('detail', 'Unknown error')))

    # Store results in session state to persist across rerun
    if success_count == len(report_ids):
        st.session_state['bulk_delete_success'] = {
            'count': success_count,
            'total': len(report_ids),
            'show_balloons': True
        }
    elif success_count > 0:
        st.session_state['bulk_delete_success'] = {
            'count': success_count,
            'total': len(report_ids),
            'show_balloons': False,
            'failed': failed_reports
        }
    else:
        st.session_state['bulk_delete_error'] = "❌ Failed to delete any reports"

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