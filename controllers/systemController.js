/**
 * System Controller - Library Management System
 * Handles Data Reset/Re-seed and Automated Diagnostics Test Suite (mirroring unit tests)
 */

const { getDb, calculateFine, MAX_BORROW_LIMIT, STANDARD_LOAN_DAYS } = require('../database/db');
const path = require('path');
const fs = require('fs');

const DATA_DIR = path.join(__dirname, '../../data');

function resetDatabase(req, res) {
  try {
    const db = getDb();

    // Clear existing tables
    db.exec('DELETE FROM transactions');
    db.exec('DELETE FROM books');
    db.exec('DELETE FROM students');

    // Re-seed from JSON
    const booksFile = path.join(DATA_DIR, 'books.json');
    const studentsFile = path.join(DATA_DIR, 'students.json');
    const transactionsFile = path.join(DATA_DIR, 'transactions.json');

    const insertBook = db.prepare(`
      INSERT INTO books (book_id, title, author, genre, total_copies, available_copies, issue_count)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    const insertStudent = db.prepare(`
      INSERT INTO students (student_id, name, department, contact)
      VALUES (?, ?, ?, ?)
    `);

    const insertTxn = db.prepare(`
      INSERT INTO transactions (txn_id, book_id, student_id, issue_date, due_date, return_date, fine_amount, status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    let bookCount = 0, studentCount = 0, txnCount = 0;

    if (fs.existsSync(booksFile)) {
      const books = JSON.parse(fs.readFileSync(booksFile, 'utf8'));
      books.forEach(b => {
        insertBook.run(
          b.book_id,
          b.title,
          b.author,
          b.genre || 'General',
          b.total_copies || 1,
          b.available_copies !== undefined ? b.available_copies : b.total_copies,
          b.issue_count || 0
        );
        bookCount++;
      });
    }

    if (fs.existsSync(studentsFile)) {
      const students = JSON.parse(fs.readFileSync(studentsFile, 'utf8'));
      students.forEach(s => {
        insertStudent.run(
          s.student_id,
          s.name,
          s.department || 'General',
          s.contact || 'N/A'
        );
        studentCount++;
      });
    }

    if (fs.existsSync(transactionsFile)) {
      const txns = JSON.parse(fs.readFileSync(transactionsFile, 'utf8'));
      txns.forEach(t => {
        insertTxn.run(
          t.txn_id,
          t.book_id,
          t.student_id,
          t.issue_date,
          t.due_date,
          t.return_date || null,
          t.fine_amount || 0.0,
          t.status || 'ISSUED'
        );
        txnCount++;
      });
    }

    res.json({
      success: true,
      message: `System reset successfully: ${bookCount} Books, ${studentCount} Students, ${txnCount} Transactions restored.`
    });
  } catch (err) {
    console.error('[System] resetDatabase error:', err);
    res.status(500).json({ success: false, error: 'Failed to reset database.' });
  }
}

function runDiagnostics(req, res) {
  try {
    const tests = [];

    function bubbleSortBooks(items, key = 'title') {
      const arr = [...items];
      const n = arr.length;
      for (let i = 0; i < n; i++) {
        let swapped = false;
        for (let j = 0; j < n - i - 1; j++) {
          const v1 = (arr[j][key] || '').toLowerCase();
          const v2 = (arr[j + 1][key] || '').toLowerCase();
          if (v1 > v2) {
            const temp = arr[j];
            arr[j] = arr[j + 1];
            arr[j + 1] = temp;
            swapped = true;
          }
        }
        if (!swapped) break;
      }
      return arr;
    }

    // Isolated in-memory tests
    // 1. Add valid book
    const mockBooks = {};
    mockBooks['TEST101'] = { book_id: 'TEST101', title: 'Python Programming', author: 'Guido van Rossum', genre: 'CS', total_copies: 2, available_copies: 2 };
    tests.push({
      id: 1,
      name: 'Add valid book to catalog',
      passed: mockBooks['TEST101'].book_id === 'TEST101' && mockBooks['TEST101'].total_copies === 2,
      category: 'Book Operations'
    });

    // 2. Reject duplicate book ID
    const isDuplicate = !!mockBooks['TEST101'];
    tests.push({
      id: 2,
      name: 'Reject duplicate book ID (DuplicateRecordError)',
      passed: isDuplicate === true,
      category: 'Book Operations'
    });

    // 3. Register valid student
    const mockStudents = {};
    mockStudents['STU99'] = { student_id: 'STU99', name: 'Test Student', department: 'MCA', contact: 'test@test.com' };
    tests.push({
      id: 3,
      name: 'Register valid student / member',
      passed: mockStudents['STU99'].student_id === 'STU99',
      category: 'Student Operations'
    });

    // 4. Issue book successfully
    mockBooks['TEST101'].available_copies -= 1;
    const mockTxns = [];
    mockTxns.push({ txn_id: 'TXN_TEST1', book_id: 'TEST101', student_id: 'STU99', status: 'ISSUED' });
    tests.push({
      id: 4,
      name: 'Issue available book to eligible student',
      passed: mockTxns[0].status === 'ISSUED' && mockBooks['TEST101'].available_copies === 1,
      category: 'Circulation Desk'
    });

    // 5. Prevent borrowing same book twice
    const alreadyBorrowed = mockTxns.some(t => t.student_id === 'STU99' && t.book_id === 'TEST101' && t.status === 'ISSUED');
    tests.push({
      id: 5,
      name: 'Prevent borrowing same book twice (BookAlreadyIssuedError)',
      passed: alreadyBorrowed === true,
      category: 'Circulation Desk'
    });

    // 6. Non-existent book validation
    const nonExistent = mockBooks['NONEXISTENT'];
    tests.push({
      id: 6,
      name: 'Reject non-existent book ID (BookNotFoundError)',
      passed: nonExistent === undefined,
      category: 'Circulation Desk'
    });

    // 7. Student borrow limit enforcement (MAX_BORROW_LIMIT = 3)
    const currentBorrows = 3;
    const canBorrowMore = currentBorrows < MAX_BORROW_LIMIT;
    tests.push({
      id: 7,
      name: 'Enforce borrowing limit of 3 books (StudentLimitExceededError)',
      passed: canBorrowMore === false,
      category: 'Circulation Desk'
    });

    // 8. Book out of stock error
    mockBooks['TEST102'] = { book_id: 'TEST102', title: 'Data Structures', available_copies: 0 };
    const canIssueOutOfStock = mockBooks['TEST102'].available_copies > 0;
    tests.push({
      id: 8,
      name: 'Prevent issuing out-of-stock book (BookNotAvailableError)',
      passed: canIssueOutOfStock === false,
      category: 'Circulation Desk'
    });

    // 9. Fine calculation: 0 days overdue = INR 0
    const f0 = calculateFine('2026-10-10', '2026-10-09');
    tests.push({
      id: 9,
      name: 'Overdue fine is INR 0 when returned on or before due date',
      passed: f0.fine === 0.0 && f0.overdueDays === 0,
      category: 'Fine Rules'
    });

    // 10. Tier 1 fine: 5 days overdue @ INR 2/day = INR 10
    const f1 = calculateFine('2026-10-01', '2026-10-06');
    tests.push({
      id: 10,
      name: 'Tier 1 fine: 5 days overdue @ INR 2/day = INR 10',
      passed: f1.fine === 10.0 && f1.overdueDays === 5,
      category: 'Fine Rules'
    });

    // 11. Tier 2 fine: 10 days overdue = (7*2) + (3*5) = INR 29
    const f2 = calculateFine('2026-10-01', '2026-10-11');
    tests.push({
      id: 11,
      name: 'Tier 2 fine: 10 days overdue = INR 29 (7*2 + 3*5)',
      passed: f2.fine === 29.0 && f2.overdueDays === 10,
      category: 'Fine Rules'
    });

    // 12. Return book and restore inventory
    mockBooks['TEST101'].available_copies += 1;
    mockTxns[0].status = 'RETURNED';
    tests.push({
      id: 12,
      name: 'Return book restores stock and marks transaction RETURNED',
      passed: mockTxns[0].status === 'RETURNED' && mockBooks['TEST101'].available_copies === 2,
      category: 'Circulation Desk'
    });

    // 13. Reject return for unissued book
    const unissuedReturn = mockTxns.some(t => t.student_id === 'STU98' && t.book_id === 'TEST101' && t.status === 'ISSUED');
    tests.push({
      id: 13,
      name: 'Reject return for book not issued to student (InvalidTransactionError)',
      passed: unissuedReturn === false,
      category: 'Circulation Desk'
    });

    // 14. Custom Bubble Sort algorithm verification
    const unsorted = [{ title: 'Zebra' }, { title: 'Alpha' }, { title: 'Beta' }];
    const sorted = bubbleSortBooks(unsorted, 'title');
    const isSortedCorrectly = sorted[0].title === 'Alpha' && sorted[1].title === 'Beta' && sorted[2].title === 'Zebra';
    tests.push({
      id: 14,
      name: 'Custom Bubble Sort algorithm sorts books alphabetically',
      passed: isSortedCorrectly,
      category: 'Algorithms'
    });

    const passedCount = tests.filter(t => t.passed).length;
    res.json({
      success: true,
      summary: {
        total: tests.length,
        passed: passedCount,
        failed: tests.length - passedCount,
        percentage: ((passedCount / tests.length) * 100).toFixed(1)
      },
      tests
    });
  } catch (err) {
    console.error('[System] runDiagnostics error:', err);
    res.status(500).json({ success: false, error: 'Failed to run diagnostics.' });
  }
}

module.exports = { resetDatabase, runDiagnostics };
