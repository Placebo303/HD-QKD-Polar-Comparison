"""R23b weak-prior retest — focused readiness tests (FAKE only).

Track EXPLORE-readiness: zero decoder calls; no weak batch execution, no
R23 graph builds (fake builders carry the suite), no real data (the only
npz touched is a synthetic diagonal fixture written to scratch, never the
frozen Model-F root). Fresh ``workspace/`` scratch roots;
``-p no:cacheprovider``.
"""
from __future__ import annotations

import importlib.util
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

RUNNER_PATH = ROOT / "scripts" / "v72p2r23_scale_weak.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d5_model_f_input as d5  # noqa: E402
import comparison_bench.formal_ir.v72p2r23_scale as r23  # noqa: E402

w23b = _load_module("v72p2r23_scale_weak_test", RUNNER_PATH)

#: Zero-decoder-call proof: wrap the production kernels with counting
#: shims at session start — any production decode/syndrome call fails
#: every fake-path test below (E23bb-calls must stay 0).
import comparison_bench.formal_ir.v35_algorithm_development as _v35  # noqa: E402

_CALL_COUNT = {"decode": 0, "syndrome": 0}
_orig_decode = _v35.decode_row_layered_fftqspa
_orig_syndrome = _v35.syndrome_of_gf32


def _counting_decode(*args, **kwargs):
    _CALL_COUNT["decode"] += 1
    return _orig_decode(*args, **kwargs)


def _counting_syndrome(*args, **kwargs):
    _CALL_COUNT["syndrome"] += 1
    return _orig_syndrome(*args, **kwargs)


_v35.decode_row_layered_fftqspa = _counting_decode
_v35.syndrome_of_gf32 = _counting_syndrome

FUTURE_ROOT = (ROOT / w23b.FUTURE_ROOT).resolve()
FAKE_MARGINAL = np.full(32, 1.0 / 32, dtype=np.float64)


