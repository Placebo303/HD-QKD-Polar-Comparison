"""Route D (nbldpc_formal_v5d_post) core tests: policy contract, bounded list
stage, ADMM golden q=4, terminal post trigger, no-additional-disclosure, and
non-serializable state.  All deterministic, no production paths touched."""
from __future__ import annotations
import inspect
import pickle
import types
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5d_post as post
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5c_decoders as v5c
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

Q, N = post.Q, post.N
_W5, _W9 = 11, 22  # wrong (argmax) symbols at the two low-confidence variables


def _beliefs(layout, default=0.01):
    """Per-variable belief peaks; variables absent from ``layout`` get their
    argmax at their own index j (so the true codeword is argmax everywhere
    except j=5/j=9, which carry the layout's error symbols)."""
    beliefs = []
    for j in range(N):
        b = np.full(Q, default)
        if j in layout:
            for symbol, value in layout[j].items():
                b[symbol] = value
        else:
            b[j] = 0.99
        beliefs.append(b)
    return beliefs


def _true_codeword():
    true = np.arange(N, dtype=np.int64)
    true[5], true[9] = 130, 777
    return true


def _list_state(matrices, true):
    syndrome = nonbinary_syndrome(matrices[40], true, GF2mField.create(Q))
    return types.SimpleNamespace(active_checks=40, syndrome=tuple(syndrome),
                                 policy_id="nbldpc_v5d_sched_post", p=0.3, messages={})


def _fresh_state(checks, syn, policy="nbldpc_v5d_sched_post", p=0.30):
    """Bare v5c.DecoderState carrying a v5d policy label (what the post
    wrapper's run_stage ladder lookup needs); nothing is run."""
    cb, mats = post.codebook()
    edges = v5c._edges(mats[checks])[0]
    messages = {(r, v): np.full(Q, 1.0 / Q, dtype=np.float64)
                for r, es in enumerate(edges) for v, _ in es}
    return v5c.DecoderState(v5c.METHOD, policy, cb["canonical_sha256"], p, checks,
                            tuple(syn), (0,) * N, messages)


def test_policy_contract():
    assert post.POLICIES == ("nbldpc_v5d_sched_post", "nbldpc_v5d_ems_post")
    for pol in post.POLICIES:
        assert post.LADDERS[pol] == {0.20: (32, 40), 0.30: (40, 48, 56)}
        assert post.verification_cap(pol) == 3
        assert post.protocol_epsilon(pol) == 2.0 ** -62
        spec = post.policy_spec(pol, 0.30)
        assert spec["post_processing"] == "list_then_admm"
        if pol == "nbldpc_v5d_sched_post":
            assert spec["decoder"] == "damped_fft_qspa"
            assert spec["damping_schedule"] == [0.5, 0.75, 0.90]
        else:
            assert spec["decoder"] == "ems" and spec["nm"] == 64 and spec["alpha"] == 0.8
    assert post.codebook()[0]["canonical_sha256"] == v5c.codebook()[0]["canonical_sha256"]


def test_list_stage_finds_correct_candidate():
    _, mats = post.codebook()
    true = _true_codeword()
    state = _list_state(mats, true)
    # j=5/j=9 low confidence (0.50), true error symbols inside their top-8
    hit = post._list_stage(state, mats, _beliefs(
        {5: {_W5: 0.50, 130: 0.40}, 9: {_W9: 0.50, 777: 0.40}}))
    assert hit["status"] == "syndrome_consistent"
    assert hit["decoded_symbols"] == tuple(true)
    # 64-candidate semantics: both top-8s hold only wrong symbols -> None
    assert post._list_stage(state, mats, _beliefs(
        {5: {_W5: 0.50, 22: 0.40}, 9: {33: 0.50, 44: 0.40}})) is None


