# D5 计划：F 模型两层 GF32 码率与嵌套母矩阵设计（只冻结计划，不实现）

- Change：`formal-ir-v72p2d5-gf32-rate-mother-plan`
- Predecessor：`formal-ir-v72p2d4-cal-gf32-model-rate-audit`（D4R2，route C，`MODEL_BUDGET_MISMATCH`）
- Cycle：`V72P2D5-GF32-RATE-MOTHER`
- Lifecycle：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 本 change 只冻结计划：不写生产代码、不运行 decoder、不读 VAL、不创建结果目录、不授予任何执行。
- `base_sha/accepted_plan_sha/implementation_sha` 只承担 AGENTS 要求的 Git 版本绑定，不承担数据或内容校验。本计划不新增任何数据或内容摘要、签名、checksum/hash 字段。
- Ponytail lite：未来实现至多算法脚本 + focused test 各一个；复用 V31/V54 历史链；不用框架、缓存、锁、retry、持久化。不预设优胜路线。

## 背景（frozen input，不得重新推导）

- 字母表 `d=1024`，分层 `U1/U2=[5,5]`，`GF(32)`，`N=1024`。
- D4R2 选中模型 F（full-symbol hierarchical `P(A|B)`），outer frame-blocked nested CV：
  `CE_L1=3.814742`、`CE_L2_oracle=3.347605`、`CE_joint=7.162347` bit/symbol，
  worst joint `7.178766`，std `0.0158`，range `0.0423`，`lambda*=137.3823795883264`（证据
  `docs/research_cycles/V72P2D4-CAL-RATE/RESULT_SUMMARY_R2.md`）。
- 历史码率 `L1=16 / L2=200 / Total=216` GF32 行在 `f=1.0` 已严重不足（见 design §2 的 bit 对比）；
  禁止继续用旧 216 行做当前域真实实验。
- D4 没有证明信息论极限，只证明 `MODEL_BUDGET_MISMATCH`（描述性预算失配，非失败定论）。

## Goal（回答 6 问，答案位置）

1. F 模型怎样无歧义转成两层 decoder prior？→ design §1 + spec S-PRIOR。
2. L1/L2 各需要多少 GF32 校验行？→ design §2 + spec S-BUDGET（`f=1.0/1.05/1.1/1.2` 行数表）。
3. 仓库哪个现有构造器最适合扩展到约 700–1000 行？→ design §3 + `PLAN_FREEZE.md` 能力表
   （结论：V31 QC-cyclic-projective `build_layer` 为基线；Lane-C 仅备份）。
4. 如何构造嵌套、满秩、稀疏且可增量披露的 GF32 mother？→ design §4 + spec S-MOTHER。
5. 跑 `n=1024` 前怎样用 tiny/`n=64`/`n=256` matched synthetic 排除数学或性能错误？
   → design §5 + spec S-SYNTH/S-GATE。
6. 哪一个最小实验可判断 GF32 路线是否值得继续？→ design §6（`n=256` go/no-go，唯一杀实验）。

## Non-Goals

- 不实现任何构造器/decoder/prior 适配代码；不修改 `src/ experiments/ tools/ comparison_bench/src/` 下任何 `.py`。
- 不运行 decoder（未来测试的显式注入 fake 也不在本轮），不读 VAL，不创建正式结果，不授权真实执行（`run_01` / `EXECUTE_AUTH` 禁止）。
- 不做跨 session 推广、扩维（`d=256` 仍为 backlog 后继）、SKR/信息极限断言、方法定级。
- 不实现后反向修改计划：本轮冻结的阈值（`SELECT` 类常量、`PASS/FAIL` 门限、行数表）在 apply 阶段不得回写放宽；
  若实现发现歧义，停下返回 planner/OpenSpec 修订（新 SHA 重审），不猜测绕过。
- 不新增任何防御性/审计/校验框架（无 hash/checksum/tag/签名/锁/retry/缓存）。

## 范围

- 新增文件仅限：本目录 `proposal.md / design.md / tasks.md / specs/spec.md / PLAN_FREEZE.md`。
- 只读引用：`AGENTS.md`、`AGENT_PROJECT_MEMORY.md`、`docs/research-cycle-sop.md`、
  D4R2/D3/V72P0 OpenSpec 与 cycle docs、历史 GF32 构造器与 decoder 接口（grep 级签名确认，不复制大段代码）。
- V72P0 mother（`9036x10240` binary IRA）仅作嵌套/秩证明模式的结构参考；
  明确记录“禁止直接假设适用于 GF32”的边界（design §3.5）。

## Impact Scope

- 新增 `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/` 下 5 个文档文件。
- 零生产代码修改，零测试执行，零数据读取，零输出目录创建。

## Acceptance Criteria

- [ ] 四工件齐全且互相一致：`proposal.md / design.md / tasks.md / specs/spec.md`。
- [ ] `PLAN_FREEZE.md` 含完整能力表（11 列逐项填写）、行数表、风险与 open questions。
- [ ] prior 合同无歧义（求和轴/归一化时机/log-概率域/下溢/形状/接口映射五项显式）。
- [ ] 行数表覆盖 `f=1.0/1.05/1.1/1.2` 且与 D4R2 审计数（`1467 vs 216 / margin -1251`）自洽。
- [ ] 嵌套 mother 定义可验收（SHALL/SHOULD），披露 API 为最小列表/指针形状。
- [ ] 三级门控 + 唯一生死实验的阈值冻结，失败三分法显式。
- [ ] 独立 Plan Review（main thread）ACCEPT 前不进入 apply；`REAL_EXECUTION_AUTHORIZED=false`，
  `DECODER_EXECUTED=false`，`VAL_LOADER_CALLS=0`。
