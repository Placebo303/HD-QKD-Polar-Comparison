from __future__ import annotations

import inspect
import json

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v2_qualification as q


def failed_runner(bob, syndrome, **kwargs):
    return {"status": "decode_failed", "reason": "fixture", "iterations": 1}


def integrity_runner(bob, syndrome, **kwargs):
    return {"status": "decoder_error", "reason": "fixture-integrity", "iterations": 1}


def success_runner(bob, syndrome, **kwargs):
    return {"status": "syndrome_consistent", "decoded_symbols": bob, "iterations": 1}


def test_plan_is_exact_unique_plan_only_and_path_locked(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(q, "production_runner", lambda *a, **k: calls.append(1))
    out = tmp_path / "plan"
    plan = q.create_plan(out, _test_only=True)
    assert calls == [] and {p.name for p in out.iterdir()} == {"pre_run_plan.json"}
    assert plan["canonical_schema"] == "NBLDPCQ2"
    assert len(plan["development_toeplitz_seeds"]) == 1152
    assert len(plan["confirmation_toeplitz_seeds"]) == 64
    ids = [x["seed_id"] for group in ("development_toeplitz_seeds", "confirmation_toeplitz_seeds")
           for x in plan[group].values()]
    assert len(ids) == len(set(ids)) and q.verify(out, _test_only=True)["plan_only"]
    with pytest.raises(FileExistsError):
        q.create_plan(out, _test_only=True)
    with pytest.raises(ValueError, match="official"):
        q.create_plan(tmp_path / "not-official")


def test_prior_seed_overlap_fails_before_creating_directory(tmp_path, monkeypatch):
    counter = iter(range(2000))
    monkeypatch.setattr(q, "materialize_seed_record",
                        lambda bits: {"seed_id": f"id-{next(counter)}", "seed_hex": "00" * 88, "seed_bit_length": bits})
    monkeypatch.setattr(q, "_prior_seed_ids", lambda **kwargs: {"id-0"})
    out = tmp_path / "overlap"
    with pytest.raises(ValueError, match="overlap"):
        q.create_plan(out, _test_only=True)
    assert not out.exists()


def test_readiness_stop_retains_all_development_and_no_confirmation(tmp_path):
    out = tmp_path / "stop"
    q.create_plan(out, _test_only=True)
    q.run(out, runner=failed_runner, _test_only=True)
    result = q.verify(out, verifier_runner=failed_runner, _test_only=True)
    assert result["run_status"] == "non_promoted_development" and not result["promoted"]
    rows = q._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 1152 and {x["qualification_role"] for x in rows} == {"development"}
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert all(g["denominator_included"] == 0 for g in report["promotion_gates"].values())
    manifest = json.loads((out / "formal_run_manifest.json").read_text())
    manifest["run_status"] = "completed"
    (out / "formal_run_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    report["run_status"] = "completed"
    report["formal_run_manifest_sha256"] = q._sha((out / "formal_run_manifest.json").read_bytes())
    (out / "formal_qualification_report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    with pytest.raises(ValueError, match="report gates"):
        q.verify(out, verifier_runner=failed_runner, _test_only=True)


def test_promotion_denominators_replay_tamper_and_worktree_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(q, "verify_nonbinary_symbols", lambda *a, **k: {"verified": True})
    out = tmp_path / "promote"
    q.create_plan(out, _test_only=True)
    q.run(out, runner=success_runner, _test_only=True)
    result = q.verify(out, verifier_runner=success_runner, _test_only=True)
    assert result["promoted"] and result["worktree_diagnostic"]
    real_provenance = q._provenance()
    drift = json.loads(json.dumps(real_provenance))
    drift["git"]["status_porcelain_v1_sha256"] = "f" * 64
    monkeypatch.setattr(q, "_provenance", lambda: drift)
    assert q.verify(out, verifier_runner=success_runner, _test_only=True)["verified"]
    scoped = json.loads(json.dumps(real_provenance))
    scoped["source_sha256"]["nonbinary_v2.py"] = "0" * 64
    monkeypatch.setattr(q, "_provenance", lambda: scoped)
    with pytest.raises(ValueError, match="scoped provenance"):
        q.verify(out, verifier_runner=success_runner, _test_only=True)
    monkeypatch.setattr(q, "_provenance", lambda: real_provenance)
    rows = q._rows(out / "formal_frame_outcomes.csv")
    assert len(rows) == 1216
    report = json.loads((out / "formal_qualification_report.json").read_text())
    assert all(g["denominator_included"] == 32 and g["verified_success"] == 32
               for g in report["promotion_gates"].values())

    # Coherent artifact rehashing is insufficient: deterministic replay rejects it.
    text = (out / "formal_frame_outcomes.csv").read_text()
    (out / "formal_frame_outcomes.csv").write_text(text.replace("verified_success", "verify_failed", 1))
    manifest = json.loads((out / "formal_run_manifest.json").read_text())
    manifest["artifacts"] = q._artifact_hashes(out)
    (out / "formal_run_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    report["formal_run_manifest_sha256"] = q._sha((out / "formal_run_manifest.json").read_bytes())
    (out / "formal_qualification_report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    with pytest.raises(ValueError, match="development CSV"):
        q.verify(out, verifier_runner=success_runner, _test_only=True)


def test_runner_and_cli_expose_no_truth_or_arbitrary_output():
    parameters = inspect.signature(q.production_runner).parameters
    assert not any(word in name.lower() for name in parameters for word in ("alice", "truth"))
    cli = (q._root() / "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v2_qualification.py").read_text()
    assert "--output-dir" not in cli


def test_complete_cap_rows_are_denominator_included_and_finalizer_is_verifiable(tmp_path):
    plan = q.expected_plan()
    frame = next(x for x in plan["frames"] if x["role"] == "confirmation")
    policy = next(x for x in plan["policies"] if all(s["check_count"] is not None for s in x["strata"]))
    cb, matrices = q.build_nbldpc_v2_codebook()
    row, events = q._cap(frame, policy, plan["confirmation_toeplitz_seeds"][frame["frame_id"]], cb, matrices)
    assert row["status"] == "aborted_resource_limit" and row["denominator_included"]
    assert row["key_dependent_disclosure_bits_total"] == row["check_count"] * 10
    assert events[-1]["payload"]["reason"] == "complete_run_s"

    out = tmp_path / "invalid"
    q.create_plan(out, _test_only=True)
    ticks = iter((0.0, 21601.0))
    with pytest.raises(TimeoutError):
        q.run(out, runner=failed_runner, clock=lambda: next(ticks, 21601.0), _test_only=True)
    result = q.verify(out, verifier_runner=failed_runner, _test_only=True)
    assert result["run_status"] == "invalid_run" and not result["promoted"]
    locked = json.loads((out / "pre_run_plan.json").read_text())
    first_policy = locked["policies"][0]
    first_id = locked["development_execution_order"][0]
    first_frame = next(x for x in locked["frames"] if x["frame_id"] == first_id)
    n1, n1_matrices = q.build_nonbinary_codebook_family(q.Q)
    forged_row, forged_events = q._one(
        first_frame, first_policy,
        locked["development_toeplitz_seeds"][first_policy["policy_sha256"] + "|" + first_id],
        success_runner, n1, n1_matrices, lambda: 0.0,
    )
    q._csv(out / "forged.csv", [forged_row])
    (out / "formal_frame_outcomes.csv").write_bytes((out / "forged.csv").read_bytes())
    (out / "forged.csv").unlink()
    (out / "formal_transcript.jsonl").write_bytes(b"".join(q.canonical_event(x) for x in forged_events))
    invalid_manifest = json.loads((out / "formal_run_manifest.json").read_text())
    invalid_manifest["artifacts"] = q._artifact_hashes(out)
    (out / "formal_run_manifest.json").write_text(json.dumps(invalid_manifest, sort_keys=True, indent=2) + "\n")
    invalid_report = json.loads((out / "formal_qualification_report.json").read_text())
    invalid_report["formal_run_manifest_sha256"] = q._sha((out / "formal_run_manifest.json").read_bytes())
    (out / "formal_qualification_report.json").write_text(json.dumps(invalid_report, sort_keys=True, indent=2) + "\n")
    with pytest.raises(ValueError, match="invalid partial replay"):
        q.verify(out, verifier_runner=failed_runner, _test_only=True)


def test_integrity_status_is_ineligible_and_exact_no_eligible_selection():
    grid = q.policy_grid()
    rows = {}
    for policy in grid:
        rows[policy["policy_sha256"]] = [
            {"stratum_p": p, "status": "verified_success", "key_dependent_disclosure_bits_total": 1, "iterations": 1}
            for p in q.PS for _ in range(24)
        ]
    eligible = next(p for p in grid if all(s["check_count"] is not None for s in p["strata"]))
    rows[eligible["policy_sha256"]][0]["status"] = "decoder_error"
    selected = q._select(rows, grid)
    assert selected["selected_policy_sha256"] != eligible["policy_sha256"]
    for values in rows.values():
        values[0]["status"] = "unsupported_domain"
    assert q._select(rows, grid) == {
        "selected_policy": None, "selected_policy_sha256": None,
        "selection_key": None, "reason": "no_eligible_policy",
    }


@pytest.mark.parametrize("field", ["source_sha256", "cli_sha256", "candidate_manifest_sha256", "contract_sha256", "commit"])
def test_scoped_provenance_fields_gate_but_status_drift_does_not(field):
    stored = q._provenance()
    live = json.loads(json.dumps(stored))
    if field == "commit":
        live["git"]["commit"] = "different"
    elif field == "source_sha256":
        live[field]["nonbinary_v2.py"] = "0" * 64
    else:
        live[field] = "0" * 64
    with pytest.raises(ValueError):
        q._verify_provenance(stored, live)
    diagnostic = json.loads(json.dumps(stored))
    diagnostic["git"]["status_porcelain_v1_sha256"] = "f" * 64
    diagnostic["git"]["dirty"] = not diagnostic["git"]["dirty"]
    q._verify_provenance(stored, diagnostic)


def _convert_to_invalid_package(out):
    manifest = {"run_id": q.RUN_ID, "run_status": "invalid_run",
                "reason": "OSError: injected after policy write",
                "artifacts": q._artifact_hashes(out)}
    (out / "formal_run_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    report = {"run_id": q.RUN_ID, "run_status": "invalid_run", "promoted": False,
              "formal_run_manifest_sha256": q._sha((out / "formal_run_manifest.json").read_bytes())}
    (out / "formal_qualification_report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")


def test_invalid_package_accepts_only_reconstructed_no_eligible_null_selection(tmp_path):
    no_eligible = tmp_path / "no-eligible"
    q.create_plan(no_eligible, _test_only=True)
    q.run(no_eligible, runner=integrity_runner, _test_only=True)
    policy = json.loads((no_eligible / "formal_policy_manifest.json").read_text())
    assert policy["selection"] == {
        "selected_policy": None, "selected_policy_sha256": None,
        "selection_key": None, "reason": "no_eligible_policy",
    }
    _convert_to_invalid_package(no_eligible)
    assert q.verify(no_eligible, verifier_runner=integrity_runner, _test_only=True)["run_status"] == "invalid_run"

    eligible = tmp_path / "eligible"
    q.create_plan(eligible, _test_only=True)
    q.run(eligible, runner=failed_runner, _test_only=True)
    forged = json.loads((eligible / "formal_policy_manifest.json").read_text())
    forged["selection"] = policy["selection"]
    forged["selected_policy_sha256"] = None
    forged["readiness"] = False
    (eligible / "formal_policy_manifest.json").write_text(json.dumps(forged, sort_keys=True, indent=2) + "\n")
    _convert_to_invalid_package(eligible)
    with pytest.raises(ValueError, match="invalid policy selection"):
        q.verify(eligible, verifier_runner=failed_runner, _test_only=True)
