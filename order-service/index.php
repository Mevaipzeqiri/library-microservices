<?php
header('Content-Type: application/json');

// Database configuration from environment variables
$db_host = getenv('DB_HOST') ?: 'order-db';
$db_name = getenv('DB_NAME') ?: 'order_db';
$db_user = getenv('DB_USER') ?: 'order_user';
$db_pass = getenv('DB_PASS') ?: 'order_pass';

// Create database connection
function getDbConnection() {
    global $db_host, $db_name, $db_user, $db_pass;

    $maxRetries = 10;
    $retryDelay = 3;

    for ($i = 0; $i < $maxRetries; $i++) {
        try {
            $conn = new PDO(
                "mysql:host=$db_host;dbname=$db_name;charset=utf8mb4",
                $db_user,
                $db_pass,
                [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
            );
            return $conn;
        } catch (PDOException $e) {
            if ($i < $maxRetries - 1) {
                sleep($retryDelay);
            } else {
                throw $e;
            }
        }
    }
}

// Initialize database table
function initDb() {
    $conn = getDbConnection();
    $sql = "CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        quantity INT DEFAULT 1,
        status VARCHAR(50) DEFAULT 'pending',
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_price DECIMAL(10, 2)
    )";
    $conn->exec($sql);
}

// Initialize database on first request
try {
    initDb();
} catch (Exception $e) {
    // Table might already exist, continue
}

// Get request method and path
$method = $_SERVER['REQUEST_METHOD'];
$uri = $_SERVER['REQUEST_URI'];
$path = parse_url($uri, PHP_URL_PATH);

// Remove trailing slash
$path = rtrim($path, '/');

// Route handling
if ($path === '/orders' || $path === '') {
    switch ($method) {
        case 'GET':
            getAllOrders();
            break;
        case 'POST':
            createOrder();
            break;
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} elseif (preg_match('/^\/orders\/(\d+)$/', $path, $matches)) {
    $orderId = $matches[1];
    switch ($method) {
        case 'GET':
            getOrder($orderId);
            break;
        case 'PUT':
            updateOrder($orderId);
            break;
        case 'DELETE':
            deleteOrder($orderId);
            break;
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} elseif ($path === '/health') {
    echo json_encode(['status' => 'healthy', 'service' => 'order-service']);
} else {
    http_response_code(404);
    echo json_encode(['error' => 'Not found']);
}

// READ - Get all orders
function getAllOrders() {
    try {
        $conn = getDbConnection();
        $stmt = $conn->query('SELECT id, user_id, book_id, quantity, status, order_date, total_price FROM orders');
        $orders = $stmt->fetchAll(PDO::FETCH_ASSOC);

        echo json_encode(['orders' => $orders]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
    }
}

// READ - Get a single order
function getOrder($orderId) {
    try {
        $conn = getDbConnection();
        $stmt = $conn->prepare('SELECT id, user_id, book_id, quantity, status, order_date, total_price FROM orders WHERE id = ?');
        $stmt->execute([$orderId]);
        $order = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$order) {
            http_response_code(404);
            echo json_encode(['error' => 'Order not found']);
            return;
        }

        echo json_encode($order);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
    }
}

// CREATE - Create a new order
function createOrder() {
    $data = json_decode(file_get_contents('php://input'), true);

    if (!$data || !isset($data['user_id']) || !isset($data['book_id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'user_id and book_id are required']);
        return;
    }

    try {
        $conn = getDbConnection();
        $stmt = $conn->prepare('INSERT INTO orders (user_id, book_id, quantity, status, total_price) VALUES (?, ?, ?, ?, ?)');
        $stmt->execute([
            $data['user_id'],
            $data['book_id'],
            $data['quantity'] ?? 1,
            $data['status'] ?? 'pending',
            $data['total_price'] ?? null
        ]);

        $orderId = $conn->lastInsertId();

        http_response_code(201);
        echo json_encode(['message' => 'Order created successfully', 'id' => (int)$orderId]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
    }
}

// UPDATE - Update an existing order
function updateOrder($orderId) {
    $data = json_decode(file_get_contents('php://input'), true);

    if (!$data) {
        http_response_code(400);
        echo json_encode(['error' => 'No data provided']);
        return;
    }

    try {
        $conn = getDbConnection();

        // Check if order exists
        $stmt = $conn->prepare('SELECT id FROM orders WHERE id = ?');
        $stmt->execute([$orderId]);
        if (!$stmt->fetch()) {
            http_response_code(404);
            echo json_encode(['error' => 'Order not found']);
            return;
        }

        // Build update query dynamically
        $updateFields = [];
        $values = [];

        if (isset($data['user_id'])) {
            $updateFields[] = 'user_id = ?';
            $values[] = $data['user_id'];
        }
        if (isset($data['book_id'])) {
            $updateFields[] = 'book_id = ?';
            $values[] = $data['book_id'];
        }
        if (isset($data['quantity'])) {
            $updateFields[] = 'quantity = ?';
            $values[] = $data['quantity'];
        }
        if (isset($data['status'])) {
            $updateFields[] = 'status = ?';
            $values[] = $data['status'];
        }
        if (isset($data['total_price'])) {
            $updateFields[] = 'total_price = ?';
            $values[] = $data['total_price'];
        }

        if (empty($updateFields)) {
            http_response_code(400);
            echo json_encode(['error' => 'No valid fields to update']);
            return;
        }

        $values[] = $orderId;
        $sql = 'UPDATE orders SET ' . implode(', ', $updateFields) . ' WHERE id = ?';
        $stmt = $conn->prepare($sql);
        $stmt->execute($values);

        echo json_encode(['message' => 'Order updated successfully']);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
    }
}

// DELETE - Delete an order
function deleteOrder($orderId) {
    try {
        $conn = getDbConnection();
        $stmt = $conn->prepare('DELETE FROM orders WHERE id = ?');
        $stmt->execute([$orderId]);

        if ($stmt->rowCount() === 0) {
            http_response_code(404);
            echo json_encode(['error' => 'Order not found']);
            return;
        }

        echo json_encode(['message' => 'Order deleted successfully']);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
    }
}
?>
