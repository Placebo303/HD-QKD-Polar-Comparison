"""D19 L2 finite-ensemble validation — focused readiness tests (F06).

Zero production decoder/DE calls; no D19 batch, no APP/D7-H/real data.
Fake builders/adapters/blocks carry the suite except the 24-graph
admission + replay tests, which use the real frozen builders (setup-only,
no decoder). Fresh ``workspace/`` scratch roots; ``-p no:cacheprovider``.
"""
from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
import uuid
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RUNNER_PATH = ROOT / "scripts" / "v72p2d19_finite_development.py"
MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2d19_l2_finite.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d15_margin_curve as d15  # noqa: E402
import comparison_bench.formal_ir.v72p2d16_matched_backoff as d16  # noqa: E402
import comparison_bench.formal_ir.v72p2d19_l2_finite as d19  # noqa: E402
import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5  # noqa: E402

runner = _load_module("v72p2d19_runner_test", RUNNER_PATH)

#: Production entries that must never appear on any fake path: the v35
#: decoder module, the Model-F contrast loader module (both registered
#: names), and the R2-runner reuse keys (binder-only).
PRODUCTION_ABSENT_KEYS = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    "v72p2d10_r2_runner_reuse_d19",
    "v72p2d10_r2_runner_reuse_d16",
    "v72p2d10_r2_runner_reuse_d15",
    "v72p2d10_r2_runner_reuse_n14",
    "v72p2d10_r2_runner_reuse_d11",
)

FUTURE_ROOT = (ROOT / d19.FUTURE_ROOT).resolve()

FROZEN_COMMAND_LITERAL = (
    ".venv/bin/python scripts/v72p2d19_finite_development.py "
    "--d19-batch --execution-authorized --model-f-root "
    "workspace/v72p2d5_model_f_input/20260907_r1 --out-root "
    "workspace/d19_l2_finite_ensemble_"
    "5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b")


def _assert_no_production_entry():
    absent = [key for key in PRODUCTION_ABSENT_KEYS if key in sys.modules]
    assert absent == [], "production entry on fake path: %r" % (absent,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("d19_fake_authorized_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert path.resolve() != FUTURE_ROOT
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never Model-F content)
# --------------------------------------------------------------------------- #
def _fake_graph(arm, width, seed):
    n, m = int(width), d19.ROWS[int(width)]
    H = np.zeros((m, n), dtype=np.int64)
    for v in range(n):
        H[v % m, v] = 1
    return {"arm": arm, "width": int(width), "graph_seed": int(seed),
            "n": n, "m": m, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "status": "ok", "admitted": True,
            "failure_reason": ""}


def _fake_block(width, seed):
    n = int(width)
    return {"bob": np.zeros(n, dtype=np.int64),
            "u1": np.zeros(n, dtype=np.int64),
            "u2": np.zeros(n, dtype=np.int64),
            "prior": np.full((n, 32), 1.0 / 32.0)}


class _FakeResult:
    def __init__(self, n, exact):
        self.x_hat = np.zeros(n, dtype=np.uint8)
        if not exact:
            self.x_hat[0] = 1
        self.syndrome_ok = True
        self.iterations = 1
        self.status = "converged_exact" if exact else "converged_max_iter"
        self.belief_provenance = "CHECK_UPDATED"


def _scripted_adapters(script, calls=None, loads=None):
    """Fake adapters consuming an exact-outcome script in dispatch order."""
    calls = calls if calls is not None else []
    loads = loads if loads is not None else []
    outcomes = list(script)

    def fake_decode(H, prior, syn, **kw):
        calls.append(tuple(H.shape))
        assert outcomes, "script exhausted"
        return _FakeResult(H.shape[1], outcomes.pop(0))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        loads.append(str(root))
        return (None, None, None)

    def fake_sample(p_b, p_f, p1, seed, width):
        return _fake_block(width, seed)

    def fake_oracle(block):
        return block["prior"]

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "sample_fn": fake_sample,
            "oracle_prior_fn": fake_oracle, "build_fn": _fake_graph}


def _fake_graphs_blocks():
    graphs = {}
    for width in d19.WIDTHS:
        for arm in d19.ARMS:
            for seed in d19.GRAPH_SEEDS[int(width)]:
                graphs[(arm, int(width), int(seed))] = _fake_graph(
                    arm, width, seed)
    blocks = {int(w): {int(s): _fake_block(w, s)
                       for s in d19.BLOCK_SEEDS[int(w)]}
              for w in d19.WIDTHS}
    return graphs, blocks


def _script_for_width(l020_per_graph, dv3_per_graph, width):
    """Exact-outcome script in frozen dispatch order (graph→block→arm).

    First ``min`` shared blocks of each graph are exact on both arms, the
    next ``L020-min`` L020-only, the next ``DV3-min`` DV3-only.
    """
    script = []
    for l020_total, dv3_total in zip(l020_per_graph, dv3_per_graph):
        shared = min(l020_total, dv3_total)
        for i in range(8):
            dv3_ok = i < shared or (
                shared <= i < shared + (dv3_total - shared))
            l020_ok = i < shared or (
                shared <= i < shared + (l020_total - shared))
            script.extend([dv3_ok, l020_ok])  # arm order DV3, L020
    assert len(script) == 96
    return script


