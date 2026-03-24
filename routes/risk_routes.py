from flask import Blueprint, jsonify, request

from models.forecast import forecast_future
from utils.load_data import load_dataset

risk_bp = Blueprint("risk", __name__)


def get_year_column(df):
    if "Year" in df.columns:
        return "Year"
    if "Forecast Year" in df.columns:
        return "Forecast Year"
    raise ValueError("No year column found in forecast data")


def get_victim_column(df):
    possible_cols = [
        "Victims",
        "Total Victims",
        "Trafficked Victims",
        "Victim_Count",
        "Victims_Total",
        "Detected Victims"
    ]
    for col in possible_cols:
        if col in df.columns:
            return col
    raise ValueError("No historical victim column found")


def normalize_country_name(value):
    return str(value).strip().casefold()


def _error(message, status=400, code="bad_request"):
    return jsonify({"error": {"code": code, "message": message}}), status


@risk_bp.route("/risk/top10", methods=["GET"])
def top10_risk_countries():
    try:
        df = forecast_future()
        if df is None or df.empty:
            return jsonify([])

        year_col = get_year_column(df)
        latest_year = df[year_col].max()
        latest_df = df[df[year_col] == latest_year]

        result = (
            latest_df
            .groupby("Country")["Predicted Victims"]
            .sum()
            .reset_index()
            .sort_values("Predicted Victims", ascending=False)
            .head(10)
        )

        result["Predicted Victims"] = result["Predicted Victims"].round().astype(int)
        return jsonify(result.to_dict(orient="records"))
    except Exception as exc:
        return _error(f"Unable to load top risk countries: {exc}", 500, "risk_top10_failed")


@risk_bp.route("/risk/history", methods=["GET"])
def historical_risk():
    try:
        df = load_dataset("data/final_ml_dataset_AGGREGATED.csv")
        if df is None or df.empty:
            return jsonify([])

        victim_col = get_victim_column(df)

        result = (
            df.groupby("Country")
            .agg({
                victim_col: "sum",
                "Latitude": "mean",
                "Longitude": "mean"
            })
            .reset_index()
            .rename(columns={victim_col: "Victims"})
            .sort_values("Victims", ascending=False)
        )

        result["Victims"] = result["Victims"].round().astype(int)
        result["Latitude"] = result["Latitude"].round(4)
        result["Longitude"] = result["Longitude"].round(4)
        return jsonify(result.to_dict(orient="records"))
    except Exception as exc:
        return _error(f"Unable to load historical risk: {exc}", 500, "risk_history_failed")


@risk_bp.route("/risk/summary", methods=["GET"])
def country_risk_summary():
    country = request.args.get("country")
    if not country:
        return _error("country query parameter required", 400, "missing_country")

    try:
        forecast_df = forecast_future()
        hist_df = load_dataset("data/final_ml_dataset_AGGREGATED.csv")
        country_key = normalize_country_name(country)

        future_victims = 0
        forecast_year = None
        if forecast_df is not None and not forecast_df.empty:
            year_col = get_year_column(forecast_df)
            future_country = forecast_df[
                forecast_df["Country"].astype(str).str.strip().str.casefold() == country_key
            ]
            if not future_country.empty:
                forecast_year = int(future_country[year_col].max())
                future_victims = future_country[
                    future_country[year_col] == forecast_year
                ]["Predicted Victims"].sum()

        past_victims = 0
        latest_historical_year = None
        latest_historical_victims = 0
        if hist_df is not None and not hist_df.empty:
            victim_col = get_victim_column(hist_df)
            hist_country = hist_df[
                hist_df["Country"].astype(str).str.strip().str.casefold() == country_key
            ]
            if not hist_country.empty:
                past_victims = hist_country[victim_col].sum()
                latest_historical_year = int(hist_country["Year"].max())
                latest_historical_victims = hist_country[
                    hist_country["Year"] == latest_historical_year
                ][victim_col].sum()

        percent_change = 0.0
        comparison_base = max(future_victims, latest_historical_victims)
        if comparison_base > 0:
            percent_change = round(
                ((future_victims - latest_historical_victims) / comparison_base) * 100,
                1
            )

        return jsonify({
            "Country": country,
            "Historical Victims": int(round(past_victims)),
            "Future Predicted Victims": int(round(future_victims)),
            "Latest Historical Year": latest_historical_year,
            "Latest Historical Victims": int(round(latest_historical_victims)),
            "Forecast Year": forecast_year,
            "Percent Change": percent_change
        })
    except Exception as exc:
        return _error(f"Unable to load country risk summary: {exc}", 500, "risk_summary_failed")
