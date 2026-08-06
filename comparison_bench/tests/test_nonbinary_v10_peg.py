"""V10 PEG codebook tests (additive; V10-30 engineering scope, T0/T1).

Covers node-view count conversion, check degree counts, socket consistency,
GF(1024) rank on small matrices, deterministic PEG identity (same seed -> same
graph), parallel-edge detection, exact degree sequences, full-rank small
constructions, nonzero edge labels, the frozen-failure trial cap, and the
parameter-only construction manifest (no self-hash / source-hash).
"""
from __future__ import annotations

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_peg as peg
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField

FIELD1024 = GF2mField.create(1024)


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


def _regular_config(n: int, m: int):
    """Regular (3, 6) config: n variables of degree 3, m = n/2 checks of
    degree 6 (socket-consistent by construction)."""
    lam = {3: 1.0}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    assert rho == {6: 1.0}
    return lam, rho, n, m


# --------------------------------------------------------------------------- #
# T0: degree counts and socket consistency
# --------------------------------------------------------------------------- #


def test_node_view_counts_sum_to_n():
    counts = peg.node_view_counts({2: 0.5, 3: 0.5}, 100)
    assert sum(counts.values()) == 100
    assert counts[2] == 60 and counts[3] == 40   # L_2 = 0.6, L_3 = 0.4
    counts5 = peg.node_view_counts({2: 0.5, 3: 0.5}, 5)
    assert sum(counts5.values()) == 5
    assert counts5[2] == 3 and counts5[3] == 2


def test_check_degree_counts_sum_to_m():
    conc = common.concentrated_check_distribution(0.5, {2: 0.5, 3: 0.5})
    rho = _rho_from_concentrated(conc)
    counts = peg.check_degree_counts(rho, 100)
    assert sum(counts.values()) == 100
    assert set(counts) == {4, 5}
    with pytest.raises(ValueError):
        peg.check_degree_counts({4: 0.5}, 100)      # weights must sum to 1
    with pytest.raises(ValueError):
        peg.check_degree_counts({1: 1.0}, 100)      # degree 1 check rejected


def test_socket_consistency():
    total = peg.socket_consistency({2: 60, 3: 40}, {4: 40, 8: 10})
    assert total == 240
    with pytest.raises(ValueError):
        peg.socket_consistency({2: 60, 3: 40}, {4: 40, 8: 11})


# --------------------------------------------------------------------------- #
# T0: GF(1024) rank on small matrices
# --------------------------------------------------------------------------- #


