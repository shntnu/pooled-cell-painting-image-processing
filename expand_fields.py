#!/usr/bin/env python3
import json
import argparse
import itertools
from copy import deepcopy


def resolve_input_source(pipelines, source, metadata):
    """Recursively resolve an input source to its file patterns"""
    parts = source.split(".")
    pipeline_name = parts[0]
    output_type = parts[2]

    if pipeline_name == "0_Microscope":
        # Base case: get patterns directly from Microscope outputs
        return pipelines[pipeline_name]["outputs"][output_type]["patterns"]

    # Get the pipeline that produces this output
    pipeline = pipelines[pipeline_name]
    output_patterns = pipeline["outputs"][output_type]["patterns"]

    # Substitute metadata in patterns
    resolved_patterns = []
    for pattern in output_patterns:
        resolved_pattern = pattern
        for key, value in metadata.items():
            resolved_pattern = resolved_pattern.replace(f"{{{key}}}", str(value))
        resolved_patterns.append(resolved_pattern)

    return resolved_patterns


def get_microscope_channel(channel, channel_type, mappings):
    """Get the microscope channel for a logical channel"""
    mapping = mappings.get(channel_type, {}).get("microscope_mapping", {})
    for mic_ch, log_ch in mapping.items():
        if log_ch == channel:
            return mic_ch
    return None


def apply_metadata_to_pattern(pattern, metadata):
    """Apply all metadata substitutions to a pattern"""
    result = pattern
    for key, value in metadata.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def expand_channel_pattern(pattern, channel, channel_type, microscope_var, mappings):
    """Expand a pattern with channel and microscope mappings"""
    result = pattern

    # Handle microscope channel mapping
    if microscope_var in result:
        microscope_channel = get_microscope_channel(channel, channel_type, mappings)
        if microscope_channel:
            result = result.replace(microscope_var, microscope_channel)

    # Direct channel substitution
    channel_var = f"{{{channel_type}_channel}}"
    result = result.replace(channel_var, channel)

    return result


def process_field(
    field_name,
    field_source,
    pipeline,
    pipelines,
    metadata,
    cycles,
    channel_type,
    channels,
    mappings,
    pipeline_name,
    uses_tile_number=False,
    tile_numbers=None,
):
    """Process a single field with channel and cycle expansion"""
    results = []

    # Skip if source is not specified
    if not field_source:
        return results

    # Get input information
    if not field_source.startswith("inputs."):
        return results

    input_name = field_source.split(".")[1]
    if input_name not in pipeline.get("inputs", {}):
        return results

    input_source = pipeline["inputs"][input_name]["source"]

    # Resolve pattern based on whether this is a cycle-dependent field
    needs_cycle = "{cycle}" in field_name
    cycle_patterns = {}

    if needs_cycle:
        # Create cycle-specific patterns for each cycle
        for cycle in cycles:
            cycle_metadata = deepcopy(metadata)
            cycle_metadata["cycle"] = cycle
            patterns = resolve_input_source(pipelines, input_source, cycle_metadata)
            if patterns:
                cycle_patterns[cycle] = patterns[0]
    else:
        # Just get a single pattern
        patterns = resolve_input_source(pipelines, input_source, metadata)
        if not patterns:
            return results
        for cycle in cycles:
            cycle_patterns[cycle] = patterns[0]

    # Process each channel
    for channel in channels:
        base_name = field_name.replace(f"{{{channel_type}_channel}}", channel)

        for cycle, pattern in cycle_patterns.items():
            # Replace cycle in field name if needed
            if needs_cycle:
                expanded_name = base_name.replace("{cycle}", str(cycle))
            else:
                expanded_name = base_name

            # Apply metadata to pattern
            cycle_metadata = deepcopy(metadata)
            if needs_cycle:
                cycle_metadata["cycle"] = cycle

            expanded_pattern = apply_metadata_to_pattern(pattern, cycle_metadata)

            # Apply channel mapping and substitution
            microscope_var = f"{{{channel_type}_microscope_channel}}"
            expanded_pattern = expand_channel_pattern(
                expanded_pattern, channel, channel_type, microscope_var, mappings
            )

            # Handle cycle substitution if needed
            if "{cycle}" in expanded_pattern:
                expanded_pattern = expanded_pattern.replace("{cycle}", str(cycle))

            # Special handling for tile_number
            if uses_tile_number and "{tile_number}" in expanded_pattern:
                if tile_numbers:
                    # Use the current tile_number from the metadata
                    tile_number = metadata.get("tile_number", "1")
                    expanded_pattern = expanded_pattern.replace(
                        "{tile_number}", str(tile_number)
                    )
            else:
                # Replace any remaining tile_number with default value "1"
                if "{tile_number}" in expanded_pattern:
                    expanded_pattern = expanded_pattern.replace("{tile_number}", "1")

            results.append({"name": expanded_name, "value": expanded_pattern})

    return results


