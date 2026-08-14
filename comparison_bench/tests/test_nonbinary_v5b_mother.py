from __future__ import annotations
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5b_mother as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v3 as v3

def test_frozen_identity_and_frozen_search_values():
    manifest, matrices = cb.build_nbldpc_v5b_codebook()
    assert manifest["canonical_schema"] == "NBLDPC5B" and manifest["q"] == 1024 and manifest["n"] == 64
    assert manifest["accepted_salt"] == 0
    assert manifest["w2_collisions"] == 0 and manifest["w3_collisions"] == 0
    assert manifest["base_masks"] == [[0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 6, 7], [0, 1, 4, 5, 6, 7],
                                      [0, 2, 4, 6], [1, 3, 5, 7], [0, 1, 2, 3, 4, 5], [0, 2, 4, 6]]
    assert len(manifest["shifts"]) == 7 and all(len(s) == 8 for s in manifest["shifts"])
    assert list(matrices.keys()) == [32, 40, 48, 56]
    assert cb.verify_nbldpc_v5b_codebook(manifest, matrices)["status"] == "ok"

def test_canonical_determinism_and_cached_container():
    m1, mats1 = cb.build_nbldpc_v5b_codebook()
    m2, mats2 = cb.build_nbldpc_v5b_codebook()
    assert m1 == m2 and mats1 == mats2
    manifest, matrices = cb.codebook()
    assert manifest == m1 and matrices == mats1

def test_search_never_runs_after_freeze(monkeypatch):
    def trap(*args, **kwargs):
        raise AssertionError("search must not run after freeze")
    monkeypatch.setattr(cb, "_find_shifts", trap)
    monkeypatch.setattr(cb, "_find_candidates", trap)
    manifest, matrices = cb.build_nbldpc_v5b_codebook()
    assert manifest["accepted_salt"] == 0
    assert cb.verify_nbldpc_v5b_codebook(manifest, matrices)["status"] == "ok"

def test_structural_contract_of_every_prefix():
    manifest, matrices = cb.build_nbldpc_v5b_codebook()
    for c in (32, 40, 48, 56):
        rows = matrices[c]
        assert len(rows) == c and all(len(row) == 64 for row in rows)
        assert all(0 < int(x) < 1024 or int(x) == 0 for row in rows for x in row)
        assert max(sum(1 for x in row if x) for row in rows) <= 8
        assert min(sum(1 for row in rows if row[col]) for col in range(64)) >= 2
    entry = {e["check_count"]: e for e in manifest["ordered_entries"]}
    for c in (32, 40, 48, 56):
        assert entry[c]["rank"] == c and entry[c]["cycle_count"] == 0 and entry[c]["pair_proxy_passed"]

def test_proxy_scores_reconstruct_and_verifier_rejects_foreign_matrix():
    manifest, matrices = cb.build_nbldpc_v5b_codebook()
    mother = matrices[56]
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
    field = GF2mField.create(1024)
    assert cb._w2_collisions(mother, field) == 0
    assert cb._w3_collisions(mother, field) == 0
    wrong = dict(matrices); wrong[56] = matrices[56][:48] + v3.build_nbldpc_v3_codebook()[1][48][:8]
    assert cb.verify_nbldpc_v5b_codebook(manifest, wrong)["status"] == "codebook_invalid"
    forged = dict(manifest); forged["shifts"] = [[1] + [0] * 7] + manifest["shifts"][1:]
    assert cb.verify_nbldpc_v5b_codebook(forged, matrices)["status"] == "codebook_invalid"
