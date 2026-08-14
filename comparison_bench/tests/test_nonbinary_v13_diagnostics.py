"""V13 diagnostic engineering tests DT0/DT1/DT2
(``formal-nonbinary-ldpc-v13-existing-data-diagnostics``).

- **DT0** compile/import, structural checks, tiny GF/syndrome math, oracle
  limits and the D02 engineering oracle;
- **DT1** role-ledger reconstruction, Alice isolation, and telemetry
  hook-equivalence (hook-off == original; hook-on does not change decoded
  word, status, or iterations);
- **DT2** a complete fake diagnostic lifecycle and decoder-free replay in a
  fresh ``workspace/nbldpc_v13_<uuid>/`` root, proving tests cannot enter a
  real source loader, a production decoder by default, or an official output
  root.

All frames and locks are synthetic; no real sidecar, no real source loader and
no official output root is ever touched.
"""
from __future__ import annotations

import hashlib
import inspect
import json
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
    with pytest.raises(SystemExit) as excinfo:
        core.v13_d04_d05_guard(authorized=False, test_only=False)
    assert excinfo.value.code == 2
    with pytest.raises(SystemExit) as excinfo:
        core.v13_d04_d05_guard(authorized=True, test_only=False)
    assert excinfo.value.code == 2
    # the escape clause exists but D04/D05 execution is not implemented
    assert core.v13_d04_d05_guard(authorized=True, test_only=True) is None


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
