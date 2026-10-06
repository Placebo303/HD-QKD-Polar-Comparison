"""S-2 robust prior: zero-decode CV selection on TRAIN halves + proxy validation.

--select: candidates (sibling diff-pmf+bg [reuse sibling code], Gaussian/
  Laplacian jitter + bg, floored plug-in) fit on half / evaluated on other half
  (2-fold); metric = mean held-out log-likelihood/pair + calibration buckets.
--validate: winner -> pseudo-counts -> MSD retune on S-1 Tier1 (m_0 from winner
  h, K ladder); target f<=1.30, valid-wrong=0, top-2 stability. Tier1 primary.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

Q = 1024


def load_half_pairs(root: Path, source: str, half: str):
    z = np.load(root / f"{source}_tier_pairs.npz")
    if half == "a":
        return (np.asarray(z["a_half_a"], dtype=np.int64),
                np.asarray(z["b_half_a"], dtype=np.int64))
    if half == "b":
        return (np.asarray(z["a_half_b"], dtype=np.int64),
                np.asarray(z["b_half_b"], dtype=np.int64))
    raise ValueError("half must be a or b")


def counts_from_pairs(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    t = np.zeros((Q, Q), dtype=np.float64)
    np.add.at(t, (a, b), 1)
    return t


def ll_diffpmf(fit: np.ndarray, held_a: np.ndarray, held_b: np.ndarray,
               alpha: float, beta: float) -> float:
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    g = np.asarray(mc.smooth_difference_counts(
        mc.difference_pmf(fit, Q), Q, alpha), dtype=np.float64)
    d = (held_b - held_a) % Q
    p = (1 - beta) * g[d] + beta / Q
    return float(np.log(np.maximum(p, 1e-300)).sum() / held_a.size)


def _kernel_table(sigma: float, lap: bool) -> tuple[np.ndarray, np.ndarray]:
    """Precomputed kernel K[d], d=0..1023 + per-a normalizers Z[a] (linear, no wrap)."""
    aks = np.arange(Q, dtype=np.float64)
    dd = np.abs(aks[None, :] - aks[:, None])
    if lap:
        k = np.exp(-dd / sigma) / (2 * sigma)
    else:
        k = np.exp(-0.5 * (dd / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))
    z = k.sum(axis=1)
    return k / z[:, None], z


def ll_gauss(ktab: np.ndarray, held_a: np.ndarray, held_b: np.ndarray,
             eps: float) -> float:
    p = (1 - eps) * ktab[held_a, held_b] + eps / Q
    return float(np.log(np.maximum(p, 1e-300)).sum() / held_a.size)


def ll_floored(fit: np.ndarray, held_a: np.ndarray, held_b: np.ndarray,
               floor: float) -> float:
    col = fit.sum(axis=0)
    col[col == 0] = 1.0
    cond = fit / col[None, :]
    q = np.maximum(cond, floor)
    q = q / q.sum(axis=0, keepdims=True)
    return float(np.log(np.maximum(q[held_a, held_b], 1e-300)).sum() / held_a.size)


def calibration(fit_cond, held_a, held_b, nbins: int = 10) -> list:
    import numpy as np
    p = np.clip(fit_cond[held_a, held_b], 0, 1)
    edges = np.linspace(0, 1, nbins + 1)
    out = []
    for i in range(nbins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i + 1 < nbins else p <= 1.0)
        if m.sum() == 0:
            continue
        out.append({"bin": [float(edges[i]), float(edges[i + 1])], "n": int(m.sum()),
                    "mean_pred": float(p[m].mean())})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--floors", default="1e-4")
    ap.add_argument("--validate-t3", action="store_true")
    args = ap.parse_args()
    root = Path(args.proxy_root)
    res = {}
    for source in ("T2-1M",):
        ah, bh = load_half_pairs(root, source, "a")
        bh_a, bh_b = load_half_pairs(root, source, "b")
        th = counts_from_pairs(ah, bh)
        th_b = counts_from_pairs(bh_a, bh_b)
        # held-out REAL pair lists (fold1: fit-a/eval-b; fold2: fit-b/eval-a)
        n1, n2 = min(40000, bh_a.size), min(40000, ah.size)
        eb_a, eb_b = bh_a[:n1], bh_b[:n1]
        ea_a, ea_b = ah[:n2], bh[:n2]
        rows = {}
        for alpha in (0.5, 1.0, 2.0, 4.0):
            for beta in (0.0, 1e-4, 1e-3):
                l1 = ll_diffpmf(th, eb_a, eb_b, alpha, beta)
                l2 = ll_diffpmf(th_b, ea_a, ea_b, alpha, beta)
                rows[f"diffpmf/a{alpha}/b{beta}"] = (l1 + l2) / 2
        for sigma in (1.0, 2.0, 4.0):
            for lap in (False, True):
                ktab, _ = _kernel_table(sigma, lap)
                for eps in (1e-4, 1e-3, 1e-2):
                    l1 = ll_gauss(ktab, eb_a, eb_b, eps)
                    l2 = ll_gauss(ktab, ea_a, ea_b, eps)
                    rows[f"{'lap' if lap else 'gauss'}/s{sigma}/e{eps}"] = (l1 + l2) / 2
        for fl in (1e-4, 1e-3, 3e-3, 1e-2):
            l1 = ll_floored(th, eb_a, eb_b, fl)
            l2 = ll_floored(th_b, ea_a, ea_b, fl)
            rows[f"floor/f{fl}"] = (l1 + l2) / 2
        order = sorted(rows.items(), key=lambda kv: kv[1], reverse=True)
        res[source] = {"rows": {k: round(v, 5) for k, v in order},
                       "best": order[0][0], "best_ll": round(order[0][1], 5),
                       "n_eval": [int(n1), int(n2)]}
        print(source, "best", order[0][0], round(order[0][1], 5))
        for k, v in order[:8]:
            print("   ", k, round(v, 5))
    if args.select and not args.validate:
        Path(args.output).write_text(json.dumps(res, indent=2), encoding="utf-8")
    if args.validate:
        out = validate_winner(Path(args.proxy_root),
                              [float(x) for x in args.floors.split(",")])
    if args.validate_t3:
        out3 = validate_t3(Path(args.proxy_root))
        out = {"t3": out3}
    if args.validate or args.validate_t3:
        Path(args.output).write_text(
            json.dumps({"select": res if args.select else "see-existing",
                        "validate": out}, indent=2), encoding="utf-8")


def validate_t3(root: Path) -> dict:
    """Cross-time tier: channel = VAL/HOLD bootstrap pairs, prior = FULL TRAIN.

    Variants: unfloored plug-in (fidelity check: must reproduce M5 100% fail),
    floored 1e-4, diff-pmf a=1 (both must decode to deliver S-2). Plus NB R1
    arm (M0-style, full-TRAIN bundle). B=60 MSD / 60 NB, T2-1M.
    """
    import functools
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
        plane_conditional_entropies,
        read_p1_scalars,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
        summarize_m2,
    )

    source = "T2-1M"
    full = load_train_table(source)
    zh = np.load(root / f"{source}_tier3_pairs.npz")
    ha_all, hb_all = (np.asarray(zh["a_hold"], dtype=np.int64),
                      np.asarray(zh["b_hold"], dtype=np.int64))
    variants = [("unfloored",
                 build_conditional_prior_model(full, encoding="NATURAL", order="LSB_FIRST")),
                ("floor1e-4", None), ("diffpmf-a1", None)]
    base_full = variants[0][1]
    variants[1] = ("floor1e-4", floored_model(base_full, 1e-4))
    _dm, _dp = diffpmf_model(full, 1.0)
    variants[2] = ("diffpmf-a1", _dm)
    msd_out, msd_pts = [], []
    for name, model in variants:
        if name == "diffpmf-a1":
            hh = plane_conditional_entropies(_dp)
        else:
            hh = plane_conditional_entropies(full)
        matrices, factories, _, m_list = build_mixed_point(16384, hh, 2000, 32, 256)
        l_base = int(sum(m_list))
        bp = functools.partial(make_bp_decoder, max_iter=200)
        rng = np.random.default_rng(20263700)
        n_fail = n_und = n_res = n_vw = n_p1f = 0
        t0 = time.perf_counter()
        for blk in range(60):
            pick = rng.choice(ha_all.size, size=16384, replace=True)
            alice = ha_all[pick].astype(np.int64)
            bob = hb_all[pick].astype(np.int64)
            r = _decode_msd_block(alice, bob, model, matrices, factories, 400, bp)
            n_fail += 0 if r["exact_ok"] else 1
            n_und += 1 if r["undetected"] else 0
            n_res += 1 if r["rescued"] else 0
            n_vw += r["valid_wrong_stages"]
            n_p1f += 1 if r["plane1_failed"] else 0
        wall = time.perf_counter() - t0
        msd_out.append({"model": name, "K": 400, "L_base": l_base, "n_rescue": n_res,
                        "failures": n_fail, "undetected": n_und,
                        "valid_wrong_total": n_vw, "plane1_failed": n_p1f,
                        "blocks": 60, "wall_s": wall})
        msd_pts.append({"source": source, "N": 16384, "gap": f"s2t3-{name}",
                        "blocks": 60, "L_EC": l_base,
                        "m_per_plane": [], "h_per_plane": [],
                        "L_base": l_base, "k_rescue": 400, "n_rescue": n_res,
                        "failures": n_fail, "undetected": n_und,
                        "stage_attempted": [], "stage_passed": [],
                        "s_per_block": wall / 60, "backend": "msd-s2t3",
                        "max_iter": 200, "seed": 0})
        print("T3", name, "fail", n_fail, "und", n_und, "vw", n_vw,
              "p1fail", n_p1f, flush=True)
    # NB R1 arm on T3 channel, full-TRAIN bundle (M0-style)
    from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
        derive_bundle,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_s2c_campaign as _s2c,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as _peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _qq,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        v80_b2f_campaign as _b2f,
    )
    from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
        p1_stage1_runner as _p1,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    bundle = _s2c.bind_empirical_bundle(derive_bundle(full))
    pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                   _p1.production_rank_fn)
    field = _GF.create(32)
    dense = {k: _peg.sparse_to_dense(
        pinned["base" if k == "base" else "full"]["triples"], 1024,
        200 if k == "base" else 208, field) for k in ("base", "full")}
    rng = np.random.default_rng(20263799)
    nb_fail = nb_und = nb_res = nb_u1 = 0
    t0 = time.perf_counter()
    for blk in range(60):
        pick = rng.choice(ha_all.size, size=1024, replace=True)
        alice = ha_all[pick].astype(np.int64)
        bob = hb_all[pick].astype(np.int64)
        x = alice & 31
        y = bob & 31
        outs = []
        for key in ("base", "full"):
            if key == "full" and outs and bool(outs[0]["exact_match"]):
                break
            prior = _s2c.center_rows_prior(
                _b2f.marginal_prior_l2(bundle, bob), y)
            sxx = _qq.syndrome_of(field, dense[key], x.tolist())
            res = _v28.decode_error_domain_posterior(
                field, y.tolist(), dense[key], sxx, prior, 300)
            xh = res.get("x_hat")
            ex = xh is not None and bool(np.array_equal(np.asarray(xh), x))
            outs.append({"exact_match": ex,
                         "reconstruction_ok": bool(res.get("reconstruction_ok", False))})
        umm = int((((np.asarray(_m0.recover_u1(bundle, bob, x))) != ((alice >> 5) & 31))).sum())
        fin = outs[0] if outs[0]["exact_match"] else (outs[1] if len(outs) > 1 else outs[0])
        rescued = len(outs) > 1
        exact = bool(fin["exact_match"])
        full_ok = exact and umm == 0
        nb_fail += 0 if full_ok else 1
        if (not exact) and bool(fin["reconstruction_ok"]):
            nb_und += 1
        nb_res += 1 if rescued else 0
        nb_u1 += umm
    wall = time.perf_counter() - t0
    scalars = read_p1_scalars()
    rows = summarize_m2(msd_pts, scalars)
    return {"msd": rows,
            "msd_raw": msd_out,
            "nb": {"failures": nb_fail, "undetected": nb_und, "rescued": nb_res,
                   "u1_mm_total": nb_u1, "blocks": 60, "wall_s": wall,
                   "u1_per_block": nb_u1 / 60},
            "target": "unfloored reproduces M5 100% fail; a robust variant decodes"}


def floored_model(base, floor: float):
    """Same-type copy with bit-conditionals clipped to [floor, 1-floor] (S-2).

    Returns a genuine ConditionalPriorModel (frozen gates pass). MAP base
    changes only when p crosses 0.5 (rare); main effect is finite error
    weights (no inf-pinning, contradictions survivable)."""
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        ConditionalPriorModel,
        ConditionalPriorStage,
    )

    stages = []
    for s in base.stages:
        p = np.clip(np.asarray(s.p_one_by_bob_prefix, dtype=np.float64),
                    floor, 1.0 - floor)
        stages.append(ConditionalPriorStage(
            alice_bit_index_from_lsb=int(s.alice_bit_index_from_lsb),
            p_one_by_bob_prefix=p,
            support_by_bob_prefix=np.asarray(s.support_by_bob_prefix)))
    return ConditionalPriorModel(
        alphabet_size=int(base.alphabet_size), encoding=str(base.encoding),
        order_name=str(base.order_name),
        bit_order_from_lsb=tuple(int(v) for v in base.bit_order_from_lsb),
        stages=tuple(stages))


def diffpmf_model(fit_table: np.ndarray, alpha: float):
    """Genuine prior model from sibling diff-pmf smoothing (mass-dependent).

    joint[a,b] = P_fit(a) * g[(b-a) % 1024]; pseudo-counts scaled to fit mass.
    Unlike global flooring, confident cells with large TRAIN mass keep weight.
    """
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    tot = fit_table.sum()
    g = np.asarray(mc.smooth_difference_counts(
        mc.difference_pmf(fit_table, 1024), 1024, alpha), dtype=np.float64)
    pa = fit_table.sum(axis=1) / tot
    aks = np.arange(1024)
    joint = pa[:, None] * g[(aks[None, :] - aks[:, None]) % 1024]
    joint = joint / joint.sum()
    pseudo = joint * tot
    return (build_conditional_prior_model(pseudo, encoding="NATURAL",
                                          order="LSB_FIRST"), pseudo)


def validate_winner(root: Path, floors: list[float]) -> dict:
    import functools
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
        build_mixed_point,
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        read_p1_scalars,
    )

    source = "T2-1M"
    th_b = np.asarray(np.load(root / f"{source}_tier_tables.npz")["half_b"])
    base_model = build_conditional_prior_model(th_b, encoding="NATURAL",
                                               order="LSB_FIRST")
    h = plane_conditional_entropies(th_b)
    matrices, factories, _, m_list = build_mixed_point(16384, h, 2000, 32, 256)
    l_base = int(sum(m_list))
    pa, pb = load_tier_pairs(root, source, "half_a")
    bp = functools.partial(make_bp_decoder, max_iter=200)
    out = []
    for fl in floors:
        model = floored_model(base_model, fl)
        name = f"floor{fl:g}"
        for k in (400,):
            rng = np.random.default_rng(20263300 + k + abs(hash(name)) % 1000)
            n_fail = n_und = n_res = n_vw = 0
            t0 = time.perf_counter()
            for blk in range(100):
                pick = rng.choice(pa.size, size=16384, replace=True)
                alice = pa[pick].astype(np.int64)
                bob = pb[pick].astype(np.int64)
                r = _decode_msd_block(alice, bob, model, matrices, factories, k, bp)
                n_fail += 0 if r["exact_ok"] else 1
                n_und += 1 if r["undetected"] else 0
                n_res += 1 if r["rescued"] else 0
                n_vw += r["valid_wrong_stages"]
            wall = time.perf_counter() - t0
            out.append({"model": name, "K": k, "L_base": l_base, "n_rescue": n_res,
                        "failures": n_fail, "undetected": n_und,
                        "valid_wrong_total": n_vw, "blocks": 100,
                        "wall_s": wall})
            print(name, "K", k, "fail", n_fail, "und", n_und, "vw", n_vw,
                  "rescue", n_res, flush=True)
    # runner-up sensitivity: Laplacian prior with winner matrices (same code)
    lap_model = _LaplacianModel(th_b, 1.0, 1e-4)
    rng = np.random.default_rng(20263399)
    n_fail = n_und = n_vw = n_res = 0
    for blk in range(100):
        pick = rng.choice(pa.size, size=16384, replace=True)
        alice = pa[pick].astype(np.int64)
        bob = pb[pick].astype(np.int64)
        r = _decode_msd_block(alice, bob, lap_model, matrices, factories, 400, bp)
        n_fail += 0 if r["exact_ok"] else 1
        n_und += 1 if r["undetected"] else 0
        n_res += 1 if r["rescued"] else 0
        n_vw += r["valid_wrong_stages"]
    out.append({"model": "lap-s1-e1e-4-sens", "K": 400, "L_base": l_base,
                "n_rescue": n_res, "failures": n_fail, "undetected": n_und,
                "valid_wrong_total": n_vw, "blocks": 100, "wall_s": 0.0})
    print("lap-sens", "fail", n_fail, "und", n_und, "vw", n_vw, flush=True)
    # f via shared M2 shape
    scalars = read_p1_scalars()
    # diff-pmf validation (sibling recipe, mass-dependent smoothing)
    for alpha in (1.0, 2.0, 4.0):
        th_b = np.asarray(np.load(root / f"{source}_tier_tables.npz")["half_b"])
        dmodel, dpseudo = diffpmf_model(th_b, alpha)
        from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
            plane_conditional_entropies as _hfun,
        )
        dh = _hfun(dpseudo)
        dmat, dfac, _, dm_list = build_mixed_point(16384, dh, 2000, 32, 256)
        dl_base = int(sum(dm_list))
        pa, pb = load_tier_pairs(root, source, "half_a")
        rng = np.random.default_rng(20263500 + int(alpha))
        n_fail = n_und = n_res = n_vw = 0
        t0 = time.perf_counter()
        for blk in range(100):
            pick = rng.choice(pa.size, size=16384, replace=True)
            alice = pa[pick].astype(np.int64)
            bob = pb[pick].astype(np.int64)
            r = _decode_msd_block(alice, bob, dmodel, dmat, dfac, 400, bp)
            n_fail += 0 if r["exact_ok"] else 1
            n_und += 1 if r["undetected"] else 0
            n_res += 1 if r["rescued"] else 0
            n_vw += r["valid_wrong_stages"]
        wall = time.perf_counter() - t0
        out.append({"model": f"diffpmf-a{alpha:g}", "K": 400, "L_base": dl_base,
                    "n_rescue": n_res, "failures": n_fail, "undetected": n_und,
                    "valid_wrong_total": n_vw, "blocks": 100, "wall_s": wall})
        print(f"diffpmf-a{alpha:g}", "fail", n_fail, "und", n_und, "vw", n_vw,
              flush=True)
    pts = [{**r, "source": source, "N": 16384, "gap": f"s2-{r['model']}-K{r['K']}",
            "L_EC": r["L_base"], "m_per_plane": [], "h_per_plane": [],
            "stage_attempted": [], "stage_passed": [],
            "s_per_block": r["wall_s"] / 100, "backend": "msd-s2",
            "max_iter": 200, "seed": 0} for r in out]
    for p, r in zip(pts, out):
        p["k_rescue"] = r["K"]
    rows = summarize_m2(pts, scalars)
    return {"points": rows,
            "target": "f<=1.30, valid-wrong=0, top-2 stability"}


class _LaplacianModel:
    """Bit-conditional prior from Laplacian-jitter joint (sensitivity probe).

    Returns the genuine ConditionalPriorModel built from pseudo-counts
    (frozen gates pass); no wrapper."""

    def __new__(cls, fit_table: np.ndarray, sigma: float, eps: float):
        from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
            build_conditional_prior_model,
        )
        tot = fit_table.sum()
        aks = np.arange(1024, dtype=np.float64)
        dd = np.abs(aks[None, :] - aks[:, None])
        k = np.exp(-dd / sigma) / (2 * sigma)
        k = k / k.sum(axis=1, keepdims=True)
        pa = fit_table.sum(axis=1) / tot
        joint = ((1 - eps) * k + eps / 1024) * pa[:, None]
        pseudo = joint / joint.sum() * tot
        return build_conditional_prior_model(pseudo, encoding="NATURAL",
                                             order="LSB_FIRST")


if __name__ == "__main__":
    main()
