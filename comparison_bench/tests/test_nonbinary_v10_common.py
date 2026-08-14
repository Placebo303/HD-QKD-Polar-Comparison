"""V10 shared-helper tests (additive; V10-10 scope, T0/T1).

Covers sizing exactness (H_q, m), the lambda exponent<->degree off-by-one
mapping with explicit examples, harmonic-exact rho agreement with the V8-60
formula (V8 is a test-only oracle), exact reconstructed rates, node-view
conversion, the K=8 lambda validator, the frozen V10-0 q=4 contract constants,
seed derivation and disjointness from all V8/V9 seeds, the ctypes process-tree
RSS watcher, and the no-production-import boundary for all four V10 modules.
"""
from __future__ import annotations

import hashlib
import inspect
import math
import time
import types

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_mcde as v8
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField

V10_MODULE_PATHS = {
    "common": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_common.py",
    "de": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_de.py",
    "peg": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_peg.py",
    "fftqspa": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_fftqspa.py",
}

# Frozen informative expected values (7-decimal rounded; the module COMPUTES
# the formula and never hard-codes them).
_INFORMATIVE_TOL = 1e-7


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


# --------------------------------------------------------------------------- #
# T0: compile / import / field identity
# --------------------------------------------------------------------------- #


def test_module_imports_and_no_v8_v9_binding():
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_common as m_common
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_de as m_de
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_peg as m_peg
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_fftqspa as m_fft
    for module in (m_common, m_de, m_peg, m_fft):
        for value in vars(module).values():
            if isinstance(value, types.ModuleType):
                assert not value.__name__.startswith(
                    ("nonbinary_v8", "nonbinary_v9", "nonbinary_v1", "nonbinary_v2",
                     "nonbinary_v3", "nonbinary_v4", "nonbinary_v5", "nonbinary_v6",
                     "nonbinary_v7", "nonbinary_qspa")), (module.__name__, value.__name__)
                assert "decode" not in value.__name__ and "production" not in value.__name__


def test_no_forbidden_import_lines_in_v10_sources():
    import re
    forbidden = re.compile(
        r"^\s*(from|import)\s+.*(nonbinary_qspa|nonbinary_v[1-9](?![0-9])|"
        r"decode_|production|numpy\s*\.\s*fft)", re.MULTILINE)
    for name, path in V10_MODULE_PATHS.items():
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert not forbidden.search(source), f"{name}: forbidden import line"
        assert "nonbinary_v8" not in source and "nonbinary_v9" not in source, f"{name}: V8/V9 token"


def test_gf1024_field_identity():
    field = GF2mField.create(1024)
    assert len(field.nonzero_cycle) == 1023
    assert len(set(field.nonzero_cycle)) == 1023
    for value in range(1024):
        assert field.add(value, 0) == value
        assert field.mul(value, 1) == value
        assert field.mul(value, 0) == 0
    for value in range(1, 1024):
        assert field.mul(value, field.inverse(value)) == 1
    assert field.mul(3, 7) == field.mul(7, 3)


# --------------------------------------------------------------------------- #
# T0: lambda exponent <-> degree off-by-one
# --------------------------------------------------------------------------- #


def test_lambda_exponent_degree_mapping_explicit():
    """lambda(x) = sum_d lambda_d * x^(d-1): exponent d-1 <-> degree d."""
    assert {d - 1 for d in (2, 3, 40)} == {1, 2, 39}
    assert 2 - 1 == 1      # degree 2 <-> exponent 1 (x^1)
    assert 3 - 1 == 2      # degree 3 <-> exponent 2 (x^2)
    assert 40 - 1 == 39    # degree 40 <-> exponent 39 (x^39)
    lam = {2: 0.5, 3: 0.5}
    exponents = {degree - 1 for degree in lam}
    assert exponents == {1, 2}
    # The published q=4 lambda keyed by degrees must equal V8's exponent-keyed
    # published polynomial shifted by +1.
    published_degrees = common.MULLER_Q4_LAMBDA_PUBLISHED_DEGREES
    assert set(published_degrees) == {exp + 1 for exp in v8.REPRODUCTION_LAMBDA_PUBLISHED}
    assert {published_degrees[exp + 1] for exp in v8.REPRODUCTION_LAMBDA_PUBLISHED} \
        == set(v8.REPRODUCTION_LAMBDA_PUBLISHED.values())


# --------------------------------------------------------------------------- #
# T0: sizing (formula-exact, never hard-coded)
# --------------------------------------------------------------------------- #


