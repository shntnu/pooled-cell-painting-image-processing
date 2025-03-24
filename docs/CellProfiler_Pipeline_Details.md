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

## Multi-Layered Configuration System

The pooled cell painting workflow employs a three-tiered configuration approach where each layer controls different aspects of the pipeline execution. Understanding this configuration hierarchy is essential for setting up and troubleshooting the workflow.

### Experiment Configuration: metadata.json

The `metadata.json` file (based on `configs/metadatatemplate.json`) controls the experimental parameters and image processing logic:

1. **Image Grid Configuration**:
   - `painting_rows`, `painting_columns`, `painting_imperwell`: Define cell painting image layout
   - `barcoding_rows`, `barcoding_columns`, `barcoding_imperwell`: Define barcoding image layout
   - These determine how many images should be expected per well

2. **Channel Dictionary Configuration**:
   ```json
   "Channeldict":"{'round0':{'DAPI':['DNA_round0',0], 'GFP':['Phalloidin',1]}, 'round1':{'DAPI':['DNA_round1',0],'GFP':['GM130',1], ...}}"
   ```
   - Maps microscope channel names to biological stains
   - Supports both single-round and multi-round (SABER) experiments
   - First value is the stain name, second is the frame index
   - Influences which images are processed and how they're organized

3. **Processing Configuration**:
   - `one_or_many_files`: Controls if each well is stored as a single file or multiple files
   - `fast_or_slow_mode`: Determines CSV generation strategy and processing path
   - `barcoding_cycles`: Sets the number of barcoding cycles to process

4. **Stitching Configuration**:
   - `overlap_pct`: Controls image overlap percentage
   - `stitchorder`: Specifies tile arrangement (e.g., "Grid: snake by rows")
   - `tileperside` and `final_tile_size`: Define output tile dimensions

### Computing Resource Configuration: Lambda config_dict

Each Lambda function contains a `config_dict` Python dictionary that controls AWS resource allocation and job execution parameters:

```python
config_dict = {
    "APP_NAME": "2018_11_20_Periscope_X_IllumPainting",
    "DOCKERHUB_TAG": "cellprofiler/distributed-cellprofiler:2.0.0_4.2.1",
    "TASKS_PER_MACHINE": "1",
    "MACHINE_TYPE": ["c5.xlarge"],
    "MEMORY": "7500",
    "DOCKER_CORES": "4",
    "CHECK_IF_DONE_BOOL": "True",
    "EXPECTED_NUMBER_FILES": "5",
    # Additional parameters...
}
```

These settings must be configured for each Lambda function and control:
- The AWS resource allocation (machine type, memory, cores)
- Job execution parameters (tasks per machine, timeout)
- Quality control thresholds (expected file count, minimum size)
- Docker container selection and configuration

### Infrastructure Configuration: AWS Config Files

The system uses two additional configuration files for AWS infrastructure:

1. **configFleet.json**: Controls the AWS Spot Fleet configuration:
   - EC2 instance types and AMIs
   - Network configuration (subnets, security groups)
   - IAM roles and policies
   - EBS volume configurations

2. **configAWS.py**: Contains general AWS settings:
   - AWS region and profile
   - S3 bucket names
   - ECS cluster names
   - SQS queue identifiers

### Pipeline Configuration via CSV Files

The three configuration layers work together to drive pipeline execution through CSV files:

1. **metadata.json** → Determines WHAT data gets processed and HOW
2. **Lambda config_dict** → Controls HOW MUCH computing resources are allocated
3. **AWS config files** → Define WHERE in AWS the processing happens

The CSV generation logic in `lambda/lambda_functions/create_CSVs.py` contains specialized functions for each pipeline stage that translate metadata parameters into CellProfiler-compatible configurations:

- **FileName_X** and **PathName_X** columns for each channel
- **Metadata_X** columns for grouping and organization
- **Frame_X** and **Series_X** columns for multi-channel files

This configuration hierarchy enables the system to adapt to different experimental designs, resource requirements, and infrastructure environments independently.

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

## How the Configuration Layers Drive the Pipeline Workflow

The pipeline workflow integrates all three configuration layers to orchestrate image processing:

1. **Lambda initializes**: Triggered by upload of prior stage results (see trigger events in the table above)
2. **Configuration loading**:
   - Reads experiment parameters from metadata.json
   - Uses internal config_dict for AWS resource configuration
   - Downloads infrastructure configuration files (configFleet.json) when needed
3. **Pipeline configuration decisions**:
   - **From metadata.json**: Determines pipeline variant and processing parameters
     ```python
     if len(Channeldict.keys()) == 1:  # Standard experiment
         pipeline_name = "1_CP_Illum.cppipe"
     if len(Channeldict.keys()) > 1:   # SABER experiment
         pipeline_name = "1_SABER_CP_Illum.cppipe"
     ```
   - **From config_dict**: Determines computing resources and validation thresholds
     ```python
     "MACHINE_TYPE": ["c5.xlarge"],
     "MEMORY": "7500",
     "EXPECTED_NUMBER_FILES": "5",
     ```
   - **From AWS config files**: Determines where processing will happen in AWS
4. **CSV generation**: Creates LoadData CSV that implements the combined configuration:
   - File paths and processing logic from metadata.json
   - Image organization based on metadata parameters (one_or_many_files, fast_or_slow_mode)
   - Job structure influenced by config_dict resource allocation
