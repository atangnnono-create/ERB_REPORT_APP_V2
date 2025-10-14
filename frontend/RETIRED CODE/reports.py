import streamlit as st
import requests
import json
from frontend.services.api_client import APIClient

API_BASE_URL = "http://127.0.0.1:8000"


def fetch_reports(token: str):
    """Fetch all reports for the currently logged-in user using Bearer token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/api/v1/reports/", headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"❌ Failed to fetch reports: {resp.text}")
            return []
    except Exception as e:
        st.error(f"⚠️ Backend connection error: {e}")
        return []


def delete_report(report_id: int, token: str):
    """Delete a report by ID using Bearer token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(f"{API_BASE_URL}/api/v1/reports/{report_id}", headers=headers)
        if resp.status_code == 200:
            st.success("🗑️ Report deleted successfully!")
            st.rerun()
        else:
            st.error(f"❌ Failed to delete report: {resp.text}")
    except Exception as e:
        st.error(f"⚠️ Backend connection error: {e}")


def reports_ui(api_client=None):
    """Streamlit UI to display the logged-in user's reports with review workflow."""
    st.set_page_config(page_title="My Reports", layout="centered")

    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to view your reports.")
        return

    token = st.session_state.token
    api = api_client or APIClient()
    api.set_token(token)

    # Fetch user's reports
    reports = fetch_reports(token)

    if not reports:
        st.info("No reports found. Go to **Create Report** to start one.")
        return

    # Display reports with enhanced status information
    for report in reports:
        status_color = {
            "draft": "⚪",
            "submitted": "🟡",
            "under_review": "🔵",
            "approved": "🟢",
            "rejected": "🔴"
        }

        status_icon = status_color.get(report.get('status', 'draft'), '⚪')

        with st.expander(f"{status_icon} {report['title']} (ID: {report['id']})"):
            # Status and metadata
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Status:** {report.get('status', 'draft').title()}")
                st.markdown(f"**Created:** {report.get('created_at', 'N/A')}")
                if report.get('submitted_at'):
                    st.markdown(f"**Submitted:** {report.get('submitted_at')}")

            with col2:
                st.markdown(f"**Competencies:** {len(report.get('competencies', []))}")
                if report.get('reviewed_at'):
                    st.markdown(f"**Reviewed:** {report.get('reviewed_at')}")
                if report.get('review_notes'):
                    st.markdown(f"**Review Notes:** {report.get('review_notes')}")

            st.markdown("---")
            st.write(report.get("content", "No content")[:500] + "..." if len(
                report.get("content", "")) > 500 else report.get("content", "No content"))

            # Action buttons based on status
            status = report.get('status', 'draft')
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if status == "draft":
                    if st.button("📤 Submit for Review", key=f"submit_{report['id']}"):
                        success, result = api.submit_report_for_review(report["id"])
                        if success:
                            st.success("✅ Report submitted for review!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to submit: {result.get('detail', 'Unknown error')}")

                elif status in ["approved", "rejected"]:
                    st.info(f"Report {status.title()}")

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{report['id']}"):
                    delete_report(report["id"], token)

            with col3:
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(report, indent=2),
                    file_name=f"report_{report['id']}.json",
                    mime="application/json",
                    key=f"download_{report['id']}"
                )


def review_dashboard(api: APIClient):
    """Review dashboard for reviewers and admins"""
    st.title("📋 Report Review Dashboard")

    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["submitted", "under_review", "approved", "rejected"],
        index=0
    )

    # Fetch reports for review
    success, reports = api.get_reports_for_review(status_filter)

    if not success:
        st.error(f"Failed to fetch reports: {reports.get('detail', 'Unknown error')}")
        return

    if not reports:
        st.info(f"No reports with status '{status_filter}' found.")
        return

    for report in reports:
        with st.expander(f"📝 {report['title']} (User ID: {report['owner_id']})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Status:** {report.get('status', 'draft').title()}")
                st.write(f"**Submitted:** {report.get('submitted_at', 'N/A')}")
                st.write(f"**Competencies:** {len(report.get('competencies', []))}")
                st.write(f"**Content:** {report.get('content', 'No content')[:300]}...")

            with col2:
                if report.get('status') in ['submitted', 'under_review']:
                    st.subheader("Review Action")

                    review_status = st.selectbox(
                        "Decision",
                        ["approved", "rejected", "under_review"],
                        key=f"decision_{report['id']}"
                    )

                    review_notes = st.text_area(
                        "Review Notes",
                        placeholder="Provide feedback for the user...",
                        key=f"notes_{report['id']}"
                    )

                    if st.button("Submit Review", key=f"review_{report['id']}"):
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

                elif report.get('status') in ['approved', 'rejected']:
                    st.write(f"**Reviewed:** {report.get('reviewed_at', 'N/A')}")
                    if report.get('review_notes'):
                        st.write(f"**Notes:** {report.get('review_notes')}")