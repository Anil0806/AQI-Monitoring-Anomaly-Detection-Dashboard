# AQI Monitoring & Anomaly Detection Dashboard
**Real-time Global Air Quality Monitoring with Intelligent Anomaly Detection**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A beautiful, full-stack, interactive dashboard that visualizes global air quality measurements in real time and automatically detects and highlights pollution anomalies using the **Interquartile Range (IQR)** method.

![Dashboard Preview](https://via.placeholder.com/1400x800.png?text=AQI+Dashboard+Live+Preview+-+Interactive+Map+%26+Anomaly+Detection)  
*(Replace the link above with your actual screenshot)*

---

## Features

### Interactive Frontend (Streamlit)
- Global interactive map powered by **Plotly Express** (zoom, pan, hover tooltips)
- Anomalous measurements highlighted in **red** with larger markers
- Real-time filtering:
  - Country & City dropdowns
  - Pollutant selector (PM2.5, PM10, NO₂, O₃, CO, SO₂, etc.)
  - Toggle to show **only anomalies**
- Live summary cards: total measurements, countries, cities, anomalies detected
- Searchable & sortable data table with anomaly scores

### High-Performance Backend (FastAPI)
- Fast RESTful API serving preprocessed and analyzed data
- Automatic data loading + anomaly detection on startup
- Smart column normalization for OpenAQ datasets
- Key Endpoints:
  - `GET /filters` → Dynamic filter options
  - `GET /map-data` → Map-ready data including `lat`, `lon`, `is_anomaly`, `anomaly_score`
  - `GET /summary` → Aggregated statistics

---

## Technology Stack

| Layer              | Technology                  |
|--------------------|-----------------------------|
| Backend            | FastAPI + Uvicorn           |
| Frontend           | Streamlit                   |
| Data Processing    | Pandas, NumPy               |
| Visualization      | Plotly Express              |
| Anomaly Detection  | Interquartile Range (IQR)   |
| Language           | Python 3.8+                 |

---

## Quick Start (2 terminals)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/yourusername/AQI-Monitoring-Anomaly-Detection-Dashboard.git
cd AQI-Monitoring-Anomaly-Detection-Dashboard

# Optional but recommended: create virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt# AQI-Monitoring-Anomaly-Detection-Dashboard
AQI Monitoring &amp; Anomaly Detection Dashboard built with Python and Streamlit. Visualizes air quality trends, detects abnormal pollution spikes using ML-based anomaly detection, and helps users track city-wise AQI in real time
