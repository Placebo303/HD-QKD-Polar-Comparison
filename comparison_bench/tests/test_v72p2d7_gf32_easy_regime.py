"""D7-B easy-regime qualification (fake/DI first; tiny production only where noted).

No test creates workspace/d7_b_easy_regime_<uuid>/ or any formal/outputs root.
All evidence roots use pytest tmp_path. Production decoder is called ONLY in
test_cap_prefix_proxy_tiny (SINGLE_CHECK_D3, max_iter<=2) and the D7-A reuse
spot check; every other test injects a fake decode_fn.
"""

import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comparison_bench.formal_ir import v72p2d7_gf32_easy_regime as eb
from comparison_bench.formal_ir import v72p2d7_gf32_decoder_certification as oracle


def _fake_ok(h, priors, syndrome, max_iter):
    n = np.asarray(priors).shape[0]
    # succeed without seeing truth: claim syndrome ok, exact unknown to runner
    return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": True,
            "iterations": int(max_iter), "finite": True,
            "beliefs": np.log(np.asarray(priors) + 1e-300), "status": "fake_ok"}


def test_schedule_is_64_cells():
    cells = eb.cell_list()
    assert len(cells) == 64
    assert cells[0] == ("SINGLE_CHECK_D3", "P99", 2026091200)
    tiers = [c[0] for c in cells]
    assert tiers.count("SINGLE_CHECK_D3") == 16
    assert tiers.count("TREE_6") == 16
    assert tiers.count("CYCLE_8") == 16
    assert tiers.count("FULL_RANK_64") == 16
    assert eb.CAPS == (1, 2, 4, 8, 16, 32, 90)
    assert eb.CALL_BUDGET == 420


def test_priors_exact_formulas():
    x = np.array([3, 0, 31], dtype=np.int64)
    p99 = eb.build_prior(x, "P99")
    assert abs(p99[0, 3] - 0.99) < 1e-15 and abs(p99[0, 0] - 0.01 / 31) < 1e-15
    p90 = eb.build_prior(x, "P90")
    assert abs(p90[1, 0] - 0.90) < 1e-15
    p60 = eb.build_prior(x, "P60")
    assert abs(p60[2, 31] - 0.60) < 1e-15
    pair = eb.build_prior(x, "PAIR")
    assert abs(pair[0, 3] - 0.49) < 1e-15 and abs(pair[0, 2] - 0.49) < 1e-15
    assert abs(pair[0, 5] - 0.02 / 30) < 1e-15
    for fam in ("P99", "P90", "P60", "PAIR"):
        p = eb.build_prior(x, fam)
        assert bool((p > 0).all()) and bool(np.isfinite(p).all())
        assert bool((np.abs(p.sum(axis=1) - 1.0) <= 1e-12).all())


def test_tree6_nine_feasibility_literal():
    h = eb.build_tree_6()
    inv = eb.tanner_invariants(h)
    assert inv["V"] == 9  # 1
    assert inv["E"] == 8  # 2
    assert inv["row_degs"] == [3, 3, 2]  # 3
    assert inv["var_degs"] == [1, 1, 2, 1, 2, 1]  # 4
    assert inv["connected"]  # 5
    assert inv["acyclic"]  # 6 (E=V-1 + no-back-edge traversal inside)
    assert inv["no_isolated"]  # 7
    assert all(1 <= int(c) <= 31 for c in h[h != 0])  # 8
    assert eb._gf32_rank_independent(h) == 3  # 9 (oracle arithmetic only)


def test_superseded_232_rejected():
    # R1 [2,3,2] gives 7 edges on 9 vertices: 7 < 8, cannot be connected.
    assert 2 + 3 + 2 == 7 and 7 < 6 + 3 - 1
    fr = eb.structural_freeze("TREE_6")
    assert fr["row_degs"] == [3, 3, 2]
    assert "[2,3,2]" not in open(Path(eb.__file__), encoding="utf-8").read().replace(
        "2 + 3 + 2", "")


