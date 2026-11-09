import numpy as np
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Spec (Hz)
fs = 48000 # Standard audio sample rate
f_pass = 4000
f_stop = 6000

h = np.load("h_float.npy")

# Quantize coefficients to B bits to closer model hardware
def quantize(h, B):
    top = 2**(B - 1) - 1 # Largest B bit value
    F = int(np.floor(np.log2(top / np.max(np.abs(h))))) # Num times to double coefficients
    h_int = np.clip(np.round(h * 2**F), -top - 1, top).astype(int)
    return h_int, F

# Comparing to spec
def check(h_q):
    w, H = signal.freqz(h_q, worN=8192, fs=fs)
    mag = np.abs(H)
    passBand = mag[w <= f_pass]
    stopBand = mag[w >= f_stop]
    ripple = 20 * np.log10(passBand.max()) - 20 * np.log10(passBand.min())
    atten = -20 * np.log10(stopBand.max())
    return w, mag, ripple, atten

# Bit-exact integer FIR: what fir.v should output
def fir_fixed(x_int, h_int, F):
    acc = np.convolve(x_int.astype(np.int64), h_int.astype(np.int64))[:len(x_int)]
    return acc >> F   # arithmetic shift = Verilog >>>

# One value per line, two's-complement hex, for $readmemh
def export_mem(vals, B, path):
    digits = (B + 3) // 4
    with open(path, "w") as f:
        for v in vals:
            f.write(f"{int(v) & (2**B - 1):0{digits}x}\n")

bit_widths = [16, 12, 10, 8, 6]

# Testing all B values
for B in bit_widths:
    h_int, F = quantize(h, B)
    h_q = h_int / 2**F
    w, mag, ripple, atten = check(h_q)
    ok = ripple < 1 and atten >= 40
    print(f"B={B:2d}  F={F:2d}  ripple={ripple:.3f} dB  atten={atten:.1f} dB  {'PASS' if ok else 'FAIL'}")

# Plot
plt.figure(figsize=(9, 5))
w, H = signal.freqz(h, worN=8192, fs=fs)
plt.plot(w, 20 * np.log10(np.abs(H) + 1e-12), "k", linewidth=2, label="ideal (float)")

for B in bit_widths:
    h_int, F = quantize(h, B)
    w, mag, _, _ = check(h_int / 2**F)
    plt.plot(w, 20 * np.log10(mag + 1e-12), label=f"{B}-bit")

plt.axvline(f_pass, color="g", linestyle="--")
plt.axvline(f_stop, color="r", linestyle="--")
plt.axhline(-40, color="gray", linestyle=":")
plt.ylim(-80, 5)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (dB)")
plt.title("Effect of coefficient quantization")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("../results/quantized_responses.png")

# Test vectors for verilog
import os
os.makedirs("../vectors", exist_ok=True)

B_COEF = 16   # Coefficient bits for the hardware build
B_X = 16      # Bits for X

h_int, F = quantize(h, B_COEF)   # Re-quantize at 16 bits (the loop left 6-bit values)
export_mem(h_int, B_COEF, "../vectors/coeffs.mem")
with open("../vectors/params.txt", "w") as f:
    f.write(f"B_COEF={B_COEF}\nB_X={B_X}\nF={F}\nN={len(h_int)}\n")

# Test input: impulse, then two tones, then random noise
rng = np.random.default_rng(0)
n = np.arange(500)
impulse = np.zeros(100); impulse[0] = 0.5 # Samples 0-99
tones = 0.45*np.sin(2*np.pi*1000*n/fs) + 0.45*np.sin(2*np.pi*10000*n/fs) # Samples 100-599
noise = rng.uniform(-0.9, 0.9, 500) # Samples 600-1099
x = np.concatenate([impulse, tones, noise])

top_x = 2**(B_X - 1) - 1
x_int = np.clip(np.round(x * 2**(B_X - 1)), -top_x - 1, top_x).astype(np.int64)

y_int = fir_fixed(x_int, h_int, F)
export_mem(x_int, B_X, "../vectors/input.mem")
np.savetxt("../vectors/expected.txt", y_int, fmt="%d")
print(f"Wrote test vectors to ../vectors/  (F={F})")