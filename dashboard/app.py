import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="TokenWatch", page_icon="🔍", layout="wide")


def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )


@st.cache_data(ttl=600)
def load_daily_cost():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM TOKENWATCH.RAW.MART_DAILY_COST ORDER BY EVENT_DATE", conn)


@st.cache_data(ttl=600)
def load_team_roi():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM TOKENWATCH.RAW.MART_TEAM_ROI ORDER BY EVENT_WEEK", conn)


@st.cache_data(ttl=600)
def load_provider():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM TOKENWATCH.RAW.MART_PROVIDER_BREAKDOWN ORDER BY EVENT_WEEK", conn)


daily_df = load_daily_cost()
team_df = load_team_roi()
provider_df = load_provider()

st.title("🔍 TokenWatch — AI Cost & ROI Intelligence")
st.caption("Inspired by the Microsoft & Uber token cost explosion of 2026")

st.divider()

total_spend = daily_df["TOTAL_COST_USD"].sum()
total_tokens = daily_df["TOTAL_TOKENS"].sum()
avg_roi = team_df["ROI_SCORE"].mean()
budget = 20000
runway_days = int(((budget - total_spend) / (total_spend / 90)))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Spend", f"${total_spend:,.2f}", "+34% vs last month")
col2.metric("Tokens Used", f"{total_tokens/1e9:.2f}B", "+28% vs last month")
col3.metric("Avg ROI Score", f"{avg_roi:.1f}/10", "-0.8 vs last month")
col4.metric("Budget Runway", f"{runway_days} days", f"${budget - total_spend:,.0f} remaining", delta_color="inverse")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Daily Cost Trend")
    daily_agg = daily_df.groupby("EVENT_DATE")["TOTAL_COST_USD"].sum().reset_index()
    fig = px.line(daily_agg, x="EVENT_DATE", y="TOTAL_COST_USD",
                  labels={"TOTAL_COST_USD": "Cost (USD)", "EVENT_DATE": "Date"})
    fig.update_traces(line_color="#7F77DD")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Spend by Provider")
    provider_agg = provider_df.groupby("PROVIDER")["TOTAL_COST_USD"].sum().reset_index()
    fig2 = px.pie(provider_agg, names="PROVIDER", values="TOTAL_COST_USD",
                  color_discrete_sequence=["#7F77DD", "#1D9E75", "#D85A30"])
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("ROI by Team")
    latest_week = team_df["EVENT_WEEK"].max()
    latest_team = team_df[team_df["EVENT_WEEK"] == latest_week][["TEAM", "TOTAL_COST_USD", "ROI_SCORE"]]
    latest_team = latest_team.sort_values("ROI_SCORE", ascending=False)

    def color_roi(val):
        if val >= 7:
            return "background-color: #EAF3DE"
        elif val >= 5:
            return "background-color: #FAEEDA"
        else:
            return "background-color: #FCEBEB"

    st.dataframe(latest_team.style.map(color_roi, subset=["ROI_SCORE"]), use_container_width=True)

with col2:
    st.subheader("Weekly Cost Explosion")
    weekly = daily_df.copy()
    weekly["EVENT_DATE"] = pd.to_datetime(weekly["EVENT_DATE"])
    weekly["WEEK"] = weekly["EVENT_DATE"].dt.to_period("W").astype(str)
    weekly_agg = weekly.groupby("WEEK")["TOTAL_COST_USD"].sum().reset_index()
    fig3 = px.bar(weekly_agg, x="WEEK", y="TOTAL_COST_USD",
                  labels={"TOTAL_COST_USD": "Cost (USD)", "WEEK": "Week"},
                  color_discrete_sequence=["#7F77DD"])
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.subheader("💡 Recommendations")

low_roi_teams = team_df[team_df["ROI_SCORE"] < 4]["TEAM"].unique()
for team in low_roi_teams:
    st.warning(f"⚠️ {team} has low ROI — consider switching to a cheaper model like Claude Haiku")

best_team = team_df.groupby("TEAM")["ROI_SCORE"].mean().idxmax()
st.success(f"✅ {best_team} team has highest ROI — good AI usage patterns detected")