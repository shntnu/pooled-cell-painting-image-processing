# CellProfiler Pipeline Mockup Generator

This utility helps you generate:
1. LoadData CSV files for CellProfiler pipelines based on the io.json specification
2. A full folder structure mockup including all input/output files for the Cell Painting pipeline workflows

## Requirements

- Python 3.6+
- io.json file (located in docs/io.json in the main repository)

## Usage

```bash
# Basic usage with minimal parameters
python create_mockup.py --io_json ../docs/io.json --output_dir ./mockup_output \
  --plates Plate1 --wells A01 --sites 1 --channels DNA --cycles 1
```

This will create:
- A folder structure mockup in `./mockup_output`
- LoadData CSV files in `./mockup_output/csvs`

## Command Line Arguments

### Required Arguments

- `--io_json`: Path to the io.json specification file
- `--output_dir`: Directory where the mockup should be created

### Optional Arguments

- `--csv_output_dir`: Where to output LoadData CSV files (default: `output_dir/csvs`)

### Essential Parameters (needed for file paths)

These parameters directly affect the file paths and are needed for proper mockup generation:

- `--batch`: Batch identifier (default: '2022_01_01_Batch1')
- `--plates`: Plate identifiers (default: ['Plate1', 'Plate2'])
- `--wells`: Well identifiers (default: ['A01', 'A02', 'B01', 'B02'])
- `--sites`: Site numbers (default: ['1', '2', '3', '4'])
- `--channels`: Channel names (default: ['DNA', 'Phalloidin', 'Mito', 'ER', 'WGA'])
- `--cycles`: Cycle numbers (default: ['1', '2', '3', '4'])
- `--metadata_dir`: Metadata directory (default: 'metadata')
- `--raw_image_template`: Raw image filename template (default: 'img')
- `--round_or_square`: Well shape (default: 'square') - affects whether quadrant naming is used

### FIJI Parameters (not essential for mockup)

These parameters are included for compatibility with the io.json specification but don't meaningfully affect the mockup structure. They're only used as placeholder values in file paths:

- `--painting_rows`, `--painting_columns`: Image grid dimensions for cell painting
- `--barcoding_rows`, `--barcoding_columns`: Image grid dimensions for barcoding
- `--painting_imperwell`, `--barcoding_imperwell`: Images per well
- `--stitchorder`: Stitch order method
- `--overlap_pct`: Overlap percentage
- `--size`: Image size
- `--tileperside`: Tiles per side
- `--final_tile_size`: Final tile size

### Other Parameters

- `--object_type`: Object types for segmentation masks (default: ['Cells', 'Nuclei', 'Cytoplasm'])
- `--channel_number`: Channel numbers for overlay images (default: ['1', '2', '3', '4', '5'])
- `--tile_number`: Tile numbers for cropped images (default: ['1', '2', '3', '4', '5'])

## Examples

### Creating a minimal mockup with only essential parameters

```bash
python create_mockup.py --io_json ../docs/io.json --output_dir ./minimal_mockup \
  --plates Plate1 --wells A01 --sites 1 --channels DNA --cycles 1
```

### Creating a mockup with specific plates and wells

```bash
python create_mockup.py --io_json ../docs/io.json --output_dir ./custom_mockup \
  --plates Plate1 Plate2 Plate3 \
  --wells A01 A02 A03 B01 B02 B03
```

### Creating a mockup with round wells

```bash
python create_mockup.py --io_json ../docs/io.json --output_dir ./round_well_mockup \
  --round_or_square round
```

## Test Scripts

The directory contains several helper scripts:

- `example.sh`: A simple example script showing basic usage
- `test_mockup.sh`: A comprehensive test script that generates and validates a mockup
- `verify_csvs.py`: A utility to validate the generated CSV files against the io.json specification

## Generated Structure

The mockup will contain the complete folder structure for all pipelines in the Cell Painting workflow, including:

1. Raw images (inputs for Pipeline 1 and Pipeline 5)
2. Illumination correction files (outputs from Pipeline 1 and Pipeline 5)
3. Corrected images (outputs from Pipeline 2 and Pipeline 6)
4. Aligned images (outputs from Pipeline 6)
5. Segmentation check images (outputs from Pipeline 3)
6. Processed barcoding images (outputs from Pipeline 7)
7. Stitched images for both cell painting and barcoding (outputs from Pipeline 4 and Pipeline 8)
8. Cropped tiles (outputs from Pipeline 4 and Pipeline 8)
9. Analysis outputs (from Pipeline 9)

## LoadData CSV Files

The utility generates appropriate LoadData CSV files for each pipeline with the correct column structure:

- Pipeline 1: FileName_Orig{Channel}, PathName_Orig{Channel}, Metadata_Plate, Metadata_Well, Metadata_Site
- Pipeline 2: Same as Pipeline 1 plus FileName_Illum{Channel}, PathName_Illum{Channel}
- Pipeline 3: FileName_{Channel}, PathName_{Channel}, Metadata columns
- Pipeline 5: Similar to Pipeline 1 but with Metadata_SBSCycle
- Pipeline 6: FileName_Cycle{K}_{Channel}, PathName_Cycle{K}_{Channel}, etc.
- Pipeline 7: Similar to Pipeline 6 with aligned image paths
- Pipeline 9: Combines channels from both cell painting and barcoding

These CSV files can be used directly with CellProfiler's LoadData module for testing or development. 