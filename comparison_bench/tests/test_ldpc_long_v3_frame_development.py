from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from comparison_bench.src.comparison_bench.formal_ir.long_v3_development import ROLE, canonical_development_policy, select_candidate
from comparison_bench.src.comparison_bench.formal_ir.long_v3_frame_development import aggregate_frame_development


def _grid():
    rows = []
    prefixes = ("p050", "p0625", "p075", "p0875")
    for n in (256, 512, 1024):
        for plane in range(10):
            for candidate in range(4):
                for stratum, p_hat in (("p001", .01), ("p002", .02)):
                    for index in range(16):
                        terminal = prefixes[(plane + candidate + index) % 4]
                        rows.append({"n": n, "plane_id": plane, "candidate_id": candidate, "stratum_id": stratum,
                                     "frame_id": f"dev_n{n}_plane{plane:02d}_{stratum}_f{index:02d}", "attempted": True,
                                     "status": "development_exact_success", "terminal_prefix_id": terminal,
                                     "rounds_attempted": prefixes.index(terminal) + 1, "syndrome_bits_disclosed": n * (prefixes.index(terminal) + 4) // 8,
                                     "exact_match": True, "policy_id": canonical_development_policy(n)["policy_id"], "p_hat": p_hat,
                                     "backend_identity": "ldpc==2.4.1", "runtime_s": 0.0, "role": ROLE,
                                     "source_sha256": "pending"})
    from comparison_bench.src.comparison_bench.formal_ir.long_v3_development import generate_sacrificed_development
    for row in rows:
        source = generate_sacrificed_development(row["n"], row["plane_id"], .01 if row["stratum_id"] == "p001" else .02)
        row["source_sha256"] = source["source_sha256"]
        row["p_hat"] = source["p_hat"]
    selections = [select_candidate([r for r in rows if r["n"] == n and r["plane_id"] == plane]) for n in (256, 512, 1024) for plane in range(10)]
    return rows, selections


def _selections(rows):
    return [select_candidate([r for r in rows if r["n"] == n and r["plane_id"] == plane]) for n in (256, 512, 1024) for plane in range(10)]


