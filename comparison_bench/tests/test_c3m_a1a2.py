"""OP-M1 验收测试（M-A1-01 / M-A2-01；EXPLORE 合成-only）.

写作用域仅限本文件（+ ``formal_ir/msd_c3m_a1a2.py``）；不碰 OP-M2 文件与
MLOG。机器根写 ``workspace/c3_mtune/mt_a1a2_pytest_<uuid8>/``
（``mt_a1a2_`` 前缀，与 OP-M2 错开）。``pytest -p no:cacheprovider``。
"""

import inspect
import json
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as runner
from comparison_bench.src.comparison_bench.formal_ir import msd_c3m_a1a2 as c3m

ROOT = Path("workspace/c3_mtune") / f"mt_a1a2_pytest_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def workdir():
    ROOT.mkdir(parents=True, exist_ok=True)
    return ROOT


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line.strip()]


# ---------------- M-A1-01：码率只读引用 ----------------

def test_rate_bin_matches_bakeoff_readonly():
    """rate_bin 与 bakeoff.compute_rate 逐值一致（只读引用，不另立公式）；
    M=3.0 相对 M=2.5 退 0.005（冻结标度）。"""
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_c3_bakeoff as bakeoff,
    )
    for wp in ("F1", "F2"):
        spec = bakeoff.WORKPOINTS[wp]
        for N in (1024, 16384):
            for M in (2.5, 3.0):
                ref = bakeoff.compute_rate(
                    family="bin", p_op=float(spec["p"]),
                    H_q=float(spec["H_q"]), q=int(spec["q"]), N=N, M=M)
                got = c3m.rate_bin(wp, N, M)
                assert got == ref
    r25 = c3m.rate_bin("F2", 16384, 2.5)["R"]
    r30 = c3m.rate_bin("F2", 16384, 3.0)["R"]
    assert abs((r25 - r30) - 0.005) < 1e-12


# ---------------- M-A1-01：QC 构造 ----------------

def test_qc_exact_shape_and_determinism():
    """QC 精确 (m×N)、无空行、确定性 hash、列重不规则。"""
    a = c3m.build_qc_code(N=256, m=100)
    b = c3m.build_qc_code(N=256, m=100)
    H = a["H"]
    assert H.shape == (100, 256)
    assert a["code_hash"] == b["code_hash"]
    assert len(a["code_hash"]) == 16
    assert np.all(np.asarray((H != 0).sum(axis=0)).ravel() >= 1)
    assert a["meta"]["col_w_min"] < a["meta"]["col_w_max"]
    assert a["meta"]["fixed_empty_rows"] == 0


# ---------------- M-A1-01：T0 门（冻结几何） ----------------

def test_t0_gate_frozen_geometry():
    """T0（N=1024/B=30/seed=20261009）：F1=13/30、F2=12/30，均过门 0.30；
    F1 R≈0.58 带外仅记录、F2 R≈0.71 带内。"""
    g1 = c3m.t0_gate("F1", 2.5)
    g2 = c3m.t0_gate("F2", 2.5)
    assert g1["pass"] and g1["success"] == 13
    assert g2["pass"] and g2["success"] == 12
    assert abs(g1["R"] - 0.5796) < 1e-3
    assert abs(g2["R"] - 0.7135) < 1e-3
    assert g1["R_in_target_zone"] is False
    assert g2["R_in_target_zone"] is True
    assert len(g1["code_hash"]) == 16


def test_t0_gated_opens_no_matrix(workdir):
    """未过门不开矩阵：零译码、零落盘、status=t0-gated。"""
    out = workdir / "gated.jsonl"
    bad_t0 = c3m.t0_gate("F2", 2.5, B=4, N=256, min_succ_rate=1.01)
    assert not bad_t0["pass"]
    cell = c3m.run_a1_cell("F2", 256, 2.5, 256 * 9.0, 4, c3m.SEED, out,
                           t0_result=bad_t0)
    assert cell["status"] == "t0-gated"
    assert cell["rows"] == 0
    assert not out.exists()


# ---------------- M-A1-01：A1 两级记账 ----------------

