"""Small fake-only contract tests for the common-seed construction canary."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.cli.probes_closed import nbldpc_gf32_construction_probe as probe
from comparison_bench.formal_ir import nonbinary_v10_common as common


def _fresh_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                name: str) -> tuple[Path, Path]:
    repo = tmp_path / f"repo-{name}"
    (repo / "workspace").mkdir(parents=True)
    relative = Path("workspace") / name
    monkeypatch.setattr(probe, "OUT_ROOT_RELATIVE", relative)
    return repo, relative


def _fake_callbacks(script=None):
    """Return explicit fake callbacks; matrices are mapping tokens, not graphs."""
    script = {} if script is None else dict(script)
    seed_location = {
        seed: (graph_id, attempt_j)
        for graph_id, attempt_j, seed in probe.attempt_seed_plan()
    }
    calls: list[tuple[int, int, int, str]] = []
    preflights: list[tuple[int, int, int, str]] = []

    def graph_builder(profile, construction_seed):
        graph_id, attempt_j = seed_location[int(construction_seed)]
        profile_id = str(profile["profile_id"])
        key = (graph_id, attempt_j, profile_id)
        calls.append((*key[:2], int(construction_seed), profile_id))
        outcome = script.get(key, "admit")
        if outcome == "raise":
            raise RuntimeError("fixture constructor exception")
        if outcome == "construction_failed":
            return {
                "status": "construction_failed",
                "graph_seed": int(construction_seed),
                "profile_id": profile_id,
                "H": None,
                "structure": None,
                "failure_reason": "fixture expected construction failure",
            }
        if outcome not in ("admit", "reject"):
            raise AssertionError(f"unknown fixture outcome: {outcome}")

        # A tiny tagged array proves retention and lineage only. The injected
        # preflight below deliberately makes no claim about GF32 graph validity.
        tag = len(calls)
        h = np.asarray([[tag, 0], [0, tag]], dtype=np.int64)
        return {
            "status": "ok",
            "graph_seed": int(construction_seed),
            "profile_id": profile_id,
            "H": h,
            "structure": {"fixture_token": tag},
            "fixture_admitted": outcome == "admit",
        }

    def profile_preflight(profile, record, construction_seed):
        key = (int(record["graph_seed"]), int(construction_seed),
               str(profile["profile_id"]))
        assert key[0] == key[1]
        assert record["profile_id"] == key[2]
        graph_id, attempt_j = seed_location[key[1]]
        preflights.append((graph_id, attempt_j, key[1], key[2]))
        return bool(record["fixture_admitted"]), {
            "fixture_preflight": True,
            "fixture_token": record["structure"]["fixture_token"],
        }

    return graph_builder, profile_preflight, calls, preflights


def _run(repo: Path, relative: Path, callbacks, **kwargs):
    graph_builder, profile_preflight, _, _ = callbacks
    return probe.execute_batch(
        out_root=relative, repo_root=repo, graph_builder=graph_builder,
        profile_preflight_fn=profile_preflight, now=lambda: 1.0,
        rss_fn=lambda: 0, **kwargs)


def test_t0_dry_run_and_existing_root_refusal_are_zero_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    t0 = probe.verify_t0()
    assert all(t0.values())
    plan = probe.attempt_seed_plan()
    assert len(plan) == 6 * 8
    assert len({seed for _, _, seed in plan}) == len(plan)
    for graph_id, attempt_j, seed in plan:
        expected = (graph_id if attempt_j == 0 else int(common.v10_seed(
            f"{probe.SEED_NAMESPACE}:{graph_id}:{attempt_j}")))
        assert seed == expected
    assert probe.MAX_GRAPH_CALLS == 96

    # An unexpected binder call would enter production graph construction.
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(probe, "_bind_production",
                        lambda: pytest.fail("dry-run used production binder"))
        target = Path("workspace") / "gf32_construct_dry_test_absent"
        repo = tmp_path / "repo-dry-run"
        (repo / "workspace").mkdir(parents=True)
        patcher.setattr(probe, "OUT_ROOT_RELATIVE", target)
        dry = probe.dry_run(target, repo_root=repo)
        assert dry["status"] == "DRY_RUN"
        assert dry["t0"] and all(dry["t0"].values())
        assert all(dry[name] == 0 for name in
                   ("writes", "input_reads", "graph_calls", "decoder_calls"))
        assert not (repo / target).exists()

        callbacks = _fake_callbacks()
        destination = repo / target
        destination.mkdir()
        sentinel = destination / "keep.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        with pytest.raises(FileExistsError):
            _run(repo, target, callbacks)
        assert callbacks[2] == []
        assert callbacks[3] == []
        assert sentinel.read_text(encoding="utf-8") == "preserve"


def test_first_common_admitted_seed_is_selected_without_splicing_profiles(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    first = probe.GRAPH_IDS[0]
    script = {
        (first, 0, "control"): "admit",
        (first, 0, "candidate"): "reject",
        (first, 1, "control"): "reject",
        (first, 1, "candidate"): "admit",
        (first, 2, "control"): "admit",
        (first, 2, "candidate"): "admit",
    }
    repo, relative = _fresh_repo(tmp_path, monkeypatch, "common-pair")
    callbacks = _fake_callbacks(script)
    result = _run(repo, relative, callbacks)
    assert result["status"] == "COMPLETE"
    assert result["classification"] == "CONSTRUCTION_FEASIBLE"
    assert result["complete_all_groups"] is True
    assert result["graph_calls"] == 16

    calls = callbacks[2]
    assert [(gid, j, arm) for gid, j, _, arm in calls[:6]] == [
        (first, j, arm) for j in range(3)
        for arm in probe.PROFILE_ORDER
    ]
    assert all(calls[index][2] == calls[index + 1][2]
               for index in (0, 2, 4))

    data = json.loads((repo / relative / "constructions.json").read_text(
        encoding="utf-8"))
    group = data["groups"][0]
    assert group["status"] == "SELECTED"
    assert group["selected_attempt_j"] == 2
    assert group["selected_seed"] == probe.seed_for(first, 2)
    selected = group["selected_matrix_indices"]
    assert set(selected) == set(probe.PROFILE_ORDER)
    for profile_id in probe.PROFILE_ORDER:
        matrix = data["matrices"][selected[profile_id]]
        assert matrix["profile_id"] == profile_id
        assert matrix["graph_id"] == first
        assert matrix["attempt_j"] == 2
        assert matrix["construction_seed"] == group["selected_seed"]

    # Earlier one-sided admissions remain in the record but cannot be combined.
    first_group_attempts = [data["attempts"][i]
                            for i in group["attempt_record_indices"]]
    assert [row["admitted"] for row in first_group_attempts] == [
        True, False, False, True, True, True]
    for matrix in data["matrices"]:
        attempt = data["attempts"][matrix["matrix_index"]]
        assert matrix["matrix_index"] == attempt["matrix_index"]
        assert (matrix["graph_id"], matrix["attempt_j"],
                matrix["construction_seed"], matrix["profile_id"]) == (
                    attempt["graph_id"], attempt["attempt_j"],
                    attempt["construction_seed"], attempt["profile_id"])
        assert matrix["H"][0][0] == matrix["structure"]["fixture_token"]


def test_eight_paired_failures_exhaust_one_group_then_continue_fixed_groups(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    first = probe.GRAPH_IDS[0]
    script = {(first, j, arm): "construction_failed"
              for j in range(probe.ATTEMPTS_PER_GROUP)
              for arm in probe.PROFILE_ORDER}
    repo, relative = _fresh_repo(tmp_path, monkeypatch, "exhaustion")
    callbacks = _fake_callbacks(script)
    result = _run(repo, relative, callbacks)

    assert result["status"] == "COMPLETE"
    assert result["classification"] == "CONSTRUCTION_EXHAUSTED"
    assert result["complete_all_groups"] is True
    assert result["exhausted_group_count"] == 1
    assert result["selected_group_count"] == 5
    assert result["graph_calls"] == 8 * 2 + 5 * 2
    calls = callbacks[2]
    assert [(gid, j, arm) for gid, j, _, arm in calls[:16]] == [
        (first, j, arm) for j in range(8)
        for arm in probe.PROFILE_ORDER
    ]
    assert all(calls[index][2] == calls[index + 1][2]
               for index in range(0, 16, 2))
    assert {gid for gid, _, _, _ in calls[16:]} == set(probe.GRAPH_IDS[1:])

    data = json.loads((repo / relative / "constructions.json").read_text(
        encoding="utf-8"))
    assert data["groups"][0]["status"] == "EXHAUSTED"
    assert data["groups"][0]["selected_seed"] is None
    assert all(group["status"] == "SELECTED" for group in data["groups"][1:])
    assert len(data["attempts"]) == 26
    assert len(data["matrices"]) == 10
    assert len(callbacks[3]) == 10


@pytest.mark.parametrize("stop_kind", ["rss", "unexpected_builder"])
def test_partial_stop_retains_prior_matrix_and_has_no_stale_or_next_attempt(
        stop_kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    first = probe.GRAPH_IDS[0]
    script = {}
    if stop_kind == "unexpected_builder":
        script[(first, 0, "candidate")] = "raise"
    repo, relative = _fresh_repo(tmp_path, monkeypatch, f"partial-{stop_kind}")
    callbacks = _fake_callbacks(script)
    graph_builder, preflight, calls, preflights = callbacks
    rss_state = {"high": False}

    def rss_fn():
        if stop_kind == "rss" and rss_state["high"]:
            return probe.RSS_CAP_BYTES
        return 0

    def graph_builder_with_state(profile, seed):
        record = graph_builder(profile, seed)
        if stop_kind == "rss":
            rss_state["high"] = True
        return record

    result = probe.execute_batch(
        out_root=relative, repo_root=repo,
        graph_builder=graph_builder_with_state,
        profile_preflight_fn=preflight, now=lambda: 1.0, rss_fn=rss_fn)
    expected_calls = 1 if stop_kind == "rss" else 2
    assert len(calls) == expected_calls
    assert result["status"] == "STOP"
    assert result["classification"] == "INCOMPLETE"
    assert result["complete_all_groups"] is None

    data = json.loads((repo / relative / "constructions.json").read_text(
        encoding="utf-8"))
    assert data["terminal_status"] == "STOP"
    assert data["complete_all_groups"] is None
    assert data["groups"][0]["status"] == "INCOMPLETE"
    assert len(data["attempts"]) == expected_calls
    assert len(data["matrices"]) == 1
    assert data["matrices"][0]["profile_id"] == "control"
    assert data["matrices"][0]["matrix_index"] == 0
    assert data["attempts"][0]["matrix_index"] == 0
    if stop_kind == "rss":
        assert result["resource_stop_markers"]
        assert "rss_cap_after_graph" in result["resource_stop_markers"][0]
        assert data["attempts"][0]["rss_b"] == probe.RSS_CAP_BYTES
        assert not preflights or preflights[0][3] == "control"
    else:
        failed = data["attempts"][1]
        assert failed["status"] == "unexpected_error"
        assert failed["profile_id"] == "candidate"
        assert failed["matrix_index"] is None
        assert "fixture constructor exception" in failed["failure_reason"]

    assert all((repo / relative / name).exists() for name in (
        "manifest.json", "constructions.json", "EXPLORATION_LOG.md"))
    manifest = json.loads((repo / relative / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["status"] == "STOP"
    assert manifest["classification"] == "INCOMPLETE"


def test_result_cap_stop_keeps_summary_manifest_and_log_incomplete(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, relative = _fresh_repo(tmp_path, monkeypatch, "result-cap")
    callbacks = _fake_callbacks()
    monkeypatch.setattr(probe, "RESULT_CAP_BYTES", 1)
    result = _run(repo, relative, callbacks)

    assert result["status"] == "STOP"
    assert result["classification"] == "INCOMPLETE"
    assert result["complete_all_groups"] is None
    assert result["selected_group_count"] == len(probe.GRAPH_IDS)
    assert len(result["resource_stop_markers"]) == 1
    assert result["resource_stop_markers"][0].startswith("result_size_cap:")

    manifest = json.loads((repo / relative / "manifest.json").read_text(
        encoding="utf-8"))
    data = json.loads((repo / relative / "constructions.json").read_text(
        encoding="utf-8"))
    log = (repo / relative / "EXPLORATION_LOG.md").read_text(encoding="utf-8")
    for output in (manifest, data):
        terminal = output.get("terminal_status", output.get("status"))
        assert terminal == "STOP"
        assert output["classification"] == "INCOMPLETE"
        assert output["complete_all_groups"] is None
        assert output["resource_stop_markers"] == result["resource_stop_markers"]
    assert "resource_stop=result_size_cap:" in log
