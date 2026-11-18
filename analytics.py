"""
Library Management System - Analytics Module (NumPy, Pandas, Matplotlib)
Course: Problem Solving Using Python (MCA17400)

This module satisfies the syllabus requirements for scientific and analytical libraries:
- NumPy: Numerical operations, statistical metrics (mean, median, standard deviation, sum)
- Pandas: DataFrames, aggregation, grouping, and structured tabular summaries
- Matplotlib: Visual charts and graphs (bar charts, pie chart, genre breakdown)
"""

import os
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib
# Use 'Agg' by default for background/file generation, switch to GUI when user requests display
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def ensure_reports_directory():
    """Ensure directory exists for generated analytical reports and charts."""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)


def get_system_summary_stats(books_dict, students_dict, transactions_list):
    """
    Computes core statistical metrics using Python collections and NumPy.
    
    Returns:
        dict: Summary metrics containing counts, totals, and NumPy calculations.
    """
    total_titles = len(books_dict)
    
    # Use NumPy arrays for numerical computations
    total_copies_arr = np.array([b.total_copies for b in books_dict.values()]) if books_dict else np.array([0])
    avail_copies_arr = np.array([b.available_copies for b in books_dict.values()]) if books_dict else np.array([0])
    issues_arr = np.array([b.issue_count for b in books_dict.values()]) if books_dict else np.array([0])
    
    total_books_stock = int(np.sum(total_copies_arr))
    total_available_stock = int(np.sum(avail_copies_arr))
    total_currently_issued = total_books_stock - total_available_stock
    
    total_students = len(students_dict)
    active_borrowers = sum(1 for s in students_dict.values() if len(s.borrowed_books) > 0)
    
    # Overdue and fines analysis using NumPy
    fine_list = [t.fine_amount for t in transactions_list if t.fine_amount > 0]
    fine_arr = np.array(fine_list) if fine_list else np.array([0.0])
    
    total_fine_collected = float(np.sum(fine_arr))
    avg_fine = float(np.mean(fine_arr)) if len(fine_list) > 0 else 0.0
    max_fine = float(np.max(fine_arr)) if len(fine_list) > 0 else 0.0

    return {
        "total_titles": total_titles,
        "total_books_stock": total_books_stock,
        "total_available_stock": total_available_stock,
        "total_currently_issued": total_currently_issued,
        "total_students": total_students,
        "active_borrowers": active_borrowers,
        "total_transactions": len(transactions_list),
        "total_fine_collected": total_fine_collected,
        "avg_fine": avg_fine,
        "max_fine": max_fine,
        "mean_issues_per_book": float(np.mean(issues_arr)) if len(issues_arr) > 0 else 0.0,
        "median_issues_per_book": float(np.median(issues_arr)) if len(issues_arr) > 0 else 0.0,
    }


def generate_pandas_reports(books_dict, students_dict, transactions_list):
    """
    Generates structured Pandas DataFrames for tabular analysis and reporting.
    
    Returns:
        dict: Contains DataFrames for books, students, and transaction summaries.
    """
    # 1. Books DataFrame
    books_data = [b.to_dict() for b in books_dict.values()]
    df_books = pd.DataFrame(books_data) if books_data else pd.DataFrame(
        columns=["book_id", "title", "author", "genre", "total_copies", "available_copies", "issue_count"]
    )
    
    # 2. Students DataFrame
    students_data = []
    for s in students_dict.values():
        rec = s.to_dict()
        rec["active_issues_count"] = len(s.borrowed_books)
        students_data.append(rec)
    df_students = pd.DataFrame(students_data) if students_data else pd.DataFrame(
        columns=["student_id", "name", "department", "contact", "active_issues_count"]
    )
    
    # 3. Transactions DataFrame
    txns_data = [t.to_dict() for t in transactions_list]
    df_txns = pd.DataFrame(txns_data) if txns_data else pd.DataFrame(
        columns=["txn_id", "book_id", "student_id", "issue_date", "due_date", "return_date", "fine_amount", "status"]
    )
    
    # Top 5 most issued books using Pandas sorting
    top_books = pd.DataFrame()
    if not df_books.empty:
        top_books = df_books.sort_values(by="issue_count", ascending=False)[["book_id", "title", "author", "genre", "issue_count"]].head(5)

    # Department-wise student distribution
    dept_distribution = pd.Series(dtype=int)
    if not df_students.empty and "department" in df_students.columns:
        dept_distribution = df_students["department"].value_counts()

    # Genre-wise book distribution
    genre_distribution = pd.Series(dtype=int)
    if not df_books.empty and "genre" in df_books.columns:
        genre_distribution = df_books["genre"].value_counts()

    return {
        "df_books": df_books,
        "df_students": df_students,
        "df_txns": df_txns,
        "top_books": top_books,
        "dept_distribution": dept_distribution,
        "genre_distribution": genre_distribution
    }


