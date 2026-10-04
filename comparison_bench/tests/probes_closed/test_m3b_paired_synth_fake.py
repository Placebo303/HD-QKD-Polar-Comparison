import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import m3b_paired_synth as m3b
from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1


def _artifact(arm="M3B-R1"):
    spec = m3b.ARMS[arm]
    base = []
    for variable in range(1024):
        base.append([variable % 200, variable, variable % 31 + 1])
        base.append([(variable + 73) % 200, variable,
                     (variable + 9) % 31 + 1])
    added = []
    for offset, row in enumerate(range(200, 208)):
        for variable in range(offset * 10, offset * 10 + 10):
            added.append([row, variable, (variable + 15) % 31 + 1])
    return {
        "status": "ok",
        "arm": spec["index"],
        "base_seed": spec["construction_seed"],
        "extension_seed": spec["extension_seed"],
        "n": 1024,
        "m_base": 200,
        "m": 208,
        "base_rank": 200,
        "rank": 208,
        "base_four_cycles": 0,
        "four_cycles": 0,
        "base_prefix_unchanged": True,
        "base_variable_degree_histogram": {"2": 1024},
        "added_row_degrees": [10] * 8,
        "twice_identical": True,
        "min_girth": 6,
        "base_triples": base,
        "added_triples": added,
        "triples": base + added,
    }


def _comparator(arm="M3B-R1"):
    spec = m3b.ARMS[arm]
    rows = []
    for idx, seed in enumerate(m3b.FRAME_SEEDS):
        failed = int(idx == 1)
        rows.append({"block_idx": idx, "seed": seed, "stage": "stage1",
                     "failed": failed, "undetected": 0})
        if failed:
            rows.append({"block_idx": idx, "seed": seed,
                         "stage": "stage2-rescue", "failed": 0,
                         "undetected": 0})
    return {"summary": {"verdict": "COMPLETE", "arm": spec["p1_arm"],
                         "construct_instance": spec["construction_seed"]},
            "rows": rows}


def _read_for(arm):
    graph = _artifact(arm)
    comparator = _comparator(arm)
    spec = m3b.ARMS[arm]

    def read(path):
        path = Path(path)
        if path.name.endswith(".json") and "P1_STAGE1" in str(path):
            return copy.deepcopy(comparator)
        assert path == spec["graph"]
        return copy.deepcopy(graph)

    return read


def test_frozen_arm_mapping_and_graph_pins():
    assert m3b.ARMS["M3B-R1"]["graph"].as_posix().endswith("arm1.json")
    assert m3b.ARMS["M3B-R2"]["graph"].as_posix().endswith("arm2.json")
    assert m3b.ARMS["M3B-R1"]["comparator"].as_posix().endswith(
        "P1S1-R1_ef7da79b/rows.json")
    assert m3b.ARMS["M3B-R2"]["comparator"].as_posix().endswith(
        "P1S1-R2_22754019/rows.json")
    pins = m3b.validate_graph_artifact(_artifact("M3B-R2"), "M3B-R2")
    assert pins["construction_seed"] == 2026092011
    assert pins["extension_seed"] == 2026096811
    assert pins["triple_count"] == 2128
    with pytest.raises(m3b.M3BError, match="base prefix"):
        broken = _artifact()
        broken["triples"][0], broken["triples"][-1] = (
            broken["triples"][-1], broken["triples"][0])
        m3b.validate_graph_artifact(broken, "M3B-R1")


