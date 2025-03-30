import csv
import json
import argparse
from pathlib import Path
import itertools


def parse_range(range_str, is_well=False):
    """Parse a range string into a list of values.

    Examples:
    - "1-5" -> [1, 2, 3, 4, 5] (for sites/cycles)
    - "A01-A04" -> ["A01", "A02", "A03", "A04"] (for wells)
    - "1,3,5" -> [1, 3, 5] (for sites/cycles)
    - "A01,B01,C01" -> ["A01", "B01", "C01"] (for wells)
    """
    if not range_str:
        raise ValueError("Empty range string provided")

    # Check if it's a comma-separated list
    if "," in range_str:
        if is_well:
            return range_str.split(",")
        else:
            return [int(x) for x in range_str.split(",")]

    # Check if it's a range (e.g., "1-5" or "A01-A04")
    elif "-" in range_str:
        start, end = range_str.split("-")

        if is_well:
            # Handle well ranges (e.g., "A01-A12")
            if not (start[0].isalpha() and end[0].isalpha()):
                raise ValueError(f"Invalid well range: {range_str}")

            # Extract the letter and number parts
            start_letter = start[0]
            end_letter = end[0]

            try:
                start_num = int(start[1:])
                end_num = int(end[1:])
            except ValueError:
                raise ValueError(f"Invalid well format in range: {range_str}")

            # Generate all wells in the range
            result = []

            # If same letter (e.g., "A01-A12")
            if start_letter == end_letter:
                for num in range(start_num, end_num + 1):
                    result.append(f"{start_letter}{num:02d}")
            else:
                # If different letters (e.g., "A01-C01")
                for letter in range(ord(start_letter), ord(end_letter) + 1):
                    letter_char = chr(letter)

                    # Determine the number range for this letter
                    if letter_char == start_letter:
                        num_start = start_num
                        num_end = 99  # Assuming max 99 columns
                    elif letter_char == end_letter:
                        num_start = 1
                        num_end = end_num
                    else:
                        num_start = 1
                        num_end = 99

                    for num in range(num_start, num_end + 1):
                        result.append(f"{letter_char}{num:02d}")

            return result
        else:
            # For sites and cycles, just return a range of integers
            return list(range(int(start), int(end) + 1))
    else:
        # It's a single value
        if is_well:
            return [range_str]
        else:
            return [int(range_str)]


