import pandas as pd
from sklearn.preprocessing import StandardScaler
from utils.feature_columns import TARGET_COL, DROP_COLS, ID_COLS

def preprocess(df):
    # Drop leakage & non-predictive columns
    df = df.drop(columns=DROP_COLS, errors="ignore")

    # Save identifiers for later use
    meta = df[ID_COLS].copy()

    # Drop identifiers from training
    df = df.drop(columns=ID_COLS, errors="ignore")

    if TARGET_COL not in df.columns:
        raise ValueError("Target column missing")

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # Handle missing values (extra safety)
    X = X.fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, X.columns.tolist(), scaler, meta
