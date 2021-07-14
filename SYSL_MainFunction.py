import numpy as np
import os
import glob
import time
import re

# Import function files
import SYSL_RasterDataFunctions as r_data
import SYSL_RasterCalcFunctions as r_calc
import SYSL_SaveDataFunctions as r_save

start_time = start_time = time.time()



# ------------------------------------------------------------------------------------------------------------------ #
#-------------------------------------------------USER INPUT-------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------ #

# 1.Input constant rasters:----------------------------------------------------------------------------------------- #
# All rasters must have the same extent, cell size, no data value and, preferably, be snapped to each other. This will be checked in "SYSL_RasterDataFUnctions"
cp_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Rasters\Cp_Mean_snap.tif'  # C Factor: Cover management raster
k_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Rasters\kfac_st_snap.tif'  # K Factor: Soil Erodibility factor
ls_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Rasters\LS_V11b.tif'  # LS factor: Slope length and steepness factor
p_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Rasters\p_factor.tif'  # P Factor: Support practice factor
tt_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Rasters\traveltime_final_h_snap.tif'  # Travel time raster

# 2. Calculation constants: ----------------------------------------------------------------------------------------- #
beta = -0.5639  # Must be a negative number!
cell_area = 0.0625  # in hectares (ha)

# 3. Folder with R factor values ------------------------------------------------------------------------------------ #
#  R Factor files must have the following format: RFactor_Year_Month (_Day if needed).tif --------------------------- #
# R_folder = r'Y:\Abt1\hiwi\Oreamuno\SY_062016_082019\Calculations\Python_Programs\Results\RFactor_REM_db\CorrectedData'  # R factor: corrected precipitation factor
R_folder = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\REM_db_rain_only'


# 4. Clip surface: Can be a folder with all shape files or just 1 shape file. --------------------------------------- #
# Files should have the following name format: Catchment_NAME.shp. -------------------------------------------------- #
# If the name format is different, change corresponding lines in loop 2 (shapes) and 3 (save .txt) ------------------ #
clip_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Shape'

# 5. Folder to save all results: ------------------------------------------------------------------------------------ #
results_path = r'P:\aktiv\2018_DLR_DIRT-X\300_Modelling\310_Models\01_Erosion_model\18_SY_052016_042018\Results\Rain_only'


# -------------------------------------------------------------------------------------------------------------------#
# --------------------------------------------MAIN CODE--------------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#

# 1.Get all R raster file paths into a list: All rasters MUST BE .tif files. if not, the type of file must also be changed.
R_filenames = sorted(glob.glob(R_folder + "\*.tif"))
# print(R_filenames)

# 2. Get all shapes into a list
Clip_filenames = glob.glob(clip_path + "\*.shp")
# print(Clip_filenames)

# 3. Check input raster properties: save all raster input paths into list, including 1R factor file IN THE 1ST POSITION
#   If more input files are used, they must be added AT THE END of the list
#   If all rasters have the same data properties, the function assigns the default projection and geotransform for the total watershed rasters.
raster_list = [R_filenames[0], cp_path, k_path, ls_path, p_path, tt_path]
GT, Proj = r_data.Check_InputRasters(raster_list, cell_area)

# 4. Save each constant into an array: if more input rasters are used, add them here with a corresponding array name factor_array
cp_array = r_data.RasterToArray(cp_path)  # Array with C factor values
k_array = r_data.RasterToArray(k_path)  # Array with K factor values
p_array = r_data.RasterToArray(p_path)  # Array with P factor values
ls_array = r_data.RasterToArray(ls_path)  # Array with LS factor values
tt_array = r_data.RasterToArray(tt_path)  # Array with transport time values

# 6. Get SDR raster, which is independent of R factor and thus constant. The function also saves the SDR, if last input value is set to "True"
SDR_array = r_calc.CalculateSDR(tt_array, beta, results_path, GT, Proj, True)

# 7. Create 3D array to save the results to a .txt file and a vector to save the dates
data_summary = np.empty(((
len(Clip_filenames) + 1, len(R_filenames), 4)))  # No. Arrays: 1 for each clip + total, rows: No. of dates, columns: 4
dates_vector = np.full((len(R_filenames), 1), "", dtype=object)
# print("3D shape: ", data_summary.shape)
# print("Dates shape: ", dates_vector.shape)

