"""R23 synthetic scale probe — focused readiness tests (R23b).

Track EXPLORE-readiness: zero decoder calls; no R23 batch, no R23 graph
builds (12 fresh graphs build at R23c setup), no real data, no Model-F.
Fake builders/adapters/blocks carry the suite except the single D19
reference byte-identity check, which uses the real frozen D19 builder on
one n128 cell (setup-only reference, no decoder). Fresh ``workspace/``
scratch roots; ``-p no:cacheprovider``.
"""
from __future__ import annotations

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

RUNNER_PATH = ROOT / "scripts" / "v72p2r23_scale.py"
MODULE_PATH = (SRC / "comparison_bench" / "formal_ir"
               / "v72p2r23_scale.py")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
import comparison_bench.formal_ir.v72p2d19_l2_finite as d19  # noqa: E402
import comparison_bench.formal_ir.v72p2r23_scale as r23  # noqa: E402

runner = _load_module("v72p2r23_runner_test", RUNNER_PATH)

#: Zero-decoder-call proof: v35 enters sys.modules via the accepted D9
#: import chain (primitive references only), so module-absence cannot
#: prove non-use. Instead wrap the production kernels with counting
#: shims at session start — any production decode/syndrome call fails
#: every fake-path test below (E23b-calls must stay 0).
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

FUTURE_ROOT = (ROOT / r23.FUTURE_ROOT).resolve()

#: Hand-recomputable B1 sheet: (n, m) -> (E, check allocation, rate, 5m).
HAND_SHEET = {
    (128, 83): {"E": 384, "check": {4: 31, 5: 52},
                "rate": 1.0 - 83 / 128, "disclosed": 415},
    (128, 92): {"E": 384, "check": {4: 76, 5: 16},
                "rate": 1.0 - 92 / 128, "disclosed": 460},
    (128, 100): {"E": 384, "check": {3: 16, 4: 84},
                 "rate": 1.0 - 100 / 128, "disclosed": 500},
    (1024, 666): {"E": 3072, "check": {4: 258, 5: 408},
                  "rate": 1.0 - 666 / 1024, "disclosed": 3330},
    (1024, 737): {"E": 3072, "check": {4: 613, 5: 124},
                  "rate": 1.0 - 737 / 1024, "disclosed": 3685},
    (1024, 799): {"E": 3072, "check": {3: 124, 4: 675},
                  "rate": 1.0 - 799 / 1024, "disclosed": 3995},
}


def _assert_no_production_entry():
    assert _CALL_COUNT == {"decode": 0, "syndrome": 0}, \
        "production kernel called on fake path: %r" % (_CALL_COUNT,)


