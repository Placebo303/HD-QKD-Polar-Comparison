# Design — D18 Current-Channel L2 Ensemble DE (E01 freeze)

Authority: `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_READINESS_R1_TASK_PACKET.md`
§§1–6, 8–9. All numbers below are frozen preregistration; nothing here
authorizes execution. Packet §§2/4/5 take precedence on any conflict; STOP
rules are fail-closed. `Phi` = standard normal CDF where referenced for
provenance only (no D18 fit uses it).

## 1. Route (packet §1)

- Repository `HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean`, change
  `v72p2d18-current-channel-l2-ensemble-de`.
- Future batch track: `EXPLORE_HEAVY`; this packet (E01–E09 readiness) is
  implementation/readiness only and authorizes zero scientific DE/decoder
  calls.
- Accepted predecessor:
  `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`
  (PRESENT — exact-string evidence in the final return message).
- Route (main-thread decision, not automatic inheritance): pause further L1
  construction/decoder investment. Optimize the L2 variable-degree ensemble
  under the exact current true-U1-conditioned channel, then validate a
  selected ensemble on finite L2 graphs in a later packet.
- Out of scope: D7-H, APP, joint decoding, real data, FER/leakage/SKR/
  qualification, route closure.

## 2. Adjudication (packet §2 — recorded FIRST, verbatim in scientific effect)

### 2.1 Frozen verdict (never relabel)

- D17's preregistered L055 result stands: `FALSIFIED` under the frozen rule
  comparing observed `27/32 = 0.84375` against the parameter-probability band
  `[0.8899387155669418, 0.9955050869733582]`.
- Trusted D16 B1 evidence (read-only, recorded not recomputed): L045 25/32
  per-graph `[7,6,7,5]` NOT_FALSIFIED; L055 27/32 per-graph `[7,7,6,7]`
  FALSIFIED; L2-ORACLE 9/32 per-graph `[3,1,2,3]` NOT_FALSIFIED against its
  own prediction `[0,0.5]`. All three predictions predated the run and were
  held unchanged with BLANK outcome fields until observation.

### 2.2 Interpretation ceiling

- The L055 miss is a mild model-calibration miss, NOT an L1-construction
  failure: 27/32 with balanced per-graph `[7,7,6,7]`; L045 25/32 survived;
  L2-ORACLE 9/32 survived `[0,0.5]`.
- No construction, optimality, or route claim follows from this ceiling.

### 2.3 Forward methodology amendment (applies to future held-outs only; D16 NOT recomputed)

Two distinct objects with distinct formulas and distinct use:

- (a) Confidence band for latent `p_success`: an interval `[p_lo, p_hi]`
  quantifying uncertainty about the underlying success probability (model-fit
  uncertainty ∪ `delta_DE ± h` granularity sensitivity in the D17
  construction). General form:

```text
CI(p): [p_lo, p_hi] s.t. P(p_lo <= p_success <= p_hi | model + data) ≈ 1 - alpha
```

  Applies when the question is "what is the true success probability?".

- (b) Predictive interval / tail for an observed binomial count: with
  `Y ~ Binomial(n, p)`,

```text
P(Y = k | n, p) = C(n,k) * p^k * (1-p)^(n-k)
P(Y <= y_obs | n, p) = sum_{k=0}^{y_obs} C(n,k) * p^k * (1-p)^(n-k)
central-95% predictive interval at fixed p: [q_0.025(p), q_0.975(p)]
  where q_a(p) = smallest y with P(Y <= y | n, p) >= a
conservative predictive band over a latent band: union over p in [p_lo, p_hi]
  of [q_0.025(p), q_0.975(p)] (or of the tail curve)
```

  Applies when the question is "is an observed count consistent with the
  model, allowing for sampling variation?". A count near but outside a
  latent-p band can still carry non-negligible predictive mass; a count far
  in the tail at every `p` in the band is the predictive-falsification
  signal.

- D16's registered verdict is NOT recomputed under (b). The D17 frozen rule
  (observed rate vs parameter-probability band) remains the verdict of
  record.

### 2.4 Descriptive D16 tail calculation (SPECIFIED here; numeric value is E02/E06 business)

- Exact specified formula (planner specifies formula only):

```text
T(p; y_obs=27, n=32) = P(X <= 27 | n=32, p) = sum_{k=0}^{27} C(32,k) * p^k * (1-p)^(32-k)
inputs: y_obs=27, n=32, p evaluated at both band edges
  p_lo = 0.8899387155669418, p_hi = 0.9955050869733582
```

