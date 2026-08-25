"""Focused V39P0 tests (T1-T19) for the Lane C robustness / Lane B control runner.

All tests are fake-runner or decoder-free. No production decoder is invoked,
no official V39 output root is created, and no NPZ is read or written.
The single slower test (real structural reconstruction of two matrices,
including one non-winner seed and one Lane C permutation comparison) is
marked ``v39_real_preflight``.
"""

from __future__ import annotations

import itertools
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from comparison_bench.formal_ir.v35_algorithm_development import (  # noqa: E402
    DecoderResult,
    GF2mField,
    load_v25_channel_counts,
)
from comparison_bench.formal_ir import v38_architecture_triage as v38_module  # noqa: E402
from comparison_bench.formal_ir import (  # noqa: E402
    v39_lanec_robustness_laneb_control as v39,
)

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "execute_v39_development.py"


# ---------------------------------------------------------------------------
# Fixtures and synthetic record helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_counts():
    return load_v25_channel_counts()


def make_record(
    lane: str,
    source: str,
    ordinal: int,
    construction_seed: int,
    block_seed: int,
    *,
    exact: bool,
    errors_final: int | None = None,
    errors_initial: int = 250,
    syndrome_ok: bool | None = None,
    iterations: int = 10,
    status: str = "converged_exact",
    runtime_s: float = 0.5,
) -> dict:
    if syndrome_ok is None:
        syndrome_ok = exact
    return {
        "lane": lane,
        "source": source,
        "construction_seed": construction_seed if lane != v39.BASELINE_LANE else None,
        "construction_seed_ordinal": ordinal if lane != v39.BASELINE_LANE else None,
        "block_seed": block_seed,
        "matrix_id": (
            f"{lane}_{source}_s{construction_seed}"
            if lane != v39.BASELINE_LANE
            else f"v31_baseline_{source}"
        ),
        "errors_initial": errors_initial,
        "errors_final": int(errors_final if errors_final is not None else (0 if exact else 7)),
        "exact_l2": bool(exact),
        "syndrome_ok": bool(syndrome_ok),
        "wrong_codeword": bool(syndrome_ok and not exact),
        "iterations": iterations,
        "status": status,
        "runtime_s": runtime_s,
    }


def synth_lane_records(lane: str, exact_pattern):
    """Build 45 records; exact_pattern(source, ordinal, block_index)->bool."""
    records = []
    for source in v39.SOURCE_ORDER:
        for ordinal, seed in enumerate(v39.CONSTRUCTION_SEEDS[lane][source], start=1):
            for idx, block_seed in enumerate(v39.BLOCK_SEEDS[source]):
                ex = exact_pattern(source, ordinal, idx)
                records.append(
                    make_record(
                        lane, source, ordinal, seed, block_seed, exact=ex,
                        errors_final=0 if ex else 7,
                        syndrome_ok=ex,  # keep wrong_codeword false in synths
                    )
                )
    return records


def c_boundary_pattern(source, ordinal, idx):
    """Exactly 4/5 per cell -> 36/45 overall, 12/15 per source and ordinal."""
    return idx < 4


def b_weaker_pattern(source, ordinal, idx):
    """3/5 per cell: subset of C's exacts -> d_CB=+1 per cell, d_BC=0."""
    return idx < 3


def synth_baseline(exact=False, final=171):
    return [
        make_record(
            v39.BASELINE_LANE, s, 0, 0, bs, exact=exact,
            errors_final=final, syndrome_ok=False,
        )
        for s in v39.SOURCE_ORDER
        for bs in v39.BLOCK_SEEDS[s]
    ]


# ---------------------------------------------------------------------------
# T1/T2: deterministic reconstruction + strict metric match
# ---------------------------------------------------------------------------


