"""Fallback-only tests for the numpy min-sum SPA backend (route A, synthetic tiny).

FAKE-ONLY: every H/vector/bundle here is synthetic and in-test; ``ldpc``
absence is mocked explicitly via ``find_spec_fn`` (env-independent); direct
backend calls write nothing; the single ``execute()`` probe uses a fake
bundle + fake construct + ``max_blocks`` with its root under pytest tmp_path.
Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>

对照表 (真体 vs numpy fallback; 与 wrapper docstring + docs 附录
``docs/research_cycles/M2-LAYEREDBIN-SYNTH/
APPENDIX_SPA_NUMPY_FALLBACK_COMPARISON.md`` 三处一致, 以本表为准):

| 维度 | 真体 ldpc.BpOsdDecoder (缺席即 STOP-BLOCKED, 永不替代) | numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder) |
| 泄漏 leak_ec_bits / blind_stage_bits | matched: m_target; blind: m_init + 已用 delta | 相同会计映射 (matched: m_target; blind: m_init + 已用 delta), 泄漏口径一致 |
| 迭代 iterations | 真体返回的实际迭代 | numpy 实测 (零错输入 iters==0; 其余为实际收敛轮数) |
| status 四旗 (exact/accepted/syndrome/toeplitz) | 双门语义: success=exact+accepted+syndrome+toeplitz, undetected 独立 | 相同双门语义与 13 键; 后端不同源, 状态位不可跨后端比较 |

CLAIM_CEILING 原文: 合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；
D1 条件化分支下不得用本批合成数论证真实优劣。

assumed 非 ldpc 不可比声明: fallback 结果为 assumed 先验 + 非 ldpc 后端,
与真体数不可比、不可互换、不可合并; ``backend_used`` 仅经 log + metadata
侧车透出精确字面量, 永不进入 outcome dict (13 键以外零新增)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import m2lb_arm_runner as m
from comparison_bench.src.comparison_bench.methods import binary_spa_numpy as npb


BACKEND_LITERAL = "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"
_MISSING = staticmethod(lambda name: None)  # mocked ldpc absence (explicit)


def _tiny_cons(n=4, m=3):
    triples = [(0, 0, 1), (0, 3, 1), (1, 1, 1),
               (1, 3, 1), (2, 2, 1), (2, 3, 1)]
    return [{"status": "ok", "triples": list(triples), "n": n,
             "m": m, "four_cycles": 0, "min_girth": 8, "rank": m}
            for _ in range(10)]


def _tiny_planes(n=4):
    return [np.array([(p + i) % 2 for i in range(n)], dtype=np.uint8)
            for p in range(10)]


def _stage_full():
    return {"mode": "matched", "m_target": 30, "m_stage": 30,
            "stage_idx": 0, "delta_steps": [4, 4, 4, 4, 4], "m_init": 10}


def _stage_blind_init():
    return {"mode": "blind", "m_target": 30, "m_stage": 10,
            "stage_idx": 0, "delta_steps": [4, 4, 4, 4, 4], "m_init": 10}


def test_backend_id_literal_and_resolve():
    assert npb.BACKEND_ID == BACKEND_LITERAL
    fn, bid = m.resolve_spa_decode_fn(find_spec_fn=_MISSING)
    assert fn is m._spa_decode_numpy_planes and bid == BACKEND_LITERAL
    fn2, bid2 = m.resolve_spa_decode_fn(
        find_spec_fn=lambda name: object())  # mocked ldpc presence
    assert fn2 is m.spa_decode_production and bid2 == "ldpc.BpOsdDecoder"
    src = Path(npb.__file__).read_text()
    assert "import ldpc" not in src and "find_spec" not in src  # 禁硬编码 ldpc


def test_direct_decode_zero_and_single(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # zero writes by construction
    h = np.zeros((3, 4), dtype=np.uint8)
    for r, c, _v in [(0, 0, 1), (0, 3, 1), (1, 1, 1),
                     (1, 3, 1), (2, 2, 1), (2, 3, 1)]:
        h[r, c] = 1
    err, ok, it = npb.decode_error_numpy_min_sum(h, np.zeros(3,
                                                             dtype=np.uint8))
    assert ok is True and it == 0 and err.tolist() == [0, 0, 0, 0]
    for j in range(4):  # every single-bit flip corrects exactly
        e = np.zeros(4, dtype=np.uint8)
        e[j] = 1
        eh, okj, _it = npb.decode_error_numpy_min_sum(h, (h @ e) % 2)
        assert okj is True and eh.tolist() == e.tolist()
    for bad_kw in ({"max_iter": 0}, {"max_iter": True},
                   {"error_rate": float("nan")},
                   {"syndrome_delta": np.zeros(4, dtype=np.uint8)},
                   {"H": np.zeros((0, 4), dtype=np.uint8)}):
        kw = {"H": h, "syndrome_delta": np.zeros(3, dtype=np.uint8)}
        kw.update(bad_kw)
        with pytest.raises(ValueError):
            npb.decode_error_numpy_min_sum(**kw)
    assert list(Path.cwd().iterdir()) == []


def test_wrapper_matched_zero_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a0 = _tiny_planes()
    sidecar: dict = {}
    out = m.spa_decode_with_explicit_fallback(
        [p.copy() for p in a0], [p.copy() for p in a0],
        _tiny_cons(), _stage_full(), 0, 300, 3,
        find_spec_fn=_MISSING, sidecar=sidecar)
    out = m._check_outcome(dict(out))
    assert len(out) == 13 and set(out) == set(m.OUTCOME_KEYS)
    assert out["exact_match"] is True and out["accepted"] is True
    assert out["syndrome_consistent"] is True
    assert out["toeplitz_verified"] is True
    assert out["leak_ec_bits"] == pytest.approx(30.0)
    assert list(out["blind_stage_bits"]) == [0.0] * 5
    assert out["iterations"] == 0  # 对照表: 零错 iters==0
    assert out["max_iter"] == 300 and out["streak"] == 3
    assert "backend_used" not in out  # 侧车隔离: 永不进 outcome dict
    assert sidecar["backend_used"] == BACKEND_LITERAL
    assert any(BACKEND_LITERAL in line for line in sidecar["log"])
    assert list(Path.cwd().iterdir()) == []


def test_wrapper_single_error_isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a0 = _tiny_planes()
    b1 = [p.copy() for p in a0]
    b1[3] = (b1[3].astype(np.uint8)
             ^ np.array([1, 0, 0, 0], dtype=np.uint8))
    sidecar: dict = {}
    out = m._check_outcome(dict(
        m.spa_decode_with_explicit_fallback(
            [p.copy() for p in a0], b1, _tiny_cons(), _stage_full(),
            1, 300, 3, find_spec_fn=_MISSING, sidecar=sidecar)))
    assert len(out) == 13
    succ = bool(out["exact_match"] is True and out["accepted"] is True
                and out["syndrome_consistent"] is True
                and out["toeplitz_verified"] is True)
    und = bool(out["accepted"] is True) and not succ
    assert und is False  # 隔离: 成功或干净失败, 永不误接受
    assert out["leak_ec_bits"] == pytest.approx(30.0)
    assert sidecar["backend_used"] == BACKEND_LITERAL
    assert list(Path.cwd().iterdir()) == []


def test_wrapper_blind_truncation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a0 = _tiny_planes()
    out = m._check_outcome(dict(
        m.spa_decode_with_explicit_fallback(
            [p.copy() for p in a0], [p.copy() for p in a0],
            _tiny_cons(), _stage_blind_init(), 2, 300, 3,
            find_spec_fn=_MISSING, sidecar={})))
    assert out["exact_match"] is True and out["accepted"] is True
    assert out["syndrome_consistent"] is True
    assert out["toeplitz_verified"] is True
    assert out["leak_ec_bits"] == pytest.approx(10.0)  # 截断段 m_init
    assert list(out["blind_stage_bits"]) == [0.0] * 5
    assert list(Path.cwd().iterdir()) == []


def test_wrapper_fail_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a0 = _tiny_planes()
    with pytest.raises(m.Refusal):  # 9 planes != 10
        m.spa_decode_with_explicit_fallback(
            a0[:9], a0[:9], _tiny_cons()[:9], _stage_full(), 0, 300, 3,
            find_spec_fn=_MISSING)
    bad_mode = dict(_stage_full())
    bad_mode["mode"] = "turbo"
    with pytest.raises(m.Refusal):
        m.spa_decode_with_explicit_fallback(
            a0, a0, _tiny_cons(), bad_mode, 0, 300, 3,
            find_spec_fn=_MISSING)
    zero_cons = _tiny_cons()
    zero_cons[0] = dict(zero_cons[0])
    zero_cons[0]["triples"] = [(0, 0, 0)]  # coeff==0 支撑空
    with pytest.raises(m.Refusal):
        m.spa_decode_with_explicit_fallback(
            a0, a0, zero_cons, _stage_full(), 0, 300, 3,
            find_spec_fn=_MISSING)
    with pytest.raises(m.Refusal):  # sidecar 非 dict
        m.spa_decode_with_explicit_fallback(
            a0, a0, _tiny_cons(), _stage_full(), 0, 300, 3,
            find_spec_fn=_MISSING, sidecar=[])
    assert list(Path.cwd().iterdir()) == []


def test_execute_probe_with_wrapper_injected(tmp_path, monkeypatch):
    """execute 覆盖: fake bundle + fake construct + wrapper 注入, 探针截断."""
    monkeypatch.chdir(tmp_path)  # probe root 落 tmp_path
    arm = "M2LB-1M-197-matched"
    spec = m.parse_arm(arm)
    alloc = m.allocation_for(spec["source_key"], spec["m"])

    def _fake_construct(m_rows, seed, trials, plane):
        assert int(trials) == m.M2LB_MAX_TRIALS
        triples = [(r, r, 1) for r in range(int(m_rows))]
        return {"status": "ok", "triples": triples, "n": 64,
                "m": int(m_rows), "four_cycles": 0,
                "min_girth": 6, "rank": int(m_rows)}

    seen_backends: list[str] = []

    def _decode(a_planes, b_planes, constructions, stage_ctx, frame_idx,
                max_iter, streak):
        sidecar: dict = {}
        out = m.spa_decode_with_explicit_fallback(
            a_planes, b_planes, constructions, stage_ctx, frame_idx,
            max_iter, streak, find_spec_fn=_MISSING, sidecar=sidecar)
        seen_backends.append(sidecar["backend_used"])
        return out

    bundle = {"source": spec["source_key"], "fake": "bound"}
    root = "workspace/m2lb_fbad0001"
    summary = m.execute(root=root, arm=arm, bundle=bundle,
                        construct_fn=_fake_construct, decode_fn=_decode,
                        rss_fn=lambda: 0, writer=m.default_writer,
                        max_blocks=2)
    assert summary["verdict"] == "PROBE-truncated"
    assert summary["blocks_done"] == 2
    assert seen_backends and all(b == BACKEND_LITERAL
                                 for b in seen_backends)
    assert (Path(root) / "block_accounting.csv").exists()
    assert (Path(root) / "rows.json").exists()
