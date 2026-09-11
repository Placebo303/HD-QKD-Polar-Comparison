"""D7-F paired reverse-order discriminator qualification (fake/DI only).

No test creates ``workspace/d7_f_reverse_order_discriminator_*`` or reads
real Model-F content; every scientific-run decoder is an injected fake.  No
production decoder is contacted anywhere in this file: all transfer math is
checked against tiny explicit in-memory fixtures and direct enumeration.
The milestone regression runs in its own pytest process with a fresh
task-owned basetemp (no broad suite that could collect historical roots).
"""

from __future__ import annotations

import csv
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "comparison_bench" / "src"
CORE_PATH = (SRC / "comparison_bench" / "formal_ir"
             / "v72p2d7_gf32_reverse_order_discriminator.py")
RUNNER = REPO / "scripts" / "v72p2d7_gf32_reverse_order_discriminator.py"
WS = REPO / "workspace"
MODEL_F_ROOT = WS / "v72p2d5_model_f_input" / "20260907_r1"
D7C_ROOT = (WS / "d7_c_bidirectional_oracle_"
            "94c0ea15-a786-4cb8-a991-6fec521cccae")
D7B_ROOT = WS / "d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964"
D7E_ROOT = (WS / "d7_e_cross_layer_discriminator_"
            "faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c")
D7F_CYCLE_STATE = (REPO / "docs" / "research_cycles"
                   / "V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR"
                   / "cycle_state.yaml")
BP_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_bp_belief_provenance.py"
SUB_TIMEOUT = 1200

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d7_gf32_reverse_order_discriminator as d7f,
)
from comparison_bench.formal_ir import (  # noqa: E402
    v35_algorithm_development as v35,
)

d7e = d7f.d7e
d7c = d7f.d7c
d5 = d7f.d5
Q = 32
TOL = 1e-10


# --------------------------------------------------------------------------
# Shared fake fixtures (no real Model-F / no production run decoder)
# --------------------------------------------------------------------------

def _uniform_joint() -> np.ndarray:
    return np.full((Q, Q, d7f.BOB_DIM), 1.0 / (Q * Q))


def _column_joint(columns: dict) -> np.ndarray:
    """Full-size joint with crafted Bob columns; all other columns uniform."""
    joint = np.full((Q, Q, d7f.BOB_DIM), 1.0 / (Q * Q))
    for bob, entries in columns.items():
        col = np.zeros((Q, Q))
        for (u1, u2), mass in entries.items():
            col[int(u1), int(u2)] = float(mass)
        col = col / col.sum()
        joint[:, :, int(bob)] = col
    return joint


def _skewed_joint() -> np.ndarray:
    """Non-uniform joint on the parity-sampler Bob values (0/1)."""
    return _column_joint({
        0: {(5, 7): 0.5, (5, 8): 0.3, (3, 7): 0.2},
        1: {(11, 13): 0.6, (1, 2): 0.4}})


def _const_block(seed, bob_val=0, a=0, b=0) -> dict:
    n = d7f.N
    bob = np.full(n, int(bob_val), dtype=np.int64)
    u1 = np.full(n, int(a), dtype=np.int64)
    u2 = np.full(n, int(b), dtype=np.int64)
    return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}


def _parity_sampler(b_even=0, b_odd=1):
    def sample(p_b, p_f, n, seed):
        idx = (int(seed) - 2026091300) % 16
        return _const_block(seed, bob_val=b_even if idx % 2 == 0 else b_odd)
    return sample


def _zero_sampler():
    def sample(p_b, p_f, n, seed):
        return _const_block(seed, bob_val=0, a=0, b=0)
    return sample


def _peaked_log(n, peak, mass=0.9):
    row = np.full(Q, (1.0 - mass) / (Q - 1))
    row[int(peak)] = mass
    return np.log(np.tile(row, (int(n), 1)))


def _scripted_source(provenances, peaks=None, iterations=None):
    """SOURCE fake: k-th source call uses script[k] (f, seed, arm order)."""
    state = {"k": 0}
    peaks = list(peaks) if peaks is not None else [0] * 64
    iterations = list(iterations) if iterations is not None else [5] * 64

    def decode(h, prior, syndrome):
        k = state["k"]
        state["k"] += 1
        p = np.asarray(prior, dtype=np.float64)
        prov = provenances[k]
        result = {"x_hat": np.argmax(p, axis=1).astype(np.int64),
                  "syndrome_ok": True, "iterations": int(iterations[k]),
                  "final_beliefs": _peaked_log(p.shape[0], peaks[k]),
                  "status": "fake_source"}
        if prov != "<missing>":
            result["belief_provenance"] = prov
        return result

    decode.calls = state
    return decode


def _argmax_target(iterations: int = 5):
    state = {"n": 0}

    def decode(h, prior, syndrome):
        state["n"] += 1
        p = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.argmax(p, axis=1).astype(np.int64),
                "syndrome_ok": True, "iterations": int(iterations),
                "final_beliefs": np.log(p + 1e-300),
                "belief_provenance": "CHECK_UPDATED",
                "status": "fake_target"}

    decode.calls = state
    return decode


def _target_order():
    """The 64 target-call identities in loop order: (f, seed, arm)."""
    return [(float(s["f"]), int(s["seed"]), s["arm"])
            for s in d7f.frozen_slots() if s["role"] == "TARGET"]


def _planned_target(decisions, iterations: int = 5):
    """TARGET fake engineered per (f, seed, arm): 'hit' decodes exactly on
    zero-truth blocks, 'miss' forces a wrong answer.  Zero sampler required."""
    order = _target_order()
    state = {"n": 0}

    def decode(h, prior, syndrome):
        key = order[state["n"]]
        state["n"] += 1
        n = int(np.asarray(prior, dtype=np.float64).shape[0])
        if decisions.get(key, "hit") == "hit":
            x_hat = np.zeros(n, dtype=np.int64)
        else:
            x_hat = np.ones(n, dtype=np.int64)
        return {"x_hat": x_hat, "syndrome_ok": True,
                "iterations": int(iterations),
                "final_beliefs": _peaked_log(n, 0),
                "belief_provenance": "CHECK_UPDATED",
                "status": "fake_target"}

    decode.calls = state
    return decode


def _source_order():
    """The 64 source-call identities in loop order: (f, seed, arm)."""
    order = []
    for f in d7f.F_VALUES:
        for seed in d7f.BLOCK_SEEDS:
            for arm in d7f.ARMS:
                order.append((float(f), int(seed), arm))
    return order


def _full_run(tmp_path, name="root", *, joint=None, sampler=None,
              source_fn=None, target_fn=None, clock=None, rss_probe=None,
              mothers=None, state=None, out_name=None,
              command_str="fake qualification"):
    out = Path(out_name) if out_name is not None else (tmp_path / name)
    if source_fn is None:
        source_fn = _scripted_source(["CHECK_UPDATED"] * 64)
    if target_fn is None:
        target_fn = _argmax_target()
    return d7f.run_reverse_order_discriminator(
        out_root=out,
        joint=_uniform_joint() if joint is None else joint,
        block_sampler=(_parity_sampler() if sampler is None else sampler),
        mothers=mothers,
        decoder_fns={"SOURCE": source_fn, "TARGET": target_fn},
        state={"d7f_execution_authorized": True} if state is None else state,
        clock=clock,
        rss_probe=(rss_probe if rss_probe is not None
                   else (lambda: 256 * 1024 * 1024)),
        command_str=command_str, repo_root=REPO)


class _ScriptedClock:
    """Deterministic clock: call k costs ``walls[k]`` seconds."""

    def __init__(self, walls):
        self.walls = list(walls)
        self.t = 0.0
        self.k = 0
        self._pending = None

    def __call__(self):
        if self._pending is None:
            self._pending = (self.walls[self.k] if self.k < len(self.walls)
                             else 0.0)
            return self.t
        self.t += self._pending
        self._pending = None
        self.k += 1
        return self.t


def _read_csv(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _rewrite_csv(path, rows, fields):
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _clean_env(extra=None):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    if extra:
        env.update(extra)
    return env


def _dir_meta(path):
    path = Path(path)
    if not path.is_dir():
        return None
    return sorted((p.name, int(p.stat().st_size), int(p.stat().st_mtime_ns))
                  for p in path.iterdir())


def _run_cli(args, cwd, env=None):
    return subprocess.run([sys.executable] + args, cwd=str(cwd),
                          env=_clean_env(env), capture_output=True, text=True,
                          timeout=SUB_TIMEOUT)


# ==========================================================================
# E01-E03: transfer formulas, estimator identity, legacy-builder static ban
# ==========================================================================

def test_e01_both_transfer_formulas_match_direct_enumeration():
    rng = np.random.default_rng(20260913)
    B, n = 3, 5
    raw = rng.random((Q, Q, B)) + 0.1
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 2, 1, 2, 0])
    q = rng.random((n, Q)) + 0.1
    q = q / q.sum(axis=1, keepdims=True)

    got_l12 = d7f.transfer_prior_l1_to_l2(joint, bob, q)
    direct = np.zeros((n, Q))
    for i in range(n):
        cond = joint[:, :, bob[i]] / joint[:, :, bob[i]].sum(
            axis=1, keepdims=True)
        direct[i] = q[i] @ cond
    assert np.allclose(got_l12, d5._floor_renorm(direct, 1e-15),
                       atol=1e-12, rtol=0)

    got_l21 = d7f.transfer_prior_l2_to_l1(joint, bob, q)
    direct = np.zeros((n, Q))
    for i in range(n):
        cond = (joint[:, :, bob[i]]
                / joint[:, :, bob[i]].sum(axis=0, keepdims=True))
        direct[i] = q[i] @ cond.T
    assert np.allclose(got_l21, d5._floor_renorm(direct, 1e-15),
                       atol=1e-12, rtol=0)

    for got in (got_l12, got_l21):
        assert got.shape == (n, Q)
        assert np.allclose(got.sum(axis=1), 1.0, atol=1e-12)
        assert np.all(got >= 1e-15 - 1e-18)

    # Zero-mass conditional slice falls back to uniform (accepted convention).
    joint0 = joint.copy()
    joint0[3, :, 1] = 0.0
    joint0[:, :, 1] = joint0[:, :, 1] / joint0[:, :, 1].sum()
    q_hot = np.zeros((2, Q))
    q_hot[:, 3] = 1.0
    out = d7f.transfer_prior_l1_to_l2(joint0, np.array([1, 1]), q_hot)
    assert np.allclose(out, np.full((2, Q), 1.0 / Q), atol=1e-12)

    # No source truth enters either formula (signature pins the inputs).
    for fn in (d7f.transfer_prior_l1_to_l2, d7f.transfer_prior_l2_to_l1):
        params = list(inspect.signature(fn).parameters)
        assert params == (["joint", "bob", "q1"] if fn is d7f.transfer_prior_l1_to_l2
                          else ["joint", "bob", "q2"])
    assert list(inspect.signature(d7f.build_transfer_prior).parameters) == [
        "joint", "direction", "bob", "q"]
    with pytest.raises(ValueError):
        d7f.build_transfer_prior(joint, "NOPE", bob, q)
    assert np.allclose(d7f.build_transfer_prior(joint, "L1_TO_L2", bob, q),
                       got_l12)
    assert np.allclose(d7f.build_transfer_prior(joint, "L2_TO_L1", bob, q),
                       got_l21)

    # Transient q helper: valid softmax, loud on bad shape/nonfinite.
    logb = np.log(q)
    assert np.allclose(d7f.softmax_source_q(logb), q, atol=1e-12)
    with pytest.raises(ValueError):
        d7f.softmax_source_q(np.zeros((n, Q - 1)))
    bad = logb.copy()
    bad[0, 0] = np.inf
    with pytest.raises(ValueError):
        d7f.softmax_source_q(bad)


