"""
Streamlit Community Cloud Entry Point (streamlit_app.py)
Directly launches the SilkCocoon AI dashboard on Streamlit Community Cloud.
"""

import os
import sys

try:
    import streamlit as st
except ImportError:
    st = None

from app import run_streamlit_dashboard

# When executed by Streamlit (streamlit run streamlit_app.py / Streamlit Cloud)
if st is not None and hasattr(st, "runtime") and st.runtime.exists():
    run_streamlit_dashboard()

if __name__ == "__main__":
    run_streamlit_dashboard()
