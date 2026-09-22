import importlib.util
import pathlib
import uuid

import numpy as np
import pandas as pd
import pytest


ROOT = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "v72p2_real_smoke_test_module", ROOT / "scripts" / "v72p2_real_smoke.py"
)
V72P2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V72P2)
ADAPTER = V72P2._ADAPTER


def _prior(nonuniform=False):
    prior = np.full((1024, 1024), -np.log(1024.0), dtype=np.float64)
    if nonuniform:
        prior[0, 0] += 1.0
        prior[0] -= np.logaddexp.reduce(prior[0])
    return prior


def _bits(value=0):
    return np.full(10240, value, dtype=np.uint8)


def _run_block_kwargs(indptr, indices, *, checkpoints, decoder, total=720, alice=None):
    bits = _bits(0) if alice is None else np.asarray(alice, dtype=np.uint8)
    return dict(
        block_id=0,
        frame_ids=list(range(1726, 1730)),
        alice_bits=bits,
        prior_logp=_prior(),
        syndrome_full=np.zeros(max(checkpoints), dtype=np.uint8),
        reference_tag=b"mismatch",
        indptr=indptr,
        indices=indices,
        decoder=decoder,
        checkpoint_rows=tuple(checkpoints),
        max_iter_per_checkpoint=1,
        max_total_iterations=total,
        deadline_s=float("inf"),
    )


def test_T1_A_warm_delta_and_final_readout():
    indptr = np.array([0, 2, 3], dtype=np.int32)
    indices = np.array([0, 1, 0], dtype=np.int32)
    syndrome = np.zeros(2, dtype=np.uint8)
    warm = np.full(3, 0.3, dtype=np.float64)
    result = ADAPTER.run_decoder(
        _prior(nonuniform=True),
        syndrome,
        indptr,
        indices,
        max_iter=1,
        warm_start_c2v=warm,
    )
    expected_residual = np.max(np.abs(result["check_to_variable"] - warm))
    assert result["residuals"][0] == pytest.approx(expected_residual)

    final_sum = np.bincount(
        result["edge_var"],
        weights=result["check_to_variable"],
        minlength=10240,
    ).reshape(1024, 10)
    assert np.allclose(result["bit_to_factor"], final_sum)
    expected_factor0 = np.array(
        [ADAPTER.local_factor_extrinsic(_prior(True)[0], final_sum[0], bit) for bit in range(10)]
    )
    assert np.allclose(result["factor_to_bit"][0], expected_factor0)
    assert np.allclose(result["factor_to_bit"][1:], 0.0)
    expected_app = np.clip(
        result["factor_to_bit"].reshape(10240) + final_sum.reshape(10240), -20.0, 20.0
    )
    assert np.allclose(result["app_llr"], expected_app)
    assert np.array_equal(result["hard_bits"], (expected_app > 0).astype(np.uint8))
    recomputed = np.zeros(2, dtype=np.uint8)
    for check in range(2):
        for edge in range(int(indptr[check]), int(indptr[check + 1])):
            recomputed[check] ^= result["hard_bits"][indices[edge]]
    assert np.array_equal(result["syndrome_observed"], recomputed)


def test_T1_B_prefix_carry_budget_and_zero_budget():
    indptr = np.array([0, 1, 3], dtype=np.int32)
    indices = np.array([0, 1, 2], dtype=np.int32)
    calls = []

    def fake_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        calls.append((target.copy(), indptr.copy(), indices.copy(), max_iter, warm_start_c2v.copy()))
        active = len(indices)
        return {
            "residuals": [1.0],
            "check_to_variable": np.arange(active, dtype=np.float64) + 0.5,
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 1.0,
        }

    result = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=(1, 2), decoder=fake_decoder, total=2)
    )
    assert [len(call[1]) for call in calls] == [2, 3]
    assert [len(call[2]) for call in calls] == [1, 3]
    assert np.array_equal(calls[0][4], np.zeros(1))
    assert np.array_equal(calls[1][4], np.array([0.5, 0.0, 0.0]))
    assert [call[3] for call in calls] == [1, 1]
    assert result["status"] == "LADDER_EXHAUSTED"
    assert result["iterations_used"] == 2
    assert result["disclosed_rows"] == 2
    assert result["control_bits_sent"] == 1
    assert V72P2.available_iterations(718) == 2
    assert V72P2.available_iterations(720) == 0

    two_calls = []

    def two_iteration_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        two_calls.append(max_iter)
        assert max_iter == 2
        return {
            "residuals": [1.0, 0.5],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 1.0,
        }

    two_kwargs = _run_block_kwargs(
        indptr,
        indices,
        checkpoints=(1, 2),
        decoder=two_iteration_decoder,
        total=2,
    )
    two_kwargs["max_iter_per_checkpoint"] = 10
    two = V72P2.run_block(**two_kwargs)
    assert two_calls == [2]
    assert two["iterations_used"] == 2 and two["disclosed_rows"] == 1
    assert two["status"] == "BUDGET_EXHAUSTED"

    zero_calls = []

    def zero_decoder(*args, **kwargs):
        zero_calls.append(True)
        raise AssertionError("zero budget must not call decoder")

    zero = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=(1,), decoder=zero_decoder, total=0)
    )
    assert zero["status"] == "BUDGET_EXHAUSTED"
    assert zero["attempted"] is False
    assert zero["disclosed_rows"] == zero["tag_bits_published"] == 0
    assert zero["control_bits_sent"] == 0
    assert zero_calls == []

    reset_warms = []

    def reset_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        reset_warms.append(warm_start_c2v.copy())
        return {
            "residuals": [1.0],
            "check_to_variable": np.arange(len(indices), dtype=np.float64) + 1.0,
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 0.0,
        }

    for _ in range(2):
        V72P2.run_block(
            **_run_block_kwargs(indptr, indices, checkpoints=(1,), decoder=reset_decoder, total=1)
        )
    assert len(reset_warms) == 2
    assert np.array_equal(reset_warms[0], np.zeros(1))
    assert np.array_equal(reset_warms[1], np.zeros(1))


