import unittest
import os
import sqlite3
import uuid # For generating unique names/IDs for testing
from datetime import datetime, timedelta

# Modules to be tested
from . import student_manager
from . import auth_manager
from . import book_manager # Added for book tests
from .database import db_setup
from .utils import get_data_path

# --- Test Configuration ---
TEST_DB_NAME = "test_library.db"
TEST_DB_DIR = "database" # This is relative to the app's root if utils.get_data_path is used carefully
TEST_DB_PATH_FOR_CODE = os.path.join(TEST_DB_DIR, TEST_DB_NAME)
ACTUAL_TEST_DB_PATH = "" # Will be set in setUpModule

# --- Module Level Setup/Teardown ---
def setUpModule():
    """Sets up the test environment once for the entire module."""
    global ACTUAL_TEST_DB_PATH

    # Determine the actual path for the test database
    # Assuming get_data_path gives a path like /app/classroom_library_app/database/test_library.db
    ACTUAL_TEST_DB_PATH = get_data_path(TEST_DB_PATH_FOR_CODE)

    # Ensure the directory for the test DB exists
    db_dir = os.path.dirname(ACTUAL_TEST_DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Override DB_PATH in relevant modules BEFORE init_db() is called
    student_manager.DB_PATH = ACTUAL_TEST_DB_PATH
    book_manager.DB_PATH = ACTUAL_TEST_DB_PATH
    # db_setup needs to know which DB to initialize for the test
    db_setup.DB_PATH_FOR_CODE = TEST_DB_PATH_FOR_CODE # This is what init_db() uses internally with get_data_path

    print(f"Initializing test database at: {ACTUAL_TEST_DB_PATH}")
    db_setup.init_db() # This will create tables and potentially the default admin

def tearDownModule():
    """Cleans up the test environment once after all tests in the module have run."""
    if os.path.exists(ACTUAL_TEST_DB_PATH):
        try:
            os.remove(ACTUAL_TEST_DB_PATH)
            print(f"Test database {ACTUAL_TEST_DB_PATH} removed.")
        except Exception as e:
            print(f"Error removing test database {ACTUAL_TEST_DB_PATH}: {e}")
    else:
        print(f"Test database {ACTUAL_TEST_DB_PATH} not found, skipping removal.")

# --- Helper Functions ---
def _generate_unique_name(base="test"):
    return f"{base}_{uuid.uuid4().hex[:8]}"

# --- Test Classes ---
class TestStudentManager(unittest.TestCase):

    def setUp(self):
        # Each test method gets a fresh context regarding auth_manager state
        auth_manager.logout()

    def test_01_hash_and_verify_password(self):
        password = "securepassword123"
        salt_hex, hashed_password_hex = student_manager.hash_password(password)
        self.assertIsNotNone(salt_hex)
        self.assertIsNotNone(hashed_password_hex)
        self.assertTrue(student_manager.verify_password(hashed_password_hex, salt_hex, password))
        self.assertFalse(student_manager.verify_password(hashed_password_hex, salt_hex, "wrongpassword"))

    def test_02_add_student_roles_and_verify(self):
        roles_to_test = ["student", "leader", "admin"]
        for role in roles_to_test:
            user_name = _generate_unique_name(f"user_{role}")
            user_pass = f"{role}pass"
            user_id = student_manager.add_student_db(user_name, f"Class {role.capitalize()}", user_pass, role)
            self.assertIsNotNone(user_id, f"Failed to add user with role {role}")

            retrieved_user = student_manager.get_student_by_id_db(user_id)
            self.assertIsNotNone(retrieved_user, f"Failed to retrieve user with role {role}")
            self.assertEqual(retrieved_user['name'], user_name)
            self.assertEqual(retrieved_user['role'], role)
            self.assertIsNotNone(retrieved_user['hashed_password'])
            self.assertIsNotNone(retrieved_user['salt'])
            self.assertTrue(
                student_manager.verify_password(retrieved_user['hashed_password'], retrieved_user['salt'], user_pass),
                f"Password verification failed for user with role {role}"
            )

    def test_03_delete_student(self):
        user_name = _generate_unique_name("todelete")
        user_id = student_manager.add_student_db(user_name, "Class Del", "delpass", "student")
        self.assertIsNotNone(user_id)

        delete_success = student_manager.delete_student_db(user_id)
        self.assertTrue(delete_success)
        self.assertIsNone(student_manager.get_student_by_id_db(user_id))
        self.assertFalse(student_manager.delete_student_db(user_id)) # Try deleting again

    def test_04_update_student_details(self):
        user_name_orig = _generate_unique_name("origdetails")
        user_pass = "detailpass"
        user_id = student_manager.add_student_db(user_name_orig, "Class Orig", user_pass, "student")
        self.assertIsNotNone(user_id)

        original_student = student_manager.get_student_by_id_db(user_id)
        original_hash = original_student['hashed_password']
        original_salt = original_student['salt']

        new_name = _generate_unique_name("newdetails")
        new_class = "Class New"
        new_role = "leader"
        update_success = student_manager.update_student_details_db(user_id, new_name, new_class, new_role)
        self.assertTrue(update_success)

        updated_student = student_manager.get_student_by_id_db(user_id)
        self.assertEqual(updated_student['name'], new_name)
        self.assertEqual(updated_student['classroom'], new_class)
        self.assertEqual(updated_student['role'], new_role)
        self.assertEqual(updated_student['hashed_password'], original_hash, "Hashed password changed during details update.")
        self.assertEqual(updated_student['salt'], original_salt, "Salt changed during details update.")
        self.assertTrue(student_manager.verify_password(updated_student['hashed_password'], updated_student['salt'], user_pass))

    def test_05_update_student_password(self):
        user_name = _generate_unique_name("passupdate")
        old_pass = "oldpassword"
        new_pass = "newpassword"
        user_id = student_manager.add_student_db(user_name, "Class Pass", old_pass, "student")
        self.assertIsNotNone(user_id)

        original_student = student_manager.get_student_by_id_db(user_id)
        original_hash = original_student['hashed_password']
        original_salt = original_student['salt']

        update_pass_success = student_manager.update_student_password_db(user_id, new_pass)
        self.assertTrue(update_pass_success)

        updated_student = student_manager.get_student_by_id_db(user_id)
        self.assertNotEqual(updated_student['hashed_password'], original_hash)
        self.assertNotEqual(updated_student['salt'], original_salt)
        self.assertFalse(student_manager.verify_password(updated_student['hashed_password'], updated_student['salt'], old_pass))
        self.assertTrue(student_manager.verify_password(updated_student['hashed_password'], updated_student['salt'], new_pass))

    def test_06_is_student_leader(self):
        leader_name = _generate_unique_name("leadercheck")
        student_name = _generate_unique_name("studentcheck")
        leader_id = student_manager.add_student_db(leader_name, "Class Check", "leadpass", "leader")
        student_id = student_manager.add_student_db(student_name, "Class Check", "studpass", "student")

        self.assertTrue(student_manager.is_student_leader(leader_id))
        self.assertFalse(student_manager.is_student_leader(student_id))
        self.assertFalse(student_manager.is_student_leader("non_existent_id"))


class TestAuthManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.admin_username = _generate_unique_name("auth_admin")
        cls.admin_password = "auth_admin_pass"
        cls.admin_user_id = student_manager.add_student_db(cls.admin_username, "AdminOffice", cls.admin_password, "admin")
        assert cls.admin_user_id is not None, "Failed to create admin user for TestAuthManager"

        cls.student_username = _generate_unique_name("auth_student")
        cls.student_password = "auth_student_pass"
        cls.student_user_id = student_manager.add_student_db(cls.student_username, "Class Auth", cls.student_password, "student")
        assert cls.student_user_id is not None, "Failed to create student user for TestAuthManager"

    def tearDown(self):
        auth_manager.logout()

    def test_01_login_success_admin(self):
        self.assertTrue(auth_manager.login(self.admin_username, self.admin_password))
        self.assertEqual(auth_manager.get_current_user_id(), self.admin_user_id)
        self.assertEqual(auth_manager.get_current_user_role(), "admin")
        self.assertTrue(auth_manager.is_user_logged_in())
        self.assertTrue(auth_manager.is_admin())

    def test_02_login_success_student(self):
        self.assertTrue(auth_manager.login(self.student_username, self.student_password))
        self.assertEqual(auth_manager.get_current_user_id(), self.student_user_id)
        self.assertEqual(auth_manager.get_current_user_role(), "student")
        self.assertTrue(auth_manager.is_user_logged_in())
        self.assertFalse(auth_manager.is_admin())

    def test_03_login_incorrect_password(self):
        self.assertFalse(auth_manager.login(self.student_username, "wrong_password"))
        self.assertIsNone(auth_manager.get_current_user_id())
        self.assertIsNone(auth_manager.get_current_user_role())
        self.assertFalse(auth_manager.is_user_logged_in())

    def test_04_login_non_existent_user(self):
        self.assertFalse(auth_manager.login("no_such_user_exists", "anypassword"))
        self.assertIsNone(auth_manager.get_current_user_id())
        self.assertIsNone(auth_manager.get_current_user_role())

    def test_05_logout(self):
        auth_manager.login(self.student_username, self.student_password)
        self.assertTrue(auth_manager.is_user_logged_in())
        auth_manager.logout()
        self.assertIsNone(auth_manager.get_current_user_id())
        self.assertIsNone(auth_manager.get_current_user_role())
        self.assertFalse(auth_manager.is_user_logged_in())
        self.assertFalse(auth_manager.is_admin())

class TestDbSetup(unittest.TestCase):

    def test_01_default_admin_creation_on_first_init(self):
        # This test assumes setUpModule called init_db() which created the default 'admin'
        # if the DB was truly fresh.
        default_admin_name = "admin"
        admin_user = None
        all_users = student_manager.get_students_db(role_filter="admin")
        for user in all_users:
            if user['name'] == default_admin_name:
                admin_user = user
                break

        self.assertIsNotNone(admin_user, f"Default admin user '{default_admin_name}' not found.")
        self.assertEqual(admin_user['role'], "admin")
        self.assertEqual(admin_user['classroom'], "AdminOffice")
        # Password check for default admin
        self.assertTrue(student_manager.verify_password(admin_user['hashed_password'], admin_user['salt'], "adminpass"))

    def test_02_init_db_idempotency_for_default_admin(self):
        # Call init_db() again. It should not create a duplicate default admin or error out.
        db_setup.init_db()

        conn = sqlite3.connect(ACTUAL_TEST_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE name = 'admin' AND role = 'admin' AND classroom = 'AdminOffice'")
        admin_count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(admin_count, 1, "Default admin 'admin' was duplicated or missing after subsequent init_db call.")

class TestBookManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Need some students for loaning books
        cls.loan_leader_name = _generate_unique_name("loan_leader")
        cls.loan_student_name = _generate_unique_name("loan_student")
        cls.loan_classroom = "Class LoanTest"

        cls.loan_leader_id = student_manager.add_student_db(cls.loan_leader_name, cls.loan_classroom, "loanleadpass", "leader")
        cls.loan_student_id = student_manager.add_student_db(cls.loan_student_name, cls.loan_classroom, "loanstudpass", "student")
        assert cls.loan_leader_id, "Failed to create leader for TestBookManager"
        assert cls.loan_student_id, "Failed to create student for TestBookManager"

    def test_01_add_and_get_book(self):
        book_title = _generate_unique_name("Test Book")
        book_author = "Test Author"
        book_classroom = self.loan_classroom
        book_isbn = "1234500000"

        book_id = book_manager.add_book_db(book_title, book_author, book_classroom, book_isbn)
        self.assertIsNotNone(book_id)

        all_books = book_manager.get_all_books_db(classroom_filter=book_classroom)
        found = any(b['id'] == book_id and b['title'] == book_title for b in all_books)
        self.assertTrue(found, "Added book not found by get_all_books_db.")

    def test_02_search_books(self):
        search_term = _generate_unique_name("SearchableBook")
        book_manager.add_book_db(search_term, "Search Author", self.loan_classroom)

        results_title = book_manager.search_books_db(search_term, "title")
        self.assertTrue(any(b['title'] == search_term for b in results_title))

        results_author = book_manager.search_books_db("Search Author", "author")
        self.assertTrue(any(b['author'] == "Search Author" for b in results_author))

    def test_03_loan_and_return_book(self):
        book_title = _generate_unique_name("Loanable Book")
        book_id = book_manager.add_book_db(book_title, "Loan Author", self.loan_classroom)
        self.assertIsNotNone(book_id)

        due_date = (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')

        # Loan the book
        loan_success = book_manager.loan_book_db(book_id, self.loan_student_id, due_date, self.loan_leader_id)
        self.assertTrue(loan_success, "Failed to loan book.")

        borrowed_book = book_manager.get_all_books_db(book_id_filter=book_id)[0] # get specific book
        self.assertEqual(borrowed_book['status'], 'borrowed')
        self.assertEqual(borrowed_book['borrower_id'], self.loan_student_id)
        self.assertEqual(borrowed_book['due_date'], due_date)

        # Check current loans
        current_loans = book_manager.get_current_loans_db(classroom_filter=self.loan_classroom)
        self.assertTrue(any(l['id'] == book_id and l['borrower_id'] == self.loan_student_id for l in current_loans))

        # Check due soon
        due_soon = book_manager.get_books_due_soon_db(days_threshold=10, classroom_filter=self.loan_classroom)
        self.assertTrue(any(b['id'] == book_id for b in due_soon))

        # Return the book
        return_success = book_manager.return_book_db(book_id, self.loan_leader_id)
        self.assertTrue(return_success, "Failed to return book.")

        returned_book = book_manager.get_all_books_db(book_id_filter=book_id)[0]
        self.assertEqual(returned_book['status'], 'available')
        self.assertIsNone(returned_book['borrower_id'])
        self.assertIsNone(returned_book['due_date'])

    # Skipping CSV import test for now as it involves file I/O and might be flaky in some CI/test environments
    # If it's critical, it can be added with careful path management and cleanup.

if __name__ == '__main__':
    # This allows running the tests directly from this file.
    # However, it's often better to use the unittest discovery mechanism:
    # `python -m unittest classroom_library_app.test_backend` from the project root,
    # or `python -m unittest discover`
    unittest.main(verbosity=2)
