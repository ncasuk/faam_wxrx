'''
Created on 5 Jan 2012

@author: axel
'''

import datetime
import netCDF4
import numpy as np
import os
import re
import scipy.interpolate

import faam_wxrx

#Variable definition
#long_name, description,
WXRX_VARS_DESCRIPTION = """reflectivity:long_name = Weather Condition/Reflectivity Data;
reflectivity:description = 0: No precipitation [< Z2] - black,
1: Light precipitation [Z2 to Z3] - green,
2: Moderate //precipitation [Z3 to Z4] - yellow,
3: Heavy precipitation [Z4 to Z5] - red,
4: Very heavy precipitation [> Z5] - magenta,
5: Reserved,
6: Medium turbulence,
7: Heavy turbulence;
operating_mode:long_name = Operating Mode;
operating_mode:description = 0: Standby,
1: Weather [only],
2: Map,
3: Contour,
4: Test,
5: Turbulence [only],
6: Weather & turbulence,
7: Reserved [Calibration annunciation];
mode_annunciation:units = None;
data_accept:units = None;
data_accept:description = 0: Do not accept data,
1: Accept data 1,
2: Accept data 2,
3: Accept any data;
lat_gin:long_name = Platform latitude from POS AV 510 GPS-aided Inertial Navigation unit;
lat_gin:units = degree_east;
lat_gin:description = Derived from the aircraft GIN;
lat_gin:standard_name = latitude;
lon_gin:long_name = Platform longitude from POS AV 510 GPS-aided Inertial Navigation unit;
lon_gin:units = degree_north;
lon_gin:description = Derived from the aircraft GIN;
lon_gin:standard_name = longitude;
alt_gin:long_name = Platform altitude from POS AV 510 GPS-aided Inertial Navigation unit;
alt_gin:units = meter;
alt_gin:description = Derived from the aircraft GIN;
alt_gin:standard_name = altitude;
hdg_gin:long_name = Platform heading from POSAV GPS-aided Inertial Navigation unit;
hdg_gin:units = degree;
hdg_gin:description = Derived from the aircraft GIN;
hdg_gin:standard_name = platform_yaw_angle;
ptch_gin:long_name = Platform pitch angle from POSAV GPS-aided Inertial Nav. unit (positive for nose up);
ptch_gin:units = degree;
ptch_gin:description = Derived from the aircraft GIN;
ptch_gin:standard_name = platform_pitch_angle;
tilt:units = degree;
tilt:description = tilt angle of the weather radar;
scan_angle:units = degree;
gain:long_name = Gain Data;
gain:units = db;
gain:description = Cal, Max, -5, -11, -62;
range:long_name = Beam scan range;
range:units = nm;
faults:long_name = Faults;
faults:description = No detected faults,
Transmitter/receiver Fault,
Antenna fault,
Control fault,
Altitude input fault,
Calibration fault [T-R],
Display fault,
Cooling fault;
stabilization:units = True/False;
control_accept:units = None;
control_accept:description = 0: Do not accept control,
1: IND 1 accept control,
2: IND 2 accept control,
3: All INDs accept control;
slave:units = None;"""


class Setup(object):

    def __init__(self, ncfilename):
        self.ncfilename = ncfilename
        self.ds = netCDF4.Dataset(self.ncfilename, 'w', format='NETCDF4')

        # set global attributes
        self.ds.description = 'FAAM WXRX data'
        self.ds.conventions = "CF-1.0"
        self.ds.institution = "FAAM - Facility for Airborne Atmospheric Measurements"
        self.ds.source = "FAAM BAe-146 Honeywell RDR-4B Doppler Weather Radar System"
        self.ds.references = "http://www.faam.ac.uk; http://www.faam.ac.uk/index.php/science-instruments/remote-sensing/288-doppler-radar"
        self.ds.time_interval = ""
        self.ds.title = "Doppler Weather Radar data from the FAAM BAe-146"
        self.dscreation_date = ""
        self.ds.comment = "Data from the Doppler Weather Radar data from the FAAM BAe-146. The data are not post processed in any way, but converted from a binary encoded file into a netCDF."
        self.ds.inputfiles = ""
        self.ds.softwareVersion = ""

        # dimensions
        self.ds.createDimension('time', None)
        self.ds.createDimension('bin', 512)

        self.ds.variables['bin'] = np.array(range(512))
        #WXRX_VARS_DESCRIPTION =
        WXRX_VARS = list(set(zip(*[v.split(':') for v in (re.sub('\n', '', WXRX_VARS_DESCRIPTION)).split(';')])[0]))
        WXRX_VARS = [w.strip() for w in WXRX_VARS]
        WXRX_ATTR = [v.split(':') for v in (re.sub('\n', '', WXRX_VARS_DESCRIPTION)).split(';')]

        variables = [('time', 'f8', ('time')),
                     ('bin', 'i2', ('time')),
                     ('reflectivity', 'byte', ('time', 'bin')),
                     ('operating_mode', 'byte', ('time')),
                     ('mode_annunciation', 'byte', ('time')),
                     ('data_accept', 'byte', ('time')),
                     ('lat_gin', 'f4', ('time')),
                     ('lon_gin', 'f4', ('time')),
                     ('alt_gin', 'f4', ('time')),
                     ('hdg_gin', 'f4', ('time')),
                     ('ptch_gin', 'f4', ('time')),
                     ('tilt', 'f4', ('time')),
                     ('scan_angle', 'f4', ('time')),
                     ('gain', 'i1', ('time')),
                     ('range', 'i2', ('time')),
                     ('faults', 'byte', ('time')),
                     ('stabilization', 'byte', ('time')),
                     ('control_accept', 'byte', ('time')),
                     ('slave', 'byte', ('time'))]

        for v in variables:
            tmp = self.ds.createVariable(v[0], v[1], v[2])
            for a in WXRX_ATTR:
                if a[0] == v[0]:
                    attrname, attrval = a[1].split('=')
                    attrname = attrname.strip()
                    attrval = attrval.strip()
                    tmp.setncattr(attrname, attrval)

        self.ds.sync()
        tmp = None


