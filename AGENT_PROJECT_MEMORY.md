# AGENT_PROJECT_MEMORY.md

> **Repository scope (2026-08-22)**: This memory serves the BINARY POLAR
> MAINLINE checkout (`HD-QKD_Polar_Release`, branch `polar-mainline`).
> Entries dated before 2026-08-22 largely record the FORMAL IR / NB-LDPC
> research line that belongs to the sibling repository
> `../HD-QKD_Polar_Comparison`; they are retained verbatim as crosstalk-era
> provenance and MUST NOT be treated as this checkout's active backlog.
> New entries should cover the Polar mainline only.

## 2026-08-26 METHODOLOGICAL WARNING — v3 ↔ v4(lossfix) same-grid deltas are NOT directly comparable

- **Do not cite** two-generation same-grid differences as "the cost of the
  rate-search fix". On high-dimensional grids — (4096,200), (2048,200),
  (1024,150) — the apparent PIE/SKR drop (v3 ≈ 6.79 vs v4fix ≈ 4.65)
  **confounds two independent factors**:
  1. **Data-lineage correction**: lossfix pools were rebuilt from original
     ttbin (`raw_ser` 0.07 → 0.24); old-pool bytes understated ser
     (contaminated shared sequence pool, see 2026-08-25 entry).
  2. **Rate-search conservatism**: frames300 + 26-step fine ladder +
     Wilson FER; deep rate tiers heavily downgraded / shifted to SCL.
- Through the single `Σk_best` lever these synthesize into an apparent gap
  of roughly **54% kept / 46% leak** contribution.
- **Isolation rule**: strategy-effect isolation requires grids whose data is
  bit-identical across generations — e.g. (64,200): PIE +0.47 ⇒ the PURE
  rate-search-strategy effect there is a **positive gain**, not a cost.
- IAB / beta_eff_empirical / secure series two-generation deltas are SER
  downstream mirrors of the same lineage shift — likewise not directly
  comparable across generations.
- Evidence: `openspec/changes/fix-candidate-loss-namespace/evidence/`
  (verified present 2026-08-26). The per-layer decomposition table from the
  attribution round exists only in chat history — **pending**: fold it into
  docs at change closeout (T5.x). [decision]

## 2026-08-26 档间 map_ser 差异机制诊断（lossfix 四档；同晚仅改衰减采集）

- 结构事实：全部错误 100% 为 ±1 邻 bin 穿越（near_neighbor_frac≡1.0），
  无随机散布错误。 [repo-observed]
- 假设鉴别：偶然符合占比被三重否决（错误方向相反 / peak_to_bg 随通量上升 /
  错误非均匀）；多对发射为次要因素（≤2.5%）；最近邻配对竞争方向对但量级不足
  （≤6~27%）。幸存主因＝**速率相关定时劣化家族**（死时/堆积/时间游走）：
  d64 同锚内控下通量 74k→688k 对应 ser 平滑单调上升；peak_sigma 随通量
  +36~43%；窄 bin 格呈阈值式单侧位移并饱和。 [decision]
- 未决混淆：归档 metrics 缺每档 singles 遥测，且 pairing_v2 自动延时重锚定
  （~100ps 粒度，used_delay_ps=peak_center_ps，见
  `src/workflow/export_joint_sequence_sidecar.py` L1094/L1163-1164，行号已核对）
  使「探测器物理」与「漂移×重锚定」两因素暂不可分。 [repo-observed]
- 可行动含义：①便宜判别实验＝禁用 auto_peak_delay、固定锚后四档重跑配对，
  若档间 ser 差收窄则说明重锚定策略参与制造差异（上游白捡收益）；
  ②PIE 恢复路径优先级修正——先评估上游定时/锚定优化（抬 IAB 上限），再评估
  解码器升级（自适应冻结序，抬 β）。 [decision]
- 证据：鉴别诊断表仅存于对话记录 —— 与上方 v3↔v4 条目的 T5.x 待办同类，
  建议 T5 收尾时一并补入 docs/troubleshooting 或 docs/。 [pending]

## 2026-08-26 fix-candidate-loss-namespace approved — Phases 0–3 PASS, Phase 4 rerun RUNNING; G3 criteria lesson

- OpenSpec change `fix-candidate-loss-namespace` **approved by user
  2026-08-25** and implemented through Phase 4. Decisions: Q1 = re-verify
  16dB shared 56 cells via full rebuild; Q2 = full grid, all 121 cells/tier;
  Q3 = quarantine-rename old shared pool to
  `real_sequences_quarantined_20260825` (**pending, T5.3, requires explicit
  authorization**); Q4 = `*_lossfix_v1` naming. [decision]
