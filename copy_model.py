"""
Copy Model Files Script

This script helps you copy your trained model files to the correct location
for the Linda Mama application to use.
"""

import os
import shutil
import sys

def get_valid_path(prompt):
    """Get a valid directory path from user input"""
    while True:
        path = input(prompt)
        if os.path.exists(path) and os.path.isdir(path):
            return path
        else:
            print(f"Directory not found: {path}")
            retry = input("Try again? (y/n): ")
            if retry.lower() != 'y':
                return None

def main():
    print("=============================================")
    print("LINDA MAMA MODEL FILE TRANSFER UTILITY")
    print("=============================================")
    print("This utility will help you copy your trained model files")
    print("to the correct location for the Linda Mama application.")
    
    # Find potential destination directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    possible_dest_dirs = [
        os.path.join(current_dir, 'LindaMamaMLmodel'),
        os.path.join(parent_dir, 'LindaMamaMLmodel'),
        'LindaMamaMLmodel'
    ]
    
    # Find a valid destination
    dest_dir = None
    for dir_path in possible_dest_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            dest_dir = dir_path
            break
    
    if not dest_dir:
        print("\n❌ Could not find a valid destination directory.")
        print("Would you like to create a LindaMamaMLmodel directory?")
        create_dir = input("Create directory? (y/n): ")
        
        if create_dir.lower() == 'y':
            dest_dir = os.path.join(current_dir, 'LindaMamaMLmodel')
            os.makedirs(dest_dir, exist_ok=True)
            print(f"✅ Created directory: {dest_dir}")
        else:
            print("Operation cancelled.")
            return
    
    # Get source directory from user
    print("\nPlease enter the directory where your trained model files are located:")
    source_dir = get_valid_path("Source directory: ")
    
    if not source_dir:
        print("Operation cancelled.")
        return
    
    print(f"\nSource directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # List files to copy
    required_files = ['risk_model.pkl', 'synthetic_pregnancy_data.csv']
    files_found = []
    
    for filename in required_files:
        source_path = os.path.join(source_dir, filename)
        if os.path.exists(source_path):
            files_found.append((filename, source_path))
    
    if not files_found:
        print("\n❌ No required model files found in the source directory.")
        print("Files needed: risk_model.pkl, synthetic_pregnancy_data.csv")
        return
    
    print("\nThe following files will be copied:")
    for filename, path in files_found:
        print(f"  - {filename}")
    
    confirm = input("\nContinue with copy? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Copy files
    print("\nCopying files...")
    success = True
    
    for filename, source_path in files_found:
        dest_path = os.path.join(dest_dir, filename)
        try:
            shutil.copy2(source_path, dest_path)
            print(f"✅ Copied {filename}")
        except Exception as e:
            print(f"❌ Error copying {filename}: {e}")
            success = False
    
    if success:
        print("\n✅ All files copied successfully!")
        print("You can now restart your Flask application to use the ML model.")
    else:
        print("\n⚠️ Some files could not be copied. Please check the errors above.")

if __name__ == "__main__":
    main() 