def generate_visual_charts(books_dict, students_dict, transactions_list, show_gui=False):
    """
    Generates a high-resolution 4-panel analytical chart using Matplotlib.
    Saves the output figure to 'reports/library_analytics.png'.
    
    Charts included:
    1. Top 5 Most Borrowed Books (Horizontal Bar Chart)
    2. Library Inventory Distribution (Pie Chart: Available vs Issued)
    3. Books Collection by Genre (Vertical Bar Chart)
    4. Member Distribution by Department (Bar Chart)
    """
    ensure_reports_directory()
    reports = generate_pandas_reports(books_dict, students_dict, transactions_list)
    summary = get_system_summary_stats(books_dict, students_dict, transactions_list)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Library Management System — Analytical Dashboard (MCA17400)", fontsize=16, fontweight='bold', y=0.98)
    plt.subplots_adjust(hspace=0.35, wspace=0.3)

    # Palette
    bar_colors = ["#2b5c8f", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"]

    # -------------------------------------------------------------
    # Panel 1: Top 5 Most Issued Books
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    top_books = reports["top_books"]
    if not top_books.empty:
        # Truncate titles if too long for clean display
        short_titles = [t[:24] + "..." if len(t) > 24 else t for t in top_books["title"]]
        y_pos = np.arange(len(short_titles))
        counts = top_books["issue_count"].values
        ax1.barh(y_pos, counts, color="#2563eb", edgecolor="#1e40af")
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(short_titles, fontsize=9)
        ax1.invert_yaxis()  # Highest at top
        ax1.set_xlabel("Total Times Issued", fontweight='semibold')
        ax1.set_title("Top 5 Most Popular Books", fontweight='bold', fontsize=12, pad=10)
        for i, v in enumerate(counts):
            ax1.text(v + 0.3, i, str(v), va='center', fontweight='bold', color="#1e3a8a")
    else:
        ax1.text(0.5, 0.5, "No Book Data Available", ha='center', va='center')
        ax1.set_title("Top 5 Most Popular Books")

    # -------------------------------------------------------------
    # Panel 2: Inventory Status (Available vs Issued)
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    avail = summary["total_available_stock"]
    issued = summary["total_currently_issued"]
    
    if (avail + issued) > 0:
        sizes = [avail, issued]
        labels = [f"Available ({avail})", f"Issued ({issued})"]
        colors = ["#10b981", "#ef4444"]
        explode = (0.05, 0.05)
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            startangle=140, colors=colors, explode=explode,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax2.set_title("Library Inventory Status (Copies)", fontweight='bold', fontsize=12, pad=10)
    else:
        ax2.text(0.5, 0.5, "No Inventory Data", ha='center', va='center')
        ax2.set_title("Library Inventory Status")

    # -------------------------------------------------------------
    # Panel 3: Books Collection by Genre
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    genres = reports["genre_distribution"]
    if not genres.empty:
        genres.plot(kind='bar', ax=ax3, color="#8b5cf6", edgecolor="#6d28d9")
        ax3.set_title("Books Count by Genre / Subject", fontweight='bold', fontsize=12, pad=10)
        ax3.set_ylabel("Number of Titles", fontweight='semibold')
        ax3.set_xticklabels(genres.index, rotation=35, ha='right', fontsize=9)
        for i, v in enumerate(genres.values):
            ax3.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, "No Genre Data", ha='center', va='center')
        ax3.set_title("Books Count by Genre")

    # -------------------------------------------------------------
    # Panel 4: Student Members by Department
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    depts = reports["dept_distribution"]
    if not depts.empty:
        depts.plot(kind='bar', ax=ax4, color="#f59e0b", edgecolor="#d97706")
        ax4.set_title("Student Membership by Department", fontweight='bold', fontsize=12, pad=10)
        ax4.set_ylabel("Registered Students", fontweight='semibold')
        ax4.set_xticklabels(depts.index, rotation=30, ha='right', fontsize=9)
        for i, v in enumerate(depts.values):
            ax4.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, "No Student Data", ha='center', va='center')
        ax4.set_title("Student Membership by Department")

    # Save output to reports
    chart_path = os.path.join(REPORTS_DIR, "library_analytics.png")
    fig.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[Analytics] Dashboard chart successfully generated and saved to: {chart_path}")

    # If requested and interactive GUI is possible
    if show_gui:
        try:
            # Reopen in interactive backend if possible
            import matplotlib
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as gui_plt
            # Just open the saved image with default OS viewer for reliability
            import webbrowser
            webbrowser.open(chart_path)
        except Exception as e:
            print(f"[Analytics] Could not launch popup window ({e}). Chart saved to disk.")

    return chart_path
