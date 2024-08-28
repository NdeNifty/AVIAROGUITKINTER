<?php
// Database configuration
$servername = "localhost";  
$username = "nextvego_AviatorBotAdmin";
$password = "AviatorBotAdmin";
$dbname = "nextvego_aviator_db";

// Create a connection to the database
$conn = new mysqli($servername, $username, $password, $dbname);

// Check the database connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
