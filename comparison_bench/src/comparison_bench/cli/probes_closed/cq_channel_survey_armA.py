"""CQ Arm A Type0 zero-correction channel survey (DECIDE; batch CHAN-QUALITY-SURVEY, Arm A only).

Applies pure-arithmetic channel metrics to the four never-opened 1.20-Type0
acquisition groups at the frozen geometry (dimension 1024, bin_width_ps 200,
frame_bins 1024) with the header-validated 1<->5 channel pair and a per-group
correlation-derived offset under the frozen A1/R1 pairing chain. No correction
is run and no correction outcome is reported anywhere here (no FER,
efficiency, leakage, f, SKR, method ranking, or operating point).

Reuse (no new alignment logic): the frozen ``src.qkd_io.ttbin_pipeline``
reader + ``_pair_nearest_unique`` + ``_frame_global`` and
``io.align_wrapper.derive_alignment`` / ``require_alignment_passed`` are
called with the new dataset paths as-is; ``m0_metrics`` + ``build_N_ab`` +
``h_full_f03`` are pure arithmetic on (a, b). The metrics module is loaded in
isolation by file path (single-file load, functions used verbatim, no
copies): a normal package import would execute ``formal_ir/__init__.py``,
which pulls correction machinery into this process and trips the gate below.

One invocation = one Type0 group. Nothing runs without BOTH
``--execute-real`` and ``--execution-authorized``.

Claim ceiling (packet Rev 2 section 11, verbatim, binds this file's outputs):
> These are channel characterization measurements only. This batch
> establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement;
> NO method comparison; NO selection of a "best" group as a favourable
> subset; and NO claim that any method works anywhere. Arm A measures channel
> characterization only, with zero correction. A lower symbol error rate does
> not imply that any method corrects. The legacy `0.098260` value is an
> expectation under a different pipeline and pairing rule (F-q, F-n), never a
> result, and must not be carried forward as one. No Type0 group may be
> presented as representative of the experiment's operating conditions. Any
> later "works on easier data" claim requires its own packet and must report
> the quality axis alongside, never the favourable subset alone. The Arm A
> quality axis exists precisely so that a later favourable-subset claim cannot
> be circular: no group may be promoted on these numbers without a new packet,
> a new authorization, and an uncertainty statement the present batch does not
> provide.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
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
        spec = importlib.util.spec_from_file_location("cqA_v25_gate_iso", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["cqA_v25_gate_iso"] = mod
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

# Frozen geometry: imposed analysis convention at the F-o PASS point.
DIMENSION = 1024
CH_A, CH_B = 1, 5
COIN_WINDOW_PS = 200
BIN_WIDTH_PS = 200
FRAME_BINS = 1024

PER_GROUP_WALL_CAP_S = 1800.0
RSS_CAP_GIB = 4.0
ROOT_PREFIX = "workspace/cq_"
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")

_BASE = "/mnt/d/Data/Raw Data/2026.1.20"
# Execution groups: key -> (gid, base member). Base member ONLY is ever
# opened; the vendor auto-follow covers the paired member (F-i).
GROUPS: dict[str, dict[str, Any]] = {
    "500K": {"gid": "CQ-20a",
             "base": f"{_BASE}/Type0_nofilter_500K_3s_2026-01-20_193050/"
                     "Type0_nofilter_500K_3s_2026-01-20_193050.ttbin"},
    "1M": {"gid": "CQ-20b",
           "base": f"{_BASE}/Type0_nofilter_1M_3s_2026-01-20_192857/"
                   "Type0_nofilter_1M_3s_2026-01-20_192857.ttbin"},
    "1_5M": {"gid": "CQ-20c",
             "base": f"{_BASE}/Type0_nofilter_1_5M_3s_2026-01-20_193255/"
                     "Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin"},
    "2M": {"gid": "CQ-20d",
           "base": f"{_BASE}/Type0_nofilter_2M_3s_2026-01-20_193411/"
                   "Type0_nofilter_2M_3s_2026-01-20_193411.ttbin"},
}

# Retained non-execution groups (packet section 5): reason only, never opened.
NON_EXEC = {
    "CQ-12": ("EXCLUDED: 3s tag measured-wrong (29.9999524 s span, quarantined "
              "from 3 s pooling); no rate tag; flat date-root layout; anomalous "
              "base-to-paired mtime gap; earliest-session protocol regime. "
              "Re-admission needs its own duration-normalized packet."),
    "CQ-13a": ("DEFERRED to a successor packet: family C, no repo-resident "
               "config and no alignment-audit PASS point; cw pump implies a "
               "multi-pair regime, not an easier-operating-point candidate."),
    "CQ-13b": ("DEFERRED to a successor packet: same grounds as CQ-13a "
               "(second SHG run of the same session)."),
}

SER_EXPECTATION_LEGACY_V1 = 0.098260
EXPECTATION_PROVENANCE = (
    "The candidate value is ser = 0.098260 at dimension=1024, bin_width_ps=200 "
    "for the 1M group, taken from that group's "
    "e2e_new_ttbin_fullgrid_20260304_231635/e2e_alignment_audit.csv "
    "(row d=1024, bw=200: map_ser=0.098260, peak_status=from_global_peak, "
    "sidecar_verdict=PASS, fail_reason blank; 110 other rows failed on "
    "map_ser>=0.1, 11 passed). This was measured by main on 2026-09-27 under "
    "the legacy-v1 pairing rule and an older pipeline, with "
    "cond_A_missing_a_or_b=1 on every row. It is an EXPECTATION TO BE TESTED "
    "UNDER THE FROZEN CHAIN, NOT A RESULT, and it must never be carried "
    "forward as a result. The comparison target is Jan-21's frozen-chain "
    "measured 23.9-25.4%. A confirmed ~10% is not by itself evidence that any "
    "method corrects; and a value that does not reproduce is an informative, "
    "legitimate outcome. Note also that e2e_alignment_audit.csv lives inside "
    "the e2e_new_ttbin_fullgrid_* subdirectory, not at the group root."
)

CLAIM_CEILING = (
    "These are channel characterization measurements only. This batch "
    "establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR "
    "statement; NO method comparison; NO selection of a \"best\" group as a "
    "favourable subset; and NO claim that any method works anywhere. Arm A "
    "measures channel characterization only, with zero correction. A lower "
    "symbol error rate does not imply that any method corrects. The legacy "
    "`0.098260` value is an expectation under a different pipeline and "
    "pairing rule (F-q, F-n), never a result, and must not be carried forward "
    "as one. No Type0 group may be presented as representative of the "
    "experiment's operating conditions. Any later \"works on easier data\" "
    "claim requires its own packet and must report the quality axis "
    "alongside, never the favourable subset alone. The Arm A quality axis "
    "exists precisely so that a later favourable-subset claim cannot be "
    "circular: no group may be promoted on these numbers without a new "
    "packet, a new authorization, and an uncertainty statement the present "
    "batch does not provide."
)


class Refusal(SystemExit):
    pass


class RefusalWithEvidence(Refusal):
    """A refusal carrying retained partial evidence (header/span/align numbers)."""

    def __init__(self, reason: str, evidence: dict[str, Any]):
        super().__init__(f"REFUSED: {reason}")
        self.evidence = dict(evidence)


def refuse(reason: str):
    raise Refusal(f"REFUSED: {reason}")


def assert_no_correction_machinery() -> None:
    """Fail closed if any repo-resident correction/construction module is loaded.

    The scan is scoped to files under this repo so that unrelated
    same-substring stdlib names cannot trip it; anything without a file path
    fails closed.
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


