/**
 * Transactions Controller - Library Management System
 * EXACT port of Python Library.issue_book() and Library.return_book() logic.
 * Uses node:sqlite (Node 24 built-in)
 * 
 * Business rules preserved:
 * - MAX_BORROW_LIMIT = 3
 * - STANDARD_LOAN_DAYS = 14
 * - Tiered fine: ₹2/day (1-7d) → ₹5/day (8-14d) → ₹10/day + ₹50 penalty (>14d)
 */

const { getDb, calculateFine, generateTxnId, getTodayStr, addDays, MAX_BORROW_LIMIT, STANDARD_LOAN_DAYS } = require('../database/db');

// POST /api/transactions/issue
function issueBook(req, res) {
  try {
    const db = getDb();
    let { student_id, book_id, issue_date } = req.body;

    if (!student_id || !student_id.trim()) return res.status(400).json({ success: false, error: 'Student ID is required.' });
    if (!book_id || !book_id.trim()) return res.status(400).json({ success: false, error: 'Book ID is required.' });

    student_id = student_id.trim().toUpperCase();
    book_id = book_id.trim().toUpperCase();

    // 1. Student exists?
    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!student) return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered in the system.` });

    // 2. Book exists?
    const book = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    if (!book) return res.status(404).json({ success: false, error: `Book with ID '${book_id}' was not found in the catalog.` });

    // 3. Borrow limit check
    const activeLoans = db.prepare(`SELECT COUNT(*) as count FROM transactions WHERE student_id = ? AND status = 'ISSUED'`).get(student_id);
    if (activeLoans.count >= MAX_BORROW_LIMIT) {
      return res.status(409).json({ success: false, error: `Borrow limit exceeded! Student '${student.name}' has already reached the maximum limit of ${MAX_BORROW_LIMIT} books.` });
    }

    // 4. Already borrowed this book?
    const alreadyBorrowed = db.prepare(`SELECT txn_id FROM transactions WHERE student_id = ? AND book_id = ? AND status = 'ISSUED'`).get(student_id, book_id);
    if (alreadyBorrowed) {
      return res.status(409).json({ success: false, error: `Student '${student.name}' has already issued a copy of '${book.title}'.` });
    }

    // 5. Book available?
    if (book.available_copies <= 0) {
      return res.status(409).json({ success: false, error: `No copies of '${book.title}' are currently available for issue.` });
    }

    // Execute issue
    const issueDateFinal = issue_date || getTodayStr();
    const dueDate = addDays(issueDateFinal, STANDARD_LOAN_DAYS);
    const txnId = generateTxnId(db);

    db.prepare(`INSERT INTO transactions (txn_id, book_id, student_id, issue_date, due_date, return_date, fine_amount, status) VALUES (?, ?, ?, ?, ?, NULL, 0.0, 'ISSUED')`).run(txnId, book_id, student_id, issueDateFinal, dueDate);
    db.prepare(`UPDATE books SET available_copies = available_copies - 1, issue_count = issue_count + 1 WHERE book_id = ?`).run(book_id);

    const updatedBook = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);

    res.status(201).json({
      success: true,
      message: `Book '${book.title}' issued successfully to ${student.name}.`,
      data: {
        txn_id: txnId,
        book_id,
        book_title: book.title,
        student_id,
        student_name: student.name,
        issue_date: issueDateFinal,
        due_date: dueDate,
        loan_period_days: STANDARD_LOAN_DAYS,
        remaining_copies: updatedBook.available_copies,
        total_copies: updatedBook.total_copies
      }
    });
  } catch (err) {
    console.error('[Transactions] issueBook error:', err);
    res.status(500).json({ success: false, error: 'Failed to issue book.' });
  }
}

// POST /api/transactions/return
function returnBook(req, res) {
  try {
    const db = getDb();
    let { student_id, book_id, return_date } = req.body;

    if (!student_id || !student_id.trim()) return res.status(400).json({ success: false, error: 'Student ID is required.' });
    if (!book_id || !book_id.trim()) return res.status(400).json({ success: false, error: 'Book ID is required.' });

    student_id = student_id.trim().toUpperCase();
    book_id = book_id.trim().toUpperCase();

    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!student) return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered in the system.` });

    const book = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    if (!book) return res.status(404).json({ success: false, error: `Book with ID '${book_id}' was not found in the catalog.` });

    // Find active transaction
    const activeTxn = db.prepare(`SELECT * FROM transactions WHERE student_id = ? AND book_id = ? AND status = 'ISSUED' ORDER BY issue_date DESC LIMIT 1`).get(student_id, book_id);
    if (!activeTxn) {
      return res.status(404).json({ success: false, error: `No active issue record found for Book '${book.title}' with Student '${student.name}'.` });
    }

    // Calculate fine
    const returnDateFinal = return_date || getTodayStr();
    const { fine, overdueDays } = calculateFine(activeTxn.due_date, returnDateFinal);

    // Update transaction and book
    db.prepare(`UPDATE transactions SET status='RETURNED', return_date=?, fine_amount=? WHERE txn_id=?`).run(returnDateFinal, fine, activeTxn.txn_id);
    db.prepare(`UPDATE books SET available_copies = MIN(available_copies + 1, total_copies) WHERE book_id = ?`).run(book_id);

    const updatedBook = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);

    res.json({
      success: true,
      message: `Book '${book.title}' returned successfully.`,
      data: {
        txn_id: activeTxn.txn_id,
        book_id,
        book_title: book.title,
        student_id,
        student_name: student.name,
        issue_date: activeTxn.issue_date,
        due_date: activeTxn.due_date,
        return_date: returnDateFinal,
        overdue_days: overdueDays,
        fine_amount: fine,
        updated_available_copies: updatedBook.available_copies
      }
    });
  } catch (err) {
    console.error('[Transactions] returnBook error:', err);
    res.status(500).json({ success: false, error: 'Failed to return book.' });
  }
}

