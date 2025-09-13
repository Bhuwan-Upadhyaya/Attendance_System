from flask import Flask, render_template, send_file, request
import sqlite3
import pandas as pd
import os
import sys
import threading
import webbrowser
import subprocess
import time
from datetime import datetime

app = Flask(__name__)

# Add project root to path for backend imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Paths
DB_PATH = os.path.join(PROJECT_ROOT, "attendance.db")
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Import backend modules
from backend.utils import get_attendance, add_student
from backend.models import create_tables

def update_database_structure():
    """Update database structure to match new frontend requirements."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create new attendance table with timestamp
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                student_name TEXT,
                status TEXT,
                timestamp TEXT,
                session TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """)
        
        # Create unverified_faces table for alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unverified_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                detected_time TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        
        # Check if we need to migrate data
        cursor.execute("SELECT COUNT(*) FROM attendance")
        old_count = cursor.fetchone()[0]
        
        if old_count > 0:
            # Check if old table has 'date' column (old structure)
            cursor.execute("PRAGMA table_info(attendance)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'date' in columns and 'timestamp' not in columns:
                # Migrate existing data to new structure
                cursor.execute("""
                    SELECT a.*, s.name 
                    FROM attendance a 
                    JOIN students s ON a.student_id = s.id
                """)
                old_records = cursor.fetchall()
                
                for record in old_records:
                    # Convert date and time to timestamp
                    timestamp = f"{record[2]} {record[3]}"
                    cursor.execute("""
                        INSERT INTO attendance_new (student_id, student_name, status, timestamp, session)
                        VALUES (?, ?, ?, ?, ?)
                    """, (record[1], record[6], record[4], timestamp, record[5]))
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE attendance")
                cursor.execute("ALTER TABLE attendance_new RENAME TO attendance")
                print(" Database structure updated successfully!")
        
        conn.commit()
        
    except Exception as e:
        print(f" Database update failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def start_face_recognition():
    """Start the face recognition system in background."""
    def run_recognition():
        time.sleep(3)  # Wait for web server to start
        try:
            subprocess.run([sys.executable, "backend/face_recognition.py"], cwd=PROJECT_ROOT)
        except Exception as e:
            print(f" Face recognition failed: {str(e)}")
    
    thread = threading.Thread(target=run_recognition, daemon=True)
    thread.start()
    print(" Face recognition started in background")

def open_browser():
    """Open web dashboard in browser."""
    def open_url():
        time.sleep(5)  # Wait for server to start
        webbrowser.open("http://127.0.0.1:5000")
        print(" Web dashboard opened in browser!")
    
    thread = threading.Thread(target=open_url, daemon=True)
    thread.start()

# Initialize database and start systems
if __name__ == "__main__":
    print(" ATTENDANCE SYSTEM STARTING...")
    print("=" * 50)
    
    # Create tables if they don't exist
    create_tables()
    
    # Update database structure
    update_database_structure()
    
    # Start face recognition
    start_face_recognition()
    
    # Open browser
    open_browser()
    
    print("All systems started!")
    print("Web Dashboard: http://127.0.0.1:5000")
    print("Face Recognition: Active")
    print("Ready for attendance marking!")
    print("=" * 50)

# ---------- Home ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- Dashboard (today’s attendance) ----------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT student_id, name, status, timestamp
        FROM attendance
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        """,
        conn
    )
    conn.close()
    return render_template("dashboard.html", records=df.to_dict(orient="records"))


# ---------- Alerts (unverified faces) ----------
@app.route("/alerts")
def alerts():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT id, image_path, detected_time
        FROM unverified_faces
        WHERE resolved = 0
        """,
        conn
    )
    conn.close()
    return render_template("alerts.html", alerts=df.to_dict(orient="records"))


# ---------- Add Student ----------
@app.route("/add_student", methods=["GET", "POST"])
def add_student_route():
    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        photo_path = request.form.get("photo_path", None)
        try:
            add_student(name, roll_no, photo_path)
            return "Student added successfully! <a href='/dashboard'>Go to Dashboard</a>"
        except Exception as e:
            return f" Error adding student: {str(e)}"
    return render_template("add_student.html")

# ---------- Download CSV (all attendance records) ----------
@app.route("/download_csv")
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    conn.close()

    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path = os.path.join(EXPORTS_DIR, filename)
    df.to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
