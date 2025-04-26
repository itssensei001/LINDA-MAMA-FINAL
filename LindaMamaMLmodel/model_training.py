'''
MODEL TRAINING MODULE

This module handles model training using RandomForestClassifier.
It includes performance output and saves the trained model, encoder, and scaler for future use.

HOW TO USE:
1. Import training function:
       from model_training import train_model
2. Prepare preprocessed data:
       df = pd.read_csv("D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv")
       from preprocessing import preprocess_data
       X_scaled, y, le_risk, scaler = preprocess_data(df)
3. Train model programmatically:
       model, le_risk, scaler = train_model(X_scaled, y, le_risk, scaler,
                                           model_path='D:/LindaMamaMLmodel/risk_model.pkl')
4. Or run this script directly to train using existing CSV and save outputs:
       python model_training.py

RETURNS:
- model   : Trained RandomForestClassifier
- le_risk : LabelEncoder used for Risk_Level
- scaler  : StandardScaler used for input features
'''

import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder, StandardScaler
from preprocessing import preprocess_data


def train_model(X, y, le_risk, scaler, le_miscarriage, le_smoking, model_path='D:/LindaMamaMLmodel/risk_model.pkl'):
    """
    Train a RandomForestClassifier on preprocessed data.
    Saves the model, encoder, and scaler as a joblib dictionary.

    Args:
        X (pd.DataFrame): Scaled input features
        y (pd.Series): Encoded target labels
        le_risk (LabelEncoder): Fitted encoder for Risk_Level
        scaler (StandardScaler): Fitted scaler for input features
        le_miscarriage (LabelEncoder): Fitted encoder for Miscarriage_History
        le_smoking (LabelEncoder): Fitted encoder for Smoking_Or_Alcohol
        model_path (str): Path to save the trained model

    Returns:
        model (RandomForestClassifier): Trained model
        le_risk (LabelEncoder): Label encoder for decoding predictions
        scaler (StandardScaler): Feature scaler for transforming inputs
        le_miscarriage (LabelEncoder): Encoder for Miscarriage_History
        le_smoking (LabelEncoder): Encoder for Smoking_Or_Alcohol
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize model
    model = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42, class_weight='balanced')

    # Train model
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print("\n✅ Model Training Complete")
    print(f"🎯 Accuracy: {acc * 100:.2f}%")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le_risk.classes_, zero_division=0))

    # Re-added Feature Importance Calculation
    importances = model.feature_importances_
    # Ensure X_train has column names (assuming X passed to function is a DataFrame)
    if isinstance(X, pd.DataFrame):
        feature_names = X.columns
    else:
        # Create generic feature names if X is not a DataFrame (e.g., NumPy array)
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
    feature_importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
    print("\n📊 Feature Importances:")
    print(feature_importance_df)

    # Ensure directory exists
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    # Save everything as a bundle, including feature encoders
    model_bundle = {
        'model': model,
        'le_risk': le_risk,
        'scaler': scaler,
        'le_miscarriage': le_miscarriage,
        'le_smoking': le_smoking
    }
    joblib.dump(model_bundle, model_path)
    print(f"💾 Model saved to: {model_path}")

    return model, le_risk, scaler, le_miscarriage, le_smoking


if __name__ == '__main__':
    # Auto-run: load data, preprocess, train, save
    print("📥 Loading synthetic dataset...")
    df = pd.read_csv("D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv")
    print("🧹 Preprocessing data...")
    X_scaled, y, le_risk, scaler, le_miscarriage, le_smoking = preprocess_data(df)
    print("🚀 Training model...")
    train_model(X_scaled, y, le_risk, scaler, le_miscarriage, le_smoking)
