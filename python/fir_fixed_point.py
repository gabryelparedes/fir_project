
# STEP 1: Load coefficients and define hardware settings

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# Load the ideal FIR filter coefficients
h = np.load("h_float.npy")

# Choose initial hardware settings
DATA_BITS = 16
COEFF_BITS = 12
ACC_BITS = 40

DATA_FRAC = DATA_BITS - 1
COEFF_FRAC = COEFF_BITS - 1

print("Number of coefficients:", len(h))
print("First 5 floating-point coefficients:", h[:5])


# STEP 2: Saturation and coefficient quantization

# Limit a value to the signed integer range
def saturate(value, bits):
    minimum = -(2 ** (bits - 1))
    maximum = 2 ** (bits - 1) - 1
    return max(min(int(value), maximum), minimum)

# Quantize the floating-point coefficients
h_fixed = np.array([
    saturate(np.rint(c * 2**COEFF_FRAC), COEFF_BITS)
    for c in h
], dtype=np.int64)

print("First 5 fixed-point coefficients:", h_fixed[:5])
print("Total coefficients:", len(h_fixed))


# STEP 3: Generate and quantize the test input

# Generate a 1 kHz sine wave
fs = 48000
t = np.arange(480) / fs
x = 0.5 * np.sin(2 * np.pi * 1000 * t)

# Convert input samples into 16-bit integers
x_fixed = np.array([
    saturate(np.rint(v * 2**DATA_FRAC), DATA_BITS)
    for v in x
], dtype=np.int64)

print("First 10 floating-point inputs:", x[:10])
print("First 10 fixed-point inputs:", x_fixed[:10])


# STEP 4: Hardware-mirrored FIR filter calculation

# Simulate fixed-width signed arithmetic
def wrap_signed(value, bits):
    return ((int(value) + 2**(bits - 1)) % (2**bits)) - 2**(bits - 1)

def hardware_fir(x_fixed, h_fixed):
    outputs = []

    for n in range(len(x_fixed)):
        accumulator = 0

        for k in range(len(h_fixed)):
            if n - k >= 0:
                product = int(x_fixed[n-k]) * int(h_fixed[k])

                accumulator = wrap_signed(
                    accumulator + product, ACC_BITS
                )

        # Truncate fractional bits
        output = accumulator >> COEFF_FRAC

        # Saturate to signed 16-bit range
        output = saturate(output, DATA_BITS)

        outputs.append(output)

    return np.array(outputs, dtype=np.int64)

# Run the hardware model
y_fixed_int = hardware_fir(x_fixed, h_fixed)

print("First 10 hardware output integers:", y_fixed_int[:10])


# STEP 5: Compare ideal and hardware-mirrored FIR outputs

# Calculate ideal floating-point FIR output
y_ideal = signal.lfilter(h, [1.0], x)

# Convert hardware integers back to floating-point scale
y_hardware = y_fixed_int / (2**DATA_FRAC)

# Calculate the error
error = y_ideal - y_hardware

print("Maximum absolute error:", np.max(np.abs(error)))
print("First 10 ideal outputs:", y_ideal[:10])
print("First 10 hardware outputs:", y_hardware[:10])

# Plot the two outputs
plt.figure(figsize=(10, 4))
plt.plot(y_ideal, label="Ideal floating-point")
plt.plot(y_hardware, "--", label="Hardware-mirrored")
plt.xlabel("Sample index")
plt.ylabel("Amplitude")
plt.title("Ideal vs Hardware-Mirrored FIR Filter")
plt.legend()
plt.grid(True)

# Save the comparison graph
plt.savefig("../results/ideal_vs_fixed.png", dpi=300)

# Save integer outputs for future Verilog verification
np.savetxt("../results/fixed_output.txt", y_fixed_int, fmt="%d")

plt.show()
