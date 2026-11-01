import numpy as np
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Spec (Hz)
fs = 48000 # Standard audio sample rate
f_pass = 4000
f_stop = 6000
N = 41

# FIR Filter (Parks-McClellan Method)
h = signal.remez(N, [0, f_pass, f_stop, fs/2], [1,0], 
                weight = [1,10], fs=fs)
print(h)

# Freq response
w, H = signal.freqz(h, worN=8192, fs=fs)

# Compare against spec
passBand = np.abs(H[w <= f_pass])
stopBand = np.abs(H[w >= f_stop])
ripple_db = 20*np.log10(passBand.max()) - 20*np.log10(passBand.min())
atten_db = -20*np.log10(stopBand.max())

print(f"Taps: {N}")
print(f"Passband ripple: {ripple_db} dB")
print(f"Stopband attentuation: {atten_db} dB")

# Gain stays w/in +-6% of ideal AND Unwanted freqs are shrunk to 1/100 size
if ripple_db < 1 and atten_db >= 40: 
    print("PASS!")
else:
    print("FAIL")

# Plot
plt.plot(w, 20*np.log10(np.abs(H) + 1e-12))
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (dB)")
plt.title("Ideal floating-point FIR Filter (N=41)")
plt.ylim(-80, 5)
plt.grid(True)
plt.axvline(f_pass, color="g", linestyle="--", label="passband edge")
plt.axvline(f_stop, color="r", linestyle="--", label="stopband edge")
plt.axhline(-40, color="gray", linestyle=":", label="-40 dB limit")
plt.legend()

plt.savefig("../results/ideal_response.png")
np.save("h_float.npy", h)