- Feasibility verified: all four tiers' raw ttbin (+`.1` shards) present and
  non-zero under `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\`
  (`evidence/G0_precheck_report.md`); materialization/gate tooling in-repo;
  extraction chain deterministic — same inputs reproduce byte-identically
  (pilot double-runs + G2 fingerprint reconciliation). [repo-observed]
- Affected-cell exact census supersedes event-record approximations:
  10∩16=56, 6∩16=56, 6∩10=40, three-way intersection 29, 6dB union **67**
  (event record ≈61 was approximate), cross-tier union **94**, 20dB shares 0.
  Artifacts: `evidence/affected_cells.csv` / `.summary.txt`. [repo-observed]
- Materialization complete: 10dB×121 + 6dB×121 + 16dB×121 (83 rebuilt +
  **38 backfilled byte-for-byte from old authoritative** with per-file sha256
  proof `backfill_from_old_authoritative_MANIFEST.csv`; 38∩affected(16dB)=0);
  MANIFEST.csv 325 rows incl. chan_ll_sha256. [repo-observed]
- Gates G0–G4 ALL PASS post-backfill: G2 = 1452 six-pair cross-tier array
  comparisons, 0 collisions; G3 = zero exact-equality + strict tier-mean
  ordering (0.24727 > 0.233595 > 0.198166 > 0.17006); G4 = 484 sidecar
  provenance fields pass (`evidence/phase3_gates_final_report.md`).
  [repo-observed]
- **Durable lesson — gate criteria took THREE revisions; binding pattern**:
  contamination gates must be only ① zero hash-level exact ser equality
  across tiers (the contamination signature) and ② strict tier-mean ser
  ordering. Per-cell monotonicity and map_sanity-style PASS are NOT
  achievable gates: historical per-cell FAIL rates of 94/89/89/77 per 121
  (6/10/16/20 dB) and 95/121 old-data violations under a monotonicity gate
  show such failures are properties of the physical map/grid, not of
  contamination. Arbitrary percentage thresholds fail in the face of
  evidence — a draft ≥2% inversion threshold sat BELOW the measured maximum
  inversion (2.2303%) of clean rebuilt data; never let such thresholds gate.
  Per-cell inversions are diagnostic-only with statistical background
  (small-sample σ, high-dim near-degenerate band). [decision]
- Parallelism directive (user, standing for these replays): use as much CPU
  as the host provides; frozen at workers=12 / metric-jobs=12 / shards=16 on
  a 20-logical-core host (basis: `evidence/phase4_launch_config.md`). Science
  params frozen frames300 / seed20260228 / tag-bits64 / shards16. [decision]
- lossfix namespace layout (do not conflate with pre-incident roots):
  candidates `results/authoritative_nsfix/e2e_{10dB,6dB,16dB}_fullgrid_pairing_v2_candidate_lossfix_v1/`
  (each with `sidecars/`, grid tables, `MANIFEST.csv`; 16dB additionally the
  backfill manifest); replay outputs
  `results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1/{loss_10dB,loss_6dB,loss_16dB}/`;
  20dB reference stays `results/authoritative/e2e_20dB_fullgrid_pairing_v2_candidate_t15/sidecars`
  (read-only). Old roots (`results/real_sequences/*`,
  `four_loss_parts_frames300`) remain read-only until T5.3 rename.
  [repo-observed]
- Frozen-baseline touch surface (all reviewed, default behavior unchanged):
  `export_sidecar_for_point` optional `pool_root` param +
  `run_e2e_pipeline.py --real-seq-pool-root` passthrough;
  `routeA_run_formal_cross_loss.py` new `--candidate-dirs` flag.
  [repo-observed]
- Phase 4 RUNNING since 2026-08-26T01:52:41+08:00: serial separated
  processes 10→6→16dB into the lossfix output root; monitoring via
  `workspace/fix-candidate-loss-namespace/p4_20260826_020352/` and
  `openspec/changes/fix-candidate-loss-namespace/evidence/phase4_launch_record.md`.
  Remaining: per-tier validator 121/121 checks → T5 closeout (T5.1/T5.2
  reports, T5.3 rename under explicit authorization, T5.4 memory/decision-log
  updates, T5.5 triage + `/finish-change`). 20dB reuses existing artifacts,
  no rerun. [repo-observed]

## 2026-08-25 v4 rerun TERMINATED — cross-loss shared sequence-pool defect (durable lesson)

- The rate-search-fix v4 four-loss full-chain rerun (PID 17828, launched
  2026-08-22, decision-log 2026-08-14 待办 #1) was **terminated by explicit
  user authorization** at 2026-08-25 20:58:53 (+08:00, `taskkill /F /T /PID
  17828`, tree verified gone, no residue). Forensics confirmed the candidate
  sidecar sources used a **loss-free namespace shared sequence pool**
  (`results/real_sequences/d{d}_bw{bw}/blk0`, materialized 2026-03-18, plus
  the since-deleted `workspace/override_points`): the same (d,bw) cell held
  byte-identical inputs across loss tiers ⇒ same-seed deterministic replay
  emitted bit-identical outputs per tier pair. [repo-observed, decision]
- Impact census: 10∩16dB=56 cells, 6∩16=56, 6∩10=40 byte-identical; **20dB
  clean** (independent t15 materialization, 0 sharing); provenance of 16dB's
  56 shared cells untraceable. Validity: within-20dB usable; within-16dB
  usable but its 56 shared cells barred from cross-loss comparison; any
  10/6dB cross-loss comparison invalid. [repo-observed]
- Disposition: all three produced tiers (267 files) preserved in place as
  forensic evidence, nothing overwritten or deleted; `loss_6dB/` retains an
  empty skeleton only. Full incident record:
  `results/paper_grade_v4_rate_search_fix/DATA_PROVENANCE_INCIDENT_20260825.md`;
  decision recorded in docs/decision-log.md 2026-08-25 entry. [repo-observed]
- **Durable lesson (binding on all future work)**: any future candidate
  materialization MUST (a) carry the loss namespace in its storage identity,
  and (b) pass a cross-tier byte-uniqueness check BEFORE downstream replay
  consumes it. Deterministic same-seed replay propagates identical inputs to
  identical outputs silently — a shared source pool is indistinguishable
  from genuine replication unless uniqueness is enforced at materialization
  time. [decision]
- Pending (new task scope, NOT started, requires user authorization +
  planner): rebuild per-point sequences from raw ttbin under per-loss
  namespaces (the old shared pool is deleted), then rerun affected tiers —
  at least 10dB and 6dB; whether the 16dB shared 56 cells get re-verified is
  undecided. Do not start without authorization. [decision-pending]

## 2026-08-22 Stage 0 full-chain rerun LAUNCHED (rate-search fix v4) — monitoring state

- Decision-log 2026-08-14 entry #1 待办 #1 (full-chain rerun with new rate-search
  params) was **authorized and actually restarted**: Stage 0 separated-process
  launch at 2026-08-22T22:00:19+08:00, main PID **17828** (6 python
  subprocesses; workers=2 + metric-jobs=4). Frozen command recorded verbatim in
  `results/paper_grade_v4_rate_search_fix/stage0_launch_record_20260822.txt`
  and `results/paper_grade_v4_rate_search_fix/launch_stage0.ps1`; logs
  `stage0_stdout_20260822.log` / `stage0_stderr_20260822.log` in the same dir.
  Output root: `results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300`
  (pre-launch it contained only the empty skeleton dirs noted last session —
  zero valid output). [repo-observed]
- Red lines while running: do NOT touch `paper_grade_v2/`, `paper_grade_v3/`,
  `authoritative/`, `supporting/`; no parameter changes post-launch; failed
  artifacts stay in place; NO security-correctness claims from this run until
  verified. [decision]
- Completion criteria for next-session verification: every loss directory under
  the output root must contain `round1a_summary.txt`,
  `actual_ir_block_table.csv`, `security_calibrated_master_table.csv`, and the
  validator must pass 121/121 with eps ≤ 1e-10. [decision]
- Next steps after completion: (1) key-sifting accounting recompute modeled on
  `results/diagnostics/leak_negative_layer_accounting_20260814/run_accounting.py`
  with inputs pointed at the v4 new root → (2) old-vs-new comparison report →
  (3) closeout writes to decision-log / project memory / CURRENT_TASK.md.
  [decision]
- Branch state update: pending pushes from the separation entry are DONE —
  `codex/feat/polar-diagnostics-occupancy` (e049415..1b7055c) and
  `project-restructure-20260427` (0e4f735..7d9a77f) pushed; `polar-mainline`
  == `origin/polar-mainline` at `6f33a26`. Earlier handover notes saying
  "pushes pending" are stale. [repo-observed]
- reviewer-go reviewed f21c94f boundary declarations: PASS, 4 non-blocking doc
  leftovers deferred as cleanup backlog (AGENTS.md §9 tree header still says
  `HD-QKD_Polar_Comparison/`; §0 blacklist does not cover surviving real-IR
  change dirs; L19–20 "provenance" sentence outdated;
  AGENT_HANDOFF.md is a dangling research-line reference). Any AGENTS.md edit
  requires an OpenSpec change first. [repo-observed]

## 2026-08-22 Repository separation executed (boundary plans 1-3)

- Roles fixed after the crosstalk incident: THIS checkout = binary Polar
  mainline on new long-lived branch **`polar-mainline`**; sibling
  `HD-QKD_Polar_Comparison` = formal IR / LDPC research mainline on `main`.
  Mirror scope declarations added as AGENTS.md §0 in BOTH checkouts (the
  sibling-side edit is left UNCOMMITTED there for user review). Never merge
  research `main` into `polar-mainline`. [decision]
- Commits on `polar-mainline`: `6a58adb` pre-separation checkpoint (on
  shared main), `f21c94f` boundary declarations (CURRENT_TASK.md rewritten
  to the Route A-complete Polar task book per 总体判断.txt; memory scope
  banner), `cd027ec` research-line removal (381 files, -73167 lines:
  `formal_ir/` package, `data_lock.py`, `final_selection_audit.py`, 48
  research CLIs, 89 research tests, 19 research OpenSpec change dirs,
  specs `final-ir-method-selection` + `formal-ir-methods`, nonbinary
  planning docs, `ldpc_v5_robustness` evidence), `5e1b82a` de-crosstalk
  test fix. [repo-observed]
- Post-separation verification: `compileall` exit 0; remaining comparison
  suite **39/39 passed**; smoke ok. Before the fix, 21 tests failed because
  `test_evidence_package.py` hardcoded
  `D:/Code/HD-QKD_Polar_Comparison/workspace/...` — literal crosstalk in
  code; now uses repo-local `workspace/pytest-evidence-test`. [repo-observed]
- Kept intentionally in this checkout: comparison_bench core bridge
  (io/methods/pipeline/sweep, lite methods, v3 parameter sweeps,
  build_long_frames, group-meeting and real-IR evidence CLIs with their
  tracked outputs under `outputs_comparison/`), plus OpenSpec changes
  `research-code-engineering-policy` and
  `standardize-agent-delivery-workflow-v1` (referenced by AGENTS.md).
  Remaining active changes: 7. [repo-observed]
- Pending: push `main` (`6a58adb`) and `polar-mainline`
  (`f21c94f`..`5e1b82a`) from an unrestricted terminal; elevated-terminal
  cleanup of ACL-locked pytest temp dirs (script in 2026-08-22 entry
  below). [decision]

## 2026-08-22 Release clone audit, V12 code location facts, session environment limits

- `D:\Code\HD-QKD_Polar_Release` (`main` = `origin/main` at `581cd05`, clean
  tree) is the release snapshot clone. Active development continues in the
  companion working repository `D:\Code\HD-QKD_Polar_Comparison`, which is on
  `main` with newer history (v31/v32-era OpenSpec changes). [repo-observed]
- V12 implementation exists ONLY in the companion repo (6 tracked files:
  `cli/run_formal_nonbinary_v12_real_micro.py`,
  `cli/verify_formal_nonbinary_v12_real_micro.py`,
  `formal_ir/nonbinary_v12_real_micro.py`,
  `formal_ir/nonbinary_v12_real_partition.py`,
  `tests/test_nonbinary_v12_real_micro.py`,
  `tests/test_nonbinary_v12_real_partition.py`). The Release clone tracks
  only the five V12 OpenSpec documents; grep for v12 code there returns zero
  hits. Authoritative output roots `outputs_comparison/formal_ir_methods/`
  and `final_ir_method_selection/` also exist only in the companion repo.
  Do not execute V12 steps (V12-T3 onward) in the Release clone.
  [repo-observed]
- Release-clone health checks 2026-08-22: `compileall` exit 0; safe smoke ok;
  scoped regression (test_nonbinary_v7_r1a_{codebook,long},
  test_nonbinary_v11_{smp_de,mcde,parallel}, test_data_lock,
  test_success_classifier, test_metrics, test_polar_existing_bridge,
  test_cascade_lite): 74 passed / 2 failed. Both failures are multiworker
  `test_nonbinary_v11_parallel.py` cases whose pool workers die on
  `PermissionError` creating TEMP dirs under the agent-session sandbox —
  environment artifact, consistent with prior full-suite passes; not code
  regressions. [repo-observed]
- Session-environment fact (reusable): in non-elevated agent sessions on this
  host, pytest temp directories become ACL-denied even for DACL reads
  (`icacls`/`takeown` fail without elevation). Verified untracked but
  undeletable from the session: 23 root `pytest-cache-files-*` dirs,
  root `tmpw7zl0atk/`, and `workspace/regression_scope_*.tmp`. They were
  left intact; removal needs an elevated terminal targeting ONLY these
  exact patterns. Also: session `git ls-remote/push/fetch` fail — schannel
  `SEC_E_NO_CREDENTIALS`, and the openssl fallback dies because Git-for-
  Windows helper processes cannot create signal pipes (Win32 error 5).
  Network git actions need an unrestricted terminal; pending there:
  delete fully merged `origin/formal-ir-accumulation` (`git rev-list
  --count main..origin/formal-ir-accumulation` = 0). [repo-observed]

## 2026-08-12 Formal IR accumulation commit, branch, and push

- Current working branch is `formal-ir-accumulation`, HEAD =
  `189d6c31aa445d0666bd78d32490041a8b14092c` ("feat(formal-ir): accumulate
  formal IR source, tests, CLIs, OpenSpec changes, and agent docs", 342 files,
  +60736/−109), pushed to origin
  (https://github.com/Placebo303/HD-QKD-Polar-pipeline.git) with upstream
  tracking set and remote hash identical. This commit was previously a
  detached-HEAD chain (2bb0d5b → 921d002 → 9666eec → 189d6c3) and is now
  mounted on the new branch; develop (b039dfb), main (2f496c0), and
  codex/feat/polar-diagnostics-occupancy (7085f0b) were not touched.
  [repo-observed]
- Commit contents: `comparison_bench/src/comparison_bench/formal_ir/` (63
  modules: cascade, ldpc, ldpc_v2-v5, codebook_*, nonbinary field/qspa/v2-v11,
  real_qualification.py, long_v3_*), 37 CLIs under `cli/`, `data_lock.py`,
  `final_selection_audit.py`, 79 test files, `requirements-formal-ir.txt`, 2
  comparison_bench docs, 4 root docs, OpenSpec 4 archived + 16 active changes +
  2 new merged spec dirs (`openspec/specs/final-ir-method-selection/`,
  `openspec/specs/formal-ir-methods/`). Frozen baseline `src/`, `experiments/`,
  `tools/`, `results/` zero change; the 111 tracked
  `outputs_comparison/` files zero change. [repo-observed]
- Deliberately NOT committed (untracked, per repo output/scratch policy): all
  `workspace/` scratch roots (145 tracked files exist under them), the
  `outputs_comparison/final_ir_method_selection/` and
  `outputs_comparison/formal_ir_methods/` output directories, and the root
  `新建卷 (D).lnk` Windows shortcut leftover. Do not commit or delete these
  unprompted. [repo-observed]

## 2026-08-11 Nonbinary LDPC V11 spatial-coupling DE gate — failed_coupling, successor guidance

- Change: `formal-nonbinary-ldpc-v11-sc-de-gate`. Final state
  **failed_coupling** (`evidence/decision/final_gate_decision.json`, schema
  `v11_final_gate_decision_v1`, decided 2026-08-11 by main thread, confirmed
  by reviewer-go V11-50.3 independent final acceptance, 16/16 A01-A16 PASS).
  All checks pass (rate/resource/replay/structured/semantic true; gates
  0/3); the provisional `failed_reference` in the execution-root summary was
  a checks-pending placeholder and is superseded by the final decision file.
  [repo-observed, decision]
- Scientific conclusion: the spatial-coupling hypothesis is REJECTED under
  the frozen V10 S1/S3 lambda distributions and the frozen G1 (w=1,L=32,W=8),
  G2 (w=2,L=32,W=16), G3 (w=2,L=32,W=32) geometries. Coupled conservative
  thresholds: S1 G1 .2100 / G2 .2025 / G3 .2019 (gate >= .22, 0/3); S3
  G1 .3125 / G2 .3000 / G3 .3000 (gate >= .32, 0/3); every paired
  conservative gain is negative (S1 -0.0075/-0.0144/-0.0156; S3
  -0.0137/-0.0256/-0.0206). No silent promotion, no "closest to gate", no
  matrix shrink. [repo-observed, decision]
- Successor guidance: after V10 failed_ensemble and V11 failed_coupling,
  design.md §8's simple alternative (stop and honestly report that the
  current uncoupled ensemble family misses the robust gates) is the current
  valid option; V11's spatial-coupling test changed nothing. Any
  finite-length/lifting, windowed FFT-QSPA, decoder, canary, real-data,
  qualification, or promotion work requires a NEW OpenSpec change with fresh
  roots and fresh development/confirmation data. [decision]
- Reference reproduction (V11-10.1/10.2): `formal_ir/nonbinary_v11_smp_de.py`
  reproduces the four published q=4/q=16 SMP-DE anchors (uncoupled + coupled,
  rate-1/2 (3,6), W=30) within frozen tol 0.002 — q=4 uncoupled 0.0890 vs
  0.0888, q=4 coupled 0.0942 vs 0.0945, q=16 uncoupled 0.1075 vs 0.1072,
  q=16 coupled 0.1288 vs 0.1287; coupled gain reproduced in both orders
  (q=4 +0.0057 vs published +0.0052; q=16 +0.0215 vs +0.0213). Sources:
  uncoupled SMP-DE Lázaro et al., arXiv:1906.02537 (Globecom 2019); coupled
  Ben Yacoub et al., AEIT 2019, DOI 10.23919/AEIT.2019.8893373. Trace:
  `evidence/reference/smp_de_trace.json`. [repo-observed]
- Resource facts (reusable for future GF(1024) DE work): full-vector coupled
  MC-DE per-iteration costs at N=2000 — G1 ~2.25 s, G2 ~4.97 s, G3 ~9.89 s,
  uncoupled control ~0.23 s (microbenchmark2.json). numba njit hot-kernel
  integration in `nonbinary_v11_mcde.py` gave 11.65x total speedup (predicted
  serial 777.33 h -> 66.72 h; per-cell 9.5-12.5x). 4-worker batch parallelism
  (#3) gives only 2.04x with per-worker efficiency 0.51 — batch efficiency
  does NOT extrapolate to the uniform 60-task matrix (load imbalance); the
  correct extrapolation is task-level LPT scheduling simulation
  (formal_plan.md §4): 17.1-19.7 h (central 18.9 h), under the 24 h limit.
  Actual execute: 60/60 runs once 2026-08-08, 15.83 h wall < 24 h, peak RSS
  2.82 GiB < 3 GiB. [repo-observed]
- Process precedents (reusable): budget amendments AMEND-2026-08-06-01
  (numba, limited to `nonbinary_v11_mcde.py` hot kernels, scientific
  parameters unchanged) and AMEND-2026-08-06-02 (4-worker parallel executor,
  RSS judged per single-run peak) — both user-approved, engineering-only,
  exactly-once re-measurement with prior evidence unchanged
  (`evidence/resource/microbenchmark{2,3}.json`). The long scientific execute
  ran as a detached background process with executor bookkeeping
  (`nonbinary_v11_execute.py`): progress.json + heartbeat.json (daemon
  thread) + `--resume` (terminal runs never re-run; failed evidence
  immutable) + `--status`. Lesson: batch-efficiency extrapolation
  overestimates for uniform task matrices; use LPT task-level simulation
  (formal_plan.md §4.4). [repo-observed, decision]
- Reusable assets under `comparison_bench/src/comparison_bench/formal_ir/`:
  `nonbinary_v11_smp_de.py` (SMP-DE reference, four reproduced anchors);
  `nonbinary_v11_mcde.py` (full-vector coupled MC-DE kernel, numba hot
  kernels, w=0 byte-identity to V9 uncoupled — covered by the 24 V11 MC-DE
  tests); `nonbinary_v11_execute.py` (threshold bisection + parallel executor
  + gate decision, reusable for any future DE gate work);
  `nonbinary_v11_parallel.py` (worker-pool executor);
  `nonbinary_v11_microbench.py`. [repo-observed]
- Frozen baseline: `src/`, `experiments/`, `tools/`, `results/` zero change;
  regression 87 passed; no new entry under
  `comparison_bench/outputs_comparison/formal_ir_methods/` (A14 PASS). All
  evidence under the change's `evidence/` (reference/, resource/, replay/,
  decision/, formal_plan.{json,md}, literature-review.md). Execute/replay
  roots: `workspace/nbldpc_v11_execute_002d51de/`,
  `workspace/nbldpc_v11_replay_8e63bf62/` (60/60 byte-identical science
  fields). docs/decision-log.md 2026-08-11 entry appended. [repo-observed]

## 2026-08-06 Nonbinary V10 failed_ensemble — final state, no-hash amendment, V11 successor

- Change: `formal-nonbinary-ldpc-v10-de-peg-fftqspa`. Final state
  **failed_ensemble** (`evidence/v10_gate_decision.json`, schema
  `v10_gate_decision_v1`): the V10A GF(1024) four-search density-evolution
  ensemble gate FAILED (hard stop V10-S02). V10-30 (PEG), V10-40 (FFT-QSPA),
  V10-50 (canary), and V10-60 (development) are all HALTED. There is no
  "closest to gate", no rerun, no tuning; no codebook/decoder/canary/
  development/qualification/real-data/promotion output exists under this
  change. [repo-observed]
- V10-0 q=4 reference-recovery gate PASS: conservative threshold 0.06414,
  |δ| = |0.06414 − 0.069| = 0.00486 ≤ 0.012; main-thread accepted
  2026-08-05. [repo-observed]
- V10A searches: S1 (p=.20, f=1.15) conservative 0.2153 < 0.22 FAIL; S2
  (p=.20, f=1.08) conservative 0.1984 < 0.215 FAIL; S3 (p=.30, f=1.15)
  conservative 0.3166 < 0.32 FAIL; S4 (p=.30, f=1.08) no eligible candidate
  FAIL. [repo-observed]
- Execute/replay: V10A executed once (~10470 s, peak RSS 335 MB < 3 GiB);
  first replay attempt interrupted (PID 21032 died, S1 only); per precedent
  `replay_attempt2/` completed 04:36–07:07Z (RSS 339 MB); direct byte
  comparison PASS across 129 files — scientific files byte-identical, only
  provenance normalization differs (plan_binding digest key, run_complete
  role/stage). [repo-observed]
- 2026-08-06 protocol amendment (main-thread): defensive SHA-256/checksum/
  integrity-manifest mechanisms (plan-bound digest, manifest self/source
  hash, per-file compare sha256) removed per AGENTS.md §5.7; replacements
  are git baseline checks, direct byte comparison, structured field
  validation, and semantic recomputation. `v10_seed` is RETAINED as a
  deterministic RNG derivation primitive — DE population initialization and
  mutation RNG streams depend on it and completed results depend on its
  byte reproduction. Amendment record:
  `evidence/v10_protocol_amendment_no_hash_v1.json`. [decision]
- Evidence (change `evidence/`): `v10a_execute_results.json`,
  `v10a_replay_evidence.json`, `v10a_gate_decision.json`,
  `v10_gate_decision.json`, `v10_t3_regression.json` (git baseline PASS,
  frozen directories zero change), `v10_protocol_amendment_no_hash_v1.json`.
  [repo-observed]
- Tests: full V10 suite 89 passed (common 23 / de 24 / gate 13 / peg 12 /
  fftqspa 17). [repo-observed]
- Frozen baseline: git HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`; `src/`, `experiments/`,
  `tools/`, `results/` zero change;
  `comparison_bench/outputs_comparison/formal_ir_methods/` has no new V10
  output; the 12 tracked modifications are pre-existing dirty-worktree
  entries of other workflows. [repo-observed]
- V10-30.DESIGN task (PEG no-hash design note) remains unchecked and is
  left for future V11 inheritance. [repo-observed]
- Close-out (2026-08-06): `evidence/v10_s4_delta_correction.json` (schema
  `v10_s4_delta_correction_v1`) records the S4 `delta` boolean-false /
  null-semantics correction (build_evidence short-circuit bug); evidence
  immutable, script expression fixed; reviewer-go final review ACCEPT
  (`evidence/v10_independent_review_acceptance.json`, schema
  `v10_independent_review_acceptance_v1`, 89 tests pass). [repo-observed]
- Successor: a brand-new V11 NB-SC-LDPC OpenSpec change (fresh everything:
  new change, new roots, new development/confirmation data); starting V11 is
  a user decision; nothing further is authorized under V10. [decision]
- Archived (2026-08-06): change directory moved to
  `openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
  (equivalent rename; delta specs not merged; local commit, not pushed).
  [repo-observed]

## 2026-08-06 Research Code Engineering Policy (AGENTS.md §5.7)

- Change `research-code-engineering-policy` implemented via the OpenSpec flow;
  policy now lives at AGENTS.md §5.7 (lines 80-110) and was reviewed ACCEPT by
  reviewer-go (no blocking items). Not yet archived; archive action pending
  user decision. [repo-observed]
- Core requirements: this repository is local research code, not a production
  service. Unless a task explicitly requires it, do not add checksums/integrity
  manifests, atomic/transactional writes, backup/rollback, file locking,
  elaborate schema validation, retry frameworks, security hardening,
  compatibility layers, custom caching, or exception handling that hides
  errors. Assume trusted local inputs, manual single-machine runs, rerunnable
  failures, and Git version control. Prioritize scientific/numerical
  correctness, explicit units/assumptions/parameters, readable calculations,
  reproducible seeds, validation against known limits, clear errors, and
  minimal dependencies/abstraction. Identify the concrete failure mode before
  adding any defensive mechanism; do not generalize one-off scripts into
  production frameworks. [repo-observed]
- Scope: only AGENTS.md and the openspec change directory; frozen baseline
  (src/, experiments/, tools/, results/) untouched. Pre-existing dirty files
  (AGENT_HANDOFF.md, CURRENT_TASK.md, AGENT_PROJECT_MEMORY.md,
  docs/decision-log.md, AGENTS.md §10.1) belong to earlier work, not this
  change. [repo-observed]

## 2026-08-04 V9A GF(1024) long-block ensemble gate STOP

- Change: `formal-nonbinary-ldpc-v9-gf1024-long-ir`.
- V9A executed once under the frozen v2 budget protocol (pid 5084, 3968.5 s,
  peak RSS 428.3 MiB) and strict-replayed once (pid 29340, 4838.5 s). Scientific
  outputs are deterministic and byte-identical between execute and replay; only
  `run_meta.json` differs in provenance fields.
- All four searches (S1 robust gate .22, S2 target gate .215, S3 robust gate
  .32, S4 target gate .32) recorded zero eligible candidates; every gate FAILS.
- Conservative threshold undefined for every gate; downstream tier selection is
  null for both strata.
- Decision: frozen STOP before any finite codebook. V9B/V9C unreachable. No
  codebook, decoder, canary, development, qualification, real/N4 data,
  promotion, or formal comparison is authorized under this change.
- Evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/`:
  `v9_00_freeze.json`, `v9a_plan_v2.json`, `v9a_execute_results.json`,
  `v9a_replay_evidence.json`, `v9a_gate_decision.json`,
  `v9a_interrupted_trial_freeze.json`, `v9a_interrupted_v2_attempt_freeze.json`,
  `v9a_independent_review_acceptance.json`.
- Process note: the replay script overwrote the shared
  `evidence/v9a_execute_results.json` path because it lacked a guard on that
  file; the orchestrator restored the original execute version from
  `workspace/v9a_04c9e7d25d7145659685415084d6fac7/v2_execute/`. Scientific
  impact: none (payload identical; only provenance fields changed); the missing
  guard is a process improvement for future changes, not a scientific defect.
- Close-out complete (2026-08-04): reviewer-go independent review verdict
  ACCEPT — all checklist items pass (matches OpenSpec spec, tests pass, no
  scope creep, decision log updated, V9B/V9C artifacts absent, scientific
  wording scoped), no blocking issues.
- Independent hash verification: 9/11 files byte-identical between execute and
  replay; 2 differ only in provenance (`evidence_v9a_execute_results.json`,
  `run_meta.json`). `S4.progress.jsonl` known hash verified:
  80ee59eb194c60a897ac43d4b09a5d1fd4ff76c8bd0a7394a155606e7cfc632a (this
  supersedes the `TO_BE_COMPUTED_BY_INDEPENDENT_REVIEWER` placeholder in
  `v9a_replay_evidence.json`).
- Change status: STOPPED at the V9A ensemble gate; will NOT advance to V9B/V9C.
  Close-out checklist V9A-C1 through V9A-C8 all checked. The change is
  archive-ready pending the archive action (`/opsx-archive`).
- Scientific boundary: the frozen 8-candidate V9A bounded enumeration failed
  its preregistered gates. This is NOT a general negation of GF(1024) LDPC and
  not a claim that complete ensemble optimization was exhausted; a successor
  requires a new OpenSpec change with fresh roots, a different ensemble family,
  and new development/confirmation data.
- Next: archive the change (OpenSpec archive action). No further work is
  authorized under this change.

## 2026-07-26 Nonbinary N3 evidence boundary

`nbldpc_formal_v1` completed its only frozen q=1024 synthetic N3 execution at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`.
Selected policy SHA `23a1b46300f1c841eed3ffc6f672840c7be17608260de6b09944cac74228983d`
was margin 7/scale 1.0/max_iter 10 with 32 checks in both strata. Confirmation
was non-promoted: p=.20 18/32 verified success and p=.30 5/32, both below the
31/32 gate; N4, reruns, and tuning are forbidden. The official strict verifier
failed only because post-execution whole-worktree git-status provenance drifted.
Source/CLI/contract hashes, commit, Python and NumPy matched; `_test_only=True`
diagnostic replay is not an official verifier pass. Preserve all seven artifacts.

## 1. Project Identity
- Project name: `HD-QKD_Polar_Comparison` [repo-observed]
- Research purpose: evaluate and compare information reconciliation (IR) methods for high-dimensional QKD data, while preserving the copied Polar pipeline as a frozen baseline and adding a separate comparison layer. [repo-observed]
- Main scientific/engineering objective: build a reproducible, non-invasive benchmark layer that can (a) read/import existing Polar results, (b) run executable comparison baselines on synthetic and real paired-symbol frame data, and (c) generate comparable CSV/Parquet/summary outputs without changing the original Polar workflow semantics. [repo-observed]
- Current maturity: mixed. The original Polar repository appears to be a mature replay/security/reporting codebase; `comparison_bench/` is an additive benchmark layer with working CLIs, tests, real-data imported Polar baseline, real-data/synthetic executable baselines, and v3 parameter-sweep/report outputs. [repo-observed]

## 2. Repository Structure Observed
- Top-level directories observed: `analysis/`, `comparison_bench/`, `docs/`, `experiments/`, `results/`, `src/`, `tools/`, `workspace/` [repo-observed]
- Top-level files observed: `README.md`, `requirements.txt`, `bootstrap_clone_clean.py`, `wsl-env.sh`, `LICENSE`, `.gitignore` [repo-observed]
- Original pipeline entrypoints:
  - `experiments/run_e2e_pipeline.py` [repo-observed]
  - `experiments/run_real_polar_max_pie.py` [repo-observed]
  - `experiments/run_golden_sweep_driver.py` [repo-observed]
  - `experiments/run_golden_sweep_four_datasets.py` [repo-observed]
- Original source areas:
  - `src/qkd_io/ttbin_pipeline.py` [repo-observed]
  - `src/workflow/coarse_grain_joint.py` [repo-observed]
  - `src/workflow/export_joint_sequence_sidecar.py` [repo-observed]
  - `src/workflow/llr_from_joint.py` [repo-observed]
  - `src/reconciliation/real_polar_sc_rescue.py` [repo-observed]
  - `src/reconciliation/cpp_scl_wrapper.py` [repo-observed]
  - `src/reconciliation/verification.py` [repo-observed]
  - `src/reconciliation/cpp_polar/` containing `.dll`, `.exe`, and C++ files [repo-observed]
- Original tooling area includes many audit/security/reporting scripts, for example:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
  - `tools/minrerun_run_frame_audit.py` [repo-observed]
  - `tools/minrerun_rebuild_security_master_20dB.py` [repo-observed]
  - `tools/routeA_run_formal_cross_loss.py` [repo-observed]
- Comparison layer structure:
  - `comparison_bench/README.md` [repo-observed]
  - `comparison_bench/requirements-comparison.txt` [repo-observed]
  - `comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
  - `comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
  - `comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
  - `comparison_bench/docs/architecture.md` [repo-observed]
  - `comparison_bench/docs/data_contract.md` [repo-observed]
  - `comparison_bench/docs/method_notes.md` [repo-observed]
  - `comparison_bench/src/comparison_bench/cli/` with:
    - `build_dataset.py` [repo-observed]
    - `run_benchmark.py` [repo-observed]
    - `compare_methods.py` [repo-observed]
    - `smoke_test.py` [repo-observed]
    - `run_cascade_param_sweep.py` [repo-observed]
    - `run_layered_ldpc_param_sweep.py` [repo-observed]
    - `run_qldpc_param_sweep.py` [repo-observed]
    - `run_ir_v3_master.py` [repo-observed]
    - `make_report_tables.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/io/` with:
    - `pairs_loader.py` [repo-observed]
    - `dataset_builder.py` [repo-observed]
    - `polar_existing_bridge.py` [repo-observed]
    - `table_store.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/methods/` with:
    - `cascade_lite.py` [repo-observed]
    - `layered_ldpc_lite.py` [repo-observed]
    - `qldpc_reference.py` [repo-observed]
    - `qary_ldpc.py` [repo-observed]
    - `polar_existing.py` [repo-observed]
    - `base.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/pipeline/` with:
    - `run_ir_benchmark.py` [repo-observed]
    - `merge_with_security.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/sweep/` with:
    - `runtime.py` [repo-observed]
    - `common.py` [repo-observed]
    - `rows.py` [repo-observed]
  - `comparison_bench/tests/` with six current test files [repo-observed]
- Historical context from prior work:
  - real-data imported Polar baseline was matched against a real result root under a legacy Windows data path. [memory-derived]
  - representative sidecar frame batches were built from real paired-symbol sidecar exports. [memory-derived]

## 3. Execution Environment
- Expected OS: Windows host environment is directly observed; WSL support is also explicitly provisioned via `wsl-env.sh`. [repo-observed]
- Expected Python/MATLAB/Octave/other runtime:
  - Python with `numpy`, `pandas`, `numba`, `tqdm` from root `requirements.txt` [repo-observed]
  - optional comparison dependencies: `pyyaml`, `pyarrow`, `pytest` from `comparison_bench/requirements-comparison.txt` [repo-observed]
  - compiled Polar binaries exist under `src/reconciliation/cpp_polar/` (`.dll`, `.exe`) [repo-observed]
  - MATLAB/Octave usage is [uncertain]; no current comparison harness file directly invokes them, but prior planning discussed possible external hooks. [memory-derived]
- Known environment constraints:
  - PowerShell profile loading emits execution-policy warnings in this environment. [memory-derived]
  - git commit/stage operations may fail due to `.git/index.lock` permission issues. [memory-derived]
  - git push over HTTPS to GitHub can fail with `SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)`; fixed on this host via `git config --global http.sslBackend schannel` (global host-level config, not repo content — other hosts may need the same fix). [memory-derived]
  - pytest cache/temp directories can trigger permission-denied warnings. [memory-derived]
  - some outputs may fall back from parquet to pickle if parquet support is missing. [repo-observed]
- WSL migration notes:
  - `wsl-env.sh` sets `PROJECT_DATA_ROOT`, `PROJECT_RESULTS_ROOT`, `TMPDIR`, and `PIP_CACHE_DIR` to POSIX-style defaults. [repo-observed]
  - For WSL work, prefer `/mnt/...` or project-relative POSIX paths, not Windows absolute paths. [repo-observed]
  - Historical Windows data/result paths should be treated as provenance only, not future execution defaults. [repo-observed]

## 4. Main Workflows

### Workflow: original Polar end-to-end pipeline
- entrypoint: `experiments/run_e2e_pipeline.py` [repo-observed]
- input: raw `.ttbin`-derived or paired-sequence materialization inputs [repo-observed]
- output: Polar evaluation artifacts under repository result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_e2e_pipeline.py` on raw data, because this is the core heavy baseline workflow and should not be rerun casually. [repo-observed]

### Workflow: original real Polar sweep / max PIE
- entrypoint: `experiments/run_real_polar_max_pie.py` [repo-observed]
- input: cached grid/source tables or materialized real-data intermediates [memory-derived]
- output: Polar result tables such as `polar_diag_summary.csv`, `polar_e2e_results.csv`, or related CSVs [memory-derived]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_real_polar_max_pie.py` against raw or large real-data inputs by default. [repo-observed]

### Workflow: replay / security / audit aggregation
- entrypoint:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
- input: prior Polar logs/results and audit/replay inputs [repo-observed]
- output: audit/shadow/master security summaries under result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - any `longrun_*` or `minrerun_*` scripts unless explicitly asked. [repo-observed]

### Workflow: real-data / synthetic comparison benchmark
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.build_dataset` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.compare_methods` [repo-observed]
- input:
  - paired symbol tables with normalized columns [repo-observed]
  - or sidecar directories containing `a_eff.npy`, `b_eff.npy`, and optional `sidecar_meta.json` [repo-observed]
  - benchmark YAML configs under `comparison_bench/configs/` [repo-observed]
- output:
  - `comparison_bench/outputs_comparison/ir_benchmark_results.csv` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_frame_results.parquet` [repo-observed]
  - `comparison_bench/outputs_comparison/run_manifest.json` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_method_summary.csv` [repo-observed]
- safe smoke command:
  - `python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
- do-not-run-by-default commands:
  - full real-data benchmark on all sidecars or all frames unless explicitly requested. [memory-derived]

### Workflow: v3 IR method parameter sweeps
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.run_cascade_param_sweep --config comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_layered_ldpc_param_sweep --config comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_qldpc_param_sweep --config comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input:
  - frame-batch parquet built under `comparison_bench/outputs_comparison/` [repo-observed]
  - sweep YAML configs [repo-observed]
- output:
  - `cascade_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `layered_ldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `qldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `run_errors_ir_v3.csv` [repo-observed]
  - `ir_v3_run_manifest.json` [repo-observed]
- safe smoke command:
  - there is no dedicated tiny smoke CLI; the lightest current path is to restrict configs before running. [uncertain]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- do-not-run-by-default commands:
  - v3 master runner or any full representative/all-point sweep in a fresh environment without confirming output policy first. [repo-observed]

### Workflow: v3 report table generation
- entrypoint: `python -m comparison_bench.src.comparison_bench.cli.make_report_tables --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input: existing v3 sweep CSV outputs [repo-observed]
- output: `comparison_bench/outputs_comparison/report_tables_v3/` CSV tables [repo-observed]
- safe smoke command: same as entrypoint, but only after sweep outputs already exist. [repo-observed]
- heavy command, if known: same as entrypoint; relatively lighter than the sweep commands. [repo-observed]
- do-not-run-by-default commands:
  - none obvious beyond not pointing it at incomplete/missing sweep outputs. [repo-observed]

## 5. Data and Result Policy
- raw data directories:
  - raw real data is external to the repo. Historical provenance includes a legacy Windows path under `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s` [memory-derived, legacy Windows path]
  - WSL default logical data root is `PROJECT_DATA_ROOT=/mnt/d/Data` from `wsl-env.sh`. [repo-observed]
- result/output directories:
  - original result area: `results/` [repo-observed]
  - comparison result area: `comparison_bench/outputs_comparison/` [repo-observed]
- checkpoint directories:
  - `comparison_bench/outputs_comparison/` contains run manifests and append-only sweep outputs, effectively acting as benchmark checkpoints. [repo-observed]
  - external run/checkpoint roots may exist outside the repo; treat them as [uncertain] unless explicitly mounted. [uncertain]
- files/directories agents must not overwrite:
  - `results/` and anything under it unless explicitly requested. [repo-observed]
  - `comparison_bench/outputs_comparison/` existing benchmark results, diagnostics, manifests, test fixtures, or summaries unless explicitly requested. [repo-observed]
  - raw data outside the repo. [repo-observed]
  - original Polar outputs imported by `polar_existing` bridge. [repo-observed]
- preferred new-output naming convention:
  - new comparison outputs should stay under `comparison_bench/outputs_comparison/` and use additive names consistent with current patterns such as `*_results.csv`, `*_frame_results.parquet`, `*_diagnostics.csv`, `*_manifest.json`, or nested subdirectories like `report_tables_v3/`. [repo-observed]

## 6. Schema and Interface Contract
- CSV columns that must not silently change:
  - normalized input columns: `frame_id`, `pair_idx`, `alice_symbol`, `bob_symbol` [repo-observed]
  - propagated metadata columns: `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `threshold_ps`, `effective_pairing_window_ps`, `processing_rule_version`, `pairing_path_tag` [repo-observed]
  - benchmark output columns include at least:
    - `dataset_id`, `data_mode`, `source_path`, `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `frame_len_symbols`, `frame_len_bits`, `method`, `method_variant`, `method_status`, `processing_rule_version`, `pairing_path_tag`, `threshold_ps`, `effective_pairing_window_ps`, `n_frames_total`, `n_frames_attempted`, `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify`, `accepted_frame_fraction`, `rejected_frame_fraction`, `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber`, `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit`, `beta_eff_empirical`, `runtime_s`, `throughput_input_bits_per_s`, `throughput_output_bits_per_s`, `notes`, `backend_status`, `error_message`, `real_ir_success`, `success_classification` [repo-observed]
  - frame-level output columns include at least:
    - `dataset_id`, `method`, `frame_idx`, `decode_success`, `verify_success`, `raw_frame_ser`, `raw_frame_ber`, `post_frame_ser`, `post_frame_ber`, `leak_bits_frame`, `iterations_used`, `runtime_ms` [repo-observed]
- JSON/YAML keys that must not silently change:
  - `datasets`, `methods`, `global` in benchmark YAMLs [repo-observed]
  - `output_dir`, `max_workers`, `frame_batch_path`, `polar_results_root`, `data_mode`, `frame_len_symbols`, `max_frames_per_dataset` in real-data benchmark YAML [repo-observed]
  - sweep config sections: `cascade`, `layered_ldpc`, `qldpc`, plus `cascade_config`, `layered_ldpc_config`, `qldpc_config` in the v3 master YAML [repo-observed]
- CLI arguments that must not silently change:
  - `build_dataset.py`: `--input`, `--output`, `--dimension`, `--frame-len-symbols`, `--dataset-id`, `--scan-sidecars` [repo-observed]
  - `build_representative_subset.py`: `--input`, `--output` [repo-observed]

  - `run_benchmark.py`: `--config` [repo-observed]
  - `compare_methods.py`: `--input`, `--output` [repo-observed]
  - `smoke_test.py`: `--config` [repo-observed]
  - `run_cascade_param_sweep.py`: `--config` [repo-observed]
  - `run_layered_ldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_qldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_ir_v3_master.py`: `--config` [repo-observed]
  - `make_report_tables.py`: `--config` [repo-observed]
- config keys that must not silently change:
  - method names: `polar_existing`, `cascade_lite`, `layered_ldpc_lite`, `qldpc_reference` [repo-observed]
  - v3 sweep keys including `block_size_schedule`, `num_passes`, `permutation_mode`, `seed`, `verify_mode`, `frame_caps`, `parity_fraction`, `max_iter`, `osd_order`, `bp_method`, `mapping`, `llr_mode`, `bitplane_rate_mode`, `check_fraction`, `row_weight`, `decoder`, `channel_model` [repo-observed]
- function signatures that must not silently change:
  - `FrameBatch`, `IRRunConfig`, `IRRunResult` dataclass fields in `comparison_bench/src/comparison_bench/types.py` [repo-observed]
  - `load_pairs_table(path: Path) -> pd.DataFrame` [repo-observed]
  - `normalize_pair_columns(df: pd.DataFrame) -> pd.DataFrame` [repo-observed]
  - `build_frame_batch(...) -> FrameBatch` [repo-observed]
  - `locate_existing_polar_outputs() -> list[Path]` and `run_polar_existing(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult` [repo-observed]
- output file naming conventions:
  - base benchmark outputs: `ir_benchmark_results.csv`, `ir_frame_results.parquet`, `run_manifest.json`, `ir_method_summary.csv` [repo-observed]
  - v3 outputs: `cascade_param_sweep_results.csv`, `layered_ldpc_param_sweep_results.csv`, `qldpc_param_sweep_results.csv`, `run_errors_ir_v3.csv`, `ir_v3_run_manifest.json`, `report_tables_v3/*.csv` [repo-observed]

## 7. Baseline and Scientific Semantics
- baseline algorithms:
  - original imported baseline: `polar_existing` [repo-observed]
  - executable classical baseline: `cascade_lite` [repo-observed]
  - executable binary LDPC baseline: `layered_ldpc_lite` [repo-observed]
  - q-ary reference baseline: `qldpc_reference` [repo-observed]
- current assumptions:
  - original Polar code is frozen and must be treated as read-only baseline logic. [repo-observed]
  - comparison layer is outer-wrapper only; it should read existing Polar outputs first and only use CLI mode if explicitly configured. [repo-observed]
  - `cascade_lite` is an internal simplified multi-pass parity/bisection baseline, not a full industrial Cascade transcript implementation. [repo-observed]
  - `layered_ldpc_lite` is a binary bit-plane baseline using `ldpc.BpOsdDecoder` when available, with explicit failure statuses rather than fake success. [repo-observed]
  - `qldpc_reference` currently represents a reference-grade q-ary decoder path, not a production qLDPC system. [memory-derived]
- high-risk variables:
  - `dimension` / `q` [repo-observed]
  - `bin_width_ps` [repo-observed]
  - `frame_len_symbols` [repo-observed]
  - `parity_fraction` [repo-observed]
  - `max_iter` [repo-observed]
  - `mapping` (`gray` vs `natural`) [repo-observed]
  - `llr_mode` and `bitplane_rate_mode` in layered LDPC sweeps [repo-observed]
  - `block_size_schedule`, `num_passes`, and `permutation_mode` in Cascade sweeps [repo-observed]
- known coupling/confounding factors:
  - raw SER and dimension are strongly coupled to decode success on real-data representative points. [memory-derived]
  - imported `polar_existing` point-level results are not always frame-identical to executable baseline frame subsets. [memory-derived]
  - leakage numbers are method-specific decompositions and should only be compared when the decomposition semantics remain consistent. [repo-observed]
  - sidecar-derived frame batches depend on `a_eff.npy` / `b_eff.npy` plus sidecar metadata, so path/layout assumptions matter. [repo-observed]
- metrics that must preserve meaning:
  - `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber` [repo-observed]
  - `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit` [repo-observed]
  - `accepted_frame_fraction`, `rejected_frame_fraction` [repo-observed]
  - `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify` [repo-observed]
  - `beta_eff_empirical` must remain derived from leakage and error inputs, not hand-filled. [repo-observed]

## 8. Known Issues and Fragile Points
- path issues:
  - original and comparison workflows have historical Windows-specific path usage; these must be translated deliberately for WSL. [repo-observed]
  - `polar_existing_bridge.py` still contains a legacy Windows default for `DEFAULT_POLAR_RESULTS_ROOT`; treat that as historical provenance, not a future path contract. [repo-observed, legacy Windows path]
- environment issues:
  - git commit/stage may fail because `.git/index.lock` cannot be created. [memory-derived]
  - PowerShell profile warnings are noisy but not necessarily fatal. [memory-derived]
  - optional parquet/YAML dependencies may be missing, causing fallback behavior. [repo-observed]
- data format issues:
  - sidecar directories are directory-based datasets, not flat CSV files. [repo-observed]
  - `load_pairs_table()` supports CSV, parquet/pickle, and sidecar directories; unsupported formats will fail. [repo-observed]
  - comparison outputs also contain test fixtures and temporary pytest artifacts under `comparison_bench/outputs_comparison/`; do not treat those as production outputs. [repo-observed]
- numerical/scientific interpretation risks:
  - `polar_existing` imported results may legitimately contain `NaN` for fields absent from source tables, especially leakage/runtime supplements. [memory-derived]
  - `qldpc_reference` results must not be described as full industrial qLDPC results unless method status and notes explicitly justify that. [repo-observed]
  - `cascade_lite` strong performance in representative sweeps should not be overinterpreted as final paper-grade evidence without broader sweeps. [memory-derived]
  - `layered_ldpc_lite` failure regions may reflect multiple causes: high raw SER, short frame length, parity allocation, or bit-plane independence assumptions. [memory-derived]
- long-running commands:
  - any `longrun_*`, `minrerun_*`, or `routeA_*` tooling under `tools/` [repo-observed]
  - real-data benchmark sweeps and `run_ir_v3_master` can be substantial even with representative subsets. [repo-observed]

## 9. Agent Operating Constraints
- minimal patch only. [repo-observed]
- no broad refactoring of original repository structure. [repo-observed]
- no raw data modification. [repo-observed]
- no result overwrite in `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked. [repo-observed]
- no baseline semantic change to the copied Polar workflow. [repo-observed]
- no schema change unless explicitly requested. [repo-observed]
- WSL/POSIX path default for future harness and agent docs. [repo-observed]
- treat legacy Windows paths as provenance only; do not bake them into new harness defaults. [repo-observed]
- preserve current CLI names, config keys, output file names, and CSV field names. [repo-observed]
- do not silently convert `reference`, `stub`, `unavailable`, `decode_failed`, or `no_verified_success` into `ok`. [memory-derived]
- follow AGENTS.md §5.7 Research Code Engineering Policy: local research code, simplest scientifically correct implementation, no unrequested defensive machinery (checksums, locking, retries, etc.). [repo-observed]

## 10. Unknowns To Verify
- Which original `docs/` files inside this repo are authoritative versus copied from another upstream state. [uncertain]
- Whether MATLAB/Octave is actually required anywhere in this repository copy. [uncertain]
- Whether the original Polar front-half and replay/security scripts are fully runnable in WSL without binary/toolchain adjustments. [uncertain]
- Whether `src/reconciliation/cpp_polar/` binaries are Windows-only in practice or have a portable rebuild path documented elsewhere. [uncertain]
- Whether all existing v3 comparison outputs should be treated as canonical or as exploratory benchmark artifacts. [uncertain]
- Whether any additional AGENTS-style repository guidance already exists outside the scanned paths. [uncertain]
- Whether the external real raw-data root used historically is mounted in the target WSL environment. [uncertain]
- Whether AGENTS.md §10.1 items 7 and 11 should be revised to remove hash wording
  ("self-hashes recomputed", "hashes for untracked files"): this conflicts with
  §5.7 and the 2026-08-06 no-hash amendment, and is a pending main-thread
  decision (noted in `evidence/v10_protocol_amendment_no_hash_v1.json`);
  revising AGENTS.md would require a separate OpenSpec change. [decision-pending]

## 11. Multi-Agent Workflow Files

### Created (2026-06-15)
- `AGENTS.md` — repository-level agent rules (baseline protection, output policy, schema stability, path discipline, agent constraints, OpenSpec workflow). [created]
- `docs/decision-log.md` — durable decisions and rejected alternatives. [created]
- `docs/troubleshooting.md` — reusable failure modes and fixes. [created]
- `openspec/project.md` — project-level context for OpenSpec change management. [created]
- `openspec/changes/real-ir-success-first/` — active change proposal details. [created]
- `CURRENT_TASK.md` — current active documentation/workflow task. [created]
- `RUN_COMMANDS.md` — curated smoke/benchmark/do-not-run command list. [created]
- `REVIEW_CHECKLIST.md` — review checklist for baseline protection and schema stability. [created]
- `AGENT_HANDOFF.md` — concise handoff note for the next agent. [created]
- `comparison_bench/src/comparison_bench/metrics/success.py` — success classification module. [created]
- `comparison_bench/src/comparison_bench/cli/build_representative_subset.py` — representative subset extractor. [created]
- `comparison_bench/configs/benchmark_representative.yaml` — representative subset benchmark config. [created]
- `comparison_bench/tests/test_success_classifier.py` — success classification unit tests. [created]
- `docs/real-ir-success-audit-20260615.md` — audit report summarizing baseline evaluations on representative frames. [created]

### Current OpenSpec state (verified 2026-07-25)
- Phase 0 reconciliation is `docs/openspec-phase0-reconciliation-20260725.md`.
  All five historical IR changes remain active: `real-ir-success-first` has
  32/34 evidenced tasks; optimization has 14/14 tasks but lacks its written
  512/1024-symbol evidence; expanded evidence has 19/20; evidence-package
  has 26/26 tasks but lacks clean direct fixed-path pytest and a before/after
  non-modification proof; group-meeting has 21/29 and lacks its frame-count,
  expected-config/test, and clean-full-suite requirements. Do not archive any
  historical change from artifact presence alone. [repo-observed]
- `final-ir-method-selection` was archived on 2026-07-25 at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/`; its
  canonical specification is `openspec/specs/final-ir-method-selection/spec.md`.
  It is the bounded comparison protocol that
  ranks only executable `cascade_lite` and `layered_ldpc_lite`; qLDPC remains
  `reference_only`, and `polar_existing` is historical, non-frame-identical
  context. It requires group-disjoint tuning/confirmation, one frozen global
  configuration per candidate, retained attempted failures, unranked
  method-specific leakage, bounded stopping, and a non-numerical Route A
  field-compatibility gate. [repo-observed]

### Final-IR authoritative evidence chain (verified 2026-07-25)
- v1 data lock is
  `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`.
  The locked domain is real d=1024, 64-symbol frames, dataset raw SER
  [0.20, 0.30), with 60 tuning frames from
  `real_typeii_20db_d1024_bw200_blk0` and 60 confirmation frames from
  `real_typeii_20db_d1024_bw180_blk0`; the groups are disjoint. Verify
  read-only with `python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --verify --manifest comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json`.
  [repo-observed]
- v1 Phase-3 outputs are invalid for decisions (`invalid_run_notice.json`).
  v2 is the sole authoritative bounded run:
  `.../20260725_v2/`; it froze Cascade `[12,6,24,13]`, 4 passes,
  seeded-random gray, and LDPC parity 1.0, 50 iterations,
  `bsc_estimated`/`uniform` gray before confirmation. It retained all 60
  attempts per candidate: Cascade 60/60 independently verified successes and
  LDPC 59/60. [repo-observed]
- v3 audit is superseded by its additive notice. v4 is authoritative:
  `.../20260725_v4_audit/`. Its read-only audit verifies the same 60 locked
  confirmation keys, frozen corrected-grid configurations, all status
  denominators, and evidence hashes. One Cascade-only discordance gives the
  pre-registered exact two-sided paired p-value 1.0 at alpha 0.05; outcome is
  strictly `no_decision`, not a winner. Claims do not extend beyond the locked
  domain, do not rank cross-method leakage, and do not select Polar or qLDPC.
  [repo-observed]
- The Route A compatibility gate is `fail`: comparison outcomes lack the
  documented universal-hash verification, leakage-accounting, and
  correctness-budget fields. No Route A numerical rerun or formal-proof claim
  was made. [repo-observed]
- Phase-5 verification: five-module `py_compile`, focused unittests 7/7,
  read-only v1/v4 verification, and safe comparison pytest 22/22 passed with
  `test_evidence_package.py` excluded because it writes a fixed tracked path.
  External pytest temp/permission behavior remains an infrastructure caveat;
  the six tracked `workspace/pytest-tmp/` deletions are pre-existing and must
  remain untouched. [repo-observed]

### Formal IR qualification evidence chain (verified 2026-07-25)
- Formal candidates are additive under
  `comparison_bench/src/comparison_bench/formal_ir/`; the
  frozen Polar pipeline and the `cascade_lite`/`layered_ldpc_lite` methods and
  their evidence remain unchanged. [repo-observed]
- The sole authoritative synthetic qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
  Its strict read-only report promotes `cascade_formal_v1` in both strata
  (32/32 `verified_success` at p=.01 and p=.02). It does not promote
  `ldpc_formal_v1` (29/32 and 14/32); all 21 retained non-successes are
  `verify_failed`, with zero unclassified/internal/provenance/accounting
  failures. [repo-observed]
- The invalid real v1 root received only its additive invalid-lock notice and
  made zero formal-method calls. The sole authoritative real qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`:
  its strict verifier accepts exactly seven artifacts, its preflight passed
  29 tests with exit 0, and Cascade achieved 60/60 requested confirmation
  frames as `verified_success`, with union bound `3.2526065174565133e-18` and
  zero unclassified/internal/provenance/accounting failures. The resulting
  promotion is limited to d=1024, 64 symbols, bw120, frame SER `[.20,.30)`;
  LDPC was not run on real data. [repo-observed]
- Read-only verification commands (do not rerun the qualification runners):
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic --verify`
  and
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_real_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade --verify`.
  [repo-observed]
- Before any frame-identical Polar/Cascade/LDPC comparison, a separate
  LDPC-improvement OpenSpec change must obtain fresh synthetic and real LDPC
  promotion. Do not substitute a lite method or tune on confirmation data.
  [repo-observed]

### Formal LDPC v2 improvement evidence (verified 2026-07-26)
- Archived change is
  `openspec/changes/archive/2026-07-26-improve-formal-ldpc-v2/`. Additive
  `ldpc_formal_v2` freezes
  nine policies: rate margin 0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, and
  `OSD_CS/2`. The n=64 nested codebook has 16 masters per plane and selected
  prefix matrices 32/40/48/56. Its structural screening is a proxy, not
  verified decoding evidence. [repo-observed]
- The v1 integration root `20260725_v1_ldpc_v2_synthetic` is invalid: the
  v1 codebook verifier makes all 576 policy outcomes plus 64 associated
  outcomes `unsupported_domain`. Its seven artifacts remain immutable and an
  additive invalid notice records the exclusion. [repo-observed]
- Fresh v2 plan SHA256 is
  `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`, with
  zero old/new CSPRNG overlap. Strict verification passed. Development results
  are 26/64 (margin 0), 33/64 (margin 1), and 56/64 (margin 2), identical for
  every OSD variant; the selected policy is rate margin 2 with `OSD_0/0`.
  [repo-observed]
- Confirmation records 28/32 at p=.01 and 29/32 at p=.02, seven
  `verify_failed`, and verification invoked for all 64 outcomes, with zero
  unclassified/internal/provenance/accounting failures. Status is
  `non_promoted`; no real lock or run is authorized, and confirmation must not
  be used to tune. [repo-observed]
- Artifact SHA256 prefixes: plan `c077...`, codebook `360b77...`, outcomes
  `9adb0...`, policy `303919...`, transcript `4b438...`, manifest `d185fc...`,
  report `53fbe5...`. Final checks: v2-focused 25 passed plus 5 subtests,
  general 52 passed/11 skipped, formal-real 12 passed, strict verification
  passed, and frozen `src/`, `experiments/`, `tools/`, and `results/` diff is
  empty. Terra low only implemented frozen tasks and specified tests; the main
  thread retained planning and acceptance. [repo-observed]
- Short- and medium-term engineering work is complete with reproducible
  evidence, but LDPC has not met promotion; the fair three-method comparison
  remains blocked. [repo-observed]

## 11. Parallel Binary and Nonbinary LDPC Direction (2026-07-26)

- Binary and nonbinary LDPC are now planned as independent parallel research
  lanes. The detailed handoff is
  `comparison_bench/docs/ldpc_parallel_handoff.md`. [repo-observed]
- Binary starts from immutable, non-promoted `ldpc_formal_v2` evidence and
  targets longer frames, deterministic QC/PEG/protograph families,
  incremental redundancy, and per-bit-plane soft information. Existing
  confirmation evidence cannot be used for tuning. [repo-observed]
- Nonbinary N0 field-backend work is implemented under the independent
  `nbldpc_formal_v1` identity in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py`.
  It pins deterministic polynomial-basis GF(2^m) arithmetic for powers-of-two
  q through 1024, canonical field metadata/IDs, and a read-only fail-closed
  preflight. `qldpc_reference` remains unchanged and reference-grade.
  This proves field-backend feasibility only, not decoder feasibility,
  qualification, promotion, or comparison readiness. [repo-observed]
- The two lanes require separate OpenSpec changes, codebooks,
  development/confirmation splits, artifacts, leakage accounting, verifiers,
  and promotion decisions. Only independently promoted methods may enter a
  later frame-identical comparison. [repo-observed]

## 12. Binary LDPC Long-Frame v3 Phase 1 (2026-07-26)

- Active OpenSpec change:
  `openspec/changes/binary-ldpc-long-frame-and-ir-v3/`. [repo-observed]
- Candidate-only `codebook_long_v3.py` supports n=256/512/1024, ten planes,
  four deterministic candidates, and nested 1/2, 5/8, 3/4, 7/8 check
  prefixes. HGF2V3 bytes and a reconstruction-verified manifest bind all 120
  candidate identities. [repo-observed]
- Actual-rank, no-zero/duplicate-column, weight-bound, exact 4-cycle, and
  `column_pair_extrinsic_degree_v1` proxy tests passed. Main-thread evidence:
  focused 4 passed in 10.88 s; v2 regression 7 passed/1 skipped in 81.41 s;
  compilation/diff checks passed and frozen directories were unchanged.
  [repo-observed]
- Phase 1 is engineering evidence only: no FER, candidate selection, decoder,
  confirmation/real data, qualification, or promotion. Next freeze a
  sacrificed-development FER evaluation contract. [repo-observed]

## 13. Binary LDPC Long-Frame v3 Phase 2 (2026-07-26)

- `long_v3_development.py` implements exact sacrificed p=.01/.02 generation,
  canonical seed/source hashes, pinned BP+OSD-0 metadata, four-prefix
  incremental evaluation, retained statuses, and exact four-candidate
  selection. It is in-memory and writes no result artifact. [repo-observed]
- Selection is frozen as worst-stratum successes, total successes, syndrome
  disclosure, then candidate ID. Runtime and structural proxies are excluded.
  Tests independently verify the data/policy/selection hash preimages and
  fail-closed malformed-grid behavior. [repo-observed]
- Main-thread evidence: focused 5 passed in 0.53 s; Phase1/v2 regression
  11 passed/1 skipped in 92.68 s; compilation and frozen-directory checks
  passed. [repo-observed]
- Phase 2 used injected test decoders only. No pinned-backend development
  sweep, candidate FER evidence, selection, confirmation, real data,
  qualification, or promotion exists yet. Next freeze a bounded backend
  preflight/pilot. [repo-observed]

## 14. Binary LDPC Long-Frame v3 Phase 3A Pilot (2026-07-26)

- A single in-memory pinned-backend pilot ran exactly once at
  n=256/plane0/candidate0/p=.01 on 16 sacrificed frames. Backend was
  `ldpc==2.4.1`; exit 0; stderr empty; process 0.3227008000249043 s; external
  wall 1.0 s. [repo-observed]
- Outcomes were 16/16 exact success, terminal p050=15/p0625=1, and 2080 total
  syndrome bits. No file was written and no candidate was selected.
  [repo-observed]
- This clears one-slice backend feasibility only. It is not comparative FER,
  n=512/1024 evidence, qualification, or promotion. Next freeze an immutable,
  verifier-bound full sacrificed-development sweep contract. [repo-observed]

## 15. Binary LDPC Long-Frame v3 Phase 3B Tooling (2026-07-26)

- Additive runner/verifier tooling now freezes a 3840-row, 30-selection
  sacrificed-development grid with prepare/execute no-overwrite lifecycle,
  six canonical artifacts, code/backend/hash DAG, failure finalization, and
  production/test isolation. [repo-observed]
- Read-only verification reconstructs deterministic source provenance and the
  accepted candidate-selection function, but does not rerun LDPC decoding.
  Its success is artifact integrity only. [repo-observed]
- Main-thread evidence: Phase3B focused 3 passed in 12.30 s; all long-v3
  12 passed in 12.94 s; v2 regression 7 passed/1 skipped in 81.34 s;
  compilation/diff/frozen-directory checks passed. Test artifacts are under
  `workspace/formal_long_v3_phase3b_tests_run3`. [repo-observed]
- No production plan or 3840-row sweep exists yet. Next create and inspect one
  fresh plan, then separately authorize its single execution. [repo-observed]

## 16. Binary LDPC Long-Frame v3 Phase 3C Development Evidence (2026-07-26)

- Immutable development root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.
  Execute ran once in 28.9 s with 3840 outcomes/30 selections; strict verifier
  ran once in 11.2 s, exit 0, without decoder reexecution. [repo-observed]
- All 3840 per-plane candidate outcomes were
  `development_exact_success`. Selected per-plane mean syndrome bits:
  n256 129.0/134.6, n512 260.4/280.4, n1024 541.6/635.2 for p001/p002.
  [repo-observed]
- The current per-plane terminal is chosen using Alice-truth exact equality.
  This is a sacrificed-development oracle and not a deployable stopping signal;
  its leakage and 100% result are not qualification evidence. [repo-observed]
- Next aggregate ten planes into global incremental rounds with one
  frame-wide Toeplitz verification tag, count slowest-plane syndrome/tag
  leakage, then select the formal length/policy before fresh confirmation.
  [repo-observed]

## 17. Binary LDPC Long-Frame v3 Phase 4 Frame Development (2026-07-26)

- Ten-plane read-only aggregation produced 96 q=1024 development frames and
  modeled one 64-bit frame-wide Toeplitz tag over at most four global rounds.
  Aggregation SHA256 is
  `029e33c42f254e40725a370065d30196216501085d5def5f0f0c935aca6c933c`.
  [repo-observed]
- All lengths retained 16/16 success in both strata. Mean frame key-disclosure
  fractions p001/p002: n256 .5640625/.68125; n512 .590625/.7546875; n1024
  .6625/.8421875. [repo-observed]
- Frozen development choice is n=256 with tuple
  `[-16,-32,.68125,.62265625,256]`. This is sacrificed-development design
  selection only; the stopping tag was modeled, not executed. [repo-observed]
- Next implement actual n256 ten-plane formal decoding, locked Toeplitz
  seed/tag, transcript, caps and fail-closed statuses before any fresh
  qualification. [repo-observed]

## 18. Binary LDPC Long-Frame v3 Phase 5 Formal Method (2026-07-26)

- `formal_ir/ldpc_v3.py` implements `ldpc_formal_v3` for exactly q=1024,
  n=256 and ten MSB-first Gray planes with frozen candidates
  `[1,0,1,2,0,0,1,3,2,3]`. [repo-observed]
- It reconstructs canonical long-v3 matrices, validates a self-hashed
  sacrificed calibration, requires `ldpc==2.4.1`, and decodes all ten planes
  in four possible synchronous incremental-syndrome rounds. [repo-observed]
- One 64-bit frame-wide Toeplitz tag is disclosed once and checked only after
  complete rounds. The decoder receives no tag/match or Alice truth. Strict
  transcript validation binds terminal prefix, syndrome/tag/seed disclosure,
  epsilon, caps, backend and frozen selection. [repo-observed]
- Main-thread evidence: focused 6 passed in 2.15 s; long-v3 regression 13
  passed in 16.12 s; v2 regression 7 passed/1 skipped in 81.27 s;
  compilation/diff/frozen-directory checks passed. [repo-observed]
- This accepts method engineering only. No confirmation runner/artifact,
  strict package verifier, qualification, promotion, real-data result, or fair
  comparison eligibility exists. Phase 6 must be planned and frozen before
  execution. [repo-observed]

## 19. Binary LDPC v3 Phase 6 TTBIN Bridge and Synthetic Stop (2026-07-26)

- Phase 6A read-only bridge binds the real 20 dB main/chunk TTBIN and exact
  q=1024 sidecars, selects 64 bw100 calibration plus 32 each bw120/180/200
  reserved confirmation frames, and reconstructs source/lock/calibration
  hashes. Calibration plane p_hat ranges from .000366 to .122620.
  [repo-observed]
- Immutable synthetic package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`
  was prepared, executed, and strictly verified exactly once. Verification
  accepted 64 outcomes and returned `decoder_reexecution=false`.
  [repo-observed]
- Calibrated confirmation achieved 3/32 and 1.25x stress achieved 1/32 versus
  31/32 gates. The other 60 outcomes are `verify_failed`; forbidden
  internal/provenance/accounting failures are zero. [repo-observed]
- Binary v3 is non-promoted. Phase 6C real tooling/output was not created and
  is locked. Do not tune or retry from confirmation. A successor requires a
  new OpenSpec improvement and fresh synthetic confirmation. [repo-observed]
- Nonbinary N1 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py` as a
  pure in-memory n=64 family: one deterministic 32x64 mother matrix and exact
  16/24/32 ordered prefixes, with three SHA256-derived cyclic shifts,
  explicit nonzero GF(q) coefficients, an identity parity half, and rank
  calculated with the pinned N0 GF(q) arithmetic. [repo-observed]
- Canonical `NBLDPC1` bytes include the full field representation,
  construction, dimensions, topology, coefficients, seed, and ordering.
  Golden codebook/manifest SHA256 tests plus reconstruction-based tamper
  checks cover field, coefficient, rank, prefix, codebook-ID, and manifest-ID
  drift. Focused N0+N1+qLDPC tests passed 22/22; the selected
  formal/nonbinary/qLDPC regression passed 29/29. [repo-observed]
- N1 is structural rank/hash evidence only. It does not establish a soft
  decoder, distance/FER performance, qualification, promotion, outputs, or
  comparison readiness. N2 must freeze decoder and formal accounting
  contracts before implementation or dependency selection. [repo-observed]
- Nonbinary N2 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py` as a pure
  full-message probability-domain FFT-QSPA feasibility decoder. It consumes
  Bob symbols, Alice's public syndrome, and verified N1 codebooks; its public
  decoder signature has no Alice truth or callback. q=4 coefficient/coset
  check updates match brute-force convolution, and q=1024 executes inside the
  frozen n=64/check/iteration/16-MiB declared dense-message bounds.
  [repo-observed]
- `syndrome_consistent` is deliberately separate from locked Toeplitz
  verification. Symbols map to fixed-width MSB-first bits; syndrome
  disclosure is checks*log2(q), invoked verification tags add their exact
  length, and public-control bits remain separate. N0-N2 plus qLDPC tests
  passed 35/35; selected formal verification/Cascade/LDPC regressions passed
  17 with 2 skipped. [repo-observed]
- N2 is bounded engineering feasibility only. It does not prove general
  correction, FER/performance, calibration, synthetic/real qualification,
  promotion, outputs, production readiness, or comparison eligibility. N3
  requires planner-owned pre-registration before execution. [repo-observed]

## 20. Nonbinary LDPC v2 Development Non-Readiness (2026-07-26)

- `nbldpc_formal_v2` Phase 1/2 was accepted with 21 focused tests; the joint
  N0-N3/v2/formal regression passed 86 with 8 skipped. [repo-observed]
- The immutable root
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
  contains one reviewed plan (112 frames, 24 policies, 1216 unique seeds,
  overlap zero), one execution, and one successful strict full replay.
  [repo-observed]
- The selected tempered+damped QC48 policy used margin 8, max_iter 10, and
  32/40 checks for p=.20/.30. Development achieved 0/24 and 5/24 verified
  successes against a 22/24-per-stratum readiness floor. Confirmation was
  never generated or executed. [repo-observed]
- Status is `non_promoted_development`, not confirmation FER or real-data
  evidence. No rerun, tuning, N4 sidecar adapter, or `.ttbin` processing is
  authorized. [repo-observed]

## 21. Binary LDPC v4 Development Backend Stop (2026-07-27)

- `binary-ldpc-adjacent-channel-v4` implements deterministic adjacent-channel
  modeling, 40 anchored sparse binary codebooks, a fixed 648-bit formal
  method, immutable development/synthetic/real packages, and read-only
  source/transcript/gate verifiers. Focused main-thread acceptance passed
  15+8+3+4 tests; cross-version regression passed 119 with 10 skipped.
  [repo-observed]
- Sole production development evidence:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `af644e2f4a3dab596f34350b18ecfb1df56cb46b93670cb16e89f3ca1ae67c5e`.
  The read-only verifier returned verified/completed with
  `decoder_reexecution=false`, but readiness was false. [repo-observed]
- Nominal and stress each retained 512 denominators, zero frame successes,
  and 5,120 selected-plane `development_decoder_error` outcomes. This is an
  implementation failure and must not be interpreted as FER or code quality.
  [repo-observed]
- A no-decode diagnostic confirmed the backend mismatch: `ldpc==2.4.1`
  rejects NumPy-array `error_channel` with `expected list`, while the same
  vector converted by `.tolist()` constructs. The formal v4 path converts it;
  the frozen development path did not. [repo-observed]
- No v4 production synthetic or real directory exists. The frozen stop rule
  forbids editing/tuning/rerunning this package. A continuation needs a new
  versioned OpenSpec implementation-correction lane and fresh evidence; fair
  Cascade/LDPC/Polar comparison remains blocked. [decision]

## 22. Binary LDPC v4 Backend Correction Readiness (2026-07-27)

- `binary-ldpc-v4-backend-correction-v1` added only versioned development
  files. It converts the frozen Bob-conditioned float64 error channel to a
  Python list at the `ldpc==2.4.1` constructor boundary; historical v4 source
  and evidence hashes remain unchanged. [repo-observed]
- Immutable corrected package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `1e208832ac421e69c0488d33e39953755ba487c25f9bf9db43bdda79cc53daaf`.
  Prepare/execute/read-only verification each ran once; verification returned
  completed/verified, `decoder_reexecution=false`, and readiness true.
  [repo-observed]
- Frozen development results are 510/512 adjacent nominal and 511/512
  adjacent stress, with zero forbidden failures. Selected candidates are
  `[0,0,0,0,0,0,2,0,2,2]`. This clears only the 495/512 sacrificed-
  development screen. [repo-observed]
- No corrected-v4 synthetic or real production output was created. Synthetic
  qualification still requires a fresh main-thread plan audit and one
  independent execution; comparison eligibility and real `.ttbin` claims
  remain unestablished. [decision]

## 23. Binary LDPC v4 Corrected Synthetic Promotion (2026-07-28)

- Immutable package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`
  strictly verified with 256 outcomes, no decoder reexecution, and promotion:
  nominal 127/128, stress 126/128, zero forbidden failures. [repo-observed]
- Plan content SHA256 is
  `02a198ea4d03ae4d7dad7db6e2b4099e85f5b75c0d8acad34e8449d67cb769fb`.
  Fresh roots/seeds have zero overlap with v3 and development. Do not rerun or
  tune from this confirmation. [repo-observed]
- Real qualification remains unrun. Current bw120/bw180/bw200 sidecars each
  have 117 complete frames; excluding 32 v3-reserved identities leaves 85,
  below the frozen 128 by 43 per stratum. Real prepare must remain blocked
  until traceable same-domain source data fills that deficit. [decision]
- Prefer at least 64 newly supplied complete frames per real stratum to absorb
  duplicate/incomplete rejection. Preserve 128 denominators and 126/128 gates;
  do not reuse reserved frames or weaken the claim to fit current data.
  [decision]

## 24. Binary LDPC v4 Real-Source Intake Acceptance (2026-07-28)

- The only other local 20 dB tree is a byte-identical raw-capture copy. Its
  main/chunk SHA256 pair equals the registered capture, so it is not new
  statistical capacity. [repo-observed]
- The Phase 4 intake layer now builds and reconstructs a no-overwrite,
  self-hashed multi-acquisition source extension. It rejects duplicate raw
  pairs and frame payloads, binds exact q=1024 bw120/bw180/bw200 sidecars,
  counts only complete 256-symbol frames, and performs no decoding.
  [repo-observed]
- Main acceptance passed 3 source, 5 real, 7 bridge/source, and 25
  backend/development/formal-real tests. Historical v3/development source
  hashes remain exact and no real production directory exists.
  [repo-observed]
- Real prepare remains unauthorized until a genuinely distinct 20 dB
  acquisition supplies enough validated capacity and a main-thread-reviewed
  extension manifest. The 128 denominators and 126/128 gate remain frozen.
  [decision]

## 25. Project-Wide Delegation Workflow (2026-07-29)

- Substantial delegated implementation starts from one complete frozen task
  packet: file scope, functionality, full test/evidence matrix, commands,
  artifacts, stop rules, and return conditions. [decision]
- The main thread owns planning, requirements, thresholds, OpenSpec,
  acceptance, and scientific conclusions. The implementation subagent is an
  operator and returns only a complete candidate or a concrete reproducible
  blocker; partial “still incomplete” reports are not completion. [decision]
- Main review normally occurs at spec freeze, complete candidate delivery, and
  independent acceptance. Tests progress from focused development to combined
  focused candidate to main regression/compile/frozen-hash/no-output review.
  [decision]
- Verifier acceptance matrices must pre-register byte drift, locally re-signed
  semantic tampering, re-signed manifest/index tampering, and deep
  cross-artifact reconstruction. Known Windows ACL failures require an
  explicitly writable non-production test root. [decision]
- These coordination optimizations do not alter prepare/review/execute/verify,
  immutable failure retention, scientific thresholds, or no-rerun/no-tuning
  boundaries. [decision]
- Acceptance items use stable IDs. Successor evidence machinery starts from
  the nearest accepted predecessor and an explicit delta list. [decision]
- Tests use T0 compile/structural, T1 focused, T2 fake qualification/replay,
  and T3 regression stages; T2/T3 run only at milestones and test-only calls
  explicitly pass fake runners. [decision]
- Windows tests use additive workspace UUID roots with pytest cache disabled.
  Process termination requires positive ownership; dirty-worktree acceptance
  includes untracked hashes, frozen diffs, and output-root checks. [decision]
- Handoffs report only changed files, commands/results, concrete blockers, and
  remaining acceptance IDs; they do not repeat durable project context.
  [decision]

## 26. Binary LDPC v4 16 dB Transfer Result (2026-07-29)

- The sole 16 dB transfer package completed and strictly verified with all 384
  outcomes: bw120 125/128, bw180 128/128, bw200 128/128, and zero forbidden
  failures. Because every layer required 126/128, the package is immutable
  `non_promoted_transfer`. [repo-observed]
- Read-only verification reported no decoder reexecution and changed none of
  the nine files. Plan content SHA256 is
  `ddbf41983d866ce5d320404323ff319b64a867f8f8c32185a890ab7baf97b2da`;
  source-lock content SHA256 is
  `5c654377751cea776a203269b8213959313aa9a0be738935816d36b52181ea87`.
  [repo-observed]
- The 16 dB evidence must not be tuned or rerun and does not promote 16 dB or
  20 dB. A separately scoped unchanged-method 10 dB transfer is frozen under
  `binary-ldpc-v4-10db-transfer-qualification-v1`; if promoted, its claim is
  limited to that independent 10 dB acquisition. [decision]

## 27. Binary LDPC v4 10 dB v1 Prepare Rejection (2026-07-29)

- The v1 10 dB prepare was rejected before execute because validation included
  its own newly written plan in the prior-real root set. It contains exactly
  plan and lock, no outcomes. Preserve it as `invalid_pre_execute`; plan file
  SHA256 is `dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c`
  and lock file SHA256 is
  `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf`.
  [repo-observed]
- A versioned correction must exclude only the current plan from prior-plan
  discovery while continuing to bind and forbid the invalid v1 roots/seeds.
  No scientific inputs or gates may change. [decision]

## 28. Binary LDPC v4 10 dB v2 Result and v5 Route (2026-07-29)

- The corrected v2 10 dB package strictly verified all 384 outcomes but was
  non-promoted: bw120 125/128, bw180 127/128, bw200 128/128, zero forbidden
  failures. Plan content SHA256 is
  `c6f3592ac24fd32ac136d16f06fd88157757216a81c40643e86d0ba3882af2f6`.
  [repo-observed]
- All four failures were retained `verify_failed` after complete syndrome
  disclosure and Toeplitz mismatch. v4 fixed-rate robustness, not source,
  backend, accounting, or resource failure, is the remaining issue.
  [repo-observed]
- Do not test progressively easier losses until one passes. The v5 route
  pre-locks disjoint unused 10 dB development and confirmation frames, screens
  frozen stronger-OSD/incremental-redundancy policies on development, then
  requires fresh synthetic promotion before one sealed real qualification.
  [decision]

## 29. Nonbinary LDPC v3 Covered-Layered Result (2026-07-30)

- The sole v3 synthetic package was planned once, executed once, and strictly
  replay-verified once. The selected layered-l075 margin-8 policy used 32/40
  checks and passed development readiness at 23/24 for p=.20 and 24/24 for
  p=.30. [repo-observed]
- Sealed confirmation was materialized only after readiness and achieved
  32/32 for p=.20 and 30/32 for p=.30, with zero prohibited failures. The
  frozen 31/32-per-stratum gate failed by one p=.30 frame, so the package is
  immutable synthetic non-promotion evidence. [repo-observed]
- Strict verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. Plan SHA256 is
  `0f35b8679166599efb294caee21822156ba971bec6271875cf55516523cfdee1`;
  selected-policy SHA256 is
  `6193f92af05c1d3a5145cbe31c95a4d20f1eaf5a09970936613c326cc1c59a28`.
  [repo-observed]
- Do not rerun, tune confirmation, overwrite evidence, build N4, access
  sidecars, or process `.ttbin`. Real-data work requires promoted synthetic
  confirmation and a new approved OpenSpec change. [decision]

## 30. Nonbinary LDPC v4 Incremental-Redundancy Result (2026-07-31)

- The sole v4 IR package was planned, executed, and strictly replay-verified
  once. Verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. [repo-observed]
- Development selected `nbldpc_v4_ir_warm`: 64/64 at p=.20 and 63/64 at
  p=.30. Sealed confirmation achieved 128/128 and 120/128; all eight misses
  were p=.30 `decode_failed`, with zero prohibited failures. [repo-observed]
- The package is immutable at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
  Do not rerun, tune, overwrite, build N4, access sidecars, or process `.ttbin`.
  Any successor requires new OpenSpec, fresh synthetic splits, and a
  pre-registered method change. [decision]
- Reusable process lesson: historical qualification suites whose own official
  roots now exist can correctly reject a test replay as identity reuse. Retain
  that evidence and use isolated algorithm regressions; never edit immutable
  outputs or weaken freshness guards merely to make an old suite green.
  [repo-observed]

## 31. Binary LDPC v5 Development, Synthetic, and Sealed Real Promotion (2026-08-01/2026-08-12)
- Phase 2 sacrificed development selected V5-C2: 1536/1536 verified success
  (512/stratum across bw120/bw180/bw200 real 10 dB frames), zero forbidden
  failures, 1 round, no fallback. Leakage 648 bits/frame = 2.531 b/symbol =
  0.253 b/input bit (h1 syndrome 584 + verification 64); real raw SER
  bw120 0.1228 / bw180 0.0833 / bw200 0.0767; 204.7 s total. Package immutable
  at comparison_bench/outputs_comparison/formal_ir_methods/
  20260731_v1_binary_ldpc_v5_development/. [repo-observed]
- Robustness evidence committed to comparison_bench/docs/ldpc_v5_robustness/:
  E1 new-seed rerun 768/768, E3 model-consistent (SER 0.243) 768/768,
  E2 uniform OOD control 0/1152 as expected. [repo-observed]
- Phase 3 fresh synthetic confirmation (2026-08-01): 256/256 verified success
  (nominal 128/128 + stress_125 128/128), zero forbidden failures,
  promoted=true, ready_for_real_qualification=true, decoder_reexecution=false.
  Package immutable at .../20260801_v1_binary_ldpc_v5_synthetic/; plan sha256
  c91171dcdde8c1cf5fb31cc21cbad72115756fff034763ce93c75cbef17c10ab. [repo-observed]
- Phase 4 sealed real qualification COMPLETED and PROMOTED (2026-08-12):
  384/384 verified_success — bw120/bw180/bw200 each 128/128, zero forbidden
  failures; report `promoted=true`, `run_status=completed`,
  `decoder_reexecution=false`. Official package (ten files, run_id
  `binary_ldpc_v5_real_qualification_v1`, plan_sha256
  `a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`,
  report_sha256
  `18b5566ed636a79473ff7290cb55d90d4ab20a170895b53f786ea2455ad953d5`):
  comparison_bench/outputs_comparison/formal_ir_methods/
  20260801_v2_binary_ldpc_v5_real/. Execute ~5m12s, read-only verify ~4m29s,
  detached background process. Chain: partition lock (20260731) → v5
  development (V5-C2, 1536/1536) → v5 synthetic (256/256, 20260801) → v5 real
  (384/384, 20260801_v2), each once with read-only verification. [repo-observed]
- v4's two real transfers remain retained as non-promoted failure evidence
  (16 dB 125/128 and 10 dB v2 125/128, both below the 126/128 gate); v5 is
  the first all-green real 10 dB Type-II promotion. Do not tune or rerun
  them. [decision]
- Comparison eligibility updated (2026-08-12): binary LDPC v5 may participate
  in comparison within the promoted 10 dB Type-II q=1024 Gray 256-symbol
  bw120/bw180/bw200 domain only; all other domains and methods (v4, 16 dB,
  20 dB, other captures, nonbinary, Cascade/Polar) keep their prior status.
  A rate-adaptive successor requires a separate OpenSpec change. [decision]
- Polar numerical comparison remains blocked: results/ is empty in this
  checkout and polar_existing imports are historical, non-frame-identical,
  leakage NaN. No Polar-vs-v5 numeric claim is supportable. [repo-observed]
- Reusable process lessons (2026-08-12): (a) Long qualification stages
  (prepare/execute/verify, ~5-20 min) exceed subagent/session channel
  timeouts; run them as a detached background process (background bat +
  log-file polling) outside the opencode session. (b) Three latent production
  bugs (synthetic_dir directory semantics, generator empty-dict check,
  missing root_id) were masked by tests that mocked core functions
  (`_seed_schedule`, `_validate_roots`, `_validate_plan`) and surfaced only at
  production prepare; keep a real-path smoke in tests rather than mocking
  whole core paths, so such defects surface at T0/T1 instead of at sealed
  qualification time. [decision]

## 32. Nonbinary LDPC v5 Multistage Change Terminated — Four Routes Non-Promoted (2026-08-02)
- The v5 multistage change (formal-nonbinary-ldpc-v5-multistage-ir) ran all four
  pre-registered routes A/B/C/D, each planned once, executed once, and strictly
  replay-verified once; every route hit the same p=.30 tail pattern
  (promotion gates p=.20 128/128, p=.30 127/128) and is `promoted=false`.
  Per task 7.4 the change terminates with four immutable non-promoted
  packages: 20260731_v5a_nbldpc_multistage_synthetic (three-level warm IR),
  20260731_v5b_nbldpc_mother_synthetic (NBLDPC5B mother, zero w2/w3),
  20260731_v5c_nbldpc_decoder_synthetic (sched/EMS decoders),
  20260731_v5d_nbldpc_post_synthetic (list L=2 x top-8 + ADMM rho=1.0
  <=50-iteration post-processing over the v5c decoders). [repo-observed]
- Route D execution (HEAD 192f455): run_status=completed, readiness true,
  512 outcomes; strict replay returned {'verified': True,
  'run_status': 'completed', 'promoted': False} with an unchanged worktree.
  Evidence: evidence/v5d_acceptance_d1_d2.json and v5d_acceptance_c3_c4.json. [repo-observed]
- Route D implementation corrections (main-thread approved, recorded in the
  module docstring and decision-log 2026-08-02): the frozen x-update prior
  term sign was wrong (+prior/RHO; correct is x = z - lambda - prior/rho) —
  a q=4 brute-force experiment showed recovery 0% -> 87-100% after the fix;
  and the frozen z-update alternating projection onto {simplex AND
  output-sum=e_s} is a strict subset of the GF(q) check polytope (it forces
  all output symbols to s) and could not recover codewords — replaced by the
  per-bit parity-relaxation projection (bitwise-XOR linearization), 100%
  exact recovery in the same experiment. A _V5D_BY_V5C reverse map fixes the
  production trigger (post.start delegates v5c and the state carries the v5c
  policy id). [decision]
- Procedural deviation recorded: the v5d 7.3 plan was created before the
  D1/D2 acceptance evidence file; closed read-only at the same HEAD with the
  plan unchanged (see v5d_acceptance_d1_d2.json). [repo-observed]
- Bounds: list L=2, top-8 symbols, exactly 64 candidates, at most one round,
  syndrome filter; ADMM rho=1.0, <=50 iterations, deterministic init, no
  random source; verification cap 3; no additional syndrome/tag disclosure. [repo-observed]
- N4, sidecar access, .ttbin processing, real-data qualification, and any
  comparison claim remain locked. A nonbinary successor requires a new
  OpenSpec change with fresh development and confirmation data; neither
  codebook redesign (B), decoder-family change (C), nor list/ADMM post (D)
  closed the p=.30 tail at the 128/128 floor. [decision]
- Reusable process lesson (already recorded at section 30): official roots
  existing in the shared output root make the same-run-id lane test suite
  self-conflict on identity freshness; that is the designed anti-replay
  guard, not a regression. [repo-observed]

## 33. Nonbinary LDPC v6 Long-Block Engineering Candidate Accepted (2026-08-02)

- Engineering candidate of change `formal-nonbinary-ldpc-v6-long-block`
  implemented and independently reviewed ACCEPTED (V6-50) 2026-08-02 at HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`. Seven new files:
  `formal_ir/nonbinary_v6_codebook.py`, `formal_ir/nonbinary_v6_long.py`,
  `formal_ir/nonbinary_v6_development.py`,
  `cli/run_formal_nonbinary_v6_development.py`,
  `tests/test_nonbinary_v6_codebook.py`, `tests/test_nonbinary_v6_long.py`,
  `tests/test_nonbinary_v6_development.py`, plus
  `evidence/v6_engineering_acceptance.json` under the change directory. No
  existing file modified; frozen `src/`/`experiments/`/`tools/`/`results/`
  diff empty; no official v6 output root exists under
  `comparison_bench/outputs_comparison/formal_ir_methods/`. [repo-observed]
- Method identity `nbldpc_formal_v6_long`: GF(1024), n=1024 symbols, two
  deterministic degree-2 PEG codebooks (1024,320) for p=.20 and (1024,480)
  for p=.30; check degrees 6/7 and 4/5; full GF rank 320/480; zero parallel
  edges; frozen seeds {320: 2026080200, 480: 2026080300} from a one-time
  bounded rank search, never re-searched at runtime; magic `b"NBLDPC6\n"`.
  [repo-observed]
- Decoder: ascending-row layered FFT-QSPA, lambda .75, max 50 iterations,
  single-threaded (workers=1 by construction), whole-graph syndrome check
  after every iteration, 64-bit Toeplitz verification only after syndrome
  consistency, syndrome disclosure 10*m bits plus 64 key-dependent tag bits,
  no fallback, fail-closed on NaN/Inf/non-finite/wrong length/malformed
  syndrome/allocation cap (dense message bound 50,331,648 bytes <= 64 MiB).
  [repo-observed]
- Acceptance: T0 16, T1 38, T2 6 (fake lifecycle + strict read-only replay
  with explicit fake runner; production decoder never entered), T3 51
  v5-regression (N0 field, N1 codebook, N2 qspa, v3 core, v5a codebook, v5a
  core); all 8 tamper classes rejected (byte, semantic self-hash, manifest
  link, source identity, transcript recanonicalized, leakage, gate
  rebuilding/promotion forgery); CLI default action is plan, execute is a
  hard SystemExit(2) refusal. Evidence JSON binds HEAD, source hashes,
  command exit codes, tier results, A01-A10. [repo-observed]
- Diagnostic observation, strictly diagnostic-only and NOT FER/qualification
  evidence: a full-rate random p=.20 frame does not converge within 50
  iterations (~85 s per frame); 1-2 planted errors and noiseless frames
  converge in 1 iteration. Consistent with the change's weak-baseline
  hypothesis. [repo-observed]
- Boundary state: V6-51 (reviewed sacrificed development plan with fresh
  roots) NOT authorized; V6-52 successor choice (qualification / n=4096 /
  multiplicative repetition / GF(32)xGF(32)) NOT made; no confirmation
  material, no real data, no promotion. v5 change remains terminated with
  four immutable non-promoted packages. [decision]
- Process note: memory-agent triage delegation returned empty three times
  without writing; the durable section above was appended directly by the
  orchestrator from verified session evidence. [decision]

## 34. Nonbinary LDPC v6 Canary 0/4 Both Strata — Long-Block Baseline Stopped (2026-08-02)

- Main-thread decision: no large-scale v6 development run. A small sacrificed
  8-frame canary (4 p=.20 + 4 p=.30, fixed (1024,320)/(1024,480) codebooks,
  lambda .75, max_iter 50, workers=1, fresh roots 202608024000/202608024100,
  no confirmation) was staged via a minimal additive CANARY config in
  `nonbinary_v6_development.py` (production execution authorized only for
  CANARY config with explicit workspace output; CONFIG 64-frame plan path and
  official-root lock preserved). Canary tests 8/8 new + 46 total + 51 v5
  regression passed. [repo-observed]
- Canary plan created once and read-only reviewed READY-FOR-SINGLE-EXECUTION
  (evidence/v6_51_canary_plan_evidence.json), executed exactly once (exit 0,
  450.9 s) and strict-replayed exactly once (exit 0, 518.6 s). Result: 0/4
  verified success in BOTH strata; all 8 frames `decode_failed` at
  max_iter=50 with zero forbidden statuses; run_status
  `development_completed`, promoted false. Package retained at
  `workspace/nbldpc_v6_canary_b01c42a5dee14ed0913e78d60944cc38/canary_plan`;
  no official root under `formal_ir_methods/` created.
  Evidence: evidence/v6_51_canary_execution_addendum.json. [repo-observed]
- Pre-registered gate fired: any stratum 0/4 -> stop the degree-2 n=1024
  long-block baseline, do NOT go to n=4096, prefer multiplicative repetition
  (2,3) mother code. V6-52 chose multiplicative repetition as the single
  successor; a new OpenSpec change must be proposed before implementation.
  [decision]
- Scientific note (diagnostic only): even the p=.30 stratum at 480 checks
  (4.6875 bits/symbol disclosed vs 3.88 entropy) failed 0/4 in 50 iterations
  on full-rate random frames; noiseless and 1-2 planted-error frames converge
  in 1 iteration. Consistent with a structurally weak degree-2 long-block
  baseline, not a tuning issue; canary is sacrificed and must not be tuned or
  rerun. [repo-observed]
- tasks.md V6-51/V6-52 marked complete with gate outcome; v6 change now has
  only the successor-change proposal as open work. [decision]

## 35. Nonbinary LDPC v7 Successor Ladder — All Four Routes failed_canary, Ladder Exhausted (2026-08-02..04)

- Change `formal-nonbinary-ldpc-v7-successor-ladder` freezes the ordered
  route ladder R1A -> R1B -> R2 -> R3 with one shared controller
  (`formal_ir/nonbinary_v7_ladder.py`, hash-bound advance, no confirmation
  path, exactly-once, no-rerun, gates: canary 0/4 in either stratum ->
  `failed_canary`; development ready = per-stratum >=15/16 verified + zero
  forbidden + strict replay + disclosure <=8.75 bits/symbol excluding tag +
  median <=120 s/frame). All v7 evidence lives in
  `openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/`;
  all v7 plans/packages live under fresh `workspace/nbldpc_v7_*` roots; no
  official `formal_ir_methods` v7 directory exists. [repo-observed]
- R1A (identity `nbldpc_formal_v7_r1a_mr0`): GF(1024) n=256 (2,3) PEG mother,
  m=170 (168 degree-3 + 2 degree-4 checks, seed 2026080400), flooding
  FFT-QSPA primary, max_iter 100. Engineering accepted (T0 19/T1 64/T2 11/
  T3 97). Sacrificed 4+4 canary executed once + strict-replayed once (exit 0,
  111.0 s / 108.8 s): 0/4 + 0/4 verified, 8/8 `decode_failed` -> canary gate
  fires -> `failed_canary`, frozen; 16+16 not eligible. Package at
  `workspace/nbldpc_v7_r1a_canary_af8ff2e751cf433ba74deb74bbe1deba/canary_plan`.
  [repo-observed]
- R1B (identity `nbldpc_formal_v7_r1b_mr1`): exact R1A mother under new
  identity + one multiplicative repetition (deterministic nonzero GF(1024)
  multipliers, seed 2026080401, rate 1/6 nominal), prior-combining decoder,
  same syndrome 1700 bits + tag. Engineering accepted (T0 15/T1 76/T2 17/
  T3 119). Sacrificed 4+4 canary executed once + strict-replayed once (exit 0,
  59.3 s / 59.6 s): p=.20 3/4, p=.30 0/4 -> gate fires on p=.30 ->
  `failed_canary`, frozen; 16+16 not eligible. Multiplicative repetition
  improved p=.20 but did not close the p=.30 tail. Package at
  `workspace/nbldpc_v7_r1b_canary_a209a853f5e34de69bf930deb60d5673/canary_plan`.
  [repo-observed]
- R2 (identity `nbldpc_formal_v7_r2_qsc_de`): faithful q-ary density
  evolution validated against published vectors (q=2 BSC (3,6) ~0.084;
  BEC (3,6)=0.429438, (3,4)=0.647426, (4,8)=0.383441, (4,6)=0.506132; q=4
  exhaustive checks), bounded search <=32 distributions (degrees 2..8, mean
  check degree <=12), per-stratum n=1024 PEG codebooks with 321 (p=.20) /
  458 (p=.30) checks, layered FFT-QSPA max_iter 100. One frozen-vector
  correction recorded ((3,4) mislabel). Engineering accepted (T0 32/T1 100/
  T2 24/T3 142). Sacrificed 4+4 canary executed once + strict-replayed once
  (exit 0, 1311.2 s / 1308.5 s): 0/4 + 0/4 verified, 8/8 `decode_failed` ->
  gate fires -> `failed_canary`, frozen; 16+16 not eligible. Package at
  `workspace/nbldpc_v7_r2_canary_d6c752a0772043768a1ca88a1ca63ed3/canary_plan`.
  [repo-observed]
- R3 (identity `nbldpc_formal_v7_r3_gf32x2`): reversible 10-bit -> high/low
  5-bit split (split roundtrip SHA256 `4716bf82...`), two GF(32) n=1024 codes
  m0=m1=404/558, layer-0-first with layer-1 priors ONLY from
  Bob/public/verified layer-0, joint 64-bit tag, flooding damped EMS nm=32
  (=q, the exact min-sum GF(32) update, exhaustively validated; FFT-QSPA
  oracle test-only), max_iter 100, disclosure 3.945/5.449 bits/symbol
  excluding tag. Engineering completed (2026-08-04): T0 19/T1 105/T2 33/
  T3 179, independent review 10/10 PASS
  (evidence/v7_r3_engineering_acceptance.json; schema v7_r3_engineering_v1;
  manifest_id b052a92748119b57d426fda4583d697f6577e6761e2b52332fee9f6e13c57582;
  13 reused-source hashes unchanged; check-count freeze m0=m1=ceil(1.15*H_32(p)/5*1024)).
  Sacrificed 4+4 canary staged and reviewed READY-FOR-SINGLE-EXECUTION; a
  minimal canary-only authorization edit applied (run() + CLI + 2 tests;
  post-edit hashes dd8ebe41.../68a17e92.../ad603eab...; first-half plan backed
  up, plan re-created in the same directory with 8 fresh 10303-bit seed
  records disjoint from all 10744 prior seed_ids, file SHA256
  43379354...fca2); executed once + strict-replayed once (exit 0, 668.8 s /
  663.4 s; git porcelain unchanged by replay): 0/4 + 0/4 verified, 8/8
  `decode_failed` (layer-0 failed every frame, 24 transcript events 3/frame,
  verification never invoked) -> gate fires -> `failed_canary`, frozen; 16+16
  development eligibility a separate main-thread decision, not claimed.
  Package at
  `workspace/nbldpc_v7_r3_canary_d006ec637ecb4b1e9463a7f4462eebf3/canary_plan`.
  [repo-observed]
- Process note: the Task tool intermittently returned empty results or
  cancelled/resumed sessions throughout this session (memory triage, several
  coder-fast engineering runs, reviewer-go returns); every completed stage was
  verified on disk before acceptance, and fresh-session retries succeeded for
  R1A/R1B/R2. R3 completion must resume from the existing partial state
  (resume session `ses_0391fa61bffeavVGlmfaDy7q1c` or fresh session with the
  partial-state inventory). [decision]
- Ladder closeout: V7-40 frozen ladder report (evidence/v7_ladder_report.md)
  at HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344 — first development-ready
  route NONE, `ladder_exhausted` TRUE, all four routes `failed_canary`, every
  failed artifact retained, no official v7 output root, no
  rerun/tuning/confirmation/real data/N4; no fourth route invented (R4
  proximal-ADMM never authorized). V7-41 independent acceptance PASS
  (main-thread-confirmed); V7-42 pending: stop unless a new qualification
  change is proposed. Decision-log entries for the R1A/R1B/R2/R3 canary
  non-promotions and the 2026-08-04 ladder-exhausted closeout exist.
  [decision]

## 36. Nonbinary LDPC v7 Ladder Exhausted — Durable Pattern And Stop Rule (2026-08-04)

- Every v7 route failed its sacrificed 4+4 canary (R1A 0/4+0/4; R1B p=.20 3/4,
  p=.30 0/4 tail; R2 0/4+0/4; R3 0/4+0/4) at max_iter=100, consistent with the
  v6 long-block baseline failure (0/4 both strata at max_iter=50, §34). The
  degree-2/3 PEG ensembles at these rates do not approach the needed
  correction under the frozen FFT-QSPA / EMS decoders on full-rate random
  frames; noiseless and 1-2 planted-error frames converge in 1-2 iterations,
  so this is a structural capacity gap, not a tuning issue. [decision]
- Do NOT re-run or tune any v7 route: the four canary packages are immutable
  non-ready evidence and the current rows are NOT tuning data. No fourth
  route was invented (R4 proximal-ADMM was never authorized). [decision]
- A nonbinary successor must be a NEW OpenSpec change with fresh development
  and confirmation data, new roots, and its code/rate/decoder change frozen
  before new development data. Qualification, promotion, and comparison
  eligibility claims remain unauthorized for every v7 route. [decision]
- No official `comparison_bench/outputs_comparison/formal_ir_methods/` v7
  directory exists before or after the ladder (recursive v7 scans clean);
  all v7 evidence lives under
  `openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/` and
  all canary packages under fresh `workspace/nbldpc_v7_*` roots.
  [repo-observed]

## 37. Nonbinary LDPC V8 Reference-Reproduction Correction (2026-08-04)

- New active change:
  `formal-nonbinary-ldpc-v8-reference-reproduction`. It is engineering and
  reference-only: error-domain syndrome algebra, an independent probability
  oracle, full-vector q-ary QSC Monte-Carlo density evolution, and one exactly
  sourced published reproduction. No V8 canary/development/confirmation/
  real/N4/comparison output is authorized. [decision]
- Scientific correction to §§35-36: V7 T0-T3 engineering suites passed, while
  the four scientific canaries failed. The failures reject the frozen
  implementations at their gates; they do not establish that nonbinary LDPC
  as a class has a structural capacity gap. [decision]
- R1B synthesized a second independently corrupted observation from Alice and
  combined it with Bob's observation. Preserve its package, but treat it only
  as an algorithmic diagnostic outside the project's one-Bob-observation plus
  public-disclosure reconciliation contract. [repo-observed, decision]
- R2 used a scalar two-level reliability surrogate rather than full q-entry
  message populations. Its variable update did not faithfully establish the
  paper contract of exact sampled degrees plus a channel term, and its degree
  perspective was not independently reproduced from a q-ary published target.
  Therefore R2 0/8 is evidence about that implementation, not closure of the
  literature's full-vector MC-DE route. [repo-observed, decision]
- V8 must reproduce a precisely cited q-ary QSC reference before any GF(1024)
  project adaptation. If exact degree vectors, perspective, channel convention,
  or target cannot be extracted, stop `implementation_blocked` rather than
  guessing. A future finite-length V9 requires a separate OpenSpec change and
  fresh data. [decision]

## 38. Nonbinary LDPC V8 Reference Reproduction — Implemented, Independently Accepted (2026-08-04)

- V8 reference-reproduction change implemented and INDEPENDENTLY REVIEWED
  ACCEPTED (reviewer-go, read-only, 2026-08-04) at HEAD
  a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344. Operator did not self-accept;
  V8-A01..A12 all pass (A12 satisfied by the independent review). [decision]
- Additive files only:
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py`,
  `nonbinary_v8_reference.py`, `nonbinary_v8_mcde.py` + 3 tests
  (`test_nonbinary_v8_error_domain.py`, `test_nonbinary_v8_reference.py`,
  `test_nonbinary_v8_mcde.py`) + 7 evidence files under the change's
  `evidence/` dir (v8_engineering_acceptance.json schema v8_engineering_v1,
  v8_source_manifest.json, v8_reproduction_trace.json,
  v8_literature_provenance.json, v8_muller2024_table1_extract.txt SHA256
  d343f0204e87994e64efd32531bc12490fb4e7125cd90b52cfaf2397279b57bd,
  v8_v7_interpretation_audit.md, v8_v9_recommendation.md). [repo-observed]
- Semantics: error-domain contract d = H*(x+y) with reconstruction
  x_hat = y + e_hat; independent direct probability-domain oracle (pairwise
  XOR convolution + sparse support enumeration + brute-force tiny-code
  coset/MAP; imports only GF2mField from nonbinary_field; import-boundary
  enforced — no V1-V7 FFT/FWHT/check-update/decoder calls); full-vector QSC
  Monte-Carlo density evolution (length-q messages, edge-perspective degree
  distributions with tested node/edge conversion, exact sampled degrees per
  update, fresh channel message at every variable update, direct convolution
  with no FWHT, base-q mean message entropy convergence, seeded deterministic
  populations, fail-closed normalization); golden regressions detect the old
  R2 missing-channel and fixed-dv_max behavior. [repo-observed, decision]
- Tiers (pytest -p no:cacheprovider, fresh
  `workspace/nbldpc_v8_reference_9c3f51e2a74b48d9b6c0a5f8e1d23a4b` root):
  T0 11/0, T1 31/0, T2 3/0, T3 179/0 (frozen 16-file v5+v6+v7-R1A/R1B/R2
  regression subset). Reviewer independently re-ran T0/T1/T2: identical.
  [repo-observed]
- Published reproduction (single frozen run, no rerun/tuning): Muller et al.,
  "Efficient Information Reconciliation for High-Dimensional Quantum Key
  Distribution", Quantum Inf Process 23, 195 (2024), arXiv:2307.02225v2,
  Section 3.1 Table 1 row rate 0.75: q=4, DET published 0.069, edge-view
  lambda 0.107x+0.245x^3+0.192x^6+0.034x^9+0.207x^18+0.161x^25+0.049x^27
  (Eq. 13 exponents = degree-1, so DE degrees {2,4,7,10,19,26,28});
  concentrated two-point check distribution inferred from the fixed rate
  dc_mean = 1/((1-R)*sum(lambda_d/d)) = 24.3285893 -> {24,25} (documented
  inference). Frozen params: seed 2026080418, 20000 nodes, max 200
  iterations, entropy < 0.01 base-q for 20 consecutive iterations, p in
  [0.01,0.12] step 0.0025, frozen tolerance 0.015. Result:
  threshold_proxy 0.062421875, delta 0.006578 <= 0.015 -> PASS.
  [repo-observed, decision]
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real-data/N4/comparison execution; frozen
  src/experiments/tools/results and all V1-V7 files unchanged; nothing staged.
  Engineering/reference-only boundary: V8 authorizes only a separate future
  V9 proposal (paper-faithful syndrome reconciliation with reproduced
  ensemble and blind puncturing/shortening, fresh roots); no
  FER/readiness/qualification/promotion/comparison claim. [decision]
- Process note: tasks.md V8-50.7 checkbox remains pending until this memory
  section exists; docs/decision-log.md, CURRENT_TASK.md, and AGENT_HANDOFF.md
  already updated with the same verified facts. [repo-observed]

## 42. fix-aggressive-ir-collapse FourLoss Truth Closure and Archive (2026-08-29)

- OpenSpec `fix-aggressive-ir-collapse` archived to `openspec/changes/archive/2026-08-29-fix-aggressive-ir-collapse/` (proposal/design/tasks/specs/gates_frozen.json). Diagnostic start `workspace/diag_6dB_collapse_20260828.md` (polar-aggressive-7x-recovery). [repo-observed]
- Truth closure four-loss 121x4 full (frames300/seed20260228/tag64/jobs18 leave-2): `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/loss_{6,10,16}dB` each 121 rows `polar_e2e_results.csv` + diag 121 + layer 847, `layers_success_best>0 121/121`, `k_best>0 6dB 814 / 10dB 825 / 16dB 825`; 20dB reused `results/authoritative/e2e_20dB_fullgrid_pairing_v2_candidate_t15` 121 rows. PIE max: 6dB 9.31 / 10dB 9.52 / 16dB 9.59 / 20dB 9.59, ordered 6<10<16~20. beta 0.85-0.87. Old map_ser>=0.1 FAIL 99/88/88 diagnostic only, new k>0 all PASS. [repo-observed]
- Frozen gates `gates_frozen.json vT0.5_pilot_20260828`: G_fer point0.10 (wilson_upper 0.082<0.10 with frames30/300), G_pairing max_pairs=0 (uncapped, removed coincidence_rate uniformity; auto reserved for OOM guard), G_pairing uniq>1 per bw bifurcation regress, G_growth optimum point0.10/sc/max0, G_scan<1m/file achieved 0.17m. Science params fer_threshold 0.10 / fer_rule point / decoder_modes sc (SCL no improvement). [decision]
- Bottleneck re-mark: `tools/auto_ir_scan.py` 18-point scan (bw120/150/180 x fer0.08/0.10/0.12 x rule wilson/point, Numba double-pointer shared sort+ThreadPool leave-2) measured scan_wall 10.2s (0.17m) / sort 0.31s (3%), far below budget 40m/1m; full 121 51-59m/tier -> per-point ~30s decode vs ~2s pairing, bottleneck is polar decode not pairing; Rust/layered tuning downgraded to on-demand (trigger: per-point>10s or tier>120m or sensitive>30%). [repo-observed, decision]
- Strategy lessons (durable): (1) map_ser<0.1 PASS/FAIL gate removed -- sidecar_verdict/map_ser diagnostic only, status only by k_best>0/rescue_success/layers_success_best>0 (changes export_joint_sequence_sidecar.py:1689 / run_e2e_pipeline.py:351-358 / run_real_polar_max_pie.py:_worker); high-dim high SER still yields key (specs/ir-policy + pairing-window synced). (2) max_pairs=687388 fixed truncation caused coincidence_rate uniformity across d (uniq=1 -> uniq>1 fixed). [decision]
- Archived artifacts: archive/2026-08-29-fix-aggressive-ir-collapse with proposal/design/tasks/specs/gates; results/auto_scan_v1/per_file_best.json + wall_time.json + results/paper_grade_aggressive_v1 four-loss full + .bak_20260828 distorted backup; auto dual-layer pilot 18 recorded in tools/auto_ir_scan.py + workspace/adaptive_ir_plan_merged.md. [repo-observed]
- Persistence triage (memory triage 2026-08-29 iteration 9 reviewer PASS): must persist = gates_frozen.json vT0.5, paper_grade_aggressive_v1 four-loss 121x4 full (incl 20dB reuse declaration), auto_scan_v1/per_file_best.json + wall_time.json (G_scan 0.17m audit baseline), .bak_20260828 distorted backup, tools/auto_ir_scan.py thin wrapper; must not persist = T0.5 8-group control/intermediate tables, wilson/point对照 temporary, per-file scan intermediate manifest, pilot coincidence_rate uniformity diagnostic and map_ser old gate intermediate stats (only final point0.10/max0/sc). [decision]

## 43. adaptive-pie-boost FourLoss Adaptive Mixed Delta (2026-08-29 Iteration2->3 reviewer PASS)

- OpenSpec `adaptive-pie-boost` per-file dual-layer (3x6 18 per tier) and four-loss max PIE comparison implemented as thin wrapper `tools/auto_ir_scan.py`: Numba double-pointer O(N+M)+shared sort+ThreadPool `workers=max(2,cpu-2)` leave-2-cores, no intrusion into frozen baseline `src/experiments`, guard fail-closed (pool_root contains `adaptive_v1`). [repo-observed]
- Four-loss frozen baseline max PIE points (6/10/16/20dB each 1 point, d4096,bw200) vs adaptive optimum `bw120 fer0.08 point` (T0 72 candidates unified optimum) full 121 real rerun (frames300/seed20260228/tag64/shards16, jobs18 leave-2, max_pairs0, pairing_v2, disable-scl, force-align) to `results/adaptive_v1/full_121_{6,10,16,20}dB_best/`: each 121 rows `polar_e2e_results.csv` 122 with header, PASS all, `PIE_practical>0` 119/120/120/120, `k>0` 484/484 diagnostic only (no overwrite paper_grade_v3/authoritative), G_scan 0.17m PASS. [repo-observed]
- Comparison `results/adaptive_v1/_adaptive_vs_frozen_real.csv` (mirror `openspec/changes/adaptive-pie-boost/evidence/_adaptive_vs_frozen_real.csv`) 4 rows:
  6dB 9.3116->9.3290 D+0.0174 (+0.19%) / 10dB 9.5167->9.4286 D-0.0881 (-0.93%) / 16dB 9.5918->9.5235 D-0.0683 (-0.71%) / 20dB 9.5904->9.6495 D+0.0591 (+0.62%); pilot estimate `_adaptive_vs_frozen.csv` uniform +0.045 superseded by real 121, not extrapolated. [repo-observed]
- Conclusion: per-file optimum on 4 frozen max points no stable gain, mixed 2 positive 2 negative, range -0.9% to +0.6%, mean ~ -0.02 near zero; 10/16dB negative is real phenomenon not script bug, must not be bypassed by tuning. Incremental `*_adaptive_v1` and budget `G_scan<1m/file` compliant, bottleneck remains polar decode ~30s/point vs pairing ~2s/point. [decision]
- Lightweight scan cost: `results/adaptive_v1/scan_{6,10,16,20}dB/` each 18 rows `scan_manifest.csv` total 72 candidates, `scan_wall_s~10.1s/tier sort0.3-1.06s` disclosed, `workers=4 (cpu20 leave-2)`, `--help` printable, `pytest -p no:cacheprovider --ignore=smoke_test 64 passed`. [repo-observed]
- Persistence triage (Iteration3, reviewer PASS): must persist = `_adaptive_vs_frozen_real.csv` 4 delta_real, `full_121_*_best/polar_e2e_results.csv` 484 real values, G_scan 0.17m, `auto_ir_scan.py` thin wrapper and leave-2 semantics; must not persist = 72 scan manifest row values, pilot +0.045 estimate intermediate table, per-file intermediate fer_upper sort details (only final optimum bw120 fer0.08 point and mixed conclusion). Next: memory -> /goal complete archive. [decision]

## 39. Nonbinary LDPC V8-60 Audit-Correction Close-Out (2026-08-04)

- V8-60 was a NON-TUNING FORMULA CORRECTION discovered by an independent audit
  of the accepted V8 candidate (2026-08-04); HEAD
  a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344 unchanged. Three corrections:
  (1) `concentrated_check_distribution` now solves the edge-perspective rate
  condition sum_j rho_j/j = (1-R)*sum_i lambda_i/i EXACTLY for adjacent check
  degrees {floor(dc), ceil(dc)} with w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi),
  w_hi = 1 - w_lo, target = (1-R)*integral_lambda, dc = 1/target (integer dc
  degenerates to regular); the old mean-matched weights (w_lo = dc_hi -
  dc_mean) approximated it with ~1e-4 relative error; new public helper
  `reconstructed_rate()`; tests assert |reconstructed_rate - rate| <= 1e-12
  (5 configs). (2) REPRODUCTION_CITATION first author corrected to "Ronny
  Müller" (was wrong given name "Rasmus T. Müller"); full arXiv:2307.02225v2
  author list. (3) Tolerance re-derived with valid arithmetic:
  0.0005 + 0.00125 + 0.005 + 0.005 = 0.01175 <= 0.012 (frozen tolerance 0.012);
  the old claim 0.005+0.003+0.0025=0.015 was arithmetically invalid and is NOT
  reused. [decision]
- Corrective reference run executed EXACTLY ONCE with parameters frozen before
  the run: q=4, R=0.75, Muller et al. 2024 Table 1 row 0.75 (DET published
  0.069), concentrated rho {24: 0.6623423944, 25: 0.3376576056}, n_samples
  100000 and max_iter 150 (the paper's own MC-DE budget), seed 2026080418,
  p in [0.01, 0.12] step 0.0025, entropy < 0.01 base-q for 20 consecutive
  iterations. Result: threshold_proxy 0.062421875, delta 0.006578125 <= 0.012
  -> PASS. No rerun, no tuning. [repo-observed, decision]
- History preservation: evidence/v8_reproduction_trace.json preserved
  byte-identical (SHA256
  dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3), marked as
  the pre-correction approximate trace via
  v8_reproduction_trace_precorrection_annotation.json;
  v8_engineering_acceptance.json NOT rewritten — its A12=blocked status is
  explicitly resolved by the main-thread evidence/
  v8_acceptance_closeout_addendum.json; v8_literature_provenance.json,
  v8_muller2024_table1_extract.txt, v8_v7_interpretation_audit.md,
  v8_v9_recommendation.md unchanged. [repo-observed]
- New evidence files: v8_reproduction_trace_corrected.json,
  v8_reproduction_trace_precorrection_annotation.json,
  v8_60_correction_evidence.json (formula/constants old->new, tolerance
  arithmetic, source-hash old->new), v8_independent_review_acceptance.json,
  v8_acceptance_closeout_addendum.json. v8_source_manifest.json regenerated
  with v8_60_delta; only two files changed: nonbinary_v8_mcde.py (new SHA256
  2c84a5ee76d09f4d6cea537289ff82d88ab19abd31d1a41951a7d24acdd66543) and
  test_nonbinary_v8_mcde.py
  (a508a4228ee06114424db2242b4db784bfa1b9cabcbae54f4cd7172ed988a81f).
  [repo-observed]
- Golden regressions: q=4 golden re-recorded under corrected rho {4: 1/6,
  5: 5/6} (same seed 2026080420; recording not tuning); omitted-channel/
  fixed_max tamper modes still differ (old-R2 detection preserved); q=8 golden
  byte-identical (regular {6:1.0}). [repo-observed]
- Tiers (V8-60.8 scope, NO T3 rerun): compile exit 0; T0 17/0; T1 32/0; T2 4/0
  (read-only reproduction-trace, source-manifest, no-production-runner,
  precorrection-preservation). Independent reviewer-go re-ran T1 32/0 and
  T2 4/0: identical; overall verdict ACCEPTED
  (evidence/v8_independent_review_acceptance.json), blocking findings none;
  non-blocking: v9 recommendation cites pre-correction numbers (superseded by
  corrected run), cosmetic duplicated line, pre-existing package __init__
  binding. [repo-observed, decision]
- Boundary: V8 remains engineering/reference-only; no V9, no canary/
  development/confirmation/real-data/N4, no official output, nothing
  staged/committed/pushed; only a separate future V9 OpenSpec proposal is
  authorized. [decision]

## 40. Nonbinary LDPC V9 GF(1024) Long-Block Route Frozen (2026-08-04)

- New active OpenSpec change:
  `formal-nonbinary-ldpc-v9-gf1024-long-ir`. V8-60's q=4 reproduction is a
  method/audit validation only; it is not GF(1024) threshold or finite-length
  FER evidence. [decision]
- Frozen autonomous state machine: V9A scalable full-vector GF(1024) WHT
  MC-DE and separate p=.20/.30 ensembles; robust f=1.15 conservative
  multi-seed thresholds must be >=.22/.32 before any codebook. Target f=1.08
  failure permits robust continuation only with
  `efficiency_target_not_met`. Rates/checks are computed as
  ceil(f*H_q(p)*n), with harmonic-exact edge-view rho. [decision]
- On V9A robust PASS only: V9B n=4096 irregular PEG/ACE-or-equivalent graph,
  nonzero GF(1024) labels, error-domain layered log-FFT-SPA (100-150 frozen
  iterations, workers=1), T0-T3 and independent acceptance, then one fresh
  4+4 canary and one strict replay. Gate: >=3/4 each stratum, zero forbidden,
  exact disclosure, median <=2h/superframe, peak RSS <=3GiB. [decision]
- On V9B PASS only: V9C n=16384 fresh 4+4 gate (>=3/4 each, median <=8h,
  <=3GiB), then n=32768 with exactly 32 ordered disjoint 1024-symbol synthetic
  constituents and fixed-rate syndrome/tag leakage. n=32768 uses one fresh
  4+4 canary, then on PASS one fresh 16+16
  development; ready gate >=15/16 each, zero forbidden, strict replay, median
  <=24h, <=3GiB. [decision]
- Every scientific stage is prepare -> independent read-only review -> exactly
  one execute -> exactly one strict replay. Failed evidence is immutable and
  stops the route; no tuning/rerun. V9 stops after the development decision;
  qualification/confirmation/real/N4/promotion/formal comparison require a
  separate future change. [decision]

## 41. Nonbinary V9 Freeze-Review Corrections (2026-08-04)

- V9A robust conservative multi-seed gates are >=.22/.32; target gates are
  >=.215/.32, with .215 below the p=.20 f=1.08 capacity threshold ~.21827.
  All four searches plus validation use one pre-frozen,
  independently reviewed, exactly-once deterministic execute and exactly-once
  strict replay. Target failure selects robust with
  `efficiency_target_not_met`; robust failure stops. [decision]
- All finite matrices require GF(1024) full row rank `rank(H)=m` before plan.
  n=4096/16384/32768 superframes bind respectively 4/16/32 ordered disjoint
  1024-symbol constituents with complete provenance and no cross-stage reuse.
  [decision]
- n=32768 canary has a hard 24h timeout per superframe and median <=16h advance
  gate. V9C is fixed-rate per stratum: `m=ceil(f*H_q(p)*n)`, syndrome leakage
  `L_recon=10*m`, separate fixed 64-bit tag, `L_total=10*m+64`; these are hard
  caps and no shortened/index/other reconciliation payload is allowed. Blind
  adaptation is prohibited in V9 and deferred to a future V10. [decision]