def test_T1_C_current_conjunction_last_legal_and_oracle_isolation():
    indptr = np.array([0, 1, 2, 3], dtype=np.int32)
    indices = np.array([0, 1, 2], dtype=np.int32)
    zeros = _bits(0)
    ones = _bits(1)
    reference = V72P2.candidate_tag(zeros)
    sequence = [
        (zeros, np.ones(1, dtype=np.uint8)),
        (ones, np.zeros(2, dtype=np.uint8)),
        (zeros, np.zeros(3, dtype=np.uint8)),
    ]
    calls = []

    def fake_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        index = len(calls)
        calls.append(index)
        hard, observed = sequence[index]
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": hard,
            "syndrome_observed": observed,
            "finite": True,
            "max_llr": 1.0,
        }

    result = V72P2.run_block(
        block_id=0,
        frame_ids=[1726, 1727, 1728, 1729],
        alice_bits=ones,
        prior_logp=_prior(),
        syndrome_full=np.zeros(3, dtype=np.uint8),
        reference_tag=reference,
        indptr=indptr,
        indices=indices,
        decoder=fake_decoder,
        checkpoint_rows=(1, 2, 3),
        max_iter_per_checkpoint=1,
        max_total_iterations=3,
        deadline_s=float("inf"),
    )
    assert calls == [0, 1, 2]
    assert result["status"] == "VERIFIED"
    assert [x["protocol_accepted"] for x in result["per_checkpoint"]] == [False, False, True]
    assert result["protocol_accepted"] is True
    assert result["oracle_exact"] is False
    assert result["verified_exact_success"] is False
    assert result["undetected"] is True

    def legal_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": zeros,
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 0.0,
        }

    legal = V72P2.run_block(
        block_id=0,
        frame_ids=[1726, 1727, 1728, 1729],
        alice_bits=zeros,
        prior_logp=_prior(),
        syndrome_full=np.zeros(1, dtype=np.uint8),
        reference_tag=reference,
        indptr=np.array([0, 1], dtype=np.int32),
        indices=np.array([0], dtype=np.int32),
        decoder=legal_decoder,
        checkpoint_rows=(1,),
        max_iter_per_checkpoint=1,
        max_total_iterations=1,
        deadline_s=float("inf"),
    )
    assert legal["status"] == "VERIFIED"
    assert legal["iterations_used"] == 1


