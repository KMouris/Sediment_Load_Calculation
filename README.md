# Sediment load calculation based on RUSLE and SEDD

# Introduction
Model chain to compute sediment loads using RUSLE and the SEDD model

## Libraries

*Python* libraries:  *gdal*, *numpy*, *pandas*

*Standard* libraries: *calendar*, *datetime*, *glob*, *re*, *os*, *sys*, *shutil*, *time*

## Input
The following input variables must be specified to run the code:

### General specifications

| Input argument | Type | Description |
|-----------------|------|-------------|
|`start_date`| STRING | Determines time interval for analysis (format: YYYYMM) |
|`end_date`| STRING | Determines time interval for analysis (format: YYYYMM)  |
|`calc_bed_load`| BOOLEAN | Optional bed load guesstimation  |
|`results_path`| STRING |Path of the main result folder|
|`beta`| FLOAT |catchment-specific beta parameter for the SEDD model|
|`cell_area`| FLOAT |pixel area (ha)|

### Input raster and shape files

| Input argument | Type | Description |
|-----------------|------|-------------|
|`cp_path`| STRING | path for the land cover and management factor (.tif format) |
|`k_path`| STRING | path for the soil erodibility factor (.tif format)  |
|`ls_path`| STRING | path for the slope length and steepness factor (.tif format)  |
|`p_path`| STRING | path for the support practice factor (.tif format)  |
|`tt_path`| STRING | path for the travel time raster (.tif format)  |
|`R_folder`| STRING | path to the 'monthly' R factor rasters (.tif, date information must be included in the format YYYYMM)  |
|`clip_path`| STRING | path to the subcatchment shapes (format: Catchment_NAME.shp  |

Note: All raster files must have the same extent and pixel size (resolution).