"""
SilkCocoon AI - REST API Server & WSGI Application (api_server.py)
Valid WSGI entry point for Vercel Serverless deployment and local execution.
"""

import os
import io
import json
import base64
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

from image_analysis import validate_image_bytes, analyze_cocoon_image_with_gemini
from scoring import calculate_cocoon_grade, DEFECT_PENALTY_WEIGHTS
from gemini_service import get_gemini_advisory, test_gemini_connection, get_gemini_client

# Load environment variables
load_dotenv()

# Initialize Flask WSGI Application
app = Flask(__name__)
handler = app
CORS(app, resources={r"/*": {"origins": "*"}})

HTML_LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SilkCocoon AI - API & Inspection Service</title>
  <style>
    :root {
      --brand-green: #123C32;
      --brand-gold: #C8A951;
      --brand-pearl: #F8F5EC;
      --brand-charcoal: #1F2925;
    }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--brand-pearl);
      color: var(--brand-charcoal);
      line-height: 1.6;
      padding: 40px 20px;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 16px;
      padding: 36px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.06);
      border: 1px solid #e2e8f0;
    }
    .header {
      border-bottom: 2px solid #f1f5f9;
      padding-bottom: 20px;
      margin-bottom: 24px;
    }
    h1 {
      color: var(--brand-green);
      margin: 0 0 6px 0;
      font-size: 28px;
    }
    .tagline {
      color: #64748b;
      margin: 0;
      font-size: 15px;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      background: #d8f3dc;
      color: #123C32;
      border: 1px solid #74c69d;
      margin-top: 10px;
    }
    .endpoint-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 12px;
    }
    .method {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 800;
      font-family: monospace;
      margin-right: 8px;
    }
    .get { background: #e0f2fe; color: #0369a1; }
    .post { background: #dcfce7; color: #15803d; }
    code {
      font-family: monospace;
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>SilkCocoon AI 🐛</h1>
      <p class="tagline">Automated Sericulture Quality Inspection & Transparent Market Grading</p>
      <div class="badge">✓ WSGI API Service Active on Vercel</div>
    </div>

    <h3>Available Endpoints:</h3>

    <div class="endpoint-card">
      <span class="method get">GET</span> <code>/api/health</code>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">Checks system health and Gemini API connection status.</p>
    </div>

    <div class="endpoint-card">
      <span class="method post">POST</span> <code>/api/advisory</code>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">Generates official Google Gemini sericulture advisory for cocoon growers.</p>
    </div>

    <div class="endpoint-card">
      <span class="method post">POST</span> <code>/api/chat</code>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">Conversational assistant for sericulture farmers.</p>
    </div>

    <div class="endpoint-card">
      <span class="method post">POST</span> <code>/api/analyze</code>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">Upload cocoon photograph (multipart or JSON base64) for optical CSTRI quality grading.</p>
    </div>

    <div class="endpoint-card">
      <span class="method get">GET</span> <code>/api/standards</code>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b;">Returns CSTRI sericulture defect penalty weights and benchmark thresholds.</p>
    </div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
@app.route("/api/", methods=["GET"])
@app.route("/api/index", methods=["GET"])
@app.route("/api/index.py", methods=["GET"])
def index():
    """Serves the root dashboard / landing overview."""
    return render_template_string(HTML_LANDING_PAGE)


@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Checks backend server health and Gemini configuration status."""
    has_key = bool(get_gemini_client())
    return jsonify({
        "status": "online",
        "service": "SilkCocoon AI Backend",
        "deployment": "Vercel Serverless WSGI",
        "gemini_connected": has_key,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    })


@app.route("/api/advisory", methods=["POST"])
@app.route("/advisory", methods=["POST"])
def advisory_endpoint():
    """
    Main Gemini Advisory Endpoint.
    Payload:
      {
        "topic": "Cocoon Transport" (optional),
        "variety": "Cross-Breed (CB)" (optional),
        "question": "How to transport cocoons in summer?" (optional)
      }
    """
    data = request.get_json(silent=True) or {}
    topic = data.get("topic", "General Sericulture Advisory")
    variety = data.get("variety", "Cross-Breed (CB)")
    question = data.get("question", None)

    result = get_gemini_advisory(topic=topic, variety=variety, question=question)
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Farmer conversational assistant endpoint."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"success": False, "reply": "Please provide a question."}), 400

    result = get_gemini_advisory(
        topic="Farmer Direct Query",
        variety="General Sericulture",
        question=message
    )

    reply_text = result.get("advisory", {}).get("content", "Unable to generate reply.")
    return jsonify({
        "success": result.get("success", False),
        "reply": reply_text,
        "source": result.get("source", "Gemini AI"),
        "is_configured": result.get("is_configured", False)
    })


@app.route("/api/analyze", methods=["POST"])
@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    """
    Analyzes an uploaded cocoon image and returns grading and defect metrics.
    Accepts:
    1. Multipart form file: 'image'
    2. JSON payload: { 'image_base64': '...' }
    """
    image_bytes = None

    if "image" in request.files:
        image_bytes = request.files["image"].read()
    else:
        json_data = request.get_json(silent=True) or {}
        b64 = json_data.get("image_base64", "")
        if b64:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(b64)
            except Exception:
                return jsonify({"status": "ERROR", "message": "Invalid base64 image data"}), 400

    if not image_bytes:
        return jsonify({"status": "ERROR", "message": "No image file or image_base64 provided"}), 400

    # 1. Validate image
    is_valid, err_msg, pil_image = validate_image_bytes(image_bytes)
    if not is_valid:
        return jsonify({"status": "INVALID_IMAGE", "message": err_msg}), 400

    # 2. Invoke Gemini Vision Analysis
    ai_success, parsed_ai, ai_err = analyze_cocoon_image_with_gemini(pil_image)
    if not ai_success:
        return jsonify({"status": "AI_ERROR", "message": ai_err}), 500

    # 3. Calculate CSTRI Grade
    result = calculate_cocoon_grade(parsed_ai)
    return jsonify(result.to_dict())


@app.route("/api/standards", methods=["GET"])
@app.route("/standards", methods=["GET"])
def standards_endpoint():
    """Returns sericulture defect penalty weights and guidelines."""
    return jsonify({
        "defect_penalties": DEFECT_PENALTY_WEIGHTS,
        "grade_thresholds": {
            "Grade A": "85.0 - 100.0",
            "Grade B": "70.0 - 84.9",
            "Grade C": "55.0 - 69.9",
            "Reject": "Below 55.0 or fatal pierced/melted defect"
        }
    })


@app.route("/api/test-gemini", methods=["GET"])
@app.route("/test-gemini", methods=["GET"])
def test_gemini_endpoint():
    """Verifies live Gemini API status."""
    res = test_gemini_connection()
    return jsonify(res)


@app.errorhandler(404)
def handle_404(e):
    """Fallback handler so any unmatched GET route returns the landing page."""
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Endpoint not found",
            "requested_path": request.path,
            "available_endpoints": [
                "/api/health",
                "/api/advisory",
                "/api/chat",
                "/api/analyze",
                "/api/standards"
            ]
        }), 404
    return render_template_string(HTML_LANDING_PAGE), 200


# Vercel Serverless requires WSGI handler exposed as 'app'
# When run locally: python api_server.py
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 SilkCocoon AI API running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
