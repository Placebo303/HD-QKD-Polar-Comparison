# Proposal — NB-LDPC L1-degree2 Stage-2 synthetic batch runner

- Change: `add-nbldpc-l1d2-synth-batch-runner`
- Cycle: `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT` R2 (Stage-2 synthetic batch only)
- Track: **DECIDE** (Model-F bundle derived from the real-session CAL fit
  session=20260123_1M_600k_0dB, CAL 702-1725). Three-document form
  `PREREG_AND_AUTH.md` / `RESULT.md` / `INDEPENDENT_ACCEPTANCE.md` +
  Pre-EXECUTE + independent Pre-RESULT + main-thread acceptance.
- Authority (read first, frozen):
  `docs/research_cycles/NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md`
  (§4 P4, §7 scale/budget),
  `docs/research_cycles/NBLDPC-L1D2-SYNTH-BATCH/PREREG_AND_AUTH.md`,
  `AGENTS.md` §1.2/§5/§6/§10.3,
  Stage-1 `openspec/changes/add-nbldpc-l1-degree2-layout/` (read-only format
  reference; this change modifies nothing under it).
- Branch: `formal-ir-v72p1-addendum-clean` (ordinary non-force push only;
  never merge `polar-mainline`; Polar baseline frozen; Joint MARGINAL, P3/P4,
  D7-H retained).

## Goal

Freeze the Stage-2 synthetic batch contract for the accepted Stage-1
L1-degree2 construction bundle: one thin batch runner invocation per width,
6 graphs x 2 data seeds x 8 frames = 96 paired samples per width, dual-arm
(control C / candidate S, `oracle=False` hardcoded both arms), with frozen
seeds, prior chain, decoder档, counting semantics, output schema, budget caps,
canary rule, and the COND-3 continuation gate. No new scientific mechanism is
introduced here.

## Approval ≠ execution authorization

**This change / this packet approval is NOT execution authorization.**
P4: the new L055 is outside the `P4_FEAS_PACKET.md` F2(n=2048)/F3/F4 scope
but is bound by the §4 procedural gate of
`NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md` → a new authorization
covering the concrete scope (DEC-1) is required before any execution.

## Non-Goals (hard prohibitions)

- No execution is granted by this change (no `--execute` without DEC-1).
- No change to any existing file, in particular nothing under
  `openspec/changes/add-nbldpc-l1-degree2-layout/`, and no change to
  `AGENTS.md` / `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md`.
- No writes to `results/` or `comparison_bench/outputs_comparison/`;
  single fresh `workspace/` out-root per width; existing roots refuse.
- No FER/SKR/qualification/promotion/publication conclusion; claim ceiling:
  only whether a next packet is worth drafting.
- No bare `G6b / C3 / D1` identifiers (confusable with D16 `D-01..D-10`);
  use the named IDs **GAP-6b / COND-3 / DEC-1**.
- The runner and the layout are unaffected by this documentation task
  (docs landing only; zero code change).

## Impact scope

- ADDED (exact file manifest):
  `openspec/changes/add-nbldpc-l1d2-synth-batch-runner/` (`proposal.md`,
  `design.md`, `tasks.md`, `specs/synth-batch-runner/spec.md`);
  `docs/research_cycles/NBLDPC-L1D2-SYNTH-BATCH/PREREG_AND_AUTH.md`.
- READ-ONLY: everything listed under Authority above; the already-implemented
  `comparison_bench/src/comparison_bench/cli/nbldpc_l1d2_synth_batch.py`
  and `comparison_bench/src/comparison_bench/formal_ir/nbldpc_l1_degree2_layout.py`
  (evidence cited in `tasks.md`, not modified).
- FORBIDDEN: everything listed under Non-Goals.
