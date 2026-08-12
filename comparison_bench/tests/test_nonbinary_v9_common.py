"""V9 shared-helper tests (additive; V9-00/V9-20.1 scope).

Covers sizing exactness (H_q, m), harmonic-exact rho agreement with the V8
formula, exact reconstructed rates, the status vocabulary, the frozen seed
derivation and V9A seed/candidate/budget/gate constants, and the ctypes
process-tree RSS watcher.
"""
from __future__ import annotations

import hashlib
import math
import time

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_common as common
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_mcde as v8
from comparison_bench.src.comparison_bench.formal_ir import shared

# Frozen informative expected values (7-decimal rounded; the module COMPUTES
# the formula and never hard-codes them).
INFORMATIVE = {
    (0.20, 1.15): (0.2721646, 0.3129893),
    (0.20, 1.08): (0.2721646, 0.2939378),
    (0.30, 1.15): (0.3880868, 0.4462998),
    (0.30, 1.08): (0.3880868, 0.4191337),
}
#: The informative constants carry 7-decimal rounding; a 1e-9 absolute bound
#: against them is arithmetically impossible (e.g. the full-precision
#: H_q(0.2)=0.27216461808 differs from the rounded 0.2721646 by 1.8e-8).  The
#: formula-exactness assertions below use 1e-12; agreement with the rounded
#: informative constants uses 1e-7 (their rounding bound).
_INFORMATIVE_TOL = 1e-7


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


# --------------------------------------------------------------------------- #
# sizing (formula-exact, never hard-coded)
# --------------------------------------------------------------------------- #


def test_sizing_formula_exact():
    assert abs(math.log2(1023) - 9.998590) < 1e-6
    for p in (0.20, 0.30):
        h2 = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
        expected = (h2 + p * math.log2(1023)) / 10.0
        assert abs(common.qary_entropy_bits_baseq(1024, p) - expected) < 1e-12


def test_sizing_vs_informative_and_integer_checks():
    for (p, f), (hq_info, mn_info) in INFORMATIVE.items():
        hq = common.qary_entropy_bits_baseq(1024, p)
        assert abs(hq - hq_info) <= _INFORMATIVE_TOL, (p, f, hq, hq_info)
        assert abs(f * hq - mn_info) <= _INFORMATIVE_TOL, (p, f, f * hq, mn_info)
        m = common.checks_for(f, p, 1024)
        assert m == math.ceil(f * hq * 1024), (p, f, m)
        assert abs(m - f * hq * 1024) < 1.0, (p, f, m)  # integer ratio within 1/1024


def test_checks_for_informative_counts():
    # Informative whole-check counts at n=1024 (proposal text): 321/458 robust,
    # 301/430 target.
    assert common.checks_for(1.15, 0.20, 1024) == 321
    assert common.checks_for(1.15, 0.30, 1024) == 458
    assert common.checks_for(1.08, 0.20, 1024) == 301
    assert common.checks_for(1.08, 0.30, 1024) == 430


def test_sizing_fail_closed():
    with pytest.raises(ValueError):
        common.qary_entropy_bits_baseq(1024, 0.0)
    with pytest.raises(ValueError):
        common.qary_entropy_bits_baseq(1024, 1.0)
    with pytest.raises(ValueError):
        common.qary_entropy_bits_baseq(3, 0.2)          # not a power of two
    with pytest.raises(ValueError):
        common.qary_entropy_bits_baseq(2048, 0.2)       # > 1024
    with pytest.raises(ValueError):
        common.checks_for(0.0, 0.20, 1024)
    with pytest.raises(ValueError):
        common.checks_for(1.15, 0.20, 0)


# --------------------------------------------------------------------------- #
# harmonic-exact rho (own V8-60 formula implementation)
# --------------------------------------------------------------------------- #


def test_harmonic_rho_matches_v8_formula():
    """The own v9 implementation of the V8-60 concentrated formula agrees with
    the accepted V8 module within 1e-12 for several (rate, lambda) pairs."""
    pairs = [
        (0.75, {2: 0.107, 4: 0.245, 7: 0.192, 10: 0.034, 19: 0.207, 26: 0.161, 28: 0.049}),
        (0.5, {2: 0.5, 3: 0.5}),
        (0.9, {2: 0.3, 4: 0.7}),
        (0.6870106892038108, {2: 0.35, 3: 0.30, 20: 0.35}),
        (0.5537001767622565, {3: 1.0}),
        (0.7060622124696657, {2: 0.20, 3: 0.45, 30: 0.35}),
        (0.5808662529593365, {2: 0.50, 3: 0.15, 40: 0.35}),
    ]
    for rate, lam in pairs:
        own = common.concentrated_check_distribution(rate, lam)
        v8c = v8.concentrated_check_distribution(rate, lam)
        assert set(own) == set(v8c)
        for key in own:
            assert abs(float(own[key]) - float(v8c[key])) < 1e-12, (rate, lam, key)


