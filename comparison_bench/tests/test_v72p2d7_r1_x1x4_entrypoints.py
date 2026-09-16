"""D7 R1 X1–X4 entrypoint tests: X1 probe, X3 ladder, X4 G2 bridge.

Fake decoders and fresh temporary roots only. No production decoder, no
Model-F read (injected contexts), no frozen-root creation, no writes outside
pytest temporary directories.
"""

from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = (ROOT / "comparison_bench" / "src" / "comparison_bench"
             / "formal_ir" / "v72p2d7_consistency_multigraph.py")
_SPEC = importlib.util.spec_from_file_location(
    "d7_r1_x1x4_core_test", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)
d5 = mod.d5
d7c = mod.d7c
d7e = mod.d7e

CLI_PATH = ROOT / "scripts" / "v72p2d7_consistency_multigraph.py"
_CSPEC = importlib.util.spec_from_file_location(
    "d7_r1_x1x4_cli_test", str(CLI_PATH))
assert _CSPEC is not None and _CSPEC.loader is not None
cli = importlib.util.module_from_spec(_CSPEC)
_CSPEC.loader.exec_module(cli)

CHECK = "CHECK_UPDATED"
PRIOR_ONLY = "PRIOR_ONLY"
X4_STATE = "X4_COMPLETE_VERIFIED_AWAITING_MAIN_THREAD_ROUTE_DECISION"
X4_GATE = "MAIN_THREAD_ROUTE_DECISION_D7H"
EXECUTED_ROOTS = ("workspace/d7_r1_multigraph_20260913_r1",
                  "workspace/d7_r1_reference_ladder_20260913_r1",
                  "workspace/v72p2d5_g2/20260906_r1")


def _boom(*args, **kwargs):
    raise AssertionError("production path must not be entered")


# --------------------------------------------------------------------------
# T0: constants, help, no production paths
# --------------------------------------------------------------------------
def test_t0_x3_constants_and_claim_ceiling():
    assert mod.X3_X2_ROOT == "workspace/d7_r1_multigraph_20260913_r1"
    assert mod.X3_OUT_ROOT == ("workspace/d7_r1_reference_ladder_"
                               "20260913_r1")
    assert mod.X3_OUT_ROOT_PREFIX == "d7_r1_reference_ladder_"
    assert mod.X3_MAX_SELECTED == 192
    assert mod.X3_LADDER_CALL_CEILING == 576
    assert mod.X3_RECONSTRUCTION_CALL_CEILING == 96
    assert mod.X3_EVIDENCE_FILES == (
        "manifest.json", "selected_records.csv", "ladder_records.csv",
        "paired_summary.csv", "summary.json", "report.md", "command_log.txt")
    assert mod.X3_TERMINAL_NOT_APPLICABLE == \
        "X3_NOT_APPLICABLE_NO_FAILED_CALLS"
    assert mod.X3_TERMINAL_MISMATCH == \
        "X3_BASELINE_REPLAY_MISMATCH_BLOCKED"
    assert mod.X3_CLAIM_LABEL == "STRONG_REFERENCE_DIAGNOSTIC"
    assert mod.X1_PROBE_FAILED_LABEL == "X1_PROVENANCE_PROBE_FAILED"
    assert mod.LADDER_ARM_IDS == ("ROW_LAYERED_90", "ROW_LAYERED_360",
                                  "FLOODING_90")


def test_t0_cli_help_lists_all_modes(capsys):
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--help"])
    out = capsys.readouterr().out
    for flag in ("--dry-run", "--historical-provenance-probe",
                 "--consistency", "--reference-ladder", "--g2",
                 "--x2-root"):
        assert flag in out, flag
    assert "same-input synthetic" in out


def test_t0_cli_rejects_multiple_modes(capsys):
    assert cli.main(["--dry-run", "--consistency"]) == 3
    assert "exactly one mode" in capsys.readouterr().out


# --------------------------------------------------------------------------
# X1: probe record contract and CLI (P01/P02)
# --------------------------------------------------------------------------
def _probe_report(provenance=CHECK, iterations=3, shape_ok=True,
                  finite=True, historical=True):
    return {
        "resolved_is_historical": historical,
        "provenance": provenance,
        "accepted_check_updated": provenance == CHECK,
        "iterations": iterations,
        "belief_shape_ok": shape_ok,
        "beliefs_finite": finite,
        "created_output_root": False,
        "wrote_files": False,
    }


class _ProbeFake:
    def __init__(self, report):
        self.report = dict(report)
        self.calls = []

    def __call__(self, *, decode_fn=None, h=None, prior=None, syndrome=None):
        self.calls.append(decode_fn)
        return dict(self.report)


def test_x1_record_success_contract():
    record = mod.historical_provenance_probe_record(_probe_report())
    assert record["ok"] is True
    assert record["mode"] == "historical_provenance_probe"
    assert record["resolved_decoder_identity"] == "historical_g0_decoder"
    assert record["resolved_is_historical"] is True
    assert record["provenance"] == CHECK
    assert record["accepted_check_updated"] is True
    assert record["iterations"] == 3
    assert record["belief_shape_ok"] is True
    assert record["beliefs_finite"] is True
    assert record["decoder_calls"] == 1
    assert record["writes"] == 0


@pytest.mark.parametrize("report", [
    _probe_report(provenance=PRIOR_ONLY),
    _probe_report(finite=False),
    _probe_report(shape_ok=False),
    _probe_report(iterations=0),
    _probe_report(iterations=None),
    _probe_report(iterations="3"),
])
def test_x1_record_failure_modes_are_not_ok(report):
    record = mod.historical_provenance_probe_record(report)
    assert record["ok"] is False
    assert record["decoder_calls"] == 1
    assert record["writes"] == 0