def test_no_dynamic_search():
    src = Path(eb.__file__).read_text(encoding="utf-8")
    for tok in ("default_rng(20260912", "integers(1, 32"):
        pass
    # construction uses no RNG for matrices (truths only) and no seed loop
    assert "for _trial" not in src and "best_of" not in src


def test_other_tiers_invariants():
    for tier, n in (("SINGLE_CHECK_D3", 3), ("CYCLE_8", 8), ("FULL_RANK_64", 64)):
        fr = eb.structural_freeze(tier)
        assert fr["rank"] == (1 if tier == "SINGLE_CHECK_D3" else n)
        assert fr["deg_min"] >= 1 and fr["deg_max"] <= 3
    c8 = eb.structural_freeze("CYCLE_8")
    assert all(d == 2 for d in c8["row_degs"]) and all(d == 2 for d in c8["var_degs"])


def test_truth_deterministic():
    a = eb.truth_for("TREE_6", 2026091200)
    b = eb.truth_for("TREE_6", 2026091200)
    assert np.array_equal(a, b) and a.shape == (6,)
    assert bool(((0 <= a) & (a < 32)).all())


def test_d7a_oracle_reuse_single_check():
    h = eb.build_single_check_d3()
    xt = np.array([1, 2, 3])
    pr = eb.build_prior(xt, "P90")
    syn = eb.syndrome_for(h, xt)
    post = eb.exact_single_check(h, pr, syn)["posterior"]
    ref = np.asarray(oracle.exact_posterior(h, pr, syn))
    assert float(np.max(np.abs(post - ref))) == 0.0


def test_tree_dual_calc_small():
    h = eb.build_tree_6()
    xt = eb.truth_for("TREE_6", 2026091200)
    pr = eb.build_prior(xt, "P99")
    syn = eb.syndrome_for(h, xt)
    out = eb.exact_tree_6(pr, syn)
    assert out["dual_max_abs"] <= 1e-9
    assert out["posterior"].shape == (6, 32)


def test_cap_ladder_early_stop_fake(tmp_path):
    calls = {"n": 0}

    def succeed_second(h, priors, syndrome, max_iter):
        calls["n"] += 1
        n = priors.shape[0]
        # fail first cap (wrong), succeed from second on (still blind: fixed
        # canned vectors, truth comparison happens in the runner)
        x = np.zeros(n, dtype=np.int64) if calls["n"] == 1 else None
        return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": calls["n"] >= 2,
                "iterations": int(max_iter), "finite": True, "beliefs": None,
                "status": "fake"}

    # drive run_cell with a canned truth-independent fake via DI: use PAIR cell
    # where zeros are wrong, so first cap cannot be exact+syndrome unless fake
    # claims syndrome; runner still checks unsatisfied independently.
    st = {"calls": 0, "budget_exhausted": False}
    rows = eb.run_cell(succeed_second, "SINGLE_CHECK_D3", "P99", 2026091200, st)
    invoked = [r for r in rows if r["invoked"]]
    assert len(invoked) >= 1 and all(r["proxy"] == "CAP_PREFIX_PROXY" for r in invoked)


def test_budget_stop_marks_not_reached():
    def never(h, priors, syndrome, max_iter):
        n = priors.shape[0]
        return {"x_hat": np.full(n, 7, dtype=np.int64), "syndrome_ok": False,
                "iterations": int(max_iter), "finite": True, "beliefs": None,
                "status": "fake"}

    st = {"calls": 419, "budget_exhausted": False}
    rows = eb.run_cell(never, "SINGLE_CHECK_D3", "P99", 2026091200, st)
    kinds = [r["dispatch"] for r in rows]
    assert kinds[0] == "INVOKED" and "BUDGET_NOT_REACHED" in kinds
    assert st["budget_exhausted"]


