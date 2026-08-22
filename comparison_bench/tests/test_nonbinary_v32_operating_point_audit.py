"""T0/T1/T2 suite for the NB-LDPC V32 operating-point consistency audit.

Audit-only change: every test injects a fake binding provider via
``--runner``; no production decoder, DE sampler or pipeline is ever invoked,
and every run root is a fresh ``workspace/<audit>/<uuid>/`` directory created
through pytest ``--basetemp``.
"""
from __future__ import annotations

import ast
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v32_operating_point_audit as audit,
)

RUNNER_SPEC = __name__ + ":make_fake_runner"

LABELS = ("1M", "1p5M", "2M")
SIDS = dict(audit.SOURCE_IDS)
SER = dict(audit.FROZEN_RAW_SER)
# (+1, -1) split of ser per source: mirrors the real V25 direction structure.
PM1_SPLIT = {"1M": (0.995, 0.005), "1p5M": (0.02, 0.98), "2M": (0.98, 0.02)}
SCHEMA = "nbldpc_v32_bridge_block_result_v1"

SHALL_O1_FILES = {
    "audit_manifest.json",
    "d0_signature.json", "d0_signature.md",
    "d1_consistency.json", "d1_consistency.md",
    "d2_feasibility.json", "d2_feasibility.md",
    "d3_v26_evidence.json", "d3_v26_evidence.md",
    "final_branch_decision.json",
}


# --------------------------------------------------------------------------- #
# Fake fixtures
# --------------------------------------------------------------------------- #

HARNESS_SNIPPET = '''\
def synth_channel_sample(seed: int, p_ser: float) -> tuple[list[int], list[int]]:
    """Matched iid synthetic channel: uniform GF(1024) words, iid substitution
    with probability ``p_ser`` (frozen V25 raw_ser), replacement delta uniform
    in [1,1023] added modulo 1024."""
    rng = np.random.default_rng(seed)
    alice = rng.integers(0, 1024, size=N_FROZEN, dtype=np.int64)
    mask = rng.random(N_FROZEN) < float(p_ser)
    deltas = rng.integers(1, 1024, size=N_FROZEN, dtype=np.int64)
    bob = np.where(mask, (alice + deltas) % 1024, alice)
    return alice.tolist(), bob.tolist()
'''

SAMPLER_SNIPPET = '''\
Semantics (V26 design section 1):
- ``(A,B)`` sampled from the train joint ``P(A,B)`` = N_ab / total.
- L1: ``P(U1=u|B) = sum_{a: L1(a)=u} P(A=a|B)``.
- L2: ``P(U2=u|B,U1) = sum_{a: L1(a)=U1,L2(a)=u} P(A=a|B) / sum_{a: L1(a)=U1} P(A=a|B)``.
'''


def _decode_record(arm: str, label: str, i: int, **kw) -> dict:
    init = 235 + (i * 7) % 17
    rec = {
        "schema": SCHEMA, "arm": arm, "source": label, "source_id": SIDS[label],
        "seed_or_block_id": str(320101 + i), "block_uid": f"{arm}|{label}|{320101 + i}",
        "graph_packet_identity": "3d0e8773a436eed5", "posterior_identity": "e0360203b8003c82",
        "truth_used": True, "l1_mode": "sequential",
        "l1_errors_initial": init, "l1_errors_final": init,
        "l2_errors_initial": init, "l2_errors_final": init,
        "exact": False, "tag": False, "false_accept": False, "syndrome": False,
        "unsatisfied_checks": 11, "iterations": 30,
        "terminal_decoder_status": "max_iter_reached",
        "l1_decoder_status_verbatim": "max_iter_reached",
        "runtime_s": 1.0 * i,
        "posterior_nll": 8.0 + i * 0.25, "posterior_entropy": 0.05 + i * 0.001,
        "truth_symbol_rank": 0.21, "calibration_bucket": 2,
        "posterior_anomaly_block": False,
        "residual_syndrome_stats": {"l1_residual_checks": None, "l2_residual_checks": 12 + i % 5},
        "success": False,
    }
    rec.update(kw)
    return rec


