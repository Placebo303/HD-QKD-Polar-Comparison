"""M4 NB-marginal对照臂 (M4 scope): P1-demonstrated single-layer soft-marginal
NB-LDPC on the R1-TRAIN channel with unified f.

Reused VERBATIM (zero edits): b2f.decode_block_marginal (exact Bayes
marginalization, max_iter 300), p1.construct_and_pin (frozen A208 instances
+ rank/fc gates), s2c.empirical_triple_sampler + bind_empirical_bundle
(shape/normalization gates), nested base rows[0,200) + single-segment rescue
rows[200,208) COLD re-decode (P1 F2 mirror). New ONLY: deterministic bundle
derivation {g1,g2,p_b} from the approved R1-TRAIN joint counts (same
transform class as MSD prior tables; exactness-tested), fresh seeds, unified
f accounting. NOT a new probe line: the U-1对照臂 execution itself.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    SOURCE_SEEDS,
    SOURCES,
    load_train_table,
    read_p1_scalars,
    wilson_upper,
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

ARMS = ("P1S1-R1", "P1S1-R2")
TAG_BITS = 64
B = 100
SEED_BASE = 2026200101
WORKERS_FULL = 12


def derive_bundle(table: np.ndarray) -> dict[str, np.ndarray]:
    """Deterministic {g1,g2,p_b} from a 1024x1024 joint-count table.

    u1 = high 5 bits, u2 = low 5 bits (F03 convention: Alice x=u2 reconciled,
    Bob y=b&31). g1[u1,b]=P(u1|b); g2[u1,u2,b]=P(u2|u1,b) (rowsum over axis=1);
    p_b = Bob marginal. Zero-mass conditioning stays zero (sampler maps to
    delta-at-0, same as frozen behavior).
    """
    total = table.sum()
    if total <= 0:
        raise ValueError("empty counts")
    joint = table / total
    alice = np.arange(1024, dtype=np.int64)
    u1a = ((alice >> 5) & 31)
    u2a = (alice & 31)
    p_b = joint.sum(axis=0)
    g1 = np.zeros((32, 1024), dtype=np.float64)
    g2 = np.zeros((32, 32, 1024), dtype=np.float64)
    for b in range(1024):
        col = joint[:, b]
        denom = col.sum()
        if denom == 0.0:
            continue
        m1 = np.bincount(u1a, weights=col, minlength=32)
        g1[:, b] = m1 / denom
        for u1 in range(32):
            sel = u1a == u1
            d2 = col[sel].sum()
            if d2 == 0.0:
                continue
            m2 = np.bincount(u2a[sel], weights=col[sel], minlength=32)
            g2[u1, :, b] = m2 / d2
    # Binder requires every (u1,b) row normalized: map zero-mass rows to the
    # sampler's own delta-at-0 rule. These rows are never drawn (g1 is zero
    # exactly where the g2 row is zero), so sampling behavior is unchanged.
    zero_rows = g2.sum(axis=1) == 0.0
    zr_u1, zr_b = np.nonzero(zero_rows)
    g2[zr_u1, 0, zr_b] = 1.0
    return {"g1": g1, "g2": g2, "p_b": p_b}


_W = {}


def _worker_init(source: str, arm: str):
    table = load_train_table(source)
    bundle = s2c.bind_empirical_bundle(derive_bundle(table))
    _W["bundle"] = bundle
    pinned = p1.construct_and_pin(arm, p1.PRODUCTION_CONSTRUCT[arm], p1.production_rank_fn)
    _W["base"] = pinned["base"]
    _W["full"] = pinned["full"]


def _decode_one(args) -> dict:
    source, arm, idx, seed = args
    bundle, base, full = _W["bundle"], _W["base"], _W["full"]
    r1 = b2f.decode_block_marginal(base, seed + idx, bundle, 1024, 200)
    rescued = False
    if bool(r1.get("exact_match")):
        final, l_rows = r1, 200
    else:
        rescued = True
        r2 = b2f.decode_block_marginal(full, seed + idx, bundle, 1024, 208)
        final, l_rows = r2, 208
    exact = bool(final.get("exact_match"))
    rok = bool(final.get("reconstruction_ok", False))
    und = (not exact) and rok
    return {"source": source, "arm": arm, "block": idx, "seed": seed + idx,
            "m_rows": l_rows, "L_EC": 5 * l_rows, "rescued": rescued,
            "exact_ok": exact, "undetected": und,
            "u1_mismatches": int(final.get("u1_mismatches", -1)),
            "iterations": int(final.get("iterations", -1)),
            "status": str(final.get("status"))}


def run_arm(*, source: str, arm: str, n_blocks: int, seed: int,
            jsonl_path: Path, workers: int) -> dict:
    import concurrent.futures as cf

    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=_worker_init,
                                initargs=(source, arm)) as ex:
        recs = list(ex.map(_decode_one, [(source, arm, i, seed) for i in range(n_blocks)]))
    wall = time.perf_counter() - t0
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    n_fail = sum(0 if r["exact_ok"] else 1 for r in recs)
    n_und = sum(1 for r in recs if r["undetected"])
    n_res = sum(1 for r in recs if r["rescued"])
    return {"source": source, "arm": arm, "N": 1024, "blocks": n_blocks,
            "failures": n_fail, "undetected": n_und, "n_rescue": n_res,
            "u1_mm_total": sum(r["u1_mismatches"] for r in recs),
            "wall_s": wall, "s_per_block": wall / n_blocks,
            "backend": "nb-marginal-P1", "seed": seed, "workers": workers}


def summarize_nbm(points: list[dict], scalars: dict) -> list[dict]:
    rows = []
    for p in points:
        s = scalars[p["source"]]
        # E[L]: base 1000 + rescue 40 bits on rescued blocks (P1 F7 mirror)
        e_l = 1000.0 + 40.0 * p["n_rescue"] / p["blocks"]
        fer = p["failures"] / p["blocks"]
        denom = p["N"] * s["H_AB"]
        kept = p["N"] * s["H_A"] - e_l
        f_point = (e_l + TAG_BITS + kept * fer) / denom
        f_upper = (e_l + TAG_BITS + kept * wilson_upper(p["failures"], p["blocks"])) / denom
        rows.append({**p, "E_L": e_l, "L_EC": int(round(e_l)), "L_base": 1000,
                     "k_rescue": 40, "tag_bits": TAG_BITS, "H_A": s["H_A"], "H_AB": s["H_AB"],
                     "FER_exact": fer,
                     "FER_wilson_upper95": wilson_upper(p["failures"], p["blocks"]),
                     "f_expected": f_point, "f_expected_upper95": f_upper})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()
    if args.smoke:
        jl = root / "blocks_nbm_smoke.jsonl"
        if jl.exists():
            jl.unlink()
        _worker_init("T2-1M", "P1S1-R1")
        recs = [_decode_one(("T2-1M", "P1S1-R1", i, SEED_BASE)) for i in range(2)]
        with jl.open("a", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        print(json.dumps({"exact": [r["exact_ok"] for r in recs],
                          "u1_mm": [r["u1_mismatches"] for r in recs]}, indent=2))
    elif args.full:
        jl = root / "blocks_nbm.jsonl"
        if jl.exists():
            jl.unlink()
        points: list[dict] = []
        for si, source in enumerate(SOURCES):
            for ai, arm in enumerate(ARMS):
                points.append(run_arm(source=source, arm=arm, n_blocks=B,
                                      seed=SEED_BASE + si * 10000 + ai * 1000,
                                      jsonl_path=jl, workers=WORKERS_FULL))
        rows = summarize_nbm(points, scalars)
        (root / "m4_nbmarginal_summary.json").write_text(json.dumps(rows, indent=2),
                                                         encoding="utf-8")
        with (root / "m4_nbmarginal_summary.csv").open("w", encoding="utf-8") as fh:
            fh.write("source,arm,N,backend,blocks,failures,undetected,n_rescue,E_L,"
                     "FER_exact,FER_wilson_upper95,f_expected,f_expected_upper95,"
                     "u1_mm_total,s_per_block,wall_s\n")
            for r in rows:
                fh.write(f"{r['source']},{r['arm']},{r['N']},{r['backend']},{r['blocks']},"
                         f"{r['failures']},{r['undetected']},{r['n_rescue']},{r['E_L']:.1f},"
                         f"{r['FER_exact']:.4f},{r['FER_wilson_upper95']:.4f},"
                         f"{r['f_expected']:.4f},{r['f_expected_upper95']:.4f},"
                         f"{r['u1_mm_total']},{r['s_per_block']:.1f},{r['wall_s']:.1f}\n")
        print((root / "m4_nbmarginal_summary.csv").read_text(encoding="utf-8"))
    else:
        raise SystemExit("specify --smoke or --full")


if __name__ == "__main__":
    main()
