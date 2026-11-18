"""
Library Management System - Models Module
Course: Problem Solving Using Python (MCA17400)

This module implements Object-Oriented Programming (OOP) concepts:
- Classes, Constructors (__init__), Instance attributes & methods
- Encapsulation and Data Modeling for Books, Students, and Transactions
- Serialization methods (to_dict, from_dict) for File Handling
"""

from datetime import datetime, timedelta
from exceptions import (
    BookNotAvailableError,
    BookAlreadyIssuedError,
    StudentLimitExceededError,
    InvalidTransactionError,
    InvalidInputError,
)

# Constants for business rules
MAX_BORROW_LIMIT = 3          # Maximum books a student can hold simultaneously
STANDARD_LOAN_DAYS = 14       # Books must be returned within 14 days


class Book:
    """
    Represents a book in the library catalog.
    
    Attributes:
        book_id (str): Unique identifier for the book (e.g. 'B101')
        title (str): Title of the book
        author (str): Author's full name
        genre (str): Category/Department (e.g. 'Computer Science', 'Mathematics')
        total_copies (int): Total stock count owned by the library
        available_copies (int): Currently available copies on the shelf
        issue_count (int): Lifetime number of times this book has been issued
    """
    def __init__(self, book_id, title, author, genre, total_copies=1, available_copies=None, issue_count=0):
        if not book_id or not str(book_id).strip():
            raise InvalidInputError("Book ID", "Book ID cannot be blank.")
        if not title or not str(title).strip():
            raise InvalidInputError("Title", "Book title cannot be blank.")
        if not author or not str(author).strip():
            raise InvalidInputError("Author", "Author name cannot be blank.")
        if int(total_copies) < 1:
            raise InvalidInputError("Total Copies", "Must be at least 1.")

        self.book_id = str(book_id).strip().upper()
        self.title = str(title).strip()
        self.author = str(author).strip()
        self.genre = str(genre).strip() if genre else "General"
        self.total_copies = int(total_copies)
        self.available_copies = int(available_copies) if available_copies is not None else self.total_copies
        self.issue_count = int(issue_count)

    def is_available(self):
        """Returns True if at least one copy is available for lending."""
        return self.available_copies > 0

    def issue(self):
        """
        Decrements available copies and increments total issue count.
        Raises BookNotAvailableError if no copies remain.
        """
        if self.available_copies <= 0:
            raise BookNotAvailableError(self.title)
        self.available_copies -= 1
        self.issue_count += 1
        return True

    def return_copy(self):
        """
        Increments available copies back to shelf.
        Ensures available copies cannot exceed total copies.
        """
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def to_dict(self):
        """Convert object attributes to a dictionary for file storage."""
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "issue_count": self.issue_count
        }

    @classmethod
    def from_dict(cls, data):
        """Factory method to construct a Book object from a dictionary."""
        return cls(
            book_id=data["book_id"],
            title=data["title"],
            author=data["author"],
            genre=data.get("genre", "General"),
            total_copies=data.get("total_copies", 1),
            available_copies=data.get("available_copies", 1),
            issue_count=data.get("issue_count", 0)
        )

    def __str__(self):
        return f"[{self.book_id}] '{self.title}' by {self.author} | Genre: {self.genre} | Avail: {self.available_copies}/{self.total_copies} | Issued: {self.issue_count} times"


