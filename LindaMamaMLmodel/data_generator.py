'''
DATA GENERATOR MODULE

This module provides utilities to generate synthetic pregnancy data that closely mimics real-world datasets (e.g., MIMIC-III, PRAMS).

HOW TO USE:
1. Import the function:
       from data_generator import generate_pregnancy_data
2. Call it to generate data:
       df = generate_pregnancy_data(n_samples=3000)

This version always saves to CSV automatically in:
       D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv

FUNCTIONS:
- generate_pregnancy_data(n_samples, csv_path)
    • n_samples : Number of records to generate (default=3000).
    • csv_path  : Path to save the generated CSV (default is 'D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv')
''' 
import numpy as np
import pandas as pd
import os


def generate_pregnancy_data(n_samples=3000, csv_path="D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv"):
    """
    Generate synthetic pregnancy records with realistic distributions.
    Automatically saves the data to the given csv_path.

    Returns:
        pandas.DataFrame: A DataFrame containing features and a risk label.
    """
    np.random.seed(42)

    # Demographics & Gestational Week
    age = np.random.normal(loc=29, scale=5, size=n_samples).clip(18, 45).round()
    current_week = np.random.randint(1, 41, size=n_samples)

    # Vitals & Labs
    blood_pressure = np.random.normal(loc=118, scale=15, size=n_samples).clip(90, 160).round()
    blood_sugar = np.random.normal(loc=95, scale=20, size=n_samples).clip(70, 160).round()
    haemoglobin = np.random.normal(loc=11.5, scale=1.5, size=n_samples).clip(8, 15).round(1)
    heart_rate = np.random.normal(loc=75, scale=10, size=n_samples).clip(60, 100).round()

    # Anthropometry
    height = np.random.normal(loc=1.62, scale=0.07, size=n_samples).clip(1.45, 1.80).round(2)
    # Weight increases ~0.3 kg per week + natural variation
    weight = (60 + current_week * 0.3) + np.random.normal(loc=0, scale=5, size=n_samples)
    weight = weight.clip(45, 100).round(1)
    bmi = (weight / (height ** 2)).round(1)

    # Prenatal care & History
    # Expect ~1 visit per 4 weeks
    expected_visits = (current_week / 4)
    prenatal_visits = np.random.poisson(lam=expected_visits).clip(0, current_week)
    miscarriage_history = np.random.choice(['Yes', 'No'], size=n_samples, p=[0.15, 0.85])
    smoking_or_alcohol = np.random.choice(['Yes', 'No'], size=n_samples, p=[0.10, 0.90])

    # Risk scoring - Vectorized approach
    risk_score = np.zeros(n_samples)

    # High blood pressure
    risk_score += (blood_pressure > 140).astype(int)
    # High blood sugar
    risk_score += (blood_sugar > 130).astype(int)
    # Low haemoglobin
    risk_score += (haemoglobin < 10).astype(int)
    # Abnormal BMI
    risk_score += ((bmi < 18.5) | (bmi > 30)).astype(int)
    # Elevated heart rate
    risk_score += (heart_rate > 100).astype(int)
    # Fewer visits than expected
    risk_score += (prenatal_visits < expected_visits / 2).astype(int)
    # History flags
    risk_score += (miscarriage_history == 'Yes').astype(int)
    risk_score += (smoking_or_alcohol == 'Yes').astype(int)

    # Assign risk label using numpy.select for efficiency
    conditions = [
        risk_score <= 1,
        risk_score <= 3,
        risk_score > 3
    ]
    choices = ['Low', 'Medium', 'High']
    risk_level = np.select(conditions, choices, default='Unknown') # default shouldn't be hit

    # Assemble DataFrame
    df = pd.DataFrame({
        'Age': age,
        'Current_Week': current_week,
        'Blood_Pressure': blood_pressure,
        'Blood_Sugar': blood_sugar,
        'Haemoglobin': haemoglobin,
        'Heart_Rate': heart_rate,
        'Height': height,
        'Weight': weight,
        'BMI': bmi,
        'Prenatal_Visits': prenatal_visits,
        'Miscarriage_History': miscarriage_history,
        'Smoking_Or_Alcohol': smoking_or_alcohol,
        'Risk_Level': risk_level
    })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print("✅ Dataset generated and saved as:", csv_path)

    return df


if __name__ == "__main__":
    generate_pregnancy_data()
