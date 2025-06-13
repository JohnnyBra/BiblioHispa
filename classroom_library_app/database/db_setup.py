import sqlite3
import os
import uuid
import hashlib
# Assuming utils.py is in the parent directory (classroom_library_app/)
from utils import get_data_path

DB_NAME = "library.db"
DB_DIR = "database" # This is the name of the folder *within* the app data structure
DB_PATH_FOR_CODE = os.path.join(DB_DIR, DB_NAME) # e.g., "database/library.db"

def _local_hash_password(password_str):
    """
    Hashes a password using PBKDF2-HMAC-SHA256 and a new salt.
    Returns salt (hex) and hashed_password (hex).
    This is a local utility to avoid circular dependency with student_manager.
    """
    salt_bytes = os.urandom(16)
    hashed_password_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password_str.encode('utf-8'),
        salt_bytes,
        100000  # Iteration count, should match what's used elsewhere (e.g., student_manager)
    )
    return salt_bytes.hex(), hashed_password_bytes.hex()

def init_db():
    """Initializes the database and creates the books table if it doesn't exist."""
    try:
        # get_data_path will handle making this correct for dev vs bundle
        # DB_PATH_FOR_CODE is "database/library.db"
        # get_data_path("database/library.db") will give:
        # DEV: classroom_library_app/database/library.db
        # BUNDLE: MEIPASS/database/library.db
        actual_db_path = get_data_path(DB_PATH_FOR_CODE)

        print("\n--- IMPORTANT ---")
        print("If you've run this application before with an older database structure,")
        print(f"you MIGHT need to delete the existing database file at '{actual_db_path}'")
        print("for schema changes (like new tables or columns) to apply correctly.")
        print("This is because tables are created with 'IF NOT EXISTS' and won't be altered if they already exist.")
        print("--- IMPORTANT ---\n")

        # Ensure the directory exists, especially for development if running init_db() standalone
        os.makedirs(os.path.dirname(actual_db_path), exist_ok=True)

        conn = sqlite3.connect(actual_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                genero TEXT,
                ubicacion TEXT NOT NULL,
                cantidad_total INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Create loans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                loan_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                classroom TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student', 'leader', 'admin')),
                hashed_password TEXT,
                salt TEXT
            )
        """)

        conn.commit()
        print("Database schema initialized successfully. Books and Students tables are ready.")

        # Add gamification columns with error handling for existing columns
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN points INTEGER DEFAULT 0;")
            conn.commit()
            print("Column 'points' added to 'students' table.")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"Column 'points' already exists in 'students'. Skipping.")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE loans ADD COLUMN worksheet_submitted INTEGER DEFAULT 0;")
            conn.commit()
            print("Column 'worksheet_submitted' added to 'loans' table.")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"Column 'worksheet_submitted' already exists in 'loans'. Skipping.")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE loans ADD COLUMN early_return_bonus_applied INTEGER DEFAULT 0;")
            conn.commit()
            print("Column 'early_return_bonus_applied' added to 'loans' table.")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"Column 'early_return_bonus_applied' already exists in 'loans'. Skipping.")
            else:
                raise

        # Check for and create the specific default admin user if it doesn't exist
        cursor.execute("SELECT id FROM students WHERE name = ? AND role = ?", ("admin", "admin"))
        existing_default_admin = cursor.fetchone()

        if existing_default_admin is None:
            # Default admin user "admin" not found, proceed to create it
            admin_id = str(uuid.uuid4())
            admin_name = "admin"
            admin_password = "adminpass" # Default password
            admin_classroom = "AdminOffice"

            salt_hex, hashed_password_hex = _local_hash_password(admin_password)

            try:
                cursor.execute("""
                    INSERT INTO students (id, name, classroom, role, hashed_password, salt)
                    VALUES (?, ?, ?, 'admin', ?, ?)
                """, (admin_id, admin_name, admin_classroom, hashed_password_hex, salt_hex))
                conn.commit()
                print(f"\nDefault admin user '{admin_name}' created.") # Added admin_name for clarity
                print(f"  Username: {admin_name}")
                print(f"  Password: {admin_password}")
                print("IMPORTANT: Change this default admin password immediately after first login via User Management tab.")
            except sqlite3.Error as e:
                print(f"Error creating default admin user '{admin_name}': {e}") # Added admin_name
        else:
            print(f"Default admin user 'admin' already exists. Skipping default admin creation.")

    except sqlite3.Error as e:
        print(f"Database error during init_db: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This allows running db_setup.py directly to initialize the DB for testing
    # Note: Running this directly might have path issues for get_data_path
    # if utils.py is not found due to relative import. Better to test via main.py or dedicated test script.
    # init_db()
    pass
