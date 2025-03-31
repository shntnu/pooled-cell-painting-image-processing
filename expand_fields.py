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
                "raw_image_template": "FOV",
            },
            "wells": ["A01"],
            "sites": [1],
            "tile_numbers": [1, 2, 3, 4],
            "cycles": [1, 2],
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

    # Get parameters from config
    wells = config.get("wells", ["A01"])
    sites = config.get("sites", [1])
    tile_numbers = config.get("tile_numbers", [1, 2, 3, 4])
    cycles = config.get("cycles", [1, 2])

    # Get basic metadata that's the same for all locations
    base_metadata = config.get("metadata", {})

    # Process each pipeline
    results = {}

    for pipeline_name, pipeline in pipelines.items():
        if "load_data_csv_config" not in pipeline:
            continue

        # Create a result container for this pipeline
        pipeline_results = {}

        # Determine if this pipeline uses tile_number instead of site
        uses_tile_as_location = False
        if pipeline_name == "9_Analysis":
            uses_tile_as_location = True

        # For most pipelines, we use well+site combinations
        # For pipeline 9, we use well+tile combinations
        if uses_tile_as_location:
            # Process combinations of well and tile (pipeline 9)
            for well in wells:
                for tile_number in tile_numbers:
                    # Create a location key
                    location_key = f"{well}-{tile_number}"

                    # Create metadata for this location
                    metadata = deepcopy(base_metadata)
                    metadata["well"] = well
                    metadata["tile_number"] = tile_number

                    # Process the fields for this well + tile combination
                    process_pipeline_fields(
                        pipeline_name,
                        pipeline,
                        pipelines,
                        metadata,
                        cycles,
                        cp_channels,
                        bc_channels,
                        channel_mappings,
                        location_key,
                        pipeline_results,
                    )
        else:
            # Process combinations of well and site (most pipelines)
            for well in wells:
                for site in sites:
                    # Create a location key
                    location_key = f"{well}-{site}"

                    # Create metadata for this location
                    metadata = deepcopy(base_metadata)
                    metadata["well"] = well
                    metadata["site"] = site

                    # Process the fields for this well + site combination
                    process_pipeline_fields(
                        pipeline_name,
                        pipeline,
                        pipelines,
                        metadata,
                        cycles,
                        cp_channels,
                        bc_channels,
                        channel_mappings,
                        location_key,
                        pipeline_results,
                    )

        # Add this pipeline's results to the overall results
        results[pipeline_name] = pipeline_results

    return results


def process_pipeline_fields(
    pipeline_name,
    pipeline,
    pipelines,
    metadata,
    cycles,
    cp_channels,
    bc_channels,
    channel_mappings,
    location_key,
    pipeline_results,
):
    """Process fields for a specific pipeline and location"""
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
                        cycle_fields.append({"name": field_name, "value": cycle})
                    elif meta_key.lower() in ["tile", "site", "well", "plate", "batch"]:
                        # Handle special case for Metadata_Tile which maps to tile_number
                        source_key = (
                            meta_key.lower()
                            if meta_key.lower() != "tile"
                            else "tile_number"
                        )
                        if source_key in cycle_metadata:
                            cycle_fields.append(
                                {
                                    "name": field_name,
                                    "value": cycle_metadata[source_key],
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
                if meta_key.lower() in ["tile", "site", "well", "plate", "batch"]:
                    # Handle special case for Metadata_Tile which maps to tile_number
                    source_key = (
                        meta_key.lower()
                        if meta_key.lower() != "tile"
                        else "tile_number"
                    )
                    if source_key in metadata:
                        expanded_fields.append(
                            {"name": field_name, "value": metadata[source_key]}
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
                    [0],  # Non-cycle fields
                    "cp",
                    cp_channels,
                    channel_mappings,
                    pipeline_name,
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
                )
                expanded_fields.extend(expanded)

        pipeline_results[location_key] = expanded_fields


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
                "raw_image_template": args.raw_image_template,
            },
            "wells": args.wells,
            "sites": args.sites,
            "tile_numbers": args.tile_numbers,
            "cycles": args.cycles,
        }

    # Expand the fields
    results = expand_fields(args.io_json, config)

    # Print the results
    print_expanded_fields(results)

    # Save to JSON if output file is specified
    if args.output:
        save_expanded_fields_as_json(results, args.output)
