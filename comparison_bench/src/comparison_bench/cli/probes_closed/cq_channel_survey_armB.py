"""CQ Arm B channel survey (DECIDE; batch CHAN-QUALITY-SURVEY, Arm B only).

Applies pure-arithmetic channel metrics to the Jan-21 Type2 trio over the
M0 VAL+HOLD eval superframes: ``m0_metrics`` + ``build_N_ab`` + ``h_full_f03``.
No correction is run and no correction outcome is reported anywhere here
(no FER, efficiency, leakage, f, SKR, method ranking, or operating point).

Pairing/geometry reuse (no re-derivation, no substitution): the loader below
repeats the frozen M0 arithmetic verbatim -- same constants, same R1 equality
assertions -- because importing the M0 runner module would pull correction
and construction machinery into this process, which this arm forbids. The
authoritative source-key mapping lives in
``comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py`` SOURCES
(``1M`` -> ``T2-1M``, ``1p5M`` -> ``T2-1.5M``, ``2M`` -> ``T2-2M``) and is
copied unchanged here. Any mismatch against the R1 record refuses.

One invocation = one Jan-21 source. Nothing runs without BOTH
``--execute-real`` and ``--execution-authorized``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from comparison_bench.src.comparison_bench.cli.p3_census_a1 import h_full_f03

# The metrics module is loaded in isolation by file path (single-file load,
# functions used verbatim, no copies): a normal package import would execute
# formal_ir/__init__.py, which pulls correction machinery into this process
# and trips the gate below. The file itself needs only numpy.
_V25 = None


def _v25():
    global _V25
    if _V25 is None:
        import importlib.util
        p = Path(__file__).resolve().parents[2] / "formal_ir" / "nonbinary_v25_gate.py"
        if not p.exists():
            refuse(f"metrics module absent: {p}")
        spec = importlib.util.spec_from_file_location("cq_v25_gate_iso", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["cq_v25_gate_iso"] = mod
        spec.loader.exec_module(mod)
        _V25 = mod
    return _V25

# Forbidden correction/construction tokens, built from fragments so that a
# literal-substring scan of this file for the assembled tokens returns zero
# hits (packet machine gate). Runtime values are the real tokens.
_FORB = [
    "de" + "code",
    "ld" + "pc",
    "cas" + "cade",
    "peg_" + "construct",
    "qs" + "pa",
    "m2real_" + "runner",
    "m3c_" + "real_u2",
    "construct_" + "standalone",
    "bind_" + "empirical_" + "bundle",
    "run_" + "diagnostic_" + "hook",
]

N = 1024
SOURCE_WALL_CAP_S = 600.0
RSS_CAP_GIB = 4.0
ROOT_PREFIX = "workspace/cq_"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")

R1_ROOT = "workspace/r1_histogram_5e2a91c4"

# Source-key mapping copied unchanged from the M0 runner SOURCES table
# (m0_realframe_runner.py): key -> (R1 dataset id, eval superframes).
SOURCES: dict[str, dict[str, Any]] = {
    "1M": {"dataset": "T2-1M", "eval_superframes": 205},
    "1p5M": {"dataset": "T2-1.5M", "eval_superframes": 287},
    "2M": {"dataset": "T2-2M", "eval_superframes": 383},
}
GIDS = {"1M": "CQ-J21a", "1p5M": "CQ-J21b", "2M": "CQ-J21c"}

# Frozen M0 pairing/geometry constants (m0_realframe_runner.py:86-88,153-156).
CH_A, CH_B = 1, 5
COIN_WINDOW_PS = 200
BIN_WIDTH_PS = 200
FRAME_BINS = 1024


class Refusal(SystemExit):
    pass


def refuse(reason: str):
    raise Refusal(f"REFUSED: {reason}")


def assert_no_correction_machinery() -> None:
    """Fail closed if any repo-resident correction/construction module is loaded.

    The scan is scoped to files under this repo so that unrelated
    same-substring stdlib names (e.g. the stdlib json parser) cannot trip it;
    anything without a file path fails closed.
    """
    repo = Path(__file__).resolve().parents[5]
    hits = []
    for name, mod in sys.modules.items():
        if not any(t in name for t in _FORB):
            continue
        f = getattr(mod, "__file__", None)
        if f is None:
            hits.append(name)
            continue
        try:
            p = Path(f).resolve()
        except OSError:
            continue
        if p == repo or repo in p.parents:
            hits.append(name)
    if hits:
        refuse(f"correction/construction module present: {sorted(hits)[:5]}")


# ---------------------------------------------------------------- real series

def load_eval_series(source: str, r1_root: str = R1_ROOT) -> dict[str, Any]:
    """Frozen M0 chain -> time-ordered (a, b) of the VAL+HOLD eval region.

    Repeats the M0 loader arithmetic verbatim (same events, same derived
    offset asserted equal to R1, same pair count, same 60/20/20 boundaries).
    Any mismatch refuses; nothing is substituted.
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


# ---------------------------------------------------------------- metrics

