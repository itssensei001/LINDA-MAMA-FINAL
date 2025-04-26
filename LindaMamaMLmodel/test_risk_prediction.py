"""
Test script for the risk prediction model

This script tests whether the risk predictor module works with the updated paths.
It imports the predict_risk function and runs a sample prediction.

Usage:
    python test_risk_prediction.py
"""

import os
import sys
import json

# Add the current directory to the path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import the risk predictor
try:
    from risk_predictor import predict_risk
    print(f"✅ Successfully imported the risk_predictor module")
except ImportError as e:
    print(f"❌ Error importing risk_predictor: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Sample input data for testing
sample_input = {
    'Age': 30,
    'Current_Week': 20,
    'Blood_Pressure': 130,
    'Blood_Sugar': 110,
    'Haemoglobin': 11.0,
    'Heart_Rate': 90,
    'Height': 1.65,
    'Weight': 62,
    'Prenatal_Visits': 4,
    'Miscarriage_History': 'No',
    'Smoking_Or_Alcohol': 'No'
}

print("\n🔍 Testing risk prediction with sample data:")
print(json.dumps(sample_input, indent=2))
print("\n⏳ Running prediction...")

try:
    # Run the prediction
    result = predict_risk(sample_input)
    
    # Display the result
    print("\n✅ Prediction successful!")
    print("\n📊 Result:")
    print(json.dumps(result, indent=2))
    
    # Print some additional information
    print(f"\n🔴 Risk Level: {result['risk_level']}")
    print(f"💡 Recommendation: {result['recommendation']}")
    print("\n⚠️ Top Factors:")
    for factor in result['top_factors']:
        print(f"  - {factor['feature']}: {factor['contribution']:.4f}")
    
    print("\n✨ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Error during prediction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 