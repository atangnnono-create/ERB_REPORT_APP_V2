from typing import Tuple
import streamlit as st
import json
from io import BytesIO
from datetime import datetime
from frontend.utilities.comps import (engineer_competencies, technician_competencies, technologist_competencies)
import enhanced_ai_service
from utilities.utils import (export_to_docx, has_responses, sort_keys, render_progress_dashboard_sorted)
from frontend.services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState, with_loading
from services.enhanced_state_manager import state_manager

api = EnhancedAPIClient()


def set_report_styles():
    """Clean CSS without container issues"""
    st.markdown("""
    <style>
    /* Clean main styling */
    .main-report-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        min-height: 100vh;
    }

    /* Enhanced progress bar styling - target main area specifically */
    .main .stProgress > div > div > div {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
        border-radius: 4px !important;
    }

    /* Make sure the progress bar container is visible in main area */
    .main .stProgress {
        background-color: #e9ecef !important;
        border-radius: 4px !important;
        height: 8px !important;
    }

    /* Scrollable AI feedback boxes */
    .scrollable-feedback {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        background: #f8f9fa;
        margin: 0.5rem 0;
    }

    /* Enhanced text area */
    .stTextArea textarea {
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: #ffffff;
    }

    .stTextArea textarea:focus {
        border-color: #3498db;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }

    /* Professional buttons */
    .stButton button {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
    }

    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Better spacing */
    .main-content {
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ========== ENHANCED STATE MANAGER INTEGRATION ==========
def setup_auto_save():
    """Initialize auto-save functionality with state manager"""
    defaults = {
        "auto_save_interval": 30,  # seconds
        "last_save_time": datetime.now(),
        "auto_save_enabled": True,
        "auto_save_attempts": 0,
        "last_save_successful": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Register key persistence with state manager
    persistent_keys = [
        "auto_save_data", "selected_role", "responses",
        "current_section", "last_role", "report_status"
    ]
    for key in persistent_keys:
        state_manager.persist_key(key)


def auto_save_check(force_save=False):
    """Check if it's time to auto-save with improved logic"""
    if not st.session_state.auto_save_enabled and not force_save:
        return False

    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_save_time).total_seconds()

    # Save if forced OR interval elapsed OR this is first significant change
    should_save = (force_save or
                   time_diff >= st.session_state.auto_save_interval or
                   st.session_state.auto_save_attempts == 0)

    if should_save:
        success = save_current_progress()
        if success:
            st.session_state.last_save_time = current_time
            st.session_state.last_save_successful = True
            if force_save:
                st.toast("💾 Progress saved successfully!", icon="✅")
            else:
                # Only show auto-save toast if not forced and not first attempt
                if st.session_state.auto_save_attempts > 0:
                    st.toast("💾 Progress auto-saved", icon="✅")
        else:
            st.session_state.last_save_successful = False
            st.toast("⚠️ Failed to save progress", icon="❌")

        st.session_state.auto_save_attempts += 1
        return success

    return False


def save_current_progress():
    """Save current report progress with enhanced error handling and backup"""
    try:
        if "responses" not in st.session_state or "selected_role" not in st.session_state:
            return False

        current_role = st.session_state.selected_role
        current_role_responses = st.session_state.responses.get(current_role, {})

        if not isinstance(current_role_responses, dict):
            current_role_responses = {}

        # Create comprehensive progress data
        progress_data = {
            "role": current_role,
            "responses": current_role_responses,
            "current_section": st.session_state.get("current_section", 0),
            "last_modified": datetime.now().isoformat(),
            "version": "2.1",
            "total_responses": len([r for r in current_role_responses.values()
                                    if isinstance(r, dict) and r.get("response", "").strip()]),
            "total_word_count": sum(len(r.get("response", "").split())
                                    for r in current_role_responses.values()
                                    if isinstance(r, dict))
        }

        # Primary save: state manager
        try:
            state_manager.set_state("auto_save_data", progress_data, persist=True)
            state_manager.set_state("selected_role", current_role, persist=True)
            state_manager.set_state("responses", st.session_state.responses, persist=True)
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)
        except Exception as state_error:
            print(f"State manager save failed: {state_error}")
            return False

        # Local backup as fallback
        if st.session_state.get("enable_local_backup", True):
            try:
                backup_key = f"auto_save_backup_{current_role}"
                st.session_state[backup_key] = progress_data
            except Exception as backup_error:
                print(f"Local backup failed: {backup_error}")

        return True

    except Exception as e:
        print(f"Auto-save failed: {e}")
        return False