def test_a1_two_level_accounting_tiny(workdir):
    """A1 小格：ROW_KEYS+frozen_hash齐全；kept=N·H_A_op（调用方传入）；
    成功块 L_EC=m+L_B（L_B=n_marked），失败块 L_EC=m；
    net 与逐块精确和一致；tag=64/0；口径注记落盘。"""
    out = workdir / "a1_tiny.jsonl"
    t0 = c3m.t0_gate("F2", 2.5)
    assert t0["pass"]
    kept = 128 * 9.0
    cell = c3m.run_a1_cell("F2", 128, 2.5, kept, 5, c3m.SEED, out,
                           t0_result=t0)
    assert cell["status"] == "ok"
    rows = _rows(out)
    assert len(rows) == 5
    for r in rows:
        for k in runner.ROW_KEYS:
            assert k in r
        assert "frozen_hash" in r and len(r["frozen_hash"]) == 16
        assert r["code_hash"] == r["frozen_hash"]
        assert r["u"] == 0 and r["undetected"] is False
        assert r["status"] in runner.ALLOWED_STATUSES
        assert r["T_dec"] >= 0.0
        assert "synthetic-truth" in r["detail"]
        if r["ver"] == 1:
            assert r["kept"] == kept
            assert r["tag"] == 64
            assert r["L_EC"] == r["m"] + r["n_marked"] == r["L_A"] + r["L_B"]
            assert r["L_B"] == r["n_marked"]
        else:
            assert r["kept"] == 0.0 and r["tag"] == 0
            assert r["L_EC"] == r["m"] and r["L_B"] == 0
    net = cell["net"]
    assert net is not None
    exact = sum((r["kept"] - r["L_EC"] - r["tag"] if r["ver"] == 1
                 else -r["L_EC"]) for r in rows)
    assert abs(exact - net["Net_seg"]) < 1e-9 * max(1.0, abs(exact))
    assert cell["success"] == sum(r["ver"] for r in rows)


# ---------------- M-A2-01：冻结集重算 + hash ----------------

def test_a2_frozen_recomputed_per_p_op():
    """冻结集按 p_op 重算：确定性、划分有效、16hex hash；F1/F2 hash 不同；
    开门检查 ok（含 K/m/R）。"""
    f1, i1 = c3m.bhattacharyya_frozen_set(64, 40, 0.060740)
    f1b, _ = c3m.bhattacharyya_frozen_set(64, 40, 0.060740)
    assert f1 == f1b
    assert sorted(f1 + i1) == list(range(64))
    assert len(f1) == 24 and len(i1) == 40
    c1 = c3m.polar_construction_check("F1", 1024, 2.5)
    c2 = c3m.polar_construction_check("F2", 1024, 2.5)
    assert c1["ok"] and c2["ok"]
    assert len(c1["frozen_hash"]) == 16
    assert c1["frozen_hash"] != c2["frozen_hash"]
    assert c1["code_hash"] == c1["frozen_hash"]


def test_sc_matches_scl1_oracle_and_encode_roundtrip():
    """本地 SC 与 sibling scl(L=1) 比特一致（20 随机帧）；本地编码与
    sibling 编码一致（SC 变体自持依据）。"""
    import sys
    sys.path.insert(0, runner.SIBLING_ROOT)
    import low_dim_opt.core.polar_core as P
    rng = np.random.default_rng(20261009)
    N, n_log, K = 64, 6, 40
    frozen, info = c3m.bhattacharyya_frozen_set(N, K, 0.06)
    mask = np.zeros(N, dtype=np.uint8)
    mask[np.asarray(info, dtype=np.int64)] = 1
    for t in range(20):
        llr = rng.normal(0, 2, N)
        fv = np.zeros(N, dtype=np.uint8)
        fv[list(frozen)] = rng.integers(0, 2, len(frozen)).astype(np.uint8)
        mine = c3m.sc_decode_nb(llr, mask, fv, n_log)
        ref = np.asarray(P.scl_decode_batch(
            llr.reshape(1, -1), mask, fv.reshape(1, -1), n_log, 1)[0])
        assert np.array_equal(mine, ref), f"SC!=SCL1 at trial {t}"
    u = rng.integers(0, 2, N).astype(np.int8)
    assert np.array_equal(c3m._polar_encode_local(u, n_log),
                          np.asarray(P.polar_encode(u, n_log)))