@pytest.mark.v39_real_preflight
def test_t1_t2_real_reconstruction_matches_committed_metrics():
    field = GF2mField.create(32)
    only = frozenset({("lane_b", "1M", 382101), ("lane_c", "1M", 383101)})
    first = v39.reconstruct_v39_matrices(field=field, only=only)
    second = v39.reconstruct_v39_matrices(field=field, only=only)
    assert set(first.keys()) == only == set(second.keys())
    for key in only:
        m1, _ = first[key]
        m2, _ = second[key]
        assert np.array_equal(m1, m2), f"constructor nondeterminism at {key}"
    (lane_b_m, _) = first[("lane_b", "1M", 382101)]
    (lane_c_m, lane_c_metrics) = first[("lane_c", "1M", 383101)]
    assert lane_b_m.shape == (184, 1024)
    assert lane_c_m.shape == (184, 1024)
    assert "position_permutations" in lane_c_metrics


def test_t2_metric_mismatch_is_integrity_failure(tmp_path, monkeypatch):
    real_authority = json.loads(Path(v39.STRUCTURAL_AUTHORITY_PATH).read_text(encoding="utf-8"))
    target = next(r for r in real_authority if r["matrix_id"] == "lane_b_1M_s382101")
    target["rank_GF32"] = int(target["rank_GF32"]) - 1
    bad_path = tmp_path / "bad_authority.json"
    bad_path.write_text(json.dumps(real_authority), encoding="utf-8")
    with pytest.raises(v39.IntegrityFailure) as excinfo:
        v39.reconstruct_v39_matrices(
            reference_metrics_path=bad_path,
            only=frozenset({("lane_b", "1M", 382101)}),
        )
    assert excinfo.value.check_id == "I1"


# ---------------------------------------------------------------------------
# T3: block registry validation
# ---------------------------------------------------------------------------


def test_t3_block_registry_accepts_frozen_and_rejects_drift():
    ok, msg = v39.validate_block_registry()
    assert ok, msg
    drifted = {s: list(bs) for s, bs in v39.BLOCK_SEEDS.items()}
    drifted["1M"][0] = 360101  # V36/V38-used seed must be rejected
    ok, msg = v39.validate_block_registry(drifted)
    assert not ok and "overlap" in msg
    dup = {s: list(bs) for s, bs in v39.BLOCK_SEEDS.items()}
    dup["2M"][1] = dup["2M"][0]
    ok, msg = v39.validate_block_registry(dup)
    assert not ok and "unique" in msg


# ---------------------------------------------------------------------------
# T4/T5: posterior-binding sentinels on the frozen probes (real counts)
# ---------------------------------------------------------------------------


def test_t4_t5_posterior_binding_sentinels_on_frozen_probes(real_counts):
    results = v39.posterior_binding_preflight(real_counts)
    assert set(results.keys()) == set(v39.SOURCE_ORDER)
    for source, checks in results.items():
        assert checks["probe_block_seed"] == v39.PROBE_BLOCK_SEEDS[source]
        assert checks["bob_gt_31"] is True
        assert checks["captured_equals_bob"] is True
        assert checks["corrected_equals_direct"] is True
        assert checks["corrected_differs_u2bob_arraywise"] is True
        assert checks["corrected_differs_u2bob_maxabs"] is True
        assert checks["argmax_divergence"] is True


# ---------------------------------------------------------------------------
# T6/T17: baseline dedup, pairing completeness, errors_initial equality
# ---------------------------------------------------------------------------


def _valid_full_record_sets():
    lane_records = synth_lane_records("lane_c", c_boundary_pattern) + synth_lane_records(
        "lane_b", b_weaker_pattern
    )
    baseline = synth_baseline()
    return lane_records, baseline


def test_t6_t17_valid_sets_pass_and_tampering_fails():
    lane_records, baseline = _valid_full_record_sets()
    assert v39.validate_post_evaluation(lane_records, baseline) == []

    duplicated = list(baseline) + [dict(baseline[0])]
    assert any(
        cid == "I5" for cid, _ in v39.validate_post_evaluation(lane_records, duplicated)
    )

    missing_one = [
        r for r in lane_records if not (r["lane"] == "lane_c" and r["block_seed"] == 390105)
    ]
    assert any(
        cid == "I6" for cid, _ in v39.validate_post_evaluation(missing_one, baseline)
    )

    flipped = json.loads(json.dumps(lane_records))
    target = next(
        r for r in flipped if r["lane"] == "lane_c" and r["block_seed"] == 390105
    )
    target["errors_initial"] += 1
    assert any(
        cid == "I8" for cid, _ in v39.validate_post_evaluation(flipped, baseline)
    )


