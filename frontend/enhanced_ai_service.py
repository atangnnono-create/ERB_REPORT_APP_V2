from openai import OpenAI, APIConnectionError, APIError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
import os
import streamlit as st
import json
from typing import Dict, List, Optional
from datetime import datetime
from services.enhanced_state_manager import state_manager

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(
        "❌ Missing OpenAI API key. Please set OPENAI_API_KEY environment variable. For technical assistance send email to fluidair2010@gmail.com")
    st.stop()

client = OpenAI(api_key=api_key)

# AI Templates for different competency types
AI_TEMPLATES = {
    "problem_solving": {
        "system_prompt": """You are an ERB engineering coach specializing in problem-solving competencies. Focus on helping users demonstrate ERB-style responses with: specific technical details, measurable outcomes, engineering methodology, and first-person professional narrative. Emphasize concrete examples with dates, locations, equipment names, and quantifiable results.""",

        "feedback_template": """**Competency Analysis:** {section_code} - {title}
**Professional Level:** {profession}

**User's Response:**
{text}

**Improved Response Example:**
[Provide a complete rewritten version using first-person professional engineering narrative.
Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover.Include: specific date/location (e.g., "On 23 February 2025 at
Morupule A Power Station"), equipment names, technical measurements, engineering methodology (FMEA, RCA, etc.), measurable 
 outcomes, and strategic alignment. Maintain user's core experiences while enhancing to ERB standards. 
 Stay within {word_limit} words and ensure it reads like a real ERB submission.]
**ERB Alignment Score:** X/10"""
    },

    "design_development": {
        "system_prompt": """You are an engineering design expert for ERB submissions. Focus on design methodology, technical specifications, material selection, and innovation. Emphasize ERB-style documentation with specific calculations, material justifications, and performance validation.""",

        "feedback_template": """**Design Competency:** {section_code} - {title}
**Professional Level:** {profession}
**User's Design Response:**
{text}


**Improved Design Response:**
[Provide a complete rewritten version using first-person professional engineering narrative.
 Include: specific design parameters, material selection justification (e.g., "stainless-steel alloy for acid resistance"), 
technical calculations, performance validation metrics, risk assessment, and cost-benefit 
analysis. Demonstrate engineering decision-making process. Include improvements for objectivity, 
clarity, and professionalism. Make sure your tone is factual, technical, and engineering-oriented 
fit fo+r an executive engineering audience.In your version include any core success indicators that the 
users response did not cover. Address these report success indicators: {indicators}]
**ERB Alignment Score:** X/10"""
    },

    "leadership_management": {
        "system_prompt": """You specialize in ERB leadership competencies. Focus on demonstrating leadership impact through specific examples of team coordination, stakeholder management, and project delivery. Emphasize ERB-style leadership narratives with concrete actions and measurable team outcomes.""",

        "feedback_template": """**Leadership Competency:** {title}
**Role:** {profession}

**Leadership Response:**
{text}

**Improved Leadership Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific 
leadership actions (e.g., "convened stakeholder planning meeting"), team coordination 
methods, stakeholder engagement details, measurable project outcomes, and leadership impact
 demonstration. Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover. Use first-person narrative showing personal responsibility. 
Address these report success indicators: {indicators}]
**ERB Alignment Score:** X/10"""
    },

    "continuous_quality_improvement": {
        "system_prompt": """You are a quality management expert for ERB submissions. Focus on quality systems implementation, improvement methodologies, and standards compliance. Emphasize ERB-style quality narratives with specific process changes, measurable improvements, and ISO standard alignment.""",

        "feedback_template": """**Quality Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Quality Response:**
{text}

**Improved Quality Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. 
Include: specific process improvements (e.g., "developed sootblowing process checklist"), measurable quality metrics, 
ISO standard references (ISO 9001, etc.), before/after performance data, and continuous 
improvement evidence. Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover. Address these report success indicators: {indicators}]
**ERB Alignment Score:** X/10"""
    },

    "effective_communication": {
        "system_prompt": """You are an engineering communication expert for ERB. Focus on technical documentation, cross-departmental coordination, and professional reporting. Emphasize ERB-style communication examples with specific meeting structures, reporting formats, and stakeholder engagement.""",

        "feedback_template": """**Communication Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Communication Response:**
{text}

**ERB Communication Evaluation:**
- **Strengths:** [Technical documentation quality, stakeholder engagement, reporting effectiveness]
- **Improvement Areas:** [Vague communication methods, missing cross-departmental examples, weak documentation evidence]
- **Specific Suggestions:** [Specify communication channels used, include meeting structures, demonstrate cross-department coordination]
- **ERB Alignment Score:** X/10

---

**Improved Communication Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. 
Include: specific communicationexamples (e.g., "chaired daily production meetings"), cross-departmental coordination details,
technical documentation created, stakeholder engagement methods, and communication outcomes. 
Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover.Address these report success indicators: {indicators}]"""
    },

    "proposals_and_justifications": {
        "system_prompt": """You are an engineering proposals expert for ERB. Focus on proposal clarity, technical justification, cost-benefit analysis, and strategic alignment. Emphasize ERB-style proposal writing with specific cost justifications, technical rationales, and business case development.""",

        "feedback_template": """**Proposal Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Proposal Response:**
{text}

**ERB Proposal Evaluation:**
- **Strengths:** [Proposal clarity, technical justification, cost-benefit analysis]
- **Improvement Areas:** [Weak cost justification, missing technical rationale, vague strategic alignment]
- **Specific Suggestions:** [Include specific cost calculations, technical specifications, business case development]
- **ERB Alignment Score:** X/10

---

**Improved Proposal Response:**
[Provide a complete rewritten version using first-person professional engineering narrative.
 Include: specific cost calculations(e.g., "P15630 x 40 drums = P625,630"), technical specifications, 
risk assessment, business case development, strategic alignment, and formal justification format. Include improvements
for objectivity, clarity, and professionalism. Make sure your tone is factual, technical, and 
engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover. Address these report success indicators: {indicators}]"""
    },

    "diversity_and_inclusion": {
        "system_prompt": """You are a workplace diversity expert for ERB. Focus on emotional intelligence, conflict resolution, team building, and inclusive practices. Emphasize ERB-style diversity narratives with specific team initiatives, conflict resolution examples, and measurable team outcomes.""",

        "feedback_template": """**Diversity Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Diversity Response:**
{text}

**ERB Diversity Assessment:**
- **Strengths:** [Team collaboration, conflict resolution, inclusive initiatives]
- **Improvement Areas:** [Vague team activities, missing conflict resolution details, weak inclusion evidence]
- **Specific Suggestions:** [Specify team building activities, detail conflict resolution process, demonstrate inclusion practices]
- **ERB Alignment Score:** X/10

---

**Improved Diversity Response:**
[Provide a complete rewritten version using first-person professional engineering narrative.
Include: specific team initiatives(e.g., "employee birthday celebrations"), conflict resolution 
process details, inclusive practices implemented, team collaboration outcomes, and cultural impact. 
Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include 
any core success indicators that the users response did not cover. Address these report success indicators: {indicators}]"""
    },

    "codes_of_conduct": {
        "system_prompt": """You are an engineering ethics expert for ERB. Focus on code compliance, ethical decision-making, and professional integrity. Emphasize ERB-style ethics examples with specific compliance situations, ethical dilemmas, and professional standards application.""",

        "feedback_template": """**Ethics Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Ethics Response:**
{text}

**ERB Ethics Evaluation:**
- **Strengths:** [Code compliance, ethical decision-making, professional integrity]
- **Improvement Areas:** [Vague ethical situations, missing compliance details, weak standards application]
- **Specific Suggestions:** [Specify ethical dilemmas faced, detail compliance actions, demonstrate standards application]
- **ERB Alignment Score:** X/10

---

**Improved Ethics Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific ethical dilemmas 
(e.g., "refusing to override alarm limits"), compliance actions taken, professional standards 
referenced, ethical decision-making process, and integrity demonstration. Include improvements
for objectivity, clarity, and professionalism. Make sure your tone is factual, technical, and
engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover. Address these report success indicators: {indicators}]"""
    },

    "occupational_safety_improvement": {
        "system_prompt": """You are a safety systems expert for ERB. Focus on risk management, safety culture, incident response, and regulatory compliance. Emphasize ERB-style safety narratives with specific incident responses, risk assessments, and safety system improvements.""",

        "feedback_template": """**Safety Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Safety Response:**
{text}

**ERB Safety Assessment:**
- **Strengths:** [Risk management, incident response, safety system implementation]
- **Improvement Areas:** [Vague safety actions, missing risk assessments, weak incident response details]
- **Specific Suggestions:** [Specify safety interventions, include risk assessment methods, detail incident response process]
- **ERB Alignment Score:** X/10

---

**Improved Safety Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific safety incidents 
(e.g., "lube oil spill containment"), risk assessment methods, emergency response coordination,
safety system improvements, and regulatory compliance. Include improvements for objectivity, 
clarity, and professionalism. Make sure your tone is factual, technical, and engineering-oriented 
fit for an executive engineering audience.In your version include any core success indicators that the users 
response did not cover.Address these report success indicators: {indicators}]"""
    },

    "sustainable_development_principles": {
        "system_prompt": """You are a sustainability expert for ERB. Focus on environmental impact reduction, resource efficiency, and sustainable practices. Emphasize ERB-style sustainability examples with specific environmental improvements, resource savings, and sustainable development applications.""",

        "feedback_template": """**Sustainability Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Sustainability Response:**
{text}

**ERB Sustainability Evaluation:**
- **Strengths:** [Environmental impact reduction, resource efficiency, sustainable practices]
- **Improvement Areas:** [Vague environmental actions, missing resource savings data, weak sustainability application]
- **Specific Suggestions:** [Specify environmental improvements, include resource savings calculations, demonstrate sustainable development principles]
- **ERB Alignment Score:** X/10

---

**Improved Sustainability Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific environmental 
improvements (e.g., "optimized boiler blowdown scheduling"), resource efficiency calculations, 
sustainable development principles applied, measurable environmental impact reduction, and business benefits. 
Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover.Address these report success indicators: {indicators}]"""
    },

    "ethical_issues": {
        "system_prompt": """You are an engineering ethics dilemma expert for ERB. Focus on ethical reasoning, moral principles, and professional conduct in challenging situations. Emphasize ERB-style ethical dilemma narratives with specific conflicts, decision-making processes, and integrity demonstrations.""",

        "feedback_template": """**Ethical Issues Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Ethical Response:**
{text}

**ERB Ethical Assessment:**
- **Strengths:** [Ethical dilemma recognition, moral reasoning, professional conduct]
- **Improvement Areas:** [Vague ethical conflicts, missing decision-making process, weak integrity demonstration]
- **Specific Suggestions:** [Specify ethical conflicts faced, detail decision-making rationale, demonstrate professional integrity]
- **ERB Alignment Score:** X/10

---

**Improved Ethical Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific ethical conflicts 
(e.g., "protecting confidential interview information"), decision-making process, professional 
standards applied, integrity demonstration, and ethical resolution.Include improvements for objectivity, 
clarity, and professionalism. Make sure your tone is factual,technical, and engineering-oriented fit
 for an executive engineering audience.In your version include any core success indicators that the users 
 response did not cover. Address these report success indicators: {indicators}]"""
    },

    "continuing_professional_development": {
        "system_prompt": """You are a CPD expert for ERB. Focus on professional development planning, competency enhancement, and career growth. Emphasize ERB-style CPD narratives with specific development activities, learning outcomes, and professional growth evidence.""",

        "feedback_template": """**CPD Competency:** {section_code} - {title}
**Professional Level:** {profession}
**CPD Response:**
{text}

**ERB CPD Assessment:**
- **Strengths:** [Development planning, learning activities, competency enhancement]
- **Improvement Areas:** [Vague development activities, missing learning outcomes, weak growth evidence]
- **Specific Suggestions:** [Specify development activities, include learning outcomes, demonstrate competency enhancement]
- **ERB Alignment Score:** X/10

---

**Improved CPD Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. 
Include: specific development activities, learning outcomes achieved, competency enhancement evidence, 
professional growth milestones, and future development planning. Include improvements for objectivity, 
clarity, and professionalism. Make sure your tone is factual, technical, and engineering-oriented fit for 
an executive engineering audience. In your version include any core success indicators that the users response 
did not cover. Address these report success indicators: {indicators}]"""
    },

    "initial_professional_development": {
        "system_prompt": """You are an IPD expert for ERB. Focus on initial competency development, gap assessment, and career foundation building. Emphasize ERB-style IPD narratives with specific skill development, knowledge gaps, and professional foundation establishment.""",

        "feedback_template": """**IPD Competency:** {section_code} - {title}
**Professional Level:** {profession}
**IPD Response:**
{text}

**ERB IPD Evaluation:**
- **Strengths:** [Gap assessment, development planning, competency foundation]
- **Improvement Areas:** [Vague skill development, missing gap analysis, weak foundation evidence]
- **Specific Suggestions:** [Specify skill development activities, include gap analysis details, demonstrate competency foundation building]
- **ERB Alignment Score:** X/10

---

**Improved IPD Response:**
[Provide a complete rewritten version using first-person professional engineering narrative. Include: specific skill development activities,
 knowledge gap analysis, competency foundation building, professional milestones, and ERB alignment planning.
  Include improvements for objectivity, clarity, and professionalism. Make sure your tone is factual, 
technical, and engineering-oriented fit for an executive engineering audience.In your version include any 
core success indicators that the users response did not cover.Address these report success indicators: {indicators}]"""
    }
}

