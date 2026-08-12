"""NBLDPC7 R1A codebook acceptance: deterministic PEG construction, canonical
bytes, GF rank, degree/cycle metrics, check-count freeze, and layered tamper
rejection."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def test_frozen_seed_and_deterministic_byte_for_byte_reconstruction():
    manifest, matrix = cb.build_nbldpc_v7_r1a_codebook()
    again, again_matrix = cb.build_nbldpc_v7_r1a_codebook()
    assert manifest == again and matrix == again_matrix
    assert manifest["canonical_schema"] == "NBLDPC7" and manifest["q"] == 1024
    assert manifest["n"] == 256 and manifest["m"] == 170
    assert manifest["construction_version"] == 1
    assert manifest["construction_seed"] == cb._FROZEN_SEED == 2026080400
    assert manifest["field_id"] == GF2mField.create(1024).spec.field_id
    assert manifest["edge_count"] == 512
    # every manifest value must reconstruct byte-for-byte from the constructor.
    seed = manifest["construction_seed"]
    header = {"canonical_schema": "NBLDPC7", "construction_version": 1, "method": cb.METHOD,
              "q": 1024, "n": 256, "m": 170, "construction_seed": seed,
              "first_edge_rule": cb._FIRST_EDGE_RULE, "second_edge_rule": cb._SECOND_EDGE_RULE,
              "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
              "field": asdict(GF2mField.create(1024).spec)}
    expected = cb._MAGIC + cb._compact(header) + b"\n"
    for row in matrix:
        for value in row:
            expected += int(value).to_bytes(2, "big")
    assert cb._sha(expected) == manifest["canonical_sha256"]
    assert len(expected) == manifest["canonical_byte_length"]
    assert cb.verify_nbldpc_v7_r1a_codebook(manifest, matrix)["status"] == "ok"
    container_manifest, container_matrix = cb.codebook()
    assert container_manifest == manifest and container_matrix == matrix


def test_full_rank_degree_histogram_and_no_parallel_edges():
    manifest, matrix = cb.build_nbldpc_v7_r1a_codebook()
    field = GF2mField.create(1024)
    assert len(matrix) == 170 and all(len(row) == 256 for row in matrix)
    assert all(0 <= int(x) < 1024 for row in matrix for x in row)
    assert all(any(row[col] for row in matrix) for col in range(256))
    # variable degree is exactly two for every column ((dv,dc)=(2,3) mother).
    assert all(sum(row[col] != 0 for row in matrix) == 2 for col in range(256))
    # frozen check-count freeze: m=170, exactly 168 x degree-3 + 2 x degree-4.
    assert manifest["check_degree_histogram"] == {"3": 168, "4": 2}
    assert manifest["rank"] == 170
    assert cb.gf_rank(matrix, field) == 170
    assert manifest["parallel_edges"] == 0
    assert manifest["cycle_count"] >= 0
    assert manifest["variable_degree_min"] == 2 and manifest["variable_degree_max"] == 2
    # syndrome disclosure freeze: 10*m = 1700 bits.
    assert 10 * manifest["m"] == 1700


def test_search_never_runs_after_freeze():
    # Construction is a fixed constructor, not a search: the frozen seed is
    # read directly and no acceptance-search function exists in the module.
    assert not any(name.startswith("_find") or "search" in name.lower() for name in dir(cb))
    manifest, matrix = cb.build_nbldpc_v7_r1a_codebook()
    assert manifest["construction_seed"] == cb._FROZEN_SEED
    assert cb.verify_nbldpc_v7_r1a_codebook(manifest, matrix)["status"] == "ok"


def test_byte_and_semantic_tamper_are_rejected():
    manifest, matrix = cb.build_nbldpc_v7_r1a_codebook()
    # byte drift: flip one coefficient in a supplied matrix.
    wrong = list(matrix)
    row = list(wrong[0]); row[0] = row[0] ^ 1 if row[0] else 1; wrong[0] = tuple(row)
    assert cb.verify_nbldpc_v7_r1a_codebook(manifest, tuple(wrong))["status"] == "codebook_invalid"
    # semantic drift: forged seed / q / derivation, re-hashed manifest rejected.
    forged = deepcopy(manifest)
    forged["construction_seed"] = forged["construction_seed"] + 1
    forged["manifest_id"] = cb._sha(cb._compact(forged))
    assert cb.verify_nbldpc_v7_r1a_codebook(forged, matrix)["status"] == "codebook_invalid"
    for key, value in (("q", 512), ("n", 128), ("m", 171),
                       ("coefficient_derivation", "forged"),
                       ("first_edge_rule", "reversed"), ("second_edge_rule", "random")):
        tampered = deepcopy(manifest); tampered[key] = value
        tampered["manifest_id"] = cb._sha(cb._compact(tampered))
        assert cb.verify_nbldpc_v7_r1a_codebook(tampered, matrix)["status"] == "codebook_invalid"
    # link drift: canonical_sha256 no longer matches the canonical bytes.
    linked = deepcopy(manifest)
    linked["canonical_sha256"] = "0" * 64
    assert cb.verify_nbldpc_v7_r1a_codebook(linked, matrix)["status"] == "codebook_invalid"


def test_constructed_matrix_matches_the_pinned_constructor():
    # The canonical build path must equal a direct _construct call with the
    # frozen seed (reconstruction provenance).
    field = GF2mField.create(1024)
    manifest, matrix = cb.build_nbldpc_v7_r1a_codebook()
    direct, degrees, parallel, cycles = cb._matrix_cached(cb._FROZEN_SEED)
    assert tuple(tuple(int(x) for x in row) for row in direct) == matrix
    assert parallel == 0 and cycles == manifest["cycle_count"]
    assert sum(degrees) == 2 * 256
    assert cb.gf_rank(direct, field) == 170
