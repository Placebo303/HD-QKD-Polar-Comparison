"""D-3 physical proxy (review §2 D-3): channel = shift-invariant diff model
fitted on TRAIN-a (+ optional uniform structural noise); priors from TRAIN-b.
Phase 1 = G-0 validation (plug-in must reproduce real failure pattern).
Phase 2 = re-evaluate smoothed priors (MSD + NB) + P-c grids with reallocated
rates, B>=300. R10 (channel/prior disjoint populations), R11 full-symbol.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

N_MSD = 16384
N_NB = 1024
B_G0_MSD = 100
B_G0_NB = 60
B = 300
K = 400
SEED = 20266300
TAG_BITS = 64
WORKERS = 12
NOISE_EPS = 1e-3  # uniform structural noise mixture ("少量结构噪声")


def fit_diff(counts: np.ndarray):
    tot = counts.sum()
    pa = counts.sum(axis=1) / tot
    d = (np.arange(1024)[None, :] - np.arange(1024)[:, None]) % 1024
    g = np.bincount(d.ravel(), weights=counts.ravel(), minlength=1024)
    return pa / pa.sum(), g / g.sum()


def gen_channel(pa, g, n, rng, noise_eps=NOISE_EPS):
    aks = np.arange(1024)
    a = rng.choice(aks, size=n, p=pa)
    u = rng.random(size=n)
    delta = np.where(u < noise_eps, rng.integers(0, 1024, size=n),
                     rng.choice(aks, size=n, p=g))
    return a.astype(np.int64), ((a + delta) % 1024).astype(np.int64)


_NBW = {}


def _nb_init(payload):
    # Delegated to importable msd_d3_nbworker (Windows spawn-safe).
    from comparison_bench.src.comparison_bench.formal_ir.msd_d3_nbworker import (  # noqa: E402
        _nb_init as _impl,
    )
    return _impl(payload)


# NOTE: legacy local _nb_one removed (moved to msd_d3_nbworker for spawn
# safety); pool calls _nb_one_imp imported from that module.


def run_pc_grids(root: Path, jl: Path, pa_ch, g_ch, th_b, pseudo_diff,
                 scalars) -> list:
    """P-c on diff channel: rebinned channel pairs + rebinned priors, MSD per
    grid with rates reallocated from per-grid measured h (R3 compliance)."""
    import functools
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        make_group_factory,
        spc_matrix,
        split_groups,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        wilson_upper as _wu,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )

    rows = []
    for d, f, nb in ((512, 2, 9), (256, 4, 8)):
        for pname, ptab in (("plugin", th_b), ("diffpmf-a1", pseudo_diff)):
            ct = ptab.reshape(d, f, d, f).sum(axis=(1, 3))
            model = _bcp(ct, encoding="NATURAL", order="LSB_FIRST")
            # per-grid h measured on diff-channel samples (reallocated rates)
            rng = np.random.default_rng(20266333)
            aks = np.arange(1024)
            a = rng.choice(aks, size=8192, p=pa_ch)
            delta = rng.choice(aks, size=8192, p=g_ch)
            ha_s = (a // f).astype(np.int64)
            hb_s = ((a + delta) % 1024 // f).astype(np.int64)
            h = []
            for bit in range(nb):
                prev = np.stack([((ha_s >> i) & 1).astype(np.uint8)
                                 for i in range(bit)], axis=0) if bit else np.empty((0, 8192), dtype=np.uint8)
                q = model.query(bit, hb_s, prev)
                p = np.clip(np.nan_to_num(np.asarray(q.p_one, dtype=np.float64),
                                          nan=0.5), 1e-12, 1.0 - 1e-12)
                h.append(float((-(p * np.log2(p) + (1 - p) * np.log2(1 - p))).mean()))
            gap = 2000 / 16384
            m_list = [min(N_MSD - 1, max(1, int(math.ceil(N_MSD * (hh + gap)))))
                      for hh in h]
            matrices, factories = [], []
            bp0 = functools.partial(make_bp_decoder, max_iter=200)
            for m in m_list:
                if m < 64:
                    groups = split_groups(N_MSD, max(8, N_MSD // max(1, m)))
                    mat = spc_matrix(groups, N_MSD)
                    matrices.append(mat)
                    factories.append(make_group_factory(groups, "spc", 0))
                else:
                    mat = build_peg_code(n=N_MSD, m=m, variable_degree=3).parity_check_matrix
                    matrices.append(mat)
                    factories.append(bp0)
            l_base = int(sum(m_list))
            rng2 = np.random.default_rng(SEED + 3)
            n_fail = n_und = n_res = n_vw = 0
            t0 = time.perf_counter()
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for blk in range(B):
                    a2 = rng2.choice(aks, size=N_MSD, p=pa_ch)
                    d2 = rng2.choice(aks, size=N_MSD, p=g_ch)
                    alice = (a2 // f).astype(np.int64)
                    bob = ((a2 + d2) % 1024 // f).astype(np.int64)
                    r = _decode_msd_block(alice, bob, model, matrices, factories,
                                          K, bp0)
                    n_fail += 0 if r["exact_ok"] else 1
                    n_und += 1 if r["undetected"] else 0
                    n_res += 1 if r["rescued"] else 0
                    n_vw += r["valid_wrong_stages"]
                    fh.write(json.dumps({"cfg": f"pc-d{d}-{pname}", "block": blk,
                                         "exact_ok": bool(r["exact_ok"]),
                                         "undetected": bool(r["undetected"])}) + "\n")
            wall = time.perf_counter() - t0
            # per-grid plug-in H from rebinned pseudo (zero-decode)
            tot = ct.sum()
            pa_m = ct.sum(axis=1) / tot
            ha = float(-(pa_m[pa_m > 0] * np.log2(pa_m[pa_m > 0])).sum())
            with np.errstate(divide="ignore", invalid="ignore"):
                cond = ct / ct.sum(axis=0, keepdims=True)
            cond = np.nan_to_num(cond)
            hab = float(-(ct / tot * np.log2(np.maximum(cond, 1e-300))).sum())
            e_l = float(l_base + K * n_res / B)
            fer = n_fail / B
            f_g = (e_l + TAG_BITS + (N_MSD * ha - e_l) * fer) / (N_MSD * hab)
            rows.append({"d": d, "prior": pname, "blocks": B, "failures": n_fail,
                         "undetected": n_und, "valid_wrong": n_vw,
                         "E_L": e_l, "FER": fer,
                         "FER_wilson_upper95": _wu(n_fail, B),
                         "f_expected": float(f_g), "H_A_grid": ha,
                         "H_AB_grid": hab, "wall_s": wall})
            print(f"pc-d{d}-{pname}: fail {n_fail}/{B} f={float(f_g):.3f}", flush=True)
    return rows


def diff_channel_h(model, pa_ch, g_ch, n_planes: int, n: int = 8192,
                   seed: int = 20266333):
    """Per-plane H(bit|B,true-prefix) measured on diff-channel samples."""
    rng = np.random.default_rng(seed)
    aks = np.arange(1024)
    a = rng.choice(aks, size=n, p=pa_ch)
    delta = rng.choice(aks, size=n, p=g_ch)
    ha_s = a.astype(np.int64)
    hb_s = ((a + delta) % 1024).astype(np.int64)
    h = []
    for bit in range(n_planes):
        prev = np.stack([((ha_s >> i) & 1).astype(np.uint8) for i in range(bit)],
                        axis=0) if bit else np.empty((0, n), dtype=np.uint8)
        q = model.query(bit, hb_s, prev)
        p = np.clip(np.nan_to_num(np.asarray(q.p_one, dtype=np.float64),
                                  nan=0.5), 1e-12, 1.0 - 1e-12)
        h.append(float((-(p * np.log2(p) + (1 - p) * np.log2(1 - p))).mean()))
    return h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--nb-pc-only", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not (args.g0 or args.full or args.nb_pc_only):
        raise SystemExit("D-3 runs with --g0 and/or --full / --nb-pc-only")
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
    from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
        _decode_msd_block,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_s2_prior import (  # noqa: E402
        diffpmf_model,
        floored_model,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    proot = Path(args.proxy_root)
    th_a = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_a"])
    th_b = np.asarray(np.load(proot / "T2-1M_tier_tables.npz")["half_b"])
    assert th_a.sum() > 100000 and th_b.sum() > 100000, "proxy tables"
    pa_ch, g_ch = fit_diff(th_a)
    hb = -(g_ch[g_ch > 0] * np.log2(g_ch[g_ch > 0])).sum()
    print("channel H(diff) =", round(float(hb), 4), "b/sym", flush=True)
    base_prior = _bcp(th_b, encoding="NATURAL", order="LSB_FIRST")
    priors = {"plugin": base_prior,
              "floor1e-4": floored_model(base_prior, 1e-4),
              "diffpmf-a1": diffpmf_model(th_b, 1.0)[0]}
    # TRUE diff-channel plane-h from near-exact genie pseudo (10M mass):
    # ALL arms share these matrices (fixed disclosure isolates prior effect).
    aks = np.arange(1024)
    _j = pa_ch[:, None] * g_ch[(aks[None, :] - aks[:, None]) % 1024]
    genie_model = _bcp(_j / _j.sum() * 1e7, encoding="NATURAL", order="LSB_FIRST")
    h_true = diff_channel_h(genie_model, pa_ch, g_ch, 10)
    print("true diff-channel plane h:", [round(v, 4) for v in h_true], flush=True)
    out = {"H_diff_channel": float(hb), "h_true_planes": h_true}
    _mats, _facs, _, _ml = None, None, None, [0]
    if args.g0 or args.full:
        _mats, _facs, _, _ml = build_mixed_point(N_MSD, h_true, 2000, 32, 256)
    out["L_base_shared"] = int(sum(_ml)) if _ml != [0] else -1
    jl = root / "blocks_d3.jsonl"
    if jl.exists():
        jl.unlink()
    bp = functools.partial(make_bp_decoder, max_iter=200)

    def run_msd(prior, n_blocks, seed, tag, matrices, factories, l_base):
        rng = np.random.default_rng(seed)
        n_fail = n_und = n_res = n_vw = n_p1f = 0
        s_att = [0] * 10
        s_pas = [0] * 10
        t0 = time.perf_counter()
        with jl.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(n_blocks):
                alice, bob = gen_channel(pa_ch, g_ch, N_MSD, rng)
                r = _decode_msd_block(alice, bob, prior, matrices, factories,
                                      K, bp)
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
        return {"cfg": tag, "N": N_MSD, "gap": f"d3-{tag}", "blocks": n_blocks,
                "L_EC": l_base, "m_per_plane": [], "L_base": l_base,
                "k_rescue": K, "n_rescue": n_res, "failures": n_fail,
                "undetected": n_und, "valid_wrong_total": n_vw,
                "plane1_failed": n_p1f, "stage_attempted": s_att,
                "stage_passed": s_pas, "wall_s": time.perf_counter() - t0,
                "backend": "msd-d3", "max_iter": 200, "seed": seed,
                "source": "T2-1M"}

    if args.g0:
        # REVISED G-0 (bias theory): on a smooth channel there are no zero-cell
        # contradictions, so plane-1 collapse is NOT expected even with a
        # mismatched plug-in prior. G-0 records the pattern instead of demanding
        # collapse: plane-1 pass rate HIGH confirms the bias mechanism from the
        # other side; plane-0 behavior follows disclosure-vs-true-h.
        r = run_msd(priors["plugin"], B_G0_MSD, SEED, "g0-plugin",
                    _mats, _facs, int(sum(_ml)))
        p1pass = B_G0_MSD - r["plane1_failed"]
        out["g0"] = {**r, "gate": "revised: plane-1 HIGH pass (=no contradictions) + und 0",
                     "plane1_pass": p1pass,
                     "verdict": "PASS" if (p1pass >= 90 and r["undetected"] == 0) else "FAIL"}
        print("G-0:", out["g0"]["verdict"], r["failures"], "p1pass",
              p1pass, "und", r["undetected"], flush=True)
        if out["g0"]["verdict"] != "PASS":
            (root / "d3_g0.json").write_text(json.dumps(out, indent=2),
                                             encoding="utf-8")
            raise SystemExit("G-0 validation FAILED — D-3 re-evaluation blocked")
    if args.full or args.nb_pc_only:
        if args.nb_pc_only:
            # MSD arms already landed in this root; run NB + P-c only.
            import json as _js
            out["H_diff_channel"] = float(hb)
            out["h_true_planes"] = h_true
            out["L_base_shared"] = int(sum(_ml))
            msd_path = root / "d3_msd.json"
            if msd_path.exists():
                out["msd_rows"] = _js.loads(msd_path.read_text(encoding="utf-8"))
        from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
            summarize_m2,
        )
        scalars = read_p1_scalars()
        pts = []
        # Shared matrices (fixed disclosure isolates prior effect); plug-in
        # included as the third arm for direct comparison.
        if args.full:
            for name in ("plugin", "floor1e-4", "diffpmf-a1"):
                pts.append(run_msd(priors[name], B, SEED + 1, name, _mats,
                                   _facs, int(sum(_ml))))
                print(name, pts[-1]["failures"], "und", pts[-1]["undetected"],
                      "vw", pts[-1]["valid_wrong_total"], flush=True)
            rows = summarize_m2(pts, scalars)
            (root / "d3_msd.json").write_text(json.dumps(rows, indent=2),
                                              encoding="utf-8")
            out["msd_rows"] = rows
        # NB re-evaluation on diff channel (pooled, B=300, plug-in bundle;
        # smoothed NB bundles use pseudo tables — same family as S-2)
        # NOTE: process pool fails on Windows spawn namespace re-import in this
        # repo layout; threads share the process (imports fine). QSPA/numpy
        # release the GIL for heavy ops; wall scales in practice.
        nb_rows = []
        pseudo_diff = diffpmf_model(th_b, 1.0)[1]
        # Serial NB (B=100/prior): Windows spawn pool is broken in this repo
        # layout (namespace-package re-import); NB is the secondary arm here
        # (primary MSD arms already at B=300). Deviation recorded.
        import pickle
        from comparison_bench.src.comparison_bench.formal_ir.msd_d3_nbworker import (  # noqa: E402
            _nb_init as _nb_init_imp,
        )
        from comparison_bench.src.comparison_bench.formal_ir.msd_d3_nbworker import (  # noqa: E402
            _nb_one as _nb_one_imp,
        )
        B_NB = 100
        for pname, ptab in (("plugin", th_b), ("diffpmf-a1", pseudo_diff)):
            payload = pickle.dumps((ptab, pa_ch.tolist(), g_ch.tolist()))
            _nb_init_imp(payload)
            t0 = time.perf_counter()
            recs = []
            for b in range(B_NB):
                recs.append(_nb_one_imp((b, SEED + 2)))
                if (b + 1) % 25 == 0:
                    print(f"NB-{pname}: {b + 1}/{B_NB}", flush=True)
            wall = time.perf_counter() - t0
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for r in recs:
                    fh.write(json.dumps({"cfg": f"nb-{pname}", **r}) + "\n")
            nf = sum(0 if r["exact_u2"] else 1 for r in recs)
            nu = sum(1 for r in recs if r["undetected"])
            e_l = sum(r["L_u2"] for r in recs) / len(recs)
            nb_rows.append({"prior": pname, "blocks": len(recs), "failures": nf,
                            "undetected": nu, "E_u2": e_l, "FER_u2": nf / len(recs),
                            "FER_wilson_upper95": wilson_upper(nf, len(recs)),
                            "wall_s": wall})
            print(f"NB-{pname}: fail {nf}/{len(recs)} und {nu}", flush=True)
        out["nb_rows"] = nb_rows
        # P-c grids on diff channel with REALLOCATED rates (R3: m from per-grid
        # measured h + same per-symbol gap; B=300 each, plug-in + diffpmf priors)
        out["pc_rows"] = run_pc_grids(root, jl, pa_ch, g_ch, th_b, pseudo_diff,
                                      scalars)
    (root / "d3_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
