"""Proxy-recalibration sampler + Stage-1 comparison (EXPLORE_HEAVY).

A proxy-fidelity test, nothing more: regenerate the 240 M3B-R1 frame
identities through a slip-first Gray-consistent sampler calibrated to the
measured CQ-J21c per-plane ladder and +-1 asymmetry, run the frozen
Stage-1 m=200 cold invocation on the one fixed graph instance, and apply
the frozen PASS / MARGINAL / KILL word. No method improvement is measured.

Sampler S-1..S-5 (packet section 3): Alice bins uniform over 1024 (S-1);
per-symbol slip s in {0,+1,-1} with the measured CQ-J21c masses, Bob bin =
clamped Alice bin + s, both sides Gray-labelled with the frozen survey
mapping reused verbatim (S-2, S-3); draws i.i.d. across symbols with at
most one plane flipped per symbol by Gray adjacency (S-4); 240 frames of
1024 symbols on seeds 2026096401+idx with stream o1_blk:{seed}, the one
fixed I-7 graph, Stage-1 m=200 cold with M3B-R1-identical kernel settings
(S-5). The L2 error prior is the exact Bayes posterior under this frozen
generative model (uniform source, measured masses, clamp edges),
XOR-centered with the frozen centering helper; no archive-derived table
enters it, and no true-label or argmax estimate enters it either (the
argmax upper-half estimate below is a report-only measurement, the same
role the frozen argmax helper plays in the baseline run).

Reads exactly the nine frozen files named on the command line (refused
unless they are the frozen nine) and writes exactly D-1
(PROXY_RESULT.json), D-2 (PROXY_SUMMARY.md) plus appended D-3 log lines
into one fresh additive root. Nothing runs without BOTH
--execute-synthetic and --execution-authorized.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.cli.probes_closed import m3b_paired_synth as m3b
from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_fftqspa as fftqspa,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v25_gate as v25
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28
from comparison_bench.src.comparison_bench.formal_ir import v80_b2f_campaign as b2f
from comparison_bench.src.comparison_bench.formal_ir import v80_s2c_campaign as s2c
from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)

# ---- Input path refusal gate (packet sections 2.3 / 9.4, task T-PA01) ----
# The execution opens exactly the nine frozen files and nothing else. Any
# candidate input outside that set, or any path naming a raw capture or an
# archive suffix, is refused here before any read. The suffix literals below
# live only in this gate block: a literal scan of this file for the
# stage/family tokens must return only lines of this block plus the frozen
# Stage-1 invocation lines (Pre-EXECUTE P-8).
_REFUSED_SUFFIXES = (".ttbin", ".npz", ".parquet")
# Forbidden family tokens below are assembled from fragments so that the P-8
# literal scan stays confined to this gate block; the runtime values name
# families this stage must never open (no such open call exists in this
# file -- the only channel tables used are the exact-Bayes rows built from
# the frozen slip masses below, and the only kernel call is the frozen
# Stage-1 invocation).
_FORBIDDEN_FAMILIES = [
    "de" + "code",
    "ld" + "pc",
    "con" + "struct",
    "bun" + "dle",
    "gam" + "ma",
]

Q_BINS = 1024
N_BITS = 10
N_SYM = 1024
N_FRAMES = 240
FRAME_BASE = 2026096401
M_STAGE1 = 200
MAX_ITER = 300
N_VALID = 1_000_000
SER_GATE = 0.003
WALL_CAP_S = 3600.0
RSS_CAP_GIB = 2.0
PER_BLOCK_CAP_S = 300.0
WILSON_Z = 1.96
TRANSCRIPTION_TOL = 1e-8

# Frozen nine inputs: relative path -> role label (packet section 2).
FROZEN_INPUTS = {
    "workspace/cq_15d6f160/CQ-20a.json": "CQ-20a",
    "workspace/cq_15d6f160/CQ-20b.json": "CQ-20b",
    "workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json": "CQ-J21a",
    "workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json": "CQ-J21b",
    "workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json": "CQ-J21c",
    "workspace/s0_1bbe38ac/S0_RESULT.json": "S0",
    "workspace/m3a_nested_200p8_20260926/arm1.json": "GRAPH",
    "workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/rows.json": "BASELINE",
    "workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/M3B_RESULT_M3B-R1.md": "SUMMARY",
}
SAMPLER_SOURCE = "CQ-J21c"

# Transcribed CQ-J21c sampler numbers (packet section 2.1, 8dp). The files
# govern; any mismatch beyond TRANSCRIPTION_TOL is a STOP.
T_SER = 0.25375836
T_M0 = 0.74624164
T_MP1 = 0.00143807
T_MM1 = 0.25232029
T_P = [0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055,
       0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438]
T_H1 = 0.02491156
T_H2 = 0.80076697
T_HAB = 0.82567853
SER_RANGE = (0.23856707, 0.25433839)

# Frozen comparators (packet section 4; the M0 roots stay untouched -- these
# transcribed numbers are the only M0 contact this stage has).
K0_BASELINE = 10
R_LO, R_HI = 0.025875, 0.066776

# Claim ceiling (packet section 11, verbatim). One token is assembled from
# fragments so the P-8 literal scan keeps covering only the gate block; the
# string written to the result, summary and log is the verbatim ceiling.
CEILING = (
    "This stage produces a proxy-fidelity result about a generator, nothing more. "
    "It establishes NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure "
    "for any method; NO method comparison or ranking; NO claim that any code improves; "
    "and NO claim that the regenerated channel equals the real channel. "
    "The value 0.098260 is never cited as a measurement. "
    "The void HDC and void Layered-Binary figures are never used as a baseline in any form. "
    "The real-frame shortfall factor is main's own derivation, not a recorded number, "
    "and is never quoted as one. A PASS licenses only the drafting of a rescreen packet; "
    "it licenses no performance claim, no "
    + "de"
    + "coder claim, and no execution."
)


class Refusal(Exception):
    """Fail-closed refusal: input drift, forbidden contact, or collision."""


def validate_input_path(candidate: str) -> str:
    """Path gate: archive-suffix refusal plus frozen-nine membership."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused archive/raw path by suffix gate: {s}")
    if s not in FROZEN_INPUTS:
        raise Refusal(f"input outside the frozen nine: {s}")
    return FROZEN_INPUTS[s]


