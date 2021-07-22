"""File contains all needed modules and libraries, as well as the user input. """

# import all needed basic python libraries
try:
    import glob
    import os
    import sys
    import time
    import datetime
    import re
    import shutil
    from calendar import monthrange
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing basic libraries (required: glob, os, sys, time')
    print(b)

# import additional python libraries
try:
    import numpy as np
    import pandas as pd
    import gdal
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing fundamental packages (required: gdal, numpy, pandas')
    print(b)


""" Input variable description: 

* Input rasters: ---------------------------------------------------------------------------------------------------
*** All rasters must have the same extent, cell size (resolution) 
- cp_path: land cover factor raster (.tif format)
- k_path: soil erodibility factor (.tif format)
- ls_path: slope length and steepness factor (.tif format)
- p_path: support practice factor (.tif format)
- tt_path: travel time raster (.tif format)

* RFactor rasters ---------------------------------------------------------------------------------------------------
*** Folder where the 'monthly' RFactor rasters (in .tif) format are located. There should be one raster for each month
    to be analyzed. The file name must include the year-month of the raster data in the format YYYYMM
- R_folder: folder with .tif files 

* Clipping shapes: -------------------------------------------------------------------------------------------------
*** files must be in *.shp format and have the same projection as the input rasters. 
*** Each file name must be in the format Catchment_NAME.shp
*** ALL .shp files in the input folder will be used to clip the results and generate result tables
- clip_path: FOLDER with *.shp files, whoch correspond to the shape files for different catchment areaes,  with which 
              to clip the result rasters. 
              
* Results folder ---------------------------------------------------------------------------------------------------*
- results_path: FOLDER path where to save the resulting SY, SL, and Total SL results. 

* Calculation constants ---------------------------------------------------------------------------------------------
- beta: previously calibrated Beta value, which must be negative
-cell_area = area of a single raster cell (in ha)
"""

# Import input rasters:
cp_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\Cp_Mean_snap.tif'
k_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\kfac_st_snap.tif'
ls_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\LS_V11b.tif'
p_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\p_factor.tif'
tt_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\traveltime_final_h_snap.tif'

# Rfactor rasters:
R_folder = r'Y:\Abt1\hiwi\Oreamuno\Tasks\Snow_Codes\Modifications_MF\Results\R_factor_REM_db'

# Clipping shape:
# clip_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Shape'
clip_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Clipping_Shapes'

# Results:
# results_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Results\Rain_only'
results_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Calculations\GIT_codes\SYSL_Results'

# Calculation constants:
beta = -0.5639  # Must be a negative number!
cell_area = 0.0625  # in hectares (ha)

