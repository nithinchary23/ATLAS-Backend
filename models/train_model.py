import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import sys
import os

from utils.load_data import load_dataset
from utils.preprocess import preprocess

DATA_PATH = "data/final_ml_dataset_AGGREGATED.csv"
MODEL_PATH = "models/victim_forecast_model.pkl"
SCALER_PATH = "models/scaler.pkl"

def train():
    print("📥 Loading dataset...")
    df = load_dataset(DATA_PATH)

    print("🔄 Preprocessing...")
    X, y, feature_cols, scaler, _ = preprocess(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("🧠 Training model...")
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("📊 Evaluation")
    print("MAE:", mean_absolute_error(y_test, preds))
    print("R²:", r2_score(y_test, preds))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("✅ Model & scaler saved successfully")
    
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    train()
