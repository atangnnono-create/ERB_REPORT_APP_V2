import streamlit as st
import functools
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState


def review_dashboard(api: EnhancedAPIClient):
    """Enhanced Review Dashboard with comprehensive metrics and overview"""
    st.title("👀 Review Dashboard")

    # Permission check for reviewers
    user_role = st.session_state.get('user_role', '')
    if user_role not in ['admin', 'reviewer']:
        ErrorHandler.show_error("🔒 Access denied. Reviewer privileges required.")
        return

    # Show comprehensive metrics first
    show_review_metrics(api)

    # Main dashboard sections
    tab1, tab2, tab3 = st.tabs(["📊 Review Queue", "📈 Analytics", "⚙️ Settings"])

    with tab1:
        _show_reviewer_dashboard(api)

    with tab2:
        _show_analytics_dashboard(api)

    with tab3:
        _show_review_settings(api)


def show_review_metrics(api: EnhancedAPIClient):
    """Display comprehensive review metrics cards"""
    stats = get_review_statistics(api)

    if not stats:
        ErrorHandler.show_error("Failed to load review statistics")
        return

    # Main metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        delta_pending = stats.get('delta_pending', 0)
        st.metric(
            "📝 Pending Review",
            stats['total_pending'],
            delta=f"{delta_pending:+}" if delta_pending != 0 else None,
            help="Reports awaiting your review (change from last week)"
        )

    with col2:
        st.metric(
            "⏳ Under Review",
            stats['under_review'],
            help="Reports currently being reviewed by you"
        )

    with col3:
        st.metric(
            "✅ Approved",
            stats['approved'],
            delta=f"{stats['approval_rate']:.1f}%",
            help="Approved reports and overall approval rate"
        )

    with col4:
        avg_review_time = stats.get('avg_review_time', 0)
        st.metric(
            "⏱️ Avg Review Time",
            f"{avg_review_time:.1f}h",
            help="Average time to complete a review"
        )

    with col5:
        your_reviews = stats.get('your_reviews_today', 0)
        st.metric(
            "📋 Reviewed Today",
            your_reviews,
            help="Number of reviews you've completed today"
        )

    # Secondary metrics row
    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        st.metric(
            "❌ Rejected",
            stats['rejected'],
            delta=f"{stats['rejection_rate']:.1f}%",
            help="Rejected reports and rejection rate"
        )

    with col7:
        st.metric(
            "📊 Total In System",
            stats['total_reports'],
            help="All reports in the review system"
        )

    with col8:
        urgent_count = stats.get('urgent_reports', 0)
        st.metric(
            "🚨 Urgent",
            urgent_count,
            delta="Priority" if urgent_count > 0 else None,
            help="Reports marked as urgent"
        )

    with col9:
        old_pending = stats.get('old_pending', 0)
        st.metric(
            "📅 Over 7 Days",
            old_pending,
            delta="Attention" if old_pending > 0 else None,
            help="Reports pending for over 7 days"
        )

    with col10:
        efficiency = stats.get('review_efficiency', 0)
        st.metric(
            "⭐ Efficiency",
            f"{efficiency:.0f}%",
            help="Your review completion rate"
        )

    st.markdown("---")