def test_rank_GF1024_small():
    assert peg.rank_GF1024(FIELD1024, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 3
    assert peg.rank_GF1024(FIELD1024, [[1, 1], [1, 1]]) == 1
    assert peg.rank_GF1024(FIELD1024, [[1, 1, 0], [0, 1, 1], [0, 0, 0]]) == 2
    # Full-rank 3x3 over GF(1024) (verified by elimination; the naive
    # [[1,2,3],[3,2,1],[0,1,1]] is rank 2 over GF(1024): row2 = 774*row0 + 258*row1).
    assert peg.rank_GF1024(FIELD1024, [[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == 3
    assert peg.rank_GF1024(FIELD1024, []) == 0
    with pytest.raises(ValueError):
        peg.rank_GF1024(object(), [[1, 0], [0, 1]])


def test_sparse_to_dense_and_syndrome_round_trip():
    triples = [(0, 0, 1), (0, 1, 3), (1, 1, 7), (1, 2, 255)]
    dense = peg.sparse_to_dense(triples, 3, 2, FIELD1024)
    assert dense.shape == (2, 3)
    assert int(dense[0, 0]) == 1 and int(dense[1, 2]) == 255
    with pytest.raises(ValueError):
        peg.sparse_to_dense([(0, 0, 1), (0, 0, 2)], 3, 2, FIELD1024)  # duplicate
    with pytest.raises(ValueError):
        peg.sparse_to_dense([(0, 0, 0)], 3, 2, FIELD1024)  # zero coefficient
    result = peg.syndrome_round_trip(FIELD1024, dense.tolist(), seed=2026100300, n_samples=5)
    assert result["round_trip_ok"] is True
    assert result["checked"] == 5


# --------------------------------------------------------------------------- #
# T1: deterministic PEG construction
# --------------------------------------------------------------------------- #


def test_peg_determinism_same_seed_same_graph():
    lam, rho, n, m = _regular_config(12, 6)
    first = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    second = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    assert first["status"] == "ok"
    assert first["triples"] == second["triples"]
    third = peg.peg_construct(n, m, lam, rho, seed=2026100301, max_trials=10)
    assert first["triples"] != third["triples"]


def test_peg_no_parallel_edges_and_degree_sequences():
    from collections import Counter
    lam, rho, n, m = _regular_config(12, 6)
    construction = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    assert construction["status"] == "ok"
    assert construction["parallel_edges"] == 0
    var_counts = common.edge_to_node_hist(lam)
    expected_var_degrees = {int(d): round(float(var_counts[d]) * n) for d in var_counts}
    var_degree = {variable: 0 for variable in range(n)}
    check_degree = {check: 0 for check in range(m)}
    seen: set[tuple[int, int]] = set()
    for row, col, coeff in construction["triples"]:
        var_degree[col] += 1
        check_degree[row] += 1
        assert (row, col) not in seen
        seen.add((row, col))
    assert dict(Counter(var_degree.values())) == {int(d): int(c) for d, c in expected_var_degrees.items()}
    assert sum(var_degree.values()) == construction["total_sockets"]
    assert sum(check_degree.values()) == construction["total_sockets"]
    assert all(degree == expected for degree, expected in zip(
        sorted(check_degree.values(), reverse=True),
        sorted(construction["check_counts"].values(), reverse=True)))


def test_peg_full_rank_small():
    lam, rho, n, m = _regular_config(12, 6)
    construction = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    assert construction["status"] == "ok"
    assert construction["rank"] == m


def test_peg_edge_labels_nonzero():
    lam, rho, n, m = _regular_config(12, 6)
    construction = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    for _, _, coeff in construction["triples"]:
        assert 1 <= coeff <= 1023
        assert FIELD1024.mul(coeff, 1) == coeff  # valid nonzero field symbol
    assert construction["edge_label_seed"] == common.v10_seed("peg_labels:2026100300")


def test_peg_irregular_variable_degrees():
    lam = {2: 0.4, 3: 0.4, 5: 0.2}   # max variable degree 5 <= m=5 (feasible)
    conc = common.concentrated_check_distribution(0.5, lam)
    rho = _rho_from_concentrated(conc)
    n, m = 10, 5
    counts = peg.node_view_counts(lam, n)
    check_counts = peg.check_degree_counts(rho, m)
    var_sockets = sum(int(d) * int(c) for d, c in counts.items())
    check_sockets = sum(int(d) * int(c) for d, c in check_counts.items())
    if var_sockets != check_sockets:
        pytest.skip("rounded counts not socket-consistent for this size")
    construction = peg.peg_construct(n, m, lam, rho, seed=2026100302, max_trials=10)
    assert construction["status"] == "ok"
    assert construction["parallel_edges"] == 0
    assert construction["total_sockets"] == var_sockets


def test_peg_trial_cap_frozen_failure():
    """Two variables of degree 2 but a single degree-4 check: after the first
    edge to the only check, parallel edges are forbidden and no candidate
    remains -> frozen failure after max_trials."""
    lam = {2: 1.0}
    rho = {4: 1.0}
    construction = peg.peg_construct(2, 1, lam, rho, seed=2026100303, max_trials=3)
    assert construction["status"] == "frozen_failure"
    assert construction["trials_used"] == 3
    assert construction["triples"] == []


def test_peg_manifest_parameter_only():
    """Manifest carries schema, status and construction parameters only; no
    self-hash / source-hash fields."""
    lam, rho, n, m = _regular_config(12, 6)
    construction = peg.peg_construct(n, m, lam, rho, seed=2026100300, max_trials=10)
    manifest = peg.peg_manifest(construction)
    assert manifest["schema"] == "v10_peg_manifest_v1"
    assert manifest["status"] == "ok"
    # construction parameters and status fields
    assert manifest["n"] == n and manifest["m"] == m
    assert manifest["seed"] == 2026100300
    assert manifest["edge_label_seed"] == common.v10_seed("peg_labels:2026100300")
    assert manifest["max_trials"] == 10
    assert manifest["trials_used"] == construction["trials_used"]
    assert manifest["rank"] == m
    assert manifest["parallel_edges"] == 0
    assert manifest["total_sockets"] == construction["total_sockets"]
    assert manifest["var_counts"] == construction["var_counts"]
    assert manifest["check_counts"] == construction["check_counts"]
    assert manifest["triples_count"] == len(construction["triples"])
    # no hash fields in the parameter-only manifest
    assert "self_hash" not in manifest
    assert "source_hash" not in manifest
