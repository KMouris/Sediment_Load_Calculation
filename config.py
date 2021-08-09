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
    import calendar
    from calendar import monthrange
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing basic libraries (required: glob, os, sys, time, datetime, re, shutil, calendar')
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
* Decision variables -----------------------------------------------------------------------------------------------
- start_date, end_date: strings or integers, in yyyymm (YearMonth) format, which determine the range of dates to 
                        analyze for. If they are the same, only said month will be analyzed. 
- calc_bed_load: boolean, if True then the bed load is calculated and added to the results table for each catchment. 

* Input rasters: ---------------------------------------------------------------------------------------------------
    *All rasters must have the same extent, cell size (resolution) 
- cp_path: string, path for the land cover factor raster (.tif format)
- k_path: string, path for the soil erodibility factor (.tif format)
- ls_path: string, path for the slope length and steepness factor (.tif format)
- p_path: string, path for the support practice factor (.tif format)
- tt_path: string, path for the travel time raster (.tif format)

* RFactor rasters ---------------------------------------------------------------------------------------------------
    *Folder where the 'monthly' RFactor rasters (in .tif) format are located. There should be one raster for each month
    to be analyzed. The file name must include the year-month of the raster data in the format YYYYMM
- R_folder: string, folder path with .tif files 

* Clipping shapes: -------------------------------------------------------------------------------------------------
    *files must be in *.shp format and have the same projection as the input rasters. 
    *Each file name must be in the format Catchment_NAME.shp
    *All .shp files in the input folder will be used to clip the results and generate result tables
- clip_path: string, folder path with *.shp files, which correspond to the shape files for different catchment areas, 
             with which to clip the result rasters. 
              
* Results folder ---------------------------------------------------------------------------------------------------*
- results_path: path,  string, path where to save the resulting SY, SL, and Total SL results for each catchment. 

* Calculation constants ---------------------------------------------------------------------------------------------
- beta: float, coefficient which was calibrated for the catchment (see Ferro and Porto (2000))
- cell_area = float, area of a single raster cell (in ha)
"""
# Dates
start_date = '201710'
end_date = '201712'
calc_bed_load = False

# Import input rasters:
cp_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\Cp_Mean_snap.tif'
k_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\kfac_st_snap.tif'
ls_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\LS_V11b.tif'
p_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\p_factor.tif'
tt_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Rasters\traveltime_final_h_snap.tif'

# Rfactor rasters:
# R_folder = r'Y:\Abt1\hiwi\Oreamuno\Tasks\Snow_Codes\Modifications_MF\Results\R_factor_REM_db'
R_folder = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Calculations\Python_Programs\Results\RFactor_REM_db\Non-CorrectedData'

# Clipping shape:
# clip_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Shape'
clip_path = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Clipping_Shapes'

# Results:
# results_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Results\Rain_only'
results_path = r'C:\Users\Mouris\Desktop\SY_SL_Calculation_Git\Results'

# Calculation constants:
beta = 0.5639
cell_area = 0.0625  # in hectares (ha)

