#!/usr/bin/env python3
"""
Create MySQL User Script for Medora
This script will create the medora_user MySQL user with proper permissions.
"""

import pymysql
import sys

def create_mysql_user():
    """Create the medora_user MySQL user"""

    try:
        # Connect to MySQL as root
        print("🔐 Connecting to MySQL as root...")
        print("Please enter your MySQL root password when prompted.")
        
        root_password = input("Enter MySQL root password (or press Enter if no password): ").strip()
        
        if root_password:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password=root_password,
                charset='utf8mb4'
            )
        else:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                charset='utf8mb4'
            )
        
        cursor = connection.cursor()
        
        # Create medora_user if it doesn't exist
        print("👤 Creating medora_user...")
        cursor.execute("CREATE USER IF NOT EXISTS 'medora_user'@'localhost' IDENTIFIED BY 'medora123'")
        
        # Grant privileges
        print("🔑 Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON medora_db.* TO 'medora_user'@'localhost'")
        cursor.execute("GRANT CREATE ON *.* TO 'medora_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("✅ MySQL user 'medora_user' created successfully!")
        print("👤 Username: medora_user")
        print("🔑 Password: medora123")
        print("📊 Database: medora_db")
        
        # Test the new user connection
        print("\n🧪 Testing new user connection...")
        test_connection = pymysql.connect(
            host='localhost',
            user='medora_user',
            password='medora123',
            charset='utf8mb4'
        )
        test_connection.close()
        print("✅ Connection test successful!")
        
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure MySQL is running")
        print("2. Check if your root password is correct")
        print("3. Make sure you have privileges to create users")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Medora MySQL User Creation")
    print("=" * 40)
    
    if create_mysql_user():
        print("\n🎉 User creation completed!")
        print("Now you can run: python setup_database.py")
    else:
        print("\n❌ Failed to create MySQL user.")
        sys.exit(1) 