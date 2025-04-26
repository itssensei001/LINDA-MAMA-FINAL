import pandas as pd
from preprocessing import preprocess_data

# Load data
df = pd.read_csv("D:/LindaMamaMLmodel/synthetic_pregnancy_data.csv")

# Preprocess
# Updated to unpack 6 returned values
X_scaled, y, le_risk, scaler, le_miscarriage, le_smoking = preprocess_data(df)

# Print info (optional, for verification)
print("✅ Preprocessing complete.")
print("🔢 Feature shape:", X_scaled.shape)
print("🎯 Target distribution:\n", y.value_counts())
print("\n🔍 Sample features (scaled):\n", X_scaled.head())
