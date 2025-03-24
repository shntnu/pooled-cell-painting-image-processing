# Pooled Cell Painting Image Processing: Technical Implementation Overview

This document provides a high-level technical overview of the system architecture, components, and data flow for processing pooled cell painting microscopy data in the cloud. It focuses on architectural aspects and component relationships rather than detailed implementation steps.

> **Note:** For detailed pipeline implementations, configuration parameters, and experiment setup instructions, see the companion document [CellProfiler_Pipeline_Details.md](./CellProfiler_Pipeline_Details.md).

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

### 4. Multi-Layered Configuration Architecture

The system employs a three-tiered configuration architecture that separates concerns and enables flexibility:

#### Configuration Layer Relationships

The three configuration layers work together to provide a complete system definition:

- **Experiment Configuration** (metadata.json): Defines **WHAT** data is processed and **HOW** it's processed
- **Computing Resource Configuration** (Lambda config_dict): Controls **HOW MUCH** computing power is allocated and **WHEN** jobs complete
- **Infrastructure Configuration** (AWS config files): Determines **WHERE** in AWS the processing happens

This separation of concerns allows for independent modification of experimental parameters, resource allocation, and AWS infrastructure, enabling system evolution without wholesale redesign.

> **Note:** For detailed configuration parameters, specific settings, and setup instructions for each layer, see the [Configuration sections in CellProfiler_Pipeline_Details.md](./CellProfiler_Pipeline_Details.md#multi-layered-configuration-system).

### 5. QC and Analysis 

- **notebooks/**: Jupyter notebooks for troubleshooting, visualization, and analysis
- **qc/QC.py**: Quality control script analyzing key metrics like barcode quality, alignment quality, and cell segmentation

## Workflow Architecture

The system implements an event-driven serverless architecture that orchestrates image processing across multiple AWS services. Each Lambda function in the pipeline acts as both a trigger handler and an orchestrator for the next stage.

### Event Flow and Orchestration

1. **S3 Event Trigger**: Object creation in S3 triggers the appropriate Lambda function
2. **Configuration Integration**: Lambda loads and integrates all configuration layers
3. **Pipeline Orchestration**: Lambda determines which CellProfiler pipeline to run
4. **Resource Orchestration**: Lambda configures and launches AWS Batch jobs
5. **Job Monitoring**: Lambda sets up monitoring of job completion via SQS
6. **Pipeline Transition**: Successful job completion triggers the next Lambda function

This architecture enables:
- **Scalability**: Process thousands of images in parallel
- **Resilience**: Each pipeline stage operates independently
- **Cost Efficiency**: Computing resources are provisioned only when needed

### Pipeline Progression Logic

The system employs a sequential processing model with built-in dependency management:

```
S3 Event → Lambda → Batch Jobs → S3 Output → Next Lambda → ...
```

Each Lambda validates the outputs of the previous stage before launching the next stage, ensuring data integrity throughout the workflow.

> **Note:** For detailed implementation of pipeline-specific workflows, CSV generation, and configuration usage, see the [Pipeline Workflow section in CellProfiler_Pipeline_Details.md](./CellProfiler_Pipeline_Details.md#how-the-configuration-layers-drive-the-pipeline-workflow).

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
