"""NBLDPC7 R3 codebook acceptance: the frozen 10-bit -> high/low 5-bit natural
split (exhaustively round-tripped), the per-stratum per-layer check-count
freeze, deterministic PEG construction of the two GF(32) n=1024 layer codes,
canonical bytes, GF(32) rank, degree/parallel-edge contracts, and layered
tamper rejection including cross-layer matrix swaps."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import math
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r3_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def _h32(p):
    p = float(p)
    h2 = -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return h2 + p * math.log2(31)


def test_frozen_seeds_check_counts_and_deterministic_reconstruction():
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    again, again_matrices = cb.build_nbldpc_v7_r3_codebook()
    assert manifest == again and matrices == again_matrices
    assert manifest["canonical_schema"] == "NBLDPC7R3" and manifest["q"] == 32
    assert manifest["n"] == 1024 and manifest["method"] == cb.METHOD == "nbldpc_formal_v7_r3_gf32x2"
    assert manifest["construction_version"] == 1
    assert manifest["field_id"] == GF2mField.create(32).spec.field_id
    assert tuple(sorted(matrices)) == ((404, 0), (404, 1), (558, 0), (558, 1))
    assert cb._CHECK_COUNTS == {0.20: 404, 0.30: 558}
    assert cb._FROZEN_SEEDS == {0.20: {0: 202608050001, 1: 202608050002},
                                0.30: {0: 202608050001, 1: 202608050002}}
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, matrices)["status"] == "ok"
    container_manifest, container_matrices = cb.codebook()
    assert container_manifest == manifest and container_matrices == matrices


def test_check_count_freeze_is_exact_arithmetic():
    # V7-30 freeze: m0 = m1 = ceil(1.15*H_32(p)/5 * 1024) with H_32(p) =
    # h2(p) + p*log2(31); the layers are symmetric (both words carry 5 bits of
    # the same 10-bit symbol under the same frozen frame-error model).
    expected = {0.20: math.ceil(1.15 * _h32(0.20) / 5.0 * 1024.0),
                0.30: math.ceil(1.15 * _h32(0.30) / 5.0 * 1024.0)}
    assert expected == {0.20: 404, 0.30: 558}
    assert all(cb._CHECK_COUNTS[p] == expected[p] for p in (0.20, 0.30))
    # disclosure 5*(m0+m1) stays below the frozen 8.75 bits/symbol ceiling.
    for p, m in expected.items():
        assert 5 * 2 * m / 1024.0 <= 8.75
        assert 5 * 2 * m == 4040 if p == 0.20 else 5 * 2 * m == 5580


def test_split_roundtrip_exhaustive_and_split_vector():
    # the frozen natural split is reversible for ALL 1024 10-bit symbols.
    for symbol in range(1024):
        high, low = cb.split_symbol(symbol)
        assert high == symbol >> 5 and low == symbol & 31
        assert cb.join_symbol(high, low) == symbol
        assert 0 <= high < 32 and 0 <= low < 32
    vector = (0, 1, 31, 32, 33, 1023, 512, 511)
    high, low = cb.split_vector(vector)
    assert high == (0, 0, 0, 1, 1, 31, 16, 15)
    assert low == (0, 1, 31, 0, 1, 31, 0, 31)
    assert cb.join_vector(high, low) == vector
    with pytest.raises(ValueError, match="10-bit natural domain"):
        cb.split_symbol(1024)
    with pytest.raises(ValueError, match="GF\\(32\\) domain"):
        cb.join_symbol(32, 0)
    with pytest.raises(ValueError, match="equal-length"):
        cb.join_vector((0, 1), (0,))


def test_canonical_bytes_reconstruct_byte_for_byte():
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    field = GF2mField.create(32)
    for entry in manifest["ordered_entries"]:
        p, m = entry["stratum_p"], entry["check_count"]
        for layer in (0, 1):
            matrix = matrices[(m, layer)]
            header = {"canonical_schema": "NBLDPC7R3", "construction_version": 1,
                      "method": cb.METHOD, "q": 32, "n": 1024, "m": m,
                      "stratum_p": p, "layer": layer,
                      "layer_label": "high" if layer == 0 else "low",
                      "construction_seed": entry[f"construction_seed_{layer}"],
                      "variable_distribution": dict(cb._DISTRIBUTIONS[p]),
                      "split_mapping": cb._SPLIT_MAPPING,
                      "first_edge_rule": cb._FIRST_EDGE_RULE,
                      "peg_edge_rule": cb._PEG_EDGE_RULE,
                      "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
                      "field": asdict(field.spec)}
            expected = cb._MAGIC + cb._compact(header) + b"\n"
            for row in matrix:
                for value in row:
                    expected += int(value).to_bytes(2, "big")
            assert cb._sha(expected) == entry[f"canonical_sha256_{layer}"]
            assert len(expected) == entry[f"canonical_byte_length_{layer}"]


def test_full_rank_degrees_and_no_parallel_edges():
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    field = GF2mField.create(32)
    for entry in manifest["ordered_entries"]:
        p, m = entry["stratum_p"], entry["check_count"]
        assert entry["check_count_total"] == 2 * m
        assert entry["syndrome_disclosure_bits_layer"] == 5 * m
        assert entry["syndrome_disclosure_bits_total"] == 5 * 2 * m
        for layer in (0, 1):
            matrix = matrices[(m, layer)]
            assert len(matrix) == m and all(len(row) == 1024 for row in matrix)
            assert all(0 <= int(x) < 32 for row in matrix for x in row)
            assert all(any(row[col] for row in matrix) for col in range(1024))
            # frozen ensemble: every column has degree exactly 3.
            assert all(sum(row[col] != 0 for row in matrix) == 3 for col in range(1024))
            assert entry[f"rank_{layer}"] == m
            assert cb.gf_rank(matrix, field) == m
            assert entry[f"parallel_edges_{layer}"] == 0
            assert entry["edge_count"] == 3 * 1024 == 3072
            histogram = {int(k): int(v) for k, v in entry[f"check_degree_histogram_{layer}"].items()}
            assert sum(d * count for d, count in histogram.items()) == 3072
            assert all(2 <= d for d in histogram)
            assert 3072 / m <= 12.0
            assert entry[f"cycle_count_{layer}"] >= 0


def test_column_degrees_contract():
    for p in (0.20, 0.30):
        degrees = cb.column_degrees(p)
        assert len(degrees) == 1024
        assert set(degrees) == {3}


def test_constructed_matrix_matches_the_pinned_constructor():
    field = GF2mField.create(32)
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    for p, m in cb._CHECK_COUNTS.items():
        for layer in (0, 1):
            seed = cb._FROZEN_SEEDS[p][layer]
            direct, degrees, parallel, cycles = cb._matrix_cached(m, seed, p)
            assert tuple(tuple(int(x) for x in row) for row in direct) == matrices[(m, layer)]
            assert parallel == 0
            assert sum(degrees) == 3 * 1024
            assert cb.gf_rank(direct, field) == m


def test_byte_and_semantic_tamper_are_rejected():
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    # byte drift: flip one coefficient in the p=.20 layer-0 matrix.
    wrong = {key: matrix for key, matrix in matrices.items()}
    row = list(wrong[(404, 0)][0]); row[0] = row[0] ^ 1 if row[0] else 1
    wrong[(404, 0)] = tuple([tuple(row)] + list(wrong[(404, 0)])[1:])
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, wrong)["status"] == "codebook_invalid"
    # semantic drift: forged seed / q / n / distribution / coefficient rule.
    for key, value in (("construction_seed_0", 1), ("q", 512), ("n", 512),
                       ("coefficient_derivation", "forged"),
                       ("first_edge_rule", "reversed"), ("peg_edge_rule", "random")):
        tampered = deepcopy(manifest)
        tampered["ordered_entries"] = [dict(e) for e in tampered["ordered_entries"]]
        tampered["ordered_entries"][0][key] = value
        tampered["manifest_id"] = cb._sha(cb._compact(tampered))
        assert cb.verify_nbldpc_v7_r3_codebook(tampered, matrices)["status"] == "codebook_invalid"
    # link drift: canonical_sha256 no longer matches the canonical bytes.
    linked = deepcopy(manifest)
    linked["ordered_entries"] = [dict(e) for e in linked["ordered_entries"]]
    linked["ordered_entries"][0]["canonical_sha256_0"] = "0" * 64
    linked["manifest_id"] = cb._sha(cb._compact(linked))
    assert cb.verify_nbldpc_v7_r3_codebook(linked, matrices)["status"] == "codebook_invalid"
    # split-mapping drift.
    split = deepcopy(manifest)
    split["split_mapping"] = "forged"
    split["manifest_id"] = cb._sha(cb._compact(split))
    assert cb.verify_nbldpc_v7_r3_codebook(split, matrices)["status"] == "codebook_invalid"


def test_verify_rejects_foreign_matrix_cross_layer_swap_and_missing_stratum():
    manifest, matrices = cb.build_nbldpc_v7_r3_codebook()
    # cross-layer swap: the two layer matrices of the same stratum swapped.
    wrong = {key: matrix for key, matrix in matrices.items()}
    wrong[(404, 1)] = wrong[(404, 0)]
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, wrong)["status"] == "codebook_invalid"
    # foreign matrix: a p=.30 layer matrix smuggled into the p=.20 container.
    wrong2 = {key: matrix for key, matrix in matrices.items()}
    wrong2[(404, 0)] = wrong2[(558, 0)]
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, wrong2)["status"] == "codebook_invalid"
    # missing stratum keys.
    missing = {key: matrix for key, matrix in matrices.items() if key[0] != 404}
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, missing)["status"] == "codebook_invalid"
    missing_layer = {key: matrix for key, matrix in matrices.items() if key != (558, 1)}
    assert cb.verify_nbldpc_v7_r3_codebook(manifest, missing_layer)["status"] == "codebook_invalid"
