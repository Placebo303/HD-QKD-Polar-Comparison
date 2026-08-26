"""Focused V41P0 tests (T1-T12) for the fresh-block confirmation runner.

All tests are fake-runner / stub-evaluator or decoder-free. No production
decoder is invoked, the official V41 output root is never created, and no NPZ
is read or written (the read-only V25 counts loader stays allowed).
"""

from __future__ import annotations

import csv
import itertools
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparison_bench.formal_ir.v35_algorithm_development import (  # noqa: E402
    GF2mField,
    load_v25_channel_counts,
)
from comparison_bench.formal_ir import (  # noqa: E402
    v41_fresh_block_confirm as v41,
)

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v41_fresh_block_confirm.py"

INITIAL_BY_BLOCK = {
    390107: 250, 390108: 261, 390109: 272,
    390207: 255, 390208: 266, 390209: 277,
    390307: 249, 390308: 258, 390309: 267,
}


@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()


# ---------------------------------------------------------------------------
# Fake world (accepted V40 pattern, adapted; no real construction cost)
# ---------------------------------------------------------------------------


class FakeWorld:
    def __init__(self):
        self.metrics_by_id: dict[str, dict] = {}
        self.constructors = {
            "lane_b": self._make_ctor("lane_b"),
            "lane_c": self._make_ctor("lane_c"),
        }

    def _make_ctor(self, lane):
        def _ctor(source: str, seed: int, field=None):
            # Wide zero matrix: the real v38 fake-decode path still computes a
            # true syndrome from u2_alice, so H must span 1024 columns.
            H = np.zeros((4, 1024), dtype=np.uint8)
            H[0, ::8] = 1
            H[1, ::9] = 1
            H[2, ::11] = 1
            H[3, ::13] = 1
            matrix_id = f"{lane}_{source}_s{seed}"
            metrics = {
                "lane": lane,
                "source": source,
                "construction_seed": seed,
                "matrix_id": matrix_id,
                "shape": [4, 1024],
                "rank_GF32": 4,
                "support_edge_count": int((H != 0).sum()),
                "col_degree_min": 0,
                "col_degree_mean": int((H != 0).sum()) / 1024,
                "col_degree_max": 4,
                "row_degree_min": 79,
                "row_degree_mean": float((H != 0).sum()) / 4,
                "row_degree_max": 128,
                "degenerate_cycles_4": 0,
                "degenerate_cycles_6": 0,
                "degenerate_cycles_8": 0,
                "support_cycles_4": 0,
                "structurally_valid": True,
            }
            if lane == "lane_c":
                metrics["position_permutations"] = [[0, 1], [1, 0]]
            self.metrics_by_id[matrix_id] = metrics
            return H, metrics

        return _ctor

    def authority_file(self, tmp_path: Path) -> Path:
        for lane in ("lane_b", "lane_c"):
            for source in v41.SOURCE_ORDER:
                for seed in v41.CONSTRUCTION_SEEDS[lane][source]:
                    self.constructors[lane](source=source, seed=seed)
        records: list[dict] = []
        for source in v41.SOURCE_ORDER:
            for seed in (911001, 911002, 911003):
                records.append(
                    {"lane": "lane_a", "source": source, "construction_seed": seed,
                     "matrix_id": f"lane_a_{source}_s{seed}", "shape": "[4, 1024]"}
                )
        for matrix_id, metrics in self.metrics_by_id.items():
            records.append(dict(metrics))
        assert len(records) == 27
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# Stub evaluator machinery (zero production decode)
# ---------------------------------------------------------------------------


def stub_raw(kwargs: dict, exact: bool, final: int, syndrome_ok: bool | None = None) -> dict:
    if syndrome_ok is None:
        syndrome_ok = exact
    return {
        "source": kwargs["source"],
        "block_seed": kwargs["block_seed"],
        "lane": kwargs["lane"],
        "construction_seed": kwargs["construction_seed"],
        "matrix_id": f"{kwargs['lane']}_{kwargs['source']}_s{kwargs['construction_seed']}",
        "errors_initial": INITIAL_BY_BLOCK[kwargs["block_seed"]],
        "errors_final": final,
        "exact_l2": exact,
        "syndrome_ok": syndrome_ok,
        "iterations": 9,
        "status": "stub",
        "runtime_s": 0.001,
    }