def _tagged(width, arm, graph_seed, block_seed, exact, syndrome=None,
            undetected=False):
    return {"call_idx": 0, "width": int(width), "arm": arm,
            "graph_seed": int(graph_seed), "block_seed": int(block_seed),
            "batch_id": d19.D19_BATCH_ID, "exact": exact,
            "syndrome_ok": exact if syndrome is None else syndrome,
            "undetected": undetected, "oracle": True, "graded": False}


def _records_for_width(width, l020_per_graph, dv3_per_graph):
    records = []
    for seed, l020_total, dv3_total in zip(
            d19.GRAPH_SEEDS[int(width)], l020_per_graph, dv3_per_graph):
        shared = min(l020_total, dv3_total)
        for i, block in enumerate(d19.BLOCK_SEEDS[int(width)]):
            dv3_ok = i < shared or (
                shared <= i < shared + (dv3_total - shared))
            l020_ok = i < shared or (
                shared <= i < shared + (l020_total - shared))
            records.append(_tagged(width, "DV3", seed, block, dv3_ok))
            records.append(_tagged(width, "L020", seed, block, l020_ok))
    return records


def _tally(m_g, c_g, b=None, c=None):
    m_g, c_g = list(m_g), list(c_g)
    if b is None or c is None:
        b = sum(a - min(a, d) for a, d in zip(m_g, c_g))
        c = sum(d - min(a, d) for a, d in zip(m_g, c_g))
    return {"width": 128, "M_g": m_g, "C_g": c_g,
            "M": sum(m_g), "C": sum(c_g), "b": b, "c": c}


# --------------------------------------------------------------------------- #
# F02/frozen tables: four cells, delta_L2, winner, no near-tie arm
# --------------------------------------------------------------------------- #
def test_d19_cells_exact():
    expected = {
        ("DV3", 128): ({3: 128}, {4: 86, 5: 8}, 384),
        ("L020", 128): ({2: 35, 3: 93}, {3: 27, 4: 67}, 349),
        ("DV3", 256): ({3: 256}, {4: 172, 5: 16}, 768),
        ("L020", 256): ({2: 70, 3: 186}, {3: 54, 4: 134}, 698),
    }
    for (arm, width), (var, chk, edges) in expected.items():
        cell = d19.degree_cell(arm, width)
        assert cell["var_counts"] == var
        assert cell["check_counts"] == chk
        assert cell["E"] == edges
        assert sum(var.values()) == width
        assert sum(chk.values()) == d19.ROWS[width]
        assert sum(d * c for d, c in var.items()) == edges
        assert sum(d * c for d, c in chk.items()) == edges
        assert cell["disclosed_bits"] == 5 * d19.ROWS[width]
    assert d19.DELTA_L2 == 0.44915511536562214
    assert d19.ROWS == {128: 94, 256: 188}


def test_d19_winner_provenance_and_no_near_tie():
    assert d19.WINNER_ID == "lam_d2_0.20_d3_0.80"
    assert d19.DV3_ID == "lam_d2_0.00_d3_1.00"
    assert d19.ARMS == ("DV3", "L020") and len(d19.ARMS) == 2
    assert d19.ARM_CANDIDATE == {"DV3": d19.DV3_ID, "L020": d19.WINNER_ID}
    for arm in d19.ARMS:
        for width in d19.WIDTHS:
            assert d19.ARM_CANDIDATE[arm] not in (
                "lam_d2_0.15_d3_0.85", "lam_d2_0.25_d3_0.75")


def test_d19_realized_deviations_exact_rationals():
    # F02 record: edge lambda2 = 70/349 (dev +1/1745); node L2 = 35/128
    # (dev +1/1408); check rho DV3 = 43/48, 5/48.
    assert Fraction(70, 349) - Fraction(1, 5) == Fraction(1, 1745)
    assert Fraction(35, 128) - Fraction(3, 11) == Fraction(1, 1408)
    assert Fraction(81, 349) + Fraction(268, 349) == 1
    assert Fraction(43, 48) + Fraction(5, 48) == 1
    cell = d19.degree_cell("L020", 128)
    var_e = sum(d * c for d, c in cell["var_counts"].items())
    assert Fraction(35 * 2, var_e) == Fraction(70, 349)
    dv3 = d19.degree_cell("DV3", 128)
    chk_e = sum(d * c for d, c in dv3["check_counts"].items())
    assert Fraction(86 * 4, chk_e) == Fraction(43, 48)
    assert Fraction(8 * 5, chk_e) == Fraction(5, 48)
    with pytest.raises(KeyError):
        d19.degree_cell("L015", 128)
    with pytest.raises(KeyError):
        d19.degree_cell("L020", 64)


