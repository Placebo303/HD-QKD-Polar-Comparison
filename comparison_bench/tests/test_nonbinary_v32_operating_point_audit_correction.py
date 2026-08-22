"""T0/T1/T2 suite for the NB-LDPC V32 operating-point audit CORRECTION verifier.

Layering per design §11 of change
``formal-nonbinary-ldpc-v32-operating-point-audit-correction``:

- T0: structure / tiny support-mismatch math / infinity semantics / frozen-rate
  verbatim constants / AST import whitelist / input-output same-root rejection.
- T1: unit + tamper (D0 classification, B2 sentinel exclusion, B3/B4 naming,
  D1 analytic-vs-MC on a toy law, conditional/truncated labels, dual-law
  coexistence, D3 wording, overwrite guard, forbidden-string schema targets,
  manifest missing/drift rejection, duplicate block_uid STOP, out-of-root write).
- T2: fake qualification full flow via explicit ``--runner`` injection — never a
  production decoder, DE sampler or pipeline; strict replay; tamper series;
  mechanical terminal-priority routing.

Every run root is a fresh ``workspace/<fresh-id>/`` directory created through
pytest ``--basetemp`` (see the four-tier commands in the change tasks).

# ponytail: fixtures reuse the v1 audit suite's proven patterns (records/counts/
# independent entropies) adapted to the v2 binding table; if v1 fixtures drift,
# update both together.
"""
from __future__ import annotations

import ast
import json
import math
import py_compile
import shutil
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v32_operating_point_audit_correction as corr,
)

RUNNER_SPEC = __name__ + ":make_fake_runner"

LABELS = ("1M", "1p5M", "2M")
SIDS = dict(corr.SOURCE_IDS)
SER = dict(corr.FROZEN_RAW_SER)
PM1_SPLIT = {"1M": (0.995, 0.005), "1p5M": (0.02, 0.98), "2M": (0.98, 0.02)}
SCHEMA = corr.PER_BLOCK_SCHEMA

# Typed independently from the spec (never imported) so a constant regression
# in the CLI cannot mask itself.
QUESTION_LITERAL = (
    "在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，对应 ensemble DE "
    "是否在三源、两层全部收敛？"
)
RATES_LITERAL = {
    "L1": {"1M": 0.984375, "1p5M": 0.984375, "2M": 0.984375},
    "L2": {"1M": 0.8203125, "1p5M": 0.814453125, "2M": 0.8125},
}
SCOPE_NOMINAL_LITERAL = (
    "nominal information budget feasible only — no finite-length/DE/"
    "fixed-graph/decoder feasibility claim"
)
INFEASIBLE_LITERAL = "information-theoretically infeasible at current allocation"
SENTINEL_DEF_LITERAL = (
    "l2_errors_final==1024 AND terminal_decoder_status=='not_run': L1 failed "
    "so L2 never ran and x2_hat does not exist (C2)"
)
TERMINALS_LITERAL = [
    "audit_evidence_inconsistent",
    "audit_verifier_blocked",
    "audit_corrected_rate_aligned_de_required",
]
LIFECYCLE_LITERAL = [
    "post_hoc_exploratory_only",
    "not_formal_pre_registered_gate",
    "numerical_outputs_retained",
    "scientific_terminal_superseded_pending_correction",
]
_READY = "-ready"  # built dynamically: this file must not carry banned tails verbatim
FORBIDDEN_TAILS = ("qualification" + _READY, "promotion" + _READY, "deployment" + _READY)

EIGHT_FILES = {
    "audit_manifest.json", "d0_failure_signature.json", "d1_support_mismatch.json",
    "d2_dual_law_feasibility.json", "d3_next_question.json",
    "corrected_branch_decision.json", "readonly_review.json", "operator_handoff.md",
}
SIX_FILES = EIGHT_FILES - {"readonly_review.json", "operator_handoff.md"}

H_Q_APPROX = {"1M": 3.1921, "1p5M": 3.3626, "2M": 3.3773}
REQ_Q_APPROX = {"1M": 3268.7, "1p5M": 3443.3, "2M": 3458.4}
GAP_B_APPROX = {"1M": -2268.7, "1p5M": -2413.3, "2M": -2418.4}
PURE_TOTAL = {"1M": 1000.0, "1p5M": 1030.0, "2M": 1040.0}
LEAK_VERBATIM = {"1M": 1064.0, "1p5M": 1094.0, "2M": 1104.0}


# --------------------------------------------------------------------------- #
# Fake fixtures (synthetic per_block-like records + tiny channel_counts npz)
# --------------------------------------------------------------------------- #

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
    """247 synthetic records: B5=1 / B0=6 / B1..B4=60 each, B2 sentinel rows."""
    recs = [{
        "schema": SCHEMA, "kind": "baseline_import", "arm": "B5", "source": "all",
        "source_id": None, "seed_or_block_id": None,
        "block_uid": "B5|import|v31_n1024_baseline",
        "terminal_decoder_status": "not_applicable", "runtime_s": 0.0,
        "imported_records": 300, "per_source_counts": {"1M": 100, "1p5M": 100, "2M": 100},
        "integrity_ok": True, "success": True,
    }]
    for label in LABELS:
        for j in range(2):
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
    a = np.arange(corr.Q_SYMBOLS)
    w = 1.0 + (a % 7) * 0.01
    n = np.zeros((corr.Q_SYMBOLS, corr.Q_SYMBOLS), dtype=np.float64)
    n[a, a] += (1.0 - ser) * w
    n[a, (a + 1) % corr.Q_SYMBOLS] += ser * plus * w
    n[a, (a - 1) % corr.Q_SYMBOLS] += ser * minus * w
    return n


def _entropies_independent(n: np.ndarray) -> dict[str, float]:
    """Independent F03/A02 recomputation (U1=a>>5, U2=a&31), different code path."""

    def h(c):
        c = np.asarray(c, dtype=np.float64)
        t = c.sum()
        p = c[c > 0]
        return float(-np.sum((p / t) * np.log2(p / t))) if t > 0 else 0.0

    aa = np.arange(corr.Q_SYMBOLS)
    u1, u2 = aa // 32, aa % 32
    j_u1_b = np.zeros((32, corr.Q_SYMBOLS))
    np.add.at(j_u1_b, u1, n)
    j3 = np.zeros((32, 32, corr.Q_SYMBOLS))
    np.add.at(j3, (u1, u2), n)
    h_b = h(n.sum(axis=0))
    return {"L1": h(j_u1_b) - h_b, "L2": h(j3) - h(j_u1_b)}


def _h2(x: float) -> float:
    return float(-x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x))


