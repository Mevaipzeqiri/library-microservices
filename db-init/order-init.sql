-- Order Service Database Initialization (MySQL)
-- Creates orders table and inserts sample data

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_price DECIMAL(10, 2)
);

-- Insert sample orders
INSERT IGNORE INTO orders (user_id, book_id, quantity, status, total_price) VALUES
    (1, 1, 2, 'completed', 29.98),
    (2, 3, 1, 'pending', 11.99),
    (3, 2, 3, 'shipped', 38.97),
    (1, 5, 1, 'completed', 13.99),
    (4, 4, 2, 'pending', 19.98);
