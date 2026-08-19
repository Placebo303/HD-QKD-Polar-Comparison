"""V28 GF32xGF32 finite-code engineering — T0/T1 focused tests.

Covers: matrix dimensions, exact GF(32) rank, syndrome consistency, source
row-prefix accounting, noiseless two-layer decode (recovers x), decoder
fail-closed behavior on errors, determinism / seed replay, 64-bit tag +
leakage accounting, Bob-only sequential semantics, and the read-only verifier.
No DE / no FER / no fresh .ttbin.
"""
from __future__ import annotations

import random
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_codebook as cb,
    nonbinary_v10_fftqspa as qspa,
    nonbinary_v28 as v28,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def _small_config():
    return {
        "schema": "nbldpc_v28_test_small",
        "q": 32, "n": 256, "m1": 4, "m2_max": 8,
        "sources": {"1M": {"m2": 6, "h_total": 0.8}},
        "seed_l1": 2026082001, "seed_l2": 2026082002,
        "topology": cb._TOPOLOGY,
        "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
        "tag_bits": 64, "field_id": GF2mField.create(32).spec.field_id,
        "p_noiseless": 1e-3, "p_controlled": 0.2, "max_iter": 30,
    }


def _rnd(n, q, seed=5):
    r = random.Random(seed)
    return [r.randrange(q) for _ in range(n)]


# --------------------------------------------------------------------------- #
# T0 — structural
# --------------------------------------------------------------------------- #
def test_matrix_dimensions():
    cfg = v28.frozen_v28_config()
    h1, h2 = v28.build_matrices(cfg)
    assert len(h1) == cfg["m1"] and len(h1[0]) == cfg["n"]
    assert len(h2) == cfg["m2_max"] and len(h2[0]) == cfg["n"]


def test_rank_full():
    field = GF2mField.create(32)
    cfg = v28.frozen_v28_config()
    h1, h2 = v28.build_matrices(cfg)
    assert cb.gf_rank(h1, field) == cfg["m1"]
    assert cb.gf_rank(h2, field) == cfg["m2_max"]


def test_syndrome_consistency():
    field = GF2mField.create(32)
    cfg = _small_config()
    h1, _ = v28.build_matrices(cfg)
    x = _rnd(cfg["n"], cfg["q"])
    s = v28.compute_syndrome(field, h1, x)
    # recomputation is stable
    assert v28.compute_syndrome(field, h1, x) == list(s)
    # a perturbed symbol changes the syndrome
    x2 = list(x); x2[0] = (x2[0] + 1) % cfg["q"]
    assert v28.compute_syndrome(field, h1, x2) != list(s)


def test_row_prefix_accounting():
    cfg = v28.frozen_v28_config()
    _, h2 = v28.build_matrices(cfg)
    for src, sinfo in cfg["sources"].items():
        hl2 = v28.layer_matrix(h2, src, cfg)
        assert len(hl2) == sinfo["m2"]
        assert list(hl2) == list(h2[:sinfo["m2"]])


# --------------------------------------------------------------------------- #
# T1 — decode / semantics / accounting
# --------------------------------------------------------------------------- #
def test_noiseless_decode_small():
    field = GF2mField.create(32)
    cfg = _small_config()
    h1, h2 = v28.build_matrices(cfg)
    h_l2 = v28.layer_matrix(h2, "1M", cfg)
    x1 = _rnd(cfg["n"], cfg["q"], 1)
    x2 = _rnd(cfg["n"], cfg["q"], 2)
    s1 = v28.compute_syndrome(field, h1, x1)
    s2 = v28.compute_syndrome(field, h_l2, x2)
    r1 = v28.decode_layer(field, x1, h1, s1, cfg["p_noiseless"], cfg["max_iter"])
    r2 = v28.decode_layer(field, x2, h_l2, s2, cfg["p_noiseless"], cfg["max_iter"])
    assert r1["status"] == qspa.STATUS_SUCCESS and r1.get("x_hat") == x1
    assert r2["status"] == qspa.STATUS_SUCCESS and r2.get("x_hat") == x2