def fixture_paths(fx: Path) -> dict[str, Path]:
    """Binding-key -> Path mapping for the correction verifier (no filesystem IO)."""
    p = {
        "v32_per_block": fx / "per_block.jsonl",
        "v32_run_manifest": fx / "RUN_MANIFEST.json",
        "v32_candidate_terminal": fx / "candidate_terminal.json",
        "oldaudit_audit_manifest_json": fx / "old_audit_manifest.json",
        "oldaudit_d0_signature_json": fx / "old_d0_signature.json",
        "oldaudit_d1_consistency_json": fx / "old_d1_consistency.json",
        "oldaudit_d2_feasibility_json": fx / "old_d2_feasibility.json",
        "oldaudit_d3_v26_evidence_json": fx / "old_d3_v26_evidence.json",
        "oldaudit_d0_signature_md": fx / "old_d0_signature.md",
        "oldaudit_d1_consistency_md": fx / "old_d1_consistency.md",
        "oldaudit_d2_feasibility_md": fx / "old_d2_feasibility.md",
        "oldaudit_d3_v26_evidence_md": fx / "old_d3_v26_evidence.md",
        "oldaudit_final_branch_decision": fx / "old_final_branch_decision.json",
        "v25_channel_counts": fx / "channel_counts.npz",
        "v25_channel_summary": fx / "channel_summary.json",
        "v25_split_manifest": fx / "split_manifest.json",
        "v26_gate": fx / "gate26.json",
        "v26_RUN_MANIFEST": fx / "manifest26.json",
        "v26_screen_results": fx / "screen_results.json",
        "v26_confirmation_results": fx / "confirmation_results.json",
        "v31_RUN_MANIFEST": fx / "manifest31.json",
        "v31_matrix_audits": fx / "matrix_audits.json",
        "v31_m1_registry": fx / "m1_registry.json",
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

    lines = "\n".join(json.dumps(r) for r in (records if records is not None else make_records()))
    paths["v32_per_block"].write_text(lines + "\n", encoding="utf-8")
    put("v32_run_manifest", {"schema": SCHEMA})
    # Persisted terminal read as DISTRUSTED: carries the superseded historical
    # attribution which must be recorded but must never reach any v2 conclusion.
    put("v32_candidate_terminal", {"schema": SCHEMA,
                                   "terminal": "finite_graph_decoder_mismatch"})
    for b in range(6):
        put(f"v32_summary_B{b}", {"schema": SCHEMA})

    for n in ("audit_manifest", "d0_signature", "d1_consistency", "d2_feasibility",
              "d3_v26_evidence"):
        put(f"oldaudit_{n}_json", {"note": "v1 artifact; cross-reference only, untrusted"})
    for n in ("d0_signature", "d1_consistency", "d2_feasibility", "d3_v26_evidence"):
        paths[f"oldaudit_{n}_md"].write_text("# v1 artifact\n", encoding="utf-8")
    put("oldaudit_final_branch_decision", {"branch": "superseded_pending_correction"})

    counts = {f"{SIDS[l]}_N_ab_train_N_ab_train": make_counts(l) for l in LABELS}
    np.savez(paths["v25_channel_counts"], **counts)
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

    put("v26_gate", {"status": "pass_target_f13",
                     "best_passing_f": {"A01": 1.6, "A02": 1.3}})
    put("v26_RUN_MANIFEST", {"schema": "nbldpc_v26_run_manifest_v1", "run_id": "run_02",
                             "design_constants": {"entropy_tol_bits": 0.01}})
    put("v26_screen_results", {"passed": {"A01": [1.6], "A02": [1.3]}})
    put("v26_confirmation_results", {"passed": {"A01": [1.6], "A02": [1.3]}})

    m2_map = {"1M": 184, "1p5M": 190, "2M": 192}
    ent = {label: _entropies_independent(make_counts(label)) for label in LABELS}
    sources = {}
    for label in LABELS:
        sources[label] = {
            "source_id": SIDS[label], "delay_used_ps": 50,
            "m_total": m2_map[label] + 16, "m1": 16, "m2": m2_map[label],
            "H": {"L1": ent[label]["L1"], "L2": ent[label]["L2"]},
            "leak_total_bits": LEAK_VERBATIM[label], "f_total": 1.2949,
        }
    put("v31_RUN_MANIFEST", {
        "schema": "nbldpc_v31_run_manifest_v1",
        "configs": {"1024": {"schema": "nbldpc_v31_frozen_config_v1", "q": 32,
                             "n": 1024, "m1": 16, "sources": sources}}})
    put("v31_matrix_audits", {
        "packets": [
            {"packet_id": "decoy_other_packet|x", "audits": {"L1": {"shape": [8, 2048]}}},
            {"packet_id": corr.PACKET_ID, "allocation_id": corr.ALLOCATION_ID,
             "audits": {"L1": {"shape": [16, 1024]}}},
        ]})
    registry_calls = []
    for label in LABELS:
        for layer in ("L1", "L2"):
            registry_calls.append({
                "allocation_id": corr.ALLOCATION_ID, "layer": layer, "source": label,
                "rate": corr.LAYER_RATE_TABLE_FROZEN[layer][label]})
    # Decoy allocation with wrong rates: stage-0 MUST filter by allocation id and
    # therefore ignore these (a full-table scan would wrongly STOP here).
    for label in LABELS[:2]:
        registry_calls.append({"allocation_id": "m1_16_n2048_decoy", "layer": "L2",
                               "source": label, "rate": 0.5})
    put("v31_m1_registry", {"registered_calls": registry_calls})
    return paths


class FakeRunner:
    """Serves fixture binding paths; whatever is on disk is served."""

    def __init__(self, fixture_dir: Path):
        self._paths = fixture_paths(Path(fixture_dir))

    def binding_paths(self) -> dict[str, Path]:
        return dict(self._paths)


_FAKE_DIR: Path | None = None


def make_fake_runner() -> FakeRunner:
    assert _FAKE_DIR is not None, "test bug: fake fixture dir not set"
    return FakeRunner(_FAKE_DIR)


def _run(argv: list[str]) -> int:
    assert "--runner" in argv  # guard: tests never touch real bindings implicitly
    return corr.cli_main(argv)


def _flow(tmp_path: Path, records: list[dict] | None = None):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    root = tmp_path / "run_root"
    build_fixtures(_FAKE_DIR, records)
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    return root, rc


def _sub(sub: str, root: Path) -> int:
    return _run([sub, "--runner", RUNNER_SPEC, "--run-root", str(root)])


def _load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(Path(root).iterdir())}


def _frozen() -> dict:
    return {
        "thresholds": corr.THRESHOLDS,
        "mc_plan": dict(corr.MC_PLAN),
        "histogram_bins": {
            "error_delta_bin_edges": list(corr.DELTA_BIN_EDGES),
            "log2_edges_bits_per_symbol": list(corr.LOG2_EDGES_BITS_PER_SYMBOL),
        },
        "margin_method": corr.MARGIN_METHOD,
        "h_cross_check_tol_bits": corr.H_CROSS_CHECK_TOL_BITS,
    }


def _mini(uid, arm, final, initial, anomaly=False, status="max_iter_reached",
          syndrome=False, exact=False):
    return {"block_uid": uid, "arm": arm, "l2_errors_final": final,
            "l2_errors_initial": initial, "posterior_anomaly_block": anomaly,
            "terminal_decoder_status": status, "syndrome": syndrome, "exact": exact}


# --------------------------------------------------------------------------- #
# T0 — structure / tiny math / semantics
# --------------------------------------------------------------------------- #