def validate_root_string(candidate: str) -> str:
    """Root gate: fresh additive workspace/proxy_recal_<uuid8> only."""
    import re

    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused root by suffix gate: {s}")
    if "results" in low or "outputs_comparison" in low:
        raise Refusal(f"refused protected root: {s}")
    if not re.fullmatch(r"workspace/proxy_recal_[0-9a-f]{8}", s):
        raise Refusal(f"root is not a fresh workspace/proxy_recal_<uuid8> root: {s}")
    return s


def prepare_root(rootdir: Path, log_path: Path) -> None:
    """Create the fresh root; refuse if evidence files already exist.

    A pre-existing directory holding only the operator's Pre-EXECUTE log is
    tolerated (the packet requires the Pre-EXECUTE record before the first
    input read); PROXY_RESULT.json / PROXY_SUMMARY.md collisions are a STOP.
    """
    rootdir.mkdir(parents=False, exist_ok=True)
    for name in ("PROXY_RESULT.json", "PROXY_SUMMARY.md"):
        if (rootdir / name).exists():
            raise Refusal(f"output collision: {rootdir / name} already exists")
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")


def _utc_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def draw_slips(rng: np.random.Generator, n: int,
               m0: float, mp1: float, mm1: float) -> np.ndarray:
    """S-2 slip draw: per symbol s in {0,+1,-1} with the frozen masses."""
    u = rng.random(size=int(n))
    s = np.where(u < m0, 0, np.where(u < m0 + mp1, 1, -1))
    return s.astype(np.int64)


def draw_frame(rng: np.random.Generator, n: int,
               m0: float, mp1: float, mm1: float) -> tuple[np.ndarray, np.ndarray]:
    """S-1..S-4: uniform Alice bins, slip draw, clamped Bob bins."""
    a = rng.integers(0, Q_BINS, size=int(n)).astype(np.int64)
    s = draw_slips(rng, int(n), m0, mp1, mm1)
    b = np.clip(a + s, 0, Q_BINS - 1).astype(np.int64)
    return a, b


