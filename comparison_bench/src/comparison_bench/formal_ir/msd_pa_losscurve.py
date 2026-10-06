"""P-a log-loss vs training-mass curve + large-B decode mapping (T-review §3).

--ll: fit-mass ladder {1/8,1/4,1/2,1}x half_b + full TRAIN; eval = mean
  -log2 P(a|b,true-prefix-chain) on half_a REAL pairs (zero-decode, high power:
  every symbol contributes). Answers saturation.
--decode: 3 configs x B=300 on Tier1 bootstrap channel (fixed channel, prior
  varies): (mass1/4, m224), (mass full, m224), (mass1/4, m232). Maps (LL, m)
  to FER/f. m fixed per config (isolates prior effect).
R10 (channel/prior disjoint halves), R11 full-symbol, no new real frames.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

MASSES = (0.125, 0.25, 0.5, 1.0, "full")
B_DEC = 300
SEED = 20266000


def fit_table(frac, bh_a, bh_b, full_table):
    if frac == "full":
        return full_table
    rng = np.random.default_rng(20266001)
    sub = rng.choice(bh_a.size, size=int(bh_a.size * frac), replace=False)
    t = np.zeros((1024, 1024), dtype=np.float64)
    np.add.at(t, (bh_a[sub], bh_b[sub]), 1)
    return t


def chain_ll(fit: np.ndarray, ea: np.ndarray, eb: np.ndarray) -> dict:
    """Mean -log2 P(a|b,true-prefix) chain LL + per-plane breakdown."""
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
def chain_ll(fit: np.ndarray, ea: np.ndarray, eb: np.ndarray,
             eps: float = 1e-9) -> dict:
    """Mean -log2 P(a|b,true-prefix-chain) + per-plane breakdown.

    eps is a MEASUREMENT floor (stated): raw plug-in assigns exact 0 to unseen
    cells (infinite surprise = the overconfidence pathology itself). The
    zero-hit rate is reported alongside so the floor never hides it.
    """
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    model = build_conditional_prior_model(fit, encoding="NATURAL", order="LSB_FIRST")
    n = ea.size
    tot = 0.0
    per_plane = []
    zero_hits = 0
    prev_rows = []
    for bit in range(10):
        prev = np.stack(prev_rows, axis=0) if prev_rows else np.empty((0, n), dtype=np.uint8)
        q = model.query(bit, eb, prev)
        p_raw = np.asarray(q.p_one, dtype=np.float64)
        tb = ((ea >> bit) & 1).astype(np.float64)
        prob_true = np.where(tb == 1, p_raw, 1 - p_raw)
        zero_hits += int((prob_true == 0.0).sum())
        p = np.clip(prob_true, eps, 1.0)
        ll = (-np.log2(p)).mean()
        per_plane.append(float(ll))
        tot += float(ll)
        prev_rows.append(((ea >> bit) & 1).astype(np.uint8))
    return {"chain_ll": tot, "per_plane": per_plane, "n": n,
            "zero_hit_rate": zero_hits / (10 * n), "eps": eps}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ll", action="store_true")
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    z = np.load(proot / "T2-1M_tier_pairs.npz")
    ah = np.asarray(z["a_half_a"], dtype=np.int64)
    bh = np.asarray(z["b_half_a"], dtype=np.int64)
    zt = np.load(proot / "T2-1M_tier_tables.npz")
    bh_a = np.asarray(z["a_half_b"], dtype=np.int64)
    bh_b = np.asarray(z["b_half_b"], dtype=np.int64)
    if args.ll:
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
            load_train_table,
        )
        full = load_train_table("T2-1M")
        rows = []
        for frac in MASSES:
            fit = fit_table(frac, bh_a, bh_b, full)
            r = chain_ll(fit, ah, bh)
            rows.append({"prior_mass_frac_halfb": frac,
                         "prior_pairs": int(fit.sum()),
                         **r})
            print(frac, "pairs", int(fit.sum()), "LL", round(r["chain_ll"], 4),
                  flush=True)
        (root / "pa_llcurve.json").write_text(json.dumps(rows, indent=2),
                                              encoding="utf-8")
    if args.decode:
        import functools
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
            build_mixed_point,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
            plane_conditional_entropies,
            read_p1_scalars,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
            build_conditional_prior_model as _bcp,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
            _decode_msd_block,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
            make_bp_decoder,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
            summarize_m2,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
            load_train_table as _ltt,
        )
        full = _ltt("T2-1M")
        # CORRECTED mapping: plane-0 stays at C0-rule (it passes); the failing
        # stage under mismatch is plane-1, so vary PLANE-1 m across prior masses.
        # (mass, m1): does denser prior reduce required plane-1 m?
        cfgs = [("q14-m1_600", 0.25, 600), ("half-m1_600", 1.0, 600),
                ("full-m1_600", "full", 600), ("full-m1_1200", "full", 1200)]
        jl = root / "blocks_pa.jsonl"
        if jl.exists():
            jl.unlink()
        pts = []
        for tag, frac, m1 in cfgs:
            fit = fit_table(frac, bh_a, bh_b, full)
            model = _bcp(fit, encoding="NATURAL", order="LSB_FIRST")
            h = plane_conditional_entropies(fit)
            matrices, factories, _, m_list = build_mixed_point(16384, h, 2000, 32, 256)
            # override PLANE-1 rows only (plane-0 keeps C0-rule which passes)
            from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
                build_peg_code,
            )
            matrices[1] = build_peg_code(n=16384, m=m1, variable_degree=3).parity_check_matrix
            m_list[1] = m1
            l_base = int(sum(m_list))
            bp = functools.partial(make_bp_decoder, max_iter=200)
            rng = np.random.default_rng(SEED)
            n_fail = n_und = n_res = n_vw = n_p1f = 0
            s_att = [0] * 10
            s_pas = [0] * 10
            t0 = time.perf_counter()
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for blk in range(B_DEC):
                    pick = rng.choice(ah.size, size=16384, replace=True)
                    alice = ah[pick].astype(np.int64)
                    bob = bh[pick].astype(np.int64)
                    r = _decode_msd_block(alice, bob, model, matrices, factories,
                                          400, bp)
                    for s, ok in enumerate(r["stages_passed"]):
                        s_att[s] += 1
                        if ok:
                            s_pas[s] += 1
                    n_fail += 0 if r["exact_ok"] else 1
                    n_und += 1 if r["undetected"] else 0
                    n_res += 1 if r["rescued"] else 0
                    n_vw += r["valid_wrong_stages"]
                    n_p1f += 1 if r["plane1_failed"] else 0
                    fh.write(json.dumps({"cfg": tag, "block": blk,
                                         "exact_ok": bool(r["exact_ok"]),
                                         "undetected": bool(r["undetected"]),
                                         "rescued": bool(r["rescued"]),
                                         "valid_wrong": r["valid_wrong_stages"],
                                         "plane1_failed": bool(r["plane1_failed"])}) + "\n")
            wall = time.perf_counter() - t0
            pts.append({"cfg": tag, "N": 16384, "gap": f"pa-{tag}",
                        "blocks": B_DEC, "L_EC": l_base, "m_per_plane": m_list,
                        "L_base": l_base, "k_rescue": 400, "n_rescue": n_res,
                        "failures": n_fail, "undetected": n_und,
                        "valid_wrong_total": n_vw, "plane1_failed": n_p1f,
                        "stage_attempted": s_att, "stage_passed": s_pas,
                        "wall_s": wall, "s_per_block": wall / B_DEC,
                        "backend": "msd-pa", "max_iter": 200, "seed": SEED,
                        "source": "T2-1M"})
            print(tag, "fail", n_fail, "und", n_und, "vw", n_vw, "p1fail", n_p1f,
                  flush=True)
        scalars = read_p1_scalars()
        rows = summarize_m2(pts, scalars)
        (root / "pa_decode.json").write_text(json.dumps(rows, indent=2),
                                             encoding="utf-8")
        print(json.dumps([{k: r[k] for k in ("cfg", "failures", "undetected",
                                            "f_expected")} for r in rows], indent=2))


if __name__ == "__main__":
    main()
