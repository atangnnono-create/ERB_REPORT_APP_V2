import streamlit as st
from datetime import datetime
from typing import List, Dict
from services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState


def author_feedback_dashboard(api: EnhancedAPIClient):
    """Dashboard for authors to view reviewer feedback on their reports"""
    st.title("📝 Reviewer Feedback")
    st.markdown("View feedback and comments from reviewers on your submitted reports")

    # Get user's reports with review feedback
    with LoadingState("Loading your reports with feedback..."):
        success, response = api.get_my_reports_paginated(limit=1000)
        if success and isinstance(response, dict) and 'reports' in response:
            reports = response.get('reports', [])
        else:
            reports = []

        if not success:
            ErrorHandler.show_error("Failed to load your reports")
            return

        # Filter reports that have review notes or have been reviewed
        reports_with_feedback = [
            r for r in reports
            if
            r.get('review_notes') or r.get('reviewed_at') or r.get('status') in ['approved', 'rejected', 'under_review']
        ]

        if not reports_with_feedback:
            st.info("""
            ## 📋 No Feedback Yet

            You'll see reviewer feedback here when:
            - Your reports are under review
            - Reviewers provide comments on your work  
            - Reports are approved or rejected with feedback

            **Next Steps:**
            1. Submit reports for review in the **Create Report** section
            2. Check back here for reviewer comments
            3. Use feedback to improve your future reports
            """)
            return

    # Statistics
    approved_count = len([r for r in reports_with_feedback if r.get('status') == 'approved'])
    rejected_count = len([r for r in reports_with_feedback if r.get('status') == 'rejected'])
    under_review_count = len([r for r in reports_with_feedback if r.get('status') == 'under_review'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total with Feedback", len(reports_with_feedback))
    with col2:
        st.metric("✅ Approved", approved_count)
    with col3:
        st.metric("🔄 Revisions", rejected_count)
    with col4:
        st.metric("⏳ Under Review", under_review_count)

    st.markdown("---")

    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search reports...", placeholder="Search by title or feedback")
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "approved", "rejected", "under_review", "submitted"],
            key="feedback_status_filter"
        )

    # Display reports with feedback
    filtered_reports = _filter_feedback_reports(reports_with_feedback, search_term, status_filter)

    if not filtered_reports:
        st.info("No reports match your search criteria.")
        return

    for report in filtered_reports:
        _display_feedback_card(report)


def _filter_feedback_reports(reports: List[Dict], search: str, status: str) -> List[Dict]:
    """Filter reports for feedback dashboard"""
    filtered = reports

    # Search filter
    if search:
        search_lower = search.lower()
        filtered = [r for r in filtered if
                    search_lower in r.get('title', '').lower() or
                    search_lower in r.get('review_notes', '').lower()]

    # Status filter
    if status != "All":
        filtered = [r for r in filtered if r.get('status') == status]

    # Sort by most recently reviewed/updated
    filtered.sort(key=lambda x: _parse_date(x.get('reviewed_at') or x.get('updated_at') or x.get('created_at')),
                  reverse=True)

    return filtered


def _display_feedback_card(report: Dict):
    """Display a report card with reviewer feedback"""
    with st.container():
        # Header with status
        status = report.get('status', 'draft')
        status_config = {
            'approved': {"emoji": "✅", "color": "success", "label": "Approved"},
            'rejected': {"emoji": "🔄", "color": "warning", "label": "Needs Revision"},
            'under_review': {"emoji": "⏳", "color": "info", "label": "Under Review"},
            'submitted': {"emoji": "📝", "color": "info", "label": "Submitted"}
        }

        status_info = status_config.get(status, {"emoji": "📄", "color": "secondary", "label": status.title()})

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{status_info['emoji']} {report['title']}**")
            st.write(f"**ID:** {report['id']} | **Submitted:** {_format_date(report.get('submitted_at'))}")

        with col2:
            if status_info['color'] == 'success':
                st.success(status_info['label'])
            elif status_info['color'] == 'warning':
                st.warning(status_info['label'])
            else:
                st.info(status_info['label'])

        # Reviewer feedback section
        if report.get('review_notes'):
            st.markdown("---")
            st.subheader("📋 Reviewer Comments")

            # Feedback with nice formatting
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #3498db;">
                    {report['review_notes']}
                </div>
                """, unsafe_allow_html=True)

            # Review metadata
            if report.get('reviewed_at'):
                st.caption(f"📅 Reviewed on: {_format_date(report['reviewed_at'])}")

        # Action guidance based on status
        st.markdown("---")
        _display_action_guidance(report)

        st.markdown("---")


def _display_action_guidance(report: Dict):
    """Show recommended actions based on report status and feedback"""
    status = report.get('status')
    has_feedback = bool(report.get('review_notes'))

    if status == 'approved':
        st.success("""
        **🎉 Congratulations! Your report has been approved.**

        **Next Steps:**
        - ✅ Review any feedback for future improvements
        - 📊 Consider this report complete
        - 🚀 Start your next report using what you've learned
        """)

    elif status == 'rejected':
        st.warning("""
        **🔄 Your report needs revisions**

        **Next Steps:**
        - 📝 Address all reviewer comments above
        - 🔧 Make the requested improvements
        - 📤 Resubmit when revisions are complete
        - 💡 Use this feedback to strengthen your report
        """)

        if has_feedback:
            st.button("📝 Create Revised Version", key=f"revise_{report['id']}",
                      help="Start working on revisions based on the feedback")

    elif status == 'under_review':
        st.info("""
        **⏳ Your report is currently under review**

        **What's happening:**
        - 🔍 Reviewers are examining your work
        - 📝 They may provide additional feedback
        - ⏰ Check back soon for updates

        **While you wait:**
        - 📚 Review your other reports
        - 🚀 Start planning your next project
        """)

    elif status == 'submitted' and not has_feedback:
        st.info("""
        **📝 Your report is in the review queue**

        **Status:** Awaiting initial review
        **Expected:** Reviewers will examine your report soon

        Check back later for feedback and status updates.
        """)


def _parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    if not date_str:
        return datetime.min

    try:
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.min


def _format_date(date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return "Not submitted"

    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def main():
    """Main function for testing the feedback dashboard"""
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    author_feedback_dashboard(api)


if __name__ == "__main__":
    main()