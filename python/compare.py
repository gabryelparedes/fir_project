import sys
import glob
import os
import numpy as np


def compare(exp_path, act_path, label):
    expected = np.loadtxt(exp_path, dtype=np.int64)
    actual = np.loadtxt(act_path, dtype=np.int64)
    if len(actual) != len(expected):
        print(f"[{label}] FAIL: length mismatch (Verilog gave {len(actual)}, expected {len(expected)})")
        return False
    diff = actual - expected
    bad = np.nonzero(diff)[0]
    if len(bad) == 0:
        print(f"[{label}] PASS: all {len(expected)} outputs match the golden model bit for bit")
        return True
    print(f"[{label}] FAIL: {len(bad)} of {len(expected)} outputs differ")
    for n in bad[:10]:
        print(f"  n={n}: Verilog {actual[n]}, golden {expected[n]}, off by {diff[n]}")
    return False


if "--all" in sys.argv:
    ok = True
    for exp_path in sorted(glob.glob("../vectors/configs/exp_*.txt")):
        name = os.path.basename(exp_path)[4:-4]
        act_path = f"../vectors/configs/act_{name}.txt"
        if not os.path.exists(act_path):
            print(f"[{name}] MISSING: run run_all.sh first")
            ok = False
            continue
        ok &= compare(exp_path, act_path, name)
else:
    ok = compare("../vectors/expected.txt", "../vectors/actual.txt", "default")

raise SystemExit(0 if ok else 1)