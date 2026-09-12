"""D7-H minimal alternating discriminator qualification (tiny fake/DI only).

No test creates ``workspace/d7_h_alternating_discriminator_*`` or reads real
Model-F content; every scientific-run decoder is an injected fake and every
scientific-run joint/block/mother is in-memory.  The only real decoder
contacts are the D7-G-pinned tiny single-check GF(32) unit fixtures
(iterations <= 1), exactly as the accepted D7-G certification suite does.
The milestone regression runs in its own pytest process with a fresh
task-owned basetemp.

Frozen contract: ``.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_
FREEZE_R1_TASK_PACKET.md`` (R1A1-corrected), ``docs/research_cycles/
V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/D7_H_PREREG_R1.md`` and
``openspec/changes/v72p2d7-alternating-discriminator/``.
"""

from __future__ import annotations

import csv
import importlib.util
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
FORMAL = SRC / "comparison_bench" / "formal_ir"
CORE_PATH = FORMAL / "v72p2d7_gf32_alternating_discriminator.py"
RUNNER = REPO / "scripts" / "v72p2d7_gf32_alternating_discriminator.py"
WS = REPO / "workspace"
MODEL_F_ROOT = WS / "v72p2d5_model_f_input" / "20260907_r1"
D7H_CYCLE_STATE = (REPO / "docs" / "research_cycles"
                   / "V72P2D7-GF32-ALTERNATING-DISCRIMINATOR"
                   / "cycle_state.yaml")
D7E_ROOT = (WS / "d7_e_cross_layer_discriminator_"
            "faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c")
D7F_ROOT = (WS / "d7_f_reverse_order_discriminator_"
            "b6d62184-fd15-483d-947e-01ea66ddc13c")
D7D_ROOT = (WS / "d7_d_schedule_discriminator_"
            "64660d16-397d-4ef3-8454-3066d27c12c7")
BP_FILE = (REPO / "comparison_bench" / "tests"
           / "test_v72p2d7_bp_belief_provenance.py")
SUB_TIMEOUT = 1200

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d7_gf32_alternating_discriminator as d7h,
)
from comparison_bench.formal_ir import (  # noqa: E402
    v35_algorithm_development as v35,
)

d7f = d7h.d7f
d7e = d7h.d7e
d7c = d7h.d7c
d5 = d7h.d5
Q = 32
TOL = 1e-10


# --------------------------------------------------------------------------
# Shared fake fixtures (no real Model-F / no production run decoder)
# --------------------------------------------------------------------------

def _uniform_joint() -> np.ndarray:
    return np.full((Q, Q, d7h.BOB_DIM), 1.0 / (Q * Q))


def _column_joint(columns: dict) -> np.ndarray:
    """Full-size joint with crafted Bob columns; all other columns uniform."""
    joint = np.full((Q, Q, d7h.BOB_DIM), 1.0 / (Q * Q))
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
    n = d7h.N
    bob = np.full(n, int(bob_val), dtype=np.int64)
    u1 = np.full(n, int(a), dtype=np.int64)
    u2 = np.full(n, int(b), dtype=np.int64)
    return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}


def _zero_sampler():
    def sample(p_b, p_f, n, seed):
        return _const_block(seed, bob_val=0, a=0, b=0)
    return sample


def _stair_sampler():
    """Nonconstant L1/L2 truths so syndromes differ per layer and identity."""
    def sample(p_b, p_f, n, seed):
        k = int(seed) - 2026091300
        u1 = (np.arange(64, dtype=np.int64) + k) % Q
        u2 = (np.arange(64, dtype=np.int64) * 7 + k) % Q
        bob = np.where(np.arange(64) % 2 == 0, 0, 1).astype(np.int64)
        return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}
    return sample


def _log_rows(dist):
    d = np.asarray(dist, dtype=np.float64)
    m = np.max(d, axis=1, keepdims=True)
    lse = m + np.log(np.sum(np.exp(d - m), axis=1, keepdims=True))
    return d - lse


def _peaked_log(n, peak, mass=0.9):
    row = np.full(Q, (1.0 - mass) / (Q - 1))
    row[int(peak)] = mass
    row = row / row.sum()
    return np.log(np.tile(row, (int(n), 1)))


def _normalized_log(rows):
    r = np.asarray(rows, dtype=np.float64)
    return r - (np.max(r, axis=1, keepdims=True)
                + np.log(np.sum(np.exp(r - np.max(r, axis=1, keepdims=True)),
                                axis=1, keepdims=True)))


def _softmax_rows(z):
    m = np.max(z, axis=1, keepdims=True)
    e = np.exp(z - m)
    return e / e.sum(axis=1, keepdims=True)


def _outcome(n, *, peak=0, iterations=5, x_hat=None, ext=None,
             ext_prov="CHECK_EXTRINSIC", include_ext=True,
             belief_prov=None, final_beliefs=None, syndrome_ok=True,
             status="fake"):
    """One fake decoder return; defaults are a valid CHECK_EXTRINSIC sweep."""
    if x_hat is None:
        x_hat = np.zeros(int(n), dtype=np.int64)
    if final_beliefs is None:
        final_beliefs = _peaked_log(n, peak)
    if ext is None and include_ext:
        ext = np.zeros((int(n), Q))
    if belief_prov is None:
        belief_prov = "CHECK_UPDATED" if iterations > 0 else "PRIOR_ONLY"
    out = {"x_hat": np.asarray(x_hat, dtype=np.int64),
           "syndrome_ok": bool(syndrome_ok),
           "iterations": int(iterations),
           "final_beliefs": np.asarray(final_beliefs, dtype=np.float64),
           "status": status}
    if include_ext:
        out["extrinsic_log_beliefs"] = np.asarray(ext, dtype=np.float64)
    if ext_prov is not None:
        out["extrinsic_provenance"] = ext_prov
    if belief_prov is not None:
        out["belief_provenance"] = belief_prov
    return out


def _blocked_outcome(n, token="NO_CHECK_EVIDENCE", **kwargs):
    """it0-style ineligible return: neutral zeros + non-admitting token."""
    ext = kwargs.pop("ext", None)
    return _outcome(n, ext=ext, ext_prov=token, **kwargs)


def _sequence_decoder(outcomes):
    """k-th call uses ``outcomes[k]`` (callable or dict); captures inputs."""
    state = {"n": 0, "h": [], "prior": [], "syn": [], "returns": []}
    items = list(outcomes)

    def decode(h, prior, syndrome):
        k = state["n"]
        state["n"] += 1
        state["h"].append(np.asarray(h).copy())
        state["prior"].append(np.asarray(prior).copy())
        state["syn"].append(np.asarray(syndrome).copy())
        item = items[k] if k < len(items) else items[-1]
        if callable(item):
            item = item(np.asarray(prior), np.asarray(syndrome), k)
        state["returns"].append(item)
        return item

    decode.calls = state
    return decode


def _identity_order():
    return [(float(f), int(seed))
            for f in d7h.F_VALUES for seed in d7h.BLOCK_SEEDS]


def _full_outcomes(**outcome_kwargs):
    return [_outcome(d7h.N, **outcome_kwargs) for _ in range(d7h.SLOT_COUNT)]


def _full_run(tmp_path, name="root", *, joint=None, sampler=None,
              decode_fn=None, source_fn=None, target_fn=None, clock=None,
              rss_probe=None, mothers=None, state=None, out_name=None,
              command_str="fake qualification"):
    out = Path(out_name) if out_name is not None else (tmp_path / name)
    if decode_fn is None and source_fn is None and target_fn is None:
        decode_fn = _sequence_decoder(_full_outcomes())
    if source_fn is None:
        source_fn = decode_fn
    if target_fn is None:
        target_fn = decode_fn
    return d7h.run_alternating_discriminator(
        out_root=out,
        joint=_uniform_joint() if joint is None else joint,
        block_sampler=_zero_sampler() if sampler is None else sampler,
        mothers=mothers,
        decoder_fns={"SOURCE": source_fn, "TARGET": target_fn},
        state={"d7h_execution_authorized": True} if state is None else state,
        clock=clock,
        rss_probe=(rss_probe if rss_probe is not None
                   else (lambda: 256 * 1024 * 1024)),
        command_str=command_str, repo_root=REPO)


class _ScriptedClock:
    """Deterministic clock: decode call k costs ``walls[k]`` seconds."""

    def __init__(self, walls):
        self.walls = list(walls)
        self.n = 0
        self.t = 0.0
        self.k = 0

    def __call__(self):
        if self.n % 2 == 1:
            self.t += (float(self.walls[self.k])
                       if self.k < len(self.walls) else 0.0)
            self.k += 1
            self.n += 1
            return self.t
        self.n += 1
        return self.t


