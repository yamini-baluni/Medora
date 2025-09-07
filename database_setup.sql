-- Medora Database Setup Script
-- This script creates the database and tables for the Medora medical records management system

-- Create database
CREATE DATABASE IF NOT EXISTS medora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE medora_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
);

-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(20) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    blood_type VARCHAR(5),
    height FLOAT,
    weight FLOAT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    address TEXT,
    medical_history TEXT,
    allergies TEXT,
    current_medications TEXT,
    insurance_provider VARCHAR(100),
    insurance_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_user_id (user_id),
    INDEX idx_name (first_name, last_name),
    INDEX idx_date_of_birth (date_of_birth),
    INDEX idx_gender (gender),
    INDEX idx_is_active (is_active)
);

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_name VARCHAR(100) NOT NULL,
    appointment_date DATETIME NOT NULL,
    appointment_type VARCHAR(50),
    symptoms TEXT,
    diagnosis TEXT,
    prescription TEXT,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_appointment_date (appointment_date),
    INDEX idx_doctor_name (doctor_name),
    INDEX idx_status (status)
);

-- Insert default admin user (password: Admin123!)
-- Note: In production, this should be changed immediately
INSERT INTO users (username, email, password_hash, first_name, last_name, role) VALUES 
('admin', 'admin@medora.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhHhqG', 'Admin', 'User', 'admin')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Create indexes for better performance
CREATE INDEX idx_patients_created_at ON patients(created_at);
CREATE INDEX idx_appointments_patient_date ON appointments(patient_id, appointment_date);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Create view for patient statistics
CREATE OR REPLACE VIEW patient_stats AS
SELECT 
    p.user_id,
    COUNT(p.id) as total_patients,
    COUNT(CASE WHEN p.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN 1 END) as new_patients_month,
    COUNT(CASE WHEN p.gender = 'Male' THEN 1 END) as male_count,
    COUNT(CASE WHEN p.gender = 'Female' THEN 1 END) as female_count,
    COUNT(CASE WHEN p.gender = 'Other' THEN 1 END) as other_count
FROM patients p
WHERE p.is_active = TRUE
GROUP BY p.user_id;

-- Create view for appointment statistics
CREATE OR REPLACE VIEW appointment_stats AS
SELECT 
    p.user_id,
    COUNT(a.id) as total_appointments,
    COUNT(CASE WHEN a.status = 'scheduled' THEN 1 END) as scheduled_count,
    COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN a.status = 'cancelled' THEN 1 END) as cancelled_count,
    COUNT(CASE WHEN DATE(a.appointment_date) = CURDATE() THEN 1 END) as today_count,
    COUNT(CASE WHEN a.appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 1 END) as week_count
FROM patients p
LEFT JOIN appointments a ON p.id = a.patient_id
WHERE p.is_active = TRUE
GROUP BY p.user_id;

-- Grant permissions (adjust as needed for your MySQL setup)
-- GRANT ALL PRIVILEGES ON medora_db.* TO 'your_username'@'localhost';
-- FLUSH PRIVILEGES;

-- Show created tables
SHOW TABLES;

-- Show table structure
DESCRIBE users;
DESCRIBE patients;
DESCRIBE appointments; 