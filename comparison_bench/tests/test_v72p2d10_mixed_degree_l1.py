"""Focused tests for the D10 mixed-degree L1 discriminator (F06-F08).

Fake/tiny only: the production decoder is never imported by the batch module,
no scientific L1 call is made and no root outside the task-owned pytest
basetemp is created. The production decoder entrypoints are treated as
forbidden (`_boom`); the runner's `--batch` path stays unauthorized.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d10_mixed_degree_l1.py")
RUNNER_PATH = (ROOT / "scripts"
               / "v72p2d10_mixed_degree_l1_development.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as d10  # noqa: E402

runner = _load_module("v72p2d10_runner_test", RUNNER_PATH)
assert Path(d10.__file__).resolve() == MODULE_PATH

PRODUCTION_DECODER = "comparison_bench.formal_ir.v35_algorithm_development"


def _boom(*_args, **_kwargs):
    raise AssertionError("production path must not be entered")


def _fake_prior(_root=None):
    """Tiny synthetic Model-F-shaped prior pair (no file read)."""
    pb = np.full(4, 0.25)
    pf = np.full((32 * 32, 4), 1.0 / (32 * 32))
    p1 = np.full((32, 4), 1.0 / 32)
    return pb, pf, p1


def _fake_sample(_p_b, _p_f, n, seed):
    rng = np.random.default_rng(int(seed))
    bob = rng.integers(0, 4, size=int(n))
    u1 = np.zeros(int(n), dtype=np.int64)
    return {"bob": bob, "alice": u1 * 32, "u1": u1,
            "u2": np.zeros(int(n), dtype=np.int64)}


def _fake_graph(arm, width, seed):
    """Correct-shape admitted fake graph; DV3 carries a degree-4 marker row."""
    cell = d10.degree_cell(arm, width)
    n, m = cell["n"], cell["m"]
    rng = np.random.default_rng(int(seed) % (2 ** 31))
    H = np.zeros((m, n), dtype=np.int64)
    for variable in range(n):
        if arm == "PEG_DV3_MATCHED":
            row = 0 if variable < 4 else 1 + (variable % (m - 1))
        else:
            row = variable % m
        H[row, variable] = 1 + int(rng.integers(0, 31))
    return {"arm": arm, "width": int(width), "graph_seed": int(seed),
            "n": n, "m": m, "E": int(np.count_nonzero(H)), "edges": [],
            "coefficients": [], "dense": H, "structure": None, "status": "ok",
            "admitted": True, "failure_reason": ""}


class _Result:
    def __init__(self, x_hat, syndrome_ok, iterations, status, provenance):
        self.x_hat = np.asarray(x_hat, dtype=np.uint8)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = int(iterations)
        self.status = status
        self.belief_provenance = provenance


def _fake_decode_dv3_quiet(H, prior, syn, max_iter=None, damping_alpha=None,
                           warm_beliefs=None, field=None):
    """Control arm: Syndrome-invalid max-iter result; candidate: exact zeros."""
    del prior, syn, damping_alpha, warm_beliefs, field
    n = H.shape[1]
    is_dv3 = any(int((H[row] != 0).sum()) >= 4 for row in range(H.shape[0]))
    if is_dv3:
        return _Result(np.full(n, 1), False, int(max_iter), "max_iter",
                       "PRIOR_ONLY")
    return _Result(np.zeros(n), True, 2, "converged_exact", "CHECK_UPDATED")


def _fake_decode_mix_stops_at_128(H, prior, syn, max_iter=None,
                                  damping_alpha=None, warm_beliefs=None,
                                  field=None):
    """Candidate positive at n64, negative from n128; control always quiet."""
    n = H.shape[1]
    is_dv3 = any(int((H[row] != 0).sum()) >= 4 for row in range(H.shape[0]))
    if is_dv3:
        return _Result(np.full(n, 1), False, int(max_iter), "max_iter",
                       "PRIOR_ONLY")
    if n >= 128:
        return _Result(np.zeros(n), False, int(max_iter), "max_iter",
                       "CHECK_UPDATED")
    return _Result(np.zeros(n), True, 1, "converged_exact", "CHECK_UPDATED")


def _zero_syndrome(H, x):
    return np.zeros(H.shape[0], dtype=np.uint8)


def _counts(exact, syndrome, blocks=8):
    return [{"graph_seed": 0, "blocks": blocks, "exact": exact[i],
             "syndrome": syndrome[i]} for i in range(len(exact))]


def _run_fake_batch(tmp_path, decode_fn, name="root"):
    out = tmp_path / name
    return runner.run_l1_batch(
        str(out), "ignored-model-f", decode_fn, _zero_syndrome,
        build_graph_fn=_fake_graph, load_prior_fn=_fake_prior,
        sample_fn=_fake_sample)


# --------------------------------------------------------------------------- #
# T0 frozen constants / exact future command
# --------------------------------------------------------------------------- #
def test_t0_frozen_constants_and_command():
    assert d10.Q == 32 and d10.POLY == 37
    assert d10.MODEL_F_INPUT_ROOT == "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d10.FUTURE_ROOT == (
        "workspace/d10_mixed_degree_l1_"
        "b2dd13e4-6600-4e27-90df-5c9038cf2c34")
    assert not hasattr(d10, "BATCH_AUTHORIZED")
    assert not hasattr(d10, "PROFILE_REPLACEMENT_SEEDS")
    assert d10.ARMS == ("PEG_DV3_MATCHED", "PEG_DV23_LAM2_045")
    assert d10.WIDTHS == (64, 128, 256)
    assert d10.GRAPH_SEEDS == {
        64: (2026092201, 2026092202, 2026092203),
        128: (2026092204, 2026092205, 2026092206),
        256: (2026092207, 2026092208, 2026092209)}
    assert d10.BLOCK_SEEDS == {
        64: tuple(range(2026092301, 2026092309)),
        128: tuple(range(2026092311, 2026092319)),
        256: tuple(range(2026092321, 2026092329))}
    assert d10.DECODER_MAX_ITER == 90 and d10.DAMPING_ALPHA == 1.0
    assert d10.SCIENTIFIC_CALL_CEILING == 144
    assert d10.SETUP_CALL_CEILING == 44 and d10.SETUP_FIXED_UNITS == 2
    assert d10.WALL_BUDGET_S == 1800.0 and d10.PER_CALL_BUDGET_S == 120.0
    assert d10.RSS_BUDGET_BYTES == 2 * 1024 ** 3
    assert tuple(d10.TERMINALS) == (
        "D10_L1_CANDIDATE_REPRODUCIBLE", "D10_L1_FINITE_SIZE_SIGNAL",
        "D10_L1_NO_MATERIAL_ADVANTAGE", "D10_L1_AMBIGUOUS",
        "D10_L1_ENGINEERING_BLOCKED", "D10_L1_NOT_RUN")
    assert runner.EVIDENCE_FILES == (
        "manifest.json", "l1_records.csv", "graph_records.csv",
        "arm_summary.csv", "summary.json", "command_log.txt")
    assert runner.FROZEN_COMMAND == d10.FROZEN_COMMAND
    assert runner.FROZEN_COMMAND == (
        ".venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py "
        "--batch --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 "
        "--out-root workspace/d10_mixed_degree_l1_"
        "b2dd13e4-6600-4e27-90df-5c9038cf2c34")
    parser = runner.build_parser()
    args = parser.parse_args([])
    assert args.batch is False and args.verify is False
    assert args.profile_only is False
    assert args.execution_authorized is False
    assert args.model_f_root == d10.MODEL_F_INPUT_ROOT
    assert args.out_root is None


def test_frozen_degree_tables_exact():
    assert d10.degree_cell("PEG_DV3_MATCHED", 64) == {
        "n": 64, "m": 59, "var_counts": {3: 64},
        "check_counts": {3: 44, 4: 15}, "E": 192}
    assert d10.degree_cell("PEG_DV3_MATCHED", 128)["check_counts"] == \
        {3: 88, 4: 30}
    assert d10.degree_cell("PEG_DV3_MATCHED", 256)["check_counts"] == \
        {3: 176, 4: 60}
    assert d10.degree_cell("PEG_DV23_LAM2_045", 64) == {
        "n": 64, "m": 59, "var_counts": {3: 29, 2: 35},
        "check_counts": {3: 39, 2: 20}, "E": 157}
    assert d10.degree_cell("PEG_DV23_LAM2_045", 128)["var_counts"] == \
        {3: 57, 2: 71}
    assert d10.degree_cell("PEG_DV23_LAM2_045", 128)["check_counts"] == \
        {3: 77, 2: 41}
    assert d10.degree_cell("PEG_DV23_LAM2_045", 256) == {
        "n": 256, "m": 236, "var_counts": {3: 115, 2: 141},
        "check_counts": {3: 155, 2: 81}, "E": 627}


# --------------------------------------------------------------------------- #
# builder: exact degrees, determinism, variation, fail-loud
# --------------------------------------------------------------------------- #
def test_builder_exact_degrees_socket_balance_and_gates():
    for width in d10.WIDTHS:
        for arm in d10.ARMS:
            cell = d10.degree_cell(arm, width)
            graph = d10.build_graph(arm, width, d10.GRAPH_SEEDS[width][0])
            assert graph["status"] == "ok" and graph["admitted"] is True
            assert graph["E"] == cell["E"]
            edges = graph["edges"]
            assert edges == sorted(edges)
            assert len(set(edges)) == len(edges) == cell["E"]
            structure = graph["structure"]
            assert structure["variable_degree_histogram"] == \
                dict(sorted(cell["var_counts"].items()))
            assert structure["check_degree_histogram"] == \
                dict(sorted(cell["check_counts"].items()))
            assert structure["var_sockets"] == structure["check_sockets"] == \
                cell["E"]
            assert structure["duplicate_edges"] == 0
            assert structure["empty_checks"] == 0
            assert structure["min_check_degree"] == \
                min(cell["check_counts"])
            assert structure["rank"] <= cell["m"] and structure["rank"] >= 0
            assert structure["four_cycles"] >= 0
            # R2 connectivity-first PEG avoids short cycles aggressively;
            # girth stays an even reported diagnostic, never a gate.
            assert structure["girth"] in (None, 4, 6, 8, 10, 12)
            assert all(structure["gates"].values())
            assert graph["dense"].shape == (cell["m"], cell["n"])
            assert np.count_nonzero(graph["dense"]) == cell["E"]


def test_builder_determinism_and_multi_graph_variation():
    first = d10.build_graph("PEG_DV23_LAM2_045", 64, 2026092201)
    again = d10.build_graph("PEG_DV23_LAM2_045", 64, 2026092201)
    assert first["edges"] == again["edges"]
    assert first["coefficients"] == again["coefficients"]
    assert np.array_equal(first["dense"], again["dense"])
    other = d10.build_graph("PEG_DV23_LAM2_045", 64, 2026092202)
    assert other["edges"] != first["edges"]
    assert other["coefficients"] != first["coefficients"]


def test_builder_tiny_exact_sequence():
    graph = d10.build_degree_sequence_peg(
        6, 4, {3: 2, 2: 4}, {4: 2, 3: 2}, 7)
    assert graph["status"] == "ok"
    degrees = {}
    for variable, _check in graph["edges"]:
        degrees[variable] = degrees.get(variable, 0) + 1
    assert degrees == {0: 3, 1: 3, 2: 2, 3: 2, 4: 2, 5: 2}
    assert len(graph["edges"]) == 2 * 3 + 4 * 2 == 14


@pytest.mark.parametrize("var,chk", [
    ({2: 2, 3: 2}, {3: 3}),          # socket mismatch
    ({2: 2, 3: 3}, {3: 5}),          # count sum / socket mismatch
    ({1: 4}, {2: 2}),                # degree < 2
    ({2: 4}, {2: 4, 0: 1}),          # zero count
    ({2: -4}, {2: 4}),               # negative count
])
def test_builder_infeasible_fails_loud(var, chk):
    with pytest.raises(ValueError):
        d10.build_degree_sequence_peg(4, 2, var, chk, 11)


def test_builder_construction_failure_retained():
    # 3 degree-3 variables over 2 checks: socket-balanced but dead-ends
    # (a variable needing 3 sockets sees only 2 checks).
    graph = d10.build_degree_sequence_peg(3, 2, {3: 3}, {5: 1, 4: 1}, 13)
    assert graph["status"] == "construction_failed"
    assert graph["edges"] == []
    assert "no eligible check" in graph["failure_reason"]


# --------------------------------------------------------------------------- #
# seeds and coefficients
# --------------------------------------------------------------------------- #
def test_seed_separation_namespaces():
    graph_seeds = {s for width in d10.WIDTHS for s in d10.GRAPH_SEEDS[width]}
    block_seeds = {s for width in d10.WIDTHS for s in d10.BLOCK_SEEDS[width]}
    assert graph_seeds.isdisjoint(block_seeds)
    from comparison_bench.formal_ir import nonbinary_v10_common as common
    assert d10.coefficient_seed(64, 2026092201) == \
        common.v10_seed("d10:coeff:64:2026092201")
    assert d10.coefficient_seed(64, 2026092201) != \
        d10.coefficient_seed(64, 2026092202)
    assert d10.coefficient_seed(64, 2026092201) != \
        d10.coefficient_seed(128, 2026092201)
    assert d10.coefficient_seed(64, 2026092201) != \
        common.v10_seed("peg_tie:2026092201:v:0:s:0")


def test_coefficient_rule_range_and_same_rule_both_arms():
    edges = [(v, c) for v in range(30) for c in (v % 7, (v + 1) % 7)]
    edges = sorted(set(edges))
    first = d10.coefficients_for_edges(edges, 64, 2026092201)
    second = d10.coefficients_for_edges(edges, 64, 2026092201)
    assert first == second
    assert all(1 <= value <= 31 for value in first)
    assert len(set(first)) > 3
    mixed = d10.build_graph("PEG_DV23_LAM2_045", 256, 2026092207)
    dv3 = d10.build_graph("PEG_DV3_MATCHED", 256, 2026092207)
    assert all(1 <= value <= 31 for value in mixed["coefficients"])
    assert len(set(mixed["coefficients"])) > 8
    assert mixed["coefficients"] != dv3["coefficients"]


# --------------------------------------------------------------------------- #
# structural diagnostics
# --------------------------------------------------------------------------- #
def test_structural_record_tiny_four_cycle_girth_rank():
    # Acyclic degree-2 chain over 3 checks: G5 fails (degree-1 checks) because
    # every check must keep degree >= 2; metrics are reported, not repaired.
    path = np.array([[1, 0], [2, 3], [0, 5]], dtype=np.int64)
    structure = d10.structural_record(path, {2: 2}, {1: 2, 2: 1})
    assert structure["four_cycles"] == 0
    assert structure["girth"] is None
    assert structure["girth_reason"] == "acyclic"
    assert structure["rank"] == 2
    assert structure["connected_components"] == 1
    assert structure["largest_component_fraction"] == 1.0
    assert structure["degree2"]["is_forest_feasible"] is True
    assert structure["gates"]["G5_no_empty_check_min_degree"] is False
    # R205: A4 fails (3 checks cannot match into 2 variables), so the
    # graph is not admitted even though A1/A2 hold for this tiny cell.
    assert structure["admission"]["A4_structural_rank_m"] is False
    assert structure["admitted"] is False
    # Complete 2x2: one 4-cycle, girth 4, N2 > m-1 reported, never repaired.
    four = np.array([[1, 2], [3, 5]], dtype=np.int64)
    structure = d10.structural_record(four, {2: 2}, {2: 2})
    assert structure["four_cycles"] == 1
    assert structure["girth"] == 4
    assert structure["rank"] == 2
    assert structure["connected_components"] == 1
    assert structure["largest_component_fraction"] == 1.0
    assert structure["degree2"]["is_forest_feasible"] is False
    assert structure["degree2"]["cycle_rank_lower_bound"] == 1
    # R205: G6 stays a retained measurement (False here) but no longer
    # gates; A1–A5 all pass (full structural and GF32 rank), so admitted.
    assert structure["admission"]["A5_gf32_rank_m"] is True
    assert structure["admitted"] is True


def test_structural_record_gate_failures_reported_not_repaired():
    dense = np.array([[1, 2], [3, 5]], dtype=np.int64)
    structure = d10.structural_record(dense, {3: 2}, {2: 2})
    assert structure["gates"]["G1_variable_degree_histogram"] is False
    assert structure["admitted"] is False
    empty_check = np.array([[1, 2], [0, 0]], dtype=np.int64)
    structure = d10.structural_record(empty_check, {1: 2}, {2: 1})
    assert structure["gates"]["G5_no_empty_check_min_degree"] is False
    assert structure["gates"]["G6_degree2_forest_feasible"] is True
    assert structure["empty_checks"] == 1


# --------------------------------------------------------------------------- #
# plan / thresholds / progression
# --------------------------------------------------------------------------- #
def test_call_plan_matrix_and_order():
    plan = d10.build_call_plan()
    assert len(plan) == 144
    assert [entry["call_idx"] for entry in plan] == list(range(144))
    per_width = {}
    for entry in plan:
        per_width.setdefault(entry["width"], []).append(entry)
    assert sorted(per_width) == [64, 128, 256]
    assert all(len(entries) == 48 for entries in per_width.values())
    for width, entries in per_width.items():
        arm_order = [e["arm"] for e in entries]
        assert arm_order[:24] == ["PEG_DV3_MATCHED"] * 24
        assert arm_order[24:] == ["PEG_DV23_LAM2_045"] * 24
        for arm in d10.ARMS:
            scoped = [e for e in entries if e["arm"] == arm]
            graph_order = [e["graph_seed"] for e in scoped]
            assert graph_order == sorted(
                list(d10.GRAPH_SEEDS[width]) * len(d10.BLOCK_SEEDS[width]),
                key=lambda s: (list(d10.GRAPH_SEEDS[width]).index(s),))
            assert set(e["block_seed"] for e in scoped) == \
                set(d10.BLOCK_SEEDS[width])
    assert len({(e["width"], e["arm"], e["graph_seed"], e["block_seed"])
                for e in plan}) == 144


def test_classify_width_frozen_thresholds():
    positive_mix = _counts([2, 2, 2], [4, 4, 4])
    quiet_dv3 = _counts([0, 1, 0], [1, 1, 1])
    assert d10.classify_width(positive_mix, quiet_dv3) == d10.POSITIVE
    assert d10.classify_width(_counts([0, 0, 0], [1, 1, 1]),
                              quiet_dv3) == d10.NEGATIVE
    assert d10.classify_width(_counts([0, 0, 0], [2, 2, 1]),
                              quiet_dv3) == d10.AMBIGUOUS
    pooled_only = _counts([0, 0, 0], [2, 8, 8])
    assert d10.classify_width(pooled_only, quiet_dv3) == d10.AMBIGUOUS
    single_rescue = _counts([4, 0, 0], [8, 8, 8])
    assert d10.classify_width(single_rescue, quiet_dv3) == d10.AMBIGUOUS
    confounded = _counts([2, 2, 2], [4, 4, 4])
    assert d10.classify_width(
        confounded, _counts([0, 0, 1], [1, 1, 2])) == d10.AMBIGUOUS
    assert d10.classify_width(
        positive_mix, quiet_dv3,
        engineering_reason="decoder crash") == d10.ENGINEERING_BLOCKED


def test_terminal_routing_frozen():
    def result(width, classification):
        return {"width": width, "classification": classification}
    assert d10.route_terminal([]) == d10.T_NOT_RUN
    assert d10.route_terminal(
        [result(64, d10.NEGATIVE)]) == d10.T_NO_MATERIAL_ADVANTAGE
    assert d10.route_terminal(
        [result(64, d10.POSITIVE),
         result(128, d10.NEGATIVE)]) == d10.T_FINITE_SIZE_SIGNAL
    assert d10.route_terminal(
        [result(64, d10.POSITIVE), result(128, d10.POSITIVE),
         result(256, d10.NEGATIVE)]) == d10.T_FINITE_SIZE_SIGNAL
    assert d10.route_terminal(
        [result(64, d10.POSITIVE), result(128, d10.POSITIVE),
         result(256, d10.POSITIVE)]) == d10.T_CANDIDATE_REPRODUCIBLE
    assert d10.route_terminal(
        [result(64, d10.POSITIVE),
         result(128, d10.AMBIGUOUS)]) == d10.T_AMBIGUOUS
    assert d10.route_terminal(
        [result(64, d10.POSITIVE),
         result(128, d10.ENGINEERING_BLOCKED)]) == d10.T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# dispatch boundary / invalid graphs / fake-runner isolation
# --------------------------------------------------------------------------- #
def test_invalid_graph_fails_before_decoder():
    cell = d10.degree_cell("PEG_DV3_MATCHED", 64)
    failed = {
        "arm": "PEG_DV3_MATCHED", "width": 64, "graph_seed": 2026092201,
        "n": cell["n"], "m": cell["m"], "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": "no eligible check placement"}
    calls = []

    def decoder(*_args, **_kwargs):
        calls.append(1)
        return _Result(np.zeros(cell["n"]), True, 1, "converged_exact", "P")

    block = {"u1": np.zeros(cell["n"], dtype=np.int64),
             "prior": np.full((cell["n"], 32), 1.0 / 32)}
    entry = {"call_idx": 0, "width": 64, "arm": "PEG_DV3_MATCHED",
             "graph_seed": 2026092201, "block_seed": 2026092301}
    with pytest.raises(d10.StructureNotAdmitted):
        d10.dispatch_l1(failed, block, entry, decoder, _zero_syndrome,
                        call_idx=0)
    assert calls == []
    with pytest.raises(ValueError):
        d10.dispatch_l1({"arm": "x", "width": 64, "graph_seed": 1,
                         "dense": np.zeros((2, 2)), "admitted": True},
                        block, entry, None, _zero_syndrome, call_idx=0)
    graphs = {("PEG_DV3_MATCHED", 64, 2026092201): failed}
    plan = [e for e in d10.build_call_plan()
            if e["width"] == 64 and e["graph_seed"] == 2026092201
            and e["block_seed"] == 2026092301]
    blocks = {64: {2026092301: block}}
    outcome = d10.execute_plan(plan, graphs, blocks, decoder, _zero_syndrome)
    assert calls == []
    assert outcome["terminal"] == d10.T_ENGINEERING_BLOCKED
    assert outcome["width_results"][0]["classification"] == \
        d10.ENGINEERING_BLOCKED


def test_no_production_decoder_entry(tmp_path):
    assert PRODUCTION_DECODER not in sys.modules
    assert "v35_algorithm_development" not in {
        name.split(".")[-1] for name in sys.modules}
    code = (
        "import sys; sys.path.insert(0, %r);"
        "import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as m;"
        "assert %r not in sys.modules;"
        "import importlib.util;"
        "spec = importlib.util.spec_from_file_location('r', %r);"
        "mod = importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(mod);"
        "assert %r not in sys.modules;"
        "rc = mod.main(['--batch', '--out-root', %r]);"
        "assert rc == 2;"
        "assert %r not in sys.modules;"
        "print('ISOLATED')" % (str(SRC), PRODUCTION_DECODER, str(RUNNER_PATH),
                               PRODUCTION_DECODER,
                               str(tmp_path / "never_created"),
                               PRODUCTION_DECODER)
    )
    completed = subprocess.run([sys.executable, "-c", code],
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    assert "ISOLATED" in completed.stdout
    assert not (tmp_path / "never_created").exists()
    with pytest.raises(TypeError):
        runner.run_l1_batch(str(tmp_path / "x"), "m")  # decoder not injected


# --------------------------------------------------------------------------- #
# paired execution, records, root writing and read-only verify
# --------------------------------------------------------------------------- #
def test_execute_plan_paired_blocks_exact_syndrome_separation(tmp_path):
    width = 64
    graph_seed = d10.GRAPH_SEEDS[width][0]
    block_seeds = d10.BLOCK_SEEDS[width][:2]
    graphs = {(arm, width, graph_seed):
              d10.build_graph(arm, width, graph_seed) for arm in d10.ARMS}
    p_b, p_f, p1 = _fake_prior()
    blocks = {width: runner.prepare_blocks(p_b, p_f, p1, width, block_seeds,
                                          sample_fn=_fake_sample)}
    plan = [e for e in d10.build_call_plan()
            if e["width"] == width and e["graph_seed"] == graph_seed
            and e["block_seed"] in block_seeds]
    assert len(plan) == 2 * len(block_seeds)
    seen = []

    def decoder(H, prior, syn, max_iter=None, damping_alpha=None,
                warm_beliefs=None, field=None):
        is_dv3 = any(int((H[row] != 0).sum()) >= 4 for row in range(H.shape[0]))
        seen.append((H.shape, bool(is_dv3)))
        n = H.shape[1]
        if is_dv3:
            # syndrome-valid but wrong codeword: exact must stay False.
            return _Result((np.arange(n) % 31 + 2), True, 7, "converged_exact",
                           "CHECK_UPDATED")
        return _Result(np.zeros(n), False, 90, "max_iter", "CHECK_UPDATED")

    def syndrome(H, x):
        # Depends on x so the residual syndrome weight is informative.
        return ((np.asarray(x, dtype=np.int64)[:H.shape[0]]
                 + np.arange(H.shape[0], dtype=np.int64)) % 31
                + 1).astype(np.uint8)

    outcome = d10.execute_plan(plan, graphs, blocks, decoder, syndrome)
    records = outcome["records"]
    assert [r["arm"] for r in records[:2]] == ["PEG_DV3_MATCHED"] * 2
    assert [r["call_idx"] for r in records] == list(range(len(records)))
    dv3 = [r for r in records if r["arm"] == "PEG_DV3_MATCHED"]
    mix = [r for r in records if r["arm"] == "PEG_DV23_LAM2_045"]
    assert all(r["syndrome_ok"] is True and r["exact"] is False for r in dv3)
    assert all(r["exact"] is False and r["syndrome_ok"] is False for r in mix)
    assert all(r["residual_syndrome_weight"] > 0 for r in dv3)
    assert all(r["residual_syndrome_weight"] == 0 for r in mix)
    assert all(r["iterations"] in (7, 90) for r in records)
    assert all(str(r["belief_provenance"]) == "CHECK_UPDATED"
               for r in records)
    # Paired identical blocks: both arms see the same (block_seed, prior, u1).
    dv3_prior = [r for r in records
                 if r["arm"] == "PEG_DV3_MATCHED"][0]["block_seed"]
    mix_blocks = [r["block_seed"] for r in mix]
    assert mix_blocks == [r["block_seed"] for r in dv3]
    assert dv3_prior in mix_blocks
    assert len(seen) == len(records)


def test_fake_runner_full_batch_root_and_verify(tmp_path, monkeypatch):
    monkeypatch.setattr(d10, "build_graph", _boom)
    summary = _run_fake_batch(tmp_path, _fake_decode_dv3_quiet)
    assert summary["terminal"] == d10.T_CANDIDATE_REPRODUCIBLE
    assert summary["scientific_l1_calls"] == 144
    assert summary["setup_calls"] == 44
    assert summary["planned_l1_calls"] == 144
    root = tmp_path / "root"
    assert sorted(p.name for p in root.iterdir()) == sorted(
        runner.EVIDENCE_FILES)
    manifest = json.loads((root / "manifest.json").read_text("utf-8"))
    assert manifest["l1_only"] is True
    assert manifest["budgets"]["retry"] is False
    assert manifest["budgets"]["resume"] is False
    assert manifest["budgets"]["seed_search"] is False
    assert manifest["budgets"]["adaptive_stop"] is False
    assert manifest["authorization"] == d10.AUTHORIZATION
    assert runner.verify_root(str(root), build_graph_fn=_fake_graph) is True

    records_path = root / "l1_records.csv"
    original = records_path.read_text("utf-8")
    records_path.write_text(original.replace(",2,converged_exact", ",999,"
                                             "converged_exact", 1),
                            encoding="utf-8")
    assert runner.verify_root(str(root), build_graph_fn=_fake_graph) is False
    records_path.write_text(original, encoding="utf-8")

    lines = original.splitlines()
    records_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    assert runner.verify_root(str(root), build_graph_fn=_fake_graph) is False
    records_path.write_text(original, encoding="utf-8")
    assert runner.verify_root(str(root), build_graph_fn=_fake_graph) is True


def test_execute_plan_progression_stops_on_negative():
    graphs = {}
    for width in (64, 128):
        for arm in d10.ARMS:
            for seed in d10.GRAPH_SEEDS[width]:
                graphs[(arm, width, seed)] = _fake_graph(arm, width, seed)
    p_b, p_f, p1 = _fake_prior()
    blocks = {width: runner.prepare_blocks(
        p_b, p_f, p1, width, d10.BLOCK_SEEDS[width],
        sample_fn=_fake_sample)
        for width in (64, 128)}
    outcome = d10.execute_plan(d10.build_call_plan(), graphs, blocks,
                               _fake_decode_mix_stops_at_128, _zero_syndrome)
    assert [r["width"] for r in outcome["width_results"]] == [64, 128]
    assert [r["classification"] for r in outcome["width_results"]] == \
        [d10.POSITIVE, d10.NEGATIVE]
    assert outcome["terminal"] == d10.T_FINITE_SIZE_SIGNAL
    assert len(outcome["records"]) == 96


# --------------------------------------------------------------------------- #
# profile seed-replacement clause / root refusal
# --------------------------------------------------------------------------- #
def test_profile_replacement_clause_retired():
    # R2 retires replacement: a frozen construction failure is retained
    # as-is with zero replacement seeds consumed and no new seed entering
    # the 18-cell profile.
    failing_seed = d10.GRAPH_SEEDS[64][0]

    def builder(arm, width, seed):
        if width == 64 and arm == "PEG_DV3_MATCHED" and seed == failing_seed:
            return {"arm": arm, "width": width, "graph_seed": seed,
                    "n": 64, "m": 59, "E": 0, "edges": [], "coefficients": [],
                    "dense": None, "structure": None,
                    "status": "construction_failed", "admitted": False,
                    "failure_reason": "no eligible check placement"}
        return _fake_graph(arm, width, seed)

    report = d10.profile_graphs(build_fn=builder)
    assert len(report["graphs"]) == 18
    assert report["seed_replacements"] == []
    assert report["replacement_seeds_used"] == 0
    assert len(report["frozen_seed_failures"]) == 1
    assert report["frozen_seed_failures"][0]["seed"] == failing_seed
    retained = [e for e in report["graphs"]
                if e["seed"] == failing_seed
                and e["arm"] == "PEG_DV3_MATCHED" and e["width"] == 64]
    assert len(retained) == 1 and retained[0]["admitted"] is False
    assert all(e["seed"] in d10.GRAPH_SEEDS[e["width"]]
               for e in report["graphs"])


def test_frozen_profile_all_18_graphs_admit():
    report = d10.profile_graphs()
    assert len(report["graphs"]) == 18
    assert report["seed_replacements"] == []
    assert report["frozen_seed_failures"] == []
    assert all(entry["admitted"] for entry in report["graphs"])


def test_fresh_root_and_protected_root_refusal(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        d10.refuse_out_root(str(existing))
    with pytest.raises(ValueError):
        d10.refuse_out_root("workspace/v72p2d9_never_write_here")
    with pytest.raises(ValueError):
        d10.refuse_out_root("results/never_write_here")
    with pytest.raises(ValueError):
        d10.refuse_out_root("comparison_bench/outputs_comparison/never")
    assert d10.refuse_out_root(str(tmp_path / "fresh")) == \
        (tmp_path / "fresh").resolve()
