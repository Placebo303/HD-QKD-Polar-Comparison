"""M0 real-frame closed loop runner (DECIDE; Acceptance ID G-M0-REALFRAME).

Frozen contract: ``docs/research_cycles/M0-REALFRAME/PREREG_AND_AUTH.md``
(+ ``M0_PROMPT.md``). One invocation = one Jan-21 source, both of its
frozen arms, every eval superframe. Nothing runs without BOTH
``--execute-real`` and ``--execution-authorized``.

What is new vs the X1 synthetic runner: the synthetic triple draw
(``s2c.empirical_triple_sampler``) is replaced by real paired symbols.
Everything else is reused read-only:

- real series: the frozen A1/R1 read → §3A alignment → pairing → framing
  chain (``src/qkd_io/ttbin_pipeline`` + ``io/align_wrapper``), base
  ``X.ttbin`` member only, derived offset asserted equal to the R1 offset,
  pair count and 60/20/20 split asserted equal to the R1 root;
- eval region: VAL+HOLD frames (time-ordered last 40%), cut into
  consecutive 1024-symbol superframes (remainder dropped, reported);
- prior: the R1-TRAIN factorization of the SAME source (1M/1p5M from
  ``x1_gamma_f03r1.npz``, 2M from ``x1_gamma_f03r1_2M_verify.npz``), so
  TRAIN and eval frames are disjoint by construction; never refit;
- code: ``x1_arm_runner.construct_standalone`` + its twice-identical /
  fc=0 / rank-full gate, instance 2026092001;
- decode: the b2f soft-marginal procedure verbatim (Alice x=a&31, Bob
  y=b&31, ``marginal_prior_l2`` → ``center_rows_prior`` →
  ``decode_error_domain_posterior``, max_iter 300, streak 3).

Block classes: success = u2 exact match (frozen V80 criterion);
undetected = converged but wrong (a failure, never success). Report-only
extra column: full 10-bit symbol match after u1 recovery
û1_i = argmax_u g1[u,b_i]·g2[u,x̂_i,b_i] (the model says H(U1|U2,B)=0;
real global errors may break that).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.cli import x1_arm_runner as x1
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_fftqspa as fftqspa
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_peg as peg
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28
from comparison_bench.src.comparison_bench.formal_ir import v80_b2f_campaign as b2f
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir import v80_s2c_campaign as s2c
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField

N = 1024
MAX_ITER = b2f.MAX_ITER  # 300
PER_DECODE_CAP_S = 300.0
SOURCE_WALL_CAP_S = 5400.0
RSS_CAP_GIB = 4.0
ROOT_PREFIX = "workspace/m0_"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
F_EFF_SLOPE = 4.785675

R1_ROOT = "workspace/r1_histogram_5e2a91c4"
BUNDLE_ROOT = "workspace/x1_bundles_7c1d4a2b"

# source key -> (R1 dataset id, bundle file, frozen arms)
SOURCES: dict[str, dict[str, Any]] = {
    "1M": {"dataset": "T2-1M", "bundle": "x1_gamma_f03r1.npz", "arms": (197, 201)},
    "1p5M": {"dataset": "T2-1.5M", "bundle": "x1_gamma_f03r1.npz", "arms": (203, 207)},
    "2M": {"dataset": "T2-2M", "bundle": "x1_gamma_f03r1_2M_verify.npz", "arms": (204, 208)},
}
H_CORR = x1.H_CORR

# X1 synthetic reference at the same (source, m, construction): (fails, blocks).
X1_SYNTH = {
    ("1M", 197): (3, 240), ("1M", 201): (0, 240),
    ("1p5M", 203): (2, 240), ("1p5M", 207): (1, 240),
    ("2M", 204): (2, 240), ("2M", 208): (0, 240),
}

# Frozen A1/R1 pairing parameters (p3_census_a1 module constants).
CH_A, CH_B = 1, 5
COIN_WINDOW_PS = 200
BIN_WIDTH_PS = 200
FRAME_BINS = 1024


class Refusal(SystemExit):
    pass


def refuse(reason: str):
    raise Refusal(f"REFUSED: {reason}")


# ---------------------------------------------------------------- accounting

def f_super(source: str, m: int) -> float:
    return (5 * m + 64) / (N * H_CORR[source])


def f_notag(source: str, m: int) -> float:
    return (5 * m) / (N * H_CORR[source])


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """95% Wilson interval for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# ---------------------------------------------------------------- real data

