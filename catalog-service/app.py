from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'catalog-db'),
        database=os.environ.get('DB_NAME', 'catalog_db'),
        user=os.environ.get('DB_USER', 'catalog_user'),
        password=os.environ.get('DB_PASS', 'catalog_pass')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) UNIQUE,
            quantity INTEGER DEFAULT 0,
            price DECIMAL(10, 2)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/catalog', methods=['GET'])
def get_books():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, author, isbn, quantity, price FROM books')
    books = cur.fetchall()
    cur.close()
    conn.close()

    books_list = []
    for book in books:
        books_list.append({
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'isbn': book[3],
            'quantity': book[4],
            'price': float(book[5]) if book[5] else None
        })

    return jsonify({'books': books_list})

@app.route('/catalog/<int:book_id>', methods=['GET'])
def get_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, author, isbn, quantity, price FROM books WHERE id = %s', (book_id,))
    book = cur.fetchone()
    cur.close()
    conn.close()

    if book is None:
        return jsonify({'error': 'Book not found'}), 404

    return jsonify({
        'id': book[0],
        'title': book[1],
        'author': book[2],
        'isbn': book[3],
        'quantity': book[4],
        'price': float(book[5]) if book[5] else None
    })

@app.route('/catalog', methods=['POST'])
def create_book():
    data = request.get_json()

    if not data or 'title' not in data or 'author' not in data:
        return jsonify({'error': 'Title and author are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            'INSERT INTO books (title, author, isbn, quantity, price) VALUES (%s, %s, %s, %s, %s) RETURNING id',
            (data['title'], data['author'], data.get('isbn'), data.get('quantity', 0), data.get('price'))
        )
        book_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Book with this ISBN already exists'}), 409

    cur.close()
    conn.close()

    return jsonify({'message': 'Book created successfully', 'id': book_id}), 201

@app.route('/catalog/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id FROM books WHERE id = %s', (book_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify({'error': 'Book not found'}), 404

    update_fields = []
    values = []

    if 'title' in data:
        update_fields.append('title = %s')
        values.append(data['title'])
    if 'author' in data:
        update_fields.append('author = %s')
        values.append(data['author'])
    if 'isbn' in data:
        update_fields.append('isbn = %s')
        values.append(data['isbn'])
    if 'quantity' in data:
        update_fields.append('quantity = %s')
        values.append(data['quantity'])
    if 'price' in data:
        update_fields.append('price = %s')
        values.append(data['price'])

    if not update_fields:
        cur.close()
        conn.close()
        return jsonify({'error': 'No valid fields to update'}), 400

    values.append(book_id)
    query = f"UPDATE books SET {', '.join(update_fields)} WHERE id = %s"

    try:
        cur.execute(query, values)
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Book with this ISBN already exists'}), 409

    cur.close()
    conn.close()

    return jsonify({'message': 'Book updated successfully'})

@app.route('/catalog/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('DELETE FROM books WHERE id = %s RETURNING id', (book_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted is None:
        return jsonify({'error': 'Book not found'}), 404

    return jsonify({'message': 'Book deleted successfully'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'catalog-service'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)