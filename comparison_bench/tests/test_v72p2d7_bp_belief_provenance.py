"""D7/BP belief-provenance interface tests (BP-01..BP-06, PV-01..PV-14).

Tiny in-memory synthetic fixtures only. No real/raw data, no Model-F, no
CAL/VAL, no formal root or evidence-artifact reads, no production execution
beyond explicit tiny synthetic decoder unit calls, no --phase/R1d/G1/G2.

The acceptance matrix PV-01..PV-14 is authoritative in
``openspec/changes/v72p2d7-layer-interface-belief-provenance/proposal.md``.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
FORMAL = SRC / "comparison_bench" / "formal_ir"
METHODS = SRC / "comparison_bench" / "methods"
SCRIPTS = ROOT / "scripts"

from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v35_algorithm_development as v35,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v72p2d5_gf32_rate_mother as d5,
)
from comparison_bench.src.comparison_bench.formal_ir.v72p2d7_gf32_decoder_certification import (  # noqa: E402
    row_layered_reference,
)

_SPEC = importlib.util.spec_from_file_location(
    "bp_test_v72p2d3", str(FORMAL / "v72p2d3_gf32_contrast.py"))
assert _SPEC is not None and _SPEC.loader is not None
d3 = importlib.util.module_from_spec(_SPEC)
sys.modules["bp_test_v72p2d3"] = d3
_SPEC.loader.exec_module(d3)

OLD_FIELDS = ("x_hat", "syndrome_ok", "iterations", "runtime_s", "status",
              "final_beliefs")

# Tiny single-check fixtures (in-memory only).
_TINY_H = np.array([[1, 1]], dtype=np.uint8)


def _peaked_prior(peaks, mass=0.9):
    row = np.full(32, (1.0 - mass) / 31.0)
    p = np.tile(row, (len(peaks), 1))
    for i, k in enumerate(peaks):
        p[i, k] = mass
    return p / p.sum(axis=1, keepdims=True)


# Cold, MAP already satisfies the syndrome -> iteration-0 early exit.
IT0_PRIOR = _peaked_prior([0, 0])
IT0_SYN = np.array([0], dtype=np.uint8)
# Cold, MAP initially unsatisfied, converges after exactly one sweep.
SWEEP_PRIOR = _peaked_prior([0, 24])
SWEEP_SYN = np.array([1], dtype=np.uint8)


def _it0_result():
    return v35.decode_row_layered_fftqspa(
        _TINY_H, IT0_PRIOR, IT0_SYN, max_iter=5)


def _sweep_result(max_iter=1):
    return v35.decode_row_layered_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=max_iter)


# ---------------------------------------------------------------------------
# PV-01..PV-05: producer token mapping and additive/numerical equivalence
# ---------------------------------------------------------------------------
def test_pv_01_cold_it0_early_exit_is_prior_only():
    res = _it0_result()
    assert res.iterations == 0
    assert res.syndrome_ok is True
    assert res.status == "converged_exact"
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_PRIOR_ONLY
    # The returned beliefs are the floored/renormalized input log-prior.
    clean = np.maximum(IT0_PRIOR, 1e-15)
    clean = clean / clean.sum(axis=1, keepdims=True)
    assert np.array_equal(res.final_beliefs, np.log(clean))


def test_pv_02_cold_after_one_completed_sweep_is_check_updated():
    res = _sweep_result(max_iter=1)
    assert res.iterations == 1
    assert res.syndrome_ok is True
    assert res.status == "converged_exact"
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    # A completed sweep changed the beliefs away from the untouched log-prior.
    clean = np.maximum(SWEEP_PRIOR, 1e-15)
    clean = clean / clean.sum(axis=1, keepdims=True)
    assert not np.array_equal(res.final_beliefs, np.log(clean))


def test_pv_03_flooding_first_return_is_check_updated():
    res = v35.decode_flooding_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=1)
    assert res.iterations >= 1
    assert res.belief_provenance == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    assert res.belief_provenance != v35.BELIEF_PROVENANCE_PRIOR_ONLY


def test_pv_04_warm_start_is_unspecified_never_inferred_from_iterations():
    warm = np.log(IT0_PRIOR)
    warm_it0 = v35.decode_row_layered_fftqspa(
        _TINY_H, IT0_PRIOR, IT0_SYN, max_iter=5, warm_beliefs=warm)
    assert warm_it0.iterations == 0  # iteration-0 shape ...
    assert warm_it0.belief_provenance == \
        v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED  # ... never PRIOR_ONLY
    warm_it1 = v35.decode_row_layered_fftqspa(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, max_iter=1, warm_beliefs=warm)
    assert warm_it1.iterations >= 1  # iterations > 0 ...
    assert warm_it1.belief_provenance == \
        v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED  # ... never CHECK_UPDATED


def test_pv_05_additive_field_and_numerical_equivalence():
    fields = dataclasses.fields(v35.DecoderResult)
    names = [f.name for f in fields]
    # Legacy first six positional fields unchanged; belief_provenance stays
    # in place; the additive D7-G extrinsic fields follow it as optional
    # defaulted fields (accepted additive API).
    assert names[:6] == list(OLD_FIELDS)
    assert names[6] == "belief_provenance"
    assert names[6:] == ["belief_provenance", "extrinsic_log_beliefs",
                         "extrinsic_provenance"]
    assert all(f.default is None for f in fields[6:])
    # Existing positional construction stays compatible.
    legacy = v35.DecoderResult(
        np.zeros(2, dtype=np.uint8), True, 0, 0.0, "legacy", np.zeros((2, 32)))
    assert legacy.belief_provenance is None
    assert legacy.extrinsic_log_beliefs is None
    assert legacy.extrinsic_provenance is None
    # Iteration-0 numeric identity against the documented floor/renorm path.
    res0 = _it0_result()
    clean = np.maximum(IT0_PRIOR, 1e-15)
    clean = clean / clean.sum(axis=1, keepdims=True)
    assert np.array_equal(res0.final_beliefs, np.log(clean))
    assert res0.x_hat.tolist() == [0, 0]
    # After one sweep, hard-decision fields and per-sweep beliefs match the
    # independent D7-A reference recurrence (probability max-abs <= 1e-12).
    sweeps, ref_iters, ref_x = row_layered_reference(
        _TINY_H, SWEEP_PRIOR, SWEEP_SYN, 1)
    res1 = _sweep_result(max_iter=1)
    assert ref_iters == res1.iterations == 1
    assert np.array_equal(res1.x_hat, ref_x)
    assert res1.status == "converged_exact" and res1.syndrome_ok is True
    got = d5._softmax_rows(res1.final_beliefs)
    ref = d5._softmax_rows(sweeps[0])
    assert float(np.max(np.abs(got - ref))) <= 1e-12


# ---------------------------------------------------------------------------
# D5 consumer fixtures (tiny in-memory only)
# ---------------------------------------------------------------------------
_H1 = np.array([[1, 1]], dtype=np.int64)
_H2 = np.array([[1, 2]], dtype=np.int64)
_P1 = np.full((32, 2), 1.0 / 32)
_P1[3, 0] = 0.6
_P1[:, 0] /= _P1[:, 0].sum()
_P1[9, 1] = 0.6
_P1[:, 1] /= _P1[:, 1].sum()
_RNG = np.random.default_rng(20260911)
_P2 = _RNG.random((32, 2, 32)) + 0.1
_P2 = _P2 / _P2.sum(axis=2, keepdims=True)
_BLOCK = {"bob": np.array([0, 1]), "u1": np.array([3, 9]),
          "u2": np.array([4, 7])}
_LOG_BEL = np.log(np.array([[0.8] + [0.2 / 31] * 31,
                            [0.2 / 31] * 31 + [0.8]]))


def _res_dict(provenance, beliefs=True, kind="l1"):
    out = {"x_hat": np.array([3, 9]) if kind == "l1" else np.array([4, 7]),
           "syndrome_ok": True, "iterations": 1}
    if beliefs:
        out["final_beliefs"] = _LOG_BEL if kind == "l1" else np.zeros((2, 32))
    if provenance is not None:
        out["belief_provenance"] = provenance
    return out


def _spy_mixer(monkeypatch):
    calls = {"mixer": 0, "l2": 0}
    real_mix = d5.app_fed_l2_prior

    def spy_mix(*args, **kwargs):
        calls["mixer"] += 1
        return real_mix(*args, **kwargs)

    monkeypatch.setattr(d5, "app_fed_l2_prior", spy_mix)

    def prior_only_l1(h, prior, syn, layer=None):
        return _res_dict("PRIOR_ONLY", kind="l1")

    return calls, prior_only_l1


def test_pv_06_prior_only_refused_before_mixer_and_l2(monkeypatch):
    calls, fake = _spy_mixer(monkeypatch)
    with pytest.raises(RuntimeError) as exc:
        d5._run_layered_block(fake, _H1, _H2, _P1, _P2, _BLOCK, False)
    assert type(exc.value).__name__ == "UnconditionedBeliefProvenanceError"
    assert "CHECK_UPDATED" in str(exc.value)
    assert calls == {"mixer": 0, "l2": 0}


def test_pv_06b_real_producer_prior_only_result_is_refused(monkeypatch):
    calls, _ = _spy_mixer(monkeypatch)
    real_it0 = _it0_result()
    fake = lambda h, prior, syn, layer=None: real_it0
    with pytest.raises(RuntimeError) as exc:
        d5._run_layered_block(fake, _H1, _H2, _P1, _P2, _BLOCK, False)
    assert type(exc.value).__name__ == "UnconditionedBeliefProvenanceError"
    assert real_it0.belief_provenance == v35.BELIEF_PROVENANCE_PRIOR_ONLY
    assert calls == {"mixer": 0, "l2": 0}


@pytest.mark.parametrize("value", [None, "BOGUS", "bogus", "", 0])
def test_pv_07_missing_none_unknown_provenance_fails_closed(
        monkeypatch, value):
    calls, _ = _spy_mixer(monkeypatch)
    if value is None:
        # Dict without the key at all (legacy/absent).
        def fake(h, prior, syn, layer=None):
            return _res_dict(None, kind="l1")
    else:
        # Key present with None/unknown/empty tokens.
        def fake(h, prior, syn, layer=None):
            return _res_dict(value, kind="l1")
    with pytest.raises(RuntimeError) as exc:
        d5._run_layered_block(fake, _H1, _H2, _P1, _P2, _BLOCK, False)
    assert type(exc.value).__name__ == "UnconditionedBeliefProvenanceError"
    assert calls == {"mixer": 0, "l2": 0}


def test_pv_07b_legacy_namespace_fake_fails_closed(monkeypatch):
    calls, _ = _spy_mixer(monkeypatch)
    legacy = SimpleNamespace(x_hat=np.array([3, 9]), syndrome_ok=True,
                             iterations=1, final_beliefs=_LOG_BEL)
    with pytest.raises(RuntimeError) as exc:
        d5._run_layered_block(
            lambda h, prior, syn, layer=None: legacy,
            _H1, _H2, _P1, _P2, _BLOCK, False)
    assert type(exc.value).__name__ == "UnconditionedBeliefProvenanceError"
    assert calls == {"mixer": 0, "l2": 0}


def test_pv_08_prior_only_q_never_reaches_l2_mixer_or_decoder(monkeypatch):
    seen_priors = []
    real_mix = d5.app_fed_l2_prior

    def spy_mix(p2, bob, q):
        seen_priors.append(np.asarray(q).copy())
        return real_mix(p2, bob, q)

    monkeypatch.setattr(d5, "app_fed_l2_prior", spy_mix)
    fake = lambda h, prior, syn, layer=None: _res_dict(
        "PRIOR_ONLY", beliefs=False, kind="l1")
    with pytest.raises(RuntimeError):
        d5._run_layered_block(fake, _H1, _H2, _P1, _P2, _BLOCK, False)
    assert seen_priors == []


def test_pv_09_check_updated_pass_through_reproduces_q_at_p():
    captured = {"priors": []}

    def fake_decode(h, prior, syn, layer=None):
        captured["priors"].append(np.asarray(prior))
        if len(captured["priors"]) == 1:
            return _res_dict("CHECK_UPDATED", kind="l1")
        return _res_dict("CHECK_UPDATED", beliefs=False, kind="l2")

    out = d5._run_layered_block(fake_decode, _H1, _H2, _P1, _P2, _BLOCK, False)
    assert out["app_l1_exact"] and out["finite"]
    q = d5._softmax_rows(_LOG_BEL)
    expected_l2 = d5.app_fed_l2_prior(_P2, _BLOCK["bob"], q)
    assert np.allclose(captured["priors"][1], expected_l2, atol=1e-12)


# ---------------------------------------------------------------------------
# PV-10: diagnostic labeling separation (no D7-B rerun)
# ---------------------------------------------------------------------------
def test_pv_10_it0_belief_is_labeled_current_belief_not_posterior():
    assert v35.PRIOR_ONLY_CURRENT_BELIEF not in v35.BELIEF_PROVENANCE_TOKENS
    assert v35.belief_diagnostic_label(
        v35.BELIEF_PROVENANCE_PRIOR_ONLY) == v35.PRIOR_ONLY_CURRENT_BELIEF
    assert v35.belief_diagnostic_label(
        v35.BELIEF_PROVENANCE_CHECK_UPDATED) == \
        v35.BELIEF_PROVENANCE_CHECK_UPDATED
    res = _it0_result()
    # Hard-decision success is a separate field; it never upgrades the label.
    assert res.syndrome_ok is True and res.iterations == 0
    label = v35.belief_diagnostic_label(res.belief_provenance)
    assert label == v35.PRIOR_ONLY_CURRENT_BELIEF
    assert label not in ("CHECK_UPDATED", "posterior", "APP")


# ---------------------------------------------------------------------------
# PV-11: plumbing through D5 adapters, _decode_block and v72p2d3
# ---------------------------------------------------------------------------
def test_pv_11_decode_block_carries_provenance():
    exact, syn_ok, it, finite, bel, prov = d5._decode_block(
        lambda h, prior, syn, layer=None: _res_dict("CHECK_UPDATED"),
        _H1, _P1, _BLOCK["u1"])
    assert (exact, syn_ok, it, finite) == (True, True, 1, True)
    assert prov == "CHECK_UPDATED"
    assert np.shape(bel) == (2, 32)


def test_pv_11_adapters_propagate_provenance(monkeypatch):
    class _FakeDecoder:
        belief_provenance = "CHECK_UPDATED"
        x_hat = np.array([0, 1], dtype=np.uint8)
        syndrome_ok = True
        iterations = 1
        final_beliefs = np.zeros((2, 32), dtype=np.float64)

        def __call__(self, *args, **kwargs):
            return self

    monkeypatch.setattr(d5, "_load_g0_decoder", lambda: _FakeDecoder())
    out = d5.historical_g0_decoder(_H1, _P1, IT0_SYN)
    assert out["belief_provenance"] == "CHECK_UPDATED"
    assert set(("x_hat", "syndrome_ok", "iterations",
                "final_beliefs")).issubset(out)
    bound = d5.bind_historical_decoder()
    out2 = bound(_H1, _P1, IT0_SYN)
    assert out2["belief_provenance"] == "CHECK_UPDATED"
    # _bound_hist is a closure inside run_g0_synthetic: assert the literal
    # passthrough key exists in its returned dict.
    src = (FORMAL / "v72p2d5_gf32_rate_mother.py").read_text(encoding="utf-8")
    seg = src[src.index("def _bound_hist"):src.index("def _bound_hist") + 900]
    assert '"belief_provenance"' in seg


def test_pv_11_v72p2d3_dict_path_carries_provenance():
    prior = np.log(np.full((2, 32), 1.0 / 32.0))
    syn = np.zeros(2, dtype=np.uint8)
    fake = lambda h_mat, prior_p, target: {
        "x_hat": np.zeros(2, dtype=np.int64), "iterations_used": 1,
        "syndrome_ok": False, "final_beliefs": np.log(prior_p),
        "belief_provenance": "CHECK_UPDATED"}
    out = d3.run_g_layer(prior, syn, np.eye(2, dtype=np.uint8),
                         max_iter=2, decode_fn=fake)
    assert out["belief_provenance"] == "CHECK_UPDATED"
    assert out["belief_label"] == "CHECK_UPDATED"
    assert out["final_beliefs"].shape == prior.shape
    # Missing-beliefs fallback is the log-prior: labeled PRIOR_ONLY.
    fake_none = lambda h_mat, prior_p, target: {
        "x_hat": np.zeros(2, dtype=np.int64), "iterations_used": 0,
        "syndrome_ok": False, "final_beliefs": None}
    out2 = d3.run_g_layer(prior, syn, np.eye(2, dtype=np.uint8),
                          max_iter=2, decode_fn=fake_none)
    assert out2["belief_provenance"] == "PRIOR_ONLY"
    assert out2["belief_label"] == "PRIOR_ONLY_CURRENT_BELIEF"


# ---------------------------------------------------------------------------
# PV-12/PV-13: additive no-retroactivity, hard-decision-only consumers
# ---------------------------------------------------------------------------
def test_pv_12_legacy_schema_and_no_real_root_reads():
    fields = dataclasses.fields(v35.DecoderResult)
    assert [f.name for f in fields[:6]] == list(OLD_FIELDS)
    legacy = SimpleNamespace(x_hat=np.array([0, 1], dtype=np.uint8),
                             syndrome_ok=False, iterations=2,
                             final_beliefs=np.zeros((2, 32)))
    exact, syn_ok, it, finite, bel, prov = d5._decode_block(
        lambda h, prior, syn, layer=None: legacy,
        _H1, _P1, _BLOCK["u1"])
    assert (exact, syn_ok, it, finite) == (False, False, 2, True)
    assert prov is None and np.shape(bel) == (2, 32)
    # This test module must never bind a real root/artifact.
    src = Path(__file__).read_text(encoding="utf-8")
    for needle in ("work" + "space/", "outputs_" + "comparison",
                   "MODEL_" + "F_ROOT"):
        assert needle not in src


def test_pv_13_hard_decision_only_consumers_ignored_provenance():
    def hard_decision_only(res):
        return (np.asarray(res.x_hat).copy(), bool(res.syndrome_ok),
                int(res.iterations))

    newest = _sweep_result(max_iter=1)
    legacy = SimpleNamespace(x_hat=newest.x_hat.copy(),
                             syndrome_ok=newest.syndrome_ok,
                             iterations=newest.iterations)
    got_new = hard_decision_only(newest)
    got_legacy = hard_decision_only(legacy)
    assert np.array_equal(got_new[0], got_legacy[0])
    assert got_new[1:] == got_legacy[1:]
    assert newest.belief_provenance == "CHECK_UPDATED"


# ---------------------------------------------------------------------------
# PV-14: D7-C oracle import-graph independence
# ---------------------------------------------------------------------------
def test_pv_14_interface_and_d7c_oracle_share_no_dependency():
    oracle = (FORMAL / "v72p2d7_gf32_bidirectional_oracle.py").read_text(
        encoding="utf-8")
    assert "belief_provenance" not in oracle
    assert "require_check_updated_provenance" not in oracle
    assert "belief_diagnostic_label" not in oracle
    assert "UnconditionedBeliefProvenanceError" not in oracle
    interface_files = [
        FORMAL / "v35_algorithm_development.py",
        FORMAL / "v72p2d5_gf32_rate_mother.py",
        FORMAL / "v72p2d3_gf32_contrast.py",
        FORMAL / "v45_l1_app_soft_transfer.py",
        FORMAL / "v46_verification_semantics.py",
        FORMAL / "v47_h1_redundancy_compression.py",
        FORMAL / "v48_heldout_confirm.py",
        FORMAL / "v50_l2_structure_factorial.py",
        FORMAL / "v51_lane_c_label_nbace.py",
        FORMAL / "v52_rate_adaptive_l2_rescue.py",
        FORMAL / "v53_rate_adaptive_l2_heldout_confirm.py",
        FORMAL / "v54_two_stage_incremental_l2_rescue.py",
        FORMAL / "v55_two_stage_rescue_independent_test.py",
        METHODS / "nbldpc_shell_adapter.py",
        SCRIPTS / "execute_v64_fresh_verify.py",
    ]
    for path in interface_files:
        src = path.read_text(encoding="utf-8")
        assert "v72p2d7_gf32_bidirectional_oracle" not in src, path.name


# ---------------------------------------------------------------------------
# Static inventory: accepted final_beliefs -> cross-layer mixer paths guarded
# ---------------------------------------------------------------------------
INVENTORY_MIXER_PATHS = (
    (FORMAL / "v45_l1_app_soft_transfer.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v46_verification_semantics.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v47_h1_redundancy_compression.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v48_heldout_confirm.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v50_l2_structure_factorial.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v51_lane_c_label_nbace.py",
     r"q = softmax_beliefs\(res\.final_beliefs\)"),
    (FORMAL / "v52_rate_adaptive_l2_rescue.py",
     r"q = softmax_beliefs\(_res_l1\.final_beliefs\)"),
    (FORMAL / "v53_rate_adaptive_l2_heldout_confirm.py",
     r"q = softmax_beliefs\(_res_l1\.final_beliefs\)"),
    (FORMAL / "v54_two_stage_incremental_l2_rescue.py",
     r"q = softmax_beliefs\(_res_l1\.final_beliefs\)"),
    (FORMAL / "v55_two_stage_rescue_independent_test.py",
     r"q = softmax_beliefs\(_res_l1\.final_beliefs\)"),
    (FORMAL / "v72p2d3_gf32_contrast.py",
     r"q = softmax_beliefs_history\("),
    (METHODS / "nbldpc_shell_adapter.py",
     r"softmax_beliefs\(res_l1\.final_beliefs\)"),
    (SCRIPTS / "execute_v64_fresh_verify.py",
     r"softmax_beliefs\(res_l1\.final_beliefs\)"),
)


def test_static_inventory_cross_layer_paths_carry_guard():
    for path, mixer_re in INVENTORY_MIXER_PATHS:
        lines = path.read_text(encoding="utf-8").splitlines()
        idxs = [i for i, line in enumerate(lines) if re.search(mixer_re, line)]
        assert len(idxs) == 1, (path.name, idxs)
        window = "\n".join(lines[max(0, idxs[0] - 10):idxs[0]])
        assert "require_check_updated_provenance" in window, (
            path.name, idxs[0] + 1)
    # D5 production layered mixer: guard inside _run_layered_block.
    d5_lines = (FORMAL / "v72p2d5_gf32_rate_mother.py").read_text(
        encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(d5_lines)
                 if line.startswith("def _run_layered_block"))
    mixer = next(i for i in range(start, len(d5_lines))
                 if "app_fed_l2_prior(" in d5_lines[i])
    assert "require_check_updated_provenance" in "\n".join(
        d5_lines[start:mixer])
