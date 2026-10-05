# NOW — 一屏导航（2026-10-05）

- 必读：`AGENTS.md` → `docs/REBOOT_HANDOFF_20261004.md`（R1–R9）→ `docs/ROADMAP_20261005_MSD.md`（路线）。
- 现场为准：`git branch --show-current`（预期 `formal-ir-v72p1-addendum-clean`）+ `git status` + HEAD。
- 主度量：带期望良率的 f（R3）；零失败认证句禁用。
- 主线 MSD，NB-LDPC 为 M4 对照臂；发表口径 G0=(B)（用户裁决见路线 §2.1）。
- 当前：M1 合成解码闭环已出首轮实测（natural LSB-first，N=16384 主 / N=1024 对照）。
  - 包：`docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/M1_PACKET.md`（+ M1′a/M1′b 修正包）。
  - 日志（唯一）：同目录 `EXPLORATION_LOG.md`；结果根：`workspace/m1_synthetic/m1_20261005/`。
  - N=16384 operating M2（C_0=2000+K400 单轮 rescue，B=300/源）：f = 1.2310 / 1.2309 / 1.2285
    （upper95 ~1.37），失败 0/300，undetected 0；比 M1′b 好 0.033–0.043，M2 门已过，M1 f≤1.25 门在 point 口径下过。
    M2 包：同目录 `M2_PACKET.md`；结果根：`workspace/m2_synthetic/m2_20261005/`；批末独立审查 PASS（EXPLORE）。
  - M4 同口径对比已齐（批末审查 PASS）：MSD-16384 f≈1.23 长块无对手；
    NB-marginal-1024 f≈1.26–1.39（u2-layer口径）短块占优；Polar 外部引用 ~1.36–1.51 不可比。
- parked-until-M4：`COMMON_VOLUME_SCOPE.md`（G-ENV/角色 metadata 同文件冻结，不推进、不阻塞 decoder）。
- 门：真帧/新 raw/发表/push 均须用户明确确认；push 只普通非强制。
- 索引：`docs/INDEX.md`；旧路径：`docs/archive/PATH_MAP.md`；隔离清单：`docs/archive/QUARANTINE_MANIFEST.md`。
