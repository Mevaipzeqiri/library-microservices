-- User Service Database Initialization (MySQL)
-- Creates users table and inserts sample data

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT IGNORE INTO users (username, email, full_name) VALUES
    ('john_doe', 'john.doe@example.com', 'John Doe'),
    ('jane_smith', 'jane.smith@example.com', 'Jane Smith'),
    ('bob_wilson', 'bob.wilson@example.com', 'Bob Wilson'),
    ('alice_jones', 'alice.jones@example.com', 'Alice Jones'),
    ('charlie_brown', 'charlie.brown@example.com', 'Charlie Brown');
