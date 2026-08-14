from __future__ import annotations

import copy
import hashlib
import json
import unittest
from unittest.mock import patch

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.codebook_v4 import candidate_entry, candidate_manifest
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_development import (
    FRAME_COUNT, ROLE, STRATA, aggregate_frame_development, canonical_development_policy,
    evaluate_candidate, generate_sacrificed_development, select_candidates,
)


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _model():
    counts = {"zero_count": 12403, "plus_one_count": 3865, "minus_one_count": 116}
    total = 16384
    p_plus, p_minus = counts["plus_one_count"] / total, counts["minus_one_count"] / total
    base = {
        "schema": "binary_ldpc_v4_adjacent_channel_v1", "role": "sacrificed_calibration_only",
        "dimension": 1024, "mapping": "gray_msb_first", "frame_len_symbols": 256,
        "calibration_frame_count": 64, "total_count": total, **counts,
        "sign_convention": "signed_modular_alice_minus_bob", "stress_scale": 1.25,
        "probabilities": {"adjacent_nominal": {"plus_one": p_plus, "minus_one": p_minus, "zero": counts["zero_count"] / total},
                          "adjacent_stress_125": {"plus_one": p_plus * 1.25, "minus_one": p_minus * 1.25, "zero": 1 - (p_plus + p_minus) * 1.25}},
        "source_lock_sha256": "1" * 64, "source_manifest_sha256": "2" * 64,
        "selected_frames_sha256": "3" * 64, "calibration_bytes_sha256": "4" * 64,
        "calibration_sha256": "5" * 64, "source_main_ttbin_sha256": "6" * 64,
        "source_chunk_ttbin_sha256": "7" * 64,
    }
    return {**base, "model_sha256": hashlib.sha256(_compact(base)).hexdigest()}


def _grid(model):
    policy = canonical_development_policy()["policy_sha256"]
    rows = []
    for plane in range(10):
        for candidate in range(4):
            entry = candidate_entry(plane, candidate)
            for stratum in STRATA:
                for index in range(FRAME_COUNT):
                    rows.append({"role": ROLE, "stratum_id": stratum, "plane_id": plane,
                                 "candidate_id": candidate, "channel_model_sha256": model["model_sha256"],
                                 "policy_sha256": policy, "matrix_sha256": entry["canonical_bytes_sha256"],
                                 "candidate_valid": entry["valid"], "backend_identity": "ldpc==2.4.1",
                                 "frame_id": f"v4dev_{stratum}_f{index:03d}", "attempted": True,
                                 "status": "development_exact_success", "exact_match": True,
                                 "syndrome_bits_disclosed": (16, 16, 16, 24, 24, 32, 48, 80, 136, 192)[plane], "runtime_s": 0.0})
    return rows


class _ExactDecoder:
    kwargs = []
    def __init__(self, h, **kwargs):
        self.h = h; self.kwargs.append(kwargs)
    def decode(self, syndrome):
        return np.zeros(256, dtype=np.uint8)


class _AdvancingClock:
    def __init__(self): self.value = 0.0
    def __call__(self):
        current = self.value; self.value += 0.1
        return current


