from flask import Flask, request, jsonify
import mysql.connector
import os
import time

app = Flask(__name__)

def get_db_connection():
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'user-db'),
                database=os.environ.get('DB_NAME', 'user_db'),
                user=os.environ.get('DB_USER', 'user_user'),
                password=os.environ.get('DB_PASS', 'user_pass')
            )
            return conn
        except mysql.connector.Error as err:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise err

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, full_name, created_at FROM users')
    users = cur.fetchall()
    cur.close()
    conn.close()

    users_list = []
    for user in users:
        users_list.append({
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3],
            'created_at': user[4].isoformat() if user[4] else None
        })

    return jsonify({'users': users_list})

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, full_name, created_at FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user[0],
        'username': user[1],
        'email': user[2],
        'full_name': user[3],
        'created_at': user[4].isoformat() if user[4] else None
    })

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Username and email are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            'INSERT INTO users (username, email, full_name) VALUES (%s, %s, %s)',
            (data['username'], data['email'], data.get('full_name'))
        )
        conn.commit()
        user_id = cur.lastrowid
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        cur.close()
        conn.close()
        if 'username' in str(e):
            return jsonify({'error': 'Username already exists'}), 409
        else:
            return jsonify({'error': 'Email already exists'}), 409

    cur.close()
    conn.close()

    return jsonify({'message': 'User created successfully', 'id': user_id}), 201

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
    if cur.fetchone() is None:
        cur.close()
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    update_fields = []
    values = []

    if 'username' in data:
        update_fields.append('username = %s')
        values.append(data['username'])
    if 'email' in data:
        update_fields.append('email = %s')
        values.append(data['email'])
    if 'full_name' in data:
        update_fields.append('full_name = %s')
        values.append(data['full_name'])

    if not update_fields:
        cur.close()
        conn.close()
        return jsonify({'error': 'No valid fields to update'}), 400

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"

    try:
        cur.execute(query, values)
        conn.commit()
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 409

    cur.close()
    conn.close()

    return jsonify({'message': 'User updated successfully'})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    affected_rows = cur.rowcount
    cur.close()
    conn.close()

    if affected_rows == 0:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'message': 'User deleted successfully'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user-service'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)