# ERB-specific competency mappings
ERB_COMPETENCY_MAPPING = {
    "A1_1": "problem_solving",
    "A1_2": "problem_solving",
    "A2_1": "problem_solving",
    "A2_2": "problem_solving",
    "B1_1": "design_development",
    "B1_2": "design_development",
    "B2_1": "design_development",
    "B2_2": "design_development",
    "C1_1": "leadership_management",
    "C1_2": "leadership_management",
    "C2_1": "leadership_management",
    "C2_2": "leadership_management",
    "C3_1": "leadership_management",
    "C3_2": "leadership_management",
    "C4_1": "continuous_quality_improvement",
    "C4_2": "continuous_quality_improvement",
    "D1_1": "effective_communication",
    "D1_2": "effective_communication",
    "D2_1": "proposals_and_justifications",
    "D2_2": "proposals_and_justifications",
    "D3_1": "diversity_and_inclusion",
    "D3_2": "diversity_and_inclusion",
    "E1_1": "codes_of_conduct",
    "E1_2": "codes_of_conduct",
    "E2_1": "occupational_safety_improvement",
    "E2_2": "occupational_safety_improvement",
    "E3_1": "sustainable_development_principles",
    "E3_2": "sustainable_development_principles",
    "E4_1": "ethical_issues",
    "E4_2": "ethical_issues",
    "F1_1": "continuing_professional_development",
    "F1_2": "continuing_professional_development",
    "F2_1": "initial_professional_development",
    "F2_2": "initial_professional_development",
}


