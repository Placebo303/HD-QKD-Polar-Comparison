# M5 INDEPENDENT ACCEPTANCE（主线程接受记录）

- Pre-RESULT 独立审查三轮：首轮 FAIL（记录项 F-E/F-B/F-F1/F-A/F-F2/O-F3）→
  返工（log 修正 + verdict 伴件 + RESULT 修正）→ 第二轮逐项核验 **PASS**，固化 run_01。
- 主线程接受本 DECIDE 结果（范围见 M5_RESULT.md ceiling）：
  NB-marginal 真实传递一致（6/6 臂）；MSD 冻结真实不一致（52/52，plane-1 隔离）；
  不测尾部、不仲裁、不 KILL。
- 后续：MSD 需先验稳健性修复 + 重新验证（M1″-prior，不在本批）；U-1 并行有效，
  NB 为当前可部署线。
- 证据链：M5_PREEXECUTE.md（授权+检查单）→ m5_*_summary.json（冻结行）→
  m5_verdicts.json（band verdict + f 全输入重算）→ M5_RESULT.md → 本接受记录。
  独立审查结论与主线程接受一致，无分歧保留。

> **Supersession note (2026-10-06, review F-1, original text above unchanged):**
> 本接受记录所接受的"NB-marginal 真实传递一致"仅限 u2 层；完整符号口径下
> NB 真实失败率约 47–64%，"可部署"含义已撤回。三轮 Pre-RESULT 未核对成功字段的
> 层覆盖（R13 新增此必查项）。接受范围以本说明为准。
