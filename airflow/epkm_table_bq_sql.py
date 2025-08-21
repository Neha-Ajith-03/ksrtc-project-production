import os
import django
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.operators.python import PythonOperator
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

# Django Setup
DJANGO_PROJECT_PATH = "/home/jeev/ff_project/new_ksrtc/last_version_ksrtc"
sys.path.append(DJANGO_PROJECT_PATH)  # Ensure Django project path is added

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ksrtc1.settings")
django.setup()

# Import Django models after setting up Django
from bus_route.models import Trip

# BigQuery Constants
GCP_PROJECT_ID = "enhanced-cable-447317-h8"
BQ_DATASET = "ksrtc_dataset"

# Queries to fetch data
SQL_QUERY = f"""
SELECT 
    CAST(TICKET_ISSUE_DATE AS DATE) AS date,
    SCHEDULE_NUMBER AS schedule_no,
    TRIP_NUMBER AS trip_no,
    SUM(amount) AS revenue  -- Total revenue per trip
FROM `enhanced-cable-447317-h8.ksrtc_dataset.ksrtc_table_with_amount`
WHERE 
    TICKET_ISSUE_DATE IS NOT NULL
    AND SCHEDULE_NUMBER IS NOT NULL
    AND TRIP_NUMBER IS NOT NULL
    AND amount IS NOT NULL
    AND TRIP_KM IS NOT NULL
GROUP BY date, schedule_no, trip_no
ORDER BY date, schedule_no, trip_no;
"""

# Function to fetch data from BigQuery and insert into SQLite
def save_bigquery_data_to_sqlite(query):
    client = bigquery.Client()
    df = client.query(query).to_dataframe()  # Convert BigQuery result to Pandas DataFrame
    
    # Convert the date column to proper date objects
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce').dt.date

    if df.empty:
        print(f"[INFO] No data fetched from BigQuery!")
        return
    
    print(f"[INFO] Fetched {len(df)} rows from BigQuery")

    # Insert data into SQLite using Django ORM
    for index, row in df.iterrows():
        Trip.objects.update_or_create(
            date=row["date"],
            schedule_no=row["schedule_no"],
            trip_no=row["trip_no"],
            defaults={"revenue": row["revenue"]}  # Update revenue if record already exists
        )
    print(f"[INFO] Data inserted/updated successfully!")

# Define DAG
default_args = {
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
}

with DAG(
    dag_id="epkm_bigquery_to_sqlite",
    default_args=default_args,
    schedule="00 10 * * *",  # Run daily at 10:00 AM
    catchup=False,
) as dag:
    
    # BigQuery Query Task
    run_query = BigQueryInsertJobOperator(
        task_id="run_query",
        configuration={"query": {"query": SQL_QUERY, "useLegacySql": False}},
        gcp_conn_id="google_cloud_default"
    )
    
    # Save to SQLite Task
    save_sqlite = PythonOperator(
        task_id="save_to_sqlite",
        python_callable=save_bigquery_data_to_sqlite,
        op_args=[SQL_QUERY]
    )

    # Define dependencies
    run_query >> save_sqlite