# --------------------------------------------------------------------------- #
# reuse, not duplication; ORACLE-only boundary
# --------------------------------------------------------------------------- #
def test_d19_reuse_not_duplication():
    assert d19.DECODER_MAX_ITER == 90 and d19.DAMPING_ALPHA == 1.0
    assert d19.Q == 32 and d19.POLY == 37
    assert d19.MODEL_F_INPUT_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert d19.RSS_BUDGET_BYTES == r2.RSS_BUDGET_BYTES
    assert d19.build_degree_sequence_peg is r2.build_degree_sequence_peg
    assert d19.structural_record is r2.structural_record
    assert d19.dense_from_edges is r2.dense_from_edges
    assert d19.dispatch_l1 is r2.dispatch_l1
    assert d19.refuse_out_root is r2.refuse_out_root
    assert d19.sample_matched_block is d5.sample_matched_block
    assert d19.oracle_l2_prior is d5.oracle_l2_prior
    assert d19.wilson_interval is d15.wilson_interval
    assert d19.PRIOR_CHAIN == d15.PRIOR_CHAIN
    assert d19.DECODER_FLOOR == d5.DECODER_FLOOR == 1e-15
    # Own coefficient namespace (arm included — shared graph-seed labels
    # would collide under the D10 namespace), so it must NOT be the R2
    # helper; the primitive underneath stays shared.
    assert d19.coefficient_seed(128, "DV3", 2026094401) != \
        d19.coefficient_seed(128, "L020", 2026094401)
    assert "d19:l2:coeff" not in r2.coefficient_seed.__doc__


def test_d19_oracle_only_boundary():
    for path in (MODULE_PATH, RUNNER_PATH):
        source = path.read_text("utf-8")
        for token in ("canonical_transfer", "transfer_prior",
                      "app_fed", "transfer_fn", "transfer_parts",
                      "transfer_mixer", "app_source", "L2_APP",
                      "APP_ARM", "app_joint", "L045", "L055"):
            assert token not in source, (path.name, token)
    assert set(d19.ARMS) == {"DV3", "L020"}
    assert not hasattr(d19, "transfer_fn")
    assert not hasattr(runner, "APP_SOURCE_PROFILE")
    import inspect as _inspect
    assert "oracle_prior_fn" in _inspect.signature(
        d19.execute_plan).parameters
    assert "transfer_fn" not in _inspect.signature(
        d19.execute_plan).parameters
    assert "oracle_prior_fn" in _inspect.signature(
        d19.run_l2_oracle_call).parameters


# --------------------------------------------------------------------------- #
# 24 real graph admissions + replay (setup-only, no decoder)
# --------------------------------------------------------------------------- #
def test_d19_24_graph_admissions_real_builders():
    # Frozen outcome (readiness STOP record, no fix-up): 23/24 admitted.
    # n256/DV3/2026094408 dead-ends deterministically inside the accepted
    # R2 constructor ("no eligible check placement at variable 255 socket
    # 2"); zero replacement seeds, retained as a frozen-seed failure that
    # engineering-blocks the n256 leg before any n256 decoder call.
    assert len(d19.GRAPH_SEEDS[128]) == 6
    assert len(d19.GRAPH_SEEDS[256]) == 6
    admitted, failures = 0, []
    for width in d19.WIDTHS:
        for arm in d19.ARMS:
            for seed in d19.GRAPH_SEEDS[int(width)]:
                graph = d19.build_graph(arm, width, seed)
                if graph["admitted"]:
                    admitted += 1
                    assert graph["status"] == "ok"
                    assert graph["failure_reason"] == ""
                    admission = graph["structure"]["admission"]
                    assert len(admission) == 6  # A1-A6
                    assert all(admission.values())
                    assert graph["E"] == d19.EDGE_TOTALS[(arm, int(width))]
                else:
                    failures.append((width, arm, seed, graph["status"],
                                     graph["failure_reason"]))
    assert admitted == 23
    assert failures == [(256, "DV3", 2026094408, "construction_failed",
                         "no eligible check placement at variable 255 "
                         "socket 2")]
    # Deterministic retention: rebuild reproduces the identical failure.
    repeat = d19.build_graph("DV3", 256, 2026094408)
    assert repeat["status"] == "construction_failed"
    assert repeat["admitted"] is False
    assert repeat["failure_reason"] == failures[0][4]
    with pytest.raises(ValueError):
        d19.build_graph("DV3", 128, 2026094407)  # n256 label at n128


def test_d19_deterministic_replay_identity():
    first = d19.build_graph("L020", 128, 2026094401)
    second = d19.build_graph("L020", 128, 2026094401)
    assert first["edges"] == second["edges"]
    assert first["coefficients"] == second["coefficients"]
    assert d19.coefficients_for_edges(
        first["edges"], 128, "L020", 2026094401) == first["coefficients"]
    # Arm-namespaced streams differ across arms sharing the seed label.
    other = d19.coefficients_for_edges(
        first["edges"], 128, "DV3", 2026094401)
    assert other != first["coefficients"]


