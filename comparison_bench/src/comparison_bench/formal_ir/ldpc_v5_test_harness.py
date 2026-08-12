"""Phase-1-only, in-memory v5 development state-machine harness.

This module deliberately has no path arguments or filesystem imports.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .ldpc_v5 import (OUTCOME_FIELDS, run_ldpc_formal_v5, validate_outcome_v5,
                      verify_public_payload_v5, encode_outcome_csv_v5,
                      decode_outcome_csv_v5, canonical_event_v5)

_CANDIDATES = ("V5-C0", "V5-C1", "V5-C2")
_STRATA = ("bw120", "bw180", "bw200")
_PREFIX = ("role", "stratum", "role_rank", "plan_frame_id", "alice_sha256", "bob_sha256")


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canon(value)).hexdigest()


def _array_hash(value: Any) -> str:
    data = np.asarray(value)
    if data.shape != (256,) or not np.issubdtype(data.dtype, np.integer):
        raise ValueError("test frame array")
    return hashlib.sha256(np.asarray(data, dtype="<u2").tobytes()).hexdigest()


def _frame_rows(frame_records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if not isinstance(frame_records, Sequence) or len(frame_records) != 1536:
        raise ValueError("test frame count")
    rows = list(frame_records)
    expected = [(s, rank) for s in _STRATA for rank in range(512)]
    got = [(r.get("stratum"), r.get("role_rank")) for r in rows]
    if got != expected:
        raise ValueError("test frame order")
    required = {"role", "stratum", "role_rank", "plan_frame_id", "dataset_id", "frame_id", "alice", "bob", "pair_idx_sequence", "alice_sha256", "bob_sha256"}
    for row in rows:
        if set(row) != required or row["role"] != "development" or row["stratum"] not in _STRATA:
            raise ValueError("test frame schema")
        a, b = np.asarray(row["alice"]), np.asarray(row["bob"])
        indices = np.asarray(row["pair_idx_sequence"])
        if a.shape != (256,) or b.shape != (256,) or indices.shape != (256,) or not np.issubdtype(a.dtype, np.integer) or not np.issubdtype(b.dtype, np.integer) or not np.issubdtype(indices.dtype, np.integer) or np.any(a < 0) or np.any(a >= 1024) or np.any(b < 0) or np.any(b >= 1024):
            raise ValueError("test frame domain")
        if row["alice_sha256"] != _array_hash(a) or row["bob_sha256"] != _array_hash(b):
            raise ValueError("test frame hashes")
    return rows


def _source_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return _sha([{"stratum": r["stratum"], "role_rank": int(r["role_rank"]), "plan_frame_id": r["plan_frame_id"], "dataset_id": r["dataset_id"], "frame_id": r["frame_id"], "alice_sha256": r["alice_sha256"], "bob_sha256": r["bob_sha256"], "pair_idx_sequence_sha256": _sha([int(x) for x in np.asarray(r["pair_idx_sequence"], dtype=np.int64)])} for r in rows])


def _policy_rows(policies: Sequence[Mapping[str, Any]], policy_manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if not isinstance(policies, Sequence) or len(policies) != 3 or [p.get("candidate_id") for p in policies] != list(_CANDIDATES):
        raise ValueError("test policy order")
    if list(policy_manifest.get("candidates", [])) != list(policies):
        raise ValueError("test policy membership")
    return list(policies)


def _seeds(seed_records: Mapping[str, Any], candidate: str, stratum: str, rank: int) -> Any:
    key = f"{candidate}|{stratum}|{rank}"
    value = seed_records.get(key) if isinstance(seed_records, Mapping) else None
    if not isinstance(value, Sequence) or len(value) != 2 or value[0].get("seed_id") == value[1].get("seed_id"):
        raise ValueError("test locked seeds")
    return value


def _summaries(outcomes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result=[]
    for candidate in _CANDIDATES:
        for stratum in _STRATA:
            part=[row for row in outcomes if row["candidate_id"] == candidate and row["stratum"] == stratum]
            result.append({"candidate_id": candidate, "stratum": stratum, "denominator": sum(bool(r["denominator_included"]) for r in part), "verified_success": sum(r["status"] == "verified_success" for r in part), "forbidden_failure_count": sum(r["status"] in {"backend_unavailable", "aborted_resource_limit", "decoder_error", "syndrome_inconsistent"} for r in part), "key_dependent_disclosure_bits_total": sum(int(r["key_dependent_disclosure_bits_total"]) for r in part), "runtime_s_total": sum(float(r["runtime_s"]) for r in part)})
    return result


def _gate(summaries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible=[]
    for candidate in _CANDIDATES:
        rows=[r for r in summaries if r["candidate_id"] == candidate]
        if all(r["denominator"] == 512 and r["verified_success"] >= 510 and r["forbidden_failure_count"] == 0 for r in rows):
            eligible.append(candidate)
    def rank(candidate: str) -> tuple[Any, ...]:
        rows=[r for r in summaries if r["candidate_id"] == candidate]
        return (sum(r["key_dependent_disclosure_bits_total"] for r in rows) / 1536.0, -min(r["verified_success"] for r in rows), -sum(r["verified_success"] for r in rows), sum(r["runtime_s_total"] for r in rows), candidate)
    return {"test_only": True, "required_successes_per_stratum": 510, "required_denominator_per_stratum": 512, "eligible_candidates": eligible, "selected_candidate_id": min(eligible, key=rank) if eligible else None}


def run_test_development_batch(frame_records, *, policies, policy_manifest, selection_manifest, channel_model, h2_manifest, seed_records, decoder_factory, preflight_result, clock_factory) -> dict:
    rows=_frame_rows(frame_records); policy_rows=_policy_rows(policies, policy_manifest)
    outcomes=[]; transcripts=[]; csv_rows=[]
    for policy in policy_rows:
        candidate=policy["candidate_id"]
        for row in rows:
            begin=getattr(decoder_factory,"begin_attempt",None)
            if begin is not None: begin(candidate,row["stratum"],row["role_rank"])
            result=run_ldpc_formal_v5(row["alice"], row["bob"], pair_idx_sequence=row["pair_idx_sequence"], dataset_id=str(row["dataset_id"]), frame_id=str(row["frame_id"]), stratum=row["stratum"], candidate_policy=policy, policy_manifest=policy_manifest, selection_manifest=selection_manifest, channel_model=channel_model, h2_manifest=h2_manifest, locked_seeds=_seeds(seed_records, candidate, row["stratum"], row["role_rank"]), _decoder_factory=decoder_factory, _preflight_result=preflight_result, _clock=clock_factory(candidate,row["stratum"],row["role_rank"]))
            out={key: row[key] for key in _PREFIX}
            out.update(result["outcome"])
            verify_public_payload_v5(result["outcome"], result["events"], alice_symbols=row["alice"], pair_idx_sequence=row["pair_idx_sequence"], stratum=row["stratum"], candidate_policy=policy, policy_manifest=policy_manifest, selection_manifest=selection_manifest, channel_model=channel_model, h2_manifest=h2_manifest, locked_seeds=_seeds(seed_records, candidate, row["stratum"], row["role_rank"]))
            transcript=b"".join(canonical_event_v5(event) for event in result["events"])
            csv_row={"role":row["role"],"stratum":row["stratum"],"plan_frame_id":row["plan_frame_id"],"alice_sha256":row["alice_sha256"],"bob_sha256":row["bob_sha256"],"transcript_bytes_len":len(transcript),"transcript_bytes_sha256":hashlib.sha256(transcript).hexdigest()}
            csv_row.update(result["outcome"])
            csv_rows.append(csv_row)
            outcomes.append(out); transcripts.append(result["events"])
    if decode_outcome_csv_v5(encode_outcome_csv_v5(csv_rows)) != csv_rows:
        raise ValueError("test CSV roundtrip")
    summaries=_summaries(outcomes)
    base={"schema":"binary_ldpc_v5_phase1_test_batch_v1","test_only":True,"execution_order":"candidate_stratum_role_rank","source_digest":_source_digest(rows),"policy_manifest_sha256":policy_manifest.get("manifest_sha256"),"h2_manifest_sha256":h2_manifest.get("manifest_sha256"),"outcomes":outcomes,"transcripts":transcripts,"candidate_summaries":summaries,"test_gate":_gate(summaries)}
    return {**base,"batch_sha256":_sha(base)}


def verify_test_development_batch(batch, *, frame_records, policies, policy_manifest, selection_manifest, channel_model, h2_manifest, seed_records) -> dict:
    if not isinstance(batch, Mapping) or set(batch) != {"schema","test_only","execution_order","source_digest","policy_manifest_sha256","h2_manifest_sha256","outcomes","transcripts","candidate_summaries","test_gate","batch_sha256"}:
        raise ValueError("test batch schema")
    supplied=dict(batch); digest=supplied.pop("batch_sha256")
    if _sha(supplied) != digest or supplied["schema"] != "binary_ldpc_v5_phase1_test_batch_v1" or supplied["test_only"] is not True or supplied["execution_order"] != "candidate_stratum_role_rank":
        raise ValueError("test batch hash")
    rows=_frame_rows(frame_records); _policy_rows(policies, policy_manifest)
    if batch["source_digest"] != _source_digest(rows) or batch["policy_manifest_sha256"] != policy_manifest.get("manifest_sha256") or batch["h2_manifest_sha256"] != h2_manifest.get("manifest_sha256"):
        raise ValueError("test batch binding")
    if len(batch["outcomes"]) != 4608 or len(batch["transcripts"]) != 4608:
        raise ValueError("test batch cardinality")
    csv_rows=[]
    for index, (out, events) in enumerate(zip(batch["outcomes"], batch["transcripts"])):
        candidate=_CANDIDATES[index // 1536]; row=rows[index % 1536]
        if tuple(out) != _PREFIX + OUTCOME_FIELDS or any(out[k] != row[k] for k in _PREFIX) or out["candidate_id"] != candidate:
            raise ValueError("test batch outcome association")
        _seeds(seed_records, candidate, row["stratum"], row["role_rank"])
        validate_outcome_v5({k:out[k] for k in OUTCOME_FIELDS}, events)
        formal={k:out[k] for k in OUTCOME_FIELDS}
        verify_public_payload_v5(formal, events, alice_symbols=row["alice"], pair_idx_sequence=row["pair_idx_sequence"], stratum=row["stratum"], candidate_policy=policies[_CANDIDATES.index(candidate)], policy_manifest=policy_manifest, selection_manifest=selection_manifest, channel_model=channel_model, h2_manifest=h2_manifest, locked_seeds=_seeds(seed_records,candidate,row["stratum"],row["role_rank"]))
        transcript=b"".join(canonical_event_v5(event) for event in events)
        csv_row={"role":row["role"],"stratum":row["stratum"],"plan_frame_id":row["plan_frame_id"],"alice_sha256":row["alice_sha256"],"bob_sha256":row["bob_sha256"],"transcript_bytes_len":len(transcript),"transcript_bytes_sha256":hashlib.sha256(transcript).hexdigest()}
        csv_row.update(formal)
        csv_rows.append(csv_row)
    if decode_outcome_csv_v5(encode_outcome_csv_v5(csv_rows)) != csv_rows: raise ValueError("test CSV roundtrip")
    summaries=_summaries(batch["outcomes"])
    if batch["candidate_summaries"] != summaries or batch["test_gate"] != _gate(summaries):
        raise ValueError("test batch accounting")
    return {"status":"verified","test_only":True,"outcomes":4608,"decoder_reexecution":False}
