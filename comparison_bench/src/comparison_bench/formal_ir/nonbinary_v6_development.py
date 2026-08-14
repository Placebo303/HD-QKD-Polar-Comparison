"""Development-only harness for the NBLDPC v6 long-block engineering lane.

This module is a *development harness*, not a qualification runner.  It
follows the accepted v5 lifecycle patterns (canonical plan, PCG64 frame
generation, identity-freshness scan, locked Toeplitz seed records, canonical
transcript, eight-artifact package, strict read-only replay, invalid-run
retention) with three frozen v6 differences:

- one codebook per stratum (320 checks for p=.20, 480 for p=.30) instead of a
  multi-policy ladder: there is no policy selection and no extension stage;
- no confirmation material: plans contain only development frames, and a run
  never materializes confirmation seeds or rows (V6-30 scientific stop);
- no promotion concept: ``promoted`` is always ``False`` and the report labels
  the run ``development_completed`` / ``invalid_run`` / ``planned``.

Production execution is deliberately unreachable in this packet: ``run``
without an explicit fake runner raises (execution requires the V6-50
main-thread review), and the official output root is locked until that
review.  Tests always pass an explicit fake runner with ``_test_only=True``
under a fresh writable workspace UUID root and never enter an official output
root; the fake runner is the only decoder seam exercised during strict
read-only replay.

V6-51 adds one narrow exception: the module-level ``CANARY`` config (a
sacrificed 4+4-frame plan with fresh roots) may execute through ``run`` with
``production_authorized=True``, but only with an explicit non-official
workspace output and an explicit production runner.  ``CONFIG`` production
execution still raises, and the official root under
``comparison_bench/outputs_comparison/formal_ir_methods/`` remains locked for
both configs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import nonbinary_syndrome, symbols_to_msb_bits
from .shared import (canonical_event, locked_seed_bits, materialize_seed_record,
                     toeplitz_tag, transcript_summary)
from . import nonbinary_v6_codebook as v6_cb
from . import nonbinary_v6_long as v6_long

METHOD = "nbldpc_formal_v6_long"
_SCHEMA = "NBLDPC6DEV"
RUN_ID = "20260802_v1_nbldpc_v6_development"
Q, N = 1024, 1024
PS = (0.20, 0.30)
CHECK_COUNTS = {0.20: 320, 0.30: 480}
SEED_BITS = N * 10 + 63  # Toeplitz seed length for 10-bit MSB-first symbols.
CAPS = {"workers": 1, "q": 1024, "n": 1024, "max_iter": 50, "lambda": .75,
        "dense_bytes_max": 64 * 1024 * 1024, "development_frames": 64}
ROOTS = {("development", .20): 202608020000, ("development", .30): 202608020100}
_SRC = (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_long.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_development.py",
    "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v6_development.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py",
    "comparison_bench/src/comparison_bench/formal_ir/shared.py",
)
CONTRACT = "openspec/changes/formal-nonbinary-ldpc-v6-long-block/specs/spec.md"

ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl",
             "formal_run_manifest.json", "formal_codebook_manifest.json",
             "formal_candidate_manifest.json", "formal_policy_manifest.json",
             "formal_qualification_report.json")
_ALLOWED_STATUSES = {"syndrome_consistent", "decode_failed", "decoder_error",
                     "codebook_invalid", "invalid_input", "unsupported_domain",
                     "aborted_resource_limit"}
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


CONFIG = DevelopmentConfig(
    run_id=RUN_ID, canonical_schema=_SCHEMA, method=METHOD, q=Q, n=N, ps=PS,
    roots=ROOTS, caps=CAPS, seed_bits=SEED_BITS, development_frames=64,
    source_files=_SRC, contract=CONTRACT)

# V6-51 sacrificed canary: the only config that may execute, and only through
# an explicit production runner into an explicit non-official workspace output.
# Fresh roots are disjoint from CONFIG roots (202608020000/202608020100) and
# from every prior evidence root; 4+4 development frames, no confirmation.
CANARY = DevelopmentConfig(
    run_id="20260802_v1_nbldpc_v6_canary", canonical_schema=_SCHEMA, method=METHOD,
    q=Q, n=N, ps=PS,
    roots={("development", .20): 202608024000, ("development", .30): 202608024100},
    caps=CAPS, seed_bits=SEED_BITS, development_frames=4,
    source_files=_SRC, contract=CONTRACT)


def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return v6_cb.codebook()


def check_count(p: float) -> int:
    try:
        return CHECK_COUNTS[float(p)]
    except (KeyError, TypeError, ValueError):
        raise ValueError("invalid NBLDPC6 stratum")


def production_runner(bob_symbols, syndrome, manifest, matrices, *, check_count, p):
    return v6_long.production_runner(bob_symbols, syndrome, manifest, matrices,
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
        raise ValueError(f"official v6 development root is locked until V6-50 review: {official}")
    chosen = Path(output).resolve()
    if chosen == official:
        raise ValueError("official v6 development root is locked until V6-50 review")
    return chosen

def _frame(config, p, index):
    rng = np.random.Generator(np.random.PCG64(config.roots["development", p] + index))
    alice = rng.integers(0, config.q, config.n, dtype=np.int64)
    mask = rng.random(config.n) < p
    error = rng.integers(1, config.q, config.n, dtype=np.int64)
    bob = alice.copy(); bob[mask] ^= error[mask]
    return {"frame_id": f"{config.method}_q{config.q}_p{int(p * 100):02d}_development_{index:03d}",
            "p": p, "role": "development", "index": index,
            "seed": config.roots["development", p] + index,
            "alice": alice.tolist(), "bob": bob.tolist(),
            "array_sha256": _sha(alice.astype("<i8").tobytes() + bob.astype("<i8").tobytes()),
            "atomic_keys": [f"{config.method}|development|{p}|{index}|{j}" for j in range(config.n)]}

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
    root = _root(); cb, _ = codebook()
    candidate = {"method": config.method,
                 "strata": {f"{p:.2f}": check_count(p) for p in config.ps},
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
    return {"policy_id": "nbldpc_v6_long", "decoder": "layered_fft_qspa_n1024",
            "lambda": .75, "max_iter": 50,
            "strata": [{"p": p, "check_count": check_count(p)} for p in config.ps]}

def _candidate_doc(config, cb=None):
    cb = codebook()[0] if cb is None else cb
    return {"method": config.method,
            "strata": {f"{p:.2f}": check_count(p) for p in config.ps},
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

def create_plan(output=None, *, config=CONFIG, _test_only=False):
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
    p = float(frame["p"]); checks = check_count(p)
    syndrome = nonbinary_syndrome(mats[checks], frame["alice"], GF2mField.create(config.q))
    raw = runner(frame["bob"], syndrome, cb, mats, check_count=checks, p=p)
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
    if not 0 <= iterations <= 50:
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
           "array_sha256": frame["array_sha256"], "transcript_event_count": len(events), **summary}
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
        cb, _ = codebook()
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
    if not _test_only and not production_authorized:
        raise ValueError("development execution is not authorized before V6-50 main-thread review")
    if production_authorized:
        # V6-51: the sacrificed canary is the only config that may execute, and
        # only with an explicit non-official workspace output and an explicit
        # production runner.  CONFIG production execution still raises above.
        if config is not CANARY:
            raise ValueError("production execution is authorized only for the sacrificed CANARY config")
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
        cb, mats = codebook(); state["codebook"] = cb
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
    return {k: str(v) for k, v in expected.items()} == {k: str(v) for k, v in right.items()}

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
        if cb != codebook()[0] or candidate != _candidate_doc(config, cb) \
                or policy != _policy_doc(config) or events:
            raise ValueError("invalid empty sentinel")
        return {"verified": True, "run_status": "invalid_run", "promoted": False}
    if cb != codebook()[0] or candidate != _candidate_doc(config, cb) or policy != _policy_doc(config):
        raise ValueError("invalid partial provenance")
    expected = _expected_frames(config, plan)
    if len(rows) > len(expected):
        raise ValueError("invalid partial row count")
    if [row.get("frame_id") for row in rows] != [frame["frame_id"] for frame, _ in expected[:len(rows)]]:
        raise ValueError("invalid partial order")
    cursor = 0; _, mats = codebook()
    for index, (actual, (frame, seed)) in enumerate(zip(rows, expected)):
        replay, events_row, _, _ = _frame_result(config, frame, verifier_runner, codebook()[0], mats, seed)
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
    if json.loads((out / "formal_codebook_manifest.json").read_text()) != codebook()[0] \
            or json.loads((out / "formal_candidate_manifest.json").read_text()) != _candidate_doc(config) \
            or json.loads((out / "formal_policy_manifest.json").read_text()) != _policy_doc(config):
        raise ValueError("candidate/codebook/policy replay")
    expected = _expected_frames(config, plan)
    if len(rows) != len(expected) or manifest.get("outcome_count") != len(rows):
        raise ValueError("row count")
    cursor = 0; _, mats = codebook()
    for index, (actual, (frame, seed)) in enumerate(zip(rows, expected)):
        replay, events_row, _, _ = _frame_result(config, frame, verifier_runner, codebook()[0], mats, seed)
        count = int(actual.get("transcript_event_count", 0)); piece = events[cursor:cursor + count]; cursor += count
        if not _same(replay, actual) or piece != events_row:
            raise ValueError(f"semantic replay at {index}")
    if cursor != len(events):
        raise ValueError("orphan transcript events")
    if report.get("per_stratum_verified_success") != _report_doc(config, out, "development_completed", rows)["per_stratum_verified_success"]:
        raise ValueError("per-stratum counts replay")
    return {"verified": True, "run_status": "development_completed", "promoted": False}
