# Same-Data Comparison Metrics — Proposal

- Charter: `docs/ROADMAP-20260921.md` §3 **P5**（同数据、同会计口径的
  MLC/R3 对照臂 + 逐源会计条款）与 §5 对外表述规范。
- Spec draft: `docs/research_cycles/V80-NBLDPC-JAN21/SAME_DATA_CMP_METRICS.md`
  （(e) 清单全文，验收项 A-CMPE-1..7）。
- Upstream evidence（只读）:
  - `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/TRACEABILITY.md`
    （MLC f=4.169 / 587 bits/帧 / 500/500；R3 f≈12 单遍本原综合征 C2/C3；
    r=10 探针 native≈9× wall，2.1 s vs 19.4 s，R2 行）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_BATCH_END_REVIEW.md` §8
    （路线输入留主线程）+ §7-F3（`decoded`≠success 列语义）；
  - `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md` **M5**
    （measured/assumed/projected/qualified 分列；SKR 选点前置条件）；
  - `AGENTS.md` §5.3（schema stability）/ §5.5（科学语义）/ §1.2（矩阵）。
- Track: **—（无 track gate：documentation-only 草案）**。本 change 只产出
  一份 docs 指标清单与本 proposal；**不含实现**，不写 `comparison_bench/`
  任何代码或列，不跑 benchmark/smoke，不 commit/push，不授权任何执行，
  不产生任何 FER/SKR/资格化/发表主张。
- Data authority: no data touched; no number is introduced — every figure
  traces to ROADMAP-20260921 / TRACEABILITY / P1 batch-end review /
  `v80-prior-cost-accounting`（1.50×）/ owned-roadmap M5。

## Why (what changed)

- P5 对照臂（二元 MLC 基线 f=4.169、587 bits/帧、500/500 与 R3 f≈12 单遍
  本原综合征，同数据、同会计口径）是 ROADMAP §3-P5 明列"必做"的最有说服力
  比较，但目前**没有一份 spec 级文档冻结"要比什么、怎么标"**：哪些列必须
  独立、哪些合并被禁、历史行何时标不可比、探针行能主张到哪里、没有安全观测量
  时结论句上限在哪——散落在 ROADMAP、TRACEABILITY、P1 review、owned-roadmap
  与 `v80-prior-cost-accounting` 里，未收口成单一 report-contract。
- `AGENTS.md` §3 要求"修改行为/架构/工作流规则先建 OpenSpec change"；
  本 change 以 proposal 草案形式占用 `same-data-comparison-metrics` 名字，
  把该 report-contract 提升到 spec 级，供 P5 包冻结时逐条引用（A-CMPE-1..7）。
- 已知的历史事故模式（ROADMAP §5 禁令、P1 §7-F3、TRACEABILITY C3/C4/E7）
  表明不冻结清单就会复发：`undetected` 并入 success、f_super 当 f_eff 报、
  跨口径差值、探针冒充真实结论、把采集率说成 SKR。

## Scope (frozen)

- 仅两件产出：
  1. `docs/research_cycles/V80-NBLDPC-JAN21/SAME_DATA_CMP_METRICS.md`
     — (e) 清单全文，含验收项 **A-CMPE-1..7**：
     - **A-CMPE-1** per-source `attempted`/`exact_match`(=success=¬failed，含
       `decoded`≠success 图例)/最终 `accepted`/`accepted_wrong`(undetected)
       独立列，`undetected` 禁并入 success/FER，禁跨源/跨实例合并；
     - **A-CMPE-2** `f_super` 与 `f_eff`（本臂 m 基）双数并列，禁互相替代；
     - **A-CMPE-3** 实际公开比特 `leak_EC`+64-bit tag ⇒ verification-aware
       `λ_total`，加验证标签、控制轮次完整协议链，加每源 1.50× prior
       机会成本行（不进 f 分子）；
     - **A-CMPE-4** 资源耗时总/每块/每译码 + 峰值 RSS + 交互消息数（P6），
       IR 吞吐与采集率分标；
     - **A-CMPE-5** `N_req` report-only vs key-eligible（200/276/364）分列；
       `d`/`q`/`n_IR` 分离；合成/真实/key-eligible 三组计数分离；
     - **A-CMPE-6** R3/MLC 历史口径标注与"不可比即标"；r=10 native≈9×
       （2.1 s vs 19.4 s）探针成本行独立 + 探针不替真实结论固定句；
     - **A-CMPE-7** 无安全观测量 ⇒ 仅"实测纠错/公开开销收益"、禁 SKR
       （owned-roadmap M5 选点禁令）；数字落
       measured/assumed/projected/qualified 四列之一。
  2. 本 `proposal.md`（唯一 OpenSpec 文件）。

## Non-goals

- **不含实现**：不写 `comparison_bench/` 任何代码、函数、CLI 或 CSV/JSON 列；
  不定义文件名与输出根；不改既有 schema（§5.3：列名静默变更仍被禁止，
  落地实现须另开 change）。
- 不改 `openspec/specs/` 任何现有 spec，不建 `specs/` 子目录（本 change
  无 delta spec — proposal-only 草案）；不建 `design.md`/`tasks.md`。
- 不跑 benchmark / smoke / 任何解码；不访问真实数据 / `.ttbin`；
  不写 `results/` 或 `outputs_comparison/`。
- 不 commit、不 push、不开 PR。
- 不产生 FER / SKR / 资格化 / 路线 / 发表主张；不冻结任何 P5 包、
  不预授权 P5 执行（P5 仍是 DECIDE，需独立 prereg + Pre-EXECUTE + 授权）。
- 不改 ROADMAP、decision-log、memory、AGENTS.md（引用不改写）。

## Affected specs

- None. No behavior change is made by this change (report-contract
  documentation only), so there is no `specs/` subdir. Delta specs arrive only
  if/when a later implementation change lands these columns in code — that
  change must carry the A-CMPE mapping and respect §5.3 schema stability.

## Acceptance mapping

- A-CMPE-1..7 defined in
  `docs/research_cycles/V80-NBLDPC-JAN21/SAME_DATA_CMP_METRICS.md` §10;
  reviewer reports by ID only (AGENTS.md §10.1-1/10.1-12: delta reports,
  stable acceptance IDs).