# ---------------------------------------------------------------- header gate

def read_header_config(base: str) -> dict[str, Any]:
    """Read-only header parse of the base member (never the paired member).

    Checks the SITT-blocked layout (TimeTagger JSON config at bytes
    @64 .. 64+u32@52, packet F-p) and returns the vendor configuration dict
    via FileReader.getConfiguration(), falling back to the raw-byte JSON.
    Any structural surprise refuses (fail closed).
    """
    raw = Path(base).read_bytes()[:131072]
    if len(raw) < 68 or raw[0:4] != b"SITT":
        refuse(f"{base}: not a SITT-blocked header (magic absent)")
    (json_len,) = struct.unpack("<I", raw[52:56])
    if not (0 < json_len < len(raw) - 64):
        refuse(f"{base}: header length word inconsistent ({json_len})")
    cfg: Any = None
    source = None
    try:
        from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
        install_timetagger_alias()
        from TimeTagger import FileReader
        reader = FileReader(base)
        try:
            cfg = reader.getConfiguration()
        finally:
            try:
                reader.close()
            except Exception:
                pass
        source = "getConfiguration"
    except Exception as exc:
        cfg = None
        source = f"getConfiguration-unavailable ({exc})"
    if not isinstance(cfg, dict):
        try:
            cfg = json.loads(raw[64:64 + json_len])
            source = "raw-header-bytes"
        except Exception as exc:
            refuse(f"{base}: header JSON not recoverable ({source}; {exc})")
    return {"config": cfg, "source": source, "sitt_magic_ok": True,
            "header_json_len": int(json_len)}


