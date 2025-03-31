#!/usr/bin/env python

import pandas as pd
import argparse
import os
import re
import logging
import sys
from datetime import datetime


# Set up logging
def setup_logging(log_level):
    """Configure logging with the specified level"""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = log_levels.get(log_level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Format: timestamp - level - message
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            # Log to file with timestamp in filename
            logging.FileHandler(
                f"logs/filter_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
            # Also log to console
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.info(f"Logging initialized at {log_level} level")


def filter_pipeline_1_to_3(df, sites=None, wells=None, plates=None):
    """
    Filter pipelines 1-3 which don't have cycle field
    """
    logging.debug(f"Filtering pipeline 1-3 data")
    logging.debug(f"Input DataFrame shape: {df.shape}")

    filtered_df = df.copy()

    # Apply filters
    if plates is not None:
        logging.debug(f"Filtering by plates: {plates}")
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]
        logging.debug(f"After plate filter: {filtered_df.shape}")

    if wells is not None:
        logging.debug(f"Filtering by wells: {wells}")
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]
        logging.debug(f"After well filter: {filtered_df.shape}")

    if sites is not None:
        logging.debug(f"Filtering by sites: {sites}")
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]
        logging.debug(f"After site filter: {filtered_df.shape}")

    logging.debug(f"Output DataFrame shape: {filtered_df.shape}")
    return filtered_df


