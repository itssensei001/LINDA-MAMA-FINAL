"""
Script to recreate the notifications table with the correct structure
"""

import pymysql

# Database connection settings - adjust these to match your configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'EddieOliver..1'  # Use your actual database password
DB_NAME = 'linda_mama'

def describe_table(cursor, table_name):
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    print(f"Structure of {table_name} table:")
    for col in columns:
        print(f"  {col[0]}: {col[1]} {' PRIMARY KEY' if col[3] == 'PRI' else ''}")
    print()

def recreate_notifications_table():
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
            cursor.execute("SHOW TABLES LIKE 'notifications'")
            if cursor.fetchone():
                # Describe the table before dropping it
                describe_table(cursor, 'notifications')
                
                # Drop the existing table
                print("Dropping existing notifications table...")
                cursor.execute("DROP TABLE IF EXISTS notifications")
                print("✅ Dropped existing notifications table")
            
            # Create the notifications table with correct structure
            sql = """
            CREATE TABLE notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                notification_type VARCHAR(50),
                related_id INT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(sql)
            print("✅ Created notifications table with correct structure")
            
            # Describe the new table
            describe_table(cursor, 'notifications')
            
            connection.commit()
            print("✅ Notifications table recreation completed")
            
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("Recreating notifications table with correct structure...")
    recreate_notifications_table() 