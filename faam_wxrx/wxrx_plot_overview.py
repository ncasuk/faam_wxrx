#!/usr/bin/python

"""
Creates an Overview plot from the Weather Radar netcdf file.

The purpose of the plot is to identify times, when interesting data
were recorded by the FAAM weather radar.

"""

__author__ = "Axel Wellpott"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Axel Wellpott"
__email__ = "axll@faam.ac.uk"
__status__ = "Development"


#TODO: add altitude plot and some status info from the weather radar in separate axes
#TODO: add time option to script, so that it is possible to get the overview only for a specific time frame instead of the whole flight
#TODO: add summary text to plot

import datetime
import numpy as np
import matplotlib as mpl
# remove x-server dependencies
mpl.use('Agg')
import matplotlib.dates
import matplotlib.pyplot as plt
import netCDF4
import os
import re
import scipy.ndimage.interpolation
import sys

from matplotlib.mlab import griddata
from matplotlib.dates import date2num

cmap_wxrx = mpl.colors.ListedColormap(['grey',
                                       'lime',
                                       'yellow',
                                       'red',
                                       'magenta',
                                       'cyan',
                                       'white',
                                       'white'])



def get_mpl_time(ds):
    """Converts the time stamp from a netCDF file into a matplotlib useable format.

    """
    pattern = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    base_time_string = re.findall(pattern, str(ds.variables['time'].units).strip())[0]
    base_time = datetime.datetime.strptime(base_time_string, '%Y-%m-%d %H:%M:%S')
    result = ds.variables['time'][:]/86400. + date2num(base_time)
    return result


class Overview(object):

    def __init__(self, netcdf_ds, imgfile, sec_start=None, sec_end=None):
        self.sec_start = sec_start
        self.sec_end = sec_end
        self.Nc_file = netcdf_ds
        self.Imgfile = imgfile
        self._open_netcdf_()
        self.__get_data__()
        self.create()
        self._close_netcdf_()

    def _open_netcdf_(self ):
        self.ncds = netCDF4.Dataset(self.Nc_file, 'r')

    def _close_netcdf_(self):
        self.ncds.close()

    def __get_data__(self):
        if self.sec_start and self.sec_end:
            ix_s = np.min(np.where(self.ncds.variables['time'][:] > self.sec_start))
            ix_e = np.max(np.where(self.ncds.variables['time'][:] < self.sec_end))
            tmp_img_data = self.ncds.variables['reflectivity'][:][ix_s:ix_e]
            self.X = get_mpl_time(self.ncds)[ix_s:ix_e]
        else:
            tmp_img_data = self.ncds.variables['reflectivity'][:]
            self.X = get_mpl_time(self.ncds)
        self.xlim = ((np.min(self.X), np.max(self.X)))
        self.Y = np.arange(512)
        # TODO: make step an input argument
        step = 500
        zoom_factor = (1, (2048./tmp_img_data.shape[0])*step)
        self.Z = scipy.ndimage.interpolation.zoom(tmp_img_data.transpose()[:,::step], zoom_factor)
        self.Z = np.resize(self.Z, (512, 2048))

    def create(self):
        xi = np.linspace(self.xlim[0], self.xlim[1], 2048)
        yi = np.linspace(0, 512, 512)
        #zi = griddata( self.X, self.Y, self.Z, xi, yi, interp='linear')
        #zi = self.Z.resize( (512, 1024 ))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        levels = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
        plt.contourf(xi, yi, self.Z, levels, cmap=cmap_wxrx)
        plt.xlim(self.xlim)
        plt.ylim((0, 512))
        plt.title(os.path.basename(self.Nc_file))
        plt.xlabel('time (UTC)')
        plt.ylabel('bin data (-)')
        plt.grid()
        cbar = plt.colorbar()
        cbar.set_ticks([0,1,2,3,4,5,6,7])
        hourloc = matplotlib.dates.HourLocator()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%Y-%m-%d\n%H:%M:%S')
        ax.xaxis.set_major_locator(hourloc)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
        plt.savefig(self.Imgfile)
        plt.clf()


def do_all(inpath=None, outpath=None):
    """Wrapper to create Overview plots for all Weather Radar files in a directory.

    """
    import glob
    if not inpath:
        file_list = glob.glob(os.path.join(inpath + '/*/*.nc'))
    else:
        file_list = glob.glob('/home/data/faam/wxrx/*/*.nc')

    file_list.sort()
    for f in file_list:
        if outpath:
            png_file = os.path.join(outpath, '%s_%s_wxrx_overview.png' % (f[-7:-3], os.path.basename(f).split('_')[2]))
        else:
            png_file = os.path.join(os.path.dirname(f), '%s_%s_wxrx_overview.png' % (f[-7:-3], os.path.basename(f).split('_')[2]))
        try:
            print('Working on ... %s' %f)
            Overview(f, png_file)
        except:
            print('Failed to create plot for ... %s' %f)
            pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Creates an overview plot from a weather radar netCDF file.",
                                     version='Version %s' % __version__,
                                     epilog="Report bugs to <axll@faam.ac.uk>.")
    parser.add_argument('wxrx_ncfile', action="store", type=str, help='FAAM Weather Radar netCDF file.')
    parser.add_argument('-a', '--all', action="store_true", default=False,
                        required=False,
                        help='Finds recursively all netcdf files in a directory and creates an overview plot for every file.')
    parser.add_argument('-o', '--outpath', action="store", type=str,
                        required=False, default=os.environ['HOME'],
                        help='Directory where the image is going to be saved. Default: $HOME.')
    args = parser.parse_args()
    if args.all:
      do_all(inpath=args.wxrx_ncfile, outpath=args.outpath)
      sys.exit(2)
    png_file = os.path.join(os.path.dirname(args.wxrx_ncfile), '%s_%s_wxrx_overview.png' % (args.wxrx_ncfile[-7:-3], os.path.basename(args.wxrx_ncfile).split('_')[2]))
    sys.stdout.write('Working on ... %s\n' % args.wxrx_ncfile)
    try:
        OVplot = Overview(args.wxrx_ncfile, os.path.join(args.outpath, png_file))
    except:
        sys.stdout.write('Failed to create plot for ... %s\n' % args.wxrx_ncfile)
        sys.exit(2)
