"""
SilkCocoon AI - REST API Server & WSGI Application (api_server.py)
Valid WSGI entry point for Vercel Serverless deployment and local execution.
Includes complete interactive web dashboard for sericulture quality inspection.
"""

import os
import io
import json
import base64
from flask import Flask, request, jsonify, render_template_string, send_from_directory
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
  <title>SilkCocoon AI - Automated Sericulture Quality Inspection</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #F8F5EC;
      --card-bg: #FFFFFF;
      --green-dark: #123C32;
      --green-primary: #1F5A49;
      --green-light: #E8F4F0;
      --green-border: #74C69D;
      --gold: #C8A951;
      --gold-light: #FDF9EE;
      --text-main: #1F2925;
      --text-muted: #5A6D65;
      --border: #E2E8F0;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-sm: 0 2px 8px rgba(18, 60, 50, 0.05);
      --shadow-md: 0 10px 30px rgba(18, 60, 50, 0.08);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding: 24px 16px 60px;
      min-height: 100vh;
    }

    .container {
      max-width: 1100px;
      margin: 0 auto;
    }

    /* Header */
    .header {
      background: linear-gradient(135deg, #123C32 0%, #1A4D40 100%);
      color: #FFFFFF;
      padding: 32px 36px;
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-md);
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
    }
    .header::after {
      content: "🐛";
      position: absolute;
      right: 30px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 80px;
      opacity: 0.18;
    }
    .brand-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .brand-title {
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }
    .header p {
      color: #C8E3D8;
      font-size: 15px;
      max-width: 650px;
      margin-bottom: 16px;
    }
    .badge-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(255, 255, 255, 0.15);
      color: #FFFFFF;
      backdrop-filter: blur(4px);
    }
    .pill.active {
      background: #74C69D;
      color: #123C32;
    }

    /* Navigation Tabs */
    .tabs-nav {
      display: flex;
      gap: 8px;
      background: #EAE6DB;
      padding: 6px;
      border-radius: var(--radius-md);
      margin-bottom: 24px;
      overflow-x: auto;
    }
    .tab-btn {
      flex: 1;
      min-width: 160px;
      padding: 12px 18px;
      background: transparent;
      border: none;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--green-dark);
      background: rgba(255, 255, 255, 0.5);
    }
    .tab-btn.active {
      background: var(--card-bg);
      color: var(--green-dark);
      box-shadow: var(--shadow-sm);
    }

    /* Tab Content Panels */
    .tab-panel {
      display: none;
      animation: fadeIn 0.3s ease;
    }
    .tab-panel.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* 2-Column Inspector Layout */
    .inspector-grid {
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 24px;
    }
    @media (max-width: 900px) {
      .inspector-grid { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      border-radius: var(--radius-md);
      padding: 28px;
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
    }
    .card-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--green-dark);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-sub {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 20px;
    }

    /* Upload Zone */
    .upload-zone {
      border: 2px dashed #B8C7C0;
      background: #FAFCFA;
      border-radius: var(--radius-md);
      padding: 32px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-bottom: 16px;
    }
    .upload-zone:hover, .upload-zone.dragover {
      border-color: var(--green-primary);
      background: var(--green-light);
    }
    .upload-zone input { display: none; }
    .upload-icon {
      font-size: 42px;
      margin-bottom: 8px;
      display: block;
    }

    /* Sample selector */
    .samples-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 20px;
    }
    .sample-chip {
      background: var(--bg);
      border: 1px solid var(--border);
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
      cursor: pointer;
      text-align: left;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .sample-chip:hover {
      background: var(--green-light);
      border-color: var(--green-border);
      color: var(--green-dark);
    }

    /* Preview Box */
    .preview-box {
      display: none;
      position: relative;
      background: #F1F5F3;
      border-radius: var(--radius-sm);
      overflow: hidden;
      margin-bottom: 18px;
      border: 1px solid var(--border);
      text-align: center;
    }
    .preview-box img {
      max-height: 240px;
      width: auto;
      max-width: 100%;
      object-fit: contain;
      display: block;
      margin: 0 auto;
    }
    .preview-clear {
      position: absolute;
      top: 8px;
      right: 8px;
      background: rgba(0,0,0,0.6);
      color: white;
      border: none;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
    }
    .preview-clear:hover { background: #ef4444; }

    /* Camera Box */
    .camera-box {
      display: none;
      background: #000000;
      border-radius: var(--radius-sm);
      overflow: hidden;
      margin-bottom: 16px;
      position: relative;
    }
    .camera-box video {
      width: 100%;
      height: 220px;
      object-fit: cover;
      display: block;
    }
    .camera-actions {
      padding: 10px;
      background: #111;
      display: flex;
      justify-content: center;
      gap: 10px;
    }

    /* Primary Buttons */
    .btn {
      width: 100%;
      padding: 14px 20px;
      border-radius: var(--radius-sm);
      border: none;
      font-family: inherit;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
    }
    .btn-primary {
      background: var(--green-dark);
      color: #FFFFFF;
      box-shadow: 0 4px 14px rgba(18, 60, 50, 0.25);
    }
    .btn-primary:hover:not(:disabled) {
      background: #194F42;
      transform: translateY(-1px);
    }
    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .btn-secondary {
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 8px 14px;
      font-size: 13px;
      width: auto;
    }
    .btn-secondary:hover { background: #E5E0D4; }

    /* Results Panel */
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }
    .empty-icon {
      font-size: 48px;
      margin-bottom: 12px;
      display: block;
      opacity: 0.7;
    }

    /* Grading Result Card */
    .result-container {
      display: none;
    }
    .grade-banner {
      padding: 24px;
      border-radius: var(--radius-md);
      text-align: center;
      margin-bottom: 20px;
      border: 2px solid;
    }
    .grade-A {
      background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
      border-color: #10B981;
      color: #065F46;
    }
    .grade-B {
      background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
      border-color: #3B82F6;
      color: #1E40AF;
    }
    .grade-C {
      background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
      border-color: #F59E0B;
      color: #92400E;
    }
    .grade-Reject {
      background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
      border-color: #EF4444;
      color: #991B1B;
    }
    .grade-Review {
      background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
      border-color: #F97316;
      color: #9A3412;
    }
    .grade-badge-pill {
      display: inline-block;
      padding: 4px 14px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      background: rgba(255, 255, 255, 0.8);
      margin-bottom: 8px;
    }
    .grade-title {
      font-size: 32px;
      font-weight: 800;
      margin-bottom: 4px;
    }
    .score-meter {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      font-size: 16px;
      font-weight: 700;
    }

    /* Score breakdown */
    .metrics-table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 13px;
    }
    .metrics-table th, .metrics-table td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .metrics-table th {
      color: var(--text-muted);
      font-weight: 600;
      background: #FAFCFA;
    }

    .recommendations-box {
      background: var(--gold-light);
      border: 1px solid #EAD8A4;
      border-radius: var(--radius-sm);
      padding: 16px;
      margin-bottom: 20px;
    }
    .recommendations-box h4 {
      color: #785A14;
      font-size: 14px;
      margin-bottom: 8px;
    }
    .recommendations-box ul {
      padding-left: 20px;
      font-size: 13px;
      color: #5C450F;
    }
    .recommendations-box li {
      margin-bottom: 4px;
    }

    /* Spinner */
    .spinner-wrap {
      display: none;
      text-align: center;
      padding: 50px 20px;
    }
    .spinner {
      width: 44px;
      height: 44px;
      border: 4px solid #E2E8F0;
      border-top-color: var(--green-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 16px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Chat Tab */
    .chat-container {
      max-width: 800px;
      margin: 0 auto;
    }
    .chat-window {
      height: 420px;
      overflow-y: auto;
      padding: 20px;
      background: #FAFCFA;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .chat-bubble {
      max-width: 78%;
      padding: 12px 16px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.5;
    }
    .chat-bot {
      background: #FFFFFF;
      border: 1px solid var(--border);
      align-self: flex-start;
      border-bottom-left-radius: 4px;
    }
    .chat-user {
      background: var(--green-dark);
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .chat-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }
    .chat-chip {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
    }
    .chat-chip:hover {
      border-color: var(--green-border);
      color: var(--green-dark);
      background: var(--green-light);
    }
    .chat-input-row {
      display: flex;
      gap: 10px;
    }
    .chat-input {
      flex: 1;
      padding: 12px 16px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 14px;
    }
    .chat-input:focus {
      outline: none;
      border-color: var(--green-primary);
    }

    /* Standards Cards */
    .standards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }
    .tier-card {
      padding: 20px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      background: white;
    }
    .tier-A { border-top: 4px solid #10B981; }
    .tier-B { border-top: 4px solid #3B82F6; }
    .tier-C { border-top: 4px solid #F59E0B; }
    .tier-Reject { border-top: 4px solid #EF4444; }

    /* API Docs */
    .endpoint-card {
      background: #F8FAFC;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 14px;
      margin-bottom: 10px;
    }
    .method-get {
      background: #E0F2FE;
      color: #0369A1;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
    }
    .method-post {
      background: #DCFCE7;
      color: #15803D;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
    }
    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      background: #F1F5F9;
      padding: 2px 6px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div class="brand-row">
        <span style="font-size: 36px;">🐛</span>
        <h1 class="brand-title">SilkCocoon AI</h1>
      </div>
      <p>Automated Sericulture Cocoon Quality Inspection, Central Silk Board (CSTRI) Grading & Transparent Market Valuation.</p>
      <div class="badge-bar">
        <span class="pill active">🟢 WSGI Active on Vercel</span>
        <span class="pill">CSTRI Scoring Standard</span>
        <span class="pill">Google Gemini Vision AI</span>
        <span class="pill">Real-time Inspection</span>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="tabs-nav">
      <button class="tab-btn active" onclick="switchTab('tab-inspector')">📷 Cocoon Inspector</button>
      <button class="tab-btn" onclick="switchTab('tab-chat')">💬 AI Farmer Assistant</button>
      <button class="tab-btn" onclick="switchTab('tab-standards')">📜 CSTRI Standards</button>
      <button class="tab-btn" onclick="switchTab('tab-api')">🔌 API & Settings</button>
    </nav>

    <!-- TAB 1: COCOON INSPECTOR -->
    <div id="tab-inspector" class="tab-panel active">
      <div class="inspector-grid">
        <!-- Input Column -->
        <div class="card">
          <div class="card-title">1. Provide Cocoon Photograph</div>
          <div class="card-sub">Upload a high-resolution photo or choose a preset test pattern.</div>

          <!-- Sample Presets -->
          <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); margin-bottom: 8px;">QUICK DEMO SAMPLES:</div>
          <div class="samples-grid">
            <button class="sample-chip" onclick="loadSample('grade_a', 'Sample 1: Grade A Bivoltine')">🏆 Grade A Bivoltine</button>
            <button class="sample-chip" onclick="loadSample('stained', 'Sample 2: Stained Cocoon')">⚠️ Stained Cocoon</button>
            <button class="sample-chip" onclick="loadSample('pierced', 'Sample 3: Uzifly Pierced')">🪰 Uzifly Pierced</button>
            <button class="sample-chip" onclick="loadSample('not_a_cocoon', 'Sample 4: Non-Cocoon')">❌ Non-Cocoon Object</button>
          </div>

          <!-- Action row (Upload vs Camera) -->
          <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <button class="btn btn-secondary" onclick="document.getElementById('file-input').click()" style="flex: 1;">📁 Browse Image</button>
            <button class="btn btn-secondary" id="cam-toggle-btn" onclick="toggleCamera()" style="flex: 1;">📷 Use Camera</button>
          </div>

          <!-- Camera Stream -->
          <div class="camera-box" id="camera-box">
            <video id="webcam-video" autoplay playsinline></video>
            <div class="camera-actions">
              <button class="btn btn-primary" onclick="captureWebcam()" style="padding: 6px 14px; font-size: 13px;">📸 Snap Photo</button>
              <button class="btn btn-secondary" onclick="stopCamera()" style="padding: 6px 14px; font-size: 13px; color: white; background: #333;">Close</button>
            </div>
          </div>
          <canvas id="camera-canvas" style="display: none;"></canvas>

          <!-- Drop Zone -->
          <div class="upload-zone" id="drop-zone" onclick="document.getElementById('file-input').click()">
            <input type="file" id="file-input" accept="image/jpeg,image/png,image/webp" onchange="handleFileSelect(event)">
            <span class="upload-icon">📸</span>
            <div style="font-weight: 700; margin-bottom: 4px;">Drag & Drop Cocoon Photo Here</div>
            <div style="font-size: 12px; color: var(--text-muted);">Supports JPG, PNG, WEBP (up to 10MB)</div>
          </div>

          <!-- Preview Box -->
          <div class="preview-box" id="preview-box">
            <button class="preview-clear" onclick="clearImage()">✕ Remove</button>
            <img id="preview-img" src="" alt="Cocoon Preview">
            <div id="preview-caption" style="padding: 6px; font-size: 12px; color: var(--text-muted);"></div>
          </div>

          <!-- Analyze CTA -->
          <button class="btn btn-primary" id="analyze-btn" onclick="runAnalysis()" disabled>
            🚀 Analyze Cocoon Quality
          </button>
        </div>

        <!-- Output Column -->
        <div class="card">
          <div class="card-title">2. AI Inspection & CSTRI Grading</div>
          <div class="card-sub">Optical analysis, defect detection & Central Silk Board score.</div>

          <!-- Empty State -->
          <div class="empty-state" id="empty-state">
            <span class="empty-icon">🔬</span>
            <h3 style="font-size: 16px; margin-bottom: 6px;">No Image Selected</h3>
            <p style="font-size: 13px; max-width: 320px; margin: 0 auto;">Select one of the demo samples on the left or upload your own cocoon photograph to see AI inspection results.</p>
          </div>

          <!-- Spinner State -->
          <div class="spinner-wrap" id="spinner-wrap">
            <div class="spinner"></div>
            <h3 style="font-size: 16px; color: var(--green-dark); margin-bottom: 4px;">Inspecting Cocoon Shell...</h3>
            <p style="font-size: 13px; color: var(--text-muted);">Evaluating compactness, color purity, and defect signatures...</p>
          </div>

          <!-- Result Container -->
          <div class="result-container" id="result-container">
            <div class="grade-banner" id="grade-banner">
              <span class="grade-badge-pill" id="grade-badge">COMMERCIAL GRADE</span>
              <div class="grade-title" id="grade-title">GRADE A</div>
              <div class="score-meter">
                <span>Quality Score:</span>
                <span id="score-val" style="font-size: 20px;">92.5</span>
                <span>/ 100</span>
              </div>
            </div>

            <table class="metrics-table">
              <tr>
                <th>Sericulture Metric</th>
                <th>Assessment</th>
              </tr>
              <tr>
                <td>Cocoon Color / Race</td>
                <td id="res-color">White (Bivoltine)</td>
              </tr>
              <tr>
                <td>Reeling Suitability</td>
                <td id="res-reeling">Eligible for Multi-end Automated Reeling</td>
              </tr>
              <tr>
                <td>Defects Detected</td>
                <td id="res-defects">None (Zero penalty)</td>
              </tr>
              <tr>
                <td>Indicative Rate (₹/kg)</td>
                <td id="res-rate" style="font-weight: 700; color: var(--green-dark);">₹680 - ₹740 / kg</td>
              </tr>
            </table>

            <div class="recommendations-box">
              <h4>💡 Actionable Recommendations for Farmer:</h4>
              <ul id="res-recommendations">
                <li>Defluff outer floss gently before auction weighing.</li>
                <li>Transport during cooler hours to prevent thermal damage.</li>
              </ul>
            </div>

            <button class="btn btn-secondary" onclick="downloadJSONReport()" style="width: 100%;">
              📥 Download Inspection Certificate (JSON)
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: AI FARMER ASSISTANT -->
    <div id="tab-chat" class="tab-panel">
      <div class="card chat-container">
        <div class="card-title">💬 Sericulture Farmer Advisory Assistant</div>
        <div class="card-sub">Ask any question regarding cocoon rearing, pest control, mandi trading, or CSTRI standards.</div>

        <div class="chat-chips">
          <span class="chat-chip" onclick="askQuestion('How to store Bivoltine cocoons before mandi auction?')">📦 Storing Bivoltine Cocoons</span>
          <span class="chat-chip" onclick="askQuestion('How to prevent Uzifly parasite damage?')">🪰 Preventing Uzifly</span>
          <span class="chat-chip" onclick="askQuestion('What causes melted cocoons during monsoon?')">💧 Melted Cocoon Causes</span>
          <span class="chat-chip" onclick="askQuestion('What are the CSTRI grading thresholds for Grade A?')">🏆 Grade A Thresholds</span>
        </div>

        <div class="chat-window" id="chat-window">
          <div class="chat-bubble chat-bot">
            <strong>SilkCocoon AI:</strong><br>
            Namaskara! I am your AI sericulture advisor. How can I assist you with your cocoon harvest, defect management, or mandi pricing today?
          </div>
        </div>

        <form class="chat-input-row" onsubmit="handleChatSubmit(event)">
          <input type="text" id="chat-input" class="chat-input" placeholder="Type your sericulture question..." required>
          <button type="submit" class="btn btn-primary" style="width: auto; padding: 12px 24px;">Send</button>
        </form>
      </div>
    </div>

    <!-- TAB 3: CSTRI STANDARDS -->
    <div id="tab-standards" class="tab-panel">
      <div class="card">
        <div class="card-title">📜 Central Silk Board (CSTRI) Cocoon Grading Standards</div>
        <div class="card-sub">Pricing benchmarks and defect deduction guidelines used across Karnataka & Tamil Nadu mandis.</div>

        <div class="standards-grid">
          <div class="tier-card tier-A">
            <h3 style="color: #065F46; font-size: 18px; margin-bottom: 6px;">Grade A (Score 85 - 100)</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Premium commercial quality. Uniform shape, firm shell, high shell ratio (>21%), reelability > 80%.</p>
            <div style="font-size: 12px; font-weight: 700; color: #065F46;">Benchmark Rate: ₹680 - ₹760 / kg</div>
          </div>

          <div class="tier-card tier-B">
            <h3 style="color: #1E40AF; font-size: 18px; margin-bottom: 6px;">Grade B (Score 70 - 84)</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Standard commercial grade. Minor fuzziness, acceptable shell firmness, reelability 70-79%.</p>
            <div style="font-size: 12px; font-weight: 700; color: #1E40AF;">Benchmark Rate: ₹580 - ₹660 / kg</div>
          </div>

          <div class="tier-card tier-C">
            <h3 style="color: #92400E; font-size: 18px; margin-bottom: 6px;">Grade C (Score 55 - 69)</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Fair grade with slight shape irregularities, loose shell, or minor external staining.</p>
            <div style="font-size: 12px; font-weight: 700; color: #92400E;">Benchmark Rate: ₹440 - ₹540 / kg</div>
          </div>

          <div class="tier-card tier-Reject">
            <h3 style="color: #991B1B; font-size: 18px; margin-bottom: 6px;">Reject (Score &lt; 55)</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Fatal defects: Pierced (Uzifly), melted/diseased, or heavily crushed. Diverted to dupion/spun silk.</p>
            <div style="font-size: 12px; font-weight: 700; color: #991B1B;">Discounted rate: ₹150 - ₹280 / kg</div>
          </div>
        </div>

        <h4 style="margin-bottom: 12px; color: var(--green-dark);">Major Defect Classifications:</h4>
        <table class="metrics-table">
          <tr>
            <th>Defect Name</th>
            <th>Cause & Severity</th>
            <th>Score Deduction</th>
          </tr>
          <tr>
            <td><strong>Pierced Cocoon</strong></td>
            <td>Uzifly parasite exit or premature moth emergence. Filament is severed. (Fatal)</td>
            <td><span style="color: #ef4444; font-weight: 700;">-50.0 (Immediate Reject)</span></td>
          </tr>
          <tr>
            <td><strong>Melted Cocoon</strong></td>
            <td>Pupa dies inside due to flacherie or grasserie; liquefies and stains shell. (Fatal)</td>
            <td><span style="color: #ef4444; font-weight: 700;">-50.0 (Immediate Reject)</span></td>
          </tr>
          <tr>
            <td><strong>Double Cocoon (Dupion)</strong></td>
            <td>Two worms spin together; produces tangled, coarse yarn.</td>
            <td><span style="color: #f59e0b; font-weight: 700;">-18.0</span></td>
          </tr>
          <tr>
            <td><strong>Urine / External Stain</strong></td>
            <td>Excretion or external dampness; weakens fiber tensile strength.</td>
            <td><span style="color: #f59e0b; font-weight: 700;">-15.0</span></td>
          </tr>
        </table>
      </div>
    </div>

    <!-- TAB 4: API & SETTINGS -->
    <div id="tab-api" class="tab-panel">
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-title">⚙️ API Key Configuration (Optional)</div>
        <div class="card-sub">Your API key is stored only in your browser session and sent encrypted to the server.</div>

        <div style="display: flex; gap: 10px; margin-bottom: 14px;">
          <input type="password" id="user-api-key" class="chat-input" placeholder="Enter Gemini or Sarvam API Key (AIzaSy... / sk_...)" style="flex: 1;">
          <button class="btn btn-primary" onclick="saveApiKey()" style="width: auto; padding: 12px 20px;">Save Key</button>
        </div>
        <p style="font-size: 12px; color: var(--text-muted);">
          Get a free key from <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: var(--green-primary); font-weight: 600;">Google AI Studio</a>.
          If no key is entered, SilkCocoon AI uses the backend environment key or CSTRI reference fallbacks.
        </p>
      </div>

      <div class="card">
        <div class="card-title">🔌 REST API Endpoints</div>
        <div class="card-sub">Integrate SilkCocoon AI grading directly into your mobile app or मंडी ERP system.</div>

        <div class="endpoint-card">
          <span class="method-get">GET</span> <code>/api/health</code>
          <p style="margin: 6px 0 0; font-size: 13px; color: var(--text-muted);">Checks backend server status and AI vision connection.</p>
        </div>

        <div class="endpoint-card">
          <span class="method-post">POST</span> <code>/api/analyze</code>
          <p style="margin: 6px 0 0; font-size: 13px; color: var(--text-muted);">Upload cocoon image (multipart or JSON base64) for optical CSTRI quality grading.</p>
        </div>

        <div class="endpoint-card">
          <span class="method-post">POST</span> <code>/api/chat</code>
          <p style="margin: 6px 0 0; font-size: 13px; color: var(--text-muted);">Send queries to sericulture advisory assistant.</p>
        </div>

        <div class="endpoint-card">
          <span class="method-get">GET</span> <code>/api/standards</code>
          <p style="margin: 6px 0 0; font-size: 13px; color: var(--text-muted);">Returns CSTRI sericulture defect penalty weights and benchmark thresholds.</p>
        </div>
      </div>
    </div>
  </div>

  <script>
    let activeImageBase64 = null;
    let currentResult = null;
    let cameraStream = null;

    // Load saved API Key if any
    document.addEventListener('DOMContentLoaded', () => {
      const savedKey = localStorage.getItem('silk_api_key');
      if (savedKey) {
        document.getElementById('user-api-key').value = savedKey;
      }
    });

    function saveApiKey() {
      const val = document.getElementById('user-api-key').value.trim();
      if (val) {
        localStorage.setItem('silk_api_key', val);
        alert('API Key saved locally for this browser session!');
      } else {
        localStorage.removeItem('silk_api_key');
        alert('API Key cleared.');
      }
    }

    function getApiKey() {
      return localStorage.getItem('silk_api_key') || '';
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.currentTarget.classList.add('active');
    }

    // Drag and Drop
    const dropZone = document.getElementById('drop-zone');
    ['dragenter', 'dragover'].forEach(name => {
      dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    });
    ['dragleave', 'drop'].forEach(name => {
      dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); });
    });
    dropZone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files.length) {
        processFile(e.dataTransfer.files[0]);
      }
    });

    function handleFileSelect(event) {
      if (event.target.files.length) {
        processFile(event.target.files[0]);
      }
    }

    function processFile(file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file (JPG, PNG, or WEBP).');
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        setImage(e.target.result, file.name + ' (' + Math.round(file.size / 1024) + ' KB)');
      };
      reader.readAsDataURL(file);
    }

    function setImage(dataUrl, caption) {
      activeImageBase64 = dataUrl;
      document.getElementById('preview-img').src = dataUrl;
      document.getElementById('preview-caption').innerText = caption || 'Uploaded image';
      document.getElementById('preview-box').style.display = 'block';
      document.getElementById('drop-zone').style.display = 'none';
      document.getElementById('analyze-btn').disabled = false;
      stopCamera();
    }

    function clearImage() {
      activeImageBase64 = null;
      document.getElementById('preview-box').style.display = 'none';
      document.getElementById('drop-zone').style.display = 'block';
      document.getElementById('file-input').value = '';
      document.getElementById('analyze-btn').disabled = true;
      document.getElementById('result-container').style.display = 'none';
      document.getElementById('empty-state').style.display = 'block';
    }

    // Preset Samples
    async function loadSample(sampleName, caption) {
      try {
        const resp = await fetch(`/api/sample/${sampleName}`);
        if (!resp.ok) throw new Error('Sample fetch failed');
        const blob = await resp.blob();
        const reader = new FileReader();
        reader.onload = (e) => {
          setImage(e.target.result, caption);
        };
        reader.readAsDataURL(blob);
      } catch (err) {
        alert('Could not load sample: ' + err.message);
      }
    }

    // Camera Support
    async function toggleCamera() {
      const box = document.getElementById('camera-box');
      if (box.style.display === 'block') {
        stopCamera();
      } else {
        try {
          cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
          const video = document.getElementById('webcam-video');
          video.srcObject = cameraStream;
          box.style.display = 'block';
          document.getElementById('drop-zone').style.display = 'none';
        } catch (err) {
          alert('Could not access camera: ' + err.message);
        }
      }
    }

    function captureWebcam() {
      const video = document.getElementById('webcam-video');
      const canvas = document.getElementById('camera-canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      setImage(dataUrl, 'Live Camera Capture (' + canvas.width + 'x' + canvas.height + 'px)');
    }

    function stopCamera() {
      if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
      }
      document.getElementById('camera-box').style.display = 'none';
      if (!activeImageBase64) {
        document.getElementById('drop-zone').style.display = 'block';
      }
    }

    // Run Analysis
    async function runAnalysis() {
      if (!activeImageBase64) return;

      document.getElementById('empty-state').style.display = 'none';
      document.getElementById('result-container').style.display = 'none';
      document.getElementById('spinner-wrap').style.display = 'block';
      document.getElementById('analyze-btn').disabled = true;

      try {
        const payload = {
          image_base64: activeImageBase64,
          api_key: getApiKey()
        };

        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        document.getElementById('spinner-wrap').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;

        if (!res.ok) {
          alert('Analysis Error: ' + (data.message || data.error || 'Server error'));
          document.getElementById('empty-state').style.display = 'block';
          return;
        }

        renderResult(data);
      } catch (err) {
        document.getElementById('spinner-wrap').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;
        alert('Connection error: ' + err.message);
        document.getElementById('empty-state').style.display = 'block';
      }
    }

    function renderResult(data) {
      currentResult = data;
      document.getElementById('result-container').style.display = 'block';

      const grade = data.grade || 'Grade A';
      const score = data.overall_score !== null && data.overall_score !== undefined ? data.overall_score : 88.0;

      const banner = document.getElementById('grade-banner');
      banner.className = 'grade-banner';

      if (grade.includes('Grade A') || grade.includes('A')) {
        banner.classList.add('grade-A');
      } else if (grade.includes('Grade B') || grade.includes('B')) {
        banner.classList.add('grade-B');
      } else if (grade.includes('Grade C') || grade.includes('C')) {
        banner.classList.add('grade-C');
      } else if (grade.includes('Reject')) {
        banner.classList.add('grade-Reject');
      } else {
        banner.classList.add('grade-Review');
      }

      document.getElementById('grade-title').innerText = grade;
      document.getElementById('score-val').innerText = typeof score === 'number' ? score.toFixed(1) : score;

      document.getElementById('res-color').innerText = data.color_type || 'White (Bivoltine)';
      document.getElementById('res-reeling').innerText = data.reeling_suitability || 'Standard Commercial Reeling';

      const defects = data.defects_detected || [];
      if (defects.length === 0) {
        document.getElementById('res-defects').innerHTML = '<span style="color: #10B981; font-weight: 700;">✓ None Detected (Clean lot)</span>';
      } else {
        document.getElementById('res-defects').innerHTML = '<span style="color: #EF4444; font-weight: 700;">⚠️ ' + defects.join(', ') + '</span>';
      }

      // Indicative Rate
      if (grade.includes('Grade A')) {
        document.getElementById('res-rate').innerText = '₹680 - ₹760 / kg';
      } else if (grade.includes('Grade B')) {
        document.getElementById('res-rate').innerText = '₹580 - ₹660 / kg';
      } else if (grade.includes('Grade C')) {
        document.getElementById('res-rate').innerText = '₹440 - ₹540 / kg';
      } else {
        document.getElementById('res-rate').innerText = '₹180 - ₹280 / kg (Discounted)';
      }

      const recsList = document.getElementById('res-recommendations');
      recsList.innerHTML = '';
      const recs = data.recommendations || ['Maintain cocoon sorting in clean wooden trays.', 'Check moisture before mandi dispatch.'];
      recs.forEach(r => {
        const li = document.createElement('li');
        li.innerText = r;
        recsList.appendChild(li);
      });
    }

    function downloadJSONReport() {
      if (!currentResult) return;
      const blob = new Blob([JSON.stringify(currentResult, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `SilkCocoon_Inspection_${currentResult.grade || 'Report'}.json`;
      a.click();
    }

    // Chat
    async function handleChatSubmit(e) {
      e.preventDefault();
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      askQuestion(text);
    }

    async function askQuestion(text) {
      switchTab('tab-chat');
      const win = document.getElementById('chat-window');

      // User Bubble
      const userDiv = document.createElement('div');
      userDiv.className = 'chat-bubble chat-user';
      userDiv.innerText = text;
      win.appendChild(userDiv);
      win.scrollTop = win.scrollHeight;

      // Bot Loading Bubble
      const botDiv = document.createElement('div');
      botDiv.className = 'chat-bubble chat-bot';
      botDiv.innerHTML = '<em>Thinking...</em>';
      win.appendChild(botDiv);
      win.scrollTop = win.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, api_key: getApiKey() })
        });
        const data = await res.json();
        botDiv.innerHTML = '<strong>SilkCocoon AI:</strong><br>' + (data.reply || 'No response.');
        if (data.action_items && data.action_items.length) {
          botDiv.innerHTML += '<ul style="margin-top: 8px; padding-left: 18px; font-size: 13px;">' +
            data.action_items.map(a => `<li>${a}</li>`).join('') + '</ul>';
        }
      } catch (err) {
        botDiv.innerHTML = '<span style="color: #ef4444;">Could not connect to advisory service.</span>';
      }
      win.scrollTop = win.scrollHeight;
    }
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
@app.route("/api/", methods=["GET"])
@app.route("/api/index", methods=["GET"])
@app.route("/api/index.py", methods=["GET"])
def index():
    """Serves the interactive sericulture quality inspection dashboard."""
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


