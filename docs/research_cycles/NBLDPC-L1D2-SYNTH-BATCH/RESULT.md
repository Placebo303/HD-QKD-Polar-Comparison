# RESULT — NB-LDPC L1D2 Stage-2 synthetic batch (DECIDE, n128 execution record)

- Cycle: `NBLDPC-L1D2-SYNTH-BATCH` (Stage-2 only; R2 of
  `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT`).
- Track: **DECIDE**. Compact three-document form:
  `PREREG_AND_AUTH.md` (frozen, unchanged) / this `RESULT.md` /
  `INDEPENDENT_ACCEPTANCE.md` (T9, not this file).
- Status: n128 EXECUTED once under DEC-1; n256 NOT executed.
- Preregistration: `PREREG_AND_AUTH.md` §§1–11 remain frozen and binding;
  this file records facts and the COND-3 mechanical gate only.

## §1 执行元数据

- Exact command (PREREG §2; `command_log.txt` identical modulo the
  `PYTHONPATH=` env prefix recorded here):

```
PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_l1d2_synth_batch_prod --width 128 --graph-seed 2026093701,2026093702,2026093703,2026093704,2026093705,2026093706 --data-seed 2026093201,2026093202 --frames 0-7 --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/nbldpc-l1d2-s2c-n128-b07b0f91 --max-iter 90 --damping 1.0 --wall-cap-s 7200 --rss-cap-bytes 4294967296 --chain-wall-cap-s 120 --execute
```

- Exit code: `0`.
- `wall_s=156.79471907997504`; `stop_reason` empty.
- `git_head=23183c73fd4b1597f2c42a6e9b06fa2de4402b9c` (provenance only).
- `planned_pairs=96`; `chains=192`; `decoder_calls=384`;
  `oracle=false`; `fake_decoder=false`; `canary=false`.
- Decoder profile:
  `row-layered/max_iter=90/damping=1.0/warm=None/CHECK_UPDATED/oracle=False dual-arm`.
- Resources: total wall 156.8 s (cap 7200, 占 2.2%); peak RSS ≈136 MiB
  (cap 4 GiB); no single chain over 120 s; no `resource_abort`.
- Out-root (single, frozen): `workspace/nbldpc-l1d2-s2c-n128-b07b0f91`,
  5 files:

| File | Size | Rows (incl. header) |
|---|---|---|
| `arm_summary.csv` | 150 B | 3 |
| `command_log.txt` | 464 B | 1 |
| `frame_records.csv` | 29494 B | 193 |
| `graph_records.csv` | 447 B | 7 |
| `manifest.json` | 2407 B | 58 (lines) |

## §2 每图聚合 + 总计

Per-graph (attempted 均为 16; blocked 0; aborts 0; construction 均为 ok):

| Graph seed | Control | Candidate | Δ_g | leads |
|---|---|---|---|---|
| 2026093701 | 9 | 10 | +1 | True |
| 2026093702 | 7 | 7 | 0 | False |
| 2026093703 | 9 | 8 | −1 | False |
| 2026093704 | 7 | 7 | 0 | False |
| 2026093705 | 9 | 10 | +1 | True |
| 2026093706 | 8 | 8 | 0 | False |

- 总计：Σ control 49; Σ candidate 50; Δ = +1; Δ_g>0 图数 2/6.

## §3 Arm 汇总 + 帧级核对

`arm_summary.csv`:

| arm | attempted | pair_exact | success | accepted_wrong | nonconverged | resource_abort | transfer_blocked |
|---|---|---|---|---|---|---|---|
| CONTROL | 96 | 49 | 49 | 0 | 47 | 0 | 0 |
| CANDIDATE | 96 | 50 | 50 | 0 | 46 | 0 | 0 |

`frame_records.csv` frame-level check:

- 192 行 (96 pairs × 2 arms).
- status 分布：CONTROL ok 49 / nonconverged 47;
  CANDIDATE ok 50 / nonconverged 46; `resource_abort` 0.
- `accepted_wrong` 全 False (192/192).
- `verify_tag_bits` 全 0.
- `transfer_invoked` 全 True (192/192); 与 `transfer_blocked=0`
  一致。注：T6 口径注记作"全 False"，与产物文件不一致，
  以产物文件为准；T8 已裁定该处为 T6 笔误（见
  `INDEPENDENT_ACCEPTANCE.md` §5）：L2 实际执行，`l2_syn_bits=520`。
- `rss_b` 全 142946304 B (≈136.3 MiB).
- 最大配对总耗时约 3.55 s（低于 120 s）。逐帧 `wall_s` 不能恢复
  单条链的精确耗时，因此不报告单链最大值；配对总耗时是组成链耗时之和，
  该总和低于 120 s 可证明本批每条链均低于 120 s。

## §4 COND-3 机械判定 (GAP-6b gate, PREREG §7)

