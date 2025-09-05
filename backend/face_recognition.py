import os
import sys
import cv2
import numpy as np
from datetime import datetime

# Ensure project root for backend-relative imports when run directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.utils import mark_attendance
from backend.database import get_connection

# Paths
DATASET_PATH = "data/faces/train"
MODEL_PATH = "data/models/face_recognizer.yml"

# Load Haar Cascade
haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Load trained recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
if os.path.exists(MODEL_PATH):
    recognizer.read(MODEL_PATH)
else:
    print(" No trained model found! Run train_faces.py first.")
    exit()

def get_student_id_from_roll(roll_no):
    """Fetch student_id from DB using roll_no."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def start_recognition(session="Morning"):
    """Start webcam and perform real-time recognition."""
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = haar_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]

            # Predict with recognizer
            label, confidence = recognizer.predict(roi_gray)

            if confidence < 60:  # Threshold (lower = better match)
                roll_no = f"Student_{label}"   # Label mapping from training
                student_id = get_student_id_from_roll(roll_no)

                if student_id:
                    mark_attendance(student_id, status="Present", session=session)

                # Draw rectangle + label
                cv2.putText(frame, roll_no, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

        cv2.imshow("Face Recognition Attendance", frame)

        # Exit with 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_recognition()
