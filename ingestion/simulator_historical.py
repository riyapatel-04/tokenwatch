import snowflake.connector
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv()
fake = Faker()

TEAMS = ["Data Engineering", "Product", "Marketing", "Support", "Sales"]
PROVIDERS = {"claude-sonnet": "Anthropic", "claude-haiku": "Anthropic", "gpt-4o": "OpenAI", "gpt-3.5-turbo": "OpenAI", "gemini-pro": "Google"}
TASK_TYPES = ["code_generation", "data_analysis", "email_drafting", "ticket_triage", "report_summary", "sql_generation"]

COST_PER_1K = {
    "claude-sonnet": 0.003,
    "claude-haiku": 0.00025,
    "gpt-4o": 0.005,
    "gpt-3.5-turbo": 0.0015,
    "gemini-pro": 0.00035
}

TEAM_PROFILES = {
    "Data Engineering": {"models": ["claude-haiku", "gpt-3.5-turbo"], "input_range": (300, 800), "output_range": (400, 1200)},
    "Support":          {"models": ["claude-haiku", "gemini-pro"],    "input_range": (200, 500), "output_range": (300, 900)},
    "Product":          {"models": ["claude-sonnet", "gpt-4o"],       "input_range": (400, 1000), "output_range": (300, 700)},
    "Sales":            {"models": ["gpt-4o", "gpt-4o"],              "input_range": (500, 1500), "output_range": (200, 500)},
    "Marketing":        {"models": ["gpt-4o", "claude-sonnet"],       "input_range": (600, 2000), "output_range": (200, 400)},
}

ENGINEERS = {
    "Data Engineering": [fake.name() for _ in range(3)],
    "Support":          [fake.name() for _ in range(3)],
    "Product":          [fake.name() for _ in range(3)],
    "Sales":            [fake.name() for _ in range(3)],
    "Marketing":        [fake.name() for _ in range(3)],
}

def generate_record(date, week_number):
    team = random.choice(TEAMS)
    profile = TEAM_PROFILES[team]
    model = random.choice(profile["models"])
    task = random.choice(TASK_TYPES)

    spike_multiplier = 1 + (week_number * 0.4)
    input_tokens = int(random.randint(*profile["input_range"]) * spike_multiplier)
    output_tokens = int(random.randint(*profile["output_range"]) * spike_multiplier)
    total_tokens = input_tokens + output_tokens
    cost = round((total_tokens / 1000) * COST_PER_1K[model], 6)

    return (
        str(uuid.uuid4()),
        date,
        random.choice(["TokenWatch", "JobLens", "CareSignal"]),
        team,
        random.choice(ENGINEERS[team]),
        model,
        PROVIDERS[model],
        task,
        input_tokens,
        output_tokens,
        total_tokens,
        cost,
        random.randint(200, 3000),
        random.random() > 0.05
    )

def run_historical_simulator():
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

    cursor = conn.cursor()
    records = []
    start_date = datetime.now() - timedelta(days=90)

    for day in range(90):
        current_date = start_date + timedelta(days=day)
        week_number = day // 7
        daily_calls = int(random.randint(40, 80) * (1 + week_number * 0.3))

        for _ in range(daily_calls):
            records.append(generate_record(current_date, week_number))

    cursor.executemany("""
        INSERT INTO TOKEN_USAGE_RAW VALUES 
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, records)

    conn.commit()
    print(f"Inserted {len(records)} historical records successfully!")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_historical_simulator()