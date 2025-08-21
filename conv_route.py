import pandas as pd
import json
import os
import traceback

def excel_to_json_folder(input_folder, output_file):
    json_data = []
    route_id = 1  # Auto-increment ID for Route
    error_log_file = "error_log.txt"

    # Clear previous error log
    with open(error_log_file, "w") as f:
        f.write("")
    arr = []
    # Iterate through all Excel files in the folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            excel_file = os.path.join(input_folder, filename)
            print(f"Processing file: {filename}")

            try:
                xls = pd.ExcelFile(excel_file)
                sheet_count = 0
                
                for sheet_name in xls.sheet_names:
                    sheet_count += 1
                    header_found = False
                    df = None
                    arr.append(sheet_name)
                    # Try header rows 3, 4, and 5 (0-based indexes: 2,3,4)
                    for header_row in [2, 3, 4]:
                        try:
                            temp_df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
                            # Check if we have at least 5 columns
                            if temp_df.shape[1] >= 5:
                                df = temp_df
                                header_found = True
                                print(f"Using header row {header_row+1} for sheet: {sheet_name}")
                                break
                        except Exception as e:
                            # If error occurs, try the next header candidate
                            continue

                    if not header_found or df is None:
                        error_message = f"Could not determine header row in sheet {sheet_name} of {filename}\n"
                        print(error_message)
                        with open(error_log_file, "a") as log:
                            log.write(error_message)
                        continue  # Skip this sheet if no proper header is found

                    route_no = sheet_name.strip().upper()
                    
                    for index, row in df.iterrows():
                        try:
                            # Use .iloc for positional indexing
                            order_sequence = int(row.iloc[0])  # Expected Column A
                            stop_name = str(row.iloc[1]).strip()  # Expected Column B
                            stop_latitude = float(row.iloc[2])  # Expected Column C
                            stop_longitude = float(row.iloc[3])  # Expected Column D
                            fare_stage = str(row.iloc[4]).strip().lower() in ['true', '1', 'yes']  # Expected Column E

                            json_data.append({
                                "model": "bus_route.route",
                                "pk": route_id,
                                "fields": {
                                    "route_no": route_no,
                                    "order_sequence": order_sequence,
                                    "stop_name": stop_name,
                                    "stop_latitude": stop_latitude,
                                    "stop_longitude": stop_longitude,
                                    "fare_stage": fare_stage
                                }
                            })
                            route_id += 1

                        except Exception as e:
                            error_message = f"Skipping row {index} in {filename} ({sheet_name}) due to error: {e}\n"
                            print(error_message)
                            with open(error_log_file, "a") as log:
                                log.write(error_message + traceback.format_exc() + "\n")
                                
                with open(error_log_file, "a") as log:
                    log.write(f"Processed {sheet_count} sheets in {filename}\n")
            except Exception as e:
                error_message = f"Error processing {filename}: {e}\n"
                print(error_message)
                with open(error_log_file, "a") as log:
                    log.write(error_message + traceback.format_exc() + "\n")

    # Save JSON to file
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

    print(f"JSON file saved to {output_file}")
    print(f"Error log saved to {error_log_file}")
    print(arr)
# Example usage
input_folder = "route_folder/"  # Replace with your actual folder path
output_file = "routes.json"
excel_to_json_folder(input_folder, output_file)
