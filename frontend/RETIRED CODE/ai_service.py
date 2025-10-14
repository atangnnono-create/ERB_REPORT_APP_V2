from openai import OpenAI,APIConnectionError, APIError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
import os
import streamlit as st

# ---------------------- Secure API Key ---------------------- #
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ Missing OpenAI API key. Please set OPENAI_API_KEY environment variable. For technicall assistance send email to fluidair2010@gmail.com ")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------------- AI Functions ---------------------- #
def _safe_content(response) -> str:
    """
    Safely extract text content from an OpenAI response object.
    Returns a clean string or a fallback message if extraction fails.
    """
    try:
        # Check if response has choices
        if hasattr(response, "choices") and response.choices:
            first_choice = response.choices[0]

            # Make sure message and content exist
            if hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                return str(first_choice.message.content).strip()

        # If nothing valid is found
        return "⚠️ No valid content found in the response."
    except (IndexError, AttributeError, KeyError, TypeError) as e:
        # Catch only predictable structural errors
        return f"⚠️ Error extracting content: {e}"


def get_gpt_feedback(text, section_code, section_data, profession):
    prompt = f"""
You are a precise AI coach helping an {profession} prepare a professional registration report for the Engineer Registration Board (ERB) of Botswana.

This response is for section **{section_code} – {section_data['title']}**.

### ERB Requirements:
- {section_data['instructions']}
- Focus on these indicators: {', '.join(section_data.get('indicators', []))}

Now, do the following:
1. Assess if the response meets the ERB expectations for a {profession}.
2. Suggest improvements for objectivity, clarity, and professionalism.
3. Make sure the tone is factual, technical, and engineering-oriented.
4. Highlight if it is missing any of the core indicators.

###{profession}'s Draft Response:
{text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a precise ERB report coach. Be specific, actionable, and aligned with the role."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2500,
            timeout=30,
            top_p=1.0,
        )
        return _safe_content(response)

    except APIConnectionError:
        return "Connection error – please try again later."

    except RateLimitError:
        return "Rate limit error – Please wait a bit before trying again."

    except Exception as e:
        return f"Unexpected error – {str(e)}"


def get_full_report_feedback(responses: dict, compt:dict,profession:str):
    """Send the entire saved report to GPT for overall review."""
    compiled_text = ""
    for key in compt.keys():
        if key in responses:
            entry = responses[key]
            compiled_text += f"### {key}: {entry['title']}\n{entry['response']}\n\n"

    prompt = f"""
You are a precise AI coach helping an {profession} prepare a professional report for the Engineer Registration Board (ERB) of Botswana.

Below is the {profession}'s full report across several competency sections.  
For each section:
1. Give constructive feedback specific to ERB expectations.
2. Suggest improvements for clarity, technical detail, and alignment with indicators.
3. Point out any missing or weakly covered indicators.

Finally, provide an **overall summary** highlighting strengths and main improvement areas.

### {profession}'s draft report:
{compiled_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a precise ERB report coach. Be specific, actionable, and aligned with the role."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2500,
            timeout=30,
            top_p=1.0,
        )
        return _safe_content(response)

    except APIConnectionError:
        return "Connection error – please try again later."

    except RateLimitError:
        return "Rate limit error – Please wait a bit before trying again."

    except Exception as e:
        return f"Unexpected error – {str(e)}"
