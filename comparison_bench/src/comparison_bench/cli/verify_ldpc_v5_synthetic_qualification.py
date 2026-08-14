"""Read-only verifier for the v1 binary LDPC v5 synthetic qualification package.

Strict: verifies the exact 10-artifact contract, canonical bytes, self-hashes,
DAG bindings, per-row public-payload reconstruction (no decoder execution),
generator reconstruction, 126/128 per-stratum gates, and accounting. Never
writes to the package.
"""
from __future__ import annotations
import argparse, json, logging
from pathlib import Path
from typing import Any
from ..formal_ir import ldpc_v5_synthetic_qualification as core
from ..formal_ir import ldpc_v5_development as dev
from ..formal_ir.ldpc_v5 import (decode_outcome_csv_v5, verify_public_payload_v5,
                                 validate_outcome_v5)
import numpy as np

logger = logging.getLogger("comparison_bench.verify_ldpc_v5_synthetic_qualification")


def verify_output(output_dir: Path, *, _private_test_only: bool = False) -> dict[str, Any]:
    if not output_dir.is_dir() or {x.name for x in output_dir.iterdir()} != set(core.ARTIFACTS):
        raise ValueError("10 artifact contract")
    before = {name: core._sha((output_dir / name).read_bytes()) for name in core.ARTIFACTS}
    plan = core._json_read(output_dir / core.ARTIFACTS[0])
    core._validate_plan(plan, test_only=_private_test_only, output_dir=output_dir)
    binding = plan["development_binding"]
    manifest_keys = {"formal_codebook_manifest.json": "codebook",
                     "formal_selection_manifest.json": "selection",
                     "formal_channel_model.json": "channel_model",
                     "v5_h2_manifest.json": "h2_manifest",
                     "v5_policy_manifest.json": "policy_manifest"}
    for name in core.ARTIFACTS[1:6]:
        if core._sha((output_dir / name).read_bytes()) != binding["artifact_hashes"][name]:
            raise ValueError("bound manifest DAG")
        if core._json_read(output_dir / name) != binding[manifest_keys[name]]:
            raise ValueError("bound manifest equality")
    frames = {s: core._generate(plan, s) for s in core.CHANNEL_STRATA}
    rows = decode_outcome_csv_v5((output_dir / core.ARTIFACTS[6]).read_bytes())
    if len(rows) > len(plan["execution"]["attempt_ids"]):
        raise ValueError("too many outcomes")
    transcript_bytes = (output_dir / core.ARTIFACTS[7]).read_bytes()
    if sum(int(r["transcript_bytes_len"]) for r in rows) != len(transcript_bytes):
        raise ValueError("transcript accounting")
    expected_ids = plan["execution"]["attempt_ids"]
    if [r["plan_frame_id"] for r in rows] != expected_ids[:len(rows)]:
        raise ValueError("execution order")
    if any(r["role"] != "confirmation" or r["stratum"] != core.DATA_STRATUM for r in rows):
        raise ValueError("row prefix")
    schedule = {(r["stratum"], r["verification_round"]): r["root_hex"]
                for r in plan["seed_schedule"]["roots"]}
    policy = binding["policy_manifest"]
    candidate_policy = next(c for c in policy["candidates"] if c["candidate_id"] == core.CANDIDATE)
    offset = 0
    total = len(rows)
    for row_idx, row in enumerate(rows):
        if row_idx and row_idx % 64 == 0:
            logger.info("verify progress: %d/%d rows (%.0f%%)", row_idx, total, 100.0 * row_idx / total)
        end = offset + int(row["transcript_bytes_len"])
        raw = transcript_bytes[offset:end]
        offset = end
        events = [json.loads(line) for line in raw.splitlines()] if raw else []
        stratum, frame = row["plan_frame_id"].split("|")
        i = int(frame[1:])
        alice, bob = frames[stratum]
        if core._sha(np.asarray(alice[i], dtype="<u2").tobytes()) != row["alice_sha256"] or \
           core._sha(np.asarray(bob[i], dtype="<u2").tobytes()) != row["bob_sha256"]:
            raise ValueError("row array hash")
        if core._sha(raw) != row["transcript_bytes_sha256"] or core._sha(raw) != row["transcript_sha256"]:
            raise ValueError("transcript slice hash")
        formal = {k: row[k] for k in core.OUTCOME_FIELDS}
        if not row["attempted"]:
            validate_outcome_v5(formal, events)
            continue
        seeds = [core.derive_seed(schedule[(stratum, r)], stratum, r, i) for r in (0, 1)]
        verify_public_payload_v5(formal, events, alice_symbols=alice[i],
                                 pair_idx_sequence=np.arange(core.N, dtype=np.int64),
                                 stratum=core.DATA_STRATUM, candidate_policy=candidate_policy,
                                 policy_manifest=policy, selection_manifest=binding["selection"],
                                 channel_model=binding["channel_model"], h2_manifest=binding["h2_manifest"],
                                 locked_seeds=seeds)
    manifest = core._json_read(output_dir / core.ARTIFACTS[8])
    report = core._json_read(output_dir / core.ARTIFACTS[9])
    csv_sha = core._sha((output_dir / core.ARTIFACTS[6]).read_bytes())
    transcript_sha = core._sha(transcript_bytes)
    index = {name: {"sha256": core._sha((output_dir / name).read_bytes()), "bytes": (output_dir / name).stat().st_size}
             for name in core.ARTIFACTS[1:8]}
    if not core._self({k: v for k, v in manifest.items() if k != "run_manifest_sha256"}, "run_manifest_sha256") == manifest or \
       manifest.get("schema") != (core.TEST_RUN_MANIFEST_SCHEMA if _private_test_only else core.RUN_MANIFEST_SCHEMA) or \
       manifest.get("run_id") != (core.TEST_RUN_ID if _private_test_only else core.RUN_ID) or \
       manifest.get("plan_sha256") != plan["plan_sha256"] or \
       manifest.get("outcome_count") != len(rows) or \
       manifest.get("artifact_file_sha256") != index:
        raise ValueError("run manifest")
    denominator = int(plan["gates"]["denominator_per_stratum"])
    floor = int(plan["gates"]["successes_per_stratum"])
    gates = {s: core._gate(rows, s, denominator, floor) for s in core.CHANNEL_STRATA}
    promoted = manifest.get("run_status") == "completed" and all(g["passed"] for g in gates.values())
    expected_report = core._self({"schema": core.TEST_REPORT_SCHEMA if _private_test_only else core.REPORT_SCHEMA,
                                  "run_id": manifest["run_id"], "run_status": manifest["run_status"],
                                  "stop_reason": manifest.get("stop_reason"), "plan_sha256": plan["plan_sha256"],
                                  "run_manifest_sha256": manifest["run_manifest_sha256"],
                                  "promotion_gates": gates, "promoted": promoted,
                                  "ready_for_real_qualification": promoted,
                                  "decoder_reexecution": False}, "report_sha256")
    if report != expected_report:
        raise ValueError("report reconstruction")
    after = {name: core._sha((output_dir / name).read_bytes()) for name in core.ARTIFACTS}
    if before != after:
        raise ValueError("artifact immutability")
    return {"status": "verified", "run_status": manifest["run_status"],
            "outcomes": len(rows), "selected_candidate_id": core.CANDIDATE,
            "ready_for_real_qualification": bool(promoted), "decoder_reexecution": False}


def main() -> int:
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="read-only verifier for the v1 binary LDPC v5 synthetic package")
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    print(core._compact(verify_output(a.output_dir)).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
