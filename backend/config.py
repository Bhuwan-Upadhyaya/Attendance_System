# Configuration settings for the attendance system

# Camera settings
CAMERA_INDEX = 0  # Try 1 if camera doesn't work
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Face detection parameters
FACE_DETECTION_SCALE_FACTOR = 1.3
FACE_DETECTION_MIN_NEIGHBORS = 5

# Face recognition settings
CONFIDENCE_THRESHOLD = 60  # Lower = stricter matching
FACE_SIZE_WIDTH = 200
FACE_SIZE_HEIGHT = 200

# File paths
DATASET_PATH = "data/faces/train"
MODEL_PATH = "data/models/face_recognizer.yml"
STUDENT_MAP_PATH = "data/models/student_id_map.json"
DATABASE_PATH = "attendance.db"

# Session settings
DEFAULT_SESSION = "Morning"
SESSIONS = ["Morning", "Afternoon", "Evening"]

# Attendance settings
ALLOW_DUPLICATE_ATTENDANCE = False  # Prevent multiple entries per student per session
ATTENDANCE_STATUS_PRESENT = "Present"
ATTENDANCE_STATUS_ABSENT = "Absent"

# Web interface settings
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/attendance.log"
