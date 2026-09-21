# Copy-paste prompt: 主要路线变更独立审查（V80 基线重置 + 先验成本会计决策）

- 用途：本项目发生了一次**较大路线变化**，需要用另一个 session 做详细独立审查。
- 粘贴方式：把下面 ```text``` 块整体复制到目标 session（ChatGPT / Codex / 其他 OpenCode session）。
- 若审查者无法直接读取仓库，请把 `docs/V80_BASELINE_20260921.md` 与其 §source-key 列出的文件一并附上；
  无法实际读取文件时只能给建议，**不得 ACCEPT**（AGENTS.md §10.2）。

```text
你是本科研项目的独立科学审查者。本次审查的是一次"较大路线变化"，不是常规批次复核。
请只读审查指定分支，不实现代码、不修改仓库、不授权任何执行。

═══════════════════════════════════════════
一、审查对象标识
═══════════════════════════════════════════

REPOSITORY:  Placebo303/HD-QKD-Polar-Comparison
BRANCH:      formal-ir-v80-nbldpc-jan21
CYCLE_ID:    V80-NBLDPC-JAN21 / BASELINE-RESET-R1
TRACK:       documentation-only（本次变更本身无 track gate）
REVIEW_KIND: MAJOR_ROUTE_CHANGE
ENTRYPOINT:  docs/V80_BASELINE_20260921.md   ← 唯一规划权威，必须先读完

项目第一性原理（AGENTS.md §1.1）：寻找科学合理、高性能的 HD-QKD 纠错/信息协调算法。
优先评价 exact recovery/FER、leakage/reconciliation efficiency、throughput/runtime、
memory cost、accepted-frame net secret-key yield。
科研代码不要求成熟软件包规范；只有当问题能具体导致错误数值/错误归因/不可复现/
未授权昂贵运行/数据覆盖时，才允许让工程或流程问题阻塞算法。

═══════════════════════════════════════════
二、这次路线变化是什么（审查对象）
═══════════════════════════════════════════

主线程把一份 fragmented、被反复打补丁的规划层（P1/P2/P3/Stage-0.5/X1 五个包 + 四个
OpenSpec change，互相引用且多次就地修订）**合并为单一权威文档**，并将旧层标记
SUPERSEDED（纯追加 banner，内容保留作历史）。同时把一项新发现的会计缺口做成了决策。
具体四件事：

  (1) 合并：docs/V80_BASELINE_20260921.md（115 行，8 节）成为唯一规划权威。
      旧包仅失去"规划权威"，其**已执行证据与复核裁定明确不受影响**。
  (2) 先验成本会计缺口被确认并决策：
        - 确认 λ_total 只计 syndrome + 64-bit tag，先验/标定成本完全未入账
        - 摊销模型定为"一次性池摊销"（gamma_f03 只读、从不重拟合、跨所有臂复用）
        - 披露路线定为"牺牲标定样本"（默认），成本只进 SKR 分子，f 不受影响
        - 可入钥块数由 500/691/911 修正为 200/276/364
  (3) 前进计划压缩为三步：(1) 摊销+披露决策【已完成，纯文档】
      (2) X1 跨源悬崖曲线 (3) 译码器等价性臂
  (4) 通用性框架反转：通用性主张必须锚定**最难的源 1M**，只报 2M 视为挑数据（禁止）

必须执行的审查动作：
  A. 通读 ENTRYPOINT 的 §source-key，按其列出的路径读全部来源文件。
     不要用旧聊天、旧分支或本 prompt 的转述补齐缺失事实——转述不等于证据。
  B. 验证合并是"无损"的：旧层里每一条仍然有效的冻结约束、门、阈值、禁止项，
     是否都已在基线 §1/§2 中保留？列出任何丢失或弱化的条目。
  C. 独立重算基线中的关键算术（用 python，只读）：
       1104/852.544 = 1.294947
       4.785675 = (5120−1040)/852.544
       3·4.785675/(1.3−1.294947) = 2842   （零失败臂认证样本量）
       36/4.3075 = 8.36                     （先验披露 vs A208 余量）
       (1108.31−64−36)/5 = 201.66 ⇒ m≤201
       逐源 m_max 与 f@208/@200/@199（用 MM 校正后 H，不是 plug-in）
     若任一项复算不出，列为 UNVERIFIED，不要默认它是对的。
  D. 检查"修正账本"（基线 §4）中每一条撤回项，确认旧值确实已被禁用、
     新值确实有来源。特别检查：plug-in 表 vs MM 校正表对 1.5M 出框判定的差异。
  E. 判断先验成本决策是否科学与完整：
       - "一次性池摊销"是否真有证据支撑（gamma_f03 只读且从不重拟合）？
       - "牺牲标定样本"作为默认路线，在可组合安全意图下是否站得住？
         对比姊妹 checkout（public_ec_only_not_secure, composable_security_claim_flag=0）
         的"零估计泄漏"是 scope 排除而非证明——本项目是否避免了同样的错误？
       - 60/20/20 切分导致先验成本 1.50× 于它所开启的密钥，这个数是否被正确传递？
       - 是否还有第三个未入账项？（例：盲披露、L1 份额、frame-acceptance 的 A 折扣）
  F. 审查通用性框架：以最差源 1M 锚定通用性主张，是科学上更强，还是只是修辞？
       1M 在 A208 出框（~9σ）、A200 也出框、只能到 m=199——这是否意味着
       "通用性"在当前设计点根本不可达？如果是，前进计划是否在面对这件事？
  G. 审查前进计划三步的顺序与范围是否合理，特别是：
       第 2 步 X1 的入口阻塞（1M/1.5M 直方图未被 A1 持久化，需 DECIDE 重读）
       是否被诚实量化？"2M-only 先回答工作点半边"的退路是否科学上可接受？
  H. 检查是否有人为了新叙事而**过度推翻**旧结论。列出任何被推翻但证据不足的判定。
  I. 明确边界：oracle/development-only/非端到端/选择偏差/复用种子/合成帧 vs 真实帧。
     V80 至今全部结果是合成配对帧；真实数据只有 Stage 0.5 与 A1 的 H_full/span/config。

═══════════════════════════════════════════
三、必须读的文件（按顺序）
═══════════════════════════════════════════

1. docs/V80_BASELINE_20260921.md                    ← 唯一权威，含 source-key
2. docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md  ← 本次新增决策
3. docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md     ← 第 2 步入口阻塞评估
4. docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md     ← 事实核验
5. docs/PRIOR_COST_CLAIM_REVIEW_20260921.md         ← 对抗性审查
6. docs/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md ← 姊妹 checkout 审计
7. AGENT_PROJECT_MEMORY.md 尾部（约 4226 行起，最新条目在文件尾）
8. docs/decision-log.md 尾部
9. docs/research_cycles/V80-NBLDPC-JAN21/ 下：
     P3_A1_REVIEW.md, P3_STAGE05_REVIEW.md          ← 已执行结果的独立复核（权威，未作废）
     PROGRAM_PLAN.md                                ← 冻结会计口径
     P1/P2/P3_CENSUS/P3_STAGE05/X1 的 *_PACKET.md   ← 已标记 SUPERSEDED，仅作历史
10. docs/TTBIN_MEMBER_SEMANTICS_20260921.md         ← 嵌套/超集禁令 + 时长须实测
11. docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md ← 强制相关对齐
12. docs/DATA_INVENTORY_20260921.md                 ← 10 个数据集分类
13. docs/ROADMAP-20260921.md                        ← 宏观路线图（早于本次变更，注意可能已过期）
14. AGENTS.md §1.2（EXPLORE/DECIDE 矩阵）、§3、§10.1、§10.3

注意：docs/ROADMAP-20260921.md 写于本次变更之前，其中部分数字已被后续修正覆盖
（尤其是认证块数与出框判定）。若发现它与基线冲突，以基线为准并指出冲突。

═══════════════════════════════════════════
四、输出格式（严格遵循，便于直接复制回仓库）
═══════════════════════════════════════════

REVIEWED_SCOPE: <实际读到的文件/diff>
EVIDENCE_ACCESS: VERIFIED | INCOMPLETE
ADVISORY_VERDICT: ADVISORY_ACCEPT | REVISE | REJECT | BLOCKED

CONSOLIDATION_LOSSLESSNESS:
- <旧层中丢失/弱化的冻结约束；若无，明确说"未发现丢失">

ARITHMETIC_RECHECKS:
- <逐项：复算命令 + 结果 + PASS/FAIL>

SCIENTIFIC_FINDINGS:
- [S1] <finding + evidence path/field>

ACCOUNTING_FINDINGS:   ← 本次审查重点
- [A1] <先验成本/摊销/披露路线/块数/任何第三项未入账成本>

GENERALITY_ASSESSMENT: ← 本次审查重点
- <1M 锚定是否科学上可辩护；当前设计点下通用性是否可达；计划是否在面对它>

ROUTE_CHANGE_ASSESSMENT:
- <合并是否无损；前进计划顺序/范围；X1 阻塞是否被诚实量化；2M-only 退路是否可接受>

OVERTURNED_CLAIMS_AUDIT:
- <被推翻但证据不足的判定；若无，明确说"未发现">

CLAIMS_ALLOWED:
- <可用的最窄措辞，逐条>

CLAIMS_FORBIDDEN:
- <必须禁止的过度表述，逐条；特别注意 f_super≠f_eff、单源 f_eff 不可认证、
   合成帧≠真实帧、H 在分母侧、通用性 headline 必须 1M 打头>

REQUIRED_CORRECTIONS:
- [R1] <具体修正 + 验收证据>

NEXT_SCIENTIFIC_DECISION:
- <一个有界的下一步决策，不是自动继任者>

EXECUTION_AUTHORIZATION:
- NOT_GRANTED（除非用户另作明确授权；本审查不授予任何执行、任何数据集、
  任何 gate 变更、任何发表声明）

AUTHORITY_BOUNDARY:
- 本裁定为 advisory 审查。它不是仓库验收、不是科学晋升、不是执行授权；
  那些保留在用户/主审，并必须记录在 Git。

═══════════════════════════════════════════
五、给审查者的额外提醒
═══════════════════════════════════════════

- 本次变更有大量"撤回项"（见基线 §4 修正账本）。其中若干条最初的申报来自
  **姊妹项目的一次审查**，在本仓库被核验为不成立（如 1.8× 比率、P20Q 数字、
  PHASE4_P0_PRIOR_CONTRACT.md、CAL 与 DEV/EVAL/HOLD 的框架）。
  请把这些当作"曾被核验推翻"处理，不要因它们看起来有出处就重新采信。
- 但请独立判断：**推翻本身是否也可能过头**。主线程明确要求审查这一点（动作 H）。
- 本项目至今没有任何 FER/SKR/route/qualification/publication 结论。
  所有"已建立结果"都是合成配对帧上的，或 Stage 0.5/A1 的只读 header/统计探针。
- 如发现本 prompt 与仓库实际内容冲突，以仓库为准，并明确指出冲突。
```
