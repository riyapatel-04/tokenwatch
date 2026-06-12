import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="TokenWatch", page_icon="💰", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #EEEAFF;
}
[data-testid="stHeader"] {
    background-color: #EEEAFF;
}
[data-testid="stMetricLabel"] {
    font-size: 100px !important;
    font-weight: 700 !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


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

@st.cache_data(ttl=600)
def load_team_model():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM TOKENWATCH.RAW.MART_TEAM_MODEL_USAGE", conn)

@st.cache_data(ttl=600)
def load_engineer_usage():
    conn = get_connection()
    return pd.read_sql("""
        SELECT 
            ENGINEER,
            TEAM,
            COUNT(*) AS TOTAL_CALLS,
            ROUND(SUM(TOTAL_TOKENS), 0) AS TOTAL_TOKENS,
            ROUND(SUM(COST_USD), 2) AS TOTAL_COST_USD,
            ROUND(AVG(OUTPUT_TOKENS * 1.0 / NULLIF(INPUT_TOKENS, 0)), 2) AS OUTPUT_RATIO,
            MAX(MODEL) AS TOP_MODEL
        FROM TOKENWATCH.RAW.TOKEN_USAGE_RAW
        GROUP BY 1, 2
        ORDER BY TOTAL_COST_USD DESC
    """, conn)

engineer_df = load_engineer_usage()

team_model_df = load_team_model()
daily_df = load_daily_cost()
team_df = load_team_roi()
provider_df = load_provider()

st.title("💰 TokenWatch - AI Cost & ROI Intelligence")
st.markdown("<p style='font-size:16px;color:gray;'>Inspired by the Microsoft & Uber token cost explosion of 2026</p>", unsafe_allow_html=True)

min_date = pd.to_datetime(daily_df["EVENT_DATE"].min()).strftime("%b %d, %Y")
max_date = pd.to_datetime(daily_df["EVENT_DATE"].max()).strftime("%b %d, %Y")
st.markdown(f"<p style='font-size:16px;color:gray;'>📅 Data range: {min_date} - {max_date}</p>", unsafe_allow_html=True)

st.divider()

total_spend = daily_df["TOTAL_COST_USD"].sum()
total_tokens = daily_df["TOTAL_TOKENS"].sum()
avg_roi = team_df["ROI_SCORE"].mean()
budget = 500
daily_burn = total_spend / 90
runway_days = int((budget - total_spend) / daily_burn)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="💰 Total Spend",
    value=f"${total_spend:,.2f}",
    delta=f"~${daily_burn:.2f}/day"
)

col2.metric(
    label="⚡ Tokens Used",
    value=f"{total_tokens/1e6:.0f}M",
    delta=f"{team_df['TEAM'].nunique()} teams"
)

col3.metric(
    label="📊 Avg ROI Score",
    value=f"{avg_roi:.1f}/10",
    delta=f"{'Good' if avg_roi >= 6 else 'Needs improvement' if avg_roi >= 4 else 'Critical'}",
    delta_color="normal" if avg_roi >= 6 else "inverse"
)

col4.metric(
    label="⏳ Budget Runway",
    value=f"{runway_days} days",
    delta=f"${budget - total_spend:,.0f} remaining",
    delta_color="inverse"
)