def make_records() -> list[dict]:
    recs = [{
        "schema": SCHEMA, "kind": "baseline_import", "arm": "B5", "source": "all",
        "source_id": None, "seed_or_block_id": None,
        "block_uid": "B5|import|v31_n1024_baseline",
        "terminal_decoder_status": "not_applicable", "runtime_s": 0.0,
        "imported_records": 300, "per_source_counts": {"1M": 100, "1p5M": 100, "2M": 100},
        "integrity_ok": True, "success": True,
    }]
    for label in LABELS:
        for j in range(2):  # B0: exactly 6 records total
            recs.append(_decode_record("B0", label, j,
                                       l1_errors_initial=0, l1_errors_final=0,
                                       l2_errors_initial=0, l2_errors_final=0,
                                       exact=True, tag=True, syndrome=True,
                                       unsatisfied_checks=0, iterations=2,
                                       terminal_decoder_status="success",
                                       l1_decoder_status_verbatim="success",
                                       posterior_nll=0.016, posterior_entropy=0.033,
                                       truth_symbol_rank=0.0, calibration_bucket=0,
                                       posterior_anomaly_block=False,
                                       residual_syndrome_stats={"l1_residual_checks": 0,
                                                                "l2_residual_checks": 0},
                                       success=True))
        for i in range(20):
            init = 235 + (i * 7) % 17
            recs.append(_decode_record(
                "B1", label, i, l1_mode="oracle",
                l1_errors_initial=205 + i % 7, l1_errors_final=0,
                l1_decoder_status_verbatim="oracle_not_decoded",
                l2_errors_final=init + 167 + (i * 13) % 29,
                unsatisfied_checks=133, posterior_nll=229.5 + ((i * 17) % 160) / 10.0,
                posterior_entropy=0.31, truth_symbol_rank=0.208, posterior_anomaly_block=True))
            recs.append(_decode_record(
                "B2", label, i, l1_errors_initial=205 + i % 7, l1_errors_final=385 + i % 23,
                l2_errors_final=1024, terminal_decoder_status="not_run",
                posterior_nll=199.5, posterior_entropy=0.0197, truth_symbol_rank=0.206,
                residual_syndrome_stats={"l1_residual_checks": 1024, "l2_residual_checks": 11}))
            recs.append(_decode_record(
                "B3", label, i, l2_errors_final=max(0, init - 56 - (i * 11) % 23),
                posterior_nll=9.0 + i * 0.2))
            recs.append(_decode_record(
                "B4", label, i, l2_errors_final=max(0, init - 61 - (i * 5) % 19),
                posterior_nll=9.5 + i * 0.2))
    return recs


def make_counts(label: str) -> np.ndarray:
    """Deterministic tiny synthetic channel: diagonal + +-1 shifts only."""
    ser = SER[label]
    plus, minus = PM1_SPLIT[label]
    a = np.arange(audit.Q_SYMBOLS)
    w = 1.0 + (a % 7) * 0.01
    N = np.zeros((audit.Q_SYMBOLS, audit.Q_SYMBOLS), dtype=np.float64)
    N[a, a] += (1.0 - ser) * w
    N[a, (a + 1) % audit.Q_SYMBOLS] += ser * plus * w
    N[a, (a - 1) % audit.Q_SYMBOLS] += ser * minus * w
    return N


def _entropies_independent(N: np.ndarray) -> dict[str, float]:
    """Independent F03/A02 entropy recomputation (U1=a>>5, U2=a&31)."""

    def H(c):
        c = np.asarray(c, dtype=np.float64)
        t = c.sum()
        p = c[c > 0]
        return float(-np.sum((p / t) * np.log2(p / t))) if t > 0 else 0.0

    aa = np.arange(audit.Q_SYMBOLS)
    u1, u2 = aa // 32, aa % 32
    j_u1_b = np.zeros((32, audit.Q_SYMBOLS))
    np.add.at(j_u1_b, u1, N)
    j3 = np.zeros((32, 32, audit.Q_SYMBOLS))
    np.add.at(j3, (u1, u2), N)
    h_b = H(N.sum(axis=0))
    return {"L1": H(j_u1_b) - h_b, "L2": H(j3) - H(j_u1_b)}