def test_e02_corrected_per_column_estimator_identity_and_legacy_differs(monkeypatch):
    assert d7f.LAMBDA_STAR == d5.LAMBDA_STAR == 137.3823795883264
    assert d7f.DECODER_FLOOR == 1e-15
    assert d7f._ESTIMATOR_ID == d7e._ESTIMATOR_ID

    # Tiny asymmetric table: per-Bob-column concentration differs numerically
    # from the historical per-cell rule.
    counts = np.array([[8., 1., 0.], [2., 6., 1.], [0., 2., 7.],
                       [1., 0., 2.]])
    lam = 2.0
    corrected = d5.build_f_model_concentration(counts, lam)
    legacy = d5.build_f_model(counts, lam)
    assert corrected.shape == legacy.shape == (4, 3)
    assert float(np.max(np.abs(corrected - legacy))) > 1e-6
    assert np.allclose(corrected.sum(axis=0), 1.0, atol=1e-12)

    # The D7-F preparation path goes only through the candidate chain.
    counts_big = np.ones((d7f.N_A, d7f.BOB_DIM))
    counts_big[0, 0] = 9.0
    p_b = np.full(d7f.BOB_DIM, 1.0 / d7f.BOB_DIM)
    calls = []
    original = d5.prepare_model_f_prior_candidate

    def spy(c_ab, p_b_in, lam_in=d5.LAMBDA_STAR):
        calls.append((np.asarray(c_ab).shape, np.asarray(p_b_in).shape,
                      float(lam_in)))
        return original(c_ab, p_b_in, lam_in)

    def _forbidden(*args, **kwargs):
        raise AssertionError("rejected estimator path must never be called")

    monkeypatch.setattr(d5, "prepare_model_f_prior_candidate", spy)
    monkeypatch.setattr(d5, "prepare_model_f_prior", _forbidden)
    monkeypatch.setattr(d5, "build_f_model", _forbidden)

    def loader(root):
        return {"counts_ab": counts_big, "p_b": p_b, "files": []}

    ctx = d7f.prepare_inputs(
        model_f_root=d7f.MODEL_F_ROOT, model_f_loader=loader,
        block_sampler=_parity_sampler(), mothers=None, repo=REPO)
    assert calls == [((d7f.N_A, d7f.BOB_DIM), (d7f.BOB_DIM,),
                      d7f.LAMBDA_STAR)]
    assert ctx["joint"].shape == (Q, Q, d7f.BOB_DIM)
    assert len(ctx["slots"]) == 128


def test_e03_legacy_builder_never_referenced_by_d7f():
    legacy_call = re.compile(r"build_f_model\s*\(")
    legacy_prior = re.compile(r"prepare_model_f_prior\s*\(")
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8")
        assert legacy_call.search(source) is None, (path.name, "legacy builder")
        assert legacy_prior.search(source) is None, (path.name, "legacy prior")
    core = CORE_PATH.read_text(encoding="utf-8")
    assert "build_f_model_concentration" in core
    assert "prepare_model_f_prior_candidate" in core


# ==========================================================================
# M01-M03: frozen 128-slot matrix, identity reuse, arm transitions
# ==========================================================================

def test_m01_exact_128_slot_order_and_64_mandatory():
    slots = d7f.frozen_slots()
    assert len(slots) == 128 and d7f.SLOT_COUNT == 128
    assert d7f.MANDATORY_CALLS == 64 and d7f.MAX_CALLS == 128
    assert d7f.ARMS == ("FORWARD_L1_TO_L2", "REVERSE_L2_TO_L1")
    assert [s["slot_idx"] for s in slots] == list(range(1, 129))
    assert len({(s["f"], s["seed"], s["arm"], s["role"])
                for s in slots}) == 128
    assert [s["f"] for s in slots[:64]] == [1.0] * 64
    assert [s["f"] for s in slots[64:]] == [1.2] * 64
    pos = 0
    for f in (1.0, 1.2):
        for seed in range(2026091300, 2026091316):
            want = [
                ("FORWARD_L1_TO_L2", "SOURCE", "L1_MARGINAL", "L1",
                 {1.0: 49, 1.2: 59}[f]),
                ("FORWARD_L1_TO_L2", "TARGET", "L2_TRANSFER", "L2",
                 {1.0: 43, 1.2: 52}[f]),
                ("REVERSE_L2_TO_L1", "SOURCE", "L2_MARGINAL", "L2",
                 {1.0: 43, 1.2: 52}[f]),
                ("REVERSE_L2_TO_L1", "TARGET", "L1_TRANSFER", "L1",
                 {1.0: 49, 1.2: 59}[f]),
            ]
            for arm, role, condition, layer, rows in want:
                slot = slots[pos]
                pos += 1
                assert slot["f"] == f and slot["seed"] == seed
                assert slot["arm"] == arm and slot["role"] == role
                assert slot["condition"] == condition and slot["layer"] == layer
                assert slot["rows"] == rows and slot["n"] == 64
    mandatory = [s for s in slots if s["role"] == "SOURCE"]
    transfers = [s for s in slots if s["role"] == "TARGET"]
    assert len(mandatory) == 64 and len(transfers) == 64


def test_m02_identity_model_rows_mothers_estimator_reuse():
    assert d7f.BLOCK_SEEDS == d7c.BLOCK_SEEDS == tuple(range(2026091300, 2026091316))
    assert d7f.F_VALUES == d7c.F_VALUES == (1.0, 1.2)
    assert d7f.ROWS == d7c.ROWS
    assert d7f.L1_ROWS == {1.0: 49, 1.2: 59}
    assert d7f.L2_ROWS == {1.0: 43, 1.2: 52}
    assert d7f.L1_GRAPH_SEED == d7c.L1_GRAPH_SEED == 2026090501
    assert d7f.L2_GRAPH_SEED == d7c.L2_GRAPH_SEED == 2026090502
    assert d7f.L1_K_MIN == d7c.L1_K_MIN == 49
    assert d7f.L2_K_MIN == d7c.L2_K_MIN == 43
    assert d7f.MAX_ITER == d7c.MAX_ITER == 90
    assert d7f.DAMPING_ALPHA == d7c.DAMPING_ALPHA == 1.0
    assert d7f.Q == d7c.Q == 32 and d7f.N == d7c.N == 64
    # Narrow reuse (aliases, not copies) of the accepted helpers.
    assert d7f.condition_prior_qn is d7e.condition_prior_qn
    assert d7f.decoder_prior is d7e.decoder_prior
    assert d7f.build_joint is d7e.build_joint
    assert d7f.build_mother is d7e.build_mother
    assert d7f._default_model_f_loader is d7e._default_model_f_loader
    assert d7f.softmax_source_q is d7e.softmax_source_q
    assert d7f.transfer_prior_l1_to_l2 is d7e.transfer_prior_l1_to_l2
    assert d7f.transfer_prior_l2_to_l1 is d7e.transfer_prior_l2_to_l1
    assert d7f.build_transfer_prior is d7e.build_transfer_prior
    assert d7f.check_source_eligibility is d7e.check_source_eligibility
    assert d7f.require_check_updated is d7e.require_check_updated
    assert d7f.dispatch_decoder is d7e.dispatch_decoder
    assert d7f.bind_row_layered_decoders is d7e.bind_row_layered_decoders
    assert d7f.parse_vmhwm_rss_bytes is d7e.parse_vmhwm_rss_bytes
    assert d7f._probe_rss_valid is d7e._probe_rss_valid
    assert np.array_equal(d7f.build_mother("L1"), d7c.build_mother("L1"))
    assert np.array_equal(d7f.build_mother("L2"), d7c.build_mother("L2"))
    # Marginal priors agree with the D7-C contract on a random joint.
    rng = np.random.default_rng(20260913)
    raw = rng.random((Q, Q, 5)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 4, 2, 3, 1, 4])
    u1 = np.array([3, 7, 31, 0, 15, 2])
    u2 = np.array([5, 1, 29, 8, 30, 6])
    block = {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}
    for condition in ("L1_MARGINAL", "L2_MARGINAL"):
        assert np.array_equal(d7f.condition_prior_qn(joint, condition, block),
                              d7c.condition_prior_qn(joint, condition, block))
    raw_prior = np.zeros((Q, 4))
    raw_prior[0, 0] = 1.0
    raw_prior[:, 1] = 1e-20
    assert np.array_equal(d7f.decoder_prior(raw_prior),
                          d7c.decoder_prior(raw_prior))