def expand_fields(io_json_path, config=None):
    """Expand all fields in the load_data_csv_config for all pipelines"""
    # Default config if none provided
    if config is None:
        config = {
            "metadata": {
                "batch": "Batch1",
                "plate": "Plate1",
                "well": "A01",
                "site": 1,
                "raw_image_template": "FOV",
            },
            "cycles": [1, 2],
            "tile_numbers": [1],  # Default to a single tile
            "wells": ["A01"],  # Default to a single well
            "sites": [1],  # Default to a single site
        }

    # Load the io.json file
    with open(io_json_path, "r") as f:
        io_data = json.load(f)

    # Extract metadata and pipelines
    metadata_schema = io_data.pop("metadata_schema")
    pipelines = io_data

    # Extract channel lists and mappings
    cp_channels = metadata_schema.get("cp_channel", {}).get("enum", [])
    bc_channels = metadata_schema.get("bc_channel", {}).get("enum", [])
    channel_mappings = metadata_schema.get("channel_mapping", {})

    # Get well, site and tile lists
    wells = config.get("wells", [config["metadata"]["well"]])
    sites = config.get("sites", [config["metadata"]["site"]])
    tile_numbers = config.get("tile_numbers", [1])
    cycles = config["cycles"]

    # Process each pipeline
    results = {}

    for pipeline_name, pipeline in pipelines.items():
        if "load_data_csv_config" not in pipeline:
            continue

        # Create a result container for this pipeline
        pipeline_results = {}

        # Check if this pipeline uses tile_number in its inputs
        uses_tile_numbers = False
        pipeline_inputs = pipeline.get("inputs", {})
        for input_name, input_config in pipeline_inputs.items():
            input_source = input_config.get("source", "")
            source_pipeline_name = (
                input_source.split(".")[0] if "." in input_source else ""
            )
            source_output_type = (
                input_source.split(".")[2] if len(input_source.split(".")) > 2 else ""
            )

            if source_pipeline_name and source_output_type:
                source_pipeline = pipelines.get(source_pipeline_name, {})
                source_patterns = (
                    source_pipeline.get("outputs", {})
                    .get(source_output_type, {})
                    .get("patterns", [])
                )

                for pattern in source_patterns:
                    if "{tile_number}" in pattern:
                        uses_tile_numbers = True
                        break

            if uses_tile_numbers:
                break

        # Determine what location parameter to iterate over
        location_param_values = []
        if uses_tile_numbers:
            # Use combinations of well, site, and tile for this pipeline
            location_param_values = list(itertools.product(wells, sites, tile_numbers))
        else:
            # Use just well and site combinations
            location_param_values = list(itertools.product(wells, sites))

        # Process each location combination
        for location_params in location_param_values:
            if uses_tile_numbers:
                well, site, tile = location_params
                location_key = f"{well}-{site}-{tile}"

                # Create metadata for this combination
                metadata = deepcopy(config["metadata"])
                metadata["well"] = well
                metadata["site"] = site
                metadata["tile_number"] = tile
            else:
                well, site = location_params
                location_key = f"{well}-{site}"

                # Create metadata for this combination
                metadata = deepcopy(config["metadata"])
                metadata["well"] = well
                metadata["site"] = site

            # Get the load_data_csv_config
            load_data_config = pipeline["load_data_csv_config"]
            grouping_keys = load_data_config["grouping_keys"]
            fields = load_data_config["fields"]

            # Check if cycle is a grouping dimension
            cycle_is_grouping_key = "cycle" in grouping_keys

            if cycle_is_grouping_key:
                # Create a cycle-grouped result for this location
                cycle_grouped_fields = {}

                for cycle in cycles:
                    cycle_fields = []
                    cycle_metadata = deepcopy(metadata)
                    cycle_metadata["cycle"] = cycle

                    for field in fields:
                        field_name = field["name"]
                        field_source = field.get("source", "")

                        # Handle metadata fields
                        if field_name.startswith("Metadata_"):
                            meta_key = field_name[9:]
                            if meta_key == "SBSCycle" and "cycle" in cycle_metadata:
                                cycle_fields.append(
                                    {"name": field_name, "value": cycle}
                                )
                            elif meta_key in cycle_metadata:
                                cycle_fields.append(
                                    {
                                        "name": field_name,
                                        "value": cycle_metadata[meta_key],
                                    }
                                )
                            continue

                        # Process channel fields
                        if "{cp_channel}" in field_name:
                            expanded = process_field(
                                field_name,
                                field_source,
                                pipeline,
                                pipelines,
                                cycle_metadata,
                                [cycle],
                                "cp",
                                cp_channels,
                                channel_mappings,
                                pipeline_name,
                                uses_tile_numbers,
                            )
                            cycle_fields.extend(expanded)
                        elif "{bc_channel}" in field_name:
                            expanded = process_field(
                                field_name,
                                field_source,
                                pipeline,
                                pipelines,
                                cycle_metadata,
                                [cycle],
                                "bc",
                                bc_channels,
                                channel_mappings,
                                pipeline_name,
                                uses_tile_numbers,
                            )
                            cycle_fields.extend(expanded)

                    cycle_grouped_fields[cycle] = cycle_fields

                pipeline_results[location_key] = cycle_grouped_fields
            else:
                # Regular field expansion
                expanded_fields = []

                for field in fields:
                    field_name = field["name"]
                    field_source = field.get("source", "")
                    condition = field.get("condition", "")

                    # Handle metadata fields
                    if field_name.startswith("Metadata_"):
                        meta_key = field_name[9:]
                        if meta_key in metadata:
                            expanded_fields.append(
                                {"name": field_name, "value": metadata[meta_key]}
                            )
                        continue

                    # Process channel fields
                    if "{cp_channel}" in field_name:
                        expanded = process_field(
                            field_name,
                            field_source,
                            pipeline,
                            pipelines,
                            metadata,
                            [0],
                            "cp",
                            cp_channels,
                            channel_mappings,
                            pipeline_name,
                            uses_tile_numbers,
                        )
                        expanded_fields.extend(expanded)
                    elif "{bc_channel}" in field_name:
                        # For bc_channel fields, we need to check the condition
                        valid_cycles = []
                        for cycle in cycles:
                            if not condition or eval(condition, {"cycle": cycle}):
                                valid_cycles.append(cycle)

                        expanded = process_field(
                            field_name,
                            field_source,
                            pipeline,
                            pipelines,
                            metadata,
                            valid_cycles,
                            "bc",
                            bc_channels,
                            channel_mappings,
                            pipeline_name,
                            uses_tile_numbers,
                        )
                        expanded_fields.extend(expanded)

                pipeline_results[location_key] = expanded_fields

        # Add this pipeline's results to the overall results
        results[pipeline_name] = pipeline_results

    return results


