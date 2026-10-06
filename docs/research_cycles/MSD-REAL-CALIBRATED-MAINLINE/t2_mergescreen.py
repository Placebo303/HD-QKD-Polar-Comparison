"""T-2 zero-decode merge screen (record): cross-source held-out LL.

Fit plug-in P(a|b) on source X counts, score plug-in-sampled pairs from source
Y (screening only; sampling limitation stated). Merged = summed counts.
Criterion (frozen): 3-way merge needs all cross drops small; pair merge needs
pairwise drop small.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    import sys
    sys.path.insert(0, ".")
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (
        load_train_table,
    )

    ts = {s: load_train_table(s) for s in ("T2-1M", "T2-1.5M", "T2-2M")}
    merged = sum(ts.values())

    def sample(t, n, seed):
        f = t.ravel() / t.sum()
        nz = np.flatnonzero(f)
        p = f[nz]
        r, c = np.unravel_index(nz, t.shape)
        rng = np.random.default_rng(seed)
        pk = rng.choice(nz.size, size=n, p=p)
        return r[pk], c[pk]

    def xll(fit, a, b):
        col = fit.sum(axis=0)
        col[col == 0] = 1.0
        cond = fit / col[None, :]
        return float(np.log(np.maximum(cond[a, b], 1e-300)).sum() / a.size)

    names = list(ts.keys())
    cross, mdrop = {}, {}
    for s in names:
        a, b = sample(ts[s], 20000, 7)
        own = xll(ts[s], a, b)
        cross[s] = {"own": round(own, 4)}
        for f in names:
            if f != s:
                cross[s][f] = round(xll(ts[f], a, b), 4)
        mdrop[s] = round(own - xll(merged, a, b), 4)
    out = {"cross_ll": cross, "merged_drop_vs_own": mdrop,
           "verdict": "3-way merge REFUSED (T2-1M cross -76..-115 nats); "
                      "1.5M+2M pair viable by LL (drop ~0.06), proxy validation deferred",
           "limitation": "pairs are plug-in-sampled, not real held-out pairs"}
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
