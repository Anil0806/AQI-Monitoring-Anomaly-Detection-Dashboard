# AQI-Monitoring-Anomaly-Detection-Dashboard/fast_api.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Optional
import os

# ✅ IMPORTANT: anomaly_detection.py must be in the project root (same folder as this "api" directory's parent)
from main import detect_anomalies

# === CONFIG ===
# Your CSV path
CSV_PATH = "preprocessed_openaq_ready.csv" 


app = FastAPI(
    title="AQI Anomaly Detection API",
    description="Backend API serving AQI data with anomaly labels",
    version="1.0.0",
)

# Allow Streamlit (usually on localhost:8501) and other local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_and_prepare_data() -> pd.DataFrame:
    """
    Load the CSV, normalize column names, map them to consistent names,
    create lat/lon, and run anomaly detection.
    """

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

    # Read CSV
    df = pd.read_csv(CSV_PATH, encoding="utf-8")

    # Save original column names (for debug messages)
    original_cols = df.columns.tolist()

    # 1️⃣ Normalize column names: lowercase, strip spaces, replace spaces with _
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    # Helper to find a column among possible names
    def find_col(possible_names):
        for name in possible_names:
            if name in df.columns:
                return name
        return None

    # 2️⃣ Try to locate each logical field in your data
    col_country_code = find_col(["country_code", "countrycode", "code"])
    col_city = find_col(["city"])
    col_location = find_col(["location", "station", "site"])
    
    # MODIFIED: Search for Latitude/Longitude instead of a single Coordinates column
    col_latitude = find_col(["latitude", "lat"])
    col_longitude = find_col(["longitude", "lon"])
    col_coordinates = "NOT_USED" # Dummy value to satisfy the logical fields check below

    col_pollutant = find_col(["pollutant", "parameter"])
    
    # MODIFIED: Set col_source_name to None if not found, and handle it later.
    # The error indicated this column is missing.
    col_source_name = find_col(["source_name", "sourcename", "source"])
    
    col_unit = find_col(["unit"])
    col_value = find_col(["value", "concentration"])
    col_last_updated = find_col(["last_updated", "date_local", "date", "timestamp"])
    col_country_label = find_col(["country_label", "country"])

    required_logical = {
        "Country_Code": col_country_code,
        "City": col_city,
        "Location": col_location,
        # 'Coordinates' is now satisfied by the dummy value, we'll use lat/lon later.
        "Coordinates": col_coordinates, 
        "Pollutant": col_pollutant,
        # We will handle missing Source_Name by filling with a default value.
        "Source_Name": col_source_name, 
        "Unit": col_unit,
        "Value": col_value,
        "Last_Updated": col_last_updated,
        "Country_Label": col_country_label,
    }

    # Filter out Coordinate and Source_Name from the required check, 
    # and ensure lat/lon are present.
    missing_logical = [
        k for k, v in required_logical.items() 
        if v is None and k not in ["Coordinates", "Source_Name"]
    ]
    
    # Check for latitude/longitude explicitly
    if col_latitude is None or col_longitude is None:
        missing_logical.append("Latitude/Longitude")


    if missing_logical:
        # Give a very clear error so we can adjust mapping if needed
        raise ValueError(
            "Your CSV column names don't match what the API expects.\n"
            f"Missing logical fields: {missing_logical}\n"
            f"CSV columns after normalization: {df.columns.tolist()}\n"
            f"Original CSV columns: {original_cols}"
        )
        
    # If Source_Name is missing, create it and fill with a default value
    if col_source_name is None:
        df["Source_Name"] = "Unknown Source"
        col_source_name = "Source_Name"


    # 3️⃣ Rename to the standard names used in the rest of the code
    rename_dict = {
        col_country_code: "Country_Code",
        col_city: "City",
        col_location: "Location",
        col_pollutant: "Pollutant",
        col_source_name: "Source_Name",
        col_unit: "Unit",
        col_value: "Value",
        col_last_updated: "Last_Updated",
        col_country_label: "Country_Label",
        
        # New: Rename the Latitude/Longitude columns to the standard 'lat'/'lon'
        col_latitude: "lat",
        col_longitude: "lon",
    }
    df = df.rename(columns=rename_dict)

    # 4️⃣ Coordinates -> lat, lon
    # MODIFIED: Removed coordinate splitting logic, as the data now has separate lat/lon columns.
    # The new lat/lon column names are already mapped in the rename_dict above.
    
    # Ensure lat/lon columns are float
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")


    # 5️⃣ Detect anomalies
    df = detect_anomalies(df)

    return df


