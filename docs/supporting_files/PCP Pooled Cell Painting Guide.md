# Pre work

1. Get collaborator to fill out a [spreadsheet]() with metadata info: [Imaging Metadata]()
2. Then we migrate this to the metadatatemplate.json in [https://github.com/broadinstitute/pooled-cell-painting-image-processing/blob/master/configs/metadatatemplate.json](https://github.com/broadinstitute/pooled-cell-painting-image-processing/blob/master/configs/metadatatemplate.json)
3. Get the barcode library from the collaborator. Recommend rename to **Barcodes.csv** and name columns **Barcode** for the barcode sequences and **Construct** for the gene name or perturbation associated with that compound. Upload this to s3://**BUCKET**/projects/**PROJECT**/workspace/metadata/**BATCH**/

# Upload Images to s3

## Transfer files:

Make sure that image file structure follows correct format:
s3://***BUCKET***/projects/***PROJECT***/***BATCH***/images/***PLATE***/10X\_c***\#***\_SBS-***\#***/
s3://***BUCKET***/projects/***PROJECT***/***BATCH***/images/***PLATE***/20X\_CP\_CP***PLATE***/

\*\*\*Make sure the CP images start with “20X\_CP\_”

# Run each lambda function in turn

The lambda functions are built to process the Cell Painting and barcoding images and go through illumination correction, cell segmentation, stitching, and analysis.

## 1\. Make a new metadata.json

1. Copy the [metadata template](https://github.com/broadinstitute/pooled-cell-painting-image-processing/blob/master/configs/metadatatemplate.json) to Atom or another text editor
2. Edit the template as follows:

	Use painting\_rows and painting\_columns if acquisition is square
Use painting\_imperwell if acquisition is circular. (Map for number must be saved in workflow, comes from “**What is the acquisition grid size of the cell painting images?**” in [spreadsheet](https://docs.google.com/spreadsheets/d/1JXQdC8qWAYReUMxEgAxJSh008PCCBSTFlZneKro2sD4/edit?pli=1#gid=0))
Channeldict is microscope channel-to-\[stain, frame\]

- for multiple rounds staining:
  - key are the folder name of the rounds
  - for the stain that is common between rounds, include \_roundN in stain name (e.g., DNA\_round0)
  - For example:

```py
{
'round0':{'DAPI':['DNA_round0',0], 'GFP':['Phalloidin',1]},
'round1':{'DAPI':['DNA_round1',0],'GFP':['GM130',1], 'A594':['Tubulin',2], 'Cy5':['Calnexin', 3]},
'round2':{'DAPI':['DNA_round2',0],'GFP':['COX-IV',1], 'A594':['TDP-43',2], 'Cy5':['G3BP1',3], '750':['LAMP1',4]},
'round3':{'DAPI':['DNA_round3',0], 'GFP':['Catalase',1], 'A594':['Golgin-97',2], 'Cy5':['p65',3], '750':['pRPS6',4]},
'round4':{'DAPI':['DNA_round4',0], 'GFP':['Syto9',1]}
 }
```

- for single round staining:
  - key is the CP folder name (or beginning of the folder name?)

  e.g.

```py
{'CP_20X':{'DAPI':['DNA', 0], 'GFP':['Phalloidin',1]}}
```

  ^ The information for the names of channels (e.g., DAPI) and their contents/CP names (e.g., DNA) should come from the spreadsheet “**Order of phenotyping acquisition**:” question and from looking at the file names themselves to confirm channel names. (e.g., **WellC1\_PointC1\_0005\_ChannelDAPI,GFP,A594\_800ms,Cy5,AF750\_200ms\_30p\_Seq0005.nd2**)

  Note: the names of the channels in the channel dictionary must match what is expected in the CellProfiler illum pipeline: **DNA, Protein, Mito, WGA, ER** (or you need to change the pipeline)

  Use barcode\_rows and barcode\_columns if acquisition is square

  Use barcode\_imperwell if acquisition is circular. (Map for number must be saved in workflow). This comes from “**What is the acquisition grid size of the barcoding images?**” in the spreadsheet.

  barcoding\_cycles comes from “**How many barcode cycles are there?**” in spreadsheet

overlap\_pct comes from **% overlap on images in spreadsheet** in spreadsheet
round\_or\_square comes from **What is the acquisition grid size of the cell painting images?** And whether this is round or square.
fast\_or\_slow\_mode and one\_or\_many\_files enable processing of pilot acquisitions and should always be slow and many, respectively
offset\_tiles are 0 unless trouleshooting gross stitching misalignments
compress should be True
stitchorder will be in metadata shared in batch

- for square acquisitions use Grid: snake by rows or Grid: row-by-row
- for round acquisitions use Filename defined position
  range\_skip is sampling frequency for SegmentCheck
  tileperside and final\_tile\_size are for cropping whole-well stitched images

3. Save it as **metadata.json**
4. Upload to s3 in s3://**BUCKET**/projects/**PROJECT**/workspace/metadata/**BATCH**/metadata.json

Example metadata.json for VarChAMP Batch2:

```
{
   "_commenton_imperwell":"If used, the imperwell fields will overwrite the columns and rows. Set to 0 if not using.",
   "painting_rows":"38",
   "painting_columns":"38",
   "painting_imperwell":"293",
   "_commenton_Channeldict":"Values are channel-to-[stain, frame] mapping",
   "_commenton_Channeldict":"If multiple rounds, keys are folder names of the rounds. For the stain that is common between rounds, include _roundN in stain name. ",
   "_commenton_Channeldict":"e.g. {'round0':{'DAPI':['DNA_round0',0], 'GFP':['Phalloidin',1]}, 'round1':{'DAPI':['DNA_round1',0],'GFP':['ER',1]}}",
   "_commenton_Channeldict":"If one round, key is the CP folder name. e.g. {'20X_CP':{'DAPI':['DNA', 0], 'GFP':['Phalloidin',1]}}",
   "Channeldict":"{'CP_20X':{'DAPI':['DNA', 0], 'GFP':['VariantProtein',1], 'A594':['Mito',2], 'Cy5':['ER',3],'AF750':['WGA',4]}}",
   "barcoding_rows":"19",
   "barcoding_columns":"19",
   "barcoding_imperwell":"88",
   "barcoding_cycles":"8",
   "overlap_pct":"10",
   "fast_or_slow_mode":"slow",
   "one_or_many_files":"many",
   "round_or_square":"round",
   "quarter_if_round":"False",
   "_commenton_offset_tiles":"Set to 0 unless trouleshooting gross stitching misalignments",
   "barcoding_xoffset_tiles":"0",
   "barcoding_yoffset_tiles":"0",
   "painting_xoffset_tiles":"0",
   "painting_yoffset_tiles":"0",
   "compress":"True",
   "_commenton_stitchorder":"Typically should be either 'Grid: snake by rows','Grid: row-by-row', or 'Filename defined position'",
   "stitchorder":"Filename defined position",
   "_commenton_range_skip":"Set your sampling frequency for SegmentCheck",
   "range_skip":"16",
   "_commenton_tile_settings":"Parameters for the cropping of whole-well stitched image",
   "tileperside":"5",
   "final_tile_size":"5500"
}
```

## 2\. Create or copy config from previous project

There are two config files that you need to upload. Blank versions can be found [on GitHub](https://github.com/broadinstitute/pooled-cell-painting-image-processing/tree/master/configs).These need to be set once per Batch.


1. **configFleet.json**
   This is like the Fleet file (e.g., analysisFleet.json) for Distributed Cell Painting. You can grab one from a previous project or download from GitHub and replace the secure info.
2. **configAWS.py**
   This is like config.py for Distributed Cell Painting.

When done, upload both files to s3://**BUCKET**/projects/**PROJECT**/workspace/lambda/**BATCH**

## 3\. Add your pipelines to s3

Pipelines can be found on GitHub [here](https://github.com/broadinstitute/pooled-cell-painting-image-processing/tree/master/pipelines).

1. Select the number of cycles based on “**How many barcode cycles are there?**” from spreadsheet
2. Copy first 3 pipelines (1\_, 2\_, and 3\_) to s3://**BUCKET**/projects/**PROJECT**/workspace/pipelines/**BATCH**

## 4\. Change config\_dict in the lambda function

1. Go to [lambda functions](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions) or specifically [PCP-1-CP-IllumCorr](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/PCP-1-CP-IllumCorr?tab=code) if starting a new run
2. In the file lambda\_function, scroll down to config\_dict (line 21\) and change the **APPNAME** and other fields like you would for config.py:

![][image1]

I’ve made a table for how to set APPNAME and EXPECTED\_NUMBER\_FILES for each step: [PCP Lambda table](PCP-Lambda-table.csv)

| Step                  | APPNAME in config\_dict                | EXPECTED\_NUMBER\_FILES                                                  |
|:----------------------|:---------------------------------------|:-------------------------------------------------------------------------|
| PCP-1-CP-IllumCorr    | **PROJECT**\_IllumPainting             | **\# of cell painting channels (5)**                                     |
| PCP-2-CP-ApplyIlum    | **PROJECT**\_ApplyIllumPainting        | **\# CP Channels x \# sites \+ 5 for the csvs**                          |
| PCP-3-CP-SegmentCheck | **PROJECT**\_PaintingSegmentationCheck | **"CHECK\_IF\_DONE\_BOOL": "False",**                                    |
| PCP-4-CP-Stitching    | **PROJECT**\_PaintingStitching         | **NA**                                                                   |
| PCP-5-BC-IllumCorr    | **PROJECT**\_IllumBarcoding            | **BC channels (5)\* plates(1) \* cycles(8)**                             |
| PCP-6-BC-ApplyIllum   | **PROJECT**\_ApplyIllumBarcoding       | **"CHECK\_IF\_DONE\_BOOL": "False",**                                    |
| PCP-7-BC-Preprocess   | **PROJECT**\_PreprocessBarcoding       | **\# CSVs (8) \+ 1 (overlay) \+ cycles(8)\* (\#bases \+ DAPI (5) \= 49** |
| PCP-8-BC-Stitching    | **PROJECT**\_BarcodingStitching        | **This is calculated (not directly set) inside the lambda function**     |
| PCP-9-Analysis        | **PROJECT**\_Analysis                  |                                                                          |

1. Remember to select “**Deploy**” to save your changes

## 4\. Manually trigger a run

1. In the Lambda page for [PCP-1-CP-IllumCorr](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/PCP-1-CP-IllumCorr?tab=code), select the orange “Test” button to manually trigger a run
2. There will be a popup that ways “Configure Test Event”
3. Name your event something that makes sense and includes your Batch “VarChMP\_Batch2”
4. If there is not an existing matching template, select “S3-put”
5. You need to change the name of the bucket from “example bucket” to whatever bucket you’re working in.
6. Change the Object Key to be the Key to the pipeline in S3. This is available if you navigate to the object in browser to the object’s page and then Key will be at the top. It should look like a path from the bucket root to that object. To know what key to use, refer to [PCP Lambda table](PCP-Lambda-table.csv).

Example full event:

```py
{
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "1970-01-01T00:00:00.000Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "EXAMPLE"
      },
      "requestParameters": {
        "sourceIPAddress": "127.0.0.1"
      },
      "responseElements": {
        "x-amz-request-id": "EXAMPLE123456789",
        "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "testConfigRule",
        "bucket": {
          "name": "imaging-platform-ssf",
          "ownerIdentity": {
            "principalId": "EXAMPLE"
          },
          "arn": "arn:aws:s3:::imaging-platform-ssf"
        },
        "object": {
          "key": "projects/2021_09_01_VarChAMP_Vidal_Taipale/workspace/pipelines/2023_01_11_Batch2/1_CP_Illum.cppipe",
          "size": 1024,
          "eTag": "0123456789abcdef0123456789abcdef",
          "sequencer": "0A1B2C3D4E5F678901"
        }
      }
    }
  ]
}
```


What this does is start the lambda function when the pipeline is in that s3 location, which it should already be if you’ve added it. Then you can trigger by pressing the orange **Test** button.

## 4\. Start DCP machine

Each lambda function that launches DCP creates a monitor file. You need to manually run this monitor file on your DCP machine.

Log into your DCP EC2 instance
ssh \-i \~/.ssh/**PEMFILE**.pem ec2-user@ or ubuntu@ADDRESS

Start a tmux
tmux new \-s PCP

Activate environment
pyenv shell 3.8.13

Variables (paste in, see [PCP Lambda table](PCP-Lambda-table.csv) for how to set for each step)
PROJECT\_NAME=2021\_09\_01\_VarChAMP\_Vidal\_Taipale
BATCH\_ID=2023\_01\_11\_Batch2
STEPNAME=PaintingStitching
STEP=4
BUCKET=imaging-platform-ssf

Copy the monitor file to your instance
cd \~/efs/${**PROJECT\_NAME}**/workspace/software/Distributed-CellProfiler

aws s3 cp s3://${**BUCKET}**/projects/${**PROJECT\_NAME}**/workspace/monitors/**${BATCH\_ID}**/${**STEP}**/${**PROJECT\_NAME}**\_${**STEPNAME}**SpotFleetRequestId.json files//${**PROJECT\_NAME}**\_${**STEPNAME}**SpotFleetRequestId.json

Run the monitor file
python run.py monitor files/${**PROJECT\_NAME}**\_${**STEPNAME}**SpotFleetRequestId.json

# Troubleshooting:

## Problem

**Response**
"Still work ongoing"

**Function Logs**
…
Checking if all files are present
Sufficient output files found from previous step.
Queue from previous step does not still exist.
Trigger already exists in FIFO queue.
Still work ongoing

## Solution

**Purge the FIFO queue**

- In SQS, select FIFO queue with name PreventOverlappingStarts.fifo
- Actions \> Purge

# How to add the Lambda functions to a new AWS account

## 1\. Create a function in Lambda on AWS

* Name the function and choose Python 3.9 runtime:![][image2]
* Choose existing role LambdaFullAccess![][image3]
* No need for advanced settings

Click **Create Function**

## 2\. Add in the functions from [the GitHub repo](https://github.com/broadinstitute/pooled-cell-painting-image-processing/tree/master/lambda)

* Within the lambda\_function, copy and paste the lambda function from that step (e.g., PCP-1-CP-IllumCorr)
* Save as lambda\_function.py

![][image4]

* Then add in each lambda function helper function in the same folder (e.g., boto3\_setup.py):

![][image5]

* Click Deploy to save code change\! (like Save)

## 3\. Add a layer containing necessary packages

* In AWS Lambda console, scroll down to the bottom and click “Add a layer” under “Layers”
* Add a Layer
  * Select the layer containing the packages necessary (e.g., AWS PandasPython39)

![][image6]

* You can also create your own layer and put in packages manually:

![][image7]

## 4\. Configuration tab (still in Lambda console)

* Slide over from Code tab to Configuration in AWS Lambda console
* [AuSPICES Lambda Setup](https://github.com/broadinstitute/AuSPICES/blob/main/SETUP.md) contains some information about setting up a run

![][image8]

* Select Edit under “General Configuration”

![][image9]

* Memory is 3008 MB
* Ephemeral storage is 512 MB
* Timeout is 15 min
* Execution role is LambdaFullAccess (should already be set by previous step)
* Select Save
* Under Asynchronous configuration or Asynchronous Invocation, click edit: Change to NO retry attempts and Save:

![][image10]

* Environment variables
  * In Configuration tab, under Environment variables copy and paste the two MY\_AWS\_ACCESS\_KEY\_ID and MY\_AWS\_SECRET\_ACCESS\_KEY for an account (copy Erin’s from previous AWS Lambda function)

![][image11]

# Make a FIFO queue (once per account)

There is a function called check\_if\_run\_done that prevents lambda functions (when automated) from triggering too many times. This looks for a first-in, first-out queue. You need to make that for the account.

In **SQS**, click **Create Queue**. Name it “**PreventOverlappingStarts.fifo**” (this name is from awsConfig.py, so if you have issues, check that the name matches with the SQS\_QUEUE mentioned in that file).

Make the type of queue “**FIFO**”

Toggle ON “**content-based deduplication**” under FIFO queue settings.

Select save to save the queue\!

That’s it\! The AWS lambda function is now ready to run\!
