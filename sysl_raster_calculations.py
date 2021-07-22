
from config import *

#In this file the user finds the functions that relate to checking and extracting data directly from raster files

## FUNCTIONS TO CHECK INPUT DATA ##



#FUNCTION receives a list with all the inut raster file PATHS and checks all the input rasters and checks if they have the same cell size, extension and projection.
# If any raster has different data, an error is generated stating the problem and stops the calculation.
#   °All rasters are compared to the RFactor raster, which is taken as the base since, in theory, it comes from the python program *NAME* where the user stated
#       the extent wanted.
#   °In each "if" statement we transform the values to float32 so all values have the same No. of decimal values and can be comparable.
#   °For the projection, it gives the user a chance to continue with the raster without the same projection (since it has the same extent)
#       or to stop the program in order to manually modify and  check the input rasters
def Check_InputRasters(list_rasters, input_area):
    i = 0 #Counter to get the raster being looped through
    for file in list_rasters: #Go through each raster file in the input raster file list
        raster = gdal.Open(file)
        if i == 0: #Gets data from the first file, which is the Rfactor raster
            gt_R, proj_R = GetRasterData(file) # Get Geotransform Data and projection from function

        else: #Gets data for each of the other rasters, in order to compare them with the Rfactor values
            gt_new, proj_new = GetRasterData(file)  # Get Geotransform Data and projection from function for each raster file "i"

            #Check extent: Check equality between 2 rasters in terms of extent. If the extent is the same, means they are snapped
            if np.float32(gt_R[0]) != np.float32(gt_new[0]) and np.float32(gt_R[3]) != np.float32(gt_new[3]):
                message = "The raster " + str(os.path.basename(file)), " does not have the same extent as the other input rasters. Please check"
                sys.exit(message)
            #Check cell size: Check equality between 2 rasters in terms of cell size. Check only 1 of the raster cell size values, since they are both equal
            if np.float32(gt_R[1]) != np.float32(gt_new[1]):
                message = "The raster " + str(os.path.basename(file)), " does not have the same cell size as the other input rasters. Please check"
                sys.exit(message)
            #Check projection: check if the projection of raster "i" is different to the R factor projection
            if proj_R != proj_new:
                print("The raster " + str(os.path.basename(file)), " does not have the same projection as the other input rasters.")
                message = "Press 1 if you want to continue with the program or 0 if you want to check the input rasters and stop the program. \n"
                decision = input(message)
                while decision != "0" and decision != "1": #If the user inputs an invalid option.
                    print("Invalid input '", decision, "'.")
                    decision = input(message) #Resend message
                if decision == "0": #If user wants to stop the program, sys.exit stops the program
                    sys.exit("Exit program. Check input raster projections.")

        i+=1 #Increase counter to compare the next raster

    #If it exits the loop, it means that all rasters have the same data, so we can now check for raster cell area and check if it coincides with the user input
    real_area = np.float32(gt_R[1]) * np.float32(gt_R[1]) #Get real area in meters, assuming the input raster projection is in meters!!!
    if real_area/10000 != input_area: #If the calculated area in ha is different than the user input.
        message = "The user input area is incorrect. If the cell size is in meters, the cell area should be: " + str(real_area/10000) + " ha."
        sys.exit(message)

    # If function reaches this point, means all input values and rasters are ok, so we assign the GeoTransform and the Projection as the default for the total
    #watershed data. Send them back to the main code.
    return gt_R, proj_R

#Function checks if the clipped raster file has data. If there are no valid pixel data (or if the masked array masks all the cells)
#then it means that the clipping shape is not within the total watershed and thus must be checked.
#Receives the complete path to the .tif file, the name of the clipping shape and the path to the
def Check_ClippedRaster(raster_path, shape_name):
    raster_array = RasterToArray(raster_path)  # Read raster file
    if np.ma.array(raster_array).mask.all() == True: #returns true if all elements are masked
        print("path: ", raster_path)
        #Delete file that was created and then erase the folder:
        os.remove(raster_path) #Remove the .tif file
        folder = os.path.dirname(os.path.dirname(raster_path))  # Gets the path for the shape folder (which is 1 folder back)
        shutil.rmtree(folder) # Deletes folder for the entire clipped subcatchment

        #Exit message
        name = os.path.basename(shape_name)  # Gets name of the catchment (without entire path)
        message = 'The shape '+ name + " falls outside of the total raster and thus generates an empty raster. Check the input shape file and run program again. "
        sys.exit(message)


