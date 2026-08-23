"""T0-T3 suite for the NB-LDPC V33 rate-aligned empirical-channel DE verifier.

Change: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic
(FROZEN_ACCEPTED, baseline 0a050066).  Layering per design §6:

- T0: compile/import/help; M != 1024 entropy toy; rate/rho construction;
  GF(32) poly-37 identity; sampler centering (truth at index 0);
  zero-denominator exception path; AST import whitelist + import-time
  zero-DE probe.
- T1: five stage-0 failure classes with exact reason mapping (zero DE calls,
  no fabricated call records); binding / rate / field / parameter tamper
  rejection; full SHALL-PATH1 guard scenarios (repo/results/diagnostics/
  archive/five protected old roots self+subpath/workspace root/sibling
  checkout rejected; production default allowed; fake + workspace child
  allowed); collision at the execute entry; malformed / duplicate / missing /
  extra / out-of-order call evidence detection by verify; unauthorized
  execute rejection (exit 7); explicit fake-runner injection guard.
- T2: complete 30-call fake qualification with three-way routing
  (PASS / FAIL / INCONCLUSIVE), strict replay (identical outputs modulo a
  timestamp whitelist), independent terminal reconstruction from persisted
  evidence, exact-once order + per-call persistence, collision checked at
  entry only (never re-triggered within one execution).
- T3: real-input READ-ONLY identity checks (R1-R7 existence / SHA256 record /
  npz keys / layer-rate literals), protected roots pre/post unchanged around
  a fake flow, official run_01 still absent.  No DE, no decoder, no graph
  builder.
  T3 scope (verbatim): "T3 smoke: PASS; full frozen T3 regression: not in
  scope."

Every run root is a fresh ``workspace/v33_tests_<uuid>/`` pytest basetemp
child run with ``-p no:cacheprovider``; the fake DE runner is injected
explicitly via ``--runner MODULE:ATTR`` on every CLI invocation (enforced by
the ``_run`` helper).  Official run_01 is never created; real inputs are
never executed against DE.
"""
from __future__ import annotations

import ast
import copy
import importlib
import json
import math
import os
import py_compile
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v33_rate_aligned_empirical_de as v33,
)

RUNNER_SPEC = __name__ + ":FAKE_PROVIDER"

# --------------------------------------------------------------------------- #
# Independently typed literals (from spec.md; never read from the CLI module)
# --------------------------------------------------------------------------- #

LABELS = ("1M", "1p5M", "2M")
LAYERS = ("L1", "L2")
SIDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
NPZ_KEYS = {lbl: f"{SIDS[lbl]}_N_ab_train_N_ab_train" for lbl in LABELS}
SER_BY_SID = {
    "type2_1M_20260121_184040": 0.239779296875,
    "type2_1p5M_20260121_183806": 0.2544695292735815,
    "type2_2M_20260121_183657": 0.2557409550754458,
}
M2_MAP = {"1M": 184, "1p5M": 190, "2M": 192}
LEAK_MAP = {"1M": 1064.0, "1p5M": 1094.0, "2M": 1104.0}
SEEDS_LITERAL = (33101, 33102, 33103, 33104, 33105)
N_SAMPLES_LITERAL = 2000
MAX_ITER_LITERAL = 200
ENTROPY_TOL_LITERAL = 0.01
STREAK_LITERAL = 20
FIELD_ID_LITERAL = ("c3a3660aa3cfbf788568cf366ee5de34"
                    "5ddc6be0372154a702c9e244a53bc6cf")
ALLOCATION_ID_LITERAL = "m1_16_n1024"
PACKET_ID_LITERAL = "m1_16_n1024_n1024|QC-cyclic-projective"
RATES_LITERAL = {
    "L1": {"1M": 0.984375, "1p5M": 0.984375, "2M": 0.984375},
    "L2": {"1M": 0.8203125, "1p5M": 0.814453125, "2M": 0.8125},
}
EXPECTED_ORDER = tuple((lbl, lyr, seed) for lbl in LABELS for lyr in LAYERS
                       for seed in SEEDS_LITERAL)
SIX_FILES = {
    "audit_manifest.json", "de_call_matrix.json", "de_cell_matrix.json",
    "de_cell_matrix.md", "final_state.json", "v26_reference_readonly.json",
}
STAGE0_REASONS = ("missing_input", "binding_drift", "field_mismatch",
                  "allocation_mismatch", "malformed_input")


# --------------------------------------------------------------------------- #
# Synthetic fixtures: three-tier N_ab matrices + a consistent R1-R7 tree
# --------------------------------------------------------------------------- #

def make_counts(lbl: str) -> np.ndarray:
    """Deterministic synthetic train N_ab (1024, 1024), one tier per source."""
    a = np.arange(v33.N_BLOCKS)
    n = np.zeros((v33.N_BLOCKS, v33.N_BLOCKS), dtype=np.float64)
    if lbl == "1M":
        # PASS tier: strong near-diagonal channel (ser 0.005) -> separable-ish.
        ser, w = 0.005, 1.0 + (a % 7) * 0.01
        n[a, a] += (1.0 - ser) * w
        n[a, (a + 1) % v33.N_BLOCKS] += ser * 0.6 * w
        n[a, (a - 1) % v33.N_BLOCKS] += ser * 0.4 * w
    elif lbl == "1p5M":
        # FAIL tier: heavy mixing -> posterior population stays high-entropy.
        n += 1.0
        n[a, a] += 0.05
    else:
        # INCONCLUSIVE tier: valid counts (stage-0 must accept them); the fake
        # runner answers INCONCLUSIVE for this source regardless.
        ser, w = 0.35, 1.0 + (a % 5) * 0.02
        n[a, a] += (1.0 - ser) * w
        for k in (1, 2, 3, 7, -3):
            n[a, (a + k) % v33.N_BLOCKS] += ser * w / 5.0
    assert np.all(np.isfinite(n)) and np.all(n >= 0.0) and n.sum() > 0.0
    return n


