from typing import Tuple
import streamlit as st
import json
from io import BytesIO
from datetime import datetime
from frontend.utilities.comps import (engineer_competencies, technician_competencies, technologist_competencies)
from frontend import enhanced_ai_service
from utilities.utils import (export_to_docx, has_responses, sort_keys, enhanced_render_progress_dashboard)
from frontend.services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState

api = EnhancedAPIClient()


# ========== AUTO-SAVE FUNCTIONS ==========

def setup_auto_save():
    """Initialize auto-save functionality"""
    if "auto_save_interval" not in st.session_state:
        st.session_state.auto_save_interval = 30  # seconds
    if "last_save_time" not in st.session_state:
        st.session_state.last_save_time = datetime.now()
    if "auto_save_enabled" not in st.session_state:
        st.session_state.auto_save_enabled = True


def auto_save_check():
    """Check if it's time to auto-save"""
    if not st.session_state.auto_save_enabled:
        return

    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_save_time).total_seconds()

    if time_diff >= st.session_state.auto_save_interval:
        save_current_progress()
        st.session_state.last_save_time = current_time
        # Show subtle save indicator
        st.toast("💾 Progress auto-saved", icon="✅")


def save_current_progress():
    """Save current report progress"""
    try:
        if "responses" in st.session_state and "selected_role" in st.session_state:
            progress_data = {
                "role": st.session_state.selected_role,
                "responses": st.session_state.responses.get(st.session_state.selected_role, {}),
                "current_section": st.session_state.get("current_section", 0),
                "last_modified": datetime.now().isoformat(),
                "version": "2.0"
            }

            # Save to session state for persistence
            st.session_state["auto_save_data"] = progress_data

            # Optional: Save to local storage
            if st.session_state.get("enable_local_backup", True):
                try:
                    with open("../auto_save_backup.json", "w") as f:
                        json.dump(progress_data, f, indent=2)
                except Exception:
                    pass  # Silent fail for local backup

    except Exception as e:
        print(f"Auto-save failed: {e}")


def load_auto_saved_progress():
    """Load auto-saved progress if available"""
    try:
        # Check session state first
        if "auto_save_data" in st.session_state:
            data = st.session_state.auto_save_data
            if data.get("version") == "2.0":
                return data

        # Check local backup
        try:
            with open("../auto_save_backup.json", "r") as f:
                data = json.load(f)
                if data.get("version") == "2.0":
                    return data
        except FileNotFoundError:
            pass

    except Exception as e:
        print(f"Failed to load auto-save: {e}")

    return None


def validate_report_data(report_data: dict) -> Tuple[bool, str]:
    """Validate report data before submission"""
    if not report_data.get('title') or not report_data['title'].strip():
        return False, "Report title is required"

    if not report_data.get('content') or len(report_data['content'].strip()) < 50:
        return False, "Report content must be at least 50 characters"

    competencies = report_data.get('competencies', [])
    if not competencies:
        return False, "At least one competency must be completed"

    # Check for minimum word count in competencies
    total_words = 0
    for comp in competencies:
        response = comp.get('user_response', '')
        total_words += len(response.split())

    if total_words < 100:
        return False, "Total report content must be at least 100 words"

    return True, "Validation passed"


