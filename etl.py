import pandas as pd
import sqlite3
from pathlib import Path

# locate CSV
csv_path = Path("ats_data.csv")
if not csv_path.exists():
    raise SystemExit("ats_data.csv not found in current folder. Put the CSV here and re-run.")

# Load raw data (try common encodings if required)
try:
    df = pd.read_csv(csv_path)
except Exception as e:
    # fallback to latin1 if encoding issue
    df = pd.read_csv(csv_path, encoding="latin1")

# Rename known columns for clarity
df = df.rename(columns={
    "target": "job_change",
    "training_hours": "training_hours_total"
})

# Fill missing for common categorical columns (if present)
for c in ["gender", "education_level", "major_discipline", "company_size", "last_new_job", "enrolled_university"]:
    if c in df.columns:
        df[c] = df[c].fillna("Unknown")

# Standardize experience values (if present)
if "experience" in df.columns:
    df["experience"] = df["experience"].astype(str).str.strip()
    df["experience"] = df["experience"].replace({">20": "21", "<1": "0"})
    df["experience"] = pd.to_numeric(df["experience"], errors="coerce").fillna(0)

# Derive a simple flag for relevant_experience if it exists
if "relevant_experience" in df.columns:
    df["is_experienced"] = df["relevant_experience"].astype(str).apply(lambda x: 1 if "Has" in x or "Yes" in x else 0)
else:
    df["is_experienced"] = 0

# Optional: convert dates if present
for date_col in ["application_date", "hire_date", "enrolment_date"]:
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# Persist to SQLite
db_path = "ats.db"
con = sqlite3.connect(db_path)
df.to_sql("applications", con, if_exists="replace", index=False)
con.close()

print("✅ ETL complete. Rows written:", len(df))
print("Columns:", list(df.columns))
print("SQLite DB:", db_path)
