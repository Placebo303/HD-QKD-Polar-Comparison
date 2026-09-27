# P4 构造可行性 — 首轮测试事故补录（P4_FEAS_INCIDENT_ADDENDUM，2026-09-23）

- 文件性质：**docs-only 事故落档（B1 补录）**。Track = **documentation-only — 无 track gate**
  （AGENTS.md §1.2 适用性矩阵 "Documentation-only changes" 行）。
- 本文件**不授权任何执行**：`P4_FEAS_PACKET.md` 保持 **FROZEN, NOT GRANTED**
  （§10(d) 授权块 BLANK）；零解码、零构造、零真实数据访问、零 commit/push。
- 创建范围（P4-3 式声明）：本任务**只新建本文件一份** + 修改 `docs/NOW.md`
  （§1/§3/§4-P3-gate 行/§6 状态行）。**不新建** `P4_FEAS_EXPLORATION_LOG.md`
  ——按 packet §6，该批次日志在**执行时**新建（append-only）；本事故发生在授权之前，
  不触发其创建。**不改** packet / prompt / P1 族 / S0.1 族 / `docs/decision-log.md` /
  `docs/ROADMAP-20260921.md` / `AGENTS.md` / `src/` / `experiments/` / `tools/`；
  **未 commit、未 push**。
- 落档依据（AGENTS.md §2）：chat 历史不作项目记忆——首轮事故此前仅存在于会话中、
  仓内零记录，本补录即为唯一持久落档。记录者：coder-doc 子代理（冻结任务 B1+M3）；
  **裁定权在主线程 / 用户**，本文件只落档 + 建议，不代裁决。

---

## §1 事故事实（2026-09-23）

- **时间**：2026-09-23，`docs/NOW.md` 21:08 快照（该页 mtime 21:08:31 +0800，当时
  脏树中不存在 runner/测试文件）之后、**首次 fail-closed 修复落盘 21:23:51 +0800**
  （`comparison_bench/tests/test_p4_feas_construct_fake.py` 与
  `comparison_bench/src/comparison_bench/cli/p4_feas_construct.py`；此后两文件又于
  22:05:40 / 22:06:16 经 M1/M5 修订——当前 mtime 即该次修订，不再等于首次修复时刻；
  **窗口上界 = 首次修复 21:23:51，不变**）
  之前——即事故窗口 **(21:08:31, 21:23:51) +0800**。精确墙钟时刻未在仓内留存；
  本补录即唯一落档。
- **调用**：首轮 fake-only focused pytest 中，**夹具类型守卫过松**（fixture
  type-guard 缺陷）放行了一次**真实生产构造调用**：内存内
  `peg_construct(2048, 416, λ={2:1}, ρ=make_rho(0.796875), seed=F1 谱系整数,
  trials=20, GF(32))`（packet F2/F3 冻结形态），**恰 1 次**——非 twice-identical
  成对第二次、**不是** `P4F-R1`/`P4F-R2` 任何臂的授权执行。
- **首轮代码字节不可考**：runner 与测试均为 untracked 文件，fail-closed 修复覆盖了
  首轮字节，仓内无 diff/历史可回溯；以上事实按主线程通报 + 现文件状态落档。

## §2 零后果边界（逐项，可复核）

- **零落盘**：调用纯内存（packet §5 依据段所述构造路径无磁盘写）。事故后复测：
  `workspace/P4_FEAS/` **不存在**；`results/`、`comparison_bench/outputs_comparison/`
  零写入；`git diff -- src/` **EMPTY**（I4）；仓内无任何新增输出/报告/日志文件。
- **零解码**：runner 结构性无解码路径（`DECODE_CALLS = 0` 冻结、模块内不存在
  `decode*` 可调用名；packet F5）；同时**零 `.ttbin` / 零 `gamma` 读取**（F4）。
- **无 pins、无结论、无复用**：该次内存返回对象**未落盘、未过 F6 门**
  （fc=0 / rank_full==416 / twice-identical / rank_base_400==400 四门均未评），
  未进任何 pins 报告、construction.json、日志或评审文件；**不产生、也不得复用
  任何 pins / 可行性结论**（packet §9 claim ceiling 不被触碰；不占臂序、无臂根、
  不消耗 key-eligible 计数）。
