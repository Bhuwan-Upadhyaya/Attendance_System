# frontend/app.py
import os
import sys
from flask import Flask

# Ensure project root is on sys.path for stable imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.models import create_tables
import frontend.dashboard as dashboard

app = Flask(__name__)

# Initialize DB tables on startup
create_tables()

# Register routes from dashboard.py
dashboard.init_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
