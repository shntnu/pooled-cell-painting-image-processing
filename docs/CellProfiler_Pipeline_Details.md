# CellProfiler Pipelines and AWS Lambda Orchestration for Pooled Cell Painting

This document provides a comprehensive explanation of both the CellProfiler pipelines and the AWS Lambda functions that orchestrate them in the Pooled Cell Painting image processing workflow. It includes detailed information on pipeline implementations, Lambda function patterns, configuration parameters, and complete experiment setup instructions.

> **Note:** For a high-level overview of the system architecture and component relationships, see the companion document [Technical_Implementation_Overview.md](./Technical_Implementation_Overview.md).

## Overview

The image processing workflow consists of two parallel tracks followed by a combined analysis:

1. **Cell Painting Processing** (Pipelines 1-4)
2. **Barcoding Processing** (Pipelines 5-8)
3. **Combined Analysis** (Pipeline 9)

Each pipeline is launched by a corresponding AWS Lambda function that configures input/output paths, prepares metadata, and creates CSV files to drive the CellProfiler analysis.

![Pooled Cell Painting Workflow Overview](overview.png)

The diagram above illustrates the complete workflow with both Cell Painting (top row) and Barcoding (middle row) image processing tracks, followed by the combined analysis step. The pipeline numbers correspond to the CellProfiler pipelines described in this document.

The workflow is orchestrated by AWS Lambda functions, with each function responsible for a specific pipeline stage. These Lambda functions serve as the automation backbone that coordinates pipeline execution, handles configuration, and manages the processing of thousands of images across AWS resources.

## Lambda Function Architecture and Implementation

### Pipeline Flow and Triggers

```mermaid
flowchart TD
    subgraph "Cell Painting Track"
        PCP1[PCP-1-CP-IllumCorr] --> PCP2[PCP-2-CP-ApplyIllum]
        PCP2 --> PCP3[PCP-3-CP-SegmentCheck]
        PCP3 --> PCP4[PCP-4-CP-Stitching]
    end
    
    subgraph "Barcoding Track"
        PCP5[PCP-5-BC-IllumCorr] --> PCP6[PCP-6-BC-ApplyIllum]
        PCP6 --> PCP7[PCP-7-BC-Preprocess]
        PCP7 --> PCP8[PCP-8-BC-Stitching]
        PCP8 --> PCP8Y[PCP-8Y-BC-CheckAlignmentPostStitch]
        PCP8Y --> PCP8Z[PCP-8Z-StitchAlignedBarcoding]
    end
    
    PCP4 & PCP8Z --> PCP9[PCP-9-Analysis]
    
    PCP7A[PCP-7A-BC-PreprocessTroubleshoot] -.-> PCP7
```

Each pipeline in the workflow is orchestrated by a corresponding AWS Lambda function (PCP-1 through PCP-9). These Lambda functions automate the pipeline execution and handle the transition of data between stages in a sequential workflow:

1. The workflow begins with two parallel tracks: cell painting processing (PCP-1 through PCP-4) and barcoding processing (PCP-5 through PCP-8)
2. Each Lambda function is triggered by the output of the previous step (typically a file upload to S3)
3. For example, PCP-1-CP-IllumCorr is triggered by the upload of the 1_CP_Illum.cppipe file, and produces illumination function files that then trigger PCP-2-CP-ApplyIllum
4. The final Lambda function (PCP-9-Analysis) integrates the outputs from both tracks for comprehensive analysis

### Lambda Function Implementation Pattern

All Lambda functions in the workflow follow a common implementation pattern:

1. **Trigger Processing**: Responds to S3 event or manual invocation
   - Lambda's `lambda_handler` function is the entry point
   - For S3 triggers: `event["Records"][0]["s3"]["object"]["key"]` extracts the triggering file path
   - For manual triggers (like PCP-9-Analysis): Empty event object is passed with hardcoded parameters

