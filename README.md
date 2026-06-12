# 🔍 TokenWatch — AI Cost & ROI Intelligence Dashboard

> *Inspired by the real Microsoft & Uber token cost explosion of 2026*

## 📌 The Problem

In May 2026, Microsoft canceled Claude Code licenses for its engineers due to skyrocketing token costs. Uber burned through its entire 2026 AI coding budget in just four months. The root cause wasn't that the tools failed — it was that **nobody was watching the bill**.

Companies had no visibility into:
- Which teams were spending the most on AI
- Whether that spending was generating value (ROI)
- When the budget would run out
- Which engineers were driving costs

**TokenWatch was built to solve exactly this.**

---

## 🎯 What TokenWatch Does

TokenWatch is a fully automated AI cost and ROI intelligence platform that:

- 📊 Tracks token usage and costs across multiple AI providers (OpenAI, Anthropic, Google)
- 🧮 Calculates ROI scores per team based on output quality vs cost
- 🔥 Identifies top spending engineers and most efficient engineers
- ⏳ Predicts budget runway before it runs out
- 🚨 Sends automated Slack alerts when thresholds are breached
- 🔄 Updates daily via an automated Airflow pipeline

---

## 🏗️ Architecture

```
simulator.py (daily)
      ↓
Snowflake (TOKEN_USAGE_RAW)
      ↓
dbt (staging + mart models)
      ↓
Streamlit Dashboard
      ↓
Slack Alerts
```

### Full Pipeline (runs daily via Airflow at 8PM EST)

```
Task 1: simulator.py
→ Adds new daily rows to Snowflake

Task 2: dbt run
→ Refreshes all mart tables
→ Rolling 90 day window slides forward

Task 3: slack_alerts.py
→ Checks budget runway, ROI scores, top spender
→ Sends alerts to #tokenwatch-alerts Slack channel
```

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data Generation | Python + Faker | Simulates realistic AI API usage |
| Data Warehouse | Snowflake | Stores raw and transformed data |
| Transformation | dbt | Cleans and aggregates raw data into marts |
| Orchestration | Apache Airflow | Runs the pipeline daily automatically |
| Dashboard | Streamlit + Plotly | Visualizes costs, ROI and insights |
| Alerts | Slack Webhooks | Notifies team of critical thresholds |
| Deployment | Streamlit Cloud | Live public dashboard |
| Version Control | GitHub + GitHub Actions | CI/CD pipeline |

---

## 📊 Dashboard Features

### Metric Cards
- **Total Spend** — cumulative cost over rolling 90 days
- **Tokens Used** — total tokens consumed across all teams
- **Avg ROI Score** — average ROI score out of 10 across all teams
- **Budget Runway** — days until budget is exhausted at current burn rate

### Charts
- **Monthly Cost Trend** — daily cost line chart showing the cost explosion over time
- **Spend by Provider** — pie chart showing OpenAI vs Anthropic vs Google spend breakdown
- **ROI by Team** — table showing which teams get the most value per dollar
- **Model Usage by Team** — stacked bar showing which models each team uses

### Team Scorecards
- Color coded cards (🟢 Gold Standard / 🟡 Needs Improvement / 🔴 Critical)
- Shows ROI score, total spend, primary model and actionable recommendation per team

### Engineer Leaderboard
- **Top Spenders** — engineers with highest AI spend
- **Most Efficient Engineers** — engineers with highest output per dollar

---

## 🚨 Slack Alert System

Three types of automated alerts:

| Alert | Trigger | Example |
|---|---|---|
| 🚨 Budget Critical | Runway ≤ 14 days | "Only 12 days of budget remaining!" |
| ⚠️ ROI Critical | Team ROI ≤ 3.0 | "Marketing has critically low ROI of 2.2/10" |
| 👤 Top Spender | Daily | "Levi Jimenez (Sales) spent $27 using GPT-4o" |

---

## 📁 Project Structure

```
tokenwatch/
│
├── ingestion/
│   ├── simulator.py              # Daily data generator (1 day)
│   ├── simulator_historical.py   # One-time 90 day seed data
│   └── slack_alerts.py           # Automated Slack notifications
│
├── models/
│   ├── staging/
│   │   ├── stg_token_usage.sql   # Clean raw data, rolling 90 day filter
│   │   └── sources.yml           # Snowflake source definitions
│   └── marts/
│       ├── mart_daily_cost.sql         # Daily cost by provider/model
│       ├── mart_team_roi.sql           # ROI scores per team per week
│       ├── mart_provider_breakdown.sql # Spend breakdown by AI provider
│       └── mart_team_model_usage.sql   # Model usage counts per team
│
├── dashboard/
│   └── app.py                    # Streamlit dashboard
│
├── airflow/
│   └── dags/
│       └── tokenwatch_dag.py     # Daily pipeline DAG
│
├── .env                          # Snowflake credentials (not committed)
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Snowflake account
- Slack workspace (for alerts)

### 1. Clone the repo

```bash
git clone https://github.com/riyapatel-04/tokenwatch.git
cd tokenwatch
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=TOKENWATCH
SNOWFLAKE_SCHEMA=RAW
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
```

### 4. Set up Snowflake

Run in Snowflake:

```sql
CREATE DATABASE IF NOT EXISTS TOKENWATCH;
CREATE SCHEMA IF NOT EXISTS TOKENWATCH.RAW;

CREATE OR REPLACE TABLE TOKENWATCH.RAW.TOKEN_USAGE_RAW (
    event_id        VARCHAR(36),
    event_timestamp TIMESTAMP_NTZ,
    project         VARCHAR(50),
    team            VARCHAR(50),
    engineer        VARCHAR(50),
    model           VARCHAR(50),
    provider        VARCHAR(20),
    task_type       VARCHAR(50),
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    total_tokens    INTEGER,
    cost_usd        FLOAT,
    duration_ms     INTEGER,
    was_successful  BOOLEAN
);
```

### 5. Load historical data

```bash
python ingestion/simulator_historical.py
```

### 6. Run dbt models

```bash
dbt run
```

### 7. Launch dashboard

```bash
cd dashboard
streamlit run app.py
```

### 8. Set up Airflow (optional)

```bash
# Inside WSL Ubuntu
airflow standalone
```

Copy the DAG:
```bash
cp airflow/dags/tokenwatch_dag.py ~/airflow/dags/
```

---

## 📈 ROI Score Calculation

ROI score is calculated in `mart_team_roi.sql`:

```sql
ROI Score = (output_tokens / cost_usd) normalized to 0-10 scale
```

Higher output per dollar = higher ROI score. Teams using cheap models (Claude Haiku, Gemini Pro) with high output naturally score higher than teams using expensive models (GPT-4o) with lower output.

---

## 🔄 Rolling 90 Day Window

The `stg_token_usage.sql` staging model filters data to always show the last 90 days:

```sql
WHERE event_timestamp >= DATEADD(day, -90, CURRENT_DATE)
```

As Airflow adds new daily data, the oldest day automatically drops off — keeping the dashboard always showing the most recent 90 days.

---

## 🌐 Live Demo

[TokenWatch Live Dashboard](https://tokenwatch.streamlit.app)

---

## 👩‍💻 Author

**Riya Patel**

- [LinkedIn](https://linkedin.com/in/riyapatel)
- [GitHub](https://github.com/riyapatel-04)
