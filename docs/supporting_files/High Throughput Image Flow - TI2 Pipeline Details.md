# High Throughput Image Flow \- TI2 Pipeline Details

Known problems in each acquisition  
Potential problems in an acquisition  
Possible additional quality control step

| Pipeline 1 \- Cell Painting Illumination Correction Calculation |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: raw Cell Painting images (images/20X\_CP\_**BATCH**) |  |  |  |
| Output folder: illum/cellpainting |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Calculate per-plate illumination correction for each channel | Per-plate illumination correction images for each channel | **PLATE**\_Illum**CHANNEL**.npy | (passed to Pipeline 2\) |

| Pipeline 2 \- Cell Painting Illumination Correction Application |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: raw Cell Painting images (images/20X\_CP\_**BATCH**), Cell Painting illumination correction images (illum/cellpainting) |  |  |  |
| Output folder: images\_corrected/cellpainting |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Apply per-plate illumination correction to each image | Illumination corrected images | Well**\#**\_...\_Site\_**\#**\_CorrCh**\#**.tiff | Vignetting, optical path aberrations |
| Identify and mask out confluent regions |  |  | Overly-confluent regions |
| Identify nuclei and cells | Auto-calculated segmentation thresholds | Cells.csv | (passed to Pipeline 3\) |

| Pipeline 3 \- Cell Painting Segmentation Check |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: whole-plate corrected Cell Painting images (images\_corrected/cellpainting) |  |  |  |
| Output Folder: segment\_check |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Identify and mask out confluent regions |  |  | Overly confluent regions |
| Identify nuclei and cells using max/min segmentation thresholds determined from pipeline 2 output. | Segmentation thresholds passed to final analysis pipeline | Cells.csv | Imaging differences across well affecting segmentation |
| Create color merged image showing identified objects | Segmented images for manual confirmation of appropriate segmentation | Well**\#**\_...\_Site\_**\#**\_CorrCh**\#**\_SegmentCheck.tiff | Used for manual confirmation of correct segmentation parameters. |

| Pipeline 4 \- Cell Painting Stitching and Cropping |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: whole-plate corrected Cell Painting images (images\_corrected/cellpainting) |  |  |  |
| Output Folders: images\_corrected\_stitched for whole-well stitched image images\_corrected\_cropped for cropped tiles from whole-well stitched image images\_corrected\_stitched\_10X for small version of whole-well stitched image |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Stitch all images into single image | Whole-well stitched image | **BATCH\_WELL**/Stitched....CorrCh**\#**.tiff | Loss of information from cells at the edge of an image. |
| Crop the whole-well image into tiles | Final images for analysis | **BATCH\_WELL/CHANNEL**/CorrCh**\#**\_Site\_**\#**.tiff | Computability of large images |
| Downsize whole-well image | 10x smaller whole-well stitched image | **BATCH\_WELL**/Stitched....CorrCh**\#**.tiff | Used for manual confirmation of correct stitching parameters.  |

| Pipeline 5 \- Barcoding Illumination Correction Calculation |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: raw Barcoding images from images |  |  |  |
| Output folder: illum/barcoding |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Calculate per-plate illumination correction for each channel | Per-plate illumination correction images for each channel | **PLATE**\_Illum**CHANNEL**.npy | (passed to Pipeline 6\) |

| Pipeline 6 \- Barcoding Illumination Correction Application, Alignment |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: raw Barcoding images from images, Barcoding illumination correction images from illum/barcoding |  |  |  |
| Output folder: images\_aligned/barcoding |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Measure image quality | Image based intensity measures | Image.csv | Allows detection of poor quality barcoding images. Quality cutoffs not yet established |
| Apply per-plate illumination correction to each image |  |  | Vignetting, optical path aberrations |
| Align A, C, G, T images from each cycle to their DAPI image |  |  | Per-channel mis-alignments caused by fast-mode acquisition |
| Align cycle 2 through n DAPI images to cycle 1 DAPI, moving the respective A, C, G, T the same amount | Illumination corrected and aligned images | Plate\_**PLATE**\_Well\_**\#**\_Site\_**\#**\_Cycle**\#**\_**CHANNEL**.tiff | Mis-alignments caused by multi-session acquisition |