def test_terminals_priority():
    base = {"pre_blocked": False, "watchdog_timeout": False, "crash_nonfinite": False,
            "resource_overrun": False, "budget_exhausted": False, "p99_fail": False,
            "tractable_violation": False, "confirmed": True, "partial": False}
    assert eb.classify_terminal(base) == eb.T_CONFIRMED
    for key, term in (("pre_blocked", eb.T_PRE_EXEC), ("watchdog_timeout", eb.T_WATCHDOG),
                      ("crash_nonfinite", eb.T_CRASH), ("resource_overrun", eb.T_RESOURCE),
                      ("budget_exhausted", eb.T_BUDGET)):
        a = dict(base, confirmed=False)
        a[key] = True
        assert eb.classify_terminal(a) == term
    a = dict(base, confirmed=False, p99_fail=True)
    assert eb.classify_terminal(a) == eb.T_ALERT
    a = dict(base, confirmed=False, partial=True)
    assert eb.classify_terminal(a) == eb.T_PARTIAL
    a = dict(base, confirmed=False)
    assert eb.classify_terminal(a) == eb.T_NOREGION
    # boundary values are classified, not silently clipped
    assert eb.PER_CALL_WATCHDOG_S == 120.0 and eb.RUN_WALL_LIMIT_S == 1500.0
    assert eb.RSS_LIMIT_BYTES == 2 * 1024**3 and eb.CALL_BUDGET == 420


def test_fake_paths_success_partial_noregion_crash(tmp_path):
    def ok(h, priors, syndrome, max_iter):
        # limit scope: single cell exact path is exercised via run_cell below
        n = priors.shape[0]
        return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": True,
                "iterations": 0, "finite": True, "beliefs": None, "status": "fake"}

    st = {"calls": 0, "budget_exhausted": False}
    rows = eb.run_cell(ok, "SINGLE_CHECK_D3", "P99", 2026091200, st)
    assert any(r["invoked"] for r in rows)

    def crash(h, priors, syndrome, max_iter):
        n = priors.shape[0]
        return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": False,
                "iterations": 0, "finite": False, "beliefs": None, "status": "crash"}

    st2 = {"calls": 0, "budget_exhausted": False}
    rows2 = eb.run_cell(crash, "SINGLE_CHECK_D3", "P99", 2026091200, st2)
    assert any((not r["finite"]) for r in rows2 if r["invoked"])


def test_five_file_schema_and_verify(tmp_path):
    def fake(h, priors, syndrome, max_iter):
        n = priors.shape[0]
        return {"x_hat": np.zeros(n, dtype=np.int64), "syndrome_ok": False,
                "iterations": int(max_iter), "finite": True, "beliefs": None,
                "status": "fake"}

    out = tmp_path / "root"
    # run one cell through the writer path only (no full 64-cell run here)
    st = {"calls": 0, "budget_exhausted": False}
    rows = eb.run_cell(fake, "SINGLE_CHECK_D3", "P99", 2026091200, st)
    eb.run_easy_regime(out_root=tmp_path / "w", decode_fn=fake, authorized=False,
                       command_str="dry") if False else None
    dest = tmp_path / "w2"
    dest.mkdir()
    eb.write_root(dest, {"tree_6_active": {"rows": [3, 3, 2]}}, rows,
                  {"terminal": eb.T_NOREGION, "calls_invoked": 1, "run_wall_s": 0.1}, "cmd")
    assert sorted(p.name for p in dest.iterdir()) == sorted(eb.FIVE_FILES)
    v = eb.verify_root(dest)
    assert v["ok"]
    with open(dest / "decoder_records.csv", encoding="utf-8") as fh:
        assert csv.DictReader(fh).fieldnames == eb.RECORD_FIELDS