# ---------------------------------------------------------------------------
# T7: call accounting via fake-runner end-to-end run
# ---------------------------------------------------------------------------


class _FakeWorld:
    def __init__(self):
        self.metrics_by_id: dict[str, dict] = {}
        self.constructors = {
            "lane_b": self._make_ctor("lane_b"),
            "lane_c": self._make_ctor("lane_c"),
        }

    def _make_ctor(self, lane):
        def _ctor(source: str, seed: int, field=None):
            H = np.zeros((4, 1024), dtype=np.uint8)
            H[0, :: 64] = 1
            H[1, :: 65] = 1
            H[2, :: 67] = 1
            H[3, :: 71] = 1
            matrix_id = f"{lane}_{source}_s{seed}"
            metrics = {
                "lane": lane,
                "source": source,
                "construction_seed": str(seed),
                "matrix_id": matrix_id,
                "shape": "[4, 1024]",
                "rank_GF32": 4,
                "support_edge_count": int((H != 0).sum()),
                "col_degree_min": 0,
                "col_degree_mean": 4 * 4 / 1024,
                "col_degree_max": 1,
                "row_degree_min": 14,
                "row_degree_mean": 16.0,
                "row_degree_max": 18,
                "degenerate_cycles_4": 0,
                "degenerate_cycles_6": 0,
                "degenerate_cycles_8": 0,
                "support_cycles_4": 0,
                "structurally_valid": True,
            }
            self.metrics_by_id[matrix_id] = metrics
            return H, metrics

        return _ctor

    def authority_file(self, tmp_path: Path) -> Path:
        # Materialize all 18 lane_b/lane_c fake matrices first so the
        # committed-authority stub carries exactly 27 records.
        for lane in ("lane_b", "lane_c"):
            for source in v39.SOURCE_ORDER:
                for seed in v39.CONSTRUCTION_SEEDS[lane][source]:
                    self.constructors[lane](source=source, seed=seed)
        records = []
        for lane in ("lane_a",):
            for source in v39.SOURCE_ORDER:
                for seed in (911001, 911002, 911003):
                    records.append(
                        {"lane": lane, "source": source, "construction_seed": str(seed),
                         "matrix_id": f"{lane}_{source}_s{seed}", "shape": "[4, 1024]"}
                    )
        for matrix_id, metrics in self.metrics_by_id.items():
            rec = dict(metrics)
            rec["construction_seed"] = str(rec["construction_seed"])
            records.append(rec)
        assert len(records) == 27
        path = tmp_path / "fake_authority.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        return path


@pytest.fixture()
def fake_v31():
    return {
        "1M": np.zeros((184, 1024), dtype=np.uint8),
        "1p5M": np.zeros((190, 1024), dtype=np.uint8),
        "2M": np.zeros((192, 1024), dtype=np.uint8),
    }


