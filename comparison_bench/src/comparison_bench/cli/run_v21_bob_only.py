"""V21 Bob-only decoder strategy runner (diagnostic).

Runs one or all of S0/S1/S2 on fresh synthetic q=1024 frames and writes
per-strategy JSON/CSV.  Alice is used only for offline metric computation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

from ..formal_ir.nonbinary_v18_b2_structured_de import build_folded_w
from ..formal_ir.nonbinary_v19_channel import symbol_entropy_bits
from ..formal_ir.nonbinary_v19_finite import construct_codebook
from ..formal_ir.nonbinary_field import GF2mField
from ..formal_ir.nonbinary_v10_fftqspa import syndrome_of
from ..formal_ir.nonbinary_v21_bob_only import run_bob_only_strategy

STRATEGIES = ["S0", "S1", "S2"]


def _load_lambda(path: str) -> dict[int, float]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(k): float(v) for k, v in data.items()}


def run_one_strategy(*, strategy: str, q: int, n: int, m: int,
                     lambda_edge: dict[int, float], w: np.ndarray,
                     seed: int, n_frames: int, max_iter: int,
                     out_dir: Path) -> dict:
    code = construct_codebook(n=n, m=m, lambda_edge=lambda_edge, q=q, seed=seed)
    matrix = np.asarray(code["matrix"], dtype=np.int64)
    field = GF2mField.create(q)
    rng = np.random.default_rng(seed)
    outcomes = []
    n_exact = 0
    n_mismatch = 0
    n_failed = 0
    started = time.monotonic()
    for frame_id in range(n_frames):
        alice = rng.integers(0, q, size=n)
        errors = rng.choice(q, size=n, p=w)
        bob = np.asarray([field.add(int(a), int(e)) for a, e in zip(alice, errors)],
                         dtype=np.int64)
        s_x = np.asarray(syndrome_of(field, matrix, alice.tolist()), dtype=np.int64)
        e_hat = run_bob_only_strategy(strategy=strategy, field=field, matrix=matrix,
                                      bob=bob, s_x=s_x, w=w, max_iter=max_iter)
        if e_hat is None:
            status = "decode_failed"
            n_failed += 1
            syndrome_ok = False
            exact = False
        else:
            x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
            syndrome_ok = syndrome_of(field, matrix, x_hat) == list(s_x)
            exact = bool(syndrome_ok and np.array_equal(x_hat, alice))
            if exact:
                status = "exact_correct"
                n_exact += 1
            elif syndrome_ok:
                status = "exact_mismatch"
                n_mismatch += 1
            else:
                status = "decode_failed"
                n_failed += 1
        outcomes.append({
            "frame_id": frame_id,
            "status": status,
            "exact_correct": bool(exact),
            "syndrome_ok": bool(syndrome_ok),
            "decoder_status": "bob_only",
        })
    wall = time.monotonic() - started
    total = len(outcomes)
    h_bits = float(symbol_entropy_bits(w))
    syndrome_bits_per_frame = m * int(math.log2(q))
    f_plain = (syndrome_bits_per_frame / float(n)) / h_bits
    doc = {
        "schema": "nbldpc_v21_strategy_execute_v1",
        "strategy": strategy,
        "q": q, "n": n, "m": int(code["m"]),
        "seed": seed, "n_frames": total,
        "n_exact_correct": n_exact,
        "n_exact_mismatch": n_mismatch,
        "n_decode_failed": n_failed,
        "fer": (total - n_exact) / float(total),
        "syndrome_bits_per_frame": syndrome_bits_per_frame,
        "public_bits": 0,
        "verification_bits": 0,
        "f_plain": float(f_plain),
        "f_total": float(f_plain),
        "wall_seconds": round(wall, 4),
        "outcomes": outcomes,
        "claim_boundary": "diagnostic_only",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "execute.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out_dir / "outcomes.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(outcomes[0].keys()))
        writer.writeheader()
        writer.writerows(outcomes)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--q-small", type=int, default=1024)
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--n-frames", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2026091001)
    ap.add_argument("--max-iter", type=int, default=60)
    ap.add_argument("--seed-lambda-json", required=True)
    ap.add_argument("--strategy", choices=STRATEGIES + ["all"], default="all")
    args = ap.parse_args()

    lam = _load_lambda(args.seed_lambda_json)
    w = np.asarray(build_folded_w(args.q_small), dtype=np.float64)
    strategies = STRATEGIES if args.strategy == "all" else [args.strategy]
    out_root = Path(args.out_dir)
    summaries = []
    for st in strategies:
        doc = run_one_strategy(
            strategy=st, q=args.q_small, n=args.n, m=args.m,
            lambda_edge=lam, w=w, seed=args.seed,
            n_frames=args.n_frames, max_iter=args.max_iter,
            out_dir=out_root / st)
        summaries.append({"strategy": st, "exact": doc["n_exact_correct"],
                          "frames": doc["n_frames"], "fer": doc["fer"]})
    (out_root / "summary.json").write_text(
        json.dumps({"schema": "nbldpc_v21_run_summary_v1", "runs": summaries},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summaries, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
