"""D-5 MSD D-1/D-3 contradiction (EXPLORE, proxy): 2x2 factorial
smoothing{none,alpha=1} x population{th_a, th_b} on th_a-diff channel, PLUS
P-c d=256 genie control. Fixed disclosure (shared matrices from diff-h).
B=100/config serial. Answers whether 7/300 -> 300/300 is smoothing,
population, or interaction. Until resolved, sharp-pin mechanism = HYPOTHESIS.
"""

from __future__ import annotations

import argparse
import functools
import json
import time
from pathlib import Path

import numpy as np

N = 16384
B = 100
K = 400
SEED = 20266500


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("D-5 runs only with --full")
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
        build_mixed_point,
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
    pa_ch = th_a.sum(axis=1) / th_a.sum()
    pa_ch = pa_ch / pa_ch.sum()
    d = (np.arange(1024)[None, :] - np.arange(1024)[:, None]) % 1024
    g_raw = np.bincount(d.ravel(), weights=th_a.ravel(), minlength=1024)
    g_raw = g_raw / g_raw.sum()

    def gen(n, rng):
        aks = np.arange(1024)
        a = rng.choice(aks, size=n, p=pa_ch)
        delta = rng.choice(aks, size=n, p=g_raw)
        return a.astype(np.int64), ((a + delta) % 1024).astype(np.int64)

    def smooth(tab, alpha):
        tot = tab.sum()
        g = np.asarray(mc.smooth_difference_counts(
            mc.difference_pmf(tab, 1024) * tot, 1024, alpha), dtype=np.float64)
        pa = tab.sum(axis=1) / tot
        aks = np.arange(1024)
        joint = pa[:, None] * g[(aks[None, :] - aks[:, None]) % 1024]
        return joint / joint.sum() * tot

    # shared matrices from near-exact genie pseudo (fixed disclosure)
    aks = np.arange(1024)
    jg = pa_ch[:, None] * g_raw[(aks[None, :] - aks[:, None]) % 1024]
    jg = jg / jg.sum()
    h_true = plane_conditional_entropies(jg * 1e7)
    matrices, factories, _, m_list = build_mixed_point(N, h_true, 2000, 32, 256)
    l_base = int(sum(m_list))
    bp = functools.partial(make_bp_decoder, max_iter=200)
    jl = root / "blocks_d5.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    rows = []
    cfgs = [("genie-a-nosmooth", th_a, 0.0), ("genie-a-alpha1", th_a, 1.0),
            ("cross-b-nosmooth", th_b, 0.0), ("cross-b-alpha1", th_b, 1.0)]
    for tag, tab, alpha in cfgs:
        if alpha == 0.0:
            pseudo = np.asarray(tab, dtype=np.float64)
        else:
            pseudo = smooth(np.asarray(tab, dtype=np.float64), alpha)
        model = _bcp(pseudo, encoding="NATURAL", order="LSB_FIRST")
        rng = np.random.default_rng(SEED)
        n_fail = n_und = n_vw = 0
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(B):
                alice, bob = gen(N, rng)
                r = _decode_msd_block(alice, bob, model, matrices, factories,
                                      K, bp)
                n_fail += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                n_vw += r["valid_wrong_stages"]
                fh.write(json.dumps({"cfg": tag, "block": blk,
                                     "exact_ok": bool(r["exact_ok"]),
                                     "undetected": bool(r["undetected"]),
                                     "valid_wrong": r["valid_wrong_stages"]}) + "\n")
        rows.append({"cfg": tag, "blocks": B, "failures": n_fail,
                     "undetected": n_und, "valid_wrong_total": n_vw,
                     "wall_s": time.perf_counter() - t0})
        print(tag, "fail", n_fail, "und", n_und, "vw", n_vw, flush=True)
    # P-c d=256 genie control (rebinned channel + same rebinned genie prior)
    ct = th_a.reshape(256, 4, 256, 4).sum(axis=(1, 3))
    cmod = _bcp(ct, encoding="NATURAL", order="LSB_FIRST")
    rng = np.random.default_rng(SEED + 9)
    n_fail = n_und = n_vw = 0
    # matrices for 8 planes: reuse SPC/PEG rule with measured h (quick)
    aks = np.arange(1024)
    a = rng.choice(aks, size=8192, p=pa_ch)
    delta = rng.choice(aks, size=8192, p=g_raw)
    ha_s = (a // 4).astype(np.int64)
    hb_s = ((a + delta) % 1024 // 4).astype(np.int64)
    h8 = []
    for bit in range(8):
        prev = np.stack([((ha_s >> i) & 1).astype(np.uint8) for i in range(bit)],
                        axis=0) if bit else np.empty((0, 8192), dtype=np.uint8)
        q = cmod.query(bit, hb_s, prev)
        p = np.clip(np.nan_to_num(np.asarray(q.p_one, dtype=np.float64),
                                  nan=0.5), 1e-12, 1.0 - 1e-12)
        h8.append(float((-(p * np.log2(p) + (1 - p) * np.log2(1 - p))).mean()))
    import math
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        make_group_factory,
        spc_matrix,
        split_groups,
    )
    gap = 2000 / 16384
    mats, facs = [], []
    for hh in h8:
        m = min(N - 1, max(1, int(math.ceil(N * (hh + gap)))))
        if m < 64:
            groups = split_groups(N, max(8, N // max(1, m)))
            mat = spc_matrix(groups, N)
            mats.append(mat)
            facs.append(make_group_factory(groups, "spc", 0))
        else:
            mat = build_peg_code(n=N, m=m, variable_degree=3).parity_check_matrix
            mats.append(mat)
            facs.append(functools.partial(make_bp_decoder, max_iter=200))
    t0 = time.perf_counter()
    with jl.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(B):
            a2 = rng.choice(aks, size=N, p=pa_ch)
            d2 = rng.choice(aks, size=N, p=g_raw)
            alice = (a2 // 4).astype(np.int64)
            bob = ((a2 + d2) % 1024 // 4).astype(np.int64)
            r = _decode_msd_block(alice, bob, cmod, mats, facs, K, bp)
            n_fail += 0 if r["exact_ok"] else 1
            n_und += 1 if r["undetected"] else 0
            n_vw += r["valid_wrong_stages"]
            fh.write(json.dumps({"cfg": "pc-d256-genie", "block": blk,
                                 "exact_ok": bool(r["exact_ok"]),
                                 "undetected": bool(r["undetected"]),
                                 "valid_wrong": r["valid_wrong_stages"]}) + "\n")
    rows.append({"cfg": "pc-d256-genie", "blocks": B, "failures": n_fail,
                 "undetected": n_und, "valid_wrong_total": n_vw,
                 "h8": [round(v, 4) for v in h8],
                 "wall_s": time.perf_counter() - t0})
    print("pc-d256-genie fail", n_fail, "und", n_und, "vw", n_vw, flush=True)
    (root / "d5_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
