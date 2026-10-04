# INDEPENDENT_ACCEPTANCE — NB-LDPC L1D2 Stage-2 synthetic batch (DECIDE, n128 only)

- Cycle: `NBLDPC-L1D2-SYNTH-BATCH`（NB-LDPC L1-degree2 Stage-2 合成批次，DECIDE）。
- Track: **DECIDE**。三文件形式 `PREREG_AND_AUTH.md`（冻结）/ `RESULT.md` / 本文件。
- Date: 2026-09-30。
- Branch: `formal-ir-v72p1-addendum-clean`；`git_head=23183c73fd4b1597f2c42a6e9b06fa2de4402b9c`（provenance only，非执行锁）。

## §1 接受范围（仅 n128）

本次接受**仅覆盖 n128 单批**（out-root `workspace/nbldpc-l1d2-s2c-n128-b07b0f91`，S1 UUID b07b0f91；planned_pairs=96；chains=192；decoder_calls=384，per-width 口径）。

n256 out-root `workspace/nbldpc-l1d2-s2c-n256-5b2240a0`**未执行**、未接受，不在本文件接受范围内。

## §2 独立复核依据

复核依据：T6 产物（§6 所列 5 文件）+ 冻结包 `PREREG_AND_AUTH.md` + T8 独立重算（全部从 `frame_records.csv` 独立重算，未重跑批次、未运行 decoder）。

T8 独立复核 10 项，结论 **10/10 PASS，无 BLOCKER**：

1. Δ/Δ_g 重算：由 `frame_records.csv` 独立重算，每图 Δ_g 与总 Δ 与聚合文件逐值一致 — PASS。
2. 泄漏可加性：`l1_syn_bits` / `l2_syn_bits` / `extra_parity_bits` / `verify_tag_bits` / `other_public_bits` 分解与产物一致；单帧 1110 位，无 double-count、无退账 — PASS。
3. `accepted_wrong` 隔离：192/192 全 False，单列隔离，从未并入 success — PASS。
4. `is_success` 公式：`is_success = pair_exact ∧ verify_accept ∧ ¬accepted_wrong` 成立，与 `arm_summary.success` 一致 — PASS。
5. syndrome/exact 关系：syndrome 从未替代 exact；双向错位各 0 — PASS。
6. per-source 分解：96 组 × 2 臂 = 192 行可追溯；C/S 同 `call_seed` 共享 — PASS。
7. transfer 注记裁定：见 §5 — PASS（以产物值为准）。
8. 口径/schema/命令：`decoder_calls=384` 为 per-width 行（768 仅为 both-widths total 标签行）；`frame_records.csv` 表头与 PREREG §4 冻结顺序一致；`manifest.json` / `command_log.txt` 齐全且与 PREREG §2 命令一致；`oracle=false` / `fake_decoder=false` / `canary=false` — PASS。
9. 资源/授权边界：总 wall 156.79 s（帽 7200）；RSS ≈136 MiB（帽 4 GiB）；最大配对总耗时约 3.55 s（<120 s）；逐帧 `wall_s` 不能恢复单链精确耗时，但配对总和 <120 s 可证明组成链各自 <120 s；`stop_reason` 空（全量完成）；`resource_abort` 0；`transfer_blocked` 0；执行在 DEC-1 n128 范围内 — PASS。
10. 阈值距离（非显著性或稳健性检验）：要使冻结门槛满足，Δ 净差须从 +1 增至 +6（至少 +5），正差图须从 2/6 增至至少 4/6（至少 +2 图）。这只是冻结阈值的算术距离，不估计抽样波动，也不构成统计稳健性结论 — PASS（仅阈值算术）。

## §3 接受判定

**判定：ACCEPTED**（`RESULT.md` 可固化；批次记账、隔离、披露、资源、授权边界均合规）。

