<?php
// Include PHPMailer classes manually
require 'PHPMailer/src/PHPMailer.php';
require 'PHPMailer/src/SMTP.php';
require 'PHPMailer/src/Exception.php';
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

$servername = "localhost";  
$username = "nextvego_AviatorBotAdmin";
$password = "AviatorBotAdmin";
$dbname = "nextvego_aviator_db";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Determine the content type of the request
$contentType = $_SERVER["CONTENT_TYPE"] ?? '';

if (strpos($contentType, 'application/json') !== false) {
    // Handle JSON input
    $data = json_decode(file_get_contents('php://input'), true);
    $name = $data['name'] ?? null;
    $email = $data['email'] ?? null;
    $country = $data['country'] ?? null;
    $validity_period = $data['validity_period'] ;
} else {
    // Handle form data input
    $name = $_POST['name'] ?? null;
    $email = $_POST['email'] ?? null;
    $country = $_POST['country'] ?? null;
    $validity_period = $_POST['validity_period'] ;
}

$ip_address = $_SERVER['REMOTE_ADDR'];
$mac_address = $_POST['mac_address'] ;

// Debugging: Output received values for debugging
error_log("Received data - Name: $name, Email: $email, Country: $country, Validity Period: $validity_period");

if ($name && $email && $country && $validity_period) {
    $licenseKey = generateLicenseKey();
    $dateGenerated = date('Y-m-d H:i:s');
    $expiryDate = date('Y-m-d H:i:s', strtotime("+$validity_period days"));

    // Insert into database
    $stmt = $conn->prepare("INSERT INTO users (name, email, ip_address, country, license_key, mac_address, date_generated, expiry_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
    if ($stmt === false) {
        error_log("Failed to prepare statement: " . $conn->error);
        echo json_encode(["error" => "Failed to prepare statement: " . $conn->error]);
        $conn->close();
        exit;
    }

    $stmt->bind_param("ssssssss", $name, $email, $ip_address, $country, $licenseKey, $mac_address, $dateGenerated, $expiryDate);

    if ($stmt->execute()) {
        if (sendEmail($email, $licenseKey, $expiryDate)) {
            echo json_encode(["success" => "License key generated and sent successfully."]);
        } else {
            error_log("Mailer Error: " . $mail->ErrorInfo);
            echo json_encode(["error" => "License key generated, but failed to send email."]);
        }
    } else {
        error_log("Failed to execute statement: " . $stmt->error);
        echo json_encode(["error" => "Failed to generate license key: " . $stmt->error]);
    }

    $stmt->close();
} else {
    echo json_encode(["error" => "Invalid input."]);
}

$conn->close();

function generateLicenseKey($length = 6) {
    $characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $charactersLength = strlen($characters);
    $randomString = '';
    for ($i = 0; $i < $length; $i++) {
        $randomString .= $characters[rand(0, $charactersLength - 1)];
    }
    return $randomString;
}

function sendEmail($email, $licenseKey, $expiryDate) {
    $mail = new PHPMailer(true); // Enable exceptions

    try {
        //Server settings
        $mail->isSMTP();
        $mail->Host = 'premium294.web-hosting.com';  // Specify main and backup SMTP servers
        $mail->SMTPAuth = true;
        $mail->Username = 'aviator@nextgendynamicsnaija.com';  // SMTP username
        $mail->Password = 'Google@2024';  // SMTP password
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port = 587;

        //Recipients
        $mail->setFrom('no-reply@nextgendynamicsnaija.com', 'License Key Service');
        $mail->addAddress($email);

        //Content
        $mail->Subject = 'Your License Key';
        $mail->Body    = "Your license key is: $licenseKey\n\nIt expires on: $expiryDate";

        $mail->send();
        return true;
    } catch (Exception $e) {
        error_log("Mailer Error: " . $e->getMessage());
        error_log("Detailed Error Info: " . print_r($e->getTrace(), true));
        return false;
    }
}
?>
