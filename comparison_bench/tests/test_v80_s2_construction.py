"""V80 S2 construction tests (EXPLORE, fake/small, deterministic seeds).

Frozen spec: S2_ENTRY_PACKET_20260920.md (G-S2ENTRY) + S2_ACCOUNTING_MAP +
PROGRAM_PLAN §1.3/S2. Construction + single-frame smoke decode ONLY
(<=5 blocks, wall <=600 s for ALL tests in this file); NO FER campaign.

Group-rule math note (packet §2, rule (a)): four independent n=256 frames,
whole-group accept/discard — any-frame-fail ⇒ group fail. Superframe
FER<=5% therefore needs per-frame FER <= 1-(1-0.05)^(1/4) = 1.274%
(never reuse the single-frame 5% gate for superframes).
"""
import inspect
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import v80_s2_peg as s2

SEED_A = 2026092001
SEED_B = 2026092002

REPO = Path(__file__).resolve().parents[3]
FORBIDDEN_PREFIX_ROOTS = (
    REPO / "results",
    REPO / "comparison_bench" / "outputs_comparison",
    REPO / "workspace",
)


def test_c1_basis_constants():
    basis = s2.construction_basis()
    assert (s2.Q, s2.N_FRAME, s2.M2) == (32, 256, 47)
    assert (s2.M1_BASIS, s2.M_TOTAL) == (2, 49)
    assert basis["l2_lambda"] == {2: 1.0}
    assert basis["l1_lambda"] == {2: 1.0}
    assert basis["family"] == "peg-irregular"
    # Frozen arithmetic cross-checks (accounting map §1/§4):
    # f_layer = 5*47/(256*0.80690067) ≈ 1.1375; f_super = 1044/852.544 ≈ 1.2246.
    assert basis["f_layer_repro_basis"] == pytest.approx(1.1375, abs=1e-3)
    assert basis["f_super_basis"] == pytest.approx(1.2246, abs=1e-4)
    assert (4 * 5 * s2.M_TOTAL + 64) == 1044


def test_c1_construct_ok_and_deterministic():
    first = s2.construct_l2(SEED_A)
    assert first["status"] == "ok"
    assert first["n"] == 256 and first["m"] == 47
    assert first["family"] == "peg-irregular"
    assert first["total_sockets"] == 256 * 2  # regular-(2): all 256 vars degree 2
    assert first["var_counts"] == {2: 256}
    assert first["parallel_edges"] == 0
    assert first["rank"] is not None and first["rank"] > 0
    second = s2.construct_l2(SEED_A)
    assert second["triples"] == first["triples"]  # same seed ⇒ bit-identical
    assert second["four_cycles"] == first["four_cycles"]
    with pytest.raises(ValueError):
        s2.construct_l2(True)
    with pytest.raises(ValueError):
        s2.construct_l2(SEED_A, max_trials=0)


def test_c2_ban_refusal():
    with pytest.raises(ValueError):
        s2.refuse_three_shift_cyclic({"family": "three-shift-cyclic"})
    with pytest.raises(ValueError):
        s2.refuse_three_shift_cyclic({"family": "Three Shift Cyclic"})
    # The constructor's own family passes the guard.
    s2.refuse_three_shift_cyclic({"family": "peg-irregular"})
    with pytest.raises(ValueError):
        s2.refuse_three_shift_cyclic("not-a-mapping")


def test_c2_four_cycle_reported_not_gated():
    code = s2.construct_l2(SEED_A)
    report = s2.four_cycle_report(code)
    assert isinstance(report["four_cycles"], int) and report["four_cycles"] >= 0
    assert report["four_cycles"] == code["four_cycles"]
    # Packet leaves the 4-cycle gate open: explicit TBD, never invented.
    assert report["gate_threshold"] is None
    assert s2.FOUR_CYCLE_GATE_THRESHOLD is None
    assert "TBD" in report["gate_status"]
    # Exactness pin on a hand-built graph: one 4-cycle {v0,v1,c0,c1}
    # (v2 dangles off c0 and contributes no check pair).
    toy = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1), (0, 2, 1)]
    assert s2.count_four_cycles(toy, 3, 2) == 1
    with pytest.raises(ValueError):
        s2.count_four_cycles([(0, 9, 1)], 3, 2)


