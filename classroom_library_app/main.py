import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from database.db_setup import init_db
import book_manager
import student_manager
from datetime import datetime, timedelta
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
        self.title("📚 Classroom Library Manager 🧸") # Added emojis for fun
        self.geometry("950x750") # Increased size for better spacing

        # self.configure(fg_color=COLOR_SECONDARY) # Main window background - might be handled by theme

        # Initialize database
        init_db()
        self.current_leader_id = None
        self.current_leader_classroom = None
        self.icon_cache = {} # For caching loaded icons

        # Main TabView
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=15, pady=15) # Increased padding

        self.manage_books_tab = self.tab_view.add("📖 Manage Books") # Added Emojis
        self.view_books_tab = self.tab_view.add("📚 View Books")
        self.manage_students_tab = self.tab_view.add("🧑‍🎓 Manage Students")
        self.manage_loans_tab = self.tab_view.add("🔄 Manage Loans")

        # Configure tabview appearance
        # self.tab_view.configure(segmented_button_selected_color=COLOR_ACCENT)
        # self.tab_view.configure(segmented_button_font=BUTTON_FONT)
        # self.tab_view.configure(tab_text_color=COLOR_TEXT)


        # Populate Tabs
        self.setup_manage_books_tab()
        self.setup_view_books_tab()
        self.setup_manage_students_tab()
        self.setup_manage_loans_tab()

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


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()
