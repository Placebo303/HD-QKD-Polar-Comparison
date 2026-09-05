# D4 CAL GF32 模型码率审计计划（只建计划不实现）

- Change：`formal-ir-v72p2d4-cal-gf32-model-rate-audit`
- Predecessor：`formal-ir-v72p2d3-gf32-contrast`（R5 数学接口与码率审计）
- Base：`main HEAD at plan creation`（Independent Plan Review 时 pin，不复用 stale SHA；D3 base `e094f7e` 仅作前序参照）
- Cycle：`V72P2D4-CAL-GF32-MODEL-RATE-AUDIT`
- Lifecycle：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 本 change 只建计划不实现：不写生产代码、不运行 decoder、不读 VAL、不创建结果目录、不授予任何执行。

`base_sha/accepted_plan_sha/implementation_sha` 只承担 AGENTS 要求的 Git 版本绑定，不承担数据或 artifact 内容校验。本计划不新增任何数据或 artifact 内容摘要、签名、checksum/hash 字段。

Ponytail lite：未来实现至多算法审计脚本 + focused test 各一个；复用 V54 prior 链口径；不用框架、缓存、锁、retry、持久化。不预设优胜模型。

## Goal

在 `CAL702..1725`（1024 帧）上冻结一次 CAL-only、frame-blocked 4 折 nested CV 的 GF32 两层模型码率审计，回答“当前数据域在历史预算下是否装得下”：

1. 冻结 `CAL702..1725` 1024 帧按 frame blocked 4 折 nested CV：outer `F0=702..957 / F1=958..1213 / F2=1214..1469 / F3=1470..1725` 各 256 连续帧；外层每次 `TEST=1折连续256帧 / TRAIN=其余768帧`；TRAIN 内再切 3 确定性 inner folds（各 256 连续帧，帧序唯一确定，禁 shuffle/逐行随机/VAL）；counts 只建在对应 TRAIN 上。机械断言：outer TEST∩TRAIN=∅、inner TEST∩TRAIN=∅、inner folds⊆outer TRAIN、3 inner folds两两互斥且并集=所属outer TRAIN（768帧）、每 TEST=256 帧、四 TEST 并=`702..1725`、每帧=256 pairs。
2. 冻结 canonical `counts[a,b]=count(Alice=a,Bob=b)`（axis0=Alice，axis1=Bob）与 `P(A|B) / P(U1|B) / P(U2|U1,B)` 链式（`U1=high`、`U2=low`、`s=low+32*high`）。
3. 冻结模型族 M0–M2 闭合 + `M3_EXIT_AMBIGUOUS`（本轮直接记录退出，不再候选）：M0 pin 为 train 边际（与 B 无关经验边际，均匀另记下界对照不参选）；M1/M2 同 design §3；数学合同与 lambda 反泄漏统一口径：lambda（Laplace/回退/收缩系数）为冻结常量或仅由对应 TRAIN 统计确定，禁 TEST/VAL/held-out 调参、早停或选模，inner 若用 lambda 只看 inner TRAIN 拟合 + inner held-out CE，不得窥视 outer TEST。
4. 冻结指标 CE（含 seen/unseen 分解）与链式检查 `|CE_joint-CE_L1-CE_L2_oracle|<1e-10`。
5. 先复现 R5：`6.422 / 5.083 / 11.505`（`CE_L1 / CE_L2_oracle / CE_joint`）；R5 来源为 synthetic 故 `REAL_CAL_EXACT_MATCH=false`，只以同 fixture 复现公式口径核对（同 counts 轴约定 + 同链式 + 同 CE 定义），不作真实 CAL 精确匹配断言；再做 M0–M2 审计（M3 本轮已直接 `M3_EXIT_AMBIGUOUS` 不参选）。根因：若复现偏离，先判口径/数据域差异，不得调参凑数。
6. 冻结选择规则：fold-mean 最小 + 简单优先 + 稳定性。
7. 冻结预算：`N=1024 symbols/block`，`f∈{1.0,1.1,1.2,1.3}`，`rows=ceil(N*CE*f/5)`，对照历史 `16 / 200 / 216` 行（即 `80 / 1000 / 1080` bit）。
8. 冻结路线 A/B/C 判定。不读 VAL、不调 decoder、不造新矩阵、不引入 hash。

## Non-Goals