@app.on_event("startup")
def startup_event():
    """
    Load data once at startup and keep in memory.
    """
    try:
        df = _load_and_prepare_data()
        app.state.df = df
        print(f"Loaded {len(df)} rows from CSV.")
    except Exception as e:
        # If this fails, API will still run but endpoints will raise HTTP 500.
        print("Error loading CSV on startup:", e)
        app.state.df = None


def get_df() -> pd.DataFrame:
    df = getattr(app.state, "df", None)
    if df is None:
        # Try to load lazily if not loaded
        df = _load_and_prepare_data()
        app.state.df = df
    return df


@app.get("/health")
def health():
    """
    Health check endpoint.
    """
    df_loaded = app.state.df is not None
    return {"status": "ok", "data_loaded": df_loaded}


@app.get("/filters")
def filters():
    """
    Return unique filter values for the Streamlit UI.
    """
    df = get_df()
    return {
        "countries": sorted(df["Country_Label"].dropna().unique().tolist()),
        "pollutants": sorted(df["Pollutant"].dropna().unique().tolist()),
        "cities": sorted(df["City"].dropna().unique().tolist()),
    }


@app.get("/map-data")
def map_data(
    country: Optional[str] = Query(
        default=None,
        description="Country label or comma-separated list, e.g. 'India,United States'",
    ),
    pollutant: Optional[str] = Query(
        default=None,
        description="Pollutant or comma-separated list, e.g. 'PM2.5,NO2'",
    ),
    only_anomalies: bool = False,
    limit: int = 10000,
):
    """
    Main data endpoint used by Streamlit.
    Returns rows + lat/lon + anomaly labels.

    Filters:
    - country: Country_Label filter (single or comma separated)
    - pollutant: Pollutant filter (single or comma separated)
    - only_anomalies: if True, return only rows where is_anomaly == 1
    """

    df = get_df()

    # Apply filters
    filtered = df.copy()

    if country:
        country_list = [c.strip() for c in country.split(",") if c.strip()]
        filtered = filtered[filtered["Country_Label"].isin(country_list)]

    if pollutant:
        pollutant_list = [p.strip() for p in pollutant.split(",") if p.strip()]
        filtered = filtered[filtered["Pollutant"].isin(pollutant_list)]

    if only_anomalies:
        filtered = filtered[filtered["is_anomaly"] == 1]

    # Limit the number of rows to avoid huge responses
    filtered = filtered.head(limit)

    return {
        "count": int(len(filtered)),
        "data": filtered[
            [
                "Country_Code",
                "Country_Label",
                "City",
                "Location",
                "Pollutant",
                "Source_Name",
                "Unit",
                "Value",
                "Last_Updated",
                "lat",
                "lon",
                "is_anomaly",
                "anomaly_score",
            ]
        ].to_dict(orient="records"),
    }


@app.get("/summary")
def summary():
    """
    Simple overall summary statistics.
    """
    df = get_df()

    summary_by_country = (
        df.groupby("Country_Label")["Value"]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "count": "num_measurements",
                "mean": "avg_value",
                "min": "min_value",
                "max": "max_value",
            }
        )
    )

    summary_by_pollutant = (
        df.groupby("Pollutant")["Value"]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "count": "num_measurements",
                "mean": "avg_value",
                "min": "min_value",
                "max": "max_value",
            }
        )
    )

    return {
        "total_rows": int(len(df)),
        "num_countries": int(df["Country_Label"].nunique()),
        "num_cities": int(df["City"].nunique()),
        "num_pollutants": int(df["Pollutant"].nunique()),
        "summary_by_country": summary_by_country.to_dict(orient="records"),
        "summary_by_pollutant": summary_by_pollutant.to_dict(orient="records"),
    }