@pytest.fixture()
def scratch_root():
    path = ROOT / "workspace" / ("r23_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert path.resolve() != FUTURE_ROOT
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# --------------------------------------------------------------------------- #
# fakes (never the production decoder; never Model-F content)
# --------------------------------------------------------------------------- #
def _fake_graph(width, ratio, seed, *, admitted=True):
    n = int(width)
    m = r23.ROWS[(n, ratio)]
    H = np.zeros((m, n), dtype=np.int64)
    for v in range(n):
        H[v % m, v] = 1
    return {"arm": r23.ARM, "width": n, "ratio": ratio,
            "graph_seed": int(seed), "n": n, "m": m,
            "E": int(np.count_nonzero(H)), "edges": [], "coefficients": [],
            "dense": H, "structure": None, "status": "ok",
            "admitted": bool(admitted),
            "failure_reason": "" if admitted else "fake non-admit"}


def _fake_build_fn(width, ratio, seed):
    return _fake_graph(width, ratio, seed)


def _fake_sample_fn(width, ratio, seed):
    return r23.sample_oracle_block(width, ratio, seed)


def _fake_syndrome_fn(matrix, vector):
    H = np.asarray(matrix)
    return np.zeros(H.shape[0], dtype=np.uint8)


class _FakeResult:
    def __init__(self, x_hat):
        self.x_hat = np.asarray(x_hat, dtype=np.uint8)
        self.syndrome_ok = True
        self.iterations = 1
        self.status = "fake_converged"
        self.belief_provenance = "FAKE"


def _fake_decode_exact(matrix, prior, syndromes, **kwargs):
    assert kwargs.get("max_iter") == 90
    assert kwargs.get("damping_alpha") == 1.0
    assert kwargs.get("warm_beliefs") is None
    return _FakeResult(np.argmax(np.asarray(prior), axis=1))


def _fake_decode_dead(matrix, prior, syndromes, **kwargs):
    return _FakeResult((np.argmax(np.asarray(prior), axis=1) + 1) % 32)


def _fake_adapters(decode_fn):
    return {"decode_fn": decode_fn, "syndrome_fn": _fake_syndrome_fn,
            "sample_fn": _fake_sample_fn, "build_fn": _fake_build_fn}


def _write_fake_root(root, decode_fn):
    bundle = runner.run_authorized_batch(
        str(root), adapters=_fake_adapters(decode_fn))
    return runner.write_batch_root(bundle)


# --------------------------------------------------------------------------- #
# T1: B1 D9 tables match the hand sheet through the D9 import
# --------------------------------------------------------------------------- #
def test_t1_d9_tables_match_hand_sheet():
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            cell = r23.degree_cell(width, key)
            want = HAND_SHEET[(width, cell["m"])]
            assert cell["m"] == r23.ROWS[(width, key)]
            assert cell["m"] == int(round(width * ratio))
            assert cell["var_counts"] == {3: width}
            assert cell["check_counts"] == want["check"]
            assert cell["E"] == want["E"] == 3 * width
            assert cell["rate"] == pytest.approx(want["rate"])
            assert cell["disclosed_bits"] == want["disclosed"] == 5 * cell["m"]
            sockets = sum(d * c for d, c in cell["check_counts"].items())
            assert sockets == cell["E"]
    _assert_no_production_entry()


def test_t1_plan_is_96_paired_oracle():
    plan = r23.build_call_plan()
    assert len(plan) == 96
    assert [e["call_idx"] for e in plan] == list(range(96))
    assert {e["arm"] for e in plan} == {"S"}
    assert all(e["disclosed_bits"] == 5 * e["m"] for e in plan)
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            scoped = [e for e in plan if e["width"] == width
                      and e["ratio"] == key]
            assert len(scoped) == 16
            for seed in r23.GRAPH_SEEDS[(width, key)]:
                got = sorted(e["block_seed"] for e in scoped
                             if e["graph_seed"] == seed)
                assert got == sorted(r23.BLOCK_SEEDS[(width, key)])
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T2: admission predicate on fakes incl construction_failed path
# --------------------------------------------------------------------------- #
def test_t2_admission_refuses_non_admitted_zero_calls():
    graphs = {}
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            for seed in r23.GRAPH_SEEDS[(width, key)]:
                bad = (width == 1024 and key == "r78"
                       and seed == r23.GRAPH_SEEDS[(width, key)][0])
                graphs[(width, key, seed)] = _fake_graph(
                    width, key, seed, admitted=not bad)
    blocks = {(w, r23.RATIO_KEY[r]): {
        s: r23.sample_oracle_block(w, r23.RATIO_KEY[r], s)
        for s in r23.BLOCK_SEEDS[(w, r23.RATIO_KEY[r])]}
        for w in r23.WIDTHS for r in r23.RATIOS}
    outcome = r23.execute_plan(r23.build_call_plan(), graphs, blocks,
                               _fake_decode_exact, _fake_syndrome_fn)
    assert outcome["decoder_calls"] == 0
    assert outcome["records"] == []
    assert "not admitted" in outcome["failure"]
    _assert_no_production_entry()


def test_t2_construction_failed_path_retained():
    def _fail_peg(n, m, var_counts, check_counts, seed):
        return {"status": "construction_failed",
                "failure_reason": "fake 4408-class dead end",
                "edges": []}

    graph = r23.build_graph(128, "r65", r23.GRAPH_SEEDS[(128, "r65")][0],
                            peg_fn=_fail_peg)
    assert graph["status"] == "construction_failed"
    assert graph["admitted"] is False
    assert graph["failure_reason"] == "fake 4408-class dead end"
    with pytest.raises(r2.StructureNotAdmitted):
        r23.run_s_oracle_call(
            graph, r23.sample_oracle_block(128, "r65", 2026094831),
            {"width": 128, "n": 128, "m": 83, "ratio": "r65", "arm": "S",
             "graph_seed": graph["graph_seed"], "block_seed": 2026094831},
            decode_fn=_fake_decode_exact, syndrome_fn=_fake_syndrome_fn,
            call_idx=0)
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T3: oracle sampler — determinism, shape, truth mass, weight range
# --------------------------------------------------------------------------- #
def test_t3_oracle_sampler_shape_and_truth_mass():
    first = r23.sample_oracle_block(128, "r65", 2026094831)
    again = r23.sample_oracle_block(128, "r65", 2026094831)
    assert np.array_equal(first["u"], again["u"])
    assert np.array_equal(first["prior"], again["prior"])
    assert first["weight"] == again["weight"]
    assert first["u"].shape == (128,)
    assert first["prior"].shape == (128, 32)
    assert np.allclose(first["prior"].sum(axis=1), 1.0)
    mass = float(np.mean(first["prior"][np.arange(128), first["u"]]))
    assert mass == pytest.approx(1.0 - r23.P_ERR)
    assert 0 <= first["weight"] <= 128
    other = r23.sample_oracle_block(128, "r65", 2026094832)
    assert not np.array_equal(first["u"], other["u"])
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T4: refusal / no-overwrite (rc2 no-write, existing root, protected)
# --------------------------------------------------------------------------- #
def test_t4_refusal_missing_grant_zero_calls(scratch_root, capsys):
    rc = runner.main(["--r23-batch", "--out-root", str(scratch_root)])
    assert rc == 2
    assert not scratch_root.exists()
    _assert_no_production_entry()


def test_t4_refusal_existing_root_zero_calls(scratch_root):
    scratch_root.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        runner.run_authorized_batch(
            str(scratch_root), adapters=_fake_adapters(_fake_decode_exact))
    _assert_no_production_entry()


def test_t4_refusal_protected_roots():
    # Existing D19 future root: refusal fires as FileExistsError (never
    # overwrite); non-existent protected subtrees fire as ValueError.
    with pytest.raises((ValueError, FileExistsError)):
        r23.refuse_out_root(
            "workspace/d19_l2_finite_ensemble_"
            "5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b")
    with pytest.raises(ValueError):
        r23.refuse_out_root("comparison_bench/outputs_comparison/r23_x")
    with pytest.raises(ValueError):
        r23.refuse_out_root("results/r23_x")
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T5: verifier — fake full-batch PASS; tamper FAILs; gate isolation
# --------------------------------------------------------------------------- #
def test_t5_verifier_pass_fake_batch(scratch_root):
    summary = _write_fake_root(scratch_root, _fake_decode_exact)
    # Uniform-exact fake: anchors 16/16, gap 0 <+4 -> SCALING-DEAD per the
    # frozen literal rule (diagnostic mapping, not a signal claim).
    assert summary["terminal"] == r23.DEAD
    assert summary["per_cell"]["1024:r65"]["E"] == 16
    assert summary["per_cell"]["128:r65"]["E"] == 16
    assert summary["scientific_calls"] == 96
    assert summary["undetected_count"] == 0
    assert runner.verify_root(str(scratch_root),
                              build_fn=_fake_build_fn) is True
    _assert_no_production_entry()


def test_t5_verifier_tamper_fails(scratch_root):
    _write_fake_root(scratch_root, _fake_decode_exact)
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
        rows[2]["belief_provenance"] = "CHECK_UPDATED"
        return True

    for tamper in (_tamper_exact_without_syndrome, _tamper_undetected_merged,
                   _tamper_provenance):
        _rewrite(tamper)
        assert runner.verify_root(str(scratch_root),
                                  build_fn=_fake_build_fn) is False
        # restore the good root for the next tamper case
        shutil.rmtree(scratch_root)
        _write_fake_root(scratch_root, _fake_decode_exact)
    _assert_no_production_entry()


def test_t5_gate_rejects_d19_reference_record():
    bad = [{"width": 128, "ratio": "r65", "arm": "S",
            "graph_seed": r23.GRAPH_SEEDS[(128, "r65")][0],
            "block_seed": s, "batch_id": d19.D19_BATCH_ID,
            "exact": True, "oracle": True, "graded": False}
           for s in r23.BLOCK_SEEDS[(128, "r65")]]
    with pytest.raises(ValueError):
        r23.cell_tally(bad * 2, 128, "r65")
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T6: D19-import byte-identity (one n128 reference cell, setup-only)
# --------------------------------------------------------------------------- #
def test_t6_d19_reference_byte_identity():
    seed = 2026094401
    via_helper = r23.d19_reference_build("DV3", seed)
    direct = d19.build_graph("DV3", 128, seed)
    assert via_helper["edges"] == direct["edges"]
    assert via_helper["coefficients"] == direct["coefficients"]
    assert np.array_equal(np.asarray(via_helper["dense"]),
                          np.asarray(direct["dense"]))
    assert (via_helper["E"], via_helper["admitted"],
            via_helper["status"]) == \
        (direct["E"], direct["admitted"], direct["status"])
    assert via_helper["E"] == 384  # 3^128 at m94 (reference only)
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T7: PROFILE_ONLY dry-run — plan 96, budgets ok, 0 calls, root absent
# --------------------------------------------------------------------------- #
def test_t7_profile_only_dry_run():
    profile = runner.profile_only()
    assert profile["plan_calls"] == 96
    assert profile["per_cell_calls"] == 16
    assert profile["decoder_calls"] == 0
    assert profile["graph_builds"] == 0
    assert profile["future_root_absent"] is True
    budgets = profile["budgets"]
    assert budgets["scientific_calls"] == 96
    assert budgets["setup_calls"] == 12
    assert budgets["wall_s"] == 3600.0
    assert budgets["per_call_s"] == 300.0
    assert budgets["per_build_s"] == {128: 60.0, 1024: 300.0}
    assert len(profile["cells"]) == 6
    assert sum(c["calls"] for c in profile["cells"]) == 96
    assert r23.FROZEN_STAGE1_ARGV == [".venv/bin/python",
                                      "scripts/v72p2r23_scale.py",
                                      "--profile-only"]
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T8: seed guard — banned literals absent; free-interval sandwich
# --------------------------------------------------------------------------- #
def test_t8_seed_disjointness_and_interval():
    graphs = {s for seeds in r23.GRAPH_SEEDS.values() for s in seeds}
    blocks = {s for seeds in r23.BLOCK_SEEDS.values() for s in seeds}
    assert len(graphs) == 12 and len(blocks) == 48
    assert graphs.isdisjoint(blocks)
    banned = ({2026094601, 2026094602}
              | set(range(2026094701, 2026094709))
              | set(range(2026094711, 2026094720))
              | {2026094720, 2026094721, 2026094722, 2026094723}
              | {2026095001, 2026098001, 2026099001})
    assert graphs.isdisjoint(banned) and blocks.isdisjoint(banned)
    assert min(graphs) > 2026094723 and max(blocks) < 2026095001
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T9: frozen R23c-R1 scaling gate units + build sub-cap checker on fakes
# --------------------------------------------------------------------------- #
def test_t9_gate_labels_frozen_rule():
    g = r23.route_scaling_gate
    assert g(8, 4, 0) == r23.WIN      # hi>=6/16 and gap>=+4/16
    assert g(6, 2, 0) == r23.WIN      # boundary WIN
    assert g(16, 16, 0) == r23.DEAD   # gap 0 <+4/16
    assert g(2, 0, 0) == r23.DEAD     # hi<=2/16
    assert g(6, 3, 0) == r23.DEAD     # gap +3 <+4/16
    assert g(5, 0, 0) == r23.INCONCLUSIVE
    assert g(4, 0, 0) == r23.INCONCLUSIVE
    assert g(8, 4, 1) == r23.STOP     # undetected>0 absolute
    assert g(8, 4, 0, "boom") == r23.STOP
    with pytest.raises(ValueError):
        g(17, 0, 0)
    _assert_no_production_entry()


def test_t9_build_subcap_checker():
    rows = [{"width": 128, "graph_seed": 1, "construction_wall_s": 59.0},
            {"width": 1024, "graph_seed": 2, "construction_wall_s": 299.0}]
    assert r23.check_build_budgets(rows) == []
    rows[0]["construction_wall_s"] = 60.5
    assert len(r23.check_build_budgets(rows)) == 1
    _assert_no_production_entry()


# --------------------------------------------------------------------------- #
# T10: cold 90/1.0 contract literals reused from R2 (no re-declaration)
# --------------------------------------------------------------------------- #
def test_t10_decoder_contract_lineage():
    assert r23.DECODER_MAX_ITER == 90 == r2.DECODER_MAX_ITER
    assert r23.DAMPING_ALPHA == 1.0 == r2.DAMPING_ALPHA
    assert r23.Q == 32 == r2.Q
    assert r23.RSS_BUDGET_BYTES == r2.RSS_BUDGET_BYTES
    _assert_no_production_entry()
