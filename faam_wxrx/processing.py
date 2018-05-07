#!/usr/bin/python

"""
Creates a weather radar netCDF file from the raw/tmp
weather radar files and the core_data netCDF file.

"""

import sys
import datetime
import os
import re
import numpy as np

from Arinc708 import Arinc708

from Reader import Reader
from Writer import Writer, Setup
from utils import get_wxrx_tmp_filelist, add_timestamp
from .wxrx_plot_overview import Overview
from .utils import get_base_time

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def _get_log_file_(ROOT_PATH, fid):
    if os.path.exists(os.path.join(ROOT_PATH, fid + '.log')):
        WXRX_LOG_FILE = os.path.join(ROOT_PATH, fid + '.log')
    elif os.path.exists(os.path.join(ROOT_PATH, str.upper(fid) + '.log')):
        WXRX_LOG_FILE = os.path.join(ROOT_PATH, str.upper(fid) + '.log')
    else:
        sys.stdout.write('No weather radar log file available. Leaving ...\n')
        sys.exit(2)
    return WXRX_LOG_FILE


def process(ROOT_PATH, CORE_FILE, fid, rev):

    WXRX_LOG_FILE = _get_log_file_(ROOT_PATH, fid)

    #set BASE_TIME from the 2nd line (logging start) in the WXRX_LOG_FILE
    BASE_TIME = get_base_time(WXRX_LOG_FILE)
    WXRX_NETCDF_FILENAME = 'weather-radar_faam_%s_r%s_%s.nc' % (datetime.datetime.strftime(BASE_TIME, '%Y%m%d'), str(rev), str.lower(fid))

    if os.path.exists(os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME)):
        sys.stdout.write('weather radar netCDF\n')
        sys.stdout.write('  ... %s\n' %
                         os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME))
        sys.stdout.write('already exists! Exiting ...\n')
        sys.exit(2)

    # get unique valid wxrx-tmp-filelist from log file
    wxrx_file_list = get_wxrx_tmp_filelist(WXRX_LOG_FILE)
    # Calculate total size of tmp-wxrx-data
    MAX_SIZE = np.max([os.stat(os.path.join(ROOT_PATH, wxrx_file)).st_size for wxrx_file in wxrx_file_list])
    MAXIMUM_NUMBER_OF_RECORDS = (MAX_SIZE*8/1744) + 1
    wxrx_data_list = []

    _RECS = np.zeros(MAXIMUM_NUMBER_OF_RECORDS, dtype = [('label',             np.str_, 4),
                                                         ('control_accept',    np.byte),
                                                         ('slave',             np.byte),
                                                         ('mode_annunciation', np.byte),
                                                         ('faults',            np.byte),
                                                         ('stabilization',     np.byte),
                                                         ('operating_mode',    np.byte),
                                                         ('tilt',              np.float),
                                                         ('gain',              np.float),
                                                         ('range',             np.int16),
                                                         ('data_accept',       np.byte),
                                                         ('scan_angle',        np.float),
                                                         ('reflectivity',      np.byte, (512,))])

    A708 = Arinc708()

    for wxrx_file in wxrx_file_list:
        sys.stdout.write('Reading ... %s\n' % (wxrx_file))
        # TODO: adding progressbar to see where we are including ETA
        wxrx_data = Reader(os.path.join(ROOT_PATH, wxrx_file))
        wxrx_data.parse()
        sys.stdout.write(wxrx_data)
        ix = []
        for i in range(len(wxrx_data.Buswords)):
            try:
                _RECS[i] = A708.parse(wxrx_data.Buswords[i])
                ix.append(i)
            except:
                pass

        wxrx_data.sIndexList = list(np.array(wxrx_data.sIndexList)[ix])

        add_timestamp(wxrx_data, WXRX_LOG_FILE)
        wxrx_data.Records = _RECS[ix]
        wxrx_data_list.append(wxrx_data)
        # Delete to save memory
        del(wxrx_data)


    # TODO
    _s = Setup(os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME))
    sys.stdout.write('Creating empty netCDF ...\n')

    sys.stdout.write('Writing data to ... %s\n' % (os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME)))
    wxrx_nc_writer = Writer(os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME), wxrx_data_list)
    wxrx_nc_writer.write()
    sys.stdout.write('Merging faam_core data ... %s\n' % (CORE_FILE))
    # TODO
    wxrx_nc_writer.merge_core_file(CORE_FILE)
    wxrx_nc_writer.close()

    # create overview figure
    Overview(os.path.join(ROOT_PATH, WXRX_NETCDF_FILENAME),
             os.path.join(ROOT_PATH,
                          '%s_%s_wxrx_overview.png' % (fid, datetime.datetime.strftime(BASE_TIME, '%Y%m%d'))))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_path', action="store", type=str,
                        help='directory that contains the raw/tmp weather radar data files')
    parser.add_argument('faam_core_netcdf', action="store", type=str,
                        help='core netCDF file, that is used to merge positional information')
    parser.add_argument('-r, --revison', dest='revision', action="store",
                        type=int, default=0,
                        help='revision number for output netcdf file [default: 0]')
    args = parser.parse_args()

    fid = re.findall('[b,B,c,C]\d{3}', os.path.basename(args.faam_core_netcdf))[0]
    process(args.data_path, args.faam_core_netcdf, fid, args.revision)
