"""V8 full-vector QSC MC-DE tests (additive; T0/T1/T2).

Covers channel/entropy math, degree-perspective conversions, the concentrated
check distribution, XOR convolution, determinism, frozen golden traces
(recorded once; regenerating requires the recorded seed), fail-closed
boundaries, the threshold-search sanity check, and (T2 only) the frozen
published-reproduction trace, the read-only source manifest and the
no-production-runner import boundary.
"""
from __future__ import annotations

import hashlib
import json
import math
import os

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_mcde as de
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_reference as ref

REPO_ROOT = "."
REPO_ROOT = "."
EVIDENCE = "openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence"
V8_MODULE_PATHS = {
    "error_domain": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py",
    "reference": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_reference.py",
    "mcde": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_mcde.py",
}


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    """Build the degree mapping from a concentrated dict, dropping any
    zero-weight point (a degenerate integer-mean two-point distribution)."""
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


# --------------------------------------------------------------------------- #
# 1. channel message math + entropy
# --------------------------------------------------------------------------- #


def test_qsc_channel_message_and_entropy():
    message = de.qsc_channel_message(4, 0.1)
    assert abs(message[0] - 0.9) < 1e-12
    assert abs(float(message.sum()) - 1.0) < 1e-12
    uniform = np.full((10, 4), 0.25)
    assert abs(de.entropy_base_q(uniform) - 1.0) < 1e-12
    delta = np.zeros((10, 4))
    delta[:, 0] = 1.0
    assert de.entropy_base_q(delta) == 0.0
    qsc = np.stack([de.qsc_channel_message(8, 0.2)] * 5)
    expected = -(0.8 * math.log(0.8) + 0.2 * math.log(0.2 / 7)) / math.log(8)
    assert abs(de.entropy_base_q(qsc) - expected) < 1e-12


# --------------------------------------------------------------------------- #
# 2. degree conversions
# --------------------------------------------------------------------------- #


def test_degree_conversion_roundtrips_and_rejections():
    edge = {2: 0.5, 3: 0.5}
    node = de.edge_to_node_hist(edge)
    assert abs(sum(node.values()) - 1.0) < 1e-12
    assert de.node_to_edge_hist(node) == pytest.approx(edge, abs=1e-12)
    node2 = {2: 0.6, 4: 0.4}
    edge2 = de.node_to_edge_hist(node2)
    assert abs(sum(edge2.values()) - 1.0) < 1e-12
    assert de.edge_to_node_hist(edge2) == pytest.approx(node2, abs=1e-12)
    with pytest.raises(ValueError):
        de.edge_to_node_hist({2: 0.5, 3: 0.4})          # sum != 1
    with pytest.raises(ValueError):
        de.node_to_edge_hist({2: 0.5, 3: 0.3})          # sum != 1
    with pytest.raises(ValueError):
        de.edge_to_node_hist({2: -0.5, 3: 1.5})         # negative weight
    degrees, probs = de.parse_degree_hist({2: 0.5, 3: 0.5}, "lam", 64)
    assert abs(float(probs.sum()) - 1.0) < 1e-12
    # parse_degree_hist normalizes published rounded vectors (sum ~= 0.995)
    degrees_p, probs_p = de.parse_degree_hist(de.REPRODUCTION_LAMBDA_PUBLISHED, "lam", 64)
    assert abs(float(probs_p.sum()) - 1.0) < 1e-12
    assert list(degrees_p) == sorted(de.REPRODUCTION_LAMBDA_PUBLISHED)
    for bad in ({}, {2: 0.0}, {2: -1.0}, {2: math.nan}, {0: 1.0}, {65: 1.0}, {2.5: 1.0}):
        with pytest.raises(ValueError):
            de.parse_degree_hist(bad, "lam", 64)


# --------------------------------------------------------------------------- #
# 3. concentrated check distribution
# --------------------------------------------------------------------------- #


