# Welcome to the `clim-recal` repository! 

Welcome to `clim-recal`, a specialized resource designed to tackle systematic errors or biases in Regional Climate Models (RCMs). As researchers, policy-makers, and various stakeholders explore publicly available RCMs, they need to consider the challenge of biases that can affect the accurate representation of climate change signals. `clim-recal` provides both a **broad review** of available bias correction methods as well as **practical tutorials** and **guidance** on how to easily apply those methods to various datasets.

`clim-recal` is an **Extensive guide to application of BC methods**: 

- Accessible information for non quantitative researchers and lay-audience stakeholders 
- Technical resource for application BC methods
- Framework for open additions
- In partnership with the MetOffice to ensure the propriety, quality, and usability of our work
- Full pipeline for bias-corrected data of the ground-breaking local-scale (2.2km) [Convection Permitting Model (CPM)](https://www.metoffice.gov.uk/pub/data/weather/uk/ukcp18/science-reports/UKCP-Convection-permitting-model-projections-report.pdf). 


## Table of Contents

2. [Overview: Bias Correction Pipeline](#overview-bias-correction-pipeline)
3. [Documentation](#documentation)
4. [The dataset](#the-dataset)
4. [Guidance for Non-Climate Scientists](#guidance-for-non-climate-scientists)
5. [Guidance for Climate Scientists](#guidance-for-non-climate-scientists)
6. [Research](#research)
7. [References](#references)
8. [License](#license)
9. [Contributors](#contributors)

## Overview: Bias Correction Pipeline

Here we provide an example of how to run a debiasing pipeline starting. The pipeline has the following steps:

1. **Set-up & data download**
    *We provide custom scripts to facilitate download of data*
2. **Preprocessing**
    *This includes reprojecting, resampling & splitting the data prior to bias correction*
5. **Apply bias correction**
    *Our pipeline embeds two distinct methods of bias correction*
6. **Assess the debiased data**
    *We have developed a way to assess the quality of the debiasing step across multiple alternative methods*

### Prerequisites

#### Setting up your environment

Methods can be used with a custom environment, here we provide a Anaconda
environment file for ease-of-use. 
```sh
conda env create -f environment.yml
```
#### Downloading the data

This streamlined pipeline is designed for raw data provided by the Met Office, accessible through the [CEDA archive]((https://catalogue.ceda.ac.uk/uuid/ad2ac0ddd3f34210b0d6e19bfc335539)). It utilizes [UKCP](https://data.ceda.ac.uk/badc/ukcp18/data/land-cpm/uk/2.2km) control, scenario data at 2.2km resolution, and [HADs](https://data.ceda.ac.uk/badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.1.0.0/1km) observational data. For those unfamiliar with this data, refer to our [the dataset](#the-dataset) section.

To access the data, [register](https://archive.ceda.ac.uk/) at the CEDA archive and configure your FTP credentials in "My Account". Utilize our [ceda_ftp_download.py](python/data_download/) script to download the data.

```sh
# cpm data
python3 ceda_ftp_download.py --input /badc/ukcp18/data/land-cpm/uk/2.2km/rcp85/ --output 'output_dir' --username 'uuu' --psw 'ppp' --change_hierarchy

# hads data
python3 ceda_ftp_download.py --input /badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.1.0.0/1km --output 'output_dir' --username 'uuu' --psw 'ppp'
```
You need to replace `uuu` and `ppp` with your CEDA username and FTP password respectively and replace `output_dir` with the directory you want to write the data to.

The `--change_hierarchy` flag modifies the folder hierarchy to fit with the hierarchy in the Turing Azure file store. This flag only applies to the UKCP data and should not be used with HADs data. You can use the same script without the `--change_hierarchy` flag in order to download files without any changes to the hierarchy.

> 📢 If you are an internal collaborator you can access the raw data as well as intermediate steps through our Azure server. [See here for a How-to]().

### Reproject the data
The HADs data and the UKCP projections have different resolution and coordinate system. For example the HADs dataset uses the British National Grid coordinate system.

 
### Resample the data

In [`python/load_data/data_loader.py`](reference/data_loader) we have written a few functions for loading and concatenating data into a single xarray which can be used for running debiasing methods. Instructions in how to use these functions can be found in `python/notebooks/load_data_python.ipynb`.

Resample the HADs data from 1km to 2.2km grid to match the UKCP reprojected grid.

reproject the UKCP datasets to the British National Grid coordinate system.
**Resampling** for the HADsUK datasets from 1km to a 2.2 km grid to match the UKCP re-projected grid.
**Data loaders** functions for loading and concatenating data into a single xarray which can be used for running debiasing methods.

### Preparing the bias correction and assessment

### Applying the bias correction
  - **Debiasing scripts** that interface with implementations of the debiasing (bias correction) methods implemented by different libraries (by March 2023 we have only implemented the [`python-cmethods`](https://github.com/alan-turing-institute/python-cmethods) library).

  The code in the `python/debiasing` directory contains scripts that interface with implementations of the debiasing methods 
implemented by different libraries.

Note: By March 2023 we have only implemented the [`python-cmethods`](https://github.com/alan-turing-institute/python-cmethods) library.


### The cmethods library

This repository contains a python script used to run debiasing in climate data using a fork of the [original python-cmethods](https://github.com/btschwertfeger/python-cmethods) module written by Benjamin Thomas Schwertfeger's , which has 
been modified to function with the dataset used in the `clim-recal` project. This library has been included as a 
submodule to this project, so you must run the following command to pull the submodules required.

```sh
cd debiasing
git submodule update --init --recursive
```

The [run_cmethods.py](python/debiasing/run_cmethods.py) allow us to adjusts climate biases in climate data using the python-cmethods library. 
It takes as input observation data (HADs data), control data (historical UKCP data), and scenario data (future UKCP data), 
and applies a correction method to the scenario data. The resulting output is saved as a `.nc` to a specified directory.
The script will also produce a time-series and a map plot of the debiased data.

**Usage**:

The script can be run from the command line using the following arguments:

```sh
python3 run_cmethods.py.py --obs <path to observation datasets> --contr <path to control datasets> --scen <path to scenario datasets> --shp <shapefile> 
--out <output file path> -m <method> -v <variable> -u <unit> -g <group> -k <kind> -n <number of quantiles> -p <number of processes>
```

where:

- `--obs` specifies the path to the observation datasets
- `--contr` specifies the path to the control datasets
- `--scen`  specifies the path to the scenario datasets (data to adjust)
- `--shp`  specifies the path to a shapefile, in case we want to select a smaller region (default: None)
- `--out` specifies the path to save the output files (default: current directory)
- `--method` specifies the correction method to use (default: quantile_delta_mapping)
- `-v` specifies the variable to adjust (default: tas)
- `-u`  specifies the unit of the variable (default: °C)
- `-g`  specifies the value grouping (default: time)
- `-k`  specifies the method kind (+ or *, default: +)
- `-n`  specifies the number of quantiles to use (default: 1000)
- `-p`  specifies the number of processes to use for multiprocessing (default: 1)

For more details on the script and options you can run:

```sh
python run_cmethods.py --help
```
**Main Functionality**:

The script applies corrections extracted from historical observed and simulated data between `1980-12-01` and `1999-11-30`.
Corrections are applied to future scenario data between `2020` and `2080` (however there is no available scenario data between `2040` to `2060`, so this time
period is skipped.


The script performs the following steps:

- Parses the input arguments.
- Loads, merges and clips (if shapefile is provided) the all input datasets and merges them into two distinct datasets: the observation and control datasets.
- Aligns the calendars of the historical simulation data and observed data, ensuring that they have the same time dimension 
and checks that the observed and simulated historical data have the same dimensions.
- Loops over the future time periods specified in the `future_time_periods` variable and performs the following steps:
  - Loads the scenario data for the current time period.
  - Applies the specified correction method to the scenario data.
  - Saves the resulting output to the specified directory.
  - Creates diagnotic figues of the output dataset (time series and time dependent maps) and saves it into the specified directory.

In this script 
datasets are debiased in periods of 10 years, in a consecutive loop, for each time period it will produce an `.nc` output file
with the adjusted data and a time-series plot and a time dependent map plot of the adjusted data. 

**Working example**.

Example of code working on the **`clim-recal`** dataset:
```sh
python run_cmethods.py --scen /Volumes/vmfileshare/ClimateData/Reprojected/UKCP2.2/tasmax/01/latest --contr /Volumes/vmfileshare/ClimateData/Reprojected/UKCP2.2/tasmax/01/latest/ --obs /Volumes/vmfileshare/ClimateData/Processed/HadsUKgrid/resampled_2.2km/tasmax/day/ --shape ../../data/Scotland/Scotland.bbox.shp -v tasmax --method delta_method --group time.month -p 5
```
    
### Assessing the corrected data

## Documentation
🚧 In Progress

We are in the process of developing comprehensive documentation for our codebase to supplement the guidance provided in this document. In the interim, for Python scripts, you can leverage the inline documentation (docstrings) available within the code. To access a summary of the available options and usage information for any Python script, you can use the `--help` flag in the command line as follows:

```sh
python resampling_hads.py --help

usage: resampling_hads.py [-h] --input INPUT [--output OUTPUT] [--grid_data GRID_DATA]

options:
-h, --help            show this help message and exit
--input INPUT         Path where the .nc files to resample is located
--output OUTPUT       Path to save the resampled data data
--grid_data GRID_DATA Path where the .nc file with the grid to resample is located
```

This will display all available options for the script, including their purposes.

For R scripts, please refer to the comments within the R scripts for contextual information and usage guidelines, and feel free to reach out with any specific queries.

We appreciate your patience and encourage you to check back for updates on our ongoing documentation efforts.

## The dataset

### UKCP18
The UK Climate Projections 2018 (UKCP18) dataset offers insights into the potential climate changes in the UK. UKCP18 is an advancement of the UKCP09 projections and delivers the latest evaluations of the UK's possible climate alterations in land and marine regions throughout the 21st century. This crucial information aids in future Climate Change Risk Assessments and supports the UK’s adaptation to climate change challenges and opportunities as per the National Adaptation Programme.

### HADS
[HadUK-Grid](https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/haduk-grid) is a comprehensive collection of climate data for the UK, compiled from various land surface observations across the country. This data is organized into a uniform grid to ensure consistent coverage throughout the UK at up to 1km x 1km resolution. The dataset, spanning from 1836 to the present, includes a variety of climate variables such as air temperature, precipitation, sunshine, and wind speed, available on daily, monthly, seasonal, and annual timescales. 

## Guidance for Non-Climate Scientists

Regional climate models (RCMs) contain systematic errors, or biases in their output [1]. Biases arise in RCMs for a number of reasons, such as the assumptions in the general circulation models (GCMs), and in the downscaling process from GCM to RCM [1,2].

Researchers, policy-makers and other stakeholders wishing to use publicly available RCMs need to consider a range of "bias correction” methods (sometimes referred to as "bias adjustment" or "recalibration"). Bias correction methods offer a means of adjusting the outputs of RCM in a manner that might better reflect future climate change signals whilst preserving the natural and internal variability of climate [2]. 

## Guidance for Climate Scientists

### Let's collaborate!

We hope to bring together the extensive work already undertaken by the climate science community and showcase a range of libraries and techniques. If you have suggestions on the repository, or would like to include a new method (see below) or library, please raise an issue or [get in touch](mailto:clim-recal@turing.ac.uk)! 

### Adding to the conda environment file 

To use `R` in anaconda you may need to specify the `conda-forge` channel:

```sh
conda config --env --add channels conda-forge
```

Some libraries may be only available through `pip`, for example, these may
require the generation / update of a `requirements.txt`:

```sh
pip freeze > requirements.txt
```

and installing with:

```sh
pip install -r requirements.txt
```

## Research
### Methods taxonomy 

Our work-in-progress taxonomy can be viewed [here](https://docs.google.com/spreadsheets/d/18LIc8omSMTzOWM60aFNv1EZUl1qQN_DG8HFy1_0NdWk/edit?usp=sharing). When we've completed our literature review, it will be submitted for publication in an open peer-reviewed journal. 

Our work is however, just like climate data, intended to be dynamic, and we are in the process of setting up a pipeline for researchers creating new methods of bias correction to be able to submit their methods for inclusion on in the **clim-recal** repository. 

## Code

In this repo we aim to provide examples of how to run the debiasing pipeline starting from the raw data available from the [MET office via CEDA](https://catalogue.ceda.ac.uk/uuid/ad2ac0ddd3f34210b0d6e19bfc335539) to the creation of debiased (bias corrected) datasets for different time periods. The pipeline has the following steps:

1. Reproject the [UKCP](https://data.ceda.ac.uk/badc/ukcp18/data/land-cpm/uk/2.2km) control and scenario data to the same coordinate system as the [HADs](https://data.ceda.ac.uk/badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.1.0.0/1km) observational data (British National Grid).
2. Resample the HADs data from 1km to 2.2km grid to match the UKCP reprojected grid.
3. Run debiasing method on the control and observational data and project it into the scenario dataset. 

After each of these steps the reprojected, resampled and debiased scenario datasets are produced and saved in an Azure fileshare storage (more details about this bellow).


### Bash

Here you find scripts to reproject the UKCP datasets to the British National Grid coordinate system.

### Python

In the `python` subdirectory you can find code for the different data download, processing and debiasing steps:
   - **Data download** for a script to download data from the CEDA archive.
   - **Resampling** for the HADsUK datasets from 1km to a 2.2 km grid to match the UKCP re-projected grid.
   - **Data loaders** functions for loading and concatenating data into a single xarray which can be used for running debiasing methods.
   - **Debiasing scripts** that interface with implementations of the debiasing (bias correction) methods implemented by different libraries (by March 2023 we have only implemented the python-cmethods library).
    
More details in how to use this code can be found in [the python README file](python/README.md) and the environment used in this [environment setup file](setup-instructions.md).

### R 

In the `R` subdirectory you can find code for replicating the different data processing and debiasing steps as above, along with comparisons of methods between the two languages. 
- **bias-correction-methods** for bias correction (debiasing) methods available specifically in `R` libraries
- **comparing-r-and-python** for replication of resampling and reviewing the bias correction methods applied in `python`.
- **Resampling** for resampling the HADsUK datasets from 1km to 2.2km grid in `R`.


## Data access

### How to download the data

You can download the raw UKCP2.2 climate data from the CEDA archive. Go [here](https://archive.ceda.ac.uk/), create an account and set up your FTP credentials in "My Account". You can then use the python script under `python/data_download/` to download the data: 
```sh
python3 ceda_ftp_download.py --input /badc/ukcp18/data/land-cpm/uk/2.2km/rcp85/ --output 'output_dir' --username 'uuu' --psw 'ppp' --change_hierarchy
```
You need to replace `uuu` and `ppp` with your CEDA username and FTP password respectively and replace 'output_dir' with the directory you want to write the data to.

Note that the `--change_hierarchy` flag is used, which modifies the folder hierarchy to fit with the hierarchy in the Turing Azure file store. You can use the same script without the `--change_hierarchy` flag in order to download files without any changes in the hierarchy.

You can download the HADs observational data from the CEDA archive using the same python script, with a different input (note the `change_hierarchy` flag should not be used with HADs data - only applies to UKCP data):
```sh
python3 ceda_ftp_download.py --input /badc/ukmo-hadobs/data/insitu/MOHC/HadOBS/HadUK-Grid/v1.1.0.0/1km --output output_dir --username 'uuu' --psw 'ppp'
```

### Accessing the pre-downloaded/pre-processed data

Datasets used in this project (raw, processed and debiased) have been pre-downloaded/pre-processed and stored in an Azure fileshare set-up for the `clim-recal` project (https://dymestorage1.file.core.windows.net/vmfileshare). You need to be given access, and register your IP address to the approved list in the following way from the azure portal:

- Go to dymestorage1 page `Home > Storage accounts > dymestorage1`
- Navigate to *Networking* tab under Security + networking
- Add your IP under the Firewall section

Once you have access you can mount the fileshare. On a Mac you can do it from a terminal:

`open smb://dymestorage1.file.core.windows.net/vmfileshare`

username is `dymestorage1` and the password can be found in the access keys as described in [here](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-keys-manage?tabs=azure-portal#view-account-access-keys).

The fileshare will be mounted under

`/Volumes/vmfileshare/`

You might also need to add your IP address to the Firewall IP expections list in the Azure portal by going to the `dymestorage1` resource and selecting `Networking`.

Instructions on how the mount in other operating systems can be found in [the azure how-tos](https://learn.microsoft.com/en-us/azure/storage/files/storage-how-to-use-files-linux?tabs=smb311). 

Alternatively, you can access the Azure Portal, go to the dymestorage1 fileshare and click the "Connect" button to get an automatically generated script. This script can be used from within an Azure VM to mount the drive.

### Pre-downloaded/pre-processed data description

All the data used in this project can be found in the `/Volumes/vmfileshare/ClimateData/` directory. 

```sh
.
├── Debiased  # Directory where debiased datasets are stored.
│   └── tasmax
├── Processed # Directory where processed climate datasets are stored. 
│   ├── CHESS-SCAPE
│   ├── HadsUKgrid # Resampled HADs grid.
│   └── UKCP2.2_Reproj # Old reprojections (to delete).
├── Raw # Raw climate data
│   ├── CHESS-SCAPE
│   ├── HadsUKgrid
│   ├── UKCP2.2
│   └── ceda_fpt_download.py # script to download data from CEDA database. 
├── Reprojected # Directory where reprojected UKCP datasets are stored.
│   └── UKCP2.2
├── Reprojected_infill # Directory where reprojected UKCP datasets are stored, including the newest infill UKCP2.2 data published in May 2023.
└── shapefiles
    ├── Middle_Layer_Super_Output_Areas_(December_2011)_Boundaries
    └── infuse_ctry_2011_clipped
```

## Future directions

In future, we're hoping to include:

- Further bias correction of UKCP18 products 
- Assessment of the influence of different observational data 
- Pipelines for adding an additional method 

## References

 1. Senatore et al., 2022, https://doi.org/10.1016/j.ejrh.2022.101120 
 2. Ayar et al., 2021, https://doi.org/10.1038/s41598-021-82715-1 

## License

## Contributors
