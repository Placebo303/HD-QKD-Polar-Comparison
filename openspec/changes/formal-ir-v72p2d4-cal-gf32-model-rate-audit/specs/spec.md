# D4 Spec Delta：CAL GF32 模型码率审计（CAL-only）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 delta 绑定 predecessor D3 R5，不合并、不替代 D1/D2/D3 行为。本周期不实现、不运行 decoder、不读 VAL、不创建输出。

`base_sha/accepted_plan_sha/implementation_sha` 仅 Git 绑定，不得添加内容校验字段。不预设优胜模型。

## S-COMMON：数据与 CV

- S-COMMON-01：审计 SHALL 只用同 session `20260123_1M_600k_0dB` 的 `CAL702..1725`（1024 帧）；VAL loader 调用 SHALL 为 0。
- S-COMMON-02：划分 SHALL 为 frame-blocked 4 折 nested：outer 按帧序连续 `F0=702..957 / F1=958..1213 / F2=1214..1469 / F3=1470..1725` 各 256 帧；外层每次 `TEST=1折连续256帧 / TRAIN=其余768帧`；每个 outer TRAIN 内 SHALL 再按帧序连续切 3 确定性 inner folds（各 256 帧，禁 shuffle/逐行随机/VAL）；counts 与拟合 SHALL 只用对应 train；test SHALL 只算 CE；模型选择 SHALL 只用外层 mean。
- S-COMMON-03：fold 分配 SHALL 确定性（帧序唯一）；报告 SHALL 含每折 `n_train/n_test`。机械断言 SHALL 全满足：outer TEST∩TRAIN=∅、inner TEST∩TRAIN=∅、inner⊆outer TRAIN、同一 outer 下 3 inner folds 两两互斥且并集=所属 outer TRAIN（768帧）、每 TEST=256 帧、四 TEST 并=702..1725、每帧 256 pairs；违反 SHALL 为 `BLOCKED`。

## S-COUNTS：canonical 统计与链式

- S-COUNTS-01：统计 SHALL 唯一采用 `counts[a,b]=count(Alice=a,Bob=b)`，`axis0=Alice/axis1=Bob`；SHALL NOT 在消费点隐式转置或并存相反约定。
- S-COUNTS-02：映射 SHALL 为 `symbol=low+32*high`（`U1=high/U2=low/bit0=LSB`），同方向、无 Gray、无置换。
- S-COUNTS-03：`P(A|B)` SHALL 为列归一；`P(U1|B)` SHALL 为按 `U2` 边际化；`P(U2|U1,B)` SHALL 为按 `(U1,B)` 条件化；`CE_L2_oracle` SHALL 用真实 `U1` 且仅作分层预算诊断。
- S-COUNTS-04：测试 SHALL 用非对称可手算联合分布分别验证三者；转置输入 SHALL 被捕获；只验归一化/对称数据 SHALL NOT 算证据。

## S-MODEL：M0–M2 闭合 + M3_EXIT_AMBIGUOUS

- S-MODEL-01：M0 SHALL 为 train 边际基线（`P_M0(a)=count_TRAIN(A=a)/n_TRAIN`，与 B 无关；均匀 `P=1/1024` SHALL 另记 `uniform_lower_bound_descriptive` 下界对照，不参选、不进选择与路线）；M1 SHALL 为全符号经验 `P(A|B)`；M2 SHALL 为 GF32 两层 `P(U1|B)*P(U2|U1,B)`（V54 口径）；输入 SHALL 仅为对应 train counts + 冻结参数；M3 SHALL 本轮直接退出（见 S-MODEL-03），审计在 M0–M2 上闭合。
- S-MODEL-02：每模型（M0–M2）SHALL 声明估计子、平滑/回退（含 lambda 反泄漏统一口径：lambda（Laplace/回退/收缩系数）SHALL 为冻结常量或仅由对应 TRAIN 统计确定，SHALL NOT 用 TEST/VAL/held-out 调参、早停或选模，inner 若用 lambda SHALL 只看 inner TRAIN 拟合 + inner held-out CE，不得窥视 outer TEST）、unseen Bob 行为、floor 精确 `1e-300`（先归一再 `max(P,1e-300)`，只保护 log）；SHALL 有手算小例。数学合同 SHALL 一致：counts 轴 + 链式 + CE + `rows=ceil(N*CE*f/5)` 同口径。
- S-MODEL-03：M3 无唯一定义，本轮 SHALL 直接记录 `M3_EXIT_AMBIGUOUS` 并从审计中移除，在 M0–M2 上闭合；SHALL NOT 猜测替代；M3 SHALL NOT 进选择、预算与路线。

