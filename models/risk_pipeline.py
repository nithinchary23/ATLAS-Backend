from models.forecast import forecast_future
from models.risk import assign_risk_levels

def generate_country_risk(year=2026):
    """
    Generates country-level risk labels for a future year
    """
    df_forecast = forecast_future()
    year_col = "Year" if "Year" in df_forecast.columns else "Forecast Year"

    df_year = df_forecast[df_forecast[year_col] == year]

    df_risk = assign_risk_levels(df_year)

    return df_risk
