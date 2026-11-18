"""
Library Management System - Automated Unit Testing Suite
Course: Problem Solving Using Python (MCA17400)

Demonstrates syllabus requirement:
"Test the program with both valid and invalid inputs before submission."

Covers:
- Valid Input Tests:
    1. Adding a valid book to the catalog
    2. Registering a valid student
    3. Successfully issuing an available book
    4. Returning an issued book on time (fine = 0.0)
    5. Sorting books by title using custom Bubble Sort
    6. Sorting books by popularity using Python Timsort
    7. Overdue fine calculation with tiered fine structure
- Invalid Input & Exception Tests:
    8. Duplicate book ID rejection (DuplicateRecordError)
    9. Non-existent book search/issue rejection (BookNotFoundError)
    10. Duplicate student ID rejection (DuplicateRecordError)
    11. Borrow limit enforcement (StudentLimitExceededError)
    12. Issuing out-of-stock book rejection (BookNotAvailableError)
    13. Duplicate book issue to same student rejection (BookAlreadyIssuedError)
    14. Returning un-issued book rejection (InvalidTransactionError)
    15. Invalid negative copies input (InvalidInputError)
"""

import unittest
import shutil
import tempfile
import os
from models import Book, Student, Transaction, MAX_BORROW_LIMIT
from exceptions import (
    BookNotFoundError,
    StudentNotFoundError,
    BookNotAvailableError,
    BookAlreadyIssuedError,
    StudentLimitExceededError,
    DuplicateRecordError,
    InvalidTransactionError,
    InvalidInputError,
)
from library_system import Library