# --------------------------------------------------------------------------- #
# seeds: frozen values + disjointness
# --------------------------------------------------------------------------- #
def test_d19_frozen_seeds_exact_and_disjoint():
    assert d19.GRAPH_SEEDS[128] == tuple(range(2026094401, 2026094407))
    assert d19.GRAPH_SEEDS[256] == tuple(range(2026094407, 2026094413))
    assert d19.BLOCK_SEEDS[128] == tuple(range(2026094501, 2026094509))
    assert d19.BLOCK_SEEDS[256] == tuple(range(2026094511, 2026094519))
    graphs = {s for seeds in d19.GRAPH_SEEDS.values() for s in seeds}
    blocks = {s for seeds in d19.BLOCK_SEEDS.values() for s in seeds}
    assert len(graphs) == 12 and len(blocks) == 16
    assert graphs.isdisjoint(blocks)
    assert min(graphs) > 2026094308 and min(blocks) > 2026094308
    assert graphs.isdisjoint(set(d16.BLOCK_SEEDS))
    assert blocks.isdisjoint(
        {s for seeds in d16.GRAPH_SEEDS.values() for s in seeds})


def test_d19_live_provenance_subprocess():
    # Live cross-check in a child process: frozen winner/control strings
    # against d18.candidate_id_for_x/DV3_CONTROL_ID, and D19 seeds against
    # the full d18.collect_prior_seeds() sets + stage seeds. Subprocess so
    # no fake path ever imports the production-adjacent D18 chain.
    import subprocess
    lines = [
        "import sys",
        "sys.path.insert(0, 'comparison_bench/src')",
        "from comparison_bench.formal_ir import v72p2d18_l2_ensemble_de "
        "as d18",
        "from comparison_bench.formal_ir import v72p2d19_l2_finite as d19",
        "assert d19.WINNER_ID == d18.candidate_id_for_x(0.20) == "
        "'lam_d2_0.20_d3_0.80'",
        "assert d19.DV3_ID == d18.DV3_CONTROL_ID == 'lam_d2_0.00_d3_1.00'",
        "sets = d18.collect_prior_seeds()",
        "graphs = {s for seeds in d19.GRAPH_SEEDS.values() for s in seeds}",
        "blocks = {s for seeds in d19.BLOCK_SEEDS.values() for s in seeds}",
        "stage = set(d18.STAGE_S_SEEDS) | set(d18.STAGE_C_SEEDS)",
        "print('prior_max', max(sets['prior']), 'banned_max', "
        "max(sets['banned']), 'd17_max', max(sets['d17']), 'd9_max', "
        "max(sets['d9']), 'stage_max', max(stage))",
        "assert max(sets['prior']) <= 2026094308",
        "assert max(sets['banned']) <= 2026094308",
        "assert max(sets['d17']) <= 2026094308",
        "assert max(sets['d9']) <= 2026094308",
        "assert max(stage) <= 2026094308",
        "assert min(graphs) > 2026094308 and min(blocks) > 2026094308",
        "for _name in ('prior', 'banned', 'd17', 'd9'):",
        "    assert graphs.isdisjoint(sets[_name]), _name",
        "    assert blocks.isdisjoint(sets[_name]), _name",
        "assert graphs.isdisjoint(stage) and blocks.isdisjoint(stage)",
        "print('D19_LIVE_PROVENANCE_OK')",
    ]
    proc = subprocess.run(
        [sys.executable, "-c", "\n".join(lines)], cwd=str(ROOT),
        capture_output=True, text=True, timeout=300)
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0
    assert "D19_LIVE_PROVENANCE_OK" in proc.stdout


def test_d19_no_source_auth_or_replacement_mechanism():
    for path in (MODULE_PATH, RUNNER_PATH):
        source = path.read_text("utf-8")
        assert "REPLACEMENT_SEEDS" not in source, path.name
        assert "PROFILE_REPLACEMENT_SEEDS" not in source, path.name
    profile = d19.profile_graphs(build_fn=_fake_graph)
    assert profile["seed_replacements"] == []
    assert profile["replacement_seeds_used"] == 0