def load_auto_saved_progress():
    """Load auto-saved progress with fallback to local backup"""
    try:
        # Try state manager first
        saved_data = state_manager.get_state("auto_save_data")
        if saved_data and saved_data.get("version") in ["2.0", "2.1"]:
            return saved_data

        # Fallback to local backup
        current_role = st.session_state.get("selected_role", "Engineer")
        backup_key = f"auto_save_backup_{current_role}"
        if backup_key in st.session_state:
            return st.session_state[backup_key]

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
    """Display enhanced auto-save controls with status information"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Auto-Save & State")

    # Auto-save toggle with status
    auto_save = st.sidebar.toggle(
        "Enable Auto-Save",
        value=st.session_state.get("auto_save_enabled", True),
        key="auto_save_toggle",
        help="Automatically save your progress every 30 seconds"
    )
    st.session_state.auto_save_enabled = auto_save

    # Interval control
    interval = st.sidebar.slider(
        "Save Interval (seconds)",
        min_value=15,
        max_value=120,
        value=st.session_state.get("auto_save_interval", 30),
        key="auto_save_interval_slider",
        disabled=not auto_save
    )
    st.session_state.auto_save_interval = interval

    # Status indicator
    if st.session_state.get("last_save_successful", True):
        st.sidebar.success("✅ All changes saved")
    else:
        st.sidebar.error("❌ Save failed - check connection")

    # Manual controls
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("💾 Save Now", use_container_width=True):
            if auto_save_check(force_save=True):
                st.sidebar.success("Progress saved!")
            else:
                st.sidebar.error("Save failed!")

    with col2:
        if st.button("🔄 Load Last Save", use_container_width=True):
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

    # Save statistics
    if st.session_state.get("auto_save_attempts", 0) > 0:
        st.sidebar.caption(
            f"🕐 Last save: {st.session_state.get('last_save_time', datetime.now()).strftime('%H:%M:%S')}")
        st.sidebar.caption(f"📊 Save attempts: {st.session_state.get('auto_save_attempts', 0)}")


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

    # ========== ADD ROLE-BASED COMPETENCY VALIDATION HERE ==========
    # Count completed competencies (excluding the _status field)
    completed_competencies = 0
    for key, response_data in st.session_state.responses[selected_role].items():
        if key != '_status' and response_data.get("response", "").strip():
            completed_competencies += 1

    # Define role-based minimum requirements
    role_minimums = {
        "Engineer": 10,
        "Engineering Technologist": 34,
        "Engineering Technician": 32
    }

    # Apply validation rules based on report status and role
    if report_status == 'submitted':
        required_minimum = role_minimums.get(selected_role, 0)

        if completed_competencies < required_minimum:
            ErrorHandler.show_error(
                f"Cannot submit report for review: {selected_role} role requires at least {required_minimum} "
                f"completed competencies. You currently have {completed_competencies} completed competencies. "
                f"Please complete more competencies or save as draft instead."
            )
            return
    # For draft status, no competency count validation is needed
    # ========== END OF VALIDATION LOGIC ==========

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

    # FINAL REPORT SUBMISSION - Use dedicated submit endpoint
    if report_status == 'submitted':
        with LoadingState("Submitting report for review..."):
            success, result = api.submit_report_for_review(payload)  # Use new endpoint with full payload

            if success and "id" in result:
                st.balloons()
                ErrorHandler.show_success(f"Report submitted for review! (ID: {result['id']})")

                # Clear session state for submitted reports
                st.session_state.responses[selected_role] = {}
                st.session_state.current_section = 0
                state_manager.set_state("responses", st.session_state.responses, persist=True)
                state_manager.set_state("current_section", 0, persist=True)
            else:
                ErrorHandler.show_error(f"Failed to submit report: {result.get('detail', 'Unknown error')}")

    # DRAFT REPORT - Use existing create endpoint
    else:
        with LoadingState("Saving report as draft..."):
            success, result = api.create_report(payload)

            if success and "id" in result:
                st.balloons()
                ErrorHandler.show_success(f"Report saved as draft! (ID: {result['id']}) - You can continue editing")
                state_manager.set_state("responses", st.session_state.responses, persist=True)
            else:
                ErrorHandler.show_error(f"Failed to save draft: {result.get('detail', 'Unknown error')}")


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
    """Handle user responses with improved auto-save triggering"""
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
        on_change=lambda: auto_save_check(force_save=True)  # Save on text change
    )

    response_data = {
        "title": section["title"],
        "response": user_input,
        "word_count": len(user_input.split()) if user_input else 0,
        "last_modified": datetime.now().isoformat()
    }

    st.session_state.responses[selected_role][current_key] = response_data
    state_manager.set_state("responses", st.session_state.responses, persist=True)

    # Auto-save on significant changes (new response or major edits)
    if user_input != current_text and len(user_input) > 10:
        auto_save_check(force_save=True)

    return user_input


def enhanced_navigation(total_sections: int):
    """Navigation with section persistence"""
    col1, col3 = st.columns([6, 1])

    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_section > 0:
            auto_save_check(force_save=True)
            st.session_state.current_section -= 1
            state_manager.set_state("current_section", st.session_state.current_section, persist=True)
            clear_competency_suggestions()
            st.rerun()

    with col3:
        if st.button("Next ➡️") and st.session_state.current_section < total_sections - 1:
            auto_save_check(force_save=True)
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
    st.set_page_config(page_title="📝 Create Report", layout="wide")

    # Apply clean styles
    set_report_styles()

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

    # Main layout with sidebar
    with st.sidebar:
        # Auto-save controls
        show_auto_save_controls()

        # File uploader
        uploaded_file = st.file_uploader(
            "📂 Load Previous Report",
            type=["json"],
            key="file_loader_report",
            help="Upload a previously saved JSON report to continue working"
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

                st.success(f"✅ Progress loaded for {st.session_state.selected_role}")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading progress: {str(e)}")

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        # Horizontal Status Section
        st.markdown("#### 👷 Professional Role")
        selected_role = enhanced_role_selection()

        if selected_role == "Engineer":
            competency_sections = engineer_competencies
        elif selected_role == "Engineering Technologist":
            competency_sections = technologist_competencies
        else:
            competency_sections = technician_competencies

        # Initialize responses for selected role
        if selected_role not in st.session_state.responses or not isinstance(st.session_state.responses[selected_role],
                                                                             dict):
            st.session_state.responses[selected_role] = {}

        # Status row
        st.markdown("---")
        status_col1, status_col2, status_col3 = st.columns(3)

        with status_col1:
            current_status = st.session_state.responses[selected_role].get('_status', 'draft')
            status_options = ["draft", "submitted"]
            selected_status = st.radio(
                "📋 Report Status",
                options=status_options,
                index=status_options.index(current_status) if current_status in status_options else 0,
                horizontal=True
            )
            st.session_state.responses[selected_role]['_status'] = selected_status
            state_manager.set_state("responses", st.session_state.responses, persist=True)

        with status_col2:
            if selected_status == "submitted":
                st.success("✅ Ready for review")
            else:
                st.info("💾 Draft mode")

        with status_col3:
            # Quick progress indicator
            section_keys = sort_keys(list(competency_sections.keys()))
            total_sections = len(section_keys)
            current_role_responses = st.session_state.responses.get(selected_role, {})
            completed_sections = 0
            if isinstance(current_role_responses, dict):
                completed_sections = sum(
                    1 for k in section_keys
                    if isinstance(current_role_responses.get(k), dict)
                    and current_role_responses[k].get("response", "").strip()
                )
            #st.metric("Progress", f"{completed_sections}/{total_sections}")

        st.markdown("---")

        # Check for auto-saved progress
        if "auto_save_loaded" not in st.session_state:
            saved_data = load_auto_saved_progress()
            if saved_data and st.session_state.get("selected_role") == saved_data.get("role"):
                st.info("💾 Auto-saved progress found from your last session")
                col_restore1, col_restore2 = st.columns(2)
                with col_restore1:
                    if st.button("🔄 Restore Progress", use_container_width=True):
                        st.session_state.responses[saved_data["role"]] = saved_data.get("responses", {})
                        st.session_state.current_section = saved_data.get("current_section", 0)
                        st.session_state.auto_save_loaded = True
                        state_manager.set_state("responses", st.session_state.responses, persist=True)
                        state_manager.set_state("current_section", st.session_state.current_section, persist=True)
                        st.rerun()
                with col_restore2:
                    if st.button("🗑️ Start Fresh", use_container_width=True):
                        st.session_state.auto_save_loaded = True
                        st.rerun()

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

        # Progress tracker
        section_keys = sort_keys(list(competency_sections.keys()))
        total_sections = len(section_keys)

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

        # Progress display
        st.markdown("#### 📊 Your Progress")
        col_prog1, col_prog2 = st.columns([3, 1])
        with col_prog1:
            st.progress(progress_ratio)
        with col_prog2:
            st.markdown(f"**{completed_sections}/{total_sections}** competencies completed")

        # Current competency section
        current_index = min(max(st.session_state.current_section, 0), total_sections - 1)
        current_key = section_keys[current_index]
        section = competency_sections[current_key]

        # Competency section
        st.markdown("---")
        st.markdown(f"#### 🎯 Competency {current_index + 1} of {total_sections}")
        st.markdown(f"##### {section['title']}")
        st.info(f"💡 **Instructions:** {section['instructions']}")

        # Response handler
        user_input = enhanced_response_handler(selected_role, current_key, section)

        # Navigation
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("⬅️ Previous", use_container_width=True,
                         key="prev_btn") and st.session_state.current_section > 0:
                auto_save_check(force_save=True)
                st.session_state.current_section -= 1
                state_manager.set_state("current_section", st.session_state.current_section, persist=True)
                clear_competency_suggestions()
                st.rerun()
        with col_nav3:
            if st.button("Next ➡️", use_container_width=True,
                         key="next_btn") and st.session_state.current_section < total_sections - 1:
                auto_save_check(force_save=True)
                st.session_state.current_section += 1
                state_manager.set_state("current_section", st.session_state.current_section, persist=True)
                clear_competency_suggestions()
                st.rerun()

        # Final actions - MOVED UP before AI section
        st.markdown("---")
        st.markdown("##### 🚀 Finalize Your Report")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("📤 Submit Report for Review", use_container_width=True, key="enhanced_submit", type="primary"):
                enhanced_submit_report(selected_role, competency_sections)

        with action_col2:
            if st.button("💾 Export to Word", use_container_width=True):
                if not has_responses(st.session_state.responses[selected_role]):
                    st.warning("No responses found to export.")
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
                        use_container_width=True
                    )

        # AI Review Section - MOVED TO BOTTOM
        st.markdown("---")
        st.markdown("##### 🤖 AI-Powered Assistance")

        # AI buttons row
        ai_col1, ai_col2 = st.columns(2)

        with ai_col1:
            if st.button("🎯 Review Current Response", use_container_width=True, key="ai_current"):
                if not user_input.strip():
                    st.session_state.suggestion = ""
                    st.warning("Please enter a response first.")
                else:
                    with st.spinner("Analyzing your response with AI..."):
                        suggestion = enhanced_ai_service.get_gpt_feedback(user_input, current_key, section,
                                                                          selected_role)
                        st.session_state.suggestion = suggestion

        with ai_col2:
            if st.button("📊 Review Entire Report", use_container_width=True, key="ai_full"):
                if not has_responses(st.session_state.responses[selected_role]):
                    st.warning("No responses found.")
                else:
                    with st.spinner("Analyzing your full report..."):
                        full_feedback = enhanced_ai_service.get_full_report_feedback(
                            st.session_state.responses[selected_role], competency_sections, selected_role)
                        st.session_state.full_feedback = full_feedback

        # AI Feedback displays - SCROLLABLE BOXES
        if st.session_state.suggestion:
            st.markdown("#### 🎯 AI Suggestions for Current Response")
            if st.session_state.suggestion.startswith("⚠️"):
                st.error(st.session_state.suggestion)
            else:
                st.markdown(
                    f'<div class="scrollable-feedback">{st.session_state.suggestion}</div>',
                    unsafe_allow_html=True
                )

        if st.session_state.full_feedback:
            st.markdown("#### 📊 AI Report Analysis")
            if st.session_state.full_feedback.startswith("⚠️"):
                st.error(st.session_state.full_feedback)
            else:
                st.markdown(
                    f'<div class="scrollable-feedback">{st.session_state.full_feedback}</div>',
                    unsafe_allow_html=True
                )

    with col2:
        # Sidebar content - Progress dashboard
        render_progress_dashboard_sorted(competency_sections, st.session_state.selected_role)

    # Footer
    st.markdown("""
       <div style='text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
           <p style='color: #666; margin: 0;'>
               <strong>Engineering Report Deck</strong> • Confidence with Clarity
           </p>
           <p style='color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
               TurtleTEC Solutions Africa
               © 2025. ALL RIGHTS RESERVED.
           </p>
       </div>
       """, unsafe_allow_html=True)


def main_ui():
    create_report_ui()


if __name__ == "__main__":
    main_ui()