def test_m03_arm_transitions_and_blocked_non_calls(tmp_path):
    # All CHECK_UPDATED: 64 sources + 64 targets, one arm row per arm.
    out = tmp_path / "m03_full"
    result = _full_run(tmp_path, out_name=out)
    assert result["records"] == 128
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    targets = [r for r in rows if r["role"] == "TARGET"]
    assert len(sources) == 64 and len(targets) == 64
    pairs = _read_csv(out / "arm_pairs.csv")
    assert len(pairs) == 64
    assert {p["arm"] for p in pairs} == set(d7f.ARMS)
    for pair in pairs:
        assert int(pair["target_slot_idx"]) == int(pair["source_slot_idx"]) + 1
        assert pair["source_provenance"] == "CHECK_UPDATED"
    # Source and target of one arm never share a layer: no transfer back.
    for pair in pairs:
        assert pair["source_layer"] != pair["target_layer"]
    assert d7f.verify_root(out)["ok"] is True

    # All refused: 64 blocked non-calls, zero target invocations.
    out2 = tmp_path / "m03_blocked"
    source = _scripted_source(["PRIOR_ONLY"] * 64)
    target = _argmax_target()
    result2 = d7f.run_reverse_order_discriminator(
        out_root=out2, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result2["records"] == 64
    assert source.calls["k"] == 64 and target.calls["n"] == 0
    assert _read_csv(out2 / "arm_pairs.csv") == []
    strata = _read_csv(out2 / "stratum_summary.csv")
    assert len(strata) == 2
    assert all(s["forward_eligible_count"] == "0" for s in strata)
    assert all(s["reverse_eligible_count"] == "0" for s in strata)
    assert result2["terminal"] == "D7_F_PROVENANCE_COVERAGE_BLOCKED"
    assert d7f.verify_root(out2)["ok"] is True

    # Frozen production call shapes carry no per-role delta.
    fns = d7f.bind_row_layered_decoders()
    assert fns["SOURCE"].target is v35.decode_row_layered_fftqspa
    assert fns["TARGET"].target is v35.decode_row_layered_fftqspa
    assert d7f.MAX_ITER == 90 and d7f.DAMPING_ALPHA == 1.0


# ==========================================================================
# G01-G05: provenance gate behavior
# ==========================================================================

def test_g01_check_updated_allows_exactly_one_transfer_call(tmp_path):
    out = tmp_path / "g01"
    result = _full_run(tmp_path, out_name=out)
    assert result["records"] == 128
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    targets = [r for r in rows if r["role"] == "TARGET"]
    assert len(sources) == 64 and len(targets) == 64
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert all(r["belief_provenance"] == "CHECK_UPDATED" for r in sources)
    pairs = _read_csv(out / "arm_pairs.csv")
    assert len(pairs) == 64
    assert all(p["source_provenance"] == "CHECK_UPDATED" for p in pairs)
    assert d7f.verify_root(out)["ok"] is True
    eligible, reason = d7f.check_source_eligibility(
        status="fake", finite=True, belief_shape_ok=True,
        provenance="CHECK_UPDATED")
    assert (eligible, reason) == (True, "ELIGIBLE")


def test_g02_refused_provenance_blocks_before_mixer_and_target(tmp_path, monkeypatch):
    refused = ["PRIOR_ONLY", "<missing>", None, "SOME_FUTURE_TOKEN",
               v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED]
    assert v35.BELIEF_PROVENANCE_PRIOR_ONLY == "PRIOR_ONLY"
    for index, token in enumerate(refused):
        mixer_calls = []

        def _mixer_raiser(joint, direction, bob, q):
            mixer_calls.append(direction)
            raise AssertionError("mixer must not run for %r" % (token,))

        def _softmax_raiser(log_beliefs):
            mixer_calls.append("softmax")
            raise AssertionError("softmax must not run for %r" % (token,))

        monkeypatch.setattr(d7e, "build_transfer_prior", _mixer_raiser)
        monkeypatch.setattr(d7e, "softmax_source_q", _softmax_raiser)
        target = _argmax_target()
        out = tmp_path / ("g02_%d" % index)
        result = d7f.run_reverse_order_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": _scripted_source([token] * 64),
                         "TARGET": target},
            state={"d7f_execution_authorized": True},
            rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
        assert mixer_calls == [], token
        assert target.calls["n"] == 0, token  # no transfer call at all
        assert result["records"] == 64, token
        rows = _read_csv(out / "decoder_records.csv")
        assert all(r["role"] == "SOURCE" for r in rows)
        assert all(r["transfer_eligible"] == "False" for r in rows)
        assert _read_csv(out / "arm_pairs.csv") == []
        strata = _read_csv(out / "stratum_summary.csv")
        assert all(s["forward_eligible_count"] == "0" for s in strata)
        assert all(s["reverse_eligible_count"] == "0" for s in strata)
        assert all(s["stratum_label"] == "COVERAGE_BLOCKED" for s in strata)
        assert all(s["coverage_status"] == "COVERAGE_BLOCKED" for s in strata)
        assert result["terminal"] == "D7_F_PROVENANCE_COVERAGE_BLOCKED"
        assert d7f.verify_root(out)["ok"] is True
        monkeypatch.undo()
        eligible, reason = d7f.check_source_eligibility(
            status="fake", finite=True, belief_shape_ok=True,
            provenance=(None if token in ("<missing>", None) else token))
        assert eligible is False and reason == "PROVENANCE_BLOCKED", token


def test_g03_source_exact_false_stays_eligible_with_valid_provenance(tmp_path):
    # Uniform joint + nonzero truth: argmax fakes miss everywhere, yet the
    # CHECK_UPDATED gate still admits every transfer.
    out = tmp_path / "g03"
    sampler = lambda p_b, p_f, n, seed: _const_block(seed, bob_val=0, a=3, b=7)
    result = _full_run(tmp_path, out_name=out, sampler=sampler)
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    assert all(r["exact"] == "False" for r in sources)
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert len([r for r in rows if r["role"] == "TARGET"]) == 64
    pairs = _read_csv(out / "arm_pairs.csv")
    assert all(p["source_exact"] == "False" for p in pairs)
    assert len(pairs) == 64
    assert d7f.verify_root(out)["ok"] is True


