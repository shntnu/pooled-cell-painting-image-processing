# Pooled Cell Painting Image Processing

A cloud-based pipeline for high-throughput pooled Cell Painting experiments using AWS services.

![Pooled Cell Painting Workflow Overview](docs/overview.png)

## Overview

Pooled Cell Painting combines genetic perturbations with high-content imaging to measure cellular phenotypes at scale. This repository implements a serverless AWS architecture for processing these complex datasets, handling:

- Illumination correction
- Cell segmentation
- Barcode calling
- Image alignment
- Feature extraction

## Documentation

- **[Technical Implementation Overview](docs/Technical_Implementation_Overview.md)** - System architecture
- **[CellProfiler Pipeline Details](docs/CellProfiler_Pipeline_Details.md)** - Pipeline and Lambda implementation
- **[User Guide](docs/supporting_files/PCP%20Pooled%20Cell%20Painting%20Guide.md)** - Setup and execution instructions

## Pipeline Structure

The workflow consists of two parallel tracks with nine sequential Lambda functions:

### Cell Painting Track
1. **PCP-1**: Illumination correction calculation
2. **PCP-2**: Apply illumination correction
3. **PCP-3**: Segmentation validation
4. **PCP-4**: Image stitching

### Barcoding Track
5. **PCP-5**: Illumination correction calculation
6. **PCP-6**: Apply correction and align channels
7. **PCP-7**: Preprocessing and barcode calling
8. **PCP-8**: Image stitching

### Analysis
9. **PCP-9**: Data integration for downstream analysis

## Repository Contents

- **lambda/**: AWS Lambda functions
- **pipelines/**: CellProfiler pipelines
- **configs/**: Configuration templates
- **notebooks/**: Analysis notebooks
- **docs/**: Documentation
- **qc/**: Quality control

## Requirements

- AWS (Lambda, Batch, S3, SQS)
- CellProfiler 4.x
- Python 3.6+
- Boto3