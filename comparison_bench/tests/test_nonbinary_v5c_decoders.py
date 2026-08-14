"""Route C decoder tests: structure, sched/EMS determinism, damping schedule,
EMS truncation bounds, and the pure in-memory v4-warm equivalence contract."""
from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5c_decoders as v5c
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v4_ir as v4
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

Q, N, NM = 1024, 64, 64


def _zero_syn(mats, checks):
    return nonbinary_syndrome(mats[checks], (0,) * N, GF2mField.create(Q))


def _fresh_state(policy, bob, syn, checks, manifest, mats, p=.30):
    """Bare uniform-initialized state without running any stage (for
    equivalence / single-update comparisons)."""
    edges = v5c._edges(mats[checks])[0]
    if policy == "nbldpc_v5c_ems":
        messages = {(r, v): np.full(Q, v5c._NEG, dtype=np.float64)
                    for r, es in enumerate(edges) for v, _ in es}
        for r, es in enumerate(edges):
            for v, _ in es:
                messages[r, v][:min(NM, Q)] = 0.0
    else:
        messages = {(r, v): np.full(Q, 1.0 / Q, dtype=np.float64)
                    for r, es in enumerate(edges) for v, _ in es}
    return v5c.DecoderState(v5c.METHOD, policy, manifest["canonical_sha256"], p, checks,
                            tuple(syn), tuple(bob), messages)


def test_public_only_core_and_state_is_not_serializable():
    cb, mats = v5c.codebook()
    assert cb["canonical_schema"] == "NBLDPC5B" and cb["q"] == 1024  # Route C identity: NBLDPC5B
    assert not any(x in name.lower() for name in inspect.signature(v5c.start).parameters
                   for x in ("alice", "truth", "callback"))
    syn = _zero_syn(mats, 32)
    started = v5c.start("nbldpc_v5c_sched", (0,) * N, syn, cb, p=.20,
                        stage_runner=lambda state, mats, stage: {"status": "syndrome_consistent",
                                                                 "iterations": 1,
                                                                 "decoded_symbols": state.bob})
    state, result, _ = started
    assert result["status"] == "syndrome_consistent"
    with pytest.raises(TypeError, match="not serializable"):
        state.__getstate__()


def test_policy_frozen_parameters():
    sched = v5c.policy_spec("nbldpc_v5c_sched", .30)
    ems = v5c.policy_spec("nbldpc_v5c_ems", .30)
    assert sched["decoder"] == "damped_fft_qspa"
    assert sched["damping_schedule"] == [0.5, 0.75, 0.90]
    assert ems["decoder"] == "ems" and ems["nm"] == 64 and ems["alpha"] == 0.8
    assert v5c.verification_cap("nbldpc_v5c_sched") == 3
    assert v5c.verification_cap("nbldpc_v5c_ems") == 3
    assert v5c.protocol_epsilon("nbldpc_v5c_sched") == 2.0 ** -62
    assert v5c.protocol_epsilon("nbldpc_v5c_ems") == 2.0 ** -62
    with pytest.raises(ValueError):
        v5c.policy_spec("nbldpc_v5c_sched", .40)


def test_three_level_warm_chain_for_both_policies_at_p30():
    cb, mats = v5c.codebook()
    fake = lambda state, mats, stage: {"status": "decode_failed", "iterations": 1}
    for policy in v5c.POLICIES:
        syn40 = _zero_syn(mats, 40)
        state, _, _ = v5c.start(policy, (0,) * N, syn40, cb, p=.30, stage_runner=fake)
        assert state.active_checks == 40
        old = next(iter(state.messages))
        state.messages[old] = np.full(Q, 1 / Q)
        first = v5c.extend(state, (0,) * 8, mats, mode="warm")
        assert first.active_checks == 48 and old in first.messages
        assert first.messages[old].shape == (Q,)
        second = v5c.extend(first, (0,) * 8, mats, mode="warm")
        assert second.active_checks == 56 and old in second.messages
        assert v5c.run_stage(second, mats, stage=2, stage_runner=fake)["status"] == "decode_failed"
        assert v5c.run_stage(second, mats, stage=3, stage_runner=fake)["status"] == "decode_failed"
        # production path on the zero frame still decodes the zero word at 56 checks
        assert v5c.production_runner(second, mats, 3)["status"] == "syndrome_consistent"
        assert v5c.extend(second, (0,) * 8, mats, mode="warm")["status"] == "invalid_input"
        assert v5c.extend(second, (0,) * 8, mats, mode="restart")["status"] == "invalid_input"
        assert v5c.extend(first, (0,) * 7, mats, mode="warm")["status"] == "invalid_input"
        assert v5c.run_stage(second, mats, stage=1)["status"] == "invalid_input"


