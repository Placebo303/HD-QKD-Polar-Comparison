"""V13 diagnostic engineering tests DT0/DT1/DT2 + D04-lane DT3 + D05-lane DT4
+ R3-candidate IT0-IT3 (``formal-nonbinary-ldpc-v13-existing-data-diagnostics``).

- **DT0** compile/import, structural checks, tiny GF/syndrome math, oracle
  limits and the D02 engineering oracle;
- **DT1** role-ledger reconstruction, Alice isolation, and telemetry
  hook-equivalence (hook-off == original; hook-on does not change decoded
  word, status, or iterations);
- **DT2** a complete fake diagnostic lifecycle and decoder-free replay in a
  fresh ``workspace/nbldpc_v13_<uuid>/`` root, proving tests cannot enter a
  real source loader, a production decoder by default, or an official output
  root;
- **DT3** the D04 baseline-probe lane with fake frames: deterministic
  pre-registration, fake lifecycle + read-only verify, authorization
  tamper rejection, Alice-information boundary and no-overwrite;
- **DT4** the D05 root-cause lane: frozen-graph analysis, structural ceiling
  with perfect correspondence, the frozen decision table (pure function) and
  fake D05 lifecycle + verify;
- **IT0-IT3** the R3 code-only candidate (`nbldpc_v13_r3_code_v1`) and the
  E01 development-screen lane: deterministic codebook gates, pre-registration
  disjointness, explicit fake runners, fake + real-tiny E01 lifecycles and
  read-only verify, official-root and frozen-dir hygiene.

All frames and locks are synthetic; no real sidecar, no real source loader and
no official output root is ever touched.
"""
from __future__ import annotations

import csv
import hashlib
import inspect
import json
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v13_diagnostics as core,
)


def _hex64(seed_text: str) -> str:
    return hashlib.sha256(seed_text.encode("ascii")).hexdigest()


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v13_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _fake_identity_rows(per_stratum: int = 8, seed_prefix: str = "fake") -> list[dict]:
    rows: list[dict] = []
    for st in core.STRATA:
        for i in range(per_stratum):
            rows.append({"stratum": st, "frame_id": i,
                         "frame_identity": _hex64(f"{seed_prefix}|{st}|frame|{i}"),
                         "payload_identity": _hex64(f"{seed_prefix}|{st}|payload|{i}"),
                         "source_pair_start": i * 256, "source_pair_end": (i + 1) * 256,
                         "source_record_sha256": _hex64(f"{seed_prefix}|{st}|src")})
    return rows


def _fake_roles(pool: list[dict], *, n_transfer: int = 2, n_conf: int = 2,
                n_dev: int = 4) -> tuple[list[dict], list[dict]]:
    """Split a fake pool into V4-transfer and V5-partition role rows.  Rows
    beyond the first ``n_transfer+n_conf+n_dev`` per stratum stay unassigned
    (used to provoke ``blocked_role_ledger``)."""
    transfer: list[dict] = []
    partition: list[dict] = []
    for st in core.STRATA:
        st_rows = [r for r in pool if r["stratum"] == st]
        if len(st_rows) < n_transfer + n_conf + n_dev:
            raise ValueError("fake role split does not cover the stratum")
        covered = st_rows[:n_transfer + n_conf + n_dev]
        transfer += covered[:n_transfer]
        for rank, row in enumerate(covered[n_transfer:n_transfer + n_conf]):
            partition.append({**row, "role": "confirmation", "partition_rank": rank})
        for rank, row in enumerate(covered[n_transfer + n_conf:]):
            partition.append({**row, "role": "development", "partition_rank": 128 + rank})
    return transfer, partition


def _fake_ledger(seed_prefix: str = "fake", *, extra_pool_rows: int = 0) -> dict:
    pool = _fake_identity_rows(seed_prefix=seed_prefix)
    if extra_pool_rows:
        for i in range(extra_pool_rows):
            pool.append({"stratum": "d1024_bw200", "frame_id": 100 + i,
                         "frame_identity": _hex64(f"{seed_prefix}|extra|frame|{i}"),
                         "payload_identity": _hex64(f"{seed_prefix}|extra|payload|{i}"),
                         "source_pair_start": (100 + i) * 256,
                         "source_pair_end": (101 + i) * 256,
                         "source_record_sha256": _hex64(f"{seed_prefix}|extra|src")})
    transfer, partition = _fake_roles(pool)
    return core.build_role_ledger(pool, transfer, partition,
                                  schema=core.LEDGER_SCHEMA_TEST,
                                  run_id="fake_v13_test",
                                  identity_sources=[
                                      {"name": "fake_v4_v1", "lock_file": "real_data_lock.json",
                                       "path": "workspace/fake_v4_v1.json", "schema": "x",
                                       "row_count": len(transfer)},
                                      {"name": "fake_v5_partition", "lock_file": "partition_lock.json",
                                       "path": "workspace/fake_v5.json", "schema": "y",
                                       "row_count": len(partition)}])


def _fake_frames(ledger: dict, *, seed: int = 20260814) -> list[dict]:
    rows = [r for r in ledger["rows"] if r["role"] == "characterization"
            and r["stratum"] == core.PRIMARY_STRATUM]
    rng = np.random.default_rng(seed)
    frames: list[dict] = []
    for row in rows:
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "role": "characterization",
                       "alice": rng.integers(0, 1024, size=256),
                       "bob": rng.integers(0, 1024, size=256)})
    return frames


def _codebook():
    return core.v7_cb.build_nbldpc_v7_r1a_codebook()


# ------------------------------------------------------------------ DT0

def test_dt0_module_imports_do_not_load_decoder_or_source():
    assert "nonbinary_v7_r1a_long" not in sys.modules
    assert "ldpc_v4_10db_source" not in sys.modules
    assert "nonbinary_v7_r1a_long" not in sys.modules
    assert core.ARTIFACTS == ("data_role_ledger.json", "channel_diagnostics.json",
                              "diagnostic_outcomes.csv", "decoder_telemetry.jsonl",
                              "root_cause_report.json", "diagnostic_run_manifest.json")


def test_dt0_structural_constants():
    assert set(core.RUN_STATES) == {
        "plan_only", "blocked_role_ledger", "implementation_interface_fault",
        "diagnosis_complete", "diagnosis_inconclusive", "failed_existing_data_feasibility",
        "retrospective_non_ready", "ready_for_fresh_confirmation",
        "invalid_diagnostic_execution"}
    assert set(core.DIAGNOSIS_CLASSES) == {"interface", "prior", "decoder", "code",
                                           "mixed", "inconclusive"}
    assert core.ROLES == ("characterization", "development", "retrospective_audit")
    assert core.PRIMARY_STRATUM == "d1024_bw200"
    assert (core.Q, core.N, core.M) == (1024, 256, 170)
    # the frozen V7 R1A binding is never re-searched
    assert core.V7_R1A_FROZEN["manifest_id"] == \
        "93267fc5f069c4189c358342f7fbd7981f7b0093d577784b7eb231a177f66ad8"
    assert core.V7_R1A_FROZEN["canonical_sha256"] == \
        "75f625bbbe1ebd74b0cf8b0b3646fa1af9ce6e5a66562e07a75507d175570608"
    assert core.V7_R1A_FROZEN["construction_seed"] == 2026080400
    assert core.V7_R1A_FROZEN["check_degree_histogram"] == {"3": 168, "4": 2}


