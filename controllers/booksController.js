/**
 * Books Controller - Library Management System
 * Implements all book CRUD operations + search + sort
 * Uses node:sqlite (Node 24 built-in)
 */

const { getDb } = require('../database/db');

// GET /api/books - Get all books with optional search/filter/sort
function getAllBooks(req, res) {
  try {
    const db = getDb();
    const { search, search_by, sort_by, order, available_only } = req.query;

    // Build base query
    let conditions = ['1=1'];
    const params = [];

    // Search
    if (search && search.trim()) {
      const q = `%${search.trim().toLowerCase()}%`;
      const mode = search_by || 'all';
      if (mode === 'title') {
        conditions.push('LOWER(title) LIKE ?');
        params.push(q);
      } else if (mode === 'author') {
        conditions.push('LOWER(author) LIKE ?');
        params.push(q);
      } else if (mode === 'genre') {
        conditions.push('LOWER(genre) LIKE ?');
        params.push(q);
      } else {
        conditions.push('(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(genre) LIKE ? OR LOWER(book_id) LIKE ?)');
        params.push(q, q, q, q);
      }
    }

    if (available_only === 'true') {
      conditions.push('available_copies > 0');
    }

    const validSortCols = { title: 'title', author: 'author', issue_count: 'issue_count', available_copies: 'available_copies', book_id: 'book_id' };
    const sortCol = validSortCols[sort_by] || 'title';
    const sortOrder = order === 'desc' ? 'DESC' : 'ASC';

    const query = `SELECT * FROM books WHERE ${conditions.join(' AND ')} ORDER BY ${sortCol} COLLATE NOCASE ${sortOrder}`;
    const books = db.prepare(query).all(...params);
    res.json({ success: true, data: books, count: books.length });
  } catch (err) {
    console.error('[Books] getAllBooks error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch books.' });
  }
}

// GET /api/books/:id
function getBookById(req, res) {
  try {
    const db = getDb();
    const book_id = req.params.id.trim().toUpperCase();
    const book = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    if (!book) {
      return res.status(404).json({ success: false, error: `Book with ID '${book_id}' was not found in the catalog.` });
    }
    res.json({ success: true, data: book });
  } catch (err) {
    console.error('[Books] getBookById error:', err);
    res.status(500).json({ success: false, error: 'Failed to fetch book.' });
  }
}

// POST /api/books
function addBook(req, res) {
  try {
    const db = getDb();
    let { book_id, title, author, genre, total_copies } = req.body;

    if (!book_id || !book_id.trim()) return res.status(400).json({ success: false, error: 'Book ID cannot be blank.' });
    if (!title || !title.trim()) return res.status(400).json({ success: false, error: 'Book title cannot be blank.' });
    if (!author || !author.trim()) return res.status(400).json({ success: false, error: 'Author name cannot be blank.' });

    book_id = book_id.trim().toUpperCase();
    total_copies = parseInt(total_copies) || 1;

    if (total_copies < 1) return res.status(400).json({ success: false, error: 'Total copies must be at least 1.' });

    const existing = db.prepare('SELECT book_id FROM books WHERE book_id = ?').get(book_id);
    if (existing) {
      return res.status(409).json({ success: false, error: `Duplicate Book ID detected: '${book_id}' already exists in the records.` });
    }

    db.prepare(`
      INSERT INTO books (book_id, title, author, genre, total_copies, available_copies, issue_count)
      VALUES (?, ?, ?, ?, ?, ?, 0)
    `).run(book_id, title.trim(), author.trim(), (genre || 'General').trim(), total_copies, total_copies);

    const newBook = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    res.status(201).json({ success: true, message: `Book '${title.trim()}' added successfully.`, data: newBook });
  } catch (err) {
    console.error('[Books] addBook error:', err);
    res.status(500).json({ success: false, error: 'Failed to add book.' });
  }
}

// PUT /api/books/:id
function updateBook(req, res) {
  try {
    const db = getDb();
    const book_id = req.params.id.trim().toUpperCase();

    const existing = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    if (!existing) {
      return res.status(404).json({ success: false, error: `Book with ID '${book_id}' was not found.` });
    }

    let { title, author, genre, total_copies } = req.body;
    if (!title || !title.trim()) return res.status(400).json({ success: false, error: 'Book title cannot be blank.' });
    if (!author || !author.trim()) return res.status(400).json({ success: false, error: 'Author name cannot be blank.' });

    total_copies = parseInt(total_copies) || existing.total_copies;
    if (total_copies < 1) return res.status(400).json({ success: false, error: 'Total copies must be at least 1.' });

    const issuedCopies = existing.total_copies - existing.available_copies;
    const newAvailable = Math.max(0, total_copies - issuedCopies);

    db.prepare(`
      UPDATE books SET title=?, author=?, genre=?, total_copies=?, available_copies=? WHERE book_id=?
    `).run(title.trim(), author.trim(), (genre || 'General').trim(), total_copies, newAvailable, book_id);

    const updated = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    res.json({ success: true, message: `Book '${book_id}' updated successfully.`, data: updated });
  } catch (err) {
    console.error('[Books] updateBook error:', err);
    res.status(500).json({ success: false, error: 'Failed to update book.' });
  }
}

// DELETE /api/books/:id
function deleteBook(req, res) {
  try {
    const db = getDb();
    const book_id = req.params.id.trim().toUpperCase();

    const existing = db.prepare('SELECT * FROM books WHERE book_id = ?').get(book_id);
    if (!existing) {
      return res.status(404).json({ success: false, error: `Book with ID '${book_id}' was not found.` });
    }

    if (existing.available_copies < existing.total_copies) {
      return res.status(409).json({ success: false, error: `Cannot delete '${existing.title}': Some copies are currently issued to students.` });
    }

    db.prepare('DELETE FROM books WHERE book_id = ?').run(book_id);
    res.json({ success: true, message: `Book '${existing.title}' deleted successfully.` });
  } catch (err) {
    console.error('[Books] deleteBook error:', err);
    res.status(500).json({ success: false, error: 'Failed to delete book.' });
  }
}

module.exports = { getAllBooks, getBookById, addBook, updateBook, deleteBook };
