# CURRENT_TASK.md


## Current Task — V13-R3 fresh 数据准入已拒绝；D1–D5 已执行，D5 drift_exceeded；P/E/V 不进入 (2026-08-16)

**状态：本目标已完成。** D1–D5 已按文档执行并验证；D5 三源 `drift_exceeded`，
P/E/V 不进入。另已运行 README/RUN_COMMANDS 中的安全检查：`unittest` 5/5 通过、
`smoke_test` 通过、`compileall` 通过。

按用户更新后的目标（P0→P1→P2）继续，但 **2026-01-21 三源已通过 D0 判定为
`data_intake_rejected_for_fresh_confirmation`**，不得作为 fresh 证据进入 P/E/V。

- **D0（已完成）**：新增 `v13r3fresh_intake_20260816` 证据包，判定三个
  `2026-01-21` Type2 源不满足 frozen fresh 条件（时间戳早于 V13 历史、损耗
  元数据不可核验；folder1 已有 D2 烟测 `raw_ser=0.254663`，远超 V13 D01
  参考 0.0771）。完整规划：
  `docs/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md`。
- **D1–D5（已完成）**：按修正参数执行完毕（2026-08-16，shell 可用后）：
  D1 环境/git 基线、D2/D3 三源 sidecar 提取（`map_sanity` 全 FAIL）、
  D4 三源 pairs-table + manifest、D5 全量漂移预检。
  D5 结果：**三源全部 `precheck_state=drift_exceeded`**（raw SER mean
  ≈0.240–0.256，偏差远超 0.03 阈值）→ 自动停止，不进入 P/E/V。
- **P1（历史冻结终态保持）**：`v13r3fresh_prepare_20260815/no_eligible_package.json`
  不变；P1 仍阻塞于真正 fresh 数据。
- **P2（V17）**：保持 `mechanism_unverified` 冻结终态；位面/边标签效率路线冻结。
- **push**：仍待用户单独授权；本地文档/证据可先提交。
- **下一步**：若用户提供真正 fresh 10 dB Type-II 数据，则重新进入 D1–D5→P1；
  若用户坚持用 2026-01-21 数据，则另开 legacy drift audit change，不能叫
  fresh-confirmed。

---

## Current Task — P2 V17 门冻结终态 mechanism_unverified；P1 阻塞于 fresh 数据 (2026-08-16)

按用户更新后的目标（P0→P1→P2）继续：

- **P0（已完成）**：V12 归档（`archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`，
  source_partition_blocked/X01/X02 未执行/v2 prepare 包保留）；V15/V16
  归档为 aborted drafts（`...-aborted/`）；陈旧文档全修复；V14 测试
  数字统一（62/62→64/64）。本地领先 `origin/main` 36+ 提交；**push 待
  单独授权**。
- **P1（冻结终态，阻塞于数据）**：change
  `formal-nonbinary-ldpc-v13-r3-fresh-acquisition` 冻结 + freeze review
  ACCEPT；PREP 工具实现（FA1–FA5，19 测试）+ 生产 prepare 执行一次 →
  **`no_eligible_frames`**（`D:\Data` 无 fresh 帧数据源，合法冻结结果；
  包 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_prepare_20260815/`）；
  主线程 review ACCEPT → 判定 **frozen failure（数据不可得）**。
  execute/verify 阻塞于 fresh 数据；用户提供新数据后重新 prepare
  （确定性工具）即可继续。
- **P2（冻结终态，FAIL 类）**：change
  `formal-nonbinary-ldpc-v17-multibit-structured-de-gate` 生产 gate
  执行一次 → **`gate_state=mechanism_unverified`**（Stage 0 锚点 A
  Δ=0.0075>0.005 失败；锚点 B |δ|=0.009≤0.012 通过；Stage 1 模型
  熵 0.549955；Stage 2 12 点诊断全部未收敛）；strict replay 5/5
  字节一致；E02 独立 gate review **ACCEPT（零 blockers）**；C01
  收尾完成。位面/边标签效率路线**冻结**：不启动 V15/V16、不扩大
  搜索、无 rerun/调参。效率路线下一步只能由用户决定另开新 change
  （② SC-LDPC、③ 多边/高维 λ）。

---

## Previous Task — P1 prepare 完成（no_eligible_frames）；P2 V17 门生产执行 (2026-08-15)

2026-08-15 状态，已被上方 2026-08-16 Current Task 取代（P2 已冻结
关闭）。P1 `no_eligible_frames` 终态与 P2 实现/生产执行记录见上。

---

## Previous Task — V14 效率可行性门：FAIL（效率路线冻结）；V15/V16 不立项 (2026-08-15)

V14 gate（`openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/`）
按冻结计划完成：Stage 0 机制回归 PASS、Stage 1 折叠验证全绿、Stage 2
的 12 个 q=1024 冻结点（3 λ × m∈{15,16,17,18}）**全部非收敛**（最终
base-q 熵 0.288–0.357，阈值 0.01 的 29–36 倍）→ **gate_state=fail**。
E02 独立 gate review ACCEPT（FAIL 机械正确、纪律干净）；strict replay
完成（科学文件 5/6 字节一致、manifest 仅 provenance 四字段差异，
V10 先例）；C01 完毕（decision-log + 记忆 §49）。

- 结论：冻结的普通不规则系综在 rate 0.93–0.94（f≤1.3 区间）上无 BP
  收敛点——效率路线按 V14 冻结纪律**终止**；V15/V16 提案/设计骨架
  已于 2026-08-15 归档为 aborted drafts（见 P0）。
- 路线状态：V13 R3（f≈12.1）仍是唯一经验证的精确纠错器；
  fresh-confirmation-only 路线不受影响（P1 已启动）。

---

## Previous Task — V13 Existing-Data Nonbinary LDPC Diagnostics: COMPLETE (2026-08-14)

The change
`openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/` has
completed the full frozen route and reached the terminal claim
**`ready_for_fresh_confirmation`**: P01-P08 accepted; D01-D03 + DT0-DT2; D04
baseline probe (8/32 exact); D05 root-cause (`code` / `diagnosis_complete`,
independent review ACCEPT); R3 code-only candidate `nbldpc_v13_r3_code_v1`
(frozen amendment; IT0-IT3, 49/49 tests); E01 screen 64/64 candidate exact
(baseline 13/64); E02 (candidate frozen); A01 retrospective audit 128/128
exact -> `ready_for_fresh_confirmation`; A02 cross-stratum bw120 128/128 +
bw180 128/128 (no promotion); **C01 independent acceptance ACCEPT (zero
blockers)**. Memory triage done (AGENT_PROJECT_MEMORY §47).

- Evidence packages (all under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/`):
  v13_d01_20260814, v13_d04_20260814, v13_d05_20260814_corrected (+
  v13_d05_20260814_invalid_execution_notice.json for the retained first
  emission), v13_e01_20260814, v13_a01_20260814, v13_a02_20260814. All
  verified read-only and committed (ed4bb690 .. 4c0f27a4).
