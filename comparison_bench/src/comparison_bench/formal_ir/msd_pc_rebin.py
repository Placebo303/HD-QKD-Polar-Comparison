"""P-c density hypothesis (T-review §3): rebin TRAIN counts to (512,400) and
(256,800) WITHOUT reading raw (same span 204800 ps, frame length unchanged).
Channel = rebinned Tier1 bootstrap pairs; prior = rebinned half_b table.
MSD frozen chain per d (C0-rule gap from M2 operating, K rescue). Tests whether
prior sparsity is d=1024-specific: transfer success at coarser grids would
confirm it AND give MSD its first usable real-candidate operating point.
Full-symbol metric (R11). B=60/point.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

GRIDS = ((512, 2), (256, 4))  # (d, rebin_factor); bw = 200*factor
N = 16384
GAP = 2000 / 16384  # per-symbol operating gap carried from M2
K = 400
B = 60
SEED = 20266100
TAG_BITS = 64


def rebin_table(t: np.ndarray, f: int) -> np.ndarray:
    d = t.shape[0] // f
    return t.reshape(d, f, d, f).sum(axis=(1, 3))


def rebin_pairs(a: np.ndarray, b: np.ndarray, f: int):
    return (a // f).astype(np.int64), (b // f).astype(np.int64)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("P-c runs only with --full")
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
        read_p1_scalars,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
        build_mixed_point,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        make_group_factory,
        spc_matrix,
        split_groups,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
        load_tier_pairs,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
        summarize_m2,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    pa, pb = load_tier_pairs(proot, "T2-1M", "half_a")
    pt = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_b"])
    nbits = {512: 9, 256: 8}
    jl = root / "blocks_pc.jsonl"
    if jl.exists():
        jl.unlink()
    pts = []
    for d, f in GRIDS:
        nb = nbits[d]
        ct = rebin_table(pt, f)  # prior table (REVIEW: prior uses half_b)
        # NOTE: channel pairs must come from the SAME half_b population for an
        # R10-cleaner check? No: channel stays half_a (rebinned) = mismatch kept.
        ca, cb = rebin_pairs(pa, pb, f)
        model = build_conditional_prior_model(ct, encoding="NATURAL", order="LSB_FIRST")
        # per-plane conditional entropy on THIS grid (existing helper hardcodes
        # d=1024): E over channel mass of h2(P(bit|b,true prefix)), n=8192 sample
        rng_h = np.random.default_rng(20266111)
        hpick = rng_h.choice(ca.size, size=8192, replace=True)
        ha_s, hb_s = ca[hpick], cb[hpick]
        h = []
        for bit in range(nb):
            prev = np.stack([((ha_s >> i) & 1).astype(np.uint8) for i in range(bit)],
                            axis=0) if bit else np.empty((0, 8192), dtype=np.uint8)
            q = model.query(bit, hb_s, prev)
            # NOTE: upper clip must be REPRESENTABLE (1.0-1e-300 rounds to 1.0
            # in float64, making the clip a no-op -> 0*log2(0) NaN). Use 1e-12.
            p = np.clip(np.nan_to_num(np.asarray(q.p_one, dtype=np.float64),
                                        nan=0.5), 1e-12, 1.0 - 1e-12)
            h.append(float((-(p * np.log2(p) + (1 - p) * np.log2(1 - p))).mean()))
        assert len(h) == nb
        m_list = [min(N - 1, max(1, int(math.ceil(N * (hh + GAP))))) for hh in h]
        from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
            build_peg_code,
        )
        matrices, factories = [], []
        bp0 = functools.partial(make_bp_decoder, max_iter=200)
        for stage, m in enumerate(m_list):
            # planes with h~0 get SPC safety (mirror M1'b structure)
            if m < 64:
                groups = split_groups(N, max(8, N // max(1, m)))
                mat = spc_matrix(groups, N)
                matrices.append(mat)
                factories.append(make_group_factory(groups, "spc", 0))
            else:
                mat = build_peg_code(n=N, m=m, variable_degree=3).parity_check_matrix
                matrices.append(mat)
                factories.append(bp0)
        l_base = int(sum(m_list))
        bp = functools.partial(make_bp_decoder, max_iter=200)
        rng = np.random.default_rng(SEED)
        n_fail = n_und = n_res = n_vw = 0
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(B):
                pick = rng.choice(ca.size, size=N, replace=True)
                alice = ca[pick].astype(np.int64)
                bob = cb[pick].astype(np.int64)
                # _decode_msd_block assumes 10 planes; patch stage count via model
                r = _decode_msd_block(alice, bob, model, matrices, factories, K, bp)
                n_fail += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                n_res += 1 if r["rescued"] else 0
                n_vw += r["valid_wrong_stages"]
                fh.write(json.dumps({"d": d, "block": blk,
                                     "exact_ok": bool(r["exact_ok"]),
                                     "undetected": bool(r["undetected"]),
                                     "rescued": bool(r["rescued"]),
                                     "valid_wrong": r["valid_wrong_stages"]}) + "\n")
        wall = time.perf_counter() - t0
        # per-grid plug-in H(A|B), H(A) from the prior table (zero-decode)
        tot = ct.sum()
        pa_m = ct.sum(axis=1) / tot
        ha = float(-(pa_m[pa_m > 0] * np.log2(pa_m[pa_m > 0])).sum())
        with np.errstate(divide="ignore", invalid="ignore"):
            cond = ct / ct.sum(axis=0, keepdims=True)
        cond = np.nan_to_num(cond)
        hab = float(-(ct / tot * np.log2(np.maximum(cond, 1e-300))).sum())
        e_l = float(l_base + K * n_res / B)
        fer = n_fail / B
        denom = N * hab
        kept = N * ha - e_l
        f_grid = (e_l + TAG_BITS + kept * fer) / denom
        pts.append({"d": d, "bw": 200 * f, "N": N, "gap": f"pc-d{d}",
                    "blocks": B, "L_EC": l_base, "m_per_plane": [int(m) for m in m_list],
                    "L_base": l_base, "k_rescue": K, "n_rescue": n_res,
                    "failures": n_fail, "undetected": n_und,
                    "valid_wrong_total": n_vw, "H_A_grid": ha, "H_AB_grid": hab,
                    "E_L_grid": e_l, "FER_grid": fer, "f_grid": float(f_grid),
                    "stage_attempted": [], "stage_passed": [],
                    "wall_s": wall, "s_per_block": wall / B,
                    "backend": "msd-pc", "max_iter": 200, "seed": SEED,
                    "source": "T2-1M"})
        print(f"d={d}: fail {n_fail}/{B} und {n_und} vw {n_vw} L={l_base}", flush=True)
    (root / "pc_summary.json").write_text(json.dumps(pts, indent=2), encoding="utf-8")
    print("NOTE: f needs P1 H per (d,bw); H differs by grid — see log.")


if __name__ == "__main__":
    main()
