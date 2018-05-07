import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def randrange(n, vmin, vmax):
    return (vmax-vmin)*np.random.rand(n) + vmin

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
n = 100
#for c, m, zl, zh in [('r', 'o', -50, -25), ('b', '^', -30, -5)]:
#    xs = randrange(n, 23, 32)
#    ys = randrange(n, 0, 100)
#    zs = randrange(n, zl, zh)
#    ax.scatter(xs, ys, zs, c=c, marker=m)

col = ['grey', 'lime', 'yellow', 'red', 'magenta', 'cyan', 'white', 'white']
for i in range(1, 4):
    ix = np.where(new_data == i)
    print(i, len(ix))
    xs = np.transpose(ix)[:,0]
    ys = np.transpose(ix)[:,1]
    zs = np.transpose(ix)[:,2]
    ax.scatter(zs, ys,  xs, c=col[i])

ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

plt.show()