def _set_terminal(rows, n, stratum, prefix):
    prefixes = ("p050", "p0625", "p075", "p0875")
    for row in rows:
        if row["n"] == n and row["stratum_id"] == stratum:
            row.update(terminal_prefix_id=prefix, rounds_attempted=prefixes.index(prefix) + 1,
                       syndrome_bits_disclosed=n * (prefixes.index(prefix) + 4) // 8)


def _independent_tuple(result, n):
    item = result["length_aggregates"][str(n)]
    successes = item["successes_by_stratum"]
    return [-min(successes.values()), -sum(successes.values()),
            item["worst_stratum_mean_key_disclosure_per_input_bit"],
            item["overall_mean_key_disclosure_per_input_bit"], n]


class FrameDevelopmentV3Test(unittest.TestCase):
    def test_global_stopping_accounting_hash_and_no_writes(self):
        rows, selections = _grid(); before = sorted(p.name for p in Path.cwd().iterdir())
        with patch("builtins.open", side_effect=AssertionError("write")), patch.object(Path, "open", side_effect=AssertionError("write")):
            result = aggregate_frame_development(rows, selections)
        self.assertEqual(sorted(p.name for p in Path.cwd().iterdir()), before)
        self.assertEqual((result["role"], result["plane_count"], result["frame_outcome_count"]), ("sacrificed_frame_development_only", 10, 96))
        frame = result["frame_outcomes"][0]
        self.assertEqual(frame["global_rounds_attempted"], 4)
        self.assertEqual((frame["syndrome_bits_disclosed"], frame["verification_tag_bits"], frame["key_dependent_disclosure_bits_total"]), (2240, 64, 2304))
        self.assertEqual(frame["epsilon_ec_union_bound"], 4 * 2.0 ** -64)
        self.assertEqual(set(result), {"role", "stopping_model", "plane_count", "verification_tag_bits", "tag_reuse_max_checks", "frame_outcome_count", "frame_outcomes", "length_aggregates", "selected_length", "length_selection_tuple", "aggregation_sha256"})
        self.assertEqual([set(item) for item in result["frame_outcomes"]], [{"n", "stratum_id", "frame_index", "selected_candidate_ids", "plane_terminal_prefix_ids", "plane_rounds_attempted", "status", "global_terminal_prefix_id", "global_rounds_attempted", "input_bits", "syndrome_bits_disclosed", "verification_tag_bits", "key_dependent_disclosure_bits_total", "public_toeplitz_seed_bits", "epsilon_ec_union_bound", "key_disclosure_per_input_bit"}] * 96)
        self.assertEqual([set(item) for item in result["length_aggregates"].values()], [{"successes_by_stratum", "terminal_prefix_counts_by_stratum", "mean_key_disclosure_per_input_bit_by_stratum", "worst_stratum_mean_key_disclosure_per_input_bit", "overall_mean_key_disclosure_per_input_bit"}] * 3)
        self.assertEqual([(x["n"], x["stratum_id"], x["frame_index"]) for x in result["frame_outcomes"]], [(n, s, i) for n in (256, 512, 1024) for s in ("p001", "p002") for i in range(16)])
        base = {key: value for key, value in result.items() if key != "aggregation_sha256"}
        self.assertEqual(result["aggregation_sha256"], hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest())

    def test_failure_retained_and_length_tuple_priority(self):
        rows, selections = _grid()
        for row in rows:
            if row["n"] == 256 and row["plane_id"] == 0 and row["stratum_id"] == "p001" and row["frame_id"].endswith("00"):
                row.update(status="development_decode_failed", terminal_prefix_id="p0875", rounds_attempted=4, syndrome_bits_disclosed=224, exact_match=False)
        selections = _selections(rows)
        result = aggregate_frame_development(rows, selections)
        failed = next(x for x in result["frame_outcomes"] if x["n"] == 256 and x["stratum_id"] == "p001" and x["frame_index"] == 0)
        self.assertEqual((failed["status"], failed["verification_tag_bits"], failed["public_toeplitz_seed_bits"]), ("development_frame_failed", 64, 2623))
        self.assertEqual(result["length_selection_tuple"], _independent_tuple(result, result["selected_length"]))

    def test_zero_round_failure_and_length_tuple_priority(self):
        rows, _ = _grid()
        for row in rows:
            if row["n"] == 256 and row["stratum_id"] == "p001" and row["frame_id"].endswith("00"):
                row.update(attempted=False, status="development_backend_unavailable", terminal_prefix_id="", rounds_attempted=0, syndrome_bits_disclosed=0, exact_match=False)
        result = aggregate_frame_development(rows, _selections(rows))
        zero = next(x for x in result["frame_outcomes"] if (x["n"], x["stratum_id"], x["frame_index"]) == (256, "p001", 0))
        self.assertEqual((zero["status"], zero["global_rounds_attempted"], zero["global_terminal_prefix_id"], zero["syndrome_bits_disclosed"], zero["verification_tag_bits"], zero["key_dependent_disclosure_bits_total"], zero["public_toeplitz_seed_bits"], zero["epsilon_ec_union_bound"]), ("development_frame_failed", 0, "", 0, 0, 0, 0, 0.0))
        rows, _ = _grid(); _set_terminal(rows, 256, "p001", "p050"); _set_terminal(rows, 256, "p002", "p050")
        for row in rows:
            if row["n"] in (256, 1024) and row["plane_id"] == 0 and row["stratum_id"] == "p001" and row["frame_id"].endswith("00"):
                row.update(status="development_decode_failed", terminal_prefix_id="p0875", rounds_attempted=4, syndrome_bits_disclosed=row["n"] * 7 // 8, exact_match=False)
        _set_terminal(rows, 512, "p001", "p0875"); _set_terminal(rows, 512, "p002", "p0875")
        result = aggregate_frame_development(rows, _selections(rows))
        self.assertEqual(result["selected_length"], 512)  # 32 successes beats the lower-leakage 31-success lengths.
        self.assertEqual(result["length_selection_tuple"], min(_independent_tuple(result, n) for n in (256, 512, 1024)))
        rows, _ = _grid(); _set_terminal(rows, 256, "p001", "p050"); _set_terminal(rows, 256, "p002", "p0875")
        _set_terminal(rows, 512, "p001", "p0625"); _set_terminal(rows, 512, "p002", "p0625")
        _set_terminal(rows, 1024, "p001", "p0875"); _set_terminal(rows, 1024, "p002", "p0875")
        result = aggregate_frame_development(rows, _selections(rows))
        self.assertEqual(result["selected_length"], 512)  # All succeed; lower worst-stratum leakage wins.
        self.assertEqual(result["length_selection_tuple"], min(_independent_tuple(result, n) for n in (256, 512, 1024)))

    def test_rejects_malformed_rows_and_selections(self):
        rows, selections = _grid()
        for mutate in (
            lambda r, s: r.pop(),
            lambda r, s: r[0].__setitem__("runtime_s", -1.0),
            lambda r, s: r[0].__setitem__("backend_identity", "test_injected"),
            lambda r, s: r[0].__setitem__("role", "wrong"),
            lambda r, s: r[0].__setitem__("source_sha256", "0" * 64),
            lambda r, s: r[0].__setitem__("p_hat", .03),
            lambda r, s: r[0].__setitem__("policy_id", "bad"),
            lambda r, s: r[0].update(terminal_prefix_id="p050", rounds_attempted=4),
            lambda r, s: r[0].__setitem__("frame_id", r[1]["frame_id"]),
            lambda r, s: s[0].__setitem__("selected_candidate_id", 3),
            lambda r, s: s[1].update(s[0]),
            lambda r, s: s[0].__setitem__("selection_sha256", "0" * 64),
        ):
            bad_rows, bad_selections = copy.deepcopy(rows), copy.deepcopy(selections); mutate(bad_rows, bad_selections)
            with self.assertRaises(ValueError): aggregate_frame_development(bad_rows, bad_selections)
