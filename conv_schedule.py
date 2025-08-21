import pandas as pd
import json
from datetime import datetime

def convert_time(time_str):
    """
    Converts a time string (e.g. '5:00') into a standard HH:MM:SS format.
    Returns None if conversion fails.
    """
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%H:%M:%S")
    except Exception as e:
        print(f"Time conversion error for value '{time_str}': {e}")
        return None

def main():
    # Excel file name (update the filename if needed)
    excel_file = "PPD SCHDL.xlsx"
    df = pd.read_excel(excel_file, header=0)
    
    # Rename columns to match Django Schedule model fields:
    # Excel columns:
    # Service Type, SCHEDULE NO, DUTY, Trip No, Departure Time,
    # Departure Place, Via, Dest. Place, Destn. Time, Km., Route no.
    # Mapping:
    # service_type: "Service Type"
    # schedule_no: "SCHEDULE NO"
    # trip_no: "Trip No"
    # start_time: "Departure Time"
    # source: "Departure Place"
    # via: "Via"
    # destination: "Dest. Place"
    # end_time: "Destn. Time"
    # trip_km: "Km."
    # route_no: "Route no."
    
    df = df.rename(columns={
        "Service Type": "service_type",
        "SCHEDULE NO": "schedule_no",
        "Trip No": "trip_no",
        "Departure Time": "start_time",
        "Departure Place": "source",
        "Via": "via",
        "Dest. Place": "destination",
        "Destn. Time": "end_time",
        "Km.": "trip_km",
        "Route no.": "route_no"
    })

    # Drop the unnecessary column (DUTY)
    if "DUTY" in df.columns:
        df = df.drop(columns=["DUTY"])
    
    fixture_data = []
    pk_counter = 1  # Primary key counter for each record

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        fields = {
            "service_type": row["service_type"],
            "schedule_no": row["schedule_no"],
            "trip_no": int(row["trip_no"]) if pd.notnull(row["trip_no"]) else None,
            "start_time": convert_time(str(row["start_time"])) if pd.notnull(row["start_time"]) else None,
            "end_time": convert_time(str(row["end_time"])) if pd.notnull(row["end_time"]) else None,
            "source": row["source"],
            "destination": row["destination"],
            "via": row["via"] if pd.notnull(row["via"]) else "",
            "trip_km": float(row["trip_km"]) if pd.notnull(row["trip_km"]) else None,
            "route_no": row["route_no"]
        }

        fixture_data.append({
            "model": "bus_route.schedule",  # Update with your actual app and model name
            "pk": pk_counter,
            "fields": fields
        })
        pk_counter += 1
    
    # Write the fixture data to a JSON file.
    json_file = "ppd_schedule_fixture.json"
    with open(json_file, "w") as f:
        json.dump(fixture_data, f, indent=4)
    
    print(f"JSON fixture file '{json_file}' created successfully with {len(fixture_data)} records.")

if __name__ == "__main__":
    main()
