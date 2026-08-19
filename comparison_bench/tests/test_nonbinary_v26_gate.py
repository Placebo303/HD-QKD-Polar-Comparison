"""V26 channel-informed multilevel DE gate — focused tests.

Covers: GF permutation table, posterior-population MC-DE mechanism (brute-force
check node, all-one degeneracy, seed replay), the M0 adapter semantic gate on
real V25 channel counts (skipped if data absent), and the M4 terminal-state
decision rule.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_channel as chn
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_mcde as de
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_gate as gate
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v26_verify as vfy
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v26_verify import (
    all_one_matches_v14,
    bruteforce_check_node,
    check_update_bruteforce_matches,
)

COUNTS = Path("comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_01")


def _has_counts() -> bool:
    try:
        return len(chn.load_channel_counts()) == 3
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# GF permutation table
# --------------------------------------------------------------------------- #

def test_gf_perm_table_domains():
    for q in (2, 32, 512):
        perm, nonzero = de.build_gf_perm_table(q)
        assert perm.shape == (q, q)
        assert set(nonzero.tolist()) == set(range(1, q))  # all nonzero coefficients


def test_gf_perm_identity_for_h1():
    # inverse(1)*y = y
    for q in (4, 32):
        perm, _ = de.build_gf_perm_table(q)
        assert np.all(perm[1] == np.arange(q))


# --------------------------------------------------------------------------- #
# MC-DE mechanism (self-contained)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("q,k", [(4, 2), (4, 3), (8, 2), (8, 3)])
def test_check_node_bruteforce(q, k):
    r = check_update_bruteforce_matches(q, k, seed=q * 100 + k)
    assert r["ok"], r


def test_all_one_matches_v14_high_q():
    for q in (32, 512):
        r = all_one_matches_v14(q, 3, seed=q + 50)
        assert r["ok"], r


def test_seed_replay_identical():
    # synthetic Gaussian-ish posterior over GF(32)
    q = 32
    def sampler(n, rng):
        rows = rng.dirichlet(np.ones(q), size=n)
        return rows
    lam = {2: 1.0}
    rho = {6: 0.5, 7: 0.5}
    r1 = de.run_mcde_posterior(q, lam, rho, channel_sampler=sampler,
                               n_samples=200, max_iter=6, seed=7,
                               entropy_tol_bits=0.01, streak=20)
    r2 = de.run_mcde_posterior(q, lam, rho, channel_sampler=sampler,
                               n_samples=200, max_iter=6, seed=7,
                               entropy_tol_bits=0.01, streak=20)
    assert r1["entropy_trace_bits"] == r2["entropy_trace_bits"]
    assert r1["converged"] == r2["converged"]


def test_target_rate_matches_frozen_table():
    # worst-H frozen rates at f=1.3 per architecture/layer
    cases = [("A01", "L1", 0.93988), ("A01", "L2", 0.45879),
             ("A02", "L1", 0.99333), ("A02", "L2", 0.79021)]
    for arch, lid, exp in cases:
        rate = gate.target_rate_for(arch, lid, 1.3)
        assert abs(rate - exp) < 5e-4, (arch, lid, rate)


# --------------------------------------------------------------------------- #
# M4 terminal-state decision (pure)
# --------------------------------------------------------------------------- #

def test_terminal_pass_target_f13_when_a02_confirms():
    m0 = {"ok": True}
    m1 = {"ok": True}
    # screen + confirm both fully pass A02 at f=1.3
    calls = {}
    for arch, lids, f, conv in [("A02", ("L1", "L2"), 1.3, True),
                                ("A01", ("L1", "L2"), 1.6, True)]:
        for lid in lids:
            for src in gate.SOURCES:
                for seed in gate.CONFIRM_SEEDS:
                    calls[f"{arch}|{lid}|{f}|{src}|{seed}"] = {"converged": conv}
    screen = {"calls": calls}
    confirm = {"calls": calls}
    g = gate.decide_terminal(screen, confirm, m0, m1)
    assert g["status"] == "pass_target_f13"
    assert g["best_passing_f"] == {"A01": 1.6, "A02": 1.3}


def test_terminal_blocked_when_m0_fails():
    g = gate.decide_terminal({}, None, {"ok": False}, {"ok": True})
    assert g["status"] == "implementation_blocked_layer_channel_semantics"
    g2 = gate.decide_terminal({}, None, {"ok": True}, {"ok": False})
    assert g2["status"] == "implementation_blocked_layer_channel_semantics"


def test_terminal_fixed_no_conv_when_nothing_passes():
    calls = {f"A01|L1|{f}|{src}|{seed}": {"converged": False}
             for f in gate.SCREEN_F for src in gate.SOURCES for seed in gate.SCREEN_SEEDS}
    screen = {"calls": calls}
    g = gate.decide_terminal(screen, None, {"ok": True}, {"ok": True})
    assert g["status"] == "fixed_ensemble_no_convergence"


# --------------------------------------------------------------------------- #
# M0 adapter semantic gate (needs real V25 counts; skip if absent)
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not _has_counts(), reason="V25 channel_counts.npz not present")
def test_m0_adapter_gate_passes():
    counts = chn.load_channel_counts()
    adapters = {}
    for arch, fact in {"A01": "F01", "A02": "F03"}.items():
        adapters[arch] = {src: chn.build_adapter(counts, fact_id=fact, source=src)
                          for src in gate.SOURCES}
    m0 = gate.run_m0_gate(adapters, counts)
    assert m0["ok"], m0["problems"]


@pytest.mark.skipif(not _has_counts(), reason="V25 channel_counts.npz not present")
def test_adapter_entropy_matches_v25_within_1e3():
    counts = chn.load_channel_counts()
    for arch, fact in {"A01": "F01", "A02": "F03"}.items():
        for src in gate.SOURCES:
            ad = chn.build_adapter(counts, fact_id=fact, source=src)
            exp = gate.V25_H[arch][src]
            got = (ad.H_bits["L1"], ad.H_bits["L2"])
            assert abs(got[0] - exp[0]) <= 1e-3
            assert abs(got[1] - exp[1]) <= 1e-3


# --------------------------------------------------------------------------- #
# V26R closeout: resource gate, delay metadata, corrected M1 references
# --------------------------------------------------------------------------- #

def _synthetic_sampler(q: int, eps: float = 0.01):
    """Deterministic-ish BSC-like centered posterior that truly converges."""
    def sampler(n: int, rng: np.random.Generator):
        rows = np.tile(np.array([1 - eps] + [0.0] * (q - 1), dtype=np.float64), (n, 1))
        rows[:, 1:] = eps / (q - 1)
        flips = rng.random(n) < eps
        if flips.any():
            rows[flips] = rows[flips][:, ::-1]
        return rows
    return sampler


class _FakeAdapter:
    """Minimal adapter for runner-level (no real channel data) tests."""

    def __init__(self, q: int = 2, eps: float = 0.001):
        self.q = q
        self.sampler = _synthetic_sampler(q, eps)

    def make_channel_sampler(self, lid):
        return self.sampler

    @property
    def source_label(self):
        return "fake"

    @property
    def delay_used_ps(self):
        return None

    @property
    def n_pairs(self):
        return None


def test_run_screen_resource_gate_blocks_on_small_budget():
    adapter = _FakeAdapter(q=2)
    adapters = {"A01": {src: adapter for src in gate.SOURCES},
                "A02": {src: adapter for src in gate.SOURCES}}
    plan = [{
        "arch": "A01", "layer": "L1", "f": 1.3, "rate": 0.9,
        "rho": {int(k): float(v) for k, v in {2: 1.0}.items()},
        "source": src, "seed": seed, "q": 2,
    } for src in gate.SOURCES for seed in (1, 2)]
    res = gate.run_screen(adapters, plan, out_dir=Path("."), checkpoint_path=None,
                          resource_limit_seconds=1e-9)
    assert res["resource_blocked"] is True
    assert res["completed_calls"] < len(plan)
    assert res["n_calls"] < len(plan)
    assert "resource_limit_seconds" in res


def test_decide_terminal_resource_blocked():
    screen = {"calls": {}, "resource_blocked": True}
    g = gate.decide_terminal(screen, None, {"ok": True}, {"ok": True})
    assert g["status"] == "resource_blocked"


def test_m1_adapter_iter0_really_enters_de_first_round():
    q = 4
    lam = {2: 1.0}
    rho = {2: 1.0}
    sampler = _synthetic_sampler(q, eps=0.02)
    r = vfy.adapter_input_entropy_matches_iter0(q, lam, rho, sampler, seed=5,
                                                n_samples=2000)
    # exact identity: the DE's own recorded iteration-0 channel entropy equals
    # re-drawing the exact channel population the kernel consumed (same seed).
    assert r["err_replay"] <= 1e-10
    # distributional: independent model draw within finite-sample tolerance
    assert r["err_model"] <= r["sampling_tol"]
    assert r["ok"] is True


def test_gf2_bsc_reference_correct_verdicts():
    bsc = vfy.gf2_bsc_reference()
    # noiseless must converge; feasible-rate noisy must converge; at-capacity
    # noisy must correctly fail (never "both non-converge = agree")
    assert bsc["noiseless_conv"] is True
    assert bsc["pass_mine_conv"] is True
    assert bsc["pass_v14_conv"] is True
    assert bsc["fail_mine_conv"] is False
    assert bsc["fail_v14_conv"] is False
    assert bsc["ok"] is True


@pytest.mark.skipif(not _has_counts(), reason="V25 channel_counts.npz not present")
def test_adapter_exposes_delay_metadata():
    counts = chn.load_channel_counts()
    for src in gate.SOURCES:
        ad = chn.build_adapter(counts, fact_id="F01", source=src)
        assert ad.source_label in {"1M", "1p5M", "2M"}
        assert ad.delay_used_ps in (-50, 50)
        assert ad.n_pairs in (512000, 708352, 933120)
    assert chn.SOURCE_METADATA["type2_1M_20260121_184040"]["delay_used_ps"] == -50
    assert chn.SOURCE_METADATA["type2_1p5M_20260121_183806"]["delay_used_ps"] == 50
    assert chn.SOURCE_METADATA["type2_2M_20260121_183657"]["delay_used_ps"] == 50
