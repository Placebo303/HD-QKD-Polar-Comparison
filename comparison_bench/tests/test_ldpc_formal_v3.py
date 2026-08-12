import hashlib
import json

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.ldpc_v3 import (
    CANDIDATE_IDS, SELECTION_BINDING_SHA256, run_ldpc_formal_v3, validate_outcome_v3,
)
from comparison_bench.src.comparison_bench.formal_ir.codebook_long_v3 import generate_master
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


def _calibration():
    base = {"calibration_role": "sacrificed_tuning_only", "dimension": 1024, "mapping": "gray", "frame_len_symbols": 256, "source_sha256": "a" * 64,
            "planes": [{"plane_id": i, "errors": 1, "total_bits": 100, "p_hat": .01} for i in range(10)]}
    return {**base, "calibration_sha256": hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()}


class _Zero:
    calls = []
    def __init__(self, h, **kwargs): self.h = h; self.__class__.calls.append((h.shape, kwargs))
    def decode(self, delta): return np.zeros(256, dtype=np.uint8)


def _run(a, b, **kwargs):
    return run_ldpc_formal_v3(a, b, frozen_calibration=_calibration(), locked_seed=seed_record(np.arange(2623, dtype=np.uint8) % 2), _decoder_factory=_Zero, _preflight={"status": "ok", "dependency_version": "2.4.1", "backend_name": "test_injected"}, **kwargs)


def _symbols_with_plane_error(error):
    bits = np.zeros((256, 10), dtype=np.uint8); bits[:, 0] = error
    gray = (bits * (1 << np.arange(9, -1, -1))).sum(axis=1).astype(np.int64)
    natural = gray.copy(); shift = 1
    while shift < 10:
        natural ^= gray >> shift; shift += 1
    return natural


def _nullspace_error():
    h = generate_master(256, 0, CANDIDATE_IDS[0]); rhs = h[:, 224].copy(); work = h[:, :224].copy()
    # The selected full prefix is full row rank, so solve A*x = rhs over GF(2).
    for pivot in range(224):
        found = next(i for i in range(pivot, 224) if work[i, pivot])
        work[[pivot, found]] = work[[found, pivot]]; rhs[[pivot, found]] = rhs[[found, pivot]]
        for row in range(224):
            if row != pivot and work[row, pivot]: work[row] ^= work[pivot]; rhs[row] ^= rhs[pivot]
    out = np.zeros(256, dtype=np.uint8); out[224] = 1; out[:224] = rhs
    assert not np.any(h @ out % 2)
    return out


def test_clean_round_one_accounting_and_validator():
    _Zero.calls = []; out = _run(np.zeros(256, dtype=np.int64), np.zeros(256, dtype=np.int64))
    row = out["outcome"]
    assert row["status"] == "verified_success"
    assert (row["ldpc_syndrome_bits"], row["key_dependent_disclosure_bits_total"], row["public_control_bits_total"], row["global_rounds_attempted"], row["verification_check_count"]) == (1280, 1344, 2623, 1, 1)
    assert len(_Zero.calls) == 10 and row["candidate_ids"] == list(CANDIDATE_IDS)
    validate_outcome_v3(row, out["events"])


def test_invalid_and_preflight_are_non_attempted():
    a = np.zeros(256, dtype=np.int64)
    bad = _run(a[:-1], a)
    assert bad["outcome"]["status"] == "invalid_input" and not bad["events"]
    out = run_ldpc_formal_v3(a, a, frozen_calibration=_calibration(), locked_seed=seed_record(np.zeros(2623, dtype=np.uint8)), _preflight={"status": "bad"})
    assert out["outcome"]["status"] == "preflight_unavailable" and not out["events"]


def test_caps_and_decoder_inputs_contain_no_tag():
    a = np.zeros(256, dtype=np.int64)
    out = _run(a, a, _caps={"decoder_calls": 0})
    assert out["outcome"]["status"] == "aborted_resource_limit"
    _Zero.calls = []; _run(a, a)
    assert all("tag" not in kwargs and "match" not in kwargs for _, kwargs in _Zero.calls)


def test_later_round_and_full_nullspace_four_round_verify_failed():
    _Zero.calls = []; error = _nullspace_error(); a = np.zeros(256, dtype=np.int64); b = _symbols_with_plane_error(error)
    out = run_ldpc_formal_v3(a, b, frozen_calibration=_calibration(), locked_seed=seed_record(np.random.Generator(np.random.PCG64(123)).integers(0, 2, 2623, dtype=np.uint8)), _decoder_factory=_Zero, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})
    assert out["outcome"]["status"] == "verify_failed"
    assert (out["outcome"]["global_rounds_attempted"], out["outcome"]["verification_check_count"], out["outcome"]["ldpc_syndrome_bits"]) == (4, 4, 2240)
    assert out["outcome"]["epsilon_ec"] == 4 * 2.0 ** -64
    assert [e["key_dependent_bits"] for e in out["events"] if e["event_type"] == "SYNDROME"] == [128] * 10 + [32] * 10 + [32] * 10 + [32] * 10
    assert [shape for shape, _ in _Zero.calls] == [(128, 256)] * 10 + [(160, 256)] * 10 + [(192, 256)] * 10 + [(224, 256)] * 10


