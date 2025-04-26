"""
Model Files Diagnostic Script

This script checks if the required ML model files exist and prints diagnostic information.
"""

import os
import sys

# Directories to check
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
POSSIBLE_MODEL_DIRS = [
    os.path.join(CURRENT_DIR, 'LindaMamaMLmodel'),  # If model is in app dir
    os.path.join(PARENT_DIR, 'LindaMamaMLmodel'),   # If model is in parent dir
    'LindaMamaMLmodel'                             # Relative to current dir
]

# Required files
REQUIRED_FILES = [
    'risk_model.pkl',
    'synthetic_pregnancy_data.csv'
]

print("============================================")
print("LINDA MAMA ML MODEL DIAGNOSTIC INFORMATION")
print("============================================")
print(f"Current working directory: {os.getcwd()}")
print("Looking for model files in the following directories:")

found_model_dir = None
found_files = {}

for dir_path in POSSIBLE_MODEL_DIRS:
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"\n✅ Directory found: {dir_path}")
        found_model_dir = dir_path
        
        # Check for required files
        for file_name in REQUIRED_FILES:
            file_path = os.path.join(dir_path, file_name)
            exists = os.path.exists(file_path)
            found_files[file_name] = exists
            
            if exists:
                size = os.path.getsize(file_path) / 1024  # in KB
                print(f"  ✅ {file_name} - Found ({size:.2f} KB)")
            else:
                print(f"  ❌ {file_name} - Not found")
    else:
        print(f"\n❌ Directory not found: {dir_path}")

print("\n============================================")
print("SUMMARY")
print("============================================")

if found_model_dir:
    print(f"Model directory found: {found_model_dir}")
    
    all_files_found = all(found_files.values())
    if all_files_found:
        print("✅ All required model files found!")
    else:
        print("❌ Some required files are missing:")
        for file_name, found in found_files.items():
            if not found:
                print(f"  - {file_name}")
                
        print("\nPlease make sure the missing files are placed in the model directory.")
        print("These files are needed for the ML model to work correctly.")
else:
    print("❌ Model directory not found!")
    print("Please make sure the LindaMamaMLmodel directory exists in one of these locations:")
    for dir_path in POSSIBLE_MODEL_DIRS:
        print(f"  - {dir_path}")

print("\n============================================")
print("INSTRUCTIONS")
print("============================================")
print("To fix the ML model integration:")
print("1. Make sure the ML model directory exists")
print("2. Ensure risk_model.pkl and synthetic_pregnancy_data.csv are in the model directory")
print("3. If you've trained your model in a different location, copy it to: " + 
      (found_model_dir if found_model_dir else "LindaMamaMLmodel directory"))
print("4. Check that all Python dependencies are installed (scikit-learn, pandas, numpy, shap)")
print("5. Restart the Flask application")
print("============================================") 