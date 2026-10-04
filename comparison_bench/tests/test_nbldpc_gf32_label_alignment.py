from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.cli import nbldpc_gf32_label_probe as probe
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as mechanism
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common


def test_frozen_pmf_grid_and_t0_arithmetic():
    assert mechanism.verify_t0() == {
        "field_multiplication": True,
        "field_inverses": True,
        "pmf_normalization": True,
        "two_edge_exact": True,
        "qsc_single_check_invariance": True,
        "column_gauge_rank_support": True,
    }
    grid = mechanism.pmf_grid()
    assert [row["index"] for row in grid] == [0, 1, 2]
    assert [row["p0"] for row in grid] == [0.20, 0.25, 0.30]
    for row in grid:
        p = row["pmf"]
        assert np.isclose(p.sum(), 1.0, atol=1e-15)
        assert p[1] == 0.10
        assert np.all(p[2:] == (0.90 - row["p0"]) / 30.0)
        assert row["entropy_bits"] == mechanism.entropy_bits(p)


def test_two_edge_example_and_qsc_check_law_are_exact():
    p = np.zeros(32)
    p[0], p[1] = 0.8, 0.2
    same = mechanism.check_sum_pmf(p, (1, 1))
    different = mechanism.check_sum_pmf(p, (1, 2))
    assert same[0] == pytest.approx(0.68)
    assert same[1] == pytest.approx(0.32)
    assert different[[0, 1, 2, 3]] == pytest.approx(
        np.asarray([0.64, 0.16, 0.16, 0.04]))
    assert np.count_nonzero(different[4:]) == 0

    qsc = np.full(32, 0.1 / 31)
    qsc[0] = 0.9
    a = mechanism.check_sum_pmf(qsc, (1, 2, 3, 31))
    b = mechanism.check_sum_pmf(qsc, (4, 8, 9, 17))
    assert a == pytest.approx(b, abs=1e-15)


def test_score_and_tolerance_ties_keep_current_then_smallest():
    assert mechanism.choose_label([(1, 2.0), (2, 2.0 + 5e-13),
                                   (3, 1.0)], current=1) == 1
    assert mechanism.choose_label([(4, 2.0), (2, 2.0 + 5e-13),
                                   (3, 2.0)], current=5) == 2
    with pytest.raises(ValueError):
        mechanism.choose_label([], current=1)


def test_one_pass_alignment_keeps_support_rank_and_column_gauge():
    h0 = np.asarray([[1, 1]], dtype=np.int64)
    pmf = np.zeros(32, dtype=np.float64)
    pmf[0], pmf[1] = 0.8, 0.2
    result = mechanism.align_labels(h0, pmf)
    assert result["nontrivial"]
    assert result["Jc"] > result["J0"] + mechanism.MIN_SCORE_GAIN
    assert result["candidate_admitted"]
    assert result["support_equal"] and result["gauge_equal"]
    assert result["baseline_rank"] == result["candidate_rank"] == 1
    assert np.array_equal(result["candidate"] != 0, h0 != 0)
    assert np.array_equal(
        mechanism.scale_columns(result["candidate"],
                                mechanism.column_inverse(result["labels"])),
        h0,
    )
    replay = mechanism.align_labels(h0, pmf)
    assert np.array_equal(replay["labels"], result["labels"])
    assert replay["Jc"] == result["Jc"]


def test_frozen_seed_domains_and_pairing_contract():
    pilots, holdouts = probe._seed_plan()
    pilot_seeds = [entry[3] for entry in pilots]
    holdout_seeds = [entry[3] for entry in holdouts]
    assert len(pilots) == 72
    assert len(holdouts) == 192
    assert len(set(pilot_seeds)) == len(pilot_seeds)
    assert len(set(holdout_seeds)) == len(holdout_seeds)
    assert set(pilot_seeds).isdisjoint(holdout_seeds)
    assert probe.pilot_seed(1, 2026093702, 3) == common.v10_seed(
        "gf32-label-v1:pilot:1:2026093702:3")
    assert probe.holdout_seed(2026093702, 1, 15) == common.v10_seed(
        "gf32-label-v1:holdout:2026093702:1:15")
    assert probe.arm_order(0) == ("control", "candidate")
    assert probe.arm_order(1) == ("candidate", "control")
    assert probe.sample_error(1234, mechanism.pmf_grid()[0]["pmf"]).tolist() == \
        probe.sample_error(1234, mechanism.pmf_grid()[0]["pmf"]).tolist()


