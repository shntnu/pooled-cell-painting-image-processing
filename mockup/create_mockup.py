import json
import os
import csv
import argparse
from pathlib import Path
import itertools


class CellProfPipelineMockup:
    def __init__(self, io_json_path):
        """Initialize with the path to the io.json file"""
        with open(io_json_path, "r") as f:
            self.io_specs = json.load(f)

    def generate_load_data_csvs(self, output_dir, params):
        """Generate LoadData CSV files for each pipeline based on io.json specs"""
        os.makedirs(output_dir, exist_ok=True)

        for pipeline_name, pipeline_spec in self.io_specs.items():
            if "load_data_csv_fields" not in pipeline_spec:
                continue

            # Create CSV file for this pipeline
            csv_path = os.path.join(output_dir, f"{pipeline_name}_LoadData.csv")
            print(f"Generating CSV for {pipeline_name} at {csv_path}")

            # Extract fields
            fields = [field["name"] for field in pipeline_spec["load_data_csv_fields"]]

            # Generate rows based on the cartesian product of parameter values
            rows = self._generate_csv_rows(pipeline_spec, params)

            # Write CSV
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

    def _generate_csv_rows(self, pipeline_spec, params):
        """Generate rows for a LoadData CSV based on pipeline spec and params"""
        # Create combinations of parameter values
        param_combinations = []

        # Extract the param combinations we need
        if "plates" in params:
            param_combinations.append(("plate", params["plates"]))
        if "wells" in params:
            param_combinations.append(("well", params["wells"]))
        if "sites" in params:
            param_combinations.append(("site", params["sites"]))
        if "channels" in params:
            param_combinations.append(("channel", params["channels"]))

        # Add cycles if this pipeline needs them
        cycles_needed = any(
            "cycle" in field["name"].lower()
            for field in pipeline_spec.get("load_data_csv_fields", [])
        )
        if cycles_needed and "cycles" in params:
            param_combinations.append(("cycle", params["cycles"]))

        # Generate all combinations
        combinations = list(
            itertools.product(*[values for _, values in param_combinations])
        )
        param_names = [name for name, _ in param_combinations]

        rows = []
        for combo in combinations:
            row = {}
            # Create a parameter dict for this combination
            combo_params = {param_names[i]: combo[i] for i in range(len(combo))}

            # Generate values for each field based on its source
            for field in pipeline_spec.get("load_data_csv_fields", []):
                field_name = field["name"]
                source = field["source"]

                # Skip fields with conditions that aren't met
                if "condition" in field:
                    # Simple condition parsing (only handles cycle>X right now)
                    condition = field["condition"]
                    if condition.startswith("cycle>"):
                        min_cycle = int(condition.split(">")[1])
                        if (
                            "cycle" in combo_params
                            and int(combo_params["cycle"]) <= min_cycle
                        ):
                            continue

                # Handle different field sources
                if source.startswith("inputs."):
                    # Get the pattern from the appropriate input
                    parts = source.split(".")
                    input_type = parts[1]
                    field_type = parts[2]  # filename or path

                    if (
                        input_type in pipeline_spec.get("inputs", {})
                        and "pattern" in pipeline_spec["inputs"][input_type]
                    ):
                        pattern = pipeline_spec["inputs"][input_type]["pattern"]

                        # Replace placeholders with parameter values
                        for param_name, param_value in combo_params.items():
                            pattern = pattern.replace(
                                f"{{{param_name}}}", str(param_value)
                            )

                        # Replace any remaining placeholders with default values
                        for param_name, param_value in params.items():
                            if isinstance(param_value, list):
                                placeholder = f"{{{param_name}}}"
                                if placeholder in pattern:
                                    pattern = pattern.replace(
                                        placeholder, str(param_value[0])
                                    )
                            else:
                                pattern = pattern.replace(
                                    f"{{{param_name}}}", str(param_value)
                                )

                        # Extract filename or path
                        if field_type == "filename":
                            value = os.path.basename(pattern)
                        else:  # path
                            value = os.path.dirname(pattern)
                    else:
                        value = f"MOCK_{input_type}_{field_type}"

                elif source.startswith("metadata."):
                    # Get value from metadata
                    meta_field = source.split(".")[1]
                    if meta_field in combo_params:
                        value = combo_params[meta_field]
                    else:
                        value = f"MOCK_{meta_field}"
                else:
                    value = f"MOCK_{source}"

                # Handle templated field names (like FileName_Orig{Channel})
                templated_field_name = field_name
                for param_name, param_value in combo_params.items():
                    templated_field_name = templated_field_name.replace(
                        f"{{{param_name}}}", param_value
                    )

                row[templated_field_name] = value

            rows.append(row)

        return rows

    def generate_folder_structure(self, output_dir, params):
        """Generate a folder structure mockup based on the io.json file"""
        base_dir = Path(output_dir)
        base_dir.mkdir(exist_ok=True, parents=True)

        created_files = []

        # Process each pipeline's inputs and outputs
        for pipeline_name, pipeline_spec in self.io_specs.items():
            print(f"Generating folder structure for {pipeline_name}")

            # Process inputs
            if "inputs" in pipeline_spec:
                for input_name, input_spec in pipeline_spec["inputs"].items():
                    if "pattern" in input_spec:
                        self._create_mockup_files(
                            base_dir, input_spec["pattern"], params, created_files
                        )
                    elif "patterns" in input_spec:
                        for pattern in input_spec["patterns"]:
                            self._create_mockup_files(
                                base_dir, pattern, params, created_files
                            )

            # Process outputs
            if "outputs" in pipeline_spec:
                for output_name, output_spec in pipeline_spec["outputs"].items():
                    if "pattern" in output_spec:
                        self._create_mockup_files(
                            base_dir, output_spec["pattern"], params, created_files
                        )
                    elif "patterns" in output_spec:
                        for pattern in output_spec["patterns"]:
                            self._create_mockup_files(
                                base_dir, pattern, params, created_files
                            )

        print(f"Created {len(created_files)} files in the mockup structure")
        return created_files

    def _create_mockup_files(self, base_dir, pattern, params, created_files):
        """Create mockup files based on a pattern and parameters"""
        # Find all placeholder keys in the pattern
        keys = []
        for key in params.keys():
            if f"{{{key}}}" in pattern:
                keys.append(key)

        # If we have keys that need to be expanded (with lists of values)
        if keys:
            # Create combinations of values for the keys
            key_values = [
                params[key] if isinstance(params[key], list) else [params[key]]
                for key in keys
            ]
            combinations = itertools.product(*key_values)

            # Create a file for each combination
            for combo in combinations:
                file_pattern = pattern
                for i, key in enumerate(keys):
                    file_pattern = file_pattern.replace(f"{{{key}}}", str(combo[i]))

                # Replace any remaining placeholders with defaults
                for key, value in params.items():
                    if isinstance(value, list):
                        placeholder = f"{{{key}}}"
                        if placeholder in file_pattern:
                            file_pattern = file_pattern.replace(
                                placeholder, str(value[0])
                            )
                    else:
                        file_pattern = file_pattern.replace(f"{{{key}}}", str(value))

                # Create the file
                file_path = base_dir / file_pattern
                self._create_file(file_path)
                created_files.append(str(file_path))
        else:
            # No keys to expand, create a single file
            file_path = base_dir / pattern
            self._create_file(file_path)
            created_files.append(str(file_path))

    def _create_file(self, file_path):
        """Create a mockup file (empty) and its parent directories"""
        # Create parent directories
        file_path.parent.mkdir(exist_ok=True, parents=True)

        # Create the file (if it doesn't exist)
        if not file_path.exists():
            file_extension = file_path.suffix.lower()

            # Create different types of mock files based on extension
            if file_extension == ".npy":
                # Create a mock NPY file
                with open(file_path, "w") as f:
                    f.write("MOCK NPY FILE\n")
            elif file_extension in [".tiff", ".png"]:
                # Create a mock image file
                with open(file_path, "w") as f:
                    f.write(f"MOCK {file_extension.upper()} IMAGE\n")
            elif file_extension == ".csv":
                # Create a mock CSV file with a header
                with open(file_path, "w") as f:
                    f.write(
                        "ObjectNumber,ImageNumber,Metadata_Plate,Metadata_Well,Metadata_Site\n"
                    )
                    f.write("1,1,MOCK_PLATE,MOCK_WELL,MOCK_SITE\n")
            else:
                # Default empty file
                file_path.touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate CellProfiler pipeline mockups"
    )
    parser.add_argument("--io_json", required=True, help="Path to the io.json file")
    parser.add_argument(
        "--output_dir", required=True, help="Output directory for mockups"
    )
    parser.add_argument(
        "--csv_output_dir",
        help="Output directory for CSV files (defaults to output_dir/csvs)",
    )

    # Essential parameters for file path structure
    essential_group = parser.add_argument_group(
        "Essential Parameters", "Parameters required for proper file path generation"
    )
    essential_group.add_argument(
        "--batch", default="2022_01_01_Batch1", help="Batch identifier"
    )
    essential_group.add_argument(
        "--plates", nargs="+", default=["Plate1", "Plate2"], help="Plate identifiers"
    )
    essential_group.add_argument(
        "--wells",
        nargs="+",
        default=["A01", "A02", "B01", "B02"],
        help="Well identifiers",
    )
    essential_group.add_argument(
        "--sites", nargs="+", default=["1", "2", "3", "4"], help="Site numbers"
    )
    essential_group.add_argument(
        "--channels",
        nargs="+",
        default=["DNA", "Phalloidin", "Mito", "ER", "WGA"],
        help="Channel names",
    )
    essential_group.add_argument(
        "--cycles", nargs="+", default=["1", "2", "3", "4"], help="Cycle numbers"
    )
    essential_group.add_argument(
        "--metadata_dir", default="metadata", help="Metadata directory"
    )
    essential_group.add_argument(
        "--raw_image_template", default="img", help="Raw image filename template"
    )
    essential_group.add_argument(
        "--round_or_square", default="square", help="Well shape (round or square)"
    )

    # FIJI script parameters (not essential for mockup but needed for io.json compatibility)
    fiji_group = parser.add_argument_group(
        "FIJI Parameters",
        "Parameters used by FIJI scripts (not essential for mockup but included for io.json compatibility)",
    )
    fiji_group.add_argument(
        "--painting_rows", default="8", help="Number of rows in painting image grid"
    )
    fiji_group.add_argument(
        "--painting_columns",
        default="8",
        help="Number of columns in painting image grid",
    )
    fiji_group.add_argument(
        "--barcoding_rows", default="8", help="Number of rows in barcoding image grid"
    )
    fiji_group.add_argument(
        "--barcoding_columns",
        default="8",
        help="Number of columns in barcoding image grid",
    )
    fiji_group.add_argument(
        "--painting_imperwell", default="64", help="Images per well for painting"
    )
    fiji_group.add_argument(
        "--barcoding_imperwell", default="64", help="Images per well for barcoding"
    )
    fiji_group.add_argument(
        "--stitchorder", default="Grid: snake by rows", help="Stitch order method"
    )
    fiji_group.add_argument("--overlap_pct", default="10", help="Overlap percentage")
    fiji_group.add_argument("--size", default="1024", help="Image size")
    fiji_group.add_argument("--tileperside", default="10", help="Tiles per side")
    fiji_group.add_argument("--final_tile_size", default="1024", help="Final tile size")

    # Other parameters
    other_group = parser.add_argument_group("Other Parameters")
    other_group.add_argument(
        "--object_type",
        nargs="+",
        default=["Cells", "Nuclei", "Cytoplasm"],
        help="Object types for segmentation masks",
    )
    other_group.add_argument(
        "--channel_number",
        nargs="+",
        default=["1", "2", "3", "4", "5"],
        help="Channel numbers for overlay images",
    )
    other_group.add_argument(
        "--tile_number",
        nargs="+",
        default=["1", "2", "3", "4", "5"],
        help="Tile numbers for cropped images",
    )

    args = parser.parse_args()

    # Convert arguments to a parameter dictionary
    params = {
        "batch": args.batch,
        "plates": args.plates,
        "wells": args.wells,
        "sites": args.sites,
        "channels": args.channels,
        "cycles": args.cycles,
        "metadata_dir": args.metadata_dir,
        "raw_image_template": args.raw_image_template,
        "round_or_square": args.round_or_square,
        "painting_rows": args.painting_rows,
        "painting_columns": args.painting_columns,
        "barcoding_rows": args.barcoding_rows,
        "barcoding_columns": args.barcoding_columns,
        "painting_imperwell": args.painting_imperwell,
        "barcoding_imperwell": args.barcoding_imperwell,
        "stitchorder": args.stitchorder,
        "overlap_pct": args.overlap_pct,
        "size": args.size,
        "tileperside": args.tileperside,
        "final_tile_size": args.final_tile_size,
        "object_type": args.object_type,
        "channel_number": args.channel_number,
        "tile_number": args.tile_number,
    }

    # Set CSV output directory
    csv_output_dir = (
        args.csv_output_dir
        if args.csv_output_dir
        else os.path.join(args.output_dir, "csvs")
    )

    # Create mockups
    mockup = CellProfPipelineMockup(args.io_json)
    mockup.generate_load_data_csvs(csv_output_dir, params)
    mockup.generate_folder_structure(args.output_dir, params)
