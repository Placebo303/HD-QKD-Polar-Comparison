# 附录: 二元 SPA numpy fallback 对照表 (Route A, implementation-only)

> 本附录为对照附录 (实现面): 冻结包 `PACKET.md` / prompt / `EXPLORATION_LOG.md`
> 一字不动; 本附录仅指定真体后端与显式 numpy fallback 之间的对照口径。
> 本次放宽仅 wrapper (`m2lb_arm_runner.py` 末尾
> `resolve_spa_decode_fn()` / `spa_decode_with_explicit_fallback()`); 本体
> `spa_decode_production` 的 STOP-BLOCKED 语义 (ldpc 缺席即 refuse, 永不切
> bit-flip) 仍有效。

## 对照表 (与 wrapper docstring + 新测试头三处一致, 以本表为准)

| 维度 | 真体 ldpc.BpOsdDecoder (缺席即 STOP-BLOCKED, 永不替代) | numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder) |
| 泄漏 leak_ec_bits / blind_stage_bits | matched: m_target; blind: m_init + 已用 delta | 相同会计映射 (matched: m_target; blind: m_init + 已用 delta), 泄漏口径一致 |
| 迭代 iterations | 真体返回的实际迭代 | numpy 实测 (零错输入 iters==0; 其余为实际收敛轮数) |
| status 四旗 (exact/accepted/syndrome/toeplitz) | 双门语义: success=exact+accepted+syndrome+toeplitz, undetected 独立 | 相同双门语义与 13 键; 后端不同源, 状态位不可跨后端比较 |

## CLAIM_CEILING 原文

合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。

## assumed 非 ldpc 不可比声明

fallback 结果为 assumed 先验 + 非 ldpc 后端, 与真体数不可比、不可互换、
不可合并; `backend_used` 仅经 log + metadata 侧车透出精确字面量
(`"numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"`), 永不进入
outcome dict (13 键以外零新增)。

## 实现位置 (additive only)

- 新后端: `comparison_bench/src/comparison_bench/methods/binary_spa_numpy.py`
  (`decode_error_numpy_min_sum`, 纯 numpy, 无新依赖, 确定性, fail-closed)。
- wrapper: `comparison_bench/src/comparison_bench/cli/m2lb_arm_runner.py` 末尾
  (`resolve_spa_decode_fn` / `spa_decode_with_explicit_fallback` /
  `_spa_decode_numpy_planes`)。
- 测试: `comparison_bench/tests/test_binary_spa_numpy_fallback.py`
  (合成 tiny, 零写盘直接调用 + `execute` 探针覆盖)。