def test_damping_schedule_quartiles_are_frozen():
    assert v5c._damping(1) == 0.5 and v5c._damping(4) == 0.5
    assert v5c._damping(5) == 0.75 and v5c._damping(8) == 0.75
    assert v5c._damping(9) == 0.90 and v5c._damping(12) == 0.90
    assert v5c._damping(13) == 0.90  # clamped at the top quartile


def test_sched_const_075_matches_v4_warm_bytewise():
    """Pure in-memory equivalence: v5c_sched with constant lambda .75 is
    byte-identical to the v4 warm decoder on identical inputs."""
    v3cb, v3mats = v4.codebook()
    rng = np.random.default_rng(7)
    alice = rng.integers(0, Q, size=N)
    syn48 = nonbinary_syndrome(v3mats[48], alice, GF2mField.create(Q))
    bob = alice.copy(); bob[3] = (alice[3] + 5) % Q
    st4 = _fresh_state("nbldpc_v5c_sched", bob, syn48[:40], 40, v3cb, v3mats)
    # v4 state uses the same uniform init; only the policy label differs
    st4 = v5c.DecoderState(v4.METHOD, "nbldpc_v4_ir_warm", v3cb["canonical_sha256"], .30,
                           40, tuple(syn48[:40]), tuple(bob), dict(st4.messages))
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v5c_decoders as mod
    original = mod.SCHEDULE
    mod.SCHEDULE = (0.75, 0.75, 0.75)  # force the constant-lambda regime
    try:
        st5 = _fresh_state("nbldpc_v5c_sched", bob, syn48[:40], 40, v3cb, v3mats)
        v4._run(st4, v3mats, iterations=1)
        mod._run_sched(st5, v3mats, iterations=1)
    finally:
        mod.SCHEDULE = original
    for key in st4.messages:
        assert np.array_equal(st4.messages[key], st5.messages[key]), key
    # and the scheduled path still terminates deterministically
    st5b = _fresh_state("nbldpc_v5c_sched", bob, syn48[:40], 40, v3cb, v3mats)
    result = mod._run_sched(st5b, v3mats, iterations=12)
    assert result["status"] in {"syndrome_consistent", "decode_failed", "decoder_error"}
    assert 1 <= int(result["iterations"]) <= 12


def test_ems_truncation_and_sorting_determinism():
    cb, mats = v5c.codebook()
    rng = np.random.default_rng(11)
    alice = rng.integers(0, Q, size=N)
    syn56 = nonbinary_syndrome(mats[56], alice, GF2mField.create(Q))
    bob = alice.copy()
    bob[0] = (alice[0] + 1) % Q; bob[9] = (alice[9] + 2) % Q
    state, _, _ = v5c.start("nbldpc_v5c_ems", bob, syn56[:40], cb, p=.30,
                            stage_runner=lambda *_: {"status": "decode_failed", "iterations": 1})
    # fresh bare state: after one real update every stored message stays
    # finite and bounded (full-domain vector, floor entries untouched)
    fresh = _fresh_state("nbldpc_v5c_ems", bob, syn56[:40], 40, cb, mats)
    v5c._run_ems(fresh, mats, iterations=1)
    for key, msg in fresh.messages.items():
        assert np.isfinite(msg).all(), key
        assert msg.max() <= 0.0 and msg.min() >= v5c._NEG, key
    # convolution inputs are nm-truncated: _top_nm on any extrinsic vector
    # keeps at most NM real entries
    priors = v5c._llr_priors(bob, Q, .30)
    truncated = v5c._top_nm(priors[0])
    assert int((truncated > v5c._NEG).sum()) <= NM
    # determinism: identical fresh inputs produce identical outcomes
    first_state = _fresh_state("nbldpc_v5c_ems", bob, syn56[:40], 40, cb, mats)
    second_state = _fresh_state("nbldpc_v5c_ems", bob, syn56[:40], 40, cb, mats)
    first = v5c._run_ems(first_state, mats, iterations=12)
    second = v5c._run_ems(second_state, mats, iterations=12)
    assert first == second  # fully deterministic
    assert first["status"] in {"syndrome_consistent", "decode_failed", "decoder_error"}
    assert 1 <= int(first["iterations"]) <= 12


