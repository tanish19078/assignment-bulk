import os
import sys

# Ensure Vercel can find the app.py file which is at the root of the project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