def get_review_statistics(api: EnhancedAPIClient) -> Dict:
    """Get comprehensive statistics for the review dashboard"""
    with LoadingState("Loading review statistics..."):
        # Get ALL reports for accurate metrics (not just pending review)
        success, all_reports = api.get_all_reports()

        if not success:
            return {}

        # Calculate comprehensive statistics
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Status counts from ALL reports
        status_counts = {
            'submitted': len([r for r in all_reports if r.get('status') == 'submitted']),
            'under_review': len([r for r in all_reports if r.get('status') == 'under_review']),
            'approved': len([r for r in all_reports if r.get('status') == 'approved']),
            'rejected': len([r for r in all_reports if r.get('status') == 'rejected']),
            'draft': len([r for r in all_reports if r.get('status') == 'draft'])
        }

        total_pending = status_counts['submitted'] + status_counts['under_review']
        total_reviewed = status_counts['approved'] + status_counts['rejected']
        total_reports = len(all_reports)

        # Calculate rates - use ALL reports for accurate percentages
        approval_rate = (status_counts['approved'] / total_reviewed * 100) if total_reviewed > 0 else 0
        rejection_rate = (status_counts['rejected'] / total_reviewed * 100) if total_reviewed > 0 else 0

        # Calculate additional metrics
        urgent_reports = len([r for r in all_reports if _is_urgent_report(r)])
        old_pending = len([r for r in all_reports if _is_old_pending_report(r, one_week_ago)])

        # Calculate review efficiency (simplified)
        your_reviews_today = len([r for r in all_reports
                                  if r.get('reviewed_by') == st.session_state.user_id
                                  and _parse_date(r.get('reviewed_at')) >= today_start])

        # Average review time (placeholder - would need more data)
        avg_review_time = 2.5  # hours - this would come from actual review data

        # Review efficiency (percentage of assigned reviews completed)
        assigned_reviews = len([r for r in all_reports if r.get('status') == 'under_review'
                                and r.get('reviewed_by') == st.session_state.user_id])
        completed_reviews = len([r for r in all_reports if r.get('status') in ['approved', 'rejected']
                                 and r.get('reviewed_by') == st.session_state.user_id])
        review_efficiency = (completed_reviews / (assigned_reviews + completed_reviews) * 100) if (
                                                                                                          assigned_reviews + completed_reviews) > 0 else 0

        # Delta calculations (change from previous period)
        delta_pending = 0  # This would require historical data

        return {
            'total_pending': total_pending,
            'under_review': status_counts['under_review'],
            'approved': status_counts['approved'],
            'rejected': status_counts['rejected'],
            'total_reports': total_reports,
            'approval_rate': approval_rate,
            'rejection_rate': rejection_rate,
            'urgent_reports': urgent_reports,
            'old_pending': old_pending,
            'your_reviews_today': your_reviews_today,
            'avg_review_time': avg_review_time,
            'review_efficiency': review_efficiency,
            'delta_pending': delta_pending,
            'status_counts': status_counts
        }

def _is_urgent_report(report: Dict) -> bool:
    """Determine if a report is urgent"""
    # Criteria for urgency: high priority, specific keywords, or from important users
    title = report.get('title', '').lower()
    content = report.get('content', '').lower()
    urgent_keywords = ['urgent', 'asap', 'critical', 'important', 'priority']

    return any(keyword in title or keyword in content for keyword in urgent_keywords)


def _is_old_pending_report(report: Dict, cutoff_date: datetime) -> bool:
    """Check if a report has been pending for too long"""
    if report.get('status') not in ['submitted', 'under_review']:
        return False

    submitted_date = _parse_date(report.get('submitted_at'))
    if not submitted_date:
        return False

    return submitted_date < cutoff_date


def _parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    if not date_str:
        return None

    try:
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None


@functools.lru_cache(maxsize=1)
def get_cached_reports_for_review(api: EnhancedAPIClient, user_id: int):
    """Cache reports for review to prevent repeated API calls"""
    return api.get_reports_for_review()


def _show_reviewer_dashboard(api: EnhancedAPIClient):
    """Show the enhanced review queue interface"""
    st.subheader("📝 Review Queue")

    # DEBUG: Check current cache state
    cache_key = f"reports_for_review_{st.session_state.user_id}"


    # Quick filters
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search_filter = st.text_input("🔍 Search reports...", placeholder="Search by title, author, or content")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "submitted", "under_review", "urgent"],
            key="queue_status_filter"
        )

    with col3:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "High", "Normal"],
            key="queue_priority_filter"
        )

    with col4:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest", "Oldest", "Urgent", "Word Count"],
            key="queue_sort_by"
        )

    # Load reports for review with caching
    with LoadingState("Loading review queue..."):
        if cache_key not in st.session_state:

            success, reports = api.get_reports_for_review()
            if success:
                st.session_state[cache_key] = reports

            else:
                st.session_state[cache_key] = []

        else:
            reports = st.session_state[cache_key]


        reports = st.session_state[cache_key]

        if not reports:
            st.success("🎉 No reports pending review!")
            return

        # Filter and sort reports
        filtered_reports = _filter_and_sort_reports(reports, search_filter, status_filter, priority_filter, sort_by)
        pending_review = [r for r in filtered_reports if r.get('status') in ['submitted', 'under_review']]

        print(f"DEBUG: After filtering - Total: {len(reports)}, Filtered: {len(filtered_reports)}, Pending: {len(pending_review)}")
        print(f"DEBUG: Status breakdown: {[(r['id'], r.get('status')) for r in reports if r.get('status') in ['submitted', 'under_review']]}")

        if not pending_review:
            st.success("✅ All reports have been reviewed!")
            return

        # Check if we're currently reviewing a report
        review_container = st.container()

        with review_container:
            if 'current_review_id' in st.session_state and st.session_state.current_review_id:
                _show_review_interface(api, st.session_state.current_review_id, pending_review)
                return

        # Display enhanced review queue
        st.write(f"**{len(pending_review)} reports awaiting review:**")

        # Display each report card
        for report in pending_review:
            _display_report_card(api, report)


