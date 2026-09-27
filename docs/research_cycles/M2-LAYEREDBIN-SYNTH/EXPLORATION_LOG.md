# M2-LAYEREDBIN-SYNTH EXPLORATION_LOG (EXPLORE batch, G-M2-LAYEREDBIN-SYNTH) — APPEND-ONLY

- Packet: `docs/research_cycles/M2-LAYEREDBIN-SYNTH/PACKET.md` (§§0–9 frozen).
- Prompt: `docs/research_cycles/M2-LAYEREDBIN-SYNTH/M2-LAYEREDBIN-SYNTH-PROMPT.md`.
- Track: doc-only draft = no gate; FUTURE execution = EXPLORE. Branch `formal-ir-v72p1-addendum-clean`, frozen HEAD `8e9c8526` (re-verify before execution).
- Claim ceiling（引用本批数值的文档必须逐字携带）：**“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**
- Rule: append-only. No rewrite, no deletion. Per-arm files forbidden; this log + batch-end review only.

## Entry 0 — PRE-AUTHORIZATION (BLANK)

- Status: `NOT-GRANTED`.
- Authorization (§7): ________
- Roots (`workspace/m2lb_<uuid8>`): ________ (absent proof: ________)
- Grant verbatim / signature: ________
- Date / main thread: ________
- Superseded: 本 Entry0 BLANK 历史保留；§7 状态与 12 臂执行以 Entry3/Entry4 为准 (PACKET §7 FROZEN + R1 修订指针)。

## Entry 1 — Pre-EXECUTE Q0–Q6 + EXECUTE BLOCKER (2026-09-24, operator coder-fast, Track EXPLORE)

- Pre-EXECUTE (任一 FAIL 即 STOP；以下逐项二值):
  - Q0 HEAD/branch: `8e9c8526` == 冻结基线 ✓ / `formal-ir-v72p1-addendum-clean` ✓ → PASS。
  - Q1 范围: `git diff -- src/` EMPTY ✓；`results/` + `comparison_bench/outputs_comparison/` 无 tracked 变更 ✓；
    本包 additive 清单: `cli/m2lb_arm_runner.py` + `methods/layered_binary.py` +
    `tests/test_m2lb_arm_runner_fake.py` + `tests/test_m2_layered_binary_fake.py`；
    他包 additive 文件 (m0/m2hdc/p4/timing runners, hd_cascade, openspec changes) 在场但未碰 (out-of-scope note) → PASS with note。
  - Q2 机验: F2 修正后 6 行 multiset 全合 (197:{20:7,19:3}, 201:{21:1,20:9}, 203:{21:3,20:7},
    207:{21:7,20:3}, 204:{21:4,20:6}, 208:{21:8,20:2}；Σ=m，≤64) ✓；
    F3 盲表 `m_init=m-20 + [4×5]` 6 levels ✓；F4 pins 300/3 ✓；
    bundle 三源 key 在场 + 只读 G-D bind 3/3 (g1 (32,1024), g2 (32,32,1024)) ✓ → PASS。
    附带门 verdict 记录 (非 Pre-FAIL): G-B 在 1M-201 (1.303241) / 1.5M-207 (1.300008) 为 FAIL (包内预期高 m FAIL)；
    G-C N_req (680/inf/608/inf/504/2842) 全 >240 (report-only, 预期 FAIL)。
  - Q3 根: `workspace/m2lb_*` 缺席 ✓；12 uuid8 候选冻结:
    01:18eb57a9 02:99d2bfef 03:d4d24a1a 04:2c09cb2d 05:bb3120fc 06:261d611c
    07:24f99582 08:407d9236 09:b9a4fdd7 10:aae025fc 11:84150bd6 12:fc719214
    (`test ! -e` 12/12 absent；填入 PACKET §7-2 属主线程授权行为，本条仅记录候选) → PASS。
  - Q4 fake 重跑 (T2): `test_m2lb_arm_runner_fake.py` 10 passed +
    `test_m2_layered_binary_fake.py` 4 passed = 14 passed, 0 failed → PASS。
  - Q5 零生产调用: 未执行任何 `--execute-real`；仅 import/只读算术/fake 测试；无新根产生 (`workspace/m2lb_*` 复验缺席) → PASS。
  - Q6 预算: 每臂 wall≤1800s / 单 decode terminal≤300s / RSS<4GiB / 1 CPU / 总额 21600s 确认；
    本机 15GiB RAM，8 CPU → 执行时须约束至 1 CPU → PASS (条件记录)。
