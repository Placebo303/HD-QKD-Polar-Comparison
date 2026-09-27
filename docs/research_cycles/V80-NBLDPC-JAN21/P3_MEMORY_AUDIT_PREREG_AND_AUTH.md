# P3 真实帧记忆/一致性审计 — PREREG_AND_AUTH (2026-09-23) — DRAFT_FROZEN_PENDING_AUTHORIZATION

- Track（恰其一）: **DECIDE**（真实/原始数据 + 路由门上游；AGENTS.md §1.2 适用性矩阵）。Status: `DRAFT_FROZEN_PENDING_AUTHORIZATION` — **本文件全部签字/预算/授权字段 BLANK；不授权任何执行**。
- Prereg 本体（权威，不重复正文）: `P3_MEMORY_AUDIT_PACKET.md`（**re-freeze v2，2026-09-23**：§2.5 阈值槽 T-M1..M4 = PROPOSED，T-C0 = REUSED）+ `P3_MEMORY_AUDIT_PROMPT.md`。Acceptance ID: **G-P3-MEM**。
- 基线（provenance，非执行锁）: 用户声明 `8e9c8526`；实际分支/HEAD 由 Pre-EXECUTE Q0 实测记录，本文件不做 SHA 相等断言（AGENTS.md §10.3）。
- **Nothing has been executed. 未读真实数据、未算任何统计量、未建机器根、未写任何输出、未 commit、未 push、0 decoder/DE/构图/`tools/*`。**
- 压缩三文档形式（AGENTS.md §10.3 允许）: 本文件 + `RESULT.md` + `INDEPENDENT_ACCEPTANCE.md` + 机器伪影。

## 1. 授权前状态表（除容差 PROPOSED 行外，全部 BLANK）

| 项 | 状态 |
|---|---|
| 容差数值（PACKET §2.5 T-M1..T-M4） | `PROPOSED — re-freeze v2（2026-09-23 已填入 PACKET §2.5；授权时由用户逐项确认，未确认 = 阻断执行）` |
| T-C0（2M 对照 vs V80 锚） | `REUSED（既有冻结值，非新设，未改动）` |
| 用户授权签名 | `[BLANK — 未授权，不得执行]` |
| 授权臂序列 / 数据集三源 / 意向分支 | `[BLANK]` |
| 预算上限（trio / 单源 / 单读 / RSS / 每源读次数） | `[BLANK — 授权时填写并确认；PACKET §5 仅为 PROPOSED 上限，本文件不填定值]` |
| 机器根 uuid（`workspace/P3_MEM/<uuid>/`） | `[BLANK — 执行时一次性实例化]` |
| Pre-EXECUTE verdict（PROMPT Q0–Q6） | `[BLANK — 未执行]` |
| 独立 Pre-RESULT verdict | `[BLANK — 未执行]` |
| 主线程接受 | `[BLANK — 未接受]` |
| PREREG 状态 | `DRAFT_FROZEN_PENDING_AUTHORIZATION` |

## 2. 授权签字块（用户填写；操作者/代理不得代签）

```
I AUTHORIZE execution of the P3 memory/consistency audit under Acceptance ID G-P3-MEM,
strictly within the frozen contract of P3_MEMORY_AUDIT_PACKET.md (re-freeze v2, 2026-09-23)
and P3_MEMORY_AUDIT_PROMPT.md. 本文件与 PACKET/PROMPT 本身授权 NOTHING。

  Branch / commit context confirmed:            ______________________________
  Datasets authorized (three sources, 分报禁合并): ______________________________
  Tolerance values confirmed (PACKET §2.5):      ______________________________
  Total wall ceiling authorized (s):             ______________________________
  Machine root uuid:                             ______________________________

  Authorized by (name/handle):                   ______________________________
  Date (UTC):                                    ______________________________
  Signature:                                     ______________________________

NOTES
- 本签字是唯一授权；签字块任何一行空白 ⇒ PROMPT §1-1 STOP，不得执行。
- 执行前 Pre-EXECUTE Q0–Q6 必须逐项记录证据并 PASS（含目标输出 absence、focused fake-only 测试）。
- 一次执行 + 一次结果记录 → 独立 Pre-RESULT → 主线程接受；失败保留，重跑 = 新授权 + 新根。
- 铁律: 0 decoder / 0 DE / 0 图构造 / 0 tools/*；分源禁合并；阈值以外无预测句；
  no-overwrite（results/、comparison_bench/outputs_comparison/ 只读）；无 commit/push。
```

## 3. 冻结边界（本文件不改变的既有约束）

- 预算与停止规则: 以 PACKET §5 为准（PROPOSED 上限，授权时确认；本文件不填数值）。
- 容差与判定: 以 PACKET §2.5（re-freeze v2）与 §4 P3-gate 判定形式为准。
- 禁碰清单: 沿用 PACKET §0-4（P1 族、P4 包、S0.1 族、EXECUTION_PLAN、NOW、decision-log、AGENTS、`src/`）。
- 修订规则: 沿用 PACKET §6（任何科学输入/阈值/预算/授权边界变更 = 新版本 re-freeze，不得静默改写）。