def test_concentrated_rho_degenerates_to_regular():
    conc = common.concentrated_check_distribution(0.5, {3: 1.0})
    assert abs(conc["dc_mean"] - 6.0) < 1e-12
    assert abs(conc["w_lo"] - 1.0) < 1e-12 and abs(conc["w_hi"] - 0.0) < 1e-12
    assert _rho_from_concentrated(conc) == {6: 1.0}


def test_concentrated_rho_fail_closed():
    with pytest.raises(ValueError):
        common.concentrated_check_distribution(1.0, {2: 1.0})   # (1-rate) <= 0
    with pytest.raises(ValueError):
        common.concentrated_check_distribution(0.5, {2: 1000.0})  # dc < 2
    with pytest.raises(ValueError):
        common.concentrated_check_distribution(0.5, {})


# --------------------------------------------------------------------------- #
# exact reconstructed rates for the whole frozen V9A package
# --------------------------------------------------------------------------- #


def test_reconstructed_rate_exact_all_candidates_all_searches():
    """For every candidate in the frozen population and every search
    (stratum/tier) of the V9A plan, the harmonic-exact concentrated rho
    reconstructs the target rate to <= 1e-12."""
    for search_id, spec in common.V9A_SEARCH_SPECS.items():
        p, f = spec["stratum_p"], spec["tier_f"]
        rate = 1.0 - f * common.qary_entropy_bits_baseq(1024, p)
        for candidate_id, lam in common.V9A_CANDIDATES.items():
            conc = common.concentrated_check_distribution(rate, lam)
            rho = _rho_from_concentrated(conc)
            assert abs(common.reconstructed_rate(lam, rho) - rate) <= 1e-12, (
                search_id, candidate_id)
            assert min(rho) >= 2, (search_id, candidate_id)  # no degree-1 checks
            assert max(rho) <= 40, (search_id, candidate_id)


# --------------------------------------------------------------------------- #
# status vocabulary
# --------------------------------------------------------------------------- #


def test_status_vocabulary_matches_shared():
    assert common.FORMAL_STATUSES == shared.FORMAL_STATUSES
    assert common.V9_STATUS_RESOURCE_ABORT == "aborted_resource_limit"
    assert common.V9_STATUS_RESOURCE_ABORT in common.FORMAL_STATUSES


# --------------------------------------------------------------------------- #
# seed derivation (frozen rule)
# --------------------------------------------------------------------------- #


def test_constituent_seed_rule_exact():
    for prefix, frame, const in (("20260901", 0, 0), ("20260901", 1, 3),
                                 ("20260902", 7, 31), ("20260904", 0, 15)):
        tag = f"{prefix}:frame{frame}:const{const}"
        expected = int(hashlib.sha256(tag.encode("utf-8")).hexdigest()[0:8], 16)
        assert common.constituent_seed(prefix, frame, const) == expected
        err = common.error_pattern_seed(prefix, frame, const)
        err_expected = int(hashlib.sha256(
            (tag + ":err").encode("utf-8")).hexdigest()[0:8], 16)
        assert err == err_expected
        assert err != expected  # error-pattern seed is distinct


def test_seed_distinctness_and_disjointness_from_prior():
    all_v9 = (list(common.V9A_OPTIMIZATION_SEEDS.values())
              + list(common.V9A_VALIDATION_SEEDS))
    assert len(set(all_v9)) == len(all_v9)  # pairwise disjoint
    assert all(str(seed).startswith("202609") for seed in all_v9)
    # Frozen representative prior V1-V8 seeds (V6 20260802xx, V7 20260804xx /
    # 20260805xxxx, V8 20260804xx) — disjoint by the 202609 prefix.
    prior = [2026080201, 2026080401, 2026080402, 2026080403, 2026080411,
             2026080412, 2026080418, 2026080420, 2026080421, 2026080501]
    assert not set(all_v9) & set(prior)
    assert not any(str(s).startswith("202609") for s in prior)