def _read_csv(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _rewrite_csv(path, rows, fields):
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _copy_root(src, dst):
    return Path(shutil.copytree(str(src), str(dst)))


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

def test_e01_transfer_formulas_match_direct_enumeration():
    rng = np.random.default_rng(20260913)
    B, n = 3, 5
    raw = rng.random((Q, Q, B)) + 0.1
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 2, 1, 2, 0])
    q = rng.random((n, Q)) + 0.1
    q = q / q.sum(axis=1, keepdims=True)

    got_l12 = d7h.build_transfer_prior(joint, "L1_TO_L2", bob, q)
    direct = np.zeros((n, Q))
    for i in range(n):
        cond = joint[:, :, bob[i]] / joint[:, :, bob[i]].sum(
            axis=1, keepdims=True)
        direct[i] = q[i] @ cond
    assert np.allclose(got_l12, d5._floor_renorm(direct, 1e-15),
                       atol=1e-12, rtol=0)

    got_l21 = d7h.build_transfer_prior(joint, "L2_TO_L1", bob, q)
    direct = np.zeros((n, Q))
    for i in range(n):
        cond = (joint[:, :, bob[i]]
                / joint[:, :, bob[i]].sum(axis=0, keepdims=True))
        direct[i] = q[i] @ cond.T
    assert np.allclose(got_l21, d5._floor_renorm(direct, 1e-15),
                       atol=1e-12, rtol=0)
    with pytest.raises(ValueError):
        d7h.build_transfer_prior(joint, "NOPE", bob, q)

    # The posterior-message helper of D7-E/F is not part of D7-H.
    assert not hasattr(d7h, "softmax_source_q")


def test_e02_concentration_estimator_identity_and_legacy_differs(monkeypatch):
    assert d7h.LAMBDA_STAR == d5.LAMBDA_STAR == 137.3823795883264
    assert d7h.DECODER_FLOOR == 1e-15
    assert d7h._ESTIMATOR_ID == d7c._ESTIMATOR_ID

    counts = np.array([[8., 1., 0.], [2., 6., 1.], [0., 2., 7.],
                       [1., 0., 2.]])
    corrected = d5.build_f_model_concentration(counts, 2.0)
    legacy = d5.build_f_model(counts, 2.0)
    assert corrected.shape == legacy.shape == (4, 3)
    assert float(np.max(np.abs(corrected - legacy))) > 1e-6

    counts_big = np.ones((d7h.N_A, d7h.BOB_DIM))
    counts_big[0, 0] = 9.0
    p_b = np.full(d7h.BOB_DIM, 1.0 / d7h.BOB_DIM)
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

    ctx = d7h.prepare_inputs(
        model_f_root=d7h.MODEL_F_ROOT, model_f_loader=loader,
        block_sampler=_zero_sampler(), mothers=None, repo=REPO)
    assert calls == [((d7h.N_A, d7h.BOB_DIM), (d7h.BOB_DIM,),
                      d7h.LAMBDA_STAR)]
    assert ctx["joint"].shape == (Q, Q, d7h.BOB_DIM)
    assert len(ctx["slots"]) == 96


def test_e03_legacy_builder_never_referenced_by_d7h():
    legacy_call = re.compile(r"build_f_model\s*\(")
    legacy_prior = re.compile(r"prepare_model_f_prior\s*\(")
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8")
        assert legacy_call.search(source) is None, (path.name, "legacy builder")
        assert legacy_prior.search(source) is None, (path.name, "legacy prior")
    core = CORE_PATH.read_text(encoding="utf-8")
    assert "prepare_model_f_prior_candidate" in core
    assert "prepare_inputs" in core and "d7c.prepare_inputs" in core


# ==========================================================================
# M01-M04: frozen 96-slot chain matrix and stage transitions
# ==========================================================================

def test_m01_exact_96_slot_order_and_32_mandatory():
    slots = d7h.frozen_slots()
    assert len(slots) == 96 and d7h.SLOT_COUNT == 96
    assert d7h.MANDATORY_CALLS == 32 and d7h.MAX_CALLS == 96
    assert d7h.IDENTITY_COUNT == 32 and d7h.STAGE_COUNT == 3
    assert d7h.STAGE_ORDER == ("SOURCE_L1_MARGINAL", "FORWARD_L1_TO_L2",
                               "BACKWARD_L2_TO_L1")
    assert [s["slot_idx"] for s in slots] == list(range(1, 97))
    assert len({(s["f"], s["seed"], s["stage"]) for s in slots}) == 96
    assert [s["f"] for s in slots[:48]] == [1.0] * 48
    assert [s["f"] for s in slots[48:]] == [1.2] * 48
    pos = 0
    for f in (1.0, 1.2):
        for seed in range(2026091300, 2026091316):
            want = [
                ("SOURCE_L1_MARGINAL", 0, "L1_MARGINAL", "L1", "SOURCE",
                 {1.0: 49, 1.2: 59}[f], False),
                ("FORWARD_L1_TO_L2", 1, "L2_TRANSFER", "L2", "TARGET",
                 {1.0: 43, 1.2: 52}[f], True),
                ("BACKWARD_L2_TO_L1", 2, "L1_RETURN_TRANSFER", "L1", "TARGET",
                 {1.0: 49, 1.2: 59}[f], True),
            ]
            for name, stage, condition, layer, role, rows, gated in want:
                slot = slots[pos]
                pos += 1
                assert slot["f"] == f and slot["seed"] == seed
                assert slot["stage_name"] == name and slot["stage"] == stage
                assert slot["condition"] == condition and slot["layer"] == layer
                assert slot["role"] == role and slot["gated"] is gated
                assert slot["rows"] == rows and slot["n"] == 64
    mandatory = [s for s in slots if s["stage"] == 0]
    assert len(mandatory) == 32


def test_m02_identity_reuse_and_narrow_imports():
    assert d7h.BLOCK_SEEDS == d7c.BLOCK_SEEDS == tuple(
        range(2026091300, 2026091316))
    assert d7h.F_VALUES == d7c.F_VALUES == (1.0, 1.2)
    assert d7h.L1_ROWS == {1.0: 49, 1.2: 59}
    assert d7h.L2_ROWS == {1.0: 43, 1.2: 52}
    assert d7h.MAX_ITER == d7c.MAX_ITER == 90
    assert d7h.DAMPING_ALPHA == d7c.DAMPING_ALPHA == 1.0
    assert d7h.Q == d7c.Q == 32 and d7h.N == d7c.N == 64
    assert d7h.MODEL_F_ROOT == d7c.MODEL_F_ROOT
    # Narrow reuse (aliases, not copies) of the accepted helpers.
    assert d7h.condition_prior_qn is d7f.condition_prior_qn
    assert d7h.decoder_prior is d7f.decoder_prior
    assert d7h.build_mother is d7f.build_mother
    assert d7h.build_joint is d7f.build_joint
    assert d7h._default_model_f_loader is d7f._default_model_f_loader
    assert d7h.build_transfer_prior is d7f.build_transfer_prior
    assert d7h.transfer_prior_l1_to_l2 is d7f.transfer_prior_l1_to_l2
    assert d7h.transfer_prior_l2_to_l1 is d7f.transfer_prior_l2_to_l1
    assert d7h.dispatch_decoder is d7f.dispatch_decoder
    assert d7h.bind_row_layered_decoders is d7f.bind_row_layered_decoders
    assert d7h.parse_vmhwm_rss_bytes is d7f.parse_vmhwm_rss_bytes
    assert d7h._probe_rss_valid is d7f._probe_rss_valid
    assert d7h.read_cycle_state is d7f.read_cycle_state
    assert d7h.model_f_root_matches is d7f.model_f_root_matches
    assert d7h._record_row is d7f._record_row
    assert d7h._load_v35 is d7e._load_v35
    # The D7-H root guard covers the accepted D7-D/E/F roots.
    for root in (D7D_ROOT, D7E_ROOT, D7F_ROOT):
        assert root.name in " ".join(d7h.PROTECTED_ROOTS)