def test_g04_token_governs_not_iterations_shape_crash_or_exactness(tmp_path):
    # iterations=0 with a CHECK_UPDATED token stays eligible; a refused token
    # with iterations>0 stays blocked.  The token governs, never the label.
    out = tmp_path / "g04"
    result = d7f.run_reverse_order_discriminator(
        out_root=out, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={
            "SOURCE": _scripted_source(["CHECK_UPDATED"] * 64,
                                       iterations=[0] * 64),
            "TARGET": _argmax_target()},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    assert all(r["current_belief_label"] == "PRIOR_ONLY_CURRENT_BELIEF"
               for r in sources)
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert result["records"] == 128
    assert d7f.verify_root(out)["ok"] is True

    out2 = tmp_path / "g04b"
    result2 = d7f.run_reverse_order_discriminator(
        out_root=out2, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={
            "SOURCE": _scripted_source(["PRIOR_ONLY"] * 64,
                                       iterations=[7] * 64),
            "TARGET": _argmax_target()},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result2["records"] == 64
    rows2 = _read_csv(out2 / "decoder_records.csv")
    assert all(r["transfer_eligible"] == "False"
               for r in rows2 if r["role"] == "SOURCE")

    # Crash status, nonfinite result and invalid belief shape all block.
    assert d7f.check_source_eligibility(
        status="crash:RuntimeError", finite=False, belief_shape_ok=False,
        provenance="CHECK_UPDATED") == (False, "SOURCE_CRASH")
    assert d7f.check_source_eligibility(
        status="ok", finite=False, belief_shape_ok=True,
        provenance="CHECK_UPDATED") == (False, "SOURCE_NONFINITE")
    assert d7f.check_source_eligibility(
        status="ok", finite=True, belief_shape_ok=False,
        provenance="CHECK_UPDATED") == (False, "SOURCE_BELIEF_SHAPE_INVALID")


def test_g05_fewer_than_12_eligible_yields_coverage_block(tmp_path):
    provenances = ["CHECK_UPDATED"] * 64
    order = _source_order()
    # Stratum f=1.0 forward arm: first five sources refused -> 11 eligible.
    refused = {(1.0, 2026091300 + k, "FORWARD_L1_TO_L2") for k in range(5)}
    for k, key in enumerate(order):
        if key in refused:
            provenances[k] = "PRIOR_ONLY"
    out = tmp_path / "g05"
    result = d7f.run_reverse_order_discriminator(
        out_root=out, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": _scripted_source(provenances),
                     "TARGET": _argmax_target()},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 64 + (64 - 5)
    strata = _read_csv(out / "stratum_summary.csv")
    thin = [s for s in strata if float(s["f"]) == 1.0][0]
    assert thin["forward_eligible_count"] == "11"
    assert thin["forward_blocked_count"] == "5"
    assert thin["stratum_label"] == "COVERAGE_BLOCKED"
    assert thin["coverage_status"] == "COVERAGE_BLOCKED"
    assert result["terminal"] == "D7_F_PROVENANCE_COVERAGE_BLOCKED"
    assert d7f.verify_root(out)["ok"] is True
    # The 12/16 boundary itself: exactly 12 labels, 11 does not.
    assert d7f.classify_stratum(
        forward_eligible=12, reverse_eligible=16, candidate_only=0,
        reference_only=0) == "NO_REVERSE_LIFT"
    assert d7f.classify_stratum(
        forward_eligible=11, reverse_eligible=16, candidate_only=0,
        reference_only=0) == "COVERAGE_BLOCKED"
    assert d7f.classify_stratum(
        forward_eligible=16, reverse_eligible=11, candidate_only=16,
        reference_only=0) == "COVERAGE_BLOCKED"


# ==========================================================================
# S01-S02: evidence-use contract (syndrome consumed once, no target reuse)
# ==========================================================================

def test_s01_each_syndrome_consumed_once_by_its_own_decoder(tmp_path):
    captured = {"SOURCE": [], "TARGET": []}
    inner_source = _scripted_source(["CHECK_UPDATED"] * 64)
    inner_target = _argmax_target()

    def make(key, inner):
        def decoder(h, prior, syndrome):
            captured[key].append((np.array(h, copy=True),
                                  np.array(prior, copy=True),
                                  np.array(syndrome, copy=True)))
            return inner(h, prior, syndrome)
        return decoder

    out = tmp_path / "s01"
    result = d7f.run_reverse_order_discriminator(
        out_root=out, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": make("SOURCE", inner_source),
                     "TARGET": make("TARGET", inner_target)},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 128
    assert len(captured["SOURCE"]) == 64
    assert len(captured["TARGET"]) == 64
    slots = d7f.frozen_slots()
    # Match captured calls back to frozen slots in order; every call consumed
    # exactly one syndrome routed to its own stage.
    calls = []
    si = ti = 0
    for slot in slots:
        if slot["role"] == "SOURCE":
            h, prior, syn = captured["SOURCE"][si]
            si += 1
        else:
            h, prior, syn = captured["TARGET"][ti]
            ti += 1
        calls.append((slot, h, prior, syn))
    assert si == 64 and ti == 64
    seen = set()
    for slot, h, prior, syn in calls:
        layer = slot["layer"]
        seed = slot["seed"]
        truth = _const_block(seed, bob_val=0 if (seed - 2026091300) % 2 == 0 else 1)
        x_true = truth["u1"] if layer == "L1" else truth["u2"]
        assert h.shape == (slot["rows"], 64)
        assert prior.shape == (64, 32)
        assert syn.shape == (slot["rows"],)
        assert np.array_equal(syn, d5._gf32_syndrome(h, x_true))
        seen.add((slot["slot_idx"], tuple(np.asarray(syn).tolist())))
    # 128 distinct (slot, syndrome) consumptions: each syndrome once.
    assert len(seen) == 128
    # Within one arm the two stages use different layers/row counts, so a
    # replayed syndrome cannot verify by shape.
    for f in (1.0, 1.2):
        for seed in range(2026091300, 2026091302):
            for arm in d7f.ARMS:
                syns = [syn for (slot, _, _, syn) in calls
                        if slot["f"] == f and slot["seed"] == seed
                        and slot["arm"] == arm]
                assert len(syns) == 2 and syns[0].shape != syns[1].shape
    assert d7f.verify_root(out)["ok"] is True


def test_s02_no_target_posterior_reuse_static_and_behavioral(tmp_path):
    # Static: no code path carries a target posterior into another call.
    source = CORE_PATH.read_text(encoding="utf-8")
    for token in ("decode_flooding_fftqspa", "L1_ORACLE_U2", "L2_ORACLE_U1",
                  "FLOODING", "flooding", "--phase", "psutil", "concurrent",
                  "multiprocessing", "threading", "warm_beliefs=q",
                  "warm_beliefs=target", "warm_beliefs=prev", "blend(",
                  "feedback(", "multiply(", "reuse_target", "third_stage",
                  "turbo_", "joint_graph"):
        assert token not in source, token
    assert source.count("warm_beliefs=None") == 2
    assert "r1d" not in source.lower()
    # Behavioral: every captured prior recomputes exactly from its own
    # stage inputs only (marginal joint slice, or the paired source belief
    # plus joint) — a target posterior contributes to no later call.
    joint = _skewed_joint()
    slots = d7f.frozen_slots()
    call_priors = []
    src_beliefs = {}
    src_fake = _scripted_source(["CHECK_UPDATED"] * 64)

    def source_wrap(h, prior, syndrome):
        call_priors.append(np.array(prior, copy=True))
        return src_fake(h, prior, syndrome)

    def target_canary(h, prior, syndrome):
        call_priors.append(np.array(prior, copy=True))
        n = int(np.asarray(prior, dtype=np.float64).shape[0])
        return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": True,
                "iterations": 5, "final_beliefs": _peaked_log(n, 31),
                "belief_provenance": "CHECK_UPDATED", "status": "fake_target"}

    out = tmp_path / "s02"
    result = d7f.run_reverse_order_discriminator(
        out_root=out, joint=joint,
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": source_wrap, "TARGET": target_canary},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 128 and len(call_priors) == 128
    for slot, captured in zip(slots, call_priors):
        seed = int(slot["seed"])
        block = _const_block(
            seed, bob_val=0 if (seed - 2026091300) % 2 == 0 else 1)
        if slot["role"] == "SOURCE":
            expected = d7f.decoder_prior(d7f.condition_prior_qn(
                joint, slot["condition"], block))
            assert np.allclose(captured, expected), slot["slot_idx"]
            src_beliefs[(float(slot["f"]), seed,
                         slot["arm"])] = _peaked_log(64, 0)
        else:
            key = (float(slot["f"]), seed, slot["arm"])
            expected = d7f.build_transfer_prior(
                joint, d7f.ARM_TO_DIRECTION[slot["arm"]], block["bob"],
                d7f.softmax_source_q(src_beliefs[key]))
            assert np.allclose(captured, expected), slot["slot_idx"]
    # Target posteriors (canary peak 31) are never read back: every prior
    # above recomputed from source-side inputs only.
    assert d7f.verify_root(out)["ok"] is True


# ==========================================================================
# B01: both-layer exact truth table and syndrome isolation
# ==========================================================================

def _b01_slot(arm, role):
    slots = d7f.frozen_slots()
    return next(s for s in slots if s["arm"] == arm and s["role"] == role
                and s["f"] == 1.0 and s["seed"] == 2026091300)


def test_b01_both_layers_exact_truth_table_and_syndrome_isolation():
    rows_l1 = d7f.L1_ROWS[1.0]
    h = np.zeros((rows_l1, d7f.N), dtype=np.int64)  # zero matrix: null syndrome
    x_true = np.zeros(d7f.N, dtype=np.int64)
    syndrome = d5._gf32_syndrome(h, x_true)
    block = {"bob": np.zeros(d7f.N, dtype=np.int64), "u1": x_true,
             "u2": np.zeros(d7f.N, dtype=np.int64)}
    prior = np.full((d7f.N, Q), 1.0 / Q)
    x_wrong = x_true.copy()
    x_wrong[0] = 1

    def run(slot, x_hat, reported):
        return d7f.evaluate_call(
            slot, h, block, syndrome,
            {"x_hat": x_hat, "syndrome_ok": reported, "iterations": 2,
             "final_beliefs": np.log(prior), "status": "fake",
             "belief_provenance": "CHECK_UPDATED"}, 0.1, 1024)

    fwd_src = _b01_slot("FORWARD_L1_TO_L2", "SOURCE")
    fwd_tgt = _b01_slot("FORWARD_L1_TO_L2", "TARGET")
    rev_src = _b01_slot("REVERSE_L2_TO_L1", "SOURCE")
    rev_tgt = _b01_slot("REVERSE_L2_TO_L1", "TARGET")

    # Syndrome-only success never sets exact: one symbol error with a null
    # observed syndrome stays inexact yet syndrome-satisfied.
    syn_only = run(fwd_tgt, x_wrong, True)
    assert syn_only["exact"] is False and syn_only["syndrome_ok"] is True
    assert syn_only["symbol_errors"] == 1
    assert syn_only["unsatisfied_checks"] == 0
    # Exact recovery with a negatively-reported flag stays exact-only.
    exact_only = run(fwd_src, x_true, False)
    assert exact_only["exact"] is True and exact_only["syndrome_ok"] is False

    # Truth table over the four (l1_exact, l2_exact) corners per arm.
    for arm, src_slot, tgt_slot in (("FORWARD_L1_TO_L2", fwd_src, fwd_tgt),
                                    ("REVERSE_L2_TO_L1", rev_src, rev_tgt)):
        for l1_hit, l2_hit in ((True, True), (True, False),
                               (False, True), (False, False)):
            if arm == "FORWARD_L1_TO_L2":
                src = run(src_slot, x_true if l1_hit else x_wrong, True)
                tgt = run(tgt_slot, x_true if l2_hit else x_wrong, True)
            else:
                src = run(src_slot, x_true if l2_hit else x_wrong, True)
                tgt = run(tgt_slot, x_true if l1_hit else x_wrong, True)
            pairs = d7f.compute_arm_pairs([src, tgt])
            assert len(pairs) == 1
            pair = pairs[0]
            assert pair["l1_exact"] == l1_hit
            assert pair["l2_exact"] == l2_hit
            assert pair["both_layers_exact"] == bool(l1_hit and l2_hit)
            # Syndrome columns ride along untouched by the AND rule.
            assert pair["l1_syndrome_ok"] is True
            assert pair["l2_syndrome_ok"] is True


# ==========================================================================
# L01-L03: paired labels, terminals, caps, budgets
# ==========================================================================

def test_l01_paired_label_boundaries_and_first_match():
    cs = d7f.classify_stratum
    assert list(inspect.signature(cs).parameters) == [
        "forward_eligible", "reverse_eligible", "candidate_only",
        "reference_only"]
    # Coverage first: either arm below 12 blocks regardless of counts.
    assert cs(forward_eligible=11, reverse_eligible=16, candidate_only=16,
              reference_only=0) == d7f.S_COVERAGE
    assert cs(forward_eligible=16, reverse_eligible=11, candidate_only=0,
              reference_only=16) == d7f.S_COVERAGE
    assert cs(forward_eligible=12, reverse_eligible=12, candidate_only=0,
              reference_only=0) == d7f.S_NONE
    # Regression boundary: reference>=2 with zero candidate.
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=0,
              reference_only=2) == d7f.S_REGRESSION
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=0,
              reference_only=16) == d7f.S_REGRESSION
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=0,
              reference_only=1) == d7f.S_NONE
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=1,
              reference_only=2) == d7f.S_NONE
    # Strong boundary: candidate>=4 with zero reference.
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=4,
              reference_only=0) == d7f.S_STRONG
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=16,
              reference_only=0) == d7f.S_STRONG
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=3,
              reference_only=0) == d7f.S_WEAK
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=4,
              reference_only=1) == d7f.S_WEAK
    # Weak: strictly more candidate than reference, strong not met.
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=1,
              reference_only=0) == d7f.S_WEAK
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=2,
              reference_only=1) == d7f.S_WEAK
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=0,
              reference_only=0) == d7f.S_NONE
    assert cs(forward_eligible=16, reverse_eligible=16, candidate_only=1,
              reference_only=1) == d7f.S_NONE
    assert d7f.STRATUM_LABELS == ("COVERAGE_BLOCKED", "REVERSE_REGRESSION",
                                  "STRONG_REVERSE_LIFT", "WEAK_REVERSE_LIFT",
                                  "NO_REVERSE_LIFT")


