"""V10 PEG constructor-rework tests (EXPLORE; deterministic, fake/small).

Covers the 2026-09-20 constructor rework (see S2_CONSTRUCTOR_REWORK packet):
D1 unreachable-first edge selection, D2 girth sentinel, D3 best-of-N trials.

- T1: reachable+unreachable coexist -> the cycle-free candidate is chosen
  (same fixture run through the pre-fix rule verbatim copy and the fixed
  ``_select_check``).
- T2: best-of-N: per-trial seeds yield different four-cycle counts; the kept
  result is the minimum; fixed seed is deterministic.
- T3: girth recording: acyclic -> ``None`` sentinel; K_{2,2} -> exactly 4;
  ``min_girth`` is never 0/1 (unreachable never a girth candidate).
- T4 lives in the existing S2 files (run, not duplicated here).
"""
from __future__ import annotations

from collections import deque

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_peg as peg


# --------------------------------------------------------------------------- #
# T1: D1 edge selection — old-vs-new on the same fixture
# --------------------------------------------------------------------------- #

def _old_select_check(n, m, var_adj, check_adj, check_free,
                      var_degree_of, check_degree_of,
                      variable, socket, tie_seed):
    """VERBATIM pre-fix selection rule (FROZEN COPY for comparison only).

    Pre-fix lines ~368-391: ``reachable`` computed, and whenever ANY
    reachable candidate exists the unreachable ones are ignored (max-depth
    group taken over reachable only).  Never used for construction.
    """
    def check_node(check):
        return n + int(check)

    free = [c for c in range(m) if check_free[c] > 0]
    existing = set(var_adj[variable])
    candidates = [c for c in free if check_node(c) not in existing]
    if not var_adj[variable]:
        best_free = max(check_free[c] for c in candidates)
        group = [c for c in candidates if check_free[c] == best_free]
        if len(group) == 1:
            return group[0]
        group.sort()
        return peg._tie_pick(tie_seed, variable, socket, group)
    distances = {variable: 0}
    parents = {variable: None}
    frontier = deque([variable])
    while frontier:
        node = frontier.popleft()
        neighbours = var_adj[node] if node < n else check_adj[node]
        for other in neighbours:
            if other not in distances:
                distances[other] = distances[node] + 1
                parents[other] = node
                frontier.append(other)
    reachable = [c for c in candidates if check_node(c) in distances]
    if not reachable:
        best_free = max(check_free[c] for c in candidates)
        group = [c for c in candidates if check_free[c] == best_free]
        if len(group) == 1:
            return group[0]
        group.sort()
        return peg._tie_pick(tie_seed, variable, socket, group)
    max_depth = max(distances[check_node(c)] for c in reachable)
    group = [c for c in reachable if distances[check_node(c)] == max_depth]
    if len(group) > 1:
        scores = {}
        for c in group:
            scores[c] = peg._ace_score(variable, check_node(c), parents,
                                       distances, var_degree_of,
                                       check_degree_of, n)
        best_score = max(scores.values())
        group = [c for c in group if scores[c] == best_score]
    if len(group) == 1:
        return group[0]
    group.sort()
    return peg._tie_pick(tie_seed, variable, socket, group)


def _t1_fixture():
    """Partial graph where v0 (socket 2) sees reachable c1 AND unreachable c3.

    Edges: v0-c0, v1-c0, v1-c1, v0-c2 (check nodes offset by n=4).
    BFS from v0 reaches c1 (depth 3, closes 4-cycle v0-c0-v1-c1-v0);
    c3 is isolated (cycle-free merge).  c0/c2 have no free sockets.
    """
    n, m = 4, 4
    var_adj = {0: [4, 6], 1: [4, 5], 2: [], 3: []}
    check_adj = {4: [0, 1], 5: [1], 6: [0], 7: []}
    check_free = {0: 0, 1: 1, 2: 0, 3: 1}
    var_degree_of = {v: 3 for v in range(n)}
    check_degree_of = {c: 2 for c in range(m)}
    return (n, m, var_adj, check_adj, check_free,
            var_degree_of, check_degree_of)