def install_stub(monkeypatch, outcome, calls: list | None = None):
    """outcome(kwargs) -> (exact, final[, syndrome_ok]); scenario owns its counters."""

    def _eval(**kwargs):
        if calls is not None:
            calls.append({
                "max_iter": kwargs["max_iter"],
                "damping_alpha": kwargs["damping_alpha"],
                "block_seed": kwargs["block_seed"],
                "lane": kwargs["lane"],
                "keys": set(kwargs.keys()),
            })
        result = outcome(kwargs)
        if len(result) == 2:
            exact, final = result
            syn = None
        else:
            exact, final, syn = result
        return stub_raw(kwargs, exact, final, syn)

    monkeypatch.setattr(v41, "evaluate_single_block", _eval)
    return _eval


def run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=None, name="run"):
    world = FakeWorld()
    install_stub(monkeypatch, outcome, calls)
    root = tmp_path / name
    result = v41.run_v41_confirmation(
        execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        check_git=False,
        check_scoped_dirty=False,
        constructors=world.constructors,
    )
    return result, root


def make_positional_outcome(special: dict[int, tuple], default=(True, 0)):
    counters = {"n": 0}

    def outcome(kwargs):
        counters["n"] += 1
        idx = counters["n"] - 1
        return special.get(idx, default)

    outcome.counters = counters
    return outcome


# ---------------------------------------------------------------------------
# T1: seed-registry validator (duplicates, shape, each forbidden family)
# ---------------------------------------------------------------------------


def test_t1_registry_accepts_frozen_nine():
    ok, msg = v41.validate_seed_registry()
    assert ok and msg == "SEED_REGISTRY_OK"
    assert set(v41.NEW_BLOCK_SEEDS.keys()) == set(v41.SOURCE_ORDER)
    assert [s for src in v41.SOURCE_ORDER for s in v41.NEW_BLOCK_SEEDS[src]] == [
        390107, 390108, 390109, 390207, 390208, 390209, 390307, 390308, 390309,
    ]


def _registry_with(source: str, replacement: list[int]) -> dict[str, list[int]]:
    reg = {src: list(seeds) for src, seeds in v41.NEW_BLOCK_SEEDS.items()}
    reg[source] = replacement
    return reg


@pytest.mark.parametrize(
    "bad_reg",
    [
        _registry_with("1M", [390107, 390107, 390108]),  # duplicate among the nine
        _registry_with("1p5M", [390207, 390208]),  # wrong shape: two seeds
        _registry_with("2M", [390307, 390308, 390309, 390310]),  # four seeds
        _registry_with("1M", [360101, 390108, 390109]),  # V36_A3 overlap
        _registry_with("1p5M", [390201, 390208, 390209]),  # V39 overlap
        _registry_with("2M", [390306, 390308, 390309]),  # V40 probe overlap
        {"1M": [390107], "1p5M": [390207]},  # missing source
    ],
)
def test_t1_registry_rejects_drift(bad_reg):
    ok, msg = v41.validate_seed_registry(bad_reg)
    assert not ok


@pytest.mark.parametrize("probe_seed", [390106, 390206, 390306])
def test_t1_each_v40_probe_seed_forbidden(probe_seed):
    reg = {src: list(seeds) for src, seeds in v41.NEW_BLOCK_SEEDS.items()}
    reg["1M"][0] = probe_seed
    ok, msg = v41.validate_seed_registry(reg)
    assert not ok and str(probe_seed) in msg


# ---------------------------------------------------------------------------
# T2: reconstruction determinism, strict metric match, identity drift (J3)
# ---------------------------------------------------------------------------


def test_t2_reconstruction_deterministic_decoder_free_write_free(tmp_path, monkeypatch):
    world = FakeWorld()
    field = GF2mField.create(32)
    decode_calls: list = []

    def _no_decode(*args, **kwargs):
        decode_calls.append(1)
        raise AssertionError("reconstruction must be decoder-free")

    monkeypatch.setattr(v41, "evaluate_single_block", _no_decode)
    authority = world.authority_file(tmp_path)
    first = v41.reconstruct_v41_matrices(authority, field=field, constructors=world.constructors)
    second = v41.reconstruct_v41_matrices(authority, field=field, constructors=world.constructors)
    assert decode_calls == []
    assert set(first.keys()) == set(second.keys()) == set(v41.RECONSTRUCTION_KEYS)
    for key in v41.RECONSTRUCTION_KEYS:
        m1, met1 = first[key]
        m2, met2 = second[key]
        assert np.array_equal(m1, m2)
        assert met1 == met2
    _, lane_c_metrics = first[("lane_c", "1M")]
    assert "position_permutations" in lane_c_metrics
    # representative identities equal the frozen constants
    ids = sorted(f"{lane}_{source}_s{v41._rep_seed(lane, source)}" for lane, source in v41.RECONSTRUCTION_KEYS)
    assert ids == sorted(v41.FROZEN_REPRESENTATIVE_MATRIX_IDS)
    # write-free: only the authority file exists in tmp_path
    assert {p.name for p in tmp_path.iterdir()} == {"fake_authority.json"}


