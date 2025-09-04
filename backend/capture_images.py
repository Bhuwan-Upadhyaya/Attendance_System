import cv2 as cv
import os

# Ask user for student number
student_number = input("Enter student number: ")
student_name = f"Student_{student_number}"

# Build absolute save directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
save_dir = os.path.join(project_root, "data", "faces", "train", student_name)

os.makedirs(save_dir, exist_ok=True)

cap = cv.VideoCapture(0)
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

    cv.imshow("Capturing Faces", frame)

    key = cv.waitKey(20) & 0xFF

    if key == ord('c'):  # Capture face when 'c' is pressed
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            count += 1
            file_path = os.path.join(save_dir, f"{student_name}_{count}.jpg")
            cv.imwrite(file_path, face_roi)
            print(f"Captured image {count} for {student_name}")
    elif key == ord('q') or count >= 20:  # Quit when 'q' pressed or 20 images
        break

cap.release()
cv.destroyAllWindows()
print(f"Saved {count} images for {student_name} in {save_dir}")