## S-METRIC：指标

- S-METRIC-01：主指标 SHALL 为 `CE=-mean(log2 P)`（bit/symbol），报告每折 `CE_L1/CE_L2_oracle/CE_joint` 及 mean/std/max-min/n。
- S-METRIC-02：held-out SHALL 按 Bob 值是否在 train 出现划分 seen/unseen；报告 SHALL 含 `seen_frac/CE_seen/CE_unseen`；SHALL NOT 删 unseen 样本。
- S-METRIC-03：链式 SHALL 满足 `|CE_joint-CE_L1-CE_L2_oracle|<1e-10`（每折与 mean）；超限 SHALL 为 `BLOCKED`。

## S-REPRO：R5 复现

- S-REPRO-01：同 fixture 同口径复算 SHALL 命中 `CE_L1=6.422 / CE_L2_oracle=5.083 / CE_joint=11.505`，各 `|Δ|<1e-6` 且链式 `<1e-10`。R5 来源为 synthetic，故 `REAL_CAL_EXACT_MATCH` SHALL 为 false：只核公式复现，SHALL NOT 作真实 CAL 精确匹配断言。
- S-REPRO-02：失败 SHALL 为 `BLOCKED` 并记根因（口径/数据域/实现），SHALL NOT 进入模型比较，SHALL NOT 调参凑数。

## S-SELECT：选择

- S-SELECT-01：主键 SHALL 为 `mean(CE_joint)` 最小；`Δ<0.02` bit/symbol 时 SHALL 简单优先（R1冻结：按实现`SELECT_DELTA=0.02`冻结，不可调；M0<M1<M2，M3 已退出不参选）。
- S-SELECT-02：稳定性数值门限 SHALL 为 `CE_joint` 跨外层折 `std>0.10 bit/symbol 或 max-min>0.20 bit/symbol` 即不稳定，SHALL 显式标记并降级，SHALL NOT 仅凭单折最优选中；选择 SHALL NOT 自动改矩阵/decoder 参数。

## S-BUDGET：预算

- S-BUDGET-01：`N` SHALL 为 `1024 symbols/block`；`f` SHALL 为 `{1.0,1.1,1.2,1.3}`；`rows_required` SHALL 为 `ceil(N*CE*f/5)`。
- S-BUDGET-02：对照 SHALL 为 `L1:16行/80bit、L2:200行/1000bit、Total:216行/1080bit`（`1080/1024=1.0546875 bit/symbol`）；SHALL 分层报告 margin 与 rows 表。
- S-BUDGET-03：不足 SHALL 只记 `MODEL_BUDGET_MISMATCH`；SHALL NOT 称 information limit/GF32 failed/LDPC impossible；L1 不足 SHALL NOT 只加 L2。

## S-ROUTE：路线

- S-ROUTE-01：结论 SHALL 为 A/B/C 互斥穷尽唯一（以选中模型 mean 计，同一口径）：A SHALL 为 `f=1.3` 时全层 fit；B SHALL 为 `f=1.0` 时全层 fit 但 `f=1.3` 时任一层 mismatch（即 ¬A∧¬C，典型 `f=1.0/1.1 fit 而 f=1.3 mismatch`）；C SHALL 为即使 `f=1.0` 仍任一层 mismatch。
- S-ROUTE-02：A SHALL NOT 授权真实诊断；B/C SHALL 暂停通用化；扩维 SHALL 仍为 backlog。

## S-STOP：边界与停止

- S-STOP-01：R5/D4 SHALL 只做文档、计划、测试定义、CAL-only 标量审计；SHALL NOT 读 VAL、调用 decoder、构造新矩阵、修 writer、创建正式输出/`run_01`、授权执行。
- S-STOP-02：SHALL NOT 引入 checksum/hash/tag/签名或内容校验字段。
- S-STOP-03：counts 不唯一、M0–M2 手算验证失败、`M3_EXIT_AMBIGUOUS` 无显式退出记录、CV 读 VAL、任何 decoder 调用、R5/链式失败时状态 SHALL 为 `BLOCKED`，不得猜测、替代或重试。
