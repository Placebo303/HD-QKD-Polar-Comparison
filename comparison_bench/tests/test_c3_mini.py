"""T0/T1 for msd_c3_mini (synthetic only, no raw data, no production roots)."""

import json
import math

import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c3_mini as M


def test_m_table_matches_launch():
    # C3_LAUNCH §5 independent table (exact cross-check of the frozen rule).
    q, g, H, _ = M.family_prior("F1")
    assert q == 3 and H == pytest.approx(0.38901, abs=1e-4)
    assert M.m_for(1024, q, H) == 364
    assert M.m_for(16384, q, H) == 5005
    q2, g2, H2, _ = M.family_prior("F2")
    assert H2 == pytest.approx(0.22579, abs=1e-4)
    # nb m from table: F2 N=1024 -> 259
    assert math.ceil(1024 * (H2 / math.log2(q2) + 0.10 + 0.01)) == 259


def test_f3_prior_sane():
    q, g, H, note = M.family_prior("F3")
    assert q == 5 and len(g) == 5
    assert 0.0 < sum(g) <= 1.0
    assert g[0] > 0.5  # peaked at zero error
    assert H > 0.0


def test_a3_tiny_run(tmp_path):
    q, g, H, _ = M.family_prior("F1")
    p = tmp_path / "a3.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        r = M.run_a3(64, q, g, 32, 3, 11, fh)
    assert r["success"] >= 0
    rows = [json.loads(x) for x in open(p, encoding="utf-8")]
    assert len(rows) == 3
    assert set(rows[0]) >= {"method", "N", "block", "ver", "u", "kept",
                            "L_EC", "tag", "T_dec", "code_hash",
                            "undetected", "status"}


def test_merge_single_writer(tmp_path):
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.formal_ir.msd_c3_mini",
         "--full", "--output-root", str(tmp_path / "mini"),
         "--families", "F1", "--methods", "A3,A4",
         "--N-list", "1024", "--B", "3", "--seed", "7"],
        capture_output=True, text=True, cwd=".")
    assert r.returncode == 0, r.stderr[-2000:]
    rows = [json.loads(x) for x in
            open(tmp_path / "mini" / "mini_rows.jsonl", encoding="utf-8")
            if x.strip()]
    assert len(rows) == 6
    assert sorted(x["method"] for x in rows) == ["A3"] * 3 + ["A4"] * 3


def test_net_per_coin_denominator(tmp_path):
    """R16 denominator guard: Net_per_coin == Net_seg / C_total (C-3 WATCH)."""
    import subprocess, sys, json as J
    r = subprocess.run(
        [sys.executable, "-m",
         "comparison_bench.src.comparison_bench.formal_ir.msd_c3_mini",
         "--full", "--output-root", str(tmp_path / "den"),
         "--families", "F1", "--methods", "A4",
         "--N-list", "1024", "--B", "3", "--seed", "7"],
        capture_output=True, text=True, cwd=".")
    assert r.returncode == 0, r.stderr[-2000:]
    d = J.load(open(tmp_path / "den" / "mini_summary.json", encoding="utf-8"))
    net = d["cells"][0]
    assert net["Net_per_coin"] == \
        net["Net_seg"] / 5_000_000.0


def test_a4_tiny_run(tmp_path):
    from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as RU
    q, g, H, _ = M.family_prior("F2")
    m = 40
    s = RU.run_cell("A4", 64, {"q": q, "p": 1.0 - g[0],
                               "p_minus": g[q - 1], "m": m},
                    3, 11, str(tmp_path / "a4.jsonl"))
    assert s["rows"] == 3 and "net" in s
