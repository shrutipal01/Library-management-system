"""
================================================================================
Library Management System (LMS)
Course: Problem Solving Using Python (MCA17400) - Project-Based Learning (PBL)
================================================================================

A comprehensive, syllabus-oriented Library Management System implementing:
1. Object-Oriented Programming (Classes: Book, Student, Transaction, Library)
2. Control Structures (Conditions: if/elif/else for fine calculation, loan rules)
3. Iteration & Loops (for, while loops for menus, data processing, searches)
4. Data Structures & Collections (Lists, Dictionaries, Sets, Tuples)
5. Custom Sorting Algorithms (Bubble Sort & Python Timsort)
6. File Handling (Persistent JSON storage with backup/recovery)
7. Robust Exception Handling (Custom exceptions for domain business logic)
8. Scientific & Data Analysis Libraries (NumPy, Pandas, Matplotlib)
================================================================================
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Import project modules
from models import Book, Student, Transaction, MAX_BORROW_LIMIT, STANDARD_LOAN_DAYS
from exceptions import (
    LibraryError,
    BookNotFoundError,
    StudentNotFoundError,
    BookNotAvailableError,
    BookAlreadyIssuedError,
    StudentLimitExceededError,
    DuplicateRecordError,
    InvalidTransactionError,
    InvalidInputError,
)
from storage import (
    BOOKS_FILE,
    STUDENTS_FILE,
    TRANSACTIONS_FILE,
    save_to_file,
    load_from_file,
    generate_seed_data,
    ensure_data_directory,
)
from analytics import (
    get_system_summary_stats,
    generate_pandas_reports,
    generate_visual_charts,
)


class Library:
    """
    Central Library Controller class that manages catalogs, members, and transactions.
    
    Attributes:
        books (dict): Dictionary mapping book_id (str) -> Book object
        students (dict): Dictionary mapping student_id (str) -> Student object
        transactions (list): List of Transaction objects
    """
    def __init__(self, name="Central University MCA Library"):
        self.name = name
        self.books = {}          # Dictionary: {book_id: Book}
        self.students = {}       # Dictionary: {student_id: Student}
        self.transactions = []   # List: [Transaction, ...]
        self.load_data()

    # =========================================================================
    # FILE HANDLING: LOAD & SAVE OPERATIONS
    # =========================================================================
    def load_data(self):
        """
        Loads library records from JSON files into memory.
        If files do not exist, automatically creates seed data.
        Demonstrates syllabus concept: File Handling & Exception Handling.
        """
        ensure_data_directory()
        
        # Check if seed generation is necessary
        if not os.path.exists(BOOKS_FILE) or not os.path.exists(STUDENTS_FILE):
            print("[System] Initializing default seed catalog for demonstration...")
            generate_seed_data()

        # Load Books
        raw_books = load_from_file(BOOKS_FILE)
        self.books = {}
        for item in raw_books:
            try:
                book = Book.from_dict(item)
                self.books[book.book_id] = book
            except Exception as e:
                print(f"[Warning] Skipped malformed book record: {e}")

        # Load Students
        raw_students = load_from_file(STUDENTS_FILE)
        self.students = {}
        for item in raw_students:
            try:
                student = Student.from_dict(item)
                self.students[student.student_id] = student
            except Exception as e:
                print(f"[Warning] Skipped malformed student record: {e}")

        # Load Transactions
        raw_txns = load_from_file(TRANSACTIONS_FILE)
        self.transactions = []
        for item in raw_txns:
            try:
                txn = Transaction.from_dict(item)
                self.transactions.append(txn)
            except Exception as e:
                print(f"[Warning] Skipped malformed transaction record: {e}")

        print(f"[Loaded] {len(self.books)} Books | {len(self.students)} Students | {len(self.transactions)} Transactions.")

    def save_data(self):
        """
        Persists all in-memory records to disk using file handling.
        Returns True if all files saved successfully.
        """
        b_ok = save_to_file(BOOKS_FILE, [b.to_dict() for b in self.books.values()])
        s_ok = save_to_file(STUDENTS_FILE, [s.to_dict() for s in self.students.values()])
        t_ok = save_to_file(TRANSACTIONS_FILE, [t.to_dict() for t in self.transactions])
        return b_ok and s_ok and t_ok

    # =========================================================================
    # BOOK OPERATIONS
    # =========================================================================
    def add_book(self, book_id, title, author, genre="General", total_copies=1):
        """
        Adds a new book to the library catalog.
        Demonstrates conditions, custom exception handling, and dictionary storage.
        """
        book_id = str(book_id).strip().upper()
        if book_id in self.books:
            raise DuplicateRecordError("Book", book_id)
        
        new_book = Book(
            book_id=book_id,
            title=title,
            author=author,
            genre=genre,
            total_copies=int(total_copies),
            available_copies=int(total_copies),
            issue_count=0
        )
        self.books[book_id] = new_book
        self.save_data()
        return new_book

    def get_book(self, book_id):
        """Fetches a Book instance by ID or raises BookNotFoundError."""
        book_id = str(book_id).strip().upper()
        if book_id not in self.books:
            raise BookNotFoundError(book_id)
        return self.books[book_id]

    def display_available_books(self):
        """
        Returns a list of books that currently have at least one copy on shelf.
        Demonstrates list comprehension and condition evaluation.
        """
        return [b for b in self.books.values() if b.is_available()]

    def search_books(self, query, search_by="all"):
        """
        Searches books by title, author, or genre (case-insensitive).
        Demonstrates loops, string operations, and conditions.
        """
        query = str(query).strip().lower()
        if not query:
            return list(self.books.values())
        
        results = []
        for book in self.books.values():
            if search_by == "title" and query in book.title.lower():
                results.append(book)
            elif search_by == "author" and query in book.author.lower():
                results.append(book)
            elif search_by == "genre" and query in book.genre.lower():
                results.append(book)
            elif search_by == "all":
                if (query in book.title.lower() or
                    query in book.author.lower() or
                    query in book.genre.lower() or
                    query in book.book_id.lower()):
                    results.append(book)
        return results

    # =========================================================================
    # SORTING ALGORITHMS (Syllabus Requirement)
    # =========================================================================
    @staticmethod
    def bubble_sort_books(book_list, key="title", reverse=False):
        """
        Custom Bubble Sort algorithm implementation.
        Demonstrates syllabus requirement for fundamental sorting algorithms.
        
        Args:
            book_list (list): List of Book objects
            key (str): Attribute to sort by ('title', 'author', 'issue_count', 'available_copies')
            reverse (bool): Ascending (False) or Descending (True)
        """
        items = list(book_list)
        n = len(items)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                val1 = getattr(items[j], key)
                val2 = getattr(items[j + 1], key)
                
                # Case-insensitive comparison for strings
                if isinstance(val1, str):
                    val1 = val1.lower()
                if isinstance(val2, str):
                    val2 = val2.lower()

                condition = (val1 < val2) if reverse else (val1 > val2)
                if condition:
                    items[j], items[j + 1] = items[j + 1], items[j]
                    swapped = True
            if not swapped:
                break
        return items

    def sort_books(self, sort_by="title", use_custom_algorithm=False, reverse=False):
        """
        Sorts the catalog books. Can switch between custom Bubble Sort
        and Python's built-in Timsort.
        """
        book_list = list(self.books.values())
        if use_custom_algorithm:
            return self.bubble_sort_books(book_list, key=sort_by, reverse=reverse)
        else:
            return sorted(book_list, key=lambda b: getattr(b, sort_by), reverse=reverse)

    # =========================================================================
    # STUDENT / MEMBER OPERATIONS
    # =========================================================================
    def register_student(self, student_id, name, department="MCA", contact="N/A"):
        """
        Registers a new student/member.
        Validates uniqueness and non-empty values.
        """
        student_id = str(student_id).strip().upper()
        if student_id in self.students:
            raise DuplicateRecordError("Student", student_id)
        
        new_student = Student(student_id, name, department, contact)
        self.students[student_id] = new_student
        self.save_data()
        return new_student

    def get_student(self, student_id):
        """Retrieves a Student object by ID or raises StudentNotFoundError."""
        student_id = str(student_id).strip().upper()
        if student_id not in self.students:
            raise StudentNotFoundError(student_id)
        return self.students[student_id]

    def search_students(self, query):
        """Searches students by name, ID, or department."""
        query = str(query).strip().lower()
        if not query:
            return list(self.students.values())
        return [
            s for s in self.students.values()
            if query in s.name.lower() or query in s.student_id.lower() or query in s.department.lower()
        ]

    # =========================================================================
    # CIRCULATION / TRANSACTION OPERATIONS
    # =========================================================================
    def issue_book(self, student_id, book_id, custom_issue_date=None):
        """
        Issues a book to a student.
        Verifies:
        1. Student exists
        2. Student borrow limit has not been reached
        3. Student does not already hold a copy of this book
        4. Book exists
        5. Book has available stock
        """
        student = self.get_student(student_id)
        book = self.get_book(book_id)

        # Student validations
        if not student.can_borrow(MAX_BORROW_LIMIT):
            raise StudentLimitExceededError(student.name, MAX_BORROW_LIMIT)
        if book.book_id in student.borrowed_books:
            raise BookAlreadyIssuedError(student.name, book.title)

        # Book availability check
        if not book.is_available():
            raise BookNotAvailableError(book.title)

        # Update entity states
        book.issue()
        student.borrow_book(book.book_id)

        # Generate unique transaction ID
        txn_id = f"TXN{len(self.transactions) + 1001}"
        new_txn = Transaction(
            txn_id=txn_id,
            book_id=book.book_id,
            student_id=student.student_id,
            issue_date=custom_issue_date,
            status="ISSUED"
        )
        self.transactions.append(new_txn)
        self.save_data()
        return new_txn

    def return_book(self, student_id, book_id, custom_return_date=None):
        """
        Returns a borrowed book.
        Calculates overdue fine based on condition tiers.
        Updates book stock and student active loans.
        """
        student = self.get_student(student_id)
        book = self.get_book(book_id)

        # Find the active transaction
        active_txn = None
        for txn in reversed(self.transactions):
            if (txn.student_id == student.student_id and
                txn.book_id == book.book_id and
                txn.status == "ISSUED"):
                active_txn = txn
                break

        if not active_txn:
            raise InvalidTransactionError(
                f"No active issue record found for Book '{book.title}' with Student '{student.name}'."
            )

        # Calculate fine and mark returned
        fine = active_txn.mark_returned(custom_return_date)
        
        # Update model states
        student.return_book(book.book_id)
        book.return_copy()

        self.save_data()
        return active_txn, fine

    def get_active_transactions(self):
        """Returns all currently issued (unreturned) transactions."""
        return [t for t in self.transactions if t.status == "ISSUED"]

    def get_student_history(self, student_id):
        """Returns all transactions associated with a given student."""
        sid = str(student_id).strip().upper()
        return [t for t in self.transactions if t.student_id == sid]


# =============================================================================
# CONSOLE USER INTERFACE HELPERS
# =============================================================================
def print_banner():
    """Prints a styled banner for the application."""
    print("=" * 80)
    print("       LIBRARY MANAGEMENT SYSTEM — MCA17400 PYTHON PROJECT")
    print("     Department of Computer Applications | Modern Academic Edition")
    print("=" * 80)


def print_menu():
    """Displays main menu options."""
    print("\n" + "-" * 40 + " MAIN MENU " + "-" * 40)
    print("  [1] Book Management        (Add, View Available, Search, Sort Catalog)")
    print("  [2] Student Management     (Register, View All, Search, Loan History)")
    print("  [3] Circulation Desk       (Issue Book, Return Book & Fines, Active Loans)")
    print("  [4] Analytics & Statistics (NumPy Metrics, Pandas Tables, Matplotlib Charts)")
    print("  [5] Run System Diagnostics (Unit Tests: Valid & Invalid Input Validation)")
    print("  [6] Reset / Re-seed Data   (Restore Sample University Library Catalog)")
    print("  [0] Save & Exit System")
    print("-" * 91)


def display_books_table(book_list, header="BOOKS CATALOG"):
    """Displays a formatted tabular list of books using Pandas or ASCII formatting."""
    print(f"\n--- {header} ({len(book_list)} Records) ---")
    if not book_list:
        print("No books found matching the criteria.")
        return
    
    data = []
    for b in book_list:
        data.append({
            "Book ID": b.book_id,
            "Title": (b.title[:28] + "..") if len(b.title) > 30 else b.title,
            "Author": (b.author[:18] + "..") if len(b.author) > 20 else b.author,
            "Genre": b.genre,
            "Avail/Total": f"{b.available_copies}/{b.total_copies}",
            "Issues": b.issue_count
        })
    df = pd.DataFrame(data)
    print(df.to_string(index=False))


def display_students_table(student_list, header="STUDENTS DIRECTORY"):
    """Displays a formatted table of registered students."""
    print(f"\n--- {header} ({len(student_list)} Records) ---")
    if not student_list:
        print("No student records found.")
        return

    data = []
    for s in student_list:
        data.append({
            "Student ID": s.student_id,
            "Name": s.name,
            "Department": s.department,
            "Contact": s.contact,
            "Active Books": len(s.borrowed_books),
            "Book IDs": ", ".join(s.borrowed_books) if s.borrowed_books else "None"
        })
    df = pd.DataFrame(data)
    print(df.to_string(index=False))


def display_transactions_table(txn_list, header="TRANSACTION RECORDS"):
    """Displays formatted transactions table."""
    print(f"\n--- {header} ({len(txn_list)} Records) ---")
    if not txn_list:
        print("No transactions to display.")
        return

    data = []
    for t in txn_list:
        data.append({
            "Txn ID": t.txn_id,
            "Book ID": t.book_id,
            "Student ID": t.student_id,
            "Issued On": t.issue_date,
            "Due Date": t.due_date,
            "Status": t.status,
            "Fine (INR)": f"{t.fine_amount:.2f}"
        })
    df = pd.DataFrame(data)
    print(df.to_string(index=False))


# =============================================================================
# SUBMENU HANDLERS
# =============================================================================
def handle_book_management(library):
    """Submenu for Book catalog operations."""
    while True:
        print("\n" + "." * 30 + " BOOK MANAGEMENT " + "." * 30)
        print("  1. Add New Book to Catalog")
        print("  2. Display All Available Books (Currently on Shelf)")
        print("  3. Display Complete Books Catalog")
        print("  4. Search Books by Title, Author, or Genre")
        print("  5. Sort Books Catalog (Bubble Sort vs Timsort)")
        print("  0. Back to Main Menu")
        choice = input("Select an option [0-5]: ").strip()

        if choice == "1":
            print("\n[Add New Book]")
            bid = input("Enter Book ID (e.g. B113): ").strip()
            title = input("Enter Book Title: ").strip()
            author = input("Enter Author Name: ").strip()
            genre = input("Enter Genre/Subject (e.g. AI & ML, Web Dev): ").strip() or "General"
            copies_str = input("Enter Total Copies (Default 1): ").strip() or "1"
            
            try:
                copies = int(copies_str)
                new_book = library.add_book(bid, title, author, genre, copies)
                print(f"[Success] Book added: {new_book}")
            except (LibraryError, ValueError) as e:
                print(f"[Error] Failed to add book: {e}")

        elif choice == "2":
            avail = library.display_available_books()
            display_books_table(avail, "AVAILABLE BOOKS FOR ISSUE")

        elif choice == "3":
            display_books_table(list(library.books.values()), "COMPLETE LIBRARY CATALOG")

        elif choice == "4":
            print("\n[Search Books]")
            print("Filter by: 1. All Fields | 2. Title | 3. Author | 4. Genre")
            f_choice = input("Choice [1-4, Default 1]: ").strip() or "1"
            mode_map = {"1": "all", "2": "title", "3": "author", "4": "genre"}
            mode = mode_map.get(f_choice, "all")
            query = input(f"Enter search query for [{mode}]: ").strip()
            results = library.search_books(query, search_by=mode)
            display_books_table(results, f"SEARCH RESULTS FOR '{query}'")

        elif choice == "5":
            print("\n[Sort Books Catalog]")
            print("Sort criteria: 1. Title | 2. Author | 3. Most Issued (Popularity) | 4. Available Copies")
            sc = input("Select criteria [1-4]: ").strip()
            crit_map = {"1": "title", "2": "author", "3": "issue_count", "4": "available_copies"}
            sort_key = crit_map.get(sc, "title")
            
            algo = input("Use Custom Bubble Sort algorithm? (y/n, default n): ").strip().lower()
            use_bubble = (algo == 'y')
            
            reverse = True if sort_key in ["issue_count", "available_copies"] else False
            sorted_books = library.sort_books(sort_by=sort_key, use_custom_algorithm=use_bubble, reverse=reverse)
            algo_name = "Custom Bubble Sort" if use_bubble else "Python Standard Sort"
            display_books_table(sorted_books, f"SORTED BY {sort_key.upper()} ({algo_name})")

        elif choice == "0":
            break
        else:
            print("[Invalid] Please select a valid number.")


def handle_student_management(library):
    """Submenu for Student / Member operations."""
    while True:
        print("\n" + "." * 29 + " STUDENT MANAGEMENT " + "." * 29)
        print("  1. Register New Student / Member")
        print("  2. Display All Registered Students")
        print("  3. Search Student by ID or Name")
        print("  4. View Student Borrowing History & Active Loans")
        print("  0. Back to Main Menu")
        choice = input("Select an option [0-4]: ").strip()

        if choice == "1":
            print("\n[Register Student]")
            sid = input("Enter Student ID (e.g. MCA202610): ").strip()
            name = input("Enter Full Name: ").strip()
            dept = input("Enter Department (Default MCA): ").strip() or "MCA"
            contact = input("Enter Contact Email / Phone: ").strip() or "N/A"
            try:
                new_student = library.register_student(sid, name, dept, contact)
                print(f"[Success] Student registered: {new_student}")
            except LibraryError as e:
                print(f"[Error] Registration failed: {e}")

        elif choice == "2":
            display_students_table(list(library.students.values()), "REGISTERED STUDENTS DIRECTORY")

        elif choice == "3":
            query = input("Enter student name or ID to search: ").strip()
            results = library.search_students(query)
            display_students_table(results, f"STUDENT SEARCH RESULTS FOR '{query}'")

        elif choice == "4":
            sid = input("Enter Student ID: ").strip()
            try:
                student = library.get_student(sid)
                print(f"\nStudent Details: {student}")
                history = library.get_student_history(sid)
                display_transactions_table(history, f"TRANSACTION HISTORY FOR {student.name} ({sid})")
            except StudentNotFoundError as e:
                print(f"[Error] {e}")

        elif choice == "0":
            break
        else:
            print("[Invalid] Please select a valid option.")


def handle_circulation(library):
    """Submenu for issuing and returning books with overdue fine calculation."""
    while True:
        print("\n" + "." * 31 + " CIRCULATION DESK " + "." * 31)
        print("  1. Issue a Book to Student")
        print("  2. Return a Book (Calculate Overdue Fine)")
        print("  3. View All Currently Active Loans")
        print("  4. View Complete Transaction History")
        print("  0. Back to Main Menu")
        choice = input("Select an option [0-4]: ").strip()

        if choice == "1":
            print("\n[Issue Book]")
            sid = input("Enter Student ID: ").strip()
            bid = input("Enter Book ID: ").strip()
            custom_date = input("Enter Issue Date (YYYY-MM-DD or press Enter for Today): ").strip() or None
            
            try:
                txn = library.issue_book(sid, bid, custom_date)
                student = library.get_student(sid)
                book = library.get_book(bid)
                print("\n" + "=" * 50)
                print("           BOOK ISSUED SUCCESSFULLY")
                print("=" * 50)
                print(f"Transaction ID : {txn.txn_id}")
                print(f"Student        : {student.name} ({student.student_id})")
                print(f"Book           : {book.title} ({book.book_id})")
                print(f"Issue Date     : {txn.issue_date}")
                print(f"Due Date       : {txn.due_date} (14 days loan period)")
                print(f"Remaining Copy : {book.available_copies} of {book.total_copies}")
                print("=" * 50)
            except LibraryError as e:
                print(f"\n[Issue Failed] {e}")

        elif choice == "2":
            print("\n[Return Book & Overdue Fine Calculation]")
            sid = input("Enter Student ID: ").strip()
            bid = input("Enter Book ID: ").strip()
            ret_date = input("Enter Return Date (YYYY-MM-DD or press Enter for Today): ").strip() or None

            try:
                txn, fine = library.return_book(sid, bid, ret_date)
                student = library.get_student(sid)
                book = library.get_book(bid)
                _, overdue_days = Transaction.calculate_fine(txn.due_date, txn.return_date)

                print("\n" + "=" * 50)
                print("           BOOK RETURN RECEIPT")
                print("=" * 50)
                print(f"Transaction ID : {txn.txn_id}")
                print(f"Student        : {student.name} ({student.student_id})")
                print(f"Book           : {book.title} ({book.book_id})")
                print(f"Due Date       : {txn.due_date}")
                print(f"Returned On    : {txn.return_date}")
                print(f"Overdue Days   : {overdue_days} day(s)")
                print(f"Fine Charged   : INR {fine:.2f}")
                if fine > 0:
                    print("  * Note: Fines calculated per MCA Library Rules:")
                    print("    - 1-7 days: INR 2/day | 8-14 days: INR 5/day | >14 days: INR 10/day + INR 50 penalty")
                else:
                    print("  * Book returned on/before due date. No fine applicable!")
                print(f"Updated Stock  : {book.available_copies} of {book.total_copies} available")
                print("=" * 50)
            except LibraryError as e:
                print(f"\n[Return Failed] {e}")

        elif choice == "3":
            active_txns = library.get_active_transactions()
            display_transactions_table(active_txns, "ACTIVE BORROWED BOOKS")

        elif choice == "4":
            display_transactions_table(library.transactions, "ALL HISTORICAL TRANSACTIONS")

        elif choice == "0":
            break
        else:
            print("[Invalid] Please select a valid option.")


def handle_analytics(library):
    """Submenu for NumPy, Pandas, and Matplotlib analytics."""
    while True:
        print("\n" + "." * 27 + " ANALYTICS & STATISTICS " + "." * 27)
        print("  1. System Summary Statistics (NumPy Aggregations & Metrics)")
        print("  2. Top 5 Most Borrowed Books (Pandas Analysis)")
        print("  3. Category & Department Breakdown (Pandas DataFrames)")
        print("  4. Generate & Save Matplotlib Graphical Dashboard (Visual Charts)")
        print("  0. Back to Main Menu")
        choice = input("Select an option [0-4]: ").strip()

        if choice == "1":
            stats = get_system_summary_stats(library.books, library.students, library.transactions)
            print("\n" + "=" * 55)
            print("        LIBRARY NUMERICAL STATISTICS (NumPy)")
            print("=" * 55)
            print(f"Total Unique Titles Owned    : {stats['total_titles']}")
            print(f"Total Books Inventory Stock  : {stats['total_books_stock']} volumes")
            print(f"Books Available on Shelves   : {stats['total_available_stock']} volumes")
            print(f"Books Currently Issued Out   : {stats['total_currently_issued']} volumes")
            print(f"Registered Students/Members  : {stats['total_students']}")
            print(f"Members with Active Loans    : {stats['active_borrowers']}")
            print(f"Total Lifetime Transactions  : {stats['total_transactions']}")
            print("-" * 55)
            print(f"Total Overdue Fines Collected: INR {stats['total_fine_collected']:.2f}")
            print(f"Average Overdue Fine (NumPy) : INR {stats['avg_fine']:.2f}")
            print(f"Maximum Overdue Fine (NumPy) : INR {stats['max_fine']:.2f}")
            print(f"Mean Issues per Book Title   : {stats['mean_issues_per_book']:.2f}")
            print(f"Median Issues per Book Title : {stats['median_issues_per_book']:.2f}")
            print("=" * 55)

        elif choice == "2":
            reports = generate_pandas_reports(library.books, library.students, library.transactions)
            print("\n--- TOP 5 MOST ISSUED BOOKS (Pandas Ranked) ---")
            top = reports["top_books"]
            if not top.empty:
                print(top.to_string(index=False))
            else:
                print("No books found.")

        elif choice == "3":
            reports = generate_pandas_reports(library.books, library.students, library.transactions)
            print("\n--- BOOKS BY GENRE / SUBJECT (Pandas Series) ---")
            print(reports["genre_distribution"].to_string())
            
            print("\n--- STUDENTS BY DEPARTMENT (Pandas Series) ---")
            print(reports["dept_distribution"].to_string())

        elif choice == "4":
            print("\n[Generating Matplotlib Data Visualization Dashboard...]")
            chart_path = generate_visual_charts(library.books, library.students, library.transactions, show_gui=True)
            print(f"[Done] High-resolution chart saved to:\n       file:///{chart_path.replace(os.sep, '/')}")
            print("You can attach this PNG figure directly in your individual spiral-bound report!")

        elif choice == "0":
            break
        else:
            print("[Invalid] Please choose an option from 0 to 4.")


def run_unit_tests():
    """
    Executes unit test validation verifying both valid operations
    and invalid operations with proper exception handling.
    Demonstrates syllabus requirement: Testing with valid & invalid inputs.
    """
    print("\n" + "=" * 65)
    print("   RUNNING AUTOMATED TEST SUITE (VALID & INVALID TEST CASES)")
    print("=" * 65)
    
    passed = 0
    total = 0

    def assert_test(name, condition):
        nonlocal passed, total
        total += 1
        if condition:
            print(f"  [PASS] Test {total}: {name}")
            passed += 1
        else:
            print(f"  [FAIL] Test {total}: {name}")

    # Isolated test instance
    test_lib = Library.__new__(Library)
    test_lib.name = "Test Lib"
    test_lib.books = {}
    test_lib.students = {}
    test_lib.transactions = []
    test_lib.save_data = lambda: True

    # Test 1: Add valid book
    try:
        b = test_lib.add_book("TEST101", "Python Programming", "Guido van Rossum", "CS", 2)
        assert_test("Add valid book to catalog", b.book_id == "TEST101" and b.total_copies == 2)
    except Exception as e:
        assert_test(f"Add valid book failed with exception {e}", False)

    # Test 2: Add duplicate book ID (Invalid Input)
    try:
        test_lib.add_book("TEST101", "Another Book", "Author", "CS", 1)
        assert_test("Reject duplicate book ID with DuplicateRecordError", False)
    except DuplicateRecordError:
        assert_test("Reject duplicate book ID with DuplicateRecordError", True)
    except Exception as e:
        assert_test(f"Wrong exception for duplicate book: {e}", False)

    # Test 3: Register valid student
    try:
        s = test_lib.register_student("STU99", "Test Student", "MCA", "test@test.com")
        assert_test("Register valid student", s.student_id == "STU99")
    except Exception as e:
        assert_test(f"Register student failed: {e}", False)

    # Test 4: Issue book successfully
    try:
        txn = test_lib.issue_book("STU99", "TEST101")
        assert_test("Issue available book to eligible student", txn.status == "ISSUED" and test_lib.books["TEST101"].available_copies == 1)
    except Exception as e:
        assert_test(f"Issue book failed: {e}", False)

    # Test 5: Prevent borrowing same book twice (Invalid Operation)
    try:
        test_lib.issue_book("STU99", "TEST101")
        assert_test("Prevent borrowing the same book twice", False)
    except BookAlreadyIssuedError:
        assert_test("Prevent borrowing the same book twice with BookAlreadyIssuedError", True)
    except Exception as e:
        assert_test(f"Wrong exception: {e}", False)

    # Test 6: Borrowing non-existent book ID (Invalid Input)
    try:
        test_lib.issue_book("STU99", "NONEXISTENT")
        assert_test("Reject non-existent book ID with BookNotFoundError", False)
    except BookNotFoundError:
        assert_test("Reject non-existent book ID with BookNotFoundError", True)
    except Exception as e:
        assert_test(f"Wrong exception: {e}", False)

    # Test 7: Student borrow limit enforcement
    try:
        test_lib.add_book("TEST102", "Data Structures", "Author A", "CS", 1)
        test_lib.add_book("TEST103", "Algorithms", "Author B", "CS", 1)
        test_lib.add_book("TEST104", "Databases", "Author C", "CS", 1)
        test_lib.issue_book("STU99", "TEST102")
        test_lib.issue_book("STU99", "TEST103")
        # STU99 now has 3 books (MAX_BORROW_LIMIT). Attempting 4th:
        test_lib.issue_book("STU99", "TEST104")
        assert_test("Enforce student borrowing limit of 3 books", False)
    except StudentLimitExceededError:
        assert_test("Enforce student borrowing limit of 3 books with StudentLimitExceededError", True)
    except Exception as e:
        assert_test(f"Wrong exception: {e}", False)

    # Test 8: Book out of stock error
    try:
        # TEST102 has 0 available copies now
        test_lib.register_student("STU98", "Second Student", "MCA", "stu2@test.com")
        test_lib.issue_book("STU98", "TEST102")
        assert_test("Prevent issuing out-of-stock book", False)
    except BookNotAvailableError:
        assert_test("Prevent issuing out-of-stock book with BookNotAvailableError", True)
    except Exception as e:
        assert_test(f"Wrong exception: {e}", False)

    # Test 9: Fine calculation logic (0 days overdue = INR 0)
    fine_zero, days_zero = Transaction.calculate_fine("2026-10-10", "2026-10-09")
    assert_test("Overdue fine is INR 0 when returned on or before due date", fine_zero == 0.0 and days_zero == 0)

    # Test 10: Tiered Fine calculation (5 days overdue = 5 * 2 = INR 10)
    fine_tier1, days_tier1 = Transaction.calculate_fine("2026-10-01", "2026-10-06")
    assert_test("Tier 1 fine: 5 days overdue @ INR 2/day = INR 10", fine_tier1 == 10.0 and days_tier1 == 5)

    # Test 11: Tiered Fine calculation (10 days overdue: 7*2 + 3*5 = 14 + 15 = INR 29)
    fine_tier2, days_tier2 = Transaction.calculate_fine("2026-10-01", "2026-10-11")
    assert_test("Tier 2 fine: 10 days overdue = INR 29", fine_tier2 == 29.0 and days_tier2 == 10)

    # Test 12: Return book and restore inventory
    try:
        txn_ret, fine_amt = test_lib.return_book("STU99", "TEST101", "2026-10-05")
        assert_test("Return book restores stock and marks transaction RETURNED", 
                    txn_ret.status == "RETURNED" and test_lib.books["TEST101"].available_copies == 2)
    except Exception as e:
        assert_test(f"Return book failed: {e}", False)

    # Test 13: Invalid return (student never borrowed book)
    try:
        test_lib.return_book("STU98", "TEST101")
        assert_test("Reject return for book not issued to student", False)
    except InvalidTransactionError:
        assert_test("Reject return for book not issued with InvalidTransactionError", True)
    except Exception as e:
        assert_test(f"Wrong exception: {e}", False)

    # Test 14: Custom Bubble Sort algorithm verification
    b_unsorted = [Book("B2", "Zebra", "A", "G"), Book("B1", "Alpha", "B", "G"), Book("B3", "Beta", "C", "G")]
    b_sorted = Library.bubble_sort_books(b_unsorted, key="title", reverse=False)
    assert_test("Custom Bubble Sort sorts books alphabetically by title",
                [b.title for b in b_sorted] == ["Alpha", "Beta", "Zebra"])

    print("-" * 65)
    print(f"Summary: {passed}/{total} Test Cases Passed ({passed/total*100:.1f}%)")
    print("=" * 65)


def main():
    """Main program entry point with interactive command-line interface."""
    # Check for CLI flags
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            run_unit_tests()
            return
        elif sys.argv[1] == "--analytics":
            lib = Library()
            generate_visual_charts(lib.books, lib.students, lib.transactions)
            print("Visual analytics generated in reports/ directory.")
            return

    print_banner()
    library = Library()

    while True:
        print_menu()
        choice = input("Enter your choice (0-6): ").strip()

        if choice == "1":
            handle_book_management(library)
        elif choice == "2":
            handle_student_management(library)
        elif choice == "3":
            handle_circulation(library)
        elif choice == "4":
            handle_analytics(library)
        elif choice == "5":
            run_unit_tests()
        elif choice == "6":
            confirm = input("Are you sure you want to reset records to default seed data? (y/n): ").strip().lower()
            if confirm == 'y':
                generate_seed_data()
                library.load_data()
                print("[Success] Library data re-initialized with fresh sample dataset.")
        elif choice == "0":
            library.save_data()
            print("\nThank you for using Central University Library Management System!")
            print("All records have been saved securely. Goodbye!")
            break
        else:
            print("[Invalid Choice] Please enter a number between 0 and 6.")


if __name__ == "__main__":
    main()
