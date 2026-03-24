import joblib
import pandas as pd

MODEL_PATH = "models/victim_forecast_model.pkl"
SCALER_PATH = "models/scaler.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

def predict(X_df):
    """
    X_df: pandas DataFrame with correct feature columns
    """
    X_scaled = scaler.transform(X_df)   # ✅ feature names preserved
    return model.predict(X_scaled)
