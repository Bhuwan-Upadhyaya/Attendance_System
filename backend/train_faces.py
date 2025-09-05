import cv2 as cv
import os
import numpy as np
import json

# Paths
project_root = os.path.dirname(os.path.abspath(__file__))  # backend folder
data_dir = os.path.join(project_root, "../data/faces/train")
model_dir = os.path.join(project_root, "../data/models")
os.makedirs(model_dir, exist_ok=True)

# Prepare training data
faces = []
labels = []

student_folders = os.listdir(data_dir)
student_folders.sort()  # consistent mapping
student_id_map = {name: idx for idx, name in enumerate(student_folders)}

for student_name, student_id in student_id_map.items():
    student_path = os.path.join(data_dir, student_name)
    for file_name in os.listdir(student_path):
        if file_name.endswith(".jpg"):
            img_path = os.path.join(student_path, file_name)
            img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)
            if img is None:
                continue
            faces.append(img)
            labels.append(student_id)

faces = np.array(faces)
labels = np.array(labels)

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

print(f"Training complete! Model saved at {model_path}")
print(f"Student mapping saved at {mapping_path}")



"""
Goal ::
1) read all images in data/faces/train/
2) assign numeric IDs per student
3) Train LBPH face recognizer


       and after doing this we will save to :
           Model: data/models/face_recognizer.yml
           Student mapping: data/models/student_id_map.json
"""