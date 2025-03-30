#!/bin/bash

# Create output directory
mkdir -p filtered_output

# Example 1: Filter pipeline 1 (no cycle filtering)
python filter_csv.py \
    docs/supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline1.csv \
    filtered_output/filtered_pipeline1.csv \
    --wells WellA1 \
    --sites 0000 \
    --plates Plate1

# Example 2: Filter pipeline 5 (row-wise cycle filtering)
python filter_csv.py \
    docs/supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline5.csv \
    filtered_output/filtered_pipeline5.csv \
    --cycles 1 \
    --wells WellA1 \
    --plates Plate1

# Example 3: Filter pipeline 6 (column-wise cycle filtering)
python filter_csv.py \
    docs/supporting_files/load_data_csv_headers_and_first_row/header_and_first_row_load_data_pipeline6.csv \
    filtered_output/filtered_pipeline6.csv \
    --cycles 1 2 \
    --wells WellA1 \
    --plates Plate1

echo "All examples completed. Check the filtered_output directory for results." 