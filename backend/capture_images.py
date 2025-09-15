import os
import sys
import cv2 as cv
import logging

# Ensure project root on sys.path for consistent paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import LOG_FILE, LOG_LEVEL, CAMERA_INDEX
from backend.utils import add_student

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

# Ask user for student info
print("Enter new student details to capture training images")
student_name = input("Full name: ").strip()
roll_no = input("Roll number: ").strip()

if not student_name or not roll_no:
    logging.error("Student name or roll number not provided")
    print("Name and roll number are required. Exiting.")
    exit()

# Upsert student in DB
try:
    student_id = add_student(student_name, roll_no)
    logging.info(f"Starting image capture for {student_name} (roll: {roll_no}, id: {student_id})")
except Exception as e:
    logging.error(f"Failed to upsert student before capture: {str(e)}")
    print(f"Failed to add/find student in DB: {e}")
    exit()

# Save under folder named by roll number to match training/recognition mapping
save_dir = os.path.join(PROJECT_ROOT, "data", "faces", "train", roll_no)
os.makedirs(save_dir, exist_ok=True)
logging.info(f"Created directory: {save_dir}")

# Camera & Haar cascade
cap = cv.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    logging.error(f"Failed to open camera with index {CAMERA_INDEX}")
    print(f"Failed to open camera with index {CAMERA_INDEX}")
    exit()

logging.info(f"Camera opened successfully with index {CAMERA_INDEX}")
haar_cascade = cv.CascadeClassifier(cv.data.haarcascades + "haarcascade_frontalface_default.xml")

count = 0
print("Press 'c' to capture an image, 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    for (x, y, w, h) in faces:
        cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv.putText(frame, f"Images: {count}/20", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv.imshow("Capturing Faces", frame)

    key = cv.waitKey(20) & 0xFF


    if key == ord('c'):  # Capture face when 'c' is pressed
        if len(faces) == 0:
            logging.warning("No face detected when trying to capture")
            print("No face detected. Try again.")
            continue
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv.resize(face_roi, (200, 200))  # normalize size
            count += 1
            file_path = os.path.join(save_dir, f"{roll_no}_{count}.jpg")
            cv.imwrite(file_path, face_roi)
            logging.info(f"Captured image {count} for {student_name} ({roll_no}): {file_path}")
            print(f" Captured image {count} for {student_name} ({roll_no})")
    elif key == ord('q') or count >= 20:  # Quit when 'q' pressed or 20 images reached
        logging.info(f"Image capture session ended. Total images captured: {count}")
        break

cap.release()
cv.destroyAllWindows()
logging.info(f"Image capture completed for {student_name} ({roll_no}). Saved {count} images in {save_dir}")
print(f"Saved {count} images for {student_name} ({roll_no}) in {save_dir}")
print("Next step: run training to update the model → python backend/train_faces.py")