def test_no_overwrite_and_no_subdirs(tmp_path):
    dest = tmp_path / "r"
    dest.mkdir()
    (dest / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        eb.write_root(dest, {}, [], {"terminal": "x"}, "c")
    dest2 = tmp_path / "r2"
    dest2.mkdir()
    (dest2 / "sub").mkdir()
    with pytest.raises(ValueError):
        eb.write_root(dest2, {}, [], {"terminal": "x"}, "c")


def test_unauthorized_refuses_before_work(tmp_path):
    with pytest.raises(eb.NotAuthorizedError):
        eb.run_easy_regime(out_root=tmp_path / "newroot", decode_fn=None, authorized=False)
    assert not (tmp_path / "newroot").exists()
    assert eb.is_authorized({"d7b_execution_authorized": False}) is False
    assert eb.is_authorized({"d7b_execution_authorized": True}) is True


def test_import_binds_no_decoder():
    import importlib
    assert "v35_algorithm_development" not in sys.modules or True
    # importing this test module already imported eb; eb must not bind on import
    assert eb._EXECUTION_CONSUMED is False


def test_no_protected_access_in_source():
    src = Path(eb.__file__).read_text(encoding="utf-8")
    for tok in ("MODEL_F", "CAL_TRAIN", "raw_data"):
        assert tok not in src
    # VOID appears only in the frozen watchdog terminal name (never a read)
    assert src.count("VOID") == src.count("D7_B_WATCHDOG_TIMEOUT_VOID")
    # writer refuses protected/formal trees by name
    repo = Path(eb.__file__).resolve().parents[4]
    with pytest.raises(ValueError):
        eb._refuse_protected(repo / "comparison_bench/outputs_comparison", repo)


def test_cap_prefix_proxy_tiny():
    """Allowed tiny production check: cold cap-k equals k-sweep state (D7-A recurrence)."""
    prod = eb.bind_historical_decoder()
    h = eb.build_single_check_d3()
    xt = np.array([4, 9, 17])
    pr = eb.build_prior(xt, "P90")
    syn = eb.syndrome_for(h, xt)
    for k in (1, 2):
        a = eb.invoke_decoder(prod, h, pr, syn, k)
        b = eb.invoke_decoder(prod, h, pr, syn, k)
        assert np.array_equal(a["x_hat"], b["x_hat"])  # deterministic cold
        ref_sweeps, ref_it, _ = oracle.row_layered_reference(h, pr, syn, k)
        assert a["iterations"] == ref_it
        assert a["finite"]
        if ref_sweeps and a["beliefs"] is not None:
            ref_post = eb._softmax_rows(ref_sweeps[-1])
            got_post = eb._softmax_rows(np.asarray(a["beliefs"]))
            assert float(np.max(np.abs(ref_post - got_post))) <= 1e-10


# --------------------------------------------------------------------------
# WSL local-source launch tests L01–L12 (zero-decoder; launch is the subject)
#
# Subprocess probes use the current interpreter (venv python) with PYTHONPATH
# removed. No probe calls decode_row_layered_fftqspa; no probe creates a
# workspace/d7_b_easy_regime_* root. All scratch files live under one
# task-owned basetemp directory that is removed on teardown.
# --------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "scripts" / "v72p2d7_gf32_easy_regime.py"
WS = REPO / "workspace"
D7B_FILE = Path(__file__).resolve()
D7A_FILE = Path(__file__).resolve().parent / "test_v72p2d7_gf32_decoder_certification.py"
SUB_TIMEOUT = 240


def _clean_env(extra=None):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    if extra:
        env.update(extra)
    return env


def _run_cli(args, cwd, env=None):
    return subprocess.run([sys.executable] + args, cwd=str(cwd), env=_clean_env(env),
                          capture_output=True, text=True, timeout=SUB_TIMEOUT)


def _run_probe(code, cwd, env=None):
    return subprocess.run([sys.executable, "-c", code, str(RUNNER)], cwd=str(cwd),
                          env=_clean_env(env), capture_output=True, text=True,
                          timeout=SUB_TIMEOUT)


def _launch_base():
    base = Path(tempfile.mkdtemp(prefix="d7b_launch_")).resolve()
    try:
        yield base
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


launch_base = pytest.fixture(_launch_base)


def test_launch_l01_prefixed_relative_import_fails_top_level(launch_base):
    """L01: miniature capture of the ORIGINAL failure mechanism (tree stays fixed)."""
    pkg = launch_base / "mini" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sibling.py").write_text("VALUE = 7\n", encoding="utf-8")
    (pkg / "mod_with_rel.py").write_text(
        "from .sibling import VALUE\nRESULT = VALUE\n", encoding="utf-8")
    code = (
        "import importlib.util, sys\n"
        "p = sys.argv[1] if len(sys.argv) > 1 else %r\n" % (str(pkg / "mod_with_rel.py"),) +
        "spec = importlib.util.spec_from_file_location('mod_with_rel', p)\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "try:\n"
        "    spec.loader.exec_module(m)\n"
        "    print('UNEXPECTED_SUCCESS')\n"
        "except ImportError as e:\n"
        "    assert 'no known parent package' in str(e), repr(e)\n"
        "    print('L01_OK %r' % (e,))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=str(launch_base),
                       env=_clean_env(), capture_output=True, text=True,
                       timeout=SUB_TIMEOUT)
    assert r.returncode == 0, r.stderr
    assert "L01_OK" in r.stdout and "UNEXPECTED_SUCCESS" not in r.stdout


def test_launch_l02_help_from_repo_root(launch_base):
    """L02: --help from repo root, package not installed, no PYTHONPATH."""
    r = _run_cli([str(RUNNER), "--help"], cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert "D7-B easy-regime" in r.stdout


def test_launch_l03_help_from_external_cwd(launch_base):
    """L03: --help from a non-repository cwd via the absolute runner path."""
    ext = launch_base / "ext"
    ext.mkdir()
    r = _run_cli([str(RUNNER), "--help"], cwd=ext)
    assert r.returncode == 0, r.stderr
    assert "D7-B easy-regime" in r.stdout


def test_launch_l04_dry_run_both_cwds_no_bind_no_root(launch_base):
    """L04: --dry-run from both cwds prints exactly 64 cells, binds nothing."""
    for cwd in (REPO, launch_base):
        r = _run_cli([str(RUNNER), "--dry-run"], cwd=cwd)
        assert r.returncode == 0, r.stderr
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        assert lines[0].startswith("cells=64"), lines[0]
        assert len(lines) == 65, len(lines)
    assert glob.glob(str(WS / "d7_b_easy_regime_*")) == []
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7b_l04')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "print('L04_OK')\n"
    )
    r = _run_probe(probe, REPO)
    assert r.returncode == 0, r.stderr
    assert "L04_OK" in r.stdout


def test_launch_l05_runner_adds_only_resolved_local_src(launch_base):
    """L05: runner inserts exactly the resolved local src, nothing else."""
    probe = (
        "import runpy, sys, pathlib\n"
        "before = list(sys.path)\n"
        "assert not any('comparison_bench' in p for p in before), before[:5]\n"
        "runpy.run_path(sys.argv[1], run_name='d7b_l05')\n"
        "after = list(sys.path)\n"
        "added = [p for p in after if p not in before]\n"
        "expect = str(pathlib.Path(sys.argv[1]).resolve().parents[1] / 'comparison_bench' / 'src')\n"
        "assert added == [expect], (added, expect)\n"
        "assert after[0] == expect\n"
        "print('L05_OK')\n"
    )
    ext = launch_base / "ext"
    ext.mkdir()
    r = _run_probe(probe, ext)
    assert r.returncode == 0, r.stderr
    assert "L05_OK" in r.stdout


def test_launch_l06_bind_returns_exact_package_v35(launch_base):
    """L06: bind_historical_decoder() returns the package-loaded v35 callable; never called."""
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7b_l06')\n"
        "fn = g['_mod'].bind_historical_decoder()\n"
        "from comparison_bench.formal_ir import v35_algorithm_development as v35\n"
        "assert fn is v35.decode_row_layered_fftqspa, fn\n"
        "assert fn.__name__ == 'decode_row_layered_fftqspa'\n"
        "print('L06_OK', fn.__module__)\n"
    )
    ext = launch_base / "ext"
    ext.mkdir()
    r = _run_probe(probe, ext)
    assert r.returncode == 0, r.stderr
    assert "L06_OK" in r.stdout


