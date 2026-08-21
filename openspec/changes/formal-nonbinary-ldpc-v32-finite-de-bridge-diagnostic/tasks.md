# Tasks: formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic

> Do NOT mark any task complete without evidence (command output, file hash, log line, or reviewer report). Checkbox format. P1 is planner-only spec freeze; implementation starts only after main accepts the freeze (P1.4).

## Allowed New Files

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py` — harness CLI (arms B0–B5, ledger, resume, terminal reconstruction)
- `comparison_bench/tests/test_nonbinary_v32_finite_de_bridge.py` — T0/T1/T2/T3 test suite
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/*` — formal run evidence (`RUN_MANIFEST.json`, `resource_ledger.json`, `progress.json`, `per_block.jsonl`, arm summaries, `terminal_reconstruction.json`, `operator_handoff.json`, `candidate_recount.json`, `candidate_terminal.json`)
- `workspace/nbldpc_v32_finite_de_bridge/OPERATOR_HANDOFF.md` — candidate-only handoff
- `workspace/<v32>/<uuid>/*` — fresh test roots (pytest basetemp)

Any other new file requires explicit main approval.

## Forbidden (MUST NOT be edited/executed/created at any stage)

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/**` (canonical V31, byte-identical, read-only)
- All OpenSpec archives: `openspec/changes/archive/**`
- Frozen baseline: `src/**`, `experiments/**`, `tools/**`
- `results/**`
- Raw `.ttbin` files (never read by V32 code or agents)
- Anything `n=2048`: blocks, configs, outputs
- Any output root other than the single new `nbldpc_v32_finite_de_bridge/run_01/`; no overwrite; no automatic `run_02`
- During the formal run phase (P4): edits to `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`, final report, archive actions, promotion documents
- Qualification/promotion statements in any V32 artifact

## Frozen Constants (identical across proposal/design/spec/tasks — do not restate differently)

- Goal text: see `proposal.md §Goal` (verbatim quote).
- Bindings: V31 n=1024 QC packet / validation blocks+frames / per-block baseline (`nbldpc_v31_20260820/run_01/`); V25 run_04 empirical channel; V26 run_02 F03/A02 allocation; V28R decoder interface; GF(32) `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`; `m1=16`; sources `type2_1M_20260121_184040` / `type2_1p5M_20260121_183806` / `type2_2M_20260121_183657`.
- Arms: B0 6 blocks (6/6 exact/tag/syndrome, 0 false accept); B1 60 (seeds 1M 320101–320120, 1.5M 320201–320220, 2M 320301–320320); B2 60 (= B1 blocks, only oracle L1 → Bob-only sequential); B3 60 (deterministic permutation of EXACTLY the B4 block set: blocks 0–19/source, marginals preserved, rule+seed pre-frozen); B4 60 (blocks 0–19/source); B5 read-only import of 300 records (no decoder invocation).
- Discriminator: arm pass = ≥19/20 block successes/source; block success = `exact && tag && syndrome && !false_accept`. Development only.
- Terminals (exactly 9): `bridge_binding_fail`, `finite_graph_decoder_mismatch`, `l1_sequential_propagation_limit`, `real_error_structure_mismatch`, `empirical_channel_model_mismatch`, `bridge_pass_ready_for_successor`, `bridge_inconclusive`, `resource_blocked`, `implementation_blocked`. Truth table: `design.md §5`; uncovered combos → `bridge_inconclusive`.
- Run rules: unique root `run_01` (exists ⇒ STOP collision, no auto `run_02`); 12h cumulative wall-clock persisted in `resource_ledger.json` (resume never resets); persist `progress.json` + `per_block.jsonl` after every completed block; execution order binding → B5 → B0 → B1 → B2 → B3 → B4 → terminal reconstruction; early-stop whitelist ONLY: binding failure / B0 failure / implementation exception / output collision / 12h exhausted / canonical-input drift / truth-use violation. Never skip B2/B3/B4 due to bad B1 results, single-source failure, trends, or time saving.

## Testing Tiers (frozen)

All tests: fresh `workspace/<v32>/<uuid>/` root + `pytest -p no:cacheprovider --basetemp <root>`; never touch legacy ACL temp dirs; never implicitly invoke production decoder/pipeline (fake runner passed explicitly).

- **T0 structural**: compile/import; GF(32)/field binding; fixed QC packet identity; B0 tiny noiseless; B1/B2 same-block identity; B3 deterministic permutation; B5 no decoder invocation; output collision refusal; no production execution from tests.
- **T1 tamper (≥14)**: seed drift; block ID drift; graph packet drift; posterior binding drift; B1/B2 block mismatch; truth leakage into B2/B3; duplicate block; resource meter reset; illegal resume; terminal tamper; source label tamper; partial JSONL; B5 re-executing decoder; output overwrite.
- **T2 fake qualification**: full fake B0–B5 (explicit fake runner); ≥1 fixture per major terminal; truth-use audit; exact resume; 12h resource simulation; independent terminal reconstruction.
- **T3 read-only regression**: V25 binding; V26 allocation; V28R decoder interface; V31 QC packet; V31 B5 import consistency; canonical/frozen directories unmodified.

T2 runs at milestone P2R; T3 runs at milestone P5. No production DE/decoder in any tier.

## Role Isolation (frozen)

- **Planner**: owns P1 (spec authorship + consistency self-check). Does not implement.
- **coder-fast**: owns P2/P2R (harness + tests + fake evidence). Must not mark ACCEPT, must not redefine requirements.
- **reviewer-go**: owns two INDEPENDENT review rounds — R1 in P3 (candidate, pre-run) and R2 in P5 (post-run evidence/terminal verification). Must not edit files; findings only. Must not be the implementer or the execution agent.
- **execution agent**: owns P4 (formal run_01 operation, monitoring, whitelisted stops/resume). MUST NOT serve as the final scientific reviewer (R2).
- **operator closeout agent**: owns P5 handoff assembly (candidate-only).
- **Main (orchestrator/user)**: owns freeze acceptance (P1.4), run authorization (P3.4), final ACCEPT/REJECT, and any decision outside the autonomy boundary.

## Autonomy Boundary (frozen — STOP and report on trigger)

Implementation/execution MAY autonomously decide: internal function/file structure; minimal data structures; fixture organization; CLI parameter details; JSON field layout (within design §3 required fields); progress display; exact-resume implementation details; Windows writable basetemp; ordinary bug fixes inside frozen scope; T0–T3 test split; internal agent division of labor.

STOP-and-report triggers (never autonomous): modifying B0–B5; changing seeds/block IDs; changing the 19/20 discriminator; expanding samples; adding n=2048; extending 12h; new matrix/new decoder; re-estimating posterior; automatic `run_02`; rerunning failed blocks; changing terminals based on results; starting V33/NB-Polar; writing qualification/promotion; push; reading raw `.ttbin`; overwriting existing evidence.

---

### P1 — Specification Freeze (planner)

- [x] P1.1 Create the four files: `proposal.md`, `design.md`, `tasks.md`, `specs/formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic/spec.md`. — Evidence: reviewer S8, change dir contains exactly 4 files.
- [x] P1.2 Self-check four-file consistency: verbatim goal text present in proposal; identical arms/seeds/discriminator/terminal set/Allowed/Forbidden across all four; truth table covers all reasonable B0–B5 combinations with uncovered → `bridge_inconclusive`. — Evidence: planner self-check + reviewer S2/S3/S4 all PASS.
- [x] P1.3 Verify no forbidden item appears as allowed; no production code written; no runs executed. — Evidence: reviewer S6/S7 PASS (no v32 files, no run root, grep clean).
- [x] P1.4 Main ACCEPTS the specification freeze (2026-08-22). Rulings recorded: (a) B3 uses oracle L1; (b) posterior-anomaly criteria pre-registered in RUN_MANIFEST before B3/B4; (c) gate-layer mapping drift→`bridge_binding_fail`, truth-violation→`implementation_blocked`, collision→pre-execution STOP; (d) B0 seeds = deterministic constants recorded pre-execution; (e) "B2 显著低于 B1" operationalized as B2 FAIL while B1 PASS under the frozen discriminator; (f) B3 permutes EXACTLY the B4 block set (blocks 0–19/source). Independent spec-freeze review: reviewer-go 9/9 PASS, verdict ACCEPT. Implementation (P2) is now authorized.
- **Evidence**: file listing of the change directory; grep counts (`SHALL` in spec.md, terminal names, seed ranges) identical across files.
- **Done when**: main reviews and accepts the freeze (P1.4 recorded by main).

### P2 — Harness Implementation + T0/T1 (coder-fast)

- [ ] P2.1 Implement `run_nonbinary_v32_finite_de_bridge.py` per design: stage-0 binding verification (9 bindings incl. field_id/m1=16/sources); B5 read-only import (no decoder call); B0–B4 arms with frozen seeds/blocks; per-block JSONL persistence immediately on completion; `resource_ledger.json` cumulative 12h meter; `progress.json`; exact resume; fixed execution order; early-stop whitelist; terminal reconstruction via design §5 truth table.
- [ ] P2.2 Implement `test_nonbinary_v32_finite_de_bridge.py` covering all T0 items and all ≥14 T1 items (fake runners explicit; workspace basetemp).
- [ ] P2.3 Static checks: no `.ttbin` path in V32 sources; B5 code path grep-clean of decoder entry points; no writes outside the run root in code paths.
- **Evidence**: `py_compile` exit 0; `pytest -k t0` and `-k t1` logs (all PASS); grep outputs empty; `git status` shows only allowed new files.
- **Done when**: T0 + T1 fully PASS with no canonical drift.

### P2R — Fake Evidence + T2 (coder-fast)

- [ ] P2R.1 Build fake fixtures for a complete fake B0–B5 run (explicit fake runner) under `workspace/<v32>/<uuid>/`; include ≥1 fixture per major terminal (each attribution terminal, `bridge_pass_ready_for_successor`, `bridge_inconclusive`, `resource_blocked`, `implementation_blocked`, `bridge_binding_fail`).
- [ ] P2R.2 Pass T2: truth-use audit; exact-resume replay (completed blocks not repeated, meter continues); 12h resource simulation; independent terminal reconstruction from persisted JSONL reproduces the classified terminal in every fixture.
- [ ] P2R.3 Assemble candidate manifest (file list + hashes + command log); deliver delta-only report.
- **Evidence**: T2 pytest log; fixture tree listing; candidate manifest.
- **Done when**: T2 PASS and candidate delivered to main.

### P3 — Candidate Review Round 1 (reviewer-go, independent)

- [ ] P3.1 reviewer-go (not the implementer) re-runs T0/T1/T2 read-only in a fresh workspace root; verifies static checks and that no canonical/frozen path was touched.
- [ ] P3.2 reviewer-go publishes findings (PASS/FAIL per tier, per frozen constant) without editing files.
- [ ] P3.3 Main decides run authorization: confirm run root absent, budget/scope unchanged, no STOP-trigger fired.
- **Evidence**: reviewer report; `git diff` empty on all Forbidden paths; main authorization note.
- **Done when**: R1 PASS + main authorizes P4.

### P4 — Formal run_01 (execution agent)

- [ ] P4.1 Execute in fixed order: binding verification → B5 import → B0 → B1 → B2 → B3 → B4 → terminal reconstruction. Persist after every block.
- [ ] P4.2 Enforce whitelist-only stops/resume: record reason in `resource_ledger.json`; never reset the meter; never repeat completed blocks; never resume from a scientific terminal; treat duplicate block as evidence-inconsistent STOP.
- [ ] P4.3 On any STOP trigger or anomaly (e.g., B0 fail, drift, truth-use violation): halt, preserve evidence immutably, report blocker with failing command/error — do not fix silently mid-run.
- [ ] P4.4 Produce `terminal_reconstruction.json` strictly via design §5; write nothing outside the run root; no edits to decision-log/memory/report/archive during this phase.
- **Evidence**: `progress.json` complete; `per_block.jsonl` line count = 246 decoded blocks (+B5 import record); `resource_ledger.json` cumulative ≤ 12h; `RUN_MANIFEST.json` identities match the 9 bindings.
- **Done when**: all arms executed or a whitelisted stop occurred with immutable evidence retained.

### P5 — Operator Closeout + Review Round 2 (operator closeout agent; reviewer-go independent)

- [ ] P5.1 Operator assembles candidate-only handoff: `workspace/nbldpc_v32_finite_de_bridge/OPERATOR_HANDOFF.md` and/or `operator_handoff.json`, `candidate_recount.json`, `candidate_terminal.json` under the run root — each marked `candidate_only=true, main_acceptance_pending=true, qualification=false, promotion=false`.
- [ ] P5.2 reviewer-go R2 (independent of implementer AND execution agent): independently recount per-block outcomes from `per_block.jsonl`, recompute arm pass/fail via the frozen discriminator, re-derive the terminal via design §5, and verify it equals `candidate_terminal.json`; run T3 read-only regression (V25/V26/V28R/V31 bindings intact; canonical directories unmodified).
- [ ] P5.3 Main performs final ACCEPT/REJECT of the diagnostic attribution; only main may end `main_acceptance_pending`. Memory triage and any decision-log entry happen AFTER main acceptance, never during P4.
- **Evidence**: R2 report with recomputed counts vs candidate; T3 pytest log; handoff artifact listing with flags.
- **Done when**: R2 verdict published and main records the final decision.

---

**Do not mark tasks complete without evidence. Each checkbox requires a cited command output, file hash, log line, or reviewer report.**
