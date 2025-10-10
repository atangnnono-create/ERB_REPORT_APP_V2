from typing import Tuple

import streamlit as st
import json
from io import BytesIO
from datetime import datetime
from frontend.utilities.comps import (engineer_competencies, technician_competencies, technologist_competencies)
from frontend.services import ai_service
from utilities.utils import (render_progress_dashboard, export_to_docx, has_responses, sort_keys)
from frontend.services.enhanced_api_client import EnhancedAPIClient
from utilities.error_handling import ErrorHandler, LoadingState, with_loading


# Add these enhanced functions to your existing create_report.py

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
                    with open("auto_save_backup.json", "w") as f:
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
            with open("auto_save_backup.json", "r") as f:
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


def enhanced_render_progress_dashboard(sections: dict, profession: str):
    """Enhanced progress dashboard with more metrics"""
    st.sidebar.markdown(
        f"""
        <h2 style="background: linear-gradient(90deg, #1e90ff, #00bfff);
                   padding: 10px; border-radius: 8px;
                   color: white; text-align: center; font-family:Arial;">
            📊 {profession}'s Progress
        </h2>
        """,
        unsafe_allow_html=True
    )

    role_responses = st.session_state.responses.get(profession, {})

    # Overall progress
    total_sections = len(sections)
    completed_sections = sum(1 for sec_id in sections if role_responses.get(sec_id, {}).get("response", "").strip())
    progress_percent = (completed_sections / total_sections) * 100 if total_sections else 0

    st.sidebar.metric("Overall Progress", f"{progress_percent:.1f}%")
    st.sidebar.progress(progress_percent / 100)

    # Quick stats
    total_words = sum(len(role_responses.get(sec_id, {}).get("response", "").split())
                      for sec_id in sections)
    st.sidebar.metric("Total Words", total_words)

    # Section-by-section progress
    for sec_id, section in sections.items():
        user_entry = role_responses.get(sec_id, {})
        user_response = user_entry.get("response", "")
        word_count = len(user_response.split())
        word_limit = section.get("word_limit", 500)
        completion = min(word_count / word_limit, 1.0)

        # Color code based on completion
        if completion >= 0.8:
            color = "#2ecc71"  # Green
            status = "✅"
        elif completion > 0:
            color = "#3498db"  # Blue
            status = "📝"
        else:
            color = "#e74c3c"  # Red
            status = "⏳"

        st.sidebar.markdown(
            f"""
            <div style="border-left: 4px solid {color}; padding-left: 8px; margin: 5px 0;">
                <div style="font-size: 14px; font-weight: bold;">{status} {sec_id}</div>
                <div style="font-size: 12px; color: #666;">{word_count}/{word_limit} words</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# Add these enhancements to your existing create_report_ui function:

def enhanced_create_report_ui():
    """Enhanced version of create_report_ui with new features"""

    # Initialize auto-save
    setup_auto_save()

    # Add auto-save controls to sidebar
    show_auto_save_controls()

    # Check for auto-saved progress on startup
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

    # Enhanced progress dashboard
    if "selected_role" in st.session_state:
        if st.session_state.selected_role == "Engineer":
            competency_sections = engineer_competencies
        elif st.session_state.selected_role == "Engineering Technologist":
            competency_sections = technologist_competencies
        else:
            competency_sections = technician_competencies

        enhanced_render_progress_dashboard(competency_sections, st.session_state.selected_role)

    # Auto-save check (runs on every interaction)
    auto_save_check()

    # Enhanced submission with validation
    def enhanced_submit_report():
        """Enhanced report submission with validation"""
        if not has_responses(st.session_state.responses[st.session_state.selected_role]):
            ErrorHandler.show_error("No responses to submit")
            return

        # Validate report data
        report_status = st.session_state.responses[st.session_state.selected_role].get('_status', 'draft')
        sorted_responses = dict(
            sorted(st.session_state.responses[st.session_state.selected_role].items(), key=lambda x: x[0]))

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
            "title": f"{st.session_state.selected_role} Report - {datetime.now().strftime('%Y-%m-%d')}",
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
                    st.session_state.responses[st.session_state.selected_role] = {}
                    st.session_state.current_section = 0
            else:
                ErrorHandler.show_error(f"Failed to submit report: {result.get('detail', 'Unknown error')}")

    # Replace the existing submit button with enhanced version
    if st.button("🚀 Submit Report to Backend", key="enhanced_submit"):
        enhanced_submit_report()