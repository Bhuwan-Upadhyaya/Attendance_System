i am creating this attendaance system in a school project 
the following is the curent structure of the project folder and i may make some changes while 
building this project or if i get some new ideas on the way to build this project


attendance_system/
│
├── backend/
│   ├── __init__.py
│   ├── capture_image.py          # Capture sample images for 20 students
│   ├── database.py               # SQLite connection and attendance tables
│   ├── models.py                 # ORM models for students, attendance, etc.
│   ├── face_recognition.py       # OpenCV Haar cascade logic + real-time capture
│   ├── utils.py                  # Helper functions (time, validation, alerts)
│   ├── config.py                 # Configs: paths, thresholds, camera index, etc.
│   └── train_faces.py            # Train recognizer and save model
│
├── frontend/
│   ├── templates/                # HTML templates for Flask
│   │   ├── index.html            # Home / navigation page
│   │   ├── dashboard.html        # Real-time attendance + download CSV
│   │   └── alerts.html           # List of unverified faces
│   │
│   ├── static/                   # CSS, JS, Images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── app.py                    # Flask app entry point
│   └── dashboard.py              # (Optional) Separate routes/logic for dashboard
│
├── data/
│   ├── faces/train/              # Training images per student
│   │   ├── Student_1/
│   │   ├── Student_2/
│   │   └── ...
│   ├── faces/test/               # Optional test images
│   └── models/                   # Saved recognizer models (.yml + json)
│
├── logs/
│   ├── attendance_logs.txt       # Optional logs for events
│   └── attendance_exports/       # Exported CSV files (timestamped)
│
├── requirements.txt              # Python dependencies (opencv, flask, sqlite3, pandas, etc.)
└── README.txt                     # Project overview + setup instructions



At this point i have decided to work on the project by working on the following logics::


backend/

1)database.py -->Connects to SQLite and creates tables like Students, Attendance.
2)models.py --> Defines the schema (Student ID, Name, Attendance records, timestamps).
                face_recognition.py -->Your real-time webcam recognition code.
                Marks attendance in DB when a student is recognized.
3)Sends alert if unknown face detected.
4)utils.py -->Time functions, validation, alerts, helper functions.
5)config.py -->All paths, camera indices, thresholds (confidence threshold).
6)train_faces.py -->Your training script to create/update the recognizer.


frontend/ 
1)app.py --> Flask (or Django) backend for web dashboard.
            Views: Dashboard, Attendance logs, Alerts.
2)templates/ --> HTML templates for pages.
3)static/ --> CSS/JS/images.
4)dashboard.py --> Functions for fetching attendance from SQLite and displaying.


data/

1)faces/train/ → Images for each student folder (used for training).
2)faces/test/ → Optional test images.
3)models/ → Saved LBPH recognizer .yml files.



IMPORTANT NOTES:
I)Attendance logic:
       Each class has two timeframes: start and end.
       During the timeframe, the face_recognition.py script runs and updates the DB.
       If a student is not recognized during a period → marked absent.



II)Alert system:

Unknown faces  :notify instructor (popup or dashboard alert).
               Instructor can approve/reject manually.



III)Frontend:
        Shows real-time camera feed (optional).
        Displays attendance status.
        Option to download CSV from SQLite.