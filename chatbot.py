import os
import groq
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq retires / re-tiers models from time to time (llama-3.1-8b-instant is now
# Enterprise-only). Keep the model name configurable: set GROQ_MODEL in .env or
# Streamlit secrets to override. Current free-tier production models:
#   openai/gpt-oss-20b   - fastest / cheapest (default)
#   openai/gpt-oss-120b  - stronger answers
# See https://console.groq.com/docs/models for the live list.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
You are MedAssist AI, a professional healthcare assistant.

Responsibilities:
- Explain symptoms and diseases in simple language.
- Provide preventive healthcare advice.
- Explain medical terms, reports, and lab values.
- Suggest healthy lifestyle practices.

Limitations:
- Never provide a definitive diagnosis.
- Never prescribe medication dosage.
- Never replace a licensed healthcare professional.

If symptoms appear serious or life-threatening, advise immediate medical attention.

Always provide educational information only.
"""


def get_medical_response(user_query):
    """
    Sends user query to Groq and returns response.
    """

    if client is None:
        return "⚠️ GROQ_API_KEY is not set. Add it to a local .env file or to Streamlit secrets and restart the app."

    try:

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.3,
            max_completion_tokens=1024
        )

        return completion.choices[0].message.content or "I couldn't generate a response. Please try again."

    except groq.NotFoundError:
        return (f"⚠️ The model `{GROQ_MODEL}` is not available on this Groq account. "
                "Set GROQ_MODEL to a model listed at console.groq.com/docs/models "
                "(e.g. openai/gpt-oss-20b) and restart the app.")
    except groq.AuthenticationError:
        return "⚠️ The Groq API key was rejected. Check GROQ_API_KEY in .env or Streamlit secrets."
    except groq.RateLimitError:
        return "⚠️ Groq's rate limit was reached. Please wait a moment and try again."
    except groq.APIConnectionError:
        return "⚠️ Could not reach the Groq API. Check your internet connection."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
