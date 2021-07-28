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

    Args:
    :param file_path: file or folder path, string or integer number, from which the date will be extracted

    :return: file/string date in datetime format

    If an unsupported date format is found, the function will generate an error and exit the program.
    """
    if not isinstance(file_path, str):
        file_path = str(file_path)
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


def filter_raster_lists(raster_list, date1, date2, file_name):
    """
    Function filters input list to only include files with within a given data range (date1-date2; analysis range).

    Args:
    :param raster_list: list with file paths, whose names contain the date in either YYYYMM or YYMM format
    :param date1: analysis start date (in datetime format)
    :param date2: analysis end date (in datetime format)
    :param file_name: string with the name of the input raster file type generating the error

    :return: filtered list, without the files that are not within the analysis date range.

    Note: If there are no files for the given date range (new_list is empty) or any month is missing, function throws
    an error and exits the program.
    """
    new_list = []
    for elem in raster_list:
        date = get_date(elem)
        if date1 <= date <= date2:
            new_list.append(elem)

    if len(new_list) == 0:
        message = "ERROR: There are no {} input raster files corresponding to the input date range. Check input.".format(file_name)
        sys.exit(message)

    # Check if there is one input file per month to analyze
    n_months = (date2.year - date1.year) * 12 + date2.month - date1.month + 1  # months to analyze
    n_days = (date2.replace(day=calendar.monthrange(date2.year, date2.month)[1]) - date1).days + 1
    n_hours = n_days * 24
    if not n_months == len(new_list) and not n_days == len(new_list) and not n_hours == len(new_list):
        message = "ERROR: One or more of the raster files between {} and {} is missing from {} input files.".format(
            str(date1.strftime('%Y%m')), str(date2.strftime('%Y%m')), file_name) + \
                                         " Check input rasters for missing date(s) or check date range."
        sys.exit(message)

    return new_list


def save_summary_table(TDA, k, dates, save_path):
    """
    Function saves the data from a numpy array into a .txt file. The data in the np.array corresponds to the summary
    data (mean SL, mean SY, total SY, and bed load (optional) for each month.

    Args:
    :param TDA: 3D np.array
    :param k: the array from the 3D array to save for (which corresponds to a given watershed)
    :param dates: np.array with the date for each analyzed month (in string YYYYMM format)
    :param save_path: file path (including name.txt) with which to save resulting table

    Note: The function first transforms the 3D np.array to a 2D array, and then converts it to a data frame and joins it
    with the df for the dates. It then saves the combined data frame to a .txt file
    """
    # Extract the "k" array from the 3D array and convert it to a 2D array
    data = TDA[k, :, :]
    data = np.reshape(data, (int(TDA.shape[1]), int(TDA.shape[2])))

    # Set column names:
    column_date = ['Date']
    if calc_bed_load:
        columns = ["Mean Soil Loss [ton/ha*month]", "Mean Sediment Yield [ton/month]",
                   'Total Sediment Yield [ton/month]',
                   'Bed Load [ton/month]']
    else:
        columns = ["Mean Soil Loss [ton/ha*month]", "Mean Sediment Yield [ton/month]",
                   'Total Sediment Yield [ton/month]']

    # Generate data frame with data values
    df = pd.DataFrame(data=data, index=None, columns=columns)
    # Generate data frame with dates:
    df_dates = pd.DataFrame(data=dates, index=None, columns=column_date)
    # Generate final df by joining dates and the value data frames:
    results = pd.concat([df_dates, df], axis=1)

    # Save the final Data frame to a .txt file:
    results.to_csv(save_path, index=False, sep='\t', na_rep="")
    print("Summary table saved: ", save_path)
