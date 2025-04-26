"""
Test script for the risk prediction endpoint

This script creates a minimal Flask app that tests the risk prediction functionality
to verify that the endpoint works correctly.

Usage:
    python test_risk_endpoint.py
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the ML model
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
POSSIBLE_MODEL_DIRS = [
    os.path.join(CURRENT_DIR, 'LindaMamaMLmodel'),  # If model is in app dir
    os.path.join(PARENT_DIR, 'LindaMamaMLmodel'),   # If model is in parent dir
    'LindaMamaMLmodel'                             # Relative to current dir
]

# Try to find the model directory
MODEL_DIR = None
for dir_path in POSSIBLE_MODEL_DIRS:
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        MODEL_DIR = dir_path
        logger.info(f"✅ Found ML model directory at: {MODEL_DIR}")
        if MODEL_DIR not in sys.path:
            sys.path.insert(0, MODEL_DIR)
        break

if MODEL_DIR is None:
    logger.error("❌ Could not find ML model directory. Checked paths:")
    for path in POSSIBLE_MODEL_DIRS:
        logger.error(f"  - {path}")
    sys.exit(1)

# Try to import the risk predictor
try:
    from risk_predictor import predict_risk
    logger.info("✅ Successfully imported the risk_predictor module")
except Exception as e:
    logger.error(f"❌ Error importing risk_predictor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create a minimal Flask app
app = Flask(__name__)

@app.route('/test_predict', methods=['POST'])
def test_predict():
    """Test endpoint for risk prediction"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    try:
        input_data = request.get_json()
        logger.info(f"Received prediction request with data: {input_data}")
        
        # Call the prediction function directly
        result = predict_risk(input_data)
        logger.info(f"Prediction result: {result}")
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Simple HTML form for testing the prediction endpoint"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Risk Prediction Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input, select { width: 100%; padding: 8px; box-sizing: border-box; }
            button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
            #result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
            .error { background-color: #ffebee; color: #c62828; }
            .success { background-color: #e8f5e9; color: #2e7d32; }
        </style>
    </head>
    <body>
        <h1>Risk Prediction Test</h1>
        <div class="form-group">
            <label for="age">Age:</label>
            <input type="number" id="age" value="30">
        </div>
        <div class="form-group">
            <label for="current-week">Current Week:</label>
            <input type="number" id="current-week" value="20">
        </div>
        <div class="form-group">
            <label for="height">Height (m):</label>
            <input type="number" id="height" value="1.65" step="0.01">
        </div>
        <div class="form-group">
            <label for="weight">Weight (kg):</label>
            <input type="number" id="weight" value="65">
        </div>
        <div class="form-group">
            <label for="bp">Blood Pressure (systolic):</label>
            <input type="number" id="bp" value="120">
        </div>
        <div class="form-group">
            <label for="hr">Heart Rate:</label>
            <input type="number" id="hr" value="80">
        </div>
        <div class="form-group">
            <label for="bs">Blood Sugar:</label>
            <input type="number" id="bs" value="100">
        </div>
        <div class="form-group">
            <label for="hb">Haemoglobin:</label>
            <input type="number" id="hb" value="12">
        </div>
        <div class="form-group">
            <label for="prenatal">Prenatal Visits:</label>
            <input type="number" id="prenatal" value="4">
        </div>
        <div class="form-group">
            <label for="miscarriage">Miscarriage History:</label>
            <select id="miscarriage">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
            </select>
        </div>
        <div class="form-group">
            <label for="smoking">Smoking or Alcohol:</label>
            <select id="smoking">
                <option value="No">No</option>
                <option value="Yes">Yes</option>
            </select>
        </div>
        <button id="predict-btn">Predict Risk</button>
        <div id="result"></div>

        <script>
            document.getElementById('predict-btn').addEventListener('click', async () => {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = 'Processing...';
                resultDiv.className = '';
                
                const data = {
                    Age: parseFloat(document.getElementById('age').value),
                    Current_Week: parseInt(document.getElementById('current-week').value),
                    Height: parseFloat(document.getElementById('height').value),
                    Weight: parseFloat(document.getElementById('weight').value),
                    Blood_Pressure: parseFloat(document.getElementById('bp').value),
                    Heart_Rate: parseFloat(document.getElementById('hr').value),
                    Blood_Sugar: parseFloat(document.getElementById('bs').value),
                    Haemoglobin: parseFloat(document.getElementById('hb').value),
                    Prenatal_Visits: parseInt(document.getElementById('prenatal').value),
                    Miscarriage_History: document.getElementById('miscarriage').value,
                    Smoking_Or_Alcohol: document.getElementById('smoking').value
                };
                
                try {
                    const response = await fetch('/test_predict', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || `Server error: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    resultDiv.innerHTML = `
                        <h3>Risk Level: ${result.risk_level}</h3>
                        <p>${result.recommendation}</p>
                        <h4>Top Factors:</h4>
                        <ul>
                            ${result.top_factors.map(f => `<li>${f.feature}: ${f.contribution.toFixed(4)}</li>`).join('')}
                        </ul>
                    `;
                    resultDiv.className = 'success';
                } catch (error) {
                    resultDiv.innerHTML = `<p>Error: ${error.message}</p>`;
                    resultDiv.className = 'error';
                    console.error('Error:', error);
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    logger.info("Starting test server on http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True) 