def test_concentrated_check_distribution_reproduction():
    """For the reproduction config: target = (1-0.75)*integral_lambda, dc =
    1/target = 24.3285893... -> dc_lo/dc_hi = 24/25; the harmonic-exact weights
    solve sum_j rho_j/j = target exactly and the reconstructed rate equals 0.75
    to <= 1e-12.  The old two-point-mean assertion (w_lo*dc_lo + w_hi*dc_hi ==
    dc_mean) no longer holds by design (V8-60: mean-matched weights were an
    approximation of the edge-perspective rate condition)."""
    lam = de.REPRODUCTION_LAMBDA_DEGREES
    integral = sum(weight / degree for degree, weight in lam.items())
    target = (1.0 - 0.75) * integral
    conc = de.concentrated_check_distribution(0.75, lam)
    assert conc["dc_lo"] == 24.0 and conc["dc_hi"] == 25.0
    assert abs(conc["integral_lambda"] - integral) < 1e-12
    assert abs(conc["integral_rho"] - (1.0 - 0.75) * conc["integral_lambda"]) < 1e-12
    assert abs(conc["rate_reconstructed"] - 0.75) < 1e-12
    expected_w_lo = (target - 1.0 / 25.0) / (1.0 / 24.0 - 1.0 / 25.0)
    assert abs(conc["w_lo"] - expected_w_lo) < 1e-12
    assert abs(conc["w_lo"] + conc["w_hi"] - 1.0) < 1e-12
    assert 0.0 < conc["w_lo"] < 1.0 and 0.0 < conc["w_hi"] < 1.0
    with pytest.raises(ValueError):
        de.concentrated_check_distribution(1.0, {2: 1.0})      # (1-rate) <= 0
    with pytest.raises(ValueError):
        de.concentrated_check_distribution(0.5, {2: 1000.0})    # dc < 2


def test_reconstructed_rate_exact():
    """The concentrated check distribution solves the edge-perspective rate
    equation exactly: |reconstructed_rate(lam, rho) - rate| <= 1e-12 for the
    reproduction config and additional rate/lambda configs; an integer dc
    degenerates to a regular check degree."""
    configs = [(0.75, de.REPRODUCTION_LAMBDA_DEGREES),
               (0.5, {2: 0.5, 3: 0.5}),
               (0.9, {2: 0.3, 4: 0.7}),
               (0.5, {3: 1.0}),
               (0.6, {2: 0.4, 4: 0.6})]
    for rate, lam in configs:
        conc = de.concentrated_check_distribution(rate, lam)
        rho = _rho_from_concentrated(conc)
        assert abs(de.reconstructed_rate(lam, rho) - rate) <= 1e-12
    # Regular integer case: rate 0.5, lambda {3:1.0} -> dc = 6 exactly -> rho
    # degenerates to the single regular check degree {6: 1.0}.
    conc = de.concentrated_check_distribution(0.5, {3: 1.0})
    assert abs(conc["dc_mean"] - 6.0) < 1e-12
    assert abs(conc["w_lo"] - 1.0) < 1e-12 and abs(conc["w_hi"] - 0.0) < 1e-12
    rho = _rho_from_concentrated(conc)
    assert rho == {6: 1.0}


# --------------------------------------------------------------------------- #
# 4. XOR convolution
# --------------------------------------------------------------------------- #


def test_xor_conv_pairwise_hand_computed():
    a = np.array([0.5, 0.25, 0.25, 0.0])
    b = np.array([0.2, 0.3, 0.4, 0.1])
    out = de.xor_conv_pairwise(a, b)
    expected = np.array([0.275, 0.225, 0.275, 0.225])
    assert np.max(np.abs(out - expected)) < 1e-12


def test_xor_conv_pairwise_vs_oracle_sparse():
    """xor_conv_pairwise(a, b) equals the oracle sparse check update on
    [delta, a, b] (target 0, syndrome 0, all-unity coefficients)."""
    rng = np.random.default_rng(2026080422)
    for q, field in ((4, GF2mField.create(4)), (8, GF2mField.create(8))):
        for _ in range(10):
            a = rng.random(q)
            a = a / a.sum()
            b = rng.random(q)
            b = b / b.sum()
            delta = np.zeros(q)
            delta[0] = 1.0
            oracle = ref.oracle_check_update_sparse(
                [delta, a, b], [1, 1, 1], 0, 0, field)
            assert oracle is not None
            assert np.max(np.abs(oracle - de.xor_conv_pairwise(a, b))) < 1e-12


def test_xor_conv_pairwise_batch_vs_scalar():
    rng = np.random.default_rng(2026080423)
    q = 4
    a = rng.random(q)
    a = a / a.sum()
    b = rng.random(q)
    b = b / b.sum()
    scalar = de.xor_conv_pairwise(a, b)
    batch = de.xor_conv_pairwise(np.stack([a, a, a]), np.stack([b, b, b]))
    assert batch.shape == (3, q)
    for row in range(3):
        assert np.max(np.abs(batch[row] - scalar)) < 1e-15
    mixed = de.xor_conv_pairwise(a, np.stack([b, b]))
    assert mixed.shape == (2, q)
    assert np.max(np.abs(mixed[1] - scalar)) < 1e-15