def fixture_paths(fx: Path) -> dict[str, Path]:
    """Binding-key -> Path mapping WITHOUT touching the filesystem."""
    p = {
        "v32_per_block": fx / "per_block.jsonl",
        "v32_run_manifest": fx / "RUN_MANIFEST.json",
        "v32_candidate_terminal": fx / "candidate_terminal.json",
        "v32_terminal_reconstruction": fx / "terminal_reconstruction.json",
        "v25_channel_counts": fx / "channel_counts.npz",
        "v25_channel_summary": fx / "channel_summary.json",
        "v25_split_manifest": fx / "split_manifest.json",
        "v26_gate": fx / "gate26.json",
        "v26_run_manifest": fx / "manifest26.json",
        "v26_m0_report": fx / "m0_report.json",
        "v26_m1_report": fx / "m1_report.json",
        "v26_screen_results": fx / "screen_results.json",
        "v26_confirmation_results": fx / "confirmation_results.json",
        "v31_run_manifest": fx / "manifest31.json",
        "v31_matrix_audits": fx / "matrix_audits.json",
        "v31_m1_registry": fx / "m1_registry.json",
        "code_fact_harness": fx / "harness_fixture.py",
        "code_fact_sampler": fx / "sampler_fixture.py",
    }
    for b in range(6):
        p[f"v32_summary_B{b}"] = fx / f"summary_B{b}.json"
    return p


