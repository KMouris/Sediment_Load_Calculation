"""
@author: María Fernanda Morales Oreamuno

Module calculates the monthly  sediment loss (SL), sediment yield (SY) and total sediment yield based on the revised
universal soil loss equation (RUSLE), using the SEDD model for SY calculations.

Procedure based on:

    Renard, K. G. (1997). Predicting soil erosion by water: a guide to conservation planning with the Revised Universal
    Soil Loss Equation (RUSLE). United States Government Printing.

    Ferro, V.; Porto, P. Sediment delivery distributed (SEDD) model. J. Hydrol. Eng. 2000, 5, 411–422.
    DOI: https://doi.org/10.1061/(ASCE)1084-0699(2000)5:4(411)

    Renard, K. et al. 1997. Predicting Soil Erosion by Water: A Guide to Conservation Planning
    with the Revised Universal Soil Loss Equation (RUSLE). s.l. : Agricultural Handbook 703, USDA-ARS, 1997

Needed information:
- See config.py file

Notes:
* Module first calculates the SL, SY and Total SY rasters for the entire extent of the input rasters (considered as
    the total watershed) and then clips them to the extent of each of the rest of the input shape files.
* Module generates a summary table with the mean SL, mean SY and total SY for each of sub-catchments, including the
    total catchment. Each summary table contains the data for each of the months within the analysis period.

"""
# Import files
from config import *
import sysl_functions as r_calc
import sysl_raster_calculations as r_data
import SYSL_SaveDataFunctions as r_save
import sysl_file_management as r_file

# -------------------------------------------------------------------------------------------------------------------#
# --------------------------------------------MAIN CODE--------------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#
start_time = start_time = time.time()

# 1.Get all R raster file paths into a list: All rasters MUST BE .tif files. if not, the type of file must also be
#   changed.
R_filenames = sorted(glob.glob(R_folder + "\*.tif"))
# print(R_filenames)

# 2. Get all shapes into a list
Clip_filenames = glob.glob(clip_path + "\*.shp")
# print(Clip_filenames)

# 3. Check input raster properties: save all raster input paths into list, including 1 R factor file
#   If more input files are used, they must be added AT THE END of the list
#   If all rasters have the same data properties, the function assigns the default projection and GEOTransform for the
#   total watershed rasters.
raster_list = [R_filenames[0], cp_path, k_path, ls_path, p_path, tt_path]
GT, Proj = r_data.Check_InputRasters(raster_list, cell_area)

# 4. Save each constant into an array: if more input rasters are used, add them here with a corresponding array name
#    factor_array
cp_array = r_data.RasterToArray(cp_path)  # Array with C factor values
k_array = r_data.RasterToArray(k_path)  # Array with K factor values
p_array = r_data.RasterToArray(p_path)  # Array with P factor values
ls_array = r_data.RasterToArray(ls_path)  # Array with LS factor values
tt_array = r_data.RasterToArray(tt_path)  # Array with transport time values

# 5. Get SDR raster, which is independent of R factor and thus constant. The function also saves the SDR, if last input
#    value is set to "True"
SDR_array = r_calc.calculate_sdr(tt_array, beta, results_path, GT, Proj, True)

# 6. Create 3D array to save the results to a .txt file and a vector to save the dates
#    Num. Arrays: 1 for each shape file + total, num. rows: months to analyze, columns: 4 (one for each result)
data_summary = np.empty((len(Clip_filenames) + 1, len(R_filenames), 4))
dates_vector = np.full((len(R_filenames), 1), "", dtype=object)
# print("3D shape: ", data_summary.shape)
# print("Dates shape: ", dates_vector.shape)