def test_t7_fake_runner_end_to_end_105_calls_and_outputs(
    tmp_path, monkeypatch, real_counts, fake_v31
):
    world = _FakeWorld()
    calls = {"n": 0}
    real_eval = v39.evaluate_single_block

    def counting_eval(*args, **kwargs):
        calls["n"] += 1
        return real_eval(*args, **kwargs)

    monkeypatch.setattr(v39, "evaluate_single_block", counting_eval)

    root = tmp_path / "v39_run"
    result = v39.run_v39_development(
        development_execution_authorized=True,
        authorized_target_sha="f" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        v31_matrices=fake_v31,
        check_git=False,
        constructors=world.constructors,
    )

    assert calls["n"] == v39.TOTAL_CALLS == 105
    assert result["terminal_state"] in v39.ALL_TERMINALS
    files = {p.name for p in root.iterdir()}
    expected_files = {
        "v39_structural_reconstruction.json", "v39_structural_reconstruction.csv",
        "v39_block_records.json", "v39_block_records.csv",
        "v39_baseline_records.json", "v39_baseline_records.csv",
        "v39_paired_comparison.json", "v39_paired_comparison.csv",
        "v39_summary.json",
    }
    assert expected_files <= files
    assert not any(name.endswith(".npz") for name in files)

    summary = json.loads((root / "v39_summary.json").read_text(encoding="utf-8"))
    assert summary["lifecycle_state"] == "DEVELOPMENT_RESULT_CANDIDATE"
    assert summary["accounting"]["decoder_calls_total"] == 105
    assert summary["aggregates"]["lane_c"]["overall"]["records_count"] == 45
    assert summary["aggregates"]["lane_b"]["overall"]["records_count"] == 45
    assert summary["aggregates"][v39.BASELINE_LANE]["overall"]["records_count"] == 15
    assert summary["paired_discordance"]["pairs_count"] == 45
    assert len(summary["aggregates"]["lane_c"]["block_clusters"]) == 15
    assert set(summary["gates"].keys()) == {"C1", "B1", "CB", "BASE_C", "BASE_B"}

    block_rows = json.loads((root / "v39_block_records.json").read_text(encoding="utf-8"))
    with (root / "v39_block_records.csv").open(encoding="utf-8") as fh:
        csv_lines = [line for line in fh.read().splitlines() if line]
    assert len(csv_lines) - 1 == len(block_rows) == 90
    base_rows = json.loads((root / "v39_baseline_records.json").read_text(encoding="utf-8"))
    with (root / "v39_baseline_records.csv").open(encoding="utf-8") as fh:
        base_csv = [line for line in fh.read().splitlines() if line]
    assert len(base_csv) - 1 == len(base_rows) == 15


# ---------------------------------------------------------------------------
# Guards: authorization, overwrite, SHA binding, NPZ policy
# ---------------------------------------------------------------------------


def test_runner_unauthorized_raises_permission_error():
    with pytest.raises(PermissionError):
        v39.run_v39_development(development_execution_authorized=False)


def test_runner_refuses_existing_output_root(tmp_path, real_counts, fake_v31, monkeypatch):
    world = _FakeWorld()
    root = tmp_path / "existing"
    root.mkdir()
    with pytest.raises(FileExistsError):
        v39.run_v39_development(
            development_execution_authorized=True,
            authorized_target_sha="a" * 40,
            fake_runner=True,
            output_root=root,
            structural_authority_path=world.authority_file(tmp_path),
            counts_by_source=real_counts,
            v31_matrices=fake_v31,
            check_git=False,
            constructors=world.constructors,
        )


def test_sha_binding_exact_equality():
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    binding = v39.verify_execution_sha_binding(Path.cwd(), head)
    assert binding["HEAD"] == head
    with pytest.raises(v39.IntegrityFailure) as excinfo:
        v39.verify_execution_sha_binding(Path.cwd(), "0" * 40)
    assert excinfo.value.check_id == "SHA_BINDING_MISMATCH"


def test_npz_policy_rejects_winner_archive_as_authority(tmp_path):
    fake_npz = tmp_path / v39.FORBIDDEN_WINNER_NPZ_NAME
    fake_npz.write_bytes(b"PK\x03\x04")
    with pytest.raises(v39.IntegrityFailure) as excinfo:
        v39.reconstruct_v39_matrices(reference_metrics_path=fake_npz)
    assert excinfo.value.check_id == "I10"


def test_v25_counts_input_remains_allowed(real_counts):
    provenance = v39.describe_v25_counts_provenance()
    assert provenance["exists"] is True
    assert provenance["role"].startswith("source-specific V25 TRAIN")


# ---------------------------------------------------------------------------
# T8: record schema incl. wrong_codeword derivation
# ---------------------------------------------------------------------------


def test_t8_schema_validation():
    good = make_record("lane_c", "1M", 1, 383101, 390101, exact=True)
    ok, msg = v39.validate_record_schema(good)
    assert ok, msg

    wrong_derived = make_record(
        "lane_c", "1M", 1, 383101, 390101, exact=False, syndrome_ok=True
    )
    assert wrong_derived["wrong_codeword"] is True
    wrong_derived["wrong_codeword"] = False
    ok, msg = v39.validate_record_schema(wrong_derived)
    assert not ok and "wrong_codeword" in msg

    missing = make_record("lane_b", "2M", 3, 382303, 390305, exact=True)
    del missing["iterations"]
    ok, _ = v39.validate_record_schema(missing)
    assert not ok

    baseline_bad = make_record(v39.BASELINE_LANE, "1M", 0, 0, 390101, exact=True)
    baseline_bad["construction_seed"] = 123
    ok, _ = v39.validate_record_schema(baseline_bad)
    assert not ok


