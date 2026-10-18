"""
Vercel Serverless Entry Point (api/index.py)
Exposes the WSGI 'app' object for Vercel Python runtime.
"""

import sys
import os

# Add parent directory to sys.path so root modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app

# Vercel Serverless Functions recognize 'app' as the WSGI callable
# Export app as both app and handler for maximum compatibility
handler = app