def load_real_series(source: str, r1_root: str = R1_ROOT) -> dict[str, Any]:
    """Frozen A1/R1 chain → time-ordered (a, b) for the eval region.

    Asserts derived offset, pair count and split equal the R1 root.
    Returns a/b int64 arrays of the VAL+HOLD region plus provenance.
    """
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw
    from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias

    install_timetagger_alias()
    from src.qkd_io.ttbin_pipeline import _frame_global, _pair_nearest_unique, read_ttbin_events

    ds = SOURCES[source]["dataset"]
    r1 = json.loads(Path(r1_root, f"{ds}.json").read_text(encoding="utf-8"))
    split = json.loads(Path(r1_root, "split_manifest.json").read_text(encoding="utf-8"))[ds]
    base = r1["ttbin_member_used"]

    t0 = time.monotonic()
    events = read_ttbin_events(base)
    read_s = time.monotonic() - t0
    align = aw.derive_alignment(events=events, ch_a=CH_A, ch_b=CH_B)
    offset = aw.require_alignment_passed(align)
    if int(offset) != int(r1["offset_ps"]):
        refuse(f"{ds}: derived offset {offset} != R1 offset {r1['offset_ps']}")

    t = np.asarray(events.time_ps, dtype=np.int64)
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
        if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a, t_b = t[valid & (ch == CH_A)], t[valid & (ch == CH_B)]
    tmin = int(t.min())
    del events
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b, window_ps=COIN_WINDOW_PS, offset_ps=offset)
    fa, sa = _frame_global(t_ps=pa, bin_width_ps=BIN_WIDTH_PS, frame_bins=FRAME_BINS, t0_ps=tmin)
    fb, sb = _frame_global(t_ps=pb, bin_width_ps=BIN_WIDTH_PS, frame_bins=FRAME_BINS, t0_ps=tmin)
    keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
    frame, sa, sb = fa[keep], sa[keep], sb[keep]
    if int(frame.size) != int(r1["n_pairs_N"]):
        refuse(f"{ds}: pair count {frame.size} != R1 {r1['n_pairs_N']}")

    order = np.argsort(frame, kind="stable")
    frame, a, b = frame[order], sa[order].astype(np.int64), sb[order].astype(np.int64)
    uframes = np.unique(frame)
    n_tr = int(uframes.size * 0.6)
    n_va = int(uframes.size * 0.2)
    got = [int(uframes[0]), int(uframes[n_tr - 1]), int(uframes[n_tr]), int(uframes[-1])]
    want = [split["train_frames"][0], split["train_frames"][1],
            split["val_frames"][0], split["hold_frames"][1]]
    if got != want or n_va != split["split_val_frames"]:
        refuse(f"{ds}: split boundaries {got} != R1 {want}")
    ev = frame >= uframes[n_tr]
    return {"a": a[ev], "b": b[ev], "dataset": ds, "ttbin": base, "offset_ps": int(offset),
            "n_pairs_total": int(frame.size), "n_pairs_eval": int(ev.sum()),
            "eval_first_frame": int(uframes[n_tr]), "read_wall_s": read_s}


def superframes(a: np.ndarray, b: np.ndarray, n: int = N) -> list[tuple[np.ndarray, np.ndarray]]:
    """Consecutive, non-overlapping n-symbol superframes; remainder dropped."""
    k = int(a.size) // n
    return [(a[i * n:(i + 1) * n], b[i * n:(i + 1) * n]) for i in range(k)]


def load_bundle(source: str, bundle_root: str = BUNDLE_ROOT) -> dict[str, Any]:
    """R1-TRAIN factorization of the same source, validated by the frozen binder."""
    path = Path(bundle_root, SOURCES[source]["bundle"])
    with np.load(path) as z:
        raw = {"g1": z[f"{source}_gamma1_L1"], "g2": z[f"{source}_gamma2_L2condU1"],
               "p_b": z[f"{source}_p_b"]}
    bound = s2c.bind_empirical_bundle(raw, source)
    bound["path"] = str(path)
    return bound


# ---------------------------------------------------------------- decode

def recover_u1(bundle: dict[str, Any], b: np.ndarray, u2_hat: np.ndarray) -> np.ndarray:
    """û1_i = argmax_u g1[u,b_i]·g2[u,u2_hat_i,b_i] (report-only)."""
    g1, g2 = bundle["g1"], bundle["g2"]
    score = g1[:, b] * g2[:, u2_hat, b]  # (32, n)
    return np.argmax(score, axis=0).astype(np.int64)


