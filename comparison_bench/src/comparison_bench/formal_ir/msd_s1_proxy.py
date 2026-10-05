"""S-1 mismatch-aware proxy (S1_PACKET.md scope): channel and prior from
DIFFERENT TRAIN halves (R10); G-0 calibration against M5 block outcomes.

--build: re-read ttbin via the frozen M5 chain pattern (TRAIN region only),
  split TRAIN by acquisition-frame midpoint into halves, save count tables
  (half-a, half-b, full, eighth-subset) per source.
--smoke/--full: T2-1M pilot, Tier1 (ch=A, prior=B) + Tier2 (ch=full, prior=1/8),
  frozen M5 MSD config (m_0 from PRIOR h) + NB-marginal arms, full-symbol metric
  (R11) + per-stage valid-wrong tracking. Zero new real frames for targets.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    load_train_table,
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
    M1_16384,
    MAX_ITER,
    build_mixed_point,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
    build_conditional_prior_model,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
    summarize_m2,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
    derive_bundle,
    summarize_nbm,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
    _syndrome,
    disclose_syndromes,
    make_bp_decoder,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_b2f_campaign as b2f,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_s2c_campaign as s2c,
)
from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
    p1_stage1_runner as p1,
)

C0_MSD = 2000
K_MSD = 400
N_MSD = 16384
N_NB = 1024
B_MSD = 100
B_NB = 60
SEED_BASE = 2026300101
SUBSET_FRAC = 1 / 8
SOURCES_S1 = ("T2-1M",)
DSMAP = {"T2-1M": "1M"}


def _pair_train_halves(source: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Frozen-chain TRAIN pairs + frame ids (TRAIN region only)."""
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias

    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import _frame_global, _pair_nearest_unique, read_ttbin_events
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as m0,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m5_realframe import (  # noqa: E402
        _win_ttbin_path,
    )

    ds = source
    r1_root = "workspace/r1_histogram_5e2a91c4"
    r1 = json.loads(Path(r1_root, f"{ds}.json").read_text(encoding="utf-8"))
    split = json.loads(Path(r1_root, "split_manifest.json").read_text(encoding="utf-8"))[ds]
    base = _win_ttbin_path(r1["ttbin_member_used"])
    events = read_ttbin_events(base)
    align = aw.derive_alignment(events=events, ch_a=m0.CH_A, ch_b=m0.CH_B)
    offset = aw.require_alignment_passed(align)
    if int(offset) != int(r1["offset_ps"]):
        raise SystemExit(f"{ds}: offset {offset} != R1 {r1['offset_ps']}")
    t = np.asarray(events.time_ps, dtype=np.int64)
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
        if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a, t_b = t[valid & (ch == m0.CH_A)], t[valid & (ch == m0.CH_B)]
    tmin = int(t.min())
    del events
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b, window_ps=m0.COIN_WINDOW_PS,
                                  offset_ps=offset)
    fa, sa = _frame_global(t_ps=pa, bin_width_ps=m0.BIN_WIDTH_PS,
                           frame_bins=m0.FRAME_BINS, t0_ps=tmin)
    fb, sb = _frame_global(t_ps=pb, bin_width_ps=m0.BIN_WIDTH_PS,
                           frame_bins=m0.FRAME_BINS, t0_ps=tmin)
    keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
    frame, a, b = fa[keep], sa[keep].astype(np.int64), sb[keep].astype(np.int64)
    if int(frame.size) != int(r1["n_pairs_N"]):
        raise SystemExit(f"{ds}: pair count {frame.size} != R1 {r1['n_pairs_N']}")
    tr0, tr1 = split["train_frames"]
    sel = (frame >= tr0) & (frame <= tr1)
    return a[sel], b[sel], frame[sel]