def test_list_stage_deterministic_and_bounded():
    _, mats = post.codebook()
    true = _true_codeword()
    state = _list_state(mats, true)
    success = _beliefs({5: {_W5: 0.50, 130: 0.40}, 9: {_W9: 0.50, 777: 0.40}})
    # identical inputs -> identical result
    assert post._list_stage(state, mats, success) == post._list_stage(state, mats, success)
    # tops are exactly 8 symbols: the true error symbol ranked 9th is missed
    rank9 = _beliefs({5: {s: 0.90 - 0.05 * i for i, s in enumerate((11, 12, 13, 14, 15, 16, 17, 18))} | {130: 0.49},
                      9: {s: 0.88 - 0.05 * i for i, s in enumerate((21, 23, 24, 25, 26, 27, 28, 29))} | {777: 0.47}})
    assert post._list_stage(state, mats, rank9) is None
    # L=2 semantics: only one variable is genuinely in error; the other worst
    # variable is low-confidence but argmax-correct, so flipping it is a no-op
    l2 = post._list_stage(state, mats, _beliefs({5: {_W5: 0.60, 130: 0.50}, 9: {777: 0.55}}))
    assert l2 is not None and l2["decoded_symbols"] == tuple(true)
    # ...but with the true symbol absent from every top-8, nothing is found
    assert post._list_stage(state, mats, _beliefs(
        {5: {_W5: 0.50, 22: 0.40}, 9: {33: 0.50, 44: 0.40}})) is None


def test_admm_golden_q4(monkeypatch):
    monkeypatch.setattr(post, "Q", 4)
    monkeypatch.setattr(post, "N", 4)
    monkeypatch.setattr(post, "_BITS", 2)
    field = GF2mField.create(4)
    matrices = {1: np.array([[1, 1, 1, 1]]),
                2: np.array([[1, 1, 1, 0], [0, 1, 1, 1]])}
    rng = np.random.default_rng(20260802)  # PCG64
    for checks, H in matrices.items():
        recovered = 0
        for trial in range(20):
            while True:
                codeword = rng.integers(0, 4, 4)
                if nonbinary_syndrome(H, codeword, field) == (0,) * checks:
                    break  # only words satisfying every row are used
            beliefs = []
            for j in range(4):
                b = np.full(4, 0.1)
                b[codeword[j]] = 0.7
                beliefs.append(b)
            syndrome = nonbinary_syndrome(H, codeword, field)
            state = types.SimpleNamespace(active_checks=checks, syndrome=tuple(syndrome),
                                          policy_id="nbldpc_v5d_sched_post", p=0.3, messages={})
            result = post._admm(state, {checks: H}, beliefs)
            assert result is not None
            assert result["iterations"] <= 50
            if result["status"] == "syndrome_consistent" and result["decoded_symbols"] == tuple(codeword):
                recovered += 1
            if trial == 0:
                assert post._admm(state, {checks: H}, beliefs) == result  # deterministic
        assert recovered >= 18


def test_run_stage_terminal_trigger(monkeypatch):
    _, mats = post.codebook()
    field = GF2mField.create(Q)
    syn40 = nonbinary_syndrome(mats[40], (0,) * N, field)
    syn56 = nonbinary_syndrome(mats[56], (0,) * N, field)
    fake_fail = lambda state, mats, stage: {"status": "decode_failed", "iterations": 1}
    st40 = _fresh_state(40, syn40)
    st56 = _fresh_state(56, syn56)
    # non-terminal level (40 is not the ladder end at p=.30): pass through
    res = post.run_stage(st40, mats, stage=2, stage_runner=fake_fail)
    assert res["status"] == "decode_failed" and "post_processing" not in res
    # terminal level (56 == ladder end): decode_failed triggers post
    calls = {"n": 0}
    sentinel = {"status": "syndrome_consistent", "post_processing": "sentinel", "iterations": 1}

    def fake_post(state, matrices, stage_result):
        calls["n"] += 1
        return dict(sentinel)

    monkeypatch.setattr(post, "_post", fake_post)
    assert post.run_stage(st56, mats, stage=2, stage_runner=fake_fail) == sentinel
    assert calls["n"] == 1
    # syndrome_consistent / decoder_error: no post trigger
    consistent = lambda state, mats, stage: {"status": "syndrome_consistent",
                                             "iterations": 1, "decoded_symbols": (0,) * N}
    assert post.run_stage(st56, mats, stage=2, stage_runner=consistent)["status"] == "syndrome_consistent"
    error = lambda state, mats, stage: {"status": "decoder_error", "iterations": 1}
    assert post.run_stage(st56, mats, stage=2, stage_runner=error)["status"] == "decoder_error"
    assert calls["n"] == 1


