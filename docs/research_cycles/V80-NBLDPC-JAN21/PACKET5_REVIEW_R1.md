# PACKET5 首审（R1）— NEEDS-CHANGES（评审批次 2026-09-23；本件为 2026-09-24 docs-only 落档）

- 文件性质：**docs-only 评审结论落档**。Track = **documentation-only — 无 track gate**
  （AGENTS.md §1.2 适用性矩阵 "Documentation-only changes" 行）。
- 本文件**不授权任何执行**：零解码、零构造、零真实数据访问、零 commit/push、
  零 `results/` 与 `comparison_bench/outputs_comparison/` 写入；**不改**任何既有
  正文 / 阈值 / 路线 / packet（本件与 `PACKET5_REVIEW_R2.md`、
  `AGENT_PROJECT_MEMORY.md` 尾部追加为本任务全部允许面）。
- 来源与保真：按 memory-free triage（建议 A+B）把会话中的首审结论落为耐久档；
  **只转录任务冻结要点 + 仓内可佐证事实，不含推测**。测试计数为当时转录，
  本文件**未重跑**任何测试。
- 被审对象：2026-09-23 同批 docs/实现交付（详见配套 memory 条目"五包收口"）。

---

## §1 判定（Verdict）

**NEEDS-CHANGES** — **1 BLOCKER + 5 MAJOR**。

同批同时通过的面（首审观察，逐项）：

- **无授权泄漏**：`P4_FEAS_PACKET.md` §10(d) 授权块 BLANK 保持、臂根 UUID 仍
  `[TO BE FROZEN]`；`P3_MEMORY_AUDIT_PREREG_AND_AUTH.md` 全部签字/预算字段 BLANK；
  无任何旗标组合被触发执行的记录。
- **无保护根写入**：`results/` 与 `comparison_bench/outputs_comparison/` 零写入；
  首轮事故本身亦零落盘（`P4_FEAS_INCIDENT_ADDENDUM.md` §2 逐项可复核）。
- **科学语义全对**：被审件中的冻结科学输入、claim ceiling、`undetected` 单列不并入
  success、逐源分列、状态词不升格等语义未见偏差。
- **focused fake-only 测试 19 passed**（R1 时点；整改后 R2 为 20 passed，
  见 `PACKET5_REVIEW_R2.md`）。

## §2 BLOCKER

### B1 — 事故零落档

- **发现**：首轮 fake-only focused pytest 中，夹具类型守卫过松放行了恰 1 次内存内
  真实构造调用（`peg_construct(2048, 416, …, trials=20, GF(32))`，非任何授权臂）。
  该事故当时**只存在于会话历史，仓内零记录** —— 直接违反 AGENTS.md §2
  "Chat history is not durable project memory"，且事故发生在未授权窗口，
  无日志/臂根可自证边界。
- **整改要求**：docs-only 补录事故事实 + 零后果边界 + 对 packet §5 "≤1 repair"
  名额的处置**建议**（裁定权留主线程/用户），并同步 `docs/NOW.md` 状态
  （后者即 M3）。
- **整改落点（仓内佐证）**：`docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_INCIDENT_ADDENDUM.md`
  （文件头自称 "**docs-only 事故落档（B1 补录）**"，记录者注 "coder-doc 子代理
  （冻结任务 **B1+M3**）"；§3 三点待裁明确列出，建议不消耗 §5 名额但**不代裁决**）。

## §3 MAJOR（M1–M5）

| ID | 发现（首审转录） | 仓内佐证 / 整改去向 |
|---|---|---|
| **M1** | **死算**：runner 内存在"算完无人读取"的死计算 | `comparison_bench/src/comparison_bench/cli/p4_feas_construct.py` 注释自证："the former constructor-side base-rank pre-computation **was dead** … and is deleted"（§5 预算注释段）＋ "`No rank pre-computation here (dead: …)`"（构造路径） |
| **M2** | **接口不兼容**：操作员 prompt 命令模板与已实现 runner 的调用接口互不兼容，且 runner 名占位符未回填 | `P4_FEAS_PROMPT.md` §1-6：per-arm 形式 `--arm P4F-R1 --n 2048 --m 416 --instance 2026092001 --trials 20 --root …`（R2 换三参），runner 路径仍 `<P4FEAS_RUNNER [TO BE FROZEN]>`；实现侧 argparse 为**双臂单次调用**（`--seeds` + `--r1-uuid8`/`--r2-uuid8` + `--root/--n/--m/--trials/…`），**无** `--arm`/`--instance`。整改口径：**只记录不选型**（`openspec/changes/p4-feas-construct-runner/proposal.md` §"M2 interface incompatibility — PENDING ADJUDICATION (recorded, not selected)"） |
| **M3** | **NOW失真**：`docs/NOW.md` 状态与实况不符（脏树清单未含 21:08 快照后新增件；事故与执行面事实缺失） | `docs/NOW.md` §1（★ 6 项快照后新增 + 本任务 B1+M3 增量）、§3（P4 执行面就绪 + 事故补录）、§4（P3-gate 行 TBD → re-freeze v2 PROPOSED）已订正；页首自证 `PACKET-A STATUS-DELTA-20260923` |
| **M4** | **无 OpenSpec**：runner 增加生产执行入口行为（可运行 CLI、授权旗标、拒收码、输出根）却无覆盖性 OpenSpec 变更，与 AGENTS.md §3 "行为变更先过 OpenSpec" 冲突，两条规则从未在耐久文档中调和 | `openspec/changes/p4-feas-construct-runner/proposal.md`（头部即引 "Review finding **M4 (MAJOR)**"；**仅 proposal**、无 design/tasks/specs、`Affected specs: None`；定位为已实现行为的回溯性行为记录，非新行为授予） |
| **M5** | **log 守卫**：`--log` 目的地缺少与 `--root` 同级的 `FORBIDDEN_ROOT_PARTS` fail-closed 守卫（可把 append-only 日志指向保护根） | runner `_check_log_path()`：拒收非 str/空、保护根分段 rc=2，注释 "same `FORBIDDEN_ROOT_PARTS` guard as `_check_base_root` now applies to the `--log` destination"；`execute()` 在任何 root/log 写入前调用；配套测试 `test_cli_log_refuses_forbidden_roots_same_as_root` |

## §4 处置

- **NEEDS-CHANGES → 整改后进入 R2**；M2 的裁决权在主线程（AGENTS.md §4：
  coder 不得重定义需求，docs-only 件只记录不选型）。
- 首审的通过面（§1 四项）在整改期间**不得回归**：授权块 BLANK、保护根零写入、
  科学语义、claim ceiling。
- 本文件不授权任何执行、commit、push；P4 仍 `FROZEN NOT GRANTED`，
  P3 re-freeze v2 阈值仍 `PROPOSED`。

**配套落档**：`PACKET5_REVIEW_R2.md`（再审判定）＋ `AGENT_PROJECT_MEMORY.md`
尾部 2026-09-23 五包收口条（交付、复审结论、开放待裁、边界、指针）。