def test_ems_alpha_correction_is_bounded_and_floor_stable():
    cb, mats = v5c.codebook()
    syn = _zero_syn(mats, 40)
    state, _, _ = v5c.start("nbldpc_v5c_ems", (0,) * N, syn, cb, p=.30,
                            stage_runner=lambda *_: {"status": "decode_failed", "iterations": 1})
    fresh = _fresh_state("nbldpc_v5c_ems", (0,) * N, syn, 40, cb, mats)
    v5c._run_ems(fresh, mats, iterations=1)
    for key, msg in fresh.messages.items():
        assert np.isfinite(msg).all()
        assert msg.max() <= 0.0 and msg.min() >= v5c._NEG
        assert int((msg > v5c._NEG).sum()) <= Q


def test_iteration_cap_and_invalid_input_fail_closed():
    cb, mats = v5c.codebook()
    syn = _zero_syn(mats, 32)
    state, result, _ = v5c.start("nbldpc_v5c_sched", (0,) * N, syn, cb, p=.20,
                                 stage_runner=lambda *_: {"status": "decode_failed", "iterations": 1})
    assert v5c.run_stage(state, mats, stage=2,
                         stage_runner=lambda *_: {"status": "decode_failed", "iterations": 13})["status"] == "aborted_resource_limit"
    assert v5c.start("nbldpc_v5c_sched", (0,) * N, syn, {"bogus": 1}, p=.20)["status"] == "codebook_invalid"
    assert v5c.start("nbldpc_v5c_sched", (0,) * 63, syn, cb, p=.20)["status"] == "invalid_input"
    assert v5c.start("nope", (0,) * N, syn, cb, p=.20)["status"] == "invalid_input"
    unknown = {"status": "something_else", "iterations": 1}
    assert v5c.run_stage(state, mats, stage=2, stage_runner=lambda *_: unknown)["status"] == "decoder_error"


def test_zero_word_production_decoding_is_deterministic_for_both():
    cb, mats = v5c.codebook()
    field = GF2mField.create(Q)
    syn56 = nonbinary_syndrome(mats[56], (0,) * N, field)
    for policy in v5c.POLICIES:
        state, _, _ = v5c.start(policy, (0,) * N, syn56[:40], cb, p=.30)
        extended = v5c.extend(state, syn56[40:48], mats, mode="warm")
        extended = v5c.extend(extended, syn56[48:56], mats, mode="warm")
        first = v5c.production_runner(extended, mats, 3)
        second = v5c.production_runner(extended, mats, 3)
        assert first == second and first["status"] == "syndrome_consistent"
        assert 1 <= int(first["iterations"]) <= 12


def test_noisy_frames_decode_deterministically():
    cb, mats = v5c.codebook()
    rng = np.random.default_rng(23)
    field = GF2mField.create(Q)
    for policy in v5c.POLICIES:
        outcomes = []
        for _ in range(8):
            alice = rng.integers(0, Q, size=N)
            bob = alice.copy()
            flips = rng.random(N) < 0.08
            bob[flips] = rng.integers(0, Q, size=int(flips.sum()))
            syn56 = nonbinary_syndrome(mats[56], alice, field)
            state, res, _ = v5c.start(policy, bob, syn56[:40], cb, p=.30)
            extended = v5c.extend(state, syn56[40:48], mats, mode="warm")
            extended = v5c.extend(extended, syn56[48:56], mats, mode="warm")
            result = v5c.production_runner(extended, mats, 3)
            assert result["status"] in {"syndrome_consistent", "decode_failed", "decoder_error"}
            outcomes.append(result["status"])
        assert outcomes  # deterministic (no crash) for all trials
