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

def get_book_by_id_db(book_id):
    """Fetches a specific book by its ID from the database.
    Returns a dictionary representing the book if found, else None."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titulo, autor, genero, ubicacion, cantidad_total
            FROM books
            WHERE id = ?
        """, (book_id,))
        book_row = cursor.fetchone()
        if book_row:
            return dict(book_row)
        else:
            return None
    except sqlite3.Error as e:
        print(f"Database error in get_book_by_id_db for book_id {book_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def import_books_from_csv_db(file_path):
    """Reads a CSV file and adds books to the database using batch processing.
    Expected headers: Título, Autor, Género, Ubicación, Cantidad_Total.
    Returns a tuple: (successful_imports_count, error_messages_list)."""
    successful_imports = 0
    error_messages = []
    books_to_insert = []
    conn = None

    try:
        # Fetch valid locations first (outside transaction, as it reads DB)
        try:
            distinct_classrooms = student_manager.get_distinct_classrooms()
        except Exception as e_sm:
            error_messages.append(f"Error crítico al obtener clases existentes: {e_sm}. No se puede continuar con la importación.")
            return 0, error_messages

        fixed_locations = ["Biblioteca"]
        valid_locations = set(distinct_classrooms + fixed_locations)
        if not valid_locations and "Biblioteca" not in fixed_locations : # Corrected logic
             error_messages.append("No se pudieron determinar ubicaciones válidas (clases o Biblioteca). La importación no puede continuar sin ubicaciones válidas.")
             return 0, error_messages

        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            actual_headers_raw = reader.fieldnames
            if not actual_headers_raw:
                error_messages.append("El archivo CSV está vacío o no tiene encabezados.")
                return 0, error_messages

            actual_headers_normalized_map = {h.strip().lower(): h.strip() for h in actual_headers_raw}
            expected_fields_with_aliases = {
                "título": ["título", "titulo"], "autor": ["autor"],
                "género": ["género", "genero", "género literario", "genero literario"],
                "ubicación": ["ubicación", "ubicacion", "clase"],
                "cantidad_total": ["cantidad_total", "cantidad total", "cantidad", "cantidad de ejemplares", "cantidad de ejemplares vistos", "num ejemplares", "no. ejemplares"]
            }
            found_header_map = {}
            missing_canonical_headers = []

            for canonical, aliases in expected_fields_with_aliases.items():
                found_alias = False
                for alias in aliases:
                    if alias in actual_headers_normalized_map:
                        found_header_map[canonical] = actual_headers_normalized_map[alias]
                        found_alias = True
                        break
                if not found_alias:
                    missing_canonical_headers.append(canonical.capitalize())

            if missing_canonical_headers:
                error_messages.append(
                    f"El archivo CSV no contiene los encabezados requeridos o sus variantes aceptadas: {', '.join(missing_canonical_headers)}. "
                    f"Encabezados encontrados: {', '.join(actual_headers_raw)}"
                )
                return 0, error_messages

            for row_num, row in enumerate(reader, start=2):
                titulo = row.get(found_header_map["título"])
                autor = row.get(found_header_map["autor"])
                ubicacion_raw = row.get(found_header_map["ubicación"])
                cantidad_total_str = row.get(found_header_map["cantidad_total"])
                genero = row.get(found_header_map["género"])

                if not all([titulo, autor, ubicacion_raw, cantidad_total_str, genero]): # Check all required fields
                    error_messages.append(f"Fila {row_num}: Faltan campos requeridos (Título, Autor, Género, Ubicación, Cantidad_Total). Saltando fila.")
                    continue

                ubicacion = ubicacion_raw.strip()
                if ubicacion not in valid_locations:
                    error_messages.append(f"Fila {row_num}: La ubicación '{ubicacion}' no es válida. Debe ser una clase existente o 'Biblioteca'. Saltando fila.")
                    continue

                try:
                    cantidad_total_int = int(cantidad_total_str)
                    if cantidad_total_int <= 0:
                        error_messages.append(f"Fila {row_num}: 'Cantidad_Total' ({cantidad_total_str}) debe ser un número positivo. Usando 1 por defecto.")
                        cantidad_total_int = 1
                except ValueError:
                    error_messages.append(f"Fila {row_num}: 'Cantidad_Total' ({cantidad_total_str}) no es un número válido. Usando 1 por defecto.")
                    cantidad_total_int = 1

                book_id = generate_id() # Generate ID here
                books_to_insert.append((book_id, titulo, autor, genero, ubicacion, cantidad_total_int))

        if not books_to_insert:
            if not error_messages: # No books to insert and no errors means empty valid CSV or all rows skipped
                 error_messages.append("No se encontraron libros válidos para importar en el archivo CSV.")
            return 0, error_messages # Return early if no books were prepared

        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION;")

        try:
            cursor.executemany("""
                INSERT INTO books (id, titulo, autor, genero, ubicacion, cantidad_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, books_to_insert)
            conn.commit()
            successful_imports = len(books_to_insert)
        except sqlite3.Error as e:
            conn.rollback()
            error_messages.append(f"Error de base de datos durante la inserción en lote: {e}. No se importaron libros en este lote.")
            return 0, error_messages # Return 0 successful imports for this batch on DB error

    except FileNotFoundError:
        error_messages.append(f"Error: No se encontró el archivo '{file_path}'.")
    except Exception as e:
        error_messages.append(f"Ocurrió un error inesperado durante la importación del CSV: {e}")
        if conn: # If connection was established before this generic error
            conn.rollback() # Rollback any potential transaction
    finally:
        if conn:
            conn.close()

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
    """Calculates the number of available copies for a given book_id using a single optimized query."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        query = """
            SELECT b.cantidad_total - COALESCE(l.active_loans, 0) AS available_count
            FROM books b
            LEFT JOIN (
                SELECT book_id, COUNT(*) AS active_loans
                FROM loans
                GROUP BY book_id
            ) l ON b.id = l.book_id
            WHERE b.id = ?;
        """
        cursor.execute(query, (book_id,))
        result = cursor.fetchone()

        if result:
            return result[0] if result[0] > 0 else 0
        else:
            # This means the book_id was not found in the books table
            print(f"Info: Book with ID {book_id} not found for available count.")
            return 0

    except sqlite3.Error as e:
        print(f"Database error in get_available_book_count for book_id {book_id}: {e}")
        return 0 # Return 0 on error as a safe default
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
        # --- Add points for borrowing ---
        try:
            points_for_borrowing = 10 # Example: 10 points for borrowing a book
            cursor.execute("UPDATE students SET points = points + ? WHERE id = ?", (points_for_borrowing, student_id))
            print(f"Awarded {points_for_borrowing} points to student {student_id} for borrowing book {book_id}.") # Optional logging
        except sqlite3.Error as e:
            print(f"Error awarding points during loan: {e}")
            # This error should cause the transaction to be rolled back by the outer catch block if commit is not reached.
            raise # Re-raise the exception to ensure transaction rollback
        # --- End points for borrowing ---
        conn.commit()
        print(f"Book '{book_id}' loaned to student '{student_id}' successfully. Loan ID: {loan_id}")
        return True
    except sqlite3.Error as e:
        print(f"Database error in loan_book_db: {e}")
        if conn:
            conn.rollback() # Ensure rollback on SQLite error
        return False
    finally:
        if conn:
            conn.close()

def return_book_db(loan_id, student_leader_id, worksheet_submitted=False):
    """Removes a loan record from the 'loans' table upon book return and applies gamification points."""
    if not student_manager.is_student_leader(student_leader_id):
        print(f"Return Error: Returning student {student_leader_id} is not a leader or does not exist.")
        return False
    if not loan_id:
        print("Return Error: Loan ID cannot be empty.")
        return False
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION;") # Start transaction
        # --- Gamification Logic: Step 1 - Fetch loan details BEFORE deleting ---
        cursor.execute("SELECT student_id, due_date, early_return_bonus_applied FROM loans WHERE loan_id = ?", (loan_id,))
        loan_details = cursor.fetchone()
        if not loan_details:
            print(f"Error: Loan ID {loan_id} not found for gamification or return.")
            conn.rollback() # Rollback if loan not found
            return False
        student_id, due_date_str, early_bonus_applied_val = loan_details
        early_bonus_already_applied = bool(early_bonus_applied_val)
        points_to_award = 0
        # 1. Base points for returning
        points_to_award += 5
        # 2. Worksheet bonus
        if worksheet_submitted:
            points_to_award += 15
            # Mark worksheet as submitted for this loan
            cursor.execute("UPDATE loans SET worksheet_submitted = 1 WHERE loan_id = ?", (loan_id,))
        # 3. Early return bonus
        if due_date_str and not early_bonus_already_applied: # Check if bonus not already applied
            try:
                due_date_dt = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if datetime.now().date() < due_date_dt:
                    points_to_award += 5
                    # Mark bonus as applied for this loan
                    cursor.execute("UPDATE loans SET early_return_bonus_applied = 1 WHERE loan_id = ?", (loan_id,))
            except ValueError as ve:
                print(f"Warning: Could not parse due_date '{due_date_str}' for loan {loan_id} during gamification: {ve}")
        # Update student's total points
        if points_to_award > 0:
            cursor.execute("UPDATE students SET points = points + ? WHERE id = ?", (points_to_award, student_id))
        # --- Main Return Logic: Step 2 - Delete the loan record ---
        cursor.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))
        if cursor.rowcount == 0:
            # This means the loan was not found by the DELETE, which is unexpected if SELECT found it.
            # This could indicate a concurrent deletion or an issue with loan_id.
            print(f"Error: Failed to delete loan ID '{loan_id}'. Loan might have been deleted concurrently.")
            conn.rollback()
            return False
        conn.commit() # Commit all changes (gamification and deletion)
        print(f"Loan ID '{loan_id}' returned successfully. Points awarded: {points_to_award}")
        return True
    except sqlite3.Error as e:
        print(f"Database error in return_book_db for loan_id {loan_id}: {e}")
        if conn:
            conn.rollback()
        return False
    except ValueError as ve:
        print(f"Date format error for loan ID {loan_id} in return_book_db: {ve}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_current_loans_db(student_id_filter=None, ubicacion_filter=None):
    """Fetches current loans, joining with books and students tables.
    Filters by student_id (exact match) and/or books.ubicacion (exact match).
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
        conditions = []
        if student_id_filter:
            conditions.append("l.student_id = ?")
            params.append(student_id_filter)
        if ubicacion_filter and ubicacion_filter != "All": # "All" means no filter for ubicacion
            conditions.append("b.ubicacion = ?")
            params.append(ubicacion_filter)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY l.due_date ASC"
        cursor.execute(query, tuple(params))
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

def get_most_read_books_db(limit=10):
    """Fetches the most loaned books from the database.
    Returns a list of book dictionaries, ordered by loan count."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT b.id, b.titulo, b.autor, b.genero, b.ubicacion, b.cantidad_total, COUNT(l.book_id) as loan_count
            FROM books b
            JOIN loans l ON b.id = l.book_id
            GROUP BY l.book_id
            ORDER BY loan_count DESC
            LIMIT ?;
        """
        cursor.execute(query, (limit,))
        books = [dict(row) for row in cursor.fetchall()]
        return books
    except sqlite3.Error as e:
        print(f"Database error in get_most_read_books_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_new_releases_db(limit=10):
    """Fetches a list of new releases (currently random books) from the database.
    Returns a list of book dictionaries."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT id, titulo, autor, genero, ubicacion, cantidad_total, date_added
            FROM books
            ORDER BY date_added DESC
            LIMIT ?;
        """
        cursor.execute(query, (limit,))
        books = [dict(row) for row in cursor.fetchall()]
        return books
    except sqlite3.Error as e:
        print(f"Database error in get_new_releases_db: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_recommendations_db(limit=10):
    """Fetches a list of recommended books (currently random books) from the database.
    Returns a list of book dictionaries."""
    conn = None
    try:
        conn = sqlite3.connect(_get_resolved_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT id, titulo, autor, genero, ubicacion, cantidad_total
            FROM books
            ORDER BY RANDOM()
            LIMIT ?;
        """
        cursor.execute(query, (limit,))
        books = [dict(row) for row in cursor.fetchall()]
        return books
    except sqlite3.Error as e:
        print(f"Database error in get_recommendations_db: {e}")
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

    print("\n--- Testing get_current_loans_db with filters ---")
    # To test this properly, we would need to:
    # 1. Ensure some students exist (student_manager.add_student_db)
    # 2. Ensure some books exist (add_book_db)
    # 3. Create some loans (loan_book_db)

    # Example (conceptual, actual IDs would vary):
    # student_id_for_filter_test = student_manager.add_student_db("LoanFilterTester", "TestClass", "testpass")
    # book_id_for_loan_test1 = add_book_db("Loan Test Book 1", "Author", "TestClass", cantidad_total=1)
    # book_id_for_loan_test2 = add_book_db("Loan Test Book 2", "Author", "AnotherClass", cantidad_total=1)

    # if student_id_for_filter_test and book_id_for_loan_test1 and book_id_for_loan_test2:
    #     print(f"Test student ID: {student_id_for_filter_test}")
    #     # Loan one book to this student in TestClass
    #     loan_book_db(book_id_for_loan_test1, student_id_for_filter_test, "2024-12-31", "some_leader_id_if_needed_by_loan_book")

    #     # Loan another book (in AnotherClass) to a different student (or same, if logic allows)
    #     # For simplicity, let's assume another student exists or we add one
    #     other_student_id = student_manager.add_student_db("OtherLoanTester", "AnotherClass", "testpass")
    #     if other_student_id:
    #         loan_book_db(book_id_for_loan_test2, other_student_id, "2024-12-31", "some_leader_id")

    #     print("\nLoans for specific student:")
    #     loans_student_specific = get_current_loans_db(student_id_filter=student_id_for_filter_test)
    #     for loan in loans_student_specific:
    #         print(f"  Loan ID: {loan['loan_id']}, Book: {loan['titulo']}, Borrower: {loan['borrower_name']}")
    #     print(f"  Count: {len(loans_student_specific)}")

    #     print("\nLoans for specific ubicacion ('TestClass'):")
    #     loans_ubicacion_specific = get_current_loans_db(ubicacion_filter="TestClass")
    #     for loan in loans_ubicacion_specific:
    #         print(f"  Loan ID: {loan['loan_id']}, Book: {loan['titulo']}, Ubicacion: {loan['ubicacion']}")
    #     print(f"  Count: {len(loans_ubicacion_specific)}")

    #     print("\nLoans for specific student AND ubicacion:")
    #     loans_both_filters = get_current_loans_db(student_id_filter=student_id_for_filter_test, ubicacion_filter="TestClass")
    #     for loan in loans_both_filters:
    #         print(f"  Loan ID: {loan['loan_id']}, Book: {loan['titulo']}, Student: {loan['borrower_name']}, Ubicacion: {loan['ubicacion']}")
    #     print(f"  Count: {len(loans_both_filters)}")

    #     print("\nAll current loans (no filters):")
    #     all_loans_for_test = get_current_loans_db()
    #     print(f"  Total loans: {len(all_loans_for_test)}")
    # else:
    #     print("Could not create test students/books for loan filter tests.")

    pass # Keep the if __name__ == '__main__': block for future direct script testing if needed
