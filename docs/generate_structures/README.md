# CSV Filtering Script for Cell Painting Data

This script allows filtering of cell painting CSV files by cycles, sites, wells, and plates.

## Features

- Handles different CSV formats from various pipelines
- Automatically detects pipeline type based on CSV structure
- Provides different filtering behavior for:
  - Pipelines 1-3: No cycle field
  - Pipeline 5: Has `Metadata_SBSCycle` field (filtered row-wise)
  - Pipelines 6, 7, 9: Has cycle in column names (filtered column-wise)

## Requirements

- Python 3.6+
- pandas

## Installation

```bash
pip install pandas
```

## Usage

```bash
python filter_csv.py <csv_path> <output_path> [OPTIONS]
```

### Arguments

- `csv_path`: Path to the CSV file to be filtered
- `output_path`: Path where the filtered CSV will be saved

### Options

- `--cycles`: Cycle numbers to include (not relevant for pipelines 1-3)
- `--sites`: Site IDs to include
- `--wells`: Well IDs to include
- `--plates`: Plate IDs to include

### Examples

1. Filter by specific wells and sites:
```bash
python filter_csv.py input.csv filtered.csv --wells WellA1 WellB2 --sites 0 1 2
```

2. Filter pipeline 5 CSVs by cycle:
```bash
python filter_csv.py pipeline5.csv filtered.csv --cycles 1 2 --wells WellA1
```

3. Filter pipeline 6/7/9 CSVs by cycle (filters columns):
```bash
python filter_csv.py pipeline6.csv filtered.csv --cycles 1 2 3 --plates Plate1
```

## Pipeline Type Detection

The script automatically determines the pipeline type by:
1. First checking the filename for pattern `pipeline<number>`
2. If that fails, analyzing the header structure

## Notes

- For pipelines 1-3: No cycle filtering is performed
- For pipeline 5: The `Metadata_SBSCycle` column is used for cycle filtering
- For pipelines 6-7-9: Column names containing cycle patterns are filtered 