2. **Configuration Loading**: 
   - Loads experiment configuration from metadata.json using `download_and_read_metadata_file()`
   - Contains pipeline-specific AWS resource requirements in `config_dict`
   - May check if previous step's completion using `check_if_run_done()`

3. **Pipeline Selection and Plate Filtering**:
   - Selects appropriate pipeline variant based on experiment configuration
   ```python
   # Example from PCP-1-CP-IllumCorr
   if len(Channeldict.keys()) == 1:  # Standard experiment
       pipeline_name = "1_CP_Illum.cppipe"
   if len(Channeldict.keys()) > 1:   # SABER experiment
       pipeline_name = "1_SABER_CP_Illum.cppipe"
   ```
   - Applies optional plate inclusion/exclusion filters

4. **Input Discovery and CSV Generation**:
   - Uses `paginate_a_folder()` to list all input files efficiently
   - Parses image names using `parse_image_names()` to extract metadata (wells, sites, channels)
   - Creates pipeline-specific CSV file using the appropriate `create_CSV_pipeline*()` function
   - Uploads the generated CSV to S3 for the CellProfiler pipeline to consume

5. **AWS Batch Job Configuration and Execution**:
   - Sets up AWS environment with `run_setup()`
   - Configures batch jobs with the pipeline-specific `create_batch_jobs_*()` function
   - Launches EC2 instances with Docker containers via `run_cluster()`
   - Sets up job completion monitoring with `run_monitor()`

### Key Utility Functions

Each Lambda function relies on a common set of utility modules:

#### From helpful_functions.py:
- **download_and_read_metadata_file()**: Retrieves and parses experiment configuration
- **paginate_a_folder()**: Lists S3 objects with pagination for large image sets
- **parse_image_names()**: Extracts metadata from image filenames
- **write_metadata_file()**: Updates metadata with processing results
- **check_if_run_done()**: Validates job completion status

#### From create_CSVs.py:
- **create_CSV_pipelineN()**: Pipeline-specific CSV generators
- Each translates experiment parameters into CellProfiler-compatible format
- Handles different acquisition modes (fast/slow, one/many files)

#### From run_DCP.py and create_batch_jobs.py:
- Functions for creating and monitoring AWS Batch jobs
- Configures EC2 instances based on pipeline requirements
- Handles container setup and execution

## Pipeline Configuration System

This section details the configuration parameters and settings needed to set up the CellProfiler pipelines for Pooled Cell Painting experiments.