def show_auto_save_controls():
    """Display auto-save controls in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Auto-Save")

    # Auto-save toggle
    auto_save = st.sidebar.toggle("Enable Auto-Save",
                                  value=st.session_state.get("auto_save_enabled", True),
                                  key="auto_save_toggle")

    st.session_state.auto_save_enabled = auto_save

    # Save interval
    interval = st.sidebar.slider("Save Interval (seconds)",
                                 min_value=10, max_value=120,
                                 value=st.session_state.get("auto_save_interval", 30),
                                 key="auto_save_interval_slider")

    st.session_state.auto_save_interval = interval

    # Manual save button
    if st.sidebar.button("💾 Save Now", use_container_width=True):
        save_current_progress()
        st.sidebar.success("Progress saved!")

    # Load previous progress
    if st.sidebar.button("🔄 Load Last Save", use_container_width=True):
        saved_data = load_auto_saved_progress()
        if saved_data:
            st.session_state.selected_role = saved_data.get("role", "Engineer")
            st.session_state.responses[saved_data["role"]] = saved_data.get("responses", {})
            st.session_state.current_section = saved_data.get("current_section", 0)
            st.sidebar.success("Progress restored!")
            st.rerun()
        else:
            st.sidebar.warning("No saved progress found")



def enhanced_submit_report(selected_role: str, competency_sections: dict):
    """Enhanced report submission with validation"""
    if not has_responses(st.session_state.responses[selected_role]):
        ErrorHandler.show_error("No responses to submit")
        return

    # Validate report data
    report_status = st.session_state.responses[selected_role].get('_status', 'draft')
    sorted_responses = dict(
        sorted(st.session_state.responses[selected_role].items(), key=lambda x: x[0]))

    competencies = []
    for key, v in sorted_responses.items():
        if key != '_status':
            competencies.append({
                "competency_key": key,
                "competency_title": v["title"],
                "user_response": v["response"],
            })

    merged_content = "\n\n".join(
        [f"{c['competency_key']} - {c['competency_title']}\n{c['user_response']}" for c in competencies]
    )

    payload = {
        "title": f"{selected_role} Report - {datetime.now().strftime('%Y-%m-%d')}",
        "content": merged_content,
        "competencies": competencies,
        "status": report_status
    }

    # Validate before submission
    is_valid, validation_msg = validate_report_data(payload)
    if not is_valid:
        ErrorHandler.show_error(validation_msg)
        return

    # Submit with loading state
    with LoadingState("Submitting report..."):
        success, result = api.create_report(payload)

        if success and "id" in result:
            ErrorHandler.show_success(f"Report submitted successfully! (ID: {result['id']})")

            # Clear auto-save data on successful submission
            if "auto_save_data" in st.session_state:
                del st.session_state.auto_save_data

            # Clear form if not draft
            if report_status != 'draft':
                st.session_state.responses[selected_role] = {}
                st.session_state.current_section = 0
        else:
            ErrorHandler.show_error(f"Failed to submit report: {result.get('detail', 'Unknown error')}")


# ========== CLEAR AI SUGGESTIONS FUNCTIONS ==========

def clear_competency_suggestions():
    if "suggestion" in st.session_state:
        st.session_state.suggestion = ""


def clear_full_report_suggestions():
    if "full_feedback" in st.session_state:
        st.session_state.full_feedback = ""


# ========== MAIN UI FUNCTION ==========

def create_report_ui():
    st.set_page_config(page_title="📝 Create Report", layout="centered")

    # ---------- Require Login ----------
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to create reports.")
        return
    else:
        api.set_token(st.session_state.token)

    # ---------- Initialize Auto-Save ----------
    setup_auto_save()

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

                # Save filename so it doesn't re-load infinitely
                st.session_state.last_loaded_file = uploaded_file.name

                st.success(f"Progress preloaded for {st.session_state.selected_role} from {uploaded_file.name}")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading progress: {str(e)}")

    # ---------- Auto-Save Controls ----------
    show_auto_save_controls()

    # ---------- Check for Auto-Saved Progress ----------
    if "auto_save_loaded" not in st.session_state:
        saved_data = load_auto_saved_progress()
        if saved_data and st.session_state.get("selected_role") == saved_data.get("role"):
            # Offer to restore saved progress
            with st.container():
                st.warning("💾 Auto-saved progress found from your last session")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Restore Progress"):
                        st.session_state.responses[saved_data["role"]] = saved_data.get("responses", {})
                        st.session_state.current_section = saved_data.get("current_section", 0)
                        st.session_state.auto_save_loaded = True
                        st.rerun()
                with col2:
                    if st.button("🗑️ Start Fresh"):
                        st.session_state.auto_save_loaded = True
                        st.rerun()

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

    # ---------- Enhanced Progress Dashboard ----------
    enhanced_render_progress_dashboard(competency_sections, st.session_state.selected_role)

    # ---------- Auto-Save Check ----------
    auto_save_check()

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

    # ---------- Status Selection ----------
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

    # ---------- Text Area for Response ----------
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

    # ---------- Action Buttons ----------
    col1, col2 = st.columns(2)
    with col1:
        # Enhanced submit button
        if st.button("🚀 Submit Report to Backend", key="enhanced_submit"):
            enhanced_submit_report(selected_role, competency_sections)

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
                    suggestion = enhanced_ai_service.get_gpt_feedback(user_input, current_key, section, selected_role)
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
                    full_feedback = enhanced_ai_service.get_full_report_feedback(
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


if __name__ == "__main__":
    main_ui()