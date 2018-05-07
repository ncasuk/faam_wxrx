'''
FAAM Weathter Radar scan plotting.
'''

import netCDF4
import numpy as np
import os
import shutil
import sys
import tempfile

import matplotlib as mpl
import matplotlib.pyplot as plt

import scipy.interpolate
import scipy.stats

from utils import conv_polar_to_cartesian, conv_compass_to_cartesian, rotate_coord, conv_angle_to_bearing

cmap_wxrx = mpl.colors.ListedColormap(['grey',
                                       'lime',
                                       'yellow',
                                       'red',
                                       'magenta',
                                       'cyan',
                                       'white',
                                       'white'], name='cmap_wxrx')


class Scan(object):
    """WeatherRadar scan plot.

    """

    def __init__(self, nc_file, secs, imgfile=None):
        self.nc_file = nc_file
        self.Imgfile = imgfile
        self.Time = secs

    def plot(self):
        self._open_netcdf_()
        self._get_index_()
        self._get_plot_data_()
        self._plot_()
        self.savefig()
        #self._close_netcdf_()

    def _get_index_(self):
        n = 1000
        secs = self.Time
        ix_timestamp = np.min(np.where(np.array(self.ncds.variables['time'][:], dtype=int) == secs))
        vals = self.ncds.variables['scan_angle'][ix_timestamp + np.arange(-n, 0)]
        ix = np.where((vals > 79) & (vals < 80) | (vals > 279) & (vals < 280))[0]
        ix_lower = np.max(ix) - n + ix_timestamp
        vals = self.ncds.variables['scan_angle'][ix_timestamp + np.arange(0, n)]
        ix = np.where((vals > 79) & (vals < 80) | (vals > 279) & (vals < 280))[0]
        ix_upper = np.min(ix) + ix_timestamp
        self.ix_lower = ix_lower
        self.ix_upper = ix_upper

    def _open_netcdf_(self):
        self.ncds = netCDF4.Dataset(self.nc_file, 'r')

    def _close_netcdf_(self):
        self.ncds.close()

    def _get_plot_data_(self):
        tilt = self.ncds.variables['tilt'][self.ix_lower:self.ix_upper]
        scan_angle = self.ncds.variables['scan_angle'][self.ix_lower:self.ix_upper]
        self.Position = {}
        self.Position['hdg'] = np.rad2deg(scipy.stats.circmean(np.deg2rad(self.ncds.variables['hdg_gin'][self.ix_lower:self.ix_upper])))
        self.Position['lat'] = np.mean(self.ncds.variables['lat_gin'][self.ix_lower:self.ix_upper])
        self.Position['lon'] = np.mean(self.ncds.variables['lon_gin'][self.ix_lower:self.ix_upper])
        radius = self.ncds.variables['range'][self.ix_lower:self.ix_upper]
        #convert radius from nm to km
        radius = radius * 1.85
        y, x, z = conv_polar_to_cartesian(scan_angle, tilt, radius)
        refl = self.ncds.variables['reflectivity'][self.ix_lower:self.ix_upper]
        #grid_x, grid_y = np.mgrid[np.linspace(np.min(x), np.max(x), n), np.linspace(np.min(y), np.max(y), n)]
        _x_dim = (-np.max(radius), np.max(radius), 0.2)
        _y_dim = (0, np.max(radius), 0.2)
        grid_x, grid_y = np.mgrid[_x_dim[0]:_x_dim[1]:_x_dim[2],
                                  _y_dim[0]:_y_dim[1]:_y_dim[2]]
        dist = np.sqrt(grid_x**2 + grid_y**2)
        result = scipy.interpolate.griddata((x.ravel(), y.ravel()),
                                            refl.ravel(),
                                            (grid_x, grid_y),
                                            method='nearest')
        ix = dist > np.min(radius)
        result[ix] = -1
        ix = np.rad2deg(np.arctan(grid_y/np.abs(grid_x))) < 10.0
        result[ix] = -1
        self.Plot_data = {}
        self.Plot_data['x_grid'] = grid_x
        self.Plot_data['y_grid'] = grid_y
        self.Plot_data['x'] = grid_x[:, 0]
        self.Plot_data['y'] = grid_y[0, :]

        #transpose reflectivity variable
        self.Plot_data['refl'] = result.T

    def _plot_(self):
        #m.get_cmap('cmap_wxrx')
        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal')
        plt.contourf(self.Plot_data['x'],
                     self.Plot_data['y'],
                     self.Plot_data['refl'],
                     levels = np.arange(9) - 0.5,
                     cmap=cmap_wxrx)
        plt.ylim(0, np.max(self.Plot_data['y']))
        #plt.ylim(0, 75)
        plt.grid()
        plt.xlabel('left-right distance (km)')
        plt.ylabel('fwd distance (km)')
        #plt.title('Time: ' + str(self.Time))
        self.Figure = fig

    def savefig(self):
        if self.Imgfile:
            self.Figure.savefig(self.Imgfile, dpi=150)

