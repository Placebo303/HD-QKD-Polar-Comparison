"""Stage-1 layout tests S-T01..S-T05 (fake-only, T0/T1).

No production decoder import, no scientific call, no root creation, no
real-data contact. S-T04 is PROFILE_ONLY graph construction (no decoder);
any admission FAIL stops with no seed change.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.formal_ir.nbldpc_l1_degree2_layout as layout  # noqa: E402
import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402


# --------------------------------------------------------------------------- #
# tiny independent oracle (peasant GF32/poly-37 arithmetic, own code path)
# --------------------------------------------------------------------------- #
def _raw_mul(a: int, b: int) -> int:
    r, aa, bb = 0, int(a), int(b)
    while bb:
        if bb & 1:
            r ^= aa
        bb >>= 1
        aa <<= 1
        if aa & 0x20:
            aa ^= 0x25
    return r & 0x1F


def _raw_syndrome(dense, word) -> list[int]:
    h = np.asarray(dense, dtype=np.int64)
    x = np.asarray(word, dtype=np.int64).ravel()
    out = []
    for row in range(h.shape[0]):
        acc = 0
        for col in np.flatnonzero(h[row]):
            acc ^= _raw_mul(int(h[row, col]), int(x[col]))
        out.append(int(acc))
    return out


# --------------------------------------------------------------------------- #
# S-T01: GF32 add/mul/syndrome vs tiny oracle, full equality
# --------------------------------------------------------------------------- #
def test_st01_gf32_matches_tiny_oracle():
    for a in range(32):
        for b in range(32):
            assert layout.gf32_add(a, b) == (a ^ b)
            assert layout.gf32_mul(a, b) == _raw_mul(a, b)
    rng = np.random.default_rng(2026094000)
    for _ in range(8):
        m, n = int(rng.integers(1, 5)), int(rng.integers(1, 7))
        h = rng.integers(0, 32, size=(m, n))
        x = rng.integers(0, 32, size=n)
        assert layout.gf32_syndrome(h, x) == _raw_syndrome(h, x)
        assert layout.syndrome_ok(h, x, _raw_syndrome(h, x)) is True
        wrong = [(v + 1) % 32 for v in _raw_syndrome(h, x)]
        if wrong != _raw_syndrome(h, x):
            assert layout.syndrome_ok(h, x, wrong) is False


# --------------------------------------------------------------------------- #
# S-T02: symbol-mapping roundtrip
# --------------------------------------------------------------------------- #
def test_st02_symbol_mapping_roundtrip():
    for a in range(1024):
        u1, u2 = layout.symbols_to_layers(np.array([a]))
        assert int(layout.layers_to_symbols(u1, u2)[0]) == a
    rng = np.random.default_rng(2026093700)
    vec = rng.integers(0, 1024, size=64)
    u1, u2 = layout.symbols_to_layers(vec)
    assert np.array_equal(layout.layers_to_symbols(u1, u2), vec)
    assert bool(np.all(u1 < 32)) and bool(np.all(u2 < 32))
    with pytest.raises(ValueError):
        layout.layers_to_symbols(np.array([0, 32]), np.array([0, 0]))
    with pytest.raises(ValueError):
        layout.symbols_to_layers(np.array([-1]))


# --------------------------------------------------------------------------- #
# S-T03: S/C vs L055 table, item by item (both widths)
# --------------------------------------------------------------------------- #
def _histograms(edges):
    var_c = Counter(int(v) for v, _ in edges)
    chk_c = Counter(int(c) for _, c in edges)
    var_hist = Counter(var_c.values())
    chk_hist = Counter(chk_c.values())
    return dict(var_hist), dict(chk_hist)


@pytest.mark.parametrize("width", [128, 256])
def test_st03_construction_matches_l055_table(width):
    cell = layout.l055_degree_cell(width)
    expect_var = {2: cell["var_counts"][2], 3: cell["var_counts"][3]}
    expect_chk = dict(cell["check_counts"])
    builders = {
        "control": r2.build_degree_sequence_peg,
        "candidate": layout.build_d2_directed_peg,
    }
    seed = layout.GRAPH_SEEDS[width][0]
    for name, fn in builders.items():
        out = fn(cell["n"], cell["m"], cell["var_counts"],
                 cell["check_counts"], seed)
        assert out["status"] == "ok", (name, out["failure_reason"])
        assert out["n"] == width and out["m"] == cell["m"]
        assert len(out["edges"]) == cell["E"]
        var_hist, chk_hist = _histograms(out["edges"])
        assert var_hist == expect_var, name
        assert chk_hist == expect_chk, name
        assert out["edges"] == sorted(out["edges"])
    # syndrome payload identity: 5 bits per GF32 row
    disc = layout.disclosure_bits(cell["m"], cell["m"])
    assert disc["l1_syn_bits"] == 5 * cell["m"]
    assert disc["l2_syn_bits"] == 5 * cell["m"]
    if width == 128:
        assert (cell["n"], cell["m"], cell["E"]) == (128, 118, 301)
        assert expect_var == {2: 83, 3: 45} and expect_chk == {2: 53, 3: 65}
    else:
        assert (cell["n"], cell["m"], cell["E"]) == (256, 236, 602)
        assert expect_var == {2: 166, 3: 90} \
            and expect_chk == {2: 106, 3: 130}


def test_st03_determinism_same_seed_same_edges_and_coeffs():
    for width in (128, 256):
        cell = layout.l055_degree_cell(width)
        seed = layout.GRAPH_SEEDS[width][1]
        first = layout.build_d2_directed_peg(
            cell["n"], cell["m"], cell["var_counts"],
            cell["check_counts"], seed)
        second = layout.build_d2_directed_peg(
            cell["n"], cell["m"], cell["var_counts"],
            cell["check_counts"], seed)
        assert first["edges"] == second["edges"]
        c1 = layout.coefficients_for_edges(first["edges"], width, seed)
        c2 = layout.coefficients_for_edges(second["edges"], width, seed)
        assert c1 == c2 and all(1 <= v <= 31 for v in c1)


# --------------------------------------------------------------------------- #
# S-T04: A1-A6 admission, both arms x frozen seeds, PROFILE_ONLY (no decoder)
# --------------------------------------------------------------------------- #
ADMISSION_KEYS = (
    "A1_exact_degrees_socket_balance",
    "A2_simple_graph_min_degree",
    "A3_single_component",
    "A4_structural_rank_m",
    "A5_gf32_rank_m",
    "A6_deterministic_replay",
)


def test_st04_admission_all_pass_profile_only():
    profile = layout.profile_graphs()
    assert profile["decoder_calls"] == 0
    assert profile["replacement_seeds_used"] == 0
    assert profile["seed_replacements"] == []
    assert len(profile["graphs"]) == 24  # 2 arms x 2 widths x 6 seeds
    # STOP with no seed change on any failure: hard assert, no fallback.
    assert profile["frozen_seed_failures"] == [], \
        "admission STOP: %r" % (profile["frozen_seed_failures"],)
    for entry in profile["graphs"]:
        assert entry["status"] == "ok" and entry["admitted"] is True
        assert set(entry["admission"]) == set(ADMISSION_KEYS)
        assert all(entry["admission"].values())


# --------------------------------------------------------------------------- #
# S-T05: noiseless small example — U1/U2/pair/syndrome/verify separation
# --------------------------------------------------------------------------- #
def _tiny_matrices():
    h = np.array([[1, 2, 0],
                  [0, 3, 1]], dtype=np.int64)
    return h.copy(), h.copy()


def test_st05_noiseless_semantics_and_separation():
    h1, h2 = _tiny_matrices()
    u1 = np.array([5, 7, 9], dtype=np.int64)
    u2 = np.array([1, 2, 3], dtype=np.int64)
    syn1 = layout.gf32_syndrome(h1, u1)
    syn2 = layout.gf32_syndrome(h2, u2)
    assert syn1 == _raw_syndrome(h1, u1) and syn2 == _raw_syndrome(h2, u2)
    assert layout.syndrome_ok(h1, u1, syn1)
    assert not layout.syndrome_ok(h1, (u1 + 1) % 32, syn1)
    disc = layout.disclosure_bits(2, 2, verify_tag_bits=64)
    ok = layout.classify_frame(u1_exact=True, u2_exact=True, syn_l1=True,
                               syn_l2=True, verify_accept=True, status="ok",
                               disclosure=disc)
    assert ok["pair_exact"] is True and ok["syn_joint"] is True
    assert ok["accepted_wrong"] is False and layout.is_success(ok) is True
    assert set(ok) == set(layout.RESULT_SCHEMA_COLUMNS)
    # separation: syndrome agreement without exact recovery is not success
    syn_only = layout.classify_frame(u1_exact=False, u2_exact=True,
                                     syn_l1=True, syn_l2=True,
                                     verify_accept=False, status="ok",
                                     disclosure=disc)
    assert syn_only["pair_exact"] is False
    assert layout.is_success(syn_only) is False
    # undetected isolation: verify accept on a wrong pair is not success
    und = layout.classify_frame(u1_exact=False, u2_exact=False, syn_l1=True,
                                syn_l2=True, verify_accept=True,
                                status="ok", disclosure=disc)
    assert und["accepted_wrong"] is True
    assert layout.is_success(und) is False