- Claim boundary: `ready_for_fresh_confirmation` is the MAXIMUM V13 state —
  NOT promotion/qualification/fresh correction. **User decisions pending**
  (independent of V13, not auto-triggered): ① whether to open a NEW OpenSpec
  change for fresh acquisition (new frame identities, prepare/review/
  execute/verify chain) to advance confirmation/qualification/promotion of
  the R3 candidate; ② the V12 archive decision (separate housekeeping; V12
  stays `source_partition_blocked`, X01/X02 not reopened).

---

## Previous Task — V13 Existing-Data Nonbinary LDPC Diagnostics: READY_FOR_FRESH_CONFIRMATION, C01 PENDING (2026-08-14)

Earlier 2026-08-14 state, superseded by the freeze review and D stage above.
The new planning change
`openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/`
recorded the user's decision to diagnose the algorithm using existing 10 dB
Type-II, q=1024 Gray 256-symbol data before considering a new acquisition.
Existing rows were sufficient for retrospective diagnostics/development, but
their frame/payload identities are historical V4/V5 identities and cannot be
fresh-canary, confirmation, qualification, or promotion evidence.

- P01-P07 were drafted only; P08 (independent read-only freeze review) was
  the next scientific task and is since complete.
- All D/R/I/E/A/C tasks were unauthorized and unexecuted; the planning turn
  performed no code change, test, decoder call, telemetry run, data
  execution, output generation, archive, or Git write operation.
- V12 remained `source_partition_blocked`; its archive is a separate
  housekeeping decision and did not block V13 plan review. Do not reopen
  V12-X01/X02.
