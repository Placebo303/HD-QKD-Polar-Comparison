# Archive record: NB-LDPC L1-degree2 Stage-2 synthetic batch runner

Archived: 2026-09-30
Disposition: completed (implemented, executed, reviewed — delta merged into
`openspec/specs/synth-batch-runner/spec.md`)

Change `add-nbldpc-l1d2-synth-batch-runner`, track DECIDE, branch
`formal-ir-v72p1-addendum-clean`. T8 Pre-RESULT PASS, T9 ACCEPTED; T10
main-thread acceptance granted → this archiving.

## Implementation files (unchanged by this archive task)

- `comparison_bench/src/comparison_bench/cli/nbldpc_l1d2_synth_batch.py`
- `comparison_bench/src/comparison_bench/cli/nbldpc_l1d2_synth_batch_prod.py`
- `comparison_bench/src/comparison_bench/formal_ir/nbldpc_l1d2_production_decode.py`
- 4 test files (33 passed total per frozen tasks.md):
  `comparison_bench/tests/test_nbldpc_l1d2_synth_batch.py` (18),
  `comparison_bench/tests/test_nbldpc_l1_degree2_seeds.py` (4),
  `comparison_bench/tests/test_nbldpc_l1_degree2_layout.py` (7),
  `comparison_bench/tests/test_nbldpc_l1_degree2_driver.py` (4).

## Execution result pointers

- Cycle dir `docs/research_cycles/NBLDPC-L1D2-SYNTH-BATCH/`:
  `PREREG_AND_AUTH.md` / `RESULT.md` / `INDEPENDENT_ACCEPTANCE.md`.
- n128 out-root `workspace/nbldpc-l1d2-s2c-n128-b07b0f91` (executed).
- COND-3 NOT MET (Δ=+1, 2/6 graphs Δ_g>0) → n256 NOT entered.
- Claim ceiling: no FER/SKR/qualification/promotion/publication conclusion;
  only whether a next packet is worth drafting.
- n256 out-root `workspace/nbldpc-l1d2-s2c-n256-5b2240a0` NOT executed;
  n256 entry still requires COND-3 plus a separate authorization.

## Retained verbatim in this directory

- proposal.md
- design.md
- tasks.md (T1–T10 checked complete, T10 dated 2026-09-30)
- specs/synth-batch-runner/spec.md (frozen delta; live copy merged to
  `openspec/specs/synth-batch-runner/spec.md` with only a provenance note
  prepended — SHALL/MUST/SHALL NOT text unchanged)
