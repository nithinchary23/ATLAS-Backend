from pathlib import Path

import pandas as pd

_DATASET_CACHE = {}


def load_dataset(path: str):
    dataset_path = Path(path)
    cache_key = str(dataset_path.resolve())

    if cache_key in _DATASET_CACHE:
        return _DATASET_CACHE[cache_key]

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    if df.empty:
        raise ValueError(f"Dataset is empty: {dataset_path}")

    _DATASET_CACHE[cache_key] = df
    return df