def test_c3_grouping_math():
    # 1.274% rule constant: 1-(1-0.05)^(1/4).
    assert s2.PER_FRAME_FER_FOR_SUPERFRAME_5PCT == pytest.approx(0.01274, abs=1e-5)
    assert s2.evaluate_superframe([True] * 4)["per_frame_fer_for_superframe_5pct"] \
        == pytest.approx(0.01274, abs=1e-5)
    all_ok = s2.evaluate_superframe([True, True, True, True])
    assert all_ok["group_accept"] is True
    assert all_ok["superframe_fail"] == 0
    assert all_ok["per_frame_fer"] == 0.0
    one_fail = s2.evaluate_superframe([True, False, True, True])
    assert one_fail["group_accept"] is False  # any-frame-fail ⇒ group fail
    assert one_fail["superframe_fail"] == 1
    assert one_fail["per_frame_fer"] == pytest.approx(0.25)
    # D_blind surcharge plumbed: 1044 + D_blind over 1024*H_full.
    assert all_ok["leak_bits"] == 1044.0
    assert all_ok["f_super"] == pytest.approx(1.2246, abs=1e-4)
    assert "NEVER-ASSUME-ZERO" in all_ok["d_blind_label"]
    with_blind = s2.evaluate_superframe([True] * 4, d_blind=8.0)
    assert with_blind["leak_bits"] == 1052.0
    assert with_blind["f_super"] > all_ok["f_super"]
    with pytest.raises(ValueError):
        s2.evaluate_superframe([True] * 3)
    with pytest.raises(ValueError):
        s2.evaluate_superframe([True] * 4, d_blind=-1.0)


def test_c4_smoke_decode_runs():
    code = s2.construct_l2(SEED_A)
    seen_status = set()
    for seed in (SEED_A, SEED_B):  # 2 blocks (budget allows <=5)
        out = s2.smoke_decode_frame(code, seed, max_iter=s2.MAX_ITER)
        assert out["max_iter"] == 300 and out["qber"] == pytest.approx(0.05)
        assert out["status"] in ("success", "converged_no_syndrome",
                                 "max_iter_reached", "decode_failed")
        assert isinstance(out["iterations"], int) and out["iterations"] >= 1
        assert isinstance(out["reconstruction_ok"], bool)
        assert isinstance(out["exact_match"], bool)
        assert "no FER meaning" in out["note"]
        seen_status.add(out["status"])
    assert len(seen_status) >= 1
    with pytest.raises(ValueError):
        s2.smoke_decode_frame(code, SEED_A, max_iter=301)
    # Sampler hook is injectable: zero-error sampler shape-conforms.
    def _perfect(rng, n):
        alice = rng.integers(0, 32, size=n).astype(np.int64)
        return alice, alice.copy()
    out = s2.smoke_decode_frame(code, SEED_A, sampler=_perfect, max_iter=300)
    assert out["status"] in ("success", "converged_no_syndrome",
                             "max_iter_reached", "decode_failed")


def test_c5_no_overwrite_guards():
    for root in FORBIDDEN_PREFIX_ROOTS:
        if root.exists():
            hits = [p for p in root.rglob("v80_s2*")]
            assert hits == [], f"v80_s2 artifacts under forbidden root {root}: {hits}"
    # Helpers are pure in-memory: no output-path/root/file arguments.
    for name in ("construct_l2", "smoke_decode_frame", "evaluate_superframe",
                 "count_four_cycles", "qsc_pair_sampler"):
        params = set(inspect.signature(getattr(s2, name)).parameters)
        assert not (params & {"root", "path", "output", "outfile", "writer"}), name