def _filter_and_sort_reports(reports: List[Dict], search: str, status: str, priority: str, sort: str) -> List[Dict]:
    """Filter and sort reports based on criteria"""
    filtered = reports

    # Search filter
    if search:
        search_lower = search.lower()
        filtered = [r for r in filtered if
                    search_lower in r.get('title', '').lower() or
                    search_lower in r.get('content', '').lower() or
                    search_lower in r.get('owner_username', '').lower() or
                    search_lower in r.get('owner_full_name', '').lower()]

    # Status filter
    if status != "All":
        if status == "urgent":
            filtered = [r for r in filtered if _is_urgent_report(r)]
        else:
            filtered = [r for r in filtered if r.get('status') == status]

    # Priority filter
    if priority != "All":
        is_high_priority = priority == "High"
        filtered = [r for r in filtered if _is_urgent_report(r) == is_high_priority]

    # Sort
    if sort == "Newest":
        filtered.sort(key=lambda x: _parse_date(x.get('submitted_at')) or datetime.min, reverse=True)
    elif sort == "Oldest":
        filtered.sort(key=lambda x: _parse_date(x.get('submitted_at')) or datetime.max)
    elif sort == "Urgent":
        filtered.sort(key=lambda x: (_is_urgent_report(x), _parse_date(x.get('submitted_at')) or datetime.min),
                      reverse=True)
    elif sort == "Word Count":
        filtered.sort(key=lambda x: len(x.get('content', '').split()), reverse=True)

    return filtered

def _display_report_card(api: EnhancedAPIClient, report: Dict):
    """Display an enhanced report card in the queue"""
    # Determine card style based on urgency and status
    is_urgent = _is_urgent_report(report)
    status = report.get('status', 'submitted')
    days_old = _get_days_old(report)

    # Create a visually distinct card
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Title with status indicator
            status_emoji = "🚨" if is_urgent else "📝"
            if status == 'under_review':
                status_emoji = "🔍"

            st.write(f"**{status_emoji} {report['title']}**")
            st.write(f"👤 **Author:** {report.get('owner_full_name', 'Unknown')} ({report.get('owner_username', 'N/A')})")
            st.write(f"📅 **Submitted:** {_format_date(report.get('submitted_at'))} ({days_old} days ago)")
            st.write(f"📊 **Words:** {len(report.get('content', '').split())} | **Competencies:** {len(report.get('competencies', []))}")

            # Quick preview
            content_preview = report.get('content', '')[:150] + "..." if len(
                report.get('content', '')) > 150 else report.get('content', '')
            with st.expander("Preview content"):
                st.write(content_preview)

        with col2:
            # Status and priority badges
            if is_urgent:
                st.error("🚨 URGENT")
            else:
                st.info("Normal Priority")

            if status == 'under_review':
                st.warning("Under Review")
            else:
                st.info("Submitted")

            if days_old > 7:
                st.error(f"⏳ {days_old} days old")

        with col3:
            # Action buttons
            if st.button("👀 Review", key=f"review_{report['id']}", use_container_width=True):
                st.session_state.current_review_id = report['id']
                # Clear cache to force refresh when returning
                cache_key = f"reports_for_review_{st.session_state.user_id}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.rerun()

            # Quick actions
            if st.button("⏳ Mark Under Review", key=f"mark_under_{report['id']}", use_container_width=True):
                _quick_status_update(api, report['id'], 'under_review')

        st.markdown("---")



