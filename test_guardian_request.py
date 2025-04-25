"""
Script to test guardian request and notification creation
"""

import pymysql
import datetime

# Database connection settings - adjust these to match your configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'EddieOliver..1'  # Use your actual database password
DB_NAME = 'linda_mama'

def test_guardian_request_notification():
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        with connection.cursor() as cursor:
            # First, check if we have a guardian and mother to use for testing
            cursor.execute("SELECT id, email, full_name FROM users WHERE role = 'guardian' LIMIT 1")
            guardian = cursor.fetchone()
            
            cursor.execute("SELECT id, email, full_name FROM users WHERE role = 'mother' LIMIT 1")
            mother = cursor.fetchone()
            
            if not guardian:
                print("⚠️ No guardian user found for testing, creating one...")
                # Insert a test guardian user
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, full_name, role, date_created, is_active, is_verified) 
                    VALUES 
                    ('testguardian', 'testguardian@example.com', 'test_password_hash', 'Test Guardian', 'guardian', NOW(), 1, 1)
                """)
                guardian_id = cursor.lastrowid
                guardian = (guardian_id, 'testguardian@example.com', 'Test Guardian')
                print(f"✅ Created test guardian user with ID: {guardian_id}")
            else:
                print(f"✓ Using existing guardian: {guardian[2]} (ID: {guardian[0]})")
            
            if not mother:
                print("⚠️ No mother user found for testing, creating one...")
                # Insert a test mother user
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, full_name, role, date_created, is_active, is_verified) 
                    VALUES 
                    ('testmother', 'testmother@example.com', 'test_password_hash', 'Test Mother', 'mother', NOW(), 1, 1)
                """)
                mother_id = cursor.lastrowid
                mother = (mother_id, 'testmother@example.com', 'Test Mother')
                
                # We need to create a MotherProfile record too
                cursor.execute("""
                    INSERT INTO mother_profiles 
                    (user_id) 
                    VALUES (%s)
                """, (mother_id,))
                print(f"✅ Created test mother user with ID: {mother_id}")
            else:
                print(f"✓ Using existing mother: {mother[2]} (ID: {mother[0]})")
            
            # Check if there's already a guardian request
            cursor.execute("""
                SELECT id FROM guardian_requests 
                WHERE guardian_id = %s AND mother_email = %s
            """, (guardian[0], mother[1]))
            existing_request = cursor.fetchone()
            
            request_id = None
            if existing_request:
                request_id = existing_request[0]
                print(f"✓ Found existing guardian request with ID: {request_id}")
            else:
                # Create a test guardian request
                cursor.execute("""
                    INSERT INTO guardian_requests 
                    (guardian_id, mother_email, request_date, status) 
                    VALUES (%s, %s, NOW(), 'pending')
                """, (guardian[0], mother[1]))
                request_id = cursor.lastrowid
                print(f"✅ Created test guardian request with ID: {request_id}")
            
            # Check if there's a notification for this request
            cursor.execute("""
                SELECT id FROM notifications 
                WHERE user_id = %s AND notification_type = 'guardian_request' AND related_id = %s
            """, (mother[0], request_id))
            existing_notification = cursor.fetchone()
            
            if existing_notification:
                notification_id = existing_notification[0]
                print(f"✓ Found existing notification with ID: {notification_id}")
            else:
                # Create a notification manually
                cursor.execute("""
                    INSERT INTO notifications 
                    (user_id, content, notification_type, related_id, is_read, timestamp) 
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (mother[0], f"{guardian[2]} wants to be your guardian", 'guardian_request', request_id, False))
                notification_id = cursor.lastrowid
                print(f"✅ Created manual notification with ID: {notification_id}")
            
            # Check if the notification is fetched correctly from API
            cursor.execute("""
                SELECT id, content, notification_type, related_id, is_read 
                FROM notifications 
                WHERE user_id = %s AND is_read = 0
            """, (mother[0],))
            all_notifications = cursor.fetchall()
            
            print(f"\nActive notifications for mother (ID: {mother[0]}):")
            for notif in all_notifications:
                print(f"  - ID: {notif[0]}, Type: {notif[2]}, Content: {notif[1]}, Related ID: {notif[3]}, Read: {notif[4]}")
            
            connection.commit()
            print("\n✅ Guardian request and notification test completed")
            print("▶ Now run the app and log in as the mother to check if notifications appear")
            
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("Testing guardian request notification system...")
    test_guardian_request_notification() 