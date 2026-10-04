"""Fake-only tests for the CQ Arm B channel survey (no .ttbin, no real data).

Every real-data contact is replaced by synthetic (a, b) arrays whose ser /
pm1 mass / Gray popcount / co-error / H values are hand-computable. The
production loader is never called.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import cq_channel_survey_armB as cq


def _fresh_root() -> str:
    return f"workspace/cq__pytest_{uuid.uuid4().hex[:8]}"


def _case_a(n: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """a all zero; b: 75% 0, 20% 1, 5% 2. ser=0.25, expected planes=1.2."""
    n0, n1 = int(n * 0.75), int(n * 0.20)
    n2 = n - n0 - n1
    a = np.zeros(n, dtype=np.int64)
    b = np.concatenate([np.zeros(n0, dtype=np.int64),
                        np.ones(n1, dtype=np.int64),
                        np.full(n2, 2, dtype=np.int64)])
    return a, b


def _fake_series_a(source: str) -> dict[str, Any]:
    n = cq.SOURCES[source]["eval_superframes"] * cq.N
    a, b = _case_a(n)
    return {"a": a, "b": b, "dataset": "<fake>", "ttbin": "<fake>",
            "offset_ps": 0, "n_pairs_total": n, "n_pairs_eval": n,
            "eval_first_frame": 0, "read_wall_s": 0.0}


def test_main_refuses_without_both_flags():
    with pytest.raises(cq.Refusal):
        cq.main(["--source", "1M", "--root", _fresh_root()])
    with pytest.raises(cq.Refusal):
        cq.main(["--source", "1M", "--root", _fresh_root(), "--execute-real"])


def test_root_rules():
    with pytest.raises(cq.Refusal):
        cq._check_root("workspace/x1_abc")
    with pytest.raises(cq.Refusal):
        cq._check_root("workspace/cq_x/results/y")
    with pytest.raises(cq.Refusal):
        cq._check_root("comparison_bench/outputs_comparison/cq_x")
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    try:
        with pytest.raises(cq.Refusal):
            cq._check_root(root)  # exists -> not fresh
    finally:
        shutil.rmtree(root, ignore_errors=True)
    cq._check_root(_fresh_root())  # fresh + right prefix passes


def test_runner_source_has_zero_forbidden_tokens():
    """Mirror of the packet machine gate: assembled tokens absent from source."""
    text = Path(cq.__file__).read_text(encoding="utf-8")
    for tok in cq._FORB:
        assert tok not in text, f"forbidden token in runner source: {tok}"


def test_sys_modules_gate_trips_on_planted_module():
    planted = cq._FORB[5]  # assembled at runtime; no literal in this file
    sys.modules[planted] = sys.modules[__name__]
    try:
        with pytest.raises(cq.Refusal):
            cq.assert_no_correction_machinery()
    finally:
        del sys.modules[planted]
    cq.assert_no_correction_machinery()  # clean again


def test_channel_record_hand_computed():
    a, b = _case_a(1000)
    rec = cq.channel_record(a, b)
    assert rec["ser"] == pytest.approx(0.25)
    assert rec["pm1_mass"]["+1"] == pytest.approx(0.20)
    assert rec["pm1_mass"]["-1"] == pytest.approx(0.0)
    assert rec["pm1_mass"]["0"] == pytest.approx(0.75)
    assert rec["modular_delta_frac_top"] == pytest.approx(
        {"0": 0.75, "+1": 0.20, "-1": 0.0, "other": 0.05})
    assert rec["direction_asymmetry_plus_minus1"] == pytest.approx(0.20)
    pop = rec["gray_mask_popcount_frac"]
    assert pop["0"] == pytest.approx(0.75)
    assert pop["1"] == pytest.approx(0.20)
    assert pop["2"] == pytest.approx(0.05)
    assert sum(pop[str(k)] for k in range(3, 11)) == pytest.approx(0.0)
    # gray(0)=0, gray(1)=1 (plane0), gray(2)=3 (planes 0+1)
    assert rec["plane_rates_lsb_first"][0] == pytest.approx(0.25)
    assert rec["plane_rates_lsb_first"][1] == pytest.approx(0.05)
    assert all(v == pytest.approx(0.0) for v in rec["plane_rates_lsb_first"][2:])
    co = np.asarray(rec["bit_plane_co_error_matrix"])
    assert co.shape == (10, 10)
    assert co[0, 0] == pytest.approx(0.25) and co[1, 1] == pytest.approx(0.05)
    assert co[0, 1] == pytest.approx(0.05)  # joint plane0+plane1 errors
    # expected planes per error = (200*1 + 50*2)/250 = 1.2, both routes
    assert rec["expected_planes_flipped_per_error_via_diag"] == pytest.approx(1.2)
    assert rec["expected_planes_flipped_per_error_via_popcount"] == pytest.approx(1.2)
    # all a=0 -> zero conditional entropy; support = 3 occupied cells
    assert rec["H_U1_given_B"] == pytest.approx(0.0)
    assert rec["H_U2_given_U1B"] == pytest.approx(0.0)
    assert rec["H_A_given_B"] == pytest.approx(0.0)
    assert rec["N_ab_support_cells"] == 3
    assert rec["N_ab_occupancy"] == pytest.approx(3 / (1024 * 1024))
    assert rec["abs_signed_delta_quantiles"]["q50"] == pytest.approx(0.0)
    assert rec["abs_signed_delta_quantiles"]["q90"] == pytest.approx(1.0)
    assert rec["abs_signed_delta_quantiles"]["q100"] == pytest.approx(2.0)
    assert len(rec["time_block_stability"]) == 6
    assert rec["time_block_stability"][0]["ser"] == pytest.approx(0.0)
    assert rec["time_block_stability"][-1]["ser"] == pytest.approx(1.0)


def test_h_full_f03_hand_computed_one_bit():
    """a in {0,1} uniform, b always 0 -> H(A|B)=1, all of it in U2."""
    a = np.array([0] * 500 + [1] * 500, dtype=np.int64)
    b = np.zeros(1000, dtype=np.int64)
    rec = cq.channel_record(a, b)
    assert rec["ser"] == pytest.approx(0.5)
    assert rec["H_U1_given_B"] == pytest.approx(0.0)
    assert rec["H_U2_given_U1B"] == pytest.approx(1.0)
    assert rec["H_A_given_B"] == pytest.approx(1.0)
    assert rec["expected_planes_flipped_per_error_via_diag"] == pytest.approx(1.0)


def test_execute_with_fake_series():
    root = _fresh_root()
    before = {m for m in sys.modules if "tagger" in m.lower()}
    try:
        s = cq.execute(source="1M", root=root, series_fn=_fake_series_a,
                       rss_fn=lambda: 0.1)
        assert s["status"] == "OK"
        assert s["gid"] == "CQ-J21a" and s["arm"] == "B"
        assert s["n_superframes"] == 205 and s["remainder_symbols"] == 0
        assert s["channel"]["ser"] == pytest.approx(0.25)
        assert s["channel"]["expected_planes_flipped_per_error_via_diag"] \
            == pytest.approx(1.2)
        assert s["provenance"]["ttbin"] == "<fake>"
        assert Path(root, "CQ-J21a.json").exists()
        after = {m for m in sys.modules if "tagger" in m.lower()}
        assert after == before  # zero TimeTagger contact
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_superframe_count_mismatch_refuses():
    def short(_source):
        a = np.zeros(3 * cq.N, dtype=np.int64)
        return {"a": a, "b": a.copy(), "ttbin": "<fake>"}

    with pytest.raises(cq.Refusal):
        cq.execute(source="1M", root=_fresh_root(), series_fn=short,
                   rss_fn=lambda: 0.1)


# ---------------------------------------------------------------------------
# Arm A additive tests (fake-only; zero .ttbin, zero TimeTagger, zero real data)
# ---------------------------------------------------------------------------

from comparison_bench.src.comparison_bench.cli.probes_closed import cq_channel_survey_armA as cqA


def _armA_ok_header() -> dict[str, Any]:
    """True header shape (read-only finding 2026-09-27 on the Type0 bases)."""
    return {"config": {"registered channels": [1, 5],
                       "measurements": [
                           {"name": "FileWriter",
                            "registered channels": [1, 5, 1001],
                            "virtual channels": [],
                            "params": {"channels": [1, 5, 1001]}},
                           {"name": "Coincidences",
                            "registered channels": [1, 5],
                            "virtual channels": [1001],
                            "params": {"groups": [[1, 5]], "type": 0,
                                       "window": 1000}}]},
            "source": "<fake>"}


def _armA_fake_events(n: int = 2048):
    """Synthetic event stream spanning exactly 3 s (tag gate passes).

    Cluster pairs sit on the 200 ps grid (ch5 +50 ps, same bin -> ser 0);
    two out-of-window anchors set tmin/tmax and correctly stay unpaired.
    """
    from types import SimpleNamespace
    grid0 = 1_000_000_000_000  # multiple of 200
    t_a = np.concatenate([[0], grid0 + np.arange(n, dtype=np.int64) * 200])
    t_b = np.concatenate([grid0 + np.arange(n, dtype=np.int64) * 200 + 50,
                          [3_000_000_000_000]])
    t = np.concatenate([t_a, t_b])
    ch = np.concatenate([np.ones(n + 1, dtype=np.int64),
                         np.full(n + 1, 5, dtype=np.int64)])
    return SimpleNamespace(time_ps=t, channel=ch,
                           event_type=np.zeros(2 * n + 2, dtype=np.int64),
                           missed_events=None)


def _armA_ok_align() -> dict[str, Any]:
    return {"align_status": "ok", "offset_ps_derived": 0,
            "peak_bin_index": 8192, "peak_to_bg": 500.0,
            "sigma_crude_ps": 60.0, "count_A": 2048, "count_B": 2048,
            "total_pairs_in_window": 2048}


def test_armA_main_refuses_without_both_flags():
    with pytest.raises(cqA.Refusal):
        cqA.main(["--group", "1M", "--root", _fresh_root()])
    with pytest.raises(cqA.Refusal):
        cqA.main(["--group", "1M", "--root", _fresh_root(), "--execute-real"])


def test_armA_root_rules():
    with pytest.raises(cqA.Refusal):
        cqA._check_root_for_group("workspace/x1_abc", "CQ-20a")
    with pytest.raises(cqA.Refusal):
        cqA._check_root_for_group("workspace/cq_x/results/y", "CQ-20a")
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    try:
        Path(root, "CQ-20a.json").write_text("{}", encoding="utf-8")
        with pytest.raises(cqA.Refusal):
            cqA._check_root_for_group(root, "CQ-20a")  # collision
        cqA._check_root_for_group(root, "CQ-20b")  # shared root, new gid: ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    cqA._check_root_for_group(_fresh_root(), "CQ-20a")  # missing root: ok


def test_armA_runner_source_has_zero_forbidden_tokens():
    text = Path(cqA.__file__).read_text(encoding="utf-8")
    for tok in cqA._FORB:
        assert tok not in text, f"forbidden token in runner source: {tok}"
    assert ".1.ttbin" not in text  # paired member never opened/concatenated


def test_armA_sys_modules_gate_trips_on_planted_module():
    planted = cqA._FORB[5]  # assembled at runtime; no literal in this file
    sys.modules[planted] = sys.modules[__name__]
    try:
        with pytest.raises(cqA.Refusal):
            cqA.assert_no_correction_machinery()
    finally:
        del sys.modules[planted]
    cqA.assert_no_correction_machinery()  # clean again


def test_armA_channel_record_hand_computed():
    a, b = _case_a(1000)
    rec = cqA.channel_record(a, b)
    assert rec["ser"] == pytest.approx(0.25)
    assert rec["pm1_mass"]["+1"] == pytest.approx(0.20)
    assert rec["plane_rates_lsb_first"][0] == pytest.approx(0.25)
    assert rec["plane_rates_lsb_first"][1] == pytest.approx(0.05)
    assert rec["expected_planes_flipped_per_error_via_diag"] == pytest.approx(1.2)
    assert rec["expected_planes_flipped_per_error_via_popcount"] == pytest.approx(1.2)
    assert rec["H_A_given_B"] == pytest.approx(0.0)
    assert rec["N_ab_support_cells"] == 3
    assert len(rec["time_block_stability"]) == 6


def _armA_header_with(config: dict[str, Any]) -> dict[str, Any]:
    return {"config": config, "source": "<fake>"}


def test_armA_header_validation_pass_and_refuse_paths():
    ok = cqA.validate_header_config(_armA_ok_header()["config"])
    assert ok["pair_validated"] is True
    assert ok["filewriter_channels"] == [1, 5, 1001, 1, 5, 1001]
    assert ok["coincidence_groups"] == [[1, 5]]
    assert ok["coincidence_window_raw"] == [1000]  # evidence only, not gated
    base_cfg = _armA_ok_header()["config"]

    def variant_fw(ch):
        cfg = json.loads(json.dumps(base_cfg))
        cfg["measurements"][0]["registered channels"] = ch
        cfg["measurements"][0]["params"]["channels"] = ch
        return cfg

    def variant_co(groups):
        cfg = json.loads(json.dumps(base_cfg))
        cfg["measurements"][1]["params"]["groups"] = groups
        return cfg

    with pytest.raises(cqA.Refusal):  # FileWriter missing channel 5
        cqA.validate_header_config(variant_fw([1, 1001]))
    with pytest.raises(cqA.Refusal):  # wrong pair group
        cqA.validate_header_config(variant_co([[1, 9]]))
    with pytest.raises(cqA.Refusal):  # no measurements at all
        cqA.validate_header_config({"registered channels": [1, 5]})
    # Window value is evidence-only: a non-200 window still validates the pair.
    other_win = json.loads(json.dumps(base_cfg))
    other_win["measurements"][1]["params"]["window"] = 200
    assert cqA.validate_header_config(other_win)["pair_validated"] is True


def _armA_tmp_base(root: str) -> str:
    """Fake base member inside a fresh workspace root (zero real contact)."""
    base = Path(root) / "Type0_nofilter_500K_3s_fake.ttbin"
    base.write_bytes(b"\x00")
    return str(base)


def test_armA_alignment_refuse_path():
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    saved = cqA.GROUPS["500K"]["base"]
    cqA.GROUPS["500K"]["base"] = _armA_tmp_base(root)
    try:
        with pytest.raises(cqA.Refusal):
            cqA.load_group_series(
                "500K", header_fn=lambda _b: _armA_ok_header(),
                read_fn=lambda _b: _armA_fake_events(),
                align_fn=lambda **_k: {"align_status": "blocked_low_peak_to_bg",
                                       "offset_ps_derived": 0})
    finally:
        cqA.GROUPS["500K"]["base"] = saved
        shutil.rmtree(root, ignore_errors=True)


def test_armA_execute_with_fake_series():
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    saved = cqA.GROUPS["500K"]["base"]
    cqA.GROUPS["500K"]["base"] = _armA_tmp_base(root)
    before = {m for m in sys.modules if "tagger" in m.lower()}
    try:
        s = cqA.execute(
            group="500K", root=root,
            header_fn=lambda _b: _armA_ok_header(),
            read_fn=lambda _b: _armA_fake_events(),
            align_fn=lambda **_k: _armA_ok_align(),
            rss_fn=lambda: 0.1)
        assert s["status"] == "OK"
        assert s["gid"] == "CQ-20a" and s["arm"] == "A"
        assert s["total_pairs"] == 2048 and s["clean_pairs"] == 2048
        assert s["framing_remainder"] == 0
        assert s["channel"]["ser"] == pytest.approx(0.0)
        assert s["provenance"]["offset_ps"] == 0
        assert Path(root, "CQ-20a.json").exists()
        after = {m for m in sys.modules if "tagger" in m.lower()}
        assert after == before  # zero TimeTagger contact
    finally:
        cqA.GROUPS["500K"]["base"] = saved
        shutil.rmtree(root, ignore_errors=True)


def test_armA_execute_captures_refusal_as_record():
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    saved = cqA.GROUPS["500K"]["base"]
    cqA.GROUPS["500K"]["base"] = _armA_tmp_base(root)
    try:
        s = cqA.execute(
            group="500K", root=root,
            header_fn=lambda _b: {"config": {"nothing": "here"},
                                  "source": "<fake>"},
            rss_fn=lambda: 0.1)
        assert s["status"].startswith("REFUSED-")
        assert Path(root, "CQ-20a.json").exists()
    finally:
        cqA.GROUPS["500K"]["base"] = saved
        shutil.rmtree(root, ignore_errors=True)


def test_armA_alignment_refuse_carries_evidence():
    root = _fresh_root()
    Path(root).mkdir(parents=True)
    saved = cqA.GROUPS["500K"]["base"]
    cqA.GROUPS["500K"]["base"] = _armA_tmp_base(root)
    try:
        s = cqA.execute(
            group="500K", root=root,
            header_fn=lambda _b: _armA_ok_header(),
            read_fn=lambda _b: _armA_fake_events(),
            align_fn=lambda **_k: {"align_status": "blocked_low_peak_to_bg",
                                   "offset_ps_derived": None,
                                   "peak_bin_index": 3,
                                   "peak_to_bg": 7.5,
                                   "sigma_crude_ps": 60.0,
                                   "count_A": 10, "count_B": 9,
                                   "total_pairs_in_window": 5},
            rss_fn=lambda: 0.1)
        assert s["status"].startswith("REFUSED-")
        assert s["provenance"]["align"]["peak_to_bg"] == pytest.approx(7.5)
        assert s["provenance"]["header_evidence"]["coincidence_groups"] == [[1, 5]]
        assert Path(root, "CQ-20a.json").exists()
    finally:
        cqA.GROUPS["500K"]["base"] = saved
        shutil.rmtree(root, ignore_errors=True)


def test_armA_non_exec_without_read():
    root = _fresh_root()
    try:
        for gid in ("CQ-12", "CQ-13a", "CQ-13b"):
            s = cqA.execute_non_exec(gid=gid, root=root)
            assert s["status"] == "NON_EXECUTION"
            assert Path(root, f"{gid}_NON_EXECUTION.json").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
