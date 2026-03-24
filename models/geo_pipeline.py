from models.forecast import forecast_future
from models.geo_cluster import detect_hotspots

def generate_future_hotspots(year=2026):
    """
    Generates hotspot clusters for a specific future year
    """
    df_forecast = forecast_future()
    year_col = "Year" if "Year" in df_forecast.columns else "Forecast Year"

    df_year = df_forecast[df_forecast[year_col] == year]

    hotspots = detect_hotspots(df_year)

    return hotspots
