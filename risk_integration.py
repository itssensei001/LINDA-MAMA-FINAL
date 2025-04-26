"""
Risk Integration Module

This module serves as a bridge between the main Flask application (app.py)
and the ML risk prediction model (risk_predictor.py).

It handles validation, error handling, and formatting of predictions.
"""

import os
import sys
import json
import traceback
from typing import Tuple, Dict, Any, Union

# Dynamically determine model directory path - check multiple possible locations
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
POSSIBLE_MODEL_DIRS = [
    os.path.join(CURRENT_DIR, 'LindaMamaMLmodel'),  # If model is in app dir
    os.path.join(PARENT_DIR, 'LindaMamaMLmodel'),   # If model is in parent dir
    'LindaMamaMLmodel',                            # Relative to current dir
    'D:/Projectwork/LINDA-MAMA-FINAL/LindaMamaMLmodel'  # Explicit path to the model directory
]

# Try to find the model directory
MODEL_DIR = None
for dir_path in POSSIBLE_MODEL_DIRS:
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        MODEL_DIR = dir_path
        print(f"✅ Found ML model directory at: {MODEL_DIR}")
        if MODEL_DIR not in sys.path:
            sys.path.insert(0, MODEL_DIR)
        break
else:
    print("❌ Could not find ML model directory. Checked paths:")
    for path in POSSIBLE_MODEL_DIRS:
        print(f"  - {path}")

# Import predict_risk function
predict_risk = None
try:
    from risk_predictor import predict_risk
    print("✅ Risk predictor loaded successfully in integration module.")
except ImportError as e:
    print(f"❌ Error importing risk_predictor in integration module: {e}")
    print(f"Looking in: {MODEL_DIR}")
except Exception as e:
    print(f"❌ Unexpected error loading risk_predictor: {e}")
    traceback.print_exc()

# Create a mock prediction function to use if the real one isn't available
def mock_predict_risk(input_data):
    """Mock version of predict_risk that returns fake data when the real model isn't available"""
    print("⚠️ Using mock prediction function - real model not available")
    # Calculate a simple risk level based on age and blood pressure
    age = float(input_data.get('Age', 30))
    bp = float(input_data.get('Blood_Pressure', 120))
    
    # Simple rule-based risk assessment
    if age > 35 and bp > 140:
        risk_level = "High"
    elif age > 30 or bp > 130:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    # Generate mock top factors
    top_factors = [
        {"feature": "Age", "contribution": 0.4 if age > 30 else 0.2},
        {"feature": "Blood_Pressure", "contribution": 0.5 if bp > 130 else 0.3},
        {"feature": "Blood_Sugar", "contribution": 0.3}
    ]
    
    # Recommendation based on risk level
    if risk_level == "High":
        recommendation = "Please contact your nearest doctor immediately."
    elif risk_level == "Medium":
        recommendation = "Consider increasing check-ups, follow tailored nutrition, and monitor vitals closely."
    else:
        recommendation = "Maintain your current routine: balanced diet, regular exercise, and attend scheduled visits."
    
    return {
        "risk_level": risk_level,
        "top_factors": top_factors,
        "recommendation": recommendation
    }

def process_risk_prediction(input_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Process risk prediction request, handle validation and errors
    
    Args:
        input_data: The input data from the request
        
    Returns:
        Tuple of (result dict, HTTP status code)
    """
    # Check if predictor is available
    if not predict_risk:
        error_msg = "ML model not loaded. Please ensure risk_model.pkl exists in LindaMamaMLmodel directory."
        print(f"Error: {error_msg}")
        return {"error": error_msg}, 503
    
    # Validate required fields
    required_fields = [
        'Age', 'Current_Week', 'Height', 'Weight', 'Blood_Pressure',
        'Heart_Rate', 'Blood_Sugar', 'Haemoglobin', 'Prenatal_Visits',
        'Miscarriage_History', 'Smoking_Or_Alcohol'
    ]
    
    missing_fields = [field for field in required_fields if field not in input_data]
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        print(f"Validation error: {error_msg}")
        return {"error": error_msg}, 400
    
    # Validate data types
    try:
        # Convert numeric values
        validated_data = {
            'Age': float(input_data['Age']),
            'Current_Week': int(input_data['Current_Week']),
            'Height': float(input_data['Height']),
            'Weight': float(input_data['Weight']),
            'Blood_Pressure': float(input_data['Blood_Pressure']),
            'Heart_Rate': float(input_data['Heart_Rate']),
            'Blood_Sugar': float(input_data['Blood_Sugar']),
            'Haemoglobin': float(input_data['Haemoglobin']),
            'Prenatal_Visits': int(input_data['Prenatal_Visits']),
            'Miscarriage_History': input_data['Miscarriage_History'],
            'Smoking_Or_Alcohol': input_data['Smoking_Or_Alcohol']
        }
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid data format: {str(e)}"
        print(f"Validation error: {error_msg}")
        return {"error": error_msg}, 400
    
    # Call the prediction function
    try:
        result = predict_risk(validated_data)
        return result, 200
    except ValueError as e:
        error_msg = f"Prediction error: {str(e)}"
        print(f"ValueError in prediction: {error_msg}")
        return {"error": error_msg}, 400
    except Exception as e:
        error_msg = f"Unexpected error during prediction: {str(e)}"
        print(f"Exception in prediction: {error_msg}")
        traceback.print_exc()
        return {"error": error_msg}, 500

# For testing only
if __name__ == "__main__":
    # Test the integration
    test_data = {
        'Age': 30,
        'Current_Week': 20,
        'Height': 1.65,
        'Weight': 68,
        'Blood_Pressure': 120,
        'Heart_Rate': 80,
        'Blood_Sugar': 95,
        'Haemoglobin': 12.5,
        'Prenatal_Visits': 5,
        'Miscarriage_History': 'No',
        'Smoking_Or_Alcohol': 'No'
    }
    
    result, status_code = process_risk_prediction(test_data)
    print(f"Status: {status_code}")
    print(json.dumps(result, indent=2)) 