def test_t0_py_compile_and_import(tmp_path):
    cfile = tmp_path / "compiled.pyc"
    py_compile.compile(str(Path(corr.__file__)), cfile=str(tmp_path / "cli.pyc"), doraise=True)
    py_compile.compile(str(Path(__file__)), cfile=str(cfile), doraise=True)
    assert corr.EXIT_OK == 0 and corr.EXIT_COLLISION == 2 and corr.EXIT_WRITE == 6
    assert callable(corr.cli_main) and corr.DEFAULT_RUN_ROOT.name == "run_01"


def test_t0_cli_help(capsys):
    with pytest.raises(SystemExit) as ei:
        corr.cli_main(["--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    for token in ("d0", "d1", "d2", "d3", "all", "--runner", "--run-root",
                  "binding provider injection"):
        assert token in out, token


def test_t0_frozen_constants_verbatim():
    assert corr.EXPECTED_COUNTS == {"B5": 1, "B0": 6, "B1": 60, "B2": 60, "B3": 60, "B4": 60}
    assert corr.FROZEN_RAW_SER == {"1M": 0.239779296875, "1p5M": 0.2544695292735815,
                                   "2M": 0.2557409550754458}
    assert corr.LAYER_RATE_TABLE_FROZEN == RATES_LITERAL          # design §7 verbatim
    assert corr.TERMINAL_PRIORITY == TERMINALS_LITERAL             # DEF-5 strict order
    assert corr.LIFECYCLE_NOTE == LIFECYCLE_LITERAL
    assert corr.D3_QUESTION == QUESTION_LITERAL
    assert corr.CONCLUSION_SCOPE_NOMINAL == SCOPE_NOMINAL_LITERAL  # C5 verbatim
    assert corr.Q_B1_INFEASIBLE_CONCLUSION == INFEASIBLE_LITERAL   # C6 verbatim
    assert corr.ALLOCATION_ID == "m1_16_n1024"
    assert corr.PACKET_ID == "m1_16_n1024_n1024|QC-cyclic-projective"
    assert corr.MC_PLAN["seed"] == 20260822 and corr.MC_PLAN["n_samples"] == 100000
    assert corr.MC_PLAN["quantiles"] == [0.05, 0.5, 0.95]
    assert set(corr.OUTPUT_FILES_EIGHT) == EIGHT_FILES
    assert corr.DEFAULT_RUN_ROOT.parent.name == "nbldpc_v32_operating_point_audit_v2"


def test_t0_q_joint_closed_form_toy():
    q = corr.build_q_joint(0.25)
    assert abs(q.sum() - 1.0) <= 1e-12                        # mass conservation
    assert q[0, 0] == pytest.approx(0.75 / corr.Q_SYMBOLS)     # diagonal mass
    offdiag = q[~np.eye(corr.Q_SYMBOLS, dtype=bool)]
    assert offdiag.min() > 0.0                                 # full b!=a support
    assert offdiag.sum() == pytest.approx(0.25, abs=1e-12)
    q0 = corr.build_q_joint(0.0)
    assert np.array_equal(q0, np.eye(corr.Q_SYMBOLS) / corr.Q_SYMBOLS)  # ser=0 hand case


def test_t0_uniform_p_toy_zero_support_miss_finite_full_nll(tmp_path):
    """Fix task B, both directions of the iff semantics.

    Direction 1 — uniform P has NO P-zero cells, so q_mass_on_p_zero_cells
    == 0 and the full expected NLL MUST be the JSON-safe finite analytic
    value (uniform 1024x1024 table => E_Q[-log2 P] = log2(1048576) = 20 bits
    exactly); it must NEVER be the string "infinity".

    Direction 2 — a sparse diagonal+/-1 toy leaves most cells at P=0 while
    Q covers everything, so q_mass_on_p_zero_cells > 0 and the full expected
    NLL MUST be exactly the string "infinity".

    After fix B the implementation derives both from the same condition, so
    ``signature_mismatch`` (the old honest-mislabel alarm) stays False in
    both directions.
    """
    q = corr.Q_SYMBOLS
    out = tmp_path / "out"
    out.mkdir()

    # ---- direction 1: zero support miss -> finite full expected NLL ----
    npz = tmp_path / "uniform.npz"
    np.savez(npz, **{f"{SIDS[l]}_N_ab_train_N_ab_train": np.full((q, q), 1024.0)
                     for l in LABELS})
    res = corr.run_d1(out, {"v25_channel_counts": npz}, _frozen())
    assert set(res["per_source"]) == set(LABELS)
    for lbl, v in res["per_source"].items():
        sm = v["support_miss"]
        assert sm["q_mass_on_p_zero_cells_analytic"] == 0.0
        assert v["full_expected_nll"] != "infinity"
        assert v["full_expected_nll"] == pytest.approx(20.0, abs=1e-9)
        assert "no mass on P-zero cells" in v["full_expected_nll_derivation"]
        ce = v["truncated_common_support_cross_entropy"]
        assert ce["value_bits"] == pytest.approx(20.0, abs=1e-9)
        assert ce["common_support_cell_count"] == q * q
        cm = v["conditional_finite_support_mean"]
        assert cm["mean_bits_per_symbol"] == pytest.approx(10.0, abs=1e-12)
        for val in cm["quantiles_bits_per_symbol"].values():
            assert val == pytest.approx(10.0, abs=1e-12)
        assert sm["zero_hit_count_mc"] == 0 and sm["zero_hit_frequency_mc"] == 0.0
        assert cm["mc_seed"] == 20260822
    assert res["signature_mismatch"] is False

    # ---- direction 2: positive support miss -> "infinity" ----
    npz_pos = tmp_path / "sparse.npz"
    np.savez(npz_pos, **{f"{SIDS[l]}_N_ab_train_N_ab_train": make_counts(l)
                         for l in LABELS})
    out2 = tmp_path / "out2"
    out2.mkdir()
    res2 = corr.run_d1(out2, {"v25_channel_counts": npz_pos}, _frozen())
    for lbl, v in res2["per_source"].items():
        sm = v["support_miss"]
        assert sm["q_mass_on_p_zero_cells_analytic"] > 0
        assert v["full_expected_nll"] == "infinity"
        assert bool(v["full_expected_nll_derivation"])
    assert res2["signature_mismatch"] is False


def test_t0_same_input_output_root_rejected(tmp_path):
    global _FAKE_DIR
    fx = tmp_path / "fixtures"
    build_fixtures(fx)
    _FAKE_DIR = fx
    before = sorted((p.name, p.stat().st_size) for p in fx.iterdir())
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(fx)])
    assert rc == corr.EXIT_COLLISION  # existing root (the inputs themselves) -> STOP
    after = sorted((p.name, p.stat().st_size) for p in fx.iterdir())
    assert before == after  # nothing written into the input root