def build_fixtures(fx_repo: Path) -> None:
    """Write a complete, internally consistent R1-R7 binding tree rooted at
    ``fx_repo`` (mirroring the repo layout BINDING_PATHS expects)."""

    def p(rid: str) -> Path:
        out = fx_repo / v33.BINDING_PATHS[rid]
        out.parent.mkdir(parents=True, exist_ok=True)
        return out

    def put(rid: str, obj) -> None:
        p(rid).write_text(json.dumps(obj, indent=1), encoding="utf-8")

    np.savez(p("R1"), **{NPZ_KEYS[lbl]: make_counts(lbl) for lbl in LABELS})

    summary = {"schema": "nbldpc_v25_m0_v1", "per_source": {}}
    for lbl in LABELS:
        sid = SIDS[lbl]
        ser = SER_BY_SID[sid]
        summary["per_source"][sid] = {
            "n_pairs": 512000, "ser": ser,
            "pm1_mass": {"+1": ser * 0.5, "-1": ser * 0.5, "0": 1.0 - ser},
        }
    put("R2", summary)

    put("R3", {"schema": "nbldpc_v25_split_manifest_v1", "per_source": {
        SIDS[lbl]: {"pairs": {"train": 512000, "validation": 1000,
                              "holdout": 1000}} for lbl in LABELS}})

    sources = {}
    for lbl in LABELS:
        h = v33.empirical_f03_entropies(make_counts(lbl))
        sources[lbl] = {
            "source_id": SIDS[lbl], "delay_used_ps": 50,
            "m_total": 16 + M2_MAP[lbl], "m1": 16, "m2": M2_MAP[lbl],
            "H": h, "leak_total_bits": LEAK_MAP[lbl],
            "f_total": LEAK_MAP[lbl] / (v33.N_BLOCKS * sum(h.values())),
        }
    put("R4", {"schema": "nbldpc_v31_run_manifest_v1", "configs": {"1024": {
        "schema": "nbldpc_v31_frozen_config_v1", "q": 32, "n": 1024, "m1": 16,
        "sources": sources,
        "field": {"q": 32, "primitive_polynomial": 37, "basis": "polynomial",
                  "field_id": FIELD_ID_LITERAL}}}})
    put("R5", {"packets": [
        {"packet_id": "decoy_other_packet|x", "allocation_id": "other_alloc",
         "audits": {"L1": {"shape": [8, 2048]}}},
        {"packet_id": PACKET_ID_LITERAL, "allocation_id": ALLOCATION_ID_LITERAL,
         "audits": {"L1": {"shape": [16, 1024]}}},
    ]})
    registry = []
    for lbl in LABELS:
        for lyr in LAYERS:
            for _ in range(5):
                registry.append({
                    "allocation_id": ALLOCATION_ID_LITERAL, "layer": lyr,
                    "source_id": SIDS[lbl], "m1": 16, "m2": M2_MAP[lbl],
                    "rate": RATES_LITERAL[lyr][lbl],
                    "H_bits_per_symbol": sources[lbl]["H"][lyr]})
    # Decoy allocation with wrong rates: must be filtered out by allocation id.
    for lbl in LABELS[:2]:
        registry.append({"allocation_id": "m1_16_n2048_decoy", "layer": "L2",
                         "source_id": SIDS[lbl], "m1": 16, "m2": 512,
                         "rate": 0.5})
    put("R6", {"registered_calls": registry})
    put("R7", {"status": "pass_target_f13",
               "best_passing_f": {"A01": 1.6, "A02": 1.3}})


# --------------------------------------------------------------------------- #
# Fake binding provider + fake DE runner (module-level singleton; the CLI's
# load_runner resolves MODULE:ATTR to the attribute itself)
# --------------------------------------------------------------------------- #

def _tiered_behavior(req: dict) -> dict:
    """Default routing: 1M->PASS, 1p5M->FAIL (finite oscillation), 2M->NaN."""
    lbl = req["source_label"]
    if lbl == "1M":
        return {"terminal": "PASS", "reason_codes": [], "iterations": 25,
                "entropy_trace_bits": [0.5] * 5 + [0.004] * STREAK_LITERAL,
                "final_entropy_bits": 0.004}
    if lbl == "1p5M":
        return {"terminal": "FAIL",
                "reason_codes": ["max_iter_exhausted_without_streak"],
                "iterations": MAX_ITER_LITERAL,
                "entropy_trace_bits": [0.02, 0.05] * 100,
                "final_entropy_bits": 0.05}
    return {"terminal": "INCONCLUSIVE", "reason_codes": ["numeric_nan"],
            "iterations": 3,
            "entropy_trace_bits": [0.5, 0.2, float("nan")],
            "final_entropy_bits": None,
            "detail": "fixture pathology: NaN entropy trace bit at terminal iteration"}


def _all_pass(_req: dict) -> dict:
    return {"terminal": "PASS", "reason_codes": [], "iterations": 20,
            "entropy_trace_bits": [0.001] * STREAK_LITERAL,
            "final_entropy_bits": 0.001}


def _all_fail(_req: dict) -> dict:
    return {"terminal": "FAIL",
            "reason_codes": ["max_iter_exhausted_without_streak"],
            "iterations": MAX_ITER_LITERAL,
            "entropy_trace_bits": [0.03] * MAX_ITER_LITERAL,
            "final_entropy_bits": 0.03}


class FakeV33Provider:
    """Serves a fixture-derived binding context and scripted DE results."""

    def __init__(self):
        self.fixture_repo: Path | None = None
        self.behavior = _tiered_behavior
        self.probe = None           # optional callable(request), runs pre-answer
        self.context_override = None  # when set, served verbatim by binding_context
        self.calls: list[dict] = []

    def binding_context(self, _repo_root):
        if self.context_override is not None:
            return self.context_override
        report, _ = v33.stage0_validate(self.fixture_repo, None)
        data = np.load(self.fixture_repo / v33.BINDING_PATHS["R1"])
        counts = {NPZ_KEYS[lbl]: np.asarray(data[NPZ_KEYS[lbl]],
                                            dtype=np.float64)
                  for lbl in LABELS}
        by_sid = {SIDS[lbl]: counts[NPZ_KEYS[lbl]] for lbl in LABELS}
        return {"mode": "fake", "bindings": report, "counts": by_sid}

    def run_call(self, request: dict) -> dict:
        self.calls.append({k: request[k] for k in
                           ("ordinal", "source_label", "layer", "seed")})
        if self.probe is not None:
            self.probe(request)
        return self.behavior(request)


FAKE_PROVIDER = FakeV33Provider()


def _run(argv: list[str]) -> int:
    assert "--runner" in argv  # guard: tests never touch the production path
    FAKE_PROVIDER.calls.clear()
    return v33.main(argv)