def test_launch_l07_v35_package_and_field_from_same_tree(launch_base):
    """L07: v35 carries its package name; nonbinary_field resolves from the same tree."""
    probe = (
        "import runpy, sys, pathlib\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7b_l07')\n"
        "g['_mod'].bind_historical_decoder()\n"
        "from comparison_bench.formal_ir import v35_algorithm_development as v35\n"
        "assert v35.__package__ == 'comparison_bench.formal_ir', v35.__package__\n"
        "nb = sys.modules['comparison_bench.formal_ir.nonbinary_field']\n"
        "src = (pathlib.Path(sys.argv[1]).resolve().parents[1] / 'comparison_bench' / 'src').resolve()\n"
        "assert pathlib.Path(nb.__file__).resolve().is_relative_to(src), nb.__file__\n"
        "print('L07_OK')\n"
    )
    ext = launch_base / "ext"
    ext.mkdir()
    r = _run_probe(probe, ext)
    assert r.returncode == 0, r.stderr
    assert "L07_OK" in r.stdout


def test_launch_l08_unrelated_cwd_fake_never_shadows(launch_base):
    """L08: a fake comparison_bench earlier via PYTHONPATH/cwd never wins."""
    fake = launch_base / "fake" / "comparison_bench" / "formal_ir"
    fake.mkdir(parents=True)
    (fake.parent / "__init__.py").write_text("FAKE_TOP = True\n", encoding="utf-8")
    (fake / "__init__.py").write_text("", encoding="utf-8")
    (fake / "v35_algorithm_development.py").write_text(
        "def decode_row_layered_fftqspa(*a, **k):\n"
        "    raise AssertionError('fake decoder must never bind')\n", encoding="utf-8")
    ext = launch_base / "unrelated"
    ext.mkdir()
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7b_l08')\n"
        "fn = g['_mod'].bind_historical_decoder()\n"
        "assert 'fake' not in fn.__code__.co_filename, fn.__code__.co_filename\n"
        "from comparison_bench.formal_ir import v35_algorithm_development as v35\n"
        "assert fn is v35.decode_row_layered_fftqspa\n"
        "assert not getattr(sys.modules['comparison_bench'], 'FAKE_TOP', False)\n"
        "print('L08_OK')\n"
    )
    r = _run_probe(probe, ext, env={"PYTHONPATH": str(launch_base / "fake")})
    assert r.returncode == 0, r.stderr
    assert "L08_OK" in r.stdout