def test_dt0_tiny_gf_math():
    field = core.GF2mField.create(4)
    assert field.q == 4 and field.m == 2
    assert field.add(3, 1) == 2 and field.mul(3, 2) == 1
    assert field.inverse(3) == 2 and field.mul(3, field.inverse(3)) == 1
    assert all(core._check_field_tiny(q)["identities"] for q in (2, 4, 8, 16))
    assert all(core._check_field_tiny(q)["inverses"] for q in (2, 4, 8, 16))
    assert all(core._check_field_tiny(q)["distributivity"] for q in (2, 4, 8, 16))


def test_dt0_tiny_syndrome_matches_brute_force():
    check = core._check_tiny_syndrome()
    assert check["ok"] is True and check["failures"] == []
    q, n, m = 4, 4, 2
    field = core.GF2mField.create(q)
    matrix = ((1, 2, 0, 3), (3, 0, 1, 2))
    from itertools import product
    for word in product(range(q), repeat=n):
        assert core.nonbinary_syndrome(matrix, word, field) == \
            core._brute_force_syndrome(matrix, word, field)


def test_dt0_gray_mapping_roundtrip():
    gray = core._check_gray_mapping()
    assert gray["ok"] is True and gray["failures"] == []
    for value in range(1024):
        assert core._gray_decode(int(core.gray_encode(np.asarray([value]))[0])) == value


def test_dt0_engineering_oracle_passes():
    result = core.run_engineering_oracle()
    assert result["status"] == "ok"
    assert result["diagnosis_class"] is None and result["run_state"] is None
    assert result["failed_checks"] == []
    assert result["checks"]["wrapper_contract"]["ok"] is True
    assert result["checks"]["wrapper_contract"]["matrix_shape"] == (170, 256)
    assert result["checks"]["tiny_syndrome"]["ok"] is True


def test_dt0_engineering_oracle_limits_fail_closed():
    # an unsupported GF(q) makes the oracle fail closed to interface fault
    result = core.run_engineering_oracle(tiny_q=(3,))
    assert result["status"] == "failed"
    assert result["diagnosis_class"] == "interface"
    assert result["run_state"] == "implementation_interface_fault"
    assert "field_q3" in result["failed_checks"]


def test_dt0_wrapper_contract_reconstruction():
    manifest, matrix = _codebook()
    assert core.v7_cb.verify_nbldpc_v7_r1a_codebook(manifest, matrix)["status"] == "ok"
    assert core.V7_R1A_FROZEN["manifest_id"] == manifest["manifest_id"]
    assert core.V7_R1A_FROZEN["canonical_sha256"] == manifest["canonical_sha256"]


# ------------------------------------------------------------------ DT1

def test_dt1_role_ledger_reconstruction_ready():
    ledger = _fake_ledger()
    core.validate_role_ledger(ledger)
    assert ledger["ledger_state"] == "ready"
    assert ledger["counts"]["total_rows"] == 24
    assert ledger["counts"]["by_role"] == {"characterization": 6, "development": 12,
                                           "retrospective_audit": 6}
    for st in core.STRATA:
        assert ledger["counts"]["by_stratum_role"][st] == \
            {"characterization": 2, "development": 4, "retrospective_audit": 2}
    roles = [r["role"] for r in ledger["rows"]]
    assert roles.count("characterization") == 6
    assert roles.count("development") == 12
    assert roles.count("retrospective_audit") == 6
    # every row carries the full identity contract
    for row in ledger["rows"]:
        assert row["stratum"] in core.STRATA and isinstance(row["frame_id"], int)
        assert len(row["frame_identity"]) == 64 and len(row["payload_identity"]) == 64
        assert row["role"] in core.ROLES and isinstance(row["source_path"], str)
        assert row["provenance"]["role_source"] in (
            "v4_10db_transfer_lock", "v5_partition_confirmation", "v5_partition_development")


def test_dt1_role_ledger_mutual_exclusivity():
    ledger = _fake_ledger()
    by_frame: dict[str, list[str]] = {}
    for row in ledger["rows"]:
        by_frame.setdefault(row["frame_identity"], []).append(row["role"])
    assert all(len(v) == 1 for v in by_frame.values())
    assert len(by_frame) == len(ledger["rows"])


def test_dt1_role_ledger_blocked_on_unassigned_row():
    ledger = _fake_ledger(extra_pool_rows=1)
    assert ledger["ledger_state"] == "blocked_role_ledger"
    assert ledger["rows"] == []
    assert any("unassigned" in reason for reason in ledger["block_reasons"])


def test_dt1_role_ledger_blocked_on_overlap():
    pool = _fake_identity_rows()
    transfer, partition = _fake_roles(pool)
    # force a v4-transfer identity into the v5 development role
    partition = partition + [dict(transfer[0], role="development", partition_rank=999)]
    ledger = core.build_role_ledger(pool, transfer, partition,
                                    schema=core.LEDGER_SCHEMA_TEST, run_id="fake")
    assert ledger["ledger_state"] == "blocked_role_ledger"
    assert any("overlap" in reason for reason in ledger["block_reasons"])


def test_dt1_alice_isolation_signatures():
    # Alice truth never reaches the decoder control / prior / stopping paths:
    # the hook wrapper, the hooked loop and the preprocessing all expose no
    # alice parameter.
    for function in (core.run_diagnostic_hook, core._hooked_decode_flooding,
                     core._decode_preprocessing):
        parameters = set(inspect.signature(function).parameters)
        assert "alice" not in parameters
        assert "alice_symbols" not in parameters
        assert "error_locations" not in parameters
    parameters = set(inspect.signature(core.run_diagnostic_hook).parameters)
    assert {"bob_symbols", "syndrome", "manifest", "matrices", "check_count", "p"} \
        <= parameters


def _hook_frame(*, seed: int = 7, noiseless: bool = False):
    cb, mats = _codebook()
    field = core.GF2mField.create(core.Q)
    rng = np.random.default_rng(seed)
    alice = rng.integers(0, core.Q, size=core.N)
    bob = alice.copy()
    if not noiseless:
        positions = rng.choice(core.N, size=13, replace=False)
        bob[positions] = rng.integers(0, core.Q, size=13)
    syndrome = core.nonbinary_syndrome(mats, alice, field)
    return bob, syndrome, cb, mats


def test_dt1_telemetry_hook_equivalence():
    bob, syndrome, cb, mats = _hook_frame()
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_long as v7_long
    direct = v7_long.decode_nbldpc_v7_r1a(bob, syndrome, cb, mats, check_count=170,
                                          p=0.20, max_iter=3)
    off = core.run_diagnostic_hook(bob, syndrome, cb, mats, check_count=170, p=0.20,
                                   max_iter=3, hook=False)
    on = core.run_diagnostic_hook(bob, syndrome, cb, mats, check_count=170, p=0.20,
                                  max_iter=3, hook=True)
    # hook-off is element-for-element identical to the original return
    assert off["result"] == direct
    assert off["telemetry"] is None
    # hook-on does not change decoded word, status, iterations or any field
    assert on["result"] == direct
    telemetry = on["telemetry"]
    assert telemetry["final_status"] == direct["status"]
    assert telemetry["final_iterations"] == direct["iterations"]
    for entry in telemetry["per_iteration"]:
        assert set(entry) == core._TELEMETRY_PER_ITERATION_KEYS
    assert not (core._TELEMETRY_FORBIDDEN_KEYS & set(telemetry))
    assert telemetry["normalisation_calls_total"] > 0