def test_t0_static_import_whitelist_no_forbidden_calls():
    cli_src = Path(corr.__file__).read_text(encoding="utf-8")
    allowed = {"argparse", "hashlib", "importlib", "json", "math", "os", "subprocess",
               "sys", "datetime", "pathlib", "numpy", "__future__"}
    tree = ast.parse(cli_src)
    imports, calls = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            f = node.func
            calls.append(getattr(f, "id", None) or getattr(f, "attr", "") or "")
    assert imports <= allowed, sorted(imports - allowed)
    blacklist = ["decode", "synth", "mcde", "ttbin", "de_sample", "graph_build",
                 "finite_control", "longrun", "minrerun", "routea"]
    for tok in blacklist:
        hits = [c for c in calls if tok in c.lower()]
        assert not hits, (tok, hits)
    # Banned tails appear in the CLI only inside the FORBIDDEN_CONCLUSION_STRINGS
    # schema-target constant (they must exist to be scannable); assert exactly that.
    for tail in FORBIDDEN_TAILS:
        assert cli_src.count(tail) == 1
    for tail in FORBIDDEN_TAILS:  # self-scan: this test file never carries them
        assert tail not in Path(__file__).read_text(encoding="utf-8")


def test_t0_test_file_import_isolation():
    ttree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    prod = [(n.module, sorted(a.name for a in n.names)) for n in ast.walk(ttree)
            if isinstance(n, ast.ImportFrom) and n.module
            and n.module.startswith("comparison_bench")]
    assert prod == [("comparison_bench.src.comparison_bench.cli",
                     ["run_nonbinary_v32_operating_point_audit_correction"])]
    call_sites = [n for n in ast.walk(ttree)
                  if isinstance(n, ast.Call) and
                  (getattr(n.func, "attr", None) or getattr(n.func, "id", "")) == "cli_main"]
    # exactly two: inside the --runner-guarded helper `_run`, plus the __main__ guard
    assert len(call_sites) == 2
    run_fn = next(n for n in ast.walk(ttree)
                  if isinstance(n, ast.FunctionDef) and n.name == "_run")
    inside_run = [c for c in call_sites if any(c is w for w in ast.walk(run_fn))]
    assert len(inside_run) == 1


# --------------------------------------------------------------------------- #
# T1 — unit / tamper
# --------------------------------------------------------------------------- #

def test_t1_d0_predicate_engine_classification():
    by_arm = {
        "B1": [_mini("b1a", "B1", 400, 240, anomaly=True),
               _mini("b1bad", "B1", 200, 240, anomaly=False)],
        "B2": [_mini("b2", "B2", 1024, 240, status="not_run"),
               _mini("b2bad", "B2", 512, 240, status="not_run")],
        "B3": [_mini("b3ok", "B3", 179, 250), _mini("b3bad", "B3", 260, 250)],
        "B4": [_mini("b4ok", "B4", 180, 251), _mini("b4syn", "B4", 180, 251, syndrome=True)],
    }
    res = corr.check_d0_predicates(by_arm)
    preds = res["predicates"]
    assert preds["P-i_B1_active_divergence_observation"]["violating_block_uids"] == ["b1bad"]
    assert preds["P-ii_B2_sentinel_not_run"]["violating_block_uids"] == ["b2bad"]
    assert preds["P-iii_B3B4_improve_but_no_syndrome"]["violating_block_uids"] == [
        "b3bad", "b4syn"]
    assert res["signature_mismatch"] is True
    clean = {"B1": [by_arm["B1"][0]], "B2": [by_arm["B2"][0]],
             "B3": [by_arm["B3"][0]], "B4": [by_arm["B4"][0]]}
    ok = corr.check_d0_predicates(clean)
    assert all(v["passed"] for v in ok["predicates"].values())
    assert ok["signature_mismatch"] is False


def test_t1_b2_sentinel_excluded_from_trajectory_stats(tmp_path):
    recs = make_records()
    per_block = tmp_path / "per_block.jsonl"
    per_block.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    res = corr.run_d0(out, {"v32_per_block": per_block},
                      {"histogram_bins": _frozen()["histogram_bins"]})
    agg = res["aggregation_arm_x_source"]
    assert set(agg) == {f"{arm}|{src}" for arm in ("B0", "B1", "B3", "B4") for src in LABELS}
    assert "B2|1M" not in agg  # C2: excluded entirely
    b2 = res["b2_sentinel"]
    assert b2["excluded_from_trajectory_and_divergence_stats"] is True
    assert b2["sentinel_definition"] == SENTINEL_DEF_LITERAL
    assert b2["total_sentinel_count"] == 60
    assert all(row["sentinel_count"] == row["n_records"] == 20
               for row in b2["per_source"].values())
    assert b2["distinct_terminal_decoder_status"] == ["not_run"]
    assert res["arm_record_counts"] == corr.EXPECTED_COUNTS
    assert res["records_total"] == 247
    assert res["predicates"]["P-ii_B2_sentinel_not_run"]["passed"] is True
    assert res["signature_mismatch"] is False


def test_t1_units_rule_raw_and_bits_per_symbol(tmp_path):
    recs = make_records()
    per_block = tmp_path / "per_block.jsonl"
    per_block.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    res = corr.run_d0(out, {"v32_per_block": per_block},
                      {"histogram_bins": _frozen()["histogram_bins"]})
    entry = res["aggregation_arm_x_source"]["B3|1M"]
    assert "posterior_nll" in entry and "posterior_nll_bits_per_symbol" in entry
    assert "posterior_entropy" in entry and "posterior_entropy_bits_per_symbol" in entry
    raw = [r["posterior_nll"] for r in recs if r.get("arm") == "B3" and r["source"] == "1M"]
    assert entry["posterior_nll"]["mean"] == pytest.approx(float(np.mean(raw)), rel=1e-15)
    assert entry["posterior_nll_bits_per_symbol"]["mean"] == pytest.approx(
        float(np.mean(raw)) / 1024, rel=1e-12)
    for key in ("l1_error_delta_histogram", "l2_error_delta_histogram",
                "posterior_nll_bits_per_symbol_histogram"):
        assert sum(entry[key]["counts"]) == entry["n_records"]


def test_t1_d1_diag_support_closed_form_mc_tolerance_and_labels(tmp_path):
    """Analytic-vs-MC tolerance on an analytically solvable toy law (design §11)."""
    q = corr.Q_SYMBOLS
    npz = tmp_path / "diag.npz"
    np.savez(npz, **{f"{SIDS[l]}_N_ab_train_N_ab_train": make_counts(l) for l in LABELS})
    out = tmp_path / "out"
    out.mkdir()
    res = corr.run_d1(out, {"v25_channel_counts": npz}, _frozen())
    assert res["naming_rules"] == corr.NAMING_RULES
    assert res["signature_mismatch"] is False  # positive mass on P-zeros => infinity holds
    for lbl, v in res["per_source"].items():
        ser = SER[lbl]
        expected_mass = (q * q - 3 * q) * ser / ((q - 1) * q)   # hand-derived closed form
        sm = v["support_miss"]
        assert sm["q_mass_on_p_zero_cells_analytic"] == pytest.approx(expected_mass, rel=1e-12)
        old = v["old_audit_reference_readonly"]
        assert old["delta_q_mass_v2_minus_v1"] == pytest.approx(
            expected_mass - corr.OLD_AUDIT_REFERENCE["q_mass_on_p_zero_cells"][lbl], rel=1e-9)
        # independent truncated CE recompute (own Q matrix, not the CLI's builder)
        n = make_counts(lbl)
        p = n / n.sum()
        qm = np.full((q, q), ser / ((q - 1) * q))
        np.fill_diagonal(qm, (1.0 - ser) / q)
        mask = p > 0
        ce_expected = float(-(qm[mask] * np.log2(p[mask])).sum())
        tc = v["truncated_common_support_cross_entropy"]
        assert tc["value_bits"] == pytest.approx(ce_expected, rel=1e-12)
        assert tc["common_support_cell_count"] == int(mask.sum()) == 3 * q
        cm = v["conditional_finite_support_mean"]
        mc_n = corr.MC_PLAN["n_samples"]
        assert sm["zero_hit_count_mc"] <= mc_n
        assert cm["n_samples_non_hit"] == mc_n - sm["zero_hit_count_mc"]
        assert sm["zero_hit_frequency_mc"] == pytest.approx(
            sm["zero_hit_count_mc"] / mc_n, rel=1e-12)
        mean = cm["mean_bits_per_symbol"]
        assert 0.0 < mean <= 10.0                       # bounded by uniform-symmetry line
        qs = list(cm["quantiles_bits_per_symbol"].values())
        assert qs == sorted(qs)                          # monotone quantiles
        assert list(cm["quantiles_bits_per_symbol"]) == ["0.05", "0.5", "0.95"]
        assert v["full_expected_nll"] == "infinity"
        assert "conditional_finite_support_mean" in v and \
            "truncated_common_support_cross_entropy" in v


