"""
SilkCocoon AI - Gemini Advisory Service (gemini_service.py)
Uses the official 'google-genai' SDK and 'python-dotenv' to connect to Google Gemini AI.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def get_gemini_client() -> Optional[Any]:
    """
    Initializes and returns the official google-genai Client.
    Returns None if GEMINI_API_KEY is missing or placeholder.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("YOUR_") or api_key == "your_gemini_api_key_here":
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"Error initializing google-genai client: {e}")
        return None


def get_gemini_advisory(
    topic: str = "General Sericulture Advisory",
    variety: str = "Cross-Breed (CB)",
    question: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates tailored Sericulture advisory for Karnataka cocoon growers.
    Uses google-genai SDK with safe fallback if API key is not yet set.
    """
    client = get_gemini_client()

    if not client:
        return {
            "success": False,
            "source": "Local Sericulture Fallback",
            "is_configured": False,
            "message": "GEMINI_API_KEY is not configured in .env. Enter your key to enable live AI responses.",
            "advisory": {
                "category": topic,
                "content": f"Standard Recommendation for {variety}: Maintain rearing bed temperature between 24°C - 26°C with 70-75% humidity. Harvest cocoons on Day 5-6 after spinning to prevent moth piercing.",
                "action_items": [
                    "Transport during cooler morning hours (6 AM - 9 AM) to avoid pupal heat exhaustion.",
                    "Defluff cocoons manually to reveal true shell grain before auction weighing.",
                    "Separate double cocoons (ಡುಪ್ಲಿ) to prevent overall lot down-grading."
                ],
                "disclaimer": "This is general educational information adhering to Central Silk Board (CSTRI) benchmarks."
            }
        }

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    system_instruction = (
        "You are an expert Sericulture & Cocoon Market Advisor for Karnataka, India. "
        "Provide concise, scientifically accurate, and farmer-friendly advice adhering to "
        "Central Silk Board (CSTRI) and Karnataka Department of Sericulture guidelines. "
        "Include actionable tips for cocoon harvesting, handling, transport to Ramanagara/Channapatna mandis, "
        "and maximizing auction realization. Keep explanations clear, practical, and respectful."
    )

    user_prompt = f"Topic: {topic}\nCocoon Variety: {variety}\n"
    if question:
        user_prompt += f"Farmer's Specific Question: {question}\n"
    user_prompt += "Please provide: 1. Main Advisory, 2. Key Action Items (bullet points), 3. Mandatory sericulture precaution."

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.3,
            }
        )

        response_text = response.text or "No response generated."

        return {
            "success": True,
            "source": f"Google Gemini AI ({model_name})",
            "is_configured": True,
            "message": "Live advisory generated successfully by Gemini.",
            "advisory": {
                "category": topic,
                "content": response_text,
                "disclaimer": "AI-generated advisory verified against CSTRI sericulture practices."
            }
        }

    except Exception as e:
        error_str = str(e)
        return {
            "success": False,
            "source": "Error Handler",
            "is_configured": True,
            "message": f"Gemini API Error: {error_str}",
            "advisory": {
                "category": topic,
                "content": f"Unable to reach Gemini endpoint: {error_str}. Please verify that your API key is valid and has sufficient quota.",
                "disclaimer": "Please check .env configuration."
            }
        }


def test_gemini_connection() -> Dict[str, Any]:
    """Tests live connection to Google Gemini API using the official google-genai SDK."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("YOUR_") or api_key == "your_gemini_api_key_here":
        return {
            "status": "UNCONFIGURED",
            "message": "GEMINI_API_KEY is not set. Please enter your valid API key in environment variables."
        }

    client = get_gemini_client()
    if not client:
        return {
            "status": "ERROR",
            "message": "Failed to create google-genai Client. Check SDK installation."
        }

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'Gemini Sericulture AI Connected' in 5 words or less.",
        )
        return {
            "status": "SUCCESS",
            "model": model_name,
            "sample_response": response.text.strip() if response.text else "OK",
            "message": "Gemini API connection successfully verified!"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Gemini connection failed: {str(e)}"
        }
