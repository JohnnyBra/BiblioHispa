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
        self.title("📚 Classroom Library Manager 🧸")
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
        self.login_window.title("Login")
        self.login_window.geometry("350x250")
        self.login_window.transient(self) # Make it appear on top of the main window (if visible)
        self.login_window.grab_set() # Make it modal
        self.login_window.protocol("WM_DELETE_WINDOW", self.quit_application) # Handle window close

        ctk.CTkLabel(self.login_window, text="Welcome! Please Login", font=HEADING_FONT).pack(pady=20)

        frame = ctk.CTkFrame(self.login_window)
        frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frame, text="Username (Name):", font=BODY_FONT).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        username_entry = ctk.CTkEntry(frame, font=BODY_FONT, width=200)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame, text="Password:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        password_entry = ctk.CTkEntry(frame, font=BODY_FONT, show="*", width=200)
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
                self.initialize_main_app_ui() # Initialize and show the main app
            else:
                error_label.configure(text="Login failed. Invalid username or password.")
                password_entry.delete(0, "end") # Clear password field
                username_entry.focus() # Set focus back to username

        button_frame = ctk.CTkFrame(self.login_window, fg_color="transparent")
        button_frame.pack(pady=10)

        login_button = ctk.CTkButton(button_frame, text="Login", font=BUTTON_FONT, command=login_action)
        login_button.pack(side="left", padx=10)

        quit_button = ctk.CTkButton(button_frame, text="Quit", font=BUTTON_FONT, command=self.quit_application, fg_color="gray50", hover_color="gray60")
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

        self.manage_books_tab = self.tab_view.add("📖 Manage Books")
        self.view_books_tab = self.tab_view.add("📚 View Books")
        self.manage_students_tab = self.tab_view.add("🧑‍🎓 Manage Students") # Original student management
        self.manage_loans_tab = self.tab_view.add("🔄 Manage Loans")

        # Conditionally add User Management Tab
        if auth_manager.is_admin():
            self.manage_users_tab = self.tab_view.add("👤 User Management") # Advanced user management
            if hasattr(self, 'setup_manage_users_tab'): # Ensure method exists
                 self.setup_manage_users_tab()
            else:
                print("Error: setup_manage_users_tab method not found but was expected for admin.")
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
        add_book_frame = ctk.CTkFrame(tab, corner_radius=10) # Added corner_radius
        add_book_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_book_frame, text="✨ Add a Magical New Book! ✨", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15))

        ctk.CTkLabel(add_book_frame, text="Title:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.title_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="e.g., The Little Prince")
        self.title_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="Author:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.author_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="e.g., Antoine de Saint-Exupéry")
        self.author_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="ISBN:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=8, sticky="w")
        self.isbn_entry = ctk.CTkEntry(add_book_frame, width=300, font=BODY_FONT, placeholder_text="Optional, e.g., 978-0156012195")
        self.isbn_entry.grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_book_frame, text="Classroom:", font=BODY_FONT).grid(row=4, column=0, padx=10, pady=8, sticky="w")
        self.classroom_combobox = ctk.CTkComboBox(add_book_frame, values=["Class A", "Class B", "Class C", "Class D"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT)
        self.classroom_combobox.grid(row=4, column=1, padx=10, pady=8, sticky="ew")
        self.classroom_combobox.set("Class A")

        add_book_icon = self.load_icon("add_book") # Example: assets/icons/add_book.png
        add_button = ctk.CTkButton(add_book_frame, text="Add Book to Library", image=add_book_icon, font=BUTTON_FONT, command=self.add_book_ui, corner_radius=8)
        add_button.grid(row=5, column=0, columnspan=2, pady=15, padx=10, sticky="ew")
        add_book_frame.columnconfigure(1, weight=1) # Make entry column expandable

        # --- Import CSV Section ---
        import_csv_frame = ctk.CTkFrame(tab, corner_radius=10)
        import_csv_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(import_csv_frame, text="📤 Import Books from CSV File 📤", font=HEADING_FONT).pack(pady=(10,15))

        import_csv_icon = self.load_icon("import_csv") # Example: assets/icons/import_csv.png
        import_button = ctk.CTkButton(import_csv_frame, text="Select CSV File", image=import_csv_icon, font=BUTTON_FONT, command=self.import_csv_ui, corner_radius=8)
        import_button.pack(pady=10, padx=60, fill="x")


    def add_book_ui(self):
        title = self.title_entry.get()
        author = self.author_entry.get()
        isbn = self.isbn_entry.get()
        classroom = self.classroom_combobox.get()

        if not title or not author or not classroom:
            messagebox.showerror("Hold on! 🚧", "Oops! Title, Author, and Classroom are needed to add a new book.")
            return

        book_id = book_manager.add_book_db(title, author, classroom, isbn if isbn else None)

        if book_id:
            messagebox.showinfo("Hooray! 🎉", f"Great job! Book '{title}' has been successfully added to the library!")
            self.title_entry.delete(0, "end")
            self.author_entry.delete(0, "end")
            self.isbn_entry.delete(0, "end")
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui()
            if hasattr(self, 'refresh_loan_related_combos_and_lists'): self.refresh_loan_related_combos_and_lists()
        else:
            messagebox.showerror("Uh oh! 😟", "Oh no! Something went wrong while adding the book. Please check the details or console.")

    def import_csv_ui(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not file_path:
            return

        import os
        if not os.path.exists("assets"):
            os.makedirs("assets")

        success_count, errors = book_manager.import_books_from_csv_db(file_path)

        summary_message = f"CSV Import Summary:\n\nSuccessfully imported {success_count} books."
        if errors:
            summary_message += "\n\nErrors encountered:\n" + "\n".join(f"- {e}" for e in errors)
            messagebox.showwarning("Import Partially Successful", summary_message)
        else:
            messagebox.showinfo("Import Successful", summary_message)
        self.refresh_book_list_ui()

    def setup_view_books_tab(self):
        tab = self.view_books_tab
        tab.configure(fg_color=("#E6F0FA", "#2B2B2B")) # Light blueish for light, slightly different dark

        controls_frame = ctk.CTkFrame(tab, corner_radius=10)
        controls_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(controls_frame, text="Filter by Classroom:", font=BODY_FONT).grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")
        self.view_classroom_filter = ctk.CTkComboBox(controls_frame, values=["All", "Class A", "Class B", "Class C", "Class D"], command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150)
        self.view_classroom_filter.grid(row=0, column=1, padx=5, pady=10)
        self.view_classroom_filter.set("All")

        ctk.CTkLabel(controls_frame, text="Filter by Status:", font=BODY_FONT).grid(row=0, column=2, padx=(10,5), pady=10, sticky="w")
        self.view_status_filter = ctk.CTkComboBox(controls_frame, values=["All", "available", "borrowed"], command=lambda x: self.refresh_book_list_ui(), font=BODY_FONT, dropdown_font=BODY_FONT, width=150)
        self.view_status_filter.grid(row=0, column=3, padx=5, pady=10)
        self.view_status_filter.set("All")

        controls_frame.columnconfigure((1,3), weight=1) # Allow comboboxes to take some space

        search_frame = ctk.CTkFrame(tab, corner_radius=10)
        search_frame.pack(pady=(0,15), padx=15, fill="x")

        ctk.CTkLabel(search_frame, text="🔍 Search Books:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=10)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type to search title or author...", font=BODY_FONT, width=300)
        self.search_entry.pack(side="left", padx=(0,10), pady=10, expand=True, fill="x")

        search_icon = self.load_icon("search")
        search_button = ctk.CTkButton(search_frame, text="Search", image=search_icon, font=BUTTON_FONT, command=self.search_books_ui, width=100, corner_radius=8)
        search_button.pack(side="left", padx=(0,5), pady=10)

        clear_search_icon = self.load_icon("clear_search")
        clear_search_button = ctk.CTkButton(search_frame, text="Clear", image=clear_search_icon, font=BUTTON_FONT, command=self.clear_search_ui, width=80, corner_radius=8, fg_color="gray50", hover_color="gray60")
        clear_search_button.pack(side="left", padx=(0,10), pady=10)

        self.book_list_frame = ctk.CTkScrollableFrame(tab, label_text="Our Wonderful Book Collection!", label_font=HEADING_FONT, corner_radius=10)
        self.book_list_frame.pack(expand=True, fill="both", padx=15, pady=(0,15))

        self.refresh_book_list_ui()

    def refresh_book_list_ui(self, books_to_display=None):
        for widget in self.book_list_frame.winfo_children():
            widget.destroy()

        classroom = self.view_classroom_filter.get() if hasattr(self, 'view_classroom_filter') else "All"
        status_filter_val = self.view_status_filter.get() if hasattr(self, 'view_status_filter') else "All"

        if books_to_display is None:
            books = book_manager.get_all_books_db(
                classroom_filter=classroom if classroom != "All" else None,
                status_filter=status_filter_val if status_filter_val != "All" else None
            )
        else:
            books = books_to_display

        if not books:
            no_books_label = ctk.CTkLabel(self.book_list_frame, text="Hmm, no books found here. Try changing filters or adding new books! 🧐", font=BODY_FONT)
            no_books_label.pack(pady=30, padx=10)
            return

        for i, book in enumerate(books):
            book_item_frame = ctk.CTkFrame(self.book_list_frame, corner_radius=6, border_width=1, border_color=("gray75", "gray30"))
            book_item_frame.pack(fill="x", pady=8, padx=8)

            # Basic grid layout for book item
            book_item_frame.columnconfigure(1, weight=1) # Allow details column to expand

            # Status Indicator (simple colored text for now)
            status_text = book.get('status', 'N/A').capitalize()
            status_color = "green" if status_text == "Available" else "orange" if status_text == "Borrowed" else ("#333333", "#DCE4EE") # Dark gray / Light gray

            status_label = ctk.CTkLabel(book_item_frame, text=f"● {status_text}", font=(APP_FONT_FAMILY, 11, "bold"), text_color=status_color, anchor="e")
            status_label.grid(row=0, column=2, padx=(5,10), pady=(5,0), sticky="ne")

            title_label = ctk.CTkLabel(book_item_frame, text=f"{book['title']}", font=(APP_FONT_FAMILY, 14, "bold"), anchor="w")
            title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5,2), sticky="w")

            author_label = ctk.CTkLabel(book_item_frame, text=f"by {book['author']}", font=(APP_FONT_FAMILY, 11, "italic"), anchor="w")
            author_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky="w")

            info_text = f"Classroom: {book['classroom']}"
            if book.get('isbn'):
                info_text += f"  |  ISBN: {book['isbn']}"
            info_label = ctk.CTkLabel(book_item_frame, text=info_text, font=(APP_FONT_FAMILY, 10), anchor="w")
            info_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(0,8), sticky="w")

            if book.get('image_path'):
                img_path_label = ctk.CTkLabel(book_item_frame, text=f"🖼️ Cover: {book['image_path']}", font=(APP_FONT_FAMILY, 9, "italic"), text_color="gray50", anchor="w")
                img_path_label.grid(row=3, column=0, columnspan=3, padx=10, pady=(0,5), sticky="w")


    def search_books_ui(self):
        query = self.search_entry.get()
        if not query:
            self.refresh_book_list_ui()
            return

        results_title = book_manager.search_books_db(query, "title")
        results_author = book_manager.search_books_db(query, "author")

        combined_results = {book['id']: book for book in results_title}
        for book in results_author:
            if book['id'] not in combined_results:
                combined_results[book['id']] = book

        self.refresh_book_list_ui(books_to_display=list(combined_results.values()))

    def clear_search_ui(self):
        self.search_entry.delete(0, "end")
        self.refresh_book_list_ui()

    def setup_manage_students_tab(self):
        tab = self.manage_students_tab
        tab.configure(fg_color=("#FAF0E6", "#2E2B28")) # Linen for light, dark brown/gray for dark

        add_student_frame = ctk.CTkFrame(tab, corner_radius=10)
        add_student_frame.pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(add_student_frame, text="🌟 Add a New Student Star! 🌟", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15))

        ctk.CTkLabel(add_student_frame, text="Student Name:", font=BODY_FONT).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.student_name_entry = ctk.CTkEntry(add_student_frame, width=300, font=BODY_FONT, placeholder_text="e.g., Luna Lovegood")
        self.student_name_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(add_student_frame, text="Classroom:", font=BODY_FONT).grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.student_classroom_combo = ctk.CTkComboBox(add_student_frame, values=["Class A", "Class B", "Class C", "Class D"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT)
        self.student_classroom_combo.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        self.student_classroom_combo.set("Class A")

        ctk.CTkLabel(add_student_frame, text="Role:", font=BODY_FONT).grid(row=3, column=0, padx=10, pady=8, sticky="w")
        self.student_role_combo = ctk.CTkComboBox(add_student_frame, values=["student", "leader"], width=300, font=BODY_FONT, dropdown_font=BODY_FONT)
        self.student_role_combo.grid(row=3, column=1, padx=10, pady=8, sticky="ew")
        self.student_role_combo.set("student")
        add_student_frame.columnconfigure(1, weight=1)

        add_student_icon = self.load_icon("add_student") # Example: assets/icons/add_student.png
        add_student_button = ctk.CTkButton(add_student_frame, text="Add Student", image=add_student_icon, font=BUTTON_FONT, command=self.add_student_ui, corner_radius=8)
        add_student_button.grid(row=4, column=0, columnspan=2, pady=15, padx=10, sticky="ew")

        students_list_frame_container = ctk.CTkFrame(tab, corner_radius=10)
        students_list_frame_container.pack(pady=(0,15), padx=15, expand=True, fill="both")

        list_header_frame = ctk.CTkFrame(students_list_frame_container, fg_color="transparent")
        list_header_frame.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(list_header_frame, text="🎓 Our Awesome Students 🎓", font=HEADING_FONT).pack(side="left", padx=10, pady=5)
        refresh_students_icon = self.load_icon("refresh")
        refresh_students_button = ctk.CTkButton(list_header_frame, text="Refresh", image=refresh_students_icon, font=BUTTON_FONT, command=self.refresh_student_list_ui, width=100, corner_radius=8)
        refresh_students_button.pack(side="right", padx=10, pady=5)

        self.students_list_frame = ctk.CTkScrollableFrame(students_list_frame_container, label_text="") # Label is now part of header_frame
        self.students_list_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.refresh_student_list_ui()

    def add_student_ui(self):
        name = self.student_name_entry.get()
        classroom = self.student_classroom_combo.get()
        role = self.student_role_combo.get()

        if not name or not classroom or not role:
            messagebox.showerror("Wait a Second! 🚦", "Oops! Name, Classroom, and Role are required to add a student.")
            return

        student_id = student_manager.add_student_db(name, classroom, role)
        if student_id:
            messagebox.showinfo("Fantastic! ✨", f"Student '{name}' has joined the roster!")
            self.student_name_entry.delete(0, "end")
            self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'):
                 self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Oh Dear! 💔", "Something went wrong adding the student. Please check the console.")

    def refresh_student_list_ui(self):
        if not hasattr(self, 'students_list_frame'):
            return

        for widget in self.students_list_frame.winfo_children():
            widget.destroy()

        students = student_manager.get_students_db()

        if not students:
            no_students_label = ctk.CTkLabel(self.students_list_frame, text="No students found.", font=ctk.CTkFont(size=14))
            no_students_label.pack(pady=20)
            return

        for i, student in enumerate(students):
            student_item_frame = ctk.CTkFrame(self.students_list_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            student_item_frame.pack(fill="x", pady=(2,0), padx=5)
            details = f"Name: {student['name']} ({student['role']})\nClassroom: {student['classroom']} | ID: {student['id']}" # Show ID for now
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
        ctk.CTkLabel(leader_selection_frame, text="👑 Select Acting Student Leader:", font=SUBHEADING_FONT).pack(side="left", padx=(10,10), pady=10)
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
        ctk.CTkLabel(lend_frame, text="➡️ Lend a Book", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w")

        ctk.CTkLabel(lend_frame, text="Book:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.lend_book_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.lend_book_combo.grid(row=1, column=1, padx=5, pady=8, sticky="ew")

        ctk.CTkLabel(lend_frame, text="Borrower:", font=BODY_FONT).grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.borrower_combo = ctk.CTkComboBox(lend_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.borrower_combo.grid(row=2, column=1, padx=5, pady=8, sticky="ew")

        ctk.CTkLabel(lend_frame, text="Due Date:", font=BODY_FONT).grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.due_date_entry = ctk.CTkEntry(lend_frame, placeholder_text=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), width=280, font=BODY_FONT)
        self.due_date_entry.grid(row=3, column=1, padx=5, pady=8, sticky="ew")
        lend_frame.columnconfigure(1, weight=1)

        lend_icon = self.load_icon("lend_book")
        lend_button = ctk.CTkButton(lend_frame, text="Lend Book", image=lend_icon, font=BUTTON_FONT, command=self.lend_book_ui, corner_radius=8)
        lend_button.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        # --- Return Book Section ---
        return_frame = ctk.CTkFrame(left_frame, corner_radius=8)
        return_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(return_frame, text="⬅️ Return a Book", font=HEADING_FONT).grid(row=0, column=0, columnspan=2, pady=(10,15), sticky="w")

        ctk.CTkLabel(return_frame, text="Book:", font=BODY_FONT).grid(row=1, column=0, padx=5, pady=8, sticky="w") # Text changed for clarity
        self.return_book_combo = ctk.CTkComboBox(return_frame, width=280, state="disabled", font=BODY_FONT, dropdown_font=BODY_FONT)
        self.return_book_combo.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        return_frame.columnconfigure(1, weight=1)

        return_icon = self.load_icon("return_book")
        return_button = ctk.CTkButton(return_frame, text="Return Book", image=return_icon, font=BUTTON_FONT, command=self.return_book_ui, corner_radius=8)
        return_button.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

        right_frame = ctk.CTkFrame(main_loan_content_frame, fg_color="transparent")
        right_frame.pack(side="left", expand=True, fill="both", padx=(10,0), pady=0)

        loans_display_tabview = ctk.CTkTabview(right_frame, corner_radius=8)
        loans_display_tabview.pack(expand=True, fill="both")

        current_loans_tab = loans_display_tabview.add("Current Loans")
        reminders_tab = loans_display_tabview.add("⏰ Reminders")
        current_loans_tab.configure(fg_color=("#F5F5F5", "#343638"))
        reminders_tab.configure(fg_color=("#FFF0F5", "#383436"))


        self.current_loans_label = ctk.CTkLabel(current_loans_tab, text="Current Loans in [Select Leader's Classroom]", font=SUBHEADING_FONT)
        self.current_loans_label.pack(pady=10, padx=10)
        self.current_loans_frame = ctk.CTkScrollableFrame(current_loans_tab, label_text="", corner_radius=6)
        self.current_loans_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        self.reminders_label = ctk.CTkLabel(reminders_tab, text="Books Due Soon/Overdue in [Select Leader's Classroom]", font=SUBHEADING_FONT)
        self.reminders_label.pack(pady=10, padx=10)
        self.reminders_frame = ctk.CTkScrollableFrame(reminders_tab, label_text="", corner_radius=6)
        self.reminders_frame.pack(expand=True, fill="both", padx=10, pady=(0,10))

        self.refresh_leader_selector_combo() # Populate initially, which then calls on_leader_selected

    def refresh_leader_selector_combo(self):
        leaders = student_manager.get_students_db(role_filter='leader')
        self.leader_student_map = {f"{s['name']} ({s['classroom']})": s['id'] for s in leaders}
        leader_names = list(self.leader_student_map.keys())

        current_value = self.leader_selector_combo.get()

        self.leader_selector_combo.configure(values=leader_names if leader_names else ["No leaders found"])

        if leader_names:
            if current_value in leader_names: # Maintain current selection if still valid
                self.leader_selector_combo.set(current_value)
            else: # Default to first leader if current is invalid or no selection
                self.leader_selector_combo.set(leader_names[0])
            self.on_leader_selected(self.leader_selector_combo.get())
        else:
            self.leader_selector_combo.set("No leaders found")
            self.on_leader_selected(None)

    def on_leader_selected(self, selected_leader_display_name):
        if selected_leader_display_name and selected_leader_display_name != "No leaders found":
            self.current_leader_id = self.leader_student_map.get(selected_leader_display_name)
            leader_details = student_manager.get_student_by_id_db(self.current_leader_id)
            if leader_details:
                self.current_leader_classroom = leader_details['classroom']
                self.current_loans_label.configure(text=f"Current Loans in {self.current_leader_classroom}")
                self.reminders_label.configure(text=f"Books Due Soon/Overdue in {self.current_leader_classroom}")
                self.lend_book_combo.configure(state="normal")
                self.borrower_combo.configure(state="normal")
                self.return_book_combo.configure(state="normal")
            else:
                self.current_leader_id = None
                self.current_leader_classroom = None
        else:
            self.current_leader_id = None
            self.current_leader_classroom = None

        self.refresh_loan_related_combos_and_lists() # This will call update_loan_section_for_no_leader if needed

    def update_loan_section_for_no_leader(self):
        self.current_loans_label.configure(text="Current Loans (Select a Leader)")
        self.reminders_label.configure(text="Reminders (Select a Leader)")
        self.lend_book_combo.configure(values=["Select leader"], state="disabled")
        self.borrower_combo.configure(values=["Select leader"], state="disabled")
        self.return_book_combo.configure(values=["Select leader"], state="disabled")
        self.lend_book_combo.set("Select leader")
        self.borrower_combo.set("Select leader")
        self.return_book_combo.set("Select leader")

        for widget in self.current_loans_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.current_loans_frame, text="Please select a student leader to manage loans.").pack(pady=20, padx=10)
        for widget in self.reminders_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.reminders_frame, text="Please select a student leader to see reminders.").pack(pady=20, padx=10)

    def refresh_loan_related_combos_and_lists(self):
        if not self.current_leader_id or not self.current_leader_classroom:
            self.update_loan_section_for_no_leader()
            return

        # Populate Lend Book ComboBox
        available_books = book_manager.get_all_books_db(classroom_filter=self.current_leader_classroom, status_filter='available')
        self.lend_book_map = {f"{b['title']} (by {b['author']})": b['id'] for b in available_books}
        lend_book_display_names = list(self.lend_book_map.keys())
        self.lend_book_combo.configure(values=lend_book_display_names if lend_book_display_names else ["No available books"])
        self.lend_book_combo.set(lend_book_display_names[0] if lend_book_display_names else "No available books")

        # Populate Borrower ComboBox
        students_in_classroom = student_manager.get_students_by_classroom_db(self.current_leader_classroom)
        self.borrower_student_map = {s['name']: s['id'] for s in students_in_classroom}
        borrower_names = list(self.borrower_student_map.keys())
        self.borrower_combo.configure(values=borrower_names if borrower_names else ["No students in class"])
        self.borrower_combo.set(borrower_names[0] if borrower_names else "No students in class")

        # Populate Return Book ComboBox
        borrowed_books_in_class = book_manager.get_current_loans_db(classroom_filter=self.current_leader_classroom)
        self.return_book_map = {f"{b['title']} (Borrower: {b.get('borrower_name', 'N/A')})": b['id'] for b in borrowed_books_in_class}
        return_book_display_names = list(self.return_book_map.keys())
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
            datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format for Due Date. Use YYYY-MM-DD.")
            return

        book_id = self.lend_book_map.get(book_display_name)
        borrower_id = self.borrower_student_map.get(borrower_display_name)

        if not book_id or not borrower_id:
            messagebox.showerror("Internal Error", "Could not resolve book or borrower ID.")
            return

        success = book_manager.loan_book_db(book_id, borrower_id, due_date_str, self.current_leader_id)
        if success:
            messagebox.showinfo("Success", f"Book '{book_display_name.split(' (by ')[0]}' loaned to {borrower_display_name}.")
            self.due_date_entry.delete(0, 'end') # Clear entry for next use
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui() # Update main book list
        else:
            messagebox.showerror("Loan Failed", "Failed to loan book. See console for details (e.g., book not available, student/leader invalid).")

    def return_book_ui(self):
        if not self.current_leader_id:
            messagebox.showerror("Leader Not Selected", "Please select a student leader first.")
            return

        return_book_display_name = self.return_book_combo.get()
        if return_book_display_name == "No borrowed books":
            messagebox.showerror("Input Error", "Please select a book to return.")
            return

        book_id = self.return_book_map.get(return_book_display_name)
        if not book_id:
            messagebox.showerror("Internal Error", "Could not resolve book ID for return.")
            return

        success = book_manager.return_book_db(book_id, self.current_leader_id)
        if success:
            messagebox.showinfo("Success", f"Book returned successfully.")
            self.refresh_loan_related_combos_and_lists()
            if hasattr(self, 'refresh_book_list_ui'): self.refresh_book_list_ui() # Update main book list
        else:
            messagebox.showerror("Return Failed", "Failed to return book. See console for details (e.g., book not borrowed, leader invalid).")

    def refresh_current_loans_list(self):
        for widget in self.current_loans_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom: # No leader selected or leader has no classroom
             ctk.CTkLabel(self.current_loans_frame, text="Select a leader to view loans.").pack(pady=20, padx=10)
             return

        loans = book_manager.get_current_loans_db(classroom_filter=self.current_leader_classroom)
        if not loans:
            ctk.CTkLabel(self.current_loans_frame, text=f"No books currently loaned out in {self.current_leader_classroom}.").pack(pady=20, padx=10)
            return

        for i, loan in enumerate(loans):
            item_frame = ctk.CTkFrame(self.current_loans_frame, fg_color=("gray85", "gray17") if i%2 == 0 else ("gray80", "gray15"))
            item_frame.pack(fill="x", pady=(2,0), padx=5)
            details = f"Book: {loan['title']} (ISBN: {loan.get('isbn', 'N/A')})\n" \
                      f"Borrower: {loan.get('borrower_name', 'Unknown')}\n" \
                      f"Due Date: {loan['due_date']}"
            label = ctk.CTkLabel(item_frame, text=details, justify="left", anchor="w")
            label.pack(pady=5, padx=10, fill="x", expand=True)

    def refresh_reminders_list(self):
        for widget in self.reminders_frame.winfo_children(): widget.destroy()

        if not self.current_leader_classroom:
            ctk.CTkLabel(self.reminders_frame, text="Select a leader to view reminders.").pack(pady=20, padx=10)
            return

        due_soon_books = book_manager.get_books_due_soon_db(days_threshold=7, classroom_filter=self.current_leader_classroom)
        if not due_soon_books:
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
        tab.configure(fg_color=("#E9E9E9", "#3B3B3B")) # Neutral gray

        # Main frame for the tab
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Add User Section ---
        add_user_outer_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        add_user_outer_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(add_user_outer_frame, text="➕ Add New User / Edit User", font=HEADING_FONT).grid(row=0, column=0, columnspan=3, pady=(10,15), padx=10)

        ctk.CTkLabel(add_user_outer_frame, text="Name:", font=BODY_FONT).grid(row=1, column=0, padx=(10,5), pady=8, sticky="w")
        self.um_name_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, placeholder_text="Full Name")
        self.um_name_entry.grid(row=1, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")

        ctk.CTkLabel(add_user_outer_frame, text="Password:", font=BODY_FONT).grid(row=2, column=0, padx=(10,5), pady=8, sticky="w")
        self.um_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Enter password")
        self.um_password_entry.grid(row=2, column=1, padx=(0,5), pady=8, sticky="ew")

        ctk.CTkLabel(add_user_outer_frame, text="Confirm:", font=BODY_FONT).grid(row=3, column=0, padx=(10,5), pady=8, sticky="w")
        self.um_confirm_password_entry = ctk.CTkEntry(add_user_outer_frame, font=BODY_FONT, show="*", placeholder_text="Confirm password")
        self.um_confirm_password_entry.grid(row=3, column=1, padx=(0,5), pady=8, sticky="ew")

        # Toggle password visibility (Optional - can be added later if desired)
        # self.um_show_password_var = ctk.StringVar(value="off")
        # show_password_check = ctk.CTkCheckBox(add_user_outer_frame, text="Show", variable=self.um_show_password_var, onvalue="on", offvalue="off", command=self.um_toggle_password_visibility, font=BODY_FONT)
        # show_password_check.grid(row=2, column=2, rowspan=2, padx=(0,10), pady=8, sticky="w")


        ctk.CTkLabel(add_user_outer_frame, text="Classroom:", font=BODY_FONT).grid(row=4, column=0, padx=(10,5), pady=8, sticky="w")
        self.um_classroom_combo = ctk.CTkComboBox(add_user_outer_frame, values=["Class A", "Class B", "Class C", "Class D", "AdminOffice"], font=BODY_FONT, dropdown_font=BODY_FONT)
        self.um_classroom_combo.grid(row=4, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")
        self.um_classroom_combo.set("Class A")

        ctk.CTkLabel(add_user_outer_frame, text="Role:", font=BODY_FONT).grid(row=5, column=0, padx=(10,5), pady=8, sticky="w")
        self.um_role_combo = ctk.CTkComboBox(add_user_outer_frame, values=["student", "leader", "admin"], font=BODY_FONT, dropdown_font=BODY_FONT)
        self.um_role_combo.grid(row=5, column=1, columnspan=2, padx=(0,10), pady=8, sticky="ew")
        self.um_role_combo.set("student")

        add_user_outer_frame.columnconfigure(1, weight=1) # Make entry column expandable

        self.um_add_user_button = ctk.CTkButton(add_user_outer_frame, text="Add User", font=BUTTON_FONT, command=self.add_user_ui, corner_radius=8)
        self.um_add_user_button.grid(row=6, column=0, padx=(10,5), pady=15, sticky="ew")

        self.um_update_user_button = ctk.CTkButton(add_user_outer_frame, text="Update Selected User", font=BUTTON_FONT, command=self.edit_user_ui, corner_radius=8, state="disabled")
        self.um_update_user_button.grid(row=6, column=1, padx=(5,5), pady=15, sticky="ew")

        self.um_clear_form_button = ctk.CTkButton(add_user_outer_frame, text="Clear Form", font=BUTTON_FONT, command=self.clear_user_form_ui, corner_radius=8, fg_color="gray50", hover_color="gray60")
        self.um_clear_form_button.grid(row=6, column=2, padx=(5,10), pady=15, sticky="ew")


        # --- User List Section ---
        user_list_container = ctk.CTkFrame(main_frame, corner_radius=10)
        user_list_container.pack(pady=10, padx=10, expand=True, fill="both")

        list_header = ctk.CTkFrame(user_list_container, fg_color="transparent")
        list_header.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(list_header, text="👥 Registered Users", font=HEADING_FONT).pack(side="left", padx=10, pady=5)
        refresh_icon = self.load_icon("refresh")
        refresh_button = ctk.CTkButton(list_header, text="Refresh List", image=refresh_icon, font=BUTTON_FONT, command=self.refresh_user_list_ui, width=120, corner_radius=8)
        refresh_button.pack(side="right", padx=10, pady=5)

        self.user_list_scroll_frame = ctk.CTkScrollableFrame(user_list_container, label_text="")
        self.user_list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # --- User Actions Section (for selected user) ---
        actions_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        actions_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(actions_frame, text="Actions for Selected User:", font=SUBHEADING_FONT).pack(side="left", padx=(10,15), pady=10)

        delete_icon = self.load_icon("delete")
        self.um_delete_button = ctk.CTkButton(actions_frame, text="Delete", image=delete_icon, font=BUTTON_FONT, command=self.delete_user_ui, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", corner_radius=8)
        self.um_delete_button.pack(side="left", padx=5, pady=10)

        reset_pass_icon = self.load_icon("reset_password") # You'll need an icon like 'reset_password.png'
        self.um_reset_password_button = ctk.CTkButton(actions_frame, text="Reset Password", image=reset_pass_icon, font=BUTTON_FONT, command=self.reset_user_password_ui, state="disabled", corner_radius=8)
        self.um_reset_password_button.pack(side="left", padx=5, pady=10)

        self.refresh_user_list_ui() # Initial population

    def clear_user_form_ui(self, clear_selection=True):
        self.um_name_entry.delete(0, "end")
        self.um_password_entry.delete(0, "end")
        self.um_confirm_password_entry.delete(0, "end")
        self.um_classroom_combo.set("Class A") # Reset to default
        self.um_role_combo.set("student")    # Reset to default
        if clear_selection:
            self.selected_user_id_manage_tab = None
            self.um_delete_button.configure(state="disabled")
            self.um_reset_password_button.configure(state="disabled")
            self.um_update_user_button.configure(state="disabled", text="Update Selected User")
            self.um_add_user_button.configure(state="normal")
            self.um_name_entry.focus() # Set focus back to name entry

    def select_user_for_management(self, user_id, user_data):
        self.selected_user_id_manage_tab = user_id
        self.um_delete_button.configure(state="normal")
        self.um_reset_password_button.configure(state="normal")
        self.um_update_user_button.configure(state="normal", text=f"Save Changes for {user_data.get('name', '')[:15]}")
        self.um_add_user_button.configure(state="disabled") # Disable "Add User" when editing

        # Populate form for editing
        self.um_name_entry.delete(0, "end")
        self.um_name_entry.insert(0, user_data.get('name', ''))
        self.um_password_entry.delete(0, "end") # Clear password fields for editing
        self.um_confirm_password_entry.delete(0, "end")
        self.um_password_entry.configure(placeholder_text="Enter new password if changing")
        self.um_confirm_password_entry.configure(placeholder_text="Confirm new password")
        self.um_classroom_combo.set(user_data.get('classroom', 'Class A'))
        self.um_role_combo.set(user_data.get('role', 'student'))

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
            ctk.CTkLabel(self.user_list_scroll_frame, text="No users found in the system.", font=BODY_FONT).pack(pady=20)
            return

        for i, user in enumerate(users):
            user_id = user['id']
            original_bg = ("gray85", "gray20") if i % 2 == 0 else ("gray90", "gray25")
            item_frame = ctk.CTkFrame(self.user_list_scroll_frame, corner_radius=5, fg_color=original_bg)
            item_frame.pack(fill="x", pady=(3,0), padx=5)
            item_frame._user_id_ref = user_id # Store id for reference
            item_frame._original_bg = original_bg # Store original color for de-selection

            # User details
            details_text = f"👤 {user['name']} ({user['role']}) - 🏫 {user['classroom']}"
            # Small ID display: f"ID: {user_id[:8]}..."
            id_label = ctk.CTkLabel(item_frame, text=f"ID: {user_id[:8]}...", font=(APP_FONT_FAMILY, 9, "italic"), text_color="gray")
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
            self.um_update_user_button.configure(state="disabled", text="Update Selected User")
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
            messagebox.showerror("Input Error", "All fields (Name, Password, Confirm Password, Classroom, Role) are required.")
            return
        if password != confirm_password:
            messagebox.showerror("Password Mismatch", "Passwords do not match. Please re-enter.")
            self.um_password_entry.delete(0, "end")
            self.um_confirm_password_entry.delete(0, "end")
            self.um_password_entry.focus()
            return

        # student_manager.add_student_db expects (name, classroom, password, role)
        student_id = student_manager.add_student_db(name, classroom, password, role)
        if student_id:
            messagebox.showinfo("Success", f"User '{name}' added successfully with ID: {student_id}")
            self.clear_user_form_ui(clear_selection=False) # Keep form clear but don't reset selection logic if any
            self.refresh_user_list_ui()
            # Also refresh other student lists if they exist (e.g., in Manage Students or Loans tab)
            if hasattr(self, 'refresh_student_list_ui'): self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'): self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Database Error", f"Failed to add user '{name}'. Check console for details.")

    def edit_user_ui(self):
        """ Handles updating an existing user's details using student_manager.update_student_details_db. """
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("No User Selected", "Please select a user from the list to update.")
            return

        user_id = self.selected_user_id_manage_tab
        new_name = self.um_name_entry.get()
        new_classroom = self.um_classroom_combo.get()
        new_role = self.um_role_combo.get()

        if not new_name: # Basic validation
            messagebox.showerror("Input Error", "Name field cannot be empty for an update.")
            self.um_name_entry.focus()
            return

        # Classroom and Role are from ComboBox, so they'll always have a value.

        success = student_manager.update_student_details_db(user_id, new_name, new_classroom, new_role)

        if success:
            messagebox.showinfo("Update Successful", f"User '{new_name}' (ID: {user_id[:8]}) details have been updated.")
            self.clear_user_form_ui(clear_selection=True) # Resets form and selection state
            self.refresh_user_list_ui() # Refresh the user list in the current tab

            # Refresh other relevant UI parts if they exist
            if hasattr(self, 'refresh_student_list_ui'): # For the "Manage Students" tab
                self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'): # For the "Manage Loans" tab
                self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Update Failed", f"Could not update details for user '{new_name}'. Please check the console for errors or ensure the user exists.")

    def delete_user_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("No User Selected", "Please select a user from the list to delete.")
            return

        user_id = self.selected_user_id_manage_tab
        # Fetch user details for confirmation message
        user_details = student_manager.get_student_by_id_db(user_id)
        user_name = user_details['name'] if user_details else "the selected user"

        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete user '{user_name}' (ID: {user_id[:8]})?\nThis action cannot be undone."):
            return

        success = student_manager.delete_student_db(user_id)
        if success:
            messagebox.showinfo("Deletion Successful", f"User '{user_name}' has been deleted.")
            self.clear_user_form_ui(clear_selection=True)
            self.refresh_user_list_ui()
            # Also refresh other student lists if they exist
            if hasattr(self, 'refresh_student_list_ui'): self.refresh_student_list_ui()
            if hasattr(self, 'refresh_leader_selector_combo'): self.refresh_leader_selector_combo()
        else:
            messagebox.showerror("Deletion Failed", f"Failed to delete user '{user_name}'. They might be involved in active loans or an error occurred.")

    def reset_user_password_ui(self):
        if not self.selected_user_id_manage_tab:
            messagebox.showwarning("No User Selected", "Please select a user to reset their password.")
            return

        user_id = self.selected_user_id_manage_tab
        user_details = student_manager.get_student_by_id_db(user_id)
        user_name = user_details['name'] if user_details else "selected user"

        new_password = simpledialog.askstring("New Password", f"Enter new password for {user_name}:", show='*')
        if not new_password:
            messagebox.showinfo("Cancelled", "Password reset cancelled.")
            return

        confirm_new_password = simpledialog.askstring("Confirm New Password", "Confirm the new password:", show='*')
        if new_password != confirm_new_password:
            messagebox.showerror("Password Mismatch", "New passwords do not match. Password not reset.")
            return

        success = student_manager.update_student_password_db(user_id, new_password)
        if success:
            messagebox.showinfo("Password Reset", f"Password for user '{user_name}' has been successfully reset.")
        else:
            messagebox.showerror("Password Reset Failed", f"Failed to reset password for '{user_name}'.")

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