def test_dt1_telemetry_hook_noiseless_converges_without_raw_data():
    bob, syndrome, cb, mats = _hook_frame(noiseless=True)
    on = core.run_diagnostic_hook(bob, syndrome, cb, mats, check_count=170, p=0.20,
                                  max_iter=3, hook=True)
    assert on["result"]["status"] == "syndrome_consistent"
    assert on["result"]["iterations"] == 1
    telemetry = on["telemetry"]
    assert len(telemetry["per_iteration"]) == 1
    assert telemetry["per_iteration"][0]["satisfied_checks"] == 170
    assert telemetry["per_iteration"][0]["unsatisfied_checks"] == 0
    # telemetry contains no decoded word / error locations / raw arrays
    assert "decoded_symbols" not in telemetry and "error_positions" not in telemetry
    assert not (core._TELEMETRY_FORBIDDEN_KEYS & set(telemetry))


def test_dt1_hook_equivalence_for_decode_failed_frame():
    # a frame with many errors and few iterations terminates as decode_failed;
    # hook-on still matches hook-off element-for-element.
    cb, mats = _codebook()
    field = core.GF2mField.create(core.Q)
    rng = np.random.default_rng(99)
    alice = rng.integers(0, core.Q, size=core.N)
    bob = rng.integers(0, core.Q, size=core.N)  # ~90% raw error, cannot converge
    syndrome = core.nonbinary_syndrome(mats, alice, field)
    off = core.run_diagnostic_hook(bob, syndrome, cb, mats, check_count=170, p=0.20,
                                   max_iter=2, hook=False)
    on = core.run_diagnostic_hook(bob, syndrome, cb, mats, check_count=170, p=0.20,
                                  max_iter=2, hook=True)
    assert on["result"] == off["result"]
    assert on["result"]["status"] == "decode_failed"
    assert on["result"]["iterations"] == 2
    assert on["telemetry"]["final_status"] == "decode_failed"


# ------------------------------------------------------------------ DT2

def test_dt2_production_entrypoints_hard_stopped():
    with pytest.raises(ValueError, match="production D01 characterization is not authorized"):
        core.run_d01(Path("workspace") / "must_not_exist",
                     run_id="fake", discovery_root=Path("workspace"),
                     production_authorized=False)
    with pytest.raises(ValueError, match="production D04 baseline probe is not authorized"):
        core.run_d04(Path("workspace") / "must_not_exist",
                     run_id="fake", discovery_root=Path("workspace"),
                     production_authorized=False)
    # both D04 and D05 require the explicit main-thread authorization flag
    with pytest.raises(SystemExit) as excinfo:
        core.v13_d04_d05_guard("d05", False)
    assert excinfo.value.code == 2
    with pytest.raises(SystemExit) as excinfo:
        core.v13_d04_d05_guard("d04", False)
    assert excinfo.value.code == 2
    # the authorized lanes are implemented (module API; test lane below)
    assert core.v13_d04_d05_guard("d05", True) is None
    assert core.v13_d04_d05_guard("d04", True) is None


def test_dt2_complete_fake_lifecycle_and_replay():
    root = _out("t2")
    ledger = _fake_ledger()
    frames = _fake_frames(ledger)
    run_dir = root / "package"
    result = core.run_d01(run_dir, run_id="fake_v13_d01", ledger=ledger, frames=frames,
                          _test_only=True, command="pytest DT2")
    assert result["run_state"] == "plan_only"
    assert result["ledger_state"] == "ready"
    assert {p.name for p in run_dir.iterdir()} == set(core.ARTIFACTS)
    # decoder-free read-only verification of the written package
    from comparison_bench.src.comparison_bench.cli.verify_nonbinary_v13_diagnostics import (
        verify_output)
    verified = verify_output(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "plan_only"
    assert verified["ledger_counts"]["total_rows"] == 24
    assert verified["characterization_performed"] is True
    # the test root lives under workspace, never under the official output root
    assert str(run_dir.resolve()).startswith(str(Path("workspace").resolve()))
    # decoder-free replay: recomputing the aggregates reproduces the package
    channel = json.loads((run_dir / "channel_diagnostics.json").read_bytes())
    replayed = core.channel_aggregates(frames)
    assert replayed == channel["aggregates"]
    # no production package directory was created by this lifecycle (the only
    # package root written is the fresh workspace root above)


def test_dt2_blocked_ledger_package_and_verify():
    root = _out("t2_blocked")
    ledger = _fake_ledger(extra_pool_rows=1)
    assert ledger["ledger_state"] == "blocked_role_ledger"
    run_dir = root / "package"
    result = core.run_d01(run_dir, run_id="fake_v13_blocked", ledger=ledger,
                          frames=[], _test_only=True, command="pytest DT2")
    assert result["run_state"] == "blocked_role_ledger"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["ledger_state"] == "blocked_role_ledger"
    assert verified["characterization_performed"] is False


def test_dt2_oracle_failure_package_is_interface_fault(monkeypatch):
    root = _out("t2_interface")
    ledger = _fake_ledger()

    def broken_oracle(*args, **kwargs):
        return {"status": "failed", "diagnosis_class": "interface",
                "run_state": "implementation_interface_fault",
                "failed_checks": ["forced"], "checks": {}}

    monkeypatch.setattr(core, "run_engineering_oracle", broken_oracle)
    run_dir = root / "package"
    result = core.run_d01(run_dir, run_id="fake_v13_ifault", ledger=ledger,
                          frames=_fake_frames(ledger), _test_only=True,
                          command="pytest DT2")
    assert result["run_state"] == "implementation_interface_fault"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "implementation_interface_fault"
    assert verified["characterization_performed"] is False
    # the D02 oracle failure stops before any characterization
    report = json.loads((run_dir / "root_cause_report.json").read_bytes())
    assert report["diagnosis_class"] is None and report["d05_emitted"] is False


def test_dt2_tests_cannot_enter_real_loader_decoder_or_official_root():
    # importing and verifying never pulls in the decoder or the real source
    # loader, and the fake lifecycle writes only under fresh workspace roots.
    assert "nonbinary_v7_r1a_long" not in sys.modules
    assert "ldpc_v4_10db_source" not in sys.modules
    source = Path(core.__file__).read_text(encoding="utf8")
    assert source.count("nonbinary_v7_r1a_long") >= 1  # lazy import exists
    # neither the decoder nor the real source loader is ever imported at
    # module level (top-level lines); both are lazy inside execute-only paths
    top_level = [line for line in source.splitlines()
                 if (line.startswith("from . import nonbinary_v7_r1a_long")
                     or line.startswith("import nonbinary_v7_r1a_long")
                     or line.startswith("from . import ldpc_v4_10db_source")
                     or line.startswith("import ldpc_v4_10db_source"))]
    assert top_level == []


# ------------------------------------------------------------------ DT3 (D04 baseline-probe lane)

def _fake_ledger_large(*, per_stratum: int = 40, n_dev: int = 36) -> dict:
    """Fake ledger with >=32 development rows in every stratum (D04 needs 32
    bw200 development frames)."""
    pool = _fake_identity_rows(per_stratum=per_stratum)
    transfer, partition = _fake_roles(pool, n_transfer=2, n_conf=2, n_dev=n_dev)
    return core.build_role_ledger(pool, transfer, partition,
                                  schema=core.LEDGER_SCHEMA_TEST,
                                  run_id="fake_v13_d04_test",
                                  identity_sources=[
                                      {"name": "fake_v4_v1", "lock_file": "real_data_lock.json",
                                       "path": "workspace/fake_v4_v1.json", "schema": "x",
                                       "row_count": len(transfer)},
                                      {"name": "fake_v5_partition", "lock_file": "partition_lock.json",
                                       "path": "workspace/fake_v5.json", "schema": "y",
                                       "row_count": len(partition)}])


def _fake_d04_frames(ledger: dict, rows: list[dict], *, seed: int = 20260815,
                     noise_frames: int = 2) -> list[dict]:
    rng = np.random.default_rng(seed)
    frames: list[dict] = []
    for index, row in enumerate(rows):
        alice = rng.integers(0, core.Q, size=core.N)
        bob = alice.copy()
        if index < noise_frames:
            positions = rng.choice(core.N, size=20, replace=False)
            bob[positions] = rng.integers(0, core.Q, size=20)
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "role": "development", "frame_identity": row["frame_identity"],
                       "alice": alice, "bob": bob})
    return frames


