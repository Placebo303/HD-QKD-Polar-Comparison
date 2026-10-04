"""Fake-only contract tests for M3-c; never read data or call production decoders."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import m0_realframe_runner as m0
from comparison_bench.src.comparison_bench.cli.probes_closed import m3b_paired_synth as m3b
from comparison_bench.src.comparison_bench.cli.probes_closed import m3c_real_u2 as m3c


def _fake_series() -> dict:
    a = np.zeros(m3c.N_PAIRS_EVAL, dtype=np.int16)
    b = a.copy()
    for index in range(m3c.N_FRAMES):
        start = index * m3c.N
        stop = start + m3c.N
        a[start:stop] = index
        b[start:stop] = index
    # Give frame 1 observable raw/u2 symbol errors without reading source data.
    b[m3c.N:2 * m3c.N] = 0
    return {
        "a": a,
        "b": b,
        "dataset": m3c.DATASET,
        "ttbin": "/fake/Type2_2M_3s_2026-01-21_183657.ttbin",
        "offset_ps": 50,
        "n_pairs_total": m3c.N_PAIRS_TOTAL,
        "n_pairs_eval": m3c.N_PAIRS_EVAL,
        "eval_first_frame": m3c.EVAL_FIRST_FRAME,
    }


def _fake_bundle() -> dict:
    return {
        "source": m3c.SOURCE,
        "path": str(m3c.PRIOR_PATH),
        "g1": np.zeros((32, 1024), dtype=np.float32),
        "g2": np.zeros((32, 32, 1024), dtype=np.float32),
        "p_b": np.full(1024, 1 / 1024, dtype=np.float32),
    }


def _fake_graph(arm: str = "M3C-R1") -> dict:
    graph_arm = "M3B-R1" if arm == "M3C-R1" else "M3B-R2"
    spec = m3b.ARMS[graph_arm]
    base = []
    for variable in range(1024):
        first = variable % 200
        base.append([first, variable, 1])
        base.append([(first + 1) % 200, variable, 1])
    added = [[row, variable, 2]
             for row in range(200, 208)
             for variable in range((row - 200) * 10, (row - 199) * 10)]
    return {
        "status": "ok",
        "arm": spec["index"],
        "base_seed": spec["construction_seed"],
        "construction_seed": spec["construction_seed"],
        "extension_seed": spec["extension_seed"],
        "n": 1024,
        "m_base": 200,
        "m": 208,
        "base_rank": 200,
        "rank": 208,
        "base_four_cycles": 0,
        "four_cycles": 0,
        "base_prefix_unchanged": True,
        "twice_identical": True,
        "base_triples": base,
        "added_triples": added,
        "triples": base + added,
        "added_row_degrees": [10] * 8,
        "base_variable_degree_histogram": {"2": 1024},
    }


def _happy_decode(_state: dict, construction: dict, a: np.ndarray,
                  _b: np.ndarray, _bundle: dict, m: int) -> dict:
    index = int(a[0])
    if m == 200 and index in {1, 2, 3}:
        return {"exact_match": False,
                "reconstruction_ok": index == 1,
                "status": "max_iter", "iterations": 300}
    if m == 200:
        return {"exact_match": True,
                "full10_match": index != 0,
                "reconstruction_ok": True,
                "status": "converged", "iterations": 2}
    assert m == 208 and construction["m"] == 208
    if index == 1:
        return {"exact_match": True, "full10_match": False,
                "reconstruction_ok": True, "status": "converged", "iterations": 1}
    return {"exact_match": False, "reconstruction_ok": index == 2,
            "status": "max_iter", "iterations": 300}


def _run_fake(tmp_path: Path, decode=_happy_decode, *, rss=None,
              root_prefix: Path | None = None, event_fn=None):
    root_prefix = tmp_path / "roots" if root_prefix is None else root_prefix
    root = root_prefix / "R1_fake"
    state = {"clock": 0.0, "rss": 0.1}
    writes: list[dict[str, str]] = []
    calls: list[tuple[int, int]] = []

    def clock() -> float:
        return state["clock"]

    def decoder(construction, a, b, bundle, m):
        calls.append((int(a[0]), m))
        return decode(state, construction, a, b, bundle, m)

    def stat(path):
        return {"path": str(path), "size_bytes": 123,
                "mtime_utc": "2026-09-26T00:00:00Z"}

    def writer(_root, files):
        writes.append(dict(files))

    summary = m3c.run_m3c_arm(
        arm="M3C-R1", root=str(root), root_prefix=str(root_prefix),
        series_fn=lambda _source: _fake_series(),
        bundle_fn=lambda _source: _fake_bundle(),
        graph_fn=lambda _path: _fake_graph(),
        decode_fn=decoder,
        stat_fn=stat,
        rss_fn=(lambda: state["rss"]) if rss is None else lambda: rss(state),
        writer=writer,
        clock=clock,
        event_fn=event_fn,
    )
    return summary, json.loads(writes[-1]["rows.json"]), writes[-1], calls, state


@pytest.mark.parametrize("extra_flags", [[], ["--execute-real"], ["--execution-authorized"]])
def test_two_flags_refuse_before_any_production_reader_or_decoder(monkeypatch, capsys, extra_flags):
    def forbidden(*_args, **_kwargs):
        pytest.fail("production M0/M3B I/O or decoder was called")

    monkeypatch.setattr(m0, "load_real_series", forbidden)
    monkeypatch.setattr(m0, "load_bundle", forbidden)
    monkeypatch.setattr(m0, "decode_real", forbidden)
    monkeypatch.setattr(m3b, "read_json", forbidden)
    result = m3c.main(["--arm", "M3C-R1", "--root", "workspace/m3c_fake", *extra_flags])
    assert result == 2
    assert "require both" in capsys.readouterr().err


def test_thread_gate_and_r2_order_block_before_real_input(monkeypatch, tmp_path, capsys):
    def forbidden(*_args, **_kwargs):
        pytest.fail("production M0/M3B I/O or decoder was called")

    monkeypatch.setattr(m3c, "_check_root", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(m3c, "run_m3c_arm", forbidden)
    monkeypatch.setattr(m0, "load_real_series", forbidden)
    monkeypatch.setattr(m0, "load_bundle", forbidden)
    monkeypatch.setattr(m0, "decode_real", forbidden)
    monkeypatch.setattr(m3b, "read_json", forbidden)

    for name in m3c.THREAD_ENV:
        monkeypatch.setenv(name, "1")
    monkeypatch.setenv("NUMBA_NUM_THREADS", "2")
    result = m3c.main(["--arm", "M3C-R1", "--root", "workspace/m3c_fake",
                       "--execute-real", "--execution-authorized"])
    assert result == 2
    assert "thread limits" in capsys.readouterr().err

    monkeypatch.setenv("NUMBA_NUM_THREADS", "1")
    monkeypatch.setitem(m3c.ARMS["M3C-R1"], "root", str(tmp_path / "R1"))
    result = m3c.main(["--arm", "M3C-R2", "--root", "workspace/m3c_fake_r2",
                       "--execute-real", "--execution-authorized"])
    assert result == 2
    assert "R2 requires" in capsys.readouterr().err


def test_root_rules_and_r2_completed_r1_gate(tmp_path):
    prefix = tmp_path / "m3c"
    good = prefix / "R1_fake"
    m3c._check_root(str(good), "M3C-R1", str(prefix))
    with pytest.raises(m3c.M3CError):
        m3c._check_root(str(tmp_path / "elsewhere" / "R1_fake"), "M3C-R1", str(prefix))
    with pytest.raises(m3c.M3CError):
        m3c._check_root(str(prefix / "nested" / "R1_fake"), "M3C-R1", str(prefix))
    with pytest.raises(m3c.M3CError):
        m3c._check_root(str(prefix / "R2_fake"), "M3C-R1", str(prefix))
    protected = tmp_path / "results" / "R1_fake"
    with pytest.raises(m3c.M3CError):
        m3c._check_root(str(protected), "M3C-R1", str(tmp_path / "results"))
    good.mkdir(parents=True)
    with pytest.raises(m3c.M3CError):
        m3c._check_root(str(good), "M3C-R1", str(prefix))

    r1_root = tmp_path / "R1_result"
    with pytest.raises(m3c.M3CError, match="R2 requires"):
        m3c._require_r1_complete(r1_root)
    rows = []
    for index in range(m3c.N_FRAMES):
        rescued = index == 0
        rows.append({"arm": "M3C-R1", "superframe": index,
                     "stage1_exact": not rescued,
                     "stage2_attempted": rescued,
                     "stage2_exact": True if rescued else None,
                     "final_u2_exact": True})
    result = {
        "summary": {"arm": "M3C-R1", "verdict": "COMPLETE",
                    "processed_n": 383, "denominator": 383,
                    "stage2_set_exact": True},
        "rows": rows,
    }
    r1_root.mkdir()
    (r1_root / "rows.json").write_text(json.dumps(result), encoding="utf-8")
    m3c._require_r1_complete(r1_root)
    result["summary"]["verdict"] = "INCOMPLETE-wall"
    (r1_root / "rows.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(m3c.M3CError, match="R2 requires"):
        m3c._require_r1_complete(r1_root)


def test_frozen_series_bundle_and_graph_pins_are_checked():
    series = _fake_series()
    a, b, blocks = m3c._series_frames(series)
    assert (a.size, b.size, len(blocks), a.size - len(blocks) * 1024) == (
        392721, 392721, 383, 529)
    assert blocks[0][0][0] == 0 and blocks[-1][0][0] == 382

    for key, value in (("dataset", "other"), ("offset_ps", 51),
                       ("n_pairs_total", 982181), ("n_pairs_eval", 392720),
                       ("eval_first_frame", 8771981),
                       ("ttbin", "/fake/wrong.ttbin")):
        changed = dict(series)
        changed[key] = value
        with pytest.raises(m3c.M3CError):
            m3c._series_frames(changed)

    bundle = _fake_bundle()
    assert "same-source R1-TRAIN" in m3c._validate_bundle(bundle)
    with pytest.raises(m3c.M3CError):
        m3c._validate_bundle({**bundle, "source": "1M"})
    with pytest.raises(m3c.M3CError):
        m3c._validate_bundle({**bundle, "path": "some-other-prior.npz"})

    graph = _fake_graph()
    base_code, full_code, pins = m3c._graph_codes(graph, "M3C-R1")
    assert (base_code["m"], full_code["m"], len(base_code["triples"]),
            len(full_code["triples"])) == (200, 208, 2048, 2128)
    assert pins["construction_seed"] == 2026092001
    graph = _fake_graph()
    graph["triples"][0] = [0, 1023, 3]
    with pytest.raises(m3b.M3BError):
        m3c._graph_codes(graph, "M3C-R1")


def test_complete_run_records_oracle_rescue_undetected_and_full10_separately(tmp_path):
    summary, saved, files, calls, _state = _run_fake(tmp_path)
    rows = saved["rows"]
    assert summary["verdict"] == "COMPLETE"
    assert summary["processed_n"] == summary["denominator"] == 383
    assert summary["stage1_failures"] == 3
    assert summary["undetected_stage1"] == 1
    assert summary["attempted"] == 3 and summary["rescued"] == 1
    assert summary["undetected_stage2"] == 1
    assert summary["final_failures"] == 2
    assert summary["final_fer"] == pytest.approx(2 / 383)
    assert summary["stage2_set_exact"] is True
    assert summary["oracle_assisted"] is True
    assert summary["full10_evaluated"] == 381
    assert summary["full10_mismatches"] == 2
    assert rows[1]["stage1_undetected"] is True and rows[1]["stage2_exact"] is True
    assert rows[2]["stage2_undetected"] is True and rows[2]["final_u2_exact"] is False
    assert rows[1]["raw_symbol_errors"] == rows[1]["u2_symbol_errors"] == 1024
    assert len(calls) == 386 and [index for index, m in calls if m == 208] == [1, 2, 3]
    assert set(files) == {
        "M3C_RESULT_M3C-R1.md", "rows.json", "block_accounting.csv", "stdout_resource.json"}
    assert "oracle-assisted" in files["M3C_RESULT_M3C-R1.md"]
    assert "no cross-arm decision" in files["M3C_RESULT_M3C-R1.md"]
    assert "f_eff" not in files["rows.json"] and "SKR" not in files["rows.json"]
    assert "tag disclosure" not in files["rows.json"]


def test_incomplete_stage2_error_counts_only_final_dispositions(tmp_path):
    def decode(state, construction, a, b, bundle, m):
        if m == 208 and int(a[0]) == 1:
            raise RuntimeError("fake Stage-2 interruption")
        return _happy_decode(state, construction, a, b, bundle, m)

    summary, saved, files, calls, _state = _run_fake(tmp_path, decode)
    assert summary["verdict"] == "INCOMPLETE-error"
    assert len(saved["rows"]) == 383
    assert summary["processed_n"] == 380
    assert summary["attempted"] == 1
    assert "denominator" not in summary
    assert "final_fer" not in summary
    assert "stage2_set_exact" not in summary
    assert saved["rows"][1]["stage2_attempted"] is True
    assert saved["rows"][1]["stage2_exact"] is None
    assert "no accepted FER/Wilson point" in files["M3C_RESULT_M3C-R1.md"]
    assert [index for index, m in calls if m == 208] == [1]


def test_stage2_over_cap_retains_returned_outcome_but_stops(tmp_path):
    def decode(state, construction, a, b, bundle, m):
        if m == 208 and int(a[0]) == 1:
            state["clock"] += 301.0
        return _happy_decode(state, construction, a, b, bundle, m)

    summary, saved, _files, calls, _state = _run_fake(tmp_path, decode)
    assert summary["verdict"] == "INCOMPLETE-decode-cap"
    assert summary["processed_n"] == 381
    assert len(saved["rows"]) == 383
    assert saved["rows"][1]["stage2_over_cap"] is True
    assert saved["rows"][1]["stage2_exact"] is True
    assert saved["rows"][1]["final_u2_exact"] is True
    assert "final_fer" not in summary
    assert [index for index, m in calls if m == 208] == [1]


def test_hung_decode_is_interrupted_logged_and_stops_without_next_call(monkeypatch, tmp_path):
    monkeypatch.setattr(m3c, "PER_DECODE_CAP_S", 0.05)
    family_root = tmp_path / "family"
    log_path = m3c._prepare_execution_log("M3C-R1", str(family_root))
    calls = []

    def append_event(record):
        fields = {key: value for key, value in record.items()
                  if key not in {"event", "time_utc"}}
        m3c._append_execution_event(log_path, record["event"], **fields)

    def hung_decode(_state, _construction, _a, _b, _bundle, _m):
        calls.append("entered")
        time.sleep(5)
        return {"exact_match": True, "full10_match": True,
                "reconstruction_ok": True, "status": "converged", "iterations": 1}

    started = time.monotonic()
    summary, saved, _files, decoder_calls, _state = _run_fake(
        tmp_path, hung_decode, root_prefix=family_root, event_fn=append_event)
    elapsed = time.monotonic() - started
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

    assert elapsed < 5
    assert calls == ["entered"] and decoder_calls == [(0, 200)]
    assert summary["verdict"] == "INCOMPLETE-decode-cap"
    assert summary["processed_n"] == 0 and "final_fer" not in summary
    assert len(saved["rows"]) == 1
    row = saved["rows"][0]
    assert row["stage1_status"] == "timeout" and row["stage1_over_cap"] is True
    assert row["stage1_exact"] is None and row["stage1_wall_s"] >= 0.04
    assert [record["event"] for record in records] == [
        "ARM_START", "INPUTS_VALIDATED", "DECODE_START", "DECODE_TIMEOUT", "TERMINAL"]
    assert records[0]["wall_cap_s"] == 5400
    assert records[0]["internal_stop_s"] == 5280
    assert records[0]["wall_reserve_s"] == 120
    assert records[-1]["verdict"] == "INCOMPLETE-decode-cap"
    with pytest.raises(FileExistsError):
        m3c._prepare_execution_log("M3C-R1", str(family_root))
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == len(records)
    m3c._prepare_execution_log("M3C-R2", str(family_root))
    after_r2 = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in after_r2[:len(records)]] == [
        record["event"] for record in records]
    assert after_r2[-1]["event"] == "ARM_START" and after_r2[-1]["arm"] == "M3C-R2"


def test_hung_stage2_is_recorded_as_attempted_and_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(m3c, "PER_DECODE_CAP_S", 0.05)
    family_root = tmp_path / "family"
    log_path = m3c._prepare_execution_log("M3C-R1", str(family_root))
    calls = []

    def append_event(record):
        fields = {key: value for key, value in record.items()
                  if key not in {"event", "time_utc"}}
        m3c._append_execution_event(log_path, record["event"], **fields)

    def decode(_state, _construction, a, _b, _bundle, m):
        index = int(a[0])
        calls.append((index, m))
        if m == 200 and index == 0:
            return {"exact_match": False, "full10_match": False,
                    "reconstruction_ok": False, "status": "max_iter", "iterations": 300}
        if m == 208 and index == 0:
            time.sleep(5)
        return {"exact_match": True, "full10_match": True,
                "reconstruction_ok": True, "status": "converged", "iterations": 1}

    started = time.monotonic()
    summary, saved, _files, decoder_calls, _state = _run_fake(
        tmp_path, decode, root_prefix=family_root, event_fn=append_event)
    elapsed = time.monotonic() - started
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    row = saved["rows"][0]

    assert elapsed < 5
    assert summary["verdict"] == "INCOMPLETE-decode-cap"
    assert summary["processed_n"] == 382 and "final_fer" not in summary
    assert row["stage2_attempted"] is True and row["stage2_exact"] is None
    assert row["stage2_status"] == "timeout" and row["stage2_over_cap"] is True
    assert row["stage2_wall_s"] >= 0.04 and row["final_u2_exact"] is None
    assert calls.count((0, 208)) == decoder_calls.count((0, 208)) == 1
    assert records[-2]["event"] == "DECODE_TIMEOUT" and records[-2]["stage"] == 2
    assert records[-1]["event"] == "TERMINAL"


def test_internal_wall_stop_reserves_headroom_and_retains_row(tmp_path):
    events = []

    def rss_at_boundary(state):
        state["rss_checks"] = state.get("rss_checks", 0) + 1
        if state["rss_checks"] == 2:
            state["clock"] = m3c.INTERNAL_STOP_S
        return state["rss"]

    summary, saved, files, calls, _state = _run_fake(
        tmp_path, rss=rss_at_boundary, event_fn=events.append)

    resource = summary["resource"]
    assert summary["verdict"] == "INCOMPLETE-wall"
    assert summary["processed_n"] == 1 and len(saved["rows"]) == 1
    assert calls == [(0, 200)]
    assert resource["wall_cap_s"] == 5400
    assert resource["internal_stop_s"] == 5280
    assert resource["wall_reserve_s"] == 120
    assert json.loads(files["stdout_resource.json"])["resource"] == resource
    assert events[-1]["event"] == "TERMINAL"
    assert events[-1]["wall_cap_s"] == 5400
    assert events[-1]["internal_stop_s"] == 5280
    assert events[-1]["wall_reserve_s"] == 120


def test_wall_and_rss_caps_are_checked_after_each_decode(tmp_path):
    def slow_decode(state, construction, a, b, bundle, m):
        state["clock"] += 299.0
        return {"exact_match": True, "full10_match": True,
                "reconstruction_ok": True, "status": "converged", "iterations": 1}

    summary, saved, _files, calls, _state = _run_fake(tmp_path, slow_decode)
    assert summary["verdict"] == "INCOMPLETE-wall"
    assert summary["processed_n"] == 18
    assert len(saved["rows"]) == 18
    assert len(calls) == 18
    assert "final_fer" not in summary

    def rss_after_first_decode(state):
        return state["rss"]

    def rss_decode(state, construction, a, b, bundle, m):
        state["rss"] = 4.0
        return {"exact_match": True, "full10_match": True,
                "reconstruction_ok": True, "status": "converged", "iterations": 1}

    summary, saved, _files, calls, _state = _run_fake(
        tmp_path / "rss", rss_decode, rss=rss_after_first_decode)
    assert summary["verdict"] == "FAIL(budget-rss)"
    assert summary["processed_n"] == 1
    assert len(saved["rows"]) == 1 and len(calls) == 1