# --------------------------------------------------------------------------- #
# plan: order, pairing, geometry
# --------------------------------------------------------------------------- #
def test_d19_plan_order_pairing_geometry():
    plan = d19.build_call_plan((128, 256))
    assert len(plan) == 192
    assert [e["call_idx"] for e in plan] == list(range(192))
    pos = 0
    for width in (128, 256):
        for graph_seed in d19.GRAPH_SEEDS[width]:
            for block_seed in d19.BLOCK_SEEDS[width]:
                for arm in ("DV3", "L020"):
                    entry = plan[pos]
                    assert entry["width"] == width
                    assert entry["graph_seed"] == graph_seed
                    assert entry["block_seed"] == block_seed
                    assert entry["arm"] == arm
                    assert entry["role"] == d19.ARM_ROLE[arm]
                    assert entry["candidate_id"] == \
                        d19.ARM_CANDIDATE[arm]
                    assert entry["m"] == d19.ROWS[width]
                    assert entry["disclosed_bits"] == 5 * d19.ROWS[width]
                    pos += 1
    n128 = d19.build_call_plan((128,))
    assert len(n128) == 96
    assert [e["call_idx"] for e in n128] == list(range(96))
    # Shared labels + same blocks per width; arm-specific graphs only via
    # the degree cells (plan carries no edges).
    for width in (128, 256):
        arms_blocks = {
            arm: sorted(e["block_seed"] for e in plan
                        if e["width"] == width and e["arm"] == arm)
            for arm in d19.ARMS}
        assert arms_blocks["DV3"] == arms_blocks["L020"]
        assert sorted(set(arms_blocks["DV3"])) == \
            list(d19.BLOCK_SEEDS[width])
    with pytest.raises(KeyError):
        d19.build_call_plan((64,))


def test_d19_budgets_frozen():
    assert d19.SCIENTIFIC_CALL_CEILING == 192
    assert d19.SETUP_CALL_CEILING == 42
    assert d19.SETUP_FIXED_UNITS == 2
    assert d19.WALL_BUDGET_S == 1800.0
    assert d19.PER_CALL_BUDGET_S == 120.0
    assert d19.FROZEN_COMMAND == FROZEN_COMMAND_LITERAL
    assert d19.FUTURE_ROOT == (
        "workspace/d19_l2_finite_ensemble_"
        "5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b")
    assert not FUTURE_ROOT.exists()


# --------------------------------------------------------------------------- #
# gates: every edge (exact-only)
# --------------------------------------------------------------------------- #
def test_d19_gate_positive_all_five_clauses():
    tally = _tally([6] * 6, [2] * 6)  # M=36 C=12 b-c=24
    assert d19.classify_width(tally) == d19.POSITIVE
    assert d19.classify_width(tally, "boom") == d19.ENGINEERING_BLOCKED


def test_d19_gate_positive_boundaries():
    assert d19.classify_width(_tally([5] * 6, [1] * 6)) == d19.POSITIVE
    assert d19.classify_width(_tally([5, 5, 5, 5, 5, 4], [1] * 6)) \
        == d19.AMBIGUOUS  # M=29
    assert d19.classify_width(_tally([8, 8, 8, 8, 8, 0], [0] * 6)) \
        == d19.POSITIVE  # exactly 5/6 graphs >= 4 and won
    assert d19.classify_width(_tally([8, 8, 8, 8, 0, 0], [0] * 6)) \
        == d19.AMBIGUOUS  # only 4/6 graphs >= 4
    assert d19.classify_width(_tally([8] * 6, [0, 0, 0, 0, 8, 8])) \
        == d19.AMBIGUOUS  # only 4/6 strict wins
    assert d19.classify_width(_tally([5] * 6, [3] * 6)) == d19.POSITIVE
    assert d19.classify_width(_tally([5, 5, 5, 5, 5, 5],
                                     [3, 3, 3, 3, 3, 4])) == d19.AMBIGUOUS
    assert d19.classify_width(_tally([6] * 6, [3, 3, 3, 3, 4, 4])) \
        == d19.POSITIVE  # C=20
    assert d19.classify_width(_tally([6] * 6, [3, 3, 4, 4, 4, 3])) \
        == d19.AMBIGUOUS  # C=21, all else holds


def test_d19_gate_negative_both_clauses():
    assert d19.classify_width(_tally([3, 3, 3, 3, 2, 2],
                                     [2, 2, 2, 2, 2, 2])) == d19.NEGATIVE
    assert d19.classify_width(_tally([3, 3, 3, 3, 3, 2],
                                     [2, 2, 2, 2, 2, 2])) == d19.AMBIGUOUS
    assert d19.classify_width(_tally([4, 3, 3, 2, 2, 2],
                                     [2, 2, 2, 2, 2, 1])) == d19.AMBIGUOUS
    assert d19.classify_width(_tally([0] * 6, [0] * 6)) == d19.NEGATIVE


def test_d19_gate_rejects_malformed_tally():
    with pytest.raises(ValueError):
        d19.classify_width(_tally([8] * 5, [0] * 5))
    with pytest.raises(ValueError):
        d19.classify_width(dict(_tally([8] * 6, [0] * 6), M=1))


# --------------------------------------------------------------------------- #
# tallies: exact-only derivation + paired b/c + predecessor boundary
# --------------------------------------------------------------------------- #
def test_d19_tally_exact_only_and_paired_bc():
    records = _records_for_width(128, [6] * 6, [2] * 6)
    tally = d19.width_tally(records, 128)
    assert tally["M_g"] == [6] * 6 and tally["C_g"] == [2] * 6
    assert (tally["M"], tally["C"]) == (36, 12)
    assert (tally["b"], tally["c"]) == (24, 0)
    assert d19.classify_width(tally) == d19.POSITIVE