def build_fixtures(fx: Path, records: list[dict] | None = None) -> dict[str, Path]:
    fx.mkdir(parents=True, exist_ok=True)
    paths = fixture_paths(fx)

    def put(key: str, obj) -> Path:
        paths[key].write_text(json.dumps(obj, indent=1), encoding="utf-8")
        return paths[key]

    # Binding 1 — V32 run_01 evidence.
    lines = "\n".join(json.dumps(r) for r in (records if records is not None else make_records()))
    paths["v32_per_block"].write_text(lines + "\n", encoding="utf-8")
    for key in ("v32_run_manifest", "v32_candidate_terminal", "v32_terminal_reconstruction"):
        put(key, {"schema": SCHEMA})
    for b in range(6):
        put(f"v32_summary_B{b}", {"schema": SCHEMA})

    # Binding 2 — V25 run_04 empirical channel.
    counts_path = paths["v25_channel_counts"]
    counts = {f"{SIDS[l]}_N_ab_train_N_ab_train": make_counts(l) for l in LABELS}
    np.savez(counts_path, **counts)
    summary = {"schema": "nbldpc_v25_m0_v1", "per_source": {}}
    for label in LABELS:
        plus, minus = PM1_SPLIT[label]
        summary["per_source"][SIDS[label]] = {
            "n_pairs": 512000, "ser": SER[label],
            "pm1_mass": {"+1": SER[label] * plus, "-1": SER[label] * minus,
                         "0": 1.0 - SER[label]},
        }
    put("v25_channel_summary", summary)
    put("v25_split_manifest", {"schema": "split"})

    # Binding 3 — V26 run_02 DE artifacts.
    put("v26_gate", {"status": "pass_target_f13",
                     "best_passing_f": {"A01": 1.6, "A02": 1.3},
                     "passed": {"A01": [1.6], "A02": [1.3]}})
    put("v26_run_manifest", {
        "schema": "nbldpc_v26_run_manifest_v1", "run_id": "run_02", "role": "canonical",
        "terminal_state": "pass_target_f13", "best_passing_f": {"A01": 1.6, "A02": 1.3},
        "design_constants": {
            "screen_n_samples": 400, "screen_max_iter": 100,
            "screen_seeds": [26001, 26002], "confirm_n_samples": 2000,
            "confirm_max_iter": 200,
            "confirm_seeds": [26101, 26102, 26103, 26104, 26105],
            "entropy_tol_bits": 0.01, "streak": 20}})
    put("v26_m0_report", {"schema": "m0", "status": "ok"})
    put("v26_m1_report", {"schema": "m1", "status": "ok"})
    put("v26_screen_results", {
        "schema": "v26_screen_v1", "passed": {"A01": [1.6], "A02": [1.3]},
        "results": [{"arch": "A01", "f": 1.6, "pass": True},
                    {"arch": "A02", "f": 1.3, "pass": True}]})
    put("v26_confirmation_results", {
        "schema": "v26_confirm_v1", "passed": {"A01": [1.6], "A02": [1.3]},
        "results": [{"arch": "A01", "f": 1.6, "pass": True},
                    {"arch": "A02", "f": 1.3, "pass": True}]})

    # Binding 4 — V31 run_01 packet/allocation/leakage (H from independent impl).
    ent = {label: _entropies_independent(make_counts(label)) for label in LABELS}
    m2_map = {"1M": 184, "1p5M": 190, "2M": 192}
    leak = {"1M": 1064.0, "1p5M": 1094.0, "2M": 1104.0}
    sources = {}
    for label in LABELS:
        sources[label] = {
            "source_id": SIDS[label], "delay_used_ps": 50, "m_total": 200 + 6 * LABELS.index(label),
            "m1": 16, "m2": m2_map[label], "H": {"L1": ent[label]["L1"], "L2": ent[label]["L2"]},
            "leak_total_bits": leak[label], "f_total": 1.2949,
        }
    v31_manifest = {"schema": "nbldpc_v31_run_manifest_v1",
                    "configs": {"1024": {"schema": "nbldpc_v31_frozen_config_v1", "q": 32,
                                         "n": 1024, "m1": 16, "sources": sources}}}
    put("v31_run_manifest", v31_manifest)
    put("v31_matrix_audits", {
        "schema": "nbldpc_v31_matrix_audits_v1",
        "packets": [{"packet_id": "m1_16_n1024_n1024|QC-cyclic-projective",
                     "matrix_id": "m1_16_n1024_n1024|QC-cyclic-projective",
                     "allocation_id": "m1_16_n1024", "family": "QC-cyclic-projective",
                     "n": 1024, "m1": 16, "m2_by_source": m2_map,
                     "audits": {"L1": {"schema": "nbldpc_v31_matrix_audit_v1",
                                       "shape": [16, 1024]}}}],
        "rejected": []})
    registry_calls = []
    for label in LABELS:
        for layer, key in (("L1", "L1"), ("L2", "L2")):
            registry_calls.append({
                "allocation_id": "m1_16_n1024", "n": 1024, "m1": 16, "m2": m2_map[label],
                "source": label, "source_id": SIDS[label], "layer": layer, "seed": 30101,
                "rate": 1.0 - m2_map[label] / 1024.0,
                "H_bits_per_symbol": ent[label][key], "n_samples": 2000, "max_iter": 200})
    put("v31_m1_registry", {"schema": "registry", "registered_calls": registry_calls})

    # Bindings 5/6 — code facts at their cited line numbers.
    harness_lines = [f"# pad {i}" for i in range(554)] + HARNESS_SNIPPET.splitlines()
    paths["code_fact_harness"].write_text("\n".join(harness_lines) + "\n", encoding="utf-8")
    sampler_lines = [f"# pad {i}" for i in range(9)] + SAMPLER_SNIPPET.splitlines()
    paths["code_fact_sampler"].write_text("\n".join(sampler_lines) + "\n", encoding="utf-8")
    return paths


_FAKE_DIR: Path | None = None


class FakeRunner:
    """Serves binding paths WITHOUT rebuilding: whatever is on disk is served."""

    def __init__(self, fixture_dir: Path):
        self._paths = fixture_paths(Path(fixture_dir))

    def binding_paths(self) -> dict[str, Path]:
        return dict(self._paths)


def make_fake_runner() -> FakeRunner:
    assert _FAKE_DIR is not None, "test bug: fake fixture dir not set"
    return FakeRunner(_FAKE_DIR)


def _run(argv: list[str]) -> int:
    assert "--runner" in argv  # guard: tests never touch real bindings implicitly
    return audit.cli_main(argv)


