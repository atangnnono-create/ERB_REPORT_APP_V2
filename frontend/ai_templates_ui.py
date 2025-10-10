import streamlit as st
from services.enhanced_ai_service import AdvancedAIService

ai_service = AdvancedAIService()


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

    selected_competency = st.selectbox(
        "Select competency for template:",
        options=list(competency_sections.keys()),
        format_func=lambda x: f"{x}: {competency_sections[x]['title']}"
    )

    if selected_competency:
        section_data = competency_sections[selected_competency]

        st.write(f"**{selected_competency}: {section_data['title']}**")
        st.info(section_data['instructions'])
        st.write(f"**Indicators:** {', '.join(section_data.get('indicators', []))}")

        if st.button("🎯 Generate Smart Template", use_container_width=True):
            with st.spinner("Generating high-quality template..."):
                template = ai_service.generate_competency_template(
                    selected_competency, section_data, profession
                )

                if not template.startswith("⚠️"):
                    st.success("✅ Template generated successfully!")
                    st.text_area(
                        "Generated Template",
                        value=template,
                        height=300,
                        key=f"template_{selected_competency}"
                    )

                    # Copy to clipboard functionality
                    st.download_button(
                        "📋 Copy Template",
                        data=template,
                        file_name=f"template_{selected_competency}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(template)


def show_gap_analysis(current_responses: dict, competency_sections: dict, profession: str):
    """Competency gap analysis"""
    st.subheader("🔍 Competency Gap Analysis")

    completed_count = len([r for r in current_responses.values() if r.get('response', '').strip()])
    total_count = len(competency_sections)

    st.metric("Completion Progress", f"{completed_count}/{total_count}")
    st.progress(completed_count / total_count if total_count > 0 else 0)

    if completed_count == 0:
        st.info("Start completing competencies to get gap analysis.")
        return

    if st.button("📊 Analyze Gaps", use_container_width=True):
        with st.spinner("Analyzing competency gaps..."):
            analysis = ai_service.analyze_competency_gaps(
                current_responses, competency_sections, profession
            )

            if not analysis.startswith("⚠️"):
                st.success("✅ Gap analysis completed!")

                # Display in expandable sections for better readability
                lines = analysis.split('\n')
                current_section = ""
                current_content = []

                for line in lines:
                    if line.strip().endswith(':') or (
                            line.strip() and not line.startswith(' ') and not line.startswith('-')):
                        # Save previous section
                        if current_section and current_content:
                            with st.expander(current_section,
                                             expanded=current_section == "1. Critical Missing Competencies"):
                                st.write('\n'.join(current_content))

                        current_section = line.strip()
                        current_content = []
                    else:
                        current_content.append(line)

                # Don't forget the last section
                if current_section and current_content:
                    with st.expander(current_section):
                        st.write('\n'.join(current_content))
            else:
                st.error(analysis)


def show_quality_improver(competency_sections: dict, profession: str, current_responses: dict):
    """Response quality improvement"""
    st.subheader("📈 Response Quality Improver")

    # Only show competencies that have responses
    competencies_with_responses = {
        k: v for k, v in competency_sections.items()
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
        section_data = competency_sections[selected_competency]
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
            st.write("**Word Count**")
            word_count = len(current_response.split())
            target_count = section_data.get('word_limit', 500)
            st.metric("Words", word_count, delta=f"Target: {target_count}")

            if st.button("✨ Improve Response", use_container_width=True):
                with st.spinner("Enhancing response quality..."):
                    improved = ai_service.improve_response_quality(
                        current_response, selected_competency, section_data, profession
                    )

                    if not improved.startswith("⚠️"):
                        st.success("✅ Response improved!")

                        # Split improved response and explanations
                        if "**Improved Response:**" in improved:
                            parts = improved.split("**Improved Response:**")
                            explanation = parts[0]
                            improved_response = parts[1] if len(parts) > 1 else improved
                        else:
                            explanation = "Improvements applied to enhance technical depth and professionalism."
                            improved_response = improved

                        with st.expander("📝 Improvement Explanation"):
                            st.write(explanation)

                        st.text_area(
                            "Improved Response",
                            value=improved_response.strip(),
                            height=200,
                            key="improved_response"
                        )

                        # Option to replace current response
                        if st.button("🔄 Use Improved Version", type="primary"):
                            # This would need to be integrated with your state management
                            st.success("Response updated! Don't forget to save your changes.")
                    else:
                        st.error(improved)


def show_feedback_history():
    """Display AI feedback history"""
    st.subheader("📚 Feedback History")

    history = ai_service.get_feedback_history()

    if not history:
        st.info("No feedback history yet. Use AI features to generate feedback.")
        return

    for i, entry in enumerate(reversed(history)):
        with st.expander(f"📅 {entry['timestamp'][:16]} - {entry['section']}"):
            st.write(entry['feedback'])

        if i >= 4:  # Show only last 5 entries in detail
            break

    # Clear history option
    if st.button("🗑️ Clear History", type="secondary"):
        ai_service.feedback_history.clear()
        st.success("Feedback history cleared!")
        st.rerun()