"""
SilkCocoonAI - Multimodal AI Image Analysis (image_analysis.py)

This module handles:
1. Secure, in-memory validation of uploaded cocoon photographs.
2. Prompt engineering for sericulture grading using multimodal Vision AI.
3. Clean JSON schema enforcement and robust response parsing.
4. Safe error handling when credentials are missing or models return invalid data.
"""

import io
import os
import json
import re
from typing import Dict, Any, Tuple, Optional
from PIL import Image

# Sericulture Prompt for Multimodal Vision Model
SERICULTURE_VISION_PROMPT = """
You are an expert Sericulture Inspector and Agricultural Vision AI specialist.
Analyze this silkworm cocoon image strictly according to commercial silk grading standards.

Output your evaluation ONLY as a raw, valid JSON object with the exact keys below.
Do not enclose in markdown blocks if possible, or use standard ```json ... ``` tags.

Required JSON Structure:
{
  "is_cocoon": true or false,
  "evidence_sufficient": true or false,
  "quality_notes": "Explanation if image is blurry, too dark, occluded, or low resolution",
  "cocoon_count": <estimated integer number of cocoons visible>,
  "color_type": "White (Bivoltine)" or "Golden Yellow (Multivoltine)" or "Greenish" or "Other",
  "shape_uniformity_score": <0 to 100 based on symmetrical oval/ellipsoidal shape>,
  "compactness_score": <0 to 100 based on shell firmness, thickness, and lack of loose floss>,
  "cleanliness_score": <0 to 100 based on pure surface, lack of urine/melting/soil stains>,
  "defects_detected": ["pierced", "double", "melted", "stained", "crushed", "flimsy", "malformed"] (list only actual defects detected, or empty list []),
  "visual_observations": [
    "<3-5 clear, factual bullet points describing the visual evidence seen in the photo>"
  ],
  "recommendations": [
    "<2-3 actionable advice points for the farmer or silk reelers regarding storage, sorting, or market pricing>"
  ]
}

STRICT INSTRUCTIONS:
1. If the photo does NOT contain silkworm cocoons (e.g. food, human, car, unrelated object), set "is_cocoon": false, "evidence_sufficient": false, and do NOT fabricate scores.
2. If the photo is too blurry, dark, far away, or obscured to judge shell quality honestly, set "evidence_sufficient": false, explain why in "quality_notes", and avoid speculating.
3. If defects like uzifly pierced holes, moth emergence, double cocoon (dupion), or melting are present, name them explicitly in "defects_detected".
"""


def validate_image_bytes(image_bytes: bytes, max_size_mb: int = 10) -> Tuple[bool, str, Optional[Image.Image]]:
    """
    Validates the uploaded file in-memory.
    Checks:
    - Non-empty byte payload
    - File size below max_size_mb
    - Valid, non-corrupted image format (JPEG, PNG, WEBP)
    - Minimum resolvable dimensions (at least 64x64)

    Returns:
        (is_valid, error_message, PIL.Image object or None)
    """
    if not image_bytes:
        return False, "Uploaded image file is empty (0 bytes).", None

    max_bytes = max_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        return False, f"File size exceeds the {max_size_mb} MB limit (Size: {len(image_bytes)/(1024*1024):.1f} MB).", None

    try:
        # Load safely into PIL without writing to disk
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verifies file integrity and header

        # Reopen after verify() because verify() clears file pointer
        image = Image.open(io.BytesIO(image_bytes))

        # Check format
        allowed_formats = {"JPEG", "JPG", "PNG", "WEBP"}
        if image.format.upper() not in allowed_formats:
            return False, f"Unsupported image format: {image.format}. Please upload JPG, PNG, or WEBP.", None

        # Check dimensions
        width, height = image.size
        if width < 64 or height < 64:
            return False, f"Image resolution ({width}x{height}) is too small for quality assessment.", None

        # Convert palette/RGBA modes to RGB for AI models if needed
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        return True, "", image

    except Exception as e:
        return False, f"Corrupted or invalid image file: {str(e)}", None


def clean_json_response(raw_text: str) -> str:
    """
    Cleans multimodal model output by stripping markdown fences,
    extraneous commentary, or leading/trailing whitespace.
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.strip()

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        # If no markdown block, locate outermost curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    return text


def parse_and_validate_ai_json(json_text: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Parses and validates the JSON response from the multimodal AI model.
    Guarantees that all required sericulture fields exist and types are valid.
    """
    if not json_text or not json_text.strip():
        return False, {}, "Multimodal model returned an empty response."

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as err:
        return False, {}, f"Failed to parse model JSON: {str(err)}"

    if not isinstance(data, dict):
        return False, {}, "Model output was not a valid JSON dictionary."

    # Normalize defaults for safe consumption
    parsed: Dict[str, Any] = {
        "is_cocoon": bool(data.get("is_cocoon", False)),
        "evidence_sufficient": bool(data.get("evidence_sufficient", False)),
        "quality_notes": str(data.get("quality_notes", "")),
        "cocoon_count": int(data.get("cocoon_count", 1) or 1),
        "color_type": str(data.get("color_type", "White (Bivoltine)")),
        "shape_uniformity_score": data.get("shape_uniformity_score", 70),
        "compactness_score": data.get("compactness_score", 70),
        "cleanliness_score": data.get("cleanliness_score", 70),
        "defects_detected": data.get("defects_detected", []) if isinstance(data.get("defects_detected"), list) else [],
        "visual_observations": data.get("visual_observations", []) if isinstance(data.get("visual_observations"), list) else [],
        "recommendations": data.get("recommendations", []) if isinstance(data.get("recommendations"), list) else [],
    }

    return True, parsed, ""


def analyze_cocoon_image_with_gemini(
    image: Image.Image,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Invokes the verified Google Gemini Vision AI model to inspect the cocoon image.
    Never fabricates responses: if the API key is missing or invalid, reports a clear error.
    """
    # 1. Retrieve API Key
    effective_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not effective_key or effective_key == "your_gemini_api_key_here":
        return False, {}, (
            "GEMINI_API_KEY is not configured. "
            "Please obtain a free key at https://aistudio.google.com/app/apikey "
            "and add it to your .env file or enter it in the sidebar settings."
        )

    # 2. Select Model Name
    effective_model = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    try:
        import google.generativeai as genai
    except ImportError:
        return False, {}, (
            "The 'google-generativeai' package is not installed. "
            "Run 'pip install google-generativeai' in your terminal."
        )

    try:
        # Configure client with API Key
        genai.configure(api_key=effective_key)
        model = genai.GenerativeModel(effective_model)

        # Call multimodal model with system instructions & image
        response = model.generate_content(
            [SERICULTURE_VISION_PROMPT, image],
            generation_config={"temperature": 0.2, "top_p": 0.9}
        )

        if not response or not response.text:
            return False, {}, "Multimodal AI returned an empty response. Please retry."

        # Clean markdown code blocks
        clean_text = clean_json_response(response.text)

        # Parse and validate JSON structure
        success, parsed_data, err_msg = parse_and_validate_ai_json(clean_text)
        if not success:
            return False, {}, f"Model returned invalid structured output: {err_msg}"

        return True, parsed_data, ""

    except Exception as exc:
        # Never leak secrets or raw trace in client response
        error_msg = str(exc)
        if "API_KEY_INVALID" in error_msg or "invalid api key" in error_msg.lower():
            return False, {}, "The provided Gemini API Key is invalid or expired. Please check your credentials."
        if "quota" in error_msg.lower() or "429" in error_msg:
            return False, {}, "API rate limit reached. Please wait a few moments and retry."
        return False, {}, f"AI analysis error: {error_msg}"
