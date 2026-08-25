"""Focused V40P0 tests (T1-T16) for the decoder-cap diagnostic runner.

All tests are fake-runner / stub-evaluator or decoder-free. No production
decoder is invoked, no official V40 output root is created, and no NPZ is
read or written (the read-only V25 counts loader stays allowed).
"""

from __future__ import annotations

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
    v40_decoder_cap_diagnostic as v40,
)

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v40_decoder_cap_diagnostic.py"

PHASE_AB_BLOCKS = frozenset({390101, 390102, 390103})
INITIAL_BY_BLOCK = {390101: 252, 390102: 258, 390103: 274, 390106: 300, 390206: 310, 390306: 320}


@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()


def phase_of(kwargs: dict) -> str:
    if kwargs["block_seed"] in PHASE_AB_BLOCKS:
        return "phase_a" if kwargs["damping_alpha"] == 1.0 else "phase_b"
    return "probe"


# ---------------------------------------------------------------------------
# Fake world (accepted V39 pattern, adapted; no real construction cost)
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
            for source in v40.SOURCE_ORDER:
                for seed in v40.CONSTRUCTION_SEEDS[lane][source]:
                    self.constructors[lane](source=source, seed=seed)
        records: list[dict] = []
        for source in v40.SOURCE_ORDER:
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
        ph = phase_of(kwargs)
        if calls is not None:
            calls.append({"phase": ph, "max_iter": kwargs["max_iter"],
                          "damping_alpha": kwargs["damping_alpha"],
                          "block_seed": kwargs["block_seed"], "lane": kwargs["lane"]})
        result = outcome(kwargs)
        if len(result) == 2:
            exact, final = result
            syn = None
        else:
            exact, final, syn = result
        return stub_raw(kwargs, exact, final, syn)

    monkeypatch.setattr(v40, "evaluate_single_block", _eval)
    return _eval


