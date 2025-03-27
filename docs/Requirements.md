# Pooled Cell Painting Image Processing System Requirements

Key: 
- starrynight roadmap (per Shantanu): 🔵 planned 🟡 in progress 🔴 not planned
- priority (per Shantanu): ⭐ low ⭐⭐ medium ⭐⭐⭐ high

## 1. System Overview

This document outlines requirements for a next-generation system for processing, analyzing, and managing high-throughput microscopy data from image-based profiling experiments, in particular, pooled optical screens. The system will orchestrate complex image processing workflows, manage computational resources efficiently, and provide mechanisms for both automated and manual intervention during the processing pipeline.

## 2. Core Requirements

### 2.1 Image Processing Capabilities

- 🟡 ⭐⭐⭐: **Must support automated execution of CellProfiler pipelines** for all stages of image processing:
  - Illumination correction calculation and application
  - Cell segmentation and validation
  - Image stitching and cropping
  - Channel alignment across imaging cycles
  - Barcode identification and calling
  - Feature extraction and analysis

- 🟡 ⭐⭐⭐: **Must process both Cell Painting (CP) and Barcoding (BC) image tracks** in parallel, with integration points for combined analysis.

- 🟡 ⭐⭐⭐: **Must allow integration of non-CellProfiler image processing tools** such as FIJI/ImageJ and custom analysis scripts.

### 2.2 Experimental Configuration

Note: This section has been intentionally over-specified to capture everything but should be pruned as needed

- 🔵 ⭐⭐⭐: **Must support all image grid configuration parameters**:
  - `painting_rows`, `painting_columns`: For square acquisition patterns
  - `painting_imperwell`: For circular acquisition patterns (overrides rows/columns)
  - `barcoding_rows`, `barcoding_columns`: For square acquisition patterns
  - `barcoding_imperwell`: For circular acquisition patterns (overrides rows/columns)

- 🔵 ⭐⭐⭐: **Must support complex channel dictionary configuration**:
  - Mapping microscope channel names to biological stains and frame indices
  - Multi-round experiment support (e.g., SABER) with round identifiers
  - Single-round experiment support with simpler configuration

- 🔵 ⭐⭐⭐: **Must support processing configuration settings**:
  - `one_or_many_files`: File organization strategy per well
  - `fast_or_slow_mode`: CSV generation and processing strategy
  - `barcoding_cycles`: Number of barcoding cycles to process
  - `range_skip`: Sampling frequency for quality control

- 🔵 ⭐⭐⭐: **Must support detailed stitching configuration**:
  - `overlap_pct`: Image overlap percentage between fields
  - `stitchorder`: Tile arrangement strategy based on acquisition pattern
  - `tileperside`: Number of tiles along each side of the stitched grid
  - `final_tile_size`: Pixel dimensions of output tiles
  - `round_or_square`: Well shape for cropping calculations
  - `quarter_if_round`: Division strategy for round wells
  - Offset parameters for alignment troubleshooting
  - `compress`: Output file compression settings

### 2.3 Workflow Control

- 🟡 ⭐⭐: **Must support fully automated end-to-end processing** with configurable pipeline sequences:
  - While current optical pooled screening experiments require significant human judgment at multiple stages, the system should be designed to enable full automation as a long-term goal
  - Must support both fully automated workflows for mature processing paths and semi-automated workflows requiring human intervention
  - Must allow gradual transition from manual to automated processing as confidence in automated methods increases

- 🟡 ⭐⭐⭐: **Must enable manual intervention at any stage** with the ability to:
  - Pause/resume pipeline execution
  - Inspect intermediate results before proceeding
  - Modify parameters between stages
  - Re-run specific stages with adjusted settings
  - Launch inspection notebooks

- 🟡 ⭐⭐: **Must enable resuming from interruptions**.

### 2.4 Compute Resource Management

- 🔵 ⭐⭐: **Must efficiently manage computational resources** appropriate to each processing stage:
  - Scale resources based on workload
  - Optimize resource allocation for memory-intensive vs. CPU-intensive tasks
  - Support parallel processing of independent tasks

- 🔵 ⭐⭐: **Must work across diverse compute environments**:
  - Cloud platforms (⭐⭐⭐: AWS, ⭐: Azure, ⭐: GCP)
  - ⭐: On-premises high-performance computing clusters
  - ⭐⭐⭐: Local workstations (with appropriate scaling)

### 2.5 Data Management

- 🟡 ⭐⭐⭐: **Must organize input and output data** in a consistent, browsable structure:
  - Must maintain compatibility with existing input data structures
  - Must produce outputs that match current output structures (unless explicitly modified by design)
  - Must provide clear documentation for any structural changes

- 🔵 ⭐⭐: **Must track data provenance** including:
  - Processing history for each image
  - Parameters used at each stage
  - Software versions and dependencies

- 🔵 ⭐⭐⭐: **Must handle large data volumes** (terabytes) efficiently with appropriate streaming and caching strategies.

- 🟡 ⭐⭐⭐: **Must implement flexible path parsing and data organization**:
  - Standardized but configurable system for extracting metadata from file paths
  - Support for mapping from various microscope vendor file organizations to internal structure
  - Ability to adapt to different naming conventions without code changes

### 2.6 User Interaction

- 🟡 ⭐⭐⭐: **Must provide multiple interaction mechanisms**:
  - Command-line interface for scripting and automation
  - Web-based or desktop GUI for visualization and control
  - Programmatic API for integration with other systems

- 🔵 ⭐⭐⭐: **Must support both expert and non-expert users** with appropriate levels of abstraction and guidance.

