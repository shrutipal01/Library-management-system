/**
 * Dashboard Controller - uses node:sqlite built-in
 */

const { getDb, getTodayStr } = require('../database/db');

function getDashboardStats(req, res) {
  try {
    const db = getDb();
    const today = getTodayStr();

    const bookStats = db.prepare(`SELECT COUNT(*) as total_titles, SUM(total_copies) as total_books_stock, SUM(available_copies) as total_available_stock, SUM(total_copies - available_copies) as total_currently_issued, SUM(issue_count) as total_lifetime_issues FROM books`).get();
    const studentStats = db.prepare(`SELECT COUNT(*) as total_students FROM students`).get();
    const activeBorrowers = db.prepare(`SELECT COUNT(DISTINCT student_id) as count FROM transactions WHERE status='ISSUED'`).get();
    const txnStats = db.prepare(`SELECT COUNT(*) as total_transactions, SUM(CASE WHEN status='ISSUED' THEN 1 ELSE 0 END) as active_transactions, SUM(CASE WHEN status='RETURNED' THEN 1 ELSE 0 END) as returned_transactions, SUM(CASE WHEN status='RETURNED' THEN fine_amount ELSE 0 END) as total_fines_collected FROM transactions`).get();
    const overdueCount = db.prepare(`SELECT COUNT(*) as count FROM transactions WHERE status='ISSUED' AND due_date < ?`).get(today);
    const topBooks = db.prepare(`SELECT book_id, title, author, genre, issue_count FROM books ORDER BY issue_count DESC LIMIT 5`).all();
    const genreDistribution = db.prepare(`SELECT genre, COUNT(*) as count FROM books GROUP BY genre ORDER BY count DESC`).all();
    const deptDistribution = db.prepare(`SELECT department, COUNT(*) as count FROM students GROUP BY department ORDER BY count DESC`).all();
    const recentTransactions = db.prepare(`SELECT t.*, b.title as book_title, s.name as student_name FROM transactions t JOIN books b ON t.book_id=b.book_id JOIN students s ON t.student_id=s.student_id ORDER BY t.issue_date DESC LIMIT 5`).all();

    const fineRows = db.prepare(`SELECT fine_amount FROM transactions WHERE fine_amount > 0 AND status='RETURNED'`).all();
    const fines = fineRows.map(r => r.fine_amount);
    const avgFine = fines.length > 0 ? fines.reduce((a, b) => a + b, 0) / fines.length : 0;
    const maxFine = fines.length > 0 ? Math.max(...fines) : 0;

    const issueCounts = db.prepare('SELECT issue_count FROM books').all().map(r => r.issue_count);
    const meanIssues = issueCounts.length > 0 ? issueCounts.reduce((a, b) => a + b, 0) / issueCounts.length : 0;
    const sortedIssues = [...issueCounts].sort((a, b) => a - b);
    const mid = Math.floor(sortedIssues.length / 2);
    const medianIssues = sortedIssues.length === 0 ? 0 : sortedIssues.length % 2 === 0 ? (sortedIssues[mid - 1] + sortedIssues[mid]) / 2 : sortedIssues[mid];

    res.json({
      success: true,
      data: {
        total_titles: bookStats.total_titles || 0,
        total_books_stock: bookStats.total_books_stock || 0,
        total_available_stock: bookStats.total_available_stock || 0,
        total_currently_issued: bookStats.total_currently_issued || 0,
        total_students: studentStats.total_students || 0,
        active_borrowers: activeBorrowers.count || 0,
        total_transactions: txnStats.total_transactions || 0,
        active_transactions: txnStats.active_transactions || 0,
        returned_transactions: txnStats.returned_transactions || 0,
        overdue_count: overdueCount.count || 0,
        total_lifetime_issues: bookStats.total_lifetime_issues || 0,
        total_fines_collected: txnStats.total_fines_collected || 0,
        avg_fine: avgFine,
        max_fine: maxFine,
        mean_issues_per_book: meanIssues,
        median_issues_per_book: medianIssues,
        top_books: topBooks,
        genre_distribution: genreDistribution,
        dept_distribution: deptDistribution,
        recent_transactions: recentTransactions
      }
    });
  } catch (err) {
    console.error('[Dashboard] getDashboardStats error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch dashboard statistics.' });
  }
}

module.exports = { getDashboardStats };