def test_continuation_without_truth_oracle():
    # This error has zero p050 syndrome but a nonzero p0625 syndrome.
    h = generate_master(256, 0, CANDIDATE_IDS[0]); e = np.zeros(256, dtype=np.uint8); e[128] = 1; e[:128] = h[:128, 128]
    class Later:
        def __init__(self, h, **kwargs): self.h = h
        def decode(self, delta): return e if self.h.shape[0] == 160 and np.any(delta) else np.zeros(256, dtype=np.uint8)
    a = np.zeros(256, dtype=np.int64); b = _symbols_with_plane_error(e)
    out = run_ldpc_formal_v3(a, b, frozen_calibration=_calibration(), locked_seed=seed_record(np.arange(2623, dtype=np.uint8) % 2), _decoder_factory=Later, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})
    assert out["outcome"]["status"] == "verified_success" and out["outcome"]["terminal_prefix_id"] == "p0625"


def test_failure_boundaries_and_validator_tamper(monkeypatch):
    a = np.zeros(256, dtype=np.int64); seed = seed_record(np.zeros(2623, dtype=np.uint8))
    bad_cal = _calibration(); bad_cal["calibration_sha256"] = "0" * 64
    assert run_ldpc_formal_v3(a, a, frozen_calibration=bad_cal, locked_seed=seed, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})["outcome"]["status"] == "unsupported_domain"
    assert _run(a, a, selection_binding_sha256="0" * 64)["outcome"]["status"] == "unsupported_domain"
    class Boom:
        def __init__(self, h, **kwargs): pass
        def decode(self, d): raise RuntimeError("x")
    assert run_ldpc_formal_v3(a, a, frozen_calibration=_calibration(), locked_seed=seed, _decoder_factory=Boom, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})["outcome"]["status"] == "decoder_error"
    class Wrong:
        def __init__(self, h, **kwargs): pass
        def decode(self, d): return np.zeros(255, dtype=np.uint8)
    assert run_ldpc_formal_v3(a, a, frozen_calibration=_calibration(), locked_seed=seed, _decoder_factory=Wrong, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})["outcome"]["status"] == "decoder_error"
    class Inconsistent:
        def __init__(self, h, **kwargs): pass
        def decode(self, d): return np.ones(256, dtype=np.uint8)
    assert run_ldpc_formal_v3(a, a, frozen_calibration=_calibration(), locked_seed=seed, _decoder_factory=Inconsistent, _preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test_injected"})["outcome"]["status"] == "syndrome_inconsistent"
    for caps in ({"wall_s": 0, "events": 100, "decoder_calls": 40}, {"wall_s": 10, "events": 2, "decoder_calls": 40}, {"wall_s": 10, "events": 100, "decoder_calls": 0}):
        assert _run(a, a, _caps=caps)["outcome"]["status"] == "aborted_resource_limit"
    ok = _run(a, a); bad = dict(ok["outcome"]); bad["pair_idx_sequence_sha256"] = "0" * 64
    try: validate_outcome_v3(bad, ok["events"])
    except ValueError: pass
    else: raise AssertionError("tampered outcome accepted")
    # Outcome-only validation still locks terminal, disclosure, and epsilon.
    for key, value in (("ldpc_syndrome_bits", 1600), ("epsilon_ec", True)):
        changed = dict(ok["outcome"]); changed[key] = value
        try: validate_outcome_v3(changed)
        except ValueError: pass
        else: raise AssertionError(f"outcome-only tamper {key} accepted")
    # Rehash cannot make a protocol-field mutation valid.
    for index, mutate in ((0, lambda e: e.update(direction="bob_local")), (1, lambda e: e["payload"].update(tag="A" * 16)), (2, lambda e: e.update(plane_id=1)), (12, lambda e: e["payload"].update(value="other"))):
        tampered = [dict(e, payload=dict(e["payload"])) for e in ok["events"]]; mutate(tampered[index])
        changed = dict(ok["outcome"]); changed.update(__import__("comparison_bench.src.comparison_bench.formal_ir.shared", fromlist=["transcript_summary"]).transcript_summary(tampered))
        try: validate_outcome_v3(changed, tampered)
        except ValueError: pass
        else: raise AssertionError("transcript tamper accepted")
    monkeypatch.setattr("comparison_bench.src.comparison_bench.formal_ir.ldpc_v3.canonical_matrix_bytes", lambda h: b"bad")
    assert _run(a, a)["outcome"]["status"] == "unsupported_domain"
