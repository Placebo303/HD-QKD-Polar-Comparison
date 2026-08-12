import hashlib
import json

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.codebook_v4 import candidate_manifest
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4 import (
    decoder_policy, run_ldpc_formal_v4, validate_outcome_v4,
)
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _model():
    counts = {"zero_count": 12403, "plus_one_count": 3865, "minus_one_count": 116}; total = 16384
    plus, minus = counts["plus_one_count"] / total, counts["minus_one_count"] / total
    base = {"schema": "binary_ldpc_v4_adjacent_channel_v1", "role": "sacrificed_calibration_only", "dimension": 1024,
            "mapping": "gray_msb_first", "frame_len_symbols": 256, "calibration_frame_count": 64, "total_count": total, **counts,
            "sign_convention": "signed_modular_alice_minus_bob", "stress_scale": 1.25,
            "probabilities": {"adjacent_nominal": {"plus_one": plus, "minus_one": minus, "zero": counts["zero_count"] / total},
                              "adjacent_stress_125": {"plus_one": plus * 1.25, "minus_one": minus * 1.25, "zero": 1 - (plus + minus) * 1.25}},
            "source_lock_sha256": "a" * 64, "source_manifest_sha256": "b" * 64, "selected_frames_sha256": "c" * 64,
            "calibration_bytes_sha256": "d" * 64, "calibration_sha256": "e" * 64, "source_main_ttbin_sha256": "f" * 64,
            "source_chunk_ttbin_sha256": "0" * 64}
    return {**base, "model_sha256": hashlib.sha256(_compact(base)).hexdigest()}


def _binding(model):
    manifest = candidate_manifest(); records = {(x["plane_id"], x["candidate_id"]): x for x in manifest["candidates"]}
    planes = []
    for plane in range(10):
        candidate = next(c for c in range(4) if records[(plane, c)]["valid"])
        row = records[(plane, candidate)]
        nominal, stress = 512, 512
        planes.append({"plane_id": plane, "candidate_id": candidate, "canonical_bytes_sha256": row["canonical_bytes_sha256"], "nominal_successes": nominal, "stress_successes": stress, "selection_key": [-512, -1024, candidate]})
    base = {"schema": "binary_ldpc_v4_selection_v1", "method_id": "ldpc_formal_v4", "codebook_manifest_sha256": manifest["manifest_sha256"], "channel_model_sha256": model["model_sha256"], "plane_selections": planes}
    return {**base, "selection_sha256": hashlib.sha256(_compact(base)).hexdigest()}


class _Zero:
    calls = []
    def __init__(self, h, **kwargs):
        self.h = h; self.__class__.calls.append((h.copy(), kwargs))
    def decode(self, syndrome):
        return np.zeros(256, dtype=np.uint8)


def _run(a=None, b=None, **kwargs):
    model = _model(); return run_ldpc_formal_v4(np.zeros(256, dtype=np.int64) if a is None else a, np.zeros(256, dtype=np.int64) if b is None else b, channel_model=model, selection_binding=_binding(model), locked_seed=seed_record(np.arange(2623, dtype=np.uint8) % 2), _decoder_factory=_Zero, _preflight_result={"status": "ok", "dependency_version": "2.4.1", "backend_name": "test"}, **kwargs)


def test_success_order_policy_and_accounting():
    _Zero.calls = []; out = _run(); row = out["outcome"]
    assert row["status"] == "verified_success"
    assert (row["decoder_call_count"], row["ldpc_syndrome_bits"], row["key_dependent_disclosure_bits_total"], row["public_control_bits_total"]) == (10, 584, 648, 2623)
    assert [h.shape[0] for h, _ in _Zero.calls] == [16, 16, 16, 24, 24, 32, 48, 80, 136, 192]
    assert all(call[1]["bp_method"] == "product_sum" and len(call[1]["error_channel"]) == 256 and "tag" not in call[1] for call in _Zero.calls)
    assert [event["event_type"] for event in out["events"]] == ["SYNDROME"] * 10 + ["VERIFICATION_SEED", "VERIFICATION_TAG", "FRAME_TAG_CHECK"]
    assert decoder_policy()["policy_sha256"] == row["policy_sha256"]
    validate_outcome_v4(row, out["events"])


