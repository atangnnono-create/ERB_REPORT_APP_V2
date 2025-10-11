import streamlit as st
from services.enhanced_ai_service import AdvancedAIService

ai_service = AdvancedAIService()


def get_role_specific_competencies(profession: str):
    """Get competency sections based on profession/role"""
    try:
        from frontend.utilities.comps import engineer_competencies, technician_competencies, technologist_competencies

        profession_lower = profession.lower()

        if "technologist" in profession_lower:
            return technologist_competencies
        elif "technician" in profession_lower:
            return technician_competencies
        else:
            return engineer_competencies
    except ImportError as e:
        st.error(f"Error loading competencies: {str(e)}")
        return {}

def show_ai_templates_ui(competency_sections: dict, profession: str, current_responses: dict):
    """Advanced AI features interface"""
    st.title("🤖 Advanced AI Features")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Smart Templates",
        "🔍 Gap Analysis",
        "📈 Quality Improver",
        "📚 Feedback History"
    ])

    with tab1:
        show_smart_templates(competency_sections, profession)

    with tab2:
        show_gap_analysis(current_responses, competency_sections, profession)

    with tab3:
        show_quality_improver(competency_sections, profession, current_responses)

    with tab4:
        show_feedback_history()


def show_smart_templates(competency_sections: dict, profession: str):
    """AI-powered template generator"""
    st.subheader("🚀 Smart Competency Templates")

    # Display current role
    st.info(f"**Current Role:** {profession}")

    # Get role-specific competencies
    role_competencies = get_role_specific_competencies(profession)

    if not role_competencies:
        st.error("Unable to load competencies for your role. Please contact support.")
        return


    selected_competency = st.selectbox(
        "Select competency for template:",
        options=list(competency_sections.keys()),
        format_func=lambda x: f"{x}: {competency_sections[x]['title']}"
    )

    if selected_competency:
        section_data = competency_sections[selected_competency]

        st.write(f"**{selected_competency}: {section_data['title']}**")
        st.info(section_data['instructions'])

        # Show indicators if available
        indicators = section_data.get('indicators', [])
        if indicators:
            st.write("**Key Indicators:**")
            for indicator in indicators:
                st.write(f"• {indicator}")

        # Template customization options
        col1, col2 = st.columns(2)
        with col1:
            template_style = st.selectbox(
                "Template Style",
                ["Professional", "Technical", "Concise", "Detailed"],
                help="Choose the writing style for the template"
            )
        with col2:
            include_examples = st.checkbox("Include examples", value=True)

        if st.button("🎯 Generate Smart Template", use_container_width=True):
            with st.spinner("Generating high-quality template..."):
                template = ai_service.generate_competency_template(
                    selected_competency, section_data, profession,
                    style = template_style, include_examples = include_examples
                )

                if not template.startswith("⚠️"):
                    st.success("✅ Template generated successfully!")
                    st.text_area(
                        "Template Content",
                        value=template,
                        height=300,
                        key=f"template_{selected_competency}",
                        label_visibility = "collapsed"
                    )

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥Download Template",
                            data=template,
                            file_name=f"{profession}_{selected_competency}_template.txt",
                            mime="text/plain",
                            use_container_width=True
                    )
                else:
                    st.error(template)


def show_gap_analysis(current_responses: dict, competency_sections: dict, profession: str):
    """Competency gap analysis synchronized with create_report.py progress"""
    st.subheader("🔍 Competency Gap Analysis")

    # Get role-specific competencies for accurate counting
    role_competencies = get_role_specific_competencies(profession)

    if not role_competencies:
        st.error("Unable to load competencies for analysis.")
        return

    # Calculate completion - synchronized with create_report.py logic
    completed_count = 0
    total_count = len(role_competencies)

    # Use the same logic as create_report.py for consistency
    for competency_key in role_competencies.keys():
        response_data = current_responses.get(competency_key, {})
        response_text = response_data.get("response", "").strip()

        # Consider it completed if there's any response text
        if response_text:
            completed_count += 1

    # Display progress metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Completion Progress", f"{completed_count}/{total_count}")

    with col2:
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")

    with col3:
        remaining = total_count - completed_count
        st.metric("Remaining", remaining)

    # Progress bar with color coding
    progress_value = completed_count / total_count if total_count > 0 else 0
    st.progress(progress_value, text=f"Overall Progress: {completed_count}/{total_count} competencies")

    if completed_count == 0:
        st.info("🎯 Start completing competencies to get detailed gap analysis.")
        st.write("**Quick Start Tips:**")
        st.write("1. Use **Smart Templates** to get started quickly")
        st.write("2. Focus on 2-3 key competencies first")
        st.write("3. Use **Quality Improver** to enhance your responses")
        return

    # Detailed gap analysis
    if st.button("📊 Analyze Competency Gaps", use_container_width=True):
        with st.spinner("Analyzing competency gaps and providing recommendations..."):
            analysis = ai_service.analyze_competency_gaps(
                current_responses, role_competencies, profession
            )

            if not analysis.startswith("⚠️"):
                st.success("✅ Gap analysis completed!")

                # Display analysis in organized sections
                if "###" in analysis:
                    # Parse markdown-style sections
                    sections = analysis.split("###")
                    for section in sections[1:]:  # Skip first empty split
                        if ":" in section:
                            section_title, section_content = section.split(":", 1)
                            with st.expander(f"📋 {section_title.strip()}",
                                             expanded=section_title.strip() == "Critical Gaps"):
                                st.write(section_content.strip())
                        else:
                            st.write(section.strip())
                else:
                    # Fallback for non-structured analysis
                    st.write(analysis)

                # Additional recommendations based on progress
                st.subheader("🎯 Recommended Next Steps")

                if completion_rate < 50:
                    st.info("""
                    **Focus on Foundation Building:**
                    - Complete at least 50% of competencies to establish a strong foundation
                    - Use Smart Templates for the most critical competencies first
                    - Prioritize competencies marked as 'essential' in your role
                    """)
                elif completion_rate < 80:
                    st.success("""
                    **Great Progress! Continue Building:**
                    - Focus on completing remaining competencies
                    - Use Quality Improver to enhance existing responses
                    - Ensure responses meet word count and quality standards
                    """)
                else:
                    st.balloons()
                    st.success("""
                    **Excellent Progress! Final Touches:**
                    - Review all responses for consistency
                    - Use Quality Improver for final enhancements
                    - Consider peer review before submission
                    """)

            else:
                st.error(analysis)