##FUNCTIONS USED FOR BOTH CLIPPED AND TOTAL RASTERS:

#Function receives 1 raster file path and extracts the Geotransform and Projection, to assign to all output rasters
def GetRasterData(raster_path):
    raster = gdal.Open(raster_path) #Extract raster from path
    gt = raster.GetGeoTransform()  #Get Geotransform Data: Coordinate left upper corner, cellsize, 0, Coord. Lower right corner, 0, cell size
    proj = raster.GetProjection()  #Get projection of raster

    return gt, proj  #Return both variables

#Function: Receives an array, obtained from a raster, and the nodata value for the given raster and generates a masked array, in which the NODATA
#values are "masked", so no calculations are done with such values
def CreateMaskedArray(array, no_data):
    mskd_array = np.ma.array(array, mask=(array == no_data)) #Mask all NODATA values from the array
    return mskd_array

#Function: Receives the path for a raster and first reads it and then converts it to an array. It then calls the function Create_MaskedData" to
# generate a Masked array from the rasters nodata value
def RasterToArray(raster_path):
    raster = gdal.Open(raster_path)  #Read raster file
    band = raster.GetRasterBand(1)   #Get raster band (the 1st one, since the inputs have only 1)
    no_data = np.float32(band.GetNoDataValue())  #Get NoData value, since all input rasters could have different values and assign a numpy type variable

    array = np.float32(band.ReadAsArray() )      #Save band info as array and assign the same data type as no_data to avoid inequalities
    masked_array = CreateMaskedArray(array, no_data)  #Create a masked array from the input data

    return masked_array


# Functions uses gdal direct function to clip a raster to a shape. It receives the original raster to be cut, the name with which to
# save the new raster (folder location + name) and the cutting shape path (shape)
def Clip_Raster(original_raster, clipped_raster, shape):
    # Clip the original raster to the clipping shape
    # Add the "-config GDALWARP_IGNORE_BAD_CUTLINE YES" in case there is an intersection in the cutting shape for some reason.
    os.system(
        "gdalwarp -cutline " + shape + " -crop_to_cutline -dstnodata -9999 -overwrite --config GDALWARP_IGNORE_BAD_CUTLINE YES " + original_raster + " " + clipped_raster)

    # Check if output raster exists:
    Check_ClippedRaster(clipped_raster,
                               shape)  # Receives the created clipped raster and the shape name (whole path)

    # If the raster is valid, calculate the statistics
    os.system("gdalinfo -stats " + clipped_raster)

#Functions receives an array to save, and the path in which to save the file. It also receies the GeoTransform and Projections of output raster
def SaveRaster(array, output_path,  GT, Proj):
    #Step 1: Get drivers in order to save outputs as raster .tif files
    driver = gdal.GetDriverByName("GTiff")  # Get Driver and save it to variable
    driver.Register()  # Register driver variable

    # #Step 2: Create the raster files to save, with all the data: folder + name, number of columns (x), number of rows (y), No. of bands, output data type (gdal type)
    outrs = driver.Create(output_path, xsize=array.shape[1], ysize=array.shape[0], bands=1, eType=gdal.GDT_Float32)

    #Step 3: Assign raster data and assaign the array to the raster
    outrs.SetGeoTransform(GT)  # assign geo transform data from the original input raster (same size)
    outrs.SetProjection(Proj)  # assign projection to raster from original input raster (same projection)
    outband = outrs.GetRasterBand(1)  # Create a band in which to input our array into
    outband.WriteArray(array)  # Read array into band
    outband.SetNoDataValue(np.nan)  # Set no data value as Numpy nan
    outband.ComputeStatistics(0) #Set the raster statistics to the output raster

    #Step 4: Save raster to folder
    outband.FlushCache()
    outband = None
    outrs = None

    print("Saved raster: ", os.path.basename(output_path))