- EXECUTE 尝试与 BLOCKER:
  - 零副作用探针: `spa_decode_production([],[],[],{},0,300,3)` →
    `NotImplementedError: production binary-SPA decode is grant-gated (no fake/test call)`
    (`m2lb_arm_runner.py:428`)。生产二元 SPA 译码路径未实现 (placeholder raise)。
  - 若强行 `run_execution`，每臂将在 block 0 烧掉真实 PEG 构造 (~20 builds) 后记 vacuous `FAIL(budget)` error 行，
    无 FER/披露/f/λ 证据意义且污染 12 根；故 12 臂生产 EXECUTE 未启动，已建根数 0。
  - repair: 未使用 (`no repair path used`；无基础设施失败可修，缺的是科学路径实现)。
  - 授权状态 note: §7-2 仍为占位 `<m2lb-uuid8-01..12>` (本条候选待主线程填冻结)；§7-8 verbatim + §7-9 2026-09-24 由主线程见证。
- 待主线程单决策 (BLOCKER 待决): 为冻结二元 SPA 生产译码接线立新包/修订包 (译码核改动 = 科学输入变更，
  本包内 STOP)，重冻 §7 后再授权 12 臂；或正式降级本批范围。12 臂在此之前保持未执行。
- Claim 固定句: **“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**

## Entry 2 — Pre-EXECUTE Q0–Q6 复验 + T2 12臂 EXECUTE BLOCKER (2026-09-24, operator coder-fast, Track EXPLORE 合成)

- 授权前提 (orchestrator 冻结指令): PACKET §7-8 用户一并授权已落闭环；R1选项A + numpy fallback 已落地 (wrapper `resolve_spa_decode_fn`/`spa_decode_with_explicit_fallback`/`_spa_decode_numpy_planes` + `methods/binary_spa_numpy.py`，本体 `spa_decode_production` STOP不动)；本次执 T2 12臂各240块。
- Pre-EXECUTE Q0–Q6 (任一 FAIL 即 STOP；以下逐项二值):
  - Q0 HEAD/branch: `8e9c852646087fe513bab45129a2f939e94f066e` / `formal-ir-v72p1-addendum-clean` == 冻结基线 ✓ → PASS。
  - Q1 范围: `git diff -- src/` EMPTY ✓ (`SRC_EMPTY_PASS`)；`results/` + `comparison_bench/outputs_comparison/` 无 tracked 变更 ✓ → PASS。
  - Q2 机验: F2 6行 multiset 全合 (197:{20:7,19:3}, 201:{21:1,20:9}, 203:{21:3,20:7}, 207:{21:7,20:3}, 204:{21:4,20:6}, 208:{21:8,20:2}；Σ=m，≤64) ✓；F3 `m_init=m-20 + [4×5]` 6 levels ✓；F4 pins 300/3 ✓；`bind_empirical_bundle` 三源 1M/1p5M/2M 只读 3/3 ✓ → PASS。
  - Q3 根: `workspace/m2lb_*` 缺席 ✓；沿用冻结 12 uuid8 (01:18eb57a9 02:99d2bfef 03:d4d24a1a 04:2c09cb2d 05:bb3120fc 06:261d611c 07:24f99582 08:407d9236 09:b9a4fdd7 10:aae025fc 11:84150bd6 12:fc719214；`test ! -e` 12/12 absent) → PASS。
  - Q4 fake: `test_m2lb_arm_runner_fake.py` + `test_binary_spa_numpy_fallback.py` + `test_m2_layered_binary_fake.py` = 26 passed, 0 failed ✓ → PASS。
  - Q5 零生产译码调用 (Pre-EXECUTE): 真体 `spa_decode_production([],[],[],{},0,300,3)` → `Refusal(2) STOP-BLOCKED: ldpc backend absent` (本体STOP不动 ✓)；runner 无 `ttbin` 字串 (grep 0)；`workspace/m2lb_*` 复验缺席 ✓ → PASS。
  - Q6 预算: 每臂 wall≤1800s / 单 decode terminal≤300s / RSS<4GiB / 1 CPU / 总额 12×1800=21600s ✓ → PASS (条件记录)。
