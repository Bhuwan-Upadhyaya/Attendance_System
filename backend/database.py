
import sqlite3

DB_NAME = "attendance.db"

def get_connection():
    """Return a SQLite connection object."""
    conn = sqlite3.connect(DB_NAME)
    return conn