class Student:
    """
    Represents a student/library member.
    
    Attributes:
        student_id (str): Unique university roll number or member ID (e.g. 'MCA202601')
        name (str): Full student name
        department (str): Academic department (e.g. 'MCA', 'Computer Science')
        contact (str): Email or phone number
        borrowed_books (list): List of book IDs currently in student's possession
    """
    def __init__(self, student_id, name, department, contact, borrowed_books=None):
        if not student_id or not str(student_id).strip():
            raise InvalidInputError("Student ID", "Student ID cannot be empty.")
        if not name or not str(name).strip():
            raise InvalidInputError("Name", "Student name cannot be empty.")
            
        self.student_id = str(student_id).strip().upper()
        self.name = str(name).strip()
        self.department = str(department).strip() if department else "General"
        self.contact = str(contact).strip() if contact else "N/A"
        self.borrowed_books = list(borrowed_books) if borrowed_books else []

    def can_borrow(self, limit=MAX_BORROW_LIMIT):
        """Condition check: verifies student has not exceeded lending limit."""
        return len(self.borrowed_books) < limit

    def borrow_book(self, book_id):
        """
        Adds a book ID to student's currently borrowed list.
        Validates duplicate borrow and limit constraints.
        """
        book_id = str(book_id).strip().upper()
        if not self.can_borrow():
            raise StudentLimitExceededError(self.name, MAX_BORROW_LIMIT)
        if book_id in self.borrowed_books:
            raise BookAlreadyIssuedError(self.name, book_id)
        self.borrowed_books.append(book_id)

    def return_book(self, book_id):
        """
        Removes a returned book ID from student's active list.
        Raises InvalidTransactionError if student does not hold this book.
        """
        book_id = str(book_id).strip().upper()
        if book_id not in self.borrowed_books:
            raise InvalidTransactionError(f"Student '{self.name}' does not have book '{book_id}' issued.")
        self.borrowed_books.remove(book_id)

    def to_dict(self):
        """Serializes student record to a dictionary."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "department": self.department,
            "contact": self.contact,
            "borrowed_books": self.borrowed_books
        }

    @classmethod
    def from_dict(cls, data):
        """Constructs a Student instance from stored dictionary data."""
        return cls(
            student_id=data["student_id"],
            name=data["name"],
            department=data.get("department", "MCA"),
            contact=data.get("contact", "N/A"),
            borrowed_books=data.get("borrowed_books", [])
        )

    def __str__(self):
        books_str = ", ".join(self.borrowed_books) if self.borrowed_books else "None"
        return f"[{self.student_id}] {self.name} ({self.department}) | Contact: {self.contact} | Active Loans: [{books_str}]"


class Transaction:
    """
    Represents an issue and return transaction between a student and a book.
    
    Attributes:
        txn_id (str): Unique transaction identifier (e.g. 'TXN1001')
        book_id (str): ID of issued book
        student_id (str): ID of borrowing student
        issue_date (str): Date formatted as YYYY-MM-DD
        due_date (str): Expected return date (YYYY-MM-DD)
        return_date (str or None): Actual date returned (YYYY-MM-DD)
        fine_amount (float): Calculated overdue fine (in INR)
        status (str): "ISSUED" or "RETURNED"
    """
    def __init__(self, txn_id, book_id, student_id, issue_date=None, due_date=None,
                 return_date=None, fine_amount=0.0, status="ISSUED"):
        self.txn_id = str(txn_id).strip().upper()
        self.book_id = str(book_id).strip().upper()
        self.student_id = str(student_id).strip().upper()
        
        now = datetime.now()
        self.issue_date = issue_date or now.strftime("%Y-%m-%d")
        
        # Calculate standard 14 days loan period if not provided
        if not due_date:
            issue_dt = datetime.strptime(self.issue_date, "%Y-%m-%d")
            self.due_date = (issue_dt + timedelta(days=STANDARD_LOAN_DAYS)).strftime("%Y-%m-%d")
        else:
            self.due_date = due_date
            
        self.return_date = return_date
        self.fine_amount = float(fine_amount)
        self.status = status.upper()

    @staticmethod
    def calculate_fine(due_date_str, actual_return_date_str=None):
        """
        Calculates overdue fine based on condition logic (Syllabus Requirement):
        - Tier 1: 0 days overdue (on or before due date) -> ₹0 fine
        - Tier 2: 1 to 7 days overdue -> ₹2 per day
        - Tier 3: 8 to 14 days overdue -> ₹2/day for first 7 days + ₹5/day for days 8-14
        - Tier 4: Greater than 14 days overdue -> ₹2*7 + ₹5*7 + ₹10/day for remaining days + ₹50 penalty
        """
        due_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
        if actual_return_date_str:
            ret_dt = datetime.strptime(actual_return_date_str, "%Y-%m-%d")
        else:
            ret_dt = datetime.now()

        overdue_days = (ret_dt - due_dt).days

        # Condition-based fine ladder
        if overdue_days <= 0:
            fine = 0.0
            overdue_days = 0
        elif overdue_days <= 7:
            fine = overdue_days * 2.0
        elif overdue_days <= 14:
            fine = (7 * 2.0) + ((overdue_days - 7) * 5.0)
        else:
            # Over 14 days: First 7 days @ Rs 2, Next 7 days @ Rs 5, remaining @ Rs 10 + Rs 50 penalty
            fine = (7 * 2.0) + (7 * 5.0) + ((overdue_days - 14) * 10.0) + 50.0

        return fine, overdue_days

    def mark_returned(self, return_date_str=None):
        """Updates transaction status to RETURNED and computes fine."""
        now_str = return_date_str or datetime.now().strftime("%Y-%m-%d")
        self.return_date = now_str
        self.fine_amount, _ = self.calculate_fine(self.due_date, self.return_date)
        self.status = "RETURNED"
        return self.fine_amount

    def to_dict(self):
        """Converts transaction data to dictionary representation."""
        return {
            "txn_id": self.txn_id,
            "book_id": self.book_id,
            "student_id": self.student_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "return_date": self.return_date,
            "fine_amount": self.fine_amount,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        """Instantiates Transaction from dictionary."""
        return cls(
            txn_id=data["txn_id"],
            book_id=data["book_id"],
            student_id=data["student_id"],
            issue_date=data.get("issue_date"),
            due_date=data.get("due_date"),
            return_date=data.get("return_date"),
            fine_amount=data.get("fine_amount", 0.0),
            status=data.get("status", "ISSUED")
        )

    def __str__(self):
        status_info = f"Returned on {self.return_date} (Fine: Rs {self.fine_amount:.2f})" if self.status == "RETURNED" else f"Active (Due: {self.due_date})"
        return f"[{self.txn_id}] Book: {self.book_id} -> Student: {self.student_id} | Issued: {self.issue_date} | {status_info}"