def test_paired_arm_data_shares_truth_prior_and_uses_each_syndrome():
    h0 = np.asarray([[1, 1], [1, 0]], dtype=np.int64)
    hc = mechanism.scale_columns(h0, [2, 1])
    truth = np.asarray([1, 2], dtype=np.int64)
    prior = np.tile(np.full(32, 1 / 32), (2, 1))
    paired = probe.paired_arm_data(h0, hc, truth, prior)
    assert np.shares_memory(paired["control"]["truth"], truth)
    assert np.shares_memory(paired["candidate"]["truth"], truth)
    assert paired["control"]["prior"] is prior
    assert paired["candidate"]["prior"] is prior
    assert paired["control"]["dense"] is h0
    assert paired["candidate"]["dense"] is hc
    assert np.array_equal(paired["control"]["syndrome"],
                          layout.gf32_syndrome(h0, truth))
    assert np.array_equal(paired["candidate"]["syndrome"],
                          layout.gf32_syndrome(hc, truth))
    assert not np.array_equal(paired["control"]["syndrome"],
                              paired["candidate"]["syndrome"])


def test_syndrome_consistent_wrong_is_recorded_as_failure_not_stop():
    h = np.asarray([[1, 1]], dtype=np.int64)
    truth = np.asarray([1, 0], dtype=np.int64)
    syndrome = np.asarray(layout.gf32_syndrome(h, truth), dtype=np.int64)
    ticks = iter((10.0, 10.25))

    def fake_decoder(_h, _prior, _syndrome):
        return SimpleNamespace(x_hat=np.asarray([0, 1]), syndrome_ok=True,
                               iterations=3, status="converged_exact")

    observed, issue = probe.decode_observation(
        fake_decoder, h, np.ones((2, 32)) / 32, truth, syndrome,
        now=lambda: next(ticks), rss_fn=lambda: 1024)
    assert issue == ""
    assert observed == {
        "exact": False,
        "syndrome_accept": True,
        "syndrome_consistent_wrong": True,
        "status": "converged_exact",
        "iterations": 3,
        "wall_s": 0.25,
        "rss_b": 1024,
    }


def test_decoder_syndrome_flag_disagreement_is_integrity_stop():
    h = np.asarray([[1]], dtype=np.int64)
    truth = np.asarray([1], dtype=np.int64)
    syndrome = np.asarray([1], dtype=np.int64)
    ticks = iter((1.0, 1.1))

    def fake_decoder(_h, _prior, _syndrome):
        return SimpleNamespace(x_hat=np.asarray([1]), syndrome_ok=False,
                               iterations=1, status="max_iter")

    observed, issue = probe.decode_observation(
        fake_decoder, h, np.ones((1, 32)) / 32, truth, syndrome,
        now=lambda: next(ticks), rss_fn=lambda: 1024)
    assert issue == "decoder_syndrome_flag_mismatch"
    assert observed["status"] == "integrity_error"
    assert observed["exact"] and observed["syndrome_accept"]


