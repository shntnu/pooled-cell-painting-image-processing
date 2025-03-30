#!/usr/bin/env python

import pandas as pd
import argparse
import os
import re


def filter_pipeline_1_to_3(df, sites=None, wells=None, plates=None):
    """
    Filter pipelines 1-3 which don't have cycle field
    """
    filtered_df = df.copy()

    # Apply filters
    if plates is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]

    if wells is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]

    if sites is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]

    return filtered_df


def filter_pipeline_5(df, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter pipeline 5 which has SBSCycle instead of cycle column
    """
    filtered_df = df.copy()

    # Apply filters
    if plates is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]

    if wells is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]

    if sites is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]

    if cycles is not None:
        filtered_df = filtered_df[filtered_df["Metadata_SBSCycle"].isin(cycles)]

    return filtered_df


def filter_pipeline_6_7_9(df, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter pipelines 6, 7, 9 which have cycle in column names
    """
    filtered_df = df.copy()

    # Apply filters for metadata columns
    if plates is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]

    if wells is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]

    if sites is not None:
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]

    # Filter columns based on cycle
    if cycles is not None:
        # Convert cycles to padded format for matching column names
        cycle_patterns = [f"Cycle{str(c).zfill(2)}" for c in cycles]

        # Keep all metadata columns
        metadata_cols = [
            col for col in filtered_df.columns if col.startswith("Metadata_")
        ]

        # Find columns matching the specified cycles
        cycle_cols = []
        for col in filtered_df.columns:
            if not col.startswith("Metadata_"):
                for pattern in cycle_patterns:
                    if pattern in col:
                        cycle_cols.append(col)
                        break

        # Keep only metadata columns and columns for specified cycles
        filtered_df = filtered_df[metadata_cols + cycle_cols]

    return filtered_df


def determine_pipeline_type(csv_path):
    """
    Determine which pipeline type the CSV belongs to
    """
    filename = os.path.basename(csv_path)

    # Extract pipeline number
    match = re.search(r"pipeline(\d+)", filename)
    if match:
        pipeline_num = int(match.group(1))

        if pipeline_num in [1, 2, 3]:
            return "pipeline_1_to_3"
        elif pipeline_num == 5:
            return "pipeline_5"
        elif pipeline_num in [6, 7, 9]:
            return "pipeline_6_7_9"

    # Default to checking headers if filename pattern doesn't match
    with open(csv_path, "r") as f:
        header = f.readline().strip()

        if "Metadata_SBSCycle" in header:
            return "pipeline_5"
        elif any(f"Cycle{str(i).zfill(2)}" in header for i in range(1, 11)):
            return "pipeline_6_7_9"
        else:
            return "pipeline_1_to_3"


def filter_csv(csv_path, output_path, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter CSV based on specified parameters
    """
    # Read the CSV
    df = pd.read_csv(csv_path)

    # Determine pipeline type
    pipeline_type = determine_pipeline_type(csv_path)

    # Apply appropriate filtering
    if pipeline_type == "pipeline_1_to_3":
        filtered_df = filter_pipeline_1_to_3(df, sites, wells, plates)
    elif pipeline_type == "pipeline_5":
        filtered_df = filter_pipeline_5(df, cycles, sites, wells, plates)
    elif pipeline_type == "pipeline_6_7_9":
        filtered_df = filter_pipeline_6_7_9(df, cycles, sites, wells, plates)

    # Save the filtered data
    filtered_df.to_csv(output_path, index=False)
    print(f"Filtered {csv_path} saved to {output_path}")
    print(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")

    if pipeline_type == "pipeline_6_7_9" and cycles is not None:
        print(
            f"Original columns: {len(df.columns)}, Filtered columns: {len(filtered_df.columns)}"
        )


def main():
    parser = argparse.ArgumentParser(description="Filter cell painting CSV files")
    parser.add_argument("csv_path", help="Path to the CSV file to filter")
    parser.add_argument("output_path", help="Path to save the filtered CSV")
    parser.add_argument(
        "--cycles", nargs="+", type=int, help="Cycle numbers to include"
    )
    parser.add_argument("--sites", nargs="+", help="Site IDs to include")
    parser.add_argument("--wells", nargs="+", help="Well IDs to include")
    parser.add_argument("--plates", nargs="+", help="Plate IDs to include")

    args = parser.parse_args()

    filter_csv(
        args.csv_path,
        args.output_path,
        cycles=args.cycles,
        sites=args.sites,
        wells=args.wells,
        plates=args.plates,
    )


if __name__ == "__main__":
    main()
