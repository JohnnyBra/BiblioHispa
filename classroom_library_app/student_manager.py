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
    """Adds a new student to the database.
    If password is provided, it's hashed. Otherwise, salt and hash are stored as None.
    Returns the new student's ID or None on failure."""
    student_id = generate_student_id()

    if password: # Check if password is not None and not an empty string
        salt_hex, hashed_password_hex = hash_password(password)
    else:
        salt_hex, hashed_password_hex = None, None

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
        cursor.execute("SELECT id, name, classroom, role, points, hashed_password, salt FROM students WHERE id = ?", (student_id,)) # Added 'points'
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

        query = "SELECT id, name, classroom, role, points, hashed_password, salt FROM students" # Added 'points'
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

def get_students_sorted_by_points(classroom_filter=None):
    conn = None
    students_list = []
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Use row_factory for dictionary-like row access
        cursor = conn.cursor()

        query = "SELECT id, name, points, classroom FROM students"
        params = []

        # Check against display values used in UI for "Global"
        if classroom_filter and classroom_filter.lower() != "global" and classroom_filter.lower() != "🏆 global":
            query += " WHERE classroom = ?"
            params.append(classroom_filter)

        query += " ORDER BY points DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        for row in rows:
            # sqlite3.Row objects can be directly converted to dicts
            students_list.append(dict(row))

        return students_list

    except sqlite3.Error as e:
        print(f"Database error in get_students_sorted_by_points: {e}")
        return [] # Return empty list on error
    finally:
        if conn:
            conn.close()

def get_distinct_classrooms():
    conn = None
    classrooms = []
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        # conn.row_factory = sqlite3.Row # Not strictly necessary for single column fetch
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT classroom FROM students WHERE classroom IS NOT NULL AND classroom != '' ORDER BY classroom")
        rows = cursor.fetchall()
        classrooms = [row[0] for row in rows]
    except sqlite3.Error as e:
        print(f"Database error in get_distinct_classrooms: {e}")
    finally:
        if conn:
            conn.close()
    return classrooms