def _flow(tmp_path: Path, records: list[dict] | None = None):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    root = tmp_path / "run_root"
    build_fixtures(_FAKE_DIR, records)
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    return root, rc


def _sub(sub: str, root: Path) -> int:
    return _run([sub, "--runner", RUNNER_SPEC, "--run-root", str(root)])


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(Path(root).iterdir())}


def _tamper_manifest(root: Path, fn) -> None:
    mp = Path(root) / "audit_manifest.json"
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    fn(manifest)
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# T0 — structural / tiny math
# --------------------------------------------------------------------------- #

def test_t0_import_and_frozen_constants():
    assert audit.PER_BLOCK_SCHEMA == "nbldpc_v32_bridge_block_result_v1"
    assert audit.EXPECTED_COUNTS == {"B5": 1, "B0": 6, "B1": 60, "B2": 60, "B3": 60, "B4": 60}
    assert audit.FROZEN_RAW_SER == {"1M": 0.239779296875, "1p5M": 0.2544695292735815,
                                    "2M": 0.2557409550754458}
    assert audit.DELTA_BIN_EDGES[0] == -1024 and audit.DELTA_BIN_EDGES[-1] == 1024
    assert audit.LOG2_EDGES_BITS_PER_SYMBOL[0] == 2.0 ** -20
    assert audit.DEFAULT_RUN_ROOT.name == "run_01"
    assert audit.DEFAULT_RUN_ROOT.parent.name == "nbldpc_v32_operating_point_audit"


def test_t0_q_construction_toy():
    q = audit.build_q_joint(0.25)
    assert abs(q.sum() - 1.0) <= 1e-12                       # mass conservation
    assert q[0, 0] == pytest.approx(0.75 / audit.Q_SYMBOLS)  # diagonal mass
    offdiag = q[~np.eye(audit.Q_SYMBOLS, dtype=bool)]
    assert offdiag.min() > 0.0                               # full b!=a support
    assert offdiag.sum() == pytest.approx(0.25, abs=1e-12)   # substitution mass
    assert np.allclose(offdiag, 0.25 / ((audit.Q_SYMBOLS - 1) * audit.Q_SYMBOLS))


def _mini(uid, arm, final, initial, anomaly=False, status="max_iter_reached",
          syndrome=False, exact=False):
    return {"block_uid": uid, "arm": arm, "l2_errors_final": final,
            "l2_errors_initial": initial, "posterior_anomaly_block": anomaly,
            "terminal_decoder_status": status, "syndrome": syndrome, "exact": exact}


def test_t0_sentinel_recognition_synthetic_b2():
    by_arm = {
        "B1": [_mini("b1", "B1", 400, 240, anomaly=True)] * 1,
        "B2": [_mini("b2", "B2", 1024, 240, status="not_run")],
        "B3": [_mini("b3", "B3", 179, 250)],
        "B4": [_mini("b4", "B4", 180, 251)],
    }
    res = audit.check_d0_predicates(by_arm)
    assert res["predicates"]["P-ii_B2_sentinel_not_run"]["passed"] is True
    # Sentinel mishandling: a B2 record without the sentinel must be flagged.
    by_arm["B2"] = [_mini("bad", "B2", 512, 240, status="not_run")]
    res = audit.check_d0_predicates(by_arm)
    assert res["predicates"]["P-ii_B2_sentinel_not_run"]["passed"] is False
    assert res["predicates"]["P-ii_B2_sentinel_not_run"]["violating_block_uids"] == ["bad"]
    assert res["signature_mismatch"] is True


def test_t0_branch_table_totality():
    literal = [(b["branch"], b["condition"]) for b in audit.BRANCH_TABLE]
    assert literal == [("A", "total infeasible"),
                       ("B", "total feasible 且 L2 allocation infeasible"),
                       ("C", "layer 与 total 均可行")]
    allowed = {"A", "B", "C", "inconclusive"}
    seen = set()
    for l1, l2, tv, tp in itertools.product([False, True], repeat=4):
        out = audit.map_branch(l1, l2, tv, tp)
        assert out["branch"] in allowed and out["reasons"]
        seen.add(out["branch"])
    assert seen <= allowed and "inconclusive" in seen
    assert audit.map_branch(True, False, True, True)["branch"] == "B"
    assert audit.map_branch(False, False, False, False)["branch"] == "A"
    assert audit.map_branch(True, True, True, True)["branch"] == "C"
    assert audit.map_branch(True, True, True, False)["branch"] == "inconclusive"