- If later authorized, diagnostic artifacts go only to the additive
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/` root;
  frozen baseline directories and official qualification roots stay unchanged.
- The six-file diagnostic package uses `diagnostic_outcomes.csv` for baseline,
  candidate-development, and retrospective-audit rows with explicit `phase`
  and `method` fields.

Claim boundary was: the highest future V13 state is
`ready_for_fresh_confirmation`; fresh acquisition or qualification requires a
separate OpenSpec change and explicit user decision.

---

## Previous Task — V12 Nonbinary LDPC Real Micro-Feasibility: TERMINAL `source_partition_blocked` (2026-08-13)

The change
`openspec/changes/formal-nonbinary-ldpc-v12-real-micro-feasibility/` is in
TERMINAL STATE **source_partition_blocked**: the four-frame bw200
micro-feasibility canary cannot be executed because the reconstructed
traceable 10 dB pool (2304 rows, 768 per stratum incl. 768 bw200 rows) is 100%
covered by historical frame/payload identities from the V4 10 dB/16 dB
transfer locks and V5 development/partition role locks (2848 excluded frame +
2688 excluded payload identities; identical union in both prepare runs). Zero
fresh eligible bw200 rows; a fresh acquisition would be required for any
future four-frame canary.

- Implementation (V12-I01..I05) and engineering acceptance (V12-T0..T2, 41/41)
  complete; prepare lane (RP01-RP03) executed, official package at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
  (v1 intermediate deleted by explicit user decision).
- Decision-log and memory triage completed on 2026-08-13; V12-D02 is complete.

There is currently no authorized execution successor. The next action is the
user's archive decision for this V12 change. Archiving does not execute
V12-X01/X02, merge unattained requirements, or manufacture a success
declaration; retain the `source_partition_blocked` terminal state and the v2
three-artifact prepare package. The alternative is fresh-acquisition
feasibility/planning, but only if the user explicitly wants to continue the
real canary and opens a new OpenSpec change. Do not start V13 or decoder work
before that acquisition-planning boundary.
2026-08-14 supersession: the user explicitly changed this successor decision
to V13 retrospective diagnostics planning first; the V12 fresh-canary identity
boundary itself remains unchanged.

Claim boundary remains strict: no finite decoder correction, FER,
qualification, or promotion was established.

---

## Previous Task — Nonbinary V11 spatially coupled DE gate: PLAN FROZEN (2026-08-06)

The new planning change is
`openspec/changes/formal-nonbinary-ldpc-v11-sc-de-gate/`. Literature review,
equal-rate control, reference-reproduction gates, three frozen coupling
geometries, resource limits, acceptance IDs, and the finite-length successor
boundary are documented. This turn authorizes documentation only: V11-P04
independent freeze review is next, and no implementation or scientific
execution is authorized yet.

Detailed plan: `docs/nonbinary-ldpc-v11-sc-de-plan.md`.

Next step: perform an independent read-only review of V11-A01..V11-A16. If
accepted, implement only the QSC SMP reference and full-vector coupled MC-DE
engineering/reference phase. Do not build a finite code or decoder under V11.

---

## Previous Task — Nonbinary V10 DE-PEG-FFT-QSPA: failed_ensemble (2026-08-06)

The active OpenSpec change is
`openspec/changes/formal-nonbinary-ldpc-v10-de-peg-fftqspa/`. V10 is
TERMINATED with final state **failed_ensemble**: the V10A GF(1024)
four-search density-evolution ensemble gate failed (hard stop V10-S02).
V10-30 (PEG), V10-40 (FFT-QSPA), V10-50 (canary), and V10-60 (development)
are all HALTED. There is no "closest to gate", no rerun, and no tuning.
The successor is a brand-new V11 NB-SC-LDPC OpenSpec change (fresh
everything), pending user decision to start it.

Gate results:
- V10-0 q=4 reference-recovery gate: PASS (conservative 0.06414,
  |δ| = 0.00486 ≤ 0.012; main-thread accepted 2026-08-05).
- S1 (p=.20, f=1.15): conservative 0.2153 < 0.22 → FAIL.
- S2 (p=.20, f=1.08): conservative 0.1984 < 0.215 → FAIL.
- S3 (p=.30, f=1.15): conservative 0.3166 < 0.32 → FAIL.
- S4 (p=.30, f=1.08): no eligible candidate → FAIL.

Key evidence (all under the change's `evidence/`):
- `v10_gate_decision.json` — final gate decision (schema
  `v10_gate_decision_v1`, `final_state=failed_ensemble`)
- `v10a_execute_results.json` — official V10A execute results
- `v10a_replay_evidence.json` — replay evidence (first attempt interrupted
  PID 21032; `replay_attempt2/` completed 04:36–07:07Z; 129-file direct
  byte comparison PASS, scientific files byte-identical, provenance-only
  normalization diffs)
- `v10a_gate_decision.json` — per-search gate decisions
- `v10_t3_regression.json` — git baseline PASS, frozen directories zero
  change
- `v10_protocol_amendment_no_hash_v1.json` — 2026-08-06 no-hash amendment

2026-08-06 protocol amendment (main-thread): defensive SHA-256/checksum/
integrity-manifest mechanisms (plan-bound digest, manifest self/source
hash, per-file compare sha256) removed per AGENTS.md §5.7; replacements
are git baseline checks, direct byte comparison, structured field
validation, and semantic recomputation. `v10_seed` is retained as a
deterministic RNG derivation primitive (DE population initialization and
mutation RNG streams depend on it; completed results depend on its byte
reproduction).

Close-out (2026-08-06): S4 delta correction recorded in
`evidence/v10_s4_delta_correction.json` (correct semantics null; evidence
untouched, script fixed); independent reviewer-go final review ACCEPT
(`evidence/v10_independent_review_acceptance.json`, 89 tests pass).

Archived (2026-08-06): moved to
`openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
(archive-move commit `921d0020f5fea9bc4452c17453365e2a1a7683f4`, local, not
pushed; delta specs not merged).

Next step: the user decides whether to start the new V11 NB-SC-LDPC
change. Nothing further is authorized under V10.

---

## Previous Task — Nonbinary V9A GF(1024) Long-Block IR STOP (2026-08-04)

The active OpenSpec change is
`openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/`. V9A ensemble
optimization executed once (pid 5084, 3968.5 s, peak RSS 428.3 MiB) and was
strict-replayed once (pid 29340, 4838.5 s). All four frozen searches recorded
zero eligible candidates; every gate FAILS. The change is frozen STOP before
any finite codebook. V9B/V9C are unreachable.

Key evidence:
- `evidence/v9a_plan_v2.json` — frozen v2 budget protocol
- `evidence/v9a_execute_results.json` — official execute results (restored from
  `workspace/v9a_04c9e7d25d7145659685415084d6fac7/v2_execute/` after the replay
  overwrote the shared evidence path)
- `evidence/v9a_replay_evidence.json` — replay confirmation (scientific files
  byte-identical; run_meta differs only in provenance)
- `evidence/v9a_gate_decision.json` — STOP decision
- `evidence/v9a_interrupted_trial_freeze.json` — v1-protocol interrupted trial
- `evidence/v9a_interrupted_v2_attempt_freeze.json` — v2-protocol attempt B
  interruption freeze

