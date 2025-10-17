import streamlit as st
import pandas as pd
from datetime import datetime
from services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState


def show_dashboard(api: EnhancedAPIClient):
    """Enhanced Dashboard - Personal Reporting Hub for Regular Users"""

    # Apply custom CSS for elegant styling
    apply_dashboard_styles()

    # Section 1: Header with Personal Welcome & Quick Stats
    show_dashboard_header(api)

    # Section 2: Key Metrics Cards
    show_metrics_cards(api)

    # Section 3: Reports Status Overview with Insights
    show_status_overview(api)


def apply_dashboard_styles():
    """Apply elegant CSS styling for the dashboard"""
    st.markdown("""
    <style>
    /* Dashboard Container */
    .dashboard-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
    }

    /* Header Section */
    .dashboard-header {
        background: linear-gradient(135deg, #1f3a60 0%, #4a6fa5 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(31, 58, 96, 0.15);
    }

    .welcome-text {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .user-stats {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 0.25rem;
    }

    /* Metrics Cards */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    @media (max-width: 1200px) {
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .metrics-grid {
            grid-template-columns: 1fr;
        }
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        border-left: 5px solid;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        text-align: center;
        backdrop-filter: blur(10px);
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .metric-card-total { border-left-color: #1f3a60; }
    .metric-card-submitted { border-left-color: #f39c12; }
    .metric-card-approved { border-left-color: #27ae60; }
    .metric-card-draft { border-left-color: #95a5a6; }

    .metric-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }

    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1f3a60;
        margin: 0.5rem 0;
    }

    .metric-label {
        font-size: 1.1rem;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Status Overview Section */
    .status-overview {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3498db;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f3a60;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .status-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    @media (max-width: 768px) {
        .status-grid {
            grid-template-columns: 1fr;
        }
    }

    .status-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        background: #f8f9fa;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
    }

    .status-item:hover {
        background: #e9ecef;
        transform: translateX(5px);
    }

    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .status-draft { background: #95a5a6; color: white; }
    .status-submitted { background: #f39c12; color: white; }
    .status-approved { background: #27ae60; color: white; }
    .status-rejected { background: #e74c3c; color: white; }

    .insights-section {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 1.5rem;
    }

    .insight-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
        font-size: 1.05rem;
    }

    .progress-bar {
        height: 8px;
        background: #e9ecef;
        border-radius: 10px;
        margin: 1rem 0;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #3498db, #1f3a60);
        transition: width 0.5s ease;
    }
    </style>
    """, unsafe_allow_html=True)


def show_dashboard_header(api: EnhancedAPIClient):
    """Display personalized header with user info fetched from API"""

    # Fetch current user data from API
    with LoadingState("Loading your profile..."):
        success, user_data = api.get_current_user()

        if not success:
            ErrorHandler.show_warning("Could not load user profile data")
            # Fallback to session state data
            user_data = st.session_state.get('user_data', {})
        else:
            # Store the fetched user data in session state for consistency
            st.session_state['user_data'] = user_data

    # Extract user information with proper fallbacks
    username = user_data.get('username', 'User')

    # Get full name - prefer full_name, then fallback to username
    full_name = user_data.get('full_name') or username

    # Get role - from session state (set during login) or user_data
    user_role = st.session_state.get('user_role') or user_data.get('role', 'user')
    user_role_display = user_role.title() if user_role else 'User'

    # Get email - from user_data
    email = user_data.get('email', 'No email available')

    # Get last login time
    last_login = st.session_state.get('last_login', datetime.now().strftime("%Y-%m-%d %H:%M"))

    st.markdown(f"""
    <div class="dashboard-header">
        <div class="welcome-text">👋 Welcome back, {full_name}!</div>
        <div class="user-stats">📅 Last login: {last_login}</div>
        <div class="user-stats">🎯 Role: {user_role_display}</div>
         <div class="user-stats">📧 Email: {email}</div>
    </div>
    """, unsafe_allow_html=True)


def show_metrics_cards(api: EnhancedAPIClient):
    """Display key metrics cards in an elegant grid using Streamlit components"""

    # Fetch user's reports data
    with LoadingState("Loading your reporting metrics..."):
        success, reports = api.fetch_reports()

        if not success:
            ErrorHandler.show_error("Failed to load reports data")
            return

        # Calculate metrics
        total_reports = len(reports)
        submitted_reports = len([r for r in reports if r.get('status') == 'submitted'])
        approved_reports = len([r for r in reports if r.get('status') == 'approved'])
        draft_reports = len([r for r in reports if r.get('status') == 'draft'])

    # Create metrics cards using Streamlit columns and markdown
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card metric-card-total">
            <div class="metric-icon">📈</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Total Reports</div>
        </div>
        """.format(total_reports), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card metric-card-submitted">
            <div class="metric-icon">📤</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Submitted</div>
        </div>
        """.format(submitted_reports), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card metric-card-approved">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Approved</div>
        </div>
        """.format(approved_reports), unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card metric-card-draft">
            <div class="metric-icon">📝</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Draft</div>
        </div>
        """.format(draft_reports), unsafe_allow_html=True)