- E01 computes NO numeric value. E02/E06 SHALL evaluate `T(p_lo)` and
  `T(p_hi)` descriptively as a test value (reported as description only,
  never as a verdict revision).
- Companion descriptive quantity permitted (same status): the conservative
  predictive band over `[p_lo, p_hi]` per §2.3(b); likewise descriptive only.

### 2.5 Secondary signal + route provenance

- Legacy `D16_L2_DEGREE_SIGNAL` agrees directionally but remains secondary.
- The L2-ensemble route is a main-thread decision on the complete evidence,
  not automatic inheritance of that terminal.

## 3. Reuse and channel identity (packet §3)

- Reuse the corrected D17 R2 production channel builder and the explicit
  `L2_DV3_ORACLE` sampler dispatch. Channel SHALL remain true-U1 conditioned,
  XOR-centered on U2, current Model-F candidate, GF32/poly37.
- Reuse the V26 MC-DE kernel (`max_iter=60`, entropy tolerance `1e-4`,
  streak 20), D9 degree/rho mathematics, D17 rate/delta axis, convergence
  rule, trajectory schema, budgets, and verifier patterns.
- Rejected duplication: do NOT copy a DE kernel, Model-F loader, GF32
  primitive, channel sampler, or candidate enumerator when an accepted helper
  can be imported. E02 SHALL document the import map and each rejected copy.
- Proof required: callable identity/signature of both the L1 and L2
  production samplers plus current-channel entropy confirmation.
- Non-transfer (explicit): D8/D9 L1 outcomes and V26 historical numeric
  thresholds SHALL NOT enter as D18 evidence or thresholds.

## 4. Frozen candidate family (packet §4)

- Variable-node edge-perspective family only:
  `lambda = {2:x, 3:1-x}` for `x = 0.00, 0.05, ..., 1.00` — exactly 21
  candidates.
- Candidate IDs use the accepted D8/D9 form `lam_d2_<x:.2f>_d3_<1-x:.2f>`
  (e.g. `lam_d2_0.55_d3_0.45`). `x=0` (`lam_d2_0.00_d3_1.00`) is the mandatory
  DV3 control.
- Per (candidate, m): derive `rho` from the exact rate `R = 1 - m/128` using
  the frozen D9 rule (largest-remainder node counts + concentrated check
  allocation). No hand-set check distribution; no CE/f label anywhere.
- L2 row grid exactly `{89, 94, 99, 104, 109}` with
  `delta = 5m/128 - H_L2`. Reference deltas from the frozen generator
  `H_L2` (same axis as D17 A2: `+0.25384/+0.44916/+0.64447/+0.83978/+1.03509`;
  E03 re-derives mechanically from the accepted entropy record).
- D17 DV3 `delta_DE = 0.5468113653656221` is the baseline comparator, not a
  refittable value (trusted A2 bracket: midpoint of the m94/m99 pair).
- Socket feasibility gate (pre-DE, per candidate/cell): reject before DE if
  the socket realization is invalid, minimum check degree < 2, maximum check
  degree > 8, or rho is not normalized. Record every refusal; do NOT replace
  candidates.

## 5. Frozen two-stage non-searching DE plan (packet §5)

### 5.1 Stage S — bounded screen

- Grid: all 21 candidates × m `{94, 104}` × seeds `2026094301..4304` (4) ×
  population 4000 (one): at most `21*2*4*1 = 168` calls.
- Kernel: V26 `max_iter=60`, entropy tolerance `1e-4`, streak 20.
- Per-candidate summaries: `S_m94`, `S_m104` = convergence counts
  (`#{H60 < 1e-4}` over the 4 seeds at pop4000); `worst_H60_m94`,
  `worst_H60_m104` = worst (max) terminal entropy H60 across the 4 seeds.
- Rank all non-refused candidates deterministically by:

```text
(S_m94 DESC, S_m104 DESC, worst_H60_m94 ASC, worst_H60_m104 ASC, candidate_id ASC)
```

- Select exactly the top three non-DV3 candidates plus DV3 (4 total). If
  fewer than three non-DV3 candidates are executable, return
  engineering-blocked; do NOT widen the family.

### 5.2 Stage C — confirmation

- For the selected four candidates ONLY: complete the full five-m grid
  `{89,94,99,104,109}`, seeds `2026094301..4308` (8), populations
  `{4000, 16000}`.
