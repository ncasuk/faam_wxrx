'''
Created on 15 Jul 2013

@author: axel
'''
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
from matplotlib import cm


cmap_wxrx = mpl.colors.ListedColormap(['grey', 'lime', 'yellow', 'red', 'magenta', 'cyan', 'white', 'white'], 'indexed')
#plt.register_cmap(name='cmap_wxrx', data=cmap_wxrx)
fig = plt.figure()
ax = fig.gca(projection='3d')

#heights below aircraft platform
heights = [1250, 1000, 750, 500]
for i in heights:
    ix = np.argmin(np.abs(np.array(_zrange) + i))
    print(np.histogram(new_data[ix,:,:].ravel(), [0,1,2,3,4,5]))
    new_data[new_data == 0] = 999
    levels = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
    cset = ax.contourf(grid_x[0,:,:], grid_y[0,:,:], new_data[ix,:,:], levels=levels, zdir='z', offset=-i, cmap=cmap_wxrx)


ax.set_xlabel('lateral distance (m)')
#ax.set_xlim(-40, 40)
ax.set_ylabel('anterior distance (m)')
#ax.set_ylim(-40, 40)
ax.set_zlabel('height below platform (m)')
ax.set_zlim(-1250, -500)

plt.show()