def show_quality_improver(competency_sections: dict, profession: str, current_responses: dict):
    """Response quality improvement"""
    st.subheader("📈 Response Quality Improver")

    # Get role-specific competencies
    role_competencies = get_role_specific_competencies(profession)

    # Only show competencies that have responses
    competencies_with_responses = {
        k: v for k, v in role_competencies.items()
        if k in current_responses and current_responses[k].get('response', '').strip()
    }

    if not competencies_with_responses:
        st.info("Complete some competencies to use the quality improver.")
        return

    selected_competency = st.selectbox(
        "Select competency to improve:",
        options=list(competencies_with_responses.keys()),
        format_func=lambda x: f"{x}: {competencies_with_responses[x]['title']}",
        key="quality_improver_select"
    )

    if selected_competency:
        section_data = role_competencies[selected_competency]
        current_response = current_responses[selected_competency]['response']

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Current Response**")
            st.text_area(
                "",
                value=current_response,
                height=200,
                disabled=True,
                key="current_response_display"
            )

        with col2:
            st.write("**Response Metrics**")
            word_count = len(current_response.split())
            target_count = section_data.get('word_limit', 500)

            # Word count with visual indicator
            st.metric("Words", word_count, delta=f"Target: {target_count}")

            # Quality indicators
            if word_count < target_count * 0.5:
                st.warning("📝 Response may be too brief")
            elif word_count > target_count * 1.2:
                st.info("📝 Response is comprehensive")
            else:
                st.success("📝 Good response length")

            # Character count
            char_count = len(current_response)
            st.metric("Characters", char_count)

        if st.button("✨ Improve Response Quality", use_container_width=True):
            with st.spinner("Enhancing response quality with AI..."):
                improved = ai_service.improve_response_quality(
                    current_response, selected_competency, section_data, profession
                )

                if not improved.startswith("⚠️"):
                    st.success("✅ Response improved!")

                    # Enhanced display of improvements
                    if "**Improved Response:**" in improved:
                        parts = improved.split("**Improved Response:**")
                        explanation = parts[0].replace("**Improvement Analysis:**", "").strip()
                        improved_response = parts[1] if len(parts) > 1 else improved
                    else:
                        explanation = "AI has enhanced your response for better technical depth, clarity, and professional presentation."
                        improved_response = improved

                    # Improvement explanation
                    with st.expander("📊 Improvement Analysis", expanded=True):
                        st.write(explanation)

                        # Show word count comparison
                        new_word_count = len(improved_response.strip().split())
                        st.metric("New Word Count", new_word_count,
                                  delta=new_word_count - word_count)

                    # Improved response
                    st.text_area(
                        "✨ Improved Response",
                        value=improved_response.strip(),
                        height=250,
                        key="improved_response_display"
                    )

                    # Action buttons for the improved response
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Use This Version", type="primary", use_container_width=True):
                            # Update the response in session state
                            if selected_competency in st.session_state.responses.get(profession, {}):
                                st.session_state.responses[profession][selected_competency][
                                    'response'] = improved_response.strip()
                                st.success("Response updated! Don't forget to save your report.")
                                st.rerun()
                    with col2:
                        st.download_button(
                            "📥 Download Improved Response",
                            data=improved_response.strip(),
                            file_name=f"improved_{selected_competency}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                else:
                    st.error(improved)


def show_feedback_history():
    """Display AI feedback history"""
    st.subheader("📚 Feedback History")

    history = ai_service.get_feedback_history()

    if not history:
        st.info("No feedback history yet. Use AI features to generate feedback.")
        st.write("**Your AI feedback history will appear here after you:**")
        st.write("• Generate Smart Templates")
        st.write("• Run Gap Analysis")
        st.write("• Improve Response Quality")
        return

    # Show recent feedback with pagination
    st.write(f"**Recent AI Feedback ({len(history)} entries):**")

    for i, entry in enumerate(reversed(history[-5:])):  # Show last 5 entries
        with st.expander(f"📅 {entry['timestamp'][:16]} - {entry['section']}",
                         expanded=i == 0):
            st.write(entry['feedback'])

            # Quick actions for each entry
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📋 Copy", key=f"copy_{i}", use_container_width=True):
                    st.success("Feedback copied to clipboard!")
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                    # Remove from history
                    history.remove(entry)
                    st.success("Entry deleted!")
                    st.rerun()

    # Clear all history option
    if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
        ai_service.feedback_history.clear()
        st.success("All feedback history cleared!")
        st.rerun()