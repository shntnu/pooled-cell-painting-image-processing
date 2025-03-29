#!/bin/bash
# Script to generate CSV files for all pipelines that need them

# Default parameters
PLATE="Plate1"
WELL="A01"
SITE="1"
CYCLE="1"
BATCH="Batch1"
OUTPUT_DIR="csv_outputs"

# Process command line arguments
while getopts "p:w:s:c:b:o:" opt; do
  case $opt in
    p) PLATE="$OPTARG" ;;
    w) WELL="$OPTARG" ;;
    s) SITE="$OPTARG" ;;
    c) CYCLE="$OPTARG" ;;
    b) BATCH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
  esac
done

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

echo "Generating CSV files for all pipelines..."
echo "Using parameters: Plate=$PLATE, Well=$WELL, Site=$SITE, Cycle=$CYCLE, Batch=$BATCH"
echo "Output directory: $OUTPUT_DIR"

# Pipeline 1: Cell Painting Illumination Correction
echo "Generating CSV for Pipeline 1: Cell Painting Illumination Correction..."
python docs/generate_csv.py --module 1_CP_Illum --plate $PLATE --well $WELL --site $SITE --batch $BATCH --output $OUTPUT_DIR/1_CP_Illum.csv

# Pipeline 2: Cell Painting Apply Illumination Correction
echo "Generating CSV for Pipeline 2: Cell Painting Apply Illumination Correction..."
python docs/generate_csv.py --module 2_CP_Apply_Illum --plate $PLATE --well $WELL --site $SITE --batch $BATCH --output $OUTPUT_DIR/2_CP_Apply_Illum.csv

# Pipeline 3: Cell Painting Segmentation Check
echo "Generating CSV for Pipeline 3: Cell Painting Segmentation Check..."
python docs/generate_csv.py --module 3_CP_SegmentCheck --plate $PLATE --well $WELL --site $SITE --batch $BATCH --output $OUTPUT_DIR/3_CP_SegmentCheck.csv

# Pipeline 5: Barcoding Illumination Correction
echo "Generating CSV for Pipeline 5: Barcoding Illumination Correction..."
python docs/generate_csv.py --module 5_BC_Illum --plate $PLATE --well $WELL --site $SITE --cycle $CYCLE --batch $BATCH --output $OUTPUT_DIR/5_BC_Illum.csv

# Pipeline 6: Barcoding Apply Illumination Correction
echo "Generating CSV for Pipeline 6: Barcoding Apply Illumination Correction..."
python docs/generate_csv.py --module 6_BC_Apply_Illum --plate $PLATE --well $WELL --site $SITE --cycle $CYCLE --batch $BATCH --output $OUTPUT_DIR/6_BC_Apply_Illum.csv

# Pipeline 7: Barcoding Preprocessing
echo "Generating CSV for Pipeline 7: Barcoding Preprocessing..."
python docs/generate_csv.py --module 7_BC_Preprocess --plate $PLATE --well $WELL --site $SITE --cycle $CYCLE --batch $BATCH --output $OUTPUT_DIR/7_BC_Preprocess.csv

# Pipeline 9: Analysis
echo "Generating CSV for Pipeline 9: Analysis..."
python docs/generate_csv.py --module 9_Analysis --plate $PLATE --well $WELL --site $SITE --cycle $CYCLE --batch $BATCH --output $OUTPUT_DIR/9_Analysis.csv

echo "All CSV files generated in $OUTPUT_DIR"
echo "Done!"

# Make the script executable
# Usage:
# ./generate_all_csvs.sh                   # Use defaults
# ./generate_all_csvs.sh -p Plate2 -w B02  # Override plate and well
# ./generate_all_csvs.sh -o my_csvs        # Change output directory 