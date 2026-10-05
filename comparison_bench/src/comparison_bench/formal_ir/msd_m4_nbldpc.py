"""M4 NB-LDPC对照臂 (M4_PACKET.md scope): frozen v28 empirical path on R1-TRAIN.

Zero decoder changes: frozen_v28_config matrices + V26 adapter built from the
SAME R1-TRAIN counts + decode_two_layer_sequential_empirical. Unified f metric.
Fresh seeds +9000. N=1024 native symbols (same native unit as MSD-1024).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_channel as v26  # noqa: E402
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28  # noqa: E402
from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    SOURCE_SEEDS,
    SOURCES,
    load_train_table,
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
    GF2mField,
)

SID = {"T2-1M": "type2_1M_20260121_184040",
       "T2-1.5M": "type2_1p5M_20260121_183806",
       "T2-2M": "type2_2M_20260121_183657"}
LABEL = {"T2-1M": "1M", "T2-1.5M": "1p5M", "T2-2M": "2M"}
TRAIN_N = {"T2-1M": "T2-1M", "T2-1.5M": "T2-1.5M", "T2-2M": "T2-2M"}
N_SYM = 1024
TAG_BITS = 64
B = 100
SEED_OFFSET = 9000
BLOCK_CAP_S = 240
WORKERS_FULL = 12  # process pool for --full (GIL-bound FFT-QSPA; same per-block numerics)


_W = {}


def _worker_init(source: str):
    """Build per-process state once (adapter/matrices/field/counts)."""
    table = load_train_table(TRAIN_N[source])
    _W["adapter"] = v26.build_adapter({SID[source]: table}, fact_id="F03", source=SID[source])
    cfg = v28.frozen_v28_config()
    _W["cfg"] = cfg
    _W["field"] = GF2mField.create(int(cfg["q"]))
    h1, h2map = v28.build_matrices(cfg)
    _W["h1"] = h1
    _W["h2"] = v28.layer_matrix(h2map, LABEL[source], cfg)
    _W["m_total"] = int(cfg["m1"]) + int(cfg["sources"][LABEL[source]]["m2"])
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    _W["nnz"] = nnz
    _W["probs"] = flat[nnz]
    _W["rows"], _W["cols"] = np.unravel_index(nnz, table.shape)


def _decode_one(args) -> dict:
    """One block, deterministic per-block seed (worker-independent)."""
    source, b, seed = args
    nnz, probs = _W["nnz"], _W["probs"]
    rows, cols = _W["rows"], _W["cols"]
    h1, h2 = _W["h1"], _W["h2"]
    rng = np.random.default_rng(seed + b)
    pick = rng.choice(nnz.size, size=N_SYM, p=probs)
    alice = rows[pick].astype(np.int64)
    bob = cols[pick].astype(np.int64)
    a1t = ((alice >> 5) & 31).tolist()
    a2t = (alice & 31).tolist()
    b1 = ((bob >> 5) & 31).tolist()
    b2 = (bob & 31).tolist()
    field = _W["field"]
    s1 = v28.compute_syndrome(field, h1, a1t)
    s2 = v28.compute_syndrome(field, h2, a2t)
    b_obs = ((((bob >> 5) & 31) << 5) | (bob & 31)).tolist()
    t = time.perf_counter()
    res = v28.decode_two_layer_sequential_empirical(
        field, b_obs, b1, b2, s1, s2, LABEL[source], _W["adapter"], config=_W["cfg"])
    wall = time.perf_counter() - t
    over = wall > BLOCK_CAP_S
    x1, x2 = res.get("x1_hat"), res.get("x2_hat")
    exact = (x1 is not None and list(x1) == a1t
             and x2 is not None and list(x2) == a2t) and not over
    r1ok = bool(res["L1"].get("reconstruction_ok"))
    r2ok = bool(res["L2"].get("reconstruction_ok"))
    und = (not exact) and r1ok and r2ok
    return {"source": source, "N": N_SYM, "block": b, "m_total": _W["m_total"],
            "L_EC": 5 * _W["m_total"], "exact_ok": bool(exact), "undetected": bool(und),
            "overrun": bool(over), "wall_s": wall,
            "L1_status": str(res["L1"].get("status")), "L2_status": str(res["L2"].get("status"))}


def run_nb_point(*, source: str, n_blocks: int, seed: int, jsonl_path: Path) -> dict:
    table = load_train_table(TRAIN_N[source])
    adapter = v26.build_adapter({SID[source]: table}, fact_id="F03", source=SID[source])
    cfg = v28.frozen_v28_config()
    field = GF2mField.create(int(cfg["q"]))
    h1, h2map = v28.build_matrices(cfg)
    h2 = v28.layer_matrix(h2map, LABEL[source], cfg)
    m_total = int(cfg["m1"]) + int(cfg["sources"][LABEL[source]]["m2"])
    l_ec = 5 * m_total
    flat = table.ravel() / table.sum()
    nnz = np.flatnonzero(flat)
    probs = flat[nnz]
    rows, cols = np.unravel_index(nnz, table.shape)
    rng = np.random.default_rng(seed)
    n_fail = n_und = n_over = 0
    l1_ok = l2_ok = 0
    walls = []
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for b in range(n_blocks):
            pick = rng.choice(nnz.size, size=N_SYM, p=probs)
            alice = rows[pick].astype(np.int64)
            bob = cols[pick].astype(np.int64)
            a1t = ((alice >> 5) & 31).tolist()
            a2t = (alice & 31).tolist()
            b1 = ((bob >> 5) & 31).tolist()
            b2 = (bob & 31).tolist()
            s1 = v28.compute_syndrome(field, h1, a1t)
            s2 = v28.compute_syndrome(field, h2, a2t)
            b_obs = ((((bob >> 5) & 31) << 5) | (bob & 31)).tolist()
            t = time.perf_counter()
            res = v28.decode_two_layer_sequential_empirical(
                field, b_obs, b1, b2, s1, s2, LABEL[source], adapter, config=cfg)
            wall = time.perf_counter() - t
            walls.append(wall)
            over = wall > BLOCK_CAP_S
            n_over += 1 if over else 0
            x1, x2 = res.get("x1_hat"), res.get("x2_hat")
            exact = (x1 is not None and list(x1) == a1t
                     and x2 is not None and list(x2) == a2t) and not over
            r1ok = bool(res["L1"].get("reconstruction_ok"))
            r2ok = bool(res["L2"].get("reconstruction_ok"))
            l1_ok += 1 if r1ok else 0
            l2_ok += 1 if r2ok else 0
            und = (not exact) and r1ok and r2ok
            n_fail += 0 if exact else 1
            n_und += 1 if und else 0
            fh.write(json.dumps({
                "source": source, "N": N_SYM, "block": b, "m_total": m_total,
                "L_EC": l_ec, "exact_ok": bool(exact), "undetected": bool(und),
                "overrun": bool(over), "wall_s": wall,
                "L1_status": str(res["L1"].get("status")),
                "L2_status": str(res["L2"].get("status"))}) + "\n")
    wall_tot = time.perf_counter() - t0
    return {"source": source, "N": N_SYM, "gap": "nbldpc-v28-frozen", "blocks": n_blocks,
            "L_EC": l_ec, "m_total": m_total, "failures": n_fail, "undetected": n_und,
            "overruns": n_over, "L1_ok": l1_ok, "L2_ok": l2_ok,
            "wall_s": wall_tot, "s_per_block": wall_tot / n_blocks,
            "max_block_s": max(walls), "backend": "v28-FFT-QSPA", "seed": seed}


def summarize_nb(points: list[dict], scalars: dict) -> list[dict]:
    rows = []
    for p in points:
        s = scalars[p["source"]]
        n, lec = p["N"], p["L_EC"]
        fer = p["failures"] / p["blocks"]
        denom = n * s["H_AB"]
        kept = n * s["H_A"] - lec
        f_point = (lec + TAG_BITS + kept * fer) / denom
        f_upper = (lec + TAG_BITS + kept * wilson_upper(p["failures"], p["blocks"])) / denom
        rows.append({**p, "E_L": float(lec), "L_base": lec, "k_rescue": 0, "n_rescue": 0,
                     "tag_bits": TAG_BITS, "H_A": s["H_A"], "H_AB": s["H_AB"],
                     "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(p["failures"], p["blocks"]),
                     "f_expected": f_point, "f_expected_upper95": f_upper})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--sources", default=",".join(SOURCES),
                    help="comma subset of T2-1M,T2-1.5M,T2-2M (stop-rule source cut)")
    args = ap.parse_args()
    sources = [s for s in args.sources.split(",") if s in SOURCES]
    if not sources:
        raise SystemExit("no valid sources selected")
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()
    points: list[dict] = []
    if args.smoke:
        jl = root / "blocks_nb_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        points.append(run_nb_point(source="T2-1M", n_blocks=2,
                                   seed=SOURCE_SEEDS["T2-1M"] + SEED_OFFSET, jsonl_path=jl))
        (root / "nb_smoke.json").write_text(json.dumps(summarize_nb(points, scalars), indent=2),
                                                       encoding="utf-8")
        print(json.dumps({k: points[0][k] for k in ("failures", "s_per_block", "max_block_s")},
                         indent=2))
    elif args.full:
        import concurrent.futures as cf

        jl = root / "blocks_nb.jsonl"
        if jl.exists():
            jl.unlink()
        for source in sources:
            seed = SOURCE_SEEDS[source] + SEED_OFFSET
            t0 = time.perf_counter()
            with cf.ProcessPoolExecutor(max_workers=WORKERS_FULL,
                                        initializer=_worker_init,
                                        initargs=(source,)) as ex:
                recs = list(ex.map(_decode_one,
                                   [(source, b, seed) for b in range(B)]))
            wall_tot = time.perf_counter() - t0
            n_fail = sum(0 if r["exact_ok"] else 1 for r in recs)
            n_und = sum(1 for r in recs if r["undetected"])
            n_over = sum(1 for r in recs if r["overrun"])
            walls = [r["wall_s"] for r in recs]
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for r in recs:
                    fh.write(json.dumps(r) + "\n")
            points.append({"source": source, "N": N_SYM, "gap": "nbldpc-v28-frozen",
                           "blocks": B, "L_EC": recs[0]["L_EC"], "m_total": recs[0]["m_total"],
                           "failures": n_fail, "undetected": n_und, "overruns": n_over,
                           "L1_ok": -1, "L2_ok": -1, "wall_s": wall_tot,
                           "s_per_block": wall_tot / B, "max_block_s": max(walls),
                           "backend": "v28-FFT-QSPA", "seed": seed,
                           "workers": WORKERS_FULL})
        rows = summarize_nb(points, scalars)
        (root / "m4_nbldpc_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        with (root / "m4_nbldpc_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write("source,N,backend,blocks,L_EC,failures,undetected,overruns,"
                     "FER_exact,FER_wilson_upper95,f_expected,f_expected_upper95,s_per_block,max_block_s\n")
            for r in rows:
                fh.write(f"{r['source']},{r['N']},{r['backend']},{r['blocks']},"
                         f"{r['L_EC']},{r['failures']},{r['undetected']},{r['overruns']},"
                         f"{r['FER_exact']:.6f},{r['FER_wilson_upper95']:.6f},"
                         f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                         f"{r['s_per_block']:.1f},{r['max_block_s']:.1f}\n")
        print((root / "m4_nbldpc_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
