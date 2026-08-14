# OpenCode Autonomous Packet — V9A through V9C

## Operator Role

You are the implementation operator for OpenSpec change
`formal-nonbinary-ldpc-v9-gf1024-long-ir`. Requirements, formulas, gates,
scope, and stop rules are frozen. Do not reinterpret or weaken them and do not
mark your own work accepted.

Read completely, in order:

1. `AGENTS.md`
2. `AGENT_PROJECT_MEMORY.md` sections 37-40
3. this change's `proposal.md`, `design.md`, `specs/spec.md`, `tasks.md`
4. V8 proposal/design/tasks and corrected V8 evidence:
   `v8_reproduction_trace_corrected.json`,
   `v8_60_correction_evidence.json`,
   `v8_independent_review_acceptance.json`, and
   `v8_acceptance_closeout_addendum.json`
5. `docs/nonbinary-ldpc-v9-plan.md`

Use exact paths or narrowly scoped text search. Do not use Glob or broad
recursive enumeration.

## Authority

You are authorized to implement and autonomously advance V9A -> V9B -> V9C,
including the bounded synthetic canaries and V9C development expressly listed
in `tasks.md`. No separate user confirmation is needed after a gate passes.
Every gate is mandatory: if a robust/canary/development gate fails, freeze the
package, complete the close-out evidence, and stop. Never tune or rerun failed
scientific data.

You are not authorized to run or create qualification, confirmation, real
data, N4, promotion, or formal comparison. Do not write a V9 official output
under `comparison_bench/outputs_comparison/formal_ir_methods/`.

## File and Process Rules

- Add V9 code/tests/CLI/evidence only in the comparison layer and this change.
- Do not modify V1-V8 source or evidence, or frozen `src/`, `experiments/`,
  `tools/`, `results/`, or existing output packages.
- Preserve unrelated dirty-worktree changes. Inspect by explicit task manifest.
- Do not install dependencies, clone/vendor/copy repositories, or access
  private data.
- Do not stage, commit, push, reset, clean, or delete user files.
- At most two agents total. Give any reviewer a read-only role.
- Scientific execution is workers=1. Tests must pass an explicit fake runner
  and cannot invoke a production decoder by default.
- Use fresh additive `workspace/<stage>/<uuid>` test roots with
  `pytest -p no:cacheprovider`; use different roots for scientific packages.
- Record PID/cell ID for long runs. Own and terminate only V9 processes.
- Enforce peak process-tree RSS <=3 GiB. Do not evade caps by spawning helpers.

## Frozen Execution State Machine

### State A0 — freeze

Complete V9-00. Record HEAD, file manifest, source hashes, frozen directories,
all prior identities, and no-V9-official-output proof. Freeze deterministic
fresh roots/seed derivation for every potentially reachable phase before the
first scientific result. Prove non-overlap dynamically against all prior
evidence and exclude the current plan during replay checks.

For every n>1024 package, freeze constituent superframes: n=4096 has 4,
n=16384 has 16, and n=32768 has 32 ordered, mutually disjoint 1024-symbol
constituents. Bind IDs/order/roots/seeds/hashes/aggregate mapping and prohibit
reuse across V9 stages. Freeze the rule `rank(H)=m` for every GF(1024) matrix;
rank failure requires bounded reconstruction before plan or a blocker.

### State A1 — scalable kernel

Implement V9-10. Full length-q messages are mandatory. WHT coefficient
permutations must be verified against the V8 direct oracle at q=4/8/32 and
bounded q=1024. Freeze numerical tolerances before tests. Fail closed.

### State A2 — ensemble search

Implement V9-20 for both p strata and f tiers. Compute, never hard-code:

```text
H_q(p) = (h2(p) + p*log2(q-1))/log2(q)
m = ceil(f*H_q(p)*n)
```

Before any result, create one plan-only package freezing all four candidate
searches, search budgets, disjoint optimization/validation seeds, targets,
degree bounds, objectives, and gate reconstruction. Obtain independent
read-only review. Then execute the whole four-search plus multi-seed validation
package deterministically exactly once and strict-replay exactly once. Use at
least three validation seeds and the minimum threshold for each gate. Require
harmonic-exact edge-view rate reconstruction <=1e-12. Failed evidence is
immutable: no tuning or rerun.

Independent reviewer gate:

- robust p=.20 threshold >=.22; and
- robust p=.30 threshold >=.32.

Apply target conservative gates p=.20 >=.215 and p=.30 >=.32. The .215 gate
retains margin below the f=1.08 p=.20 capacity threshold (~.21827). A target failure records
`efficiency_target_not_met` for that stratum and permits robust-only downstream
work. If either robust gate fails, write evidence and STOP before codebooks.