def test_l02_ten_terminal_priorities_and_truth_table():
    assert list(d7f.TERMINALS) == [
        "D7_F_PRE_EXECUTION_BLOCKED", "D7_F_WATCHDOG_TIMEOUT_VOID",
        "D7_F_NONFINITE_OR_CRASH_BLOCKED", "D7_F_RESOURCE_OVERRUN",
        "D7_F_INCOMPLETE_MATRIX_BLOCKED", "D7_F_PROVENANCE_COVERAGE_BLOCKED",
        "D7_F_REVERSE_ORDER_STRONG_LIFT", "D7_F_REVERSE_ORDER_WEAK_LIFT",
        "D7_F_REVERSE_ORDER_REGRESSION", "D7_F_NO_USEFUL_REVERSE_ORDER_LIFT"]
    base = {"pre_blocked": False, "watchdog_timeout": False,
            "crash_nonfinite": False, "resource_overrun": False,
            "incomplete": False, "coverage_blocked": False,
            "strata": {1.0: d7f.S_NONE, 1.2: d7f.S_NONE}}
    assert d7f.classify_terminal(base) == d7f.T_NO_LIFT
    # T1..T6 cascade: each beats every lower terminal.
    for key, terminal in (("pre_blocked", d7f.T_PRE_EXEC),
                          ("watchdog_timeout", d7f.T_WATCHDOG),
                          ("crash_nonfinite", d7f.T_CRASH),
                          ("resource_overrun", d7f.T_RESOURCE),
                          ("incomplete", d7f.T_INCOMPLETE),
                          ("coverage_blocked", d7f.T_COVERAGE)):
        assert d7f.classify_terminal(dict(base, **{key: True})) == terminal
    everything = dict(base, pre_blocked=True, watchdog_timeout=True,
                      crash_nonfinite=True, resource_overrun=True,
                      incomplete=True, coverage_blocked=True)
    assert d7f.classify_terminal(everything) == d7f.T_PRE_EXEC
    assert d7f.classify_terminal(dict(everything, pre_blocked=False)) == d7f.T_WATCHDOG
    assert d7f.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False)) == d7f.T_CRASH
    assert d7f.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False)) == d7f.T_RESOURCE
    assert d7f.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False,
                                      resource_overrun=False)) == d7f.T_INCOMPLETE
    assert d7f.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False,
                                      resource_overrun=False,
                                      incomplete=False)) == d7f.T_COVERAGE
    # T7: either f strong while the other does not regress.
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_STRONG, 1.2: d7f.S_NONE})) == d7f.T_STRONG
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_NONE, 1.2: d7f.S_STRONG})) == d7f.T_STRONG
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_STRONG, 1.2: d7f.S_WEAK})) == d7f.T_STRONG
    # T8: either f weak while neither regresses.
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_WEAK, 1.2: d7f.S_NONE})) == d7f.T_WEAK
    # T9: regression when no strong/weak lift survives the priority above.
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_REGRESSION, 1.2: d7f.S_NONE})) == d7f.T_REGRESSION
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_STRONG,
                      1.2: d7f.S_REGRESSION})) == d7f.T_REGRESSION
    assert d7f.classify_terminal(dict(
        base, strata={1.0: d7f.S_WEAK,
                      1.2: d7f.S_REGRESSION})) == d7f.T_REGRESSION
    # Coverage outranks every mechanism terminal.
    assert d7f.classify_terminal(dict(
        base, coverage_blocked=True,
        strata={1.0: d7f.S_STRONG, 1.2: d7f.S_STRONG})) == d7f.T_COVERAGE


def _target_decisions(pairs):
    """Map ((f, seed, arm) -> 'hit'/'miss') for TARGET calls from a compact
    per-seed plan: {(f, seed): (forward_hit, reverse_hit)}."""
    decisions = {}
    for f in d7f.F_VALUES:
        for seed in d7f.BLOCK_SEEDS:
            fwd_hit, rev_hit = pairs.get((float(f), int(seed)), (True, True))
            decisions[(float(f), int(seed),
                       "FORWARD_L1_TO_L2")] = "hit" if fwd_hit else "miss"
            decisions[(float(f), int(seed),
                       "REVERSE_L2_TO_L1")] = "hit" if rev_hit else "miss"
    return decisions


def test_l03_loop_terminal_families_and_budgets(tmp_path):
    assert d7f.PER_CALL_WATCHDOG_S == 120.0
    assert d7f.STORED_WALL_LIMIT_S == 1500.0
    assert d7f.OUTER_WATCHDOG_S == 1800.0 and d7f.OUTER_GRACE_S == 30.0
    assert d7f.RSS_LIMIT_BYTES == 2 * 1024**3

    # T7: strong reverse lift at f=1.2 (5 candidate-only, 0 reference).
    plan = {(1.2, 2026091300 + k): (False, True) for k in range(5)}
    result = d7f.run_reverse_order_discriminator(
        out_root=tmp_path / "t7", joint=_uniform_joint(),
        block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": _scripted_source(["CHECK_UPDATED"] * 64),
                     "TARGET": _planned_target(_target_decisions(plan))},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 128
    labels = {row["f"]: row["stratum_label"]
              for row in result["summary"]["strata"]}
    assert labels[1.2] == d7f.S_STRONG, result["summary"]["strata"]
    assert labels[1.0] == d7f.S_NONE
    assert result["terminal"] == d7f.T_STRONG
    assert d7f.verify_root(tmp_path / "t7")["ok"] is True

    # T8: weak reverse lift at f=1.0 (2 candidate-only, 1 reference-only).
    plan = {(1.0, 2026091300): (False, True),
            (1.0, 2026091301): (False, True),
            (1.0, 2026091302): (True, False)}
    result = d7f.run_reverse_order_discriminator(
        out_root=tmp_path / "t8", joint=_uniform_joint(),
        block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": _scripted_source(["CHECK_UPDATED"] * 64),
                     "TARGET": _planned_target(_target_decisions(plan))},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["terminal"] == d7f.T_WEAK, result["summary"]["strata"]
    labels = {row["f"]: row["stratum_label"]
              for row in result["summary"]["strata"]}
    assert labels[1.0] == d7f.S_WEAK and labels[1.2] == d7f.S_NONE
    assert d7f.verify_root(tmp_path / "t8")["ok"] is True

    # T9: reverse regression at f=1.0 (0 candidate, 2 reference-only).
    plan = {(1.0, 2026091300): (True, False),
            (1.0, 2026091301): (True, False)}
    result = d7f.run_reverse_order_discriminator(
        out_root=tmp_path / "t9", joint=_uniform_joint(),
        block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": _scripted_source(["CHECK_UPDATED"] * 64),
                     "TARGET": _planned_target(_target_decisions(plan))},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["terminal"] == d7f.T_REGRESSION
    assert d7f.verify_root(tmp_path / "t9")["ok"] is True

    # T10: uniform zero-truth run recovers both arms everywhere (neither).
    result = _full_run(tmp_path, sampler=_zero_sampler(),
                       out_name=tmp_path / "t10")
    assert result["terminal"] == d7f.T_NO_LIFT
    assert all(row["stratum_label"] == d7f.S_NONE
               for row in result["summary"]["strata"])
    assert d7f.verify_root(tmp_path / "t10")["ok"] is True

    # Hard cap: an all-eligible run makes exactly 128 calls, no retry.
    source = _scripted_source(["CHECK_UPDATED"] * 64)
    target = _argmax_target()
    result = d7f.run_reverse_order_discriminator(
        out_root=tmp_path / "cap", joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7f_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 128
    assert source.calls["k"] == 64 and target.calls["n"] == 64

    # Crash priority: no retry, prefix records, crash terminal.
    counter = {"n": 0}

    def crash_at_40(h, prior, syndrome):
        counter["n"] += 1
        if counter["n"] == 40:
            raise RuntimeError("boom")
        return _argmax_target()(h, prior, syndrome)

    result = _full_run(tmp_path, target_fn=crash_at_40,
                       out_name=tmp_path / "t3")
    assert counter["n"] == 40
    assert result["terminal"] == d7f.T_CRASH
    records = _read_csv(tmp_path / "t3" / "decoder_records.csv")
    assert records[-1]["status"].startswith("crash:")
    assert d7f.verify_root(tmp_path / "t3")["ok"] is True

    # Watchdog boundary: 120.0 s passes, anything above voids the run.
    result = _full_run(tmp_path, clock=_ScriptedClock([120.0] + [0.0] * 127),
                       out_name=tmp_path / "w120")
    assert result["terminal"] != d7f.T_WATCHDOG
    result = _full_run(tmp_path, clock=_ScriptedClock([120.0001] + [0.0] * 127),
                       out_name=tmp_path / "w121")
    assert result["terminal"] == d7f.T_WATCHDOG and result["records"] == 1
    assert d7f.verify_root(tmp_path / "w121")["ok"] is True

    # Stored-wall boundary: exactly 1500 s passes, anything above overruns.
    result = _full_run(tmp_path, clock=_ScriptedClock([11.71875] * 128),
                       out_name=tmp_path / "wall1500")
    assert result["records"] == 128 and result["terminal"] != d7f.T_RESOURCE
    summary = json.loads((tmp_path / "wall1500" / "summary.json")
                         .read_text(encoding="utf-8"))
    assert abs(float(summary["stored_wall_s"]) - 1500.0) <= 1e-9
    result = _full_run(tmp_path,
                       clock=_ScriptedClock([11.71875] * 127 + [11.71876]),
                       out_name=tmp_path / "wall1501")
    assert result["terminal"] == d7f.T_RESOURCE
    result = _full_run(tmp_path, rss_probe=lambda: d7f.RSS_LIMIT_BYTES,
                       out_name=tmp_path / "rss2g")
    assert result["terminal"] == d7f.T_RESOURCE and result["records"] == 1

    # RSS preflight refuses before any work (zero decoder calls, no root).
    events = []
    out = tmp_path / "t1"

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    with pytest.raises(d7f.PreflightBlocked) as excinfo:
        d7f.run_reverse_order_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7f_execution_authorized": True},
            rss_probe=lambda: 0, repo_root=REPO)
    assert excinfo.value.terminal == d7f.T_PRE_EXEC and events == []
    assert not out.exists()

    # Truncated record sets without a stop recompute to INCOMPLETE.
    _full_run(tmp_path, out_name=tmp_path / "trunc_src")
    rows = _read_csv(tmp_path / "trunc_src" / "decoder_records.csv")
    kept = [r for r in rows if int(r["slot_idx"]) <= 120]
    paired = d7f.compute_arm_pairs(kept)
    strata = d7f.compute_strata(kept, paired)
    assert d7f.terminal_from_records(kept, paired, strata) == d7f.T_INCOMPLETE


