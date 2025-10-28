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

    # ✅ FIX: Clear cache when first loading dashboard
    cache_key = f"reports_for_review_{st.session_state.user_id}"
    if cache_key in st.session_state:
        del st.session_state[cache_key]

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


def _show_erb_stage_progression(api: EnhancedAPIClient, report: Dict):
    """Show ERB stage progression interface with SINGLE text area"""

    # Define ERB stages in order - this is the single source of truth
    erb_stages = [
        {"stage": "desktop_assessment", "name": "Desktop Assessment",
         "description": "Administrative completeness check"},
        {"stage": "standard_review", "name": "Standard Review", "description": "Technical compliance assessment"},
        {"stage": "professional_assessment", "name": "Professional Assessment",
         "description": "Depth & quality evaluation"},
        {"stage": "professional_review", "name": "Professional Review",
         "description": "Final validation & interview decision"}
    ]

    # Get current stage - reports now properly start at desktop_assessment
    current_stage = report.get('erb_stage', 'desktop_assessment')
    current_status = report.get('current_stage_status', 'not_started')

    # Show progression timeline
    st.write("### 📋 Report Assessment Progress")

    # Create columns for each stage
    cols = st.columns(len(erb_stages))

    for i, stage_info in enumerate(erb_stages):
        stage = stage_info["stage"]
        with cols[i]:
            # Determine stage status
            stage_index = _get_erb_stage_index(erb_stages, stage)
            current_index = _get_erb_stage_index(erb_stages, current_stage)

            if stage_index < current_index:
                # Stage is completed
                status_emoji = "✅"
                status_color = "success"
            elif stage_index == current_index:
                # Current stage
                if current_status == 'completed':
                    status_emoji = "✅"
                    status_color = "success"
                else:
                    status_emoji = "🔍"
                    status_color = "warning"
            else:
                # Future stage
                status_emoji = "⏳"
                status_color = "secondary"

            # Display stage card
            if status_color == "success":
                st.success(f"{status_emoji} {stage_info['name']}")
            elif status_color == "warning":
                st.warning(f"{status_emoji} {stage_info['name']}")
            else:
                st.info(f"{status_emoji} {stage_info['name']}")

            st.caption(stage_info['description'])

    st.markdown("---")

    # SINGLE TEXT AREA for the entire timeline
    st.write("### 📝 Assessment Timeline")

    # Use separate keys: one for widget, one for storage
    timeline_key = f"timeline_{report['id']}"
    widget_key = f"timeline_widget_{report['id']}"

    # Initialize timeline in session state if not exists
    if timeline_key not in st.session_state:
        # Use existing notes or start with current stage marker
        existing_notes = report.get('review_notes', '')
        if existing_notes:
            st.session_state[timeline_key] = existing_notes
        else:
            # Start with current stage marker
            current_stage_name = current_stage.upper().replace('_', ' ')
            st.session_state[timeline_key] = f"--- ERB STAGE: {current_stage_name} ---\n"

    # Editable timeline text area - uses widget key
    timeline_notes = st.text_area(
        "Assessment Notes & Timeline",
        value=st.session_state[timeline_key],  # Initial value from storage key
        placeholder="Write your assessment notes under each stage marker...",
        height=300,
        key=widget_key  # Different key for the widget
    )

    # Sync widget value back to storage key on change
    if timeline_notes != st.session_state[timeline_key]:
        st.session_state[timeline_key] = timeline_notes

    st.markdown("---")

    # Stage progression controls
    st.write("### 🚀 Stage Actions")

    current_index = _get_erb_stage_index(erb_stages, current_stage)

    # Show controls for current stage
    if current_index < len(erb_stages):
        current_stage_info = erb_stages[current_index]

        st.write(f"**Current Stage:** {current_stage_info['name']}")
        st.write(f"**Status:** {current_status.replace('_', ' ').title()}")
        st.write(f"**Description:** {current_stage_info['description']}")

        # Clean button logic - no debug output
        if current_status != 'completed':
            # Show Complete Current Stage button
            if st.button("✅ Complete Current Stage", type="primary", use_container_width=True,
                         key=f"complete_{report['id']}"):
                if _progress_to_stage(api, report['id'], current_stage, "completed"):
                    st.success(f"✅ {current_stage_info['name']} completed!")
                    st.rerun()
        else:
            if current_index < len(erb_stages) - 1:
                # Show Start Next Stage button
                next_stage_info = erb_stages[current_index + 1]
                if st.button(f"➡️ Start {next_stage_info['name']}", type="primary", use_container_width=True,
                             key=f"start_{report['id']}"):
                    # Auto-add next stage marker to timeline
                    _add_stage_marker_to_timeline(report['id'], next_stage_info['stage'])
                    if _progress_to_stage(api, report['id'], next_stage_info['stage'], "in_progress"):
                        st.success(f"🚀 Started {next_stage_info['name']}!")
                        st.rerun()
            else:
                # FINAL STAGE
                if st.session_state.get('final_decision_report') != report['id']:
                    if st.button("🎯 Make Final Decision", type="primary", use_container_width=True,
                                 key=f"final_{report['id']}"):
                        _add_final_decision_marker(report['id'])
                        st.session_state.final_decision_report = report['id']
                        st.rerun()
                else:
                    # Show approve/reject buttons
                    st.write("**Final Decision:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("✅ Approve Registration", type="primary", use_container_width=True,
                                     key=f"approve_{report['id']}"):
                            if _progress_to_stage(api, report['id'], "approved", "completed"):
                                st.balloons()
                                st.success("🎉 Registration Approved!")
                                if 'final_decision_report' in st.session_state:
                                    del st.session_state.final_decision_report
                                st.rerun()

                    with col2:
                        if st.button("❌ Reject Registration", type="secondary", use_container_width=True,
                                     key=f"reject_{report['id']}"):
                            if _progress_to_stage(api, report['id'], "rejected", "completed"):
                                st.success("📋 Registration Rejected")
                                if 'final_decision_report' in st.session_state:
                                    del st.session_state.final_decision_report
                                st.rerun()