- Backend对照 (APPENDIX三处一致，以附录为准):
  - `BACKEND_ID` 精确字面量 `"numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"` ✓ (`binary_spa_numpy.BACKEND_ID` + `resolve_spa_decode_fn(find_spec_fn=lambda n: None)` → `(_spa_decode_numpy_planes, 该字面量)`；`ldpc` 本机 `find_spec` = None，走缺席分支 ✓)。
  - 本体 `spa_decode_production` 459-461 refuse 未动，真体缺席即 STOP-BLOCKED，永不切 bit-flip ✓。
  - assumed 非ldpc不可比声明: fallback 为 assumed 先验 + 非ldpc后端，与真体数不可比、不可互换、不可合并；`backend_used` 仅经 log + metadata 侧车透出精确字面量，永不进 outcome dict (13键以外零新增)；CLAIM_CEILING 原文见本条末。
- EXECUTE 尝试与 BLOCKER (冻结调用形 `execute(decode_fn=resolve缺席分支)`，construct 用生产默认；零 `.ttbin` 读；未改冻结模块；未写 `results/`/`outputs_comparison/`；未碰他包；未 commit/push):
  - Arm01 `M2LB-1M-197-matched` @ `workspace/m2lb_18eb57a9` (bundle `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` key `1M` 只读绑定): `execute(root, arm, bundle=bound, bundle_label=bpath, decode_fn=_spa_decode_numpy_planes)` → `Refusal(2)`: `plane 0 m_j=20 binary-support GF(2) rank 19 != 20 (STOP-BLOCKED; measured girth 6)` (`m2lb_arm_runner.py:816` in `_construct_gate_planes` ← `execute:1204`)；根未建 (`exists after False`)。
  - 确证臂 `M2LB-2M-204-matched` @ `bb3120fc` + `M2LB-1M-201-blind` @ `fc719214`: 同门同错 (`plane 0 m_j=21 rank 20 != 21` / `plane 0 m_j=21 rank 20 != 21`)，根均未建。另对 6×m × fidx 0..2 直调门诊断 18/18 同错 (197/201/203/207/204/208 全 FAIL)。
  - 结构根因 (非瞬态infra): 冻结构造 `lam={2:1}` 列重恒2 → 各列偶重 → 全行和 mod2==0 → 支撑H秩 ≤ m_j-1 (实测 m19→18, m20→19, m21→20；`sum rows mod2==0 True`；PEG 原生 GF(1024) rank 满 20 但 R1冻结明令不读该字段、重算二元支撑秩)；故 R1选项A `binary-support GF(2) rank==m_j GATED` 与冻结 `lam={2:1}` 结构互斥，12臂任一 block 0 即 STOP (科学输入不一致，非infra)。
  - 计数/wall/RSS: 已建根数 0/12；成功块 0；FER/披露/f/λ 无证据 (decode 未达，outcome 13键未产生；13键门 `_check_outcome` 未进)；wall/RSS 未耗 (block 0 门前 STOP，无 INCOMPLETE-wall)；`backend_used` 侧车已验 (resolve 字面量 + wrapper sidecar 隔离，见 Q4 fallback 7测)。
  - repair: 未使用 (`no repair path used`；非infra失败，无预注册repair适用；第二次确证失败即 STOP-BLOCKED，余下9臂未试，保留缺席)。