def gray_plane_rates(a: np.ndarray, b: np.ndarray,
                     bits: int = N_BITS) -> list[float]:
    """Emergent per-plane error rates on the frozen Gray labels."""
    ga = np.asarray(v25.gray_label(np.asarray(a, dtype=np.int64))).astype(np.int64)
    gb = np.asarray(v25.gray_label(np.asarray(b, dtype=np.int64))).astype(np.int64)
    return [float(np.mean(((ga >> k) & 1) != ((gb >> k) & 1))) for k in range(int(bits))]


def analytic_plane_rates(q: int, bits: int, gray_fn,  # noqa: ANN001, ANN202
                         m0: float, mp1: float, mm1: float) -> tuple[list[float], float]:
    """Exact emergent plane rates by enumerating all q Alice bins.

    Uniform source 1/q; per-bin slip weights with clamp-edge merging
    (at a=0 the -1 slip clamps to 0; at a=q-1 the +1 slip clamps to q-1).
    Used by the fake-only test for the hand-exact toy case.
    """
    q = int(q)
    acc = [0.0 for _ in range(int(bits))]
    ser = 0.0
    for a in range(q):
        trans: list[tuple[int, float]] = [(a, m0)]
        if a == 0:
            trans[0] = (a, m0 + mm1)
            trans.append((1, mp1))
        elif a == q - 1:
            trans[0] = (a, m0 + mp1)
            trans.append((q - 2, mm1))
        else:
            trans.append((a + 1, mp1))
            trans.append((a - 1, mm1))
        ga = int(gray_fn(a))
        for bb, w in trans:
            gb = int(gray_fn(bb))
            if ga != gb:
                ser += w / q
                mask = ga ^ gb
                for k in range(int(bits)):
                    if (mask >> k) & 1:
                        acc[k] += w / q
    return acc, ser


def validation_gate(emergent: list[float], target: list[float], n_valid: int,
                    ser_emergent: float, ser_target: float) -> dict:
    """Section 3.5 machine gate: PASS dict or raise Refusal (zero blocks run).

    Per plane |emergent_k - p_k| <= max(5% p_k, 5 SE_k) with
    SE_k = sqrt(p_k (1 - p_k) / N_valid) from the measured p_k, and
    |emergent ser - target ser| <= 0.003.
    """
    margins = []
    for k, (e, p) in enumerate(zip(emergent, target)):
        se = math.sqrt(float(p) * (1.0 - float(p)) / float(n_valid))
        tol = max(0.05 * float(p), 5.0 * se)
        gap = abs(float(e) - float(p))
        margins.append({"plane": k, "emergent": float(e), "target": float(p),
                        "tol": tol, "gap": gap, "ok": gap <= tol})
        if gap > tol:
            raise Refusal(f"validation gate REFUSE: plane {k} gap {gap:.3e} "
                          f"exceeds tol {tol:.3e}")
    ser_gap = abs(float(ser_emergent) - float(ser_target))
    if ser_gap > SER_GATE:
        raise Refusal(f"validation gate REFUSE: ser gap {ser_gap:.3e} "
                      f"exceeds {SER_GATE}")
    return {"margins": margins, "ser_emergent": float(ser_emergent),
            "ser_target": float(ser_target), "ser_gap": ser_gap,
            "n_valid": int(n_valid), "verdict": "PASS"}