@pytest.mark.parametrize("flags", [
    ["--execute-synthetic"],
    ["--execution-authorized"],
])
def test_execution_requires_both_flags_before_reads(monkeypatch, flags, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("a pre-gate read or bind occurred")

    monkeypatch.setattr(m3b, "read_json", forbidden)
    monkeypatch.setattr(p1.s2c, "bind_empirical_bundle", forbidden)
    rc = m3b.main(flags + ["--arm", "M3B-R1", "--root",
                          "workspace/m3b_nested_paired_20260926/P1S1-R1_test"])
    assert rc == 2
    assert "require both" in capsys.readouterr().err


def test_dry_mode_has_zero_file_and_production_calls(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry mode must not read or bind production inputs")

    monkeypatch.setattr(m3b, "read_json", forbidden)
    monkeypatch.setattr(p1.s2c, "bind_empirical_bundle", forbidden)
    assert m3b.main(["--dry"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["graph_reads"] == 0
    assert result["decoder_calls"] == 0


def test_failed_rescue_is_charged_and_persisted_provenance_is_truthful(
        tmp_path, monkeypatch):
    load_count = {"graph": 0}
    read = _read_for("M3B-R1")

    def counted_read(path):
        if Path(path) == m3b.ARMS["M3B-R1"]["graph"]:
            load_count["graph"] += 1
        return read(path)

    monkeypatch.setattr(p1.peg, "sparse_to_dense",
                        lambda triples, n, m, field: np.zeros((m, n), dtype=np.uint8))
    decode_calls = []
    rescue_calls = []
    failed_seed = m3b.FRAME_SEEDS[0]

    def decode(construction, seed):
        decode_calls.append((construction["m"], seed))
        failed = seed == failed_seed
        return {"exact_match": not failed, "reconstruction_ok": failed,
                "iterations": 4, "prior_entropy_bits": 0.5,
                "u1_mismatches": int(failed), "status": "fake"}

    def rescue(construction, seed):
        rescue_calls.append((construction["m"], seed))
        return {"exact_match": False, "reconstruction_ok": False,
                "iterations": 5, "prior_entropy_bits": 0.5,
                "u1_mismatches": 1, "status": "fake-failed-rescue"}

    prefix = str(tmp_path) + os.sep
    root = str(tmp_path / "P1S1-R1_fake")
    summary = m3b.run_m3b_arm(
        arm="M3B-R1", root=root, decode_fn=decode,
        rescue_decode_fn=rescue, rank_fn=lambda rows: 200,
        read=counted_read, root_prefix=prefix, rss_fn=lambda: 0)

    assert len(decode_calls) == 240
    assert rescue_calls == [(208, failed_seed)]
    assert load_count["graph"] == 2
    assert summary["verdict"] == "COMPLETE"
    assert summary["attempted"] == 1
    assert summary["rescued"] == 0
    assert summary["rescue_disclosure_bits"] == 40
    expected_e = 1064 + 40 / 240
    expected_f_exp = expected_e / 852.544
    assert summary["e_leak"] == pytest.approx(expected_e)
    assert summary["f_exp"] == pytest.approx(expected_f_exp)
    assert summary["f_eff"] == pytest.approx(expected_f_exp + 4.785675 / 240)
    assert summary["undetected_stage1"] == 1
    assert summary["undetected_stage2"] == 0
    assert summary["paired_frame_transitions"]["matched_frame_count"] == 240
    assert summary["paired_frame_transitions"]["transitions"][
        "old_success_new_failure"] == 1
    assert summary["graph_provenance"]["stored_artifact_loaded_twice"] is True
    assert summary["graph_provenance"]["m3a_twice_identical"] is True
    assert summary["graph_provenance"]["m3a_twice_identical_is_upstream_fact"] is True
    assert summary["graph_provenance"]["m3b_new_peg_constructions"] == 0
    assert summary["graph_label"] == "M3-b nested A200+8 stored graph"

    saved = json.loads((Path(root) / "rows.json").read_text(encoding="utf-8"))
    markdown = (Path(root) / "M3B_RESULT_M3B-R1.md").read_text(encoding="utf-8")
    assert saved["summary"]["rescue_disclosure_bits"] == 40
    assert saved["summary"]["attempted"] == 1
    assert saved["summary"]["rescued"] == 0
    assert "stored_artifact_loaded_twice" in json.dumps(saved)
    assert "upstream M3-a twice-identical" in markdown
    assert "M3-b nested A200+8" in markdown
    assert "A208" not in json.dumps(saved)
    assert "A208" not in markdown
    assert (Path(root) / "block_accounting.csv").exists()


def test_root_and_comparator_pins_refuse_before_decoder(tmp_path):
    called = {"read": 0, "decode": 0, "write": 0}

    def read(path):
        called["read"] += 1
        raise AssertionError("escaped root must be rejected before reads")

    def decode(*args):
        called["decode"] += 1

    def writer(*args):
        called["write"] += 1

    escaped = "workspace/m3b_nested_paired_20260926/../P1_STAGE1/P1S1-R1_new"
    with pytest.raises(m3b.M3BError, match="direct child"):
        m3b.run_m3b_arm(
            arm="M3B-R1", root=escaped, decode_fn=decode,
            rescue_decode_fn=decode, rank_fn=lambda rows: 200,
            read=read, writer=writer,
            root_prefix="workspace/m3b_nested_paired_20260926/")
    assert called == {"read": 0, "decode": 0, "write": 0}

    with pytest.raises(p1.Refusal):
        p1._check_root(
            escaped, "P1S1-R1",
            root_prefix="workspace/m3b_nested_paired_20260926/")


def test_default_m3b_root_family_is_frozen():
    assert m3b.M3B_ROOT_PREFIX == "workspace/m3b_nested_paired_20260926/"
    m3b._check_output_root(
        "workspace/m3b_nested_paired_20260926/P1S1-R2_test",
        "M3B-R2", m3b.M3B_ROOT_PREFIX)
