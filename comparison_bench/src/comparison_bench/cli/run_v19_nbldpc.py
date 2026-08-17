"""CLI for V19 Nonbinary LDPC primary-route diagnostics (N1-N4).

Modes:
  channel          write N1 channel model JSON
  rate-ladder      run N2a warm-started rate ladder on folded real channel
  qsc-control      run B-1 QSC equal-entropy control searches
  extended-probe   run N2c extended-degree DE probes (dc > 40 path)
  finite           run N3/N4 finite code construction + synthetic frames
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..formal_ir import nonbinary_v19_channel as channel
from ..formal_ir import nonbinary_v19_de_search as de_search
from ..formal_ir import nonbinary_v19_finite as finite
from ..formal_ir.nonbinary_v18_b2_structured_de import build_folded_w


def _write_json(out_dir: Path, name: str, doc: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("channel")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--q-small", type=int, default=16)
    p.add_argument("--qsc-p", type=float, default=0.038)
    p.set_defaults(func=cmd_channel)

    p = sub.add_parser("rate-ladder")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--q-small", type=int, default=16)
    p.add_argument("--rate", type=float, action="append", default=[])
    p.add_argument("--seed", type=int, default=2026082001)
    p.add_argument("--pop-size", type=int, default=6)
    p.add_argument("--max-gen", type=int, default=2)
    p.add_argument("--n-samples", type=int, default=800)
    p.add_argument("--max-iter", type=int, default=40)
    p.add_argument("--seed-lambda-json", type=str, default=None)
    p.add_argument("--no-warm-start", action="store_true")
    p.set_defaults(func=cmd_rate_ladder)

    p = sub.add_parser("qsc-control")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--q-small", type=int, default=16)
    p.add_argument("--qsc-p", type=float, default=0.038)
    p.add_argument("--rate", type=float, action="append", default=[0.63, 0.65])
    p.add_argument("--seed", type=int, action="append", default=[])
    p.add_argument("--pop-size", type=int, default=4)
    p.add_argument("--max-gen", type=int, default=1)
    p.add_argument("--n-samples", type=int, default=500)
    p.add_argument("--max-iter", type=int, default=20)
    p.set_defaults(func=cmd_qsc_control)

    p = sub.add_parser("extended-probe")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--q-small", type=int, default=16)
    p.add_argument("--rate", type=float, default=0.65)
    p.add_argument("--n-samples", type=int, default=1000)
    p.add_argument("--max-iter", type=int, default=30)
    p.add_argument("--seed", type=int, default=2026082002)
    p.add_argument("--candidate-json", type=str, default=None,
                   help="JSON list of candidate lambda mappings")
    p.set_defaults(func=cmd_extended_probe)

    p = sub.add_parser("finite")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--q-small", type=int, default=16)
    p.add_argument("--n", type=int, default=256)
    p.add_argument("--m", type=int, default=102)
    p.add_argument("--rate", type=float, default=None,
                   help="If given, m is computed as round((1-rate)*n)")
    p.add_argument("--n-frames", type=int, default=20)
    p.add_argument("--seed", type=int, default=2026082003)
    p.add_argument("--frame-seed", type=int, default=None,
                   help="Optional separate seed for frame sampling (code uses --seed)")
    p.add_argument("--frame-offset", type=int, default=0,
                   help="Skip this many frames before sampling (for chunked runs)")
    p.add_argument("--max-iter", type=int, default=60)
    p.add_argument("--seed-lambda-json", type=str, required=True,
                   help="JSON mapping of the lambda degree distribution")
    p.add_argument("--osd-order", type=int, default=None,
                   help="Override OSD order (0 or 1)")
    p.add_argument("--osd-top-info", type=int, default=4,
                   help="Number of least-reliable free variables for OSD-1")
    p.set_defaults(func=cmd_finite)

    args = ap.parse_args()
    return int(args.func(args))


def _load_lambda(path: str | None) -> dict[int, float] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        raise ValueError("_load_lambda expects a single mapping; use _load_candidates for lists")
    return {int(k): float(v) for k, v in data.items()}


def _load_candidates(path: str | None) -> list[dict[int, float]] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [{int(k): float(v) for k, v in item.items()} for item in data]
    if isinstance(data, dict):
        return [{int(k): float(v) for k, v in data.items()}]
    raise ValueError("candidate JSON must be a mapping or list of mappings")


def cmd_channel(args) -> int:
    doc = channel.build_channel_doc(q_small=args.q_small, qsc_p=args.qsc_p)
    _write_json(Path(args.out_dir), "channel.json", doc)
    print(json.dumps(doc, sort_keys=True))
    return 0


def cmd_rate_ladder(args) -> int:
    q = int(args.q_small)
    w = build_folded_w(q)
    rates = [float(x) for x in args.rate] or [0.65, 0.70, 0.75]
    doc = de_search.run_rate_ladder(
        q=q, w=w, rates=rates, seed=args.seed,
        pop_size=args.pop_size, max_gen=args.max_gen,
        n_samples=args.n_samples, max_iter=args.max_iter,
        seed_lambda=_load_lambda(args.seed_lambda_json),
        warm_start=not args.no_warm_start,
        out_dir=Path(args.out_dir))
    print(json.dumps(doc, sort_keys=True))
    return 0


def cmd_qsc_control(args) -> int:
    q = int(args.q_small)
    seeds = [int(x) for x in args.seed] or [2026082008 + i for i in range(2)]
    doc = de_search.run_qsc_control(
        q=q, p=args.qsc_p, rates=[float(x) for x in args.rate],
        seeds=seeds, pop_size=args.pop_size, max_gen=args.max_gen,
        n_samples=args.n_samples, max_iter=args.max_iter,
        out_dir=Path(args.out_dir))
    print(json.dumps(doc, sort_keys=True))
    return 0


def cmd_extended_probe(args) -> int:
    q = int(args.q_small)
    w = build_folded_w(q)
    candidates = _load_candidates(args.candidate_json)
    if candidates is None:
        # Default extended-degree candidates for the smoke path.
        candidates = [
            {2: 0.3, 3: 0.3, 4: 0.2, 48: 0.2},
            {2: 0.35, 3: 0.25, 4: 0.15, 60: 0.25},
        ]
    doc = de_search.run_extended_degree_probe(
        q=q, rate=args.rate, w=w, candidates=candidates,
        n_samples=args.n_samples, max_iter=args.max_iter, seed=args.seed,
        out_dir=Path(args.out_dir))
    print(json.dumps(doc, sort_keys=True))
    return 0


def cmd_finite(args) -> int:
    q = int(args.q_small)
    w = build_folded_w(q)
    lam = _load_lambda(args.seed_lambda_json)
    if lam is None:
        print("--seed-lambda-json is required for finite mode", file=sys.stderr)
        return 2
    m = args.m
    if args.rate is not None:
        m = int(round((1.0 - float(args.rate)) * int(args.n)))
    if m <= 0:
        print("m must be positive", file=sys.stderr)
        return 2
    doc = finite.execute_synthetic_frames(
        q=q, n=args.n, m=m, lambda_edge=lam, w=w,
        n_frames=args.n_frames, seed=args.seed, max_iter=args.max_iter,
        osd_order=args.osd_order, osd_top_info=args.osd_top_info,
        frame_seed=args.frame_seed,
        frame_offset=args.frame_offset,
        out_dir=Path(args.out_dir))
    print(json.dumps({k: v for k, v in doc.items() if k != "outcomes"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