class Writer(object):

    def __init__(self, ncfile, wxrx_data_list):
        self.ncfile = ncfile
        self.wxrx_data_list = wxrx_data_list
        # open netCDF file in append mode
        self.ds = netCDF4.Dataset(ncfile, 'a', format='NETCDF4')

    def close(self):

        self.ds.sync()
        stimestamp = (netCDF4.num2date(self.ds.variables['time'][:].min(), self.ds.variables['time'].units)).strftime('%Y-%m-%d %H:%M:%SUTC')
        etimestamp = (netCDF4.num2date(self.ds.variables['time'][:].max(), self.ds.variables['time'].units)).strftime('%Y-%m-%d %H:%M:%SUTC')
        self.ds.time_interval = '%s - %s' % (stimestamp, etimestamp)
        self.ds.close()

    def __write_global_attributes__(self):
        self.ds.summary = "Data from the Honeywell RDR-4B doppler weather radar."
        self.ds.creation_date = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SUTC')
        self.ds.inputfiles = "Inputfiles: %s" % '; '.join([os.path.basename(i) for i in self.wxrs_data_list])
        self.ds.softwareVersion = 'Processed with Version %s' % faam_wxrx.__version__
        self.ds.variables['time'].units = self.wxrx_data_list[0].Base_time.strftime('seconds since %Y-%m-%d 00:00:00 UTC')
        self.ds.sync()
        return

    def __write_variable__(self, var_name):

        dummy = None
        for wxrx_data in self.wxrx_data_list:
            if (dummy is None):
                dummy = wxrx_data.Records[var_name]
            else:
                dummy = np.concatenate((dummy, wxrx_data.Records[var_name]))
        self.ds.variables[var_name][:] = dummy[self.good_index]
        return

    def write(self):
        """
        Write the wxrx data to netcdf file.
        """
        self.__write_global_attributes__()

        bin_val = self.ds.variables['bin']
        bin_val[:] = range(512)

        for wxrx_data in self.wxrx_data_list:
            time_stamp = [tmp * 86400. for tmp in wxrx_data.Timestamp]

        self.good_index = list(np.where(np.array(time_stamp) > 0)[0])
        self.ds.variables['time'][:] = np.array(time_stamp)[self.good_index]

        pairs = [('Reflectivity', 'reflectivity'),
                 ('Control Accept', 'control_accept'),
                 ('Slave', 'slave'),
                 ('Mode Annunciation', 'mode_annunciation'),
                 ('Faults', 'faults'),
                 ('Stabilization', 'stabilization'),
                 ('Operating Mode', 'operating_mode'),
                 ('Tilt', 'tilt'),
                 ('Gain', 'gain'),
                 ('Range', 'range'),
                 ('Data Accept', 'data_accept'),
                 ('Scan Angle', 'scan_angle')]

        for p in pairs:
            sys.stdout.write('  Writing variable  ... %s\n' % (p[1]))
            self.__write_variable__(p[1])
        return

    def merge_core_file(self, core_file):
        core_ds = netCDF4.Dataset(core_file, 'r', format='NETCDF4')
        time_array = self.ds.variables['time']

        pairs = [('hdg_gin',  'HDG_GIN'),
                 ('lon_gin',  'LON_GIN'),
                 ('lat_gin',  'LAT_GIN'),
                 ('alt_gin',  'ALT_GIN'),
                 ('ptch_gin', 'PTCH_GIN')]

        for p in pairs:
            tck = scipy.interpolate.splrep(core_ds.variables['Time'][:].ravel(), core_ds.variables[p[1]][:,0].ravel())
            self.ds.variables[p[0]][:] = scipy.interpolate.splev(time_array, tck)

        core_ds.close()
        return