def test_d19_tally_rejects_predecessor_and_mistagged():
    records = _records_for_width(128, [6] * 6, [2] * 6)
    bad = [dict(r, batch_id=d16.D16_BATCH_ID) for r in records]
    with pytest.raises(ValueError):
        d19.width_tally(bad, 128)
    bad = [dict(r, graded=True) for r in records]
    with pytest.raises(ValueError):
        d19.width_tally(bad, 128)
    with pytest.raises(ValueError):
        d19.width_tally(records[:-2], 128)  # zero-skip
    with pytest.raises(ValueError):
        d19.width_tally(records, 256)  # wrong width


# --------------------------------------------------------------------------- #
# dispatch: ORACLE tagging, isolation, admission gate, no retry
# --------------------------------------------------------------------------- #
def test_d19_dispatch_oracle_tag_and_isolation():
    graphs, blocks = _fake_graphs_blocks()
    entry = d19.build_call_plan((128,))[1]  # L020 arm
    adapters = _scripted_adapters([True])
    record = d19.run_l2_oracle_call(
        graphs[("L020", 128, 2026094401)], blocks[128][2026094501],
        entry, decode_fn=adapters["decode_fn"],
        syndrome_fn=adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=7)
    assert record["exact"] is True and record["syndrome_ok"] is True
    assert record["oracle"] is True and record["graded"] is False
    assert record["belief_provenance"] == "ORACLE"
    assert record["batch_id"] == d19.D19_BATCH_ID
    assert record["layer"] == "L2"
    assert record["target_exact"] is True and record["source_exact"] is False
    assert record["undetected"] is False
    assert record["call_idx"] == 7
    # Syndrome-valid but inexact never counts as exact at the gate.
    adapters = _scripted_adapters([False])
    miss = d19.run_l2_oracle_call(
        graphs[("DV3", 128, 2026094401)], blocks[128][2026094501],
        d19.build_call_plan((128,))[0], decode_fn=adapters["decode_fn"],
        syndrome_fn=adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=0)
    assert miss["exact"] is False and miss["syndrome_ok"] is True
    tally = d19.width_tally(
        [dict(r, exact=False, syndrome_ok=True)
         for r in _records_for_width(128, [0] * 6, [0] * 6)], 128)
    assert tally["M"] == 0 and d19.classify_width(tally) == d19.NEGATIVE


def test_d19_dispatch_refuses_nonadmitted_without_call():
    calls: list = []
    adapters = _scripted_adapters([True], calls)
    graph = _fake_graph("L020", 128, 2026094401)
    graph["admitted"] = False
    with pytest.raises(r2.StructureNotAdmitted):
        d19.run_l2_oracle_call(
            graph, _fake_block(128, 2026094501),
            d19.build_call_plan((128,))[1],
            decode_fn=adapters["decode_fn"],
            syndrome_fn=adapters["syndrome_fn"],
            oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=0)
    assert calls == []
    with pytest.raises(ValueError):
        d19.run_l2_oracle_call(
            _fake_graph("L020", 128, 2026094401),
            _fake_block(128, 2026094501),
            d19.build_call_plan((128,))[1], decode_fn=None,
            syndrome_fn=adapters["syndrome_fn"],
            oracle_prior_fn=adapters["oracle_prior_fn"], call_idx=0)


