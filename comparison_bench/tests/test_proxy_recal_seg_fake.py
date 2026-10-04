"""Fake-only tests for the segmented proxy driver (R2 T-R2-02).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no CQ JSON, no baseline rows, no graph, no archive, nothing.
The only files touched are fresh additive
workspace/proxy_recal_r2__pytest_<uuid8> roots created below. Fake SEG
rows are hand-built dicts (block_idx/seed/failed), never decoder outputs.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli import proxy_recal_sampler as pr
from comparison_bench.src.comparison_bench.cli import proxy_recal_sampler_seg as seg


def _fresh_root() -> Path:
    root = Path(f"workspace/proxy_recal_r2__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def _fake_rows(idx_list: list[int]) -> list[dict]:
    return [{"block_idx": i, "seed": pr.FRAME_BASE + i,
             "failed": i % 2, "undetected": 0} for i in idx_list]


def test_pytest_root_is_fresh_additive():
    root = _fresh_root()
    assert root.is_dir()
    assert str(root).startswith("workspace/proxy_recal_r2__pytest_")


def test_partition_covers_frozen_once_ascending():
    parts = [seg.segment_idx_list(g) for g in range(6)]
    assert all(len(p) == 40 for p in parts)
    assert parts[0] == list(range(0, 40)) and parts[5] == list(range(200, 240))
    flat = [i for p in parts for i in p]
    assert flat == list(range(240))  # ascending, no overlap, no gap
    seeds = [seg.segment_seeds(g) for g in range(6)]
    assert seeds[0][0] == pr.FRAME_BASE and seeds[5][-1] == pr.FRAME_BASE + 239


def test_num_segments_refusal():
    assert seg.validate_num_segments(6) == 6
    for bad in (1, 5, 7, 40, 240):
        with pytest.raises(pr.Refusal):
            seg.validate_num_segments(bad)
    with pytest.raises(pr.Refusal):
        seg.segment_idx_list(0, num_segments=5)
    with pytest.raises(pr.Refusal):
        seg.segment_idx_list(6)


def test_dual_flag_refusal():
    with pytest.raises(pr.Refusal):
        seg.require_dual_flags(False, True)
    with pytest.raises(pr.Refusal):
        seg.require_dual_flags(True, False)
    seg.require_dual_flags(True, True)


def test_checkpoint_survives_kill():
    # Simulate a kill after k blocks: the rewritten SEG file retains them.
    root = _fresh_root()
    seg_path = root / "SEG_2.json"
    k = 17
    rows = _fake_rows(seg.segment_idx_list(2))[:k]
    for n in range(1, k + 1):  # per-block rewrite, full-file + flush
        seg.write_seg_file(seg_path, {"segment_index": 2, "num_segments": 6,
                                      "idx_range": [80, 119],
                                      "validation": {"verdict": "PASS"},
                                      "rows": rows[:n], "block_count": n})
    back = seg.read_seg_file(seg_path)
    assert back["block_count"] == k
    assert [r["block_idx"] for r in back["rows"]] == list(range(80, 80 + k))


def test_assemble_refuses_short():
    full = [seg.segment_idx_list(g) for g in range(6)]
    short = [_fake_rows(p) for p in full[:5]]  # 200 rows only
    with pytest.raises(pr.Refusal):
        seg.assemble_rows(short)
    thin = [_fake_rows(p) for p in full]
    thin[3] = thin[3][:39]  # 239 rows
    with pytest.raises(pr.Refusal):
        seg.assemble_rows(thin)


def test_assemble_refuses_overlap():
    full = [seg.segment_idx_list(g) for g in range(6)]
    rows = [_fake_rows(p) for p in full]
    rows[1] = _fake_rows(full[0])  # duplicate idx 0..39, gap at 40..79
    with pytest.raises(pr.Refusal):
        seg.assemble_rows(rows)
    rows2 = [_fake_rows(p) for p in full]
    rows2[4][0] = {"block_idx": 160, "seed": pr.FRAME_BASE + 999,
                   "failed": 0, "undetected": 0}  # seed mismatch
    with pytest.raises(pr.Refusal):
        seg.assemble_rows(rows2)


def test_assemble_accepts_full_240_in_order():
    rows = [_fake_rows(seg.segment_idx_list(g)) for g in range(6)]
    flat = seg.assemble_rows(rows)
    assert len(flat) == 240
    assert [r["block_idx"] for r in flat] == list(range(240))


def test_word_helper_equality_three_cases():
    cases = [(15, 10, 0.030, 0.080, 0.025875, 0.066776),   # PASS
             (60, 10, 0.200, 0.300, 0.025875, 0.066776),   # MARGINAL
             (10, 10, 0.020, 0.070, 0.025875, 0.066776)]   # KILL
    for args in cases:
        assert seg.decide_word(*args) == pr.decide_word(*args)
    assert seg.decide_word(*cases[0]) == ("PASS", "section 5.1")
    assert seg.decide_word(*cases[1]) == ("MARGINAL", "section 5.2")
    assert seg.decide_word(*cases[2]) == ("KILL", "section 5.3")


def test_path_gate_refuses_archives_before_any_read():
    with pytest.raises(pr.Refusal):
        seg.validate_input_path("docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz")
    with pytest.raises(pr.Refusal):
        seg.validate_input_path("workspace/cq_15d6f160/frames.ttbin")
    with pytest.raises(pr.Refusal):
        seg.validate_input_path("comparison_bench/outputs_comparison/pairs.parquet")
    with pytest.raises(pr.Refusal):
        seg.validate_input_path("workspace/m3a_nested_200p8_20260926/arm2.json")
    for path, role in pr.FROZEN_INPUTS.items():  # string check only, no read
        assert seg.validate_input_path(path) == role


def test_root_gate_seg_pattern():
    assert seg.validate_root_string("workspace/proxy_recal_r2_1234abcd") == \
        "workspace/proxy_recal_r2_1234abcd"
    with pytest.raises(pr.Refusal):  # Packet-A single-shot pattern rejected
        seg.validate_root_string("workspace/proxy_recal_1234abcd")
    with pytest.raises(pr.Refusal):
        seg.validate_root_string("results/ir_benchmark_results.csv")
    with pytest.raises(pr.Refusal):
        seg.validate_root_string("comparison_bench/outputs_comparison/x.json")