def test_t0_collision_refusal(tmp_path):
    root = tmp_path / "run_root"
    root.mkdir()
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)]) == audit.EXIT_COLLISION
    assert list(root.iterdir()) == []  # nothing written into the pre-existing root


def test_t0_static_checks_no_production_execution():
    token = "." + "ttbin"  # built dynamically: this file itself must stay clean too
    audit_src = Path(audit.__file__).read_text(encoding="utf-8")
    test_src = Path(__file__).read_text(encoding="utf-8")
    assert token not in audit_src and token not in test_src

    allowed = {"argparse", "hashlib", "importlib", "json", "math", "sys",
               "datetime", "pathlib", "numpy", "__future__"}
    tree = ast.parse(audit_src)
    imports = set()
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            f = node.func
            calls.append(getattr(f, "id", None) or getattr(f, "attr", "") or "")
    assert imports <= allowed, sorted(imports - allowed)
    for tok in ("decode", "synth_channel", "mcde"):
        hits = [c for c in calls if tok in c.lower()]
        assert not hits, (tok, hits)

    ttree = ast.parse(test_src)
    prod = [(n.module, sorted(a.name for a in n.names)) for n in ast.walk(ttree)
            if isinstance(n, ast.ImportFrom) and n.module
            and n.module.startswith("comparison_bench")]
    assert prod == [("comparison_bench.src.comparison_bench.cli",
                     ["run_nonbinary_v32_operating_point_audit"])]
    cli_call_sites = [n for n in ast.walk(ttree)
                      if isinstance(n, ast.Call) and
                      (getattr(n.func, "attr", None) or getattr(n.func, "id", "")) == "cli_main"]
    assert len(cli_call_sites) == 1  # only via the --runner-guarded helper `_run`


# --------------------------------------------------------------------------- #
# T1 — tamper / drift refusals
# --------------------------------------------------------------------------- #

def test_t1_missing_input_file(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    (_FAKE_DIR / "summary_B3.json").unlink()
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "r")])
    assert rc == audit.EXIT_BINDING
    assert not (tmp_path / "r" / "audit_manifest.json").exists()


def test_t1_truncated_jsonl(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    p = _FAKE_DIR / "per_block.jsonl"
    good = json.dumps(make_records()[0])
    p.write_text(good + '\n{"schema": "nbldpc_v32_bridge_bl', encoding="utf-8")
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "r")])
    assert rc == audit.EXIT_EVIDENCE


def test_t1_duplicate_block_uid(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    p = _FAKE_DIR / "per_block.jsonl"
    recs = make_records()
    recs.append(dict(recs[10]))  # duplicate a decode record verbatim
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "r")])
    assert rc == audit.EXIT_EVIDENCE


def test_t1_arm_label_tamper(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    p = _FAKE_DIR / "per_block.jsonl"
    recs = make_records()
    tampered = [dict(r, arm="B9") if r.get("arm") == "B3" else r for r in recs]
    p.write_text("\n".join(json.dumps(r) for r in tampered) + "\n", encoding="utf-8")
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "r")])
    assert rc == audit.EXIT_EVIDENCE