def test_d19_n256_dispatch_conditional():
    graphs, blocks = _fake_graphs_blocks()
    plan_n128 = d19.build_call_plan((128,))
    plan_n256 = d19.build_call_plan((256,))
    # POSITIVE n128 -> n256 dispatched (192 calls).
    script = _script_for_width([6] * 6, [2] * 6, 128)
    script += _script_for_width([6] * 6, [2] * 6, 256)
    adapters = _scripted_adapters(script)
    outcome = d19.execute_plan(
        plan_n128, plan_n256, graphs, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 192
    assert outcome["n256_dispatched"] is True
    assert outcome["terminal"] == d19.T_SIGNAL_REPRODUCED
    # NEGATIVE n128 -> n256 never dispatched (96 calls).
    adapters = _scripted_adapters(_script_for_width([0] * 6, [0] * 6, 128))
    outcome = d19.execute_plan(
        plan_n128, plan_n256, graphs, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 96
    assert outcome["n256_dispatched"] is False
    assert outcome["terminal"] == d19.T_NO_USEFUL_RECOVERY
    # AMBIGUOUS n128 -> n256 never dispatched.
    adapters = _scripted_adapters(
        _script_for_width([5, 5, 5, 5, 5, 4], [1] * 6, 128))
    outcome = d19.execute_plan(
        plan_n128, plan_n256, graphs, blocks, adapters["decode_fn"],
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["n256_dispatched"] is False
    assert outcome["terminal"] == d19.T_AMBIGUOUS


def test_d19_terminals_all_four():
    neg = {"width": 128, "classification": d19.NEGATIVE,
           "engineering_reason": ""}
    pos = {"width": 128, "classification": d19.POSITIVE,
           "engineering_reason": ""}
    amb = {"width": 128, "classification": d19.AMBIGUOUS,
           "engineering_reason": ""}
    blk = {"width": 128, "classification": d19.ENGINEERING_BLOCKED,
           "engineering_reason": "x"}
    pos256 = {"width": 256, "classification": d19.POSITIVE,
              "engineering_reason": ""}
    neg256 = {"width": 256, "classification": d19.NEGATIVE,
              "engineering_reason": ""}
    amb256 = {"width": 256, "classification": d19.AMBIGUOUS,
              "engineering_reason": ""}
    assert d19.route_terminal(pos, pos256) == d19.T_SIGNAL_REPRODUCED
    assert d19.route_terminal(neg) == d19.T_NO_USEFUL_RECOVERY
    assert d19.route_terminal(pos, neg256) == d19.T_NO_USEFUL_RECOVERY
    assert d19.route_terminal(amb) == d19.T_AMBIGUOUS
    assert d19.route_terminal(pos, amb256) == d19.T_AMBIGUOUS
    assert d19.route_terminal(blk) == d19.T_ENGINEERING_BLOCKED
    assert d19.route_terminal(pos) == d19.T_ENGINEERING_BLOCKED


def test_d19_engineering_blocks_with_zero_decoder_calls():
    graphs, blocks = _fake_graphs_blocks()
    graphs[("L020", 128, 2026094403)]["admitted"] = False
    calls: list = []
    adapters = _scripted_adapters([True] * 192, calls)
    outcome = d19.execute_plan(
        d19.build_call_plan((128,)), d19.build_call_plan((256,)),
        graphs, blocks, adapters["decode_fn"], adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 0
    assert outcome["n256_dispatched"] is False
    assert outcome["terminal"] == d19.T_ENGINEERING_BLOCKED
    assert outcome["width_results"][0]["engineering_reason"] != ""


def test_d19_real_builders_n256_blocked_zero_n256_calls():
    # Frozen-contract end to end with real graphs + fake decoder: n128 is
    # fully admitted and POSITIVE, yet the retained n256/DV3/2026094408
    # construction failure engineering-blocks before any n256 decoder call.
    graphs = {}
    for width in d19.WIDTHS:
        for arm in d19.ARMS:
            for seed in d19.GRAPH_SEEDS[int(width)]:
                graphs[(arm, int(width), int(seed))] = d19.build_graph(
                    arm, width, seed)
    blocks = {int(w): {int(s): _fake_block(w, s)
                       for s in d19.BLOCK_SEEDS[int(w)]}
              for w in d19.WIDTHS}
    calls: list = []
    adapters = _scripted_adapters(
        _script_for_width([6] * 6, [2] * 6, 128), calls)
    outcome = d19.execute_plan(
        d19.build_call_plan((128,)), d19.build_call_plan((256,)),
        graphs, blocks, adapters["decode_fn"], adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 96
    assert len(calls) == 96  # zero n256 decoder calls
    assert outcome["n256_dispatched"] is False
    assert outcome["terminal"] == d19.T_ENGINEERING_BLOCKED
    assert "2026094408" in outcome["width_results"][1]["engineering_reason"]


def test_d19_decoder_crash_retained_never_retried():
    graphs, blocks = _fake_graphs_blocks()

    def boom(H, prior, syn, **kw):
        raise RuntimeError("synthetic crash")

    adapters = _scripted_adapters([])
    outcome = d19.execute_plan(
        d19.build_call_plan((128,)), None, graphs, blocks, boom,
        adapters["syndrome_fn"],
        oracle_prior_fn=adapters["oracle_prior_fn"])
    assert outcome["decoder_calls"] == 1
    assert outcome["records"][0]["crash"] is True
    assert outcome["terminal"] == d19.T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# runner: refusal, never-overwrite, fake authorized runs, verifier
# --------------------------------------------------------------------------- #
def test_d19_unauthorized_batch_refuses_before_write_or_bind(tmp_path):
    _assert_no_production_entry()
    target = tmp_path / "d19_no_auth"
    rc = runner.main(["--d19-batch", "--out-root", str(target)])
    assert rc == 2
    assert not target.exists()
    _assert_no_production_entry()
    assert not FUTURE_ROOT.exists()


def test_d19_writer_never_overwrites(tmp_path):
    script = _script_for_width([6] * 6, [2] * 6, 128)
    script += _script_for_width([6] * 6, [2] * 6, 256)
    adapters = _scripted_adapters(script)
    target = tmp_path / "d19_root"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT, adapters=adapters)
    summary = runner.write_batch_root(bundle)
    assert summary["scientific_calls"] == 192
    assert summary["setup_calls"] == 42
    assert summary["terminal"] == d19.T_SIGNAL_REPRODUCED
    assert summary["n256_dispatched"] is True
    assert sorted(p.name for p in target.iterdir()) == \
        sorted(d19.EVIDENCE_FILES)
    with pytest.raises(FileExistsError):
        runner.write_batch_root(bundle)  # never overwrite
    probe_calls: list = []
    with pytest.raises(FileExistsError):
        runner.run_authorized_batch(  # refuse probe before decoder calls
            str(target), d19.MODEL_F_INPUT_ROOT,
            adapters=_scripted_adapters([], probe_calls))
    assert probe_calls == []
    assert not FUTURE_ROOT.exists()


def test_d19_fake_negative_run_n128_only_and_verify(tmp_path):
    adapters = _scripted_adapters(
        _script_for_width([0] * 6, [0] * 6, 128))
    target = tmp_path / "d19_negative"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT, adapters=adapters)
    summary = runner.write_batch_root(bundle)
    assert summary["scientific_calls"] == 96
    assert summary["terminal"] == d19.T_NO_USEFUL_RECOVERY
    assert summary["n256_dispatched"] is False
    assert runner.verify_root(str(target), build_fn=_fake_graph) is True


def test_d19_fake_ambiguous_run_and_verify(tmp_path):
    adapters = _scripted_adapters(
        _script_for_width([5, 5, 5, 5, 5, 4], [1] * 6, 128))
    target = tmp_path / "d19_ambiguous"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT, adapters=adapters)
    runner.write_batch_root(bundle)
    assert bundle["summary"]["terminal"] == d19.T_AMBIGUOUS
    assert runner.verify_root(str(target), build_fn=_fake_graph) is True


def test_d19_verify_roundtrip_and_fail_closed(tmp_path):
    script = _script_for_width([6] * 6, [2] * 6, 128)
    script += _script_for_width([6] * 6, [2] * 6, 256)
    target = tmp_path / "d19_verify"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT,
        adapters=_scripted_adapters(script))
    runner.write_batch_root(bundle)
    assert runner.verify_root(str(target), build_fn=_fake_graph) is True
    (target / "arm_summary.csv").unlink()  # partial root
    assert runner.verify_root(str(target), build_fn=_fake_graph) is False


def test_d19_verify_fail_closed_on_isolation_and_blocked(tmp_path):
    script = _script_for_width([6] * 6, [2] * 6, 128)
    script += _script_for_width([6] * 6, [2] * 6, 256)
    target = tmp_path / "d19_isolation"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT,
        adapters=_scripted_adapters(script))
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
    assert runner.verify_root(str(target), build_fn=_fake_graph) is False
    # Engineering-blocked roots fail closed even when internally coherent.
    target2 = tmp_path / "d19_blocked"
    bad_graphs, _blocks = _fake_graphs_blocks()
    bad_graphs[("DV3", 256, 2026094407)]["admitted"] = False
    scripted = _script_for_width([6] * 6, [2] * 6, 128)
    scripted += _script_for_width([6] * 6, [2] * 6, 256)
    adapters = _scripted_adapters(scripted)
    adapters["build_fn"] = lambda arm, width, seed: bad_graphs[
        (arm, int(width), int(seed))]
    bundle = runner.run_authorized_batch(
        str(target2), d19.MODEL_F_INPUT_ROOT, adapters=adapters)
    assert bundle["summary"]["terminal"] == d19.T_ENGINEERING_BLOCKED
    runner.write_batch_root(bundle)
    assert runner.verify_root(str(target2),
                              build_fn=adapters["build_fn"]) is False


