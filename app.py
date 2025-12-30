import streamlit as st
import pandas as pd
import sqlite3
import subprocess
from pathlib import Path

st.set_page_config(page_title="Hiring Campaign Insights", layout="wide")
st.title("Hiring Campaign Insights")
st.markdown("Quick dashboard showing candidate funnel and hiring signals from ATS data.")

DB_PATH = "ats.db"
ETL_SCRIPT = "etl.py"

@st.cache_data(ttl=600)
def load_data(db_path=DB_PATH):
    if not Path(db_path).exists():
        return pd.DataFrame()
    con = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM applications", con)
    con.close()
    return df

df = load_data()

if df.empty:
    st.warning("No data found. Run `python etl.py` in the project folder first, then refresh this page.")
    st.stop()

# Normalize column names if needed
if "job_change" not in df.columns and "target" in df.columns:
    df["job_change"] = df["target"]

# KPIs
total_apps = len(df)
job_change_count = int(df["job_change"].sum()) if "job_change" in df.columns else 0
job_change_pct = (job_change_count / total_apps * 100) if total_apps else 0
avg_experience = df["experience"].mean() if "experience" in df.columns else None
avg_training = df["training_hours_total"].mean() if "training_hours_total" in df.columns else None

col1, col2, col3, col4 = st.columns([1,1,1,1])
col1.metric("Total applications", total_apps)
col2.metric("Moved / job_change", f"{job_change_count} ({job_change_pct:.1f}%)")
col3.metric("Avg experience (yrs)", f"{avg_experience:.1f}" if avg_experience is not None else "N/A")
col4.metric("Avg training hrs", f"{avg_training:.1f}" if avg_training is not None else "N/A")

st.markdown("---")

# Sidebar filters
st.sidebar.header("Filters")
gender_options = ["All"] + sorted(df["gender"].dropna().unique().tolist()) if "gender" in df.columns else ["All"]
edu_options = ["All"] + sorted(df["education_level"].dropna().unique().tolist()) if "education_level" in df.columns else ["All"]

sel_gender = st.sidebar.selectbox("Gender", gender_options)
sel_edu = st.sidebar.selectbox("Education Level", edu_options)
min_exp = int(df["experience"].min()) if "experience" in df.columns else 0
max_exp = int(df["experience"].max()) if "experience" in df.columns else 0
sel_exp = st.sidebar.slider("Experience (years)", min_exp, max_exp, (min_exp, max_exp)) if max_exp > min_exp else (min_exp, max_exp)

# Apply filters
df_filtered = df.copy()
if sel_gender != "All":
    df_filtered = df_filtered[df_filtered["gender"] == sel_gender]
if sel_edu != "All":
    df_filtered = df_filtered[df_filtered["education_level"] == sel_edu]
if "experience" in df.columns:
    df_filtered = df_filtered[(df_filtered["experience"] >= sel_exp[0]) & (df_filtered["experience"] <= sel_exp[1])]

# Charts
st.subheader("Funnel & Distributions")
left, right = st.columns([2,3])

with left:
    st.write("Job change by source")
    if "enrolled_university" in df_filtered.columns:
        temp = df_filtered.groupby("enrolled_university")["job_change"].mean().sort_values(ascending=False).head(10)
        st.bar_chart(temp)
    else:
        st.write("No source data available")

with right:
    st.write("Education level distribution")
    if "education_level" in df_filtered.columns:
        st.bar_chart(df_filtered["education_level"].value_counts())
    else:
        st.write("No education level data available")

st.markdown("---")
st.subheader("Time series (applications over time)")
if "application_date" in df.columns:
    ts = df.copy()
    ts["application_date"] = pd.to_datetime(ts["application_date"], errors="coerce")
    ts = ts.dropna(subset=["application_date"])
    ts = ts.set_index("application_date").resample("W").size()
    st.line_chart(ts)
else:
    st.write("No application_date column found to plot time series.")

st.markdown("---")
st.subheader("Filtered data (first 200 rows)")
st.dataframe(df_filtered.head(200))

# Download filtered CSV
def convert_df_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv_bytes(df_filtered)
st.download_button("Download filtered CSV", csv, "filtered_applications.csv", "text/csv")

st.markdown("---")
st.write("### Actions")
st.write("- Run ETL to refresh data if `ats_data.csv` changed.")
st.write("- Consider pushing `ats.db` to S3 or Redshift for production.")

# Safe ETL run button (only run locally; for demo only)
if st.button("Run ETL (runs etl.py)"):
    st.warning("Running ETL script now. This spawns a local Python process — do not use on public hosting without safeguards.")
    try:
        proc = subprocess.run(["python", ETL_SCRIPT], capture_output=True, text=True, timeout=120)
        st.text("ETL stdout:")
        st.code(proc.stdout)
        if proc.stderr:
            st.text("ETL stderr:")
            st.code(proc.stderr)
        # reload data after ETL
        load_data.clear()
        df = load_data()
        st.success("ETL completed and data reloaded. Refresh charts if needed.")
    except Exception as e:
        st.error(f"Error running ETL: {e}")

st.markdown("### Notes")
st.write("- This demo reads a local SQLite DB (ats.db). For production use, read from S3/Redshift and configure proper credentials.")
st.write("- Use the ETL button for local demos only.")