# --------------------------------------------------------------------------- #
# 5. determinism
# --------------------------------------------------------------------------- #


def test_run_mcde_determinism():
    lam = {2: 0.5, 3: 0.5}
    rho = _rho_from_concentrated(de.concentrated_check_distribution(0.5, lam))
    first = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080420)
    second = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080420)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert first["error_trace"] == second["error_trace"]
    assert first["iterations"] == second["iterations"]
    third = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080421)
    assert third["entropy_trace"] != first["entropy_trace"]


# --------------------------------------------------------------------------- #
# 6. frozen golden regressions
# --------------------------------------------------------------------------- #

# Frozen golden trace (re-recorded 2026-08-04 under the V8-60 harmonic-exact
# weights; the old values were recorded under the mean-matched weights):
# q=4, lambda_edge {2:0.5, 3:0.5}, rho concentrated rate 0.5 -> now
# {4: 1/6, 5: 5/6}, p=0.1, n_samples=500, max_iter=60, seed=2026080420.
GOLDEN_Q4_ENTROPY = [
    0.698571562538453, 0.5597973046435794, 0.4930898228331547, 0.37596334306471363,
    0.37315413406634296, 0.2719669644956375, 0.2387994115627575, 0.16935930406775554,
    0.09542797737694468, 0.09534260320823164, 0.06403291549174793, 0.029173260274635696,
    0.011038225475624528, 0.0037311917428284784, 0.0012215686847508326, 0.002458954162537628,
    0.0005787596585212564, 0.0009149393728254126, 0.0003664378771406588,
    9.303749984184997e-05, 0.00020142558556804517, 8.401352190378647e-05,
    2.8404151021834667e-05, 0.00021108078343297826, 8.859145402432656e-06,
    6.075978902696957e-07, 7.433634421421474e-08, 3.430247470731363e-07,
    1.8002794367959427e-08, 1.2948368869426728e-07, 4.5340183998279695e-07,
    5.0139789697000734e-08, 1.4549336124047101e-08,
]
GOLDEN_Q4_ERROR = [
    0.066, 0.048, 0.018, 0.03, 0.016, 0.006, 0.004, 0.006, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]
GOLDEN_Q4_CONVERGED = True
GOLDEN_Q4_ITERATIONS = 33

# Frozen golden trace (recorded once; regenerating requires the recorded seed
# 2026080421): q=8, lambda_edge {3:1.0}, rho concentrated rate 0.5 (degenerates
# to regular degree 6), p=0.05, n_samples=500, max_iter=60.
GOLDEN_Q8_ENTROPY = [
    0.46390582768518746, 0.24485433741020604, 0.043019539185817114,
    0.00013426917927675524, 4.391579205435829e-11, 5.427149747669045e-23,
    3.460710902649787e-50, 4.145326563536252e-103, 1.0375836060095772e-210,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]
GOLDEN_Q8_ERROR = [
    0.03, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]
GOLDEN_Q8_CONVERGED = True
GOLDEN_Q8_ITERATIONS = 23


def _q4_config():
    lam = {2: 0.5, 3: 0.5}
    rho = _rho_from_concentrated(de.concentrated_check_distribution(0.5, lam))
    return lam, rho


def test_golden_q4_canonical_and_old_r2_regressions():
    """(a) canonical (fresh+sampled) run equals the frozen golden trace
    exactly; (b) `_channel_mode='omitted'` differs; (c)
    `_degree_mode='fixed_max'` differs; (d) the canonical final iteration
    satisfies the frozen converged/iterations status."""
    lam, rho = _q4_config()
    canonical = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080420)
    assert canonical["entropy_trace"] == GOLDEN_Q4_ENTROPY
    assert canonical["error_trace"] == GOLDEN_Q4_ERROR
    assert canonical["converged"] is GOLDEN_Q4_CONVERGED
    assert canonical["iterations"] == GOLDEN_Q4_ITERATIONS
    omitted = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080420,
                          _channel_mode="omitted")
    assert omitted["entropy_trace"] != GOLDEN_Q4_ENTROPY
    fixed = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026080420,
                        _degree_mode="fixed_max")
    assert fixed["entropy_trace"] != GOLDEN_Q4_ENTROPY
    # (d) status check on the frozen final values.
    assert canonical["entropy_trace"][-1] < de.REPRODUCTION_ENTROPY_TOL
    assert canonical["error_trace"][-1] == 0.0


