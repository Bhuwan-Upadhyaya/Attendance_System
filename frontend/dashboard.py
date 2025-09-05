# frontend/dashboard.py
import os
import sys
from flask import render_template, request

# Ensure project root for backend imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.utils import get_attendance, add_student

def init_routes(app):
    @app.route("/")
    def home():
        records = get_attendance()
        return render_template("index.html", records=records)

    @app.route("/add_student", methods=["GET", "POST"])
    def add_student_route():
        if request.method == "POST":
            name = request.form["name"]
            roll_no = request.form["roll_no"]
            photo_path = request.form.get("photo_path", None)
            add_student(name, roll_no, photo_path)
            return " Student added successfully!"
        return render_template("add_student.html")
