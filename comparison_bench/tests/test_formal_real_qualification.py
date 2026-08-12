"""Contract tests for the immutable Cascade-only real qualification."""
from __future__ import annotations

import csv
import hashlib
import inspect
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

import pytest

from comparison_bench.src.comparison_bench.formal_ir import real_qualification as rq


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet"
FINAL_MANIFEST = REPO / "comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json"
SYNTHETIC_REPORT = REPO / "comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/formal_qualification_report.json"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_json_bytes(value))


def _safe_remove(path: Path, root: Path) -> None:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_path == resolved_root or resolved_root not in resolved_path.parents:
        raise AssertionError(f"refusing cleanup outside test root: {resolved_path}")
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture(scope="module")
def real_root() -> Path:
    parent = Path(os.environ["FORMAL_IR_TEST_TMP"]).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / f"formal-real-contract-{os.getpid()}"
    if root.exists():
        raise FileExistsError(f"unique test root already exists: {root}")
    root.mkdir()
    try:
        yield root
    finally:
        _safe_remove(root, parent)


@pytest.fixture(scope="module")
def baseline_lock(real_root: Path) -> Path:
    output = real_root / "baseline-lock"
    rq.make_lock(SOURCE, output, FINAL_MANIFEST, SYNTHETIC_REPORT)
    rq.verify_lock(output, "lock")
    return output


def _copy_lock(source: Path, target: Path) -> Path:
    shutil.copytree(source, target)
    plan_path = target / "pre_run_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["declared_argv"][-1] = str(target)
    _write_json(plan_path, plan)
    return target


def _rewrite_lock(target: Path, mutate: Callable[[dict[str, Any], dict[str, Any]], None]) -> None:
    lock_path = target / "real_data_lock.json"
    plan_path = target / "pre_run_plan.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    mutate(lock, plan)
    core = {key: value for key, value in lock.items() if key != "lock_content_sha256"}
    lock["lock_content_sha256"] = _sha(_compact(core))
    _write_json(lock_path, lock)
    plan["real_data_lock_sha256"] = _sha(lock_path.read_bytes())
    plan["declared_argv"][-1] = str(target)
    _write_json(plan_path, plan)


def _preflight(passed: bool = True) -> dict[str, Any]:
    command = [
        os.sys.executable,
        "-m",
        "pytest",
        "comparison_bench/tests/test_formal_verification.py",
        "comparison_bench/tests/test_cascade_formal.py",
        "comparison_bench/tests/test_ldpc_formal.py",
        "comparison_bench/tests/test_formal_real_qualification.py",
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        "external-test-preflight",
    ]
    return {
        "command": command,
        "exit_code": 0 if passed else 1,
        "passed_count": 29 if passed else 0,
        "output_sha256": "a" * 64,
        "passed": passed,
    }


def _git() -> dict[str, Any]:
    raw = b" M deliberate-test-state\n"
    return {
        "commit": "1" * 40,
        "porcelain_bytes_hex": raw.hex(),
        "porcelain_sha256": _sha(raw),
        "dirty": True,
    }


def _argv(output: Path) -> list[str]:
    return ["run_formal_real_qualification.py", "--output-dir", str(output)]


def _assert_external(path: Path) -> None:
    resolved = path.resolve()
    assert resolved != REPO
    assert REPO not in resolved.parents


