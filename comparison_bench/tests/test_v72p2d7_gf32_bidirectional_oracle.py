"""D7-C bidirectional-oracle qualification C01-C20 (fake/DI only).

No test creates ``workspace/d7_c_bidirectional_oracle_*`` or reads real Model-F
content; every decoder is an injected fake. Real D5 n=64 mothers are built in
memory only where noted (C06/C19). The production v35 decoder is never called.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "comparison_bench" / "src"
CORE_PATH = (SRC / "comparison_bench" / "formal_ir"
             / "v72p2d7_gf32_bidirectional_oracle.py")
RUNNER = REPO / "scripts" / "v72p2d7_gf32_bidirectional_oracle.py"
WS = REPO / "workspace"
MODEL_F_ROOT = WS / "v72p2d5_model_f_input" / "20260907_r1"
CYCLE_STATE = (REPO / "docs" / "research_cycles"
               / "V72P2D7-GF32-BIDIRECTIONAL-ORACLE" / "cycle_state.yaml")
TEST_FILE = Path(__file__).resolve()
D7A_FILE = TEST_FILE.parent / "test_v72p2d7_gf32_decoder_certification.py"
D7B_FILE = TEST_FILE.parent / "test_v72p2d7_gf32_easy_regime.py"
D5_FILE = TEST_FILE.parent / "test_v72p2d5_gf32_rate_mother.py"
SUB_TIMEOUT = 600


def _load_core_isolated():
    """Load the D7-C core by file path without leaving package-cache residue."""
    saved = {k: v for k, v in sys.modules.items()
             if k == "comparison_bench" or k.startswith("comparison_bench.")}
    for key in saved:
        sys.modules.pop(key, None)
    try:
        spec = importlib.util.spec_from_file_location(
            "d7c_bidirectional_oracle_under_test", str(CORE_PATH))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        for key in [k for k in sys.modules
                    if k == "comparison_bench" or k.startswith("comparison_bench.")]:
            sys.modules.pop(key, None)
        sys.modules.update(saved)
    return mod


bo = _load_core_isolated()

_OBS_MARGINAL_ITERATIONS = 1


# --------------------------------------------------------------------------
# Shared fake fixtures (no real Model-F / decoder)
# --------------------------------------------------------------------------

def _perfect_oracle_joint() -> np.ndarray:
    """J such that oracle priors peak at truth and marginals are flat.

    ``J[u1,u2,b] = B[u1,u2]/32`` with a cyclic
    ``B = 1/32 + c*(delta[u1=u2+1] - delta[u1=u2])``: every row/column sums to
    ``1`` (marginals uniform -> tie at q=0) while ``B[:,u2]`` peaks at
    ``u2+1`` and ``B[u1,:]`` peaks at ``u1-1`` (both oracle priors exact for
    the paired block truths below).
    """
    base = np.full((bo.Q, bo.Q), 1.0 / bo.Q)
    for u2 in range(bo.Q):
        base[(u2 + 1) % bo.Q, u2] += 1.0 / 64.0
        base[u2, u2] -= 1.0 / 64.0
    return np.repeat((base / float(bo.Q))[:, :, None], bo.BOB_DIM, axis=2)


def _perfect_oracle_block(seed) -> dict:
    bob = ((np.arange(bo.N) * 13 + int(seed)) % bo.BOB_DIM).astype(np.int64)
    u2 = (bob % 30) + 1
    u1 = u2 + 1
    return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * bo.Q + u2}


def _argmax_decoder(iterations: int = _OBS_MARGINAL_ITERATIONS):
    def decode(h, prior, syndrome):
        p = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.argmax(p, axis=1).astype(np.int64),
                "syndrome_ok": True, "iterations": int(iterations),
                "final_beliefs": np.log(p + 1e-300), "status": "fake_argmax"}

    return decode


def _sampler(events=None):
    def sample(p_b, p_f, n, seed):
        if events is not None:
            events.append(("sample", int(seed)))
        return _perfect_oracle_block(seed)

    return sample


class _ScriptedClock:
    """Deterministic clock: call k costs ``walls[k]`` seconds."""

    def __init__(self, walls):
        self.walls = list(walls)
        self.t = 0.0
        self.k = 0
        self._pending = None

    def __call__(self):
        if self._pending is None:
            self._pending = (self.walls[self.k] if self.k < len(self.walls) else 0.0)
            return self.t
        self.t += self._pending
        self._pending = None
        self.k += 1
        return self.t


def _full_run(tmp_path, name="root", *, decoder=None, sampler=None, clock=None,
              rss_probe=None, joint=None, mothers=None, state=None,
              out_name=None, command_str="fake qualification"):
    out = Path(out_name) if out_name is not None else (tmp_path / name)
    return bo.run_bidirectional_oracle(
        out_root=out,
        joint=_perfect_oracle_joint() if joint is None else joint,
        block_sampler=_sampler() if sampler is None else sampler,
        mothers=mothers,
        decode_fn=_argmax_decoder() if decoder is None else decoder,
        state={"d7c_execution_authorized": True} if state is None else state,
        clock=clock,
        rss_probe=rss_probe if rss_probe is not None else (lambda: 256 * 1024 * 1024),
        command_str=command_str, repo_root=REPO)


def _read_csv(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


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


# --------------------------------------------------------------------------
# C01-C04: frozen matrix, block reuse, prior formulas, axis negative controls
# --------------------------------------------------------------------------

def test_c01_frozen_128_identity_matrix_and_order():
    identities = bo.frozen_identities()
    assert len(identities) == 128 and bo.MAX_CALLS == 128
    assert bo.BLOCK_SEEDS == tuple(range(2026091300, 2026091316))
    assert identities[0] == {"call_idx": 1, "f": 1.0, "seed": 2026091300,
                             "condition": "L1_MARGINAL", "layer": "L1",
                             "rows": 49, "n": 64}
    assert identities[3]["condition"] == "L2_ORACLE_U1"
    assert identities[3]["layer"] == "L2" and identities[3]["rows"] == 43
    assert identities[4]["seed"] == 2026091301
    assert identities[63] == {"call_idx": 64, "f": 1.0, "seed": 2026091315,
                              "condition": "L2_ORACLE_U1", "layer": "L2",
                              "rows": 43, "n": 64}
    assert identities[64] == {"call_idx": 65, "f": 1.2, "seed": 2026091300,
                              "condition": "L1_MARGINAL", "layer": "L1",
                              "rows": 59, "n": 64}
    assert identities[127]["f"] == 1.2 and identities[127]["seed"] == 2026091315
    assert identities[127]["condition"] == "L2_ORACLE_U1"
    assert identities[127]["rows"] == 52
    keys = [(i["f"], i["seed"], i["condition"]) for i in identities]
    assert len(set(keys)) == 128
    assert [i["f"] for i in identities[:64]] == [1.0] * 64
    assert [i["f"] for i in identities[64:]] == [1.2] * 64
    for start in range(0, 128, 4):
        assert [i["condition"] for i in identities[start:start + 4]] == list(bo.CONDITIONS)
        assert len({i["seed"] for i in identities[start:start + 4]}) == 1
    for identity in identities:
        assert identity["rows"] == bo.ROWS[identity["layer"]][identity["f"]]
        assert identity["n"] == 64
    assert bo.CONDITIONS == ("L1_MARGINAL", "L1_ORACLE_U2", "L2_MARGINAL", "L2_ORACLE_U1")
    assert bo.ROWS == {"L1": {1.0: 49, 1.2: 59}, "L2": {1.0: 43, 1.2: 52}}


def test_c02_blocks_sampled_once_per_seed_and_reused_across_f(tmp_path):
    events = []

    def sampler(p_b, p_f, n, seed):
        events.append(("sample", int(seed)))
        return _perfect_oracle_block(seed)

    captured = []

    def decoder(h, prior, syndrome):
        events.append(("decode", len(captured)))
        captured.append(np.array(prior, dtype=np.float64, copy=True))
        return _argmax_decoder()(h, prior, syndrome)

    _full_run(tmp_path, sampler=sampler, decoder=decoder, out_name=tmp_path / "c02")
    assert [seed for kind, seed in events if kind == "sample"] == list(bo.BLOCK_SEEDS)
    assert len(captured) == 128
    # All 16 blocks are sampled before the first decoder call and only once.
    first_decode = next(idx for idx, value in enumerate(events) if value[0] == "decode")
    assert all(kind == "sample" for kind, _ in events[:first_decode])
    assert first_decode == 16
    # Same seed/condition prior for both f (same block + same J; rows differ only).
    for seed_index in range(16):
        for condition_index in range(4):
            left = captured[seed_index * 4 + condition_index]
            right = captured[64 + seed_index * 4 + condition_index]
            assert np.array_equal(left, right)


def test_c03_four_prior_formulas_match_literal_tensor_calculations():
    rng = np.random.default_rng(20260913)
    raw = rng.random((bo.Q, bo.Q, 5)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 4, 2, 3, 1, 4])
    u1 = np.array([3, 7, 31, 0, 15, 2])
    u2 = np.array([5, 1, 29, 8, 30, 6])
    block = {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * bo.Q + u2}
    n = bob.shape[0]

    got_l1_marginal = bo.condition_prior_qn(joint, "L1_MARGINAL", block)
    want_l1_marginal = np.stack([joint[:, :, b].sum(axis=1) for b in bob], axis=1)
    assert got_l1_marginal.shape == (bo.Q, n)
    assert np.allclose(got_l1_marginal, want_l1_marginal, atol=1e-12, rtol=0)

    got_l2_marginal = bo.condition_prior_qn(joint, "L2_MARGINAL", block)
    want_l2_marginal = np.stack([joint[:, :, b].sum(axis=0) for b in bob], axis=1)
    assert np.allclose(got_l2_marginal, want_l2_marginal, atol=1e-12, rtol=0)

    got_l1_oracle = bo.condition_prior_qn(joint, "L1_ORACLE_U2", block)
    want_l1_oracle = np.zeros((bo.Q, n))
    for i in range(n):
        sl = joint[:, u2[i], bob[i]]
        want_l1_oracle[:, i] = sl / sl.sum()
    assert np.allclose(got_l1_oracle, want_l1_oracle, atol=1e-12, rtol=0)

    got_l2_oracle = bo.condition_prior_qn(joint, "L2_ORACLE_U1", block)
    want_l2_oracle = np.zeros((bo.Q, n))
    for i in range(n):
        sl = joint[u1[i], :, bob[i]]
        want_l2_oracle[:, i] = sl / sl.sum()
    assert np.allclose(got_l2_oracle, want_l2_oracle, atol=1e-12, rtol=0)

    assert np.allclose(got_l1_oracle.sum(axis=0), 1.0, atol=1e-12)
    assert np.allclose(got_l2_oracle.sum(axis=0), 1.0, atol=1e-12)
    # Marginal rows are already normalized over the layer axis.
    assert np.allclose(got_l1_marginal.sum(axis=0), 1.0, atol=1e-12)
    assert np.allclose(got_l2_marginal.sum(axis=0), 1.0, atol=1e-12)
    # Zero-mass oracle slice falls back to uniform 1/32 for that position
    # (mass moved inside the same Bob column so the tensor stays normalized).
    sparse = joint.copy()
    column_mass = sparse[:, u2[0], bob[0]].sum()
    sparse[:, u2[0], bob[0]] = 0.0
    sparse[0, (u2[0] + 1) % bo.Q, bob[0]] += column_mass
    fallback = bo.condition_prior_qn(sparse, "L1_ORACLE_U2", block)
    assert np.allclose(fallback[:, 0], np.full(bo.Q, 1.0 / bo.Q), atol=1e-15)


def test_c04_axis_swap_negative_controls_fail():
    rng = np.random.default_rng(20260914)
    raw = rng.random((bo.Q, bo.Q, 4)) + 0.02
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 1, 2, 3])
    u1 = np.array([3, 11, 29, 7])
    u2 = np.array([5, 13, 31, 2])
    block = {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * bo.Q + u2}

    l1_marginal = bo.condition_prior_qn(joint, "L1_MARGINAL", block)
    swapped_marginal = bo.condition_prior_qn(joint, "L2_MARGINAL", block)
    assert float(np.max(np.abs(l1_marginal - swapped_marginal))) > 1e-6

    l1_oracle = bo.condition_prior_qn(joint, "L1_ORACLE_U2", block)
    wrong_u_axis = np.stack(
        [joint[:, u1[i], bob[i]] / joint[:, u1[i], bob[i]].sum() for i in range(4)],
        axis=1)
    assert float(np.max(np.abs(l1_oracle - wrong_u_axis))) > 1e-6

    l2_oracle = bo.condition_prior_qn(joint, "L2_ORACLE_U1", block)
    wrong_u2_axis = np.stack(
        [joint[u2[i], :, bob[i]] / joint[u2[i], :, bob[i]].sum() for i in range(4)],
        axis=1)
    assert float(np.max(np.abs(l2_oracle - wrong_u2_axis))) > 1e-6

    swapped_layer_axes = joint.transpose(1, 0, 2)
    swapped_oracle = np.stack(
        [swapped_layer_axes[u1[i], :, bob[i]]
         / swapped_layer_axes[u1[i], :, bob[i]].sum() for i in range(4)], axis=1)
    assert float(np.max(np.abs(l2_oracle - swapped_oracle))) > 1e-6


# --------------------------------------------------------------------------
# C05-C08: boundary floor, mother prefixes, non-persistence, pair sharing
# --------------------------------------------------------------------------

def test_c05_positivity_normalization_and_single_floor(tmp_path, monkeypatch):
    raw = np.zeros((bo.Q, 4))
    raw[0, 0] = 1.0
    raw[:, 1] = 1e-20
    raw[3, 2] = 1.0
    raw[:, 3] = 1.0 / bo.Q
    prior_pq = bo.decoder_prior(raw)
    expected = np.maximum(raw.T, bo.DECODER_FLOOR)
    expected = expected / expected.sum(axis=1, keepdims=True)
    assert np.all(prior_pq > 0)
    assert np.allclose(prior_pq.sum(axis=1), 1.0, atol=1e-15)
    assert np.allclose(prior_pq, expected, atol=1e-15, rtol=0)

    zero_slice = bo._normalized_oracle_slice(np.zeros((bo.Q, 3)))
    assert np.allclose(zero_slice, 1.0 / bo.Q)

    original = bo.d5._floor_renorm
    counter = {"n": 0}

    def counting_floor(prior, floor):
        counter["n"] += 1
        return original(prior, floor)

    monkeypatch.setattr(bo.d5, "_floor_renorm", counting_floor)
    _full_run(tmp_path, out_name=tmp_path / "c05")
    assert counter["n"] == 128  # exactly one boundary floor per dispatched prior

    source = CORE_PATH.read_text(encoding="utf-8")
    assert source.count("_floor_renorm(") == 1
    assert "np.clip" not in source and "clip(" not in source


def test_c06_rows_and_mother_prefix_identity(tmp_path):
    mother_l1 = bo.d5.build_dv3_nested_mother(64, 64, 49, 2026090501, None)
    mother_l2 = bo.d5.build_dv3_nested_mother(64, 64, 43, 2026090502, None)
    assert np.array_equal(bo.build_mother("L1"), mother_l1)
    assert np.array_equal(bo.build_mother("L2"), mother_l2)
    captured = []

    def decoder(h, prior, syndrome):
        captured.append(np.array(h, copy=True))
        return _argmax_decoder()(h, prior, syndrome)

    _full_run(tmp_path, decoder=decoder, mothers=None, out_name=tmp_path / "c06")
    assert len(captured) == 128
    for identity, got in zip(bo.frozen_identities(), captured):
        expected = (mother_l1 if identity["layer"] == "L1" else mother_l2)[:identity["rows"]]
        assert got.shape == (identity["rows"], bo.N)
        assert np.array_equal(got, expected)
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "build_dv3_nested_support(N, N, L1_K_MIN, L1_GRAPH_SEED)" in source
    assert "build_dv3_nested_support(N, N, L2_K_MIN, L2_GRAPH_SEED)" in source
    assert "assign_gf32_coefficients(support, L1_GRAPH_SEED, None, N)" in source
    assert "assign_gf32_coefficients(support, L2_GRAPH_SEED, None, N)" in source
    assert bo.L1_GRAPH_SEED == 2026090501 and bo.L2_GRAPH_SEED == 2026090502


def test_c07_oracle_truth_only_selects_prior_and_is_never_persisted(tmp_path):
    out = tmp_path / "c07"
    _full_run(tmp_path, out_name=out)
    text = "".join((out / name).read_text(encoding="utf-8") for name in bo.SIX_FILES)
    for seed in bo.BLOCK_SEEDS:
        block = _perfect_oracle_block(seed)
        assert json.dumps([int(v) for v in block["u1"]]) not in text
        assert json.dumps([int(v) for v in block["u2"]]) not in text
        assert json.dumps([int(v) for v in block["bob"]]) not in text
    for token in ("u1_true", "u2_true", "oracle_truth", "block_vector"):
        assert token not in text
    frozen_fields = set(bo.RECORD_FIELDS) | set(bo.PAIRED_FIELDS)
    assert not any(field.endswith("_vector") or field in ("u1", "u2", "bob")
                   for field in frozen_fields)
    # Oracle truth changes the oracle prior but never the marginal prior.
    joint = _perfect_oracle_joint()
    block_a = _perfect_oracle_block(2026091300)
    block_b = dict(block_a)
    block_b["u2"] = (block_a["u2"] + 3) % bo.Q
    assert np.array_equal(
        bo.condition_prior_qn(joint, "L1_MARGINAL", block_a),
        bo.condition_prior_qn(joint, "L1_MARGINAL", block_b))
    assert not np.array_equal(
        bo.condition_prior_qn(joint, "L1_ORACLE_U2", block_a),
        bo.condition_prior_qn(joint, "L1_ORACLE_U2", block_b))


def test_c08_marginal_oracle_pair_shares_h_syndrome_and_config(tmp_path):
    seen = []

    def decoder(*args, **kwargs):
        seen.append((args, kwargs))
        return _argmax_decoder()(*args, **kwargs)

    _full_run(tmp_path, decoder=decoder, out_name=tmp_path / "c08")
    assert len(seen) == 128
    identities = bo.frozen_identities()
    for idx, (args, kwargs) in enumerate(seen):
        assert len(args) == 3 and kwargs == {}
        h_prefix, prior, syndrome = args
        identity = identities[idx]
        assert np.asarray(h_prefix).shape == (identity["rows"], bo.N)
        assert np.asarray(prior).shape == (bo.N, bo.Q)
        assert np.asarray(syndrome).shape == (identity["rows"],)
        assert bo.ROWS[identity["layer"]][identity["f"]] == identity["rows"]
    for start in (0, 2):
        for pair_start in range(start, 128, 4):
            h_a, prior_a, syn_a = seen[pair_start][0]
            h_b, prior_b, syn_b = seen[pair_start + 1][0]
            assert np.array_equal(h_a, h_b)
            assert np.array_equal(syn_a, syn_b)
            assert np.array_equal(prior_a, prior_b) is False
    assert bo.MAX_ITER == 90 and bo.DAMPING_ALPHA == 1.0
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "warm_beliefs" not in source
    assert "oracle_l2_prior" not in source


# --------------------------------------------------------------------------
# C09-C12: strata, terminals, cap, budgets
# --------------------------------------------------------------------------

def _synthetic_record(f, seed, condition, exact, syndrome_ok=True, finite=True,
                      iterations=1, status="ok"):
    layer = bo.CONDITION_LAYER[condition]
    conditioned = iterations > 0
    return {
        "call_idx": 0, "f": f, "seed": seed, "condition": condition,
        "layer": layer, "rows": bo.ROWS[layer][f], "n": bo.N,
        "exact": exact, "syndrome_ok": syndrome_ok, "iterations": iterations,
        "status": status, "finite": finite,
        "symbol_errors": 0 if exact else 1, "unsatisfied_checks": 0,
        "wall_s": 0.1, "rss_bytes": 1024, "belief_max_prob": 1.0,
        "belief_mean_true_p": 1.0, "belief_mean_entropy": 0.0,
        "beliefs_conditioned": conditioned,
        "current_belief_label": (bo.CHECK_UPDATED_CURRENT_BELIEF if conditioned
                                 else bo.PRIOR_ONLY_CURRENT_BELIEF),
    }


def test_c09_stratum_thresholds_and_boundaries():
    classify = bo.classify_stratum
    assert classify(16, 4, 4, 1, 0, 0) == bo.S_STRONG
    assert classify(0, 4, 4, 0, 0, 0) == bo.S_STRONG
    assert classify(0, 3, 4, 0, 0, 0) != bo.S_STRONG
    assert classify(0, 4, 3, 0, 0, 0) != bo.S_STRONG
    assert classify(0, 4, 4, 2, 0, 0) != bo.S_STRONG
    assert classify(0, 4, 4, 0, 1, 0) != bo.S_STRONG
    assert classify(0, 4, 4, 0, 0, 1) != bo.S_STRONG
    assert classify(1, 1, 1, 1, 0, 0) == bo.S_NO_RECOVERY
    assert classify(0, 1, 1, 0, 0, 0) == bo.S_NO_RECOVERY
    assert classify(0, 2, 2, 0, 0, 0) != bo.S_NO_RECOVERY
    assert classify(2, 1, 1, 1, 0, 0) != bo.S_NO_RECOVERY
    assert classify(12, 2, 1, 1, 0, 0) == bo.S_MARGINAL
    assert classify(11, 2, 1, 1, 0, 0) == bo.S_AMBIGUOUS
    assert classify(16, 16, 16, 0, 0, 0) == bo.S_STRONG
    assert classify(5, 5, 2, 1, 0, 0) == bo.S_AMBIGUOUS

    # Incomplete strata keep partial counts and an empty label.
    records = []
    for seed in bo.BLOCK_SEEDS:
        records.append(_synthetic_record(1.0, seed, "L1_MARGINAL", False))
        records.append(_synthetic_record(1.0, seed, "L1_ORACLE_U2", True))
    rows = bo.compute_paired_rows(records)
    l1_row = [r for r in rows if r["f"] == 1.0 and r["layer"] == "L1"][0]
    assert l1_row["stratum_label"] == bo.S_STRONG
    # L2 strata are entirely absent -> never a fabricated label.
    l2_row = [r for r in rows if r["f"] == 1.0 and r["layer"] == "L2"][0]
    assert l2_row["stratum_label"] == "" and l2_row["marginal_exact_count"] == 0
    # Missing one oracle record in an otherwise full stratum -> no label.
    records = []
    for seed in bo.BLOCK_SEEDS:
        records.append(_synthetic_record(1.0, seed, "L1_MARGINAL", False))
        if seed != bo.BLOCK_SEEDS[-1]:
            records.append(_synthetic_record(1.0, seed, "L1_ORACLE_U2", True))
    l1_row = [r for r in bo.compute_paired_rows(records)
              if r["f"] == 1.0 and r["layer"] == "L1"][0]
    assert l1_row["stratum_label"] == ""
    assert l1_row["oracle_exact_count"] == 15 and l1_row["marginal_exact_count"] == 0
    # Full finite stratum gets its label.
    records.append(_synthetic_record(1.0, bo.BLOCK_SEEDS[-1], "L1_ORACLE_U2", True))
    l1_row = [r for r in bo.compute_paired_rows(records)
              if r["f"] == 1.0 and r["layer"] == "L1"][0]
    assert l1_row["stratum_label"] == bo.S_STRONG
    # A nonfinite call in an otherwise full stratum blocks the label.
    records[-1] = _synthetic_record(1.0, bo.BLOCK_SEEDS[-1], "L1_ORACLE_U2",
                                    True, finite=False)
    l1_row = [r for r in bo.compute_paired_rows(records)
              if r["f"] == 1.0 and r["layer"] == "L1"][0]
    assert l1_row["stratum_label"] == "" and l1_row["nonfinite_count"] == 1


def test_c10_all_run_terminals_and_priority(tmp_path):
    ambiguous = {(1.0, "L1"): bo.S_AMBIGUOUS, (1.0, "L2"): bo.S_AMBIGUOUS,
                 (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_AMBIGUOUS}
    base = {"pre_blocked": False, "watchdog_timeout": False,
            "crash_nonfinite": False, "resource_overrun": False,
            "incomplete": False, "strata": ambiguous}
    assert bo.classify_terminal(base) == bo.T_MIXED
    for key, terminal in (("pre_blocked", bo.T_PRE_EXEC),
                          ("watchdog_timeout", bo.T_WATCHDOG),
                          ("crash_nonfinite", bo.T_CRASH),
                          ("resource_overrun", bo.T_RESOURCE),
                          ("incomplete", bo.T_INCOMPLETE)):
        agg = dict(base)
        agg[key] = True
        assert bo.classify_terminal(agg) == terminal
    everything = {"pre_blocked": True, "watchdog_timeout": True,
                  "crash_nonfinite": True, "resource_overrun": True,
                  "incomplete": True, "strata": ambiguous}
    assert bo.classify_terminal(everything) == bo.T_PRE_EXEC
    assert bo.classify_terminal(dict(everything, pre_blocked=False)) == bo.T_WATCHDOG
    assert bo.classify_terminal(dict(everything, pre_blocked=False,
                                     watchdog_timeout=False)) == bo.T_CRASH

    strong_l1 = dict(base, strata={(1.0, "L1"): bo.S_STRONG, (1.0, "L2"): bo.S_AMBIGUOUS,
                                   (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_AMBIGUOUS})
    assert bo.classify_terminal(strong_l1) == bo.T_L1_DEPENDS
    strong_l2 = dict(base, strata={(1.0, "L1"): bo.S_AMBIGUOUS, (1.0, "L2"): bo.S_AMBIGUOUS,
                                   (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_STRONG})
    assert bo.classify_terminal(strong_l2) == bo.T_L2_DEPENDS
    both_same_f = dict(base, strata={(1.0, "L1"): bo.S_STRONG, (1.0, "L2"): bo.S_STRONG,
                                     (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_AMBIGUOUS})
    assert bo.classify_terminal(both_same_f) == bo.T_BIDIRECTIONAL
    # Strong L1 in one f and strong L2 in the other is not bidirectional.
    cross_f = dict(base, strata={(1.0, "L1"): bo.S_STRONG, (1.0, "L2"): bo.S_AMBIGUOUS,
                                 (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_STRONG})
    assert bo.classify_terminal(cross_f) == bo.T_MIXED
    marginal = dict(base, strata={(1.0, "L1"): bo.S_MARGINAL, (1.0, "L2"): bo.S_AMBIGUOUS,
                                  (1.2, "L1"): bo.S_AMBIGUOUS, (1.2, "L2"): bo.S_AMBIGUOUS})
    assert bo.classify_terminal(marginal) == bo.T_MARGINAL_REGION
    no_recovery = {(1.0, "L1"): bo.S_NO_RECOVERY, (1.0, "L2"): bo.S_NO_RECOVERY,
                   (1.2, "L1"): bo.S_NO_RECOVERY, (1.2, "L2"): bo.S_NO_RECOVERY}
    assert bo.classify_terminal(dict(base, strata=no_recovery)) == bo.T_NO_RECOVERY
    assert list(bo.TERMINALS) == [
        "D7_C_PRE_EXECUTION_BLOCKED", "D7_C_WATCHDOG_TIMEOUT_VOID",
        "D7_C_NONFINITE_OR_CRASH_BLOCKED", "D7_C_RESOURCE_OVERRUN",
        "D7_C_INCOMPLETE_CALL_MATRIX", "D7_C_BIDIRECTIONAL_DEPENDENCE",
        "D7_C_L1_DEPENDS_ON_U2", "D7_C_L2_DEPENDS_ON_U1",
        "D7_C_MARGINAL_REGION_EXISTS", "D7_C_ORACLE_NO_USEFUL_RECOVERY",
        "D7_C_MIXED_DIAGNOSTIC"]

    # Run-path stratum terminals (the full fixture above yields T6).
    def layer_selective(active_layer):
        def decode(h, prior, syndrome):
            p = np.asarray(prior, dtype=np.float64)
            layer = "L1" if np.asarray(h).shape[0] in (49, 59) else "L2"
            x = (np.argmax(p, axis=1).astype(np.int64) if layer == active_layer
                 else np.zeros(p.shape[0], dtype=np.int64))
            return {"x_hat": x, "syndrome_ok": True, "iterations": 1,
                    "final_beliefs": np.log(p + 1e-300), "status": "fake_layer"}

        return decode

    result = _full_run(tmp_path, decoder=layer_selective("L1"),
                       out_name=tmp_path / "term_l1")
    assert result["terminal"] == bo.T_L1_DEPENDS
    result = _full_run(tmp_path, decoder=layer_selective("L2"),
                       out_name=tmp_path / "term_l2")
    assert result["terminal"] == bo.T_L2_DEPENDS

    def always_zeros(h, prior, syndrome):
        p = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.zeros(p.shape[0], dtype=np.int64), "syndrome_ok": True,
                "iterations": 1, "final_beliefs": np.log(p + 1e-300),
                "status": "fake_zeros"}

    result = _full_run(tmp_path, decoder=always_zeros, out_name=tmp_path / "term_none")
    assert result["terminal"] == bo.T_NO_RECOVERY

    def delta_joint():
        joint = np.zeros((bo.Q, bo.Q, bo.BOB_DIM))
        for b in range(bo.BOB_DIM):
            joint[b % 31 + 1, (b // 31) % 31 + 1, b] = 1.0
        return joint

    def delta_sampler(p_b, p_f, n, seed):
        bob = ((np.arange(bo.N) * 13 + int(seed)) % bo.BOB_DIM).astype(np.int64)
        u1 = bob % 31 + 1
        u2 = (bob // 31) % 31 + 1
        return {"bob": bob, "u1": u1, "u2": u2}

    result = _full_run(tmp_path, joint=delta_joint(), sampler=delta_sampler,
                       out_name=tmp_path / "term_marginal")
    assert result["terminal"] == bo.T_MARGINAL_REGION


def test_c11_128_call_cap_and_no_retry(tmp_path):
    calls = []

    def counting_decoder(h, prior, syndrome):
        calls.append(1)
        return _argmax_decoder()(h, prior, syndrome)

    result = _full_run(tmp_path, decoder=counting_decoder, out_name=tmp_path / "c11")
    assert len(calls) == 128
    assert result["records"] == 128
    assert result["terminal"] == bo.T_BIDIRECTIONAL
    assert bo.MAX_CALLS == 128 and len(bo.frozen_identities()) == 128

    counter = {"n": 0}

    def crash_at_40(h, prior, syndrome):
        counter["n"] += 1
        if counter["n"] == 40:
            raise RuntimeError("boom")
        return _argmax_decoder()(h, prior, syndrome)

    result = _full_run(tmp_path, decoder=crash_at_40, out_name=tmp_path / "c11b")
    assert counter["n"] == 40  # no retry, no replacement
    assert result["records"] == 40 and result["terminal"] == bo.T_CRASH
    records = _read_csv(tmp_path / "c11b" / "decoder_records.csv")
    assert [int(r["call_idx"]) for r in records] == list(range(1, 41))
    assert records[-1]["status"].startswith("crash:")


def test_c12_budget_boundaries(tmp_path):
    assert bo.PER_CALL_WATCHDOG_S == 120.0
    assert bo.STORED_WALL_LIMIT_S == 1500.0
    assert bo.OUTER_WATCHDOG_S == 1800.0 and bo.OUTER_GRACE_S == 30.0
    assert bo.RSS_LIMIT_BYTES == 2 * 1024**3

    walls = [120.0] + [0.0] * 127
    result = _full_run(tmp_path, clock=_ScriptedClock(walls), out_name=tmp_path / "w120")
    assert result["terminal"] == bo.T_BIDIRECTIONAL and result["records"] == 128

    walls = [120.0001] + [0.0] * 127
    result = _full_run(tmp_path, clock=_ScriptedClock(walls), out_name=tmp_path / "w121")
    assert result["terminal"] == bo.T_WATCHDOG and result["records"] == 1

    walls = [12.0] * 125 + [0.0] * 3
    result = _full_run(tmp_path, clock=_ScriptedClock(walls), out_name=tmp_path / "wall1500")
    assert result["terminal"] == bo.T_BIDIRECTIONAL and result["records"] == 128
    summary = json.loads((tmp_path / "wall1500" / "summary.json").read_text(encoding="utf-8"))
    assert abs(float(summary["stored_wall_s"]) - 1500.0) <= 1e-9

    walls = [12.0] * 125 + [0.001] + [0.0] * 2
    result = _full_run(tmp_path, clock=_ScriptedClock(walls), out_name=tmp_path / "wall1501")
    assert result["terminal"] == bo.T_RESOURCE and result["records"] == 126

    result = _full_run(tmp_path, rss_probe=lambda: bo.RSS_LIMIT_BYTES,
                       out_name=tmp_path / "rss2g")
    assert result["terminal"] == bo.T_RESOURCE and result["records"] == 1


# --------------------------------------------------------------------------
# C13-C16: RSS units/preflight, provenance labels, schema, verifier tampering
# --------------------------------------------------------------------------

def test_c13_wsl_rss_kib_to_bytes_and_fail_before_first_call(tmp_path, monkeypatch):
    monkeypatch.setattr(bo, "_read_ru_maxrss", lambda: 123456)
    assert bo.get_rss_bytes() == 123456 * 1024
    monkeypatch.setattr(bo, "_read_ru_maxrss", lambda: None)
    assert bo.get_rss_bytes() is None
    monkeypatch.setattr(bo, "_read_ru_maxrss", lambda: float("nan"))
    assert bo.get_rss_bytes() is None
    monkeypatch.setattr(bo, "_read_ru_maxrss", lambda: -1)
    assert bo.get_rss_bytes() == -1024  # negative value is rejected by preflight
    monkeypatch.undo()
    live = bo.get_rss_bytes()
    assert live is not None and live > 0
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "psutil" not in source and "import resource" in source

    for index, probe in enumerate((lambda: None, lambda: 0, lambda: -5,
                                   lambda: float("nan"), lambda: float("inf"))):
        events = []
        out = tmp_path / ("c13_%d" % index)

        def decoder(h, prior, syndrome):
            events.append("decode")
            return _argmax_decoder()(h, prior, syndrome)

        def sampler(p_b, p_f, n, seed):
            events.append("sample")
            return _perfect_oracle_block(seed)

        def model_f_loader(root):
            events.append("model_f")
            raise AssertionError("Model-F loader must not run")

        with pytest.raises(bo.PreflightBlocked) as excinfo:
            bo.run_bidirectional_oracle(
                out_root=out, joint=_perfect_oracle_joint(),
                block_sampler=sampler, mothers=None, decode_fn=decoder,
                model_f_loader=model_f_loader,
                state={"d7c_execution_authorized": True}, rss_probe=probe,
                repo_root=REPO)
        assert bo.T_PRE_EXEC in str(excinfo.value)
        assert events == []
        assert not out.exists()


def test_c14_current_belief_labels_never_posterior_or_app(tmp_path):
    assert bo.CURRENT_BELIEF_LABELS == ("PRIOR_ONLY_CURRENT_BELIEF",
                                        "CHECK_UPDATED_CURRENT_BELIEF")
    for iterations, expected_label, conditioned in (
            (0, bo.PRIOR_ONLY_CURRENT_BELIEF, False),
            (3, bo.CHECK_UPDATED_CURRENT_BELIEF, True)):
        out = tmp_path / ("c14_%d" % iterations)
        _full_run(tmp_path, decoder=_argmax_decoder(iterations=iterations), out_name=out)
        records = _read_csv(out / "decoder_records.csv")
        assert len(records) == 128
        for record in records:
            assert record["current_belief_label"] == expected_label
            assert str(record["beliefs_conditioned"]) == str(conditioned)
            assert "posterior" not in record["current_belief_label"].lower()
            assert "app" not in record["current_belief_label"].lower()
            assert record["belief_max_prob"] not in ("", "nan")
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "PRIOR_ONLY_CURRENT_BELIEF" in source
    assert "CHECK_UPDATED_CURRENT_BELIEF" in source
    assert "final_beliefs" in source  # read only; never fed to another layer
    assert "warm_beliefs" not in source


def test_c15_six_file_scalar_schema_no_subdirs_no_overwrite(tmp_path):
    out = tmp_path / "c15"
    _full_run(tmp_path, out_name=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(bo.SIX_FILES)
    assert not any(p.is_dir() for p in out.iterdir())
    with open(out / "decoder_records.csv", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == bo.RECORD_FIELDS
        records = list(reader)
    with open(out / "paired_summary.csv", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == bo.PAIRED_FIELDS
        paired = list(reader)
    assert len(records) == 128 and len(paired) == 4
    for record in records:
        for value in record.values():
            assert not value.startswith("[") and not value.startswith("{")
    json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert (out / "report.md").read_text(encoding="utf-8").strip()
    assert (out / "command_log.txt").read_text(encoding="utf-8").strip()

    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        bo.write_root(populated, {}, [], [], {})
    empty_existing = tmp_path / "empty_existing"
    empty_existing.mkdir()
    with pytest.raises(FileExistsError):
        bo.write_root(empty_existing, {}, [], [], {})
    subdir = tmp_path / "subdir"
    (subdir / "nested").mkdir(parents=True)
    with pytest.raises(ValueError):
        bo.write_root(subdir, {}, [], [], {})

    complete = {key: "" for key in bo.RECORD_FIELDS}
    complete.update({"call_idx": 1, "f": 1.0, "seed": 2026091300,
                     "condition": "L1_MARGINAL", "layer": "L1", "rows": 49, "n": 64})
    bad_extra = dict(complete, u1_true_vector=[1, 2, 3])
    with pytest.raises(ValueError):
        bo.write_root(tmp_path / "bad_extra", {}, [bad_extra], [], {})
    bad_array = dict(complete, wall_s=np.zeros(3))
    with pytest.raises(ValueError):
        bo.write_root(tmp_path / "bad_array", {}, [bad_array], [], {})

    existing = tmp_path / "existing"
    existing.mkdir()
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_decoder()(h, prior, syndrome)

    with pytest.raises(FileExistsError):
        bo.run_bidirectional_oracle(
            out_root=existing, joint=_perfect_oracle_joint(),
            block_sampler=_sampler(), decode_fn=decoder,
            state={"d7c_execution_authorized": True}, repo_root=REPO)
    assert events == []


def _copy_root(source: Path, destination: Path) -> Path:
    shutil.copytree(str(source), str(destination))
    return destination


def test_c16_verifier_detects_duplicate_missing_unpaired_and_tampered(tmp_path):
    good = tmp_path / "c16_good"
    _full_run(tmp_path, out_name=good)
    report = bo.verify_root(good)
    assert report["ok"] and report["records"] == 128, report

    record_lines = (good / "decoder_records.csv").read_text(encoding="utf-8").splitlines()
    paired_lines = (good / "paired_summary.csv").read_text(encoding="utf-8").splitlines()

    # duplicate
    root = _copy_root(good, tmp_path / "t_dup")
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines + [record_lines[1]]) + "\n", encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # missing / unpaired middle record (identity shift breaks pairing/order)
    root = _copy_root(good, tmp_path / "t_missing")
    kept = [line for line in record_lines if not line.startswith("63,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # tampered scalar (exact flag contradicts symbol_errors and pair counts)
    root = _copy_root(good, tmp_path / "t_scalar")
    tampered = []
    for line in record_lines:
        if line.startswith("62,"):  # f=1.2 L1_ORACLE_U2 is exact=True
            line = line.replace("True", "False", 1)
        tampered.append(line)
    (root / "decoder_records.csv").write_text("\n".join(tampered) + "\n", encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # tampered syndrome flag only
    root = _copy_root(good, tmp_path / "t_syndrome")
    rows = _read_csv(root / "decoder_records.csv")
    for row in rows:
        if row["call_idx"] == "61":  # marginal call: syndrome_ok is False
            row["syndrome_ok"] = "True"
    with open(root / "decoder_records.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=bo.RECORD_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    assert bo.verify_root(root)["ok"] is False
    # tampered paired count
    root = _copy_root(good, tmp_path / "t_paired")
    lines = list(paired_lines)
    fields = lines[1].split(",")
    fields[4] = str(int(fields[4]) + 1)
    lines[1] = ",".join(fields)
    (root / "paired_summary.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # tampered terminal
    root = _copy_root(good, tmp_path / "t_terminal")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["terminal"] = bo.T_MIXED
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # tampered manifest constant
    root = _copy_root(good, tmp_path / "t_manifest")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["lambda_star"] = 1.0
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False
    # extra seventh file
    root = _copy_root(good, tmp_path / "t_extra")
    (root / "extra.txt").write_text("x", encoding="utf-8")
    assert bo.verify_root(root)["ok"] is False


# --------------------------------------------------------------------------
# C17-C18: launch isolation and external-cwd sentinel
# --------------------------------------------------------------------------

def _run_cli(args, cwd, env=None):
    return subprocess.run([sys.executable] + args, cwd=str(cwd), env=_clean_env(env),
                          capture_output=True, text=True, timeout=SUB_TIMEOUT)


def test_c17_lazy_import_help_dry_run_and_unauthorized_isolation(tmp_path):
    assert bo._EXECUTION_CONSUMED is False
    assert "v35_algorithm_development" not in sys.modules
    external = tmp_path / "ext"
    external.mkdir()
    assert _run_cli([str(RUNNER), "--help"], cwd=REPO).returncode == 0
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-C" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("calls=128") and len(lines) == 129
    assert lines[1].split()[1] == "L1_MARGINAL"
    assert lines[128].split()[1] == "L2_ORACLE_U1"
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7c_c17')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "print('C17_OK')\n")
    result = subprocess.run([sys.executable, "-c", probe, str(RUNNER)],
                            cwd=str(external), env=_clean_env(),
                            capture_output=True, text=True, timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "C17_OK" in result.stdout

    with pytest.raises(ValueError):
        bo.validate_production_out_root(tmp_path / "outside", repo_root=REPO)
    with pytest.raises(ValueError):
        bo.validate_production_out_root(WS / "wrong_name", repo_root=REPO)
    assert bo.validate_production_out_root(
        WS / (bo.OUT_ROOT_PREFIX + "abc"), repo_root=REPO).name.endswith("abc")

    target = WS / (bo.OUT_ROOT_PREFIX + "unauthorized_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", bo.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3
    assert "not authorized" in result.stdout
    assert not target.exists()
    bad_shape = tmp_path / "bad_shape"
    result = _run_cli([str(RUNNER), "--model-f-root", bo.MODEL_F_ROOT,
                       "--out-root", str(bad_shape)], cwd=REPO)
    assert result.returncode == 3 and "refused" in result.stdout
    assert not bad_shape.exists()


def test_c18_external_cwd_sentinel_reaches_first_decoder_call(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    out_root = tmp_path / "c18_never_created"
    code = r'''
import runpy
import pathlib
import sys

import numpy as np

g = runpy.run_path(sys.argv[1], run_name="d7c_c18")
mod = g["_mod"]
out_root = pathlib.Path(sys.argv[2])
repo = pathlib.Path(sys.argv[3])

events = {"loader": 0, "sample": [], "decode": []}


class Sentinel(BaseException):
    pass


def loader(root):
    events["loader"] += 1
    raise AssertionError("real Model-F loader must never be called")


base = np.full((32, 32), 1.0 / 32.0)
for u2 in range(32):
    base[(u2 + 1) % 32, u2] += 1.0 / 64.0
    base[u2, u2] -= 1.0 / 64.0
joint = np.repeat((base / 32.0)[:, :, None], 1024, axis=2)


def sampler(p_b, p_f, n, seed):
    events["sample"].append(int(seed))
    bob = ((np.arange(64) * 13 + int(seed)) % 1024).astype(np.int64)
    u2 = (bob % 30) + 1
    return {"bob": bob, "u1": u2 + 1, "u2": u2}


def sentinel_decoder(h, prior, syn):
    events["decode"].append(1)
    raise Sentinel("reached first decoder call")


try:
    mod.run_bidirectional_oracle(
        out_root=out_root, joint=joint, block_sampler=sampler,
        decode_fn=sentinel_decoder, model_f_loader=loader,
        state={"d7c_execution_authorized": True}, repo_root=repo)
except Sentinel:
    pass
else:
    raise AssertionError("sentinel must have been reached")

assert events["loader"] == 0, events
assert len(events["decode"]) == 1, events
assert events["sample"] == list(range(2026091300, 2026091316)), events["sample"]
assert not out_root.exists(), "no root may be created during the call phase"
print("C18_OK")
'''
    result = subprocess.run(
        [sys.executable, "-c", code, str(RUNNER), str(out_root), str(REPO)],
        cwd=str(external), env=_clean_env(), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "C18_OK" in result.stdout


# --------------------------------------------------------------------------
# C19-C20: protected-root lifecycle, related regression, compile
# --------------------------------------------------------------------------

def test_c19_protected_root_lifecycle_and_g2_r1d_absence(tmp_path):
    workspace_before = sorted(p.name for p in WS.iterdir())
    model_f_before = _dir_meta(MODEL_F_ROOT)
    _full_run(tmp_path, out_name=tmp_path / "c19")
    workspace_after = sorted(p.name for p in WS.iterdir())
    assert workspace_after == workspace_before
    assert list(WS.glob(bo.OUT_ROOT_PREFIX + "*")) == []
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert not (WS / "v72p2d5_g2" / "20260906_r1").exists()
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert list(WS.glob("d7_c_bidirectional_oracle_*")) == []
    state = bo.read_cycle_state(CYCLE_STATE)
    for key in ("d7c_execution_authorized", "decoder_executed", "result_created",
                "formal_execution_authorized", "synthetic_execution_authorized",
                "real_execution_authorized", "g1_authorized", "g2_authorized"):
        assert state.get(key) is False, (key, state.get(key))
    assert str(state.get("r1d_state", "")).startswith("R1D_PAUSED")
    assert "workspace/v72p2d5_model_f_input/20260907_r1" in bo.PROTECTED_ROOTS


def test_c20_related_regression_and_py_compile(tmp_path):
    for target in (CORE_PATH, TEST_FILE, RUNNER):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(target)],
            cwd=str(REPO), capture_output=True, text=True, timeout=SUB_TIMEOUT)
        assert result.returncode == 0, result.stderr
    base = tmp_path / "inner"
    base.mkdir()

    def related(files, expected, extra=()):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider",
             "--basetemp", str(base), *extra],
            cwd=str(REPO), env=dict(os.environ), capture_output=True, text=True,
            timeout=SUB_TIMEOUT)
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected in result.stdout, result.stdout

    related([str(D7A_FILE)], "14 passed")
    related([str(D5_FILE)], "165 passed")
    # The two excluded D7-B launch tests assert that no D7-B R2 root exists;
    # the frozen D7-B R2 root c605d1e6 is part of the accepted baseline now.
    related([str(D7B_FILE), "-k",
             "not test_launch_l04_dry_run_both_cwds_no_bind_no_root and "
             "not test_launch_l12_roots_and_authorization_unchanged"],
            "29 passed")