Close-out complete (2026-08-04): independent reviewer-go ACCEPT, SHA256
verification (9/11 byte-identical; 2 provenance-only diffs), acceptance
record `evidence/v9a_independent_review_acceptance.json`.

Archived (2026-08-05):
`openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/`.
Delta spec NOT synced to main specs (per user choice — unattained V9B/V9C
requirements must not become canonical spec). No codebook, decoder, canary,
development, qualification, real/N4 data, promotion, or formal comparison was
produced or is authorized under this change.

---

## Current Task (historical)

The active implementation change is
`openspec/changes/implement-formal-nonbinary-ldpc/`. Its N0 deterministic
GF(2^m) backend/preflight, N1 structural codebook, and N2 bounded FFT-QSPA
feasibility/accounting slices are complete.

## Scope

- Keep agent rules centralized in `AGENTS.md`
- Keep durable decisions in `docs/decision-log.md`
- Keep reusable failures and fixes in `docs/troubleshooting.md`
- Use `openspec/` for any substantial change
- Use `docs/openspec-phase0-reconciliation-20260725.md` as the current
  evidence/archival matrix for the five historical changes that remain active.
- Use the archived final selection record at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/` and its
  merged canonical spec before interpreting the bounded result.
- Use `openspec/changes/implement-formal-cascade-and-ldpc/` before changing
  comparison behavior: it upgrades only formal Cascade/LDPC candidates, not
  Polar or a three-method ranking.

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked
- If a request changes behavior, architecture, prompt rules, tool semantics, or workflow rules, create/update an OpenSpec change first

## Current Status

- `final-ir-method-selection` is archived; its merged canonical spec is
  `openspec/specs/final-ir-method-selection/spec.md`.
- The five historical IR changes have implementation/report artifacts, but all
  remain active because their Phase-0 evidence gaps are unresolved. See the
  reconciliation matrix for change-specific blockers.
- Cascade-lite remains the preferred executable non-Polar candidate;
  Layered LDPC remains a control baseline; qLDPC remains reference-only.
- Historical Polar imports are not frame-identical confirmation evidence.
- Phase 2 is locked at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`:
  d=1024, frame length 64, dataset raw SER [0.20, 0.30), with 60 tuning and
  60 confirmation frames from group-disjoint dataset IDs. Source and split
  hashes verify through `lock_final_ir_data --verify`.
- The original Phase-3 files in `20260725_v1/` are excluded from every
  decision; `invalid_run_notice.json` records the non-reviewed tuning grid.
  The Phase-2 lock files in that directory remain authoritative and read-only.
- The authoritative Phase-3 evidence is additive `20260725_v2/`, which uses
  the v1 lock manifest and exact same frames. It froze Cascade `[12,6,24,13]`,
  4 passes, seeded-random gray and LDPC parity 1.0, 50 iterations,
  bsc-estimated/uniform gray before confirmation. Confirmation retained all
  60 attempts per candidate: Cascade 60 verified successes; LDPC 59.
