# OPS pipeline inputs-outputs

Note on batching: The current batches are not optimal. More expermentation is required. Make it configurable.

Note on output paths: Can change. Ongoing [github discussion.](https://github.com/broadinstitute/pooled-cell-painting-image-processing/issues/11)
## Cell Painting Images
### Illum correction calculation

- inputs:
    - The raw cell painting images
    - CellProfiler pipeline
    - LoadData CSV
- Notes:
    - Batched at plate level
    - Metadata grouping information have to match the cp run command on the CLI
- outputs:
    - .npy files: one per channel: currently saved at `illum/`
- checks:
    - .npy files shlould have some number of pixels that are of value 1.
    - Throw a warning flag if the largest value is greater than 4
    - A manual(optional) check: generate a png/pdf files with .npy files for visual inspection by a human

### Illum correction application

- inputs:
    - The raw cell painting images
    - The .npy files from `Illum correction calculation` step 
    - CellProfiler pipeline
    - LoadData CSV
- Notes:
    - Batched at well level
    - Metadata grouping information have to match the cp run command on the CLI
    
- outputs:
    - New corrected images: currently saved at `images_corrected/painting`
    - Image.csv for every well containing `image measurements form CP - standard in CP for whole image measurement`: currently saved at `images_corrected/[plate-well]/PaintingIlluminationApplication_Image.csv`
    
- checks: 
    - Read Image.csv files and report 10th and 90th percentile. This is not a boolean check or a warning
    - Code link: https://github.com/broadinstitute/pooled-cell-painting-image-processing/blob/cb7779efe78dfb74b724b0149f510828565699d5/lambda/PCP-3-CP-SegmentCheck/lambda_function.py#L132-L149



### Segmentation check

- inputs:
    - The corrected cell painting images
    - CellProfiler pipeline
    - LoadData CSV
    
- Notes:
    - Batched at well level
    - Metadata grouping information have to match the cp run command on the CLI

- outputs:
    - Psuedo coloured segmented images: for visual inspection by biologist: currently saved `images_segmented`

- checks:
    - Take the individual segmented images, stitch them together into a rectangle, scale them down. Generate a report that can be manually inspected. This is boolean step to make decision to continue execution of the pipeline.
    - Code link: https://github.com/broadinstitute/ImagingPlatformHelpfulScripts/blob/main/make_fiji_montages_std.py

### Stitching and cropping

- inputs:
    - The corrected cell painting images
    - Fiji script
    
- Notes:
    - Batched at well level
    
- outputs:
    - Images corrected cropped: currently saved at `images_corrected_cropped` - These are the images used by the cellprofiler for generating measurements
    - Images corrected stiched 10x downscaled
        
- checks:
    - Manual inspection: Generate a report with downscale images for visual inspection


## Barcoding Images 
### Illum correction calculation
- inputs:
    - The raw barocding images
    - CellProfiler pipeline
    - LoadData CSV
- Notes:
    - Batched at plate and cycle level
    - Metadata grouping information have to match the cp run command on the CLI
- outputs:
    - .npy files: one per plate, channel and cycle: currently saved at `illum/`
- checks:
    - .npy files shlould have some number of pixels that are of value 1.
    - Throw a warning flag if the largest value is greater than 4
    - A manual(optional) check: generate a png/pdf files with .npy files for visual inspection by a human

### Illum correction application and alignment

- inputs:
    - The raw barcoding images
    - The .npy files from `Illum correction calculation` step 
    - CellProfiler pipeline
    - LoadData CSV
- Notes:
    - Batched at plate, well and site level
    - Metadata grouping information have to match the cp run command on the CLI
    
- outputs:
    - New corrected images: currently saved at `images_aligned/barcoding`
    - Image.csv for every well containing `image measurements form CP - standard in CP for whole image measurement`: currently saved at `images_aligned/[plate-well]/BarcodingIlluminationApplication_Image.csv`
    
- checks: 
    - Use Image.csv to throw warning for `alignment metric`
    - Code link: look at notebook on slack: 6_barcode_align

### Preprocessing

Major things happening here are: Foci identification, image masking, colour compensation and barcode calling

- inputs:
    - The aligned barcoding images saved at `images_aligned`
    - Barcodes.csv saved at `workspace/metadata`
    - CellProfiler pipeline
    - LoadData CSV
- Notes:
    - Batched at plate, well and site level
    - Metadata grouping information have to match the cp run command on the CLI
    - This step is iterated the most

- outputs:
    - corrected_images: masked_images, channel compensated
- checks:
    - Read `Foci.csv` and look at barcode quality metrics
    - Code link (outdated, Erin will update): see on slack
    - There are multiple QC metrics in the notebook, Flag/bool (configurable) on metric threshold

### Stitching and cropping

- inputs:
    - The corrected barcoding images
    - Fiji script
    
- Notes:
    - Batched at well level
    
- outputs:
    - Images corrected cropped: currently saved at `images_corrected_cropped` - These are the images used by the cellprofiler for generating measurements
    - Images corrected stiched 10x downscaled
        
- checks:
    - Manual inspection: Generate a report with downscale images for visual inspection


## Barcoding and Cell Painting Images (Analysis)

Don't break it down into multiple steps

- inputs:
    - images_corrected_cropped from both painting and barcoding 
    - Barcodes.csv
    - Cellprofiler pipeline
    - LoadData.csv
    
- Notes:
    - Batched at site level
        
- outputs:
    - Measurements
        - Foci.csv: contains strings in some columns
        - Barcode_foci.csv
        - Cell.csv
        - Image.csv
        - Experiment.csv
        - confluent_regions.csv
    - overlay_images
    - spot_overlay_images
    - segmentation masks (tiffs)
        - cell
        - cytoplasm
        - nuclei
        
- checks:
    - We might not want to add checks here for now


---

Notes: Look at periscope data, we want to restructure folder structure.
