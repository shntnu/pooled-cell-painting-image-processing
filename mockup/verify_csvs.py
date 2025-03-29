#!/usr/bin/env python3

"""
Verification script for the CellProfiler Pipeline Mockup Generator
This script checks if the generated CSV files match the expected structure
based on the io.json specification.
"""

import os
import json
import csv
import argparse
import glob
from pathlib import Path


def validate_csv_structure(io_json_path, csv_dir):
    """Validate that the generated CSV files match the expected structure"""
    # Load the io.json specification
    with open(io_json_path, "r") as f:
        io_specs = json.load(f)

    # Find all CSV files in the directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    # Track validation results
    validation_results = {}

    for csv_path in csv_files:
        csv_filename = os.path.basename(csv_path)
        pipeline_name = csv_filename.split("_LoadData.csv")[0]

        if pipeline_name not in io_specs:
            validation_results[csv_filename] = {
                "status": "Error",
                "message": f"No matching pipeline '{pipeline_name}' found in io.json",
            }
            continue

        pipeline_spec = io_specs[pipeline_name]

        if "load_data_csv_fields" not in pipeline_spec:
            validation_results[csv_filename] = {
                "status": "Warning",
                "message": f"Pipeline '{pipeline_name}' does not specify load_data_csv_fields",
            }
            continue

        # Get expected fields from the spec
        expected_fields = set()
        for field in pipeline_spec["load_data_csv_fields"]:
            field_name = field["name"]
            # For fields with placeholders, we'll check the pattern below
            if "{" not in field_name:
                expected_fields.add(field_name)

        # Read CSV to check its structure
        with open(csv_path, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)

            if not header:
                validation_results[csv_filename] = {
                    "status": "Error",
                    "message": "CSV file is empty",
                }
                continue

            # Check fields with placeholders (like FileName_Orig{Channel})
            placeholder_fields = [
                f for f in pipeline_spec["load_data_csv_fields"] if "{" in f["name"]
            ]
            for field in placeholder_fields:
                field_pattern = field["name"]
                field_parts = field_pattern.split("{")
                prefix = field_parts[0]
                suffix = field_parts[1].split("}")[1] if "}" in field_parts[1] else ""

                found_match = False
                for col in header:
                    if col.startswith(prefix) and col.endswith(suffix):
                        found_match = True
                        break

                if not found_match:
                    expected_fields.add(field_pattern + " (no match found)")

            # Check actual vs expected fields
            actual_fields = set(header)
            missing_fields = expected_fields - actual_fields
            unexpected_fields = actual_fields - expected_fields

            # Check for rows
            row_count = sum(1 for _ in reader)

            validation_results[csv_filename] = {
                "status": "Valid" if not missing_fields else "Error",
                "row_count": row_count,
                "header_count": len(header),
                "missing_fields": list(missing_fields) if missing_fields else "None",
                "unexpected_fields": list(unexpected_fields)
                if unexpected_fields
                else "None",
            }

    return validation_results


def display_results(results):
    """Display validation results in a readable format"""
    print("\n=== CSV Validation Results ===\n")

    valid_count = sum(1 for r in results.values() if r["status"] == "Valid")
    error_count = sum(1 for r in results.values() if r["status"] == "Error")
    warning_count = sum(1 for r in results.values() if r["status"] == "Warning")

    print(f"Total CSV files: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")
    print("")

    for filename, result in results.items():
        status_color = ""
        if result["status"] == "Valid":
            status_color = "\033[92m"  # Green
        elif result["status"] == "Warning":
            status_color = "\033[93m"  # Yellow
        else:
            status_color = "\033[91m"  # Red

        print(f"{status_color}{result['status']}\033[0m: {filename}")

        if "message" in result:
            print(f"  Message: {result['message']}")

        if "row_count" in result:
            print(f"  Rows: {result['row_count']}")
            print(f"  Header columns: {result['header_count']}")

            if result["missing_fields"] != "None":
                print(f"  Missing fields: {', '.join(result['missing_fields'])}")

            if (
                result["unexpected_fields"] != "None"
                and len(result["unexpected_fields"]) <= 5
            ):
                print(f"  Extra fields: {', '.join(result['unexpected_fields'])}")
            elif result["unexpected_fields"] != "None":
                print(f"  Extra fields: {len(result['unexpected_fields'])} fields")

        print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate CellProfiler LoadData CSV files"
    )
    parser.add_argument("--io_json", required=True, help="Path to the io.json file")
    parser.add_argument(
        "--csv_dir", required=True, help="Directory containing the generated CSV files"
    )

    args = parser.parse_args()

    results = validate_csv_structure(args.io_json, args.csv_dir)
    display_results(results)
