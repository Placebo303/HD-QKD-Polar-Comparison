# Proposal: formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate

> Status: DRAFT_PENDING_P0_AUDIT_AND_FREEZE_REVIEW. 本 change 只做经验信道表征与
> 多层分解门；不实现 DE、MET、有限码、解码器、FER、qualification、promotion。
> 按 docs/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md 冻结执行。

## What

对项目已有到达时间戳、Alice/Bob 配对符号与冻结诊断证据做系统整理，建立可审计的
经验条件信道模型 `P(A|B,Z)`（A,B∈{0..1023} 为 1024-bin 原始符号，Z 为公共配置
元数据），并评估保留 1024-bin 高维原始符号、使用分层 NB-LDPC（GF(512)/GF(256)/
GF(32)/GF(16)/GF(8)）在信息论与信道结构上是否合理。

V25 只回答六问：错误规律、旧模型丢失的结构、GF(1024) 可逆分层、值得进入 DE 的
分层、GF(512)/GF(256) 主候选还是对照、delay/source/bin boundary/parity/jitter/
accidentals 的影响。

## Why

- V24 只排除了：在冻结 V17 聚合信道上、GF(1024)、bounded single-edge λ/ρ 空间内无
  预注册 DE 门候选。它没有排除 GF(512)/GF(256)、multilevel NB-LDPC、
  source-conditioned 信道、Bob-full-side-information、混合图码、true MET、重新校准
  delay 后的经验信道。
- 旧模型（QSC、独立 Gray 位面 product、translation-averaged）丢弃了真实时间戳误差
  的结构；需要一个经验条件信道来为下一阶段 DE 提供冻结的 channel initialization。

## Scope

- q=1024 原始符号保持 1024-bin 不变；只做符号标签的可逆分层（编码分层），与物理
  bin 合并（物理粗粒化，仅作单独对照）严格区分。
- 候选分层 F01–F05、labeling L01–L02 严格预注册。
- 经验信道主模型 `P(A|B,Z)`；诊断量 signed/modular delta、Gray XOR mask 只作诊断、
  不混用为解码信道。
- M0 误差图谱、M1 信道模型比较（C01–C06）、M2 delay/alignment 门、M3 chain-rule
  分解门、M4 架构选择（仅四个终态）。
- 数据切分：每 source/file 按时间 60/20/20（train/validation/holdout）。
- 输出：additive `nbldpc_v25_YYYYMMDD/run_<ts>/` 全套 JSON/CSV/NPZ + 只读 verifier。

## Out of scope

- 实现 true MET、多边类型 DE、有限长 NB-LDPC、解码器、FER、fresh qualification、
  promotion、运行 V24 搜索、扩大 λ/ρ 搜索、公开 residual/LSB、把 q512/q256 coarse
  SER 当作总 reconciliation FER。
- 用 Alice 真值选候选、用 holdout 选 mapping、修改冻结 Polar baseline、运行
  `experiments/run_e2e_pipeline.py` 或任何 `longrun_*`/`minrerun_*`/`routeA_*`。
- 未经新授权运行重型 raw pipeline（需要重新读 `.ttbin` 时必须先提交精确输入/命令/
  资源/输出目录给主线程）。

## Decision states (M4)

- `pass_ready_for_de_change`
- `fail_no_stable_factorization`
- `blocked_insufficient_joint_data`
- `blocked_alignment_unresolved`

V25 PASS 仅允许提出 V26，不得自动启动 V26。

## Claim boundary

V25 不得宣称已经得到可用 NB-LDPC、已满足 FER、已达 f≤1.3、GF(512)/GF(256) 已被
证明可收敛、已完成 qualification/promotion。参考目标码率
`R_i_ref = 1 - 1.3*H_i/a_i` 只是 f=1.3 下的信息论参考，不代表 DE 可达。
