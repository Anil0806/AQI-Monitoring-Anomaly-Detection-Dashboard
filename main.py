# AQI-Monitoring-Anomaly-Detection-Dashboard/main.py

import pandas as pd
import numpy as np
from typing import Tuple


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple anomaly detection on 'Value' column using IQR.
    Adds:
        * is_anomaly (0 or 1)
        * anomaly_score (distance from median, 0 for non-anomalies)
    """

    df = df.copy()

    if "Value" not in df.columns:
        raise ValueError("Expected a 'Value' column in the dataframe.")

    # Ensure numeric Value
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Work only on non-null values to compute thresholds
    value_series = df["Value"].dropna()

    if value_series.empty:
        df["is_anomaly"] = 0
        df["anomaly_score"] = 0.0
        return df

    q1 = value_series.quantile(0.25)
    q3 = value_series.quantile(0.75)
    
    # MODIFIED: Simplified IQR calculation.
    iqr = q3 - q1 

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    median = value_series.median()

    def _is_anomaly(v: float) -> int:
        if pd.isna(v):
            return 0
        return int(v < lower_bound or v > upper_bound)

    def _score(v: float) -> float:
        if pd.isna(v):
            return 0.0
        if v < lower_bound or v > upper_bound:
            return float(abs(v - median))
        return 0.0

    df["is_anomaly"] = df["Value"].apply(_is_anomaly)
    df["anomaly_score"] = df["Value"].apply(_score)

    return df