def test_t2_reconstruction_detects_metric_and_permutation_drift(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)

    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"] == "lane_b_1M_s382102")
    victim["rank_GF32"] = int(victim["rank_GF32"]) - 1
    bad_rank = tmp_path / "bad_rank.json"
    bad_rank.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.reconstruct_v41_matrices(bad_rank, field=field, constructors=world.constructors)
    assert excinfo.value.check_id == "J3"

    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"] == "lane_c_1M_s383102")
    victim["position_permutations"] = [[5, 5], [5, 5]]
    bad_perms = tmp_path / "bad_perms.json"
    bad_perms.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.reconstruct_v41_matrices(bad_perms, field=field, constructors=world.constructors)
    assert excinfo.value.check_id == "J3"


def test_t2_reconstruction_identity_and_missing_record_drift(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    authority = world.authority_file(tmp_path)

    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"] == "lane_c_1M_s383102")
    victim["lane"] = "lane_b"  # identity mismatch in committed metrics
    bad_ident = tmp_path / "bad_ident.json"
    bad_ident.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.reconstruct_v41_matrices(bad_ident, field=field, constructors=world.constructors)
    assert excinfo.value.check_id == "J3"

    records = json.loads(authority.read_text(encoding="utf-8"))
    records = [r for r in records if r["matrix_id"] != "lane_b_2M_s382302"]
    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.reconstruct_v41_matrices(missing, field=field, constructors=world.constructors)
    assert excinfo.value.check_id == "J3"

    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.reconstruct_v41_matrices(tmp_path / "winner.npz", field=field, constructors=world.constructors)
    assert excinfo.value.check_id == "J8"


# ---------------------------------------------------------------------------
# T3: posterior-binding sentinels (six fixed conditions; tamper detection)
# ---------------------------------------------------------------------------


def test_t3_posterior_sentinels_pass_on_real_first_blocks(real_counts):
    results = v41.posterior_binding_preflight(real_counts)
    assert set(results.keys()) == set(v41.SOURCE_ORDER)
    for source, checks in results.items():
        assert checks["probe_block_seed"] == v41.PREFLIGHT_BLOCK_SEEDS[source]
        assert checks["bob_gt_31"] is True
        assert checks["captured_equals_bob"] is True
        assert checks["corrected_equals_direct"] is True
        assert checks["corrected_differs_u2bob_arraywise"] is True
        assert checks["corrected_differs_u2bob_maxabs"] is True
        assert checks["argmax_divergence"] is True


def test_t3_posterior_tampered_second_argument_detected(real_counts):
    real = v41.get_conditional_posterior_l2

    def substituting_posterior(cnt, b, u1):
        # substitutes the bound second argument's contents in place, mimicking
        # a u2_bob-class swap after binding; the spy's pre-call copy diverges
        return real(cnt, b.__setitem__(slice(None), (np.asarray(b) + 1) % 32) or b, u1)

    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.posterior_binding_preflight(real_counts, posterior_fn=substituting_posterior)
    assert excinfo.value.check_id == "J5"
    assert "captured_equals_bob" in excinfo.value.message


# ---------------------------------------------------------------------------
# T4: per-lane gate boundaries on synthetic records
# ---------------------------------------------------------------------------


def _synthetic_lane_records(lane, exact_flags, wrong_positions=()):
    """exact_flags: dict source -> list of 3 bools."""
    recs = []
    call_no = 0
    for source in v41.SOURCE_ORDER:
        for k, exact in enumerate(exact_flags[source]):
            call_no += 1
            syndrome_ok = True
            exact_eff = exact and (call_no - 1) not in wrong_positions
            recs.append({
                "call_id": f"C{call_no:02d}",
                "lane": lane,
                "source": source,
                "block_seed": list(INITIAL_BY_BLOCK)[call_no - 1],
                "matrix_id": f"{lane}_{source}_s383102",
                "max_iter": 90,
                "damping_alpha": 1.0,
                "errors_initial": 100,
                "errors_final": 0 if exact_eff else 50,
                "exact_l2": exact_eff,
                "syndrome_ok": syndrome_ok,
                "wrong_codeword": syndrome_ok and not exact_eff,
                "iterations": 5,
                "status": "stub",
                "runtime_s": 0.001,
            })
    return recs


def test_t4_g1_overall_boundary():
    fail_6 = {"1M": [True, True, True], "1p5M": [True, True, True], "2M": [False, False, False]}
    gate = v41.evaluate_lane_gate("lane_c", _synthetic_lane_records("lane_c", fail_6))
    assert gate["g1_overall_exact_ge_7_of_9"]["exact_total"] == 6
    assert gate["g1_overall_exact_ge_7_of_9"]["pass"] is False
    assert gate["passed"] is False

    pass_7 = {"1M": [True, True, True], "1p5M": [True, True, True], "2M": [True, False, False]}
    gate = v41.evaluate_lane_gate("lane_c", _synthetic_lane_records("lane_c", pass_7))
    assert gate["g1_overall_exact_ge_7_of_9"]["exact_total"] == 7
    assert gate["g1_overall_exact_ge_7_of_9"]["pass"] is True


def test_t4_g2_per_source_boundary():
    # overall 7/9 but one source at 1/3 -> G2 fails while G1 passes
    flags = {"1M": [True, True, True], "1p5M": [True, True, True], "2M": [True, False, False]}
    gate = v41.evaluate_lane_gate("lane_b", _synthetic_lane_records("lane_b", flags))
    assert gate["g1_overall_exact_ge_7_of_9"]["pass"] is True
    assert gate["g2_every_source_ge_2_of_3"]["exact_by_source"]["2M"] == 1
    assert gate["g2_every_source_ge_2_of_3"]["pass"] is False
    assert gate["passed"] is False

    flags["2M"] = [True, True, False]
    flags["1p5M"] = [True, True, False]
    gate = v41.evaluate_lane_gate("lane_b", _synthetic_lane_records("lane_b", flags))
    assert gate["g2_every_source_ge_2_of_3"]["pass"] is True


def test_t4_g3_single_wrong_codeword_fails_lane():
    # everything else perfect except one wrong codeword -> own G3 fails
    flags = {"1M": [True, True, True], "1p5M": [True, True, True], "2M": [True, True, False]}
    recs = _synthetic_lane_records("lane_c", flags)
    recs[8]["exact_l2"] = False
    recs[8]["syndrome_ok"] = True
    recs[8]["wrong_codeword"] = True
    recs[8]["errors_final"] = 50
    gate = v41.evaluate_lane_gate("lane_c", recs)
    assert gate["g1_overall_exact_ge_7_of_9"]["pass"] is True
    assert gate["g2_every_source_ge_2_of_3"]["pass"] is True
    assert gate["g3_wrong_zero"]["wrong_count"] == 1
    assert gate["g3_wrong_zero"]["pass"] is False
    assert gate["passed"] is False


# ---------------------------------------------------------------------------
# T5: terminal-machine truth table - exhaustive and mutually exclusive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("integrity_ok", [True, False])
@pytest.mark.parametrize("wrong_total", [0, 1, 3])
@pytest.mark.parametrize("pass_pair", [(True, True), (True, False), (False, True), (False, False)])
def test_t5_truth_table_exhaustive_mutually_exclusive(integrity_ok, wrong_total, pass_pair):
    pc, pb = pass_pair
    terminal, reason, trace = v41.determine_v41_terminal(integrity_ok, wrong_total, pc, pb)
    assert terminal in v41.ALL_TERMINALS
    if not integrity_ok:
        expected = v41.TERMINAL_EVIDENCE_INVALID
    elif wrong_total > 0:
        expected = v41.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    elif pc and pb:
        expected = v41.TERMINAL_BOTH_LANES_RETAINED
    elif pc:
        expected = v41.TERMINAL_C_ONLY_RETAINED
    elif pb:
        expected = v41.TERMINAL_B_ONLY_RETAINED
    else:
        expected = v41.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert terminal == expected  # lands in EXACTLY ONE terminal
    if not integrity_ok:
        assert reason is None
    elif wrong_total > 0:
        assert reason == v41.REASON_WRONG_CODEWORD_GLOBAL
    elif not pc and not pb:
        assert reason == v41.REASON_BOTH_LANES_GATES_FAILED
    else:
        assert reason is None


def test_t5_stop_precedes_retained_when_any_wrong_exists():
    for pc, pb in itertools.product([True, False], repeat=2):
        terminal, reason, _ = v41.determine_v41_terminal(True, 1, pc, pb)
        assert terminal == v41.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
        assert reason == v41.REASON_WRONG_CODEWORD_GLOBAL


# ---------------------------------------------------------------------------
# T6: wrong-codeword GLOBAL termination through the full guarded runner
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pos,lane_of_pos", [(0, "lane_c"), (5, "lane_b"), (12, "lane_c"), (17, "lane_b")])
def test_t6_single_wrong_codeword_terminates_globally(tmp_path, monkeypatch, real_counts, pos, lane_of_pos):
    outcome = make_positional_outcome({pos: (False, 7, True)})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name=f"wrong_{pos}")
    assert result["terminal_state"] == v41.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert result["terminal_reason"] == v41.REASON_WRONG_CODEWORD_GLOBAL
    summary = json.loads((root / "v41_summary.json").read_text(encoding="utf-8"))
    assert summary["aggregates"]["wrong_total"] >= 1
    # even when both lanes' count clauses would numerically pass, STOP fires first
    assert summary["routing_trace"][1].startswith("rule_1_wrong_total=")


