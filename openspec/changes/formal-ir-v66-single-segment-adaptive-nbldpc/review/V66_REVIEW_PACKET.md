# V66 Independent Review Packet — Pre-RESULT (PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK) — revised single-source 20260123_1M_600k_0dB

**Change**: `formal-ir-v66-single-segment-adaptive-nbldpc`  
**HEAD**: `TBD_NEW_PLAN_SHA` (`formal-ir-mainline`, 推送后新 40位 Plan SHA — 需 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，40位全量)  
**ACCEPTED_PLAN_SHA**: `TBD_NEW_PLAN_SHA` (本次修订后单独提交推送的新 Plan SHA；独立线程需 `rg TBD_NEW_PLAN_SHA` 0 hits 在旧 SHA 残留检查 + `rg cabc928f` 0 hits 旧 SHA 已清除)  
**Data SHA**: `84d62779` (`d1024 bw200 nearest legacy_v1`)  
**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`  
**Single-source**: `20260123_1M_600k_0dB` 72 overall (CAL24 VAL24 EVAL24)  
**Reviewer**: 独立线程 / reviewer-go (非实现线程)  
**Date**: 2026-08-31 (revised)

## 1. Scope (本轮禁止项核查, revised)

- [ ] `rg "decode_" 0 hits` 在 `scripts/v66_*.py` (`grep -r "decode_" openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/scripts scripts/v66_*.py`)  
- [ ] `rg "import.*decoder" 0 hits`  
- [ ] `py_compile` PASS (`python -m py_compile scripts/v66_*.py scripts/v66_data_readiness.py scripts/v66_spike.py`)  
- [ ] `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0` (未改冻结基线)  
- [ ] `git diff -- openspec/changes/formal-ir-v6[0-5]/ ==0` (除本变更外零改)  
- [ ] `comparison_bench/outputs_comparison/**/v66_*/run_01` 不存在 (未创建 decoder 执行, 禁 run_01)  
- [ ] 未比较方法、未改 baseline、未转 qualification  
- [ ] `DECODE_FORBIDDEN` 保持至 `EXECUTE_AUTH`  
- [ ] `TBD` 0 hits in `v66_spike_summary.json` + `V66_ADAPTIVE_REPORT.md` (已回填)  
- [ ] `per-source 6/8` 0 hits (已删，仅 overall 19/24)  
- [ ] `m_total<1024` 0 hits (已改为 `m1<1024 && m2<1024`)  

## 2. 单段冻结与只读调查 (A, revised single-source)

- [ ] `v66_data_registry.json` 存在且 `schema v66_data_v1` 且 `single_source 20260123_1M_600k_0dB`  
- [ ] `overall 72 = CAL24+VAL24+EVAL24` 单源 24/段 (per_source 24)  
- [ ] `CAL_session_id == VAL_session_id == EVAL_session_id == "20260123_1M_600k_0dB"` (单 session 单源)  
- [ ] `CAL_key∩VAL_key==∅ && CAL∪VAL∩EVAL==∅ && CAL∪VAL∪EVAL ∩ (V13..V64)==∅` 键 `(source,session,frame)` 单源 72 内部互不重叠  
- [ ] `not_cross_spliced`, `frame 256` 每帧 `256 pairs`  
- [ ] `development_replay=true` 且 `replay_source=v55_intake_20260828` 显式 (可复用旧数据但标记)  
- [ ] `K=532 ≥72` → `DATA_NOT_READY` false, `F=2130`  
- [ ] `F_s` 足 288 frames 已验  

## 3. 冻结主体 (B, single-source)

- [ ] `U=32*U1+U2 F03 5+5 natural, U1>>5 U2&31`  
- [ ] `n1024 GF32 poly37 H1 16×1024 rank16 80b`  
- [ ] `Lane C ordinal-2 s38310x m2 184` single-source base  
- [ ] `H_inc Δ8 家族 nested`  
- [ ] `decoder 90/1.0 poly37 full-tag canonical 32*U1+U2 single 64b leak 5*(m1+m2)+64` (禁用)  
- [ ] 未引 `MET/protograph/SC` (`rg "MET|protograph|SC-LDPC" 0 hits` 在冻结主体)  

## 4. P 重估 + VAL CE + raw m + 同家族 +8 + 先验校验 (C, revised m1<1024&&m2<1024)

- [ ] `C_ab 1024×1024 sum 24576` (CAL-only single-source)  
- [ ] `P(U1|B) 32×1024 + P(U2|U1B) 32x32x1024` 已生成  
- [ ] `CE1=-E_VAL log P(U1|B)=0.4207, CE2=0.3907, CE_full=0.8114` 且 `|CE_full-CE1-CE2|=2.3e-12 <1e-9`  
- [ ] `m1_raw = ceil(1.3*1024*CE1/5)=112, m2_raw=104` 未 `min(1024, ...)` cap (`grep "min(" 0 hits` 为伪装)  
- [ ] `m1_family = ceil_to_+8(m1_raw)=112, m2_family=104` 显式 `+8` 档，不依 `EVAL` (`used_eval==False`)  
- [ ] `m1<1024 && m2<1024` true (已改，不用 m_total)  
- [ ] `gf_rank(H1(m1))==m1` (112) true, `gf_rank(H2(m2))==m2` (104) true (满秩, GF32 poly37)  
- [ ] `nested(H_base, H_inc)` true  
- [ ] `disclosure==5*(m1+m2)+64 =1144` true  
- [ ] `constructible true` (Δ8 family 覆盖 112/104), `MATRIX_NOT_CONSTRUCTIBLE false`  
- [ ] 若族不能覆盖则 `MATRIX_NOT_CONSTRUCTIBLE` 已显式 (本 spike 覆盖)  
- [ ] 若任一失败 → `RATE_NOT_FEASIBLE` (含 `MATRIX_NOT_CONSTRUCTIBLE`) 已显式  
- [ ] `TBD` 0 hits, `constructibility` 已回填  

## 5. EVAL 密封门禁 (D, revised 已删 per-source)

- [ ] `EVAL 24 blocks overall single-source` 仅 `identity` (`used_eval==False` 在估计侧)  
- [ ] 门禁 `exact_full ≥19/24 overall && undetected==0 && all exact→tag_ok_full && disclosure==5*(m1+m2)+64` 已冻结 (**无 per-source 6/8**)  
- [ ] `per-source` 0 hits in gate (已删)  
- [ ] `efficiency = disclosure/(1024*CE_full)` 报告占位  

## 6. 终态机 (E, revised)

- [ ] 优先级 `EVIDENCE_INVALID > DATA_NOT_READY > RATE_NOT_FEASIBLE/MATRIX_NOT_CONSTRUCTIBLE > ADAPTIVE_EVAL_FAIL > ADAPTIVE_EVAL_PASS` (未执行时 `READY`) 已显式, **已删 per-source**  
- [ ] `RATE_NOT_FEASIBLE` 含 `MATRIX_NOT_CONSTRUCTIBLE` 子类, `m1<1024 && m2<1024` (not m_total)  
- [ ] `ADAPTIVE_EVAL_PASS` 需 `EVAL` 执行后 `19/24 overall undetected0` (**无 per-source**)  
- [ ] 当前终态 `DEVELOPMENT_BENCHMARK_READY` (m1 112 m2 104 <1024 constructible)  

## 7. 四工件+registry+spike+脚本单独提交推送 (F, new)

- [ ] `proposal.md/design.md/tasks.md/specs/spec.md` 一致 HEAD `TBD_NEW_PLAN_SHA`  
- [ ] `v66_data_registry.json` single-source 72 已落盘  
- [ ] `v66_spike_summary.json` 已回填 CE1/CE2/raw/aligned m1/m2 rank nested disclosure constructibility 无 TBD  
- [ ] `scripts/v66_data_readiness.py` + `scripts/v66_spike.py` 已创建 `rg decode 0 hits` `py_compile PASS`  
- [ ] `V66_ADAPTIVE_REPORT.md` 已回填无 TBD  
- [ ] `git log --oneline -1` 显示 `TBD_NEW_PLAN_SHA` 且 `git rev-parse HEAD == origin/formal-ir-mainline` (推送后)  
- [ ] 未创建 `run_01`  

## 8. 结论

- [ ] **PASS** → 建议 `PLAN_ACCEPT` (仍 `EXECUTE_NOT_AUTHORIZED`，需另起 `EXECUTE_AUTH` 才允 `EVAL` decoder, 单源 19/24 overall)  
- [ ] **FAIL** → `revise-required` (列明失败门编号与 rg/py_compile/TBD/per-source/m_total 残留证据)  
- [ ] **不自行 ACCEPT** — 本 packet 仅建议，主线程/用户裁决  

**Reviewer 签名**: _________________  
**实现线程 SHA 重核**: `git rev-parse HEAD` = `TBD_NEW_PLAN_SHA` (需 40位全量, 推送后)  
**独立复核命令**: `rg "decode_" scripts/v66_*.py` → 0 hits ; `rg "TBD" openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/` → 0 hits (除 HEAD 占位); `rg "per-source" openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/` → 0 hits (except history); `rg "m_total<1024" openspec/changes/formal-ir-v66-single-segment-adaptive-nbldpc/` → 0 hits ; `python -m py_compile scripts/v66_*.py` → PASS ; `ls comparison_bench/outputs_comparison/**/v66_*/run_01` → not found ; `python scripts/v66_spike.py --registry v66_data_registry.json` → CE1 0.4207 CE2 0.3907 m1 112 m2 104 constructible true