def run_scenario(tmp_path, monkeypatch, real_counts, outcome, calls=None, name="run"):
    world = FakeWorld()
    install_stub(monkeypatch, outcome, calls)
    root = tmp_path / name
    result = v40.run_v40_diagnostic(
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


# Scenario factories (fresh counters per run).


def sc_factory(per_phase):
    counters: dict[str, int] = {}

    def outcome(kwargs):
        ph = phase_of(kwargs)
        counters[ph] = counters.get(ph, 0) + 1
        fn = per_phase.get(ph)
        if fn is None:
            raise AssertionError(f"unexpected call in phase {ph}")
        return fn(counters[ph])

    outcome.counters = counters
    return outcome


def sc_cap_material_confirm():
    return sc_factory({
        "phase_a": lambda n: (True, 0) if n <= 4 else (False, 100),
        "probe": lambda n: (True, 0) if n <= 4 else (False, 50),
    })


def sc_damping_value_confirm():
    return sc_factory({
        "phase_a": lambda n: (False, 100),
        "phase_b": lambda n: (True, 0) if n <= 3 else (False, 90),
        "probe": lambda n: (True, 0) if n <= 4 else (False, 50),
    })


def sc_damping_no_value():
    return sc_factory({
        "phase_a": lambda n: (False, 100),
        "phase_b": lambda n: (False, 90),
    })


def sc_wrong_phase_b():
    return sc_factory({
        "phase_a": lambda n: (False, 100),
        "phase_b": lambda n: (False, 10, True) if n == 5 else (False, 90),
    })


def sc_wrong_phase_a():
    return sc_factory({
        "phase_a": lambda n: (False, 10, True) if n == 5 else (False, 100),
    })


def sc_weak_rescue():
    return sc_factory({
        "phase_a": lambda n: (True, 0) if n <= 2 else (False, 100),
    })


def sc_no_material():
    return sc_factory({
        "phase_a": lambda n: (False, 150),
    })


# ---------------------------------------------------------------------------
# T1: instance extraction (determinism, decoys, drift J1, residual guard J2)
# ---------------------------------------------------------------------------


def _committed_pairs() -> list[dict]:
    return json.loads(Path(v40.PAIRED_AUTHORITY_PATH).read_text(encoding="utf-8"))


def test_t1_extraction_matches_frozen_table_and_ignores_decoys(tmp_path):
    extracted = v40.extract_instances(v40.PAIRED_AUTHORITY_PATH)
    assert extracted == [dict(row) for row in v40.FROZEN_INSTANCES]

    pairs = _committed_pairs()
    decoys = [
        dict(pairs[0], block_seed=999999, discordance_label="BOTH_EXACT"),
        dict(pairs[1], block_seed=999998, discordance_label="C_ONLY_EXACT"),
        dict(pairs[2], block_seed=999997, discordance_label="B_ONLY_EXACT"),
    ]
    doctored = [decoys[0]] + pairs[:3] + [decoys[1]] + pairs[3:] + [decoys[2]]
    path = tmp_path / "decoys.json"
    path.write_text(json.dumps(doctored), encoding="utf-8")
    assert v40.extract_instances(path) == extracted


@pytest.mark.parametrize("mutation", ["residual", "matrix_id", "reorder", "delete", "add"])
def test_t1_extraction_drift_raises_j1(tmp_path, mutation):
    pairs = _committed_pairs()
    if mutation == "residual":
        target = next(r for r in pairs if r["discordance_label"] == "NEITHER_EXACT")
        target["c_errors_final"] += 1
    elif mutation == "matrix_id":
        target = next(r for r in pairs if r["discordance_label"] == "NEITHER_EXACT")
        target["b_matrix_id"] = "lane_b_1M_s999999"
    elif mutation == "reorder":
        neither_idx = [i for i, r in enumerate(pairs) if r["discordance_label"] == "NEITHER_EXACT"]
        i, j = neither_idx[0], neither_idx[1]
        pairs[i], pairs[j] = pairs[j], pairs[i]
    elif mutation == "delete":
        neither_idx = [i for i, r in enumerate(pairs) if r["discordance_label"] == "NEITHER_EXACT"]
        del pairs[neither_idx[0]]
    elif mutation == "add":
        extra = dict(pairs[0], block_seed=399999, discordance_label="NEITHER_EXACT")
        pairs.append(extra)
    path = tmp_path / f"drift_{mutation}.json"
    path.write_text(json.dumps(pairs), encoding="utf-8")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.extract_instances(path)
    assert excinfo.value.check_id == "J1"


def test_t1_j2_zero_residual_guard(tmp_path, monkeypatch):
    real = [dict(row) for row in v40.extract_instances(v40.PAIRED_AUTHORITY_PATH)]
    tampered = [dict(row) for row in real]
    tampered[0]["v39_reference_errors_final"] = 0
    monkeypatch.setattr(v40, "FROZEN_INSTANCES", tuple(tampered))
    pairs = _committed_pairs()
    target = next(r for r in pairs if r["discordance_label"] == "NEITHER_EXACT")
    target["c_errors_final"] = 0  # keep file consistent with the tampered table
    path = tmp_path / "zero_residual.json"
    path.write_text(json.dumps(pairs), encoding="utf-8")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.extract_instances(path)
    assert excinfo.value.check_id == "J2"


# ---------------------------------------------------------------------------
# T2: reconstruction determinism + strict metric match (incl. permutations)
# ---------------------------------------------------------------------------


def test_t2_reconstruction_deterministic_and_tamper_detection(tmp_path):
    world = FakeWorld()
    field = GF2mField.create(32)
    only = frozenset({("lane_c", "1M", 383102), ("lane_b", "1M", 382102)})
    authority = world.authority_file(tmp_path)
    first = v40.reconstruct_v40_matrices(authority, field=field, constructors=world.constructors, only=only)
    second = v40.reconstruct_v40_matrices(authority, field=field, constructors=world.constructors, only=only)
    assert set(first.keys()) == only == set(second.keys())
    for key in only:
        m1, met1 = first[key]
        m2, met2 = second[key]
        assert np.array_equal(m1, m2)
        assert met1 == met2
    _, lane_c_metrics = first[("lane_c", "1M", 383102)]
    assert "position_permutations" in lane_c_metrics

    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"] == "lane_b_1M_s382102")
    victim["rank_GF32"] = int(victim["rank_GF32"]) - 1
    bad_rank = tmp_path / "bad_rank.json"
    bad_rank.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.reconstruct_v40_matrices(bad_rank, field=field, constructors=world.constructors, only=only)
    assert excinfo.value.check_id == "RECONSTRUCTION_MISMATCH"

    records = json.loads(authority.read_text(encoding="utf-8"))
    victim = next(r for r in records if r["matrix_id"] == "lane_c_1M_s383102")
    victim["position_permutations"] = [[5, 5], [5, 5]]
    bad_perms = tmp_path / "bad_perms.json"
    bad_perms.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.reconstruct_v40_matrices(bad_perms, field=field, constructors=world.constructors, only=only)
    assert excinfo.value.check_id == "RECONSTRUCTION_MISMATCH"


def test_usage_rows_are_twelve_with_ten_unique_ids():
    rows = v40.matrix_usage_rows()
    assert len(rows) == 12
    ids = [r["matrix_id"] for r in rows]
    assert len(set(ids)) == 10
    assert sum(1 for r in rows if r["usage"] == "phase_ab") == 6
    assert sum(1 for r in rows if r["usage"] == "probe") == 6


# ---------------------------------------------------------------------------
# T3: representative-ordinal rule (unique/tied max) and frozen constants
# ---------------------------------------------------------------------------


def _write_summary_doc(tmp_path, name, lane_counts):
    doc = {"aggregates": {
        lane: {"by_construction_seed_ordinal": {str(o): {"exact_count": c} for o, c in counts.items()}}
        for lane, counts in lane_counts.items()
    }}
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_t3_representative_ordinals_synthetic_and_committed(tmp_path):
    unique = _write_summary_doc(tmp_path, "unique.json", {
        "lane_c": {1: 5, 2: 9, 3: 7}, "lane_b": {1: 3, 2: 4, 3: 4}})
    assert v40.recompute_representative_ordinals(unique) == {"lane_c": 2, "lane_b": 2}

    tied_top = _write_summary_doc(tmp_path, "tied_top.json", {
        "lane_c": {1: 5, 2: 9, 3: 9}, "lane_b": {1: 8, 2: 3, 3: 1}})
    assert v40.recompute_representative_ordinals(tied_top) == {"lane_c": 2, "lane_b": 1}

    tied_low = _write_summary_doc(tmp_path, "tied_low.json", {
        "lane_c": {1: 9, 2: 9, 3: 3}, "lane_b": {1: 1, 2: 2, 3: 3}})
    assert v40.recompute_representative_ordinals(tied_low) == {"lane_c": 1, "lane_b": 3}

    doc = json.loads(Path(v40.SUMMARY_AUTHORITY_PATH).read_text(encoding="utf-8"))
    agg = doc["aggregates"]
    assert {o: agg["lane_c"]["by_construction_seed_ordinal"][o]["exact_count"] for o in ("1", "2", "3")} == {"1": 11, "2": 12, "3": 10}
    assert {o: agg["lane_b"]["by_construction_seed_ordinal"][o]["exact_count"] for o in ("1", "2", "3")} == {"1": 10, "2": 11, "3": 10}
    assert v40.verify_representative_ordinals(v40.SUMMARY_AUTHORITY_PATH) == {"lane_c": 2, "lane_b": 2}

    drifted = _write_summary_doc(tmp_path, "drifted.json", {
        "lane_c": {1: 5, 2: 6, 3: 9}, "lane_b": {1: 1, 2: 2, 3: 3}})
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.verify_representative_ordinals(drifted)
    assert excinfo.value.check_id == "J3"


# ---------------------------------------------------------------------------
# T4: probe-seed registry validation (J4)
# ---------------------------------------------------------------------------


def test_t4_probe_seed_validator():
    ok, msg = v40.validate_probe_seeds()
    assert ok, msg
    assert v40.PROBE_BLOCK_SEEDS == {"1M": 390106, "1p5M": 390206, "2M": 390306}

    dup = dict(v40.PROBE_BLOCK_SEEDS, **{"1p5M": 390106})
    ok, msg = v40.validate_probe_seeds(dup)
    assert not ok and "unique" in msg

    wrong_shape = {"1M": 390106, "1p5M": 390206}
    ok, msg = v40.validate_probe_seeds(wrong_shape)
    assert not ok and "sources" in msg

    overlap_v36 = dict(v40.PROBE_BLOCK_SEEDS, **{"1M": 360101})
    ok, msg = v40.validate_probe_seeds(overlap_v36)
    assert not ok and "overlap" in msg

    overlap_v39 = dict(v40.PROBE_BLOCK_SEEDS, **{"2M": 390305})
    ok, msg = v40.validate_probe_seeds(overlap_v39)
    assert not ok and "overlap" in msg


# ---------------------------------------------------------------------------
# T5: posterior-binding sentinels on the new probe blocks (real counts)
# ---------------------------------------------------------------------------


def test_t5_posterior_binding_sentinels_on_new_probes(real_counts):
    results = v40.posterior_binding_preflight(real_counts)
    assert set(results.keys()) == set(v40.SOURCE_ORDER)
    for source, checks in results.items():
        assert checks["probe_block_seed"] == v40.PROBE_BLOCK_SEEDS[source]
        assert checks["bob_gt_31"] is True
        assert checks["captured_equals_bob"] is True
        assert checks["corrected_equals_direct"] is True
        assert checks["corrected_differs_u2bob_arraywise"] is True
        assert checks["corrected_differs_u2bob_maxabs"] is True
        assert checks["argmax_divergence"] is True


# ---------------------------------------------------------------------------
# T6: IMP math fixtures (boundary 0.25, empty subset, zero denominator J2,
# matched-subset vs pooled medians)
# ---------------------------------------------------------------------------


def _fixture_instances(refs):
    return [
        dict(v40.FROZEN_INSTANCES[i], v39_reference_errors_final=refs[i])
        for i in range(12)
    ]


def _fixture_records(exacts, finals):
    recs = []
    for inst, ex, fi in zip(v40.FROZEN_INSTANCES, exacts, finals):
        recs.append({
            "lane": inst["lane"],
            "source": inst["source"],
            "block_seed": inst["block_seed"],
            "matrix_id": inst["matrix_id"],
            "errors_initial": inst["v39_reference_errors_initial"],
            "errors_final": fi,
            "exact_l2": ex,
        })
    return recs


def test_t6_imp_boundary_exact_quarter():
    instances = _fixture_instances([100] * 12)
    records = _fixture_records([False] * 12, [75] * 12)
    report = v40.residual_improvement(records, instances, label="IMP_A")
    assert report["imp"] == 0.25
    assert report["median_errors_final_subset"] == 75.0
    assert report["median_v39_residual_subset"] == 100.0
    assert v40.phase_b_trigger(0, 1, report["imp"]) is True
    assert v40.phase_b_trigger(0, 1, 0.2499999999) is False


def test_t6_imp_empty_subset_is_one():
    instances = _fixture_instances([100] * 12)
    records = _fixture_records([True] * 12, [0] * 12)
    report = v40.residual_improvement(records, instances)
    assert report["imp"] == 1.0
    assert report["matched_subset_size"] == 0
    assert report["median_errors_final_subset"] is None


def test_t6_imp_zero_denominator_raises_j2():
    instances = _fixture_instances([0] * 7 + [1] * 5)  # even-count median of subset is 0
    records = _fixture_records([False] * 12, [50] * 12)
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.residual_improvement(records, instances)
    assert excinfo.value.check_id == "J2"


def test_t6_imp_matched_subset_vs_pooled_median():
    instances = [dict(row) for row in v40.FROZEN_INSTANCES]
    finals = [inst["v39_reference_errors_final"] - 26 for inst in instances]
    exacts = [True] + [False] * 11  # rescue A01 (ref 139) -> S_P has 11 members
    records = _fixture_records(exacts, finals)
    report = v40.residual_improvement(records, instances, label="IMP_A")
    assert report["matched_subset_size"] == 11
    assert report["median_v39_residual_subset"] == 171.0  # median of refs minus A01
    assert report["median_errors_final_subset"] == 145.0
    assert report["pooled_v39_median_all12"] == 155.0
    assert report["imp"] == pytest.approx(1.0 - 145.0 / 171.0)


# ---------------------------------------------------------------------------
# T7: call accounting across routing scenarios (fake mode, zero production decode)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scenario_factory,executed,total,terminal,reason",
    [
        (sc_cap_material_confirm, ["phase_a", "probe"], 18, v40.TERMINAL_PROBE_CONFIRM_ALLOWED, None),
        (sc_damping_value_confirm, ["phase_a", "phase_b", "probe"], 30, v40.TERMINAL_PROBE_CONFIRM_ALLOWED, None),
        (sc_damping_no_value, ["phase_a", "phase_b"], 24, v40.TERMINAL_GO_STRUCTURE, v40.REASON_DAMPING_NO_VALUE),
        (sc_wrong_phase_b, ["phase_a", "phase_b"], 24, v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, v40.REASON_WRONG_CODEWORD_PHASE_B),
        (sc_wrong_phase_a, ["phase_a"], 12, v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, v40.REASON_WRONG_CODEWORD_PHASE_A),
        (sc_weak_rescue, ["phase_a"], 12, v40.TERMINAL_GO_STRUCTURE, v40.REASON_WEAK_EXACT_RESCUE),
        (sc_no_material, ["phase_a"], 12, v40.TERMINAL_GO_STRUCTURE, v40.REASON_NO_MATERIAL_CAP_EFFECT),
    ],
)
def test_t7_call_accounting_scenarios(tmp_path, monkeypatch, real_counts, scenario_factory, executed, total, terminal, reason):
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, scenario_factory())
    assert result["terminal_state"] == terminal
    assert result["terminal_reason"] == reason
    assert result["decoder_calls_completed"] == total <= v40.HARD_CALL_CAP
    accounting = result["summary"]["accounting"]
    assert accounting["executed_phases"] == executed
    assert accounting["decoder_calls_completed"]["total"] == total
    assert accounting["decoder_calls_started"]["total"] == total
    for phase, cap in v40.BUDGET_CAPS.items():
        if phase in executed:
            assert accounting["decoder_calls_completed"][phase] == cap
            assert accounting["decoder_calls_started"][phase] == cap
        else:
            assert accounting["decoder_calls_completed"][phase] == 0
            assert accounting["decoder_calls_started"][phase] == 0
    files = {p.name for p in root.iterdir()}
    assert files == {"v40_diagnostic_records.json", "v40_diagnostic_records.csv", "v40_summary.json"}
    assert not any(name.endswith(".npz") for name in files)