- 待主线程单决策 (BLOCKER 待决): 为 `lam={2:1}` vs 二元满秩门立新包/修订包 (科学输入变更，本包内 STOP；例如改 lam / 放宽秩至 m-1 / 恢复GF秩，重冻 §7 后再授权 T2)，或正式降级本批范围。12臂在此之前保持未执行 (0/12)。
- Claim 固定句: **“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**

## Entry 3 — Pre-EXECUTE Q0–Q6 复验 + T2 12臂 EXECUTE 启动 (2026-09-24, operator coder-fast, Track EXPLORE 合成)

- 授权前提 (orchestrator 冻结指令，转述不改写): PACKET §7 doc 本体不动 (仍 BLANK, operator 不自填)；执行权 = 用户一并授权已落闭环 (§7-8 verbatim “授权不用找我，我现在一并授权”，主线程见证) + R1选项A + numpy fallback + rank∈{m-1,m}容忍已落地 (m2lb 19 passed) + fallback 附录；本次重执 T2 12臂各240。FROZEN: PACKET §7 + R1 7条 + rank修订 + fallback附录。
- Pre-EXECUTE Q0–Q6 (任一 FAIL 即 STOP；以下逐项二值):
  - Q0 HEAD/branch: `8e9c852646087fe513bab45129a2f939e94f066e` / `formal-ir-v72p1-addendum-clean` == 冻结基线 ✓ → PASS。
  - Q1 范围: `git diff -- src/` EMPTY ✓；`git diff --name-only -- results/ comparison_bench/outputs_comparison/ outputs_comparison/` 无输出 ✓；rg 本包三文件 + additive 实现 (runner/methods/tests/附录) 在场，`test_m2hdc_arm_runner_fake.py` 仅提及未改 (out-of-scope note) → PASS with note (同 Entry 1 口径)。
  - Q2 机验: F2 6行 multiset 全合 (197:{20:7,19:3}, 201:{21:1,20:9}, 203:{21:3,20:7}, 207:{21:7,20:3}, 204:{21:4,20:6}, 208:{21:8,20:2}；Σ=m，≤64) ✓；F3 `m_init=m-20 + [4×5]` 6 levels ✓；F4 pins 300/3 ✓；`bind_empirical_bundle` 三源 1M/1p5M/2M 只读 3/3 (g1 (32,1024), g2 (32,32,1024)) ✓ → PASS。
  - Q3 根: `workspace/m2lb_*` 缺席 ✓；沿用冻结 12 uuid8 (01:18eb57a9 02:99d2bfef 03:d4d24a1a 04:2c09cb2d 05:bb3120fc 06:261d611c 07:24f99582 08:407d9236 09:b9a4fdd7 10:aae025fc 11:84150bd6 12:fc719214；`test ! -e` 12/12 absent) → PASS。
  - Q4 fake: `-o addopts=""` (绕过 pytest.ini Windows basetemp；Linux 下默认 addopts 误触 `D:/...` 路径) → `test_m2lb_arm_runner_fake` 19 + `test_m2_layered_binary_fake` 4 + `test_binary_spa_numpy_fallback` 7 = 30 passed, 0 failed ✓ → PASS。
  - Q5 零生产 (Pre-EXECUTE): 真体 `spa_decode_production([],[],[],{},0,300,3)` → `Refusal(2) STOP-BLOCKED: ldpc backend absent` (本体STOP不动 ✓)；runner 无 `ttbin` 字串 (grep 0)；`workspace/m2lb_*` 复验缺席 ✓ → PASS。
  - Q6 预算: 每臂 wall≤1800s / 单 decode terminal≤300s / RSS<4GiB / 1 CPU / 总额 12×1800=21600s ✓ → PASS (条件记录)。