- Phase 4 audit is authoritative at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`; v3 is superseded by its additive notice after a generic decision-branch repair.
  It verifies the 60 identical locked confirmation keys, frozen corrected-grid configurations, retained statuses and aggregate denominators, and recorded lock hashes. The exact two-sided paired p-value is 1.0 for the single Cascade-only success, so the required decision is `no_decision`, not a winner. Leakage remains method-specific and unranked. The non-numerical Route A field gate fails because the comparison schema lacks the documented universal-hash proof-interface fields.

## Next Step

Phase 5 code/doc hardening is complete: the data-lock selection unit test is
file-free, the authoritative lock and v4 audit have read-only verification
commands, and the Phase-3 runner requires a new output directory and records
its immutable pre-run plan before tuning. `python -m py_compile` passed for
the five new modules; focused unittest passed 7/7; and safe comparison pytest
passed 22/22 with `test_evidence_package.py` excluded because it still uses a
fixed tracked path. The external basetemp tore down normally in this pass.

The final completion audit and archive are complete for
`final-ir-method-selection`. Do not infer a winner: the authoritative v4 audit
remains `no_decision` at p=1 with a failing non-numerical Route A gate. Keep
the five historical IR changes active until their own written evidence gaps are
closed through separate work.

## Next Step

Formal shared-core Phases 1--2 are implemented in
`comparison_bench/src/comparison_bench/formal_ir/`: six-artifact/status
validation, pinned-LDPC fail-closed preflight, 64-pair provenance validation,
locked-seed Toeplitz verification, and canonical secrecy-checked transcripts.
`test_formal_verification.py` and `test_cascade_formal.py` passed 11/11;
no qualification outputs were created. Phase 3 now provides additive,
protocol-faithful `cascade_formal_v1` with fixed passes, cached look-back,
resource caps, locked Toeplitz verification, and secrecy-checked public
events. Next implement codebook-backed `ldpc_formal_v1`, then independent
synthetic and locked real-frame qualification. Existing lite results stay lite;
Polar and formal three-method comparison require a later change.

The reviewed OpenSpec now freezes the exact Toeplitz convention and locked
per-frame seeds; Cascade FIFO/re-entry state machine and caps; 64-symbol,
four-rate deterministic LDPC codebooks and pinned `ldpc==2.4.1` parameters;
calibration-only `p_hat`; six-artifact/status/provenance contracts; and exact
synthetic plus fresh `bw100`/`bw120` real promotion gates. The shared Phase
1--2 task items are checked; algorithm and qualification tasks remain open. A
method may finish as `non_promoted`, but lite cannot
substitute for it in a future formal Polar comparison.

Phase 4 is complete. `ldpc_formal_v1` now has deterministic manifest-backed
four-rate codebooks, sacrificed-calibration-only frozen `p_hat`/rate selection,
MSB-first syndrome reconciliation, the exact pinned serial BpOsd configuration,
syndrome consistency, locked Toeplitz verification, transcript-safe disclosure
accounting, and fail-closed status handling without fallback. The revised
constructor probe succeeds on installed `ldpc==2.4.1`; a real-backend
single-error frame completed as `verified_success`. Calibration provenance now
hashes the source plus dataset, ordered unique sacrificed frame keys, mapping,
and dimension; confirmation recomputes that hash and validates every per-plane
count, `p_hat`, and selected rate. The public runner exposes no decoder or
preflight test seam. Focused formal tests passed 18/18 and the safe comparison
suite excluding fixed-path `test_evidence_package.py` passed 40/40 with the
TemporaryDirectory-backed 40-codebook test enabled outside the Windows sandbox.
No qualification output had been generated at Phase-4 completion.

Formal synthetic v1 remains excluded as a partial pre-execution run. Synthetic
v2 is now also non-authoritative diagnostics: its declared Alice seed
`2026072501` and frame-order seed `2026072531` were unused, while undeclared
Alice seeds `2026072502..2505` generated its batches. Its observed Cascade/LDPC
counts therefore confer no promotion. Phase 5 checkboxes are reopened.

Formal synthetic Phase 5 is complete at additive
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
The immutable v3 package verified read-only with 128 outcomes: Cascade passed
both strata (32/32 at p=.01 and 32/32 at p=.02) and is synthetically
promoted; LDPC recorded 29/32 and 14/32 respectively and is synthetically
`non_promoted`. All 21 retained failures were `verify_failed`; there were no
unclassified/internal/provenance/accounting failures. This does not authorize
retuning, lite substitution, real qualification, Polar adaptation, or a
three-method ranking. Phase 6 remains the next gated work.

## Formal IR Phase 6--7 Verified Status

Phase 6 is complete for the only eligible real method. The invalid real v1
lock received only additive `invalid_lock_notice.json` (SHA256
`9f9d72f6c1e39467f08b86a514851b78a8aaf6a8ef2fb1f869b22f60e980d556`);
its original plan
`3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`
and lock
`aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
remain unchanged, with zero formal method calls.

