# bridge.py

import os
from flask import Flask, request, jsonify, render_template, abort

# --- Configuration & Initialization ---

# Determine the absolute path to the project directory
# This assumes bridge.py is in the LindaMamaMLmodel directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PROJECT_DIR, 'risk_model.pkl')
DATA_PATH = os.path.join(PROJECT_DIR, 'synthetic_pregnancy_data.csv')

# Print environment info for debugging
print(f"Project directory: {PROJECT_DIR}")
print(f"Model path: {MODEL_PATH}")
print(f"Data path: {DATA_PATH}")

app = Flask(__name__)

# --- Load Predictor Function ---

# Attempt to import the prediction function
try:
    from risk_predictor import predict_risk
    print("✅ Risk predictor function loaded successfully.")
except ImportError as e:
    print(f"❌ Error importing risk_predictor: {e}")
    print("Ensure risk_predictor.py is in the same directory or Python path.")
    predict_risk = None # Set to None if import fails
except Exception as e:
    print(f"❌ An unexpected error occurred during import: {e}")
    predict_risk = None

# --- Routes --- 

# Example route to serve the HTML page (adjust as needed)
@app.route('/')
@app.route('/health_monitoring')
def health_monitoring_page():
    # You might already have a route like this
    # Ensure it serves the correct HTML file
    try:
        return render_template('health_monitoring.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        abort(500, description="Could not render health monitoring page.")

# --- Prediction API Endpoint --- 

@app.route('/predict_risk', methods=['POST'])
def handle_predict_risk():
    # Check if predictor is loaded
    if not predict_risk:
        print("Error: handle_predict_risk called but predict_risk function is not loaded.")
        return jsonify({"error": "Risk predictor module not available"}), 500

    # Check if request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    input_data = request.get_json()
    print(f"Received input data: {input_data}") # Log received data

    # --- Input Validation --- 
    required_keys = [
        'Age', 'Current_Week', 'Height', 'Weight', 'Blood_Pressure',
        'Heart_Rate', 'Blood_Sugar', 'Haemoglobin', 'Prenatal_Visits',
        'Miscarriage_History', 'Smoking_Or_Alcohol'
    ]
    missing_keys = [key for key in required_keys if key not in input_data or input_data[key] is None]
    if missing_keys:
        print(f"Validation Error: Missing keys - {missing_keys}")
        return jsonify({"error": f"Missing required input fields: {', '.join(missing_keys)}"}), 400

    # --- Data Type Conversion & Prediction --- 
    try:
        # Convert numeric fields (handle potential None or empty strings explicitly)
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
            else: # Categorical
                if value is None or value == '':
                     raise ValueError(f"Missing value for categorical field: {key}")
                processed_data[key] = value

        print(f"Processed data for prediction: {processed_data}") # Log processed data
        
        # Call the prediction function with the processed data
        result = predict_risk(processed_data)
        print(f"Prediction result: {result}") # Log result
        
        return jsonify(result)

    except ValueError as e:
        # Handle known errors (e.g., invalid categorical value, missing values after check)
        print(f"ValueError during prediction: {e}")
        return jsonify({"error": f"Prediction error: {str(e)}"}), 400
    except KeyError as e:
        # Handle potential errors if keys are missing unexpectedly in predict_risk (should be caught earlier)
        print(f"KeyError during prediction: {e}")
        return jsonify({"error": f"Internal error: Missing expected data key - {str(e)}"}), 500
    except FileNotFoundError as e:
        # Handle missing model/data files if predict_risk or its imports try to load them again
        print(f"FileNotFoundError during prediction: {e}")
        return jsonify({"error": "Internal error: Required model or data file not found."}), 500
    except Exception as e:
        # Catch-all for other unexpected errors
        print(f"Unexpected error during prediction: {e}") # Log detailed error
        import traceback
        traceback.print_exc() # Print traceback for debugging
        return jsonify({"error": "An unexpected error occurred during analysis."}), 500

# --- Run the App --- 

if __name__ == '__main__':
    # Check if the predictor loaded correctly before running
    if predict_risk is None:
        print("--- Cannot start Flask server: predict_risk function failed to load. ---")
    else:
        print("--- Starting Flask Development Server --- ")
        # Use host='0.0.0.0' to make it accessible on your network
        # Use debug=True for development (auto-reloads, more error details)
        app.run(host='0.0.0.0', port=5000, debug=True) 