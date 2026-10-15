# SilkCocoon AI 🐛
### Automated Sericulture Cocoon Quality Inspection & Transparent Market Grading

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini Vision](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-4285F4.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Project Overview

**SilkCocoon AI** is an open, beginner-maintainable, multimodal AI application built for the sericulture (silk farming) industry. It enables smallholder silkworm farmers and silk reeling buyers to quickly inspect silkworm cocoons, detect commercial defects (such as uzifly parasite pierced holes, melting, or double cocoons), compute an objective sericulture quality grade, and determine fair market pricing recommendations.

Unlike systems that fabricate scores or rely on opaque black-box models, **SilkCocoon AI** implements **transparent scoring logic**, provides **verifiable visual evidence**, and features a **safe manual-review state** whenever visual evidence is inadequate or ambiguous.

---

## 2. Problem Statement

In traditional silk-producing regions (e.g., Karnataka, Andhra Pradesh, Tamil Nadu in India, as well as parts of China, Brazil, and Vietnam):

1. **Subjective Manual Inspection:** Cocoon markets (mandis) rely on visual estimates by human intermediaries. Farmers frequently suffer arbitrary price cuts due to disputed defect rates.
2. **Hidden Pierced & Melted Defects:** Parasitic uzifly larvae bore exit holes in cocoons. A single pierced cocoon breaks the continuous 800–1,500-meter silk filament, making automated reeling impossible.
3. **Lack of Digital Transparency:** Smallholder farmers lack access to laboratory testing tools before traveling to distant auction markets.

---

## 3. Key Features

- **Multi-Source Image Input:** Supports drag-and-drop file upload (`.jpg`, `.png`, `.webp`) and live camera capture directly from mobile devices or laptops.
- **Strict In-Memory Validation:** Validates image format, prevents file-size overflows, and guarantees privacy by processing photos in RAM without permanent disk writes.
- **Multimodal AI Analysis:** Evaluates shape uniformity, shell compactness, surface cleanliness, and color type using verified Vision-Language models.
- **Auditable Sericulture Scoring:** Implements transparent scoring based on Central Silk Board and FAO commercial grading benchmarks.
- **Severe Defect Safeguards:** Automatically caps fatal defects (e.g., uzifly pierced emergence or melted pupa) at **Reject** status.
- **Anti-Fabrication Guardrail (Manual Review):** Refuses to guess or generate random numbers if an image is blurry, poorly lit, or does not contain cocoons.
- **One-Click Test Gallery:** Pre-loaded with Grade A, Stained, Pierced, and Non-Cocoon sample images for instant evaluation.
- **Certificate Export:** Download an inspection audit report in standard JSON format.

---

## 4. Architecture

```text
[ Farmer / Buyer ]
       │
       ▼ (Mobile / Laptop Web UI)
┌────────────────────────────────────────────────────────┐
│               Streamlit Dashboard (app.py)             │
│  - Responsive UI / Camera Capture / Preset Gallery     │
└───────────┬────────────────────────────────┬───────────┘
            │ In-Memory Bytes                │
            ▼                                ▼
┌───────────────────────────┐   ┌──────────────────────────┐
│ image_analysis.py         │   │ scoring.py               │
│ - PIL Validation          │   │ - Domain Penalties       │
│ - Gemini Vision Prompt    │──▶│ - Weighted Grading Math  │
│ - JSON Response Validator │   │ - Manual Review Guard    │
└───────────┬───────────────┘   └────────────┬─────────────┘
            │                                │
            ▼ (HTTPS REST)                   ▼
┌───────────────────────────┐   ┌──────────────────────────┐
│ Multimodal Vision AI      │   │ Verified Inspection      │
│ (Google Gemini 1.5 Flash) │   │ Certificate & Guidance   │
└───────────────────────────┘   └──────────────────────────┘
```

---

## 5. Model Information, License & Source

| Attribute | Specification |
| :--- | :--- |
| **Model Name** | Google Gemini 1.5 Flash (`gemini-1.5-flash`) / Gemini 2.0 Flash |
| **Provider** | Google DeepMind / Google AI Studio |
| **License** | Google AI Studio Terms of Service (Permitted for commercial & hackathon development) |
| **Architecture** | Multimodal Transformer (Vision & Text unified attention) |
| **Role in App** | Extracts visual features (shell compactness, surface cleanliness, shape symmetry, and identifies defect classes). |
| **Alternative Open-Source Models** | Compatible with Hugging Face Vision LLMs (e.g. `Qwen/Qwen2.5-VL-7B-Instruct` or `meta-llama/Llama-3.2-11B-Vision-Instruct`). |

---

## 6. Installation & Local Setup (Windows)

### Prerequisites
- Python 3.10 to 3.13 installed ([python.org](https://www.python.org/downloads/))
- Git installed ([git-scm.com](https://git-scm.com/))
- A free Google AI Studio API Key ([aistudio.google.com](https://aistudio.google.com/app/apikey))

### Step 1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd "c:\Users\MEGHANA MAHADEVA\OneDrive\Desktop\backend\SilkCocoonAI"
```

### Step 2: Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure API Credentials
Create a `.env` file from `.env.example`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in Notepad and insert your real Gemini API Key:
```env
GEMINI_API_KEY=AIzaSy...your_real_key_here
GEMINI_MODEL=gemini-1.5-flash
MAX_UPLOAD_SIZE_MB=10
```

---

## 7. How to Run Locally

Start the Streamlit application:
```powershell
streamlit run app.py
```
The browser will automatically open at:
```text
http://localhost:8501
```

---

## 8. Running the Test Suite

SilkCocoon AI includes a thorough test suite verifying image safety, response parsing, missing credentials, and scoring logic:

```powershell
pytest -v
```

Expected output:
```text
tests/test_image_validation.py::test_valid_jpeg_upload PASSED
tests/test_image_validation.py::test_valid_png_upload PASSED
tests/test_image_validation.py::test_empty_image_upload PASSED
tests/test_image_validation.py::test_oversized_image_upload PASSED
tests/test_image_validation.py::test_corrupted_image_bytes PASSED
tests/test_image_validation.py::test_undersized_image_resolution PASSED
tests/test_scoring.py::test_grade_a_sufficient_evidence PASSED
tests/test_scoring.py::test_grade_b_standard_cocoon PASSED
tests/test_scoring.py::test_fatal_defect_pierced_cocoon PASSED
tests/test_scoring.py::test_fatal_defect_melted_cocoon PASSED
tests/test_scoring.py::test_major_defect_double_cocoon PASSED
tests/test_scoring.py::test_no_score_generated_when_not_a_cocoon PASSED
tests/test_scoring.py::test_no_score_generated_when_evidence_insufficient PASSED
tests/test_ai_parsing_and_errors.py::test_clean_json_response_with_markdown_fences PASSED
tests/test_ai_parsing_and_errors.py::test_clean_json_response_without_fences PASSED
tests/test_ai_parsing_and_errors.py::test_parse_empty_model_response PASSED
tests/test_ai_parsing_and_errors.py::test_parse_invalid_json_syntax PASSED
tests/test_ai_parsing_and_errors.py::test_missing_api_credentials_handling PASSED
tests/test_ai_parsing_and_errors.py::test_dummy_placeholder_api_key_handling PASSED
```

---

## 9. Security & Privacy Safeguards

1. **Zero Secret Leaks:** API credentials are read exclusively from environment variables or masked session inputs. Secrets are barred from client responses and `.gitignore` prevents `.env` commits.
2. **RAM-Only Processing:** Uploaded photos are held in Python `BytesIO` streams during analysis and discarded after inference. No photos are written to disk.
3. **Upload Boundary Limits:** Files larger than 10MB or resolutions smaller than 64x64 are rejected before invoking AI models.
4. **Data Transmission Notice:** The interface explicitly informs users that images are transmitted over secure HTTPS to the inference endpoint.

---

## 10. Known Limitations

- **Shell Thickness / Floss Density:** A 2D photograph evaluates visible surface texture and firmness; it cannot weigh individual cocoons or calculate precise shell ratio without a physical balance scale.
- **Inner Melted Pupa Stains:** While exterior urine and disease stains are readily detected, mild internal pupal melting without shell penetration requires candling (light illumination).
- **Network Dependency:** Cloud inference requires an active internet connection.

---

## 11. Deployment Guide

### Deploy to Streamlit Community Cloud (Recommended & Free)
1. Push your repository to GitHub (ensure `.env` is NOT committed).
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub repository:
   - **Repository:** `your-username/SilkCocoonAI`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Advanced Settings** -> **Secrets**, and add your API key:
   ```toml
   GEMINI_API_KEY = "your_actual_key"
   ```
5. Click **Deploy**. Your app is live with HTTPS!

---

## 12. Future Improvements Roadmap

- [ ] **On-Device Edge Inference:** Integrate TensorFlow Lite or ONNX vision models for offline rural mandi operation.
- [ ] **Physical Scale Integration:** Connect Bluetooth balance scales to automatically compute Shell Ratio percentage ($SR\%$).
- [ ] **Vernacular Voice Advisory:** Add audio explanations in Kannada, Telugu, Tamil, and Hindi for grassroots sericulture farmers.
- [ ] **Market Auction Direct Bidding:** Connect verified grades directly to local mandi trading boards.