- 🔵 ⭐⭐⭐: **Must integrate result visualization and quality control**:
  - Built-in visualization tools for reviewing processing results, including cell segmentation, barcode calling, and feature data
  - Integrated quality control metrics with contextual interpretations

- 🔵 ⭐⭐⭐: **Must provide interactive inspection tools**:
  - Support for Jupyter notebooks (or similar) as a first-class inspection interface
  - Widgets for visualizing image 

## 3. Technical Requirements

### 3.1 System Architecture

- 🔵 ⭐⭐: **Must implement a modular architecture** with:
  - ⭐⭐⭐: Clear separation between workflow orchestration, execution, and configuration
  - ⭐⭐⭐: Well-defined interfaces between components
  - ⭐: Plugin system for extensibility

- 🔵 ⭐⭐⭐: **Must support distributed processing** across multiple compute nodes.

- 🔵 ⭐⭐⭐: **Must be resilient to failures** with appropriate error handling and recovery mechanisms.

### 3.2 Configuration System

- 🔵 ⭐⭐⭐: **Must implement a multi-layered configuration approach** separating:
  - Experimental parameters (what data to process and how)
  - Computational resource parameters (how much compute power to allocate)
  - Infrastructure parameters (where the processing will occur)

- 🔵 ⭐⭐: **Must validate configuration** against schema to catch errors early.

- 🔴 ⭐: **Must allow configuration overrides** at different levels (system, experiment, batch, plate).

### 3.3 Cross-Platform Support

- 🔵 ⭐: **Must run on ⭐⭐⭐Linux, ⭐⭐MacOS, and ⭐Windows** operating systems.

- 🔵 ⭐: **Must provide consistent interfaces** across platforms.

- 🔵 ⭐: **Must accommodate platform-specific resources** (GPU acceleration, memory limits).

### 3.4 Extensibility

- 🔵 ⭐⭐⭐: **Must allow addition of new processing tools** beyond CellProfiler.

- 🔵 ⭐: **Must support custom analysis modules** for specialized experiments.

- 🔴 ⭐: **Must enable integration with external systems** via APIs and data exchange formats.

### 3.5 Documentation and Support

- 🟡 ⭐⭐⭐: **Must provide comprehensive user documentation** including installation and setup guides, configuration reference, workflow tutorials, and troubleshooting information.

- 🟡 ⭐⭐⭐: **Must include developer documentation** covering architecture overview, API references, extension guides, development setup

## 4. Implementation Recommendations

Unlike the previous sections which define WHAT the system must do (requirements), this section provides guidance on HOW these requirements might be implemented. These recommendations are not mandatory specifications but suggested approaches based on best practices and domain expertise.

<details>
  
### 4.1 System Components

- **Workflow Engine**: Orchestrates pipeline steps, manages dependencies, and tracks state.
- **Resource Manager**: Allocates and monitors compute resources across infrastructure.
- **Configuration Manager**: Handles loading, validation, and distribution of parameters.
- **Execution Engine**: Runs image processing tools with appropriate parameters.
- **Data Manager**: Organizes and tracks files throughout the processing pipeline.
- **User Interfaces**: CLI, GUI, and API implementations for system interaction.

### 4.2 Key Technical Approaches

- **Container-Based Deployment**: Package tools and dependencies in containers for consistent execution.
- **State Management**: Persist workflow state to enable resumption after interruptions.
- **Event-Driven Architecture**: Use events to coordinate pipeline progression and notifications.
- **Distributed Computing**: Implement task distribution for parallel processing.
- **Pluggable Storage**: Support multiple storage backends (local, network, cloud).
- **Leverage Existing Tools**: Prefer established, maintained tools over custom solutions whenever possible, even if they have limitations, to minimize maintenance burden.

### 4.3 User Experience Considerations

- **Progress Visualization**: Provide clear indication of pipeline progress and estimated completion.
- **Result Browsing**: Enable navigation and inspection of intermediate and final results.
- **Error Handling**: Present clear error messages with actionable remediation steps.
- **Parameter Exploration**: Support interactive adjustment of processing parameters.
- **Notebook Integration**: 
  - Include example notebooks for common inspection tasks

</details>

## 5. Additional Information Needed for Implementation

The following information would greatly enhance implementation efforts and should be provided by domain experts:

<details>

### 5.1 Prioritization and Constraints

- **Feature Prioritization**: Which requirements are absolutely critical vs. nice-to-have?
- **Performance Requirements**: 
  - What are acceptable processing times for each pipeline step?
  - What dataset sizes must be supported initially vs. eventually?
  - Are there specific memory constraints for typical workstations?
- **Scalability Targets**: Maximum number of images, wells, or plates to process in a single experiment

### 5.2 User Workflows and Context

- **Typical Workflows**: Step-by-step examples of how scientists currently execute experiments
- **Decision Points**: When and why do researchers need to evaluate intermediate results?
- **Common Bottlenecks**: Current pain points and processing areas that require most attention
- **Error Handling Preferences**: How should the system manage and communicate different error types?

### 5.3 Validation and Testing

- **Representative Test Data**: Sample datasets of varying complexity for development and testing
- **Quality Assurance**: 
  - Examples of successful vs. problematic outputs at each stage
  - Specific metrics for evaluating processing quality
  - Tolerance limits for various processing artifacts
- **Backward Compatibility**: Test cases that must pass for compatibility with existing data

### 5.4 Integration Requirements

- **Third-Party Tools**: Complete list of external tools that must be supported
- **API Requirements**: Specifications for APIs to interact with other research systems if any
- **Data Exchange**: Standards or formats required for interoperability with other software
- **Security Considerations**: Requirements for data protection, user authentication, and access control

Providing this information will help ensure the system not only meets the technical requirements but also delivers maximum value to researchers in their specific scientific contexts.

</details>