def _assert_no_production_entry():
    assert _CALL_COUNT == {"decode": 0, "syndrome": 0}, \
        "production kernel called on fake path: %r" % (_CALL_COUNT,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("r23b_weak_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert path.resolve() != FUTURE_ROOT
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def prior_dir():
    path = ROOT / "workspace" / ("r23b_weak_priorfake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never the real Model-F root)
# --------------------------------------------------------------------------- #
def _fake_graph(width, ratio, seed, *, admitted=True):
    n = int(width)
    m = r23.ROWS[(n, ratio)]
    H = np.zeros((m, n), dtype=np.int64)
    for v in range(n):
        H[v % m, v] = 1
    return {"arm": w23b.ARM, "width": n, "ratio": ratio,
            "graph_seed": int(seed), "n": n, "m": m,
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": bool(admitted),
            "failure_reason": "" if admitted else "fake non-admit"}


def _fake_build_fn(width, ratio, seed):
    return _fake_graph(width, ratio, seed)


def _fake_graph_s(width, ratio, seed, *, admitted=True):
    """S-stamped fake graph (like the production R23 builder per REUSE)."""
    graph = _fake_graph(width, ratio, seed, admitted=admitted)
    graph["arm"] = r23.ARM
    return graph


def _fake_build_fn_s(width, ratio, seed):
    return _fake_graph_s(width, ratio, seed)


def _fake_sample_fn(width, ratio, seed):
    return r23.sample_oracle_block(width, ratio, seed)


def _fake_syndrome_fn(matrix, vector):
    H = np.asarray(matrix)
    return np.zeros(H.shape[0], dtype=np.uint8)


class _FakeResult:
    def __init__(self, x_hat, provenance="FAKE-WEAK-SCRIPT"):
        self.x_hat = np.asarray(x_hat, dtype=np.uint8)
        self.syndrome_ok = True
        self.iterations = 1
        self.status = "fake_converged"
        self.belief_provenance = provenance


def _scripted_decode(u_iter, modes_iter, marginal):
    """Fake decoder: pops truth+mode per call in plan order.

    Proves the decode path feeds the tiled weak marginal (exact tile
    equality asserted on every call) under the cold 90/1.0 contract.
    """
    def fn(matrix, prior, syndromes, **kwargs):
        assert kwargs.get("max_iter") == 90
        assert kwargs.get("damping_alpha") == 1.0
        assert kwargs.get("warm_beliefs") is None
        n = int(np.asarray(matrix).shape[1])
        assert np.array_equal(np.asarray(prior, dtype=np.float64),
                              np.tile(np.asarray(marginal).ravel(),
                                      (n, 1)))
        u = np.asarray(next(u_iter), dtype=np.uint8)
        mode = next(modes_iter)
        x_hat = u if mode else (u + 1) % 32
        return _FakeResult(x_hat)

    return fn


def _fake_adapters(decode_fn):
    return {"decode_fn": decode_fn, "syndrome_fn": _fake_syndrome_fn,
            "sample_fn": _fake_sample_fn, "build_fn": _fake_build_fn}


def _plan_truth_and_modes(plan, modes):
    """Truth vectors in plan order (deterministic sampler) + mode list."""
    assert len(modes) == len(plan)
    blocks = {}
    for entry in plan:
        key = (int(entry["width"]), str(entry["ratio"]))
        blocks.setdefault(key, {})[int(entry["block_seed"])] = \
            r23.sample_oracle_block(int(entry["width"]), str(entry["ratio"]),
                                    int(entry["block_seed"]))
    u_list = [blocks[(int(e["width"]), str(e["ratio"]))][
        int(e["block_seed"])]["u"] for e in plan]
    return u_list, list(modes)


def _write_fake_root(root, plan, modes, marginal):
    u_list, mode_list = _plan_truth_and_modes(plan, modes)
    decode_fn = _scripted_decode(iter(u_list), iter(mode_list), marginal)
    bundle = w23b.run_authorized_batch(
        str(root), adapters=_fake_adapters(decode_fn),
        marginal_32=np.asarray(marginal, dtype=np.float64))
    return w23b.write_batch_root(bundle)


def _write_fake_root_with_build(root, plan, modes, marginal, build_fn):
    """Fake root with an explicit graph builder (e.g. S-stamped)."""
    u_list, mode_list = _plan_truth_and_modes(plan, modes)
    decode_fn = _scripted_decode(iter(u_list), iter(mode_list), marginal)
    adapters = _fake_adapters(decode_fn)
    adapters["build_fn"] = build_fn
    bundle = w23b.run_authorized_batch(
        str(root), adapters=adapters,
        marginal_32=np.asarray(marginal, dtype=np.float64))
    return w23b.write_batch_root(bundle)


def _write_synthetic_prior(prior_dir):
    """Valid synthetic Model-F fixture: diagonal counts (no real payload)."""
    counts = (np.eye(1024, dtype=np.int64) * 256)
    assert int(counts.sum()) == 262144
    p_b = np.full(1024, 1.0 / 1024, dtype=np.float64)
    return d5.write_model_f_input(str(prior_dir), counts, p_b)


# --------------------------------------------------------------------------- #
# W1: prior path — Model-F marginal loads on a synthetic fixture
# --------------------------------------------------------------------------- #
def test_w1_marginal_loads_on_synthetic_npz(prior_dir):
    _write_synthetic_prior(prior_dir)
    marginal = w23b.load_weak_marginal(str(prior_dir))
    assert marginal.shape == (32,)
    assert np.all(np.isfinite(marginal)) and np.all(marginal > 0.0)
    assert float(marginal.sum()) == pytest.approx(1.0)
    # Diagonal fixture -> uniform Bob marginal -> uniform U2 marginal.
    assert np.allclose(marginal, 1.0 / 32)
    tiled = w23b.weak_prior_for_block(128, marginal)
    assert tiled.shape == (128, 32)
    assert np.all(tiled == tiled[0])  # no per-position truth information
    assert np.allclose(tiled.sum(axis=1), 1.0)
    # Same artifact path as R9 (read-only D5 loader).
    assert w23b.FROZEN_PRIOR_ROOT == r2.MODEL_F_INPUT_ROOT
    assert w23b.FROZEN_PRIOR_ROOT == d5.MODEL_F_FORMAL_ROOT
    _assert_no_production_entry()


def test_w1_marginal_rejects_tampered_npz(prior_dir):
    _write_synthetic_prior(prior_dir)
    np.savez_compressed(str(prior_dir / d5.NPZ_NAME),
                        counts_ab=np.zeros((4, 4), dtype=np.int64),
                        p_b=np.zeros(4))
    with pytest.raises(ValueError):
        w23b.load_weak_marginal(str(prior_dir))
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W2: decode path — weak prior in, NO ORACLE token out (hard fail)
# --------------------------------------------------------------------------- #
def test_w2_oracle_token_hard_fails():
    graph = _fake_graph(128, "r65", r23.GRAPH_SEEDS[(128, "r65")][0])
    block = r23.sample_oracle_block(128, "r65", 2026094885)
    entry = {"width": 128, "n": 128, "m": 83, "ratio": "r65",
             "arm": w23b.ARM, "graph_seed": graph["graph_seed"],
             "block_seed": 2026094885,
             "disclosed_bits": r23.disclosed_bits(83)}

    def _leak_decode(matrix, prior, syndromes, **kwargs):
        return _FakeResult(np.zeros(128, dtype=np.uint8),
                           provenance="ORACLE-SNEAK")

    def _leak_decode_lower(matrix, prior, syndromes, **kwargs):
        return _FakeResult(np.zeros(128, dtype=np.uint8),
                           provenance="oracle")

    for leak in (_leak_decode, _leak_decode_lower):
        with pytest.raises(AssertionError):
            w23b.run_w_weak_call(
                graph, block, FAKE_MARGINAL, entry, decode_fn=leak,
                syndrome_fn=_fake_syndrome_fn, call_idx=0)
    _assert_no_production_entry()


def test_w2_weak_call_ignores_oracle_rows():
    graph = _fake_graph(128, "r65", r23.GRAPH_SEEDS[(128, "r65")][0])
    block = r23.sample_oracle_block(128, "r65", 2026094885)
    del block["prior"]  # decode path must not need oracle rows at all
    entry = {"width": 128, "n": 128, "m": 83, "ratio": "r65",
             "arm": w23b.ARM, "graph_seed": graph["graph_seed"],
             "block_seed": 2026094885,
             "disclosed_bits": r23.disclosed_bits(83)}
    u_list = [np.asarray(block["u"])]
    record = w23b.run_w_weak_call(
        graph, block, FAKE_MARGINAL, entry,
        decode_fn=_scripted_decode(iter(u_list), iter([True]),
                                   FAKE_MARGINAL),
        syndrome_fn=_fake_syndrome_fn, call_idx=0)
    assert record["batch_id"] == w23b.R23B_BATCH_ID
    assert record["oracle"] is False
    assert record["belief_provenance"] == w23b.WEAK_PROVENANCE
    assert "ORACLE" not in record["belief_provenance"]
    assert record["exact"] is True and record["syndrome_ok"] is True
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W3: gate — calibration guard, then the frozen R23c-R1 text
# --------------------------------------------------------------------------- #
def test_w3_gate_calibration_and_frozen_edges():
    g = w23b.route_weak_gate
    assert g(8, 4, 0) == w23b.WIN       # hi>=6/16 and gap>=+4/16
    assert g(6, 2, 0) == w23b.WIN       # boundary WIN
    assert g(6, 4, 0) == w23b.DEAD      # gap +2 < +4/16
    assert g(16, 4, 0) == w23b.WIN      # lo at the guard boundary: no trip
    assert g(8, 5, 0) == w23b.STOP      # calibration trip beats WIN
    assert g(16, 16, 0) == w23b.STOP    # calibration trip beats frozen DEAD
    assert r23.route_scaling_gate(16, 16, 0) == r23.DEAD  # frozen text intact
    assert g(2, 0, 0) == w23b.DEAD      # hi <= 2/16
    assert g(6, 3, 0) == w23b.DEAD      # gap +3 < +4
    assert g(5, 0, 0) == w23b.INCONCLUSIVE
    assert g(4, 0, 0) == w23b.INCONCLUSIVE
    assert g(8, 4, 1) == w23b.STOP      # undetected > 0 absolute
    assert g(8, 4, 0, "boom") == w23b.STOP
    with pytest.raises(ValueError):
        g(17, 0, 0)
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W4: refusal / no-overwrite (rc2 no-write, extension gate, protected)
# --------------------------------------------------------------------------- #
def test_w4_refusal_missing_grant_zero_calls(scratch_root):
    rc = w23b.main(["--weak-batch", "--out-root", str(scratch_root)])
    assert rc == 2
    assert not scratch_root.exists()
    _assert_no_production_entry()


def test_w4_refusal_extension_without_second_grant(scratch_root):
    rc = w23b.main(["--weak-batch", "--include-r72",
                    "--execution-authorized",
                    "--out-root", str(scratch_root)])
    assert rc == 2
    assert not scratch_root.exists()
    _assert_no_production_entry()


def test_w4_refusal_existing_root_zero_calls(scratch_root):
    scratch_root.mkdir(parents=True)
    u_list, mode_list = _plan_truth_and_modes(
        w23b.build_weak_plan(), [True] * 32)
    with pytest.raises(FileExistsError):
        w23b.run_authorized_batch(
            str(scratch_root),
            adapters=_fake_adapters(
                _scripted_decode(iter(u_list), iter(mode_list),
                                 FAKE_MARGINAL)),
            marginal_32=FAKE_MARGINAL)
    _assert_no_production_entry()


def test_w4_refusal_protected_roots():
    # Existing R23 / prior roots: refusal fires as FileExistsError (never
    # overwrite); non-existent protected subtrees fire as ValueError.
    with pytest.raises((ValueError, FileExistsError)):
        w23b.refuse_out_root(
            "workspace/r23_scale_a3f1c9d2-4b7e-4f2a-9e1d-8c5f6a7b9d0e")
    with pytest.raises((ValueError, FileExistsError)):
        w23b.refuse_out_root("workspace/v72p2d5_model_f_input/20260907_r1")
    with pytest.raises(ValueError):
        w23b.refuse_out_root(
            "workspace/v72p2d5_model_f_input/20260907_r1_evil")
    with pytest.raises(ValueError):
        w23b.refuse_out_root("comparison_bench/outputs_comparison/w23b_x")
    with pytest.raises(ValueError):
        w23b.refuse_out_root("results/w23b_x")
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W5: verifier — fake batches PASS; tamper FAILs; gate isolation
# --------------------------------------------------------------------------- #
def test_w5_verifier_pass_win_batch(scratch_root):
    plan = w23b.build_weak_plan()
    assert len(plan) == 32
    # 1024:r65 -> 8/16 (g0 exact, g1 dead); 128:r65 -> 4/16: WIN, no trip.
    modes = ([True] * 4 + [False] * 4 + [False] * 8
             + [True] * 8 + [False] * 8)
    summary = _write_fake_root(scratch_root, plan, modes, FAKE_MARGINAL)
    assert summary["terminal"] == w23b.WIN
    assert summary["per_cell"]["1024:r65"]["E"] == 8
    assert summary["per_cell"]["1024:r65"]["E_g"] == [8, 0]
    assert summary["per_cell"]["128:r65"]["E"] == 4
    assert summary["calibration"]["tripped"] is False
    assert summary["scientific_calls"] == 32
    assert summary["setup_graphs"] == 4
    assert summary["undetected_count"] == 0
    assert w23b.verify_root(str(scratch_root),
                            build_fn=_fake_build_fn) is True
    _assert_no_production_entry()


def test_w5_verifier_pass_calibration_stop(scratch_root):
    plan = w23b.build_weak_plan()
    summary = _write_fake_root(scratch_root, plan, [True] * 32,
                               FAKE_MARGINAL)
    # Uniform-exact fake: anchors 16/16 -> calibration trip STOP.
    assert summary["terminal"] == w23b.STOP
    assert summary["calibration"]["tripped"] is True
    assert summary["calibration"]["e_lo_128_r65"] == 16
    assert w23b.verify_root(str(scratch_root),
                            build_fn=_fake_build_fn) is True
    _assert_no_production_entry()


def test_w5_verifier_tamper_fails(scratch_root):
    plan = w23b.build_weak_plan()
    modes = ([True] * 4 + [False] * 4 + [False] * 8
             + [True] * 8 + [False] * 8)
    _write_fake_root(scratch_root, plan, modes, FAKE_MARGINAL)
    import csv as _csv

    def _rewrite(rows):
        path = scratch_root / "decoder_records.csv"
        with open(path, encoding="utf-8", newline="") as fh:
            original = list(_csv.DictReader(fh))
        assert rows(original)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = _csv.DictWriter(fh, fieldnames=list(original[0].keys()))
            writer.writeheader()
            writer.writerows(original)

    def _tamper_exact_without_syndrome(rows):
        rows[0]["exact"] = "True"
        rows[0]["syndrome_ok"] = "False"
        return True

    def _tamper_undetected_merged(rows):
        rows[1]["undetected"] = "True"
        rows[1]["exact"] = "True"
        return True

    def _tamper_provenance(rows):
        rows[2]["belief_provenance"] = "ORACLE-SNEAK"
        return True

    for tamper in (_tamper_exact_without_syndrome, _tamper_undetected_merged,
                   _tamper_provenance):
        _rewrite(tamper)
        assert w23b.verify_root(str(scratch_root),
                                build_fn=_fake_build_fn) is False
        # restore the good root for the next tamper case
        shutil.rmtree(scratch_root)
        _write_fake_root(scratch_root, plan, modes, FAKE_MARGINAL)
    _assert_no_production_entry()


def test_w5_gate_rejects_r23_oracle_records():
    bad = [{"width": 128, "ratio": "r65", "arm": "S",
            "graph_seed": r23.GRAPH_SEEDS[(128, "r65")][0],
            "block_seed": s, "batch_id": r23.R23_BATCH_ID,
            "exact": True, "oracle": True, "graded": False,
            "belief_provenance": "ORACLE"}
           for s in r23.BLOCK_SEEDS[(128, "r65")]]
    with pytest.raises(ValueError):
        w23b.weak_cell_tally(bad * 2, 128, "r65")
    _assert_no_production_entry()


def test_w5_verifier_pass_s_stamped_production_graphs(scratch_root):
    # Reviewer-mandated regression (option b): the production R23 builder
    # stamps reused graphs 'S'; W-only fakes masked the strict predicate.
    # S-stamped fakes like production must PASS (decoder rows stay 'W').
    plan = w23b.build_weak_plan()
    modes = ([True] * 4 + [False] * 4 + [False] * 8
             + [True] * 8 + [False] * 8)
    summary = _write_fake_root_with_build(
        scratch_root, plan, modes, FAKE_MARGINAL, _fake_build_fn_s)
    assert summary["terminal"] == w23b.WIN
    import csv as _csv
    with open(scratch_root / "graph_records.csv",
              encoding="utf-8", newline="") as fh:
        graph_rows = list(_csv.DictReader(fh))
    assert len(graph_rows) == 4
    assert {row["arm"] for row in graph_rows} == {r23.ARM}
    assert w23b.verify_root(str(scratch_root),
                            build_fn=_fake_build_fn_s) is True
    _assert_no_production_entry()


def test_w5_verifier_rejects_unknown_graph_seed(scratch_root):
    # Troubleshooting-adjacent: the widened predicate still fails closed
    # on graph seeds outside the frozen R23.GRAPH_SEEDS set.
    plan = w23b.build_weak_plan()
    modes = ([True] * 4 + [False] * 4 + [False] * 8
             + [True] * 8 + [False] * 8)
    _write_fake_root(scratch_root, plan, modes, FAKE_MARGINAL)
    import csv as _csv
    path = scratch_root / "graph_records.csv"
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    assert rows
    rows[0]["graph_seed"] = "12345678"  # outside every frozen seed set
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    assert w23b.verify_root(str(scratch_root),
                            build_fn=_fake_build_fn) is False
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W6: PROFILE_ONLY dry-run — 32-call default plan, budgets ok, 0 calls
# --------------------------------------------------------------------------- #
def test_w6_profile_only_dry_run(capsys):
    profile = w23b.profile_only()
    assert profile["plan_calls"] == 32
    assert profile["per_cell_calls"] == 16
    assert profile["conditional_r72"] is False
    assert profile["extended_plan_calls"] == 64
    assert profile["decoder_calls"] == 0
    assert profile["graph_builds"] == 0
    assert profile["future_root_absent"] is True
    assert profile["prior_root"] == w23b.FROZEN_PRIOR_ROOT
    assert profile["calibration"] == {"anchor": "128:r65", "max_exact": 4}
    budgets = profile["budgets"]
    assert budgets["scientific_calls"] == 64
    assert budgets["setup_calls"] == 8
    assert budgets["wall_s"] == 3600.0
    assert budgets["per_call_s"] == 300.0
    assert budgets["per_build_s"] == {128: 60.0, 1024: 300.0}
    assert len(profile["cells"]) == 2
    assert sum(c["calls"] for c in profile["cells"]) == 32
    assert all(c["independent_blocks"] for c in profile["cells"])
    assert w23b.FROZEN_STAGE1_ARGV == [".venv/bin/python",
                                       "scripts/v72p2r23_scale_weak.py",
                                       "--profile-only"]
    assert w23b.main(["--profile-only"]) == 0
    _assert_no_production_entry()


def test_w6_extended_plan_shape_without_execution():
    plan = w23b.build_weak_plan(include_r72=True)
    assert len(plan) == 64
    assert [e["call_idx"] for e in plan] == list(range(64))
    assert {e["arm"] for e in plan} == {w23b.ARM}
    assert all(e["disclosed_bits"] == 5 * e["m"] for e in plan)
    for width in r23.WIDTHS:
        for key in ("r65", "r72"):
            scoped = [e for e in plan if e["width"] == width
                      and e["ratio"] == key]
            assert len(scoped) == 16
            groups = [sorted(e["block_seed"] for e in scoped
                             if e["graph_seed"] == seed)
                      for seed in r23.GRAPH_SEEDS[(width, key)]]
            assert groups[0] != groups[1]  # independent, never shared
            assert len(set(groups[0]) | set(groups[1])) == 16
    w23b._validate_weak_plan(plan, include_r72=True)
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# W7: seed guard — independent per-graph groups; banned literals absent
# --------------------------------------------------------------------------- #
def test_w7_weak_block_seeds_independent_and_guarded():
    groups = w23b.WEAK_BLOCK_SEEDS
    assert len(groups) == 8  # 2 widths x 2 ratios x 2 graphs
    assert all(len(seeds) == 8 for seeds in groups.values())
    weak = {s for seeds in groups.values() for s in seeds}
    assert len(weak) == 64
    r23seeds = ({s for seeds in r23.GRAPH_SEEDS.values() for s in seeds}
                | {s for seeds in r23.BLOCK_SEEDS.values() for s in seeds})
    assert weak.isdisjoint(r23seeds)
    banned = ({2026094601, 2026094602}
              | set(range(2026094701, 2026094709))
              | set(range(2026094711, 2026094720))
              | {2026094720, 2026094721, 2026094722, 2026094723}
              | {2026095001, 2026098001, 2026099001})
    assert weak.isdisjoint(banned)
    assert min(weak) > 2026094723 and max(weak) < 2026095001
    # W-graphs reuse the R23 12 identically (seed identity, quoted).
    assert r23.GRAPH_SEEDS[(128, "r65")] == (2026094801, 2026094802)
    assert r23.GRAPH_SEEDS[(1024, "r65")] == (2026094811, 2026094812)
    assert r23.GRAPH_SEEDS[(128, "r72")] == (2026094803, 2026094804)
    assert r23.GRAPH_SEEDS[(1024, "r72")] == (2026094813, 2026094814)
    _assert_no_production_entry()
