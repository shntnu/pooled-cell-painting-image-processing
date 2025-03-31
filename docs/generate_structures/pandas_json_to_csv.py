import json
import pandas as pd
import os

# Create output directory
os.makedirs("csv_output", exist_ok=True)

# Load the JSON file
with open("result.json", "r") as f:
    data = json.load(f)

# Process each section
for section_name, section_data in data.items():
    if not section_data:
        continue

    # Convert to DataFrame and save as CSV in one step
    df = pd.DataFrame(section_data)
    output_file = f"csv_output/{section_name}.csv"
    df.to_csv(output_file, index=False)

    print(f"Created {output_file} with {len(df)} rows and {len(df.columns)} columns")

print("All CSV files have been saved to the 'csv_output' directory")
