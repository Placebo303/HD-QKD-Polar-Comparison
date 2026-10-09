"""A2 alignment-audit synthetic reproduction (EXPLORE, no real data).

Demonstrates: coarse 100 ps cross-correlation histogram + argmax bin-centre
(no interpolation) quantizes the true residual delay mu to a 100 ps grid,
leaving a residual error up to +/-50 ps. Sign convention: lag = tB - tA,
offset added to side A (frozen _pair_nearest_unique).

Writes a small JSON report to a fresh --output-root.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BIN_W = 100
MAX_LAG = 819200
SEED = 20261009


def coarse_align(lags: np.ndarray) -> dict:
    edges = np.arange(-MAX_LAG, MAX_LAG + BIN_W, BIN_W, dtype=np.int64)
    counts, _ = np.histogram(lags, bins=edges)
    pk = int(np.argmax(counts))
    center = float((int(edges[pk]) + int(edges[pk + 1])) / 2.0)
    return {"peak_bin": [int(edges[pk]), int(edges[pk + 1])],
            "offset_ps": int(round(center)), "peak_count": int(counts[pk]),
            "total": int(len(lags))}


def run_case(mu_true: float, sigma: float, n: int, rng: np.random.Generator) -> dict:
    lags = rng.normal(loc=mu_true, scale=sigma, size=n)
    rec = coarse_align(lags)
    resid = float(mu_true - rec["offset_ps"])
    return {"mu_true": mu_true, "sigma": sigma, "n": n, **rec,
            "residual_ps": round(resid, 2),
            "quant_bound_ok": bool(abs(resid) <= BIN_W / 2.0 + 1e-9)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    cases = [run_case(mu, 25.0, 200000, rng) for mu in (+1.0, +37.0, -73.0)]
    # sign-convention check: shifting A by +offset must centre the peak
    lags = rng.normal(loc=40.0, scale=25.0, size=200000)
    rec = coarse_align(lags)
    shifted = lags - float(rec["offset_ps"])  # A-side correction moves lags by -offset
    sign_ok = bool(abs(float(np.mean(shifted))) <= 50.0)
    report = {"seed": SEED, "bin_width_ps": BIN_W, "sigma_ps": 25.0,
              "cases": cases,
              "sign_check": {"mu_true": 40.0, "offset": rec["offset_ps"],
                             "mean_after_correction": round(float(np.mean(shifted)), 2),
                             "ok": sign_ok},
              "conclusion": ("Coarse 100ps argmax-bin-centre alignment leaves "
                             "residual = mu_true - bin_centre, bounded by +/-50ps; "
                             "mu_true=+1ps case gives residual ~-49ps.")}
    (root / "a2_repro.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for c in cases:
        print(f"mu_true={c['mu_true']:+.0f} -> offset={c['offset_ps']:+d} "
              f"residual={c['residual_ps']:+.1f}ps ok={c['quant_bound_ok']}")
    print("sign check:", report["sign_check"])
    print(f"wrote {root / 'a2_repro.json'}")


if __name__ == "__main__":
    main()