The unique real v2 Cascade package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`
contains exactly seven top-level artifacts and passes its strict read-only
verifier. Its SHA256 chain is: plan
`ef0c496d4679c8a790fa6715fca010c65bbe80dbcc9fb1a640139750e8f87161`,
lock `fea6d1e9912415c37f78393ef7d5e5e9bae156531bc9e6bd9a07936c41a09348`,
outcomes `d3ef26555e19fa58d74e40ccc9dc253e27db058a1b79720e77ab265f652c01f0`,
transcript `f95478b529f13871846400395d97b9d8a4f1948ddd30859a16dd7f66074a34c8`,
codebook manifest
`e8fbbd2ca195c8aa6d4a2ca8c821c2f8bb0eb73e6830ac85fff4558ef329738c`,
run manifest
`42d18066cc13740fd4367430b0319020ec4b943e5c01bf43f4df0759257ce172`,
and report
`750aaebf4919aa9a66383e6e4bf2d441efd718324ebca564157e6607d2b21e1b`.
The exact preflight passed 29 tests with exit 0 and output hash
`8760383422fb96ce6b8d644333e52064287e394f2827f57459bc110ded0a7a7c`.
All 60 requested frames were attempted, denominator-included, independently
verified, and `verified_success`; the verification union bound is
`3.2526065174565133e-18`, with zero unclassified/internal/provenance/accounting
failures. `cascade_formal_v1` is therefore promoted only for the locked real
domain `d=1024`, 64 symbols, bw120, frame SER `[0.20,0.30)`.

Synthetic v3 still promotes Cascade at 32/32 in both strata. LDPC remains
synthetically non-promoted at 29/32 and 14/32 and was not run on real data.
Phase 7 read-only verification passed for synthetic v3 and real v2; the safe
non-formal regression passed 22/22 in 0.66 s; `git diff --check` exited 0
apart from known ACL/LF warnings; frozen `src/`, `experiments/`, `tools/`, and
`results/` diffs were empty; and the independent audit result was PASS.

The active change is technically ready for archive review but is not archived.
Memory triage and the actual archive action remain pending.

## Next Step

Create a new LDPC-improvement OpenSpec change. LDPC must earn fresh synthetic
and real promotion before any frame-identical Polar/Cascade/LDPC comparison is
created. Do not substitute a lite method or tune on confirmation data.

## Archive Complete

`implement-formal-cascade-and-ldpc` is archived at
`openspec/changes/archive/2026-07-25-implement-formal-cascade-and-ldpc/`.
Its canonical merged specification is
`openspec/specs/formal-ir-methods/spec.md`. Final method state:
`cascade_formal_v1` is promoted by synthetic v3 and the bounded real v2
qualification; `ldpc_formal_v1` is synthetically `non_promoted` and had no
real run.

The next change must be a new LDPC-improvement OpenSpec change; it has not yet
been created. Do not begin a direct frame-identical Polar/Cascade/LDPC
comparison until LDPC earns fresh synthetic and real promotion.

## Nonbinary LDPC N0 Status (2026-07-26)

`nbldpc_formal_v1` now has a deterministic internal polynomial-basis GF(2^m)
contract for q=2 through q=1024, canonical field IDs, strict integer symbol
validation, and a read-only fail-closed preflight. Unsupported q returns
`unsupported_domain`; an expected field-ID mismatch returns
`backend_unavailable`; no external backend, decoder, or lower-q fallback is
used. Focused nonbinary plus existing qLDPC-reference tests passed 15/15, and
the selected formal/qLDPC regression passed 22/22.

N1 now adds one deterministic n=64, 32-row mother matrix with exact 16/24/32
prefix codebooks, pinned GF(q) rank, canonical bytes, golden codebook/manifest
hashes, and reconstruction-based fail-closed verification. Focused tests pass
22/22 and the selected formal/nonbinary/qLDPC regression passes 29/29.

N2 now adds a truth-isolated full-message FFT-QSPA decoder, q-ary symmetric
priors, GF(q) coset syndrome semantics, bounded q=1024 execution, MSB-first
mapping, locked Toeplitz wrapper, and exact syndrome/tag/public-control
accounting. N0-N2 plus qLDPC tests pass 35/35; selected formal regressions pass
17 with 2 skipped.

This is bounded engineering feasibility only. It proves no general
correction, FER/performance, calibration, synthetic/real qualification,
promotion, output, production readiness, or comparison eligibility. The next
task is planner-owned N3 pre-registration: freeze development/confirmation
data and separation, claim domain, one global policy, metrics/gates, resource
and stop rules, additive artifacts, invalid-run handling, and a strict
read-only verifier. Do not generate data or execute qualification yet.

# Nonbinary N3 outcome (2026-07-26)

`nbldpc_formal_v1` N3 is complete as an immutable **non-promoted** synthetic
package. N4 real-data work, confirmation tuning, and reruns are forbidden.
Official strict verification is failed/unverifiable because whole-worktree git
status drifted after execution; diagnostic replay is not a substitute.

## Nonbinary v2 Final Outcome (2026-07-26)

The successor package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
was planned once, executed once, and strictly replay-verified. The verifier
returned `verified=True`, `run_status=non_promoted_development`,
`promoted=False`.

The selected tempered+damped QC48 policy (margin 8, max_iter 10, checks 32/40)
achieved only 0/24 at p=.20 and 5/24 at p=.30 versus the frozen 22/24
development-readiness floor. Confirmation was therefore not generated or
executed. Stop: no rerun, confirmation tuning, N4, sidecar access, `.ttbin`
processing, FER claim, or real-data claim.

## Nonbinary v3 Final Outcome (2026-07-30)

The covered-layered successor is complete at
`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic/`.
Its plan, execute, and strict read-only replay each ran exactly once. The
selected layered-l075 margin-8 policy passed development readiness at 23/24
for p=.20 and 24/24 for p=.30. Sealed confirmation achieved 32/32 and 30/32,
with zero prohibited failures, but the frozen gate required 31/32 in both
strata. The verifier returned `verified=True`, `run_status=completed`,
`promoted=False`.

This task ends at immutable synthetic non-promotion. Do not rerun or tune it.
N4, sidecar access, and real `.ttbin` processing remain forbidden until a
successor earns fresh synthetic promotion and a new OpenSpec change is
approved.

## Nonbinary v4 IR Final Outcome (2026-07-31)

`formal-nonbinary-ldpc-v4-incremental-redundancy` completed its one authorized
synthetic run at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
The sole strict replay returned `verified=True`, `run_status=completed`, and
`promoted=False`.

Development selected warm incremental redundancy at 64/64 for p=.20 and 63/64
for p=.30. Confirmation was 128/128 and 120/128, respectively, with eight
retained p=.30 `decode_failed` rows and zero prohibited failures. The terminal
gate is therefore A3. Do not rerun, tune, build N4, access sidecars, or process
real `.ttbin`.

The next permissible work is planner-only exploration of a fresh synthetic
successor. It must use new roots and freeze its code/rate/decoder change before
new development data; the current confirmation rows may diagnose the route but
must not be used as tuning data.

## NBLDPC v5 Routes A and B Final Outcomes (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Routes A and B, each
planned once and executed once (512 outcomes each, `run_status=completed`,
readiness true, `promoted=False`).

- Route A `20260731_v5a_nbldpc_multistage_synthetic`: p=.20 128/128, p=.30
  127/128 (one tail miss).
- Route B `20260731_v5b_nbldpc_mother_synthetic`: NBLDPC5B mother with zero
  w2/w3 syndrome collisions; p=.20 128/128, p=.30 127/128 (one tail miss).
- Both strict read-only replay attempts were blocked by external-session git
  HEAD drift after plan creation (`71bda20d`→`3a5d96a` for A,
  `3a5d96a`→`4dd6b7e` for B); source/CLI/contract hashes all still match. See
  the two 2026-08-01 decision-log entries.

Both packages are immutable non-promotion evidence; no rerun or confirmation
tuning is authorized. Route C was next (codebook identity fixed to NBLDPC5B,
roots 202607800000-202607830000, run ID
`20260731_v5c_nbldpc_decoder_synthetic`) and has completed; see the Route C
section below.

## NBLDPC v5 Route C Final Outcome (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route C once:
`20260731_v5c_nbldpc_decoder_synthetic` (NBLDPC5B codebook identity, dual
policies `nbldpc_v5c_sched` / `nbldpc_v5c_ems`, roots
202607800000-202607830000), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained tail miss) —
  the same p=.30 tail pattern as Routes A and B.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` was unchanged by the replay.

