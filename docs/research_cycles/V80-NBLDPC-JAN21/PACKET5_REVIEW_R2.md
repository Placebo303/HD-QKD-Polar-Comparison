# PACKET5 再审（R2）— PASS WITH COMMENTS（整改件 mtime 2026-09-23 22:01–22:06 之后；本件为 2026-09-24 docs-only 落档）

- 文件性质：**docs-only 评审结论落档**。Track = **documentation-only — 无 track gate**
  （AGENTS.md §1.2 适用性矩阵 "Documentation-only changes" 行）。
- 本文件**不授权任何执行**：零解码、零构造、零真实数据访问、零 commit/push、
  零保护根写入；**不改**任何既有正文 / 阈值 / 路线 / packet（允许面 = 本件 +
  `PACKET5_REVIEW_R1.md` + `AGENT_PROJECT_MEMORY.md` 尾部追加）。
- 来源与保真：按 memory-free triage（建议 A+B）转录会话中的再审结论 +
  仓内可佐证事实，**不含推测**；测试计数为当时转录，本文件**未重跑**任何测试。
- 时点：整改件（`openspec/changes/p4-feas-construct-runner/proposal.md` 22:01、
  runner 22:05、fake-only 测试 22:06）均落盘后再审；确切墙钟未在仓内留存。

---

## §1 判定（Verdict）

**PASS WITH COMMENTS** — **0 BLOCKER / 0 MAJOR / 5 MINOR**。

- 5 MINOR **全部为文档精度级**（措辞/引用/精度类，不触及授权边界、阈值、
  科学语义与 claim ceiling）；**细目不在本转录要点内，本件不推测**。
- **focused fake-only 测试 20 passed**（R2 时点；R1 为 19 passed）。
  仓内旁证：`comparison_bench/tests/test_p4_feas_construct_fake.py` 现含
  **20 个 `def test_`**，其中含 M5 整改新增的
  `test_cli_log_refuses_forbidden_roots_same_as_root` —— 与 19 → 20 的 +1 相符。

## §2 BLOCKER / MAJOR 清零核对

| 首审项 | R2 状态 | 仓内佐证 |
|---|---|---|
| **B1** 事故零落档 | **已清**；且**三点待裁已明确写成文字**（补录只建议、不代裁决） | `P4_FEAS_INCIDENT_ADDENDUM.md`：§1 事故事实、§2 零后果边界（零落盘/零解码/无 pins 可复用/科学输入零变动/现 fail-closed）、§3 待裁三点 = (i) packet §5 至多 1 次 repair 名额**是否计数**（"不耗 repair" 为建议、**未裁**）、(ii) 授权时 Pre-EXECUTE **是否披露**本事故、(iii) 事故窗口内**是否还有其他未落档调用**需补录 |
| **M1** 死算 | **到位**（死算已删除并留删除理由注释） | runner 注释："the former constructor-side base-rank pre-computation was dead … and is deleted"；`construct_and_pin` 经注入 `rank_fn` 自算 `rank_base_400`，构造路径不再预计算 |
| **M5** log 守卫 | **到位**（`--log` 与 `--root` 同级 fail-closed + 专门测试） | `_check_log_path()` 保护根分段拒收 rc=2，在 `execute()` 任何写入前调用；测试 `test_cli_log_refuses_forbidden_roots_same_as_root` |
| **M4** 无 OpenSpec | **到位**（行为记录已建；**不改任何现有 spec**） | `openspec/changes/p4-feas-construct-runner/proposal.md`：自引 "Review finding M4 (MAJOR)"；仅 proposal、无 design/tasks/specs、`Affected specs: None`；与 packet §10(b) "双标准消解" 段并存——packet 仍是唯一执行权威 |
| **M3** NOW失真 | **到位**（`docs/NOW.md` §1/§3/§4 状态与实况一致） | §1 脏树清单（含 ★ 快照后新增 + B1+M3 增量）、§3 执行面就绪 + 事故补录 + G0B/SAME-DATA、§4 P3-gate `PROPOSED` 行 |
| **M2** 接口不兼容 | **只记录、不选型**（**不计入已清**，留须决） | proposal.md §"M2 interface incompatibility — PENDING ADJUDICATION (recorded, not selected)"：两侧形态逐字并列，**未冻结任何 runner 名、未选任何选项**；裁决属主线程 Pre-EXECUTE / packet 修订时点 |

## §3 遗留须决（非阻断本批判定，但须主线程/用户书面裁）

1. **M2 接口**：prompt per-arm 形式 vs runner 双臂单次调用形式，二选一
   （或在 Pre-EXECUTE 记录中接受显式翻译步）；随附 `<P4FEAS_RUNNER
   [TO BE FROZEN]>` / `<P4FEAS_TEST_FILE [TO BE FROZEN]>` 占位符回填。
2. **600–1800 帽实测**：`P4_FEAS_PACKET.md` §5 的单次构造 **≤600 s**、单臂 wall
   **≤1800 s** 目前依据段自称"估，非承诺"（runner 内 `P4_CONSTRUCT_CAP_S=600`、
   `P4_WALL_CAP_S=1800` 只是常量转录）——帽是否切合须**执行时实测**校准记录，
   不得把估计当已验证预算。
3. **B1 三点**（见 §2 首行 (i)(ii)(iii)）——含"不耗 repair"建议是否采纳。
4. **5 MINOR 文档精度细目**（本件不推测；按 §1 类别处置即可，不阻断）。
5. **状态确认（同列须知，非新裁）**：**P4 仍 `FROZEN NOT GRANTED`**
   （`P4_FEAS_PACKET.md` §10(d) BLANK、臂根 `[TO BE FROZEN]` ⇒ 禁任何构造执行）；
   **P3 仍 `PROPOSED`**（re-freeze v2 §2.5 阈值 T-M1..M4 已填数但授权时须逐项
   确认，签字块 BLANK ⇒ 未授权）。

## §4 边界（本批）

- 本批为 **docs-only**：**不授权任何执行、commit、push**；本件与 R1 件、
  memory 尾部追加**均未 commit**。
- **claim ceiling 不变**：无 FER / SKR / 资格化 / 发表主张被本批判定触及；
  P4 本包只产（未来授权后的）构造可行性证据。
- **P4 升为 S3 必经与否留待未来 DECIDE**（`docs/NOW.md` §2 / decision-log F3：
  不因 P1-FAIL 自动升格）——本件不裁。
- R1 的通过面不得回归：授权块 BLANK、保护根零写入、科学语义、claim ceiling。

**配套落档**：`PACKET5_REVIEW_R1.md`（首审 NEEDS-CHANGES 明细）＋
`AGENT_PROJECT_MEMORY.md` 尾部 2026-09-23 五包收口条（交付、复审结论、
开放待裁、边界、指针）。
