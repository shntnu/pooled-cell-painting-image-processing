import os
import pandas as pd
import glob
import argparse


def extract_file_paths(csv_file):
    """
    Extract all file paths from a CSV file that contains FileName/PathName pairs.

    Args:
        csv_file: Path to the CSV file

    Returns:
        List of full file paths
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Get all columns that start with FileName or PathName
    filename_cols = [col for col in df.columns if col.startswith("FileName_")]
    pathname_cols = [col for col in df.columns if col.startswith("PathName_")]

    # Match filename and pathname columns based on their suffix
    column_pairs = []
    for filename_col in filename_cols:
        suffix = filename_col.replace("FileName_", "")
        pathname_col = f"PathName_{suffix}"

        if pathname_col in pathname_cols:
            column_pairs.append((filename_col, pathname_col))

    # Extract all file paths
    file_paths = []

    for _, row in df.iterrows():
        for filename_col, pathname_col in column_pairs:
            if pd.notna(row[filename_col]) and pd.notna(row[pathname_col]):
                file_path = os.path.join(row[pathname_col], row[filename_col])
                file_paths.append(file_path)

    return file_paths


def process_csv_files(input_dir, output_file=None):
    """
    Process all CSV files in the input directory and extract file paths.

    Args:
        input_dir: Directory containing CSV files
        output_file: Optional file to write the paths to
    """
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

    all_file_paths = []

    # Process each CSV file
    for csv_file in csv_files:
        print(f"Processing {csv_file}...")
        file_paths = extract_file_paths(csv_file)
        all_file_paths.extend(file_paths)
        print(f"Found {len(file_paths)} file paths in {csv_file}")

    # Remove duplicates and sort the paths
    all_file_paths = sorted(set(all_file_paths))
    print(f"Found {len(all_file_paths)} unique file paths after deduplication")

    # Write to output file if specified
    if output_file:
        with open(output_file, "w") as f:
            for path in all_file_paths:
                f.write(f"{path}\n")
        print(f"Wrote {len(all_file_paths)} file paths to {output_file}")

    return all_file_paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract file paths from CSV files")
    parser.add_argument("input_dir", type=str, help="Directory containing CSV files")
    parser.add_argument(
        "--output", "-o", type=str, help="Output file to write paths to"
    )

    args = parser.parse_args()

    file_paths = process_csv_files(args.input_dir, args.output)

    if not args.output:
        for path in file_paths:
            print(path)