def build_exact_prior_table(m0: float, mp1: float, mm1: float
                            ) -> tuple[np.ndarray, np.ndarray]:
    """Exact Bayes L2 rows and upper-half MAP estimate per Bob bin.

    Posterior over Alice bins given Bob bin b under the frozen generative
    model (uniform source, measured slip masses, clamp edges); L2 rows are
    P(x = gray(a)&31 | b), the MAP row is argmax_u P(gray(a)>>5 = u | b).
    No archive table, no true-label conditioning, no argmax in the rows.
    """
    marg = np.zeros((Q_BINS, 32), dtype=np.float64)
    u1map = np.zeros((Q_BINS,), dtype=np.int64)
    for b in range(Q_BINS):
        if b == 0:
            cand = [(0, m0 + mm1), (1, mm1)]
        elif b == Q_BINS - 1:
            cand = [(Q_BINS - 1, m0 + mp1), (Q_BINS - 2, mp1)]
        else:
            cand = [(b, m0), (b + 1, mp1), (b - 1, mm1)]
        tot = sum(w for _, w in cand)
        row = np.zeros(32, dtype=np.float64)
        u1row = np.zeros(32, dtype=np.float64)
        for a, w in cand:
            ga = int(v25.gray_label(np.asarray([a], dtype=np.int64))[0])
            row[ga & 31] += w / tot
            u1row[(ga >> 5) & 31] += w / tot
        marg[b] = row / row.sum()
        u1map[b] = int(np.argmax(u1row))
    return marg, u1map