def test_sizing_formula_exact():
    for p in (0.20, 0.30):
        h2 = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
        expected = (h2 + p * math.log2(1023)) / 10.0
        assert abs(common.qary_entropy_bits_baseq(1024, p) - expected) < 1e-12
    h2_q4 = -0.2 * math.log2(0.2) - 0.8 * math.log2(0.8)
    expected_q4 = (h2_q4 + 0.2 * math.log2(3)) / 2.0
    assert abs(common.qary_entropy_bits_baseq(4, 0.2) - expected_q4) < 1e-12


def test_sizing_vs_informative_and_integer_checks():
    for (p, f), (hq_info, mn_info) in {
        (0.20, 1.15): (0.2721646, 0.3129893),
        (0.20, 1.08): (0.2721646, 0.2939378),
        (0.30, 1.15): (0.3880868, 0.4462998),
        (0.30, 1.08): (0.3880868, 0.4191337),
    }.items():
        hq = common.qary_entropy_bits_baseq(1024, p)
        assert abs(hq - hq_info) <= _INFORMATIVE_TOL
        assert abs(f * hq - mn_info) <= _INFORMATIVE_TOL
        m = common.checks_for(f, p, 1024)
        assert m == math.ceil(f * hq * 1024)
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
        common.qary_entropy_bits_baseq(3, 0.2)
    with pytest.raises(ValueError):
        common.qary_entropy_bits_baseq(2048, 0.2)
    with pytest.raises(ValueError):
        common.checks_for(0.0, 0.20, 1024)
    with pytest.raises(ValueError):
        common.checks_for(1.15, 0.20, 0)


# --------------------------------------------------------------------------- #
# T0: harmonic-exact rho (own V8-60 formula) + rate exactness
# --------------------------------------------------------------------------- #


def test_harmonic_rho_matches_v8_formula():
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


def test_concentrated_rho_reconstruction_rate_exact():
    for rate, lam in [(0.75, {2: 0.107, 4: 0.245, 7: 0.192, 10: 0.034,
                              19: 0.207, 26: 0.161, 28: 0.049}),
                      (0.5, {2: 0.5, 3: 0.5}),
                      (0.9, {2: 0.3, 4: 0.7})]:
        conc = common.concentrated_check_distribution(rate, lam)
        rho = _rho_from_concentrated(conc)
        assert abs(common.reconstructed_rate(lam, rho) - rate) <= 1e-12
        assert abs(conc["rate_reconstructed"] - rate) <= 1e-12
        assert min(rho) >= 2


def test_concentrated_rho_degenerates_to_regular():
    conc = common.concentrated_check_distribution(0.5, {3: 1.0})
    assert abs(conc["dc_mean"] - 6.0) < 1e-12
    assert abs(conc["w_lo"] - 1.0) < 1e-12 and abs(conc["w_hi"] - 0.0) < 1e-12
    assert _rho_from_concentrated(conc) == {6: 1.0}


def test_edge_mean_inverse_and_node_view():
    assert abs(common.edge_mean_inverse({2: 0.5, 3: 0.5}) - (0.25 + 1.0 / 6.0)) < 1e-12
    node = common.edge_to_node_hist({2: 0.5, 3: 0.5})
    assert abs(node[2] - 0.6) < 1e-12 and abs(node[3] - 0.4) < 1e-12
    assert abs(sum(node.values()) - 1.0) < 1e-12


# --------------------------------------------------------------------------- #
# T1: lambda validator
# --------------------------------------------------------------------------- #


def test_lambda_validate_accepts_valid():
    lam = {2: 0.2, 3: 0.3, 5: 0.15, 8: 0.1, 12: 0.1, 20: 0.05, 30: 0.05, 40: 0.05}
    assert sum(lam.values()) == 1.0
    result = common.lambda_validate(lam)
    assert result == lam
    assert list(result) == sorted(lam)


def test_lambda_validate_violations():
    good = {2: 0.2, 3: 0.3, 5: 0.15, 8: 0.1, 12: 0.1, 20: 0.05, 30: 0.05, 40: 0.05}
    with pytest.raises(ValueError):
        common.lambda_validate({2: 0.2, 3: 0.3, 5: 0.15, 8: 0.1, 12: 0.1, 20: 0.05, 30: 0.05})

    class _DupDegreeDict(dict):
        """Mapping with 8 entries but a duplicated degree (dict keys cannot
        duplicate, so this exercises the uniqueness branch directly)."""
        def __len__(self):
            return 8

        def items(self):
            return [(2, 0.2), (2, 0.25), (5, 0.15), (8, 0.1), (12, 0.1),
                    (20, 0.05), (30, 0.05), (40, 0.1)]

    with pytest.raises(ValueError):
        common.lambda_validate(_DupDegreeDict())
    low = dict(good)
    low[40] = 0.005
    with pytest.raises(ValueError):
        common.lambda_validate(low)
    off = dict(good)
    off[2] = 0.25
    with pytest.raises(ValueError):
        common.lambda_validate(off)
    nan = dict(good)
    nan[2] = math.nan
    with pytest.raises(ValueError):
        common.lambda_validate(nan)
    ood = dict(good)
    ood.pop(2)
    ood[1] = 0.2
    with pytest.raises(ValueError):
        common.lambda_validate(ood)
    with pytest.raises(ValueError):
        common.lambda_validate(42)