def test_no_additional_disclosure():
    source = inspect.getsource(post)
    for name in ("materialize_seed_record", "locked_seed_bits", "toeplitz_tag"):
        assert name not in source
        assert not hasattr(post, name)
    assert not hasattr(post._post, "materialize_seed_record")


def test_state_not_serializable():
    _, mats = post.codebook()
    syn40 = nonbinary_syndrome(mats[40], (0,) * N, GF2mField.create(Q))
    state = _fresh_state(40, syn40)
    with pytest.raises(TypeError, match="not serializable"):
        pickle.dumps(state)


def test_start_extend_runstage_integration_trigger(monkeypatch):
    """Full delegation chain in production shape (runtime _result loop):
    post.start -> post.extend (+1 ladder level each) -> post.run_stage.
    The delegated state carries the *v5c* policy id, so the v5d ladder lookup
    in run_stage must use the reverse map for the terminal trigger to fire."""
    rng = np.random.default_rng(20260802)  # PCG64 fixed seed
    cb, mats = post.codebook()
    bob = tuple(int(x) for x in rng.integers(0, Q, N))
    syn40 = tuple(int(x) for x in rng.integers(0, Q, 40))
    # production extends one ladder level per call: 40->48 and 48->56 each
    # consume 8 new syndrome symbols (runtime passes full[prev_checks:checks])
    suffix_a, suffix_b = tuple(range(8)), tuple(range(8, 16))
    # legal decode_failed dict per v5c._stage (iterations field required)
    fake_fail = lambda state, matrices, stage: {"status": "decode_failed", "q": Q, "n": N,
                                                "check_count": 40, "iterations": 12,
                                                "reason": "iteration_limit"}
    calls = {"n": 0}
    sentinel = {"status": "syndrome_consistent", "post_processing": "sentinel", "iterations": 1}

    def fake_post(state, matrices, stage_result):
        calls["n"] += 1
        return dict(sentinel)

    monkeypatch.setattr(post, "_post", fake_post)

    # forward: v5d policy id delegated by post.start -> state carries v5c id
    bound = post.start("nbldpc_v5d_sched_post", bob, syn40, cb, p=0.30, stage_runner=fake_fail)
    state, first, _ = bound
    assert first["status"] == "decode_failed"
    assert state.policy_id == "nbldpc_v5c_sched"  # delegation label on the state
    state = post.extend(state, suffix_a, mats, mode="warm")
    state = post.extend(state, suffix_b, mats, mode="warm")
    assert state.active_checks == 56  # terminal ladder level
    res = post.run_stage(state, mats, stage=3, stage_runner=fake_fail)
    assert res == sentinel  # terminal trigger path reached post
    assert calls["n"] == 1

    # reverse control: state carrying the v5c policy id directly (non-delegated
    # usage via v5c.start) also triggers, because the reverse map resolves it
    bound2 = v5c.start("nbldpc_v5c_sched", bob, syn40, cb, p=0.30, stage_runner=fake_fail)
    state2, _, _ = bound2
    state2 = post.extend(state2, suffix_a, mats, mode="warm")
    state2 = post.extend(state2, suffix_b, mats, mode="warm")
    assert state2.policy_id == "nbldpc_v5c_sched"
    res2 = post.run_stage(state2, mats, stage=3, stage_runner=fake_fail)
    assert res2 == sentinel  # reverse map effective
    assert calls["n"] == 2