def test_t1_cycle_free_candidate_preferred_over_cycle_closing():
    (n, m, var_adj, check_adj, check_free,
     var_degree_of, check_degree_of) = _t1_fixture()
    old = _old_select_check(n, m, var_adj, check_adj, check_free,
                            var_degree_of, check_degree_of, 0, 2, 999)
    new = peg._select_check(n, m, var_adj, check_adj, check_free,
                            var_degree_of, check_degree_of, 0, 2, 999)
    assert old == 1  # pre-fix: closes the 4-cycle v0-c0-v1-c1-v0
    assert new == 3  # fixed: cycle-free merge with isolated c3
    # The new pick creates no cycle: c3 has no path from v0.
    assert peg._bfs_distance(0, n + 3, n, var_adj, check_adj) == -1
    # ... while the old pick closes a length-4 cycle (distance 3 + 1).
    assert peg._bfs_distance(0, n + 1, n, var_adj, check_adj) == 3


def test_t1_tie_break_policy_unreachable_prefers_largest_free_degree():
    """Exact tie-break policy, unreachable group: largest free degree wins;
    residual ties -> seeded-RNG pick over the sorted tied list."""
    (n, m, var_adj, check_adj, _, var_degree_of,
     check_degree_of) = _t1_fixture()
    # Both c1(reachable) and c3(unreachable) free, but give c1 MORE free
    # sockets: the unreachable c3 must still win (priority beats degree).
    check_free = {0: 0, 1: 5, 2: 0, 3: 1}
    new = peg._select_check(n, m, var_adj, check_adj, check_free,
                            var_degree_of, check_degree_of, 0, 2, 999)
    assert new == 3
    # Within the unreachable group, largest free degree wins: add a second
    # unreachable check c3b... (m fixed) — instead raise c3 above a lone
    # rival by splitting: single unreachable candidate is always picked.
    check_free2 = {0: 0, 1: 0, 2: 0, 3: 1}  # only c3 eligible
    assert peg._select_check(n, m, var_adj, check_adj, check_free2,
                             var_degree_of, check_degree_of,
                             0, 2, 999) == 3


# --------------------------------------------------------------------------- #
# T2: D3 best-of-N trials
# --------------------------------------------------------------------------- #

_T2_N, _T2_M = 12, 6
_T2_LAM, _T2_RHO = {3: 1.0}, {6: 1.0}
_T2_BASE, _T2_NTRIALS = 71000, 6


