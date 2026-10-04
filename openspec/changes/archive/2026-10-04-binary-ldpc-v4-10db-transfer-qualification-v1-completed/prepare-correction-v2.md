# Frozen Prepare Correction v2

## Incident

The sole v1 production prepare created exactly `pre_run_plan.json` and
`real_data_lock.json`, but main-thread review rejected it before execute.
Post-write `_validate()` called `_prior_sets()`, which rediscovered the
current plan as a prior real plan and therefore reported collision with its
own roots. No decoder ran and no 10 dB outcome was observed.

The directory
`20260729_v1_binary_ldpc_v4_10db_transfer` is immutable
`invalid_pre_execute`. Do not delete, overwrite, modify, execute, or treat it
as qualification evidence.

## Allowed correction

Create new v2 runner/verifier modules and focused v2 tests. Preserve all v1
source files and the invalid v1 directory byte-for-byte.

- **C2-01 Identity:** use run/plan/run-manifest/report identities ending `_v2`
  and a fresh additive `20260729_v2_binary_ldpc_v4_10db_transfer` production
  root.
- **C2-02 Self exclusion:** prior-plan discovery accepts an exact current plan
  content SHA exclusion. Post-prepare validation excludes only that plan.
- **C2-03 Failed-plan isolation:** the invalid v1 plan remains a bound prior
  plan; all three v1 roots and 384 v1 seed IDs remain forbidden to v2.
- **C2-04 Other isolation:** retain synthetic, v3, development, 16 dB, and all
  other real/transfer root/seed isolation.
- **C2-05 Lifecycle:** v2 prepare must validate strictly after files exist.
  Tests and the operator must not run production prepare or execute.
- **C2-06 No semantic change:** source selection, method, matrices, channel,
  backend, caps, statuses, artifacts, denominators, and 126/128 gate remain
  exact.

## Acceptance

- **C2-T0:** compile/import and exact v2 identities.
- **C2-T1:** fake prepare followed by strict validation succeeds; removing
  self exclusion fails; excluding any plan other than exact current SHA
  fails; v1 root and seed collisions fail.
- **C2-T2:** complete fake package and deep tamper/read-only tests pass under
  v2.
- **C2-T3:** v1 10 dB, v2 10 dB, 16 dB, corrected synthetic, development
  package, codebook/channel/formal, and formal-real regressions pass; v1
  production directory hashes are unchanged; v2 production root is absent.

Operator return conditions remain complete candidate or concrete blocker.
Only the main thread may accept and run v2 production.

