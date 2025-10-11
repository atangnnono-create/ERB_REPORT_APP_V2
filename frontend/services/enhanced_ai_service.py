from openai import OpenAI, APIConnectionError, APIError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
import os
import streamlit as st
import json
from typing import Dict, List, Optional
from datetime import datetime

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
        "system_prompt": """You are an expert engineering coach specializing in ERB (Engineer Registration Board) report preparation. 
        You provide specific, actionable feedback that helps engineers demonstrate their competencies effectively.

        Focus on:
        - Technical accuracy and depth
        - Alignment with ERB competency indicators
        - Professional engineering language
        - Evidence-based examples
        - Structured problem-solving approach""",

        "feedback_template": """Analyze this engineering competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Technical depth and accuracy
2. Evidence of engineering methodology
3. Alignment with competency indicators
4. Professional communication
5. Areas for improvement

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },

    "design_development": {
        "system_prompt": """You are an engineering design expert coaching professionals on ERB design competency submissions.
        Focus on design methodology, innovation, and technical rigor.""",

        "feedback_template": """Review this design competency response:

**Competency:** {section_code} - {title}
**Professional Level:** {profession}
**Key Requirements:** {instructions}

**Design Response:**
{text}

**Evaluate:**
- Design methodology and process
- Technical specifications and calculations
- Innovation and creativity
- Risk and constraint consideration
- Professional documentation

**Provide structured feedback with examples.**"""
    },

    "leadership_management": {
        "system_prompt": """You specialize in engineering leadership and management competencies for ERB submissions.
        Focus on leadership impact, team management, and project delivery.""",

        "feedback_template": """Assess this leadership/management competency:

**Competency:** {title}
**Role:** {profession}
**Context:** {instructions}

**Candidate's Response:**
{text}

**Analyze:**
- Leadership approach and impact
- Team management and development
- Project planning and execution
- Stakeholder engagement
- Results and outcomes

