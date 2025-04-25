"""
Database Reset Script

This script recreates all database tables with the updated schemas.
USE WITH CAUTION: This will delete all existing data!
"""

from app import app, db
import time

if __name__ == "__main__":
    with app.app_context():
        print("WARNING: This will delete all data in the database.")
        print("Are you sure you want to continue? (yes/no)")
        confirm = input().lower()
        
        if confirm == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            time.sleep(1)  # Give a moment for the operation to complete
            
            print("Creating tables with new schema...")
            db.create_all()
            
            print("Database has been reset successfully!")
        else:
            print("Operation cancelled.") 