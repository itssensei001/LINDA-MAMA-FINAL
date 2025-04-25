"""
Risk Prediction Integration Module

This module integrates the risk prediction model from LindaMamaMLmodel
with the main Linda Mama Flask application.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure paths
# Adjust this path to point to your LindaMamaMLmodel directory
ML_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'LindaMamaMLmodel')

# Add ML model directory to path so we can import from it
if ML_MODEL_DIR not in sys.path:
    sys.path.insert(0, ML_MODEL_DIR)

# Try to import the predict_risk function
try:
    from risk_predictor import predict_risk
    logger.info("✅ Risk predictor function loaded successfully.")
    PREDICTOR_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Error importing risk_predictor: {e}")
    logger.error("Ensure risk_predictor.py is available in the LindaMamaMLmodel directory.")
    PREDICTOR_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ An unexpected error during import: {e}")
    PREDICTOR_AVAILABLE = False

def process_risk_prediction(input_data):
    """
    Process risk prediction request using the loaded ML model.
    
    Args:
        input_data (dict): Input data from the user's form
        
    Returns:
        dict: Prediction result or error message
    """
    if not PREDICTOR_AVAILABLE:
        return {"error": "Risk prediction service is currently unavailable"}, 503
    
    # Required input fields for the model
    required_keys = [
        'Age', 'Current_Week', 'Height', 'Weight', 'Blood_Pressure',
        'Heart_Rate', 'Blood_Sugar', 'Haemoglobin', 'Prenatal_Visits',
        'Miscarriage_History', 'Smoking_Or_Alcohol'
    ]
    
    # Check for missing required fields
    missing_keys = [key for key in required_keys if key not in input_data or input_data[key] is None]
    if missing_keys:
        return {"error": f"Missing required input fields: {', '.join(missing_keys)}"}, 400
    
    try:
        # Process and convert data types
        numeric_keys = ['Age', 'Height', 'Weight', 'Blood_Pressure', 'Heart_Rate', 'Blood_Sugar', 'Haemoglobin']
        integer_keys = ['Current_Week', 'Prenatal_Visits']
        
        processed_data = {}
        for key in required_keys:
            value = input_data[key]
            if key in numeric_keys:
                if value is None or value == '': 
                    raise ValueError(f"Missing value for numeric field: {key}")
                processed_data[key] = float(value)
            elif key in integer_keys:
                if value is None or value == '': 
                    raise ValueError(f"Missing value for integer field: {key}")
                processed_data[key] = int(value)
            else:  # Categorical fields
                if value is None or value == '':
                    raise ValueError(f"Missing value for categorical field: {key}")
                processed_data[key] = value
        
        # Call the prediction function
        logger.info(f"Making prediction with data: {processed_data}")
        result = predict_risk(processed_data)
        logger.info(f"Prediction result: {result}")
        
        return result, 200
        
    except ValueError as e:
        logger.error(f"ValueError during prediction: {e}")
        return {"error": f"Prediction error: {str(e)}"}, 400
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "An unexpected error occurred during analysis."}, 500 