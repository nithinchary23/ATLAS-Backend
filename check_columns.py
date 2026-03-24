# check_columns.py
import pandas as pd

path = r"C:\Users\Niharika Ramojipally\Desktop\master\final_ml_dataset_cleaned.csv"
df = pd.read_csv(path)

print("TOTAL COLUMNS:", len(df.columns))
print("\nCOLUMN NAMES:\n")
for c in df.columns:
    print(c)