# ---------------------------------------------------------------------------
# T8: record schema, per-phase settings, decoder-parameter contract (J10)
# ---------------------------------------------------------------------------


def test_t8_records_schema_settings_and_decoder_contract(tmp_path, monkeypatch, real_counts):
    calls: list[dict] = []
    result, root = run_scenario(tmp_path, monkeypatch, real_counts, sc_damping_value_confirm(), calls=calls)
    assert result["terminal_state"] == v40.TERMINAL_PROBE_CONFIRM_ALLOWED

    phase_calls = {ph: [(c["max_iter"], c["damping_alpha"]) for c in calls if c["phase"] == ph]
                   for ph in ("phase_a", "phase_b", "probe")}
    assert len(phase_calls["phase_a"]) == 12 and set(phase_calls["phase_a"]) == {(90, 1.0)}
    assert len(phase_calls["phase_b"]) == 12 and set(phase_calls["phase_b"]) == {(90, 0.7)}
    assert len(phase_calls["probe"]) == 6 and set(phase_calls["probe"]) == {(90, 0.7)}
    assert [c["block_seed"] for c in calls if c["phase"] == "probe"] == [390106, 390106, 390206, 390206, 390306, 390306]
    assert [c["lane"] for c in calls if c["phase"] == "probe"] == ["lane_c", "lane_b"] * 3

    records = json.loads((root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    assert len(records) == 30
    for rec in records:
        ok, msg = v40.validate_record_schema(rec)
        assert ok, msg
        assert rec["wrong_codeword"] == (rec["syndrome_ok"] and not rec["exact_l2"])
        if rec["phase"] == "probe":
            assert rec["v39_reference_errors_final"] is None
            assert rec["v39_reference_exact_l2"] is None
            assert rec["rescued_vs_v39"] is None
        else:
            assert rec["rescued_vs_v39"] == (rec["exact_l2"] and not rec["v39_reference_exact_l2"])

    with (root / "v40_diagnostic_records.csv").open(encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    assert len(lines) - 1 == len(records)

    assert v40.POLYNOMIAL == 37
    assert GF2mField.create(32).primitive_polynomial == 37
    assert not any("warm" in key for key in v40.ALLOWED_CALL_KEYS)

    good_params = {"H": None, "source": "1M", "block_seed": 390101, "lane": "lane_c",
                   "construction_seed": 383101, "counts": None, "max_iter": 90,
                   "damping_alpha": 1.0, "fake_runner": True, "field": None}
    v40.validate_decoder_contract(good_params, (90, 1.0))  # must not raise
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.validate_decoder_contract(dict(good_params, warm_start_state={"x": 1}), (90, 1.0))
    assert excinfo.value.check_id == "J10"
    with pytest.raises(v40.IntegrityFailure):
        v40.validate_decoder_contract(good_params, (90, 0.7))
    with pytest.raises(v40.IntegrityFailure):
        v40.validate_decoder_contract(dict(good_params, max_iter=60), (90, 1.0))


# ---------------------------------------------------------------------------
# T9: terminal machine truth table (total/disjoint, invalid precedence,
# impossible combinations) + exhaustive probe judgment table
# ---------------------------------------------------------------------------


PROBE_VARIANTS = (
    None,
    {"exact_total": 0, "exact_lane_c": 0, "exact_lane_b": 0, "wrong_lane_c": 0, "wrong_lane_b": 0},
    {"exact_total": 3, "exact_lane_c": 2, "exact_lane_b": 1, "wrong_lane_c": 0, "wrong_lane_b": 0},
    {"exact_total": 4, "exact_lane_c": 2, "exact_lane_b": 2, "wrong_lane_c": 0, "wrong_lane_b": 0},
    {"exact_total": 5, "exact_lane_c": 3, "exact_lane_b": 2, "wrong_lane_c": 0, "wrong_lane_b": 0},
    {"exact_total": 4, "exact_lane_c": 1, "exact_lane_b": 3, "wrong_lane_c": 0, "wrong_lane_b": 0},
    {"exact_total": 4, "exact_lane_c": 2, "exact_lane_b": 2, "wrong_lane_c": 1, "wrong_lane_b": 0},
)


def test_t9_machine_truth_table_total_disjoint_invalid_precedence():
    seen_terminals: set[str] = set()
    seen_reasons: set[str] = set()
    j12_unreachable = 0
    checked = 0
    for w_a, r_a, imp_a, b_ran, w_b, r_b_new, p_ran, probe in itertools.product(
        (0, 1), (0, 1, 2, 3, 4), (0.0, 0.3), (False, True), (0, 1), (0, 2, 3), (False, True), PROBE_VARIANTS
    ):
        checked += 1
        kwargs = dict(
            integrity_ok=True, w_a=w_a, r_a=r_a, imp_a=imp_a, phase_b_ran=b_ran,
            w_b=w_b, r_b_new=r_b_new, probe_ran=p_ran, probe_aggregates=probe,
        )
        try:
            terminal, term_reason, trace = v40.determine_v40_terminal(**kwargs)
        except v40.IntegrityFailure as exc:
            assert exc.check_id == "J12"  # provably unreachable combination
            j12_unreachable += 1
            continue
        assert terminal in v40.ALL_TERMINALS
        again = v40.determine_v40_terminal(**kwargs)
        assert again[0] == terminal and again[1] == term_reason  # disjoint/deterministic
        seen_terminals.add(terminal)
        if term_reason:
            seen_reasons.add(term_reason)

    assert checked == 2 * 5 * 2 * 2 * 2 * 3 * 2 * len(PROBE_VARIANTS)
    assert seen_terminals == {
        v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION,
        v40.TERMINAL_GO_STRUCTURE,
        v40.TERMINAL_PROBE_INCONCLUSIVE,
        v40.TERMINAL_PROBE_CONFIRM_ALLOWED,
    }
    assert seen_reasons == {
        v40.REASON_WRONG_CODEWORD_PHASE_A,
        v40.REASON_WRONG_CODEWORD_PHASE_B,
        v40.REASON_WEAK_EXACT_RESCUE,
        v40.REASON_NO_MATERIAL_CAP_EFFECT,
        v40.REASON_DAMPING_NO_VALUE,
    }
    assert j12_unreachable > 0

    # Impossible combinations cannot fire: probe data is ignored whenever W_A > 0.
    terminal, term_reason, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=1, r_a=4, imp_a=0.9, phase_b_ran=True, w_b=1,
        r_b_new=9, probe_ran=True, probe_aggregates=PROBE_VARIANTS[3],
    )
    assert terminal == v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert term_reason == v40.REASON_WRONG_CODEWORD_PHASE_A

    # EVIDENCE_INVALID precedence overrides every combination.
    for w_a, r_a, imp_a in itertools.product((0, 1), (0, 2, 4), (0.0, 0.3)):
        terminal, term_reason, trace = v40.determine_v40_terminal(
            integrity_ok=False, w_a=w_a, r_a=r_a, imp_a=imp_a,
            phase_b_ran=True, w_b=1, r_b_new=5, probe_ran=True, probe_aggregates=PROBE_VARIANTS[3],
        )
        assert terminal == v40.TERMINAL_EVIDENCE_INVALID and term_reason is None
        assert trace == ["rule_0:integrity_first"]


def test_t9_probe_truth_table_exhaustive_and_mutually_exclusive():
    for exact_total, lane_c, lane_b, wrong in itertools.product(range(7), range(4), range(4), (0, 1)):
        terminal, _ = v40.judge_probe(exact_total, lane_c, lane_b, wrong)
        if wrong > 0 or exact_total <= 2:
            expected = v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
        elif exact_total == 3:
            expected = v40.TERMINAL_PROBE_INCONCLUSIVE
        elif lane_c < 2 or lane_b < 2:
            expected = v40.TERMINAL_PROBE_INCONCLUSIVE
        else:
            expected = v40.TERMINAL_PROBE_CONFIRM_ALLOWED
        assert terminal == expected


# ---------------------------------------------------------------------------
# T10: boundary cases (phase routing + probe judgments)
# ---------------------------------------------------------------------------


def test_t10_boundaries_phase_routing():
    # R_A = 4 with W_A > 0 -> STOP_BC (probe unreachable despite strong rescues).
    terminal, reason, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=1, r_a=4, imp_a=0.9, probe_ran=True,
        probe_aggregates=PROBE_VARIANTS[3])
    assert (terminal, reason) == (v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, v40.REASON_WRONG_CODEWORD_PHASE_A)

    # R_A = 4 with W_A = 0 -> CAP_MATERIAL -> probe at (90, 1.0).
    assert v40.resolve_probe_setting(True, False) == (90, 1.0)
    terminal, reason, trace = v40.determine_v40_terminal(
        integrity_ok=True, w_a=0, r_a=4, imp_a=0.0, probe_ran=True,
        probe_aggregates=PROBE_VARIANTS[3])
    assert (terminal, reason) == (v40.TERMINAL_PROBE_CONFIRM_ALLOWED, None)
    assert v40.SIGNAL_CAP_MATERIAL in trace[-2]

    # R_A = 2-3 with W_A = 0 -> WEAK_RESIDUAL -> GO_STRUCTURE even when IMP_A >= 0.25.
    for r_a in (2, 3):
        terminal, reason, _ = v40.determine_v40_terminal(
            integrity_ok=True, w_a=0, r_a=r_a, imp_a=0.9)
        assert (terminal, reason) == (v40.TERMINAL_GO_STRUCTURE, v40.REASON_WEAK_EXACT_RESCUE)

    # R_A = 1 with IMP_A = 0.25 exactly -> Phase B trigger holds.
    assert v40.phase_b_trigger(0, 1, 0.25) is True
    terminal, _, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=0, r_a=1, imp_a=0.25, phase_b_ran=True,
        w_b=0, r_b_new=0)
    assert terminal == v40.TERMINAL_GO_STRUCTURE  # via DAMPING_NO_VALUE (r_b_new=0)

    # R_B_new = 3 boundary: DAMPING_VALUE only when W_B = 0. With W_B > 0 the
    # first-match-wins machine terminates at rule 5a before any damping judgment.
    assert v40.resolve_probe_setting(False, True) == (90, 0.7)
    terminal, reason, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=0, r_a=1, imp_a=0.5, phase_b_ran=True,
        w_b=0, r_b_new=3, probe_ran=True, probe_aggregates=PROBE_VARIANTS[3])
    assert terminal == v40.TERMINAL_PROBE_CONFIRM_ALLOWED
    terminal, reason, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=0, r_a=1, imp_a=0.5, phase_b_ran=True,
        w_b=1, r_b_new=3)
    assert (terminal, reason) == (v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, v40.REASON_WRONG_CODEWORD_PHASE_B)
    # W_B = 0 with R_B_new below the boundary -> DAMPING_NO_VALUE.
    terminal, reason, _ = v40.determine_v40_terminal(
        integrity_ok=True, w_a=0, r_a=1, imp_a=0.5, phase_b_ran=True,
        w_b=0, r_b_new=2)
    assert (terminal, reason) == (v40.TERMINAL_GO_STRUCTURE, v40.REASON_DAMPING_NO_VALUE)

    # R_A <= 1 boundary split by IMP_A.
    terminal, reason, _ = v40.determine_v40_terminal(integrity_ok=True, w_a=0, r_a=1, imp_a=0.24)
    assert (terminal, reason) == (v40.TERMINAL_GO_STRUCTURE, v40.REASON_NO_MATERIAL_CAP_EFFECT)