def test_t1_d2_dual_law_sibling_objects(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    paths = build_fixtures(_FAKE_DIR)
    out = tmp_path / "out"
    out.mkdir()
    sub = {k: paths[k] for k in ("v25_channel_counts", "v31_RUN_MANIFEST",
                                 "v31_matrix_audits", "v31_m1_registry")}
    res = corr.run_d2(out, sub, _frozen())
    law_a, law_b = res["empirical_P_budget"], res["original_Q_B1_budget"]
    assert law_a["law"] == "A" and law_b["law"] == "B"       # two flat sibling objects
    assert law_a["conclusion_scope"] == SCOPE_NOMINAL_LITERAL == corr.CONCLUSION_SCOPE_NOMINAL
    assert law_b["conclusion"] == INFEASIBLE_LITERAL == corr.Q_B1_INFEASIBLE_CONCLUSION
    assert law_b["de_note"] == corr.Q_B1_DE_NOTE and law_b["de_note"]
    assert "never" in res["red_line_note"]
    assert set(law_a["per_source"]) == set(law_b["per_source"]) == set(LABELS)
    assert ("empirical_P_budget" in res and "original_Q_B1_budget" in res) is True
    popped = dict(res)
    popped.pop("original_Q_B1_budget")
    assert ("empirical_P_budget" in popped and "original_Q_B1_budget" in popped) is False
    for lbl in LABELS:
        ps = law_a["per_source"][lbl]
        leak = ps["leakage_bits_two_definitions_explicitly_separate"]
        assert leak["L1_syndrome_bits_m1x5"] == 80.0
        assert leak["total_pure_recomputed_m1m2x5"] == PURE_TOTAL[lbl]
        assert leak["total_verbatim_leak_total_bits"] == LEAK_VERBATIM[lbl]
        ent = _entropies_independent(make_counts(lbl))
        req = ps["required_bits_n1024"]
        assert req["L1"] == pytest.approx(ent["L1"] * 1024, rel=1e-9)
        assert req["L2"] == pytest.approx(ent["L2"] * 1024, rel=1e-9)
        gaps = ps["gap_bits_leakage_minus_required"]
        assert gaps["total_pure_syndrome"] == pytest.approx(PURE_TOTAL[lbl] - req["total_H_A_given_B"],
                                                            rel=1e-12)
        ratios = ps["ratio_leakage_over_required"]
        assert ratios["L1"] == pytest.approx(80.0 / req["L1"], rel=1e-12)
        drift = ps["v31_cross_check_abs_diff_bits"]
        assert drift["tolerance"] == 1e-6
        assert max(drift["L1"], drift["L2"]) < 1e-9
        chain = ps["recomputed_chain_entropies_bits_per_symbol"]
        assert chain["chain_rule_identity_H_U1_plus_H_U2"] == pytest.approx(
            chain["H_U1_given_B"] + chain["H_U2_given_B_U1"], rel=1e-12)
        lb = law_b["per_source"][lbl]
        ser = SER[lbl]
        assert lb["h_q_b_given_a_bits_per_symbol"] == pytest.approx(
            _h2(ser) + ser * math.log2(1023), rel=1e-12)
        assert lb["h_q_b_given_a_bits_per_symbol"] == pytest.approx(H_Q_APPROX[lbl], abs=1e-3)
        assert lb["required_bits_n1024"] == pytest.approx(REQ_Q_APPROX[lbl], abs=0.1)
        assert lb["pure_syndrome_total_bits_m1m2x5"] == PURE_TOTAL[lbl]
        assert lb["gap_bits_pure_syndrome_minus_required"] == pytest.approx(GAP_B_APPROX[lbl],
                                                                            abs=0.1)


def test_t1_d3_question_verbatim_and_flags(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    paths = build_fixtures(_FAKE_DIR)
    out = tmp_path / "out"
    out.mkdir()
    res = corr.run_d3(out, {"v26_gate": paths["v26_gate"]}, _frozen())
    assert res["question"] == QUESTION_LITERAL == corr.D3_QUESTION
    assert res["not_fixed_packet_de"] is True
    assert "NOT fixed-QC-graph" in res["question_scope_qualification"]
    rates = res["layer_rate_table_verbatim_from_v31_registry"]
    assert rates["rates"] == RATES_LITERAL == corr.LAYER_RATE_TABLE_FROZEN
    assert rates["allocation_id_filter"] == "m1_16_n1024"
    v26 = res["v26_historical_reference_readonly"]
    assert v26["gate_status"] == "pass_target_f13"
    assert v26["best_passing_f"] == {"A01": 1.6, "A02": 1.3}
    assert "must not be extrapolated" in v26["non_extrapolation_note"]
    assert "finite-control" in res["stop_condition"]
    assert "ensemble/channel" in res["advance_condition"]
    assert res["no_DE_executed_in_this_change"] is True


def test_t1_old_output_overwrite_guard(tmp_path):
    root = tmp_path / "pre_existing"
    root.mkdir()
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    assert rc == corr.EXIT_COLLISION
    assert list(root.iterdir()) == []  # collision refused, nothing written


def test_t1_no_forbidden_strings_schema_targets(tmp_path):
    expected = ["finite_graph_decoder_mismatch", "QC graph confirmed failure",
                "decoder confirmed failure", "NB-Polar preferred",
                FORBIDDEN_TAILS[0], FORBIDDEN_TAILS[1], FORBIDDEN_TAILS[2]]
    assert corr.FORBIDDEN_CONCLUSION_STRINGS == expected
    assert corr.SCAN_SCOPE_FILES == ["d0_failure_signature.json", "d1_support_mismatch.json",
                                     "d2_dual_law_feasibility.json", "d3_next_question.json",
                                     "corrected_branch_decision.json"]
    empty = tmp_path / "none"
    empty.mkdir()
    assert corr._scan_forbidden_strings(empty, {"conclusion": "clean"}) == []
    hit = tmp_path / "hit"
    hit.mkdir()
    (hit / "d0_failure_signature.json").write_text('{"x": "NB-Polar preferred"}',
                                                   encoding="utf-8")
    assert corr._scan_forbidden_strings(hit, {}) == ["NB-Polar preferred"]


def test_t1_manifest_missing_rejected(tmp_path):
    rc = _run(["d0", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "never_created")])
    assert rc == corr.EXIT_MANIFEST


@pytest.mark.parametrize("mutate,want", [
    (lambda m: m["frozen"]["thresholds"].__setitem__("support_miss_fraction_max", 0.5),
     corr.EXIT_MANIFEST),
    (lambda m: m["frozen"]["mc_plan"].__setitem__("seed", 1), corr.EXIT_MANIFEST),
    (lambda m: m["frozen"]["histogram_bins"]["error_delta_bin_edges"].__setitem__(-1, 1023),
     corr.EXIT_MANIFEST),
    (lambda m: m["frozen"].__setitem__("margin_method", "normal approximation"),
     corr.EXIT_MANIFEST),
    (lambda m: m["bindings"][0].__setitem__("sha256", "0" * 64), corr.EXIT_BLOCKED),
    # ---- fix task D: field-level manifest guards ----
    (lambda m: m.__setitem__("lifecycle_note", ["drifted"]), corr.EXIT_MANIFEST),
    (lambda m: m.__setitem__("no_de_run", False), corr.EXIT_MANIFEST),
    (lambda m: m.__setitem__("no_decoder_run", False), corr.EXIT_MANIFEST),
    (lambda m: m.__setitem__("old_roots_read_only", False), corr.EXIT_MANIFEST),
    (lambda m: m.__setitem__("schema", "nbldpc_v32_operating_point_audit_correction_manifest_v0"),
     corr.EXIT_MANIFEST),
    (lambda m: m["implementation_identity"].__setitem__("sha256", "zz"), corr.EXIT_MANIFEST),
    (lambda m: m.__setitem__("output_files_expected_eight", ["a.json"]), corr.EXIT_MANIFEST),
    # frozen-field tamper WITH a correctly recomputed digest must still be
    # rejected by the frozen-block content equality check:
    (lambda m: (m["frozen"]["thresholds"].__setitem__("expected_nll_ratio_K", 9.9),
                m.__setitem__("freeze_digest",
                              __import__("hashlib").sha256(json.dumps(
                                  m["frozen"], sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False).encode("utf-8")).hexdigest())),
     corr.EXIT_MANIFEST),
], ids=["thresholds", "mc_seed", "bin_edge", "margin_method", "binding_sha",
        "lifecycle_note", "no_de_run", "no_decoder_run", "old_roots_read_only",
        "schema", "implementation_identity", "expected_outputs",
        "frozen_field_with_fixed_digest"])
def test_t1_manifest_freeze_drift_rejected(tmp_path, mutate, want):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    mp = root / "audit_manifest.json"
    manifest = _load(mp)
    mutate(manifest)
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    assert _sub("d1", root) == want


def test_t1_duplicate_block_uid_stop(tmp_path):
    recs = make_records()
    recs.pop()                      # keep total at 247
    recs.append(dict(recs[7]))      # verbatim duplicate decode record
    root, rc = _flow(tmp_path, records=recs)
    assert rc == corr.EXIT_EVIDENCE


def test_t1_out_of_root_write_rejection(tmp_path):
    root = tmp_path / "rr"
    root.mkdir()
    for bad in ("../evil.json", "sub/dir.json", "..\\evil.json"):
        with pytest.raises(corr.AuditStop) as ei:
            corr._safe_path(root, bad)
        assert ei.value.code == corr.EXIT_WRITE
    assert corr._safe_path(root, "fine.json").name == "fine.json"


def test_t1_run_root_guardrail_rejects_and_allows():
    """Fix task C: minimal explicit path guardrail (pure path logic; the
    validation runs before any filesystem IO, so pointing it at real protected
    roots touches nothing)."""
    def w(rel: str) -> Path:
        return corr.REPO_ROOT / rel

    diag = "comparison_bench/outputs_comparison/nonbinary_diagnostics"
    protected_self = [
        f"{diag}/nbldpc_v32_finite_de_bridge/run_01",
        f"{diag}/nbldpc_v32_operating_point_audit/run_01",
        f"{diag}/nbldpc_v31_20260820/run_01",
        f"{diag}/nbldpc_v31_closeout_audit_v2/run_01",
    ]
    for rel in protected_self:
        with pytest.raises(corr.AuditStop) as ei:
            corr.validate_run_root(w(rel), fake_runner=True)
        assert ei.value.code == corr.EXIT_WRITE

    # subpath INSIDE a protected root is equally rejected
    with pytest.raises(corr.AuditStop) as ei:
        corr.validate_run_root(w(f"{diag}/nbldpc_v32_finite_de_bridge/run_01/sub/dir"),
                               fake_runner=True)
    assert ei.value.code == corr.EXIT_WRITE

    # repo root / results root / outputs_comparison root / diagnostics root:
    # all too broad
    for bad in (corr.REPO_ROOT,
                w("results"),
                w("comparison_bench/outputs_comparison"),
                w(diag)):
        with pytest.raises(corr.AuditStop) as ei:
            corr.validate_run_root(bad, fake_runner=True)
        assert ei.value.code == corr.EXIT_WRITE

    # workspace root itself is too broad even for a fake runner
    with pytest.raises(corr.AuditStop) as ei:
        corr.validate_run_root(w("workspace"), fake_runner=True)
    assert ei.value.code == corr.EXIT_WRITE

    # without a fake runner, even a fresh workspace test root is rejected
    fresh = w("workspace/guardrail_probe_root")
    with pytest.raises(corr.AuditStop) as ei:
        corr.validate_run_root(fresh, fake_runner=False)
    assert ei.value.code == corr.EXIT_WRITE

    # allowed: the frozen additive v2 default root (validation only; collision
    # handling stays downstream)
    corr.validate_run_root(corr.DEFAULT_RUN_ROOT, fake_runner=False)

    # allowed: explicit fake runner + fresh workspace test root
    corr.validate_run_root(fresh, fake_runner=True)


def test_t1_manifest_time_binding_head_drift_accepted(tmp_path):
    """Fix task D: git_head/implementation identity bind the EXECUTION-time
    commit/file.  Drifting the recorded HEAD to another well-formed hash must
    NOT be refused at manifest verification (no current-HEAD equality check).
    Observable: verification passes and the flow proceeds to the stage-output
    collision (d1 already exists after the initial all-flow)."""
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    mp = root / "audit_manifest.json"
    manifest = _load(mp)
    assert manifest["git_head"] != "a" * 40
    manifest["git_head"] = "a" * 40          # well-formed but different
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    assert _sub("d1", root) == corr.EXIT_COLLISION  # got past verify_manifest


# --------------------------------------------------------------------------- #
# T2 — fake qualification full flow (explicit --runner injection only)
# --------------------------------------------------------------------------- #

def test_t2_fake_flow_six_files_and_blocked_terminal(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    assert {p.name for p in root.iterdir()} == SIX_FILES  # six of the eight; review/handoff later
    manifest = _load(root / "audit_manifest.json")
    assert manifest["lifecycle_note"] == LIFECYCLE_LITERAL
    assert manifest["no_de_run"] is True and manifest["no_decoder_run"] is True
    assert manifest["old_roots_read_only"] is True
    order = ["manifest_freeze", "d0", "d1", "d2", "d3", "corrected_branch_decision"]
    assert manifest["execution_order"] == order
    assert set(manifest["output_files_expected_eight"]) == EIGHT_FILES
    assert len(manifest["bindings"]) == len(corr.RepoBindings().binding_paths())
    frozen = manifest["frozen"]
    assert frozen["mc_plan"]["seed"] == 20260822 and frozen["mc_plan"]["n_samples"] == 100000
    assert frozen["thresholds"]["expected_nll_ratio_K"] == 3.0
    assert frozen["histogram_bins"]["error_delta_bin_edges"] == corr.DELTA_BIN_EDGES
    assert manifest["freeze_digest"] == corr.sha256_canonical(frozen)
    identity = manifest["implementation_identity"]
    assert identity["sha256"] == corr.sha256_file(Path(corr.__file__))
    assert len(manifest["git_head"]) == 40
    decision = _load(root / "corrected_branch_decision.json")
    assert decision["generated_by_execution_order"] == order
    assert decision["selected_branch"] == "audit_verifier_blocked"  # C13 honest pending
    ck = decision["conditions_checklist_c01_c13"]
    assert ck["C13_reviewer_artifact_blocking_false"] is False
    assert all(v for k, v in ck.items() if k != "C13_reviewer_artifact_blocking_false")
    assert decision["failed_conditions"] == ["C13_reviewer_artifact_blocking_false"]
    assert decision["candidate_only"] is True and decision["main_acceptance_pending"] is True


def test_t2_independent_headline_recount(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    recs = make_records()

    d0 = _load(root / "d0_failure_signature.json")
    assert d0["records_total"] == len(recs) == 247
    counts = {}
    for r in recs:
        counts[r["arm"]] = counts.get(r["arm"], 0) + 1
    assert d0["arm_record_counts"] == counts
    b3_vals = [r["l2_errors_initial"] for r in recs
               if r.get("arm") == "B3" and r.get("source") == "1M"]
    got = d0["aggregation_arm_x_source"]["B3|1M"]["l2_errors_initial"]["mean"]
    assert got == pytest.approx(float(np.mean(b3_vals)), rel=1e-15)
    assert all(v["passed"] for v in d0["predicates"].values())
    assert d0["signature_mismatch"] is False

    q = corr.Q_SYMBOLS
    d1 = _load(root / "d1_support_mismatch.json")
    for lbl in LABELS:
        ser = SER[lbl]
        expected_mass = (q * q - 3 * q) * ser / ((q - 1) * q)
        sm = d1["per_source"][lbl]["support_miss"]
        assert sm["q_mass_on_p_zero_cells_analytic"] == pytest.approx(expected_mass, rel=1e-12)
        assert d1["per_source"][lbl]["raw_ser"] == ser
        assert d1["per_source"][lbl]["full_expected_nll"] == "infinity"

    d2 = _load(root / "d2_dual_law_feasibility.json")
    for lbl in LABELS:
        lb = d2["original_Q_B1_budget"]["per_source"][lbl]
        assert lb["required_bits_n1024"] == pytest.approx(REQ_Q_APPROX[lbl], abs=0.1)
        assert lb["gap_bits_pure_syndrome_minus_required"] == pytest.approx(GAP_B_APPROX[lbl],
                                                                            abs=0.1)
        pa = d2["empirical_P_budget"]["per_source"][lbl]
        assert pa["leakage_bits_two_definitions_explicitly_separate"][
            "L2_syndrome_bits_m2x5"] == {"1M": 920.0, "1p5M": 950.0, "2M": 960.0}[lbl]

    d3 = _load(root / "d3_next_question.json")
    assert d3["question"] == QUESTION_LITERAL
    assert d3["layer_rate_table_verbatim_from_v31_registry"]["rates"] == RATES_LITERAL
    assert d3["not_fixed_packet_de"] is True


def test_t2_persisted_terminal_distrusted_never_propagates(tmp_path):
    root, rc = _flow(tmp_path)   # fixture terminal already carries the historical string
    assert rc == corr.EXIT_OK
    manifest = _load(root / "audit_manifest.json")
    distrust = manifest["persisted_terminal_distrust"]
    assert distrust["recorded_value"] == "finite_graph_decoder_mismatch"
    assert distrust["status"] == "read_as_distrusted_not_accepted"
    for name in corr.SCAN_SCOPE_FILES:  # never reaches any v2 analysis output
        assert "finite_graph_decoder_mismatch" not in (root / name).read_text(encoding="utf-8")


def test_t2_persisted_terminal_tamper_detected(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    (_FAKE_DIR / "candidate_terminal.json").write_text(
        '{"schema": "x", "terminal": "tampered"}', encoding="utf-8")
    assert _sub("d3", root) == corr.EXIT_BLOCKED  # input drift caught at verify time


def test_t2_persisted_summary_tamper_detected(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    p = _FAKE_DIR / "channel_summary.json"
    p.write_bytes(p.read_bytes() + b"\n")
    assert _sub("d1", root) == corr.EXIT_BLOCKED


def test_t2_record_count_drift_stop(tmp_path):
    # total-line drift: 248 != 247 -> stage-0 STOP before any output root exists
    recs = make_records()
    extra = dict(recs[-1])
    extra["block_uid"] = extra["block_uid"] + "_extra"
    root, rc = _flow(tmp_path, records=recs + [extra])
    assert rc == corr.EXIT_BLOCKED
    assert not root.exists()
    # arm-level drift at constant total: freeze succeeds, d0 refuses
    recs2 = make_records()
    recs2[1]["arm"] = "BX"  # one B0 record relabeled
    root2, rc2 = _flow(tmp_path / "second", records=recs2)
    assert rc2 == corr.EXIT_EVIDENCE
    assert (root2 / "audit_manifest.json").is_file()
    assert not (root2 / "d0_failure_signature.json").exists()


@pytest.mark.parametrize("mode,want", [
    ("source_substitution", corr.EXIT_BLOCKED),
    ("rate_substitution", corr.EXIT_BLOCKED),
    ("law_parameter_substitution", corr.EXIT_MANIFEST),
])
def test_t2_source_rate_law_substitution_stop(tmp_path, mode, want):
    if mode == "law_parameter_substitution":
        root, rc = _flow(tmp_path)
        assert rc == corr.EXIT_OK
        mp = root / "audit_manifest.json"
        manifest = _load(mp)
        manifest["frozen"]["mc_plan"]["seed"] = 7  # swapped MC law parameters
        mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        assert _sub("d1", root) == want
        return
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    if mode == "source_substitution":
        p = _FAKE_DIR / "channel_summary.json"
        s = _load(p)
        s["per_source"][SIDS["1M"]]["ser"], s["per_source"][SIDS["2M"]]["ser"] = \
            s["per_source"][SIDS["2M"]]["ser"], s["per_source"][SIDS["1M"]]["ser"]
        p.write_text(json.dumps(s, indent=1), encoding="utf-8")
    else:  # rate substitution inside the allocation-filtered registry entries
        p = _FAKE_DIR / "m1_registry.json"
        reg = _load(p)
        victim = next(c for c in reg["registered_calls"]
                      if c["allocation_id"] == corr.ALLOCATION_ID
                      and c["layer"] == "L2" and c["source"] == "1p5M")
        victim["rate"] = 0.9
        p.write_text(json.dumps(reg, indent=1), encoding="utf-8")
    rc = _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(tmp_path / "r")])
    assert rc == want


def test_t2_deep_semantic_tamper(tmp_path):
    # (a) evidence-level semantic tamper: break one B1 anomaly flag pre-run.
    recs = make_records()
    victim = next(r for r in recs if r.get("arm") == "B1")
    victim["posterior_anomaly_block"] = False
    root, rc = _flow(tmp_path, records=recs)
    assert rc == corr.EXIT_OK  # recorded honestly, never silently reconciled nor fatal
    d0 = _load(root / "d0_failure_signature.json")
    pred = d0["predicates"]["P-i_B1_active_divergence_observation"]
    assert pred["passed"] is False and victim["block_uid"] in pred["violating_block_uids"]
    assert d0["signature_mismatch"] is True

    # (b) persisted-output semantic tamper: inject a banned conclusion string.
    root2, rc2 = _flow(tmp_path / "inj")
    assert rc2 == corr.EXIT_OK
    dp = root2 / "d0_failure_signature.json"
    payload = _load(dp)
    payload["_probe"] = "say " + FORBIDDEN_TAILS[1]
    dp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    runner = make_fake_runner()
    loaded = [(name, _load(root2 / name)) for name in
              ("d0_failure_signature.json", "d1_support_mismatch.json",
               "d2_dual_law_feasibility.json", "d3_next_question.json")]
    with pytest.raises(corr.AuditStop) as ei:
        corr.write_corrected_branch_decision(root2, runner, *[d for _, d in loaded])
    assert ei.value.code == corr.EXIT_EVIDENCE
    assert FORBIDDEN_TAILS[1] in ei.value.reason


def test_t2_strict_replay_identical_outputs(tmp_path):
    global _FAKE_DIR
    _FAKE_DIR = tmp_path / "fixtures"
    build_fixtures(_FAKE_DIR)
    root_a = tmp_path / "replay_a"
    root_b = tmp_path / "replay_b"
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root_a)]) == corr.EXIT_OK
    snap_a = {name: _load(root_a / name) for name in SIX_FILES}
    shutil.rmtree(root_a)
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root_b)]) == corr.EXIT_OK
    snap_b = {name: _load(root_b / name) for name in SIX_FILES}
    assert "created_utc" in snap_a["audit_manifest.json"]  # whitelist is really used

    def norm(obj):
        if isinstance(obj, dict):
            return {k: norm(v) for k, v in obj.items() if k != "created_utc"}
        if isinstance(obj, list):
            return [norm(v) for v in obj]
        if isinstance(obj, str):
            return obj.replace(str(_FAKE_DIR.resolve()), "&FX&")
        return obj

    for name in sorted(SIX_FILES):
        assert norm(snap_a[name]) == norm(snap_b[name]), name


