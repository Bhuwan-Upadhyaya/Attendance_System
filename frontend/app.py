from flask import Flask, render_template, send_file
import sqlite3
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "../data/attendance.db")
EXPORTS_DIR = os.path.join(BASE_DIR, "../logs")
os.makedirs(EXPORTS_DIR, exist_ok=True)


# ---------- Home ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- Dashboard (today’s attendance) ----------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT student_id, name, status, timestamp
        FROM attendance
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        """,
        conn
    )
    conn.close()
    return render_template("dashboard.html", records=df.to_dict(orient="records"))


# ---------- Alerts (unverified faces) ----------
@app.route("/alerts")
def alerts():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT id, image_path, detected_time
        FROM unverified_faces
        WHERE resolved = 0
        """,
        conn
    )
    conn.close()
    return render_template("alerts.html", alerts=df.to_dict(orient="records"))


# ---------- Download CSV (all attendance records) ----------
@app.route("/download_csv")
def download_csv():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    conn.close()

    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path = os.path.join(EXPORTS_DIR, filename)
    df.to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
