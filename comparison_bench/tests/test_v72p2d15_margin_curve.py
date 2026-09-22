"""D15 focused tests: frozen cells/seeds/math, plan, gates, dispatch, refusal.

Fake/tiny only: the production decoder is never imported, no scientific
call is made and no root outside pytest tmp paths or fresh gitignored
``workspace/`` scratch dirs is created. The single real-builder test is
``test_d15_profile_only_36_graphs`` (PROFILE_ONLY, no decoder, no root).
The fake authorized branch runs ``--d15-batch --execution-authorized``
with injected fakes into a scratch root — never the frozen future root,
never the production binder, never the Model-F loader, never the
production decoder (288/288 fakes, 46 setup, six files, verifier PASS).

Process rule: this file must run in a process where the named production
keys are absent at entry — standalone
``pytest -p no:cacheprovider comparison_bench/tests/test_v72p2d15_margin_curve.py``
first, or in a full-suite run where this file sorts before any
v35-importing suite. Every fake-branch test injects ALL adapters
(including the oracle prior and builders), so nothing here imports the
production modules even mid-run.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d15_margin_curve_development.py"
MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d15_margin_curve.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d10_r3_fresh_scaling as r3  # noqa: E402
import comparison_bench.formal_ir.v72p2d11_forward_app as d11  # noqa: E402
import comparison_bench.formal_ir.v72p2d12_finite_l1_degree as d12  # noqa: E402
import comparison_bench.formal_ir.v72p2d14n_calibrated_discriminator as d14n  # noqa: E402
import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5  # noqa: E402
import comparison_bench.formal_ir.v72p2d15_margin_curve as d15  # noqa: E402

runner = _load_module("v72p2d15_runner_test", RUNNER_PATH)

#: Production entries that must never appear on any fake path: the v35
#: decoder module, the Model-F contrast loader module (both registered
#: names), and the R2-runner reuse key (binder-only).
PRODUCTION_ABSENT_KEYS = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "v72p2d10_r2_runner_reuse_d15",
    "v72p2d10_r2_runner_reuse_n14",
    "v72p2d10_r2_runner_reuse_d11",
)

FUTURE_ROOT = (ROOT / d15.FUTURE_ROOT).resolve()


def _assert_no_production_entry():
    absent = [key for key in PRODUCTION_ABSENT_KEYS if key in sys.modules]
    assert absent == [], "production entry on fake path: %r" % (absent,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("d15_fake_authorized_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert path.resolve() != FUTURE_ROOT
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never Model-F content)
# --------------------------------------------------------------------------- #
def _fake_graph(arm, rows, seed):
    m = int(rows)
    H = np.zeros((m, 128), dtype=np.int64)
    for v in range(128):
        H[v % m, v] = 1
    return {"arm": arm, "width": 128, "graph_seed": int(seed),
            "n": 128, "m": m, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "status": "ok", "admitted": True,
            "failure_reason": ""}


def _fake_l1_graph(profile, rows, seed):
    return _fake_graph(profile, rows, seed)


def _fake_l2_graph(rows, seed):
    return _fake_graph(d15.ORACLE_ARM, rows, seed)


def _fake_block(seed):
    n = 128
    return {"bob": np.zeros(n, dtype=np.int64),
            "u1": np.zeros(n, dtype=np.int64),
            "u2": np.zeros(n, dtype=np.int64),
            "prior": np.full((n, 32), 1.0 / 32.0)}


class _FakeResult:
    def __init__(self, n):
        self.x_hat = np.zeros(n, dtype=np.uint8)
        self.syndrome_ok = True
        self.iterations = 1
        self.status = "converged_exact"
        self.belief_provenance = "CHECK_UPDATED"


def _fake_adapters(calls=None, loads=None):
    calls = calls if calls is not None else []
    loads = loads if loads is not None else []

    def fake_decode(H, prior, syn, **kw):
        calls.append(tuple(H.shape))
        return _FakeResult(H.shape[1])

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        loads.append(str(root))
        return (None, None, None)

    def fake_sample(p_b, p_f, p1, seed):
        return _fake_block(seed)

    def fake_oracle(block):
        return block["prior"]

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "sample_fn": fake_sample,
            "oracle_prior_fn": fake_oracle,
            "build_l1_fn": _fake_l1_graph, "build_l2_fn": _fake_l2_graph}


def _fake_graphs_blocks():
    graphs_l1, graphs_l2 = {}, {}
    for profile, rows in d15.CELLS:
        for seed in d15.GRAPH_SEEDS[(profile, int(rows))]:
            if profile in d15.L1_PROFILES:
                graphs_l1[(profile, int(rows),
                           int(seed))] = _fake_l1_graph(
                               profile, rows, seed)
            else:
                graphs_l2[(int(rows), int(seed))] = _fake_l2_graph(
                    rows, seed)
    blocks = {int(s): _fake_block(s) for s in d15.BLOCK_SEEDS}
    return graphs_l1, graphs_l2, blocks


def _tallies(spec):
    """Build D15Tallies from {(arm, rows): [4 per-graph counts]}."""
    return d15.D15Tallies({key: list(vec) for key, vec in spec.items()})


def _full_cells(pool_fn):
    return {(arm, int(m)): pool_fn(arm, int(m))
            for arm, m in [("L045", 110), ("L045", 114), ("L045", 118),
                           ("L055", 110), ("L055", 114), ("L055", 118),
                           (d15.ORACLE_ARM, 83), (d15.ORACLE_ARM, 86),
                           (d15.ORACLE_ARM, 89)]}


def _tagged(arm, rows, graph_seed, block_seed, exact, oracle=False,
            graded=True, syndrome=None, undetected=False):
    layer = "L2" if oracle else "L1"
    return {"call_idx": 0, "point_idx": 1, "layer": layer, "arm": arm,
            "rows": rows, "disclosed_bits": 5 * rows,
            "effective_factor": d15.effective_factor(layer, rows),
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": d15.D15_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome is None else syndrome,
            "source_exact": False, "target_exact": exact if oracle else False,
            "joint_exact": False, "undetected": undetected,
            "oracle": oracle, "graded": graded}


def _full_tagged(spec):
    """Tagged records from {(arm, rows): [4 per-graph exact counts 0..8]}."""
    records = []
    for (arm, rows), vec in spec.items():
        oracle = arm == d15.ORACLE_ARM
        profile = "L2" if oracle else arm
        for seed, total in zip(d15.GRAPH_SEEDS[(profile, int(rows))], vec):
            for i, block in enumerate(d15.BLOCK_SEEDS):
                records.append(_tagged(arm, int(rows), int(seed),
                                       int(block), i < total,
                                       oracle=oracle,
                                       graded=not oracle))
    return records


# --------------------------------------------------------------------------- #
# D1503/frozen tables: nine cells, rate math, seeds, scope guards
# --------------------------------------------------------------------------- #
def test_d15_cells_exact():
    assert d15.degree_cell("L045", 110)["check_counts"] == {2: 17, 3: 93}
    assert d15.degree_cell("L045", 114)["check_counts"] == {2: 29, 3: 85}
    assert d15.degree_cell("L045", 118)["check_counts"] == {2: 41, 3: 77}
    assert d15.degree_cell("L055", 110)["check_counts"] == {2: 29, 3: 81}
    assert d15.degree_cell("L055", 114)["check_counts"] == {2: 41, 3: 73}
    assert d15.degree_cell("L055", 118)["check_counts"] == {2: 53, 3: 65}
    assert d15.degree_cell("L2", 83)["check_counts"] == {4: 31, 5: 52}
    assert d15.degree_cell("L2", 86)["check_counts"] == {4: 46, 5: 40}
    assert d15.degree_cell("L2", 89)["check_counts"] == {4: 61, 5: 28}
    assert d15.degree_cell("L045", 110)["E"] == 313
    assert d15.degree_cell("L055", 110)["E"] == 301
    assert d15.degree_cell("L2", 83)["E"] == 384
    for profile, rows in d15.CELLS:
        cell = d15.degree_cell(profile, rows)
        assert sum(cell["var_counts"].values()) == 128 == cell["n"]
        assert sum(cell["check_counts"].values()) == rows == cell["m"]
        assert cell["E"] == sum(d * c for d, c in
                                cell["var_counts"].items())
        assert cell["E"] == sum(d * c for d, c in
                                cell["check_counts"].items())
        assert cell["E"] == d15.EDGE_TOTALS[profile]
    with pytest.raises(KeyError):
        d15.degree_cell("L050", 110)  # D12-only arm refused
    with pytest.raises(KeyError):
        d15.degree_cell("L045", 104)  # non-frozen rows refused
    with pytest.raises(KeyError):
        d15.degree_cell("L2", 104)  # D14N-only rows refused


def test_d15_rate_math_computed_not_copied():
    assert d15.H_L1 == 4.286720430201375
    assert d15.H_L2 == 3.222719884634378
    assert d15.LOAD_L1 == 548.700215065776
    assert d15.LOAD_L2 == 412.508145233200
    assert d15.LOAD_L1 == 128 * d15.H_L1
    assert abs(d15.LOAD_L2 - 128 * d15.H_L2) < 1e-9
    assert [d15.disclosed_bits(m) for m in d15.ROWS_L1] == [550, 570, 590]
    assert [d15.disclosed_bits(m) for m in d15.ROWS_L2] == [415, 430, 445]
    # Factors are computed as disclosed/load (exact division identities).
    for layer, load, rows_seq in (("L1", d15.LOAD_L1, d15.ROWS_L1),
                                  ("L2", d15.LOAD_L2, d15.ROWS_L2)):
        for m in rows_seq:
            assert d15.effective_factor(layer, m) == \
                (5 * m) / load
    # Approximations match the frozen packet values; pairing gaps < 0.004.
    approx = {("L1", 110): 1.00237, ("L1", 114): 1.03882,
              ("L1", 118): 1.07527, ("L2", 83): 1.00604,
              ("L2", 86): 1.04240, ("L2", 89): 1.07877}
    for (layer, m), want in approx.items():
        assert abs(d15.effective_factor(layer, m) - want) < 5e-6
    for m1, m2 in zip(d15.ROWS_L1, d15.ROWS_L2):
        gap = d15.effective_factor("L2", m2) - d15.effective_factor(
            "L1", m1)
        assert 0.0 < gap < 0.004
    # No rounded factor constant exists to copy: factors only come from
    # the division above.
    assert not hasattr(d15, "EFFECTIVE_FACTOR")
    assert not hasattr(d15, "F_EFF")
    with pytest.raises(KeyError):
        d15.effective_factor("L0", 110)


def test_d15_frozen_seeds_exact_and_disjoint():
    assert d15.GRAPH_SEEDS[("L045", 110)] == tuple(range(2026093801,
                                                        2026093805))
    assert d15.GRAPH_SEEDS[("L2", 89)] == tuple(range(2026093833,
                                                     2026093837))
    assert d15.BLOCK_SEEDS == tuple(range(2026093901, 2026093909))
    assert len({s for seeds in d15.GRAPH_SEEDS.values()
                for s in seeds}) == 36
    priors = ({s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
              | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds}
              | set(d14n.L1_GRAPH_SEEDS) | set(d14n.L2_GRAPH_SEEDS)
              | set(d14n.BLOCK_SEEDS))
    assert {s for seeds in d15.GRAPH_SEEDS.values()
            for s in seeds}.isdisjoint(priors)
    assert set(d15.BLOCK_SEEDS).isdisjoint(priors)
    with pytest.raises(ValueError):
        d15.build_l1_graph("L045", 110, 2026093001)  # D12 seed refused
    with pytest.raises(ValueError):
        d15.build_l1_graph("L045", 110, 2026093901)  # block seed refused
    with pytest.raises(ValueError):
        d15.build_l1_graph("L045", 110, 2026093825)  # L2 seed refused
    with pytest.raises(ValueError):
        d15.build_l1_graph("L045", 114, 2026093801)  # wrong-cell refused
    with pytest.raises(ValueError):
        d15.build_l2_graph(83, 2026093801)  # L1 seed refused
    with pytest.raises(KeyError):
        d15.build_l1_graph("L050", 110, 2026093801)  # D12 profile refused


def test_d15_no_source_auth_or_replacement_mechanism():
    assert not hasattr(d15, "BATCH_AUTHORIZED")
    assert not hasattr(d15, "REPLACEMENT_SEEDS")
    assert not hasattr(d15, "PROFILE_REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.d15_batch is False
    assert args.execution_authorized is False


def test_d15_reuse_not_duplication():
    assert d15.DECODER_MAX_ITER == 90 and d15.DAMPING_ALPHA == 1.0
    assert d15.Q == 32 and d15.POLY == 37
    assert d15.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d15.RSS_BUDGET_BYTES == r2.RSS_BUDGET_BYTES
    assert d15.dispatch_l1 is r2.dispatch_l1
    assert d15.coefficient_seed is r2.coefficient_seed
    assert d15.refuse_out_root is r2.refuse_out_root
    assert d15.sample_matched_block is d5.sample_matched_block
    assert d15.prepare_model_f_prior_candidate is \
        d5.prepare_model_f_prior_candidate
    assert d15.marginalize_f_to_p1 is d5.marginalize_f_to_p1
    assert d15.floor_renorm is d5._floor_renorm
    assert d15.oracle_l2_prior is d5.oracle_l2_prior
    assert d15.DECODER_FLOOR == d5.DECODER_FLOOR == 1e-15


def test_d15_no_cross_layer_binding_path():
    for path in (MODULE_PATH, RUNNER_PATH):
        source = path.read_text("utf-8")
        for token in ("canonical_transfer", "transfer_prior",
                      "app_fed", "transfer_fn", "transfer_parts",
                      "transfer_mixer", "app_source", "L2_APP",
                      "APP_ARM", "app_joint"):
            assert token not in source, (path.name, token)
    assert "L2_APP" not in d15.ARMS and len(d15.ARMS) == 3
    assert not hasattr(d15, "transfer_fn")
    assert not hasattr(runner, "APP_SOURCE_PROFILE")
    import inspect as _inspect
    assert "oracle_prior_fn" in _inspect.signature(
        d15.execute_plan).parameters
    assert "transfer_fn" not in _inspect.signature(
        d15.execute_plan).parameters
    assert "oracle_prior_fn" in _inspect.signature(
        d15.run_l2_oracle_cell).parameters


def test_d15_shared_constructor_all_families_one_path(monkeypatch):
    calls = []
    real = r2.build_degree_sequence_peg

    def counting(n, m, var_counts, check_counts, seed, field=None):
        calls.append((n, m, int(seed)))
        return real(n, m, var_counts, check_counts, seed, field=field)

    monkeypatch.setattr(r2, "build_degree_sequence_peg", counting)
    d15.build_l1_graph("L045", 110, 2026093801)
    d15.build_l1_graph("L055", 118, 2026093821)
    d15.build_l2_graph(89, 2026093833)
    assert calls
    assert all(seed in {s for seeds in d15.GRAPH_SEEDS.values()
                        for s in seeds} for _, _, seed in calls)


# --------------------------------------------------------------------------- #
# D1504: deterministic 288-record plan, paired blocks, budgets
# --------------------------------------------------------------------------- #
def test_d15_plan_288_paired_identities():
    plan = d15.build_call_plan()
    assert len(plan) == 288 == d15.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in plan] == list(range(288))
    per_cell = {}
    for entry in plan:
        per_cell.setdefault((entry["arm"], entry["rows"]), []).append(entry)
    assert len(per_cell) == 9
    for (arm, rows), entries in per_cell.items():
        assert len(entries) == 32  # 4 graphs x 8 blocks
        assert sorted(e["graph_seed"] for e in entries) == sorted(
            s for s in {e["graph_seed"] for e in entries}
            for _ in d15.BLOCK_SEEDS)
        assert sorted({e["block_seed"] for e in entries}) == \
            sorted(int(s) for s in d15.BLOCK_SEEDS)  # paired blocks
        for e in entries:
            assert e["disclosed_bits"] == 5 * rows
            assert e["effective_factor"] == d15.effective_factor(
                e["layer"], rows)
    # Frozen point-major order: point, L045 → L055 → L2-ORACLE, seeds.
    pos = 0
    for point_idx, point_rows in enumerate(d15.POINTS, start=1):
        for profile, rows in zip(("L045", "L055", "L2"), point_rows):
            arm = profile if profile in d15.L1_PROFILES else d15.ORACLE_ARM
            for seed in d15.GRAPH_SEEDS[(profile, int(rows))]:
                for block in d15.BLOCK_SEEDS:
                    e = plan[pos]
                    assert (e["point_idx"], e["arm"], e["rows"],
                            e["graph_seed"], e["block_seed"]) == \
                        (point_idx, arm, int(rows), int(seed), int(block))
                    pos += 1
    assert pos == 288
    runner._validate_call_plan(plan)
    with pytest.raises(ValueError):
        runner._validate_call_plan(plan[:-1])  # short plan refused
    swapped = list(plan)
    swapped[0], swapped[32] = swapped[32], swapped[0]
    with pytest.raises(ValueError):
        runner._validate_call_plan(swapped)  # order violation refused


def test_d15_budgets_frozen():
    assert d15.SCIENTIFIC_CALL_CEILING == 288
    assert d15.SETUP_CALL_CEILING == 46 == 36 + 8 + 2
    assert d15.SETUP_FIXED_UNITS == 2
    assert d15.WALL_BUDGET_S == 1800.0
    assert d15.PER_CALL_BUDGET_S == 120.0
    assert d15.RSS_BUDGET_BYTES == 2 * 1024 ** 3


# --------------------------------------------------------------------------- #
# D1508: gate boundaries, all six terminals, collision priority
# --------------------------------------------------------------------------- #
def test_d15_gate_boundaries():
    ok = {("L045", 118): [8, 8, 8, 8]}
    weak = {("L045", 118): [0, 0, 0, 0]}
    base = _full_cells(lambda arm, m: [8, 8, 8, 8])
    assert d15.is_cell_adequate(_tallies({**base, **ok}), "L045", 118)
    # Pool 23 with support is the middle zone: neither adequate nor weak.
    mid = _full_cells(lambda arm, m: [8, 8, 8, 8])
    mid[("L045", 118)] = [8, 8, 7, 0]  # pool 23
    assert not d15.is_cell_adequate(_tallies(mid), "L045", 118)
    assert not d15.is_cell_weak(_tallies(mid), "L045", 118)
    # Pool 16 with support is weak; pool 17 is the middle zone.
    weak16 = _full_cells(lambda arm, m: [8, 8, 8, 8])
    weak16[("L045", 118)] = [4, 4, 4, 4]
    assert d15.is_cell_weak(_tallies(weak16), "L045", 118)
    mid17 = _full_cells(lambda arm, m: [8, 8, 8, 8])
    mid17[("L045", 118)] = [5, 4, 4, 4]  # pool 17
    assert not d15.is_cell_weak(_tallies(mid17), "L045", 118)
    assert not d15.is_cell_adequate(_tallies(mid17), "L045", 118)
    # Pool ≤16 WITHOUT multi-graph support is not weak (no single-graph
    # pattern closes anything): [8, 8, 0, 0] has only two ≤4... use a
    # failing shape [6, 5, 5, 0]: pool 16, only one graph ≤4.
    nosupport = _full_cells(lambda arm, m: [8, 8, 8, 8])
    nosupport[("L045", 118)] = [6, 5, 5, 0]
    assert not d15.is_cell_weak(_tallies(nosupport), "L045", 118)
    assert d15.is_cell_weak(_tallies({**base, **weak}), "L045", 118)
    with pytest.raises(TypeError):
        d15.is_cell_adequate("not-tallies", "L045", 118)
    with pytest.raises(TypeError):
        d15.route_terminal("not-tallies")


def _l1_specific_spec():
    spec = _full_cells(lambda arm, m: [0, 0, 0, 0])
    spec[("L045", 110)] = [0, 0, 0, 0]
    spec[("L045", 114)] = [0, 0, 0, 0]
    spec[("L045", 118)] = [0, 0, 0, 0]
    spec[("L055", 110)] = [0, 0, 0, 0]
    spec[("L055", 114)] = [0, 0, 0, 0]
    spec[("L055", 118)] = [0, 0, 0, 0]
    spec[(d15.ORACLE_ARM, 83)] = [8, 8, 8, 8]
    spec[(d15.ORACLE_ARM, 86)] = [8, 8, 8, 8]
    spec[(d15.ORACLE_ARM, 89)] = [8, 8, 8, 8]
    return spec


def test_d15_terminals_all_six_and_priority():
    assert d15.route_terminal(_tallies(_l1_specific_spec())) == \
        d15.T_L1_SPECIFIC
    l2 = _full_cells(lambda arm, m: [8, 8, 8, 8])
    for key in [(d15.ORACLE_ARM, 83), (d15.ORACLE_ARM, 86),
                (d15.ORACLE_ARM, 89)]:
        l2[key] = [0, 0, 0, 0]
    assert d15.route_terminal(_tallies(l2)) == d15.T_L2_SPECIFIC
    backoff = _full_cells(lambda arm, m: [4, 4, 4, 4])
    for key in [("L045", 118), ("L055", 118), (d15.ORACLE_ARM, 89)]:
        backoff[key] = [8, 8, 8, 8]
    for key in [("L045", 110), ("L055", 110), (d15.ORACLE_ARM, 83)]:
        backoff[key] = [0, 0, 0, 0]
    assert d15.route_terminal(_tallies(backoff)) == d15.T_FINITE_BACKOFF
    both = _full_cells(lambda arm, m: [0, 0, 0, 0])
    assert d15.route_terminal(_tallies(both)) == d15.T_BOTH_WEAK
    all_exact = _full_cells(lambda arm, m: [8, 8, 8, 8])
    assert d15.route_terminal(_tallies(all_exact)) == d15.T_AMBIGUOUS
    # Collision priority: engineering first, then L1/L2/backoff/both.
    assert d15.route_terminal(_tallies(_l1_specific_spec()),
                              "decoder crash") == d15.T_ENGINEERING_BLOCKED
    assert d15.route_terminal(_tallies(both), "wall budget") == \
        d15.T_ENGINEERING_BLOCKED
    assert d15.route_terminal(_tallies(all_exact), "") == d15.T_AMBIGUOUS
    assert set(d15.TERMINALS) == {
        d15.T_L1_SPECIFIC, d15.T_L2_SPECIFIC, d15.T_FINITE_BACKOFF,
        d15.T_BOTH_WEAK, d15.T_AMBIGUOUS, d15.T_ENGINEERING_BLOCKED}


def test_d15_monotonicity_reported_never_repaired():
    # L1-specific shape but L045 pools decrease with margin: the violation
    # is reported and the route falls through to AMBIGUOUS (never smoothed
    # or re-scored into a layer claim).
    spec = _l1_specific_spec()
    spec[("L045", 110)] = [4, 4, 4, 4]  # pool 16, weak
    spec[("L045", 114)] = [2, 2, 2, 2]  # pool 8, weak
    spec[("L045", 118)] = [0, 0, 0, 0]  # pool 0, weak
    tallies = _tallies(spec)
    report = d15.monotonicity_report(tallies)
    assert report["arms"]["L045"]["pools"] == [16, 8, 0]
    assert report["arms"]["L045"]["non_decreasing"] is False
    assert report["arms"]["L055"]["non_decreasing"] is True
    assert report["all_non_decreasing"] is False
    assert len(report["violations"]) == 2
    assert d15.route_terminal(tallies) == d15.T_AMBIGUOUS
    with pytest.raises(TypeError):
        d15.monotonicity_report("not-tallies")


def test_d15_paired_discordance_descriptive_only():
    ref, chal = {}, {}
    for o in range(4):
        for i, block in enumerate(d15.BLOCK_SEEDS):
            ref[(o, int(block))] = (i % 2 == 0)
            chal[(o, int(block))] = (i % 4 == 0)
    out = d15.describe_paired_l1(ref, chal)
    assert out["cells"] == 32 and out["descriptive_only"] is True
    # ref true on even i ({0,2,4,6}); chal true on i%4==0 ({0,4}):
    # challenger-only 0, reference-only {2,6} x4 ordinals = 8.
    assert out["challenger_only"] == 0  # i%4==0 implies i%2==0
    assert out["reference_only"] == 8
    assert out["concordant"] == 24
    assert out["trials"] == 8
    with pytest.raises(ValueError):
        d15.describe_paired_l1({}, chal)  # unpaired trials refused


def test_d15_wilson_descriptive_only():
    lo, hi = d15.wilson_interval(32, 32)
    assert 0.85 < lo < hi == 1.0
    lo0, hi0 = d15.wilson_interval(0, 32)
    assert lo0 == 0.0 and hi0 < 0.15
    prev = -1.0
    for k in (0, 8, 16, 24, 32):
        lo_k, hi_k = d15.wilson_interval(k, 32)
        assert lo_k <= k / 32 <= hi_k
        assert lo_k >= prev - 1e-12  # monotone in k
        prev = lo_k
    with pytest.raises(ValueError):
        d15.wilson_interval(33, 32)
    with pytest.raises(ValueError):
        d15.wilson_interval(0, 0)


def test_d15_syndrome_never_substitutes_for_exact():
    # Syndrome-valid but inexact trials contribute zero to every pool.
    spec = _full_cells(lambda arm, m: [0, 0, 0, 0])
    records = _full_tagged(spec)
    for rec in records[:10]:
        rec["syndrome_ok"] = True  # still inexact
    tallies = d15.tallies_from_d15_records(records)
    assert all(tallies.pool(arm, m) == 0
               for arm, m in tallies.cells())
    assert d15.route_terminal(tallies) == d15.T_BOTH_WEAK


def test_d15_predecessor_records_cannot_enter_gate():
    spec = _full_cells(lambda arm, m: [8, 8, 8, 8])
    records = _full_tagged(spec)
    assert len(records) == 288
    d15.tallies_from_d15_records(records)  # valid baseline passes
    bad = [dict(r) for r in records]
    bad[0] = dict(bad[0], batch_id="d14-discriminator-v1")
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(bad)
    dup = [dict(r) for r in records] + [dict(records[0])]
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(dup)
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(records[:-1])  # short: zero-skip
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records([])
    wrong = [dict(r) for r in records]
    wrong[5] = dict(wrong[5], arm="L2_APP")
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(wrong)
    ungraded_l1 = [dict(r) for r in records]
    ungraded_l1[0] = dict(ungraded_l1[0], graded=False)
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(ungraded_l1)
    graded_oracle = [dict(r) for r in records]
    idx = next(i for i, r in enumerate(graded_oracle)
               if r["arm"] == d15.ORACLE_ARM)
    graded_oracle[idx] = dict(graded_oracle[idx], graded=True)
    with pytest.raises(ValueError):
        d15.tallies_from_d15_records(graded_oracle)
    with pytest.raises(ValueError):
        d15.D15Tallies({("L045", 110): [8, 8, 8, 8]})  # not nine cells
    with pytest.raises(ValueError):
        d15.D15Tallies(_full_cells(lambda arm, m: [8, 8, 9, 8]))


# --------------------------------------------------------------------------- #
# Fake dispatch: identities, oracle isolation, admission block, zero calls
# --------------------------------------------------------------------------- #
def test_d15_fake_dispatch_shares_identities_with_zero_real_calls():
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(calls)
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    plan = d15.build_call_plan()
    outcome = d15.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["engineering_reason"] == ""
    assert outcome["decoder_calls"] == 288
    assert len(calls) == 288  # fakes only; production never bound
    _assert_no_production_entry()
    tallies = d15.tallies_from_d15_records(outcome["records"])
    assert all(tallies.pool(arm, m) == 32 for arm, m in tallies.cells())
    assert d15.route_terminal(tallies) == d15.T_AMBIGUOUS
    for record, entry in zip(outcome["records"], plan):
        for key in ("point_idx", "layer", "arm", "rows", "graph_seed",
                    "block_seed"):
            assert str(record[key]) == str(entry[key])
        if record["arm"] == d15.ORACLE_ARM:
            assert record["oracle"] is True and record["graded"] is False
            assert record["belief_provenance"] == "ORACLE"
        else:
            assert record["oracle"] is False and record["graded"] is True


def test_d15_oracle_ungraded_and_excluded():
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    entry = {"point_idx": 1, "layer": "L2", "arm": d15.ORACLE_ARM,
             "rows": 83, "disclosed_bits": 415,
             "effective_factor": d15.effective_factor("L2", 83),
             "graph_seed": 2026093825, "block_seed": 2026093901}
    adapters = _fake_adapters()
    record = d15.run_l2_oracle_cell(
        graphs_l2[(83, 2026093825)], blocks[2026093901], entry,
        decode_fn=adapters["decode_fn"],
        syndrome_fn=adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=0)
    assert record["exact"] is True and record["graded"] is False
    assert record["oracle"] is True
    assert record["batch_id"] == d15.D15_BATCH_ID
    with pytest.raises(ValueError):
        d15.run_l2_oracle_cell(
            graphs_l2[(83, 2026093825)], blocks[2026093901], entry,
            decode_fn=adapters["decode_fn"],
            syndrome_fn=adapters["syndrome_fn"],
            oracle_prior_fn=None, call_idx=0)


def test_d15_nonadmitted_graph_blocks_with_zero_decoder_calls():
    calls = []
    adapters = _fake_adapters(calls)
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    broken = dict(graphs_l1[("L045", 110, 2026093801)])
    broken["admitted"] = False
    graphs_l1[("L045", 110, 2026093801)] = broken
    outcome = d15.execute_plan(
        d15.build_call_plan(), graphs_l1, graphs_l2, blocks,
        adapters["decode_fn"], adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 0
    assert calls == []
    assert "not admitted" in outcome["engineering_reason"]
    assert d15.route_terminal(
        _tallies(_full_cells(lambda arm, m: [0, 0, 0, 0])),
        outcome["engineering_reason"]) == d15.T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# Runner: refusal, writer, verifier, profile-only, fake authorized branch
# --------------------------------------------------------------------------- #
def test_d15_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    _assert_no_production_entry()
    target = tmp_path / "d15_no_auth"
    rc = runner.main(["--d15-batch", "--out-root", str(target)])
    assert rc == 2
    assert not target.exists()
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()


def test_d15_writer_never_overwrites(tmp_path):
    calls = []
    adapters = _fake_adapters(calls)
    target = tmp_path / "d15_root"
    bundle = runner.run_authorized_batch(
        str(target), d15.MODEL_F_INPUT_ROOT, adapters=adapters)
    summary = runner.write_batch_root(bundle)
    assert summary["scientific_calls"] == 288
    assert summary["setup_calls"] == 46
    assert sorted(p.name for p in target.iterdir()) == \
        sorted(d15.EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        runner.write_batch_root(bundle)  # never overwrite
    probe_calls = []
    with pytest.raises(FileExistsError):
        runner.run_authorized_batch(  # refuse probe before decoder calls
            str(target), d15.MODEL_F_INPUT_ROOT,
            adapters=_fake_adapters(probe_calls))
    assert probe_calls == []
    assert not FUTURE_ROOT.exists()


def test_d15_verify_roundtrip_and_fail_closed(tmp_path):
    adapters = _fake_adapters()
    target = tmp_path / "d15_verify"
    bundle = runner.run_authorized_batch(
        str(target), d15.MODEL_F_INPUT_ROOT, adapters=adapters)
    runner.write_batch_root(bundle)
    assert runner.verify_root(
        str(target), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is True
    (target / "arm_summary.csv").unlink()  # partial root
    assert runner.verify_root(
        str(target), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False


def test_d15_verify_fail_closed_on_isolation_and_blocked(tmp_path):
    adapters = _fake_adapters()
    target = tmp_path / "d15_isolation"
    bundle = runner.run_authorized_batch(
        str(target), d15.MODEL_F_INPUT_ROOT, adapters=adapters)
    runner.write_batch_root(bundle)
    with open(target / "decoder_records.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    rows[0]["syndrome_ok"] = "False"  # exact without syndrome_ok
    with open(target / "decoder_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh,
                                fieldnames=list(runner
                                                .DECODER_RECORD_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    assert runner.verify_root(
        str(target), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False
    # Engineering-blocked roots fail closed even when fully written.
    blocked = tmp_path / "d15_blocked"
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    broken = dict(graphs_l1[("L055", 118, 2026093821)])
    broken["admitted"] = False
    graphs_l1[("L055", 118, 2026093821)] = broken
    plan = d15.build_call_plan()
    outcome = d15.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["engineering_reason"] != ""
    bundle = runner.run_authorized_batch(
        str(blocked), d15.MODEL_F_INPUT_ROOT, adapters=adapters)
    bundle["records"] = outcome["records"]
    bundle["summary"] = dict(
        bundle["summary"],
        engineering_reason=outcome["engineering_reason"],
        terminal=d15.T_ENGINEERING_BLOCKED,
        scientific_calls=len(outcome["records"]))
    runner.write_batch_root(bundle)
    assert runner.verify_root(
        str(blocked), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False


def test_d15_profile_only_36_graphs():
    _assert_no_production_entry()
    report = runner.profile_only()
    assert report["total_graphs"] == 36
    assert report["admitted"] == 36
    assert report["replacement_seeds_used"] == 0
    assert report["frozen_seed_failures"] == []
    assert report["plan_calls"] == 288
    assert report["decoder_calls"] == 0
    assert report["future_root_absent"] is True
    assert not FUTURE_ROOT.exists()
    admissions = set()
    for entry in report["graphs"]:
        assert entry["E"] == d15.EDGE_TOTALS[
            "L2" if entry["arm"] == d15.ORACLE_ARM else entry["arm"]]
        admissions.update(entry["admission"])
        assert entry["admission"]["A1_exact_degrees_socket_balance"]
        assert entry["admission"]["A2_simple_graph_min_degree"]
        assert entry["admission"]["A3_single_component"]
        assert entry["admission"]["A4_structural_rank_m"]
        assert entry["admission"]["A5_gf32_rank_m"]
        assert entry["admission"]["A6_deterministic_replay"]
    assert admissions == {
        "A1_exact_degrees_socket_balance", "A2_simple_graph_min_degree",
        "A3_single_component", "A4_structural_rank_m", "A5_gf32_rank_m",
        "A6_deterministic_replay"}
    _assert_no_production_entry()


def _spy_on_binder(monkeypatch):
    calls = []

    def boom():
        calls.append(1)
        raise AssertionError("production binder entered on the fake path")

    monkeypatch.setattr(runner, "bind_production_adapters", boom)
    return calls


def _authorized_args(scratch):
    return ["--d15-batch", "--execution-authorized",
            "--out-root", str(scratch)]


def test_d15_fake_authorized_true_branch_288(monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls, loads = [], []
    adapters = _fake_adapters(calls, loads)
    binder_calls = _spy_on_binder(monkeypatch)
    rc = runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert rc == 0
    assert len(calls) == 288  # 192 L1 (L045+L055) + 96 ORACLE
    shapes = sorted(shape[0] for shape in calls)
    assert shapes.count(110) + shapes.count(114) + shapes.count(118) == 192
    assert shapes.count(83) + shapes.count(86) + shapes.count(89) == 96
    assert len(loads) == 1  # injected prior path ran exactly once
    assert binder_calls == []  # production binder never entered
    _assert_no_production_entry()
    assert sorted(p.name for p in scratch_root.iterdir()) == \
        sorted(d15.EVIDENCE_FILES)
    summary = json.loads((scratch_root / "summary.json").read_text("utf-8"))
    assert summary["setup_calls"] == 46  # 36 graphs + 8 blocks + 2 fixed
    assert summary["scientific_calls"] == 288
    assert summary["planned_calls"] == 288
    assert summary["terminal"] == d15.T_AMBIGUOUS  # all-exact fakes
    assert summary["engineering_reason"] == ""
    assert all(v == 32 for v in summary["pools"].values())
    plan = d15.build_call_plan()
    with open(scratch_root / "decoder_records.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(plan) == 288
    for index, (row, entry) in enumerate(zip(rows, plan)):
        assert int(row["call_idx"]) == index
        for key in ("point_idx", "layer", "arm", "rows", "graph_seed",
                    "block_seed"):
            assert str(row[key]) == str(entry[key]), (index, key)
    assert runner.verify_root(
        str(scratch_root), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is True
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()