def decode_real(construction: dict[str, Any], a: np.ndarray, b: np.ndarray,
                bundle: dict[str, Any], m: int) -> dict[str, Any]:
    """b2f soft-marginal decode on one real superframe (frozen procedure)."""
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction["triples"], N, m, field)
    x = a & 31
    y = b & 31
    prior = s2c.center_rows_prior(b2f.marginal_prior_l2(bundle, b), y)
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    res = v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x, prior, MAX_ITER)
    x_hat = res.get("x_hat")
    exact = x_hat is not None and bool(np.array_equal(np.asarray(x_hat), x))
    full10 = False
    if exact:
        full10 = bool(np.array_equal(recover_u1(bundle, b, x), a >> 5))
    return {"exact_match": exact, "full10_match": full10,
            "reconstruction_ok": bool(res.get("reconstruction_ok", False)),
            "status": res.get("status"), "iterations": res.get("iterations")}


# ---------------------------------------------------------------- execution

def _check_root(root: str) -> None:
    norm = root.replace("\\", "/")
    if not norm.startswith(ROOT_PREFIX):
        refuse(f"root must start with {ROOT_PREFIX}")
    if any(p in Path(norm).parts for p in FORBIDDEN_ROOT_PARTS):
        refuse("root under a protected output tree")
    if os.path.exists(root):
        refuse(f"root not fresh: {root}")


def _rss_gib() -> float:
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


def _write(root: str, files: dict[str, str]) -> None:
    os.makedirs(root, exist_ok=True)
    for name, text in files.items():
        Path(root, name).write_text(text, encoding="utf-8")


