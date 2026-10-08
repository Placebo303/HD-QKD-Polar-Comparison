"""C1-RUN-01 / C1-ADAPT-01（OP2 scope）.

- ``net_of_cell`` 覆盖成功/失败/undetected/尾部四分支（纯函数精确断言）。
- runner 在合成信道 B=10 跑通并落盘 JSONL 行键齐全。
- A1/A2/A5/A6/A7 适配行；A7 缺失 ``unavailable`` 透传锁定。
- 不读 D:/Data，不跑 B≥300；临时文件只写 ``workspace/c1_op2_<uuid>/``。
"""

from __future__ import annotations

import json
import math
import sys
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as R

WS = Path("workspace") / f"c1_op2_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def ws():
    WS.mkdir(parents=True, exist_ok=True)
    assert "c1_op2_" in str(WS)
    return WS


# ---------------- net_of_cell 四分支 ----------------

def _base_kwargs(**over):
    kw = dict(kept_bits=200.0, L_EC_bits=40.0, tag_bits=64,
              n_fail=0, n_blocks=10, C_total=640.0, N=64)
    kw.update(over)
    return kw


def test_net_success_branch_exact():
    # S=10：Net = 10*(200−40−64) = 960；L_total = 400+640 = 1040。
    r = R.net_of_cell(**_base_kwargs())
    assert r["S_main"] == 10 and r["F"] == 0 and r["U"] == 0
    assert r["Net_seg"] == pytest.approx(960.0)
    assert r["L_total"] == pytest.approx(1040.0)
    assert r["w_tail"] == pytest.approx(0.0)
    assert r["FER_hat"] == pytest.approx(0.0)
    assert r["Net_per_coin"] == pytest.approx(960.0 / 640.0)
    assert r["Net_per_used"] == pytest.approx(960.0 / 640.0)


def test_net_failure_branch_exact():
    # F=3：S=7，Net = 7*96 − 3*40 = 552；FER=0.3；Wilson 上界 ≥ 点估计。
    r = R.net_of_cell(**_base_kwargs(n_fail=3))
    assert r["Net_seg"] == pytest.approx(552.0)
    assert r["FER_hat"] == pytest.approx(0.3)
    assert 0.3 <= r["FER_wilson_hi"] <= 1.0
    assert r["net_seg_wilson_hi"] <= r["Net_seg"]


def test_net_undetected_isolated():
    # F=1,U=2：S=7，Net = 7*96 − 1*40 = 632（U 项为 0，不惩罚不奖励）；
    # U 不计入 F，U_rate 独立列。
    r = R.net_of_cell(**_base_kwargs(n_fail=1, n_undetected=2))
    assert r["S_main"] == 7
    assert r["Net_seg"] == pytest.approx(632.0)
    assert r["FER_hat"] == pytest.approx(0.1)
    assert r["U_rate"] == pytest.approx(0.2)


def test_net_tail_branch():
    r = R.net_of_cell(**_base_kwargs(C_total=1000.0))
    assert r["C_tail"] == pytest.approx(360.0)
    assert r["w_tail"] == pytest.approx(0.36)
    assert r["Net_per_coin"] < r["Net_per_used"]
    assert r["Net_per_coin"] == pytest.approx(r["Net_seg"] / 1000.0)


def test_net_f_beta_and_validation():
    r = R.net_of_cell(**_base_kwargs(h_op=0.5, I_op=1.0))
    assert r["f_full"] == pytest.approx(1040.0 / (10 * 64 * 0.5))
    assert r["f_noTAG"] == pytest.approx(400.0 / (10 * 64 * 0.5))
    assert r["beta_side"] == pytest.approx(960.0 / 640.0)
    assert "不作为主度量" in (r["beta_warning"] or "")
    with pytest.raises(ValueError):
        R.net_of_cell(**_base_kwargs(n_fail=9, n_undetected=2))  # F+U>B
    with pytest.raises(ValueError):
        R.net_of_cell(**_base_kwargs(C_total=100.0))  # C_total < B*N
    assert R.wilson_upper(10, 10) == pytest.approx(1.0)
    assert 0.0 < R.wilson_upper(0, 10) < 0.5
    assert R.wilson_upper(0, 0) == 1.0


# ---------------- runner B=10 ----------------

def test_run_cell_a4_b10_jsonl(ws):
    out = ws / "blocks_a4.jsonl"
    ch = {"k": 1, "p": 0.05, "p_minus": 0.025}
    s = R.run_cell("A4", 64, ch, 10, 20261008, out)
    assert s["success"] >= 1  # T1：成功块非零
    assert s["undetected"] == 0
    assert "net" in s and s["net"]["B"] == 10
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 10
    for r in rows:
        for k in R.ROW_KEYS:
            assert k in r, f"missing row key {k}"
        assert "undetected" in r and r["undetected"] is False
        assert r["status"] in R.ALLOWED_STATUSES
        assert r["u"] == 0
    assert sum(r["ver"] for r in rows) == s["success"]


def test_run_cell_refuses_decide_rerun():
    with pytest.raises(ValueError):
        R.run_cell("A1", 64, {"k": 1, "p": 0.05}, 2, 0, "ws_never.jsonl")
    with pytest.raises(ValueError):
        R.run_cell("A5", 64, {"k": 1, "p": 0.05}, 2, 0, "ws_never.jsonl")
    with pytest.raises(ValueError):
        R.run_cell("ZZ", 64, {"k": 1, "p": 0.05}, 2, 0, "ws_never.jsonl")