# ---------------------------------------------------------------------------
# T9-T11: gates C1/B1/CB/BASE boundary behavior
# ---------------------------------------------------------------------------


def test_t9_gate_c1_boundary_pass_and_single_cell_fail():
    lane_records, baseline = _valid_full_record_sets()
    gate = v39.evaluate_gate_robustness("lane_c", lane_records)
    assert gate["passed"] is True
    details = gate["details"]
    assert details["overall_min_36_of_45"]["exact_count"] == 36
    assert all(v["exact_count"] == 12 for v in details["each_source_min_12_of_15"].values())
    assert all(v["passed"] for v in details["each_cell_min_4_of_5"].values())

    weakened = json.loads(json.dumps(lane_records))
    cell_key = ("lane_c", "1p5M")
    victim = next(
        r for r in weakened
        if r["lane"] == "lane_c" and r["construction_seed_ordinal"] == 2
        and r["source"] == "1p5M" and r["block_seed"] == 390203
    )
    victim["exact_l2"] = False
    victim["errors_final"] = 11
    gate2 = v39.evaluate_gate_robustness("lane_c", weakened)
    assert gate2["passed"] is False
    cells = gate2["details"]["each_cell_min_4_of_5"]
    failed_cells = [k for k, v in cells.items() if not v["passed"]]
    assert failed_cells == ["1p5M_s383202"]


def test_t10_gate_cb_boundaries():
    lane_records, baseline = _valid_full_record_sets()
    paired = v39.build_paired_rows(lane_records, baseline)
    gate = v39.evaluate_gate_cb(lane_records, paired)
    disc = v39.paired_discordance_summary(paired)
    assert disc["d_CB"] == 9 and disc["d_BC"] == 0
    assert gate["passed"] is True
    details = gate["details"]
    assert details["cb_a_exact_margin"]["exact_count_C"] == 36
    assert details["cb_a_exact_margin"]["exact_count_B"] == 27

    # Boundary sweep: promote B-only-exact pairs (idx==4 blocks where C is not exact).
    # k=4 flips -> exact_B=31 (CB-a margin exactly +5, passes), d_BC=4, margin=5.
    boosted = json.loads(json.dumps(lane_records))
    b_idx4 = [
        r for r in boosted
        if r["lane"] == "lane_b" and not r["exact_l2"]
        and r["block_seed"] == v39.BLOCK_SEEDS[r["source"]][4]
    ]
    for r in b_idx4[:4]:
        r["exact_l2"] = True
        r["errors_final"] = 0
    paired_k4 = v39.build_paired_rows(boosted, baseline)
    gate_k4 = v39.evaluate_gate_cb(boosted, paired_k4)
    disc_k4 = v39.paired_discordance_summary(paired_k4)
    assert gate_k4["details"]["cb_a_exact_margin"]["passed"] is True  # 36 >= 31+5 boundary
    assert gate_k4["details"]["cb_a_exact_margin"]["exact_count_B"] == 31
    assert disc_k4["discordance_margin_d_CB_minus_d_BC"] == 5
    assert gate_k4["passed"] is True

    # k=5 flips -> exact_B=32: CB-a fails while CB-b still holds.
    for r in b_idx4[4:5]:
        r["exact_l2"] = True
        r["errors_final"] = 0
    paired_k5 = v39.build_paired_rows(boosted, baseline)
    gate_k5 = v39.evaluate_gate_cb(boosted, paired_k5)
    assert gate_k5["details"]["cb_a_exact_margin"]["passed"] is False  # 36 >= 37 false
    assert gate_k5["details"]["cb_b_discordance_margin"]["passed"] is True
    assert gate_k5["details"]["cb_b_discordance_margin"]["margin"] == 4
    assert gate_k5["passed"] is False