def test_x1_cli_probe_success_exactly_one_call_no_writes(monkeypatch,
                                                         tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x1_consistency_probe_authorized": True})
    fake = _ProbeFake(_probe_report())
    monkeypatch.setattr(cli._mod.d5, "probe_historical_decoder_provenance",
                        fake)
    assert cli.main(["--historical-provenance-probe"]) == 0
    out = capsys.readouterr()
    payload = json.loads(out.out.strip())
    assert payload["ok"] is True
    assert payload["mode"] == "historical_provenance_probe"
    assert payload["decoder_calls"] == 1
    assert payload["writes"] == 0
    assert fake.calls == [None]  # exactly one call, no injected decoder
    assert list(tmp_path.rglob("*")) == []
    assert out.err == ""


@pytest.mark.parametrize("report", [
    _probe_report(provenance=PRIOR_ONLY),
    _probe_report(finite=False),
    _probe_report(shape_ok=False),
    _probe_report(iterations=0),
])
def test_x1_cli_probe_failure_nonzero_and_label(monkeypatch, capsys, report):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x1_consistency_probe_authorized": True})
    fake = _ProbeFake(report)
    monkeypatch.setattr(cli._mod.d5, "probe_historical_decoder_provenance",
                        fake)
    assert cli.main(["--historical-provenance-probe"]) != 0
    out = capsys.readouterr()
    assert json.loads(out.out.strip())["ok"] is False
    assert mod.X1_PROBE_FAILED_LABEL in out.err
    assert len(fake.calls) == 1


def test_x1_cli_probe_refuses_unauthorized_before_calling(monkeypatch,
                                                          capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x1_consistency_probe_authorized": False})
    monkeypatch.setattr(cli._mod.d5, "probe_historical_decoder_provenance",
                        _boom)
    assert cli.main(["--historical-provenance-probe"]) == 3
    assert "not authorized" in capsys.readouterr().out


def test_x1_probe_fixture_syndrome_is_nonzero_and_consistent():
    fix = d5._probe_fixture()
    assert np.any(fix["syndrome"] != 0)
    assert np.array_equal(fix["syndrome"], np.array([1, 2], dtype=np.int64))
    assert np.array_equal(d5._gf32_syndrome(fix["h"], fix["x_true"]),
                          fix["syndrome"])
    assert np.array_equal(
        d5._load_v35_provenance_module().syndrome_of_gf32(
            fix["h"], fix["x_true"]),
        fix["syndrome"])


def test_x1_probe_fixture_iteration_zero_early_return_cannot_fire():
    fix = d5._probe_fixture()
    start = np.argmax(fix["prior"], axis=1)  # uniform prior -> all-zero word
    assert np.array_equal(start, np.zeros(2, dtype=np.int64))
    assert not np.array_equal(d5._gf32_syndrome(fix["h"], start),
                              fix["syndrome"])
    assert not np.array_equal(
        d5._load_v35_provenance_module().syndrome_of_gf32(fix["h"], start),
        fix["syndrome"])


def test_consistency_is_relabelled_not_x1():
    record = cli._consistency_record({"ok": True, "items": {}})
    assert record["mode"] == "same_input_synthetic_consistency"
    assert "not X1" in record["label"]
    assert cli.build_parser().format_help().count("same-input synthetic") >= 1


def test_consistency_refuses_unauthorized_with_synthetic_wording(monkeypatch,
                                                                 capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x1_consistency_probe_authorized": False})
    assert cli.main(["--consistency"]) == 3
    assert "synthetic consistency" in capsys.readouterr().out


# --------------------------------------------------------------------------
# X3: selector, call plan, guards (P03/P04)
# --------------------------------------------------------------------------
def _frozen_slot_rows():
    return mod.frozen_slots()


def _by_slot(**key):
    for slot in mod.frozen_slots():
        if all(slot[k] == v for k, v in key.items()):
            return slot
    raise KeyError(key)


def _csv_row(slot, *, invoked=True, status="ok", exact=False, finite=True):
    row = {field: "" for field in mod.CALL_RECORD_FIELDS}
    for field in ("slot_idx", "graph_idx", "l1_graph_seed", "l2_graph_seed",
                  "f", "seed", "arm", "role", "layer", "condition", "rows",
                  "n"):
        row[field] = slot[field]
    row.update({"invoked": invoked, "status": status, "exact": exact,
                "syndrome_ok": False, "iterations": 3, "finite": finite,
                "symbol_errors": 64, "unsatisfied_checks": 7,
                "provenance": CHECK, "transfer_eligible": True,
                "transfer_block_reason": "", "wall_s": 0.1, "rss_bytes": 100})
    return row


def test_x3_selector_predicate_exact_boundary():
    failed = _by_slot(graph_idx=0, f=1.2, seed=mod.BLOCK_SEEDS[0],
                      arm="L1_MARGINAL")
    assert mod.is_failed_f12_record(_csv_row(failed)) is True
    assert mod.is_failed_f12_record(_csv_row(failed, exact=True)) is False
    assert mod.is_failed_f12_record(_csv_row(failed, invoked=False)) is False
    assert mod.is_failed_f12_record(
        _csv_row(failed, status="crash:ValueError", finite=False)) is False
    assert mod.is_failed_f12_record(_csv_row(failed, finite=False)) is False
    assert mod.is_failed_f12_record(_csv_row(failed)) is True  # f checked
    sanity = _by_slot(graph_idx=0, f=1.0, seed=mod.BLOCK_SEEDS[0],
                      arm="L1_MARGINAL")
    assert mod.is_failed_f12_record(_csv_row(sanity)) is False


def test_x3_selector_preserves_identity_and_does_not_dedup():
    slot = _by_slot(graph_idx=2, f=1.2, seed=mod.BLOCK_SEEDS[7],
                    arm="L2_TO_L1_TRANSFER")
    rows = [_csv_row(slot), _csv_row(slot)]  # two distinct calls, same shape
    selected = mod.select_failed_x2_records(rows)
    assert len(selected) == 2
    for rec in selected:
        assert int(rec["graph_idx"]) == 2
        assert int(rec["l1_graph_seed"]) == mod.GRAPH_PAIRS[2][0]
        assert int(rec["l2_graph_seed"]) == mod.GRAPH_PAIRS[2][1]
        assert int(rec["seed"]) == mod.BLOCK_SEEDS[7]
        assert rec["arm"] == "L2_TO_L1_TRANSFER"
        assert rec["role"] == "TARGET"
        assert int(rec["rows"]) == mod.F_ROWS[1.2]["L1"]
        assert mod._prior_kind(rec) == "TRANSFER"


def test_x3_plan_counts_selected_source_reuse():
    target = _by_slot(graph_idx=0, f=1.2, seed=mod.BLOCK_SEEDS[0],
                      arm="L1_TO_L2_TRANSFER")
    source = _by_slot(graph_idx=0, f=1.2, seed=mod.BLOCK_SEEDS[0],
                      arm="L1_MARGINAL")
    # target alone: its source is not selected -> one reconstruction call
    plan = mod.plan_x3_calls([_csv_row(target)])
    assert plan["ladder_calls"] == 3
    assert plan["reconstruction_calls"] == 1
    assert plan["total_calls"] == 4
    # source + target: the source baseline supplies the beliefs
    plan = mod.plan_x3_calls([_csv_row(source), _csv_row(target)])
    assert plan["ladder_calls"] == 6
    assert plan["reconstruction_calls"] == 0
    assert plan["total_calls"] == 6
    assert plan["max_selected_records"] == 192
    assert plan["ladder_call_ceiling"] == 576
    assert plan["reconstruction_call_ceiling"] == 96


def test_x3_plan_guard_rejects_over_ceiling():
    with pytest.raises(mod.PreflightBlocked):
        mod._guard_x3_plan({"selected_records": 193, "ladder_calls": 579,
                            "reconstruction_calls": 0})
    with pytest.raises(mod.PreflightBlocked):
        mod._guard_x3_plan({"selected_records": 192, "ladder_calls": 579,
                            "reconstruction_calls": 0})
    with pytest.raises(mod.PreflightBlocked):
        mod._guard_x3_plan({"selected_records": 96, "ladder_calls": 288,
                            "reconstruction_calls": 97})


def test_x3_manifest_validation_refuses_foreign_root():
    manifest = _frozen_manifest()
    ok = mod.validate_x2_manifest(dict(manifest))
    assert ok["cycle_id"] == "V72P2D7-ROOT-CAUSE-RESET"
    bad = dict(manifest, cycle_id="OTHER")
    with pytest.raises(mod.PreflightBlocked):
        mod.validate_x2_manifest(bad)
    bad = dict(manifest, model_f_root="workspace/elsewhere")
    with pytest.raises(mod.PreflightBlocked):
        mod.validate_x2_manifest(bad)
    bad = dict(manifest, graph_pairs=[[1, 2]])
    with pytest.raises(mod.PreflightBlocked):
        mod.validate_x2_manifest(bad)


# --------------------------------------------------------------------------
# X3: runner fixtures (fake contexts, fake decoders, fabricated X2 roots)
# --------------------------------------------------------------------------
def _frozen_manifest():
    return {
        "cycle_id": "V72P2D7-ROOT-CAUSE-RESET",
        "change_name": "formal-ir-d7-root-cause-and-route-reset",
        "phase": "X2_MULTIGRAPH_EXPLORATORY",
        "terminal": "INCONCLUSIVE",
        "graph_pairs": [list(pair) for pair in mod.GRAPH_PAIRS],
        "block_seeds": [int(s) for s in mod.BLOCK_SEEDS],
        "f_values": [float(f) for f in mod.F_VALUES],
        "rows": {str(f): dict(mod.F_ROWS[f]) for f in mod.F_VALUES},
        "arms": list(mod.ARM_IDS),
        "max_calls": int(mod.MAX_CALLS),
        "model_f_root": mod.MODEL_F_ROOT,
        "output_files": list(mod.EVIDENCE_FILES),
        "no_overwrite": True,
    }


def _x3_context(seed=13):
    rng = np.random.default_rng(seed)
    joint = rng.random((32, 32, 6)) + 1e-3
    joint = joint / joint.sum(axis=(0, 1), keepdims=True)
    blocks = {}
    for s in mod.BLOCK_SEEDS:
        r = np.random.default_rng(s)
        blocks[int(s)] = {"bob": r.integers(0, 6, size=64),
                          "u1": r.integers(1, 32, size=64),
                          "u2": r.integers(1, 32, size=64)}
    mothers = []
    for g in range(len(mod.GRAPH_PAIRS)):
        rg = np.random.default_rng(200 + g)
        mothers.append({"L1": rg.integers(0, 32, size=(64, 64)),
                        "L2": rg.integers(0, 32, size=(64, 64))})
    return {"joint": joint, "blocks": blocks, "mothers": mothers}


def _write_x2_root(repo_root, rows, manifest=None):
    root = Path(repo_root) / mod.X3_X2_ROOT
    root.mkdir(parents=True)
    with open(root / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest or _frozen_manifest(), fh, sort_keys=True)
    with open(root / "call_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(mod.CALL_RECORD_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return root


def _result(x_hat, beliefs, iterations=2, syndrome_ok=False,
            provenance=CHECK):
    return {"x_hat": np.asarray(x_hat, dtype=np.int64),
            "syndrome_ok": bool(syndrome_ok),
            "iterations": int(iterations),
            "final_beliefs": np.asarray(beliefs, dtype=np.float64),
            "belief_provenance": provenance}


def _input_key(h, prior, syndrome):
    return (np.asarray(h).shape, np.asarray(prior).tobytes(),
            np.asarray(syndrome).tobytes())


class _InputKeyedFake:
    """Deterministic fake keyed by the exact decoder input (test only)."""

    def __init__(self, mapping):
        self.mapping = dict(mapping)
        self.calls = 0
        self.unexpected = []

    def __call__(self, h, prior, syndrome):
        self.calls += 1
        key = _input_key(h, prior, syndrome)
        if key not in self.mapping:
            self.unexpected.append(key)
            raise AssertionError("unexpected decoder input")
        return self.mapping[key]


class _ConstFake:
    """Constant fake used for full-matrix X2 generation and replay."""

    def __init__(self, iterations=3, syndrome_ok=False, provenance=CHECK):
        self.iterations = iterations
        self.syndrome_ok = syndrome_ok
        self.provenance = provenance
        self.calls = 0

    def __call__(self, h, prior, syndrome):
        self.calls += 1
        prior = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.zeros(prior.shape[0], dtype=np.int64),
                "syndrome_ok": bool(self.syndrome_ok),
                "iterations": int(self.iterations),
                "final_beliefs": prior.copy(),
                "belief_provenance": self.provenance}


def _row_from_eval(slot, evaluated, invoked=True):
    row = {field: "" for field in mod.CALL_RECORD_FIELDS}
    for field in ("slot_idx", "graph_idx", "l1_graph_seed", "l2_graph_seed",
                  "f", "seed", "arm", "role", "layer", "condition", "rows",
                  "n"):
        row[field] = slot[field]
    row["invoked"] = invoked
    row["exact"] = bool(evaluated.get("exact", False))
    row["syndrome_ok"] = bool(evaluated.get("syndrome_ok", False))
    row["iterations"] = int(evaluated.get("iterations", 0))
    row["finite"] = bool(evaluated.get("finite", True))
    row["symbol_errors"] = evaluated.get("symbol_errors", "")
    row["unsatisfied_checks"] = evaluated.get("unsatisfied_checks", "")
    row["provenance"] = evaluated.get("provenance", "")
    row["status"] = evaluated.get("status", "ok")
    return row


def _mixed_fixture(tmp_path):
    """One exact source, one failed transfer, one failed source+transfer."""
    ctx = _x3_context()
    s0, s1 = mod.BLOCK_SEEDS[0], mod.BLOCK_SEEDS[1]
    src0 = _by_slot(graph_idx=0, f=1.2, seed=s0, arm="L1_MARGINAL")
    tgt0 = _by_slot(graph_idx=0, f=1.2, seed=s0, arm="L1_TO_L2_TRANSFER")
    src1 = _by_slot(graph_idx=0, f=1.2, seed=s1, arm="L1_MARGINAL")
    tgt1 = _by_slot(graph_idx=0, f=1.2, seed=s1, arm="L1_TO_L2_TRANSFER")
    src0_inp = mod.x3_reconstruct_marginal_call(ctx, src0)
    src0_res = _result(src0_inp["x_true"], src0_inp["prior"], iterations=2,
                       syndrome_ok=True)
    src0_eval = mod._evaluate_record(
        src0, src0_inp["h"], src0_inp["prior"], src0_inp["syndrome"],
        src0_inp["x_true"], src0_res, 0.01, 100)
    tgt0_inp = mod.x3_reconstruct_transfer_call(
        ctx, tgt0, src0_res["final_beliefs"])
    tgt0_res = _result(np.zeros_like(tgt0_inp["x_true"]), tgt0_inp["prior"],
                       iterations=5, syndrome_ok=False)
    tgt0_eval = mod._evaluate_record(
        tgt0, tgt0_inp["h"], tgt0_inp["prior"], tgt0_inp["syndrome"],
        tgt0_inp["x_true"], tgt0_res, 0.01, 100)
    src1_inp = mod.x3_reconstruct_marginal_call(ctx, src1)
    src1_res = _result(np.zeros_like(src1_inp["x_true"]), src1_inp["prior"],
                       iterations=4, syndrome_ok=False)
    src1_eval = mod._evaluate_record(
        src1, src1_inp["h"], src1_inp["prior"], src1_inp["syndrome"],
        src1_inp["x_true"], src1_res, 0.01, 100)
    tgt1_inp = mod.x3_reconstruct_transfer_call(
        ctx, tgt1, src1_res["final_beliefs"])
    tgt1_res = _result(np.zeros_like(tgt1_inp["x_true"]), tgt1_inp["prior"],
                       iterations=6, syndrome_ok=False)
    tgt1_eval = mod._evaluate_record(
        tgt1, tgt1_inp["h"], tgt1_inp["prior"], tgt1_inp["syndrome"],
        tgt1_inp["x_true"], tgt1_res, 0.01, 100)
    exact_f12 = _by_slot(graph_idx=1, f=1.2, seed=s0, arm="L2_MARGINAL")
    sanity = _by_slot(graph_idx=0, f=1.0, seed=s0, arm="L1_MARGINAL")
    blocked = _by_slot(graph_idx=1, f=1.2, seed=s0, arm="L2_TO_L1_TRANSFER")
    crashed = _by_slot(graph_idx=1, f=1.2, seed=s1, arm="L2_MARGINAL")
    rows = [
        _row_from_eval(src0, src0_eval),
        _row_from_eval(tgt0, tgt0_eval),
        _row_from_eval(src1, src1_eval),
        _row_from_eval(tgt1, tgt1_eval),
        _row_from_eval(exact_f12, {"exact": True, "syndrome_ok": True,
                                   "iterations": 1, "finite": True,
                                   "symbol_errors": 0,
                                   "unsatisfied_checks": 0,
                                   "provenance": CHECK, "status": "ok"}),
        _csv_row(sanity),
        _csv_row(blocked, invoked=False, status="blocked:SOURCE_NONFINITE"),
        _csv_row(crashed, status="crash:ValueError", finite=False),
    ]
    root = _write_x2_root(tmp_path, rows)
    truth_mapping = {}
    for rec in (tgt0, src1, tgt1):
        inp = (tgt0_inp if rec is tgt0 else
               src1_inp if rec is src1 else tgt1_inp)
        truth_mapping[_input_key(inp["h"], inp["prior"], inp["syndrome"])] = \
            _result(inp["x_true"], inp["prior"], iterations=2,
                    syndrome_ok=True)
    zero_mapping = {}
    for inp in (tgt0_inp, src1_inp, tgt1_inp):
        zero_mapping[_input_key(inp["h"], inp["prior"], inp["syndrome"])] = \
            _result(np.zeros_like(inp["x_true"]), inp["prior"], iterations=3,
                    syndrome_ok=False)
    replay_mapping = {
        _input_key(src0_inp["h"], src0_inp["prior"],
                   src0_inp["syndrome"]): src0_res,
        _input_key(tgt0_inp["h"], tgt0_inp["prior"],
                   tgt0_inp["syndrome"]): tgt0_res,
        _input_key(src1_inp["h"], src1_inp["prior"],
                   src1_inp["syndrome"]): src1_res,
        _input_key(tgt1_inp["h"], tgt1_inp["prior"],
                   tgt1_inp["syndrome"]): tgt1_res,
    }
    return {
        "ctx": ctx, "root": root, "src0": src0, "tgt0": tgt0,
        "src1": src1, "tgt1": tgt1,
        "fake90": _InputKeyedFake(replay_mapping),
        "fake360": _InputKeyedFake(truth_mapping),
        "flooding": _InputKeyedFake(zero_mapping),
    }


def _run_mixed(fx, tmp_path, out_name="d7_r1_reference_ladder_mixed",
               wall_budget_s=None):
    return mod.run_reference_ladder_selected(
        x2_root=str(fx["root"]),
        out_root=str(Path(tmp_path) / "workspace" / out_name),
        authorized=True, repo_root=str(tmp_path), context=fx["ctx"],
        decoder_fns={"ROW_LAYERED_90": fx["fake90"],
                     "ROW_LAYERED_360": fx["fake360"],
                     "FLOODING_90": fx["flooding"]},
        wall_budget_s=wall_budget_s, command_str="pytest x3 mixed")


def _read_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------
# X3: runner behaviour
# --------------------------------------------------------------------------
def test_x3_runner_completes_mixed_selection_with_accounting(tmp_path):
    fx = _mixed_fixture(tmp_path)
    result = _run_mixed(fx, tmp_path)
    assert result["terminal"] == mod.X3_TERMINAL_COMPLETED
    assert result["selected_records"] == 3
    assert result["ladder_calls"] == 9
    assert result["reconstruction_calls"] == 1
    assert result["total_calls"] == 10
    out = Path(result["out_root"])
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.X3_EVIDENCE_FILES)
    ladder_rows = _read_csv(out / "ladder_records.csv")
    assert len(ladder_rows) == 10
    assert ladder_rows[0]["row_kind"] == "SOURCE_RECONSTRUCTION"
    assert ladder_rows[0]["input_source"] == "source_marginal_replay"
    assert ladder_rows[0]["baseline_replay_match"] == "True"
    assert ladder_rows[0]["record_slot_idx"] == str(fx["src0"]["slot_idx"])
    kinds = [row["row_kind"] for row in ladder_rows]
    assert kinds.count("LADDER") == 9
    assert kinds.count("SOURCE_RECONSTRUCTION") == 1
    for offset, slot in ((1, fx["tgt0"]), (4, fx["src1"]), (7, fx["tgt1"])):
        block = ladder_rows[offset:offset + 3]
        assert [row["ladder_arm"] for row in block] == list(
            mod.LADDER_ARM_IDS)
        assert all(row["record_slot_idx"] == str(slot["slot_idx"])
                   for row in block)
        assert all(row["input_source"] == "record_input" for row in block)
        assert block[0]["baseline_replay_match"] == "True"
    paired = _read_csv(out / "paired_summary.csv")
    assert len(paired) == 3
    by_arm = {row["arm"]: row for row in paired}
    assert by_arm["L1_TO_L2_TRANSFER"]["prior_kind"] == "TRANSFER"
    assert by_arm["L1_MARGINAL"]["prior_kind"] == "MARGINAL"
    for row in paired:
        assert row["arm_360_changed"] == "True"
        assert row["flooding_changed"] == "False"
        assert row["baseline_replay_match"] == "True"
    selected = _read_csv(out / "selected_records.csv")
    assert [row["slot_idx"] for row in selected] == [
        str(fx["tgt0"]["slot_idx"]), str(fx["src1"]["slot_idx"]),
        str(fx["tgt1"]["slot_idx"])]
    assert selected[0]["prior_kind"] == "TRANSFER"
    assert selected[1]["prior_kind"] == "MARGINAL"
    manifest = json.loads((out / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["terminal"] == mod.X3_TERMINAL_COMPLETED
    assert manifest["claim_label"] == mod.X3_CLAIM_LABEL
    assert manifest["ladder_calls"] == 9
    assert manifest["reconstruction_calls"] == 1
    assert manifest["no_overwrite"] is True
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["total_calls"] == 10
    assert summary["stop"] is None
    assert (out / "report.md").read_text(
        encoding="utf-8").startswith("# D7 R1 X3")
    assert (out / "command_log.txt").read_text(
        encoding="utf-8").startswith("command: pytest x3 mixed")


def test_x3_runner_never_overwrites(tmp_path):
    fx = _mixed_fixture(tmp_path)
    _run_mixed(fx, tmp_path)
    with pytest.raises(FileExistsError):
        _run_mixed(fx, tmp_path)


def test_x3_runner_record_baseline_mismatch_stops_before_later_records(
        tmp_path):
    fx = _mixed_fixture(tmp_path)
    csv_path = fx["root"] / "call_records.csv"
    rows = _read_csv(csv_path)
    for row in rows:
        if row["slot_idx"] == str(fx["tgt0"]["slot_idx"]):
            row["iterations"] = "99"
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(mod.CALL_RECORD_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    result = _run_mixed(fx, tmp_path)
    assert result["terminal"] == mod.X3_TERMINAL_MISMATCH
    assert result["stop"]["where"] == "record_baseline"
    assert result["stop"]["field"] == "iterations"
    out = Path(result["out_root"])
    ladder_rows = _read_csv(out / "ladder_records.csv")
    assert len(ladder_rows) == 2  # one reconstruction + one baseline attempt
    assert ladder_rows[1]["mismatch_field"] == "iterations"
    slots = {row["record_slot_idx"] for row in ladder_rows}
    assert str(fx["src1"]["slot_idx"]) not in slots
    assert str(fx["tgt1"]["slot_idx"]) not in slots
    assert _read_csv(out / "paired_summary.csv") == []
    assert result["ladder_calls"] == 1
    assert result["reconstruction_calls"] == 1


def test_x3_runner_source_reconstruction_mismatch_blocks(tmp_path):
    fx = _mixed_fixture(tmp_path)
    csv_path = fx["root"] / "call_records.csv"
    rows = _read_csv(csv_path)
    for row in rows:
        if row["slot_idx"] == str(fx["src0"]["slot_idx"]):
            row["iterations"] = "77"
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(mod.CALL_RECORD_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    result = _run_mixed(fx, tmp_path)
    assert result["terminal"] == mod.X3_TERMINAL_MISMATCH
    assert result["stop"]["where"] == "source_reconstruction"
    assert result["stop"]["field"] == "iterations"
    assert result["ladder_calls"] == 0
    assert result["reconstruction_calls"] == 1


def test_x3_runner_zero_selected_terminal(tmp_path):
    rows = [
        _csv_row(_by_slot(graph_idx=0, f=1.0, seed=mod.BLOCK_SEEDS[0],
                          arm="L1_MARGINAL")),
        _csv_row(_by_slot(graph_idx=1, f=1.2, seed=mod.BLOCK_SEEDS[0],
                          arm="L2_MARGINAL"), exact=True),
        _csv_row(_by_slot(graph_idx=1, f=1.2, seed=mod.BLOCK_SEEDS[0],
                          arm="L2_TO_L1_TRANSFER"), invoked=False,
                 status="blocked:SOURCE_NONFINITE"),
        _csv_row(_by_slot(graph_idx=2, f=1.2, seed=mod.BLOCK_SEEDS[0],
                          arm="L1_MARGINAL"), status="crash:ValueError",
                 finite=False),
    ]
    _write_x2_root(tmp_path, rows)
    result = mod.run_reference_ladder_selected(
        x2_root=str(Path(tmp_path) / mod.X3_X2_ROOT),
        out_root=str(Path(tmp_path) / "workspace"
                     / "d7_r1_reference_ladder_none"),
        authorized=True, repo_root=str(tmp_path),
        decoder_fns={"ROW_LAYERED_90": _boom, "ROW_LAYERED_360": _boom,
                     "FLOODING_90": _boom})
    assert result["terminal"] == mod.X3_TERMINAL_NOT_APPLICABLE
    assert result["selected_records"] == 0
    assert result["ladder_calls"] == 0
    assert result["reconstruction_calls"] == 0
    out = Path(result["out_root"])
    assert sorted(p.name for p in out.iterdir()) == sorted(
        mod.X3_EVIDENCE_FILES)
    assert _read_csv(out / "ladder_records.csv") == []
    assert _read_csv(out / "selected_records.csv") == []
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["terminal"] == mod.X3_TERMINAL_NOT_APPLICABLE
    assert summary["total_calls"] == 0


def test_x3_runner_wall_budget_stops_before_calls(tmp_path):
    fx = _mixed_fixture(tmp_path)
    result = _run_mixed(fx, tmp_path, wall_budget_s=-1.0)
    assert result["terminal"] == mod.X3_TERMINAL_ENGINEERING
    assert result["stop"]["reason"] == "WALL_BUDGET_EXHAUSTED"
    assert result["ladder_calls"] == 0
    assert result["reconstruction_calls"] == 0


def test_x3_runner_refuses_unauthorized_before_reading_x2(tmp_path,
                                                          monkeypatch):
    monkeypatch.setattr(mod, "read_x2_root", _boom)
    out_root = Path(tmp_path) / "workspace" / "d7_r1_reference_ladder_gate"
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_reference_ladder_selected(
            x2_root=str(Path(tmp_path) / mod.X3_X2_ROOT),
            out_root=str(out_root), authorized=False,
            repo_root=str(tmp_path))
    assert not out_root.exists()


def test_x3_runner_requires_exact_frozen_x2_root(tmp_path):
    _write_x2_root(tmp_path, [])
    other = Path(tmp_path) / "workspace" / "d7_r1_multigraph_other"
    other.mkdir()
    with pytest.raises(ValueError):
        mod.run_reference_ladder_selected(
            x2_root=str(other),
            out_root=str(Path(tmp_path) / "workspace"
                         / "d7_r1_reference_ladder_wrongroot"),
            authorized=True, repo_root=str(tmp_path))


def test_x3_runner_never_binds_production_decoders_when_injected(
        tmp_path, monkeypatch):
    fx = _mixed_fixture(tmp_path)
    monkeypatch.setattr(mod, "bind_reference_ladder_decoders", _boom)
    result = _run_mixed(fx, tmp_path)
    assert result["terminal"] == mod.X3_TERMINAL_COMPLETED


def test_x3_runner_full_matrix_all_fail_reaches_ceiling(tmp_path):
    ctx = _x3_context()
    x2_root = Path(tmp_path) / mod.X3_X2_ROOT
    gen_fake = _ConstFake()
    mod.run_multigraph_diagnostic(
        out_root=str(x2_root), authorized=True, joint=ctx["joint"],
        blocks=ctx["blocks"], mothers=ctx["mothers"],
        decoder_fns={"SOURCE": gen_fake, "TARGET": gen_fake},
        repo_root=str(tmp_path), command_str="pytest x2 fake")
    result = mod.run_reference_ladder_selected(
        x2_root=str(x2_root),
        out_root=str(Path(tmp_path) / "workspace"
                     / "d7_r1_reference_ladder_full"),
        authorized=True, repo_root=str(tmp_path), context=ctx,
        decoder_fns={"ROW_LAYERED_90": _ConstFake(),
                     "ROW_LAYERED_360": _ConstFake(),
                     "FLOODING_90": _ConstFake()})
    assert result["terminal"] == mod.X3_TERMINAL_COMPLETED
    assert result["selected_records"] == mod.X3_MAX_SELECTED
    assert result["ladder_calls"] == mod.X3_LADDER_CALL_CEILING
    assert result["reconstruction_calls"] == 0
    assert result["total_calls"] == 576


# --------------------------------------------------------------------------
# X3: CLI gating (P07)
# --------------------------------------------------------------------------
def test_x3_cli_refuses_unauthorized_before_reading_x2(tmp_path, monkeypatch,
                                                       capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x3_reference_ladder_authorized": False})
    monkeypatch.setattr(cli._mod, "read_x2_root", _boom)
    out_root = Path(tmp_path) / "workspace" / "d7_r1_reference_ladder_cli"
    rc = cli.main(["--reference-ladder",
                   "--x2-root", str(Path(tmp_path) / mod.X3_X2_ROOT),
                   "--out-root", str(out_root)])
    assert rc == 3
    assert not out_root.exists()
    assert "not authorized" in capsys.readouterr().out


def test_x3_cli_requires_both_roots(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x3_reference_ladder_authorized": True})
    assert cli.main(["--reference-ladder"]) == 3
    assert "missing --x2-root" in capsys.readouterr().out


def test_x3_cli_authorized_wiring_and_mismatch_exit(tmp_path, monkeypatch,
                                                    capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x3_reference_ladder_authorized": True})
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"terminal": mod.X3_TERMINAL_COMPLETED, "out_root": "x",
                "selected_records": 2, "ladder_calls": 6,
                "reconstruction_calls": 0}

    monkeypatch.setattr(cli._mod, "run_reference_ladder_selected",
                        fake_runner)
    rc = cli.main(["--reference-ladder",
                   "--x2-root", "workspace/d7_r1_multigraph_20260913_r1",
                   "--out-root", "workspace/"
                                 "d7_r1_reference_ladder_20260913_r1",
                   "--wall-budget-s", "3600"])
    assert rc == 0
    assert captured["authorized"] is True
    assert captured["repo_root"] == cli.ROOT
    assert captured["wall_budget_s"] == 3600.0
    assert "terminal=X3_REFERENCE_LADDER_COMPLETED" in capsys.readouterr().out

    def mismatch_runner(**kwargs):
        return {"terminal": mod.X3_TERMINAL_MISMATCH, "out_root": "x",
                "selected_records": 1, "ladder_calls": 1,
                "reconstruction_calls": 0}

    monkeypatch.setattr(cli._mod, "run_reference_ladder_selected",
                        mismatch_runner)
    assert cli.main(["--reference-ladder", "--x2-root", "a",
                     "--out-root", "b"]) == 1


# --------------------------------------------------------------------------
# Prior finding: reference-ladder bind/import/signature coverage
# --------------------------------------------------------------------------
class _FakeV35:
    def __init__(self):
        self.row_calls = []
        self.flood_calls = []

    def decode_row_layered_fftqspa(self, h, prior, syndrome, **kwargs):
        self.row_calls.append(kwargs)
        return {"x_hat": np.zeros(np.asarray(prior).shape[0], dtype=np.int64)}

    def decode_flooding_fftqspa(self, h, prior, syndrome, **kwargs):
        self.flood_calls.append(kwargs)
        return {"x_hat": np.zeros(np.asarray(prior).shape[0], dtype=np.int64)}


def test_rl_bind_wrapper_contract_without_production_decoder(monkeypatch):
    fake = _FakeV35()
    monkeypatch.setattr(d7e, "_load_v35", lambda: fake)
    bound = mod.bind_reference_ladder_decoders()
    assert sorted(bound) == ["FLOODING_90", "ROW_LAYERED_360",
                             "ROW_LAYERED_90"]
    for fn in bound.values():
        assert list(inspect.signature(fn).parameters) == ["h", "prior",
                                                          "syndrome"]
    assert fake.row_calls == [] and fake.flood_calls == []
    prior = np.full((4, 32), 1.0 / 32)
    syndrome = np.zeros(2)
    bound["ROW_LAYERED_90"](np.zeros((2, 4)), prior, syndrome)
    bound["ROW_LAYERED_360"](np.zeros((2, 4)), prior, syndrome)
    bound["FLOODING_90"](np.zeros((2, 4)), prior, syndrome)
    assert fake.row_calls[0] == {"max_iter": 90, "damping_alpha": 1.0,
                                 "warm_beliefs": None, "field": None}
    assert fake.row_calls[1]["max_iter"] == 360
    assert fake.row_calls[1]["damping_alpha"] == 1.0
    assert fake.flood_calls[0] == {"max_iter": 90, "field": None}


def test_rl_bind_real_import_in_production_layout_subprocess():
    # The production CLI runs with comparison_bench/src on sys.path (flat
    # layout).  Prove the real v35 import + bind in that layout in a clean
    # subprocess so the in-process dual-namespace shadowing cannot interfere.
    # No wrapper is invoked: the true-condition binding probe belongs to X3
    # Pre-EXECUTE before the authorization is consumed.
    import os
    import subprocess
    import textwrap

    code = textwrap.dedent(
        """
        import importlib.util
        import inspect
        import sys

        spec = importlib.util.spec_from_file_location(
            "x3_bind_probe", sys.argv[1])
        module = importlib.util.module_from_spec(spec)
        sys.modules["x3_bind_probe"] = module
        spec.loader.exec_module(module)
        bound = module.bind_reference_ladder_decoders()
        assert sorted(bound) == ["FLOODING_90", "ROW_LAYERED_360",
                                 "ROW_LAYERED_90"]
        for fn in bound.values():
            assert list(inspect.signature(fn).parameters) == [
                "h", "prior", "syndrome"]
        print("BIND_OK")
        """)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "comparison_bench" / "src")
    proc = subprocess.run(
        [sys.executable, "-c", code, str(CORE_PATH)], cwd=str(ROOT),
        env=env, capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert "BIND_OK" in proc.stdout


# --------------------------------------------------------------------------
# X4: G2 bridge (P08/P09)
# --------------------------------------------------------------------------
def _all_false_d5_state():
    return {key: False for key in mod.D5_EXECUTION_FLAG_KEYS}


def test_x4_bridge_requires_x4_grant():
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g2_bridge(d7_state={}, d5_state=_all_false_d5_state(),
                          run_g2_fn=_boom)
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g2_bridge(
            d7_state={"x4_g2_execution_authorized": False},
            d5_state=_all_false_d5_state(), run_g2_fn=_boom)


@pytest.mark.parametrize("flag", mod.D5_EXECUTION_FLAG_KEYS)
def test_x4_bridge_rejects_any_other_d5_execution_flag(flag):
    state = _all_false_d5_state()
    state[flag] = True
    with pytest.raises(mod.NotAuthorizedError):
        mod.run_g2_bridge(
            d7_state={"x4_g2_execution_authorized": True},
            d5_state=state, run_g2_fn=_boom)


def test_x4_bridge_refuses_existing_frozen_root(tmp_path):
    existing = tmp_path / "workspace" / "v72p2d5_g2" / "20260906_r1"
    existing.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        mod.run_g2_bridge(
            d7_state={"x4_g2_execution_authorized": True},
            d5_state=_all_false_d5_state(), frozen_root=str(existing),
            run_g2_fn=_boom)


def test_x4_bridge_calls_runner_exactly_once_and_never_sets_flag(tmp_path):
    calls = []

    def fake_runner():
        calls.append(1)
        return {"grade": "G2_INCONCLUSIVE", "passed": False,
                "decoder_calls": 1320, "wall_seconds": 1.5,
                "peak_rss_bytes": 1024, "runtime_status":
                "G2_RUNTIME_UNVERIFIED"}

    d5_state = _all_false_d5_state()
    frozen = tmp_path / "workspace" / "v72p2d5_g2" / "20260906_r1"
    result = mod.run_g2_bridge(
        d7_state={"x4_g2_execution_authorized": True}, d5_state=d5_state,
        frozen_root=str(frozen), run_g2_fn=fake_runner)
    assert calls == [1]
    assert result["grade"] == "G2_INCONCLUSIVE"
    assert result["decoder_calls"] == 1320
    assert d5_state == _all_false_d5_state()
    assert not frozen.exists()


def test_x4_cli_refuses_unauthorized_before_bridge(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_load_state",
                        lambda path: {"x4_g2_execution_authorized": False})
    monkeypatch.setattr(cli._mod, "run_g2_bridge", _boom)
    assert cli.main(["--g2"]) == 3
    assert "not authorized" in capsys.readouterr().out


def test_x4_cli_rejects_true_d5_flag_without_production_run(
        monkeypatch, tmp_path, capsys):
    d7_state = {"x4_g2_execution_authorized": True}
    d5_state = _all_false_d5_state()
    d5_state["g1_execution_authorized"] = True

    def loader(path):
        return d5_state if str(path) == str(cli.D5_STATE_PATH) else d7_state

    monkeypatch.setattr(cli, "_load_state", loader)
    real_bridge = mod.run_g2_bridge

    def guarded(**kwargs):
        kwargs["run_g2_fn"] = _boom
        return real_bridge(**kwargs)

    monkeypatch.setattr(cli._mod, "run_g2_bridge", guarded)
    # The frozen G2 root now exists from the authorized X4 execution; the
    # refusal must leave it byte-untouched (same files, same mtimes) instead
    # of the former pre-X4 absence check.
    frozen = ROOT / d5.G2_FORMAL_ROOT
    before = sorted((p.name, p.stat().st_mtime_ns) for p in frozen.iterdir())
    assert cli.main(["--g2"]) == 3
    assert "must remain false" in capsys.readouterr().out
    after = sorted((p.name, p.stat().st_mtime_ns) for p in frozen.iterdir())
    assert after == before


def test_x4_cli_authorized_wiring(monkeypatch, capsys):
    d7_state = {"x4_g2_execution_authorized": True}
    d5_state = _all_false_d5_state()
    monkeypatch.setattr(
        cli, "_load_state",
        lambda path: d5_state if str(path) == str(cli.D5_STATE_PATH)
        else d7_state)
    captured = {}

    def fake_bridge(**kwargs):
        captured.update(kwargs)
        return {"grade": "G2_SYNTHETIC_QUALIFIED", "out_root": "x",
                "decoder_calls": 1320}

    monkeypatch.setattr(cli._mod, "run_g2_bridge", fake_bridge)
    assert cli.main(["--g2"]) == 0
    assert captured["repo_root"] == cli.ROOT
    assert captured["d5_state"] == d5_state
    assert "grade=G2_SYNTHETIC_QUALIFIED" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Cycle-state + frozen-root guards
# --------------------------------------------------------------------------
def test_cycle_state_marker_and_all_flags_false():
    state = cli._load_state(cli.STATE_PATH)
    for key in ("x1_consistency_probe_authorized",
                "x2_multigraph_execution_authorized",
                "x3_reference_ladder_authorized", "x4_g2_execution_authorized",
                "d7h_execution_authorized", "g1_rerun_authorized",
                "result_solidification_authorized", "scientific_promotion"):
        assert state.get(key) is False, key
    assert state.get("implementation_accepted") is True
    assert str(state.get("state")).upper() == X4_STATE
    assert str(state.get("terminal")).upper() == X4_STATE
    assert str(state.get("next_gate")).upper() == X4_GATE
    assert str(state.get("historical_evidence")).lower() == \
        "retained_byte_identical"


def test_execution_roots_state_after_x4():
    for rel in EXECUTED_ROOTS:
        assert (ROOT / rel).is_dir(), rel
