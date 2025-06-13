import sqlite3
import os
from datetime import datetime, timedelta

# Adjust paths if necessary, assuming script is in classroom_library_app
import book_manager
import student_manager
from database.db_setup import init_db

DB_PATH = 'database/library.db'

def db_connect():
    return sqlite3.connect(DB_PATH)

def print_test_title(title):
    print(f"\n--- {title} ---")

def check_db_for_student(student_id, expected_name, expected_classroom, expected_role):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, classroom, role FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()
    assert student is not None, f"Student {student_id} not found in DB."
    assert student[0] == expected_name, f"Student name mismatch: expected {expected_name}, got {student[0]}"
    assert student[1] == expected_classroom, f"Student classroom mismatch: expected {expected_classroom}, got {student[1]}"
    assert student[2] == expected_role, f"Student role mismatch: expected {expected_role}, got {student[2]}"
    print(f"DB Check PASSED for student {student_id} ({expected_name})")

def check_db_for_book(book_id, expected_title, expected_status='available', expected_borrower_id=None, expected_due_date=None):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT title, status, borrower_id, due_date FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()
    assert book is not None, f"Book {book_id} not found in DB."
    assert book[0] == expected_title, f"Book title mismatch: expected {expected_title}, got {book[0]}"
    assert book[1] == expected_status, f"Book status mismatch: expected {expected_status}, got {book[1]}"
    assert book[2] == expected_borrower_id, f"Book borrower_id mismatch: expected {expected_borrower_id}, got {book[2]}"
    assert book[3] == expected_due_date, f"Book due_date mismatch: expected {expected_due_date}, got {book[3]}"
    print(f"DB Check PASSED for book {book_id} ({expected_title})")

