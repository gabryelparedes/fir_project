import os
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fs = 48000
f_pass = 4000
f_stop = 6000
f_cut = (f_pass + f_stop) / 2

def check(h):
    w, H = signal.freqz(h, worN=8192, fs=fs)
    mag = np.abs(H)
    passBand = mag[w <= f_pass]
    stopBand = mag[w >= f_stop]
    ripple = 20 * np.log10(passBand.max()) - 20 * np.log10(passBand.min())
    atten = -20 * np.log10(stopBand.max())
    return w, mag, ripple, atten

N_hamming = None
for N in range(11, 201, 2):
    h_ham = signal.firwin(N, f_cut, window="hamming", fs=fs)
    _, _, ripple, atten = check(h_ham)
    if ripple < 1 and atten >= 40:
        N_hamming = N
        break

if N_hamming is None:
    raise SystemExit("No Hamming design under 200 taps met the spec")

h_remez = np.load("h_float.npy")
N_remez = len(h_remez)

w, mag_r, rip_r, att_r = check(h_remez)
_, mag_h, rip_h, att_h = check(h_ham)

print(f"Parks-McClellan: N={N_remez}  ripple={rip_r:.3f} dB  atten={att_r:.1f} dB")
print(f"Hamming window:  N={N_hamming}  ripple={rip_h:.3f} dB  atten={att_h:.1f} dB")
print(f"Hamming needs {N_hamming - N_remez} more taps "
      f"({100 * (N_hamming / N_remez - 1):.0f}% more multipliers)")

os.makedirs("../results", exist_ok=True)
plt.figure(figsize=(9, 5))
plt.plot(w, 20 * np.log10(mag_r + 1e-12), label=f"Parks-McClellan (N={N_remez})")
plt.plot(w, 20 * np.log10(mag_h + 1e-12), label=f"Hamming window (N={N_hamming})")
plt.axvline(f_pass, color="g", linestyle="--", label="passband edge")
plt.axvline(f_stop, color="r", linestyle="--", label="stopband edge")
plt.axhline(-40, color="gray", linestyle=":", label="-40 dB limit")
plt.ylim(-100, 5)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (dB)")
plt.title("Windowed vs. Parks-McClellan design, both meeting the spec")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("../results/firwin_vs_remez.png")
