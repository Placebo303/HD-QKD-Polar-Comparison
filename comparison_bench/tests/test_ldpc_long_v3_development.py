from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.long_v3_development import (
    canonical_development_policy, evaluate_candidate, generate_sacrificed_development, select_candidate,
)
from comparison_bench.src.comparison_bench.formal_ir.codebook_long_v3 import generate_master


class _ExactDecoder:
    def __init__(self, h, **kwargs): self.h = h; self.kwargs = kwargs
    def decode(self, delta): return np.zeros(self.h.shape[1], dtype=np.uint8)


class _RaisingDecoder(_ExactDecoder):
    def decode(self, delta): raise RuntimeError("test")


class _CaptureDecoder(_ExactDecoder):
    kwargs_seen: list[dict] = []
    def __init__(self, h, **kwargs): super().__init__(h, **kwargs); self.__class__.kwargs_seen.append(kwargs)


class _WrongLengthDecoder(_ExactDecoder):
    def decode(self, delta): return np.zeros(self.h.shape[1] - 1, dtype=np.uint8)


class _NonbinaryDecoder(_ExactDecoder):
    def decode(self, delta): return np.full(self.h.shape[1], 2, dtype=np.uint8)


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class DevelopmentV3Test(unittest.TestCase):
    def test_generation_policy_and_backend_unavailable(self):
        data = generate_sacrificed_development(256, 0, .01)
        self.assertEqual(data["role"], "sacrificed_development_only")
        self.assertEqual(data["frame_ids"][0], "dev_n256_plane00_p001_f00")
        self.assertEqual(len(data["alice_seed_hex"]), 32)
        domain = {"construction_id": "binary_ldpc_protograph_accumulator_candidate_v3", "construction_version": "1",
                  "role": "sacrificed_development_only", "n": 256, "plane_id": 0, "p": "p001", "frame_count": 16}
        seeds = {}
        for kind in ("alice", "noise"):
            raw = hashlib.sha256(_compact({**domain, "kind": kind})).digest()[:16]
            seeds[kind] = int.from_bytes(raw, "big")
            self.assertEqual(data[f"{kind}_seed_hex"], raw.hex())
            self.assertEqual(data[f"{kind}_seed_id"], hashlib.sha256(raw).hexdigest())
        alice = np.random.Generator(np.random.PCG64(seeds["alice"])).integers(0, 2, size=(16, 256), dtype=np.uint8)
        noise = (np.random.Generator(np.random.PCG64(seeds["noise"])).random(size=(16, 256)) < .01).astype(np.uint8)
        self.assertTrue(np.array_equal(data["alice_frames"], alice)); self.assertTrue(np.array_equal(data["bob_frames"], alice ^ noise))
        self.assertEqual((data["error_count"], data["total_bits"], data["p_hat"]), (int(noise.sum()), 4096, noise.sum() / 4096))
        metadata = {key: data[key] for key in ("role", "n", "plane_id", "p", "p_id", "frame_count", "frame_ids", "alice_seed_hex", "alice_seed_id", "noise_seed_hex", "noise_seed_id", "error_count", "total_bits", "p_hat")}
        self.assertEqual(data["source_sha256"], hashlib.sha256(_compact(metadata) + b"\nALICE\n" + alice.tobytes(order="C") + b"\nBOB\n" + (alice ^ noise).tobytes(order="C")).hexdigest())
        policy = canonical_development_policy(256); self.assertEqual(len(policy["serial_schedule_order"]), 256)
        with patch("comparison_bench.src.comparison_bench.formal_ir.long_v3_development.importlib.metadata.version", return_value="mismatch"):
            rows = evaluate_candidate(data["alice_frames"], data["bob_frames"], n=256, plane_id=0, candidate_id=0,
                                      p_hat=data["p_hat"], stratum_id="p001", frame_ids=data["frame_ids"], decoder_factory=None)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all((not row["attempted"] and row["status"] == "development_backend_unavailable" and row["terminal_prefix_id"] == "" and row["rounds_attempted"] == 0 and row["syndrome_bits_disclosed"] == 0 and not row["exact_match"]) for row in rows))
        root = Path.cwd(); before = sorted(item.name for item in root.iterdir())
        with patch("builtins.open", side_effect=AssertionError("write")), patch.object(Path, "open", side_effect=AssertionError("write")):
            self.assertEqual(generate_sacrificed_development(256, 1, .02)["role"], "sacrificed_development_only")
        self.assertEqual(sorted(item.name for item in root.iterdir()), before)

    def test_decoder_kwargs_early_success_and_bad_output_inputs(self):
        data = generate_sacrificed_development(256, 0, .01); _CaptureDecoder.kwargs_seen = []
        rows = evaluate_candidate(data["alice_frames"], data["alice_frames"], n=256, plane_id=0, candidate_id=0,
                                  p_hat=0.0, stratum_id="p001", frame_ids=data["frame_ids"], decoder_factory=_CaptureDecoder)
        expected = {"error_rate": 1e-4, "max_iter": 50, "bp_method": "minimum_sum", "ms_scaling_factor": 1.0,
                    "schedule": "serial", "omp_thread_count": 1, "serial_schedule_order": list(range(256)), "osd_method": "OSD_0", "osd_order": 0}
        self.assertEqual(_CaptureDecoder.kwargs_seen[0], expected)
        self.assertTrue(all((row["status"], row["terminal_prefix_id"], row["rounds_attempted"], row["syndrome_bits_disclosed"], row["exact_match"]) == ("development_exact_success", "p050", 1, 128, True) for row in rows))
        for decoder in (_WrongLengthDecoder, _NonbinaryDecoder):
            bad = evaluate_candidate(data["alice_frames"], data["alice_frames"], n=256, plane_id=0, candidate_id=0,
                                     p_hat=.01, stratum_id="p001", frame_ids=data["frame_ids"], decoder_factory=decoder)
            self.assertTrue(all(row["status"] == "development_decoder_error" for row in bad))
        with self.assertRaises(ValueError): evaluate_candidate(data["alice_frames"].astype(np.int64), data["bob_frames"], n=256, plane_id=0, candidate_id=0, p_hat=.01, stratum_id="p001", frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder)

    def test_injected_decoder_selection_and_validation(self):
        data1 = generate_sacrificed_development(256, 0, .01)
        data2 = generate_sacrificed_development(256, 0, .02)
        all_rows = []
        for candidate in range(4):
            for data, stratum in ((data1, "p001"), (data2, "p002")):
                all_rows.extend(evaluate_candidate(data["alice_frames"], data["alice_frames"], n=256, plane_id=0,
                    candidate_id=candidate, p_hat=data["p_hat"], stratum_id=stratum, frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder))
        selection = select_candidate(all_rows)
        self.assertEqual(selection["selected_candidate_id"], 0)
        self.assertEqual(selection["selection_tuple"], [-16, -32, 4096, 0])
        policy_base = {key: value for key, value in canonical_development_policy(256).items() if key != "policy_id"}
        self.assertEqual(canonical_development_policy(256)["policy_id"], hashlib.sha256(_compact(policy_base)).hexdigest())
        selection_base = {key: value for key, value in selection.items() if key != "selection_sha256"}
        self.assertEqual(selection["selection_sha256"], hashlib.sha256(_compact(selection_base)).hexdigest())
        runtime_changed = copy.deepcopy(all_rows)
        for row in runtime_changed: row["runtime_s"] = 999.0
        self.assertEqual(select_candidate(runtime_changed), selection)
        broken = copy.deepcopy(all_rows); broken.pop()
        with self.assertRaises(ValueError): select_candidate(broken)
        for mutate in (
            lambda r: r.__setitem__(0, {**r[0], "frame_id": r[1]["frame_id"]}),
            lambda r: r.__setitem__(0, {**r[0], "p_hat": .03}),
            lambda r: r.__setitem__(0, {**r[0], "attempted": False}),
            lambda r: r.__setitem__(0, {**r[0], "policy_id": "bad"}),
            lambda r: r.__setitem__(0, {**r[0], "n": 999}),
            lambda r: r.__setitem__(0, {**r[0], "plane_id": 99}),
            lambda r: r.__setitem__(0, {**r[0], "syndrome_bits_disclosed": -1}),
            lambda r: r.__setitem__(0, {**r[0], "terminal_prefix_id": "p0625"}),
            lambda r: r.__setitem__(0, {**r[0], "rounds_attempted": True}),
            lambda r: r.__setitem__(0, {**r[0], "exact_match": False}),
            lambda r: r.__setitem__(0, {**r[0], "candidate_id": True}),
        ):
            malformed = copy.deepcopy(all_rows); mutate(malformed)
            with self.assertRaises(ValueError): select_candidate(malformed)
        with self.assertRaises(ValueError): generate_sacrificed_development(256, 0, .03)

    def test_selection_lexicographic_priority(self):
        first = generate_sacrificed_development(256, 0, .01); second = generate_sacrificed_development(256, 0, .02); rows = []
        for candidate in range(4):
            for data, stratum in ((first, "p001"), (second, "p002")):
                rows.extend(evaluate_candidate(data["alice_frames"], data["alice_frames"], n=256, plane_id=0, candidate_id=candidate, p_hat=data["p_hat"], stratum_id=stratum, frame_ids=data["frame_ids"], decoder_factory=_ExactDecoder))
        def fail(grid, candidate, stratum, index):
            for row in grid:
                if row["candidate_id"] == candidate and row["stratum_id"] == stratum and row["frame_id"].endswith(f"{index:02d}"):
                    row.update(status="development_decode_failed", terminal_prefix_id="p0875", rounds_attempted=4, syndrome_bits_disclosed=224, exact_match=False)
        worst = copy.deepcopy(rows); fail(worst, 0, "p001", 0); fail(worst, 0, "p001", 1); fail(worst, 1, "p001", 0); fail(worst, 1, "p002", 0)
        for candidate in (2, 3):
            fail(worst, candidate, "p001", 0); fail(worst, candidate, "p001", 1); fail(worst, candidate, "p001", 2)
        self.assertEqual(select_candidate(worst)["selected_candidate_id"], 1)
        total = copy.deepcopy(rows); fail(total, 1, "p001", 0); fail(total, 1, "p002", 0); fail(total, 2, "p001", 0)
        for candidate in (0, 3):
            fail(total, candidate, "p001", 0); fail(total, candidate, "p001", 1)
        self.assertEqual(select_candidate(total)["selected_candidate_id"], 2)
        disclosure = copy.deepcopy(rows); fail(disclosure, 0, "p001", 0); fail(disclosure, 0, "p001", 1); fail(disclosure, 1, "p001", 0); fail(disclosure, 1, "p001", 1); fail(disclosure, 2, "p001", 0)
        for row in disclosure:
            if row["candidate_id"] == 2 and row["status"] == "development_exact_success": row.update(terminal_prefix_id="p0875", rounds_attempted=4, syndrome_bits_disclosed=224)
        self.assertEqual(select_candidate(disclosure)["selected_candidate_id"], 3)

    def test_incremental_continuation_and_failure_statuses(self):
        n = 256; ids = [f"dev_n{n}_plane00_p001_f{i:02d}" for i in range(16)]
        alice = np.zeros((16, n), dtype=np.uint8)
        # A nonzero codeword of the full master is syndrome-consistent at every prefix.
        master = generate_master(n, 0, 0); bob = np.zeros_like(alice); pivot = np.zeros(master.shape[0], dtype=np.uint8)
        for row in range(master.shape[0] - 1, -1, -1):
            pivot[row] = (master[row, n - 1] ^ (master[row, row + 1:master.shape[0]] @ pivot[row + 1:] % 2))
        bob[:, :master.shape[0]] = pivot; bob[:, n - 1] = 1
        rows = evaluate_candidate(alice, bob, n=n, plane_id=0, candidate_id=0, p_hat=.01,
                                  stratum_id="p001", frame_ids=ids, decoder_factory=_ExactDecoder)
        self.assertTrue(all(row["status"] == "development_decode_failed" for row in rows))
        self.assertTrue(all((row["rounds_attempted"], row["terminal_prefix_id"], row["syndrome_bits_disclosed"]) == (4, "p0875", 224) for row in rows))
        bad_bob = np.zeros_like(alice); bad_bob[:, 0] = 1
        inconsistent = evaluate_candidate(alice, bad_bob, n=n, plane_id=0, candidate_id=0, p_hat=.01,
                                          stratum_id="p001", frame_ids=ids, decoder_factory=_ExactDecoder)
        self.assertTrue(all(row["status"] == "development_syndrome_inconsistent" for row in inconsistent))
        errors = evaluate_candidate(alice, bad_bob, n=n, plane_id=0, candidate_id=0, p_hat=.01,
                                    stratum_id="p001", frame_ids=ids, decoder_factory=_RaisingDecoder)
        self.assertTrue(all(row["status"] == "development_decoder_error" for row in errors))