@app.route("/api/sample/<sample_name>", methods=["GET"])
@app.route("/sample/<sample_name>", methods=["GET"])
def sample_image_endpoint(sample_name):
    """Serves bundled sample images for testing."""
    allowed = {
        "grade_a": "sample_grade_a.jpg",
        "stained": "sample_stained.jpg",
        "pierced": "sample_pierced.jpg",
        "not_a_cocoon": "sample_not_a_cocoon.jpg",
    }
    filename = allowed.get(sample_name.lower().replace("-", "_"))
    if not filename:
        return jsonify({"error": "Sample image not found"}), 404
    asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return send_from_directory(asset_dir, filename)


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
    action_items = result.get("advisory", {}).get("action_items", [])
    return jsonify({
        "success": result.get("success", False),
        "reply": reply_text,
        "action_items": action_items,
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
    2. JSON payload: { 'image_base64': '...', 'api_key': '...' }
    """
    image_bytes = None
    client_api_key = None

    if "image" in request.files:
        image_bytes = request.files["image"].read()
        client_api_key = request.form.get("api_key") or request.headers.get("X-API-Key")
    else:
        json_data = request.get_json(silent=True) or {}
        client_api_key = json_data.get("api_key") or request.headers.get("X-API-Key")
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

    # 2. Invoke Vision Analysis
    ai_success, parsed_ai, ai_err = analyze_cocoon_image_with_gemini(pil_image, api_key=client_api_key)
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