| Pipeline 7 \- Barcoding Preprocessing |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: aligned Barcoding images |  |  |  |
| Output folder: images\_corrected/barcoding |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Per-image illumination correction (grouped by cycle) |  |  | High background levels obscuring dim signal |
| Identify Nuclei, Cells, and Foci | Objects |  |  |
| Measure foci intensity | Foci intensity before any rescaling or compensation | Foci.csv | Allows for Bayesian spot calling and quality control of rescale methods. |
| Histogram matching within foci (optional) |  |  | Low intensity/dynamic range of a single channel. Cutoffs triggering use not yet set. |
| Compensate colors within foci |  |  | Bleedthrough between barcoding channels |
| Rescaling within foci (optional) |  |  | Low intensity/dynamic range of a single channel. Cutoffs triggering use not yet set. |
| Measure foci intensity and call barcodes | Barcode calls and quality metrics such as % perfect. | Foci.csv |  |
| Save images with corrected foci | Illumination corrected images with rescaled and compensated foci. | Plate\_**PLATE**\_Well\_**\#**\_Site\_**\#**\_Cycle**\#**\_**CHANNEL**.tiff |  |
| Create color merged image showing identified objects | Segmented images for manual confirmation of appropriate segmentation | Plate\_**PLATE**\_Well\_**\#**\_Site\_**\#\_**Max\_Overlay.tiff | Used for manual confirmation of correct segmentation parameters |

| Pipeline 8 \- Barcoding Stitching and Cropping |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: whole-plate corrected Barcoding images (images\_corrected/barcoding) |  |  |  |
| Output Folders: images\_corrected\_stitched for whole-well stitched image images\_corrected\_cropped for cropped tiles from whole-well stitched image images\_corrected\_stitched\_10X for small version of whole-well stitched image |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Stitch all images into single image | Whole-well stitched image | **BATCH\_WELL**/Stitched....CorrCh**\#**.tiff | Loss of information from cells at the edge of a well. |
| Crop the whole-well image into tiles | Final images for analysis | **BATCH\_WELL/CHANNEL**/CorrCh**\#**\_Site\_**\#**.tiff | Computability of large images |
| Downsize whole-well image | 10x smaller whole-well stitched image | **BATCH\_WELL**/Stitched....CorrCh**\#**.tiff | Used for manual confirmation of correct stitching parameters.  |

| Pipeline 9 \- Analysis |  |  |  |
| :---- | :---- | :---- | :---- |
| Input: corrected Cell Painting (images\_corrected/cellpainting) and Barcoding (images\_corrected/barcoding) |  |  |  |
| Output folder: workspace/analysis |  |  |  |
| Pipeline Steps | Output | File Names | Corrects For |
| Align Cell Painting images to Barcoding images using DAPI channels |  |  | Mis-alignments caused by multi-session acquisition |
| Identify and mask out overly-confluent regions  | % each image overly-confluent | ConfluentRegions.csv | Overly-confluent regions |
| Identify cells, nuclei, cytoplasm, and foci | Objects | Cells.csv Cytoplasm.csv Foci.csv Nuclei.csv |  |
| Measure foci intensities and call barcodes | Barcode calls | Foci.csv |  |
| Cell painting measurements | Cell painting measurements | Cells.csv Cytoplasm.csv Nuclei.csv |  |
| Filter objects into Perfect Cells, Great Cells, Empty Cells, Perfect Foci | Gross object classification |  |  |
| Annotate foci touching cell edges |  | Foci\_NonCellEdge.csv | Improper foci to cell assignment for foci at edges of cells |
| Measure image quality | Image quality metrics for all images |  | Allows for filtering based on image quality. No thresholds currently set. |
|  | Merged and annotated image | CorrCh**\#**\_Site\_**\#**\_Overlay.png |  |
| Save segmentation masks of Cells, Nuclei, and Cytoplasm | Segmentation masks | Plate\_**\#**\_Well\_**\#**\_Site\_**\#**\_Cells\_Objects.tiff Plate\_**\#**\_Well\_**\#**\_Site\_**\#**\_Cytoplasm\_Objects.tiff Plate\_**\#**\_Well\_**\#**\_Site\_**\#**\_Nuclei\_Objects.tiff |  |

