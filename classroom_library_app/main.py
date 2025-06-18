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
ctk.set_default_color_theme("green") # Options: "blue" (default), "green", "dark-blue"

APP_FONT_FAMILY = "Comic Sans MS" # A common sans-serif font
HEADING_FONT = (APP_FONT_FAMILY, 22, "bold")
SUBHEADING_FONT = (APP_FONT_FAMILY, 18, "bold")
BODY_FONT = (APP_FONT_FAMILY, 14)
BUTTON_FONT = (APP_FONT_FAMILY, 15, "bold")

# Define a simple color palette (using CTk's theme system primarily, but can define for specific widgets if needed)
# COLOR_PRIMARY = "#007ACC" # Blue
# COLOR_SECONDARY = "#F0F0F0" # Light Gray
# COLOR_ACCENT = "#FFA500" # Orange
# COLOR_TEXT = "#333333" # Dark Gray for light mode

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📚 Leerflix 🧸") # Changed title
        self.geometry("950x750")

        # Set window icon
        try:
            # Ensure get_data_path and os are available in this scope
            # get_data_path is imported from utils, os is imported directly
            icon_path_str = os.path.join("assets", "logo.ico")
            icon_path = get_data_path(icon_path_str) # Corrected: use icon_path_str here
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                # Try a fallback path if not found (e.g. if get_data_path points inside app dir already)
                fallback_icon_path = os.path.join("assets", "logo.ico")
                if os.path.exists(fallback_icon_path):
                    self.iconbitmap(fallback_icon_path)
                else:
                    print(f"Warning: Window icon 'logo.ico' not found at {icon_path} (resolved from {icon_path_str}) or {fallback_icon_path}")
        except Exception as e:
            print(f"Error setting window icon: {e}")

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
        self.login_window.title("¡Hola Peque!") # Translated
        self.login_window.geometry("450x550") # Adjusted window size
        self.login_window.transient(self)
        self.login_window.grab_set()
        self.login_window.protocol("WM_DELETE_WINDOW", self.quit_application)

        # Load and display the image
        try:
            image_path_str = os.path.join('assets', 'Leerflix igual.jpg')
            image_path = get_data_path(image_path_str)
            if os.path.exists(image_path):
                img = Image.open(image_path)
                # Adjust size as needed, maintaining aspect ratio if possible
                # Original image dimensions might be large, so we scale it down.
                # Let's aim for a width of 400, and scale height accordingly, or set a fixed size.
                # For example, if original is 1200x600, scaled could be 400x200.
                # For now, using a fixed size, e.g. 400x150, adjust as needed.
                desired_width = 400
                desired_height = 150 # Adjust this based on actual image aspect ratio
                img_resized = img.resize((desired_width, desired_height), Image.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(desired_width, desired_height))
                image_label = ctk.CTkLabel(self.login_window, image=ctk_image, text="")
                image_label.pack(pady=(20, 10)) # Padding top and bottom
            else:
                print(f"Login screen image not found at {image_path}")
                # Optionally, add a placeholder label if image is missing
                ctk.CTkLabel(self.login_window, text="[Imagen no encontrada]", font=BODY_FONT).pack(pady=(20,10))
        except Exception as e:
            print(f"Error loading login screen image: {e}")
            ctk.CTkLabel(self.login_window, text="[Error al cargar imagen]", font=BODY_FONT).pack(pady=(20,10))


        ctk.CTkLabel(self.login_window, text="Bienvenidos a LEERFLIX", font=HEADING_FONT).pack(pady=(10, 20)) # Changed text

        frame = ctk.CTkFrame(self.login_window, fg_color="#E0F2F1") # Added fg_color
        frame.pack(pady=10, padx=30, fill="x") # Adjusted padding
        frame.columnconfigure(1, weight=1) # Allow entry column to expand if needed

        ctk.CTkLabel(frame, text="Usuario (Nombre):", font=BODY_FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w") # Translated and adjusted padding
        username_entry = ctk.CTkEntry(frame, font=BODY_FONT, width=200, placeholder_text="Nombre de usuario") # Translated placeholder, adjusted width
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew") # Adjusted padding and sticky

        ctk.CTkLabel(frame, text="Contraseña:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w") # Translated and adjusted padding
        password_entry = ctk.CTkEntry(frame, font=BODY_FONT, show="*", width=200, placeholder_text="Contraseña") # Translated placeholder, adjusted width
        password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew") # Adjusted padding and sticky

        # Give focus to username entry initially
        username_entry.focus()
        # Bind Enter key to login action for password field for convenience
        password_entry.bind("<Return>", lambda event: login_action())


        error_label = ctk.CTkLabel(self.login_window, text="", text_color="red", font=BODY_FONT) # Ensured BODY_FONT
        error_label.pack(pady=(0,10)) # Adjusted padding

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
        button_frame.pack(pady=20) # Adjusted padding

        login_button = ctk.CTkButton(button_frame, text="Acceder", font=BUTTON_FONT, command=login_action) # Translated and ensured BUTTON_FONT
        login_button.pack(side="left", padx=15) # Adjusted padding

        quit_button = ctk.CTkButton(button_frame, text="Salir", font=BUTTON_FONT, command=self.quit_application, fg_color="gray50", hover_color="gray60") # Translated and ensured BUTTON_FONT
        quit_button.pack(side="left", padx=15) # Adjusted padding

        # Creator Label
        creator_label = ctk.CTkLabel(self.login_window, text="Creado por Javi Barrero", font=BODY_FONT)
        creator_label.pack(side="bottom", pady=(10, 10)) # Adjusted padding for bottom

        # Center the login window
        self.login_window.update_idletasks() # Update geometry
        x = self.winfo_screenwidth() // 2 - self.login_window.winfo_width() // 2
        y = self.winfo_screenheight() // 2 - self.login_window.winfo_height() // 2
        self.login_window.geometry(f"+{x}+{y}")


    def initialize_main_app_ui(self):
        # --- Header Frame ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent") # Or a specific color
        header_frame.pack(pady=(10, 5), padx=15, fill="x")

        try:
            logo_path_str = os.path.join('assets', 'leerflix logo ancho.jpg') # Changed filename
            logo_path = get_data_path(logo_path_str)
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                # Adjust size for header
                original_width, original_height = img.size
                desired_height = 80  # Increased target height
                aspect_ratio = original_width / original_height
                desired_width = int(desired_height * aspect_ratio)

                # Ensure width is not excessively large for the window
                max_header_width = 900 # Increased max_header_width
                if desired_width > max_header_width:
                    desired_width = max_header_width
                    # Recalculate height to maintain aspect ratio if width is capped
                    desired_height = int(desired_width / aspect_ratio)

                # It's good practice to ensure desired_height is at least 1px if capping width leads to 0
                if desired_height < 1: desired_height = 1


                img_resized = img.resize((desired_width, desired_height), Image.LANCZOS)
                ctk_logo_image = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(desired_width, desired_height))

                logo_label = ctk.CTkLabel(header_frame, image=ctk_logo_image, text="")
                logo_label.pack(pady=5) # Center pack by default
            else:
                print(f"Header logo image not found at {logo_path}")
                # Fallback text if logo not found
                ctk.CTkLabel(header_frame, text="Leerflix", font=HEADING_FONT).pack(pady=10) # Changed text
        except Exception as e:
            print(f"Error loading header logo image: {e}")
            # Fallback text on error
            ctk.CTkLabel(header_frame, text="Leerflix - Error Cargando Logo", font=HEADING_FONT).pack(pady=10) # Changed text

        # Main TabView
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=15, pady=(5, 15)) # Adjusted top pady for tab_view

        # Pestaña de Clasificación primero
        self.leaderboard_tab = self.tab_view.add("🏆 Clasificación")
        if hasattr(self, 'setup_leaderboard_tab'): # Verificar si el método existe
            self.setup_leaderboard_tab()
        else:
            print("Advertencia: El método setup_leaderboard_tab no se encontró.")

        # Otras pestañas después
        self.manage_books_tab = self.tab_view.add("📖 Gestionar Libros") # Translated
        self.view_books_tab = self.tab_view.add("📚 Ver Libros") # Translated
        self.manage_students_tab = self.tab_view.add("🧑‍🎓 Gestionar Alumnos") # Translated
        self.manage_loans_tab = self.tab_view.add("🔄 Gestionar Préstamos") # Translated

        # Configurar las otras pestañas principales
        if hasattr(self, 'setup_manage_books_tab'): self.setup_manage_books_tab()
        if hasattr(self, 'setup_view_books_tab'): self.setup_view_books_tab()
        if hasattr(self, 'setup_manage_students_tab'): self.setup_manage_students_tab()
        if hasattr(self, 'setup_manage_loans_tab'): self.setup_manage_loans_tab()

        # Pestañas condicionales de administrador
        if auth_manager.is_admin():
            self.manage_users_tab = self.tab_view.add("👤 Gestionar Usuarios") # Translated
            if hasattr(self, 'setup_manage_users_tab'):
                 self.setup_manage_users_tab()
            else:
                print("Error: El método setup_manage_users_tab no se encontró pero se esperaba para el admin.")

            self.manage_classrooms_tab = self.tab_view.add("🏫 Gestionar Clases") # Translated
            if hasattr(self, 'setup_manage_classrooms_tab'):
                self.setup_manage_classrooms_tab()
            else:
                print("Error: El método setup_manage_classrooms_tab no se encontró pero se esperaba para el admin.")
        else:
            self.manage_users_tab = None
            # self.manage_classrooms_tab = None # Ensure it's None if user is not admin

        # Asegurar que la pestaña de Clasificación esté activa
        self.tab_view.set("🏆 Clasificación")

        # Deiconify (show) the main window now that UI is initialized
        self.deiconify()

    def quit_application(self):
        # Perform any cleanup if necessary
        if self.login_window is not None and self.login_window.winfo_exists():
            self.login_window.destroy()
        self.quit() # Properly exits the Tkinter mainloop

    def load_icon(self, icon_name, size=(24,24)): # Default size changed to (24,24)
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
                placeholder_image = Image.new("RGBA", size, (200, 220, 200, 100)) # Pale green placeholder for light mode
                dark_placeholder_image = Image.new("RGBA", size, (70, 90, 70, 100))   # Darker pale green for dark mode
                img_ctk = ctk.CTkImage(light_image=placeholder_image, dark_image=dark_placeholder_image, size=size)
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
                placeholder_image = Image.new("RGBA", size, (200, 220, 200, 100)) # Pale green placeholder for light mode
                dark_placeholder_image = Image.new("RGBA", size, (70, 90, 70, 100))   # Darker pale green for dark mode
                img_ctk = ctk.CTkImage(light_image=placeholder_image, dark_image=dark_placeholder_image, size=size)
                self.icon_cache[icon_name] = img_ctk # Cache placeholder
                return img_ctk
            except Exception as pe: # Placeholder creation error
                print(f"Critical error: Could not create placeholder icon for {icon_name}: {pe}")
                return None


    def setup_manage_books_tab(self):
        tab = self.manage_books_tab
        tab.configure(fg_color=("#E8F5E9", "#2C3E50"))

        # --- Add Book Form ---
        add_book_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_book_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_book_frame, text="✨ ¡Añade un Nuevo Libro Mágico! ✨", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,20)) # Increased pady

        ctk.CTkLabel(add_book_frame, text="Título:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w") # Increased pady
        self.title_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., El Principito")
        self.title_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew") # Increased pady

        ctk.CTkLabel(add_book_frame, text="Autor:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w") # Increased pady
        self.author_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Antoine de Saint-Exupéry")
        self.author_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew") # Increased pady

        ctk.CTkLabel(add_book_frame, text="Género:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=10, sticky="w") # Increased pady
        self.genero_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Fábula, Ciencia Ficción")
        self.genero_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew") # Increased pady

        ctk.CTkLabel(add_book_frame, text="Ubicación:", font=BODY_FONT).grid(row=4, column=0, padx=10, pady=10, sticky="w") # Increased pady

        dynamic_classrooms = student_manager.get_distinct_classrooms()
        fixed_locations = ["Biblioteca"]
        all_ubicaciones = sorted(list(set(dynamic_classrooms + fixed_locations)))
        display_values_setup = all_ubicaciones if all_ubicaciones else ["N/A"]

        self.ubicacion_combobox = ctk.CTkComboBox(add_book_frame,
                                                  values=display_values_setup,
                                                  width=300,
                                                  font=BODY_FONT, # Ensured BODY_FONT
                                                  dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.ubicacion_combobox.grid(row=4, column=1, padx=10, pady=10, sticky="ew") # Increased pady
        if all_ubicaciones:
            self.ubicacion_combobox.set(all_ubicaciones[0])
        else:
            self.ubicacion_combobox.set("N/A")

        ctk.CTkLabel(add_book_frame, text="Cantidad Total:", font=BODY_FONT).grid(row=5, column=0, padx=10, pady=10, sticky="w") # Increased pady
        self.cantidad_total_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Ej., 1")
        self.cantidad_total_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew") # Increased pady

        add_book_icon = self.load_icon("add_book")
        add_button = ctk.CTkButton(add_book_frame, text="Añadir Libro a la Biblioteca", image=add_book_icon, font=BUTTON_FONT, command=self.add_book_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        add_button.grid(row=6, column=0, columnspan=2, pady=20, padx=10, sticky="ew") # Increased pady
        add_book_frame.columnconfigure(1, weight=1)

        # --- Import CSV Section ---
        import_csv_frame = ctk.CTkFrame(tab, corner_radius=10)
        import_csv_frame.pack(pady=20, padx=15, fill="x") # Increased pady
        ctk.CTkLabel(import_csv_frame, text="📤 Importar Libros desde Archivo CSV 📤", font=HEADING_FONT).pack(pady=(10,20)) # Increased pady
        import_csv_icon = self.load_icon("import_csv")
        import_button = ctk.CTkButton(import_csv_frame, text="Seleccionar Archivo CSV", image=import_csv_icon, font=BUTTON_FONT, command=self.import_csv_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        import_button.pack(pady=15, padx=60, fill="x") # Increased pady


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
        tab.configure(fg_color=("#E0F2F1", "#2C3E50"))

        controls_frame = ctk.CTkFrame(tab, corner_radius=10)
        controls_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(controls_frame, text="Filtrar por Ubicación:", font=BODY_FONT).grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")
        self.view_ubicacion_filter = ctk.CTkComboBox(controls_frame, values=["Todos", "Biblioteca"] + student_manager.get_distinct_classrooms() , command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150) # Dynamic classrooms
        self.view_ubicacion_filter.grid(row=0, column=1, padx=5, pady=10)
        self.view_ubicacion_filter.set("Todos")

        # Status filter removed
        # ctk.CTkLabel(controls_frame, text="Filter by Status:", font=BODY_FONT).grid(row=0, column=2, padx=(10,5), pady=10, sticky="w")
        # self.view_status_filter = ctk.CTkComboBox(controls_frame, values=["All", "available", "borrowed"], command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150)
        # self.view_status_filter.grid(row=0, column=3, padx=5, pady=10)
        # self.view_status_filter.set("All")

        controls_frame.columnconfigure(1, weight=1) # Allow combobox to take some space (adjust column index if needed)


        search_frame = ctk.CTkFrame(tab, corner_radius=10)
        search_frame.pack(pady=(0,15), padx=15, fill="x")

        ctk.CTkLabel(search_frame, text="🔍 Buscar Libros:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=15) # SUBHEADING_FONT applied, adjusted pady
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Escribe para buscar por título o autor...", font=BODY_FONT, width=300) # Ensured BODY_FONT
        self.search_entry.pack(side="left", padx=(0,10), pady=15, expand=True, fill="x") # Adjusted pady

        search_icon = self.load_icon("search")
        search_button = ctk.CTkButton(search_frame, text="Buscar", image=search_icon, font=BUTTON_FONT, command=self.search_books_ui, width=100, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        search_button.pack(side="left", padx=(0,5), pady=15) # Adjusted pady

        clear_search_icon = self.load_icon("clear_search")
        clear_search_button = ctk.CTkButton(search_frame, text="Limpiar", image=clear_search_icon, font=BUTTON_FONT, command=self.clear_search_ui, width=80, corner_radius=8, fg_color="gray50", hover_color="gray60") # Ensured BUTTON_FONT and corner_radius
        clear_search_button.pack(side="left", padx=(0,10), pady=15) # Adjusted pady

        self.book_list_frame = ctk.CTkScrollableFrame(tab, label_text="Nuestra Maravillosa Colección de Libros", label_font=HEADING_FONT, corner_radius=10) # Ensured HEADING_FONT
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
            availability_color = "green" if available_count > 0 else "red" # This color logic is fine

            status_label = ctk.CTkLabel(book_item_frame, text=availability_text, font=(APP_FONT_FAMILY, 12, "bold"), text_color=availability_color, anchor="e") # Font updated
            status_label.grid(row=0, column=2, padx=(5,10), pady=(5,0), sticky="ne")

            title_label = ctk.CTkLabel(book_item_frame, text=f"{book.get('titulo', 'N/A')}", font=(APP_FONT_FAMILY, 16, "bold"), anchor="w") # Font updated
            title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5,2), sticky="w")

            author_label = ctk.CTkLabel(book_item_frame, text=f"por {book.get('autor', 'N/A')}", font=(APP_FONT_FAMILY, 13, "italic"), anchor="w") # Font updated
            author_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky="w")

            info_text = f"Ubicación: {book.get('ubicacion', 'N/A')}"
            if book.get('genero'):
                info_text += f"  |  Género: {book.get('genero')}"
            info_label = ctk.CTkLabel(book_item_frame, text=info_text, font=(APP_FONT_FAMILY, 12), anchor="w")# Font updated
            info_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(0,8), sticky="w")

            # Removed image_path display for now as it's not in the new schema

            # --- Lend Button ---
            available_count = book_manager.get_available_book_count(book['id'])
            lend_button_state = ctk.NORMAL if available_count > 0 else ctk.DISABLED

            lend_button = ctk.CTkButton(
                book_item_frame,
                text="Prestar",
                font=BUTTON_FONT,
                state=lend_button_state,
                command=lambda b=book: self.prompt_lend_book_from_view_tab(b['id']),
                corner_radius=6
            )
            lend_button.grid(row=3, column=0, columnspan=3, padx=10, pady=(5,10), sticky="ew")

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
        tab.configure(fg_color=("#F1F8E9", "#2C3E50"))

        add_student_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_student_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_student_frame, text="🌟 ¡Añade un Nuevo Alumno Estrella! 🌟", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,20)) # HEADING_FONT, Increased pady

        ctk.CTkLabel(add_student_frame, text="Nombre del Alumno:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w") # BODY_FONT, Increased pady
        self.student_name_entry = ctk.CTkEntry(add_student_frame, width=300, font=BODY_FONT, placeholder_text="Ej., Luna Lovegood") # Ensured BODY_FONT
        self.student_name_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew") # Increased pady

        ctk.CTkLabel(add_student_frame, text="Clase:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w") # BODY_FONT, Increased pady

        current_classrooms_stud = student_manager.get_distinct_classrooms()
        stud_combo_values = current_classrooms_stud if current_classrooms_stud else ["N/A"]
        self.student_classroom_combo = ctk.CTkComboBox(add_student_frame, values=stud_combo_values, width=300, font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.student_classroom_combo.grid(row=2, column=1, padx=10, pady=10, sticky="ew") # Increased pady
        if current_classrooms_stud:
            self.student_classroom_combo.set(current_classrooms_stud[0])
        else:
            self.student_classroom_combo.set("N/A")

        ctk.CTkLabel(add_student_frame, text="Rol:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=10, sticky="w") # BODY_FONT, Increased pady
        self.student_role_combo = ctk.CTkComboBox(add_student_frame, values=["alumno", "líder", "admin"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.student_role_combo.grid(row=3, column=1, padx=10, pady=10, sticky="ew") # Increased pady
        self.student_role_combo.set("alumno")
        add_student_frame.columnconfigure(1, weight=1)

        add_student_icon = self.load_icon("students")
        add_student_button = ctk.CTkButton(add_student_frame, text="Añadir Alumno", image=add_student_icon, font=BUTTON_FONT, command=self.add_student_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        add_student_button.grid(row=4, column=0, columnspan=2, pady=20, padx=10, sticky="ew") # Increased pady

        students_list_frame_container = ctk.CTkFrame(tab, corner_radius=10)
        students_list_frame_container.pack(pady=(0,15), padx=15, expand=True, fill="both")

        list_header_frame = ctk.CTkFrame(students_list_frame_container, fg_color="transparent")
        list_header_frame.pack(fill="x", pady=(10,5)) # Adjusted pady
        ctk.CTkLabel(list_header_frame, text="🎓 Nuestros Increíbles Alumnos 🎓", font=HEADING_FONT).pack(side="left", padx=10, pady=10) # HEADING_FONT, Adjusted pady
        refresh_students_icon = self.load_icon("refresh")
        refresh_students_button = ctk.CTkButton(list_header_frame, text="Actualizar", image=refresh_students_icon, font=BUTTON_FONT, command=self.refresh_student_list_ui, width=120, corner_radius=8) # Ensured BUTTON_FONT, Adjusted width and corner_radius
        refresh_students_button.pack(side="right", padx=10, pady=10) # Adjusted pady

        self.students_list_frame = ctk.CTkScrollableFrame(students_list_frame_container, label_text="") # Label text removed as title is above
        self.students_list_frame.pack(expand=True, fill="both", padx=10, pady=(5,10)) # Adjusted pady

        self.refresh_student_list_ui()

    def add_student_ui(self):
        name = self.student_name_entry.get().strip()
        classroom_raw = self.student_classroom_combo.get()
        role_spanish = self.student_role_combo.get() # This is 'alumno', 'líder', etc.

        # Validate inputs
        if not name: # Name is primary, check first
            messagebox.showerror("Error de Entrada", "El nombre del alumno no puede estar vacío.")
            return

        classroom_stripped = classroom_raw.strip()
        if not classroom_stripped or classroom_stripped == "N/A":
            messagebox.showerror("Error de Entrada", "Por favor, seleccione o introduzca un nombre de clase válido.")
            return

        if not role_spanish: # Should not happen if combobox has a default
            messagebox.showerror("Error de Entrada", "El rol es requerido.")
            return

        # Map Spanish role to English for database
        # This tab is simpler and might only add 'student' or 'leader' if 'admin' role is restricted to user management tab
        role_map_simple = {
            "alumno": "student",
            "líder": "leader"
            # Not including 'admin' here as this tab might be for non-admin user management
        }
        role_english = role_map_simple.get(role_spanish, "student") # Default to student

        # For this simplified tab, password is not set directly, so it will be None
        student_id = student_manager.add_student_db(name, classroom_stripped, None, role_english)
        if student_id:
            messagebox.showinfo("¡Fantástico! ✨", f"¡El alumno '{name}' se ha unido al listado!") # Translated
            self.student_name_entry.delete(0, "end")
            # self.refresh_student_list_ui() # This will be covered by refresh_all_classroom_displays
            # if hasattr(self, 'refresh_leader_selector_combo'):
            #      self.refresh_leader_selector_combo() # Also covered by refresh_all_classroom_displays
            self.refresh_all_classroom_displays() # Ensure all classroom lists are updated
        else:
            messagebox.showerror("¡Oh No! 💔", "Algo salió mal al añadir el alumno. Revisa la consola.") # Translated

    def refresh_student_list_ui(self):
        if not hasattr(self, 'students_list_frame'):
            return

        for widget in self.students_list_frame.winfo_children():
            widget.destroy()

        students = student_manager.get_students_db()

        if not students:
            no_students_label = ctk.CTkLabel(self.students_list_frame, text="No se encontraron alumnos.", font=BODY_FONT) # BODY_FONT
            no_students_label.pack(pady=20, padx=10) # Adjusted padding
            return

        for i, student in enumerate(students):
            student_item_frame = ctk.CTkFrame(self.students_list_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15")) # Alternating colors are fine
            student_item_frame.pack(fill="x", pady=4, padx=5) # Adjusted pady
            details = f"Nombre: {student['name']} ({student['role']}) - Puntos: {student.get('points', 0)}\nClase: {student['classroom']} | ID: {student['id']}"
            label = ctk.CTkLabel(student_item_frame, text=details, justify="left", anchor="w", font=BODY_FONT) # BODY_FONT
            label.pack(pady=8, padx=10, fill="x", expand=True) # Adjusted pady

    def setup_manage_loans_tab(self):
        tab = self.manage_loans_tab
        tab.configure(fg_color=("#E0F7FA", "#2C3E50"))  # This was already updated

        # Dictionaries to map display names to IDs
        self.leader_student_map = {}
        self.lend_book_map = {}
        self.borrower_student_map = {}
        self.return_book_map = {}

        # --- Student Leader Selection ---
        leader_selection_frame = ctk.CTkFrame(tab, corner_radius=10)
        leader_selection_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(leader_selection_frame, text="👑 Seleccionar Líder Estudiantil Actuante:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=10) # SUBHEADING_FONT
        self.leader_selector_combo = ctk.CTkComboBox(leader_selection_frame, width=300, font=BODY_FONT, dropdown_font=BODY_FONT, command=self.on_leader_selected) # Ensured BODY_FONT
        self.leader_selector_combo.pack(side="left", padx=(0,10), pady=10, expand=True)

        # --- Main content frame for loans (will split into left and right) ---
        main_loan_content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_loan_content_frame.pack(expand=True, fill="both", padx=15, pady=(0,15))

        left_frame = ctk.CTkFrame(main_loan_content_frame, corner_radius=10)
        left_frame.pack(side="left", fill="y", padx=(0,10), pady=0, anchor="n")

        # --- Lend Book Section ---
        lend_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        lend_frame.pack(pady=(0,10), padx=10, fill="x")
        ctk.CTkLabel(lend_frame, text="➡️ Prestar un Libro", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w") # HEADING_FONT

        ctk.CTkLabel(lend_frame, text="Libro:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.lend_book_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.lend_book_combo.grid(row=1, column=1, padx=5, pady=10, sticky="ew") # pady adjusted

        ctk.CTkLabel(lend_frame, text="Prestatario:", font=BODY_FONT).grid(row=2, column=0, padx=5, pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.borrower_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.borrower_combo.grid(row=2, column=1, padx=5, pady=10, sticky="ew") # pady adjusted

        # ctk.CTkLabel(lend_frame, text="Fecha de Devolución:", font=BODY_FONT).grid(row=3, column=0, padx=5, pady=8, sticky="w") # Translated "Due Date"
        # self.due_date_entry = ctk.CTkEntry(lend_frame, placeholder_text=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), width=280, font=BODY_FONT)
        # self.due_date_entry.grid(row=3, column=1, padx=5, pady=8, sticky="ew")
        lend_frame.columnconfigure(1, weight=1)

        lend_icon = self.load_icon("book_alt")
        # Storing the button in an instance variable self.lend_book_button
        self.lend_book_button = ctk.CTkButton(lend_frame, text="Prestar Libro", image=lend_icon, font=BUTTON_FONT, command=self.lend_book_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        self.lend_book_button.grid(row=3, column=0, columnspan=2, pady=20, sticky="ew") # Increased pady

        # --- Return Book Section ---
        return_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        return_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(return_frame, text="⬅️ Devolver un Libro", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w") # HEADING_FONT

        ctk.CTkLabel(return_frame, text="Libro Prestado:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.return_book_combo = ctk.CTkComboBox(return_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT, command=self.on_return_book_selection_change) # Ensured BODY_FONT
        self.return_book_combo.grid(row=1, column=1, padx=5, pady=10, sticky="ew") # pady adjusted
        return_frame.columnconfigure(1, weight=1)

        self.worksheet_submitted_checkbox = ctk.CTkCheckBox(return_frame, text="Hoja de trabajo entregada", font=BODY_FONT) # Ensured BODY_FONT
        self.worksheet_submitted_checkbox.configure(state="disabled")
        self.worksheet_submitted_checkbox.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="w") # pady adjusted

        return_icon = self.load_icon("home")
        return_button = ctk.CTkButton(return_frame, text="Devolver Libro", image=return_icon, font=BUTTON_FONT, command=self.return_book_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        return_button.grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")

        extend_loan_icon = self.load_icon("refresh")
        self.extend_loan_button = ctk.CTkButton(return_frame, text="Extender Préstamo", image=extend_loan_icon, font=BUTTON_FONT, state="disabled", corner_radius=8, command=self.extend_loan_ui) # Ensured BUTTON_FONT and corner_radius
        self.extend_loan_button.grid(row=4, column=0, columnspan=2, pady=(5,15), sticky="ew")

        right_frame = ctk.CTkFrame(main_loan_content_frame, fg_color="transparent")
        right_frame.pack(side="left", expand=True, fill="both", padx=(10,0), pady=0)

        loans_display_tabview = ctk.CTkTabview(right_frame, corner_radius=8)
        loans_display_tabview.pack(expand=True, fill="both")

        current_loans_tab = loans_display_tabview.add("Préstamos Actuales") # Translated
        reminders_tab = loans_display_tabview.add("⏰ Recordatorios") # Translated
        current_loans_tab.configure(fg_color=("#F5F5F5", "#343638"))
        reminders_tab.configure(fg_color=("#FFF0F5", "#383436"))


        self.current_loans_label = ctk.CTkLabel(current_loans_tab, text="Préstamos Actuales en [Clase del Líder]", font=SUBHEADING_FONT) # Ensured SUBHEADING_FONT
        self.current_loans_label.pack(pady=10, padx=10)
        self.current_loans_frame = ctk.CTkScrollableFrame(current_loans_tab, label_text="", corner_radius=6) # Label text removed
        self.current_loans_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        self.reminders_label = ctk.CTkLabel(reminders_tab, text="Libros Próximos a Vencer/Vencidos en [Clase del Líder]", font=SUBHEADING_FONT) # Ensured SUBHEADING_FONT
        self.reminders_label.pack(pady=10, padx=10)
        self.reminders_frame = ctk.CTkScrollableFrame(reminders_tab, label_text="", corner_radius=6) # Label text removed
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
        self.reminders_label.configure(text="Recordatorios (Seleccione un líder)") # Translated
        self.lend_book_combo.configure(values=["Seleccione un líder"], state="disabled") # Translated
        self.borrower_combo.configure(values=["Seleccione un líder"], state="disabled") # Translated
        self.return_book_combo.configure(values=["Seleccione un líder"], state="disabled") # Translated
        self.lend_book_combo.set("Seleccione un líder") # Translated
        self.borrower_combo.set("Seleccione un líder") # Translated
        self.return_book_combo.set("Seleccione un líder") # Translated

        # Disable buttons
        if hasattr(self, 'lend_book_button'): self.lend_book_button.configure(state="disabled")
        # Ensure return_book_button exists before configuring
        # It is defined as a local variable in setup_manage_loans_tab, needs to be self.return_book_button
        # For now, let's assume it will be made self.return_book_button
        if hasattr(self, 'return_book_button'): self.return_book_button.configure(state="disabled")
        if hasattr(self, 'extend_loan_button'): self.extend_loan_button.configure(state="disabled")


        for widget in self.current_loans_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.current_loans_frame, text="Por favor, seleccione un líder estudiantil para gestionar préstamos.").pack(pady=20, padx=10) # Translated
        for widget in self.reminders_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.reminders_frame, text="Por favor, seleccione un líder estudiantil para ver recordatorios.").pack(pady=20, padx=10) # Translated

    def refresh_loan_related_combos_and_lists(self):
        if not self.current_leader_id or not self.current_leader_classroom: # current_leader_classroom is the ubicacion
            self.update_loan_section_for_no_leader()
            return

        can_lend = True # Flag to manage lend button state

        # Populate Lend Book ComboBox
        all_books_in_ubicacion = book_manager.get_all_books_db(ubicacion_filter=None) # Filter by leader's classroom later if needed
        lend_book_display_names = []
        self.lend_book_map = {}
        for book in all_books_in_ubicacion:
            available_count = book_manager.get_available_book_count(book['id'])
            if available_count > 0:
                display_text = f"{book.get('titulo', 'N/A')} (por {book.get('autor', 'N/A')}) - Disp: {available_count}" # Spanish 'by'
                self.lend_book_map[display_text] = book['id']
                lend_book_display_names.append(display_text)

        if not lend_book_display_names:
            self.lend_book_combo.configure(values=["No hay libros disponibles"], state="disabled") # Translated
            self.lend_book_combo.set("No hay libros disponibles") # Translated
            can_lend = False
        else:
            self.lend_book_combo.configure(values=lend_book_display_names, state="normal")
            self.lend_book_combo.set(lend_book_display_names[0])

        # Populate Borrower ComboBox
        # Students from the selected leader's classroom
        students_in_classroom = student_manager.get_students_by_classroom_db(self.current_leader_classroom)
        self.borrower_student_map = {s['name']: s['id'] for s in students_in_classroom if s['id'] != self.current_leader_id} # Leader cannot borrow from themselves
        borrower_names = list(self.borrower_student_map.keys())

        if not borrower_names:
            self.borrower_combo.configure(values=["No hay alumnos en esta clase"], state="disabled") # Translated
            self.borrower_combo.set("No hay alumnos en esta clase") # Translated
            can_lend = False
        else:
            self.borrower_combo.configure(values=borrower_names, state="normal")
            self.borrower_combo.set(borrower_names[0])

        # Manage Lend Book Button state
        if hasattr(self, 'lend_book_button'): # Ensure button exists
            if can_lend:
                self.lend_book_button.configure(state="normal")
            else:
                self.lend_book_button.configure(state="disabled")

        # Populate Return Book ComboBox
        # New Logic: Fetch all loans, then filter by students in the leader's class
        students_in_leader_class = student_manager.get_students_by_classroom_db(self.current_leader_classroom)
        student_ids_in_leader_class = [s['id'] for s in students_in_leader_class]

        all_active_loans = book_manager.get_current_loans_db(ubicacion_filter=None, student_id_filter=None) # Ensure fetching all

        relevant_loans_for_return = []
        if all_active_loans: # Ensure all_active_loans is not None
            relevant_loans_for_return = [loan for loan in all_active_loans if loan.get('student_id') in student_ids_in_leader_class]

        self.return_book_map = {}
        return_book_display_names = []
        for loan in relevant_loans_for_return:
            due_date_str = loan.get('due_date', 'N/A')
            due_date_display = 'N/A'
            if due_date_str != 'N/A':
                try:
                    due_date_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
                    due_date_display = due_date_dt.strftime('%d-%m-%Y') # Format for display
                except ValueError:
                    due_date_display = due_date_str

            display_text = f"{loan.get('titulo', 'N/A')} (Prestatario: {loan.get('borrower_name', 'N/A')}) Vence: {due_date_display}"
            self.return_book_map[display_text] = loan['loan_id']
            return_book_display_names.append(display_text)

        if not return_book_display_names:
            self.return_book_combo.configure(values=["No hay libros prestados por alumnos de esta clase"], state="disabled") # Updated placeholder
            self.return_book_combo.set("No hay libros prestados por alumnos de esta clase") # Updated placeholder
        else:
            self.return_book_combo.configure(values=return_book_display_names, state="normal")
            self.return_book_combo.set(return_book_display_names[0])

        self.on_return_book_selection_change(self.return_book_combo.get())

        self.refresh_current_loans_list()
        self.refresh_reminders_list()

    def lend_book_ui(self):
        if not self.current_leader_id:
            messagebox.showerror("Líder No Seleccionado", "Por favor, seleccione primero un líder estudiantil.") # Translated
            return

        book_display_name = self.lend_book_combo.get()
        borrower_display_name = self.borrower_combo.get()

        if book_display_name == "No hay libros disponibles" or borrower_display_name == "No hay alumnos en esta clase": # Translated
            messagebox.showerror("Error de Entrada", "Por favor, seleccione un libro y prestatario válidos.") # Translated
            return

        book_id = self.lend_book_map.get(book_display_name)
        borrower_id = self.borrower_student_map.get(borrower_display_name)

        if not book_id or not borrower_id:
            messagebox.showerror("Error Interno", "No se pudo resolver el ID del libro o prestatario desde la selección.") # Translated
            return

        due_date_calculated = datetime.now() + timedelta(days=14)
        due_date_str_for_db = due_date_calculated.strftime('%Y-%m-%d')

        success = book_manager.loan_book_db(book_id, borrower_id, due_date_str_for_db, self.current_leader_id)

        if success:
            # Assuming display_text format: "Book Title (por Author) - Disp: Count"
            actual_book_title = book_display_name.split(' (por ')[0]
            messagebox.showinfo("Éxito", f"Libro '{actual_book_title}' prestado a {borrower_display_name}.") # Translated
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
        else:
            messagebox.showerror("Préstamo Fallido", "Error al prestar el libro. Revise la consola (el libro podría no estar disponible o ocurrió otro error de BD).") # Translated

    def return_book_ui(self):
        if not self.current_leader_id:
            messagebox.showerror("Líder No Seleccionado", "Por favor, seleccione primero un líder estudiantil.") # Translated
            return

        return_loan_display_name = self.return_book_combo.get()
        if return_loan_display_name == "No borrowed books":
            messagebox.showerror("Input Error", "Please select a loan to return.")
            return

        loan_id = self.return_book_map.get(return_loan_display_name) # Get loan_id
        if not loan_id:
            messagebox.showerror("Internal Error", "Could not resolve loan ID for return from selection.")
            return

        is_worksheet_submitted = bool(self.worksheet_submitted_checkbox.get())

        # Call the updated book_manager.return_book_db with loan_id
        success = book_manager.return_book_db(loan_id, self.current_leader_id, worksheet_submitted=is_worksheet_submitted)

        if success:
            messagebox.showinfo("Success", f"Loan returned successfully.")
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
            self.worksheet_submitted_checkbox.deselect()
            # Ensure the checkbox state is updated based on new combo selection
            self.on_return_book_selection_change(self.return_book_combo.get())
        else:
            messagebox.showerror("Return Failed", "Failed to return book. Check console (loan ID might be invalid or other DB error).")

    def on_return_book_selection_change(self, selection=None): # 'selection' arg is passed by CTkComboBox command
        # selection is the display text from the combobox
        loan_id = self.return_book_map.get(selection)
        if loan_id:
            self.extend_loan_button.configure(state="normal")
            self.worksheet_submitted_checkbox.configure(state="normal")
        else:
            self.extend_loan_button.configure(state="disabled")
            self.worksheet_submitted_checkbox.configure(state="disabled")
            self.worksheet_submitted_checkbox.deselect()

    def extend_loan_ui(self):
        selected_loan_display_text = self.return_book_combo.get()
        loan_id = self.return_book_map.get(selected_loan_display_text)

        if not loan_id: # This also handles cases where selected_loan_display_text might be a placeholder like "No hay libros prestados" if that key isn't in the map
            messagebox.showerror("Error", "Por favor, seleccione un préstamo válido para extender.")
            return

        # Assuming book_manager.extend_loan_db(loan_id) will be created and will return True on success, False on failure.
        # We'll default days_to_extend to 14 in the db function.
        success = book_manager.extend_loan_db(loan_id)

        if success:
            messagebox.showinfo("Éxito", "Préstamo extendido con éxito por 14 días.")
            self.refresh_loan_related_combos_and_lists()
            # Consider if self.refresh_book_list_ui() is needed if due dates are shown there or affect availability. For now, focus on loan list.
        else:
            messagebox.showerror("Error", "No se pudo extender el préstamo. Verifique la consola para más detalles.")

    def refresh_current_loans_list(self):
        for widget in self.current_loans_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom:
             ctk.CTkLabel(self.current_loans_frame, text="Select a leader to view loans.").pack(pady=20, padx=10)
             return

        # Use current_leader_classroom as ubicacion_filter
        loans = book_manager.get_current_loans_db(ubicacion_filter=None)
        if not loans:
            ctk.CTkLabel(self.current_loans_frame, text=f"No books currently loaned out in {self.current_leader_classroom}.").pack(pady=20, padx=10)
            return

        for i, loan in enumerate(loans): # loan is now a dict from get_current_loans_db
            item_frame = ctk.CTkFrame(self.current_loans_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            item_frame.pack(fill="x", pady=(2,0), padx=5)

            loan_date_str = loan.get('loan_date', 'N/A')
            loan_date_display = 'N/A'
            if loan_date_str != 'N/A':
                try:
                    loan_date_dt = datetime.strptime(loan_date_str, '%Y-%m-%d')
                    loan_date_display = loan_date_dt.strftime('%d-%m-%Y')
                except ValueError:
                    loan_date_display = loan_date_str # Fallback

            due_date_str = loan.get('due_date', 'N/A')
            due_date_display = 'N/A'
            if due_date_str != 'N/A':
                try:
                    due_date_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
                    due_date_display = due_date_dt.strftime('%d-%m-%Y')
                except ValueError:
                    due_date_display = due_date_str # Fallback

            borrower_name = loan.get('borrower_name', 'Estudiante Desconocido')

            details = f"Libro: {loan.get('titulo', 'N/A')} (Autor: {loan.get('autor', 'N/A')})\n" \
                      f"Prestatario: {borrower_name}\n" \
                      f"Prestado: {loan_date_display} | Vence: {due_date_display} (ID: {loan.get('loan_id', '')[:8]}...)"
            label = ctk.CTkLabel(item_frame, text=details, justify="left", anchor="w", font=BODY_FONT) # BODY_FONT
            label.pack(pady=8, padx=10, fill="x", expand=True) # Adjusted pady

    def refresh_reminders_list(self):
        for widget in self.reminders_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom:
            ctk.CTkLabel(self.reminders_frame, text="Select a leader to view reminders.").pack(pady=20, padx=10)
            return

        # Use current_leader_classroom as ubicacion_filter
        due_soon_loans = book_manager.get_books_due_soon_db(days_threshold=7, ubicacion_filter=None)
        if not due_soon_loans:
            ctk.CTkLabel(self.reminders_frame, text=f"No books due soon or overdue in {self.current_leader_classroom}.").pack(pady=20, padx=10)
            return

        today = datetime.now().date()
        for i, book in enumerate(due_soon_loans): # Corrected variable name here
            item_frame = ctk.CTkFrame(self.reminders_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            item_frame.pack(fill="x", pady=(2,0), padx=5)

            due_date_str = book['due_date']
            due_date_display = 'N/A'
            is_overdue = False # Default
            if due_date_str != 'N/A':
                try:
                    due_date_dt_obj = datetime.strptime(due_date_str, '%Y-%m-%d')
                    due_date_display = due_date_dt_obj.strftime('%d-%m-%Y')
                    is_overdue = due_date_dt_obj.date() < today
                except ValueError:
                    due_date_display = due_date_str # Fallback

            borrower_name = book.get('borrower_name', 'Desconocido')

            details = f"Libro: {book['titulo']}\n" \
                      f"Prestatario: {borrower_name}\n" \
                      f"Fecha Vencimiento: {due_date_display}"

            text_color = ("#D03030", "#E04040") if is_overdue else (None, None) # CustomTkinter default if None
            font_weight = "bold" if is_overdue else "normal"

            if is_overdue: details += " (VENCIDO)"

            label = ctk.CTkLabel(item_frame, text=details, justify="left", anchor="w", text_color=text_color[0] if ctk.get_appearance_mode().lower() == "light" else text_color[1], font=ctk.CTkFont(family=APP_FONT_FAMILY, size=BODY_FONT[1], weight=font_weight)) # BODY_FONT size, custom weight
            label.pack(pady=8, padx=10, fill="x", expand=True) # Adjusted pady

    # --- USER MANAGEMENT TAB ---
    def setup_manage_users_tab(self):
        tab = self.manage_users_tab
        tab.configure(fg_color=("#F5F5F5", "#333333"))

        # Main frame for the tab
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Add User Section ---
        add_user_outer_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        add_user_outer_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(add_user_outer_frame, text="➕ Añadir Nuevo Usuario / Editar Usuario", font=HEADING_FONT).grid(row=0, column=0, columnspan=3, pady=(10,20), padx=10) # HEADING_FONT, pady adjusted

        ctk.CTkLabel(add_user_outer_frame, text="Nombre:", font=BODY_FONT).grid(row=1, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.um_name_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, placeholder_text="Nombre Completo") # Ensured BODY_FONT
        self.um_name_entry.grid(row=1, column=1, columnspan=2, padx=(0,10), pady=10, sticky="ew") # pady adjusted

        ctk.CTkLabel(add_user_outer_frame, text="Contraseña:", font=BODY_FONT).grid(row=2, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.um_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Introducir contraseña") # Ensured BODY_FONT
        self.um_password_entry.grid(row=2, column=1, padx=(0,5), pady=10, sticky="ew") # pady adjusted

        ctk.CTkLabel(add_user_outer_frame, text="Confirmar:", font=BODY_FONT).grid(row=3, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.um_confirm_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Confirmar contraseña") # Ensured BODY_FONT
        self.um_confirm_password_entry.grid(row=3, column=1, padx=(0,5), pady=10, sticky="ew") # pady adjusted

        # self.um_show_password_var = ctk.StringVar(value="off")
        # show_password_check = ctk.CTkCheckBox(add_user_outer_frame, text="Mostrar", variable=self.um_show_password_var, onvalue="on", offvalue="off", command=self.um_toggle_password_visibility, font=BODY_FONT) # Translated "Show"
        # show_password_check.grid(row=2, column=2, rowspan=2, padx=(0,10), pady=10, sticky="w") # pady adjusted

        ctk.CTkLabel(add_user_outer_frame, text="Clase/Oficina:", font=BODY_FONT).grid(row=4, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted

        current_classrooms_um = student_manager.get_distinct_classrooms()
        # Ensure "OficinaAdmin" is always an option, and handle if no other classrooms exist
        um_initial_values = sorted(list(set(current_classrooms_um + ["OficinaAdmin"])))
        if not um_initial_values:
            um_initial_values = ["OficinaAdmin"]

        self.um_classroom_combo = ctk.CTkComboBox(add_user_outer_frame, values=um_initial_values, font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.um_classroom_combo.grid(row=4, column=1, columnspan=2, padx=(0,10), pady=10, sticky="ew") # pady adjusted
        if "Clase A" in um_initial_values:
             self.um_classroom_combo.set("Clase A")
        elif um_initial_values:
            self.um_classroom_combo.set(um_initial_values[0])


        ctk.CTkLabel(add_user_outer_frame, text="Rol:", font=BODY_FONT).grid(row=5, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted
        self.um_role_combo = ctk.CTkComboBox(add_user_outer_frame, values=["alumno", "líder", "admin"], font=BODY_FONT, dropdown_font=BODY_FONT) # Ensured BODY_FONT
        self.um_role_combo.grid(row=5, column=1, columnspan=2, padx=(0,10), pady=10, sticky="ew") # pady adjusted
        self.um_role_combo.set("alumno")

        add_user_outer_frame.columnconfigure(1, weight=1)

        self.um_add_user_button = ctk.CTkButton(add_user_outer_frame, text="Añadir Usuario", font=BUTTON_FONT, command=self.add_user_ui, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        self.um_add_user_button.grid(row=6, column=0, padx=(10,5), pady=20, sticky="ew") # pady adjusted

        self.um_update_user_button = ctk.CTkButton(add_user_outer_frame, text="Actualizar Usuario Seleccionado", font=BUTTON_FONT, command=self.edit_user_ui, corner_radius=8, state="disabled") # Ensured BUTTON_FONT and corner_radius
        self.um_update_user_button.grid(row=6, column=1, padx=(5,5), pady=20, sticky="ew") # pady adjusted

        self.um_clear_form_button = ctk.CTkButton(add_user_outer_frame, text="Limpiar Formulario", font=BUTTON_FONT, command=self.clear_user_form_ui, corner_radius=8, fg_color="gray50", hover_color="gray60") # Ensured BUTTON_FONT and corner_radius
        self.um_clear_form_button.grid(row=6, column=2, padx=(5,10), pady=20, sticky="ew") # pady adjusted

        # --- Import Students CSV Section ---
        import_students_csv_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        import_students_csv_frame.pack(pady=(15,10), padx=10, fill="x") # Adjusted pady

        ctk.CTkLabel(import_students_csv_frame, text="📤 Importar Alumnos desde CSV", font=HEADING_FONT).grid(row=0, column=0, columnspan=3, pady=(10,15), padx=10, sticky="w") # HEADING_FONT, pady adjusted

        ctk.CTkLabel(import_students_csv_frame, text="Seleccionar Clase:", font=BODY_FONT).grid(row=1, column=0, padx=(10,5), pady=10, sticky="w") # BODY_FONT, pady adjusted

        # Populate classroom combo for CSV import
        # Note: get_distinct_classrooms() is already defined in student_manager
        available_classrooms_for_csv = student_manager.get_distinct_classrooms()
        if not available_classrooms_for_csv: # If no classrooms exist yet, provide a default or guidance
            available_classrooms_for_csv = ["Primero cree una clase"]


        self.import_csv_classroom_combo = ctk.CTkComboBox(import_students_csv_frame, values=available_classrooms_for_csv, font=BODY_FONT, dropdown_font=BODY_FONT, width=250) # Ensured BODY_FONT
        self.import_csv_classroom_combo.grid(row=1, column=1, padx=(0,10), pady=10, sticky="ew") # pady adjusted
        if available_classrooms_for_csv and available_classrooms_for_csv[0] != "Primero cree una clase":
            self.import_csv_classroom_combo.set(available_classrooms_for_csv[0])
        else:
            self.import_csv_classroom_combo.set(available_classrooms_for_csv[0] if available_classrooms_for_csv else "")


        import_csv_icon = self.load_icon("import_csv") # Re-use icon if appropriate
        self.import_students_csv_button = ctk.CTkButton(
            import_students_csv_frame,
            text="Seleccionar Archivo CSV e Importar Alumnos",
            image=import_csv_icon,
            font=BUTTON_FONT, # Ensured BUTTON_FONT
            command=self.import_students_csv_ui,
            corner_radius=8 # Ensured corner_radius
        )
        self.import_students_csv_button.grid(row=1, column=2, padx=(5,10), pady=10, sticky="ew") # pady adjusted

        import_students_csv_frame.columnconfigure(1, weight=1)
        import_students_csv_frame.columnconfigure(2, weight=1)


        # --- User List Section ---
        user_list_container = ctk.CTkFrame(main_frame, corner_radius=10)
        user_list_container.pack(pady=10, padx=10, expand=True, fill="both")

        list_header = ctk.CTkFrame(user_list_container, fg_color="transparent")
        list_header.pack(fill="x", pady=(10,5)) # Adjusted pady
        ctk.CTkLabel(list_header, text="👥 Usuarios Registrados", font=HEADING_FONT).pack(side="left", padx=10, pady=10) # HEADING_FONT, pady adjusted
        refresh_icon = self.load_icon("refresh")
        refresh_button = ctk.CTkButton(list_header, text="Actualizar Lista", image=refresh_icon, font=BUTTON_FONT, command=self.refresh_user_list_ui, width=120, corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        refresh_button.pack(side="right", padx=10, pady=10) # pady adjusted

        self.user_list_scroll_frame = ctk.CTkScrollableFrame(user_list_container, label_text="") # Label text removed
        self.user_list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=(5,10)) # Adjusted pady

        # --- User Actions Section (for selected user) ---
        actions_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        actions_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(actions_frame, text="Acciones para Usuario Seleccionado:", font=SUBHEADING_FONT).pack(side="left", padx=(10,15), pady=10) # SUBHEADING_FONT

        delete_icon = self.load_icon("close")
        self.um_delete_button = ctk.CTkButton(actions_frame, text="Eliminar", image=delete_icon, font=BUTTON_FONT, command=self.delete_user_ui, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        self.um_delete_button.pack(side="left", padx=5, pady=10)

        reset_pass_icon = self.load_icon("refresh")
        self.um_reset_password_button = ctk.CTkButton(actions_frame, text="Restablecer Contraseña", image=reset_pass_icon, font=BUTTON_FONT, command=self.reset_user_password_ui, state="disabled", corner_radius=8) # Ensured BUTTON_FONT and corner_radius
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
            role_display_map = {
                "student": "alumno",
                "leader": "líder",
                "admin": "admin"
            }
            display_role = role_display_map.get(user['role'], user['role']) # Fallback to original if no map found
            details_text = f"👤 {user['name']} ({display_role}) - Puntos: {user.get('points', 0)} - 🏫 {user['classroom']}"

            id_label = ctk.CTkLabel(item_frame, text=f"ID: {user_id[:8]}...", font=(APP_FONT_FAMILY, 11, "italic"), text_color="gray") # Adjusted font size slightly
            id_label.pack(side="right", padx=(0,10), pady=2)

            label = ctk.CTkLabel(item_frame, text=details_text, font=BODY_FONT, anchor="w") # Ensured BODY_FONT
            label.pack(side="left", padx=10, pady=10, fill="x", expand=True) # Adjusted pady

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
        role_spanish = self.um_role_combo.get()

        if not name or not password or not confirm_password or not classroom or not role_spanish:
            messagebox.showerror("Error de Entrada", "Todos los campos (Nombre, Contraseña, Confirmar Contraseña, Clase/Oficina, Rol) son requeridos.") # Translated
            return
        if password != confirm_password:
            messagebox.showerror("Contraseñas no Coinciden", "Las contraseñas no coinciden. Por favor, inténtalo de nuevo.") # Translated
            self.um_password_entry.delete(0, "end")
            self.um_confirm_password_entry.delete(0, "end")
            self.um_password_entry.focus()
            return

        role_map = {
            "alumno": "student",
            "líder": "leader",
            "admin": "admin"
        }
        role_english = role_map.get(role_spanish.lower(), "student") # Default to student

        # Validate classroom input (strip first)
        classroom_stripped = classroom.strip()
        if not classroom_stripped or classroom_stripped == "N/A" or (classroom_stripped == "OficinaAdmin" and role_english != "admin"):
            if classroom_stripped == "OficinaAdmin" and role_english != "admin":
                messagebox.showerror("Error de Entrada", "Solo los administradores pueden ser asignados a 'OficinaAdmin'.")
            else:
                messagebox.showerror("Error de Entrada", "Por favor, seleccione o introduzca un nombre de clase/oficina válido.")
            return

        student_id = student_manager.add_student_db(name, classroom_stripped, password, role_english)
        if student_id:
            messagebox.showinfo("Éxito", f"Usuario '{name}' ({role_english}) añadido con éxito. ID: {student_id}") # Translated
            self.clear_user_form_ui(clear_selection=False)
            self.refresh_all_classroom_displays()
        else:
            messagebox.showerror("Error de Base de Datos", f"Error al añadir usuario '{name}'. Revisa la consola para más detalles.") # Translated

    def edit_user_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("Ningún Usuario Seleccionado", "Por favor, selecciona un usuario de la lista para actualizar.") # Translated
            return

        user_id = self.selected_user_id_manage_tab
        new_name = self.um_name_entry.get().strip()
        new_classroom_stripped = self.um_classroom_combo.get().strip() # Strip here
        new_role_spanish = self.um_role_combo.get() # This is the Spanish role from the combobox

        if not new_name:
            messagebox.showerror("Error de Entrada", "El campo de nombre no puede estar vacío para una actualización.") # Translated
            self.um_name_entry.focus()
            return

        if not new_classroom_stripped or new_classroom_stripped == "N/A":
            messagebox.showerror("Error de Entrada", "Por favor, seleccione o introduzca un nombre de clase/oficina válido para la actualización.")
            return

        # Map Spanish role to English for database operations
        role_map = {
            "alumno": "student",
            "líder": "leader",
            "admin": "admin"
        }
        new_role_english = role_map.get(new_role_spanish.lower(), "student") # Default to student if mapping fails

        success = student_manager.update_student_details_db(user_id, new_name, new_classroom, new_role_english)

        if success:
            messagebox.showinfo("Actualización Exitosa", f"Los detalles del usuario '{new_name}' (Rol: {new_role_spanish}) han sido actualizados.") # Translated, show Spanish role

            # Check if the user was made a leader and has no password
            if new_role_english == 'leader':
                updated_student_details = student_manager.get_student_by_id_db(user_id)
                if updated_student_details and (updated_student_details.get('hashed_password') is None or updated_student_details.get('hashed_password') == ''):
                    # Prompt to set password for the new leader
                    new_leader_password = simpledialog.askstring("Establecer Contraseña para Líder", # Translated
                                                                 f"El usuario {new_name} ha sido asignado como líder. Por favor, establece una contraseña para este líder:", # Translated
                                                                 show='*')
                    if new_leader_password and new_leader_password.strip():
                        confirm_leader_password = simpledialog.askstring("Confirmar Nueva Contraseña", # Translated
                                                                         "Confirma la nueva contraseña:", show='*') # Translated
                        if new_leader_password == confirm_leader_password:
                            if student_manager.update_student_password_db(user_id, new_leader_password):
                                messagebox.showinfo("Contraseña Establecida", f"Contraseña para el líder {new_name} establecida con éxito.") # Translated
                            else:
                                messagebox.showerror("Error de Contraseña", f"No se pudo establecer la contraseña para {new_name}.") # Translated
                        else:
                            messagebox.showwarning("Contraseñas no Coinciden", "Las contraseñas no coinciden. La contraseña no ha sido establecida para el líder.") # Translated
                    else:
                        messagebox.showwarning("Contraseña no Establecida", "No se proporcionó contraseña. El líder no tendrá contraseña hasta que se establezca una manualmente.") # Translated


            self.clear_user_form_ui(clear_selection=True)
            # self.refresh_user_list_ui() # Covered
            # if hasattr(self, 'refresh_student_list_ui'): self.refresh_student_list_ui() # Covered
            # if hasattr(self, 'refresh_leader_selector_combo'): self.refresh_leader_selector_combo() # Covered
            self.refresh_all_classroom_displays()
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

    def import_students_csv_ui(self):
        selected_classroom = self.import_csv_classroom_combo.get().strip() # Added .strip() here
        if not selected_classroom or selected_classroom == "Primero cree una clase": # Check after stripping
            messagebox.showerror("Error de Selección de Clase", "Por favor, seleccione o introduzca una clase válida para la importación de CSV. El nombre no puede estar vacío.") # Translated and clarified
            return

        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV para importar alumnos", # Translated
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")) # Translated
        )
        if not file_path:
            return # User cancelled

        success_count, errors = student_manager.import_students_from_csv(file_path, selected_classroom)

        summary_message = f"Resumen de Importación de Alumnos CSV:\n\nAlumnos importados con éxito: {success_count} a la clase '{selected_classroom}'." # Translated
        if errors:
            error_details = "\n".join(f"- {e}" for e in errors[:10]) # Show first 10 errors
            if len(errors) > 10:
                error_details += f"\n- ... y {len(errors)-10} más errores." # Translated
            summary_message += f"\n\nErrores encontrados ({len(errors)}):\n{error_details}"
            messagebox.showwarning("Importación Parcialmente Exitosa o Fallida", summary_message) # Translated
        else:
            messagebox.showinfo("Importación Exitosa", summary_message) # Translated

        self.refresh_all_classroom_displays() # Use the new central refresh method


    def setup_manage_classrooms_tab(self):
        self.selected_classroom_for_rename = None # Initialize instance variable
        tab = self.manage_classrooms_tab
        tab.configure(fg_color=("#F5F5F5", "#333333")) # Neutral gray for admin tab

        # Main content frame, splitting into two columns
        main_content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_content_frame.pack(expand=True, fill="both", padx=15, pady=15)
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_columnconfigure(1, weight=1)
        main_content_frame.grid_rowconfigure(0, weight=1)

        # --- Left Column: List and Select Classroom ---
        left_column_frame = ctk.CTkFrame(main_content_frame, corner_radius=10)
        left_column_frame.grid(row=0, column=0, padx=(0,10), pady=0, sticky="nsew")

        ctk.CTkLabel(left_column_frame, text="Clases Existentes", font=HEADING_FONT).pack(pady=(15,10), padx=10) # HEADING_FONT, Adjusted pady

        self.classrooms_list_frame = ctk.CTkScrollableFrame(left_column_frame, corner_radius=6)
        self.classrooms_list_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        # --- Right Column: Rename Classroom ---
        right_column_frame = ctk.CTkFrame(main_content_frame, corner_radius=10)
        right_column_frame.grid(row=0, column=1, padx=(10,0), pady=0, sticky="nsew")

        rename_frame = ctk.CTkFrame(right_column_frame, fg_color="transparent")
        rename_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(rename_frame, text="Renombrar Clase Seleccionada", font=HEADING_FONT).pack(pady=(0,20)) # HEADING_FONT, Adjusted pady

        ctk.CTkLabel(rename_frame, text="Nuevo Nombre para la Clase:", font=BODY_FONT).pack(anchor="w", pady=(0,5)) # BODY_FONT, pady adjusted
        self.rename_classroom_entry = ctk.CTkEntry(rename_frame, font=BODY_FONT, placeholder_text="Escribe el nuevo nombre aquí", state="disabled") # Ensured BODY_FONT
        self.rename_classroom_entry.pack(fill="x", pady=(0,15)) # pady adjusted

        self.rename_classroom_button = ctk.CTkButton(rename_frame, text="Guardar Nuevo Nombre", font=BUTTON_FONT, command=self.rename_classroom_ui, state="disabled", corner_radius=8) # Ensured BUTTON_FONT and corner_radius
        self.rename_classroom_button.pack(fill="x", pady=10)

        self.refresh_classroom_management_list()

    def refresh_classroom_management_list(self):
        if not hasattr(self, 'classrooms_list_frame'):
            return
        for widget in self.classrooms_list_frame.winfo_children():
            widget.destroy()

        classrooms = student_manager.get_distinct_classrooms()
        if not classrooms:
            ctk.CTkLabel(self.classrooms_list_frame, text="No hay clases definidas actualmente.").pack(pady=10) # Translated
            # Disable rename functionality if no classes
            if hasattr(self, 'rename_classroom_entry'): self.rename_classroom_entry.configure(state="disabled")
            if hasattr(self, 'rename_classroom_button'): self.rename_classroom_button.configure(state="disabled")
            self.selected_classroom_for_rename = None
            return

        for classroom_name in classrooms:
            btn = ctk.CTkButton(
                self.classrooms_list_frame,
                text=classroom_name,
                font=BODY_FONT,
                command=lambda cn=classroom_name: self.on_classroom_select_for_rename(cn)
            )
            btn.pack(fill="x", pady=3, padx=5)

    def on_classroom_select_for_rename(self, classroom_name):
        self.selected_classroom_for_rename = classroom_name
        self.rename_classroom_entry.configure(state="normal")
        self.rename_classroom_entry.delete(0, "end")
        self.rename_classroom_entry.insert(0, classroom_name)
        self.rename_classroom_button.configure(state="normal")

    def rename_classroom_ui(self):
        if not self.selected_classroom_for_rename:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una clase de la lista para renombrar.") # Translated
            return

        old_name = self.selected_classroom_for_rename
        new_name = self.rename_classroom_entry.get().strip()

        if not new_name:
            messagebox.showerror("Error de Entrada", "El nuevo nombre de la clase no puede estar vacío.") # Translated
            return

        if new_name == old_name:
            messagebox.showinfo("Información", "El nuevo nombre es igual al anterior. No se realizaron cambios.") # Translated
            return

        # Optional: Check if new_name conflicts with another existing classroom (excluding old_name)
        # existing_classrooms = student_manager.get_distinct_classrooms()
        # if new_name in existing_classrooms and new_name != old_name:
        #     if not messagebox.askyesno("Confirmar Sobrescritura Potencial",
        #                                f"La clase '{new_name}' ya existe. Si continúas, los alumnos de '{old_name}' se moverán a '{new_name}'.\n¿Estás seguro?"):
        #         return

        success = student_manager.rename_classroom(old_name, new_name)

        if success:
            messagebox.showinfo("Éxito", f"La clase '{old_name}' ha sido renombrada a '{new_name}'.") # Translated
            self.refresh_all_classroom_displays()
            # Reset selection and UI state
            self.selected_classroom_for_rename = None
            self.rename_classroom_entry.delete(0, "end")
            self.rename_classroom_entry.configure(state="disabled")
            self.rename_classroom_button.configure(state="disabled")
        else:
            messagebox.showerror("Error al Renombrar", f"No se pudo renombrar la clase '{old_name}'. Verifica si la clase tenía alumnos o revisa la consola.") # Translated

    def refresh_all_classroom_displays(self):
        # 1. Refresh the list in the current "Gestionar Clases" tab
        if hasattr(self, 'refresh_classroom_management_list'):
            self.refresh_classroom_management_list()

        # 2. Get updated list of distinct classrooms
        updated_classrooms = student_manager.get_distinct_classrooms()
        # Ensure "OficinaAdmin" is available if it's special, or handle classroom lists consistently
        # For now, let's assume "OficinaAdmin" might not be in distinct_classrooms if no student is there.
        # It's better if UI elements requiring "OficinaAdmin" explicitly add it if not present.

        # Create a base list for general classroom selection
        general_classroom_list = updated_classrooms if updated_classrooms else ["(N/A)"]

        # 3. Refresh classroom combobox in "Gestionar Usuarios" (CSV import)
        if hasattr(self, 'import_csv_classroom_combo'):
            current_csv_class = self.import_csv_classroom_combo.get()
            self.import_csv_classroom_combo.configure(values=general_classroom_list)
            if current_csv_class in general_classroom_list and current_csv_class != "(N/A)": # Check against N/A
                self.import_csv_classroom_combo.set(current_csv_class)
            elif general_classroom_list[0] != "(N/A)":
                self.import_csv_classroom_combo.set(general_classroom_list[0])
            else:
                self.import_csv_classroom_combo.set(general_classroom_list[0]) # Sets to "(N/A)"

        # 4. Refresh classroom combobox in "Gestionar Usuarios" (user editing)
        um_classroom_list_with_admin = sorted(list(set(updated_classrooms + ["OficinaAdmin"])))
        if not um_classroom_list_with_admin: um_classroom_list_with_admin = ["N/A"]

        if hasattr(self, 'um_classroom_combo'):
            current_um_class = self.um_classroom_combo.get()
            self.um_classroom_combo.configure(values=um_classroom_list_with_admin)
            if current_um_class in um_classroom_list_with_admin and current_um_class != "N/A":
                self.um_classroom_combo.set(current_um_class)
            elif um_classroom_list_with_admin[0] != "N/A":
                self.um_classroom_combo.set(um_classroom_list_with_admin[0])
            else:
                self.um_classroom_combo.set(um_classroom_list_with_admin[0]) # Sets to "N/A"

        # 5. Refresh classroom combobox in "Gestionar Alumnos" (original student tab)
        if hasattr(self, 'student_classroom_combo'):
            current_student_tab_class = self.student_classroom_combo.get()
            self.student_classroom_combo.configure(values=general_classroom_list)
            if current_student_tab_class in general_classroom_list and current_student_tab_class != "(N/A)":
                self.student_classroom_combo.set(current_student_tab_class)
            elif general_classroom_list[0] != "(N/A)":
                self.student_classroom_combo.set(general_classroom_list[0])
            else:
                self.student_classroom_combo.set(general_classroom_list[0]) # Sets to "(N/A)"

        # 6. Refresh 'Ubicación' combobox in "Gestionar Libros"
        if hasattr(self, 'ubicacion_combobox'):
            fixed_locations_refresh = ["Biblioteca"]
            combined_ubicaciones_refresh = sorted(list(set(updated_classrooms + fixed_locations_refresh)))
            display_ubicaciones_refresh = combined_ubicaciones_refresh if combined_ubicaciones_refresh else ["N/A"]

            current_selection = self.ubicacion_combobox.get()
            self.ubicacion_combobox.configure(values=display_ubicaciones_refresh)

            if current_selection in display_ubicaciones_refresh and current_selection != "N/A":
                self.ubicacion_combobox.set(current_selection)
            elif combined_ubicaciones_refresh : # If there are actual valid ubicaciones
                self.ubicacion_combobox.set(combined_ubicaciones_refresh[0])
            else: # List is empty or only contains "N/A"
                self.ubicacion_combobox.set("N/A")

        # 7. Refresh classroom filter in "Ver Libros" (self.view_ubicacion_filter)
        # This one also includes "Todos" and "Biblioteca"
        view_books_ubicaciones_list = updated_classrooms if updated_classrooms else []
        view_books_options = sorted(list(set(view_books_ubicaciones_list + ["Biblioteca", "Todos"])))
        if not view_books_options : view_books_options = ["Todos"]

        if hasattr(self, 'view_ubicacion_filter'):
            current_view_ubicacion = self.view_ubicacion_filter.get()
            self.view_ubicacion_filter.configure(values=view_books_options)
            if current_view_ubicacion in view_books_options:
                self.view_ubicacion_filter.set(current_view_ubicacion)
            elif "Todos" in view_books_options:
                self.view_ubicacion_filter.set("Todos")
            elif view_books_options:
                self.view_ubicacion_filter.set(view_books_options[0])

        # 8. Refresh classroom filter in Leaderboards
        if hasattr(self, 'leaderboard_class_filter_combo'):
            if self.leaderboard_filter_type_combo.get() == "🏫 Por Clase":
                current_leaderboard_class = self.leaderboard_class_filter_combo.get()
                lb_class_list = general_classroom_list if general_classroom_list[0] != "(N/A)" else ["No hay clases"]
                self.leaderboard_class_filter_combo.configure(values=lb_class_list)
                if current_leaderboard_class in lb_class_list and current_leaderboard_class != "No hay clases":
                    self.leaderboard_class_filter_combo.set(current_leaderboard_class)
                elif lb_class_list[0] != "No hay clases":
                    self.leaderboard_class_filter_combo.set(lb_class_list[0])
                else:
                    self.leaderboard_class_filter_combo.set(lb_class_list[0])

        # 9. Refresh leader selector combo in Manage Loans (as it displays classroom names)
        if hasattr(self, 'refresh_leader_selector_combo'):
            self.refresh_leader_selector_combo()

        print("All relevant classroom displays and lists have been refreshed.")


    def setup_leaderboard_tab(self):
       tab = self.leaderboard_tab # Use the instance variable for the tab
       tab.configure(fg_color=("#E0F7FA", "#2C3E50")) # Example color, adjust as needed

       # --- Controls Frame ---
       controls_frame = ctk.CTkFrame(tab, corner_radius=10)
       controls_frame.pack(pady=10, padx=10, fill="x")

       ctk.CTkLabel(controls_frame, text="Ver:", font=BODY_FONT).pack(side="left", padx=(10,5), pady=10) # BODY_FONT applied

       self.leaderboard_filter_type_combo = ctk.CTkSegmentedButton(controls_frame,
                                                                  values=["🏆 Global", "🏫 Por Clase"],
                                                                  font=BUTTON_FONT, # BUTTON_FONT (global)
                                                                  # command will be added later
                                                                  )
       self.leaderboard_filter_type_combo.pack(side="left", padx=5, pady=10)
       self.leaderboard_filter_type_combo.set("🏆 Global") # Default selection

       self.leaderboard_class_filter_combo = ctk.CTkComboBox(controls_frame,
                                                               values=[], # To be populated later
                                                               font=BODY_FONT, # BODY_FONT applied
                                                               dropdown_font=BODY_FONT, # BODY_FONT applied
                                                               state="disabled", # Enabled when "Por Clase" is selected
                                                               # command will be added later
                                                               )
       self.leaderboard_class_filter_combo.pack(side="left", padx=5, pady=10)

       refresh_icon = self.load_icon("refresh")
       self.leaderboard_refresh_button = ctk.CTkButton(controls_frame, text="Refrescar",
                                                      image=refresh_icon, font=BUTTON_FONT, # BUTTON_FONT applied
                                                      # command will be added later
                                                      width=120, corner_radius=8) # Increased width
       self.leaderboard_refresh_button.pack(side="right", padx=10, pady=10)

       # --- Leaderboard Display Area ---
       self.leaderboard_scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Tabla de Clasificación",
                                                              label_font=HEADING_FONT, corner_radius=10) # HEADING_FONT applied
       self.leaderboard_scroll_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

       # Configure commands for filters
       self.leaderboard_filter_type_combo.configure(command=self.on_leaderboard_filter_type_change)
       self.leaderboard_class_filter_combo.configure(command=self.refresh_leaderboard_display) # Refresh on class change
       self.leaderboard_refresh_button.configure(command=self.refresh_leaderboard_display)

       # Initial population and setup of class filter
       self.on_leaderboard_filter_type_change(self.leaderboard_filter_type_combo.get())

    def on_leaderboard_filter_type_change(self, selection=None): # selection is passed from segmented button
        if selection == "🏫 Por Clase":
            classrooms = student_manager.get_distinct_classrooms()
            if not classrooms: # Handle case with no classrooms
                classrooms = ["No hay clases"] # Placeholder
                self.leaderboard_class_filter_combo.configure(state="disabled", values=classrooms)
                self.leaderboard_class_filter_combo.set(classrooms[0])
            else:
                self.leaderboard_class_filter_combo.configure(state="normal", values=classrooms)
                self.leaderboard_class_filter_combo.set(classrooms[0]) # Select first class by default
        else: # "🏆 Global"
            self.leaderboard_class_filter_combo.configure(state="disabled", values=[])
            self.leaderboard_class_filter_combo.set("") # Clear selection or set to a placeholder

        self.refresh_leaderboard_display()

    def refresh_leaderboard_display(self):
        # Clear existing leaderboard entries
        for widget in self.leaderboard_scroll_frame.winfo_children():
            widget.destroy()

        filter_type = self.leaderboard_filter_type_combo.get()
        classroom_to_filter = None

        if filter_type == "🏫 Por Clase":
            classroom_to_filter = self.leaderboard_class_filter_combo.get()
            # Assuming "Todas las Clases" might be a placeholder if class combo is populated with it.
            if not classroom_to_filter or classroom_to_filter == "Todas las Clases":
                # If no specific class or "All Classes" is selected in "Por Clase" mode,
                # effectively treat as global or show specific message.
                # For this implementation, if "Todas las Clases" is selected, it means no specific class filter.
                # However, student_manager.get_students_sorted_by_points expects None for global.
                # We'll rely on the segmented button's "Global" value to pass None.
                # If "Por Clase" is selected but the class combo has a "All Classes" type of value,
                # this might mean we should show all, or prompt user, or disable this state.
                # For now, if classroom_to_filter is "Todas las Clases", we set it to None
                # to fetch all students, which might be confusing if "Por Clase" is selected.
                # This logic might need refinement based on how class_filter_combo is populated.
                if classroom_to_filter == "Todas las Clases": #This placeholder needs to be consistent if used
                    classroom_to_filter = None
                # If classroom_to_filter is empty (e.g. not set), it might also mean fetch all or do nothing.
                # For now, if it's empty, it will pass None to the backend.

        students_data = student_manager.get_students_sorted_by_points(classroom_filter=classroom_to_filter)

        if not students_data:
            no_data_label = ctk.CTkLabel(self.leaderboard_scroll_frame, text="No hay datos para mostrar.", font=BODY_FONT)
            no_data_label.pack(pady=30, padx=10)
            return

        entry_icon = self.load_icon("students", size=(24,24))

        gold_color = ("#FFD700", "#B8860B")    # Updated Gold
        silver_color = ("#E0E0E0", "#A0A0A0")  # Updated Silver
        bronze_color = ("#CD7F32", "#8C581E")  # Updated Bronze
        default_item_color = ("#FFFFFF", "#2B2B2B") # Verified: Remains as specified

        for i, student in enumerate(students_data):
            rank = i + 1

            item_bg_color = default_item_color
            name_font_size_increase = 0
            rank_font_size = 18

            if rank == 1:
                item_bg_color = gold_color
                name_font_size_increase = 2
                rank_font_size = 20
            elif rank == 2:
                item_bg_color = silver_color
            elif rank == 3:
                item_bg_color = bronze_color
            # else: # For alternating row colors if desired for ranks > 3
                # if i % 2 == 0:
                #     item_bg_color = ("#F0F0F0", "#303030")
                # else:
                #     item_bg_color = default_item_color # Or another color for odd rows

            item_frame = ctk.CTkFrame(self.leaderboard_scroll_frame, corner_radius=6, border_width=1, border_color=("gray70", "gray40"), fg_color=item_bg_color) # border_color adjusted slightly
            item_frame.pack(fill="x", pady=8, padx=10)

            rank_label = ctk.CTkLabel(item_frame, text=f"#{rank}", font=(APP_FONT_FAMILY, rank_font_size, "bold"))
            rank_label.pack(side="left", padx=(10,15), pady=10)

            if entry_icon:
                icon_label = ctk.CTkLabel(item_frame, image=entry_icon, text="")
                icon_label.pack(side="left", padx=(0,10), pady=10)

            details_frame = ctk.CTkFrame(item_frame, fg_color="transparent") # Transparent to show item_frame color
            details_frame.pack(side="left", padx=10, pady=(8,8), expand=True, fill="x")

            name_text = student.get('name', 'N/A')
            points_text = student.get('points', 0)
            classroom_text = student.get('classroom', 'N/A')

            base_name_font_size = 16
            name_label_font = (APP_FONT_FAMILY, base_name_font_size + name_font_size_increase, "bold")
            name_label = ctk.CTkLabel(details_frame, text=name_text, font=name_label_font, anchor="w")
            name_label.pack(fill="x", pady=(0,2))

            points_label_text = f"{points_text} Puntos"
            if filter_type == "🏆 Global":
                points_label_text += f"  |  Clase: {classroom_text}"

            points_label = ctk.CTkLabel(details_frame, text=points_label_text, font=BODY_FONT, anchor="w")
            points_label.pack(fill="x")

    # def um_toggle_password_visibility(self): # Optional helper
    #     if self.um_show_password_var.get() == "on":
    #         self.um_password_entry.configure(show="")
    #         self.um_confirm_password_entry.configure(show="")
    #     else:
    #         self.um_password_entry.configure(show="*")
    #         self.um_confirm_password_entry.configure(show="*")

    def prompt_lend_book_from_view_tab(self, book_id):
        book_details = book_manager.get_book_by_id_db(book_id)
        if not book_details:
            messagebox.showerror("Error", f"No se pudo encontrar el libro con ID: {book_id}")
            return

        book_title = book_details.get('titulo', 'Desconocido')

        dialog = ctk.CTkToplevel(self)
        dialog.title("Prestar Libro")
        dialog.geometry("450x350") # Adjusted size for more content
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: dialog.destroy()) # Ensure clean close

        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=15, pady=15)

        ctk.CTkLabel(main_frame, text=f"Prestar el libro: {book_title}", font=SUBHEADING_FONT).pack(pady=(0,10))

        # --- Borrowing Student Selection ---
        ctk.CTkLabel(main_frame, text="Seleccionar Alumno Prestatario:", font=BODY_FONT).pack(anchor="w", pady=(5,0))
        student_combo = ctk.CTkComboBox(main_frame, font=BODY_FONT, width=400, dropdown_font=BODY_FONT)
        student_combo.pack(fill="x", pady=(0,10))

        students = student_manager.get_students_db()
        student_name_to_id_map = {s['name']: s['id'] for s in students}
        student_names = list(student_name_to_id_map.keys())

        if student_names:
            student_combo.configure(values=student_names)
            student_combo.set(student_names[0])
        else:
            student_combo.configure(values=["No hay alumnos"], state="disabled")
            student_combo.set("No hay alumnos")

        # --- Lending Leader Selection ---
        ctk.CTkLabel(main_frame, text="Seleccionar Líder que Autoriza:", font=BODY_FONT).pack(anchor="w", pady=(5,0))
        leader_combo = ctk.CTkComboBox(main_frame, font=BODY_FONT, width=400, dropdown_font=BODY_FONT)
        leader_combo.pack(fill="x", pady=(0,15))

        leaders = student_manager.get_students_db(role_filter='leader')
        leader_name_to_id_map = {f"{l['name']} ({l['classroom']})": l['id'] for l in leaders}
        leader_names = list(leader_name_to_id_map.keys())

        if leader_names:
            leader_combo.configure(values=leader_names)
            leader_combo.set(leader_names[0])
        else:
            leader_combo.configure(values=["No hay líderes"], state="disabled")
            leader_combo.set("No hay líderes")

        # --- Confirm and Cancel Buttons ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10,0))
        button_frame.columnconfigure((0,1), weight=1) # Make buttons expand

        confirm_button = ctk.CTkButton(
            button_frame,
            text="Confirmar Préstamo",
            font=BUTTON_FONT,
            command=lambda: self._confirm_lend_action(
                dialog, book_id, student_combo, leader_combo,
                student_name_to_id_map, leader_name_to_id_map
            )
        )
        confirm_button.grid(row=0, column=0, padx=(0,5), sticky="ew")

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            font=BUTTON_FONT,
            command=dialog.destroy,
            fg_color="gray50", hover_color="gray60"
        )
        cancel_button.grid(row=0, column=1, padx=(5,0), sticky="ew")

        if not student_names or not leader_names: # Disable confirm if no students or no leaders
            confirm_button.configure(state="disabled")
            if not student_names:
                 ctk.CTkLabel(main_frame, text="No hay alumnos disponibles para prestar.", text_color="orange", font=BODY_FONT).pack(pady=(5,0))
            if not leader_names:
                 ctk.CTkLabel(main_frame, text="No hay líderes disponibles para autorizar.", text_color="orange", font=BODY_FONT).pack(pady=(5,0))


    def _confirm_lend_action(self, dialog, book_id, student_combo, leader_combo, student_map, leader_map):
        selected_student_name = student_combo.get()
        selected_leader_display_name = leader_combo.get()

        if selected_student_name == "No hay alumnos" or not selected_student_name:
            messagebox.showerror("Error de Selección", "Por favor, seleccione un alumno prestatario.", parent=dialog)
            return

        if selected_leader_display_name == "No hay líderes" or not selected_leader_display_name:
            messagebox.showerror("Error de Selección", "Por favor, seleccione un líder que autoriza.", parent=dialog)
            return

        student_id = student_map.get(selected_student_name)
        leader_id = leader_map.get(selected_leader_display_name)

        if not student_id:
            messagebox.showerror("Error Interno", f"No se pudo encontrar el ID para el alumno: {selected_student_name}", parent=dialog)
            return

        if not leader_id:
            messagebox.showerror("Error Interno", f"No se pudo encontrar el ID para el líder: {selected_leader_display_name}", parent=dialog)
            return

        due_date_str = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

        try:
            success = book_manager.loan_book_db(book_id, student_id, due_date_str, leader_id)
            if success:
                messagebox.showinfo("Éxito", "Libro prestado correctamente.", parent=dialog)
                self.refresh_book_list_ui() # Refresh the main book list
                if hasattr(self, 'refresh_loan_related_combos_and_lists'):
                    self.refresh_loan_related_combos_and_lists() # Refresh lists in manage loans tab
                dialog.destroy()
            else:
                # Check available count again, it might have changed
                available_count = book_manager.get_available_book_count(book_id)
                if available_count == 0:
                    messagebox.showerror("Error", "No se pudo prestar el libro. Ya no hay ejemplares disponibles.", parent=dialog)
                else:
                    messagebox.showerror("Error", "No se pudo prestar el libro. Verifique los datos o la consola.", parent=dialog)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {str(e)}", parent=dialog)
            print(f"Error during loan_book_db: {e}") # Log to console for debugging
            dialog.destroy() # Still destroy dialog on unexpected error


# Main execution
if __name__ == "__main__":
    # It's good practice to ensure DB is ready before app starts fully.
    # init_db() # This is already called in App.__init__

    app = App()
    app.mainloop()
