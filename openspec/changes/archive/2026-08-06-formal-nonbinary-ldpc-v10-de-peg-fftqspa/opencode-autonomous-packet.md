# OpenCode Autonomous Packet — V10 DE-PEG-FFTQSPA

## Operator Role

You are the implementation operator for OpenSpec change
`formal-nonbinary-ldpc-v10-de-peg-fftqspa`. Requirements, formulas, gates,
scope, and stop rules are frozen. Do not reinterpret or weaken them and do not
mark your own work accepted.

Read completely, in order:

1. `AGENTS.md`
2. `AGENT_PROJECT_MEMORY.md` (all sections, especially V8/V9 entries)
3. This change's `proposal.md`, `design.md`, `specs/spec.md`, `tasks.md`
4. V8-60 corrected evidence:
   `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_reproduction_trace_corrected.json`,
   `v8_60_correction_evidence.json`,
   `v8_independent_review_acceptance.json`
5. V9 evidence (for seed disjointness and gate reference):
   `openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/v9a_plan_v2.json`,
   `v9a_execute_results.json`,
   `v9a_gate_decision.json`,
   `v9a_independent_review_acceptance.json`

Use exact paths or narrowly scoped text search. Do not use Glob or broad
recursive enumeration.

## Authority

You are authorized to implement and autonomously advance through the V10 state
machine: V10-00 → V10-05 → V10-10 → V10-0 → V10-20 → V10-30 → V10-40 →
V10-50 → V10-60 → V10-70. Every gate is mandatory: if a reference/ensemble/
canary/development gate fails, freeze the package, complete close-out evidence,
and stop. Never tune or rerun failed scientific data.

You are not authorized to run or create qualification, confirmation, real
data, N4, promotion, or formal comparison. Do not write a V10 official output
under `comparison_bench/outputs_comparison/formal_ir_methods/`.

## File and Process Rules

- Add V10 code/tests/CLI/evidence only in the comparison layer and this change.
- Allowed additive modules (design §15):
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_common.py`
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_de.py`
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_peg.py`
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_fftqspa.py`
- Allowed additive tests:
  `comparison_bench/tests/test_nonbinary_v10_common.py`
  `comparison_bench/tests/test_nonbinary_v10_de.py`
  `comparison_bench/tests/test_nonbinary_v10_peg.py`
  `comparison_bench/tests/test_nonbinary_v10_fftqspa.py`
- Evidence files under this change's `evidence/`.
- V8 modules (`nonbinary_v8_mcde`, `nonbinary_v8_reference`, `nonbinary_v8_error_domain`):
  test-only imports; production code must not import them.
- V9 modules: NOT imported by V10 production code (none explicitly allowed).
- Do not modify V1–V9 source or evidence, or frozen `src/`, `experiments/`,
  `tools/`, `results/`, or existing output packages.
- Preserve unrelated dirty-worktree changes. Inspect by explicit task manifest.
- Do not install dependencies, clone/vendor/copy repositories, or access
  private data.
- Do not stage, commit, push, reset, clean, or delete user files.
- At most two agents total. Give any reviewer a read-only role.
- Scientific execution is workers=1. Tests must pass an explicit fake runner
  and cannot invoke a production decoder by default.
- Use fresh additive `workspace/<v10-stage>/<uuid>` test roots with
  `pytest -p no:cacheprovider`; use different roots for scientific packages.
- Record PID/cell ID for long runs. Own and terminate only V10 processes.
- Enforce peak process-tree RSS ≤ 3 GiB. Do not evade caps by spawning helpers.

## Frozen Execution State Machine

### State S00 — freeze

Complete V10-00. Record HEAD, file manifest, frozen directories, all prior
identities. Freeze deterministic fresh roots/seed derivation: V10 prefix
`202610xx`. Prove non-overlap numerically: V8 prefix `20260804xx`, V9 prefix
`20260901xx`; `202610 > 202609` → disjoint ranges. Write
`evidence/v10_freeze_acceptance.json` and
`evidence/v10_literature_crosswalk.md`.

### State S05 — microbenchmark

Complete V10-05. Run ONE deterministic q=1024 microbenchmark with small
population, few generations, non-scientific seed. Measure wall-clock per
evaluation. Label output `engineering_only_non_scientific`. Do not produce
threshold/winner/gate claims. Do not use S1–S4 formal roots.

### State S10 — kernel engineering

Complete V10-10. Implement all four V10 modules + tests. Run T0 and T1.
Freeze `pre_run_plan.json` per design §5.2 with exact budgets, caps, paths.
Obtain independent review. Hard caps: screen ≤ 600, refinement ≤ 12,
RSS ≤ 3 GiB, workers=1. Budget must not change after formal results.