def test_t10_boundaries_probe_judgments():
    assert v40.judge_probe(2, 2, 0, 0)[0] == v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert v40.judge_probe(3, 2, 1, 0)[0] == v40.TERMINAL_PROBE_INCONCLUSIVE
    assert v40.judge_probe(4, 2, 2, 0)[0] == v40.TERMINAL_PROBE_CONFIRM_ALLOWED
    assert v40.judge_probe(4, 1, 3, 0)[0] == v40.TERMINAL_PROBE_INCONCLUSIVE
    assert v40.judge_probe(4, 3, 1, 0)[0] == v40.TERMINAL_PROBE_INCONCLUSIVE
    assert v40.judge_probe(5, 3, 2, 0)[0] == v40.TERMINAL_PROBE_CONFIRM_ALLOWED
    assert v40.judge_probe(6, 3, 3, 1)[0] == v40.TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION
    assert v40.judge_probe(6, 2, 2, 0)[0] == v40.TERMINAL_PROBE_CONFIRM_ALLOWED


# ---------------------------------------------------------------------------
# T11: errors_initial equality (real sampling semantics) + J7 injections
# ---------------------------------------------------------------------------


def test_t11_errors_initial_equalities_and_j7_injection(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()
    root = tmp_path / "real_sampling_run"
    result = v40.run_v40_diagnostic(
        execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,  # v38 fake decode path: real sampling, no production decoder
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        check_git=False,
        check_scoped_dirty=False,
        constructors=world.constructors,
    )
    assert result["terminal_state"] == v40.TERMINAL_GO_STRUCTURE
    assert result["terminal_reason"] == v40.REASON_NO_MATERIAL_CAP_EFFECT

    records = json.loads((root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    assert len(records) == 12
    instances = v40.extract_instances(v40.PAIRED_AUTHORITY_PATH)
    for rec, inst in zip(records, instances):
        assert (rec["lane"], rec["block_seed"]) == (inst["lane"], inst["block_seed"])
        assert rec["errors_initial"] == inst["v39_reference_errors_initial"]

    by_block: dict[int, set[int]] = {}
    for rec in records:
        by_block.setdefault(rec["block_seed"], set()).add(rec["errors_initial"])
    assert all(len(vals) == 1 for vals in by_block.values())

    assert v40.validate_post_evaluation(records, instances) == []

    flipped = json.loads(json.dumps(records))
    flipped[3]["errors_initial"] += 1
    failures = v40.validate_post_evaluation(flipped, instances)
    assert any(cid == "J7" and "A04" in msg for cid, msg in failures)

    cross_bad = json.loads(json.dumps(records))
    cross_bad[1]["errors_initial"] += 3  # break cross-lane equality for block 390101
    failures = v40.validate_post_evaluation(cross_bad, instances)
    assert any(cid == "J7" and "cross-lane" in msg for cid, msg in failures)

    schema_bad = json.loads(json.dumps(records))
    del schema_bad[0]["runtime_s"]
    failures = v40.validate_post_evaluation(schema_bad, instances)
    assert any(cid == "J6" for cid, _ in failures)


# ---------------------------------------------------------------------------
# T12: writer contract, summary contents, NPZ policy, invalid notice
# ---------------------------------------------------------------------------


def _mini_records_and_summary(accounting):
    inst = v40.FROZEN_INSTANCES[0]
    raw = stub_raw({"source": inst["source"], "block_seed": inst["block_seed"],
                    "lane": inst["lane"], "construction_seed": inst["construction_seed"]}, True, 0)
    rec = v40.build_record("phase_a", inst, raw, (90, 1.0), inst)
    summary = v40.build_v40_summary(
        lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE", fake_runner=True,
        authorized_target_sha="f" * 40, sha_binding={"HEAD": "f" * 40},
        counts_provenance={}, accounting=accounting, executed_phases=["phase_a"],
        signals={"A_signal": v40.SIGNAL_CAP_MATERIAL, "B_signal": None},
        improvements={"IMP_A": {"imp": 0.5}}, rescue_wrong_counts={},
        probe_results=None, routing_trace=["rule_2:CAP_MATERIAL"],
        integrity_failures=None, terminal_state=v40.TERMINAL_PROBE_CONFIRM_ALLOWED,
        terminal_reason=None, structural_rows_count=10,
    )
    return [rec], summary


def test_t12_writer_contract_and_overwrite_guard(tmp_path):
    accounting = v40.CallAccounting()
    accounting.started["phase_a"] = accounting.completed["phase_a"] = 12
    records, summary = _mini_records_and_summary(accounting)
    root = tmp_path / "out"
    written = v40.write_v40_outputs(root, records, summary)
    assert written == root
    names = {p.name for p in root.iterdir()}
    assert names == {"v40_diagnostic_records.json", "v40_diagnostic_records.csv", "v40_summary.json"}
    assert not list(root.glob("*.npz"))
    rows_json = json.loads((root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    with (root / "v40_diagnostic_records.csv").open(encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    assert len(lines) - 1 == len(rows_json) == 1
    with pytest.raises(FileExistsError):
        v40.write_v40_outputs(root, records, summary)

    empty = tmp_path / "precreated"
    empty.mkdir()
    v40.write_v40_outputs(empty, records, summary)
    assert (empty / "v40_summary.json").is_file()

    notice = v40.write_invalid_notice(root, [("J5", "test failure")], True)
    payload = json.loads(notice.read_text(encoding="utf-8"))
    assert payload["terminal_state"] == v40.TERMINAL_EVIDENCE_INVALID
    assert payload["performance_interpretation"] == "none"
    assert payload["partial_records_retained_byte_for_byte"] is True


def test_t12_summary_contents_master_rule_claim_boundary():
    accounting = v40.CallAccounting()
    _, summary = _mini_records_and_summary(accounting)
    assert summary["master_stop_rule"] == v40.MASTER_STOP_RULE
    assert "不同时继续优化" in summary["master_stop_rule"]
    assert summary["claim_boundary"] == list(v40.CLAIM_BOUNDARY) and len(summary["claim_boundary"]) >= 5
    assert summary["statistics_note"] == v40.STATISTICS_NOTE
    assert summary["accounting"]["decoder_calls_planned"] == {"total": 30, "phase_a": 12, "phase_b": 12, "probe": 6}
    assert summary["provenance"]["v39_input_identity"]["predecessor_result_sha"] == v40.PREDECESSOR_RESULT_SHA
    assert summary["execution_scope"] == "v40_decoder_only_max30_calls_exactly_once"


def test_t12_npz_policy_rejects_winner_archive_as_authority(tmp_path):
    fake_npz = tmp_path / v40.FORBIDDEN_WINNER_NPZ_NAME
    fake_npz.write_bytes(b"PK\x03\x04")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.reconstruct_v40_matrices(reference_metrics_path=fake_npz)
    assert excinfo.value.check_id == "J9"


# ---------------------------------------------------------------------------
# T13: CLI guards, SHA binding, scoped-dirty checks (J11)
# ---------------------------------------------------------------------------


def test_t13_cli_requires_flags_and_has_no_fake_runner_option():
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


def test_t13_cli_sha_binding_rejects_mismatch():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--execution-authorized",
         "--authorized-target-sha", "0" * 40],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "J11_SHA_BINDING_MISMATCH" in (proc.stdout + proc.stderr)


def test_t13_sha_binding_exact_equality():
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    binding = v40.verify_execution_sha_binding(v40.REPO_ROOT, head)
    assert binding["HEAD"] == head
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.verify_execution_sha_binding(v40.REPO_ROOT, "0" * 40)
    assert excinfo.value.check_id == "J11_SHA_BINDING_MISMATCH"


def test_t13_scoped_dirty_checks(tmp_path, monkeypatch):
    def git_stub(returncode):
        def _run(cmd, *args, **kwargs):
            assert cmd[0] == "git" and "diff" in cmd and "HEAD" in cmd
            for rel in v40.SCOPED_TRACKED_PATHS:
                assert rel in cmd
            return SimpleNamespace(returncode=returncode, stdout="", stderr="")

        return _run

    monkeypatch.setattr(v40.subprocess, "run", git_stub(1))
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.verify_scoped_clean(tmp_path)
    assert excinfo.value.check_id == "J11_TRACKED_DIRTY"

    monkeypatch.setattr(v40.subprocess, "run", git_stub(0))
    v40.verify_scoped_clean(tmp_path)  # must not raise


def test_t13_runner_refuses_scoped_dirty_before_root_creation(tmp_path, monkeypatch, real_counts):
    world = FakeWorld()

    def dirty_run(cmd, *args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(v40.subprocess, "run", dirty_run)
    root = tmp_path / "dirty_run_root"
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.run_v40_diagnostic(
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
    assert excinfo.value.check_id == "J11_TRACKED_DIRTY"
    assert not root.exists()


def test_runner_default_deny_and_existing_root_refusal(tmp_path, monkeypatch, real_counts):
    with pytest.raises(PermissionError):
        v40.run_v40_diagnostic(execution_authorized=False)

    world = FakeWorld()
    root = tmp_path / "existing"
    root.mkdir()
    with pytest.raises(FileExistsError):
        v40.run_v40_diagnostic(
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


# ---------------------------------------------------------------------------
# T14: partial retention after mid-run BaseException
# ---------------------------------------------------------------------------


def test_t14_partial_retention_byte_for_byte(tmp_path, monkeypatch, real_counts):
    def make_fail_at(fail_index):
        counters = {"phase_a": 0}

        def outcome(kwargs):
            if phase_of(kwargs) != "phase_a":
                raise AssertionError("unexpected phase during failure scenario")
            counters["phase_a"] += 1
            if counters["phase_a"] == fail_index:
                raise RuntimeError("simulated decoder crash")
            return (False, 100, False)

        return outcome

    def make_ok_all_phases():
        return lambda kwargs: (False, 100, False)

    with pytest.raises(RuntimeError):
        run_scenario(tmp_path, monkeypatch, real_counts, make_fail_at(5), name="crash")

    fail_root = tmp_path / "crash"
    names = {p.name for p in fail_root.iterdir()}
    assert "v40_diagnostic_records.json" in names
    assert "v40_diagnostic_records.csv" in names
    assert "v40_invalid_notice.json" in names
    assert "v40_summary.json" in names
    notice = json.loads((fail_root / "v40_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["terminal_state"] == v40.TERMINAL_EVIDENCE_INVALID
    summary = json.loads((fail_root / "v40_summary.json").read_text(encoding="utf-8"))
    assert summary["terminal_state"] == v40.TERMINAL_EVIDENCE_INVALID
    assert summary["performance_interpretation_presented"] is False
    assert summary["signals"] == {} and summary["probe_results"] is None
    assert summary["accounting"]["decoder_calls_started"]["phase_a"] == 5
    assert summary["accounting"]["decoder_calls_completed"]["phase_a"] == 4

    ok_root = tmp_path / "okrun"
    run_scenario(tmp_path, monkeypatch, real_counts, make_ok_all_phases(), name="okrun")
    ok_records = json.loads((ok_root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    retained = json.loads((fail_root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    assert retained == ok_records[:4]


def test_t14_keyboard_interrupt_retains_partials(tmp_path, monkeypatch, real_counts):
    counters = {"phase_a": 0}

    def outcome(kwargs):
        counters["phase_a"] += 1
        if counters["phase_a"] == 2:
            raise KeyboardInterrupt
        return (False, 100, False)

    with pytest.raises(KeyboardInterrupt):
        run_scenario(tmp_path, monkeypatch, real_counts, outcome, name="ki")
    root = tmp_path / "ki"
    records = json.loads((root / "v40_diagnostic_records.json").read_text(encoding="utf-8"))
    assert len(records) == 1
    assert "v40_invalid_notice.json" in {p.name for p in root.iterdir()}


# ---------------------------------------------------------------------------
# T15: budget hard cap (structural refusal of a 31st call)
# ---------------------------------------------------------------------------


def test_t15_budget_hard_cap():
    accounting = v40.CallAccounting()
    for _ in range(v40.HARD_CALL_CAP):
        accounting.register_start("phase_a")
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        accounting.register_start("phase_a")
    assert excinfo.value.check_id == "J5"

    accounting.completed["phase_a"] = v40.HARD_CALL_CAP
    failures = accounting.validate_executed(["phase_a"])
    assert any(cid == "J5" and "planned 12" in msg for cid, msg in failures)

    fresh = v40.CallAccounting()
    fresh.started["phase_b"] = 1  # skipped phase consumed a call
    failures = fresh.validate_executed(["phase_a"])
    assert any(cid == "J5" and "skipped" in msg for cid, msg in failures)

    fresh2 = v40.CallAccounting()
    failures = fresh2.validate_executed(["phase_a"])
    assert any(cid == "J5" and "planned 12" in msg for cid, msg in failures)


# ---------------------------------------------------------------------------
# T16: phase gating violations (J12)
# ---------------------------------------------------------------------------


def test_t16_phase_gating_j12():
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.require_phase_b_trigger(1, 0, 0.9)
    assert excinfo.value.check_id == "J12"
    with pytest.raises(v40.IntegrityFailure):
        v40.require_phase_b_trigger(0, 2, 0.9)
    with pytest.raises(v40.IntegrityFailure):
        v40.require_phase_b_trigger(0, 0, 0.2)
    v40.require_phase_b_trigger(0, 1, 0.25)  # boundary holds
    v40.require_phase_b_trigger(0, 0, 0.25)

    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.resolve_probe_setting(True, True)
    assert excinfo.value.check_id == "J12" and "ambiguous" in excinfo.value.message
    assert v40.resolve_probe_setting(False, False) is None

    # Rule 5 selected but Phase B did not run -> unreachable, J12.
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.determine_v40_terminal(integrity_ok=True, w_a=0, r_a=0, imp_a=0.9, phase_b_ran=False)
    assert excinfo.value.check_id == "J12"

    # Probe eligible (CAP_MATERIAL) but probe did not run -> unreachable, J12.
    with pytest.raises(v40.IntegrityFailure) as excinfo:
        v40.determine_v40_terminal(integrity_ok=True, w_a=0, r_a=4, imp_a=0.0, probe_ran=False)
    assert excinfo.value.check_id == "J12"