# Loop through R factor rasters ------------------------------------------------------------------------------------ #
i = 0  # loop for every row in the 3D array (for every measurement month)
for file in R_filenames:
    r_name = os.path.basename(file)  # Get complete name of raster being analyzed (including extension)

    # Get date:
    date = r_file.get_date(file)
    r_date = str(date.strftime("%Y%m"))

    # print("Name: ", r_name)
    # print("Date: ", r_date)

    # 1. Save the masked array for the R factor raster
    R_array = r_data.RasterToArray(file)  # Extract the data from the Rfactor file into a masked array

    # 2. Create folder to save the Total watershed files. Checks if it already exists, if not it creates it
    total_path = results_path + "\\Total"
    r_data.CheckFolder(total_path)

    # 3. Calculate results for each R factor file (Soil Loss, Soil Yield, Total Soil Yield)
    SL_array = r_calc.calculate_sl(R_array, cp_array, k_array, p_array, ls_array)  # Calculate SY for eac R Factor.
    SY_array = r_calc.Calculate_SY(SL_array, SDR_array, cell_area)  # Calculate SL
    SY_Tot_array = r_calc.Calculate_TotalSY(SY_array)  # Calculate the sum of all cells in SY
    BedL = r_calc.Calculate_BL(SY_Tot_array, r_date)

    # 4. Save the SL and SY for the entire watershed
    #   4.1. Save SL and save mean value to array
    save_SL = total_path + "\SL\SL_Banja_" + r_date + "_Total.tif"  # Assign raster pth, including name and extension
    r_save.SaveRaster(SL_array, save_SL, GT, Proj)  # Save array as raster
    data_summary[0][i][0] = np.nanmean(SL_array)  # Get SL mean, and save to the 1st column of each array, row "i"

    #   4.2 Save SY and save mean value to array
    save_SY = total_path + "\SY\SY_Banja_" + r_date + ".tif"  # Assign raster pth, including name and extension
    r_save.SaveRaster(SY_array, save_SY, GT, Proj)  # Save array as raster
    data_summary[0][i][1] = np.nanmean(SY_array)  # Get SY mean, and save to the 2nd column of each array, row "i"

    #   4.3 Save Total Soil Yield and save mean value to array
    save_SYTot = total_path + "\SY_Total\SYTot_Banja_" + r_date + ".tif"  # assign output file name
    r_save.SaveRaster(SY_Tot_array, save_SYTot, GT, Proj)  # Save array as raster
    data_summary[0][i][2] = np.nanmean(SY_Tot_array)  # Get SL_tot mean

    # 4.4 Save Bed Load to array
    data_summary[0][i][3] = BedL

    # Loop through Clipping Shapes (Masks) ------------------------------------------------------------------------- #
    k = 1  # Loop for every array in the 3D array. Starts at 1, since array[0] is the total watershed.
    for shape in Clip_filenames:
        shape_name = os.path.splitext(os.path.basename(shape))[0][10:]  # File name must be is Catchment_NAME.

        # 1. Create Folders to Save clipped rasters:
        #   1.1 Create General folder with name of Clipping shape and check if they exist. If it doesn't exist, create
        save_clip = results_path + "\\" + shape_name
        r_data.CheckFolder(save_clip)

        # 2. Clip SL and SY rasters to shape and save resulting raster automatically

        # 2.1 Clip SL, save raster and save mean_SL to 3D array
        save_CLipSL = save_clip + "\\SL\SL_" + r_date + "_" + shape_name + ".tif"
        r_calc.Clip_Raster(save_SL, save_CLipSL, shape)  # Clip and save SL raster
        data_summary = r_calc.Clipped_SLMean(save_CLipSL, data_summary, i, k)

        # 2.2 Clip SY and save raster
        save_ClipSY = save_clip + "\\SY\SY_" + r_date + "_" + shape_name + ".tif"
        r_calc.Clip_Raster(save_SY, save_ClipSY, shape)  # Clip and save SY raster

        # 3. Generate the Total SY raster and save mean SY and total SY to 3D array

        #  3.1 Get total SY clipped array and bed load, and save the SY mean, SY Total and BL to 3D array, row "i" in
        #  array "k", columns 1 and 2
        SY_Tot_array, data_summary = r_calc.Clipped_TotalSY(save_ClipSY, data_summary, i, k)
        BedL = r_calc.Calculate_BL(SY_Tot_array, r_date)
        data_summary[k][i][3] = BedL

        #   3.2 Get the GEOTransform from the clipped raster, which is different from the total raster
        GT_clip, Proj_clip = r_data.GetRasterData(save_ClipSY)

        #   3.3 Save Clipped total SY array to raster:
        save_name = save_clip + "\\SY_Total\SYTot_" + r_date + "_" + shape_name + ".tif"
        r_save.SaveRaster(SY_Tot_array, save_name, GT_clip, Proj)

        k += 1

    dates_vector[i][0] = r_date  # Save the R Factor date in a different array, in row "i"
    i += 1

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
