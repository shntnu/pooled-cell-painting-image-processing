# Pooled Cell Painting Image Processing: Technical Implementation Overview

This document provides a technical overview of the pooled-cell-painting-image-processing codebase, explaining how the various components work together to process high-throughput microscopy data in the cloud.

## System Architecture

The system implements a serverless, distributed image processing pipeline using AWS services:

1. **AWS Lambda** - Orchestrates the workflow, handling metadata management, job creation, and pipeline transitions
2. **AWS Batch** - Runs computationally intensive CellProfiler pipelines on scalable compute resources
3. **Amazon S3** - Stores raw and processed images, illumination correction files, and metadata
4. **Amazon SQS** - Manages job queues and coordinates worker instances
5. **Amazon EC2** - Provides elastic computing resources for image processing

## Core Components

### 1. Lambda Functions

The backbone of the system is a series of Lambda functions that implement a sequential workflow:

#### Cell Painting Image Processing
- **PCP-1-CP-IllumCorr**: Calculates illumination correction functions for cell painting images
- **PCP-2-CP-ApplyIllum**: Applies illumination correction to raw cell painting images
- **PCP-3-CP-SegmentCheck**: Validates segmentation quality through threshold calculation
- **PCP-4-CP-Stitching**: Stitches field-of-view images into whole-well montages

#### Barcoding Image Processing
- **PCP-5-BC-IllumCorr**: Calculates illumination correction for barcoding images
- **PCP-6-BC-ApplyIllum**: Applies illumination correction to barcoding images and aligns channels
- **PCP-7-BC-Preprocess**: Identifies nuclei, cells, and barcoding foci; calls barcodes
- **PCP-8-BC-Stitching**: Stitches aligned barcoding images
- **PCP-8Y/8Z**: Validates barcoding image alignment and performs additional stitching

#### Analysis
- **PCP-9-Analysis**: Integrates cell painting and barcoding data for downstream analysis

### 2. Shared Utility Functions

The `lambda/lambda_functions/` directory contains shared utility modules:

- **helpful_functions.py**: Common operations for image list parsing, AWS interactions, and metadata handling
- **create_CSVs.py**: Creates pipeline-specific CSV files that drive CellProfiler processing
- **run_DCP.py**: Handles AWS Batch job configuration and execution
- **create_batch_jobs.py**: Configures distributed compute jobs for each pipeline step
- **boto3_setup.py**: Manages AWS resources and API interactions

### 3. CellProfiler Pipelines

The `pipelines/12cycles/` directory contains the CellProfiler analysis pipelines that perform the actual image processing:

- Illumination correction calculation and application
- Cell and nuclear segmentation
- Image alignment between fluorescence channels and cycles
- Barcode calling
- Feature extraction
- Quality control

### 4. Multi-Layered Configuration

The system employs a three-tiered configuration approach where each layer controls a different aspect of the workflow:

#### Experiment Configuration Layer
- **metadata.json**: Controls experimental parameters and image processing logic:
  - **Image Grid Parameters**: `painting_rows/columns/imperwell` and `barcoding_rows/columns/imperwell` define the physical layout of images
  - **Channel-to-Stain Mapping**: The complex `Channeldict` object maps microscope channels to biological stains across imaging rounds
  - **Pipeline Flow Control**: `one_or_many_files`, `fast_or_slow_mode`, and `barcoding_cycles` control how pipelines process data
  - **Stitching Parameters**: `overlap_pct`, `stitchorder`, `tileperside`, and others control image stitching behavior
  - **Troubleshooting Parameters**: Offset parameters allow manual adjustment of stitching alignment

#### Computing Resource Configuration Layer
- **Lambda `config_dict`**: Each Lambda function contains a Python dictionary that controls:
  - **AWS Resource Allocation**: Machine type, memory, EBS volume size, cores
  - **Job Configuration**: Tasks per machine, timeout settings, visibility
  - **Quality Control**: Expected file counts, minimum file sizes
  - **Application Identity**: APP_NAME that identifies the experiment in logs and AWS resources

#### Infrastructure Configuration Layer
- **configFleet.json**: AWS Spot Fleet configuration controlling instance types, networking, and IAM roles
- **configAWS.py**: General AWS settings such as region, bucket names, and SQS queue identifiers

### 5. QC and Analysis 

- **notebooks/**: Jupyter notebooks for troubleshooting, visualization, and analysis
- **qc/QC.py**: Quality control script analyzing key metrics like barcode quality, alignment quality, and cell segmentation

## Workflow Implementation

Each Lambda function follows a similar pattern that integrates the three configuration layers:

1. **Parse Event**: Extract bucket and key information from the S3 trigger event
2. **Load Configuration**:
   - Read experiment configuration from S3's metadata.json file
   - Use the internal Lambda `config_dict` for AWS resource settings
   - Download AWS infrastructure configuration files when needed
3. **Configure Pipeline Behavior**: Use metadata parameters to determine:
   - Which pipeline file to run (e.g., standard vs. SABER for multi-round experiments)
   - How many images to expect per well
   - Which channels to process
   - How to organize the data (one file vs. many files)
4. **Identify Images**: List S3 objects matching specific patterns and filter for completeness
5. **Generate CSVs**: Create CellProfiler LoadData CSV files containing:
   - File paths derived from metadata parameters
   - Channel-to-stain mapping from the `Channeldict`
   - Metadata columns for grouping and organization
   - Frame indices based on acquisition configuration
6. **Configure Jobs**: Set up AWS Batch jobs using settings from all three configuration layers:
   - Pipeline selection from metadata.json
   - AWS resource allocation from Lambda `config_dict`
   - Instance fleet configuration from configFleet.json
7. **Run Cluster**: Launch EC2 instances to execute CellProfiler pipelines
8. **Monitor Execution**: Track job completion and handle failures using SQS queues and monitoring thresholds from `config_dict`
9. **Trigger Next Step**: When all jobs complete, initiate the next pipeline stage

This multi-layered configuration approach allows the system to adapt to different experimental designs (via metadata.json), resource requirements (via Lambda `config_dict`), and infrastructure changes (via AWS config files) independently.

## Data Flow

1. Raw microscopy images are uploaded to S3 in a specific organization
2. Lambda functions process these images through sequential stages:
   - Illumination correction to handle optical artifacts
   - Image alignment to register multi-channel data
   - Cell/nuclei segmentation to identify cellular compartments
   - Foci identification to locate barcode signals
   - Barcode calling to translate fluorescent signals to sequence codes
   - Stitching and cropping to create whole-well images
3. Processed image data and feature measurements are saved to S3
4. CSV files with extracted measurements enable downstream analysis

## Technical Challenges Addressed

1. **Scale**: Handles thousands of high-resolution images through distributed processing
2. **Alignment**: Registers images across multiple fluorescence channels and acquisition cycles
3. **Signal Quality**: Corrects for illumination artifacts and poor signal-to-noise
4. **Barcode Calling**: Implements sophisticated algorithms to call genetic barcodes from fluorescent signals
5. **Stitching**: Creates seamless montages from tiled acquisitions

## System Evolution

The codebase shows evidence of evolution:
- Support for different imaging modalities (one vs. many files per well)
- Multiple acquisition speeds (fast vs. slow acquisition)
- Variable cycle counts (8, 9, 12) for different experimental designs
- Specialized troubleshooting pipelines (PCP-7A-BC-PreprocessTroubleshoot)

This architecture enables high-throughput processing of complex microscopy datasets in a scalable, cost-effective manner leveraging cloud resources.