def arm_summary(source: str, m: int, rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    fails = sum(1 for r in rows if not r["exact_match"])
    und = sum(1 for r in rows if r["undetected"])
    fails10 = sum(1 for r in rows if not r["full10_match"])
    fer = fails / n if n else float("nan")
    fs = f_super(source, m)
    sk, sn = X1_SYNTH[(source, m)]
    lo, hi = wilson(fails, n)
    slo, shi = wilson(sk, sn)
    return {
        "source": source, "m": m, "superframes": n, "fails": fails, "undetected": und,
        "fer": fer, "fer_ci95": [lo, hi], "fails_full10": fails10,
        "fer_full10": fails10 / n if n else float("nan"),
        "f_super": fs, "f_notag": f_notag(source, m), "f_eff": fs + F_EFF_SLOPE * fer,
        "synthetic_x1": {"fails": sk, "blocks": sn, "fer": sk / sn, "fer_ci95": [slo, shi]},
        "real_over_synth_ci_overlap": bool(lo <= shi and slo <= hi),
        "overruns": sum(1 for r in rows if r.get("status") == "overrun"),
        "wall_s": sum(r["wall_s"] for r in rows),
    }


def result_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# M0 real-frame result — {summary['source']} ({summary['verdict']})", "",
             f"- ttbin: `{summary['provenance'].get('ttbin')}`; offset {summary['provenance'].get('offset_ps')} ps",
             f"- eval pairs {summary['provenance'].get('n_pairs_eval')} → superframes {summary['n_superframes']}"
             f" (remainder {summary['remainder_symbols']} symbols dropped)",
             f"- bundle: `{summary['bundle']}` (R1-TRAIN, disjoint from eval frames)", "",
             "| m | superframes | fails | undetected | FER [95% CI] | fails (full 10-bit) | f_super | f_notag | f_eff | X1 synthetic fails/240 [95% CI] |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in summary["arms"]:
        x = s["synthetic_x1"]
        lines.append(
            f"| {s['m']} | {s['superframes']} | {s['fails']} | {s['undetected']} | "
            f"{s['fer']:.4f} [{s['fer_ci95'][0]:.4f}, {s['fer_ci95'][1]:.4f}] | {s['fails_full10']} | "
            f"{s['f_super']:.4f} | {s['f_notag']:.4f} | {s['f_eff']:.4f} | "
            f"{x['fails']}/{x['blocks']} [{x['fer_ci95'][0]:.4f}, {x['fer_ci95'][1]:.4f}] |")
    lines += ["", "success = u2 exact match; undetected counted as failure, never success; "
              "f_super and f_eff are distinct lines; no certification sentence; no SKR.",
              f"- wall {summary['wall_s']:.1f} s; peak RSS {summary['rss_gib']:.2f} GiB; decodes {summary['decodes']}"]
    return "\n".join(lines) + "\n"


def rows_csv(rows: list[dict]) -> str:
    cols = ["m", "superframe", "exact_match", "undetected", "full10_match", "status",
            "iterations", "wall_s", "raw_symbol_errors", "u2_symbol_errors"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def execute(*, source: str, root: str,
            series_fn: Callable[[str], dict[str, Any]] | None = None,
            bundle_fn: Callable[[str], dict[str, Any]] | None = None,
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable[[], float] = time.monotonic,
            rss_fn: Callable[[], float] | None = None) -> dict[str, Any]:
    """Run both frozen arms of one source over every eval superframe.

    Tests MUST inject fake ``series_fn`` / ``bundle_fn`` / ``construct_fn``
    / ``decode_fn``; the production defaults read real data.
    """
    if source not in SOURCES:
        refuse(f"unknown source {source}")
    _check_root(root)
    series_fn = series_fn or load_real_series
    bundle_fn = bundle_fn or load_bundle
    construct_fn = construct_fn or (lambda m, seed, trials: x1.construct_standalone(m, seed, trials))
    decode_fn = decode_fn or decode_real
    rss_fn = rss_fn or _rss_gib

    t_start = clock()
    series = series_fn(source)
    bundle = bundle_fn(source)
    blocks = superframes(series["a"], series["b"])
    prov = {k: v for k, v in series.items() if k not in ("a", "b")}
    rows: list[dict] = []
    arms_out: list[dict] = []
    verdict = "COMPLETE"
    rss_peak = 0.0

    def summary() -> dict[str, Any]:
        return {"source": source, "verdict": verdict, "provenance": prov,
                "bundle": bundle.get("path", "<injected>"),
                "n_superframes": len(blocks),
                "remainder_symbols": int(series["a"].size) - N * len(blocks),
                "arms": arms_out + ([arm_summary(source, cur_m, cur_rows)] if cur_rows else []),
                "wall_s": clock() - t_start, "rss_gib": rss_peak, "decodes": len(rows)}

    def flush() -> None:
        s = summary()
        _write(root, {f"M0_RESULT_{source}.md": result_markdown(s),
                      "rows.json": json.dumps({"summary": s, "rows": rows}, indent=1, default=str),
                      "block_accounting.csv": rows_csv(rows)})

    cur_m, cur_rows = 0, []
    for m in SOURCES[source]["arms"]:
        construction = x1._construct_gate(m, construct_fn, x1.X1_CONSTRUCT_SEED, x1.X1_MAX_TRIALS)
        cur_m, cur_rows = m, []
        for k, (a, b) in enumerate(blocks):
            if clock() - t_start > SOURCE_WALL_CAP_S:
                verdict = "INCOMPLETE-wall"
                flush()
                return summary()
            rss_peak = max(rss_peak, float(rss_fn()))
            if rss_peak >= RSS_CAP_GIB:
                verdict = "FAIL(budget-rss)"
                flush()
                return summary()
            t0 = clock()
            out = decode_fn(construction, a, b, bundle, m)
            dt = clock() - t0
            overrun = dt > PER_DECODE_CAP_S  # terminal: counted as a failure, never re-run
            exact = bool(out["exact_match"]) and not overrun
            row = {"m": m, "superframe": k, "exact_match": exact,
                   "undetected": bool(not overrun and not exact and out.get("reconstruction_ok")),
                   "full10_match": bool(exact and out.get("full10_match")),
                   "status": "overrun" if overrun else out.get("status"),
                   "iterations": out.get("iterations"), "wall_s": dt,
                   "raw_symbol_errors": int(np.count_nonzero(a != b)),
                   "u2_symbol_errors": int(np.count_nonzero((a & 31) != (b & 31)))}
            rows.append(row)
            cur_rows.append(row)
            flush()
        arms_out.append(arm_summary(source, m, cur_rows))
        cur_rows = []
    flush()
    return summary()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", required=True, choices=sorted(SOURCES))
    p.add_argument("--root", required=True, help="fresh workspace/m0_<uuid8>_<source> root")
    p.add_argument("--execute-real", action="store_true")
    p.add_argument("--execution-authorized", action="store_true")
    args = p.parse_args(argv)
    if not (args.execute_real and args.execution_authorized):
        refuse("real-data execution needs BOTH --execute-real and --execution-authorized "
               "(G-M0-REALFRAME grant in PREREG_AND_AUTH.md)")
    s = execute(source=args.source, root=args.root)
    print(json.dumps({"source": s["source"], "verdict": s["verdict"], "root": args.root,
                      "arms": [{k: a[k] for k in ("m", "superframes", "fails", "undetected", "fer",
                                                  "fails_full10", "f_super", "f_eff")}
                               for a in s["arms"]]}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