def test_run_cell_a3_missing_passthrough(ws, monkeypatch):
    # A3 模块缺失（OP1 未交付时）→ unavailable 行透传，不断言失败。
    monkeypatch.setitem(sys.modules,
                        "comparison_bench.src.comparison_bench.formal_ir.msd_c1_nbldpc",
                        None)
    out = ws / "blocks_a3.jsonl"
    s = R.run_cell("A3", 64, {"k": 1, "p": 0.05}, 4, 0, out)
    assert s["status"] == "unavailable"
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 4 and all(r["status"] == "unavailable" for r in rows)
    assert all(r["ver"] == 0 and r["u"] == 0 for r in rows)


def test_run_cell_a7_row_keys(ws):
    out = ws / "blocks_a7.jsonl"
    s = R.run_cell("A7", 64, {"k": 1, "p": 0.05}, 3, 0, out)
    assert s["status"] in ("unavailable", "stub")
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    for r in rows:
        for k in R.ROW_KEYS:
            assert k in r


# ---------------- C1-ADAPT-01 ----------------

def test_adapt_g5_a1_branches():
    base = dict(block=3, a_ok=True, L_A=100, L_B=50, extra=0)
    r_ok = R.adapt_g5_block({**base, "exact_full": True, "undetected": False},
                            method="A1", N=1024, kept_bits=500.0)
    assert (r_ok["ver"], r_ok["u"], r_ok["status"]) == (1, 0, "ok")
    assert r_ok["kept"] == 500.0 and r_ok["L_EC"] == 150 and r_ok["tag"] == 64
    assert r_ok["undetected"] is False
    r_fail = R.adapt_g5_block({**base, "a_ok": False, "exact_full": False,
                               "undetected": False, "extra": 64},
                              method="A1", N=1024, kept_bits=500.0)
    assert (r_fail["ver"], r_fail["status"], r_fail["kept"]) == (0, "decode_failed", 0.0)
    assert r_fail["L_EC"] == 214
    r_und = R.adapt_g5_block({**base, "exact_full": False, "undetected": True},
                             method="A1", N=1024, kept_bits=500.0)
    assert r_und["ver"] == 1 and r_und["u"] == 1 and r_und["undetected"] is True
    assert r_und["kept"] == 0.0  # undetected 永隔离
    r_a2 = R.adapt_g5_block({**base, "exact_full": True, "undetected": False},
                            method="A2", N=1024, kept_bits=500.0)
    assert r_a2["method"] == "A2" and r_a2["status"] == "ok"
    with pytest.raises(ValueError):
        R.adapt_g5_block({**base, "exact_full": True}, method="A5",
                         N=1024, kept_bits=1.0)


def test_adapt_a5_status_never_upgrades():
    res = {"dataset_id": "synth", "method_status": "ok", "frame_results": [
        {"frame_idx": 0, "decode_success": True, "verify_success": True,
         "syndrome_bits_frame": 40, "verification_bits_frame": 32,
         "frame_len_symbols": 64, "frame_len_bits": 128, "runtime_ms": 5.0},
        {"frame_idx": 1, "decode_success": False, "verify_success": False,
         "syndrome_bits_frame": 40, "verification_bits_frame": 32,
         "frame_len_symbols": 64, "frame_len_bits": 128, "runtime_ms": 5.0},
    ]}
    rows = R.adapt_layered_lite_result(res)
    assert [r["status"] for r in rows] == ["ok", "decode_failed"]
    assert rows[0]["ver"] == 1 and rows[0]["kept"] == 128.0
    assert all(r["u"] == 0 and r["undetected"] is False for r in rows)
    bad = dict(res, method_status="experimental_failed")
    rows_bad = R.adapt_layered_lite_result(bad)
    assert all(r["status"] != "ok" for r in rows_bad)  # 永不把非 ok 转 ok
    unav = dict(res, method_status="unavailable")
    assert all(r["status"] == "unavailable"
               for r in R.adapt_layered_lite_result(unav))


def test_adapt_m4_branches():
    base = dict(source="T2-1M", N=1024, block=0, m_total=100, L_EC=500)
    r_ok = R.adapt_m4_block({**base, "exact_ok": True, "undetected": False},
                            kept_bits=900.0)
    assert (r_ok["ver"], r_ok["u"], r_ok["status"]) == (1, 0, "ok")
    assert r_ok["kept"] == 900.0
    r_und = R.adapt_m4_block({**base, "exact_ok": False, "undetected": True},
                             kept_bits=900.0)
    assert (r_und["ver"], r_und["u"]) == (1, 1) and r_und["kept"] == 0.0
    r_fail = R.adapt_m4_block({**base, "exact_ok": False, "undetected": False},
                              kept_bits=900.0)
    assert (r_fail["ver"], r_fail["status"]) == (0, "decode_failed")
    r_over = R.adapt_m4_block({**base, "exact_ok": True, "undetected": False,
                               "overrun": True}, kept_bits=900.0)
    assert (r_over["ver"], r_over["status"]) == (0, "decode_failed")


def test_adapt_a7_unavailable_passthrough():
    r = R.adapt_a7_row(N=64, block=0, available=False)
    assert r["status"] == "unavailable" and r["ver"] == 0 and r["u"] == 0
    for k in R.ROW_KEYS:
        assert k in r
    r2 = R.adapt_a7_row(N=64, block=1, available=True)
    assert r2["status"] == "stub"
    st = R.sibling_polar_core_available()
    assert isinstance(st.get("available"), bool)
    r3 = R.adapt_a7_row(N=64, block=2)  # 真实 sibling 状态分支（不断言具体值）
    assert r3["status"] in R.ALLOWED_STATUSES
