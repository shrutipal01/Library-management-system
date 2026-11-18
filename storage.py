"""
Library Management System - File Storage Module
Course: Problem Solving Using Python (MCA17400)

This module handles File Handling concepts:
- File opening, reading, writing using Python context managers ('with' statement)
- JSON serialization/deserialization
- Exception handling for FileNotFoundError and corrupted data
- Default initial dataset generation (Seed Data)
"""

import json
import os
from datetime import datetime, timedelta
from models import Book, Student, Transaction

# Directory and file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")


def ensure_data_directory():
    """Creates the data storage directory if it does not already exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def save_to_file(filepath, data_list):
    """
    Saves a list of serializable dictionaries to a JSON file.
    Demonstrates file handling and exception handling.
    """
    ensure_data_directory()
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data_list, file, indent=4)
        return True
    except IOError as e:
        print(f"[Error] Failed to write to {filepath}: {e}")
        return False


def load_from_file(filepath):
    """
    Reads records from a JSON file.
    Returns an empty list if file doesn't exist or is corrupted.
    """
    ensure_data_directory()
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[Warning] Could not parse {filepath} ({e}). Starting with empty list.")
        return []


def generate_seed_data():
    """
    Generates realistic sample data for books, students, and transactions
    relevant to an MCA (Master of Computer Applications) library.
    """
    sample_books = [
        Book("B101", "Python Crash Course", "Eric Matthes", "Programming", 5, 3, 14),
        Book("B102", "Introduction to Algorithms (CLRS)", "Thomas Cormen", "Data Structures", 4, 2, 22),
        Book("B103", "Database System Concepts", "Silberschatz & Korth", "Databases", 6, 4, 18),
        Book("B104", "Computer Networks", "Andrew S. Tanenbaum", "Networking", 3, 1, 9),
        Book("B105", "Operating System Concepts", "Abraham Silberschatz", "Systems", 5, 3, 15),
        Book("B106", "Clean Code: A Handbook of Agile Craftsmanship", "Robert C. Martin", "Software Engg", 4, 3, 12),
        Book("B107", "Artificial Intelligence: A Modern Approach", "Stuart Russell", "AI & ML", 3, 1, 19),
        Book("B108", "Discrete Mathematics and Its Applications", "Kenneth Rosen", "Mathematics", 5, 4, 8),
        Book("B109", "Design Patterns: Elements of Reusable Object-Oriented Software", "Gang of Four", "Software Engg", 4, 2, 11),
        Book("B110", "Hands-On Machine Learning with Scikit-Learn", "Aurelien Geron", "AI & ML", 4, 2, 16),
        Book("B111", "Web Development with Django", "William S. Vincent", "Web Development", 3, 3, 6),
        Book("B112", "Data Science from Scratch: First Principles with Python", "Joel Grus", "Data Science", 4, 3, 10),
    ]

    sample_students = [
        Student("MCA202601", "Aarav Sharma", "MCA", "aarav.sharma@univ.edu", ["B101", "B104"]),
        Student("MCA202602", "Priya Patel", "MCA", "priya.patel@univ.edu", ["B102"]),
        Student("MCA202603", "Rohan Verma", "Computer Science", "rohan.v@univ.edu", ["B107"]),
        Student("MCA202604", "Sneha Iyer", "Data Science", "sneha.i@univ.edu", ["B110"]),
        Student("MCA202605", "Vikram Singh", "MCA", "vikram.s@univ.edu", ["B102", "B103"]),
        Student("MCA202606", "Ananya Gupta", "Information Tech", "ananya.g@univ.edu", []),
        Student("MCA202607", "Karan Mehta", "MCA", "karan.m@univ.edu", ["B109"]),
    ]

    today = datetime.now()
    sample_transactions = [
        # Returned transactions with various loan periods & fines
        Transaction("TXN1001", "B101", "MCA202601",
                    (today - timedelta(days=40)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=26)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=27)).strftime("%Y-%m-%d"),
                    fine_amount=0.0, status="RETURNED"),
        Transaction("TXN1002", "B102", "MCA202602",
                    (today - timedelta(days=35)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=21)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=16)).strftime("%Y-%m-%d"),
                    fine_amount=10.0, status="RETURNED"),
        Transaction("TXN1003", "B103", "MCA202603",
                    (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=16)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                    fine_amount=34.0, status="RETURNED"),
        Transaction("TXN1004", "B105", "MCA202604",
                    (today - timedelta(days=28)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=14)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=14)).strftime("%Y-%m-%d"),
                    fine_amount=0.0, status="RETURNED"),
        Transaction("TXN1005", "B107", "MCA202605",
                    (today - timedelta(days=50)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=36)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    fine_amount=169.0, status="RETURNED"),

        # Active issues
        Transaction("TXN1006", "B101", "MCA202601",
                    (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=8)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
        Transaction("TXN1007", "B104", "MCA202601",
                    (today - timedelta(days=20)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                    status="ISSUED"),  # Overdue by 6 days!
        Transaction("TXN1008", "B102", "MCA202602",
                    (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=9)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
        Transaction("TXN1009", "B107", "MCA202603",
                    (today - timedelta(days=25)).strftime("%Y-%m-%d"),
                    (today - timedelta(days=11)).strftime("%Y-%m-%d"),
                    status="ISSUED"),  # Overdue by 11 days!
        Transaction("TXN1010", "B110", "MCA202604",
                    (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=11)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
        Transaction("TXN1011", "B102", "MCA202605",
                    (today - timedelta(days=8)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=6)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
        Transaction("TXN1012", "B103", "MCA202605",
                    (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=13)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
        Transaction("TXN1013", "B109", "MCA202607",
                    (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    (today + timedelta(days=12)).strftime("%Y-%m-%d"),
                    status="ISSUED"),
    ]

    save_to_file(BOOKS_FILE, [b.to_dict() for b in sample_books])
    save_to_file(STUDENTS_FILE, [s.to_dict() for s in sample_students])
    save_to_file(TRANSACTIONS_FILE, [t.to_dict() for t in sample_transactions])
    print("[Storage] Default seed dataset initialized successfully.")