- 不读 `VAL1726..1729` 或任何 VAL；不用 VAL 选参、调参、确认或回灌。
- 不运行 decoder（含 V35/V54 真核、fake 除外由测试显式注入）；不发布 syndrome/tag；不度量 FER/纠错成功。
- 不构造新矩阵（不造 H1/H_base/joint/total，不替代历史 QC-cyclic-projective H1）；不修 terminal writer。
- 不引入 checksum/hash/tag/签名或内容校验字段；registry 多余键忽略。
- 不做跨 session 推广、扩维（`d=256/512` 仍为 backlog）、SKR/信息极限断言、方法定级。
- 不直接进入匹配合成信道或预注册真实诊断；D4 只输出审计结论与路线判定。

## 冻结设计摘要

- 数据：同 session `20260123_1M_600k_0dB` 的 `CAL702..1725`（1024 帧，每帧 256 pairs，共 262144 symbols）。VAL 加载调用必须为 0。
- CV：frame-blocked 4 折 nested：outer 按帧序连续切 `F0=702..957 / F1=958..1213 / F2=1214..1469 / F3=1470..1725`（各 256 帧）；外层 `train=3折768帧 / test=1折连续256帧`；TRAIN 内 3 确定性 inner folds（各 256 连续帧，禁 shuffle/逐行随机/VAL）；counts 与模型拟合只用对应 train；在 test 算 CE；模型选择只用外层 mean（nested 语义：test 不进拟合与选参）；确定性划分，不跨帧打散 symbols。机械断言：outer/inner 零交集、inner 属 TRAIN、3 inner folds两两互斥且并集=所属outer TRAIN（768帧）、TEST=256、四 TEST 并=702..1725、每帧 256 pairs。
- 链式：`P(U1|B)` 为 `P(A|B)` 按 `U2` 边际化；`P(U2|U1,B)` 为按 `(U1,B)` 条件化；`prior_l2=q@P` 口径保留但本审计 `CE_L2_oracle` 用真实 `U1`（仅分层预算诊断，非生产性能）。Floor 精确 `1e-300`（非量级）：概率先正常归一，再 `max(P,1e-300)` 后取 log，只保护 log。
- 模型：M0–M2 闭合 + 本轮直接 `M3_EXIT_AMBIGUOUS`（冻结，不再候选，互斥）：M0 pin 为 train 边际（`P_M0(a)=count_TRAIN(A=a)/n_TRAIN`，与 B 无关），均匀 `P=1/1024` 另记 `uniform_lower_bound_descriptive` 下界对照不参选、不进选择与路线；M1/M2 同 design §3；lambda 统一口径同 Goal 3；M3 本轮无唯一定义，直接记录退出，审计在 M0–M2 上闭合，不猜测替代。
- 指标：`CE=-mean(log2 P)`（bit/symbol）；seen/unseen 按 held-out 的 Bob 值是否在 train 出现划分，报告覆盖率与分 CE；链式误差 `<1e-10`。
- R5 复现：同 fixture 同口径复算 R5 三数 `6.422/5.083/11.505`，容差 `1e-6`（链式另按 `1e-10`）；R5 来源 synthetic 故 `REAL_CAL_EXACT_MATCH=false`，只核公式复现，不作真实 CAL 精确匹配；失败即 `BLOCKED`并记根因（口径/数据域/实现），不进入 M0–M2 比较。
- 选择：`mean(CE_joint)` 最小为主；接近（`Δ<0.02` bit/symbol，R1冻结：按实现`SELECT_DELTA=0.02`冻结，不可调）时简单优先（M0<M1<M2，M3 已退出不参选）；稳定性数值门限冻结：`CE_joint` 跨外层折 `std>0.10 bit/symbol 或 max-min>0.20 bit/symbol` 即不稳定，降级并显式标记，不得仅凭单折最优选中。
- 预算：`N=1024 symbols/block`，`required_bits=N*CE*f`，`rows=ceil(/5)`；分层对照 `L1:16行/80bit、L2:200行/1000bit、Total:216行/1080bit`（`1080/1024=1.0546875 bit/symbol`）；`required>available` 只记 `MODEL_BUDGET_MISMATCH`。
- 路线 A/B/C 互斥穷尽（以选中模型 mean 计，同一口径）：A=装得下（`f=1.3` 时 L1/L2/Total 全层 fit）→ 允许谈匹配合成信道；B=仅低 f fit（`f=1.0` 时全层 fit 但 `f=1.3` 时任一层 mismatch，即 ¬A∧¬C，典型 `f=1.0/1.1 fit 而 f=1.3 mismatch`）→ 只允许重预算/小诊断计划，不进真实诊断；C=装不下（即使 `f=1.0` 仍任一层 mismatch）→ 停止，后继仅 backlog。L1 不足不得只加 L2。
- 禁止：VAL、decoder、新矩阵、hash/checksum/tag、正式输出、执行授权。

完整数学、任务、验收见同目录 `design.md`、`tasks.md`、`specs/spec.md`。