def run_tests():
    # Initialize DB (creates tables if they don't exist)
    # For true repeatable tests, you might delete the DB file here first
    if os.path.exists(DB_PATH):
        print(f"Note: Database {DB_PATH} already exists. Tests will run on existing DB.")
    init_db()

    # --- A. student_manager.py Tests ---
    print_test_title("Student Manager Tests")

    # 1. Add 'leader' and 'student'
    leader_name, leader_class, leader_role = "TestLeader Tom", "Class Alpha", "leader"
    student_name, student_class, student_role = "TestStudent Jerry", "Class Alpha", "student"
    student2_name, student2_class, student2_role = "TestStudent Beta", "Class Beta", "student"

    leader_id = student_manager.add_student_db(leader_name, leader_class, leader_role)
    student_id = student_manager.add_student_db(student_name, student_class, student_role)
    student2_id = student_manager.add_student_db(student2_name, student2_class, student2_role)

    assert leader_id is not None, "add_student_db failed for leader."
    assert student_id is not None, "add_student_db failed for student."
    assert student2_id is not None, "add_student_db failed for student2."
    print(f"Leader added with ID: {leader_id}")
    print(f"Student added with ID: {student_id}")
    print(f"Student2 added with ID: {student2_id}")

    check_db_for_student(leader_id, leader_name, leader_class, leader_role)
    check_db_for_student(student_id, student_name, student_class, student_role)

    # 2. Get student by ID
    fetched_leader = student_manager.get_student_by_id_db(leader_id)
    assert fetched_leader is not None and fetched_leader['name'] == leader_name, "get_student_by_id_db failed or returned incorrect data for leader."
    print(f"Fetched leader by ID: {fetched_leader['name']}")

    # 3. is_student_leader
    assert student_manager.is_student_leader(leader_id) is True, "is_student_leader failed for actual leader."
    assert student_manager.is_student_leader(student_id) is False, "is_student_leader failed for actual student."
    assert student_manager.is_student_leader("non_existent_id") is False, "is_student_leader failed for non-existent ID."
    print("is_student_leader tests PASSED.")

    # 4. get_students_by_classroom_db
    class_alpha_students = student_manager.get_students_by_classroom_db("Class Alpha")
    class_beta_students = student_manager.get_students_by_classroom_db("Class Beta")
    assert len(class_alpha_students) >= 2, "get_students_by_classroom_db failed for Class Alpha (expected at least 2)." # >= because tests might re-run
    class_alpha_names = [s['name'] for s in class_alpha_students]
    assert leader_name in class_alpha_names, f"{leader_name} not found in Class Alpha students."
    assert student_name in class_alpha_names, f"{student_name} not found in Class Alpha students."

    assert len(class_beta_students) >= 1, "get_students_by_classroom_db failed for Class Beta (expected at least 1)."
    assert student2_name in [s['name'] for s in class_beta_students], f"{student2_name} not found in Class Beta students."
    print("get_students_by_classroom_db tests PASSED.")


    # --- B. book_manager.py Tests ---
    print_test_title("Book Manager Tests")

    # 1. Add book
    book1_title, book1_author, book1_class = "The Adventures of Coding", "AI Bot", "Class Alpha"
    book1_id = book_manager.add_book_db(book1_title, book1_author, book1_class, isbn="1234567890")
    assert book1_id is not None, "add_book_db failed for book1."
    print(f"Book1 added with ID: {book1_id}")
    check_db_for_book(book1_id, book1_title)

    # 2. Import CSV
    # Create a dummy CSV file for testing
    dummy_csv_content = "Title,Author,Classroom,ISBN,CoverImage\n" \
                        "CSV Book 1,Author CSV1,Class Alpha,111222333,\n" \
                        "CSV Book 2,Author CSV2,Class Beta,444555666,test.jpg"
    dummy_csv_path = "assets/test_import.csv"
    # Ensure assets directory exists
    if not os.path.exists("assets"):
        os.makedirs("assets")
    with open(dummy_csv_path, "w") as f:
        f.write(dummy_csv_content)

    success_count, errors = book_manager.import_books_from_csv_db(dummy_csv_path)
    assert success_count == 2, f"import_books_from_csv_db expected 2 successes, got {success_count}."
    assert not errors, f"import_books_from_csv_db reported errors: {errors}"
    print(f"CSV Import: {success_count} successes, Errors: {errors}")
    # Check one of the imported books in DB (basic check)
    # This requires knowing the title to search for, as IDs are dynamic
    csv_book1_data = book_manager.search_books_db("CSV Book 1", "title")
    assert csv_book1_data and csv_book1_data[0]['author'] == "Author CSV1", "CSV Book 1 not found or data mismatch after import."
    print("CSV import basic check PASSED.")
    os.remove(dummy_csv_path) # Clean up dummy file

    # 3. get_all_books_db
    all_books = book_manager.get_all_books_db()
    assert isinstance(all_books, list), "get_all_books_db did not return a list."
    assert len(all_books) >= 3, "get_all_books_db should have at least 3 books now." # book1 + 2 from CSV
    print(f"get_all_books_db returned {len(all_books)} books.")

    # 4. search_books_db
    searched_books = book_manager.search_books_db(book1_title, "title")
    # Check if any of the found books match the ID, to handle multiple test runs creating duplicate titles
    found_book1_in_search = any(book['id'] == book1_id for book in searched_books)
    assert found_book1_in_search, f"search_books_db failed to find book1_id: {book1_id} with title '{book1_title}'."
    if searched_books:
        print(f"Search for '{book1_title}' found {len(searched_books)} book(s). First match: {searched_books[0]['title']}")
    else:
        print(f"Search for '{book1_title}' found no books.")


    # 5. Loan/Return Logic
    print_test_title("Loan/Return Logic Tests")
    # Use leader_id and student_id from Student Manager tests (ensure they are in Class Alpha)
    # Use book1_id (The Adventures of Coding, Class Alpha)

    # Ensure book1_id is available (it should be, as it was just added)
    book_to_loan_details_before_loan = book_manager.get_all_books_db(status_filter='available')
    available_book_for_loan = None
    for bk in book_to_loan_details_before_loan:
        if bk['classroom'] == "Class Alpha" and bk['title'] == book1_title : # find a suitable book
             available_book_for_loan = bk['id']
             break

    assert available_book_for_loan is not None, f"Could not find an available book titled '{book1_title}' in Class Alpha for loan test."
    print(f"Attempting to loan book ID: {available_book_for_loan}")

    loan_due_date = (datetime.now().date() + timedelta(days=10)).strftime('%Y-%m-%d')
    loan_success = book_manager.loan_book_db(available_book_for_loan, student_id, loan_due_date, leader_id)
    assert loan_success is True, f"loan_book_db failed. Book: {available_book_for_loan}, Student: {student_id}, Leader: {leader_id}"
    print(f"Book {available_book_for_loan} loaned to {student_id} successfully.")
    check_db_for_book(available_book_for_loan, book1_title, expected_status='borrowed', expected_borrower_id=student_id, expected_due_date=loan_due_date)

    current_loans = book_manager.get_current_loans_db(classroom_filter="Class Alpha")
    assert any(loan['id'] == available_book_for_loan and loan['borrower_id'] == student_id for loan in current_loans), "Loaned book not found in get_current_loans_db."
    print(f"Loaned book found in current loans for Class Alpha.")

    # Test get_books_due_soon_db (should include the one we just loaned)
    due_soon_books = book_manager.get_books_due_soon_db(days_threshold=15, classroom_filter="Class Alpha")
    assert any(book['id'] == available_book_for_loan for book in due_soon_books), "Loaned book not found in get_books_due_soon_db."
    print(f"Loaned book found in due_soon_books for Class Alpha.")


    return_success = book_manager.return_book_db(available_book_for_loan, leader_id)
    assert return_success is True, "return_book_db failed."
    print(f"Book {available_book_for_loan} returned successfully.")
    check_db_for_book(available_book_for_loan, book1_title, expected_status='available', expected_borrower_id=None, expected_due_date=None)

    # Check it's no longer in current loans
    current_loans_after_return = book_manager.get_current_loans_db(classroom_filter="Class Alpha")
    assert not any(loan['id'] == available_book_for_loan for loan in current_loans_after_return), "Returned book still appears in current loans."
    print(f"Returned book no longer in current loans for Class Alpha.")


    print("\nAll backend logic tests PASSED (or assertions met for this run).")

if __name__ == "__main__":
    run_tests()