5. **AWS Batch job creation**: Uses run_DCP.py and create_batch_jobs.py to:
   - Configure Docker container parameters from config_dict
   - Set up EC2 fleet using configFleet.json
   - Configure timeout and visibility based on config_dict
6. **Pipeline execution**: CellProfiler processes images according to all configuration layers
7. **Result validation**: Uses config_dict parameters (EXPECTED_NUMBER_FILES, CHECK_IF_DONE_BOOL) to verify completion
8. **Next stage triggering**: Completion triggers the next Lambda function

This multi-layered configuration approach enables several advantages:

1. **Separation of concerns**:
   - Experiment design parameters (metadata.json)
   - Computing resource allocation (config_dict)
   - Infrastructure configuration (AWS config files)
   
2. **Adaptability at multiple levels**:
   - Process different experimental designs by modifying metadata.json
   - Adjust resource allocation for specific pipeline stages via each Lambda's config_dict
   - Change AWS infrastructure without affecting pipeline logic

3. **Flexible optimization**:
   - Tune computing resources for cost/performance without changing experiment parameters
   - Adjust experiment parameters without reconfiguring AWS resources

The image processing behavior is tailored through the combined influence of all configuration layers, with specific aspects controlled by each layer:

1. **Metadata.json controls**:
   - Image organization (one_or_many_files, fast_or_slow_mode)
   - Channel selection (Channeldict mapping)
   - Grid configuration (rows, columns, imperwell parameters)
   - Stitching behavior (overlap_pct, stitchorder, quarter_if_round)

2. **Lambda config_dict controls**:
   - Processing performance (machine type, memory, cores)
   - Job timeout and visibility settings
   - Quality control thresholds (expected files, minimum size)

3. **AWS config files control**:
   - Infrastructure location and configuration
   - Network settings and IAM roles
   - EC2 fleet parameters

## Setting Up a New Experiment

To set up a new experiment with this workflow, you need to configure all three layers:

### 1. Experiment Configuration (metadata.json)

Create a metadata.json file based on the template with experiment-specific parameters:

- **Image Grid Configuration**:
  - Cell painting acquisition grid (`painting_rows`, `painting_columns`, `painting_imperwell`)
  - Barcoding acquisition grid (`barcoding_rows`, `barcoding_columns`, `barcoding_imperwell`)
  
- **Channel Dictionary**:
  - Map microscope channels to stains across imaging rounds
  - For single-round: `{'20X_CP':{'DAPI':['DNA', 0], 'GFP':['Phalloidin',1]}}`
  - For multi-round SABER: `{'round0':{'DAPI':['DNA_round0',0], ...}, 'round1':{...}}`
  
- **Acquisition Parameters**:
  - Number of barcoding cycles (`barcoding_cycles`)
  - Fast/slow acquisition mode (`fast_or_slow_mode`)
  - One/many files per well (`one_or_many_files`)
  
- **Stitching Configuration**:
  - Overlap percentage (`overlap_pct`)
  - Stitching order (`stitchorder`)
  - Well shape (`round_or_square`, `quarter_if_round`)
  - Output tile dimensions (`tileperside`, `final_tile_size`)

### 2. Computing Resource Configuration (Lambda config_dict)

Modify each Lambda function's `config_dict` to set appropriate resource allocation:

- **Update APP_NAME**: Set a project-specific identifier (e.g., "MyProject_IllumPainting")
- **Adjust compute resources**:
  - Set appropriate `MACHINE_TYPE` for each pipeline step's requirements
  - Configure `MEMORY` and `DOCKER_CORES` based on pipeline needs
  - Set `EBS_VOL_SIZE` according to expected data volume
- **Set validation parameters**:
  - Configure `EXPECTED_NUMBER_FILES` per the table above for each Lambda
  - Set appropriate `CHECK_IF_DONE_BOOL` and `NECESSARY_STRING`
- **Configure timeout settings**:
  - Set `SECONDS_TO_START` and `SQS_MESSAGE_VISIBILITY` for job monitoring

### 3. Infrastructure Configuration (AWS config files)

Prepare and upload AWS configuration files:

- **configFleet.json**:
  - Update EC2 instance settings (`ImageId`, network configurations)
  - Configure IAM roles and security groups
  - Set EBS volume parameters
  
- **configAWS.py**:
  - Update AWS region and profile
  - Configure S3 bucket names
  - Set ECS cluster names and SQS queue identifiers

### 4. Deploy and Trigger

After configuring all three layers:

1. Upload all configuration files to the appropriate S3 locations
2. Upload CellProfiler pipelines for your specific barcoding cycle count
3. Deploy the Lambda functions with their updated config_dict parameters
4. Trigger the workflow by uploading the appropriate file to S3 (typically 1_CP_Illum.cppipe)

This three-layered configuration approach provides flexibility at multiple levels:

- **Experiment flexibility**: Change experimental parameters without modifying code
- **Resource optimization**: Tune compute resources for each pipeline stage independently
- **Infrastructure portability**: Move the workflow between AWS environments by updating only the infrastructure configuration

By properly configuring all three layers, you can ensure the workflow runs efficiently while maintaining consistent processing across different experimental designs.