- Backend对照 (附录三处一致，以附录为准): `resolve_spa_decode_fn(find_spec_fn=lambda n: None)` → `(_spa_decode_numpy_planes, "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)")` == `binary_spa_numpy.BACKEND_ID` ✓；`ldpc` 本机 `find_spec` = None，走缺席分支 ✓；本体 459-461 refuse 未动。
- 定时探针 (零证据主张): `M2LB-1M-197-matched` max_blocks=1 + 生产构造默认 + 缺席分支 → 0.2s `PROBE-truncated` (failures 0, decodes 1)；探针根 `workspace/m2lb_a1b2c3d4` (非冻结uuid，PROBE-only) 已删，12 根仍缺席。
- EXECUTE 启动 (冻结调用形 `execute(decode_fn=resolve缺席分支)`，construct 生产默认；`spa_decode_with_explicit_fallback(..., find_spec_fn=缺席, sidecar=逐臂)` 包缺席分支并记 `backend_used` 侧车；零 `.ttbin` 读；未改冻结模块；输出仅 12 根 + 本 LOG；禁 `results/`/`outputs_comparison`/他包/commit/push):
  - 臂序 (§7-7): 01:M2LB-1M-197-matched@18eb57a9 02:M2LB-1M-201-matched@99d2bfef 03:M2LB-1.5M-203-matched@d4d24a1a 04:M2LB-1.5M-207-matched@2c09cb2d 05:M2LB-2M-204-matched@bb3120fc 06:M2LB-2M-208-matched@261d611c 07:M2LB-2M-204-blind@24f99582 08:M2LB-2M-208-blind@407d9236 09:M2LB-1.5M-203-blind@b9a4fdd7 10:M2LB-1.5M-207-blind@aae025fc 11:M2LB-1M-197-blind@84150bd6 12:M2LB-1M-201-blind@fc719214 (各 N=240)。
  - 停止/修复: 超时不重跑 (INCOMPLETE 保留)；第二次失败即 STOP-BLOCKED (余臂保留缺席)；至多一次 repair 仅非 Refusal 基础设施异常 (科学输入/种子/阈值/数据角色/假设不变)；outcome 13 键由 `_check_outcome` 门控，`backend_used` 仅 log+sidecar (精确字面量，永不进 outcome)。
- Claim 固定句: **“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**

## Entry 4 — T2 12臂 EXECUTE 结果 (2026-09-24, operator coder-fast, Track EXPLORE 合成)

