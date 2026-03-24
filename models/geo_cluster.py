import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import MinMaxScaler

def detect_hotspots(
    df,
    eps_km=600,
    min_samples=3
):
    """
    Detects geospatial hotspots using DBSCAN
    eps_km: clustering radius in kilometers
    """

    # Copy to avoid mutation
    data = df.copy()

    # Convert lat/long to radians (for haversine)
    coords = np.radians(data[["Latitude", "Longitude"]].values)

    # Convert km to radians (Earth radius ≈ 6371 km)
    eps = eps_km / 6371.0

    # Run DBSCAN
    db = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="haversine"
    ).fit(coords)

    data["Cluster"] = db.labels_

    # Noise points = -1
    hotspots = data[data["Cluster"] != -1]

    if hotspots.empty:
        return pd.DataFrame()

    # Aggregate cluster severity
    cluster_summary = (
        hotspots
        .groupby("Cluster")
        .agg({
            "Predicted Victims": "sum",
            "Latitude": "mean",
            "Longitude": "mean",
            "Country": "count"
        })
        .rename(columns={"Country": "Countries_Count"})
        .reset_index()
    )

    # Normalize severity score
    scaler = MinMaxScaler()
    cluster_summary["Risk_Score"] = scaler.fit_transform(
        cluster_summary[["Predicted Victims"]]
    )

    return cluster_summary
