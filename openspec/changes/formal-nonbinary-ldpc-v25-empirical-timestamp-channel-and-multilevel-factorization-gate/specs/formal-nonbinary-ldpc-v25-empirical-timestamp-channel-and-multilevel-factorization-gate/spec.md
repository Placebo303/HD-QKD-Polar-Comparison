# Spec: formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate

> Status: FROZEN_ACCEPTED（P102 ACCEPT，主线程 2026-08-18；M0–M4 实现已授权）。

## Feature: empirical timestamp channel + multilevel factorization gate

建立可审计的经验条件信道 `P(A|B,Z)`（A,B∈{0..1023}，Z 公共配置元数据）与
F01–F05 × L01–L02 的 chain-rule 分解门，用于判断保留 1024-bin 源、使用分层
NB-LDPC（GF(512)/GF(256)/GF(32)/GF(16)/GF(8)）是否信息论/结构合理。终止于 M4
架构选择，不进入 DE/MET/有限码/FER。

## Requirements

1. R-RAW-SYM：原始符号保持 A,B∈{0..1023}；编码分层不得改变 1024-bin 字母表；
   物理 bin 合并是单独对照，须与编码分层区分记录。
2. R-CHANNEL：冻结联合计数 N_ab[a,b]=count(A=a,B=b)（取 fresh pairs 或
   joint_counts_sparse，整数计数）；主解码信道为 **P(A|B) = N_ab 对 b 列归一化**
   （P(A=a|B=b)=N_ab[a,b]/Σ_a' N_ab[a',b]）；sidecar chan_ll_table.npy 冻结为该
   P(A|B) 的 (log-)likelihood 方向；signed/modular offset 与 Gray XOR mask 仅
   作诊断产物，不得作为解码信道替代；f=leak_IR/H(A|B,Z)，包含所有 residual 层。
3. R-LAYER：Bob 输入保留完整 B；第 i 层仅用 B + Z + Bob-only 已验证前层；residual
   不公开；每层 syndrome 计入总 leakage；链式律
   H(A|B,Z)=Σ_i H(U_i|B,Z,U_<i) 用同一联合计数器在浮点误差内闭合。
4. R-SPLIT：每 source/file 时间序 60/20/20（train/validation/holdout）；操作计数
   为 pairs.parquet 行数（1M=512000/1p5M=708352/2M=933120，source 尺寸见 design
   冻结计表）；禁止 frame
   跨集、随机拆 symbol、holdout 估 delay、按 holdout 选 mapping、混合 source 随机切。
5. R-FROZEN-SPACE：候选仅 F01–F05（GF(512)+GF(2) / GF(256)+GF(4) / GF(32)+GF(32)
   / GF(16)+GF(16)+GF(4) / GF(8)x3+GF(2)）与 L01 natural / L02 Gray；禁止事后发明
   mapping 或扩层组合。位切分冻结为对 10-bit 标签（natural 或 gray 后）**MSB→LSB**
   按 design §4 表划分（F01 [9..1],[0]；F02 [9..2],[1..0]；F03 [9..5],[4..0]；
   F04 [9..6],[5..2],[1..0]；F05 [9..7],[6..4],[3..1],[0]）。
6. R-MODELS：至少 C01 QSC、C02 V17 product、C03 pooled additive signed-delta、
   C04 source-conditioned、C05 source+parity/boundary、C06 local-jitter+global
   background；每个在 validation/holdout 上按 per-source 报告 NLL/条件熵/
   calibration/zero-prob；pooled 仅补充。
7. R-DELAY：在既有 delay 配置（sidecar 已记 delay_used_ps）下分析 ±1 结构、方向
   与时间稳定性；**不重读 .ttbin、不重估亚 bin delay**；方向随 source/delay_used_ps
   变化视为需要建模的 source/delay-conditioned channel，不作为 alignment blocker。
8. R-GATE：M4 产出供 V26 的候选——**高域 GF(512)/GF(256)** + **中域对照
   GF(32)/GF(16)/GF(8)**（不选唯一方案）；同时给出总状态
   pass_ready_for_de_change / fail_no_stable_factorization /
   blocked_insufficient_joint_data / blocked_alignment_unresolved。PASS 只允许
   提出 V26，不自动启动。
9. R-EVIDENCE：P0 data_inventory.json 持久化到 change 的 evidence/ 目录；additive 输出
   `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_YYYYMMDD/run_<ts>/`
   含 data_inventory/split_manifest/channel_summary/delta_by_source/gray_joint_masks/
   channel_counts/model_holdout_scores/factorization_layers/chain_rule_check/
   alignment_report/gate_summary/readonly_verify；独立 verifier 从原始统计重算。
10. R-FORBID：未经新授权禁止 V24 搜索、扩 λ/ρ、true MET、有限 NB-LDPC、FER、
    fresh qualification、公开 residual/LSB、q512/q256 coarse SER 冒充总 FER、
    Alice-oracle 选候选、holdout 选 mapping、改动冻结 Polar baseline、
    experiments/run_e2e_pipeline.py、longrun_*/minrerun_*/routeA_*、覆盖旧输出、push。