def show_status_overview(api: EnhancedAPIClient):
    """Display reports status overview with insights"""

    # Fetch reports data
    with LoadingState("Analyzing your reporting status..."):
        success, reports = api.fetch_reports()

        if not success:
            ErrorHandler.show_error("Failed to load reports data")
            return

        # Calculate status distribution
        status_counts = {
            'draft': len([r for r in reports if r.get('status') == 'draft']),
            'submitted': len([r for r in reports if r.get('status') == 'submitted']),
            'approved': len([r for r in reports if r.get('status') == 'approved']),
            'rejected': len([r for r in reports if r.get('status') == 'rejected']),
            'under_review': len([r for r in reports if r.get('status') == 'under_review'])
        }

        total_reports = len(reports)

        # Calculate insights
        if total_reports > 0:
            in_progress_reports = status_counts['submitted'] + status_counts['under_review'] + status_counts['approved']
            progress_percentage = (in_progress_reports / total_reports) * 100
            approved_rate = (status_counts['approved'] / total_reports * 100) if total_reports > 0 else 0
        else:
            progress_percentage = 0
            approved_rate = 0
            in_progress_reports = 0

    # Now these variables are available in the function scope
    st.markdown("""
    <div class="status-overview">
        <div class="section-title">📋 Reports Status Distribution</div>
    """, unsafe_allow_html=True)

    # Status distribution grid
    st.markdown("""
    <div class="status-grid">
        <div>
            <div class="status-item">
                <span>🟢 Draft Reports</span>
                <span class="status-badge status-draft">{draft}</span>
            </div>
            <div class="status-item">
                <span>🟡 Submitted</span>
                <span class="status-badge status-submitted">{submitted}</span>
            </div>
            <div class="status-item">
                <span>🔵 Under Review</span>
                <span class="status-badge status-submitted">{under_review}</span>
            </div>
        </div>
        <div>
            <div class="status-item">
                <span>✅ Approved</span>
                <span class="status-badge status-approved">{approved}</span>
            </div>
            <div class="status-item">
                <span>🔴 Rejected</span>
                <span class="status-badge status-rejected">{rejected}</span>
            </div>
            <div class="status-item">
                <span>📊 Total</span>
                <span class="status-badge" style="background: #1f3a60; color: white;">{total}</span>
            </div>
        </div>
    </div>
    """.format(
        draft=status_counts['draft'],
        submitted=status_counts['submitted'],
        under_review=status_counts['under_review'],
        approved=status_counts['approved'],
        rejected=status_counts['rejected'],
        total=total_reports
    ), unsafe_allow_html=True)

    # Progress visualization
    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600;">Overall Progress</span>
            <span style="font-weight: 600; color: #1f3a60;">{progress_percentage:.0f}%</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_percentage}%;"></div>
        </div>
        <div style="text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 0.5rem;">
            {in_progress_reports} of {total_reports} reports in review/approved status
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Insights - Use Streamlit components instead of raw HTML
    st.markdown("""
    <div class="insights-section">
        <div style="font-weight: 600; margin-bottom: 1rem; color: #1f3a60;">⚡ Quick Insights</div>
    </div>
    """, unsafe_allow_html=True)

    # Create insights using Streamlit components
    col1, col2 = st.columns([1, 20])
    with col1:
        st.markdown("📈")
    with col2:
        st.markdown(f"**{progress_percentage:.0f}%** of your reports are in review/approved status")

    col1, col2 = st.columns([1, 20])
    with col1:
        st.markdown("📝")
    with col2:
        draft_plural = "" if status_counts['draft'] == 1 else "s"
        st.markdown(f"You have **{status_counts['draft']}** draft{draft_plural} ready for submission")

    col1, col2 = st.columns([1, 20])
    with col1:
        st.markdown("⭐")
    with col2:
        st.markdown(f"Your approval rate: **{approved_rate:.0f}%**")

    col1, col2 = st.columns([1, 20])
    with col1:
        st.markdown("🎯" if status_counts['rejected'] == 0 else "⚠️")
    with col2:
        if status_counts['rejected'] == 0:
            st.markdown("Great work! No rejected reports")
        else:
            rejection_plural = "" if status_counts['rejected'] == 1 else "s"
            st.markdown(f"You have **{status_counts['rejected']}** rejected report{rejection_plural} needing attention")

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function to run the enhanced dashboard"""
    api = EnhancedAPIClient()
    if st.session_state.get('token'):
        api.set_token(st.session_state.token)
    show_dashboard(api)


if __name__ == "__main__":
    main()