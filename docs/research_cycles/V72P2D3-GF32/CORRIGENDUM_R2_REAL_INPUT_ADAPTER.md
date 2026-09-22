# V72P2D3-GF32 Corrigendum R2 — REAL INPUT ADAPTER

- Cycle: `V72P2D3-GF32`（R2 真实输入适配，不开新 cycle）。日期: 2026-09-04。
- 性质: 仅文档计数纠正 + R2 prepare-only 适配说明。不重新计算、不运行 decoder、不重跑 G、不调参、
  不覆盖 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`
  四文件（如存在则 untouched）、不读逐符号密钥数据作发布、不创建 `run_01`。
- 历史原文（`RESULT_SUMMARY.md` / `OPERATOR_RETURN.md` / `cycle_state.yaml` 相关条目）保持原样不回写，
  以本文件为准进行纠正阅读。本文件不授予真实 decoder 执行。
- 状态: `ACCEPTED_FOR_IMPLEMENTATION / PREP_ONLY / REAL_EXECUTION_NOT_AUTHORIZED`。
  `real_execution_authorized=false`、`formal_execution_authorized=false` 保持。

> R1/R2 编号澄清：R1 指此前 fail-closed invocation（`OPERATOR_RETURN.md` exit2，
> `registry/frames/matrices=None`，parquet 未打开，真 decoder 未调用，生产根未创建）。
> R2 指当前真实输入适配修复（registry->parquet 受限读->CAL/VAL->prior->block->A->words->
> matrix/syndrome 形状校验->workspace READY，decoder 0），避免周期编号混淆。
> V72P2D2-TRIAGE 的 `CORRIGENDUM_R1_DRAFT.md` 内容已迁入本文件，原 draft 删除，不同时保留两份。

## 1. 纠正对象：invocation 计数误作 decoder 计数

- 既有 `execution_count_completed=1/1`（V72P2D3-GF32 fail-closed）记录的是单次 invocation 授权消耗，不是 decoder 消耗。
- 该次止于首个真实 decoder 之前的门控失败，未调用真实 decoder，
  未读 raw/parquet 逐符号数据，未发布 syndrome/tag：
  `exit=2`（`real chain needs injected registry/frames/matrices; parquet is never opened here`
  runner production gate，`PermissionError` 路径）。
- `real_decoder_executed=false`、`decoder_executed=false` 保持。

## 2. 三级计数区分（纠正阅读口径）

- `invocation_attempts`：进入 `require_real_authorization` 门控的调用次数。
- `prep_attempts`：通过门控、进入 prep 的次数。
- `decoder_attempts`：进入首个真实 decoder arm 的次数（G 任一 stage `attempted=true`）。
- V72P2D3-GF32 R1（fail-closed）：invocation 1 / prep 0（门控前止）/ decoder 0。
- V72P2D3-GF32 R2（prepare-only）：invocation 0（不消耗授权）/ prep 1（workspace READY）/
  decoder 0（`decoder_calls=0`，`published_bits=0`）。

## 3. `decoder_executions_authorized` 消耗规则（仅前瞻，不追认扣减）

- 仅首个真实 decoder 调用前的原子检查点消耗 `decoder_executions_authorized`
  （检查通过即扣减一次，失败即停不进 decoder）。
- gate 拒绝 / prep 失败 / prepare-only 不消耗 `decoder_executions_authorized`；
  已记录的 `execution_count_*=1/1` 历史值不改写、不折算。
- 本规则为纠正说明，不新增 SHA/checksum/签名/内容校验字段；
  Git 版本绑定仍仅作版本来源。

## 4. `real=false` 保持与边界

- `real_execution_authorized=false`、`formal_execution_authorized=false`、
  `formal_protocol_qualification=false`、`scientific_promotion=false`、
  `no_run_01=true` 保持；
  `undetected` 隔离（从不并入 success/FER）保持；无 FER/SKR/推广断言。
- R2 prepare-only 输出仅 `workspace` 下 `prepare_summary.json`（标量-only），
  不创建正式输出根四文件，不发布 syndrome/tag，不读逐符号密钥数据作发布。

## Evidence links

- Previous fail-closed result: [RESULT_SUMMARY.md](./RESULT_SUMMARY.md)
- Previous operator return: [OPERATOR_RETURN.md](./OPERATOR_RETURN.md)
- Current lifecycle state: [cycle_state.yaml](./cycle_state.yaml)
- R2 prepare-only evidence: [PREP_ONLY_SUMMARY.json](./PREP_ONLY_SUMMARY.json)
- R2 independent implementation review: [R2_IMPLEMENTATION_REVIEW.md](./R2_IMPLEMENTATION_REVIEW.md)
