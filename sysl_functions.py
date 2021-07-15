import numpy as np
import pandas as pd
import numpy.ma as ma
from calendar import monthrange
import os

import SYSL_SaveDataFunctions as r_save
import SYSL_RasterDataFunctions as r_data


# In this file the user finds the functions that relate to calculations done either on the masked arrays obtained from the
# raster files or directly on the raster files for both the total and clipped raster files.

# Function calculates the mean from any raster, in array form. It excludes all nan (NOData values) from the calculation
def GetMean(array):
    mean = np.nanmean(array)
    return mean


## FUNCTIONS USED IN TOTAL WATERSHED RASTERS

# Function calculates the SDR raster, from the travel time and beta values
# Can also save the SDR raster to a .tif raster file if needed. Send "True" as save value
def CalculateSDR(tt, beta, path, GT, Proj, Save):
    SDR = np.exp(tt * beta)  # SDR operation
    SDR = np.where(SDR.mask == True, np.nan, SDR)  # Convert all masked cells to np.nan values

    if Save == True:
        # Save SDR to folder:
        path = path + "\SDR"  # Create Folder path
        SDR_name = path + "\SDR.tif"  # Create file name

        if not os.path.exists(path):  # If the SDR folder does not exist, create one
            print("Creating folder: ", path)
            os.makedirs(path)

        r_save.SaveRaster(SDR, SDR_name, GT, Proj)  # Saves array to raster

    return SDR  # Return SDR with the masked cells with 'nan' value


# Function: receives the R, C, K, P, LS rasters and multiplies them in order to get the SL value
#   If more rasters are to be used for this calculation in the future, they must be added here and in every instance of the function
def Calculate_SL(R, C, K, P, LS):
    SL = R * C * K * P * LS
    # In cells where not all rasters have values, the multiply function will place an inf value or keep a "--".
    # We must convert these to nodata "nan" values
    SL = SL.filled(np.nan)  # Convert cells which multiplied a masked cell with a value cell (value = "--") to np.nan
    # SL = np.where(np.isinf(SL), np.nan, SL) #Convert possible "inf" values to np.nan ---Uncomment if any value appears to be "inf"

    return SL  # Return Soil Loss Array


# Function calculates the Soil Yield value for each cell in the raster, by multiplying SL by SDR and the cell area
# Receives the SL and SDR rasters calculated previously and the cell area value
def Calculate_SY(SL, SDR, cell_area):
    SY = np.multiply(SL, SDR) * cell_area  # Multpiply SDR by SL to get total soil yield in each cell
    SY = np.where(np.isinf(SY), np.nan, SY)  # Remove any "inf" value, like with the SY calculations
    return SY  # return SY to main code


# Function Calculates the total SY for the entire watershed and assigns this value to every cell in a new raster
# Receives only the cell-wise SY raster and sums all non-NoData cells (excluding cells with nan value)
def Calculate_TotalSY(SY):
    sum = np.nansum(SY)  # Sum all cells with values (non-nan cells)
    SY_Tot = np.ma.where(SY >= 0, sum, np.nan)  # For all cells with values, assign the value "sum"

    return SY_Tot


# Function estimates the BL after Turowski based on the suspended load rate
def Calculate_BL(sy, dates):
    year = int(dates[0:4])
    month = int(dates[4:6])
    days_per_month = monthrange(year, month)[1]
    sec_month = days_per_month * 24 * 60 * 60
    SL = GetMean(sy)
    sl_rate = SL / sec_month *1000
    if sl_rate <= 0.394206310:
        bl_rate = 0.833 * sl_rate ** 1.34
    else:
        bl_rate = 0.437 * sl_rate ** 0.647
    bl = bl_rate / 1000 * sec_month
    return bl


##FUNCTIONS USED BY CLIPPED RASTERS##

# Functions uses gdal direct function to clip a raster to a shape. It receives the original raster to be cut, the name with which to
# save the new raster (folder location + name) and the cutting shape path (shape)
def Clip_Raster(original_raster, clipped_raster, shape):
    # Clip the original raster to the clipping shape
    # Add the "-config GDALWARP_IGNORE_BAD_CUTLINE YES" in case there is an intersection in the cutting shape for some reason.
    os.system(
        "gdalwarp -cutline " + shape + " -crop_to_cutline -dstnodata -9999 -overwrite --config GDALWARP_IGNORE_BAD_CUTLINE YES " + original_raster + " " + clipped_raster)

    # Check if output raster exists:
    r_data.Check_ClippedRaster(clipped_raster,
                               shape)  # Receives the created clipped raster and the shape name (whole path)

    # If the raster is valid, calculate the statistics
    os.system("gdalinfo -stats " + clipped_raster)


# Function calculates the mean for the clipped SL raster
# Receives the clipped SL file path, the 3D array where to save the mean value (column 0) and the row (i) and array (k)to fill
def Clipped_SLMean(SL_path, data, i, k):
    # Convert SL raster to array first:
    SL_ClippedArray = r_data.RasterToArray(SL_path)  # Using existing function, get the masked array
    data[k][i][0] = GetMean(SL_ClippedArray)  # get the array average (average SL for the raster in array form)
    return data  # return modified data array


# Function to calculate the total SY value for the clipped rasters. Since the clipped rasters have not been, it must first get the masked array. To avoid to save the SY array
# multiple times, the function calculates the Total SY raster, mean SY value and the sum SY (for the entire raster) and saves it to the data 3D array
# Receives the clipped SY file path, the 3D array where to save the mean value (column 0) and the row (i) and array (k)to fill
def Clipped_TotalSY(SY_path, data, i, k):
    # 1. Convert SY raster to array
    SY_ClippedArray = r_data.RasterToArray(SY_path)
    # 2. Calculate Total SY raster:
    Clipped_SYTotal = Calculate_TotalSY(SY_ClippedArray)
    # 3. Calculate Mean SY value for the raster and save it to the 3D array
    data[k][i][1] = GetMean(SY_ClippedArray)
    # 4. Calculate total SY value for the clipped watershed (which is the same as the mean, since all cells have the same value):
    data[k][i][2] = GetMean(Clipped_SYTotal)
    # 5. Return both the Clipped Total SY and the modified 3D data array
    return Clipped_SYTotal, data
