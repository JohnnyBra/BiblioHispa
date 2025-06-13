import sqlite3
import uuid
import csv # Re-added for CSV import functionality
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

def add_book_db(titulo, autor, ubicacion, genero=None, cantidad_total=1): # Added genero, cantidad_total, changed others
    """Adds a new book to the database.
    Returns the new book's ID or None on failure."""
    book_id = generate_id()
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (id, titulo, autor, genero, ubicacion, cantidad_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (book_id, titulo, autor, genero, ubicacion, cantidad_total))
        conn.commit()
        return book_id
    except sqlite3.Error as e:
        print(f"Database error in add_book_db: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_books_db(ubicacion_filter=None): # Changed classroom_filter to ubicacion_filter, removed status_filter
    """Queries the books table, applying optional filters for ubicacion.
    Returns a list of dictionaries (each dict representing a book)."""
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()

        query = "SELECT id, titulo, autor, genero, ubicacion, cantidad_total FROM books" # Updated columns
        params = []

        if ubicacion_filter and ubicacion_filter != "All": # Assuming "All" means no filter
            query += " WHERE ubicacion = ?"
            params.append(ubicacion_filter)

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
    Expected headers: Título, Autor, Género, Ubicación, Cantidad_Total.
    Returns a tuple: (successful_imports_count, error_messages_list)."""
    successful_imports = 0
    error_messages = []

    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            # Verify headers
            expected_headers = ["Título", "Autor", "Ubicación", "Cantidad_Total"] # Género is optional
            # Allow for flexibility with "Genero" vs "Género"
            actual_headers = reader.fieldnames
            if not actual_headers:
                 error_messages.append("El archivo CSV está vacío o no tiene encabezados.")
                 return successful_imports, error_messages

            # Normalize actual headers for comparison (e.g. handle BOM if any)
            normalized_actual_headers = [h.strip() for h in actual_headers]


            missing_headers = [eh for eh in expected_headers if eh not in normalized_actual_headers]
            if missing_headers:
                error_messages.append(f"El archivo CSV no contiene los encabezados requeridos: {', '.join(missing_headers)}. Encontrados: {', '.join(normalized_actual_headers)}")
                return successful_imports, error_messages

            # Check for Género header, handle if missing
            genero_header_present = "Género" in normalized_actual_headers or "Genero" in normalized_actual_headers
            genero_header_name = "Género" if "Género" in normalized_actual_headers else "Genero" if "Genero" in normalized_actual_headers else None


            for row_num, row in enumerate(reader, start=2):
                titulo = row.get("Título")
                autor = row.get("Autor")
                ubicacion = row.get("Ubicación")
                cantidad_total_str = row.get("Cantidad_Total")
                genero = row.get(genero_header_name) if genero_header_present and genero_header_name else None


                if not titulo or not autor or not ubicacion or not cantidad_total_str:
                    error_messages.append(f"Fila {row_num}: Faltan campos requeridos (Título, Autor, Ubicación, Cantidad_Total). Saltando fila.")
                    continue

                try:
                    cantidad_total_int = int(cantidad_total_str)
                    if cantidad_total_int <= 0:
                        error_messages.append(f"Fila {row_num}: 'Cantidad_Total' ({cantidad_total_str}) debe ser un número positivo. Usando 1 por defecto.")
                        cantidad_total_int = 1
                except ValueError:
                    error_messages.append(f"Fila {row_num}: 'Cantidad_Total' ({cantidad_total_str}) no es un número válido. Usando 1 por defecto.")
                    cantidad_total_int = 1

                book_id = add_book_db(titulo, autor, ubicacion, genero, cantidad_total_int)
                if book_id:
                    successful_imports += 1
                else:
                    error_messages.append(f"Fila {row_num}: Error al añadir libro '{titulo}' por '{autor}' a la base de datos.")

    except FileNotFoundError:
        error_messages.append(f"Error: No se encontró el archivo '{file_path}'.")
    except Exception as e:
        error_messages.append(f"Ocurrió un error inesperado durante la importación del CSV: {e}")

    return successful_imports, error_messages

def search_books_db(query, search_field="titulo"): # default to 'titulo'
    """Searches books where search_field CONTAINS query (case-insensitive).
    Returns a list of book dictionaries."""
    if not query:
        return []
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()

        allowed_search_fields = ["titulo", "autor", "genero", "ubicacion"] # Updated fields
        if search_field not in allowed_search_fields:
            print(f"Invalid search field: {search_field}. Defaulting to titulo.")
            search_field = "titulo"

        # Using LIKE for case-insensitive partial matching
        sql_query = f"SELECT id, titulo, autor, genero, ubicacion, cantidad_total FROM books WHERE {search_field} LIKE ?" # Updated columns

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

def get_available_book_count(book_id):
    """Calculates the number of available copies for a given book_id."""
    conn = None  # Ensure conn is defined in the outer scope for finally block
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        # Fetch total quantity of the book
        cursor.execute("SELECT cantidad_total FROM books WHERE id = ?", (book_id,))
        book_result = cursor.fetchone()
        if not book_result:
            print(f"Error: Book with ID {book_id} not found.")
            return 0
        cantidad_total = book_result[0]

        # Count active loans for the book
        cursor.execute("SELECT COUNT(*) FROM loans WHERE book_id = ?", (book_id,))
        active_loans_count = cursor.fetchone()[0]

        available_count = cantidad_total - active_loans_count
        return available_count if available_count > 0 else 0

    except sqlite3.Error as e:
        print(f"Database error in get_available_book_count for book_id {book_id}: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def loan_book_db(book_id, student_id, due_date_str, lending_student_leader_id):
    """Records a book loan in the 'loans' table."""
    if not student_manager.is_student_leader(lending_student_leader_id):
        print(f"Loan Error: Lending student {lending_student_leader_id} is not a leader or does not exist.")
        return False

    borrower = student_manager.get_student_by_id_db(student_id)
    if not borrower:
        print(f"Loan Error: Borrower student {student_id} does not exist.")
        return False

    conn = None # Ensure conn is defined for the finally block
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        # Check if book exists (though get_available_book_count also implicitly checks)
        cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
        if not cursor.fetchone():
            print(f"Loan Error: Book with ID {book_id} not found.")
            return False

        available_count = get_available_book_count(book_id)
        if available_count <= 0:
            print(f"Loan Error: No available copies of book ID {book_id} to loan.")
            return False

        loan_id = str(uuid.uuid4())
        loan_date_str = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO loans (loan_id, book_id, student_id, loan_date, due_date)
            VALUES (?, ?, ?, ?, ?)
        """, (loan_id, book_id, student_id, loan_date_str, due_date_str))
        conn.commit()

        print(f"Book '{book_id}' loaned to student '{student_id}' successfully. Loan ID: {loan_id}")
        return True

    except sqlite3.Error as e:
        print(f"Database error in loan_book_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def return_book_db(loan_id, student_leader_id):
    """Removes a loan record from the 'loans' table upon book return."""
    if not student_manager.is_student_leader(student_leader_id):
        print(f"Return Error: Returning student {student_leader_id} is not a leader or does not exist.")
        return False

    if not loan_id:
        print("Return Error: Loan ID cannot be empty.")
        return False

    conn = None # Ensure conn is defined for the finally block
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        cursor.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Loan ID '{loan_id}' returned successfully.")
            return True
        else:
            print(f"Return Error: No loan found with ID '{loan_id}', or failed to delete.")
            return False

    except sqlite3.Error as e:
        print(f"Database error in return_book_db for loan_id {loan_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_current_loans_db(ubicacion_filter=None):
    """Fetches current loans, joining with books and students tables.
    Filters by books.ubicacion if ubicacion_filter is provided.
    Returns list of dicts (loan info + book info + borrower_name)."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT l.loan_id, l.loan_date, l.due_date,
                   b.id as book_id, b.titulo, b.autor, b.genero, b.ubicacion,
                   s.id as student_id, s.name as borrower_name
            FROM loans l
            JOIN books b ON l.book_id = b.id
            JOIN students s ON l.student_id = s.id
        """
        params = []

        if ubicacion_filter and ubicacion_filter != "All":
            query += " WHERE b.ubicacion = ?"
            params.append(ubicacion_filter)

        query += " ORDER BY l.due_date ASC"

        cursor.execute(query, params)
        loans = [dict(row) for row in cursor.fetchall()]
        return loans
    except sqlite3.Error as e:
        print(f"Database error in get_current_loans_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_books_due_soon_db(days_threshold=7, ubicacion_filter=None):
    """Fetches loans due within days_threshold or already overdue.
    Joins with books and students. Filters by books.ubicacion.
    Returns list of dicts."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        threshold_date_str = (datetime.now().date() + timedelta(days=days_threshold)).strftime('%Y-%m-%d')

        query = """
            SELECT l.loan_id, l.loan_date, l.due_date,
                   b.id as book_id, b.titulo, b.autor, b.genero, b.ubicacion,
                   s.id as student_id, s.name as borrower_name
            FROM loans l
            JOIN books b ON l.book_id = b.id
            JOIN students s ON l.student_id = s.id
            WHERE l.due_date <= ?
        """
        params = [threshold_date_str]

        if ubicacion_filter and ubicacion_filter != "All":
            query += " AND b.ubicacion = ?"
            params.append(ubicacion_filter)

        query += " ORDER BY l.due_date ASC"

        cursor.execute(query, params)
        due_books = [dict(row) for row in cursor.fetchall()]
        return due_books
    except sqlite3.Error as e:
        print(f"Database error in get_books_due_soon_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def extend_loan_db(loan_id, days_to_extend=14):
    conn = None  # Initialize conn to None for the finally block
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()

        # Fetch the current due_date
        cursor.execute("SELECT due_date FROM loans WHERE loan_id = ?", (loan_id,))
        result = cursor.fetchone()

        if result is None:
            print(f"Error: Loan ID {loan_id} not found.")
            return False

        current_due_date_str = result[0]
        # Ensure current_due_date_str is not None and is a valid date string
        if not current_due_date_str:
            print(f"Error: Due date is missing for loan ID {loan_id}.")
            return False

        current_due_date_dt = datetime.strptime(current_due_date_str, '%Y-%m-%d').date()

        new_due_date_dt = current_due_date_dt + timedelta(days=days_to_extend)
        new_due_date_str = new_due_date_dt.strftime('%Y-%m-%d')

        # Update the due_date
        cursor.execute("UPDATE loans SET due_date = ? WHERE loan_id = ?", (new_due_date_str, loan_id))
        conn.commit()

        if cursor.rowcount == 0:
            # This case should ideally not be hit if the SELECT found the loan,
            # but as a safeguard for the UPDATE not affecting rows.
            print(f"Error: Failed to update loan ID {loan_id}. Loan might have been deleted concurrently.")
            return False

        return True

    except sqlite3.Error as e:
        print(f"Database error in extend_loan_db: {e}")
        # Consider specific error handling or logging here
        return False
    except ValueError as ve: # Handles potential strptime errors if date format is unexpected
        print(f"Date format error for loan ID {loan_id}: {ve}")
        return False
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
    # new_id = add_book_db("El Principito", "Antoine de Saint-Exupéry", "Salón A", "Fábula", 5)
    # if new_id:
    #     print(f"Libro añadido con ID: {new_id}")
    # else:
    #     print("Error al añadir libro.")

    # Test getting all books
    print("\nObteniendo todos los libros:")
    all_books = get_all_books_db()
    if all_books:
        for book in all_books:
            print(f"  Título: {book['titulo']}, Autor: {book['autor']}, Ubicación: {book['ubicacion']}, Cantidad: {book['cantidad_total']}")
    else:
        print("No se encontraron libros o ocurrió un error.")

    # Test getting books for a specific ubicacion
    print("\nObteniendo libros para Salón A:")
    salon_a_books = get_all_books_db(ubicacion_filter="Salón A")
    if salon_a_books:
        for book in salon_a_books:
            print(f"  Título: {book['titulo']}, Autor: {book['autor']}, Ubicación: {book['ubicacion']}")
    else:
        print("No se encontraron libros para Salón A.")

    # Test searching books
    print("\nBuscando libros con 'Principito' en título:")
    cat_books = search_books_db("Principito", "titulo")
    if cat_books:
        for book in cat_books:
            print(f"  Encontrado: {book['titulo']} por {book['autor']}")
    else:
        print("No se encontraron libros con 'Principito' en el título.")

    # Loan management functions below this point are not yet updated for the new schema
    # and will likely not work correctly. They are preserved as placeholders for future refactoring.
    # ... (original __main__ content for loan tests would be here, but needs significant changes) ...
    # Example Usage (for testing purposes)
    # First, ensure database and table are created by running db_setup.py or main.py
    # from database.db_setup import init_db
    # init_db() # Make sure db is initialized

    # Test adding a book
    print("Attempting to add a book...")
    # new_id = add_book_db("El Principito", "Antoine de Saint-Exupéry", "Salón A", "Fábula", 5)
    # if new_id:
    #     print(f"Libro añadido con ID: {new_id}")
    # else:
    #     print("Error al añadir libro.")

    # Test getting all books
    print("\nObteniendo todos los libros:")
    all_books = get_all_books_db()
    if all_books:
        for book in all_books:
            print(f"  Título: {book['titulo']}, Autor: {book['autor']}, Ubicación: {book['ubicacion']}, Cantidad: {book['cantidad_total']}")
    else:
        print("No se encontraron libros o ocurrió un error.")

    # Test getting books for a specific ubicacion
    print("\nObteniendo libros para Salón A:")
    salon_a_books = get_all_books_db(ubicacion_filter="Salón A")
    if salon_a_books:
        for book in salon_a_books:
            print(f"  Título: {book['titulo']}, Autor: {book['autor']}, Ubicación: {book['ubicacion']}")
    else:
        print("No se encontraron libros para Salón A.")

    # Test searching books
    print("\nBuscando libros con 'Principito' en título:")
    cat_books = search_books_db("Principito", "titulo")
    if cat_books:
        for book in cat_books:
            print(f"  Encontrado: {book['titulo']} por {book['autor']}")
    else:
        print("No se encontraron libros con 'Principito' en el título.")

    # Loan management functions below this point are not yet updated for the new schema
    # and will likely not work correctly. They are preserved as placeholders for future refactoring.
    # ... (original __main__ content for loan tests would be here, but needs significant changes) ...
    pass # Keep the if __name__ == '__main__': block for future direct script testing if needed
