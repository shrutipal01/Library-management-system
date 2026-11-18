/**
 * Students Controller - Library Management System
 * Uses node:sqlite (Node 24 built-in)
 */

const { getDb } = require('../database/db');

function isValidStudentName(name) {
  return typeof name === 'string' && /^[\p{L} ]+$/u.test(name.trim());
}

function getAllStudents(req, res) {
  try {
    const db = getDb();
    const { search } = req.query;

    let students;
    if (search && search.trim()) {
      const q = `%${search.trim().toLowerCase()}%`;
      students = db.prepare(`
        SELECT s.*, 
          (SELECT COUNT(*) FROM transactions t WHERE t.student_id = s.student_id AND t.status = 'ISSUED') as active_loans
        FROM students s
        WHERE LOWER(s.name) LIKE ? OR LOWER(s.student_id) LIKE ? OR LOWER(s.department) LIKE ?
        ORDER BY s.name COLLATE NOCASE
      `).all(q, q, q);
    } else {
      students = db.prepare(`
        SELECT s.*, 
          (SELECT COUNT(*) FROM transactions t WHERE t.student_id = s.student_id AND t.status = 'ISSUED') as active_loans
        FROM students s
        ORDER BY s.name COLLATE NOCASE
      `).all();
    }

    const getActiveLoanBooks = db.prepare(
      `SELECT book_id FROM transactions WHERE student_id = ? AND status = 'ISSUED'`
    );

    const enriched = students.map(s => ({
      ...s,
      borrowed_books: getActiveLoanBooks.all(s.student_id).map(r => r.book_id)
    }));

    res.json({ success: true, data: enriched, count: enriched.length });
  } catch (err) {
    console.error('[Students] getAllStudents error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch students.' });
  }
}

function getStudentById(req, res) {
  try {
    const db = getDb();
    const student_id = req.params.id.trim().toUpperCase();

    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!student) {
      return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered in the system.` });
    }

    const borrowedBooks = db.prepare(`
      SELECT t.book_id, b.title FROM transactions t
      JOIN books b ON t.book_id = b.book_id
      WHERE t.student_id = ? AND t.status = 'ISSUED'
    `).all(student_id);

    res.json({
      success: true,
      data: {
        ...student,
        borrowed_books: borrowedBooks.map(r => r.book_id),
        borrowed_book_titles: borrowedBooks
      }
    });
  } catch (err) {
    console.error('[Students] getStudentById error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch student.' });
  }
}

function addStudent(req, res) {
  try {
    const db = getDb();
    let { student_id, name, department, contact } = req.body;

    if (!student_id || !student_id.trim()) return res.status(400).json({ success: false, error: 'Student ID cannot be empty.' });
    if (typeof name !== 'string' || !name.trim()) return res.status(400).json({ success: false, error: 'Student name cannot be empty.' });
    if (!isValidStudentName(name)) return res.status(400).json({ success: false, error: 'Student name can only contain letters and spaces.' });

    student_id = student_id.trim().toUpperCase();

    const existing = db.prepare('SELECT student_id FROM students WHERE student_id = ?').get(student_id);
    if (existing) {
      return res.status(409).json({ success: false, error: `Duplicate Student ID detected: '${student_id}' already exists in the records.` });
    }

    db.prepare(`
      INSERT INTO students (student_id, name, department, contact) VALUES (?, ?, ?, ?)
    `).run(student_id, name.trim(), (department || 'MCA').trim(), (contact || 'N/A').trim());

    const newStudent = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    res.status(201).json({ success: true, message: `Student '${name.trim()}' registered successfully.`, data: { ...newStudent, borrowed_books: [] } });
  } catch (err) {
    console.error('[Students] addStudent error:', err);
    res.status(500).json({ success: false, error: 'Failed to register student.' });
  }
}

function updateStudent(req, res) {
  try {
    const db = getDb();
    const student_id = req.params.id.trim().toUpperCase();

    const existing = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!existing) {
      return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered.` });
    }

    let { name, department, contact } = req.body;
    if (typeof name !== 'string' || !name.trim()) return res.status(400).json({ success: false, error: 'Student name cannot be empty.' });
    if (!isValidStudentName(name)) return res.status(400).json({ success: false, error: 'Student name can only contain letters and spaces.' });

    db.prepare(`UPDATE students SET name=?, department=?, contact=? WHERE student_id=?`)
      .run(name.trim(), (department || 'MCA').trim(), (contact || 'N/A').trim(), student_id);

    const updated = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    res.json({ success: true, message: `Student '${student_id}' updated successfully.`, data: updated });
  } catch (err) {
    console.error('[Students] updateStudent error:', err);
    res.status(500).json({ success: false, error: 'Failed to update student.' });
  }
}

function deleteStudent(req, res) {
  try {
    const db = getDb();
    const student_id = req.params.id.trim().toUpperCase();

    const existing = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!existing) {
      return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered.` });
    }

    const activeLoans = db.prepare(`SELECT COUNT(*) as count FROM transactions WHERE student_id = ? AND status = 'ISSUED'`).get(student_id);
    if (activeLoans.count > 0) {
      return res.status(409).json({ success: false, error: `Cannot delete student '${existing.name}': They have ${activeLoans.count} active book loan(s). Please return all books first.` });
    }

    db.prepare('DELETE FROM students WHERE student_id = ?').run(student_id);
    res.json({ success: true, message: `Student '${existing.name}' removed from the system.` });
  } catch (err) {
    console.error('[Students] deleteStudent error:', err);
    res.status(500).json({ success: false, error: 'Failed to delete student.' });
  }
}

function getStudentHistory(req, res) {
  try {
    const db = getDb();
    const student_id = req.params.id.trim().toUpperCase();

    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(student_id);
    if (!student) {
      return res.status(404).json({ success: false, error: `Student with ID '${student_id}' is not registered.` });
    }

    const history = db.prepare(`
      SELECT t.*, b.title as book_title, b.author as book_author
      FROM transactions t
      JOIN books b ON t.book_id = b.book_id
      WHERE t.student_id = ?
      ORDER BY t.issue_date DESC
    `).all(student_id);

    res.json({ success: true, data: history, student });
  } catch (err) {
    console.error('[Students] getStudentHistory error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch student history.' });
  }
}

module.exports = { getAllStudents, getStudentById, addStudent, updateStudent, deleteStudent, getStudentHistory };
