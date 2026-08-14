"""CLI for the V14 q=1024 efficiency gate
(``formal-nonbinary-ldpc-v14-efficiency-gate``, additive layer).

AUTHORIZATION BOUNDARY: ``model`` and ``gate`` run the frozen QSC / structured
scientific computations and produce change-evidence; they REFUSE to run
without the explicit ``--authorized --production`` flags (main-thread
authorization).  ``replay`` byte-compares an evidence dir against a sibling
replay dir and also requires ``--authorized --production``.  ``self-check``
performs no scientific work.  All evidence writing is additive: writing an
already-existing evidence file is a hard stop (fail closed).  The real channel
conductor loads V13 characterization frames via
``nonbinary_v14_channel.load_production_frames`` (execute-only, lazy).

Actions:
  model    build and write the frozen structured channel model
           (``v14_structured_channel_model.json``); refuses to overwrite.
  gate     run Stage 0 (QSC mechanism regression), Stage 1 (folded small-q
           structured validation) and Stage 2 (12 q=1024 structured DE points)
           and write the gate evidence set.  The structured channel model is
           part of the same evidence set: it is read as input (never written)
           and the gate fails closed per file for its own outputs
           (execute-once).
  replay   byte-compare the evidence dir against a sibling replay dir and
           write ``v14_replay_evidence.json``.
  self-check   structural import check (no scientific run).

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_v14_gate --self-check
  python -m comparison_bench.src.comparison_bench.cli.run_v14_gate model \\
      --authorized --production
  python -m comparison_bench.src.comparison_bench.cli.run_v14_gate gate \\
      --authorized --production
  python -m comparison_bench.src.comparison_bench.cli.run_v14_gate replay \\
      --authorized --production --replay-root DIR
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from ..formal_ir import nonbinary_v14_channel as channel
from ..formal_ir import nonbinary_v14_mcde as mcde
from ..formal_ir.nonbinary_v9_common import V9_RSS_CAP_BYTES

#: Change evidence dir (design section 4): the frozen single-run evidence root.
EVIDENCE_DIR = os.path.join(
    "openspec", "changes", "formal-nonbinary-ldpc-v14-efficiency-gate", "evidence")

#: Evidence filenames (frozen, design section 4).
CHANNEL_MODEL_FILE = "v14_structured_channel_model.json"
STAGE0_FILE = "v14_stage0_q4_qsc_regression.json"
STAGE1_FILE = "v14_stage1_structured_smallq.json"
STAGE2_FILE = "v14_stage2_q1024_threshold.json"
GATE_DECISION_FILE = "v14_gate_decision.json"
GATE_MANIFEST_FILE = "v14_gate_manifest.json"
REPLAY_EVIDENCE_FILE = "v14_replay_evidence.json"

#: Stage-1 folded small-q structured DE settings (design section 3).
STAGE1_Q_BITS = (2, 3, 4)      # folded q = 4 / 8 / 16
STAGE1_N_SAMPLES = 2000
STAGE1_MAX_ITER = 50
STAGE1_PROFILE = 3
STAGE1_M = 16
STAGE1_SEED = 2026090203

#: Stage-2 per-point seed root (deterministic, disjoint prefix 202609).
STAGE2_SEED_START = 2026090210

#: Gate's own output files (design section 4).  The channel model is part of
#: the SAME evidence set and is read (never written) by the gate; these files
#: are the gate's own writes, enforced execute-once per file.
GATE_OUTPUT_FILES = (
    STAGE0_FILE,
    STAGE1_FILE,
    STAGE2_FILE,
    GATE_DECISION_FILE,
    GATE_MANIFEST_FILE,
    REPLAY_EVIDENCE_FILE,
)


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _write_evidence(path: str, payload: dict) -> str:
    """Additive evidence writer: refuses to overwrite an existing file."""
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"evidence file already exists (fail closed): {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return str(target)


def _load_and_verify_model(path: str) -> dict:
    """Read and verify the pre-existing channel model from the evidence dir
    (design section 4).  The channel model is part of the SAME evidence set and
    is READ as a gate input, never written by the gate.  Missing or invalid ->
    hard error (fail closed)."""
    target = Path(path)
    if not target.is_file():
        raise FileExistsError(f"fresh additive evidence root required: "
                              f"channel model missing (expected: {target})")
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surface any parse failure
        raise ValueError(f"invalid channel model JSON {target}: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != channel.CHANNEL_MODEL_SCHEMA:
        raise ValueError(f"channel model schema mismatch (expected "
                         f"{channel.CHANNEL_MODEL_SCHEMA}): {target}")
    w = doc.get("w")
    if not isinstance(w, list) or len(w) != channel.Q:
        raise ValueError(f"channel model w must have length {channel.Q}: {target}")
    w_arr = np.asarray(w, dtype=np.float64)
    if not np.all(np.isfinite(w_arr)) or np.any(w_arr < 0.0):
        raise ValueError(f"channel model w must be finite and non-negative: {target}")
    if not math.isclose(float(w_arr.sum()), 1.0, abs_tol=1e-6):
        raise ValueError(f"channel model w must sum to ~1 "
                         f"(got {float(w_arr.sum())}): {target}")
    return doc


def _git_commit() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_repo_root(),
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return None
    return None


def _watcher():
    """Start a process-tree RSS watcher if available (returns None on any
    non-Windows / import failure so the CLI degrades gracefully)."""
    try:
        from ..formal_ir.nonbinary_v9_common import ProcessTreeRSSWatcher as W
        w = W(interval=2.0, cap_bytes=V9_RSS_CAP_BYTES)
        w.start()
        return w
    except Exception:
        return None


def _fake_frames(frames: int = 8, *, seed: int = 2026090202,
                 corr: float = 0.6, q: int = 1024) -> list[dict]:
    """Synthetic fake characterization frames (test lane only): each bob XORs
    a low-weight difference onto the alice frame with probability ``corr``, and
    an independent random symbol otherwise, so the empirical difference
    distribution is a structured (non-QSC) prior."""
    rng = np.random.default_rng(seed)
    frames_out: list[dict] = []
    for f in range(int(frames)):
        alice = rng.integers(0, q, size=256)
        bob = rng.integers(0, q, size=256)
        structured = rng.random(256) < corr
        diffs = rng.integers(0, 32, size=256) * structured
        bob = np.where(structured, alice ^ diffs, bob)
        frames_out.append({"frame_id": f, "stratum": "d1024_bw200",
                           "role": "characterization", "alice": alice, "bob": bob})
    return frames_out


def _build_channel_model(*, production_authorized: bool, _test_only: bool,
                         frames_override: list | None = None) -> tuple[dict, list]:
    """Build the frozen channel model doc plus the loaded frames.  Test lane
    uses synthetic frames; production loads V13 characterization frames
    (lazy, execute-only)."""
    if _test_only:
        frames = frames_override if frames_override is not None else _fake_frames()
    else:
        if not production_authorized:
            raise ValueError("channel model build requires production_authorized")
        frames = channel.load_production_frames(production_authorized=True)
    w_emp = channel.build_diff_distribution(frames, q=channel.Q)
    w_smooth = channel.smooth(w_emp, q=channel.Q)
    doc = channel.build_channel_model_doc(w_smooth, frames_used=len(frames))
    return doc, frames


def _struct_rho(rate: float, lam: dict) -> dict:
    """rho_edge map from the harmonic-exact concentrated distribution, keeping
    only positive weights (a degenerate single check degree collapses to a
    single entry)."""
    conc = mcde.concentrated_check_distribution(rate, lam)
    return {int(k): float(v) for k, v in
            ((conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"]))
            if float(v) > 0.0}


def _profile_lambda(profile_id: int) -> dict:
    for profile in mcde.PROFILES:
        if int(profile["id"]) == int(profile_id):
            return dict(profile["lambda"])
    raise ValueError(f"unknown profile id {profile_id}")


def _run_stage0() -> dict:
    lam = mcde.STAGE0_LAMBDA_DEGREES
    rho = _struct_rho(mcde.STAGE0_RATE, lam)
    sweep = mcde.threshold_binary_search(
        mcde.STAGE0_Q, mcde.STAGE0_RATE, lam, rho,
        n_samples=mcde.STAGE0_N_SAMPLES, max_iter=mcde.STAGE0_MAX_ITER,
        seed=mcde.STAGE0_SEED, p_lo=mcde.STAGE0_P_LO, p_hi=mcde.STAGE0_P_HI,
        grid_step=mcde.STAGE0_GRID_STEP)
    return mcde.build_stage0_doc(run=sweep)


def _run_stage1(w_smooth: np.ndarray, model_doc: dict) -> dict:
    """Folded small-q structured validation: one structured DE per folded
    cardinality (q=4/8/16) on profile 3 at a single rate (m=16)."""
    lam = _profile_lambda(STAGE1_PROFILE)
    rate = 1.0 - STAGE1_M / float(mcde.N_BLOCKS)
    rho = _struct_rho(rate, lam)
    small_q_runs: list[dict] = []
    for mb in STAGE1_Q_BITS:
        q_small = 1 << int(mb)
        w_small = channel.fold(w_smooth, int(mb))
        run = mcde.run_mcde(q_small, lam, rho, channel_mode=mcde.STRUCTURED,
                            w=w_small, n_samples=STAGE1_N_SAMPLES,
                            max_iter=STAGE1_MAX_ITER, seed=STAGE1_SEED)
        small_q_runs.append({"m_bits": int(mb), "q": q_small,
                             "converged": bool(run["converged"]),
                             "iterations": int(run["iterations"]),
                             "final_entropy": run["final_entropy"]})
    structured_run = {
        "channel_mode": mcde.STRUCTURED,
        "converged": bool(small_q_runs) and all(r["converged"] for r in small_q_runs),
        "iterations": small_q_runs[-1]["iterations"] if small_q_runs else 0,
        "final_entropy": small_q_runs[-1]["final_entropy"] if small_q_runs else None,
    }
    return mcde.build_stage1_doc(channel_doc=model_doc,
                                 m_bits=tuple(int(m) for m in STAGE1_Q_BITS),
                                 structured_smallq_run=structured_run)


def _run_stage2(w_smooth: np.ndarray, entropy_bits_w: float) -> tuple[dict, list]:
    """Stage 2: 12 frozen point evaluations (3 profiles x 4 m) on the q=1024
    structured channel.  Returns ``(stage2_doc, points)``."""
    w = np.asarray(w_smooth, dtype=np.float64)
    points: list[dict] = []
    for profile in mcde.PROFILES:
        pid = int(profile["id"])
        lam = dict(profile["lambda"])
        for m in mcde.MS:
            m = int(m)
            rate = 1.0 - m / float(mcde.N_BLOCKS)
            rho = _struct_rho(rate, lam)
            f_achieved = mcde.stage2_f_achieved(m, entropy_bits_w)
            seed = STAGE2_SEED_START + pid * 100 + m
            run = mcde.run_mcde(1024, lam, rho, channel_mode=mcde.STRUCTURED,
                                w=w, n_samples=mcde.STAGE2_N_SAMPLES,
                                max_iter=mcde.STAGE2_MAX_ITER, seed=seed,
                                entropy_tol=mcde.STAGE2_ENTROPY_TOL,
                                streak=mcde.STAGE2_STREAK)
            points.append({
                "id": pid * 100 + m, "profile": pid, "m": m,
                "rate": rate, "lambda": lam, "rho": rho,
                "f_achieved": f_achieved,
                "converged": bool(run["converged"]),
                "iterations": int(run["iterations"]),
                "final_entropy": run["final_entropy"],
            })
    return mcde.build_stage2_doc(points=points, entropy_bits_w=entropy_bits_w), points


def run_gate(output_dir: str, *, production_authorized: bool,
             _test_only: bool = False, frames_override: list | None = None,
             command: str = "") -> dict:
    """Run the full V14 gate (Stage 0/1/2) and write the gate evidence set into
    ``output_dir`` (additive, fail closed per file).  The channel model is part
    of the same evidence set (design section 4): it is READ as input from a
    pre-existing ``v14_structured_channel_model.json`` and never written by the
    gate.  The gate fails closed if ANY of its own output files already exists
    (execute-once).  ``_test_only=True`` relaxes the production authorization;
    the DE kernels are invoked through :mod:`nonbinary_v14_mcde` so tests can
    inject fakes."""
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("V14 gate requires the explicit production authorization")
    if not out.is_dir():
        raise FileExistsError(f"fresh additive evidence root required "
                              f"(missing evidence dir: {out})")
    # Read + verify the pre-existing structured channel model (same evidence set).
    model_doc = _load_and_verify_model(os.path.join(str(out), CHANNEL_MODEL_FILE))
    # Fail closed per file for the gate's own outputs (execute-once discipline).
    for name in GATE_OUTPUT_FILES:
        existing = out / name
        if existing.exists():
            raise FileExistsError(
                f"evidence file already exists (fail closed): {existing}")
    start = time.monotonic()
    watcher = _watcher()
    payload: dict = {}
    try:
        w_smooth = np.asarray(model_doc["w"], dtype=np.float64)
        entropy_bits_w = float(model_doc["entropy_bits"])

        stage0 = _run_stage0()
        payload["stage0_file"] = _write_evidence(
            os.path.join(str(out), STAGE0_FILE), stage0)

        stage1 = _run_stage1(w_smooth, model_doc)
        payload["stage1_file"] = _write_evidence(
            os.path.join(str(out), STAGE1_FILE), stage1)

        stage2, points = _run_stage2(w_smooth, entropy_bits_w)
        payload["stage2_file"] = _write_evidence(
            os.path.join(str(out), STAGE2_FILE), stage2)

        decision = mcde.build_gate_decision_doc(stage0=stage0, stage2=stage2, points=points)
        payload["gate_decision_file"] = _write_evidence(
            os.path.join(str(out), GATE_DECISION_FILE), decision)

        wall = time.monotonic() - start
        peak_rss = watcher.peak_rss_bytes if watcher is not None else None
        manifest = mcde.build_gate_manifest_doc(
            command=command, git_commit=_git_commit(), wall_seconds=wall,
            peak_rss_bytes=peak_rss, rss_cap_bytes=V9_RSS_CAP_BYTES)
        payload["gate_manifest_file"] = _write_evidence(
            os.path.join(str(out), GATE_MANIFEST_FILE), manifest)
        payload["gate_state"] = decision["gate_state"]
        payload["evidence_dir"] = str(out)
        payload["channel_model_file"] = os.path.join(str(out), CHANNEL_MODEL_FILE)
        return payload
    finally:
        if watcher is not None:
            watcher.stop()


def run_model(output_dir: str, *, production_authorized: bool,
              _test_only: bool = False, frames_override: list | None = None,
              command: str = "") -> dict:
    """Build and write the frozen structured channel model (additive, fail
    closed)."""
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("channel model build requires production_authorized")
    if out.exists():
        raise FileExistsError(f"fresh additive model root required (exists: {out})")
    out.mkdir(parents=True)
    start = time.monotonic()
    try:
        doc, frames = _build_channel_model(production_authorized=production_authorized,
                                           _test_only=_test_only,
                                           frames_override=frames_override)
        path = Path(_write_evidence(os.path.join(str(out), CHANNEL_MODEL_FILE), doc))
        wall = time.monotonic() - start
        return {"model_file": str(path.resolve()),
                "model_dir": str(out),
                "fit_frames": int(doc["fit_frames"]),
                "entropy_bits": float(doc["entropy_bits"]),
                "wall_seconds": float(wall)}
    finally:
        pass


# --------------------------------------------------------------------------- #
# byte-level replay (strict)
# --------------------------------------------------------------------------- #


def _read_bytes(path: Path) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def replay_evidence(evidence_root: str, replay_root: str) -> dict:
    """Strict byte comparison of ``replay_root`` against ``evidence_root``.
    Every evidence file must exist and be byte-identical in ``replay_root``;
    extra replay files are reported (not an error).  ``ok`` is true only when
    the evidence set is non-empty and every evidence file matches."""
    evidence = Path(evidence_root)
    replay = Path(replay_root)
    if not evidence.is_dir() or not replay.is_dir():
        raise ValueError("both evidence and replay roots must be directories")
    evidence_files = sorted(p for p in evidence.rglob("*") if p.is_file())
    if not evidence_files:
        raise ValueError("evidence root contains no files")
    matched = 0
    mismatches: list[dict] = []
    missing: list[str] = []
    for ef in evidence_files:
        rel = ef.relative_to(evidence)
        rf = replay / rel
        if not rf.is_file():
            missing.append(str(rel))
            continue
        eb = _read_bytes(ef)
        rb = _read_bytes(rf)
        if eb != rb:
            mismatches.append({"relative": str(rel),
                               "evidence_size": len(eb), "replay_size": len(rb)})
        else:
            matched += 1
    evidence_set = set(str(p.relative_to(evidence)) for p in evidence_files)
    replay_only = sorted(str(p.relative_to(replay)) for p in replay.rglob("*")
                         if p.is_file() and str(p.relative_to(replay)) not in evidence_set)
    ok = matched == len(evidence_files) == len(evidence_set) and not mismatches and not missing
    return {
        "schema": "nbldpc_v14_replay_evidence_v1",
        "ok": ok,
        "evidence_files": len(evidence_files),
        "matched": matched,
        "mismatches": mismatches,
        "missing_in_replay": missing,
        "replay_only": replay_only,
        "evidence_root": str(evidence),
        "replay_root": str(replay),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="self-check",
                        choices=["model", "gate", "replay", "self-check"],
                        help="action to run")
    parser.add_argument("--authorized", action="store_true",
                        help="explicit main-thread authorization")
    parser.add_argument("--production", action="store_true",
                        help="run the production lane (real channel model)")
    parser.add_argument("--out", default=None,
                        help="output dir (default: change evidence dir)")
    parser.add_argument("--test-only", dest="test_only", action="store_true",
                        help="test lane: synthetic frames, writable root")
    parser.add_argument("--replay-root", default=None,
                        help="replay root to byte-compare against the evidence "
                             "root (replay action)")
    args = parser.parse_args(argv)

    if args.action == "self-check":
        print(f"V14 gate self-check: imports ok; "
              f"profiles={len(mcde.PROFILES)} ms={list(mcde.MS)} "
              f"channel_schema={channel.CHANNEL_MODEL_SCHEMA} "
              f"gate_schema={mcde.V14_GATE_DECISION_SCHEMA}")
        return 0

    if args.action == "replay":
        if not args.authorized or not args.production:
            print("replay requires --authorized --production", file=sys.stderr)
            return 2
        if args.replay_root is None:
            print("--replay-root is required for replay", file=sys.stderr)
            return 2
        evidence_root = args.out or EVIDENCE_DIR
        report = replay_evidence(evidence_root, args.replay_root)
        try:
            _write_evidence(os.path.join(evidence_root, REPLAY_EVIDENCE_FILE), report)
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(report, sort_keys=True))
        return 0 if report["ok"] else 1

    if args.action == "model":
        if not args.test_only and not (args.authorized and args.production):
            print("model requires --authorized --production (or --test-only)",
                  file=sys.stderr)
            return 2
        out = args.out or EVIDENCE_DIR
        try:
            result = run_model(out, production_authorized=args.production,
                               _test_only=args.test_only,
                               command=" ".join(sys.argv))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0

    # gate
    if not args.test_only and not (args.authorized and args.production):
        print("gate requires --authorized --production (or --test-only)",
              file=sys.stderr)
        return 2
    out = args.out or EVIDENCE_DIR
    try:
        result = run_gate(out, production_authorized=args.production,
                          _test_only=args.test_only, command=" ".join(sys.argv))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