def test_dt3_d04_pre_registration_deterministic_and_disjoint():
    ledger = _fake_ledger_large()
    first = core.pre_registered_d04_frames(ledger)
    second = core.pre_registered_d04_frames(ledger)
    assert [r["frame_id"] for r in first] == [r["frame_id"] for r in second]
    assert len(first) == core.D04_FRAME_COUNT == 32
    assert all(r["role"] == "development" and r["stratum"] == core.PRIMARY_STRATUM
               for r in first)
    ids = [r["frame_id"] for r in first]
    assert ids == sorted(ids)
    # disjoint from the sealed audit frames by role construction
    audit_ids = {r["frame_id"] for r in ledger["rows"]
                 if r["role"] == "retrospective_audit"}
    assert not (set(ids) & audit_ids)
    # insufficient development rows fail closed
    with pytest.raises(ValueError, match="insufficient development rows"):
        core.pre_registered_d04_frames(_fake_ledger())


def test_dt3_d04_fake_lifecycle_and_verify():
    root = _out("t3_d04")
    ledger = _fake_ledger_large()
    rows = core.pre_registered_d04_frames(ledger, count=4)
    frames = _fake_d04_frames(ledger, rows)
    run_dir = root / "package"
    result = core.run_d04(run_dir, run_id="fake_v13_d04", ledger=ledger, frames=frames,
                          count=4, max_iter=2, _test_only=True, command="pytest DT3")
    assert result["run_state"] == "plan_only"
    assert result["ledger_state"] == "ready"
    assert {p.name for p in run_dir.iterdir()} == set(core.ARTIFACTS)
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "plan_only"
    assert verified["outcome_rows"] == 4
    assert verified["telemetry_records"] == 4
    outcome = list(csv.DictReader(
        (run_dir / "diagnostic_outcomes.csv").read_text("utf-8").splitlines()))
    assert all(row["phase"] == "baseline" for row in outcome)
    assert all(row["method"] == core.V7_R1A_METHOD for row in outcome)
    assert all(row["stratum"] == core.PRIMARY_STRATUM and row["role"] == "development"
               for row in outcome)
    assert [int(row["frame_id"]) for row in outcome] == [int(f["frame_id"]) for f in frames]
    # the two noiseless frames must be exactly corrected; noisy frames are
    # retained as failures when the decoder cannot converge in 2 iterations
    assert sum(1 for row in outcome if row["reason"] == "exact_correct") >= 2
    assert all(row["status"] in ("syndrome_consistent", "decode_failed") for row in outcome)
    # manifest carries the D04-limited authorization and the baseline summary
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    assert manifest["authorization"] == {"d04_authorized": True, "d05_authorized": False,
                                         "real_decode_authorized": True,
                                         "phase": "V13-D04 baseline probe"}
    assert manifest["stages_completed"] == ["D04"]
    assert manifest["baseline"]["frames"] == 4
    assert manifest["baseline"]["frozen_binding"] == core.V7_R1A_FROZEN["manifest_id"]
    assert sum(manifest["baseline"]["status_counts"].values()) == 4
    # root-cause report carries no D05 conclusion
    report = json.loads((run_dir / "root_cause_report.json").read_bytes())
    assert report["d05_emitted"] is False and report["diagnosis_class"] is None
    assert str(run_dir.resolve()).startswith(str(Path("workspace").resolve()))


def test_dt3_d04_tampered_authorization_rejected():
    root = _out("t3_tamper")
    ledger = _fake_ledger_large()
    rows = core.pre_registered_d04_frames(ledger, count=4)
    frames = _fake_d04_frames(ledger, rows)
    run_dir = root / "package"
    core.run_d04(run_dir, run_id="fake_v13_d04_t", ledger=ledger, frames=frames,
                 count=4, max_iter=2, _test_only=True, command="pytest DT3")
    # a D04 package claiming real-decode authorization without the main-thread
    # D04 flag must fail read-only verification
    manifest_path = run_dir / "diagnostic_run_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["authorization"] = {"d04_authorized": False, "d05_authorized": False,
                                 "real_decode_authorized": True,
                                 "phase": "V13-D04 baseline probe"}
    manifest_path.write_bytes(core._compact(manifest))
    with pytest.raises(ValueError, match="manifest D04 authorization"):
        core.verify_package(run_dir, _private_test_only=True)
    # a D04 package with a D05 conclusion is rejected too
    manifest = json.loads(manifest_path.read_bytes())
    manifest["authorization"] = {"d04_authorized": True, "d05_authorized": False,
                                 "real_decode_authorized": True,
                                 "phase": "V13-D04 baseline probe"}
    manifest_path.write_bytes(core._compact(manifest))
    report_path = run_dir / "root_cause_report.json"
    report = json.loads(report_path.read_bytes())
    report["d05_emitted"] = True
    report_path.write_bytes(core._compact(report))
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifact_files"]["root_cause_report.json"]["bytes"] = \
        report_path.stat().st_size
    manifest_path.write_bytes(core._compact(manifest))
    with pytest.raises(ValueError, match="must not carry a D05 conclusion"):
        core.verify_package(run_dir, _private_test_only=True)


def test_dt3_d04_alice_only_in_syndrome_and_exact_check(monkeypatch):
    # Alice truth never reaches the decoder path: spy the hook and assert the
    # call carries bob + the disclosed syndrome only; persisted artifacts
    # contain no raw arrays.
    root = _out("t3_alice")
    ledger = _fake_ledger_large()
    rows = core.pre_registered_d04_frames(ledger, count=4)
    frames = _fake_d04_frames(ledger, rows)
    calls: list[dict] = []
    real_hook = core.run_diagnostic_hook

    def spy(bob_symbols, syndrome, manifest, matrices, *, check_count, p,
            schedule="flooding", max_iter=100, hook=True):
        calls.append({"bob": np.asarray(bob_symbols), "syndrome": tuple(syndrome)})
        return real_hook(bob_symbols, syndrome, manifest, matrices,
                         check_count=check_count, p=p, schedule=schedule,
                         max_iter=max_iter, hook=hook)

    monkeypatch.setattr(core, "run_diagnostic_hook", spy)
    run_dir = root / "package"
    core.run_d04(run_dir, run_id="fake_v13_d04_a", ledger=ledger, frames=frames,
                 count=4, max_iter=2, _test_only=True, command="pytest DT3")
    assert len(calls) == 4
    for call in calls:
        assert call["bob"].shape == (core.N,)
        assert len(call["syndrome"]) == core.M
    text = (run_dir / "diagnostic_outcomes.csv").read_text("utf-8")
    assert "alice" not in text.lower() and "bob" not in text.lower()
    telemetry = (run_dir / "decoder_telemetry.jsonl").read_text("utf-8")
    assert "alice" not in telemetry and "bob" not in telemetry
    assert "decoded_symbols" not in telemetry and "error_positions" not in telemetry