def test_golden_q8():
    """Frozen q=8 golden trace: lambda {3:1.0}, rho concentrated rate 0.5
    (regular degree 6), p=0.05, n_samples=500, max_iter=60, seed=2026080421."""
    lam = {3: 1.0}
    rho = _rho_from_concentrated(de.concentrated_check_distribution(0.5, lam))
    assert rho == {6: 1.0}
    run = de.run_mcde(8, lam, rho, 0.05, n_samples=500, max_iter=60, seed=2026080421)
    assert run["entropy_trace"] == GOLDEN_Q8_ENTROPY
    assert run["error_trace"] == GOLDEN_Q8_ERROR
    assert run["converged"] is GOLDEN_Q8_CONVERGED
    assert run["iterations"] == GOLDEN_Q8_ITERATIONS


# --------------------------------------------------------------------------- #
# 7. fail-closed boundaries
# --------------------------------------------------------------------------- #


def test_fail_closed_numerical_and_parameter_boundaries():
    lam, rho = _q4_config()
    rng = np.random.default_rng(7)
    good = np.full((8, 4), 0.25)
    rho_ok = {int(k): float(v) for k, v in rho.items()}
    for bad in (np.full((8, 4), np.nan), np.full((8, 4), np.inf),
                np.full((8, 4), -0.25), np.zeros((8, 4))):
        with pytest.raises(ValueError):
            de.variable_update_mcde(good, [2, 3], [0.5, 0.5], bad, rng, 4)
        with pytest.raises(ValueError):
            de.check_update_mcde(bad, rho_ok.keys(), list(rho_ok.values()), rng, 4)
        with pytest.raises(ValueError):
            de.belief_update_mcde(bad, [2, 3], [0.5, 0.5], good, rng, 4)
        with pytest.raises(ValueError):
            de.entropy_base_q(bad)
    with pytest.raises(ValueError):
        de.xor_conv_pairwise(np.full(4, np.nan), good[0])
    with pytest.raises(ValueError):
        de.qsc_channel_message(4, 0.0)
    with pytest.raises(ValueError):
        de.qsc_channel_message(4, 0.75)     # (q-1)/q boundary excluded
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.0, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.1, n_samples=99, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=2001, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(3, lam, rho, 0.1, n_samples=500, max_iter=60, seed=1)   # q not power of two
    with pytest.raises(ValueError):
        de.run_mcde(4, {}, rho, 0.1, n_samples=500, max_iter=60, seed=1)   # empty lambda
    with pytest.raises(ValueError):
        de.run_mcde(4, {2: math.nan}, rho, 0.1, n_samples=500, max_iter=60, seed=1)


# --------------------------------------------------------------------------- #
# 8. threshold search sanity
# --------------------------------------------------------------------------- #


def test_threshold_binary_search_sanity():
    """On the small q=4 config: 0 < threshold_proxy < 0.49, the p_lo probe
    converges, and the probe list is a deterministic binary search."""
    lam, rho = _q4_config()
    result = de.threshold_binary_search(4, lam, rho, n_samples=500, max_iter=60,
                                        seed=2026080420, p_lo=0.01, p_hi=0.49, p_tol=0.01)
    assert 0.0 < result["threshold_proxy"] < 0.49
    assert len(result["probes"]) >= 2
    at_lo = de.run_mcde(4, lam, rho, 0.01, n_samples=500, max_iter=60, seed=2026080420)
    assert at_lo["converged"] is True
    first = result["probes"][0]["p"]
    assert abs(first - (0.01 + 0.49) / 2.0) < 1e-12


# --------------------------------------------------------------------------- #
# T2: frozen reproduction trace (read-only; the single run happens via the
# V8-40.3 python -c command, never inside pytest)
# --------------------------------------------------------------------------- #


def _read_evidence(name: str) -> dict:
    with open(f"{EVIDENCE}/{name}", encoding="utf-8") as handle:
        return json.load(handle)