# ==========================================================================
# W01-W03: scalar writer, verifier tamper cases, forbidden payloads
# ==========================================================================

def test_w01_seven_file_schema_scalar_no_subdirs_no_overwrite(tmp_path):
    out = tmp_path / "w01"
    _full_run(tmp_path, out_name=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(d7f.SEVEN_FILES)
    assert not any(p.is_dir() for p in out.iterdir())
    records = _read_csv(out / "decoder_records.csv")
    paired = _read_csv(out / "arm_pairs.csv")
    strata = _read_csv(out / "stratum_summary.csv")
    assert list(records[0].keys()) == d7f.RECORD_FIELDS
    assert list(paired[0].keys()) == d7f.PAIR_FIELDS
    assert list(strata[0].keys()) == d7f.STRATUM_FIELDS
    assert len(records) == 128 and len(paired) == 64 and len(strata) == 2
    for row in records + paired + strata:
        for value in row.values():
            assert not str(value).startswith("[") and not str(value).startswith("{")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert manifest["max_calls"] == 128 and manifest["mandatory_calls"] == 64
    assert manifest["arms"] == ["FORWARD_L1_TO_L2", "REVERSE_L2_TO_L1"]
    assert manifest["call_order"] == d7f._CALL_ORDER
    assert manifest["decoder_ids"] == dict(d7f._DECODER_IDS)
    assert (out / "report.md").read_text(encoding="utf-8").strip()
    assert (out / "command_log.txt").read_text(encoding="utf-8").strip()

    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        d7f.write_root(populated, {}, [], [], [], {})
    empty_existing = tmp_path / "empty_existing"
    empty_existing.mkdir()
    with pytest.raises(FileExistsError):
        d7f.write_root(empty_existing, {}, [], [], [], {})
    subdir = tmp_path / "subdir"
    (subdir / "nested").mkdir(parents=True)
    with pytest.raises(ValueError):
        d7f.write_root(subdir, {}, [], [], [], {})

    complete = {key: "" for key in d7f.RECORD_FIELDS}
    complete.update({"slot_idx": 1, "f": 1.0, "seed": 2026091300,
                     "arm": "FORWARD_L1_TO_L2", "role": "SOURCE",
                     "condition": "L1_MARGINAL", "layer": "L1",
                     "rows": 49, "n": 64})
    with pytest.raises(ValueError):
        d7f.write_root(tmp_path / "bad_extra", {},
                       [dict(complete, u1_vector=[1])], [], [], {})
    with pytest.raises(ValueError):
        d7f.write_root(tmp_path / "bad_array", {},
                       [dict(complete, wall_s=np.zeros(3))], [], [], {})

    existing = tmp_path / "existing"
    existing.mkdir()
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    with pytest.raises(FileExistsError):
        d7f.run_reverse_order_discriminator(
            out_root=existing, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7f_execution_authorized": True}, repo_root=REPO)
    assert events == []
    with pytest.raises(ValueError):
        d7f.validate_production_out_root(tmp_path / "outside", repo_root=REPO)
    with pytest.raises(ValueError):
        d7f.validate_production_out_root(WS / "wrong_name", repo_root=REPO)
    assert d7f.validate_production_out_root(
        WS / (d7f.OUT_ROOT_PREFIX + "abc"), repo_root=REPO).name.endswith("abc")


def _copy_root(src, dst):
    return Path(shutil.copytree(str(src), str(dst)))


def test_w02_verifier_tamper_cases(tmp_path):
    good = tmp_path / "w02_good"
    _full_run(tmp_path, sampler=_parity_sampler(), out_name=good)
    report = d7f.verify_root(good)
    assert report["ok"] and report["records"] == 128, report

    record_lines = (good / "decoder_records.csv").read_text(
        encoding="utf-8").splitlines()

    root = _copy_root(good, tmp_path / "t_dup")
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines + [record_lines[1]]) + "\n", encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_missing")
    kept = [line for line in record_lines if not line.startswith("63,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_unpaired")
    kept = [line for line in record_lines if not line.startswith("3,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_exact")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["exact"] = "False" if rows[0]["exact"] == "True" else "True"
    _rewrite_csv(root / "decoder_records.csv", rows, d7f.RECORD_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_syndrome")
    rows = _read_csv(root / "decoder_records.csv")
    rows[1]["syndrome_ok"] = ("False" if rows[1]["syndrome_ok"] == "True"
                              else "True")
    _rewrite_csv(root / "decoder_records.csv", rows, d7f.RECORD_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    # Provenance-gate tampers: flipping the admitting token (or the cached
    # eligibility bit) breaks the gate recompute.
    root = _copy_root(good, tmp_path / "t_prov")
    rows = _read_csv(root / "decoder_records.csv")
    row = next(r for r in rows if r["role"] == "SOURCE")
    row["belief_provenance"] = "PRIOR_ONLY"
    _rewrite_csv(root / "decoder_records.csv", rows, d7f.RECORD_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_elig")
    rows = _read_csv(root / "decoder_records.csv")
    row = next(r for r in rows if r["role"] == "SOURCE")
    row["transfer_eligible"] = "False"
    _rewrite_csv(root / "decoder_records.csv", rows, d7f.RECORD_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    # Both-layer AND tamper: flipping one layer exact without the AND breaks.
    root = _copy_root(good, tmp_path / "t_and")
    rows = _read_csv(root / "arm_pairs.csv")
    row = next(r for r in rows)
    row["l1_exact"] = "False" if row["l1_exact"] == "True" else "True"
    _rewrite_csv(root / "arm_pairs.csv", rows, d7f.PAIR_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_pairs_count")
    rows = _read_csv(root / "arm_pairs.csv")
    _rewrite_csv(root / "arm_pairs.csv", rows[:-1], d7f.PAIR_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_strata")
    rows = _read_csv(root / "stratum_summary.csv")
    rows[0]["stratum_label"] = "REVERSE_REGRESSION"
    _rewrite_csv(root / "stratum_summary.csv", rows, d7f.STRATUM_FIELDS)
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_terminal")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert summary["terminal"] != d7f.T_STRONG
    summary["terminal"] = d7f.T_STRONG
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_wall")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["stored_wall_s"] = float(summary["stored_wall_s"]) + 1.0
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_manifest")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["lambda_star"] = 1.0
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_extra")
    (root / "extra.txt").write_text("x", encoding="utf-8")
    assert d7f.verify_root(root)["ok"] is False

    # A legitimately truncated root (watchdog stop) still verifies.
    stopped = tmp_path / "w02_stopped"
    _full_run(tmp_path, clock=_ScriptedClock([120.5] + [0.0] * 127),
              out_name=stopped)
    assert d7f.verify_root(stopped)["ok"] is True


def test_w03_scalar_only_schema_and_forbidden_payloads(tmp_path):
    out = tmp_path / "w03"
    _full_run(tmp_path, out_name=out)
    forbidden_name = re.compile(
        r"belief_|prior|symbol|syndrome_vec|vector|digest| Likelihood", re.I)
    for field in d7f.RECORD_FIELDS + d7f.PAIR_FIELDS + d7f.STRATUM_FIELDS:
        low = field.lower()
        assert "vector" not in low and "digest" not in low, field
        assert "prior" not in low or "provenance" in low, field
    assert "belief_provenance" in d7f.RECORD_FIELDS
    assert "belief_shape_ok" in d7f.RECORD_FIELDS
    # No payload-looking values anywhere in the seven files.
    for name in d7f.SEVEN_FILES:
        text = (out / name).read_text(encoding="utf-8")
        assert "array(" not in text and "dtype" not in text, name
    for row in _read_csv(out / "decoder_records.csv"):
        for key in ("belief_max_prob", "belief_mean_true_p",
                    "belief_mean_entropy"):
            assert row[key] == "" or float(row[key]) == float(row[key])
    assert forbidden_name.search("belief_provenance") is not None  # guard sanity
    pairs = _read_csv(out / "arm_pairs.csv")
    assert all("both_layers_exact" in p for p in pairs)


# ==========================================================================
# R01: protected roots, no-overwrite, authorization-false state
# ==========================================================================

def test_r01_protected_state_and_no_production_read(tmp_path, monkeypatch):
    workspace_before = sorted(p.name for p in WS.iterdir())
    model_f_before = _dir_meta(MODEL_F_ROOT)
    d7c_before = _dir_meta(D7C_ROOT)
    d7b_before = _dir_meta(D7B_ROOT)
    d7e_before = _dir_meta(D7E_ROOT)
    assert d7e_before is not None  # accepted D7-E root exists and is immutable
    assert list(WS.glob(d7f.OUT_ROOT_PREFIX + "*")) == []
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert not (WS / "v72p2d5_g2" / "20260906_r1").exists()

    def _raiser(*args, **kwargs):
        raise AssertionError("Model-F loader must not run in qualification")

    monkeypatch.setattr(d5, "_load_model_f_input_or_blocked", _raiser)
    monkeypatch.setattr(d7c, "_default_model_f_loader", _raiser)
    _full_run(tmp_path, out_name=tmp_path / "r01")

    assert sorted(p.name for p in WS.iterdir()) == workspace_before
    assert list(WS.glob(d7f.OUT_ROOT_PREFIX + "*")) == []
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert _dir_meta(D7C_ROOT) == d7c_before
    assert _dir_meta(D7E_ROOT) == d7e_before
    if d7b_before is not None:
        assert _dir_meta(D7B_ROOT) == d7b_before
    assert d7f._EXECUTION_CONSUMED is False
    state = d7f.read_cycle_state(D7F_CYCLE_STATE)
    for key in ("d7f_execution_authorized", "decoder_executed",
                "result_created", "implementation_authorized",
                "formal_execution_authorized", "synthetic_execution_authorized",
                "real_execution_authorized", "scientific_promotion",
                "plan_accepted", "g1_authorized", "g2_authorized"):
        assert state.get(key) is False, (key, state.get(key))
    # Protected roots refuse before any decoder contact.
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    for protected in (D7E_ROOT, D7C_ROOT,
                      REPO / "comparison_bench" / "outputs_comparison" / "x",
                      REPO / "results" / "x"):
        with pytest.raises((ValueError, FileExistsError)):
            d7f.run_reverse_order_discriminator(
                out_root=protected, joint=_uniform_joint(),
                block_sampler=_parity_sampler(),
                decoder_fns={"SOURCE": decoder, "TARGET": decoder},
                state={"d7f_execution_authorized": True}, repo_root=REPO)
    assert events == []


# ==========================================================================
# X01-X05: launch isolation, sentinels, independence, regressions
# ==========================================================================

def test_x01_lazy_import_help_dry_run_and_unauthorized_isolation(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    assert _run_cli([str(RUNNER), "--help"], cwd=REPO).returncode == 0
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-F" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("slots=128") and len(lines) == 129
    assert lines[1].split()[3:5] == ["FORWARD_L1_TO_L2", "SOURCE"]
    assert lines[2].split()[3:5] == ["FORWARD_L1_TO_L2", "TARGET"]
    assert lines[3].split()[3:5] == ["REVERSE_L2_TO_L1", "SOURCE"]
    assert lines[4].split()[3:5] == ["REVERSE_L2_TO_L1", "TARGET"]
    assert lines[128].split()[3:5] == ["REVERSE_L2_TO_L1", "TARGET"]
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7f_x01')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "print('X01_OK')\n")
    result = subprocess.run([sys.executable, "-c", probe, str(RUNNER)],
                            cwd=str(external), env=_clean_env(),
                            capture_output=True, text=True, timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "X01_OK" in result.stdout

    target = WS / (d7f.OUT_ROOT_PREFIX + "unauthorized_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7f.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3
    assert "not authorized" in result.stdout
    assert not target.exists()
    bad_shape = tmp_path / "bad_shape"
    result = _run_cli([str(RUNNER), "--model-f-root", d7f.MODEL_F_ROOT,
                       "--out-root", str(bad_shape)], cwd=REPO)
    assert result.returncode == 3 and "refused" in result.stdout
    assert not bad_shape.exists()
    missing = tmp_path / "no_such_root"
    result = _run_cli([str(RUNNER), "--verify", str(missing)], cwd=REPO)
    assert result.returncode == 2 and "VERIFY_FAIL" in result.stdout
    good = tmp_path / "x01_good"
    _full_run(tmp_path, out_name=good)
    result = _run_cli([str(RUNNER), "--verify", str(good)], cwd=REPO)
    assert result.returncode == 0 and "VERIFY_OK" in result.stdout


def test_x02_external_cwd_dual_decoder_and_loader_sentinels(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    out_root = tmp_path / "never_created"
    code = r'''
import pathlib
import runpy
import sys

import numpy as np

g = runpy.run_path(sys.argv[1], run_name="d7f_x02")
mod = g["_mod"]
external = pathlib.Path(sys.argv[2])
out_root = pathlib.Path(sys.argv[3])
from comparison_bench.formal_ir import v35_algorithm_development as v35

fns = mod.bind_row_layered_decoders()
assert fns["SOURCE"].target is v35.decode_row_layered_fftqspa
assert fns["TARGET"].target is v35.decode_row_layered_fftqspa
assert fns["SOURCE"].__name__ == "source"
assert fns["TARGET"].__name__ == "target"


class Sentinel(BaseException):
    pass


events = []
h = np.zeros((2, 4), dtype=np.uint8)
h[0, :2] = [1, 7]
h[1, 2:] = [3, 1]
prior = np.full((4, 32), 1.0 / 32.0)
syn = np.array([5, 17], dtype=np.uint8)


def sentinel(tag):
    def dec(hh, pp, ss):
        events.append((tag, np.asarray(hh).shape, np.asarray(pp).shape,
                       np.asarray(ss).shape))
        raise Sentinel(tag)
    return dec


for key, tag in (("SOURCE", "src"), ("TARGET", "tgt")):
    try:
        mod.dispatch_decoder(key, {key: sentinel(tag)}, h, prior, syn)
    except Sentinel as exc:
        assert str(exc) == tag
    else:
        raise AssertionError("sentinel not reached for %s" % key)

try:
    mod.dispatch_decoder("NOPE", {}, h, prior, syn)
except ValueError:
    pass
else:
    raise AssertionError("unknown decoder key must refuse")

assert mod._default_model_f_loader is mod.d7e._default_model_f_loader
assert events == [("src", (2, 4), (4, 32), (2,)),
                  ("tgt", (2, 4), (4, 32), (2,))], events
assert not external.joinpath("never_created").exists()
assert not out_root.exists()
print("X02_OK")
'''
    result = subprocess.run(
        [sys.executable, "-c", code, str(RUNNER), str(external), str(out_root)],
        cwd=str(external), env=_clean_env(), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "X02_OK" in result.stdout

    # A raising Model-F loader stays silent once the joint is injected, and a
    # wrong model-f root refuses before any decoder bind.
    def _raising_loader(root):
        raise AssertionError("Model-F loader must not run with joint injected")

    out = tmp_path / "x02_loader"
    _full_run(tmp_path, out_name=out, joint=_uniform_joint(),
              sampler=_parity_sampler())
    assert (out / "decoder_records.csv").exists()
    with pytest.raises(d7f.PreflightBlocked):
        d7f.prepare_inputs(model_f_root="workspace/elsewhere",
                           model_f_loader=_raising_loader,
                           block_sampler=_parity_sampler(), repo=REPO)
    assert d7f.model_f_root_matches(d7f.MODEL_F_ROOT, repo_root=REPO) is True
    assert d7f.model_f_root_matches("workspace/elsewhere",
                                    repo_root=REPO) is False


def test_x03_d7c_d7d_import_and_behavior_independence():
    assert "v72p2d7_gf32_schedule_discriminator" not in sys.modules
    assert "schedule_discriminator" not in CORE_PATH.read_text(
        encoding="utf-8")
    before = (d7c.MAX_CALLS, d7c.CONDITIONS, d7c.LAMBDA_STAR,
              len(d7c.frozen_identities()))
    assert before == (128, ("L1_MARGINAL", "L1_ORACLE_U2", "L2_MARGINAL",
                            "L2_ORACLE_U1"), 137.3823795883264, 128)
    rng = np.random.default_rng(20260915)
    raw = rng.random((Q, Q, 4)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    block = {"bob": np.array([0, 1, 2, 3]),
             "u1": np.array([1, 2, 3, 4]), "u2": np.array([5, 6, 7, 8]),
             "alice": np.array([37, 70, 103, 136])}
    ref_l1 = d7c.condition_prior_qn(joint, "L1_MARGINAL", block).copy()
    ref_l2 = d7c.condition_prior_qn(joint, "L2_MARGINAL", block).copy()
    assert np.array_equal(d7f.condition_prior_qn(joint, "L1_MARGINAL", block),
                          ref_l1)
    assert np.array_equal(d7f.condition_prior_qn(joint, "L2_MARGINAL", block),
                          ref_l2)
    assert "v72p2d7_gf32_schedule_discriminator" not in sys.modules


def test_x04_d7e_bp_provenance_regression():
    # Narrow D7-E/BP contract still enforced through the D7-F gate.
    assert d7f.CHECK_UPDATED == v35.BELIEF_PROVENANCE_CHECK_UPDATED == "CHECK_UPDATED"
    assert v35.BELIEF_PROVENANCE_PRIOR_ONLY == "PRIOR_ONLY"
    assert (v35.BELIEF_PROVENANCE_WARM_START_UNSPECIFIED
            == "WARM_START_UNSPECIFIED")
    assert d7f.PRIOR_ONLY_CURRENT_BELIEF == "PRIOR_ONLY_CURRENT_BELIEF"
    assert d7f.CHECK_UPDATED_CURRENT_BELIEF == "CHECK_UPDATED_CURRENT_BELIEF"
    for token in ("PRIOR_ONLY", None, "WARM_START_UNSPECIFIED",
                  "SOME_FUTURE_TOKEN"):
        assert d7f.check_source_eligibility(
            status="ok", finite=True, belief_shape_ok=True,
            provenance=token) == d7e.check_source_eligibility(
                status="ok", finite=True, belief_shape_ok=True,
                provenance=token) == (False, "PROVENANCE_BLOCKED")
    assert d7f.check_source_eligibility(
        status="ok", finite=True, belief_shape_ok=True,
        provenance="CHECK_UPDATED") == (True, "ELIGIBLE")
    # The D7-F gate is the D7-E gate object (narrow import intact).
    assert d7f.check_source_eligibility is d7e.check_source_eligibility
    assert d7f.require_check_updated is d7e.require_check_updated
    assert d7f.belief_provenance_error is d7e.belief_provenance_error
    with pytest.raises(d7f.belief_provenance_error()):
        d7f.require_check_updated("PRIOR_ONLY", consumer="probe")
    d7f.require_check_updated("CHECK_UPDATED", consumer="probe")


def _inner_pytest(files, *, extra=(), basetemp):
    return subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider",
         "--basetemp", str(basetemp), *extra],
        cwd=str(REPO), env=dict(os.environ), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)


def test_x05_bp_milestone_regression(tmp_path):
    base = tmp_path / "inner"
    base.mkdir()
    result = _inner_pytest([str(BP_FILE)], basetemp=base / "bp")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "23 passed" in result.stdout


# ==========================================================================
# A2: WSL VmHWM-only RSS telemetry (fail-closed; injected fixtures only)
# ==========================================================================

def _a2_status(*lines):
    return ("Name:\tpython\n" + "".join(line + "\n" for line in lines)
            + "VmRSS:\t    9999 kB\n")


def test_a2_01_valid_vmhwm_conversion():
    assert d7f.parse_vmhwm_rss_bytes is d7e.parse_vmhwm_rss_bytes
    assert d7f.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t   48256 kB")) == 48256 * 1024
    assert d7f.parse_vmhwm_rss_bytes("VmHWM: 1 kB\n") == 1024
    assert d7f.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t123456 kB")) == 123456 * 1024
    # Leading zeros still denote a positive integer.
    assert d7f.parse_vmhwm_rss_bytes("VmHWM: 007 kB\n") == 7 * 1024


def test_a2_02_whitespace_only_where_linux_requires():
    for line in ("VmHWM: 123 kB", "VmHWM:\t123 kB", "VmHWM:\t   123 kB",
                 "VmHWM: \t \t123 kB"):
        assert d7f.parse_vmhwm_rss_bytes(line + "\n") == 123 * 1024, line
    for line in (" VmHWM: 123 kB", "\tVmHWM: 123 kB", "VmHWM : 123 kB",
                 "VmHWM:123 kB", "VmHWM: 123\tkB", "VmHWM: 123  kB",
                 "VmHWM: 123 kB ", "VmHWM: 123 kB",
                 "VmHWM: 123 kB"):
        assert d7f.parse_vmhwm_rss_bytes(line + "\n") is None, repr(line)


def test_a2_03_missing_field():
    assert d7f.parse_vmhwm_rss_bytes("Name:\tpython\nVmRSS:\t 1 kB\n") is None
    assert d7f.parse_vmhwm_rss_bytes("") is None
    assert d7f.parse_vmhwm_rss_bytes(None) is None
    assert d7f.parse_vmhwm_rss_bytes(b"VmHWM: 1 kB\n") is None
    assert d7f.parse_vmhwm_rss_bytes("VmHWMExtra: 123 kB\n") is None


def test_a2_04_duplicate_field():
    assert d7f.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t 123 kB", "VmHWM:\t 123 kB")) is None
    # A valid line plus a malformed same-field line still blocks.
    assert d7f.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t 123 kB", "VmHWM: nope kB")) is None


def test_a2_05_wrong_unit():
    for unit in ("MB", "KB", "kb", "K", "k", "B", "bytes", "kBB"):
        line = "VmHWM: 123 %s" % unit
        assert d7f.parse_vmhwm_rss_bytes(line + "\n") is None, line
    assert d7f.parse_vmhwm_rss_bytes("VmHWM: 123\n") is None


def test_a2_06_malformed_signed_zero_negative():
    for line in ("VmHWM: 12.5 kB", "VmHWM: 1e4 kB", "VmHWM: +123 kB",
                 "VmHWM: -123 kB", "VmHWM: 0 kB", "VmHWM: 000 kB",
                 "VmHWM: abc kB", "VmHWM:  kB", "VmHWM: kB",
                 "VmHWM 123 kB", "VmHWM:", "VmHWM: 12,345 kB",
                 "VmHWM: 0x10 kB", "VmHWM: １２３ kB",
                 "６mHWM: 123 kB", "VmHWM: 123 ｋB"):
        assert d7f.parse_vmhwm_rss_bytes(line + "\n") is None, repr(line)


def test_a2_07_read_failure_and_fresh_read_per_call(tmp_path, monkeypatch):
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH",
                        str(tmp_path / "does_not_exist"))
    assert d7f.get_rss_bytes() is None
    fixture = tmp_path / "status"
    fixture.write_text("VmHWM: 100 kB\n", encoding="utf-8")
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7f.get_rss_bytes() == 100 * 1024
    # No caching: a rewritten file is re-read on the next probe call.
    fixture.write_text("VmHWM: 200 kB\n", encoding="utf-8")
    assert d7f.get_rss_bytes() == 200 * 1024


def test_a2_08_overflow_rejection_without_wrapping():
    assert d7f.parse_vmhwm_rss_bytes(
        "VmHWM: 9999999999999999999 kB\n") is None  # 19 digits
    assert d7f.parse_vmhwm_rss_bytes(
        "VmHWM: %s kB\n" % ("9" * 100,)) is None
    assert d7f.parse_vmhwm_rss_bytes(
        "VmHWM: 1%s kB\n" % ("0" * 18,)) is None  # 19 digits
    edge = "9" * 18
    assert d7f.parse_vmhwm_rss_bytes(
        "VmHWM: %s kB\n" % (edge,)) == int(edge) * 1024


def test_a2_09_bogus_ru_maxrss_cannot_affect_wsl_result(tmp_path,
                                                        monkeypatch):
    assert not hasattr(d7f, "_read_ru_maxrss")  # legacy fallback deleted
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8")
        assert "ru_maxrss" not in source, path.name
        assert "import resource" not in source, path.name
    import resource
    calls = []

    def _bogus_ru(who):
        calls.append(who)

        class _Bogus(object):
            ru_maxrss = 4026531  # ~3.84 GiB in KiB: implausible vs VmHWM

        return _Bogus()

    monkeypatch.setattr(resource, "getrusage", _bogus_ru)
    fixture = tmp_path / "status"
    fixture.write_text(_a2_status("VmHWM:\t 123456 kB"), encoding="utf-8")
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7f.get_rss_bytes() == 123456 * 1024
    assert calls == []


def test_a2_10_below_limit_permits_existing_path(tmp_path, monkeypatch):
    mib = 256 * 1024 * 1024
    fixture = tmp_path / "status"
    fixture.write_text(_a2_status("VmHWM:\t 262144 kB"), encoding="utf-8")
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7f.get_rss_bytes() == mib
    first = _full_run(tmp_path, rss_probe=d7f.get_rss_bytes,
                      out_name=tmp_path / "a2below")
    second = _full_run(tmp_path, rss_probe=lambda: mib,
                       out_name=tmp_path / "a2below_ref")
    assert first["terminal"] == second["terminal"]
    assert first["records"] == second["records"] == 128


def test_a2_11_limit_boundary_blocks(tmp_path, monkeypatch):
    limit_kb = d7f.RSS_LIMIT_BYTES // 1024
    fixture = tmp_path / "status"
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    # One KiB below the strict <2 GiB limit permits a full run.
    fixture.write_text(_a2_status("VmHWM: %d kB" % (limit_kb - 1,)),
                       encoding="utf-8")
    assert d7f.get_rss_bytes() == d7f.RSS_LIMIT_BYTES - 1024
    result = _full_run(tmp_path, rss_probe=d7f.get_rss_bytes,
                       out_name=tmp_path / "a2lim_ok")
    assert result["records"] == 128 and result["terminal"] != d7f.T_RESOURCE
    # Equal-to and above the limit block at the first call.
    for kb in (limit_kb, limit_kb * 2):
        fixture.write_text(_a2_status("VmHWM: %d kB" % (kb,)),
                           encoding="utf-8")
        out = tmp_path / ("a2lim_%d" % (kb,))
        result = _full_run(tmp_path, rss_probe=d7f.get_rss_bytes,
                           out_name=out)
        assert result["terminal"] == d7f.T_RESOURCE, kb
        assert result["records"] == 1, kb
        assert d7f.verify_root(out)["ok"] is True


def test_a2_12_none_blocks_preflight_before_first_decoder(tmp_path,
                                                          monkeypatch):
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    out = tmp_path / "a2pre"
    with pytest.raises(d7f.PreflightBlocked) as excinfo:
        d7f.run_reverse_order_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7f_execution_authorized": True},
            rss_probe=lambda: None, repo_root=REPO)
    assert excinfo.value.terminal == d7f.T_PRE_EXEC and events == []
    assert not out.exists()
    # A VmHWM-backed None (missing-field fixture) blocks identically.
    fixture = tmp_path / "status"
    fixture.write_text("Name:\tpython\nVmRSS:\t 1 kB\n", encoding="utf-8")
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    out2 = tmp_path / "a2pre2"
    with pytest.raises(d7f.PreflightBlocked):
        d7f.run_reverse_order_discriminator(
            out_root=out2, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7f_execution_authorized": True},
            rss_probe=d7f.get_rss_bytes, repo_root=REPO)
    assert events == [] and not out2.exists()


def test_a2_13_midrun_none_or_overlimit_keeps_resource_terminal(tmp_path):
    ok = 256 * 1024 * 1024
    for bad in (None, 3 * 1024**3):
        state = {"n": 0}

        def seq_probe(state=state, bad=bad):
            state["n"] += 1
            return ok if state["n"] <= 5 else bad

        source = _scripted_source(["CHECK_UPDATED"] * 64)
        target = _argmax_target()
        out = tmp_path / ("a2mid_%s" % (bad,))
        result = d7f.run_reverse_order_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": source, "TARGET": target},
            state={"d7f_execution_authorized": True},
            rss_probe=seq_probe, command_str="fake qualification",
            repo_root=REPO)
        assert result["terminal"] == d7f.T_RESOURCE, bad
        # Preflight plus slots 1-4 probe ok; the 5th slot's probe goes bad,
        # is recorded once, and stops the run with no retry.
        assert result["records"] == 5, bad
        assert source.calls["k"] + target.calls["n"] == 5, bad
        assert d7f.verify_root(out)["ok"] is True


def test_a2_14_rss_bytes_schema_invariant(tmp_path, monkeypatch):
    assert d7f.RECORD_FIELDS.count("rss_bytes") == 1
    fixture = tmp_path / "status"
    fixture.write_text(_a2_status("VmHWM:\t 262144 kB"), encoding="utf-8")
    monkeypatch.setattr(d7f, "_PROC_SELF_STATUS_PATH", str(fixture))
    out = tmp_path / "a2schema"
    _full_run(tmp_path, rss_probe=d7f.get_rss_bytes, out_name=out)
    rows = _read_csv(out / "decoder_records.csv")
    assert list(rows[0].keys()) == d7f.RECORD_FIELDS
    assert {row["rss_bytes"] for row in rows} == {str(256 * 1024 * 1024)}
    assert d7f.verify_root(out)["ok"] is True
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rss_limit_bytes"] == 2 * 1024**3


def test_a2_15_cli_surface_zero_decoder_zero_root(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-F" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("slots=128") and len(lines) == 129
    target = WS / (d7f.OUT_ROOT_PREFIX + "a2_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7f.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3 and "not authorized" in result.stdout
    assert not target.exists()