def test_dt3_d04_oracle_failure_package_frozen_and_verifiable(monkeypatch):
    # an oracle failure freezes the D04 package at interface fault with zero
    # baseline rows; the frozen package still verifies read-only
    root = _out("t3_d04_interface")
    ledger = _fake_ledger_large()
    rows = core.pre_registered_d04_frames(ledger, count=4)
    frames = _fake_d04_frames(ledger, rows)

    def broken_oracle(*args, **kwargs):
        return {"status": "failed", "diagnosis_class": "interface",
                "run_state": "implementation_interface_fault",
                "failed_checks": ["forced"], "checks": {}}

    monkeypatch.setattr(core, "run_engineering_oracle", broken_oracle)
    run_dir = root / "package"
    result = core.run_d04(run_dir, run_id="fake_v13_d04_if", ledger=ledger, frames=frames,
                          count=4, max_iter=2, _test_only=True, command="pytest DT3")
    assert result["run_state"] == "implementation_interface_fault"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "implementation_interface_fault"
    assert verified["outcome_rows"] == 0 and verified["telemetry_records"] == 0


def test_dt3_d04_no_overwrite_fresh_root():
    root = _out("t3_overwrite")
    run_dir = root / "package"
    run_dir.mkdir(parents=True)
    ledger = _fake_ledger_large()
    rows = core.pre_registered_d04_frames(ledger, count=4)
    frames = _fake_d04_frames(ledger, rows)
    with pytest.raises(FileExistsError, match="fresh additive output root required"):
        core.run_d04(run_dir, run_id="fake", ledger=ledger, frames=frames,
                     count=4, max_iter=2, _test_only=True, command="pytest DT3")


# ------------------------------------------------------------------ DT4 (D05 root-cause lane)

def test_dt4_graph_analysis_frozen_r1a_is_degenerate():
    graph = core.v7_r1a_graph_analysis()
    assert graph["codebook"]["method"] == core.V7_R1A_METHOD
    assert graph["variable_degree_distribution"] == {2: 256}
    assert graph["check_degree_distribution"] == {3: 168, 4: 2}
    census = graph["check_node_graph"]
    assert census["check_nodes"] == 170 and census["variable_edges"] == 256
    # the frozen graph is 85 disconnected 2-check components with parallel
    # variable edges -> Tanner girth 4 and component minimum distance <= 3
    assert census["component_count"] == 85
    assert census["component_sizes"] == [2] * 85
    assert census["parallel_pairs"] == 85
    assert graph["girth"]["tanner_girth"] == 4
    assert graph["minimum_distance"]["d_min_bound"] == 3
    assert graph["anomalies"] == []


def test_dt4_ceiling_perfect_correspondence():
    # fake frames: two of four have >=2 errors in one component; outcomes mark
    # exactly those two frames as failed -> perfect correspondence
    rows = _fake_identity_rows(per_stratum=4)
    transfer, partition = _fake_roles(rows, n_transfer=1, n_conf=1, n_dev=2)
    ledger = core.build_role_ledger(rows, transfer, partition,
                                    schema=core.LEDGER_SCHEMA_TEST,
                                    run_id="fake_v13_d05_test")
    dev_rows = [r for r in ledger["rows"] if r["role"] == "development"
                and r["stratum"] == core.PRIMARY_STRATUM]
    mapping = core.component_map()
    key = next(iter(sorted(set(mapping.values()))))
    frames = []
    for i, row in enumerate(dev_rows):
        alice = np.zeros(core.N, dtype=np.int64)
        bob = alice.copy()
        if i < 2:
            cols = [c for c in mapping if mapping[c] == key][:2]
            bob[cols[0]] = 1
            bob[cols[1]] = 2
        frames.append({"frame_id": int(row["frame_id"]),
                       "stratum": row["stratum"], "role": "development",
                       "alice": alice, "bob": bob})
    outcomes = [{"phase": "baseline", "method": core.V7_R1A_METHOD,
                 "frame_id": int(f["frame_id"]), "stratum": core.PRIMARY_STRATUM,
                 "role": "development",
                 "status": "decode_failed" if i < 2 else "syndrome_consistent",
                 "reason": "iteration_limit" if i < 2 else "exact_correct",
                 "raw_ser": 0.05, "iterations": 100 if i < 2 else 1,
                 "notes": "hook_equivalence=ok"}
                for i, f in enumerate(frames)]
    ceiling = core.structural_failure_ceiling(frames, outcomes=outcomes)
    assert ceiling["frames"] == 2
    assert ceiling["structural_failure_fraction"] == 1.0
    assert ceiling["perfect_correspondence"]["exact_match"] is True


def test_dt4_decision_table_emits_code_with_prior_co_factor():
    graph = core.v7_r1a_graph_analysis()
    evidence = {
        "oracle_status": "ok", "hook_equivalence_ok": True,
        "decoder_error_count": 0, "nonfinite_events": 0,
        "normalisation_failures": 0,
        "prior_calibration_mismatch": 0.1229, "prior_entropy_gap_bits": 2.17,
        "oscillation_frames": 11, "total_frames": 32,
        "graph": graph,
        "ceiling": {"structural_failure_fraction": 0.75,
                    "observed_failure_fraction": 0.75,
                    "observed_success_fraction": 0.25},
    }
    decision = core.decide_root_cause(evidence)
    assert decision["diagnosis_class"] == "code"
    assert decision["run_state"] == "diagnosis_complete"
    assert decision["prior_documented_co_factor"] is True


def test_dt4_decision_table_prior_when_graph_healthy():
    healthy = {"variable_degree_distribution": {3: 256},
               "check_degree_distribution": {6: 85},
               "check_node_graph": {"component_count": 1,
                                    "component_sizes": [170]},
               "girth": {"tanner_girth": 8, "check_graph_girth": 4},
               "minimum_distance": {"d_min_bound": 8}}
    evidence = {
        "oracle_status": "ok", "hook_equivalence_ok": True,
        "decoder_error_count": 0, "nonfinite_events": 0,
        "normalisation_failures": 0,
        "prior_calibration_mismatch": 0.1229, "prior_entropy_gap_bits": 2.17,
        "oscillation_frames": 0, "total_frames": 32,
        "graph": healthy,
        "ceiling": {"structural_failure_fraction": 0.05,
                    "observed_failure_fraction": 0.75},
    }
    decision = core.decide_root_cause(evidence)
    assert decision["diagnosis_class"] == "prior"
    assert decision["run_state"] == "diagnosis_complete"