def test_t11_gate_base_per_ordinal_against_single_baseline():
    lane_records, baseline = _valid_full_record_sets()
    base_c = v39.evaluate_gate_base("lane_c", lane_records, baseline)
    base_b = v39.evaluate_gate_base("lane_b", lane_records, baseline)
    assert base_c["passed"] is True
    assert base_b["passed"] is True
    assert base_b["report_only"] is True and base_c["report_only"] is False
    for o in ("1", "2", "3"):
        assert base_c["ordinals"][o]["exact_count_v31_baseline"] == 0
        assert base_c["ordinals"][o]["median_errors_final_v31_overall"] == 171.0

    strong_baseline = synth_baseline(exact=True, final=0)
    base_fail = v39.evaluate_gate_base("lane_c", lane_records, strong_baseline)
    assert base_fail["passed"] is False  # exact condition 36 > 45 fails


# ---------------------------------------------------------------------------
# T12: exhaustive terminal truth table
# ---------------------------------------------------------------------------


def test_t12_terminal_truth_table_total_and_disjoint():
    combos = list(itertools.product([False, True], repeat=4))
    seen: dict[str, int] = {}
    reasons = {}
    for c1, cb, base_c, b1 in combos:
        state, reason = v39.determine_v39_terminal_state(True, c1, cb, base_c, b1)
        assert state in v39.ALL_TERMINALS
        seen[state] = seen.get(state, 0) + 1
        if state == v39.TERMINAL_C_ROBUST_NO_COMPLETE_ADVANTAGE:
            reasons[(c1, cb, base_c, b1)] = reason
    assert seen[v39.TERMINAL_C_ROBUST_AND_ADVANTAGE] == 2  # rule 1 ignores B1
    assert seen[v39.TERMINAL_BOTH_ROUTES_ROBUST] == 3
    assert seen[v39.TERMINAL_B_ONLY_ROBUST] == 4
    assert seen[v39.TERMINAL_NO_ROBUST_ROUTE_SIGNAL] == 4
    assert seen[v39.TERMINAL_C_ROBUST_NO_COMPLETE_ADVANTAGE] == 3
    assert sum(seen.values()) == 16

    assert reasons[(True, False, True, False)] == "CB_FAIL"
    assert reasons[(True, True, False, False)] == "BASE_C_FAIL"
    assert reasons[(True, False, False, False)] == "CB_AND_BASE_C_FAIL"

    # Integrity-first precedence overrides every combination.
    for c1, cb, base_c, b1 in combos:
        state, reason = v39.determine_v39_terminal_state(False, c1, cb, base_c, b1)
        assert state == v39.TERMINAL_EVIDENCE_INVALID and reason is None


# ---------------------------------------------------------------------------
# T13: Wilson / McNemar fixtures
# ---------------------------------------------------------------------------


def test_t13_wilson_and_mcnemar_fixtures():
    lo, hi = v39.wilson_interval_95(0, 5)
    assert lo == 0.0
    assert abs(hi - 0.4345) < 1e-3
    lo, hi = v39.wilson_interval_95(5, 5)
    assert abs(lo - 0.5655) < 1e-3 and hi == 1.0
    mid = v39.wilson_interval_95(9, 45)
    assert mid[0] < 0.2 < mid[1]

    assert v39.mcnemar_exact_two_sided(1, 5) == pytest.approx(0.21875)
    assert v39.mcnemar_exact_two_sided(0, 0) == 1.0
    assert v39.mcnemar_exact_two_sided(3, 0) == pytest.approx(0.25)
    n = 6
    manual = min(1.0, 2 * sum(math.comb(n, i) for i in range(3)) / 2**n)
    assert v39.mcnemar_exact_two_sided(2, 4) == pytest.approx(manual)


# ---------------------------------------------------------------------------
# T14: writer contract
# ---------------------------------------------------------------------------


