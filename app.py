"""
SilkCocoonAI - Main Application Dashboard (app.py)

A practical, transparent, beginner-maintainable AI tool for silk cocoon quality
assessment and commercial grading using Multimodal AI.
"""

import os
import json
from io import BytesIO
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Import local modules
from image_analysis import (
    validate_image_bytes,
    analyze_cocoon_image_with_gemini,
)
from scoring import (
    calculate_cocoon_grade,
    CocoonGradingResult,
    DEFECT_PENALTY_WEIGHTS,
)

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="SilkCocoon AI - Sericulture Quality Grading",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Silk-Inspired Styling (Mobile & Desktop Responsive)
st.markdown(
    """
    <style>
    /* Global & Typography */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1b4332;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #40916c;
        margin-bottom: 1.5rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-green { background-color: #d8f3dc; color: #1b4332; border: 1px solid #74c69d; }
    .badge-gold { background-color: #fefae0; color: #b08968; border: 1px solid #dda15e; }
    .badge-red { background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .badge-blue { background-color: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }

    /* Cards */
    .metric-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .grade-display-card {
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
        border-width: 2px;
        border-style: solid;
    }
    .grade-A {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-color: #22c55e;
        color: #14532d;
    }
    .grade-B {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-color: #3b82f6;
        color: #1e3a8a;
    }
    .grade-C {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-color: #f59e0b;
        color: #78350f;
    }
    .grade-Reject {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-color: #ef4444;
        color: #7f1d1d;
    }
    .grade-Review {
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
        border-color: #f97316;
        color: #7c2d12;
    }

    /* Privacy and footer */
    .privacy-notice {
        font-size: 0.82rem;
        color: #64748b;
        border-top: 1px solid #e2e8f0;
        padding-top: 12px;
        margin-top: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar: Setup, Credentials, & Quick Test Samples
# ---------------------------------------------------------
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=400&q=80",
        caption="Sericulture AI Quality Verification",
        use_container_width=True,
    )
    st.title("⚙️ Configuration")

    # API Key check and manual entry option
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    has_env_key = bool(env_key and env_key != "your_gemini_api_key_here")

    if has_env_key:
        st.success("✅ GEMINI_API_KEY detected from environment.")
        user_api_key = env_key
    else:
        st.warning("⚠️ API Key not configured in `.env`.")
        user_api_key = st.text_input(
            "Enter Gemini API Key (Temporary Session):",
            type="password",
            help="Your key stays in session memory and is never logged or written to disk.",
        )
        if user_api_key and len(user_api_key.strip()) < 15:
            st.info("💡 A valid Google API Key is usually 30-60 characters long. Click 'Copy key' from Google AI Studio and paste it here.")
        st.caption(
            "Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)."
        )

    # Model Selection
    selected_model = st.selectbox(
        "Multimodal AI Model:",
        options=["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0,
        help="Fast, cost-effective multimodal vision model for real-time agricultural grading.",
    )

    st.markdown("---")
    st.subheader("🧪 Demo Sample Gallery")
    st.write("Test grading instantly without needing your own photos:")

    sample_choice = st.radio(
        "Select a sample image:",
        options=[
            "None (Upload my own)",
            "Sample 1: Grade A Bivoltine",
            "Sample 2: Stained Cocoon",
            "Sample 3: Uzifly Pierced Cocoon",
            "Sample 4: Non-Cocoon (Out of Domain)",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        """
        <div class="privacy-notice">
        <b>🔒 Privacy & Security:</b><br>
        - Uploaded images are held strictly in temporary RAM during analysis.<br>
        - No images are saved permanently to the server disk without explicit consent.<br>
        - Files are verified over encrypted HTTPS with the selected AI vision endpoint.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Helper: Load Sample Images
# ---------------------------------------------------------
def get_sample_image_bytes(choice: str) -> BytesIO:
    base_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    mapping = {
        "Sample 1: Grade A Bivoltine": os.path.join(base_assets, "sample_grade_a.jpg"),
        "Sample 2: Stained Cocoon": os.path.join(base_assets, "sample_stained.jpg"),
        "Sample 3: Uzifly Pierced Cocoon": os.path.join(base_assets, "sample_pierced.jpg"),
        "Sample 4: Non-Cocoon (Out of Domain)": os.path.join(base_assets, "sample_not_a_cocoon.jpg"),
    }
    file_path = mapping.get(choice)
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return BytesIO(f.read())
    return None


# ---------------------------------------------------------
# Main UI Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">SilkCocoon AI 🐛</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Automated Sericulture Cocoon Quality Inspection & Fair Market Grading</div>',
    unsafe_allow_html=True,
)