def test_seed_derivation_fail_closed():
    with pytest.raises(ValueError):
        common.constituent_seed("20260901", -1, 0)
    with pytest.raises(ValueError):
        common.constituent_seed("20260901", 0, -1)


# --------------------------------------------------------------------------- #
# frozen V9A plan constants (V9-20.1)
# --------------------------------------------------------------------------- #


def test_v9a_search_specs_frozen():
    expected = {
        "S1": (0.20, 1.15, "robust", (0.15, 0.26), 0.22),
        "S2": (0.20, 1.08, "target", (0.15, 0.26), 0.215),
        "S3": (0.30, 1.15, "robust", (0.24, 0.36), 0.32),
        "S4": (0.30, 1.08, "target", (0.24, 0.36), 0.32),
    }
    assert set(common.V9A_SEARCH_SPECS) == set(expected)
    for sid, (p, f, label, probe, gate) in expected.items():
        spec = common.V9A_SEARCH_SPECS[sid]
        assert spec["stratum_p"] == p and spec["tier_f"] == f
        assert spec["tier_label"] == label
        assert tuple(spec["probe_range"]) == probe
        assert spec["gate_conservative"] == gate
    assert common.V9A_GATES == {"robust": {0.20: 0.22, 0.30: 0.32},
                                "target": {0.20: 0.215, 0.30: 0.32}}
    assert common.V9A_PROBE_RANGES == {0.20: (0.15, 0.26), 0.30: (0.24, 0.36)}
    assert common.V9A_OPTIMIZATION_SEEDS == {
        "S1": 2026090101, "S2": 2026090102, "S3": 2026090103, "S4": 2026090104}
    assert tuple(common.V9A_VALIDATION_SEEDS) == (2026090111, 2026090112, 2026090113)


def test_v9a_candidates_frozen():
    expected = {
        "C1": {2: 0.35, 3: 0.30, 20: 0.35},
        "C2": {2: 0.40, 3: 0.25, 30: 0.35},
        "C3": {2: 0.45, 3: 0.20, 40: 0.35},
        "C4": {2: 0.30, 3: 0.35, 20: 0.35},
        "C5": {3: 1.0},
        "C6": {2: 0.25, 3: 0.40, 40: 0.35},
        "C7": {2: 0.50, 3: 0.15, 40: 0.35},
        "C8": {2: 0.20, 3: 0.45, 30: 0.35},
    }
    assert dict(common.V9A_CANDIDATES) == expected
    assert [f"C{i}" for i in range(1, 9)] == list(common.V9A_CANDIDATES)
    for lam in common.V9A_CANDIDATES.values():
        assert all(1 <= d <= 40 for d in lam)
        assert abs(sum(lam.values()) - 1.0) < 1e-9


def test_v9a_budgets_frozen():
    assert common.V9A_BUDGETS == {
        "n_samples": 2000, "max_iter": 150, "entropy_tol": 0.01,
        "streak": 20, "floor": 1e-300, "p_tol": 0.002}
    assert common.V9_RSS_CAP_BYTES == 3 * 1024 ** 3


# --------------------------------------------------------------------------- #
# process-tree RSS watcher (ctypes)
# --------------------------------------------------------------------------- #


def test_rss_watcher_records_peak_and_cap():
    with common.ProcessTreeRSSWatcher(interval=0.02, cap_bytes=1024 ** 3) as watcher:
        time.sleep(0.15)
    assert watcher.peak_rss_bytes > 0
    assert len(watcher.samples) >= 1
    assert watcher.cap_exceeded is False


def test_rss_watcher_cap_exceeded():
    watcher = common.ProcessTreeRSSWatcher(interval=0.02, cap_bytes=1)
    watcher.start()
    try:
        time.sleep(0.15)
        assert watcher.peak_rss_bytes > 0
        assert watcher.cap_exceeded is True
    finally:
        watcher.stop()


def test_rss_watcher_validation():
    with pytest.raises(ValueError):
        common.ProcessTreeRSSWatcher(interval=0.0)
    with pytest.raises(ValueError):
        common.ProcessTreeRSSWatcher(interval=-1.0)
    with pytest.raises(ValueError):
        common.ProcessTreeRSSWatcher(cap_bytes=-5)