def _flow(tmp_path: Path, behavior=None):
    """Fresh fixture tree + one fake execute into a fresh run root."""
    FAKE_PROVIDER.fixture_repo = tmp_path / "fixture_repo"
    build_fixtures(FAKE_PROVIDER.fixture_repo)
    FAKE_PROVIDER.behavior = behavior if behavior is not None else _tiered_behavior
    FAKE_PROVIDER.probe = None
    FAKE_PROVIDER.context_override = None
    root = tmp_path / "run_root"
    rc = _run(["execute", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    return root, rc


def _sub(sub: str, root: Path) -> int:
    return _run(["verify", "--runner", RUNNER_SPEC, "--run-root", str(root)])


def _load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dump(path: Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True),
                          encoding="utf-8")


def _snapshot(root: Path) -> dict:
    out = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return out


def _payload(capsys):
    """Last top-level JSON document printed since the last drain (earlier
    ``main()`` invocations within one test may still be buffered)."""
    out = capsys.readouterr().out
    dec, pos, doc = json.JSONDecoder(), 0, None
    while True:
        j = out.find("{", pos)
        if j < 0:
            return doc
        try:
            doc, pos = dec.raw_decode(out, j)
        except ValueError:
            pos = j + 1


def _problems(capsys) -> list[str]:
    return _payload(capsys)["problems"]


# --------------------------------------------------------------------------- #
# T0 — structure / tiny math / semantics / static hygiene
# --------------------------------------------------------------------------- #

def test_t0_py_compile_import_help(tmp_path, capsys):
    cfile = str(tmp_path / "v33_cli.pyc")
    py_compile.compile(str(Path(v33.__file__)), cfile=cfile, doraise=True)
    py_compile.compile(str(Path(__file__)), cfile=str(tmp_path / "t.pyc"),
                       doraise=True)
    assert (v33.EXIT_OK, v33.EXIT_COLLISION, v33.EXIT_BLOCKED_BINDING,
            v33.EXIT_EVIDENCE_INCONSISTENT, v33.EXIT_MANIFEST,
            v33.EXIT_WRITE_GUARD, v33.EXIT_UNAUTHORIZED) == (0, 2, 3, 4, 5, 6, 7)
    assert v33.OFFICIAL_RUN_ROOT.name == "run_01"
    with pytest.raises(SystemExit) as ei:
        v33.main(["--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    for token in ("prepare", "verify", "execute", "test-selfcheck"):
        assert token in out, token
    with pytest.raises(SystemExit) as ei2:
        v33.main(["execute", "--help"])
    assert ei2.value.code == 0
    out2 = capsys.readouterr().out
    for token in ("--runner", "--run-root", "--execute-auth-file"):
        assert token in out2, token


def test_t0_import_time_runs_no_de(monkeypatch):
    """Lazy-DE guarantee: importing the module must not touch any DE kernel."""
    def _boom(*_a, **_k):
        raise AssertionError("DE computation ran at import time")
    monkeypatch.setattr(np.random, "default_rng", _boom)
    importlib.reload(v33)
    assert callable(v33.mcde_iterate)  # defs/constants only; nothing executed


def test_t0_mean_bits_entropy_M_not_n():
    """SHALL-CONV1: H_t averages over population rows M=shape[0], not n=1024."""
    pop = np.zeros((7, v33.Q))
    manual = []
    for i in range(7):
        pop[i, 0] = 1.0 - (i + 1) * 0.05
        rest = 1.0 - pop[i, 0]
        for j in range(1, v33.Q):
            pop[i, j] = rest / (v33.Q - 1)
        p = pop[i]
        manual.append(float(-(p[p > 0] * np.log2(p[p > 0])).sum()))
    got = v33.mean_bits_entropy(pop)
    assert abs(got - float(np.mean(manual))) < 1e-12
    assert abs(got - float(np.sum(manual)) / v33.N_BLOCKS) > 1e-3  # not /1024
    with pytest.raises(v33.NumericError):
        v33.mean_bits_entropy(np.zeros((7, 31)))  # wrong symbol width


def test_t0_layer_rates_and_make_rho_properties():
    rates = v33.layer_rates()
    for lbl in LABELS:
        for lyr in LAYERS:
            entry = rates[lbl][lyr]
            m_i = 16 if lyr == "L1" else M2_MAP[lbl]
            assert entry["m_i"] == m_i
            assert entry["R_i"] == pytest.approx(RATES_LITERAL[lyr][lbl])
            rho = entry["rho"]
            degrees = sorted(rho)
            assert all(isinstance(d, int) and d >= 2 for d in degrees)
            assert max(degrees) - min(degrees) <= 1          # two-point adjacent
            assert all(w > 0.0 for w in rho.values())
            integ = sum(w / d for d, w in rho.items())
            assert integ == pytest.approx((1.0 - entry["R_i"]) * 0.5,
                                          rel=1e-12)         # lambda={2:1}
    assert v33.make_rho(1.0 - 16 / 1024) == {128: 1.0}       # exact concentration
    with pytest.raises(v33.NumericError):
        v33.make_rho(1.0)                                    # (1-rate)<=0


def test_t0_gf32_identity_poly37_field_id():
    assert v33.PRIMITIVE_POLYNOMIAL == 37                    # 0b100101
    f = v33.get_field()
    assert len(f["exp"]) == 31 and len(set(f["exp"])) == 31  # complete cycle
    assert all(v33.gf_mul(x, v33.gf_inverse(x)) == 1 for x in range(1, 32))
    assert v33.gf_mul(5, 7) == v33.gf_mul(7, 5)              # commutative
    # field_id recomputed from an independently typed payload
    payload = {"method": "nbldpc_formal_v1",
               "backend_id": "internal_polynomial_basis_gf2m",
               "backend_version": "1", "q": 32, "m": 5,
               "primitive_polynomial": 37, "basis": "polynomial",
               "symbol_encoding": "unsigned_coefficient_integer_lsb_x_to_the_i"}
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True)
    import hashlib
    assert hashlib.sha256(canon.encode("ascii")).hexdigest() == FIELD_ID_LITERAL
    assert v33.FROZEN_FIELD_ID == FIELD_ID_LITERAL
    ident = v33.check_field_identity()
    assert ident["match"] is True and ident["cycle_ok"] and ident["inverse_ok"]


def test_t0_centering_truth_index0_and_pcg64_reproducible():
    rows = np.zeros((2, v33.Q))
    rows[0, 5] = 1.0
    rows[1, 9] = 0.5
    rows[1, 3] = 0.5
    centered = v33._center_rows(rows, np.array([5, 3]))
    assert centered[0, 0] == pytest.approx(1.0)     # truth GF-XOR'ed to index 0
    assert centered[1, 0] == pytest.approx(0.5)
    assert centered[1, 10] == pytest.approx(0.5)    # 9 XOR 3 = 10
    toy = np.zeros((v33.N_BLOCKS, v33.N_BLOCKS))
    toy[5, 3] = 1000.0
    qd = v33.build_q_joint(toy)
    r1 = v33.sample_centered_rows(qd, "L1", 16, np.random.default_rng(7))
    r2 = v33.sample_centered_rows(qd, "L2", 16, np.random.default_rng(7))
    assert np.allclose(r1[:, 0], 1.0) and np.allclose(r2[:, 0], 1.0)
    r3 = v33.sample_centered_rows(qd, "L1", 16, np.random.default_rng(7))
    assert np.array_equal(r1, r3)                   # fixed PCG64 draw order
    assert np.random.default_rng(1).bit_generator.__class__.__name__ == "PCG64"
    assert v33.RNG_NAME == "PCG64"


def test_t0_zero_denominator_inconclusive_no_fallback():
    degenerate = np.zeros((v33.N_BLOCKS, v33.N_BLOCKS))
    degenerate[0, 0] = 10.0
    qd = v33.build_q_joint(degenerate)
    assert qd["p_u1_gb"][0, 0] == 1.0
    with pytest.raises(v33.ZeroDenominatorError):
        v33._l2_rows(qd, np.array([7]), np.array([3]))   # P(U1=3|B=7) undefined
    # Same failure surfacing through the full per-call engine: hit a sampled
    # point whose true-predecessor conditional denominator was zeroed.
    toy = np.zeros((v33.N_BLOCKS, v33.N_BLOCKS))
    toy[5, 3] = 1000.0
    qd2 = v33.build_q_joint(toy)
    qd2["p_u1_gb"][0, 3] = 0.0                           # illegal denominator
    rec = v33.mcde_iterate(qd2, "L2", 42, rate=0.984375,
                           n_samples=64, max_iter=8)
    assert rec["terminal"] == "INCONCLUSIVE"
    assert rec["reason_codes"] == ["inconclusive_input_binding"]
    assert rec.get("detail")                              # fail-closed, no rows


def test_t0_real_engine_toys_pass_fail_nan():
    # separable toy channel -> quick mechanical PASS (streak met)
    toy = np.zeros((v33.N_BLOCKS, v33.N_BLOCKS))
    toy[5, 3] = 1000.0
    ok = v33.mcde_iterate(v33.build_q_joint(toy), "L2", 12345, rate=0.984375,
                          n_samples=64, max_iter=40, entropy_tol_bits=1e-6,
                          streak_target=5)
    assert ok["terminal"] == "PASS" and ok["reason_codes"] == []
    assert 5 <= ok["iterations"] <= 40
    assert all(math.isfinite(h) for h in ok["entropy_trace_bits"])
    assert ok["not_fixed_packet_de"] is True
    # uniform toy -> H_t cannot sustain a 20-streak inside 8 iters => FAIL
    uni = np.full((v33.N_BLOCKS, v33.N_BLOCKS), 1.0)
    bad = v33.mcde_iterate(v33.build_q_joint(uni), "L1", 999, rate=0.984375,
                           n_samples=64, max_iter=8)
    assert bad["terminal"] == "FAIL"
    assert bad["iterations"] == 8 and len(bad["entropy_trace_bits"]) == 8
    # non-finite channel mass -> NumericError path => INCONCLUSIVE(numeric_nan)
    nan_qd = v33.build_q_joint(toy)
    nan_qd["p_u1_gb"][0, 3] = np.nan
    nanrec = v33.mcde_iterate(nan_qd, "L1", 7, rate=0.984375,
                              n_samples=64, max_iter=8)
    assert nanrec["terminal"] == "INCONCLUSIVE"
    assert nanrec["reason_codes"] == ["numeric_nan"]
    assert isinstance(nanrec.get("detail"), str) and nanrec["detail"]


def test_t0_numeric_reason_classification_is_scientifically_specific():
    state = {"p": np.array([1.0])}
    pop = np.full((2, v33.Q), 1.0 / v33.Q)
    assert v33._numeric_pathology(
        state, pop, [], v33.NumericError("negative mass"))[0] == \
        "negative_probability"
    assert v33._numeric_pathology(
        state, pop, [], v33.NumericError("not normalized"))[0] == \
        "normalization_failed"
    assert v33._numeric_pathology(
        state, pop, [], RuntimeError("unexpected"))[0] == "internal_exception"


def test_t0_static_whitelist_no_forbidden_calls_and_test_isolation():
    cli_src = Path(v33.__file__).read_text(encoding="utf-8")
    allowed = {"argparse", "hashlib", "importlib", "json", "math", "os",
               "subprocess", "sys", "datetime", "pathlib", "numpy",
               "__future__"}
    tree = ast.parse(cli_src)
    imports, calls = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            calls.append(getattr(node.func, "id", None) or
                         getattr(node.func, "attr", "") or "")
    assert imports <= allowed, sorted(imports - allowed)
    # no decoder / graph-builder / ttbin / pipeline markers among CALL sites
    blacklist = ["decode", "ttbin", "graph_build", "graphbuild",
                 "finite_control", "finitecontrol", "longrun", "minrerun",
                 "routea", "cascade", "synth", "polar", "ldpc"]
    for tok in blacklist:
        hits = [c for c in calls if tok in c.lower()]
        assert not hits, (tok, hits)
    # this test file imports only the CLI module from the project
    ttree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    prod = [(n.module, sorted(a.name for a in n.names)) for n in ast.walk(ttree)
            if isinstance(n, ast.ImportFrom) and n.module
            and n.module.startswith("comparison_bench")]
    assert prod == [("comparison_bench.src.comparison_bench.cli",
                     ["run_nonbinary_v33_rate_aligned_empirical_de"])]
    # the _run helper really enforces the --runner injection guard
    run_fn = next(n for n in ast.walk(ttree)
                  if isinstance(n, ast.FunctionDef) and n.name == "_run")
    consts = [c.value for c in ast.walk(run_fn)
              if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    assert any("--runner" in s for s in consts)


def test_t0_call_matrix_order_thirty_calls():
    assert v33.TOTAL_CALLS == 30 == len(EXPECTED_ORDER)
    calls = v33.enumerate_calls()
    assert [(c["source_label"], c["layer"], c["seed"]) for c in calls] == \
        list(EXPECTED_ORDER)
    assert [c["ordinal"] for c in calls] == list(range(1, 31))
    assert all(c["source_id"] == SIDS[c["source_label"]] for c in calls)


# --------------------------------------------------------------------------- #
# T1 — stage-0 failures / tampers / path guard / evidence attacks
# --------------------------------------------------------------------------- #

def test_t1_stage0_fixture_repo_ok_and_hashes_recorded(tmp_path):
    fx = tmp_path / "fixture_repo"
    build_fixtures(fx)
    report, counts = v33.stage0_validate(fx, None)
    assert report["ok"] is True and report["reasons"] == []
    assert report["field_identity"]["match"] is True
    for lbl in LABELS:
        for lyr in LAYERS:
            assert report["rates"][lbl][lyr]["R_i"] == \
                pytest.approx(RATES_LITERAL[lyr][lbl])
        assert np.array_equal(counts[SIDS[lbl]], make_counts(lbl))
    for rid, entry in report["bindings"].items():
        assert entry["exists"] is True and entry["failure_reason"] is None
        assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64


@pytest.mark.parametrize("victim,reason", [
    ("R3", "missing_input"),
    ("R2", "binding_drift"),
    ("R4", "field_mismatch"),
    ("R6", "allocation_mismatch"),
    ("R1", "malformed_input"),
])
def test_t1_stage0_five_failure_reasons(tmp_path, victim, reason):
    fx = tmp_path / "fixture_repo"
    build_fixtures(fx)
    target = fx / v33.BINDING_PATHS[victim]
    if reason == "missing_input":
        target.unlink()
    elif reason == "binding_drift":
        doc = _load(target)
        doc["per_source"][SIDS["1M"]]["ser"] = 0.111
        _dump(target, doc)
    elif reason == "field_mismatch":
        doc = _load(target)
        doc["configs"]["1024"]["field"]["field_id"] = "0" * 64
        _dump(target, doc)
    elif reason == "allocation_mismatch":
        doc = _load(target)
        for call in doc["registered_calls"]:
            call["allocation_id"] = "m1_16_n2048_decoy"
        _dump(target, doc)
    else:
        target.write_bytes(b"this is not an npz")
    report, _ = v33.stage0_validate(fx, None)
    assert report["ok"] is False
    assert report["reasons"] == [reason]


def test_t1_stage0_rejects_r4_entropy_and_r6_layer_identity_drift(tmp_path):
    fx = tmp_path / "fixture_repo"
    build_fixtures(fx)

    r4 = fx / v33.BINDING_PATHS["R4"]
    doc = _load(r4)
    doc["configs"]["1024"]["sources"]["1M"]["H"]["L2"] += 0.01
    _dump(r4, doc)
    report, _ = v33.stage0_validate(fx, None)
    assert "binding_drift" in report["reasons"]

    build_fixtures(fx)
    r6 = fx / v33.BINDING_PATHS["R6"]
    doc = _load(r6)
    target = next(c for c in doc["registered_calls"]
                  if c["source_id"] == SIDS["1M"] and
                  c["rate"] == RATES_LITERAL["L2"]["1M"])
    target["H_bits_per_symbol"] = doc["registered_calls"][0]["H_bits_per_symbol"]
    _dump(r6, doc)
    report, _ = v33.stage0_validate(fx, None)
    assert "binding_drift" in report["reasons"]


@pytest.mark.parametrize("reason", STAGE0_REASONS)
def test_t1_execute_stage0_failure_zero_de_calls(tmp_path, reason, capsys):
    """SHALL-SF1: blocked stage-0 => zero DE calls, no run root, no fabricated
    30-call records, overall blocked with the mapped reason."""
    root, rc = None, None
    fx = tmp_path / "fixture_repo"
    build_fixtures(fx)
    FAKE_PROVIDER.fixture_repo = fx
    FAKE_PROVIDER.behavior = _tiered_behavior
    FAKE_PROVIDER.probe = None
    good = FAKE_PROVIDER.binding_context(tmp_path)
    bad = copy.deepcopy(good)          # deep copy (counts hold ndarrays)
    bad["bindings"]["ok"] = False
    bad["bindings"]["reasons"] = [reason]
    FAKE_PROVIDER.context_override = bad
    run_root = tmp_path / "run_root"
    rc = _run(["execute", "--runner", RUNNER_SPEC, "--run-root", str(run_root)])
    FAKE_PROVIDER.context_override = None
    assert rc == v33.EXIT_BLOCKED_BINDING
    assert not run_root.exists()
    assert FAKE_PROVIDER.calls == []                  # zero DE calls
    assert not list(tmp_path.rglob("de_call_matrix.json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["blocked"] == "stage0_binding_failure"
    assert payload["reasons"] == [reason]


def test_t1_unauthorized_execute_paths(tmp_path, capsys):
    assert not v33.OFFICIAL_RUN_ROOT.exists()
    # (a) no auth flag at all; (b) auth file missing; (c) auth file refuses
    ap = tmp_path / "auth.json"
    ap.write_text('{"granted": false}', encoding="utf-8")
    for argv in (["execute"],
                 ["execute", "--execute-auth-file",
                  str(tmp_path / "nope.json")],
                 ["execute", "--execute-auth-file", str(ap)]):
        assert v33.main(argv) == v33.EXIT_UNAUTHORIZED
        payload = json.loads(capsys.readouterr().out)
        assert payload["blocked"] == "unauthorized"
    assert not v33.OFFICIAL_RUN_ROOT.exists()          # zero side effects


def test_t1_execute_auth_binds_head_and_call_matrix():
    auth = dict(v33.EXECUTE_AUTH_EXACT_VALUES)
    auth.update({
        "implementation_commit": v33.git_head(),
        "call_matrix_digest": v33.expected_call_matrix_digest(),
        "granted_by": "Codex main",
        "decision_id": "test-only",
        "granted": True,
    })
    assert v33.validate_execute_auth(auth) is None

    bad_commit = dict(auth, implementation_commit="0" * 40)
    assert "current HEAD" in v33.validate_execute_auth(bad_commit)
    bad_matrix = dict(auth, call_matrix_digest="0" * 64)
    assert "frozen call matrix" in v33.validate_execute_auth(bad_matrix)


def test_t1_path_guard_full_scenarios():
    def w(rel: str) -> Path:
        return v33.REPO_ROOT / rel

    protected_self = [rel for _, rel in v33.PROTECTED_OLD_ROOTS]
    for rel in protected_self:
        with pytest.raises(v33.WriteGuardError):
            v33.guard_run_root(w(rel), fake=True)
        with pytest.raises(v33.WriteGuardError):
            v33.guard_run_root(w(rel + "/sub/dir"), fake=True)
    for bad in (v33.REPO_ROOT, v33.RESULTS_ROOT, w(v33.DIAGNOSTICS_REL),
                v33.ARCHIVE_ROOT, v33.WORKSPACE_ROOT):
        with pytest.raises(v33.WriteGuardError):
            v33.guard_run_root(bad, fake=True)
    if v33.SIBLING_CHECKOUT.exists():                  # present on this machine
        with pytest.raises(v33.WriteGuardError):
            v33.guard_run_root(v33.SIBLING_CHECKOUT, fake=True)
    # fake mode must never target the official root, even fresh
    with pytest.raises(v33.WriteGuardError):
        v33.guard_run_root(v33.OFFICIAL_RUN_ROOT, fake=True)
    # production mode: only the complete official run_01 is legal
    assert v33.guard_run_root(v33.OFFICIAL_RUN_ROOT, fake=False) == \
        v33.OFFICIAL_RUN_ROOT.resolve()
    with pytest.raises(v33.WriteGuardError):
        v33.guard_run_root(v33.WORKSPACE_ROOT / "fresh_child", fake=False)
    # fake mode + fresh workspace child root is the sanctioned combination
    fresh = v33.WORKSPACE_ROOT / "v33_guard_probe_child"
    assert v33.guard_run_root(fresh, fake=True) == fresh.resolve()


def test_t1_prepare_rejects_removed_report_out(tmp_path):
    out = tmp_path / "binding_report.json"
    with pytest.raises(SystemExit) as exc:
        v33.main(["prepare", "--runner", RUNNER_SPEC,
                  "--report-out", str(out)])
    assert exc.value.code == 2
    assert not out.exists()


def test_t1_collision_existing_root_byte_frozen(tmp_path):
    root = tmp_path / "run_root"
    root.mkdir()
    (root / "sentinel.txt").write_text("keep me", encoding="utf-8")
    before = _snapshot(root)
    FAKE_PROVIDER.fixture_repo = tmp_path / "fixture_repo"
    build_fixtures(FAKE_PROVIDER.fixture_repo)
    FAKE_PROVIDER.behavior = _tiered_behavior
    FAKE_PROVIDER.probe = None
    FAKE_PROVIDER.context_override = None
    rc = _run(["execute", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    assert rc == v33.EXIT_COLLISION
    assert _snapshot(root) == before                   # nothing written


def test_t1_verify_missing_or_drifted_manifest(tmp_path):
    rc = _sub("verify", tmp_path / "never_created")
    assert rc == v33.EXIT_MANIFEST
    root, rc = _flow(tmp_path / "a")
    assert rc == v33.EXIT_OK
    manifest = _load(root / "audit_manifest.json")
    manifest["git_head"] = "0" * 40                    # any body drift...
    _dump(root / "audit_manifest.json", manifest)
    assert _sub("verify", root) == v33.EXIT_MANIFEST   # ...breaks freeze_digest


def test_t1_verify_fixed_digest_matrix_tamper(tmp_path):
    root, rc = _flow(tmp_path)
    assert rc == v33.EXIT_OK
    mp = root / "audit_manifest.json"
    manifest = _load(mp)
    manifest["frozen_call_matrix"]["entropy_tol_bits"] = 0.05   # judgement tamper
    body = {k: v for k, v in manifest.items() if k != "freeze_digest"}
    manifest["freeze_digest"] = v33.sha256_bytes(
        v33.canonical_json(body).encode("utf-8"))               # digest repaired
    _dump(mp, manifest)
    assert v33.verify_freeze_digest(manifest) is True           # digest alone insufficient
    assert _sub("verify", root) == v33.EXIT_EVIDENCE_INCONSISTENT


def test_t1_verify_binding_and_field_tamper_post_run(tmp_path, capsys):
    # (a) raw byte drift on a bound input after execution
    root, rc = _flow(tmp_path / "byte")
    assert rc == v33.EXIT_OK
    p2 = FAKE_PROVIDER.fixture_repo / v33.BINDING_PATHS["R2"]
    p2.write_bytes(p2.read_bytes() + b"\n")
    assert _sub("verify", root) == v33.EXIT_EVIDENCE_INCONSISTENT
    assert any("binding_sha_drift:R2" in p for p in _problems(capsys))
    # (b) semantic field tamper (field identity) after execution
    root2, rc2 = _flow(tmp_path / "field")
    assert rc2 == v33.EXIT_OK
    p4 = FAKE_PROVIDER.fixture_repo / v33.BINDING_PATHS["R4"]
    doc = _load(p4)
    doc["configs"]["1024"]["field"]["field_id"] = "f" * 64
    _dump(p4, doc)
    assert _sub("verify", root2) == v33.EXIT_EVIDENCE_INCONSISTENT
    assert any("field_mismatch" in p for p in _problems(capsys))


@pytest.mark.parametrize("mutate,token", [
    (lambda recs: recs[0].__setitem__("rate", 0.5), "rate_drift"),
    (lambda recs: recs[0].__setitem__("rho", {"64": 1.0}), "rho_drift"),
    (lambda recs: recs[0]["params"].__setitem__("streak", 5), "param_drift"),
    (lambda recs: recs[0].__setitem__("not_fixed_packet_de", False),
     "not_fixed_packet_de_flag_missing"),
    (lambda recs: recs[0].__setitem__("source_id", "wrong-source"),
     "source_id_drift"),
    (lambda recs: recs[0].__setitem__("claim_boundary", "finite-ready"),
     "call_claim_boundary_drift"),
    (lambda recs: recs[0].__setitem__("terminal", "FAIL"), "terminal_replay"),
    (lambda recs: recs[0].__setitem__(
        "entropy_trace_bits", recs[0]["entropy_trace_bits"][:10]),
     "terminal_replay"),
], ids=["rate", "rho", "params", "flag", "source_id", "claim_boundary",
        "terminal", "truncated_trace"])
def test_t1_verify_record_drift_family(tmp_path, mutate, token, capsys):
    root, rc = _flow(tmp_path, behavior=_all_pass)     # uniform PASS records
    assert rc == v33.EXIT_OK
    cp = root / "de_call_matrix.json"
    doc = _load(cp)
    mutate(doc["records"])
    _dump(cp, doc)
    assert _sub("verify", root) == v33.EXIT_EVIDENCE_INCONSISTENT
    assert any(token in p for p in _problems(capsys))


def test_t1_verify_rejects_final_claim_promotion(tmp_path, capsys):
    root, rc = _flow(tmp_path, behavior=_all_pass)
    assert rc == v33.EXIT_OK
    fp = root / "final_state.json"
    final = _load(fp)
    final["candidate_only"] = False
    final["claim_boundary"] = "qualified"
    _dump(fp, final)
    assert _sub("verify", root) == v33.EXIT_EVIDENCE_INCONSISTENT
    assert any("candidate_claim_boundary_invalid" in p
               for p in _problems(capsys))


@pytest.mark.parametrize("attack,token", [
    ("malformed", "unparsable"),
    ("duplicate", "duplicate_call"),
    ("missing", "missing_calls"),
    ("extra", "extra_call_at_index"),
    ("out_of_order", "out_of_order_at_index"),
])
def test_t1_verify_call_sequence_attacks(tmp_path, attack, token, capsys):
    root, rc = _flow(tmp_path, behavior=_all_pass)
    assert rc == v33.EXIT_OK
    cp = root / "de_call_matrix.json"
    doc = _load(cp)
    recs = doc["records"]
    if attack == "malformed":
        cp.write_bytes(b"{broken json")
    elif attack == "duplicate":
        recs.insert(3, dict(recs[3]))
        _dump(cp, doc)
    elif attack == "missing":
        doc["records"] = recs[:-1]
        _dump(cp, doc)
    elif attack == "extra":
        bogus = dict(recs[-1])
        bogus["ordinal"] = 31
        doc["records"] = recs + [bogus]
        _dump(cp, doc)
    else:
        recs[0], recs[1] = recs[1], recs[0]
        _dump(cp, doc)
    assert _sub("verify", root) == v33.EXIT_EVIDENCE_INCONSISTENT
    assert any(token in p for p in _problems(capsys))


# --------------------------------------------------------------------------- #
# T2 — full fake qualification / replay / reconstruction / exact-once
# --------------------------------------------------------------------------- #

def test_t2_full_flow_three_way_routing_and_files(tmp_path):
    root, rc = _flow(tmp_path)                          # tiered default behavior
    assert rc == v33.EXIT_OK
    assert {p.name for p in root.iterdir()} == SIX_FILES
    assert len(FAKE_PROVIDER.calls) == 30
    manifest = _load(root / "audit_manifest.json")
    assert manifest["schema"] == v33.MANIFEST_SCHEMA
    assert manifest["lifecycle"]["execute_auth"]["mechanism"] == "fake_runner"
    assert manifest["lifecycle"]["not_fixed_packet_de"] is True
    fcm = manifest["frozen_call_matrix"]
    assert fcm["seeds"] == list(SEEDS_LITERAL)
    assert fcm["n_samples"] == N_SAMPLES_LITERAL
    assert fcm["max_iter"] == MAX_ITER_LITERAL
    assert fcm["entropy_tol_bits"] == ENTROPY_TOL_LITERAL
    assert fcm["streak"] == STREAK_LITERAL
    assert fcm["rng"] == "PCG64" and fcm["total_calls"] == 30
    assert fcm["m1"] == 16 and fcm["n_blocks"] == 1024
    assert "2000 MC population rows" in manifest["convergence_definition"]
    assert manifest["implementation_identity"]["cli_sha256"] == \
        v33.sha256_file(Path(v33.__file__))
    assert set(manifest["output_inventory"]) == SIX_FILES
    cells = _load(root / "de_cell_matrix.json")["cells"]
    want = {"1M|L1": "PASS", "1M|L2": "PASS",
            "1p5M|L1": "FAIL", "1p5M|L2": "FAIL",
            "2M|L1": "INCONCLUSIVE", "2M|L2": "INCONCLUSIVE"}
    assert {k: c["terminal"] for k, c in cells.items()} == want
    md = (root / "de_cell_matrix.md").read_text(encoding="utf-8")
    assert "2M|L2" in md and "INCONCLUSIVE" in md
    final = _load(root / "final_state.json")
    assert final["overall_terminal"] == "INCONCLUSIVE"
    assert final["overall_label"] == v33.OVERALL_INCONCLUSIVE_LABEL
    assert final["reason_codes"] == ["numeric_nan"]
    assert final["calls_total"] == 30
    assert final["not_fixed_packet_de"] is True
    assert final["candidate_only"] is True
    assert final["main_acceptance_pending"] is True
    assert final["qualification"] is False and final["promotion"] is False
    assert final["freeze_digest_ref"] == manifest["freeze_digest"]
    assert final["claim_boundary"] == v33.CLAIM_BOUNDARY
    records = _load(root / "de_call_matrix.json")["records"]
    assert len(records) == 30
    assert all(r["not_fixed_packet_de"] is True for r in records)
    assert all(r["claim_boundary"] == v33.CLAIM_BOUNDARY for r in records)
    assert all(isinstance(r.get("detail"), str) and r["detail"]
               for r in records if r["terminal"] == "INCONCLUSIVE")
    ref = _load(root / "v26_reference_readonly.json")
    assert ref["gate"]["status"] == "pass_target_f13"


def test_t2_overall_pass_route(tmp_path):
    root, rc = _flow(tmp_path, behavior=_all_pass)
    assert rc == v33.EXIT_OK
    cells = _load(root / "de_cell_matrix.json")["cells"]
    assert all(c["terminal"] == "PASS" for c in cells.values())
    final = _load(root / "final_state.json")
    assert final["overall_terminal"] == "PASS"
    assert final["overall_label"] == v33.OVERALL_PASS_LABEL
    assert final["reason_codes"] == []


def test_t2_overall_fail_route(tmp_path):
    root, rc = _flow(tmp_path, behavior=_all_fail)
    assert rc == v33.EXIT_OK
    cells = _load(root / "de_cell_matrix.json")["cells"]
    assert all(c["terminal"] == "FAIL" for c in cells.values())
    final = _load(root / "final_state.json")
    assert final["overall_terminal"] == "FAIL"
    assert final["overall_label"] == v33.OVERALL_FAIL_LABEL


def test_t2_exact_once_order_and_per_call_persistence(tmp_path):
    root, _ = _flow(tmp_path, behavior=_tiered_behavior)
    FAKE_PROVIDER.calls.clear()
    assert _run(["execute", "--runner", RUNNER_SPEC,
                 "--run-root", str(root)]) == v33.EXIT_COLLISION  # root exists
    # rerun into a sibling root to observe persistence sequencing
    root2 = tmp_path / "run_root2"
    FAKE_PROVIDER.fixture_repo = tmp_path / "fixture_repo"
    seen: list[int] = []

    def probe(_req):
        cp = root2 / "de_call_matrix.json"
        seen.append(len(json.loads(cp.read_text(encoding="utf-8"))["records"])
                    if cp.exists() else 0)

    FAKE_PROVIDER.probe = probe                        # armed before the run
    rc = _run(["execute", "--runner", RUNNER_SPEC, "--run-root", str(root2)])
    assert rc == v33.EXIT_OK
    assert seen == list(range(30))     # k-th call answered with k-1 persisted
    records = _load(root2 / "de_call_matrix.json")["records"]
    assert len(records) == 30
    assert [(r["source_label"], r["layer"], r["seed"]) for r in records] == \
        list(EXPECTED_ORDER)
    assert [r["ordinal"] for r in records] == list(range(1, 31))
    keys = [(r["source_label"], r["layer"], r["seed"]) for r in records]
    assert len(set(keys)) == 30                        # exact-once, no repeats


def test_t2_independent_reconstruction_from_evidence(tmp_path):
    """Independently recompute call/cell/overall terminals from the persisted
    evidence only (own replay + own aggregation, own literals)."""
    root, rc = _flow(tmp_path)                         # three-way tiered routing
    assert rc == v33.EXIT_OK
    records = _load(root / "de_call_matrix.json")["records"]

    def own_replay(rec):
        if rec["terminal"] == "INCONCLUSIVE":
            return "INCONCLUSIVE"
        streak = 0
        for h in rec["entropy_trace_bits"]:
            if (not math.isfinite(h)) or h < 0.0:
                return "INCONCLUSIVE"
            streak = streak + 1 if h < ENTROPY_TOL_LITERAL else 0
            if streak >= STREAK_LITERAL:
                return "PASS"
        return "FAIL" if len(rec["entropy_trace_bits"]) >= \
            MAX_ITER_LITERAL else "INCONCLUSIVE"

    assert all(own_replay(r) == r["terminal"] for r in records)
    cells_own = {}
    for lbl in LABELS:
        for lyr in LAYERS:
            terms = [r["terminal"] for r in records
                     if r["source_label"] == lbl and r["layer"] == lyr]
            if len(terms) != 5 or "INCONCLUSIVE" in terms:
                t = "INCONCLUSIVE"
            elif all(x == "PASS" for x in terms):
                t = "PASS"
            else:
                t = "FAIL"
            cells_own[f"{lbl}|{lyr}"] = t
    stored = _load(root / "de_cell_matrix.json")["cells"]
    assert {k: c["terminal"] for k, c in stored.items()} == cells_own
    terms_all = list(cells_own.values())
    if "INCONCLUSIVE" in terms_all:
        overall = "INCONCLUSIVE"
    elif all(t == "PASS" for t in terms_all):
        overall = "PASS"
    else:
        overall = "FAIL"
    final = _load(root / "final_state.json")
    assert final["overall_terminal"] == overall
    labels = {"PASS": v33.OVERALL_PASS_LABEL,
              "FAIL": v33.OVERALL_FAIL_LABEL,
              "INCONCLUSIVE": v33.OVERALL_INCONCLUSIVE_LABEL}
    assert final["overall_label"] == labels[overall]


def test_t2_strict_replay_identical_outputs(tmp_path):
    fx = tmp_path / "fixture_repo"
    build_fixtures(fx)
    FAKE_PROVIDER.fixture_repo = fx
    FAKE_PROVIDER.behavior = _tiered_behavior
    FAKE_PROVIDER.probe = None
    FAKE_PROVIDER.context_override = None
    root_a = tmp_path / "replay_a"
    root_b = tmp_path / "replay_b"
    assert _run(["execute", "--runner", RUNNER_SPEC,
                 "--run-root", str(root_a)]) == v33.EXIT_OK
    assert _run(["execute", "--runner", RUNNER_SPEC,
                 "--run-root", str(root_b)]) == v33.EXIT_OK
    def snap(root: Path) -> dict:
        # ponytail: .md member read as text; JSON members parsed
        return {name: (_load(root / name) if name.endswith(".json")
                       else (root / name).read_text(encoding="utf-8"))
                for name in SIX_FILES}

    snap_a = snap(root_a)
    snap_b = snap(root_b)
    assert "generated_utc" in snap_a["audit_manifest.json"]  # whitelist is real

    base = str(tmp_path.resolve())

    def norm(obj):
        if isinstance(obj, dict):
            return {k: norm(v) for k, v in obj.items()
                    if k not in ("generated_utc", "freeze_digest",
                                 "run_root", "freeze_digest_ref")}
        if isinstance(obj, list):
            return [norm(v) for v in obj]
        if isinstance(obj, str):
            return obj.replace(base, "&BASE&")
        return obj

    for name in sorted(SIX_FILES):
        assert norm(snap_a[name]) == norm(snap_b[name]), name


def test_t2_collision_entry_only_snapshot_frozen(tmp_path):
    """Collision fires once at the execute entry; the stages inside one
    execution never re-trigger it (the first flow wrote all six files after
    mkdir without aborting)."""
    root, rc = _flow(tmp_path)
    assert rc == v33.EXIT_OK                            # post-mkdir stages ran
    before = {p.name: p.read_bytes() for p in sorted(root.iterdir())}
    FAKE_PROVIDER.fixture_repo = tmp_path / "fixture_repo"
    rc2 = _run(["execute", "--runner", RUNNER_SPEC, "--run-root", str(root)])
    assert rc2 == v33.EXIT_COLLISION                    # entry check only
    after = {p.name: p.read_bytes() for p in sorted(root.iterdir())}
    assert after == before                              # refused run: byte-frozen


def test_t2_explicit_injection_required(tmp_path):
    """Without --runner the production gate demands an auth file: a fake-less
    execute can never be entered implicitly from tests."""
    child = v33.WORKSPACE_ROOT / "v33_probe_child_root"
    rc = v33.main(["execute", "--run-root", str(child)])
    assert rc == v33.EXIT_UNAUTHORIZED
    assert not child.exists()


# --------------------------------------------------------------------------- #
# T3 — real-input read-only identity smoke (no DE, no decoder, no graph)
# T3 scope: "T3 smoke: PASS; full frozen T3 regression: not in scope."
# --------------------------------------------------------------------------- #

def test_t3_real_bindings_readonly_identity():
    digests = {}
    for rid, rel in v33.BINDING_PATHS.items():
        p = v33.REPO_ROOT / rel
        assert p.exists(), f"real binding {rid} missing: {rel}"
        d1, d2 = v33.sha256_file(p), v33.sha256_file(p)
        assert d1 == d2 and len(d1) == 64
        digests[rid] = d1
    # R1 npz keys verbatim + shapes (lazy per-key read)
    with np.load(v33.REPO_ROOT / v33.BINDING_PATHS["R1"]) as data:
        keys = list(data.files)
        for lbl in LABELS:
            assert NPZ_KEYS[lbl] in keys
            arr = data[NPZ_KEYS[lbl]]
            assert arr.shape == (1024, 1024)
    # R2 raw_ser literals present
    summary = _load(v33.REPO_ROOT / v33.BINDING_PATHS["R2"])
    for sid, ser in SER_BY_SID.items():
        assert float(summary["per_source"][sid]["ser"]) == ser
    # layer-rate table literals (independent typing)
    rates = v33.layer_rates()
    for lbl in LABELS:
        for lyr in LAYERS:
            assert rates[lbl][lyr]["R_i"] == RATES_LITERAL[lyr][lbl]
    # R5 packet identity / R6 allocation filter / R7 gate literals
    audits = _load(v33.REPO_ROOT / v33.BINDING_PATHS["R5"])
    pk = [q for q in audits["packets"]
          if q.get("packet_id") == PACKET_ID_LITERAL]
    assert pk and pk[0]["audits"]["L1"]["shape"] == [16, 1024]
    reg = _load(v33.REPO_ROOT / v33.BINDING_PATHS["R6"])
    filt = [c for c in reg["registered_calls"]
            if c.get("allocation_id") == ALLOCATION_ID_LITERAL]
    assert len(filt) >= 6
    gate = _load(v33.REPO_ROOT / v33.BINDING_PATHS["R7"])
    assert gate["status"] == "pass_target_f13"
    assert gate["best_passing_f"] == {"A01": 1.6, "A02": 1.3}
    assert set(digests) == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}


def _project_engine_modules() -> set:
    """Names of any loaded project modules outside the CLI under test."""
    import sys
    return {k for k in sys.modules
            if k.startswith("comparison_bench")
            and "run_nonbinary_v33_rate_aligned_empirical_de" not in k}


def test_t3_fake_flow_leaves_protected_roots_and_official_root_untouched(tmp_path):
    watch = [rel for _, rel in v33.PROTECTED_OLD_ROOTS] + [
        v33.BINDING_PATHS[r] for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R7")]
    pre = {rel: _snapshot(v33.REPO_ROOT / rel) for rel in watch}
    mods_before = _project_engine_modules()
    root, rc = _flow(tmp_path)                          # full fake qualification
    assert rc == v33.EXIT_OK
    assert _sub("verify", root) == v33.EXIT_OK
    post = {rel: _snapshot(v33.REPO_ROOT / rel) for rel in watch}
    assert pre == post                                  # read-only respected
    new_mods = _project_engine_modules() - mods_before  # no DE/decoder/graph
    # only this test module (imported by load_runner via --runner) may appear
    assert all(k.startswith("test_nonbinary_v33") for k in new_mods), new_mods
    assert not v33.OFFICIAL_RUN_ROOT.exists()           # official root untouched
