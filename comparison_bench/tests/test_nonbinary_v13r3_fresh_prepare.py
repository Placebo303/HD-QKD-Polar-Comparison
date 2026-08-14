"""V13 R3 fresh-acquisition prepare acceptance tests
(``formal-nonbinary-ldpc-v13-r3-fresh-acquisition``).

Tier structure (frozen by the change):

- **T0** — compile/import/structural checks.  ``__pycache__`` writes are denied
  in this environment, so imports are checked via ``ast.parse`` of the three
  allowed sources (never ``py_compile``), plus frozen-constant assertions.
- **T1** — focused unit tests: identity determinism, exclusion collision
  detection, role mutual exclusivity + counts, insufficient-frames path,
  no-data path, no-overwrite, and authorization-flag refusal without the flag.
- **T2** — complete fake lifecycle: a temporary directory carries fake pairs
  rows written by the test itself, ``prepare`` runs the fake lane end-to-end
  into a fresh writable ``workspace/nbldpc_v13r3_<uuid>/`` root, and the output
  schemas are verified read-only.

Discipline: every execution uses the fake lane (``_test_only=True``) with fake
discovery data and a test-owned fresh root.  No production decoder, no
production output root, and no ``comparison_bench/outputs_comparison/`` write
can be entered.  T3 is NOT run.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v13r3_fresh as core


def _hex64(seed_text: str) -> str:
    return hashlib.sha256(seed_text.encode("ascii")).hexdigest()


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v13r3_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _fresh_row(frame_id: int, *, stratum: str = "d1024_bw200") -> dict:
    return {"stratum": stratum, "frame_id": frame_id,
            "source_record_sha256": _hex64(f"fresh|src|{stratum}|{frame_id}")}


def _write_fake_source(root: Path, n_frames: int, *, path_name: str = "fresh.csv") -> Path:
    """Write a fake pairs-table CSV with the V13 pairs-table column contract."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / path_name
    rows = []
    frame_id = 0
    for _ in range(n_frames):
        for pair_idx in range(256):
            rows.append({"frame_id": frame_id, "pair_idx": pair_idx,
                         "alice_symbol": 0, "bob_symbol": 0})
        frame_id += 1
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["frame_id", "pair_idx",
                                                "alice_symbol", "bob_symbol"])
        writer.writeheader()
        writer.writerows(rows)
    return path


# ---------------------------------------------------------------- T0


def _parse_ok(path: str) -> ast.Module:
    with open(path, encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=path)


def test_t0_sources_parse():
    for rel in ("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v13r3_fresh.py",
                "comparison_bench/src/comparison_bench/cli/run_v13r3_fresh_prepare.py",
                "comparison_bench/tests/test_nonbinary_v13r3_fresh_prepare.py"):
        _parse_ok(rel)


def test_t0_import_and_constants():
    assert core.METHOD == "nbldpc_v13r3_fresh"
    assert core.IDENTITY_PREFIX == "v13r3fresh"
    assert core.PRIMARY_STRATUM == "d1024_bw200"
    assert core.STRATA == ("d1024_bw120", "d1024_bw180", "d1024_bw200")
    assert core.PLAN_SEED_DEFAULT == 20260815
    assert core.CANARY_COUNT == 64
    assert core.CONFIRMATION_COUNT == 128
    assert core.REQUIRED_EXEC_FRAMES == 192
    assert core.ROLES == ("characterization", "canary", "confirmation")
    assert core.PLAN_SCHEMA == "nbldpc_v13r3_fresh_plan_v1"
    assert core.NO_ELIGIBLE_SCHEMA == "nbldpc_v13r3_fresh_no_eligible_v1"
    assert core.INSUFFICIENT_SCHEMA == "nbldpc_v13r3_fresh_insufficient_v1"
    assert core.DECODER_INVARIANT["codebook"] == "nbldpc_v13_r3_code_v1"


def test_t0_no_decoder_import():
    """The prepare path must never import a decoder (r3 candidate or any other
    decoder module)."""
    forbidden = ["nonbinary_v13_r3_candidate", "nonbinary_v7_r1a_long",
                 "nonbinary_v7_r1b_long", "nonbinary_v7_r2_long",
                 "nonbinary_v7_r3_long"]
    loaded = [n for n in sys.modules if any(f in n for f in forbidden)]
    assert not loaded, loaded