def test_T1_D_public_accounting_tails_and_failure_retention():
    checkpoints = (160, 288, 8992, 9032, 9036)
    indptr = np.arange(9037, dtype=np.int32)
    indices = np.zeros(9036, dtype=np.int32)

    def fail_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 1.0,
        }

    result = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=checkpoints, decoder=fail_decoder)
    )
    assert [x["new_rows"] for x in result["per_checkpoint"]] == [160, 128, 8704, 40, 4]
    assert result["status"] == "LADDER_EXHAUSTED"
    assert result["syndrome_bits_published"] == 9036
    assert result["tag_bits_published"] == 64
    assert result["control_bits_sent"] == 4
    assert result["leak_IR_bits"] == 9100
    assert result["total_public_bits"] == 9104

    calls = []

    def exception_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        calls.append(len(target))
        if len(calls) == 2:
            raise RuntimeError("synthetic decoder fault")
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 1.0,
        }

    failed = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=(160, 288, 8992), decoder=exception_decoder)
    )
    assert failed["status"] == "DECODER_ERROR"
    assert calls == [160, 288]
    assert failed["disclosed_rows"] == 288
    assert failed["syndrome_bits_published"] == 288
    assert failed["tag_bits_published"] == 64
    assert failed["control_bits_sent"] == 1
    assert failed["leak_IR_bits"] == 352
    assert failed["total_public_bits"] == 353
    assert failed["per_checkpoint"][1]["iterations"] is None
    assert failed["per_checkpoint"][1]["iterations_known"] is False

    def nonfinite_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": False,
            "max_llr": 20.0,
        }

    nonfinite = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=(160, 288), decoder=nonfinite_decoder)
    )
    assert nonfinite["status"] == "NUMERIC_FAILURE"
    assert nonfinite["disclosed_rows"] == 160
    assert nonfinite["tag_bits_published"] == 64
    assert nonfinite["control_bits_sent"] == 0

    def overclip_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 21.0,
        }

    overclip = V72P2.run_block(
        **_run_block_kwargs(indptr, indices, checkpoints=(160,), decoder=overclip_decoder, total=1)
    )
    assert overclip["status"] == "NUMERIC_FAILURE"
    assert overclip["iterations_used"] == 1
    assert overclip["per_checkpoint"][0]["iterations"] == 1
    assert overclip["per_checkpoint"][0]["iterations_known"] is True


def test_T1_E_frame_grouping_validation_and_cal_prior():
    frame_ids = list(range(1726, 1762))
    frame = pd.DataFrame(
        {
            "frame_id": np.repeat(frame_ids, 256),
            "pair_idx": np.tile(np.arange(256), len(frame_ids)),
            "alice_symbol": np.tile(np.arange(256), len(frame_ids)),
            "bob_symbol": np.tile(np.arange(256), len(frame_ids)),
        }
    )
    valid, errors = V72P2.validate_selected_frames(frame, frame_ids)
    assert not errors and len(valid) == 36
    groups = [frame_ids[offset : offset + 4] for offset in range(0, 36, 4)]
    alice, bob = V72P2.assemble_frame_group(valid, groups[0])
    assert alice.shape == bob.shape == (1024,)
    assert groups[1] == [1730, 1731, 1732, 1733]

    missing = frame.loc[frame.frame_id != 1732].copy()
    missing_valid, missing_errors = V72P2.validate_selected_frames(missing, frame_ids)
    assert 1732 in missing_errors
    assert any(fid not in missing_valid for fid in groups[1])
    with pytest.raises(V72P2.DataValidationError):
        V72P2.assemble_frame_group(
            {fid: value for fid, value in valid.items() if fid != 1732}, groups[1]
        )

    duplicate = frame.copy()
    duplicate.loc[(duplicate.frame_id == 1726) & (duplicate.pair_idx == 1), "pair_idx"] = 0
    _, duplicate_errors = V72P2.validate_selected_frames(duplicate, [1726])
    assert 1726 in duplicate_errors

    probabilities = np.full((1024, 1024), 1.0 / 1024.0, dtype=np.float64)
    probabilities[7, 11] = 0.25
    probabilities[7] /= probabilities[7].sum()
    prior = V72P2.build_prior_logp(np.array([7] + [8] * 1023), probabilities)
    assert prior.dtype == np.float64
    assert np.all(np.isfinite(prior))
    assert np.allclose(np.exp(prior[0]), probabilities[7])

    seen = {}

    def fake_select(a_cal, b_cal):
        seen["a"] = a_cal.copy()
        seen["b"] = b_cal.copy()
        return 3.0, {"3.0": 2.0}, 2.0, False

    old_select = V72P2._V70.select_lambda
    V72P2._V70.select_lambda = fake_select
    try:
        model = V72P2.fit_full_cal_model(
            np.array([1, 2, 3, 4], dtype=np.int32),
            np.array([5, 6, 7, 8], dtype=np.int32),
        )
    finally:
        V72P2._V70.select_lambda = old_select
    assert np.array_equal(seen["a"], np.array([1, 2, 3, 4]))
    assert np.array_equal(seen["b"], np.array([5, 6, 7, 8]))
    assert model["selected_lambda"] == 3.0
    assert model["ce_ref_log2"] == 2.0


