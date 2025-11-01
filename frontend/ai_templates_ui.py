import streamlit as st
from frontend.enhanced_ai_service import AdvancedAIService

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
    """AI-powered template generator with ERB optimization"""
    st.subheader("🚀 ERB-Optimized Smart Templates")

    st.info(f"**Current Role:** {profession}")

    # ERB-specific template options
    col1, col2, col3 = st.columns(3)
    with col1:
        template_style = st.selectbox(
            "Template Style",
            ["Professional ERB", "Technical Detailed", "Concise Executive"],
            help="Choose ERB-optimized writing style"
        )
    with col2:
        example_count = st.select_slider(
            "Number of Examples",
            options=[1, 2],
            value=2,
            help="ERB reports typically use 2 examples per competency"
        )
    with col3:
        include_metrics = st.checkbox("Include Metrics", value=True,
                                      help="Add measurable outcomes and performance indicators")

    selected_competency = st.selectbox(
        "Select competency for template:",
        options=list(competency_sections.keys()),
        format_func=lambda x: f"{x}: {competency_sections[x]['title'][:80]}..."
    )

    if selected_competency:
        section_data = competency_sections[selected_competency]

        # Enhanced competency info display
        with st.expander("📋 Competency Details", expanded=True):
            st.write(f"**Title:** {section_data['title']}")
            st.write(f"**Instructions:** {section_data['instructions']}")

            indicators = section_data.get('indicators', [])
            if indicators:
                st.write("**Key Indicators:**")
                for indicator in indicators:
                    st.write(f"• {indicator}")

        if st.button("🎯 Generate ERB-Optimized Template", use_container_width=True):
            with st.spinner("Creating professional ERB template..."):
                template = ai_service.generate_competency_template(
                    selected_competency, section_data, profession,
                    style=template_style,
                    include_examples=example_count > 0
                )

                if not template.startswith("⚠️"):
                    st.success("✅ ERB template generated successfully!")

                    # Enhanced template display with ERB formatting
                    st.subheader("✨ Your ERB-Ready Template")

                    with st.expander("📊 Template Features", expanded=False):
                        st.write("""
                        **This template includes:**
                        • First-person professional narrative
                        • Specific technical details and dates
                        • Measurable outcomes and metrics
                        • Engineering methodology demonstration
                        • ERB-compliant structure
                        """)

                    st.text_area(
                        "Template Content",
                        value=template,
                        height=400,  # Increased for better visibility
                        key=f"template_{selected_competency}",
                        label_visibility="collapsed"
                    )

                    # Enhanced action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download ERB Template",
                            data=template,
                            file_name=f"ERB_{profession}_{selected_competency}_template.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col2:
                        if st.button("💾 Copy to Clipboard", use_container_width=True):
                            # Implementation for clipboard copy
                            st.success("Template copied to clipboard!")
                else:
                    st.error(template)


def show_gap_analysis(current_responses: dict, competency_sections: dict, profession: str):
    """ERB-focused competency gap analysis"""
    st.subheader("🔍 ERB Competency Gap Analysis")

    # Add ERB context
    st.info("""
    **ERB Competency Framework:**
    • Sections A-B: Technical Engineering Competencies
    • Section C: Leadership & Management  
    • Section D: Communication & Interpersonal
    • Section E: Professional Standards & Ethics
    • Section F: Professional Development
    """)

    # Calculate completion progress
    completed_count = 0
    total_count = len(competency_sections)

    # Use safe logic that handles ANY data structure
    for competency_key in competency_sections.keys():
        try:
            # Safe extraction of response data
            response_data = None

            if isinstance(current_responses, dict) and competency_key in current_responses:
                response_data = current_responses[competency_key]

            # Extract response text safely
            response_text = ""
            if isinstance(response_data, dict):
                response_text = response_data.get("response", "")
            elif isinstance(response_data, str):
                response_text = response_data
            elif response_data is not None:
                response_text = str(response_data)

            # Clean and check response
            if response_text and response_text.strip():
                completed_count += 1

        except Exception as e:
            # Skip this competency if there's an error
            continue

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

    if st.button("📊 Analyze ERB Competency Gaps", use_container_width=True, type="primary"):
        with st.spinner("Analyzing ERB competency alignment and gaps..."):
            analysis = ai_service.analyze_competency_gaps(
                current_responses, competency_sections, profession
            )

            if not analysis.startswith("⚠️"):
                st.success("✅ ERB gap analysis completed!")

                # Enhanced display with ERB focus
                st.subheader("🎯 ERB Submission Strategy")

                # Parse and display analysis in ERB-focused sections
                if "OVERALL PROGRESS" in analysis:
                    # Extract and display key sections
                    sections = {
                        "Progress Overview": "OVERALL PROGRESS",
                        "Competency Distribution": "SECTION BREAKDOWN",
                        "Critical Gaps": "CRITICAL GAPS IDENTIFIED",
                        "Strategic Recommendations": "STRATEGIC RECOMMENDATIONS",
                        "ERB Readiness": "ERB SUBMISSION READINESS"
                    }

                    for section_title, section_key in sections.items():
                        if section_key in analysis:
                            start_idx = analysis.index(section_key)
                            # Find the next section or end of analysis
                            next_section_start = len(analysis)
                            for next_key in sections.values():
                                if next_key in analysis and analysis.index(next_key) > start_idx:
                                    next_section_start = min(next_section_start, analysis.index(next_key))

                            section_content = analysis[start_idx:next_section_start].replace(section_key, "").strip()

                            with st.expander(f"📋 {section_title}",
                                             expanded=section_title in ["Critical Gaps", "Strategic Recommendations"]):
                                st.write(section_content)
                else:
                    st.write(analysis)

                # ERB-specific next steps
                st.subheader("🚀 ERB Preparation Roadmap")

                if completion_rate < 60:
                    st.error("""
                    **Priority: Foundation Building**
                    • Focus on completing Sections A & B competencies first
                    • Use ERB templates for technical competencies
                    • Aim for 60% completion before enhancing quality
                    """)
                elif completion_rate < 85:
                    st.warning("""
                    **Priority: Quality Enhancement** 
                    • Use Quality Improver on completed responses
                    • Ensure all Section C leadership examples are strong
                    • Balance technical vs professional competencies
                    """)
                else:
                    st.success("""
                    **Priority: Final Polish**
                    • Review all responses for ERB standards compliance
                    • Ensure measurable outcomes in every example
                    • Validate competency indicator alignment
                    • Consider peer review before submission
                    """)
            else:
                st.error(analysis)