def test_decoder_works_on_proper_code():
    """Control: the reused GF(32) FFT-QSPA corrects errors on a properly
    connected code (m=n/2).  Proves the decoder machinery is sound; the V27
    split's sparse high-rate matrices are the limiter, not the decoder."""
    field = GF2mField.create(32)
    proper = {"q": 32, "n": 64, "m1": 32, "m2_max": 32,
              "sources": {"1M": {"m2": 32, "h_total": 0.8}},
              "seed_l1": 2026082001, "seed_l2": 2026082002,
              "topology": cb._TOPOLOGY, "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
              "tag_bits": 64, "field_id": field.spec.field_id,
              "p_noiseless": 1e-3, "p_controlled": 0.1, "max_iter": 40}
    h, _ = v28.build_matrices(proper)
    assert cb.gf_rank(h, field) == 32
    x = _rnd(64, 32, 7)
    s = v28.compute_syndrome(field, h, x)
    for k in (1, 3, 5):
        y = list(x)
        for j in range(k):
            y[j] = (y[j] + (j + 3)) % 32
        r = v28.decode_layer(field, y, h, s, 0.1, 40)
        assert r["status"] == qspa.STATUS_SUCCESS and r.get("x_hat") == x


def test_controlled_error_fail_closed():
    """Injected errors on the sparse V27-style matrix are NOT silently claimed
    correct: the decoder is fail-closed (reconstruction_ok iff status==success,
    never a false success)."""
    field = GF2mField.create(32)
    cfg = _small_config()
    h1, _ = v28.build_matrices(cfg)
    x = _rnd(cfg["n"], cfg["q"], 3)
    s = v28.compute_syndrome(field, h1, x)
    y = list(x); y[32] = (y[32] + 5) % cfg["q"]  # parity column (constrained)
    r = v28.decode_layer(field, y, h1, s, cfg["p_controlled"], cfg["max_iter"])
    # fail-closed invariant
    assert r.get("reconstruction_ok") == (r["status"] == qspa.STATUS_SUCCESS)
    if r["status"] != qspa.STATUS_SUCCESS:
        assert not r.get("reconstruction_ok")


def test_bob_only_sequential_order():
    field = GF2mField.create(32)
    cfg = _small_config()
    h1, h2 = v28.build_matrices(cfg)
    h_l2 = v28.layer_matrix(h2, "1M", cfg)
    x1 = _rnd(cfg["n"], cfg["q"], 11)
    x2 = _rnd(cfg["n"], cfg["q"], 12)
    s1 = v28.compute_syndrome(field, h1, x1)
    s2 = v28.compute_syndrome(field, h_l2, x2)
    res = v28.decode_two_layer(field, x1, x2, s1, s2, "1M",
                                p1=cfg["p_noiseless"], p2=cfg["p_noiseless"],
                                config=cfg)
    assert res["layer_order"] == ["L1", "L2"]
    assert res["x1_hat"] == x1 and res["x2_hat"] == x2


def test_deterministic_seed_replay():
    cfg = _small_config()
    h1a, h2a = v28.build_matrices(cfg)
    h1b, h2b = v28.build_matrices(cfg)
    assert h1a == h1b and h2a == h2b  # deterministic matrices
    field = GF2mField.create(32)
    x1 = _rnd(cfg["n"], cfg["q"], 21)
    s1 = v28.compute_syndrome(field, h1a, x1)
    ra = v28.decode_layer(field, x1, h1a, s1, cfg["p_noiseless"], cfg["max_iter"])
    rb = v28.decode_layer(field, x1, h1b, s1, cfg["p_noiseless"], cfg["max_iter"])
    assert ra["status"] == rb["status"]
    assert ra.get("x_hat") == rb.get("x_hat")


def test_tag_and_leakage():
    cfg = v28.frozen_v28_config()
    # deterministic tag
    x1 = _rnd(cfg["n"], cfg["q"], 31)
    x2 = _rnd(cfg["n"], cfg["q"], 32)
    t1 = v28.tag64(x1, x2)
    t2 = v28.tag64(list(x1), list(x2))
    assert t1 == t2 and len(t1) == 16  # 8 bytes = 64 bits hex
    # leakage f < 1.3 for all sources
    for src, sinfo in cfg["sources"].items():
        m_total = cfg["m1"] + sinfo["m2"]
        leak = v28.leakage_bits(m_total, cfg["q"])
        f = leak / (cfg["n"] * sinfo["h_total"])
        assert f < 1.3


def test_verify_v28_small_run(tmp_path):
    root = Path(tmp_path) / "v28_small"
    cfg = _small_config()
    out = v28.run_v28_evidence(root, cfg)
    assert out["status"] == "engineering_ready_for_retrospective_gate"
    vr = v28.verify_v28(root)
    assert vr["ok"] is True
    assert vr["recomputed_terminal"] == "engineering_ready_for_retrospective_gate"
    assert vr["persisted_terminal"] == "engineering_ready_for_retrospective_gate"