- Identities per selected candidate: `5*8*2 = 80`; four candidates: 320.
  Reuse the 32 already-computed Stage-S identities for the selected
  candidates (`4 selected * 2 m * 4 seeds * 1 pop = 32`); NEVER rerun them.
- Maximum new confirmation calls 288; total ceiling `168 + 288 = 456`.
- The selected set is determined ONLY by the frozen Stage-S rank. No manual
  substitution, outcome-driven extension, binary search, or extra seed.

### 5.3 Candidate decision

- Recompute each selected candidate's pop16000 bracket using D17's exact
  `DE_BRACKET / DE_SOFT_BRACKET / DE_ONE_SIDED / POP_UNSTABLE` rules.
- Eligible ONLY IF all three hold: clean stable `DE_BRACKET`; no refusal on
  that candidate; `delta_DE <= 0.5077488653656221` (at least one n128 row
  step below the reviewed DV3 threshold; `0.0390625 = 5/128` per row step;
  subtraction verified by hand in proposal Return — see final message).
- Rank eligible non-DV3 candidates by:

```text
(delta_DE ASC, worst_H60_at_hi ASC, max_check_degree ASC, candidate_id ASC)
```

  (`worst_H60_at_hi` = worst H60 at the high-delta bracket edge;
  `max_check_degree` = maximum realized check degree for the candidate.)
- One winner only. The result selects a candidate for a later finite-L2
  packet; it does NOT authorize finite construction and claims NO
  optimality.

## 6. Terminals (packet §6)

- `D18_L2_DE_SELECT_ONE_ENSEMBLE`: at least one eligible candidate exists
  (§5.3) and the deterministic winner rank yields exactly one ID.
- `D18_L2_DE_NO_IMPROVING_ENSEMBLE`: the frozen plan completed (Stage S +
  mechanical Stage C) and no non-DV3 candidate is eligible.
- `D18_L2_DE_BASELINE_DRIFT`: the recomputed DV3 pop16000 result conflicts
  with the accepted D17 baseline (`delta_DE = 0.5468113653656221`) beyond
  the frozen grid/stability rule (bracket edge/flag disagreement under the
  exact D17 `DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED/POP_UNSTABLE` rules —
  e.g. DV3 fails to reproduce a clean stable bracket at the frozen grid, or
  its recomputed bracket is inconsistent with the A2 lo94/hi99 placement
  beyond the predeclared `delta_DE ± h` granularity sensitivity).
- `D18_L2_DE_ENGINEERING_BLOCKED`: any contract, resource, channel,
  refusal-count, or incomplete-plan failure — including <3 executable
  non-DV3 in Stage S, unprovable channel identity, seed collision, existing
  future root, or review blocker.
- All four are synthetic DE evidence only.

## 7. Rejected alternatives (recorded)

Outcome-adaptive grid extension/binary search; refitting DV3 `delta_DE` to
new data; hand-set check distributions or CE/f rate labels; replacing refused
candidates; rerunning Stage-S overlap identities; widening the family when
<3 non-DV3 are executable; manual substitution into the selected four;
APP/joint/L1 evidence in the L2 decision; merging exact/syndrome/undetected;
new DE kernel or optimizer dependency; FER/leakage/SKR/qualification use of
the winner.

## 8. Future execution boundary (packet §8)

- Fresh root pattern (reserved by planner; UUID picked by implementer):
  `workspace/d18_l2_ensemble_de_<uuid>`. One exact repo-venv command frozen
  during E05/readiness. Root SHALL be absent throughout readiness (E07
  proves absence).
- Ceilings: maximum 456 scientific DE calls plus ≤16 setup units; wall
  ≤1800s; per-call ≤300s (checked between/after calls, never interrupting a
  call); RSS <2GiB; one CPU process; no retry/resume/seed-search/adaptive
  grid extension.
- One later explicit user grant may cover Stage S and the mechanically
  selected Stage C together. This readiness packet grants none.
- Note: UUID selection is E05 implementation business — planner reserves the
  naming pattern; the implementer picks the UUID and proves root absence.

## 9. STOP conditions (packet §9)

STOP without scientific execution if: the current true-conditioned L2 sampler
cannot be proven identical to corrected D17; D16's verdict would be
rewritten; the candidate/grid/selection is outcome-adaptive beyond §5;
Stage-S overlap is rerun; exact/syndrome/undetected are merged; APP/joint/L1
enters; seeds collide; the future root exists; or independent review has a
blocker.

(End of file)
