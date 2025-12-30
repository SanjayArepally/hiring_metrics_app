# Hiring Campaign Metrics — Streamlit Demo

## Problem
Hiring teams need quick, trusted metrics for the hiring funnel without manual data pulls.

## Solution
Lightweight ETL (pandas → SQLite) + Streamlit dashboard. Shows KPIs, filters, charts, and downloadable CSV. Demo includes an ETL button to re-run the pipeline locally.

## How to run (local)
1. Create venv and install:
   - python3 -m venv venv
   - source venv/bin/activate
   - pip install -r requirements.txt
2. Load data and create DB:
   - python etl.py
3. Run the app:
   - streamlit run app.py

## Files
- etl.py — ETL script (CSV → SQLite)
- app.py — Streamlit dashboard
- ats_data.csv — input CSV (Kaggle) **(do not push sensitive or proprietary CSVs)**
- ats.db — generated SQLite DB (ignored by .gitignore)

## Notes
- For production: replace SQLite with S3/Redshift, schedule ETL via Airflow/Glue, use secure credentials, and remove the ETL button from public hosting.