### State B1 — n=4096 engineering

Only after robust A2 PASS, complete V9-30 and T0-T3. The graph must come from
the accepted stratum/tier ensemble, have no parallel edges, recorded rank and
PEG/ACE-or-equivalent diagnostics, deterministic construction, and independently
seeded nonzero GF(1024) labels, and satisfy `rank(H)=m` before plan. Every
superframe binds 4 ordered disjoint 1024-symbol constituents with full
provenance and cross-stage no-reuse. Decoder: error-domain layered log-FFT-SPA,
workers=1, frozen 100-150 iterations, complete syndrome checks, no truth or
fallback. Obtain independent engineering ACCEPT before a canary plan.

### State B2 — n=4096 canary

Complete V9-40: fresh 4+4 at p=.20/.30, prepare -> independent read-only review
-> execute exactly once -> strict replay exactly once. Advance only if both
strata are >=3/4 verified, forbidden=0, disclosure reconstructs exactly,
median runtime <=2h/superframe, and peak RSS <=3GiB. Otherwise freeze STOP.

### State C1 — n=16384 bridge

Only after B2 PASS, complete V9-50 engineering/review and a fresh 4+4 lifecycle.
Advance only if each stratum is >=3/4 verified, forbidden=0, exact disclosure,
median <=8h/superframe, peak RSS <=3GiB. Otherwise freeze STOP.
Every superframe binds 16 ordered disjoint constituents with full provenance;
the matrix must satisfy `rank(H)=m` before plan.

### State C2 — n=32768 engineering and canary

Only after C1 PASS, complete V9-60. Each superframe has exactly 32 ordered,
disjoint 1024-symbol synthetic constituents with complete identities, hashes,
order, roots, seeds, and aggregate mapping. Use f=1.08 per stratum only if its
V9A target gate passed; otherwise f=1.15 and label
`efficiency_target_not_met`.

Use one fixed rate per stratum. If its target gate passed, use f=1.08;
otherwise use f=1.15 and `efficiency_target_not_met`. Freeze
`m=ceil(f*H_q(p)*n)`, syndrome `L_recon=10*m` bits, separate fixed 64-bit tag,
and `L_total=10*m+64`; those values are exact hard caps. V9 must reject any
puncturing, shortening, interactive/adaptive stage, information-bearing index/
control, or other reconciliation payload. Blind rate adaptation is deferred
to V10 and must not be implemented in V9.

Complete T0-T3 and independent engineering review, then one fresh 4+4
prepare/review/execute/replay lifecycle. Require `rank(H)=m`.

Continue only at >=3/4 verified per stratum, zero forbidden, exact disclosure,
median runtime <=16h, hard timeout 24h per superframe, and <=3GiB RSS.
Otherwise freeze STOP.

### State C3 — n=32768 development

Only after C2 PASS, complete V9-70 with fresh disjoint 16+16 development.
Prepare, independently review, execute once, and strict-replay once. Record
development-ready only at >=15/16 verified per stratum, forbidden=0, exact
hash/replay/disclosure reconstruction, median <=24h/superframe, and <=3GiB RSS.
Obtain an independent final V9-A01..A16 review. Then STOP regardless of verdict.
Do not create the next lifecycle phase.

## Evidence and Tests

Use T0 compile/import/structure/tiny math; T1 focused kernel/oracle/graph/
decoder/invalid/numerical/disclosure; T2 complete fake lifecycle, strict replay,
and layered tamper; T3 V8 plus selected frozen V5-V7 regression. Run T2/T3 at
milestones, not after every small edit.

Evidence must bind commands, exit codes, counts, hashes, HEAD, allowed files,
plans, roots/seeds, codebooks, transcripts, public payload, disclosure ledger,
gate reconstruction, runtimes, process-tree peak RSS, and output-absence checks.
Tamper coverage includes raw bytes, recomputed local self-hashes, recomputed
manifest links, deep source/transcript/public-payload/leakage/gate changes, and
constituent-superframe mapping.

## Reporting

Return only one of:

1. `COMPLETE`: all tasks reachable through the first mandatory STOP point are
   complete, with changed files, commands/results, evidence paths, independent
   verdict, every gate result, output-absence check, and exact next authority;
2. `CONCRETE_BLOCKER`: exact failing command/error, attempted safe remedies,
   changed files and preserved artifacts, current gate, and the single
   decision needed.

“In progress”, partial task narration, or a request for routine stage approval
is not a return condition.
