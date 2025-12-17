-- Catalog Service Database Initialization (PostgreSQL)
-- Creates books table and inserts sample data

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    quantity INTEGER DEFAULT 0,
    price DECIMAL(10, 2)
);

-- Insert sample books
INSERT INTO books (title, author, isbn, quantity, price) VALUES
    ('The Great Gatsby', 'F. Scott Fitzgerald', '978-0743273565', 10, 14.99),
    ('To Kill a Mockingbird', 'Harper Lee', '978-0061120084', 15, 12.99),
    ('1984', 'George Orwell', '978-0451524935', 20, 11.99),
    ('Pride and Prejudice', 'Jane Austen', '978-0141439518', 8, 9.99),
    ('The Catcher in the Rye', 'J.D. Salinger', '978-0316769488', 12, 13.99)
ON CONFLICT (isbn) DO NOTHING;
