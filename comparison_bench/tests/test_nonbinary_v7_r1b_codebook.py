"""NBLDPC7 R1B codebook acceptance: exact R1A mother reconstruction under the
new identity, mother-provenance binding, deterministic multiplier spec,
canonical bytes, GF rank, and layered tamper rejection (bytes, semantic
self-hash, manifest links, mother provenance, multipliers)."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1b_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_codebook as r1a
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def test_frozen_seed_mother_provenance_and_deterministic_reconstruction():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    again, again_matrix = cb.build_nbldpc_v7_r1b_codebook()
    assert manifest == again and matrix == again_matrix
    assert manifest["canonical_schema"] == "NBLDPC7R1B" and manifest["q"] == 1024
    assert manifest["n"] == 256 and manifest["m"] == 170
    assert manifest["method"] == cb.METHOD == "nbldpc_formal_v7_r1b_mr1"
    assert manifest["construction_version"] == 1
    # exact R1A mother under the new identity: same construction seed and the
    # mother provenance must equal the frozen R1A canonical hash.
    assert manifest["construction_seed"] == cb._FROZEN_SEED == r1a._FROZEN_SEED == 2026080400
    assert manifest["multiplier_seed"] == cb._MULTIPLIER_SEED == 2026080401
    assert manifest["mother_provenance_sha256"] == cb._MOTHER_PROVENANCE_SHA256 \
        == r1a.build_nbldpc_v7_r1a_codebook()[0]["canonical_sha256"] \
        == "75f625bbbe1ebd74b0cf8b0b3646fa1af9ce6e5a66562e07a75507d175570608"
    assert manifest["mother_provenance_byte_length"] == 87793
    assert manifest["field_id"] == GF2mField.create(1024).spec.field_id
    assert manifest["edge_count"] == 512
    # every manifest value must reconstruct byte-for-byte from the constructor.
    header = {"canonical_schema": "NBLDPC7R1B", "construction_version": 1, "method": cb.METHOD,
              "q": 1024, "n": 256, "m": 170, "construction_seed": manifest["construction_seed"],
              "multiplier_seed": manifest["multiplier_seed"],
              "mother_provenance_sha256": cb._MOTHER_PROVENANCE_SHA256,
              "mother_provenance_byte_length": 87793,
              "first_edge_rule": cb._FIRST_EDGE_RULE, "second_edge_rule": cb._SECOND_EDGE_RULE,
              "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
              "multiplier_derivation": cb._MULTIPLIER_DERIVATION,
              "field": asdict(GF2mField.create(1024).spec)}
    expected = cb._MAGIC + cb._compact(header) + b"\n"
    for row in matrix:
        for value in row:
            expected += int(value).to_bytes(2, "big")
    for value in cb.multipliers():
        expected += int(value).to_bytes(2, "big")
    assert cb._sha(expected) == manifest["canonical_sha256"]
    assert len(expected) == manifest["canonical_byte_length"]
    assert cb.verify_nbldpc_v7_r1b_codebook(manifest, matrix)["status"] == "ok"
    container_manifest, container_matrix = cb.codebook()
    assert container_manifest == manifest and container_matrix == matrix


def test_mother_matrix_is_byte_identical_to_r1a():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    r1a_manifest, r1a_matrix = r1a.build_nbldpc_v7_r1a_codebook()
    assert tuple(tuple(int(x) for x in row) for row in matrix) == r1a_matrix
    # the R1B mother canonical bytes (R1A byte scheme) hash to the frozen R1A id.
    mother_bytes = r1a._canonical_bytes(matrix, GF2mField.create(1024), seed=r1a._FROZEN_SEED)
    assert cb._sha(mother_bytes) == r1a_manifest["canonical_sha256"]
    assert len(mother_bytes) == r1a_manifest["canonical_byte_length"]
    assert manifest["mother_codebook_manifest_id"] == r1a_manifest["manifest_id"]


def manifest_multiplier_spec_id():
    return cb.build_nbldpc_v7_r1b_codebook()[0]["multiplier_spec_id"]


def test_multipliers_are_deterministic_nonzero_and_domain_separated():
    first = cb.multipliers()
    second = cb.multipliers()
    assert first == second and len(first) == 256
    assert all(1 <= value < 1024 for value in first)
    # independently derived per variable: the derivation is SHA256-domain-
    # separated from the mother coefficients and from any frame data.
    field = GF2mField.create(1024)
    assert all(field.mul(value, field.inverse(value)) == 1 for value in first)
    assert cb._multiplier(cb._MULTIPLIER_SEED, 3) == first[3]
    coefficient_style = r1a._coefficient(cb._MULTIPLIER_SEED, 0, 3)
    assert first[3] != coefficient_style  # distinct domain separation
    assert cb.multiplier_spec_id() == cb._sha(cb._compact(
        {"multiplier_seed": cb._MULTIPLIER_SEED, "derivation": cb._MULTIPLIER_DERIVATION,
         "count": 256, "multipliers": list(first)}))
    assert cb.multiplier_spec_id() == manifest_multiplier_spec_id()


def test_full_rank_degree_histogram_and_no_parallel_edges():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    field = GF2mField.create(1024)
    assert len(matrix) == 170 and all(len(row) == 256 for row in matrix)
    assert all(0 <= int(x) < 1024 for row in matrix for x in row)
    assert all(any(row[col] for row in matrix) for col in range(256))
    assert all(sum(row[col] != 0 for row in matrix) == 2 for col in range(256))
    assert manifest["check_degree_histogram"] == {"3": 168, "4": 2}
    assert manifest["rank"] == 170
    assert cb.gf_rank(matrix, field) == 170
    assert manifest["parallel_edges"] == 0
    assert manifest["cycle_count"] == 85  # identical mother topology
    assert manifest["variable_degree_min"] == 2 and manifest["variable_degree_max"] == 2
    # the same mother syndrome disclosure: 10*m = 1700 bits.
    assert 10 * manifest["m"] == 1700


def test_repetition_metadata_and_final_depth():
    manifest, _ = cb.build_nbldpc_v7_r1b_codebook()
    assert manifest["repetition_depth"] == 1
    assert abs(manifest["effective_rate"] - 1 / 6) < 1e-12
    assert manifest["multiplier_count"] == 256
    assert 1 <= manifest["multiplier_min"] <= manifest["multiplier_max"] < 1024
    assert manifest["multipliers"] == list(cb.multipliers())


def test_search_never_runs_after_freeze():
    assert not any(name.startswith("_find") or "search" in name.lower() for name in dir(cb))
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    assert manifest["construction_seed"] == cb._FROZEN_SEED
    assert manifest["multiplier_seed"] == cb._MULTIPLIER_SEED
    assert cb.verify_nbldpc_v7_r1b_codebook(manifest, matrix)["status"] == "ok"


def test_byte_and_semantic_tamper_are_rejected():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    # byte drift: flip one coefficient in a supplied matrix.
    wrong = list(matrix)
    row = list(wrong[0]); row[0] = row[0] ^ 1 if row[0] else 1; wrong[0] = tuple(row)
    assert cb.verify_nbldpc_v7_r1b_codebook(manifest, tuple(wrong))["status"] == "codebook_invalid"
    # semantic drift: forged seed / q / derivation, re-hashed manifest rejected.
    forged = deepcopy(manifest)
    forged["construction_seed"] = forged["construction_seed"] + 1
    forged["manifest_id"] = cb._sha(cb._compact(forged))
    assert cb.verify_nbldpc_v7_r1b_codebook(forged, matrix)["status"] == "codebook_invalid"
    for key, value in (("q", 512), ("n", 128), ("m", 171),
                       ("coefficient_derivation", "forged"),
                       ("first_edge_rule", "reversed"), ("second_edge_rule", "random"),
                       ("multiplier_derivation", "forged")):
        tampered = deepcopy(manifest); tampered[key] = value
        tampered["manifest_id"] = cb._sha(cb._compact(tampered))
        assert cb.verify_nbldpc_v7_r1b_codebook(tampered, matrix)["status"] == "codebook_invalid"
    # link drift: canonical_sha256 no longer matches the canonical bytes.
    linked = deepcopy(manifest)
    linked["canonical_sha256"] = "0" * 64
    assert cb.verify_nbldpc_v7_r1b_codebook(linked, matrix)["status"] == "codebook_invalid"


def test_mother_provenance_binding_rejects_foreign_mother():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    # A re-signed manifest claiming a different mother provenance is rejected.
    forged = deepcopy(manifest)
    forged["mother_provenance_sha256"] = "0" * 64
    forged["manifest_id"] = cb._sha(cb._compact(forged))
    assert cb.verify_nbldpc_v7_r1b_codebook(forged, matrix)["status"] == "codebook_invalid"
    # A supplied matrix that is not the exact R1A mother is rejected even when
    # the manifest is untouched (reconstruction mismatch), and the frozen
    # mother-provenance constant still independently binds the R1A identity.
    drift = list(matrix)
    row = list(drift[170 - 1]); row[255] = row[255] ^ 1 if row[255] else 1; drift[170 - 1] = tuple(row)
    assert cb.verify_nbldpc_v7_r1b_codebook(manifest, tuple(drift))["status"] == "codebook_invalid"
    with pytest.raises(ValueError, match="provenance drift"):
        cb._mother_provenance(tuple(drift), GF2mField.create(1024))


def test_multiplier_tamper_is_rejected():
    manifest, matrix = cb.build_nbldpc_v7_r1b_codebook()
    # multiplier list drift (re-signed) is rejected.
    forged = deepcopy(manifest)
    forged["multipliers"] = list(manifest["multipliers"])
    forged["multipliers"][0] = 1 if forged["multipliers"][0] != 1 else 2
    forged["manifest_id"] = cb._sha(cb._compact(forged))
    assert cb.verify_nbldpc_v7_r1b_codebook(forged, matrix)["status"] == "codebook_invalid"
    # multiplier seed drift (re-signed) is rejected.
    tampered = deepcopy(manifest)
    tampered["multiplier_seed"] = tampered["multiplier_seed"] + 1
    tampered["manifest_id"] = cb._sha(cb._compact(tampered))
    assert cb.verify_nbldpc_v7_r1b_codebook(tampered, matrix)["status"] == "codebook_invalid"
    # the canonical bytes themselves bind the multiplier list: a multiplier
    # byte drift changes canonical_sha256 -> link drift is rejected.
    assert manifest["canonical_sha256"] != cb._sha(manifest["canonical_sha256"].encode("ascii"))
