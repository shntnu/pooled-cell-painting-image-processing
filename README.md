# Pooled Cell Painting Image Processing

A cloud-based distributed image processing pipeline for high-throughput pooled Cell Painting experiments.

## Background

Pooled Cell Painting combines genetic perturbations (CRISPR) with high-content imaging to link genetic modifications to cellular phenotypes. This method requires:

1. **Cell Painting** - Fluorescent staining that highlights cellular components (nuclei, cytoplasm, etc.)
2. **Barcoding** - Multi-cycle fluorescent imaging that identifies genetic perturbations via DNA barcodes

Processing these images involves complex workflows including illumination correction, cell segmentation, barcode calling, image alignment, and feature extraction. This repository implements an automated, scalable workflow for processing large pooled Cell Painting datasets using AWS cloud services.

## System Architecture

The pipeline uses AWS serverless architecture to orchestrate image processing:

- **AWS Lambda** functions coordinate the workflow steps
- **AWS Batch** runs computationally intensive CellProfiler pipelines on scalable compute resources
- **Amazon S3** stores images and analysis results
- **Amazon SQS** manages job queues

The workflow is split into two parallel tracks (Cell Painting and Barcoding) followed by a combined analysis:

![Pooled Cell Painting Workflow Overview](docs/overview.png)

## Documentation

This repository contains several documentation files:

- **[Technical Implementation Overview](docs/Technical_Implementation_Overview.md)** - High-level system architecture and component interactions
- **[CellProfiler Pipeline Details](docs/CellProfiler_Pipeline_Details.md)** - Detailed explanation of each pipeline and its configuration
- **[PCP_Pooled_Cell_Painting_Guide](<docs/PCP Pooled Cell Painting Guide.md>)** - Step-by-step instructions for running experiments
- **[High_Throughput_Image_Flow_-_TI2_Pipeline_Details](<docs/High Throughput Image Flow - TI2 Pipeline Details.md>)** - Pipeline-specific information

For development guidelines, see [CLAUDE.md](CLAUDE.md).

## Pipeline Structure

The image processing workflow consists of nine sequential steps:

### Cell Painting Track
1. **PCP-1-CP-IllumCorr**: Calculate illumination correction for Cell Painting images
2. **PCP-2-CP-ApplyIllum**: Apply illumination correction to Cell Painting images
3. **PCP-3-CP-SegmentCheck**: Check cell segmentation on a subset of images
4. **PCP-4-CP-Stitching**: Stitch and crop Cell Painting images

### Barcoding Track
5. **PCP-5-BC-IllumCorr**: Calculate illumination correction for barcoding images
6. **PCP-6-BC-ApplyIllum**: Apply illumination correction and align barcoding images
7. **PCP-7-BC-Preprocess**: Preprocess barcoding images, identify foci, and call barcodes
8. **PCP-8-BC-Stitching**: Stitch and crop barcoding images

### Analysis
9. **PCP-9-Analysis**: Combine Cell Painting and barcoding data for downstream analysis

## Getting Started

For detailed setup and execution instructions, refer to the [PCP Pooled Cell Painting Guide](docs/PCP%20Pooled%20Cell%20Painting%20Guide.md).

Key steps include:
1. Preparing experimental metadata
2. Configuring AWS resources
3. Uploading images to S3
4. Executing the Lambda pipeline
5. Monitoring job progress
6. Analyzing results

## Repository Structure

- **lambda/**: AWS Lambda functions for workflow orchestration
  - Separate directories for each pipeline stage
  - Shared utility functions in lambda_functions/
- **pipelines/**: CellProfiler pipelines for image analysis
- **configs/**: Configuration templates
- **FIJI/**: FIJI scripts for stitching
- **notebooks/**: Jupyter notebooks for data analysis
- **docs/**: Documentation
- **qc/**: Quality control scripts

## Requirements

- AWS account with access to Lambda, Batch, S3, and SQS
- CellProfiler 4.x
- Python 3.6+
- Boto3 for AWS interactions