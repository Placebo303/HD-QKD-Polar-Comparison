"""Fake-only tests for the shape-aware accounting identities.

Hand constants only (f = 1.3, N = 1024, H = 0.5, TAG = 64, BUDGET = 1104);
zero scientific/real-data contact -- this file reads no CQ JSON, no
S0_RESULT.json, no .ttbin, nothing, and imports no science code (the helper
under test is stdlib + math only).
"""

from __future__ import annotations

from comparison_bench.src.comparison_bench.cli.probes_closed import accounting_identities as ai


def test_c1_total_identity_holds():
    # ceil(1.3*1024*0.5) = ceil(665.6) = 666; LEAK = 666 - 64 = 602;
    # margins 1104 - 666 = 438 and 1040 - 602 = 438 agree.
    assert ai.joint_total(1.3, 1024, 0.5) == 666
    assert ai.leak_of(666, 64) == 602
    assert ai.check_c1_total_identity(1.3, 1024, 0.5, 666, 64, 1104)


def test_c1_negative_each_arm_fires():
    # Wrong total (tag added on): gate equivalence breaks -> check fires.
    assert not ai.check_c1_total_identity(1.3, 1024, 0.5, 730, 64, 1104)
    # Wrong total (tag omitted from the leak side is impossible here, so use
    # a bare off-by-one total): any total != ceil trips the check.
    assert not ai.check_c1_total_identity(1.3, 1024, 0.5, 665, 64, 1104)


def test_c2_trap_rejects_double_count():
    # Honest single-block quantity passes: Q - B == ceil - B.
    assert ai.check_c2_no_double_count(666, 1.3, 1024, 0.5, 1104)
    # THE TRAP: Q formed as ceil(f*N*H) + 64 = 730 must be detected.
    assert not ai.check_c2_no_double_count(730, 1.3, 1024, 0.5, 1104)


def test_c3_frame_shape_holds():
    parities = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    assert ai.check_c3_frame_shape(parities, sum(parities) + 64, 64)


def test_c3_negative_both_misforms_fire():
    parities = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    # Tag omitted (difference 0) trips.
    assert not ai.check_c3_frame_shape(parities, sum(parities), 64)
    # Tag doubled (difference 128) trips.
    assert not ai.check_c3_frame_shape(parities, sum(parities) + 128, 64)
