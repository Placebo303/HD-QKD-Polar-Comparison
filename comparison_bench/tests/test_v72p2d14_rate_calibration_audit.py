"""D14 Phase R focused tests: audit math fixtures + no-write/refusal checks.

Tiny fixtures only (32x2 tables — Alice dim is a multiple of 32 as the
accepted helpers require). The production decoder is never imported, no
scientific call is made, and no root outside pytest tmp paths is created.
The frozen audit root must remain absent after these tests (R1: no run).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5
import comparison_bench.formal_ir.v72p2d14_rate_calibration_audit as audit


def _tiny_counts():
    rng = np.random.default_rng(7)
    counts = rng.integers(0, 10, size=(32, 2)).astype(np.float64) + 1.0
    pb = np.array([0.4, 0.6])
    return counts, pb


def _expected_ce(counts, pb, smooth):
    pf = smooth(counts)
    fl = 1e-300
    joint = -sum(
        pb[b] * sum(max(pf[a, b], fl) * math.log2(max(pf[a, b], fl))
                    for a in range(32))
        for b in range(2))
    # A = 32*U1 + U2 with A-dim 32 -> U1 dim 1, U2 dim 32.
    p1 = pf.sum(axis=0, keepdims=True)  # (1, 2), already normalized
    l1 = -sum(pb[b] * sum(max(p1[u, b], fl) * math.log2(max(p1[u, b], fl))
                          for u in range(1)) for b in range(2))
    return joint, l1


def _candidate(counts):
    lam = d5.LAMBDA_STAR
    total = counts.sum()
    p_global = counts.sum(axis=1) / total
    n_b = counts.sum(axis=0)
    return (counts + lam * p_global[:, None]) / (n_b[None, :] + lam)


def test_generator_entropy_matches_hand_math():
    counts, pb = _tiny_counts()
    got = audit.generator_entropy(counts, pb)
    joint, l1 = _expected_ce(counts, pb / pb.sum(), _candidate)
    assert got["l1"] == pytest.approx(l1, rel=1e-12)
    assert got["joint"] == pytest.approx(joint, rel=1e-12)
    assert got["units"] == "bits_per_symbol"
    assert "prepare_model_f_prior_candidate" in got["estimator"]


def test_legacy_ce_diagnostic_matches_hand_math():
    counts, pb = _tiny_counts()
    got = audit.legacy_ce_diagnostic(counts, pb)
    joint, l1 = _expected_ce(counts, pb / pb.sum(),
                             lambda c: d5.build_f_model(c, d5.LAMBDA_STAR))
    assert got["l1"] == pytest.approx(l1, rel=1e-12)
    assert got["joint"] == pytest.approx(joint, rel=1e-12)
    assert "REJECTED" in got["estimator"]


def test_rate_row_record_frozen_p0_g1_tables():
    rec = audit.rate_row_record("G1", "L1", d5.CE_L1_MEAN, "test", 4.0, 64, 1.0)
    assert rec["stage"] == "G1"
    assert rec["rows"] == 49
    assert rec["disclosed_bits"] == 49 * 5
    assert rec["rows"] == d5._rows_required(d5.CE_L1_MEAN, 64, 1.0)
    assert audit.rate_row_record("G1", "L1", d5.CE_L1_MEAN, "t", 4.0, 64, 1.2)["rows"] == 59
    assert audit.rate_row_record("P0", "L2", d5.CE_L2_ORACLE_MEAN, "t", 3.0, 64, 1.0)["rows"] == 43
    assert audit.rate_row_record("G1", "L2", d5.CE_L2_ORACLE_MEAN, "t", 3.0, 64, 1.2)["rows"] == 52
    assert rec["nominal_factor"] == pytest.approx(245 / (64 * d5.CE_L1_MEAN))
    assert rec["effective_factor"] == pytest.approx(245 / (64 * 4.0))
    assert rec["entropy_load_bits"] == pytest.approx(64 * 4.0)


def test_block_self_info_deterministic_and_hand_checked():
    counts, pb = _tiny_counts()
    _, pf = d5.prepare_model_f_prior_candidate(counts, pb / pb.sum())
    a = audit.block_self_info(pb / pb.sum(), pf, 8, 1234)
    b = audit.block_self_info(pb / pb.sum(), pf, 8, 1234)
    assert a == b  # frozen seed -> identical block, never a new block
    blk = d5.sample_matched_block(pb / pb.sum(), pf, 8, 1234)
    p1 = d5.marginalize_f_to_p1(pf)
    fl = float(d5.AUDIT_FLOOR)
    want = sum(-math.log2(max(float(pb[int(x)]), fl))
               - math.log2(max(float(p1[int(v), int(x)]), fl))
               for x, v in zip(blk["bob"], blk["u1"]))
    assert a["i_l1_bits"] == pytest.approx(want, rel=1e-12)
    assert a["n"] == 8


def test_expand_cell_pairs_uses_call_counts_not_block_length():
    assert audit.expand_cell_pairs(1.5, 3, 1) == [(1.5, 0), (1.5, 0), (1.5, 1)]
    assert audit.expand_cell_pairs(2.0, 0, 0) == []
    with pytest.raises(ValueError):
        audit.expand_cell_pairs(2.0, 2, 3)


def test_quantile_summary_bins_and_correlation():
    pairs = [(float(i), 1 if i >= 6 else 0) for i in range(9)]
    q = audit.quantile_summary(pairs)
    assert [b["n"] for b in q["bins"]] == [3, 3, 3]
    assert [b["success"] for b in q["bins"]] == [0, 0, 3]
    assert q["pearson_r"] == pytest.approx(0.8215838, rel=1e-6)


def test_import_map_is_reuse_not_copy():
    assert audit.d5 is d5
    assert audit.model_f_in.load_model_f_input is not None
    import comparison_bench.formal_ir.v72p2d5_model_f_input as mfi
    assert audit.model_f_in is mfi
    assert audit.d11.L1_BLOCK_SEEDS is not None
    assert audit.d12.BLOCK_SEEDS is not None


def test_hypothesis_numbers_are_not_module_constants():
    src = Path(audit.__file__).read_text(encoding="utf-8")
    for token in ("4.2867", "3.2227", "0.890", "0.979", "1.068"):
        assert token not in src
    for token in ("decode_fn", "decode_row_layered", "BpOsd", "execution-authorized",
                  "execution_authorized"):
        assert token not in src


def test_refuse_non_accepted_input_root(tmp_path):
    with pytest.raises(ValueError):
        audit.refuse_unless_accepted_input(str(tmp_path))
    with pytest.raises(ValueError):
        audit.refuse_unless_allowed_records(str(tmp_path), "d12")
    with pytest.raises(ValueError):
        audit.refuse_fresh_out_root("results/some_audit")
    with pytest.raises(ValueError):
        audit.refuse_fresh_out_root(
            "workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450/x")
    existing = tmp_path / "exists"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        audit.refuse_fresh_out_root(str(existing))


def test_refuses_to_overwrite_existing_roots(tmp_path):
    # Post R-run the frozen audit root exists: a second run must refuse
    # before any write (no-overwrite proof); sentinel content stays intact.
    assert (ROOT / audit.FROZEN_AUDIT_ROOT).exists()
    with pytest.raises(FileExistsError):
        audit.refuse_fresh_out_root(audit.FROZEN_AUDIT_ROOT)
    sentinel = tmp_path / "root"
    sentinel.mkdir()
    (sentinel / "sentinel.txt").write_text("x")
    with pytest.raises(FileExistsError):
        audit.refuse_fresh_out_root(str(sentinel))
    assert (sentinel / "sentinel.txt").read_text() == "x"
