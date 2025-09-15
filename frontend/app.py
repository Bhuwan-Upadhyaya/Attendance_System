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

# (Removed early __main__ block to avoid double-execution with Flask reloader)

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
        SELECT student_id, student_name AS name, status, timestamp
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
        SELECT id, image_path, detected_time, resolved
        FROM unverified_faces
        WHERE resolved = 0
        ORDER BY detected_time DESC
        """,
        conn
    )
    conn.close()
    return render_template("alerts.html", alerts=df.to_dict(orient="records"))

# ---------- Approve Unknown Face ----------
@app.route("/approve/<int:alert_id>", methods=["POST"])
def approve_face(alert_id):
    if request.method == "POST":
        student_name = request.form.get("student_name")
        roll_no = request.form.get("roll_no")
        
        if student_name and roll_no:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Add student to database
                cursor.execute("""
                    INSERT INTO students (name, roll_no)
                    VALUES (?, ?)
                """, (student_name, roll_no))
                
                student_id = cursor.lastrowid
                
                # Mark attendance
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO attendance (student_id, student_name, status, timestamp, session)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, student_name, "Present", timestamp, "Morning"))
                
                # Mark alert as resolved
                cursor.execute("""
                    UPDATE unverified_faces 
                    SET resolved = 1 
                    WHERE id = ?
                """, (alert_id,))
                
                conn.commit()
                conn.close()
                
                return f"✅ Student {student_name} approved and marked present! <a href='/alerts'>Back to Alerts</a>"
                
            except Exception as e:
                return f" Error approving student: {str(e)}"
        
        return " Please provide student name and roll number"

# ---------- Reject Unknown Face (Mark as Threat) ----------
@app.route("/reject/<int:alert_id>", methods=["POST"])
def reject_face(alert_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Mark alert as resolved (threat)
        cursor.execute("""
            UPDATE unverified_faces 
            SET resolved = 2 
            WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()
        
        return "Face marked as threat! Security has been notified. <a href='/alerts'>Back to Alerts</a>"
        
    except Exception as e:
        return f" Error rejecting face: {str(e)}"

# ---------- Get Recent Attendance (for real-time updates) ----------
@app.route("/api/recent_attendance")
def recent_attendance():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT student_name, status, timestamp
        FROM attendance
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        LIMIT 10
        """,
        conn
    )
    conn.close()
    return df.to_json(orient="records")

# ---------- Get Alert Count ----------
@app.route("/api/alert_count")
def alert_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM unverified_faces WHERE resolved = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return {"count": count}
# ---------- Search Students ----------
@app.route("/api/search_students")
def search_students():
    q = request.args.get("q", "").strip()
    if not q:
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, roll_no, '' as email, '' as phone
        FROM students
        WHERE name LIKE ? OR roll_no LIKE ?
        ORDER BY name ASC
        """,
        (f"%{q}%", f"%{q}%"),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r[0], "roll_no": r[1], "email": r[2], "phone": r[3]} for r in rows]


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
    print(" ATTENDANCE SYSTEM STARTING...")
    print("=" * 50)

    # Create tables if they don't exist and migrate structure
    create_tables()
    update_database_structure()

    # Guard to avoid running side-effects twice under Flask reloader
    import os as _os
    is_reloader_main = _os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if not app.debug or is_reloader_main:
        # Start face recognition and open browser once
        start_face_recognition()
        open_browser()

        print("All systems started!")
        print("Web Dashboard: http://127.0.0.1:5000")
        print("Face Recognition: Active")
        print("Ready for attendance marking!")
        print("=" * 50)

    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
