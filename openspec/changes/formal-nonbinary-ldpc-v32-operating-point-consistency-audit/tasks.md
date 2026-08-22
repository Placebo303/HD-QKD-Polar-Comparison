# Tasks: formal-nonbinary-ldpc-v32-operating-point-consistency-audit

> Do NOT mark any task complete without evidence (command output, file hash, log line, or reviewer report). Checkbox format. P1 is planner-only spec freeze; implementation starts only after main accepts the freeze (P1.4).

## Allowed New Files

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_operating_point_audit.py` — single audit CLI (subcommands d0/d1/d2/d3/all; `--runner` injection mode for test fakes)
- `comparison_bench/tests/test_nonbinary_v32_operating_point_audit.py` — T0/T1/T2 test suite
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/*` — audit reports (`audit_manifest.json`, `d0_signature.json/md`, `d1_consistency.json/md`, `d2_feasibility.json/md`, `d3_v26_evidence.json/md`, `final_branch_decision.json`)
- `workspace/<audit>/<uuid>/*` — fresh test roots (pytest basetemp)
- `workspace/nbldpc_v32_operating_point_audit/OPERATOR_HANDOFF.md` — candidate-only handoff

Any other new file requires explicit main approval.

## Forbidden (MUST NOT be edited/executed/created at any stage)

