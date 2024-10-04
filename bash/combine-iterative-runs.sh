#!/bin/bash

# Run this script from the root of the `group_run_*` directory

# /datadrive/clim-recal-results/group_run_2024-09-26-15-11
# Manaually add in 1981 data from 
# /datadrive/clim-recal-results/group_run_2024-09-30-16-04/run_24-09-30_16-07


combined_dir=./combined_output

# combined_dir=/mnt/vmfileshare/ClimateData/processed_2024_09_26/combined_output

mkdir -p $combined_dir

# Get all output directories
output_dirs=`find . -type d -name "run_*"`

for output_dir in $output_dirs; do

    # The trailling slash on the `$output_dir` is required!
    rsync \
      --recursive \
      --verbose \
      $output_dir/ \
      $combined_dir
done