def _add_stage_marker_to_timeline(report_id: int, stage: str):
    """Auto-add stage marker to the timeline (for next stages)"""
    timeline_key = f"timeline_{report_id}"
    if timeline_key in st.session_state:
        current_timeline = st.session_state[timeline_key]
        stage_marker = f"\n\n--- ERB STAGE: {stage.upper()} ---\n"

        # Add stage marker if not already present
        if stage_marker.strip() not in current_timeline:
            st.session_state[timeline_key] = current_timeline + stage_marker
            # Force a rerun to update the widget
            st.rerun()


def _add_final_decision_marker(report_id: int):
    """Auto-add final decision marker to the timeline"""
    timeline_key = f"timeline_{report_id}"
    if timeline_key in st.session_state:
        current_timeline = st.session_state[timeline_key]
        decision_marker = f"\n\n--- FINAL DECISION ---\n"

        # Add decision marker if not already present
        if decision_marker.strip() not in current_timeline:
            st.session_state[timeline_key] = current_timeline + decision_marker
            st.rerun()


def _get_erb_stage_index(erb_stages: List[Dict], stage: str) -> int:
    """Get index of ERB stage within the defined stages list"""
    for i, stage_info in enumerate(erb_stages):
        if stage_info["stage"] == stage:
            return i
    return 0


