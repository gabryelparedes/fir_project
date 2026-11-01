import numpy as numpy
from scipy import signal


fs = 48000 # Standard audio sample rate
f_pass = 4000
f_stop = 6000
N = 41

h = signal.remez(N, [0, f_pass, f_stop, fs/2], [1,0], 
                weight = [1,10], fs=fs)
print(h)