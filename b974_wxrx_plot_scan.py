'''
Created on 16 Nov 2011

@author: axel
'''

import os
import sys

sys.path.insert(0, '/home/axel/git-repos/faam_wxrx')

import faam_wxrx
import faam_wxrx.wxrx_plot_scan
import faam_wxrx.tiff_to_kmz
import matplotlib.pyplot as plt

ncfile='/home/axel/b974_wxrx/weather-radar-trial_faam_20160707_r0_b974.nc'

ii = range(16500, 29700, 60)

opath = '/home/axel/b974_wxrx/b974_wxrx_scans/'
for i in ii:
    imgfile = os.path.join(opath, 'faam_wxrx_scan_b974_%05.i.png' % i)
    s = faam_wxrx.wxrx_plot_scan.Scan(ncfile, i, imgfile=imgfile)
    s.plot()
    plt.close(s.Figure)
    tiff_filename = os.path.join(opath, 'faam_wxrx_scan_b974_%05.i.tiff' % i)
    faam_wxrx.wxrx_plot_scan.to_geotiff(s, tiff_filename)

    faam_wxrx.tiff_to_kmz.tiff_to_kmz(tiff_filename, opath)
