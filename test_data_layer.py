import pandas as pd
import pytest

from models import forecast as forecast_module
from utils import load_data as load_data_module


def test_load_dataset_missing_file():
    with pytest.raises(FileNotFoundError):
        load_data_module.load_dataset("data/does_not_exist.csv")


def test_load_dataset_caches_by_path(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text("Country,Year,Latitude,Longitude,Victims\nIndia,2022,1,2,10\n", encoding="utf-8")
    second.write_text("Country,Year,Latitude,Longitude,Victims\nNigeria,2022,3,4,20\n", encoding="utf-8")

    load_data_module._DATASET_CACHE = {}

    df_first = load_data_module.load_dataset(str(first))
    df_second = load_data_module.load_dataset(str(second))

    assert df_first.iloc[0]["Country"] == "India"
    assert df_second.iloc[0]["Country"] == "Nigeria"
    assert len(load_data_module._DATASET_CACHE) == 2


def test_forecast_future_missing_required_columns(monkeypatch):
    broken = pd.DataFrame(
        {
            "Country": ["India"],
            "Latitude": [10.0],
            "Longitude": [20.0],
            "Victims": [100],
        }
    )

    monkeypatch.setattr(forecast_module, "_FORECAST_CACHE", None)
    monkeypatch.setattr(forecast_module, "load_dataset", lambda path: broken)

    with pytest.raises(ValueError, match="Missing required columns"):
        forecast_module.forecast_future()


def test_forecast_future_cleans_dirty_rows(monkeypatch):
    dirty = pd.DataFrame(
        {
            "Country": ["India", "India", "India", "Nigeria", ""],
            "Year": ["2020", "2021", "bad", "2022", "2022"],
            "Latitude": ["20.0", "21.0", "x", "9.0", "10.0"],
            "Longitude": ["78.0", "79.0", "y", "8.0", "11.0"],
            "Victims": ["100", "120", "bad", "50", "80"],
        }
    )

    monkeypatch.setattr(forecast_module, "_FORECAST_CACHE", None)
    monkeypatch.setattr(forecast_module, "load_dataset", lambda path: dirty)

    result = forecast_module.forecast_future()

    assert not result.empty
    assert set(result.columns) == {
        "Country",
        "Latitude",
        "Longitude",
        "Forecast Year",
        "Predicted Victims",
    }
    assert set(result["Country"]) == {"India", "Nigeria"}
    assert set(result["Forecast Year"]) == {2025, 2026, 2027}