@pytest.mark.parametrize("fname,mangle", [
    ("per_block.jsonl",
     lambda p: p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")),
    ("channel_summary.json", lambda p: p.write_bytes(p.read_bytes() + b"\n")),
    ("gate26.json", lambda p: p.write_bytes(p.read_bytes() + b" ")),
    ("manifest31.json", lambda p: p.write_bytes(p.read_bytes() + b" ")),
], ids=["binding1_per_block", "binding2_channel_summary",
        "binding3_gate", "binding4_v31_manifest"])
def test_t1_input_drift_rejection(tmp_path, fname, mangle):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    mangle(tmp_path / "fixtures" / fname)
    assert _sub("d1", root) == audit.EXIT_BINDING


def test_t1_threshold_tamper_detected(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    _tamper_manifest(root, lambda m: m["frozen"]["thresholds"].__setitem__(
        "expected_nll_ratio_K", 99.0))
    assert _sub("d1", root) == audit.EXIT_MANIFEST


def test_t1_mc_seed_and_sample_size_drift(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    _tamper_manifest(root, lambda m: m["frozen"]["mc_plan"].__setitem__("seed", 1))
    assert _sub("d1", root) == audit.EXIT_MANIFEST


def test_t1_histogram_bin_drift(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    _tamper_manifest(root, lambda m: m["frozen"]["histogram_bins"].__setitem__(
        "error_delta_bin_edges", [-999] + audit.DELTA_BIN_EDGES[1:]))
    assert _sub("d0", root) == audit.EXIT_MANIFEST


def test_t1_margin_method_tamper(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    _tamper_manifest(root, lambda m: m["frozen"].__setitem__(
        "margin_method", "normal approximation"))
    assert _sub("d2", root) == audit.EXIT_MANIFEST


def test_t1_branch_table_tamper(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    _tamper_manifest(root, lambda m: m["frozen"]["branch_table"][0].__setitem__("branch", "Z"))
    assert _sub("d2", root) == audit.EXIT_MANIFEST


def test_t1_out_of_root_write_rejection(tmp_path):
    root = tmp_path / "run_root"
    root.mkdir()
    for bad in ("../evil.json", "sub/dir.json", "..\\evil.json"):
        with pytest.raises(audit.AuditStop) as ei:
            audit._safe_path(root, bad)
        assert ei.value.code == audit.EXIT_WRITE


def test_t1_output_root_collision_end_to_end(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    before = _snapshot(root)
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)]) == audit.EXIT_COLLISION
    assert _snapshot(root) == before  # byte-identical: no overwrite happened


def test_t1_sentinel_mishandling_detection(tmp_path):
    recs = make_records()
    victim = next(r for r in recs if r.get("arm") == "B2")
    victim["l2_errors_final"] = 512  # sentinel value broken -> predicate must fire
    root, rc = _flow(tmp_path, records=recs)
    assert rc == audit.EXIT_OK  # recorded, never silently reconciled nor fatal
    d0 = json.loads((root / "d0_signature.json").read_text(encoding="utf-8"))
    assert d0["signature_mismatch"] is True
    pred = d0["predicates"]["P-ii_B2_sentinel_not_run"]
    assert pred["passed"] is False and victim["block_uid"] in pred["violating_block_uids"]
    assert "l2_error_delta_histogram" not in d0["aggregation_arm_x_source"]["B2|1M"]


# --------------------------------------------------------------------------- #
# T2 — fake qualification full flow
# --------------------------------------------------------------------------- #

def test_t2_fake_flow_d0_to_branch_order_and_files(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    assert {p.name for p in root.iterdir()} == SHALL_O1_FILES  # SHALL-O1 exact set
    manifest = json.loads((root / "audit_manifest.json").read_text(encoding="utf-8"))
    order = ["manifest_freeze", "d0", "d1", "d2", "d3", "final_branch_decision"]
    assert manifest["execution_order"] == order
    decision = json.loads((root / "final_branch_decision.json").read_text(encoding="utf-8"))
    assert decision["generated_by_execution_order"] == order
    assert decision["selected_branch"] == "C"
    assert [(b["branch"], b["condition"]) for b in decision["branch_table_frozen"]] == [
        ("A", "total infeasible"), ("B", "total feasible 且 L2 allocation infeasible"),
        ("C", "layer 与 total 均可行")]
    assert decision["d0_signature_mismatch"] is False


def test_t2_independent_recomputation_matches_persisted(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    recs = make_records()
    d0 = json.loads((root / "d0_signature.json").read_text(encoding="utf-8"))
    assert d0["records_total"] == len(recs)
    counts = {}
    for r in recs:
        counts[r["arm"]] = counts.get(r["arm"], 0) + 1
    assert d0["arm_record_counts"] == counts
    b3_vals = [r["l2_errors_initial"] for r in recs
               if r["arm"] == "B3" and r["source"] == "1M"]
    got = d0["aggregation_arm_x_source"]["B3|1M"]["l2_errors_initial"]["mean"]
    assert got == pytest.approx(float(np.mean(b3_vals)), rel=1e-15)
    assert all(v["passed"] for v in d0["predicates"].values())
    assert d0["signature_mismatch"] is False
    assert "l2_error_delta_histogram" not in d0["aggregation_arm_x_source"]["B2|1M"]

    d1 = json.loads((root / "d1_consistency.json").read_text(encoding="utf-8"))
    for label in LABELS:
        ser = SER[label]
        zero_offdiag = audit.Q_SYMBOLS * (audit.Q_SYMBOLS - 1) - 2 * audit.Q_SYMBOLS
        expected_zero_mass = zero_offdiag * ser / ((audit.Q_SYMBOLS - 1) * audit.Q_SYMBOLS)
        sm = d1["per_source"][label]["support_miss"]
        assert sm["q_mass_on_p_zero_cells"] == pytest.approx(expected_zero_mass, rel=1e-12)
        own = d1["per_source"][label]["dual_expected_nll"][
            "E_V25_nll_under_own_posterior_bits_per_symbol"]
        ent = _entropies_independent(make_counts(label))
        assert own["L1"] == pytest.approx(ent["L1"], rel=1e-9)
        assert own["L2"] == pytest.approx(ent["L2"], rel=1e-9)
        assert d1["per_source"][label]["raw_ser"] == ser

    d2 = json.loads((root / "d2_feasibility.json").read_text(encoding="utf-8"))
    m2_map = {"1M": 184, "1p5M": 190, "2M": 192}
    leak = {"1M": 1064.0, "1p5M": 1094.0, "2M": 1104.0}
    for label in LABELS:
        ps = d2["per_source"][label]
        ent_l = _entropies_independent(make_counts(label))
        gap_l2 = m2_map[label] * 5.0 - ent_l["L2"] * 1024
        assert ps["margin_simple_gap_n1024"]["gap_L2_bits"] == pytest.approx(gap_l2, rel=1e-12)
        assert ps["leakage_bits"]["L1_syndrome"] == 80.0
        assert ps["leakage_bits"]["L2_syndrome"] == m2_map[label] * 5.0
        assert ps["leakage_bits"]["total_verbatim_leak_total_bits"] == leak[label]
        assert ps["leakage_bits"]["total_pure_syndrome_recomputed"] == (16 + m2_map[label]) * 5.0
        assert all(ps["feasible"].values())
        assert ps["v31_manifest_quoted"]["leak_total_bits"] == leak[label]

    d3 = json.loads((root / "d3_v26_evidence.json").read_text(encoding="utf-8"))
    assert d3["new_DE_change_required"] is True
    assert len(d3["minimal_DE_question_list"]) == 2
    assert d3["no_DE_executed_inside_this_change"] is True
    assert "pass_target_f13" in json.dumps(d3["v26_pass_location"])

    bi = {"l1_all_ok": True, "l2_all_ok": True, "total_verbatim_ok": True,
          "total_pure_ok": True}
    decision = json.loads((root / "final_branch_decision.json").read_text(encoding="utf-8"))
    assert decision["branch_inputs"] == bi
    assert decision["selected_branch"] == audit.map_branch(**bi)["branch"]


def test_t2_new_de_change_required_true_and_collision(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == audit.EXIT_OK
    d3 = json.loads((root / "d3_v26_evidence.json").read_text(encoding="utf-8"))
    assert d3["new_DE_change_required"] is True
    assert d3["code_facts_cited_verbatim"]["de_sampler_draws_AB_from_P_AB"]["citation"].endswith(
        "nonbinary_v26_channel.py L10-13")
    # collision path end-to-end: second `all` refuses and changes nothing
    before = _snapshot(root)
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)]) == audit.EXIT_COLLISION
    assert _snapshot(root) == before
