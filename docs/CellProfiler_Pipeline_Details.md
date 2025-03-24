# CellProfiler Pipeline Details for Pooled Cell Painting

This document provides a comprehensive explanation of the CellProfiler pipelines used in the Pooled Cell Painting image processing workflow, including how they're configured and connected through AWS Lambda functions.

## Overview

The image processing workflow consists of two parallel tracks followed by a combined analysis:

1. **Cell Painting Processing** (Pipelines 1-4)
2. **Barcoding Processing** (Pipelines 5-8)
3. **Combined Analysis** (Pipeline 9)

Each pipeline is launched by a corresponding AWS Lambda function that configures input/output paths, prepares metadata, and creates CSV files to drive the CellProfiler analysis.

![Pooled Cell Painting Workflow Overview](overview.png)

The diagram above illustrates the complete workflow with both Cell Painting (top row) and Barcoding (middle row) image processing tracks, followed by the combined analysis step. The pipeline numbers correspond to the CellProfiler pipelines described in this document.

## Lambda Function Configuration

Each Lambda function in the workflow requires specific configuration to function properly. These settings are defined in the `config_dict` section of each Lambda function:

| Lambda Function | Trigger Event | APP_NAME Configuration | Expected Files | Output Location | Output Structure |
|-----------------|---------------|------------------------|----------------|-----------------|------------------|
| PCP-1-CP-IllumCorr | 1_CP_Illum.cppipe upload | PROJECT_IllumPainting | # of cell painting channels (5) | illum/PLATE/ | Per-plate |
| PCP-2-CP-ApplyIllum | IllumMito.npy file upload | PROJECT_ApplyIllumPainting | (# CP Channels * # sites) + 5 for CSVs | images_corrected/painting/ | Per-plate, per-well |
| PCP-3-CP-SegmentCheck | PaintingIllumApplication_Image.csv upload | PROJECT_PaintingSegmentationCheck | CHECK_IF_DONE_BOOL set to False | images_segmentation/PLATE/ | Per-plate, per-well, per-site |
| PCP-4-CP-Stitching | SegmentationCheck_Experiment.csv upload | PROJECT_PaintingStitching | N/A | images_corrected_cropped/, images_corrected_stitched/, images_corrected_stitched_10X/ | Per-plate, per-well |
| PCP-5-BC-IllumCorr | 5_BC_Illum.cppipe upload | PROJECT_IllumBarcoding | # Barcoding channels (5) * # plates (1) * # cycles(8) | illum/PLATE/ | Per-plate |
| PCP-6-BC-ApplyIllum | Cycle1_IllumA.npy upload | PROJECT_ApplyIllumBarcoding | CHECK_IF_DONE_BOOL set to False | images_aligned/barcoding/ | Per-plate, per-well, per-site |
| PCP-7-BC-Preprocess | BarcodingApplication_Experiment.csv upload | PROJECT_PreprocessBarcoding | # CSVs (8) + 1 (overlay) + cycles(8) * (#bases + DAPI (5)) = 49 | images_corrected/barcoding | Per-plate, per-well, per-site |
| PCP-8-BC-Stitching | BarcodePreprocessing_Experiment.csv upload | PROJECT_BarcodingStitching | Calculated in the lambda function | images_corrected_cropped/, images_corrected_stitched/, images_corrected_stitched_10X/ | Per-plate, per-well |
| PCP-9-Analysis | Manual trigger with empty event | PROJECT_Analysis | N/A | workspace/analysis/ | Various |

When configuring a new experiment, these parameters need to be set in each Lambda function's configuration. The `APP_NAME` should be changed to include the specific project identifier (e.g., "MyProject_IllumPainting").

The Lambda functions are designed to be triggered sequentially, with each function triggered by the output of the previous step.

## Pipeline Configuration via CSV Files

All pipelines are driven by CSV files generated programmatically by Lambda functions. These CSVs conform to CellProfiler's LoadData module requirements:

- **FileName_X** and **PathName_X** columns for each channel
- **Metadata_X** columns for grouping and organization
- **Frame_X** and **Series_X** columns for multi-channel files

The CSV generation logic in `lambda/lambda_functions/create_CSVs.py` contains specialized functions for each pipeline stage. These functions dynamically generate the appropriate CSV structure based on experiment metadata, using consistent naming conventions that map directly to CellProfiler's expectations.

## Cell Painting Processing Pipelines

### Pipeline 1: Cell Painting Illumination Correction (1_CP_Illum.cppipe)

**Purpose**: Calculate per-plate illumination correction functions for each cell painting channel

**Lambda Function**: `PCP-1-CP-IllumCorr`

**CSV Generation**: `create_CSV_pipeline1()`

**Key Operations**:
1. Loads raw images via CSV configuration
2. For each channel (DNA, ER, Phalloidin, Mito, WGA):
   - Downsample images to 25% size for faster processing
   - Calculate illumination function across all images using median filtering
   - Upsample correction back to original size
3. Save correction functions as .npy files with naming convention: `{Plate}_Illum{Channel}.npy`

**Programmatic Configuration**:
- The LoadData module's input path is configured by the Lambda function
- CSV file specifies image grouping by plate for plate-specific corrections
- Lambda determines single/multi-file mode from metadata.json

### Pipeline 2: Cell Painting Illumination Application (2_CP_Apply_Illum.cppipe)

**Purpose**: Apply illumination correction and segment cells for quality control

**Lambda Function**: `PCP-2-CP-ApplyIllum`

**CSV Generation**: Created by `create_CSV_pipeline1()` (generates two CSVs at once)

**Key Operations**:
1. Apply illumination correction to all channels via division method
2. Identify confluent regions to mask out problem areas
3. Segment nuclei in DNA channel (10-80 pixel diameter)
4. Identify cell boundaries from nuclei using watershed segmentation
5. Export segmentation thresholds for quality control
6. Save corrected images as TIFF files

**Programmatic Configuration**:
- Input CSV includes paths to both raw images and illumination functions
- Well metadata is added for organization and naming
- Segmentation thresholds are automatically calculated and stored for Pipeline 3

### Pipeline 3: Cell Painting Segmentation Check (3_CP_SegmentationCheck.cppipe)

**Purpose**: Verify segmentation quality on a subset of images

**Lambda Function**: `PCP-3-CP-SegmentCheck`

**CSV Generation**: `create_CSV_pipeline3()`

**Key Operations**:
1. Load a subset of corrected images (skipping some sites per Lambda configuration)
2. Apply segmentation using min/max thresholds from Pipeline 2
3. Create color overlay images showing segmentation results
4. Export metrics to validate segmentation quality

**Programmatic Configuration**:
- Uses `range_skip` parameter to process only a subset of images
- Lambda reads segmentation thresholds from Pipeline 2 output
- Input CSV points to corrected images from Pipeline 2

### Pipeline 4: Cell Painting Stitching and Cropping

**Purpose**: Stitch field-of-view images into whole-well montages and create manageable tiles

**Lambda Function**: `PCP-4-CP-Stitching`

**Key Operations**:
1. Stitch multiple fields of view into single whole-well image
2. Generate a smaller (10x) version for preview
3. Crop stitched image into standardized tiles
4. Save output in tiered directory structure by batch and well

**Programmatic Configuration**:
- Stitching uses parameters from metadata.json:
  - Overlap percentage
  - Grid arrangement (rows/columns)
  - Tile coordinates
- Uses a FIJI-based stitching approach (non-CellProfiler)

## Barcoding Processing Pipelines

### Pipeline 5: Barcoding Illumination Correction (5_BC_Illum.cppipe)

**Purpose**: Calculate illumination correction for barcoding images in each cycle

**Lambda Function**: `PCP-5-BC-IllumCorr`

**CSV Generation**: `create_CSV_pipeline5()`

**Key Operations**:
1. Load barcoding images from all cycles
2. For each channel (DNA, A, C, G, T) in each cycle:
   - Downsample for faster processing
   - Calculate illumination function with cycle-specific correction
   - Upsample back to original size
3. Save per-cycle, per-channel correction functions

**Programmatic Configuration**:
- CSV generation handles both fast and slow acquisition modes
- Configured based on one_or_many and fast_or_slow parameters
- Handles different frame positions depending on acquisition configuration

### Pipeline 6: Barcoding Illumination Application (6_BC_Apply_Illum.cppipe)

**Purpose**: Apply illumination correction and align images across channels and cycles

**Lambda Function**: `PCP-6-BC-ApplyIllum`

**CSV Generation**: `create_CSV_pipeline6()`

**Key Operations**:
1. Apply cycle and channel-specific illumination correction
2. Align A, C, G, T channels to DAPI within each cycle
3. Align all cycle DAPI images to Cycle 1 DAPI
4. Shift A, C, G, T channels by same amount as their DAPI image
5. Save corrected and aligned images

**Programmatic Configuration**:
- CSV structure varies significantly between fast and slow acquisition
- Handles arbitrary grouping for memory-efficient processing
- Extremely long pipeline (81+ modules) that's likely generated programmatically

### Pipeline 7: Barcoding Preprocessing (7_BC_Preprocess.cppipe)

**Purpose**: Process aligned barcoding images to identify and characterize barcode foci

**Lambda Function**: `PCP-7-BC-Preprocess`

**CSV Generation**: `create_CSV_pipeline7()`

**Key Operations**:
1. Perform per-image illumination correction grouped by cycle
2. Identify nuclei and cells using DAPI
3. Identify potential barcode foci in each channel
4. Perform histogram matching within foci (optional)
5. Apply channel compensation to correct for spectral bleed-through
6. Rescale foci intensities (optional)
7. Analyze foci intensities and call barcodes
8. Create composite images for QC visualization

**Programmatic Configuration**:
- Uses parsed barcode file information from metadata
- Complex CSV structure to handle all cycles and channels
- Configurable parameters controlled via metadata:
  - Whether to apply histogram matching
  - Whether to apply channel compensation
  - Quality thresholds for barcode calling

### Pipeline 8: Barcoding Stitching and Cropping

**Purpose**: Stitch and crop barcoding images similar to cell painting images

**Lambda Function**: `PCP-8-BC-Stitching`

**Key Operations**:
1. Similar to Pipeline 4, but operates on barcoding images
2. Stitches according to same grid layout as cell painting
3. Produces consistent tile naming for alignment with cell painting tiles

## Final Analysis Pipeline

### Pipeline 9: Analysis (9_Analysis.cppipe)

**Purpose**: Integrate cell painting and barcoding data for downstream analysis

**Lambda Function**: `PCP-9-Analysis`

**CSV Generation**: `create_CSV_pipeline9()`

**Key Operations**:
1. Align cell painting images to barcoding images using DAPI channels
2. Identify and mask overly-confluent regions
3. Segment nuclei, cells, cytoplasm in cell painting images
4. Locate barcode foci in aligned images
5. Measure cell painting features across all compartments
6. Call barcodes and annotate quality metrics
7. Filter objects into quality categories (Perfect, Great, Empty, etc.)
8. Export segmentation masks and merged, annotated images for visualization

**Programmatic Configuration**:
- The most complex CSV structure, integrating all prior pipelines
- Maps both barcoding and cell painting images into a unified view
- Contains channels from all cycles of barcoding
- Contains all cell painting channels
- Sets up proper metadata relationships for integrated analysis

## Special-Purpose Pipelines

In addition to the main pipeline sequence, there are specialized pipelines for troubleshooting:

### 7A_BC_Preprocess_Troubleshooting.cppipe

**Purpose**: Specialized version of Pipeline 7 with additional diagnostics

**Lambda Function**: `PCP-7A-BC-PreprocessTroubleshoot`

**Key Differences**:
- Includes additional QC measurements
- Outputs more diagnostic images
- May use alternative image processing parameters
- Used when standard pipeline produces unexpected results

### 6_BC_Apply_Illum_DebrisMask.cppipe

**Purpose**: Alternative version of Pipeline 6 that identifies and masks debris

**Key Differences**:
- Adds debris identification and masking
- Prevents debris from interfering with alignment
- Used for samples with high debris content

## How the CSV Files Drive the Pipelines

The CSV files serve as the critical link between the Lambda orchestration and CellProfiler execution:

1. **Lambda initializes**: Triggered by upload of prior stage results (see trigger events in the table above)
2. **Metadata parsing**: Reads experiment config from metadata.json
3. **Image identification**: Lists all images in the appropriate S3 buckets
4. **CSV generation**: Creates LoadData CSV with all file paths and grouping
5. **AWS Batch job**: Launches CellProfiler Docker container with appropriate pipeline
6. **Pipeline execution**: CellProfiler reads the CSV and processes images accordingly
7. **Result upload**: Processed files saved back to S3
8. **Next stage triggering**: Completion triggers the next Lambda function

The dynamic generation of these CSVs allows the system to handle different experimental designs without modifying the CellProfiler pipelines themselves. Pipeline behavior is controlled through:

1. **Image grouping** (how CellProfiler treats images together)
2. **Metadata values** (how images are categorized)
3. **File paths** (what images are processed)
4. **QC metrics** (carried between pipeline stages)

## Setting Up a New Experiment

To set up a new experiment with this workflow:

1. **Prepare metadata.json**: Configure experiment-specific parameters including:
   - Cell painting acquisition grid (rows/columns or imperwell for circular)
   - Barcoding acquisition grid
   - Channel dictionary mapping microscope channels to stains
   - Number of barcoding cycles
   - Overlap percentage
   - Fast/slow acquisition mode
   - One/many files per well

2. **Configure AWS resources**:
   - Upload configFleet.json and configAWS.py to S3
   - Upload appropriate CellProfiler pipelines based on number of barcoding cycles

3. **Modify Lambda functions**:
   - Update the config_dict APP_NAME with project-specific identifier
   - Set EXPECTED_NUMBER_FILES per the table above
   - Deploy the changes

4. **Trigger the workflow**:
   - Either upload trigger files to S3 (1_CP_Illum.cppipe)
   - Or manually trigger the first Lambda function with a test event

This architecture enables a robust, flexible workflow that can adapt to different experimental designs while maintaining consistent processing across all images.