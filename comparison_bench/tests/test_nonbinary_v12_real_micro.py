"""V12 nonbinary LDPC real micro-feasibility acceptance
(``formal-nonbinary-ldpc-v12-real-micro-feasibility``).

Initially authorized V12-I01..I05 / V12-T0..T2 scope: frozen V7 R1
reconstruction checks, the V12 method wrapper with the Alice-information
boundary, tiny syndrome / Toeplitz / accounting checks, focused boundary,
role, no-overwrite, status, denominator, transcript, accounting, lifecycle
and tamper tests, and a complete four-frame fake package with decoder-free
strict replay (pass, 0/4 failure, forbidden failure, partial-invalid).

Every execution uses an explicit fake runner and a fresh
``workspace/nbldpc_v12_tests_<uuid>`` root; no real source loader, production
decoder by default, or official output root can be entered.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_qspa as qspa
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v12_real_micro as micro
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v12_real_partition as partition
from comparison_bench.src.comparison_bench.formal_ir import shared
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def _hex64(seed_text: str) -> str:
    return hashlib.sha256(seed_text.encode("ascii")).hexdigest()


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v12_tests_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _fake_pool(n_bw200: int = 8, *, n_bw120: int = 2, n_bw180: int = 2) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    for i in range(n_bw120):
        rows.append({"stratum": "d1024_bw120", "frame_id": offset + i,
                     "frame_identity": _hex64(f"pool|bw120|{i}"),
                     "payload_identity": _hex64(f"pool|bw120|payload|{i}"),
                     "source_pair_start": (offset + i) * 256,
                     "source_pair_end": (offset + i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw120")})
    offset += n_bw120
    for i in range(n_bw180):
        rows.append({"stratum": "d1024_bw180", "frame_id": offset + i,
                     "frame_identity": _hex64(f"pool|bw180|{i}"),
                     "payload_identity": _hex64(f"pool|bw180|payload|{i}"),
                     "source_pair_start": (offset + i) * 256,
                     "source_pair_end": (offset + i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw180")})
    offset += n_bw180
    for i in range(n_bw200):
        rows.append({"stratum": "d1024_bw200", "frame_id": offset + i,
                     "frame_identity": _hex64(f"pool|bw200|{i}"),
                     "payload_identity": _hex64(f"pool|bw200|payload|{i}"),
                     "source_pair_start": (offset + i) * 256,
                     "source_pair_end": (offset + i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw200")})
    return rows


def _bw200(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["stratum"] == "d1024_bw200"]


def _fake_discovery_root(root: Path, pool: list[dict], *, excluded_indices: tuple[int, ...] = (1, 3, 5)) -> None:
    bw = _bw200(pool)
    indices = [i for i in excluded_indices if i < len(bw)]

    def lock_frames(rows: list[dict]) -> list[dict]:
        return [{"stratum": r["stratum"], "frame_id": r["frame_id"],
                 "frame_identity": r["frame_identity"], "payload_identity": r["payload_identity"],
                 "source_pair_start": r["source_pair_start"], "source_pair_end": r["source_pair_end"],
                 "source_record_sha256": r["source_record_sha256"], "selection_rank": rank}
                for rank, r in enumerate(rows)]

    for name in ("20260729_v1_binary_ldpc_v4_10db_transfer",
                 "20260729_v2_binary_ldpc_v4_10db_transfer"):
        d = root / name
        d.mkdir(parents=True)
        doc = {"schema": "binary_ldpc_v4_10db_source_lock_v1",
               "selected_frames": lock_frames([bw[i] for i in indices[:2]])}
        (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))
    d = root / "20260731_v1_binary_ldpc_v5_partition"
    d.mkdir(parents=True)
    role_rows: list[dict] = []
    if indices:
        row = bw[indices[-1]]
        role_rows = [{"role": "confirmation", "role_rank": 0, "partition_rank": 0, **{
            k: row[k] for k in ("stratum", "frame_id", "frame_identity", "payload_identity",
                                "source_pair_start", "source_pair_end", "source_record_sha256")}}]
    doc = {"schema": "binary_ldpc_v5_10db_partition_lock_v1", "role_rows": role_rows}
    (d / "partition_lock.json").write_text(json.dumps(doc, sort_keys=True))
    for name in ("20260727_v2_binary_ldpc_v4_development",
                 "20260728_v2_binary_ldpc_v4_synthetic"):
        (root / name).mkdir(parents=True)
    d = root / "20260729_v1_binary_ldpc_v4_16db_transfer"
    d.mkdir(parents=True)
    doc = {"schema": "binary_ldpc_v4_16db_source_lock_v1", "selected_frames": []}
    (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))
    d = root / "20990101_v1_some_other_real_package"
    d.mkdir(parents=True)
    doc = {"schema": "other_real_lock_v1", "selected_frames": lock_frames([bw[len(bw) - 1]])}
    (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))


def _prepare(out: Path, root: Path, pool: list[dict], *, excluded_indices: tuple[int, ...] = (1, 3, 5)) -> dict:
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool, excluded_indices=excluded_indices)
    return partition.prepare(out, _test_only=True, discovery_root=discovery, pool_rows=pool,
                             run_id=partition.TEST_RUN_ID, source_adapter="fake_adapter",
                             canonical_rule=partition.CANONICAL_RULE)


def _frames(rows: list[dict], *, noiseless: bool = True) -> list[dict]:
    rng = np.random.default_rng(20260812)
    frames = []
    for row in rows:
        alice = rng.integers(0, 1024, 256, dtype=np.int64)
        bob = alice.copy() if noiseless else (alice + 1) % 1024
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "frame_identity": row["frame_identity"],
                       "payload_identity": row["payload_identity"],
                       "source_pair_start": row["source_pair_start"],
                       "source_pair_end": row["source_pair_end"],
                       "source_record_sha256": row["source_record_sha256"],
                       "dataset_id": f"real_10db_{row['stratum']}",
                       "alice": alice.tolist(), "bob": bob.tolist()})
    return frames


def _nonzero_codeword(field: GF2mField, matrix: Any) -> tuple[int, ...]:
    """Gaussian elimination over GF(1024) returning a nonzero codeword
    (H c = 0) of the frozen R1A matrix.  Used only to build a
    syndrome-consistent-but-wrong fake decoded word."""
    rows = [list(row) for row in matrix]
    pivots: dict[int, int] = {}
    r, col = 0, 0
    while r < 170 and col < 256:
        piv = next((rr for rr in range(r, 170) if rows[rr][col] != 0), None)
        if piv is None:
            col += 1
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        inv = field.inverse(rows[r][col])
        rows[r] = [field.mul(v, inv) for v in rows[r]]
        for rr in range(170):
            if rr != r and rows[rr][col] != 0:
                factor = rows[rr][col]
                rows[rr] = [field.add(rows[rr][k], field.mul(factor, rows[r][k])) for k in range(256)]
        pivots[col] = r
        r += 1
        col += 1
    free = [c for c in range(256) if c not in pivots]
    assert free, "no free variables"
    cvec = [0] * 256
    cvec[free[0]] = 1
    for c, rr in pivots.items():
        total = 0
        for k in range(256):
            if k != c and rows[rr][k] != 0:
                total = field.add(total, field.mul(rows[rr][k], cvec[k]))
        cvec[c] = total  # negation is the identity in GF(2^m)
    cvec = tuple(cvec)
    assert any(cvec)
    assert qspa.nonbinary_syndrome(matrix, cvec, field) == tuple([0] * 170)
    return cvec


# ---------------------------------------------------------------- fake runners

def failed(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "decode_failed", "iterations": 1}


def success(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": tuple(bob)}


def wrong(bob, syndrome, manifest, matrices, *, check_count, p):
    field = GF2mField.create(1024)
    c = _nonzero_codeword(field, matrices)
    decoded = tuple(field.add(int(x), c[i]) for i, x in enumerate(bob))
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": decoded}


def forbidden(bob, syndrome, manifest, matrices, *, check_count, p):
    return {"status": "decoder_error", "iterations": 1, "reason": "fake_forbidden"}


# ---------------------------------------------------------------- helpers

def _prepare_package(root: Path, runner, *, excluded_indices: tuple[int, ...] = (1, 3, 5),
                     fatal_hook=None) -> tuple[Path, dict]:
    """Full fake lifecycle up to execute; returns (out, prepared)."""
    out = root / "package"
    pool = _fake_pool(n_bw200=8)
    prepared = _prepare(out, root, pool, excluded_indices=excluded_indices)
    frames = _frames(prepared["partition_lock"]["selected_rows"])
    seeds = {f["frame_id"]: micro.materialize_seed_record(micro.SEED_BITS) for f in frames}
    micro.create_plan(out, frames=frames, seeds=seeds, _test_only=True)
    if fatal_hook is None:
        micro.run(out, runner=runner, _test_only=True)
    else:
        with pytest.raises(RuntimeError):
            micro.run(out, runner=runner, _test_only=True, fatal_hook=fatal_hook)
    return out, prepared


def _canon_line(event: dict) -> bytes:
    return json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"


# ---------------------------------------------------------------- T0

def test_frozen_constants():
    assert micro.Q == 1024 and micro.N == 256 and micro.M == 170
    assert micro.SYNDROME_BITS == 1700
    assert micro.SEED_BITS == 2623 and micro.SEED_BITS == 2560 + 63
    assert micro.TAG_BITS == 64
    assert micro.P == 0.20
    assert micro.FRAME_COUNT == 4
    assert micro.ROLE == "sacrificed_real_canary"
    assert micro.V7_R1A_FROZEN["construction_seed"] == 2026080400
    assert micro.V7_R1A_FROZEN["rank"] == 170 and micro.V7_R1A_FROZEN["edge_count"] == 512
    assert micro.V7_R1A_FROZEN["check_degree_histogram"] == {"3": 168, "4": 2}
    assert micro.CAPS["max_iter"] == 100
    assert micro.terminal_state([{"status": "decode_failed", "denominator_included": True}] * 4) == "failed_canary"


def test_v7_r1a_reconstruction_binding():
    manifest, matrix = micro.reconstruct_v7_r1a()
    assert manifest["method"] == "nbldpc_formal_v7_r1a_mr0"
    assert manifest["manifest_id"] == micro.V7_R1A_FROZEN["manifest_id"]
    assert manifest["canonical_sha256"] == micro.V7_R1A_FROZEN["canonical_sha256"]
    assert len(matrix) == 170 and len(matrix[0]) == 256
    result = micro.verify_v7_r1a_binding()
    assert result["status"] == "ok"
    assert result["matrix_shape"] == (170, 256)


def test_tiny_syndrome():
    field = GF2mField.create(1024)
    matrix = ((1, 0, 2, 0), (0, 1, 0, 3))
    syndrome = qspa.nonbinary_syndrome(matrix, (5, 7, 9, 11), field)
    assert syndrome[0] == field.add(field.mul(1, 5), field.mul(2, 9))
    assert syndrome[1] == field.add(field.mul(1, 7), field.mul(3, 11))
    assert qspa.nonbinary_syndrome(matrix, (0, 0, 0, 0), field) == (0, 0)


def test_toeplitz_and_seed_record_semantics():
    x = np.array([1, 0, 1, 1, 0], dtype=np.uint8)
    seed = np.array([1, 1, 0, 1, 0, 1], dtype=np.uint8)  # len(x) + tag_bits - 1 = 6
    tag = shared.toeplitz_tag(x, seed, tag_bits=2)
    expected = []
    for i in range(2):
        total = 0
        for j in range(5):
            total ^= int(seed[j - i + 1]) & int(x[j])
        expected.append(total)
    assert tag == shared.pack_bits_msb(expected)
    record = shared.seed_record([1, 0, 1, 1, 0])
    assert set(record) == {"seed_hex", "seed_bit_length", "seed_id"}
    assert record["seed_bit_length"] == 5
    assert shared.locked_seed_bits(record, 5).tolist() == [1, 0, 1, 1, 0]
    materialized = micro.materialize_seed_record(micro.SEED_BITS)
    assert set(materialized) == {"seed_hex", "seed_bit_length", "seed_id"}
    assert materialized["seed_bit_length"] == micro.SEED_BITS
    assert len(shared.locked_seed_bits(materialized, micro.SEED_BITS)) == micro.SEED_BITS


def test_disclosure_accounting():
    base = qspa.nonbinary_disclosure_accounting(170, 1024, verification_invoked=False)
    assert base == {"syndrome_disclosure_bits": 1700, "verification_tag_bits": 0,
                    "key_dependent_disclosure_bits_total": 1700, "public_control_bits": 0}
    invoked = qspa.nonbinary_disclosure_accounting(170, 1024, verification_invoked=True)
    assert invoked["key_dependent_disclosure_bits_total"] == 1700 + 64
    assert micro.LEAKAGE_CONTRACT["syndrome_bits"] == 1700
    assert micro.LEAKAGE_CONTRACT["local_event_disclosure_bits"] == 0


# ---------------------------------------------------------------- T1

def test_alice_information_boundary_enforced_before_runner():
    field = GF2mField.create(1024)
    cb, mats = micro.reconstruct_v7_r1a()
    frame = {"frame_id": 0, "dataset_id": "real_10db_d1024_bw200",
             "alice": [7, 3] + [0] * 254, "bob": [7, 3] + [0] * 254}
    seed = micro.materialize_seed_record(micro.SEED_BITS)
    captured = {}

    def capturing(bob, syndrome, manifest, matrices, *, check_count, p, **extra):
        captured["bob"] = tuple(int(x) for x in bob)
        captured["syndrome"] = tuple(int(x) for x in syndrome)
        captured["check_count"] = check_count
        captured["p"] = p
        captured["extra_kwargs"] = sorted(extra)
        return {"status": "decode_failed", "iterations": 1}

    row, events, final = micro._frame_result(frame, seed, capturing, cb, mats, field, 1)
    # the runner received only Bob, the public syndrome, the codebook binding,
    # the check count and the frozen prior: no Alice truth, SER, error
    # locations or verification feedback.
    assert captured["bob"] == tuple(frame["bob"])
    assert captured["check_count"] == 170 and captured["p"] == 0.20
    assert captured["extra_kwargs"] == []
    expected_syndrome = qspa.nonbinary_syndrome(mats, np.asarray(frame["alice"], dtype=np.int64), field)
    assert captured["syndrome"] == tuple(expected_syndrome)
    assert final == "decode_failed" and row["status"] == "decode_failed"
    assert row["verification_invoked"] is False
    assert row["key_dependent_disclosure_bits_total"] == 1700
    assert row["public_control_bits_total"] == 0


def test_full_package_role_and_denominator():
    out, _ = _prepare_package(_out("role"), success)
    rows = micro.decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    assert len(rows) == 4
    for row in rows:
        assert row["role"] == "sacrificed_real_canary"
        assert row["stratum"] == "d1024_bw200"
        assert row["method"] == micro.METHOD
        assert row["attempted"] is True and row["denominator_included"] is True
        assert row["status"] in micro._ALLOWED_STATUSES
        assert row["dimension"] == 1024 and row["frame_len_symbols"] == 256
        assert row["mapping"] == "gray" and row["check_count"] == 170


def test_run_requires_plan_only_directory_and_no_overwrite():
    out, _ = _prepare_package(_out("no_overwrite"), success)
    assert {p.name for p in out.iterdir()} == set(micro.ARTIFACTS)
    with pytest.raises(ValueError, match="plan-only directory"):
        micro.run(out, runner=success, _test_only=True)
    # a plan-only directory with a stray file is also rejected
    root = _out("stray")
    out2 = root / "package"
    pool = _fake_pool(n_bw200=8)
    _prepare(out2, root, pool)
    (out2 / "stray.txt").write_text("x", encoding="utf8")
    with pytest.raises(ValueError, match="plan-only directory"):
        micro.run(out2, runner=success, _test_only=True)


def test_production_and_implicit_runner_paths_blocked():
    with pytest.raises(ValueError, match="production execution is not authorized"):
        micro.run(None, runner=success, _test_only=False)
    with pytest.raises(ValueError, match="explicit fake runner"):
        micro.run(_out("x") / "pkg", _test_only=True)
    with pytest.raises(ValueError, match="production plan preparation is not authorized"):
        micro.create_plan(_out("p"), frames=[], seeds={}, _test_only=False)


def test_fake_runner_never_falls_back_to_production(monkeypatch):
    root = _out("no_fallback")
    out = root / "package"
    pool = _fake_pool(n_bw200=8)
    _prepare(out, root, pool)
    frames = _frames(_json_selected(out))
    seeds = {f["frame_id"]: micro.materialize_seed_record(micro.SEED_BITS) for f in frames}
    micro.create_plan(out, frames=frames, seeds=seeds, _test_only=True)

    def trap(*args, **kwargs):
        raise AssertionError("production decoder entered")

    monkeypatch.setattr(micro, "production_runner", trap)
    result = micro.run(out, runner=failed, _test_only=True)
    assert result["run_status"] == "completed"
    assert result["terminal_state"] == "failed_canary"
    assert micro.verify(out, _test_only=True)["verified"]


def _json_selected(out: Path) -> list[dict]:
    lock = micro._json_read(out / "partition_lock.json")
    return lock["selected_rows"]


def test_forbidden_status_makes_execution_invalid():
    out, _ = _prepare_package(_out("forbidden"), forbidden)
    result = micro.verify(out, _test_only=True)
    assert result["run_status"] == "invalid_execution"
    assert result["terminal_state"] == "invalid_execution"
    report = micro._json_read(out / "real_micro_report.json")
    assert report["gate"]["forbidden_failure_count"] == 4
    assert report["gate"]["passed"] is False


def test_verify_failed_path_uses_real_tag_comparison():
    out, _ = _prepare_package(_out("verify_failed"), wrong)
    result = micro.verify(out, _test_only=True)
    assert result["run_status"] == "completed"
    assert result["terminal_state"] == "failed_canary"  # 0/4 verified, valid outcomes
    rows = micro.decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    for row in rows:
        assert row["status"] == "verify_failed"
        assert row["verification_invoked"] is True
        assert row["verification_tag_bits"] == 64
        assert row["epsilon_ec"] == 2.0 ** -64
        assert row["key_dependent_disclosure_bits_total"] == 1700 + 64
        assert row["public_control_bits_total"] == 2623


def test_terminal_states_unit():
    def row(status):
        return {"status": status, "denominator_included": True}

    assert micro.terminal_state([row("verified_success")] + [row("decode_failed")] * 3) == "observed_real_correction"
    assert micro.terminal_state([row("decode_failed")] * 4) == "failed_canary"
    assert micro.terminal_state([row("verify_failed")] * 4) == "failed_canary"
    assert micro.terminal_state([row("decode_failed")] * 3) == "invalid_execution"
    assert micro.terminal_state([row("decoder_error")] + [row("decode_failed")] * 3) == "invalid_execution"
    assert micro.terminal_state([{"status": "decode_failed", "denominator_included": False}] * 4) == "invalid_execution"


def test_transcript_tamper_rejected():
    out, _ = _prepare_package(_out("tamper_transcript"), success)
    path = out / "real_transcript.jsonl"
    lines = path.read_bytes().splitlines()
    first = json.loads(lines[0])
    first["key_dependent_bits"] = int(first["key_dependent_bits"]) + 1
    path.write_bytes(b"".join([_canon_line(first)] + [_canon_line(json.loads(line)) for line in lines[1:]]))
    with pytest.raises(ValueError):
        micro.verify(out, _test_only=True)


def test_csv_status_tamper_rejected():
    out, _ = _prepare_package(_out("tamper_csv"), success)
    path = out / "real_frame_outcomes.csv"
    text = path.read_text(encoding="utf8")
    text = text.replace("verified_success", "decode_failed", 1)
    path.write_text(text, encoding="utf8")
    with pytest.raises(ValueError):
        micro.verify(out, _test_only=True)


def test_seed_record_tamper_rejected():
    out, _ = _prepare_package(_out("tamper_seed"), success)
    plan_path = out / "pre_run_plan.json"
    plan = micro._json_read(plan_path)
    forged = micro.materialize_seed_record(micro.SEED_BITS)
    plan["seed_schedule"]["records"][0] = forged
    plan_path.write_bytes(micro._compact(plan))
    with pytest.raises(ValueError):
        micro.verify(out, _test_only=True)


def test_manifest_tamper_rejected():
    out, _ = _prepare_package(_out("tamper_manifest"), success)
    path = out / "real_run_manifest.json"
    manifest = micro._json_read(path)
    manifest["outcome_count"] = int(manifest["outcome_count"]) + 1
    path.write_bytes(micro._compact(manifest))
    with pytest.raises(ValueError):
        micro.verify(out, _test_only=True)


def test_report_tamper_rejected():
    out, _ = _prepare_package(_out("tamper_report"), success)
    path = out / "real_micro_report.json"
    report = micro._json_read(path)
    report["gate"]["verified_success"] = 0
    path.write_bytes(micro._compact(report))
    with pytest.raises(ValueError, match="report reconstruction"):
        micro.verify(out, _test_only=True)


def test_official_root_never_created_and_production_verify_blocked():
    # The only official v12 directories that may exist are prepare-only: they
    # hold exactly the three preparation artifacts and no execute artifact.
    official = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    v12_dirs = [d for d in official.iterdir() if d.is_dir() and "v12" in d.name.lower()]
    for d in v12_dirs:
        assert {p.name for p in d.iterdir()} == set(micro.PREPARE_ARTIFACTS), d.name
    out, _ = _prepare_package(_out("prod_verify_block"), success)
    with pytest.raises(ValueError, match="production verification is not authorized"):
        micro.verify(out, _test_only=False)


def test_verify_is_decoder_free_by_construction():
    for fn in (micro.verify, micro._verify_frame_public, micro.validate_outcome_v12,
               micro._validate_event_flow, micro.run, micro._frame_result):
        source = inspect.getsource(fn)
        assert "v7_long" not in source
        assert "nonbinary_v7_r1a_long" not in source
        assert "production_runner" not in source
    source = inspect.getsource(micro.production_runner)
    assert "nonbinary_v7_r1a_long" in source  # the only decoder boundary


def test_fresh_interpreter_imports_no_decoder():
    code = (
        "import sys; sys.path.insert(0, '.')\n"
        "from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v12_real_micro as m\n"
        "mods = [n for n in sys.modules if 'nonbinary_v7_r1a_long' in n or 'nonbinary_v7_r1b_long' in n]\n"
        "assert not mods, mods\n"
        "print('ok')\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


# ---------------------------------------------------------------- T2

def test_t2_complete_fake_package_pass_and_decoder_free_replay():
    root = _out("t2_pass")
    out, prepared = _prepare_package(root, success)
    assert prepared["partition_state"] == "ready"
    assert {p.name for p in out.iterdir()} == set(micro.ARTIFACTS)
    result = micro.verify(out, _test_only=True)
    assert result["verified"] is True
    assert result["run_status"] == "completed"
    assert result["terminal_state"] == "observed_real_correction"
    assert result["outcomes"] == 4
    rows = micro.decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    assert [r["plan_frame_id"] for r in rows] == [f"d1024_bw200|{r['frame_id']}" for r in rows]
    for row in rows:
        assert row["status"] == "verified_success"
        assert row["verification_invoked"] is True
        assert row["key_dependent_disclosure_bits_total"] == 1764
        assert row["public_control_bits_total"] == 2623
    report = micro._json_read(out / "real_micro_report.json")
    assert report["terminal_state"] == "observed_real_correction"
    assert report["gate"] == {"denominator": 4, "verified_success": 4, "verify_failed": 0,
                              "decode_failed": 0, "forbidden_failure_count": 0, "passed": True}
    manifest = micro._json_read(out / "real_run_manifest.json")
    assert manifest["decoder_reexecution"] is False


def test_t2_zero_of_four_failure_is_failed_canary():
    root = _out("t2_zero4")
    out, _ = _prepare_package(root, failed)
    result = micro.verify(out, _test_only=True)
    assert result["run_status"] == "completed"
    assert result["terminal_state"] == "failed_canary"
    rows = micro.decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    assert all(r["status"] == "decode_failed" for r in rows)
    # decode_failed frames emit no seed or tag: zero public-control disclosure
    assert all(r["verification_invoked"] is False for r in rows)
    assert all(r["key_dependent_disclosure_bits_total"] == 1700 for r in rows)
    assert all(r["public_control_bits_total"] == 0 for r in rows)


def test_t2_partial_invalid_run_is_retained_and_replayable():
    def partial_hook(count: int) -> None:
        if count >= 2:
            raise RuntimeError("forced_partial")

    root = _out("t2_partial")
    out, _ = _prepare_package(root, success, fatal_hook=partial_hook)
    result = micro.verify(out, _test_only=True)
    assert result["run_status"] == "invalid_execution"
    assert result["terminal_state"] == "invalid_execution"
    rows = micro.decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    assert len(rows) == 2  # retained prefix, never replaced or resumed
    assert {p.name for p in out.iterdir()} == set(micro.ARTIFACTS)


def test_t2_official_output_root_absent_after_all_lifecycles():
    # The only official v12 directories that may exist are prepare-only (the
    # main-thread-authorized production package); the fake lifecycle below
    # never writes there.
    official = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    v12_dirs = [d for d in official.iterdir() if d.is_dir() and "v12" in d.name.lower()]
    for d in v12_dirs:
        assert {p.name for p in d.iterdir()} == set(micro.PREPARE_ARTIFACTS), d.name
    # no workspace root outside the nbldpc_v12_tests_* namespace was created
    for candidate in (Path("workspace") / "nbldpc_v12_real_micro",
                      Path("workspace") / "nbldpc_v12_execute"):
        assert not candidate.exists()


# ---------------------------------------------------------------- production prepare lane (RP01-RP03)

def _production_prepare(root: Path, pool: list[dict], *, excluded_indices: tuple[int, ...] = (1, 3, 5)) -> tuple[Path, dict]:
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool, excluded_indices=excluded_indices)
    out = root / "package"
    prepared = partition.prepare(out, production_prepare_authorized=True,
                                 discovery_root=discovery, pool_rows=pool,
                                 run_id=partition.RUN_ID,
                                 source_adapter=partition.SOURCE_ADAPTER,
                                 canonical_rule=partition.CANONICAL_RULE)
    return out, prepared


def test_production_plan_lane_blocked_partition():
    """A partition with fewer than four eligible rows yields a
    ``source_partition_blocked`` production plan: zero attempt ids, zero
    frames, zero seed records, no symbols/syndromes anywhere.  The read-only
    verifier accepts it plan-only; production execution stays hard-stopped."""
    root = _out("prod_plan_blocked")
    pool = _fake_pool(n_bw200=4)  # 2 eligible after excluding 1,3
    out, prepared = _production_prepare(root, pool, excluded_indices=(1, 3, 5))
    assert prepared["partition_state"] == "source_partition_blocked"
    plan = micro.create_plan(out, production_prepare_authorized=True)
    assert plan["plan_state"] == "source_partition_blocked"
    assert plan["schema"] == micro.PLAN_SCHEMA and plan["run_id"] == micro.RUN_ID
    assert plan["execution"]["attempt_ids"] == []
    assert plan["frames"] == []
    assert plan["seed_schedule"]["seed_count"] == 0
    assert plan["seed_schedule"]["records"] == []
    text = json.dumps(plan)
    for forbidden in ('"alice"', '"bob"', '"syndrome"', '"seed_hex"'):
        assert forbidden not in text, forbidden
    assert {p.name for p in out.iterdir()} == set(micro.PREPARE_ARTIFACTS)
    result = micro.verify(out, _test_only=False)
    assert result["plan_only"] and result["run_status"] == "planned"
    assert result["terminal_state"] == "source_partition_blocked"
    # plan-only verification never imports a decoder
    assert "nonbinary_v7_r1a_long" not in sys.modules
    with pytest.raises(ValueError, match="production execution is not authorized"):
        micro.run(out, runner=success, _test_only=False)


def test_production_plan_lane_ready_identity_only():
    """A ready production partition freezes four identity-only frames (never
    Alice/Bob symbols) and four unique fresh seed records in the production
    plan schemas; the plan-only read-only verifier accepts it without
    ``_test_only``."""
    root = _out("prod_plan_ready")
    pool = _fake_pool(n_bw200=8)
    out, prepared = _production_prepare(root, pool, excluded_indices=(1, 3, 5))
    assert prepared["partition_state"] == "ready"
    lock = partition._json_read(out / "partition_lock.json")
    frames = [dict(r) for r in lock["selected_rows"]]  # identity-only rows
    seeds = {f["frame_id"]: micro.materialize_seed_record(micro.SEED_BITS) for f in frames}
    plan = micro.create_plan(out, frames=frames, seeds=seeds, production_prepare_authorized=True)
    assert plan["schema"] == micro.PLAN_SCHEMA and plan["run_id"] == micro.RUN_ID
    assert plan["plan_state"] == "ready"
    assert len(plan["frames"]) == 4 and len(plan["seed_schedule"]["records"]) == 4
    for frame in plan["frames"]:
        assert "alice" not in frame and "bob" not in frame
    micro._validate_plan(plan, test_only=False, output_dir=out)
    result = micro.verify(out, _test_only=False)
    assert result["plan_only"] and result["run_status"] == "planned"
    assert result["terminal_state"] is None
    assert "nonbinary_v7_r1a_long" not in sys.modules
    # un-authorized production plan creation stays blocked
    with pytest.raises(ValueError, match="production plan preparation is not authorized"):
        micro.create_plan(out, frames=frames, seeds=seeds, _test_only=False)
