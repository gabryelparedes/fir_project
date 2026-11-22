import numpy as np

# Load the expected (Quantized Python) and actual (Verilog) files
expected = np.loadtxt("../vectors/expected.txt", dtype=np.int64)
actual = np.loadtxt("../vectors/actual.txt", dtype=np.int64)

if len(actual) != len(expected):
    print(f"FAIL: length mismatch (Verilog gave {len(actual)}, expected {len(expected)})")
    raise SystemExit(1)

diff = actual - expected
bad = np.nonzero(diff)[0]

# Pass when they match perfectly, fail otherwise
if len(bad) == 0:
    print(f"PASS: all {len(expected)} outputs match the golden model by for bit!")
else: 
    print(f"FAIL: {len(bad)} of {len(expected)} outputs differ")
    for n in bad[:10]:
        print(f"n={n}: Verilog {actual[n]}, golden {expected[n]}, off by {diff[n]}")
    raise SystemExit(1)