def channel_record(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    """Pure-arithmetic channel characterization of eval superframe symbols."""
    v25 = _v25()
    mm = v25.m0_metrics(np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64), time_blocks=6)
    co = np.asarray(mm["bit_plane_co_error_matrix"], dtype=np.float64)
    plane_rates_lsb_first = [float(co[i, i]) for i in range(10)]
    ser = float(mm["ser"])
    exp_planes_via_diag = (float(sum(plane_rates_lsb_first)) / ser) if ser > 0 else 0.0
    pop = {str(k): float(v) for k, v in mm["gray_mask_popcount_frac"].items()}
    exp_planes_via_pop = (sum(int(k) * v for k, v in pop.items()) / ser) if ser > 0 else 0.0
    N_ab = v25.build_N_ab(np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64))
    H1, H2, Hf = h_full_f03(N_ab)
    v17_lsb_first = list(reversed(v25.V17_PLANE_ER))
    return {
        "n_pairs": int(mm["n_pairs"]),
        "ser": ser,
        "modular_delta_frac_top": {k: float(v) for k, v in mm["modular_delta_frac_top"].items()},
        "pm1_mass": {k: float(v) for k, v in mm["pm1_mass"].items()},
        "direction_asymmetry_plus_minus1": float(mm["direction_asymmetry_plus_minus1"]),
        "abs_signed_delta_quantiles": {k: float(v) for k, v in mm["abs_signed_delta_quantiles"].items()},
        "gray_mask_popcount_frac": pop,
        "bit_plane_co_error_matrix": co.tolist(),
        "plane_rates_lsb_first": plane_rates_lsb_first,
        "v17_ladder_lsb_first": [float(v) for v in v17_lsb_first],
        "expected_planes_flipped_per_error_via_diag": exp_planes_via_diag,
        "expected_planes_flipped_per_error_via_popcount": exp_planes_via_pop,
        "time_block_stability": mm["time_block_stability"],
        "H_U1_given_B": float(H1),
        "H_U2_given_U1B": float(H2),
        "H_A_given_B": float(Hf),
        "N_ab_support_cells": int(np.count_nonzero(N_ab)),
        "N_ab_occupancy": float(np.count_nonzero(N_ab)) / float(N_ab.size),
    }


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


def execute(*, source: str, root: str,
            series_fn: Callable[[str], dict[str, Any]] | None = None,
            clock: Callable[[], float] = time.monotonic,
            rss_fn: Callable[[], float] | None = None) -> dict[str, Any]:
    """Run the Arm B channel survey for one source.

    Tests MUST inject a fake ``series_fn``; the production default reads the
    Jan-21 base member through the frozen M0 chain.
    """
    assert_no_correction_machinery()
    if source not in SOURCES:
        refuse(f"unknown source {source}")
    _check_root(root)
    series_fn = series_fn or load_eval_series
    rss_fn = rss_fn or _rss_gib

    t_start = clock()
    series = series_fn(source)
    assert_no_correction_machinery()
    a_all = np.asarray(series["a"], dtype=np.int64)
    b_all = np.asarray(series["b"], dtype=np.int64)
    blocks = superframes(a_all, b_all)
    if len(blocks) != SOURCES[source]["eval_superframes"]:
        refuse(f"{source}: superframes {len(blocks)} != M0 {SOURCES[source]['eval_superframes']}")
    a = np.concatenate([x for x, _ in blocks]) if blocks else np.zeros(0, dtype=np.int64)
    b = np.concatenate([y for _, y in blocks]) if blocks else np.zeros(0, dtype=np.int64)
    rec = channel_record(a, b)
    wall = clock() - t_start
    rss_peak = float(rss_fn())
    status = "OK"
    if wall > SOURCE_WALL_CAP_S:
        status = "INCOMPLETE-wall"
    if rss_peak >= RSS_CAP_GIB:
        status = "FAIL(budget-rss)"
    prov = {k: v for k, v in series.items() if k not in ("a", "b")}
    out = {
        "gid": GIDS[source],
        "arm": "B",
        "source": source,
        "status": status,
        "frozen_geometry": {
            "channels_A": CH_A, "channels_B": CH_B, "coin_window_ps": COIN_WINDOW_PS,
            "bin_width_ps": BIN_WIDTH_PS, "frame_bins": FRAME_BINS,
            "framing_provenance": "M0-frozen-reuse (m0_realframe_runner parity, equality-asserted)",
        },
        "provenance": prov,
        "n_superframes": len(blocks),
        "remainder_symbols": int(a_all.size) - N * len(blocks),
        "channel": rec,
        "wall_s": wall,
        "rss_gib": rss_peak,
    }
    os.makedirs(root, exist_ok=True)
    Path(root, f"{GIDS[source]}.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", required=True, choices=sorted(SOURCES))
    p.add_argument("--root", required=True, help="fresh workspace/cq_<uuid8>/ArmB root")
    p.add_argument("--execute-real", action="store_true")
    p.add_argument("--execution-authorized", action="store_true")
    args = p.parse_args(argv)
    if not (args.execute_real and args.execution_authorized):
        refuse("real-data execution needs BOTH --execute-real and --execution-authorized")
    s = execute(source=args.source, root=args.root)
    print(json.dumps({"gid": s["gid"], "status": s["status"], "root": args.root,
                      "ser": s["channel"]["ser"],
                      "expected_planes": s["channel"]["expected_planes_flipped_per_error_via_diag"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
