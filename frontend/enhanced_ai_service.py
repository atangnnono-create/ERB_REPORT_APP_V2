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
    },

    "continuous_quality_improvement": {
        "system_prompt": """You are an expert in quality management systems and continuous improvement methodologies for engineering professionals.
        You specialize in evaluating ERB submissions related to quality standards, process improvement, and organizational excellence.

        Focus on:
        - Quality management system implementation (ISO 9000, EFQM, etc.)
        - Continuous improvement methodologies and frameworks
        - Supplier and customer quality networks
        - Lessons learned processes and knowledge sharing
        - Professional standards adherence and promotion""",

        "feedback_template": """Analyze this quality and continuous improvement competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Quality management system knowledge and application
2. Continuous improvement methodology implementation
3. Supplier/customer network quality integration
4. Lessons learned processes and organizational learning
5. Professional standards adherence and promotion

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "effective_communication": {
        "system_prompt": """You are an expert in engineering communication and professional documentation.
        You specialize in evaluating ERB submissions related to technical communication, documentation standards, and professional collaboration.

        Focus on:
        - Technical documentation quality (reports, drawings, specifications)
        - Meeting leadership and participation skills
        - Audience-appropriate communication strategies
        - Professional network engagement and knowledge sharing
        - Clarity and effectiveness in complex technical communication""",

        "feedback_template": """Analyze this communication and documentation competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Technical documentation quality and clarity
2. Meeting leadership and participation effectiveness
3. Communication adaptability for different audiences
4. Professional network engagement
5. Complex information distillation and presentation

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "proposals_and_justifications": {
        "system_prompt": """You are an expert in engineering proposals, strategic communication, and technical justification.
        You specialize in evaluating ERB submissions related to proposal development, strategic presentations, and technical persuasion.

        Focus on:
        - Proposal and bid preparation quality
        - Technical justification and rationale development
        - Strategic presentation delivery and adaptation
        - Academic and professional publication contributions
        - Collective goal alignment and leadership""",

        "feedback_template": """Analyze this proposals and justifications competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Proposal clarity and persuasiveness
2. Technical justification strength and rationale
3. Strategic presentation effectiveness
4. Academic/professional publication contributions
5. Collective goal leadership and alignment

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "diversity_and_inclusion": {
        "system_prompt": """You are an expert in workplace diversity, inclusion practices, and emotional intelligence for engineering professionals.
        You specialize in evaluating ERB submissions related to interpersonal skills, team dynamics, and inclusive workplace environments.

        Focus on:
        - Emotional intelligence and self-awareness development
        - Diversity and inclusion principles implementation
        - Conflict resolution and relationship management
        - Team collaboration and collective goal achievement
        - Interpersonal adaptability and social awareness""",

        "feedback_template": """Analyze this diversity and inclusion competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Emotional intelligence and self-awareness demonstration
2. Diversity and inclusion principles application
3. Conflict resolution and relationship management
4. Team collaboration and collective goal achievement
5. Interpersonal adaptability and social support

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "codes_of_conduct": {
        "system_prompt": """You are an expert in engineering ethics, professional codes of conduct, and regulatory compliance.
        You specialize in evaluating ERB submissions related to professional ethics, legal frameworks, and regulatory adherence.

        Focus on:
        - Code of Conduct and Professional Ethics compliance
        - Legislative and regulatory framework understanding
        - Role-specific ethical considerations and applications
        - Social and employment legislation integration
        - Ethical leadership and compliance demonstration""",

        "feedback_template": """Analyze this codes of conduct and ethics competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Code of Conduct compliance and understanding
2. Legislative and regulatory framework awareness
3. Role-specific ethical application
4. Social and employment legislation integration
5. Ethical leadership and compliance demonstration

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "occupational_safety_improvement": {
        "system_prompt": """You are an expert in occupational health and safety systems, risk management, and safety culture development for engineering professionals.
        You specialize in evaluating ERB submissions related to workplace safety, hazard management, and regulatory compliance.

        Focus on:
        - Health and safety system development and implementation
        - Hazard identification and risk management methodologies
        - Safety legislation compliance (ISO 45001, Health and Safety laws)
        - Safety culture development and leadership
        - Continuous safety system improvement and evaluation""",

        "feedback_template": """Analyze this occupational safety and improvement competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Health and safety system implementation quality
2. Hazard identification and risk management effectiveness
3. Safety legislation knowledge and application
4. Safety culture development and leadership
5. Continuous safety improvement processes

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "sustainable_development_principles": {
        "system_prompt": """You are an expert in sustainable development principles and environmental engineering practices.
        You specialize in evaluating ERB submissions related to sustainability, environmental impact, and resource efficiency in engineering projects.

        Focus on:
        - Triple bottom line integration (environmental, social, economic outcomes)
        - Sustainable product and service development
        - Resource efficiency and environmental impact minimization
        - Stakeholder engagement in sustainability initiatives
        - Practical application of sustainability principles in daily work""",

        "feedback_template": """Analyze this sustainable development competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Sustainable development principles application
2. Environmental, social, and economic balance
3. Resource efficiency and environmental impact reduction
4. Stakeholder engagement in sustainability
5. Practical sustainability implementation in daily work

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "ethical_issues": {
        "system_prompt": """You are an expert in engineering ethics, moral reasoning, and professional ethical decision-making.
        You specialize in evaluating ERB submissions related to ethical dilemmas, moral principles, and professional conduct standards.

        Focus on:
        - Ethical dilemma recognition and resolution
        - Code of Conduct and Professional Ethics application
        - Organizational ethical standards adherence
        - Moral reasoning and ethical decision-making processes
        - Professional integrity and ethical leadership""",

        "feedback_template": """Analyze this ethical issues competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Ethical issue recognition and understanding
2. Code of Conduct and Professional Ethics application
3. Organizational ethical standards implementation
4. Ethical decision-making and moral reasoning
5. Professional integrity and ethical leadership

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "continuing_professional_development": {
        "system_prompt": """You are an expert in Continuing Professional Development (CPD) planning, implementation, and evaluation for engineering professionals.
        You specialize in evaluating ERB submissions related to lifelong learning, competency development, and professional growth strategies.

        Focus on:
        - CPD needs assessment and planning
        - Professional development activity implementation
        - Competence evidence maintenance and documentation
        - CPD outcome evaluation and improvement
        - Mentoring and supporting others' professional development""",

        "feedback_template": """Analyze this continuing professional development competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. CPD needs assessment and planning quality
2. Development activity implementation and documentation
3. Competence evidence maintenance
4. CPD outcome evaluation and improvement
5. Support for others' professional development

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
    "initial_professional_development": {
        "system_prompt": """You are an expert in Initial Professional Development (IPD) planning and early-career engineering competency development.
        You specialize in evaluating ERB submissions related to graduate development, career transition planning, and foundational professional growth.

        Focus on:
        - Post-graduation skills and knowledge gap assessment
        - Structured IPD plan development and alignment with ERB requirements
        - Targeted professional development activity implementation
        - IPD evidence compilation and documentation
        - Development plan review and adjustment processes""",

        "feedback_template": """Analyze this initial professional development competency response for {profession}:

**Competency:** {section_code} - {title}
**Indicators:** {indicators}
**Word Limit:** {word_limit}

**User's Response:**
{text}

**Provide feedback on:**
1. Skills and knowledge gap assessment quality
2. IPD plan structure and ERB alignment
3. Development activity implementation
4. Evidence compilation and documentation
5. Plan review and adjustment processes

**Format your response as:**
- **Strengths:** [bullet points]
- **Improvement Areas:** [bullet points]
- **Specific Suggestions:** [actionable advice]
- **ERB Alignment Score:** X/10"""
    },
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
                model="gpt-4",
                messages=[
                    {"role": "system", "content": template["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
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
            self.update_usage_stats("feedback")
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
            self.update_usage_stats("template")
            return template

        except Exception as e:
            return f"⚠️ Error generating template: {str(e)}"

    def analyze_competency_gaps(self, responses, competency_data, profession):
        """Simple safe gap analysis"""
        try:
            # Convert inputs to safe types
            safe_responses = responses if hasattr(responses, 'items') else {}
            safe_competency_data = competency_data if hasattr(competency_data, 'items') else {}
            safe_profession = str(profession) if profession else "Engineering Professional"

            # Count completed competencies
            completed = []
            if hasattr(safe_responses, 'items'):
                for key, data in safe_responses.items():
                    try:
                        response_text = ""
                        if isinstance(data, dict) and 'response' in data:
                            response_text = str(data['response'])
                        elif isinstance(data, str):
                            response_text = data

                        if response_text.strip():
                            completed.append(key)
                    except:
                        continue

            all_competencies = list(safe_competency_data.keys()) if hasattr(safe_competency_data, 'keys') else []
            missing = [c for c in all_competencies if c not in completed]
            completion_rate = (len(completed) / len(all_competencies) * 100) if all_competencies else 0

            # Generate simple analysis
            return f"""
    **Gap Analysis for {safe_profession}**

    **Completion:** {len(completed)}/{len(all_competencies)} ({completion_rate:.1f}%)
    **Remaining:** {len(missing)} competencies

    **Recommendations:**
    - Focus on completing remaining competencies
    - Use templates for quick starts
    - Prioritize role-specific competencies
    """

        except Exception as e:
            return f"Basic gap analysis: Error processing data - {str(e)}"
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
            self.update_usage_stats("quality_improvement")
            return improved

        except Exception as e:
            return f"⚠️ Error improving response: {str(e)}"

    def _compile_full_report(self, responses: dict, competency_data: dict) -> str:
        """Compile full report for analysis with safe data access"""
        report_parts = []

        if not responses or not isinstance(responses, dict):
            return "No responses available."

        for key, response_data in responses.items():
            try:
                # Safely get competency data
                competency = None
                if key in competency_data:
                    competency = competency_data[key]

                # Safely extract response text
                response_text = ""
                if isinstance(response_data, dict):
                    response_text = response_data.get('response', 'No response')
                elif isinstance(response_data, str):
                    response_text = response_data
                else:
                    response_text = str(response_data)

                # Safely get competency title
                title = "Unknown Title"
                if isinstance(competency, dict):
                    title = competency.get('title', 'Unknown Title')
                elif competency:
                    title = str(competency)

                # Safely get indicators
                indicators = []
                if isinstance(competency, dict):
                    indicators = competency.get('indicators', [])

                report_parts.append(f"""
    COMPETENCY {key}: {title}
    Indicators: {', '.join(indicators) if indicators else 'No indicators'}
    Response: {response_text}
    {'=' * 50}
    """)
            except Exception as e:
                print(f"Warning: Could not compile report for competency {key}: {e}")
                continue

        return "\n".join(report_parts)
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