def counts_of(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    t = np.zeros((1024, 1024), dtype=np.float64)
    np.add.at(t, (a, b), 1)
    return t


def build_all(root: Path) -> dict:
    """Build Tier tables per source; returns manifest (also saved)."""
    manifest = {}
    for si, source in enumerate(SOURCES_S1):
        a, b, f = _pair_train_halves(source)
        mid = (f.min() + f.max()) // 2
        ma, mb = f <= mid, f > mid
        ta = counts_of(a[ma], b[ma])
        tb = counts_of(a[mb], b[mb])
        full = ta + tb
        rng = np.random.default_rng(20263000 + si)
        sub = rng.random(a.size) < SUBSET_FRAC
        te = counts_of(a[sub], b[sub])
        np.savez_compressed(root / f"{source}_tier_tables.npz",
                            half_a=ta, half_b=tb, full=full, eighth=te)
        np.savez_compressed(root / f"{source}_tier_pairs.npz",
                            a_half_a=a[ma].astype(np.int64),
                            b_half_a=b[ma].astype(np.int64),
                            a_full=a.astype(np.int64),
                            b_full=b.astype(np.int64))
        manifest[source] = {"n_a": int(ma.sum()), "n_b": int(mb.sum()),
                            "n_full": int(a.size), "n_eighth": int(sub.sum()),
                            "frame_mid": int(mid)}
    (root / "proxy_manifest.json").write_text(json.dumps(manifest, indent=2),
                                              encoding="utf-8")
    return manifest


def load_tier_pairs(root: Path, source: str, which: str) -> tuple[np.ndarray, np.ndarray]:
    """Bootstrap pair arrays (empirical joint preserved exactly)."""
    z = np.load(root / f"{source}_tier_pairs.npz")
    key = {"half_a": ("a_half_a", "b_half_a"),
           "full": ("a_full", "b_full")}[which]
    return (np.asarray(z[key[0]], dtype=np.int64),
            np.asarray(z[key[1]], dtype=np.int64))


def load_tier(root: Path, source: str, which: str) -> np.ndarray:
    z = np.load(root / f"{source}_tier_tables.npz")
    return np.asarray(z[which], dtype=np.float64)


def _decode_msd_block(alice, bob, model, matrices, factories, k_rescue, bp):
    n = alice.size
    dis = disclose_syndromes(alice, model, matrices)
    recovered, passed, exact_stage = [], [], []
    rescued, extra = False, 0

    def mux_factory(*, parity_check_matrix, error_channel):
        idx = mux_factory.calls[0]
        mux_factory.calls[0] += 1
        return factories[idx](parity_check_matrix=parity_check_matrix,
                              error_channel=error_channel)

    mux_factory.calls = [0]
    truth_planes = [((alice >> bit) & 1).astype(np.uint8) for bit in range(10)]
    valid_wrong = 0
    for stage, mat in enumerate(matrices):
        prev = np.stack(recovered, axis=0) if recovered else np.empty((0, n), dtype=np.uint8)
        q = model.query(stage, bob, prev)
        base = (q.p_one > 0.5).astype(np.uint8)
        ch = np.minimum(q.p_one, 1 - q.p_one).copy()
        syndromes = np.asarray(dis.public_syndromes[stage], dtype=np.uint8)
        delta = np.bitwise_xor(syndromes, _syndrome(mat, base))
        if stage == 0:
            dec = mux_factory(parity_check_matrix=mat, error_channel=ch)
            rec = np.bitwise_xor(base, np.asarray(dec.decode(delta.copy())).astype(np.uint8))
            if not bool(np.array_equal(_syndrome(mat, rec), syndromes)):
                rescued, extra = True, k_rescue
                w = np.log((1 - np.maximum(ch, 1e-300)) / np.maximum(ch, 1e-300))
                weak = np.argsort(w, kind="stable")[:k_rescue]
                base[weak] = truth_planes[0][weak]
                ch[weak] = 0.0
                delta2 = np.bitwise_xor(syndromes, _syndrome(mat, base))
                dec2 = mux_factory(parity_check_matrix=mat, error_channel=ch)
                rec = np.bitwise_xor(
                    base, np.asarray(dec2.decode(delta2.copy())).astype(np.uint8))
        else:
            dec = mux_factory(parity_check_matrix=mat, error_channel=ch)
            rec = np.bitwise_xor(
                base, np.asarray(dec.decode(delta.copy())).astype(np.uint8))
        recovered.append(rec)
        ok = bool(np.array_equal(_syndrome(mat, rec), syndromes))
        passed.append(ok)
        ex = bool(np.array_equal(rec, truth_planes[stage]))
        exact_stage.append(ex)
        if ok and not ex:
            valid_wrong += 1
        if not ok:
            break
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        _natural_symbols_from_stages,
    )
    full = len(passed) == 10 and all(passed)
    recon = _natural_symbols_from_stages(recovered, model, n) if full else None
    exact = recon is not None and bool(np.array_equal(recon, alice))
    return {"exact_ok": exact, "undetected": full and not exact, "rescued": rescued,
            "extra": extra, "stages_passed": [bool(v) for v in passed],
            "valid_wrong_stages": valid_wrong,
            "plane1_failed": len(passed) > 1 and bool(passed[0]) and not bool(passed[1])}


