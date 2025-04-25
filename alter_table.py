"""
Script to alter the password_hash column in the users table
"""

import pymysql

# Database connection settings - adjust these to match your configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'EddieOliver..1'  # Use your actual database password
DB_NAME = 'linda_mama'

def alter_password_hash_column():
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        with connection.cursor() as cursor:
            # Execute the ALTER TABLE statement to increase column size
            sql = "ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(512) NOT NULL;"
            cursor.execute(sql)
            connection.commit()
            print("✅ Successfully altered password_hash column to VARCHAR(512)")
            
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("Altering users table to fix password_hash column length...")
    alter_password_hash_column() 