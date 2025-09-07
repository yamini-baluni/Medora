#!/usr/bin/env python3
"""
Database Setup Script for Medora
This script will create the database and tables if they don't exist.
"""

import pymysql
import sys
import os

def create_database():
    """Create the database and tables"""
    
    # Database configuration - Updated to use new user
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'medora_user',
        'password': 'medora123',
        'charset': 'utf8mb4'
    }
    
    try:
        # Connect to MySQL server
        print("Connecting to MySQL server...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        print("Creating database 'medora_db'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS medora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE medora_db")
        
        # Create users table
        print("Creating users table...")
        cursor.execute("""
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Create patients table
        print("Creating patients table...")
        cursor.execute("""
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
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create appointments table
        print("Creating appointments table...")
        cursor.execute("""
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
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        try:
            cursor.execute("CREATE INDEX idx_username ON users(username)")
        except:
            pass  # Index might already exist
        try:
            cursor.execute("CREATE INDEX idx_email ON users(email)")
        except:
            pass  # Index might already exist
        try:
            cursor.execute("CREATE INDEX idx_patient_id ON patients(patient_id)")
        except:
            pass  # Index might already exist
        try:
            cursor.execute("CREATE INDEX idx_user_id ON patients(user_id)")
        except:
            pass  # Index might already exist
        try:
            cursor.execute("CREATE INDEX idx_appointment_date ON appointments(appointment_date)")
        except:
            pass  # Index might already exist
        
        # Insert default admin user (password: Admin123!)
        print("Creating default admin user...")
        admin_password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhHhqG'
        cursor.execute("""
            INSERT IGNORE INTO users (username, email, password_hash, first_name, last_name, role) 
            VALUES ('admin', 'admin@medora.com', %s, 'Admin', 'User', 'admin')
        """, (admin_password_hash,))
        
        # Commit changes
        connection.commit()
        
        print("✅ Database setup completed successfully!")
        print("📊 Database: medora_db")
        print("👤 Default admin user: admin / Admin123!")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📋 Tables created: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure MySQL is running")
        print("2. We need to create the 'medora_user' first")
        print("3. Run the create_user script first")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
        
    finally:
        if 'connection' in locals():
            connection.close()

def test_connection():
    """Test the database connection"""
    try:
        connection = pymysql.connect(
            host='localhost',
            user='medora_user',
            password='medora123',
            database='medora_db',
            charset='utf8mb4'
        )
        print("✅ Database connection test successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Medora Database Setup")
    print("=" * 40)
    
    print("⚠️  IMPORTANT: This script requires the 'medora_user' MySQL user to exist.")
    print("If you haven't created it yet, run the create_user script first.")
    
    create_database()
    
    if test_connection():
        print("\n🎉 Setup completed! You can now run the Flask application.")
        print("Run: python run.py")
    else:
        print("\n⚠️  Setup completed but connection test failed.")
        print("Please check your MySQL configuration.") 