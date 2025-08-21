from google.cloud import bigquery
from django.conf import settings
import pandas as pd
import logging
from bus_route.models import Route, Schedule  # Add Schedule import here

logger = logging.getLogger(__name__)

def get_bigquery_client():
    """Return an authenticated BigQuery client"""
    try:
        return bigquery.Client()
    except Exception as e:
        logger.error(f"Failed to create BigQuery client: {e}")
        raise

def fetch_trip_revenue_data(schedule_no, trip_no, date=None):
    """Fetch revenue data for a specific trip from BigQuery"""
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        SCHEDULE_NUMBER, 
        TRIP_NUMBER,
        TICKET_ISSUE_DATE,
        FROM_STOP_NAME,
        TO_STOP_NAME,
        SUM(TOTAL_PASSENGER) AS PASSENGERS,
    FROM `{settings.GCP_PROJECT_ID}.{settings.BQ_DATASET}.{settings.BQ_TABLE}`
    WHERE SCHEDULE_NUMBER = '{schedule_no.upper()}'
      AND TRIP_NUMBER = {trip_no}
    """
    
    if date:
        query += f" AND TICKET_ISSUE_DATE = '{date}'"
        
    query += """
    GROUP BY SCHEDULE_NUMBER, TRIP_NUMBER, TICKET_ISSUE_DATE, FROM_STOP_NAME, TO_STOP_NAME
    ORDER BY TICKET_ISSUE_DATE
    """
    
    try:
        logger.info(f"Executing BigQuery query for schedule {schedule_no}, trip {trip_no}")
        return client.query(query).to_dataframe()
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        # Return empty DataFrame instead of raising exception
        return pd.DataFrame()

def calculate_fare_stage_revenue(schedule_no, trip_no, date=None):
    """Calculate revenue for each fare stage"""
    try:
        # Get revenue data
        df = fetch_trip_revenue_data(schedule_no, trip_no, date)
        if df.empty:
            return pd.DataFrame()
            
        # Try to get route data from the database to identify fare stages
        routes = Route.objects.filter(
            route_no=(
                Schedule.objects.filter(schedule_no=schedule_no.upper(), trip_no=trip_no)
                .first().route_no if Schedule.objects.filter(schedule_no=schedule_no.upper(), trip_no=trip_no).exists() else ""
            )
        ).order_by('order_sequence')
        
        # If routes exist, mark fare stages in the revenue data
        fare_stages = []
        if routes:
            for route in routes:
                if route.fare_stage:
                    fare_stages.append(route.stop_name)
            
            # Add fare_stage column to DataFrame
            df['IS_FARE_STAGE'] = df['TO_STOP_NAME'].apply(lambda x: x in fare_stages)
            
        return df
    except Exception as e:
        logger.error(f"Error calculating fare stage revenue: {e}")
        return pd.DataFrame()