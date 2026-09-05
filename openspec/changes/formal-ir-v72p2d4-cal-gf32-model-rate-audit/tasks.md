# D4 任务与验收（PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED）

状态：本轮只审查计划，不实现、不运行 decoder、不读 VAL/parquet、不创建结果目录、不改 `src/experiments/tools/results` 或既有输出。`base/accepted_plan/implementation SHA` 只做 Git 绑定，不做内容校验。

计划文件固定为（独立 Plan Review 只审这 4 文件）：

1. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/proposal.md`
2. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/design.md`
3. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/tasks.md`
4. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/specs/spec.md`

## D4T0：结构、无副作用与禁止

- D4T0-1：未来实现至多审计脚本 + focused test 各一个；`py_compile`/import 无副作用；测试 decoder/path 只能显式注入 fake。
- D4T0-2：断言数据为 `CAL702..1725` 1024 帧 frame-blocked 4 折 nested（outer `F0=702..957 / F1=958..1213 / F2=1214..1469 / F3=1470..1725` 各 256 帧，TEST=1折连续256帧/TRAIN=其余768帧，TRAIN 内 3 确定性 inner folds 各 256 帧，帧序唯一，禁 shuffle/逐行随机/VAL）；VAL loader 调用恒 0。机械断言：outer/inner 零交集、inner⊆TRAIN、3 inner folds两两互斥且并集=所属outer TRAIN（768帧）、TEST=256、四 TEST 并=702..1725、每帧 256 pairs。
- D4T0-3：断言 `counts[a,b]` 轴约定（axis0=Alice/axis1=Bob）唯一；转置反例测试存在。
- D4T0-4：断言禁 VAL/decoder/新矩阵/hash：源码探针 `VAL1726 / decode_row_layered / zeros((16,1024)) / checksum|sha256|md5|compute_tag` 在审计路径零命中（测试注释与文档引用除外，需显式 allowlist）。

## D4T1：counts、链式与模型单元（T0/T1 级）

- D4T1-1：canonical counts 轴测试：不对称可手算联合分布分别验证 `P(A|B)/P(U1|B)/P(U2|U1,B)`；转置输入必须失败；对称/只验归一化不算证据。
- D4T1-2：链式测试：`|CE_joint-CE_L1-CE_L2|<1e-10`（log2，float64），自然 log/decorder 转换不进入本审计。
- D4T1-3：M0 pin 为 train 边际（`P_M0(a)=count_TRAIN(A=a)/n_TRAIN`，均匀 `P=1/1024` 另记 `uniform_lower_bound_descriptive` 下界对照不参选）+ M1/M2 各有唯一估计子 + 平滑/回退声明（含 lambda 反泄漏统一口径：lambda（Laplace/回退/收缩系数）为冻结常量或仅由对应 TRAIN 统计确定，禁 TEST/VAL/held-out 调参、早停或选模，inner 若用 lambda 只看 inner TRAIN 拟合 + inner held-out CE，不得窥视 outer TEST）+ unseen 行为 + 手算小例 + floor 精确 `1e-300`（先归一再 `max(P,1e-300)`）；M3 本轮直接记录 `M3_EXIT_AMBIGUOUS` 并从比较中移除（有显式退出记录，不算 FAIL，M0–M2 闭合）。数学合同一致性：counts 轴 + 链式 + CE + 预算公式同口径。
- D4T1-4：seen/unseen 划分测试：覆盖率 `seen_frac` 复算一致；unseen 不得删样本；`CE_seen/CE_unseen` 口径显式。

## D4T2：CV 审计、R5 复现、预算与路线（T2 级，CAL-only）

- D4T2-1：CAL-only 4 折 CV：outer/inner fold 零重叠（帧级 disjoint 全覆盖，inner⊆TRAIN，3 inner folds两两互斥且并集=所属outer TRAIN（768帧））、counts 只用对应 train、test 只算 CE；报告每折 `CE_L1/CE_L2_oracle/CE_joint + n_train/n_test + seen_frac/seen/unseen CE` 及 mean/std/max-min；附机械断言（TEST256/四并全集/每帧256/inner互斥并=TRAIN）。
- D4T2-2：R5 复现门：同 fixture 同口径复算 `6.422/5.083/11.505`，各 `|Δ|<1e-6` 且链式 `<1e-10`；`REAL_CAL_EXACT_MATCH=false`（R5 来源 synthetic，只核公式复现）；失败即 `BLOCKED`并记根因（口径/数据域/实现），不进选择。
- D4T2-3：选择规则：`mean(CE_joint)` 最小 + `Δ<0.02 bit/symbol` 简单优先（R1冻结：按实现`SELECT_DELTA=0.02`冻结，不可调；M0<M1<M2，M3 已退出不参选）+ 稳定性数值门限（`std>0.10 或 max-min>0.20 bit/symbol` 即不稳定，降级并显式标记）；输出名次表，不自动改矩阵/decoder 参数。
- D4T2-4：预算表：`N=1024 symbols/block`，`f∈{1.0,1.1,1.2,1.3}`，`rows=ceil(N*CE*f/5)`；对照历史 `16/200/216` 行（`80/1000/1080` bit）；`required>available` 只记 `MODEL_BUDGET_MISMATCH`；L1 不足禁只加 L2。
- D4T2-5：路线判定：按 design §8 输出 A/B/C 互斥穷尽唯一结论及依据（`A=fit@1.3，C=mismatch@1.0，B=fit@1.0∧mismatch@1.3`，典型 `f=1.0/1.1 fit 而 f=1.3 mismatch`，以选中模型 mean 计，分层 margin）；A 不授权真实诊断，B/C 暂停通用化。
- D4T2-6：审计输出仅标量（fold 表 + mean/std + 预算表 + 路线结论）；无 VAL、无 decoder 调用（`decoder_calls=0`）、无正式输出根、`published_bits=0`。

## 完成与停止条件

- 完成：4 计划文件一致、`REAL_EXECUTION_AUTHORIZED=false`、`DECODER_EXECUTED=false`、`VAL_LOADER_CALLS=0`，停于 `NEXT_GATE: INDEPENDENT_PLAN_REVIEW`。
- 停止（任一即 `BLOCKED`）：counts 不唯一、M0–M2 不可手算验证、`M3_EXIT_AMBIGUOUS` 无显式退出记录、CV 读 VAL、任何 decoder 调用、R5 复现失败、链式超 `1e-10`；不猜测、不替代、不重试。
