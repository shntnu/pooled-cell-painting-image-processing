#!/bin/bash

# Test script for the CellProfiler Pipeline Mockup Generator
# This script generates a mockup and then validates it

# Set paths
IO_JSON="../docs/io.json"
OUTPUT_DIR="./test_mockup"
CSV_DIR="${OUTPUT_DIR}/csvs"

# Clean up any previous test run
if [ -d "${OUTPUT_DIR}" ]; then
  echo "Removing previous test mockup..."
  rm -rf "${OUTPUT_DIR}"
fi

# Generate the mockup with only essential parameters
echo "Generating mockup..."
python create_mockup.py \
  --io_json "${IO_JSON}" \
  --output_dir "${OUTPUT_DIR}" \
  --plates Plate1 \
  --wells A01 B01 \
  --sites 1 2 \
  --channels DNA ER \
  --cycles 1 2 \
  --round_or_square square

# Check exit status
if [ $? -ne 0 ]; then
  echo "ERROR: Mockup generation failed!"
  exit 1
fi

echo "Mockup generation completed."

# Verify the generated CSVs
echo "Verifying CSV files..."
python verify_csvs.py --io_json "${IO_JSON}" --csv_dir "${CSV_DIR}"

# Check exit status
if [ $? -ne 0 ]; then
  echo "ERROR: CSV verification failed!"
  exit 1
fi

# Show folder structure stats
echo ""
echo "Folder structure statistics:"
echo "--------------------------"
echo "Total directories: $(find "${OUTPUT_DIR}" -type d | wc -l)"
echo "Total files: $(find "${OUTPUT_DIR}" -type f | wc -l)"
echo "Files by type:"
echo "  .csv: $(find "${OUTPUT_DIR}" -name "*.csv" | wc -l)"
echo "  .tiff: $(find "${OUTPUT_DIR}" -name "*.tiff" | wc -l)"
echo "  .png: $(find "${OUTPUT_DIR}" -name "*.png" | wc -l)"
echo "  .npy: $(find "${OUTPUT_DIR}" -name "*.npy" | wc -l)"

echo ""
echo "Test completed successfully!" 