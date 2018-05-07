
import netCDF4
import pyvtk
import scipy.interpolate

import numpy as np

from evtk.hl import gridToVTK
from evtk.hl import pointsToVTK
from pylab import *


# Extract x, y, z and reflectivity from the netcdf
# x,y,z,r


def get_data(ncfile, start_time, end_time):
    ds = netCDF4.Dataset(ncfile, 'r')
    ix_s = np.min(np.where(ds.variables['time'][:] > start_time))
    ix_e = np.max(np.where(ds.variables['time'][:] < end_time))
    lon = ds.variables['lon_gin'][:][ix_s:ix_e]
    lat = ds.variables['lat_gin'][:][ix_s:ix_e]
    alt = ds.variables['alt_gin'][:][ix_s:ix_e]
    hdg = ds.variables['hdg_gin'][:][ix_s:ix_e]
    scan_angle = ds.variables['scan_angle'][:][ix_s:ix_e]
    tilt = ds.variables['tilt'][:][ix_s:ix_e]
    rng = ds.variables['range'][:][ix_s:ix_e]
    refl = ds.variables['reflectivity'][:][ix_s:ix_e] 
    ds.close()
    return (lon, lat, alt, hdg, scan_angle, tilt, rng, refl)


def compass2cartesian(angle):
    """The scan_angle of the weather radar is given in compass
    units and need to be converted to cartesian before calculating
    xyz coordinates.
    
    """
    angle = np.array(angle)
    angle[angle > 360] = angle[angle > 360] - 360.
    angle[angle <= 90] = angle[angle <= 90]*(-1.) + 90.
    angle[angle > 90] = angle[angle > 90]*(-1.) + 450.
    return angle


def calc_xyz(scan_angle, tilt, rng, y_offset):
    n = len(tilt)
    y_offset = np.repeat(y_offset, 512)
    range_arr = np.tile(np.linspace(0, 1, 512), n) * np.repeat(rng, 512) * 1825.0    
    new_scan_angle = compass2cartesian(scan_angle)             
    x = range_arr * np.repeat(np.sin(np.deg2rad(90.0-tilt)) * np.cos(np.deg2rad(new_scan_angle)), 512)
    y = range_arr * np.repeat(np.sin(np.deg2rad(90.0-tilt)) * np.sin(np.deg2rad(new_scan_angle)), 512)
    y += y_offset 
    z = range_arr * np.repeat(np.cos(np.deg2rad(90-tilt)), 512)
    return (x, y, z)



def meshgrid2(*arrs):
    """see: http://stackoverflow.com/questions/1827489/numpy-meshgrid-in-3d
    
    """
    arrs = tuple(reversed(arrs))  #edit
    lens = map(len, arrs)
    dim = len(arrs)
    sz = 1
    for s in lens:
        sz*=s
    ans = []    
    for i, arr in enumerate(arrs):
        slc = [1]*dim
        slc[i] = lens[i]
        arr2 = np.asarray(arr).reshape(slc)
        for j, sz in enumerate(lens):
            if j!=i:
                arr2 = arr2.repeat(sz, axis=j) 
        ans.append(arr2)
    return tuple(ans[::-1])


def t2s(s):
    """converts time string to seconds past midnight"""
    s = str.strip(s)
    result = int(s[0:2]) * 3600 + int(s[2:4]) * 60 + int(s[4:6])
    return result


#SETTINGS
ncfile = '/home/data/faam/wxrx/b728_wxrx/weather-radar-trial_faam_20120815_r0_b728.nc'
ncfile = '/home/data/faam/wxrx/b784_wxrx/weather-radar-trial_faam_20130628_r0_b784.nc'

_RUNS = (('Run', '142500', '143000'),)

#start_time = 46400
#end_time = 46600

for _R in _RUNS:
    start_time = t2s(_R[1])
    end_time = t2s(_R[2])
    
    step = 4
    _x_res = 100
    _y_res = 250
    _z_res = 50
    _INTP_METHOD = 'nearest'
    
    lon, lat, alt, hdg, scan_angle, tilt, rng, refl = get_data(ncfile, start_time, end_time)
    
    ORIGIN = {'lon': lon[0], 'lat': lat[0], 'alt': alt[0], 'hdg': hdg[0]}
    
    #get number of records
    n = len(lon)
    ix = range(0, (n // step) * step, step)
    y_offset = 100./190. * np.arange(n)
    x, y, z = calc_xyz(scan_angle[ix], tilt[ix], rng[ix], y_offset[ix])
    #r = refl[ix,:].flatten()
    r = refl[ix,:].ravel()
    
    xlim = ((np.min(x) // _x_res) * _x_res, ((np.max(x) // _x_res)+1) * _x_res) 
    ylim = (0, ((np.max(y) // _y_res)+1) * _y_res)
    zlim = ((np.min(z) // _z_res) * _z_res, (np.max(z) // _z_res) * _z_res)
    
    _xrange = range(int(xlim[0]), int(xlim[1]), _x_res)
    _yrange = range(int(ylim[0]), int(ylim[1]), _y_res)
    _yrange.reverse()
    _zrange = range(int(zlim[0]), int(zlim[1]), _z_res)
    
    
    
    grid_x, grid_y, grid_z = meshgrid2(_xrange,
                                       _yrange,
                                       _zrange)
    r[z < -2200] = 0
    print('xlim: ', xlim)
    print('ylim: ', ylim)
    print('zlim: ', zlim)
    print('Shape:', grid_x.shape)
    
    new_data = scipy.interpolate.griddata((x.ravel(), y.ravel(), z.ravel()), 
                                          r.ravel(), 
                                          (grid_x, grid_y, grid_z),
                                          method=_INTP_METHOD)
    
    #new_data = new_data.transpose((2,1,0))
    
    _x = np.arange(new_data.shape[0])
    _y = np.arange(new_data.shape[1])
    _z = np.arange(new_data.shape[2]) * 25.
    
    outfile = '/home/axel/b784_%s_%s_%s' % (_R[0].replace(' ', '').lower(), _R[1], _R[2])
    
    #gridToVTK(outfile,  _x, _y, _z, cellData = {"reflectivity" : new_data})
    gridToVTK(outfile,  _x, _y, _z * 3, pointData = {"reflectivity" : new_data})
    #pointsToVTK("/home/axel/point",  grid_x.ravel(), grid_y.ravel(), grid_z.ravel(), data = {"reflectivity" : new_data.ravel()})
    #pointsToVTK("/home/axel/point",  _x, _y, _z, data = {"reflectivity" : new_data})


