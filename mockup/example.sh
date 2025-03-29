#!/bin/bash

# Example script for generating a minimal mockup for testing

# Create a minimal mockup with just essential parameters
python create_mockup.py \
  --io_json ../docs/io.json \
  --output_dir ./test_mockup \
  --plates Plate1 \
  --wells A01 A02 \
  --sites 1 2 \
  --channels DNA ER \
  --cycles 1 2

echo "Minimal test mockup created in ./test_mockup"
echo "LoadData CSV files are in ./test_mockup/csvs"

# Optional: List the created directory structure
echo "Directory structure:"
find ./test_mockup -type d | sort | head -n 10
echo "... and more directories"

# Optional: Count the number of mock files created
echo "Number of mock files created:"
find ./test_mockup -type f | wc -l 