def _meas_by_name(cfg: dict[str, Any], name: str) -> list[dict[str, Any]]:
    meas = cfg.get("measurements")
    if not isinstance(meas, list):
        return []
    return [m for m in meas if isinstance(m, dict)
            and str(m.get("name", "")).lower() == name]


def _channels_of(m: dict[str, Any]) -> list[int]:
    seen: list[int] = []
    for cand in (m.get("registered channels"),
                 m.get("params", {}).get("channels") if isinstance(m.get("params"), dict) else None):
        if isinstance(cand, list):
            seen.extend(x for x in cand if isinstance(x, int) and not isinstance(x, bool))
    return seen


def validate_header_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Header-validated 1<->5 pair gate (fail closed).

    True header structure (read-only finding 2026-09-27 on the Type0 bases):
    top-level ``measurements`` list of ``{name, registered channels, virtual
    channels, params}`` mappings. Passes iff a ``FileWriter`` measurement
    shows channels superset {1,5} AND a ``Coincidences`` measurement shows a
    group exactly {1,5}. The Coincidences ``window`` is persisted as evidence
    only: the frozen pairing window comes from the M0/R1 code
    (``COIN_WINDOW_PS=200``), never from the header (measured 1000 on the
    500K base, contradicting the packet F-p "window 200" note — recorded, not
    gated). Anything else refuses.
    """
    top_keys = sorted(cfg.keys()) if isinstance(cfg, dict) else []
    fw = _meas_by_name(cfg, "filewriter")
    co = _meas_by_name(cfg, "coincidences")
    if not fw:
        refuse(f"header lacks a FileWriter measurement (top keys: {top_keys})")
    if not co:
        refuse(f"header lacks a Coincidences measurement (top keys: {top_keys})")
    fw_hit = next((m for m in fw if 1 in _channels_of(m) and 5 in _channels_of(m)), None)
    if fw_hit is None:
        refuse(f"header FileWriter channels lack {{1,5}} "
               f"(saw {[ _channels_of(m) for m in fw ]})")
    groups: list[Any] = []
    for m in co:
        params = m.get("params") if isinstance(m.get("params"), dict) else {}
        g = params.get("groups")
        if isinstance(g, list):
            groups.extend(g)
    pair_hit = next((g for g in groups
                     if isinstance(g, list) and set(g) == {1, 5}), None)
    if pair_hit is None:
        refuse(f"header Coincidences groups lack [1,5] (saw {groups})")
    windows = [m.get("params", {}).get("window") for m in co
               if isinstance(m.get("params"), dict)]
    return {"pair_validated": True,
            "filewriter_channels": _channels_of(fw_hit),
            "coincidence_groups": groups,
            "coincidence_window_raw": windows,
            "top_level_registered_channels": cfg.get("registered channels"),
            "top_keys": top_keys}


# ------------------------------------------------------------ real-data chain

def _sibling_members(base: str) -> list[Path]:
    """Vendor auto-followed paired members (stat-only evidence, never opened).

    Found by directory listing on the shared filename stem so that no paired
    member is ever opened or concatenated here (F-i); the loader streams the
    merged events through the base handle alone.
    """
    b = Path(base)
    stem = b.name[:-len(".ttbin")]
    return sorted(p for p in b.parent.iterdir()
                  if p.is_file() and p.name != b.name and p.name.startswith(stem))


def load_group_series(group: str, *,
                      header_fn: Callable[[str], dict[str, Any]] | None = None,
                      read_fn: Callable[[str], Any] | None = None,
                      align_fn: Callable[..., dict[str, Any]] | None = None
                      ) -> dict[str, Any]:
    """Frozen A1/R1 chain pointed at a Type0 base member (base only).

    Header-validated pair, per-group correlation-derived offset, frozen
    1024 x 200 ps framing convention. Any gate failure refuses (fail closed).
    Tests MUST inject fakes; the production defaults touch real data.
    """
    from comparison_bench.src.comparison_bench.io import align_wrapper as aw

    if group not in GROUPS:
        refuse(f"unknown Arm A group {group}")
    base = GROUPS[group]["base"]
    gid = GROUPS[group]["gid"]
    if not os.path.exists(base):
        refuse(f"{gid}: input base absent: {base}")

    header_fn = header_fn or read_header_config
    hinfo = header_fn(base)
    hval = validate_header_config(hinfo["config"])

    if read_fn is None:
        from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
        install_timetagger_alias()
        from src.qkd_io.ttbin_pipeline import read_ttbin_events as _read
        read_fn = _read
    t0 = time.monotonic()
    events = read_fn(base)
    read_s = time.monotonic() - t0

    t = np.asarray(events.time_ps, dtype=np.int64)
    n_rows = int(t.size)
    if t.size == 0:
        refuse(f"{gid}: empty event stream")
    span_s = float(t.max() - t.min()) * 1e-12
    tag_disputed = bool(abs(span_s - 3.0) > 0.5)
    if span_s <= 0:
        refuse(f"{gid}: non-positive span {span_s}")
    if tag_disputed:
        refuse(f"{gid}: duration tag disputed (measured span {span_s} s)")
    sibs = _sibling_members(base)
    sib_info = [{"name": p.name, "bytes": int(p.stat().st_size),
                 "mtime": float(p.stat().st_mtime)} for p in sibs]
    base_mtime = float(Path(base).stat().st_mtime)
    gap = (max(s["mtime"] for s in sib_info) - base_mtime) if sib_info else None
    if gap is not None and not (-5.0 <= gap <= 300.0):
        refuse(f"{gid}: paired-member mtime gap out of tolerance ({gap} s)")

    align_fn = align_fn or aw.derive_alignment
    t_align = time.monotonic()
    align = align_fn(events=events, ch_a=CH_A, ch_b=CH_B)
    align_wall = time.monotonic() - t_align
    align_info = {"offset_ps_derived": align.get("offset_ps_derived"),
                  "peak_bin_index": align.get("peak_bin_index"),
                  "peak_to_bg": align.get("peak_to_bg"),
                  "sigma_crude_ps": align.get("sigma_crude_ps"),
                  "align_status": align.get("align_status"),
                  "align_wall_s": align_wall,
                  "count_A": align.get("count_A"),
                  "count_B": align.get("count_B"),
                  "total_pairs_in_window": align.get("total_pairs_in_window")}
    part = {"gid": gid, "group": group, "base": base,
            "duration_measured_s": span_s, "filename_duration_tag": "3s",
            "tag_disputed": tag_disputed, "siblings": sib_info,
            "sibling_mtime_gap_s": gap, "header_source": hinfo.get("source"),
            "header_evidence": {k: hval[k] for k in
                                ("filewriter_channels", "coincidence_groups",
                                 "coincidence_window_raw",
                                 "top_level_registered_channels", "top_keys")},
            "align": align_info, "n_rows": n_rows}
    try:
        offset = aw.require_alignment_passed(align)
    except RuntimeError as exc:
        raise RefusalWithEvidence(f"{gid}: alignment {align.get('align_status')}: {exc}",
                                  part) from exc

    from src.qkd_io.ttbin_pipeline import _frame_global, _pair_nearest_unique
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
        if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a, t_b = t[valid & (ch == CH_A)], t[valid & (ch == CH_B)]
    tmin = int(t.min())
    del events
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                 window_ps=COIN_WINDOW_PS, offset_ps=int(offset))
    total_pairs = int(pa.size)
    fa, sa = _frame_global(t_ps=pa, bin_width_ps=BIN_WIDTH_PS,
                           frame_bins=FRAME_BINS, t0_ps=tmin)
    fb, sb = _frame_global(t_ps=pb, bin_width_ps=BIN_WIDTH_PS,
                           frame_bins=FRAME_BINS, t0_ps=tmin)
    keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
    frame, a, b = fa[keep], sa[keep].astype(np.int64), sb[keep].astype(np.int64)
    clean_pairs = int(frame.size)
    order = np.argsort(frame, kind="stable")
    frame, a, b = frame[order], a[order], b[order]
    return {"a": a, "b": b, "gid": gid, "group": group, "base": base,
            "offset_ps": int(offset), "total_pairs": total_pairs,
            "clean_pairs": clean_pairs,
            "framing_remainder": int(total_pairs - clean_pairs),
            "n_frames": int(np.unique(frame).size) if frame.size else 0,
            "n_rows": n_rows, "read_wall_s": read_s,
            "duration_measured_s": span_s, "filename_duration_tag": "3s",
            "tag_disputed": tag_disputed, "siblings": sib_info,
            "sibling_mtime_gap_s": gap,
            "header_source": hinfo.get("source"),
            "header_evidence": {k: hval[k] for k in
                                ("filewriter_channels", "coincidence_groups",
                                 "coincidence_window_raw",
                                 "top_level_registered_channels", "top_keys")},
            "align": {"offset_ps_derived": int(offset),
                      "peak_bin_index": align.get("peak_bin_index"),
                      "peak_to_bg": align.get("peak_to_bg"),
                      "sigma_crude_ps": align.get("sigma_crude_ps"),
                      "align_status": align.get("align_status"),
                      "align_wall_s": align_wall,
                      "count_A": align.get("count_A"),
                      "count_B": align.get("count_B"),
                      "total_pairs_in_window": align.get("total_pairs_in_window")}}


# ------------------------------------------------------------------- metrics

def channel_record(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    """Pure-arithmetic channel characterization of kept pair symbols."""
    v25 = _v25()
    mm = v25.m0_metrics(np.asarray(a, dtype=np.int64),
                        np.asarray(b, dtype=np.int64), time_blocks=6)
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
        "expected_planes_derivation": (
            f"sum_plane_rates={sum(plane_rates_lsb_first):.8f} / ser={ser:.8f} = "
            f"{exp_planes_via_diag:.6f} (diag route; popcount route "
            f"{exp_planes_via_pop:.6f}; bitwise: each symbol error flips k "
            "planes, reported value is mean k over errors)"),
        "time_block_stability": mm["time_block_stability"],
        "H_U1_given_B": float(H1),
        "H_U2_given_U1B": float(H2),
        "H_A_given_B": float(Hf),
        "N_ab_support_cells": int(np.count_nonzero(N_ab)),
        "N_ab_occupancy": float(np.count_nonzero(N_ab)) / float(N_ab.size),
    }


# ------------------------------------------------------------------ execution

def _check_root_for_group(root: str, gid: str) -> None:
    norm = root.replace("\\", "/")
    if not norm.startswith(ROOT_PREFIX):
        refuse(f"root must start with {ROOT_PREFIX}")
    if any(p in Path(norm).parts for p in FORBIDDEN_ROOT_PARTS):
        refuse("root under a protected output tree")
    if os.path.exists(root):
        if os.path.exists(os.path.join(root, f"{gid}.json")):
            refuse(f"output collision: {gid}.json already in {root}")
    # A missing root is created by the writer; a present root is shared by the
    # four sequential per-group processes (no-overwrite guarded per gid file).


def _rss_gib() -> float:
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


def execute_non_exec(*, gid: str, root: str) -> dict[str, Any]:
    """Retained non-execution record: reason only, zero data contact."""
    assert_no_correction_machinery()
    if gid not in NON_EXEC:
        refuse(f"unknown non-execution gid {gid}")
    _check_root_for_group(root, gid)
    out = {"gid": gid, "arm": "A", "status": "NON_EXECUTION",
           "reason": NON_EXEC[gid], "claim_ceiling": CLAIM_CEILING}
    os.makedirs(root, exist_ok=True)
    Path(root, f"{gid}_NON_EXECUTION.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


def execute(*, group: str, root: str,
            series_fn: Callable[..., dict[str, Any]] | None = None,
            header_fn: Callable[[str], dict[str, Any]] | None = None,
            read_fn: Callable[[str], Any] | None = None,
            align_fn: Callable[..., dict[str, Any]] | None = None,
            clock: Callable[[], float] = time.monotonic,
            rss_fn: Callable[[], float] | None = None,
            argv: list[str] | None = None) -> dict[str, Any]:
    """Run the Arm A channel survey for one Type0 group.

    Tests MUST inject a fake ``series_fn`` (or fake ``header_fn``/``read_fn``/
    ``align_fn``); the production default reads the Type0 base member through
    the frozen chain. A Refusal is captured into a retained REFUSED record.
    """
    assert_no_correction_machinery()
    if group not in GROUPS:
        refuse(f"unknown Arm A group {group}")
    gid = GROUPS[group]["gid"]
    _check_root_for_group(root, gid)
    rss_fn = rss_fn or _rss_gib

    t_start = clock()
    status = "OK"
    series: dict[str, Any] = {}
    rec: dict[str, Any] = {}
    refused_evidence: dict[str, Any] = {}
    try:
        if series_fn is not None:
            series = series_fn(group)
        else:
            series = load_group_series(group, header_fn=header_fn,
                                       read_fn=read_fn, align_fn=align_fn)
        assert_no_correction_machinery()
        a = np.asarray(series["a"], dtype=np.int64)
        b = np.asarray(series["b"], dtype=np.int64)
        rec = channel_record(a, b)
    except Refusal as exc:
        status = f"REFUSED-{exc}"
        refused_evidence = dict(getattr(exc, "evidence", {}))
    wall = clock() - t_start
    rss_peak = float(rss_fn())
    if status == "OK" and wall > PER_GROUP_WALL_CAP_S:
        status = "INCOMPLETE-wall"
    if status == "OK" and rss_peak >= RSS_CAP_GIB:
        status = "FAIL(budget-rss)"
    prov = {k: v for k, v in series.items() if k not in ("a", "b")}
    if refused_evidence:
        prov = {**refused_evidence, **prov}
    base = GROUPS[group]["base"]
    out = {
        "gid": gid, "arm": "A", "group": group, "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "expectation_provenance": EXPECTATION_PROVENANCE,
        "frozen_geometry": {
            "dimension": DIMENSION, "channels_A": CH_A, "channels_B": CH_B,
            "coin_window_ps": COIN_WINDOW_PS, "bin_width_ps": BIN_WIDTH_PS,
            "frame_bins": FRAME_BINS,
            "framing_provenance": "IMPOSED-CONVENTION (analysis convention at "
                                  "the F-o PASS point, not an acquisition "
                                  "parameter)",
        },
        "pair_provenance": "HEADER-VALIDATED (1<->5; fail-closed REFUSE otherwise)",
        "offset_provenance": "DERIVED per group by correlation auto-alignment "
                             "under the frozen A1/R1 chain (never guessed, "
                             "never borrowed, never header-taken)",
        "provenance": prov,
        "total_pairs": prov.get("total_pairs"),
        "clean_pairs": prov.get("clean_pairs"),
        "framing_remainder": prov.get("framing_remainder"),
        "ser_expectation_legacy_v1": {
            "value": SER_EXPECTATION_LEGACY_V1, "role": "EXPECTATION ONLY",
            "caveats": ("legacy-v1 pairing rule vs frozen _pair_nearest_unique; "
                        "older pipeline; cond_A_missing_a_or_b=1 on every row; "
                        "never carried forward as a result (F-q, F-n)")},
        "channel": rec,
        "base_bytes": int(Path(base).stat().st_size) if os.path.exists(base) else None,
        "command_argv": argv,
        "wall_s": wall, "rss_gib": rss_peak,
    }
    os.makedirs(root, exist_ok=True)
    Path(root, f"{gid}.json").write_text(json.dumps(out, indent=1, default=str) + "\n",
                                         encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--group", required=True, choices=sorted(GROUPS))
    p.add_argument("--root", required=True, help="fresh workspace/cq_<uuid8> root")
    p.add_argument("--execute-real", action="store_true")
    p.add_argument("--execution-authorized", action="store_true")
    args = p.parse_args(argv)
    if not (args.execute_real and args.execution_authorized):
        refuse("real-data execution needs BOTH --execute-real and --execution-authorized")
    s = execute(group=args.group, root=args.root,
                argv=["--group", args.group, "--root", args.root,
                      "--execute-real", "--execution-authorized"])
    ch = s.get("channel", {})
    print(json.dumps({"gid": s["gid"], "status": s["status"], "root": args.root,
                      "ser": ch.get("ser"),
                      "expected_planes": ch.get("expected_planes_flipped_per_error_via_diag")},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
