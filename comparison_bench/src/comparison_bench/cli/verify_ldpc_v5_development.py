"""Read-only verifier for the v1 binary LDPC v5 sacrificed-development package.

Strict: verifies the exact 12-artifact contract, canonical bytes, self-hashes,
DAG bindings, per-row public-payload reconstruction (no decoder execution),
selection reconstruction, and accounting. Never writes to the package.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from ..formal_ir import ldpc_v5_development as core
from ..formal_ir import ldpc_v4_10db_source as source
from ..formal_ir.codebook_v5_h2 import verify_h2_manifest
from ..formal_ir.ldpc_v5 import (decode_outcome_csv_v5, verify_v5_policy_manifest,
                                 _selected_candidates, verify_public_payload_v5,
                                 validate_outcome_v5)
from ..formal_ir.ldpc_v5_partition import validate_partition_lock
import numpy as np


def _json(p: Path) -> dict[str, Any]:
    raw = p.read_bytes()
    v = json.loads(raw)
    if not isinstance(v, dict) or core._compact(v) != raw:
        raise ValueError("noncanonical json")
    return v


def _hashed(doc: dict[str, Any], key: str) -> bool:
    base = dict(doc)
    got = base.pop(key, None)
    return isinstance(got, str) and got == core._sha(core._compact(base))


def _locked_alice(partition: dict[str, Any], row: dict[str, Any]) -> np.ndarray:
    """Rebuild exact Alice bits from the locked development row (contract §7.1).

    The partition lock is validated once by the caller; array loading reuses
    the frozen source adapter without re-validating the whole lock per row.
    """
    matches = [x for x in partition["role_rows"]
               if x["role"] == "development" and x["stratum"] == f"d1024_{row['stratum']}"
               and x["role_rank"] == int(row["frame_id"])]
    if len(matches) != 1:
        raise ValueError("locked development row")
    locked = matches[0]
    src = source.build_source_lock()
    a, _ = source.arrays_for_frame(src, {"stratum": locked["stratum"], "frame_id": locked["frame_id"]})
    return np.asarray(a)


def verify_output(output_dir: Path, *, _private_test_only: bool = False) -> dict[str, Any]:
    if not output_dir.is_dir() or {x.name for x in output_dir.iterdir()} != set(core.ARTIFACTS):
        raise ValueError("12 artifact contract")
    before = {name: core._sha((output_dir / name).read_bytes()) for name in core.ARTIFACTS}
    plan = _json(output_dir / core.ARTIFACTS[0])
    core._validate_plan(plan, test_only=_private_test_only, output_dir=output_dir)
    partition = _json(output_dir / core.ARTIFACTS[1])
    validate_partition_lock(partition)
    codebook = (output_dir / core.ARTIFACTS[2]).read_bytes()
    selection_bytes = (output_dir / core.ARTIFACTS[3]).read_bytes()
    channel = (output_dir / core.ARTIFACTS[4]).read_bytes()
    if core._sha(codebook) != plan["method_bindings"]["h1_codebook_manifest_sha256"] or \
       core._sha(selection_bytes) != plan["method_bindings"]["h1_selection_sha256"] or \
       core._sha(channel) != plan["method_bindings"]["channel_model_sha256"]:
        raise ValueError("method source DAG")
    selection = json.loads(selection_bytes.decode("ascii"))
    _selected_candidates(selection)
    selected = [x["candidate_id"] for x in selection["plane_selections"]]
    h2 = _json(output_dir / core.ARTIFACTS[5])
    verify_h2_manifest(h2, selected)
    if core._sha(core._compact(h2)) != plan["method_bindings"]["h2_manifest_sha256"]:
        raise ValueError("h2 DAG")
    policy = _json(output_dir / core.ARTIFACTS[6])
    verify_v5_policy_manifest(policy, selected_candidates=selected,
                              selection_sha256=selection["selection_sha256"],
                              codebook_manifest_sha256=selection["codebook_manifest_sha256"],
                              channel_model_sha256=selection["channel_model_sha256"], h2_manifest=h2)
    if core._sha(core._compact(policy)) != plan["method_bindings"]["policy_manifest_sha256"]:
        raise ValueError("policy DAG")
    method = core._method_objects()
    if (output_dir / core.ARTIFACTS[2]).read_bytes() != method["codebook_bytes"] or \
       (output_dir / core.ARTIFACTS[3]).read_bytes() != method["selection_bytes"] or \
       (output_dir / core.ARTIFACTS[4]).read_bytes() != method["channel_bytes"] or \
       _json(output_dir / core.ARTIFACTS[5]) != method["h2"] or \
       _json(output_dir / core.ARTIFACTS[6]) != method["policy"]:
        raise ValueError("method frozen equality")
    rows = decode_outcome_csv_v5((output_dir / core.ARTIFACTS[7]).read_bytes())
    if len(rows) > core._expected_outcomes(plan):
        raise ValueError("too many outcomes")
    transcript_bytes = (output_dir / core.ARTIFACTS[8]).read_bytes()
    if sum(int(r["transcript_bytes_len"]) for r in rows) != len(transcript_bytes):
        raise ValueError("transcript accounting")
    expected_ids = core._attempt_ids()
    if [f"{r['candidate_id']}|{r['stratum']}|{r['frame_id']}" for r in rows] != expected_ids[:len(rows)]:
        raise ValueError("execution order")
    policies = {c["candidate_id"]: c for c in method["policy"]["candidates"]}
    schedule = {(r["candidate_id"], r["stratum"], r["verification_round"]): r["root_hex"] for r in plan["seed_schedule"]["roots"]}
    offset = 0
    for row in rows:
        end = offset + int(row["transcript_bytes_len"])
        raw = transcript_bytes[offset:end]
        offset = end
        events = [json.loads(line) for line in raw.splitlines()] if raw else []
        candidate, stratum, rank = row["candidate_id"], row["stratum"], int(row["frame_id"])
        if row["role"] != "development" or row["plan_frame_id"] != f"{stratum}-{rank}":
            raise ValueError("row prefix")
        if core._sha(raw) != row["transcript_bytes_sha256"] or core._sha(raw) != row["transcript_sha256"]:
            raise ValueError("transcript slice hash")
        formal = {k: row[k] for k in core.OUTCOME_FIELDS}
        if not row["attempted"]:
            validate_outcome_v5(formal, events)
            continue
        seeds = [core.derive_seed(schedule[(candidate, stratum, 0)], candidate, stratum, 0, rank),
                 core.derive_seed(schedule[(candidate, stratum, 1)], candidate, stratum, 1, rank)]
        if _private_test_only:
            # Test packages detach synthetic arrays; public-payload
            # reconstruction is checked at execute time, the verifier
            # re-checks event accounting without Alice symbols.
            validate_outcome_v5(formal, events)
            continue
        alice = _locked_alice(partition, row)
        verify_public_payload_v5(formal, events, alice_symbols=alice,
                                 pair_idx_sequence=np.arange(core.N, dtype=np.int64), stratum=stratum,
                                 candidate_policy=policies[candidate], policy_manifest=method["policy"],
                                 selection_manifest=method["selection"], channel_model=method["channel"],
                                 h2_manifest=method["h2"], locked_seeds=seeds)
    selection_doc = _json(output_dir / core.ARTIFACTS[9])
    manifest = _json(output_dir / core.ARTIFACTS[10])
    report = _json(output_dir / core.ARTIFACTS[11])
    csv_sha = core._sha((output_dir / core.ARTIFACTS[7]).read_bytes())
    transcript_sha = core._sha(transcript_bytes)
    if manifest.get("run_status") == "invalid_execution":
        if selection_doc != core._invalid_selection(plan, rows):
            raise ValueError("partial selection")
    else:
        if selection_doc != core._selection(plan, rows, csv_sha, transcript_sha):
            raise ValueError("selection reconstruction")
    index = {n: {"sha256": core._sha((output_dir / n).read_bytes()), "bytes": (output_dir / n).stat().st_size} for n in core.ARTIFACTS[1:10]}
    if not _hashed(manifest, "run_manifest_sha256") or manifest.get("schema") != (core.TEST_RUN_MANIFEST_SCHEMA if _private_test_only else core.RUN_MANIFEST_SCHEMA) or manifest.get("run_id") != (core.TEST_RUN_ID if _private_test_only else core.RUN_ID) or manifest.get("artifact_file_sha256") != index or manifest.get("plan_sha256") != plan["plan_sha256"] or manifest.get("observed_outcomes") != len(rows) or manifest.get("expected_outcomes") != core._expected_outcomes(plan):
        raise ValueError("run manifest")
    if not _hashed(report, "report_sha256") or report.get("schema") != (core.TEST_REPORT_SCHEMA if _private_test_only else core.REPORT_SCHEMA) or report.get("run_id") != manifest.get("run_id") or report.get("run_status") != manifest.get("run_status") or report.get("plan_sha256") != plan["plan_sha256"] or report.get("run_manifest_sha256") != manifest.get("run_manifest_sha256") or report.get("run_manifest_file_sha256") != core._sha((output_dir / core.ARTIFACTS[10]).read_bytes()) or report.get("selection_sha256") != selection_doc.get("selection_sha256"):
        raise ValueError("report DAG")
    # contract §7 step 10: hashes files before and after; changes none
    after = {name: core._sha((output_dir / name).read_bytes()) for name in core.ARTIFACTS}
    if before != after:
        raise ValueError("artifact immutability")
    # contract §8: successful return contains exactly these six fields
    return {"status": "verified", "run_status": manifest["run_status"],
            "outcomes": len(rows),
            "selected_candidate_id": selection_doc.get("selected_candidate_id"),
            "ready_for_synthetic_prepare": selection_doc.get("ready_for_synthetic_prepare"),
            "decoder_reexecution": False}


def main() -> int:
    p = argparse.ArgumentParser(description="read-only verifier for the v1 binary LDPC v5 development package")
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    print(core._compact(verify_output(a.output_dir)).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
