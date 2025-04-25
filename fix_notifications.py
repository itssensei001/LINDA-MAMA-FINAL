"""
Script to fix the notifications table structure and check notifications for guardian requests
"""

import pymysql
import json

# Database connection settings - adjust these to match your configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'EddieOliver..1'  # Use your actual database password
DB_NAME = 'linda_mama'

def fix_notifications_table():
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        with connection.cursor() as cursor:
            # Check if the notifications table exists
            cursor.execute("SHOW TABLES LIKE 'notifications'")
            if not cursor.fetchone():
                # Create the table if it doesn't exist
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
                print("✅ Created notifications table")
            else:
                print("✓ Notifications table exists")
            
            connection.commit()
            print("✅ Notifications table structure verified")
            
            # Check existing guardian requests
            cursor.execute("""
                SELECT gr.id, gr.guardian_id, gr.mother_email, u.full_name as guardian_name, gr.status 
                FROM guardian_requests gr
                JOIN users u ON gr.guardian_id = u.id
                WHERE gr.status = 'pending'
            """)
            
            pending_requests = cursor.fetchall()
            print(f"Found {len(pending_requests)} pending guardian requests")
            
            # Check if each guardian request has a corresponding notification
            for request in pending_requests:
                request_id = request[0]
                guardian_id = request[1]
                mother_email = request[2]
                guardian_name = request[3]
                
                # Find the mother's user ID
                cursor.execute("SELECT id FROM users WHERE email = %s AND role = 'mother'", (mother_email,))
                mother_result = cursor.fetchone()
                
                if mother_result:
                    mother_id = mother_result[0]
                    
                    # Check if a notification exists for this request
                    cursor.execute("""
                        SELECT id FROM notifications 
                        WHERE user_id = %s AND notification_type = 'guardian_request' AND related_id = %s
                    """, (mother_id, request_id))
                    
                    notification = cursor.fetchone()
                    
                    if not notification:
                        # Create a notification for the mother
                        content = f"{guardian_name} wants to be your guardian"
                        cursor.execute("""
                            INSERT INTO notifications 
                            (user_id, content, notification_type, related_id, is_read) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (mother_id, content, 'guardian_request', request_id, False))
                        print(f"✅ Created missing notification for mother {mother_email} for guardian request {request_id}")
                    else:
                        print(f"✓ Notification already exists for mother {mother_email} for guardian request {request_id}")
                else:
                    print(f"⚠️ Could not find mother user with email {mother_email}")
            
            connection.commit()
            print("✅ Guardian request notifications verified and fixed")
            
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed")

def check_notification_creation_in_app():
    print("\nChecking notification creation code in app...")
    
    # The following path assumes the file is in the main directory
    # Adjust if needed
    try:
        with open('app.py', 'r') as file:
            app_code = file.read()
            
        # Look for notification creation in guardian request code
        if "notification = Notification(" in app_code and "guardian_request" in app_code:
            print("✅ Found notification creation code for guardian requests in app.py")
        else:
            print("⚠️ Could not find notification creation code for guardian requests")
            print("You may need to update the app.py file to create notifications when guardian requests are made")
            
            # Suggest fix based on common pattern
            suggested_code = """
# Add this code in the route that handles guardian requests
notification = Notification(
    user_id=mother.id,
    content=f"{user.full_name} wants to be your guardian",
    notification_type="guardian_request",
    related_id=guardian_request.id
)
db.session.add(notification)
db.session.commit()
"""
            print("\nSuggested code to add:\n" + suggested_code)
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")

if __name__ == "__main__":
    print("Checking and fixing notifications system...")
    fix_notifications_table()
    check_notification_creation_in_app() 