> **Note:** For the architectural overview of the configuration system and its role in the overall workflow, see the [Multi-Layered Configuration Architecture section in the Technical Implementation Overview](./Technical_Implementation_Overview.md#4-multi-layered-configuration-architecture).

### Multi-layered Configuration Architecture

The system employs a three-tiered configuration approach that separates experimental, computational, and infrastructure concerns. This separation allows independent modification of experimental parameters, resource allocation, and AWS infrastructure without requiring wholesale redesign of the system.

```mermaid
flowchart TD
    %% Color-coded configuration sources by layer
    subgraph "Configuration Sources" 
        metadata["metadata.json
        WHAT data to process
        HOW to process it
        (painting_rows, barcoding_cycles, Channeldict)"]:::experimentConfig
        config_dict["Lambda config_dict
        HOW MUCH compute power
        WHEN jobs complete
        (MACHINE_TYPE, MEMORY, EXPECTED_NUMBER_FILES)"]:::computeConfig
        aws_config["AWS config files
        WHERE in AWS to run
        (AWS_REGION, ECS_CLUSTER, IamFleetRole)"]:::infraConfig
    end
    
    subgraph "Configuration Processing" 
        download_metadata["download_and_read_metadata_file
        (in every Lambda function)"]
        grab_config["grab_batch_config
        (loads from S3)"]
        loadConfig["loadConfig
        (processes infrastructure settings)"]
    end
    
    subgraph "Configuration Consumers"
        csv_gen["CSV Generation
        Uses image grid, channels,
        acquisition mode, cycles"]
        batch_creation["Batch Job Creation
        Experiment parameters +
        Resource allocation +
        Infrastructure location"]
        pipeline_selection["Pipeline Selection
        Based on cycle count, channels,
        experiment type"]
        ec2_config["EC2 Configuration
        Subnet, security groups,
        AMI, instance profile"]
    end
    
    %% Configuration flow with numbered sequence
    metadata -->|1. First loaded| download_metadata
    config_dict -->|2. Defined in each Lambda| batch_creation
    aws_config -->|3. Loaded when needed| grab_config
    
    download_metadata --> pipeline_selection
    download_metadata --> csv_gen
    grab_config --> loadConfig
    loadConfig --> ec2_config
    
    pipeline_selection --> batch_creation
    csv_gen --> batch_creation
    ec2_config --> batch_creation
    
    %% Style definitions
    classDef experimentConfig fill:#e6f3ff,stroke:#0066cc
    classDef computeConfig fill:#e6ffe6,stroke:#009900  
    classDef infraConfig fill:#fff2e6,stroke:#ff8c1a
```

#### Configuration Layer Relationships

Each layer serves a distinct purpose in the overall system:

- **Experiment Configuration** (metadata.json): Controls WHAT data is processed and HOW it's processed
- **Computing Resource Configuration** (Lambda config_dict): Specifies HOW MUCH computing power is allocated and WHEN jobs are considered complete
- **Infrastructure Configuration** (AWS config files): Determines WHERE in AWS the processing happens

### Detailed Configuration Parameters

#### 1. Experiment Configuration (metadata.json)

The `metadata.json` file (based on `configs/metadatatemplate.json`) defines all experiment-specific parameters:

##### Image Grid Configuration
- `painting_rows`, `painting_columns`, `painting_imperwell`: Define cell painting image layout
- `barcoding_rows`, `barcoding_columns`, `barcoding_imperwell`: Define barcoding image layout
- These determine how many images should be expected per well

##### Channel Dictionary Configuration
```json
"Channeldict":"{'round0':{'DAPI':['DNA_round0',0], 'GFP':['Phalloidin',1]}, 'round1':{'DAPI':['DNA_round1',0],'GFP':['GM130',1], ...}}"
```
- Maps microscope channel names to biological stains
- Supports both single-round and multi-round (SABER) experiments
- First value is the stain name, second is the frame index
- Influences which images are processed and how they're organized

##### Processing Configuration
- `one_or_many_files`: Controls if each well is stored as a single file or multiple files
- `fast_or_slow_mode`: Determines CSV generation strategy and processing path
- `barcoding_cycles`: Sets the number of barcoding cycles to process

##### Stitching Configuration
- `overlap_pct`: Controls image overlap percentage
- `stitchorder`: Specifies tile arrangement (e.g., "Grid: snake by rows")
- `tileperside` and `final_tile_size`: Define output tile dimensions

#### 2. Computing Resource Configuration (Lambda config_dict)

Each Lambda function contains a specific `config_dict` with pipeline-appropriate settings:

```python
config_dict = {
    "APP_NAME": "2018_11_20_Periscope_X_IllumPainting",
    "DOCKERHUB_TAG": "cellprofiler/distributed-cellprofiler:2.0.0_4.2.1",
    "TASKS_PER_MACHINE": "1",
    "MACHINE_TYPE": ["c5.xlarge"],
    "MEMORY": "7500",
    "DOCKER_CORES": "4",
    "CHECK_IF_DONE_BOOL": "True",
    "EXPECTED_NUMBER_FILES": "5",  # Varies by pipeline
    # Additional parameters...
}
```

The key parameters that need configuration for each pipeline are:
- **APP_NAME**: Unique identifier for the specific experiment
- **MACHINE_TYPE**: EC2 instance type appropriate for the pipeline's computational needs
- **MEMORY**: RAM allocation for the Docker container
- **EXPECTED_NUMBER_FILES**: Number of output files to expect
- **CHECK_IF_DONE_BOOL**: Controls validation of job completion

#### 3. Pipeline-Specific CSV Configuration

Each pipeline is driven by a CSV file with a specific structure generated by functions in `create_CSVs.py`:

| Pipeline                      | CSV Generator Function    | Key Columns                                     | Special Considerations                          |
| ----------------------------- | ------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| 1: CP-Illum                   | `create_CSV_pipeline1()`  | FileName_Orig*, PathName_Orig*, Frame_Orig*     | Generates two CSVs (for pipelines 1 & 2)        |
| 2: CP-ApplyIllum              | (generated by pipeline1)  | PathName_Illum*, FileName_Illum*                | Reuses pipeline1 CSV with illumination paths    |
| 3: SegmentCheck               | `create_CSV_pipeline3()`  | PathName_DNA, FileName_DNA, Metadata_Well       | Uses range_skip parameter for subset processing |
| 4: CP-Stitching               | (external FIJI script)    | (uses file system patterns)                     | Not CSV-driven                                  |
| 5: BC-Illum                   | `create_CSV_pipeline5()`  | Metadata_SBSCycle, PathName_Orig*, Series_Orig* | Mode-dependent structure (fast/slow)            |
| 6: BC-ApplyIllum              | `create_CSV_pipeline6()`  | Cycle*_Orig*, Cycle*_Illum*                     | Complex multi-cycle column structure            |
| 7: BC-Preprocess              | `create_CSV_pipeline7()`  | PathName_Cycle*, FileName_Cycle*                | Cycle-indexed structure with DAPI from Cycle01  |
| 7A: BC-PreprocessTroubleshoot | (uses pipeline7 CSV)      | (same as pipeline7)                             | Uses same CSV structure as pipeline7            |
| 8: BC-Stitching               | (external FIJI script)    | (uses file system patterns)                     | Not CSV-driven                                  |
| 8Y: BC-CheckAlignment         | `create_CSV_pipeline8Y()` | PathName_Cycle01_DAPI, PathName_CorrDNA         | Cross-references painting and barcoding         |
| 9: Analysis                   | `create_CSV_pipeline9()`  | CP_Corr* and Cycle*_* columns                   | Most complex CSV - integrates all data types    |

The CSV files translate configuration parameters into CellProfiler-compatible format using:
- **FileName_X** and **PathName_X** columns for each channel
- **Metadata_X** columns for grouping and organization
- **Frame_X** and **Series_X** columns for multi-channel files
- **Cycle**-prefixed columns for barcoding data

## Cell Painting Processing Pipelines

### Pipeline 1: Cell Painting Illumination Correction (1_CP_Illum.cppipe)

**Purpose**: Calculate per-plate illumination correction functions for each cell painting channel

**Lambda Function**: `PCP-1-CP-IllumCorr`
- **Trigger**: S3 upload of 1_CP_Illum.cppipe
- **CSV Generator**: `create_CSV_pipeline1()`
- **Output**: Illumination function files (.npy)

**Key Operations**:
1. Loads raw images via CSV configuration
2. For each channel (DNA, ER, Phalloidin, Mito, WGA):
   - Downsample images to 25% size for faster processing
   - Calculate illumination function across all images using median filtering
   - Upsample correction back to original size
3. Save correction functions as .npy files with naming convention: `{Plate}_Illum{Channel}.npy`

**Configuration Details**:
- The LoadData module's input path is configured by the Lambda function
- CSV file specifies image grouping by plate for plate-specific corrections
- Lambda determines single/multi-file mode from metadata.json
- Channel names are extracted from the Channeldict in metadata.json

### Pipeline 2: Cell Painting Illumination Application (2_CP_Apply_Illum.cppipe)

**Purpose**: Apply illumination correction and segment cells for quality control

**Lambda Function**: `PCP-2-CP-ApplyIllum`
- **Trigger**: S3 upload of IllumMito.npy (output from Pipeline 1)
- **CSV Generator**: Created by `create_CSV_pipeline1()` (generates two CSVs at once)
- **Output**: Corrected cell images (.tiff) and segmentation parameters

**Key Operations**:
1. Apply illumination correction to all channels via division method
2. Identify confluent regions to mask out problem areas
3. Segment nuclei in DNA channel (10-80 pixel diameter)
4. Identify cell boundaries from nuclei using watershed segmentation
5. Export segmentation thresholds for quality control
6. Save corrected images as TIFF files

**Configuration Details**:
- Input CSV includes paths to both raw images and illumination functions
- Well metadata is added for organization and naming
- Segmentation thresholds are automatically calculated and stored for Pipeline 3
- Lambda function manages AWS Batch resources based on image count

### Pipeline 3: Cell Painting Segmentation Check (3_CP_SegmentationCheck.cppipe)

**Purpose**: Verify segmentation quality on a subset of images

**Lambda Function**: `PCP-3-CP-SegmentCheck`
- **Trigger**: S3 upload of PaintingIllumApplication_Image.csv (from Pipeline 2)
- **CSV Generator**: `create_CSV_pipeline3()`
- **Output**: Quality control overlay images showing segmentation

**Key Operations**:
1. Load a subset of corrected images (skipping some sites per Lambda configuration)
2. Apply segmentation using min/max thresholds from Pipeline 2
3. Create color overlay images showing segmentation results
4. Export metrics to validate segmentation quality

**Configuration Details**:
- Uses `range_skip` parameter to process only a subset of images
- Lambda reads segmentation thresholds from Pipeline 2 output
- Input CSV points to corrected images from Pipeline 2
- Lambda optimizes AWS resources for faster QC processing

### Pipeline 4: Cell Painting Stitching and Cropping

**Purpose**: Stitch field-of-view images into whole-well montages and create manageable tiles

**Lambda Function**: `PCP-4-CP-Stitching`
- **Trigger**: S3 upload of SegmentationCheck_Experiment.csv (from Pipeline 3)
- **Implementation**: Uses FIJI scripts rather than CellProfiler
- **Output**: Stitched and cropped cell painting images

**Key Operations**:
1. Stitch multiple fields of view into single whole-well image
2. Generate a smaller (10x) version for preview
3. Crop stitched image into standardized tiles
4. Save output in tiered directory structure by batch and well

**Configuration Details**:
- Stitching uses parameters from metadata.json:
  - Overlap percentage
  - Grid arrangement (rows/columns)
  - Tile coordinates
- Lambda function executes FIJI scripts via AWS Batch
- Tile size and arrangement are configured per experiment

## Barcoding Processing Pipelines

### Pipeline 5: Barcoding Illumination Correction (5_BC_Illum.cppipe)

**Purpose**: Calculate illumination correction for barcoding images in each cycle

**Lambda Function**: `PCP-5-BC-IllumCorr`
- **Trigger**: S3 upload of 5_BC_Illum.cppipe
- **CSV Generator**: `create_CSV_pipeline5()`
- **Output**: Cycle-specific illumination function files (.npy)

**Key Operations**:
1. Load barcoding images from all cycles
2. For each channel (DNA, A, C, G, T) in each cycle:
   - Downsample for faster processing
   - Calculate illumination function with cycle-specific correction
   - Upsample back to original size
3. Save per-cycle, per-channel correction functions

**Configuration Details**:
- CSV generation handles both fast and slow acquisition modes
- Configured based on one_or_many and fast_or_slow parameters
- Handles different frame positions depending on acquisition configuration
- Lambda sets up AWS resources based on cycle count

### Pipeline 6: Barcoding Illumination Application (6_BC_Apply_Illum.cppipe)

**Purpose**: Apply illumination correction and align images across channels and cycles

**Lambda Function**: `PCP-6-BC-ApplyIllum`
- **Trigger**: S3 upload of Cycle1_IllumA.npy (from Pipeline 5)
- **CSV Generator**: `create_CSV_pipeline6()`
- **Output**: Aligned barcoding images

**Key Operations**:
1. Apply cycle and channel-specific illumination correction
2. Align A, C, G, T channels to DAPI within each cycle
3. Align all cycle DAPI images to Cycle 1 DAPI
4. Shift A, C, G, T channels by same amount as their DAPI image
5. Save corrected and aligned images

**Configuration Details**:
- CSV structure varies significantly between fast and slow acquisition
- Handles arbitrary grouping for memory-efficient processing
- Extremely long pipeline (81+ modules) that's likely generated programmatically
- Lambda manages AWS resources based on cycle count and image count

### Pipeline 7: Barcoding Preprocessing (7_BC_Preprocess.cppipe)

**Purpose**: Process aligned barcoding images to identify and characterize barcode foci

**Lambda Function**: `PCP-7-BC-Preprocess`
- **Trigger**: S3 upload of BarcodingApplication_Experiment.csv (from Pipeline 6)
- **CSV Generator**: `create_CSV_pipeline7()`
- **Output**: Processed barcoding images with foci identification

**Key Operations**:
1. Perform per-image illumination correction grouped by cycle
2. Identify nuclei and cells using DAPI
3. Identify potential barcode foci in each channel
4. Perform histogram matching within foci (optional)
5. Apply channel compensation to correct for spectral bleed-through
6. Rescale foci intensities (optional)
7. Analyze foci intensities and call barcodes
8. Create composite images for QC visualization

**Configuration Details**:
- Uses parsed barcode file information from metadata
- Complex CSV structure to handle all cycles and channels
- Configurable parameters controlled via metadata:
  - Whether to apply histogram matching
  - Whether to apply channel compensation
  - Quality thresholds for barcode calling
- Lambda manages AWS resources based on cycle and channel counts

### Pipeline 8: Barcoding Stitching and Cropping

**Purpose**: Stitch and crop barcoding images similar to cell painting images

**Lambda Function**: `PCP-8-BC-Stitching`
- **Trigger**: S3 upload of BarcodePreprocessing_Experiment.csv (from Pipeline 7)
- **Implementation**: Uses FIJI scripts rather than CellProfiler
- **Output**: Stitched barcoding images

**Key Operations**:
1. Similar to Pipeline 4, but operates on barcoding images
2. Stitches according to same grid layout as cell painting
3. Produces consistent tile naming for alignment with cell painting tiles

**Configuration Details**:
- Uses the same stitching parameters as the cell painting pipeline
- Lambda executes FIJI scripts via AWS Batch
- Ensures consistent tile naming for later alignment with cell painting images

## Final Analysis Pipeline

### Pipeline 9: Analysis (9_Analysis.cppipe)

**Purpose**: Integrate cell painting and barcoding data for downstream analysis

**Lambda Function**: `PCP-9-Analysis`
- **Trigger**: Manual trigger (triggered after both tracks complete)
- **CSV Generator**: `create_CSV_pipeline9()`
- **Output**: Integrated analysis results and segmentation masks

**Key Operations**:
1. Align cell painting images to barcoding images using DAPI channels
2. Identify and mask overly-confluent regions
3. Segment nuclei, cells, cytoplasm in cell painting images
4. Locate barcode foci in aligned images
5. Measure cell painting features across all compartments
6. Call barcodes and annotate quality metrics
7. Filter objects into quality categories (Perfect, Great, Empty, etc.)
8. Export segmentation masks and merged, annotated images for visualization

**Configuration Details**:
- The most complex CSV structure, integrating all prior pipelines
- Maps both barcoding and cell painting images into a unified view
- Contains channels from all cycles of barcoding
- Contains all cell painting channels
- Sets up proper metadata relationships for integrated analysis
- Lambda allocates the largest AWS resources due to complexity

## Special-Purpose Pipelines

In addition to the main pipeline sequence, there are specialized pipelines for troubleshooting:

### 7A_BC_Preprocess_Troubleshooting.cppipe

**Purpose**: Specialized version of Pipeline 7 with additional diagnostics

**Lambda Function**: `PCP-7A-BC-PreprocessTroubleshoot`
- **Trigger**: Manual trigger for troubleshooting
- **Output**: Diagnostic images and measurements

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

## Pipeline-Specific Implementation Details

This section explains how CellProfiler pipelines interact with the configuration system and detailed implementation considerations for each pipeline step.

> **Note:** For the architectural view of how configuration layers interact within the overall system, see the [Workflow Architecture section in the Technical Implementation Overview](./Technical_Implementation_Overview.md#workflow-architecture).

### Pipeline Variant Selection

Lambda functions select specific pipeline variants based on experimental configuration:

```python
# Sample code from PCP-1-CP-IllumCorr
if len(Channeldict.keys()) == 1:  # Standard experiment
    pipeline_name = "1_CP_Illum.cppipe"
if len(Channeldict.keys()) > 1:   # SABER experiment
    pipeline_name = "1_SABER_CP_Illum.cppipe"
```

This dynamic selection allows the same Lambda function to handle different experimental designs without code changes.

### CSV Generation Implementation

Each pipeline stage has a specialized CSV generator function that translates metadata parameters into CellProfiler-compatible input:

1. **Channel Dictionary Parsing**:
   ```python
   # From create_CSV_pipeline1()
   Channeldict = ast.literal_eval(Channeldict)
   rounddict = {}
   Channelrounds = list(Channeldict.keys())
   for eachround in Channelrounds:
       templist = []
       templist += Channeldict[eachround].values()
       channels += list(i[0] for i in templist)
   ```

2. **Acquisition Mode Handling**:
   ```python
   # From create_CSV_pipeline6()
   if one_or_many == "one" and fast_or_slow == "fast":
       # One file structure
   elif one_or_many == "many" and fast_or_slow == "slow":
       # Many file structure
   ```

3. **Cycle-Aware Configuration**:
   ```python
   # From create_CSV_pipeline7()
   for cycle in range(1, (expected_cycles + 1)):
       this_cycle = "Cycle%02d_" % cycle
       # Configure cycle-specific columns
   ```

### CellProfiler Pipeline Parameterization

CellProfiler pipelines are parameterized through CSV columns that control their behavior:

1. **Metadata Grouping**: Controls how images are processed together
   ```
   Group images by metadata?:Yes
   Select metadata tags for grouping:Plate
   ```

2. **Channel Selection**: Driven by metadata-derived CSV columns
   ```
   Select the input image:OrigDNA  # Comes from CSV FileName_OrigDNA column
   ```

3. **Output Naming**: Uses metadata variables from the CSV
   ```
   Enter single file name:\g<Plate>_IllumDNA  # \g<> syntax references metadata
   ```

This parameterization approach enables the same pipeline code to process different experimental designs based on the configuration-derived CSV input.

## Experiment Setup Guide

This section provides detailed instructions for setting up and running a new Pooled Cell Painting experiment using this workflow.

### Step 1: Prepare Your Image Data

1. **Organize Raw Images** in S3 following the expected structure:
   ```
   s3://your-bucket/
   └── project_name/
       └── batch_name/
           └── images/
               └── plate_name/
                   ├── 20X_CP/  (for cell painting)
                   └── 20X_BC_Cycle1/  (for barcoding)
   ```

2. **Verify Image Naming**:
   - Cell painting: `{well}_T{field}.tif` or similar pattern
   - Barcoding: `{well}_T{field}_Z{z}.tif` per cycle
   - Ensure names match expected patterns in the code

### Step 2: Configure Experiment Parameters (metadata.json)

Create a metadata.json file based on `configs/metadatatemplate.json`:

```json
{
  "painting_rows": "38",
  "painting_columns": "38",
  "painting_imperwell": "1364",
  "Channeldict": "{'20X_CP':{'DAPI':['DNA', 0], 'GFP':['Phalloidin',1], 'A594':['Mito',2], 'Cy5':['ER',3], '750':['WGA',4]}}",
  "barcoding_rows": "19",
  "barcoding_columns": "19",
  "barcoding_imperwell": "320",
  "barcoding_cycles": "12",
  "overlap_pct": "10",
  "fast_or_slow_mode": "slow",
  "one_or_many_files": "many",
  "round_or_square": "round",
  "quarter_if_round": "True",
  "tileperside": "10",
  "final_tile_size": "5500"
}
```

Adjust parameters for your specific experiment:
- Adjust grid parameters based on your acquisition setup
- Configure the channel dictionary to match your microscope configuration
- Set the appropriate mode based on your file organization
- Adjust stitching parameters based on your imaging setup

### Step 3: Configure Lambda Functions

For each Lambda function (PCP-1 through PCP-9):

1. **Update the config_dict**:
   ```python
   config_dict = {
       "APP_NAME": "MyProject_IllumPainting",  # Change to your project name
       "MACHINE_TYPE": ["c5.xlarge"],  # Adjust based on computational needs
       "MEMORY": "7500",              # Adjust based on image size
       "EXPECTED_NUMBER_FILES": "5",  # Set based on pipeline requirements
   }
   ```

2. **Deploy Lambda code** to AWS Lambda with proper execution role and permissions
   - Update APP_NAME to include your project identifier
   - Adjust machine type based on computational requirements
   - Set appropriate expected file counts for each pipeline

### Step 4: Configure AWS Infrastructure

1. **Update configFleet.json**:
   ```json
   {
     "IamFleetRole": "arn:aws:iam::YOUR_ACCOUNT:role/your-fleet-role",
     "LaunchSpecifications": [
       {
         "ImageId": "ami-YOUR_AMI_ID",
         "NetworkInterfaces": [
           {
             "SubnetId": "subnet-YOUR_SUBNET",
             "Groups": ["sg-YOUR_SECURITY_GROUP"]
           }
         ]
       }
     ]
   }
   ```

2. **Update configAWS.py**:
   ```python
   AWS_REGION = "us-east-1"  # Your preferred region
   AWS_BUCKET = "your-bucket"
   ECS_CLUSTER = "your-cluster"
   ```

3. **Upload Configuration Files** to S3:
   ```
   s3://your-bucket/project_name/batch_name/
   ├── metadata/
   │   └── batch_name/
   │       └── metadata.json
   └── lambda/
       └── batch_name/
           ├── configAWS.py
           └── configFleet.json
   ```

### Step 5: Upload CellProfiler Pipelines

Upload the appropriate pipeline files to trigger the workflow:

```
s3://your-bucket/project_name/batch_name/pipelines/
└── batch_name/
    └── 1_CP_Illum.cppipe  # Triggers the workflow
```

### Step 6: Monitor and Troubleshoot

1. **Monitor AWS CloudWatch Logs** for Lambda function execution
2. **Check S3 output folders** for results from each pipeline step
3. **Look for SQS messages** in case of failures
4. **Check Expected Output** in each step's S3 location before proceeding to the next step

### Common Issues and Solutions

| Issue            | Possible Cause      | Solution                                     |
| ---------------- | ------------------- | -------------------------------------------- |
| Missing files    | Incomplete upload   | Verify all raw images are uploaded           |
| Lambda timeout   | Large image set     | Increase Lambda timeout or optimize the code |
| Missing metadata | Incorrect S3 path   | Check metadata.json path in S3               |
| Pipeline error   | Mismatched channels | Verify Channeldict matches actual images     |