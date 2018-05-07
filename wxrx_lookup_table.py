"""Calculates the optimal weather radar settings for
    range
    tilt
   Inputs required: cloud top height, cloud height, aircraft
   altitude
"""

#Input

cloud_bottom = 2000.
cloud_top = 16000./3.
altitude = 20000./3.


import numpy as np
for rng in [5,10,20,40,80,160,315,320]:
    for tilt in range(15, 1, -1):
        rng_downwards = np.sin(np.deg2rad(tilt)) * rng * 1825.0
        full_height = (altitude - rng_downwards) < cloud_bottom        
        hits_ground = rng_downwards > altitude

        width_at_cloud_bottom = np.sin(np.deg2rad(80)) * (altitude - cloud_bottom)
        width_at_cloud_top = np.sin(np.deg2rad(80)) * (altitude - cloud_top)
        if not hits_ground and full_height:
            print('rng: %3i tilt: %2i hgt: %.2f ' % (rng, tilt, rng_downwards))
print('\n' + 35*'#' + '\n')
print('width@cloud_top   : %.2fm' %  width_at_cloud_top)
print('width@cloud_bottom: %.2fm' % width_at_cloud_bottom)