def run_msd_tier(*, source: str, root: Path, channel: str, prior: str,
                 n_blocks: int, seed: int, jsonl_path: Path, tag: str) -> dict:
    ct = load_tier(root, source, channel)
    pt = load_tier(root, source, prior)
    # R10: channel SAMPLING is bootstrap over the channel half's empirical
    # pair list (joint preserved exactly); prior is the other half's table.
    # (Plug-in-parametric sampling destroyed joint concentration and is retired.)
    pair_key = {"half_a": "half_a", "full": "full"}[channel]
    pa_all, pb_all = load_tier_pairs(root, source, pair_key)
    model = build_conditional_prior_model(pt, encoding="NATURAL", order="LSB_FIRST")
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        plane_conditional_entropies,
    )
    h_prior = plane_conditional_entropies(pt)
    matrices, factories, _, m_list = build_mixed_point(N_MSD, h_prior, C0_MSD, 32, 256)
    l_base = int(sum(m_list))
    n_pairs = pa_all.size
    rng = np.random.default_rng(seed)
    bp = functools.partial(make_bp_decoder, max_iter=MAX_ITER)
    n_fail = n_und = n_res = n_vw = n_p1f = 0
    s_att = [0] * 10
    s_pas = [0] * 10
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(n_blocks):
            pick = rng.choice(n_pairs, size=N_MSD, replace=True)
            alice = pa_all[pick].astype(np.int64)
            bob = pb_all[pick].astype(np.int64)
            r = _decode_msd_block(alice, bob, model, matrices, factories, K_MSD, bp)
            for s, ok in enumerate(r["stages_passed"]):
                s_att[s] += 1
                if ok:
                    s_pas[s] += 1
            n_fail += 0 if r["exact_ok"] else 1
            n_und += 1 if r["undetected"] else 0
            n_res += 1 if r["rescued"] else 0
            n_vw += r["valid_wrong_stages"]
            n_p1f += 1 if r["plane1_failed"] else 0
            fh.write(json.dumps({"source": source, "tier": tag, "N": N_MSD, "block": blk,
                                 "L_base": l_base, "extra": r["extra"],
                                 "rescued": r["rescued"], **{k: r[k] for k in
                                 ("exact_ok", "undetected", "stages_passed")},
                                 "valid_wrong_stages": r["valid_wrong_stages"],
                                 "plane1_failed": r["plane1_failed"]}) + "\n")
    wall = time.perf_counter() - t0
    return {"source": source, "tier": tag, "N": N_MSD, "gap": f"s1-{tag}",
            "blocks": n_blocks, "L_EC": l_base, "m_per_plane": [int(m) for m in m_list],
            "L_base": l_base, "k_rescue": K_MSD, "n_rescue": n_res,
            "failures": n_fail, "undetected": n_und,
            "valid_wrong_total": n_vw, "plane1_failed": n_p1f,
            "stage_attempted": s_att, "stage_passed": s_pas,
            "wall_s": wall, "s_per_block": wall / n_blocks,
            "backend": "msd-s1-proxy", "max_iter": MAX_ITER, "seed": seed}


def _channel_of_tier(tag: str) -> str:
    if tag == "T1":
        return "half_a"
    if tag == "T2":
        return "full"
    raise ValueError(f"unknown tier {tag}")


