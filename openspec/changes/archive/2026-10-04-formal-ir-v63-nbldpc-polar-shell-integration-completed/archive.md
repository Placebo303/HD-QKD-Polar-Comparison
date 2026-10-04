# Archive disposition: formal-ir-v63-nbldpc-polar-shell-integration

- Date: 2026-10-04
- Disposition: completed
- Evidence state: implementation_independently_reviewed; production_execution_not_authorized
- Source evidence: docs/research_cycles/V63P0/REVIEW_VERDICT.md:L1-L55 is an independent implementation review covering R63-01..R63-04, fake adapter, guards, and tests; DELIVERY.md:L1-L20,L94-L98 records implementation complete and EXECUTE_NOT_AUTHORIZED.
- Known review/execution state: Independent read-only implementation review PASS; report records 12 fake/unit tests PASS (historical record, not rerun here). Review explicitly says no real decoder, formal PA, or 90-block execution; EXECUTE_NOT_AUTHORIZED remains.
- Frozen merge boundary: Implementation-only R63-01..R63-04: 32*u1+u2 full-symbol exact mapping; frozen IRRunResult with ShellResult wrapper; smoke/fresh registries and zero-overlap guard; DOMAIN_CALIBRATION_REQUIRED guard. Also reviewed fail-closed loader, disclosure accounting, decoder-call accounting, and fake-runner wiring. Exclude real decoder, formal PA, 90-block execution, run_01, qualification, and promotion.
- Next action from frozen table: Archive the reviewed implementation clauses only; keep all production execution and qualification requirements unmerged.
- Ambiguity or unknown retained: Spec lifecycle text remains plan/spike oriented while later REVIEW_VERDICT and DELIVERY document production implementation. This disposition is limited to reviewed implementation, not a result or scientific acceptance.
- Exact-title merge outcome is recorded during phase B; this phase-A record preserves the frozen scope only and grants no new execution, qualification, or route acceptance.

## Original tracked files
- openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/design.md
- openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/proposal.md
- openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/specs/spec.md
- openspec/changes/formal-ir-v63-nbldpc-polar-shell-integration/tasks.md

## Phase-B delta disposition

Title-level consolidation is recorded in `openspec/changes/reboot-repository-organization-20261004/S6_DELTA_MERGE.tsv` under change key `formal-ir-v63-nbldpc-polar-shell-integration`. Included titles: 0; remaining listed titles are omitted or already equivalent, with the specific reason retained in that ledger. This resolves the earlier pending-merge filing snapshot; current AGENTS and reboot R1–R9 govern. Filing/consolidation confers no new scientific acceptance or execution authorization.