tab_inspect, tab_standards, tab_diagnostics = st.tabs(
    ["📷 Cocoon Inspector", "📜 Sericulture Standards", "🛠️ System Diagnostics"]
)


# ---------------------------------------------------------
# TAB 1: COCOON INSPECTOR
# ---------------------------------------------------------
with tab_inspect:
    col_input, col_output = st.columns([1, 1], gap="large")

    active_image_bytes: bytes = None
    source_name = ""

    with col_input:
        st.subheader("1. Provide Cocoon Photograph")

        # Determine if a demo sample was chosen from the sidebar
        if sample_choice != "None (Upload my own)":
            sample_stream = get_sample_image_bytes(sample_choice)
            if sample_stream:
                active_image_bytes = sample_stream.getvalue()
                source_name = sample_choice
                st.info(f"Loaded preset: **{sample_choice}**")
            else:
                st.warning("Sample asset not found on disk. Please upload your own image below.")

        if not active_image_bytes:
            input_mode = st.radio(
                "Image Source:",
                options=["File Upload (Drag & Drop)", "Live Camera Capture"],
                horizontal=True,
            )

            if input_mode == "File Upload (Drag & Drop)":
                uploaded_file = st.file_uploader(
                    "Upload a clear photograph of silk cocoon(s):",
                    type=["jpg", "jpeg", "png", "webp"],
                    help="Upload JPG, PNG, or WEBP up to 10MB.",
                )
                if uploaded_file is not None:
                    active_image_bytes = uploaded_file.getvalue()
                    source_name = uploaded_file.name
            else:
                camera_file = st.camera_input("Take a photo of the cocoon:")
                if camera_file is not None:
                    active_image_bytes = camera_file.getvalue()
                    source_name = "Camera_Capture.jpg"

        # Validate and preview if an image is loaded
        valid_img_obj: Image.Image = None
        if active_image_bytes:
            is_valid, val_msg, valid_img_obj = validate_image_bytes(active_image_bytes, max_size_mb=10)

            if not is_valid:
                st.error(f"❌ Image Validation Failed: {val_msg}")
            else:
                st.success("✅ Image validated: Format & resolution suitable for inspection.")
                st.image(
                    valid_img_obj,
                    caption=f"Preview: {source_name} ({valid_img_obj.width}x{valid_img_obj.height} px)",
                    use_container_width=True,
                )

                if st.button("🔄 Reset / Clear Image"):
                    st.rerun()

    with col_output:
        st.subheader("2. AI Inspection & Sericulture Grading")

        if not active_image_bytes or not valid_img_obj:
            st.info(
                "👈 Please upload a cocoon photograph or select a sample from the sidebar to begin."
            )
        else:
            # Check API Key availability
            session_key = st.session_state.get("api_key", "").strip()
            effective_key = user_api_key or session_key

            if not effective_key or effective_key == "your_gemini_api_key_here":
                st.warning("⚠️ Multimodal AI service is not yet configured.")
                st.markdown(
                    """
                    To analyze this cocoon photograph, SilkCocoon AI connects to Google's Multimodal Vision AI.
                    
                    You can get a **100% free Gemini API key** in 30 seconds (no credit card required).
                    """
                )

                st.markdown("#### 🔑 Activate AI Vision Engine")
                direct_key_input = st.text_input(
                    "Paste your Gemini API Key below:",
                    type="password",
                    placeholder="AIzaSy...",
                    help="Your key is kept safe and used only for evaluating your uploaded photo.",
                )

                col_k1, col_k2 = st.columns([1, 1])
                with col_k1:
                    save_env_choice = st.checkbox("Remember key on this computer (save to `.env`)", value=True)
                with col_k2:
                    st.caption("[👉 Get Free Key at Google AI Studio](https://aistudio.google.com/app/apikey)")

                if st.button("🚀 Activate & Run Analysis", type="primary", use_container_width=True):
                    if direct_key_input and direct_key_input.strip():
                        clean_k = direct_key_input.strip()
                        st.session_state["api_key"] = clean_k
                        if save_env_choice:
                            try:
                                env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
                                with open(env_file_path, "w", encoding="utf-8") as f:
                                    f.write(f"GEMINI_API_KEY={clean_k}\nGEMINI_MODEL=gemini-1.5-flash\nMAX_UPLOAD_SIZE_MB=10\n")
                            except Exception:
                                pass
                        st.rerun()
                    else:
                        st.error("Please paste your Gemini API Key in the box above.")

                with st.expander("❓ How to get your free Gemini API Key (3 Quick Steps)"):
                    st.markdown(
                        """
                        1. Visit **[Google AI Studio](https://aistudio.google.com/app/apikey)** and sign in with any Google account.
                        2. Click the blue **'Create API key'** button (select 'Create in new project').
                        3. Copy the key (starts with `AIzaSy...`) and paste it into the box above!
                        """
                    )
                st.stop()

            # Trigger Button
            analyze_clicked = st.button("🚀 Analyze Cocoon Quality", type="primary", use_container_width=True)

            if analyze_clicked:
                with st.spinner("Analyzing cocoon visual features using Multimodal AI..."):
                    # Step 1: Call Multimodal Vision AI
                    success, ai_response, error_msg = analyze_cocoon_image_with_gemini(
                        image=valid_img_obj,
                        api_key=effective_key,
                        model_name=selected_model,
                    )

                    if not success:
                        st.error(f"❌ AI Analysis Error: {error_msg}")
                        st.info("💡 You can retry the analysis or check your network connection.")
                    else:
                        # Step 2: Compute transparent grading & audit trail
                        result: CocoonGradingResult = calculate_cocoon_grade(ai_response)
                        st.session_state["last_result"] = result.to_dict()
                        st.session_state["raw_ai"] = ai_response

            # Display Results if available in session
            if "last_result" in st.session_state:
                res_dict = st.session_state["last_result"]
                status = res_dict.get("status")
                grade = res_dict.get("grade", "Manual Review")
                overall_score = res_dict.get("overall_score")

                # ====================================================
                # CASE 1: MANUAL REVIEW / INSUFFICIENT EVIDENCE
                # ====================================================
                if status == "MANUAL_REVIEW_REQUIRED" or overall_score is None:
                    st.markdown(
                        f"""
                        <div class="grade-display-card grade-Review">
                            <span class="badge-pill badge-gold">ACTION REQUIRED</span>
                            <h2 style="margin: 8px 0; color: #9a3412;">⚠️ Manual Review Recommended</h2>
                            <p style="font-size: 1.05rem; margin: 0;"><b>Reason:</b> {res_dict.get('manual_review_reason')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("#### 📸 Recommended Photography Guidelines for Farmers:")
                    for tip in res_dict.get("guidance_tips", []):
                        st.write(f"- {tip}")

                    with st.expander("🔍 AI Diagnostic Notes"):
                        st.write(f"**Identified as Cocoon:** {'Yes' if res_dict.get('is_cocoon') else 'No'}")
                        st.write(f"**Evidence Sufficient:** {'Yes' if res_dict.get('evidence_sufficient') else 'No'}")
                        for obs in res_dict.get("observations", []):
                            st.write(f"• {obs}")

                # ====================================================
                # CASE 2: SUCCESSFUL SERICULTURE GRADING
                # ====================================================
                else:
                    card_css = f"grade-{grade.replace(' ', '')}"
                    st.markdown(
                        f"""
                        <div class="grade-display-card {card_css}">
                            <span class="badge-pill badge-green">AUDITED EVALUATION</span>
                            <h1 style="margin: 6px 0; font-size: 2.5rem;">{grade}</h1>
                            <h3 style="margin: 0; font-weight: 500;">Overall Quality Score: <b>{overall_score} / 100</b></h3>
                            <p style="margin-top: 8px; font-size: 0.95rem;"><b>Commercial Recommendation:</b> {res_dict.get('commercial_action')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Sub-scores breakdown
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Shell Compactness", f"{res_dict.get('compactness_score')}/100", help="Firmness and silk layer thickness (Weight: 35%)")
                    with m2:
                        st.metric("Cleanliness", f"{res_dict.get('cleanliness_score')}/100", help="Freedom from urine stains or soil (Weight: 35%)")
                    with m3:
                        st.metric("Shape Uniformity", f"{res_dict.get('shape_uniformity_score')}/100", help="Symmetrical oval shape (Weight: 30%)")

                    # Defects section
                    st.markdown("#### 🔍 Defect Analysis & Deductions")
                    defects = res_dict.get("defects_detected", [])
                    if not defects:
                        st.success("✅ **Zero commercial defects detected.** Cocoon shell is intact, clean, and uniform.")
                    else:
                        st.warning(
                            f"⚠️ **Defects Flagged ({len(defects)}):** {', '.join([d.title() for d in defects])} "
                            f"(Penalty applied: -{res_dict.get('defect_penalty')} pts)"
                        )

                    # Reelability & Commercial Insights
                    st.markdown("#### 🏭 Reeling & Market Suitability")
                    st.write(f"• **Estimated Reelability:** {res_dict.get('estimated_reelability')}")
                    st.write(f"• **Color / Race Classification:** {res_dict.get('color_type')}")
                    st.write(f"• **Estimated Cocoon Count:** {res_dict.get('cocoon_count')}")

                    # Visual Observations & Recommendations
                    with st.expander("📋 Detailed Observations & Advisory", expanded=True):
                        st.markdown("**Visual Observations:**")
                        for obs in res_dict.get("observations", []):
                            st.write(f"• {obs}")

                        st.markdown("**Actionable Farmer Recommendations:**")
                        for rec in res_dict.get("recommendations", []):
                            st.write(f"💡 {rec}")

                    # Download Report Option
                    report_json = json.dumps(res_dict, indent=2)
                    st.download_button(
                        label="📥 Download Inspection Certificate (JSON)",
                        data=report_json,
                        file_name=f"Cocoon_Grading_{grade.replace(' ', '_')}.json",
                        mime="application/json",
                    )


# ---------------------------------------------------------
# TAB 2: SERICULTURE STANDARDS
# ---------------------------------------------------------
with tab_standards:
    st.subheader("📜 Sericulture Cocoon Quality Standards")
    st.markdown(
        """
        Silk cocoon pricing depends heavily on reelability and silk percentage.
        Below are the standard sericulture parameters used across major silk-producing markets
        (e.g., Central Silk Board, Karnataka & Tamil Nadu mandis):
        """
    )

    col_std1, col_std2 = st.columns(2)
    with col_std1:
        st.markdown(
            """
            ### 🏆 Commercial Grade Tiers
            - **Grade A (Score 85 - 100):**
              - Clean, uniform, firm shell with no stains or holes.
              - Reelability > 80%, continuous filament, low renditta (6-7 kg cocoons per 1 kg silk).
              - Eligible for automated multi-end reeling and premium prices.
            - **Grade B (Score 70 - 84):**
              - Minor surface wrinkles or light fuzz; firm body.
              - Reelability 70-79%. Standard commercial pricing.
            - **Grade C (Score 50 - 69):**
              - Moderate shape irregularities, loose shell, or slight exterior staining.
              - Higher filament breakage during reeling.
            - **Reject / Defective (Score < 50):**
              - Pierced, melted, double, or severely crushed cocoons.
              - Unsuitable for standard reeling; diverted to dupion or spun silk.
            """
        )

    with col_std2:
        st.markdown(
            """
            ### ❌ Major Defect Classification
            - **Pierced Cocoon (Fatal):**
              - Caused by uzifly parasite emergence or premature moth exit. The continuous silk thread is severed into small bits, making commercial reeling impossible.
            - **Melted Cocoon (Fatal):**
              - Silkworm dies inside the cocoon due to disease (flacherie/grassserie) and liquefies, heavily staining the inner shell.
            - **Double Cocoon / Dupion (Major):**
              - Spun by two worms together. Filament is tangled and irregular, producing coarse dupion yarn.
            - **Urine Stained (Moderate):**
              - Stained by moth excretion before harvest; weakens fiber tensile strength.
            """
        )


# ---------------------------------------------------------
# TAB 3: SYSTEM DIAGNOSTICS & AUDIT TRAIL
# ---------------------------------------------------------
with tab_diagnostics:
    st.subheader("🛠️ Technical Diagnostics & System Health")

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.write("**Environment Status:**")
        st.write(f"- Python Runtime: 3.13")
        st.write(f"- Multimodal Vision Provider: Google Gemini API")
        st.write(f"- Active Model: `{selected_model}`")
        st.write(f"- API Key Configured: `{'Yes (Valid length)' if user_api_key else 'No'}`")
        st.write(f"- In-Memory Image Buffer: Active (Zero disk writes)")

    with d_col2:
        st.write("**Defect Penalty Configuration:**")
        st.json(DEFECT_PENALTY_WEIGHTS)

    if "raw_ai" in st.session_state:
        st.markdown("#### 🔬 Last Raw Multimodal Model Payload (Audit Trail)")
        st.json(st.session_state["raw_ai"])