class V4DevelopmentTest(unittest.TestCase):
    def test_generator_roots_and_exact_selection_schema(self):
        model = _model()
        nominal = generate_sacrificed_development(model, "adjacent_nominal")
        repeated = generate_sacrificed_development(model, "adjacent_nominal")
        stress = generate_sacrificed_development(model, "adjacent_stress_125")
        self.assertEqual(nominal["frame_ids"][0], "v4dev_adjacent_nominal_f000")
        self.assertEqual(nominal["frame_ids"][-1], "v4dev_adjacent_nominal_f511")
        self.assertTrue(np.array_equal(nominal["bob_frames"], repeated["bob_frames"]))
        self.assertFalse(np.array_equal(nominal["bob_frames"], stress["bob_frames"]))
        rows = _grid(model); binding = select_candidates(rows, model)
        self.assertEqual(set(binding), {"schema", "method_id", "codebook_manifest_sha256", "channel_model_sha256", "plane_selections", "selection_sha256"})
        self.assertEqual((binding["schema"], binding["method_id"], len(binding["plane_selections"])), ("binary_ldpc_v4_selection_v1", "ldpc_formal_v4", 10))
        self.assertEqual(binding["codebook_manifest_sha256"], candidate_manifest()["manifest_sha256"])
        self.assertTrue(all(set(item) == {"plane_id", "candidate_id", "canonical_bytes_sha256", "nominal_successes", "stress_successes", "selection_key"} for item in binding["plane_selections"]))
        self.assertTrue(all(item["selection_key"] == [-512, -1024, item["candidate_id"]] for item in binding["plane_selections"]))
        base = dict(binding); digest = base.pop("selection_sha256")
        self.assertEqual(digest, hashlib.sha256(_compact(base)).hexdigest())

    def test_aggregation_readiness_and_tamper_rejection(self):
        model = _model(); rows = _grid(model); binding = select_candidates(rows, model)
        result = aggregate_frame_development(rows, binding, model)
        self.assertTrue(result["ready_for_synthetic_prepare"])
        self.assertEqual([result["stratum_aggregates"][s]["frame_exact_successes"] for s in STRATA], [512, 512])
        self.assertEqual(len(result["frame_outcomes"]), 1024)
        self.assertEqual(result["frame_outcomes"][0]["syndrome_bits_disclosed"], 584)
        damaged = copy.deepcopy(rows)
        for item in damaged:
            if item["plane_id"] == 0 and item["stratum_id"] == "adjacent_nominal" and int(item["frame_id"][-3:]) < 18:
                item.update(status="development_decode_failed", exact_match=False)
        damaged_binding = select_candidates(damaged, model)
        self.assertFalse(aggregate_frame_development(damaged, damaged_binding, model)["ready_for_synthetic_prepare"])
        with self.assertRaises(ValueError):
            aggregate_frame_development(rows, {**binding, "selection_sha256": "0" * 64}, model)

    def test_decoder_policy_channel_and_malformed_status(self):
        model = _model(); data = generate_sacrificed_development(model, "adjacent_nominal")
        zeros = np.zeros_like(data["bob_frames"])
        _ExactDecoder.kwargs = []
        rows = evaluate_candidate(zeros, zeros, model=model, plane_id=0, candidate_id=0,
                                  stratum="adjacent_nominal", frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder)
        self.assertEqual(len(rows), 512)
        self.assertTrue(all(row["status"] == "development_exact_success" for row in rows))
        self.assertEqual(_ExactDecoder.kwargs[0]["bp_method"], "product_sum")
        self.assertEqual(_ExactDecoder.kwargs[0]["schedule"], "serial")
        self.assertEqual(_ExactDecoder.kwargs[0]["osd_method"], "OSD_0")
        self.assertEqual(_ExactDecoder.kwargs[0]["max_iter"], 50)
        self.assertEqual(_ExactDecoder.kwargs[0]["error_channel"].shape, (256,))
        with self.assertRaises(ValueError):
            evaluate_candidate(zeros[:1], zeros[:1], model=model, plane_id=0, candidate_id=0,
                               stratum="adjacent_nominal", frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder)

    def test_backend_status_distinction_and_post_decode_timeout(self):
        model = _model(); data = generate_sacrificed_development(model, "adjacent_nominal")
        zeros = np.zeros_like(data["bob_frames"])
        with patch("comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_development.importlib.metadata.version", return_value="2.4.0"):
            mismatch = evaluate_candidate(zeros, zeros, model=model, plane_id=0, candidate_id=0,
                                          stratum="adjacent_nominal", frame_ids=data["frame_ids"])
        self.assertTrue(all(row["status"] == "development_backend_mismatch" and not row["attempted"] for row in mismatch))
        with patch("comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_development.importlib.metadata.version", side_effect=__import__("importlib").metadata.PackageNotFoundError("ldpc")):
            unavailable = evaluate_candidate(zeros, zeros, model=model, plane_id=0, candidate_id=0,
                                             stratum="adjacent_nominal", frame_ids=data["frame_ids"])
        self.assertTrue(all(row["status"] == "development_backend_unavailable" and not row["attempted"] for row in unavailable))
        timed = evaluate_candidate(zeros, zeros, model=model, plane_id=0, candidate_id=0,
                                  stratum="adjacent_nominal", frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder,
                                  max_runtime_s=.15, _clock=_AdvancingClock())
        self.assertTrue(all(row["status"] == "development_timeout" and not row["exact_match"] and row["runtime_s"] > .15 for row in timed))