- 执行形态: `/tmp/opencode/m2lb_t2_run.py` (operator scratch, 非仓库输出) 顺序执行 12 臂；`execute(root, arm, bundle=只读绑定, bundle_label=冻结路径, decode_fn=spa_decode_with_explicit_fallback(find_spec_fn=缺席, sidecar=逐臂))`；construct 生产默认；各臂 N=240 上限；零 `.ttbin` 读；冻结模块未改；无 commit/push。RUNNER_EXIT:0，repair 使用 0 次。
- 逐臂结果 (verdict/fails/blocks/FER/f_super→f_eff/undetected/G-A…G-E/decodes/wall/backend_used):
  - 01 M2LB-1M-197-matched@18eb57a9: FAIL-early-stop 13/60 FER 0.2167 1.278858→2.315755 und 2 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 60 wall 14.0s backend ✓字面量。
  - 02 M2LB-1M-201-matched@99d2bfef: FAIL-early-stop 13/58 FER 0.2241 1.303241→2.375892 und 3 A-FAIL/B-FAIL/C-expFAIL/D-PASS/E-PASS dec 58 wall 12.3s backend ✓。
  - 03 M2LB-1.5M-203-matched@d4d24a1a: FAIL-early-stop 13/58 FER 0.2241 1.276350→2.349001 und 3 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 58 wall 12.0s backend ✓。
  - 04 M2LB-1.5M-207-matched@2c09cb2d: FAIL-early-stop 13/64 FER 0.2031 1.300008→2.272098 und 4 A-FAIL/B-FAIL/C-expFAIL/D-PASS/E-PASS dec 64 wall 13.1s backend ✓。
  - 05 M2LB-2M-204-matched@bb3120fc: FAIL-early-stop 13/58 FER 0.2241 1.271488→2.344139 und 3 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 58 wall 12.1s backend ✓。
  - 06 M2LB-2M-208-matched@261d611c: FAIL-early-stop 13/80 FER 0.1625 1.294947→2.072619 und 4 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 80 wall 16.6s backend ✓。
  - 07 M2LB-2M-204-blind@24f99582: FAIL-early-stop 13/58 FER 0.2241 1.271488→2.344139 und 3 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 132 wall 27.7s backend ✓。
  - 08 M2LB-2M-208-blind@407d9236: FAIL-early-stop 13/80 FER 0.1625 1.294947→2.072619 und 4 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 154 wall 30.8s backend ✓。
  - 09 M2LB-1.5M-203-blind@b9a4fdd7: FAIL-early-stop 13/58 FER 0.2241 1.276350→2.349001 und 3 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 134 wall 25.7s backend ✓。
  - 10 M2LB-1.5M-207-blind@aae025fc: FAIL-early-stop 13/64 FER 0.2031 1.300008→2.272098 und 4 A-FAIL/B-FAIL/C-expFAIL/D-PASS/E-PASS dec 139 wall 25.1s backend ✓。
  - 11 M2LB-1M-197-blind@84150bd6: FAIL-early-stop 13/60 FER 0.2167 1.278858→2.315755 und 2 A-FAIL/B-PASS/C-expFAIL/D-PASS/E-PASS dec 143 wall 26.7s backend ✓。
  - 12 M2LB-1M-201-blind@fc719214: FAIL-early-stop 13/58 FER 0.2241 1.303241→2.375892 und 3 A-FAIL/B-FAIL/C-expFAIL/D-PASS/E-PASS dec 138 wall 26.8s backend ✓。
  - (backend 全臂断言 `== "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"` 通过；`backend_used` 仅 sidecar/log，rows.json/summary 抽查无泄漏；outcome 13 键由 `_check_outcome` 全程门控。)
- 门语义注记: 12 臂一致 `FAIL-early-stop` + CENSORED (fails-at-stop/blocks-at-stop 实报，projected NEVER) — 系 G-A 门逐臂 verdict (包内预期行为)，非 §3.2 预算失败；无 INCOMPLETE-wall、无 FAIL(budget)、无 Refusal、无第二次失败、无 STOP-BLOCKED；repair 0 次 (`no repair path used` 同效)。
- 结构注记: rank∈{m-1,m} 修订后生产 PEG 构造门 12 臂全过 (Entry 2 的 `lam={2:1}` vs 满秩门 BLOCKER 已消)；numpy fallback 下 FER≈0.16–0.22，bar-12 在 58–80 块处触发；G-B 在 1M-201/1.5M-207 为 FAIL (包内预期高 m FAIL，与 Q2 预告一致)；G-C 全臂 report-only expFAIL。
- 范围复验 (EXECUTE 后): `git diff --name-only -- src/ results/ comparison_bench/outputs_comparison/ outputs_comparison/` 无文件名输出 ✓；12 根各 3 件 (`M2LB_RESULT_*.md` + `rows.json` + `block_accounting.csv`) ✓；抽查 arm01: 60 行 fails 13 und 2 独立、csv 39 列、md 含 arm/f_eff/λ/固定句 ✓；总 wall 约 243s ≪ 21600s ✓。
- 待主线程: batch-end 独立 review + acceptance (本 batch 不做 acceptance；本条仅为 operator 执行记录)。
- Claim 固定句: **“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**
