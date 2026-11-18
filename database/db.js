/**
 * Database Module - Library Management System
 * Uses Node.js built-in node:sqlite (available in Node 22+)
 * No native compilation required!
 * 
 * Schema mirrors the Python models: Book, Student, Transaction.
 * Business constants preserved from original Python code.
 */

const { DatabaseSync } = require('node:sqlite');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, 'library.db');
const DATA_DIR = path.join(__dirname, '../../data');

// Business rule constants (matching Python models.py)
const MAX_BORROW_LIMIT = 3;
const STANDARD_LOAN_DAYS = 14;
const FINE_TIER1_RATE = 2.0;   // INR per day for days 1-7
const FINE_TIER2_RATE = 5.0;   // INR per day for days 8-14
const FINE_TIER3_RATE = 10.0;  // INR per day for days > 14
const FINE_PENALTY = 50.0;     // Fixed penalty for > 14 days overdue

let db = null;

function getDb() {
  if (!db) {
    db = new DatabaseSync(DB_PATH);
    db.exec('PRAGMA journal_mode = WAL');
    db.exec('PRAGMA foreign_keys = ON');
  }
  return db;
}

function initializeDatabase() {
  const database = getDb();

  // Create Books table
  database.exec(`
    CREATE TABLE IF NOT EXISTS books (
      book_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      author TEXT NOT NULL,
      genre TEXT DEFAULT 'General',
      total_copies INTEGER DEFAULT 1,
      available_copies INTEGER DEFAULT 1,
      issue_count INTEGER DEFAULT 0
    )
  `);

  // Create Students table
  database.exec(`
    CREATE TABLE IF NOT EXISTS students (
      student_id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      department TEXT DEFAULT 'General',
      contact TEXT DEFAULT 'N/A'
    )
  `);

  // Create Transactions table
  database.exec(`
    CREATE TABLE IF NOT EXISTS transactions (
      txn_id TEXT PRIMARY KEY,
      book_id TEXT NOT NULL,
      student_id TEXT NOT NULL,
      issue_date TEXT NOT NULL,
      due_date TEXT NOT NULL,
      return_date TEXT,
      fine_amount REAL DEFAULT 0.0,
      status TEXT DEFAULT 'ISSUED'
    )
  `);

  // Seed from existing JSON files if DB is empty
  const bookCount = database.prepare('SELECT COUNT(*) as count FROM books').get();
  if (bookCount.count === 0) {
    seedFromJsonFiles(database);
  }

  console.log('[DB] Database initialized successfully.');
  return database;
}

function seedFromJsonFiles(database) {
  const booksFile = path.join(DATA_DIR, 'books.json');
  const studentsFile = path.join(DATA_DIR, 'students.json');
  const transactionsFile = path.join(DATA_DIR, 'transactions.json');

  const insertBook = database.prepare(`
    INSERT OR IGNORE INTO books (book_id, title, author, genre, total_copies, available_copies, issue_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  const insertStudent = database.prepare(`
    INSERT OR IGNORE INTO students (student_id, name, department, contact)
    VALUES (?, ?, ?, ?)
  `);

  const insertTxn = database.prepare(`
    INSERT OR IGNORE INTO transactions (txn_id, book_id, student_id, issue_date, due_date, return_date, fine_amount, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // Seed Books
  if (fs.existsSync(booksFile)) {
    const books = JSON.parse(fs.readFileSync(booksFile, 'utf8'));
    books.forEach(b => insertBook.run(
      b.book_id,
      b.title,
      b.author,
      b.genre || 'General',
      b.total_copies || 1,
      b.available_copies !== undefined ? b.available_copies : b.total_copies,
      b.issue_count || 0
    ));
    console.log(`[DB] Seeded ${books.length} books from JSON.`);
  }

  // Seed Students
  if (fs.existsSync(studentsFile)) {
    const students = JSON.parse(fs.readFileSync(studentsFile, 'utf8'));
    students.forEach(s => insertStudent.run(
      s.student_id,
      s.name,
      s.department || 'General',
      s.contact || 'N/A'
    ));
    console.log(`[DB] Seeded ${students.length} students from JSON.`);
  }

  // Seed Transactions
  if (fs.existsSync(transactionsFile)) {
    const txns = JSON.parse(fs.readFileSync(transactionsFile, 'utf8'));
    txns.forEach(t => insertTxn.run(
      t.txn_id,
      t.book_id,
      t.student_id,
      t.issue_date,
      t.due_date,
      t.return_date || null,
      t.fine_amount || 0.0,
      t.status || 'ISSUED'
    ));
    console.log(`[DB] Seeded ${txns.length} transactions from JSON.`);
  }
}

/**
 * Calculate overdue fine - EXACT port of Python Transaction.calculate_fine()
 * Tier 1: 1-7 days overdue   -> INR 2/day
 * Tier 2: 8-14 days overdue  -> INR 2*7 + INR 5*(days-7)
 * Tier 3: >14 days overdue   -> INR 2*7 + INR 5*7 + INR 10*(days-14) + INR 50 penalty
 */
function calculateFine(dueDateStr, returnDateStr = null) {
  const dueDate = new Date(dueDateStr);
  const returnDate = returnDateStr ? new Date(returnDateStr) : new Date();

  // Normalize to midnight for accurate day count
  dueDate.setHours(0, 0, 0, 0);
  returnDate.setHours(0, 0, 0, 0);

  const msPerDay = 24 * 60 * 60 * 1000;
  const overdueDays = Math.floor((returnDate - dueDate) / msPerDay);

  let fine = 0.0;
  let actualOverdue = overdueDays;

  if (overdueDays <= 0) {
    fine = 0.0;
    actualOverdue = 0;
  } else if (overdueDays <= 7) {
    fine = overdueDays * FINE_TIER1_RATE;
  } else if (overdueDays <= 14) {
    fine = (7 * FINE_TIER1_RATE) + ((overdueDays - 7) * FINE_TIER2_RATE);
  } else {
    fine = (7 * FINE_TIER1_RATE) + (7 * FINE_TIER2_RATE) + ((overdueDays - 14) * FINE_TIER3_RATE) + FINE_PENALTY;
  }

  return { fine, overdueDays: actualOverdue };
}

/**
 * Generate unique transaction ID like original: TXN1001, TXN1002...
 */
function generateTxnId(database) {
  const row = database.prepare('SELECT COUNT(*) as count FROM transactions').get();
  return `TXN${row.count + 1001}`;
}

/**
 * Get today's date as YYYY-MM-DD string
 */
function getTodayStr() {
  return new Date().toISOString().split('T')[0];
}

/**
 * Add N days to a date string, return YYYY-MM-DD
 */
function addDays(dateStr, days) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

module.exports = {
  getDb,
  initializeDatabase,
  calculateFine,
  generateTxnId,
  getTodayStr,
  addDays,
  MAX_BORROW_LIMIT,
  STANDARD_LOAN_DAYS
};
