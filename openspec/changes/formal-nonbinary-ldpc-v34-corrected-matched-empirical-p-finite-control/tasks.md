# Tasks: V34 corrected matched empirical-P finite control

> **Status: FR1_ACCEPTED_SCIENCE_AMENDMENTS_PENDING / IMPLEMENTATION_NOT_AUTHORIZED**

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
- [x] P2 Initial FR1 returned `REJECT_FREEZE`: exact RNG call, fixed 19/20
  threshold, failure taxonomy, V31-vs-V28R matrix binding, probability precheck,
  evidence fields and protected roots required revision.
- [x] P2R Independent FR1 re-review returned `ACCEPT_FREEZE`; every original
  `design.md` section 8 item was accepted.
- [ ] P2S Independent science-amendment re-review: mechanical-not-statistical
  19/20 language, bounded-sample claim, max_iter comparability, channel-law-only
  intervention, and NumPy 2.4.0 sampler identity.
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

After science-amendment re-review, stop unless the main thread explicitly records
`ACCEPT_FREEZE`.
Nothing in the V33 execution authorization carries forward to V34.
