'''
PREPROCESSING MODULE

This module prepares the synthetic pregnancy dataset for machine learning.
It handles label encoding for categorical values and scales numeric features.

HOW TO USE:
1. Import the function:
       from preprocessing import preprocess_data
2. Load your dataset:
       import os
       current_dir = os.path.dirname(os.path.abspath(__file__))
       data_path = os.path.join(current_dir, 'synthetic_pregnancy_data.csv')
       df = pd.read_csv(data_path)
3. Preprocess:
       X_scaled, y, le_risk, scaler = preprocess_data(df)

RETURNS:
- X_scaled : Scaled feature matrix (pandas DataFrame)
- y        : Encoded labels for risk level (pandas Series)
- le_risk  : LabelEncoder fitted to risk levels
- scaler   : StandardScaler fitted to the feature set
'''

import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def preprocess_data(df):
    """
    Preprocess the pregnancy dataset: encode labels and scale features.

    Args:
        df (pandas.DataFrame): Raw dataset with columns from synthetic generation.

    Returns:
        X_scaled (pd.DataFrame): Scaled features
        y (pd.Series): Encoded target labels
        le_risk (LabelEncoder): Fitted encoder for target
        scaler (StandardScaler): Fitted scaler for features
    """

    # Label encode categorical features
    le_miscarriage = LabelEncoder()
    le_smoking = LabelEncoder()
    le_risk = LabelEncoder()

    df['Miscarriage_History_Enc'] = le_miscarriage.fit_transform(df['Miscarriage_History'])
    df['Smoking_Or_Alcohol_Enc'] = le_smoking.fit_transform(df['Smoking_Or_Alcohol'])
    df['Risk_Level_Enc'] = le_risk.fit_transform(df['Risk_Level'])

    # Define features for model training
    features = [
        'Age', 'Current_Week', 'Blood_Pressure', 'Blood_Sugar', 'Haemoglobin', 'Heart_Rate',
        'Height', 'Weight', 'BMI', 'Prenatal_Visits',
        'Miscarriage_History_Enc', 'Smoking_Or_Alcohol_Enc'
    ]

    X = df[features]
    y = df['Risk_Level_Enc']

    # Scale features
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=features)

    # Return all fitted transformers
    return X_scaled, y, le_risk, scaler, le_miscarriage, le_smoking