def test_t2_collision_end_to_end_byte_identical(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    before = _snapshot(root)
    assert _run(["all", "--runner", RUNNER_SPEC, "--run-root", str(root)]) == corr.EXIT_COLLISION
    assert _snapshot(root) == before


def test_t2_terminal_priority_mechanical_routing(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == corr.EXIT_OK
    base = [_load(root / n) for n in ("d0_failure_signature.json",
                                      "d1_support_mismatch.json",
                                      "d2_dual_law_feasibility.json",
                                      "d3_next_question.json")]
    d0, d1, d2, d3 = base
    summary_path = _FAKE_DIR / "channel_summary.json"
    summary_bytes = summary_path.read_bytes()
    review = root / "readonly_review.json"

    def decide(d1_=None, d2_=None, d3_=None):
        return corr.write_corrected_branch_decision(
            root, make_fake_runner(), d0, d1_ or d1, d2_ or d2, d3_ or d3)

    # baseline: everything fine except C13 reviewer artifact pending -> blocked
    payload = decide()
    assert payload["selected_branch"] == "audit_verifier_blocked"
    assert payload["failed_conditions"] == ["C13_reviewer_artifact_blocking_false"]

    # D-verdict failure C04 -> inconsistent (highest priority class)
    short = dict(d1)
    short["per_source"] = {k: v for k, v in d1["per_source"].items() if k != "2M"}
    payload = decide(d1_=short)
    assert payload["selected_branch"] == "audit_evidence_inconsistent"
    assert any(c.startswith("C04_") for c in payload["failed_conditions"])

    # D-verdict failure C10 -> inconsistent
    bad3 = dict(d3)
    bad3["question"] = d3["question"] + "（mutated）"
    payload = decide(d3_=bad3)
    assert payload["selected_branch"] == "audit_evidence_inconsistent"

    # combined C04+C06 failures: inconsistent wins over blocked-class (strict order)
    combo = dict(short)
    combo["naming_rules"] = {}
    payload = decide(d1_=combo)
    assert payload["selected_branch"] == "audit_evidence_inconsistent"
    assert any(c.startswith("C06_") for c in payload["failed_conditions"])

    # semantic/law-conclusion drift C08/C09 -> blocked (self-consistency class)
    scope_bad = dict(d2)
    scope_bad["empirical_P_budget"] = {**d2["empirical_P_budget"],
                                       "conclusion_scope": "drifted scope"}
    assert decide(d2_=scope_bad)["selected_branch"] == "audit_verifier_blocked"
    concl_bad = dict(d2)
    concl_bad["original_Q_B1_budget"] = {**d2["original_Q_B1_budget"],
                                         "conclusion": "drifted conclusion"}
    payload = decide(d2_=concl_bad)
    assert payload["selected_branch"] == "audit_verifier_blocked"
    assert any(c.startswith("C09_") for c in payload["failed_conditions"])

    # C12 runtime window: input mutated after freeze -> blocked with drift reason
    summary_path.write_bytes(summary_bytes + b"\n")
    payload = decide()
    assert payload["selected_branch"] == "audit_verifier_blocked"
    assert payload["conditions_checklist_c01_c13"]["C12_old_roots_byte_identical_runtime_window"] \
        is False
    summary_path.write_bytes(summary_bytes)  # restore byte-identical state

    # all thirteen satisfied -> corrected (mechanically reachable endpoint)
    review.write_text(json.dumps({"blocking": False, "reviewer_id": "test-stub"}),
                      encoding="utf-8")
    try:
        payload = decide()
        assert payload["selected_branch"] == "audit_corrected_rate_aligned_de_required"
        assert all(payload["conditions_checklist_c01_c13"].values())
        assert payload["failed_conditions"] == []
    finally:
        review.unlink()
