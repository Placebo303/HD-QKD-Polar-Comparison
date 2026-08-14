"""CLI for the V17 multibit structured feasibility gate
(``formal-nonbinary-ldpc-v17-multibit-structured-de-gate``, additive layer).

AUTHORIZATION BOUNDARY: the ``model`` / ``stage0`` / ``stage1`` / ``stage2`` /
``gate`` / ``replay`` actions perform the frozen scientific computations and
produce change-evidence; they REFUSE to run without the explicit
``--authorized --production`` flags (main-thread authorization), or the
``--test-only`` lane (writable root, synthetic inputs).  ``self-check`` performs
no scientific work.  All evidence writing is additive: writing an
already-existing evidence file is a hard stop (fail closed PER FILE, the V14
lesson — never fail closed on a whole evidence dir).

``gate`` runs Stage 0 -> Stage 1 -> Stage 2 sequentially (design section 2-4);
each stage writes only its own evidence file and the sequence stops at the first
hard error.  The channel model is part of the same evidence set and is read
(never written) by the gate.

Actions:
  model     build + write ``v17_multibit_channel_model.json`` (Stage 1).
  stage0    run the Stage 0 mechanism anchors + write ``v17_stage0.json``.
  stage1    run Stage 1 model build + write ``v17_multibit_channel_model.json``.
  stage2    run the Stage 2 candidate point evaluation + write ``v17_stage2.json``.
  gate      run Stage 0 -> Stage 1 -> Stage 2 + write the decision + manifest.
  replay    byte-compare an evidence dir against a sibling replay dir.
  self-check  structural import check (no scientific run).

Usage:
  python -m comparison_bench.src.comparison_bench.cli.run_v17_gate self-check
  python -m comparison_bench.src.comparison_bench.cli.run_v17_gate gate \
      --authorized --production --out DIR
  python -m comparison_bench.src.comparison_bench.cli.run_v17_gate model \
      --authorized --production --out DIR
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from ..formal_ir import nonbinary_v17_channel as channel
from ..formal_ir import nonbinary_v17_mcde as mcde
from ..formal_ir import nonbinary_v17_stage0 as stage0
from ..formal_ir.nonbinary_v9_common import V9_RSS_CAP_BYTES

#: Change evidence dir (design section 6): the frozen single-run evidence root.
EVIDENCE_DIR = os.path.join(
    "openspec", "changes", "formal-nonbinary-ldpc-v17-multibit-structured-de-gate",
    "evidence")

#: Evidence filenames (frozen, design section 6).
CHANNEL_MODEL_FILE = "v17_multibit_channel_model.json"
STAGE0_FILE = "v17_stage0.json"
STAGE2_FILE = "v17_stage2.json"
GATE_DECISION_FILE = "v17_gate_decision.json"
GATE_MANIFEST_FILE = "v17_gate_manifest.json"
REPLAY_EVIDENCE_FILE = "v17_replay_evidence.json"

#: The gate's own output files (Stage 0 / Stage 2 / decision / manifest).  The
#: channel model (Stage 1) is part of the same evidence set and is read as a
#: gate input when already present, but ``gate`` (re)builds it via Stage 1 and
#: writes it only if absent (execute-once per file).
GATE_OUTPUT_FILES = (
    STAGE0_FILE,
    STAGE2_FILE,
    GATE_DECISION_FILE,
    GATE_MANIFEST_FILE,
    REPLAY_EVIDENCE_FILE,
)

#: All scientific evidence files written by the production gate (Stage 1 model
#: included), for execute-once / replay accounting.
EVIDENCE_FILES = (
    CHANNEL_MODEL_FILE,
    STAGE0_FILE,
    STAGE2_FILE,
    GATE_DECISION_FILE,
    GATE_MANIFEST_FILE,
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
    """Start a process-tree RSS watcher if available (None on failure)."""
    try:
        from ..formal_ir.nonbinary_v9_common import ProcessTreeRSSWatcher as W
        w = W(interval=2.0, cap_bytes=V9_RSS_CAP_BYTES)
        w.start()
        return w
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# stage runners (production / test lanes)
# --------------------------------------------------------------------------- #

def _run_stage0(**anchor_kwargs) -> dict:
    return stage0.run_stage0(anchor_a_kwargs=anchor_kwargs.get("anchor_a_kwargs"),
                             anchor_b_kwargs=anchor_kwargs.get("anchor_b_kwargs"))


def _build_model(*, production_authorized: bool, _test_only: bool,
                 rates_override: list | None = None,
                 d01_root: str | None = None) -> dict:
    if _test_only:
        if rates_override is not None:
            rates = list(rates_override)
        else:
            rates = channel.synthetic_mismatch_rates()
        return channel.build_channel_model_doc(rates, run_id="v17_multibit_test",
                                               source_fields={"test_lane": True},
                                               frames_used=None, symbols_used=None)
    return channel.build_production_channel_model(
        production_authorized=production_authorized, d01_root=d01_root)


def _run_stage2(model_doc: dict, *, production_authorized: bool, _test_only: bool,
                n_samples: int | None = None, max_iter: int | None = None) -> dict:
    rates = list(model_doc["per_bit_plane_error_probability_msb_first"])
    n_s = int(n_samples) if n_samples is not None else mcde.STAGE2_N_SAMPLES
    m_i = int(max_iter) if max_iter is not None else mcde.STAGE2_MAX_ITER
    results = []
    for candidate in mcde.CANDIDATES:
        results.append(mcde.evaluate_candidate(candidate, rates,
                                               n_samples=n_s, max_iter=m_i))
    return mcde.build_stage2_doc(candidates=results, rates=rates,
                                 n_samples=n_s, max_iter=m_i)


def run_gate(output_dir: str, *, production_authorized: bool,
             _test_only: bool = False, rates_override: list | None = None,
             d01_root: str | None = None,
             n_samples: int | None = None, max_iter: int | None = None,
             command: str = "") -> dict:
    """Run the full V17 gate (Stage 0 -> Stage 1 -> Stage 2) and write the
    evidence set into ``output_dir`` (additive, fail closed per file).  The
    channel model may already exist (same evidence set) and is then read (never
    overwritten); otherwise Stage 1 writes it."""
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("V17 gate requires the explicit production authorization")
    if not out.is_dir():
        raise FileExistsError(f"fresh additive evidence root required "
                              f"(missing evidence dir: {out})")
    # Fail closed per file for the gate's own outputs (execute-once discipline).
    for name in GATE_OUTPUT_FILES:
        if (out / name).exists():
            raise FileExistsError(f"evidence file already exists (fail closed): {out / name}")
    start = time.monotonic()
    watcher = _watcher()
    payload: dict = {}
    try:
        # Stage 0
        stage0_doc = _run_stage0()
        payload["stage0_file"] = _write_evidence(
            os.path.join(str(out), STAGE0_FILE), stage0_doc)

        # Stage 1 (model; read if already present, else build + write)
        model_path = out / CHANNEL_MODEL_FILE
        if model_path.exists():
            model_doc = json.loads(model_path.read_text(encoding="utf-8"))
            payload["channel_model_file"] = str(model_path.resolve())
            payload["channel_model_reused"] = True
        else:
            model_doc = _build_model(production_authorized=production_authorized,
                                     _test_only=_test_only,
                                     rates_override=rates_override,
                                     d01_root=d01_root)
            payload["channel_model_file"] = _write_evidence(str(model_path), model_doc)
            payload["channel_model_reused"] = False

        # Stage 2
        stage2_doc = _run_stage2(model_doc, production_authorized=production_authorized,
                                 _test_only=_test_only, n_samples=n_samples,
                                 max_iter=max_iter)
        payload["stage2_file"] = _write_evidence(
            os.path.join(str(out), STAGE2_FILE), stage2_doc)

        decision = mcde.build_gate_decision_doc(stage0=stage0_doc, stage1=model_doc,
                                                stage2=stage2_doc)
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
        return payload
    finally:
        if watcher is not None:
            watcher.stop()


# --------------------------------------------------------------------------- #
# single-action helpers (model / stage0 / stage1 / stage2)
# --------------------------------------------------------------------------- #

def run_model(output_dir: str, *, production_authorized: bool,
              _test_only: bool = False, rates_override: list | None = None,
              d01_root: str | None = None, command: str = "") -> dict:
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("model build requires production_authorized")
    if not out.is_dir():
        out.mkdir(parents=True)
    start = time.monotonic()
    doc = _build_model(production_authorized=production_authorized,
                       _test_only=_test_only, rates_override=rates_override,
                       d01_root=d01_root)
    path = Path(_write_evidence(os.path.join(str(out), CHANNEL_MODEL_FILE), doc))
    wall = time.monotonic() - start
    return {"model_file": str(path.resolve()), "model_dir": str(out),
            "entropy_bits": float(doc["entropy_bits"]),
            "bit_planes": int(doc["bit_planes"]),
            "wall_seconds": float(wall)}


def run_stage0_action(output_dir: str, *, production_authorized: bool,
                      _test_only: bool = False, command: str = "") -> dict:
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("stage0 requires production_authorized")
    if not out.is_dir():
        out.mkdir(parents=True)
    doc = _run_stage0()
    path = Path(_write_evidence(os.path.join(str(out), STAGE0_FILE), doc))
    return {"stage0_file": str(path.resolve()), "gate_state": doc["gate_state"]}


def run_stage1_action(output_dir: str, *, production_authorized: bool,
                      _test_only: bool = False, rates_override: list | None = None,
                      d01_root: str | None = None, command: str = "") -> dict:
    return run_model(output_dir, production_authorized=production_authorized,
                     _test_only=_test_only, rates_override=rates_override,
                     d01_root=d01_root, command=command)


def run_stage2_action(output_dir: str, *, production_authorized: bool,
                      _test_only: bool = False, rates_override: list | None = None,
                      d01_root: str | None = None,
                      n_samples: int | None = None, max_iter: int | None = None,
                      command: str = "") -> dict:
    out = Path(output_dir).resolve()
    if not _test_only and not production_authorized:
        raise ValueError("stage2 requires production_authorized")
    if not out.is_dir():
        out.mkdir(parents=True)
    model_path = out / CHANNEL_MODEL_FILE
    if not model_path.exists():
        raise FileExistsError(f"stage2 requires a pre-existing channel model "
                              f"(missing: {model_path})")
    model_doc = json.loads(model_path.read_text(encoding="utf-8"))
    doc = _run_stage2(model_doc, production_authorized=production_authorized,
                      _test_only=_test_only, n_samples=n_samples, max_iter=max_iter)
    path = Path(_write_evidence(os.path.join(str(out), STAGE2_FILE), doc))
    return {"stage2_file": str(path.resolve()),
            "candidates": [c["candidate"] for c in doc["candidates"]]}


# --------------------------------------------------------------------------- #
# byte-level replay (strict)
# --------------------------------------------------------------------------- #

def _read_bytes(path: Path) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def replay_evidence(evidence_root: str, replay_root: str) -> dict:
    """Strict byte comparison of ``replay_root`` against ``evidence_root``."""
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
        if _read_bytes(ef) != _read_bytes(rf):
            mismatches.append({"relative": str(rel),
                               "evidence_size": len(_read_bytes(ef)),
                               "replay_size": len(_read_bytes(rf))})
        else:
            matched += 1
    evidence_set = set(str(p.relative_to(evidence)) for p in evidence_files)
    replay_only = sorted(str(p.relative_to(replay)) for p in replay.rglob("*")
                         if p.is_file() and str(p.relative_to(replay)) not in evidence_set)
    ok = matched == len(evidence_files) == len(evidence_set) and not mismatches and not missing
    return {
        "schema": "nbldpc_v17_replay_evidence_v1",
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
                        choices=["model", "stage0", "stage1", "stage2", "gate",
                                 "replay", "self-check"],
                        help="action to run")
    parser.add_argument("--authorized", action="store_true",
                        help="explicit main-thread authorization")
    parser.add_argument("--production", action="store_true",
                        help="run the production lane (real V13 D01 model)")
    parser.add_argument("--out", default=None,
                        help="output dir (default: change evidence dir)")
    parser.add_argument("--test-only", dest="test_only", action="store_true",
                        help="test lane: synthetic rates, writable root")
    parser.add_argument("--n_samples", type=int, default=None,
                        help="override Stage 2 n_samples (test lane)")
    parser.add_argument("--max_iter", type=int, default=None,
                        help="override Stage 2 max_iter (test lane)")
    parser.add_argument("--replay-root", default=None,
                        help="replay root to byte-compare against the evidence "
                             "root (replay action)")
    args = parser.parse_args(argv)

    if args.action == "self-check":
        print(f"V17 gate self-check: imports ok; "
              f"candidates={[c['id'] for c in mcde.CANDIDATES]} "
              f"ms={list(mcde.MS)} "
              f"channel_schema={channel.CHANNEL_MODEL_SCHEMA} "
              f"gate_schema=nbldpc_v17_gate_decision_v1")
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

    if not args.test_only and not (args.authorized and args.production):
        print(f"{args.action} requires --authorized --production (or --test-only)",
              file=sys.stderr)
        return 2
    out = args.out or EVIDENCE_DIR
    try:
        if args.action == "model":
            result = run_model(out, production_authorized=args.production,
                               _test_only=args.test_only,
                               command=" ".join(sys.argv))
        elif args.action == "stage0":
            result = run_stage0_action(out, production_authorized=args.production,
                                       _test_only=args.test_only,
                                       command=" ".join(sys.argv))
        elif args.action == "stage1":
            result = run_stage1_action(out, production_authorized=args.production,
                                       _test_only=args.test_only,
                                       command=" ".join(sys.argv))
        elif args.action == "stage2":
            result = run_stage2_action(out, production_authorized=args.production,
                                       _test_only=args.test_only,
                                       n_samples=args.n_samples,
                                       max_iter=args.max_iter,
                                       command=" ".join(sys.argv))
        else:  # gate
            result = run_gate(out, production_authorized=args.production,
                              _test_only=args.test_only,
                              n_samples=args.n_samples, max_iter=args.max_iter,
                              command=" ".join(sys.argv))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
