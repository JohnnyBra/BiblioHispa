import sqlite3
import uuid
import hashlib
import os
from utils import get_data_path

# DB_PATH = 'database/library.db' # Using the same database file

# DB_PATH_FOR_CODE is the relative path string that get_data_path will use.
DB_PATH_FOR_CODE = os.path.join("database", "library.db")

def _get_resolved_db_path():
    # This helper ensures the database directory exists.
    path = get_data_path(DB_PATH_FOR_CODE)
    # Ensure the directory for the database exists, especially for development.
    # PyInstaller typically handles the creation of bundled directories.
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def generate_student_id():
    """Generates a unique ID for a student."""
    return str(uuid.uuid4())

def hash_password(password, salt=None):
    """Hashes the password with a salt.
    If salt is not provided, a new salt is generated.
    Returns salt (hex) and hashed_password (hex)."""
    if salt is None:
        salt = os.urandom(16) # Generate a new salt
    else:
        # If salt is provided (e.g., from storage), ensure it's bytes
        if isinstance(salt, str):
            salt = bytes.fromhex(salt)

    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex(), hashed_password.hex()

def verify_password(stored_hashed_password_hex, salt_hex, provided_password):
    """Verifies a provided password against a stored hash and salt."""
    if not stored_hashed_password_hex or not salt_hex:
        return False # Cannot verify if hash or salt is missing

    try:
        # Convert hex salt and stored_hashed_password back to bytes
        salt = bytes.fromhex(salt_hex)
        stored_hashed_password = bytes.fromhex(stored_hashed_password_hex)

        # Hash the provided password using the stored salt
        provided_password_hashed = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return provided_password_hashed == stored_hashed_password
    except (ValueError, TypeError): # Handle potential errors from hex conversion (e.g., non-hex string)
        return False

