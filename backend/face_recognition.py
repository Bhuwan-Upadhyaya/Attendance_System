import os
import sys
import cv2
import numpy as np
import logging
import json
from datetime import datetime

# Ensure project root for backend-relative imports when run directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.utils import mark_attendance
from backend.database import get_connection
from backend.config import (
    LOG_FILE, LOG_LEVEL, CONFIDENCE_THRESHOLD, 
    FACE_SIZE_WIDTH, FACE_SIZE_HEIGHT, MODEL_PATH, STUDENT_MAP_PATH
)

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

# Load student mapping
student_id_map = {}
if os.path.exists(STUDENT_MAP_PATH):
    with open(STUDENT_MAP_PATH, 'r') as f:
        student_id_map = json.load(f)
    # Create reverse mapping (label -> student_name)
    label_to_name = {v: k for k, v in student_id_map.items()}
    logging.info(f"Loaded student mapping: {len(student_id_map)} students")
else:
    logging.error(f"Student mapping file not found: {STUDENT_MAP_PATH}")
    exit()

# Load Haar Cascade
haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Load trained recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
if os.path.exists(MODEL_PATH):
    recognizer.read(MODEL_PATH)
    logging.info(f"Loaded face recognizer model from {MODEL_PATH}")
else:
    logging.error(f"No trained model found at {MODEL_PATH}! Run train_faces.py first.")
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
    logging.info(f"Starting face recognition for {session} session")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Failed to open camera")
        return
    
    logging.info("Camera opened successfully")
    recognized_students = set()  # Track already recognized students this session

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Failed to read frame from camera")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = haar_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            # Normalize face size to match training
            roi_gray = cv2.resize(roi_gray, (FACE_SIZE_WIDTH, FACE_SIZE_HEIGHT))

            # Predict with recognizer
            label, confidence = recognizer.predict(roi_gray)

            if confidence < CONFIDENCE_THRESHOLD:
                # Use proper mapping from training
                student_name = label_to_name.get(label, f"Unknown_Label_{label}")
                student_id = get_student_id_from_roll(student_name)

                if student_id:
                    # Check if already recognized this session
                    if student_name not in recognized_students:
                        mark_attendance(student_id, status="Present", session=session)
                        recognized_students.add(student_name)
                        logging.info(f"Student {student_name} (ID: {student_id}) recognized with confidence {confidence:.1f}")
                    else:
                        logging.debug(f"Student {student_name} already recognized this session")
                else:
                    logging.warning(f"Student {student_name} not found in database")

                # Draw rectangle + label
                cv2.putText(frame, student_name, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            else:
                logging.debug(f"Unknown face detected with confidence {confidence:.1f}")
                cv2.putText(frame, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

        cv2.imshow("Face Recognition Attendance", frame)

        # Exit with 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            logging.info("Face recognition stopped by user")
            break

    cap.release()
    cv2.destroyAllWindows()
    logging.info(f"Face recognition session ended. Recognized {len(recognized_students)} students")

if __name__ == "__main__":
    start_recognition()
