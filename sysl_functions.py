"""
@author: Kilian Mouris and Maria Fernanda Morales Oreamuno

Module contains functions that relate to the calculations on either masked or unmasked np.arrays, which correspond to
the input raster data.

Functions included in this module directly calculate the sediment loss, sediment yield and total sediment yield for each
sub-catchment.

The equations in this module, corresponding to the calculation of the SY and SL are based on the following papers:

* SDR and SY:
    Ferro, V.; Porto, P. Sediment delivery distributed (SEDD) model. J. Hydrol. Eng. 2000, 5, 411–422.
        DOI: https://doi.org/10.1061/(ASCE)1084-0699(2000)5:4(411)
    Fernandez, C., Wu, J. Q., McCool, D. K., & Stöckle, C. O. (2003). Estimating water erosion and sediment yield with
        GIS, RUSLE, and SEDD. Journal of soil and Water Conservation, 58(3), 128-136.

* Sediment loss: Renard, K. et al. 1997. Predicting Soil Erosion by Water: A Guide to Conservation Planning
                with the Revised Universal Soil Loss Equation (RUSLE). s.l. : Agricultural Handbook 703, USDA-ARS, 1997

* Bed load: Turowski, J. M., Rickenmann, D., & Dadson, S. J. (2010). The partitioning of the total sediment load of a
            river into suspended load and bedload: a review of empirical data. Sedimentology, 57(4), 1126-1146.
"""

from config import *
import SYSL_SaveDataFunctions as r_save
import sysl_raster_calculations as r_data


# Functions for total watershed rasters:

def calculate_sdr(tt, beta, path, GT, Proj, Save):
    """
    Function calculates the sediment delivery ratio (SDR) data for each cell, based on the travel time data and beta
    value. The equations are based on the SEDD model by Ferro and Porto (2000)

    Args:
    :param tt: np.array with data from travel time raster
    :param beta: float value for beta, which was obtained from calibration. Value must be negative.
    :param path: file path (including name.tif) with which to save the SDR data values.
    :param GT: tuple with GEOTransform data with which to save resulting raster
    :param Proj: tuple with projection data with which to save the resulting raster
    :param Save: boolean, when True saves the SDR data to a .tif raster.

    :return: np.array with SDR values
    """
    sdr = np.exp(tt * beta)  # SDR operation
    sdr = np.where(sdr.mask == True, np.nan, sdr)  # Convert all masked cells to np.nan values

    if Save:
        # Save SDR to folder:
        path = path + "\SDR"  # Create Folder path
        sdr_name = path + "\SDR.tif"  # Create file name

        if not os.path.exists(path):  # If the SDR folder does not exist, create one
            print("Creating folder: ", path)
            os.makedirs(path)

        r_data.SaveRaster(sdr, sdr_name, GT, Proj)  # Saves array to raster

    return sdr  # Return SDR with the masked cells with 'nan' value


def calculate_sl(R, C, K, P, LS):
    """
    Function calculates soil loss (ton/ha*month) based on the RUSLE model by Renard et al (1997)

    Args:
    :param R: np.array with monthly R(ain) factor values
    :param C: np.array with land C(over) factor values
    :param K: np.array with soil erodibility factor
    :param P: np.array with support P(ractice) factor
    :param LS: np.array with L(ength) and S(lope) factor

    :return: np.array with sediment loss values

    Note: If more values are to be added to the equation in the future, they must be added as an additional argument to
        the function.
    """
    sl = R * C * K * P * LS

    # Convert masked cells to np.nan values
    sl = sl.filled(np.nan)  # Convert cells which multiplied a masked cell with a value cell (value = "--") to np.nan

    # Convert possible "inf" values to np.nan
    # SL = np.where(np.isinf(SL), np.nan, SL)  ---Uncomment if any value appears to be "inf"

    return sl


def calculate_sy(SL, SDR, cell_area):
    """
    Function calculates the sediment yield (ton/month) for each cell in the input rasters.

    Args:
    :param SL: np.array with soil loss data
    :param SDR: np.array with sediment delivery ratio values
    :param cell_area: float with the area of each cell, in ha.

    :return: np.array with sediment yield values
    """
    sy = np.multiply(SL, SDR) * cell_area
    sy = np.where(np.isinf(sy), np.nan, sy)  # Convert 'inf' and masked cells to np.nan

    return sy


def calculate_total_sy(SY):
    """
    Function calculates the total sediment yield for an input SY raster, by adding all value cells (excluding np.nan
    cells). Generates an np.array where each value cell has the same value, equivalent to the total SY value.

    Args:
    :param SY: np.array with sediment yield data values

    :return: np.array with each cell containing the total SY value
    """
    sum_sy = np.nansum(SY)
    sy_tot = np.ma.where(SY >= 0, sum_sy, np.nan)  # For all cells with values, assign the value "sum"

    return sy_tot


def calculate_bl(sy, dates):
    """
    Function calculates the bed load (BL) after Turowski et al (2010) based on the suspended load rate

    Args:
    :param sy: np.array with sediment yield values
    :param dates: string with date in format YYYYMM

    :return: np.array with bed load values
    """
    # Get year and month
    year = int(dates[0:4])
    month = int(dates[4:6])
    days_per_month = monthrange(year, month)[1]
    sec_month = days_per_month * 24 * 60 * 60

    sl = np.nanmean(sy)
    sl_rate = sl / sec_month * 1000

    if sl_rate <= 0.394206310:
        bl_rate = 0.833 * sl_rate ** 1.34
    else:
        bl_rate = 0.437 * sl_rate ** 0.647
    bl = bl_rate / 1000 * sec_month

    return bl


# Function calculates the mean for the clipped SL raster

def clipped_sl_mean(SL_path, data, i, k):
    """
    Function calculates the mean for the clipped soil loss (SL) raster data

    Args:
    :param SL_path: path for the clipped soil loss raster
    :param data: 3D np.array where the summary results for the given watershed are to be stored
    :param i: int with the row value to fill
    :param k: int with the array (in the 3D array) to be filled

    :return: modified 'data' 3D np.array, which will include the mean SL value for the given date (row i)
    """
    # Convert SL raster to array first:
    sl_clipped_array = r_data.RasterToArray(SL_path)  # Get the masked array
    data[k][i][0] = np.nanmean(sl_clipped_array)      # get the array average

    return data


def clipped_sy(SY_path, data, i, k):
    """
    Function calculates the mean and total sediment yield (SY) for a given clipped raster and saved it to a 3D array,
    which contains the summary data for the given watershed.

    Args:
    :param SY_path: path of clipped SY raster to extract data from
    :param data: 3D np.array where the summary results for the given watershed are to be stored
    :param i: int with the row value to fill
    :param k: int with the array (in the 3D array) to be filled

    :return: modified 'data' 3D np.array, which will include the mean SY and total SY values for the given date (row i)
            and the clipped SY raster
    """
    # 1. Convert SY raster to array
    sy_clipped_array = r_data.RasterToArray(SY_path)
    # 2. Calculate Total SY raster:
    clipped_sy_total = calculate_total_sy(sy_clipped_array)
    # 3. Calculate Mean SY value for the raster and save it to the 3D array
    data[k][i][1] = np.nanmean(sy_clipped_array)
    # 4. Calculate total SY value for the clipped watershed
    # (which is the same as the mean, since all cells have the same value):
    data[k][i][2] = np.nanmean(clipped_sy_total)

    return clipped_sy_total, data