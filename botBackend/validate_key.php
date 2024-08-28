<?php
header('Content-Type: application/json');
include 'config.php';  // Make sure to include your database connection

// Log the request method for debugging
error_log("Request method: " . $_SERVER['REQUEST_METHOD']);

// Get the raw POST data
$input = file_get_contents('php://input');

// Log the raw input data for debugging
error_log("Raw input data: " . $input);

// Check if the input is not empty
if (!$input) {
    // Attempt to use $_POST as a fallback
    error_log("Attempting to use \$_POST");
    $input = json_encode($_POST);
    error_log("\$_POST data: " . print_r($_POST, true));
}

if (!$input) {
    echo json_encode(["error" => "No input data received"]);
    exit;
}

// Decode the JSON data
$data = json_decode($input, true);

// Check if JSON decoding succeeded
$jsonError = json_last_error();
if ($jsonError !== JSON_ERROR_NONE) {
    error_log("JSON decode error: " . json_last_error_msg());
    echo json_encode(["error" => "Invalid JSON input: " . json_last_error_msg()]);
    exit;
}

// Debugging: Output received values for debugging
error_log("Received data: " . print_r($data, true));

// Validate the input data
if (!isset($data['key']) || !isset($data['mac_address'])) {
    echo json_encode(["error" => "Invalid input"]);
    exit;
}

$key = $data['key'];
$mac_address = $data['mac_address'];

// Debugging: Output the extracted key and mac_address
error_log("Extracted key: $key");
error_log("Extracted MAC address: $mac_address");

// Prepare the SQL statement
$stmt = $conn->prepare("SELECT id, mac_address, expiry_date FROM users WHERE license_key = ?");
if ($stmt === false) {
    error_log("Failed to prepare statement: " . $conn->error);
    echo json_encode(["error" => "Failed to prepare statement: " . $conn->error]);
    exit;
}

$stmt->bind_param("s", $key);
$stmt->execute();
$stmt->bind_result($id, $existing_mac_address, $expiry_date);

// Check if the license key exists in the database
if ($stmt->fetch()) {
    // Store the result into variables
    $row_id = $id;
    $row_mac_address = $existing_mac_address;
    $row_expiry_date = $expiry_date;

    // Close the select statement
    $stmt->close();

    // Debugging: Output the retrieved row
    error_log("Database row: id=$row_id, mac_address=$row_mac_address, expiry_date=$row_expiry_date");

    // Check if the license has expired
    $current_date = new DateTime();
    $expiry_date = new DateTime($row_expiry_date);
    
    if ($expiry_date < $current_date) {
        echo json_encode(["error" => "License key has expired"]);
    } else {
        // Check if the MAC address is already associated with this key
        if (!empty($row_mac_address) && $row_mac_address !== $mac_address) {
            echo json_encode(["error" => "License key is already used on another device"]);
        } else {
            // Prepare the update statement
            $update_stmt = $conn->prepare("UPDATE users SET mac_address = ? WHERE id = ?");
            if ($update_stmt === false) {
                error_log("Failed to prepare update statement: " . $conn->error);
                echo json_encode(["error" => "Failed to prepare update statement: " . $conn->error]);
                exit;
            }
            $update_stmt->bind_param("si", $mac_address, $row_id);
            if ($update_stmt->execute()) {
                echo json_encode(["success" => "License key is valid", "data" => ["expiry_date" => $row_expiry_date]]);
            } else {
                error_log("Failed to update MAC address: " . $update_stmt->error);
                echo json_encode(["error" => "Failed to update the MAC address"]);
            }
            $update_stmt->close();
        }
    }
} else {
    echo json_encode(["error" => "Invalid license key"]);
}

// Close the initial statement if it's still open
if ($stmt) {
    $stmt->close();
}

$conn->close();
?>
