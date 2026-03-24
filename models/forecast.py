import math

import pandas as pd

from utils.load_data import load_dataset

_DATASET_PATH = "data/final_ml_dataset_AGGREGATED.csv"
_FORECAST_CACHE = None


def _get_victim_column(df):
    for col in df.columns:
        if col.lower().replace(" ", "") in {
            "victims",
            "totalvictims",
            "victimcount",
            "numberofvictims",
        }:
            return col
    raise ValueError(
        "Victim column not found. Expected something like 'Victims' or 'Total Victims'."
    )


def _validate_required_columns(df, victim_col):
    required = {"Country", "Year", "Latitude", "Longitude", victim_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def _prepare_forecast_frame(df, victim_col):
    working = df.copy()

    working["Country"] = working["Country"].astype(str).str.strip()
    working["Year"] = pd.to_numeric(working["Year"], errors="coerce")
    working["Latitude"] = pd.to_numeric(working["Latitude"], errors="coerce")
    working["Longitude"] = pd.to_numeric(working["Longitude"], errors="coerce")
    working[victim_col] = pd.to_numeric(working[victim_col], errors="coerce")

    working = working.dropna(subset=["Country", "Year", "Latitude", "Longitude", victim_col])
    working = working[working["Country"] != ""]

    if working.empty:
        raise ValueError("No usable rows remain after cleaning the forecast dataset.")

    working["Year"] = working["Year"].astype(int)
    return working


def _holt_forecast(values, steps, alpha, beta, phi=0.9):
    if len(values) == 1:
        return [max(values[0], 0.0)] * steps

    level = float(values[0])
    trend = float(values[1] - values[0])

    for value in values[1:]:
        prev_level = level
        level = alpha * float(value) + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - prev_level) + (1 - beta) * phi * trend

    forecasts = []
    for step in range(1, steps + 1):
        if abs(1 - phi) < 1e-9:
            forecast = level + step * trend
        else:
            damped_multiplier = phi * (1 - phi**step) / (1 - phi)
            forecast = level + damped_multiplier * trend
        forecasts.append(max(forecast, 0.0))
    return forecasts


def _one_step_mae(values, alpha, beta, phi=0.9):
    if len(values) < 3:
        return math.inf

    errors = []
    for end_idx in range(2, len(values)):
        history = values[:end_idx]
        actual = values[end_idx]
        predicted = _holt_forecast(history, 1, alpha, beta, phi=phi)[0]
        errors.append(abs(predicted - actual))

    return sum(errors) / len(errors) if errors else math.inf


def _select_holt_params(values):
    if len(values) < 3:
        return 0.6, 0.2, 0.9

    candidates = [0.2, 0.4, 0.6, 0.8]
    damping = [0.85, 0.9, 0.95, 1.0]
    best = None

    for alpha in candidates:
        for beta in candidates:
            for phi in damping:
                mae = _one_step_mae(values, alpha, beta, phi)
                if best is None or mae < best[0]:
                    best = (mae, alpha, beta, phi)

    return best[1], best[2], best[3]


def _fallback_forecast(values, steps):
    last_value = float(values[-1])
    if len(values) < 2:
        return [max(last_value, 0.0)] * steps

    recent_values = values[-3:]
    deltas = [
        float(recent_values[idx] - recent_values[idx - 1])
        for idx in range(1, len(recent_values))
    ]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

    return [
        max(last_value + (avg_delta * step), 0.0)
        for step in range(1, steps + 1)
    ]


def _forecast_country_series(values, steps):
    if len(values) < 2:
        return [max(float(values[-1]), 0.0)] * steps

    try:
        alpha, beta, phi = _select_holt_params(values)
        return _holt_forecast(values, steps, alpha, beta, phi)
    except Exception:
        return _fallback_forecast(values, steps)


def forecast_future():
    global _FORECAST_CACHE

    if _FORECAST_CACHE is not None:
        return _FORECAST_CACHE

    df = load_dataset(_DATASET_PATH)
    victim_col = _get_victim_column(df)
    _validate_required_columns(df, victim_col)
    df = _prepare_forecast_frame(df, victim_col)

    future_years = [2025, 2026, 2027]
    forecast_steps = len(future_years)
    results = []

    for country, cdf in df.groupby("Country"):
        yearly = (
            cdf.groupby("Year")
            .agg({
                victim_col: "sum",
                "Latitude": "mean",
                "Longitude": "mean",
            })
            .reset_index()
            .sort_values("Year")
        )

        if yearly.empty:
            continue

        values = yearly[victim_col].astype(float).tolist()
        predictions = _forecast_country_series(values, forecast_steps)
        lat = round(float(yearly["Latitude"].iloc[-1]), 4)
        lon = round(float(yearly["Longitude"].iloc[-1]), 4)

        for year, predicted in zip(future_years, predictions):
            results.append({
                "Country": country,
                "Latitude": lat,
                "Longitude": lon,
                "Forecast Year": year,
                "Predicted Victims": int(round(max(predicted, 0.0))),
            })

    final_df = pd.DataFrame(results)
    if final_df.empty:
        raise ValueError("Forecast generation produced no rows.")

    _FORECAST_CACHE = final_df
    return final_df
