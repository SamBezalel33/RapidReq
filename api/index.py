"""
=============================================================================
RAPIDREQ - Vercel Serverless Entry Point
=============================================================================
Vercel requires the Flask app to be exposed as `app` in api/index.py.
All routes, queue logic, and DB access remain in the parent modules.
=============================================================================
"""

import sys
import os

# Add parent directory to path so we can import app.py, database.py, etc.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# Import the Flask app instance from app.py
from app import app

# Ensure Flask resolves /static and /templates from the project root
# (not from the api/ subfolder where this file lives)
app.static_folder = os.path.join(ROOT_DIR, "static")
app.template_folder = os.path.join(ROOT_DIR, "templates")

# Vercel looks for a variable named `app` (WSGI callable)
