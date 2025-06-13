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

    # Attempt to add a test admin user if not present (requires DB setup and student_manager)
    # This is a simplified setup for testing.
    # In a real app, user creation would be more robust.

    # Clean up previous test users to ensure a consistent test environment
    # This might not be strictly necessary if add_student_db handles duplicates gracefully or if names are unique.
    # However, for testing login, we want to be sure about the state of these users.
    # Note: Deleting requires student_id, which we get upon creation.
    # A better approach for testing might be to use a dedicated test database that's reset.
    # For now, we'll rely on adding them and assume add_student_db won't create exact duplicates if run multiple times
    # (or that it's okay for the test if it does, as login uses the first match).

    # Let's ensure classroom_library_app/database/library.db is initialized for tests
    # This is a bit of a hack for testing; ideally, test setup is more robust.
    try:
        from database import db_setup # Check if accessible
        # Attempt to initialize DB (creates tables if they don't exist, adds default admin)
        # Running init_db() multiple times is generally safe due to "IF NOT EXISTS"
        # and checks for default admin.
        print("Initializing DB for auth_manager tests (if needed)...")
        db_setup.init_db()
    except ImportError:
        print("Warning: Could not import db_setup to initialize database for tests.")
    except Exception as e_init:
        print(f"Error initializing DB for tests: {e_init}")


    try:
        print("\nAttempting to ensure test users exist for auth_manager tests...")

        # Admin user (should always require password)
        # The default "admin" user is created by db_setup.init_db() with password "adminpass"
        # We can rely on that or create a specific TestAdmin.
        # For consistency, let's try to add our TestAdmin.
        # If db_setup.init_db() already created "admin", that's fine.
        # Our login tests will use "TestAdmin".
        test_admin_name = "TestAdminAuth" # Using a unique name for this test
        admin_id = student_manager.add_student_db(test_admin_name, "AdminOffice", "adminpass123", "admin")
        if admin_id:
            print(f"'{test_admin_name}' user ensured/created with ID: {admin_id}")
        else:
            print(f"Could not add '{test_admin_name}'. It might already exist or there's a DB issue.")


        # Student with a password
        test_student_with_pass_name = "TestStudentWithPassAuth"
        student_id_with_pass = student_manager.add_student_db(test_student_with_pass_name, "ClassAuth", "studentpass123", "student")
        if student_id_with_pass:
            print(f"'{test_student_with_pass_name}' user ensured/created with ID: {student_id_with_pass}")
        else:
            print(f"Could not add '{test_student_with_pass_name}'. It might already exist.")

        # Student without a password
        test_student_no_pass_name = "TestStudentNoPassAuth"
        student_id_no_pass = student_manager.add_student_db(test_student_no_pass_name, "ClassAuth", None, "student")
        if student_id_no_pass:
            print(f"'{test_student_no_pass_name}' user (no password) ensured/created with ID: {student_id_no_pass}")
        else:
            print(f"Could not add '{test_student_no_pass_name}'. It might already exist.")

        # Leader with a password
        test_leader_name = "TestLeaderAuth"
        leader_id = student_manager.add_student_db(test_leader_name, "LeaderOffice", "leaderpass123", "leader")
        if leader_id:
            print(f"'{test_leader_name}' user ensured/created with ID: {leader_id}")
        else:
            print(f"Could not add '{test_leader_name}'. It might already exist.")


        # Verification: Fetch the student with no password to confirm salt/hash are None
        if student_id_no_pass:
            fetched_no_pass_student = student_manager.get_student_by_id_db(student_id_no_pass)
            if fetched_no_pass_student:
                print(f"  Verification for '{test_student_no_pass_name}': "
                      f"Salt is '{fetched_no_pass_student.get('salt')}', "
                      f"Hash is '{fetched_no_pass_student.get('hashed_password')}' (expected None or empty for both)")
            else:
                print(f"  Could not fetch '{test_student_no_pass_name}' to verify salt/hash.")


    except Exception as e:
        print(f"Error during test user setup for auth_manager: {e}")
        print("Please ensure database is initialized and student_manager is functional.")

    # Test login
    print("\nTesting login scenarios...")

    # 1. Admin login
    login_success_admin = login(test_admin_name, "adminpass123")
    print(f"1. Admin login ('{test_admin_name}', 'adminpass123'): {login_success_admin} (Expected: True)")
    if login_success_admin: logout()

    login_fail_admin_wrong_pass = login(test_admin_name, "wrongpass")
    print(f"   Admin login ('{test_admin_name}', 'wrongpass'): {login_fail_admin_wrong_pass} (Expected: False)")
    if login_fail_admin_wrong_pass: logout() # Should not happen

    # 2. Student with password
    login_success_student_wp = login(test_student_with_pass_name, "studentpass123")
    print(f"2. Student with password ('{test_student_with_pass_name}', 'studentpass123'): {login_success_student_wp} (Expected: True)")
    if login_success_student_wp: logout()

    login_fail_student_wp_wrong_pass = login(test_student_with_pass_name, "wrongpass")
    print(f"   Student with password ('{test_student_with_pass_name}', 'wrongpass'): {login_fail_student_wp_wrong_pass} (Expected: False)")
    if login_fail_student_wp_wrong_pass: logout()

    login_fail_student_wp_empty_pass = login(test_student_with_pass_name, "")
    print(f"   Student with password ('{test_student_with_pass_name}', ''): {login_fail_student_wp_empty_pass} (Expected: False)")
    if login_fail_student_wp_empty_pass: logout()

    # 3. Student without password
    login_success_student_no_pass_empty = login(test_student_no_pass_name, "")
    print(f"3. Student without password ('{test_student_no_pass_name}', ''): {login_success_student_no_pass_empty} (Expected: True)")
    if login_success_student_no_pass_empty:
        print(f"   Logged in as {get_current_user_role()} {student_manager.get_student_by_id_db(get_current_user_id())['name']}")
        logout()

    login_success_student_no_pass_none = login(test_student_no_pass_name, None)
    print(f"   Student without password ('{test_student_no_pass_name}', None): {login_success_student_no_pass_none} (Expected: True)")
    if login_success_student_no_pass_none: logout()

    login_fail_student_no_pass_with_pass = login(test_student_no_pass_name, "anypassword")
    print(f"   Student without password ('{test_student_no_pass_name}', 'anypassword'): {login_fail_student_no_pass_with_pass} (Expected: False)")
    if login_fail_student_no_pass_with_pass: logout()

    # 4. Leader login (should require password)
    login_success_leader = login(test_leader_name, "leaderpass123")
    print(f"4. Leader login ('{test_leader_name}', 'leaderpass123'): {login_success_leader} (Expected: True)")
    if login_success_leader: logout()

    login_fail_leader_wrong_pass = login(test_leader_name, "wrongpass")
    print(f"   Leader login ('{test_leader_name}', 'wrongpass'): {login_fail_leader_wrong_pass} (Expected: False)")
    if login_fail_leader_wrong_pass: logout()

    login_fail_leader_empty_pass = login(test_leader_name, "")
    print(f"   Leader login ('{test_leader_name}', ''): {login_fail_leader_empty_pass} (Expected: False)")
    if login_fail_leader_empty_pass: logout()

    # 5. Non-existent user
    login_fail_no_user = login("NoSuchUserAuth", "anypass")
    print(f"5. Login with non-existent user ('NoSuchUserAuth', 'anypass'): {login_fail_no_user} (Expected: False)")
    if login_fail_no_user: logout()

    # General checks after tests
    print(f"\nAfter all login tests, is user logged in? {is_user_logged_in()} (Expected: False)")
    print(f"Current user ID: {get_current_user_id()} (Expected: None)")
    print(f"Current user role: {get_current_user_role()} (Expected: None)")

    # Old test cases, ensure they are covered or adapted
    # print("\nTesting login...")
    # login_success_admin = login("TestAdmin", "adminpass") # Covered by test_admin_name
    # print(f"Admin login with correct password ('TestAdmin', 'adminpass'): {login_success_admin}")

    # if login_success_admin:
    #     print(f"Current User ID: {get_current_user_id()}")
    #     print(f"Current User Role: {get_current_user_role()}")
    #     print(f"Is user logged in? {is_user_logged_in()}")
    #     print(f"Is user admin? {is_admin()}")
    #     logout()
    #     print(f"After logout, is user logged in? {is_user_logged_in()}")
    #     print(f"After logout, current user role: {get_current_user_role()}")

    # login_fail_wrong_pass = login("TestAdmin", "wrongpass") # Covered
    # print(f"Admin login with incorrect password ('TestAdmin', 'wrongpass'): {login_fail_wrong_pass}")

    # login_fail_no_user = login("NoSuchUser", "anypass") # Covered
    # print(f"Login with non-existent user ('NoSuchUser', 'anypass'): {login_fail_no_user}")

    # login_success_student = login("TestStudent", "studentpass") # Covered by test_student_with_pass_name
    # print(f"Student login with correct password ('TestStudent', 'studentpass'): {login_success_student}")

    # if login_success_student:
    #     print(f"Current User ID: {get_current_user_id()}")
    #     print(f"Current User Role: {get_current_user_role()}")
    #     print(f"Is user logged in? {is_user_logged_in()}")
    #     print(f"Is user admin? {is_admin()}")
    #     logout()

    print("\nTesting with a user that might not have password fields (if any added manually without password):")
    # This scenario is now explicitly tested with TestStudentNoPassAuth

    # The "Alice Wonderland" test relies on student_manager.py's __main__ being run.
    # This is less reliable for auth_manager specific tests.
    # We'll keep it as a legacy check but prioritize the new explicit tests.
    print("Login attempt for 'Alice Wonderland' (password 'password123' - from student_manager tests, if run):")
    alice_login_test = login("Alice Wonderland", "password123") # This student has a password
    print(f"Login for Alice: {alice_login_test}")
    if alice_login_test:
        print(f"Alice role: {get_current_user_role()}")
        logout()

    # Test a student who should have a password, but we try to log in with empty string
    # (assuming Alice has a password from student_manager.py's tests)
    alice_login_empty_pass_test = login("Alice Wonderland", "")
    print(f"Login for Alice with empty password: {alice_login_empty_pass_test} (Expected: False if Alice has a password)")
    if alice_login_empty_pass_test: logout()


    print("\nAuth Manager tests finished.")
భార్యadmin_id = student_manager.add_student_db("TestAdmin", "AdminOffice", "adminpass", "admin")
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
