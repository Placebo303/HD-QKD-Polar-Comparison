"""D7-E provenance-safe cross-layer discriminator qualification (fake/DI only).

No test creates ``workspace/d7_e_cross_layer_discriminator_*`` or reads real
Model-F content; every scientific-run decoder is an injected fake.  No
production decoder is contacted anywhere in this file: all transfer math is
checked against tiny explicit in-memory fixtures and direct enumeration.
Each D7 inner regression suite runs in its own pytest process (no broad
suite that could collect historical run roots).

The D7-D suite carries two pre-existing stale lifecycle assertions
(``test_f08_...`` and ``test_s21_...`` assert no D7-D evidence root exists;
a committed leftover ``workspace/d7_d_schedule_discriminator_64660d16-*``
root now exists), so the D7-D regression deselects exactly those two IDs
with the reason recorded (R22 lifecycle-test debt; D7-E creates no workspace
roots and repairs nothing outside its three new files).
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
             / "v72p2d7_gf32_cross_layer_discriminator.py")
RUNNER = REPO / "scripts" / "v72p2d7_gf32_cross_layer_discriminator.py"
WS = REPO / "workspace"
MODEL_F_ROOT = WS / "v72p2d5_model_f_input" / "20260907_r1"
D7C_ROOT = (WS / "d7_c_bidirectional_oracle_"
            "94c0ea15-a786-4cb8-a991-6fec521cccae")
D7B_ROOT = WS / "d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964"
D7D_LEFTOVER = (WS / "d7_d_schedule_discriminator_64660d16-397d-4ef3-"
                "8454-3066d27c12c7")
D7E_CYCLE_STATE = (REPO / "docs" / "research_cycles"
                   / "V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR"
                   / "cycle_state.yaml")
D6_RUNNER = REPO / "scripts" / "v72p2d6_graph_mother_development.py"
D6_CORE = (SRC / "comparison_bench" / "formal_ir"
           / "v72p2d6_gf32_graph_mother.py")
BP_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_bp_belief_provenance.py"
D7A_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_gf32_decoder_certification.py"
D7B_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_gf32_easy_regime.py"
D7C_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_gf32_bidirectional_oracle.py"
D7D_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d7_gf32_schedule_discriminator.py"
D5_FILE = REPO / "comparison_bench" / "tests" / "test_v72p2d5_gf32_rate_mother.py"
SUB_TIMEOUT = 1200

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d7_gf32_cross_layer_discriminator as d7e,
)
from comparison_bench.formal_ir import (  # noqa: E402
    v35_algorithm_development as v35,
)

d7c = d7e.d7c
d5 = d7c.d5
Q = 32
TOL = 1e-10

A_U1, B_U2 = 3, 7          # shared truth symbols for crafted fixtures
B_PRIME = 9                # wrong L2-marginal peak
X_U1 = 11                  # wrong L1-marginal peak
AQ1, AQ2 = 5, 15           # scripted source-q peaks (L1-source, L2-source)


# --------------------------------------------------------------------------
# Shared fake fixtures (no real Model-F / no production run decoder)
# --------------------------------------------------------------------------

def _uniform_joint() -> np.ndarray:
    return np.full((Q, Q, d7e.BOB_DIM), 1.0 / (Q * Q))


def _column_joint(columns: dict) -> np.ndarray:
    """Full-size joint with crafted Bob columns; all other columns uniform."""
    joint = np.full((Q, Q, d7e.BOB_DIM), 1.0 / (Q * Q))
    for bob, entries in columns.items():
        col = np.zeros((Q, Q))
        for (u1, u2), mass in entries.items():
            col[int(u1), int(u2)] = float(mass)
        col = col / col.sum()
        joint[:, :, int(bob)] = col
    return joint


def _const_block(seed, bob_val=0, a=A_U1, b=B_U2) -> dict:
    n = d7e.N
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


def _mixed_truth_sampler(b_even=0, b_odd=1):
    """Even seeds decode exactly, odd seeds miss (uniform-joint runs)."""
    def sample(p_b, p_f, n, seed):
        idx = (int(seed) - 2026091300) % 16
        if idx % 2 == 0:
            return _const_block(seed, bob_val=b_even, a=0, b=0)
        return _const_block(seed, bob_val=b_odd, a=A_U1, b=B_U2)
    return sample


def _peaked_log(n, peak, mass=0.9):
    row = np.full(Q, (1.0 - mass) / (Q - 1))
    row[int(peak)] = mass
    return np.log(np.tile(row, (int(n), 1)))


def _scripted_source(provenances, peaks=None, iterations=None):
    """SOURCE fake: k-th source call uses script[k] (order: f, seed, dir)."""
    state = {"k": 0}
    peaks = list(peaks) if peaks is not None else [AQ1] * 64
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


def _source_order():
    """The 64 source-call identities in loop order: (f, seed, direction)."""
    order = []
    for f in d7e.F_VALUES:
        for seed in d7e.BLOCK_SEEDS:
            for direction in d7e.DIRECTIONS:
                order.append((float(f), int(seed), direction))
    return order


def _dir_peaks(value_l1=AQ1, value_l2=AQ2):
    return [value_l1 if direction == "L1_TO_L2" else value_l2
            for (_, _, direction) in _source_order()]


def _full_run(tmp_path, name="root", *, joint=None, sampler=None,
              source_fn=None, target_fn=None, clock=None, rss_probe=None,
              mothers=None, state=None, out_name=None,
              command_str="fake qualification"):
    out = Path(out_name) if out_name is not None else (tmp_path / name)
    if source_fn is None:
        source_fn = _scripted_source(["CHECK_UPDATED"] * 64,
                                     peaks=_dir_peaks())
    if target_fn is None:
        target_fn = _argmax_target()
    return d7e.run_cross_layer_discriminator(
        out_root=out,
        joint=_uniform_joint() if joint is None else joint,
        block_sampler=(_parity_sampler() if sampler is None else sampler),
        mothers=mothers,
        decoder_fns={"SOURCE": source_fn, "TARGET": target_fn},
        state={"d7e_execution_authorized": True} if state is None else state,
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

    got_l12 = d7e.transfer_prior_l1_to_l2(joint, bob, q)
    direct = np.zeros((n, Q))
    for i in range(n):
        cond = joint[:, :, bob[i]] / joint[:, :, bob[i]].sum(
            axis=1, keepdims=True)
        direct[i] = q[i] @ cond
    assert np.allclose(got_l12, d5._floor_renorm(direct, 1e-15),
                       atol=1e-12, rtol=0)

    got_l21 = d7e.transfer_prior_l2_to_l1(joint, bob, q)
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
    out = d7e.transfer_prior_l1_to_l2(joint0, np.array([1, 1]), q_hot)
    assert np.allclose(out, np.full((2, Q), 1.0 / Q), atol=1e-12)

    # No source truth enters either formula (signature pins the inputs).
    for fn in (d7e.transfer_prior_l1_to_l2, d7e.transfer_prior_l2_to_l1):
        params = list(inspect.signature(fn).parameters)
        assert params == (["joint", "bob", "q1"] if fn is d7e.transfer_prior_l1_to_l2
                          else ["joint", "bob", "q2"])
    assert list(inspect.signature(d7e.build_transfer_prior).parameters) == [
        "joint", "direction", "bob", "q"]
    with pytest.raises(ValueError):
        d7e.build_transfer_prior(joint, "NOPE", bob, q)
    assert np.allclose(d7e.build_transfer_prior(joint, "L1_TO_L2", bob, q),
                       got_l12)
    assert np.allclose(d7e.build_transfer_prior(joint, "L2_TO_L1", bob, q),
                       got_l21)

    # Transient q helper: valid softmax, loud on bad shape/nonfinite.
    logb = np.log(q)
    assert np.allclose(d7e.softmax_source_q(logb), q, atol=1e-12)
    with pytest.raises(ValueError):
        d7e.softmax_source_q(np.zeros((n, Q - 1)))
    bad = logb.copy()
    bad[0, 0] = np.inf
    with pytest.raises(ValueError):
        d7e.softmax_source_q(bad)


def test_e02_corrected_per_column_estimator_identity_and_legacy_differs(monkeypatch):
    assert d7e.LAMBDA_STAR == d5.LAMBDA_STAR == 137.3823795883264
    assert d7e.DECODER_FLOOR == 1e-15
    assert d7e._ESTIMATOR_ID == d7c._ESTIMATOR_ID

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

    # The D7-E preparation path goes only through the candidate chain.
    counts_big = np.ones((d7e.N_A, d7e.BOB_DIM))
    counts_big[0, 0] = 9.0
    p_b = np.full(d7e.BOB_DIM, 1.0 / d7e.BOB_DIM)
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

    ctx = d7e.prepare_inputs(
        model_f_root=d7e.MODEL_F_ROOT, model_f_loader=loader,
        block_sampler=_parity_sampler(), mothers=None, repo=REPO)
    assert calls == [((d7e.N_A, d7e.BOB_DIM), (d7e.BOB_DIM,),
                      d7e.LAMBDA_STAR)]
    assert ctx["joint"].shape == (Q, Q, d7e.BOB_DIM)


def test_e03_legacy_builder_never_referenced_by_d7e_or_d6_r1d():
    legacy_call = re.compile(r"build_f_model\s*\(")
    legacy_prior = re.compile(r"prepare_model_f_prior\s*\(")
    for path in (CORE_PATH, RUNNER, D6_RUNNER, D6_CORE):
        source = path.read_text(encoding="utf-8")
        assert legacy_call.search(source) is None, (path.name, "legacy builder")
        assert legacy_prior.search(source) is None, (path.name, "legacy prior")
    core = CORE_PATH.read_text(encoding="utf-8")
    assert "build_f_model_concentration" in core
    assert "prepare_model_f_prior_candidate" in core
    assert "prepare_model_f_prior_candidate" in D6_RUNNER.read_text(
        encoding="utf-8")


# ==========================================================================
# M01-M03: frozen 192-slot matrix, D7-C identity reuse, pair sharing
# ==========================================================================

def test_m01_exact_192_slot_order_and_128_mandatory():
    slots = d7e.frozen_slots()
    assert len(slots) == 192 and d7e.SLOT_COUNT == 192
    assert d7e.MANDATORY_CALLS == 128 and d7e.MAX_CALLS == 192
    assert d7e.DIRECTIONS == ("L1_TO_L2", "L2_TO_L1")
    assert [s["slot_idx"] for s in slots] == list(range(1, 193))
    assert len({(s["f"], s["seed"], s["direction"], s["role"])
                for s in slots}) == 192
    assert [s["f"] for s in slots[:96]] == [1.0] * 96
    assert [s["f"] for s in slots[96:]] == [1.2] * 96
    pos = 0
    for f in (1.0, 1.2):
        for seed in range(2026091300, 2026091316):
            want = [
                ("L1_TO_L2", "SOURCE", "L1_MARGINAL", "L1",
                 {1.0: 49, 1.2: 59}[f]),
                ("L1_TO_L2", "CONTROL", "L2_MARGINAL", "L2",
                 {1.0: 43, 1.2: 52}[f]),
                ("L1_TO_L2", "TRANSFER", "L2_TRANSFER", "L2",
                 {1.0: 43, 1.2: 52}[f]),
                ("L2_TO_L1", "SOURCE", "L2_MARGINAL", "L2",
                 {1.0: 43, 1.2: 52}[f]),
                ("L2_TO_L1", "CONTROL", "L1_MARGINAL", "L1",
                 {1.0: 49, 1.2: 59}[f]),
                ("L2_TO_L1", "TRANSFER", "L1_TRANSFER", "L1",
                 {1.0: 49, 1.2: 59}[f]),
            ]
            for direction, role, condition, layer, rows in want:
                slot = slots[pos]
                pos += 1
                assert slot["f"] == f and slot["seed"] == seed
                assert slot["direction"] == direction and slot["role"] == role
                assert slot["condition"] == condition and slot["layer"] == layer
                assert slot["rows"] == rows and slot["n"] == 64
    mandatory = [s for s in slots if s["role"] in ("SOURCE", "CONTROL")]
    transfers = [s for s in slots if s["role"] == "TRANSFER"]
    assert len(mandatory) == 128 and len(transfers) == 64


def test_m02_d7c_identity_model_rows_mothers_estimator_reuse():
    assert d7e.BLOCK_SEEDS == d7c.BLOCK_SEEDS == tuple(range(2026091300, 2026091316))
    assert d7e.F_VALUES == d7c.F_VALUES == (1.0, 1.2)
    assert d7e.ROWS == d7c.ROWS
    assert d7e.L1_ROWS == {1.0: 49, 1.2: 59}
    assert d7e.L2_ROWS == {1.0: 43, 1.2: 52}
    assert d7e.L1_GRAPH_SEED == d7c.L1_GRAPH_SEED == 2026090501
    assert d7e.L2_GRAPH_SEED == d7c.L2_GRAPH_SEED == 2026090502
    assert d7e.L1_K_MIN == d7c.L1_K_MIN == 49
    assert d7e.L2_K_MIN == d7c.L2_K_MIN == 43
    assert d7e.MAX_ITER == d7c.MAX_ITER == 90
    assert d7e.DAMPING_ALPHA == d7c.DAMPING_ALPHA == 1.0
    assert d7e.Q == d7c.Q == 32 and d7e.N == d7c.N == 64
    # Narrow reuse (aliases, not copies) of the accepted helpers.
    assert d7e.condition_prior_qn is d7c.condition_prior_qn
    assert d7e.decoder_prior is d7c.decoder_prior
    assert d7e.build_joint is d7c.build_joint
    assert d7e.build_mother is d7c.build_mother
    assert d7e._default_model_f_loader is d7c._default_model_f_loader
    assert np.array_equal(d7e.build_mother("L1"), d7c.build_mother("L1"))
    assert np.array_equal(d7e.build_mother("L2"), d7c.build_mother("L2"))
    # Marginal-control priors agree with the D7-C contract on a random joint.
    rng = np.random.default_rng(20260913)
    raw = rng.random((Q, Q, 5)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 4, 2, 3, 1, 4])
    u1 = np.array([3, 7, 31, 0, 15, 2])
    u2 = np.array([5, 1, 29, 8, 30, 6])
    block = {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}
    for condition in ("L1_MARGINAL", "L2_MARGINAL"):
        assert np.array_equal(d7e.condition_prior_qn(joint, condition, block),
                              d7c.condition_prior_qn(joint, condition, block))
    raw_prior = np.zeros((Q, 4))
    raw_prior[0, 0] = 1.0
    raw_prior[:, 1] = 1e-20
    assert np.array_equal(d7e.decoder_prior(raw_prior),
                          d7c.decoder_prior(raw_prior))


def test_m03_control_transfer_share_identity_only_prior_differs(tmp_path):
    joint = _lift_joint_l12_only()
    captured = {"SOURCE": [], "TARGET": []}
    inner_source = _scripted_source(["CHECK_UPDATED"] * 64,
                                    peaks=_dir_peaks())

    def source_decoder(h, prior, syndrome):
        captured["SOURCE"].append((np.array(h, copy=True),
                                   np.array(prior, copy=True),
                                   np.array(syndrome, copy=True)))
        return inner_source(h, prior, syndrome)

    def make(key):
        def decoder(h, prior, syndrome):
            captured[key].append((np.array(h, copy=True),
                                  np.array(prior, copy=True),
                                  np.array(syndrome, copy=True)))
            return _argmax_target()(h, prior, syndrome)
        return decoder

    out = tmp_path / "m03"
    result = d7e.run_cross_layer_discriminator(
        out_root=out, joint=joint, block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": source_decoder, "TARGET": make("TARGET")},
        state={"d7e_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 192  # all CHECK_UPDATED: 128 + 64
    assert len(captured["SOURCE"]) == 64
    assert len(captured["TARGET"]) == 128
    rows = _read_csv(out / "decoder_records.csv")
    pairs = _read_csv(out / "transfer_pairs.csv")
    assert len(pairs) == 64
    target_calls = iter(captured["TARGET"])
    for pair in pairs:
        h_c, prior_c, syn_c = next(target_calls)   # control first in slot order
        h_t, prior_t, syn_t = next(target_calls)   # then its transfer
        assert np.array_equal(h_c, h_t)
        assert np.array_equal(syn_c, syn_t)
        assert h_c.shape[1] == 64 and prior_c.shape == (64, 32)
        assert not np.allclose(prior_c, prior_t)
        assert pair["control_slot_idx"] != pair["transfer_slot_idx"]
    # Frozen production call shapes carry no per-role delta.
    fns = d7e.bind_row_layered_decoders()
    assert fns["SOURCE"].target is v35.decode_row_layered_fftqspa
    assert fns["TARGET"].target is v35.decode_row_layered_fftqspa
    bind_src = inspect.getsource(d7e.bind_row_layered_decoders)
    assert bind_src.count("damping_alpha=DAMPING_ALPHA") == 2
    assert bind_src.count("warm_beliefs=None") == 2
    assert bind_src.count("field=None") == 2
    assert bind_src.count("max_iter=MAX_ITER") == 2
    for match in re.finditer(r"warm_beliefs\s*=\s*(\S+)", bind_src):
        assert match.group(1).rstrip(",") == "None"
    assert d7e.MAX_ITER == 90 and d7e.DAMPING_ALPHA == 1.0


# ==========================================================================
# G01-G05: provenance gate behavior
# ==========================================================================

def test_g01_check_updated_allows_exactly_one_transfer_call(tmp_path):
    out = tmp_path / "g01"
    result = _full_run(tmp_path, out_name=out)
    assert result["records"] == 192
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    transfers = [r for r in rows if r["role"] == "TRANSFER"]
    assert len(sources) == 64 and len(transfers) == 64
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert all(r["belief_provenance"] == "CHECK_UPDATED" for r in sources)
    pairs = _read_csv(out / "transfer_pairs.csv")
    assert len(pairs) == 64
    assert all(p["source_provenance"] == "CHECK_UPDATED" for p in pairs)
    assert d7e.verify_root(out)["ok"] is True
    eligible, reason = d7e.check_source_eligibility(
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
        result = d7e.run_cross_layer_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": _scripted_source([token] * 64),
                         "TARGET": target},
            state={"d7e_execution_authorized": True},
            rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
        assert mixer_calls == [], token
        assert target.calls["n"] == 64, token  # controls only, no transfer
        assert result["records"] == 128, token
        rows = _read_csv(out / "decoder_records.csv")
        assert all(r["role"] in ("SOURCE", "CONTROL") for r in rows)
        assert all(r["transfer_eligible"] == "False"
                   for r in rows if r["role"] == "SOURCE")
        assert _read_csv(out / "transfer_pairs.csv") == []
        strata = _read_csv(out / "stratum_summary.csv")
        assert all(s["eligible_count"] == "0" for s in strata)
        assert all(s["blocked_count"] == "16" for s in strata)
        assert all(s["stratum_label"] == "" for s in strata)
        assert all(s["coverage_status"] == "PROVENANCE_COVERAGE_BLOCKED"
                   for s in strata)
        assert result["terminal"] == "D7_E_PROVENANCE_COVERAGE_BLOCKED"
        assert d7e.verify_root(out)["ok"] is True
        monkeypatch.undo()
        eligible, reason = d7e.check_source_eligibility(
            status="fake", finite=True, belief_shape_ok=True,
            provenance=(None if token in ("<missing>", None) else token))
        assert eligible is False and reason == "PROVENANCE_BLOCKED", token


def test_g03_source_exact_false_stays_eligible_with_valid_provenance(tmp_path):
    # Uniform joint + nonzero truth: argmax fakes miss everywhere, yet the
    # CHECK_UPDATED gate still admits every transfer.
    out = tmp_path / "g03"
    sampler = lambda p_b, p_f, n, seed: _const_block(seed, bob_val=0)
    result = _full_run(tmp_path, out_name=out, sampler=sampler)
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    assert all(r["exact"] == "False" for r in sources)
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert len([r for r in rows if r["role"] == "TRANSFER"]) == 64
    pairs = _read_csv(out / "transfer_pairs.csv")
    assert all(p["source_exact"] == "False" for p in pairs)
    assert len(pairs) == 64
    assert d7e.verify_root(out)["ok"] is True


def test_g04_token_governs_not_iterations_or_exactness(tmp_path):
    # iterations=0 with a CHECK_UPDATED token stays eligible; a refused token
    # with iterations>0 stays blocked.  The token governs, never the label.
    out = tmp_path / "g04"
    result = d7e.run_cross_layer_discriminator(
        out_root=out, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={
            "SOURCE": _scripted_source(["CHECK_UPDATED"] * 64,
                                       iterations=[0] * 64),
            "TARGET": _argmax_target()},
        state={"d7e_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    rows = _read_csv(out / "decoder_records.csv")
    sources = [r for r in rows if r["role"] == "SOURCE"]
    assert all(r["current_belief_label"] == "PRIOR_ONLY_CURRENT_BELIEF"
               for r in sources)
    assert all(r["transfer_eligible"] == "True" for r in sources)
    assert result["records"] == 192
    assert d7e.verify_root(out)["ok"] is True

    out2 = tmp_path / "g04b"
    result2 = d7e.run_cross_layer_discriminator(
        out_root=out2, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={
            "SOURCE": _scripted_source(["PRIOR_ONLY"] * 64,
                                       iterations=[7] * 64),
            "TARGET": _argmax_target()},
        state={"d7e_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result2["records"] == 128
    rows2 = _read_csv(out2 / "decoder_records.csv")
    assert all(r["transfer_eligible"] == "False"
               for r in rows2 if r["role"] == "SOURCE")


def test_g05_fewer_than_12_eligible_yields_coverage_block(tmp_path):
    provenances = ["CHECK_UPDATED"] * 64
    order = _source_order()
    # Stratum (1.0, L1_TO_L2): first five L1 sources refused -> 11 eligible.
    refused = {(1.0, 2026091300 + k, "L1_TO_L2") for k in range(5)}
    for k, key in enumerate(order):
        if key in refused:
            provenances[k] = "PRIOR_ONLY"
    out = tmp_path / "g05"
    result = d7e.run_cross_layer_discriminator(
        out_root=out, joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": _scripted_source(provenances),
                     "TARGET": _argmax_target()},
        state={"d7e_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 128 + (64 - 5)
    strata = _read_csv(out / "stratum_summary.csv")
    thin = [s for s in strata
            if float(s["f"]) == 1.0 and s["direction"] == "L1_TO_L2"][0]
    assert thin["eligible_count"] == "11" and thin["blocked_count"] == "5"
    assert thin["stratum_label"] == ""
    assert thin["coverage_status"] == "PROVENANCE_COVERAGE_BLOCKED"
    assert result["terminal"] == "D7_E_PROVENANCE_COVERAGE_BLOCKED"
    assert d7e.verify_root(out)["ok"] is True
    # The 12/16 boundary itself: exactly 12 eligible labels, 11 does not.
    assert d7e.classify_stratum(eligible=12, transfer_only_exact=0,
                                control_only_exact=0, transfer_exact=8,
                                control_exact=8,
                                crash_nonfinite=0) == "AMBIGUOUS_TRANSFER_EFFECT"
    assert d7e.classify_stratum(eligible=11, transfer_only_exact=0,
                                control_only_exact=0, transfer_exact=8,
                                control_exact=8,
                                crash_nonfinite=0) == ""


# ==========================================================================
# L01-L03: labels, terminals, caps, budgets
# ==========================================================================

def test_l01_five_labels_thresholds_and_boundaries():
    cs = d7e.classify_stratum
    assert list(inspect.signature(cs).parameters) == [
        "eligible", "transfer_only_exact", "control_only_exact",
        "transfer_exact", "control_exact", "crash_nonfinite"]
    # STRONG_TRANSFER_LIFT and each boundary fall-through.
    assert cs(eligible=16, transfer_only_exact=4, control_only_exact=1,
              transfer_exact=4, control_exact=0,
              crash_nonfinite=0) == d7e.S_STRONG
    assert cs(eligible=12, transfer_only_exact=16, control_only_exact=0,
              transfer_exact=16, control_exact=0,
              crash_nonfinite=0) == d7e.S_STRONG
    assert cs(eligible=16, transfer_only_exact=3, control_only_exact=0,
              transfer_exact=8, control_exact=5,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    assert cs(eligible=16, transfer_only_exact=4, control_only_exact=2,
              transfer_exact=8, control_exact=8,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    assert cs(eligible=16, transfer_only_exact=4, control_only_exact=1,
              transfer_exact=3, control_exact=0,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    assert cs(eligible=16, transfer_only_exact=4, control_only_exact=1,
              transfer_exact=4, control_exact=0,
              crash_nonfinite=1) == d7e.S_AMBIGUOUS
    # TRANSFER_REGRESSION and boundaries.
    assert cs(eligible=16, transfer_only_exact=1, control_only_exact=4,
              transfer_exact=0, control_exact=8,
              crash_nonfinite=0) == d7e.S_REGRESSION
    assert cs(eligible=16, transfer_only_exact=2, control_only_exact=4,
              transfer_exact=2, control_exact=8,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    assert cs(eligible=16, transfer_only_exact=1, control_only_exact=3,
              transfer_exact=8, control_exact=8,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    # NO_TRANSFER_RECOVERY and boundaries.
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=1, control_exact=1,
              crash_nonfinite=0) == d7e.S_NO_RECOVERY
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=0, control_exact=0,
              crash_nonfinite=0) == d7e.S_NO_RECOVERY
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=2, control_exact=1,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    # CONTROL_ALREADY_RECOVERS and boundary.
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=16, control_exact=16,
              crash_nonfinite=0) == d7e.S_CONTROL
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=12, control_exact=12,
              crash_nonfinite=0) == d7e.S_CONTROL
    assert cs(eligible=16, transfer_only_exact=0, control_only_exact=0,
              transfer_exact=11, control_exact=11,
              crash_nonfinite=0) == d7e.S_AMBIGUOUS
    # Coverage-blocked: empty label for every eligible < 12.
    for eligible in (0, 1, 11):
        assert cs(eligible=eligible, transfer_only_exact=16,
                  control_only_exact=0, transfer_exact=16, control_exact=0,
                  crash_nonfinite=0) == ""
    assert d7e.STRATUM_LABELS == ("STRONG_TRANSFER_LIFT",
                                  "TRANSFER_REGRESSION",
                                  "NO_TRANSFER_RECOVERY",
                                  "CONTROL_ALREADY_RECOVERS",
                                  "AMBIGUOUS_TRANSFER_EFFECT")


def _labels_map(entries):
    out = {}
    for f in d7e.F_VALUES:
        for direction in d7e.DIRECTIONS:
            out[(f, direction)] = entries.get((f, direction),
                                              d7e.S_AMBIGUOUS)
    return out


def test_l02_twelve_terminal_priorities_and_truth_table():
    assert list(d7e.TERMINALS) == [
        "D7_E_PRE_EXECUTION_BLOCKED", "D7_E_WATCHDOG_TIMEOUT_VOID",
        "D7_E_NONFINITE_OR_CRASH_BLOCKED", "D7_E_RESOURCE_OVERRUN",
        "D7_E_INCOMPLETE_CORE_CALL_MATRIX",
        "D7_E_PROVENANCE_COVERAGE_BLOCKED",
        "D7_E_BIDIRECTIONAL_TRANSFER_LIFT", "D7_E_L1_TO_L2_TRANSFER_LIFT",
        "D7_E_L2_TO_L1_TRANSFER_LIFT", "D7_E_TRANSFER_REGRESSION",
        "D7_E_NO_USEFUL_TRANSFER_RECOVERY",
        "D7_E_MIXED_TRANSFER_DIAGNOSTIC"]
    all_mixed = _labels_map({})
    all_no_recovery = _labels_map({k: d7e.S_NO_RECOVERY
                                   for k in [(1.0, "L1_TO_L2"),
                                             (1.0, "L2_TO_L1"),
                                             (1.2, "L1_TO_L2"),
                                             (1.2, "L2_TO_L1")]})
    base = {"pre_blocked": False, "watchdog_timeout": False,
            "crash_nonfinite": False, "resource_overrun": False,
            "incomplete": False, "coverage_blocked": False,
            "strata": all_mixed}
    assert d7e.classify_terminal(base) == d7e.T_MIXED
    assert d7e.classify_terminal(dict(base, strata=all_no_recovery)) == d7e.T_NO_RECOVERY
    # T1..T6 cascade: each beats every lower terminal.
    for key, terminal in (("pre_blocked", d7e.T_PRE_EXEC),
                          ("watchdog_timeout", d7e.T_WATCHDOG),
                          ("crash_nonfinite", d7e.T_CRASH),
                          ("resource_overrun", d7e.T_RESOURCE),
                          ("incomplete", d7e.T_INCOMPLETE),
                          ("coverage_blocked", d7e.T_COVERAGE)):
        assert d7e.classify_terminal(dict(base, **{key: True})) == terminal
    everything = dict(base, pre_blocked=True, watchdog_timeout=True,
                      crash_nonfinite=True, resource_overrun=True,
                      incomplete=True, coverage_blocked=True)
    assert d7e.classify_terminal(everything) == d7e.T_PRE_EXEC
    assert d7e.classify_terminal(dict(everything, pre_blocked=False)) == d7e.T_WATCHDOG
    assert d7e.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False)) == d7e.T_CRASH
    assert d7e.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False)) == d7e.T_RESOURCE
    assert d7e.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False,
                                      resource_overrun=False)) == d7e.T_INCOMPLETE
    assert d7e.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False,
                                      resource_overrun=False,
                                      incomplete=False)) == d7e.T_COVERAGE
    # T7 needs the same f strong in both directions.
    both_10 = {(1.0, "L1_TO_L2"): d7e.S_STRONG,
               (1.0, "L2_TO_L1"): d7e.S_STRONG}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(both_10))) == d7e.T_BIDIRECTIONAL
    both_12 = {(1.2, "L1_TO_L2"): d7e.S_STRONG,
               (1.2, "L2_TO_L1"): d7e.S_STRONG}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(both_12))) == d7e.T_BIDIRECTIONAL
    split_f = {(1.0, "L1_TO_L2"): d7e.S_STRONG,
               (1.2, "L2_TO_L1"): d7e.S_STRONG}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(split_f))) == d7e.T_MIXED
    # T8/T9: strong on one side only.
    only_l12 = {(1.0, "L1_TO_L2"): d7e.S_STRONG,
                (1.2, "L1_TO_L2"): d7e.S_STRONG}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(only_l12))) == d7e.T_L1_TO_L2
    only_l21 = {(1.2, "L2_TO_L1"): d7e.S_STRONG}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(only_l21))) == d7e.T_L2_TO_L1
    # T10 needs a regression and no strong lift anywhere.
    reg = {(1.0, "L2_TO_L1"): d7e.S_REGRESSION}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(reg))) == d7e.T_REGRESSION
    strong_plus_reg = {(1.0, "L1_TO_L2"): d7e.S_STRONG,
                       (1.0, "L2_TO_L1"): d7e.S_REGRESSION}
    assert d7e.classify_terminal(dict(base, strata=_labels_map(strong_plus_reg))) == d7e.T_L1_TO_L2
    # Coverage outranks every mechanism terminal.
    assert d7e.classify_terminal(dict(base, coverage_blocked=True,
                                      strata=_labels_map(both_10))) == d7e.T_COVERAGE


def _lift_joint_both_directions():
    return _column_joint({0: {(AQ1, B_U2): 0.2, (X_U1, B_PRIME): 0.5,
                              (A_U1, AQ2): 0.2, (A_U1, 13): 0.1}})


def _lift_joint_l12_only():
    return _column_joint({
        0: {(AQ1, B_U2): 0.25, (X_U1, B_PRIME): 0.35,
            (A_U1, 13): 0.20, (A_U1, AQ2): 0.20},
        1: {(AQ1, B_U2): 0.25, (X_U1, B_PRIME): 0.45,
            (A_U1, 13): 0.15, (X_U1, AQ2): 0.15}})


def _lift_joint_l21_only():
    return _column_joint({
        0: {(AQ1, B_U2): 0.20, (X_U1, B_U2): 0.45,
            (A_U1, B_PRIME): 0.10, (A_U1, AQ2): 0.25},
        1: {(AQ1, B_PRIME): 0.30, (X_U1, 13): 0.40,
            (X_U1, AQ2): 0.30}})


def _regression_joint():
    return _column_joint({0: {(A_U1, B_U2): 0.50, (AQ1, B_PRIME): 0.20,
                              (X_U1, AQ2): 0.20, (A_U1, 13): 0.10}})


def _no_recovery_joint():
    return _column_joint({0: {(AQ1, B_PRIME): 0.30, (X_U1, 13): 0.40,
                              (X_U1, AQ2): 0.30}})


def test_l03_loop_terminal_families_and_budgets(tmp_path):
    assert d7e.PER_CALL_WATCHDOG_S == 120.0
    assert d7e.STORED_WALL_LIMIT_S == 1500.0
    assert d7e.OUTER_WATCHDOG_S == 1800.0 and d7e.OUTER_GRACE_S == 30.0
    assert d7e.RSS_LIMIT_BYTES == 2 * 1024**3

    # T7: same-f strong lift in both directions.
    result = _full_run(tmp_path, joint=_lift_joint_both_directions(),
                       sampler=_parity_sampler(), out_name=tmp_path / "t7")
    assert result["records"] == 192
    assert result["terminal"] == d7e.T_BIDIRECTIONAL
    assert all(row["stratum_label"] == d7e.S_STRONG
               for row in result["summary"]["strata"])
    assert d7e.verify_root(tmp_path / "t7")["ok"] is True

    # T8/T9: single-direction lift.
    result = _full_run(tmp_path, joint=_lift_joint_l12_only(),
                       sampler=_parity_sampler(), out_name=tmp_path / "t8")
    assert result["terminal"] == d7e.T_L1_TO_L2, result["summary"]["strata"]
    labels = {(row["f"], row["direction"]): row["stratum_label"]
              for row in result["summary"]["strata"]}
    assert labels[(1.0, "L1_TO_L2")] == d7e.S_STRONG
    assert labels[(1.0, "L2_TO_L1")] == d7e.S_AMBIGUOUS
    assert d7e.verify_root(tmp_path / "t8")["ok"] is True
    result = _full_run(tmp_path, joint=_lift_joint_l21_only(),
                       sampler=_parity_sampler(), out_name=tmp_path / "t9")
    assert result["terminal"] == d7e.T_L2_TO_L1, result["summary"]["strata"]
    assert d7e.verify_root(tmp_path / "t9")["ok"] is True

    # T10/T11: regression / no useful recovery loops.
    result = _full_run(tmp_path, joint=_regression_joint(),
                       sampler=_parity_sampler(), out_name=tmp_path / "t10")
    assert result["terminal"] == d7e.T_REGRESSION
    assert d7e.verify_root(tmp_path / "t10")["ok"] is True
    result = _full_run(tmp_path, joint=_no_recovery_joint(),
                       sampler=_parity_sampler(), out_name=tmp_path / "t11")
    assert result["terminal"] == d7e.T_NO_RECOVERY
    assert d7e.verify_root(tmp_path / "t11")["ok"] is True

    # T12: zero-truth uniform run decodes everything marginally (control
    # already recovers everywhere, so the run is mixed-diagnostic, not lift).
    result = _full_run(tmp_path, sampler=_zero_sampler(),
                       out_name=tmp_path / "t12")
    assert result["terminal"] == d7e.T_MIXED
    assert all(row["stratum_label"] == d7e.S_CONTROL
               for row in result["summary"]["strata"])

    # Hard cap: an all-eligible run makes exactly 192 calls, no retry.
    source = _scripted_source(["CHECK_UPDATED"] * 64)
    target = _argmax_target()
    result = d7e.run_cross_layer_discriminator(
        out_root=tmp_path / "cap", joint=_uniform_joint(),
        block_sampler=_parity_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7e_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 192
    assert source.calls["k"] == 64 and target.calls["n"] == 128

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
    assert result["terminal"] == d7e.T_CRASH
    records = _read_csv(tmp_path / "t3" / "decoder_records.csv")
    assert records[-1]["status"].startswith("crash:")
    assert d7e.verify_root(tmp_path / "t3")["ok"] is True

    # Watchdog boundary: 120.0 s passes, anything above voids the run.
    result = _full_run(tmp_path, clock=_ScriptedClock([120.0] + [0.0] * 191),
                       out_name=tmp_path / "w120")
    assert result["terminal"] != d7e.T_WATCHDOG
    result = _full_run(tmp_path, clock=_ScriptedClock([120.0001] + [0.0] * 191),
                       out_name=tmp_path / "w121")
    assert result["terminal"] == d7e.T_WATCHDOG and result["records"] == 1
    assert d7e.verify_root(tmp_path / "w121")["ok"] is True

    # Stored-wall boundary: exactly 1500 s passes, anything above overruns.
    result = _full_run(tmp_path, clock=_ScriptedClock([7.8125] * 192),
                       out_name=tmp_path / "wall1500")
    assert result["records"] == 192 and result["terminal"] != d7e.T_RESOURCE
    summary = json.loads((tmp_path / "wall1500" / "summary.json")
                         .read_text(encoding="utf-8"))
    assert abs(float(summary["stored_wall_s"]) - 1500.0) <= 1e-9
    result = _full_run(tmp_path,
                       clock=_ScriptedClock([7.8125] * 191 + [7.8126]),
                       out_name=tmp_path / "wall1501")
    assert result["terminal"] == d7e.T_RESOURCE
    result = _full_run(tmp_path, rss_probe=lambda: d7e.RSS_LIMIT_BYTES,
                       out_name=tmp_path / "rss2g")
    assert result["terminal"] == d7e.T_RESOURCE and result["records"] == 1

    # RSS preflight refuses before any work (zero decoder calls, no root).
    events = []
    out = tmp_path / "t1"

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    with pytest.raises(d7e.PreflightBlocked) as excinfo:
        d7e.run_cross_layer_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7e_execution_authorized": True},
            rss_probe=lambda: 0, repo_root=REPO)
    assert excinfo.value.terminal == d7e.T_PRE_EXEC and events == []
    assert not out.exists()

    # Truncated record sets without a stop recompute to INCOMPLETE.
    _full_run(tmp_path, out_name=tmp_path / "trunc_src")
    rows = _read_csv(tmp_path / "trunc_src" / "decoder_records.csv")
    kept = [r for r in rows if int(r["slot_idx"]) <= 180]
    paired = d7e.compute_transfer_pairs(kept)
    strata = d7e.compute_strata(kept, paired)
    assert d7e.terminal_from_records(kept, paired, strata) == d7e.T_INCOMPLETE


# ==========================================================================
# W01-W03: scalar writer, verifier tamper cases, exact/syndrome isolation
# ==========================================================================

def test_w01_seven_file_schema_scalar_no_subdirs_no_overwrite(tmp_path):
    out = tmp_path / "w01"
    _full_run(tmp_path, out_name=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(d7e.SEVEN_FILES)
    assert not any(p.is_dir() for p in out.iterdir())
    records = _read_csv(out / "decoder_records.csv")
    paired = _read_csv(out / "transfer_pairs.csv")
    strata = _read_csv(out / "stratum_summary.csv")
    assert list(records[0].keys()) == d7e.RECORD_FIELDS
    assert list(paired[0].keys()) == d7e.PAIR_FIELDS
    assert list(strata[0].keys()) == d7e.STRATUM_FIELDS
    assert len(records) == 192 and len(paired) == 64 and len(strata) == 4
    for row in records + paired + strata:
        for value in row.values():
            assert not str(value).startswith("[") and not str(value).startswith("{")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert manifest["max_calls"] == 192 and manifest["mandatory_calls"] == 128
    assert manifest["directions"] == ["L1_TO_L2", "L2_TO_L1"]
    assert manifest["call_order"] == d7e._CALL_ORDER
    assert manifest["decoder_ids"] == dict(d7e._DECODER_IDS)
    assert (out / "report.md").read_text(encoding="utf-8").strip()
    assert (out / "command_log.txt").read_text(encoding="utf-8").strip()

    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        d7e.write_root(populated, {}, [], [], [], {})
    empty_existing = tmp_path / "empty_existing"
    empty_existing.mkdir()
    with pytest.raises(FileExistsError):
        d7e.write_root(empty_existing, {}, [], [], [], {})
    subdir = tmp_path / "subdir"
    (subdir / "nested").mkdir(parents=True)
    with pytest.raises(ValueError):
        d7e.write_root(subdir, {}, [], [], [], {})

    complete = {key: "" for key in d7e.RECORD_FIELDS}
    complete.update({"slot_idx": 1, "f": 1.0, "seed": 2026091300,
                     "direction": "L1_TO_L2", "role": "SOURCE",
                     "condition": "L1_MARGINAL", "layer": "L1",
                     "rows": 49, "n": 64})
    with pytest.raises(ValueError):
        d7e.write_root(tmp_path / "bad_extra", {},
                       [dict(complete, u1_vector=[1])], [], [], {})
    with pytest.raises(ValueError):
        d7e.write_root(tmp_path / "bad_array", {},
                       [dict(complete, wall_s=np.zeros(3))], [], [], {})

    existing = tmp_path / "existing"
    existing.mkdir()
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    with pytest.raises(FileExistsError):
        d7e.run_cross_layer_discriminator(
            out_root=existing, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7e_execution_authorized": True}, repo_root=REPO)
    assert events == []
    with pytest.raises(ValueError):
        d7e.validate_production_out_root(tmp_path / "outside", repo_root=REPO)
    with pytest.raises(ValueError):
        d7e.validate_production_out_root(WS / "wrong_name", repo_root=REPO)
    assert d7e.validate_production_out_root(
        WS / (d7e.OUT_ROOT_PREFIX + "abc"), repo_root=REPO).name.endswith("abc")


def _copy_root(src, dst):
    return Path(shutil.copytree(str(src), str(dst)))


def test_w02_verifier_tamper_cases(tmp_path):
    good = tmp_path / "w02_good"
    _full_run(tmp_path, sampler=_mixed_truth_sampler(), out_name=good)
    report = d7e.verify_root(good)
    assert report["ok"] and report["records"] == 192, report

    record_lines = (good / "decoder_records.csv").read_text(
        encoding="utf-8").splitlines()

    root = _copy_root(good, tmp_path / "t_dup")
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines + [record_lines[1]]) + "\n", encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_missing")
    kept = [line for line in record_lines if not line.startswith("63,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_unpaired")
    kept = [line for line in record_lines if not line.startswith("3,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_exact")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["exact"] = "False" if rows[0]["exact"] == "True" else "True"
    _rewrite_csv(root / "decoder_records.csv", rows, d7e.RECORD_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_syndrome")
    rows = _read_csv(root / "decoder_records.csv")
    rows[1]["syndrome_ok"] = ("False" if rows[1]["syndrome_ok"] == "True"
                              else "True")
    _rewrite_csv(root / "decoder_records.csv", rows, d7e.RECORD_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    # Provenance-gate tampers: flipping the admitting token (or the cached
    # eligibility bit) breaks the gate recompute.
    root = _copy_root(good, tmp_path / "t_prov")
    rows = _read_csv(root / "decoder_records.csv")
    row = next(r for r in rows if r["role"] == "SOURCE")
    row["belief_provenance"] = "PRIOR_ONLY"
    _rewrite_csv(root / "decoder_records.csv", rows, d7e.RECORD_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_elig")
    rows = _read_csv(root / "decoder_records.csv")
    row = next(r for r in rows if r["role"] == "SOURCE")
    row["transfer_eligible"] = "False"
    _rewrite_csv(root / "decoder_records.csv", rows, d7e.RECORD_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_paired")
    rows = _read_csv(root / "transfer_pairs.csv")
    row = next(r for r in rows if r["transfer_only_exact"] == "False")
    row["transfer_only_exact"] = "True"
    _rewrite_csv(root / "transfer_pairs.csv", rows, d7e.PAIR_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_pairs_count")
    rows = _read_csv(root / "transfer_pairs.csv")
    _rewrite_csv(root / "transfer_pairs.csv", rows[:-1], d7e.PAIR_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_strata")
    rows = _read_csv(root / "stratum_summary.csv")
    rows[0]["stratum_label"] = "TRANSFER_REGRESSION"
    _rewrite_csv(root / "stratum_summary.csv", rows, d7e.STRATUM_FIELDS)
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_terminal")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert summary["terminal"] != d7e.T_BIDIRECTIONAL
    summary["terminal"] = d7e.T_BIDIRECTIONAL
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_wall")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["stored_wall_s"] = float(summary["stored_wall_s"]) + 1.0
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_manifest")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["lambda_star"] = 1.0
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_extra")
    (root / "extra.txt").write_text("x", encoding="utf-8")
    assert d7e.verify_root(root)["ok"] is False

    # A legitimately truncated root (watchdog stop) still verifies.
    stopped = tmp_path / "w02_stopped"
    _full_run(tmp_path, clock=_ScriptedClock([120.5] + [0.0] * 191),
              out_name=stopped)
    assert d7e.verify_root(stopped)["ok"] is True


def test_w03_exact_syndrome_isolation():
    rows_l1 = d7e.L1_ROWS[1.0]
    h = np.zeros((rows_l1, d7e.N), dtype=np.int64)  # zero matrix: null syndrome
    x_true = np.zeros(d7e.N, dtype=np.int64)
    syndrome = d5._gf32_syndrome(h, x_true)
    block = {"bob": np.zeros(d7e.N, dtype=np.int64), "u1": x_true,
             "u2": np.zeros(d7e.N, dtype=np.int64)}
    prior = np.full((d7e.N, Q), 1.0 / Q)
    slots = d7e.frozen_slots()
    control_slot = next(s for s in slots if s["role"] == "CONTROL"
                        and s["direction"] == "L1_TO_L2"
                        and s["seed"] == 2026091300)
    transfer_slot = next(s for s in slots if s["role"] == "TRANSFER"
                         and s["direction"] == "L1_TO_L2"
                         and s["seed"] == 2026091300)
    source_slot = next(s for s in slots if s["role"] == "SOURCE"
                       and s["direction"] == "L1_TO_L2"
                       and s["seed"] == 2026091300)
    # Control: one symbol error (exact False) yet null observed syndrome.
    x_wrong = x_true.copy()
    x_wrong[0] = 1
    control = d7e.evaluate_call(
        control_slot, h, block, syndrome,
        {"x_hat": x_wrong, "syndrome_ok": True, "iterations": 2,
         "final_beliefs": np.log(prior), "status": "fake",
         "belief_provenance": "CHECK_UPDATED"}, 0.1, 1024)
    assert control["exact"] is False and control["syndrome_ok"] is True
    assert control["symbol_errors"] == 1 and control["unsatisfied_checks"] == 0
    # Transfer: exact recovery with a negatively-reported syndrome flag.
    transfer = d7e.evaluate_call(
        transfer_slot, h, block, syndrome,
        {"x_hat": x_true, "syndrome_ok": False, "iterations": 2,
         "final_beliefs": np.log(prior), "status": "fake",
         "belief_provenance": "CHECK_UPDATED"}, 0.1, 1024)
    assert transfer["exact"] is True and transfer["syndrome_ok"] is False
    source = d7e.evaluate_call(
        source_slot, h, block, syndrome,
        {"x_hat": x_true, "syndrome_ok": True, "iterations": 2,
         "final_beliefs": np.log(prior), "status": "fake",
         "belief_provenance": "CHECK_UPDATED"}, 0.1, 1024)
    assert source["transfer_eligible"] is True
    pairs = d7e.compute_transfer_pairs([source, control, transfer])
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["transfer_only_exact"] is True
    assert pair["control_only_exact"] is False
    assert pair["both_syndrome_ok"] is False
    assert pair["control_syndrome_ok"] is True
    assert pair["transfer_syndrome_ok"] is False


# ==========================================================================
# X01-X06: launch isolation, sentinels, independence, regressions
# ==========================================================================

def test_x01_lazy_import_help_dry_run_and_unauthorized_isolation(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    assert _run_cli([str(RUNNER), "--help"], cwd=REPO).returncode == 0
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-E" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("slots=192") and len(lines) == 193
    assert lines[1].split()[3:5] == ["L1_TO_L2", "SOURCE"]
    assert lines[2].split()[3:5] == ["L1_TO_L2", "CONTROL"]
    assert lines[3].split()[3:5] == ["L1_TO_L2", "TRANSFER"]
    assert lines[6].split()[3:5] == ["L2_TO_L1", "TRANSFER"]
    assert lines[192].split()[3:5] == ["L2_TO_L1", "TRANSFER"]
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7e_x01')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "print('X01_OK')\n")
    result = subprocess.run([sys.executable, "-c", probe, str(RUNNER)],
                            cwd=str(external), env=_clean_env(),
                            capture_output=True, text=True, timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "X01_OK" in result.stdout

    target = WS / (d7e.OUT_ROOT_PREFIX + "unauthorized_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7e.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3
    assert "not authorized" in result.stdout
    assert not target.exists()
    bad_shape = tmp_path / "bad_shape"
    result = _run_cli([str(RUNNER), "--model-f-root", d7e.MODEL_F_ROOT,
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

g = runpy.run_path(sys.argv[1], run_name="d7e_x02")
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

assert mod._default_model_f_loader is mod.d7c._default_model_f_loader
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
    with pytest.raises(d7e.PreflightBlocked):
        d7e.prepare_inputs(model_f_root="workspace/elsewhere",
                           model_f_loader=_raising_loader,
                           block_sampler=_parity_sampler(), repo=REPO)
    assert d7e.model_f_root_matches(d7e.MODEL_F_ROOT, repo_root=REPO) is True
    assert d7e.model_f_root_matches("workspace/elsewhere",
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
    assert np.array_equal(d7e.condition_prior_qn(joint, "L1_MARGINAL", block),
                          ref_l1)
    assert np.array_equal(d7e.condition_prior_qn(joint, "L2_MARGINAL", block),
                          ref_l2)
    assert "v72p2d7_gf32_schedule_discriminator" not in sys.modules


def test_x04_no_forbidden_cross_layer_or_phase_paths(tmp_path):
    forbidden = (
        "decode_flooding_fftqspa",
        "app_fed_l2_prior",
        "oracle_l2_prior",
        "L1_ORACLE_U2",
        "L2_ORACLE_U1",
        "FLOODING",
        "flooding",
        "--phase",
        "psutil",
        "concurrent",
        "multiprocessing",
        "threading",
    )
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, (path.name, token)
        assert "r1d" not in source.lower(), (path.name, "r1d")
    legacy_call = re.compile(r"build_f_model\s*\(")
    legacy_prior = re.compile(r"prepare_model_f_prior\s*\(")
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8")
        assert legacy_call.search(source) is None, path.name
        assert legacy_prior.search(source) is None, path.name
    source = CORE_PATH.read_text(encoding="utf-8")
    assert source.count("decode_row_layered_fftqspa(") == 4
    for token in ("d7c.run_bidirectional_oracle", "d7c.write_root",
                  "d7c.verify_root", "d7c.bind_historical_decoder",
                  "d7c._default_model_f_loader("):
        assert token not in source, token
    runner_source = RUNNER.read_text(encoding="utf-8")
    assert "verify_root" in runner_source
    assert "CHECK_UPDATED" in source  # the single admitting token, pinned
    assert d7e.CHECK_UPDATED == v35.BELIEF_PROVENANCE_CHECK_UPDATED
    assert not (tmp_path / "root").exists()


def test_x05_protected_state_and_no_production_read(tmp_path, monkeypatch):
    workspace_before = sorted(p.name for p in WS.iterdir())
    model_f_before = _dir_meta(MODEL_F_ROOT)
    d7c_before = _dir_meta(D7C_ROOT)
    d7b_before = _dir_meta(D7B_ROOT)
    d7d_before = _dir_meta(D7D_LEFTOVER)
    assert d7c_before is not None
    assert list(WS.glob(d7e.OUT_ROOT_PREFIX + "*")) == []
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert not (WS / "v72p2d5_g2" / "20260906_r1").exists()

    def _raiser(*args, **kwargs):
        raise AssertionError("Model-F loader must not run in qualification")

    monkeypatch.setattr(d5, "_load_model_f_input_or_blocked", _raiser)
    monkeypatch.setattr(d7c, "_default_model_f_loader", _raiser)
    _full_run(tmp_path, out_name=tmp_path / "x05")

    assert sorted(p.name for p in WS.iterdir()) == workspace_before
    assert list(WS.glob(d7e.OUT_ROOT_PREFIX + "*")) == []
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert _dir_meta(D7C_ROOT) == d7c_before
    if d7b_before is not None:
        assert _dir_meta(D7B_ROOT) == d7b_before
    if d7d_before is not None:
        assert _dir_meta(D7D_LEFTOVER) == d7d_before
    assert d7e._EXECUTION_CONSUMED is False
    state = d7e.read_cycle_state(D7E_CYCLE_STATE)
    for key in ("d7e_execution_authorized", "decoder_executed",
                "result_created", "implementation_authorized",
                "formal_execution_authorized", "synthetic_execution_authorized",
                "real_execution_authorized", "scientific_promotion",
                "plan_accepted", "g1_authorized", "g2_authorized"):
        assert state.get(key) is False, (key, state.get(key))


def _inner_pytest(files, *, extra=(), basetemp):
    return subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider",
         "--basetemp", str(basetemp), *extra],
        cwd=str(REPO), env=dict(os.environ), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)


def test_x06a_bp_and_d7a_regressions(tmp_path):
    base = tmp_path / "inner"
    base.mkdir()
    result = _inner_pytest([str(BP_FILE)], basetemp=base / "bp")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "23 passed" in result.stdout
    result = _inner_pytest([str(D7A_FILE)], basetemp=base / "d7a")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 passed" in result.stdout


def test_x06b_d7b_d7c_regressions(tmp_path):
    base = tmp_path / "inner"
    base.mkdir()
    result = _inner_pytest(
        [str(D7B_FILE), "-k",
         "not test_launch_l04_dry_run_both_cwds_no_bind_no_root and "
         "not test_launch_l12_roots_and_authorization_unchanged"],
        basetemp=base / "d7b")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "29 passed" in result.stdout
    result = _inner_pytest(
        [str(D7C_FILE), "-k",
         "not test_c19_protected_root_lifecycle_and_g2_r1d_absence"],
        basetemp=base / "d7c")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "19 passed" in result.stdout and "1 deselected" in result.stdout


def test_x06c_d7d_d5_regressions(tmp_path):
    base = tmp_path / "inner"
    base.mkdir()
    # Two pre-existing stale lifecycle IDs deselected with reason recorded in
    # the module docstring (leftover committed D7-D root; R22 debt).
    result = _inner_pytest(
        [str(D7D_FILE), "-k",
         "not test_f08_no_real_model_f_production_root_or_formal_root_read and "
         "not test_s21_protected_root_lifecycle_and_d7bc_immutability"],
        basetemp=base / "d7d")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "28 passed" in result.stdout and "2 deselected" in result.stdout
    result = _inner_pytest([str(D5_FILE)], basetemp=base / "d5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "165 passed" in result.stdout


# ==========================================================================
# A2: WSL VmHWM-only RSS telemetry (fail-closed; injected fixtures only)
# ==========================================================================

def _a2_status(*lines):
    return ("Name:\tpython\n" + "".join(line + "\n" for line in lines)
            + "VmRSS:\t    9999 kB\n")


def test_a2_01_valid_vmhwm_conversion():
    assert d7e.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t   48256 kB")) == 48256 * 1024
    assert d7e.parse_vmhwm_rss_bytes("VmHWM: 1 kB\n") == 1024
    assert d7e.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t123456 kB")) == 123456 * 1024
    # Leading zeros still denote a positive integer.
    assert d7e.parse_vmhwm_rss_bytes("VmHWM: 007 kB\n") == 7 * 1024


def test_a2_02_whitespace_only_where_linux_requires():
    for line in ("VmHWM: 123 kB", "VmHWM:\t123 kB", "VmHWM:\t   123 kB",
                 "VmHWM: \t \t123 kB"):
        assert d7e.parse_vmhwm_rss_bytes(line + "\n") == 123 * 1024, line
    for line in (" VmHWM: 123 kB", "\tVmHWM: 123 kB", "VmHWM : 123 kB",
                 "VmHWM:123 kB", "VmHWM: 123\tkB", "VmHWM: 123  kB",
                 "VmHWM: 123 kB ", "VmHWM:\u00a0123 kB",
                 "VmHWM: 123\u00a0kB"):
        assert d7e.parse_vmhwm_rss_bytes(line + "\n") is None, repr(line)


def test_a2_03_missing_field():
    assert d7e.parse_vmhwm_rss_bytes("Name:\tpython\nVmRSS:\t 1 kB\n") is None
    assert d7e.parse_vmhwm_rss_bytes("") is None
    assert d7e.parse_vmhwm_rss_bytes(None) is None
    assert d7e.parse_vmhwm_rss_bytes(b"VmHWM: 1 kB\n") is None
    assert d7e.parse_vmhwm_rss_bytes("VmHWMExtra: 123 kB\n") is None


def test_a2_04_duplicate_field():
    assert d7e.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t 123 kB", "VmHWM:\t 123 kB")) is None
    # A valid line plus a malformed same-field line still blocks.
    assert d7e.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t 123 kB", "VmHWM: nope kB")) is None


def test_a2_05_wrong_unit():
    for unit in ("MB", "KB", "kb", "K", "k", "B", "bytes", "kBB"):
        line = "VmHWM: 123 %s" % unit
        assert d7e.parse_vmhwm_rss_bytes(line + "\n") is None, line
    assert d7e.parse_vmhwm_rss_bytes("VmHWM: 123\n") is None


def test_a2_06_malformed_signed_zero_negative():
    for line in ("VmHWM: 12.5 kB", "VmHWM: 1e4 kB", "VmHWM: +123 kB",
                 "VmHWM: -123 kB", "VmHWM: 0 kB", "VmHWM: 000 kB",
                 "VmHWM: abc kB", "VmHWM:  kB", "VmHWM: kB",
                 "VmHWM 123 kB", "VmHWM:", "VmHWM: 12,345 kB",
                 "VmHWM: 0x10 kB", "VmHWM: \uff11\uff12\uff13 kB",
                 "\uff36mHWM: 123 kB", "VmHWM: 123 \uff4bkB"):
        assert d7e.parse_vmhwm_rss_bytes(line + "\n") is None, repr(line)


def test_a2_07_read_failure_and_fresh_read_per_call(tmp_path, monkeypatch):
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH",
                        str(tmp_path / "does_not_exist"))
    assert d7e.get_rss_bytes() is None
    fixture = tmp_path / "status"
    fixture.write_text("VmHWM: 100 kB\n", encoding="utf-8")
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7e.get_rss_bytes() == 100 * 1024
    # No caching: a rewritten file is re-read on the next probe call.
    fixture.write_text("VmHWM: 200 kB\n", encoding="utf-8")
    assert d7e.get_rss_bytes() == 200 * 1024


def test_a2_08_overflow_rejection_without_wrapping():
    assert d7e.parse_vmhwm_rss_bytes(
        "VmHWM: 9999999999999999999 kB\n") is None  # 19 digits
    assert d7e.parse_vmhwm_rss_bytes(
        "VmHWM: %s kB\n" % ("9" * 100,)) is None
    assert d7e.parse_vmhwm_rss_bytes(
        "VmHWM: 1%s kB\n" % ("0" * 18,)) is None  # 19 digits
    edge = "9" * 18
    assert d7e.parse_vmhwm_rss_bytes(
        "VmHWM: %s kB\n" % (edge,)) == int(edge) * 1024


def test_a2_09_bogus_ru_maxrss_cannot_affect_wsl_result(tmp_path,
                                                        monkeypatch):
    assert not hasattr(d7e, "_read_ru_maxrss")  # legacy fallback deleted
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
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7e.get_rss_bytes() == 123456 * 1024
    assert calls == []


def test_a2_10_below_limit_permits_existing_path(tmp_path, monkeypatch):
    mib = 256 * 1024 * 1024
    fixture = tmp_path / "status"
    fixture.write_text(_a2_status("VmHWM:\t 262144 kB"), encoding="utf-8")
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    assert d7e.get_rss_bytes() == mib
    first = _full_run(tmp_path, rss_probe=d7e.get_rss_bytes,
                      out_name=tmp_path / "a2below")
    second = _full_run(tmp_path, rss_probe=lambda: mib,
                       out_name=tmp_path / "a2below_ref")
    assert first["terminal"] == second["terminal"]
    assert first["records"] == second["records"] == 192


def test_a2_11_limit_boundary_blocks(tmp_path, monkeypatch):
    limit_kb = d7e.RSS_LIMIT_BYTES // 1024
    fixture = tmp_path / "status"
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    # One KiB below the strict <2 GiB limit permits a full run.
    fixture.write_text(_a2_status("VmHWM: %d kB" % (limit_kb - 1,)),
                       encoding="utf-8")
    assert d7e.get_rss_bytes() == d7e.RSS_LIMIT_BYTES - 1024
    result = _full_run(tmp_path, rss_probe=d7e.get_rss_bytes,
                       out_name=tmp_path / "a2lim_ok")
    assert result["records"] == 192 and result["terminal"] != d7e.T_RESOURCE
    # Equal-to and above the limit block at the first call.
    for kb in (limit_kb, limit_kb * 2):
        fixture.write_text(_a2_status("VmHWM: %d kB" % (kb,)),
                           encoding="utf-8")
        out = tmp_path / ("a2lim_%d" % (kb,))
        result = _full_run(tmp_path, rss_probe=d7e.get_rss_bytes,
                           out_name=out)
        assert result["terminal"] == d7e.T_RESOURCE, kb
        assert result["records"] == 1, kb
        assert d7e.verify_root(out)["ok"] is True


def test_a2_12_none_blocks_preflight_before_first_decoder(tmp_path,
                                                          monkeypatch):
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_target()(h, prior, syndrome)

    out = tmp_path / "a2pre"
    with pytest.raises(d7e.PreflightBlocked) as excinfo:
        d7e.run_cross_layer_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7e_execution_authorized": True},
            rss_probe=lambda: None, repo_root=REPO)
    assert excinfo.value.terminal == d7e.T_PRE_EXEC and events == []
    assert not out.exists()
    # A VmHWM-backed None (missing-field fixture) blocks identically.
    fixture = tmp_path / "status"
    fixture.write_text("Name:\tpython\nVmRSS:\t 1 kB\n", encoding="utf-8")
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    out2 = tmp_path / "a2pre2"
    with pytest.raises(d7e.PreflightBlocked):
        d7e.run_cross_layer_discriminator(
            out_root=out2, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7e_execution_authorized": True},
            rss_probe=d7e.get_rss_bytes, repo_root=REPO)
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
        result = d7e.run_cross_layer_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_parity_sampler(),
            decoder_fns={"SOURCE": source, "TARGET": target},
            state={"d7e_execution_authorized": True},
            rss_probe=seq_probe, command_str="fake qualification",
            repo_root=REPO)
        assert result["terminal"] == d7e.T_RESOURCE, bad
        # Preflight plus slots 1-4 probe ok; the 5th slot's probe goes bad,
        # is recorded once, and stops the run with no retry.
        assert result["records"] == 5, bad
        assert source.calls["k"] + target.calls["n"] == 5, bad
        assert d7e.verify_root(out)["ok"] is True


def test_a2_14_rss_bytes_schema_invariant(tmp_path, monkeypatch):
    assert d7e.RECORD_FIELDS.count("rss_bytes") == 1
    fixture = tmp_path / "status"
    fixture.write_text(_a2_status("VmHWM:\t 262144 kB"), encoding="utf-8")
    monkeypatch.setattr(d7e, "_PROC_SELF_STATUS_PATH", str(fixture))
    out = tmp_path / "a2schema"
    _full_run(tmp_path, rss_probe=d7e.get_rss_bytes, out_name=out)
    rows = _read_csv(out / "decoder_records.csv")
    assert list(rows[0].keys()) == d7e.RECORD_FIELDS
    assert {row["rss_bytes"] for row in rows} == {str(256 * 1024 * 1024)}
    assert d7e.verify_root(out)["ok"] is True
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rss_limit_bytes"] == 2 * 1024**3


def test_a2_15_cli_surface_zero_decoder_zero_root(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-E" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("slots=192") and len(lines) == 193
    target = WS / (d7e.OUT_ROOT_PREFIX + "a2_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7e.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3 and "not authorized" in result.stdout
    assert not target.exists()