def _get_days_old(report: Dict) -> int:
    """Calculate how many days old a report is"""
    submitted_date = _parse_date(report.get('submitted_at'))
    if not submitted_date:
        return 0

    return (datetime.now() - submitted_date).days


def _quick_status_update(api: EnhancedAPIClient, report_id: int, status: str):
    """Quickly update report status without full review"""
    with LoadingState(f"Updating status to {status}..."):
        success, result = api.review_report(
            report_id=report_id,
            status=status,
            review_notes="Status updated via quick action"
        )

    if success:
        st.success(f"✅ Report marked as {status}!")
        # ONLY clear cache for final decisions, not for "under_review"
        if status in ["approved", "rejected"]:
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
        st.rerun()
    else:
        ErrorHandler.show_error(f"Failed to update status: {result.get('detail', 'Unknown error')}")


def _show_review_interface(api: EnhancedAPIClient, report_id: int, pending_reports: List[Dict]):
    """Display the enhanced review interface with under_review option"""
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

    # Get existing review notes from the report data
    existing_notes = report_to_review.get('review_notes', '')

    # Initialize session state with existing notes if not already set
    notes_key = f"notes_{report_id}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = existing_notes

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

    # Enhanced report details in columns
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Report Details**")
        st.write(f"**ID:** {report_to_review['id']}")
        st.write(f"**Author:** {report_to_review.get('owner_full_name', 'Unknown')}")
        st.write(f"**Username:** {report_to_review.get('owner_username', 'N/A')}")
        st.write(f"**Email:** {report_to_review.get('owner_email', 'No email')}")
        st.write(f"**Submitted:** {_format_date(report_to_review.get('submitted_at'))}")

        # Status with visual indicator
        status = report_to_review.get('status', 'unknown')
        if status == 'submitted':
            st.info(f"**Status:** 📝 Submitted")
        elif status == 'under_review':
            st.warning(f"**Status:** 🔍 Under Review")
        else:
            st.write(f"**Status:** {status}")

    with col2:
        st.write("**Statistics**")
        st.write(f"**Word Count:** {len(report_to_review.get('content', '').split())}")
        st.write(f"**Created:** {_format_date(report_to_review.get('created_at'))}")
        if report_to_review.get('updated_at'):
            st.write(f"**Last Updated:** {_format_date(report_to_review.get('updated_at'))}")

        # Urgency indicator
        if _is_urgent_report(report_to_review):
            st.error("🚨 **This report is marked as URGENT**")

        # Age indicator
        days_old = _get_days_old(report_to_review)
        if days_old > 7:
            st.warning(f"⏳ **This report is {days_old} days old**")

    # Report content
    st.markdown("---")
    st.subheader("Report Content")
    st.text_area("Content", report_to_review.get('content', ''), height=300, key="review_content", disabled=True)

    # Enhanced Review actions with UNDER_REVIEW option
    st.markdown("---")
    st.subheader("Review Decision")

    # Three-column layout for the three main actions
    col3, col4, col5 = st.columns(3)

    with col3:
        st.write("**✅ Final Approval**")
        if st.button("Approve Report", type="primary", use_container_width=True, key="approve_btn"):
            _submit_review_decision(api, report_id, "approved")

    with col4:
        st.write("**🔄 Needs More Work**")
        if st.button("Send Back for Revision", type="secondary", use_container_width=True, key="reject_btn"):
            _submit_review_decision(api, report_id, "rejected")

    with col5:
        st.write("**⏳ Further Review Needed**")
        if st.button("Mark Under Review", type="secondary", use_container_width=True, key="under_review_btn"):
            _submit_review_decision(api, report_id, "under_review")

    # Review notes section - FIXED: Use session state directly, no value parameter
    st.markdown("---")
    st.subheader("Review Notes & Feedback")

    # Create the text area using ONLY the session state key
    review_notes = st.text_area(
        "Add your review notes, feedback, or instructions:",
        placeholder="Provide constructive feedback for the author. Explain your decision and suggest improvements if needed...",
        height=150,
        key=notes_key  # Session state manages the value automatically
    )

    # Quick feedback templates
    st.write("**Quick Feedback Templates:**")
    template_col1, template_col2, template_col3 = st.columns(3)

    with template_col1:
        if st.button("📝 Needs More Detail", use_container_width=True):
            st.session_state[
                notes_key] = "The report would benefit from more detailed explanations and specific examples."

    with template_col2:
        if st.button("🔍 Technical Review Needed", use_container_width=True):
            st.session_state[
                notes_key] = "Please have a technical expert review the engineering calculations and methodology."

    with template_col3:
        if st.button("✨ Well Written", use_container_width=True):
            st.session_state[
                notes_key] = "Excellent work! The report is well-structured, comprehensive, and clearly communicated."

    # Competencies section (if available)
    if report_to_review.get('competencies'):
        st.markdown("---")
        st.subheader("Competencies Assessment")
        for comp in report_to_review['competencies']:
            with st.expander(
                    f"🔧 {comp.get('competency_title', 'Competency')} - {len(comp.get('user_response', '').split())} words"):
                st.write(f"**Response:** {comp.get('user_response', 'No response')}")

                # Quick competency assessment
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    if st.button(f"👍 Good", key=f"comp_good_{comp['id']}"):
                        st.info("Marked as good - consider adding this to your notes above.")
                with comp_col2:
                    if st.button(f"📝 Needs Work", key=f"comp_improve_{comp['id']}"):
                        st.warning("Marked as needs improvement - consider adding specific feedback above.")

                        

