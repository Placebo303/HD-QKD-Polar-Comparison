"""C-3 bakeoff tests (EXPLORE, T0/T1 small only).

T0: 常量/码率数学（TAG=64、N 网格、gap 表、M 阶梯、锚点 N、未定阈值、
infeasible、M→R 冻结标度）、信道规范字面值（F1/F2/F3，F3 exploratory）、
ROW_KEYS 超集要求。
T1: 驱动 dry-run（B≤10 小规模）：落盘行键齐全、m 由规则显式算出、
net 汇总存在、方向冒烟 T2-1M δ*=-50 通过、fresh-root 拒绝、mapped/A7 分表。

只写 ``workspace/c3_probe_<uuid>/`` 临时根；不写生产输出根；
不读原始数据，不跑 B≥300。
"""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c3_bakeoff as C3
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as R

WS = Path("workspace") / f"c3_probe_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def ws():
    WS.mkdir(parents=True, exist_ok=True)
    assert "c3_probe_" in str(WS)
    return WS


# ---------------- T0 ----------------

def test_t0_frozen_constants():
    assert C3.TAG == 64 and R.TAG_BITS == 64
    assert C3.N_GRID == (1024, 2048, 4096, 8192, 16384, 32768, 65536)
    assert C3.GAP_BIN[16384] == 0.03 and C3.GAP_NB[16384] == 0.05
    assert C3.MARGIN_B == 0.01
    assert C3.M_LADDER == (2.5, 3.0)
    assert C3.ANCHOR_N == 16384
    assert C3.B_FULL == 300
    assert C3.FRESH_METHODS == ("A1", "A2", "A3", "A4")
    assert "不作为主度量" in C3.BETA_WARNING


def test_t0_channel_specs_literal():
    f1, f2, f3 = C3.WORKPOINTS["F1"], C3.WORKPOINTS["F2"], C3.WORKPOINTS["F3"]
    assert (f1["p"], f1["p_minus"], f1["rest"]) == (0.060740, 0.037000, 1.3e-05)
    assert (f2["p"], f2["p_minus"], f2["rest"]) == (0.030413, 0.018564, 0.0)
    assert f1["tag"] == "calibrated" and f2["tag"] == "calibrated"
    assert f3["tag"] == "exploratory" and f3["q"] == 5 and f3["k"] == 2
    assert abs(f1["p"] * 0.609160 - 0.037000) < 1e-6  # LAUNCH §2 三值关系
    assert abs(f2["p"] * 0.610378 - 0.018564) < 1e-6


def test_t0_rate_rule_exact():
    # 二进制臂 F1 N=16384 M=2.5：R = 1−h2(0.06074)−0.03−0.01。
    rr = C3.compute_rate(family="bin", p_op=0.060740, H_q=0.0, q=2,
                         N=16384, M=2.5)
    assert rr["R"] == pytest.approx(1.0 - C3.h2(0.060740) - 0.03 - 0.01)
    assert rr["K"] + rr["m"] == 16384 and rr["feasible"]
    # M 冻结标度：M=3.0 比 M=2.5 多退 0.005。
    rr3 = C3.compute_rate(family="bin", p_op=0.060740, H_q=0.0, q=2,
                          N=16384, M=3.0)
    assert rr["R"] - rr3["R"] == pytest.approx(0.005)
    # 高维臂用 H_sym/log2(q)。
    rnb = C3.compute_rate(family="nb", p_op=0.060740,
                          H_q=C3.WORKPOINTS["F1"]["H_q"], q=3,
                          N=16384, M=2.5)
    assert rnb["R"] == pytest.approx(
        1.0 - C3.WORKPOINTS["F1"]["H_q"] / 1.584962500721156 - 0.05 - 0.01,
        rel=1e-9)
    # 不可行：p=0.5 时 h2=1，R<0 → K<1。
    bad = C3.compute_rate(family="bin", p_op=0.5, H_q=0.0, q=2,
                          N=1024, M=3.0)
    assert not bad["feasible"] and "infeasible" in bad["reason"]
    with pytest.raises(ValueError):
        C3.compute_rate(family="ZZ", p_op=0.1, H_q=0.1, q=3,
                        N=1024, M=2.5)


def test_t0_direction_smoke_passes():
    # T2-1M δ*=−50：正确符号侧必须优于错误符号代理，否则全停。
    res = C3.direction_smoke()
    assert res["pass"] is True
    assert res["delta_star"] == -50 and res["source"] == "T2-1M"
    assert res["p_ok"] < res["p_bad"]
    assert res["net_ok"] > res["net_bad"]


