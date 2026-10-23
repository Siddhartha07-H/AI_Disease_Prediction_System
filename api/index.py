"""
Vercel Serverless Function entrypoint for FastAPI.
Exposes the FastAPI 'app' instance to Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

# Vercel looks for 'app' in api/index.py
__all__ = ["app"]
