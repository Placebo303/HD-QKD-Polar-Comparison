import json
import os
import signal
import time
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli import m3d_iter250_synth as m3d


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def _comparator(arm):
    spec = m3d.ARMS[arm]
    exact = set(spec["exact_indices"])
    nonexact = set(spec["nonexact_indices"])
    expected_failures = spec["baseline_stage1_failures"]
    extras = [idx for idx in range(240)
              if idx not in exact and idx not in nonexact]
    nonexact.update(extras[:expected_failures - len(nonexact)])
    rows = []
    for idx in range(240):
        if idx in exact:
            wall = spec["baseline_exact_wall_s"] / 8
        elif idx in spec["nonexact_indices"]:
            wall = spec["baseline_nonexact_wall_s"] / 8
        else:
            wall = 0.1
        failed = int(idx in nonexact)
        rows.append({
            "block_idx": idx,
            "seed": m3d.SEED_BASE + idx,
            "stage": "stage1",
            "status": "max_iter_reached" if failed else "success",
            "failed": failed,
            "undetected": 0,
            "iters": 300 if failed else 20,
            "wall_s": wall,
        })
    return {"summary": {"verdict": "COMPLETE", "arm": spec["m3b_arm"]},
            "rows": rows}


def _read_for(arm, document=None):
    expected = m3d.ARMS[arm]["comparator"]
    document = document or _comparator(arm)

    def read(path):
        assert Path(path) == expected
        return document

    return read


def _graph_loader(arm, read):
    assert arm in m3d.ARMS
    return ({"n": 1024, "m": 200, "triples": [(0, 0, 1)]},
            {"arm": arm, "rank": 208, "base_rank": 200})


def _run(tmp_path, arm="M3D-R1", *, decode_fn=None, rss_fn=None,
         clock=None, document=None):
    family = tmp_path / "family"
    prefix = str(family) + os.sep
    root = str(family / f"{arm.split('-')[-1]}_fake")
    clock = clock or FakeClock()
    calls = []

    if decode_fn is None:
        def decode_fn(construction, seed, max_iter):
            idx = seed - m3d.SEED_BASE
            calls.append((construction["m"], idx, max_iter))
            clock.advance(1)
            baseline_exact = idx in m3d.ARMS[arm]["exact_indices"]
            return {"status": "success" if baseline_exact else "nonexact",
                    "iterations": 20 if baseline_exact else 100,
                    "max_iter": max_iter,
                    "exact_match": baseline_exact,
                    "reconstruction_ok": False}

    summary = m3d.run_m3d_arm(
        arm=arm, root=root, decode_fn=decode_fn,
        read=_read_for(arm, document), writer=None,
        clock=clock, rss_fn=rss_fn or (lambda: 1024),
        root_prefix=prefix, graph_loader=_graph_loader,
        prior_summary=({"arm": "M3D-R1", "verdict": "COMPLETE",
                        "arm_pass": True} if arm == "M3D-R2" else None))
    return summary, calls, Path(root)


@pytest.mark.parametrize("arm", ["M3D-R1", "M3D-R2"])
def test_selected_calls_pair_with_exact_frozen_stage1_seeds(tmp_path, arm):
    summary, calls, root = _run(tmp_path, arm)
    payload = json.loads((root / "rows.json").read_text(encoding="utf-8"))
    rows = payload["rows"]
    spec = m3d.ARMS[arm]
    expected_indices = list(spec["exact_indices"] + spec["nonexact_indices"])

    assert summary["verdict"] == "COMPLETE"
    assert summary["arm_pass"] is True
    assert len(calls) == 16
    assert [idx for _, idx, _ in calls] == expected_indices
    assert all(m == 200 and cap == 250 for m, _, cap in calls)
    assert [row["block_idx"] for row in rows] == expected_indices
    assert [row["seed"] for row in rows] == [m3d.SEED_BASE + i
                                             for i in expected_indices]
    assert all(row["baseline_exact"] == row["new_exact"] for row in rows)
    assert all(row["max_iter"] == 250 for row in rows)
    assert summary["stage2_calls"] == 0
    assert summary["blocks_done"] == 16
    assert (root / "M3D_RESULT.md").exists()


