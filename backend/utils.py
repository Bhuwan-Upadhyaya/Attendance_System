
import os
import logging
from backend.database import get_connection
from backend.config import LOG_FILE, LOG_LEVEL, ATTENDANCE_STATUS_PRESENT
from datetime import datetime

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

def mark_attendance(student_id, status="Present", session="Morning"):
    """Insert an attendance record for a student."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        cursor.execute("""
            INSERT INTO attendance (student_id, date, time, status, session)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, date, time, status, session))

        conn.commit()
        conn.close()
        
        logging.info(f"Attendance marked: Student ID {student_id}, Status: {status}, Session: {session}, Date: {date} {time}")
        print(f"Attendance marked for student_id={student_id} on {date} {time}")
        
    except Exception as e:
        logging.error(f"Failed to mark attendance for student_id {student_id}: {str(e)}")
        raise

def get_attendance(date=None):
    """Fetch attendance records. Default = today."""
    conn = get_connection()
    cursor = conn.cursor()

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT a.id, s.name, s.roll_no, a.date, a.time, a.status, a.session
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
    """, (date,))

    records = cursor.fetchall()
    conn.close()
    return records

def add_student(name, roll_no, photo_path=None):
    """Add a new student if roll_no is not already present. Returns student id.

    This function performs an upsert-like behavior: if a student with the
    provided roll number already exists, it returns the existing student's id
    without creating a duplicate record. Otherwise, it inserts a new student
    row and returns the newly created id.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check for existing student by roll number
        cursor.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,))
        row = cursor.fetchone()
        if row:
            conn.close()
            logging.info(f"Student {name} (roll_no: {roll_no}) already exists with ID {row[0]}")
            return row[0]

        cursor.execute(
            """
            INSERT INTO students (name, roll_no, photo_path)
            VALUES (?, ?, ?)
            """,
            (name, roll_no, photo_path),
        )
        student_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logging.info(f"New student added: {name} (roll_no: {roll_no}, ID: {student_id})")
        return student_id
        
    except Exception as e:
        logging.error(f"Failed to add student {name} (roll_no: {roll_no}): {str(e)}")
        raise
