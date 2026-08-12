from __future__ import annotations


def throughput(bits: float, runtime_s: float) -> float:
    rt = float(runtime_s)
    if rt <= 0.0:
        return 0.0
    return float(bits) / rt
