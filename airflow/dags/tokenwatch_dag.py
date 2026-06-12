from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import sys
import os

default_args = {
    'owner': 'riya',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_simulator():
    subprocess.run([sys.executable, 
        'C:/Users/RIYA/Documents/tokenwatch/ingestion/simulator.py'], 
        check=True)

def run_dbt():
    subprocess.run(['dbt', 'run', '--project-dir', 
        'C:/Users/RIYA/Documents/tokenwatch'], 
        check=True)

def run_slack_alerts():
    subprocess.run([sys.executable, 
        'C:/Users/RIYA/Documents/tokenwatch/ingestion/slack_alerts.py'], 
        check=True)

with DAG(
    dag_id='tokenwatch_daily_pipeline',
    default_args=default_args,
    description='Daily TokenWatch pipeline — simulate, transform, alert',
    schedule='0 0 * * *',
    start_date=datetime(2026, 6, 11),
    catchup=False,
    tags=['tokenwatch']
) as dag:

    task_simulate = PythonOperator(
        task_id='run_simulator',
        python_callable=run_simulator
    )

    task_dbt = PythonOperator(
        task_id='run_dbt',
        python_callable=run_dbt
    )

    task_alerts = PythonOperator(
        task_id='run_slack_alerts',
        python_callable=run_slack_alerts
    )

    task_simulate >> task_dbt >> task_alerts