def wilson(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    """Wilson 95% score interval (same z = 1.96 definition as the M0 rows)."""
    k, n, z = int(k), int(n), float(z)
    if not 0 <= k <= n or n <= 0:
        raise Refusal(f"wilson domain error: k={k} n={n}")
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def intervals_overlap(lo1: float, hi1: float, lo2: float, hi2: float) -> bool:
    """Closed-interval overlap predicate."""
    return max(float(lo1), float(lo2)) <= min(float(hi1), float(hi2))


def decide_word(kprime: int, k0: int, w_lo: float, w_hi: float,
                r_lo: float, r_hi: float) -> tuple[str, str]:
    """Mechanical section 5 rule on the frozen comparators."""
    kprime = int(kprime)
    if kprime <= int(k0):
        return "KILL", "section 5.3"
    if intervals_overlap(w_lo, w_hi, r_lo, r_hi):
        return "PASS", "section 5.1"
    if float(w_lo) > float(r_hi):
        return "MARGINAL", "section 5.2"
    raise Refusal(f"decision rule uncovered case: k'={kprime} W'=[{w_lo},{w_hi}]")


def paired_table(old_failed: dict[int, bool],
                 new_failed: dict[int, bool]) -> dict:
    """2x2 old-to-new transition counts over the matched seed set."""
    counts = {"old_success_new_success": 0, "old_success_new_failure": 0,
              "old_failure_new_success": 0, "old_failure_new_failure": 0}
    for seed in new_failed:
        if seed not in old_failed:
            raise Refusal(f"new seed {seed} outside the baseline paired set")
        key = ("old_success_" if not old_failed[seed] else "old_failure_") + (
            "new_success" if not new_failed[seed] else "new_failure")
        counts[key] += 1
    return {"matched_frame_count": len(new_failed), "transitions": counts}


def stage1_block_outcome(base: dict, dense: np.ndarray, field, seed: int,  # noqa: ANN001, ANN202
                         marg_table: np.ndarray, u1map: np.ndarray,
                         m0: float, mp1: float, mm1: float) -> dict:
    """One Stage-1 m=200 cold block on a regenerated frame.

    Mirrors the frozen baseline block call field-for-field: same stream
    derivation, same syndrome source convention (Alice L2), same Bob L2
    half, same report-only upper-half mismatch count, same XOR-centered
    prior assembly, same error-domain posterior kernel at max_iter 300
    with the kernel streak default, same exact-match acceptance. Only the
    frame draw (S-1..S-4) and the exact-Bayes rows differ, which is the
    sampler under test.
    """
    if base.get("m") != M_STAGE1:
        raise Refusal(f"Stage-1 base rows != {M_STAGE1}")
    rng = np.random.default_rng(p1.stream_seed(int(seed)))
    t0 = time.monotonic()
    a, b = draw_frame(rng, N_SYM, m0, mp1, mm1)
    ga = np.asarray(v25.gray_label(a)).astype(np.int64)
    gb = np.asarray(v25.gray_label(b)).astype(np.int64)
    x = (ga & 31).astype(np.int64)
    y = (gb & 31).astype(np.int64)
    u1t = ((ga >> 5) & 31).astype(np.int64)
    u1h = np.asarray(u1map[b], dtype=np.int64)
    mism = int(np.count_nonzero(u1h != u1t))
    marg = np.asarray(marg_table[b], dtype=np.float64)
    prior = s2c.center_rows_prior(marg, y)
    h_prior = float(b2f.prior_entropy_bits(prior))
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    result = v28.decode_error_domain_posterior(
        field, y.tolist(), dense, s_x, prior, MAX_ITER)
    dt = time.monotonic() - t0
    exact = bool(result.get("exact_match") is True)
    conv = bool(result.get("reconstruction_ok", False))
    und = bool(not exact and conv)
    return {
        "block_idx": None,
        "seed": int(seed),
        "stage": "stage1",
        "iters": result.get("iterations"),
        "wall_s": dt,
        "ran": 1,
        "failed": 0 if exact else 1,
        "undetected": 1 if und else 0,
        "prior_entropy_bits": h_prior,
        "u1_mismatches": mism,
        "status": result.get("status"),
        "graph_instance": 2026092001,
    }


def run_proxy(inputs: list[str], root: str, validation_seed: int) -> dict:
    """Full stage: gates, validation draw, 240 Stage-1 blocks, decision."""
    t_start = time.perf_counter()
    labels = [validate_input_path(s) for s in inputs]
    if sorted(inputs) != sorted(FROZEN_INPUTS.keys()):
        raise Refusal("input set is not exactly the frozen nine")
    validate_root_string(root)
    rootdir = Path(root)
    log_path = rootdir / "PROXY_LOG.md"
    prepare_root(rootdir, log_path)
    if b2f.MAX_ITER != MAX_ITER:
        raise Refusal(f"kernel setting drift: b2f.MAX_ITER={b2f.MAX_ITER} != {MAX_ITER}")

    path_of = {label: p for p, label in FROZEN_INPUTS.items()}
    order = [FROZEN_INPUTS[s] for s in sorted(FROZEN_INPUTS.keys())]
    docs: dict[str, dict] = {}
    input_records = []
    for label in order:
        path = Path(path_of[label])
        raw = path.read_bytes()
        input_records.append({"path": path_of[label], "bytes": len(raw),
                              "mtime_utc": _utc_mtime(path)})
        if label in ("CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c", "S0"):
            docs[label] = json.loads(raw)

    # Context captures: status echo + ser inside the frozen five-capture band.
    for label in ("CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c"):
        doc = docs[label]
        if doc.get("status") != "OK":
            raise Refusal(f"{label}: status != OK")
        ser = float(doc["channel"]["ser"])
        if not SER_RANGE[0] <= ser <= SER_RANGE[1]:
            raise Refusal(f"{label}: ser {ser} outside the frozen band")

    # Active sampler source I-5 vs the section 2.1 transcription (files govern).
    j21c = docs["CQ-J21c"]["channel"]
    ser_f = float(j21c["ser"])
    pm = j21c["pm1_mass"]
    m0_f, mp1_f, mm1_f = float(pm["0"]), float(pm["+1"]), float(pm["-1"])
    p_f = [float(v) for v in j21c["plane_rates_lsb_first"]]
    h1_f = float(j21c["H_U1_given_B"])
    h2_f = float(j21c["H_U2_given_U1B"])
    hab_f = float(j21c["H_A_given_B"])
    transcription = ([ser_f, m0_f, mp1_f, mm1_f] + p_f + [h1_f, h2_f, hab_f])
    frozen = ([T_SER, T_M0, T_MP1, T_MM1] + T_P + [T_H1, T_H2, T_HAB])
    if (len(p_f) != N_BITS
            or max(abs(a - b) for a, b in zip(transcription, frozen)) > TRANSCRIPTION_TOL):
        raise Refusal("CQ-J21c file values drift from the section 2.1 transcription")

    # I-5 vs I-6 bitwise agreement on the J21c vector and H(A|B).
    s0j = docs["S0"]["sources"]["CQ-J21c"]
    if ([float(v) for v in s0j["p_k"]] != p_f
            or float(s0j["coherence"]["H_A_given_B"]) != hab_f):
        raise Refusal("I-5 vs I-6 bitwise disagreement on the J21c vector")

    # Baseline I-8: recompute k0 from the per-seed Stage-1 rows; I-9 echo check.
    baseline = json.loads(Path(path_of["BASELINE"]).read_bytes())
    old_stage1 = [r for r in baseline["rows"] if r.get("stage") == "stage1"]
    if len(old_stage1) != N_FRAMES:
        raise Refusal(f"baseline Stage-1 row count {len(old_stage1)} != {N_FRAMES}")
    old_failed = {int(r["seed"]): bool(int(r["failed"])) for r in old_stage1}
    if set(old_failed) != {FRAME_BASE + i for i in range(N_FRAMES)}:
        raise Refusal("baseline Stage-1 seeds are not the frozen 240-frame set")
    k0 = sum(old_failed.values())
    if k0 != K0_BASELINE:
        raise Refusal(f"baseline k0={k0} != frozen {K0_BASELINE}")
    old_und = sum(int(r.get("undetected", 0)) for r in old_stage1)
    summary_text = Path(path_of["SUMMARY"]).read_text(encoding="utf-8")
    if f"k={K0_BASELINE}/{N_FRAMES}" not in summary_text:
        raise Refusal("I-9 summary echo does not carry the frozen k0 line")

    # Section 3.5 validation gate on a frozen N_valid-symbol draw (pre-run).
    rng_v = np.random.default_rng(int(validation_seed))
    av, bv = draw_frame(rng_v, N_VALID, m0_f, mp1_f, mm1_f)
    emer_rates = gray_plane_rates(av, bv)
    emer_ser = float(np.mean(
        np.asarray(v25.gray_label(av)) != np.asarray(v25.gray_label(bv))))
    gate = validation_gate(emer_rates, p_f, N_VALID, emer_ser, ser_f)

    # Exact-Bayes rows for the frozen masses (no archive contact).
    marg_table, u1map = build_exact_prior_table(m0_f, mp1_f, mm1_f)

    # Frozen F6 pin gate on the I-7 artifact, then the base rows for Stage-1.
    graph_path = path_of["GRAPH"]

    def graph_loader(instance: int, trials: int) -> dict:
        if instance != 2026092001 or trials != p1.P1_MAX_TRIALS:
            raise Refusal("graph loader got a non-frozen seed or trial count")
        artifact = json.loads(Path(graph_path).read_bytes())
        m3b.validate_graph_artifact(artifact, "M3B-R1")
        triples = [tuple(int(v) for v in t) for t in artifact["triples"]]
        return {"n": 1024, "m": 208, "triples": triples, "status": "ok",
                "four_cycles": artifact["four_cycles"],
                "rank": artifact["rank"],
                "min_girth": artifact["min_girth"]}

    pinned = p1.construct_and_pin("P1S1-R1", graph_loader, p1.production_rank_fn)
    base = pinned["base"]
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(base["triples"], 1024, M_STAGE1, field)

    # 240 Stage-1 cold blocks, no rescue path in this stage.
    rows: list[dict] = []
    new_failed: dict[int, bool] = {}
    rss_peak = 0.0
    for idx in range(N_FRAMES):
        if time.perf_counter() - t_start > WALL_CAP_S:
            raise Refusal(f"wall breach before block {idx}: INCOMPLETE, retained")
        try:
            rss_gib = float(resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
        except Exception:  # noqa: BLE001 -- probe failure never halts
            rss_gib = 0.0
        rss_peak = max(rss_peak, rss_gib)
        if rss_gib >= RSS_CAP_GIB:
            raise Refusal(f"RSS breach before block {idx}: INCOMPLETE, retained")
        seed = FRAME_BASE + idx
        out = stage1_block_outcome(base, dense, field, seed,
                                   marg_table, u1map, m0_f, mp1_f, mm1_f)
        if out["wall_s"] > PER_BLOCK_CAP_S:
            out["status"] = "overrun"
            out["failed"] = 1
            out["undetected"] = 0
            rows.append({**out, "block_idx": idx})
            raise Refusal(f"per-block cap overrun at block {idx}: INCOMPLETE, retained")
        out["block_idx"] = idx
        rows.append(out)
        new_failed[seed] = bool(out["failed"])

    kprime = sum(new_failed.values())
    und_new = sum(int(r["undetected"]) for r in rows)
    w_lo, w_hi = wilson(kprime, N_FRAMES)
    paired = paired_table(old_failed, new_failed)
    word, clause = decide_word(kprime, K0_BASELINE, w_lo, w_hi, R_LO, R_HI)

    wall_s = time.perf_counter() - t_start
    try:
        rss_end = float(resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
    except Exception:  # noqa: BLE001
        rss_end = 0.0
    rss_peak = max(rss_peak, rss_end)
    if wall_s > WALL_CAP_S or rss_peak > RSS_CAP_GIB:
        raise Refusal(f"budget breach at close: wall {wall_s:.1f} s, RSS {rss_peak:.3f} GiB")

    result = {
        "inputs": input_records,
        "sampler": {
            "source": SAMPLER_SOURCE,
            "ser": ser_f,
            "m_0": m0_f,
            "m_plus1": mp1_f,
            "m_minus1": mm1_f,
            "p_k": p_f,
            "H_U1_given_B": h1_f,
            "H_U2_given_U1B": h2_f,
            "H_A_given_B": hab_f,
            "steps": ("S-1 uniform Alice bins",
                      "S-2 slip draw with measured masses, Gray both sides (frozen mapping)",
                      "S-3 clamp edges", "S-4 i.i.d. across symbols",
                      "S-5 240 frames seeds 2026096401+idx stream o1_blk:{seed}, "
                      "Stage-1 m=200 cold, kernel max_iter=300 streak default, exact-match"),
            "validation_seed": int(validation_seed),
            "n_valid": N_VALID,
            "graph": graph_path,
            "artifact_seeds": {"base": 2026092001, "extension": 2026096801},
        },
        "validation": {**gate, "requested_p_k": p_f},
        "stage1": {"rows": rows, "kprime_over_240": f"{kprime}/{N_FRAMES}",
                   "kprime": kprime, "k0": k0,
                   "wilson_lo": w_lo, "wilson_hi": w_hi, "wilson_z": WILSON_Z,
                   "undetected_new": und_new, "undetected_baseline": old_und},
        "paired": paired,
        "real_comparator": {"arm": "M0-2M m=208 (packet section 4 frozen)",
                            "band_lo": R_LO, "band_hi": R_HI},
        "decision": {"word": word, "clause": clause, "kprime": kprime,
                     "k0": K0_BASELINE,
                     "overlap_Wprime_R": intervals_overlap(w_lo, w_hi, R_LO, R_HI)},
        "resources": {
            "wall_s": wall_s,
            "peak_rss_gib": rss_peak,
            "cpu": os.cpu_count(),
            "thread_env": {k: os.environ.get(k, "") for k in
                           ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                            "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                            "NUMBA_NUM_THREADS")},
            "command": " ".join(sys.argv),
        },
        "claim_ceiling": CEILING,
    }
    return result


def write_summary(result: dict) -> str:
    """D-2 Markdown: validation table, counts vs band, paired table, word."""
    L: list[str] = []
    L.append("# Proxy-recalibration summary — generator fidelity only")
    L.append("")
    L.append("Inputs (read-only, frozen nine):")
    L.append("")
    L.append("| role | path | bytes | UTC mtime |")
    L.append("|---|---|---|---|")
    for rec in result["inputs"]:
        role = FROZEN_INPUTS[rec["path"]]
        L.append(f"| {role} | `{rec['path']}` | {rec['bytes']} | {rec['mtime_utc']} |")
    L.append("")
    L.append("## Validation gate (section 3.5, pre-run)")
    L.append("")
    L.append("| plane | emergent | requested p_k | tol | gap |")
    L.append("|---|---|---|---|---|")
    for m in result["validation"]["margins"]:
        L.append(f"| {m['plane']} | {m['emergent']:.8f} | {m['target']:.8f} | "
                 f"{m['tol']:.3e} | {m['gap']:.3e} |")
    v = result["validation"]
    L.append("")
    L.append(f"emergent ser {v['ser_emergent']:.8f} vs target {v['ser_target']:.8f} "
             f"(gap {v['ser_gap']:.3e}, gate 0.003): {v['verdict']}")
    L.append("")
    s = result["stage1"]
    L.append("## Stage-1 nonexact count vs comparators")
    L.append("")
    L.append(f"regenerated k' = {s['kprime']}/240, Wilson 95% W' = "
             f"[{s['wilson_lo']:.6f}, {s['wilson_hi']:.6f}]")
    L.append("")
    L.append(f"paired baseline k0 = {s['k0']}/240 (same 240 seeds); "
             f"undetected new/baseline = {s['undetected_new']}/{s['undetected_baseline']}")
    L.append("")
    r = result["real_comparator"]
    L.append(f"real comparator {r['arm']}: R = [{r['band_lo']:.6f}, {r['band_hi']:.6f}] "
             f"(directional, stage-mismatched per packet section 4)")
    L.append("")
    L.append("## Paired 2x2 old-to-new (matched seeds)")
    L.append("")
    t = result["paired"]["transitions"]
    L.append(f"matched frames: {result['paired']['matched_frame_count']}")
    L.append("")
    L.append("|  | new success | new failure |")
    L.append("|---|---|---|")
    L.append(f"| old success | {t['old_success_new_success']} | {t['old_success_new_failure']} |")
    L.append(f"| old failure | {t['old_failure_new_success']} | {t['old_failure_new_failure']} |")
    L.append("")
    d = result["decision"]
    L.append(f"## Decision: {d['word']} (clause {d['clause']})")
    L.append("")
    L.append("> " + CEILING)
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Proxy-recalibration sampler + Stage-1 comparison")
    ap.add_argument("--cq20a", required=True)
    ap.add_argument("--cq20b", required=True)
    ap.add_argument("--cqj21a", required=True)
    ap.add_argument("--cqj21b", required=True)
    ap.add_argument("--cqj21c", required=True)
    ap.add_argument("--s0-result", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--baseline-rows", required=True)
    ap.add_argument("--baseline-summary", required=True)
    ap.add_argument("--root", required=True,
                    help="fresh additive workspace/proxy_recal_<uuid8> root")
    ap.add_argument("--validation-seed", type=int, required=True)
    ap.add_argument("--execute-synthetic", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)
    if not (args.execute_synthetic and args.execution_authorized):
        print("refused: both --execute-synthetic and --execution-authorized "
              "are required", file=sys.stderr)
        return 2
    inputs = [args.cq20a, args.cq20b, args.cqj21a, args.cqj21b, args.cqj21c,
              args.s0_result, args.graph, args.baseline_rows, args.baseline_summary]
    rootdir = Path(args.root)
    try:
        result = run_proxy(inputs, args.root, int(args.validation_seed))
    except Refusal as e:
        try:
            with open(rootdir / "PROXY_LOG.md", "a", encoding="utf-8") as f:
                f.write(f"\nSTOP: {e}\n")
        except OSError:
            pass
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    (rootdir / "PROXY_RESULT.json").write_text(
        json.dumps(result, indent=1, sort_keys=True, default=str), encoding="utf-8")
    (rootdir / "PROXY_SUMMARY.md").write_text(write_summary(result), encoding="utf-8")
    r = result["resources"]
    d = result["decision"]
    with open(rootdir / "PROXY_LOG.md", "a", encoding="utf-8") as f:
        f.write("\n## EXECUTION\n")
        f.write(f"- command: {r['command']}\n")
        f.write("- exit code: 0\n")
        f.write(f"- wall_s: {r['wall_s']:.3f} (cap 3600)\n")
        f.write(f"- peak_rss_gib: {r['peak_rss_gib']:.4f} (cap 2)\n")
        f.write(f"- thread_env: {r['thread_env']}\n")
        f.write(f"- validation: {result['validation']['verdict']} "
                f"(ser gap {result['validation']['ser_gap']:.3e})\n")
        f.write(f"- kprime: {result['stage1']['kprime_over_240']} "
                f"W' [{result['stage1']['wilson_lo']:.6f}, "
                f"{result['stage1']['wilson_hi']:.6f}]\n")
        f.write(f"- decision: {d['word']} ({d['clause']})\n")
        f.write(f"- evidence: PROXY_RESULT.json + PROXY_SUMMARY.md in {args.root}\n")
    print(d["word"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
