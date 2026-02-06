# ===================================================================
# PythonAnywhere WSGI Configuration File
# ===================================================================
# This file is NOT used locally. Copy its contents into the
# PythonAnywhere WSGI configuration file found at:
#   Web tab → "WSGI configuration file" link
#   (typically /var/www/yourusername_pythonanywhere_com_wsgi.py)
# ===================================================================

import sys
import os

# Add your project directory to the sys.path
# Replace 'RohanAnil' with your actual PythonAnywhere username
project_home = '/home/RohanAnil/Study-Notion'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables (optional overrides)
os.environ['SECRET_KEY'] = 'study-notion-secret-key-2026'
os.environ['GEMINI_API_KEY'] = ''  # Optional: add your Gemini API key

# Import and create the Flask app
from main import create_app
application = create_app()
