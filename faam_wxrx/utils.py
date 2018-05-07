'''
Collection of short functions that are called by other scripts in faam_wxrx
project.

'''

import datetime
import numpy as np
import os

from matplotlib.dates import date2num, num2date

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_base_time(wxrx_log_file):
    ifile = open(wxrx_log_file, 'r')
    lines = ifile.readlines()
    ifile.close()
    line = lines[1]
    base_time = datetime.datetime.strptime((line.split('Logging started:')[1]).strip(), TIME_FORMAT + '.%f')
    return base_time


def read_log_file(log_file):
    """Reads in the log file that is created by
    filesizeLogger.pyw script.

    """
    f = open(log_file, 'r')
    log = f.readlines()
    f.close()
    timestamp, file_size, file_name = [], [], []
    # TODO: this should use np.general read in function
    for line in log:
        if not line.startswith('#'):
            tmp = line.split(',')
            timestamp.append(date2num(datetime.datetime.strptime(tmp[0], TIME_FORMAT)))
            file_size.append(float(tmp[1]))
            file_name.append(str.strip(tmp[2]))
    return (np.array(timestamp), np.array(file_size), np.array(file_name))


def get_wxrx_tmp_filelist(log_file):
    """Get the set of temporary weather radar files.

    """
    _SIZE_LIMIT = 2485200   #equals ~60 seconds
    time_stamp_arr, file_size_arr, file_name_arr = read_log_file(log_file)
    # need to keep the order
    tmp_file_list = []
    [tmp_file_list.append(fn) for fn in list(file_name_arr) if fn not in tmp_file_list]

    checked_tmp_file_list = []
    for tmp_file in tmp_file_list:
        if not os.path.exists(os.path.join(os.path.dirname(log_file), tmp_file)):
            sys.stdout.write('Skipping ... %s. File does not exist.\n' % (tmp_file))
            continue
        elif os.stat(os.path.join(os.path.dirname(log_file), tmp_file)).st_size < _SIZE_LIMIT:
            sys.stdout.write('Skipping ... %s. File is too small.\n' % (tmp_file))
            continue
        else:
            checked_tmp_file_list.append(tmp_file)
    return checked_tmp_file_list


def time_sync(s_size_index, file_name, timestamp_array, file_size_array, file_name_array):
    # TODO: needs serious speed improvement
    # TODO: should use the np.interp method
    # filter the records. Only use those records that agree with the file name.
    # A single log file can log the size of several weather radar tmp-files
    filter_index = np.where(file_name_array == file_name)
    flt_timestamp_array = timestamp_array[filter_index]
    flt_file_size_array = file_size_array[filter_index]
    flt_file_name_array = file_name_array[filter_index]
    # calculate the time using the timestamps before and after the submitted one using interpolation
    try:
        ix1 = np.max(np.where(flt_file_size_array < s_size_index))
        ix2 = np.min(np.where(flt_file_size_array > s_size_index))
        ratio = (s_size_index - flt_file_size_array[ix1]) / (flt_file_size_array[ix2] - flt_file_size_array[ix1])
        timestamp = ratio * (flt_timestamp_array[ix2] - flt_timestamp_array[ix1]) + flt_timestamp_array[ix1]
        return num2date(timestamp)
    except:
        return None


def add_timestamp(wxrx_data, log_file):
    base_time = get_base_time(log_file)
    wxrx_data.Base_time = base_time
    wxrx_data.Timestamp = []
    timestamp_array, file_size_array, file_name_array = read_log_file(log_file)
    # convert units to Bits
    file_size_array = file_size_array * 8.
    fname = os.path.basename(wxrx_data.Filename)
    # TODO: try to avoid loop
    for size in wxrx_data.sIndexList:
        ts = time_sync(size, fname, timestamp_array, file_size_array, file_name_array)
        if ts != None:
            wxrx_data.Timestamp.append(date2num(ts) - np.floor(date2num(base_time)))
        else:
            wxrx_data.Timestamp.append(-9999)


def conv_angle_to_bearing(angle):
    result = np.mod(450-angle, 360)
    return result


def conv_compass_to_cartesian(angle):
    """The scan_angle of the weather radar is given in compass
    units and needs to be converted to cartesian before calculating
    xyz coordinates.

    """
    angle = np.array(angle)
    angle[angle > 360] = angle[angle > 360] - 360.
    angle[angle <= 90] = angle[angle <= 90]*(-1.) + 90.
    angle[angle > 90] = angle[angle > 90]*(-1.) + 450.
    return angle


def conv_polar_to_cartesian(scan_angle, tilt, rng):
    """Converts from scan_angle, tilt and range measurements into
    xyz coordinates with reference to the aircraft nose, where the
    radar is located.
    :param float scan_angle: scan angle (deg)
    :param float tilt: tilt angle of the radar dish (deg)
    :param float rng: range setting of weather radar (km)
    """
    n = len(tilt)
    range_arr = np.tile(np.linspace(0, 1, 512), n) * np.repeat(rng, 512)
    # forward distance see: http://en.wikipedia.org/wiki/Trigonometry
    x = range_arr * np.repeat(np.sin(np.deg2rad(90.0-tilt)) * np.cos(np.deg2rad(scan_angle)), 512)
    # left-right distance see: http://en.wikipedia.org/wiki/Trigonometry
    y = range_arr * np.repeat(np.sin(np.deg2rad(90.0-tilt)) * np.sin(np.deg2rad(scan_angle)), 512)
    # up-down distance
    z = range_arr * np.repeat(np.cos(np.deg2rad(90.0-tilt)), 512)
    x, y, z = x.reshape(n, 512), y.reshape(n, 512), z.reshape(n, 512)
    return (x, y, z)


def rotate_coord(x, y, angle):
    """coordinate rotation around an angle in a cartesian coordinate system.

    :param float x: x-coordinate
    :param float y: y-coordinate
    :param float angle: rotation angle in a cartesian coordinate system

    """
    x = float(x)
    y = float(y)
    angle = float(angle)
    x_rot = x * np.cos(np.deg2rad(angle)) + y * np.sin(np.deg2rad(angle))
    y_rot = -x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    return(x_rot, y_rot)
