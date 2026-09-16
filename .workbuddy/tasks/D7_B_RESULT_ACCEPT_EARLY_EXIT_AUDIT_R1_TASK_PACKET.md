# D7-B — scoped result acceptance and zero-decoder early-exit belief audit R1

## 0. Main-thread preliminary adjudication

The WSL R2 invocation and independent consistency review are accepted as
authentic, immutable and contract-faithful evidence. The stored terminal is:

`D7_B_RESOURCE_OVERRUN`

This terminal was triggered by 64/64 `rss_bytes=null`, not by a measured value
at or above 2 GiB. It must not be rewritten as a measured memory breach.

The run also established the following narrow observed facts:

- 64/64 cells returned exact+syndrome-consistent hard decisions at cap 1;
- P99/P90/P60: 48/48 returned at decoder iteration 0;
- PAIR: 1/16 returned at iteration 0 and 15/16 at iteration 1;
- zero crash/nonfinite/unsatisfied/symbol errors;
- tractable MAP agreement 64/64;
- tractable posterior error was not small: SINGLE max about 0.500 and TREE max
  about 0.400 against the `1e-10` requirement.

Therefore the main thread accepts neither `D7_B_EASY_REGIME_CONFIRMED` nor a
general decoder-performance claim. The result currently supports only:

`HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`

The next decision depends on whether early syndrome satisfaction returning
untouched log-priors is a documented current-belief behavior, a D7-B metric
design mismatch, or a downstream L1→L2 APP contract defect.

## 1. Authority and prohibitions

This packet authorizes:

- scoped acceptance documentation for the immutable R2 root;
- read-only scalar analysis of that root;
- static/code-contract review;
- pure D7-A oracle/fixture calculations that bind no historical decoder;
- an independent scientific/semantic review;
- local scoped commits and memory triage.

It authorizes zero decoder calls. It does not authorize D7-B rerun, R1d, D7-C,
D7-D, any `--phase`, G1/G2, Model-F, CAL, VAL, real/raw or result-root edits.

## 2. Baseline

- Branch: `formal-ir-v72p1-addendum-clean`
- Expected HEAD: `03c2e68e`
- Accepted invocation UUID:
  `c605d1e6-8577-4c52-a865-12500fc8c964`
- Required review: `D7_B_PRE_RESULT_REVIEW_PASS_R2`
- Root: exactly five immutable files under
  `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`
- `d7b_execution_authorized: false`, attempts/completed `1/1`,
  decoder/result `true/true`
- current gate: `INDEPENDENT_D7_B_RESULT_ACCEPTANCE_R2`
- R1d/G2 absent; protected roots unchanged; no push

Read the root twice by names/sizes/mtime around the task. Do not modify it.
Known unrelated dirty/CRLF and pending SOP/workbuddy changes are out of scope.

## 3. Phase A — durable scoped acceptance

Create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_RESULT_ACCEPTANCE_R2.md`

The acceptance must state all of the following without reinterpretation:

1. lifecycle and five-file evidence are accepted;
2. stored terminal remains `D7_B_RESOURCE_OVERRUN`;
3. `resource_overrun` means RSS unknown because WSL venv lacked psutil;
4. no measured RSS breach occurred and no `<2GiB` PASS may be claimed;
5. all 64 hard decisions were exact+syndrome at cap 1;
6. 49 cells used iteration 0 and 15 used iteration 1;
7. truth-centered P99/P90/P60 make the 48 iteration-0 successes an initial-MAP
   sanity region, not evidence of iterative BP gain;
8. PAIR supplies the only cells that generally required one sweep;
9. posterior tolerance failed although MAP agreement passed;
10. accepted scope is exactly
   `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`;
11. D7-B `CONFIRMED/PARTIAL` is not accepted;
12. no FER, leakage, key rate, CAL recovery, qualification, R1d/G2 permission or
    broad NB-LDPC conclusion follows.

Update `cycle_state.yaml` only with factual acceptance fields and move
`next_gate` to `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT`. Keep every authorization
false. Append this narrow acceptance to decision log and project memory.

Commit Phase A separately before the audit:

`docs(d7-b): accept WSL R2 hard-decision calibration with disclosed limits`

## 4. Phase B — zero-decoder audit questions

Create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md`

Answer E01–E12 using source, frozen docs, root scalars and pure independent
math only:

- E01 independently reproduce the 49×iteration-0 / 15×iteration-1 partition;
- E02 prove from v35 source exactly what happens before the initial syndrome
  check and what `final_beliefs` contains on iteration 0;
- E03 for representative SINGLE/TREE P99/P90/P60 cells, prove whether
  `softmax(final_beliefs)` equals the input prior at iteration 0;
- E04 independently compute syndrome-conditioned exact posteriors and explain
  the observed 0.500/0.400 scale without calling the decoder;
- E05 split posterior error by tier, prior family and decoder iteration;
- E06 distinguish hard-decision correctness, syndrome satisfaction, MAP
  agreement and calibrated posterior equality;
- E07 inventory every production consumer of `final_beliefs` and state whether
  it treats the value as current score, channel prior, or syndrome-conditioned
  APP;
- E08 audit D5 `_run_layered_block` and `app_fed_l2_prior`: identify the exact
  probabilistic quantity expected for L1→L2 conditioning;
- E09 determine whether iteration-0 return can silently omit syndrome evidence
  from L2 while still reporting a valid L1 codeword;
- E10 determine whether D7-B's posterior criterion is invalid when the decoder
  legitimately stops before message updates, or correctly detects an interface
  contract mismatch;