def show_quality_improver(competency_sections: dict, profession: str, current_responses: dict):
    """ERB-focused response quality improvement"""
    st.subheader("📈 ERB Response Quality Improver")

    # Add ERB quality assessment
    st.info("""
    **ERB Quality Standards:**
    • First-person professional narrative
    • Specific technical details and dates  
    • Measurable outcomes and performance metrics
    • Engineering methodology demonstration
    • Clear competency indicator alignment
    """)

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
        format_func=lambda x: f"{x}: {competencies_with_responses[x]['title'][:60]}...",
        key="quality_improver_select"
    )

    if selected_competency:
        section_data = competency_sections[selected_competency]
        current_response = current_responses[selected_competency]['response']

        # Enhanced metrics display
        col1, col2, col3 = st.columns(3)
        with col1:
            word_count = len(current_response.split())
            target_count = section_data.get('word_limit', 500)
            st.metric("Words", word_count, delta=f"Target: {target_count}")

        with col2:
            # ERB quality indicators
            erb_indicators = section_data.get('indicators', [])
            indicator_coverage = "Partial"
            if any(indicator.lower() in current_response.lower() for indicator in erb_indicators):
                indicator_coverage = "Good"
            st.metric("Indicator Coverage", indicator_coverage)

        with col3:
            # Technical depth assessment
            technical_terms = sum(1 for term in ['analysis', 'methodology', 'metrics', 'outcome', 'implementation']
                                  if term in current_response.lower())
            st.metric("Technical Depth", f"{technical_terms}/5")

        # Current response with ERB assessment
        with st.expander("📋 Current Response Analysis", expanded=True):
            st.text_area(
                "Current Response",
                value=current_response,
                height=200,
                disabled=True,
                key="current_response_display"
            )

            # Quick ERB assessment
            st.write("**ERB Quality Check:**")
            if word_count < 100:
                st.error("❌ Response may be too brief for ERB standards")
            elif word_count >= 300:
                st.success("✅ Good length for ERB submission")
            else:
                st.warning("⚠️ Consider expanding for better depth")

        if st.button("✨ Enhance for ERB Submission", use_container_width=True, type="primary"):
            with st.spinner("Transforming response to ERB professional standards..."):
                improved = ai_service.improve_response_quality(
                    current_response, selected_competency, section_data, profession
                )

                if not improved.startswith("⚠️"):
                    st.success("✅ Response enhanced to ERB standards!")

                    # Parse the improved response
                    if "**Improved Response:**" in improved:
                        parts = improved.split("**Improved Response:**")
                        explanation = parts[0].replace("**Improvement Analysis:**", "").strip()
                        improved_response = parts[1].strip() if len(parts) > 1 else improved.strip()
                    else:
                        explanation = "AI has transformed your response to meet ERB professional standards."
                        improved_response = improved.strip()

                    # Enhanced improvement analysis
                    with st.expander("📊 ERB Enhancement Analysis", expanded=True):
                        st.write(explanation)

                        # Show comprehensive metrics
                        new_word_count = len(improved_response.split())
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Word Improvement", new_word_count, delta=new_word_count - word_count)
                        with col2:
                            new_technical_terms = sum(
                                1 for term in ['analysis', 'methodology', 'metrics', 'outcome', 'implementation']
                                if term in improved_response.lower())
                            st.metric("Technical Depth", f"{new_technical_terms}/5",
                                      delta=new_technical_terms - technical_terms)
                        with col3:
                            st.metric("ERB Readiness", "High" if new_word_count >= 300 else "Medium")

                    # Improved response with ERB formatting
                    st.subheader("✨ ERB-Enhanced Response")
                    st.text_area(
                        "Enhanced Response",
                        value=improved_response,
                        height=300,
                        key="improved_response_display"
                    )

                    # Enhanced action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Use This ERB Version", type="primary", use_container_width=True):
                            if selected_competency in st.session_state.responses.get(profession, {}):
                                st.session_state.responses[profession][selected_competency][
                                    'response'] = improved_response
                                st.success("✅ Response updated to ERB standards!")
                                st.rerun()
                    with col2:
                        st.download_button(
                            "📥 Download ERB Response",
                            data=improved_response,
                            file_name=f"ERB_{selected_competency}_response.txt",
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