def test_a2_sc_cell_tiny(workdir):
    """A2-SC 小格：跑到 verdict，行键齐全，两级记账同 A1 口径。"""
    out = workdir / "a2sc_tiny.jsonl"
    kept = 64 * 9.0
    cell = c3m.run_a2_cell("F2", 64, 2.5, "SC", kept, 3, c3m.SEED, out)
    assert cell["status"] == "ok"
    assert cell["variant"] == "SC"
    rows = _rows(out)
    assert len(rows) == 3
    for r in rows:
        for k in runner.ROW_KEYS:
            assert k in r
        assert r["variant"] == "SC"
        assert len(r["frozen_hash"]) == 16
        if r["ver"] == 1:
            assert r["kept"] == kept and r["tag"] == 64
            assert r["L_EC"] == r["L_A"] + r["L_B"]
        else:
            assert r["L_EC"] == r["L_A"] and r["L_B"] == 0


def test_a2_scl8_cell_tiny_or_unavailable(workdir):
    """A2-SCL8 小格：sibling 存在则 verdict 行，无则 unavailable 透传
    （不断言失败；记录实际分支）。"""
    out = workdir / "a2scl8_tiny.jsonl"
    cell = c3m.run_a2_cell("F2", 64, 2.5, "SCL8", 64 * 9.0, 3,
                           c3m.SEED, out)
    rows = _rows(out)
    assert len(rows) == 3
    if cell["status"] == "unavailable":
        assert all(r["status"] == "unavailable" for r in rows)
    else:
        assert cell["status"] == "ok"
        assert all(r["variant"] == "SCL8" for r in rows)
        for k in runner.ROW_KEYS:
            assert all(k in r for r in rows)


# ---------------- F3 / 无超时 / 根目录 ----------------

def test_f3_binary_infeasible_by_construction(workdir):
    """F3 二进制两级：infeasible-by-construction，不跑、零行、原因含 R<0。"""
    rec = c3m.f3_binary_infeasible(N=1024)
    assert rec["status"] == "infeasible-by-construction"
    assert rec["rows"] == 0 and rec["net"] is None
    assert rec["R"] < 0
    assert "not missing" in rec["detail"]
    assert not (workdir / "f3.jsonl").exists()


def test_no_per_block_timeout_anywhere():
    """无 per-block 超时：全部译码/执行签名无 timeout/budget/deadline 参数；
    小格逐块均有 verdict + T_dec。"""
    fns = [c3m.run_a1_cell, c3m.run_a2_cell, c3m.run_cell_parallel,
           c3m.t0_gate,
           c3m._bp_decode_block, c3m._a2_decode_sc, c3m._a2_decode_scl8,
           c3m._a1_block, c3m._a2_block,
           c3m.select_M_anchor_m, c3m.run_grid_m]
    for fn in fns:
        params = set(inspect.signature(fn).parameters)
        assert not {p for p in params
                    if any(s in p.lower()
                           for s in ("timeout", "budget", "deadline"))}, \
            fn.__name__


def test_default_root_prefix_convention():
    """机器根为 mt_a1a2_ 前缀（与 OP-M2 错开；不含 OP-M2 的 mt_20261008）。"""
    root = c3m.default_root()
    assert root.parent.name == "c3_mtune"
    assert root.name.startswith("mt_a1a2_")
    assert root.name != "mt_20261008"


def test_anchor_tiny_selects_winner(workdir, monkeypatch):
    """M 锚点映射（tiny 代理）：N=anchor 两 M 实跑，winner 按 Net_seg，
    tie/未定→M2.5；其余 N 用 winner（由 run_grid_m 保证，此处验锚点）。"""
    monkeypatch.setattr(c3m, "ANCHOR_N", 256)
    anchor = c3m.select_M_anchor_m("F2", "A1", B=4, seed=c3m.SEED,
                                   out_dir=workdir / "anchor")
    assert anchor["M_winner"] in (2.5, 3.0)
    assert set(anchor["cells"]) == {2.5, 3.0}
    nets = anchor["nets"]
    assert set(nets) == {2.5, 3.0}


def test_sanitize_drops_torn_tail(workdir):
    """自愈：torn 尾行被丢弃，好行块号集正确返回。"""
    p = workdir / "torn.jsonl"
    p.write_text('{"block": 0, "ver": 1}\n{"block": 1, "ver": 0}\n'
                 '{"block": 2, "ver": 1, BROKEN\n',
                 encoding="utf-8")
    present = c3m._sanitize_blocks(p)
    assert present == {0, 1}
    assert len(_rows(p)) == 2


def _norm(rows):
    return [{k: v for k, v in sorted(r.items()) if k != "T_dec"}
            for r in sorted(rows, key=lambda r: r["block"])]