def _progress_to_stage(api: EnhancedAPIClient, report_id: int, next_stage: str, status: str = "in_progress"):
    """Progress report to specified ERB stage with proper notes formatting"""

    # Get timeline content from session state
    timeline_key = f"timeline_{report_id}"
    final_notes = st.session_state.get(timeline_key, "")

    with LoadingState(f"Progressing to {next_stage}..."):
        success, result = api.progress_erb_stage(report_id, next_stage, final_notes, status)

    if success:
        # Clear cache to refresh data
        cache_key = f"reports_for_review_{st.session_state.user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        return True
    else:
        error_msg = f"Failed to progress stage: {result.get('detail', 'Unknown error')}"
        ErrorHandler.show_error(error_msg)
        return False


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
        success, response = api.get_all_reports_paginated(limit=1000)
        if success and isinstance(response, dict) and 'reports' in response:
            all_reports = response.get('reports', [])
        else:
            all_reports = []

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

        # ✅ FIXED: Check for None dates before comparison
        your_reviews_today = len([r for r in all_reports
                                  if r.get('reviewed_by') == st.session_state.user_id
                                  and _parse_date(r.get('reviewed_at')) is not None
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
    """Parse date string to datetime object, return None if invalid"""
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
def get_cached_reports_for_review(api: EnhancedAPIClient):
    """Cache reports for review to prevent repeated API calls"""
    return api.get_reports_for_review()


def _show_reviewer_dashboard(api: EnhancedAPIClient):
    """Show the enhanced review queue interface"""
    st.subheader("📝 Review Queue")

    # ✅ FIX: Add refresh button at the top
    col_refresh, col_space = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_queue", help="Refresh the review queue with latest data"):
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()

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
        cache_key = f"reports_for_review_{st.session_state.user_id}"

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
    """Display an enhanced report card in the queue with assignment status"""
    # Define ERB stages for consistent display
    erb_stages = [
        {"stage": "desktop_assessment", "name": "Desktop Assessment"},
        {"stage": "standard_review", "name": "Standard Review"},
        {"stage": "professional_assessment", "name": "Professional Assessment"},
        {"stage": "professional_review", "name": "Professional Review"}
    ]

    # Get current stage - reports now properly initialized
    current_erb_stage = report.get('erb_stage', 'desktop_assessment')

    # Find stage display name
    stage_display_name = "Desktop Assessment"  # Default
    for stage_info in erb_stages:
        if stage_info["stage"] == current_erb_stage:
            stage_display_name = stage_info["name"]
            break

    # Get report assignment info
    current_user_id = st.session_state.user_id
    assigned_reviewer_id = report.get('reviewed_by')
    assigned_reviewer_name = report.get('reviewer_full_name') or report.get('reviewer_username', 'Another Reviewer')
    is_assigned_to_me = assigned_reviewer_id == current_user_id
    is_assigned_to_other = assigned_reviewer_id and not is_assigned_to_me
    user_role = st.session_state.get('user_role', '')
    is_admin = user_role == 'admin'

    # Rest of your existing card display logic...
    is_urgent = _is_urgent_report(report)
    status = report.get('status', 'submitted')
    days_old = _get_days_old(report)

    # Create a visually distinct card with different styling based on assignment
    card_style = ""
    if is_assigned_to_me:
        card_style = "border: 2px solid #10B981; background-color: #F0FDF4;"
    elif is_assigned_to_other:
        card_style = "border: 1px solid #6B7280; background-color: #F9FAFB; opacity: 0.7;"
    else:
        card_style = "border: 1px solid #E5E7EB; background-color: white;"

    with st.container():
        st.markdown(f'<div style="{card_style} padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">',
                    unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Title with ERB stage indicator
            stage_emoji = {
                'desktop_assessment': '📄',
                'standard_review': '🔍',
                'professional_assessment': '⭐',
                'professional_review': '🎯',
                'approved': '✅',
                'rejected': '❌'
            }.get(current_erb_stage, '📝')

            st.write(f"**{stage_emoji} {report['title']}**")
            st.write(f"📈 **Assessment Stage:** {stage_display_name}")

            # Show assignment status
            if is_assigned_to_me:
                st.success(f"👤 **Assigned to:** You")
            elif is_assigned_to_other:
                st.warning(f"👤 **Assigned to:** {assigned_reviewer_name}")
            else:
                st.info("👤 **Assigned to:** Available for review")

            # Rest of your existing column 1 content...
            st.write(
                f"👤 **Author:** {report.get('owner_full_name', 'Unknown')} ({report.get('owner_username', 'N/A')})")
            st.write(f"📅 **Submitted:** {_format_date(report.get('submitted_at'))} ({days_old} days ago)")
            st.write(
                f"📊 **Words:** {len(report.get('content', '').split())} | **Competencies:** {len(report.get('competencies', []))}")

            # Quick preview
            content_preview = report.get('content', '')[:150] + "..." if len(
                report.get('content', '')) > 150 else report.get('content', '')
            with st.expander("Preview content"):
                st.write(content_preview)

        with col2:
            if is_urgent:
                st.error("🚨 URGENT")
            else:
                st.info("Normal Priority")

            if is_assigned_to_me:
                st.success("🔍 **Under Your Review**")
            elif is_assigned_to_other:
                st.warning(f"🔍 **Under Review by {assigned_reviewer_name}**")
            else:
                st.info("📝 **Submitted**")

            if days_old > 7:
                st.error(f"⏳ {days_old} days old")

        with col3:
            # Button logic based on assignment
            if is_assigned_to_me:
                # Current reviewer - can continue review
                if st.button("🔍 Continue Review", key=f"review_{report['id']}", use_container_width=True):
                    st.session_state.current_review_id = report['id']
                    cache_key = f"reports_for_review_{st.session_state.user_id}"
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    st.rerun()

                # Release button for current reviewer
                if st.button("🔓 Release Report", key=f"release_{report['id']}", use_container_width=True):
                    _release_report(api, report['id'])

            elif is_assigned_to_other:
                # Assigned to another reviewer - show disabled button
                st.button("🔒 Claimed", key=f"claimed_{report['id']}",
                          use_container_width=True, disabled=True)

                # Admin can release reports from other reviewers
                if is_admin:
                    if st.button("🔓 Release (Admin)", key=f"admin_release_{report['id']}",
                                 use_container_width=True):
                        _release_report(api, report['id'])
            else:
                # Available for claiming
                if st.button("⏳ Claim Report", key=f"claim_{report['id']}", use_container_width=True):
                    _claim_report(api, report['id'])

        st.markdown('</div>', unsafe_allow_html=True)


def _claim_report(api: EnhancedAPIClient, report_id: int):
    """Claim a report for review (assign to current user without changing status)"""
    lock_name = f"claim_report_{report_id}"
    if not _acquire_lock(lock_name):
        return

    try:
        with LoadingState("Claiming report for review..."):
            # Call API to assign reviewer without changing status or adding notes
            success, result = api.assign_reviewer(report_id, st.session_state.user_id)

        if success:
            st.success("✅ Report claimed successfully! You can now start your review.")
            # Clear cache to refresh data
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()
        else:
            error_msg = result.get('detail', 'Unknown error occurred')
            ErrorHandler.show_error(f"Failed to claim report: {error_msg}")
    finally:
        _release_lock(lock_name)


def _release_report(api: EnhancedAPIClient, report_id: int):
    """Release a report from review (remove assignment)"""
    lock_name = f"release_report_{report_id}"
    if not _acquire_lock(lock_name):
        return

    try:
        with LoadingState("Releasing report..."):
            # Call API to remove reviewer assignment
            success, result = api.assign_reviewer(report_id, None)

        if success:
            st.success("✅ Report released successfully! It's now available for other reviewers.")
            # Clear cache to refresh data
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()
        else:
            error_msg = result.get('detail', 'Unknown error occurred')
            ErrorHandler.show_error(f"Failed to release report: {error_msg}")
    finally:
        _release_lock(lock_name)


def _get_days_old(report: Dict) -> int:
    """Calculate how many days old a report is"""
    submitted_date = _parse_date(report.get('submitted_at'))
    if not submitted_date:
        return 0

    return (datetime.now() - submitted_date).days


def _show_review_interface(api: EnhancedAPIClient, report_id: int, pending_reports: List[Dict]):
    """Display the enhanced review interface with access control"""
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

    # Check if current user is the assigned reviewer or admin
    current_user_id = st.session_state.user_id
    assigned_reviewer_id = report_to_review.get('reviewed_by')
    user_role = st.session_state.get('user_role', '')
    is_admin = user_role == 'admin'
    is_assigned_reviewer = assigned_reviewer_id == current_user_id

    if not is_assigned_reviewer and not is_admin:
        st.error(
            "🔒 This report is currently assigned to another reviewer. You cannot access the full review interface.")
        if st.button("← Back to Review Queue"):
            if 'current_review_id' in st.session_state:
                del st.session_state.current_review_id
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

    # Show assignment info
    if is_admin and assigned_reviewer_id and not is_assigned_reviewer:
        assigned_reviewer_name = report_to_review.get('reviewer_full_name') or report_to_review.get('reviewer_username',
                                                                                                    'Unknown')
        st.warning(f"🔍 **Admin View**: This report is assigned to {assigned_reviewer_name}")

    # Enhanced report details in columns
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Report Details**")
        st.write(f"🏷️ **ID:** {report_to_review['id']}")
        st.write(f"👤 **Author:** {report_to_review.get('owner_full_name', 'Unknown')}")
        st.write(f"✒️ **Username:** {report_to_review.get('owner_username', 'N/A')}")
        st.write(f"📨 **Email:** {report_to_review.get('owner_email', 'No email')}")

        # Status with visual indicator
        status = report_to_review.get('status', 'unknown')

        # Define assigned_reviewer_name for status display
        assigned_reviewer_name = report_to_review.get('reviewer_full_name') or report_to_review.get('reviewer_username',
                                                                                                    'Another Reviewer')

        if status == 'submitted':
            st.info(f"**Status:** 📝 Submitted")
        elif status == 'under_review':
            if is_assigned_reviewer:
                st.success(f"**Status:** 🔍 Under Your Review")
            else:
                st.warning(f"**Status:** 🔍 Under Review by {assigned_reviewer_name}")

    with col2:
        st.write("**Statistics**")
        st.write(f"📊 **Word Count:** {len(report_to_review.get('content', '').split())}")
        st.write(f"📝 **Created:** {_format_date(report_to_review.get('created_at'))}")
        if report_to_review.get('updated_at'):
            st.write(f"**Last Updated:** {_format_date(report_to_review.get('updated_at'))}")

        # Urgency indicator
        if _is_urgent_report(report_to_review):
            st.error("🚨 **This report is marked as URGENT**")

        # Age indicator
        days_old = _get_days_old(report_to_review)
        if days_old > 7:
            st.warning(f"⏳ **This report is {days_old} days old**")

        # Release button for assigned reviewer and admin
        if is_assigned_reviewer or is_admin:
            if st.button("🔓 Release Report", key="release_from_review"):
                _release_report(api, report_id)

    # Report content
    st.markdown("---")
    st.subheader("Report Content")
    st.text_area("Content", report_to_review.get('content', ''), height=300, key="review_content", disabled=True)

    # Enhanced Review actions - REMOVED the "Mark Under Review" button from full view
    st.markdown("---")
    st.subheader("Review Decision")

    # Two-column layout for the main actions (removed under_review button)
    col3, col4 = st.columns(2)

    with col3:
        st.write("**✅ Final Approval**")
        if st.button("Approve Report", type="primary", use_container_width=True, key="approve_btn"):
            _submit_review_decision(api, report_id, "approved")

    with col4:
        st.write("**🔄 Needs More Work**")
        if st.button("Send Back for Revision", type="secondary", use_container_width=True, key="reject_btn"):
            _submit_review_decision(api, report_id, "rejected")

    st.markdown("---")

    # The single timeline text area is now in _show_erb_stage_progression
    _show_erb_stage_progression(api, report_to_review)

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
    # Use a lock to prevent duplicate calls
    lock_key = f"decision_lock_{report_id}"
    if lock_key in st.session_state and st.session_state[lock_key]:
        return

    st.session_state[lock_key] = True

    try:
        # Get review notes from session state
        notes_key = f"notes_{report_id}"
        timeline_key = f"timeline_{report_id}"

        review_notes = st.session_state.get(notes_key, "")
        current_timeline = st.session_state.get(timeline_key, "")

        # Only add notes to timeline if they are not empty
        if review_notes.strip():
            reviewer_name = st.session_state.get('user_full_name', 'Reviewer')

            # Format the new notes entry for final decisions
            if decision in ["approved", "rejected"]:
                stage_marker = "FINAL DECISION"
                new_entry = f"--- {stage_marker} ---\n{review_notes.strip()}\nReview done by {reviewer_name}"
            else:
                stage_marker = "STAGE NOTES"
                new_entry = f"--- {stage_marker} ---\n{review_notes.strip()}\nReview done by {reviewer_name}"

            # Add to timeline with proper separation
            if current_timeline and not current_timeline.startswith("Report/Reviewer's assessment notes"):
                updated_timeline = current_timeline + "\n\n" + new_entry
            else:
                updated_timeline = new_entry

            st.session_state[timeline_key] = updated_timeline

        # Get the final timeline content for submission
        final_notes = st.session_state.get(timeline_key, "")

        with LoadingState(f"Submitting {decision} decision..."):
            success, result = api.review_report(
                report_id=report_id,
                status=decision,
                review_notes=final_notes
            )

        if success:
            st.balloons()

            if decision == "approved":
                st.success("✅ Report approved successfully! The author will be notified.")
            elif decision == "rejected":
                st.success("🔄 Report sent back for revisions. The author will receive your feedback.")
            elif decision == "under_review":
                st.success("⏳ Report marked for further review. It remains in the review queue.")

            # Clear input notes but keep timeline
            st.session_state[notes_key] = ""

            # Clear review state
            if 'current_review_id' in st.session_state:
                del st.session_state.current_review_id

            # Clear cache
            cache_key = f"reports_for_review_{st.session_state.user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]

            if decision == "under_review":
                if st.button("← Back to Review Queue", key="success_back"):
                    st.rerun()
            else:
                st.rerun()

        else:
            error_msg = result.get('detail', 'Unknown error occurred')
            ErrorHandler.show_error(f"Failed to submit review: {error_msg}")
    finally:
        st.session_state[lock_key] = False


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

    # Remove unused variables and simplify settings
    st.info("Settings functionality coming soon!")

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully!")


def _format_date(date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return ""

    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


# GLOBAL LOCK SYSTEM to prevent duplicate executions
def _acquire_lock(lock_name: str) -> bool:
    """Acquire a global lock to prevent duplicate executions"""
    lock_key = f"global_lock_{lock_name}"
    if lock_key in st.session_state and st.session_state[lock_key]:
        return False
    st.session_state[lock_key] = True
    return True


def _release_lock(lock_name: str):
    """Release a global lock"""
    lock_key = f"global_lock_{lock_name}"
    if lock_key in st.session_state:
        del st.session_state[lock_key]


def main():
    """Main function for testing the review dashboard"""
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    review_dashboard(api)


if __name__ == "__main__":
    main()