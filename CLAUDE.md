# Claude Guidelines for pooled-cell-painting-image-processing

## Project Overview
AWS-based serverless pipeline for high-throughput Cell Painting and barcoding image processing.

## Running the Code
- No formal testing framework
- QC scripts in `qc/` directory for quality control checks

## Code Style Guidelines

### Imports
1. Standard library imports first (os, sys, json)
2. Third-party libraries next (boto3, pandas)
3. Project modules last

### Naming Conventions
- Functions: snake_case (e.g., `parse_image_names`)
- Variables: snake_case (e.g., `image_dict`)
- Constants: UPPER_CASE (e.g., `AWS_REGION`)

### Error Handling
- Use try/except blocks with specific exception handling
- Print descriptive error messages
- Return None or appropriate values on error conditions

### Documentation
- Add inline comments for complex logic
- Explain AWS resource interactions and data transformations
- Document AWS configuration requirements

### Project Structure
- Lambda functions in separate directories by pipeline stage
- AWS Lamda functions in functions in `lambda/lambda_functions/`
- Configuration files in `configs/`
- CellProfiler pipelines in `pipelines/` directory