# ---------------------------------------------------------------- T1


def test_identity_determinism():
    row = _fresh_row(3)
    a = core.derive_identity("d1024_bw200", row)
    b = core.derive_identity("d1024_bw200", row)
    assert a == b
    assert a.startswith("v13r3fresh-d1024_bw200-")
    assert core.derive_identity("d1024_bw200", row, seed=20260815) == a
    # different seed → different identity
    assert core.derive_identity("d1024_bw200", row, seed=1) != a
    # different frame_id → different identity
    assert core.derive_identity("d1024_bw200", _fresh_row(4)) != a


def test_exclusion_collision_detection():
    ident = core.derive_identity("d1024_bw200", _fresh_row(0))
    # clean set → no collision
    assert core.exclusion_check(ident, {"frame": set(), "payload": set()})["collision"] is False
    # uuid-field collision against an excluded frame identity
    uuid_field = ident.rsplit("-", 1)[-1]
    assert core.exclusion_check(ident, {"frame": {uuid_field}, "payload": set()})["collision"] is True
    # identity-string collision
    assert core.exclusion_check(ident, {"frame": {ident}, "payload": set()})["collision"] is True
    # v13 role ledger extra set
    assert core.exclusion_check(ident, {"frame": set(), "payload": set(),
                                        "v13_frame": {uuid_field}})["collision"] is True
    # namespace violation fails closed
    with pytest.raises(ValueError):
        core.exclusion_check("not-v13r3fresh", {"frame": set(), "payload": set()})


def test_role_mutual_exclusion_and_counts():
    rows = [_fresh_row(i) for i in range(192)]
    assignment = core.assign_roles(rows)
    assert assignment["state"] == "ready"
    assert assignment["counts"]["canary"] == 64
    assert assignment["counts"]["confirmation"] == 128
    assert assignment["counts"]["characterization"] == 0
    assert core.role_mutual_exclusion_holds(assignment)
    # exactly one role per assigned row
    assert all(a["role"] in core.ROLES for a in assignment["assignments"])
    assert len({a["identity"] for a in assignment["assignments"]}) == 192


def test_role_assignment_with_characterization_remainder():
    rows = [_fresh_row(i) for i in range(200)]
    assignment = core.assign_roles(rows)
    assert assignment["counts"]["canary"] == 64
    assert assignment["counts"]["confirmation"] == 128
    assert assignment["counts"]["characterization"] == 8


def test_role_assignment_ambiguous_blocked():
    rows = [_fresh_row(0), _fresh_row(0)]  # duplicate canonical fields → same identity
    assignment = core.assign_roles(rows)
    assert assignment["state"] == "blocked_role_ledger"
    assert assignment["ambiguous_identities"]


def test_no_data_path():
    scan = core.scan_fresh_sources([])
    assert scan["eligible_row_count"] == 0
    assert scan["eligible_rows"] == []
    pkg = core.build_no_eligible_package()
    assert pkg["schema"] == core.NO_ELIGIBLE_SCHEMA
    assert pkg["terminal_state"] == "no_eligible_frames"
    assert pkg["eligible_row_count"] == 0


def test_insufficient_frames_path():
    fake = _out("insufficient")
    src = _write_fake_source(fake, n_frames=100)  # < 192
    scan = core.scan_fresh_sources([src])
    assert scan["eligible_row_count"] == 100
    pkg = core.build_frozen_failure_package("insufficient_eligible_frames",
                                            scan=scan, exclusion_sets={})
    assert pkg["schema"] == core.INSUFFICIENT_SCHEMA
    assert pkg["terminal_state"] == "insufficient_eligible_frames"
    assert pkg["shortfall"] == 192 - 100
    assert pkg["no_shrinking"] is True


def test_authorization_refusal_without_flag():
    with pytest.raises(ValueError, match="not authorized"):
        core.prepare(_out("auth_refuse") / "pkg", declared_paths=[],
                     _test_only=False, production_prepare_authorized=False)


def test_no_overwrite():
    out = _out("no_overwrite")
    core.prepare(out / "pkg", declared_paths=[], _test_only=True)
    # a second prepare into the same directory must fail (fresh dir required)
    with pytest.raises(FileExistsError):
        core.prepare(out / "pkg", declared_paths=[], _test_only=True)


