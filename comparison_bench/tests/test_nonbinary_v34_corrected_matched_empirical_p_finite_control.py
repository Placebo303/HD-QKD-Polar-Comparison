"""Focused T0/T1/fake checks plus the P4 fake T2/T3 packet for the V34 CLI.

Every execute flow below injects ``FakeV34Provider`` explicitly and writes to a
fresh child of ``workspace/``. No test is allowed to construct the production
runner or the official V34 root. The P4 section (OX-A1..A7) adds structural
lazy-decoder isolation, independent real-input binding checks, exact-once RNG
proofs, the full 60-call fake matrix with threshold-priority aggregation,
authorization/collision zero-side-effect cases, multi-layer strict-replay
tamper cases, and protected-root boundary snapshots. Production decoder
modules are never imported by any flow under test.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import py_compile
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v34_corrected_matched_empirical_p_finite_control as v34,
)


class FakeV34Provider:
    """Explicit fake binding/runner seam; no decoder dependency."""

    def __init__(self, mode: str = "pass"):
        self.counts = {source: np.ones((v34.N, v34.N), dtype=np.float64)
                       for source in v34.SOURCE_ORDER}
        self.mode = mode
        self.calls: list[dict] = []

    def binding_context(self, _repo_root: Path):
        return {
            "mode": "fake",
            "bindings": {
                "ok": True,
                "schema": "fake_v34_bindings_v1",
                "bindings": {"fixture": {"sha256": "fixture"}},
            },
            "counts": self.counts,
        }

    def run_call(self, request: dict):
        self.calls.append(request)
        if self.mode == "fail":
            return {"exact_l2": False, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False,
                    "l2_status": "max_iter", "l2_iterations": v34.MAX_ITER}
        if self.mode == "fatal":
            raise RuntimeError("fake interface failure")
        if self.mode == "malformed":
            return {"exact_l2": 1, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False}
        if self.mode == "nonfinite":
            return {"exact_l2": True, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False,
                    "runtime_s": float("nan")}
        return {"exact_l2": True, "syndrome_ok": True,
                "tag_ok": True, "false_accept": False,
                "l2_status": "converged", "l2_iterations": 20}


class X2CandidateProvider(FakeV34Provider):
    """Fake legal candidate path used only for accounting/replay tests."""

    def run_call(self, request: dict):
        self.calls.append(request)
        return {
            "x2_hat": [0] * v34.N,
            "l2_syndrome_ok": False,
            "l2_status": "max_iter",
            "l2_iterations": v34.MAX_ITER,
            # Deliberately forged; V34 must recompute from x2_hat.
            "l2_errors_final": 999,
        }


def _fresh_root() -> Path:
    root = v34.WORKSPACE_ROOT / f"v34_impl_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    root.rmdir()
    return root


@pytest.fixture
def fake_pass():
    provider = FakeV34Provider("pass")
    root = _fresh_root()
    try:
        yield provider, root
    finally:
        if root.exists():
            shutil.rmtree(root)


FAKE_VERIFY = FakeV34Provider("pass")


def test_t0_compile_import_help_and_lazy_decoder():
    module = importlib.import_module(v34.__name__)
    assert module.NUMPY_REQUIRED == "2.4.0"
    assert len(module.enumerate_calls()) == 60
    assert "comparison_bench.src.comparison_bench.cli.run_nonbinary_v32_finite_de_bridge" not in module.sys.modules
    assert v34.main(["test-selfcheck"]) == v34.EXIT_OK


def test_t0_ref1_and_exact_sampler_determinism():
    assert v34.check_sampler_reference()
    counts = np.ones((v34.N, v34.N), dtype=np.float64)
    first = v34.sample_empirical_block(counts, 340101)
    second = v34.sample_empirical_block(counts, 340101)
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    assert first[0].shape == (v34.N,)
    assert np.all(first[1] == first[0] // v34.N)
    assert np.all(first[2] == first[0] % v34.N)


def test_t0_schedule_and_authorization_digest():
    calls = v34.enumerate_calls()
    assert [(c["source"], c["seed"]) for c in calls[:2]] == [("1M", 340101), ("1M", 340102)]
    assert calls[20]["source"] == "1p5M" and calls[40]["source"] == "2M"
    assert len({(c["source"], c["block"], c["seed"]) for c in calls}) == 60
    auth = dict(v34.AUTH_EXACT_VALUES)
    auth.update({"implementation_commit": v34.git_head(),
                 "call_matrix_digest": v34.expected_call_matrix_digest(),
                 "granted_by": "test", "decision_id": "test-v34", "granted": True})
    assert v34.validate_execute_auth(auth) is None
    assert v34.validate_execute_auth(dict(auth, decision="NO"))
    assert v34.validate_execute_auth(dict(auth, call_matrix_digest="0" * 64))
    assert v34.validate_execute_auth(dict(auth, implementation_commit="0" * 40))
    assert v34.validate_execute_auth(dict(auth, extra=True))


def test_t1_stage0_real_readonly_and_no_official_root():
    report, counts = v34.stage0_validate(v34.REPO_ROOT)
    assert report["ok"] is True
    assert report["sampler_reference"] is True
    assert report["packet"]["m2"] == v34.M2
    assert set(counts) == set(v34.SOURCE_ORDER)
    assert not v34.OFFICIAL_RUN_ROOT.exists()


def test_t1_probability_fail_closed():
    bad = np.ones((v34.N, v34.N), dtype=np.float64)
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite_counts"):
        v34.sample_empirical_block(bad, 340101)
    zero = np.zeros((v34.N, v34.N), dtype=np.float64)
    with pytest.raises(ValueError, match="invalid_total"):
        v34.sample_empirical_block(zero, 340101)


def test_t1_fake_end_to_end_exact_60_and_strict_verify(fake_pass):
    provider, root = fake_pass
    rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                 auth_info={"mechanism": "fake_runner"})
    assert rc == v34.EXIT_OK
    assert final["overall_terminal"] == v34.TERMINAL_PASS
    assert len(provider.calls) == 60
    records = json.loads((root / "block_records.json").read_text())["records"]
    assert len(records) == 60
    assert [r["ordinal"] for r in records] == list(range(1, 61))
    assert all(r["truth_role"] == "oracle_l1" and r["operational"] is False for r in records)
    assert all(r["sampler_choice_calls"] == 1 for r in records)
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root), "runner": None})()) == v34.EXIT_EVIDENCE_INCONSISTENT
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root),
                                               "runner": f"{__name__}:FAKE_VERIFY"})()) == v34.EXIT_OK


def test_t1_fake_ordinary_fail_continues_and_threshold_terminal():
    provider = FakeV34Provider("fail")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_OK
        assert final["overall_terminal"] == v34.TERMINAL_FAIL
        assert len(provider.calls) == 60
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_fatal_stops_and_no_resume_or_run02():
    provider = FakeV34Provider("fatal")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        assert len(provider.calls) == 1
        assert not (root.parent / "run_02").exists()
        before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
        rc2, _ = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                 auth_info={"mechanism": "fake_runner"})
        assert rc2 == v34.EXIT_COLLISION
        after = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
        assert before == after
    finally:
        if root.exists():
            shutil.rmtree(root)


@pytest.mark.parametrize("mode", ["malformed", "nonfinite"])
def test_t1_malformed_or_nonfinite_decoder_result_is_fatal(mode):
    provider = FakeV34Provider(mode)
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        assert len(provider.calls) == 1
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_strict_replay_rejects_record_tamper(fake_pass):
    provider, root = fake_pass
    assert v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                           auth_info={"mechanism": "fake_runner"})[0] == v34.EXIT_OK
    payload = json.loads((root / "block_records.json").read_text())
    payload["records"][0]["sampled_ser"] += 0.01
    (root / "block_records.json").write_text(json.dumps(payload), encoding="utf-8")
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root),
                                               "runner": f"{__name__}:FAKE_VERIFY"})()) == v34.EXIT_EVIDENCE_INCONSISTENT


def test_t1_unauthorized_execute_has_zero_side_effects():
    root = _fresh_root()
    try:
        rc = v34.main(["execute", "--run-root", str(root)])
        assert rc == v34.EXIT_UNAUTHORIZED
        assert not root.exists()
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_official_root_never_created_by_fake(fake_pass):
    provider, root = fake_pass
    v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                    auth_info={"mechanism": "fake_runner"})
    assert not v34.OFFICIAL_RUN_ROOT.exists()


# ---------------------------------------------------------------------------
# P4 frozen acceptance packet (OX-A1..A7): fake T2/T3, additive only.
# No production decoder import/call; no official-root creation; no CLI edits.
# ---------------------------------------------------------------------------

V32_PRODUCTION_MODULE = (
    "comparison_bench.src.comparison_bench.cli.run_nonbinary_v32_finite_de_bridge")
V28R_DECODER_MODULE = (
    "comparison_bench.src.comparison_bench.formal_ir.nonbinary_v28")
PRODUCTION_MODULES = (V32_PRODUCTION_MODULE, V28R_DECODER_MODULE)

# Independent REF1 oracle duplicated from the frozen design constants so the
# sampler identity is checked without trusting module internals.
_REF_GRID_LITERAL = np.arange(1, 17, dtype=np.float64).reshape((4, 4), order="C")
_REF_SEED_LITERAL = 340101
_REF_SIZE_LITERAL = 12
_REF_IDX_LITERAL = [8, 9, 14, 9, 15, 13, 10, 14, 10, 4, 11, 15]

_BINDING_FILE_RELS = tuple(sorted({
    rel for rel in v34.BINDING_PATHS.values()
}))
_BINDING_DIR_RELS = (
    str(Path(v34.V25_REL).parent),
    str(Path(v34.V31_PAYLOAD_REL).parent),
    str(Path(v34.V32_RUN_REL).parent),
    v34.V28R_ROOT_REL,
)


def _no_decoder_modules_imported() -> None:
    leaked = [m for m in PRODUCTION_MODULES if m in sys.modules]
    assert not leaked, f"production decoder modules were imported: {leaked}"


def _forbid_production_runner(monkeypatch) -> None:
    """Tripwire: any production-runner construction fails the test loudly."""
    def _boom(*_args, **_kwargs):
        raise AssertionError("production runner constructed outside authorized execute")
    monkeypatch.setattr(v34, "_production_runner", _boom)


def _fresh_child(prefix: str) -> Path:
    root = v34.WORKSPACE_ROOT / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _build_fake_pass_run(provider=None):
    provider = provider or FakeV34Provider("pass")
    root = _fresh_root()
    rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider,
                                fake=True, auth_info={"mechanism": "fake_runner"})
    assert rc == v34.EXIT_OK, f"fake pass run failed rc={rc}"
    return provider, root, final


def _verify_namespace(root: Path, runner: str | None = f"{__name__}:FAKE_VERIFY"):
    return SimpleNamespace(run_root=str(root), runner=runner)


def _read_last_json(capsys_obj) -> dict:
    return json.loads(capsys_obj.readouterr().out)


def _edit_json(path: Path, mutate) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _snapshot_tree(root: Path) -> dict:
    if not root.exists():
        return {"<absent>": True}
    snap: dict = {}
    for p in sorted(root.rglob("*")):
        try:
            st = p.stat()
        except OSError:
            continue
        snap[str(p.relative_to(root))] = (
            p.is_dir(), 0 if p.is_dir() else st.st_size, st.st_mtime_ns)
    snap["<root_mtime_ns>"] = root.stat().st_mtime_ns
    return snap


def _snapshot_protected_roots() -> dict:
    return {label: _snapshot_tree(v34.REPO_ROOT / rel)
            for label, rel in v34.PROTECTED_OLD_ROOTS}


def _snapshot_sibling_top_level() -> dict:
    if not v34.SIBLING_CHECKOUT.exists():
        return {"<absent>": True}
    snap = {}
    for p in sorted(v34.SIBLING_CHECKOUT.iterdir()):
        try:
            st = p.stat()
        except OSError:
            continue
        snap[p.name] = (p.is_dir(), st.st_mtime_ns)
    return snap


def _valid_auth() -> dict:
    auth = dict(v34.AUTH_EXACT_VALUES)
    auth.update({
        "implementation_commit": v34.git_head(),
        "call_matrix_digest": v34.expected_call_matrix_digest(),
        "granted_by": "ox-alpha-p4-focused-tests",
        "decision_id": "test-only-not-an-authorization",
        "granted": True,
    })
    return auth


AUTH_MUTATIONS = {
    "missing_granted_by": lambda a: {k: v for k, v in a.items() if k != "granted_by"},
    "missing_granted_flag": lambda a: {k: v for k, v in a.items() if k != "granted"},
    "extra_field": lambda a: dict(a, unexpected_field=1),
    "wrong_type_decision": lambda a: dict(a, decision=123),
    "wrong_head_commit": lambda a: dict(a, implementation_commit="b" * 40),
    "nonhex_head_commit": lambda a: dict(a, implementation_commit="z" * 40),
    "wrong_freeze_commit": lambda a: dict(a, freeze_commit="0" * 40),
    "wrong_matrix_digest": lambda a: dict(a, call_matrix_digest="e" * 64),
    "short_matrix_digest": lambda a: dict(a, call_matrix_digest="ab"),
    "wrong_official_path": lambda a: dict(
        a, official_run_root=str(Path(v34.OFFICIAL_RUN_REL).parent / "run_02")),
    "wrong_change_name": lambda a: dict(a, change="some-other-change"),
    "wrong_schema": lambda a: dict(a, schema="nbldpc_v34_execute_auth_v2"),
    "blank_grantee": lambda a: dict(a, granted_by="   "),
    "blank_decision_id": lambda a: dict(a, decision_id=""),
    "granted_false": lambda a: dict(a, granted=False),
    "granted_string_true": lambda a: dict(a, granted="true"),
}


class ScriptedProvider(FakeV34Provider):
    """Per-ordinal outcome script over the explicit fake seam."""

    def __init__(self, default: str = "pass", script: dict[int, str] | None = None):
        super().__init__(default)
        self.default = default
        self.script = {int(k): v for k, v in (script or {}).items()}

    def run_call(self, request: dict):
        self.mode = self.script.get(int(request["ordinal"]), self.default)
        return super().run_call(request)


def _assert_record_evidence(records: list[dict]) -> None:
    calls = v34.enumerate_calls()
    assert len(records) == len(calls) == v34.TOTAL_CALLS
    assert [r["ordinal"] for r in records] == [c["ordinal"] for c in calls]
    hexdigits = set("0123456789abcdef")
    for rec, call in zip(records, calls):
        for key in ("source", "source_id", "block", "seed", "ordinal"):
            assert rec[key] == call[key], (rec["ordinal"], key)
        assert rec["block_uid"] == f"V34|{call['source']}|{call['block']}"
        assert rec["packet_id"] == v34.PACKET_ID
        assert rec["packet_sha256"] == v34.V31_PACKET_SHA256
        assert rec["packet_m1"] == v34.M1
        assert rec["packet_m2"] == v34.M2[call["source"]]
        assert rec["field_id"] == v34.FIELD_ID
        assert rec["truth_used"] is True and rec["truth_role"] == "oracle_l1"
        assert rec["operational"] is False and rec["qualification"] is False
        assert rec["sample_rng"] == "PCG64"
        assert rec["numpy_version"] == v34.NUMPY_REQUIRED == "2.4.0"
        assert rec["sampler_choice_calls"] == 1
        digest = rec["sampled_pair_digest"]
        assert isinstance(digest, str) and len(digest) == 64 and set(digest) <= hexdigits
        assert rec["syndrome_leakage_bits"] == v34.M2[call["source"]] * 5
        assert rec["verification_leakage_bits"] == 64
        assert rec["claim_boundary"] == v34.CLAIM_BOUNDARY
        assert rec["terminal"] in ("PASS", "FAIL", "INCONCLUSIVE")
        assert rec["fatal"] is False
        assert rec["success"] == (rec["terminal"] == "PASS")
        assert rec["reason"] == ("" if rec["success"] else v34.REASON_ORDINARY)
        ser = float(rec["sampled_ser"])
        assert math.isfinite(ser) and 0.0 <= ser <= 1.0


def test_p4_ox_a1_structural_flows_never_import_production_decoder(capsys):
    # Byte-compile into a plain workspace child: this machine's legacy
    # __pycache__ directories and pytest-managed temp roots have restrictive
    # ACLs (AGENTS.md section 8), so all artifacts go to writable paths we
    # create ourselves.
    compile_out = _fresh_child("v34_ox_a1_compile")
    try:
        py_compile.compile(str(v34.__file__),
                           cfile=str(compile_out / "cli.pyc"), doraise=True)
        py_compile.compile(str(Path(__file__)),
                           cfile=str(compile_out / "tests.pyc"), doraise=True)
    finally:
        shutil.rmtree(compile_out, ignore_errors=True)
    module = importlib.import_module(v34.__name__)
    assert module.NUMPY_REQUIRED == "2.4.0"
    assert len(module.enumerate_calls()) == v34.TOTAL_CALLS

    with pytest.raises(SystemExit) as exc:
        v34.main(["--help"])
    assert exc.value.code == 0
    assert "usage:" in capsys.readouterr().out
    _no_decoder_modules_imported()

    assert v34.main(["test-selfcheck"]) == v34.EXIT_OK
    assert _read_last_json(capsys)["ok"] is True
    _no_decoder_modules_imported()

    rc = v34.cmd_prepare(SimpleNamespace(runner=None))
    assert rc == v34.EXIT_OK
    report = _read_last_json(capsys)
    assert report["ok"] is True
    _no_decoder_modules_imported()

    _, run_root, _ = _build_fake_pass_run()
    try:
        assert v34.cmd_verify(_verify_namespace(run_root)) == v34.EXIT_OK
        _no_decoder_modules_imported()
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


def test_p4_ox_a2_real_bindings_independent_and_prepare_zero_side_effects(monkeypatch, capsys):
    _forbid_production_runner(monkeypatch)

    def sha(rel: str) -> str:
        h = hashlib.sha256()
        with open(v34.REPO_ROOT / rel, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    pre_files = {rel: sha(rel) for rel in _BINDING_FILE_RELS
                 if (v34.REPO_ROOT / rel).is_file()}
    pre_dirs = {rel: _snapshot_tree(v34.REPO_ROOT / rel) for rel in _BINDING_DIR_RELS}

    # --- V25 empirical counts, independently of stage0 ---
    assert sha(v34.V25_REL) == v34.V25_COUNTS_SHA256
    with np.load(v34.REPO_ROOT / v34.V25_REL, allow_pickle=False) as data:
        assert set(data.files) == set(v34.NPZ_KEYS.values())
        for source in v34.SOURCE_ORDER:
            arr = np.asarray(data[v34.NPZ_KEYS[source]])
            assert arr.shape == (v34.N, v34.N)
            assert arr.dtype == np.float64
            assert bool(np.all(np.isfinite(arr))) and bool(np.all(arr >= 0))
            assert float(arr.sum()) > 0

    # --- V31 QC packet identity, independent of stage0 ---
    assert sha(v34.V31_PAYLOAD_REL) == v34.V31_PACKET_SHA256
    doc = json.loads((v34.REPO_ROOT / v34.V31_PAYLOAD_REL).read_text(encoding="utf-8"))
    packets = [p for p in doc.get("packets", []) if p.get("packet_id") == v34.PACKET_ID]
    assert len(packets) == 1
    packet = packets[0]
    assert int(packet["n"]) == v34.N == 1024
    assert int(packet["q"]) == v34.Q == 32
    assert int(packet["m1"]) == v34.M1 == 16
    assert {s: int(packet["m2_by_source"][s]) for s in v34.SOURCE_ORDER} == v34.M2
    mats = packet["matrices"]
    assert len(mats["L1"]) == v34.M1
    assert set(mats["L2"].keys()) == set(v34.SOURCE_ORDER)
    assert all(len(mats["L2"][s]) == v34.M2[s] for s in v34.SOURCE_ORDER)

    # --- GF(32) field identity derived in a clean subprocess from the pure
    # nonbinary_field contract (never imports a decoder module here) ---
    code = ("from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field "
            "import get_field_spec; s = get_field_spec(32); "
            "print(s.field_id); print(s.primitive_polynomial)")
    proc = subprocess.run([sys.executable, "-B", "-c", code],
                          cwd=str(v34.REPO_ROOT), capture_output=True,
                          text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    field_id_line, poly_line = proc.stdout.split()
    assert field_id_line == v34.FIELD_ID
    assert int(poly_line) == v34.FIELD_POLY == 37

    # --- decoder-chain source identities ---
    v32_source = (v34.REPO_ROOT / v34.V32_CLI_REL).read_text(encoding="utf-8")
    for token in ("class ProductionRunner", "def run_block",
                  "decode_error_domain_posterior", "l1_mode"):
        assert token in v32_source
    v28_source = (v34.REPO_ROOT / v34.V28R_CLI_REL).read_text(encoding="utf-8")
    assert "def decode_error_domain_posterior" in v28_source

    # --- environment + exact V34-PCG64-REF1, from duplicated literals ---
    assert np.__version__ == "2.4.0"
    p_ref = _REF_GRID_LITERAL.reshape(-1, order="C") / _REF_GRID_LITERAL.sum()
    idx_ref = np.asarray(np.random.Generator(np.random.PCG64(_REF_SEED_LITERAL)).choice(
        16, size=_REF_SIZE_LITERAL, replace=True, p=p_ref), dtype=np.int64)
    assert idx_ref.tolist() == _REF_IDX_LITERAL

    # --- stage0 + prepare agree, and nothing is written anywhere ---
    report, counts = v34.stage0_validate(v34.REPO_ROOT)
    assert report["ok"] is True
    assert report["bindings"]["v25_counts"]["sha256"] == v34.V25_COUNTS_SHA256
    assert set(counts) == set(v34.SOURCE_ORDER)
    assert v34.cmd_prepare(SimpleNamespace(runner=None)) == v34.EXIT_OK
    prepared = _read_last_json(capsys)
    assert prepared["ok"] is True
    assert prepared["sampler_reference_id"] == "V34-PCG64-REF1"

    post_files = {rel: sha(rel) for rel in _BINDING_FILE_RELS
                  if (v34.REPO_ROOT / rel).is_file()}
    post_dirs = {rel: _snapshot_tree(v34.REPO_ROOT / rel) for rel in _BINDING_DIR_RELS}
    assert pre_files == post_files
    assert pre_dirs == post_dirs
    assert not v34.OFFICIAL_RUN_ROOT.exists()
    _no_decoder_modules_imported()


def test_p4_ox_a3_sampler_exact_once_c_order_and_fail_closed(monkeypatch):
    pcg_seeds: list[int] = []
    choice_log: list[tuple] = []
    real_pcg64 = np.random.PCG64
    real_generator_cls = np.random.Generator

    def counting_pcg64(seed=None):
        pcg_seeds.append(int(seed))
        return real_pcg64(int(seed))

    class WrapGen:
        def __init__(self, bit_generator):
            self._gen = real_generator_cls(bit_generator)

        def choice(self, *args, **kwargs):
            choice_log.append((args, kwargs))
            return self._gen.choice(*args, **kwargs)

        def __getattr__(self, item):
            return getattr(self._gen, item)

    monkeypatch.setattr(np.random, "PCG64", counting_pcg64)
    monkeypatch.setattr(np.random, "Generator", WrapGen)

    # Non-symmetric table so C-order flattening is actually distinguishable.
    table = np.arange(1, v34.N * v34.N + 1, dtype=np.float64).reshape(v34.N, v34.N)
    expected_c = table.reshape(-1, order="C") / table.sum()
    expected_f = table.reshape(-1, order="F") / table.sum()
    assert not np.allclose(expected_c, expected_f)

    idx, alice, bob = v34.sample_empirical_block(table, 340101)
    assert pcg_seeds == [340101]
    assert len(choice_log) == 1
    args, kwargs = choice_log[0]
    assert args[0] == v34.N * v34.N
    assert kwargs["size"] == v34.N
    assert kwargs["replace"] is True
    assert np.allclose(kwargs["p"], expected_c)
    assert idx.shape == (v34.N,) and idx.dtype == np.int64
    np.testing.assert_array_equal(alice, idx // v34.N)
    np.testing.assert_array_equal(bob, idx % v34.N)

    # Full fake 60-call matrix: exactly one PCG64 instance and one C-order
    # choice per block, in frozen matrix order.  The CLI's own V34-PCG64-REF1
    # self-checks also construct generators; those are recognizable by their
    # frozen (seed=340101, size=12) signature and must account for every
    # non-block event, leaving no room for hidden resampling or fallbacks.
    def split_events(events):
        blocks = [(s, a, k) for s, (a, k) in events if k.get("size") == v34.N]
        others = [(s, a, k) for s, (a, k) in events if k.get("size") != v34.N]
        return blocks, others

    pcg_seeds.clear()
    choice_log.clear()
    provider = FakeV34Provider("pass")
    root = _fresh_root()
    try:
        rc, _final = v34.execute_run(v34.REPO_ROOT, root, provider=provider,
                                     fake=True, auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_OK
        assert len(pcg_seeds) == len(choice_log)
        matrix = v34.enumerate_calls()
        blocks, others = split_events(list(zip(pcg_seeds, choice_log)))
        assert [s for s, _a, _k in blocks] == [c["seed"] for c in matrix]
        assert all(a[0] == v34.N * v34.N and k["replace"] is True
                   and len(k["p"]) == v34.N * v34.N for _s, a, k in blocks)
        for seed, args, kwargs in others:
            assert seed == _REF_SEED_LITERAL
            assert kwargs.get("size") == _REF_SIZE_LITERAL
            assert args[0] == 16

        pcg_before = len(pcg_seeds)
        choice_before = len(choice_log)
        assert v34.cmd_verify(_verify_namespace(root)) == v34.EXIT_OK
        assert len(pcg_seeds) == len(choice_log)
        events_verify = list(zip(pcg_seeds[pcg_before:], choice_log[choice_before:]))
        blocks_v, others_v = split_events(events_verify)
        assert [s for s, _a, _k in blocks_v] == [c["seed"] for c in matrix]
        assert all(a[0] == v34.N * v34.N and k["replace"] is True
                   for _s, a, k in blocks_v)
        assert all(seed == _REF_SEED_LITERAL for seed, _a, _k in others_v)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Invalid tables are rejected before any RNG construction: no fallback,
    # no resampling, zero additional generator/choice usage.
    bad_tables = [
        ("shape:", np.ones((v34.N, v34.N - 1))),
        ("negative_counts", np.where(np.arange(v34.N * v34.N).reshape(v34.N, v34.N) == 5,
                                     -1.0, 1.0)),
        ("nonfinite_counts", np.full((v34.N, v34.N), np.nan)),
        ("invalid_total", np.zeros((v34.N, v34.N))),
        ("invalid_total", np.full((v34.N, v34.N), 1e308)),
    ]
    for token, bad in bad_tables:
        seeds_before = list(pcg_seeds)
        choices_before = len(choice_log)
        with pytest.raises(ValueError, match=token):
            v34.sample_empirical_block(bad, 340101)
        assert pcg_seeds == seeds_before
        assert len(choice_log) == choices_before


def test_p4_ox_a4_t2_full_matrix_evidence_and_threshold_priority():
    # A: exactly-at-threshold 19/20 stays PASS in every source.
    provider_a = ScriptedProvider("pass", script={21: "fail"})
    _, root_a, final_a = _build_fake_pass_run(provider_a)
    try:
        assert final_a["overall_terminal"] == v34.TERMINAL_PASS
        records = json.loads((root_a / "block_records.json").read_text())["records"]
        _assert_record_evidence(records)
        summaries = json.loads((root_a / "source_summaries.json").read_text())
        assert {s: summaries[s]["terminal"] for s in v34.SOURCE_ORDER} == \
            {"1M": "PASS", "1p5M": "PASS", "2M": "PASS"}
        assert summaries["1p5M"]["successes"] == 19
        assert summaries["1p5M"]["threshold"] == 19
    finally:
        shutil.rmtree(root_a, ignore_errors=True)

    # B: below threshold is an ordinary FAIL and the matrix still completes.
    provider_b = ScriptedProvider("pass", script={21: "fail", 22: "fail"})
    _, root_b, final_b = _build_fake_pass_run(provider_b)
    try:
        assert final_b["overall_terminal"] == v34.TERMINAL_FAIL
        summaries = json.loads((root_b / "source_summaries.json").read_text())
        assert summaries["1p5M"]["terminal"] == "FAIL"
        assert summaries["1p5M"]["successes"] == 18
        assert summaries["1p5M"]["attempted"] == 20
        assert summaries["1p5M"]["missing"] == 0
        assert summaries["1p5M"]["duplicates"] == 0
    finally:
        shutil.rmtree(root_b, ignore_errors=True)

    # C: a fatal block stops the matrix and outranks passing sources.
    provider_c = ScriptedProvider("pass", script={41: "fatal"})
    root_c = _fresh_root()
    try:
        rc, final_c = v34.execute_run(v34.REPO_ROOT, root_c, provider=provider_c,
                                      fake=True, auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final_c["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        assert final_c["fatal"] is True
        assert len(provider_c.calls) == 41
        records = json.loads((root_c / "block_records.json").read_text())["records"]
        assert len(records) == 41
        assert records[-1]["terminal"] == "INCONCLUSIVE"
        assert records[-1]["fatal"] is True
        assert records[-1]["reason"] == "decoder_interface_exception"
        summaries = json.loads((root_c / "source_summaries.json").read_text())
        assert summaries["1M"]["terminal"] == "PASS"
        assert summaries["1p5M"]["terminal"] == "PASS"
        assert summaries["2M"]["terminal"] == "INCONCLUSIVE"
        assert summaries["2M"]["attempted"] == 1
        assert summaries["2M"]["missing"] == 19
    finally:
        shutil.rmtree(root_c, ignore_errors=True)

    # D: INCONCLUSIVE outranks even a local FAIL elsewhere.
    provider_d = ScriptedProvider("pass", script={22: "fail", 23: "fail", 24: "fail",
                                                  41: "fatal"})
    root_d = _fresh_root()
    try:
        rc, final_d = v34.execute_run(v34.REPO_ROOT, root_d, provider=provider_d,
                                      fake=True, auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final_d["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        summaries = json.loads((root_d / "source_summaries.json").read_text())
        assert summaries["1p5M"]["terminal"] == "FAIL"
        assert final_d["overall_terminal"] != v34.TERMINAL_FAIL
    finally:
        shutil.rmtree(root_d, ignore_errors=True)


@pytest.mark.parametrize("mutation_name", sorted(AUTH_MUTATIONS))
def test_p4_ox_a5_auth_tamper_causes_zero_side_effects(monkeypatch, mutation_name):
    _forbid_production_runner(monkeypatch)
    auth_dir = _fresh_child("v34_ox_auth")
    target = v34.WORKSPACE_ROOT / f"v34_ox_target_{uuid.uuid4().hex}"
    try:
        payload = AUTH_MUTATIONS[mutation_name](_valid_auth())
        auth_file = auth_dir / f"{mutation_name}.json"
        auth_file.write_text(json.dumps(payload), encoding="utf-8")
        args = SimpleNamespace(runner=None, run_root=str(target),
                               execute_auth_file=str(auth_file))
        rc = v34.cmd_execute(args)
        assert rc == v34.EXIT_UNAUTHORIZED
        assert not target.exists()
        assert not v34.OFFICIAL_RUN_ROOT.exists()
        _no_decoder_modules_imported()
    finally:
        shutil.rmtree(auth_dir, ignore_errors=True)


def test_p4_ox_a5_valid_auth_reaches_collision_before_decoder(monkeypatch):
    """The official root is never created; a patched existing directory stands
    in for it to prove collision precedes any decoder construction."""
    _forbid_production_runner(monkeypatch)
    standing = _fresh_child("v34_ox_official_standin")
    try:
        pre_listing = sorted(p.name for p in standing.iterdir())
        monkeypatch.setattr(v34, "OFFICIAL_RUN_ROOT", standing)
        auth_dir = _fresh_child("v34_ox_auth")
        try:
            auth_file = auth_dir / "valid.json"
            auth_file.write_text(json.dumps(_valid_auth()), encoding="utf-8")
            assert v34.validate_execute_auth(json.loads(auth_file.read_text())) is None
            args = SimpleNamespace(runner=None, run_root=str(standing),
                                   execute_auth_file=str(auth_file))
            rc = v34.cmd_execute(args)
            assert rc == v34.EXIT_COLLISION
            assert sorted(p.name for p in standing.iterdir()) == pre_listing
            _no_decoder_modules_imported()
        finally:
            shutil.rmtree(auth_dir, ignore_errors=True)
    finally:
        shutil.rmtree(standing, ignore_errors=True)


@pytest.mark.parametrize("target_kind", [
    "official_root", "protected_v25", "results_child", "archive_child",
    "diagnostics_parent", "sibling_child",
])
def test_p4_ox_a5_fake_mode_rejects_official_protected_and_broad_roots(
        monkeypatch, target_kind):
    _forbid_production_runner(monkeypatch)
    canaries = {
        "results_child": v34.RESULTS_ROOT / "v34_ox_guard_canary",
        "archive_child": v34.ARCHIVE_ROOT / "v34_ox_guard_canary",
        "sibling_child": v34.SIBLING_CHECKOUT / "v34_ox_guard_canary",
    }
    targets = {
        "official_root": v34.OFFICIAL_RUN_ROOT,
        "protected_v25": v34.REPO_ROOT / v34.PROTECTED_OLD_ROOTS[0][1],
        "diagnostics_parent": v34.REPO_ROOT / v34.DIAGNOSTICS_REL,
    }
    targets.update(canaries)
    target = targets[target_kind]
    provider = FakeV34Provider("pass")
    rc, _final = v34.execute_run(v34.REPO_ROOT, target, provider=provider,
                                 fake=True, auth_info={"mechanism": "fake_runner"})
    assert rc == v34.EXIT_WRITE_GUARD
    assert provider.calls == []
    if target_kind in canaries:
        assert not canaries[target_kind].exists()
    assert not v34.OFFICIAL_RUN_ROOT.exists()
    _no_decoder_modules_imported()


TAMPER_CASES = (
    ("raw_byte_drift_records",
     lambda base: (base / "block_records.json").write_bytes(
         (base / "block_records.json").read_bytes() + b"\n{/*raw drift*/}"),
     ("records_unparsable",)),
    ("record_seed_drift",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"][9].update(seed=999999)),
     ("out_of_order",)),
    ("sampler_marker_drift",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"][3].update(sample_rng="MT19937")),
     ("field_drift",)),
    ("m2_marker_drift",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"][30].update(packet_m2=200)),
     ("field_drift",)),
    ("claim_boundary_drift",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"][0].update(claim_boundary="overclaim")),
     ("field_drift",)),
    ("numpy_marker_drift",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"][12].update(numpy_version="1.26.0")),
     ("field_drift",)),
    ("drop_record",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"].pop(7)),
     ("out_of_order",)),
    ("duplicate_record",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"].insert(6, dict(d["records"][5]))),
     ("duplicate_call",)),
    ("extra_record",
     lambda base: _edit_json(base / "block_records.json",
                             lambda d: d["records"].append(dict(d["records"][-1],
                                                                ordinal=61))),
     ("extra_record",)),
    ("summary_semantic_tamper",
     lambda base: _edit_json(base / "source_summaries.json",
                             lambda d: d["1M"].update(successes=99)),
     ("source_summary_recompute_mismatch",)),
    ("final_terminal_tamper",
     lambda base: _edit_json(base / "final_state.json",
                             lambda d: d.update(overall_terminal=v34.TERMINAL_FAIL,
                                                terminal=v34.TERMINAL_FAIL)),
     ("final_terminal_recompute_mismatch",)),
    ("manifest_matrix_digest_link",
     lambda base: _edit_json(base / "audit_manifest.json",
                             lambda d: d["matrix"].update(digest="f" * 64)),
     ("freeze_digest_mismatch", "matrix_digest_mismatch")),
    ("manifest_lifecycle_flag",
     lambda base: _edit_json(base / "audit_manifest.json",
                             lambda d: d.update(no_resume_no_retry=False)),
     ("freeze_digest_mismatch", "lifecycle_semantics_mismatch")),
)


def test_p4_ox_a6_strict_replay_multi_layer_tamper(capsys):
    _, base_root, _ = _build_fake_pass_run()
    capsys.readouterr()  # drain execute_run's own stdout line
    parent = _fresh_child("v34_ox_tamper")
    try:
        assert v34.cmd_verify(_verify_namespace(base_root)) == v34.EXIT_OK
        problems = _read_last_json(capsys)["problems"]
        assert problems == []

        for name, mutate, tokens in TAMPER_CASES:
            variant = parent / name
            shutil.copytree(base_root, variant)
            mutate(variant)
            rc = v34.cmd_verify(_verify_namespace(variant))
            assert rc == v34.EXIT_EVIDENCE_INCONSISTENT, name
            got = _read_last_json(capsys)["problems"]
            for token in tokens:
                assert any(token in problem for problem in got), (name, token, got[:5])
        _no_decoder_modules_imported()
    finally:
        shutil.rmtree(parent, ignore_errors=True)
        shutil.rmtree(base_root, ignore_errors=True)


def test_p4_ox_a7_complete_fake_flow_keeps_protected_roots_frozen(monkeypatch, capsys):
    pre_protected = _snapshot_protected_roots()
    pre_sibling = _snapshot_sibling_top_level()
    assert not v34.OFFICIAL_RUN_ROOT.exists()
    _forbid_production_runner(monkeypatch)

    with pytest.raises(SystemExit) as exc:
        v34.main(["--help"])
    assert exc.value.code == 0
    capsys.readouterr()
    assert v34.main(["test-selfcheck"]) == v34.EXIT_OK
    capsys.readouterr()
    assert v34.cmd_prepare(SimpleNamespace(runner=None)) == v34.EXIT_OK
    capsys.readouterr()

    _, run_root, _ = _build_fake_pass_run()
    tamper_parent = _fresh_child("v34_ox_boundary")
    try:
        assert v34.cmd_verify(_verify_namespace(run_root)) == v34.EXIT_OK
        capsys.readouterr()

        drift = tamper_parent / "drift"
        shutil.copytree(run_root, drift)
        _edit_json(drift / "block_records.json",
                   lambda d: d["records"][0].update(sampled_ser=0.5))
        assert v34.cmd_verify(_verify_namespace(drift)) == \
            v34.EXIT_EVIDENCE_INCONSISTENT
        capsys.readouterr()

        _no_decoder_modules_imported()
        assert _snapshot_protected_roots() == pre_protected
        assert _snapshot_sibling_top_level() == pre_sibling
        assert not v34.OFFICIAL_RUN_ROOT.exists()
    finally:
        shutil.rmtree(run_root, ignore_errors=True)
        shutil.rmtree(tamper_parent, ignore_errors=True)


def test_p4a_l2_errors_measure_partial_candidates_and_ignore_forged_count():
    private = {
        "x1": np.zeros(v34.N, dtype=np.int64),
        "x2": np.zeros(v34.N, dtype=np.int64),
    }
    for expected_errors in (1, 3):
        x2_hat = np.zeros(v34.N, dtype=np.int64)
        x2_hat[:expected_errors] = 1
        normal = v34._normalise_result(
            {
                "x2_hat": x2_hat.tolist(),
                "l2_syndrome_ok": False,
                "l2_status": "max_iter",
                "l2_iterations": v34.MAX_ITER,
                "l2_errors_final": 999,
            },
            private,
        )
        assert normal["l2_errors_final"] == expected_errors
        assert normal["l2_error_accounting"] == "measured"
        assert normal["x2_hat"] == x2_hat.tolist()


def test_p4a_external_monotonic_runtime_is_authoritative(monkeypatch):
    # Replace only V34's time binding so the rest of pytest is unaffected.
    real_time = v34.time
    tick_values = iter(
        value
        for ordinal in range(v34.TOTAL_CALLS)
        for value in (100.0 + ordinal * 2.0, 100.125 + ordinal * 2.0)
    )
    monkeypatch.setattr(
        v34,
        "time",
        SimpleNamespace(
            monotonic=lambda: next(tick_values),
            strftime=real_time.strftime,
            gmtime=real_time.gmtime,
        ),
    )
    provider = FakeV34Provider("pass")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(
            v34.REPO_ROOT,
            root,
            provider=provider,
            fake=True,
            auth_info={"mechanism": "fake_runner"},
        )
        assert rc == v34.EXIT_OK
        assert final["records"] == v34.TOTAL_CALLS
        records = json.loads((root / "block_records.json").read_text())["records"]
        assert all(math.isclose(float(r["runtime_s"]), 0.125, abs_tol=1e-15)
                   for r in records)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_p4a_verify_recomputes_l2_errors_and_rejects_x2_hat_or_count_tamper(capsys):
    provider = X2CandidateProvider("pass")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(
            v34.REPO_ROOT,
            root,
            provider=provider,
            fake=True,
            auth_info={"mechanism": "fake_runner"},
        )
        assert rc == v34.EXIT_OK
        assert final["overall_terminal"] == v34.TERMINAL_FAIL
        records_path = root / "block_records.json"
        original = records_path.read_text(encoding="utf-8")
        records = json.loads(original)["records"]
        assert all(isinstance(r["x2_hat"], list) for r in records)
        assert all(r["l2_error_accounting"] == "measured" for r in records)
        assert v34.cmd_verify(_verify_namespace(root, f"{__name__}:X2CandidateProvider")) == v34.EXIT_OK
        capsys.readouterr()

        _edit_json(records_path, lambda d: d["records"][0].update(
            l2_errors_final=d["records"][0]["l2_errors_final"] + 1))
        assert v34.cmd_verify(_verify_namespace(root, f"{__name__}:X2CandidateProvider")) == \
            v34.EXIT_EVIDENCE_INCONSISTENT
        capsys.readouterr()

        records_path.write_text(original, encoding="utf-8")
        _edit_json(records_path, lambda d: d["records"][0].update(
            l2_errors_initial=d["records"][0]["l2_errors_initial"] + 1))
        assert v34.cmd_verify(_verify_namespace(root, f"{__name__}:X2CandidateProvider")) == \
            v34.EXIT_EVIDENCE_INCONSISTENT
        capsys.readouterr()

        records_path.write_text(original, encoding="utf-8")
        _, alice, _ = v34.sample_empirical_block(provider.counts["1M"], 340101, v34.N)
        _, replay_x2 = v34._factor(alice)
        changed_index = next((j for j, value in enumerate(replay_x2) if int(value) != 0), 0)
        changed_value = int(replay_x2[changed_index]) if int(replay_x2[changed_index]) != 0 else 1
        _edit_json(records_path, lambda d: d["records"][0]["x2_hat"].__setitem__(
            changed_index, changed_value))
        assert v34.cmd_verify(_verify_namespace(root, f"{__name__}:X2CandidateProvider")) == \
            v34.EXIT_EVIDENCE_INCONSISTENT
        capsys.readouterr()
    finally:
        shutil.rmtree(root, ignore_errors=True)
