"""Development-only harness for the NBLDPC v7 R1A/R1B/R2 engineering lanes.

This module is a *development harness*, not a qualification runner.  It
follows the accepted v6 lane patterns (canonical plan, PCG64 frame
generation, identity-freshness scan, locked Toeplitz seed records, canonical
transcript, eight-artifact package, strict read-only replay, invalid-run
retention) with the frozen v7 differences:

- one fixed `(2,3)` mother codebook (``nbldpc_formal_v7_r1a_mr0``, n=256,
  m=170) shared by both strata; syndrome disclosure exactly ``10*m = 1700``
  bits per frame plus an invoked 64-bit Toeplitz tag;
- the R1B one-repetition lane (``nbldpc_formal_v7_r1b_mr1``) reuses the exact
  R1A mother under a new identity and adds one multiplicative repetition per
  variable with deterministic public GF(1024) multipliers; the repeated
  evidence is combined into the variable prior before mother decoding and the
  transcript records only multiplier identities/control bits, never raw or
  corrected symbols; effective rate 1/6, syndrome still exactly 1700 bits;
- the R2 QSC density-evolution lane (``nbldpc_formal_v7_r2_qsc_de``) uses two
  fixed-rate GF(1024) n=1024 codebooks (m=321 for p=.20, m=458 for p=.30,
  frozen 1.15*H_q(p)/10 check-count freeze) built by deterministic PEG from
  the frozen bounded q-ary density-evolution selection (regular degree 3);
  the decoder is layered FFT-QSPA, max_iter=100, lambda=.75, workers=1;
  syndrome disclosure ``10*m`` bits (3210 / 4580) plus an invoked 64-bit tag;
- the R3 GF(32)xGF(32) multilevel lane (``nbldpc_formal_v7_r3_gf32x2``)
  reversibly splits each 10-bit symbol into high/low 5-bit words and uses two
  GF(32) n=1024 layer codes per stratum (m0=m1=404 for p=.20, m0=m1=558 for
  p=.30, frozen V7-30 check-count freeze); layer 0 (high words) is decoded
  first by flooding damped EMS (nm=32, max_iter=100, lambda=.75, workers=1),
  layer 1 (low words) only after a verified layer-0 result with priors
  restricted to Bob data, public model data and the verified layer-0 output;
  success requires BOTH layers syndrome-consistent plus one 64-bit Toeplitz
  tag on the reconstructed 10-bit symbols; all layer syndromes count as
  disclosure (5*(m0+m1) bits = 4040 / 5580 plus the invoked 64-bit tag); a
  failed layer 0 short-circuits (no layer 1, no verification);
- sacrificed configs with *fresh, mutually disjoint roots*: the 4+4 canary and
  the 16+16 development package for R1A, R1B and R2.  Roots and seed records
  are disjoint from every prior evidence root/seed found under
  ``comparison_bench/outputs_comparison/formal_ir_methods/`` (identity and
  seed freshness are enforced at plan creation/validation time);
- no confirmation material: plans contain only development frames, and no
  code path materializes confirmation seeds, rows, or statuses;
- **V7-12/V7-15 canary-plan authorization**: after the corresponding
  main-thread review, the sacrificed 4+4 CANARY plan may be prepared for real
  by passing ``production_authorized=True`` (the CLI does this only for
  ``--canary``); the official root is still locked and **execution is still
  never authorized for R1B until the V7-15 second half** — ``run``
  (production) raises for every R1B config and for every DEVELOPMENT plan
  path.  Only the explicit fake-runner ``_test_only`` lane can run/replay
  plans under a fresh writable workspace UUID root, and it never enters an
  official output root.  The official root under
  ``comparison_bench/outputs_comparison/formal_ir_methods/`` is locked for
  every config.
- **V7-12 second-half R1A canary execution authorization**: after the
  main-thread R1A canary execution decision, ``run`` may execute the R1A
  sacrificed 4+4 CANARY plan through the explicit production runner, but only
  with ``production_authorized=True`` AND the CANARY config AND an explicit
  non-official workspace output.  Every other production execution still
  raises and the official root stays locked.
- **V7-15 second-half R1B canary execution authorization**: after the
  main-thread R1B canary execution decision, ``run`` may execute the R1B
  sacrificed 4+4 CANARY plan through the explicit production runner
  (``production_runner_r1b``), but only with ``production_authorized=True``
  AND the R1B CANARY config AND an explicit non-official workspace output.
  Every DEVELOPMENT production execution (R1A and R1B) still raises and the
  official root stays locked.
- **V7-22 R2 engineering gate**: no R2 plan is prepared in the engineering
  stage; R2 production ``run`` raises for EVERY R2 config (canary and
  development) until the V7-22 main-thread canary-plan review, exactly like
  the R1B engineering stage.  Plan *preparation* is gated like the earlier
  routes (``production_authorized=True`` is accepted only for CANARY
  run-ids).
- **V7-22 second-half R2 canary execution authorization**: after the
  main-thread R2 canary execution decision, ``run`` may execute the R2
  sacrificed 4+4 CANARY plan through the explicit production runner
  (``production_runner_r2``), but only with ``production_authorized=True``
  AND the R2 CANARY config AND an explicit non-official workspace output.
  Every R2 DEVELOPMENT production execution still raises and the official
  root stays locked.
- **V7-30 R3 engineering gate**: no R3 plan is prepared in the engineering
  stage; R3 production ``run`` raises for EVERY R3 config (canary and
  development) until the V7-30 main-thread canary-plan review, exactly like
  the R2 engineering gate.  Plan *preparation* is gated like the earlier
  routes (``production_authorized=True`` is accepted only for CANARY
  run-ids).
- **V7-30 second-half R3 canary execution authorization**: after the
  main-thread R3 canary execution decision, ``run`` may execute the R3
  sacrificed 4+4 CANARY plan through the explicit production runner
  (``production_runner_r3``), but only with ``production_authorized=True``
  AND the R3 CANARY config AND an explicit non-official workspace output.
  Every R3 DEVELOPMENT production execution still raises and the official
  root stays locked.

The R1A/R1B primary production decoder is the flooding FFT-QSPA
(literature-reference schedule); layered FFT-QSPA is a frozen same-code
diagnostic.  The R2 primary decoder is the frozen layered FFT-QSPA (single
schedule).  The R3 primary decoder is the frozen flooding damped EMS
(nm=32, GF(32) two-layer).  The harness records one ``runtime_s`` per frame
(a measured environment diagnostic) and strict replay excludes that single
non-reproducible column from the otherwise exact deterministic comparison.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import nonbinary_syndrome, symbols_to_msb_bits
from .shared import (canonical_event, locked_seed_bits, materialize_seed_record,
                     toeplitz_tag, transcript_summary)
from . import nonbinary_v7_r1a_codebook as v7_cb
from . import nonbinary_v7_r1a_long as v7_long
from . import nonbinary_v7_r1b_codebook as v7_r1b_cb
from . import nonbinary_v7_r1b_long as v7_r1b_long
from . import nonbinary_v7_r2_codebook as v7_r2_cb
from . import nonbinary_v7_r2_long as v7_r2_long
from . import nonbinary_v7_r2_de as v7_r2_de
from . import nonbinary_v7_r3_codebook as v7_r3_cb
from . import nonbinary_v7_r3_long as v7_r3_long

METHOD = "nbldpc_formal_v7_r1a_mr0"
METHOD_R1B = "nbldpc_formal_v7_r1b_mr1"
METHOD_R2 = "nbldpc_formal_v7_r2_qsc_de"
METHOD_R3 = "nbldpc_formal_v7_r3_gf32x2"
_SCHEMA = "NBLDPC7DEV"
_SCHEMA_R1B = "NBLDPC7R1BDEV"
_SCHEMA_R2 = "NBLDPC7R2DEV"
_SCHEMA_R3 = "NBLDPC7R3DEV"
Q, N = 1024, 256
PS = (0.20, 0.30)
CHECK_COUNTS = {0.20: 170, 0.30: 170}
SEED_BITS = N * 10 + 63  # Toeplitz seed length for 10-bit MSB-first symbols.
CAPS = {"workers": 1, "q": 1024, "n": 256, "max_iter": 100, "lambda": .75,
        "dense_bytes_max": 16 * 1024 * 1024}
# R2 lane: n=1024, two fixed-rate codebooks (m=321/458), layered FFT-QSPA.
N_R2 = 1024
CHECK_COUNTS_R2 = {0.20: 321, 0.30: 458}
SEED_BITS_R2 = N_R2 * 10 + 63  # 10303
CAPS_R2 = {"workers": 1, "q": 1024, "n": 1024, "max_iter": 100, "lambda": .75,
           "dense_bytes_max": 80 * 1024 * 1024}
# R3 lane: n=1024 10-bit frames, two GF(32) layer codes per stratum
# (m0 = m1 = 404 / 558, frozen V7-30 check-count freeze), flooding damped EMS
# nm=32, one 64-bit tag on the reconstructed 10-bit symbols.
N_R3 = 1024
CHECK_COUNTS_R3 = {0.20: (404, 404), 0.30: (558, 558)}
SEED_BITS_R3 = N_R3 * 10 + 63  # 10303
CAPS_R3 = {"workers": 1, "q": 1024, "n": 1024, "max_iter": 100, "lambda": .75,
           "nm": 32, "field_q": 32, "dense_bytes_max": 8 * 1024 * 1024}
# Fresh roots: disjoint from every prior evidence root (v1-v6 all lie in
# 20260725..20260802, R1A canary/development in 202608047xxx/202608048xxx,
# R1B in 202608049xxx) and from each other (canary != development).
CANARY_ROOTS = {("development", .20): 202608047000, ("development", .30): 202608047100}
DEVELOPMENT_ROOTS = {("development", .20): 202608048000, ("development", .30): 202608048100}
# R1B fresh roots: disjoint from R1A canary/development AND from the R1A
# engineering-test roots (202608049xxx) so no frame/array identity can collide.
CANARY_ROOTS_R1B = {("development", .20): 202608049500, ("development", .30): 202608049600}
DEVELOPMENT_ROOTS_R1B = {("development", .20): 202608049700, ("development", .30): 202608049800}
# R2 fresh roots: disjoint from every R1A/R1B root (202608041xxx) and from
# the frozen construction seeds (202608040x).
CANARY_ROOTS_R2 = {("development", .20): 202608041000, ("development", .30): 202608041100}
DEVELOPMENT_ROOTS_R2 = {("development", .20): 202608041200, ("development", .30): 202608041300}
# R3 fresh roots: disjoint from every prior evidence root (v1-v6, R1A, R1B, R2
# all lie in 20260725..202608041xxx, engineering-test roots in
# 202608049xxx/2026080504xx) and from each other (canary != development) and
# from the frozen R3 construction seeds (202608050001/202608050002).
CANARY_ROOTS_R3 = {("development", .20): 202608050000, ("development", .30): 202608050100}
DEVELOPMENT_ROOTS_R3 = {("development", .20): 202608050200, ("development", .30): 202608050300}
_SRC = (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_ladder.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1a_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1a_long.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_development.py",
    "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v7_development.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py",
    "comparison_bench/src/comparison_bench/formal_ir/shared.py",
)
_SRC_R1B = _SRC + (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1b_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1b_long.py",
)
_SRC_R2 = _SRC + (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r2_de.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r2_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r2_long.py",
)
_SRC_R3 = _SRC + (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r3_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r3_long.py",
)
CONTRACT = "openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/specs/spec.md"
# R1B multiplier identities are public model data recorded in the transcript;
# each of the 256 GF(1024) multipliers is a 10-bit control value.
MULTIPLIER_CONTROL_BITS = 256 * 10

ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl",
             "formal_run_manifest.json", "formal_codebook_manifest.json",
             "formal_candidate_manifest.json", "formal_policy_manifest.json",
             "formal_qualification_report.json")
_ALLOWED_STATUSES = {"syndrome_consistent", "decode_failed", "decoder_error",
                     "codebook_invalid", "invalid_input", "unsupported_domain",
                     "aborted_resource_limit"}
# Frozen gate semantics: these statuses are forbidden failures for the
# development-ready gate; `decode_failed` is an honest capacity miss.
_FORBIDDEN_STATUSES = {"decoder_error", "codebook_invalid", "invalid_input",
                       "unsupported_domain", "aborted_resource_limit", "verify_failed"}
_FORBIDDEN = ("residual", "posterior", "message", "cycle", "alice", "truth",
              "error_location", "decision_hash", "decoded_symbols")


@dataclass(frozen=True)
class DevelopmentConfig:
    run_id: str
    canonical_schema: str
    method: str
    q: int
    n: int
    ps: tuple[float, ...]
    roots: Mapping[tuple[str, float], int]
    caps: Mapping[str, Any]
    seed_bits: int
    development_frames: int
    source_files: tuple[str, ...]
    contract: str


# V7-12 sacrificed canary: 4+4 development frames, fresh roots.
CANARY = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r1a_canary", canonical_schema=_SCHEMA, method=METHOD,
    q=Q, n=N, ps=PS,
    roots=CANARY_ROOTS, caps=CAPS, seed_bits=SEED_BITS, development_frames=4,
    source_files=_SRC, contract=CONTRACT)

# V7-13 sacrificed development: 16+16 development frames, fresh roots distinct
# from the canary roots.
DEVELOPMENT = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r1a_development", canonical_schema=_SCHEMA, method=METHOD,
    q=Q, n=N, ps=PS,
    roots=DEVELOPMENT_ROOTS, caps=CAPS, seed_bits=SEED_BITS, development_frames=16,
    source_files=_SRC, contract=CONTRACT)

# V7-15 R1B sacrificed canary: 4+4 development frames over the R1B one
# repetition identity, fresh roots distinct from every R1A root.
CANARY_R1B = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r1b_canary", canonical_schema=_SCHEMA_R1B, method=METHOD_R1B,
    q=Q, n=N, ps=PS,
    roots=CANARY_ROOTS_R1B, caps=CAPS, seed_bits=SEED_BITS, development_frames=4,
    source_files=_SRC_R1B, contract=CONTRACT)

# V7-15 R1B sacrificed development: 16+16 development frames, fresh roots
# distinct from the R1B canary roots.
DEVELOPMENT_R1B = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r1b_development", canonical_schema=_SCHEMA_R1B, method=METHOD_R1B,
    q=Q, n=N, ps=PS,
    roots=DEVELOPMENT_ROOTS_R1B, caps=CAPS, seed_bits=SEED_BITS, development_frames=16,
    source_files=_SRC_R1B, contract=CONTRACT)

# V7-22 R2 sacrificed canary: 4+4 development frames over the R2 QSC-DE
# identity (n=1024, m=321/458), fresh roots disjoint from every R1A/R1B root.
CANARY_R2 = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r2_canary", canonical_schema=_SCHEMA_R2, method=METHOD_R2,
    q=Q, n=N_R2, ps=PS,
    roots=CANARY_ROOTS_R2, caps=CAPS_R2, seed_bits=SEED_BITS_R2, development_frames=4,
    source_files=_SRC_R2, contract=CONTRACT)

# V7-22 R2 sacrificed development: 16+16 development frames, fresh roots
# distinct from the R2 canary roots.
DEVELOPMENT_R2 = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r2_development", canonical_schema=_SCHEMA_R2, method=METHOD_R2,
    q=Q, n=N_R2, ps=PS,
    roots=DEVELOPMENT_ROOTS_R2, caps=CAPS_R2, seed_bits=SEED_BITS_R2, development_frames=16,
    source_files=_SRC_R2, contract=CONTRACT)

# V7-30 R3 sacrificed canary: 4+4 development frames over the R3 GF(32)xGF(32)
# multilevel identity (n=1024, m0=m1=404/558), fresh roots disjoint from every
# prior R1A/R1B/R2 root and from the frozen R3 construction seeds.
CANARY_R3 = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r3_canary", canonical_schema=_SCHEMA_R3, method=METHOD_R3,
    q=Q, n=N_R3, ps=PS,
    roots=CANARY_ROOTS_R3, caps=CAPS_R3, seed_bits=SEED_BITS_R3, development_frames=4,
    source_files=_SRC_R3, contract=CONTRACT)

# V7-30 R3 sacrificed development: 16+16 development frames, fresh roots
# distinct from the R3 canary roots.
DEVELOPMENT_R3 = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v7_r3_development", canonical_schema=_SCHEMA_R3, method=METHOD_R3,
    q=Q, n=N_R3, ps=PS,
    roots=DEVELOPMENT_ROOTS_R3, caps=CAPS_R3, seed_bits=SEED_BITS_R3, development_frames=16,
    source_files=_SRC_R3, contract=CONTRACT)

CONFIG = DEVELOPMENT  # CLI default: the 16+16 development config (plan-only).


def is_r1b(config) -> bool:
    """True when the config drives the R1B one-repetition lane."""
    return getattr(config, "method", None) == METHOD_R1B


def is_r2(config) -> bool:
    """True when the config drives the R2 QSC-DE lane."""
    return getattr(config, "method", None) == METHOD_R2


def is_r3(config) -> bool:
    """True when the config drives the R3 GF(32)xGF(32) multilevel lane."""
    return getattr(config, "method", None) == METHOD_R3


def codebook(config: DevelopmentConfig | None = CONFIG) -> tuple[dict[str, Any], Any]:
    if is_r3(config):
        return v7_r3_cb.codebook()
    if is_r2(config):
        return v7_r2_cb.codebook()
    if is_r1b(config):
        return v7_r1b_cb.codebook()
    return v7_cb.codebook()


def check_count(p: float, config: DevelopmentConfig | None = CONFIG) -> int:
    if is_r3(config):
        # The R3 row carries the TOTAL per-frame check count m0 + m1; the
        # per-layer counts are recorded in the codebook manifest.
        try:
            m0, m1 = CHECK_COUNTS_R3[float(p)]
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid NBLDPC7R3 stratum")
        return m0 + m1
    table = CHECK_COUNTS_R2 if is_r2(config) else CHECK_COUNTS
    try:
        return table[float(p)]
    except (KeyError, TypeError, ValueError):
        raise ValueError("invalid NBLDPC7 stratum")


def production_runner(bob_symbols, syndrome, manifest, matrices, *, check_count, p):
    return v7_long.production_runner(bob_symbols, syndrome, manifest, matrices,
                                     check_count=check_count, p=p)


def production_runner_r1b(bob_symbols, repeated_symbols, syndrome, manifest, matrices, *, check_count, p):
    return v7_r1b_long.production_runner(bob_symbols, repeated_symbols, syndrome, manifest, matrices,
                                         check_count=check_count, p=p)


def production_runner_r2(bob_symbols, syndrome, manifest, matrices, *, check_count, p):
    return v7_r2_long.production_runner(bob_symbols, syndrome, manifest, matrices,
                                        check_count=check_count, p=p)


def production_runner_r3(bob_symbols, syndrome0, syndrome1, manifest, matrices, *, check_count, p):
    return v7_r3_long.production_runner(bob_symbols, syndrome0, syndrome1, manifest, matrices,
                                        check_count=check_count, p=p)


# ---------------------------------------------------------------- small helpers

def _compact(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
def _sha(x): return hashlib.sha256(x).hexdigest()
def _root(): return Path(__file__).resolve().parents[4]
def _official(config): return (_root() / "comparison_bench/outputs_comparison/formal_ir_methods" / config.run_id).resolve()
def _put(p, x):
    with p.open("xb") as f:
        f.write(json.dumps(x, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False).encode() + b"\n")
def _csv(p, rows):
    with p.open("x", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}) or ["status"])
        w.writeheader(); w.writerows(rows)
def _rows(p):
    with p.open(newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))

def _resolve_output(config, output, _test_only):
    official = _official(config)
    if output is None:
        if _test_only:
            raise ValueError("test-only lane requires an explicit workspace output")
        raise ValueError(f"official v7 development root is locked until V7-12 review: {official}")
    chosen = Path(output).resolve()
    if chosen == official:
        raise ValueError("official v7 development root is locked until V7-12 review")
    return chosen

def _frame(config, p, index):
    rng = np.random.Generator(np.random.PCG64(config.roots["development", p] + index))
    alice = rng.integers(0, config.q, config.n, dtype=np.int64)
    mask = rng.random(config.n) < p
    error = rng.integers(1, config.q, config.n, dtype=np.int64)
    bob = alice.copy(); bob[mask] ^= error[mask]
    row = {"frame_id": f"{config.method}_q{config.q}_p{int(p * 100):02d}_development_{index:03d}",
           "p": p, "role": "development", "index": index,
           "seed": config.roots["development", p] + index,
           "alice": alice.tolist(), "bob": bob.tolist()}
    if is_r1b(config):
        # One multiplicative repetition: z_v = mult_v * x_v xor e'_v with an
        # independent q-ary-symmetric error; the multiplier is public model
        # data derived from the frozen R1B multiplier seed.
        field = GF2mField.create(config.q)
        multipliers = v7_r1b_cb.multipliers()
        repeated = np.empty(config.n, dtype=np.int64)
        for col in range(config.n):
            repeated[col] = field.mul(int(multipliers[col]), int(alice[col]))
        mask2 = rng.random(config.n) < p
        error2 = rng.integers(1, config.q, config.n, dtype=np.int64)
        repeated[mask2] ^= error2[mask2]
        row["repeated"] = repeated.tolist()
        row["array_sha256"] = _sha(alice.astype("<i8").tobytes() + bob.astype("<i8").tobytes()
                                   + repeated.astype("<i8").tobytes())
    else:
        row["array_sha256"] = _sha(alice.astype("<i8").tobytes() + bob.astype("<i8").tobytes())
    row["atomic_keys"] = [f"{config.method}|development|{p}|{index}|{j}" for j in range(config.n)]
    return row

def _excluded(path, exclude):
    if exclude is None:
        return False
    target = Path(exclude).resolve(); current = Path(path).resolve()
    return current == target if target.suffix else current.is_relative_to(target)

def _prior_seed_ids(exclude=None):
    found = set(); base = _root() / "comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():
        return found
    for path in base.rglob("*.json"):
        if _excluded(path, exclude):
            continue
        try:
            text = path.read_text(encoding="utf8")
        except OSError:
            continue
        found.update(re.findall(r'"seed_id"\s*:\s*"([0-9a-f]{64})"', text))
    return found

def _prior_identities(exclude=None):
    found = {"roots": set(), "frame_ids": set(), "array_sha256": set(), "atomic_keys": set()}
    base = _root() / "comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():
        return found
    for path in base.rglob("pre_run_plan.json"):
        if _excluded(path, exclude):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf8"))
        except (OSError, ValueError):
            continue
        roots = doc.get("roots", {}); found["roots"].update(map(str, roots.values()))
        for frame in doc.get("frames", []):
            if isinstance(frame, dict):
                found["frame_ids"].add(str(frame.get("frame_id", "")))
                found["array_sha256"].add(str(frame.get("array_sha256", "")))
                found["atomic_keys"].update(map(str, frame.get("atomic_keys", [])))
    return found

def _identity_overlap(config, frames, *, exclude=None):
    old = _prior_identities(exclude); roots = {str(x) for x in config.roots.values()}
    now = {"roots": roots, "frame_ids": {str(x["frame_id"]) for x in frames},
           "array_sha256": {str(x["array_sha256"]) for x in frames},
           "atomic_keys": {str(k) for x in frames for k in x["atomic_keys"]}}
    return {key: sorted(now[key] & old[key]) for key in now}

def _provenance(config):
    root = _root(); cb, _ = codebook(config)
    candidate = {"method": config.method,
                 "strata": {f"{p:.2f}": check_count(p, config) for p in config.ps},
                 "codebook_manifest_id": cb["manifest_id"]}
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = "unavailable"
    return {"source_sha256": {p: _sha((root / p).read_bytes()) for p in config.source_files},
            "contract_sha256": _sha((root / config.contract).read_bytes()),
            "candidate_sha256": _sha(_compact(candidate)),
            "codebook_manifest_id": cb["manifest_id"],
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "git_commit": commit}

def _policy_doc(config):
    if is_r3(config):
        # Float keys do not survive the JSON round-trip, so the frozen
        # per-stratum records are pre-stringified exactly as json.dumps would
        # render them; strict replay compares against this.
        return {"policy_id": "nbldpc_v7_r3_gf32x2",
                "decoder": "ems_nm32_gf32_two_layer_flooding_l0_first_l1_conditional",
                "nm": v7_r3_long._NM, "max_iter": v7_r3_long._MAX_ITER,
                "lambda": v7_r3_long._LAMBDA, "schedule": v7_r3_long._SCHEDULE, "workers": 1,
                "split": v7_r3_cb._SPLIT_MAPPING,
                "verification": "single_64_bit_toeplitz_tag_on_reconstructed_10_bit_symbols",
                "layer_syndrome_disclosure_bits": 5,
                "check_count_freeze": {str(p): {"m0": v7_r3_cb._CHECK_COUNTS[p],
                                                "m1": v7_r3_cb._CHECK_COUNTS[p]}
                                       for p in (0.20, 0.30)},
                "strata": [{"p": p, "check_count": check_count(p, config)} for p in config.ps]}
    if is_r2(config):
        # Float keys do not survive the JSON round-trip (they become strings),
        # so the frozen per-stratum records are pre-stringified exactly as
        # json.dumps would render them; strict replay compares against this.
        return {"policy_id": "nbldpc_v7_r2_qsc_de",
                "decoder": "layered_fft_qspa_n1024_single_schedule",
                "lambda": .75, "max_iter": 100, "schedule": "layered", "workers": 1,
                "selection": {"method": "qary_density_evolution",
                              "n_candidates_max": v7_r2_de.MAX_CANDIDATES,
                              "threshold_proxies": {str(p): v for p, v in v7_r2_cb._DE_THRESHOLD_PROXIES.items()},
                              "check_count_freeze": {str(p): v for p, v in v7_r2_cb._CHECK_COUNTS.items()}},
                "strata": [{"p": p, "check_count": check_count(p, config)} for p in config.ps]}
    if is_r1b(config):
        return {"policy_id": "nbldpc_v7_r1b_mr1",
                "decoder": "prior_combined_flooding_fft_qspa_n256_primary_layered_diagnostic",
                "lambda": .75, "max_iter": 100, "repetition_depth": 1, "effective_rate": 1 / 6,
                "strata": [{"p": p, "check_count": check_count(p, config)} for p in config.ps]}
    return {"policy_id": "nbldpc_v7_r1a_mr0",
            "decoder": "flooding_fft_qspa_n256_primary_layered_diagnostic",
            "lambda": .75, "max_iter": 100,
            "strata": [{"p": p, "check_count": check_count(p, config)} for p in config.ps]}

def _candidate_doc(config, cb=None):
    cb = codebook(config)[0] if cb is None else cb
    return {"method": config.method,
            "strata": {f"{p:.2f}": check_count(p, config) for p in config.ps},
            "codebook_manifest_id": cb["manifest_id"]}

def _tag(config, symbols, seed):
    return toeplitz_tag(symbols_to_msb_bits(symbols, config.q), locked_seed_bits(seed, config.seed_bits))

def _seed_keys(config, frames):
    return {frame["frame_id"] for frame in frames}


# ---------------------------------------------------------------- plan

def expected_plan(config):
    frames = [_frame(config, p, i) for p in config.ps for i in range(config.development_frames)]
    seeds = {frame["frame_id"]: materialize_seed_record(config.seed_bits) for frame in frames}
    return {"canonical_schema": config.canonical_schema, "run_id": config.run_id,
            "method": config.method, "q": config.q, "n": config.n,
            "roots": {f"{role}|{p}": v for (role, p), v in config.roots.items()},
            "caps": dict(config.caps), "frames": frames,
            "identity_overlap": _identity_overlap(config, frames),
            "development_toeplitz_seeds": seeds, "provenance": _provenance(config)}

def _validate_plan(config, plan, *, plan_path=None):
    if plan.get("canonical_schema") != config.canonical_schema or plan.get("run_id") != config.run_id \
            or plan.get("method") != config.method or plan.get("q") != config.q or plan.get("n") != config.n:
        raise ValueError("plan identity")
    if plan.get("roots") != {f"{role}|{p}": v for (role, p), v in config.roots.items()} \
            or plan.get("caps") != dict(config.caps) or plan.get("provenance") != _provenance(config):
        raise ValueError("plan contract/provenance")
    expected = [_frame(config, p, i) for p in config.ps for i in range(config.development_frames)]
    frames = plan.get("frames")
    if frames != expected or any(x.get("role") != "development" for x in frames):
        raise ValueError("confirmation or foreign frame leaked into plan")
    if plan.get("identity_overlap") != _identity_overlap(config, frames, exclude=plan_path) \
            or any(plan["identity_overlap"].values()):
        raise ValueError("identity freshness")
    seeds = plan.get("development_toeplitz_seeds", {})
    if set(seeds) != _seed_keys(config, frames):
        raise ValueError("development seed binding")
    ids = []
    for record in seeds.values():
        locked_seed_bits(record, config.seed_bits); ids.append(record["seed_id"])
    if len(ids) != len(set(ids)) or set(ids) & _prior_seed_ids(exclude=plan_path):
        raise ValueError("seed freshness")
    return True

def create_plan(output=None, *, config=CONFIG, _test_only=False, production_authorized=False):
    if not _test_only:
        # The sacrificed CANARY plan may be prepared only after its main-thread
        # review: R1A CANARY (V7-12), R1B CANARY (V7-15), R2 CANARY (V7-22) and
        # R3 CANARY (V7-30) with the explicit production_authorized flag; every
        # DEVELOPMENT plan still refuses.
        if not production_authorized or config.run_id not in (CANARY.run_id, CANARY_R1B.run_id,
                                                              CANARY_R2.run_id, CANARY_R3.run_id):
            raise ValueError("plan preparation is not authorized before V7-12/V7-15/V7-22/V7-30 main-thread review")
    out = _resolve_output(config, output, _test_only)
    if out.exists():
        raise FileExistsError(out)
    plan = expected_plan(config); _validate_plan(config, plan)
    out.mkdir(parents=True); _put(out / "pre_run_plan.json", plan)
    return plan


# ---------------------------------------------------------------- execution

def _events(config, frame, syndrome, status, *, invoked, tag, seed, disclosed_bits, decision):
    events = []; eid = 0
    def add(kind, direction, parent, key=0, public=0, payload=None):
        nonlocal eid
        events.append({"event_id": eid, "frame_key": frame["frame_id"], "method": config.method,
                       "event_type": kind, "direction": direction, "parent_event_id": parent,
                       "pass_id": eid, "plane_id": "q1024", "key_dependent_bits": key,
                       "public_control_bits": public, "payload": payload or {"reason": kind}})
        eid += 1
    add("SYNDROME_INITIAL", "alice_to_bob", eid - 1, disclosed_bits, 0, {"syndrome": list(syndrome)})
    if is_r1b(config):
        # One multiplicative repetition: the deterministic public GF(1024)
        # multiplier identities are control-plane data; raw or corrected
        # symbols are never recorded (mirrors the v7 _FORBIDDEN discipline).
        add("MULTIPLIER_REPETITION", "control", eid - 1, 0, MULTIPLIER_CONTROL_BITS,
            {"matrix_id": v7_r1b_cb.multiplier_spec_id(),
             "rate_id": "r1b_mr1_rate_1_over_6",
             "value": list(v7_r1b_cb.multipliers()),
             "note": "deterministic GF(1024) multiplier identities (public model data); repetition depth 1; no raw or corrected symbols"})
    add("DECODER_STAGE1", "bob_local", eid - 1, 0, 0, {"reason": status})
    if invoked:
        add("VERIFICATION_TAG_STAGE1", "alice_to_bob", eid - 1, 64, config.seed_bits,
            {"tag": tag.hex(), "seed_id": seed["seed_id"], "seed_bit_length": config.seed_bits})
    add("STAGE_DECISION_STAGE1", "control", eid - 1, 0, 2, {"reason": decision})
    return events

def _frame_result(config, frame, runner, cb, mats, seed):
    """Run one development frame through the explicit runner and bind the
    outcome, verification accounting and canonical events.  Always returns a
    complete (row, events, final_status, raw_status) tuple; invalid runner
    output fails closed to ``decoder_error``/``aborted_resource_limit``."""
    if is_r3(config):
        return _frame_result_r3(config, frame, runner, cb, mats, seed)
    p = float(frame["p"]); checks = check_count(p, config)
    # R2 (like v6) carries one matrix per stratum in a dict; R1A/R1B carry a
    # single shared matrix.  Select the per-stratum matrix before computing the
    # disclosed syndrome.
    matrix = mats[checks] if is_r2(config) else mats
    syndrome = nonbinary_syndrome(matrix, frame["alice"], GF2mField.create(config.q))
    started = time.monotonic()
    if is_r1b(config):
        raw = runner(frame["bob"], frame["repeated"], syndrome, cb, mats, check_count=checks, p=p)
    else:
        raw = runner(frame["bob"], syndrome, cb, mats, check_count=checks, p=p)
    runtime_s = round(time.monotonic() - started, 3)
    if not isinstance(raw, Mapping):
        raw = {}
    status = raw.get("status", "decoder_error")
    if status not in _ALLOWED_STATUSES:
        status, reason = "decoder_error", "unknown_stage_status"
    else:
        reason = status
    try:
        iterations = int(raw.get("iterations", 0))
    except (TypeError, ValueError):
        iterations = 0
    if not 0 <= iterations <= 100:
        status, reason = "aborted_resource_limit", "iterations"
    final, tag, invoked = status, b"", False
    if status == "syndrome_consistent":
        try:
            decoded = tuple(int(x) for x in raw["decoded_symbols"])
            valid = len(decoded) == config.n and all(0 <= x < config.q for x in decoded)
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            status, reason = "decoder_error", "decoded_symbols"
        else:
            alice_tag = _tag(config, frame["alice"], seed)
            bob_tag = _tag(config, decoded, seed)
            final = "verified_success" if alice_tag == bob_tag else "verify_failed"
            tag = alice_tag; invoked = True
    disclosed = checks * 10
    decision = "00" if final == "verified_success" else "10"
    events = _events(config, frame, syndrome, reason, invoked=invoked, tag=tag, seed=seed,
                     disclosed_bits=disclosed, decision=decision)
    summary = transcript_summary(events)
    row = {"frame_id": frame["frame_id"], "stratum_p": p, "qualification_role": "development",
           "status": final, "denominator_included": True, "check_count": checks,
           "iterations": iterations, "verification_invoked": invoked,
           "verification_attempts": 1 if invoked else 0,
           "outcome_epsilon_ec": 2.0 ** -64 if final == "verified_success" else None,
           "array_sha256": frame["array_sha256"], "transcript_event_count": len(events),
           "runtime_s": runtime_s, **summary}
    return row, events, final, status


def _events_r3(config, frame, syndrome0, syndrome1, layer0_status, layer1_status, *,
               invoked, tag, seed, m0, m1, decision):
    """Canonical R3 events: both layer syndromes are disclosed (5 bits per
    GF(32) check); a failed layer 0 short-circuits (no layer-1 event, no
    verification); the layer-1 syndrome event appears only after a verified
    layer-0 result.  Raw or corrected symbols are never recorded."""
    events = []; eid = 0
    def add(kind, direction, parent, key=0, public=0, payload=None):
        nonlocal eid
        events.append({"event_id": eid, "frame_key": frame["frame_id"], "method": config.method,
                       "event_type": kind, "direction": direction, "parent_event_id": parent,
                       "pass_id": eid, "plane_id": "q32", "key_dependent_bits": key,
                       "public_control_bits": public, "payload": payload or {"reason": kind}})
        eid += 1
    add("SYNDROME_INITIAL", "alice_to_bob", eid - 1, 5 * m0, 0,
        {"syndrome": list(syndrome0), "note": "layer 0 GF(32) syndrome on the high 5-bit words (5*m0 bits)"})
    add("DECODER_STAGE1", "bob_local", eid - 1, 0, 0, {"reason": layer0_status})
    if layer0_status == "syndrome_consistent":
        add("SYNDROME_INITIAL_LAYER1", "alice_to_bob", eid - 1, 5 * m1, 0,
            {"syndrome": list(syndrome1), "note": "layer 1 GF(32) syndrome on the low 5-bit words (5*m1 bits)"})
        add("DECODER_STAGE2", "bob_local", eid - 1, 0, 0, {"reason": layer1_status})
        if invoked:
            add("VERIFICATION_TAG_STAGE1", "alice_to_bob", eid - 1, 64, config.seed_bits,
                {"tag": tag.hex(), "seed_id": seed["seed_id"], "seed_bit_length": config.seed_bits})
    add("STAGE_DECISION_STAGE1", "control", eid - 1, 0, 2, {"reason": decision})
    return events


def _frame_result_r3(config, frame, runner, cb, mats, seed):
    """R3 two-layer frame runner: both layer syndromes are computed from the
    frame (public data), the runner decodes layer 0 first and layer 1 only
    after a verified layer-0 result; the single 64-bit tag is applied to the
    reconstructed 10-bit symbols.  Disclosure: 5*(m0+m1) bits when layer 0 is
    consistent, 5*m0 when layer 0 fails (short-circuit, no layer 1 and no
    verification), plus 64 tag bits when the tag is invoked."""
    p = float(frame["p"]); m0, m1 = CHECK_COUNTS_R3[p]; checks = m0 + m1
    field = GF2mField.create(32)
    high, low = v7_r3_cb.split_vector(frame["alice"])
    syndrome0 = nonbinary_syndrome(mats[(m0, 0)], high, field)
    syndrome1 = nonbinary_syndrome(mats[(m1, 1)], low, field)
    started = time.monotonic()
    raw = runner(frame["bob"], syndrome0, syndrome1, cb, mats, check_count=checks, p=p)
    runtime_s = round(time.monotonic() - started, 3)
    if not isinstance(raw, Mapping):
        raw = {}
    status = raw.get("status", "decoder_error")
    if status not in _ALLOWED_STATUSES:
        status, reason = "decoder_error", "unknown_stage_status"
    else:
        reason = status
    try:
        iterations = int(raw.get("iterations", 0))
    except (TypeError, ValueError):
        iterations = 0
    # R3 runs at most max_iter per layer, so the total iteration count may
    # reach 200 (the R1A/R1B/R2 lanes cap at 100).
    if not 0 <= iterations <= 200:
        status, reason = "aborted_resource_limit", "iterations"
    if status == "syndrome_consistent":
        # The R3 decoder returns syndrome_consistent only when BOTH layers are
        # consistent; the single tag is applied to the 10-bit reconstruction.
        layer0_consistent = layer1_consistent = layer1_invoked = True
    else:
        layer0_consistent = bool(raw.get("layer0_consistent", False))
        layer1_consistent = bool(raw.get("layer1_consistent", False))
        layer1_invoked = bool(raw.get("layer1_invoked", False))
    final, tag, invoked = status, b"", False
    if status == "syndrome_consistent":
        try:
            decoded = tuple(int(x) for x in raw["decoded_symbols"])
            valid = len(decoded) == config.n and all(0 <= x < config.q for x in decoded)
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            status, reason = "decoder_error", "decoded_symbols"
            layer0_consistent = layer1_consistent = layer1_invoked = False
        else:
            alice_tag = _tag(config, frame["alice"], seed)
            bob_tag = _tag(config, decoded, seed)
            final = "verified_success" if alice_tag == bob_tag else "verify_failed"
            tag = alice_tag; invoked = True
    disclosed = 5 * (m0 + m1) if layer0_consistent else 5 * m0
    if invoked:
        disclosed += 64
    decision = "00" if final == "verified_success" else "10"
    layer0_status = "syndrome_consistent" if layer0_consistent else reason
    layer1_status = "syndrome_consistent" if layer1_consistent else (
        reason if layer1_invoked else "not_invoked")
    events = _events_r3(config, frame, syndrome0, syndrome1, layer0_status, layer1_status,
                        invoked=invoked, tag=tag, seed=seed, m0=m0, m1=m1, decision=decision)
    summary = transcript_summary(events)
    row = {"frame_id": frame["frame_id"], "stratum_p": p, "qualification_role": "development",
           "status": final, "denominator_included": True, "check_count": checks,
           "iterations": iterations, "verification_invoked": invoked,
           "verification_attempts": 1 if invoked else 0,
           "outcome_epsilon_ec": 2.0 ** -64 if final == "verified_success" else None,
           "array_sha256": frame["array_sha256"], "transcript_event_count": len(events),
           "runtime_s": runtime_s, **summary}
    return row, events, final, status

def _artifact_hashes(out):
    return {name: _sha((out / name).read_bytes()) for name in ARTIFACTS
            if name not in {"formal_run_manifest.json", "formal_qualification_report.json"}
            and (out / name).exists()}

def _write_events(path, events):
    with path.open("xb") as handle:
        for event in events:
            handle.write(canonical_event(event))

def _report_doc(config, out, run_status, rows):
    counts = {f"{p:.2f}": sum(float(r["stratum_p"]) == p and r["status"] == "verified_success"
                              for r in rows) for p in config.ps}
    return {"run_id": config.run_id, "run_status": run_status, "promoted": False,
            "per_stratum_verified_success": counts,
            "formal_run_manifest_sha256": _sha((out / "formal_run_manifest.json").read_bytes())}

def _finalize_invalid(config, out, exc, state):
    rows, events = state["rows"], state["events"]
    if not (out / "formal_frame_outcomes.csv").exists():
        _csv(out / "formal_frame_outcomes.csv", rows)
    if not (out / "formal_transcript.jsonl").exists():
        _write_events(out / "formal_transcript.jsonl", events)
    cb = state.get("codebook")
    if cb is None:
        cb, _ = codebook(config)
    if not (out / "formal_codebook_manifest.json").exists():
        _put(out / "formal_codebook_manifest.json", cb)
    if not (out / "formal_candidate_manifest.json").exists():
        _put(out / "formal_candidate_manifest.json", _candidate_doc(config, cb))
    if not (out / "formal_policy_manifest.json").exists():
        _put(out / "formal_policy_manifest.json", _policy_doc(config))
    _put(out / "formal_run_manifest.json",
         {"run_id": config.run_id, "run_status": "invalid_run",
          "reason": f"{type(exc).__name__}: {exc}", "outcome_count": len(rows),
          "artifacts": _artifact_hashes(out)})
    _put(out / "formal_qualification_report.json", _report_doc(config, out, "invalid_run", rows))

def _write_normal(config, out, rows, events, cb):
    _put(out / "formal_codebook_manifest.json", cb)
    _put(out / "formal_candidate_manifest.json", _candidate_doc(config, cb))
    _put(out / "formal_policy_manifest.json", _policy_doc(config))
    _csv(out / "formal_frame_outcomes.csv", rows)
    _write_events(out / "formal_transcript.jsonl", events)
    _put(out / "formal_run_manifest.json",
         {"run_id": config.run_id, "run_status": "development_completed",
          "outcome_count": len(rows), "artifacts": _artifact_hashes(out)})
    _put(out / "formal_qualification_report.json", _report_doc(config, out, "development_completed", rows))
    return {"run_status": "development_completed", "promoted": False, "outcome_count": len(rows)}

def run(output=None, *, config=CONFIG, runner: Callable | None = None, _test_only=False,
        fatal_hook: Callable[[int], None] | None = None, production_authorized: bool = False):
    if not _test_only and is_r2(config) and config is not CANARY_R2:
        # V7-22 engineering gate: R2 production execution (canary AND
        # development) was blocked until the V7-22 main-thread canary-plan
        # review.  After that review the R2 sacrificed CANARY may execute
        # below through production_authorized (mirror of R1A/R1B); every R2
        # DEVELOPMENT production run still raises here and the official root
        # stays locked.
        raise ValueError("R2 development execution is blocked; only the sacrificed R2 CANARY may execute")
    if not _test_only and is_r3(config) and config is not CANARY_R3:
        # V7-32 engineering gate: R3 production execution (canary AND
        # development) was blocked until the V7-32 main-thread canary-plan
        # review.  After that review the R3 sacrificed CANARY may execute
        # below through production_authorized (mirror of R1A/R1B/R2); every R3
        # DEVELOPMENT production run still raises here and the official root
        # stays locked.
        raise ValueError("R3 development execution is blocked; only the sacrificed R3 CANARY may execute")
    if not _test_only and not production_authorized:
        raise ValueError("development execution is not authorized before V7-12/V7-15 main-thread review")
    if production_authorized:
        # V7-12/V7-15/V7-22/V7-30 second half: the sacrificed CANARY configs
        # (R1A, R1B, R2 and R3) may execute, and only with an explicit
        # non-official workspace output and an explicit production runner.
        # Every DEVELOPMENT config still raises above or here; the official
        # root stays locked.
        if config not in (CANARY, CANARY_R1B, CANARY_R2, CANARY_R3):
            raise ValueError("production execution is authorized only for the sacrificed CANARY configs "
                             "(R1A/R1B/R2/R3); DEVELOPMENT production execution is blocked")
        if output is None:
            raise ValueError("production execution requires an explicit workspace output")
        if runner is None:
            raise ValueError("production execution requires an explicit production runner")
    elif runner is None:
        raise ValueError("test-only development execution requires an explicit fake runner")
    out = _resolve_output(config, output, _test_only)
    if {x.name for x in out.iterdir()} != {"pre_run_plan.json"}:
        raise ValueError("run requires plan-only directory")
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    _validate_plan(config, plan, plan_path=plan_path)
    state = {"rows": [], "events": [], "codebook": None, "plan": plan}
    try:
        cb, mats = codebook(config); state["codebook"] = cb
        for frame in plan["frames"]:
            seed = plan["development_toeplitz_seeds"][frame["frame_id"]]
            row, events, _, _ = _frame_result(config, frame, runner, cb, mats, seed)
            state["rows"].append(row); state["events"] += events
            if fatal_hook is not None:
                fatal_hook(len(state["rows"]))
        return _write_normal(config, out, state["rows"], state["events"], cb)
    except Exception as exc:
        _finalize_invalid(config, out, exc, state)
        raise


# ---------------------------------------------------------------- strict replay

def _reject_diagnostics(value):
    if isinstance(value, Mapping):
        for key, item in value.items():
            if any(token in str(key).lower() for token in _FORBIDDEN):
                raise ValueError("forbidden diagnostic")
            _reject_diagnostics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_diagnostics(item)

def _same(expected, actual):
    right = dict(actual)
    if right.get("outcome_epsilon_ec") == "":
        right["outcome_epsilon_ec"] = None
    # ponytail: runtime_s is a measured environment diagnostic (never
    # reproducible); it is excluded from the otherwise exact strict-replay
    # comparison. Every scientific column must still match exactly.
    expected_clean = dict(expected); expected_clean.pop("runtime_s", None)
    right.pop("runtime_s", None)
    return {k: str(v) for k, v in expected_clean.items()} == {k: str(v) for k, v in right.items()}

def _expected_frames(config, plan):
    return [(frame, plan["development_toeplitz_seeds"][frame["frame_id"]])
            for frame in plan["frames"]]

def _verify_invalid(config, out, plan, verifier_runner):
    manifest = json.loads((out / "formal_run_manifest.json").read_text())
    report = json.loads((out / "formal_qualification_report.json").read_text())
    if {x.name for x in out.iterdir()} != set(ARTIFACTS) \
            or set(manifest) != {"run_id", "run_status", "reason", "outcome_count", "artifacts"} \
            or set(report) != {"run_id", "run_status", "promoted", "per_stratum_verified_success",
                               "formal_run_manifest_sha256"}:
        raise ValueError("invalid package shape")
    if manifest.get("run_id") != config.run_id or manifest.get("run_status") != "invalid_run" \
            or not isinstance(manifest.get("reason"), str) or not manifest["reason"] \
            or manifest.get("artifacts") != _artifact_hashes(out) \
            or report != _report_doc(config, out, "invalid_run", _rows(out / "formal_frame_outcomes.csv")):
        raise ValueError("invalid package identity")
    rows = _rows(out / "formal_frame_outcomes.csv")
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    if b"".join(canonical_event(event) for event in events) != (out / "formal_transcript.jsonl").read_bytes() \
            or manifest["outcome_count"] != len(rows):
        raise ValueError("invalid transcript")
    cb = json.loads((out / "formal_codebook_manifest.json").read_text())
    candidate = json.loads((out / "formal_candidate_manifest.json").read_text())
    policy = json.loads((out / "formal_policy_manifest.json").read_text())
    if not rows:
        if cb != codebook(config)[0] or candidate != _candidate_doc(config, cb) \
                or policy != _policy_doc(config) or events:
            raise ValueError("invalid empty sentinel")
        return {"verified": True, "run_status": "invalid_run", "promoted": False}
    if cb != codebook(config)[0] or candidate != _candidate_doc(config, cb) or policy != _policy_doc(config):
        raise ValueError("invalid partial provenance")
    expected = _expected_frames(config, plan)
    if len(rows) > len(expected):
        raise ValueError("invalid partial row count")
    if [row.get("frame_id") for row in rows] != [frame["frame_id"] for frame, _ in expected[:len(rows)]]:
        raise ValueError("invalid partial order")
    cursor = 0; _, mats = codebook(config)
    for index, (actual, (frame, seed)) in enumerate(zip(rows, expected)):
        replay, events_row, _, _ = _frame_result(config, frame, verifier_runner, codebook(config)[0], mats, seed)
        count = int(actual.get("transcript_event_count", 0)); piece = events[cursor:cursor + count]; cursor += count
        if not _same(replay, actual) or piece != events_row:
            raise ValueError(f"invalid partial replay at {index}")
    if cursor != len(events):
        raise ValueError("orphan invalid events")
    return {"verified": True, "run_status": "invalid_run", "promoted": False}

def verify(output=None, *, config=CONFIG, verifier_runner: Callable | None = None, _test_only=False):
    if not _test_only and verifier_runner is not None:
        raise ValueError("production verify does not accept verifier_runner")
    out = _resolve_output(config, output, _test_only)
    plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text())
    _validate_plan(config, plan, plan_path=plan_path)
    if verifier_runner is None and _test_only:
        raise ValueError("test-only verify requires explicit verifier_runner")
    if {x.name for x in out.iterdir()} == {"pre_run_plan.json"}:
        return {"verified": True, "plan_only": True, "run_status": "planned", "promoted": False}
    if verifier_runner is None:
        if is_r3(config):
            verifier_runner = production_runner_r3
        elif is_r2(config):
            verifier_runner = production_runner_r2
        elif is_r1b(config):
            verifier_runner = production_runner_r1b
        else:
            verifier_runner = production_runner
    manifest = json.loads((out / "formal_run_manifest.json").read_text())
    if manifest.get("run_status") == "invalid_run":
        return _verify_invalid(config, out, plan, verifier_runner)
    if {x.name for x in out.iterdir()} != set(ARTIFACTS):
        raise ValueError("artifact set")
    report = json.loads((out / "formal_qualification_report.json").read_text())
    rows = _rows(out / "formal_frame_outcomes.csv")
    events = [json.loads(line) for line in (out / "formal_transcript.jsonl").read_bytes().splitlines()]
    if set(manifest) != {"run_id", "run_status", "outcome_count", "artifacts"} \
            or set(report) != {"run_id", "run_status", "promoted", "per_stratum_verified_success",
                               "formal_run_manifest_sha256"}:
        raise ValueError("normal package schema")
    if manifest.get("run_id") != config.run_id or report.get("run_id") != config.run_id \
            or manifest.get("run_status") != "development_completed" \
            or report.get("run_status") != "development_completed" \
            or report.get("promoted") is not False \
            or manifest.get("artifacts") != _artifact_hashes(out) \
            or report.get("formal_run_manifest_sha256") != _sha((out / "formal_run_manifest.json").read_bytes()):
        raise ValueError("artifact DAG")
    for path, payload in (("formal_frame_outcomes.csv", rows), ("formal_transcript.jsonl", events),
                          ("formal_policy_manifest.json", json.loads((out / "formal_policy_manifest.json").read_text())),
                          ("formal_candidate_manifest.json", json.loads((out / "formal_candidate_manifest.json").read_text()))):
        if path.endswith(".csv"):
            _reject_diagnostics(payload)
        elif path.endswith(".jsonl"):
            for line in payload:
                _reject_diagnostics(line)
        else:
            _reject_diagnostics(payload)
    if json.loads((out / "formal_codebook_manifest.json").read_text()) != codebook(config)[0] \
            or json.loads((out / "formal_candidate_manifest.json").read_text()) != _candidate_doc(config) \
            or json.loads((out / "formal_policy_manifest.json").read_text()) != _policy_doc(config):
        raise ValueError("candidate/codebook/policy replay")
    expected = _expected_frames(config, plan)
    if len(rows) != len(expected) or manifest.get("outcome_count") != len(rows):
        raise ValueError("row count")
    cursor = 0; _, mats = codebook(config)
    for index, (actual, (frame, seed)) in enumerate(zip(rows, expected)):
        replay, events_row, _, _ = _frame_result(config, frame, verifier_runner, codebook(config)[0], mats, seed)
        count = int(actual.get("transcript_event_count", 0)); piece = events[cursor:cursor + count]; cursor += count
        if not _same(replay, actual) or piece != events_row:
            raise ValueError(f"semantic replay at {index}")
    if cursor != len(events):
        raise ValueError("orphan transcript events")
    if report.get("per_stratum_verified_success") != _report_doc(config, out, "development_completed", rows)["per_stratum_verified_success"]:
        raise ValueError("per-stratum counts replay")
    return {"verified": True, "run_status": "development_completed", "promoted": False}


# ---------------------------------------------------------------- controller gate bridge

def verified_report_payload(config, out, *, replay_report_sha256, strict_replay_verified=True):
    """Build the frozen controller-gate payload of an immutable package.

    Reads only the immutable package artifacts (frames CSV + run manifest) and
    computes the per-stratum gate inputs the controller re-evaluates: frame
    counts, verified successes, forbidden failures, disclosure excluding the
    tag, and the median per-frame runtime.
    """
    rows = _rows(out / "formal_frame_outcomes.csv")
    per = {}
    for p in config.ps:
        stratum = [r for r in rows if abs(float(r["stratum_p"]) - p) < 1e-9]
        check_count_value = int(stratum[0]["check_count"]) if stratum else check_count(p, config)
        # R3 disclosure: every layer syndrome counts at 5 bits per GF(32)
        # check (the row carries the total check count m0 + m1); R1A/R1B/R2
        # disclose 10 bits per GF(1024) check.
        disclosure = 5 * check_count_value if is_r3(config) else 10 * check_count_value
        per[f"{p:.2f}"] = {
            "frames": len(stratum),
            "verified_success": sum(r["status"] == "verified_success" for r in stratum),
            "forbidden_failures": sum(r["status"] in _FORBIDDEN_STATUSES for r in stratum),
            "key_dependent_bits_excluding_tag": disclosure,
            "symbols_per_frame": config.n,
        }
    runtimes = sorted(float(r["runtime_s"]) for r in rows) if rows else [0.0]
    median = runtimes[len(runtimes) // 2]
    return {"stage": "canary" if config.development_frames == 4 else "development",
            "per_stratum": per,
            "strict_replay_verified": bool(strict_replay_verified),
            "median_runtime_seconds": median,
            "replay_report_sha256": replay_report_sha256,
            "run_manifest_sha256": _sha((out / "formal_run_manifest.json").read_bytes())}