- **科学输入零变动**：F1–F10 冻结值一字节未改；假设 / 阈值 / seeds / 数据角色 /
  计算规则全部不变。事故不改变任何科学契约，只暴露了测试夹具的类型守卫缺陷。
- **现态 fail-closed**（首次修复 21:23:51 起；22:05:40 / 22:06:16 又经 M1/M5 修订，
  事故窗口上界不变）：`production_construct` 类型守卫严格拒绝
  bool / 字符串 / 非整数（明文 "integer literal only, no coercion"，非法参一律
  `Refusal` rc=2）；fake-only 测试现**只喂非法参、仅触及拒绝分支**，合法参生产
  构造不再发生于该测试路径。focused 单文件测试按 fake-only（显式注入
  `construct_fn`/`rank_fn`）运行，符合 AGENTS §10.1 条款 8。

## §3 对 packet §5 "≤1 次 repair" 名额的处置（已裁决；主线程签字行 BLANK）

- **已裁决：不消耗** `P4_FEAS_PACKET.md` §5 的至多 1 次预注册 repair+rerun 名额
  （**夹具缺陷，非科学失败**）。
- **已裁决：Pre-EXECUTE Q0–Q6（prompt §0）必须披露**本事故 + 事故窗口
  **(21:08:31, 21:23:51) +0800** + §2 零后果边界（零落盘、零解码、无 pins、
  科学输入零变动、现态 fail-closed）。
- 主线程签字：________（**BLANK**）／日期：________
- **理由（对应 §5 三要件）**：
  1. §5 repair 面向**授权执行中的基础设施失败**（进程死亡、无 pins 可得）。本事故
     **发生在授权之前**——§10(d) BLANK、无 Pre-EXECUTE、无臂根、无批次日志
     （日志按 §6 只在执行时新建），根本不处于 §5 适用的执行阶段。
  2. §5 要求失败尝试"在**同一日志**保留记录（exact error + unchanged-inputs 声明）"。
     本事故**零落盘 ⇒ 无失败执行体可保留**：没有臂根、没有日志条目、没有结果文件
     可供 append；"保留"机制无对象，消耗名额无法按 §5 合规形态执行。
  3. 失败类型是**夹具类型守卫缺陷**（测试工具缺陷），不是冻结科学契约失败；科学输入
     零变动，一次修复即 fail-closed。把科学执行的安全阀花在测试夹具缺陷上，会无谓
     消耗授权批次唯一的一次 repair 机会。
- **裁决状态**：(i) 名额是否计数 → **已裁决：不消耗**（上条）；(ii) 授权时
  Pre-EXECUTE Q0–Q6 是否须披露本事故 → **已裁决：必须披露**（上条）；
  (iii) 本窗口内是否还有其他未落档调用需要补录 → 仍**待主线程/用户书面确认**
  （仓内零证据；如有即补录本文件）。
- **非升级触发自查**：本事故无真实数据、无解码、无任何主张产出，**不构成** packet §7
  的 DECIDE 升级触发；也**不构成** EXPLORE 批次 repair 记录义务（无授权批次、无日志
  可写）——两者都以"已授权执行"为前提，而授权始终为零。

## §4 与 packet / 本周期文件的关系

- `P4_FEAS_PACKET.md` / `P4_FEAS_PROMPT.md` 一字节未动，仍 **FROZEN, NOT GRANTED**；
  `P4_FEAS_EXPLORATION_LOG.md` **未创建**（执行时按 packet §6 新建，届时条目 0 =
  Pre-EXECUTE Q0–Q6，其中可含本事故披露——由裁定点 (ii) 决定）。
- `docs/NOW.md` 同任务更新：§1 脏树清单（9→11 项 + 21:08 后新增注记）、§3 落档事实
  （runner 已就绪 / 本补录 / G0B / SAME-DATA 指针）、§4 P3-gate 行
  （TBD → re-freeze v2 PROPOSED）、§6 权威指针——与本补录互为索引。
- 本文件是 B1 的**唯一仓内落档**；后续任何引用本事故的评审/授权文书一律指向本文件，
  不依赖会话历史。
