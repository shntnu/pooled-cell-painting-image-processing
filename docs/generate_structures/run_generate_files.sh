#!/bin/bash

python generate_outputs.py \
    --io-json ../io.json \
    --batch Batch1 \
    --plates Plate1 \
    --rows 1 \
    --columns 1 \
    --wells A01 \
    --tileperside 2 \
    --barcoding-cycles 1 \
    --output-file output_paths.json \
    --output-format both \
    --create-files \
    --base-path Source1/