def test_dt4_decision_table_prior_when_structure_does_not_explain():
    graph = core.v7_r1a_graph_analysis()
    evidence = {
        "oracle_status": "ok", "hook_equivalence_ok": True,
        "decoder_error_count": 0, "nonfinite_events": 0,
        "normalisation_failures": 0,
        "prior_calibration_mismatch": 0.1229, "prior_entropy_gap_bits": 2.17,
        "oscillation_frames": 0, "total_frames": 32,
        "graph": graph,
        "ceiling": {"structural_failure_fraction": 0.30,
                    "observed_failure_fraction": 0.75},
    }
    decision = core.decide_root_cause(evidence)
    # structure explains only 0.30 of 0.75 failures (< 0.8 share) -> the code
    # row is not established; the D01 prior mismatch row is -> prior
    assert decision["diagnosis_class"] == "prior"
    assert decision["run_state"] == "diagnosis_complete"


def test_dt4_decision_table_inconclusive_when_no_class_established():
    healthy = {"variable_degree_distribution": {3: 256},
               "check_degree_distribution": {6: 85},
               "check_node_graph": {"component_count": 1,
                                    "component_sizes": [170]},
               "girth": {"tanner_girth": 8, "check_graph_girth": 4},
               "minimum_distance": {"d_min_bound": 8}}
    evidence = {
        "oracle_status": "ok", "hook_equivalence_ok": True,
        "decoder_error_count": 0, "nonfinite_events": 0,
        "normalisation_failures": 0,
        "prior_calibration_mismatch": 0.01, "prior_entropy_gap_bits": 0.2,
        "oscillation_frames": 0, "total_frames": 32,
        "graph": healthy,
        "ceiling": {"structural_failure_fraction": 0.05,
                    "observed_failure_fraction": 0.75},
    }
    decision = core.decide_root_cause(evidence)
    assert decision["diagnosis_class"] == "inconclusive"
    assert decision["run_state"] == "diagnosis_inconclusive"


def test_dt4_decision_table_interface_on_oracle_failure():
    decision = core.decide_root_cause({"oracle_status": "failed"})
    assert decision["diagnosis_class"] == "interface"
    assert decision["run_state"] == "implementation_interface_fault"


def test_dt4_d05_fake_lifecycle_and_verify():
    root = _out("t4_d05")
    ledger = _fake_ledger_large()
    frames = _fake_frames(ledger, seed=5)
    dev_rows = core.pre_registered_d04_frames(ledger, count=4)
    dev_frames = _fake_d04_frames(ledger, dev_rows)
    outcomes = [{"phase": "baseline", "method": core.V7_R1A_METHOD,
                 "frame_id": int(f["frame_id"]), "stratum": core.PRIMARY_STRATUM,
                 "role": "development", "status": "decode_failed",
                 "reason": "iteration_limit", "raw_ser": 0.07,
                 "iterations": 100, "notes": "hook_equivalence=ok"}
                for f in dev_frames]
    graph = core.v7_r1a_graph_analysis()
    evidence = {
        "oracle_status": "ok", "hook_equivalence_ok": True,
        "decoder_error_count": 0, "nonfinite_events": 0,
        "normalisation_failures": 0,
        "prior_calibration_mismatch": 0.1229, "prior_entropy_gap_bits": 2.17,
        "oscillation_frames": 0, "total_frames": len(outcomes),
        "graph": graph,
        "ceiling": {"structural_failure_fraction": 0.75,
                    "observed_failure_fraction": 0.75},
    }
    run_dir = root / "package"
    result = core.run_d05(run_dir, run_id="fake_v13_d05", ledger=ledger,
                          frames=frames, dev_frames=dev_frames,
                          outcome_rows=outcomes, evidence=evidence,
                          _test_only=True, command="pytest DT4")
    assert result["run_state"] == "diagnosis_complete"
    assert {p.name for p in run_dir.iterdir()} == set(core.ARTIFACTS)
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "diagnosis_complete"
    assert verified["characterization_performed"] is True
    report = json.loads((run_dir / "root_cause_report.json").read_bytes())
    assert report["d05_emitted"] is True and report["diagnosis_concluded"] is True
    assert report["diagnosis_class"] == "code"
    assert report["run_state"] == "diagnosis_complete"
    assert report["successor"] == "R3 code-only"
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    assert manifest["stages_completed"] == ["D01", "D04", "D05"]
    assert manifest["authorization"]["d05_authorized"] is True
    assert manifest["baseline"]["frames"] == 4
    assert str(run_dir.resolve()).startswith(str(Path("workspace").resolve()))


def test_dt4_d05_oracle_freeze_package_verifies(monkeypatch):
    root = _out("t4_d05_interface")
    ledger = _fake_ledger_large()
    frames = _fake_frames(ledger, seed=6)

    def broken_oracle(*args, **kwargs):
        return {"status": "failed", "diagnosis_class": "interface",
                "run_state": "implementation_interface_fault",
                "failed_checks": ["forced"], "checks": {}}

    monkeypatch.setattr(core, "run_engineering_oracle", broken_oracle)
    run_dir = root / "package"
    result = core.run_d05(run_dir, run_id="fake_v13_d05_if", ledger=ledger,
                          frames=frames, _test_only=True, command="pytest DT4")
    assert result["run_state"] == "implementation_interface_fault"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "implementation_interface_fault"


# ------------------------------------------------------------------ IT0-IT3 (R3 candidate + E01 lane)

def _r3():
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v13_r3_candidate as r3)
    return r3


def _fake_ledger_r3(*, per_stratum: int = 104, n_dev: int = 100,
                    n_conf: int = 2) -> dict:
    """Fake ledger with >=96 development rows per stratum (D04 32 + E01 64);
    pool size == transfer 2 + confirmation n_conf + development n_dev."""
    pool = _fake_identity_rows(per_stratum=per_stratum)
    transfer, partition = _fake_roles(pool, n_transfer=2, n_conf=n_conf, n_dev=n_dev)
    return core.build_role_ledger(pool, transfer, partition,
                                  schema=core.LEDGER_SCHEMA_TEST,
                                  run_id="fake_v13_r3_test",
                                  identity_sources=[
                                      {"name": "fake_v4_v1", "lock_file": "real_data_lock.json",
                                       "path": "workspace/fake_v4_v1.json", "schema": "x",
                                       "row_count": len(transfer)},
                                      {"name": "fake_v5_partition", "lock_file": "partition_lock.json",
                                       "path": "workspace/fake_v5.json", "schema": "y",
                                       "row_count": len(partition)}])


def _fake_e01_frames(ledger: dict, rows: list[dict], *, seed: int = 20260820,
                     clean_first: int = 2) -> list[dict]:
    """Fake frames: the first ``clean_first`` are noiseless (bob == alice)."""
    rng = np.random.default_rng(seed)
    frames = []
    for index, row in enumerate(rows):
        alice = rng.integers(0, core.Q, size=core.N)
        bob = alice.copy()
        if index >= clean_first:
            positions = rng.choice(core.N, size=20, replace=False)
            bob[positions] = rng.integers(0, core.Q, size=20)
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "role": "development", "frame_identity": row["frame_identity"],
                       "alice": alice, "bob": bob})
    return frames


def _fake_baseline_decode(bob, syndrome):
    return {"result": {"status": "decode_failed", "iterations": 100,
                       "reason": "iteration_limit"}, "telemetry": None}


def _fake_candidate_decode(bob, syndrome):
    # returns bob unchanged: exact_correct exactly on noiseless frames
    return {"result": {"status": "syndrome_consistent", "iterations": 1,
                       "decoded_symbols": tuple(int(v) for v in bob)},
            "telemetry": None}