def test_t14_writer_contract_and_overwrite_guard(tmp_path):
    structural = [{
        "lane": "lane_c", "source": "1M", "construction_seed": 383101,
        "construction_seed_ordinal": 1, "matrix_id": "lane_c_1M_s383101",
        "strict_match_committed_metrics": True,
    }]
    lane_records, baseline = _valid_full_record_sets()
    paired = v39.build_paired_rows(lane_records, baseline)
    summary = v39.build_v39_summary(
        lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE", fake_runner=True,
        authorized_target_sha=None, sha_binding=None,
        counts_provenance={}, v31_identity={}, structural_rows=structural,
        aggregates=None, gates=None, discordance=None, integrity_failures=None,
        terminal_state=v39.TERMINAL_BOTH_ROUTES_ROBUST, terminal_reason=None,
    )
    root = tmp_path / "out"
    written = v39.write_v39_outputs(root, structural, lane_records, baseline, paired, summary)
    names = {p.name for p in root.iterdir()}
    assert names == {
        "v39_structural_reconstruction.json", "v39_structural_reconstruction.csv",
        "v39_block_records.json", "v39_block_records.csv",
        "v39_baseline_records.json", "v39_baseline_records.csv",
        "v39_paired_comparison.json", "v39_paired_comparison.csv",
        "v39_summary.json",
    }
    rows_json = json.loads((root / "v39_block_records.json").read_text(encoding="utf-8"))
    with (root / "v39_block_records.csv").open(encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    assert len(lines) - 1 == len(rows_json)
    assert not list(root.glob("*.npz"))
    with pytest.raises(FileExistsError):
        v39.write_v39_outputs(written, structural, lane_records, baseline, paired, summary)

    notice = v39.write_invalid_notice(root, [("I6", "test failure")], True)
    payload = json.loads(notice.read_text(encoding="utf-8"))
    assert payload["terminal_state"] == v39.TERMINAL_EVIDENCE_INVALID
    assert payload["performance_interpretation"] == "none"


def test_partial_failure_retains_raw_records_without_aggregates(tmp_path):
    structural = [{"matrix_id": "x", "strict_match_committed_metrics": True}]
    partial_lane = [make_record("lane_c", "1M", 1, 383101, 390101, exact=True)]
    root = tmp_path / "partial"
    root.mkdir()
    v39._persist_invalid_evidence(
        root,
        structural_rows=structural,
        lane_records=partial_lane,
        baseline_records=[],
        summary_ctx={"fake_runner": True},
        failures=[("mid_run_failure", "raw partial records retained")],
    )
    names = {p.name for p in root.iterdir()}
    assert "v39_block_records.json" in names
    assert "v39_invalid_notice.json" in names
    assert "v39_summary.json" in names
    assert "v39_paired_comparison.json" not in names
    summary = json.loads((root / "v39_summary.json").read_text(encoding="utf-8"))
    assert summary["terminal_state"] == v39.TERMINAL_EVIDENCE_INVALID
    assert summary["aggregates"] is None and summary["gates"] is None


def test_runner_mid_run_exception_retains_partials(
    tmp_path, monkeypatch, real_counts, fake_v31
):
    world = _FakeWorld()

    def exploding_eval(*args, **kwargs):
        raise RuntimeError("simulated decoder crash")

    monkeypatch.setattr(v39, "evaluate_single_block", exploding_eval)
    root = tmp_path / "crash_run"
    with pytest.raises(RuntimeError):
        v39.run_v39_development(
            development_execution_authorized=True,
            authorized_target_sha="b" * 40,
            fake_runner=True,
            output_root=root,
            structural_authority_path=world.authority_file(tmp_path),
            counts_by_source=real_counts,
            v31_matrices=fake_v31,
            check_git=False,
            constructors=world.constructors,
        )
    notice = json.loads((root / "v39_invalid_notice.json").read_text(encoding="utf-8"))
    assert notice["terminal_state"] == v39.TERMINAL_EVIDENCE_INVALID
    assert "v39_paired_comparison.json" not in {p.name for p in root.iterdir()}


def test_runner_integrity_failure_path_writes_invalid_artifacts(
    tmp_path, monkeypatch, real_counts, fake_v31
):
    world = _FakeWorld()
    calls = {"n": 0}
    real_eval = v39.evaluate_single_block

    def counting_eval(*args, **kwargs):
        calls["n"] += 1
        return real_eval(*args, **kwargs)

    monkeypatch.setattr(v39, "evaluate_single_block", counting_eval)
    monkeypatch.setattr(
        v39,
        "validate_post_evaluation",
        lambda lane, base: [("I6", "injected accounting failure")],
    )
    root = tmp_path / "invalid_run"
    result = v39.run_v39_development(
        development_execution_authorized=True,
        authorized_target_sha="c" * 40,
        fake_runner=True,
        output_root=root,
        structural_authority_path=world.authority_file(tmp_path),
        counts_by_source=real_counts,
        v31_matrices=fake_v31,
        check_git=False,
        constructors=world.constructors,
    )
    assert result["terminal_state"] == v39.TERMINAL_EVIDENCE_INVALID
    summary = json.loads((root / "v39_summary.json").read_text(encoding="utf-8"))
    assert summary["integrity_failures"][0]["check"] == "I6"
    assert summary["performance_interpretation_presented"] is False


# ---------------------------------------------------------------------------
# T15: CLI guards
# ---------------------------------------------------------------------------


def test_t15_cli_requires_flag_and_has_no_fake_runner_option():
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--fake-runner" not in script

    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True
    )
    assert proc.returncode != 0
    assert "EXECUTE_NOT_AUTHORIZED" in (proc.stdout + proc.stderr)

    proc2 = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--development-execution-authorized"],
        capture_output=True, text=True,
    )
    assert proc2.returncode != 0
    assert "--authorized-target-sha" in (proc2.stdout + proc2.stderr)