def run_nb_tier(*, source: str, root: Path, prior: str, n_blocks: int,
                seed: int, jsonl_path: Path, tag: str) -> list[dict]:
    pt = load_tier(root, source, prior)
    bundle = s2c.bind_empirical_bundle(_bundle_parts(pt))
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_peg as _peg,
    )
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
        GF2mField as _GF,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v10_fftqspa as _q,
    )
    from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
        nonbinary_v28 as _v28,
    )
    from comparison_bench.src.comparison_bench.cli.probes_closed import (  # noqa: E402
        m0_realframe_runner as _m0,
    )
    field = _GF.create(32)
    # bootstrap channel pairs (M0-style real-pair decode, not self-sampling)
    pa_all, pb_all = load_tier_pairs(root, source, _channel_of_tier(tag))
    dense = {}
    for arm in ("P1S1-R1", "P1S1-R2"):
        pinned = p1.construct_and_pin(arm, p1.PRODUCTION_CONSTRUCT[arm],
                                      p1.production_rank_fn)
        dense[arm] = {}
        for key, code, m in (("base", pinned["base"], 200), ("full", pinned["full"], 208)):
            dense[arm][key] = _peg.sparse_to_dense(code["triples"], N_NB, m, field)
    pts = []
    for arm in ("P1S1-R1", "P1S1-R2"):
        rng = np.random.default_rng(seed)
        n_fail = n_und = n_res = u1mm = fvw = n_u1r = 0
        t0 = time.perf_counter()
        with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
            for blk in range(n_blocks):
                pick = rng.choice(pa_all.size, size=N_NB, replace=True)
                alice = pa_all[pick].astype(np.int64)
                bob = pb_all[pick].astype(np.int64)
                x = alice & 31
                y = bob & 31
                out = []
                for key in ("base", "full"):
                    if key == "full" and out and bool(out[0]["exact_match"]):
                        break
                    prior = s2c.center_rows_prior(
                        b2f.marginal_prior_l2(bundle, bob), y)
                    sxx = _q.syndrome_of(field, dense[arm][key], x.tolist())
                    res = _v28.decode_error_domain_posterior(
                        field, y.tolist(), dense[arm][key], sxx, prior, 300)
                    xh = res.get("x_hat")
                    ex = xh is not None and bool(np.array_equal(np.asarray(xh), x))
                    out.append({"exact_match": ex,
                                "reconstruction_ok": bool(res.get("reconstruction_ok", False)),
                                "status": str(res.get("status")),
                                "iterations": int(res.get("iterations", -1))})
                umm = int((((np.asarray(_m0.recover_u1(bundle, bob, x))) != ((alice >> 5) & 31))).sum())
                if out[0]["exact_match"]:
                    final, l_rows, rescued = out[0], 200, False
                elif len(out) > 1:
                    final, l_rows, rescued = out[1], 208, True
                else:
                    final, l_rows, rescued = out[0], 200, False
                exact = bool(final["exact_match"])
                und = (not exact) and bool(final["reconstruction_ok"])
                if und:
                    fvw += 1
                full_ok = exact and umm == 0
                n_fail += 0 if full_ok else 1
                n_und += 1 if und else 0
                n_res += 1 if rescued else 0
                n_u1r = (n_u1r + 1) if (exact and umm > 0) else n_u1r
                u1mm += umm
                fh.write(json.dumps({"source": source, "arm": arm, "tier": tag,
                                     "block": blk, "m_rows": l_rows,
                                     "exact_u2": exact, "exact_full": full_ok,
                                     "undetected": und, "u1_mismatches": umm,
                                     "rescued": rescued}) + "\n")
        wall = time.perf_counter() - t0
        pts.append({"source": source, "arm": arm, "tier": tag, "N": N_NB,
                    "blocks": n_blocks, "failures": n_fail, "undetected": n_und,
                    "valid_wrong_nb": fvw, "n_rescue": n_res, "u1_mm_total": u1mm,
                    "u1_residual_blocks": n_u1r,
                    "u2_fer": None, "wall_s": wall, "s_per_block": wall / n_blocks,
                    "backend": "nb-s1-proxy", "seed": seed})
    return pts


def _bundle_parts(table: np.ndarray) -> dict[str, np.ndarray]:
    from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
        derive_bundle,
    )
    full = derive_bundle(table)
    return {"g1": full["g1"], "g2": full["g2"], "p_b": full["p_b"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    if args.build:
        manifest = build_all(root)
        print(json.dumps(manifest, indent=2))
    elif args.smoke or args.full:
        n_msd = 4 if args.smoke else B_MSD
        n_nb = 4 if args.smoke else B_NB
        scalars = read_p1_scalars()
        msd_pts, nb_raw = [], []
        jl = root / ("blocks_s1_smoke.jsonl" if args.smoke else "blocks_s1.jsonl")
        if jl.exists():
            jl.unlink()
        for tier, ch, pr in (("T1", "half_a", "half_b"), ("T2", "full", "eighth")):
            msd_pts.append(run_msd_tier(source="T2-1M", root=root, channel=ch, prior=pr,
                                        n_blocks=n_msd, seed=SEED_BASE,
                                        jsonl_path=jl, tag=tier))
            nb_raw.extend(run_nb_tier(source="T2-1M", root=root, prior=pr,
                                      n_blocks=n_nb, seed=SEED_BASE + 500,
                                      jsonl_path=jl, tag=tier))
        msd_rows = summarize_m2(msd_pts, scalars)
        (root / "s1_msd_summary.json").write_text(json.dumps(msd_rows, indent=2),
                                                 encoding="utf-8")
        from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
            summarize_nbm,
        )
        nb_summ = summarize_nbm(nb_raw, scalars)
        (root / "s1_nb_summary.json").write_text(json.dumps(nb_summ, indent=2),
                                                 encoding="utf-8")
        print(json.dumps({"msd": [{k: r[k] for k in
                                   ("tier", "failures", "plane1_failed",
                                    "valid_wrong_total", "undetected")} for r in msd_pts],
                          "nb": [{k: r[k] for k in
                                  ("tier", "arm", "failures", "undetected",
                                   "u1_mm_total", "u1_residual_blocks")} for r in nb_raw]}, indent=2))
    else:
        raise SystemExit("specify --build, --smoke or --full")


if __name__ == "__main__":
    main()
