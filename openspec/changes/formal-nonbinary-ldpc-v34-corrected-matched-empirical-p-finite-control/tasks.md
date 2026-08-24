# Tasks: V34 corrected matched empirical-P finite control

> **Status: DRAFT_PENDING_FR1 / IMPLEMENTATION_NOT_AUTHORIZED**

## Allowed before freeze

- Read-only inspection of bound code, documents, and evidence.
- Edits confined to this OpenSpec change packet.
- Independent literature, data-semantics, lifecycle, and FR1 reviews.

## Forbidden before freeze

- Production/test implementation, decoder calls, empirical block generation,
  official output creation, smoke execution, tuning, or benchmarks.
- Writes to V25/V28R/V31/V32/V33 roots, `src/`, `experiments/`, `tools/`,
  `results/`, sibling checkout, or raw data.
- Run_02, retry/resume, extra seeds, threshold selection from observed V34
  results, qualification/promotion claims, or automatic V35 work.

## Review IDs

- **FR1**: independent specification-freeze review.
- **IR1**: independent implementation-candidate review.
- **ER1**: independent post-execution read-only evidence review.

## Stages

- [x] P0 Evidence audit: identify exact V25 empirical counts, V31 packet,
  V28R decoder chain, V32 oracle path/schedule/discriminator, historical seeds,
  and unresolved choices.
- [x] P1 Draft proposal/design/spec/tasks with candidate constants and explicit
  claim/lifecycle boundaries.
- [ ] P2 FR1 independently resolves all `design.md` section 7 decisions and
  returns findings. Main thread either revises or records `ACCEPT_FREEZE`.
- [ ] P3 After freeze only: implement the smallest CLI and focused T0/T1 tests
  using explicit fake-runner injection and fresh workspace roots.
- [ ] P4 Milestone fake T2 strict replay/exact-once/tamper checks, then IR1 on
  the exact candidate. Stop at
  `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`.
- [ ] P5 Only after a new user `EXECUTE_AUTH`: preflight frozen HEAD and matrix,
  execute exactly 60 blocks once, then stop decoder activity.
- [ ] P6 ER1 independently reconstructs bindings, ordinals, success counts,
  tags/syndromes, terminal, protected-root status, and claim boundary.
- [ ] P7 Main-thread scientific acceptance or rejection, durable documentation,
  and archive. No successor is implied.

## Current stop condition

After FR1, stop unless the main thread explicitly records `ACCEPT_FREEZE`.
Nothing in the V33 execution authorization carries forward to V34.

