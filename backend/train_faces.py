import os
import sys
import cv2 as cv
import numpy as np
import json
import logging

# Ensure project root on sys.path when invoked directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import LOG_FILE, LOG_LEVEL, MODEL_PATH, STUDENT_MAP_PATH

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

project_root = CURRENT_DIR  # backend folder
data_dir = os.path.join(PROJECT_ROOT, "data", "faces", "train")
model_dir = os.path.join(PROJECT_ROOT, "data", "models")
os.makedirs(model_dir, exist_ok=True)

# Training data containers
faces = []
labels = []

# Only include folders (skip files like .DS_Store)
student_folders = [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]
student_folders.sort()  # consistent mapping
student_id_map = {name: idx for idx, name in enumerate(student_folders)}

logging.info(f"Students found for training: {student_id_map}")
print(" Students found for training:", student_id_map)

# Collect faces & labels
total_images = 0
for student_name, student_id in student_id_map.items():
    student_path = os.path.join(data_dir, student_name)
    student_images = 0
    for file_name in os.listdir(student_path):
        if file_name.endswith(".jpg"):
            img_path = os.path.join(student_path, file_name)
            img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)
            if img is None:
                logging.warning(f"Skipping unreadable image: {img_path}")
                print(f" Skipping unreadable image: {img_path}")
                continue

            # Ensure consistent size
            img = cv.resize(img, (200, 200))

            faces.append(img)
            labels.append(student_id)
            student_images += 1
            total_images += 1
    
    logging.info(f"Loaded {student_images} images for {student_name}")

# Convert to numpy arrays
faces = np.array(faces, dtype="uint8")  # uint8 = required for OpenCV
labels = np.array(labels)

logging.info(f"Collected {len(faces)} face images for training")
print(f" Collected {len(faces)} face images for training.")

# Train recognizer
logging.info("Starting face recognizer training...")
face_recognizer = cv.face.LBPHFaceRecognizer_create()
face_recognizer.train(faces, labels)
logging.info("Face recognizer training completed")

# Save model
face_recognizer.save(MODEL_PATH)
logging.info(f"Model saved to {MODEL_PATH}")

# Save student mapping
with open(STUDENT_MAP_PATH, "w") as f:
    json.dump(student_id_map, f)
logging.info(f"Student mapping saved to {STUDENT_MAP_PATH}")

logging.info("Training process completed successfully")
print(f" Training complete! Model saved at {MODEL_PATH}")
print(f"Student mapping saved at {STUDENT_MAP_PATH}")