def rename_classroom(old_classroom_name, new_classroom_name):
    """
    Renames a classroom for all students in it.

    Args:
        old_classroom_name (str): The current name of the classroom.
        new_classroom_name (str): The new name for the classroom.

    Returns:
        bool: True if at least one student's classroom was updated, False otherwise.
    """
    if not new_classroom_name or not new_classroom_name.strip():
        print("Error: New classroom name cannot be empty or just whitespace.")
        return False
    if old_classroom_name == new_classroom_name:
        print("Info: Old and new classroom names are the same. No change made.")
        return False # Or True, depending on desired behavior for no-op

    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET classroom = ? WHERE classroom = ?",
                       (new_classroom_name.strip(), old_classroom_name))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Successfully renamed classroom '{old_classroom_name}' to '{new_classroom_name}' for {cursor.rowcount} students.")
            return True
        else:
            print(f"No students found in classroom '{old_classroom_name}'. No changes made.")
            return False
    except sqlite3.Error as e:
        print(f"Database error in rename_classroom: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- CSV Import Functionality ---
import csv
import io # For testing with StringIO

def import_students_from_csv(file_path, classroom_name):
    """
    Imports students from a CSV file.
    Each row in the CSV should contain: last_name, first_name
    Students are added with role='student' and no password.

    Args:
        file_path (str): The path to the CSV file.
        classroom_name (str): The classroom to assign to these students.

    Returns:
        tuple: (success_count, errors_list)
               success_count is the number of students successfully added.
               errors_list contains descriptions of errors encountered.
    """
    success_count = 0
    errors = []
    students_to_insert = []
    conn = None

    if not classroom_name or not classroom_name.strip():
        errors.append("Classroom name cannot be empty.")
        return 0, errors

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8-sig') as csvfile: # Added utf-8-sig
            csv_reader = csv.reader(csvfile)
            try:
                header = next(csv_reader, None) # Skip header row if it exists
            except StopIteration: # Handles empty file
                errors.append("El archivo CSV está vacío.")
                return 0, errors

            for row_num, row in enumerate(csv_reader, start=2 if header else 1): # Adjust start_num based on header
                try:
                    last_name_str = None
                    first_name_str = None

                    if not row:
                        errors.append(f"Fila {row_num}: Fila vacía.")
                        continue

                    if len(row) == 1:
                        content = row[0].strip()
                        parts = content.split(',', 1)
                        if len(parts) == 2:
                            last_name_str = parts[0].strip()
                            first_name_str = parts[1].strip()
                        else:
                            errors.append(f"Fila {row_num}: Dato malformado (campo único no contiene 'apellido,nombre'): '{row[0]}'")
                            continue
                    elif len(row) == 2:
                        last_name_str = row[0].strip()
                        first_name_str = row[1].strip()
                    else:
                        errors.append(f"Fila {row_num}: Dato malformado (se esperaban 1 o 2 campos, se obtuvieron {len(row)}): '{','.join(row)}'")
                        continue

                    if not last_name_str or not first_name_str:
                        errors.append(f"Fila {row_num}: Falta nombre o apellido después del análisis. Contenido original: '{','.join(row)}'")
                        continue

                    full_name = f"{first_name_str} {last_name_str}".strip()
                    if not full_name:
                        errors.append(f"Fila {row_num}: El nombre completo resultante está vacío. Contenido original: '{','.join(row)}'")
                        continue

                    # Generate student ID here, password fields will be None
                    student_id = generate_student_id()
                    students_to_insert.append((student_id, full_name, classroom_name.strip(), 'student', None, None))

                except IndexError:
                    errors.append(f"Fila {row_num}: Dato malformado (probablemente faltan campos). Contenido: '{','.join(row)}'")
                except Exception as e:
                    errors.append(f"Fila {row_num}: Ocurrió un error inesperado: {e}. Contenido: '{','.join(row)}'")

        if not students_to_insert:
            if not errors: # No students to insert and no errors means empty valid CSV or all rows skipped
                 errors.append("No se encontraron alumnos válidos para importar en el archivo CSV.")
            return 0, errors

        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION;")

        try:
            cursor.executemany("""
                INSERT INTO students (id, name, classroom, role, hashed_password, salt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, students_to_insert)
            conn.commit()
            success_count = len(students_to_insert)
        except sqlite3.Error as e:
            conn.rollback()
            errors.append(f"Error de base de datos durante la inserción en lote: {e}. No se importaron alumnos en este lote.")
            return 0, errors # Return 0 successful imports for this batch on DB error

    except FileNotFoundError:
        errors.append(f"Error: No se encontró el archivo '{file_path}'.")
    except Exception as e:
        errors.append(f"Ocurrió un error inesperado durante la importación del CSV: {e}")
        if conn: # If connection was established before this generic error
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return success_count, errors


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


    # Test adding student with no password
    s_no_pass_id = add_student_db("NoPass User", "Class C", None, "student")
    print(f"Added NoPass User (Student, Class C, no password): {s_no_pass_id}")
    if s_no_pass_id:
        no_pass_student = get_student_by_id_db(s_no_pass_id)
        if no_pass_student:
            print(f"  Fetched NoPass User: Name='{no_pass_student['name']}', Salt='{no_pass_student['salt']}', HashedPassword='{no_pass_student['hashed_password']}'")
            if no_pass_student['salt'] is None and no_pass_student['hashed_password'] is None:
                print("  SUCCESS: Salt and hashed_password are None as expected for NoPass User.")
            else:
                print("  FAILURE: Salt and/or hashed_password are NOT None for NoPass User.")
        else:
            print("  FAILURE: Could not fetch NoPass User to verify.")
    else:
        print("  FAILURE: Could not add NoPass User.")

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

    print("\n--- Testing CSV Import ---")

    # Create a dummy CSV for testing using io.StringIO
    csv_content_valid = "Doe,John\nSmith,Jane\nBond,James"
    csv_file_valid = io.StringIO(csv_content_valid)

    # Create a temporary file path for testing FileNotFoundError
    # This is a bit of a hack for testing; normally, you'd mock os.path.exists or similar
    # For this environment, we'll just use a non-existent path.
    non_existent_file_path = "temp_test_students_non_existent.csv"

    # Create a dummy CSV file on disk for more realistic testing
    temp_csv_file_path = "temp_test_students.csv"

    # Test case 1: Valid CSV import
    print("\nTest Case 1: Valid CSV")
    with open(temp_csv_file_path, 'w', newline='') as f:
        f.write("LastName,FirstName\n") # With header
        f.write("Doe,John\n")
        f.write("Smith,Jane\n")
        f.write("Bond,James\n")
        f.write("Skywalker, Luke\n") # Name with space

    success_count, errors = import_students_from_csv(temp_csv_file_path, "Test Class CSV 1")
    print(f"  Successfully imported: {success_count}")
    print(f"  Errors: {errors}")
    # Expected: 4 successes, 0 errors (or 3 if header isn't skipped, but it is now)
    # Let's verify by fetching these students
    if success_count > 0:
        csv_students = get_students_db(classroom_filter="Test Class CSV 1")
        print(f"  Students found in 'Test Class CSV 1': {len(csv_students)}")
        # for s in csv_students:
        #     if s['name'] in ["John Doe", "Jane Smith", "James Bond", "Luke Skywalker"]:
        #         print(f"    Found: {s['name']}, No-Pass: {s['hashed_password'] is None}")


    # Test case 2: Malformed CSV (missing fields, extra fields, empty names)
    print("\nTest Case 2: Malformed CSV")
    csv_content_malformed = (
        "SoloLastName\n"  # Missing first name
        "Mouse,Mickey,ExtraField\n" # Extra field (should still process first two)
        ",\n"             # Both empty
        "OnlyFirstName,\n" # Empty last name
        ",OnlyLastName\n"  # Empty first name
        "Good,Row\n"
    )
    with open(temp_csv_file_path, 'w', newline='') as f:
        f.write("HeaderLast,HeaderFirst\n") # With header
        f.write(csv_content_malformed)

    success_count, errors = import_students_from_csv(temp_csv_file_path, "Test Class CSV 2")
    print(f"  Successfully imported: {success_count}") # Expected: 1 (Mickey Mouse, Row Good)
    print(f"  Errors: {len(errors)} errors")
    for err in errors:
        print(f"    - {err}")
    # Expected errors for: SoloLastName, empty_row, OnlyFirstName, OnlyLastName.
    # "Mouse,Mickey,ExtraField" should succeed as "Mickey Mouse" (first two fields taken)
    # "Good,Row" should succeed.

    # Test case 3: File Not Found (already exists, good)
    print("\nTest Case 3: File Not Found")
    success_count, errors = import_students_from_csv(non_existent_file_path, "Test Class CSV 3")
    print(f"  Successfully imported: {success_count}") # Expected: 0
    print(f"  Errors: {errors}") # Expected: ["Error: The file '...' was not found."]

    # Test case 3b: New format CSV import - Relying on csv.reader's default unquoting
    print("\nTest Case 3b: New Format CSV (single and mixed fields, csv.reader handles quotes)")
    # When writing to a file that csv.reader will process:
    # - If you want a field to contain a comma, you must quote it: "Doe,John"
    # - If a field is already quoted in your source string, and you write it directly,
    #   it might result in double quoting if not handled carefully by the writer.
    #   However, here we are just creating the string content.
    #   The csv.reader will interpret "Doe,John" as a single field 'Doe,John'.
    #   It will interpret Doe,John (no quotes) as two fields 'Doe' and 'John'.
    csv_content_new_format = (
        'CombinedNameOrLastName,FirstNameIfSeparate\n'  # Header
        '"Doe,John"\n'                 # Parsed by csv.reader as ['Doe,John']
        '"Smith, Jane"\n'              # Parsed as ['Smith, Jane']
        '"O\'Malley,Sean"\n'           # Parsed as ["O'Malley,Sean"]
        'Regular,Entry\n'              # Parsed as ['Regular', 'Entry']
        'JustOneValueNoComma\n'        # Parsed as ['JustOneValueNoComma'] -> error in our logic
        '"JustOneValueInQuotes"\n'     # Parsed as ['JustOneValueInQuotes'] -> error in our logic
        '"Bond, James, ExtraPart"\n'   # Parsed as ['Bond, James, ExtraPart'] -> split logic takes 'Bond' and ' James, ExtraPart'
        ',""\n'                        # Parsed as ['', ''] -> error: last name empty
        'NoLastName,\n'                # Parsed as ['NoLastName', ''] -> error: first name empty
        '"",""\n'                      # Parsed as ['', ''] -> error: last name empty
        '" "," "\n'                    # Parsed as [' ', ' '] -> error: last name empty (after strip)
        '"OnlyLast," \n'               # Parsed as ['OnlyLast,'] -> split -> 'OnlyLast' and '' -> error: first name empty
        '",OnlyFirst"\n'               # Parsed as [',OnlyFirst'] -> split -> '' and 'OnlyFirst' -> error: last name empty
        'CompletelyEmptyRow\n'         # This line will be skipped by `if not row:` if csv.reader yields an empty list for it.
                                       # If it yields ['CompletelyEmptyRow'], it will be an error.
                                       # If it's truly an empty line in the file, csv.reader skips it by default.
        '  LeadingSpace,TrailingSpace  \n' # Parsed as ['  LeadingSpace', 'TrailingSpace  '] -> names will be stripped
    )
    with open(temp_csv_file_path, 'w', newline='') as f:
        f.write(csv_content_new_format)

    success_count, errors = import_students_from_csv(temp_csv_file_path, "Test Class CSV 3b")
    print(f"  Successfully imported: {success_count}")
    # Expected: John Doe, Jane Smith, Sean O'Malley, Entry Regular, James Bond (from "Bond, James, ExtraPart"), TrailingSpace LeadingSpace = 6
    print(f"  Errors: {len(errors)} errors")
    for err in errors:
        print(f"    - {err}")
    # Expected errors for:
    # JustOneValueNoComma (single field no comma)
    # "JustOneValueInQuotes" (single field no comma)
    # ,"" (empty last name)
    # NoLastName, (empty first name)
    # "","" (empty last name)
    # " "," " (empty last name)
    # "OnlyLast," (empty first name)
    # ",OnlyFirst" (empty last name)

    # Verify successful imports for 3b
    if success_count > 0:
        csv_students_3b = get_students_db(classroom_filter="Test Class CSV 3b")
        print(f"  Students found in 'Test Class CSV 3b': {len(csv_students_3b)}")
        expected_names_3b = ["John Doe", "Jane Smith", "Sean O'Malley", "Entry Regular", "James Bond", "TrailingSpace LeadingSpace"]
        imported_names_3b = sorted([s['name'] for s in csv_students_3b])
        print(f"  Imported names: {imported_names_3b}")
        for name in sorted(expected_names_3b):
            if name in imported_names_3b:
                print(f"    SUCCESS: Found '{name}'")
            else:
                print(f"    FAILURE: Did not find '{name}'")
        # Check count carefully
        if len(imported_names_3b) == len(expected_names_3b):
             print(f"    SUCCESS: Correct number of students imported ({len(expected_names_3b)}).")
        else:
             print(f"    FAILURE: Incorrect number of students imported. Expected {len(expected_names_3b)}, got {len(imported_names_3b)}.")


    # Test case 4: Empty classroom name (already exists, good)
    print("\nTest Case 4: Empty Classroom Name")
    with open(temp_csv_file_path, 'w', newline='') as f: # re-use valid content
        f.write("Doe,John\n")
    success_count, errors = import_students_from_csv(temp_csv_file_path, "  ") # Empty classroom
    print(f"  Successfully imported: {success_count}") # Expected: 0
    print(f"  Errors: {errors}") # Expected: ["Classroom name cannot be empty."]


    # Test case 5: CSV with only a header
    print("\nTest Case 5: CSV with only a header")
    with open(temp_csv_file_path, 'w', newline='') as f:
        f.write("Col1,Col2\n")
    success_count, errors = import_students_from_csv(temp_csv_file_path, "Test Class CSV 5")
    print(f"  Successfully imported: {success_count}") # Expected: 0
    print(f"  Errors: {errors}") # Expected: []

    # Test case 6: Empty CSV file
    print("\nTest Case 6: Empty CSV file")
    with open(temp_csv_file_path, 'w', newline='') as f:
        pass # Create empty file
    success_count, errors = import_students_from_csv(temp_csv_file_path, "Test Class CSV 6")
    print(f"  Successfully imported: {success_count}") # Expected: 0
    print(f"  Errors: {errors}") # Expected: [] (header skip handles this gracefully)


    # --- Test Classroom Renaming ---
    print("\n--- Testing Classroom Renaming ---")
    # Add some students to a test classroom
    rename_test_class_old = "RenameTestClassOld"
    rename_test_class_new = "RenameTestClassNew"
    add_student_db("Rename Student 1", rename_test_class_old, None)
    add_student_db("Rename Student 2", rename_test_class_old, None)
    add_student_db("Rename Student Other", "OtherClassUnchanged", None)

    print(f"Initial students in '{rename_test_class_old}':")
    for s in get_students_db(classroom_filter=rename_test_class_old):
        print(f"  - {s['name']}")

    # Test successful rename
    print(f"\nAttempting to rename '{rename_test_class_old}' to '{rename_test_class_new}'...")
    rename_success = rename_classroom(rename_test_class_old, rename_test_class_new)
    print(f"Rename operation success: {rename_success}") # Expected: True

    print(f"Students in '{rename_test_class_new}' after rename:")
    students_in_new = get_students_db(classroom_filter=rename_test_class_new)
    for s in students_in_new:
        print(f"  - {s['name']}")
    if len(students_in_new) == 2:
        print("  SUCCESS: Correct number of students in new class name.")
    else:
        print(f"  FAILURE: Incorrect number of students. Expected 2, got {len(students_in_new)}")

    print(f"Students in '{rename_test_class_old}' after rename (should be 0):")
    students_in_old_after_rename = get_students_db(classroom_filter=rename_test_class_old)
    if not students_in_old_after_rename:
        print("  SUCCESS: No students found in old class name.")
    else:
        print(f"  FAILURE: Found {len(students_in_old_after_rename)} students still in old class name.")


    # Test renaming non-existent class
    print("\nAttempting to rename a non-existent class ('NonExistentClassOld' to 'NonExistentClassNew')...")
    rename_non_existent_success = rename_classroom("NonExistentClassOld", "NonExistentClassNew")
    print(f"Rename non-existent class success: {rename_non_existent_success}") # Expected: False

    # Test renaming to empty/whitespace name
    print(f"\nAttempting to rename '{rename_test_class_new}' to an empty string...")
    rename_to_empty_success = rename_classroom(rename_test_class_new, "   ")
    print(f"Rename to empty string success: {rename_to_empty_success}") # Expected: False
    # Verify students are still in rename_test_class_new
    students_after_empty_attempt = get_students_db(classroom_filter=rename_test_class_new)
    if len(students_after_empty_attempt) == 2:
        print(f"  SUCCESS: Students correctly remained in '{rename_test_class_new}'.")
    else:
        print(f"  FAILURE: Student count in '{rename_test_class_new}' changed after attempting rename to empty.")


    # Clean up the temporary file
    try:
        os.remove(temp_csv_file_path)
        print(f"\nCleaned up temporary file: {temp_csv_file_path}")
    except OSError as e:
        print(f"\nError cleaning up temporary file {temp_csv_file_path}: {e}")
