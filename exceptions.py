"""
Library Management System - Custom Exceptions Module
Course: Problem Solving Using Python (MCA17400)

This module defines custom exception classes used throughout the system
to provide descriptive, syllabus-oriented error handling for business logic
violations (e.g. duplicate IDs, limits exceeded, missing records).
"""

class LibraryError(Exception):
    """Base exception class for all library management system errors."""
    def __init__(self, message="A library system error occurred."):
        self.message = message
        super().__init__(self.message)


class BookNotFoundError(LibraryError):
    """Raised when a requested book ID or search query does not match any record."""
    def __init__(self, book_id):
        self.book_id = book_id
        super().__init__(f"Book with ID '{book_id}' was not found in the catalog.")


class StudentNotFoundError(LibraryError):
    """Raised when a requested student/member ID does not exist."""
    def __init__(self, student_id):
        self.student_id = student_id
        super().__init__(f"Student with ID '{student_id}' is not registered in the system.")


class BookNotAvailableError(LibraryError):
    """Raised when an attempt is made to issue a book with zero available copies."""
    def __init__(self, title):
        self.title = title
        super().__init__(f"No copies of '{title}' are currently available for issue.")


class BookAlreadyIssuedError(LibraryError):
    """Raised when a student attempts to borrow a book they already currently hold."""
    def __init__(self, student_name, book_title):
        self.student_name = student_name
        self.book_title = book_title
        super().__init__(f"Student '{student_name}' has already issued a copy of '{book_title}'.")


class StudentLimitExceededError(LibraryError):
    """Raised when a student exceeds the maximum allowed borrowed books quota."""
    def __init__(self, student_name, limit):
        self.student_name = student_name
        self.limit = limit
        super().__init__(f"Borrow limit exceeded! Student '{student_name}' has already reached the maximum limit of {limit} books.")


class DuplicateRecordError(LibraryError):
    """Raised when attempting to add a book or student with an ID that already exists."""
    def __init__(self, record_type, record_id):
        self.record_type = record_type
        self.record_id = record_id
        super().__init__(f"Duplicate {record_type} ID detected: '{record_id}' already exists in the records.")


class InvalidTransactionError(LibraryError):
    """Raised when a return operation is attempted for a book not issued to that student."""
    def __init__(self, message="Invalid transaction operation."):
        super().__init__(message)


class InvalidInputError(LibraryError):
    """Raised when input validation fails (e.g., negative numbers, empty fields)."""
    def __init__(self, field_name, reason):
        self.field_name = field_name
        self.reason = reason
        super().__init__(f"Invalid value for '{field_name}': {reason}")
