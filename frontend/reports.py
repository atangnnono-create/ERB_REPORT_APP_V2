# frontend/reports.py
import streamlit as st
import requests
import json

API_BASE_URL = "https://erb-backend.onrender.com"  # adjust if backend runs elsewhere

# --------------------- Backend API Calls ---------------------
def fetch_reports(token: str):
    """Fetch all reports for the currently logged-in user using Bearer token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/reports/", headers=headers)
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
        resp = requests.delete(f"{API_BASE_URL}/reports/{report_id}", headers=headers)
        if resp.status_code == 200:
            st.success("🗑️ Report deleted successfully!")
            st.rerun()
        else:
            st.error(f"❌ Failed to delete report: {resp.text}")
    except Exception as e:
        st.error(f"⚠️ Backend connection error: {e}")


# --------------------- Reports UI ---------------------
def reports_ui(api_client=None):
    """Streamlit UI to display the logged-in user's reports."""
    st.set_page_config(page_title="My Reports", layout="centered")



    # --------------------- Check Authentication ---------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to view your reports.")
        return

    token = st.session_state.token

    # --------------------- Fetch Reports ---------------------
    reports = fetch_reports(token)

    if not reports:
        st.info("No reports found. Go to **Create Report** to start one.")
        return

    # --------------------- Display Reports ---------------------
    for report in reports:
        with st.expander(f"📝 {report['title']} (ID: {report['id']})"):
            st.markdown(f"**Category:** {report.get('category', 'N/A')}")
            st.markdown(f"**Created At:** {report.get('created_at', 'N/A')}")
            st.markdown("---")
            st.write(report.get("content", "No content"))

            # --------------------- Action Buttons ---------------------
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🗑️ Delete", key=f"delete_{report['id']}"):
                    delete_report(report["id"], token)
            with col2:
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(report, indent=2),
                    file_name=f"report_{report['id']}.json",
                    mime="application/json",
                )


# --------------------- For Local Testing ---------------------
if __name__ == "__main__":
    reports_ui()
