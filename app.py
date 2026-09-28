"""
Bellabeat / Fitbit Fitness Data — Streamlit + SQL Analytics App
================================================================
Run:
    streamlit run app.py

Expects fitbit.db and queries.py in the same folder as this file.
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from queries import QUERIES

sns.set_theme(style="whitegrid")

DB_PATH = Path(__file__).parent / "fitbit.db"

st.set_page_config(page_title="Bellabeat Fitness Analytics", layout="wide")


# ---------------------------------------------------------------- helpers
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn)


if not DB_PATH.exists():
    st.error(
        f"Couldn't find {DB_PATH.name}. Run `python build_database.py` first "
        "to generate it from the raw CSVs."
    )
    st.stop()

NAMED_QUERIES = QUERIES

# ---------------------------------------------------------------- sidebar
st.sidebar.title("🏃 Bellabeat Analytics")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview Dashboard", "🔎 SQL Insights Explorer", "🧮 Custom SQL Query"],
)

# ================================================================ PAGE 1
if page == "📊 Overview Dashboard":
    st.title("Bellabeat Fitness Data — Overview")
    st.caption("33 Fitbit users · April–May 2016 · smart-device usage patterns")

    kpis = run_query(NAMED_QUERIES["total_summary_kpis"]["sql"]).iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Users tracked", int(kpis["total_users"]))
    c2.metric("Avg daily steps", f'{int(kpis["avg_daily_steps"]):,}')
    c3.metric("Avg daily calories", f'{int(kpis["avg_daily_calories"]):,}')
    c4.metric("Avg sleep (hrs)", f'{kpis["avg_sleep_hours"]:.1f}')
    c5.metric("Avg sedentary (hrs)", f'{kpis["avg_sedentary_hours"]:.1f}')

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Activity by Day of Week")
        df = run_query(NAMED_QUERIES["usage_by_weekday"]["sql"])
        fig, ax = plt.subplots(figsize=(5, 3.5))
        sns.barplot(data=df, x="Weekday", y="avg_steps", ax=ax, color="#4C72B0")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right")
        ax.set_ylabel("Avg Steps")
        st.pyplot(fig)
        st.caption("Saturday and Tuesday are the most active days; Sunday is the least active — "
                   "a chance for Bellabeat to nudge users on Sundays.")

    with col2:
        st.subheader("Steps vs. Calories Burned")
        df = run_query(NAMED_QUERIES["steps_calories_correlation"]["sql"])
        fig, ax = plt.subplots(figsize=(5, 3.5))
        sns.scatterplot(data=df, x="TotalSteps", y="Calories", alpha=0.5, ax=ax)
        sns.regplot(data=df, x="TotalSteps", y="Calories", scatter=False,
                    color="red", ax=ax)
        st.pyplot(fig)
        corr = df["TotalSteps"].corr(df["Calories"])
        st.caption(f"Correlation coefficient: **{corr:.2f}** — steps are "
                   "moderately strongly related to calories burned.")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Calories Burned by Hour of Day")
        df = run_query(NAMED_QUERIES["hourly_activity_pattern"]["sql"])
        fig, ax = plt.subplots(figsize=(5, 3.5))
        sns.lineplot(data=df, x="hour_of_day", y="avg_calories", marker="o", ax=ax)
        ax.set_xlabel("Hour of Day")
        st.pyplot(fig)
        st.caption("Calorie burn peaks in the early evening (5-7 PM) with a smaller midday bump — "
                   "good windows for push notifications/reminders.")

    with col4:
        st.subheader("User Activity Segments")
        df = run_query(NAMED_QUERIES["segment_summary"]["sql"])
        fig, ax = plt.subplots(figsize=(5, 3.5))
        order = ["Sedentary", "Low Active", "Somewhat Active", "Active"]
        df["activity_segment"] = pd.Categorical(df["activity_segment"], order)
        df = df.sort_values("activity_segment")
        sns.barplot(data=df, x="activity_segment", y="num_users", ax=ax, color="#55A868")
        ax.set_ylabel("Number of Users")
        ax.set_xlabel("")
        st.pyplot(fig)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Sleep vs. Sedentary Time")
    df = run_query(NAMED_QUERIES["sedentary_vs_sleep"]["sql"])
    if not df.empty:
        fig, ax = plt.subplots(figsize=(9, 3.5))
        sns.scatterplot(data=df, x="SedentaryMinutes", y="TotalMinutesAsleep", alpha=0.5, ax=ax)
        sns.regplot(data=df, x="SedentaryMinutes", y="TotalMinutesAsleep", scatter=False,
                    color="red", ax=ax)
        ax.set_xlabel("Sedentary Minutes")
        ax.set_ylabel("Minutes Asleep")
        st.pyplot(fig)
        corr = df["SedentaryMinutes"].corr(df["TotalMinutesAsleep"])
        st.caption(f"Correlation: **{corr:.2f}** — more sedentary time is associated with less sleep (moderate negative relationship).")

# ================================================================ PAGE 2
elif page == "🔎 SQL Insights Explorer":
    st.title("SQL Insights Explorer")
    st.caption("Pick a business question — see the SQL behind it and the resulting data/chart.")

    names = list(NAMED_QUERIES.keys())
    labels = [f'{n} — {NAMED_QUERIES[n]["question"]}' for n in names]
    choice = st.selectbox("Business question", labels)
    name = names[labels.index(choice)]
    q = NAMED_QUERIES[name]

    st.markdown(f"**Question:** {q['question']}")
    with st.expander("View SQL", expanded=False):
        st.code(q["sql"], language="sql")

    df = run_query(q["sql"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    numeric_cols = df.select_dtypes("number").columns.tolist()
    if len(df) <= 500 and len(numeric_cols) >= 1 and len(df.columns) >= 2:
        st.subheader("Quick chart")
        x_col = df.columns[0]
        y_col = st.selectbox("Plot column", numeric_cols, index=0)
        fig, ax = plt.subplots(figsize=(9, 4))
        if df[x_col].nunique() <= 40:
            sns.barplot(data=df, x=x_col, y=y_col, ax=ax, color="#4C72B0")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        else:
            sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax)
        st.pyplot(fig)

    st.download_button(
        "Download results as CSV",
        df.to_csv(index=False).encode(),
        file_name=f"{name}.csv",
        mime="text/csv",
    )

# ================================================================ PAGE 3
elif page == "🧮 Custom SQL Query":
    st.title("Custom SQL Query")
    st.caption("Write your own read-only SQL against the fitbit.db tables and run it.")

    with st.expander("Available tables"):
        tables = run_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for t in tables["name"]:
            cols = run_query(f"PRAGMA table_info({t})")
            st.markdown(f"**{t}** — {', '.join(cols['name'])}")

    default_sql = "SELECT * FROM daily_activity LIMIT 20;"
    sql_text = st.text_area("SQL query", value=default_sql, height=140)

    if st.button("Run query"):
        stripped = sql_text.strip().rstrip(";").lower()
        if not stripped.startswith("select") and not stripped.startswith("with"):
            st.error("Only SELECT / WITH (read-only) queries are allowed here.")
        else:
            try:
                df = run_query(sql_text)
                st.success(f"{len(df)} rows returned")
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Query failed: {e}")