# ---------------------------------------------------------------------------
# T18: frozen decoder parameters and polynomial
# ---------------------------------------------------------------------------


def test_t18_frozen_decoder_parameters_are_binding(real_counts, monkeypatch):
    assert v39.POLYNOMIAL == 37
    assert v39.MAX_ITER == 30
    assert v39.DAMPING_ALPHA == 1.0
    field = GF2mField.create(32)
    assert field.primitive_polynomial == 37

    captured = {}

    def fake_decode(H, prior, syn_true, **kwargs):
        captured.update(kwargs)
        captured["positional_H_shape"] = np.shape(H)
        return DecoderResult(
            x_hat=np.zeros(1024, dtype=np.int64),
            syndrome_ok=True,
            iterations=3,
            runtime_s=0.001,
            status="converged_exact",
            final_beliefs=np.zeros((1024, 32), dtype=float),
        )

    monkeypatch.setattr(v38_module, "decode_row_layered_fftqspa", fake_decode)
    counts = real_counts["1M"]
    record = v38_module.evaluate_single_block(
        H=np.zeros((184, 1024), dtype=np.uint8),
        source="1M",
        block_seed=390101,
        lane="lane_c",
        construction_seed=383101,
        counts=counts,
        max_iter=v39.MAX_ITER,
        damping_alpha=v39.DAMPING_ALPHA,
        fake_runner=False,
        field=field,
    )
    assert captured["max_iter"] == 30
    assert captured["damping_alpha"] == 1.0
    assert "field" in captured
    assert captured["positional_H_shape"] == (184, 1024)
    assert isinstance(record["exact_l2"], bool)


# ---------------------------------------------------------------------------
# T19: block-cluster aggregates
# ---------------------------------------------------------------------------


def test_t19_block_cluster_aggregates():
    lane_records = synth_lane_records("lane_c", c_boundary_pattern)
    clusters = v39.aggregate_lane_records(lane_records, [])["lane_c"]["block_clusters"]
    assert len(clusters) == 15
    # Block 390101 (idx 0) is exact under the idx<4 pattern for all three
    # construction seeds of the cell -> cluster count 3/3.
    cluster = clusters["1M_390101"]
    assert cluster["matrices_count"] == 3
    assert cluster["seed_exact_count"] == 3
    assert cluster["seed_exact_fraction"] == pytest.approx(1.0)
    residuals = [
        r["errors_final"]
        for r in lane_records
        if r["source"] == "1M" and r["block_seed"] == 390101
    ]
    assert residuals == [0, 0, 0]
    assert cluster["residual_median_across_3_matrices"] == 0.0
    # Block 390105 (idx 4) is non-exact in all three matrices -> 0/3, residual 7.
    cluster_last = clusters["1M_390105"]
    assert cluster_last["seed_exact_count"] == 0
    assert cluster_last["residual_mean_across_3_matrices"] == pytest.approx(7.0)