VRT_CONTENT = """<OGRVRTDataSource>
    <OGRVRTLayer name="wxrx_data">
        <SrcDataSource>wxrx_data.csv</SrcDataSource>
        <GeometryType>wkbPoint</GeometryType>
        <LayerSRS>EPSG:4326</LayerSRS>
        <GeometryField encoding="PointFromColumns" x="Longitude" y="Latitude" z="Reflectivity"/>
    </OGRVRTLayer>
</OGRVRTDataSource>
"""

COLOR_CONTENT = """0 grey
1 green
2 yellow
3 red
4 magenta
5 cyan
5 white
6 white
"""


def to_geotiff(scan, ofilename):
        from geopy import Point
        from geopy.distance import VincentyDistance

        origin = Point(scan.Position['lat'],
                       scan.Position['lon'])  # this is the origin
        hdg = scan.Position['hdg']
        lon, lat = [], []
        for coord in zip(list(scan.Plot_data['x_grid'][:].ravel()),
                         list(scan.Plot_data['y_grid'][:].ravel())):
            dist = np.sqrt(coord[0]**2+coord[1]**2)
            angl = hdg + np.rad2deg(np.arctan(coord[0]/coord[1]))
            if not np.isfinite(angl):
                angl = 0.0
            destination = VincentyDistance(kilometers=dist).destination(origin, angl)
            lon.append(destination.longitude)
            lat.append(destination.latitude)
        tmpdir = tempfile.mkdtemp()
        data = zip(lon, lat, list(scan.Plot_data['refl'].T[:].ravel()))
        f = open(os.path.join(tmpdir, 'wxrx_data.csv'), 'w')
        f.write('Longitude,Latitude,Reflectivity\n')
        for d in data:
            f.write('%f,%f,%i\n' % (d))
        f.close()

        f = open(os.path.join(tmpdir, 'wxrx.vrt'), 'w')
        f.write(VRT_CONTENT)
        f.close()

        f = open(os.path.join(tmpdir, 'color.txt'), 'w')
        f.write(COLOR_CONTENT)
        f.close()

        os.chdir(tmpdir)
        gdal_cmd_1 = """gdal_grid -a nearest:nodata=-1 -of GTiff -ot Int16 -outsize 800 800 -l wxrx_data wxrx.vrt wxrx.tiff --config GDAL_NUM_THREADS ALL_CPUS"""
        os.system(gdal_cmd_1)
        # apply the color table to the geotiff file
        gdal_cmd_2 = """gdaldem color-relief wxrx.tiff color.txt wxrx.tiff"""
        os.system(gdal_cmd_2)

        shutil.copy(os.path.join(tmpdir, 'wxrx.tiff'), ofilename)
        return ofilename


def wxrx_plot_scan(ncfile, start_time, figoutpath, step_size=None):
    if ':' in str(start_time):
        tmp = start_time.split(':')
        start_time_secs = int(tmp[0])*3600 + int(tmp[1])*60 + int(tmp[2])
    else:
        start_time_secs = int(start_time)

    if step_size:
        ds = netCDF4.Dataset(ncfile, 'r')
        # TODO: take the maximum time from the global netCDF attribute
        start_time_secs_max = np.max(ds.variables['time'][:])
        ds.close()
        time_array = range(start_time_secs, int(np.floor(start_time_secs_max)), step_size)
    else:
        time_array = [start_time_secs]

    for secs in time_array:
        imgfilename = os.path.join(figoutpath, 'faam_wxrx_scan_%s_%i.png' % (os.path.basename(ncfile)[-7:-3], start_time_secs))
        Splot = Scan(ncfile, secs, imgfilename)
        Splot._open_netcdf_()
        Splot._get_index_()
        Splot._get_plot_data_()
        Splot._plot_()
        Splot.savefig()
        Splot._close_netcdf_()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Creates a single scan plot from FAAM weather radar netCDF.')
    parser.add_argument('ncfile', action="store", type=str,
                        help='input netCDF-file')
    parser.add_argument('timestamp', action="store", type=str,
                        help='time of interest')
    parser.add_argument('-s', action="store", type=int,
                        help='in seconds')
    parser.add_argument('figoutpath', action="store", nargs='?', type=str,
                        default=os.environ['HOME'],
                        help='path where figure will be saved')
    args = parser.parse_args()
    wxrx_plot_scan(args.ncfile, args.timestamp, args.figoutpath)
