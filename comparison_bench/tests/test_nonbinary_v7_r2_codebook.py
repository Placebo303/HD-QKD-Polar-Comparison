"""NBLDPC7 R2 codebook acceptance: deterministic PEG construction from the
frozen DE selection, canonical bytes, GF rank, degree/parallel-edge contracts,
the check-count freeze, the DE-selection freeze, and layered tamper
rejection."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r2_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r2_de as de
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def test_frozen_seeds_check_counts_and_deterministic_reconstruction():
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    again, again_matrices = cb.build_nbldpc_v7_r2_codebook()
    assert manifest == again and matrices == again_matrices
    assert manifest["canonical_schema"] == "NBLDPC7R2" and manifest["q"] == 1024
    assert manifest["n"] == 1024 and manifest["method"] == cb.METHOD == "nbldpc_formal_v7_r2_qsc_de"
    assert manifest["construction_version"] == 1
    assert manifest["field_id"] == GF2mField.create(1024).spec.field_id
    assert tuple(sorted(matrices)) == (321, 458)
    assert cb._FROZEN_SEEDS == {0.20: 2026080402, 0.30: 2026080403}
    assert cb._CHECK_COUNTS == {0.20: 321, 0.30: 458}
    assert cb.verify_nbldpc_v7_r2_codebook(manifest, matrices)["status"] == "ok"
    container_manifest, container_matrices = cb.codebook()
    assert container_manifest == manifest and container_matrices == matrices


def test_canonical_bytes_reconstruct_byte_for_byte():
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    field = GF2mField.create(1024)
    for entry in manifest["ordered_entries"]:
        p = entry["stratum_p"]
        m = entry["check_count"]
        matrix = matrices[m]
        header = {"canonical_schema": "NBLDPC7R2", "construction_version": 1,
                  "method": cb.METHOD, "q": 1024, "n": 1024, "m": m,
                  "stratum_p": p, "construction_seed": entry["construction_seed"],
                  "variable_distribution": dict(cb._DISTRIBUTIONS[p]),
                  "de_selection": {"method": "qary_density_evolution",
                                   "threshold_proxy": cb._DE_THRESHOLD_PROXIES[p],
                                   "search_record": cb._DE_SEARCH_RECORDS[p]},
                  "first_edge_rule": cb._FIRST_EDGE_RULE, "peg_edge_rule": cb._PEG_EDGE_RULE,
                  "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
                  "field": asdict(field.spec)}
        expected = cb._MAGIC + cb._compact(header) + b"\n"
        for row in matrix:
            for value in row:
                expected += int(value).to_bytes(2, "big")
        assert cb._sha(expected) == entry["canonical_sha256"]
        assert len(expected) == entry["canonical_byte_length"]


def test_full_rank_degrees_and_no_parallel_edges():
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    field = GF2mField.create(1024)
    for entry in manifest["ordered_entries"]:
        p, m = entry["stratum_p"], entry["check_count"]
        matrix = matrices[m]
        assert len(matrix) == m and all(len(row) == 1024 for row in matrix)
        assert all(0 <= int(x) < 1024 for row in matrix for x in row)
        assert all(any(row[col] for row in matrix) for col in range(1024))
        # frozen DE selection: every column has degree exactly 3.
        assert all(sum(row[col] != 0 for row in matrix) == 3 for col in range(1024))
        assert entry["variable_degree_min"] == 3 and entry["variable_degree_max"] == 3
        assert entry["rank"] == m
        assert cb.gf_rank(matrix, field) == m
        assert entry["parallel_edges"] == 0
        assert entry["edge_count"] == 3 * 1024 == 3072
        # structural check-degree contract (mean <= 12, every degree in bounds).
        histogram = {int(k): int(v) for k, v in entry["check_degree_histogram"].items()}
        assert sum(d * count for d, count in histogram.items()) == 3072
        assert all(2 <= d <= de.CHECK_DEGREE_MAX for d in histogram)
        assert 3072 / m <= de.MEAN_CHECK_DEGREE_MAX
        assert entry["cycle_count"] >= 0
        assert entry["de_threshold_proxy"] == cb._DE_THRESHOLD_PROXIES[p]


def test_de_selection_freeze_binds_search_to_codebook():
    manifest, _ = cb.build_nbldpc_v7_r2_codebook()
    # the manifest records the frozen DE selection identity.
    identity = cb._sha(cb._compact({
        p: {"m": cb._CHECK_COUNTS[p], "distribution": dict(cb._DISTRIBUTIONS[p]),
            "threshold_proxy": cb._DE_THRESHOLD_PROXIES[p]}
        for p in (0.20, 0.30)}))
    assert manifest["de_selection_identity"] == identity
    # the frozen check-count freeze equals the exact DE formula.
    assert all(cb._CHECK_COUNTS[p] == de.frozen_check_count(1024, p) for p in (0.20, 0.30))


def test_search_never_runs_after_freeze():
    # Construction is a fixed constructor, not a search: the frozen seeds are
    # read directly at runtime.  The only acceptance helper is the documented
    # one-time find_frozen_seeds (never invoked by build/verify); the frozen
    # DE records (_DE_SEARCH_RECORDS) are data constants, not functions.
    assert not any((name.startswith("_find") or "search" in name.lower())
                   and name != "find_frozen_seeds"
                   for name in dir(cb) if callable(getattr(cb, name)))
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    assert manifest["ordered_entries"][0]["construction_seed"] == cb._FROZEN_SEEDS[0.20]
    assert cb.verify_nbldpc_v7_r2_codebook(manifest, matrices)["status"] == "ok"


def test_column_degrees_contract():
    for p in (0.20, 0.30):
        degrees = cb.column_degrees(p)
        assert len(degrees) == 1024
        assert all(2 <= d <= 8 for d in degrees)
        # the frozen selection is the regular degree-3 distribution.
        assert set(degrees) == {3}


def test_byte_and_semantic_tamper_are_rejected():
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    # byte drift: flip one coefficient in the p=.20 matrix.
    wrong = {m: matrix for m, matrix in matrices.items()}
    row = list(wrong[321][0]); row[0] = row[0] ^ 1 if row[0] else 1
    wrong[321] = tuple([tuple(row)] + list(wrong[321])[1:])
    assert cb.verify_nbldpc_v7_r2_codebook(manifest, wrong)["status"] == "codebook_invalid"
    # semantic drift: forged seed / q / n / distribution / threshold, re-hashed.
    for key, value in (("construction_seed", 1), ("q", 512), ("n", 512),
                       ("coefficient_derivation", "forged"),
                       ("first_edge_rule", "reversed"), ("peg_edge_rule", "random"),
                       ("de_threshold_proxy", 0.5)):
        tampered = deepcopy(manifest)
        tampered["ordered_entries"] = [dict(e) for e in tampered["ordered_entries"]]
        tampered["ordered_entries"][0][key] = value
        tampered["manifest_id"] = cb._sha(cb._compact(tampered))
        assert cb.verify_nbldpc_v7_r2_codebook(tampered, matrices)["status"] == "codebook_invalid"
    # link drift: canonical_sha256 no longer matches the canonical bytes.
    linked = deepcopy(manifest)
    linked["ordered_entries"] = [dict(e) for e in linked["ordered_entries"]]
    linked["ordered_entries"][0]["canonical_sha256"] = "0" * 64
    linked["manifest_id"] = cb._sha(cb._compact(linked))
    assert cb.verify_nbldpc_v7_r2_codebook(linked, matrices)["status"] == "codebook_invalid"


def test_verify_rejects_foreign_matrix_and_missing_stratum():
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    # swap a different matrix into the container.
    wrong = {m: matrix for m, matrix in matrices.items()}
    wrong[458] = wrong[321]
    assert cb.verify_nbldpc_v7_r2_codebook(manifest, wrong)["status"] == "codebook_invalid"
    # missing stratum key.
    missing = {m: matrix for m, matrix in matrices.items() if m != 321}
    assert cb.verify_nbldpc_v7_r2_codebook(manifest, missing)["status"] == "codebook_invalid"


def test_constructed_matrix_matches_the_pinned_constructor():
    field = GF2mField.create(1024)
    manifest, matrices = cb.build_nbldpc_v7_r2_codebook()
    for p, m in cb._CHECK_COUNTS.items():
        seed = cb._FROZEN_SEEDS[p]
        direct, degrees, parallel, cycles = cb._matrix_cached(m, seed, p)
        assert tuple(tuple(int(x) for x in row) for row in direct) == matrices[m]
        assert parallel == 0
        assert sum(degrees) == 3 * 1024
        assert cb.gf_rank(direct, field) == m
