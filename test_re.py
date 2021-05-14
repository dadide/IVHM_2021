import numpy as np

from scipy import signal



N = 5

x = np.linspace(0, 1, N, endpoint=False)

y = 2 + x**2 - 1.7*np.sin(x) + .2*np.cos(11*x)

y2 = 1 + x**3 + 0.1*np.sin(x) + .1*np.cos(11*x)

Y = np.stack([y, y2], axis=-1)

up = 4

xr = np.linspace(0, 1, N*up, endpoint=False)



y2 = signal.resample_poly(Y, up, 1, padtype='constant')

y3 = signal.resample_poly(Y, up, 1, padtype='mean')

y4 = signal.resample_poly(Y, up, 1, padtype='line')

print(y4)

import matplotlib.pyplot as plt

for i in [0,1]:

    plt.figure()

    plt.plot(xr, y4[:,i], 'g.', label='line')

    plt.plot(xr, y3[:,i], 'y.', label='mean')

    plt.plot(xr, y2[:,i], 'r.', label='constant')

    plt.plot(x, Y[:,i], 'k-')

    plt.legend()

plt.show()