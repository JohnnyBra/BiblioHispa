# auth_manager.py

from . import student_manager # Use . to indicate relative import within the package

# Session Management Variables
current_user_id = None
current_user_role = None

def login(username, password):
    """
    Logs in a user (student) by their username (name) and password.
    Note: This function assumes 'name' from the students table is used as the username.
    If multiple students share the same name, the first one found will be used for login.
    For robust authentication, unique usernames are recommended.
    """
    global current_user_id, current_user_role

    # Fetch all students. In a larger system, fetching only the user by username would be more efficient.
    all_students = student_manager.get_students_db()
    if not all_students:
        return False

    for student in all_students:
        # Assuming 'name' is used as the username field
        if student['name'] == username:
            stored_hashed_password = student.get('hashed_password')
            stored_salt = student.get('salt')

            if not stored_hashed_password or not stored_salt:
                # This student does not have password information set up, cannot log in
                print(f"Warning: Student {username} does not have password/salt set.")
                continue # Check next student if multiple have same name

            if student_manager.verify_password(stored_hashed_password, stored_salt, password):
                current_user_id = student['id']
                current_user_role = student['role']
                return True
            else:
                # Password incorrect for this user
                return False # Username found, but password mismatch

    # User not found
    return False

def logout():
    """Logs out the current user by resetting session variables."""
    global current_user_id, current_user_role
    current_user_id = None
    current_user_role = None

def get_current_user_id():
    """Returns the ID of the currently logged-in user."""
    return current_user_id

def get_current_user_role():
    """Returns the role of the currently logged-in user."""
    return current_user_role

def is_user_logged_in():
    """Checks if a user is currently logged in."""
    return current_user_id is not None

def is_admin():
    """Checks if the currently logged-in user has an 'admin' role."""
    return current_user_role == 'admin'

if __name__ == '__main__':
    # This section is for basic testing of auth_manager.
    # It requires student_manager and a database with students.
    # Ensure db_setup.py has been run and you have added students with passwords.

    print("Testing Auth Manager...")

    # Attempt to add a test admin user if not present (requires DB setup and student_manager)
    # This is a simplified setup for testing.
    # In a real app, user creation would be more robust.
    try:
        print("\nAttempting to ensure test users exist...")
        # Check if db_setup needs to be run (if db file doesn't exist or is empty)
        # This is tricky to do perfectly without more context on project structure & execution path.
        # For now, we assume student_manager.py can be run to populate some data if its __main__ is invoked.

        admin_id = student_manager.add_student_db("TestAdmin", "AdminOffice", "adminpass", "admin")
        student_id = student_manager.add_student_db("TestStudent", "ClassA", "studentpass", "student")

        if admin_id:
            print(f"TestAdmin user ensured/created with ID: {admin_id}")
        else:
            # Attempt to find existing TestAdmin if add failed (e.g. unique constraint on name if names were unique)
            # For this test, we'll just note if add failed.
            print("Could not add TestAdmin. It might already exist or there's a DB issue.")
            # Try to fetch existing admin to continue tests
            admins = student_manager.get_students_db(role_filter="admin")
            test_admin_exists = any(s['name'] == "TestAdmin" for s in admins)
            if not test_admin_exists:
                 print("Failed to create or find TestAdmin. Login tests for admin might fail.")


        if student_id:
            print(f"TestStudent user ensured/created with ID: {student_id}")
        else:
            print("Could not add TestStudent. It might already exist or there's a DB issue.")
            students = student_manager.get_students_db(role_filter="student")
            test_student_exists = any(s['name'] == "TestStudent" for s in students)
            if not test_student_exists:
                 print("Failed to create or find TestStudent. Login tests for student might fail.")


    except Exception as e:
        print(f"Error during test user setup: {e}")
        print("Please ensure database is initialized and student_manager is functional.")

    # Test login
    print("\nTesting login...")
    login_success_admin = login("TestAdmin", "adminpass")
    print(f"Admin login with correct password ('TestAdmin', 'adminpass'): {login_success_admin}") # Expected: True

    if login_success_admin:
        print(f"Current User ID: {get_current_user_id()}")
        print(f"Current User Role: {get_current_user_role()}")
        print(f"Is user logged in? {is_user_logged_in()}") # Expected: True
        print(f"Is user admin? {is_admin()}") # Expected: True
        logout()
        print(f"After logout, is user logged in? {is_user_logged_in()}") # Expected: False
        print(f"After logout, current user role: {get_current_user_role()}") # Expected: None

    login_fail_wrong_pass = login("TestAdmin", "wrongpass")
    print(f"Admin login with incorrect password ('TestAdmin', 'wrongpass'): {login_fail_wrong_pass}") # Expected: False

    login_fail_no_user = login("NoSuchUser", "anypass")
    print(f"Login with non-existent user ('NoSuchUser', 'anypass'): {login_fail_no_user}") # Expected: False

    login_success_student = login("TestStudent", "studentpass")
    print(f"Student login with correct password ('TestStudent', 'studentpass'): {login_success_student}") # Expected: True

    if login_success_student:
        print(f"Current User ID: {get_current_user_id()}")
        print(f"Current User Role: {get_current_user_role()}")
        print(f"Is user logged in? {is_user_logged_in()}") # Expected: True
        print(f"Is user admin? {is_admin()}") # Expected: False
        logout()

    print("\nTesting with a user that might not have password fields (if any added manually without password):")
    # To test this properly, you'd need a student in DB without hashed_password/salt,
    # or modify an existing one.
    # For now, this is a placeholder for that test concept.
    # Example: student_manager.add_student_db("NoPassUser", "ClassZ", role="student") # but add_student_db now requires password
    # So, this case is less likely with current student_manager.py unless DB is manually altered.
    # We can simulate by trying to log in as a user that might exist from previous runs but no password.

    # Assuming a user "OldUser" might exist from previous tests before password logic was added
    # This part of the test is speculative without knowing the exact state of the DB over time.
    # If student_manager.py's main was run before password fields, such users might exist.
    # However, db_setup.py would ensure the columns exist.

    print("Login attempt for 'Alice Wonderland' (password 'password123' - from student_manager tests):")
    # This relies on student_manager.py's test data if its __main__ was run
    alice_login_test = login("Alice Wonderland", "password123")
    print(f"Login for Alice: {alice_login_test}")
    if alice_login_test:
        print(f"Alice role: {get_current_user_role()}")
        logout()

    print("\nAuth Manager tests finished.")
