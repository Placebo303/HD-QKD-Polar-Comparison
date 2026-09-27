# PREREG — EXPLORE packet `s01_dimension_probe_20260923`

Track: **EXPLORE** (AGENTS.md §1.2). Cost annotation: none (no DECIDE-class gate reached).

## Goal

Answer, with the cheapest scientifically valid computation, one question that
gates the high-dimensional IR exploration direction:

> Does the arrival-time-encoding error law in this project contain enough
> *structure* that a decomposition-based (low-dimensional) corrector is
> information-lossless, or does the inter-plane correlation that BICM-style
> parallel decoding loses actually exist in our data?

Secondary goal: produce a zero-cost, no-decoder, no-frame-array map of the
frozen channel structure so that later packets do not have to rediscover it.

## Non-Goals

- No FER, efficiency (f), SKR, leakage, qualification, promotion or publication
  claim of any kind. Every number produced here is `diagnostic_only`.
- No modification of any frozen constant: `K1/K2`, `P16`, `w=5`, `N=32768`,
  `tag=64`, `H_M2`/`H_full`, `f=1.3`, codebooks, packet texts.
- No real-data decoder execution. No new measurement. No raw frame arrays are
  loaded.
- No decision about the native-q vs binary-plane code family. This packet only
  measures the *channel*, not the code.
- No cross-checkout merge, no push, no branch operation (AGENTS.md §10.2).

## Impact Scope

Allowed to write (additive only):

- `workspace/s01_dimension_probe_20260923/**` — fresh additive root for all
  artifacts and scripts of this packet.
- `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/**` — this packet's
  preregistration and the single append-only exploration log.

Forbidden to write: `src/`, `experiments/`, `tools/`, `results/`,
`comparison_bench/src/`, `comparison_bench/outputs_comparison/`, any
`openspec/specs/` or `openspec/changes/` frozen document, and the sibling
checkout `../HD-QKD_Polar_Release` (frozen Polar mainline, never touched).

## Authorization Boundary

One authorization covers the frozen conditional arm sequence below. No per-arm
authorization, operator-return, failure-verification, repair-review or
rerun-review files are produced (AGENTS.md §1.2 EXPLORE contract).

Frozen arms (in order; the operator continues to the next arm while the
preceding machine gate permits):

| Arm | Content | Stop rule |
|---|---|---|
| **A0** | Read-only arithmetic on the frozen D01 aggregate `channel_diagnostics.json` (magnitude classes, Gray-plane occupancy ladder, binary-plane entropy sum). No decode, no frame array. | Any script error → record and stop; no repair without a preregistered correction. |
| **A1** | Small-q synthetic screening (`q ∈ {4,8,16}`), *synthetic* channels only, comparing native-symbol decoding against per-plane binary decoding on the FER–leakage plane. | STOP if no separation is observed once the frozen seed set is exhausted. |

Preregistered engineering corrections (max one repair+rerun with unchanged
scientific inputs): any script defect in A0/A1 — not a hypothesis change — may be
repaired once and rerun; the failed attempt is retained unchanged in the same log.

Escalation to DECIDE is required before any of the following (AGENTS.md §1.2):
real/raw frame data, any FER or efficiency number intended as a claim, any
change to the scientific inputs or the tested hypothesis, a materially higher
compute budget, or a destructive write.

## Acceptance Criteria

Stable IDs; the operator reports these, not a restatement of the plan.

| ID | Criterion |
|---|---|
| S0-1 | `sum_j p_j` (the 10 frozen per-bit-plane mismatch rates) compared against the frozen `raw_ser` with the equality/inequality outcome reported at full precision. |
| S0-2 | Magnitude-class masses table with `P(|Δ|<32)`, `P(|Δ|≥32)`, and the support size `#{unique Δ} / q`. |
| S0-3 | `sum_j h2(p_j)` compared against the empirical `H(diff)`; the capture ratio and the signed loss reported. |
| S0-4 | Every number traceable to a frozen file path + JSON key; no number invented, interpolated or fitted. |
| A1-1 | FER–leakage curves for native-symbol vs per-plane binary decoding on ≥3 seeds per q, on synthetic channels with the *measured* plane-rate ladder as the channel model. |
| A1-2 | The separation (if any) reported with its point of crossing, and the difference expressed in the same unit for both arms. |

## Claim Ceiling

`diagnostic_only`. No result from this packet may be cited as an FER, an
efficiency, a leakage budget, a code-family verdict, or evidence that any method
is or is not applicable. A PASS on S0-* states a fact about a *frozen aggregate*,
not about the decoder, not about a code family, and not about achievable
performance.

## Provenance Of Third-Party Findings Recorded In This Packet

The following items are recorded in the exploration log as **third-party inputs
that this checkout cannot independently verify** and that are marked as such

- Q1 "preregistered cap" adjudication constants (`H = 0.8168138204133305`,
  `cap = 34794 bits/block`, `K_max = 6946`, …) originate from the sibling
  NB-Polar checkout. A grep of this repository for those literals returns no
  match; they are recorded as *received*, arithmetic-internally-consistent, but
  unverified against this checkout's frozen sources.
- The sibling's six correction statements about the sibling's own internal
  conclusions. Only the subset reproducible in this repository is marked
  verified; the rest is recorded as received.

This provenance split is deliberate: AGENTS.md §0's crosstalk incident is
precisely the failure mode of treating a sibling's internal state as one's own.
