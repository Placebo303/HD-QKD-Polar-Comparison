"""P0-P4 equivalence + regression gates for perf-v38-triage-test-cost.

Lane: PYTHONPATH=comparison_bench/src (same as test_v38_architecture_triage.py).
All seeds/inputs are TEST-ONLY and synthetic; no production outputs are touched.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.formal_ir import v38_architecture_triage as v38_module
from comparison_bench.formal_ir import v35_algorithm_development as v35_module
from comparison_bench.formal_ir.v35_algorithm_development import GF2mField
from comparison_bench.formal_ir.v38_architecture_triage import (
    CycleInfo,
    _enumerate_cycles_uncached,
    compute_gf32_rank,
    enumerate_canonical_simple_cycles,
    evaluate_single_block,
    get_canonical_support_edges,
)

TEST_SEED = 938701


@pytest.fixture(scope="session")
def v38_session_fields():
    """P1 session field cache: parsed field mappings keyed by
    (dataset_id_or_path, header_fingerprint); discarded at session teardown."""
    cache: dict[tuple[str, str], dict] = {}

    def _fingerprint_v31() -> str:
        mats = v35_module.load_v31_qc_baseline_matrices()
        return ",".join(f"{k}:{v.shape[0]}x{v.shape[1]}" for k, v in sorted(mats.items()))

    cache[("v31", _fingerprint_v31())] = {
        "field": GF2mField.create(32),
        "matrices": v35_module.load_v31_qc_baseline_matrices(),
    }

    yield cache
    cache.clear()


def test_p1_session_field_cache_hit_and_fingerprint_key(v38_session_fields):
    mats = v35_module.load_v31_qc_baseline_matrices()
    fp = ",".join(f"{k}:{v.shape[0]}x{v.shape[1]}" for k, v in sorted(mats.items()))
    first = v38_session_fields[("v31", fp)]
    second = v38_session_fields[("v31", fp)]
    assert first is second
    assert ("v31", "other-fingerprint") not in v38_session_fields


def _tiny_payload(path: Path) -> None:
    doc = {
        "packets": [
            {
                "packet_id": "m1_16_n1024_n1024|QC-cyclic-projective",
                "matrices": {
                    "L2": {
                        "1M": [[1, 0, 1, 0], [0, 1, 1, 1]],
                        "1p5M": [[1, 1, 0, 0], [0, 1, 0, 1]],
                        "2M": [[1, 0, 0, 1], [1, 1, 1, 0]],
                    }
                },
            }
        ]
    }
    path.write_text(json.dumps(doc), encoding="utf-8")


def test_p1_load_v31_stat_key_hit_miss_and_normalization(tmp_path):
    v35_module.load_v31_qc_baseline_matrices_cache_clear()
    f = tmp_path / "mats.json"
    _tiny_payload(f)
    info0 = v35_module._load_v31_payload_cached.cache_info()
    a = v35_module.load_v31_qc_baseline_matrices(f)
    b = v35_module.load_v31_qc_baseline_matrices(str(f.resolve()))
    c = v35_module.load_v31_qc_baseline_matrices(Path(str(f)))
    info1 = v35_module._load_v31_payload_cached.cache_info()
    assert a["1M"].shape == (2, 4)
    assert all(np.array_equal(a[k], b[k]) and np.array_equal(a[k], c[k]) for k in a)
    assert info1.misses - info0.misses == 1  # relative/absolute/str hit one entry
    assert info1.hits - info0.hits == 2
    # stat change (content rewrite) must miss
    _tiny_payload(f)
    f.write_bytes(f.read_bytes() + b" ")
    d = v35_module.load_v31_qc_baseline_matrices(f)
    info2 = v35_module._load_v31_payload_cached.cache_info()
    assert info2.misses - info1.misses == 1
    assert all(np.array_equal(a[k], d[k]) for k in a)
    # failures are never cached
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        v35_module.load_v31_qc_baseline_matrices(missing)
    with pytest.raises(FileNotFoundError):
        v35_module.load_v31_qc_baseline_matrices(missing)
    info3 = v35_module._load_v31_payload_cached.cache_info()
    assert info3.misses == info2.misses


def test_p1_load_v31_mutation_isolation_and_parse_once(tmp_path):
    v35_module.load_v31_qc_baseline_matrices_cache_clear()
    f = tmp_path / "mats.json"
    _tiny_payload(f)
    a = v35_module.load_v31_qc_baseline_matrices(f)
    a["1M"][0, 0] ^= 1
    b = v35_module.load_v31_qc_baseline_matrices(f)
    assert b["1M"][0, 0] == 1  # caller mutation never pollutes the cache
    for _ in range(5):
        v35_module.load_v31_qc_baseline_matrices(f)
    info = v35_module._load_v31_payload_cached.cache_info()
    assert info.misses == 1  # one JSON parse for N loads (fixture setup dedup)


def test_p1_default_v31_shapes_unchanged():
    mats = v35_module.load_v31_qc_baseline_matrices()
    assert {k: tuple(v.shape) for k, v in mats.items()} == {
        "1M": (184, 1024), "1p5M": (190, 1024), "2M": (192, 1024),
    }
    assert all(v.dtype == np.uint8 for v in mats.values())


def _small_supports():
    h4 = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]], dtype=np.uint8)
    rng = np.random.Generator(np.random.PCG64(TEST_SEED))
    h = np.zeros((24, 64), dtype=np.uint8)
    for c in range(64):
        rows = rng.choice(24, size=2, replace=False)
        h[rows, c] = 1
    return [("empty", np.zeros((3, 4), dtype=np.uint8)),
            ("single", np.array([[5]], dtype=np.uint8)),
            ("four_cycle", h4),
            ("skeleton_24x64", h)]


def test_p0_support_edges_match_direct_and_hit():
    v38_module.v38_support_caches_clear()
    for name, h in _small_supports():
        rows, cols = np.nonzero(h)
        expected = sorted((int(r), int(c)) for r, c in zip(rows, cols))
        assert get_canonical_support_edges(h) == expected
    info0 = v38_module._support_edges_cached.cache_info()
    for _, h in _small_supports():
        get_canonical_support_edges(h)
    info1 = v38_module._support_edges_cached.cache_info()
    assert info1.hits - info0.hits == len(_small_supports())
    assert info1.misses == info0.misses


def test_p0_cycles_match_uncached_and_containers_are_copies():
    v38_module.v38_support_caches_clear()
    for name, h in _small_supports():
        mask = (np.asarray(h) != 0)
        ref = _enumerate_cycles_uncached(mask)
        got = enumerate_canonical_simple_cycles(h)
        assert [list(x) for x in ref[:3]] == [list(x) for x in got[:3]]
        assert {e: list(v) for e, v in ref[3]} == got[3]
    # mutating returned containers must not pollute the cache
    _, h = _small_supports()[2]
    first = enumerate_canonical_simple_cycles(h)
    first[0].append(CycleInfo(length=4, checks=(0, 1), vars=(0, 1),
                              edges=((0, 0), (1, 0), (1, 1), (0, 1))))
    first[3][(0, 0)].append(999)
    second = enumerate_canonical_simple_cycles(h)
    assert len(second[0]) == len(first[0]) - 1
    assert 999 not in second[3][(0, 0)]


def test_p0_different_supports_do_not_pollute():
    v38_module.v38_support_caches_clear()
    a = np.array([[1, 1], [1, 1]], dtype=np.uint8)
    b = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    ra = enumerate_canonical_simple_cycles(a)
    rb = enumerate_canonical_simple_cycles(b)
    assert len(ra[0]) == 1 and len(rb[0]) == 0
    assert enumerate_canonical_simple_cycles(a)[0] == ra[0]


def test_p2_rank_equality_gate_random_and_boundary():
    field = GF2mField.create(32)
    loop = v35_module._compute_gf32_rank_loop
    tiny = v35_module._compute_gf32_rank_tiny
    vec = v35_module._compute_gf32_rank_vectorized
    cases = [
        np.zeros((0, 5), dtype=np.uint8),
        np.zeros((3, 0), dtype=np.uint8),
        np.array([[0]], dtype=np.uint8),
        np.array([[31]], dtype=np.uint8),
        np.array([[1, 2, 0], [0, 3, 4], [5, 0, 6]], dtype=np.uint8),
        np.array([[1, 2, 3], [1, 2, 3]], dtype=np.uint8),  # all-tie rows
        np.zeros((4, 4), dtype=np.uint8),
        np.eye(6, dtype=np.uint8),
        np.triu(np.ones((5, 5), dtype=np.uint8)),
        np.tril(np.ones((5, 5), dtype=np.uint8)),
    ]
    rng = np.random.Generator(np.random.PCG64(TEST_SEED))
    for _ in range(120):
        m = int(rng.integers(1, 9))
        n = int(rng.integers(1, 9))
        cases.append(rng.integers(0, 32, size=(m, n)).astype(np.uint8))
    cases.append(rng.integers(0, 32, size=(40, 40)).astype(np.uint8))
    cases.append(rng.integers(0, 2, size=(96, 256)).astype(np.uint8))  # sparse binary
    for i, h in enumerate(cases):
        got = [fn(h, field) for fn in (compute_gf32_rank, loop, tiny, vec)]
        assert all(type(v) is int for v in got), i
        assert got[0] == got[1] == got[2] == got[3], (i, h.shape, got)


def test_p3_fake_shortcircuit_keeps_semantics():
    alice = np.tile(np.array([1, 34, 547, 996], dtype=np.int64), 256)
    bob = np.tile(np.array([32, 321, 1023, 64], dtype=np.int64), 256)
    u2a = (alice & 31).astype(np.uint8)
    u2b = (bob & 31).astype(np.uint8)
    expected_initial = int(np.sum(u2a != u2b))
    assert expected_initial > 10  # guarantees non-success fake outcome below
    real_sample = v38_module.sample_empirical_block
    v38_module.sample_empirical_block = lambda counts, seed, size: (
        np.arange(1024, dtype=np.int64), alice, bob)
    try:
        rec = evaluate_single_block(
            np.zeros((184, 1024), dtype=np.uint8), source="1M", block_seed=360101,
            lane="lane_test", construction_seed=TEST_SEED,
            counts=np.ones((1024, 1024), dtype=np.float64), fake_runner=True)
    finally:
        v38_module.sample_empirical_block = real_sample
    # R4 row: raw count keeps real sampled value (not a placeholder), status non-ok
    assert isinstance(rec["errors_initial"], int) and rec["errors_initial"] == expected_initial
    assert isinstance(rec["errors_final"], int)
    assert rec["errors_final"] == expected_initial - 10
    assert rec["status"] == "max_iter" and rec["status"] != "ok"
    assert rec["syndrome_ok"] is False and rec["exact_l2"] is False
    assert set(rec) == {"source", "block_seed", "lane", "construction_seed", "matrix_id",
                        "errors_initial", "errors_final", "exact_l2", "syndrome_ok",
                        "iterations", "status", "runtime_s"}


def test_p4_slow_mark_registered_and_shards_collect():
    ini = Path("pytest.ini").read_text(encoding="utf-8")
    assert "slow:" in ini  # mark registered; default lane = -m "not slow"
    env = dict(os.environ, PYTHONPATH=str(Path("comparison_bench/src").resolve()))
    base = [sys.executable, "-m", "pytest",
            "comparison_bench/tests/test_v38_architecture_triage.py",
            "--collect-only", "-q", "-p", "no:cacheprovider"]
    out_slow = subprocess.run(base + ["-m", "slow"], capture_output=True, text=True,
                              check=True, env=env).stdout
    out_fast = subprocess.run(base + ["-m", "not slow"], capture_output=True, text=True,
                              check=True, env=env).stdout
    n_slow = sum(1 for line in out_slow.splitlines() if "::" in line)
    n_fast = sum(1 for line in out_fast.splitlines() if "::" in line)
    assert (n_slow, n_fast) == (5, 33)
