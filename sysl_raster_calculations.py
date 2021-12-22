"""
Module contains functions that correspond to raster data reading extraction and that take the .tif raster files as
input.
"""
from config import *


# Functions to check input raster files:

def check_input_rasters(list_rasters, input_area):
    """
    Function checks if all input raster files have the same configuration, including pixel resolution, raster extension
    and projection. All rasters are compared to the RFactor_REM_db raster, since it comes from the RFactor_REM_db python
    program. If all rasters have the same configuration, the GEOTransform and projection for the Rfactor_REM_db raster
    is returned, to serve as the default data for rasters to be created.

    :param list_rasters: list, with all raster data paths to check and compare
    :param input_area: float, with the area of each pixel (in ha), which was set by the user.

    :return: 2 tuples, one for the GEOTransform and one for the projection for the RFactor_REM_db raster file.

    Note:
    * The function generates an ERROR if any of the rasters have a different extension and pixel resolution and ends the
    program.
    * If two files have the same extension and pixel resolution but different projection, a WARNING is sent and the user
    can choose, by introducing a "1" in the comment line to continue the calculations or to end the program to change
    input rasters by introducing a "0".
    * The function assumes the raster projection and GEOTransform data is in meters.
    """
    # Loop through each raster file in the input raster file list
    i = 0  # Counter to get the raster being looped through
    for file in list_rasters:
        if i == 0:  # Gets data from the first file, which is the Rfactor raster
            gt_r, proj_r = get_raster_data(file)

        else:  # Gets data for each of the other rasters, in order to compare them with the R factor values
            gt_new, proj_new = get_raster_data(file)

            # Check extent:
            if np.float32(gt_r[0]) != np.float32(gt_new[0]) and np.float32(gt_r[3]) != np.float32(gt_new[3]):
                message = "The raster " + str(os.path.basename(file)), \
                          " does not have the same extent as the other input rasters. Please check"
                sys.exit(message)
            # Check pixel size
            if np.float32(gt_r[1]) != np.float32(gt_new[1]):
                message = "The raster " + str(os.path.basename(file)), \
                          " does not have the same pixel size as the other input rasters. Please check"
                sys.exit(message)
            # Check projection
            if proj_r != proj_new:
                print("The raster " + str(os.path.basename(file)),
                      " does not have the same projection as the other input rasters.")
                message = "Press 1 if you want to continue with the program or 0 if you want" + \
                          " to check the input rasters and stop the program. \n"
                decision = input(message)
                while decision != "0" and decision != "1":  # If the user inputs an invalid option.
                    print("Invalid input '", decision, "'.")
                    decision = input(message)  # Resend message
                if decision == "0":  # If user wants to stop the program.
                    sys.exit("Exit program. Check input raster projections.")
        i += 1

    # Check pixel resolution and pixel area (assuming input rasters are in meters)
    real_area = np.float32(gt_r[1]) * np.float32(gt_r[1])
    if real_area / 10000 != input_area:  # If the calculated area in ha is different than the user input.
        message = "The user input area is incorrect. If the pixel size is in meters, the pixel area should be: " + \
                  str(real_area / 10000) + " ha."
        sys.exit(message)

    return gt_r, proj_r


def check_clipped_raster(raster_path, shape_name):
    """
    Function checks if the raster, which was clipped to a shape file, has data. If there are no valid pixel data, or all
    pixels are masked, then it means the clipping shape is not within the total watershed and thus no calculations can
    be done on it.

    :param raster_path: path of clipped raster file (including name.tif)
    :param shape_name: path of shapefile with which the raster_path raster was clipped.

    Note: function generates an ERROR if the input raster file has no valid data. Additionally, it eliminates the empty
    clipped raster and the folder generated for it.
    """
    raster_array = raster_to_array(raster_path)  # Read raster file
    # Check if all raster pixels are masked:
    if np.ma.array(raster_array).mask.all():
        # Delete file that was created and then erase the where it is located:
        os.remove(raster_path)
        folder = os.path.dirname(os.path.dirname(raster_path))
        shutil.rmtree(folder)

        # Exit message
        name = os.path.basename(shape_name)
        message = 'The shape ' + name + \
                  " falls outside of the total raster and thus generates an empty raster." + \
                  " Check the input shape file and run program again. "
        sys.exit(message)


