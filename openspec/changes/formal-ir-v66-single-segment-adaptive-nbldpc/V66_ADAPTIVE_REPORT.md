# V66 Single-Segment Adaptive Report (PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK) — single-source 20260123_1M_600k_0dB

**Status**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 预冻结，decoder-free 已回填无 TBD，不含 EVAL decoder 执行  
**HEAD**: `832e5394bb366927c779414ee5a08427bd740a2d` (`formal-ir-mainline`, 推送后新 Plan SHA)  
**Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`)  
**Predecessor**: `V64 22/24 full-tag PASS` + `V65 new-session`  
**Registry**: `v66_data_registry.json` authoritative (CAL24+VAL24+EVAL24 =72 overall 单源 20260123_1M_600k_0dB, development_replay=true)  
**Spike**: `v66_spike_summary.json` 已回填 CE1/CE2/raw/aligned m1/m2 rank nested disclosure constructibility, `MATRIX_NOT_CONSTRUCTIBLE` 已判定，无 TBD

## 1. 冻结分段 (单 session 单源 72, development_replay)

- **Overall**: `CAL 24 + VAL 24 + EVAL 24 =72` blocks (每 block 4×256=1024 symbols), 每段 24 单源，单 `session_id=20260123_1M_600k_0dB`，不跨 session 拼接。
- **Per source single** (冻结窗口 contiguous 0-71):
  - `20260123_1M_600k_0dB` (F=2130 K=532): CAL blocks 0–23 (frames 0–95), VAL 24–47 (96–191), EVAL 48–71 (192–287), 各 24576 pairs (96 frames)
- **复用**: 来自 `v55_intake_20260828/pairs/20260123_1M_600k_0dB` 单 session 旧数据，已标记 `development_replay=true, replay_source=v55_intake_20260828`，与 `V13/V48..V64` 内部互不重叠（键 `(source,session,frame)`），`F_s=2130 K=532 ≥72` 已过 `DATA_NOT_READY` 门。
- **零重叠**: `CAL∩VAL==∅ && CAL∪VAL∩EVAL==∅ && CAL∪VAL∪EVAL ∩ (V13..V64)==∅` (元组键)，`not_cross_spliced`, `single_session`。

## 2. 冻结主体 (U=32*U1+U2, Lane C, Δ8 单源)

- `n1024, q1024, GF32 poly37, H1 16×1024 rank16 80b, U=32*U1+U2 F03 5+5 natural, Lane C ordinal-2 s38310x m2 184 base（单源）, H_inc Δ8 家族 nested, decoder 90/1.0 poly37 (禁用), full-tag canonical 32*U1+U2 single 64b, leak=5*(m1+m2)+64` — 零改，不引 MET/protograph/SC，`git diff -- src/ ==0`。

## 3. P 重估 + VAL CE + raw m + 同家族 +8 + 先验校验 (不依 EVAL, decoder-free, m1<1024&&m2<1024)

| source | CE1 (VAL) | CE2 (VAL) | CE_full | chain_delta | m1_raw | m2_raw | m_total_raw | m1 (+8) | m2 (+8) | m_total | Δm1 | Δm2 | rank_m1==m1 | rank_m2==m2 | nested | disclosure 5*(m1+m2)+64 | constructible | feasible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB (1M) | 0.4207 | 0.3907 | 0.8114 | 2.3e-12 <1e-9 | 112 | 104 | 216 | 112 | 104 | 216 | 0 | 0 | true | true | true | 1144 | true | true |

- **公式**: `m1_raw = ceil(1.3*1024*CE1/5)`, `m2_raw = ceil(1.3*1024*CE2/5)`, `m1 = ceil_to_family(m1_raw,+8)`, `m2 = ceil_to_family(m2_raw,+8)` (仅上调), `CE` 为 `VAL` 上 `P(CAL)` 的交叉熵，`EVAL` 未参与 (`used_eval==False`)。**已从 m_total<1024 改为 m1<1024 && m2<1024**，不用 m_total 判 feasibility。
- **守卫**: `m_raw` 未 `min(1024, ...)` cap，`CE_chain |CE_full-CE1-CE2|<1e-9` 已验，禁第二 estimator，`MATRIX_NOT_CONSTRUCTIBLE` 已判定（family 可覆盖，false）。
- **先验**: `m1<1024 && m2<1024 true, rank_m1 112==112 true, rank_m2 104==104 true, nested true, disclosure 1144==5*216+64 true, constructible true` → `RATE_NOT_FEASIBLE` 不触发，`MATRIX_NOT_CONSTRUCTIBLE` false，`DEVELOPMENT_BENCHMARK_READY` 可申请 EVAL。

## 4. 满秩嵌套披露先验 (进 EVAL 前, m1/m2 分别)

- `m1<1024 && m2<1024 && gf_rank(H1(m1))==m1 && gf_rank(H2(m2))==m2 && nested(H) && disclosure==5*(m1+m2)+64 && constructible` — decoder-free 校验，**已通过**，否则 `overall=V66_RATE_NOT_FEASIBLE` (含 `MATRIX_NOT_CONSTRUCTIBLE` 子类) 不启动 decoder。**无 TBD**。

## 5. EVAL 密封门禁 (19/24 overall undetected0, 已删 per-source, 未执行预冻结)

- **规模**: `EVAL 24 blocks (96 frames 24576 pairs)` 单源 20260123_1M_600k_0dB 密封，仅一度量，不回灌 `P/m`。
- **门禁**: `exact_full ≥19/24 overall (79.17%) && undetected_full_tag==0 && all exact→tag_ok_full && disclosure==5*(m1+m2)+64 && efficiency=disclosure/(1024*CE_full)` 报告。**已删 per-source 6/8，仅 overall**。
- **本轮**: `EVAL` 未执行，门禁仅框架冻结，`used_eval==False` 已守卫，`m1/m2` 已冻结 112/104。

## 6. 五态终态机 (优先级, 已删 per-source, 已改 m1/m2)

```
EVIDENCE_INVALID (materialization/CE_chain/frame256/provenance) >
DATA_NOT_READY (K<72 or segment !=24) >
RATE_NOT_FEASIBLE / MATRIX_NOT_CONSTRUCTIBLE (m1>=1024 or m2>=1024 or rank!=m or not nested or disclosure or not constructible) >
ADAPTIVE_EVAL_FAIL (EVAL exact<19/24 or undetected!=0) >
ADAPTIVE_EVAL_PASS (EVAL exact>=19/24 && undetected==0)
else DEVELOPMENT_BENCHMARK_READY (EVAL 未执行但前三态已过)
```

- **当前**: `EVIDENCE_INVALID` 未触发，`DATA_NOT_READY` false (K 532 ≥72), `RATE_NOT_FEASIBLE` false (`m1 112 m2 104 <1024 constructible`), `MATRIX_NOT_CONSTRUCTIBLE` false, `EVAL` 未执行故终态为 `DEVELOPMENT_BENCHMARK_READY`。

## 7. Spike 摘要 (decoder-free, 已回填无 TBD)

- `v66_spike_summary.json` 已执行 `scripts/v66_spike.py` 回填：`CE1 0.4207 CE2 0.3907 CE_full 0.8114 chain 2.3e-12, m1_raw 112->112 m2_raw 104->104, disclosure 1144, rank 112/104 nested true constructible true, feasible true`。
- `rg "decode_" 0 hits`, `py_compile PASS` 已验，`m1<1024 && m2<1024` 已验，`MATRIX_NOT_CONSTRUCTIBLE false`。
- **控制台摘要**: `CAL 24 (24576 pairs) -> C_ab 1024x1024 -> P(U1|B) 32x1024 P(U2|U1B) 32x32x1024 -> VAL 24 CE1 0.4207 CE2 0.3907 CE_full 0.8114 chain 2.3e-12 -> m1_raw 112->112 m2_raw 104->104 (+8, constructible true) -> m1<1024&&m2<1024 true rank true nested true disclosure 1144 -> overall DEVELOPMENT_BENCHMARK_READY`。

## 8. 独立 Review Packet

- `review/V66_REVIEW_PACKET.md` 已更新单源 72、新 Plan SHA、`m1<1024&&m2<1024`、`MATRIX_NOT_CONSTRUCTIBLE`、无 per-source、无 TBD，需独立线程复核 `HEAD/832e5394bb366927c779414ee5a08427bd740a2d, data 84d62779, 单 session 72 24/段, development_replay, zero_overlap (source,session,frame), CAL→VAL CE→m_raw→+8→m1<1024&&m2<1024 rank nested disclosure constructibility, EVAL 未读, 19/24 overall undetected0, 五态` 后方可 `PLAN_ACCEPT`，**不自行 ACCEPT**。

## 9. 下一步

1. 执行 `scripts/v66_data_readiness.py` (只读调查) 确认 `v66_data_registry.json` 零重叠与 24/段 单源 72。
2. 已执行 `scripts/v66_spike.py` 得 `CE1/CE2/m_raw/m_family/rank/constructibility` 判定 `RATE_NOT_FEASIBLE`/`MATRIX_NOT_CONSTRUCTIBLE` 或 `READY` — **已 READY**。
3. 独立 review 线程 `Pre-RESULT` 复核后，主线程判 `PLAN_ACCEPT` 或 `revise-required`。
4. 仅 `READY` 后另起 `EXECUTE_AUTH` 授权 `EVAL 24` decoder 度量 `19/24 overall undetected0`，本轮不创建 `run_01`。
5. **四工件+registry+spike+脚本已单独提交推送，返回新 Plan SHA `832e5394bb366927c779414ee5a08427bd740a2d`（推送后替换）**。

## 10. 边界声明

- 本报告不宣称 `FER/SKR/晋升/安全证明`，不比较方法，不转 qualification，`DEVELOPMENT_BENCHMARK` 可复用旧数据但已显式标记，与 fresh 区分。**已删 per-source 6/8，仅 overall 19/24**；**已改 m1<1024&&m2<1024**；**无 TBD**；**禁 decoder/run_01**。