def test_T1_F_deadline_partial_output_and_inert_default():
    indptr = np.array([0, 1, 2], dtype=np.int32)
    indices = np.array([0, 1], dtype=np.int32)
    calls = []

    def decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        calls.append(True)
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": True,
            "max_llr": 1.0,
        }

    clock_values = iter([0.0, 0.0, 0.0, 601.0])

    def fake_clock():
        return next(clock_values, 601.0)

    timeout_kwargs = _run_block_kwargs(indptr, indices, checkpoints=(1, 2), decoder=decoder)
    timeout_kwargs["clock"] = fake_clock
    timeout_kwargs["deadline_s"] = 600.0
    timeout = V72P2.run_block(**timeout_kwargs)
    assert timeout["status"] == "TIMEOUT"
    assert timeout["disclosed_rows"] == 1
    assert timeout["tag_bits_published"] == 64
    assert len(calls) == 1

    root = pathlib.Path("workspace") / "v72p2_tests" / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    rows = [V72P2._empty_block(index, [1726 + 4 * index + j for j in range(4)]) for index in range(9)]
    rows[0]["status"] = "LADDER_EXHAUSTED"
    results = V72P2._results_payload(rows, "synthetic stop")
    V72P2._write_outputs(root, {"schema": "test"}, results)
    assert {path.name for path in root.iterdir()} == {
        "manifest.json",
        "results.json",
        "table.csv",
        "report.md",
    }

    existing = root / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        V72P2.execute_real("missing-registry.json", existing)
    inert = root / "inert"
    assert V72P2.main(["--registry", "missing-registry.json", "--out-dir", str(inert)]) == 0
    assert not inert.exists()


def test_T1_F_fake_execute_preserves_partial_nine_slots(monkeypatch):
    cal_ids = list(range(702, 1726))
    groups = [list(range(1726 + 4 * i, 1730 + 4 * i)) for i in range(9)]
    selected_ids = cal_ids + [fid for group in groups for fid in group]
    session = {
        "session_id": "20260123_1M_600k_0dB",
        "source_label": "1M",
        "provenance": "fake.parquet",
        "stage2_CAL_frame_ids": cal_ids,
        "stage2_VAL_frame_ids": list(range(1726, 1982)),
    }
    registry = {"schema": "v71_data_v1", "data_sha": "84d62779", "sessions": [session]}
    fake_frame = pd.DataFrame({"frame_id": selected_ids})
    monkeypatch.setattr(V72P2, "_git_head", lambda: "a" * 40)
    monkeypatch.setattr(
        V72P2,
        "load_registry",
        lambda path: (registry, pathlib.Path("v71_data_registry.json").resolve()),
    )
    monkeypatch.setattr(
        V72P2,
        "read_selected_pairs",
        lambda path, ids: (fake_frame, "fake_predicate"),
    )

    def fake_validate(frame, ids):
        return {
            int(fid): {
                "alice_symbols": np.zeros(256, dtype=np.int32),
                "bob_symbols": np.zeros(256, dtype=np.int32),
            }
            for fid in ids
        }, {}

    monkeypatch.setattr(V72P2, "validate_selected_frames", fake_validate)
    monkeypatch.setattr(
        V72P2,
        "fit_full_cal_model",
        lambda a, b: {
            "selected_lambda": 3.0,
            "lambda_cv_scores": {"3.0": 2.0},
            "ce_ref_log2": 2.0,
            "ce_ref_definition": "selected CAL-CV; not entropy",
            "probability_floor": 1e-300,
            "Ps_full": np.full((1024, 1024), 1.0 / 1024.0),
        },
    )
    monkeypatch.setattr(
        V72P2,
        "get_mother_csr",
        lambda: (np.arange(9037, dtype=np.int32), np.zeros(9036, dtype=np.int32), 49620),
    )

    def fatal_decoder(prior, target, *, indptr, indices, max_iter, warm_start_c2v):
        return {
            "residuals": [1.0],
            "check_to_variable": np.zeros(len(indices), dtype=np.float64),
            "hard_bits": _bits(),
            "syndrome_observed": target.copy(),
            "finite": False,
            "max_llr": 0.0,
            "app_llr": np.zeros(10240, dtype=np.float64),
        }

    monkeypatch.setattr(V72P2._ADAPTER, "run_decoder", fatal_decoder)
    out_dir = ROOT / "workspace" / "v72p2_tests" / uuid.uuid4().hex
    rc = V72P2.execute_real(
        "v71_data_registry.json",
        out_dir,
        block_deadline_s=600.0,
        invocation_deadline_s=7200.0,
    )
    assert rc == 1
    assert {path.name for path in out_dir.iterdir()} == {
        "manifest.json",
        "results.json",
        "table.csv",
        "report.md",
    }
    results = __import__("json").loads((out_dir / "results.json").read_text(encoding="utf-8"))
    assert results["assigned_count"] == 9
    assert results["attempted_count"] == 1
    assert results["not_attempted_count"] == 8
    assert results["invalid_input_count"] == 0
    assert results["aggregate"]["all_attempts"]["f_model_relative"] is not None
    assert results["aggregate"]["success_conditional"]["f_model_relative"] is None
    for index in range(1, 9):
        assert results["assigned_blocks"][index]["frame_ids"] == groups[index]