### State S00_ref — q=4 reference gate

Complete V10-0. Optimize Müller q=4 R=0.75 without injecting published lambda.
Optimization seed ≠ 2026080418 and ≠ all V9 seeds. Validate on ≥2 independent
seeds. Gate: |threshold − 0.069| ≤ 0.012, rate error ≤ 1e-12, replay identical.

**PASS** → advance to S20. **FAIL** → freeze evidence, STOP (`failed_reference`).

### State S20 — V10A ensemble search

Complete V10-20. Four searches S1–S4, each with frozen budget from pre_run_plan.
One package: plan → review → execute once → strict replay once (direct byte
comparison, no SHA-256). Gate per proposal:

```text
if S1 < .22 or S3 < .32:
    STOP (failed_ensemble)
elif S2 < .215 or S4 < .32:
    robust_only (f=1.15 lane only)
else:
    target_ready (f=1.08 lane, f=1.15 frozen backup)
```

Do not pick "closest to gate" from a failed search.

**STOP** → close-out. **robust_only or target_ready** → advance to S30.

**Current status (2026-08-06): failed_ensemble.** S1=0.2153 < 0.22, S2=0.1984
< 0.215, S3=0.3166 < 0.32, S4 zero eligible. Advance immediately to S70.

### State S30 — PEG codebook

Complete V10-30. Only after V10A gate pass. Build deterministic irregular PEG
n=4096 codebook from V10A winner lambda + concentrated rho. Verify: no parallel
edges, rank(H)=m, socket equality, degree sequences, syndrome round-trip,
manifest complete. Trial cap exhausted → frozen failure, STOP.

**PASS** → advance to S40.

### State S40 — FFT-QSPA decoder

Complete V10-40. Implement error-domain log-domain FFT-QSPA. Validate against
V8 oracle at q=4/q=8/GF(1024) small acyclic graphs. Verify: no Alice truth,
coefficient permutation correct, syndrome shift, fail-closed NaN/Inf, flooding
only (no layered).

**PASS** → advance to S50.

### State S50 — canary

Complete V10-50. T0–T3 milestone + independent engineering ACCEPT → prepare
4+4 n=4096 canary plan → review → execute once → strict replay once.

Gate: both strata ≥ 3/4 verified, zero forbidden, exact leakage, RSS ≤ 3 GiB,
runtime ≤ frozen cap.

**PASS** → advance to S60. **FAIL** → STOP (`failed_canary`).

### State S60 — development

Complete V10-60. Only after canary pass. Prepare 16+16 development plan with
fresh roots (zero overlap). Review → execute once → strict replay once.

Gate: both strata ≥ 15/16 verified, zero forbidden, RSS ≤ 3 GiB, median
runtime ≤ frozen cap.

**PASS** → `development_ready_not_qualified`, STOP. **FAIL** → `development_not_ready`, STOP.

### State S70 — close-out

Complete V10-70. Write final state (failed_ensemble), gate decision evidence
(no hash fields), independent final review, memory triage, decision log update.
Verify frozen baseline via git baseline (`git status --porcelain` +
`git diff --name-only`). Do not create any follow-up phase.

## Evidence and Tests

Use T0 compile/import/structure/tiny math; T1 focused kernel/oracle/graph/
decoder/invalid/numerical/disclosure; T2 complete fake lifecycle plus strict
replay and layered tamper; T3 frozen V8/V9 regression (git baseline) plus
no-output check. Run T2/T3 at milestones, not after every small edit.

Evidence must bind commands, exit codes, counts, git HEAD, allowed files,
plans, roots/seeds, codebooks, transcripts, public payload, leakage ledger,
gate reconstruction, runtimes, process-tree peak RSS, and output-absence checks.
**No SHA-256 hash fields** in new evidence files. Completed evidence files
(V10-0, V10-00, V10-05, pre_run_plan) are immutable and preserved as-is.

Tamper coverage: raw byte drift (direct comparison), semantic JSON tamper
(gate reconstruction disagreement, leakage accounting recomputation failure,
winner reconstruction mismatch), plan-binding field validation rejection,
seed separation verification, fake promotion detection via gate reconstruction.
No SHA-256 self-hash, source-hash, or manifest-hash fields in new code.

Do NOT simulate failure — use real malformed inputs in test-only paths.

## Reporting

Return only one of:

1. `COMPLETE`: all reachable tasks through the first mandatory STOP point are
   complete, with changed files, commands/results, evidence paths, independent
   verdict, every gate result, output-absence check, and exact next authority.
2. `CONCRETE_BLOCKER`: exact failing command/error, attempted safe remedies,
   changed files and preserved artifacts, current gate, and the single
   decision needed.

"In progress", partial task narration, or a request for routine stage approval
is not a return condition.