def test_external_root_probe_collision_preserves_existing_file(real_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = real_root / "probe-collision"
    candidate.mkdir()
    existing = candidate / ".formal-ir-write-probe-collision"
    existing.write_bytes(b"must-survive")
    monkeypatch.setattr(rq.secrets, "token_hex", lambda _length: "collision")
    assert rq._writable_external_root(candidate, REPO) is None
    assert existing.read_bytes() == b"must-survive"


def test_preflight_inherits_only_writable_external_root(real_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inherited = real_root / "preflight-inherited"
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured.update(command=command, **kwargs)
        return type("Result", (), {"stdout": b"29 passed\n", "stderr": b"", "returncode": 0})()

    monkeypatch.setenv("FORMAL_IR_TEST_TMP", str(inherited))
    monkeypatch.setattr(rq.subprocess, "run", fake_run)
    evidence = rq._deterministic_preflight()
    basetemp = Path(captured["command"][-1])
    assert Path(captured["env"]["FORMAL_IR_TEST_TMP"]) == inherited.resolve()
    assert evidence["passed_count"] == 29
    _assert_external(inherited); _assert_external(basetemp)
    assert basetemp.parent == inherited.resolve()


@pytest.mark.parametrize("candidate_kind", ["missing", "inside_repo", "unwritable"])
def test_preflight_invalid_root_falls_back_external(real_root: Path, monkeypatch: pytest.MonkeyPatch, candidate_kind: str) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(rq, "_system_temp_root", lambda: real_root)
    if candidate_kind == "missing":
        monkeypatch.delenv("FORMAL_IR_TEST_TMP", raising=False)
    elif candidate_kind == "inside_repo":
        monkeypatch.setenv("FORMAL_IR_TEST_TMP", str(REPO / "workspace" / "forbidden-preflight"))
    else:
        rejected = (real_root / "unwritable-candidate").resolve()
        original = rq._writable_external_root
        monkeypatch.setenv("FORMAL_IR_TEST_TMP", str(rejected))
        monkeypatch.setattr(rq, "_writable_external_root", lambda path, repo: None if path.resolve() == rejected else original(path, repo))

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured.update(command=command, **kwargs)
        return type("Result", (), {"stdout": b"29 passed\n", "stderr": b"", "returncode": 0})()

    monkeypatch.setattr(rq.subprocess, "run", fake_run)
    rq._deterministic_preflight()
    test_root = Path(captured["env"]["FORMAL_IR_TEST_TMP"])
    basetemp = Path(captured["command"][-1])
    _assert_external(test_root); _assert_external(basetemp)
    assert test_root != (REPO / "workspace" / "forbidden-preflight").resolve()
    assert basetemp.parent == test_root


def _fake_success(*_args: Any, **kwargs: Any) -> dict[str, Any]:
    key = f"{kwargs['dataset_id']}:{kwargs['frame_id']}"
    event = {
        "event_id": 1,
        "frame_key": key,
        "method": rq.METHOD,
        "event_type": "BLOCK_PARITY",
        "direction": "alice_to_bob",
        "parent_event_id": None,
        "pass_id": 0,
        "block_id": 0,
        "key_dependent_bits": 1,
        "public_control_bits": 0,
        "payload": {"parity": 0},
    }
    transcript = rq.canonical_event(event)
    seed = kwargs["locked_seed"]
    outcome = {
        "dataset_id": str(kwargs["dataset_id"]),
        "frame_id": str(kwargs["frame_id"]),
        "n_pairs": 64,
        "pair_idx_sequence_sha256": _sha(_compact(list(range(64)))),
        "method": rq.METHOD,
        "attempted": True,
        "denominator_included": True,
        "status": "verified_success",
        "failure_reason": "",
        "dimension": rq.Q,
        "frame_len_symbols": rq.N,
        "raw_ser": 0.25,
        "verification_invoked": True,
        "verification_seed_id": seed["seed_id"],
        "verification_tag_bits": 64,
        "epsilon_ec": 2.0 ** -64,
        "key_dependent_disclosure_bits_total": 1,
        "public_control_bits_total": 0,
        "transcript_first_event_id": 1,
        "transcript_last_event_id": 1,
        "transcript_sha256": _sha(transcript),
        "runtime_s": 0.001,
    }
    return {"events": [event], "outcome": outcome}


@pytest.fixture(scope="module")
def success_package(real_root: Path, baseline_lock: Path) -> Path:
    output = _copy_lock(baseline_lock, real_root / "success")
    rq._run_locked_for_test(
        output,
        runner=_fake_success,
        _argv=_argv(output),
        _preflight=_preflight(),
        _git=_git(),
    )
    rq.verify_run(output)
    return output


def _coordinated_manifest_rewrite(output: Path, mutate: Callable[[dict[str, Any]], None] | None = None) -> None:
    manifest_path = output / "formal_run_manifest.json"
    report_path = output / "formal_qualification_report.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"] = rq._dag(output)
    if mutate is not None:
        mutate(manifest)
    _write_json(manifest_path, manifest)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["formal_run_manifest_sha256"] = _sha(manifest_path.read_bytes())
    _write_json(report_path, report)


def test_actual_lock_create_and_verify(baseline_lock: Path) -> None:
    assert {item.name for item in baseline_lock.iterdir()} == rq.LOCK_FILES
    lock = rq.verify_lock(baseline_lock, "lock")
    assert lock["eligibility"]["bw100"] == {"count": 295, **{f"{key}_sha256": value for key, value in rq.ELIGIBILITY_HASHES["bw100"].items()}}
    assert lock["eligibility"]["bw120"] == {"count": 322, **{f"{key}_sha256": value for key, value in rq.ELIGIBILITY_HASHES["bw120"].items()}}
    assert len(lock["selected_frames"]) == 120
    assert len(lock["confirmation_seeds"]) == 60
    assert lock["synthetic_v3"]["ldpc_excluded"] is True
    assert lock["method"] == "cascade_formal_v1"
    assert "ldpc_formal_v1" not in json.dumps(lock["selected_frames"])


def test_coordinated_lock_tampering_is_rejected(real_root: Path, baseline_lock: Path) -> None:
    mutations: list[tuple[str, Callable[[dict[str, Any], dict[str, Any]], None]]] = [
        ("selected-ser", lambda lock, _plan: (lock["selected_frames"][0].__setitem__("frame_ser", 0.234375), lock.__setitem__("selected_frames_sha256", _sha(_compact(lock["selected_frames"]))))),
        ("eligibility", lambda lock, _plan: lock["eligibility"]["bw100"].__setitem__("selected_sha256", "0" * 64)),
        ("overlap", lambda lock, _plan: lock["final_ir_v1"].__setitem__("overlap_count", 1)),
        ("calibration-seed", lambda lock, _plan: lock["confirmation_seeds"].__setitem__(lock["selected_frames"][0]["frame_key"], next(iter(lock["confirmation_seeds"].values())))),
        ("ldpc-flag", lambda lock, _plan: lock["synthetic_v3"].__setitem__("ldpc_excluded", False)),
        ("plan-method", lambda _lock, plan: plan.__setitem__("method", "ldpc_formal_v1")),
    ]
    for name, mutation in mutations:
        target = _copy_lock(baseline_lock, real_root / f"tamper-{name}")
        _rewrite_lock(target, mutation)
        with pytest.raises(ValueError):
            rq.verify_lock(target, "lock")
    extra = _copy_lock(baseline_lock, real_root / "tamper-extra")
    (extra / "extra.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact set"):
        rq.verify_lock(extra, "lock")


def test_invalid_lock_makes_zero_method_calls(real_root: Path, baseline_lock: Path) -> None:
    target = _copy_lock(baseline_lock, real_root / "invalid-zero-calls")
    _rewrite_lock(target, lambda lock, _plan: lock.__setitem__("method", "ldpc_formal_v1"))
    calls: list[int] = []

    def fake(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {}

    with pytest.raises(ValueError):
        rq._run_locked_for_test(target, runner=fake, _argv=_argv(target), _preflight=_preflight(), _git=_git())
    assert calls == []


def test_fake_success_produces_strict_completed_package(success_package: Path) -> None:
    rq.verify_run(success_package)
    rows = list(csv.DictReader((success_package / "formal_frame_outcomes.csv").open(encoding="utf-8")))
    report = json.loads((success_package / "formal_qualification_report.json").read_text(encoding="utf-8"))
    assert len(rows) == 60
    assert {row["status"] for row in rows} == {"verified_success"}
    assert report["promotion_gate"]["promoted"] is True
    assert set(inspect.signature(rq.run_locked).parameters) == {"output"}
    source = inspect.getsource(rq.run_locked)
    assert "ldpc" not in source.lower()
    assert "_lite" not in source


def test_success_package_coordinated_tampering_is_rejected(success_package: Path) -> None:
    tracked = {path.name: path.read_bytes() for path in success_package.iterdir() if path.is_file()}

    def restore() -> None:
        for name, data in tracked.items():
            (success_package / name).write_bytes(data)
        for path in success_package.iterdir():
            if path.is_file() and path.name not in tracked:
                path.unlink()

    cases: list[Callable[[], None]] = []

    def extra() -> None:
        (success_package / "extra.txt").write_text("x", encoding="utf-8")

    cases.append(extra)
    cases.append(lambda: _coordinated_manifest_rewrite(success_package, lambda manifest: manifest["argv"].append("--extra")))
    cases.append(lambda: _coordinated_manifest_rewrite(success_package, lambda manifest: manifest.__setitem__("verification_union_bound", 0.0)))

    def gate() -> None:
        report_path = success_package / "formal_qualification_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["promotion_gate"]["promoted"] = False
        _write_json(report_path, report)

    cases.append(gate)

    def transcript() -> None:
        path = success_package / "formal_transcript.jsonl"
        event = json.loads(path.read_bytes().splitlines()[0])
        path.write_bytes((json.dumps(event, sort_keys=True) + "\n").encode("utf-8") + b"\n".join(path.read_bytes().splitlines()[1:]) + b"\n")
        _coordinated_manifest_rewrite(success_package)

    cases.append(transcript)

    def empty_codebook() -> None:
        (success_package / "formal_codebook_manifest.json").write_bytes(b"")
        _coordinated_manifest_rewrite(success_package)

    cases.append(empty_codebook)

    def outcome_status() -> None:
        path = success_package / "formal_frame_outcomes.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        fields = list(rows[0])
        rows[0]["status"] = "verified_success"
        rows[0]["key_dependent_disclosure_bits_total"] = "2"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        _coordinated_manifest_rewrite(success_package)

    cases.append(outcome_status)

    for mutate in cases:
        restore()
        mutate()
        with pytest.raises((ValueError, json.JSONDecodeError)):
            rq.verify_run(success_package)
    restore()
    rq.verify_run(success_package)


def test_failed_preflight_is_verifiable_and_rerun_refused(real_root: Path, baseline_lock: Path) -> None:
    output = _copy_lock(baseline_lock, real_root / "failed-preflight")
    calls: list[int] = []

    def fake(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {}

    with pytest.raises(RuntimeError, match="preflight"):
        rq._run_locked_for_test(output, runner=fake, _argv=_argv(output), _preflight=_preflight(False), _git=_git())
    assert calls == []
    assert {item.name for item in output.iterdir()} == rq.RUN_FILES
    rq.verify_run(output)
    with pytest.raises((FileExistsError, ValueError)):
        rq._run_locked_for_test(output, runner=fake, _argv=_argv(output), _preflight=_preflight(), _git=_git())
    assert calls == []


def test_bad_original_transcript_hash_finalizes_nonpromotion(real_root: Path, baseline_lock: Path) -> None:
    output = _copy_lock(baseline_lock, real_root / "bad-method-transcript")
    calls: list[int] = []

    def bad(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        result = _fake_success(*args, **kwargs)
        result["outcome"]["transcript_sha256"] = "0" * 64
        return result

    with pytest.raises(ValueError, match="original transcript"):
        rq._run_locked_for_test(output, runner=bad, _argv=_argv(output), _preflight=_preflight(), _git=_git())
    assert calls == [1]
    rq.verify_run(output)
    rows = list(csv.DictReader((output / "formal_frame_outcomes.csv").open(encoding="utf-8")))
    assert len(rows) == 0
    assert json.loads((output / "formal_qualification_report.json").read_text(encoding="utf-8"))["promotion_gate"]["promoted"] is False