def test_it0_r3_codebook_deterministic_gates_and_identity():
    r3 = _r3()
    m1, mat1 = r3.build_r3_codebook()
    m2, mat2 = r3.build_r3_codebook()
    assert m1 == m2 and mat1 == mat2
    assert m1["method"] == r3.R3_METHOD == core.R3_METHOD_ID
    assert m1["construction_seed"] == 20260818
    assert m1["q"] == 1024 and m1["n"] == 256 and m1["m"] == 170
    assert m1["check_degree_histogram"] == {"3": 168, "4": 2}
    assert m1["variable_degree_histogram"] == {"2": 256}
    assert m1["component_count"] == 1          # connected
    assert m1["tanner_girth"] == 8             # check-graph girth 4 gate
    assert m1["rank"] == 170
    assert m1["canonical_sha256"] == \
        "857d25a4ca0a23fd759cea1428e2e36ac544679101c64908fabd2743f6a14d7f"
    assert r3.verify_r3_codebook(m1, mat1)["status"] == "ok"
    # tamper detection
    tampered = tuple(row[:128] + (1,) + row[129:] for row in mat1)
    assert r3.verify_r3_codebook(m1, tampered)["status"] == "failed"


def test_it0_r3_noiseless_frame_converges_iteration_one():
    r3 = _r3()
    manifest, matrix = r3.build_r3_codebook()
    field = core.GF2mField.create(core.Q)
    rng = np.random.default_rng(11)
    alice = rng.integers(0, core.Q, size=core.N)
    syndrome = core.nonbinary_syndrome(matrix, alice, field)
    out = r3.decode_r3_frame(alice, syndrome, manifest, matrix,
                             check_count=170, p=0.20, max_iter=3)
    assert out["result"]["status"] == "syndrome_consistent"
    assert out["result"]["iterations"] == 1
    assert out["telemetry"]["final_status"] == "syndrome_consistent"


def test_it0_r3_imports_do_not_load_frozen_decoder():
    r3 = _r3()
    source = Path(r3.__file__).read_text(encoding="utf8")
    top_level = [line for line in source.splitlines()
                 if "nonbinary_v7_r1a_long" in line
                 and (line.startswith("from") or line.startswith("import"))]
    assert top_level == []
    assert "nonbinary_v7_r1a_long" not in sys.modules


def test_it1_e01_pre_registration_deterministic_and_disjoint():
    ledger = _fake_ledger_r3()
    e01_first = core.pre_registered_e01_frames(ledger, count=64)
    e01_second = core.pre_registered_e01_frames(ledger, count=64)
    ids_first = [r["frame_id"] for r in e01_first]
    assert ids_first == [r["frame_id"] for r in e01_second]
    assert len(ids_first) == 64
    d04_ids = {r["frame_id"] for r in core.pre_registered_d04_frames(ledger)}
    audit_ids = {r["frame_id"] for r in ledger["rows"]
                 if r["role"] == "retrospective_audit"}
    assert not (set(ids_first) & d04_ids)
    assert not (set(ids_first) & audit_ids)
    with pytest.raises(ValueError, match="insufficient development rows"):
        core.pre_registered_e01_frames(_fake_ledger_large())


def test_it1_e01_alice_isolation_and_binding_tamper():
    r3 = _r3()
    parameters = set(inspect.signature(r3.decode_r3_frame).parameters)
    assert "alice" not in parameters and "alice_symbols" not in parameters
    manifest, matrix = r3.build_r3_codebook()
    field = core.GF2mField.create(core.Q)
    bob = np.zeros(core.N, dtype=np.int64)
    syndrome = tuple(0 for _ in range(170))
    with pytest.raises(ValueError, match="binding mismatch"):
        r3.decode_r3_frame(bob, syndrome, {"method": "wrong"}, matrix)
    with pytest.raises(ValueError, match="binding mismatch"):
        r3.decode_r3_frame(bob, syndrome, manifest, matrix[:1])


def test_it1_e01_no_overwrite_fresh_root():
    root = _out("t_r3_overwrite")
    run_dir = root / "package"
    run_dir.mkdir(parents=True)
    ledger = _fake_ledger_r3()
    rows = core.pre_registered_e01_frames(ledger, count=4)
    frames = _fake_e01_frames(ledger, rows)
    with pytest.raises(FileExistsError, match="fresh additive output root required"):
        core.run_e01(run_dir, run_id="fake", ledger=ledger, frames=frames,
                     count=4, baseline_decode=_fake_baseline_decode,
                     candidate_decode=_fake_candidate_decode,
                     _test_only=True, command="pytest IT1")


def test_it2_e01_fake_lifecycle_and_verify():
    root = _out("t_r3_e01")
    ledger = _fake_ledger_r3()
    rows = core.pre_registered_e01_frames(ledger, count=4)
    frames = _fake_e01_frames(ledger, rows, clean_first=2)
    run_dir = root / "package"
    result = core.run_e01(run_dir, run_id="fake_v13_e01", ledger=ledger,
                          frames=frames, count=4,
                          baseline_decode=_fake_baseline_decode,
                          candidate_decode=_fake_candidate_decode,
                          _test_only=True, command="pytest IT2")
    assert result["run_state"] == "plan_only"   # candidate >= 1/64 gate passed
    assert {p.name for p in run_dir.iterdir()} == set(core.ARTIFACTS)
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["outcome_rows"] == 8        # 4 frames x (baseline + candidate)
    outcome = list(csv.DictReader(
        (run_dir / "diagnostic_outcomes.csv").read_text("utf-8").splitlines()))
    phases = {row["phase"] for row in outcome}
    assert phases == {"baseline", "candidate_development"}
    methods = {row["method"] for row in outcome}
    assert methods == {core.V7_R1A_METHOD, core.R3_METHOD_ID}
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    gate = manifest["e01_gate"]
    assert gate["frames"] == 4 and gate["candidate_exact_correct"] == 2
    assert gate["baseline_exact_correct"] == 0 and gate["gate_passed"] is True
    assert manifest["authorization"]["r3_authorized"] is True
    assert manifest["stages_completed"] == ["E01"]
    report = json.loads((run_dir / "root_cause_report.json").read_bytes())
    assert report["d05_emitted"] is False
    assert str(run_dir.resolve()).startswith(str(Path("workspace").resolve()))


def test_it2_e01_fake_lifecycle_zero_candidate_frozen():
    root = _out("t_r3_e01_zero")
    ledger = _fake_ledger_r3()
    rows = core.pre_registered_e01_frames(ledger, count=4)
    frames = _fake_e01_frames(ledger, rows, clean_first=0)  # all noisy
    run_dir = root / "package"
    result = core.run_e01(run_dir, run_id="fake_v13_e01_zero", ledger=ledger,
                          frames=frames, count=4,
                          baseline_decode=_fake_baseline_decode,
                          candidate_decode=_fake_candidate_decode,
                          _test_only=True, command="pytest IT2")
    assert result["run_state"] == "failed_existing_data_feasibility"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "failed_existing_data_feasibility"
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    assert manifest["e01_gate"]["gate_passed"] is False
    assert manifest["e01_gate"]["candidate_exact_correct"] == 0