def test_reproduction_muller2024_table1_q4_rate075():
    """Read-only verification of the single frozen corrective reproduction run
    recorded in evidence/v8_reproduction_trace_corrected.json (the run itself
    is V8-60.6, executed once via python -c with the corrected frozen
    constants; this test never re-runs the search)."""
    trace = _read_evidence("v8_reproduction_trace_corrected.json")
    assert trace["schema"] == "v8_reproduction_trace_corrected_v1"
    frozen = trace["frozen_parameters"]
    assert frozen["q"] == de.REPRODUCTION_Q
    assert frozen["rate"] == de.REPRODUCTION_RATE
    assert frozen["n_samples"] == de.REPRODUCTION_N_SAMPLES
    assert frozen["max_iter"] == de.REPRODUCTION_MAX_ITER
    assert frozen["seed"] == de.REPRODUCTION_SEED
    assert frozen["p_lo"] == de.REPRODUCTION_P_LO
    assert frozen["p_hi"] == de.REPRODUCTION_P_HI
    assert frozen["p_tol"] == de.REPRODUCTION_P_TOL
    assert frozen["entropy_tol"] == de.REPRODUCTION_ENTROPY_TOL
    assert frozen["streak"] == de.REPRODUCTION_STREAK
    assert frozen["det_published"] == de.REPRODUCTION_DET_PUBLISHED
    assert frozen["tolerance"] == de.REPRODUCTION_TOL
    proxy = trace["threshold_proxy"]
    delta = trace["delta_vs_published"]
    assert abs(delta - abs(proxy - de.REPRODUCTION_DET_PUBLISHED)) < 1e-12
    expected_verdict = "PASS" if delta <= de.REPRODUCTION_TOL else "FAIL"
    assert trace["verdict"] == expected_verdict
    assert len(trace["probes"]) >= 1
    # deterministic binary search from the frozen endpoints
    lo, hi = de.REPRODUCTION_P_LO, de.REPRODUCTION_P_HI
    for probe in trace["probes"]:
        assert abs(probe["p"] - (lo + hi) / 2.0) < 1e-12
        if probe["converged"]:
            lo = probe["p"]
        else:
            hi = probe["p"]
    assert abs(proxy - (lo + hi) / 2.0) < 1e-9


def test_v8_precorrection_trace_preserved_readonly():
    """The original evidence/v8_reproduction_trace.json is preserved
    byte-identical: the sidecar annotation records its original file name and
    SHA256, and the on-disk bytes still match the recorded hash; the corrected
    trace exists and is a different path."""
    annotation = _read_evidence("v8_reproduction_trace_precorrection_annotation.json")
    assert annotation["schema"] == "v8_reproduction_trace_precorrection_annotation_v1"
    assert annotation["original_file"] == "v8_reproduction_trace.json"
    assert annotation["recorded_before_correction"] is True
    recorded = annotation["original_sha256"].lower()
    with open(f"{EVIDENCE}/v8_reproduction_trace.json", "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    assert digest == recorded, "v8_reproduction_trace.json bytes drifted from recorded hash"
    corrected_path = os.path.abspath(f"{EVIDENCE}/v8_reproduction_trace_corrected.json")
    assert os.path.exists(corrected_path)
    assert corrected_path != os.path.abspath(f"{EVIDENCE}/v8_reproduction_trace.json")


def test_v8_source_manifest_readonly():
    """Read-only evidence verification: every file listed in
    evidence/v8_source_manifest.json matches its on-disk SHA256 (the manifest
    is written before any tier runs)."""
    manifest = _read_evidence("v8_source_manifest.json")
    assert manifest["schema"] == "v8_source_manifest_v1"
    assert manifest["created_before_tests"] is True
    for relative_path, sha256 in manifest["files"].items():
        with open(relative_path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        assert digest == sha256, f"{relative_path} hash mismatch"


def test_v8_no_production_runner_bound():
    """No production runner is bound: importing the three V8 modules must not
    bind any V1-V7 module object, and no forbidden import line appears in
    their source."""
    import types
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v8_error_domain as m_ed
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v8_reference as m_ref
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v8_mcde as m_de
    forbidden_substrings = ("nonbinary_qspa", "nonbinary_v6", "nonbinary_v7")
    for module in (m_ed, m_ref, m_de):
        for value in vars(module).values():
            if isinstance(value, types.ModuleType):
                assert not any(token in value.__name__ for token in forbidden_substrings), (
                    module.__name__, value.__name__)
    # The reference module's source must not contain the frozen oracle tokens
    # (case-sensitive, exactly as assert_oracle_independent scans).
    with open(V8_MODULE_PATHS["reference"], encoding="utf-8") as handle:
        ref_source = handle.read()
    for token in ("fwht", "nonbinary_qspa", "nonbinary_v7", "nonbinary_v6",
                  "decode_", "production"):
        assert token not in ref_source, f"forbidden token {token!r} in reference source"
    # No forbidden import lines in any V8 module.
    import re
    forbidden_import = re.compile(
        r"^\s*(from|import)\s+.*(nonbinary_v[1-7]|nonbinary_qspa|"
        r"decode_nbldpc|production_runner|numpy\s*\.\s*fft)", re.MULTILINE)
    for name, path in V8_MODULE_PATHS.items():
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert not forbidden_import.search(source), f"{name}: forbidden import line"
