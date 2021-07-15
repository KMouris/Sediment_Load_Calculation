
from config import *


#IN this file, the user finds the functions that save either raster files or the summary tables as .txt format.

##FUNCTIONS TO SAVE THE RESUTS:

#Function saves the summary table for the given shape "k" to a .txt file. The file summarizes the Mean SL, mean SY and total SY for each month-date combination
#Receives the 3D array, the array to sake "k", the array with the dates in column form, and the save directory
def Save_SummaryTable(TDA, k, dates, save_path):
    # 1. Extract the "k" array from the 3D array and convert it to a 2D array
    data = TDA[k,:,:] #Save current array "k" as a single 2D matrix
    data = np.reshape(data,(int(TDA.shape[1]),int(TDA.shape[2]))) #reshape m as 2D matrix, since we already removed all other arrays that made it a 3D array

    #2. Generate individual Data Frames
    # Set data column names
    columns = ["Mean Soil Loss [Ton/Ha*Month]", "Mean Soil Yield [Ton/month]", 'Total Soil Yield [ton/month]', 'Bed Load [ton/month]']
    column_date = ['Date']
    #   2.1 Generate Data Frame with data values
    df = pd.DataFrame(data=data, index=None, columns=columns)
    #   2.2 Generate Data Frame with dates:
    df_dates = pd.DataFrame(data=dates, index=None, columns=column_date)
    #   2.3 Generate Final Table by joining Dates and the value data frames:
    Results = pd.concat([df_dates, df], axis=1)

    #3. Save the final Data frame to a .txt file:
    Results.to_csv(save_path, index=False, sep='\t', na_rep="")
    print("Summary table saved: ", save_path)

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