def test_synchronous_decoder_overrun_is_classified_after_return():
    h = np.asarray([[1]], dtype=np.int64)
    truth = np.asarray([0], dtype=np.int64)
    syndrome = np.asarray([0], dtype=np.int64)
    ticks = iter((1.0, 1.0 + probe.CALL_CAP_S + 0.1))

    def fake_decoder(_h, _prior, _syndrome):
        return SimpleNamespace(x_hat=np.asarray([0]), syndrome_ok=True,
                               iterations=0, status="converged_exact")

    observed, issue = probe.decode_observation(
        fake_decoder, h, np.ones((1, 32)) / 32, truth, syndrome,
        now=lambda: next(ticks), rss_fn=lambda: 1024)
    assert issue == "decoder_call_wall_cap_after_return"
    assert observed["status"] == "resource_abort"
    assert observed["exact"] and observed["syndrome_accept"]


@pytest.mark.parametrize(
    ("elapsed", "rss", "calls", "expected"),
    [
        (probe.WALL_CAP_S, 0, 0, "total_wall_cap_before_next_call"),
        (0, probe.RSS_CAP_BYTES, 0, "rss_cap_before_next_call"),
        (0, 0, probe.MAX_CALLS, "decoder_call_count_cap_before_next_call"),
        (0, 0, 0, ""),
    ],
)
def test_budget_gate_stops_before_next_decoder_call(elapsed, rss, calls,
                                                     expected):
    stop = probe.check_before_call(
        0.0, now=lambda: elapsed, rss_fn=lambda: rss, calls=calls)
    assert stop == expected


def test_fixed_root_refusal_and_dry_run_make_no_writes(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    before = sorted(p.name for p in workspace.iterdir())
    result = probe.dry_run(probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    assert result["status"] == "DRY_RUN"
    assert result["writes"] == result["decoder_calls"] == 0
    assert sorted(p.name for p in workspace.iterdir()) == before
    assert not (workspace / "gf32_label_a74e912c").exists()

    fixed_root = workspace / "gf32_label_a74e912c"
    fixed_root.mkdir()
    with pytest.raises(FileExistsError):
        probe.validate_out_root(probe.OUT_ROOT_RELATIVE, repo_root=tmp_path)
    with pytest.raises(ValueError):
        probe.validate_out_root("workspace/another-root", repo_root=tmp_path)


def test_batch_wall_budget_stops_before_a_decoder_call_and_retains_root(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dense = np.zeros((probe.M, probe.N), dtype=np.int64)
    dense[np.arange(probe.M), np.arange(probe.M)] = 1
    for extra in range(probe.EDGE_COUNT - probe.M):
        row = extra % probe.M
        col = probe.M + extra % (probe.N - probe.M)
        dense[row, col] = 1 + extra % 31
    assert np.count_nonzero(dense) == probe.EDGE_COUNT

    def fake_graph_builder(_width, graph_seed):
        return {
            "status": "ok", "admitted": True, "n": probe.N,
            "m": probe.M, "E": probe.EDGE_COUNT, "dense": dense,
            "structure": {"gf32_rank": probe.M},
            "seed": graph_seed,
        }

    clock_calls = 0

    def fake_clock():
        nonlocal clock_calls
        clock_calls += 1
        return 0.0 if clock_calls == 1 else probe.WALL_CAP_S

    decoder_calls = 0

    def should_not_decode(_h, _prior, _syndrome):
        nonlocal decoder_calls
        decoder_calls += 1
        raise AssertionError("budget should stop before first decoder call")

    summary = probe.execute_batch(
        out_root=probe.OUT_ROOT_RELATIVE,
        decode_fn=should_not_decode,
        repo_root=tmp_path,
        now=fake_clock,
        rss_fn=lambda: 0,
        graph_builder=fake_graph_builder,
    )
    root = workspace / "gf32_label_a74e912c"
    assert summary["terminal_status"] == "RESOURCE_STOP"
    assert summary["stop_reason"] == "total_wall_cap_before_next_call"
    assert summary["attempted_decoder_calls"] == decoder_calls == 0
    assert summary["attempted_frame_rows"] == 0
    assert sorted(p.name for p in root.iterdir()) == [
        "EXPLORATION_LOG.md", "frame_records.csv", "manifest.json",
        "summary.json",
    ]
