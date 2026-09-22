# D14N Calibrated L1/L2 Discriminator — Implementation Readiness R1

## 1. Identity and authorization boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d14n-calibrated-l1-l2-discriminator`
- Work type: implementation-only; future scientific batch track `EXPLORE`.
- Authority: accepted D14-FINAL plus
  `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`.
- This packet authorizes implementation, fake-only tests, PROFILE_ONLY, a
  read-only verifier, scoped local commits, and independent readiness review.
- It authorizes zero production/scientific decoder calls and does not authorize
  the frozen 288-call batch, D7-H, real data, or push.

## 2. Frozen scientific contract

Transcribe the preregistration exactly; do not reinterpret it:

- n=128 only; L1 m=110; L045 control and L055 challenger;
- L2 DV3 m=104, E=384, check allocation `3^32+4^72`;
- six paired L1/L2 graph seeds `2026093401..06` /
  `2026093501..06`; twelve block seeds `2026093601..12`;
- 72 calls each for L045, L055, L2 APP and L2 ORACLE; exactly 288 planned;
- candidate concentration-backoff prior only; GF32/poly37; row-layered cold
  decoder max_iter=90, damping=1.0; every non-oracle transfer requires
  `CHECK_UPDATED`; oracle is diagnostic and never gates;
- exact/syndrome/source/target/joint/undetected remain separate;
- preserve the six frozen routing terminals and priority order verbatim;
- budgets ≤288 decoder calls, ≤26 setup, ≤1800 s wall, ≤120 s/call,
  RSS <2 GiB, one process, CPU-only, no retry/resume/repair/seed search/tuning;
- future root `workspace/v72p2d14_discriminator/20260914_r1` remains absent.

Any ambiguity or mismatch with the accepted preregistration is a STOP for main
thread adjudication, not permission to edit thresholds or inputs.

## 3. N201–N210 implementation tasks

- **N201 OpenSpec first**: proposal, design, tasks, and delta spec. Explicitly
  list reused D11/D12/D14 helpers and rejected duplication.
- **N202 plan and identities**: deterministic 288-record plan built before any
  decoder binding or Model-F load; exact seed/profile/arm equality checks.
- **N203 construction reuse**: import the accepted connectivity-first graph,
  admission, coefficient, sampling, and prior helpers. One construction path
  per frozen arm family; do not copy decoder or GF32 kernels.
- **N204 dispatch**: share each paired block and graph identity across four
  arms; L2 APP consumes only CHECK_UPDATED L1 beliefs; L2 ORACLE uses true-L1
  conditioning and is marked `ORACLE`/ungraded.
- **N205 gates**: implement the six terminals and exact priority from prereg
  §7. L045 discordances are descriptive only. Unit-test every boundary and
  priority collision.
- **N206 CLI**: add
  `scripts/v72p2d14_discriminator_development.py` with `--profile-only`,
  `--n14-batch`, `--execution-authorized`, and `--verify`. Default-false batch
  refusal must occur before output creation, decoder binding, or Model-F load.
- **N207 evidence**: fresh never-overwrite six-file root matching the prereg;
  minimal manifest, graph records, decoder records, arm summary, summary, and
  command log. Do not add hashes, transactional writes, retry frameworks, or
  production-style infrastructure.
- **N208 verifier**: read-only fail-closed recomputation of identity set,
  admissions, calls, metric isolation, provenance, gates, terminal, and
  budgets. Missing/partial/mismatched roots fail nonzero.
- **N209 focused tests/profile**: fake-runner tests for plan, sharing,
  provenance refusal, oracle exclusion, all gates, no-write authorization,
  writer and verifier. PROFILE_ONLY constructs all 12 graphs, proves A1–A6,
  emits exact mixed-degree counts and the 288 plan, with zero decoder calls and
  no future-root write.
- **N210 independent readiness review**: actual artifact access; independently
  recompute graph counts/admission, plan identities, gate boundaries, reuse,
  refusal ordering, root absence, budgets, and zero production calls.

## 4. Verification proportionality

- T0: `py_compile` new module, runner and tests.
- T1: new focused suite plus only directly reused D11/D12 focused suites, using
  a fresh `workspace/` basetemp and `-p no:cacheprovider`.
- Do not rerun historical broad suites without a concrete focused conflict.
- Run PROFILE_ONLY and live unauthorized refusal; run no production batch.
- Reviewer-go evidence is accepted when `EVIDENCE_ACCESS: VERIFIED`, tests are
  named, and no blocking inconsistency exists; main thread does not duplicate it.

## 5. Group5 and commit discipline

The prior group5 STOP is non-blocking. If the D14/D13 entries in
`AGENT_PROJECT_MEMORY.md` and `docs/decision-log.md` can be selected by complete
content headers without including unrelated hunks, commit only those explicit
sections with the D14 implementation/docs group. Otherwise leave both files
uncommitted and report them as excluded. Never use `git add .`, `git add -A`,
bulk line-ending normalization, reset, clean, stash, or partial-hunk guessing.

After independent PASS, a scoped local commit of the new OpenSpec/code/tests/
cycle docs is permitted. No push and no branch switch.

## 6. Readiness record and return

Create a compact readiness record and append to the existing D14 exploration
log. Return only:

`D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION`

when N201–N210 pass, the exact future command is frozen, authorization remains
false, the result root is absent, and decoder/scientific calls are 0. Include:

- changed/reused files and duplication rejection;
- exact realized degree tables and 12-graph admission summary;
- plan/call/setup/budget equality and exact future command;
- tests, PROFILE_ONLY, refusal evidence and independent verdict;
- commit/exclusion/no-push state and all findings.

On blocker, return raw evidence and the single decision needed. Do not create an
execution prompt or self-authorize the batch; the main thread supplies the
paired A1 execution packet after accepting readiness.
