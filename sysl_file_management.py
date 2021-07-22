"""
@author: Maria Fernanda Morales Oreamuno


Module contains functions that reads and create files and folders, including reading file names and saving files other
than raster files (e.g. .txt files).
"""

from config import *


def get_date(file_path):
    """
    Function extracts the date from the input file/folder name. The date should be in YYYYMM, YYYYMMDD, or YYYYMMDD0HH
    format

    Parameters: --------
    :param file_path: file or folder path

    :return: file date in datetime format

    If an unsupported date format is found, the function will generate an error and exit the program.
    """
    file_name = os.path.basename(file_path)  # Get file name (which should contain the date)
    digits = ''.join(re.findall(r'\d+', file_name))  # Combine all digits to a string (removes any integer)

    if len(digits) == 6:  # Either MMYYYY or YYYYMM
        if int(digits[0:2]) > 12:  # YYYYMM format
            try:
                # print(" Date in YYYYMM format")
                date = datetime.datetime.strptime(digits, '%Y%m')
            except ValueError:
                sys.exit("Wrong input date format.")
        else:  # MMYYYY format
            try:
                # print("date in MMYYYY format")
                date = datetime.datetime.strptime(digits, '%m%Y')
            except ValueError:
                sys.exit("Wrong input date format.")
    elif len(digits) == 4:  # Should be YY_MM
        # print("Date format in YYMM")
        try:
            date = datetime.datetime.strptime(digits, '%y%m')
        except ValueError:
            sys.exit("Wrong input date format in input file {}.".format(file_path))
    elif len(digits) == 8:  # YYYYMMDD format:
        # print("Date format in YYYYMMDD")
        try:
            date = datetime.datetime.strptime(digits, '%Y%m%d')
        except ValueError:
            sys.exit("Wrong input date format in input file {}.".format(file_path))
    elif len(digits) == 10:  # YYYYMMDDHH
        # print("Date format in YYYYMMDD_HH")
        try:
            date = datetime.datetime.strptime(digits, '%Y%m%d%H')
        except ValueError:
            sys.exit("Wrong input date format in input file {}.".format(file_path))
    elif len(digits) == 11:  # YYYYMMDD0HH
        # print("Date format in YYYYMMDD_0HH")
        try:
            date = datetime.datetime.strptime(digits, '%Y%m%d0%H')
        except ValueError:
            sys.exit("Wrong input date format in input file {}.".format(file_path))
    else:
        sys.exit("Check input date format. It must be in either YYYYMM, MMYYYY or YYMM.")

    return date


def check_folder(path):
    """
    Function checks if a folder, in which the data for a given watershed will be saved, exists and, if it doesn't, it
     creates it, along with the sub-folders in which to save the soil loss (SL) sediment yield (SY) and total SY.

     Args:
    :param path: path of folder to check for

    :return: ---
    """
    if not os.path.exists(path):
        print("Creating folder: ", path)
        os.makedirs(path)
        os.makedirs(path+"\\SL")
        os.makedirs(path + "\\SY")
        os.makedirs(path + "\\SY_Total")


def save_summary_table(TDA, k, dates, save_path):
    """
    Function saves the data from a numpy array into a .txt file. The data in the np.array corresponds to the summary
    data (mean SL, mean SY, total SY, and bed load (optional) for each month.

    Args:
    :param TDA: 3D np.array
    :param k: the array from the 3D array to save for (which corresponds to a given watershed)
    :param dates: np.array with the date for each analyzed month (in string YYYYMM format)
    :param save_path: file path (including name.txt) with which to save resulting tabe

    :return: ---

    Note: The function first transforms the 3D np.array to a 2D array, and then converts it to a data frame and joins it
    with the df for the dates. It then saves the combined data frame to a .txt file
    """
    # 1. Extract the "k" array from the 3D array and convert it to a 2D array
    data = TDA[k, :, :]
    data = np.reshape(data, (int(TDA.shape[1]), int(TDA.shape[2])))

    # 2. Generate individual Data Frames
    columns = ["Mean Soil Loss [ton/ha*month]", "Mean Sediment Yield [ton/month]", 'Total Sediment Yield [ton/month]',
               'Bed Load [ton/month]']
    column_date = ['Date']
    #   2.1 Generate Data Frame with data values
    df = pd.DataFrame(data=data, index=None, columns=columns)
    #   2.2 Generate Data Frame with dates:
    df_dates = pd.DataFrame(data=dates, index=None, columns=column_date)
    #   2.3 Generate Final Table by joining Dates and the value data frames:
    results = pd.concat([df_dates, df], axis=1)

    # 3. Save the final Data frame to a .txt file:
    results.to_csv(save_path, index=False, sep='\t', na_rep="")
    print("Summary table saved: ", save_path)
