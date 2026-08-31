# V66 Single-Segment Adaptive Report (PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK) — single-source 20260123_1M_600k_0dB

**Status**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — 预冻结，decoder-free 真实 parquet 重算，无 TBD，不含 EVAL decoder 执行  
**HEAD**: `99511e62043cf3af04f08aee2569d1291af0101e` (ACCEPTED_PLAN_SHA `832e5394bb366927c779414ee5a08427bd740a2d`，`git rev-parse HEAD == origin/formal-ir-mainline` 重核)  
**Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`)  
**Predecessor**: `V64 22/24 full-tag PASS` + `V65 new-session`  
**Registry**: `v66_data_registry.json` authoritative (CAL24+VAL24+EVAL24 =72 overall 单源 20260123_1M_600k_0dB, development_replay=true)  
**Spike**: `v66_spike_summary.json` 真实 parquet CE1/CE2 + CAL-only λ + H1-112/H2-184→192 rank nested disclosure 已重算，`V66_RATE_NOT_FEASIBLE / MATRIX_NOT_CONSTRUCTIBLE`，无 TBD，fail-closed

## 1. 冻结分段 (单 session 单源 72, development_replay, 历史重叠机械审计)

- **Overall**: `CAL 24 + VAL 24 + EVAL 24 =72` blocks (每 block 4×256=1024 symbols), 每段 24 单源，单 `session_id=20260123_1M_600k_0dB`，不跨 session 拼接。
- **Per source single** (冻结窗口 contiguous 0-71):
  - `20260123_1M_600k_0dB` (F=2130 K=532): CAL blocks 0–23 (frames 0–95), VAL 24–47 (96–191), EVAL 48–71 (192–287), 各 24576 pairs (96 frames)
- **复用与机械审计**: 来自 `v55_intake_20260828/pairs/20260123_1M_600k_0dB` 单 session 旧数据，已标记 `development_replay=true, replay_source=v55_intake_20260828`，与 `V13/V48..V64` 键 `(source,session,frame)` 机械审计：历史 `(source,session,frame)` 与 `v55_stratified_registry_candidate.json + v64_fresh_registry.json` 对比，存在预期重叠（同 session 前 72 blocks 复用），已标注 `development_replay` 区分 fresh qualification，非 fresh 拼接，`CAL∩VAL==∅ && CAL∪VAL∩EVAL==∅` 内部零重叠已验，`F_s=2130 K=532 ≥72` 已过 `DATA_NOT_READY` 门。
- **零重叠**: 内部 `CAL∩VAL==∅ && CAL∪VAL∩EVAL==∅` (元组键)，`single_session` 隔离，`not_cross_spliced`，历史重叠已审计标记 `development_replay=true`。

## 2. 冻结主体 (U=32*U1+U2, Lane C, Δ8 单源)

- `n1024, q1024, GF32 poly37, H1 16×1024 rank16, U=32*U1+U2 F03 5+5 natural, Lane C ordinal-2 s38310x m2 184 base（单源）, H_inc Δ8 家族 nested, decoder 90/1.0 poly37 (禁用), full-tag canonical 32*U1+U2 single 64b, leak=5*(m1+m2)+64` — 零改，不引 MET/protograph/SC，`git diff -- src/ ==0`。

## 3. P 重估 + VAL CE + raw m + 同家族 +8 + 先验校验 (真实 parquet, CAL-only λ, 不依 EVAL, m1<1024&&m2<1024)

| source | λ (CAL-only) | CE1 (VAL) | CE2 (VAL) | CE_full | chain_delta | m1_raw | m2_raw | m_total_raw | m1 (+8) | m2 (+8, ≥184 仅+8) | m_total | disclosure_capped 5*(m1+m2)+64 | disclosure_raw_required 5*(m1_raw+m2_raw)+64 | eff (capped) | rank_m1==m1 | rank_m2==m2 | nested | constructible | feasible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260123_1M_600k_0dB (1M) | 20.0 (CAL 4-fold CV 最优) | 3.9552 | 3.3933 | 7.3485 | 0.0 <1e-9 | 1054 | 904 | 1958 | 1056 | 192 | 1248 | 6304 | 9854 | 0.838 | false | true | false | false | false |

- **λ 冻结 (CAL-only)**: `LAMBDA_CANDIDATES [0.1,0.5,1,2,5,10,20,50]` 在 CAL 24 blocks 内 4-fold CV (每 fold 24 frames 6144 pairs) 计 `CE_full` 平均，最优 `λ=20.0` CV CE 7.3431，最差 0.1 10.621，**仅 CAL 选择，未用 VAL/EVAL**。
- **公式**: `m1_raw = ceil(1.3*1024*CE1/5)`, `m2_raw = ceil(1.3*1024*CE2/5)`, `m1 = ceil_to_family(m1_raw,+8)`, `m2 = (m2_raw<=184?184 : 184+8)` 仅单步 +8 (指令要求 H2 至少 184 仅+8)，`CE` 为 `VAL` 上 `P(CAL,λ)` 的交叉熵，`EVAL` 未参与。
- **守卫**: `m_raw` 未 cap，`CE_chain 0.0<1e-9` 已验，`m1 1056>=1024` 与 `m2_raw 904 >192` 单步覆盖不足 → `MATRIX_NOT_CONSTRUCTIBLE true`，`disclosure_capped 6304=5*1248+64` 用实际行数重算，`disclosure_raw_required 9854=5*1958+64` 为未截断理论需求，`efficiency 6304/(1024*7.3485)=0.838` 按 capped 报告（raw 则 9854/7524.9=1.31 已超限）。
- **H 实际构造**: `H1 16×1024 QC rank16==16 true`, `H1 112×1024 QC rank112==112 true` 但 `H1-16` 非 `H1-112` 前缀 (`contains False`, QC 家族非嵌套)，`H2 184 rank184 true`, `H2 192 rank192 true` 但 `184` 非 `192` 前缀 (`nested False`)，故 `nested_ok false`, `rank_m1_ok false (m1>=1024)` → `RATE_NOT_FEASIBLE`。
- **先验**: `m1 1056 >=1024` 已触发 `RATE_NOT_FEASIBLE`，`MATRIX_NOT_CONSTRUCTIBLE true`，不启动 decoder。

## 4. 满秩嵌套披露先验 (进 EVAL 前, m1/m2 分别, 实际 GF32 rank)

- `m1<1024 && m2<1024 && gf_rank(H1(m1))==m1 && gf_rank(H2(m2))==m2 && nested(H) && disclosure_capped==5*(m1+m2)+64 && constructible` — decoder-free 实际 QC 构造+GF32 rank 校验，**未通过** (`m1 1056>=1024, rank_m1 false, nested false, constructible false`) → `overall=V66_RATE_NOT_FEASIBLE` (含 `MATRIX_NOT_CONSTRUCTIBLE` 子类) 不启动 decoder，`disclosure_capped 6304` 已用实际行数重算（`disclosure_raw_required 9854` 供对照）。**无 TBD**。
- **H1-112 验证**: `H1-16` 16×1024 rank16，`H1-112` 112×1024 rank112，`contains False` (QC 不嵌套；ponytail: PEG 家族可得 true 嵌套，若吞吐重要可切 PEG，但当前 m1 已超限，嵌套不影响终态)。
- **H2 验证**: `m2` 至少 184，仅 +8 至 192 单步，`H2-184 rank184 true`, `H2-192 rank192 true`, `nested False` (QC)，且 `m2_raw 904` 需 904 行，单步 192 无法覆盖 → `MATRIX_NOT_CONSTRUCTIBLE`。

## 5. EVAL 密封门禁 (19/24 overall undetected0, 已删 per-source, 未执行预冻结)

- **规模**: `EVAL 24 blocks (96 frames 24576 pairs)` 单源 20260123_1M_600k_0dB 密封，仅一度量，不回灌 `P/m/λ`。
- **门禁**: `exact_full ≥19/24 overall (79.17%) && undetected_full_tag==0 && all exact→tag_ok_full && disclosure_capped==5*(m1+m2)+64 (6304) && disclosure_raw_required==5*(m1_raw+m2_raw)+64 (9854) && efficiency=disclosure_capped/(1024*CE_full)` 报告。**已删 per-source 6/8，仅 overall**。
- **本轮**: 未执行（`RATE_NOT_FEASIBLE` 阻断），门禁仅框架冻结，`used_eval==False` 已守卫，`m1/m2` 已冻结 1056/192，`disclosure_capped 6304 / raw_required 9854` 待验但已因先验失败不进入 EVAL。

## 6. 五态终态机 (优先级, 已删 per-source, 已改 m1/m2)

```
EVIDENCE_INVALID (materialization/CE_chain/frame256/provenance) >
DATA_NOT_READY (K<72 or segment !=24) >
RATE_NOT_FEASIBLE / MATRIX_NOT_CONSTRUCTIBLE (m1>=1024 or m2>=1024 or rank!=m or not nested or disclosure or not constructible or m_raw>allowed +8) >
ADAPTIVE_EVAL_FAIL (EVAL exact<19/24 or undetected!=0) >
ADAPTIVE_EVAL_PASS (EVAL exact>=19/24 && undetected==0)
else DEVELOPMENT_BENCHMARK_READY (EVAL 未执行但前三态已过)
```

- **当前**: `EVIDENCE_INVALID` false, `DATA_NOT_READY` false (K 532 ≥72), `RATE_NOT_FEASIBLE` **true** (`m1 1056>=1024`, `rank_m1 false`, `nested false`, `MATRIX_NOT_CONSTRUCTIBLE true`), `EVAL` 未执行但已被第三态阻断，终态 `V66_RATE_NOT_FEASIBLE` (子类 `MATRIX_NOT_CONSTRUCTIBLE`)。

## 7. Spike 摘要 (真实 parquet, fail-closed, 无 TBD)

- `v66_spike_summary.json` 已执行 `scripts/v66_spike.py` 真实 parquet (24576 pairs CAL/VAL) + CAL-only λ=20.0 + QC H 构造：`CE1 3.9552 CE2 3.3933 CE_full 7.3485 chain 0.0, m1_raw 1054->1056 m2_raw 904->192, H1-16 16 H1-112 112 contains False, H2-184 184 H2-192 192, disclosure 6304 eff 0.838, MATRIX_NOT_CONSTRUCTIBLE true -> RATE_NOT_FEASIBLE`。
- `rg "decode_" 0 hits`, `py_compile PASS` 已验，`fail-closed` 已验 (缺 parquet exit 2, 合成仅 `--allow-synthetic` 显式)，`CAL-only λ` 已验，`H 实际 GF32 rank` 已验，`+8` 仅单步已验，`development_replay` 机械审计已标记。
- **控制台摘要**: `CAL 24 (24576) -> C_ab 1024x1024 -> λ 20.0 CAL CV -> VAL CE1 3.9552 CE2 3.3933 CE_full 7.3485 chain 0.0 -> m1_raw 1054->1056 m2_raw 904->192 (+8 capped) H1-16 16 H1-112 112 contains False disclosure 6304 -> overall V66_RATE_NOT_FEASIBLE (MATRIX_NOT_CONSTRUCTIBLE)`。

## 8. 独立 Review Packet

- `review/V66_REVIEW_PACKET.md` 需更新新 SHA、真实 CE/λ/H rank/nested/disclosure、`MATRIX_NOT_CONSTRUCTIBLE`、`development_replay` 机械审计、fail-closed 证据，需独立线程复核 `HEAD/99511e62043cf3af04f08aee2569d1291af0101e (plan 832e5394bb366927c779414ee5a08427bd740a2d), data 84d62779, 单 session 72 24/段, development_replay+历史键审计, CAL-only λ 20.0, CE1/CE2 真实 parquet, m_raw 1054/904 -> 1056/192 +8 capped, H1-16/112 rank 16/112 contains False, H2 184/192 rank, disclosure_capped 6304 / disclosure_raw_required 9854, MATRIX_NOT_CONSTRUCTIBLE, 五态 RATE_NOT_FEASIBLE` 后方可 `PLAN_ACCEPT` 或 `revise-required`，**不自行 ACCEPT**。

## 9. 下一步

1. 执行 `scripts/v66_data_readiness.py` 确认 `v66_data_registry.json` 零重叠与 24/段 单源 72 + 历史审计。
2. 已执行 `scripts/v66_spike.py` 真实 parquet 得 `CE1/CE2 λ m_raw/m_family H rank/nested/disclosure` → `V66_RATE_NOT_FEASIBLE / MATRIX_NOT_CONSTRUCTIBLE` — **需 revise-required** (非 READY)，不进入 EVAL decoder。
3. 独立 review 线程 `Pre-RESULT` 复核后，主线程判 `revise-required` (当前) 或改信道/码参数后重提。
4. 本轮不创建 `run_01`，保持 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，fail-closed 已验。
5. **待单独提交推送新 SHA** (替代旧 `832e5394`)，推送后独立 review。

## 10. 边界声明

- 本报告不宣称 `FER/SKR/晋升/安全证明`，不比较方法，不转 qualification，`DEVELOPMENT_BENCHMARK` 可复用旧数据但已显式机械审计标记 `development_replay`，与 fresh 区分。**真实 parquet 无手填 JSON**；**CAL-only λ**；**H1-112/H2-184→192 实际 GF32 rank 嵌套已验**；**disclosure_capped 6304 用实际行数重算，disclosure_raw_required 9854 供对照**；**fail-closed 生产路径，无硬编码 fallback**。