- DE 重跑 / 任何新 DE 采样；decoder 调用；读取 `.ttbin`
- Canonical/frozen 写入：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/**`（V32 run_01 只读保护）；V31/V30R/V28R/V26/V25 根目录；OpenSpec archives
- Frozen baseline: `src/**`, `experiments/**`, `tools/**`; `results/**`
- Anything `n=2048`: blocks, configs, outputs
- Any output root other than the single new `nbldpc_v32_operating_point_audit/run_01/`; no overwrite; no automatic `run_02`
- `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`; V32 归档动作；qualification/promotion 措辞
- 启动 V33、NB-Polar、corrected-B1（审计后继变更）

## Frozen Constants (identical across proposal/design/spec/tasks — do not restate differently)

- Goal text: see `proposal.md §Goal` (verbatim quote).
- Bindings: V32 run_01 evidence (`per_block.jsonl` 247 lines + RUN_MANIFEST + summary_B0..B5); V25 run_04 (`channel_counts.npz` keys `{sid}_N_ab_train_N_ab_train` — verbatim on-disk key with duplicated suffix; `channel_summary.json` raw_ser 1M `0.239779296875` / 1p5M `0.2544695292735815` / 2M `0.2557409550754458`; `split_manifest.json`); V26 run_02 artifacts (`gate.json` status `pass_target_f13`, best_passing_f A01=1.6/A02=1.3); V31 run_01 (RUN_MANIFEST `configs["1024"].sources[].{H.L1,H.L2,m1=16,m2∈{184,190,192},m_total,leak_total_bits∈{1064,1094,1104},f_total}`; matrix_audits L1 shape [16,1024]; m1_registry per-layer rate/H); code facts: harness `synth_channel_sample` L555–564, V26 sampler semantics L10–13.
- Semantic corrections (normative): truth_symbol_rank = `(centered > p_true[:,None]).sum(axis=1)` (not a normalized rank; ≈0 ⇒ true symbol rank 1–2 of 32); B2 `l2_errors_final=1024` = not_run sentinel, excluded from trajectory analysis; divergence applies to B1 only; B3/B4 improve-but-no-syndrome.
- D0 predicates: P-i B1 all-60 active divergence (final > initial, anomaly true); P-ii B2 all-60 sentinel with `terminal_decoder_status=="not_run"`; P-iii B3/B4 improvement without syndrome/exact.
- Branch table (exactly A/B/C/inconclusive): A total infeasible → LDPC 与 Polar 同速率方案均暂停，先重审泄漏预算/运行点; B total feasible 且 L2 allocation infeasible → 当前 multilevel allocation 失败，NB-Polar feasibility 价值上升，不值得先换 QC 图; C layer 与 total 均可行 → corrected matched control 值得一次（后续单独变更）; uncovered/ambiguous → inconclusive with reasons.
- Manifest freeze before computation: thresholds (derivation basis anchored to log2(1024)=10 bits/symbol), MC seeds/sample sizes, histogram bin edges, margin method = simple gap reporting at n=1024 only.
- Run rules: unique root `run_01` (exists ⇒ STOP collision, no auto `run_02`); execution order manifest freeze → d0 → d1 → d2 → d3 → final_branch_decision; all inputs read-only.

## Testing Tiers (frozen)

All tests: fresh `workspace/<audit>/<uuid>/` root + `pytest -p no:cacheprovider --basetemp <root>`; never touch legacy ACL temp dirs; never implicitly invoke production decoder/DE/pipeline (fake runner passed explicitly).

- **T0 structural/tiny math**: compile/import; Q_B1 toy construction (mass conservation, b≠a support); sentinel recognition on synthetic B2 record; branch-table totality; collision refusal; static checks (no decoder entry points / no DE sampling calls / no `.ttbin` in audit source; tests do no production execution).
- **T1 tamper (≥12)**: input drift rejection (bindings 1–4); missing input file; truncated JSONL; duplicate block_uid; arm-label tamper; sentinel mishandling detection; threshold tamper vs frozen manifest; MC seed/sample-size drift; histogram-bin drift; output-root collision; branch-table tamper; out-of-root write rejection.
- **T2 fake qualification**: full fake fixture flow via `--runner` injection covering d0→d3→branch decision; independent recomputation reproduces every persisted headline number; `new_DE_change_required=true` path exercised; collision path exercised end-to-end.

No T3 tier exists for this change (nothing canonical may be executed or regenerated; input integrity is asserted via fixtures and the formal-run stage-0 binding check). T2 runs at milestone P2R.

## Role Isolation (frozen)

- **Planner**: owns P1 (spec authorship + consistency self-check). Does not implement.
- **coder-fast**: owns P2/P2R (audit CLI + tests + fake evidence). Must not mark ACCEPT, must not redefine requirements.
- **reviewer-go**: owns two INDEPENDENT review rounds — R1 in P3 (candidate, pre-execution) and R2 in P5 (post-execution report verification). Must not edit files; findings only. Must not be the implementer or the execution agent.
- **execution agent**: owns P4 (single formal `all` execution under the frozen manifest). MUST NOT serve as the final scientific reviewer (R2).
- **operator closeout agent**: owns P5 handoff assembly (candidate-only).
- **Main (orchestrator/user)**: owns freeze acceptance (P1.4), execution authorization (P3.4), final ACCEPT/REJECT of the audit reports and branch, and any decision outside the autonomy boundary. All ACCEPT gates held by main.

## Autonomy Boundary (frozen — STOP and report on trigger)

Implementation/execution MAY autonomously decide: internal function/file structure; minimal data structures; fixture organization; CLI parameter details; JSON field layout within spec SHALL-O1 content; test split T0–T2; Windows writable basetemp; ordinary bug fixes inside frozen scope; internal agent division of labor.

STOP-and-report triggers (never autonomous): changing D0–D3 definitions, predicates P-i..P-iii, thresholds, or the branch table; touching canonical/frozen paths; running any DE or decoder; reading `.ttbin`; creating `run_02`; editing decision-log/memory; qualification/promotion wording; starting V33/NB-Polar/corrected-B1; push; overwriting existing evidence.

---

### P1 — Specification Freeze (planner)

- [x] P1.1 Create the four files: `proposal.md`, `design.md`, `tasks.md`, `specs/formal-nonbinary-ldpc-v32-operating-point-consistency-audit/spec.md`. — Evidence: reviewer A12, change dir contains exactly 4 files.
- [x] P1.2 Self-check four-file consistency: verbatim goal text present in proposal; identical Allowed/Forbidden lists, D0–D3 definitions, predicates P-i..P-iii, semantic corrections, branch table, output-file set, and collision rule across all four files. — Evidence: planner self-check table + reviewer A2/A3/A5/A7 PASS.
- [x] P1.3 Verify no forbidden item appears as allowed; no production code written; no analysis executed; V32/V25/V26/V31 artifacts untouched. — Evidence: reviewer A9/A10 PASS (no audit script/tests/output root exist).
- [x] P1.4 Main ACCEPTS the specification freeze (2026-08-22, after one REJECT→fix cycle). Blocking defect fixed: `channel_counts.npz` binding key corrected to verbatim on-disk `{sid}_N_ab_train_N_ab_train` in proposal/design/tasks/SHALL-D1a (reviewer A8 FAIL item); non-blocking gaps closed (design §9 STOP list + n=2048; handoff flags tuple restated in design §9). Post-fix consistency re-check by main: grep shows 4/4 occurrences consistent, zero stale. Reviewer verdict otherwise ACCEPT-grade (A1–A7, A9–A12 PASS). Implementation (P2) authorized.
- **Done when**: main reviews and accepts the freeze.

### P2 — Audit CLI Implementation + T0/T1 (coder-fast)

- [x] P2.1 Implement `run_nonbinary_v32_operating_point_audit.py` per design §3–§8: stage-0 binding verification (bindings 1–7) recorded into `audit_manifest.json`; manifest freeze (thresholds w/ log2(1024)=10 derivation basis, MC seeds/sizes, histogram bins, margin method) BEFORE any computation; subcommands d0/d1/d2/d3/all; sentinel handling per semantic corrections; leakage fields quoted verbatim with citations; gap-only margins; branch mapping incl. inconclusive path; `new_DE_change_required` output; run-root collision STOP. — Evidence: `py_compile` exit 0; stage-0 verifies verbatim npz keys `{sid}_N_ab_train_N_ab_train`, frozen raw_ser three-source values, V26 gate identity, V31 m1/m2/leak_total_bits/L1-shape/registry fields, code-fact markers at harness L555–564 and sampler L10–13; `audit_manifest.json` sealed by `freeze_digest` over the frozen section (thresholds K=3 with stated derivation, support-miss 0.01 with n=1024 derivation, MC seed 20260822/n=100000/zero-hit policy, delta+log2 bin edges, margin method string); distinct exit codes 0/2/3/4/5/6; B2 excluded from trajectory histograms; leakage quoted verbatim AND pure-syndrome `(m1+m2)·5` recomputed separately; gap-only margins; branch A/B/C/inconclusive mechanical map.
- [x] P2.2 Implement `test_nonbinary_v32_operating_point_audit.py` covering all T0 items and all ≥12 T1 items (fake runners explicit; workspace basetemp). — Evidence: `python -m pytest ... -k t0 -q -p no:cacheprovider --basetemp workspace/opaudit_final_*/t0` → `6 passed`; `-k t1 ... /t1` → `16 passed` (missing input; truncated JSONL; duplicate block_uid; arm-label tamper; 4× parametrized input drift bindings 1–4; threshold tamper; MC seed drift; histogram-bin drift; margin-method tamper; branch-table tamper; out-of-root write rejection; output-root collision end-to-end; sentinel mishandling detection).
- [x] P2.3 Static checks: no decoder entry points, no DE sampling calls, no `.ttbin` path anywhere in the audit source; no writes outside the run root in code paths. — Evidence: Select-String zero hits for `ttbin|Decoder\(|decode_block|decode_frame|finite_graph_decoder|run_decoder|mcde|synth_channel_sample\(`; AST import whitelist = stdlib+numpy only and forbidden-call scan enforced by `test_t0_static_checks_no_production_execution` (also asserts tests import only the audit module and call `cli_main` solely via the `--runner`-guarded helper); all writes funnel through `_safe_path` containment guard (`EXIT_WRITE=6`).
- **Evidence**: `py_compile` exit 0; T0+T1 pytest logs all PASS; grep outputs empty; `git status` shows only allowed new files.
- **Done when**: T0 + T1 fully PASS with no canonical drift. — Confirmed 2026-08-22: T0 6 passed / T1 16 passed / full suite 25 passed.

### P2R — Fake Fixtures + T2 (coder-fast)

- [x] P2R.1 Build fake fixtures (synthetic per_block-like records incl. a sentinel B2 record; tiny synthetic channel_counts) under `workspace/<audit>/<uuid>/`; exercise every subcommand through `--runner` injection. — Evidence: fixture builder produces 247-record JSONL (B5=1/B0=6/B1..B4=60, B2 sentinel `l2_errors_final=1024`+`not_run`), deterministic 1024×1024 diag+±1 channel_counts.npz with verbatim keys, V25 summary with frozen ser values, V26 gate/manifest/screen/confirm/m0/m1, V31 manifest/matrix_audits/m1_registry built from an independent entropy implementation, code-fact snippets placed at exact cited line numbers; all served via `test_...:make_fake_runner`.
- [x] P2R.2 Pass T2: full fake flow d0→d3→branch; independent recomputation reproduces persisted headline numbers exactly; `new_DE_change_required=true` fixture; collision fixture end-to-end. — Evidence: `-k t2 ... /t2` → `3 passed`: SHALL-O1 exact file set + execution-order assertions; independent recomputation of d0 counts/aggregates/predicates, d1 Q-mass-on-P-zero + E_V25[NLL|own posterior]=H(U|B) identity vs independent entropies, d2 gaps/leakage quotes/feasibility; branch C from frozen table; d3 ruling + minimal DE questions; second `all` → EXIT_COLLISION with byte-identical root snapshot.
- [x] P2R.3 Assemble candidate manifest (file list + hashes + command log); deliver delta-only report. — Evidence: `workspace/nbldpc_v32_operating_point_audit/CANDIDATE_MANIFEST_P2.md` written with SHA256 of both source files, pytest command log lines, static-check results, and fixture→coverage mapping; delta-only report returned to main.
- **Evidence**: T2 pytest log; fixture tree listing; candidate manifest.
- **Done when**: T2 PASS and candidate delivered to main. — Confirmed 2026-08-22.

### P3 — Candidate Review Round 1 (reviewer-go, independent)

- [ ] P3.1 reviewer-go (not the implementer) re-runs T0/T1/T2 read-only in a fresh workspace root; verifies static checks and that no canonical/frozen path was touched.
- [ ] P3.2 reviewer-go publishes findings (PASS/FAIL per tier, per frozen constant) without editing files.
- [ ] P3.3 Main decides execution authorization: confirm run root absent, manifest-freeze mechanism intact, no STOP-trigger fired.
- **Done when**: R1 PASS + main authorizes P4.

### P4 — Formal Execution Once (execution agent)

- [ ] P4.1 Execute `all` once against the real bindings in fixed order (manifest freeze → d0 → d1 → d2 → d3 → final_branch_decision), writing only under the audit run root.
- [ ] P4.2 On binding mismatch, predicate violation requiring judgment, or anomaly: halt, preserve evidence immutably, report blocker with failing command/error — do not fix silently mid-run.
- [ ] P4.3 No edits to decision-log/memory/report/archive during this phase; V32 run_01 remains byte-identical.
- **Evidence**: run-root file listing matches SHALL-O1; stage-0 binding identities logged; input hashes unchanged pre/post.
- **Done when**: all four report pairs + `final_branch_decision.json` produced, or a whitelisted stop occurred with immutable evidence retained.

### P5 — Operator Closeout + Review Round 2 (operator closeout agent; reviewer-go independent)

- [ ] P5.1 Operator assembles candidate-only handoff (`workspace/nbldpc_v32_operating_point_audit/OPERATOR_HANDOFF.md`), marked `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false`.
- [ ] P5.2 reviewer-go R2 (independent of implementer AND execution agent): independently recomputes D0–D3 headline numbers from the bound inputs, verifies they equal the persisted reports, re-derives the branch from the frozen table, and confirms inputs remain byte-identical.
- [ ] P5.3 Main performs final ACCEPT/REJECT of the audit conclusions and branch decision; only main may end `main_acceptance_pending`. Memory triage and any decision-log entry happen AFTER main acceptance, never during P4.
- **Evidence**: R2 report with recomputed values vs persisted; handoff artifact flags.
- **Done when**: R2 verdict published and main records the final decision.

---

**Do not mark tasks complete without evidence. Each checkbox requires a cited command output, file hash, log line, or reviewer report.**