**Provide coaching feedback with leadership frameworks.**"""
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
    # Add more mappings as needed
}


class AdvancedAIService:
    def __init__(self):
        self.client = client
        self.feedback_history = []

    def get_template_type(self, section_code: str) -> str:
        """Get the appropriate template type for a competency"""
        return ERB_COMPETENCY_MAPPING.get(section_code, "problem_solving")

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
                model="gpt-4",  # Use more advanced model for better feedback
                messages=[
                    {"role": "system", "content": template["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent feedback
                max_tokens=2000,
                timeout=45,
            )

            feedback = self._safe_content(response)
            self._store_feedback_history(section_code, feedback)
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
        """Get comprehensive feedback on the entire report"""
        compiled_report = self._compile_full_report(responses, competency_data)

        prompt = f"""
        You are an ERB assessment expert providing comprehensive feedback on a full engineering report.

        **Professional Level:** {profession}
        **Report Structure:** Organized by ERB competency framework
        **Total Competencies Completed:** {len(responses)}

        **FULL REPORT CONTENT:**
        {compiled_report}

        **Provide comprehensive feedback covering:**

        1. **OVERALL ASSESSMENT**
           - Overall strength and completeness
           - Alignment with {profession} level expectations
           - Professional communication quality

        2. **TECHNICAL DEPTH ANALYSIS**
           - Engineering methodology demonstrated
           - Technical accuracy and detail
           - Problem-solving approach

        3. **COMPETENCY COVERAGE**
           - Key strengths across competencies
           - Gaps or underdeveloped areas
           - Balance between technical and professional competencies

        4. **ERB ALIGNMENT**
           - Evidence meeting competency indicators
           - Professional engineering standards
           - Readiness for ERB submission

        5. **ACTIONABLE RECOMMENDATIONS**
           - Priority improvements
           - Specific competency enhancements
           - Final polishing suggestions

        Format your response with clear sections and bullet points for readability.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": "You are an experienced ERB assessor providing detailed, constructive feedback on engineering competency reports."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=3000,
                timeout=60,
            )

            feedback = self._safe_content(response)
            self._store_feedback_history("full_report", feedback)
            return feedback

        except Exception as e:
            return f"⚠️ Error generating comprehensive feedback: {str(e)}"

    def generate_competency_template(self, section_code: str, section_data: dict, profession: str,
                                     style: str = "Professional", include_examples: bool = True) -> str:
        """Generate a template response for a competency with customization options"""
        prompt = f"""
        Generate a {style.lower()} template response for an ERB competency submission.

        **Competency:** {section_code} - {section_data['title']}
        **Professional Level:** {profession}
        **Style Preference:** {style}
        **Include Examples:** {include_examples}
        **Instructions:** {section_data['instructions']}
        **Key Indicators:** {', '.join(section_data.get('indicators', []))}
        **Target Word Count:** {section_data.get('word_limit', 500)}

        Create a template that:
        1. Demonstrates engineering best practices in {style.lower()} style
        2. Addresses all competency indicators
        3. Uses professional engineering language appropriate for {profession}
        4. Includes {'detailed examples and ' if include_examples else ''}placeholders for specific projects/experiences
        5. Shows appropriate technical depth for {profession} level
        6. Is structured for easy customization

        Format as a ready-to-customize template with [BRACKETED_PLACEHOLDERS] for user-specific details.
        Provide clear section headings and practical guidance.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": f"You are an engineering expert creating high-quality ERB competency templates in {style.lower()} style."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            template = self._safe_content(response)
            self._store_feedback_history(section_code, f"Generated {style} template")
            return template

        except Exception as e:
            return f"⚠️ Error generating template: {str(e)}"

    def analyze_competency_gaps(self, responses: dict, competency_data: dict, profession: str) -> str:
        """Enhanced gap analysis with role-specific insights"""
        completed_competencies = [k for k, v in responses.items() if v.get('response', '').strip()]
        all_competencies = list(competency_data.keys())
        missing_competencies = [c for c in all_competencies if c not in completed_competencies]

        completion_rate = (len(completed_competencies) / len(all_competencies) * 100) if all_competencies else 0

        prompt = f"""
        Analyze competency completion gaps and provide strategic recommendations for a {profession} ERB submission.

        **Completion Status:** {len(completed_competencies)}/{len(all_competencies)} ({completion_rate:.1f}%)
        **Missing Competencies:** {missing_competencies}

        **Completed Competencies:**
        {chr(10).join(f"- {comp}: {competency_data[comp]['title']}" for comp in completed_competencies)}

        **Missing Competencies:**
        {chr(10).join(f"- {comp}: {competency_data[comp]['title']}" for comp in missing_competencies)}

        **Provide strategic gap analysis focusing on:**
        1. **Critical Priority Competencies** - Which missing competencies are most important for {profession} role?
        2. **Quick Wins** - Which competencies can be completed most efficiently?
        3. **Interdependencies** - How do completed and missing competencies relate?
        4. **Role-Specific Strategy** - Optimal completion order for {profession}
        5. **Risk Assessment** - Impact of current gaps on ERB submission success

        **Format your response with clear, actionable sections:**
        - Critical Missing Competencies
        - Recommended Completion Order  
        - Quick Wins & Low-Hanging Fruit
        - Strategic Recommendations for {profession}
        - Estimated Timeline & Effort

        Focus on practical, role-specific advice that helps prioritize effectively.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": f"You are an ERB submission strategist specializing in {profession} role requirements. Provide targeted, actionable gap analysis."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            analysis = self._safe_content(response)
            self._store_feedback_history("gap_analysis",
                                         f"Gap analysis for {profession} - {len(completed_competencies)}/{len(all_competencies)} completed")
            return analysis

        except Exception as e:
            return f"⚠️ Error analyzing gaps: {str(e)}"

    def improve_response_quality(self, text: str, section_code: str, section_data: dict, profession: str) -> str:
        """Provide specific improvements for a response with enhanced formatting"""
        prompt = f"""
        Improve this engineering competency response for ERB submission:

        **Competency:** {section_code} - {section_data['title']}
        **Professional Level:** {profession}
        **Current Response:** {text}

        **Provide an improved version with these enhancements:**
        1. **Technical Depth** - Add specific engineering details, calculations, methodologies
        2. **Evidence Strength** - Strengthen examples and measurable outcomes
        3. **Professional Language** - Use appropriate engineering terminology for {profession}
        4. **Structure & Clarity** - Improve organization and readability
        5. **Competency Alignment** - Better address indicators: {', '.join(section_data.get('indicators', []))}

        **Format your response as:**

        **Improvement Analysis:**
        [Brief explanation of key improvements made and why they matter for ERB assessment]

        **Improved Response:**
        [The complete enhanced response ready for use]

        Maintain the original experiences and intent while significantly elevating professional quality.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": "You are an engineering editor specializing in ERB submissions. Enhance responses while preserving authenticity and adding professional rigor."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=2000,
            )

            improved = self._safe_content(response)
            self._store_feedback_history(section_code, "Response quality improvement applied")
            return improved

        except Exception as e:
            return f"⚠️ Error improving response: {str(e)}"
    def _compile_full_report(self, responses: dict, competency_data: dict) -> str:
        """Compile full report for analysis"""
        report_parts = []
        for key, response_data in responses.items():
            if key in competency_data:
                competency = competency_data[key]
                report_parts.append(f"""
                COMPETENCY {key}: {competency['title']}
                Indicators: {', '.join(competency.get('indicators', []))}
                Response: {response_data.get('response', 'No response')}
                {'=' * 50}
                """)

        return "\n".join(report_parts)

    def _store_feedback_history(self, section: str, feedback: str):
        """Store feedback in history"""
        self.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'section': section,
            'feedback': feedback[:500] + "..." if len(feedback) > 500 else feedback  # Store preview
        })

        # Keep only last 10 entries
        if len(self.feedback_history) > 10:
            self.feedback_history.pop(0)

    def get_feedback_history(self) -> List[Dict]:
        """Get feedback history"""
        return self.feedback_history

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
    return ai_service.get_enhanced_feedback(text, section_code, section_data, profession)


def get_full_report_feedback(responses, competency_data, profession):
    """Legacy function for backward compatibility"""
    return ai_service.get_comprehensive_report_feedback(responses, competency_data, profession)