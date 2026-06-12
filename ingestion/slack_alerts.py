import requests
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

def send_slack_message(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    response = requests.post(webhook_url, json={"text": message})
    return response

def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

def get_snowflake_data():
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ROUND(SUM(COST_USD), 2) FROM TOKENWATCH.RAW.TOKEN_USAGE_RAW")
    total_spend = cursor.fetchone()[0]

    cursor.execute("""
        SELECT TEAM, ROUND(AVG(ROI_SCORE), 1) AS AVG_ROI
        FROM TOKENWATCH.RAW.MART_TEAM_ROI
        GROUP BY TEAM
        ORDER BY AVG_ROI ASC
        LIMIT 1
    """)
    worst_team, worst_roi = cursor.fetchone()

    conn.close()
    return total_spend, worst_team, worst_roi

def get_top_spender():
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ENGINEER, TEAM, ROUND(SUM(COST_USD), 2) AS TOTAL_SPEND, MAX(MODEL) AS TOP_MODEL
        FROM TOKENWATCH.RAW.TOKEN_USAGE_RAW
        GROUP BY 1, 2
        ORDER BY TOTAL_SPEND DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    return result

def run_alerts():
    total_spend, worst_team, worst_roi = get_snowflake_data()
    top_engineer, eng_team, eng_spend, eng_model = get_top_spender()

    budget = 500
    remaining = budget - total_spend
    daily_burn = total_spend / 90
    runway_days = int(remaining / daily_burn)

    alerts = []

    if runway_days <= 14:
        alerts.append(f"""🚨 *Budget Alert* — Only *{runway_days} days* of budget remaining!
Current spend: *${total_spend:,.2f}* / *${budget:,.2f}* budget
At this rate budget runs out soon. Review AI usage immediately.""")

    if worst_roi <= 3:
        alerts.append(f"""⚠️ *ROI Alert* — *{worst_team}* has critically low ROI of *{worst_roi}/10*
They are overspending on expensive models with poor output.
Recommendation: Switch to Claude Haiku immediately.""")

    alerts.append(f"""👤 *Top Spender This Month* — *{top_engineer}* ({eng_team})
Spent *${eng_spend}* using *{eng_model}*
Review their AI task types to ensure productive usage.""")

    if not alerts:
        alerts.append(f"""✅ *TokenWatch Daily Check* — All systems normal!
Total spend: *${total_spend:,.2f}* | Budget runway: *{runway_days} days* | Worst ROI: *{worst_team} ({worst_roi}/10)*""")

    for alert in alerts:
        send_slack_message(alert)
        print(f"Sent alert: {alert[:50]}...")

if __name__ == "__main__":
    run_alerts()