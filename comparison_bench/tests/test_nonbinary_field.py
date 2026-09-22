from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField, get_field_spec, preflight_nonbinary_field


@pytest.mark.parametrize("q", [2, 256, 1024])
def test_pinned_fields_preflight_and_complete_cycles(q: int):
    first, second = preflight_nonbinary_field(q), preflight_nonbinary_field(q)
    assert first["status"] == second["status"] == "ok"
    assert first["field"]["field_id"] == second["field"]["field_id"]
    field = GF2mField.create(q)
    assert len(field.nonzero_cycle) == q - 1 == len(set(field.nonzero_cycle))
    assert all(field.mul(value, field.inverse(value)) == 1 for value in range(1, q))


def test_full_supported_domain_has_unique_deterministic_field_ids():
    reports = [preflight_nonbinary_field(q) for q in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)]
    assert all(report["status"] == "ok" for report in reports)
    assert len({report["field"]["field_id"] for report in reports}) == len(reports)


def test_numpy_integer_q_is_normalized_for_json_safe_metadata():
    report = preflight_nonbinary_field(np.int64(8))
    assert report["status"] == "ok"
    assert report["requested_q"] == 8
    assert report["field"]["q"] == 8


def test_field_operations_accept_numpy_integer_symbols_and_normalize_results():
    field = GF2mField.create(8)
    assert field.add(np.int64(3), np.uint8(5)) == 6
    assert field.mul(np.int64(3), np.uint8(5)) == field.mul(3, 5)
    assert field.inverse(np.int32(3)) == field.inverse(3)


@pytest.mark.parametrize("value", [1.5, "1", True])
def test_field_operations_reject_non_integral_or_bool_symbols(value: object):
    field = GF2mField.create(8)
    for operation in (
        lambda: field.add(value, 1),
        lambda: field.mul(value, 1),
        lambda: field.inverse(value),
    ):
        with pytest.raises(ValueError, match="GF symbol outside pinned field domain"):
            operation()


def test_unsupported_and_expected_id_mismatch_fail_closed():
    assert preflight_nonbinary_field(3)["status"] == "unsupported_domain"
    assert preflight_nonbinary_field(1024, expected_field_id="0" * 64)["status"] == "backend_unavailable"
    assert preflight_nonbinary_field(1024, expected_field_id=get_field_spec(1024).field_id)["status"] == "ok"


@pytest.mark.parametrize("q", [8.5, "8", True])
def test_non_integer_q_requests_fail_closed_without_coercion(q: object):
    with pytest.raises(ValueError, match="unsupported GF\\(q\\) domain"):
        get_field_spec(q)  # type: ignore[arg-type]
    assert preflight_nonbinary_field(q) == {
        "status": "unsupported_domain",
        "method": "nbldpc_formal_v1",
        "requested_q": q,
        "backend": "internal_polynomial_basis_gf2m",
    }


def test_qldpc_reference_source_is_not_mutated():
    path = Path("comparison_bench/src/comparison_bench/methods/qldpc_reference.py")
    # Pin recomputed 2026-09-20 from the committed artifact (git blob c64518,
    # created in 71bda20d, working tree clean for this file): the prior pin
    # c40d690c... never matched any committed version (stale from birth).
    # Artifact verified legitimate (364-line reference bridge, ast-parseable),
    # so the pin — not the artifact — was fixed.
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "7756929fcf41b8c97c6c1ae18949c8320fac23f1c6043ce6570b015bf554988e"