def test_it3_e01_real_r3_integration_tiny():
    root = _out("t_r3_real")
    ledger = _fake_ledger_r3()
    rows = core.pre_registered_e01_frames(ledger, count=4)
    frames = _fake_e01_frames(ledger, rows, clean_first=2)
    run_dir = root / "package"
    # production wiring without production authorization: real R1A baseline +
    # real R3 candidate at max_iter=2 (fast, tiny lane)
    result = core.run_e01(run_dir, run_id="fake_v13_e01_real", ledger=ledger,
                          frames=frames, count=4, max_iter=2,
                          _test_only=True, command="pytest IT3")
    assert result["run_state"] == "plan_only"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    outcome = list(csv.DictReader(
        (run_dir / "diagnostic_outcomes.csv").read_text("utf-8").splitlines()))
    assert all(row["status"] in ("syndrome_consistent", "decode_failed")
               for row in outcome)
    assert all(row["notes"] == "hook_equivalence=ok" for row in outcome)


def test_it3_official_root_and_frozen_dirs_hygiene():
    diag = Path("comparison_bench/outputs_comparison/nonbinary_diagnostics")
    before = sorted(p.name for p in diag.iterdir()) if diag.is_dir() else []
    root = _out("t_r3_hygiene")
    ledger = _fake_ledger_r3()
    rows = core.pre_registered_e01_frames(ledger, count=4)
    frames = _fake_e01_frames(ledger, rows, clean_first=2)
    core.run_e01(root / "package", run_id="fake_hygiene", ledger=ledger,
                 frames=frames, count=4,
                 baseline_decode=_fake_baseline_decode,
                 candidate_decode=_fake_candidate_decode,
                 _test_only=True, command="pytest IT3")
    after = sorted(p.name for p in diag.iterdir()) if diag.is_dir() else []
    assert after == before  # official output root untouched by the test lane
    # frozen baseline directories carry no working-tree changes
    repo = Path(__file__).resolve().parents[2]
    out = subprocess.run(["git", "status", "--porcelain", "--",
                          "src", "experiments", "tools", "results"],
                         capture_output=True, text=True, cwd=repo)
    assert out.returncode == 0 and out.stdout.strip() == ""


# ------------------------------------------------------------------ A01 retrospective audit lane

def _fake_audit_frames(ledger: dict, *, seed: int = 20260821,
                       clean_first: int = 120) -> list[dict]:
    rows = core.pre_registered_a01_frames(ledger)
    rng = np.random.default_rng(seed)
    frames = []
    for index, row in enumerate(rows):
        alice = rng.integers(0, core.Q, size=core.N)
        bob = alice.copy()
        if index >= clean_first:
            positions = rng.choice(core.N, size=20, replace=False)
            bob[positions] = rng.integers(0, core.Q, size=20)
        frames.append({"frame_id": int(row["frame_id"]),
                       "stratum": row["stratum"],
                       "role": "retrospective_audit",
                       "frame_identity": row["frame_identity"],
                       "alice": alice, "bob": bob})
    return frames


def test_a01_pre_registration_128_disjoint():
    ledger = _fake_ledger_r3(per_stratum=230, n_dev=100, n_conf=128)
    first = core.pre_registered_a01_frames(ledger)
    second = core.pre_registered_a01_frames(ledger)
    assert len(first) == 128
    assert [r["frame_id"] for r in first] == [r["frame_id"] for r in second]
    assert all(r["role"] == "retrospective_audit" for r in first)
    dev_ids = {r["frame_id"] for r in ledger["rows"]
               if r["role"] == "development"}
    assert not ({r["frame_id"] for r in first} & dev_ids)
    with pytest.raises(ValueError, match="audit rows"):
        core.pre_registered_a01_frames(_fake_ledger_r3())


def test_a01_fake_lifecycle_gate_pass_and_fail():
    # pass case: 120/128 noiseless -> candidate exact 120 -> gate passed
    ledger = _fake_ledger_r3(per_stratum=230, n_dev=100, n_conf=128)
    frames = _fake_audit_frames(ledger, clean_first=120)
    root = _out("t_a01_pass")
    run_dir = root / "package"
    result = core.run_a01(run_dir, run_id="fake_v13_a01", ledger=ledger,
                          frames=frames, candidate_decode=_fake_candidate_decode,
                          _test_only=True, command="pytest A01")
    assert result["run_state"] == "ready_for_fresh_confirmation"
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "ready_for_fresh_confirmation"
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    gate = manifest["a01_gate"]
    assert gate["candidate_exact_correct"] == 120
    assert gate["gate_passed"] is True
    assert gate["disclosure_bits_per_symbol"] == 170 * 10 / 256
    outcome = list(csv.DictReader(
        (run_dir / "diagnostic_outcomes.csv").read_text("utf-8").splitlines()))
    assert len(outcome) == 128
    assert all(row["phase"] == "retrospective_audit" for row in outcome)
    assert all(row["role"] == "retrospective_audit" for row in outcome)
    # fail case: 119/128 -> retrospective_non_ready
    frames_fail = _fake_audit_frames(ledger, clean_first=119, seed=99)
    root_f = _out("t_a01_fail")
    run_dir_f = root_f / "package"
    result_f = core.run_a01(run_dir_f, run_id="fake_v13_a01_f", ledger=ledger,
                            frames=frames_fail, candidate_decode=_fake_candidate_decode,
                            _test_only=True, command="pytest A01")
    assert result_f["run_state"] == "retrospective_non_ready"
    verified_f = core.verify_package(run_dir_f, _private_test_only=True)
    assert verified_f["verified"] is True
    assert verified_f["run_state"] == "retrospective_non_ready"


def _fake_audit_frames_for_stratum(ledger: dict, stratum: str, *,
                                   seed: int = 20260821,
                                   clean_first: int = 128) -> list[dict]:
    rows = core.pre_registered_a01_frames(ledger, stratum=stratum)
    rng = np.random.default_rng(seed)
    frames = []
    for index, row in enumerate(rows):
        alice = rng.integers(0, core.Q, size=core.N)
        bob = alice.copy()
        if index >= clean_first:
            positions = rng.choice(core.N, size=20, replace=False)
            bob[positions] = rng.integers(0, core.Q, size=20)
        frames.append({"frame_id": int(row["frame_id"]), "stratum": stratum,
                       "role": "retrospective_audit",
                       "frame_identity": row["frame_identity"],
                       "alice": alice, "bob": bob})
    return frames


def test_a02_fake_lifecycle_cross_stratum_no_promotion():
    ledger = _fake_ledger_r3(per_stratum=230, n_dev=100, n_conf=128)
    frames_by_stratum = {stratum: _fake_audit_frames_for_stratum(
        ledger, stratum, seed=100 + i)
        for i, stratum in enumerate(core.A02_STRATA)}
    root = _out("t_a02")
    run_dir = root / "package"
    result = core.run_a02(run_dir, run_id="fake_v13_a02", ledger=ledger,
                          frames=frames_by_stratum,
                          candidate_decode=_fake_candidate_decode,
                          _test_only=True, command="pytest A02")
    assert result["run_state"] == "plan_only"   # never promotes state
    verified = core.verify_package(run_dir, _private_test_only=True)
    assert verified["verified"] is True
    assert verified["run_state"] == "plan_only"
    manifest = json.loads((run_dir / "diagnostic_run_manifest.json").read_bytes())
    gate = manifest["a02_gate"]
    assert gate["no_state_promotion"] is True
    assert set(gate["strata"]) == set(core.A02_STRATA)
    assert all(s["candidate_exact_correct"] == 128 for s in gate["strata"].values())
    assert all(s["readiness_gate_met"] is True for s in gate["strata"].values())
