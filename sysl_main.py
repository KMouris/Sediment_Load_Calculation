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
import sysl_raster_calculations as rc
import sysl_file_management as fm

# -------------------------------------------------------------------------------------------------------------------#
# --------------------------------------------MAIN CODE--------------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#
start_time = start_time = time.time()

# 1. Set the date ranges to analyze for:
start_date = fm.get_date(start_date)
end_date = fm.get_date(end_date)

# 2. Get all R raster .tif file paths into a list. The list is then filtered to only include the dates within the input
# data range.
R_filenames = sorted(glob.glob(R_folder + "\*.tif"))
R_filenames = fm.filter_raster_lists(R_filenames, start_date, end_date, "Rfactor")

# 3. Get all shapes into a list
clip_filenames = glob.glob(clip_path + "\*.shp")
# print(Clip_filenames)

# 4. Check input raster properties and get raster properties:
# If more input files are used, they must be added AT THE END of the list.
raster_list = [R_filenames[0], cp_path, k_path, ls_path, p_path, tt_path]
gt, proj = rc.check_input_rasters(raster_list, cell_area)

# 5. Save each constant into an array: if more input rasters are used, add them here with a corresponding array name
# factor_array
cp_array = rc.raster_to_array(cp_path)  # Array with C factor values
k_array = rc.raster_to_array(k_path)  # Array with K factor values
p_array = rc.raster_to_array(p_path)  # Array with P factor values
ls_array = rc.raster_to_array(ls_path)  # Array with LS factor values
tt_array = rc.raster_to_array(tt_path)  # Array with transport time values

# 6. Get SDR raster, which is independent of R factor and thus constant. The function also saves the SDR, if last input
# value is set to "True"
SDR_array = r_calc.calculate_sdr(tt_array, beta, results_path, gt, proj, True)

# 7. Create 3D array to save the results to a .txt file and a vector to save the dates
# Num. Arrays: 1 for each shape file + total, Num. rows: months to analyze, columns: 3 or 4, depending on results to
# calculate for
if calc_bed_load:
    result_cols = 4
else:
    result_cols = 3
data_summary = np.full((len(clip_filenames) + 1, len(R_filenames), result_cols), 0.0)
dates_vector = np.full((len(R_filenames), 1), "", dtype=object)
# print("3D shape: ", data_summary.shape)
# print("Dates shape: ", dates_vector.shape)

# Loop through R factor rasters ------------------------------------------------------------------------------------ #
i = 0  # loop for every row in the 3D array (for every measurement month)
for file in R_filenames:
    r_name = os.path.basename(file)  # Get complete name of raster being analyzed (including extension)

    # Get date:
    date = fm.get_date(file)
    r_date = str(date.strftime("%Y%m"))

    # print("Name: ", r_name)
    # print("Date: ", r_date)

    # Save the masked array for the R factor raster
    R_array = rc.raster_to_array(file)  # Extract the data from the Rfactor file into a masked array

    # Create folder to save the Total watershed files. Checks if it already exists, if not it creates it
    total_path = results_path + "\\Total"
    fm.check_folder(total_path)

    # Calculate results for each R factor file (soil Loss(SL), sediment yield (SY), total SY)
    sl_array = r_calc.calculate_sl(R_array, cp_array, k_array, p_array, ls_array)
    sy_array = r_calc.calculate_sy(sl_array, SDR_array, cell_area)
    sy_tot_array = r_calc.calculate_total_sy(sy_array)

    # Save the resulting rasters for the total watershed
    save_sl = total_path + "\SL\SL_Banja_" + r_date + "_Total.tif"  # Assign raster pth, including name and extension
    rc.save_raster(sl_array, save_sl, gt, proj)  # Save array as raster
    data_summary[0][i][0] = np.nanmean(sl_array)  # Get SL mean, and save to the 1st column of each array, row "i"

    save_sy = total_path + "\SY\SY_Banja_" + r_date + ".tif"  # Assign raster pth, including name and extension
    rc.save_raster(sy_array, save_sy, gt, proj)  # Save array as raster
    data_summary[0][i][1] = np.nanmean(sy_array)  # Get SY mean, and save to the 2nd column of each array, row "i"

    save_sy_tot = total_path + "\SY_Total\SYTot_Banja_" + r_date + ".tif"  # assign output file name
    rc.save_raster(sy_tot_array, save_sy_tot, gt, proj)  # Save array as raster
    data_summary[0][i][2] = np.nanmean(sy_tot_array)  # Get SL_tot mean

    # Calculate bed load
    if calc_bed_load:
        bedL = r_calc.calculate_bl(sy_tot_array, r_date)
        data_summary[0][i][3] = bedL

    # Loop through Clipping Shapes (Masks) ------------------------------------------------------------------------- #
    k = 1  # Loop for every array in the 3D array. Starts at 1, since array[0] is the total watershed.
    for shape in clip_filenames:
        shape_name = os.path.splitext(os.path.basename(shape))[0][10:]  # File name must be is Catchment_NAME.

        # Create folders to save clipped rasters:
        save_path = results_path + "\\" + shape_name
        fm.check_folder(save_path)

        # Clip SL and SY rasters to shape and save resulting raster automatically
        save_clip_sl = save_path + "\\SL\SL_" + r_date + "_" + shape_name + ".tif"
        rc.clip_raster(save_sl, save_clip_sl, shape)  # Clip and save SL raster
        data_summary = r_calc.clipped_sl_mean(save_clip_sl, data_summary, i, k)

        save_clip_sy = save_path + "\\SY\SY_" + r_date + "_" + shape_name + ".tif"
        rc.clip_raster(save_sy, save_clip_sy, shape)  # Clip and save SY raster

        # Generate the Total SY raster and save mean SY and total SY to 3D array
        sy_tot_array_clip, data_summary = r_calc.clipped_sy(save_clip_sy, data_summary, i, k)

        # Calculate bed load
        if calc_bed_load:
            bedL = r_calc.calculate_bl(sy_tot_array_clip, r_date)
            data_summary[k][i][3] = bedL

        # Get the GEOTransform from the clipped raster, which is different from the total raster
        gt_clip, proj_clip = rc.get_raster_data(save_clip_sy)

        # Save Clipped total SY array to raster:
        save_name = save_path + "\\SY_Total\SYTot_" + r_date + "_" + shape_name + ".tif"
        rc.save_raster(sy_tot_array_clip, save_name, gt_clip, proj_clip)

        k += 1

    dates_vector[i][0] = r_date  # Save the R Factor date in a different array, in row "i"
    i += 1

raster_time = time.time()

print("Time to save rasters: ", time.time() - start_time)

# Loops to save the .txt files with the results summary for each array (clipped shape) in the 3D array:
for k in range(0, int(data_summary.shape[0])):
    # 1. Get the name of the array in order:
    if k == 0:
        file_name = total_path + "\\BanjaResults.txt"
    else:  # for catchments, the file name must be is Catchment_NAME.
        shape_name = os.path.splitext(os.path.basename(clip_filenames[k - 1])[10:])[0]
        file_name = results_path + "\\" + shape_name + "\\" + shape_name + ".txt"

    # 2. Save array using function
    fm.save_summary_table(data_summary, k, dates_vector, file_name)

print("Time to save summary tables: ", time.time() - raster_time)
print('Total time: ', time.time() - start_time)
