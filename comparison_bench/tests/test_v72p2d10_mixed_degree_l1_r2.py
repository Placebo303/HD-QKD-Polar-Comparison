"""R2 focused tests: connectivity-first builder + admission A1–A6 (R202–R208).

Fake/tiny only: the production decoder is never imported, no scientific L1
call is made and no root outside pytest tmp paths is created. Entry-boundary
tests inject fake decoders and count their calls (must stay zero).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as d10  # noqa: E402
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d5_gf32_rate_mother as d5)

runner = _load_module("v72p2d10_runner_r2_test", RUNNER_PATH)


def _fake_graph(arm, width, seed):
    cell = d10.degree_cell(arm, width)
    n, m = cell["n"], cell["m"]
    H = np.zeros((m, n), dtype=np.int64)
    for variable in range(n):
        H[variable % m, variable] = 1
    if arm == "PEG_DV3_MATCHED":
        # Control marker: extra edges so the fake decoder can tell the
        # arms apart by edge count (structure stays None; never admitted
        # through the real admission path).
        rng = np.random.default_rng(int(seed) + 7919)
        while int(np.count_nonzero(H)) < n + 40:
            H[int(rng.integers(0, m)), int(rng.integers(0, n))] = 1
    return {"arm": arm, "width": int(width), "graph_seed": int(seed),
            "n": n, "m": m, "E": int(np.count_nonzero(H)), "edges": [],
            "coefficients": [], "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


def _zero_syndrome(H, x):
    return np.zeros(H.shape[0], dtype=np.uint8)


class _Result:
    def __init__(self, x_hat, syndrome_ok):
        self.x_hat = np.asarray(x_hat, dtype=np.uint8)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = 1
        self.status = "converged_exact"
        self.belief_provenance = "FAKE"


# --------------------------------------------------------------------------- #
# R206/R202 retirement guards
# --------------------------------------------------------------------------- #
def test_r2_no_source_auth_or_replacement_mechanism():
    assert not hasattr(d10, "BATCH_AUTHORIZED")
    assert not hasattr(d10, "PROFILE_REPLACEMENT_SEEDS")
    args = runner.build_parser().parse_args([])
    assert args.execution_authorized is False
    assert args.batch is False


def test_r2_frozen_tables_and_seeds_exact():
    assert d10.degree_cell("PEG_DV3_MATCHED", 64) == {
        "n": 64, "m": 59, "var_counts": {3: 64},
        "check_counts": {3: 44, 4: 15}, "E": 192}
    assert d10.degree_cell("PEG_DV3_MATCHED", 128)["E"] == 384
    assert d10.degree_cell("PEG_DV3_MATCHED", 256)["E"] == 768
    assert d10.degree_cell("PEG_DV23_LAM2_045", 64) == {
        "n": 64, "m": 59, "var_counts": {3: 29, 2: 35},
        "check_counts": {3: 39, 2: 20}, "E": 157}
    assert d10.degree_cell("PEG_DV23_LAM2_045", 128)["E"] == 313
    assert d10.degree_cell("PEG_DV23_LAM2_045", 256)["E"] == 627
    for (arm, width), cell in sorted(d10.DEGREE_TABLE.items()):
        frozen = d10.degree_cell(arm, width)
        assert frozen["E"] == 2 * frozen["var_counts"].get(2, 0) \
            + 3 * frozen["var_counts"].get(3, 0) \
            + 4 * frozen["var_counts"].get(4, 0)
        assert cell["m"] == {64: 59, 128: 118, 256: 236}[width]
    assert d10.GRAPH_SEEDS == {
        64: (2026092201, 2026092202, 2026092203),
        128: (2026092204, 2026092205, 2026092206),
        256: (2026092207, 2026092208, 2026092209)}
    assert d10.BLOCK_SEEDS == {
        64: tuple(range(2026092301, 2026092309)),
        128: tuple(range(2026092311, 2026092319)),
        256: tuple(range(2026092321, 2026092329))}
    graph_seeds = {s for seeds in d10.GRAPH_SEEDS.values() for s in seeds}
    block_seeds = {s for seeds in d10.BLOCK_SEEDS.values() for s in seeds}
    assert len(graph_seeds) == 9 and graph_seeds.isdisjoint(block_seeds)


# --------------------------------------------------------------------------- #
# R202: one constructor + tie policy shared by both arms
# --------------------------------------------------------------------------- #
def test_r2_both_arms_share_one_constructor(monkeypatch):
    calls = []
    original = d10.build_degree_sequence_peg

    def spy(n, m, var_counts, check_counts, seed, field=None):
        calls.append((dict(var_counts), dict(check_counts), seed))
        return original(n, m, var_counts, check_counts, seed, field)

    monkeypatch.setattr(d10, "build_degree_sequence_peg", spy)
    dv3 = d10.build_graph("PEG_DV3_MATCHED", 64, 2026092201)
    mix = d10.build_graph("PEG_DV23_LAM2_045", 64, 2026092201)
    assert dv3["status"] == "ok" and mix["status"] == "ok"
    # construction + replay per graph, identical seed routed to one builder.
    assert len(calls) == 4
    assert all(seed == 2026092201 for _, _, seed in calls)
    assert calls[0][0] == {3: 64} and calls[2][0] == {3: 29, 2: 35}
    assert dv3["edges"] != mix["edges"]  # only the degree sequence differs


def test_r2_determinism_same_seed_identical_output():
    first = d10.build_graph("PEG_DV23_LAM2_045", 128, 2026092205)
    again = d10.build_graph("PEG_DV23_LAM2_045", 128, 2026092205)
    assert first["edges"] == again["edges"]
    assert first["coefficients"] == again["coefficients"]
    assert np.array_equal(first["dense"], again["dense"])
    assert first["structure"]["admission"] == again["structure"]["admission"]


def test_r2_no_parallel_edges_all_frozen_cells():
    for width in d10.WIDTHS:
        for arm in d10.ARMS:
            for seed in d10.GRAPH_SEEDS[width]:
                graph = d10.build_graph(arm, width, seed)
                assert graph["status"] == "ok"
                assert len(set(graph["edges"])) == len(graph["edges"])
                assert len(graph["edges"]) == graph["E"]


# --------------------------------------------------------------------------- #
# R203/R204 primitives
# --------------------------------------------------------------------------- #
def test_r2_gf32_arithmetic_spot_checks():
    for value in range(1, 32):
        assert d10._gf32_mul_raw(value, d10._gf32_inv(value)) == 1
    assert d10._gf32_mul_raw(0, 17) == 0
    assert d10.gf32_row_rank(np.eye(4, dtype=np.int64)) == 4
    assert d10.gf32_row_rank(np.zeros((3, 5), dtype=np.int64)) == 0
    assert d10.structural_rank(2, 2, [(0, 0), (1, 1)]) == 2
    assert d10.structural_rank(2, 3, [(0, 0), (1, 1)]) == 2


def test_r2_ranks_match_oracle_on_all_18_cells():
    for width in d10.WIDTHS:
        for arm in d10.ARMS:
            cell = d10.degree_cell(arm, width)
            for seed in d10.GRAPH_SEEDS[width]:
                graph = d10.build_graph(arm, width, seed)
                dense = np.asarray(graph["dense"])
                assert graph["structure"]["structural_rank"] == cell["m"]
                assert graph["structure"]["gf32_rank"] == cell["m"]
                assert int(d5._gf32_rank(dense)) == cell["m"]
                assert graph["structure"]["rank"] == cell["m"]


# --------------------------------------------------------------------------- #
# R205: each admission predicate rejects its deliberate violator
# --------------------------------------------------------------------------- #
def test_r2_a1_rejects_degree_and_socket_mismatch():
    dense = np.array([[1, 2], [3, 5]], dtype=np.int64)
    bad_var = d10.structural_record(dense, {3: 2}, {2: 2})
    assert bad_var["admission"]["A1_exact_degrees_socket_balance"] is False
    assert bad_var["admitted"] is False
    bad_check = d10.structural_record(dense, {2: 2}, {3: 2})
    assert bad_check["admission"]["A1_exact_degrees_socket_balance"] is False


def test_r2_a2_rejects_empty_check_and_min_degree():
    dense = np.array([[1, 2], [0, 0]], dtype=np.int64)
    structure = d10.structural_record(dense, {1: 2}, {2: 1})
    assert structure["empty_checks"] == 1
    assert structure["admission"]["A2_simple_graph_min_degree"] is False
    assert structure["admitted"] is False


def test_r2_a3_rejects_disconnected_graph():
    dense = np.zeros((4, 4), dtype=np.int64)
    dense[0, 0] = dense[0, 1] = dense[1, 0] = dense[1, 1] = 1
    dense[2, 2] = dense[2, 3] = dense[3, 2] = dense[3, 3] = 2
    structure = d10.structural_record(dense, {2: 4}, {2: 4})
    assert structure["connected_components"] == 2
    assert structure["admission"]["A1_exact_degrees_socket_balance"] is True
    assert structure["admission"]["A2_simple_graph_min_degree"] is True
    assert structure["admission"]["A3_single_component"] is False
    assert structure["admitted"] is False


def test_r2_a4_rejects_structural_rank_deficiency():
    # Checks 0 and 1 both see only variable 0: at most 2 of 3 checks match.
    dense = np.array([[1, 0, 0], [2, 0, 0], [0, 3, 4]], dtype=np.int64)
    assert d10.structural_rank(3, 3, [(0, 0), (0, 1), (1, 2), (2, 2)]) == 2
    structure = d10.structural_record(dense, {2: 1, 1: 2}, {2: 1, 1: 2})
    assert structure["admission"]["A4_structural_rank_m"] is False
    assert structure["admitted"] is False


def test_r2_a5_rejects_gf32_rank_deficiency():
    # Complete skeleton (structural rank 2) but proportional rows over GF32.
    dense = np.array([[1, 2], [2, 4]], dtype=np.int64)
    assert d10.structural_rank(2, 2, [(0, 0), (1, 0), (0, 1), (1, 1)]) == 2
    assert d10.gf32_row_rank(dense) == 1
    structure = d10.structural_record(dense, {2: 2}, {2: 2})
    assert structure["admission"]["A4_structural_rank_m"] is True
    assert structure["admission"]["A5_gf32_rank_m"] is False
    assert structure["admitted"] is False


def test_r2_a6_replay_holds_on_frozen_cell():
    graph = d10.build_graph("PEG_DV3_MATCHED", 64, 2026092201)
    assert graph["structure"]["admission"]["A6_deterministic_replay"] is True
    assert graph["admitted"] is True


def test_r2_all_18_cells_pass_a1_to_a6():
    report = d10.profile_graphs()
    assert len(report["graphs"]) == 18
    assert report["seed_replacements"] == []
    assert report["replacement_seeds_used"] == 0
    assert report["frozen_seed_failures"] == []
    for entry in report["graphs"]:
        assert entry["status"] == "ok" and entry["admitted"] is True
        assert entry["connected_components"] == 1
        assert entry["largest_component_fraction"] == 1.0
        cell = d10.degree_cell(entry["arm"], entry["width"])
        assert entry["structural_rank"] == cell["m"]
        assert entry["gf32_rank"] == cell["m"]
        assert len(entry["admission"]) == 6
        assert all(entry["admission"].values())


# --------------------------------------------------------------------------- #
# R206/R207: unauthorized refusal + fail-closed verify (fake decoders only)
# --------------------------------------------------------------------------- #
def test_r2_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    out = tmp_path / "must_not_exist"
    rc = runner.main(["--batch", "--out-root", str(out)])
    assert rc == 2
    assert not out.exists()
    assert "comparison_bench.formal_ir.v35_algorithm_development" \
        not in sys.modules


def test_r2_nonadmitted_graph_fails_before_fake_decoder():
    cell = d10.degree_cell("PEG_DV23_LAM2_045", 64)
    blocked = {"arm": "PEG_DV23_LAM2_045", "width": 64,
               "graph_seed": 2026092201, "n": cell["n"], "m": cell["m"],
               "E": 0, "edges": [], "coefficients": [], "dense": None,
               "structure": None, "status": "construction_failed",
               "admitted": False, "failure_reason": "A3_single_component"}
    calls = []

    def fake_decode(*_args, **_kwargs):
        calls.append(1)
        n = cell["n"]
        return _Result(np.zeros(n), True)

    block = {"u1": np.zeros(cell["n"], dtype=np.int64),
             "prior": np.full((cell["n"], 32), 1.0 / 32)}
    entry = {"call_idx": 0, "width": 64, "arm": "PEG_DV23_LAM2_045",
             "graph_seed": 2026092201, "block_seed": 2026092301}
    with pytest.raises(d10.StructureNotAdmitted):
        d10.dispatch_l1(blocked, block, entry, fake_decode, _zero_syndrome,
                        call_idx=0)
    assert calls == []
    outcome = d10.execute_plan(
        [e for e in d10.build_call_plan()
         if e["width"] == 64 and e["graph_seed"] == 2026092201
         and e["block_seed"] == 2026092301],
        {("PEG_DV23_LAM2_045", 64, 2026092201): blocked},
        {64: {2026092301: block}}, fake_decode, _zero_syndrome)
    assert calls == []
    assert outcome["terminal"] == d10.T_ENGINEERING_BLOCKED


def _run_fake_batch(tmp_path, name="root"):
    def fake_prior(_root=None):
        pb = np.full(4, 0.25)
        pf = np.full((32 * 32, 4), 1.0 / (32 * 32))
        return pb, pf, np.full((32, 4), 1.0 / 32)

    def fake_sample(_p_b, _p_f, n, seed):
        rng = np.random.default_rng(int(seed))
        return {"bob": rng.integers(0, 4, size=int(n)),
                "u1": np.zeros(int(n), dtype=np.int64)}

    def fake_decode(H, prior, syn, max_iter=None, damping_alpha=None,
                    warm_beliefs=None, field=None):
        # Control fake carries n+40 edges vs n on the candidate: stay quiet
        # on control, exact zeros on the candidate so the fake batch
        # routes POSITIVE.
        n = H.shape[1]
        if int(np.count_nonzero(H)) > n + 20:
            return _Result(np.full(n, 1), False)
        return _Result(np.zeros(n), True)

    out = tmp_path / name
    summary = runner.run_l1_batch(
        str(out), "ignored-model-f", fake_decode, _zero_syndrome,
        build_graph_fn=_fake_graph, load_prior_fn=fake_prior,
        sample_fn=fake_sample)
    assert summary["terminal"] == d10.T_CANDIDATE_REPRODUCIBLE
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is True
    return out


def test_r2_verify_fail_closed_on_nonadmitted_graph(tmp_path):
    import csv
    out = _run_fake_batch(tmp_path)
    path = out / "graph_records.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows and rows[0]["admitted"] == "True"
    rows[0]["admitted"] = "False"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False


def test_r2_verify_fail_closed_on_engineering_blocked_width(tmp_path):
    out = _run_fake_batch(tmp_path, name="root_blocked")
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text("utf-8"))
    summary["width_results"][1]["engineering_reason"] = "decoder crash X"
    summary["width_results"][1]["classification"] = d10.ENGINEERING_BLOCKED
    summary["terminal"] = d10.T_ENGINEERING_BLOCKED
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    assert runner.verify_root(str(out), build_graph_fn=_fake_graph) is False
