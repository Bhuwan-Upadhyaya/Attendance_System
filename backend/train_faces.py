import os
import cv2 as cv
import numpy as np
import json

# Paths
project_root = os.path.dirname(os.path.abspath(__file__))  # backend folder
data_dir = os.path.join(project_root, "../data/faces/train")
model_dir = os.path.join(project_root, "../data/models")
os.makedirs(model_dir, exist_ok=True)

# Training data containers
faces = []
labels = []

# Only include folders (skip files like .DS_Store)
student_folders = [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]
student_folders.sort()  # consistent mapping
student_id_map = {name: idx for idx, name in enumerate(student_folders)}

print("🔍 Students found for training:", student_id_map)

# Collect faces & labels
for student_name, student_id in student_id_map.items():
    student_path = os.path.join(data_dir, student_name)
    for file_name in os.listdir(student_path):
        if file_name.endswith(".jpg"):
            img_path = os.path.join(student_path, file_name)
            img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)
            if img is None:
                print(f"⚠️ Skipping unreadable image: {img_path}")
                continue

            # Ensure consistent size
            img = cv.resize(img, (200, 200))

            faces.append(img)
            labels.append(student_id)

# Convert to numpy arrays
faces = np.array(faces, dtype="uint8")  # uint8 = required for OpenCV
labels = np.array(labels)

print(f"✅ Collected {len(faces)} face images for training.")

# Train recognizer
face_recognizer = cv.face.LBPHFaceRecognizer_create()
face_recognizer.train(faces, labels)

# Save model
model_path = os.path.join(model_dir, "face_recognizer.yml")
face_recognizer.save(model_path)

# Save student mapping
mapping_path = os.path.join(model_dir, "student_id_map.json")
with open(mapping_path, "w") as f:
    json.dump(student_id_map, f)

print(f" Training complete! Model saved at {model_path}")
print(f"Student mapping saved at {mapping_path}")
