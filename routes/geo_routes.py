import hashlib
import math

from flask import Blueprint, jsonify, request

from models.forecast import forecast_future

geo_bp = Blueprint("geo", __name__)


INDIA_PRIORITY_AREAS = [
    {"name": "Bihar", "latitude": 25.5941, "longitude": 85.1376, "weight": 0.28},
    {"name": "Odisha", "latitude": 20.2961, "longitude": 85.8245, "weight": 0.18},
    {"name": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873, "weight": 0.16},
    {"name": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777, "weight": 0.20},
    {"name": "West Bengal", "latitude": 22.5726, "longitude": 88.3639, "weight": 0.18},
]


def _normalize_country(value):
    return str(value).strip().casefold()


def _error(message, status=400, code="bad_request"):
    return jsonify({"error": {"code": code, "message": message}}), status


def _build_future_risk_areas(df, year):
    areas = []

    for _, row in df.iterrows():
        country = row["Country"]
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        risk_score = int(round(row["Predicted Victims"]))

        if risk_score <= 0:
            continue

        if _normalize_country(country) == "india":
            for idx, area in enumerate(INDIA_PRIORITY_AREAS, start=1):
                area_risk = int(round(risk_score * area["weight"]))
                areas.append({
                    "country": country,
                    "year": year,
                    "risk_score": area_risk,
                    "latitude": area["latitude"],
                    "longitude": area["longitude"],
                    "source_latitude": round(lat, 4),
                    "source_longitude": round(lon, 4),
                    "area_index": idx,
                    "area_name": area["name"],
                })
            continue

        point_count = max(3, min(6, 2 + int(math.log10(risk_score + 1))))
        spread_km = max(70.0, min(260.0, 55.0 + math.log10(risk_score + 1) * 65.0))
        seed_bytes = hashlib.sha256(f"{country}-{year}".encode("utf-8")).digest()

        raw_weights = []
        for idx in range(point_count):
            raw_weights.append(1.0 + (seed_bytes[idx] / 255.0))

        total_weight = sum(raw_weights)

        for idx in range(point_count):
            angle = (2 * math.pi * idx / point_count) + ((seed_bytes[idx + 8] / 255.0) * 0.85)
            distance_scale = 0.38 + ((seed_bytes[idx + 16] / 255.0) * 0.62)
            distance_km = spread_km * distance_scale

            lat_offset = (distance_km / 111.0) * math.cos(angle)
            lon_divisor = max(0.25, math.cos(math.radians(lat)))
            lon_offset = (distance_km / (111.0 * lon_divisor)) * math.sin(angle)
            area_risk = int(round(risk_score * (raw_weights[idx] / total_weight)))

            areas.append({
                "country": country,
                "year": year,
                "risk_score": area_risk,
                "latitude": round(lat + lat_offset, 4),
                "longitude": round(lon + lon_offset, 4),
                "source_latitude": round(lat, 4),
                "source_longitude": round(lon, 4),
                "area_index": idx + 1,
                "area_name": f"Area {idx + 1}",
            })

    return areas


@geo_bp.route("/geo-hotspots", methods=["GET"])
def geo_hotspots():
    try:
        year = request.args.get("year", type=int)
        if year is not None and year < 0:
            return _error("year must be a positive integer", 400, "invalid_year")

        df = forecast_future()
        year_col = "Year" if "Year" in df.columns else "Forecast Year"

        if year:
            df = df[df[year_col] == year]

        result = (
            df.groupby("Country")
            .agg({
                "Latitude": "mean",
                "Longitude": "mean",
                "Predicted Victims": "sum"
            })
            .reset_index()
        )

        result["Predicted Victims"] = result["Predicted Victims"].round().astype(int)

        return jsonify([
            {
                "country": row["Country"],
                "latitude": row["Latitude"],
                "longitude": row["Longitude"],
                "risk_score": row["Predicted Victims"]
            }
            for _, row in result.iterrows()
        ])
    except Exception as exc:
        return _error(f"Unable to load hotspot map data: {exc}", 500, "geo_hotspots_failed")


@geo_bp.route("/geo-future-areas", methods=["GET"])
def geo_future_areas():
    try:
        year = request.args.get("year", default=2027, type=int)
        if year < 0:
            return _error("year must be a positive integer", 400, "invalid_year")

        country = request.args.get("country")
        df = forecast_future()
        year_col = "Year" if "Year" in df.columns else "Forecast Year"
        df = df[df[year_col] == year]

        if country:
            country_key = _normalize_country(country)
            df = df[df["Country"].astype(str).str.strip().str.casefold() == country_key]

        if df.empty:
            return jsonify([])

        areas = _build_future_risk_areas(df, year)
        return jsonify(areas)
    except Exception as exc:
        return _error(f"Unable to load future hotspot areas: {exc}", 500, "geo_future_areas_failed")