- 记账：Σ control pair_exact 49；Σ candidate pair_exact 50；总 Δ=+1；Δ_g>0 图数 2/6（3701 +1、3705 +1；3703 −1；3702/3704/3706 为 0）。
- 隔离：`accepted_wrong` 0 行且单列隔离（CONTROL 0 / CANDIDATE 0）。
- 披露：93 例 nonconverged（47+46）全额 attempted 披露、保留，无退账。
- 资源：wall 156.79 s（帽 7200）；RSS ≈136 MiB（帽 4 GiB）；最大配对总耗时约 3.55 s（<120 s）；逐帧 `wall_s` 不能恢复单链精确耗时，但配对总和 <120 s 可证明组成链各自 <120 s；`stop_reason` 空；`resource_abort` 0；`transfer_blocked` 0。
- 授权边界：在 DEC-1 n128 范围内（n256 未执行）。

`arm_summary`（照抄）：CONTROL 96/49/49/accepted_wrong 0/nonconverged 47/resource_abort 0/transfer_blocked 0；CANDIDATE 96/50/50/0/46/0/0。

## §4 COND-3 机械判定结果

**COND-3 结果：NOT MET**（Δ=+1<6；2/6<4/6；零违规）→ 按冻结规则**不进入 n256**，STOP 条件臂。

（PREREG §7 机检程序：Δ≥6？否；≥4/6 图 Δ_g>0？否；accounting/undetected/授权/资源违规：均无。）

## §5 冻结措辞结论（原文语义，非路线判断）

因 COND-3 未满足 → 不进入 n256，记"此冻结试验未给出足够机制信号"；**不得**写成"NB-LDPC 不行"或任何路线否定。

两臂成功率约 51–52%（49/96、50/96）既非全零地板也非对照近满天花板，记录为"可区分但幅度小"（观察，不作因果或显著性主张）。

**transfer 注记裁定**：T6 报告曾称 `transfer_invoked` 全 False，产物实测**全 True（192/192）**，与 `transfer_blocked=0` 自洽 → L2 确已执行（`l2_syn_bits=520≠0`），`u2_exact` 来自真实 L2 译码，无"未做 L2 记成功"问题。**以产物值为准，T6 该笔误不得再被引用**。

## §6 Claim ceiling（原文）

本次接受不支持任何 FER/SKR/qualification/promotion/publication 结论；仅支持"是否值得拟定下一包"的判断。

（PREREG §11 同样冻结：No FER/SKR/qualification/promotion/publication conclusion; the batch supports only "whether a next packet is worth drafting".）

## §7 保留失败与观察

- 93 例 nonconverged（47+46）全额 attempted 披露、保留。
- Δ_g ∈ {−1,0,+1}，幅度小（观察，不作因果或显著性主张）。
- transfer 注记差异已裁定（以产物为准，见 §5）。

## §8 证据与 provenance

- 产物根：`workspace/nbldpc-l1d2-s2c-n128-b07b0f91/`，5 文件：`manifest.json`、`frame_records.csv`（193 行含头）、`graph_records.csv`（7 行）、`arm_summary.csv`、`command_log.txt`。
- `git_head=23183c73fd4b1597f2c42a6e9b06fa2de4402b9c`（provenance only，非执行锁）。
- 执行命令：引用 PREREG §2 n128 命令（`command_log.txt` 与之 modulo `PYTHONPATH=` env 前缀一致），此处不复述全文。
- n256 根 `workspace/nbldpc-l1d2-s2c-n256-5b2240a0` 未执行，无产物。

## §9 独立性声明与签名

独立复核人 ≠ 执行操作员：T6 由 coder-fast 执行，T8 复核由 reviewer-go 独立会话完成，本文由 coder-doc 记录；**不得**自我接受。

Independent reviewer: reviewer-go (T8, session ses_f11aea008ffecblPITfz6YguYd); recorded by coder-doc (T9).

Date: 2026-09-30.

## §10 后续（仅流程性，不作科学建议）

- n256 需 COND-3 满足 + 单独授权（本次 NOT MET，未授权）。
- 是否拟定下一包由主线程裁决。
- 归档与 memory triage 由 T10 处理。
