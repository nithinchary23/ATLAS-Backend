from flask import Blueprint, jsonify, request

from models.forecast import forecast_future
from utils.load_data import load_dataset

forecast_bp = Blueprint("forecast", __name__)


def _normalize_forecast_df(df):
    if "Forecast Year" in df.columns and "Year" not in df.columns:
        df = df.rename(columns={"Forecast Year": "Year"})
    return df


def _filter_country(df, country):
    if not country or "Country" not in df.columns:
        return df

    country_key = country.strip().casefold()
    return df[df["Country"].astype(str).str.strip().str.casefold() == country_key]


def _error(message, status=400, code="bad_request"):
    return jsonify({"error": {"code": code, "message": message}}), status


@forecast_bp.route("/forecast", methods=["GET"])
def raw_forecast():
    try:
        country = request.args.get("country")
        df = _normalize_forecast_df(forecast_future())
        df = _filter_country(df, country)
        return jsonify(df.to_dict(orient="records"))
    except Exception as exc:
        return _error(f"Unable to load forecast data: {exc}", 500, "forecast_load_failed")


@forecast_bp.route("/forecast/aggregated", methods=["GET"])
def aggregated_forecast():
    try:
        country = request.args.get("country")
        df = _normalize_forecast_df(forecast_future())

        result = (
            df.groupby(["Country", "Year"])
            .agg({
                "Predicted Victims": "sum",
                "Latitude": "mean",
                "Longitude": "mean"
            })
            .reset_index()
        )

        result["Predicted Victims"] = result["Predicted Victims"].round().astype(int)
        result["Latitude"] = result["Latitude"].round(4)
        result["Longitude"] = result["Longitude"].round(4)

        result = _filter_country(result, country)
        return jsonify(result.to_dict(orient="records"))
    except Exception as exc:
        return _error(f"Unable to load aggregated forecast: {exc}", 500, "forecast_aggregate_failed")


@forecast_bp.route("/forecast/timeline", methods=["GET"])
def forecast_timeline():
    country = request.args.get("country")
    if not country:
        return _error("country query parameter required", 400, "missing_country")

    try:
        forecast_df = _filter_country(_normalize_forecast_df(forecast_future()), country)
        hist_df = load_dataset("data/final_ml_dataset_AGGREGATED.csv")

        historical = []
        if hist_df is not None and not hist_df.empty:
            victim_col = None
            for col in hist_df.columns:
                if col.lower().replace(" ", "") in {
                    "victims",
                    "totalvictims",
                    "victimcount",
                    "numberofvictims"
                }:
                    victim_col = col
                    break

            if victim_col:
                hist_country = _filter_country(hist_df, country)
                historical = (
                    hist_country.groupby("Year")[victim_col]
                    .sum()
                    .reset_index()
                    .sort_values("Year")
                    .tail(5)
                    .rename(columns={victim_col: "Victims"})
                    .assign(Type="Historical")
                    .to_dict(orient="records")
                )

        forecast = (
            forecast_df[["Year", "Predicted Victims"]]
            .rename(columns={"Predicted Victims": "Victims"})
            .sort_values("Year")
            .assign(Type="Forecast")
            .to_dict(orient="records")
        )

        return jsonify(historical + forecast)
    except Exception as exc:
        return _error(f"Unable to load forecast timeline: {exc}", 500, "forecast_timeline_failed")
