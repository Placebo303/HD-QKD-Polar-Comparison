from __future__ import annotations
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5a_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v3 as v3

def test_frozen_identity_and_exact_v3_row_reuse():
    manifest, matrices = cb.build_nbldpc_v5a_codebook()
    assert manifest["canonical_schema"] == "NBLDPC5A" and manifest["q"] == 1024 and manifest["n"] == 64
    assert manifest["s6"] == [0, 3, 6, 7, 6, 0, 0, 0] and manifest["salt"] == 0
    assert manifest["v3_manifest_id"] == v3.build_nbldpc_v3_codebook()[0]["manifest_id"]
    _, v3_matrices = v3.build_nbldpc_v3_codebook()
    assert tuple(matrices[48]) == tuple(v3_matrices[48])  # rows 0..47 are the exact v3 rows
    assert list(matrices.keys()) == [32, 40, 48, 56]
    assert cb.verify_nbldpc_v5a_codebook(manifest, matrices)["status"] == "ok"

def test_canonical_determinism_and_cached_container():
    m1, mats1 = cb.build_nbldpc_v5a_codebook()
    m2, mats2 = cb.build_nbldpc_v5a_codebook()
    assert m1 == m2 and mats1 == mats2
    manifest, matrices = cb.codebook()
    assert manifest == m1 and matrices == mats1

def test_search_never_runs_after_freeze(monkeypatch):
    def trap(*args, **kwargs):
        raise AssertionError("search must not run after freeze")
    monkeypatch.setattr(cb, "_find_s6", trap)
    monkeypatch.setattr(cb, "_find_salt", trap)
    manifest, matrices = cb.build_nbldpc_v5a_codebook()
    assert manifest["s6"] == [0, 3, 6, 7, 6, 0, 0, 0]
    assert cb.verify_nbldpc_v5a_codebook(manifest, matrices)["status"] == "ok"

def test_structural_contract_of_every_prefix():
    manifest, matrices = cb.build_nbldpc_v5a_codebook()
    for c in (32, 40, 48, 56):
        rows = matrices[c]
        assert len(rows) == c and all(len(row) == 64 for row in rows)
        assert all(0 < int(x) < 1024 or int(x) == 0 for row in rows for x in row)
        assert max(sum(1 for x in row if x) for row in rows) <= 8
        assert min(sum(1 for row in rows if row[col]) for col in range(64)) >= 2
    entry = {e["check_count"]: e for e in manifest["ordered_entries"]}
    for c in (32, 40, 48, 56):
        assert entry[c]["rank"] == c and entry[c]["cycle_count"] == 0 and entry[c]["pair_proxy_passed"]

def test_verifier_rejects_foreign_matrix():
    manifest, matrices = cb.build_nbldpc_v5a_codebook()
    _, v3_matrices = v3.build_nbldpc_v3_codebook()
    wrong = dict(matrices); wrong[56] = v3_matrices[48] + matrices[56][:8]
    assert cb.verify_nbldpc_v5a_codebook(manifest, wrong)["status"] == "codebook_invalid"
    forged = dict(manifest); forged["s6"] = [1, 0, 0, 0, 0, 0, 0, 0]
    assert cb.verify_nbldpc_v5a_codebook(forged, matrices)["status"] == "codebook_invalid"