st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Cost Trend")
    daily_agg = daily_df.groupby("EVENT_DATE")["TOTAL_COST_USD"].sum().reset_index()
    fig = px.line(daily_agg, x="EVENT_DATE", y="TOTAL_COST_USD",
                  labels={"TOTAL_COST_USD": "Cost (USD)", "EVENT_DATE": "Month"})
    fig.update_traces(line_color="#7F77DD")
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
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
    min_week = pd.to_datetime(daily_df["EVENT_DATE"].min()).strftime("%b %d, %Y")
    max_week = pd.to_datetime(daily_df["EVENT_DATE"].max()).strftime("%b %d, %Y")
    st.caption(f"{min_week} — {max_week}")
    latest_team = team_df.groupby("TEAM").agg(
        TOTAL_COST_USD=("TOTAL_COST_USD", "sum"),
        ROI_SCORE=("ROI_SCORE", "mean")
    ).reset_index()
    latest_team["ROI_SCORE"] = latest_team["ROI_SCORE"].round(1)
    latest_team["TOTAL_COST_USD"] = latest_team["TOTAL_COST_USD"].round(2)
    latest_team = latest_team.sort_values("ROI_SCORE", ascending=False).reset_index(drop=True)

    def color_roi(val):
        if val >= 6:
            return "background-color: #EAF3DE"
        elif val >= 4:
            return "background-color: #FAEEDA"
        else:
            return "background-color: #FCEBEB"

    st.dataframe(
        latest_team.style.map(color_roi, subset=["ROI_SCORE"]).format({"ROI_SCORE": "{:.1f}", "TOTAL_COST_USD": "{:.2f}"}),
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader("Model usage by team")
    fig3 = px.bar(team_model_df, 
                  x="TEAM", 
                  y="TOTAL_CALLS",
                  color="MODEL",
                  labels={"TOTAL_CALLS": "Total calls", "TEAM": "Team", "MODEL": "Model"},
                  color_discrete_sequence=["#7F77DD", "#1D9E75", "#D85A30", "#378ADD", "#EF9F27"])
    fig3.update_layout(barmode="stack")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.subheader("💡 Team Scorecards")

dominant_model = team_model_df.groupby("TEAM").apply(
    lambda x: x.loc[x["TOTAL_CALLS"].idxmax(), "MODEL"]
).reset_index()
dominant_model.columns = ["TEAM", "DOMINANT_MODEL"]

scorecard_df = latest_team.merge(dominant_model, on="TEAM")
cols = st.columns(len(scorecard_df))

for i, row in scorecard_df.iterrows():
    roi = row["ROI_SCORE"]
    team = row["TEAM"]
    spend = row["TOTAL_COST_USD"]
    model = row["DOMINANT_MODEL"]
    potential_saving = round(spend * 0.4, 2)

    if roi >= 6:
        border_color = "#3B6D11"
        bg_color = "#F4FAF0"
        roi_color = "#3B6D11"
        badge_bg = "#EAF3DE"
        badge_color = "#3B6D11"
        status = "🏆 Gold standard"
        action = "Keep current approach"
    elif roi >= 4:
        border_color = "#854F0B"
        bg_color = "#FFFBF0"
        roi_color = "#854F0B"
        badge_bg = "#FAEEDA"
        badge_color = "#854F0B"
        status = "⚠️ Needs improvement"
        action = "Mix in cheaper models"
    else:
        border_color = "#A32D2D"
        bg_color = "#FFF8F8"
        roi_color = "#A32D2D"
        badge_bg = "#FCEBEB"
        badge_color = "#A32D2D"
        status = "🚨 Critical"
        action = f"Switch to Haiku — save ~${potential_saving}"

    with cols[i]:
        st.markdown(f"""
<div style="
    background: {bg_color};
    border: 1.5px solid {border_color};
    border-radius: 14px;
    padding: 20px 14px;
    text-align: center;
    height: 260px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
">
    <div>
        <div style="font-weight: 700; font-size: 15px; color: #1a1a1a; margin-bottom: 8px;">{team}</div>
        <div style="font-size: 32px; font-weight: 800; color: {roi_color}; line-height: 1;">{roi}<span style="font-size:14px;font-weight:500;color:gray;">/10</span></div>
        <div style="font-size: 11px; color: gray; margin-top: 6px;">ROI Score</div>
    </div>
    <div>
        <div style="font-size: 12px; color: #444; margin: 8px 0;">
            💰 <b>${spend}</b> &nbsp;|&nbsp; 🤖 <b>{model}</b>
        </div>
        <div style="
            display: inline-block;
            background: {badge_bg};
            color: {badge_color};
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 99px;
            margin-bottom: 8px;
        ">{status}</div>
        <div style="font-size: 11px; color: #555; font-style: italic;">{action}</div>
    </div>
</div>
""", unsafe_allow_html=True)    
        
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Top spenders")
    st.caption("Engineers with highest AI spend this period")
    top_spenders = engineer_df.head(5)[["ENGINEER", "TEAM", "TOTAL_COST_USD", "TOP_MODEL"]].copy()
    top_spenders["TOTAL_COST_USD"] = top_spenders["TOTAL_COST_USD"].round(2)
    top_spenders.columns = ["Engineer", "Team", "Spend ($)", "Primary Model"]
    st.dataframe(top_spenders, hide_index=True, use_container_width=True)

with col2:
    st.subheader("🌟 Most efficient engineers")
    st.caption("Engineers with highest output per dollar")
    engineer_df["OUTPUT_RATIO"] = pd.to_numeric(engineer_df["OUTPUT_RATIO"], errors='coerce')
    top_efficient = engineer_df.nlargest(5, "OUTPUT_RATIO")[["ENGINEER", "TEAM", "TOTAL_COST_USD", "OUTPUT_RATIO"]].copy()
    top_efficient["TOTAL_COST_USD"] = top_efficient["TOTAL_COST_USD"].round(2)
    top_efficient["OUTPUT_RATIO"] = top_efficient["OUTPUT_RATIO"].round(2)
    top_efficient.columns = ["Engineer", "Team", "Spend ($)", "Output Ratio"]
    st.dataframe(top_efficient, hide_index=True, use_container_width=True)