def test_t0_anchor_selection_logic(ws, monkeypatch):
    # M 锚点二选一逻辑（fake cells，不跑译码）：按 Net_seg 选，冻结记录完整。
    fake = {2.5: {"method": "A4", "WP": "F1", "N": 16384, "M": 2.5,
                  "B": 8, "rows": 8, "success": 8,
                  "net": {"Net_seg": 100.0, "F": 0, "S_main": 8,
                          "U": 0, "FER_hat": 0.0}},
            3.0: {"method": "A4", "WP": "F1", "N": 16384, "M": 3.0,
                  "B": 8, "rows": 8, "success": 8,
                  "net": {"Net_seg": 200.0, "F": 0, "S_main": 8,
                          "U": 0, "FER_hat": 0.0}}}

    def _fake_guard(wp, method, N, M, **kw):
        return dict(fake[M])

    monkeypatch.setattr(C3, "_run_cell_guarded", _fake_guard)
    anchor = C3.select_M_anchor("F1", "A4", B=8, seed=1,
                                out_dir=ws / "anchor_logic")
    assert anchor["M_winner"] == 3.0
    assert anchor["N"] == 16384
    assert set(anchor["nets"]) == {2.5, 3.0}


# ---------------- T1：dry-run ----------------

def test_t1_dryrun_b8_rows_and_keys(ws):
    root = ws / "dry"
    rc = C3.main(["--dry-run", "--output-root", str(root)])
    assert rc == 0
    assert (root / "manifest.json").exists()
    assert (root / "net_main_fresh.csv").exists()
    assert (root / "net_detail_fresh.csv").exists()
    assert (root / "a7_column.csv").exists()  # A7 unavailable 列位
    assert (root / "mapped_NOTE.txt").exists()  # fresh/mapped 分表注记
    manifest = json.loads((root / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["direction_smoke"]["pass"] is True
    for cell in manifest["cells"]:
        if cell.get("status") in ("infeasible",) or cell.get("rows", 0) == 0:
            continue
        assert cell["B"] <= 10
    # 逐块落盘：ROW_KEYS 超集 + code_hash/frozen_hash + TAG=64。
    checked = 0
    for jf in sorted((root / "blocks").glob("*.jsonl")):
        rows = [json.loads(line) for line in jf.read_text(
            encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) <= 10
        for r in rows:
            for k in R.ROW_KEYS:
                assert k in r, f"{jf.name} missing {k}"
            assert r["frozen_hash"] and r["code_hash"]
            assert r["tag"] in (0, 64)
            assert r["status"] in R.ALLOWED_STATUSES
            checked += 1
    assert checked > 0


def test_t1_m_explicit_and_net_summary(ws):
    root = ws / "dry"
    if not root.exists():  # 允许单独 -k 运行本用例
        assert C3.main(["--dry-run", "--output-root", str(root)]) == 0
    manifest = json.loads((root / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["cells"], "dry-run must produce cells"
    for cell in manifest["cells"]:
        if cell.get("status") != "ok" or not cell.get("decided", False):
            continue
    # m 由规则显式算出：抽查 A4 行的 m == compute_rate 的 m。
    a4 = next((c for c in manifest["cells"]
               if c["method"] == "A4" and c["status"] == "ok"), None)
    assert a4 is not None
    ri = C3.rate_inputs(a4["WP"])
    rr = C3.compute_rate(family="nb", p_op=ri["p_op"], H_q=ri["H_q"],
                         q=ri["q"], N=a4["N"], M=a4["M"])
    assert a4["M"] == 2.5  # dry 网格锚点跳过，冻结 M2.5 并注记
    jf = root / "blocks" / f"{a4['WP']}_A4_N{a4['N']}_M{a4['M']}.jsonl"
    rows = [json.loads(line) for line in jf.read_text(
        encoding="utf-8").splitlines()]
    assert rows and all(r["m"] == rr["m"] for r in rows)
    # net 汇总存在（含 beta 附带列）。
    det = list(csv.DictReader(
        (root / "net_detail_fresh.csv").open(encoding="utf-8")))
    assert det and all("Net_seg" in r and "beta_side" in r for r in det)
    main = list(csv.DictReader(
        (root / "net_main_fresh.csv").open(encoding="utf-8")))
    assert main and all("N_opt" in r and "f_same_time" in r for r in main)


def test_t1_fresh_root_refused(ws):
    root = ws / "dry"  # 已存在
    rc = C3.main(["--full", "--output-root", str(root)])
    assert rc == 2  # fresh-root 纪律：执行前须不存在


def test_t1_a5_wrap_does_not_raise(ws):
    out = ws / "a5_probe.jsonl"
    res = C3._run_a5_cell("F1", 32, 2.5, 2, 7, out)
    assert res["method"] == "A5" and res["B"] == 2
    assert res["status"] in ("ok", "unavailable", "decode_failed",
                             "overtime-risk", "short")