def test_m03_full_chain_and_all_blocked_cascade(tmp_path):
    out = tmp_path / "m03_full"
    result = _full_run(tmp_path, out_name=out)
    assert result["records"] == 96
    rows = _read_csv(out / "decoder_records.csv")
    assert [int(r["stage"]) for r in rows] == [0, 1, 2] * 32
    assert all(r["transfer_eligible"] == "True" for r in rows[:2])
    pairs = _read_csv(out / "arm_pairs.csv")
    assert len(pairs) == 32
    assert all(p["chain_complete"] == "True" for p in pairs)
    assert all(p["stage0_transfer_eligible"] == "True" for p in pairs)
    assert all(p["stage1_transfer_eligible"] == "True" for p in pairs)
    assert all(p["blocked_at_stage1"] == "False" for p in pairs)
    assert all(p["blocked_at_stage2"] == "False" for p in pairs)
    assert result["terminal"] == d7h.T_NO_LIFT
    assert d7h.verify_root(out)["ok"] is True

    # All STAGE 0 outputs NO_CHECK_EVIDENCE: 32 calls, cascade to 1/2.
    out2 = tmp_path / "m03_blocked"
    dec = _sequence_decoder([_blocked_outcome(d7h.N)] * d7h.SLOT_COUNT)
    result2 = d7h.run_alternating_discriminator(
        out_root=out2, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": dec, "TARGET": dec},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result2["records"] == 32
    assert dec.calls["n"] == 32  # zero gated calls, no fabrication
    rows2 = _read_csv(out2 / "decoder_records.csv")
    assert {r["stage"] for r in rows2} == {"0"}
    assert all(r["transfer_eligible"] == "False" for r in rows2)
    assert all(r["transfer_block_reason"] == "EXTRINSIC_NO_CHECK_EVIDENCE"
               for r in rows2)
    pairs2 = _read_csv(out2 / "arm_pairs.csv")
    assert all(p["chain_complete"] == "False" for p in pairs2)
    assert all(p["blocked_at_stage1"] == "True" for p in pairs2)
    assert all(p["blocked_at_stage2"] == "True" for p in pairs2)
    strata2 = _read_csv(out2 / "stratum_summary.csv")
    assert all(s["complete_chain_count"] == "0" for s in strata2)
    assert all(s["blocked_at_stage1"] == "16" for s in strata2)
    assert all(s["blocked_at_stage2"] == "16" for s in strata2)
    assert all(s["stratum_label"] == "COVERAGE_BLOCKED" for s in strata2)
    assert result2["terminal"] == d7h.T_COVERAGE
    assert d7h.verify_root(out2)["ok"] is True


def test_m04_partial_blocks_cascade_without_fabrication(tmp_path):
    # Frozen per-identity decision tables (f, seed) keyed.
    blocked0 = {(1.0, 2026091300), (1.0, 2026091301), (1.2, 2026091300)}
    blocked1 = {(1.0, 2026091302), (1.0, 2026091303)}
    source_outcomes = []
    target_outcomes = []
    expected_stage1 = expected_stage2 = 0
    for key in _identity_order():
        if key in blocked0:
            source_outcomes.append(_blocked_outcome(d7h.N, iterations=0,
                                                    x_hat=np.zeros(d7h.N)))
            continue
        source_outcomes.append(_outcome(d7h.N))
        expected_stage1 += 1
        if key in blocked1:
            target_outcomes.append(_blocked_outcome(
                d7h.N, token="WARM_START_UNSPECIFIED", include_ext=False))
            continue
        target_outcomes.append(_outcome(d7h.N))
        expected_stage2 += 1
        target_outcomes.append(_outcome(d7h.N))
    out = tmp_path / "m04"
    source = _sequence_decoder(source_outcomes)
    target = _sequence_decoder(target_outcomes)
    result = d7h.run_alternating_discriminator(
        out_root=out, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert source.calls["n"] == 32
    assert target.calls["n"] == expected_stage1 + expected_stage2 == 56
    assert result["records"] == 32 + expected_stage1 + expected_stage2 == 88
    rows = _read_csv(out / "decoder_records.csv")
    assert sum(1 for r in rows if r["stage"] == "1") == 29
    assert sum(1 for r in rows if r["stage"] == "2") == 27
    strata = {float(s["f"]): s for s in _read_csv(out / "stratum_summary.csv")}
    assert strata[1.0]["complete_chain_count"] == "12"
    assert strata[1.0]["blocked_at_stage1"] == "2"
    assert strata[1.0]["blocked_at_stage2"] == "4"
    assert strata[1.2]["complete_chain_count"] == "15"
    assert strata[1.2]["blocked_at_stage1"] == "1"
    assert strata[1.2]["blocked_at_stage2"] == "1"
    pairs = _read_csv(out / "arm_pairs.csv")
    p = next(x for x in pairs if float(x["f"]) == 1.0
             and x["seed"] == "2026091302")
    assert p["blocked_at_stage1"] == "False"
    assert p["blocked_at_stage2"] == "True"
    assert p["stage1_block_reason"] == "EXTRINSIC_WARM_START_UNSPECIFIED"
    p0 = next(x for x in pairs if float(x["f"]) == 1.0
              and x["seed"] == "2026091300")
    assert p0["blocked_at_stage1"] == "True"
    assert p0["stage0_block_reason"] == "EXTRINSIC_NO_CHECK_EVIDENCE"
    assert p0["stage1_slot_idx"] == "" and p0["stage2_slot_idx"] == ""
    assert d7h.verify_root(out)["ok"] is True


# ==========================================================================
# G01-G05: CHECK_EXTRINSIC gate, cavity rule, no posterior path
# ==========================================================================

def test_g01_gate_transport_uses_the_certified_helper(tmp_path, monkeypatch):
    seen = []
    real = d7h.require_check_extrinsic_for_transfer

    def spy(ext, prov, *, consumer, expected_n=None):
        seen.append((id(ext), prov, expected_n, consumer))
        return real(ext, prov, consumer=consumer, expected_n=expected_n)

    monkeypatch.setattr(d7h, "require_check_extrinsic_for_transfer", spy)
    out = tmp_path / "g01"
    result = _full_run(tmp_path, out_name=out)
    assert result["records"] == 96
    assert len(seen) == 96  # every stage's output is judged by the helper
    assert {prov for _, prov, _, _ in seen} == {"CHECK_EXTRINSIC"}
    assert {n for _, _, n, _ in seen} == {64}
    assert all("D7-H " in consumer for _, _, _, consumer in seen)
    rows = _read_csv(out / "decoder_records.csv")
    assert all(r["transfer_eligible"] == "True" for r in rows)
    assert d7h.verify_root(out)["ok"] is True


def test_g02_refused_extrinsic_blocks_before_mixer_and_target(tmp_path,
                                                             monkeypatch):
    cases = [
        ("NO_CHECK_EVIDENCE", dict(ext=None, ext_prov="NO_CHECK_EVIDENCE",
                                   include_ext=True),
         "EXTRINSIC_NO_CHECK_EVIDENCE"),
        ("WARM_START_UNSPECIFIED",
         dict(ext=None, ext_prov="WARM_START_UNSPECIFIED", include_ext=False),
         "EXTRINSIC_WARM_START_UNSPECIFIED"),
        ("missing", dict(ext=None, ext_prov=None, include_ext=False,
                         belief_prov="CHECK_UPDATED"),
         "EXTRINSIC_UNKNOWN_OR_MISSING"),
        ("unknown", dict(ext=None, ext_prov="BOGUS", include_ext=True),
         "EXTRINSIC_UNKNOWN_OR_MISSING"),
        ("check-none", dict(ext=None, ext_prov="CHECK_EXTRINSIC",
                            include_ext=False),
         "EXTRINSIC_SHAPE_OR_NONFINITE"),
        ("check-shape", dict(ext=np.zeros((d7h.N, 31)),
                             ext_prov="CHECK_EXTRINSIC", include_ext=True),
         "EXTRINSIC_SHAPE_OR_NONFINITE"),
        ("check-nonfinite", dict(ext=np.full((d7h.N, Q), np.nan),
                                 ext_prov="CHECK_EXTRINSIC", include_ext=True),
         "EXTRINSIC_SHAPE_OR_NONFINITE"),
    ]
    for tag, kwargs, reason in cases:
        mixer_calls = []

        def _mixer_raiser(*args, _c=mixer_calls, **kw):
            _c.append(1)
            raise AssertionError("mixer must not run for %s" % (tag,))

        monkeypatch.setattr(d7h, "build_transfer_prior", _mixer_raiser)
        dec = _sequence_decoder([_outcome(d7h.N, **kwargs)] * d7h.SLOT_COUNT)
        out = tmp_path / ("g02_%s" % tag)
        result = d7h.run_alternating_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_zero_sampler(),
            decoder_fns={"SOURCE": dec, "TARGET": dec},
            state={"d7h_execution_authorized": True},
            rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
        assert mixer_calls == [], tag
        assert dec.calls["n"] == 32, tag
        assert result["records"] == 32, tag
        rows = _read_csv(out / "decoder_records.csv")
        assert all(r["transfer_eligible"] == "False" for r in rows)
        assert all(r["transfer_block_reason"] == reason for r in rows), tag
        assert d7h.verify_root(out)["ok"] is True, tag
        monkeypatch.undo()


def test_g03_iteration0_hard_success_blocks_and_source_exact_not_gate(
        tmp_path):
    # The certified producer's iteration-0 early exit: hard/syndrome exact
    # yet NEUTRAL zeros + NO_CHECK_EVIDENCE (tiny in-memory unit call only).
    tiny_h = np.array([[1, 1]], dtype=np.uint8)
    it0 = v35.decode_row_layered_fftqspa(
        tiny_h, _softmax_rows(_peaked_log(2, 0)), np.array([0], dtype=np.uint8),
        max_iter=5)
    assert it0.iterations == 0 and it0.syndrome_ok is True
    q, eligible, reason = d7h.chain_gate(
        status=it0.status, finite=True,
        extrinsic_log_beliefs=it0.extrinsic_log_beliefs,
        extrinsic_provenance=it0.extrinsic_provenance, expected_n=2,
        consumer="test")
    assert (q, eligible, reason) == (None, False,
                                     "EXTRINSIC_NO_CHECK_EVIDENCE")

    # Full-chain it0-style fake: exact hard decision + syndrome, still blocked.
    out = tmp_path / "g03"
    dec = _sequence_decoder([_blocked_outcome(
        d7h.N, iterations=0, x_hat=np.zeros(d7h.N), syndrome_ok=True)]
        * d7h.SLOT_COUNT)
    result = d7h.run_alternating_discriminator(
        out_root=out, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": dec, "TARGET": dec},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    rows = _read_csv(out / "decoder_records.csv")
    assert all(r["exact"] == "True" and r["syndrome_ok"] == "True"
               for r in rows)
    assert all(r["transfer_eligible"] == "False" for r in rows)
    assert result["records"] == 32
    assert d7h.verify_root(out)["ok"] is True

    # Source exact/miss is irrelevant when CHECK_EXTRINSIC is present.
    out2 = tmp_path / "g03_miss"
    miss = _outcome(d7h.N, x_hat=np.ones(d7h.N, dtype=np.int64),
                    syndrome_ok=False, peak=3)
    dec2 = _sequence_decoder([miss] * d7h.SLOT_COUNT)
    result2 = d7h.run_alternating_discriminator(
        out_root=out2, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": dec2, "TARGET": dec2},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert dec2.calls["n"] == 96  # source miss still transferred
    rows2 = _read_csv(out2 / "decoder_records.csv")
    assert all(r["transfer_eligible"] == "True" for r in rows2)
    assert any(r["exact"] == "False" for r in rows2)
    assert d7h.verify_root(out2)["ok"] is True


def test_g04_cavity_prior_is_function_of_check_evidence_only(tmp_path,
                                                             monkeypatch):
    """(a)/(e): the backward prior must not depend on STAGE 0's evidence
    (the stage-1 incoming prior it removes) and must depend on STAGE 1's own
    check evidence; the posterior path fails the first check."""
    stage0_ext_a = np.zeros((d7h.N, Q))
    stage0_ext_b = np.tile(_normalized_log(_peaked_log(1, 5, mass=0.95)),
                           (d7h.N, 1))
    m1 = np.tile(_normalized_log(_peaked_log(1, 7, mass=0.6)), (d7h.N, 1))
    m2 = np.tile(_normalized_log(_peaked_log(1, 21, mass=0.9)), (d7h.N, 1))

    def run_with(tag, source_ext, m):
        captured = []
        captured_final = []
        real_mix = d7h.build_transfer_prior

        def spy(joint, direction, bob, q):
            captured.append((direction, np.asarray(q).copy()))
            return real_mix(joint, direction, bob, q)

        def target(h, prior, syndrome):
            p = np.asarray(prior, dtype=np.float64)
            final = np.log(np.maximum(p, 1e-300)) + m
            captured_final.append(np.asarray(final).copy())
            return {"x_hat": np.zeros(d7h.N, dtype=np.int64),
                    "syndrome_ok": True, "iterations": 5,
                    "final_beliefs": final,
                    "extrinsic_log_beliefs": m.copy(),
                    "extrinsic_provenance": "CHECK_EXTRINSIC",
                    "belief_provenance": "CHECK_UPDATED", "status": "fake2"}

        src = _sequence_decoder(
            [_outcome(d7h.N, ext=source_ext, include_ext=True)]
            * d7h.SLOT_COUNT)
        monkeypatch.setattr(d7h, "build_transfer_prior", spy)
        out = tmp_path / ("g04_%s" % (tag,))
        d7h.run_alternating_discriminator(
            out_root=out, joint=_skewed_joint(), block_sampler=_stair_sampler(),
            decoder_fns={"SOURCE": src, "TARGET": target},
            state={"d7h_execution_authorized": True},
            rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
        monkeypatch.undo()
        return captured, captured_final

    cap_a1, fin_a1 = run_with("a1", stage0_ext_a, m1)
    cap_b1, fin_b1 = run_with("b1", stage0_ext_b, m1)
    cap_b2, fin_b2 = run_with("b2", stage0_ext_b, m2)
    bob = _const_block(2026091300)["bob"]

    def backward_prior(captured):
        # Identity 1's call order: [0] = stage-1 transport (q0), [1] = stage-2
        # transport (q1 = softmax of STAGE 1's own check evidence).
        assert captured[0][0] == "L1_TO_L2"
        assert captured[1][0] == "L2_TO_L1"
        return d7h.build_transfer_prior(_skewed_joint(), "L2_TO_L1", bob,
                                        captured[1][1])

    # The stage-1 transport is exactly softmax(m1) in both runs ...
    expected_q1 = _softmax_rows(m1)
    assert float(np.max(np.abs(cap_a1[1][1] - expected_q1))) <= TOL
    assert float(np.max(np.abs(cap_b1[1][1] - expected_q1))) <= TOL
    # ... so the backward prior is invariant to STAGE 0's evidence ...
    prior_a = backward_prior(cap_a1)
    prior_b = backward_prior(cap_b1)
    assert float(np.max(np.abs(prior_a - prior_b))) <= TOL
    # ... while remaining sensitive to STAGE 1's own check evidence ...
    prior_c = d7h.build_transfer_prior(_skewed_joint(), "L2_TO_L1", bob,
                                       cap_b2[1][1])
    gap = float(np.max(np.abs(prior_b - prior_c)))
    assert gap >= 1e-3, gap
    # ... and a posterior-based back-transfer would have changed the answer.
    posterior_q = _softmax_rows(fin_b1[0])
    post_prior = d7h.build_transfer_prior(_skewed_joint(), "L2_TO_L1", bob,
                                          posterior_q)
    gap_post = float(np.max(np.abs(post_prior - prior_b)))
    assert gap_post >= 1e-3, gap_post
    gap_transport = float(np.max(np.abs(_softmax_rows(m1) - posterior_q)))
    assert gap_transport >= 1e-3, gap_transport


def test_g05_posterior_transfer_path_is_unreachable_statically():
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "softmax_source_q" not in source
    assert "extrinsic_log_beliefs" in source
    assert "require_check_extrinsic_for_transfer" in source
    # The D7-E/F current-belief transport helper is not imported at all.
    assert not hasattr(d7h, "softmax_source_q")
    assert "build_transfer_prior" in source


# ==========================================================================
# S01-S02: per-invocation designated syndrome and no returned evidence
# ==========================================================================

def test_s01_each_invocation_consumes_its_designated_syndrome(tmp_path):
    out = tmp_path / "s01"
    source = _sequence_decoder([_outcome(d7h.N)] * 32)
    target = _sequence_decoder([_outcome(d7h.N)] * 64)
    result = d7h.run_alternating_discriminator(
        out_root=out, joint=_uniform_joint(), block_sampler=_stair_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 96
    assert source.calls["n"] == 32 and target.calls["n"] == 64
    h1 = d7h.build_mother("L1")
    h2 = d7h.build_mother("L2")
    sampler = _stair_sampler()
    for i, (f, seed) in enumerate(_identity_order()):
        block = sampler(None, None, 64, seed)
        rows1 = d7h.ROWS["L1"][f]
        rows2 = d7h.ROWS["L2"][f]
        l1_syn = d5._gf32_syndrome(h1[:rows1], block["u1"])
        l2_syn = d5._gf32_syndrome(h2[:rows2], block["u2"])
        assert np.array_equal(source.calls["syn"][i], l1_syn)
        assert np.array_equal(source.calls["h"][i], h1[:rows1])
        assert np.array_equal(target.calls["syn"][2 * i], l2_syn)
        assert np.array_equal(target.calls["h"][2 * i], h2[:rows2])
        # L1 is decoded twice; the return invocation re-consumes the L1
        # designated syndrome with its own H/slot, never L2's.
        assert np.array_equal(target.calls["syn"][2 * i + 1], l1_syn)
        assert np.array_equal(target.calls["h"][2 * i + 1], h1[:rows1])
    rows = _read_csv(out / "decoder_records.csv")
    owners = {int(r["stage"]): r["syndrome_owner"] for r in rows}
    assert owners == {0: "L1", 1: "L2", 2: "L1"}
    for r in rows:
        assert int(r["stage"]) in (0, 1, 2)
        if r["stage"] == "0":
            assert int(r["unsatisfied_checks"]) >= 0
    # Each invocation has a unique slot; stage 2 is not a reuse of stage 0.
    slots = {(float(r["f"]), r["seed"], r["stage"]): int(r["slot_idx"])
             for r in rows}
    for f, seed in _identity_order():
        key0 = (f, str(seed), "0")
        key2 = (f, str(seed), "2")
        assert slots[key2] == slots[key0] + 2
    assert d7h.verify_root(out)["ok"] is True


def test_s02_stage2_unreachable_when_stage1_gate_refuses(tmp_path):
    out = tmp_path / "s02"
    source = _sequence_decoder([_outcome(d7h.N)] * 32)
    target = _sequence_decoder([_blocked_outcome(d7h.N)] * 32)
    result = d7h.run_alternating_discriminator(
        out_root=out, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": source, "TARGET": target},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result["records"] == 64
    assert source.calls["n"] == 32 and target.calls["n"] == 32
    rows = _read_csv(out / "decoder_records.csv")
    assert {r["stage"] for r in rows} == {"0", "1"}
    assert all(r["transfer_eligible"] == "False"
               for r in rows if r["stage"] == "1")
    pairs = _read_csv(out / "arm_pairs.csv")
    assert all(p["chain_complete"] == "False" for p in pairs)
    assert all(p["blocked_at_stage1"] == "False" for p in pairs)
    assert all(p["blocked_at_stage2"] == "True" for p in pairs)
    assert all(p["stage1_block_reason"] == "EXTRINSIC_NO_CHECK_EVIDENCE"
               for p in pairs)
    strata = _read_csv(out / "stratum_summary.csv")
    assert all(s["complete_chain_count"] == "0" for s in strata)
    assert all(s["stratum_label"] == "COVERAGE_BLOCKED" for s in strata)
    assert d7h.verify_root(out)["ok"] is True


# ==========================================================================
# B01 / L01-L03: endpoint AND semantics, labels, terminals
# ==========================================================================

def _fake_record(f, seed, stage, *, exact=False, syndrome_ok=False,
                 eligible=True, status="fake", finite=True, iterations=5,
                 reason=None):
    slots = {(s["f"], s["seed"], s["stage"]): s for s in d7h.frozen_slots()}
    slot = slots[(float(f), int(seed), int(stage))]
    if reason is None:
        reason = d7h.ELIGIBLE if eligible else d7h.BLOCK_NO_CHECK_EVIDENCE
    return {"slot_idx": slot["slot_idx"], "f": float(f), "seed": int(seed),
            "stage": int(stage), "stage_name": slot["stage_name"],
            "role": slot["role"], "condition": slot["condition"],
            "layer": slot["layer"], "rows": slot["rows"], "n": slot["n"],
            "exact": bool(exact), "syndrome_ok": bool(syndrome_ok),
            "syndrome_owner": slot["layer"], "iterations": iterations,
            "status": status, "finite": bool(finite),
            "symbol_errors": 0 if exact else 1,
            "unsatisfied_checks": 0 if syndrome_ok else 1,
            "wall_s": 0.0, "rss_bytes": 256 * 1024 * 1024,
            "transfer_eligible": bool(eligible),
            "transfer_block_reason": reason}


def _chain_row(f, seed, flags):
    records = []
    for stage, (exact, syn, eligible) in enumerate(flags):
        records.append(_fake_record(f, seed, stage, exact=exact,
                                    syndrome_ok=syn, eligible=eligible))
    rows = d7h.compute_chain_rows(records)
    return next(r for r in rows
                if float(r["f"]) == float(f) and r["seed"] == seed)


def test_b01_endpoint_and_semantics_and_syndrome_isolation():
    row = _chain_row(1.0, 2026091300, [(True, True, True),
                                       (True, True, True),
                                       (True, True, True)])
    assert row["l1_exact"] and row["l2_exact"] and row["l1_return_exact"]
    assert row["reference_both_layers_exact"] is True
    assert row["candidate_both_layers_exact"] is True
    assert row["chain_complete"] is True

    row = _chain_row(1.0, 2026091301, [(False, True, True),
                                       (True, False, True),
                                       (True, True, True)])
    assert row["l1_exact"] is False and row["l2_exact"] is True
    assert row["l1_syndrome_ok"] is True and row["l2_syndrome_ok"] is False
    assert row["reference_both_layers_exact"] is False  # AND only
    assert row["candidate_both_layers_exact"] is True   # l2 AND l1_return

    row = _chain_row(1.0, 2026091302, [(True, True, True),
                                       (True, True, True),
                                       (False, False, True)])
    assert row["reference_both_layers_exact"] is True
    assert row["candidate_both_layers_exact"] is False
    assert row["l1_return_exact"] is False
    assert row["l1_return_syndrome_ok"] is False

    # Syndrome never upgrades or blocks an exactness verdict.
    row = _chain_row(1.0, 2026091303, [(False, True, True),
                                       (False, True, True),
                                       (False, True, True)])
    assert not row["reference_both_layers_exact"]
    assert not row["candidate_both_layers_exact"]

    # A gate refusal on STAGE 0 blocks 1 and cascades to 2.
    row = _chain_row(1.0, 2026091304, [(True, True, False)])
    assert row["blocked_at_stage1"] is True
    assert row["blocked_at_stage2"] is True
    assert row["stage0_block_reason"] == d7h.BLOCK_NO_CHECK_EVIDENCE
    assert row["stage1_slot_idx"] == "" and row["stage2_slot_idx"] == ""
    assert row["reference_both_layers_exact"] is False


def test_l01_paired_label_boundaries_and_first_match():
    c = d7h.classify_stratum
    assert c(complete_chain_count=11, candidate_only=10,
             reference_only=0) == d7h.S_COVERAGE
    assert c(complete_chain_count=12, candidate_only=0,
             reference_only=2) == d7h.S_REGRESSION
    assert c(complete_chain_count=16, candidate_only=4,
             reference_only=0) == d7h.S_STRONG
    assert c(complete_chain_count=12, candidate_only=3,
             reference_only=1) == d7h.S_WEAK
    assert c(complete_chain_count=12, candidate_only=2,
             reference_only=1) == d7h.S_WEAK
    assert c(complete_chain_count=12, candidate_only=1,
             reference_only=2) == d7h.S_NONE
    assert c(complete_chain_count=12, candidate_only=0,
             reference_only=0) == d7h.S_NONE
    assert c(complete_chain_count=12, candidate_only=2,
             reference_only=2) == d7h.S_NONE
    # First-match order: coverage short-circuits, strong requires ref == 0.
    assert c(complete_chain_count=11, candidate_only=0,
             reference_only=5) == d7h.S_COVERAGE
    assert c(complete_chain_count=12, candidate_only=4,
             reference_only=1) == d7h.S_WEAK
    assert c(complete_chain_count=12, candidate_only=0,
             reference_only=0) == d7h.S_NONE


def test_l02_ten_terminal_priorities_and_truth_table():
    t = d7h.classify_terminal
    base = {"pre_blocked": False, "watchdog_timeout": False,
            "crash_nonfinite": False, "resource_overrun": False,
            "incomplete": False, "coverage_blocked": False,
            "strata": {1.0: d7h.S_NONE, 1.2: d7h.S_NONE}}
    assert t(dict(base, pre_blocked=True, watchdog_timeout=True)) == d7h.T_PRE_EXEC
    assert t(dict(base, watchdog_timeout=True, crash_nonfinite=True)) == d7h.T_WATCHDOG
    assert t(dict(base, crash_nonfinite=True, resource_overrun=True)) == d7h.T_CRASH
    assert t(dict(base, resource_overrun=True, incomplete=True)) == d7h.T_RESOURCE
    assert t(dict(base, incomplete=True, coverage_blocked=True)) == d7h.T_INCOMPLETE
    assert t(dict(base, coverage_blocked=True)) == d7h.T_COVERAGE
    assert t(dict(base, strata={1.0: d7h.S_STRONG,
                                1.2: d7h.S_NONE})) == d7h.T_STRONG
    assert t(dict(base, strata={1.0: d7h.S_STRONG,
                                1.2: d7h.S_REGRESSION})) == d7h.T_REGRESSION
    assert t(dict(base, strata={1.0: d7h.S_WEAK,
                                1.2: d7h.S_NONE})) == d7h.T_WEAK
    assert t(dict(base, strata={1.0: d7h.S_WEAK,
                                1.2: d7h.S_REGRESSION})) == d7h.T_REGRESSION
    assert t(dict(base, strata={1.0: d7h.S_REGRESSION,
                                1.2: d7h.S_NONE})) == d7h.T_REGRESSION
    assert t(base) == d7h.T_NO_LIFT
    assert d7h.TERMINALS == (
        "D7_H_PRE_EXECUTION_BLOCKED", "D7_H_WATCHDOG_TIMEOUT_VOID",
        "D7_H_NONFINITE_OR_CRASH_BLOCKED", "D7_H_RESOURCE_OVERRUN",
        "D7_H_INCOMPLETE_MATRIX_BLOCKED", "D7_H_PROVENANCE_COVERAGE_BLOCKED",
        "D7_H_ALTERNATING_STRONG_LIFT", "D7_H_ALTERNATING_WEAK_LIFT",
        "D7_H_ALTERNATING_REGRESSION", "D7_H_NO_USEFUL_ALTERNATING_LIFT")
    assert d7h.STRATUM_LABELS == ("COVERAGE_BLOCKED",
                                  "ALTERNATING_REGRESSION",
                                  "STRONG_ALTERNATING_LIFT",
                                  "WEAK_ALTERNATING_LIFT",
                                  "NO_ALTERNATING_LIFT")


def test_l03_loop_stop_families_and_budgets(tmp_path):
    # Watchdog: first recorded call exceeds 120 s -> one record, no retry.
    out = tmp_path / "l03_watchdog"
    result = _full_run(tmp_path, out_name=out,
                       clock=_ScriptedClock([120.5] + [0.0] * 95))
    assert result["terminal"] == d7h.T_WATCHDOG
    assert result["records"] == 1
    assert d7h.verify_root(out)["ok"] is True

    # Resource: a mid-run invalid probe stops fail-closed, no retry.
    out2 = tmp_path / "l03_resource"
    state = {"n": 0}

    def seq_probe():
        state["n"] += 1
        return (256 * 1024 * 1024) if state["n"] <= 5 else None

    result2 = _full_run(tmp_path, out_name=out2, rss_probe=seq_probe)
    assert result2["terminal"] == d7h.T_RESOURCE
    assert result2["records"] == 5
    assert d7h.verify_root(out2)["ok"] is True

    # Decoder crash: attempted-but-not-completed record, terminal crash.
    out3 = tmp_path / "l03_crash"

    def raiser(prior, syndrome, k):
        raise RuntimeError("fake crash")

    dec = _sequence_decoder([_outcome(d7h.N), _outcome(d7h.N), raiser])
    result3 = d7h.run_alternating_discriminator(
        out_root=out3, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": dec, "TARGET": dec},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result3["terminal"] == d7h.T_CRASH
    assert result3["records"] == 3
    rows3 = _read_csv(out3 / "decoder_records.csv")
    assert rows3[-1]["status"] == "crash:RuntimeError"
    assert rows3[-1]["transfer_eligible"] == "False"
    assert d7h.verify_root(out3)["ok"] is True

    # Nonfinite beliefs are a crash stop with a scalar record (no repair).
    out4 = tmp_path / "l03_nonfinite"
    bad = _outcome(d7h.N, final_beliefs=np.full((d7h.N, Q), np.nan))
    dec4 = _sequence_decoder([bad] * d7h.SLOT_COUNT)
    result4 = d7h.run_alternating_discriminator(
        out_root=out4, joint=_uniform_joint(), block_sampler=_zero_sampler(),
        decoder_fns={"SOURCE": dec4, "TARGET": dec4},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024, repo_root=REPO)
    assert result4["terminal"] == d7h.T_CRASH
    assert result4["records"] == 1
    rows4 = _read_csv(out4 / "decoder_records.csv")
    assert rows4[0]["finite"] == "False"
    assert rows4[0]["transfer_block_reason"] == "STAGE_NONFINITE"
    assert d7h.verify_root(out4)["ok"] is True

    # Truncated core matrix without any stop cause -> INCOMPLETE (crafted).
    records = [_fake_record(1.0, seed, 0, exact=True, syndrome_ok=True)
               for seed in list(d7h.BLOCK_SEEDS)[:5]]
    pairs = d7h.compute_chain_rows(records)
    strata = d7h.compute_strata(records, pairs)
    assert d7h.terminal_from_records(records, pairs, strata) == d7h.T_INCOMPLETE
    assert d7h.MAX_CALLS == 96 and d7h.MANDATORY_CALLS == 32


# ==========================================================================
# W01-W03: seven-file writer, verifier, scalar-only schema
# ==========================================================================

def test_w01_seven_file_schema_scalar_no_subdirs_no_overwrite(tmp_path):
    out = tmp_path / "w01"
    _full_run(tmp_path, out_name=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(d7h.SEVEN_FILES)
    assert not any(p.is_dir() for p in out.iterdir())
    records = _read_csv(out / "decoder_records.csv")
    paired = _read_csv(out / "arm_pairs.csv")
    strata = _read_csv(out / "stratum_summary.csv")
    assert list(records[0].keys()) == d7h.RECORD_FIELDS
    assert list(paired[0].keys()) == d7h.PAIR_FIELDS
    assert list(strata[0].keys()) == d7h.STRATUM_FIELDS
    assert len(records) == 96 and len(paired) == 32 and len(strata) == 2
    for row in records + paired + strata:
        for value in row.values():
            assert not str(value).startswith("[") and not str(value).startswith("{")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert manifest["max_calls"] == 96 and manifest["mandatory_calls"] == 32
    assert manifest["stage_order"] == list(d7h.STAGE_ORDER)
    assert manifest["call_order"] == d7h._CALL_ORDER
    assert manifest["decoder_ids"] == dict(d7h._DECODER_IDS)
    assert (out / "report.md").read_text(encoding="utf-8").strip()
    assert (out / "command_log.txt").read_text(encoding="utf-8").strip()

    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        d7h.write_root(populated, {}, [], [], [], {})
    empty_existing = tmp_path / "empty_existing"
    empty_existing.mkdir()
    with pytest.raises(FileExistsError):
        d7h.write_root(empty_existing, {}, [], [], [], {})
    subdir = tmp_path / "subdir"
    (subdir / "nested").mkdir(parents=True)
    with pytest.raises(ValueError):
        d7h.write_root(subdir, {}, [], [], [], {})

    complete = {key: "" for key in d7h.RECORD_FIELDS}
    complete.update({"slot_idx": 1, "f": 1.0, "seed": 2026091300,
                     "stage": 0, "stage_name": "SOURCE_L1_MARGINAL",
                     "role": "SOURCE", "condition": "L1_MARGINAL",
                     "layer": "L1", "rows": 49, "n": 64})
    with pytest.raises(ValueError):
        d7h.write_root(tmp_path / "bad_extra", {},
                       [dict(complete, u1_vector=[1])], [], [], {})
    with pytest.raises(ValueError):
        d7h.write_root(tmp_path / "bad_array", {},
                       [dict(complete, wall_s=np.zeros(3))], [], [], {})

    existing = tmp_path / "existing"
    existing.mkdir()
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _outcome(d7h.N)

    with pytest.raises(FileExistsError):
        d7h.run_alternating_discriminator(
            out_root=existing, joint=_uniform_joint(),
            block_sampler=_zero_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7h_execution_authorized": True}, repo_root=REPO)
    assert events == []
    with pytest.raises(ValueError):
        d7h.validate_production_out_root(tmp_path / "outside", repo_root=REPO)
    with pytest.raises(ValueError):
        d7h.validate_production_out_root(WS / "wrong_name", repo_root=REPO)
    assert d7h.validate_production_out_root(
        WS / (d7h.OUT_ROOT_PREFIX + "abc"), repo_root=REPO).name.endswith("abc")


def test_w02_verifier_tamper_cases(tmp_path):
    good = tmp_path / "w02_good"
    _full_run(tmp_path, out_name=good)
    report = d7h.verify_root(good)
    assert report["ok"] and report["records"] == 96, report

    record_lines = (good / "decoder_records.csv").read_text(
        encoding="utf-8").splitlines()

    root = _copy_root(good, tmp_path / "t_dup")
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines + [record_lines[1]]) + "\n", encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_no_stage0")
    kept = [line for line in record_lines if not line.startswith("1,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_no_stage1")
    kept = [line for line in record_lines if not line.startswith("2,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n",
                                              encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_no_last")
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines[:-1]) + "\n", encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_exact")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["exact"] = "False"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_syndrome")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["syndrome_ok"] = "False"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_gate")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["transfer_eligible"] = "False"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_reason")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["transfer_block_reason"] = "EXTRINSIC_WARM_START_UNSPECIFIED"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_prov")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["extrinsic_provenance"] = "PRIOR_ONLY"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_owner")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["syndrome_owner"] = "L2"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_payload")
    rows = _read_csv(root / "decoder_records.csv")
    rows[0]["belief_provenance"] = "[1, 2, 3]"
    _rewrite_csv(root / "decoder_records.csv", rows, d7h.RECORD_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_and")
    rows = _read_csv(root / "arm_pairs.csv")
    rows[0]["candidate_both_layers_exact"] = "False"
    _rewrite_csv(root / "arm_pairs.csv", rows, d7h.PAIR_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_pairs_count")
    rows = _read_csv(root / "arm_pairs.csv")
    _rewrite_csv(root / "arm_pairs.csv", rows[:-1], d7h.PAIR_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_strata")
    rows = _read_csv(root / "stratum_summary.csv")
    rows[0]["stratum_label"] = "ALTERNATING_REGRESSION"
    _rewrite_csv(root / "stratum_summary.csv", rows, d7h.STRATUM_FIELDS)
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_terminal")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert summary["terminal"] != d7h.T_STRONG
    summary["terminal"] = d7h.T_STRONG
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_wall")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["stored_wall_s"] = float(summary["stored_wall_s"]) + 1.0
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_manifest")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["lambda_star"] = 1.0
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    root = _copy_root(good, tmp_path / "t_extra")
    (root / "extra.txt").write_text("x", encoding="utf-8")
    assert d7h.verify_root(root)["ok"] is False

    # A legitimately truncated root (watchdog stop) still verifies.
    stopped = tmp_path / "w02_stopped"
    _full_run(tmp_path, clock=_ScriptedClock([120.5] + [0.0] * 95),
              out_name=stopped)
    assert d7h.verify_root(stopped)["ok"] is True


def test_w03_scalar_only_schema_and_forbidden_payloads(tmp_path):
    out = tmp_path / "w03"
    _full_run(tmp_path, out_name=out)
    for field in d7h.RECORD_FIELDS + d7h.PAIR_FIELDS + d7h.STRATUM_FIELDS:
        low = field.lower()
        assert "vector" not in low and "digest" not in low, field
        assert "prior" not in low or "provenance" in low, field
        assert field not in ("extrinsic_log_beliefs", "final_beliefs",
                             "beliefs"), field
    assert "belief_provenance" in d7h.RECORD_FIELDS
    assert "extrinsic_provenance" in d7h.RECORD_FIELDS
    assert "extrinsic_shape_ok" in d7h.RECORD_FIELDS
    for name in d7h.SEVEN_FILES:
        text = (out / name).read_text(encoding="utf-8")
        assert "array(" not in text and "dtype" not in text, name
    for row in _read_csv(out / "decoder_records.csv"):
        for key in ("belief_max_prob", "belief_mean_true_p",
                    "belief_mean_entropy"):
            assert row[key] == "" or float(row[key]) == float(row[key])
    pairs = _read_csv(out / "arm_pairs.csv")
    assert all("reference_both_layers_exact" in p
               and "candidate_both_layers_exact" in p for p in pairs)


# ==========================================================================
# R01-R03: protected roots, authorization state, no production reads
# ==========================================================================

def test_r01_protected_state_and_no_production_read(tmp_path, monkeypatch):
    workspace_before = sorted(p.name for p in WS.iterdir())
    model_f_before = _dir_meta(MODEL_F_ROOT)
    d7c_root = (WS / "d7_c_bidirectional_oracle_"
                "94c0ea15-a786-4cb8-a991-6fec521cccae")
    d7c_before = _dir_meta(d7c_root)
    d7e_before = _dir_meta(D7E_ROOT)
    d7f_before = _dir_meta(D7F_ROOT)
    assert d7e_before is not None and d7f_before is not None
    assert list(WS.glob(d7h.OUT_ROOT_PREFIX + "*")) == []

    def _raiser(*args, **kwargs):
        raise AssertionError("Model-F loader must not run in qualification")

    monkeypatch.setattr(d5, "_load_model_f_input_or_blocked", _raiser)
    monkeypatch.setattr(d7c, "_default_model_f_loader", _raiser)
    monkeypatch.setattr(d7h, "_default_model_f_loader", _raiser)
    _full_run(tmp_path, out_name=tmp_path / "r01")

    assert sorted(p.name for p in WS.iterdir()) == workspace_before
    assert list(WS.glob(d7h.OUT_ROOT_PREFIX + "*")) == []
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert _dir_meta(d7c_root) == d7c_before
    assert _dir_meta(D7E_ROOT) == d7e_before
    assert _dir_meta(D7F_ROOT) == d7f_before
    assert d7h._EXECUTION_CONSUMED is False
    state = d7h.read_cycle_state(D7H_CYCLE_STATE)
    for key in ("d7h_execution_authorized", "decoder_executed",
                "result_created", "implementation_authorized",
                "formal_execution_authorized", "synthetic_execution_authorized",
                "real_execution_authorized", "scientific_promotion",
                "plan_accepted", "g1_authorized", "g2_authorized"):
        assert state.get(key) is False, (key, state.get(key))
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _outcome(d7h.N)

    for protected in (D7F_ROOT, D7E_ROOT, D7D_ROOT,
                      REPO / "comparison_bench" / "outputs_comparison" / "x",
                      REPO / "results" / "x"):
        with pytest.raises((ValueError, FileExistsError)):
            d7h.run_alternating_discriminator(
                out_root=protected, joint=_uniform_joint(),
                block_sampler=_zero_sampler(),
                decoder_fns={"SOURCE": decoder, "TARGET": decoder},
                state={"d7h_execution_authorized": True}, repo_root=REPO)
    assert events == []


def test_r02_unauthorized_refusal_before_any_work(tmp_path, monkeypatch):
    events = []

    def _raiser(*args, **kwargs):
        events.append("touched")
        raise AssertionError("must not run before authorization")

    monkeypatch.setattr(d7h, "bind_row_layered_decoders", _raiser)
    monkeypatch.setattr(d7h, "_default_model_f_loader", _raiser)

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _outcome(d7h.N)

    for state in ({}, {"d7h_execution_authorized": False},
                  {"d7h_execution_authorized": 0}):
        out = tmp_path / ("r02_%d" % len(events))
        with pytest.raises(d7h.NotAuthorizedError) as excinfo:
            d7h.run_alternating_discriminator(
                out_root=out, decoder_fns={"SOURCE": decoder, "TARGET": decoder},
                state=state, repo_root=REPO)
        assert d7h.T_PRE_EXEC in str(excinfo.value)
        assert not out.exists()
    assert events == []
    assert d7h._EXECUTION_CONSUMED is False
    assert d7h.is_authorized({"d7h_execution_authorized": True}) is True
    assert d7h.is_authorized({}) is False


def test_r03_wrong_model_f_root_refuses_before_bind(tmp_path):
    def _raising_loader(root):
        raise AssertionError("Model-F loader must not run with wrong root")

    with pytest.raises(d7h.PreflightBlocked) as excinfo:
        d7h.prepare_inputs(model_f_root="workspace/elsewhere",
                           model_f_loader=_raising_loader,
                           block_sampler=_zero_sampler(), repo=REPO)
    assert d7h.T_PRE_EXEC in str(excinfo.value)
    assert d7h.model_f_root_matches(d7h.MODEL_F_ROOT, repo_root=REPO) is True
    assert d7h.model_f_root_matches("workspace/elsewhere",
                                    repo_root=REPO) is False
    assert d7h.model_f_root_matches(None, repo_root=REPO) is False

    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _outcome(d7h.N)

    out = tmp_path / "r03"
    with pytest.raises(d7h.PreflightBlocked):
        d7h.run_alternating_discriminator(
            out_root=out, model_f_root="workspace/elsewhere",
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7h_execution_authorized": True}, repo_root=REPO)
    assert events == [] and not out.exists()


# ==========================================================================
# X01-X05: launch isolation, sentinels, helper contract, regressions
# ==========================================================================

def test_x01_lazy_import_help_dry_run_and_unauthorized_isolation(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    assert _run_cli([str(RUNNER), "--help"], cwd=REPO).returncode == 0
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-H" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("slots=96 mandatory=32 budget=96")
    assert len(lines) == 97
    assert lines[1].split()[3:7] == ["SOURCE_L1_MARGINAL", "SOURCE",
                                     "L1_MARGINAL", "L1"]
    assert lines[1].split()[2] == "2026091300"
    assert lines[2].split()[3:5] == ["FORWARD_L1_TO_L2", "TARGET"]
    assert lines[3].split()[3] == "BACKWARD_L2_TO_L1"
    assert lines[96].split()[0] == "96"
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7h_x01')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "print('X01_OK')\n")
    result = subprocess.run([sys.executable, "-c", probe, str(RUNNER)],
                            cwd=str(external), env=_clean_env(),
                            capture_output=True, text=True, timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "X01_OK" in result.stdout

    target = WS / (d7h.OUT_ROOT_PREFIX + "unauthorized_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7h.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3
    assert "not authorized" in result.stdout
    assert "D7_H_PRE_EXECUTION_BLOCKED" in result.stdout
    assert not target.exists()
    bad_shape = tmp_path / "bad_shape"
    result = _run_cli([str(RUNNER), "--model-f-root", d7h.MODEL_F_ROOT,
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


def test_x02_external_cwd_sentinel_zero_real_binding(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    out_root = external / "never_created"
    code = r'''
import pathlib
import runpy
import sys

import numpy as np

g = runpy.run_path(sys.argv[1], run_name="d7h_x02")
mod = g["_mod"]
external = pathlib.Path(sys.argv[2])
out_root = pathlib.Path(sys.argv[3])
assert mod.bind_row_layered_decoders is mod.d7f.bind_row_layered_decoders
assert mod.dispatch_decoder is mod.d7f.dispatch_decoder
assert mod._default_model_f_loader is mod.d7f._default_model_f_loader


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

joint = np.full((32, 32, mod.BOB_DIM), 1.0 / (32 * 32))


def sampler(p_b, p_f, n, seed):
    z = np.zeros(64, dtype=np.int64)
    return {"bob": z, "u1": z, "u2": z}


def boom(hh, pp, ss):
    events.append(("boom",))
    raise Sentinel("boom")


try:
    mod.run_alternating_discriminator(
        out_root=out_root, joint=joint, block_sampler=sampler,
        decoder_fns={"SOURCE": boom, "TARGET": boom},
        state={"d7h_execution_authorized": True},
        rss_probe=lambda: 256 * 1024 * 1024)
except Sentinel as exc:
    assert str(exc) == "boom"
else:
    raise AssertionError("sentinel must propagate")

assert events == [("src", (2, 4), (4, 32), (2,)),
                  ("tgt", (2, 4), (4, 32), (2,)),
                  ("boom",)], events
assert not out_root.exists()
assert list(external.iterdir()) == []
print("X02_OK")
'''
    result = subprocess.run(
        [sys.executable, "-c", code, str(RUNNER), str(external),
         str(out_root)],
        cwd=str(external), env=_clean_env(), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "X02_OK" in result.stdout
    assert not out_root.exists()


def test_x03_d7g_helper_contract_used():
    assert d7h.EXTRINSIC_CHECK_EXTRINSIC == v35.EXTRINSIC_CHECK_EXTRINSIC \
        == "CHECK_EXTRINSIC"
    assert d7h.EXTRINSIC_NO_CHECK_EVIDENCE == v35.EXTRINSIC_NO_CHECK_EVIDENCE
    assert (d7h.EXTRINSIC_WARM_START_UNSPECIFIED
            == v35.EXTRINSIC_WARM_START_UNSPECIFIED)
    assert d7h.EXTRINSIC_PROVENANCE_TOKENS == \
        v35.EXTRINSIC_PROVENANCE_TOKENS
    assert d7h.unusable_extrinsic_error() is v35.UnusableExtrinsicError
    for prov in (None, "NO_CHECK_EVIDENCE", "WARM_START_UNSPECIFIED", "BOGUS",
                 "", 0, "CHECK_UPDATED", "PRIOR_ONLY"):
        with pytest.raises(v35.UnusableExtrinsicError):
            d7h.require_check_extrinsic_for_transfer(
                np.zeros((2, 32)), prov, consumer="t", expected_n=2)
    for arr in (None, np.zeros(32), np.zeros((2, 31)), np.zeros((2, 33)),
                np.full((2, 32), np.nan), np.zeros((3, 2, 32))):
        with pytest.raises(v35.UnusableExtrinsicError):
            d7h.require_check_extrinsic_for_transfer(
                arr, "CHECK_EXTRINSIC", consumer="t", expected_n=2)
    q = d7h.require_check_extrinsic_for_transfer(
        np.zeros((2, 32)), "CHECK_EXTRINSIC", consumer="t", expected_n=2)
    assert q.shape == (2, 32)
    assert float(np.max(np.abs(q.sum(axis=1) - 1.0))) <= 1e-12
    with pytest.raises(v35.UnusableExtrinsicError):
        d7h.require_check_extrinsic_for_transfer(
            np.zeros((2, 32)), "CHECK_EXTRINSIC", consumer="t", expected_n=3)
    # The extrinsic namespace never satisfies the belief gate and vice versa.
    assert d7h.is_authorized({"d7h_execution_authorized": True}) is True


def test_x04_d7c_d7d_import_and_behavior_independence():
    assert "v72p2d7_gf32_schedule_discriminator" not in sys.modules
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "v72p2d7_gf32_schedule_discriminator" not in source
    assert "d7d" not in source
    before = (d7c.MAX_CALLS, d7c.CONDITIONS, d7c.LAMBDA_STAR,
              len(d7c.frozen_identities()))
    assert before == (128, ("L1_MARGINAL", "L1_ORACLE_U2", "L2_MARGINAL",
                            "L2_ORACLE_U1"), 137.3823795883264, 128)
    assert d7f.SLOT_COUNT == 128 and d7f.MAX_CALLS == 128
    rng = np.random.default_rng(20260915)
    raw = rng.random((Q, Q, 4)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    block = {"bob": np.array([0, 1, 2, 3]),
             "u1": np.array([1, 2, 3, 4]), "u2": np.array([5, 6, 7, 8]),
             "alice": np.array([37, 70, 103, 136])}
    ref_l1 = d7c.condition_prior_qn(joint, "L1_MARGINAL", block).copy()
    assert np.array_equal(d7h.condition_prior_qn(joint, "L1_MARGINAL", block),
                          ref_l1)
    assert "v72p2d7_gf32_schedule_discriminator" not in sys.modules


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


def test_a2_01_parse_alias_and_strict_limit_boundary(tmp_path):
    assert d7h.parse_vmhwm_rss_bytes is d7f.parse_vmhwm_rss_bytes
    assert d7h._probe_rss_valid is d7f._probe_rss_valid
    assert d7h.parse_vmhwm_rss_bytes(
        _a2_status("VmHWM:\t   48256 kB")) == 48256 * 1024
    assert d7h.parse_vmhwm_rss_bytes("VmHWM: 0 kB\n") is None
    assert d7h.parse_vmhwm_rss_bytes("VmHWM: nope kB\n") is None
    assert d7h.parse_vmhwm_rss_bytes("VmHWM: 1.5 kB\n") is None
    limit = d7h.RSS_LIMIT_BYTES
    assert limit == 2 * 1024**3
    out = tmp_path / "a2_ok"
    result = _full_run(tmp_path, out_name=out,
                       rss_probe=lambda: limit - 1024)
    assert result["records"] == 96 and result["terminal"] != d7h.T_RESOURCE
    assert d7h.verify_root(out)["ok"] is True
    out2 = tmp_path / "a2_boundary"
    result2 = _full_run(tmp_path, out_name=out2, rss_probe=lambda: limit)
    assert result2["terminal"] == d7h.T_RESOURCE
    assert result2["records"] == 1
    assert d7h.verify_root(out2)["ok"] is True


def test_a2_02_preflight_none_blocks_before_first_decoder(tmp_path):
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _outcome(d7h.N)

    out = tmp_path / "a2_pre"
    with pytest.raises(d7h.PreflightBlocked) as excinfo:
        d7h.run_alternating_discriminator(
            out_root=out, joint=_uniform_joint(),
            block_sampler=_zero_sampler(),
            decoder_fns={"SOURCE": decoder, "TARGET": decoder},
            state={"d7h_execution_authorized": True},
            rss_probe=lambda: None, repo_root=REPO)
    assert excinfo.value.terminal == d7h.T_PRE_EXEC
    assert events == [] and not out.exists()


def test_a2_03_rss_schema_invariant(tmp_path):
    assert d7h.RECORD_FIELDS.count("rss_bytes") == 1
    out = tmp_path / "a2_schema"
    _full_run(tmp_path, out_name=out)
    rows = _read_csv(out / "decoder_records.csv")
    assert {r["rss_bytes"] for r in rows} == {str(256 * 1024 * 1024)}
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rss_limit_bytes"] == 2 * 1024**3
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["peak_rss_bytes"] == 256 * 1024 * 1024
    assert d7h.verify_root(out)["ok"] is True
