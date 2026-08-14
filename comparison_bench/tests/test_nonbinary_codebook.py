from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_codebook import (
    build_nonbinary_codebook_family,
    gf_rank,
    verify_nonbinary_codebook_family,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def test_gf_rank_uses_pinned_field_not_ordinary_real_rank():
    matrix = ((1, 2), (2, 3))
    assert np.linalg.matrix_rank(np.asarray(matrix)) == 2
    assert gf_rank(matrix, GF2mField.create(4)) == 1


@pytest.mark.parametrize(
    ("q", "expected_entries", "expected_manifest_id"),
    [
        (2, [(16, 2862, "3b1b0f449751efa4ef5bcc49b1b8abf0a8a6fa52f06a20a54372d74014d873e3"), (24, 3886, "4b3499e2331f65cdafc6e96d51c68f5defa16fc05aecf92ca6713ee84a36fdd5"), (32, 4910, "46fc022b799b48a607374728b0a500042506a4770c23c6227a3aa0e81dbf2f7d")], "0e7c359fe605193b91e362a3ae5c68aacdc92ea80da86879c0669b88de63db96"),
        (1024, [(16, 2872, "410824d9fa62f69b374e3800b28f7e0c5ddad599962b9def7eb7b5158785ecfa"), (24, 3896, "27c2219c703af6fe51a8e0db1acbf3d587ab5fad84200db72674562c0858c962"), (32, 4920, "bc94bff90f7148c65d55ccebd5098ad10eab90713c9b2dfd544281e94e6d97aa")], "5dcb29690a2f3a0349383d09b6a77c1f261468dc2eb2a22135b86f009240fc33"),
    ],
)
def test_n1_default_seed_golden_codebook_and_manifest_ids(q, expected_entries, expected_manifest_id):
    manifest, _ = build_nonbinary_codebook_family(q)
    assert [(entry["check_count"], entry["byte_length"], entry["codebook_id"]) for entry in manifest["ordered_entries"]] == expected_entries
    assert manifest["manifest_id"] == expected_manifest_id


@pytest.mark.parametrize("q", [2, 1024])
def test_n1_deterministic_nested_prefixes_and_gf_ranks(q: int):
    manifest, matrices = build_nonbinary_codebook_family(q)
    again_manifest, again_matrices = build_nonbinary_codebook_family(q)
    assert manifest == again_manifest
    assert matrices == again_matrices
    mother = matrices[32]
    field = GF2mField.create(q)
    shifts = manifest["frozen_family"]["ordered_circulant_shifts"]
    assert len(shifts) == len(set(shifts)) == 3
    for row_index, row in enumerate(mother):
        assert row[32 + row_index] == 1
        assert sum(value != 0 for value in row[:32]) == 3
    for checks in (16, 24, 32):
        assert matrices[checks] == mother[:checks]
        assert gf_rank(matrices[checks], field) == checks
    assert verify_nonbinary_codebook_family(manifest, matrices)["status"] == "ok"


def test_n1_verifier_rejects_all_frozen_evidence_tampering():
    manifest, matrices = build_nonbinary_codebook_family(1024)
    for mutate in (
        lambda value: value.__setitem__("field_id", "0" * 64),
        lambda value: value["field"].__setitem__("field_id", "0" * 64),
        lambda value: value["ordered_entries"][0].__setitem__("rank", 0),
        lambda value: value.__setitem__("prefix_relationship", "wrong"),
        lambda value: value["ordered_entries"][0].__setitem__("codebook_id", "0" * 64),
        lambda value: value.__setitem__("manifest_id", "0" * 64),
    ):
        tampered = deepcopy(manifest)
        mutate(tampered)
        assert verify_nonbinary_codebook_family(tampered, matrices)["status"] == "codebook_invalid"
    changed = {checks: tuple(tuple((value + 1) % 1024 if row_index == 0 and column == 0 else value for column, value in enumerate(row)) for row_index, row in enumerate(matrix)) for checks, matrix in matrices.items()}
    assert verify_nonbinary_codebook_family(manifest, changed)["status"] == "codebook_invalid"


def test_n1_rejects_invalid_seed_and_unsupported_domain():
    with pytest.raises(ValueError, match="construction_seed"):
        build_nonbinary_codebook_family(2, construction_seed=True)
    manifest, matrices = build_nonbinary_codebook_family(2)
    bad = deepcopy(manifest)
    bad["q"] = 3
    assert verify_nonbinary_codebook_family(bad, matrices)["status"] == "unsupported_domain"
