# AQI-Monitoring-Anomaly-Detection-Dashboard/streamlit.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(
    page_title="AQI Anomaly Detection Dashboard",
    layout="wide",
)

# === CONFIG ===
API_URL = "http://127.0.0.1:8000"  # FastAPI backend URL


@st.cache_data(ttl=300)
def get_filters_from_api():
    try:
        resp = requests.get(f"{API_URL}/filters")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error fetching filters from API: {e}")
        return {"countries": [], "pollutants": [], "cities": []}


def fetch_map_data(
    countries_selected,
    pollutants_selected,
    only_anomalies: bool,
):
    params = {
        "only_anomalies": str(only_anomalies).lower(),
    }

    if countries_selected:
        params["country"] = ",".join(countries_selected)
    if pollutants_selected:
        params["pollutant"] = ",".join(pollutants_selected)

    try:
        resp = requests.get(f"{API_URL}/map-data", params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to FastAPI at {API_URL}. Ensure the backend is running.")
        return {"count": 0, "data": []}
    except Exception as e:
        st.error(f"Error fetching map data from API: {e}")
        return {"count": 0, "data": []}


@st.cache_data(ttl=300)
def fetch_summary():
    try:
        resp = requests.get(f"{API_URL}/summary")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to FastAPI at {API_URL}. Ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"Error fetching summary from API: {e}")
        return None


# === SIDEBAR ===
st.sidebar.title("AQI Filters")

filters = get_filters_from_api()
countries = filters.get("countries", [])
pollutants = filters.get("pollutants", [])

selected_countries = st.sidebar.multiselect("Country", options=countries, default=[])
selected_pollutants = st.sidebar.multiselect(
    "Pollutant", options=pollutants, default=[]
)

only_anomalies = st.sidebar.checkbox("Show only anomalies", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("Backend API: " + API_URL)

# === MAIN LAYOUT ===
st.title("🌍 AQI Monitoring & Anomaly Detection Dashboard")

col_top1, col_top2 = st.columns([2, 1])

with col_top2:
    st.subheader("Summary")
    summary = fetch_summary()
    if summary:
        st.metric("Total Measurements", summary["total_rows"])
        st.metric("Countries", summary["num_countries"])
        st.metric("Cities", summary["num_cities"])
        st.metric("Pollutants", summary["num_pollutants"])


with col_top1:
    st.subheader("Global Map")

    data_json = fetch_map_data(
        countries_selected=selected_countries,
        pollutants_selected=selected_pollutants,
        only_anomalies=only_anomalies,
    )
    count = data_json.get("count", 0)
    data_records = data_json.get("data", [])
    df = pd.DataFrame(data_records)

    if df.empty:
        st.warning("No data to display. Try changing the filters or check the backend connection.")
    else:
        st.caption(f"Number of points: {count}")

        # MODIFIED: Prepare new columns for clearer visual distinction of anomalies
        df['Anomaly_Status'] = df['is_anomaly'].apply(lambda x: '🔴 Anomaly' if x == 1 else '🔵 Normal')
        # Increase the size of anomaly points for better visibility on the map
        df['Plot_Size'] = df.apply(lambda row: row['Value'] * 2 if row['is_anomaly'] == 1 else row['Value'], axis=1)

        # Plotly map
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            # MODIFIED: Color by Anomaly Status for immediate visual recognition
            color="Anomaly_Status",
            # MODIFIED: Use the adjusted size column to make anomalies bigger
            size="Plot_Size",
            color_discrete_map={'🔴 Anomaly': 'red', '🔵 Normal': 'blue'},
            hover_name="City",
            hover_data={
                "Country_Label": True,
                "Location": True,
                "Value": True,
                "Pollutant": True,
                "Last_Updated": True,
                "is_anomaly": True,
                "anomaly_score": True, # Added anomaly_score to hover
                "lat": False,
                "lon": False,
                "Plot_Size": False # Hide this helper column
            },
            zoom=1,
            height=600,
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("Data Table")

if not df.empty:
    # Show a slightly nicer table
    table_df = df[
        [
            "Country_Label",
            "Country_Code",
            "City",
            "Location",
            "Pollutant",
            "Value",
            "Unit",
            "Last_Updated",
            "is_anomaly",
            "anomaly_score",
        ]
    ].copy()

    st.dataframe(table_df, use_container_width=True, height=400)
else:
    st.info("No data to show in the table.")