def print_expanded_fields(results):
    """Print the expanded fields in a readable format"""
    # Iterate through pipelines
    for pipeline_name, locations in results.items():
        print(f"\n\n=== Pipeline: {pipeline_name} ===")

        # Print each location's results
        for location_key, fields in locations.items():
            print(f"\n== Location: {location_key} ==")

            # Check if this location has cycle-grouped fields
            if isinstance(fields, dict) and all(
                isinstance(key, int) for key in fields.keys()
            ):
                # Print each cycle's fields separately
                for cycle, cycle_fields in fields.items():
                    print(f"\n--- Cycle {cycle} ---")
                    for field in cycle_fields:
                        print(f"{field['name']}: {field['value']}")
            else:
                # Regular non-cycle-grouped fields
                for field in fields:
                    print(f"{field['name']}: {field['value']}")


def save_expanded_fields_as_json(results, output_file):
    """Save the expanded fields to a JSON file"""
    # Convert cycle keys from int to str for JSON serialization
    json_results = {}

    for pipeline_name, locations in results.items():
        pipeline_json = {}

        for location_key, fields in locations.items():
            if isinstance(fields, dict) and all(
                isinstance(key, int) for key in fields.keys()
            ):
                # Convert cycle keys to strings for JSON
                pipeline_json[location_key] = {
                    str(cycle): cycle_fields for cycle, cycle_fields in fields.items()
                }
            else:
                pipeline_json[location_key] = fields

        json_results[pipeline_name] = pipeline_json

    with open(output_file, "w") as f:
        json.dump(json_results, f, indent=2)

    print(f"Expanded fields saved to: {output_file}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Expand fields for CellProfiler pipelines"
    )
    parser.add_argument(
        "--io_json", type=str, default="docs/io.json", help="Path to the io.json file"
    )
    parser.add_argument("--config", type=str, help="Path to a JSON config file")
    parser.add_argument("--batch", type=str, default="Batch1", help="Batch identifier")
    parser.add_argument("--plate", type=str, default="Plate1", help="Plate identifier")
    parser.add_argument(
        "--wells",
        type=str,
        nargs="+",
        default=["A01"],
        help="Well identifiers (e.g. A01 B02)",
    )
    parser.add_argument(
        "--sites", type=int, nargs="+", default=[1], help="Site numbers"
    )
    parser.add_argument(
        "--raw_image_template", type=str, default="FOV", help="Raw image template"
    )
    parser.add_argument(
        "--cycles", type=int, nargs="+", default=[1, 2], help="Cycle numbers"
    )
    parser.add_argument(
        "--tile_numbers", type=int, nargs="+", default=[1, 2, 3, 4], help="Tile numbers"
    )
    parser.add_argument("--output", type=str, help="Output file path for JSON results")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Load config from file if provided
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    else:
        # Create config from command line arguments
        config = {
            "metadata": {
                "batch": args.batch,
                "plate": args.plate,
                "well": args.wells[0],  # Default to first well for basic metadata
                "site": args.sites[0],  # Default to first site for basic metadata
                "raw_image_template": args.raw_image_template,
            },
            "cycles": args.cycles,
            "tile_numbers": args.tile_numbers,
            "wells": args.wells,  # List of all wells to process
            "sites": args.sites,  # List of all sites to process
        }

    # Expand the fields
    results = expand_fields(args.io_json, config)

    # Print the results
    print_expanded_fields(results)

    # Save to JSON if output file is specified
    if args.output:
        save_expanded_fields_as_json(results, args.output)
