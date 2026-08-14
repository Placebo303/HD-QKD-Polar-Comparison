from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5b_multistage as v5b
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

def test_public_only_core_and_state_is_not_serializable():
    cb, mats = v5b.codebook()
    assert cb["canonical_schema"] == "NBLDPC5B" and cb["q"] == 1024
    assert not any(x in name.lower() for name in inspect.signature(v5b.start).parameters
                   for x in ("alice", "truth", "callback"))
    syn = nonbinary_syndrome(mats[32], (0,) * 64, GF2mField.create(1024))
    started = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn, cb, p=.20,
                        stage_runner=lambda state, mats, stage: {"status": "syndrome_consistent",
                                                                 "iterations": 1,
                                                                 "decoded_symbols": state.bob})
    state, result, matrices = started
    assert result["status"] == "syndrome_consistent"
    with pytest.raises(TypeError, match="not serializable"):
        state.__getstate__()

def test_three_level_warm_chain_for_ir56_at_p30():
    cb, mats = v5b.codebook()
    syn = nonbinary_syndrome(mats[40], (0,) * 64, GF2mField.create(1024))
    fake = lambda state, mats, stage: {"status": "decode_failed", "iterations": 1}
    state, _, _ = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn, cb, p=.30, stage_runner=fake)
    assert state.active_checks == 40
    old = next(iter(state.messages))
    state.messages[old] = np.full(1024, 1 / 1024)
    first = v5b.extend(state, (0,) * 8, mats, mode="warm")
    assert first.active_checks == 48 and old in first.messages
    assert first.messages[old].shape == (1024,)
    second = v5b.extend(first, (0,) * 8, mats, mode="warm")
    assert second.active_checks == 56 and old in second.messages
    assert v5b.run_stage(second, mats, stage=2, stage_runner=fake)["status"] == "decode_failed"
    assert v5b.run_stage(second, mats, stage=3, stage_runner=fake)["status"] == "decode_failed"
    # production path on the zero frame still decodes the zero word at 56 checks
    assert v5b.production_runner(second, mats, 3)["status"] == "syndrome_consistent"
    # extension past the final level is closed
    assert v5b.extend(second, (0,) * 8, mats, mode="warm")["status"] == "invalid_input"
    assert v5b.extend(second, (0,) * 8, mats, mode="restart")["status"] == "invalid_input"
    assert v5b.extend(first, (0,) * 7, mats, mode="warm")["status"] == "invalid_input"
    assert v5b.run_stage(second, mats, stage=1)["status"] == "invalid_input"

def test_control_policy_never_exceeds_two_levels():
    cb, mats = v5b.codebook()
    fake = lambda state, mats, stage: {"status": "decode_failed", "iterations": 1}
    syn40 = nonbinary_syndrome(mats[40], (0,) * 64, GF2mField.create(1024))
    state, _, _ = v5b.start("nbldpc_v5b_ir48", (0,) * 64, syn40, cb, p=.30, stage_runner=fake)
    extended = v5b.extend(state, (0,) * 8, mats, mode="warm")
    assert extended.active_checks == 48
    assert isinstance(v5b.extend(extended, (0,) * 8, mats, mode="warm"), dict)
    syn32 = nonbinary_syndrome(mats[32], (0,) * 64, GF2mField.create(1024))
    state, _, _ = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn32, cb, p=.20, stage_runner=fake)
    extended = v5b.extend(state, (0,) * 8, mats, mode="warm")
    assert extended.active_checks == 40
    assert isinstance(v5b.extend(extended, (0,) * 8, mats, mode="warm"), dict)

def test_ladders_slots_caps_and_epsilon_bounds():
    assert v5b.policy_spec("nbldpc_v5b_ir56", .20)["ladder"] == [32, 40]
    assert v5b.policy_spec("nbldpc_v5b_ir56", .30)["ladder"] == [40, 48, 56]
    assert v5b.policy_spec("nbldpc_v5b_ir48", .30)["ladder"] == [40, 48]
    assert v5b.stage_slots("nbldpc_v5b_ir56", .30) == (0, 1, 2)
    assert v5b.stage_slots("nbldpc_v5b_ir48", .30) == (0, 1)
    assert v5b.extension_mode("nbldpc_v5b_ir56") == "warm"
    assert v5b.verification_cap("nbldpc_v5b_ir56") == 3 and v5b.verification_cap("nbldpc_v5b_ir48") == 2
    assert v5b.protocol_epsilon("nbldpc_v5b_ir56") == 2.0 ** -62
    assert v5b.protocol_epsilon("nbldpc_v5b_ir48") == 2.0 ** -63
    with pytest.raises(ValueError):
        v5b.policy_spec("nbldpc_v5b_ir56", .40)

def test_iteration_cap_and_invalid_input_fail_closed():
    cb, mats = v5b.codebook()
    syn = nonbinary_syndrome(mats[32], (0,) * 64, GF2mField.create(1024))
    state, result, _ = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn, cb, p=.20,
                                 stage_runner=lambda *_: {"status": "decode_failed", "iterations": 1})
    assert v5b.run_stage(state, mats, stage=2,
                         stage_runner=lambda *_: {"status": "decode_failed", "iterations": 13})["status"] == "aborted_resource_limit"
    assert v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn, {"bogus": 1}, p=.20)["status"] == "codebook_invalid"
    assert v5b.start("nbldpc_v5b_ir56", (0,) * 63, syn, cb, p=.20)["status"] == "invalid_input"
    assert v5b.start("nope", (0,) * 64, syn, cb, p=.20)["status"] == "invalid_input"
    unknown = {"status": "something_else", "iterations": 1}
    assert v5b.run_stage(state, mats, stage=2, stage_runner=lambda *_: unknown)["status"] == "decoder_error"

def test_zero_word_production_decoding_is_deterministic_and_bounded():
    cb, mats = v5b.codebook()
    field = GF2mField.create(1024)
    syn56 = nonbinary_syndrome(mats[56], (0,) * 64, field)
    syn40 = syn56[:40]
    state, _, _ = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn40, cb, p=.30)
    extended = v5b.extend(state, syn56[40:48], mats, mode="warm")
    extended = v5b.extend(extended, syn56[48:56], mats, mode="warm")
    first = v5b.production_runner(extended, mats, 3)
    second = v5b.production_runner(extended, mats, 3)
    assert first == second and first["status"] == "syndrome_consistent"
    assert 1 <= int(first["iterations"]) <= 12

def test_production_runner_is_bound_and_status_is_bounded():
    cb, mats = v5b.codebook()
    syn = nonbinary_syndrome(mats[40], (0,) * 64, GF2mField.create(1024))
    state, _, _ = v5b.start("nbldpc_v5b_ir56", (0,) * 64, syn, cb, p=.30)
    result = v5b.production_runner(state, mats, 1)
    assert result["status"] in {"syndrome_consistent", "decode_failed", "decoder_error"}
