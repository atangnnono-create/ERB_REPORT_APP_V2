from typing import Tuple
import streamlit as st
import json
from io import BytesIO
from datetime import datetime
from frontend.utilities.comps import (engineer_competencies, technician_competencies, technologist_competencies)
import enhanced_ai_service
from utilities.utils import (export_to_docx, has_responses, sort_keys, enhanced_render_progress_dashboard)
from frontend.services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState, with_loading
from services.enhanced_state_manager import state_manager


api = EnhancedAPIClient()

# ========== ENHANCED STATE MANAGER INTEGRATION ==========
def setup_auto_save():
    """Initialize auto-save functionality with state manager"""
    if "auto_save_interval" not in st.session_state:
        st.session_state.auto_save_interval = 30  # seconds
    if "last_save_time" not in st.session_state:
        st.session_state.last_save_time = datetime.now()
    if "auto_save_enabled" not in st.session_state:
        st.session_state.auto_save_enabled = True

    # Register key persistence with state manager
    state_manager.persist_key("auto_save_data")
    state_manager.persist_key("selected_role")
    state_manager.persist_key("responses")
    state_manager.persist_key("current_section")
    state_manager.persist_key("last_role")


def auto_save_check():
    """Check if it's time to auto-save"""
    if not st.session_state.auto_save_enabled:
        return

    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_save_time).total_seconds()

    if time_diff >= st.session_state.auto_save_interval:
        save_current_progress()
        st.session_state.last_save_time = current_time
        st.toast("💾 Progress auto-saved", icon="✅")


def save_current_progress():
    """Save current report progress using state manager"""
    try:
        if "responses" in st.session_state and "selected_role" in st.session_state:
            # Ensure responses for current role exists and is a dictionary
            current_role_responses = st.session_state.responses.get(st.session_state.selected_role, {})
            if not isinstance(current_role_responses, dict):
                current_role_responses = {}

            progress_data = {
                "role": st.session_state.selected_role,
                "responses": current_role_responses,
                "current_section": st.session_state.get("current_section", 0),
                "last_modified": datetime.now().isoformat(),
                "version": "2.0"
            }

            # Use state manager for persistence
            state_manager.set_state("auto_save_data", progress_data, persist=True)
            state_manager.set_state("selected_role", st.session_state.selected_role, persist=True)
            state_manager.set_state("responses", st.session_state.responses, persist=True)
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)

    except Exception as e:
        print(f"Auto-save failed: {e}")


def load_auto_saved_progress():
    """Load auto-saved progress using state manager"""
    try:
        saved_data = state_manager.get_state("auto_save_data")
        if saved_data and saved_data.get("version") == "2.0":
            return saved_data
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

    total_words = 0
    for comp in competencies:
        response = comp.get('user_response', '')
        total_words += len(response.split())

    if total_words < 100:
        return False, "Total report content must be at least 100 words"

    return True, "Validation passed"