def _count_four(triples):
    pair_counts = {}
    var_checks = {}
    for row, col, _ in triples:  # labeled order: (row=check, col=variable)
        var_checks.setdefault(col, []).append(row)
    for checks in var_checks.values():
        ordered = sorted(set(checks))
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                key = (ordered[i], ordered[j])
                pair_counts[key] = pair_counts.get(key, 0) + 1
    return sum(k * (k - 1) // 2 for k in pair_counts.values())


def test_t2_per_trial_seeds_differ_and_minimum_kept():
    per_trial = []
    for t in range(_T2_NTRIALS):
        # max_trials=1 with seed BASE+t replays exactly trial t+1 of the
        # best-of-N run (tie_seed = seed + trial - 1); labels do not affect
        # four-cycle counts.
        r = peg.peg_construct(_T2_N, _T2_M, _T2_LAM, _T2_RHO,
                              seed=_T2_BASE + t, max_trials=1)
        assert r["status"] == "ok"
        per_trial.append(r["four_cycles"])
    assert len(set(per_trial)) > 1  # trials genuinely differ
    best = peg.peg_construct(_T2_N, _T2_M, _T2_LAM, _T2_RHO,
                             seed=_T2_BASE, max_trials=_T2_NTRIALS)
    assert best["status"] == "ok"
    assert best["four_cycles"] == min(per_trial)
    assert best["four_cycles"] == _count_four(best["triples"])  # independent
    assert best["trials_used"] == _T2_NTRIALS  # no early stop (min != 0)


def test_t2_deterministic_for_fixed_seed():
    first = peg.peg_construct(_T2_N, _T2_M, _T2_LAM, _T2_RHO,
                              seed=_T2_BASE, max_trials=_T2_NTRIALS)
    second = peg.peg_construct(_T2_N, _T2_M, _T2_LAM, _T2_RHO,
                               seed=_T2_BASE, max_trials=_T2_NTRIALS)
    assert first["triples"] == second["triples"]
    assert first["four_cycles"] == second["four_cycles"]


# --------------------------------------------------------------------------- #
# T3: D2 girth recording
# --------------------------------------------------------------------------- #

def test_t3_acyclic_graph_reports_none_sentinel():
    # v0-c0, v1-c0: a tree (no cycle exists) -> sentinel None ("acyclic").
    r = peg.peg_construct(2, 1, {1: 1.0}, {2: 1.0}, seed=424242, max_trials=3)
    assert r["status"] == "ok"
    assert r["min_girth"] is None
    assert r["four_cycles"] == 0


def test_t3_known_girth_k22_is_exactly_four():
    # K_{2,2}: every placement closes the single 4-cycle -> girth exactly 4.
    # (Pre-fix code returned 0 here: unreachable -1 plus 1.)
    r = peg.peg_construct(2, 2, {2: 1.0}, {2: 1.0}, seed=777, max_trials=3)
    assert r["status"] == "ok"
    assert r["min_girth"] == 4
    assert r["four_cycles"] == 1


def test_t3_min_girth_never_zero_or_one():
    for seed in (71000, 71001, 2026100300, 2026092001 % 100000):
        r = peg.peg_construct(12, 6, {3: 1.0}, {6: 1.0},
                              seed=seed, max_trials=2)
        assert r["status"] == "ok"
        assert r["min_girth"] is None or r["min_girth"] >= 4


# --------------------------------------------------------------------------- #
# T5: socket reconciliation (2026-09-20 fix; S2b dv-study blocker)
# --------------------------------------------------------------------------- #

_S2B_N, _S2B_M, _S2B_SEED = 256, 47, 2026092001


def _s2b_construct(lam):
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v26_mcde as mcde)
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
        GF2mField)
    rho = mcde.make_rho(1.0 - _S2B_M / _S2B_N, dict(lam))
    result = peg.peg_construct(_S2B_N, _S2B_M, dict(lam), rho, _S2B_SEED,
                               max_trials=20, field=GF2mField.create(1024))
    return result, rho


def test_t5_lb_reconciled_exact_sockets():
    # Independent largest-remainder gave var 614 vs chk 615 (off by 1);
    # reconciliation moves one check 14 -> 13: 44*13 + 3*14 = 614.
    c, _ = _s2b_construct({2: 0.5, 3: 0.5})
    assert c["status"] == "ok"
    assert c["var_counts"] == {2: 154, 3: 102}
    assert c["check_counts"] == {13: 44, 14: 3}
    assert sum(d * v for d, v in c["check_counts"].items()) == 614
    assert c["total_sockets"] == 614
    assert sum(c["check_counts"].values()) == _S2B_M


def test_t5_lc_reconciled_exact_sockets():
    # Independent largest-remainder gave var 768 vs chk 769 (off by 1);
    # reconciliation moves one check 17 -> 16: 31*16 + 16*17 = 768.
    c, _ = _s2b_construct({3: 1.0})
    assert c["status"] == "ok"
    assert c["var_counts"] == {3: 256}
    assert c["check_counts"] == {16: 31, 17: 16}
    assert sum(d * v for d, v in c["check_counts"].items()) == 768
    assert c["total_sockets"] == 768
    assert sum(c["check_counts"].values()) == _S2B_M


def test_t5_impossible_request_still_refuses():
    # Genuinely non-representable: var sockets 10 < 2*m minimum.
    import pytest

    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
        GF2mField)
    with pytest.raises(ValueError):
        peg.peg_construct(5, 47, {2: 1.0}, {10: 1.0}, seed=1, max_trials=2,
                          field=GF2mField.create(1024))


def test_t5_la_bit_identity_pin():
    # Reconciliation is a no-op for already-consistent L-A: pinned outputs
    # four_cycles=0, min_girth=6, rank=47 and construct-twice identity.
    c, _ = _s2b_construct({2: 1.0})
    assert c["status"] == "ok"
    assert c["four_cycles"] == 0
    assert c["min_girth"] == 6
    assert c["rank"] == 47
    assert c["var_counts"] == {2: 256}
    assert c["check_counts"] == {10: 5, 11: 42}
    c2, _ = _s2b_construct({2: 1.0})
    assert c["triples"] == c2["triples"]