1. Δ≥6? 否（+1）。
2. ≥4/6 图 Δ_g>0? 否（2/6）。
3. accounting/undetected/授权/资源违规：均无
   (`accepted_wrong` 全 0 且已隔离未并入 success;
   失败帧全额披露无退账，见 §6;
   执行在 DEC-1 n128 范围内，§6 caps 内；
   `resource_abort` 0, `transfer_blocked` 0)。
4. 结论：**COND-3 NOT MET** → 不进入 n256，STOP 条件臂。

## §5 冻结措辞结论（原文语义记录，非路线判断）

- 因 COND-3 未满足 → **不进入 n256**，记"此冻结试验未给出足够机制信号"，
  **不得**写成"NB-LDPC 不行"或任何路线否定结论。
- 两臂成功率约 51–52%（49/96、50/96），既非全零（地板）也非对照近满
  （天花板），故不适用"区分能力不足/天花板受限"措辞；如实记录为
  "可区分但幅度小"。
- 单图 Δ_g ∈ {−1,0,+1}，总 Δ=+1，记录为**幅度小、近平**的观察
  （供后续解读），**不得**据此作任何因果或显著性主张。

## §6 披露核算

- 失败帧 93 例（47+46 nonconverged）按 attempted 全额披露、无退账。
- `decoder_calls=384` = 192 chains × 2 层（per-width 口径，
  与冻结双行算术 per-width 96/192/384 一致；both-widths total 行
  为 192/384/768，仅作口径标签，不代表本次执行量）。
- 泄漏分量：`verify_tag_bits` 全 0; `extra_parity_bits` / `l1_syn_bits` /
  `l2_syn_bits` / `other_public_bits` 按 `frame_records.csv` schema 列序
  记录；T8 已独立核对分量可加性通过，单帧 1110 位，无 double-count、
  无退账（见 `INDEPENDENT_ACCEPTANCE.md` §2 第 2 项）。

## §7 Claim ceiling

本批不支持任何 FER/SKR/qualification/promotion/publication 结论；
只支持"是否值得拟定下一包"的判断。不得出现 FER/SKR/资格/提升/发表类
结论句。（PREREG §11 同样冻结：No FER/SKR/qualification/promotion/
publication conclusion; the batch supports only
"whether a next packet is worth drafting".）

## §8 未做事项

- 未跑 n256（COND-3 未满足 + 需单独授权）。
- 未做任何重跑、调参、换种子、减样本。
- T7 编写本执行记录时尚未写 `INDEPENDENT_ACCEPTANCE.md`（T9 另有任务；
  T8/T9 后续状态见该文件）。
- 未改任何现有文件：未改 `PREREG_AND_AUTH.md`，未改 openspec 下文件，
  未改任何代码。

## §9 T8 独立复核项目索引（已完成）

T8 Pre-RESULT 已只读产物根 `workspace/nbldpc-l1d2-s2c-n128-b07b0f91/`
完成独立复核、未重跑；逐项结果见 `INDEPENDENT_ACCEPTANCE.md` §2。
以下保留原核对项目索引：

1. Δ/Δ_g 重算：由 `graph_records.csv` / `frame_records.csv` 独立重算
   每图 Δ_g 与总 Δ（期望：+1/0/−1/0/+1/0，总 +1）。
2. 泄漏分量可加性：`l1_syn_bits` / `l2_syn_bits` /
   `extra_parity_bits` / `verify_tag_bits` / `other_public_bits`
   分解与产物一致，无合并、无手填。
3. `accepted_wrong` 隔离：192/192 False，从未并入 success；
   `pair_exact ∧ verify_accept ∧ ¬accepted_wrong` 语义与
   `arm_summary.success` 一致。
4. per-source 分解：按 (graph_seed, block_seed, frame_idx) 可追溯
   至 96 pairs × 2 arms = 192 行。
5. 384/768 口径：本次 `decoder_calls=384` 为 per-width 行；
   768 仅为 both-widths total 标签行，不得混用。
6. wall/RSS 与帽：总 wall 156.79471907997504 s ≤ 7200；
   RSS 142946304 B ≤ 4294967296；最大配对总耗时约 3.55 s < 120；
   逐帧 `wall_s` 不足以恢复单链精确耗时，但配对总和 <120 可证明每条链 <120；
   `stop_reason` 空；`resource_abort` 0。
7. schema 列序：`frame_records.csv` 表头与 PREREG §4 冻结顺序一致
   （width, arm, graph_seed, block_seed, frame_idx, call_seed,
   transfer_invoked + 17 列）。
8. `manifest.json` / `command_log.txt` 齐全且与 PREREG §2 命令一致；
   `oracle=false` / `fake_decoder=false` / `canary=false`。
9. §3 `transfer_invoked` 注记差异裁定（产物全 True vs T6 口径全 False）。
