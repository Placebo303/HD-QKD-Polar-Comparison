"""NBLDPC6 codebook acceptance: deterministic PEG construction, canonical
bytes, GF rank, degree/cycle metrics, and layered tamper rejection (A02/A07)."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v6_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def test_frozen_seeds_and_deterministic_byte_for_byte_reconstruction():
    manifest, matrices = cb.build_nbldpc_v6_codebook()
    again, again_matrices = cb.build_nbldpc_v6_codebook()
    assert manifest == again and matrices == again_matrices
    assert manifest["canonical_schema"] == "NBLDPC6" and manifest["q"] == 1024 and manifest["n"] == 1024
    assert manifest["construction_version"] == 1 and manifest["field_id"] == GF2mField.create(1024).spec.field_id
    assert list(matrices.keys()) == [320, 480]
    assert {e["construction_seed"] for e in manifest["ordered_entries"]} == set({320: 2026080200, 480: 2026080300}.values())
    # every ordered entry's canonical bytes hash and length must reconstruct.
    for entry in manifest["ordered_entries"]:
        m = entry["check_count"]; seed = entry["construction_seed"]
        row_major = matrices[m]
        header = {"canonical_schema": "NBLDPC6", "construction_version": 1, "method": "nbldpc_formal_v6_long",
                  "q": 1024, "n": 1024, "m": m, "stratum_p": entry["stratum_p"],
                  "construction_seed": seed, "first_edge_rule": cb._FIRST_EDGE_RULE,
                  "second_edge_rule": cb._SECOND_EDGE_RULE,
                  "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
                  "field": asdict(GF2mField.create(1024).spec)}
        expected = cb._MAGIC + cb._compact(header) + b"\n"
        for row in row_major:
            for value in row:
                expected += int(value).to_bytes(2, "big")
        assert cb._sha(expected) == entry["canonical_sha256"]
        assert len(expected) == entry["canonical_byte_length"]
    assert cb.verify_nbldpc_v6_codebook(manifest, matrices)["status"] == "ok"
    container_manifest, container_matrices = cb.codebook()
    assert container_manifest == manifest and container_matrices == matrices


def test_full_rank_degree_balance_and_no_parallel_edges():
    manifest, matrices = cb.build_nbldpc_v6_codebook()
    field = GF2mField.create(1024)
    expected = {320: (6, 7), 480: (4, 5)}
    for entry in manifest["ordered_entries"]:
        m = entry["check_count"]
        rows = matrices[m]
        assert len(rows) == m and all(len(row) == 1024 for row in rows)
        assert all(0 <= int(x) < 1024 for row in rows for x in row)
        assert all(any(row[col] for row in rows) for col in range(1024))
        # variable degree is exactly two for every column.
        assert all(sum(row[col] != 0 for row in rows) == 2 for col in range(1024))
        assert entry["rank"] == m  # full GF(1024) row rank.
        assert entry["parallel_edges"] == 0
        assert entry["variable_degree_min"] == 2 and entry["variable_degree_max"] == 2
        histogram = entry["check_degree_histogram"]
        assert sorted(map(int, histogram)) == list(expected[m])
        # check degrees differ by at most one (frozen histogram).
        assert max(int(k) for k in histogram) - min(int(k) for k in histogram) == 1
        assert entry["edge_count"] == 2048 and entry["cycle_count"] >= 0
    assert cb.gf_rank(matrices[320], field) == 320
    assert cb.gf_rank(matrices[480], field) == 480


def test_search_never_runs_after_freeze():
    # Construction is a fixed constructor, not a search: the frozen seeds are
    # read directly and no acceptance-search function exists in the module.
    assert not any(name.startswith("_find") or "search" in name.lower() for name in dir(cb))
    manifest, matrices = cb.build_nbldpc_v6_codebook()
    assert {e["check_count"]: e["construction_seed"] for e in manifest["ordered_entries"]} == dict(cb._FROZEN_SEEDS)
    assert cb.verify_nbldpc_v6_codebook(manifest, matrices)["status"] == "ok"


def test_byte_and_semantic_tamper_are_rejected():
    manifest, matrices = cb.build_nbldpc_v6_codebook()
    # byte drift: flip one coefficient in a supplied matrix.
    wrong = deepcopy(matrices)
    row = list(wrong[320][0]); row[0] = row[0] ^ 1 if row[0] else 1; wrong[320] = (tuple(row),) + wrong[320][1:]
    assert cb.verify_nbldpc_v6_codebook(manifest, wrong)["status"] == "codebook_invalid"
    # semantic drift: forged seed / rank / derivation, re-hashed manifest is rejected.
    forged = deepcopy(manifest)
    forged["ordered_entries"] = [dict(e, construction_seed=e["construction_seed"] + 1) for e in forged["ordered_entries"]]
    forged["manifest_id"] = cb._sha(cb._compact(forged))
    assert cb.verify_nbldpc_v6_codebook(forged, matrices)["status"] == "codebook_invalid"
    for key, value in (("q", 512), ("coefficient_derivation", "forged"),
                       ("first_edge_rule", "reversed"), ("second_edge_rule", "random")):
        tampered = deepcopy(manifest); tampered[key] = value
        tampered["manifest_id"] = cb._sha(cb._compact(tampered))
        assert cb.verify_nbldpc_v6_codebook(tampered, matrices)["status"] == "codebook_invalid"
    # link drift: canonical_sha256 no longer matches the canonical bytes.
    linked = deepcopy(manifest)
    linked["ordered_entries"][0]["canonical_sha256"] = "0" * 64
    assert cb.verify_nbldpc_v6_codebook(linked, matrices)["status"] == "codebook_invalid"


def test_constructed_matrix_matches_the_pinned_constructor():
    # The canonical build path must equal a direct _construct call with the
    # frozen seeds (reconstruction provenance).
    field = GF2mField.create(1024)
    manifest, matrices = cb.build_nbldpc_v6_codebook()
    for m in (320, 480):
        seed = manifest["ordered_entries"][0 if m == 320 else 1]["construction_seed"]
        direct, degrees, parallel, cycles = cb._matrix_cached(m, seed)
        assert tuple(tuple(int(x) for x in row) for row in direct) == matrices[m]
        assert parallel == 0 and cycles == manifest["ordered_entries"][0 if m == 320 else 1]["cycle_count"]
        assert sum(degrees) == 2 * 1024
