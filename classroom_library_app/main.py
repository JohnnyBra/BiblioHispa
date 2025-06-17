import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
from PIL import Image, ImageTk
import os
import book_manager
import student_manager
import auth_manager

# --- Constantes de Estilo ---
APP_FONT_FAMILY = "Roboto"
HEADING_FONT = (APP_FONT_FAMILY, 24, "bold")
SUBHEADING_FONT = (APP_FONT_FAMILY, 16, "bold")
BODY_FONT = (APP_FONT_FAMILY, 12)
BUTTON_FONT = (APP_FONT_FAMILY, 12, "bold")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BiblioHispa - Sistema de Gestión de Biblioteca de Aula")
        self.geometry("1100x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.iconpath = self.load_icon("hispanidad_logo")
        if self.iconpath:
            self.iconphoto(True, self.iconpath)

        self.setup_login_ui()

    def load_icon(self, icon_name):
        # Asegura que la ruta es correcta sin importar desde dónde se ejecute el script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path_png = os.path.join(script_dir, "assets", f"{icon_name}.png")
        icon_path_ico = os.path.join(script_dir, "assets", f"{icon_name}.ico")

        if os.path.exists(icon_path_png):
            return tk.PhotoImage(file=icon_path_png)
        elif os.path.exists(icon_path_ico):
             # .ico puede necesitar un manejo especial o ser convertido, pero para Tkinter PhotoImage, a menudo se prefiere PNG.
             # Esta línea es más para compatibilidad con el método self.iconphoto.
            return tk.PhotoImage(file=icon_path_ico)
        else:
            print(f"Advertencia: No se encontró el icono '{icon_name}' en la ruta {icon_path_png} o {icon_path_ico}")
            return None

    def setup_login_ui(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=15)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        logo_image = self.load_icon("hispanidad_logo_medium")
        if logo_image:
            logo_label = ctk.CTkLabel(self.login_frame, image=logo_image, text="")
            logo_label.pack(pady=(20, 10))

        ctk.CTkLabel(self.login_frame, text="Bienvenido a BiblioHispa", font=HEADING_FONT).pack(pady=12, padx=40)

        ctk.CTkLabel(self.login_frame, text="Usuario", font=BODY_FONT).pack(anchor="w", padx=20)
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Nombre de usuario", width=250, font=BODY_FONT)
        self.username_entry.pack(pady=5, padx=20)

        ctk.CTkLabel(self.login_frame, text="Contraseña", font=BODY_FONT).pack(anchor="w", padx=20)
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Contraseña", show="*", width=250, font=BODY_FONT)
        self.password_entry.pack(pady=5, padx=20)
        self.password_entry.bind("<Return>", self.login_event)


        login_button = ctk.CTkButton(self.login_frame, text="Iniciar Sesión", command=self.login_event, font=BUTTON_FONT, corner_radius=8)
        login_button.pack(pady=20, padx=20)

    def login_event(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if auth_manager.authenticate_user(username, password):
            self.login_frame.destroy()
            self.setup_main_ui()
        else:
            CTkMessagebox(title="Error de Acceso", message="Usuario o contraseña incorrectos.", icon="cancel")

    def setup_main_ui(self):
        # Frame principal que contendrá todo
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True)

        # Frame del encabezado
        header_frame = ctk.CTkFrame(main_frame, corner_radius=0, height=60, fg_color=("#3498db", "#2b2b2b"))
        header_frame.pack(fill="x")

        title_label = ctk.CTkLabel(header_frame, text="BiblioHispa", font=HEADING_FONT, text_color=("white", "white"))
        title_label.pack(side="left", padx=20, pady=10)

        # Botón de cambio de tema
        theme_icon = self.load_icon("theme_switch")
        self.theme_button = ctk.CTkButton(header_frame, text="", image=theme_icon, width=32, command=self.toggle_theme, fg_color="transparent", hover_color=("#2980b9", "#343638"))
        self.theme_button.pack(side="right", padx=20)

        # Notebook para las pestañas
        self.tab_view = ctk.CTkTabview(main_frame, anchor="nw", text_color="black", segmented_button_selected_color="#3498db", segmented_button_selected_hover_color="#2980b9")
        self.tab_view.pack(pady=10, padx=20, fill="both", expand=True)

        # Crear pestañas
        self.manage_books_tab = self.tab_view.add("Gestionar Libros")
        self.view_books_tab = self.tab_view.add("Ver Libros")
        self.manage_students_tab = self.tab_view.add("Gestionar Alumnos")
        self.checkin_checkout_tab = self.tab_view.add("Préstamos y Devoluciones")

        # Configurar el contenido de cada pestaña
        self.setup_manage_books_tab()
        self.setup_view_books_tab()
        self.setup_manage_students_tab()
        self.setup_checkin_checkout_tab()

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    # --- Pestaña: Gestionar Libros ---
    def setup_manage_books_tab(self):
        tab = self.manage_books_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B"))

        # --- Frame para Añadir/Editar Libros ---
        add_edit_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_edit_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_edit_frame, text="Añadir Nuevo Libro", font=SUBHEADING_FONT).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        # Título
        ctk.CTkLabel(add_edit_frame, text="Título:", font=BODY_FONT).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.titulo_entry = ctk.CTkEntry(add_edit_frame, placeholder_text="Título del libro", font=BODY_FONT)
        self.titulo_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Autor
        ctk.CTkLabel(add_edit_frame, text="Autor:", font=BODY_FONT).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.autor_entry = ctk.CTkEntry(add_edit_frame, placeholder_text="Autor del libro", font=BODY_FONT)
        self.autor_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        # Género
        ctk.CTkLabel(add_edit_frame, text="Género:", font=BODY_FONT).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.genero_entry = ctk.CTkEntry(add_edit_frame, placeholder_text="Género literario", font=BODY_FONT)
        self.genero_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        # Ubicación
        ctk.CTkLabel(add_edit_frame, text="Ubicación:", font=BODY_FONT).grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.ubicacion_entry = ctk.CTkComboBox(add_edit_frame, values=["Salón A", "Salón B", "Salón C", "Biblioteca"], font=BODY_FONT, dropdown_font=BODY_FONT)
        self.ubicacion_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

        # Cantidad
        ctk.CTkLabel(add_edit_frame, text="Cantidad Total:", font=BODY_FONT).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.cantidad_entry = ctk.CTkEntry(add_edit_frame, placeholder_text="Número de copias", font=BODY_FONT)
        self.cantidad_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)


        add_edit_frame.columnconfigure(1, weight=1)

        # Botones
        button_frame = ctk.CTkFrame(add_edit_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        add_icon = self.load_icon("add_book")
        add_book_button = ctk.CTkButton(button_frame, text="Añadir Libro", image=add_icon, font=BUTTON_FONT, command=self.add_book_ui, corner_radius=8)
        add_book_button.pack(side="left", padx=5)

        clear_icon = self.load_icon("clear_form")
        clear_fields_button = ctk.CTkButton(button_frame, text="Limpiar Campos", image=clear_icon, font=BUTTON_FONT, command=self.clear_book_fields_ui, corner_radius=8, fg_color="gray50", hover_color="gray60")
        clear_fields_button.pack(side="left", padx=5)

        # --- Frame para Importar desde CSV ---
        import_frame = ctk.CTkFrame(tab, corner_radius=10)
        import_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(import_frame, text="Importar Libros desde CSV", font=SUBHEADING_FONT).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")
        import_icon = self.load_icon("import_csv")
        import_csv_button = ctk.CTkButton(import_frame, text="Importar desde CSV", image=import_icon, font=BUTTON_FONT, command=self.import_books_from_csv_ui, corner_radius=8)
        import_csv_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        # --- Frame para Eliminar Libros ---
        delete_frame = ctk.CTkFrame(tab, corner_radius=10)
        delete_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(delete_frame, text="Eliminar Libro", font=SUBHEADING_FONT).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        ctk.CTkLabel(delete_frame, text="Buscar libro a eliminar:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.delete_book_entry = ctk.CTkEntry(delete_frame, placeholder_text="ID, Título o Autor del libro", font=BODY_FONT)
        self.delete_book_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        delete_icon = self.load_icon("delete_book")
        delete_book_button = ctk.CTkButton(delete_frame, text="Eliminar Libro", image=delete_icon, font=BUTTON_FONT, command=self.delete_book_ui, corner_radius=8, fg_color="#E74C3C", hover_color="#C0392B")
        delete_book_button.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        delete_frame.columnconfigure(1, weight=1)

    def add_book_ui(self):
        titulo = self.titulo_entry.get()
        autor = self.autor_entry.get()
        genero = self.genero_entry.get()
        ubicacion = self.ubicacion_entry.get()
        cantidad_str = self.cantidad_entry.get()

        if not all([titulo, autor, ubicacion, cantidad_str]):
            CTkMessagebox(title="Error", message="Los campos Título, Autor, Ubicación y Cantidad son obligatorios.", icon="warning")
            return

        try:
            cantidad = int(cantidad_str)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            CTkMessagebox(title="Error", message="La cantidad debe ser un número entero positivo.", icon="warning")
            return

        success = book_manager.add_book_db(titulo, autor, genero, ubicacion, cantidad)
        if success:
            CTkMessagebox(title="Éxito", message=f"Libro '{titulo}' añadido correctamente.")
            self.clear_book_fields_ui()
            self.refresh_book_list_ui() # Actualizar la lista de libros visibles
        else:
            CTkMessagebox(title="Error", message="Error al añadir el libro a la base de datos.", icon="cancel")


    def clear_book_fields_ui(self):
        self.titulo_entry.delete(0, "end")
        self.autor_entry.delete(0, "end")
        self.genero_entry.delete(0, "end")
        self.ubicacion_entry.set("")
        self.cantidad_entry.delete(0, "end")

    def delete_book_ui(self):
        identifier = self.delete_book_entry.get()
        if not identifier:
            CTkMessagebox(title="Error", message="Por favor, introduce el ID, título o autor del libro a eliminar.", icon="warning")
            return

        msg = CTkMessagebox(title="Confirmar Eliminación",
                            message=f"¿Estás seguro de que quieres eliminar el libro '{identifier}'? Esta acción no se puede deshacer.",
                            icon="question", option_1="Cancelar", option_2="Eliminar")

        if msg.get() == "Eliminar":
            success, message = book_manager.delete_book_db(identifier)
            if success:
                CTkMessagebox(title="Éxito", message=message)
                self.delete_book_entry.delete(0, "end")
                self.refresh_book_list_ui() # Actualizar la vista de libros
            else:
                CTkMessagebox(title="Error", message=message, icon="cancel")

    def import_books_from_csv_ui(self):
        filepath = tk.filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*"))
        )
        if not filepath:
            return

        msg = CTkMessagebox(title="Confirmar Importación",
                            message="¿Estás seguro de que quieres importar libros desde este archivo? Los duplicados (basados en título y autor) serán ignorados.",
                            icon="question", option_1="Cancelar", option_2="Importar")

        if msg.get() == "Importar":
            success, message = book_manager.import_from_csv_db(filepath)
            if success:
                CTkMessagebox(title="Éxito", message=message)
                self.refresh_book_list_ui()
            else:
                CTkMessagebox(title="Error", message=message, icon="cancel")

    # --- Pestaña: Ver Libros ---
    def setup_view_books_tab(self):
        tab = self.view_books_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B"))
        controls_frame = ctk.CTkFrame(tab, corner_radius=10)
        controls_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(controls_frame, text="Filtrar por Ubicación:", font=BODY_FONT).grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.view_ubicacion_filter = ctk.CTkComboBox(controls_frame, values=["Todos", "Salón A", "Salón B", "Salón C", "Biblioteca"], command=lambda x: self.refresh_book_list_ui(
        ), font=BODY_FONT, dropdown_font=BODY_FONT, width=150)  # Translated "All"
        self.view_ubicacion_filter.grid(row=0, column=1, padx=5, pady=10)
        self.view_ubicacion_filter.set("Todos")  # Translated "All"

        controls_frame.columnconfigure(1, weight=1)
        search_frame = ctk.CTkFrame(tab, corner_radius=10)
        search_frame.pack(pady=(0, 15), padx=15, fill="x")
        ctk.CTkLabel(search_frame, text="🔍 Buscar Libros:", font=SUBHEADING_FONT).pack(
            side="left", padx=(10, 10), pady=10)  # Translated
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Escribe para buscar por título o autor...", font=BODY_FONT, width=300)  # Translated
        self.search_entry.pack(side="left", padx=(
            0, 10), pady=10, expand=True, fill="x")
        search_icon = self.load_icon("search")
        search_button = ctk.CTkButton(search_frame, text="Buscar", image=search_icon, font=BUTTON_FONT,
                                      command=self.search_books_ui, width=100, corner_radius=8)  # Translated
        search_button.pack(side="left", padx=(0, 5), pady=10)
        clear_search_icon = self.load_icon("clear_search")
        clear_search_button = ctk.CTkButton(search_frame, text="Limpiar", image=clear_search_icon, font=BUTTON_FONT,
                                            command=self.clear_search_ui, width=80, corner_radius=8, fg_color="gray50", hover_color="gray60")  # Translated
        clear_search_button.pack(side="left", padx=(0, 10), pady=10)
        self.book_list_frame = ctk.CTkScrollableFrame(
            tab, label_text="Nuestra Maravillosa Colección de Libros", label_font=HEADING_FONT, corner_radius=10)  # Translated
        self.book_list_frame.pack(expand=True, fill="both", padx=15, pady=(0, 15))
        self.refresh_book_list_ui()

    def refresh_book_list_ui(self, books_to_display=None):
        for widget in self.book_list_frame.winfo_children():
            widget.destroy()
        ubicacion_val = self.view_ubicacion_filter.get() if hasattr(
            self, 'view_ubicacion_filter') else "Todos"  # Changed variable name and default
        if books_to_display is None:
            books = book_manager.get_all_books_db(
                # Changed "All" to "Todos"
                ubicacion_filter=ubicacion_val if ubicacion_val != "Todos" else None
            )
        else:
            books = books_to_display
        if not books:
            no_books_label = ctk.CTkLabel(
                self.book_list_frame, text="No se encontraron libros. Intenta cambiar los filtros o añadir nuevos libros.", font=BODY_FONT)  # Translated
            no_books_label.pack(pady=30, padx=10)
            return
        for i, book in enumerate(books):
            book_item_frame = ctk.CTkFrame(
                self.book_list_frame, corner_radius=6, border_width=1, border_color=("gray75", "gray30"))
            book_item_frame.pack(fill="x", pady=8, padx=8)
            book_item_frame.columnconfigure(1, weight=1)
            available_count = book_manager.get_available_book_count(book['id'])
            total_count = book.get('cantidad_total', 0)
            availability_text = f"Disponible: {available_count} / {total_count}"
            availability_color = "green" if available_count > 0 else "red"
            status_label = ctk.CTkLabel(book_item_frame, text=availability_text, font=(
                APP_FONT_FAMILY, 11, "bold"), text_color=availability_color, anchor="e")
            status_label.grid(row=0, column=1, padx=(5, 10), pady=(5, 0), sticky="ne")
            title_label = ctk.CTkLabel(
                book_item_frame, text=f"{book.get('titulo', 'N/A')}", font=(APP_FONT_FAMILY, 14, "bold"), anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
            author_label = ctk.CTkLabel(
                book_item_frame, text=f"por {book.get('autor', 'N/A')}", font=(APP_FONT_FAMILY, 11, "italic"), anchor="w")
            author_label.grid(row=1, column=0, columnspan=3,
                              padx=10, pady=(0, 5), sticky="w")
            info_text = f"Ubicación: {book.get('ubicacion', 'N/A')}"
            if book.get('genero'):
                info_text += f"  |  Género: {book.get('genero')}"
            info_label = ctk.CTkLabel(book_item_frame, text=info_text, font=(
                APP_FONT_FAMILY, 10), anchor="w")
            info_label.grid(row=2, column=0, columnspan=3,
                            padx=10, pady=(0, 8), sticky="w")

    def search_books_ui(self):
        query = self.search_entry.get()
        if not query:
            self.refresh_book_list_ui()  # Show all if query is empty
            return
        results_titulo = book_manager.search_books_db(query, search_field="titulo")
        results_autor = book_manager.search_books_db(query, search_field="autor")
        combined_results = {book['id']: book for book in results_titulo}
        for book in results_autor:
            combined_results[book['id']] = book
        self.refresh_book_list_ui(books_to_display=list(combined_results.values()))

    def clear_search_ui(self):
        self.search_entry.delete(0, "end")
        self.refresh_book_list_ui()
        
    # --- Pestaña: Gestionar Alumnos ---
    def setup_manage_students_tab(self):
        tab = self.manage_students_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B"))
        # Frame para añadir alumno
        add_student_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_student_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_student_frame, text="Añadir Nuevo Alumno", font=SUBHEADING_FONT).grid(
            row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        ctk.CTkLabel(add_student_frame, text="Nombre:", font=BODY_FONT).grid(
            row=1, column=0, sticky="w", padx=10, pady=5)
        self.student_name_entry = ctk.CTkEntry(
            add_student_frame, placeholder_text="Nombre completo del alumno", font=BODY_FONT)
        self.student_name_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(add_student_frame, text="Clase:", font=BODY_FONT).grid(
            row=2, column=0, sticky="w", padx=10, pady=5)
        self.student_class_entry = ctk.CTkEntry(
            add_student_frame, placeholder_text="Clase del alumno (ej. 5ºA)", font=BODY_FONT)
        self.student_class_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        add_student_frame.columnconfigure(1, weight=1)

        add_student_button = ctk.CTkButton(
            add_student_frame, text="Añadir Alumno", command=self.add_student_ui, font=BUTTON_FONT, corner_radius=8)
        add_student_button.grid(row=3, column=1, pady=10, padx=10, sticky="e")

        # Frame para listar y eliminar alumnos
        self.student_list_frame = ctk.CTkScrollableFrame(
            tab, label_text="Alumnos Registrados", label_font=SUBHEADING_FONT, corner_radius=10)
        self.student_list_frame.pack(expand=True, fill="both", padx=15, pady=15)
        self.refresh_student_list_ui()
        
    def add_student_ui(self):
        nombre = self.student_name_entry.get()
        clase = self.student_class_entry.get()
        if not nombre or not clase:
            CTkMessagebox(title="Error", message="Nombre y Clase son campos obligatorios.", icon="warning")
            return
        if student_manager.add_student_db(nombre, clase):
            CTkMessagebox(title="Éxito", message=f"Alumno '{nombre}' añadido correctamente.")
            self.student_name_entry.delete(0, "end")
            self.student_class_entry.delete(0, "end")
            self.refresh_student_list_ui()
        else:
            CTkMessagebox(title="Error", message="Error al añadir el alumno.", icon="cancel")

    def delete_student_ui(self, student_id):
        student = student_manager.get_student_by_id_db(student_id)
        if not student:
            CTkMessagebox(title="Error", message="No se pudo encontrar al alumno.", icon="cancel")
            return
        msg = CTkMessagebox(title="Confirmar Eliminación",
                            message=f"¿Estás seguro de que quieres eliminar al alumno '{student['nombre']}'? Se eliminarán también sus registros de préstamos.",
                            icon="question", option_1="Cancelar", option_2="Eliminar")
        if msg.get() == "Eliminar":
            if student_manager.delete_student_db(student_id):
                CTkMessagebox(title="Éxito", message="Alumno eliminado correctamente.")
                self.refresh_student_list_ui()
            else:
                CTkMessagebox(title="Error", message="Error al eliminar al alumno.", icon="cancel")

    def refresh_student_list_ui(self):
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()
        students = student_manager.get_all_students_db()
        if not students:
            ctk.CTkLabel(self.student_list_frame, text="No hay alumnos registrados.", font=BODY_FONT).pack(pady=20)
            return
        for student in students:
            item_frame = ctk.CTkFrame(self.student_list_frame)
            item_frame.pack(fill="x", pady=4, padx=5)
            label = ctk.CTkLabel(item_frame, text=f"{student['nombre']} - {student['clase']}", font=BODY_FONT)
            label.pack(side="left", padx=10, pady=5)
            delete_button = ctk.CTkButton(item_frame, text="Eliminar", width=80, command=lambda s_id=student['id']: self.delete_student_ui(s_id),
                                        fg_color="#E74C3C", hover_color="#C0392B", font=BUTTON_FONT, corner_radius=6)
            delete_button.pack(side="right", padx=10, pady=5)

    # --- Pestaña: Préstamos y Devoluciones ---
    def setup_checkin_checkout_tab(self):
        tab = self.checkin_checkout_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B"))

        # --- Frame para Préstamos (Check-out) ---
        checkout_frame = ctk.CTkFrame(tab, corner_radius=10)
        checkout_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(checkout_frame, text="Realizar un Préstamo (Check-out)", font=SUBHEADING_FONT).grid(
            row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        # Autocompletar libro
        ctk.CTkLabel(checkout_frame, text="Buscar Libro:", font=BODY_FONT).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.checkout_book_entry = ctk.CTkEntry(checkout_frame, placeholder_text="ID o Título del libro", font=BODY_FONT)
        self.checkout_book_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Autocompletar alumno
        ctk.CTkLabel(checkout_frame, text="Buscar Alumno:", font=BODY_FONT).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.checkout_student_entry = ctk.CTkEntry(checkout_frame, placeholder_text="ID o Nombre del alumno", font=BODY_FONT)
        self.checkout_student_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        checkout_frame.columnconfigure(1, weight=1)

        checkout_button = ctk.CTkButton(checkout_frame, text="Prestar Libro", command=self.checkout_book_ui, font=BUTTON_FONT, corner_radius=8)
        checkout_button.grid(row=3, column=1, sticky="e", padx=10, pady=10)

        # --- Frame para Devoluciones (Check-in) ---
        checkin_frame = ctk.CTkFrame(tab, corner_radius=10)
        checkin_frame.pack(pady=15, padx=15, fill="x")
        ctk.CTkLabel(checkin_frame, text="Realizar una Devolución (Check-in)", font=SUBHEADING_FONT).grid(
            row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        ctk.CTkLabel(checkin_frame, text="Buscar Libro a devolver:", font=BODY_FONT).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.checkin_book_entry = ctk.CTkEntry(checkin_frame, placeholder_text="ID o Título del libro", font=BODY_FONT)
        self.checkin_book_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        checkin_frame.columnconfigure(1, weight=1)

        checkin_button = ctk.CTkButton(checkin_frame, text="Devolver Libro", command=self.checkin_book_ui, font=BUTTON_FONT, corner_radius=8, fg_color="#5cb85c", hover_color="#4cae4c")
        checkin_button.grid(row=2, column=1, sticky="e", padx=10, pady=10)

        # --- Frame para ver Préstamos Activos ---
        self.loans_frame = ctk.CTkScrollableFrame(tab, label_text="Préstamos Activos", label_font=SUBHEADING_FONT, corner_radius=10)
        self.loans_frame.pack(expand=True, fill="both", padx=15, pady=15)
        self.refresh_active_loans_ui()

    def checkout_book_ui(self):
        book_identifier = self.checkout_book_entry.get()
        student_identifier = self.checkout_student_entry.get()
        if not book_identifier or not student_identifier:
            CTkMessagebox(title="Error", message="Se requieren los identificadores del libro y del alumno.", icon="warning")
            return
        success, message = book_manager.checkout_book_db(book_identifier, student_identifier)
        if success:
            CTkMessagebox(title="Éxito", message=message)
            self.checkout_book_entry.delete(0, "end")
            self.checkout_student_entry.delete(0, "end")
            self.refresh_active_loans_ui()
            self.refresh_book_list_ui() # Para actualizar la disponibilidad
        else:
            CTkMessagebox(title="Error", message=message, icon="cancel")

    def checkin_book_ui(self):
        book_identifier = self.checkin_book_entry.get()
        if not book_identifier:
            CTkMessagebox(title="Error", message="Se requiere el identificador del libro.", icon="warning")
            return
        success, message = book_manager.checkin_book_db(book_identifier)
        if success:
            CTkMessagebox(title="Éxito", message=message)
            self.checkin_book_entry.delete(0, "end")
            self.refresh_active_loans_ui()
            self.refresh_book_list_ui() # Para actualizar la disponibilidad
        else:
            CTkMessagebox(title="Error", message=message, icon="cancel")

    def refresh_active_loans_ui(self):
        for widget in self.loans_frame.winfo_children():
            widget.destroy()
        loans = book_manager.get_active_loans_db()
        if not loans:
            ctk.CTkLabel(self.loans_frame, text="No hay préstamos activos en este momento.", font=BODY_FONT).pack(pady=20)
            return
        for loan in loans:
            loan_text = f"Libro: '{loan['titulo']}' (ID: {loan['libro_id']}) prestado a {loan['nombre_alumno']} ({loan['clase_alumno']}) el {loan['fecha_prestamo']}"
            ctk.CTkLabel(self.loans_frame, text=loan_text, font=BODY_FONT, wraplength=800, justify="left").pack(anchor="w", padx=10, pady=5)

if __name__ == "__main__":
    book_manager.init_database()
    student_manager.init_database()
    auth_manager.init_database()
    app = App()
    app.mainloop()
