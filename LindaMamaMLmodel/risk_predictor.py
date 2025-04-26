'''
RISK PREDICTOR MODULE

This module uses the trained RandomForest model to predict pregnancy risk levels
and provides interpretability via SHAP values.

HOW TO USE:
1. Ensure you have a trained model bundle at the correct path
2. Import the function:
       from risk_predictor import predict_risk
3. Provide input data as a dict:
       input_data = {
           'Age': 28,
           'Current_Week': 24,
           'Blood_Pressure': 125,
           'Blood_Sugar': 100,
           'Haemoglobin': 11.2,
           'Heart_Rate': 85,
           'Height': 1.60,
           'Weight': 65,
           'Prenatal_Visits': 5,
           'Miscarriage_History': 'No',
           'Smoking_Or_Alcohol': 'No'
       }
4. Call prediction:
       result = predict_risk(input_data)
5. Result dict contains:
       {
           'risk_level': 'Medium',
           'top_factors': [
               {'feature': 'Systolic_BP', 'contribution': 0.45},
               ...
           ],
           'recommendation': '...'
       }
'''

import os
import joblib
import pandas as pd
import shap
import numpy as np

# Determine path to model bundle - use relative path from script location
current_dir = os.path.dirname(os.path.abspath(__file__))
default_bundle_path = os.path.join(current_dir, 'risk_model.pkl')
# Allow overriding via environment variable
bundle_path = os.environ.get('RISK_MODEL_PATH', default_bundle_path)

if not os.path.exists(bundle_path):
    raise FileNotFoundError(f"Model bundle not found at {bundle_path}")

model_bundle = joblib.load(bundle_path)
model = model_bundle['model']
le_risk = model_bundle['le_risk']
scaler = model_bundle['scaler']
# Load the feature encoders
le_miscarriage = model_bundle['le_miscarriage']
le_smoking = model_bundle['le_smoking']

# Prepare SHAP explainer with a small background sample
from preprocessing import preprocess_data
data_path = os.path.join(current_dir, 'synthetic_pregnancy_data.csv')
if not os.path.exists(data_path):
    raise FileNotFoundError(f"Dataset not found at {data_path}")

df_bg = pd.read_csv(data_path)
X_bg, _, _, _, _, _ = preprocess_data(df_bg)  # Adjust unpacking for new return values
background = X_bg.sample(n=100, random_state=42)
explainer = shap.TreeExplainer(model, background)


def predict_risk(input_data):
    """
    Predicts risk level and explains prediction with top SHAP feature contributions.

    Args:
        input_data (dict): Raw input with keys matching feature names.

    Returns:
        dict: {
            'risk_level': str,
            'top_factors': list of {'feature': str, 'contribution': float},
            'recommendation': str
        }
    """
    # Convert input dict to DataFrame (single row)
    df_input = pd.DataFrame([input_data])

    # Compute BMI - Ensure Height and Weight are present
    if 'Height' in df_input.columns and 'Weight' in df_input.columns:
        df_input['BMI'] = round(df_input['Weight'] / (df_input['Height'] ** 2), 1)
    else:
        raise ValueError("Input data must contain 'Height' and 'Weight' to calculate BMI.")

    # Use loaded encoders for categorical features
    if 'Miscarriage_History' in df_input.columns:
        df_input['Miscarriage_History_Enc'] = le_miscarriage.transform(df_input['Miscarriage_History'])
    else:
        raise ValueError("Input data missing 'Miscarriage_History'.")

    if 'Smoking_Or_Alcohol' in df_input.columns:
        df_input['Smoking_Or_Alcohol_Enc'] = le_smoking.transform(df_input['Smoking_Or_Alcohol'])
    else:
        raise ValueError("Input data missing 'Smoking_Or_Alcohol'.")

    # Get feature names in the order the scaler expects
    model_features = scaler.feature_names_in_
    missing_features = set(model_features) - set(df_input.columns)
    if missing_features:
        raise ValueError(f"Input data missing required features: {missing_features}")

    # Select and order features for scaling
    X_raw = df_input[model_features]
    X_scaled_np = scaler.transform(X_raw)
    X_scaled = pd.DataFrame(X_scaled_np, columns=model_features)

    # Predict
    pred_enc = model.predict(X_scaled)[0]
    risk_label = le_risk.inverse_transform([pred_enc])[0]

    # SHAP value computation
    shap_values = explainer.shap_values(X_scaled)
    if isinstance(shap_values, list):
        shap_for_class = shap_values[pred_enc][0]
    else:
        shap_for_class = shap_values[0]

    # Flatten SHAP values
    shap_for_class = np.array(shap_for_class).flatten()

    # Pair features with SHAP contributions
    contribs = [
        {'feature': feat, 'contribution': float(val)}
        for feat, val in zip(model_features, shap_for_class)
    ]
    top_factors = sorted(contribs, key=lambda x: abs(x['contribution']), reverse=True)[:3]

    # Recommendation logic
    if risk_label == 'High':
        recommendation = 'Please contact your nearest doctor immediately.'
    elif risk_label == 'Medium':
        recommendation = 'Consider increasing check-ups, follow tailored nutrition, and monitor vitals closely.'
    else:
        recommendation = 'Maintain your current routine: balanced diet, regular exercise, and attend scheduled visits.'

    return {
        'risk_level': risk_label,
        'top_factors': top_factors,
        'recommendation': recommendation
    }


if __name__ == '__main__':
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
    result = predict_risk(sample_input)
    print("Result:\n", result)
