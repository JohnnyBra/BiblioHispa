# auth_manager.py

import student_manager # Use . to indicate relative import within the package

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
            # Check if user is 'student' and has no password set
            if student['role'] == 'student' and \
               (student.get('hashed_password') is None or student.get('hashed_password') == '') and \
               (student.get('salt') is None or student.get('salt') == ''):

                # For students with no password, allow login if provided password is also empty or None
                if password is None or password == '':
                    current_user_id = student['id']
                    current_user_role = student['role']
                    return True
                else:
                    # Student has no password set, but a password was provided by user
                    return False # Password mismatch (no password vs some password)

            # Existing logic for users with passwords (students, leaders, admins)
            stored_hashed_password = student.get('hashed_password')
            stored_salt = student.get('salt')

            # This check is important for users who *should* have a password
            # (e.g. leaders, admins, or students who had a password set)
            if not stored_hashed_password or not stored_salt:
                print(f"Warning: User {username} (role: {student['role']}) is missing password/salt information needed for login.")
                # If it's a student, this means they were expected to have a password but don't.
                # If it's an admin/leader, they MUST have a password.
                return False # Cannot log in without password info if it's expected.

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

    try:
        from database import db_setup
        print("Initializing DB for auth_manager tests (if needed)...")
        db_setup.init_db()
    except ImportError:
        print("Warning: Could not import db_setup to initialize database for tests.")
        print("         Please ensure classroom_library_app is in PYTHONPATH or run tests from project root.")
    except Exception as e_init:
        print(f"Error initializing DB for tests: {e_init}")

    test_admin_name = "TestAdminAuth"
    test_student_with_pass_name = "TestStudentWithPassAuth"
    test_student_no_pass_name = "TestStudentNoPassAuth"
    test_leader_name = "TestLeaderAuth"

    admin_id = None
    student_id_with_pass = None
    student_id_no_pass = None
    leader_id = None

    try:
        print("\nAttempting to ensure test users exist for auth_manager tests...")

        admin_id = student_manager.add_student_db(test_admin_name, "AdminOffice", "adminpass123", "admin")
        if admin_id:
            print(f"'{test_admin_name}' user ensured/created with ID: {admin_id}")
        else:
            print(f"Could not add '{test_admin_name}'. It might already exist or there's a DB issue.")

        student_id_with_pass = student_manager.add_student_db(test_student_with_pass_name, "ClassAuth", "studentpass123", "student")
        if student_id_with_pass:
            print(f"'{test_student_with_pass_name}' user ensured/created with ID: {student_id_with_pass}")
        else:
            print(f"Could not add '{test_student_with_pass_name}'. It might already exist.")

        student_id_no_pass = student_manager.add_student_db(test_student_no_pass_name, "ClassAuth", None, "student")
        if student_id_no_pass:
            print(f"'{test_student_no_pass_name}' user (no password) ensured/created with ID: {student_id_no_pass}")
        else:
            print(f"Could not add '{test_student_no_pass_name}'. It might already exist.")

        leader_id = student_manager.add_student_db(test_leader_name, "LeaderOffice", "leaderpass123", "leader")
        if leader_id:
            print(f"'{test_leader_name}' user ensured/created with ID: {leader_id}")
        else:
            print(f"Could not add '{test_leader_name}'. It might already exist.")

        if student_id_no_pass:
            fetched_no_pass_student = student_manager.get_student_by_id_db(student_id_no_pass)
            if fetched_no_pass_student:
                print(f"  Verification for '{test_student_no_pass_name}': "
                      f"Salt is '{fetched_no_pass_student.get('salt')}', "
                      f"Hash is '{fetched_no_pass_student.get('hashed_password')}' (expected None or empty for both)")
            else:
                print(f"  Could not fetch '{test_student_no_pass_name}' to verify salt/hash.")
        else:
            print(f"  Skipping verification for '{test_student_no_pass_name}' as it was not added successfully.")

    except Exception as e:
        print(f"Error during test user setup for auth_manager: {e}")
        print("Please ensure database is initialized and student_manager is functional.")

    print("\nTesting login scenarios...")

    if admin_id:
        login_success_admin = login(test_admin_name, "adminpass123")
        print(f"1. Admin login ('{test_admin_name}', 'adminpass123'): {login_success_admin} (Expected: True)")
        if login_success_admin: logout()

        login_fail_admin_wrong_pass = login(test_admin_name, "wrongpass")
        print(f"   Admin login ('{test_admin_name}', 'wrongpass'): {login_fail_admin_wrong_pass} (Expected: False)")
    else:
        print(f"Skipping admin login tests for '{test_admin_name}' as user was not added.")

    if student_id_with_pass:
        login_success_student_wp = login(test_student_with_pass_name, "studentpass123")
        print(f"2. Student with password ('{test_student_with_pass_name}', 'studentpass123'): {login_success_student_wp} (Expected: True)")
        if login_success_student_wp: logout()

        login_fail_student_wp_wrong_pass = login(test_student_with_pass_name, "wrongpass")
        print(f"   Student with password ('{test_student_with_pass_name}', 'wrongpass'): {login_fail_student_wp_wrong_pass} (Expected: False)")

        login_fail_student_wp_empty_pass = login(test_student_with_pass_name, "")
        print(f"   Student with password ('{test_student_with_pass_name}', ''): {login_fail_student_wp_empty_pass} (Expected: False)")
    else:
        print(f"Skipping student with password tests for '{test_student_with_pass_name}' as user was not added.")

    if student_id_no_pass:
        login_success_student_no_pass_empty = login(test_student_no_pass_name, "")
        print(f"3. Student without password ('{test_student_no_pass_name}', ''): {login_success_student_no_pass_empty} (Expected: True)")
        if login_success_student_no_pass_empty:
            logout()

        login_success_student_no_pass_none = login(test_student_no_pass_name, None)
        print(f"   Student without password ('{test_student_no_pass_name}', None): {login_success_student_no_pass_none} (Expected: True)")
        if login_success_student_no_pass_none: logout()

        login_fail_student_no_pass_with_pass = login(test_student_no_pass_name, "anypassword")
        print(f"   Student without password ('{test_student_no_pass_name}', 'anypassword'): {login_fail_student_no_pass_with_pass} (Expected: False)")
    else:
        print(f"Skipping student without password tests for '{test_student_no_pass_name}' as user was not added.")

    if leader_id:
        login_success_leader = login(test_leader_name, "leaderpass123")
        print(f"4. Leader login ('{test_leader_name}', 'leaderpass123'): {login_success_leader} (Expected: True)")
        if login_success_leader: logout()

        login_fail_leader_wrong_pass = login(test_leader_name, "wrongpass")
        print(f"   Leader login ('{test_leader_name}', 'wrongpass'): {login_fail_leader_wrong_pass} (Expected: False)")

        login_fail_leader_empty_pass = login(test_leader_name, "")
        print(f"   Leader login ('{test_leader_name}', ''): {login_fail_leader_empty_pass} (Expected: False)")
    else:
        print(f"Skipping leader login tests for '{test_leader_name}' as user was not added.")

    login_fail_no_user = login("NoSuchUserAuth", "anypass")
    print(f"5. Login with non-existent user ('NoSuchUserAuth', 'anypass'): {login_fail_no_user} (Expected: False)")

    print(f"\nAfter all login tests, is user logged in? {is_user_logged_in()} (Expected: False)")
    print(f"Current user ID: {get_current_user_id()} (Expected: None)")
    print(f"Current user role: {get_current_user_role()} (Expected: None)")

    print("\nLegacy Test: Login attempt for 'Alice Wonderland' (password 'password123' - from student_manager.py tests, if run):")
    alice_exists = False
    try:
        all_students_for_alice_check = student_manager.get_students_db()
        if any(s['name'] == "Alice Wonderland" for s in all_students_for_alice_check):
            alice_exists = True
    except Exception as e_alice_check:
        print(f"Could not check for Alice Wonderland due to: {e_alice_check}")

    if alice_exists:
        alice_login_test = login("Alice Wonderland", "password123")
        print(f"Login for Alice: {alice_login_test} (Expected: True if Alice was added with this password)")
        if alice_login_test:
            print(f"Alice role: {get_current_user_role()}")
            logout()

        alice_login_empty_pass_test = login("Alice Wonderland", "")
        print(f"Login for Alice with empty password: {alice_login_empty_pass_test} (Expected: False if Alice has a password)")
        if alice_login_empty_pass_test: logout()
    else:
        print("Alice Wonderland not found in DB or could not be checked, skipping her specific legacy tests.")

    print("\nAuth Manager tests finished.")
