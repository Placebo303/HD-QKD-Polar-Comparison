"""E-1 MSD retune with diff-reconstructed prior (cross-half th_b, alpha=1,
CERTAIN-fixed smoothing scale): plane-1 m ladder {600,1200,2400} + K rescue,
N=16384, B>=300/point, full-symbol f. Simultaneously verifies the D-3 und-226
row: if und replicates ~75%, it stands as corrected behavior; if ~0-10%, the
226 ran pre-fix code and gets relabeled.
R14: layers = 10 binary planes; per-plane H from diff-channel truth (logged);
ideal disclosure = N*h; actual m per ladder; rescue K disclosed on fail.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

N = 16384
M1_LADDER = (600, 1200, 2400)
B = 300
K = 400
SEED = 20266600
TAG_BITS = 64


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("E-1 runs only with --full")
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
        read_p1_scalars,
        wilson_upper,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
        build_mixed_point,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    th_a = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_a"])
    th_b = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_b"])
    assert th_a.sum() > 100000, "proxy tables"
    # channel generative pair (th_a fit) + prior (th_b fit, CORRECTED scale)
    def fit_g(t):
        tot = t.sum()
        pa = t.sum(axis=1) / tot
        d = (np.arange(1024)[None, :] - np.arange(1024)[:, None]) % 1024
        g = np.bincount(d.ravel(), weights=t.ravel(), minlength=1024)
        return pa / pa.sum(), g / g.sum()
    pa_ch, g_ch = fit_g(th_a)
    tot_b = th_b.sum()
    g_b = np.asarray(mc.smooth_difference_counts(
        mc.difference_pmf(th_b, 1024) * tot_b, 1024, 1.0), dtype=np.float64)
    # sanity: corrected scale concentrates on window (H1 fix check)
    top3 = sorted(g_b, reverse=True)[:3]
    print("prior g top3:", [round(float(v), 4) for v in top3], flush=True)
    assert top3[0] > 0.5, "smoothing scale still broken"
    pa_b = th_b.sum(axis=1) / tot_b
    aks = np.arange(1024)
    joint = pa_b[:, None] * g_b[(aks[None, :] - aks[:, None]) % 1024]
    joint = joint / joint.sum()
    model = _bcp(joint * tot_b, encoding="NATURAL", order="LSB_FIRST")
    # TRUE diff-channel plane h (genie pseudo, fixed disclosure baseline)
    jg = pa_ch[:, None] * g_ch[(aks[None, :] - aks[:, None]) % 1024]
    jg = jg / jg.sum()
    h_true = plane_conditional_entropies(jg * 1e7)
    print("R14 plane h:", [round(float(v), 4) for v in h_true], flush=True)
    print("R14 ideal disclosure:", [round(float(v * N), 1) for v in h_true],
          flush=True)
    jl = root / "blocks_e1.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    bp = functools.partial(make_bp_decoder, max_iter=200)
    scalars = read_p1_scalars()["T2-1M"]
    rows = []
    for m1 in M1_LADDER:
        matrices, factories, _, m_list = build_mixed_point(N, h_true, 2000, 32, 256)
        matrices[1] = build_peg_code(n=N, m=m1, variable_degree=3).parity_check_matrix
        m_list[1] = m1
        l_base = int(sum(m_list))
        rng = np.random.default_rng(SEED)
        n_fail = n_und = n_res = n_vw = n_p1f = 0
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(B):
                a = rng.choice(aks, size=N, p=pa_ch)
                delta = rng.choice(aks, size=N, p=g_ch)
                alice = a.astype(np.int64)
                bob = ((a + delta) % 1024).astype(np.int64)
                r = _decode_msd_block(alice, bob, model, matrices, factories,
                                      K, bp)
                n_fail += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                n_res += 1 if r["rescued"] else 0
                n_vw += r["valid_wrong_stages"]
                n_p1f += 1 if r["plane1_failed"] else 0
                fh.write(json.dumps({"m1": m1, "block": blk,
                                     "exact_ok": bool(r["exact_ok"]),
                                     "undetected": bool(r["undetected"]),
                                     "rescued": bool(r["rescued"]),
                                     "valid_wrong": r["valid_wrong_stages"],
                                     "plane1_failed": bool(r["plane1_failed"])}) + "\n")
        wall = time.perf_counter() - t0
        e_l = float(l_base + K * n_res / B)
        fer = n_fail / B
        denom = N * scalars["H_AB"]
        kept = N * scalars["H_A"] - e_l
        f_p = (e_l + TAG_BITS + kept * fer) / denom
        rows.append({"m1": m1, "N": N, "blocks": B, "L_EC": l_base,
                     "failures": n_fail, "undetected": n_und,
                     "valid_wrong_total": n_vw, "plane1_failed": n_p1f,
                     "n_rescue": n_res, "E_L": e_l, "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(n_fail, B),
                     "f_expected": f_p, "source": "T2-1M",
                     "backend": "msd-e1", "wall_s": wall})
        print(f"m1={m1}: fail {n_fail}/{B} und {n_und} vw {n_vw} "
              f"p1fail {n_p1f} f={f_p:.3f}", flush=True)
    (root / "e1_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