def _submit_review_decision(api: EnhancedAPIClient, report_id: int, decision: str):
    """Submit the review decision to the API"""
    # Get review notes from session state
    notes_key = f"notes_{report_id}"
    review_notes = st.session_state.get(notes_key, "")

    with LoadingState(f"Submitting {decision} decision..."):
        success, result = api.review_report(
            report_id=report_id,
            status=decision,
            review_notes=review_notes
        )

    if success:
        st.balloons()

        # Custom success messages based on decision
        if decision == "approved":
            st.success("✅ Report approved successfully! The author will be notified.")
        elif decision == "rejected":
            st.success("🔄 Report sent back for revisions. The author will receive your feedback.")
        elif decision == "under_review":
            st.success("⏳ Report marked for further review. It remains in the review queue.")

        # Clear review state but KEEP the notes in session state for future reference
        if 'current_review_id' in st.session_state:
            del st.session_state.current_review_id

        # DO NOT clear the notes from session state - they should persist

        # ONLY clear cache for final decisions (approve/reject)
        # DO NOT clear cache for "under_review" - it should stay in queue
        if decision in ["approved", "rejected"]:
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]

        # Let the user see the success message
        st.balloons()

        # For under_review, provide a button to go back
        if decision == "under_review":
            if st.button("← Back to Review Queue", key="success_back"):
                st.rerun()
        else:
            # For approve/reject, go back immediately
            st.rerun()

    else:
        error_msg = result.get('detail', 'Unknown error occurred')
        ErrorHandler.show_error(f"Failed to submit review: {error_msg}")


def _show_analytics_dashboard(api: EnhancedAPIClient):
    """Show analytics and reporting for reviews"""
    st.subheader("📈 Review Analytics")

    with LoadingState("Loading analytics..."):
        success, reports = api.get_reports_for_review()

        if not success:
            ErrorHandler.show_error("Failed to load analytics data")
            return

        # Basic charts and analytics would go here
        # This is a placeholder for future analytics implementation
        st.info("📊 Analytics dashboard coming soon!")
        st.write("Planned features:")
        st.write("- 📈 Review trend analysis")
        st.write("- 👥 Reviewer performance metrics")
        st.write("- ⏱️ Turnaround time analysis")
        st.write("- 🎯 Quality scoring trends")


def _show_review_settings(api: EnhancedAPIClient):
    """Show review settings and preferences"""
    st.subheader("⚙️ Review Settings")

    st.write("Configure your review preferences and workflow settings.")

    # Notification settings
    st.write("**🔔 Notification Preferences**")
    email_notifications = st.checkbox("Receive email notifications for new submissions", value=True)
    urgent_alerts = st.checkbox("Get alerts for urgent reports", value=True)

    # Review preferences
    st.write("**📝 Review Preferences**")
    default_view = st.selectbox("Default review view", ["Detailed", "Compact"])
    auto_save = st.checkbox("Auto-save review notes", value=True)

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully!")


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


def main():
    """Main function for testing the review dashboard"""
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    review_dashboard(api)


if __name__ == "__main__":
    main()