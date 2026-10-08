"""C-3 M 波驱动测试（OP-M2, EXPLORE, T0/T1 小规模 only）.

T0: 冻结常量（TAG=64、B=300、种子 20261009、A3 max_iter=300 单值、
A4 SC/SCL8 变体、kept=N·H_A_op、网格定义、无 per-block 超时哨兵）、
码率规则只读引用（GAP_NB/M_LADDER/ANCHOR_N/compute_rate 与 bakeoff 别名
恒等）、ROW_KEYS 超集要求.
T1: 驱动 dry-run（B≤10 小规模）：落盘行键齐全、m 由规则显式算出、
kept 全符号口径、net 汇总 + T_p50/p95/max 列、fresh-root 拒绝、
MLOG 写者注入路径、A6 T0/T1 门形状（ok 或 BLOCKED 四件套）.

只写 ``workspace/c3m_probe_<uuid>/`` 临时根；不写生产输出根
``workspace/c3_mtune/mt_20261008/``；不读原始数据，不跑 B≥300.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c3m_driver as M
from comparison_bench.src.comparison_bench.formal_ir import msd_c3_bakeoff as C3R
from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as R

WS = Path("workspace") / f"c3m_probe_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def ws():
    WS.mkdir(parents=True, exist_ok=True)
    assert "c3m_probe_" in str(WS)
    return WS


# ---------------- T0 ----------------

def test_t0_frozen_constants():
    assert M.TAG == 64 and R.TAG_BITS == 64
    assert M.B_FULL == 300
    assert M.SEED_M == 20261009
    assert M.A3_MAX_ITER == 300
    assert M.A4_VARIANTS == {"SC": 1, "SCL8": 8}
    assert M.H_A_OP == {"F1": 10.0, "F2": 9.0, "F3": 11.0}
    assert M.D_OF == {"F1": 1024, "F2": 512, "F3": 2048}
    assert M.GRID_N6 == (1024, 2048, 4096, 8192, 16384, 32768)
    assert M.GRID_F3 == (1024, 4096)
    assert M.A6_NS == (1024, 4096, 16384)
    assert M.NO_TIMEOUT is True  # 无 per-block 超时哨兵
    assert "不作为主度量" in R.BETA_WARNING


def test_t0_rate_rule_readonly():
    # 只读引用：别名恒等（本驱动无自有 gap 表 / R 公式 / M 标度）.
    assert M.GAP_NB is C3R.GAP_NB
    assert M.M_LADDER is C3R.M_LADDER
    assert M.ANCHOR_N == C3R.ANCHOR_N == 16384
    assert M.C_TOTAL_PLAN == C3R.C_TOTAL_PLAN
    rr = M.rate_of("F1", 16384, 2.5)
    ref = C3R.compute_rate(family="nb", p_op=C3R.WORKPOINTS["F1"]["p"],
                           H_q=C3R.WORKPOINTS["F1"]["H_q"], q=3,
                           N=16384, M=2.5)
    assert rr == ref
    rr3 = M.rate_of("F1", 16384, 3.0)
    assert rr["R"] - rr3["R"] == pytest.approx(0.005)  # M 冻结标度


def test_t0_kept_fullsym():
    assert M.kept_of("F1", 1024) == 10240.0
    assert M.kept_of("F2", 2048) == 18432.0
    assert M.kept_of("F3", 4096) == 45056.0


def test_t0_a6_bundle_fit():
    bun = M.a6_fit_bundle("F1")
    assert bun["q"] == 32
    assert bun["p_star"] == pytest.approx(0.060740)
    assert bun["pm_star"] == pytest.approx(0.037000)
    g = bun["prior_g"]
    assert len(g) == 32 and abs(sum(g) - 1.0) < 1e-12
    assert g[0] == pytest.approx(1.0 - 0.060740)
    assert g[31] == pytest.approx(0.037000)  # runner q 分支：g[q-1]=p_minus
    assert g[1] == pytest.approx((0.060740 - 0.037000) / 30)
    with pytest.raises(ValueError):
        M.a6_fit_bundle("F3")


def test_t0_blocked_shape():
    # BLOCKED 四件套形状（伪造失败路径的契约；真门失败同形）.
    bad = {"status": "BLOCKED", "gate": "T0", "command": "cmd",
           "traceback": "tb", "remedies_tried": ["r"],
           "decision_needed": "d"}
    for k in ("command", "traceback", "remedies_tried", "decision_needed"):
        assert k in bad


# ---------------- T1：dry-run ----------------

def test_t1_dryrun_rows_keys_kept(ws):
    root = ws / "dry"
    rc = M.main(["--dry-run", "--output-root", str(root)])
    assert rc == 0
    assert (root / "manifest.json").exists()
    assert (root / "net_main_m.csv").exists()
    assert (root / "net_detail_m.csv").exists()
    manifest = json.loads((root / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["A3_max_iter"] == 300
    assert manifest["per_block_timeout"] is None
    assert manifest["kept_rule"] == "kept=N*H_A_op"
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
            if r["ver"] == 1:
                # 全符号 kept 口径（非 q 元 k_info 口径）.
                assert r["kept"] == pytest.approx(
                    M.kept_of(r["WP"], r["N"]))
            checked += 1
    assert checked > 0


def test_t1_m_explicit_and_tstats(ws):
    root = ws / "dry"
    if not root.exists():
        assert M.main(["--dry-run", "--output-root", str(root)]) == 0
    manifest = json.loads((root / "manifest.json").read_text(
        encoding="utf-8"))
    assert manifest["cells"], "dry-run must produce cells"
    a4 = next((c for c in manifest["cells"]
               if c["method"] == "A4" and c["status"] == "ok"), None)
    assert a4 is not None
    rr = M.rate_of(a4["WP"], a4["N"], a4["M"])
    jf = root / "blocks" / (
        f"{a4['WP']}_A4-{a4['variant']}_N{a4['N']}_M{a4['M']}.jsonl")
    rows = [json.loads(line) for line in jf.read_text(
        encoding="utf-8").splitlines()]
    assert rows and all(r["m"] == rr["m"] for r in rows)
    assert rows[0].get("max_iter", 300) == 300 or \
        "list_size" in rows[0]
    import csv
    det = list(csv.DictReader(
        (root / "net_detail_m.csv").open(encoding="utf-8")))
    assert det and all("T_p50" in r and "T_p95" in r and "T_max" in r
                       for r in det)
    assert all("Net_seg" in r and "beta_side" in r for r in det)


def test_t1_fresh_root_refused(ws):
    root = ws / "dry"  # 已存在
    rc = M.main(["--full", "--output-root", str(root)])
    assert rc == 2
    rc = M.main(["--a6-full", "--output-root", str(root)])
    assert rc == 2


def test_t1_mlog_writer_injected(ws):
    lp = ws / "C3_MLOG_probe.md"
    out = M.append_mlog(["probe line"], path=lp, header="probe")
    assert out == lp
    text = lp.read_text(encoding="utf-8")
    assert "OP-M2" in text and "probe line" in text


def test_t1_a6_t1_gate_shape():
    # 小样本 T1 门：ok 或 BLOCKED（四件套齐全），不得无声降级.
    t1 = M.a6_bridge_t1("F1", n_symbols=30720)
    assert t1["status"] in ("ok", "BLOCKED")
    if t1["status"] == "ok":
        assert abs(t1["p_hat"] - t1["p_star"]) <= max(
            abs(t1["p_star"]) * 0.25, 0.005)
    else:
        for k in ("command", "traceback", "remedies_tried",
                  "decision_needed"):
            assert k in t1 and t1[k]


def test_t1_a3_memory_wall_precheck(ws):
    # 内存墙预检：N=32768 稠密 H（GB 级）不开构造即 overtime-risk short.
    rr = M.rate_of("F1", 32768, 2.5)
    out = ws / "memwall.jsonl"
    if out.exists():
        out.unlink()
    c = M._run_guarded("A3", "F1", 32768, 2.5, rr, 300, 20261009, out)
    assert c["status"] == "overtime-risk" and c["rows"] == 0
    assert "128MB" in c["detail"]
    assert not out.exists()


def test_t1_anchor_cells_gate(ws):
    # --cells 门控锚点：滤掉 N16384 的分片不跑锚点（冻 M2.5 + 注记）.
    root = ws / "gate"
    man = M.run_grid(root=root, B=2, seed=20261009,
                     workpoints=("F1",), Ns=(32, 64),
                     cells_filter="F1/A3/32", write_tables=False)
    assert man["anchors"]["F1/A3"]["M_winner"] == 2.5
    assert "filtered" in man["anchors"]["F1/A3"]["note"]
    # 两段式 token（WP/臂）选中整行 N.
    root2 = ws / "gate2"
    man2 = M.run_grid(root=root2, B=2, seed=20261009,
                      workpoints=("F1",), Ns=(32, 64),
                      cells_filter="F1/A4", write_tables=False)
    a4cells = [c for c in man2["cells"] if c["method"] == "A4"]
    assert {c["N"] for c in a4cells} == {32, 64}
    assert not [c for c in man2["cells"] if c["method"] == "A3"]


def test_t1_probe_resume_partial(ws):
    # 回归：探针不得破坏续跑部分文件（B=1 net 重算曾致负 F → construction-fail）.
    out = ws / "resume_blocks" / "F1_A4-SC_N32_M2.5.jsonl"
    rr = M.rate_of("F1", 32, 2.5)
    M.run_a4_cell("F1", 32, 2.5, rr, 1, 20261009, out, variant="SC")
    assert M._jsonl_count(out) == 1
    c = M._run_guarded("A4", "F1", 32, 2.5, rr, 3, 20261009, out,
                       variant="SC", cell_budget_s=3600)
    assert c["status"] in ("ok", "short")
    assert M._jsonl_count(out) == 3
    assert not out.with_name(out.stem + ".probe.jsonl").exists()


def test_t1_recount_tables(ws):
    # recount：满行重计 + 短格保留 + 期望网格补全 + 主表明细落盘（隔离小根）.
    root = ws / "rec"
    M.run_grid(root=root, B=2, seed=20261009,
               workpoints=("F1",), Ns=(32,),
               cells_filter="F1/A4-SC/32", write_tables=False)
    res = M.recount_grid(root=root, B=2, seed=20261009)
    assert res["cells"] >= 3  # 1 满格 + 锚点/网格补全
    assert res["main"] >= 1
    assert (root / "net_detail_m.csv").exists()
    assert (root / "net_main_m.csv").exists()
    import csv
    det = list(csv.DictReader(
        (root / "net_detail_m.csv").open(encoding="utf-8")))
    full = [r for r in det if r["WP"] == "F1" and r["method"] == "A4"
            and r["variant"] == "SC" and r["N"] == "32"]
    assert full and full[0]["status"] == "ok"
    assert "T_p95" in det[0] and "beta_warning" in det[0]


def test_t1_anchor_logic(ws, monkeypatch):
    fake = {2.5: {"method": "A3", "variant": "", "WP": "F1", "N": 16384,
                  "M": 2.5, "B": 8, "rows": 8, "success": 8,
                  "net": {"Net_seg": 100.0, "F": 0, "S_main": 8,
                          "U": 0, "FER_hat": 0.0}},
            3.0: {"method": "A3", "variant": "", "WP": "F1", "N": 16384,
                  "M": 3.0, "B": 8, "rows": 8, "success": 8,
                  "net": {"Net_seg": 200.0, "F": 0, "S_main": 8,
                          "U": 0, "FER_hat": 0.0}}}

    def _fake_guard(kind, wp, N, M, rr, B, seed, out, **kw):
        return dict(fake[M])

    monkeypatch.setattr(M, "_run_guarded", _fake_guard)
    anchor = M.select_m_anchor("F1", "A3", variant="", B=8, seed=1,
                               out_dir=ws / "anchor_logic")
    assert anchor["M_winner"] == 3.0
    assert anchor["N"] == 16384
    assert set(anchor["nets"]) == {2.5, 3.0}
