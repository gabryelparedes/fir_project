import numpy as np
from scipy import signal


fs = 48000 # Standard audio sample rate
f_pass = 4000
f_stop = 6000
N = 41

# FIR Filter
h = signal.remez(N, [0, f_pass, f_stop, fs/2], [1,0], 
                weight = [1,10], fs=fs)
print(h)

w, H = signal.freqz(h, worN=8192, fs=fs)

passBand = np.abs(H[w <= f_pass])
stopBand = np.abs(H[w >= f_stop])
ripple_db = 20*np.log10(passBand.max()) - 20*np.log10(passBand.min())
atten_db = -20*np.log10(stopBand.max())
print(ripple_db, atten_db)