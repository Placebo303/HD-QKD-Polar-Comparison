"""D16 focused tests: frozen cells/seeds/math, plan, gates, dispatch, refusal.

Fake/tiny only: the production decoder is never imported, no scientific
call is made and no root outside pytest tmp paths or fresh gitignored
``workspace/`` scratch dirs is created. The single real-builder test is
``test_d16_profile_only_12_graphs`` (PROFILE_ONLY, no decoder, no root).
The fake authorized branch runs ``--d16-batch --execution-authorized``
with injected fakes into a scratch root — never the frozen future root,
never the production binder, never the Model-F loader, never the
production decoder (96/96 fakes, 22 setup, six files, verifier PASS).

Process rule: this file must run in a process where the named production
keys are absent at entry — standalone
``pytest -p no:cacheprovider comparison_bench/tests/test_v72p2d16_matched_backoff.py``
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

RUNNER_PATH = ROOT / "scripts" / "v72p2d16_matched_backoff_development.py"
MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d16_matched_backoff.py")


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
import comparison_bench.formal_ir.v72p2d15_margin_curve as d15  # noqa: E402
import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5  # noqa: E402
import comparison_bench.formal_ir.v72p2d16_matched_backoff as d16  # noqa: E402

runner = _load_module("v72p2d16_runner_test", RUNNER_PATH)

#: Production entries that must never appear on any fake path: the v35
#: decoder module, the Model-F contrast loader module (both registered
#: names), and the R2-runner reuse keys (binder-only).
PRODUCTION_ABSENT_KEYS = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "v72p2d10_r2_runner_reuse_d16",
    "v72p2d10_r2_runner_reuse_d15",
    "v72p2d10_r2_runner_reuse_n14",
    "v72p2d10_r2_runner_reuse_d11",
)

FUTURE_ROOT = (ROOT / d16.FUTURE_ROOT).resolve()

FROZEN_COMMAND_LITERAL = (
    ".venv/bin/python scripts/v72p2d16_matched_backoff_development.py "
    "--d16-batch --execution-authorized --model-f-root "
    "workspace/v72p2d5_model_f_input/20260907_r1 --out-root "
    "workspace/d16_matched_backoff_discriminator_"
    "b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a")


def _assert_no_production_entry():
    absent = [key for key in PRODUCTION_ABSENT_KEYS if key in sys.modules]
    assert absent == [], "production entry on fake path: %r" % (absent,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("d16_fake_authorized_%s" % uuid.uuid4().hex)
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
    return _fake_graph(d16.ORACLE_ARM, rows, seed)


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
    for profile, rows in d16.CELLS:
        for seed in d16.GRAPH_SEEDS[(profile, int(rows))]:
            if profile in d16.L1_PROFILES:
                graphs_l1[(profile, int(rows),
                           int(seed))] = _fake_l1_graph(
                               profile, rows, seed)
            else:
                graphs_l2[(int(rows), int(seed))] = _fake_l2_graph(
                    rows, seed)
    blocks = {int(s): _fake_block(s) for s in d16.BLOCK_SEEDS}
    return graphs_l1, graphs_l2, blocks


def _tallies(spec):
    """Build D16Tallies from {(arm, rows): [4 per-graph counts]}."""
    return d16.D16Tallies({key: list(vec) for key, vec in spec.items()})


def _full_cells(pool_fn):
    return {(arm, int(m)): pool_fn(arm, int(m))
            for arm, m in [("L045", 125), ("L055", 125),
                           (d16.ORACLE_ARM, 94)]}


def _tagged(arm, rows, graph_seed, block_seed, exact, oracle=False,
            graded=True, syndrome=None, undetected=False):
    layer = "L2" if oracle else "L1"
    return {"call_idx": 0, "point_idx": 1, "layer": layer, "arm": arm,
            "rows": rows, "disclosed_bits": 5 * rows,
            "effective_factor": d16.effective_factor(layer, rows),
            "graph_seed": graph_seed, "block_seed": block_seed,
            "batch_id": d16.D16_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome is None else syndrome,
            "source_exact": False, "target_exact": exact if oracle else False,
            "joint_exact": False, "undetected": undetected,
            "oracle": oracle, "graded": graded}


def _full_tagged(spec):
    """Tagged records from {(arm, rows): [4 per-graph exact counts 0..8]}."""
    records = []
    for (arm, rows), vec in spec.items():
        oracle = arm == d16.ORACLE_ARM
        profile = "L2" if oracle else arm
        for seed, total in zip(d16.GRAPH_SEEDS[(profile, int(rows))], vec):
            for i, block in enumerate(d16.BLOCK_SEEDS):
                records.append(_tagged(arm, int(rows), int(seed),
                                       int(block), i < total,
                                       oracle=oracle,
                                       graded=not oracle))
    return records


# --------------------------------------------------------------------------- #
# D1603/frozen tables: three cells, rate math, seeds, scope guards
# --------------------------------------------------------------------------- #
def test_d16_cells_exact():
    assert d16.degree_cell("L045", 125)["check_counts"] == {2: 62, 3: 63}
    assert d16.degree_cell("L055", 125)["check_counts"] == {2: 74, 3: 51}
    assert d16.degree_cell("L2", 94)["check_counts"] == {4: 86, 5: 8}
    assert d16.degree_cell("L045", 125)["E"] == 313
    assert d16.degree_cell("L055", 125)["E"] == 301
    assert d16.degree_cell("L2", 94)["E"] == 384
    for profile, rows in d16.CELLS:
        cell = d16.degree_cell(profile, rows)
        assert sum(cell["var_counts"].values()) == 128 == cell["n"]
        assert sum(cell["check_counts"].values()) == rows == cell["m"]
        assert cell["E"] == sum(d * c for d, c in
                                cell["var_counts"].items())
        assert cell["E"] == sum(d * c for d, c in
                                cell["check_counts"].items())
        assert cell["E"] == d16.EDGE_TOTALS[profile]
    with pytest.raises(KeyError):
        d16.degree_cell("L050", 125)  # D12-only arm refused
    with pytest.raises(KeyError):
        d16.degree_cell("L045", 118)  # D15-only rows refused
    with pytest.raises(KeyError):
        d16.degree_cell("L2", 89)  # D15-only rows refused
    with pytest.raises(KeyError):
        d16.degree_cell("L2", 104)  # D14N-only rows refused


def test_d16_rate_math_computed_not_copied():
    assert d16.LOAD_L1 == 548.700215065776
    assert d16.LOAD_L2 == 412.508145233200
    assert d16.disclosed_bits(125) == 625
    assert d16.disclosed_bits(94) == 470
    # Exact frozen factors: computed as disclosed/load (exact identities).
    assert d16.effective_factor("L1", 125) == 625 / 548.700215065776
    assert d16.effective_factor("L1", 125) == 1.1390555039696448
    assert d16.effective_factor("L2", 94) == 470 / 412.508145233200
    assert d16.effective_factor("L2", 94) == 1.1393714413428093
    gap = d16.effective_factor("L2", 94) - d16.effective_factor("L1", 125)
    assert gap == 0.00031593737316448767
    assert 0.0 < gap < 0.001
    # No rounded factor constant exists to copy: factors only come from
    # the division above.
    assert not hasattr(d16, "EFFECTIVE_FACTOR")
    assert not hasattr(d16, "F_EFF")
    with pytest.raises(KeyError):
        d16.effective_factor("L0", 125)


def test_d16_frozen_seeds_exact_and_disjoint():
    assert d16.GRAPH_SEEDS[("L045", 125)] == tuple(range(2026094001,
                                                        2026094005))
    assert d16.GRAPH_SEEDS[("L055", 125)] == tuple(range(2026094005,
                                                        2026094009))
    assert d16.GRAPH_SEEDS[("L2", 94)] == tuple(range(2026094009,
                                                     2026094013))
    assert d16.BLOCK_SEEDS == tuple(range(2026094101, 2026094109))
    assert len({s for seeds in d16.GRAPH_SEEDS.values()
                for s in seeds}) == 12
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
              | set(d14n.BLOCK_SEEDS)
              | {s for seeds in d15.GRAPH_SEEDS.values() for s in seeds}
              | set(d15.BLOCK_SEEDS))
    assert {s for seeds in d16.GRAPH_SEEDS.values()
            for s in seeds}.isdisjoint(priors)
    assert set(d16.BLOCK_SEEDS).isdisjoint(priors)
    with pytest.raises(ValueError):
        d16.build_l1_graph("L045", 125, 2026093001)  # D12 seed refused
    with pytest.raises(ValueError):
        d16.build_l1_graph("L045", 125, 2026094101)  # block seed refused
    with pytest.raises(ValueError):
        d16.build_l1_graph("L045", 125, 2026094009)  # L2 seed refused
    with pytest.raises(ValueError):
        d16.build_l1_graph("L045", 125, 2026094005)  # wrong-cell refused
    with pytest.raises(ValueError):
        d16.build_l2_graph(94, 2026094001)  # L1 seed refused
    with pytest.raises(ValueError):
        d16.build_l2_graph(94, 2026093825)  # D15 seed refused
    with pytest.raises(KeyError):
        d16.build_l1_graph("L050", 125, 2026094001)  # D12 profile refused


def test_d16_no_source_auth_or_replacement_mechanism():
    assert not hasattr(d16, "BATCH_AUTHORIZED")
    assert not hasattr(d16, "REPLACEMENT_SEEDS")
    assert not hasattr(d16, "PROFILE_REPLACEMENT_SEEDS")
    assert not hasattr(runner, "BATCH_AUTHORIZED")
    args = runner.build_parser().parse_args([])
    assert args.d16_batch is False
    assert args.execution_authorized is False


def test_d16_reuse_not_duplication():
    assert d16.DECODER_MAX_ITER == 90 and d16.DAMPING_ALPHA == 1.0
    assert d16.Q == 32 and d16.POLY == 37
    assert d16.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d16.RSS_BUDGET_BYTES == r2.RSS_BUDGET_BYTES
    assert d16.dispatch_l1 is r2.dispatch_l1
    assert d16.coefficient_seed is r2.coefficient_seed
    assert d16.refuse_out_root is r2.refuse_out_root
    assert d16.sample_matched_block is d5.sample_matched_block
    assert d16.prepare_model_f_prior_candidate is \
        d5.prepare_model_f_prior_candidate
    assert d16.marginalize_f_to_p1 is d5.marginalize_f_to_p1
    assert d16.floor_renorm is d5._floor_renorm
    assert d16.oracle_l2_prior is d5.oracle_l2_prior
    assert d16.wilson_interval is d15.wilson_interval
    assert d16.LOAD_L1 is d15.LOAD_L1 or d16.LOAD_L1 == d15.LOAD_L1
    assert d16.LOAD_L2 == d15.LOAD_L2
    assert d16.PRIOR_CHAIN == d15.PRIOR_CHAIN
    assert d16.DECODER_FLOOR == d5.DECODER_FLOOR == 1e-15


def test_d16_no_cross_layer_binding_path():
    for path in (MODULE_PATH, RUNNER_PATH):
        source = path.read_text("utf-8")
        for token in ("canonical_transfer", "transfer_prior",
                      "app_fed", "transfer_fn", "transfer_parts",
                      "transfer_mixer", "app_source", "L2_APP",
                      "APP_ARM", "app_joint"):
            assert token not in source, (path.name, token)
    assert "L2_APP" not in d16.ARMS and len(d16.ARMS) == 3
    assert not hasattr(d16, "transfer_fn")
    assert not hasattr(runner, "APP_SOURCE_PROFILE")
    import inspect as _inspect
    assert "oracle_prior_fn" in _inspect.signature(
        d16.execute_plan).parameters
    assert "transfer_fn" not in _inspect.signature(
        d16.execute_plan).parameters
    assert "oracle_prior_fn" in _inspect.signature(
        d16.run_l2_oracle_cell).parameters


def test_d16_shared_constructor_all_families_one_path(monkeypatch):
    calls = []
    real = r2.build_degree_sequence_peg

    def counting(n, m, var_counts, check_counts, seed, field=None):
        calls.append((n, m, int(seed)))
        return real(n, m, var_counts, check_counts, seed, field=field)

    monkeypatch.setattr(r2, "build_degree_sequence_peg", counting)
    d16.build_l1_graph("L045", 125, 2026094001)
    d16.build_l1_graph("L055", 125, 2026094005)
    d16.build_l2_graph(94, 2026094009)
    assert calls
    assert all(seed in {s for seeds in d16.GRAPH_SEEDS.values()
                        for s in seeds} for _, _, seed in calls)


# --------------------------------------------------------------------------- #
# D1604: deterministic 96-record plan, paired blocks, budgets
# --------------------------------------------------------------------------- #
def test_d16_plan_96_paired_identities():
    plan = d16.build_call_plan()
    assert len(plan) == 96 == d16.SCIENTIFIC_CALL_CEILING
    assert [e["call_idx"] for e in plan] == list(range(96))
    per_cell = {}
    for entry in plan:
        per_cell.setdefault((entry["arm"], entry["rows"]), []).append(entry)
    assert len(per_cell) == 3
    for (arm, rows), entries in per_cell.items():
        assert len(entries) == 32  # 4 graphs x 8 blocks
        assert sorted({e["block_seed"] for e in entries}) == \
            sorted(int(s) for s in d16.BLOCK_SEEDS)  # paired blocks
        for e in entries:
            assert e["point_idx"] == 1
            assert e["disclosed_bits"] == 5 * rows
            assert e["effective_factor"] == d16.effective_factor(
                e["layer"], rows)
    # Frozen arm-major order: L045 → L055 → L2-ORACLE, seeds ascending.
    pos = 0
    for profile, rows in (("L045", 125), ("L055", 125), ("L2", 94)):
        arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
        for seed in d16.GRAPH_SEEDS[(profile, int(rows))]:
            for block in d16.BLOCK_SEEDS:
                e = plan[pos]
                assert (e["point_idx"], e["arm"], e["rows"],
                        e["graph_seed"], e["block_seed"]) == \
                    (1, arm, int(rows), int(seed), int(block))
                pos += 1
    assert pos == 96
    runner._validate_call_plan(plan)
    with pytest.raises(ValueError):
        runner._validate_call_plan(plan[:-1])  # short plan refused
    swapped = list(plan)
    swapped[0], swapped[32] = swapped[32], swapped[0]
    with pytest.raises(ValueError):
        runner._validate_call_plan(swapped)  # order violation refused


def test_d16_budgets_frozen():
    assert d16.SCIENTIFIC_CALL_CEILING == 96
    assert d16.SETUP_CALL_CEILING == 22 == 12 + 8 + 2
    assert d16.SETUP_FIXED_UNITS == 2
    assert d16.WALL_BUDGET_S == 900.0
    assert d16.PER_CALL_BUDGET_S == 120.0
    assert d16.RSS_BUDGET_BYTES == 2 * 1024 ** 3


def test_d16_frozen_command_exact():
    assert d16.FROZEN_COMMAND == FROZEN_COMMAND_LITERAL
    assert runner.FROZEN_COMMAND == FROZEN_COMMAND_LITERAL
    assert "--d16-batch" in d16.FROZEN_COMMAND
    assert "--execution-authorized" in d16.FROZEN_COMMAND
    assert d16.FUTURE_ROOT == (
        "workspace/d16_matched_backoff_discriminator_"
        "b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a")


# --------------------------------------------------------------------------- #
# D1603 gate: boundaries, all six terminals, collision priority, L045 silence
# --------------------------------------------------------------------------- #
def test_d16_gate_boundaries():
    base = _full_cells(lambda arm, m: [8, 8, 8, 8])
    assert d16.is_cell_adequate(_tallies(base), "L055", 125)
    # Pool 23 with support is the middle zone: neither adequate nor weak.
    mid = _full_cells(lambda arm, m: [8, 8, 8, 8])
    mid[("L055", 125)] = [8, 8, 7, 0]  # pool 23
    assert not d16.is_cell_adequate(_tallies(mid), "L055", 125)
    assert not d16.is_cell_weak(_tallies(mid), "L055", 125)
    # Pool 16 with support is weak; pool 17 is the middle zone.
    weak16 = _full_cells(lambda arm, m: [8, 8, 8, 8])
    weak16[("L055", 125)] = [4, 4, 4, 4]
    assert d16.is_cell_weak(_tallies(weak16), "L055", 125)
    mid17 = _full_cells(lambda arm, m: [8, 8, 8, 8])
    mid17[("L055", 125)] = [5, 4, 4, 4]  # pool 17
    assert not d16.is_cell_weak(_tallies(mid17), "L055", 125)
    assert not d16.is_cell_adequate(_tallies(mid17), "L055", 125)
    # Pool ≥24 WITHOUT multi-graph support is not adequate: [8, 8, 8, 0]
    # has pool 24 but only one graph ≥6... use [8, 8, 5, 5]: pool 26,
    # only two ≥6? that passes. Failing shape: [8, 8, 8, 0] pool 24,
    # three ≥6 — passes. Use pool 24 with one ≥6: [8, 6, 5, 5] pool 24,
    # two ≥6 — passes. Failing: [8, 5, 5, 6] same. True fail: [8, 5, 5, 5]
    # pool 23. For pool ≥24 fail use [8, 8, 4, 4]: pool 24, two ≥6 passes.
    # [8, 7, 5, 4]: pool 24, two ≥6 (8,7) passes. [8, 5, 5, 6]: passes.
    # Genuine fail: [6, 5, 5, 8] passes too. Take [8, 5, 5, 6]... all pass
    # with two ≥6. Fail needs <2 graphs ≥6 with pool ≥24: [8, 5, 5, 6]
    # has two. [8, 8, 4, 4] has two. [8, 5, 6, 5] two. Impossible? No:
    # [8, 5, 5, 6] → 8,6 two. [7, 7, 5, 5]: pool 24, two ≥6 passes.
    # [8, 4, 6, 6]: passes. Fail: [8, 5, 5, 6]... two again. Use
    # [8, 5, 5, 5]: pool 23 <24 anyway. Max pool with ≤1 graph ≥6:
    # 8+5+5+5=23 <24 — so every pool-24 shape has ≥2 graphs ≥6? 8,8,4,4
    # yes; 7,6,6,5 yes; 8,6,5,5 yes. Adequate support is vacuous at the
    # boundary but still enforced by the predicate code path below.
    nosupport = _full_cells(lambda arm, m: [8, 8, 8, 8])
    nosupport[("L055", 125)] = [6, 5, 5, 0]  # pool 16, one ≤4
    assert not d16.is_cell_weak(_tallies(nosupport), "L055", 125)
    with pytest.raises(TypeError):
        d16.is_cell_adequate("not-tallies", "L055", 125)
    with pytest.raises(TypeError):
        d16.route_terminal("not-tallies")


def _l2_degree_signal_spec():
    # L055 ADEQUATE, L2 WEAK → D16_L2_DEGREE_SIGNAL (L045 arbitrary).
    return {("L045", 125): [0, 0, 0, 0],
            ("L055", 125): [8, 8, 8, 8],
            (d16.ORACLE_ARM, 94): [0, 0, 0, 0]}


def test_d16_terminals_all_six_and_priority():
    assert d16.route_terminal(_tallies(_l2_degree_signal_spec())) == \
        d16.T_L2_DEGREE_SIGNAL
    l1_signal = {("L045", 125): [8, 8, 8, 8],
                 ("L055", 125): [0, 0, 0, 0],
                 (d16.ORACLE_ARM, 94): [8, 8, 8, 8]}
    assert d16.route_terminal(_tallies(l1_signal)) == \
        d16.T_L1_CONSTRUCTION_SIGNAL
    both_ok = _full_cells(lambda arm, m: [8, 8, 8, 8])
    assert d16.route_terminal(_tallies(both_ok)) == d16.T_MATCHED_BACKOFF_SUFFICIENT
    both_weak = _full_cells(lambda arm, m: [0, 0, 0, 0])
    assert d16.route_terminal(_tallies(both_weak)) == d16.T_BOTH_WEAK
    # L055 middle (pool 20), L2 adequate → AMBIGUOUS.
    ambiguous = {("L045", 125): [0, 0, 0, 0],
                 ("L055", 125): [5, 5, 5, 5],
                 (d16.ORACLE_ARM, 94): [8, 8, 8, 8]}
    assert d16.route_terminal(_tallies(ambiguous)) == d16.T_AMBIGUOUS
    # Collision priority: engineering first; then L2-signal before every
    # weaker terminal even when weaker conditions also hold vacuously.
    assert d16.route_terminal(_tallies(_l2_degree_signal_spec()),
                              "decoder crash") == d16.T_ENGINEERING_BLOCKED
    assert d16.route_terminal(_tallies(both_weak), "wall budget") == \
        d16.T_ENGINEERING_BLOCKED
    assert set(d16.TERMINALS) == {
        d16.T_ENGINEERING_BLOCKED, d16.T_L2_DEGREE_SIGNAL,
        d16.T_L1_CONSTRUCTION_SIGNAL, d16.T_MATCHED_BACKOFF_SUFFICIENT,
        d16.T_BOTH_WEAK, d16.T_AMBIGUOUS}


def test_d16_l045_descriptive_only():
    # The gate reads L055 + L2 only: flipping L045 across adequate/weak/
    # middle never changes the terminal.
    for l045_vec in ([8, 8, 8, 8], [0, 0, 0, 0], [5, 5, 5, 5]):
        spec = {("L045", 125): l045_vec,
                ("L055", 125): [8, 8, 8, 8],
                (d16.ORACLE_ARM, 94): [0, 0, 0, 0]}
        assert d16.route_terminal(_tallies(spec)) == d16.T_L2_DEGREE_SIGNAL
        spec2 = {("L045", 125): l045_vec,
                 ("L055", 125): [0, 0, 0, 0],
                 (d16.ORACLE_ARM, 94): [0, 0, 0, 0]}
        assert d16.route_terminal(_tallies(spec2)) == d16.T_BOTH_WEAK


def test_d16_paired_discordance_descriptive_only():
    ref, chal = {}, {}
    for o in range(4):
        for i, block in enumerate(d16.BLOCK_SEEDS):
            ref[(o, int(block))] = (i % 2 == 0)
            chal[(o, int(block))] = (i % 4 == 0)
    out = d16.describe_paired_l1(ref, chal)
    assert out["cells"] == 32 and out["descriptive_only"] is True
    # ref true on even i ({0,2,4,6}); chal true on i%4==0 ({0,4}):
    # challenger-only 0, reference-only {2,6} x4 ordinals = 8.
    assert out["challenger_only"] == 0  # i%4==0 implies i%2==0
    assert out["reference_only"] == 8
    assert out["concordant"] == 24
    assert out["trials"] == 8
    with pytest.raises(ValueError):
        d16.describe_paired_l1({}, chal)  # unpaired trials refused


def test_d16_wilson_descriptive_only():
    assert d16.wilson_interval is d15.wilson_interval  # reuse, not a copy
    lo, hi = d16.wilson_interval(32, 32)
    assert 0.85 < lo < hi == 1.0
    lo0, hi0 = d16.wilson_interval(0, 32)
    assert lo0 == 0.0 and hi0 < 0.15
    prev = -1.0
    for k in (0, 8, 16, 24, 32):
        lo_k, hi_k = d16.wilson_interval(k, 32)
        assert lo_k <= k / 32 <= hi_k
        assert lo_k >= prev - 1e-12  # monotone in k
        prev = lo_k
    with pytest.raises(ValueError):
        d16.wilson_interval(33, 32)
    with pytest.raises(ValueError):
        d16.wilson_interval(0, 0)


def test_d16_syndrome_never_substitutes_for_exact():
    # Syndrome-valid but inexact trials contribute zero to every pool.
    spec = _full_cells(lambda arm, m: [0, 0, 0, 0])
    records = _full_tagged(spec)
    for rec in records[:10]:
        rec["syndrome_ok"] = True  # still inexact
    tallies = d16.tallies_from_d16_records(records)
    assert all(tallies.pool(arm, m) == 0
               for arm, m in tallies.cells())
    assert d16.route_terminal(tallies) == d16.T_BOTH_WEAK


def test_d16_predecessor_records_cannot_enter_gate():
    spec = _full_cells(lambda arm, m: [8, 8, 8, 8])
    records = _full_tagged(spec)
    assert len(records) == 96
    d16.tallies_from_d16_records(records)  # valid baseline passes
    bad = [dict(r) for r in records]
    bad[0] = dict(bad[0], batch_id="d15-margin-curve-v1")
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(bad)
    dup = [dict(r) for r in records] + [dict(records[0])]
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(dup)
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(records[:-1])  # short: zero-skip
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records([])
    wrong = [dict(r) for r in records]
    wrong[5] = dict(wrong[5], arm="L2_APP")
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(wrong)
    ungraded_l1 = [dict(r) for r in records]
    ungraded_l1[0] = dict(ungraded_l1[0], graded=False)
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(ungraded_l1)
    graded_oracle = [dict(r) for r in records]
    idx = next(i for i, r in enumerate(graded_oracle)
               if r["arm"] == d16.ORACLE_ARM)
    graded_oracle[idx] = dict(graded_oracle[idx], graded=True)
    with pytest.raises(ValueError):
        d16.tallies_from_d16_records(graded_oracle)
    with pytest.raises(ValueError):
        d16.D16Tallies({("L045", 125): [8, 8, 8, 8]})  # not three cells
    with pytest.raises(ValueError):
        d16.D16Tallies(_full_cells(lambda arm, m: [8, 8, 9, 8]))


# --------------------------------------------------------------------------- #
# Fake dispatch: identities, oracle isolation, admission block, zero calls
# --------------------------------------------------------------------------- #
def test_d16_fake_dispatch_shares_identities_with_zero_real_calls():
    _assert_no_production_entry()
    calls = []
    adapters = _fake_adapters(calls)
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    plan = d16.build_call_plan()
    outcome = d16.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["engineering_reason"] == ""
    assert outcome["decoder_calls"] == 96
    assert len(calls) == 96  # fakes only; production never bound
    _assert_no_production_entry()
    tallies = d16.tallies_from_d16_records(outcome["records"])
    assert all(tallies.pool(arm, m) == 32 for arm, m in tallies.cells())
    # All-exact fakes: L055 ADEQUATE and L2 ADEQUATE → MATCHED_BACKOFF_SUFFICIENT.
    assert d16.route_terminal(tallies) == d16.T_MATCHED_BACKOFF_SUFFICIENT
    for record, entry in zip(outcome["records"], plan):
        for key in ("point_idx", "layer", "arm", "rows", "graph_seed",
                    "block_seed"):
            assert str(record[key]) == str(entry[key])
        if record["arm"] == d16.ORACLE_ARM:
            assert record["oracle"] is True and record["graded"] is False
            assert record["belief_provenance"] == "ORACLE"
        else:
            assert record["oracle"] is False and record["graded"] is True


def test_d16_oracle_ungraded_and_excluded():
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    entry = {"point_idx": 1, "layer": "L2", "arm": d16.ORACLE_ARM,
             "rows": 94, "disclosed_bits": 470,
             "effective_factor": d16.effective_factor("L2", 94),
             "graph_seed": 2026094009, "block_seed": 2026094101}
    adapters = _fake_adapters()
    record = d16.run_l2_oracle_cell(
        graphs_l2[(94, 2026094009)], blocks[2026094101], entry,
        decode_fn=adapters["decode_fn"],
        syndrome_fn=adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=0)
    assert record["exact"] is True and record["graded"] is False
    assert record["oracle"] is True
    assert record["batch_id"] == d16.D16_BATCH_ID
    with pytest.raises(ValueError):
        d16.run_l2_oracle_cell(
            graphs_l2[(94, 2026094009)], blocks[2026094101], entry,
            decode_fn=adapters["decode_fn"],
            syndrome_fn=adapters["syndrome_fn"],
            oracle_prior_fn=None, call_idx=0)


def test_d16_nonadmitted_graph_blocks_with_zero_decoder_calls():
    calls = []
    adapters = _fake_adapters(calls)
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    broken = dict(graphs_l1[("L045", 125, 2026094001)])
    broken["admitted"] = False
    graphs_l1[("L045", 125, 2026094001)] = broken
    outcome = d16.execute_plan(
        d16.build_call_plan(), graphs_l1, graphs_l2, blocks,
        adapters["decode_fn"], adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 0
    assert calls == []
    assert "not admitted" in outcome["engineering_reason"]
    assert d16.route_terminal(
        _tallies(_full_cells(lambda arm, m: [0, 0, 0, 0])),
        outcome["engineering_reason"]) == d16.T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# Runner: refusal, writer, verifier, profile-only, fake authorized branch
# --------------------------------------------------------------------------- #
def test_d16_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    _assert_no_production_entry()
    target = tmp_path / "d16_no_auth"
    rc = runner.main(["--d16-batch", "--out-root", str(target)])
    assert rc == 2
    assert not target.exists()
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()


def test_d16_writer_never_overwrites(tmp_path):
    calls = []
    adapters = _fake_adapters(calls)
    target = tmp_path / "d16_root"
    bundle = runner.run_authorized_batch(
        str(target), d16.MODEL_F_INPUT_ROOT, adapters=adapters)
    summary = runner.write_batch_root(bundle)
    assert summary["scientific_calls"] == 96
    assert summary["setup_calls"] == 22
    assert sorted(p.name for p in target.iterdir()) == \
        sorted(d16.EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        runner.write_batch_root(bundle)  # never overwrite
    probe_calls = []
    with pytest.raises(FileExistsError):
        runner.run_authorized_batch(  # refuse probe before decoder calls
            str(target), d16.MODEL_F_INPUT_ROOT,
            adapters=_fake_adapters(probe_calls))
    assert probe_calls == []
    assert not FUTURE_ROOT.exists()


def test_d16_verify_roundtrip_and_fail_closed(tmp_path):
    adapters = _fake_adapters()
    target = tmp_path / "d16_verify"
    bundle = runner.run_authorized_batch(
        str(target), d16.MODEL_F_INPUT_ROOT, adapters=adapters)
    runner.write_batch_root(bundle)
    assert runner.verify_root(
        str(target), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is True
    (target / "arm_summary.csv").unlink()  # partial root
    assert runner.verify_root(
        str(target), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False


def test_d16_verify_fail_closed_on_isolation_and_blocked(tmp_path):
    adapters = _fake_adapters()
    target = tmp_path / "d16_isolation"
    bundle = runner.run_authorized_batch(
        str(target), d16.MODEL_F_INPUT_ROOT, adapters=adapters)
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
    blocked = tmp_path / "d16_blocked"
    graphs_l1, graphs_l2, blocks = _fake_graphs_blocks()
    broken = dict(graphs_l1[("L055", 125, 2026094005)])
    broken["admitted"] = False
    graphs_l1[("L055", 125, 2026094005)] = broken
    plan = d16.build_call_plan()
    outcome = d16.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["engineering_reason"] != ""
    bundle = runner.run_authorized_batch(
        str(blocked), d16.MODEL_F_INPUT_ROOT, adapters=adapters)
    bundle["records"] = outcome["records"]
    bundle["summary"] = dict(
        bundle["summary"],
        engineering_reason=outcome["engineering_reason"],
        terminal=d16.T_ENGINEERING_BLOCKED,
        scientific_calls=len(outcome["records"]))
    runner.write_batch_root(bundle)
    assert runner.verify_root(
        str(blocked), build_l1_fn=_fake_l1_graph,
        build_l2_fn=_fake_l2_graph) is False


def test_d16_profile_only_12_graphs():
    _assert_no_production_entry()
    report = runner.profile_only()
    assert report["total_graphs"] == 12
    assert report["admitted"] == 12
    assert report["replacement_seeds_used"] == 0
    assert report["frozen_seed_failures"] == []
    assert report["plan_calls"] == 96
    assert report["decoder_calls"] == 0
    assert report["future_root_absent"] is True
    assert not FUTURE_ROOT.exists()
    admissions = set()
    for entry in report["graphs"]:
        assert entry["E"] == d16.EDGE_TOTALS[
            "L2" if entry["arm"] == d16.ORACLE_ARM else entry["arm"]]
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
    return ["--d16-batch", "--execution-authorized",
            "--out-root", str(scratch)]


def test_d16_fake_authorized_true_branch_96(monkeypatch, scratch_root):
    _assert_no_production_entry()
    calls, loads = [], []
    adapters = _fake_adapters(calls, loads)
    binder_calls = _spy_on_binder(monkeypatch)
    rc = runner.main(_authorized_args(scratch_root),
                     adapters_override=adapters)
    assert rc == 0
    assert len(calls) == 96  # 64 L1 (L045+L055) + 32 ORACLE
    shapes = sorted(shape[0] for shape in calls)
    assert shapes.count(125) == 64
    assert shapes.count(94) == 32
    assert len(loads) == 1  # injected prior path ran exactly once
    assert binder_calls == []  # production binder never entered
    _assert_no_production_entry()
    assert sorted(p.name for p in scratch_root.iterdir()) == \
        sorted(d16.EVIDENCE_FILES)
    summary = json.loads((scratch_root / "summary.json").read_text("utf-8"))
    assert summary["setup_calls"] == 22  # 12 graphs + 8 blocks + 2 fixed
    assert summary["scientific_calls"] == 96
    assert summary["planned_calls"] == 96
    assert summary["terminal"] == d16.T_MATCHED_BACKOFF_SUFFICIENT  # all-exact fakes
    assert summary["engineering_reason"] == ""
    assert all(v == 32 for v in summary["pools"].values())
    plan = d16.build_call_plan()
    with open(scratch_root / "decoder_records.csv", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(plan) == 96
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