def process_pattern(
    source_key,
    patterns,
    metadata,
    channels,
    channel_to_microscope,
    pattern_configs,
    args,
    verbose=False,
):
    """Generic function to process a pattern based on its configuration"""
    results = {}

    # Get the pattern configuration or use defaults if not found
    config = pattern_configs.get(source_key, {})

    # Determine which channel types to process
    channel_types = config.get("channel_types", [config.get("channel_type")])
    if not channel_types:
        channel_types = ["cp"]  # Default to CP if no type specified

    # Process each channel type
    for channel_type in channel_types:
        # Get appropriate channels and converter based on channel type
        if channel_type == "cp":
            current_channels = channels["cp"]
            channel_converter = channel_to_microscope["cp"]
            microscope_prefix = "cp_microscope_channel"
            channel_prefix = "cp_channel"
        else:  # "bc"
            current_channels = channels["bc"]
            channel_converter = channel_to_microscope["bc"]
            microscope_prefix = "bc_microscope_channel"
            channel_prefix = "bc_channel"

        # Check if we need cycle for this channel type
        requires_cycle = config.get("requires_cycle", False)
        if isinstance(requires_cycle, list):
            requires_cycle = channel_type in config.get("requires_cycle_for", [])

        # Skip if we need cycle but don't have it
        if requires_cycle and "cycle" not in metadata:
            continue

        # Process each channel
        for channel in current_channels:
            microscope_channel = channel_converter[channel]

            # Format parameters based on channel type
            format_params = {
                "raw_image_template": args.raw_image_template,
                f"{microscope_prefix}": microscope_channel,
                f"{channel_prefix}": channel,
                "tile_number": metadata["site"],
            }

            # Determine the output key format
            output_key_format = config.get("output_key_format", "{channel}")
            if isinstance(output_key_format, dict):
                output_key_format = output_key_format.get(channel_type, "{channel}")

            # Generate the output key
            if "cycle" in metadata and "{cycle}" in output_key_format:
                output_key = output_key_format.format(
                    channel=channel, cycle=metadata["cycle"]
                )
            else:
                output_key = output_key_format.format(channel=channel)

            try:
                # Format the path with all parameters
                formatted_path = patterns[0].format(**metadata, **format_params)
                path_obj = Path(formatted_path)

                # Create result entry
                result_entry = {
                    "filename": path_obj.name,
                    "path": str(path_obj.parent),
                    f"{channel_prefix}": channel,
                }

                # Add cycle if available
                if "cycle" in metadata:
                    result_entry["cycle"] = metadata["cycle"]

                results[output_key] = result_entry

            except KeyError as e:
                if verbose:
                    print(f"KeyError in {source_key} pattern: {e}")
                # Skip if formatting fails

    return results


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
    parser.add_argument("--plate", default="Plate1", help="Plate identifier")
    parser.add_argument(
        "--well",
        required=True,
        help="Well identifier (e.g. A01) or range (e.g. A01-A12) or comma-separated list (e.g. A01,B01,C01)",
    )
    parser.add_argument(
        "--site",
        required=True,
        help="Site number or range (e.g. 1-9) or comma-separated list (e.g. 1,3,5)",
    )
    parser.add_argument("--batch", default="Batch1", help="Batch identifier")
    parser.add_argument(
        "--cycle",
        default="1",
        help="Cycle number (if required) or range (e.g. 1-5) or comma-separated list (e.g. 1,3,5)",
    )
    parser.add_argument("--output", default="output.csv", help="Output CSV file")
    parser.add_argument("--config", default="../io.json", help="IO configuration file")
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

    # Get pattern configurations from metadata schema
    pattern_configs = metadata_schema.get("pattern_configs", {})

    if args.verbose and not pattern_configs:
        print(
            "Warning: No pattern_configs found in metadata_schema. Using default configurations."
        )

    # map between channel names
    microscope_to_cp_channel = channel_mapping["cp"]["microscope_mapping"]
    cp_channel_to_microscope = {v: k for k, v in microscope_to_cp_channel.items()}

    microscope_to_bc_channel = channel_mapping["bc"]["microscope_mapping"]
    bc_channel_to_microscope = {v: k for k, v in microscope_to_bc_channel.items()}

    # Get channel lists directly from schema
    cp_channels = metadata_schema["cp_channel"]["enum"]
    bc_channels = metadata_schema["bc_channel"]["enum"]

    # Validate with compact assert statements
    assert set(cp_channels) == set(microscope_to_cp_channel.values()), (
        f"CP channel mismatch: {cp_channels} vs {list(microscope_to_cp_channel.values())}"
    )
    assert set(bc_channels) == set(microscope_to_bc_channel.values()), (
        f"BC channel mismatch: {bc_channels} vs {list(microscope_to_bc_channel.values())}"
    )

    # Channel data structure for easier passing around
    channels = {"cp": cp_channels, "bc": bc_channels}

    channel_to_microscope = {
        "cp": cp_channel_to_microscope,
        "bc": bc_channel_to_microscope,
    }

    if args.verbose:
        print(f"CP channels: {cp_channels}")
        print(f"BC channels: {bc_channels}")

    # Parse well, site, and cycle ranges/lists
    wells = parse_range(args.well, is_well=True)
    assert wells, f"Invalid well specification: {args.well}"

    sites = parse_range(args.site)
    assert sites, f"Invalid site specification: {args.site}"

    cycles = parse_range(args.cycle) if args.cycle != "0" else [0]
    assert cycles is not None, f"Invalid cycle specification: {args.cycle}"

    if args.verbose:
        print("Generating data for:")
        print(f"  Wells: {wells}")
        print(f"  Sites: {sites}")
        print(f"  Cycles: {cycles}")

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

    # Get the grouping keys from the config to determine how to pivot the data
    grouping_keys = module_config["load_data_csv_config"].get(
        "grouping_keys", ["plate", "well", "site"]
    )

    # Initialize inputs dictionary and collect all possible fields
    all_possible_fields = set()

    # Dictionary to store rows indexed by group key
    # This will ensure we combine all cycle data for the same plate/well/site
    pivoted_data = {}

    # Iterate through all combinations of well, site, and cycle
    for well, site, cycle in itertools.product(wells, sites, cycles):
        # Skip cycles <= 0 for modules that require cycles
        if cycle <= 0 and any("{cycle}" in field["name"] for field in field_configs):
            continue

        if args.verbose:
            print(f"Processing combination: Well={well}, Site={site}, Cycle={cycle}")

        # Define metadata values for this combination
        metadata = {
            "batch": args.batch,
            "plate": args.plate,
            "well": well,
            "site": site,
        }

        # Add cycle if provided
        if cycle > 0:
            metadata["cycle"] = cycle

            # Special handling for Pipeline 5_BC_Illum which uses Metadata_SBSCycle
            if args.module == "5_BC_Illum":
                metadata["SBSCycle"] = cycle

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

                            # Process the pattern using our generic function
                            pattern_results = process_pattern(
                                source_key,
                                patterns,
                                metadata,
                                channels,
                                channel_to_microscope,
                                pattern_configs,
                                args,
                                args.verbose,
                            )

                            # Add the results to the inputs dictionary
                            inputs[input_key].update(pattern_results)

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
                if condition == "cycle>0" and (cycle <= 0 or "cycle" not in metadata):
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
                cycle_value = metadata["cycle"]
                for bc_channel in bc_channels:
                    field_name = name_template.format(
                        bc_channel=bc_channel, cycle=cycle_value
                    )
                    processed_field_templates.append(
                        (field_name, source, "bc_channel", bc_channel, cycle_value)
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
                processed_field_templates.append(
                    (name_template, source, None, None, None)
                )

        # Process all expanded field templates
        for field_info in processed_field_templates:
            field_name, source, channel_type, channel, cycle_value = field_info

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
                    if cycle_value and channel and channel_type == "bc_channel":
                        # For barcoding with cycle, use the combined key
                        cycle_key = f"Cycle{cycle_value}_{channel}"
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
                                print(
                                    f"  Found value for {channel}.{input_attr}: {value}"
                                )

                    elif len(inputs[input_type]) > 0:
                        # If no specific channel, use the first one
                        first_key = next(iter(inputs[input_type]))
                        value = inputs[input_type][first_key].get(input_attr, "")
                        if args.verbose:
                            print(
                                f"  Using first key {first_key}.{input_attr}: {value}"
                            )

            elif source.startswith("metadata."):
                # Get value from metadata
                meta_key = source.split(".")[1]
                value = metadata.get(meta_key, "")

            else:
                value = ""

            row_data[field_name] = value

        # Collect all field names for this row
        all_possible_fields.update(row_data.keys())

        # Create a group key based on the grouping values
        # Convert metadata values to tuple based on grouping keys (exclude cycle)
        group_key = tuple(metadata.get(key) for key in grouping_keys)

        # If we already have a row for this group, update it with the new data
        # otherwise create a new entry
        if group_key in pivoted_data:
            pivoted_data[group_key].update(row_data)
        else:
            pivoted_data[group_key] = row_data.copy()

    # Open CSV file for writing after collecting all possible fields
    with open(args.output, "w", newline="") as csvfile:
        # Sort columns in the desired order
        # First the specific metadata columns
        priority_metadata = ["Metadata_Plate", "Metadata_Well", "Metadata_Site"]

        # Get all column names
        all_columns = list(all_possible_fields)

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

        # Write all rows (now pivoted by group key)
        for row_data in pivoted_data.values():
            # Fill in missing fields with empty values
            for field in ordered_columns:
                if field not in row_data:
                    row_data[field] = ""
            writer.writerow(row_data)

    # Print summary
    num_combinations = len(pivoted_data)
    print(
        f"CSV with {num_combinations} rows generated for {args.module} in {args.output}"
    )


if __name__ == "__main__":
    main()
