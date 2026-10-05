# 粘贴用 prompt — MSD 路线续推（2026-10-05）

> 把分隔线之间的内容原样粘贴给新 session。

---

你接手 `D:\Code\HD-QKD_Polar_Comparison`，分支以现场 `git branch --show-current` 为准（预期 `formal-ir-v72p1-addendum-clean`）。

**必读**：`AGENTS.md`、`docs/REBOOT_HANDOFF_20261004.md`（R1–R9 硬约束）、`docs/ROADMAP_20261005_MSD.md`（本轮路线，覆盖 NOW.md 里旧的「下一步」排序）。

**审查结论（不得重犯）**：上一轮在整理完成后，又做了 17 次提交、约 6k 行代码和测试、8 组验收及其独立审查，但 **MSD 解码次数为零**；而且在解码器存在之前，就把真实数据比较设计（共同体量配对、G-ENV、角色 metadata）设成了阻塞门。这正是 E3/E6 的重犯。

**用户裁决（路线文档 §2.1）**：MSD 为主线，NB-LDPC 作 M4 对照臂；M5 真实帧原则同意，但具体命令和预算仍须在 Pre-EXECUTE 时获得用户明确确认；发表口径为 G0=(B)。

**本次任务**：执行路线文档 §3：
1. 把 COMMON_VOLUME_SCOPE / G-ENV / 角色 metadata 线标为 parked-until-M4（只改状态说明，不删文件）。
2. 写 **M1**（标定合成信道上的 MSD 解码闭环）的单个 EXPLORE packet + 单日志。要求：
   - 信道：从已批准的 R1 TRAIN 联合计数抽样；
   - 码：逐面二元 LDPC，N=16384 为主、N=1024 为对照，natural LSB-first，条件软先验；
   - 复用 `msd_sparse_code.py`、`msd_conditional_prior.py`、`methods/binary_spa_numpy.py`；
   - 先做 ≤2 min 计时 smoke，再按实测成本和 MDE 定块数；
   - 主度量是带期望良率的 f。
3. 实现并运行 M1（合成、EXPLORE，在用户已授权的 P1→P2/P3→P4 持续推进范围内）；同时做 M3（SPA 核逐位一致的 numba/C 移植）。
4. 精简 NOW.md 为一屏导航，移除额度、兑换卡等运维记录。

**硬约束**：
- 每个里程碑只做一次批末独立审查，中间步骤只跑聚焦数值测试；
- 一个工作日内如果没有产生新的解码或性能数字，下一步必须是产生数字的步骤；
- 不读新的真实数据或 raw，不做真实帧运行，不发表，不 push（push 先问用户）；
- 不删除文件；scoped 提交，禁 `git add -A`。

**返回条件**：
1. M1 有结果：报告每面 FER–码率曲线、实用码隙、三源 `f_expected`（N=16384 与 N=1024）、每块成本、提交哈希，以及推荐的下一步（M2 或 M1′）及其预期收益和成本。
2. 遇到具体阻塞：给出失败命令、报错、已尝试的补救，以及需要用户做的那**一个**决定。

---
