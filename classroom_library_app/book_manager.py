import sqlite3
import uuid
import csv
from datetime import datetime, timedelta
import student_manager
import os
# Assuming utils.py is in the same directory level (classroom_library_app/)
from utils import get_data_path

# DB_PATH_FOR_CODE is the relative path string that get_data_path will use.
# It should point to where the database is expected to be within the application's
# data structure (e.g., "database/library.db").
DB_PATH_FOR_CODE = os.path.join("database", "library.db")
# The actual path used by sqlite3.connect will be resolved by get_data_path(DB_PATH_FOR_CODE)

def _get_resolved_db_path():
    # This helper ensures the database directory exists, especially for dev.
    # PyInstaller's bundled 'database' dir will exist.
    path = get_data_path(DB_PATH_FOR_CODE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def generate_id():
    """Generates a unique ID for a book."""
    return str(uuid.uuid4())

def add_book_db(title, author, classroom, isbn=None, image_path=None):
    """Adds a new book to the database.
    Returns the new book's ID or None on failure."""
    book_id = generate_id()
    status = 'available'
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (id, title, author, isbn, classroom, status, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (book_id, title, author, isbn, classroom, status, image_path))
        conn.commit()
        return book_id
    except sqlite3.Error as e:
        print(f"Database error in add_book_db: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_books_db(classroom_filter=None, status_filter=None):
    """Queries the books table, applying optional filters for classroom and status.
    Returns a list of dictionaries (each dict representing a book)."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()

        query = "SELECT * FROM books"
        filters = []
        params = []

        if classroom_filter and classroom_filter != "All":
            filters.append("classroom = ?")
            params.append(classroom_filter)

        if status_filter and status_filter != "All":
            filters.append("status = ?")
            params.append(status_filter)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
        books = [dict(row) for row in cursor.fetchall()]
        return books
    except sqlite3.Error as e:
        print(f"Database error in get_all_books_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def import_books_from_csv_db(file_path):
    """Reads a CSV file and adds books to the database.
    Expected headers: Title, Author, Classroom, ISBN, CoverImage.
    Returns a tuple: (successful_imports_count, error_messages_list)."""
    successful_imports = 0
    error_messages = []

    try:
        # file_path for import_books_from_csv_db is an absolute path from filedialog,
        # so it does not need get_data_path.
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            required_headers = ["Title", "Author", "Classroom"]
            if not all(header in reader.fieldnames for header in required_headers):
                error_messages.append(f"CSV file is missing one or more required headers: {', '.join(required_headers)}. Found: {', '.join(reader.fieldnames or [])}")
                return successful_imports, error_messages

            for row_num, row in enumerate(reader, start=2): # start=2 for 1-based indexing + header
                title = row.get("Title")
                author = row.get("Author")
                classroom = row.get("Classroom")
                isbn = row.get("ISBN")
                cover_image = row.get("CoverImage") # Or 'image_path' depending on CSV

                if not title or not author or not classroom:
                    error_messages.append(f"Row {row_num}: Missing required fields (Title, Author, Classroom). Skipping.")
                    continue

                book_id = add_book_db(title, author, classroom, isbn, cover_image)
                if book_id:
                    successful_imports += 1
                else:
                    error_messages.append(f"Row {row_num}: Failed to add book '{title}' by '{author}' to database.")

    except FileNotFoundError:
        error_messages.append(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        error_messages.append(f"An unexpected error occurred during CSV import: {e}")

    return successful_imports, error_messages

def search_books_db(query, search_field="title"):
    """Searches books where search_field CONTAINS query (case-insensitive).
    Returns a list of book dictionaries."""
    if not query:
        return []

    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()

        # Basic protection against SQL injection for search_field
        allowed_search_fields = ["title", "author", "isbn", "classroom", "status"] # Add more if needed
        if search_field not in allowed_search_fields:
            print(f"Invalid search field: {search_field}. Defaulting to title.")
            search_field = "title"

        # Using LIKE for case-insensitive partial matching
        # The ? placeholder will handle escaping the query string
        sql_query = f"SELECT * FROM books WHERE {search_field} LIKE ?"

        cursor.execute(sql_query, (f"%{query}%",))
        books = [dict(row) for row in cursor.fetchall()]
        return books
    except sqlite3.Error as e:
        print(f"Database error in search_books_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

# --- Loan Management Functions ---

def loan_book_db(book_id, student_id, due_date, lending_student_leader_id):
    """Loans a book to a student if validations pass.
    Validates: student leader, book availability, student existence.
    Updates book status, borrower_id, due_date. Returns True/False."""
    if not student_manager.is_student_leader(lending_student_leader_id):
        print(f"Loan Error: Lending student {lending_student_leader_id} is not a leader or does not exist.")
        return False

    borrower = student_manager.get_student_by_id_db(student_id)
    if not borrower:
        print(f"Loan Error: Borrower student {student_id} does not exist.")
        return False

    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        cursor.execute("SELECT status, classroom FROM books WHERE id = ?", (book_id,))
        book_data = cursor.fetchone()

        if not book_data:
            print(f"Loan Error: Book with ID {book_id} not found.")
            return False

        current_status, book_classroom = book_data[0], book_data[1]

        if current_status != 'available':
            print(f"Loan Error: Book '{book_id}' is not available (current status: {current_status}).")
            return False

        cursor.execute("""
            UPDATE books
            SET status = 'borrowed', borrower_id = ?, due_date = ?
            WHERE id = ?
        """, (student_id, due_date, book_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Book '{book_id}' loaned to student '{student_id}' successfully.")
            return True
        else:
            print(f"Loan Error: Failed to update book status for '{book_id}'.")
            return False

    except sqlite3.Error as e:
        print(f"Database error in loan_book_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def return_book_db(book_id, student_leader_id):
    """Returns a book.
    Validates: student leader, book is currently borrowed.
    Updates book status, clears borrower_id, due_date. Returns True/False."""
    if not student_manager.is_student_leader(student_leader_id):
        print(f"Return Error: Returning student {student_leader_id} is not a leader or does not exist.")
        return False

    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM books WHERE id = ?", (book_id,))
        result = cursor.fetchone()
        if not result:
            print(f"Return Error: Book ID {book_id} not found.")
            return False

        current_status = result[0]
        if current_status != 'borrowed':
            print(f"Return Error: Book '{book_id}' is not currently borrowed (status: {current_status}).")
            return False

        cursor.execute("""
            UPDATE books
            SET status = 'available', borrower_id = NULL, due_date = NULL
            WHERE id = ?
        """, (book_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Book '{book_id}' returned successfully.")
            return True
        else:
            print(f"Return Error: Failed to update book status for '{book_id}' upon return.")
            return False

    except sqlite3.Error as e:
        print(f"Database error in return_book_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_current_loans_db(classroom_filter=None):
    """Fetches books with status 'borrowed', joining with students for borrower_name.
    Filters by books.classroom if classroom_filter is provided.
    Returns list of dicts (book info + borrower_name)."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT b.*, s.name as borrower_name
            FROM books b
            JOIN students s ON b.borrower_id = s.id
            WHERE b.status = 'borrowed'
        """
        params = []

        if classroom_filter and classroom_filter != "All":
            query += " AND b.classroom = ?"
            params.append(classroom_filter)

        cursor.execute(query, params)
        loans = [dict(row) for row in cursor.fetchall()]
        return loans
    except sqlite3.Error as e:
        print(f"Database error in get_current_loans_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_books_due_soon_db(days_threshold=7, classroom_filter=None):
    """Fetches borrowed books due within days_threshold or already overdue.
    Joins with students for borrower_name. Filters by classroom.
    Returns list of dicts. (Due date format is YYYY-MM-DD)."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        threshold_date_str = (datetime.now().date() + timedelta(days=days_threshold)).strftime('%Y-%m-%d')

        query = """
            SELECT b.*, s.name as borrower_name
            FROM books b
            JOIN students s ON b.borrower_id = s.id
            WHERE b.status = 'borrowed' AND b.due_date IS NOT NULL
            AND b.due_date <= ?
        """
        params = [threshold_date_str]

        if classroom_filter and classroom_filter != "All":
            query += " AND b.classroom = ?"
            params.append(classroom_filter)

        query += " ORDER BY b.due_date ASC"

        cursor.execute(query, params)
        due_books = [dict(row) for row in cursor.fetchall()]
        return due_books
    except sqlite3.Error as e:
        print(f"Database error in get_books_due_soon_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    # First, ensure database and table are created by running db_setup.py or main.py
    # from database.db_setup import init_db
    # init_db() # Make sure db is initialized

    # Test adding a book
    print("Attempting to add a book...")
    # new_id = add_book_db("The Little Prince", "Antoine de Saint-Exupéry", "Class A", "978-0156012195")
    # if new_id:
    #     print(f"Book added successfully with ID: {new_id}")
    # else:
    #     print("Failed to add book.")

    # Test adding another book
    # new_id_2 = add_book_db("To Kill a Mockingbird", "Harper Lee", "Class B", "978-0061120084")
    # if new_id_2:
    #     print(f"Book added successfully with ID: {new_id_2}")
    # else:
    #     print("Failed to add book.")

    # Test getting all books
    print("\nGetting all books:")
    all_books = get_all_books_db()
    if all_books:
        for book in all_books:
            print(f"  Title: {book['title']}, Author: {book['author']}, Classroom: {book['classroom']}, Status: {book['status']}")
    else:
        print("No books found or error occurred.")

    # Test getting books for a specific classroom
    print("\nGetting books for Class A:")
    class_a_books = get_all_books_db(classroom_filter="Class A")
    if class_a_books:
        for book in class_a_books:
            print(f"  Title: {book['title']}, Author: {book['author']}, Classroom: {book['classroom']}")
    else:
        print("No books found for Class A.")

    # Test getting available books
    print("\nGetting available books:")
    available_books = get_all_books_db(status_filter="available")
    if available_books:
        for book in available_books:
            print(f"  Title: {book['title']}, Status: {book['status']}")
    else:
        print("No available books found.")

    # Test getting available books for Class B
    # print("\nGetting available books for Class B:")
    # available_class_b_books = get_all_books_db(classroom_filter="Class B", status_filter="available")
    # if available_class_b_books:
    #     for book in available_class_b_books:
    #         print(f"  Title: {book['title']}, Classroom: {book['classroom']}, Status: {book['status']}")
    # else:
    #     print("No available books found for Class B.")

    # Test importing books from CSV
    # print(f"\nImporting books from sample_books.csv:")
    # import os
    # if not os.path.exists("assets"):
    #     os.makedirs("assets")
    # # To test import_books_from_csv_db, you would typically run the main app
    # # and use the UI, or ensure 'assets/sample_books.csv' exists and call:
    # # success_count, errors = import_books_from_csv_db("assets/sample_books.csv")
    # # print(f"Successfully imported {success_count} books.")
    # # if errors:
    # #     print("Errors during import:")
    # #     for error in errors:
    # #         print(f"  - {error}")
    #
    # print("\nBooks after potential import (if you uncommented and ran import):")
    # all_books_after_import = get_all_books_db()
    # if all_books_after_import:
    #     for book in all_books_after_import:
    #         print(f"  Title: {book['title']}, Author: {book['author']}, Classroom: {book['classroom']}")
    # else:
    #     print("No books found or error occurred.")

    # Test searching books
    # print("\nSearching for books with 'Cat' in title:") # Assuming Cat in the Hat was added or imported
    # # Ensure init_db() was called from student_manager or main to have tables ready for loan tests
    # # from database.db_setup import init_db
    # # init_db()
    #
    # # Sample data for testing loan functions (assuming student_manager.py was run or students exist)
    # # Ensure these IDs exist in your DB if running this test block directly.
    # sample_book_id_available = add_book_db("Available Book 1", "Author A", "Class A")
    # sample_book_id_borrowed = add_book_db("Borrowed Book 1", "Author B", "Class A") # Will be borrowed
    #
    # # Assuming student_manager.py created these or you add them manually for testing
    # # student_leader_id = student_manager.add_student_db("Test Leader", "Class A", "leader")
    # # regular_student_id = student_manager.add_student_db("Test Borrower", "Class A", "student")
    #
    # # Manually find/set existing IDs from your DB for robust testing if not adding above:
    # print("\n--- Setup for Loan/Return Tests ---")
    # print("Fetching existing leader and student for tests...")
    # leaders_for_test = student_manager.get_students_db(role_filter="leader", classroom_filter="Class A")
    # students_for_test = student_manager.get_students_db(role_filter="student", classroom_filter="Class A")
    #
    # if not leaders_for_test or not students_for_test:
    #     print("Please ensure you have at least one leader and one student in Class A to run loan tests.")
    # else:
    #     student_leader_id = leaders_for_test[0]['id']
    #     regular_student_id = students_for_test[0]['id']
    #     print(f"Using Leader ID: {student_leader_id}, Student ID: {regular_student_id} for tests")
    #
    #     if sample_book_id_available:
    #         print(f"Available book for loan test: {sample_book_id_available}")
    #
    #     # Test loan_book_db
    #     print("\n--- Testing loan_book_db ---")
    #     due_date_str = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    #     if sample_book_id_available and student_leader_id and regular_student_id:
    #         loan_success = loan_book_db(sample_book_id_available, regular_student_id, due_date_str, student_leader_id)
    #         print(f"Loan attempt for '{sample_book_id_available}' to '{regular_student_id}': {'Success' if loan_success else 'Failed'}")
    #         if loan_success:
    #             # Setup sample_book_id_borrowed to be this book for return test
    #             sample_book_id_borrowed = sample_book_id_available
    #
    #     # Test loan_book_db - book already borrowed
    #     if sample_book_id_borrowed and student_leader_id and regular_student_id: # Try to loan the now borrowed book
    #         loan_fail_due_to_status = loan_book_db(sample_book_id_borrowed, regular_student_id, due_date_str, student_leader_id)
    #         print(f"Loan attempt for already borrowed book '{sample_book_id_borrowed}': {'Failed as expected' if not loan_fail_due_to_status else 'Unexpectedly succeeded'}")
    #
    #     # Test loan_book_db - invalid leader
    #     if sample_book_id_available and regular_student_id: # Assuming sample_book_id_available is still available or use another one
    #         another_available_book = add_book_db("Available Book 2", "Author C", "Class A")
    #         if another_available_book:
    #             loan_fail_leader = loan_book_db(another_available_book, regular_student_id, due_date_str, "invalid_leader_id")
    #             print(f"Loan attempt with invalid leader: {'Failed as expected' if not loan_fail_leader else 'Unexpectedly succeeded'}")
    #
    #     # Test get_current_loans_db
    #     print("\n--- Testing get_current_loans_db ---")
    #     current_loans_class_a = get_current_loans_db(classroom_filter="Class A")
    #     if current_loans_class_a:
    #         print("Current Loans in Class A:")
    #         for loan in current_loans_class_a:
    #             print(f"  Book: {loan['title']}, Borrower: {loan.get('borrower_name', 'N/A')}, Due: {loan['due_date']}")
    #     else:
    #         print("No current loans found in Class A.")
    #
    #     # Test get_books_due_soon_db
    #     print("\n--- Testing get_books_due_soon_db ---")
    #     due_soon_class_a = get_books_due_soon_db(days_threshold=15, classroom_filter="Class A") # Should catch the book loaned above
    #     if due_soon_class_a:
    #         print("Books due soon/overdue in Class A (15 days threshold):")
    #         for book in due_soon_class_a:
    #             print(f"  Book: {book['title']}, Borrower: {book.get('borrower_name', 'N/A')}, Due: {book['due_date']}")
    #     else:
    #         print("No books due soon or overdue in Class A with 15 days threshold.")
    #
    #     # Test return_book_db
    #     print("\n--- Testing return_book_db ---")
    #     if sample_book_id_borrowed and student_leader_id : # This book should be currently borrowed
    #         return_success = return_book_db(sample_book_id_borrowed, student_leader_id)
    #         print(f"Return attempt for '{sample_book_id_borrowed}': {'Success' if return_success else 'Failed'}")
    #
    #     # Test return_book_db - book not borrowed
    #     # Use another_available_book which was not successfully loaned or add a new one
    #     not_borrowed_book_id = add_book_db("Not Borrowed Book", "Author D", "Class A")
    #     if not_borrowed_book_id and student_leader_id:
    #         return_fail_status = return_book_db(not_borrowed_book_id, student_leader_id)
    #         print(f"Return attempt for not borrowed book '{not_borrowed_book_id}': {'Failed as expected' if not return_fail_status else 'Unexpectedly succeeded'}")
    #
    #     print("\n--- Final check of loans in Class A after return ---")
    #     final_loans_class_a = get_current_loans_db(classroom_filter="Class A")
    #     if final_loans_class_a:
    #         print("Current Loans in Class A:")
    #         for loan in final_loans_class_a:
    #             print(f"  Book: {loan['title']}, Borrower: {loan.get('borrower_name', 'N/A')}, Due: {loan['due_date']}")
    #     else:
    #         print("No current loans found in Class A (as expected if all returned).")

    # cat_books = search_books_db("Cat", "title")
    # if cat_books:
    #     for book in cat_books:
    #         print(f"  Found: {book['title']} by {book['author']}")
    # else:
    #     print("No books found with 'Cat' in title.")

    # print("\nSearching for books by author 'Dr. Seuss':")
    # seuss_books = search_books_db("Dr. Seuss", "author")
    # if seuss_books:
    #     for book in seuss_books:
    #         print(f"  Found: {book['title']} by {book['author']}")
    # else:
    #     print("No books by 'Dr. Seuss' found.")
    #
    # print("\nSearching for books in 'Class A':")
    # class_a_search_books = search_books_db("Class A", "classroom")
    # if class_a_search_books:
    #     for book in class_a_search_books:
    #         print(f"  Found: {book['title']} in {book['classroom']}")
    # else:
    #     print("No books found in 'Class A' through search.")
    pass # Keep the if __name__ == '__main__': block for future direct script testing if needed