# -Loop through R factor rasters-#:
i = 0  # loop for every row in the 3D array (for every measurement month)
for file in R_filenames:
    r_name = os.path.basename(file)  # Get complete name of raster being analyzed (including extension)

    # Get the index for the first number in the name, which MUST correspond to the beginning of the date YYYYMM
    index = re.search(r"\d", r_name)
    r_date = os.path.splitext(os.path.basename(r_name))[0][index.start():]  # Get the date, in YYYYMM format

    # print("Name: ", r_name)
    # print("Date: ", r_date)

    # 1. Save the masked array for the R factor raster
    R_array = r_data.RasterToArray(file)  # Extract the data from the Rfactor file into a masked array

    # 2. Create folder to save the Total watershed files. Checks if it already exists, if not it creates it
    total_path = results_path + "\\Total"
    r_data.CheckFolder(total_path)

    # 3. Calculate results for each R factor file (Soil Loss, Soil Yield, Total Soil Yield)
    SL_array = r_calc.Calculate_SL(R_array, cp_array, k_array, p_array, ls_array)  # Calculate SY for eac R Factor.
    SY_array = r_calc.Calculate_SY(SL_array, SDR_array, cell_area)  # Calculate SL
    SY_Tot_array = r_calc.Calculate_TotalSY(SY_array)  # Calculate the sum of all cells in SY
    BedL = r_calc.Calculate_BL(SY_Tot_array, r_date)


    # 4. Save the SL and SY for the entire watershed
    #   4.1. Save SL and save mean value to array
    save_SL = total_path + "\SL\SL_Banja_" + r_date + "_Total.tif"  # Assign raster pth, including name and extension
    r_save.SaveRaster(SL_array, save_SL, GT, Proj)  # Save array as raster
    data_summary[0][i][0] = r_calc.GetMean(SL_array)  # Get SL mean, and save to the 1st column of each array, row "i"

    #   4.2 Save SY and save mean value to array
    save_SY = total_path + "\SY\SY_Banja_" + r_date + ".tif"  # Assign raster pth, including name and extension
    r_save.SaveRaster(SY_array, save_SY, GT, Proj)  # Save array as raster
    data_summary[0][i][1] = r_calc.GetMean(SY_array)  # Get SY mean, and save to the 2nd column of each array, row "i"

    #   4.3 Save Total Soil Yield and save mean value to array
    save_SYTot = total_path + "\SY_Total\SYTot_Banja_" + r_date + ".tif"  # Assign raster pth, including name and extension
    r_save.SaveRaster(SY_Tot_array, save_SYTot, GT, Proj)  # Save array as raster
    data_summary[0][i][2] = r_calc.GetMean(
        SY_Tot_array)  # Get SL_tot mean, and save to the 3rd column of each array, row "i"

    # 4.4 Save Bed Load to array
    data_summary[0][i][3] = BedL

    # -Loop through Clipping Shapes (Masks)-#
    k = 1  # Loop for every array in the 3D array. Starts at 1, since array[0] is the total watershed. The clipped arrays begin at 1
    for shape in Clip_filenames:
        shape_name = os.path.splitext(os.path.basename(shape))[0][
                     10:]  # File name must be is Catchment_NAME. If not CHANGE THIS LINE

        # 1. Create Folders to Save clipped rasters:
        #   1.1 Create General folder with name of Clipping shape and check if they exist. If it doesn't exist, it is created
        save_clip = results_path + "\\" + shape_name
        r_data.CheckFolder(save_clip)

        # 2. Clip SL and SY rasters to shape and save resulting raster automatically
        #   2.1 Clip SL, save raster (in 1 same function) and save mean_SL to 3D array
        save_CLipSL = save_clip + "\\SL\SL_" + r_date + "_" + shape_name + ".tif"  # Folder and file name of clipped SL raster
        r_calc.Clip_Raster(save_SL, save_CLipSL, shape)  # Clip and save SL raster
        data_summary = r_calc.Clipped_SLMean(save_CLipSL, data_summary, i,
                                             k)  # Save mean SL in 3D array, row "i", array "k", column 0
        #   2.2 Clip SY and save raster (in 1 same function)
        save_ClipSY = save_clip + "\\SY\SY_" + r_date + "_" + shape_name + ".tif"  # Folder and file name of clipped SY raster
        r_calc.Clip_Raster(save_SY, save_ClipSY, shape)  # Clip and save SY raster

        # 3. Generate the Total SY raster and save mean SY and total SY to 3D array
        #   3.1 Get total SY clipped array and bed load, and save the SY mean, SY Total and BL to 3D array, row "i" in array "k", columns 1 and 2
        SY_Tot_array, data_summary = r_calc.Clipped_TotalSY(save_ClipSY, data_summary, i, k)
        BedL = r_calc.Calculate_BL(SY_Tot_array, r_date)
        data_summary[k][i][3] = BedL
        #   3.2 Get the Geotransform from the clipped raster, which is different from the total raster
        GT_clip, Proj_clip = r_data.GetRasterData(save_ClipSY)
        #   3.3 Save CLipped total SY array to raster:
        save_name = save_clip + "\\SY_Total\SYTot_" + r_date + "_" + shape_name + ".tif"  # Folder and file name of clipped Total SY raster
        r_save.SaveRaster(SY_Tot_array, save_name, GT_clip, Proj)  # Save Clipped SYTotal raster

        k += 1  # Add to array counter

    dates_vector[i][0] = r_date  # Save the R Factor date in a different array, in row "i"
    i += 1  # add to date (row) counter

raster_time = time.time()

print("Time to save rasters: ", time.time() - start_time)


# Loops to save the .txt files with the results summary for each array (clipped shape) in the 3D array:
for k in range(0, int(data_summary.shape[0])):
    # 1. Get the name of the array in order:
    if k == 0:  # for the first array,which is for the total raster
        file_name = total_path + "\\BanjaResults.txt"
    else:  # For each array corresponding to a clipping shape
        # Get the clipping shape name, to find the corresponding saving folder
        shape_name = os.path.splitext(os.path.basename(Clip_filenames[k - 1])[10:])[
            0]  # File name must be is Catchment_NAME. If not CHANGE THIS LINE
        file_name = results_path + "\\" + shape_name + "\\" + shape_name + ".txt"

    # 2. Save array using function
    r_save.Save_SummaryTable(data_summary, k, dates_vector, file_name)

print("Time to save summary tables: ", time.time() - raster_time)
print('Total time: ', time.time() - start_time)
