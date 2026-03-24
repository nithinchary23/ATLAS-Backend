import numpy as np

def compute_country_trend(df, country, target_col="Total Victims"):
    country_df = df[df["Country"] == country].sort_values("Year")

    if len(country_df) < 3:
        return 0.0

    values = country_df[target_col].values
    growth_rates = []

    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]

        if prev > 0:
            growth_rates.append((curr - prev) / prev)

    if len(growth_rates) == 0:
        return 0.0

    trend = np.mean(growth_rates)

    # Clamp growth (very important)
    return float(np.clip(trend, -0.3, 0.5))
