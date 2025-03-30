# Generate Structures

Utility scripts for creating test file structures and LoadData CSVs for the pooled cell painting image processing pipeline.

## Scripts

- `run_generate_files.sh` - Generates dummy output files according to the IO schema
- `run_generate_csv.sh` - Creates LoadData CSV files
- `extract_file_paths.py` - Extracts file paths from LoadData CSV files to a list
- `check_files.sh` - Verifies existence of files from a list

## Usage

```bash
./run_generate_files.sh

# ...
# Total output files: 153
# Detailed output written to output_paths.json

./run_generate_csv.sh

# Generating CSV files for all pipelines...
# Using parameters: Plate=Plate1, Well=A01, Site=1, Cycle=1, Batch=Batch1
# Output directory: Source1/workspace/load_data_csv
# ...
# All CSV files generated in Source1/workspace/load_data_csv

python extract_file_paths.py Source1/workspace/load_data_csv/ -o list.txt

# Processing Source1/workspace/load_data_csv/6_BC_Apply_Illum.csv...
# ...
# Wrote 40 file paths to list.txt

./check_files.sh list.txt Source1/

# Checked 40 files. Found: 40, Missing: 0
```