def test_parallel_matches_serial_a1(workdir):
    """并行分片与串行行一致（A1 tiny，2 workers；除 T_dec 外逐键相等）。"""
    t0 = c3m.t0_gate("F2", 2.5)
    kept = 128 * 9.0
    s_out = workdir / "par_s.jsonl"
    p_out = workdir / "par_p.jsonl"
    c3m.run_a1_cell("F2", 128, 2.5, kept, 6, c3m.SEED, s_out,
                    t0_result=t0)
    cell = c3m.run_cell_parallel("A1", "QC-BP", "F2", 128, 2.5, kept, 6,
                                 c3m.SEED, p_out, workers=2,
                                 t0_cache={("F2", 2.5): t0})
    assert cell["status"] == "ok"
    assert _norm(_rows(p_out)) == _norm(_rows(s_out))


def test_parallel_matches_serial_a2sc(workdir):
    """并行分片与串行行一致（A2-SC tiny，2 workers）。"""
    kept = 64 * 9.0
    s_out = workdir / "par2_s.jsonl"
    p_out = workdir / "par2_p.jsonl"
    c3m.run_a2_cell("F2", 64, 2.5, "SC", kept, 4, c3m.SEED, s_out)
    cell = c3m.run_cell_parallel("A2", "SC", "F2", 64, 2.5, kept, 4,
                                 c3m.SEED, p_out, workers=2)
    assert cell["status"] == "ok"
    assert _norm(_rows(p_out)) == _norm(_rows(s_out))


def test_manifest_from_blocks_no_decode(workdir):
    """终态盘点只汇总不补算：满格 ok + 缺格 short。"""
    root = workdir / "recount"
    blocks = root / "blocks"
    t0 = c3m.t0_gate("F2", 2.5)
    kept = 128 * 9.0
    c3m.run_a1_cell("F2", 128, 2.5, kept, 5, c3m.SEED,
                    blocks / "F2_A1_N128_M2.5.jsonl", t0_result=t0)
    c3m.run_a2_cell("F2", 64, 2.5, "SC", 64 * 9.0, 3, c3m.SEED,
                    blocks / "F2_A2-SC_N64_M2.5.jsonl")
    manifest = c3m.manifest_from_blocks(root, B=5, seed=c3m.SEED)
    by_name = {c["N"]: c for c in manifest["cells"]}
    assert by_name[128]["status"] == "ok" and by_name[128]["rows"] == 5
    assert by_name[64]["status"] == "short" and by_name[64]["rows"] == 3
    assert (root / "cells.json").exists()


def test_manifest_anchor_recompute_filters_anchor_N(workdir):
    """锚点复算只看 anchor_N 双 M 满格（他 N 同名文件不得混入；未定→M2.5）。"""
    import json as _json
    root = workdir / "anchor2"
    blocks = root / "blocks"
    blocks.mkdir(parents=True, exist_ok=True)

    def _row(b, ver, lec, kept):
        return {"method": "A1", "N": 256, "block": b, "ver": ver, "u": 0,
                "kept": kept if ver else 0.0, "L_EC": lec,
                "tag": 64 if ver else 0, "T_dec": 0.01,
                "code_hash": "h", "frozen_hash": "h", "undetected": False,
                "status": "ok" if ver else "decode_failed",
                "WP": "F2", "M": 2.5, "seed": 1, "R": 0.7, "m": 70,
                "K": 186, "L_A": 70, "L_B": 0, "n_marked": 0}

    for M in (2.5, 3.0):
        with open(blocks / f"F2_A1_N256_M{M}.jsonl", "w",
                  encoding="utf-8") as fh:
            for b in range(4):
                r = _row(b, 1 if b < 3 else 0, 70, 2304.0)
                r["M"] = M
                fh.write(_json.dumps(r) + "\n")
    # 干扰文件：同族他 N 的 M3.0（不得参与锚点判定）。
    with open(blocks / "F2_A1_N128_M3.0.jsonl", "w",
              encoding="utf-8") as fh:
        for b in range(4):
            fh.write(_json.dumps(_row(b, 1, 70, 1152.0)) + "\n")
    manifest = c3m.manifest_from_blocks(root, B=4, seed=1, anchor_N=256)
    assert set(manifest["anchors"]) == {"F2/A1/QC-BP"}
    anc = manifest["anchors"]["F2/A1/QC-BP"]
    assert anc["M_winner"] == 2.5
    assert anc["note"] == "both-undecided→freeze-M2.5"