def test_undetected_is_kept_separate_and_fails_accuracy_gate(tmp_path):
    clock = FakeClock()
    spec = m3d.ARMS["M3D-R1"]

    def decode(construction, seed, max_iter):
        idx = seed - m3d.SEED_BASE
        clock.advance(1)
        exact = idx in spec["exact_indices"]
        return {"status": "success" if exact else "converged_no_syndrome",
                "iterations": 20 if exact else 100, "max_iter": max_iter,
                "exact_match": exact, "reconstruction_ok": not exact}

    summary, _, root = _run(tmp_path, decode_fn=decode, clock=clock)
    payload = json.loads((root / "rows.json").read_text(encoding="utf-8"))
    rows = payload["rows"]

    assert summary["new_undetected"] == 8
    assert summary["accuracy_pass"] is False
    assert summary["arm_pass"] is False
    assert all(row["new_exact"] is False and row["new_undetected"] == 1
               for row in rows if row["selection_stratum"] == "nonexact")


def test_escaped_root_refuses_before_comparator_or_decoder(tmp_path):
    calls = {"read": 0, "decode": 0, "graph": 0}
    family = tmp_path / "family"
    prefix = str(family) + os.sep
    escaped = str(family / ".." / "R1_escape")

    def read(_path):
        calls["read"] += 1
        raise AssertionError("root must be checked before input reads")

    def decode(*_args):
        calls["decode"] += 1

    def graph_loader(*_args, **_kwargs):
        calls["graph"] += 1

    with pytest.raises(m3d.M3DError, match="direct child"):
        m3d.run_m3d_arm(
            arm="M3D-R1", root=escaped, decode_fn=decode, read=read,
            root_prefix=prefix, graph_loader=graph_loader)
    assert calls == {"read": 0, "decode": 0, "graph": 0}


def test_existing_root_refuses_before_input_reads(tmp_path):
    family = tmp_path / "family"
    root_path = family / "R1_existing"
    root_path.mkdir(parents=True)
    calls = {"read": 0, "decode": 0}

    def read(_path):
        calls["read"] += 1

    def decode(*_args):
        calls["decode"] += 1

    with pytest.raises(m3d.M3DError, match="already exists"):
        m3d.run_m3d_arm(
            arm="M3D-R1", root=str(root_path), decode_fn=decode,
            read=read, root_prefix=str(family) + os.sep,
            graph_loader=_graph_loader)
    assert calls == {"read": 0, "decode": 0}


def test_comparator_seed_drift_refuses():
    document = _comparator("M3D-R1")
    document["rows"][0]["seed"] += 1
    with pytest.raises(m3d.M3DError, match="seed does not match"):
        m3d.validate_comparator(document, "M3D-R1")


@pytest.mark.parametrize("stop_kind", ["rss", "call", "wall"])
def test_resource_stop_retains_partial_rows_and_stops(tmp_path, stop_kind):
    clock = FakeClock()
    decode_calls = []

    def decode(construction, seed, max_iter):
        idx = seed - m3d.SEED_BASE
        decode_calls.append(idx)
        seconds = {"rss": 1, "call": 91, "wall": 80}[stop_kind]
        clock.advance(seconds)
        exact = idx in m3d.ARMS["M3D-R1"]["exact_indices"]
        return {"status": "success" if exact else "nonexact",
                "iterations": 20 if exact else 100, "max_iter": max_iter,
                "exact_match": exact, "reconstruction_ok": False}

    rss = (lambda: 2 * (1024 ** 3)) if stop_kind == "rss" else (lambda: 1)
    summary, _, root = _run(tmp_path, decode_fn=decode,
                            rss_fn=rss, clock=clock)
    payload = json.loads((root / "rows.json").read_text(encoding="utf-8"))

    expected_verdict = {
        "rss": "INCOMPLETE-budget",
        "call": "INCOMPLETE-decode-cap",
        "wall": "INCOMPLETE-wall",
    }[stop_kind]
    assert summary["verdict"] == expected_verdict
    assert summary["arm_pass"] is False
    assert len(payload["rows"]) == len(decode_calls)
    assert len(decode_calls) == {"rss": 0, "call": 1, "wall": 15}[stop_kind]


def test_hard_decode_timeout_retains_unknown_row_and_restores_signals(
        monkeypatch, tmp_path):
    if not hasattr(signal, "setitimer") or not hasattr(signal, "ITIMER_REAL"):
        pytest.skip("hard timeout requires POSIX setitimer")
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer != (0.0, 0.0):
        pytest.skip("test process already has an ITIMER_REAL timer")

    def prior_handler(_signum, _frame):
        raise AssertionError("the prior SIGALRM handler should not run")

    signal.signal(signal.SIGALRM, prior_handler)
    monkeypatch.setattr(m3d, "MAX_CALL_WALL_S", 0.05)
    calls = []

    def hung_decode(_construction, seed, _max_iter):
        calls.append(seed)
        time.sleep(5)

    started = time.monotonic()
    try:
        summary, _, root = _run(tmp_path, decode_fn=hung_decode)
        elapsed = time.monotonic() - started
        payload = json.loads((root / "rows.json").read_text(encoding="utf-8"))
        rows = payload["rows"]

        assert elapsed < 1
        assert calls == [m3d.SEED_BASE]
        assert summary["verdict"] == "INCOMPLETE-decode-cap"
        assert summary["arm_pass"] is False
        assert summary["accuracy_pass"] is False
        assert summary["new_undetected_unknown"] == 1
        assert len(rows) == 1
        assert rows[0]["new_status"] == "timeout"
        assert rows[0]["new_exact"] is None
        assert rows[0]["new_undetected"] is None
        assert rows[0]["new_wall_s"] >= 0.04
        assert rows[0]["max_iter"] == m3d.MAX_ITER
        assert "hard decoder deadline exceeded" in rows[0]["error"]
        assert signal.getsignal(signal.SIGALRM) is prior_handler
        assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)
        signal.setitimer(signal.ITIMER_REAL, *old_timer)


