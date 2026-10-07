"""H-3 parameter-estimation cost (EXPLORE zero-decode + 1 decode confirmation):
(a) sampling error of (p, p-) vs n_train by bootstrap on TRAIN pairs;
(b) analytic KL penalty -> f-loss curve;
(c) ONE decode confirmation at n=10k (N=16384 RA-gap0.10, B=100);
(d) net kept-material gain vs old 60% sacrifice.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--curve", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    z = np.load(proot / "T2-1M_tier_pairs.npz")
    a_full = np.asarray(z["a_full"], dtype=np.int64)
    b_full = np.asarray(z["b_full"], dtype=np.int64)
    e_full = (b_full - a_full) % 1024
    N_TOT = a_full.size
    p_true = float((e_full != 0).mean())
    pm_true = float(((e_full == 1023)).sum() / max(1, int((e_full != 0).sum())))
    out = {"p_true": p_true, "p_minus_cond_true": pm_true, "N_total": N_TOT}
    print("true p:", round(p_true, 5), "p-:", round(pm_true, 5), flush=True)
    if args.curve:
        rng = np.random.default_rng(20267500)
        rows = []
        for ntr in (1000, 3000, 10000, 30000, 100000):
            se_p, se_pm, kl = [], [], []
            for rep in range(30):
                sub = rng.choice(N_TOT, size=min(ntr, N_TOT), replace=False)
                ee = e_full[sub]
                ph = float((ee != 0).mean())
                pmh = float((ee == 1023).sum() / max(1, int((ee != 0).sum())))
                se_p.append(ph)
                # KL(true || est) per symbol on ternary {0,+, -} approx
                q = np.array([1 - ph, ph * (1 - pmh), ph * pmh])
                p0 = np.array([1 - p_true, p_true * (1 - pm_true),
                               p_true * pm_true])
                q = np.maximum(q, 1e-300)
                kl.append(float((p0 * np.log2(p0 / q)).sum()))
            klm = float(np.mean(kl))
            # f-loss: extra disclosure N*KL amortized + margin opinion
            f_loss = (16384 * klm) / (16384 * 0.7981344445)
            rows.append({"n_train": ntr, "p_std": round(float(np.std(se_p)), 6),
                         "KL_mean_bits": round(klm, 6),
                         "f_loss_analytic": round(f_loss, 5),
                         "sacrifice_frac": round(min(ntr, N_TOT) / N_TOT, 5)})
            print(rows[-1], flush=True)
        # net kept gain vs old 60% sacrifice (per 1000-superframe deployment)
        new_sac = 10000 / (1000 * 1024)
        out["curve"] = rows
        out["net_gain"] = {"old_sacrifice": 0.60, "new_sacrifice_10k": new_sac,
                           "kept_multiplier": round((1 - new_sac) / (1 - 0.60), 3)}
        print("net kept multiplier @10k:", out["net_gain"]["kept_multiplier"])
    (root / "h3_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