def filter_pipeline_5(df, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter pipeline 5 which has SBSCycle instead of cycle column
    """
    logging.debug(f"Filtering pipeline 5 data")
    logging.debug(f"Input DataFrame shape: {df.shape}")

    filtered_df = df.copy()

    # Apply filters
    if plates is not None:
        logging.debug(f"Filtering by plates: {plates}")
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]
        logging.debug(f"After plate filter: {filtered_df.shape}")

    if wells is not None:
        logging.debug(f"Filtering by wells: {wells}")
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]
        logging.debug(f"After well filter: {filtered_df.shape}")

    if sites is not None:
        logging.debug(f"Filtering by sites: {sites}")
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]
        logging.debug(f"After site filter: {filtered_df.shape}")

    if cycles is not None:
        logging.debug(f"Filtering by SBSCycles: {cycles}")
        filtered_df = filtered_df[filtered_df["Metadata_SBSCycle"].isin(cycles)]
        logging.debug(f"After cycle filter: {filtered_df.shape}")

    logging.debug(f"Output DataFrame shape: {filtered_df.shape}")
    return filtered_df


def filter_pipeline_6_7_9(df, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter pipelines 6, 7, 9 which have cycle in column names
    """
    logging.debug(f"Filtering pipeline 6/7/9 data")
    logging.debug(f"Input DataFrame shape: {df.shape}")
    logging.debug(f"Input DataFrame columns: {len(df.columns)}")

    filtered_df = df.copy()

    # Apply filters for metadata columns
    if plates is not None:
        logging.debug(f"Filtering by plates: {plates}")
        filtered_df = filtered_df[filtered_df["Metadata_Plate"].isin(plates)]
        logging.debug(f"After plate filter: {filtered_df.shape}")

    if wells is not None:
        logging.debug(f"Filtering by wells: {wells}")
        filtered_df = filtered_df[filtered_df["Metadata_Well"].isin(wells)]
        logging.debug(f"After well filter: {filtered_df.shape}")

    if sites is not None:
        logging.debug(f"Filtering by sites: {sites}")
        filtered_df = filtered_df[filtered_df["Metadata_Site"].isin(sites)]
        logging.debug(f"After site filter: {filtered_df.shape}")

    # Filter columns based on cycle
    if cycles is not None:
        logging.debug(f"Filtering columns by cycles: {cycles}")
        # Convert cycles to padded format for matching column names
        cycle_patterns = [f"Cycle{str(c).zfill(2)}" for c in cycles]
        logging.debug(f"Using cycle patterns: {cycle_patterns}")

        # Keep all metadata columns
        metadata_cols = [
            col for col in filtered_df.columns if col.startswith("Metadata_")
        ]
        logging.debug(f"Keeping {len(metadata_cols)} metadata columns")

        # Find columns matching the specified cycles
        cycle_cols = []
        for col in filtered_df.columns:
            if not col.startswith("Metadata_"):
                for pattern in cycle_patterns:
                    if pattern in col:
                        cycle_cols.append(col)
                        break

        logging.debug(f"Found {len(cycle_cols)} columns matching cycle patterns")

        # Keep only metadata columns and columns for specified cycles
        filtered_df = filtered_df[metadata_cols + cycle_cols]
        logging.debug(
            f"After column filtering: {filtered_df.shape} with {len(filtered_df.columns)} columns"
        )

    logging.debug(f"Output DataFrame shape: {filtered_df.shape}")
    return filtered_df


def determine_pipeline_type(csv_path):
    """
    Determine which pipeline type the CSV belongs to
    """
    logging.info(f"Determining pipeline type for {csv_path}")
    filename = os.path.basename(csv_path)

    # Extract pipeline number
    match = re.search(r"pipeline(\d+)", filename)
    if match:
        pipeline_num = int(match.group(1))

        if pipeline_num in [1, 2, 3]:
            pipeline_type = "pipeline_1_to_3"
            logging.info(f"Determined pipeline type from filename: {pipeline_type}")
            return pipeline_type
        elif pipeline_num == 5:
            pipeline_type = "pipeline_5"
            logging.info(f"Determined pipeline type from filename: {pipeline_type}")
            return pipeline_type
        elif pipeline_num in [6, 7, 9]:
            pipeline_type = "pipeline_6_7_9"
            logging.info(f"Determined pipeline type from filename: {pipeline_type}")
            return pipeline_type

    # Default to checking headers if filename pattern doesn't match
    logging.debug("Filename pattern not recognized, checking header structure")
    with open(csv_path, "r") as f:
        header = f.readline().strip()

        if "Metadata_SBSCycle" in header:
            pipeline_type = "pipeline_5"
            logging.info(f"Determined pipeline type from header: {pipeline_type}")
            return pipeline_type
        elif any(f"Cycle{str(i).zfill(2)}" in header for i in range(1, 11)):
            pipeline_type = "pipeline_6_7_9"
            logging.info(f"Determined pipeline type from header: {pipeline_type}")
            return pipeline_type
        else:
            pipeline_type = "pipeline_1_to_3"
            logging.info(f"Determined pipeline type from header: {pipeline_type}")
            return pipeline_type


def filter_csv(csv_path, output_path, cycles=None, sites=None, wells=None, plates=None):
    """
    Filter CSV based on specified parameters
    """
    logging.info(f"Starting to filter CSV: {csv_path}")
    logging.info(f"Output will be saved to: {output_path}")

    if cycles:
        logging.info(f"Cycle filter: {cycles}")
    if sites:
        logging.info(f"Site filter: {sites}")
    if wells:
        logging.info(f"Well filter: {wells}")
    if plates:
        logging.info(f"Plate filter: {plates}")

    # Read the CSV
    try:
        logging.debug(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        logging.info(f"Successfully read CSV with shape: {df.shape}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        raise

    # Determine pipeline type
    try:
        pipeline_type = determine_pipeline_type(csv_path)
    except Exception as e:
        logging.error(f"Error determining pipeline type: {e}")
        raise

    # Apply appropriate filtering
    try:
        if pipeline_type == "pipeline_1_to_3":
            filtered_df = filter_pipeline_1_to_3(df, sites, wells, plates)
        elif pipeline_type == "pipeline_5":
            filtered_df = filter_pipeline_5(df, cycles, sites, wells, plates)
        elif pipeline_type == "pipeline_6_7_9":
            filtered_df = filter_pipeline_6_7_9(df, cycles, sites, wells, plates)
    except Exception as e:
        logging.error(f"Error during filtering: {e}")
        raise

    # Save the filtered data
    try:
        logging.debug(f"Saving filtered DataFrame to {output_path}")
        filtered_df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved filtered CSV to {output_path}")
    except Exception as e:
        logging.error(f"Error saving filtered CSV: {e}")
        raise

    # Log statistics
    logging.info(f"Filtering statistics:")
    logging.info(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")

    if pipeline_type == "pipeline_6_7_9" and cycles is not None:
        logging.info(
            f"Original columns: {len(df.columns)}, Filtered columns: {len(filtered_df.columns)}"
        )

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
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Log script start
    logging.info("=" * 50)
    logging.info("CSV filtering script started")
    logging.info(f"Arguments: {args}")

    try:
        filter_csv(
            args.csv_path,
            args.output_path,
            cycles=args.cycles,
            sites=args.sites,
            wells=args.wells,
            plates=args.plates,
        )
        logging.info("CSV filtering completed successfully")
    except Exception as e:
        logging.critical(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