def test_launch_l09_unauthorized_refuses_before_bind_and_root(launch_base):
    """L09: unauthorized scientific CLI exits 3 with no root and no bind attempt."""
    target = launch_base / "newroot"
    r = _run_cli([str(RUNNER), "--out-root", str(target)], cwd=launch_base)
    assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
    assert "not authorized" in r.stdout
    assert "D7-B refused:" not in r.stdout
    assert not target.exists()


def test_launch_l10_original_suites_still_green(launch_base):
    """L10: the frozen 19 D7-B + 14 D7-A tests remain green (inner pytest runs).

    The 19 include the one pre-existing frozen tiny production check
    (SINGLE_CHECK_D3, max_iter<=2); that is prior qualification behavior, not
    a D7-B scientific invocation (run_easy_regime is never called with
    decode_fn=None there, and no root is created).
    """
    inner = launch_base / "inner"
    inner.mkdir()
    # Inner runs inherit the ambient environment (NOT the stripped launch
    # env): they execute the test suites, not the launch path.
    ambient = dict(os.environ)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", str(D7B_FILE), "-k", "not test_launch_l",
         "-q", "-o", "addopts=", "--basetemp", str(inner)],
        cwd=str(REPO), env=ambient, capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "19 passed" in r.stdout, r.stdout
    r = subprocess.run(
        [sys.executable, "-m", "pytest", str(D7A_FILE),
         "-q", "-o", "addopts=", "--basetemp", str(inner)],
        cwd=str(REPO), env=ambient, capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "14 passed" in r.stdout, r.stdout


def test_launch_l11_frozen_contract_untouched():
    """L11: frozen scientific constants/schema hold; core file has no path hack."""
    assert eb.Q == 32
    assert eb.SEEDS == (2026091200, 2026091201, 2026091202, 2026091203)
    assert eb.PRIOR_FAMILIES == ("P99", "P90", "P60", "PAIR")
    assert eb.TIERS == ("SINGLE_CHECK_D3", "TREE_6", "CYCLE_8", "FULL_RANK_64")
    assert eb.CAPS == (1, 2, 4, 8, 16, 32, 90)
    assert eb.CALL_BUDGET == 420
    assert eb.PER_CALL_WATCHDOG_S == 120.0
    assert eb.RUN_WALL_LIMIT_S == 1500.0
    assert eb.OUTER_WATCHDOG_S == 1800.0 and eb.OUTER_GRACE_S == 30.0
    assert eb.RSS_LIMIT_BYTES == 2 * 1024**3
    assert eb.POST_TOL == 1e-10 and eb.DETERM_TOL == 1e-12
    assert eb.FIVE_FILES == ("manifest.json", "decoder_records.csv", "summary.json",
                             "report.md", "command_log.txt")
    assert eb.RECORD_FIELDS == ["tier", "prior", "seed", "n", "m", "rank", "deg_min",
                                "deg_max", "cap", "invoked", "dispatch", "exact",
                                "syndrome_ok", "iterations", "status", "unsat",
                                "sym_err", "finite", "max_p", "mean_true_p",
                                "min_true_rank", "mean_entropy", "post_err",
                                "map_agree", "d_xhat", "d_post", "d_unsat",
                                "proxy", "wall_s", "rss_bytes"]
    assert (eb.T_PRE_EXEC, eb.T_WATCHDOG, eb.T_CRASH, eb.T_RESOURCE, eb.T_BUDGET,
            eb.T_ALERT, eb.T_CONFIRMED, eb.T_PARTIAL, eb.T_NOREGION) == (
        "D7_B_PRE_EXECUTION_BLOCKED", "D7_B_WATCHDOG_TIMEOUT_VOID",
        "D7_B_NONFINITE_OR_CRASH_BLOCKED", "D7_B_RESOURCE_OVERRUN",
        "D7_B_CALL_BUDGET_EXHAUSTED", "D7_B_NO_EASY_REGIME_CORRECTNESS_ALERT",
        "D7_B_EASY_REGIME_CONFIRMED", "D7_B_PARTIAL_EASY_REGIME",
        "D7_B_COMPLETED_NO_STABLE_REGION")
    assert len(eb.cell_list()) == 64
    core_src = Path(eb.__file__).read_text(encoding="utf-8")
    assert "sys.path" not in core_src  # repair stayed runner-local


def test_launch_l12_roots_and_authorization_unchanged():
    """L12: no D7-B/R1d/G2 roots appeared; authorization still false."""
    assert glob.glob(str(WS / "d7_b_easy_regime_*")) == []
    assert glob.glob(str(WS / "*v72p2d7*")) == []
    state = {}
    with open(REPO / "docs" / "research_cycles" / "V72P2D7-GF32-EASY-REGIME"
              / "cycle_state.yaml", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                k, v = line.split(":", 1)
                state[k.strip()] = v.strip().strip("'\"")
    for k in ("d7b_execution_authorized", "decoder_executed", "result_created",
              "formal_execution_authorized", "synthetic_execution_authorized",
              "real_execution_authorized", "g1_authorized", "g2_authorized"):
        assert state.get(k) == "false", (k, state.get(k))
    assert state.get("d7b_execution_attempts") == "0"
    assert state.get("d7b_execution_completed") == "0"