def show_auto_save_controls():
    """Display auto-save controls with state manager information"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Auto-Save & State")

    auto_save = st.sidebar.toggle("Enable Auto-Save",
                                  value=st.session_state.get("auto_save_enabled", True),
                                  key="auto_save_toggle")
    st.session_state.auto_save_enabled = auto_save

    interval = st.sidebar.slider("Save Interval (seconds)",
                                 min_value=10, max_value=120,
                                 value=st.session_state.get("auto_save_interval", 30),
                                 key="auto_save_interval_slider")
    st.session_state.auto_save_interval = interval

    if st.sidebar.button("💾 Save Now", use_container_width=True):
        save_current_progress()
        st.sidebar.success("Progress saved to persistent storage!")

    if st.sidebar.button("🔄 Load Last Save", use_container_width=True):
        saved_data = load_auto_saved_progress()
        if saved_data:
            st.session_state.selected_role = saved_data.get("role", "Engineer")
            st.session_state.responses[saved_data["role"]] = saved_data.get("responses", {})
            st.session_state.current_section = saved_data.get("current_section", 0)
            state_manager.set_state("selected_role", st.session_state.selected_role, persist=True)
            state_manager.set_state("responses", st.session_state.responses, persist=True)
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)
            st.sidebar.success("Progress restored!")
            st.rerun()
        else:
            st.sidebar.warning("No saved progress found")


def enhanced_submit_report(selected_role: str, competency_sections: dict):
    """Enhanced report submission with state manager cleanup"""
    # FIX: Add proper null check for responses
    if not st.session_state.responses.get(selected_role):
        ErrorHandler.show_error("No responses to submit")
        return

    if not has_responses(st.session_state.responses[selected_role]):
        ErrorHandler.show_error("No responses to submit")
        return

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

    is_valid, validation_msg = validate_report_data(payload)
    if not is_valid:
        ErrorHandler.show_error(validation_msg)
        return

    with LoadingState("Submitting report..."):
        success, result = api.create_report(payload)

        if success and "id" in result:
            ErrorHandler.show_success(f"Report submitted successfully! (ID: {result['id']})")

            if report_status != 'draft':
                st.session_state.responses[selected_role] = {}
                st.session_state.current_section = 0
                state_manager.set_state("responses", st.session_state.responses, persist=True)
                state_manager.set_state("current_section", 0, persist=True)
            else:
                state_manager.set_state("responses", st.session_state.responses, persist=True)

        else:
            ErrorHandler.show_error(f"Failed to submit report: {result.get('detail', 'Unknown error')}")


def initialize_session_state():
    """Initialize all session state variables with state manager support"""
    defaults = {
        "responses": {},
        "suggestion": "",
        "full_feedback": "",
        "current_section": 0,
        "selected_role": "Engineer",
        "role_selector": "Engineer",
        "last_loaded_file": None,
        "pending_responses": None,
        "last_role": None,
        "auto_save_enabled": True,
        "auto_save_loaded": False,
        "enable_local_backup": True,
        "last_save_time": datetime.now()
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            persisted_value = state_manager.get_state(key)
            if persisted_value is not None:
                st.session_state[key] = persisted_value
            else:
                st.session_state[key] = default_value

    # FIX: Ensure responses is properly initialized and is a dict
    if not isinstance(st.session_state.responses, dict):
        st.session_state.responses = {}

    # Ensure current role has responses dict
    current_role = st.session_state.get("selected_role", "Engineer")
    if current_role not in st.session_state.responses or not isinstance(st.session_state.responses[current_role], dict):
        st.session_state.responses[current_role] = {}


def enhanced_role_selection():
    """Role selection with state manager persistence"""
    selected_role = st.radio(
        "👷 Select your professional category:",
        ["Engineer", "Engineering Technologist", "Engineering Technician"],
        key="role_selector",
        horizontal=True,
    )

    if selected_role != st.session_state.get("selected_role"):
        st.session_state.selected_role = selected_role
        state_manager.set_state("selected_role", selected_role, persist=True)

        # FIX: Ensure the new role has responses initialized
        if selected_role not in st.session_state.responses or not isinstance(st.session_state.responses[selected_role],
                                                                             dict):
            st.session_state.responses[selected_role] = {}

        clear_competency_suggestions()
        clear_full_report_suggestions()
        st.session_state.last_role = selected_role
        state_manager.set_state("last_role", selected_role, persist=True)

        st.session_state.current_section = 0
        state_manager.set_state("current_section", 0, persist=True)

        st.rerun()

    return selected_role


def enhanced_response_handler(selected_role: str, current_key: str, section: dict):
    """Handle user responses with automatic state persistence"""

    # FIX: Ensure responses for current role exists and is a dict
    if selected_role not in st.session_state.responses or not isinstance(st.session_state.responses[selected_role],
                                                                         dict):
        st.session_state.responses[selected_role] = {}

    current_responses = st.session_state.responses.get(selected_role, {})
    current_response_data = current_responses.get(current_key, {})
    current_text = current_response_data.get("response", "")

    user_input = st.text_area(
        "✍️ Your response:",
        value=current_text,
        height=300,
        key=f"text_area_{current_key}",
    )

    response_data = {
        "title": section["title"],
        "response": user_input,
        "word_count": len(user_input.split()) if user_input else 0,
    }

    st.session_state.responses[selected_role][current_key] = response_data
    state_manager.set_state("responses", st.session_state.responses, persist=True)
    auto_save_check()

    return user_input


def enhanced_navigation(total_sections: int):
    """Navigation with section persistence"""
    col1, col3 = st.columns([6, 1])

    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_section > 0:
            st.session_state.current_section -= 1
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)
            clear_competency_suggestions()
            st.rerun()

    with col3:
        if st.button("Next ➡️") and st.session_state.current_section < total_sections - 1:
            st.session_state.current_section += 1
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)
            clear_competency_suggestions()
            st.rerun()


def clear_competency_suggestions():
    if "suggestion" in st.session_state:
        st.session_state.suggestion = ""


def clear_full_report_suggestions():
    if "full_feedback" in st.session_state:
        st.session_state.full_feedback = ""


def create_report_ui():
    st.set_page_config(page_title="📝 Create Report", layout="centered")

    # Require Login
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("⚠️ Please login first to create reports.")
        return
    else:
        api.set_token(st.session_state.token)

    # Enhanced Session Initialization
    initialize_session_state()

    # Setup auto-save
    setup_auto_save()

    # Auto-save controls
    show_auto_save_controls()

    # Check for auto-saved progress
    if "auto_save_loaded" not in st.session_state:
        saved_data = load_auto_saved_progress()
        if saved_data and st.session_state.get("selected_role") == saved_data.get("role"):
            with st.container():
                st.warning("💾 Auto-saved progress found from your last session")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Restore Progress"):
                        st.session_state.responses[saved_data["role"]] = saved_data.get("responses", {})
                        st.session_state.current_section = saved_data.get("current_section", 0)
                        st.session_state.auto_save_loaded = True
                        state_manager.set_state("responses", st.session_state.responses, persist=True)
                        state_manager.set_state("current_section", st.session_state.current_section, persist=True)
                        st.rerun()
                with col2:
                    if st.button("🗑️ Start Fresh"):
                        st.session_state.auto_save_loaded = True
                        st.rerun()

    # File uploader
    with st.sidebar:
        uploaded_file = st.file_uploader(
            "⬇️ Load Report 📂",
            type=["json"],
            key="file_loader_report"
        )

        if uploaded_file is not None and st.session_state.get("last_loaded_file") != uploaded_file.name:
            try:
                loaded_responses = json.load(uploaded_file)

                if not isinstance(loaded_responses, dict):
                    st.error("Invalid file format. Please upload a valid JSON file.")
                    return

                available_roles = [
                    r for r in ["Engineer", "Engineering Technologist", "Engineering Technician"]
                    if r in loaded_responses
                ]

                if available_roles:
                    st.session_state.role_selector = available_roles[0]
                    st.session_state.selected_role = available_roles[0]
                    state_manager.set_state("selected_role", available_roles[0], persist=True)

                st.session_state.pending_responses = loaded_responses
                st.session_state.last_loaded_file = uploaded_file.name

                st.success(f"Progress preloaded for {st.session_state.selected_role} from {uploaded_file.name}")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading progress: {str(e)}")

    # Role selection
    selected_role = enhanced_role_selection()

    if selected_role == "Engineer":
        competency_sections = engineer_competencies
    elif selected_role == "Engineering Technologist":
        competency_sections = technologist_competencies
    else:
        competency_sections = technician_competencies

    # FIX: Ensure the selected role has responses initialized
    if selected_role not in st.session_state.responses or not isinstance(st.session_state.responses[selected_role],
                                                                         dict):
        st.session_state.responses[selected_role] = {}

    # Progress dashboard
    enhanced_render_progress_dashboard(competency_sections, st.session_state.selected_role)

    # Auto-Save Check
    auto_save_check()

    # File upload normalization
    if "pending_responses" in st.session_state and st.session_state.pending_responses is not None:
        raw_data = st.session_state.pending_responses

        if isinstance(raw_data, dict):
            role = st.session_state.selected_role
            role_data = raw_data.get(role, {})

            if isinstance(role_data, dict):
                for k, v in role_data.items():
                    if isinstance(v, dict) and k in competency_sections:
                        v.setdefault("title", competency_sections[k]["title"])
                        v.setdefault("response", "")
                        v.setdefault(
                            "word_count",
                            len(v.get("response", "").split()) if v.get("response") else 0
                        )

                st.session_state.responses[role] = role_data
                state_manager.set_state("responses", st.session_state.responses, persist=True)

            del st.session_state.pending_responses
        else:
            st.error("Invalid data format in uploaded file")
            del st.session_state.pending_responses

    # Main UI components
    role_responses = st.session_state.responses.get(selected_role, {})

    # Handle role switching
    if "last_role" not in st.session_state:
        st.session_state.last_role = selected_role
    elif st.session_state.last_role != selected_role:
        st.session_state.current_section = 0
        state_manager.set_state("current_section", 0, persist=True)
        clear_competency_suggestions()
        clear_full_report_suggestions()
        st.session_state.last_role = selected_role
        state_manager.set_state("last_role", selected_role, persist=True)
        st.rerun()

    # Progress tracker - FIX: Added proper null checks
    section_keys = sort_keys(list(competency_sections.keys()))
    total_sections = len(section_keys)

    # FIX: Safe completion count with proper null checks
    completed_sections = 0
    current_role_responses = st.session_state.responses.get(selected_role, {})
    if isinstance(current_role_responses, dict):
        completed_sections = sum(
            1
            for k in section_keys
            if isinstance(current_role_responses.get(k), dict)
            and current_role_responses[k].get("response", "").strip()
        )

    progress_ratio = completed_sections / total_sections if total_sections else 0
    st.progress(progress_ratio, text=f"{completed_sections}/{total_sections} completed")

    # Current section
    current_index = min(max(st.session_state.current_section, 0), total_sections - 1)
    current_key = section_keys[current_index]
    section = competency_sections[current_key]

    st.subheader(f"Competency {current_index + 1} of {total_sections}: {section['title']}")
    st.info(section["instructions"])

    # Status selection
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
        state_manager.set_state("responses", st.session_state.responses, persist=True)

        if selected_status == "submitted":
            st.info("🔔 Your report will be submitted for review and cannot be edited further until reviewed.")

    # Response handler
    user_input = enhanced_response_handler(selected_role, current_key, section)

    # Navigation
    enhanced_navigation(total_sections)

    st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
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

    # AI Review
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
        if st.button("🔍 Review Entire Report with AI"):
            if not has_responses(st.session_state.responses[selected_role]):
                st.warning("No responses found.")
            else:
                with st.spinner("Analyzing full report with GPT..."):
                    full_feedback = enhanced_ai_service.get_full_report_feedback(
                        st.session_state.responses[selected_role], competency_sections, selected_role)
                    st.session_state.full_feedback = full_feedback

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