- E11 classify WSL RSS null as telemetry dependency gap, code defect or true
  resource evidence; specify the minimal future stdlib measurement rule without
  implementing it;
- E12 state which next route is scientifically justified.

Do not infer posterior meaning from the name `final_beliefs`; use assignments,
normalization, return paths and consumer calculations.

## 5. Required competing interpretations

Evaluate all three explicitly:

### I1 — documented current-belief behavior, no decoder defect

`final_beliefs` means the decoder's current log-belief state. At iteration 0
that state is the normalized input log-prior. Early syndrome success is valid
for the decoder's hard-decision objective; D7-B incorrectly required a
conditioned exact posterior after no check update.

### I2 — downstream APP contract defect

The decoder return is internally honest, but D5 consumes `final_beliefs` as an
approximation to `P(U1 | B, disclosed syndrome)`. Iteration-0 early return
contains no syndrome message, so forwarding it to L2 omits disclosed evidence.
The repair belongs at the decoder/adapter contract boundary.

### I3 — decoder early-stop semantic defect

The public decoder contract itself promises syndrome-conditioned posterior-like
beliefs even on success, so returning untouched priors is incorrect and at
least one check sweep/posterior computation is required before return.

More than one may apply at different layers. State separately:

- decoder hard-decision correctness;
- decoder belief-return contract;
- D5 layer-interface expectation;
- D7-B metric validity.

## 6. Frozen audit outcomes

Choose exactly one primary outcome:

- `D7_B_METRIC_CONTRACT_MISMATCH_ONLY`: decoder/consumer contracts are honest;
  D7-B posterior gate was inapplicable to iteration-0 early success.
- `D7_B_EARLY_EXIT_LAYER_INTERFACE_CONTRACT_DEFECT`: decoder hard decision is
  valid, but D5 consumes unconditioned iteration-0 beliefs as conditioned APP.
- `D7_B_DECODER_BELIEF_RETURN_CONTRACT_DEFECT`: v35 itself promises conditioned
  beliefs and violates that promise at iteration 0.
- `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`: metric design and downstream
  interface both require scoped correction.
- `D7_B_EARLY_EXIT_AUDIT_BLOCKED`: source/docs do not establish the intended
  contract; list the single main-thread decision required.

Secondary RSS outcome must be:

- `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`, unless evidence shows a different cause.

Do not implement any repair in this packet.

## 7. Independent review

An independent reviewer that did not author the audit must:

- reread v35 initial return and all `final_beliefs` consumers;
- independently recompute representative exact posteriors;
- verify the 49/15 partition and error stratification;
- challenge the selected I1/I2/I3 combination;
- ensure no decoder call or root mutation occurred;
- verify acceptance wording does not upgrade the frozen terminal.

Create `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md` with one verdict:

- `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`
- `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_FAIL`
- `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_BLOCKED`

FAIL/BLOCKED stops route advancement. No self-repair beyond correcting an
arithmetic/transcription error in the audit.

## 8. Next-route mapping

After review PASS:

- metric-only → `D7_C_BIDIRECTIONAL_ORACLE_PACKET_FREEZE`, with D7-C metrics
  separating hard success from posterior calibration;
- layer-interface or mixed →
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`, before D7-C;
- decoder-belief contract defect →
  `D7_A_DECODER_BELIEF_RETURN_CORRECTION_PROPOSAL`, before D7-C/R1d;
- blocked → remain at `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT`.

Every future WSL runner must use a reviewed stdlib RSS path (`resource` on
Linux/WSL with documented units) or another explicitly available measurement;
absence must fail before scientific execution, not convert an otherwise useful
run into a post-hoc resource terminal. Do not implement this rule here.

Commit audit/review/state route and append-only durable decision separately:

`docs(d7-b): classify early-exit soft-belief semantics and next route`

No push.

## 9. Acceptance matrix

- A01 immutable R2 root/lifecycle/review verified
- A02 scoped acceptance preserves `D7_B_RESOURCE_OVERRUN`
- A03 RSS unknown distinguished from measured breach
- A04 hard-decision evidence and 49/15 iteration split exact
- A05 no `CONFIRMED/PARTIAL` or performance overclaim
- A06 E01–E12 answered with reproducible scalar evidence
- A07 exact posterior recomputation uses no production decoder
- A08 every `final_beliefs` consumer inventoried
- A09 I1/I2/I3 separated by layer
- A10 one frozen primary outcome selected
- A11 RSS secondary outcome selected
- A12 independent review PASS
- A13 next gate follows §8 mapping only
- A14 zero decoder/phase/data execution and zero root mutation
- A15 all auth false, R1d/G2 absent, scoped commits/no push
- A16 memory triage contains only accepted durable facts

## 10. Hard STOP

STOP if the R2 root/review/state differs, calculations require a decoder call,
the root would be modified, a production-code fix becomes necessary, contract
intent cannot be established, or independent review fails. Do not rerun D7-B.

## 11. Return

Report Phase-A acceptance scope, commits, E01–E12, 49/15 and posterior-error
tables, consumer inventory, I1/I2/I3 decisions, primary+RSS outcomes, review,
next gate, root equality, authorization/R1d/G2/no-push checklist.

End exactly:

`D7-B WSL R2 已按受限口径接受并完成 early-exit soft-belief 零-decoder归因；正式终局仍为 RESOURCE_OVERRUN，后续按独立评审通过的合同分支推进，R1d、G1、G2 均未授权。`

