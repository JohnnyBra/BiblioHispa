import sqlite3
import os
# Assuming utils.py is in the parent directory (classroom_library_app/)
from ..utils import get_data_path

DB_NAME = "library.db"
DB_DIR = "database" # This is the name of the folder *within* the app data structure
DB_PATH_FOR_CODE = os.path.join(DB_DIR, DB_NAME) # e.g., "database/library.db"

def init_db():
    """Initializes the database and creates the books table if it doesn't exist."""
    try:
        # get_data_path will handle making this correct for dev vs bundle
        # DB_PATH_FOR_CODE is "database/library.db"
        # get_data_path("database/library.db") will give:
        # DEV: classroom_library_app/database/library.db
        # BUNDLE: MEIPASS/database/library.db
        actual_db_path = get_data_path(DB_PATH_FOR_CODE)

        # Ensure the directory exists, especially for development if running init_db() standalone
        os.makedirs(os.path.dirname(actual_db_path), exist_ok=True)

        conn = sqlite3.connect(actual_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                classroom TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                borrower_id TEXT,
                due_date TEXT,
                image_path TEXT
            )
        """)

        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                classroom TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student', 'leader'))
            )
        """)

        conn.commit()
        print("Database initialized successfully. Books and Students tables are ready.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This allows running db_setup.py directly to initialize the DB for testing
    # Note: Running this directly might have path issues for get_data_path
    # if utils.py is not found due to relative import. Better to test via main.py or dedicated test script.
    # init_db()
    pass