The Route C package is immutable non-promotion evidence; no rerun or
confirmation tuning is authorized. Route D is next
(`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-202607870000,
list stage L=2 + one ADMM run per task 1.6; implementation starts at
task 7.1).

## NBLDPC v5 Route D Final Outcome (2026-08-02)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route D once:
`20260731_v5d_nbldpc_post_synthetic` (NBLDPC5B via v5c delegation, dual
policies `nbldpc_v5d_sched_post` / `nbldpc_v5d_ems_post`, list L=2 x top-8
+ ADMM rho=1.0 post-processing), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained
  confirmation-frame `decode_failed`) — the same p=.30 tail pattern as
  Routes A, B, C.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` unchanged.
- Implementation corrections recorded: x-update prior sign and per-bit
  parity-relaxation z-projection (q=4 brute-force verified; see
  decision-log 2026-08-02 and module docstring).

With all four routes non-promoted, the v5 multistage change **terminates**
per task 7.4 with four immutable non-promoted packages
(20260731_v5a/v5b/v5c/v5d_nbldpc_*_synthetic). No rerun, tuning, N4,
sidecar, `.ttbin`, real-data, or comparison claim is authorized. A
successor must be a new OpenSpec change with fresh development and
confirmation data.

## Nonbinary v6 Long-Block Outcome (2026-08-02)

Change `formal-nonbinary-ldpc-v6-long-block` built the GF(1024) n=1024
degree-2 PEG engineering candidate (codebooks (1024,320)/(1024,480), layered
FFT-QSPA 50 iterations, lambda .75), accepted engineering (T0 16/T1 38/T2 6/
T3 51), then ran a sacrificed 4+4 canary once + strict replay once: 0/4 + 0/4
verified success, all 8 `decode_failed` at max_iter=50. Gate fires:
long-block baseline stopped, n=4096 NOT taken, successor = multiplicative
repetition (2,3) mother code. Evidence under
`openspec/changes/formal-nonbinary-ldpc-v6-long-block/evidence/`; canary
package at `workspace/nbldpc_v6_canary_b01c42a5dee14ed0913e78d60944cc38/canary_plan`.

## Nonbinary v7 Successor Ladder (2026-08-02)

Change `formal-nonbinary-ldpc-v7-successor-ladder` runs the pre-registered
route ladder R1A -> R1B -> R2 -> R3 (canary 4+4 -> 0/4 freeze and advance;
else 16+16 -> readiness gate >=15/16, <=8.75 bits/symbol, median <=120 s/frame).

- **R1A** `(2,3)` mother n=256 m=170: engineering accepted; canary 0/4 + 0/4
  -> `failed_canary`, frozen.
- **R1B** one multiplicative repetition (rate 1/6): engineering accepted;
  canary p=.20 3/4, p=.30 0/4 -> `failed_canary` (p=.30 tail), frozen.
- **R2** QSC density-evolution ensemble (n=1024, 321/458 checks, DE validated
  against published BSC/BEC vectors): engineering accepted; canary 0/4 + 0/4
  -> `failed_canary`, frozen.
- **R3** GF(32)xGF(32) multilevel (EMS nm=32): engineering accepted (T0 19/
  T1 105/T2 33/T3 179, 10/10 independent review PASS); canary 0/4 + 0/4 ->
  `failed_canary` (executed once 668.8 s, strict-replayed once 663.4 s, 8/8
  decode_failed at max_iter=100, verification never invoked), frozen.

**LADDER EXHAUSTED (2026-08-04)**: all four routes R1A/R1B/R2/R3 ended
`failed_canary`; no route reached development-ready. Closeout report frozen at
`evidence/v7_ladder_report.md` (V7-40 complete): first-ready route NONE,
`ladder_exhausted` TRUE, every failed artifact retained, no official
`formal_ir_methods` v7 output root, no rerun/tuning/confirmation/real data,
disclosure ceilings and forbidden-status scans clean across all routes. No
fourth route is invented.

All v7 packages are immutable under `workspace/nbldpc_v7_*`; no official
`formal_ir_methods` v7 output exists; evidence under
`openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/`;
decision-log entries 2026-08-02 for R1A/R1B/R2 non-promotion and 2026-08-04
for R3 non-promotion + ladder_exhausted + closeout.

## Next Step

The v7 successor ladder is closed (`ladder_exhausted`). Any successor must be
a **NEW OpenSpec change** with fresh development and confirmation data, new
roots, and its code/rate/decoder change frozen before new development data;
current canary/confirmation rows are not tuning data. Remaining v7 closeout:
V7-41 independent acceptance and project-memory triage, V7-42 finalize
without inventing a fourth route. Qualification/promotion/comparison claims
remain unauthorized.

## Nonbinary V8 Reference Reproduction — V8-60 Audit-Correction Close-out (2026-08-04)

- Change: `formal-nonbinary-ldpc-v8-reference-reproduction`.
- Status: implemented, then corrected by V8-60 (non-tuning formula correction
  from an independent audit), corrective reference run executed once, and
  INDEPENDENTLY REVIEWED ACCEPTED (reviewer-go, read-only, 2026-08-04) at HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`. V8-A01..V8-A11 pass; V8-A12
  resolved pass by the V8-60 independent review (operator did not self-accept).
- Scope: additive only — 3 modules + 3 tests + 12 evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/`:
  error-domain contract (`nonbinary_v8_error_domain.py`), independent
  probability-domain oracle (`nonbinary_v8_reference.py`, GF2mField-only
  import boundary), and full-vector QSC MC-DE (`nonbinary_v8_mcde.py`); see
  decision-log 2026-08-04.
- V8-60 correction (not tuning): `concentrated_check_distribution` previously
  matched the two-point MEAN check degree (`w_lo = dc_hi - dc_mean`), which
  only approximates the edge-perspective rate condition
  `sum_j rho_j/j = (1-R)*sum_i lambda_i/i` (relative error ~1e-4); corrected
  to solve it exactly for adjacent check degrees `{floor(dc), ceil(dc)}` with
  `w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`,
  `target = (1-R)*integral_lambda`, `dc = 1/target` (integer `dc` degenerates
  to the regular degree); new helper `reconstructed_rate(lambda_edge, rho_edge)`;
  tests assert `|reconstructed_rate - rate| <= 1e-12` (5 configs). Citation
  first author corrected "Rasmus T. Müller" -> "Ronny Müller"
  (arXiv:2307.02225v2 author list). Invalid tolerance arithmetic
  `0.005+0.003+0.0025=0.015` replaced by 0.0005 + 0.00125 + 0.005 + 0.005 =
  0.01175 <= 0.012; frozen tolerance 0.012.
- Corrective reference run (exactly once, frozen before run): q=4, R=0.75,
  Muller et al. 2024 Table 1 row 0.75 (DET published 0.069), concentrated rho
  {24: 0.6623423944, 25: 0.3376576056} (dc_mean 24.3285893 unchanged),
  n_samples 100000, max_iter 150 (the paper's own MC-DE budget), seed
  2026080418, p in [0.01,0.12] step 0.0025, entropy < 0.01 base-q for 20
  consecutive iterations: threshold_proxy 0.062421875, delta 0.006578125 <=
  0.012 -> PASS; full trace in `evidence/v8_reproduction_trace_corrected.json`.
  No rerun, no tuning.
- History preserved: `evidence/v8_reproduction_trace.json` byte-identical
  (SHA256 `dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3`)
  + `v8_reproduction_trace_precorrection_annotation.json`;
  `v8_engineering_acceptance.json` NOT rewritten (A12=blocked resolved by
  `v8_acceptance_closeout_addendum.json`); provenance/extract/audit/recommend
  files unchanged. q=4 golden re-recorded under corrected rho {4: 1/6, 5: 5/6}
  (recording, not tuning); old-R2 tamper modes still differ; q=8 golden
  byte-identical (regular {6:1.0}).
- Tiers (V8-60.8, no T3): compile exit 0; T0 17/0, T1 32/0, T2 4/0
  (reproduction-trace + source-manifest + no-production-runner +
  precorrection-preservation, all read-only); reviewer-go re-ran T1 32/0 and
  T2 4/0: identical.
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real/N4/comparison execution; frozen
  `src/`/`experiments/`/`tools/`/`results/` and all V1-V7 files unchanged
  (git status/diff empty); nothing staged.
- Boundary: V8 is engineering/reference-only; no FER, readiness, qualification,
  promotion, or comparison claim is made from V8.
- Next: nothing remains for V8 except the V8-60.11 memory-agent close-out
  (AGENT_PROJECT_MEMORY.md section 39 pending). V9 is a separate future OpenSpec
  change (paper-faithful syndrome reconciliation with the reproduced ensemble
  and blind puncturing/shortening, fresh roots); NOT implemented.

## Active: Nonbinary V9 GF(1024) Long-Block IR (2026-08-04)

- Change: `formal-nonbinary-ldpc-v9-gf1024-long-ir`.
- Next task: V9-00 freeze/audit, then V9A scalable full-vector GF(1024) MC-DE.
- Route is autonomously gated through V9B n=4096 and V9C n=16384/n=32768;
  first failed robust/canary/development gate freezes and stops without tuning.
- V9C authorizes bounded synthetic canary and 16+16 development only. No
  qualification, confirmation, real/N4, promotion, or formal comparison.
- Operator packet:
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/opencode-autonomous-packet.md`.
- Freeze-review corrections are incorporated: target .215/.32 gates; one V9A
  plan/execute/replay; 4/16/32 constituent provenance; `rank(H)=m`; n=32768
  canary 24h hard timeout and <=16h median; fixed-rate syndrome/tag only.
  Blind adaptation is prohibited in V9 and deferred to V10.