def test_active_prior_timer_refuses_without_replacing_handler():
    if not hasattr(signal, "setitimer") or not hasattr(signal, "ITIMER_REAL"):
        pytest.skip("hard timeout requires POSIX setitimer")
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer != (0.0, 0.0):
        pytest.skip("test process already has an ITIMER_REAL timer")

    def prior_handler(_signum, _frame):
        pass

    signal.signal(signal.SIGALRM, prior_handler)
    try:
        signal.setitimer(signal.ITIMER_REAL, 30.0, 0.0)
        before = signal.getitimer(signal.ITIMER_REAL)
        with pytest.raises(m3d.M3DError, match="existing ITIMER_REAL"):
            m3d._require_hard_timeout_support()
        after = signal.getitimer(signal.ITIMER_REAL)
        assert signal.getsignal(signal.SIGALRM) is prior_handler
        assert before[0] > 0 and after[0] > 0
        assert before[1] == after[1] == 0.0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)
        signal.setitimer(signal.ITIMER_REAL, *old_timer)


def test_cli_dry_and_missing_authorization_make_no_production_calls(monkeypatch,
                                                                   capsys):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("pre-gate CLI must not read or bind inputs")

    monkeypatch.setattr(m3d, "read_json", forbidden)
    monkeypatch.setattr(m3d.p1.s2c, "bind_empirical_bundle", forbidden)
    monkeypatch.setattr(m3d.p1.b2f, "decode_block_marginal", forbidden)

    assert m3d.main(["--dry"]) == 0
    dry = json.loads(capsys.readouterr().out)
    assert dry["reads"] == 0
    assert dry["decoder_calls"] == dry["stage2_calls"] == 0

    assert m3d.main([
        "--arm", "M3D-R1", "--root", m3d.ARMS["M3D-R1"]["root"],
        "--execute-synthetic"]) == 2
    assert "require both" in capsys.readouterr().err


def test_cli_timeout_support_gate_precedes_r2_reads_and_channel_bind(
        monkeypatch, capsys):
    calls = {"read": 0, "bind": 0}

    def forbidden_read(*_args, **_kwargs):
        calls["read"] += 1
        raise AssertionError("R2 summary read before timeout support check")

    def forbidden_bind(*_args, **_kwargs):
        calls["bind"] += 1
        raise AssertionError("channel bind before timeout support check")

    def unsupported():
        raise m3d.M3DError("hard decoder timeout unavailable")

    monkeypatch.setattr(m3d, "_check_root", lambda *_args: None)
    monkeypatch.setattr(m3d, "_require_hard_timeout_support", unsupported)
    monkeypatch.setattr(m3d, "read_json", forbidden_read)
    monkeypatch.setattr(m3d.p1.s2c, "bind_empirical_bundle", forbidden_bind)

    result = m3d.main([
        "--arm", "M3D-R2", "--root", m3d.ARMS["M3D-R2"]["root"],
        "--execute-synthetic", "--execution-authorized",
    ])

    assert result == 2
    assert calls == {"read": 0, "bind": 0}
    assert "hard decoder timeout unavailable" in capsys.readouterr().err


def test_r2_requires_r1_complete_and_passed(tmp_path):
    calls = []
    family = tmp_path / "family"
    root = str(family / "R2_fake")
    with pytest.raises(m3d.M3DError, match="requires a complete"):
        m3d.run_m3d_arm(
            arm="M3D-R2", root=root,
            decode_fn=lambda *_args: calls.append(True),
            read=_read_for("M3D-R2"), root_prefix=str(family) + os.sep,
            graph_loader=_graph_loader,
            prior_summary={"arm": "M3D-R1", "verdict": "INCOMPLETE",
                           "arm_pass": False})
    assert calls == []
