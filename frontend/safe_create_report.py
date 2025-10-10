import streamlit as st
import json
from io import BytesIO
from frontend.utilities.comps import (engineer_competencies,technician_competencies,technologist_competencies)
from frontend.services import ai_service
from frontend.utilities.utils import (
    render_progress_dashboard,
    export_to_docx,
    has_responses,
    sort_keys,
)
from frontend.services.enhanced_api_client import EnhancedAPIClient

api = EnhancedAPIClient()


def create_report_ui():
    st.set_page_config(page_title="📝 Create Report", layout="centered")

    # ---------- Require Login ----------
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to create reports.")
        return
    else:
        api.set_token(st.session_state.token)

    ######## CLEAR AI SUGGESTIONS FUNCTIONS #########
    def clear_competency_suggestions():
        if "suggestion" in st.session_state:
            st.session_state.suggestion = ""

    def clear_full_report_suggestions():
        if "full_feedback" in st.session_state:
            st.session_state.full_feedback = ""

    # ---------- Session Init ----------
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "suggestion" not in st.session_state:
        st.session_state.suggestion = ""
    if "full_feedback" not in st.session_state:
        st.session_state.full_feedback = ""
    if "current_section" not in st.session_state:
        st.session_state.current_section = 0
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "Engineer"
    if "role_selector" not in st.session_state:
        st.session_state.role_selector = st.session_state.selected_role

    # ---------- FILE UPLOADER (runs before radio) ----------
    with st.sidebar:
        uploaded_file = st.file_uploader(
            "⬇️ Load Report 📂",
            type=["json"],
            key="file_loader_report"  # ✅ unique key
        )

        if uploaded_file is not None and st.session_state.get("last_loaded_file") != uploaded_file.name:
            try:
                loaded_responses = json.load(uploaded_file)

                # 🔍 Detect role in the uploaded file
                available_roles = [
                    r for r in ["Engineer", "Engineering Technologist", "Engineering Technician"]
                    if r in loaded_responses
                ]

                if available_roles:
                    # ✅ Auto-switch role
                    st.session_state.role_selector = available_roles[0]
                    st.session_state.selected_role = available_roles[0]

                # ✅ Save raw data for later normalization
                st.session_state.pending_responses = loaded_responses

                # Save filename so it doesn’t re-load infinitely
                st.session_state.last_loaded_file = uploaded_file.name

                st.success(f"Progress preloaded for {st.session_state.selected_role} from {uploaded_file.name}")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading progress: {str(e)}")

    # ---------- Role Selector ----------
    selected_role = st.radio(
        "👷 Select your professional category:",
        ["Engineer", "Engineering Technologist", "Engineering Technician"],
        key="role_selector",
        horizontal=True,
    )

    st.session_state.selected_role = selected_role

    if selected_role == "Engineer":
        competency_sections = engineer_competencies
    elif selected_role == "Engineering Technologist":
        competency_sections = technologist_competencies
    else:
        competency_sections = technician_competencies

    if selected_role not in st.session_state.responses:
        st.session_state.responses[selected_role] = {}

    # ---------- NORMALIZE AFTER competency_sections EXISTS ----------
    if "pending_responses" in st.session_state:
        raw_data = st.session_state.pending_responses
        role = st.session_state.selected_role
        role_data = raw_data.get(role, {})

        for k, v in role_data.items():
            if isinstance(v, dict):
                v.setdefault("title", competency_sections[k]["title"])
                v.setdefault("response", "")
                v.setdefault(
                    "word_count",
                    len(v.get("response", "").split()) if v.get("response") else 0
                )

        st.session_state.responses[role] = role_data
        del st.session_state.pending_responses

    # ---------- MAIN TEXT AREA + SIDEBAR ----------
    role_responses = st.session_state.responses.get(selected_role, {})

    ##### clear AI suggestions and start with first competency when switching roles ####
    if "last_role" not in st.session_state:
        st.session_state.last_role = selected_role
    elif st.session_state.last_role != selected_role:
        st.session_state.current_section = 0
        clear_competency_suggestions()
        clear_full_report_suggestions()
        st.session_state.last_role = selected_role
        st.rerun()

    # ---------- Progress Tracker ----------
    section_keys = sort_keys(list(competency_sections.keys()))
    total_sections = len(section_keys)
    completed_sections = sum(
        1
        for k in section_keys
        if isinstance(st.session_state.responses[selected_role].get(k), dict)
        and st.session_state.responses[selected_role][k].get("response", "").strip()
    )
    progress_ratio = completed_sections / total_sections if total_sections else 0
    st.progress(progress_ratio, text=f"{completed_sections}/{total_sections} completed")

    # ---------- Current Section ----------
    current_index = min(max(st.session_state.current_section, 0), total_sections - 1)
    current_key = section_keys[current_index]
    section = competency_sections[current_key]

    st.subheader(f"Competency {current_index + 1} of {total_sections}: {section['title']}")
    st.info(section["instructions"])

    ###############################################################################################


    # Add status selection to the sidebar or main form
    with st.sidebar:
        st.subheader("📋 Report Status")

        current_status = st.session_state.responses[selected_role].get('_status', 'draft')

        status_options = ["draft", "submitted"]
        status_descriptions = {
            "draft": "💾 Save as draft (you can continue editing later)",
            "submitted": "📤 Submit for review (ready for reviewer assessment)"
        }

        selected_status = st.radio(
            "Report Status:",
            options=status_options,
            format_func=lambda x: status_descriptions[x],
            index=status_options.index(current_status) if current_status in status_options else 0
        )

        st.session_state.responses[selected_role]['_status'] = selected_status

        if selected_status == "submitted":
            st.info("🔔 Your report will be submitted for review and cannot be edited further until reviewed.")

    #############################################################################################################


    user_input = st.text_area(
        "✍️ Your response:",
        value=st.session_state.responses[selected_role].get(current_key, {}).get("response", ""),
        height=300,
        key=f"text_area_{current_key}",
    )

    st.session_state.responses[selected_role][current_key] = {
        "title": section["title"],
        "response": user_input,
        "word_count": len(user_input.split()) if user_input else 0,
    }

    # ---------- Navigation ----------
    col1, col3 = st.columns([6, 1])
    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_section > 0:
            st.session_state.current_section -= 1
            clear_competency_suggestions()
            st.rerun()

    with col3:
        if st.button("Next ➡️") and st.session_state.current_section < total_sections - 1:
            st.session_state.current_section += 1
            clear_competency_suggestions()
            st.rerun()

    st.markdown("---")

    with st.sidebar:
        render_progress_dashboard(competency_sections, selected_role)

    col1, col2 = st.columns(2)
    with col1:
        # ---------- Submit a List of Competencies ----------
        if st.button("🚀 Submit Full Report to Backend"):
            if not has_responses(st.session_state.responses[selected_role]):
                st.warning("No responses to submit.")
            else:
                # Get the selected status
                report_status = st.session_state.responses[selected_role].get('_status', 'draft')
                # Sort keys
                sorted_responses = dict(
                    sorted(st.session_state.responses[selected_role].items(), key=lambda x: x[0])
                )

                # Build payload with competencies
                competencies = []
                for key, v in sorted_responses.items():
                    if key != '_status':  # Exclude status from competencies
                        competencies.append({
                            "competency_key": key,
                            "competency_title": v["title"],
                            "user_response": v["response"],
                        })

                merged_content = "\n\n".join(
                    [f"{c['competency_key']} - {c['competency_title']}\n{c['user_response']}" for c in competencies]
                )

                payload = {
                    "title": f"{selected_role} Report",
                    "content": merged_content,
                    "competencies": competencies,
                    "status": report_status  # ✅ Include status in payload
                }

                success, result = api.create_report(payload)
                if success and "id" in result:
                    st.success(f"Report submitted! ✅ (ID: {result['id']})")

                    # If submitted for review, show additional info
                    if report_status == "submitted":
                        st.info("📨 Your report has been submitted for review. You will be notified when it's reviewed.")

                    # Clear the form if submitted
                    if report_status != "draft":
                        st.session_state.responses[selected_role] = {}
                        st.session_state.current_section = 0
                else:
                    msg = result.get("detail") or str(result)
                    st.error(f"Failed to submit report: {msg}")

    # ---------- Export / Load ----------
    with col2:
        if st.button("📄 Export Report to Word"):
            if not has_responses(st.session_state.responses[selected_role]):
                st.warning("No responses found.")
            else:
                doc = export_to_docx(st.session_state.responses[selected_role], competency_sections)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button(
                    "📥 Download ERB_Report.docx",
                    data=buffer.getvalue(),
                    file_name="ERB_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

    # ---------- AI Review ----------
    col1, col2 = st.columns(2)
    with col1:
        if st.button("֎Review Response with AI"):
            if not user_input.strip():
                st.session_state.suggestion = ""
                st.warning("Please enter a response first.")
            else:
                with st.spinner("Generating AI suggestions..."):
                    suggestion = ai_service.get_gpt_feedback(user_input, current_key, section, selected_role)
                    st.session_state.suggestion = suggestion

        # ---------------------- AI Suggestions ---------------------- #
        if st.session_state.suggestion:
            if st.session_state.suggestion.startswith("⚠️"):
                st.error(st.session_state.suggestion)
            else:
                st.markdown(
                    f"""
                    **֎🇦🇮 AI Suggestions:**
                    <div style="
                        max-height: 250px; 
                        overflow-y: auto; 
                        padding: 0.5rem; 
                        border: 1px solid #ddd; 
                        border-radius: 8px;
                        background-color: #f9f9f9;">
                        {st.session_state.suggestion}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col2:
        ########################### REVIEW ENTIRE REPORT ###################################
        if st.button("🔍 Review Entire Report with AI"):
            if not has_responses(st.session_state.responses[selected_role]):
                st.warning("No responses found.")
            else:
                with st.spinner("Analyzing full report with GPT..."):
                    full_feedback = ai_service.get_full_report_feedback(
                            st.session_state.responses[selected_role], competency_sections, selected_role)
                    st.session_state.full_feedback = full_feedback


        # ---------------------- AI Suggestions ---------------------- #
        if st.session_state.full_feedback:
            if st.session_state.full_feedback.startswith("⚠️"):
                st.error(st.session_state.full_feedback)
            else:
                st.markdown(
                    f"""
                    **֎🇦🇮 AI Suggestions:**
                    <div style="
                        max-height: 250px; 
                        overflow-y: auto; 
                        padding: 0.5rem; 
                        border: 1px solid #ddd; 
                        border-radius: 8px;
                        background-color: #f9f9f9;">
                        {st.session_state.full_feedback}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def main_ui():
    create_report_ui()