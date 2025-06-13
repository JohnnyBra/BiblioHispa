import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from database.db_setup import init_db
import book_manager
import student_manager
import auth_manager # Added for user management context
from tkinter import simpledialog # Added for password dialogs
from datetime import datetime, timedelta
import os # <--- ADD THIS LINE
from utils import get_data_path # Import the helper

# --- Global Styling & Theme ---
ctk.set_appearance_mode("Light")  # Options: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue") # Options: "blue" (default), "green", "dark-blue"

APP_FONT_FAMILY = "Arial" # A common sans-serif font
HEADING_FONT = (APP_FONT_FAMILY, 18, "bold")
SUBHEADING_FONT = (APP_FONT_FAMILY, 15, "bold")
BODY_FONT = (APP_FONT_FAMILY, 12)
BUTTON_FONT = (APP_FONT_FAMILY, 12, "bold")

# Define a simple color palette (using CTk's theme system primarily, but can define for specific widgets if needed)
# COLOR_PRIMARY = "#007ACC" # Blue
# COLOR_SECONDARY = "#F0F0F0" # Light Gray
# COLOR_ACCENT = "#FFA500" # Orange
# COLOR_TEXT = "#333333" # Dark Gray for light mode

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📚 Gestor de Biblioteca Escolar 🧸") # Translated
        self.geometry("950x750")

        # Initialize database
        init_db() # Ensure DB is set up early

        self.current_leader_id = None
        self.current_leader_classroom = None
        self.selected_user_id_manage_tab = None
        self.icon_cache = {}
        self.login_window = None # Placeholder for the login window

        self.withdraw() # Hide main window initially
        self.show_login_screen() # Show login screen first

    def show_login_screen(self):
        if self.login_window is not None and self.login_window.winfo_exists():
            self.login_window.focus()
            return

        self.login_window = ctk.CTkToplevel(self)
        self.login_window.title("Iniciar Sesión") # Translated
        self.login_window.geometry("350x250")
        self.login_window.transient(self)
        self.login_window.grab_set()
        self.login_window.protocol("WM_DELETE_WINDOW", self.quit_application)

        ctk.CTkLabel(self.login_window, text="¡Bienvenido/a! Por favor, inicia sesión", font=HEADING_FONT).pack(pady=20) # Translated

        frame = ctk.CTkFrame(self.login_window)
        frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frame, text="Usuario (Nombre):", font=BODY_FONT).grid(row=0, column=0, padx=5, pady=5, sticky="w") # Translated
        username_entry = ctk.CTkEntry(frame, font=BODY_FONT, width=200, placeholder_text="Nombre de usuario") # Translated placeholder
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Contraseña:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=8, sticky="w") # Translated
        password_entry = ctk.CTkEntry(frame, font=BODY_FONT, show="*", width=200, placeholder_text="Contraseña") # Translated placeholder
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        # Give focus to username entry initially
        username_entry.focus()
        # Bind Enter key to login action for password field for convenience
        password_entry.bind("<Return>", lambda event: login_action())


        error_label = ctk.CTkLabel(self.login_window, text="", text_color="red", font=BODY_FONT)
        error_label.pack(pady=(0,5))

        def login_action():
            username = username_entry.get()
            password = password_entry.get()
            if auth_manager.login(username, password):
                self.login_window.destroy()
                self.login_window = None
                self.initialize_main_app_ui()
            else:
                error_label.configure(text="Error de acceso. Usuario o contraseña incorrectos.") # Translated
                password_entry.delete(0, "end")
                username_entry.focus()

        button_frame = ctk.CTkFrame(self.login_window, fg_color="transparent")
        button_frame.pack(pady=10)

        login_button = ctk.CTkButton(button_frame, text="Acceder", font=BUTTON_FONT, command=login_action) # Translated
        login_button.pack(side="left", padx=10)

        quit_button = ctk.CTkButton(button_frame, text="Salir", font=BUTTON_FONT, command=self.quit_application, fg_color="gray50", hover_color="gray60") # Translated
        quit_button.pack(side="left", padx=10)

        # Center the login window
        self.login_window.update_idletasks() # Update geometry
        x = self.winfo_screenwidth() // 2 - self.login_window.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.login_window.winfo_height() // 2
        self.login_window.geometry(f"+{x}+{y}")


    def initialize_main_app_ui(self):
        # Main TabView
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=15, pady=15)

        self.manage_books_tab = self.tab_view.add("📖 Gestionar Libros") # Translated
        self.view_books_tab = self.tab_view.add("📚 Ver Libros") # Translated
        self.manage_students_tab = self.tab_view.add("🧑‍🎓 Gestionar Alumnos") # Translated
        self.manage_loans_tab = self.tab_view.add("🔄 Gestionar Préstamos") # Translated

        # Conditionally add User Management Tab
        if auth_manager.is_admin():
            self.manage_users_tab = self.tab_view.add("👤 Gestionar Usuarios") # Translated
            if hasattr(self, 'setup_manage_users_tab'):
                 self.setup_manage_users_tab()
            else:
                print("Error: El método setup_manage_users_tab no se encontró pero se esperaba para el admin.") # Translated
        else:
            # Ensure self.manage_users_tab is None or handled if it might exist from a previous session/state
            self.manage_users_tab = None


        # Populate Tabs (ensure setup methods exist)
        if hasattr(self, 'setup_manage_books_tab'): self.setup_manage_books_tab()
        if hasattr(self, 'setup_view_books_tab'): self.setup_view_books_tab()
        if hasattr(self, 'setup_manage_students_tab'): self.setup_manage_students_tab() # Original student management
        if hasattr(self, 'setup_manage_loans_tab'): self.setup_manage_loans_tab()

        # Deiconify (show) the main window now that UI is initialized
        self.deiconify()

    def quit_application(self):
        # Perform any cleanup if necessary
        if self.login_window is not None and self.login_window.winfo_exists():
            self.login_window.destroy()
        self.quit() # Properly exits the Tkinter mainloop

    def load_icon(self, icon_name, size=(20,20)):
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]

        relative_icon_path = os.path.join("assets", "icons", f"{icon_name}.png")
        try:
            icon_path = get_data_path(relative_icon_path)

            if not os.path.exists(icon_path):
                # Fallback: try to create assets/icons dir for placeholder, assumes CWD is classroom_library_app for dev
                dev_placeholder_dir = os.path.join(os.path.abspath("."), "assets", "icons")
                os.makedirs(dev_placeholder_dir, exist_ok=True)
                print(f"Warning: Icon {icon_path} (from {relative_icon_path}) not found. Creating placeholder.")
                placeholder_image = Image.new("RGBA", size, (200, 200, 200, 50))
                img_ctk = ctk.CTkImage(light_image=placeholder_image, dark_image=placeholder_image, size=size)
                self.icon_cache[icon_name] = img_ctk # Cache placeholder
                return img_ctk

            img = Image.open(icon_path)
            img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            self.icon_cache[icon_name] = img_ctk
            return img_ctk
        except Exception as e: # Catch broader exceptions for path issues or PIL errors
            print(f"Error loading icon {relative_icon_path}: {e}")
            # Attempt to return a placeholder on any error during load
            try:
                placeholder_image = Image.new("RGBA", size, (220, 220, 220, 70)) # Slightly different placeholder
                img_ctk = ctk.CTkImage(light_image=placeholder_image, dark_image=placeholder_image, size=size)
                self.icon_cache[icon_name] = img_ctk # Cache placeholder
                return img_ctk
            except Exception as pe: # Placeholder creation error
                print(f"Critical error: Could not create placeholder icon for {icon_name}: {pe}")
                return None


    def setup_manage_books_tab(self):
        tab = self.manage_books_tab
        tab.configure(fg_color=("#F0F8FF", "#2A2D2E")) # AliceBlue for light, dark gray for dark

        # --- Add Book Form ---
        add_book_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_book_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_book_frame, text="✨ ¡Añade un Nuevo Libro Mágico! ✨", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15)) # Translated

        ctk.CTkLabel(add_book_frame, text="Título:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.title_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., El Principito") # Translated
        self.title_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="Autor:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.author_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Antoine de Saint-Exupéry") # Translated
        self.author_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="Género:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=8, sticky="w")
        self.genero_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Fábula, Ciencia Ficción") # Translated
        self.genero_entry.grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="Ubicación:", font=BODY_FONT).grid(row=4, column=0, padx=10, pady=8, sticky="w")
        self.ubicacion_combobox = ctk.CTkComboBox(add_book_frame, values=["Salón A", "Salón B", "Salón C", "Biblioteca"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT) # Values may need translation later
        self.ubicacion_combobox.grid(row=4, column=1, padx=10, pady=8, sticky="ew")
        self.ubicacion_combobox.set("Salón A")

        ctk.CTkLabel(add_book_frame, text="Cantidad Total:", font=BODY_FONT).grid(row=5, column=0, padx=10, pady=8, sticky="w")
        self.cantidad_total_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., 1") # Translated
        self.cantidad_total_entry.grid(row=5, column=1, padx=10, pady=8, sticky="ew")

        add_book_icon = self.load_icon("add_book")
        add_button = ctk.CTkButton(add_book_frame, text="Añadir Libro a la Biblioteca", image=add_book_icon, font=BUTTON_FONT, command=self.add_book_ui, corner_radius=8)
        add_button.grid(row=6, column=0, columnspan=2, pady=15, padx=10, sticky="ew")
        add_book_frame.columnconfigure(1, weight=1)

        # --- Import CSV Section ---
        import_csv_frame = ctk.CTkFrame(tab, corner_radius=10)
        import_csv_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(import_csv_frame, text="📤 Importar Libros desde Archivo CSV 📤", font=HEADING_FONT).pack(pady=(10,15)) # Translated
        import_csv_icon = self.load_icon("import_csv")
        import_button = ctk.CTkButton(import_csv_frame, text="Seleccionar Archivo CSV", image=import_csv_icon, font=BUTTON_FONT, command=self.import_csv_ui, corner_radius=8) # Translated
        import_button.pack(pady=10, padx=60, fill="x")


    def add_book_ui(self):
        titulo = self.title_entry.get()
        autor = self.author_entry.get()
        genero = self.genero_entry.get() # New field
        ubicacion = self.ubicacion_combobox.get() # Renamed, was classroom
        cantidad_total_str = self.cantidad_total_entry.get()

        if not titulo or not autor or not ubicacion or not cantidad_total_str:
            messagebox.showerror("¡Un momento! 🚧", "¡Uy! Título, Autor, Ubicación y Cantidad Total son necesarios.") # Translated
            return

        try:
            cantidad_total = int(cantidad_total_str)
            if cantidad_total <= 0:
                messagebox.showerror("Error de Entrada", "La Cantidad Total debe ser un número positivo.") # Translated
                return
        except ValueError:
            messagebox.showerror("Error de Entrada", "La Cantidad Total debe ser un número válido.") # Translated
            return

        # Assuming book_manager.add_book_db signature is (titulo, autor, ubicacion, genero=None, cantidad_total=1)
        book_id = book_manager.add_book_db(titulo, autor, ubicacion, genero if genero else None, cantidad_total)

        if book_id:
            messagebox.showinfo("¡Éxito! 🎉", f"¡Excelente! El libro '{titulo}' ha sido añadido correctamente.") # Translated
            self.title_entry.delete(0, "end")
            self.author_entry.delete(0, "end")
            self.genero_entry.delete(0, "end")
            # self.ubicacion_combobox.set("Salón A") # Reset to default or clear
            self.cantidad_total_entry.delete(0, "end")
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
            if hasattr(self, 'refresh_loan_related_combos_and_lists'): self.refresh_loan_related_combos_and_lists()
        else:
            messagebox.showerror("¡Oh no! 😟", "Algo salió mal al añadir el libro.") # Translated

    def import_csv_ui(self): # Re-implemented
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV para importar", # Translated
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")) # Translated
        )
        if not file_path:
            return

        # The os.makedirs("assets") line was likely for a sample CSV, not needed for general import.
        # If a specific assets folder for user-provided CSVs was intended, that's a different feature.

        success_count, errors = book_manager.import_books_from_csv_db(file_path)

        summary_message = f"Resumen de Importación CSV:\n\nLibros importados con éxito: {success_count}." # Translated
        if errors:
            summary_message += "\n\nErrores encontrados:\n" + "\n".join(f"- {e}" for e in errors)
            messagebox.showwarning("Importación Parcialmente Exitosa", summary_message) # Translated
        else:
            messagebox.showinfo("Importación Exitosa", summary_message) # Translated

        if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
        if hasattr(self, 'refresh_loan_related_combos_and_lists'): self.refresh_loan_related_combos_and_lists()


    def setup_view_books_tab(self):
        tab = self.view_books_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B"))

        controls_frame = ctk.CTkFrame(tab, corner_radius=10)
        controls_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(controls_frame, text="Filtrar por Ubicación:", font=BODY_FONT).grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")
        self.view_ubicacion_filter = ctk.CTkComboBox(controls_frame, values=["Todos", "Salón A", "Salón B", "Salón C", "Biblioteca"], command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150) # Translated "All"
        self.view_ubicacion_filter.grid(row=0, column=1, padx=5, pady=10)
        self.view_ubicacion_filter.set("Todos") # Translated "All"

        # Status filter removed
        # ctk.CTkLabel(controls_frame, text="Filter by Status:", font=BODY_FONT).grid(row=0, column=2, padx=(10,5), pady=10, sticky="w")
        # self.view_status_filter = ctk.CTkComboBox(controls_frame, values=["All", "available", "borrowed"], command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150)
        # self.view_status_filter.grid(row=0, column=3, padx=5, pady=10)
        # self.view_status_filter.set("All")

        controls_frame.columnconfigure(1, weight=1) # Allow combobox to take some space (adjust column index if needed)


        search_frame = ctk.CTkFrame(tab, corner_radius=10)
        search_frame.pack(pady=(0,15), padx=15, fill="x")

        ctk.CTkLabel(search_frame, text="🔍 Buscar Libros:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=10) # Translated
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Escribe para buscar por título o autor...", font=BODY_FONT, width=300) # Translated
        self.search_entry.pack(side="left", padx=(0,10), pady=10, expand=True, fill="x")

        search_icon = self.load_icon("search")
        search_button = ctk.CTkButton(search_frame, text="Buscar", image=search_icon, font=BUTTON_FONT, command=self.search_books_ui, width=100, corner_radius=8) # Translated
        search_button.pack(side="left", padx=(0,5), pady=10)

        clear_search_icon = self.load_icon("clear_search")
        clear_search_button = ctk.CTkButton(search_frame, text="Limpiar", image=clear_search_icon, font=BUTTON_FONT, command=self.clear_search_ui, width=80, corner_radius=8, fg_color="gray50", hover_color="gray60") # Translated
        clear_search_button.pack(side="left", padx=(0,10), pady=10)

        self.book_list_frame = ctk.CTkScrollableFrame(tab, label_text="Nuestra Maravillosa Colección de Libros", label_font=HEADING_FONT, corner_radius=10) # Translated
        self.book_list_frame.pack(expand=True, fill="both", padx=15, pady=(0,15))

        self.refresh_book_list_ui()

    def refresh_book_list_ui(self, books_to_display=None):
        for widget in self.book_list_frame.winfo_children():
            widget.destroy()

        ubicacion_val = self.view_ubicacion_filter.get() if hasattr(self, 'view_ubicacion_filter') else "Todos" # Changed variable name and default

        if books_to_display is None:
            books = book_manager.get_all_books_db(
                ubicacion_filter=ubicacion_val if ubicacion_val != "Todos" else None # Changed "All" to "Todos"
            )
        else:
            books = books_to_display

        if not books:
            no_books_label = ctk.CTkLabel(self.book_list_frame, text="No se encontraron libros. Intenta cambiar los filtros o añadir nuevos libros.", font=BODY_FONT) # Translated
            no_books_label.pack(pady=30, padx=10)
            return

        for i, book in enumerate(books):
            book_item_frame = ctk.CTkFrame(self.book_list_frame, corner_radius=6, border_width=1, border_color=("gray75", "gray30"))
            book_item_frame.pack(fill="x", pady=8, padx=8)
            book_item_frame.columnconfigure(1, weight=1)

            available_count = book_manager.get_available_book_count(book['id'])
            total_count = book.get('cantidad_total', 0)

            availability_text = f"Disponible: {available_count} / {total_count}"
            availability_color = "green" if available_count > 0 else "red"

            status_label = ctk.CTkLabel(book_item_frame, text=availability_text, font=(APP_FONT_FAMILY, 11, "bold"), text_color=availability_color, anchor="e")
            status_label.grid(row=0, column=2, padx=(5,10), pady=(5,0), sticky="ne")

            title_label = ctk.CTkLabel(book_item_frame, text=f"{book.get('titulo', 'N/A')}", font=(APP_FONT_FAMILY, 14, "bold"), anchor="w")
            title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5,2), sticky="w")

            author_label = ctk.CTkLabel(book_item_frame, text=f"por {book.get('autor', 'N/A')}", font=(APP_FONT_FAMILY, 11, "italic"), anchor="w")
            author_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky="w")

            info_text = f"Ubicación: {book.get('ubicacion', 'N/A')}"
            if book.get('genero'):
                info_text += f"  |  Género: {book.get('genero')}"
            info_label = ctk.CTkLabel(book_item_frame, text=info_text, font=(APP_FONT_FAMILY, 10), anchor="w")
            info_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(0,8), sticky="w")

            # Removed image_path display for now as it's not in the new schema

    def search_books_ui(self):
        query = self.search_entry.get()
        if not query:
            self.refresh_book_list_ui() # Show all if query is empty
            return

        # Search by title and author, then combine results
        # book_manager.search_books_db now defaults to "titulo" if field not specified
        results_titulo = book_manager.search_books_db(query, search_field="titulo")
        results_autor = book_manager.search_books_db(query, search_field="autor")
        # Potentially search by genero and ubicacion as well if desired by product
        # results_genero = book_manager.search_books_db(query, search_field="genero")
        # results_ubicacion = book_manager.search_books_db(query, search_field="ubicacion")

        # Combine results, avoiding duplicates
        combined_results = {book['id']: book for book in results_titulo}
        for book in results_autor:
            combined_results[book['id']] = book
        # for book in results_genero:
        #     combined_results[book['id']] = book
        # for book in results_ubicacion:
        #     combined_results[book['id']] = book

        self.refresh_book_list_ui(books_to_display=list(combined_results.values()))

    def clear_search_ui(self):
        self.search_entry.delete(0, "end")
        self.refresh_book_list_ui()

    def setup_manage_students_tab(self):
        tab = self.manage_students_tab
        tab.configure(fg_color=("#FAF0E6", "#2E2B28"))

        add_student_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_student_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_student_frame, text="🌟 ¡Añade un Nuevo Alumno Estrella! 🌟", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15)) # Translated

        ctk.CTkLabel(add_student_frame, text="Nombre del Alumno:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=8, sticky="w") # Translated
        self.student_name_entry = ctk.CTkEntry(add_student_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Luna Lovegood") # Translated
        self.student_name_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_student_frame, text="Clase:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=8, sticky="w") # Translated "Classroom" to "Clase"
        self.student_classroom_combo = ctk.CTkComboBox(add_student_frame, values=["Clase A", "Clase B", "Clase C", "Clase D"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT) # Translated values
        self.student_classroom_combo.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        self.student_classroom_combo.set("Clase A") # Translated

        ctk.CTkLabel(add_student_frame, text="Rol:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=8, sticky="w") # Translated
        self.student_role_combo = ctk.CTkComboBox(add_student_frame, values=["alumno", "líder", "admin"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT) # Translated values
        self.student_role_combo.grid(row=3, column=1, padx=10, pady=8, sticky="ew")
        self.student_role_combo.set("alumno") # Translated
        add_student_frame.columnconfigure(1, weight=1)

        add_student_icon = self.load_icon("add_student")
        add_student_button = ctk.CTkButton(add_student_frame, text="Añadir Alumno", image=add_student_icon, font=BUTTON_FONT, command=self.add_student_ui, corner_radius=8) # Translated
        add_student_button.grid(row=4, column=0, columnspan=2, pady=15, padx=10, sticky="ew")

        students_list_frame_container = ctk.CTkFrame(tab, corner_radius=10)
        students_list_frame_container.pack(pady=(0,15), padx=15, expand=True, fill="both")

        list_header_frame = ctk.CTkFrame(students_list_frame_container, fg_color="transparent")
        list_header_frame.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(list_header_frame, text="🎓 Nuestros Increíbles Alumnos 🎓", font=HEADING_FONT).pack(side="left", padx=10, pady=5) # Translated
        refresh_students_icon = self.load_icon("refresh")
        refresh_students_button = ctk.CTkButton(list_header_frame, text="Actualizar", image=refresh_students_icon, font=BUTTON_FONT, command=self.refresh_student_list_ui, width=100, corner_radius=8) # Translated
        refresh_students_button.pack(side="right", padx=10, pady=5)

        self.students_list_frame = ctk.CTkScrollableFrame(students_list_frame_container, label_text="")
        self.students_list_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.refresh_student_list_ui()

    def add_student_ui(self):
        name = self.student_name_entry.get()
        classroom = self.student_classroom_combo.get()
        role = self.student_role_combo.get()

        if not name or not classroom or not role:
            messagebox.showerror("¡Un Segundo! 🚦", "¡Uy! Nombre, Clase y Rol son requeridos para añadir un alumno.") # Translated
            return

        student_id = student_manager.add_student_db(name, classroom, role) # Assuming student_manager.add_student_db handles 'alumno', 'líder'
        if student_id:
            messagebox.showinfo("¡Fantástico! ✨", f"¡El alumno '{name}' se ha unido al listado!") # Translated
            self.student_name_entry.delete(0, "end")
            self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'):
                 self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("¡Oh No! 💔", "Algo salió mal al añadir el alumno. Revisa la consola.") # Translated

    def refresh_student_list_ui(self):
        if not hasattr(self, 'students_list_frame'):
            return

        for widget in self.students_list_frame.winfo_children():
            widget.destroy()

        students = student_manager.get_students_db()

        if not students:
            no_students_label = ctk.CTkLabel(self.students_list_frame, text="No se encontraron alumnos.", font=ctk.CTkFont(size=14)) # Translated
            no_students_label.pack(pady=20)
            return

        for i, student in enumerate(students):
            student_item_frame = ctk.CTkFrame(self.students_list_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            student_item_frame.pack(fill="x", pady=(2,0), padx=5)
            details = f"Nombre: {student['name']} ({student['role']})\nClase: {student['classroom']} | ID: {student['id']}" # Translated
            label = ctk.CTkLabel(student_item_frame, text=details, justify="left", anchor="w")
            label.pack(pady=5, padx=10, fill="x", expand=True)

    def setup_manage_loans_tab(self):
        tab = self.manage_loans_tab
        tab.configure(fg_color=("#E0FFFF", "#2C3E50")) # LightCyan for light, dark slate blue for dark

        # Dictionaries to map display names to IDs
        self.leader_student_map = {}
        self.lend_book_map = {}
        self.borrower_student_map = {}
        self.return_book_map = {}

        # --- Student Leader Selection ---
        leader_selection_frame = ctk.CTkFrame(tab, corner_radius=10)
        leader_selection_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(leader_selection_frame, text="👑 Seleccionar Líder Estudiantil Actuante:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=10) # Translated
        self.leader_selector_combo = ctk.CTkComboBox(leader_selection_frame, width=300, font=BODY_FONT, dropdown_font=BODY_FONT, command=self.on_leader_selected)
        self.leader_selector_combo.pack(side="left", padx=(0,10), pady=10, expand=True)

        # --- Main content frame for loans (will split into left and right) ---
        main_loan_content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_loan_content_frame.pack(expand=True, fill="both", padx=15, pady=(0,15))

        left_frame = ctk.CTkFrame(main_loan_content_frame, corner_radius=10)
        left_frame.pack(side="left", fill="y", padx=(0,10), pady=0, anchor="n")

        # --- Lend Book Section ---
        lend_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        lend_frame.pack(pady=(0,10), padx=10, fill="x")
        ctk.CTkLabel(lend_frame, text="➡️ Prestar un Libro", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w") # Translated

        ctk.CTkLabel(lend_frame, text="Libro:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=8, sticky="w") # Translated
        self.lend_book_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.lend_book_combo.grid(row=1, column=1, padx=5, pady=8, sticky="ew")

        ctk.CTkLabel(lend_frame, text="Prestatario:", font=BODY_FONT).grid(row=2, column=0, padx=5, pady=8, sticky="w") # Translated "Borrower"
        self.borrower_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.borrower_combo.grid(row=2, column=1, padx=5, pady=8, sticky="ew")

        ctk.CTkLabel(lend_frame, text="Fecha de Devolución:", font=BODY_FONT).grid(row=3, column=0, padx=5, pady=8, sticky="w") # Translated "Due Date"
        self.due_date_entry = ctk.CTkEntry(lend_frame, placeholder_text=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), width=280, font=BODY_FONT)
        self.due_date_entry.grid(row=3, column=1, padx=5, pady=8, sticky="ew")
        lend_frame.columnconfigure(1, weight=1)

        lend_icon = self.load_icon("lend_book")
        lend_button = ctk.CTkButton(lend_frame, text="Prestar Libro", image=lend_icon, font=BUTTON_FONT, command=self.lend_book_ui, corner_radius=8) # Translated
        lend_button.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        # --- Return Book Section ---
        return_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        return_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(return_frame, text="⬅️ Devolver un Libro", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w") # Translated

        ctk.CTkLabel(return_frame, text="Libro Prestado:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=8, sticky="w") # Translated "Book:" to "Libro Prestado:" for clarity
        self.return_book_combo = ctk.CTkComboBox(return_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.return_book_combo.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        return_frame.columnconfigure(1, weight=1)

        return_icon = self.load_icon("return_book")
        return_button = ctk.CTkButton(return_frame, text="Devolver Libro", image=return_icon, font=BUTTON_FONT, command=self.return_book_ui, corner_radius=8) # Translated
        return_button.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

        right_frame = ctk.CTkFrame(main_loan_content_frame, fg_color="transparent")
        right_frame.pack(side="left", expand=True, fill="both", padx=(10,0), pady=0)

        loans_display_tabview = ctk.CTkTabview(right_frame, corner_radius=8)
        loans_display_tabview.pack(expand=True, fill="both")

        current_loans_tab = loans_display_tabview.add("Préstamos Actuales") # Translated
        reminders_tab = loans_display_tabview.add("⏰ Recordatorios") # Translated
        current_loans_tab.configure(fg_color=("#F5F5F5", "#343638"))
        reminders_tab.configure(fg_color=("#FFF0F5", "#383436"))


        self.current_loans_label = ctk.CTkLabel(current_loans_tab, text="Préstamos Actuales en [Clase del Líder]", font=SUBHEADING_FONT) # Translated
        self.current_loans_label.pack(pady=10, padx=10)
        self.current_loans_frame = ctk.CTkScrollableFrame(current_loans_tab, label_text="", corner_radius=6)
        self.current_loans_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        self.reminders_label = ctk.CTkLabel(reminders_tab, text="Libros Próximos a Vencer/Vencidos en [Clase del Líder]", font=SUBHEADING_FONT) # Translated
        self.reminders_label.pack(pady=10, padx=10)
        self.reminders_frame = ctk.CTkScrollableFrame(reminders_tab, label_text="", corner_radius=6)
        self.reminders_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        self.refresh_leader_selector_combo() # Populate initially, which then calls on_leader_selected

    def refresh_leader_selector_combo(self):
        leaders = student_manager.get_students_db(role_filter='leader')
        self.leader_student_map = {f"{s['name']} ({s['classroom']})": s['id'] for s in leaders} # classroom here refers to student's classroom
        leader_names = list(self.leader_student_map.keys())

        current_value = self.leader_selector_combo.get()

        self.leader_selector_combo.configure(values=leader_names if leader_names else ["No hay líderes"]) # Translated

        if leader_names:
            if current_value in leader_names:
                self.leader_selector_combo.set(current_value)
            else:
                self.leader_selector_combo.set(leader_names[0])
            self.on_leader_selected(self.leader_selector_combo.get())
        else:
            self.leader_selector_combo.set("No hay líderes") # Translated
            self.on_leader_selected(None)

    def on_leader_selected(self, selected_leader_display_name):
        if selected_leader_display_name and selected_leader_display_name != "No hay líderes": # Translated
            self.current_leader_id = self.leader_student_map.get(selected_leader_display_name)
            leader_details = student_manager.get_student_by_id_db(self.current_leader_id)
            if leader_details:
                self.current_leader_classroom = leader_details['classroom'] # This is the leader's classroom, used as ubicacion for books
                self.current_loans_label.configure(text=f"Préstamos Actuales en {self.current_leader_classroom}") # Translated
                self.reminders_label.configure(text=f"Libros Próximos a Vencer/Vencidos en {self.current_leader_classroom}") # Translated
                self.lend_book_combo.configure(state="normal")
                self.borrower_combo.configure(state="normal")
                self.return_book_combo.configure(state="normal")
            else:
                self.current_leader_id = None
                self.current_leader_classroom = None
        else:
            self.current_leader_id = None
                self.current_leader_classroom = None # Used as ubicacion for books

        self.refresh_loan_related_combos_and_lists()

    def update_loan_section_for_no_leader(self):
        self.current_loans_label.configure(text="Préstamos Actuales (Seleccione un Líder)") # Translated
        self.reminders_label.configure(text="Recordatorios (Seleccione un Líder)") # Translated
        self.lend_book_combo.configure(values=["Seleccione líder"], state="disabled") # Translated
        self.borrower_combo.configure(values=["Seleccione líder"], state="disabled") # Translated
        self.return_book_combo.configure(values=["Seleccione líder"], state="disabled") # Translated
        self.lend_book_combo.set("Seleccione líder") # Translated
        self.borrower_combo.set("Seleccione líder") # Translated
        self.return_book_combo.set("Seleccione líder") # Translated

        for widget in self.current_loans_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.current_loans_frame, text="Por favor, seleccione un líder estudiantil para gestionar préstamos.").pack(pady=20, padx=10) # Translated
        for widget in self.reminders_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.reminders_frame, text="Por favor, seleccione un líder estudiantil para ver recordatorios.").pack(pady=20, padx=10) # Translated

    def refresh_loan_related_combos_and_lists(self):
        if not self.current_leader_id or not self.current_leader_classroom: # current_leader_classroom is the ubicacion
            self.update_loan_section_for_no_leader()
            return

        # Populate Lend Book ComboBox
        # Books from the selected leader's ubicacion
        all_books_in_ubicacion = book_manager.get_all_books_db(ubicacion_filter=self.current_leader_classroom)

        lend_book_display_names = []
        self.lend_book_map = {}
        for book in all_books_in_ubicacion:
            available_count = book_manager.get_available_book_count(book['id'])
            if available_count > 0:
                display_text = f"{book.get('titulo', 'N/A')} (by {book.get('autor', 'N/A')}) - Disp: {available_count}"
                self.lend_book_map[display_text] = book['id']
                lend_book_display_names.append(display_text)

        self.lend_book_combo.configure(values=lend_book_display_names if lend_book_display_names else ["No available books"])
        self.lend_book_combo.set(lend_book_display_names[0] if lend_book_display_names else "No available books")

        # Populate Borrower ComboBox
        students_in_classroom = student_manager.get_students_by_classroom_db(self.current_leader_classroom) # Assuming classroom is equivalent to ubicacion for students
        self.borrower_student_map = {s['name']: s['id'] for s in students_in_classroom}
        borrower_names = list(self.borrower_student_map.keys())
        self.borrower_combo.configure(values=borrower_names if borrower_names else ["No students in class"])
        self.borrower_combo.set(borrower_names[0] if borrower_names else "No students in class")

        # Populate Return Book ComboBox
        # Using current_leader_classroom as the ubicacion_filter for get_current_loans_db
        active_loans_in_ubicacion = book_manager.get_current_loans_db(ubicacion_filter=self.current_leader_classroom)
        self.return_book_map = {}
        return_book_display_names = []
        for loan in active_loans_in_ubicacion:
            # loan dict now contains 'titulo', 'borrower_name', 'due_date', 'loan_id'
            display_text = f"{loan.get('titulo', 'N/A')} (Borrower: {loan.get('borrower_name', 'N/A')}) Due: {loan.get('due_date', 'N/A')}"
            self.return_book_map[display_text] = loan['loan_id'] # Map display text to loan_id
            return_book_display_names.append(display_text)

        self.return_book_combo.configure(values=return_book_display_names if return_book_display_names else ["No borrowed books"])
        self.return_book_combo.set(return_book_display_names[0] if return_book_display_names else "No borrowed books")

        self.refresh_current_loans_list()
        self.refresh_reminders_list()

    def lend_book_ui(self):
        if not self.current_leader_id:
            messagebox.showerror("Leader Not Selected", "Please select a student leader first.")
            return

        book_display_name = self.lend_book_combo.get()
        borrower_display_name = self.borrower_combo.get()
        due_date_str = self.due_date_entry.get()

        if book_display_name == "No available books" or borrower_display_name == "No students in class":
            messagebox.showerror("Input Error", "Please select a valid book and borrower.")
            return

        if not due_date_str:
            messagebox.showerror("Input Error", "Due date is required.")
            return
        try:
            # Validate due_date_str format, but allow it to be in the past for flexibility if needed,
            # though typically it should be in the future.
            datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format for Due Date. Use YYYY-MM-DD.")
            return

        book_id = self.lend_book_map.get(book_display_name)
        borrower_id = self.borrower_student_map.get(borrower_display_name)

        if not book_id or not borrower_id:
            messagebox.showerror("Internal Error", "Could not resolve book or borrower ID from selection.")
            return

        # Call the updated book_manager.loan_book_db
        success = book_manager.loan_book_db(book_id, borrower_id, due_date_str, self.current_leader_id)

        if success:
            messagebox.showinfo("Success", f"Book '{book_display_name.split(' (by ')[0]}' loaned to {borrower_display_name}.")
            self.due_date_entry.delete(0, 'end') # Clear entry for next use
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
        else:
            messagebox.showerror("Loan Failed", "Failed to loan book. Check console (book might not be available or other DB error).")

    def return_book_ui(self):
        if not self.current_leader_id:
            messagebox.showerror("Leader Not Selected", "Please select a student leader first.")
            return

        return_loan_display_name = self.return_book_combo.get()
        if return_loan_display_name == "No borrowed books":
            messagebox.showerror("Input Error", "Please select a loan to return.")
            return

        loan_id = self.return_book_map.get(return_loan_display_name) # Get loan_id
        if not loan_id:
            messagebox.showerror("Internal Error", "Could not resolve loan ID for return from selection.")
            return

        # Call the updated book_manager.return_book_db with loan_id
        success = book_manager.return_book_db(loan_id, self.current_leader_id)

        if success:
            messagebox.showinfo("Success", f"Loan returned successfully.")
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
        else:
            messagebox.showerror("Return Failed", "Failed to return book. Check console (loan ID might be invalid or other DB error).")

    def refresh_current_loans_list(self):
        for widget in self.current_loans_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom:
             ctk.CTkLabel(self.current_loans_frame, text="Select a leader to view loans.").pack(pady=20, padx=10)
             return

        # Use current_leader_classroom as ubicacion_filter
        loans = book_manager.get_current_loans_db(ubicacion_filter=self.current_leader_classroom)
        if not loans:
            ctk.CTkLabel(self.current_loans_frame, text=f"No books currently loaned out in {self.current_leader_classroom}.").pack(pady=20, padx=10)
            return

        for i, loan in enumerate(loans): # loan is now a dict from get_current_loans_db
            item_frame = ctk.CTkFrame(self.current_loans_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            item_frame.pack(fill="x", pady=(2,0), padx=5)
            details = f"Book: {loan.get('titulo', 'N/A')} (Autor: {loan.get('autor', 'N/A')})\n" \
                      f"Borrower: {loan.get('borrower_name', 'Unknown Student')}\n" \
                      f"Loaned: {loan.get('loan_date', 'N/A')} | Due: {loan.get('due_date', 'N/A')} (ID: {loan.get('loan_id', '')[:8]}...)"
            label = ctk.CTkLabel(item_frame, text=details, justify="left", anchor="w")
            label.pack(pady=5, padx=10, fill="x", expand=True)

    def refresh_reminders_list(self):
        for widget in self.reminders_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom:
            ctk.CTkLabel(self.reminders_frame, text="Select a leader to view reminders.").pack(pady=20, padx=10)
            return

        # Use current_leader_classroom as ubicacion_filter
        due_soon_loans = book_manager.get_books_due_soon_db(days_threshold=7, ubicacion_filter=self.current_leader_classroom)
        if not due_soon_loans:
            ctk.CTkLabel(self.reminders_frame, text=f"No books due soon or overdue in {self.current_leader_classroom}.").pack(pady=20, padx=10)
            return

        today = datetime.now().date()
        for i, book in enumerate(due_soon_books):
            item_frame = ctk.CTkFrame(self.reminders_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            item_frame.pack(fill="x", pady=(2,0), padx=5)

            due_date = datetime.strptime(book['due_date'], '%Y-%m-%d').date()
            is_overdue = due_date < today

            details = f"Book: {book['title']}\n" \
                      f"Borrower: {book.get('borrower_name', 'Unknown')}\n" \
                      f"Due Date: {book['due_date']}"

            text_color = ("#D03030", "#E04040") if is_overdue else (None, None) # CustomTkinter default if None
            font_weight = "bold" if is_overdue else "normal"

            if is_overdue: details += " (OVERDUE)"

            label = ctk.CTkLabel(item_frame, text=details, justify="left", anchor="w", text_color=text_color[0] if ctk.get_appearance_mode().lower() == "light" else text_color[1], font=ctk.CTkFont(weight=font_weight))
            label.pack(pady=5, padx=10, fill="x", expand=True)

    # --- USER MANAGEMENT TAB ---
    def setup_manage_users_tab(self):
        tab = self.manage_users_tab
        tab.configure(fg_color=("#E9E9E9", "#3B3B3B"))

        # Main frame for the tab
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Add User Section ---
        add_user_outer_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        add_user_outer_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(add_user_outer_frame, text="➕ Añadir Nuevo Usuario / Editar Usuario", font=HEADING_FONT).grid(row=0, column=0, columnspan=3, pady=(10,15), padx=10) # Translated

        ctk.CTkLabel(add_user_outer_frame, text="Nombre:", font=BODY_FONT).grid(row=1, column=0, padx=(10,5), pady=8, sticky="w") # Translated
        self.um_name_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, placeholder_text="Nombre Completo") # Translated
        self.um_name_entry.grid(row=1, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")

        ctk.CTkLabel(add_user_outer_frame, text="Contraseña:", font=BODY_FONT).grid(row=2, column=0, padx=(10,5), pady=8, sticky="w") # Translated
        self.um_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Introducir contraseña") # Translated
        self.um_password_entry.grid(row=2, column=1, padx=(0,5), pady=8, sticky="ew")

        ctk.CTkLabel(add_user_outer_frame, text="Confirmar:", font=BODY_FONT).grid(row=3, column=0, padx=(10,5), pady=8, sticky="w") # Translated
        self.um_confirm_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Confirmar contraseña") # Translated
        self.um_confirm_password_entry.grid(row=3, column=1, padx=(0,5), pady=8, sticky="ew")

        # self.um_show_password_var = ctk.StringVar(value="off")
        # show_password_check = ctk.CTkCheckBox(add_user_outer_frame, text="Mostrar", variable=self.um_show_password_var, onvalue="on", offvalue="off", command=self.um_toggle_password_visibility, font=BODY_FONT) # Translated "Show"
        # show_password_check.grid(row=2, column=2, rowspan=2, padx=(0,10), pady=8, sticky="w")

        ctk.CTkLabel(add_user_outer_frame, text="Clase/Oficina:", font=BODY_FONT).grid(row=4, column=0, padx=(10,5), pady=8, sticky="w") # Translated "Classroom"
        self.um_classroom_combo = ctk.CTkComboBox(add_user_outer_frame, values=["Clase A", "Clase B", "Clase C", "Clase D", "OficinaAdmin"], font=BODY_FONT, dropdown_font=BODY_FONT) # Translated "AdminOffice", other values might need translation
        self.um_classroom_combo.grid(row=4, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")
        self.um_classroom_combo.set("Clase A") # Default

        ctk.CTkLabel(add_user_outer_frame, text="Rol:", font=BODY_FONT).grid(row=5, column=0, padx=(10,5), pady=8, sticky="w") # Translated
        self.um_role_combo = ctk.CTkComboBox(add_user_outer_frame, values=["alumno", "líder", "admin"], font=BODY_FONT, dropdown_font=BODY_FONT) # Translated
        self.um_role_combo.grid(row=5, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")
        self.um_role_combo.set("alumno") # Translated

        add_user_outer_frame.columnconfigure(1, weight=1)

        self.um_add_user_button = ctk.CTkButton(add_user_outer_frame, text="Añadir Usuario", font=BUTTON_FONT, command=self.add_user_ui, corner_radius=8) # Translated
        self.um_add_user_button.grid(row=6, column=0, padx=(10,5), pady=15, sticky="ew")

        self.um_update_user_button = ctk.CTkButton(add_user_outer_frame, text="Actualizar Usuario Seleccionado", font=BUTTON_FONT, command=self.edit_user_ui, corner_radius=8, state="disabled") # Translated
        self.um_update_user_button.grid(row=6, column=1, padx=(5,5), pady=15, sticky="ew")

        self.um_clear_form_button = ctk.CTkButton(add_user_outer_frame, text="Limpiar Formulario", font=BUTTON_FONT, command=self.clear_user_form_ui, corner_radius=8, fg_color="gray50", hover_color="gray60") # Translated
        self.um_clear_form_button.grid(row=6, column=2, padx=(5,10), pady=15, sticky="ew")


        # --- User List Section ---
        user_list_container = ctk.CTkFrame(main_frame, corner_radius=10)
        user_list_container.pack(pady=10, padx=10, expand=True, fill="both")

        list_header = ctk.CTkFrame(user_list_container, fg_color="transparent")
        list_header.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(list_header, text="👥 Usuarios Registrados", font=HEADING_FONT).pack(side="left", padx=10, pady=5) # Translated
        refresh_icon = self.load_icon("refresh")
        refresh_button = ctk.CTkButton(list_header, text="Actualizar Lista", image=refresh_icon, font=BUTTON_FONT, command=self.refresh_user_list_ui, width=120, corner_radius=8) # Translated
        refresh_button.pack(side="right", padx=10, pady=5)

        self.user_list_scroll_frame = ctk.CTkScrollableFrame(user_list_container, label_text="")
        self.user_list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- User Actions Section (for selected user) ---
        actions_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        actions_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(actions_frame, text="Acciones para Usuario Seleccionado:", font=SUBHEADING_FONT).pack(side="left", padx=(10,15), pady=10) # Translated

        delete_icon = self.load_icon("delete")
        self.um_delete_button = ctk.CTkButton(actions_frame, text="Eliminar", image=delete_icon, font=BUTTON_FONT, command=self.delete_user_ui, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", corner_radius=8) # Translated
        self.um_delete_button.pack(side="left", padx=5, pady=10)

        reset_pass_icon = self.load_icon("reset_password")
        self.um_reset_password_button = ctk.CTkButton(actions_frame, text="Restablecer Contraseña", image=reset_pass_icon, font=BUTTON_FONT, command=self.reset_user_password_ui, state="disabled", corner_radius=8) # Translated
        self.um_reset_password_button.pack(side="left", padx=5, pady=10)

        self.refresh_user_list_ui()

    def clear_user_form_ui(self, clear_selection=True):
        self.um_name_entry.delete(0, "end")
        self.um_password_entry.delete(0, "end")
        self.um_confirm_password_entry.delete(0, "end")
        self.um_classroom_combo.set("Clase A") # Reset to default (Spanish value)
        self.um_role_combo.set("alumno")    # Reset to default (Spanish value)
        if clear_selection:
            self.selected_user_id_manage_tab = None
            self.um_delete_button.configure(state="disabled")
            self.um_reset_password_button.configure(state="disabled")
            self.um_update_user_button.configure(state="disabled", text="Actualizar Usuario Seleccionado") # Translated
            self.um_add_user_button.configure(state="normal")
            self.um_name_entry.focus()

    def select_user_for_management(self, user_id, user_data):
        self.selected_user_id_manage_tab = user_id
        self.um_delete_button.configure(state="normal")
        self.um_reset_password_button.configure(state="normal")
        self.um_update_user_button.configure(state="normal", text=f"Guardar Cambios para {user_data.get('name', '')[:15]}") # Translated
        self.um_add_user_button.configure(state="disabled")

        # Populate form for editing
        self.um_name_entry.delete(0, "end")
        self.um_name_entry.insert(0, user_data.get('name', ''))
        self.um_password_entry.delete(0, "end")
        self.um_confirm_password_entry.delete(0, "end")
        self.um_password_entry.configure(placeholder_text="Nueva contraseña si cambia") # Translated
        self.um_confirm_password_entry.configure(placeholder_text="Confirmar nueva contraseña") # Translated
        self.um_classroom_combo.set(user_data.get('classroom', 'Clase A')) # Ensure Spanish values used if applicable
        self.um_role_combo.set(user_data.get('role', 'alumno')) # Ensure Spanish values used

        # Highlight the selected user in the list (visual feedback)
        for widget in self.user_list_scroll_frame.winfo_children():
            if hasattr(widget, "_user_id_ref") and widget._user_id_ref == user_id:
                widget.configure(fg_color=("lightblue", "darkblue")) # Highlight color
            else:
                # Reset others to default alternating colors or a standard non-highlight color
                # This depends on how you set initial colors. For simplicity, using a fixed one here.
                original_color = widget._original_bg if hasattr(widget, "_original_bg") else ("gray85", "gray17") # Fallback
                widget.configure(fg_color=original_color)


    def refresh_user_list_ui(self):
        if not hasattr(self, 'user_list_scroll_frame'): return
        for widget in self.user_list_scroll_frame.winfo_children():
            widget.destroy()

        users = student_manager.get_students_db()
        if not users:
            ctk.CTkLabel(self.user_list_scroll_frame, text="No hay usuarios en el sistema.", font=BODY_FONT).pack(pady=20) # Translated
            return

        for i, user in enumerate(users):
            user_id = user['id']
            original_bg = ("gray85", "gray20") if i % 2 == 0 else ("gray90", "gray25")
            item_frame = ctk.CTkFrame(self.user_list_scroll_frame, corner_radius=5, fg_color=original_bg)
            item_frame.pack(fill="x", pady=(3,0), padx=5)
            item_frame._user_id_ref = user_id # Store id for reference
            item_frame._original_bg = original_bg # Store original color for de-selection

            # User details
            details_text = f"👤 {user['name']} ({user['role']}) - 🏫 {user['classroom']}" # Keep classroom as it's from DB, role might need translation if roles are translated in DB/logic
            # Small ID display: f"ID: {user_id[:8]}..."
            id_label = ctk.CTkLabel(item_frame, text=f"ID: {user_id[:8]}...", font=(APP_FONT_FAMILY, 9, "italic"), text_color="gray") # "ID" is common
            id_label.pack(side="right", padx=(0,10), pady=2)

            label = ctk.CTkLabel(item_frame, text=details_text, font=BODY_FONT, anchor="w")
            label.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            # Make the frame clickable
            # Using lambda with default argument to capture current user_id and user data for the callback
            item_frame.bind("<Button-1>", lambda event, uid=user_id, udata=user: self.select_user_for_management(uid, udata))
            label.bind("<Button-1>", lambda event, uid=user_id, udata=user: self.select_user_for_management(uid, udata))
            # id_label.bind("<Button-1>", lambda event, uid=user_id, udata=user: self.select_user_for_management(uid, udata))


        # After refresh, ensure selection state is consistent
        if not self.selected_user_id_manage_tab:
            self.um_delete_button.configure(state="disabled")
            self.um_reset_password_button.configure(state="disabled")
            self.um_update_user_button.configure(state="disabled", text="Actualizar Usuario Seleccionado") # Translated
            self.um_add_user_button.configure(state="normal")
        else:
            # Re-highlight if selected user is still in the list
            found_selected = False
            for widget in self.user_list_scroll_frame.winfo_children():
                 if hasattr(widget, "_user_id_ref") and widget._user_id_ref == self.selected_user_id_manage_tab:
                    widget.configure(fg_color=("lightblue", "darkblue"))
                    found_selected = True
                    break
            if not found_selected: # Selected user might have been deleted
                self.clear_user_form_ui(clear_selection=True)


    def add_user_ui(self):
        name = self.um_name_entry.get()
        password = self.um_password_entry.get()
        confirm_password = self.um_confirm_password_entry.get()
        classroom = self.um_classroom_combo.get()
        role = self.um_role_combo.get()

        if not name or not password or not confirm_password or not classroom or not role:
            messagebox.showerror("Error de Entrada", "Todos los campos (Nombre, Contraseña, Confirmar Contraseña, Clase/Oficina, Rol) son requeridos.") # Translated
            return
        if password != confirm_password:
            messagebox.showerror("Contraseñas no Coinciden", "Las contraseñas no coinciden. Por favor, inténtalo de nuevo.") # Translated
            self.um_password_entry.delete(0, "end")
            self.um_confirm_password_entry.delete(0, "end")
            self.um_password_entry.focus()
            return

        student_id = student_manager.add_student_db(name, classroom, password, role)
        if student_id:
            messagebox.showinfo("Éxito", f"Usuario '{name}' añadido con éxito. ID: {student_id}") # Translated
            self.clear_user_form_ui(clear_selection=False)
            self.refresh_user_list_ui()
            if hasattr(self, 'refresh_student_list_ui'): self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'): self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Error de Base de Datos", f"Error al añadir usuario '{name}'. Revisa la consola para más detalles.") # Translated

    def edit_user_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("Ningún Usuario Seleccionado", "Por favor, selecciona un usuario de la lista para actualizar.") # Translated
            return

        user_id = self.selected_user_id_manage_tab
        new_name = self.um_name_entry.get()
        new_classroom = self.um_classroom_combo.get()
        new_role = self.um_role_combo.get()

        if not new_name:
            messagebox.showerror("Error de Entrada", "El campo de nombre no puede estar vacío para una actualización.") # Translated
            self.um_name_entry.focus()
            return

        success = student_manager.update_student_details_db(user_id, new_name, new_classroom, new_role)

        if success:
            messagebox.showinfo("Actualización Exitosa", f"Los detalles del usuario '{new_name}' (ID: {user_id[:8]}) han sido actualizados.") # Translated
            self.clear_user_form_ui(clear_selection=True)
            self.refresh_user_list_ui()
            if hasattr(self, 'refresh_student_list_ui'):
                self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'):
                self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Actualización Fallida", f"No se pudieron actualizar los detalles para el usuario '{new_name}'. Por favor, revisa la consola.") # Translated

    def delete_user_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("Ningún Usuario Seleccionado", "Por favor, selecciona un usuario de la lista para eliminar.") # Translated
            return

        user_id = self.selected_user_id_manage_tab
        user_details = student_manager.get_student_by_id_db(user_id)
        user_name = user_details['name'] if user_details else "el usuario seleccionado" # Translated

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar permanentemente al usuario '{user_name}' (ID: {user_id[:8]})?\nEsta acción no se puede deshacer."): # Translated
            return

        success = student_manager.delete_student_db(user_id)
        if success:
            messagebox.showinfo("Eliminación Exitosa", f"El usuario '{user_name}' ha sido eliminado.") # Translated
            self.clear_user_form_ui(clear_selection=True)
            self.refresh_user_list_ui()
            if hasattr(self, 'refresh_student_list_ui'): self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'): self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Eliminación Fallida", f"Error al eliminar el usuario '{user_name}'. Podría estar involucrado en préstamos activos o ocurrió un error.") # Translated

    def reset_user_password_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("Ningún Usuario Seleccionado", "Por favor, selecciona un usuario para restablecer su contraseña.") # Translated
            return

        user_id = self.selected_user_id_manage_tab
        user_details = student_manager.get_student_by_id_db(user_id)
        user_name = user_details['name'] if user_details else "usuario seleccionado" # Translated

        new_password = simpledialog.askstring("Nueva Contraseña", f"Introduce la nueva contraseña para {user_name}:", show='*') # Translated
        if not new_password:
            messagebox.showinfo("Cancelado", "Restablecimiento de contraseña cancelado.") # Translated
            return

        confirm_new_password = simpledialog.askstring("Confirmar Nueva Contraseña", "Confirma la nueva contraseña:", show='*') # Translated
        if new_password != confirm_new_password:
            messagebox.showerror("Contraseñas no Coinciden", "Las nuevas contraseñas no coinciden. La contraseña no ha sido restablecida.") # Translated
            return

        success = student_manager.update_student_password_db(user_id, new_password)
        if success:
            messagebox.showinfo("Contraseña Restablecida", f"La contraseña para el usuario '{user_name}' ha sido restablecida con éxito.") # Translated
        else:
            messagebox.showerror("Error al Restablecer Contraseña", f"Error al restablecer la contraseña para '{user_name}'.") # Translated

    # def um_toggle_password_visibility(self): # Optional helper
    #     if self.um_show_password_var.get() == "on":
    #         self.um_password_entry.configure(show="")
    #         self.um_confirm_password_entry.configure(show="")
    #     else:
    #         self.um_password_entry.configure(show="*")
    #         self.um_confirm_password_entry.configure(show="*")

# Main execution
if __name__ == "__main__":
    # It's good practice to ensure DB is ready before app starts fully.
    # init_db() # This is already called in App.__init__

    app = App()
    app.mainloop()