# Functions that read en extract raster data:


def get_raster_data(raster_path):
    """
        Function extracts the GEOTransform and projection from a raster file

        :param raster_path: raster file path, including name.tif

        :return: 2 tuples, one with the GEOTransform and one with the projection
        """
    try:
        raster = gdal.Open(raster_path)  # Extract raster from path
        gt = raster.GetGeoTransform()  # Get GEOTransform Data: coordinate left upper corner, pixel size, 0, coord.
        #                                  lower right corner, 0, pixel size
        proj = raster.GetProjection()  # Get projection of raster
    except AttributeError:
        print("The input file " + raster_path + " is not a valid raster file or does not exist.")
    else:
        return gt, proj


def create_masked_array(array, no_data):
    """
        Function masks the no_data values in an input array, which contains the data values from a raster file

        :param array: np.array to mask
        :param no_data: float with value to mask in array

        :return: masked np.array
        """
    mskd_array = np.ma.array(array, mask=(array == no_data))  # Mask all NODATA values from the array
    return mskd_array


def raster_to_array(raster_path):
    """
        Function extracts raster data from input raster file and saves it to an array. This array is then masked using
        the function 'create_masked_array'.

        :param raster_path: path for .tif raster file

        :return: masked np.array (masking no data values)

        Note: since the input rasters could have different nodata values and different pixel precision, the nodata
         and the raster data are all changed to np.float32 to compare them with the same precision.
        """
    raster = gdal.Open(raster_path)  # Read raster file
    band = raster.GetRasterBand(1)  # Get raster band (the 1st one, since the inputs have only 1)
    no_data = np.float32(band.GetNoDataValue())  # Get NoData value

    array = np.float32(band.ReadAsArray())  # Save band info as array
    masked_array = create_masked_array(array, no_data)  # Create a masked array from the input data

    return masked_array


def clip_raster(original_raster, clipped_path, shape_path):
    """
    Function clips the raster to the same extents as an input shapefile and saves the clipped raster using gdalwarp.

    :param original_raster: path of raster to clip to shape extent (interpolated raster)
    :param clipped_path: file path (including extension and name) where to save the clipped raster
    :param shape_path: file path (including extension and name) where to save the clipped raster

    Note: the argument '-config GDALWARP_IGNORE_BAD_CUTLINE YES' is added to the gdal line to avoid errors due to
    intersection lines.
    """
    # Clip the original raster to the clipping shape
    os.system(
        "gdalwarp -cutline " + shape_path
        + " -crop_to_cutline -dstnodata -9999 -overwrite --config GDALWARP_IGNORE_BAD_CUTLINE YES "
        + original_raster + " " + clipped_path)

    # Check if output raster exists:
    check_clipped_raster(clipped_path, shape_path)

    # If the raster is valid, calculate the statistics
    os.system("gdalinfo -stats " + clipped_path)


def save_raster(array, output_path, gt, proj):
    """
    Function saves a np.array into a .tif raster file.

    :param array: np.array with raster data to save
    :param output_path: file path (with nam and extension) with which to save raster array
    :param gt: geotransform of resulting raster
    :param proj: projection for resulting raster
        """
    # 1: Get drivers in order to save outputs as raster .tif files
    driver = gdal.GetDriverByName("GTiff")  # Get Driver and save it to variable
    driver.Register()  # Register driver variable

    # 2: Create the raster files to save, with all the data: folder + name, number of columns (x), number of rows (y),
    # No. of bands, output data type (gdal type)
    outrs = driver.Create(output_path, xsize=array.shape[1], ysize=array.shape[0], bands=1, eType=gdal.GDT_Float32)

    # 3: Assign raster data and assaign the array to the raster
    outrs.SetGeoTransform(gt)
    outrs.SetProjection(proj)
    outband = outrs.GetRasterBand(1)
    outband.WriteArray(array)
    outband.SetNoDataValue(np.nan)
    outband.ComputeStatistics(0)

    # 4: Save raster to folder
    outband.FlushCache()
    outband = None
    outrs = None

    print("Saved raster: ", os.path.basename(output_path))
