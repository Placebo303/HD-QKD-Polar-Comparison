# D7 root-cause and route-reset R1 — proposal

> Status: `IMPLEMENTATION_IN_PROGRESS / EXECUTION_NOT_AUTHORIZED`.
> Single authority: `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`
> (R1). This change records the Phase A–F implementation contract only. It
> authorizes no production decoder, CAL/VAL, G1, multi-graph, G2, or D7-H
> execution, no result solidification, no push, and no scientific promotion.

## What

Remove the unresolved experimental-design and evidence problems that make
further D7-H execution premature, without altering historical evidence:

1. establish whether the historical G1 and current D7 transfer paths are
   mathematically equivalent when given the same graph, block, priors, and
   decoder outputs;
2. make provenance and per-layer outcomes observable instead of inferring
   them from joint counters;
3. measure graph-seed sensitivity with a small pre-registered multi-graph
   diagnostic;
4. restore G2 as the frozen n=256 length discriminator, or explicitly
   supersede it only through an accepted scientific decision;
5. add a bounded strong-reference/feasibility diagnostic without calling it
   an information-theoretic proof;
6. supersede over-strong single-graph terminal wording without altering
   historical artifacts;
7. implement the existing lightweight exploratory workflow instead of adding
   another ceremony framework.

## Why

- Historical G1 and current D7 used different block seeds and do not expose
  identical metrics. Their numerical difference is an unresolved consistency
  question, not a logical contradiction.
- D7-C/D/E/F used one graph pair. Their terminal labels are pre-registered
  classifications for that graph, not general mechanism facts.
- G2 remains the accepted-plan n=256 length discriminator until an explicit
  accepted plan supersedes it.
- The D7-F paired table is candidate-only 0, reference-only 2, both 0,
  neither 14 at f=1.2; the terminal name is not statistical confirmation.

## Authoritative corrections carried forward (packet §4)

- Do NOT encode the unsupported hypothesis that historical G1 used `None`
  beliefs or silently fell back to a uniform L2 prior. The old wrapper
  converted `result.final_beliefs` to an array, and the old row-layered
  decoder updated beliefs during its 90 iterations.
- In current code, provenance is checked before the `bel1 is None` branch;
  missing provenance fails closed rather than silently using a uniform
  transfer.
- D7-C/D/E/F terminal labels are single-graph pre-registered classifications
  only.
- The D7-F f=1.2 paired table (candidate-only 0 / reference-only 2 / both 0 /
  neither 14) is exact paired evidence for one graph; the weak evidential
  status is recorded, and the terminal name is not treated as statistical
  confirmation.
- G2 stays the accepted-plan n=256 length discriminator. P0's 485-second
  projection is not a reliable G2 runtime estimate; the runtime status is
  `G2_RUNTIME_UNVERIFIED` until measured/scaled probes are explicitly
  authorized.

## Evidence retention (A02)

Historical artifacts are retained byte-identical. This change adds no edit
under `results/`, `comparison_bench/outputs_comparison/`, historical
`workspace/` roots, or historical G1/D7 manifests, summaries, tables,
reports, or authorization records. All corrections are additive or
superseding documentation; no historical file is rewritten, renamed, or
relabelled.

## Claim ceiling (packet §3)

Allowed claims after implementation/tests only:

- implementation candidate;
- same-input transfer-path equivalence or a concrete localized mismatch;
- runner/test readiness;
- frozen exploratory and G2 commands awaiting authorization.

Forbidden without separately authorized execution and independent result
review: G1 validity; a particular graph/four-cycle/decoder/direction/block
length/information margin as failure cause; D7-F reverse-order regression as
a mechanism fact; G2 pass/fail; FER, leakage, efficiency, SKR,
qualification, route death, or promotion.

## Corrections and status entries

- D7-F corrigendum: `D7_F_REVERSE_ORDER_REGRESSION` remains a historical
  machine label but is not an immutable general mechanism fact. The accepted
  interpretation is single-graph, n=16 paired evidence with exact discordant
  counts and an exact-test p-value. See
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/D7_F_CORRIGENDUM_R1.md`.
- G2 status: pending, not failed, not skipped, not superseded. See
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_STATUS_NOTE_R1.md` and
  `cycle_state.yaml`.
- OQ2 four-state G2 vocabulary is preserved:
  `G2_SYNTHETIC_QUALIFIED / G2_INCONCLUSIVE /
  G2_CURRENT_CONFIGURATION_FAILED / IMPLEMENTATION_OR_NUMERICAL_BLOCKED`;
  no unconditional `ROUTE_DEAD` wording is revived.

## Scope

In scope (packet §5 allowlist): this change folder, one new narrowly named
formal-IR consistency/multi-graph module, one new narrowly named CLI under
`scripts/`, focused tests under `comparison_bench/tests/`, the cycle folder
`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/`, a narrow decision-log
entry, additive schema/probe work in
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
and G2-readiness tests.

Out of scope: frozen `src/`, `experiments/`, historical `tools/`, sibling
repositories, raw data, VAL/CAL decoding, production decoder execution, G1
rerun, multi-graph execution, G2 execution, D7-H execution, result
solidification, push, and any edit to historical evidence.

## Dormant execution phases (packet §8)

X1 consistency probe (read-only), X2 multi-graph exploratory batch, X3
failed-block reference ladder, X4 G2, and D7-H each require their own
explicit authorization recorded by the main thread with exact command, fresh
output root, budget, and stop rules. No phase may review or accept its own
results; Pre-RESULT independent review remains mandatory.