def add_student_db(name, classroom, password, role='student'):
    """Adds a new student to the database with a hashed password.
    Returns the new student's ID or None on failure."""
    student_id = generate_student_id()
    salt_hex, hashed_password_hex = hash_password(password)
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (id, name, classroom, role, hashed_password, salt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, name, classroom, role, hashed_password_hex, salt_hex))
        conn.commit()
        return student_id
    except sqlite3.Error as e:
        print(f"Database error in add_student_db: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_student_by_id_db(student_id):
    """Fetches a single student by their ID.
    Returns a dictionary representing the student, or None if not found."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, classroom, role, hashed_password, salt FROM students WHERE id = ?", (student_id,))
        student_row = cursor.fetchone()
        return dict(student_row) if student_row else None
    except sqlite3.Error as e:
        print(f"Database error in get_student_by_id_db: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_students_db(classroom_filter=None, role_filter=None):
    """Fetches a list of students, with optional filters for classroom and role.
    Returns a list of dictionaries."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT id, name, classroom, role, hashed_password, salt FROM students"
        filters = []
        params = []

        if classroom_filter and classroom_filter != "All":
            filters.append("classroom = ?")
            params.append(classroom_filter)

        if role_filter and role_filter != "All":
            filters.append("role = ?")
            params.append(role_filter)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
        students = [dict(row) for row in cursor.fetchall()]
        return students
    except sqlite3.Error as e:
        print(f"Database error in get_students_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_students_by_classroom_db(classroom):
    """Fetches students for a specific classroom.
    Returns a list of dictionaries."""
    if not classroom: # Avoid querying with an empty classroom value if "All" or similar is passed
        return get_students_db() # Or handle as an error/empty list
    return get_students_db(classroom_filter=classroom)

def delete_student_db(student_id):
    """Deletes a student from the database by their ID.
    Returns True on successful deletion, False otherwise."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cursor.rowcount > 0 # Check if any row was affected
    except sqlite3.Error as e:
        print(f"Database error in delete_student_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_student_password_db(student_id, new_password):
    """Updates a student's password in the database.
    A new salt is generated for the new password.
    Returns True on successful update, False otherwise."""
    new_salt_hex, new_hashed_password_hex = hash_password(new_password)
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students
            SET hashed_password = ?, salt = ?
            WHERE id = ?
        """, (new_hashed_password_hex, new_salt_hex, student_id))
        conn.commit()
        return cursor.rowcount > 0 # Check if any row was affected
    except sqlite3.Error as e:
        print(f"Database error in update_student_password_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_student_details_db(student_id, name, classroom, role):
    """Updates a student's name, classroom, and role in the database.
    Password and salt are not affected.
    Returns True on successful update, False otherwise."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students
            SET name = ?, classroom = ?, role = ?
            WHERE id = ?
        """, (name, classroom, role, student_id))
        conn.commit()
        return cursor.rowcount > 0 # True if at least one row was updated
    except sqlite3.Error as e:
        print(f"Database error in update_student_details_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def is_student_leader(student_id):
    """Checks if a student is a leader.
    Returns True if the student's role is 'leader', False otherwise.
    Handles non-existent student_id gracefully by returning False."""
    if not student_id:
        return False
    student = get_student_by_id_db(student_id)
    if student and student['role'] == 'leader':
        return True
    return False

if __name__ == '__main__':
    # This section is for testing purposes.
    # Ensure db_setup.py has been run or main.py to create tables.
    # from database.db_setup import init_db
    # init_db()

    print("Testing Student Management Functions...")

    # Test adding students
    # Note: The add_student_db function now requires a password.
    # For testing, we'll use simple passwords.
    s1_id = add_student_db("Alice Wonderland", "Class A", "password123", "leader")
    s2_id = add_student_db("Bob The Builder", "Class A", "bobspass", "student")
    s3_id = add_student_db("Charlie Brown", "Class B", "charliepass", "student")
    s4_id = add_student_db("Diana Prince", "Class B", "wonderpass", "leader")
    s5_id = add_student_db("Edward Scissorhands", "Class A", "edwardpass", "student")
    s6_id = add_student_db("Admin User", "AdminOffice", "adminpass", "admin")


    print(f"Added Alice (Leader, Class A): {s1_id}")
    print(f"Added Bob (Student, Class A): {s2_id}")
    print(f"Added Charlie (Student, Class B): {s3_id}")
    print(f"Added Diana (Leader, Class B): {s4_id}")
    print(f"Added Edward (Student, Class A): {s5_id}")
    print(f"Added Admin User (Admin, AdminOffice): {s6_id}")


    # Test getting a student by ID
    print("\nFetching Alice by ID:")
    alice = get_student_by_id_db(s1_id)
    if alice:
        print(f"  {alice['name']}, Role: {alice['role']}, Salt: {alice['salt'][:10]}...") # Don't print full salt/hash
    else:
        print("Alice not found.")

    # Test password verification
    print("\nTesting Password Verification for Alice:")
    if alice:
        is_correct = verify_password(alice['hashed_password'], alice['salt'], "password123")
        print(f"  Verification with correct password ('password123'): {is_correct}") # Expected: True
        is_correct = verify_password(alice['hashed_password'], alice['salt'], "wrongpassword")
        print(f"  Verification with incorrect password ('wrongpassword'): {is_correct}") # Expected: False

    # Test updating password
    print("\nUpdating Bob's password:")
    if s2_id:
        update_success = update_student_password_db(s2_id, "newbobpass")
        print(f"  Password update status for Bob: {update_success}") # Expected: True
        bob_updated = get_student_by_id_db(s2_id)
        if bob_updated:
            is_correct_new = verify_password(bob_updated['hashed_password'], bob_updated['salt'], "newbobpass")
            print(f"  Verification with new password ('newbobpass'): {is_correct_new}") # Expected: True
            is_correct_old = verify_password(bob_updated['hashed_password'], bob_updated['salt'], "bobspass")
            print(f"  Verification with old password ('bobspass'): {is_correct_old}") # Expected: False


    print("\nFetching non-existent student:")
    no_student = get_student_by_id_db("fake-id")
    print(no_student if no_student else "Fake student not found as expected.")

    # Test getting all students
    print("\nAll Students (name, role, classroom - no sensitive data shown here):")
    all_students = get_students_db()
    for s in all_students: print(f"  {s['name']} ({s['role']}) in {s['classroom']}")

    # Test filtering by classroom
    print("\nStudents in Class A:")
    class_a_students = get_students_by_classroom_db("Class A")
    for s in class_a_students: print(f"  {s['name']} ({s['role']})")

    # Test filtering by role
    print("\nAll Leaders:")
    leaders = get_students_db(role_filter="leader")
    for s in leaders: print(f"  {s['name']} in {s['classroom']}")

    print("\nAll Admins:")
    admins = get_students_db(role_filter="admin")
    for s in admins: print(f"  {s['name']} in {s['classroom']}")


    # Test filtering by classroom and role
    print("\nLeaders in Class B:")
    class_b_leaders = get_students_db(classroom_filter="Class B", role_filter="leader")
    for s in class_b_leaders: print(f"  {s['name']}")

    # Test is_student_leader
    print(f"\nIs Alice a leader? {is_student_leader(s1_id)}")       # Expected: True
    print(f"Is Bob a leader? {is_student_leader(s2_id)}")         # Expected: False
    print(f"Is non-existent student a leader? {is_student_leader('fake-id')}") # Expected: False
    print(f"Is student with None ID a leader? {is_student_leader(None)}") # Expected: False

    # Test deleting a student
    print(f"\nDeleting Edward (Student, Class A): {s5_id}")
    delete_success = delete_student_db(s5_id)
    print(f"  Deletion status for Edward: {delete_success}") # Expected: True
    edward_deleted = get_student_by_id_db(s5_id)
    print(f"  Searching for Edward after deletion: {'Not found' if not edward_deleted else 'Found (Error!)'}")

    print("\nAll Students after deletion:")
    all_students_after_delete = get_students_db()
    for s in all_students_after_delete: print(f"  {s['name']} ({s['role']}) in {s['classroom']}")

    # Test updating student details
    print("\nTesting update_student_details_db...")
    s7_id = add_student_db("Updateable User", "Class C", "updatepass", "student")
    if s7_id:
        print(f"Added Updateable User: {s7_id}")
        update_details_success = update_student_details_db(s7_id, "Updated User Name", "Class D", "leader")
        print(f"  Update details success: {update_details_success}") # Expected: True
        updated_s7 = get_student_by_id_db(s7_id)
        if updated_s7:
            print(f"  Fetched after update: Name='{updated_s7['name']}', Class='{updated_s7['classroom']}', Role='{updated_s7['role']}'")
            # Verify password hasn't changed (optional quick check, verify_password is more robust)
            original_pass_still_works = verify_password(updated_s7['hashed_password'], updated_s7['salt'], "updatepass")
            print(f"  Original password still works: {original_pass_still_works}") # Expected: True
        else:
            print("  Failed to fetch user after update.")
    else:
        print("Failed to add s7_id for update details test.")
