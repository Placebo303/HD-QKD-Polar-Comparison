"""E-3 d256-genie double-gap control (artifacted): rate-adequacy arithmetic
retained + block records. Tests whether coarse-grid failure is a rate problem.
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
B = 60
K = 400
SEED = 20266800


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("E-3 runs only with --full")
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        make_group_factory,
        spc_matrix,
        split_groups,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_d3_physproxy import (  # noqa: E402
        fit_diff,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    th_a = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_a"])
    assert th_a.sum() > 100000, "proxy tables"
    pa_ch, g_ch = fit_diff(th_a)
    ct = th_a.reshape(256, 4, 256, 4).sum(axis=(1, 3))
    model = build_conditional_prior_model(ct, encoding="NATURAL", order="LSB_FIRST")
    rng = np.random.default_rng(20266800)
    aks = np.arange(1024)
    a = rng.choice(aks, size=8192, p=pa_ch)
    delta = rng.choice(aks, size=8192, p=g_ch)
    ha_s = (a // 4).astype(np.int64)
    hb_s = ((a + delta) % 1024 // 4).astype(np.int64)
    h8 = []
    for bit in range(8):
        prev = np.stack([((ha_s >> i) & 1).astype(np.uint8) for i in range(bit)],
                        axis=0) if bit else np.empty((0, 8192), dtype=np.uint8)
        q = model.query(bit, hb_s, prev)
        p = np.clip(np.nan_to_num(np.asarray(q.p_one, dtype=np.float64),
                                  nan=0.5), 1e-12, 1.0 - 1e-12)
        h8.append(float((-(p * np.log2(p) + (1 - p) * np.log2(1 - p))).mean()))
    jl = root / "blocks_e3.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    bp0 = functools.partial(make_bp_decoder, max_iter=200)
    rows = []
    for mult in (1.0, 2.0):
        gap = 2000 / 16384 * mult
        m_list = [min(N - 1, max(1, int(math.ceil(N * (hh + gap))))) for hh in h8]
        matrices, factories = [], []
        for m in m_list:
            if m < 64:
                groups = split_groups(N, max(8, N // max(1, m)))
                mat = spc_matrix(groups, N)
                matrices.append(mat)
                factories.append(make_group_factory(groups, "spc", 0))
            else:
                mat = build_peg_code(n=N, m=m, variable_degree=3).parity_check_matrix
                matrices.append(mat)
                factories.append(bp0)
        rng2 = np.random.default_rng(20266899)
        nf = n_und = 0
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(B):
                a2 = rng2.choice(aks, size=N, p=pa_ch)
                d2 = rng2.choice(aks, size=N, p=g_ch)
                alice = (a2 // 4).astype(np.int64)
                bob = ((a2 + d2) % 1024 // 4).astype(np.int64)
                r = _decode_msd_block(alice, bob, model, matrices, factories,
                                      400, bp0)
                nf += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                fh.write(json.dumps({"gap_mult": mult, "block": blk,
                                     "exact_ok": bool(r["exact_ok"]),
                                     "undetected": bool(r["undetected"])}) + "\n")
        rows.append({"gap_mult": mult, "h8": [round(v, 4) for v in h8],
                     "m_list": m_list, "blocks": B, "failures": nf,
                     "undetected": n_und,
                     "wall_s": time.perf_counter() - t0})
        print(f"gap x {mult}: fail {nf}/{B}", flush=True)
    (root / "e3_summary.json").write_text(json.dumps(rows, indent=2),
                                          encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
