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

### 4. Configuration

Two primary configuration systems control the workflow:

- **metadata.json**: Experiment-specific settings including plate layouts, channels, cycle counts, and acquisition parameters
- **configFleet.json**: AWS resource configuration controlling instance types, memory allocation, and job execution parameters

### 5. QC and Analysis 

- **notebooks/**: Jupyter notebooks for troubleshooting, visualization, and analysis
- **qc/QC.py**: Quality control script analyzing key metrics like barcode quality, alignment quality, and cell segmentation

## Workflow Implementation

Each Lambda function follows a similar pattern:

1. **Parse Metadata**: Read experiment configuration from S3
2. **Identify Images**: List S3 objects matching specific patterns and filter for completeness
3. **Generate CSVs**: Create input files describing image paths and metadata for CellProfiler
4. **Configure Jobs**: Set up AWS Batch jobs with appropriate resource allocations
5. **Run Cluster**: Launch EC2 instances to execute CellProfiler pipelines
6. **Monitor Execution**: Track job completion and handle failures
7. **Trigger Next Step**: When all jobs complete, initiate the next pipeline stage

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