import pandas as pd
import numpy as np

def assign_risk_levels(df, value_col="Predicted Victims"):
    """
    Assigns Low / Medium / High risk based on percentiles
    """
    if df.empty:
        return df

    p30 = np.percentile(df[value_col], 30)
    p80 = np.percentile(df[value_col], 80)

    def risk_label(x):
        if x >= p80:
            return "High"
        elif x >= p30:
            return "Medium"
        else:
            return "Low"

    df = df.copy()
    df["Risk_Level"] = df[value_col].apply(risk_label)

    return df