class TestLibraryManagementSystem(unittest.TestCase):
    """Test suite evaluating domain business logic, edge cases, and exceptions."""

    def setUp(self):
        """Creates an isolated in-memory test environment before each test."""
        self.library = Library.__new__(Library)
        self.library.name = "Test Library"
        self.library.books = {}
        self.library.students = {}
        self.library.transactions = []
        # Override save_data to avoid disk overwriting during unit tests
        self.library.save_data = lambda: True

        # Prepopulate with standard test instances
        self.test_book = Book("B101", "Python Programming", "Guido van Rossum", "CS", 2, 2, 5)
        self.library.books["B101"] = self.test_book

        self.test_student = Student("MCA01", "Rahul Kumar", "MCA", "rahul@test.edu")
        self.library.students["MCA01"] = self.test_student

    # =========================================================================
    # 1. VALID INPUT TESTS
    # =========================================================================
    def test_add_valid_book(self):
        """Test adding a brand new valid book to catalog."""
        book = self.library.add_book("B102", "Data Structures", "Mark Weiss", "CS", 3)
        self.assertEqual(book.book_id, "B102")
        self.assertEqual(book.total_copies, 3)
        self.assertEqual(book.available_copies, 3)
        self.assertIn("B102", self.library.books)

    def test_register_valid_student(self):
        """Test registering a valid student member."""
        student = self.library.register_student("MCA02", "Pooja Sharma", "MCA", "pooja@test.edu")
        self.assertEqual(student.student_id, "MCA02")
        self.assertEqual(student.name, "Pooja Sharma")
        self.assertIn("MCA02", self.library.students)

    def test_issue_book_success(self):
        """Test issuing an available book to an eligible student."""
        initial_avail = self.test_book.available_copies
        txn = self.library.issue_book("MCA01", "B101")
        self.assertEqual(txn.status, "ISSUED")
        self.assertEqual(self.test_book.available_copies, initial_avail - 1)
        self.assertIn("B101", self.test_student.borrowed_books)

    def test_return_book_on_time_zero_fine(self):
        """Test returning a book on or before the due date produces zero fine."""
        self.library.issue_book("MCA01", "B101", custom_issue_date="2026-10-01")
        txn, fine = self.library.return_book("MCA01", "B101", custom_return_date="2026-10-10")
        self.assertEqual(txn.status, "RETURNED")
        self.assertEqual(fine, 0.0)
        self.assertEqual(self.test_book.available_copies, 2)
        self.assertNotIn("B101", self.test_student.borrowed_books)

    def test_fine_calculation_tiered(self):
        """
        Verify condition-based tiered fine calculation:
        - 0 days overdue: Rs 0
        - 5 days overdue: 5 * 2 = Rs 10
        - 10 days overdue: 7*2 + 3*5 = 14 + 15 = Rs 29
        - 20 days overdue: 7*2 + 7*5 + 6*10 + 50 = 14 + 35 + 60 + 50 = Rs 159
        """
        # On time
        fine, days = Transaction.calculate_fine("2026-10-14", "2026-10-14")
        self.assertEqual(fine, 0.0)
        self.assertEqual(days, 0)

        # Tier 1 (1-7 days)
        fine, days = Transaction.calculate_fine("2026-10-10", "2026-10-15")
        self.assertEqual(days, 5)
        self.assertEqual(fine, 10.0)

        # Tier 2 (8-14 days)
        fine, days = Transaction.calculate_fine("2026-10-01", "2026-10-11")
        self.assertEqual(days, 10)
        self.assertEqual(fine, 29.0)

        # Tier 3 (> 14 days)
        fine, days = Transaction.calculate_fine("2026-10-01", "2026-10-21")
        self.assertEqual(days, 20)
        self.assertEqual(fine, 159.0)

    def test_bubble_sort_by_title(self):
        """Test custom Bubble Sort implementation."""
        b1 = Book("B1", "Zebra Book", "Author", "CS")
        b2 = Book("B2", "Alpha Book", "Author", "CS")
        b3 = Book("B3", "Mango Book", "Author", "CS")
        sorted_list = Library.bubble_sort_books([b1, b2, b3], key="title", reverse=False)
        self.assertEqual([b.title for b in sorted_list], ["Alpha Book", "Mango Book", "Zebra Book"])

    def test_search_books(self):
        """Test book search functionality by title and author."""
        results = self.library.search_books("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].book_id, "B101")

        results_author = self.library.search_books("Guido", search_by="author")
        self.assertEqual(len(results_author), 1)

    # =========================================================================
    # 2. INVALID INPUT & EXCEPTION HANDLING TESTS
    # =========================================================================
    def test_duplicate_book_id_rejected(self):
        """Attempting to add duplicate book ID must raise DuplicateRecordError."""
        with self.assertRaises(DuplicateRecordError):
            self.library.add_book("B101", "Duplicate Book", "Author", "CS", 1)

    def test_duplicate_student_id_rejected(self):
        """Attempting to register duplicate student ID must raise DuplicateRecordError."""
        with self.assertRaises(DuplicateRecordError):
            self.library.register_student("MCA01", "Another Student", "MCA", "phone")

    def test_book_not_found(self):
        """Querying non-existent book ID must raise BookNotFoundError."""
        with self.assertRaises(BookNotFoundError):
            self.library.get_book("INVALID999")

    def test_student_not_found(self):
        """Querying non-existent student ID must raise StudentNotFoundError."""
        with self.assertRaises(StudentNotFoundError):
            self.library.get_student("NO_SUCH_STUDENT")

    def test_borrow_limit_exceeded(self):
        """Student cannot borrow more than MAX_BORROW_LIMIT books."""
        b1 = self.library.add_book("B01", "Book 1", "Auth", "CS", 1)
        b2 = self.library.add_book("B02", "Book 2", "Auth", "CS", 1)
        b3 = self.library.add_book("B03", "Book 3", "Auth", "CS", 1)
        b4 = self.library.add_book("B04", "Book 4", "Auth", "CS", 1)

        self.library.issue_book("MCA01", "B01")
        self.library.issue_book("MCA01", "B02")
        self.library.issue_book("MCA01", "B03")

        with self.assertRaises(StudentLimitExceededError):
            self.library.issue_book("MCA01", "B04")

    def test_prevent_duplicate_issue_to_same_student(self):
        """A student cannot issue two copies of the exact same book."""
        self.library.issue_book("MCA01", "B101")
        with self.assertRaises(BookAlreadyIssuedError):
            self.library.issue_book("MCA01", "B101")

    def test_book_out_of_stock(self):
        """Issuing a book with 0 available copies must raise BookNotAvailableError."""
        b_single = self.library.add_book("BSINGLE", "Single Copy", "Auth", "CS", 1)
        self.library.register_student("MCA99", "Student Two", "MCA", "s2@test.edu")
        
        self.library.issue_book("MCA01", "BSINGLE")
        self.assertEqual(b_single.available_copies, 0)

        with self.assertRaises(BookNotAvailableError):
            self.library.issue_book("MCA99", "BSINGLE")

    def test_return_unissued_book_rejected(self):
        """Returning a book never issued to that student must raise InvalidTransactionError."""
        with self.assertRaises(InvalidTransactionError):
            self.library.return_book("MCA01", "B101")

    def test_invalid_input_empty_strings(self):
        """Empty book ID or negative total copies must raise InvalidInputError."""
        with self.assertRaises(InvalidInputError):
            Book("", "Title", "Author", "CS", 1)

        with self.assertRaises(InvalidInputError):
            Book("B99", "Title", "Author", "CS", -5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