# ---------------------------------------------------------------------------
# T7: budget hard cap - structural refusal of call 19
# ---------------------------------------------------------------------------


def test_t7_budget_hard_cap_structural_refusal():
    accounting = v41.CallAccounting()
    for _ in range(v41.HARD_CALL_CAP):
        accounting.register_start()
        accounting.register_complete()
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        accounting.register_start()  # call 19 refused structurally
    assert excinfo.value.check_id == "J10"
    assert v41.HARD_CALL_CAP == 18 == v41.PLANNED_CALLS


# ---------------------------------------------------------------------------
# T8: scientific-preflight failure paths persist the invalid trio, ZERO calls
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "check_id,target",
    [("J2", "validate_seed_registry"), ("J3", "reconstruct_v41_matrices"),
     ("J5", "posterior_binding_preflight")],
)
def test_t8_preflight_failure_invalid_trio(tmp_path, monkeypatch, real_counts, check_id, target):
    world = FakeWorld()
    calls: list[dict] = []
    install_stub(monkeypatch, lambda kwargs: (False, 100), calls)

    if target == "validate_seed_registry":
        monkeypatch.setattr(v41, target, lambda seeds=None: (False, f"injected {check_id} failure"))
    else:
        def boom(*args, **kwargs):
            raise v41.IntegrityFailure(check_id, f"injected {check_id} failure")

        monkeypatch.setattr(v41, target, boom)

    root = tmp_path / f"preflight_{check_id}"
    kwargs = dict(
        execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        check_git=False,
        check_scoped_dirty=False,
        constructors=world.constructors,
    )
    result = v41.run_v41_confirmation(**kwargs)

    assert result["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"] == [(check_id, f"injected {check_id} failure")]
    assert calls == []  # evaluator truly never invoked

    names = {p.name for p in root.iterdir()}
    assert names == {
        "v41_invalid_notice.json",
        "v41_confirm_records.json",
        "v41_confirm_records.csv",
        "v41_summary.json",
    }
    records = json.loads((root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    assert records == []
    notice = json.loads((root / "v41_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert notice["partial_records_retained_byte_for_byte"] is False
    summary = json.loads((root / "v41_summary.json").read_text(encoding="utf-8"))
    assert summary["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    acc = summary["accounting"]
    assert acc["decoder_calls_planned"] == {"total": 18}
    assert acc["decoder_calls_started"] == {"total": 0}
    assert acc["decoder_calls_completed"] == {"total": 0}
    assert summary["aggregates"] == {} and summary["gate_evaluation"] == {}
    assert summary["routing_trace"] == []
    assert summary["performance_interpretation_presented"] is False

    # Relaunch on the same root is refused (J7): stop, no rerun.
    with pytest.raises(FileExistsError):
        v41.run_v41_confirmation(**kwargs)


def test_t8_counts_shape_failure_j4_invalid_trio(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()
    calls: list[dict] = []
    install_stub(monkeypatch, lambda kwargs: (False, 100), calls)
    root = tmp_path / "preflight_J4"
    result = v41.run_v41_confirmation(
        execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source={s: np.zeros((4, 4)) for s in v41.SOURCE_ORDER},  # wrong shapes
        check_git=False,
        check_scoped_dirty=False,
        constructors=world.constructors,
    )
    assert result["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert result["integrity_failures"][0][0] == "J4"
    assert calls == []
    summary = json.loads((root / "v41_summary.json").read_text(encoding="utf-8"))
    assert summary["accounting"]["decoder_calls_completed"] == {"total": 0}


# ---------------------------------------------------------------------------
# T9: mid-run BaseException retains raw partials byte-for-byte, then re-raises
# ---------------------------------------------------------------------------


def test_t9_partial_retention_byte_for_byte(tmp_path, monkeypatch, real_counts):
    def make_fail_at(fail_index):
        counter = {"n": 0}

        def outcome(kwargs):
            counter["n"] += 1
            if counter["n"] == fail_index:
                raise RuntimeError("simulated decoder crash")
            return (False, 100, False)

        return outcome

    with pytest.raises(RuntimeError) as excinfo:
        run_scenario(tmp_path, monkeypatch, real_counts, make_fail_at(5), name="crash")
    assert "simulated decoder crash" in str(excinfo.value)  # re-raise observed

    fail_root = tmp_path / "crash"
    names = {p.name for p in fail_root.iterdir()}
    assert names == {
        "v41_confirm_records.json",
        "v41_confirm_records.csv",
        "v41_summary.json",
        "v41_invalid_notice.json",
    }
    notice = json.loads((fail_root / "v41_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert notice["partial_records_retained_byte_for_byte"] is True
    summary = json.loads((fail_root / "v41_summary.json").read_text(encoding="utf-8"))
    assert summary["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert summary["performance_interpretation_presented"] is False
    assert summary["aggregates"] == {} and summary["gate_evaluation"] == {}
    assert summary["accounting"]["decoder_calls_started"] == {"total": 5}
    assert summary["accounting"]["decoder_calls_completed"] == {"total": 4}
    assert any(f["check"] == "mid_run_failure" for f in summary["integrity_failures"])

    ok_root = tmp_path / "okrun"
    run_scenario(tmp_path, monkeypatch, real_counts, lambda kwargs: (False, 100, False), name="okrun")
    ok_records = json.loads((ok_root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    retained = json.loads((fail_root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    assert retained == ok_records[:4]  # byte-for-byte prefix retention


def test_t9_keyboard_interrupt_retains_partials(tmp_path, monkeypatch, real_counts):
    counter = {"n": 0}

    def outcome(kwargs):
        counter["n"] += 1
        if counter["n"] == 2:
            raise KeyboardInterrupt
        return (False, 100, False)

    with pytest.raises(KeyboardInterrupt):
        run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="ki")
    root = tmp_path / "ki"
    records = json.loads((root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    assert len(records) == 1
    assert "v41_invalid_notice.json" in {p.name for p in root.iterdir()}


# ---------------------------------------------------------------------------
# T10: refusal-class guards (default deny, flags, SHA binding, scoped dirty)
# ---------------------------------------------------------------------------


def test_t10_cli_requires_flags_and_has_no_fake_runner_option():
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script

    proc = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout + proc.stderr)

    proc2 = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--execution-authorized"],
        capture_output=True, text=True,
    )
    assert proc2.returncode != 0
    assert "--authorized-target-sha" in (proc2.stdout + proc2.stderr)
    assert not v41.OUTPUT_ROOT.exists()  # nothing created on guard failures


def test_t10_cli_sha_binding_rejects_mismatch():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--execution-authorized",
         "--authorized-target-sha", "0" * 40],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "J1_SHA_BINDING_MISMATCH" in (proc.stdout + proc.stderr)
    assert not v41.OUTPUT_ROOT.exists()


def test_t10_sha_binding_exact_equality_both_refs():
    head = subprocess.run(
        ["git", "-C", str(v41.REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    binding = v41.verify_execution_sha_binding(v41.REPO_ROOT, head)
    assert binding["HEAD"] == head
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.verify_execution_sha_binding(v41.REPO_ROOT, "0" * 40)
    assert excinfo.value.check_id == "J1_SHA_BINDING_MISMATCH"


def test_t10_scoped_dirty_checks(tmp_path, monkeypatch):
    def git_stub(returncode):
        def _run(cmd, *args, **kwargs):
            assert cmd[0] == "git" and "diff" in cmd and "HEAD" in cmd
            for rel in v41.SCOPED_TRACKED_PATHS:
                assert rel in cmd
            return SimpleNamespace(returncode=returncode, stdout="", stderr="")

        return _run

    monkeypatch.setattr(v41.subprocess, "run", git_stub(1))
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.verify_scoped_clean(tmp_path)
    assert excinfo.value.check_id == "J1_TRACKED_DIRTY"

    monkeypatch.setattr(v41.subprocess, "run", git_stub(0))
    v41.verify_scoped_clean(tmp_path)  # must not raise


def test_t10_runner_refuses_scoped_dirty_before_root_creation(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()

    def dirty_run(cmd, *args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(v41.subprocess, "run", dirty_run)
    root = tmp_path / "dirty_run_root"
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.run_v41_confirmation(
            execution_authorized=True,
            authorized_target_sha="d" * 40,
            fake_runner=True,
            output_root=root,
            structural_authority_path=world.authority_file(tmp_path),
            counts_by_source=real_counts,
            check_git=False,
            check_scoped_dirty=True,
            constructors=world.constructors,
        )
    assert excinfo.value.check_id == "J1_TRACKED_DIRTY"
    assert not root.exists()


def test_t10_runner_default_deny_and_existing_root_refusal(tmp_path, monkeypatch, real_counts):
    with pytest.raises(PermissionError):
        v41.run_v41_confirmation(execution_authorized=False)

    world = FakeWorld()
    root = tmp_path / "existing"
    root.mkdir()
    with pytest.raises(FileExistsError):
        v41.run_v41_confirmation(
            execution_authorized=True,
            authorized_target_sha="a" * 40,
            fake_runner=True,
            output_root=root,
            structural_authority_path=world.authority_file(tmp_path),
            counts_by_source=real_counts,
            check_git=False,
            check_scoped_dirty=False,
            constructors=world.constructors,
        )
    assert not any(root.iterdir())  # nothing written into the pre-existing root


# ---------------------------------------------------------------------------
# T11: record schema, decoder-parameter contract (J9), cross-lane J6
# ---------------------------------------------------------------------------


def test_t11_schema_settings_and_call_contract(tmp_path, monkeypatch, real_counts):
    calls: list[dict] = []
    outcome = make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=calls, name="schema")

    records = json.loads((root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    assert len(records) == 18
    assert [r["call_id"] for r in records] == [f"C{i:02d}" for i in range(1, 19)]
    for rec in records:
        assert set(rec.keys()) == set(v41.RECORD_FIELDS)
        assert rec["max_iter"] == 90 and rec["damping_alpha"] == 1.0
        assert rec["wrong_codeword"] == (rec["syndrome_ok"] and not rec["exact_l2"])
        ok, msg = v41.validate_record_schema(rec)
        assert ok, msg
    assert all(c["keys"] == set(v41.ALLOWED_CALL_KEYS) for c in calls)
    assert all(c["max_iter"] == 90 and c["damping_alpha"] == 1.0 for c in calls)
    assert v41.POLYNOMIAL == 37
    assert GF2mField.create(32).primitive_polynomial == 37
    assert result["decoder_calls_completed"] == 18


def test_t11_j9_warm_start_and_setting_deviation_rejected():
    base = {
        "H": None, "source": "1M", "block_seed": 390107, "lane": "lane_c",
        "construction_seed": 383102, "counts": None, "max_iter": 90,
        "damping_alpha": 1.0, "fake_runner": False, "field": None,
    }
    v41.validate_decoder_contract(base, v41.DECODER_SETTING)  # must not raise

    warm = dict(base, warm_start=True)
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.validate_decoder_contract(warm, v41.DECODER_SETTING)
    assert excinfo.value.check_id == "J9"

    drifted = dict(base, max_iter=60)
    with pytest.raises(v41.IntegrityFailure) as excinfo:
        v41.validate_decoder_contract(drifted, v41.DECODER_SETTING)
    assert excinfo.value.check_id == "J9"


def test_t11_j6_cross_lane_errors_initial_injection(tmp_path, monkeypatch, real_counts):
    def _eval(**kwargs):
        shift = 9 if (kwargs["block_seed"] == 390107 and kwargs["lane"] == "lane_b") else 0
        raw = stub_raw(kwargs, False, 100, False)
        raw["errors_initial"] = INITIAL_BY_BLOCK[kwargs["block_seed"]] + shift
        return raw

    monkeypatch.setattr(v41, "evaluate_single_block", _eval)
    world = FakeWorld()
    root = tmp_path / "j6"
    result = v41.run_v41_confirmation(
        execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        check_git=False,
        check_scoped_dirty=False,
        constructors=world.constructors,
    )
    assert result["terminal_state"] == v41.TERMINAL_EVIDENCE_INVALID
    assert any(cid == "J6" for cid, _ in result["integrity_failures"])
    summary = json.loads((root / "v41_summary.json").read_text(encoding="utf-8"))
    assert summary["aggregates"] == {}  # no performance aggregation on invalid evidence


# ---------------------------------------------------------------------------
# T12: writer contract - file-set exactness, CSV/JSON parity, summary contents
# ---------------------------------------------------------------------------


def test_t12_writer_contract_full_run(tmp_path, monkeypatch, real_counts):
    outcome = make_positional_outcome({})
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="writer")

    names = {p.name for p in root.iterdir()}
    assert names == {"v41_confirm_records.json", "v41_confirm_records.csv", "v41_summary.json"}
    assert not list(root.glob("*.npz"))

    records = json.loads((root / "v41_confirm_records.json").read_text(encoding="utf-8"))
    with (root / "v41_confirm_records.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(records) == 18
    for row, rec in zip(rows, records):
        for col in v41.RECORD_FIELDS:
            assert row[col] == str(v41._csv_value(rec[col]))

    summary_text = (root / "v41_summary.json").read_text(encoding="utf-8")
    summary = json.loads(summary_text)
    # terminal determination precedes the gate-detail display (D4)
    assert summary_text.index('"terminal_state"') < summary_text.index('"gate_evaluation"')
    assert summary["terminal_state"] == v41.TERMINAL_BOTH_LANES_RETAINED
    assert summary["terminal_reason"] is None
    acc = summary["accounting"]
    assert acc["decoder_calls_planned"] == {"total": 18}
    assert acc["decoder_calls_started"] == {"total": 18}
    assert acc["decoder_calls_completed"] == {"total": 18}
    assert acc["structural_reconstruction_decoder_calls"] == 0
    assert acc["preflight_decoder_calls"] == 0
    assert summary["aggregates"]["per_lane"]["lane_c"]["exact_total"] == 9
    assert summary["aggregates"]["per_lane"]["lane_b"]["exact_total"] == 9
    assert summary["aggregates"]["per_source"]["1M"]["calls"] == 6
    assert summary["aggregates"]["wrong_total"] == 0
    for lane in ("lane_c", "lane_b"):
        gate = summary["gate_evaluation"][lane]
        assert gate["passed"] is True
        assert set(gate.keys()) >= {
            "g1_overall_exact_ge_7_of_9", "g2_every_source_ge_2_of_3", "g3_wrong_zero",
        }
    assert summary["master_stop_rule"] == v41.MASTER_STOP_RULE
    assert summary["statistics_note"]
    assert summary["claim_boundary"]
    prov = summary["provenance"]
    assert prov["predecessor_plan_sha"] == v41.PREDECESSOR_PLAN_SHA
    assert prov["predecessor_execution_sha"] == v41.PREDECESSOR_EXECUTION_SHA
    assert prov["sha_binding"] is None or set(prov["sha_binding"]) == {"HEAD", v41.BRANCH_REF}
    assert summary["npz_policy"]["any_npz_output_written"] is False


def test_t12_writer_refuses_non_empty_root(tmp_path):
    root = tmp_path / "occupied"
    root.mkdir()
    (root / "stale.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        v41.write_v41_outputs(root, [], {})


def test_t12_all_four_terminals_reachable_via_runner(tmp_path, monkeypatch, real_counts):
    # BOTH retained
    result, _ = run_scenario(tmp_path, monkeypatch, real_counts, make_positional_outcome({}), name="both")
    assert result["terminal_state"] == v41.TERMINAL_BOTH_LANES_RETAINED

    # C only: lane_c 9/9, lane_b below G1
    def outcome_c_only(kwargs):
        return (kwargs["lane"] == "lane_c", 0 if kwargs["lane"] == "lane_c" else 100)

    result, _ = run_scenario(tmp_path, monkeypatch, real_counts, outcome_c_only, name="conly")
    assert result["terminal_state"] == v41.TERMINAL_C_ONLY_RETAINED

    # B only: mirror
    def outcome_b_only(kwargs):
        return (kwargs["lane"] == "lane_b", 0 if kwargs["lane"] == "lane_b" else 100)

    result, _ = run_scenario(tmp_path, monkeypatch, real_counts, outcome_b_only, name="bonly")
    assert result["terminal_state"] == v41.TERMINAL_B_ONLY_RETAINED

    # both gates failed
    result, _ = run_scenario(
        tmp_path, monkeypatch, real_counts, lambda kwargs: (False, 100, False), name="none"
    )
    assert result["terminal_state"] == v41.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert result["terminal_reason"] == v41.REASON_BOTH_LANES_GATES_FAILED
