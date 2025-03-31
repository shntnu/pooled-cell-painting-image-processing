#!/bin/bash

# Create output directory
mkdir -p filtered_output
mkdir -p logs

echo "=== Running examples with different log levels ==="

# Example 1: Filter pipeline 1 (no cycle filtering) with INFO logging
echo -e "\n\n=== Example 1: Pipeline 1 with INFO logging ==="
python filter_csv.py \
    ../supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline1.csv \
    filtered_output/filtered_pipeline1.csv \
    --wells WellA1 \
    --sites 0000 \
    --plates Plate1 \
    --log-level INFO

# Example 2: Filter pipeline 5 (row-wise cycle filtering) with DEBUG logging
echo -e "\n\n=== Example 2: Pipeline 5 with DEBUG logging ==="
python filter_csv.py \
    ../supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline5.csv \
    filtered_output/filtered_pipeline5.csv \
    --cycles 1 \
    --wells WellA1 \
    --plates Plate1 \
    --log-level DEBUG

# Example 3: Filter pipeline 6 (column-wise cycle filtering) with DEBUG logging
echo -e "\n\n=== Example 3: Pipeline 6 with DEBUG logging ==="
python filter_csv.py \
    ../supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline6.csv \
    filtered_output/filtered_pipeline6.csv \
    --cycles 1 2 \
    --wells WellA1 \
    --plates Plate1 \
    --log-level DEBUG

echo -e "\n\nAll examples completed. Check the filtered_output directory for results."
echo "Log files can be found in the logs directory." 