class AdvancedAIService:
    def __init__(self):
        self.client = client
        self.feedback_history = []
        self._setup_state_manager()

    def _setup_state_manager(self):
        """Initialize state manager for AI service"""
        state_manager.persist_key("ai_feedback_history")
        state_manager.persist_key("ai_template_preferences")
        state_manager.persist_key("ai_usage_stats")

        persisted_history = state_manager.get_state("ai_feedback_history")
        if persisted_history:
            self.feedback_history = persisted_history

    def get_template_type(self, section_code: str) -> str:
        """Get the appropriate template type for a competency"""
        return ERB_COMPETENCY_MAPPING.get(section_code)

    def get_enhanced_feedback(self, text: str, section_code: str, section_data: dict, profession: str) -> str:
        """Get enhanced AI feedback using specialized templates"""
        template_type = self.get_template_type(section_code)
        template = AI_TEMPLATES[template_type]

        prompt = template["feedback_template"].format(
            section_code=section_code,
            title=section_data['title'],
            indicators=', '.join(section_data.get('indicators', [])),
            instructions=section_data['instructions'],
            word_limit=section_data.get('word_limit', 500),
            profession=profession,
            text=text
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": template["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=3000,
                timeout=45,
            )

            feedback = self._safe_content(response)
            self._store_feedback_history(section_code, feedback)
            self.update_usage_stats("feedback")
            return feedback

        except APIConnectionError:
            return "🔌 Connection error – please check your internet connection and try again."
        except RateLimitError:
            return "⏳ Rate limit exceeded – please wait a few minutes before requesting more feedback."
        except AuthenticationError:
            return "🔑 Authentication error – please check your API key configuration."
        except Exception as e:
            return f"⚠️ Unexpected error: {str(e)}"

    def get_comprehensive_report_feedback(self, responses: dict, competency_data: dict, profession: str) -> str:
        """Get summary-level comprehensive feedback optimized for token limits"""
        compiled_summary = self._compile_summary_report(responses, competency_data, profession)

        prompt = f"""**ERB REPORT STRATEGIC ASSESSMENT**

    **Professional Category:** {profession}
    **Report Summary Analysis:**

    {compiled_summary}

    **As an experienced ERB assessor, provide strategic feedback focusing on:**

    **1. OVERALL SUBMISSION READINESS**
    - Based on completion rates and quality indicators, how ready is this report for ERB submission?
    - What is the overall strength and professionalism demonstrated?

    **2. COMPETENCY BALANCE ASSESSMENT**
    - How well balanced are the technical (A/B) vs professional (C/D/E) competencies?
    - Are there any critical gaps in series coverage?
    - Does the distribution match {profession} level expectations?

    **3. QUALITY PATTERN ANALYSIS**
    - What patterns do you see in response quality based on the metrics?
    - Are there consistent strengths or weaknesses across the report?
    - How strong is the evidence of engineering rigor and professional standards?

    **4. STRATEGIC IMPROVEMENT PRIORITIES**
    - Based on the summary data, what are the 3-5 highest impact improvements needed?
    - Should the focus be on completion, quality enhancement, or specific competency areas?
    - What quick wins would most improve ERB readiness?

    **5. SUBMISSION TIMELINE GUIDANCE**
    - Is this report close to submission ready, or does it need significant work?
    - What would be a realistic timeline for ERB submission preparation?

    **Provide concise, actionable strategic guidance. Suggest improvements for objectivity, clarity, 
    and professionalism. Make sure the tone is factual, technical, and engineering-oriented.Highlight 
    if it is missing any of the core indicators.Focus on patterns and priorities rather than detailed 
    line-by-line analysis.**"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": "You are a senior ERB assessor. Provide high-level strategic feedback on engineering competency reports. Focus on overall readiness, competency balance, and priority improvements. Be concise and actionable."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,  # Reduced since we're doing summary analysis
                timeout=60,
            )

            feedback = self._safe_content(response)
            self._store_feedback_history("full_report", feedback)
            self.update_usage_stats("feedback")
            return feedback

        except Exception as e:
            return f"⚠️ Error generating comprehensive feedback: {str(e)}"


    def _compile_summary_report(self, responses: dict, competency_data: dict, profession: str) -> str:
        """Compile metrics summary for comprehensive analysis"""
        if not responses or not isinstance(responses, dict):
            return "No competency responses available for analysis."

        # Initialize metrics tracking
        metrics = {
            'total_competencies': 0,
            'completed_competencies': 0,
            'series_counts': {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0},
            'series_completed': {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0},
            'total_word_count': 0,
            'quality_indicators': {
                'has_technical_terms': 0,
                'has_measurements': 0,
                'has_methodology': 0,
                'has_outcomes': 0,
                'good_length': 0
            },
            'word_count_ranges': {'0-100': 0, '101-300': 0, '301-500': 0, '500+': 0}
        }

        # Analyze each competency
        for key, response_data in responses.items():
            if key == '_status':
                continue

            try:
                # Extract response data
                response_text = ""
                word_count = 0

                if isinstance(response_data, dict):
                    response_text = response_data.get('response', '').strip()
                    word_count = len(response_text.split())
                elif isinstance(response_data, str):
                    response_text = response_data.strip()
                    word_count = len(response_text.split())

                if not response_text:
                    continue

                # Track competency completion
                metrics['total_competencies'] += 1
                if word_count >= 50:  # Minimum meaningful response
                    metrics['completed_competencies'] += 1

                # Track series distribution
                series = key[0] if key and key[0] in metrics['series_counts'] else None
                if series:
                    metrics['series_counts'][series] += 1
                    if word_count >= 50:
                        metrics['series_completed'][series] += 1

                # Track word count
                metrics['total_word_count'] += word_count

                # Track word count ranges
                if word_count <= 100:
                    metrics['word_count_ranges']['0-100'] += 1
                elif word_count <= 300:
                    metrics['word_count_ranges']['101-300'] += 1
                elif word_count <= 500:
                    metrics['word_count_ranges']['301-500'] += 1
                else:
                    metrics['word_count_ranges']['500+'] += 1

                # Analyze quality indicators (for substantial responses only)
                if word_count >= 100:
                    text_lower = response_text.lower()
                    if any(term in text_lower for term in ['analysis', 'method', 'approach', 'process']):
                        metrics['quality_indicators']['has_methodology'] += 1
                    if any(term in text_lower for term in ['result', 'outcome', 'achieved', 'improved']):
                        metrics['quality_indicators']['has_outcomes'] += 1
                    if any(term in text_lower for term in ['%', 'metric', 'measure', 'data', 'calculated']):
                        metrics['quality_indicators']['has_measurements'] += 1
                    if any(term in text_lower for term in ['technical', 'engineering', 'design', 'system']):
                        metrics['quality_indicators']['has_technical_terms'] += 1
                    if word_count >= 200:
                        metrics['quality_indicators']['good_length'] += 1

            except Exception:
                continue

        return self._format_summary_report(metrics, profession)

    def _format_summary_report(self, metrics: dict, profession: str) -> str:
        """Format metrics into analysis-ready summary"""
        if metrics['total_competencies'] == 0:
            return "No competencies available for analysis."

        completion_rate = (metrics['completed_competencies'] / metrics['total_competencies'] * 100)
        avg_word_count = metrics['total_word_count'] / metrics['completed_competencies'] if metrics[
                                                                                                'completed_competencies'] > 0 else 0

        summary = f"""
    **ERB REPORT SUMMARY - {profession.upper()}**

    **COMPLETION OVERVIEW:**
    - Total Competencies: {metrics['total_competencies']}
    - Completed Responses: {metrics['completed_competencies']} ({completion_rate:.1f}%)
    - Average Response Length: {avg_word_count:.0f} words
    - Total Word Count: {metrics['total_word_count']}

    **SERIES DISTRIBUTION (Completed/Total):**
    """

        # Add series breakdown
        for series in ["A", "B", "C", "D", "E", "F"]:
            if metrics['series_counts'][series] > 0:
                completed = metrics['series_completed'][series]
                total = metrics['series_counts'][series]
                completion_pct = (completed / total * 100) if total > 0 else 0
                series_type = "Technical" if series in ["A", "B"] else "Professional"
                summary += f"- Series {series} ({series_type}): {completed}/{total} ({completion_pct:.1f}%)\n"

        summary += f"""
    **RESPONSE LENGTH DISTRIBUTION:**
    - Brief (0-100 words): {metrics['word_count_ranges']['0-100']}
    - Moderate (101-300 words): {metrics['word_count_ranges']['101-300']}  
    - Comprehensive (301-500 words): {metrics['word_count_ranges']['301-500']}
    - Extensive (500+ words): {metrics['word_count_ranges']['500+']}

    **QUALITY INDICATORS (Substantial Responses Only):**
    - Technical Terminology: {metrics['quality_indicators']['has_technical_terms']}
    - Engineering Methodology: {metrics['quality_indicators']['has_methodology']}
    - Measurable Outcomes: {metrics['quality_indicators']['has_outcomes']}
    - Performance Metrics: {metrics['quality_indicators']['has_measurements']}
    - Good Length (200+ words): {metrics['quality_indicators']['good_length']}
    """

        return summary



    def _compile_erb_optimized_report(self, responses: dict, competency_data: dict, profession: str) -> str:
        """ERB-optimized report compilation focusing on assessment quality"""
        if not responses or not isinstance(responses, dict):
            return "No completed competencies available for assessment."

        report_parts = []
        competency_series = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}

        for key, response_data in responses.items():
            if key == '_status':
                continue

            try:
                # Extract response text safely
                response_text = ""
                word_count = 0

                if isinstance(response_data, dict):
                    response_text = response_data.get('response', '').strip()
                    word_count = response_data.get('word_count', 0) or len(response_text.split())
                elif isinstance(response_data, str):
                    response_text = response_data.strip()
                    word_count = len(response_text.split())

                if not response_text or word_count < 50:  # Minimum meaningful content
                    continue

                # Get competency details
                title = "Unknown Competency"
                indicators = []

                if key in competency_data and isinstance(competency_data[key], dict):
                    title = competency_data[key].get('title', 'Unknown Competency')
                    indicators = competency_data[key].get('indicators', [])

                # Track competency series distribution
                series = key[0] if key and key[0] in competency_series else "Other"
                if series in competency_series:
                    competency_series[series] += 1

                # ERB-optimized formatting
                report_parts.append(f"""
    **{key}: {title}**
    Indicators: {', '.join(indicators) if indicators else 'Not specified'}
    Word Count: {word_count}
    Content: {response_text}
    ───────────────────────────────""")

            except Exception as e:
                print(f"Warning: Could not compile competency {key}: {e}")
                continue

        # Add competency distribution summary
        if report_parts:
            distribution_summary = "\n**COMPETENCY DISTRIBUTION SUMMARY:**\n"
            for series, count in competency_series.items():
                if count > 0:
                    distribution_summary += f"- Series {series}: {count} competencies\n"

            report_parts.insert(0, distribution_summary)
            report_parts.insert(0, f"**ERB REPORT ANALYSIS - {profession.upper()}**")
            report_parts.insert(1, f"**Total Meaningful Competencies:** {len(report_parts) - 3}")
        else:
            return "No substantial competency responses found for comprehensive analysis."

        return "\n".join(report_parts)


    def generate_competency_template(self, section_code: str, section_data: dict, profession: str,
                                     style: str = "Professional", include_examples: bool = True) -> str:
        """Generate an ERB-optimized template response for a competency"""
        prompt = f"""**ERB COMPETENCY TEMPLATE GENERATION**

    **Competency:** {section_code} - {section_data['title']}
    **Professional Level:** {profession}
    **Template Style:** {style}
    **Include Realistic Examples:** {include_examples}
    **Key Indicators to Address:** {', '.join(section_data.get('indicators', []))}
    **Target Word Count:** {section_data.get('word_limit', 500)}
    **Competency Instructions:** {section_data['instructions']}

    **Generate an ERB-optimized template that demonstrates:**

    **1. ERB PROFESSIONAL STRUCTURE**
    - Use first-person professional narrative throughout
    - Follow ERB example format with clear example headings
    - Include specific dates, locations, and equipment references
    - Maintain professional engineering tone for {profession} level

    **2. TECHNICAL DEPTH & EVIDENCE**
    - Demonstrate engineering methodologies (FMEA, RCA, risk assessment, etc.)
    - Include measurable outcomes and performance metrics
    - Show technical specifications and calculations where appropriate
    - Reference relevant standards (ISO, safety protocols, etc.)

    **3. COMPETENCY INDICATOR ALIGNMENT**
    - Clearly address each indicator: {', '.join(section_data.get('indicators', []))}
    - Show progression from problem identification to solution implementation
    - Demonstrate professional responsibility and decision-making

    **4. PRACTICAL CUSTOMIZATION GUIDANCE**
    - Use [BRACKETED_PLACEHOLDERS] for project-specific details
    - Provide clear sections for easy user modification
    - Include guidance on what details to customize

    {'**5. REALISTIC ERB EXAMPLES**' if include_examples else ''}
    {'• Include 2 concrete examples following ERB report structure' if include_examples else ''}
    {'• Each example should have specific technical context and outcomes' if include_examples else ''}
    {'• Examples should demonstrate different scenarios/situations' if include_examples else ''}

    **Format the template to be immediately usable for ERB submission preparation.**"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": f"""You are an ERB preparation expert creating professional competency templates. 
                     Create templates that mirror real ERB submission style with:
                     - First-person professional narrative
                     - Specific technical details and dates
                     - Measurable engineering outcomes
                     - Professional structure and formatting
                     - Clear placeholders for easy customization
                     Style: {style.lower()}"""},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,  # Balanced for consistency with some creativity
                max_tokens=1800,  # Increased for comprehensive templates
            )

            template = self._safe_content(response)
            self._store_feedback_history(section_code, f"Generated ERB {style} template")
            self.update_usage_stats("template")
            return template

        except Exception as e:
            return f"⚠️ Error generating template: {str(e)}"

    def analyze_competency_gaps(self, responses, competency_data, profession):
        """Enhanced gap analysis using summary metrics"""
        try:
            # Use our new summary compilation for consistent analysis
            compiled_summary = self._compile_summary_report(responses, competency_data, profession)

            prompt = f"""**ERB GAP ANALYSIS REQUEST**

    **Professional Role:** {profession}
    **Report Summary:** {compiled_summary}

    **Identify critical gaps and provide strategic recommendations for ERB submission preparation.**"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": "You are an ERB preparation expert. Analyze competency gaps and provide strategic recommendations for improvement."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1200,
            )

            analysis = self._safe_content(response)
            return analysis

        except Exception as e:
            return f"Basic gap analysis: Error processing data - {str(e)}"



    def improve_response_quality(self, text: str, section_code: str, section_data: dict, profession: str) -> str:
        """Provide ERB-optimized improvements for a competency response"""
        prompt = f"""**ERB RESPONSE QUALITY ENHANCEMENT**

    **Competency:** {section_code} - {section_data['title']}
    **Professional Level:** {profession}
    **Key Indicators:** {', '.join(section_data.get('indicators', []))}
    **Target Word Count:** {section_data.get('word_limit', 500)}

    **Current Response:**
    {text}

    **Transform this response into an ERB-ready submission by enhancing:**

    **1. ERB PROFESSIONAL STRUCTURE**
    - Convert to first-person professional narrative
    - Use ERB example format with clear example headings
    - Add specific dates, locations, and equipment references
    - Maintain professional engineering tone for {profession} level

    **2. TECHNICAL DEPTH & ENGINEERING RIGOR**
    - Incorporate engineering methodologies (FMEA, RCA, risk assessment, weighted matrices)
    - Add specific technical specifications and measurements
    - Include calculations, performance metrics, and quantifiable results
    - Reference relevant standards (ISO, safety protocols, regulatory requirements)

    **3. EVIDENCE-BASED OUTCOMES**
    - Strengthen with measurable before/after comparisons
    - Add specific performance metrics and business impact
    - Demonstrate strategic alignment (e.g., Maduo 2026, corporate objectives)
    - Show cost-benefit analysis where appropriate

    **4. COMPETENCY INDICATOR ALIGNMENT**
    - Ensure clear demonstration of: {', '.join(section_data.get('indicators', []))}
    - Show professional responsibility and decision-making
    - Demonstrate progressive problem-solving approach

    **5. PROFESSIONAL COMMUNICATION**
    - Enhance clarity and professional tone
    - Improve logical flow and structure
    - Use appropriate engineering terminology
    - Ensure readability for ERB assessors

    **Format your response as:**

    **Improvement Analysis:**
    [Specific enhancements made and their importance for ERB assessment. Focus on technical depth, evidence quality, and professional standards.]

    **Improved Response:**
    [Complete ERB-ready response following professional format with 2 concrete examples, specific technical details, measurable outcomes, and first-person narrative. Maintain original experiences while elevating to ERB standards.]

    Ensure the improved response stays within approximately {section_data.get('word_limit', 500)} words and is immediately usable for ERB submission."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": """You are an ERB submission specialist and engineering editor. Your expertise is transforming basic responses into professional ERB-ready submissions. You excel at:
    - Converting responses to first-person professional ERB narrative style
    - Adding specific technical details, dates, and measurable outcomes
    - Incorporating engineering methodologies and standards references
    - Enhancing evidence quality with quantifiable results
    - Maintaining authenticity while elevating professional rigor
    - Structuring responses with clear example formats
    Focus on creating submissions that would impress ERB assessors with their technical depth and professional quality."""},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Consistent for quality improvements
                max_tokens=2500,  # Increased for comprehensive enhancements
            )

            improved = self._safe_content(response)
            self._store_feedback_history(section_code, "ERB response quality improvement applied")
            self.update_usage_stats("quality_improvement")
            return improved

        except Exception as e:
            return f"⚠️ Error improving response: {str(e)}"

    def _compile_full_report(self, responses: dict, competency_data: dict) -> str:
        """Compile ERB-optimized full report for comprehensive analysis"""
        report_parts = []

        if not responses or not isinstance(responses, dict):
            return "No competency responses available for analysis."

        # Track competency series distribution for analysis
        series_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        total_word_count = 0
        completed_competencies = 0

        for key, response_data in responses.items():
            if key == '_status':
                continue

            try:
                # Safely extract response text and metadata
                response_text = ""
                word_count = 0

                if isinstance(response_data, dict):
                    response_text = response_data.get('response', '').strip()
                    word_count = response_data.get('word_count', 0) or len(response_text.split())
                elif isinstance(response_data, str):
                    response_text = response_data.strip()
                    word_count = len(response_text.split())
                else:
                    response_text = str(response_data)
                    word_count = len(response_text.split())

                # Skip empty or very short responses
                if not response_text or word_count < 50:
                    continue

                # Get competency details
                title = "Unknown Competency"
                indicators = []
                instructions = ""

                if key in competency_data and isinstance(competency_data[key], dict):
                    competency = competency_data[key]
                    title = competency.get('title', 'Unknown Competency')
                    indicators = competency.get('indicators', [])
                    instructions = competency.get('instructions', '')

                # Track series distribution
                series = key[0] if key and key[0] in series_counts else "Other"
                if series in series_counts:
                    series_counts[series] += 1

                total_word_count += word_count
                completed_competencies += 1

                # ERB-optimized formatting for better AI analysis
                report_parts.append(f"""
    **{key}: {title}**

    *Competency Indicators:* {', '.join(indicators) if indicators else 'Not specified'}
    *Word Count:* {word_count}
    *Response Content:*

    {response_text}

    {'─' * 80}
    """)

            except Exception as e:
                print(f"Warning: Could not compile report for competency {key}: {e}")
                continue

        # Add comprehensive report header with metadata
        if report_parts:
            # Calculate series percentages
            series_analysis = ""
            for series in ["A", "B", "C", "D", "E", "F"]:
                if series_counts[series] > 0:
                    series_analysis += f"- Section {series}: {series_counts[series]} competencies\n"

            header = f"""
    **ERB COMPETENCY REPORT - COMPREHENSIVE ANALYSIS**

    **Report Overview:**
    - Total Competencies Completed: {completed_competencies}
    - Total Word Count: {total_word_count}
    - Average Response Length: {total_word_count // completed_competencies if completed_competencies else 0} words

    **Competency Distribution:**
    {series_analysis}

    **Detailed Competency Responses:**
    ────────────────────────────────────────────────────────────────────────────────
    """
            report_parts.insert(0, header)

            # Add footer with analysis context
            footer = f"""
    **END OF REPORT**
    Total meaningful competencies analyzed: {completed_competencies}
    Report compiled for ERB assessment preparation.
    """
            report_parts.append(footer)

            return "\n".join(report_parts)
        else:
            return "No substantial competency responses found for comprehensive analysis."


    def _store_feedback_history(self, section: str, feedback: str):
        """Store feedback in history with state manager persistence"""
        self.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'section': section,
            'feedback': feedback[:500] + "..." if len(feedback) > 500 else feedback
        })

        # Keep only last 20 entries
        if len(self.feedback_history) > 20:
            self.feedback_history.pop(0)

        # Persist feedback history using state manager
        state_manager.set_state("ai_feedback_history", self.feedback_history, persist=True)

    def get_feedback_history(self) -> List[Dict]:
        """Get feedback history with state manager fallback"""
        persisted_history = state_manager.get_state("ai_feedback_history")
        if persisted_history:
            self.feedback_history = persisted_history
        return self.feedback_history

    def clear_feedback_history(self):
        """Clear feedback history with state manager integration"""
        self.feedback_history = []
        state_manager.clear_persisted("ai_feedback_history")
        return "Feedback history cleared successfully!"

    def get_ai_usage_stats(self) -> Dict:
        """Get AI usage statistics with state manager persistence"""
        stats = state_manager.get_state("ai_usage_stats") or {
            "total_feedback_requests": 0,
            "total_template_generations": 0,
            "total_gap_analyses": 0,
            "total_quality_improvements": 0,
            "last_activity": None
        }

        state_manager.set_state("ai_usage_stats", stats, persist=True)
        return stats

    def update_usage_stats(self, action_type: str):
        """Update usage statistics for AI features"""
        stats = self.get_ai_usage_stats()

        if action_type == "feedback":
            stats["total_feedback_requests"] += 1
        elif action_type == "template":
            stats["total_template_generations"] += 1
        elif action_type == "gap_analysis":
            stats["total_gap_analyses"] += 1
        elif action_type == "quality_improvement":
            stats["total_quality_improvements"] += 1

        stats["last_activity"] = datetime.now().isoformat()
        state_manager.set_state("ai_usage_stats", stats, persist=True)

    def save_template_preferences(self, preferences: Dict):
        """Save user template preferences with state manager"""
        state_manager.set_state("ai_template_preferences", preferences, persist=True)

    def get_template_preferences(self) -> Dict:
        """Get user template preferences with state manager fallback"""
        return state_manager.get_state("ai_template_preferences") or {
            "default_style": "Professional",
            "include_examples": True,
            "preferred_templates": {}
        }

    def export_ai_data(self) -> Dict:
        """Export all AI-related data for backup"""
        return {
            "feedback_history": self.get_feedback_history(),
            "usage_stats": self.get_ai_usage_stats(),
            "template_preferences": self.get_template_preferences(),
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }

    def import_ai_data(self, data: Dict):
        """Import AI data from backup"""
        if "feedback_history" in data:
            self.feedback_history = data["feedback_history"]
            state_manager.set_state("ai_feedback_history", self.feedback_history, persist=True)

        if "usage_stats" in data:
            state_manager.set_state("ai_usage_stats", data["usage_stats"], persist=True)

        if "template_preferences" in data:
            state_manager.set_state("ai_template_preferences", data["template_preferences"], persist=True)

    def _safe_content(self, response) -> str:
        """Safely extract content from OpenAI response"""
        try:
            if hasattr(response, "choices") and response.choices:
                first_choice = response.choices[0]
                if hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                    return str(first_choice.message.content).strip()
            return "⚠️ No valid content found in the response."
        except Exception as e:
            return f"⚠️ Error extracting content: {e}"


# Global AI service instance
ai_service = AdvancedAIService()


# Backward compatibility functions
def get_gpt_feedback(text, section_code, section_data, profession):
    """Legacy function for backward compatibility"""
    ai_service.update_usage_stats("feedback")
    return ai_service.get_enhanced_feedback(text, section_code, section_data, profession)


def get_full_report_feedback(responses, competency_data, profession):
    """Legacy function for backward compatibility"""
    ai_service.update_usage_stats("feedback")
    return ai_service.get_comprehensive_report_feedback(responses, competency_data, profession)