def test_tag_failure_and_selection_binding_tamper():
    def kernel(h):
        work = h.copy().astype(np.uint8); pivots = []; row = 0
        for col in range(256):
            found = next((r for r in range(row, work.shape[0]) if work[r, col]), None)
            if found is None: continue
            work[[row, found]] = work[[found, row]]
            for other in range(work.shape[0]):
                if other != row and work[other, col]: work[other] ^= work[row]
            pivots.append(col); row += 1
            if row == work.shape[0]: break
        free = next(col for col in range(256) if col not in pivots)
        out = np.zeros(256, dtype=np.uint8); out[free] = 1
        for r, col in reversed(list(enumerate(pivots))): out[col] = int(np.dot(work[r], out) % 2)
        return out
    class WrongConsistent:
        def __init__(self, h, **kwargs): self.h = h
        def decode(self, syndrome): return kernel(self.h) if self.h.shape[0] == 16 else np.zeros(256, dtype=np.uint8)
    model = _model()
    seed = seed_record(np.random.Generator(np.random.PCG64(123)).integers(0, 2, 2623, dtype=np.uint8))
    out = run_ldpc_formal_v4(np.zeros(256, dtype=np.int64), np.zeros(256, dtype=np.int64), channel_model=model, selection_binding=_binding(model), locked_seed=seed, _decoder_factory=WrongConsistent, _preflight_result={"status": "ok", "dependency_version": "2.4.1", "backend_name": "test"})
    assert out["outcome"]["status"] == "verify_failed"
    model = _model(); binding = _binding(model); binding["plane_selections"][0]["candidate_id"] = 3
    out = run_ldpc_formal_v4(np.zeros(256, dtype=np.int64), np.zeros(256, dtype=np.int64), channel_model=model, selection_binding=binding, locked_seed=seed_record(np.zeros(2623, dtype=np.uint8)), _preflight_result={"status": "ok", "dependency_version": "2.4.1"})
    assert out["outcome"]["status"] == "unsupported_domain"


def test_malformed_backend_resource_and_validator_tamper():
    class Bad:
        def __init__(self, h, **kwargs): pass
        def decode(self, syndrome): return np.zeros(255, dtype=np.uint8)
    model = _model(); binding = _binding(model); seed = seed_record(np.zeros(2623, dtype=np.uint8)); a = np.zeros(256, dtype=np.int64)
    malformed = run_ldpc_formal_v4(a, a, channel_model=model, selection_binding=binding, locked_seed=seed, _decoder_factory=Bad, _preflight_result={"status": "ok", "dependency_version": "2.4.1", "backend_name": "test"})
    assert malformed["outcome"]["status"] == "decoder_error"
    assert (malformed["outcome"]["verification_tag_bits"], malformed["outcome"]["verification_check_count"], malformed["outcome"]["public_control_bits_total"]) == (0, 0, 0)
    unavailable = run_ldpc_formal_v4(a, a, channel_model=model, selection_binding=binding, locked_seed=seed, _preflight_result={"status": "backend_unavailable"})
    assert unavailable["outcome"]["status"] == "backend_unavailable" and not unavailable["outcome"]["attempted"]
    limited = _run(_caps={"wall_s": 5, "decoder_calls": 0, "events": 32})
    assert limited["outcome"]["status"] == "aborted_resource_limit"
    ticks = iter((0.0, 0.0, 6.0, 6.0, 6.0))
    capped = _run(_clock=lambda: next(ticks))
    assert capped["outcome"]["status"] == "aborted_resource_limit"
    assert (capped["outcome"]["verification_tag_bits"], capped["outcome"]["verification_check_count"], capped["outcome"]["public_control_bits_total"]) == (0, 0, 0)
    changed = dict(_run()["outcome"]); changed["ldpc_syndrome_bits"] = 1
    try: validate_outcome_v4(changed)
    except ValueError: pass
    else: raise AssertionError("accepted tampered accounting")