def test_d19_verify_rejects_tampered_terminal(tmp_path):
    adapters = _scripted_adapters(
        _script_for_width([0] * 6, [0] * 6, 128))
    target = tmp_path / "d19_tamper"
    bundle = runner.run_authorized_batch(
        str(target), d19.MODEL_F_INPUT_ROOT, adapters=adapters)
    runner.write_batch_root(bundle)
    summary_path = target / "summary.json"
    import json as _json
    summary = _json.loads(summary_path.read_text("utf-8"))
    summary["terminal"] = d19.T_SIGNAL_REPRODUCED  # tampered gate outcome
    summary_path.write_text(_json.dumps(summary), encoding="utf-8")
    assert runner.verify_root(str(target), build_fn=_fake_graph) is False


def test_d19_profile_only_24_graphs_no_decoder_no_root(capsys):
    _assert_no_production_entry()
    report = runner.profile_only()
    assert report["total_graphs"] == 24
    assert report["admitted"] == 23  # frozen n256/DV3/2026094408 retained
    assert len(report["frozen_seed_failures"]) == 1
    assert report["frozen_seed_failures"][0]["seed"] == 2026094408
    assert report["seed_replacements"] == []
    assert report["replacement_seeds_used"] == 0
    assert report["plan_calls"] == 192
    assert report["plan_per_width"] == {"n128": 96, "n256": 96}
    assert report["decoder_calls"] == 0
    assert report["future_root_absent"] is True
    assert len(report["per_cell"]) == 24
    assert not FUTURE_ROOT.exists()
    _assert_no_production_entry()
    rc = runner.main(["--profile-only"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"decoder_calls": 0' in out
    assert not FUTURE_ROOT.exists()
