import csv
import json
import argparse
import os
from pathlib import Path
import re


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate a CSV row for a pipeline module based on io.json configuration"
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Pipeline module (e.g., '1_CP_Illum', '2_CP_Apply_Illum')",
    )
    parser.add_argument("--plate", required=True, help="Plate identifier")
    parser.add_argument("--well", required=True, help="Well identifier (e.g. A01)")
    parser.add_argument("--site", required=True, type=int, help="Site number")
    parser.add_argument("--batch", default="Batch1", help="Batch identifier")
    parser.add_argument(
        "--cycle", type=int, default=0, help="Cycle number (if required)"
    )
    parser.add_argument("--output", default="output.csv", help="Output CSV file")
    parser.add_argument(
        "--config", default="docs/io.json", help="IO configuration file"
    )
    parser.add_argument(
        "--raw_image_template", default="IMAGE", help="Raw image template name"
    )
    parser.add_argument("--verbose", action="store_true", help="Print debug info")
    args = parser.parse_args()

    # Load io.json configuration
    with open(args.config, "r") as f:
        io_config = json.load(f)

    # Check if the requested module exists
    if args.module not in io_config:
        print(f"Error: Module '{args.module}' not found in configuration")
        return

    # Extract metadata schema and channel mappings
    metadata_schema = io_config["metadata_schema"]
    channel_mapping = io_config["metadata_schema"]["channel_mapping"]

    # Define metadata values from arguments
    metadata = {
        "batch": args.batch,
        "plate": args.plate,
        "well": args.well,
        "site": args.site,
    }

    # Add cycle if provided
    if args.cycle > 0:
        metadata["cycle"] = args.cycle

        # Special handling for Pipeline 5_BC_Illum which uses Metadata_SBSCycle
        if args.module == "5_BC_Illum":
            metadata["SBSCycle"] = args.cycle

    # Get channel mappings
    cp_channels = list(channel_mapping["cp"]["microscope_mapping"].values())
    bc_channels = list(channel_mapping["bc"]["microscope_mapping"].values())
    cp_microscope_channels = list(channel_mapping["cp"]["microscope_mapping"].keys())
    bc_microscope_channels = list(channel_mapping["bc"]["microscope_mapping"].keys())

    if args.verbose:
        print(f"CP channels: {cp_channels}")
        print(f"BC channels: {bc_channels}")

    # Get module configuration
    module_config = io_config[args.module]

    # Check if load_data_csv_config exists
    if "load_data_csv_config" not in module_config:
        print(
            f"Error: Module '{args.module}' does not have a load_data_csv_config section"
        )
        return

    # Get field configurations
    field_configs = module_config["load_data_csv_config"]["fields"]

    # Initialize inputs dictionary
    inputs = {}

    # Process each input source defined in the module
    if "inputs" in module_config:
        for input_key, input_config in module_config["inputs"].items():
            inputs[input_key] = {}

            if "source" in input_config:
                source_path = input_config["source"].split(".")
                source_module = source_path[0]
                source_section = source_path[1]
                source_key = source_path[2] if len(source_path) > 2 else None

                # Get the source patterns
                if (
                    source_module in io_config
                    and source_section in io_config[source_module]
                ):
                    source_patterns = io_config[source_module][source_section]

                    if source_key and source_key in source_patterns:
                        patterns = source_patterns[source_key]["patterns"]

                        # Process each pattern based on pattern type
                        if (
                            "cp_images" in input_config["source"]
                            or "cp_channel" in patterns[0]
                        ):
                            # Process Cell Painting images
                            for idx, cp_channel in enumerate(cp_channels):
                                cp_microscope_channel = cp_microscope_channels[idx]

                                # Add format parameters without duplicating metadata
                                format_params = {
                                    "raw_image_template": args.raw_image_template,
                                    "cp_microscope_channel": cp_microscope_channel,
                                    "cp_channel": cp_channel,
                                    "tile_number": metadata["site"],
                                }

                                try:
                                    formatted_path = patterns[0].format(
                                        **metadata, **format_params
                                    )

                                    path_obj = Path(formatted_path)

                                    inputs[input_key][cp_channel] = {
                                        "filename": path_obj.name,
                                        "path": str(path_obj.parent),
                                        "cp_channel": cp_channel,
                                    }
                                except KeyError as e:
                                    if args.verbose:
                                        print(f"KeyError in cp_images pattern: {e}")
                                    # Skip if formatting fails

                        elif (
                            "bc_images" in input_config["source"]
                            or "bc_channel" in patterns[0]
                        ):
                            # Process Barcoding images, only if cycle is provided
                            if "cycle" in metadata:
                                for idx, bc_channel in enumerate(bc_channels):
                                    bc_microscope_channel = bc_microscope_channels[idx]

                                    # Add format parameters without duplicating metadata
                                    format_params = {
                                        "raw_image_template": args.raw_image_template,
                                        "bc_microscope_channel": bc_microscope_channel,
                                        "bc_channel": bc_channel,
                                        "tile_number": metadata["site"],
                                    }

                                    try:
                                        formatted_path = patterns[0].format(
                                            **metadata, **format_params
                                        )

                                        path_obj = Path(formatted_path)

                                        cycle_key = (
                                            f"Cycle{metadata['cycle']}_{bc_channel}"
                                        )
                                        inputs[input_key][cycle_key] = {
                                            "filename": path_obj.name,
                                            "path": str(path_obj.parent),
                                            "bc_channel": bc_channel,
                                            "cycle": metadata["cycle"],
                                        }
                                    except KeyError as e:
                                        if args.verbose:
                                            print(f"KeyError in bc_images pattern: {e}")
                                        # Skip if formatting fails

                        elif "illum_functions" in input_config["source"]:
                            # Process illumination functions
                            for cp_channel in cp_channels:
                                try:
                                    # Add format parameters without duplicating metadata
                                    format_params = {
                                        "cp_channel": cp_channel,
                                        "tile_number": metadata["site"],
                                    }

                                    formatted_path = patterns[0].format(
                                        **metadata, **format_params
                                    )

                                    path_obj = Path(formatted_path)

                                    inputs[input_key][cp_channel] = {
                                        "filename": path_obj.name,
                                        "path": str(path_obj.parent),
                                        "cp_channel": cp_channel,
                                    }
                                except KeyError as e:
                                    if args.verbose:
                                        print(f"KeyError in cp illum pattern: {e}")
                                    # Skip if format fails

                            # Handle BC illum if cycle is provided
                            if "cycle" in metadata:
                                for bc_channel in bc_channels:
                                    try:
                                        # Add format parameters without duplicating metadata
                                        format_params = {
                                            "bc_channel": bc_channel,
                                            "tile_number": metadata["site"],
                                        }

                                        formatted_path = patterns[0].format(
                                            **metadata, **format_params
                                        )

                                        path_obj = Path(formatted_path)

                                        cycle_key = (
                                            f"Cycle{metadata['cycle']}_{bc_channel}"
                                        )
                                        inputs[input_key][cycle_key] = {
                                            "filename": path_obj.name,
                                            "path": str(path_obj.parent),
                                            "bc_channel": bc_channel,
                                            "cycle": metadata["cycle"],
                                        }
                                    except KeyError as e:
                                        if args.verbose:
                                            print(f"KeyError in bc illum pattern: {e}")
                                        # Skip if format fails

    # Create a dictionary to store the row data
    row_data = {}

    # Process fields and expand for all channels/cycles
    processed_field_templates = []

    for field_config in field_configs:
        name_template = field_config["name"]
        source = field_config["source"]

        # Skip fields with conditions that aren't met
        if "condition" in field_config:
            condition = field_config["condition"]
            if condition == "cycle>0" and (args.cycle <= 0 or "cycle" not in metadata):
                continue

        # Debug the field template
        if args.verbose:
            print(f"Processing field template: {name_template}")

        # Check for placeholders in the name template
        has_cycle = "{cycle}" in name_template
        has_cp_channel = "{cp_channel}" in name_template
        has_bc_channel = "{bc_channel}" in name_template

        # Generate all variations of the field
        if has_cp_channel and not has_cycle:
            # Cell painting channel fields
            for cp_channel in cp_channels:
                field_name = name_template.format(cp_channel=cp_channel)
                processed_field_templates.append(
                    (field_name, source, "cp_channel", cp_channel, None)
                )

        elif has_bc_channel and not has_cycle and args.module == "5_BC_Illum":
            # Special case for 5_BC_Illum: bc_channel fields without cycle in field name
            for bc_channel in bc_channels:
                field_name = name_template.format(bc_channel=bc_channel)
                processed_field_templates.append(
                    (
                        field_name,
                        source,
                        "bc_channel",
                        bc_channel,
                        metadata.get("cycle"),
                    )
                )

        elif has_bc_channel and has_cycle and "cycle" in metadata:
            # Barcoding channel fields with cycle
            cycle = metadata["cycle"]
            for bc_channel in bc_channels:
                field_name = name_template.format(bc_channel=bc_channel, cycle=cycle)
                processed_field_templates.append(
                    (field_name, source, "bc_channel", bc_channel, cycle)
                )

        elif (
            has_cycle
            and not has_bc_channel
            and not has_cp_channel
            and "cycle" in metadata
        ):
            # Cycle-only fields
            field_name = name_template.format(cycle=metadata["cycle"])
            processed_field_templates.append(
                (field_name, source, None, None, metadata["cycle"])
            )

        else:
            # Plain fields with no substitution
            processed_field_templates.append((name_template, source, None, None, None))

    # Process all expanded field templates
    for field_info in processed_field_templates:
        field_name, source, channel_type, channel, cycle = field_info

        if args.verbose:
            print(f"Processing field: {field_name} (source: {source})")

        # Get the value based on source
        if source.startswith("inputs."):
            # Parse the source path
            source_parts = source.split(".")
            input_type = source_parts[1]
            input_attr = source_parts[2]

            value = ""
            # Handle different input types and naming schemes
            if input_type in inputs:
                if cycle and channel and channel_type == "bc_channel":
                    # For barcoding with cycle, use the combined key
                    cycle_key = f"Cycle{cycle}_{channel}"
                    if cycle_key in inputs[input_type]:
                        value = inputs[input_type][cycle_key].get(input_attr, "")
                        if args.verbose:
                            print(
                                f"  Found value for {cycle_key}.{input_attr}: {value}"
                            )

                elif channel and channel_type == "cp_channel":
                    # For cell painting channels
                    if channel in inputs[input_type]:
                        value = inputs[input_type][channel].get(input_attr, "")
                        if args.verbose:
                            print(f"  Found value for {channel}.{input_attr}: {value}")

                elif len(inputs[input_type]) > 0:
                    # If no specific channel, use the first one
                    first_key = next(iter(inputs[input_type]))
                    value = inputs[input_type][first_key].get(input_attr, "")
                    if args.verbose:
                        print(f"  Using first key {first_key}.{input_attr}: {value}")

        elif source.startswith("metadata."):
            # Get value from metadata
            meta_key = source.split(".")[1]
            value = metadata.get(meta_key, "")

        else:
            value = ""

        row_data[field_name] = value

    # Write to CSV
    with open(args.output, "w", newline="") as csvfile:
        # Sort columns in the desired order
        # First the specific metadata columns
        priority_metadata = ["Metadata_Plate", "Metadata_Well", "Metadata_Site"]

        # Get all column names
        all_columns = list(row_data.keys())

        # Separate columns into different categories
        metadata_columns = [col for col in all_columns if col.startswith("Metadata_")]
        filename_columns = [col for col in all_columns if col.startswith("FileName_")]
        pathname_columns = [col for col in all_columns if col.startswith("PathName_")]
        other_columns = [
            col
            for col in all_columns
            if not (
                col.startswith("Metadata_")
                or col.startswith("FileName_")
                or col.startswith("PathName_")
            )
        ]

        # Sort the metadata columns to put priority ones first
        sorted_metadata = []
        for col in priority_metadata:
            if col in metadata_columns:
                sorted_metadata.append(col)
                metadata_columns.remove(col)

        # Add remaining metadata columns
        sorted_metadata.extend(sorted(metadata_columns))

        # Create pairs of FileName/PathName columns and keep them together
        filename_pathname_pairs = []
        for filename_col in sorted(filename_columns):
            # Find the corresponding PathName column
            base_name = filename_col[len("FileName_") :]
            pathname_col = f"PathName_{base_name}"
            if pathname_col in pathname_columns:
                filename_pathname_pairs.extend([filename_col, pathname_col])
                pathname_columns.remove(pathname_col)

        # Add any remaining pathname columns and other columns
        remaining_columns = sorted(pathname_columns) + sorted(other_columns)

        # Combine all columns in the desired order
        ordered_columns = sorted_metadata + filename_pathname_pairs + remaining_columns

        if args.verbose:
            print("Column order:")
            for i, col in enumerate(ordered_columns):
                print(f"  {i + 1}. {col}")

        writer = csv.DictWriter(csvfile, fieldnames=ordered_columns)
        writer.writeheader()
        writer.writerow(row_data)

    print(f"CSV row generated for {args.module} in {args.output}")

    # Print field names if verbose
    if args.verbose:
        print("Generated field names:")
        for field_name in row_data.keys():
            print(f"  {field_name}")


if __name__ == "__main__":
    main()
