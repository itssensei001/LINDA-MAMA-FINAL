"""
Script to fix the guardian_requests table structure
"""

import pymysql

# Database connection settings - adjust these to match your configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'EddieOliver..1'  # Use your actual database password
DB_NAME = 'linda_mama'

def fix_guardian_requests_table():
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute("SHOW TABLES LIKE 'guardian_requests'")
            if cursor.fetchone():
                # Drop the existing table
                print("Dropping existing guardian_requests table...")
                cursor.execute("DROP TABLE IF EXISTS guardian_requests")
                print("✅ Dropped existing guardian_requests table")
            
            # Create the table with the correct structure
            sql = """
            CREATE TABLE guardian_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guardian_id INT NOT NULL,
                mother_email VARCHAR(100) NOT NULL,
                request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (guardian_id) REFERENCES users(id)
            )
            """
            cursor.execute(sql)
            print("✅ Created new guardian_requests table with correct structure")
            
            connection.commit()
            print("✅ Guardian requests table structure fixed")
            
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("Fixing guardian_requests table structure...")
    fix_guardian_requests_table() 