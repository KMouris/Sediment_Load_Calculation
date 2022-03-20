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

"""Input variable description: * Decision variables 
- start_date, end_date: strings, in yyyymm (YearMonth) format, which determine the range of dates to analyze. If they 
are the same, only one month will be analyzed. - calc_bed_load: boolean, if 'True' then the bed load is calculated 
and added to the results table for each subcatchment. 

* Input rasters:
    *All rasters must have the same extent, pixel size (resolution) 
- cp_path: string, path for the land cover factor (.tif format)
- c_winter_path: string, path for the seasonal land cover factor (.tif format; if seasonal_cfactor = True)
- c_summer_path: string, path for the seasonal land cover factor (.tif format; if seasonal_cfactor = True)
- k_path: string, path for the soil erodibility factor (.tif format)
- ls_path: string, path for the slope length and steepness factor (.tif format)
- p_path: string, path for the support practice factor (.tif format)
- tt_path: string, path for the travel time raster (.tif format)

* RFactor rasters
    *Folder where the 'monthly' RFactor rasters (in .tif) format are located. There should be one raster for each month
    to be analyzed. The file name must include the year-month of the raster data in the format YYYYMM
- R_folder: string, folder path with .tif files 

* Clipping shapes:
    *files must be in *.shp format and have the same projection as the input rasters. 
    *Each file name must be in the format Catchment_NAME.shp
    *All .shp files in the input folder will be used to clip the results and generate result tables
- clip_path: string, folder path with *.shp files, which correspond to the shape files for different catchment areas, 
             with which to clip the result rasters. 
              
* Results folder
- results_path: path,  string, path where to save the resulting SY, SL, and Total SL results for each catchment. 

* Calculation constants
- beta: float, coefficient which was calibrated for the catchment (see Ferro and Porto (2000))
- pixel_area = float, area of a single raster pixel (in ha)
"""
# Dates
start_date = '201605'
end_date = '201804'
calc_bed_load = True
seasonal_cfactor = True

# Import input rasters:
k_path = r''
ls_path = r''
p_path = r'
tt_path = r''

if seasonal_cfactor:
    print('Seasonal C factor')
    c_winter_path = r''
    c_summer_path = r''
else:
    cp_path = r''

# Rfactor rasters:
r_folder = r''

# Clipping shape:
clip_path = r''

# Results:
results_path = r''

# Calculation constants:
beta = 0.5639
pixel_area = 0.0625  # in hectares (ha)