// GET /api/transactions
function getAllTransactions(req, res) {
  try {
    const db = getDb();
    const { status, student_id, book_id, search } = req.query;

    let conditions = ['1=1'];
    const params = [];

    if (status && ['ISSUED', 'RETURNED'].includes(status.toUpperCase())) {
      conditions.push('t.status = ?');
      params.push(status.toUpperCase());
    }
    if (student_id) { conditions.push('t.student_id = ?'); params.push(student_id.trim().toUpperCase()); }
    if (book_id) { conditions.push('t.book_id = ?'); params.push(book_id.trim().toUpperCase()); }
    if (search && search.trim()) {
      const q = `%${search.trim().toLowerCase()}%`;
      conditions.push('(LOWER(b.title) LIKE ? OR LOWER(s.name) LIKE ? OR LOWER(t.txn_id) LIKE ? OR LOWER(t.book_id) LIKE ? OR LOWER(t.student_id) LIKE ?)');
      params.push(q, q, q, q, q);
    }

    const query = `
      SELECT t.*, b.title as book_title, b.author as book_author, s.name as student_name, s.department as student_department
      FROM transactions t
      JOIN books b ON t.book_id = b.book_id
      JOIN students s ON t.student_id = s.student_id
      WHERE ${conditions.join(' AND ')}
      ORDER BY t.issue_date DESC
    `;

    const transactions = db.prepare(query).all(...params);
    res.json({ success: true, data: transactions, count: transactions.length });
  } catch (err) {
    console.error('[Transactions] getAllTransactions error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch transactions.' });
  }
}

// GET /api/transactions/active
function getActiveTransactions(req, res) {
  try {
    const db = getDb();
    const today = getTodayStr();

    const active = db.prepare(`
      SELECT t.*, b.title as book_title, b.author as book_author, s.name as student_name, s.department as student_department,
             CASE WHEN t.due_date < ? THEN 1 ELSE 0 END as is_overdue
      FROM transactions t
      JOIN books b ON t.book_id = b.book_id
      JOIN students s ON t.student_id = s.student_id
      WHERE t.status = 'ISSUED'
      ORDER BY t.due_date ASC
    `).all(today);

    res.json({ success: true, data: active, count: active.length });
  } catch (err) {
    console.error('[Transactions] getActiveTransactions error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch active transactions.' });
  }
}

// GET /api/transactions/:id
function getTransactionById(req, res) {
  try {
    const db = getDb();
    const txn_id = req.params.id.trim().toUpperCase();
    const txn = db.prepare(`
      SELECT t.*, b.title as book_title, b.author as book_author, s.name as student_name, s.department as student_department
      FROM transactions t
      JOIN books b ON t.book_id = b.book_id
      JOIN students s ON t.student_id = s.student_id
      WHERE t.txn_id = ?
    `).get(txn_id);

    if (!txn) return res.status(404).json({ success: false, error: `Transaction '${txn_id}' not found.` });
    res.json({ success: true, data: txn });
  } catch (err) {
    console.error('[Transactions] getTransactionById error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch transaction.' });
  }
}

module.exports = { issueBook, returnBook, getAllTransactions, getActiveTransactions, getTransactionById };