# --------------------------------------------------------------------------- #
# channel and entropy math
# --------------------------------------------------------------------------- #


def test_qsc_channel_message():
    vector = common.qsc_channel_message(4, 0.2)
    assert abs(vector[0] - 0.8) < 1e-12
    assert abs(vector[1] - 0.2 / 3.0) < 1e-12
    assert abs(vector.sum() - 1.0) < 1e-12
    with pytest.raises(ValueError):
        common.qsc_channel_message(4, 0.0)
    with pytest.raises(ValueError):
        common.qsc_channel_message(4, 0.75)


def test_entropy_base_q_math():
    uniform = np.full(4, 0.25)
    assert abs(common.entropy_base_q(uniform, 4) - 1.0) < 1e-12
    delta = np.zeros(4)
    delta[0] = 1.0
    assert common.entropy_base_q(delta, 4) == 0.0
    qsc = common.qsc_channel_message(8, 0.2)
    expected = -(0.8 * math.log(0.8) + 0.2 * math.log(0.2 / 7)) / math.log(8)
    assert abs(common.entropy_base_q(qsc, 8) - expected) < 1e-12
    with pytest.raises(ValueError):
        common.entropy_base_q(np.full(3, 1.0 / 3.0), 4)


# --------------------------------------------------------------------------- #
# seed derivation and disjointness
# --------------------------------------------------------------------------- #


def test_v10_seed_rule_exact():
    for tag in ("frame:0:const:0", "de:init:2026100201", "err:1"):
        expected = int(hashlib.sha256(f"V10:{tag}".encode("utf-8")).hexdigest()[0:8], 16)
        assert common.v10_seed(tag) == expected
        assert 0 < common.v10_seed(tag) < 2 ** 32
    with pytest.raises(ValueError):
        common.v10_seed(123)


def test_seed_disjointness_from_prior():
    v10_seeds = [2026100000, 2026100100, 2026100101, 2026100102, 2026100103,
                 2026100201, 2026100202, 2026100203, 2026100204,
                 2026100211, 2026100212, 2026100213, 2026100214, 2026100215,
                 2026100300, 2026100301]
    assert len(set(v10_seeds)) == len(v10_seeds)
    assert all(str(seed).startswith(common.V10_SEED_PREFIX) for seed in v10_seeds)
    prior = [2026080418, 2026080420, 2026080421, 2026090101, 2026090102, 2026090103,
             2026090104, 2026090111, 2026090112, 2026090113]
    assert not set(v10_seeds) & set(prior)
    assert max(prior) < min(v10_seeds)


# --------------------------------------------------------------------------- #
# frozen constants
# --------------------------------------------------------------------------- #


def test_frozen_q4_contract_constants():
    assert common.V10_0_Q4_TARGET_DET == 0.069
    assert common.V10_0_Q4_TOL == 0.012
    assert common.V10_0_Q4_RATE == 0.75
    assert common.V10_0_Q4_N_SAMPLES == 100000
    assert common.V10_0_Q4_MAX_ITER == 150
    assert common.V10_0_Q4_P_LO == 0.01
    assert common.V10_0_Q4_P_HI == 0.12
    assert common.V10_0_Q4_P_TOL == 0.0025
    assert common.V10_0_Q4_ENTROPY_TOL == 0.01
    assert common.V10_0_Q4_STREAK == 20
    assert common.V10_RSS_CAP_BYTES == 3 * 1024 ** 3


def test_muller_q4_lambda_constant_verbatim():
    assert common.MULLER_Q4_LAMBDA_PUBLISHED_DEGREES == {
        2: 0.107, 4: 0.245, 7: 0.192, 10: 0.034, 19: 0.207, 26: 0.161, 28: 0.049}


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


# --------------------------------------------------------------------------- #
# source-structure guards
# --------------------------------------------------------------------------- #


def test_fftqspa_source_has_no_alice_truth_parameters():
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_fftqspa as m_fft
    for name in ("decode_fftqspa", "decode_error_domain"):
        parameters = inspect.signature(getattr(m_fft, name)).parameters
        assert "x" not in parameters, name
        assert "e" not in parameters, name
        assert "error_syndrome" in parameters or "s_x" in parameters, name
