import sqlite3
import uuid

DB_PATH = 'database/library.db' # Using the same database file

def generate_student_id():
    """Generates a unique ID for a student."""
    return str(uuid.uuid4())

def add_student_db(name, classroom, role='student'):
    """Adds a new student to the database.
    Returns the new student's ID or None on failure."""
    student_id = generate_student_id()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (id, name, classroom, role)
            VALUES (?, ?, ?, ?)
        """, (student_id, name, classroom, role))
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
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        return dict(student) if student else None
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
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM students"
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
    s1_id = add_student_db("Alice Wonderland", "Class A", "leader")
    s2_id = add_student_db("Bob The Builder", "Class A", "student")
    s3_id = add_student_db("Charlie Brown", "Class B", "student")
    s4_id = add_student_db("Diana Prince", "Class B", "leader")
    s5_id = add_student_db("Edward Scissorhands", "Class A", "student")

    print(f"Added Alice (Leader, Class A): {s1_id}")
    print(f"Added Bob (Student, Class A): {s2_id}")
    print(f"Added Charlie (Student, Class B): {s3_id}")
    print(f"Added Diana (Leader, Class B): {s4_id}")
    print(f"Added Edward (Student, Class A): {s5_id}")

    # Test getting a student by ID
    print("\nFetching Alice by ID:")
    alice = get_student_by_id_db(s1_id)
    print(alice if alice else "Alice not found.")

    print("\nFetching non-existent student:")
    no_student = get_student_by_id_db("fake-id")
    print(no_student if no_student else "Fake student not found as expected.")

    # Test getting all students
    print("\nAll Students:")
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

    # Test filtering by classroom and role
    print("\nLeaders in Class B:")
    class_b_leaders = get_students_db(classroom_filter="Class B", role_filter="leader")
    for s in class_b_leaders: print(f"  {s['name']}")

    # Test is_student_leader
    print(f"\nIs Alice a leader? {is_student_leader(s1_id)}")       # Expected: True
    print(f"Is Bob a leader? {is_student_leader(s2_id)}")         # Expected: False
    print(f"Is non-existent student a leader? {is_student_leader('fake-id')}") # Expected: False
    print(f"Is student with None ID a leader? {is_student_leader(None)}") # Expected: False