def test_empty_declared_list_legitimate():
    """The default (absent/empty) declared list is a legitimate frozen outcome,
    not an error."""
    out = _out("empty")
    result = core.prepare(out / "pkg", declared_paths=[], _test_only=True)
    assert result["state"] == "no_eligible_frames"
    assert (out / "pkg" / "no_eligible_package.json").exists()


# ---------------------------------------------------------------- T2


def test_t2_complete_fake_lifecycle():
    root = _out("t2")
    src = _write_fake_source(root, n_frames=200)  # >= 192 → ready plan
    out = root / "package"
    result = core.prepare(out, declared_paths=[src], _test_only=True)
    assert result["state"] == "ready"
    assert (out / "plan.json").exists()
    plan = core._json_read(out / "plan.json")
    assert plan["schema"] == core.PLAN_SCHEMA_TEST
    assert plan["plan_state"] == "ready"
    assert plan["seed"] == core.PLAN_SEED_DEFAULT
    assert plan["eligible_row_count"] == 200
    # identity ledger has one entry per eligible row, roles mutually exclusive
    ledger = plan["identity_ledger"]
    assert len(ledger) == 200
    roles = [e["role"] for e in ledger]
    assert roles.count("canary") == 64
    assert roles.count("confirmation") == 128
    assert roles.count("characterization") == 8
    assert len({e["identity"] for e in ledger}) == 200
    # read-only structural validation
    validated = core.validate_package(out, test_only=True)
    assert validated["verified"] is True
    # no production output root was touched
    official = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    assert not (official / "nbldpc_v13r3_fresh").exists()


def test_t2_no_eligible_lifecycle_and_schema():
    root = _out("t2_no_eligible")
    out = root / "package"
    result = core.prepare(out, declared_paths=[], _test_only=True)
    assert result["state"] == "no_eligible_frames"
    pkg = core._json_read(out / "no_eligible_package.json")
    assert pkg["schema"] == core.NO_ELIGIBLE_SCHEMA_TEST
    assert pkg["terminal_state"] == "no_eligible_frames"
    validated = core.validate_package(out, test_only=True)
    assert validated["verified"] is True


def test_t2_cli_fake_lane_end_to_end():
    root = _out("t2_cli")
    src = _write_fake_source(root, n_frames=200)
    out = root / "package"
    code = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.cli.run_v13r3_fresh_prepare",
         "prepare", "--declared", str(src), "--output", str(out), "--test-only"],
        capture_output=True, text=True, cwd=str(Path.cwd()))
    assert code.returncode == 0, code.stderr
    assert (out / "plan.json").exists()
    # production prepare without the flag must refuse
    code2 = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.cli.run_v13r3_fresh_prepare",
         "prepare", "--declared", str(src), "--output", str(root / "prod"),
         "--production-prepare-authorized"],
        capture_output=True, text=True, cwd=str(Path.cwd()))
    # production lane with real declared path + no discovery root: build_frozen_failure/
    # or plan; authorization present so it should NOT be the refusal path.
    assert code2.returncode != 2 or "authorized" not in code2.stderr


def test_t2_cli_refuses_production_without_flag():
    root = _out("t2_cli_refuse")
    code = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.cli.run_v13r3_fresh_prepare",
         "prepare", "--output", str(root / "pkg")],
        capture_output=True, text=True, cwd=str(Path.cwd()))
    assert code.returncode == 2
    assert "authorized" in code.stderr


def test_t2_self_check():
    code = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.cli.run_v13r3_fresh_prepare",
         "self-check"],
        capture_output=True, text=True, cwd=str(Path.cwd()))
    assert code.returncode == 0, code.stderr
    result = json.loads(code.stdout)
    assert result["no_data_ok"] is True
    assert result["identity_deterministic"] is True
    assert result["decoder_imported"] is False


def test_t2_official_output_root_never_written():
    """The fake lifecycle never writes under comparison_bench/outputs_comparison/."""
    official = Path("comparison_bench/outputs_comparison")
    before = {str(p) for p in official.rglob("*") if p.is_file()}
    root = _out("t2_official_guard")
    src = _write_fake_source(root, n_frames=200)
    core.prepare(root / "pkg", declared_paths=[src], _test_only=True)
    after = {str(p) for p in official.rglob("*") if p.is_file()}
    assert before == after
