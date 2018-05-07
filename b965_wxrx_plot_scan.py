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

ii = range(46800, 56000, 60)

ncfile = '/home/axel/b965_wxrx/weather-radar-trial_faam_20160626_r0_b965.nc'

opath = '/home/axel/b965_wxrx/b965_wxrx_scans/'
for i in ii:
    imgfile = os.path.join(opath, 'faam_wxrx_scan_b965_%05.i.png' % i)
    try:
        s = faam_wxrx.wxrx_plot_scan.Scan(ncfile, i, imgfile=imgfile)
        s.plot()
        plt.close(s.Figure)
    except:
        continue
    tiff_filename = os.path.join(opath, 'faam_wxrx_scan_b965_%05.i.tiff' % i)
    faam_wxrx.wxrx_plot_scan.to_geotiff(s, tiff_filename)

    faam_wxrx.tiff_to_kmz.tiff_to_kmz(tiff_filename, opath)
