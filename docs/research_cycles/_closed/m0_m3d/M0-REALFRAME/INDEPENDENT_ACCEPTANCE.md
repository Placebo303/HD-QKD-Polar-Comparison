# M0 真实帧闭环 — INDEPENDENT_ACCEPTANCE（G-M0-REALFRAME，独立 Pre-RESULT）

- **包**：`G-M0-REALFRAME`；**Track**：**DECIDE**（真实数据）。
- **分支 / HEAD**：`formal-ir-v72p1-addendum-clean` / `8e9c8526`（执行前后一致，见 `RESULT.md`）。
- **对照基线**：`PREREG_AND_AUTH.md`（冻结 §2–§6） vs `RESULT.md`（执行者记录）
  vs 三个输出根 `workspace/m0_359922a7_1M` / `workspace/m0_642a8fe8_1p5M` / `workspace/m0_b1a9142d_2M`
  内 `rows.json` / `block_accounting.csv`。
- **角色**：独立复核，只验阈值 / 口径 / 隔离 / 分列 / 会计 / 判定与实际产物的一致性；
  不做科学解读（F9(i) 判读归主线程裁决，见 `docs/decision-log.md` 2026-09-24 条下 F9(i) 裁定小节）；
  不重跑、不续跑、不补抄 stdout、不改任何数值。

---

## 第一轮初审：FAIL（B1 + B2）

- **B1 — 跨源 / 跨臂合并**：初审稿把三源计数合并为 103/1/910（fails / undetected / fails_full10 跨源合计），
  违反 PREREG §3“逐源、逐臂分列，禁止合并”与 §6 禁止 ⇒ **FAIL**。
- **B2 — 授权空白**：PREREG §8 授权块空白（空 = 未授权），执行无授权依据 ⇒ **FAIL**。
- **处置**：返工 —— 删除合并数（恢复逐源逐臂分列）、补填 §8 授权块
  （grant verbatim + 日期 / 授权人 + 预算确认）；FAIL 稿保留在案，不删除。

## 返工后重审：PASS（2026-09-24）

- **数值核验 PASS**：`RESULT.md` §2.1–2.3 逐臂抄录（超帧 205 / 287 / 383、fails、undetected、
  FER 及 95% Wilson 区间、fails_full10、f 列、X1 合成对照 fails/240 与区间、overruns、臂 wall、
  峰值 RSS、解码次数）与各根 `rows.json` → `summary` 一致；
  `raw_symbol_errors` 均值 / 最小 / 最大与 `block_accounting.csv` 一致。
- **D1 机械判定 PASS**：6 臂“更差 5 / 一致 1 / 更好 0”为 §4 区间比较的机械结论
  （真实 95% CI vs X1 合成 95% CI），标签与区间一致；作用域仅限“合成信道能否继续作开发代理”，非 P3 verdict。
- **泄漏 / 会计 PASS**：`f_super` / `f_notag` / `f_eff` 公式与各源 H_corr
  （0.80127 / 0.82729 / 0.83333）与 PREREG §3 一致；无 f_super 当 f_eff 报；
  无单点 `f_eff ≤ 1.3` 认证句（最小实测 1.464047）。
- **undetected 隔离 PASS**：合计 1（1p5M m=203），计为失败、永不并入 success。
- **逐源分列 PASS**：无跨源 / 跨臂合并；F1 / F2 断言（偏移 −50 / +50 / +50 ps、配对数、
  切分边界、余数丢弃 407 / 405 / 529）与 R1 一致；预算合规
  （逐源 wall 3409 / 3696 / 4672 s 均 < 5400 s 帽，峰值 RSS 最大 0.73 GiB < 4 GiB，
  overruns 全 0，无重跑 / 续跑 / REFUSED / INCOMPLETE）；保护根零改动
  （`git diff -- src/` 0 B，`results/` 0 B，`outputs_comparison/` 执行前后相同）。
- **F9 核验 PASS（口径）**：F9(i) / (ii) 仅抄录为观测列，未写成 P3 verdict；
  F9(i) 判读留待主线程（`docs/decision-log.md` F9(i) 裁定小节）。

---

## 永久开放项（只影响终端留痕，不影响数值）

- 三源 runner stdout 终态 END / JSON 行未落盘（runner 只 print 到 stdout，未写任何文件）；
  数值来源（`rows.json` → `summary`）与打印字段同源，数值不受影响。
- 补救：发起执行的会话若有 stdout 记录，可逐字抄录进 `RESULT.md` §1
  （或另存 `stdout_END_*.txt`，属新增文件，须主线程另行授权后写入）；
  本独立复核不代抄、不推测。

---

## 接受

- 独立 Pre-RESULT 结论：**PASS**（重审，2026-09-24）。`RESULT.md` 可固化；
  F9(i) 裁决与主线程接受仍按分工由主线程完成。
- 用户签字：**BLANK**（待主线程接受时填写）。
