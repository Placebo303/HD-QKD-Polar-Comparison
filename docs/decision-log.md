# Decision Log

Durable decisions and rejected alternatives for the HD-QKD_Polar_Comparison project.

---

## Template

```
### YYYY-MM-DD: <Title>

**Decision**: <What was decided>

**Context**: <Why this was needed>

**Alternatives considered**:
- Alternative A: <Why rejected>
- Alternative B: <Why rejected>

**Consequences**: <What this means going forward>
```

---

## Decisions

> **最新条目在文件尾部**（tail）；头部为历史区（head stale，当前头为 2026-09-14 D13）。最新条目起于第 4612 行（`### 2026-09-21: P0 reduced-m L2 probes`）；验证：`grep -n '^### 2026' docs/decision-log.md | tail`。

### 2026-09-14: Accept D13 Batch A1 reviewed evidence-only result (modest decoder rescue)

**Decision**: Accept `D13_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized D13 Batch A1 run. Stored terminal `D13_MODEST_DECODER_RESCUE` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 224/224 calls (56 replay + 168 ladder), budgets PASS; REPLAY 56/56 match; rescues RL360_a1 3 (MODEST) / RL360_a0.7 1 (NO) / FLOOD360 0 (NO); undetected 0; ranking []. Batch-end review `D13-B1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS with one non-blocking finding (manifest.command flag omission by design); D12/Model-F inputs unmodified. Full record in `docs/research_cycles/V72P2D13-L055-LADDER/EXPLORATION_LOG.md`; root `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — MODEST_RESCUE terminal is evidence-only by frozen design.
- Retry/repair/rerun or second run: rejected — grant consumed, single-pass identities verified.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic L1 decoder diagnostic; no FER/leakage/SKR/forward/L2/real-data/qualification/D7-H claim; no commit/push authorized.

### 2026-09-14: Accept D12 Batch A1 reviewed evidence-only result (select L055)

**Decision**: Accept `D12_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized D12 Batch A1 run. Stored terminal `D12_SELECT_L055` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 432/432 calls, 62/62 setup, budgets PASS; 36/36 admission; exact 221 = syndrome 221, undetected 0 all cells (n128 26/39/42, n256 33/35/46); STABLE all six; MATERIAL L050 False / L055 True; SPLIT False; ranking skipped. Batch-end review `D12-B1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS with non-blocking findings only; predecessors untouched. Full record in `docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/EXPLORATION_LOG.md`; root `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — SELECT_L055 terminal is evidence-only by frozen design.
- Retry/repair/rerun or second run: rejected — grant consumed, single-pass identities verified.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic finite L1 comparison; no FER/leakage/SKR/forward/L2/real-data/qualification/D7-H claim; no commit/push authorized.

### 2026-09-14: Accept D12 finite L1 degree refinement readiness (no execution)

**Decision**: Accept `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION` after D1201-D1210 (D1210 `EVIDENCE_ACCESS: VERIFIED` / `PASS`, no blocker). Grants no execution; predecessor D11 wide-recovery stays immutable and never pooled.

**Context**: Six degree cells recomputed from D9 rule EXACT, 36/36 A1-A6 independently recomputed, isolation/gates-ranking/terminals verified, budgets match, 26/26 + 41/41 tests rerun, decoder/scientific 0, future root `workspace/d12_finite_l1_degree_94fb9d22-…` absent. Records in `docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d12-finite-l1-degree/`.

**Alternatives considered**:
- Authorize D12 batch now: rejected — readiness grants no execution; needs separate explicit authorization.
- Re-run D1210 checks now: rejected — trusted VERIFIED review, not rerun per trust rule.

**Consequences**: Future batch is EXPLORE_HEAVY (432 calls). Claim ceiling synthetic finite L1 degree comparison only; no FER/leakage/SKR/forward/L2/real-data/qualification/promotion/D7-H/commit/push. Pre-EXECUTE must reconfirm dirty-tree preflight.

### 2026-09-14: Accept D11 Forward APP Batch A1 reviewed evidence-only result (wide recovery)

**Decision**: Accept `D11_FORWARD_APP_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized D11 Batch A1 run. Stored terminal `D11_FORWARD_APP_WIDE_RECOVERY` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 720/720 calls, 62/64 setup, budgets PASS; L1 replay EQUAL R3 both widths; 288/288 CHECK_UPDATED; exact 209 = syndrome 209 (n128 J_M22/O43, n256 J_M28/O64); SIGNAL/SIGNAL both widths. Batch-end review `D11-B1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS with non-blocking F1-F5 only; R3 root untouched. Full record in `docs/research_cycles/V72P2D11-FORWARD-APP/EXPLORATION_LOG.md`; root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — wide-recovery terminal is evidence-only by frozen design.
- Retry/repair/rerun or verify_root fix now: rejected — grant consumed, F2 latent fix deferred to next verify touch.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic two-layer forward diagnostic; no FER/leakage/SKR/qualification/real-data/L2-mixed/D7-H claim; no commit/push authorized.

### 2026-09-14: Accept D11 wide forward recovery; refine L1 degree mix

**Decision**: Accept D11 as
`D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`, retaining
machine terminal `D11_FORWARD_APP_WIDE_RECOVERY`. Run no D7-H. The next
orthogonal experiment is a small finite L1 comparison of D9-supported λ2
values 0.45, 0.50 and 0.55.

**Context**: joint/source conversion is 22/23 at n128 and 28/29 at n256 with
288/288 CHECK_UPDATED transfers; L2 oracle is 43/72 and 64/72. Forward transfer
works. Overall joint yield is limited chiefly by L1 exact recovery.

**Alternatives considered**:
- D7-H: rejected because reverse feedback adds complexity to an interface that
  already preserves nearly every L1 success.
- Mixed-degree L2: rejected because D9 calibrated only the L1 channel.
- Real-data DECIDE now: deferred until synthetic recovery improves beyond the
  present roughly one-third operating point.

**Consequences**: issue D12 finite L1 degree-refinement readiness. No execution,
real data, FER/leakage/SKR, D7-H, commit or push is authorized.

### 2026-09-14: Accept D12 finite L1 degree-refinement readiness

**Decision**: Accept D1201--D1210 as
`D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` based
on `D12-R1210`, `EVIDENCE_ACCESS: VERIFIED / PASS`, no blocker. Do not repeat
the independent checks.

**Context**: all six degree cells match D9 realization math; 36/36 fresh graphs
pass A1--A6; isolation, STABLE/MATERIAL/ranking/split rules, 432 identities,
budgets and no-production boundary pass. The one four-cycle is diagnostic-only
and stays frozen.

**Consequences**: issue one EXPLORE_HEAVY execution packet measuring both widths
without early stopping. Readiness acceptance grants no execution, D7-H, real
data, claim, commit or push.

### 2026-09-14: Accept L055 and route frozen failures to decoder ladder

**Decision**: Accept D12 as `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`,
retaining `D12_SELECT_L055`. Do not extend the λ grid yet. Run a strong-decoder
diagnostic only on the 56 frozen L055 failures.

**Context**: L055 gives 42/72 vs L045 26/72 at n128 and 46/72 vs 33/72 at
n256; it alone satisfies MATERIAL_BETTER. Every L055 failure reached iteration
90, whereas successes converged by iteration 50, leaving decoder truncation or
dynamics as the cheapest unresolved variable.

**Alternatives considered**:
- More λ values: deferred until decoder-limited failure is excluded.
- Immediate forward rerun: deferred because D11 already showed 50/52 L1
  successes became joint successes.
- D7-H: rejected; it does not address the remaining L1 failures.

**Consequences**: issue D13 strong-decoder-ladder readiness for exact D12 failed
identities. No execution, L2/D7-H, real data, claim, commit or push.

### 2026-09-14: Accept D11 canonical forward APP readiness (no execution)

**Decision**: Accept `D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION` after D1101-D1110 (R1110 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker). Grants no execution; predecessor D10 R3 stays immutable and never pooled.

**Context**: Canonical transfer/provenance/q-APP/oracle/admission reuse is-identical, L1 replay gate verbatim, shared-L2 identity (6 distinct/width, oracle rides MIX), gates/priorities/terminals verified, budgets match; 33/33 tests rerun + PROFILE 36/36; decoder/scientific 0; future root `workspace/d11_forward_app_7c1878b5-…` absent. Records in `docs/research_cycles/V72P2D11-FORWARD-APP/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d11-forward-app/`.

**Alternatives considered**:
- Authorize D11 batch now: rejected — readiness grants no execution; needs separate explicit authorization.
- Re-run R1110 checks or 23 R3 tests now: rejected — trusted VERIFIED review, not rerun per trust rule.

**Consequences**: Future batch is EXPLORE_HEAVY (360/width, max 720, n256 iff `D11_FORWARD_SIGNAL(n128)`). Claim ceiling synthetic two-layer forward diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion/D7-H/commit/push. Pre-EXECUTE must reconfirm dirty v72p2d5 tree state (kwargs on `_run_layered_block`).

### 2026-09-14: Accept D10 R3 Batch A1 reviewed evidence-only result (wide L1 signal reproduced)

**Decision**: Accept `D10_R3_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized R3 Batch A1 run. Stored terminal `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 288/288 calls, 50/50 setup, budgets PASS; exact 52 = syndrome-valid 52 with n128 M=23 and n256 M=29 (both `R3_REPRODUCED`, DV3 0); n256 dispatched only after n128 REPRODUCED. Batch-end review `D10-R3-B1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS with no blocking finding; A1 untouched/unpooled. Full record in `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/EXPLORATION_LOG.md`; root `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — wide-signal terminal is evidence-only by frozen design.
- Retry/repair/rerun or A1 pooling: rejected — grant consumed, A1 frozen and never pooled into R3 gates.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic L1-only; no FER/leakage/SKR/qualification/real-data/L2/D7-H claim; no commit/push authorized.

### 2026-09-14: Accept D10 R3 fresh-graph scaling readiness (no execution)

**Decision**: Accept `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION` after R301-R310 (R310 VERIFIED pass-with-comments, no blocker). Grants no execution; A1 stays immutable and unpooled.

**Context**: 48 fresh seeds separated; 24/24 A1-A6 independently recomputed; 23 new + 18 R2 tests; PROFILE_ONLY 24/24; decoder calls 0; future root absent. Records in `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d10-r3-fresh-graph-scaling/`.

**Alternatives considered**:
- Authorize R3 batch now: rejected — readiness grants no execution; needs separate explicit authorization.
- Rerun/repair A1 or reuse its graphs: rejected — A1 frozen, never pooled into R3 gates.

**Consequences**: Future batch is EXPLORE_HEAVY (144/width, max 288, n256 iff `R3_REPRODUCED(n128)`). Claim ceiling L1-only synthetic; no FER/leakage/SKR/real-data/L2/D7-H/commit/push.

### 2026-09-14: Accept D10 Batch A1 reviewed evidence-only result (AMBIGUOUS terminal)

**Decision**: Accept `D10_MIXED_DEGREE_L1_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized Batch A1 run. Stored terminal `D10_L1_AMBIGUOUS` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 96/144 L1 calls, 44/44 setup, budgets PASS; exact 31 = syndrome-valid 31 with n64 POSITIVE dispatching n128 and n128 AMBIGUOUS leaving n256 undispatched. Batch-end review `EVIDENCE_ACCESS: VERIFIED` / PASS with no findings. Full record in `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/EXPLORATION_LOG.md`; root `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — AMBIGUOUS terminal is evidence-only by frozen design.
- Retry/repair/rerun or n256 dispatch: rejected — grant consumed, thresholds frozen, no second invocation authorized.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic L1-only; no FER/leakage/SKR/qualification/real-data/L2/D7-H claim; no commit/push authorized.

### 2026-09-14: Accept wide L1 signal and route to canonical forward APP

**Decision**: Accept the R3 evidence as
`D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`. Preserve machine
terminal `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`. The next experiment is a single
forward L1→L2 APP integration with mixed-L1 versus DV3-L1, a shared DV3 L2
target, and a shared L2-oracle diagnostic.

**Context**: fresh-graph MIX exact is 23/72 at n128 and 29/72 at n256 while
DV3 is 0/72 at both; 12 graph pairs reproduce the effect. The base L1 code is
no longer the unresolved variable. The next uncertainty is whether canonical
transfer preserves the signal and whether L2 itself is decodable.

**Alternatives considered**:
- D7-H alternation: rejected; it adds reverse feedback/schedule/double-counting
  before single forward transfer and L2 oracle ceiling are known.
- Tune L1 further: rejected; wide L1 recovery is already reproducible.
- Apply λ2=0.45 to L2: rejected; D9 calibrated the L1 channel only, so that
  would introduce an unvalidated second degree-distribution change.

**Consequences**: issue D11 forward-APP readiness. No execution, L2 result,
FER/leakage/SKR, real data, D7-H, commit or push is authorized.

### 2026-09-14: Accept D11 canonical forward-APP readiness

**Decision**: Accept D1101--D1110 as
`D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` based on
independent `D11-R1110`, `EVIDENCE_ACCESS: VERIFIED`, no blocker. Do not repeat
the independent checks.

**Context**: canonical helper reuse, exact R3 replay, shared-DV3-L2 isolation,
oracle separation, gates, priorities, 360→conditional-720 accounting and
no-production boundary passed. The reviewed dirty d5 dependency remains a
specific pre-execution check rather than a readiness blocker.

**Consequences**: issue one EXPLORE_HEAVY execution packet. Readiness acceptance
does not authorize execution, D7-H, real data, claims, commit or push.

### 2026-09-14: Route D10 A1 ambiguity to fresh-graph scaling replication

**Decision**: Accept A1 as
`D10_L1_AMBIGUOUS_RESULT_ACCEPTED_ROUTE_TO_R3_REPLICATION`. Preserve the frozen
AMBIGUOUS terminal; do not relax its thresholds or dispatch its withheld n256
arm. Build a successor using fresh graphs/blocks: n128 replication first, then
n256 only if the new n128 gate passes.

**Context**: MIX recovered 20/24 vs DV3 1/24 at n64 and 10/24 vs 0/24 at n128.
The n128 distribution 5/2/3 is evidence of a material candidate effect but is
too small to separate scaling from graph variability. Reusing the same three
graphs or changing A1 thresholds would not resolve that ambiguity.

**Alternatives considered**:
- Continue D7-H: rejected because stable wider-width L1 recovery is not yet
  established; alternation would add interface/schedule/feedback confounders.
- Run A1 n256 alone: rejected because 3 graphs × 8 blocks leaves the identified
  graph-variance question unresolved and violates A1 conditional progression.
- Reclassify A1 post hoc: rejected; its frozen terminal remains immutable.

**Consequences**: issue D10 R3 replication readiness packet. No execution,
L2/APP, D7-H, real-data, promotion, commit or push is authorized.

### 2026-09-14: Accept D10 R3 fresh-graph scaling readiness

**Decision**: Accept R301--R310 as
`D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
based on independent review `D10-R3-R310`, `EVIDENCE_ACCESS: VERIFIED`, with no
blocking finding. Do not repeat the reviewer's checks.

**Context**: 24/24 frozen fresh graphs pass A1--A6 with zero replacements;
seed separation, gates, six terminals, A1 non-pooling, budgets and no-production
boundary were independently recomputed. Deferred live refusal and focused tests
belong to the future execution preflight.

**Consequences**: issue one EXPLORE_HEAVY execution packet. Readiness acceptance
does not authorize it and does not revive D7-H or any claim-bearing route.

### 2026-09-14: Freeze D10 mixed-degree L1 finite discriminator readiness (F01–F05)

**Decision**: Freeze the two-arm L1-only finite discriminator
(`PEG_DV3_MATCHED` control vs `PEG_DV23_LAM2_045` candidate) in
`openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/` before any
behavior edit: exact D9 f1.2 degree tables at n64/n128/n256, one minimal
deterministic degree-sequence PEG (`build_degree_sequence_peg`, reusing the
accepted `nonbinary_v10_peg` placement primitives), three fresh graph seeds per
width, eight fresh block seeds per width, uniform nonzero GF32 coefficient
stream, paired identical-block decoding, gates G1–G10, pre-frozen
per-graph/per-pool thresholds, conditional n64 -> n128 -> n256 progression and
an L1-only claim ceiling. Full ceiling 144 scientific L1 calls; fresh root
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` verified
absent; exact future command left absent/unauthorized.

**Context**: D9 accepted `lam_d2_0.45_d3_0.55` from a DE-only screen, but DE
convergence is not a decoder result and D6 recorded 0/40 L1 exact/syndrome for
its DV3-family graphs. No existing builder honors an arbitrary exact
variable-degree sequence with exact check-degree counts, so the smallest
compliant path adds one minimal builder using the already-accepted tie-breaking
policy rather than reusing a `lambda`/`rho`-only constructor.

**Alternatives considered**:
- Reuse `nonbinary_v10_peg.peg_construct` directly: rejected — its API takes
  edge-perspective distributions and re-derives variable counts, so it cannot
  honor an arbitrary exact degree sequence.
- Reuse `nonbinary_v7_r3_codebook._construct`: rejected — hardcoded `_N=1024`
  and no exact check-degree-count control.
- Reuse D6/D5 nested DV3 or V30/V31 support builders: rejected — regular or
  degree-2-only structures with emergent check allocation.
- Shared graph/block seeds across widths or a single graph seed: rejected —
  the design requires per-width fresh seeds and reproducibility across graph
  seeds.

**Consequences**: F06–F12 may now implement the frozen contract; the L1 batch
remains unauthorized until a separate explicit user/main-thread authorization
names the batch, branch, root, seeds and budgets. No L2/APP, FER, leakage,
SKR, real-data or qualification claim is established; D7-H is not revived.
This readiness call performed no behavior edit, decoder call, L1 call, root
creation, commit or push.

### 2026-09-14: Accept D9 calibration and select DV23-0.45 for finite readiness

**Decision**: Accept `D9_DE_CALIBRATION_SELECT_ONE` and select
`lam_d2_0.45_d3_0.55` as the sole next finite-length construction candidate.
Route to `D10_MIXED_DEGREE_L1_FINITE_READINESS`.

**Context**: The selected candidate converged 8/8 at both f1.2 population
sizes and met the frozen 0.95 AUT_30 margin. Lambda2 0.50 was correctly excluded
as stability-ambiguous (7/8 at population 4000) despite a lower AUT_30; 0.55
and DV3 were stable-unconverged. Independent review recomputed all 96 calls and
the stored selection with no blocking finding.

**Consequences**: D10 must compare mixed DV23-0.45 against a regular-DV3 control
using the same finite graph-construction family, multiple graph seeds and L1
f1.2 only at n64/n128/n256. Selection is DE-only and establishes no decoder,
FER, leakage, real-data or qualification result. L2 APP and D7-H remain out of
scope until reproducible base L1 recovery exists.

### 2026-09-14: Accept D9 DE-decoder calibration readiness

**Decision**: Accept the D9 semantic calibration/readiness package and freeze
one 96-call stability batch over DV3 and lambda2 0.45/0.50/0.55. f1.2 is the
only advancement condition; f1.0 is prospectively frozen as a boundary
diagnostic.

**Context**: Independent review verified primitive V26↔v35 equality within
1.94e-16 while preserving the non-equivalence ceiling for flooding versus
row-layered trajectories and DE entropy versus decoder terminals. All 24
finite degree/socket cells are realizable. The f1.0 role follows from its
0.013383 bit/symbol margin, not the D8 outcome. Focused tests passed 20/20.

**Consequences**: Next gate is explicit authorization of the frozen D9
calibration batch. Its result may select at most one ensemble for a later
finite-length packet; it cannot itself establish decoder performance or revive
D7-H. No calibration run, finite decoder, real data, commit or push is
authorized by readiness acceptance.

### 2026-09-14: D9 DE-decoder calibration contract; f1.0 boundary diagnostic

**Decision**: Freeze the D9 calibration contract
(`openspec/changes/v72p2d9-gf32-de-decoder-calibration/`): V26↔v35 semantic map
with equivalence ceiling; f1.0 prospective role `BOUNDARY_DIAGNOSTIC`; deterministic
`{2,3}` degree/socket realization for n64/n128/n256; minimal stability matrix
(DV3 + 0.45 + 0.50 + 0.55 control, 8 seeds, 4000/16000 samples, <=96 DE calls);
routing terminals; fresh future root `10076f83-...` left absent/unauthorized.

**Context**: D8 left 0.45/0.50 primary f1.2 3/3 with every f1.0 result 0/3 and no
winner. D9 must separate threshold, mismatch, instability and gate-role
hypotheses before any finite-length work. The map certifies same-input check
primitives but no flooding-DE ↔ row-layered or DE ↔ decoder terminal
equivalence. f1.0 discloses only `+0.013383` bits/symbol above
`H_L1=3.814742` (0.35 %), below the frozen `0.05` bits/symbol hard-gate
allowance (`R_ent = 1 - H_L1/5 = 0.2370516`).

**Alternatives considered**:
- f1.0 as hard gate: rejected — sub-percent margin, and both C1/C2 predict
  failure there, so it discriminates neither while vetoing f1.2-valid ensembles.
- Broader/adaptive lambda search: rejected — packet bounds the matrix; 0.55 is
  the only added point, with the stated upper-flank control role.
- DE convergence as decoder-equivalent: rejected — staging (e)(f)(g) mismatches.
- Patching V26/v35/channel for exact equivalence: rejected — inherited ensemble
  convention, no defect; STOP not triggered.

**Consequences**: C07–C12 readiness implementation + independent review end at
`D9_DE_DECODER_CALIBRATION_READY_AWAITING_EXPLICIT_AUTHORIZATION`; the 96-call
`EXPLORE_HEAVY` calibration still needs separate explicit authorization. No
decoder/DE execution, root, commit or push; D8 terminal and winner=none
unchanged; D7-H remains unauthorized.

### 2026-09-14: Accept D8 DE result and route to DE-decoder calibration

**Decision**: Accept the reviewed 126-call D8 sweep and terminal
`D8_DE_BASELINE_NOT_CONVERGED`. No candidate advances under the frozen
two-condition rule. Route next to `D9_DE_DECODER_CALIBRATION_AND_THRESHOLD`.

**Context**: The regular-DV3 baseline converged 0/3 at both conditions and no
candidate converged all seeds at both. Lambda2 0.45 and 0.50 nevertheless
converged 3/3 at the primary f1.2 condition, while all candidates were 0/3 at
f1.0. Independent review had verified artifact access, reproduced all 126
metrics and 42 summaries, and found no blocker.

**Consequences**: The D8 winner remains none; the primary-only observations
are successor-design evidence, not post-hoc promotion. Before finite-length
decoding, D9 must calibrate DE versus decoder semantics, MC stability,
finite-graph realizability and the scientific role of f1.0. D7-H, real data,
qualification, promotion, commit and push remain unauthorized.

### 2026-09-13: Accept D8 rate-aligned ensemble readiness

**Decision**: Accept the independently reviewed D8 readiness candidate and
freeze the 21-candidate GF32 `{2,3}` lambda sweep at the two registered rates
and three seeds. Next gate is explicit authorization of one D8 DE sweep.

**Context**: V26 MC-DE is reused unchanged through a thin Model-F adapter; the
full 32-ary L1 posterior is preserved, rate/degree identities were independently
re-derived (56/56), focused tests passed 15/15 after the sole F1 correction,
and no scientific DE sweep or decoder ran. F2–F4 are non-blocking execution
semantics: partial roots fail normal verification, the call cap is post-call,
and DE coefficients are an ensemble convention rather than a finite-length
seed stream.

**Consequences**: Readiness terminal is
`D8_RATE_ALIGNED_ENSEMBLE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The future sweep remains DE-only synthetic evidence and cannot authorize a
finite-length decoder, D7-H, real data, qualification, promotion, commit or
push.

### 2026-09-13: Open D8 rate-aligned GF32 ensemble feasibility with V26 DE reuse

**Decision**: Open `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY` (cycle
`V72P2D8-RATE-ALIGNED-ENSEMBLE`, track `EXPLORE_HEAVY`, readiness/design only)
and freeze the ensemble-feasibility reuse contract in
`openspec/changes/v72p2d8-rate-aligned-gf32-ensemble-feasibility/`. Reuse the
accepted V26 Monte-Carlo DE kernel (`nonbinary_v26_mcde.run_mcde_posterior`,
GF32 poly 37) unchanged, with one thin L1 Model-F channel adapter (accepted
CAL-only artifact `workspace/v72p2d5_model_f_input/20260907_r1` → E2 `P_F` →
`P1` → `1e-15` floor → XOR centering; 32-ary rows preserved exactly), the
V27-style `R = 1 - m/n` / `ρ = make_rho` mapping on the accepted D6 row budgets
(n64 L1 (49,59,64) / L2 (43,52,64); n128/n256 ×2/×4), V37 trajectory metrics,
and a bounded deterministic λ family (support {2,3}, step 0.05, 21 candidates,
regular-DV3 baseline included). Rejected: V14/V9/V10/V11 QSC/all-unity-coefficient
engines (no nonzero edge coefficients, surrogate channels), V22/V18 structured
harnesses, and direct V27/V37 runner reuse (real-data-derived V25 channel,
hard-coded high-rate sources). The future sweep (≤126 DE calls, seeds
`2026091601..2026091603`, wall ≤1800 s, RSS <2 GiB) stays absent and
unauthorized.

**Context**: D6 closed the eligible-only DV3 topology substitution at the
unchanged Model-F channel (L1 0/40; end-to-end APP 0/120); the next orthogonal
variable is the degree distribution/ensemble. The current prior/L1 channel must
enter a DE without scalar approximation, and the candidate search must be
bounded and outcome-independent before another finite-length decoder batch.

**Alternatives considered**:
- V14/V9 MC-DE (probability-domain WHT, all-unity coefficients): rejected as
  primary — cannot represent the current decoder's nonzero GF32 coefficient
  contract; channel is QSC/structured, not the empirical 32-ary posterior.
- V27/V37 runner reuse: rejected — V25 real-data-derived `channel_counts.npz`,
  fixed `λ={2:1}`, hard-coded n=1024/m=184..192 high-rate sources; only their
  rate mapping and metric definitions are reused.
- Passing the D5/X4 frozen per-cell prior (`build_f_model`) instead of the
  D6-current E2 backoff: rejected as the D8 anchor to keep one channel variable
  fixed to the accepted predecessor; retained as an out-of-scope sensitivity
  variant.

**Consequences**: Readiness establishes only mathematical specification,
rate alignment and testability; it establishes no decoder improvement or
ensemble superiority and grants no execution. A future DE advancement
authorizes only the next finite-length task packet; `NO_ADVANCE` closes only
the frozen {2,3}×0.05 grid and routes to a broader ensemble proposal or an
explicit channel/decoder mismatch analysis, never a graph-family or NB-LDPC
impossibility claim. D7-H remains unauthorized/not recommended. All
authorization flags false; no commit or push authorized.

### 2026-09-13: Accept D6 R1d negative and close eligible-only DV3 graph redirect

**Decision**: Accept the independently reviewed D6 R1d A1 EXPLORE result with
stored terminal `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` under the frozen
B0/B1/T1 DV3 contract. Close the eligible-only DV3 topology redirect and route
the mainline to `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY`.

**Context**: The fresh batch completed 120 scientific calls plus 18 setup calls
within all budgets. L1 exact/syndrome was 0/40, L2-APP 5/40, L2-oracle 35/40,
and end-to-end APP exact 0/120. PEG-DV3 was silent at n64, n128 and n256.
Independent batch-end review had `EVIDENCE_ACCESS: VERIFIED` and
`PASS_WITH_FINDINGS`, with no blocking finding.

**Consequences**: The result rejects only the current eligible-only DV3
topology substitution; it does not reject graph families or other degree
distributions. The next orthogonal question is rate-aligned GF32 ensemble and
degree-distribution feasibility at the accepted Model-F channel. D7-H remains
unauthorized/not recommended because alternation does not repair the observed
base L1 failure. No real-data, qualification, promotion, commit or push is
authorized.
### 2026-09-13: Close the D5 rate-mother configuration and redirect D6 to graph/code construction

**Decision**: Accept the X1–X4 evidence and record the D5 current rate-mother
configuration as closed with terminal `G2_CURRENT_CONFIGURATION_FAILED`
(measured stored wall `2141.9420988290076 s`; earlier D5 decomposition terminal
`DECOMPOSITION_NO_N64_RECOVERY` retained as superseded history). D7-H remains
`NOT_AUTHORIZED / NOT_RECOMMENDED`. Resume the existing D6 R1d Option C
eligible-only route — exact arm set `{B0_D5_DV3_NATIVE,
B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3}` with T1 the sole new graph candidate — so
the next orthogonal scientific variable is graph/code construction at the
unchanged Model-F, rows, coefficients contract, decoder and schedule.

**Context**: The accepted X4 G2 run completed 1320/1320 frozen n=256 calls with
L1/L2 exact = 0 and syndrome-valid = 0 for all 200 blocks at each of
f ∈ {1.0, 1.1, 1.2} (grade `G2_CURRENT_CONFIGURATION_FAILED`); X3 showed longer
iteration (row-layered 360: 1/156 rescued) and schedule replacement (flooding
90: 0/156) do not repair the base failure; X2 showed graph-to-graph variation
(forward joint exact 2/16, 2/16, 1/16; reverse 0/16) without a qualitative
recovery transition. Another cross-layer alternation (D7-H) would therefore not
address the identified base-code failure.

**Alternatives considered**:
- Continue D7-H cross-layer alternation: rejected; X3/X4 identify the base-layer
  code failure, not the alternation, as the missing mechanism.
- Reopen the SC/accumulator repair menu: rejected; the R1c-A5 matrix found those
  families structurally inadmissible as frozen (0/10 repair rules admissible),
  and the accepted Option C ruling fixed the eligible-only arm set.
- Invent a new harness: rejected; the existing D6 R1d Option C route already
  carries the frozen thresholds, validity matrix and evidence schema.

**Consequences**: All D6 authorization keys remain false; `evidence_root` and
`terminal` remain null; no D6 R1d output root exists. The batch runs under the
accepted `EXPLORE_HEAVY` two-tier workflow (one prereg + one fresh root + one
append-only exploration log + one independent batch-end review). Any positive T1
result is exploratory graph-candidate evidence only — not FER, qualification,
promotion or real-data success — and does not automatically revive D7-H. A
separate explicit user authorization is still required before any decoder call.

### 2026-09-13: Adopt the two-tier EXPLORE/DECIDE research workflow repository-wide

**Decision**: Replace one-size-fits-all research ceremony with two explicit
tracks as the repository-wide default. `EXPLORE` (synthetic, fresh workspace,
bounded, reversible, no claim) uses one authorization, one append-only
`EXPLORATION_LOG.md`, and one independent batch-end review. `DECIDE` (route
gate, real data, expensive/irreversible, publication/qualification/promotion)
keeps the full gate contract: accepted preregistration, Pre-EXECUTE with
explicit user authorization, one result record, independent Pre-RESULT, and
main-thread acceptance.

**Context**: The completed D7 X1–X4 cycle used ~24 cycle documents plus 6
task/prompt documents (~3556 lines / 197 KB) for ~44 minutes of decoder
computation. X1 was a seconds-scale probe but accumulated separate failure,
fix, rerun, authorization and multiple review records. The process stayed
scientifically safe but was materially over-ceremonial (AGENTS.md §1.1).

**Alternatives considered**:
- Keep one-size-fits-all ceremony: rejected; it delays algorithm work without
  preventing a concrete scientific/overwrite failure.
- Delete the review gates: rejected; it weakens user-only authorization,
  no-overwrite, real-data protection and Pre-RESULT.
- Create a third lifecycle or a workflow engine: rejected; YAGNI.

**Consequences**: Main-thread acceptance was recorded on 2026-09-13 with
terminal `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` and compatibility alias
`TWO_TIER_WORKFLOW_ACCEPTED`. Two tracks are now the repository-wide default. EXPLORE uses
one authorization + single log + one batch-end review; DECIDE gates are
unchanged. Supersedes the per-task review-frequency reading of
`standardize-task-packet-review-loop` and extends
`research-cycle-sop-single-user-simplification`. Machine terminal labels are
scoped classifications (D7-F corrigendum). This workflow acceptance grants no
scientific execution authorization.

### 2026-09-12: Return Codex/OpenCode exchange to manual handoff

**Decision**: Use manual copy-paste for all project-level Codex/ChatGPT ↔
OpenCode prompts and returns. Do not call `opencode_session`,
`codex_desktop_bridge`, or an automatic callback loop as part of this
repository's workflow.

**Context**: The local bridge retained the durable OpenCode session and could
deliver callbacks, but Desktop-native callback turns did not reliably expose
the Codex reply text back to OpenCode. The resulting half-automatic loop added
coordination and approval ambiguity without removing the manual gate.

**Alternatives considered**:
- Keep the half-automatic loop: rejected because Codex replies were not
  reliably readable by OpenCode in the same turn.
- Modify or reinstall the global bridge: rejected because the user requested
  a workflow rollback, not bridge development.

**Consequences**: The user manually transfers the paired prompt and the
`COMPLETE`/`BLOCKED` receipt. Repository packets and cycle documents remain
the durable source of truth. The global bridge, server, skills, and existing
sessions remain installed and are neither modified nor closed.

### 2026-08-24: Use GitHub as the ChatGPT/OpenCode research exchange surface

**Decision**: Use repository-native, copy-pasteable handoffs rather than MCP.
ChatGPT owns planning and read-only scientific review; OpenCode implements a
frozen packet; the user/main reviewer owns acceptance and formal-execution
authorization. `docs/research-cycle-sop.md` is the workflow authority.

**Context**: Chat histories are not durable or shared, and high-capability
execution models can confidently invent missing requirements or overstate
results. Each side therefore receives an exact repository/branch/SHA and a
fixed entrypoint, then returns a stable schema that is copied back into Git.

**Data decision**: Each research milestone includes compact machine-readable
data when practical. Large, binary, raw, private, or replaceable artifacts may
remain outside Git only when the commit includes a result summary with data
identity, seeds, commands, metrics, omissions, claim limits, and reproduction
or retrieval instructions.

**Publishing boundary**: Normal non-force pushes only. An incompatible remote
Polar/crosstalk line is not merged into the formal-IR research history; use a
separate formal-IR branch.

**Consequences**: Agent completion is not acceptance, a test pass is not
scientific success, and development evidence is not qualification. The SOP
must remain lighter than the algorithm work it supports.

### 2026-08-24: Preserve V36 as an exploratory residual signal, not an accepted candidate

**Decision**: Retain V36 code and compact run data, but label A1 DE selection
unaccepted, A2 structural gate failed, and A3 development-only exploratory.
The overall terminal remains `NO_FINITE_GRAPH_ADVANCE`.

**Evidence**: The paired finite data show mean residual 174.80 -> 157.07 and
10/15 improved blocks, but 0/15 exact recovery. All source median gates miss
15%; two blocks worsen by more than 10 errors. The realized graphs contain
thousands of 4-cycles and degree-2 cycle ranks 779--801 despite a frozen zero
cycle requirement. DE confirmation did not compare each source to a baseline
under identical confirmation settings or enforce the required 10% threshold.

**Consequences**: V36 supports a bounded hypothesis that low-average-degree
irregular graphs deserve a corrected finite-aware test. It does not prove
empirical-P DE superiority, trapping-set causality, general FER improvement,
or the necessity of MET.

### 2026-08-24: Close V34 as an ER1-accepted bounded finite-control failure

**Decision**: Accept the single authorized V34 official run as
`matched_empirical_finite_control_fail` and prohibit V34 rerun or tuning.

**Evidence**: Accounting-corrected HEAD `c8cc1fbe` passed independent IR1 and
the complete 45-test fake suite. The authorized 60-block matrix completed with
no fatal record. All three sources had 0/20 exact/syndrome/tag successes, while
mean L2 errors fell by about 31--32%. Strict absolute-path verification was
consistent and independent ER1 accepted all recomputed initial/final counts,
runtime fields, ordinals, authorization, and terminal. No run_02 exists.

**Interpretation**: Matching the empirical generator and posterior removes the
V32 B1 attribution defect, but does not make this one V31 QC finite realization
and V28R decoder succeed at oracle L1 and max_iter=30. Partial error reduction
shows useful posterior/decoder motion; 37 converged-no-syndrome and 23 max-iter
blocks point to finite-graph/iterative dynamics without uniquely identifying
the cause.

**Consequences**: Close current-packet tuning. Use existing residuals to guide
one empirical-P-informed protograph/MET candidate and one rate-adaptive or
incremental-syndrome mother-code design. Any higher-iteration check or new
finite run is a separate successor, not a V34 retry.

### 2026-08-24: High-performance correction algorithms are the strict first principle

**Decision**: Make discovery, implementation, and experimental validation of
high-performance IR/error-correction algorithms the project's strict first
principle. Benchmark, evidence, lifecycle, and review work are supporting
means, not the research output.

**Priority metrics**: correction success/FER, leakage and reconciliation
efficiency, throughput/runtime, memory/resource cost, and accepted-frame net
secret-key yield.

**Blocking rule**: Engineering, audit, or verifier findings block algorithm
work only when they can concretely cause wrong numerics/scientific attribution,
irreproducibility, unauthorized expensive execution, or destructive overwrite.
All other engineering improvements are non-blocking or deferred.

**Consequences**: Do not turn algorithm development into package-hardening or
adversarial-verifier work. Use the smallest scientifically valid implementation
and validation, measure the method, then allocate effort to the next
highest-information correction algorithm.

### 2026-08-24: Freeze V34 and stop after the P3 implementation candidate

**Decision**: Accept the revised V34 specification freeze, implement only the
minimal fake/test-isolated candidate, and stop at
`IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED` for Ox Alpha evidence work
and independent Codex IR1.

**Evidence**: Initial FR1 rejected ambiguous RNG, threshold, decoder-matrix,
failure and protected-root semantics. Revised FR1 returned ACCEPT; independent
science review accepted the carried-forward >=19/20 mechanical discriminator,
bounded-sample claim, max_iter=30 comparability binding and literal NumPy 2.4.0
reference vector. The P3 candidate passes compile, selfcheck, real-input
read-only prepare and 13 focused fake tests; official V34 `run_01` is absent.

**Alternatives considered**:
- Change the gate to 20/20: rejected because it would change the decision rule
  together with the generator and spoil the V32/V34 single-channel-law contrast.
- Raise max_iter to 200 now: rejected because it changes a second variable;
  decoder-iteration adequacy is a separate possible successor.
- Treat 19/20 as FER evidence: rejected; 20 blocks/source are only a bounded
  diagnostic conditional on this packet and decoder configuration.
- Let Ox Alpha execute the real decoder or self-accept: rejected; it is an
  implementation/evidence operator, while Codex retains IR1 and execution gates.

**Consequences**: Ox Alpha may complete the frozen P4 fake T2/T3 evidence
packet. No production decoder, official root, EXECUTE_AUTH, ER1, qualification,
promotion or successor is authorized. See
`docs/v34-p3-implementation-candidate-and-ox-alpha-handoff-20260824.md`.

### 2026-08-24: V33 exact-rate empirical-P ensemble gate passed

**Decision**: Accept the single authorized V33 `run_01` as
`PASS / pass_rate_aligned_empirical_de` after independent ER1, while retaining
an ensemble-only claim boundary.

**Evidence**: 30/30 registered calls PASS; all six source×layer cells PASS
5/5 at the V31 exact rates. Strict replay returned `consistent`,
`problems=[]`, `records_checked=30`; independent ER1 returned ACCEPT. L1 used
23–25 iterations and L2 37–44. No decoder, finite-control, rerun, tuning, or
successor ran.

**Alternatives considered**:
- Treat V31/V32 as proof the whole NB-LDPC route failed: rejected because V32
  used mismatched generator/posterior laws and V33 now passes at the actual
  empirical-P ensemble operating point.
- Infer finite-code success from V33: rejected because DE does not test the
  fixed QC graph, decoder, FER, or finite-length conversion.
- Start a matched control automatically: rejected; it requires a new frozen
  OpenSpec and explicit authorization.

**Consequences**: The exact-rate ensemble veto is removed. The next proposed
scientific gate is one corrected matched empirical-P finite-control that keeps
the V31 QC packet/decoder fixed and changes only generator/posterior matching.
V33 must not be rerun, tuned, or promoted to qualification evidence.
The diagnostic change is archived without merging its delta spec into the
canonical method specs; no successor is authorized.

### 2026-08-21: V31 deterministic finite-graph redesign gate closed with `finite_graph_fail`

**Decision**: Execute and archive the V31 gate as `finite_graph_fail`.

**Context**: V30R failed at the finite graph/decoder conversion layer. V31
tested the successor hypotheses (m1=16, projective-capacity-aware PEG,
deterministic QC control, n=1024/2048) with no search/seed/probity changes.

**Evidence**:
- M1 DE confirmation PASS 60/60 (30/30 per n, m1=16).
- M2: PEG-capacity-aware rejected at both n (L2 GF32 rank-deficient:
  m=200->199, m=414->413); QC-cyclic-projective constructed OK (occupancy<=31).
- M3: n=1024 full window 300/300 exact/tag=0, L2 always `converged_no_syndrome`
  -> exact/tag FER=1.0; n=2048 bounded 1M prefix (14 blocks) repeats the failure.
- Read-only verifier ok=true, problems=[]; terminal finite_graph_fail.

**Alternatives considered**:
- Re-run/tune V30R balanced packets: prohibited by the frozen objective.
- Random matrix-library search / seed adjustment: prohibited.
- Continue the unbounded n=2048 full window: infeasible (non-converging L2
  decodes took tens of minutes to hours per block); closed on a bounded 1M
  prefix per the pre-registered design contingency.

**Consequences**: V31 closes this finite-graph conversion route as negative at
both tested block lengths and both deterministic families. A successor requires
a new user authorization and new OpenSpec change; the primary diagnostics are
L2 syndrome non-convergence on the empirical channel and PEG L2 rank
deficiency at these sizes. No push, qualification, or promotion occurred.


### 2026-08-20: V30R finite-graph gate closed with `finite_graph_fail`

**Decision**: Close and archive V30R after the canonical `run_01` execution
and independent read-only verification. The verifier returned `ok=true`,
`problems=[]`, and recomputed the persisted terminal `finite_graph_fail`.

**Evidence**: M0 reproduced `15/69/303/922/1107`. M1 persisted all 72 screen
calls and 60 confirmation calls; screen-eligible `m1=9,12,16` were ranked,
`m1_9` and `m1_12` were selected, and both completed 30/30 confirmation. M2
retained valid balanced packets for `m1=9,12`; both PEG packets were
deterministically rejected because no projectively unique ratio survived for
support `(0,1)`. M3 screened both valid packets on source 1M blocks `0..5`,
with `0/6` exact/tag-verified and `0` false accepts for each, making the
frozen `15/20` screen threshold impossible. The stage stopped before other
sources and before confirmation. M1/M3 meters were 74.828 s and 719.876 s.

**Scientific boundary**: This is negative only for the tested `n=1024`, F03,
fixed-allocation, balanced/PEG-family finite conversion under the V28 decoder.
It does not negate V25's empirical channel, V26's channel-informed DE, or all
NBLDPC designs. It makes no FER qualification, fresh qualification, promotion,
integration, or public-residual claim.

**Consequences**: V30R evidence and failure are archived. Same-packet expansion,
rerun, decoder tuning, random matrix/degree search, V29 holdout reuse, and
automatic fallback are prohibited. A future finite-graph redesign requires a
new user-authorized OpenSpec; recorded hypotheses are `m1=16`,
projective-capacity-aware PEG, L2 girth/expander/QC/SC constraints, and
`n=2048/4096`. No push was performed.

### 2026-08-20: V30R P103 freeze review ACCEPTED

**Decision**: The independent third P103 freeze review ACCEPTED the V30R
projective-safe finite-graph gate on 2026-08-20. The four-document packet is
now `FROZEN_P103_ACCEPTED`; its frozen implementation and pre-registered V30R
execution are authorized.

**Boundary**: This records authorization, not execution. No V30R code,
finite-code construction, DE, decoder call, or scientific output has started
as of this entry. Fresh qualification, promotion, archive, commit, and push
remain separate actions and are not implied by P103.

**Consequence**: The next operator may implement the exact frozen packet and
then execute its registered gate, preserving the no-rerun/no-tuning and
evidence-boundary rules in the V30R four-set. The active state is not pending
review, and P102 remains historical/superseded.

### 2026-08-20: V27R freeze review ACCEPT (P102) — in-conversation independent review

**Decision**: The V27R OpenSpec (source-adaptive finite-leakage-margin) received an
independent freeze review run ON THE MAIN THREAD directly in this conversation (per
user authorization; subagent not required). Verdict: ACCEPT. The main thread recorded
P102 ACCEPT, unblocking Phase B.

**Context**: subagent infrastructure was persistently unavailable (rounds 1-4). The user
explicitly authorized running the independent review in-conversation and updating the
goal wording accordingly (goal revision 3-4: reviews by main thread in this conversation,
not gated on subagent availability).

**Independent review findings (recomputed independently):**
- H from channel_counts.npz (F03): 1M 0.024280547/0.776757278; 1p5M 0.025199497/0.800366555;
  2M 0.025662049/0.806900673. Matches frozen docs.
- m_total source-adaptive: 1M 200/413/840/1693; 1p5M 206/426/866/1745; 2M 208/430/873/1760
  for block_len 1024/2048/4096/8192. MATCH.
- m1_ep=round(m_total*H1/H_total): 1M 6/13/25/51; 1p5M 6/13/26/53; 2M 6/13/27/54. MATCH.
- Realized f<1.3 all 12 cells (1.29409-1.29974). All 5 candidates per cell legal
  (m1,m2 in [0,m_total], <n). Rates R1~0.993-0.994, R2~0.79-0.81.
- All 14 required spec items captured (proposal/design/tasks/spec); terminal states only
  the 4 allowed; no fixed_ensemble_margin_fail; prohibitions present; no overclaim
  (V27 is asymptotic DE only). Item-by-item check passed.

**Consequences**: V27R FREEZE ACCEPTED; P102 ACCEPT recorded by main thread (goal owns
ACCEPT). Phase B may now proceed: minimal budget planner + V26 MC-DE adapter wrapper,
T0/T1, screen/confirmation, readonly verifier, local commit + archive, no push.

### 2026-08-20: V27R freeze-review gate still blocked by subagent infrastructure (round 2)

**Decision**: Keep V27R OpenSpec in PENDING_FREEZE_REVIEW. P102 ACCEPT is NOT recorded and
Phase B is NOT started because the required independent Luna freeze review still cannot be
delivered: the subagent infrastructure failed every attempt this round (foreground subagent
x1, background subagent x3, muse_spark x1), and earlier-round attempts also failed. The main
thread has independently re-verified the full arithmetic and evidence (P001/P002 closed) and
produced a freeze-review packet (tmp_v27r/v27r_freeze_review_packet.md), but that does NOT
substitute for the independent review.

**Context**: Phase A gate (item 13/14) requires an independent Luna freeze review before
acceptance. This is a process/infrastructure blocker, not a scientific result.

**Alternatives considered**:
- Record P102 ACCEPT on the main thread's own verification: rejected — the goal mandates an
  independent Luna review; fabricating acceptance would violate the strict gate.
- Start Phase B implementation anyway: rejected — violates "freeze review ACCEPT 前不实现".

**Consequences**: V27R docs and evidence are ready; only the independent review is pending on
infrastructure. When subagent infra is available again, a fresh Luna freeze review must run;
on ACCEPT, record P102 and proceed to Phase B. Goal remains active.

### 2026-08-19: V27R OpenSpec revision — source-adaptive finite-leakage-margin budget

**Decision**: Revise V27 OpenSpec from a single worst-source budget to a **source-adaptive**
budget: each source (1M/1p5M/2M) uses its own full-precision H1/H2 and
`m_total = floor((1.3*block_len*H_source - 64)/5)`. Frozen table (block_len
1024/2048/4096/8192 -> m_total): 1M 200/413/840/1693, 1p5M 206/426/866/1745,
2M 208/430/873/1760 (arithmetic re-verified). m1_ep = round(m_total*H1/H_total) (Python
round, round-half-to-even, frozen explicit rule); candidates m1_ep+offset for offset in
{-2,-1,0,+1,+2}; all five eligible. V27 is asymptotic true-predecessor-conditioned
multistage DE (L2 conditioned on correct L1; no finite-code error propagation); the
single 64-bit tag counts only in total block leakage, not between layers. Terminal states
only pass_finite_budget_ready / de_pass_no_finite_headroom / implementation_blocked /
resource_blocked. 24h global completed-call cumulative resource gate; checkpoint bound
to frozen config; V26 archived reference only (no rerun).

**Context**: V26 proved asymptotic A02 (F03 GF32+GF32) DE converges 30/30 at f=1.3. The
finite-leakage-margin gate must answer whether, at finite block length + integer code
rate + 64-bit tag cost, the fixed ensemble retains positive convergence headroom per
source. A single worst-source budget under-allocates 1M/1p5M.

**Alternatives considered**:
- Worst-source single budget (previous draft): rejected — under-allocates 1M/1p5M
  headroom; replaced by source-adaptive.
- m1/m2 search: rejected — only entropy-proportional split plus +/-2 window is tested;
  no degree/m1/m2 search.

**Consequences**: V27R docs written to openspec/changes/formal-nonbinary-ldpc-v27-.../
(proposal/design/tasks/spec). STILL PENDING_FREEZE_REVIEW: the independent Luna freeze
review could not be delivered this session because the subagent infrastructure failed
repeatedly (foreground and background subagent/muse_spark all failed; background agents
stuck in "ready" with no result). P102 ACCEPT was NOT recorded and Phase B was NOT
started, per the strict gate. The freeze review must be completed (Luna worker) and
accepted before any V27 implementation/execution.


### 2025-06-01: Non-invasive comparison layer architecture

**Decision**: The comparison benchmark is built as an outer wrapper (`comparison_bench/`) that reads the original Polar pipeline outputs without modifying them. The original `src/`, `experiments/`, and `tools/` directories are frozen baselines.

**Context**: We needed to compare multiple IR methods without risking regressions in the proven Polar pipeline.

**Alternatives considered**:
- Fork the repo and modify in-place: rejected because it would create maintenance burden and risk breaking the original workflow.
- Build a separate, fully independent project: rejected because we need to directly import/read Polar results.

**Consequences**: 
- `comparison_bench/` is the only mutable area for new IR comparison work.
- The `polar_existing` bridge in `comparison_bench/src/comparison_bench/io/polar_existing_bridge.py` is the sole interface for reading original Polar outputs.

---

### 2025-06-15: OpenSpec workflow initialization

**Decision**: Adopt OpenSpec as the change management workflow for all substantial feature work.

**Context**: Multi-agent workflow requires clear proposal → design → tasks → implement → review → archive pipeline.

**Alternatives considered**:
- GitHub Issues only: rejected because no structured design/spec/task linkage.
- Ad-hoc task lists: rejected because no durable record of decisions and spec changes.

**Consequences**:
- All substantial changes must go through `openspec/` workflow.
- `AGENTS.md` is authoritative for agent rules.
- `docs/decision-log.md` (this file) records durable decisions.

---

### 2026-06-15: Real IR success before final method selection

**Decision**: Prioritize verified real information reconciliation success on high-dimensional arrival-time QKD frames before final error-correction method selection or efficiency comparison.

**Context**: The existing Polar line has produced results, while most non-Polar comparison methods still need stable real-data verification success. Comparing `beta_eff_empirical`, leakage, or runtime before methods actually reconcile real frames risks optimizing a metric artifact instead of solving the IR problem.

**Alternatives considered**:
- Immediate final method selection: rejected because non-Polar methods have not yet established enough verified real-data success.
- Continue broad parameter sweeps first: rejected because broad sweeps are less useful until success/failure criteria and representative real-frame validation are explicit.
- Treat synthetic success as sufficient: rejected because the first-principles target is real high-dimensional arrival-time QKD reconciliation.

**Consequences**:
- The next active OpenSpec change is `real-ir-success-first`.
- Cascade-lite is treated as the first non-Polar real-success candidate, with simplified-Cascade caveats.
- Layered LDPC is treated as an executable failure-diagnosis target before being considered a final candidate.
- qLDPC remains a reference-grade q-ary feasibility direction until stronger evidence exists.
- Final method selection is deferred until verified real-data success and leakage accounting are established.

---

### 2026-07-25: Reconciled evidence is not final method-selection proof

**Decision**: Retain Cascade-lite as the preferred executable non-Polar
candidate and Layered LDPC as the control baseline, but defer final selection
until a new, pre-registered frame-identical confirmation change is completed.

**Context**: The Phase 0 reconciliation verified real-success, optimization,
expanded-evidence, and group-meeting artifacts. It also found material limits:
historical Polar is not frame-identical, low-dimensional group-meeting points
usually have only four frames, and historical changes do not all meet their
written acceptance criteria.

**Alternatives considered**:
- Archive historical changes solely because reports and manifests exist:
  rejected because the acceptance gaps are explicit and measurable.
- Declare Cascade-lite the final production method now: rejected because the
  evidence is bounded and accounting/Polar comparability are incomplete.

**Consequences**:
- No historical IR OpenSpec change is archived in this reconciliation pass.
- The next substantive work is a `final-ir-method-selection` OpenSpec change
  with fixed candidates, compatible leakage reporting, separate tuning and
  confirmation frames, and a stated stopping rule.

---

### 2026-07-25: Bounded final-IR confirmation yields no final winner

**Decision**: Record `no_decision` for the locked medium-SER confirmation; do
not promote Cascade-lite to a final winner from this run.

**Context**: The read-only Phase 4 audit at
`comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`
verified the same 60 unique locked confirmation keys for both candidates, all
attempted statuses, summary denominators, corrected-grid frozen configurations,
and recorded lock hashes. Cascade had 60/60 independently verified successes
and Layered LDPC 59/60; the exact pre-registered two-sided McNemar/binomial
p-value for the one discordant pair is 1.0 at alpha 0.05.

The prior v3 audit is superseded by its additive notice because a generic
decision-helper branch did not represent an LDPC winner or insufficient
evidence. That repair does not change this run's p=1.0 `no_decision` outcome.

**Alternatives considered**:
- Declare Cascade the winner on raw success count: rejected because the
  pre-registered paired test is not significant.
- Rank methods by reported leakage: rejected because the disclosure
  decompositions are method-specific and intentionally non-comparable.

**Consequences**:
- The evidence supports only real d=1024, 64-symbol frames with dataset raw
  SER in [0.20, 0.30); it makes no broader, Polar, qLDPC, or Route A proof claim.
- The non-numerical Route A compatibility gate is `fail`: the Phase-3 schema
  lacks the documented universal-hash protocol, leakage, and correctness-bound
  fields. No Route A numerical rerun was performed.

---

### 2026-07-25: Final-selection evidence is revalidated read-only

**Decision**: Keep the locked v1 data split, authoritative v2 run, and v4
audit immutable; use only read-only verification for their revalidation.

**Context**: Phase 5 hardened the comparison-layer workflow without changing
the frozen baseline or existing evidence. The v1 lock verification and v4
audit verification passed; the latter still reports `no_decision` with p=1.0
and a failing non-numerical Route A compatibility gate.

**Consequences**:
- Future Phase-3 runs require an explicit new additive output directory and
  persist `pre_run_plan.json` before tuning.
- The runbook at `comparison_bench/docs/final_ir_method_selection_runbook.md`
  is the operational entry point for lock, bounded run, and audit commands.
- The result remains bounded to its locked domain; no winner, cross-method
  leakage rank, Polar/qLDPC comparison, Route A numerical result, or proof
  completion is implied.
---

### 2026-07-25: Formal Cascade/LDPC Must Precede Three-Method Ranking

## Decision

Create OpenSpec `implement-formal-cascade-and-ldpc` before attempting a
frame-identical Cascade/LDPC/Polar comparison. It introduces additive
`cascade_formal_v1` and `ldpc_formal_v1` under an offline, already-authenticated
public-channel model, with Alice reference/Bob correction, universal2 Toeplitz
verification, explicit disclosure accounting, and independent qualification.

## Rationale

The existing `cascade_lite` and `layered_ldpc_lite` are executable baselines,
not sufficiently protocol-faithful formal competitors. A three-way comparison
before formalizing them would compare Polar to simplified implementations.

## Consequences

- Lite identities and historical evidence remain unchanged.
- No Polar adapter, formal winner, network/authentication cost, finite-key or
  Route-A numerical claim belongs to this change.
- A later OpenSpec may enable frame-identical three-method comparison only
  after separately qualified formal candidates exist.
- The active spec freezes exact Toeplitz seed/index/transcript semantics,
  Cascade FIFO look-back, deterministic HGF2V1 LDPC codebooks, calibration-only
  rate selection, pinned `ldpc==2.4.1`, additive artifact/status provenance,
  and predeclared synthetic and fresh real-frame promotion gates.
- One or both methods may be archived as `non_promoted`. Only promoted formal
  methods may enter a future Polar comparison; a non-promoted method requires
  a new improvement change and cannot be replaced by its lite predecessor.
- Pinned `ldpc==2.4.1` constructor behavior overrides its docstring: although
  the documentation advertises `random_serial_schedule`, the constructor
  rejects it. Formal kwargs omit it and require serial schedule, explicit
  `[0..63]` order, and one OMP thread. Preflight must prove exact kwargs
  acceptance with a no-decode 1-by-64 constructor probe and fail closed
  otherwise.

---

### 2026-07-25: Synthetic v2 is diagnostic and does not promote a method

**Decision**: Exclude synthetic v1 and v2 from promotion and reopen Phase 5 for
a fresh, contract-compliant v3. No formal method is promoted by these runs.

**Context**: v1 made zero frame calls. v2 listed the pre-registered Alice seed
`2026072501` and frame-order seed `2026072531` but did not use them; it
generated batches using undeclared Alice seeds `2026072502..2505`. Therefore
its outcomes and prior verifier pass do not prove pre-registered generation.

**Consequences**: v2 receives an additive invalid notice and remains diagnostic.
Fresh v3 must bind exact RNG calls/order, qualification-only shared verification
seeds, original transcript bytes, deterministic runner preflight, complete
provenance, exception finalization, and strict verification. Phase 6 and Polar
comparison remain unauthorized.

---

### 2026-07-25: Formal synthetic v3 promotes Cascade only

**Decision**: Record the immutable v3 synthetic qualification as promotion for
`cascade_formal_v1` and non-promotion for `ldpc_formal_v1`.

**Context**: The additive v3 package completed once and its strict read-only
verifier accepted all six artifacts and 128 outcomes. Cascade achieved 32/32
`verified_success` in each p=.01 and p=.02 stratum. LDPC achieved 29/32 and
14/32, below the 31/32 promotion threshold; all remaining outcomes were
retained `verify_failed`, with zero unclassified/internal/provenance/accounting
failures.

**Consequences**: Do not retune this LDPC evidence or replace it with a lite
method. Phase 6 locked real qualification remains required; no Polar adapter
or three-method ranking is authorized by the synthetic result.

---

### 2026-07-25: Bounded formal real qualification promotes Cascade only

**Decision**: Promote `cascade_formal_v1` for the locked real confirmation
domain only: `d=1024`, 64 symbols, bw120, frame SER `[0.20,0.30)`. Do not
infer general Cascade performance or a Cascade-versus-Polar winner.

**Context**: The unique real v2 package passed its strict read-only verifier.
All 60 requested confirmation frames were attempted, denominator-included,
verification-invoked, and `verified_success`, with verification union bound
`3.2526065174565133e-18` and zero unclassified/internal/provenance/accounting
failures. Its exact preflight passed 29 tests with exit 0. The invalid real v1
lock remained unexecuted and byte-preserved apart from its additive invalid
notice. Synthetic v3 separately promotes Cascade at 32/32 in both strata but
leaves LDPC non-promoted at 29/32 and 14/32; LDPC was not run on real data.

**Alternatives considered**:
- Generalize the 60-frame result to other dimensions, frame lengths, bandwidth
  groups, or SER regions: rejected because those domains were not qualified.
- Treat this as a Polar comparison or winner claim: rejected because Polar was
  not run frame-identically in this change.
- Substitute `layered_ldpc_lite` or retune formal LDPC on confirmation:
  rejected because the formal LDPC promotion gate failed and confirmation is
  locked evidence, not tuning data.

**Consequences**:
- The active formal-method change is technically ready for archive review, but
  is not archived until memory triage and the actual archive action complete.
- A new LDPC-improvement OpenSpec change must earn fresh synthetic and real
  promotion before any frame-identical Polar/Cascade/LDPC comparison.
- No general performance, Polar winner, cross-domain, or lite-equivalence claim
  follows from this bounded promotion.

---

### 2026-07-26: Formal LDPC v2 remains non-promoted after frozen qualification

**Decision**: Record `ldpc_formal_v2` as `non_promoted`; do not authorize a
real-data lock/run or a frame-identical Cascade/LDPC/Polar comparison.

**Context**: The active `improve-formal-ldpc-v2` change froze nine policies
(rate margins 0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, `OSD_CS/2`) and a
nested n=64 codebook with selected 32/40/48/56 prefixes. The prior v1
integration root is invalid because its v1 codebook verifier classified all
576 policy outcomes plus 64 associated outcomes as `unsupported_domain`; its
seven artifacts remain immutable with an additive invalid notice. A fresh v2
plan (SHA256 `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`)
had zero old/new CSPRNG overlap and passed strict verification. Development
selected margin 2 with `OSD_0/0` (26/64, 33/64, 56/64 for margins 0, 1, 2,
identical across OSD variants). Confirmation was 28/32 at p=.01 and 29/32 at
p=.02, with seven `verify_failed`, verification invoked on all 64 outcomes,
and zero unclassified/internal/provenance/accounting failures.

**Alternatives considered**:
- Continue tuning against the confirmation outcomes: rejected because the
  confirmation set is frozen evidence, not development data.
- Treat structural codebook screening as qualification: rejected because it is
  only a structural proxy, not verified decoding evidence.
- Proceed to real qualification or three-method comparison: rejected because
  the synthetic promotion gate was not met.

**Consequences**:
- The short- and medium-term engineering tasks are complete with reproducible
  evidence, but LDPC remains below promotion.
- Archive the completed engineering change as explicit non-promotion evidence;
  archiving does not authorize real LDPC qualification or comparison.
- Terra low acted only as the frozen-task implementer/test operator; the main
  thread retained planning and acceptance.

---

### 2026-07-29: Standardize the project-wide agent delivery workflow

**Decision**: Adopt `AGENTS.md` §10.1 as the global default and
`AGENT_HANDOFF.md` as the operator checklist for substantial delegated work.

**Context**: Formal qualification work repeatedly discovered acceptance
requirements late, returned partial subagent status as completion, reran broad
tests after small edits, hit Windows temp ACL failures, and accidentally
entered production decoder paths from tests.

**Consequences**:
- Freeze stable acceptance IDs and feasibility checks before delegation.
- Reuse the nearest accepted predecessor through an explicit delta list.
- Use T0--T3 staged verification and explicit fake runners in test-only paths.
- Use additive Windows workspace roots, process ownership, scoped dirty-tree
  review, and compact delta-only handoffs.
- Preserve all scientific gates, immutable failures, no-rerun/no-tuning rules,
  and main-thread production authorization.

---

### 2026-07-26: Advance binary and nonbinary LDPC as independent parallel lanes

**Decision**: Continue binary LDPC and nonbinary LDPC in parallel, with
separate formal method identities, OpenSpec changes, codebooks, evidence
chains, disclosure accounting, and promotion decisions.

**Context**: `ldpc_formal_v2` is reproducible but non-promoted at 28/32 and
29/32. Its n=64 result points toward longer frames, stronger code families,
incremental redundancy, and bit-plane soft information. The existing
`qldpc_reference` path uses reference-grade matrix construction and hard
syndrome decoding and does not satisfy the formal backend, codebook,
verification, or leakage contracts required of a production-oriented
nonbinary method.

**Alternatives considered**:
- Improve only binary LDPC: rejected because nonbinary symbol-domain coding is
  a scientifically distinct candidate worth evaluating.
- Treat `qldpc_reference` as the formal nonbinary method: rejected because that
  would overstate its implementation and evidence.
- Use one shared qualification pipeline and promotion result: rejected because
  field arithmetic, codebooks, decoder semantics, and leakage decompositions
  differ materially.

**Consequences**:
- Binary and nonbinary work may proceed concurrently through their engineering
  and synthetic-qualification stages.
- The provisional new nonbinary identity is `nbldpc_formal_v1`; the existing
  `qldpc_reference` identity and status remain unchanged.
- Neither lane may reuse existing confirmation evidence for tuning or borrow
  the other lane's promotion.
- A later fair comparison requires independent promotion and frame-identical
  inputs, with disclosure normalized to bits while preserving method-specific
  decomposition.

---

### 2026-07-26: Accept binary long-frame candidate-codebook foundation only

**Decision**: Accept Phase 1 of `binary-ldpc-long-frame-and-ir-v3` as an
offline, candidate-only engineering foundation. Do not select a code family,
wire a decoder, or infer FER or promotion.

**Context**: The additive implementation supports n=256/512/1024, ten planes,
four deterministic candidates, and four nested redundancy prefixes. Canonical
HGF2V3 bytes and a complete 120-candidate manifest bind construction and
structural diagnostics. Main-thread verification passed the focused 4-test
suite, the v2 regression, compilation, and frozen-directory checks.

**Consequences**:
- `ldpc_formal_v2` and its non-promotion evidence remain unchanged.
- Rank, weight, 4-cycle, and `column_pair_extrinsic_degree_v1` values are
  structural proxies, not decoder evidence.
- The next work package must freeze sacrificed-development FER evaluation and
  candidate-selection rules before it reads any development frames.
- Confirmation and real data remain unauthorized.

---

### 2026-07-26: Accept the long-frame development evaluator, not FER evidence

**Decision**: Accept the Phase 2 sacrificed-development evaluator and exact
candidate-selection contract. Do not claim that any candidate or length has
demonstrated FER improvement.

**Context**: The in-memory kernel freezes deterministic p=.01/.02 development
data, pinned BP+OSD-0 parameters, four nested syndrome prefixes, retained
failure statuses, incremental disclosure, and a runtime-independent
lexicographic selection tuple. Main-thread tests independently reconstructed
seed/hash preimages and exercised valid and malformed selection grids.

**Consequences**:
- The evaluator is ready for a separately frozen pinned-backend pilot.
- Injected-decoder tests are contract evidence, not LDPC performance evidence.
- No full development sweep, confirmation, real-data run, candidate
  qualification, or promotion is authorized by Phase 2.

---

### 2026-07-26: Backend pilot clears feasibility, not performance

**Decision**: Use the successful single-slice pinned-backend pilot to proceed
with planning a full sacrificed-development sweep. Do not treat the pilot as
candidate-selection or FER qualification evidence.

**Context**: The one authorized n=256/plane0/candidate0/p=.01 run completed
16/16 exact successes using `ldpc==2.4.1`, mostly at p050, in 0.323 seconds
process time and 1.0 second external wall. It wrote no files.

**Consequences**:
- Backend/API feasibility is no longer the immediate blocker for n=256.
- n=512/1024, other planes/candidates, comparative FER, artifact finalization,
  and verifier cost remain unmeasured.
- A full development sweep requires a new frozen runner/artifact/verifier
  contract before execution.

---

### 2026-07-26: Accept full-development tooling before running the sweep

**Decision**: Accept the Phase 3B runner/verifier implementation and its
test-only evidence. Keep production plan creation and execution as separate
review gates.

**Context**: The tool freezes 3840 ordered outcomes, 30 selections, six
canonical artifacts, a complete hash DAG, failure finalization, no-overwrite,
and strict production/test isolation. Tests cover valid and failed packages
plus semantic tampering after downstream hashes are recomputed.

**Consequences**:
- Tooling is ready to prepare one fresh production plan.
- No candidate FER or selection exists until the production sweep completes
  and the read-only verifier accepts its package.
- Verifier acceptance will still mean artifact integrity and deterministic
  selection reconstruction, not decoder reexecution or promotion.

---

### 2026-07-26: Full per-plane development succeeds but exposes a stopping oracle

**Decision**: Retain the verified 3840-row development package and its
candidate selections, but do not use its per-plane terminal leakage or
100%-success result as formal qualification evidence.

**Context**: Every candidate/length/plane/stratum outcome was an exact
development success. The strict verifier accepted the package and reconstructed
all 30 selections without rerunning decoding. However, the development
evaluator stops each plane by comparing corrected bits directly with Alice.
Bob does not possess that truth oracle in a deployed protocol.

**Consequences**:
- The code-family/backend lane is promising enough to continue.
- Per-plane terminal rounds must be lifted into ten-plane frame-level rounds.
- A formal design should disclose one frame-wide Toeplitz tag and let the
  slowest plane determine each global incremental-redundancy stop.
- Qualification and promotion remain unauthorized until frame-level
  development leakage and stopping semantics are frozen and tested.

---

### 2026-07-26: Select n=256 from frame-level sacrificed development

**Decision**: Freeze n=256 as the next binary LDPC formal-development length.
Do not qualify it until actual frame-wide Toeplitz stopping and formal
transcript/status accounting are implemented.

**Context**: Ten-plane aggregation retained 16/16 successes in both strata for
all three lengths. With one modeled 64-bit tag and slowest-plane global
rounds, n256 had the lowest worst-stratum and overall disclosure fractions:
.68125 and .62265625. The exact selection tuple was
`[-16,-32,.68125,.62265625,256]`.

**Consequences**:
- Candidate IDs selected per n256 plane remain frozen from Phase 3C.
- Formal v3 should use n=256, q=1024, ten planes, and the four global nested
  prefixes.
- Actual Toeplitz tag execution, transcript disclosure, caps and status
  semantics must be implemented before fresh confirmation is planned.
- No promotion follows from sacrificed development.

---

### 2026-07-26: Accept executable binary LDPC v3 before qualification

**Decision**: Accept `ldpc_formal_v3` as the binary lane's formal method
implementation for q=1024/n=256, while withholding qualification and
promotion.

**Context**: The method executes ten frozen Gray bit planes in synchronous
nested-syndrome rounds and uses one locked frame-wide Toeplitz tag only for
global stopping. Tests cover later-round correction and a full-prefix
nullspace error that remains syndrome-consistent through four rounds and ends
`verify_failed`.

**Consequences**:
- Alice truth and verification-tag feedback are not decoder inputs.
- Transcript validation binds round, terminal prefix, incremental syndrome,
  tag, seed, epsilon, backend, calibration and candidate selection.
- Phase 6 must pre-register fresh confirmation, calibration binding, package
  DAG/verifier, gate and stop rules before execution.
- Engineering acceptance does not make the method comparison-eligible.

---

### 2026-07-26: Stop binary LDPC v3 after failed Phase 6 synthetic gate

**Decision**: Retain the strictly verified Phase 6B package as non-promoted
and do not create or execute the real Phase 6C lane.

**Context**: The TTBIN-derived calibration exposed strongly unequal Gray-plane
BER, reaching about .123 on plane 9. Fresh confirmation produced only 3/32
verified successes in the calibrated stratum and 1/32 under 1.25x stress,
against independent 31/32 gates. The remaining 60 frames were classified
`verify_failed`; integrity and accounting failures were zero.

**Consequences**:
- This is an algorithmic/code-channel mismatch, not a packaging/verifier
  failure.
- Real confirmation remains sealed by the synthetic hard gate.
- No confirmation tuning, rerun, real-data execution, or comparison claim is
  allowed.
- A successor requires a new decoder/code-design proposal and fresh synthetic
  confirmation.

---

### 2026-07-26: Pin the nonbinary N0 field contract before decoder selection

**Decision**: Implement the first `nbldpc_formal_v1` slice as a deterministic
internal polynomial-basis GF(2^m) contract for powers-of-two q through 1024,
with canonical field IDs and a read-only fail-closed preflight. Keep
`qldpc_reference` unchanged.

**Context**: The formal nonbinary lane needs an exact field representation and
q=1024 support before a soft-decoder backend or codebook can be evaluated.
The existing reference fallback stops at q=256 and its greedy hard decoder is
not a promotion candidate.

**Alternatives considered**:
- Relabel `qldpc_reference`: rejected because its implementation and evidence
  remain reference-grade.
- Install a large decoder/GF dependency immediately: deferred until a bounded
  N1/N2 contract identifies the smallest backend that satisfies the frozen
  interface.

**Consequences**:
- N0 establishes field-backend feasibility only. It does not establish
  decoder feasibility, qualification, promotion, or performance.
- Unsupported q, non-integral field inputs, field-ID mismatch, and arithmetic
  inconsistency fail closed without backend or lower-q fallback.
- N1 must define deterministic GF(q) codebooks, GF(q) rank, canonical bytes,
  and manifest hashes. N2 must separately freeze soft decoding and formal
  disclosure/Toeplitz accounting before experiments.

---

### 2026-07-26: Freeze the nonbinary N1 structural codebook family

**Decision**: Use a pure in-memory n=64 nonbinary family with one deterministic
32x64 mother matrix and exact 16/24/32 ordered prefixes. Verify rank over the
pinned GF(q), and identify every codebook and ordered family manifest through
canonical `NBLDPC1` bytes and SHA256.

**Context**: The formal lane needs immutable, rate-compatible codebook
identities before any soft decoder can be evaluated. Random reference matrices
and GF(2)/real rank would not provide that evidence.

**Alternatives considered**:
- Random sparse matrices: rejected because their topology and identity would
  not be a stable formal contract.
- PEG search or an external code-design dependency: deferred because the
  deterministic cyclic/protograph-style plus identity construction satisfies
  the bounded N1 structural contract without adding dependency or search
  nondeterminism.

**Consequences**:
- N1 has reproducible GF(q) ranks, prefix relations, canonical bytes, golden
  hashes, and fail-closed tamper verification for q through 1024.
- Structural rank/hash evidence is not decoder feasibility, distance/FER
  performance, qualification, promotion, or comparison evidence.
- N2 must freeze soft decoding and exact public-disclosure/Toeplitz accounting
  before decoder implementation, dependency selection, or experiments.

---

### 2026-07-26: Accept bounded nonbinary FFT-QSPA feasibility only

**Decision**: Use a pure full-message probability-domain FFT-QSPA as the first
bounded `nbldpc_formal_v1` decoder-feasibility implementation. Keep EMS and
min-sum as separately pre-registered alternatives rather than inventing an
unreviewed truncation/tail rule.

**Context**: The q=2^m additive group permits q log(q) Walsh-Hadamard check
convolution, while the pinned N1 matrices require exact nonzero GF(q)
coefficient permutations. The decoder must implement syndrome/coset semantics
without reading Alice truth, and q=1024 must fail closed under explicit
resource bounds.

**Consequences**:
- q=4 coefficient/coset messages agree with brute-force convolution, and a
  bounded q=1024 no-error case executes within the declared memory cap.
- Syndrome consistency remains distinct from locked Toeplitz verification;
  syndrome, tag, and public-control disclosure are separately accounted.
- These are unit-level engineering feasibility results, not general
  correction, FER/performance, calibration, qualification, promotion,
  real-data, production, or comparison evidence.
- N3 may not execute until development/confirmation isolation, claim domain,
  global policy, metrics/gates, resources/stops, artifacts/statuses,
  invalid-run handling, and strict verification are pre-registered.
### 2026-07-26: Nonbinary N3 is non-promoted and strict-verification-unverifiable

**Decision**: Retain the sole `nbldpc_formal_v1` N3 package unchanged as
non-promoted. Do not tune confirmation, rerun, or authorize N4 real-data work.

**Context**: The frozen q=1024 synthetic run selected margin 7, scale 1.0,
max_iter 10 and 32 checks. It achieved 18/32 verified successes at p=.20 and
5/32 at p=.30, below the independent 31/32 gates. The official strict CLI
verifier then failed only because live whole-worktree `git_status_sha256`
drifted post-execution. Source/CLI/contract hashes, commit, Python and NumPy
matched; a diagnostic `_test_only=True` replay checked artifacts/DAG/gates but
does not qualify as official verification.

**Consequences**: The seven artifacts at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`
remain immutable. No promotion, N4, real-data claim, performance comparison,
or confirmation retuning follows.

---

### 2026-07-26: Stop nonbinary LDPC v2 before confirmation

**Decision**: Retain the sole strictly verified `nbldpc_formal_v2` package as
`non_promoted_development`; do not generate confirmation or authorize N4.

**Context**: The selected QC48 tempered+damped policy used margin 8,
max_iter 10, and 32/40 checks for p=.20/.30. Fresh sacrificed development
achieved 0/24 and 5/24 verified successes, below the frozen 22/24 floor in
both strata. The sole execution and full deterministic replay both exited
successfully; scoped provenance passed.

**Consequences**:
- This is development non-readiness, not confirmation failure or FER.
- No confirmation rows/events were generated or executed.
- No rerun, tuning, N4 sidecar adapter, `.ttbin` processing, real-data claim,
  or comparison claim is authorized.

---

### 2026-07-27: Stop binary LDPC v4 at the production development gate

**Decision**: Retain the sole strictly verified
`20260727_v1_binary_ldpc_v4_development` package unchanged and stop before
fresh synthetic preparation. Do not create real qualification evidence,
retune, or rerun this package.

**Context**: The frozen plan executed all 40,960 candidate-plane outcomes and
the read-only verifier reconstructed source, channel, codebooks, selection,
accounting, and readiness without decoder reexecution. Nominal and stress each
had 0/512 frame successes and 5,120 forbidden
`development_decoder_error` plane outcomes, so neither met 495/512.

A subsequent no-decode constructor diagnostic identified a backend-boundary
implementation defect: `ldpc==2.4.1` rejects the NumPy `error_channel` passed
by `ldpc_v4_development.py` and requires a Python list. The formal v4 method
already performs that conversion. Consequently this package is not FER
evidence and cannot support a scientific rejection of the code family.

**Consequences**:
- No production v4 synthetic or real directory, data lock, execution, or
  qualification result exists.
- The immutable package and scoped source hashes remain the audit record.
- Fair Cascade/LDPC/Polar comparison remains blocked.
- Any continuation requires a new main-thread OpenSpec implementation
  correction with a production-constructor regression and newly versioned
  evidence. It must not be represented as a retry or parameter tuning of v4.

---

### 2026-07-27: Accept the versioned v4 backend correction at development

**Decision**: Accept
`20260727_v2_binary_ldpc_v4_development` as strictly verified,
development-ready evidence. Preserve both the failed v1 package and corrected
v2 package unchanged. Do not treat development readiness as qualification.

**Context**: The correction changed only the pinned decoder constructor
boundary from a NumPy float64 array to an equivalent Python list. All matrices,
channel probabilities, deterministic frames, decoder parameters, selection,
accounting, and the 495/512 gates were unchanged. The package achieved 510/512
nominal and 511/512 stress with zero forbidden failures. The read-only verifier
reconstructed predecessor, source, model, codebooks, selection, accounting,
and gates without decoder reexecution.

**Consequences**:
- The confirmed constructor defect is resolved for the versioned development
  path.
- Binary v4 is eligible for a separately reviewed fresh synthetic prepare.
- No synthetic promotion, real-data readiness, FER claim, or fair
  Cascade/LDPC/Polar comparison follows from this decision.
- Do not rerun or tune the immutable development package.

---

### 2026-07-28: Promote corrected binary v4 synthetic; wait for real capacity

**Decision**: Accept the strictly verified corrected-v2 synthetic package as
promoted. Do not prepare real qualification until the registered 128-frame
capacity exists independently in all three real strata.

**Context**: The fresh package achieved 127/128 nominal and 126/128 stress
with zero forbidden failures. Its eight CSPRNG roots and 256 Toeplitz seeds
are unique and disjoint from v3 and development. Read-only verification
reconstructed the full prerequisite/source/method/transcript/outcome/gate DAG
without decoder reexecution.

The current source has 117 complete frames in each of bw120, bw180, and bw200.
The frozen exclusion of 32 v3-reserved identities leaves 85 eligible, a
43-frame deficit against 128.

**Consequences**:
- Binary v4 has passed its independent synthetic qualification.
- Do not reuse v3-reserved real frames or lower the 128/126 gate to fit the
  current capture.
- Obtain traceable same-domain data, preferably at least 64 new complete
  frames per stratum, freeze an extended source manifest, and only then create
  one real lock/plan.
- No real `.ttbin` promotion or Cascade/LDPC/Polar comparison claim exists yet.

---

### 2026-07-28: Accept the v4 real-source intake layer

**Decision**: Accept the frozen source-extension builder, candidate pool, real
lock binding, and read-only reconstruction. Continue to block production real
prepare until a genuinely distinct same-domain acquisition is supplied.

**Context**: The only additional local 20 dB directory has byte-identical
main/chunk `.ttbin` hashes and is therefore a copy, not independent capacity.
The new intake rejects duplicate raw pairs and duplicate 256-symbol payloads,
binds all three q=1024 sidecars and their provenance, ignores rather than pads
natural incomplete tails, and deterministically reconstructs selection without
decoding.

Main-thread acceptance passed 3 source, 5 real, 7 bridge/source, and 25
backend/development/formal-real tests. The first broad regression used a
repository-internal temporary root and retained 8 environment failures; the
same suite passed 25/25 using its required external temp root.

**Consequences**:
- New data can be validated and frozen without modifying the historical v3
  bridge or inspecting real qualification outcomes.
- A copied or re-materialized registered capture supplies zero new capacity.
- Real prepare must bind a reviewed source-extension manifest and remains
  forbidden until all strata have at least 128 eligible frames.
- The next external input is a distinct 20 dB `.ttbin` main/chunk pair with
  traceable bw120/bw180/bw200 sidecars; prefer at least 64 complete frames per
  stratum.

---

### 2026-07-29: Retain the non-promoted 16 dB transfer and pre-register 10 dB

**Decision**: Retain the sole verified 16 dB transfer package as immutable
non-promoted evidence. Do not tune or rerun it. Pre-register one
unchanged-method transfer qualification on the independent 10 dB Type-II
capture.

**Context**: The 16 dB package completed all 384 denominators. bw120 achieved
125/128 against the frozen 126/128 floor; bw180 and bw200 achieved 128/128;
all forbidden counts were zero. Strict verification succeeded without decoder
reexecution or file changes. The 10 dB capture has 1108, 1111, and 1112
complete frames in the same q=1024 bw120/bw180/bw200 processing layers.

**Consequences**:
- The 16 dB and original 20 dB domains remain unpromoted.
- No v4 parameter, matrix, channel, decoder, leakage, cap, or gate changes are
  authorized for the 10 dB transfer.
- The 10 dB package must bind both the promoted synthetic prerequisite and the
  exact non-promoted 16 dB predecessor.
- A promoted result would establish only registered 10 dB transfer, not a
  general real-data or multi-loss claim.

---

### 2026-07-29: Reject 10 dB v1 at prepare review

**Decision**: Do not execute the v1 10 dB plan. Preserve its two files as
immutable `invalid_pre_execute` evidence and permit only a versioned v2
self-exclusion correction.

**Context**: v1 prepare completed without decoding, but strict post-write
validation rediscovered the current plan among prior real plans and therefore
collided with its own roots. This was detected at the required main-thread
review gate before execute.

**Consequences**:
- No 10 dB result has been observed and v1 is not qualification evidence.
- v1 must not be overwritten, deleted, or executed.
- v2 may exclude only its exact current plan SHA during validation.
- v2 must bind v1 and forbid all v1 roots and seeds; all scientific semantics
  remain unchanged.

---

### 2026-07-29: Retain 10 dB v2 non-promotion; develop v5 IR

**Decision**: Retain the strictly verified 10 dB v2 package as non-promoted.
Do not rerun v4 on 10 dB or move through easier losses until a pass appears.
Develop binary LDPC v5 using a pre-locked unused-frame development and
confirmation split.

**Context**: v2 achieved 125/128 at bw120, 127/128 at bw180, and 128/128 at
bw200, with zero forbidden failures. The misses were final Toeplitz
mismatches after complete fixed v4 syndrome decoding. The same fixed policy
also missed 16 dB by one frame, so rate/decoder robustness is the repeated
limitation.

**Consequences**:
- Reserve 512 unused development and 128 sealed confirmation frames per 10 dB
  layer before any v5 decoding.
- Screen only the pre-registered control, stronger OSD, and incremental
  syndrome policies.
- Count all added syndrome/tag disclosure and feedback; a pass with excessive
  leakage remains visible rather than being called free improvement.
- Require a fresh synthetic confirmation before the sealed real attempt.

---

### 2026-07-30: Retain nonbinary LDPC v3 synthetic non-promotion

**Decision**: Retain the sole strictly verified v3 covered-layered synthetic
package as immutable non-promotion evidence. Do not rerun, tune confirmation,
or begin N4/sidecar/`.ttbin` work.

**Context**: The selected layered-l075 margin-8 policy passed development
readiness at 23/24 for p=.20 and 24/24 for p=.30. Its sealed confirmation then
achieved 32/32 and 30/32 with zero prohibited failures. The frozen promotion
floor was 31/32 in each stratum, so p=.30 missed by one frame. The sole strict
read-only replay returned `verified=True`, `run_status=completed`, and
`promoted=False`.

**Consequences**:
- The new codebook and decoder route is implemented and qualified as a
  reproducible synthetic experiment, but is not promoted.
- Confirmation failures remain retained; no post-result parameter search or
  rerun is authorized.
- N4 and real `.ttbin` ingestion remain blocked by the synthetic promotion
  gate and require a new approved OpenSpec change even after promotion.

---

### 2026-07-31: Retain nonbinary LDPC v4 IR synthetic non-promotion

**Decision**: Retain the sole strictly verified v4 incremental-redundancy
package as immutable non-promotion evidence. Stop at A3; do not rerun, tune,
or begin N4/sidecar/`.ttbin` work.

**Context**: Development selected the warm 40→48/32→40 IR policy at 64/64 for
p=.20 and 63/64 for p=.30. Sealed confirmation achieved 128/128 at p=.20 and
120/128 at p=.30. All eight misses were `decode_failed`; there were zero
prohibited failures. The pre-registered gate was exactly 128/128 per stratum.
The sole verifier returned `verified=True`, `run_status=completed`, and
`promoted=False`.

**Consequences**:
- Preserve the complete eight-artifact package without overwrite or rerun.
- One extra eight-symbol syndrome prefix materially improved v3 but did not
  eliminate the p=.30 tail under the frozen decoder and codebook.
- A successor may investigate a stronger pre-registered rate-compatible
  family, additional extension stage, or decoder/codebook redesign only on
  fresh synthetic development data.
- Existing v4 confirmation failures are diagnostic evidence, not tuning data.
  Real-data eligibility remains blocked.

---

### 2026-08-01: Retain nonbinary LDPC v5a Route A synthetic non-promotion

**Decision**: Retain the sole completed v5a multistage-IR package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5a_nbldpc_multistage_synthetic`
as immutable non-promotion evidence. Do not rerun, tune confirmation, or begin
N4/sidecar/`.ttbin` work. Continue to Route B (task 5.1) as pre-registered.

**Context**: The frozen plan (development seeds 202607720000/730000,
confirmation 202607740000/750000, 128 frames per stratum, caps checks<=56 /
row weight<=8 / stage iterations<=12 / workers 1, probe 202607719999) executed
once: all 512 outcomes completed (`run_status=completed`, `outcome_count=512`).
Readiness passed (both strata >= 63/64) and confirmation material was
atomically materialized and executed. Promotion gates: p=.20 stratum 128/128,
p=.30 stratum 127/128 (one `decode_failed` tail miss), so `promoted=false`
against the frozen 128/128 floor in both strata. Zero prohibited failures.

The pre-registered strict read-only replay was attempted once and could not
run: between plan creation (git HEAD `71bda20d`) and the replay attempt, an
external session committed two unrelated changes (HEAD `3a5d96a`, binary LDPC
v1 sacrificed-development package and a Phase-2 verifier conformity fix;
neither touched any v5a source file). The frozen `_validate_plan` provenance
check therefore rejects the current HEAD. Source/CLI/contract hashes all
still match; only the `git_commit` provenance field drifted. This is an
external interference event, not a package defect; per at-most-once semantics
the strict replay is not rerun.

**Alternatives considered**:
- Reset HEAD to the plan-frozen commit and replay: rejected because it would
  discard another session's committed work.
- Re-run the strict verifier in a temporary worktree: rejected because
  untracked v5a sources and the official output path do not exist there; a
  mirrored environment would not verify the real package.
- Treat the blocked replay as package verification: rejected; the package
  remains "completed but replay-blocked" until a future window with matching
  HEAD re-enables the at-most-once strict replay.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized (no-rerun/no-tuning rules intact).
- Route B (`20260731_v5b_nbldpc_mother_synthetic`, roots 202607760000-
  202607790000) is next; Route A evidence does not establish codebook/decoder
  failure, only failure of the 128/128 promotion floor in the p=.30 tail.
- s6* shift-difference intersection deviation (task 1.3 UNSAT contingency:
  `mask_a ∩ mask6` replaced the full 6-element mask condition; recorded in
  codebook docstring and v5a acceptance evidence) is registered here as a
  formal deviation of the frozen design, not a gate or leakage change.
- Any later strict replay must happen only when the repository HEAD matches
  the plan-frozen commit, and remains an at-most-once action.

---

### 2026-08-01: Retain nonbinary LDPC v5b Route B synthetic non-promotion

**Decision**: Retain the sole completed v5b mother-redesign package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5b_nbldpc_mother_synthetic`
as immutable non-promotion evidence. Do not rerun or tune. Continue to Route C
(task 6.1) as pre-registered.

**Context**: NBLDPC5B (7 frozen 8-row block templates, disjoint-shift-
difference shift enumeration, salt 0, K=8 proxy candidates with w2=w3=0 —
zero weight-2/weight-3 syndrome collisions over the 56-row mother) ran once:
all 512 outcomes completed (`run_status=completed`, `outcome_count=512`).
Readiness passed in both strata; confirmation material was materialized and
executed. Promotion gates: p=.20 128/128, p=.30 127/128 (one tail miss), so
`promoted=false` against the frozen 128/128 floor. Zero prohibited failures.

The pre-registered strict read-only replay was attempted once and could not
run: between plan creation (git HEAD `3a5d96a`) and the replay attempt an
external session committed an unrelated `ldpc_v5_development` speedup (HEAD
`4dd6b7e`); the frozen `_validate_plan` provenance check therefore rejects
the current HEAD. Source/CLI/contract hashes all still match; only the
`git_commit` provenance field drifted — the same external-interference
pattern already recorded for v5a.

**Alternatives considered**:
- Reset HEAD or drop the external commit: rejected — would discard another
  session's committed work.
- Verify in a temporary worktree: rejected — untracked v5b sources and the
  official output path do not exist there.
- Treat the blocked replay as verification: rejected; the package remains
  "completed but replay-blocked" until a matching-HEAD window re-enables the
  at-most-once strict replay.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized.
- Route C (`20260731_v5c_nbldpc_decoder_synthetic`, roots 202607800000-
  202607830000) is next; codebook identity is fixed to NBLDPC5B (Route B ran
  and is non-promoted).
- A zero-short-weight-codeword mother did not close the p=.30 tail either;
  the remaining lever is the decoder family (damping-schedule FFT-QSPA vs
  truncated EMS), not further codebook search.
- Any later strict replay must happen only when the repository HEAD matches
  the plan-frozen commit, and remains an at-most-once action.

---

### 2026-08-01: Phase 2 speedup refactor and single re-execute approval

**Decision**: Accept the performance refactor of the Phase 2 execute/verify
path (commit `4dd6b7e`) with two formal deviations from the frozen
`phase2-task-packet.md` contract, and approve one fresh prepare/execute/verify
cycle to replace the invalidated official package. The new package
(`20260731_v1_binary_ldpc_v5_development`, plan_sha256
`287d17e825f5bc2a230de7e3b27a77fb99587a91c6057780b5d91d7df7f427d3`) is the
single executed package; the first attempt wrote zero artifacts
(`ValueError: plan frozen equality` — plan binds frozen source hashes and the
source changed under it) and the stale directory was deleted.

**Deviations (semantic-preserving, approved by main thread before re-execute)**:
1. Per-frame loader: `_execute` validates the partition lock once and builds
   rows from `lock["role_rows"]`; per-frame symbols now come from
   `_production_arrays_for_frame` (role membership check + cached
   `build_source_lock()`), replacing per-frame `development_arrays_for_frame`.
2. Verifier: source lock is built once per run instead of per frame; the
   full partition-lock rebuild is skipped for test-injected packages.

**Context**: The unmodified contract cost ~100 s per frame (partition-lock
validation inside the per-frame development loader) and ~0.086 s per frame in
the verifier — an estimated ~130 h wall clock for 4608 frames. The refactor
cut the test suite from 484 s to 97 s (29 passed, 1 skipped), and the official
execute completed in ~4.5 min with per-512-frame progress logs.

**Alternatives considered**:
- Keep the frozen contract and wait ~130 h: rejected as operationally
  unacceptable; speedup is behavior-neutral (verified by
  `test_production_array_loader_matches_locked_source` plus 29-test suite).
- Amend the plan in place: rejected; plans are immutable by design, the only
  legal path is one fresh prepare/execute/verify cycle.

**Consequences**:
- Official package verified once: EXIT=0,
  `{"decoder_reexecution":false,"outcomes":4608,"ready_for_synthetic_prepare":true,"run_status":"completed","selected_candidate_id":"V5-C2","status":"verified"}`.
- V5-C0/C1 are intentionally inactive control candidates (`active=False` in
  `ldpc_v5.py`); their 512x3 `backend_unavailable` rows are expected, not a
  defect.
- The speedup pattern (lock validated once, cached source lock, progress
  logs) is now the normal Phase 3/4 execute/verify path.

---

### 2026-08-01: V5-C2 real-data success promoted — success conditions and robustness boundary

**Decision**: Promote `V5-C2` (round-0 OSD_0/50-iter with H1, strong
OSD_CS/OSD-2/100-iter H1+H2 fallback, 64-bit Toeplitz verification) as the
main flow for binary LDPC v5 incremental redundancy, and proceed to Phase 3
(fresh synthetic confirmation). The promotion is based on verified real-data
success plus a pre-registered robustness argument.

**Context**: The official package verified 1536/1536 V5-C2 frames
(512/512 in bw120, bw180, bw200; fallback invoked 0/1536; SER quantiles
[0.0352, 0.0742, 0.0898, 0.1133, 0.1328, 0.1602, 0.2148]; runtime ~0.133 s;
h1 584 bits/frame). Robustness validation (`workspace/ldpc_v5_robustness/`):
- E1 seed/root independence: 768/768 verified with a fresh root set.
- E3 model-consistent boundary: 768/768 verified at the model's nominal SER
  0.2430 (adjacent +/-1 injected at the frozen calibration probabilities
  plus_one 3865/16384, minus_one 116/16384) — the decoder prior
  (`v5_plane_error_channel` hardcodes `adjacent_nominal`) exactly matches the
  injected distribution there.
- E2 out-of-distribution control: 0/1152 with uniform random symbol
  replacement (structure mismatch vs the +/-1 model) — expected and
  diagnostic, proving the error_channel prior is load-bearing.

**Success-condition analysis**: `plane_error_channel` is Bob-conditioned
(per-position error probability from the frozen calibration table only; it
never sees Alice). Correct decoding therefore requires the real noise to be
adjacent-bin +/-1 errors at rates at or below the frozen nominal table
(SER 0.243). Real frames satisfy this (max SER 0.215 < 0.243), so round-0
corrects everything and the strong fallback never fires. Failure is only
possible under out-of-distribution noise.

**Alternatives considered**:
- Keep C0/C1 as live candidates: rejected; they are intentionally inactive
  controls, not competing decoders.
- Require synthetic confirmation before promotion: deferred; the official
  package itself already gates `ready_for_synthetic_prepare=true`, and Phase 3
  remains the next mandatory gate before sealed real qualification.

**Consequences**:
- V5-C2 is the main v5 flow; Phase 3 synthetic package must still meet
  126/128 nominal and stress with zero forbidden failures before Phase 4.
- The robustness harness (`run_robustness.py`) is retained as reusable
  evidence infrastructure; results in
  `workspace/ldpc_v5_robustness/results.json` (E1/E2) and `results_e1e2.json`
  plus E3 in `results.json`.
- Any future SER-beyond-model evidence must be generated model-consistently
  (adjacent +/-1 at known probabilities); uniform-noise injections are
  recorded as OOD controls, not capability boundaries.

---

### 2026-08-01: Retain nonbinary LDPC v5c Route C synthetic non-promotion

**Decision**: Retain the sole completed v5c decoder-family package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5c_nbldpc_decoder_synthetic`
as immutable non-promotion evidence. Do not rerun or tune confirmation.
Continue to Route D (task 7.1) as pre-registered.

**Context**: The frozen plan (NBLDPC5B codebook identity fixed at plan freeze
because Route B ran and is non-promoted; dual policies `nbldpc_v5c_sched`
damped FFT-QSPA lambda 0.5/0.75/0.9 per 4-iteration quartile and
`nbldpc_v5c_ems` LLR min-sum nm=64 alpha=0.8; roots 202607800000-
202607830000; 128 frames, 640 development Toeplitz seeds) executed once with
`run_status=completed`. Readiness passed (both strata >= 63/64) and
confirmation material was atomically materialized and executed. Promotion
gates: p=.20 stratum 128/128, p=.30 stratum 127/128 (one retained tail
miss), so `promoted=false` against the frozen 128/128 floor in both strata.
Prohibited failures were zero.

The pre-registered strict read-only replay completed once and returned
`{'verified': True, 'run_status': 'completed', 'promoted': False}`; the
repository worktree status was unchanged by the replay.

**Alternatives considered**:
- Promote on 127/128 in the p=.30 tail: rejected; the frozen floor is 128/128
  in both strata and no-rerun/no-tuning rules remain intact.
- Tune the decoder policies against confirmation outcomes: rejected;
  confirmation is frozen evidence, not tuning data.
- Treat the result as codebook or decoder failure: rejected; it is failure of
  the promotion floor in the p=.30 tail only, the same pattern as v5a and v5b.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning is
  authorized (no-rerun/no-tuning rules intact).
- Route D (`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-
  202607870000) is next; the pre-registered list-stage + ADMM post stage is
  the remaining lever after codebook redesign (v5b) and decoder-family change
  (v5c) both left the p=.30 tail open.
- The replay succeeded in this window; the strict replay remains an
  at-most-once action.

---

### 2026-08-02: Retain nonbinary LDPC v5d Route D synthetic non-promotion; v5 change terminates

**Decision**: Retain the sole completed v5d post-processing package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5d_nbldpc_post_synthetic`
as immutable non-promotion evidence. Do not rerun or tune. Per the frozen
rule (task 7.4), with all four routes non-promoted the v5 multistage change
terminates with four immutable non-promoted packages; N4, sidecars,
`.ttbin`, real-data, and comparison claims remain locked.

**Context**: The frozen plan (run ID `20260731_v5d_nbldpc_post_synthetic`,
NBLDPC5B codebook via v5c delegation, dual policies
`nbldpc_v5d_sched_post`/`nbldpc_v5d_ems_post`, roots 202607840000-
202607870000, 128 frames, 640 development Toeplitz seeds, caps and gates
unchanged from the shared v5 contract) executed once with
`run_status=completed` and readiness true; confirmation material was
atomically materialized and executed. Promotion gates: p=.20 128/128,
p=.30 127/128 (one retained confirmation-frame `decode_failed`),
prohibited failures zero, so `promoted=false`. The pre-registered strict
read-only replay completed once and returned
`{'verified': True, 'run_status': 'completed', 'promoted': False}` with an
unchanged worktree.

Implementation corrections were approved and recorded during D1/D2
(module docstring + Verification Notes): the frozen x-update prior-term
sign was wrong (`+ prior/RHO`; correct proximal is `x = z - lambda -
prior/rho`) — a q=4 brute-force experiment showed codeword recovery jump
from ~0% to 87-100% after the fix; and the frozen z-update alternating
projection onto `{per-variable simplex AND output-sum = e_s}` is a strict
subset of the GF(q) check polytope and could not recover codewords — it
was replaced by the per-bit parity-relaxation projection (bitwise-XOR
linearization), which reached 100% exact recovery in the same experiment
(clean and noisy beliefs). A procedural deviation was also recorded: the
7.3 plan was created before the D1/D2 acceptance evidence file; it was
closed read-only at the same HEAD with the plan unchanged.

**Alternatives considered**:
- Promote on 127/128 in the p=.30 tail: rejected; the frozen floor is
  128/128 in both strata and no-rerun/no-tuning rules remain intact.
- Continue Route D tuning (larger list, more ADMM iterations): rejected;
  the list and ADMM bounds are frozen and confirmation is sealed evidence.
- Extend the change with a fifth route: rejected; the pre-registered
  stop rule terminates at four non-promoted routes.

**Consequences**:
- The eight-artifact package is immutable; no rerun or confirmation tuning
  is authorized.
- The v5 multistage change terminates: Routes A, B, C, D are all
  non-promoted with the same p=.30 tail pattern (127/128). Neither codebook
  redesign (B), decoder-family change (C), nor list/ADMM post-processing
  (D) closed the p=.30 tail at the 128/128 floor.
- N4, sidecar access, `.ttbin` processing, real-data qualification, and any
  comparison claim remain locked; a successor requires a new OpenSpec
  change with fresh development and confirmation data.
- The strict replay remains an at-most-once action; any later replay
  requires a matching-HEAD window.

---

### 2026-08-02: Nonbinary v7 R1A canary non-promotion → R1B

**Decision**: R1A (GF(1024) n=256 (2,3) mother, m=170, flooding FFT-QSPA
primary, max_iter 100) sacrificed canary achieved 0/4 verified success in
both strata (8/8 decode_failed at 100 iterations, zero forbidden statuses);
the pre-registered ladder gate fires failed_canary; R1A package frozen
immutably at the workspace canary dir; no rerun/tuning; R1B (one
multiplicative repetition, rate 1/6) is the authorized next route;
development-ready definition (>=15/16 per stratum, zero forbidden, strict
replay, disclosure <=8.75 bits/symbol excluding tag, median <=120 s/frame)
unchanged.

---

### 2026-08-02: Nonbinary v7 R1B canary non-promotion → R2

**Decision**: R1B (one multiplicative repetition of the (2,3) R1A mother,
rate 1/6 nominal, identity nbldpc_formal_v7_r1b_mr1) sacrificed canary
achieved p=.20 3/4 and p=.30 0/4 verified success (5 decode_failed at 100
iterations, zero forbidden statuses); multiplicative repetition improved
p=.20 (vs R1A 0/4) but did not close the p=.30 tail; the pre-registered
ladder gate fires failed_canary (any stratum 0/4); R1B package frozen
immutably; no rerun/tuning; R2 (QSC density-evolution ensemble) is the
authorized next route with its scientific identity requirement (DE must be
independently validated or the route stops implementation_blocked).

---

### 2026-08-02: Nonbinary v7 R2 canary non-promotion → R3

**Decision**: R2 (QSC density-evolution ensemble, identity
nbldpc_formal_v7_r2_qsc_de, DE validated against published BSC/BEC vectors,
per-stratum n=1024 codebooks with 321/458 checks) sacrificed canary achieved
0/4 verified success in both strata (8/8 decode_failed at 100 iterations,
zero forbidden statuses, execute ~21.9 min); the pre-registered ladder gate
fires failed_canary; R2 package frozen immutably at the workspace canary
dir; no rerun/tuning; R3 (GF(32)xGF(32) nonbinary multilevel, EMS nm=32
primary) is the final authorized route; if R3 also fails, the ladder closes
with a non-ready report (V7-40..42).

### 2026-08-02: Nonbinary v7 R3 engineering interrupted — resume state frozen

**Decision**: R3 engineering (identity nbldpc_formal_v7_r3_gf32x2,
reversible 10-bit → high/low 5-bit split, two GF(32) n=1024 codes,
layer-0-first, EMS nm=32 primary, max_iter 100) is PARTIAL on disk:
`formal_ir/nonbinary_v7_r3_codebook.py`, `nonbinary_v7_r3_long.py`, R3
CANARY/DEVELOPMENT configs in `nonbinary_v7_development.py`
(CANARY_R3/DEVELOPMENT_R3), and `tests/test_nonbinary_v7_r3_codebook.py`
exist; missing `tests/test_nonbinary_v7_r3_long.py`, additive harness tests,
T0-T3 runs, and `evidence/v7_r3_engineering_acceptance.json`. The Task tool
intermittently returned empty results or cancelled sessions (memory triage,
coder-fast runs, reviewer-go returns); every completed stage was verified on
disk before acceptance and fresh-session retries succeeded for R1A/R1B/R2.
No R3 plan/execution/official output exists; resume from the frozen partial
inventory (handoff: AGENT_HANDOFF.md current-state section; memory:
AGENT_PROJECT_MEMORY.md §35), then run the R3 canary gate and ladder
closeout (V7-40..42).

---

### 2026-08-04: Nonbinary v7 R3 canary non-promotion — ladder exhausted, closeout

**Decision**: R3 (identity nbldpc_formal_v7_r3_gf32x2, GF(32)xGF(32) two-layer
EMS nm=32 exact min-sum, reversible 10-bit split, layer-0-first conditional
layer-1 priors, m0=m1=404/558, disclosure 4040/5580 bits excluding tag,
3.945/5.449 bits/symbol) engineering was accepted (T0 19/T1 105/T2 33/T3 179,
10/10 independent review PASS); its sacrificed 4+4 canary was staged and
reviewed READY-FOR-SINGLE-EXECUTION, a minimal canary-only authorization edit
was applied, and the canary executed exactly once (exit 0, 668.8 s) and
strict-replayed exactly once (exit 0, 663.4 s) with per-stratum verified
success {0.20: 0, 0.30: 0} (8/8 decode_failed at max_iter=100, layer-0 failed
on every frame, zero forbidden statuses, verification never invoked). The
pre-registered canary gate fires -> failed_canary; R3 package frozen
immutably; no rerun/tuning/confirmation/real data; no official root created.
With R1A, R1B, R2, and R3 all `failed_canary`, no route reached
development-ready: **ladder_exhausted** (report
evidence/v7_ladder_report.md, V7-40 complete). No fourth route is invented;
any successor requires a NEW OpenSpec change with fresh development and
confirmation data, new roots, and its code/rate/decoder change frozen before
new development data; current confirmation rows are not tuning data.
Qualification/promotion/comparison claims remain unauthorized (V7-41/42
pending).

---

### 2026-08-04: Nonbinary V8 starts with reference reproduction, not another canary

**Decision**: Open change
`formal-nonbinary-ldpc-v8-reference-reproduction`. Preserve V7 evidence and
its `ladder_exhausted` result, while narrowing its scientific interpretation:
V7 T0-T3 engineering passed; its route canaries failed. R1B is retained only
as an algorithmic diagnostic because it synthesizes an additional independent
Alice-derived observation outside the project's single-Bob-observation IR
contract. R2's 0/8 applies to its scalar two-level DE surrogate, not to the
paper's full-vector q-ary density evolution. V8 shall implement error-domain
syndrome equivalence, an independent probability-domain oracle, full-vector
QSC MC-DE with edge-perspective degrees and channel terms, and one precisely
sourced published q-ary reproduction. V8 is engineering/reference-only: no
canary, development, confirmation, real/N4/comparison execution or official
output. A separate V9 may be proposed only after V8 acceptance.

---

### 2026-08-04: Nonbinary V8 reference reproduction complete and independently accepted

**Decision**: Accept `formal-nonbinary-ldpc-v8-reference-reproduction` as
implemented and INDEPENDENTLY REVIEWED ACCEPTED (reviewer-go, read-only,
2026-08-04, HEAD `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`). V8-A01..V8-A11
pass; V8-A12 is satisfied by the independent review (the operator did not
self-accept). V8 is engineering/reference-only: it authorizes no FER,
readiness, qualification, promotion, or comparison claim; only a separate V9
proposal follows.

**Context**:
- Additive files only (3 modules + 3 tests + 7 evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/`):
  `nonbinary_v8_error_domain.py` (error-domain contract d = H*(x+y),
  reconstruction x_hat = y + e_hat, pure field-tables-only helpers);
  `nonbinary_v8_reference.py` (independent direct probability-domain oracle:
  pairwise XOR convolution + sparse support enumeration + brute-force tiny-code
  coset/MAP, imports only GF2mField, import-boundary test enforced);
  `nonbinary_v8_mcde.py` (full-vector QSC Monte-Carlo density evolution:
  length-q messages, edge-perspective degree distributions with tested
  node/edge conversion, exact sampled degrees, fresh channel message at every
  variable update, direct convolution without FWHT, base-q mean entropy
  convergence, seeded deterministic, fail-closed; golden regressions detect
  old R2 missing-channel and fixed-`dv_max` behavior).
- Tiers (`pytest -q -p no:cacheprovider`, fresh
  `workspace/nbldpc_v8_reference_9c3f51e2a74b48d9b6c0a5f8e1d23a4b` root):
  T0 11/0, T1 31/0, T2 3/0 (read-only reproduction-trace + source-manifest +
  no-production-runner verification), T3 179/0 (frozen 16-file
  v5+v6+v7-R1A/R1B/R2 regression subset, exact frozen file list). The reviewer
  re-ran T0/T1/T2: identical.
- Published reproduction (single frozen run, no rerun/tuning): Muller et al.,
  "Efficient Information Reconciliation for High-Dimensional Quantum Key
  Distribution", Quantum Inf Process 23, 195 (2024), arXiv:2307.02225v2,
  Section 3.1 Table 1 row "0.75": q=4, rate 0.75, DET 0.069, EEff 1.053,
  edge-view lambda with coefficients
  `0.107x+0.245x^3+0.192x^6+0.034x^9+0.207x^18+0.161x^25+0.049x^27`
  (paper Eq. 13: exponents are degree-1, so DE degrees {2,4,7,10,19,26,28});
  concentrated two-point check distribution inferred from the fixed rate:
  dc_mean = 1/((1-R)*sum(lambda_d/d)) = 24.3285893 -> {24,25} (documented
  inference; provenance record `evidence/v8_literature_provenance.json`;
  verbatim extract `evidence/v8_muller2024_table1_extract.txt` SHA256
  `d343f0204e87994e64efd32531bc12490fb4e7125cd90b52cfaf2397279b57bd`). Frozen
  params: seed 2026080418, 20000 nodes, max 200 iterations, entropy
  convergence < 0.01 base-q for 20 consecutive iterations, binary search p in
  [0.01, 0.12] step 0.0025, frozen tolerance 0.015. Result:
  threshold_proxy 0.062421875, delta vs 0.069 = 0.006578 <= 0.015 -> PASS;
  full probe trace in `evidence/v8_reproduction_trace.json`.
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real-data/N4/comparison execution; frozen
  `src/`/`experiments/`/`tools/`/`results/` and all V1-V7 files unchanged
  (git status/diff empty); nothing staged.
- Evidence: `evidence/v8_engineering_acceptance.json` (schema
  v8_engineering_v1; source manifest with SHA256 of the 6 additive files;
  pre-test manifest `evidence/v8_source_manifest.json` re-verified read-only;
  one recorded manifest delta for a test-file assertion addition, all tiers
  re-verified); `evidence/v8_v7_interpretation_audit.md` (R1B =
  out-of-contract extra-observation diagnostic; R2 = unvalidated scalar-DE
  surrogate result; V7 T0-T3 engineering PASS distinct from canary failures);
  `evidence/v8_v9_recommendation.md` (V9 lead: paper-faithful syndrome
  reconciliation with a reproduced ensemble and blind puncturing/shortening,
  fresh roots, separate OpenSpec change; NOT implemented).

**Consequences**:
- V8 is closed; nothing remains for V8 except a future separate V9 proposal.
- No FER, readiness, qualification, promotion, or comparison claim is made
  from V8.

---

### 2026-08-04: Nonbinary V8-60 audit-correction close-out

**Decision**: Record V8-60 as a **non-tuning formula correction** discovered by
an independent audit of the accepted V8 candidate: (a) `concentrated_check_distribution`
previously matched the two-point MEAN check degree (`w_lo = dc_hi - dc_mean`),
which only approximates the edge-perspective rate condition
`sum_j rho_j/j = (1-R)*sum_i lambda_i/i` (relative error ~1e-4); corrected to
solve it exactly for adjacent check degrees `{floor(dc), ceil(dc)}` with
`w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`,
`target = (1-R)*integral_lambda`, `dc = 1/target` (integer `dc` degenerates to
the regular degree); new public helper
`reconstructed_rate(lambda_edge, rho_edge) = 1 - (sum rho_j/j)/(sum lambda_i/i)`;
tests assert `|reconstructed_rate - rate| <= 1e-12` (5 configs). (b) The
`REPRODUCTION_CITATION` first author was corrected from the wrong given name
"Rasmus T. Müller" to "Ronny Müller" (full arXiv:2307.02225v2 author list).
(c) The frozen tolerance justification `0.005+0.003+0.0025=0.015` was
arithmetically invalid; replaced by `0.0005` (3-decimal published rounding) +
`0.00125` (p_tol/2) + `0.005` (our MC-DE finite-sample error at 100000 nodes)
+ `0.005` (paper MC-DE error at its 100000 nodes) = `0.01175 <= 0.012`; frozen
tolerance 0.012.

**Context**:
- Corrective reference run (exactly once, parameters frozen BEFORE the run):
  q=4, R=0.75, Muller et al. 2024 Table 1 row 0.75 (DET published 0.069),
  concentrated rho `{24: 0.6623423944, 25: 0.3376576056}` (dc_mean 24.3285893
  unchanged), n_samples 100000 and max_iter 150 (the paper's own MC-DE budget),
  seed 2026080418, p in [0.01,0.12] step 0.0025, entropy < 0.01 base-q for 20
  consecutive iterations. Result: threshold_proxy 0.062421875, delta
  0.006578125 <= 0.012 -> PASS; full probe trace in
  `evidence/v8_reproduction_trace_corrected.json`. No rerun, no tuning.
- History preservation: `evidence/v8_reproduction_trace.json` preserved
  byte-identical (SHA256
  `dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3`) and
  marked as the pre-correction approximate trace via
  `evidence/v8_reproduction_trace_precorrection_annotation.json`;
  `evidence/v8_engineering_acceptance.json` NOT rewritten (its A12=blocked
  status is explicitly resolved by the new
  `evidence/v8_acceptance_closeout_addendum.json`, main-thread V8-60.10);
  `v8_literature_provenance.json`, `v8_muller2024_table1_extract.txt`,
  `v8_v7_interpretation_audit.md`, `v8_v9_recommendation.md` unchanged.
- Golden regressions: q=4 golden re-recorded under the corrected rho
  `{4: 1/6, 5: 5/6}` (same seed/config; recording not tuning);
  omitted-channel and fixed_max tamper modes still differ (old-R2 detection
  preserved); q=8 golden byte-identical (regular `{6:1.0}`).
- Tiers (V8-60.8 scope, no T3): compile exit 0; T0 17 passed / 0 failed;
  T1 32 passed / 0 failed; T2 4 passed / 0 failed (reproduction-trace +
  source-manifest + no-production-runner + precorrection-preservation, all
  read-only). Independent reviewer-go re-ran T1 32/0 and T2 4/0: identical.
- Independent review (V8-60.9): reviewer-go ACCEPTED the corrected candidate;
  `evidence/v8_independent_review_acceptance.json` written (review scope,
  re-run commands/results, source hashes, V8-A01..A12 conclusions; A12
  resolved pass by this review). Blocking findings: none. Non-blocking:
  `v8_v9_recommendation.md` cites pre-correction run numbers (direction
  unaffected; corrected numbers supersede); cosmetic duplicated REPO_ROOT
  line; pre-existing package `__init__` binding (test scopes correctly).
- Evidence inventory (new in V8-60): `v8_reproduction_trace_corrected.json`,
  `v8_reproduction_trace_precorrection_annotation.json`,
  `v8_60_correction_evidence.json` (formula/constants old->new, tolerance
  arithmetic, source-hash old->new; only `nonbinary_v8_mcde.py` and
  `test_nonbinary_v8_mcde.py` changed: new hashes
  `2c84a5ee76d09f4d6cea537289ff82d88ab19abd31d1a41951a7d24acdd66543` /
  `a508a4228ee06114424db2242b4db784bfa1b9cabcbae54f4cd7172ed988a81f`),
  `v8_independent_review_acceptance.json`, `v8_acceptance_closeout_addendum.json`;
  `v8_source_manifest.json` regenerated with a `v8_60_delta` field (old hashes
  remain in the original acceptance).

**Consequences**:
- V8-60.9 and V8-60.10 are complete; V8-60.11 remains open until the memory
  agent writes AGENT_PROJECT_MEMORY.md section 39.
- The corrected formula, citation, and tolerance supersede the pre-correction
  records; the original evidence remains byte-identical.
- V8 remains engineering/reference-only; no V9 implementation, no
  canary/development/confirmation/real-data/N4, no official output, no
  staging/committing/pushing; only a separate future V9 OpenSpec proposal is
  authorized.
- Nothing remains for V8; the pre-correction evidence stays byte-identical and
  the corrected numbers supersede it.

---

### 2026-08-04: Authorize gated V9 GF(1024) ensemble-to-long-block route

**Decision**: Create OpenSpec change
`formal-nonbinary-ldpc-v9-gf1024-long-ir` and authorize its frozen state
machine V9A -> V9B -> V9C. V9A first validates scalable full-vector GF(1024)
MC-DE and separate p=.20/.30 robust f=1.15 and target f=1.08 ensembles. Robust
multi-seed thresholds must reach .22/.32 before a finite codebook exists.
Passing stages may advance autonomously to n=4096, n=16384, and n=32768
synthetic canary/development; any failed gate freezes evidence and stops.

V8 q=4 validates method/audit machinery only, not GF(1024) threshold or FER.
V9C stops after the n=32768 16+16 development decision. Qualification,
confirmation, real/N4, promotion, and formal comparison remain unauthorized.
Full formulas, resource gates, lifecycle rules, and acceptance IDs V9-A01..
V9-A16 are frozen in the new change and `docs/nonbinary-ldpc-v9-plan.md`.

**Specification correction after independent freeze review**: V9A robust
candidates use conservative .22/.32 gates; target uses .215/.32 (.215 remains
below the p=.20 f=1.08 capacity threshold ~.21827). All four searches
plus multi-seed validation form one reviewed, once-executed, once-replayed
package. n=4096/16384/32768 bind 4/16/32 disjoint constituents respectively;
all finite matrices require `rank(H)=m`. n=32768 canary uses hard 24h timeout
and median <=16h. V9C uses fixed rates only: `m=ceil(f*H_q(p)*n)`, syndrome
`L_recon=10*m`, separate 64-bit tag, `L_total=10*m+64`, with no other
reconciliation payload. Blind adaptation is prohibited in V9 and deferred to
V10.

### 2026-08-04: V9A ensemble gate fails — frozen STOP before codebooks

**Decision**: V9A stops at the ensemble gate. No finite codebook, decoder,
canary, development run, qualification, real/N4 data, promotion, or formal
comparison will be produced under `formal-nonbinary-ldpc-v9-gf1024-long-ir`.

**Context**: V9A executed exactly once under the v2 budget protocol (pid 5084,
3968.5 s, peak RSS 428.3 MiB) and was strict-replayed exactly once (pid 29340,
4838.5 s, peak RSS 451.5 MiB). Scientific outputs are deterministic and
byte-identical between execute and replay; only `run_meta.json` differs in
provenance fields. All four searches (S1 robust p=.20 f=1.15 gate .22; S2
target p=.20 f=1.08 gate .215; S3 robust p=.30 f=1.15 gate .32; S4 target
p=.30 f=1.08 gate .32) recorded zero eligible candidates: every one of the
32 candidate screens at the gate p failed to converge in 150 iterations (final
entropy 0.66-0.93, final error 0.08-0.31). The conservative threshold is
undefined for every gate.

Capacity context (informational only): S1 p*=0.2345, S2 p*=0.2183, S3
p*=0.3527, S4 p*=0.3279. The gates sit below capacity, but the frozen
8-candidate population of 3-term lambda mixtures with harmonic-exact
concentrated rho did not approach it.

**Alternatives considered**:
- Tune the candidate population or expand the search budget: rejected because
  the plan was frozen before any result and a failed execute is immutable.
- Lower the robust gate to match the observed proxies (~0.19-0.20 for S1):
  rejected because that would redefine the frozen gate after seeing the result.
- Advance to V9B anyway with the best non-eligible candidate: rejected because
  the plan requires an eligible/searched winner with a conservative threshold
  before any finite codebook exists.

**Consequences**:
- Evidence is frozen under
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/`.
- The replay script's missing guard on the shared
  `evidence/v9a_execute_results.json` path caused an overwrite; the original
  execute version was restored from `v2_execute/evidence_v9a_execute_results.json`.
- V9B/V9C are unreachable. A successor nonbinary LDPC lane would require a new
  OpenSpec change with fresh roots, a different ensemble family, and new
  development/confirmation data.

### 2026-08-05: V9A acceptance and archive complete

**Decision**: The V9A package passed independent review and the change
`formal-nonbinary-ldpc-v9-gf1024-long-ir` was archived (STOP at the ensemble
gate).

**Context**: reviewer-go accepted the V9A evidence package read-only (all
checklist items pass, no blocking issues). Independent SHA256 verification
confirmed 9/11 execute/replay files byte-identical; the 2 differing files
(`evidence_v9a_execute_results.json`, `run_meta.json`) differ only in
provenance fields (pid/start/end/elapsed/peak_rss/command). The official
execute evidence hash matches the v2_execute copy
(`540295123a8a19f3f335f727339df14f4c1106fc01cccab46ecb644dd1eedb8c`).
Acceptance record: `evidence/v9a_independent_review_acceptance.json`.

The generic openspec archive CLI rejected the change (its `verifyChange`
requires numeric `- [ ] 1.1` task IDs and all tasks checked; this project uses
custom `- [x] **V9-XX.Y**` task IDs and V9-30..V9-70 are legitimately
unchecked as unreachable after the frozen STOP). The archive was therefore
performed as the CLI's underlying operation — a dated directory move — exactly
as prior project archives were done.

**Alternatives considered**:
- Rewrite tasks.md to the CLI's numeric format and check all boxes: rejected
  because it would falsify the record (V9B/V9C tasks were never done).
- Run the CLI anyway: rejected because `verifyChange` hard-fails on the
  custom task format and on any pending task.

**Consequences**:
- Change moved to
  `openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/`
  (all 6 artifacts: proposal, design, tasks, specs, packet, evidence).
- Delta spec NOT synced into `openspec/specs/` (per user choice: the
  unattained V9B/V9C requirements must not become canonical spec).
- No V9B/V9C artifacts exist; no scientific command was executed during
  close-out or archive.
- Successor nonbinary LDPC work requires a new OpenSpec change with fresh
  roots, a different ensemble family, and new development/confirmation data.

---

### 2026-08-06: Nonbinary V10 fails at the ensemble gate — failed_ensemble, V11 successor

**Decision**: Terminate `formal-nonbinary-ldpc-v10-de-peg-fftqspa` with final
state `failed_ensemble` (`evidence/v10_gate_decision.json`, schema
`v10_gate_decision_v1`). V10A GF(1024) four-search density-evolution ensemble
gate failed (hard stop V10-S02); V10-30 (PEG), V10-40 (FFT-QSPA), V10-50
(canary), and V10-60 (development) are all HALTED. There is no "closest to
gate" candidate, no rerun, and no tuning. The successor is a brand-new V11
NB-SC-LDPC OpenSpec change (fresh everything: new change, new roots, new
development/confirmation data).

**Context**:
- V10-0 q=4 reference-recovery gate PASS: conservative threshold 0.06414,
  |δ| = |0.06414 − 0.069| = 0.00486 ≤ 0.012; main-thread accepted
  2026-08-05.
- V10A searches: S1 (p=.20, f=1.15) conservative 0.2153 < 0.22 FAIL; S2
  (p=.20, f=1.08) conservative 0.1984 < 0.215 FAIL; S3 (p=.30, f=1.15)
  conservative 0.3166 < 0.32 FAIL; S4 (p=.30, f=1.08) no eligible candidate
  FAIL. Triggered hard stop V10-S02.
- Execution record: V10A executed once (~10470 s, peak RSS 335 MB < 3 GiB);
  the first replay attempt was interrupted (PID 21032 died after S1 only);
  per precedent, the replay was rerun in `replay_attempt2/` and completed
  (04:36–07:07Z, RSS 339 MB). Direct byte comparison PASS across 129 files:
  scientific files byte-identical; only provenance normalization differs
  (plan_binding digest key and run_complete role/stage).
- 2026-08-06 protocol amendment (main-thread directive): per AGENTS.md §5.7,
  defensive SHA-256/checksum/integrity-manifest mechanisms were removed
  (plan-bound digest, manifest self/source hash, per-file compare sha256,
  etc.); replacements are git baseline checks, direct byte comparison,
  structured field validation, and semantic recomputation. `v10_seed` is
  retained as a deterministic RNG derivation primitive (DE population
  initialization and mutation RNG streams depend on it; completed results
  depend on its byte reproduction). Amendment record:
  `evidence/v10_protocol_amendment_no_hash_v1.json`.
- Evidence files (change `evidence/`): `v10a_execute_results.json`,
  `v10a_replay_evidence.json`, `v10a_gate_decision.json`,
  `v10_gate_decision.json`, `v10_t3_regression.json` (git baseline PASS,
  frozen directories zero change), `v10_protocol_amendment_no_hash_v1.json`.
- Tests: full V10 suite 89 passed (common 23 / de 24 / gate 13 / peg 12 /
  fftqspa 17).
- Frozen baseline: git HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`; `src/`, `experiments/`,
  `tools/`, `results/` zero change; no new output under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; the 12 tracked
  modifications are pre-existing dirty-worktree entries of other workflows.
- V10-30.DESIGN task (PEG no-hash design note) remains unchecked and is left
  for future V11 inheritance.

**Alternatives considered**:
- Report a "closest to gate" candidate: rejected — the gates are
  pre-registered absolute thresholds; no candidate reached them, and naming a
  closest value would imply partial success or tunability.
- Rerun or tune (expand search budget, adjust population): rejected — the
  failed execution is immutable and no-rerun/no-tuning rules remain intact.
- Advance to V10-30 with the best non-eligible candidate: rejected — the
  hard stop V10-S02 requires all gates to pass before any finite codebook.

**Consequences**:
- V10 terminates at `failed_ensemble`; no codebook, decoder, canary,
  development, qualification, real-data, promotion, or comparison output was
  produced under this change.
- The successor is a new V11 NB-SC-LDPC OpenSpec change with fresh roots,
  fresh development/confirmation data, and its code/rate/decoder change
  frozen before new data; starting V11 is a user decision.
- `v10_seed` remains a deterministic RNG primitive; the other defensive hash
  mechanisms were removed per the 2026-08-06 amendment and must not be
  re-added to new evidence without a new decision.
- V10-30.DESIGN (PEG no-hash design note) is inherited by V11, unchecked.
- S4 delta correction (2026-08-06): `evidence/v10_s4_delta_correction.json`
  (schema `v10_s4_delta_correction_v1`) records that the S4 `delta` field in
  `evidence/v10a_gate_decision.json` was a boolean false from the
  build_evidence short-circuit bug; correct semantics is null. The evidence
  file was not overwritten; the script expression was fixed for future reuse.
  The S4 FAIL verdict and the `failed_ensemble` conclusion are unaffected.
- Independent final review (2026-08-06): reviewer-go ACCEPT recorded in
  `evidence/v10_independent_review_acceptance.json` (schema
  `v10_independent_review_acceptance_v1`; 89 tests pass, covering the S4
  correction record).

---

### 2026-08-06: Freeze V11 as a spatially coupled DE-only successor

**Decision**: Create `formal-nonbinary-ldpc-v11-sc-de-gate` as a plan-only
OpenSpec change. V11 first reproduces published q=4/q=16 QSC coupled and
uncoupled SMP thresholds, then validates a separate full-vector coupled MC-DE,
and finally tests the frozen V10 robust S1/S3 ensembles under equal effective
rate. The only formal geometries are G1 `(w=1,L=32,W=8)`, G2
`(w=2,L=32,W=16)`, and G3 `(w=2,L=32,W=32)`.

**Rationale**: The direct QSC literature supports a spatial-coupling gain but
uses simplified symbol-message passing; BEC/AWGN threshold-saturation results
do not by themselves validate GF(1024) HD-QKD full-vector behavior. A dual
reference gate prevents those claims from being conflated. Equal-rate
termination compensation and paired uncoupled controls isolate coupling from
extra leakage.

**Consequences**:
- Passing requires conservative S1/S3 thresholds of .22/.32 and at least .002
  paired gain in both strata.
- Reference mismatch, resource excess, or no passing geometry stops as
  `failed_reference`, `resource_blocked`, or `failed_coupling` respectively.
- V11 stops at `ready_for_finite_length`; it cannot construct a finite code,
  run FFT-QSPA/canary/real data, or make qualification/promotion claims.
- V11-P04 independent freeze review is required before implementation or any
  scientific execution.

---

### 2026-08-12: Binary LDPC v5 sealed real qualification promoted on real 10 dB ttbin

**Decision**: Accept the sealed real qualification of binary LDPC v5 on the
independent 10 dB Type-II capture: 384/384 verified successes (bw120, bw180,
and bw200 each 128/128) with zero forbidden failures and `promoted=true`.
This is the first real-data promotion for binary LDPC.

**Context**: The full pre-registered chain completed, each stage exactly once
with read-only verification: 20260731 partition lock → 20260731 v5
development (V5-C2, 1536/1536) → 20260801 v5 synthetic (256/256, promoted) →
20260801_v2 real (384/384, promoted). The official ten-file package is
`comparison_bench/outputs_comparison/formal_ir_methods/20260801_v2_binary_ldpc_v5_real/`
(run_id `binary_ldpc_v5_real_qualification_v1`, plan_sha256
`a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`, report
sha256 `18b5566ed636a79473ff7290cb55d90d4ab20a170895b53f786ea2455ad953d5`).
Report fields: `promoted=true`, `run_status=completed`,
`decoder_reexecution=false`. Execute took ~5m12s and read-only verify ~4m29s,
run in a detached background process on 2026-08-12.

The CSV role uses the frozen encoder's allowed `real` value: the contract's
literal `real_confirmation` is rejected by the encoder, the same precedent as
Phase 3. During implementation, three latent bugs masked by test mocks were
found and fixed (synthetic_dir directory semantics, generator empty-dict
check, missing root_id); the fixes are semantic-preserving and do not change
the scientific result.

**Alternatives considered**:
- None: the qualification is pre-registered and gated; alternatives would
  apply only on a failed gate, which did not occur.

**Consequences**:
- The promotion is limited to the 10 dB Type-II, q=1024, Gray, 256-symbol,
  bw120/bw180/bw200 domain with the V5-C2 strategy. It does not extend to v4,
  the 16 dB/20 dB captures, other acquisitions, nonbinary LDPC, or any
  Cascade/Polar comparison claim.
- v4's two real transfers (16 dB 125/128 and 10 dB v2 125/128, both below the
  126/128 gate) remain retained non-promoted failure evidence; v5 is the
  first all-green real 10 dB Type-II promotion.
- Comparison eligibility is updated: binary LDPC v5 may participate in
  comparison within the promoted 10 dB domain; all other domains and methods
  keep their prior status. Binary/nonbinary parallel status: binary v5
  promoted; the nonbinary lane is unchanged.
- A rate-adaptive successor requires a separate new OpenSpec change.

---

### 2026-08-11: V11 spatial-coupling hypothesis rejected — `failed_coupling`

**Decision**: Terminate `formal-nonbinary-ldpc-v11-sc-de-gate` with final
state `failed_coupling` (`evidence/decision/final_gate_decision.json`, schema
`v11_final_gate_decision_v1`). The V11 spatial-coupling hypothesis is
rejected: none of G1/G2/G3 reached the frozen dual gates (S1 ≥ .22 and S3 ≥
.32), and every paired conservative gain is negative. V11 ends honestly at
`failed_coupling`; no silent promotion is made.

**Context**: Under the frozen V10 S1/S3 lambda distributions and the frozen
G1 `(w=1,L=32,W=8)`, G2 `(w=2,L=32,W=16)`, G3 `(w=2,L=32,W=32)` geometries,
the coupled conservative thresholds were S1 G1 .2100 / G2 .2025 / G3 .2019
(all < .22) and S3 G1 .3125 / G2 .3000 / G3 .3000 (all < .32); paired gains
were all negative (S1 -0.0075 / -0.0144 / -0.0156 and S3 -0.0137 / -0.0256 /
-0.0206). The scientific matrix executed 60/60 runs once (2026-08-08,
execution root `workspace/nbldpc_v11_execute_002d51de/`); the strict replay
was 60/60 byte-identical on science fields from a fresh workspace
(`workspace/nbldpc_v11_replay_8e63bf62/`). Independent final acceptance
(reviewer-go V11-50.3) recomputed 12 conservative aggregates + 6 paired gains
+ 3 gate verdicts, all consistent (16/16 A01-A16 PASS).

**Alternatives considered**:
- Silent promotion or describing a "closest to gate" geometry: rejected —
  the gates are pre-registered absolute thresholds and no silent promotion of
  failures is allowed (design.md §6, A15).
- Retune parameters/ensembles and rerun: rejected — the failed execution is
  immutable and no-rerun/no-tuning rules remain intact.
- Shrink the matrix (drop a geometry/stratum or relax the gates after seeing
  the result): rejected — it would redefine the frozen plan after the result.

**Consequences**:
- V11 stops at `failed_coupling`; the provisional `failed_reference` in the
  execution-root summary was a checks-pending placeholder and is superseded by
  the final decision file.
- No finite code, decoder, canary, development, qualification, promotion, or
  comparison output was produced under this change.
- Finite-length/lifting, windowed FFT-QSPA, decoder, canary, real-data,
  qualification, and promotion work all require a new OpenSpec change with
  fresh roots and fresh development/confirmation data (design.md §6/§8).
- Resource budget (15.83 h < 24 h, peak RSS 2.82 GiB < 3 GiB) and rate
  contract passed; the failure is purely scientific (no threshold gain from
  spatial coupling under the frozen distributions and geometries).

---

### 2026-08-13: V12 nonbinary LDPC real micro-feasibility: source_partition_blocked

**Decision**: V12 terminated with terminal state `source_partition_blocked`. The
four-frame bw200 micro-feasibility canary cannot be executed because the
reconstructed traceable 10 dB pool (2304 rows, 768 per stratum) is 100%
covered by historical frame/payload identities from the V4 10 dB/16 dB
transfer locks (20260729_v1/v2) and V5 development/partition role locks
(20260731_v1): 2848 excluded frame + 2688 excluded payload identities, zero
eligible bw200 rows. Implementation (V12-I01..I05) and engineering acceptance
(V12-T0..T2, 41/41 tests) completed; prepare lane (RP01-RP03) produced the
official package
`comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
(v1 intermediate package deleted by explicit user decision). No successor,
rerun, tuning, replacement, or promotion is automatically authorized.

**Context**: V12 asked whether the frozen finite GF(1024) R1 baseline
(unchanged V7 R1A matrix, p=.20 prior, full 170-row syndrome) can produce an
independently verified exact correction on four fresh compatible real frames;
the partition-freeze step found zero collision-free rows in the existing pool.

**Alternatives considered**:
- Reuse historical frames: rejected — cross-history frame/payload exclusion is
  frozen in V12-P05 and design §4.
- Relax the exclusion inventory: rejected — the identities are genuinely
  shared with prior V4/V5 real packages; relaxing would break freshness.
- Fresh acquisition now: deferred — out of V12 scope; requires new capture and
  a new OpenSpec change.

**Consequences**: V12 stands as a documentation + engineering deliverable with
terminal state `source_partition_blocked`; no finite decoder correction was
established for the existing pool; any future canary requires a fresh
acquisition and a new OpenSpec change. Claim boundary: V12 never establishes
success probability, FER, threshold, qualification, or promotion.

---

### 2026-08-14: 先用现有数据诊断非二元 LDPC，不以重新采集为前置

**Decision**: 用户决定先使用现有 10 dB Type-II、q=1024、Gray、256-symbol
数据做非二元 LDPC 的 retrospective diagnostic/development 规划，不把
重新采集设为 V13 的前置条件。V13 change
`formal-nonbinary-ldpc-v13-existing-data-diagnostics` 仅处于
`PLAN DRAFTED / EXECUTION NOT AUTHORIZED`；本轮只请求独立只读 freeze
review，不请求 decoder 或真实数据执行。

**Context**: V12 的 `source_partition_blocked` 是 freshness/identity
partition 失败：已有 10 dB 池中的 768 个 bw200 行均已被 V4/V5 历史
frame/payload identities 覆盖，而不是数据量为零。现有行可用于 channel
统计、接口/数值诊断和事后 exact-correction 检查，但不能被称为 fresh
canary、confirmation、qualification 或 promotion evidence。

**Frozen boundary**: V7 R1A、V10 `failed_ensemble`、V11
`failed_coupling`、V12 `source_partition_blocked` 的含义不改写；binary
V5 同域 384/384 仅作 frame-difficulty/control 参照，不复制其 leakage、
prior 或模型。Alice truth 仅可进入离线 aggregate 与事后 exact check；
公共 telemetry 不保存 raw arrays 或逐位置 error mask。bw200 是 primary，
bw120/bw180 只能在 bw200 根因结论之后做预注册 cross-stratum check。

**Artifact naming**: future diagnostics use the six-file additive package;
`diagnostic_outcomes.csv` contains baseline, candidate-development, and
retrospective-audit rows with explicit `phase` and `method` fields. The
diagnostic CSV name is frozen to `diagnostic_outcomes.csv`.

**Consequences**: P01--P07 只在文档中 drafted，P08 独立 freeze review
尚未完成；所有 D/R/I/E/A/C 均未授权。即使未来诊断全绿，最高状态也
只是 `ready_for_fresh_confirmation`。fresh acquisition、正式
qualification 或 promotion 必须另开 OpenSpec change 并由用户决定；V12
仍保持 `source_partition_blocked`，不重开 X01/X02。

---

### 2026-08-14: V13-D04 baseline probe — 主线程授权、实现并执行一次

**Decision**: 主线程授权执行 V13-D04（unchanged V7 R1A `p=.20` baseline
probe，32 个预注册 bw200 development frames，恰好一次，禁止重试/替换/调
参）。D04 通道实现于 `comparison_bench/`：`run_d04` core lane（含 D04
限定的 manifest authorization、冻结失败包处理）、CLI `d04` action、
只读 verify 扩展、D04-lane 工程测试（DT3，27/27 全绿）。生产执行一次，
run_id `v13_d04_20260814`，六文件包位于
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d04_20260814/`，
严格只读 verify PASS（32 outcome rows、32 telemetry records、ledger ready）。

**Context**: P08 freeze review 已 ACCEPT；DT0-DT2 21/21 通过。D04 结果：
8/32 `syndrome_consistent` + `exact_correct`（全部在第 1 次迭代收敛）、
24/32 `decode_failed` 到 100 次迭代上限、零 `decoder_error`、零
exact_mismatch、零 non-finite/normalisation/underflow 事件。telemetry
观测（经验诊断，非结论）：decode_failed 帧末态后验高度集中（mean
posterior max 0.986、entropy 0.103 bits）但平均 3.79 个 unsatisfied
checks，11/32 帧有振荡迹象。hook 等价性在全部 32 帧保持
（hook_equivalence=ok），V7 R1A 冻结源码字节未改。

**Alternatives considered**: D04 之前是 CLI 硬停止（exit 2）；实现即唯一
路径。输出根写入在沙箱下被拒一次，以 danger-full-access 重试同一命令
成功（用户批准）。

**Consequences**: D04 包 run_state=`plan_only`、`d05_emitted=false`，不产
生任何 diagnosis_class/run_state 结论。D05（根因报告 + 独立复核）仍未
授权、未实现；R/I/E/A/C 全部锁死。8/32 不得被表述为 promotion、
qualification 或 fresh correction。下一授权点是主线程决定是否授权 D05。

---

### 2026-08-14: V13 D01 run 统计 bug 修正 + D04 数据的信道结构观测

**Decision**: 修正 `nonbinary_v13_diagnostics._frame_channel_stats` 的 run
计数 bug（条件表达式在 run-end 检查前把 `run` 清零，导致 D01 记录
`run_count=8` 的伪影）；D01 六文件包保持不可变证据不重写。修正后的同一
128 个 bw200 characterization 帧聚合值记入本条目作为可信参考。

**Corrected aggregates** (read-only recompute, same frames): 2525 个错误符
号；2340 个 run（每帧均值 18.3）；run 长度直方图 {1: 2169, 2: 157, 3: 14}
（最大长度 3）；185 个相邻错误对（7.3% 的错误有相邻错误）——错误是孤立
的单符号扰动，不是突发。**99.3%（2508/2525）的非零 Alice-Bob 差分落在
[0,128)**，与位面失配的 MSB→LSB 单调结构（3.1e-5 → 3.75e-2）一致，并与
binary V5 同域已知的相邻 ±1 符号扰动结构（troubleshooting 中
`plane_error_channel` 的 adjacent_nominal）互证。这些是 D01 邻近的经验观
测，不构成 D05 结论。

**Context**: 主线程层面的 D04 数据预分析（非 D05）：基线双峰行为（8/32
在第 1 次迭代 exact-correct、24/32 迭代上限 decode_failed）、失败帧高置
信错字（posterior max 0.986、entropy 0.103、均值 3.79 unsatisfied
checks、11/32 振荡）与"QSC p=.20 均匀先验严重失配于小差分集中信道"的假
说一致（校准失配 0.1229；模型熵 2.722 vs 经验条件熵 0.547 bits/symbol；
R1A 泄漏 6.64 bits/symbol ≈ 12× 经验下界）。候选排序与文献对照详见本轮
分析答复；正式 diagnosis_class 只能由 D05 发射。

**Consequences**: run 统计 bug 修正只影响未来运行；修正后的聚合值用于
后续文档引用（替代 CURRENT_TASK 中旧 8-run 表述）。信道结构观测不自动
授权 R1 候选——R 阶段仍需 D05 + OpenSpec amendment + 主线程批准。

---

### 2026-08-14: V13-D05 根因报告 — code / diagnosis_complete（含一次无效发射修正）

**Decision**: 主线程按推荐步骤授权 D05 发射。离线 girth 分析显示冻结 V7
R1A 图**结构性退化**：170 个校验节点分成 85 个互不相连的 2-校验组件
（每个组件 3-4 个全 degree-2 变量），check 图 girth=2、Tanner girth=4、
逐组件最小距离 d_min=3。对 32 个 D04 development 帧的结构天花板分析：
structural_failure_fraction=0.75 == 观测失败率 0.75，且**帧级完美对应**
（24/24 失败帧都含 ≥2 错误组件；8/8 exact-correct 帧都不含）。D05 发射
`diagnosis_class=code`、`run_state=diagnosis_complete`、后继 **R3
code-only**；QSC p=.20 先验失配（校准失配 0.1229、|熵差| 2.17 bits）作为
已记录的 co-factor（其不解释观测失败——结构单独解释 100% 失败）。

**Correction**: 首次发射 `v13_d05_20260814` 因决策机制缺陷被判
inconclusive（ceiling 文档缺 observed 分数→默认 1.0；entropy gap 为负而
阈值用了带符号值），按 V8-60 先例：保留原包不可变 + 同级
`v13_d05_20260814_invalid_execution_notice.json` 记录 + 修正后以新 run id
`v13_d05_20260814_corrected` 加法重发一次（决策函数为纯函数，证据字段原
样保留）。严格只读 verifier PASS。

**Context**: 该结论与 V7 合成 canary 0/4+0/4（SER 0.20 ≈ 51 错误/帧 → 每
组件多错）以及 V6/V7 全线 0/N 历史一致；并解释 D04 双峰行为（iter-1 成
功/100 迭代失败）——4-cycle 消息传递的振荡是症状而非独立类别。

**Consequences**: R 阶段仅解锁 **R3 code-only**（prior 与 decoder 接口不
变，只改一个明确的 finite graph/rate 属性：把退化的 85 组件图换成同
n/m/rate/度数、连通、girth≥8 的图）。R1/R2 锁死。R3 候选需 OpenSpec
amendment + 独立复核后方可冻结；E01 门（≥1/64）与 A01 门（≥120/128）不
变。D05 独立只读复核（reviewer-go）为下一科学门。最高状态仍为
`ready_for_fresh_confirmation`，禁止 promoted/qualified/
observed_fresh_correction。

---

### 2026-08-14: V13-D05 独立复核 ACCEPT + R3 候选冻结（amendment）

**Decision**: reviewer-go 独立只读复核（2026-08-14）对修正版 D05 包
`v13_d05_20260814_corrected` 出具 **ACCEPT，零 blocker**：五任务全过
（六文件包 + verifier PASS；图普查 85 组件/girth4/d_min3 独立重算一致；
结构天花板 0.75==0.75、完美对应 24/24+8/8、对抗性逐帧 0 失配；决策表符
合性判断——`mixed` 不成立，因为帧级完美对应是决定性分离：每个失败帧结
构上不可纠（≥2 错误在 d_min=3 组件），每个结构干净帧在（失配的）先验
下也成功，先验解释 0/32 结果；边界扫描干净；无效发射处理正确）。四个
非阻塞警告记录在案（共存分辨率 operationalization、rationale 措辞、
D05 重算聚合的可复现性依赖、real_decode_authorized 语义）。

**R3 amendment (frozen by this entry)**: 唯一候选 = **一个** finite
graph/rate 属性变更——把冻结 R1A 退化图（85 个不相连 2-校验组件，Tanner
girth 4，组件 d_min 3）替换为**连通简单 check 图**（170 校验节点、256
变量边、变量全 degree 2、校验度 168×3+2×4、无平行边、check 图 girth≥4
即 Tanner girth≥8）。构造：确定性种子化随机配对，冻结种子 = 20260818
（>=20260814 中第一个通过 简单/连通/check-girth≥4 门的种子；原型验证
通过）。**不变**：prior（QSC p=.20）、decoder 接口（flooding FFT-QSPA，
与 D03 证明等价的镜像循环）、校验数 170、n=256、rate、max_iter=100、
syndrome/tag 语义、Alice 边界、六文件包契约。新身份
`nbldpc_v13_r3_code_v1`（canonical manifest 含构造种子与 girth 证书）。

**E01 预注册（冻结）**: 64 个 bw200 development 帧 = 按 (frame_id,
frame_identity) 排序的 development 行，跳过前 32（D04），取接下来 64：
[77,78,88,89,92,98,100,102,104,105,106,108,111,113,115,116,117,118,119,
121,123,124,125,127,128,129,134,138,139,140,142,144,145,148,151,153,159,
160,161,163,165,166,168,170,171,172,173,175,177,179,181,184,187,190,193,
194,196,198,208,212,215,216,217,221]。与 D04 的 32 帧及 128 个 audit 帧
互斥。E01 = baseline（unchanged R1A）与 candidate 各执行一次；门：
candidate ≥1/64 independently exact-corrected + syndrome consistency +
post-decode exact check + 零 forbidden/internal/accounting failures；
0/64 → `failed_existing_data_feasibility` 冻结路线。E01 通过 → E02 冻结
候选（禁止继续调参/替换）。A01（候选在 128 个 frame-identical audit 帧
上各一次；≥120/128、零 forbidden、median ≤120 s/frame、disclosure ≤8.75
bits/symbol——170×10/256=6.64 结构性通过）→ A02（bw120/bw180 预注册只读
跨层检查）→ C01。

**Consequences**: R3 候选实现（`comparison_bench/` 内新模块 + E01 通道 +
IT0-IT3 测试）现在开始；E01 前必须 IT0-IT3 全过。所有失败保留；禁止
重试/调参/替换/同义重跑 V7/V10/V11 路线。

---

### 2026-08-14: V13-E01 门通过（candidate 64/64）+ A01 开始

**Decision**: E01 development screen 生产执行一次（run_id
`v13_e01_20260814`，64 个预注册 bw200 development 帧）：R3 候选
`nbldpc_v13_r3_code_v1`（QSC p=.20、flooding、连通 girth-8 图）**64/64
exact_correct**，unchanged V7 R1A 基线 13/64，零 forbidden/internal/
accounting 失败，全部行 syndrome consistency + post-decode exact equality，
严格只读 verifier PASS。E01 门（≥1/64）**通过**；E02 无操作——候选在 R3
amendment 中已预冻结，无调参/替换。这与此前 D05 `code` 诊断完全一致：
把退化的 85 组件图换成同契约的连通图后，在相同先验/解码器下可解码性
剧变。

**A01 预注册（本条目固化）**: candidate-only（baseline 不在 audit 帧上
运行——预先决定）；128 个 frame-identical V5 confirmation 帧
（partition ranks 0..127，bw200，与 D04/E01 development 帧互斥）；门
≥120/128 exact + 零 forbidden + median ≤120 s/frame + disclosure ≤8.75
bits/symbol（170×10/256=6.640625 结构性满足）。通过 → 仅
`ready_for_fresh_confirmation`；未过 → `retrospective_non_ready`。

**Consequences**: A01 生产运行（`v13_a01_20260814`）已启动；其后是 A02
（bw200 通过后预注册只读 bw120/bw180 跨层检查，不提升状态）与 C01
（独立验收 + 记忆 triage + 用户决定 fresh acquisition）。64/64 与任何
后续结果均不构成 promotion/qualification/fresh correction。

---

### 2026-08-14: V13-A01 通过（128/128）→ ready_for_fresh_confirmation；A02 通过

**Decision**: A01 retrospective audit 生产执行一次（run_id
`v13_a01_20260814`，128 个 frame-identical V5 confirmation 帧，candidate
once）：R3 候选 **128/128 exact_correct**（raw SER 0.039–0.113），零
forbidden，median 0.90 s/frame（门 ≤120），disclosure 6.640625（门
≤8.75）。全部 readiness 门通过 → **run_state=`ready_for_fresh_confirmation`**
（V13 冻结计划允许的最高声明状态）。严格只读 verifier PASS。

A02 cross-stratum check 生产执行一次（run_id `v13_a02_20260814`）：
bw120 128/128、bw180 128/128 exact_correct，readiness gate 均满足；
`no_state_promotion=true`（只读检查，不改变 bw200 状态）；verifier PASS。

**Context**: E01（64/64）+ A01（128/128）+ A02（256/256）在同一冻结候选
（连通 girth-8 图 + QSC p=.20 先验 + flooding FFT-QSPA）上的全绿结果与
D05 `code` 诊断闭环：图的连通性/girth 是此前 24/32 失败的根因，替换后
在相同先验/解码器下全部精确纠错。补充观测：candidate 帧耗时 median
~0.9–1.0 s（远低于 120 s 门）；全部帧 syndrome_consistent + post-decode
exact equality。

**Consequences**: V13 的 existing-data 诊断路线达到终态
`ready_for_fresh_confirmation`。**不构成** promotion/qualification/fresh
correction（身份仍为历史复用）。下一步由用户决定：是否另开 OpenSpec
change 做 fresh acquisition（新帧身份）以把该候选提升为 fresh canary/
confirmation/qualification。C01（独立验收 + 记忆 triage）进行中。

---

### 2026-08-14: V13-C01 独立验收 ACCEPT — V13 规划完成

**Decision**: reviewer-go 独立只读验收（2026-08-14）出具 **ACCEPT，零
blocker**：六项任务全过——(1) 五个生产包（D04/D05_corrected/E01/A01/A02）
只读 verifier 全 PASS 且 run_state 与声明集一致；(2) 冻结门全部满足
（E01 candidate 64/64≥1/64、A01 128/128≥120 + median 0.904s≤120 +
disclosure 6.640625≤8.75 + gate_passed==run_state、A02 两层 128/128 +
no_state_promotion）；(3) 预注册纪律（D04=排序前 32、E01=次 64、A01=128
audit，互斥且与 decision-log 冻结清单精确一致）；(4) 声明边界（无
promoted/qualified/observed_fresh_correction、无 raw 数据持久化、纯加法
提交零删除）；(5) 执行授权（outcome 行数精确匹配授权解码集：32/128/128/
256）；(6) 科学一致性（`ready_for_fresh_confirmation` 为 V13 最高状态、
R3 候选独立重算一致：seed 20260818、连通、Tanner girth 8、rank 170）。
三个非阻塞警告记录在案（首版 D05 包的 run_state 标注、D01 bursts_runs
已知 bug 与 D05 修正聚合、A02 跨层 frame_id 复用——身份以
(stratum, frame_id, frame_identity) 三元组为准）。

**Consequences**: V13 冻结规划**全部完成**：P→D→R→I→E→A→C 每阶段按
纪律执行，终态 `ready_for_fresh_confirmation`，七个生产包 + 无效发射
notice 全部保留并提交。记忆 triage 完成（AGENT_PROJECT_MEMORY §47）。
待用户决定的独立事项：① 是否另开 OpenSpec change 做 fresh acquisition
（新帧身份 + prepare/review/execute/verify 链）以推进
confirmation/qualification/promotion；② V12 change 的 archive 决定
（独立 housekeeping）。两者都不由 V13 自动触发。`

---

### 2026-08-14: V14 效率可行性门——计划冻结（freeze review ACCEPT）+ 实现 + 门执行启动

**Decision**: 按调研路线（docs/nonbinary-ldpc-efficiency-roadmap-survey.md）
立项 V14 效率可行性门：在构造任何高码率码之前，用 DE 判定"结构化信道
（V13 characterization 帧经验差分分布）上是否存在 rate≥0.90、f≤1.3 的
非二元 LDPC 系综"。冻结内容：信道模型（λ=1e-3 光滑化、cross-fit 只用
characterization 帧；H(w')=0.5677 bits/symbol）；候选集 3 个 λ
（{2:.25,3:.30,4:.45}/{2:.20,3:.25,5:.55}/{3:.3,4:.7}）× m∈{15,16,17,18}
共 12 点评估（不做 profile 搜索——V11 教训 66.7h）；Stage 0 QSC 回归
（q=4 R=0.75 发表门限 0.069±0.012）；Stage 1 折叠小 q 结构化验证
（φ_m(d)=d mod 2^m）；Stage 2 q=1024 点评估（n_samples=1e4、max_iter
150、熵≤0.01 连续 20 迭代）；预算 3 GiB RSS / 24 h wall / execute-once
+ 严格字节回放；预注册降级链（Li-Fair-Krzymień GA → Cohen 位面分解 →
resource_blocked）。判定规则先冻结：PASS iff Stage 0 通过且存在收敛点
且 f≤1.3；FAIL → 路线冻结为"仅 fresh 确认 V13 R3 现状"。

**Process**: DE 机制由调研子代理定稿（V9 run_mcde 信道块 ~10 行改动
即支持任意 w；q=1024 单点 ~1.18s/500×30 可行、profile 搜索不可行）；
freeze review 首轮 BLOCKERS（spec 候选集与 design 矛盾、Stage 0 锚点
漂移）修复后复评 ACCEPT（三个非阻塞词汇警告已并入）；实现由
opencode-go/deepseek-v4-flash 子代理落实（nonbinary_v14_channel.py、
nonbinary_v14_mcde.py——numba 本地核拷贝 + QSC 模式与 V9 等价 1e-12、
cli/run_v14_gate.py），独立 verifier ACCEPT；测试 13/13 + v13 回归
49/49 = 62/62（gate 修复后 64/64）；V8/V9/V11/V13 源码零改动。

**Correction**: 首启失败——gate 动作对 evidence 目录整体 fail-closed，
而模型文件（model 动作产物、已提交）先存在；修复为按文件 fail-closed
（模型文件属同一冻结证据集，gate 只读校验之；gate 自身 6 个输出文件
任一存在即拒绝，execute-once 不变）。

**Consequences**: 生产门（Stage 0/1/2）已启动（execute-once）。门结果
决定 V15：PASS → V15 高码率候选立项（合成资格 + fresh 实数据需用户
决定采集）；FAIL → 路线冻结声明。门证据落 change 的 evidence/ 目录
（加法、fail-closed）。

---

### 2026-08-15: V14 效率可行性门——gate_state=FAIL，效率路线冻结声明

**Decision**: V14 门生产执行一次（evidence 提交 1cdc63b6），E02 独立
gate review **ACCEPT**：Stage 0 机制回归 PASS（proxy 0.060 vs 发表
0.069，|δ|=0.009≤0.012）；Stage 1 折叠验证全绿；Stage 2 的 12 个冻结
点（3 λ × m∈{15,16,17,18}，q=1024 结构化信道）**全部非收敛**——150
迭代后平均 base-q 熵停在 0.288–0.357（收敛阈 0.01 的 29–36 倍，非
边际失败）；f 值 1.032–1.239 全部满足 f≤1.3，但收敛是绑定判据 →
**gate_state=fail**。预算：wall 87 min ≤ 24 h、peak RSS 577 MiB ≤
3 GiB；严格回放在途。机制经 T2 等价测试（与 V9 1e-12）与 Stage 0
文献回归双重背书，FAIL 不是机制伪影。

**科学解读（规划层，非新结论）**: 四个码率点（R=0.9414–0.9297）全部
低于该信道容量（C≈0.9432 base-q），故非信息论不可能；而是**普通不
规则系综（含 degree-2 的 λ、dc≈51 集中 ρ）在该极端码率上的 BP 阈值
距容量存在结构性缺口**。这与历史一致：V10/V11 在 QSC 上 .22/.32 门
失败是同类"普通系综的 BP 阈限"现象。V13 R3（f≈12.1）仍是唯一经
验证的正确器；fresh-confirmation-only 路线不受影响。

**Consequences（冻结纪律的终态）**: V15（高码率候选）与 V16（部署
适配）**不立项**——其提案/设计骨架保留为"门未过、不立项"状态。V14
禁"最接近"续行与换候选重跑；效率路线的下一步只能由用户决定另开
新 change，候选方向（均需新 DE 门先行）：① 非二元 SC-LDPC（阈值饱和
文献：Zhang 2016；V11 在 QSC 门失败但本结构化信道上耦合增益未测）；
② Cohen 2019 位面分解（与本数据 MSB→LSB 单调失配同构）；③ 多边/
高维 λ 族。V12 archive 与 fresh acquisition 决定仍待用户。

---

### 2026-08-15: 更新目标 P0 收口完成 + P1（fresh acquisition）/ P2（V17 位面门）立项

**Decision（用户更新目标）**: P0 状态收口（纯 housekeeping、无科学
执行）→ P1（立即优先：V13 R3 fresh acquisition）→ P2（独立效率研究：
位面/边标签 DE 门先行）。

**P0 执行（2026-08-15，提交 fb6e579d）**:
- V12 正式归档 →
  `openspec/changes/archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`
  （保留 `source_partition_blocked`、X01/X02 未执行、v2 prepare 包；
  归档≠成功、不重开执行；delta spec 未合并——V9/V10 先例）。
- V15/V16 归档为 aborted drafts（未立项/前置门失败；delta spec 未合并；
  aborted_notice.md 记录重启边界：需新 DE 门 PASS）。
- 陈旧文档修复：CURRENT_TASK.md（V14 段降级为历史）、V14 tasks.md
  （头部状态、测试数字、回放完成）、V13 tasks.md（C01 COMPLETE、
  IT0-IT3 49/49）、AGENT_HANDOFF.md（Current State 重写）、记忆
  §47/§48 修订 + §50 新增。
- V14 测试数字统一（原始记录 = decision-log 2026-08-14）：修复前
  13+49=62/62 → 修复后 15+49=**64/64**。
- 本地领先 `origin/main` 28 个提交（收口后 29）；**push 待用户单独
  授权**。

**P1 立项（提交 240e3a2e）**: 新 change
`formal-nonbinary-ldpc-v13-r3-fresh-acquisition`——冻结：新帧/载荷
身份（排除 V4/V5/V12/V13 全部历史锁）、acquisition/window/stratum
（bw200 主）、三角色隔离、R3 码本/先验/迭代上限不变、漂移与无
eligible frame 停止规则、失败原样保留；流程冻结→prepare→review→
单次 execute→只读 verify→fresh-confirmed/frozen failure。数据事实：
2026-08-15 检查 `D:\Data` 无 fresh 帧数据源（最新 2026-07-28 JSI，
非帧数据）→ prepare 预计产出 zero-eligible（合法冻结结果，V12 先例）；
用户提供新数据后 prepare 可确定性重跑（非失败重跑）。

**P2 立项（提交 240e3a2e）**: 新 change
`formal-nonbinary-ldpc-v17-multibit-structured-de-gate`——纯可行性门：
Stage 0 Cohen/多位机制复现 → Stage 1 MSB→LSB 单调失配映射为冻结
多位信道模型（schema v1）→ Stage 2 预注册 3–5 个边标签/位面候选点
评估（复用/扩展 V14 structured 分支）→ 冻结收敛（熵≤0.01×20 迭代）/
f≤1.3/预算（3 GiB/24h）/execute-once+回放 → 一次执行。PASS → 另开
有限码 candidate change；FAIL → 冻结、不启动 V15/V16、不扩大搜索。
排名冻结：①位面/边标签（直接对应当前数据位面不均匀性）；②SC-LDPC
（QSC 负耦合、结构化未否定）；③多边/高维 λ。

**Process**: P0 由主线程完成并本地提交；P1/P2 规划文档由主线程起草，
两个独立 freeze review（opencode-go/deepseek-v4-flash 子代理，只读）
在途；ACCEPT 前禁止 prepare/实现/执行。V13/V14 源码零改动。

**Consequences**: 两个新 change 的 tasks P07 均为独立 freeze review；
review 结果决定是否进入 PREP/实现阶段。push（30 个本地领先提交）
仍待用户单独授权。

---

### 2026-08-16: V17 多位结构化 DE 门——gate_state=mechanism_unverified（FAIL 类），位面/边标签效率路线冻结

**Decision**: V17 生产 gate 执行一次（wall 7026.6 s，peak RSS 541 MB
≤ 3 GiB/24h 预算），strict replay 5/5 字节一致，E02 独立 gate review
**ACCEPT（零 blockers）**。终态 **`mechanism_unverified`**（FAIL 类）：
- **Stage 0 锚点 A（q=4 退化 p1=p2 内部一致性）失败**：
  bit-plane 分解 DE 阈值 0.0525 vs 符号级 QSC DE 阈值 0.0600，
  Δ=0.0075 > 容差 0.005 → `mechanism_verified=false`。方向性成立：
  位面分解在 p=0.055 起 joint 未收敛（熵跃升 0.95），符号级至
  p=0.060 仍收敛（0.0625 才翻转）——同一系综/seed/n_samples=1e5/
  max_iter=150 下位面分解阈值严格低于符号级阈值，Cohen 式
  位面分解机制未在冻结判据内复现。
- **Stage 0 锚点 B（文献交叉）通过**：computed 0.0600 vs published
  0.069，|δ|=0.009 ≤ 0.012（V14 冻结常量逐字一致）。
- **Stage 1 模型构建成功**：V13 D01 只读聚合 → 10 个 MSB-first
  位面误码率（3.05e-5→3.75e-2），product-of-marginals 联合近似
  （显式声明保守假设），熵 0.549955 bits/symbol。
- **Stage 2 诊断（diagnostic_only）**：3 候选（bitplane/edgelabel/
  planeweight）× m∈{15,16,17,18} 全 12 点 **全部未收敛**，
  f_achieved∈[1.065,1.279] 均 < f_limit 1.3 但收敛为绑定判据；
  无 pass_point、无 closest/rerun/调参痕迹。

**科学解读（规划层，非新结论）**: 门冻结发生在机制层而非系综层——
Cohen 2019 多位位面分解机制未通过内部一致性锚点，故 Stage 2 的
12 个诊断点不构成效率结论（仅记录，不引用为证据）。这与 V14
（普通不规则系综在 rate 0.93–0.94 无 BP 收敛点）共同说明：位面/
边标签路线在该冻结判据下不可验证，不进入有限码。

**Consequences（冻结纪律的终态）**: 位面/边标签效率路线按 V17 纪律
**冻结**；不启动 V15/V16、不扩大搜索、无"最接近"续行、无 rerun/
调参。效率路线的下一步只能由用户决定另开新 change（候选方向：
② SC-LDPC——QSC 下负耦合、结构化信道下未否定，仍排第二；
③ 多边/高维 λ 族，排第三；或用户指定的其他方向）。本门无 FER/
资格/效率实测结论；P1（V13 R3 fresh acquisition）独立推进不受
影响，仍阻塞于 fresh 数据（用户提供后重新 prepare 即可）。
证据：change `evidence/` 6 文件（5 科学 + replay 记账）。


### 2026-08-16: V13-R3 fresh 数据准入——2026-01-21 三源判定为 data_intake_rejected

**Decision**: 用户提供的三个 `2026-01-21` Type2 ttbin 源不能作为 V13 R3
fresh-confirmation 数据源。新增 D0 准入证据包
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_intake_20260816/intake_decision.json`，
判定 `data_intake_rejected_for_fresh_confirmation`。不进入 P1 prepare/execute/verify。

**Context**: frozen design §1 要求 fresh 数据晚于 V13 历史且为可核验 10 dB
Type-II 帧数据。三个源时间戳为 2026-01-21、损耗元数据缺失；且 folder1 已有
D2 烟测 `raw_ser=0.254663`，远超 V13 D01 参考 0.0771，已触发漂移门。

**Alternatives considered**:
- 按原“v16”规划继续 prepare/execute：拒绝，因数据不 fresh 且烟测已漂移。
- 降级为 legacy drift audit：可另开新 change，但不得使用 fresh-confirmed/
  promotion/qualification 声明。

**Consequences**: P1 保持 `no_eligible_frames` 阻塞态；D1–D5 仅在诊断标签下
可后续执行；真正 fresh 数据到达后重新进入 D1–D5→P1。push 仍待用户单独授权。

### 2026-08-16: V13-R3 fresh 数据准入——D1–D5 诊断执行完成，D5 drift_exceeded

**Decision**: shell 可用后按修正参数执行 D1–D5 诊断，完成三源 sidecar/pairs/manifest 与全量漂移预检。D5 三源全部 `drift_exceeded`，按冻结停止规则自动停止，不进入 P/E/V。

**Context**: D0 已判定 `2026-01-21` 三源 `data_intake_rejected_for_fresh_confirmation`；D1–D5 作为只读诊断仍按修正参数执行，以固定证据并确认漂移幅度。

**Evidence**:
- D1: `workspace/v13r3fresh_20260816/d1_baseline.json`
- D2/D3 sidecars: `workspace/v13r3fresh_20260816/sidecars/<source_tag>/`（`map_sanity.verdict=FAIL`，raw SER ≈0.240–0.256）
- D4 pairs: `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/<source_tag>/pairs.parquet` + `build_manifest.json`
- D5: `workspace/v13r3fresh_20260816/precheck_report.json`，三源 `precheck_state=drift_exceeded`，fail reason 均为 `raw_ser_mean_deviation_exceeded`

**Consequences**: P1 仍保持 `no_eligible_frames` 冻结终态；P/E/V 不进入。真正 fresh 数据到达后重新进入 D1–D5→P1；若用户坚持使用 2026-01-21 数据，另开 legacy drift audit change。push 仍待用户单独授权。

### 2026-08-16: V13-R3 legacy drift audit——用户决定使用 2026-01-21 三源；192 帧 188 exact_correct / 4 decode_failed

**Decision**: 用户明确表示这些是之前采集的数据、纠错算法对具体数据源要求没那么高，要求使用三份 `2026-01-21` Type2 数据继续。按冻结规则不以 fresh-confirmation 进入 P/E/V，另开 change `formal-nonbinary-ldpc-v13-r3-legacy-drift-audit`，claim boundary 仅限 `legacy_drift_audit`。

**Execution（一次）**: 新增最小 execute/verify 工具（8 测试通过）。三源各取前 64 个完整帧（frame_id 0..63，共 192 帧），不变 R3 候选 `nbldpc_v13_r3_code_v1`（p=.20、flooding FFT-QSPA、max_iter=100）每帧解码一次，失败原样保留。

**Result**: 188/192 `exact_correct`；4 帧 `decode_failed`（`iteration_limit`：type2_1M frame 15/20、type2_2M frame 52/56），raw SER 0.230–0.297。三源 raw SER 均值约 0.243–0.255（V13 D01 参考 0.0771）。只读 verify OK。证据包：
`comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`。

**Consequences**: 本结果仅证明 R3 候选在已知漂移 legacy 数据上 188/192 精确纠错，不构成 fresh-confirmed / promotion / qualification；P1 `no_eligible_frames` 冻结终态不变；P2 V17 `mechanism_unverified` 不变。push 仍待用户单独授权。

### 2026-08-16: V13-R3 legacy drift audit——全量 8412 帧完成，8284 exact_correct / 128 decode_failed

**Decision**: 用户要求继续使用三份 `2026-01-21` legacy 数据；在 192 帧审计后进一步执行全量 8412 帧审计。采用 8 chunk 并行（`--all-frames --chunks 8`），每个 chunk 独立 additive 包，claim boundary 仍仅 `legacy_drift_audit`。

**Result**: 8/8 chunk verify OK；合并全量结果：
- 总帧数：8412
- exact_correct：**8284**
- decode_failed：**128**（均为 iteration_limit）
- exact_mismatch：0
- 分源：1p5M 2729/2767，1M 1970/2000，2M 3585/3645
- raw SER 均值：0.240–0.256（V13 D01 参考 0.0771）

**Evidence**: 合并包 `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_full_20260816/` + 8 个 chunk 包。

**Consequences**: 仍不构成 fresh-confirmed / promotion / qualification；P1 `no_eligible_frames` 与 P2 V17 `mechanism_unverified` 均不变。push 待用户单独授权。

### 2026-08-16: V20 scientific reclassification and V21 Bob-only plan

**Decision**: 接受外部审查结论，V20 的 `31/64`、`40/96` 不得标为可执行 FER：
- `31/64` = oracle-aided best-of cascade upper bound；
- `40/96` = top-4 oracle list coverage；
- standalone bounded4 `30/64` = unverified Bob-only estimate；
- V01 = counting-only verifier。
V20 状态改为 `CONCLUDED_PENDING_SCIENTIFIC_CORRECTION_AND_ARCHIVE`，语义修正后
再归档。新建 V21 plan：`docs/nbldpc-v21-bob-only-plan-20260816.md`，只验证
Bob-only 策略 S0/S1/S2，Alice 仅出现在最终指标阶段；停止门 FER≥0.45 则冻结
短块 OSD/top-K 路线，转 V22 结构化构造。

**Context**: V20 cascade 用 `np.array_equal(x_hat, alice)` 决定是否调用
bounded4 以及从 top-K 中选谁；Bob 无法知道 syndrome-consistent 候选是否是
exact mismatch，因此该策略不可执行。n64 最多只剩 5 bits 公开预算，n80 只剩
7 bits，16/32-bit 验证标签会使 f 升到 1.50–2.05，top-K+public hash 不能直接
立项。

**Alternatives considered**:
- 继续扩样 n80 top-K：拒绝，因 oracle coverage 与可执行 FER 混同；
- 直接进入 fresh qualification：拒绝，必须先完成 Bob-only 重分类与验证；
- 直接归档不修语义：拒绝，因会固化错误 FER 标签。

**Consequences**: V20 保持 active 直到 Phase 0 addendum 完成并真正移动到
archive；下一阶段执行 V21 Bob-only 验证；push 仍待用户单独授权。

### 2026-08-16: V21 Bob-only stop gate triggered

**Decision**: V21 Bob-only validation on 64 fresh n=64 frames:
- S0 BP-only: 24/64, FER=0.625
- S1 bounded4-only: 28/64, FER=0.5625
- S2 BP-first-fallback-bounded4: 28/64, FER=0.5625
All >= 0.45, so stop gate is triggered. Short-block OSD/top-K branch is frozen as
`scientific_not_ready`. V20 moved to archive; V22 structured construction drafted.

**Context**: This confirms the external review: Bob-only executable FER is around
0.56-0.63, not the oracle upper bounds 0.5156/0.5.

**Consequences**: No fresh qualification; next phase is V22 DE-gated MET/protograph
or SC-LDPC construction. push still user-gated.

### 2026-08-16: V22 structured DE declared not-ready for target f

**Decision**: V22 structured DE gate at q=1024, rate=0.9375 does not converge
with current SC-LDPC/plain tools even at n_samples=200, max_iter=30,
degree_max=512. V22 is frozen as `scientific_not_ready` pending a MET/protograph
multi-edge DE implementation. No finite-code construction is started.

**Context**: plain structured DE ceiling confirmed; SC-LDPC V10 winners only pass
at low QSC p=0.05, not target rate. degree cap unblocked by V22b but candidates
still non-converged.

**Consequences**: no finite construction, no fresh qualification. Next candidate
is a MET/protograph DE (V23) or acceptance of current not-ready state.

### 2026-08-16: V23 DE not reachable with current ensembles

**Decision**: q=1024, rate=0.9375 structured-channel DE does not converge with
plain irregular, SC-LDPC, regular protograph, or simple irregular protograph
ensembles (entropy floor ~0.19-0.34, tolerance 0.01). V23 status set to
`DE_NOT_REACHABLE`. Further progress requires full DE optimization
(Müller-style) or a different channel decomposition; no finite-code construction
is started.

**Consequences**: f<=1.3 structured high-rate reconciliation is not demonstrated
with current tooling; record as scientific limitation. push still user-gated.

### 2026-08-16: NBLDPC structured high-rate route end (awaiting user direction)

**Decision**: After V19→V23 diagnostics, q=1024 structured f<=1.3 is not
reachable with current ensembles (DE non-convergent; Bob-only FER>=0.45 for
short blocks). No further automatic step is justified without a user decision
among: (a) full structured DE optimization, (b) adjusted target (higher f /
smaller q / channel decomposition), (c) MET multi-edge implementation, or
(d) accept current not-ready state and archive.

**Consequences**: Objective stays active as a blocker; push remains user-gated.

### 2026-08-17: Correct NBLDPC route-wide conclusion and plan bounded V24 successor

**Decision**: Supersede `NBLDPC_ROUTE_BLOCKED` and any route-wide “unreachable”
or “MET failed” wording with `NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`.
V21 concluded its observed stop gate but lacks pre-freeze and runtime
Alice-injection/V01 verification. V22 is negative only for tested candidates
under the current kernel. V23 reduced base matrices to aggregate single-edge
`lambda/rho` and called V22b; it did not implement topology-preserving
protograph DE or MET DE. Its raw scan contains three matrices, while additional
consolidated points lack independent raw/verify packages.

**Context**: The 2026-08-16 closeout wording overreached the actual evidence and
collapsed engineering tests, scientific verification, candidate coverage, and
unimplemented MET into one route-wide conclusion.

**Consequences**:
- V21, V22, and V23 are respectively
  `CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE`,
  `CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`, and
  `CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE`.
- This round performs documentation/planning only; no code, DE/FER execution,
  scientific output, archive movement, or push.
- Actual archive order is V21 -> V22 -> V23 only after independent read-only
  closeout ACCEPT and explicit user authorization.
- V24 is frozen pending P07 user authorization for bounded q=1024 V17
  structured single-edge optimization.
  DE PASS precedes any finite-code proposal. True MET is untested and can only
  become a separate user-authorized change after V24 FAIL.

**Freeze-review addendum**: V24 P06 independent read-only review returned
ACCEPT on 2026-08-17 after the frozen V8-trace reuse, deterministic indexed
generator, ranking/error semantics, and resource-stop contract were made
unambiguous. P01–P06 are complete. P07 user authorization remains required
before implementation or scientific execution.

---

## 2026-08-18 — V24 archived predecessor + engineering + gate launch

**Context**: The current objective granted P07 (implement + scientific
execution) and asked to formally archive V21->V22->V23 first.

**Decisions**:
- V21/V22/V23 archives moved:
  `openspec/changes/archive/2026-08-18-*` with archive notes. Archive direction
  V21 -> V22 -> V23 preserved.
- V24 engineering (I01-I11) implemented and all 21 focused tests pass
  (T0/T1/T2/T3). No frozen predecessor source modified.
- Pre-registered M0-M2 scientific gate launched in background with a 24 h
  completed-DE-call resource ceiling; M0 mechanism gate passed.

**Observed**:
- Proposal sparsity: 135 unique valid in-band candidates across the 8192
  attempt ceiling.
- Screen DE calls non-converged (final base-q entropy ~0.3), consistent with
  the V22/V23 single-edge negative diagnostics.
- Evidence root:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`.

**Pending**: gate completion (~7 h) and independent verifier; terminal state
(pass/fail/resource_blocked) recorded in M3. No finite code/FER/qualification/
promotion before a DE PASS, and no push.

---

## 2026-08-18 — V24 M0-M2 gate result: FAIL (bounded single-edge route closed)

**Gate**: pre-registered V24 M0-M2 scientific gate completed in background
(314 DE calls, 4.87 h accumulated completed-DE-call time, well under the 24 h
ceiling; 0 errors; 0 converged).

**Result**:
- M0 mechanism/accounting gate: PASS.
- 135 unique valid candidates found in 8192 attempts (search band
  R in [0.9375, 0.94140625]).
- Screen (270 calls): 0/135 converged; entropy floor ~0.20-0.32.
- Refine (24 calls): 0/8 converged; entropy ~0.29-0.30.
- Holdout (20 calls, 4 pre-declared finalists x 5 seeds): 0 finalists converged
  on all five seeds (final base-q entropy ~0.29-0.30).
- Terminal state: **`fail`** = `single_edge_bounded_optimization_failed`.

**Interpretation**: The bounded single-edge `lambda/rho` optimization over the
frozen V17 q=1024 structured channel at target f<=1.3 found no DE-convergent
candidate. This is an asymptotic ensemble result only (VA09/VA10): no
finite-code, FER, qualification, promotion, or MET claim is made.

**Successor rule**: true MET/multi-edge DE is only a new user-authorized
change candidate; adjusting q / channel decomposition / f target is a separate
user decision. No automatic fallback runs. No push was performed.

**Evidence**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`
(read-only verifier: ok=True, recomputed terminal fail).

---

## 2026-08-18 — V25 M0-M4 complete: pass_ready_for_de_change

**Context**: main-thread freeze decision accepted the +-1 empirical regularity as a
source/delay-conditioned channel (not alignment blocker); P102 ACCEPT; M0-M4 authorized.

**Result**:
- Empirical timestamp channel: H(A|B) ~ 0.80 bits; errors ~ {-1,0,+1} adjacent bins;
  direction flips with delay_used_ps sign (-50 -> +1, +50 -> -1), stable over time.
- M1: empirical delta conditional models (C03/C04/C05) beat QSC (3.20-3.35) and V17
  independent-plane product (3.32-3.50) on every source's holdout (NLL 0.81-0.83).
- M3: chain-rule closure error <= 5e-9 across F01-F05 x {natural, Gray}.
- M4: high-field candidate F01/GF512(+GF2), mid-field control F03/GF32(+GF32) for V26;
  terminal state = pass_ready_for_de_change.
- Evidence root: comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/
- Read-only verifier ok=true.

**Successor**: V26 small-scale channel-informed DE is a NEW change requiring explicit user
authorization; V25 PASS only proposes V26 and does not auto-start it. No finite code / FER /
MET / fresh qualification / public residual / Alice-oracle; no push.

## 2026-08-19 — V26 channel-informed multilevel DE gate: RUN_COMPLETE pass_target_f13 (+ closeout fixes)

**Context**: V25 (pass_ready_for_de_change) proposed two preselected exploration points —
high-field F01 GF512+GF2 (A01) and mid-field F03 GF32+GF32 (A02). V26 ran a small-scale
channel-informed multilevel MC-DE gate on them at f in {1.3,1.6,2.0}.

**Result**:
- M0 adapter semantic gate + M1 mechanism tests all pass; A02 f=1.3 converges on all
  2 layer x 3 source x 5 confirm-seed (30/30), final mean entropy 0.00000 bits/symbol.
  A01 f=1.3 fails on the GF2 residual layer, passes at f=1.6. Terminal = pass_target_f13.
- Independent read-only verifier recomputes 72 screen + 60 confirmation + A02@f=1.3 30/30
  + rate/rho/seed/entropy/terminal; run_01 and run_02 both 0 mismatch, ok=true.
- Fixed definitions: f_i = leak_i / H_i with leak_i = (1 - R_i) log2(q_i) and
  R_i = 1 - f_i H_i / log2(q_i) throughout proposal/design/spec/report/code/v27 planning.
- Corrected weak M1 references: iteration-0 test now genuinely enters the MC-DE first round
  (record_channel_entropy); GF2 BSC reference now clearly decides pass/fail (noiseless must
  converge; feasible-rate must converge; at-capacity must fail) instead of "both non-converge
  = agree".
- Implemented the declared 24h completed-call resource gate (RESOURCE_LIMIT_SECONDS) in
  run_screen/run_confirmation + resource_blocked terminal state; not triggered in V26.
- Added explicit source<->delay metadata (SOURCE_METADATA: 1M/1p5M/2M -> delay_used_ps
  -50/+50/+50, n_pairs 512000/708352/933120) into ChannelAdapter, M0 detail, RUN_MANIFEST.
- Run roles: run_02 = canonical, run_01 = deterministic_repeat (RUN_MANIFEST/README).

**Consequences**:
- pass_target_f13 only authorizes proposing A02 (F03 GF32+GF32) finite-code/construction
  change; still no FER/qualification/promotion/MET claim.
- V27 is a NEW change (finite-leakage-margin DE gate) to be written as OpenSpec and returned
  to main-thread freeze review; it is NOT auto-executed here.
- V26 archived locally; no push.

---

## 2026-08-19 — V27 scope freeze (OpenSpec only, no execution)

**Decision**: Create V27 as a *finite-leakage-margin* DE gate OpenSpec, four-part
(proposal/design/tasks/spec delta), frozen parameters: architecture fixed to F03 GF32+GF32;
source/delay-conditioned empirical posterior; Bob-full sequential decoding semantics;
lambda={2:1}; forbid degree search/MET/finite FER; n in {1024,2048,4096,8192}; 64-bit public
verification tag counted in total leakage; integer m_total per n with total f <= 1.3;
test only entropy-proportional m1/m2 and m1+/-1/m1+/-2; screen seeds 27001-27002,
confirmation seeds 27101-27105; terminal states pass_finite_budget_ready /
de_pass_no_finite_headroom / fixed_ensemble_margin_fail. After writing the four parts, return
to the main thread for freeze review; do NOT execute V27.


---

## 2026-08-20 — V27 finite-leakage-margin gate PASS (pass_finite_budget_ready)

**Decision**: V27 executed once (additive run root; V26 MC-DE kernel reused via thin wrapper,
not copied/rewritten) and reached terminal `pass_finite_budget_ready` with passing_block_len=1024;
all four block_lens (1024/2048/4096/8192) confirmed all three sources (1M/1p5M/2M) at the m1_ep
offset-0 candidate.

**Context**: Phase B required minimal budget planner + V26 MC-DE adapter wrapper, T0/T1,
independent candidate-delivery review, one-shot screen+ranked-confirmation, read-only verifier,
evidence preservation, local commit (no push). Independent review run in-conversation (subagent
infrastructure unavailable; user authorized in-conversation review, not gated on subagent).

**Alternatives considered**:
- Reuse V26 DE gate kernel directly: rejected — V27 needs source-adaptive budget + 5-candidate
  ranking + four terminal states; V26 kernel reused only via thin wrapper.
- Simulate finite-code error propagation: rejected — V27 is asymptotic true-predecessor-
  conditioned multistage DE; 64-bit tag only in total block leakage.

**Consequences**:
- `pass_finite_budget_ready` authorizes entering Phase C (V28 GF32xGF32 finite-code engineering)
  and Phase D (V29 retrospective finite-code gate). Stop before fresh qualification.
- Critical bug found/fixed during candidate-delivery review: `run_v27_gate` collapsed 5
  candidates per (source,block_len) to 1 via `candidates[(bl,src)]=cand`; fixed to 3-tuple key
  `(block_len, source, m1)`. Manifest `frozen_config_sha_binding` misclaim removed (no SHA was
  computed). Read-only verifier ok=true (recomputed terminal == persisted).
- Evidence: comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v27r_finite_leakage_margin/run_01/ (frozen_config, screen/confirm checkpoints+results,
  ranking, gate, RUN_MANIFEST, EXECUTION_WALLCLOCK_S=322.9s). No push.


---

## 2026-08-20 — V28 OpenSpec frozen + freeze review ACCEPT (Phase C)

**Decision**: Freeze the V28 GF32xGF32 finite-code engineering OpenSpec and ACCEPT its
independent freeze review (in-conversation; subagent unavailable). V28 reuses existing
`GF2mField.create(32)` (pinned poly 0b100101), `nonbinary_codebook` three-shift-cyclic GF(32)
mother-matrix construction + `gf_rank`, and `nonbinary_qspa.decode_nonbinary_fft_qspa`
(GF(32) FFT-QSPA). No new field/decoder science.

**Context**: V27 reached `pass_finite_budget_ready` at block_len=1024; V28 must materialize
that split `(m1=6, m2 in {194,200,202}, R1, R2)` as real GF(32) parity-check matrices + a
Bob-only sequential decoder so V29 can run the retrospective finite-code gate on frozen V25
holdout.

**Alternatives considered**:
- New GF(32) field/decoder: rejected — pinned `GF2mField` and FFT-QSPA already exist and are
  verified; V28 is engineering, not new science.
- Re-run DE to re-pick parameters: rejected — V27 already fixed the split; V28 must not
  re-optimize (forbidden re-tuning).

**Consequences**:
- Leakage = m_total*5 + 64 bits; f = leak/(n*H_source) < 1.3 for all three sources
  (1.29715 / 1.29409 / 1.29495), consistent with V27.
- Terminal state only `engineering_ready_for_retrospective_gate`; no FER/qualification/
  promotion in V28. V29 follows on frozen holdout. No push.


---

## 2026-08-20 — V28 implementation complete + acceptance ACCEPT (Phase C)

**Decision**: Implement V28 GF32xGF32 finite-code engineering and ACCEPT its independent
main-thread acceptance review. V28 reuses `GF2mField.create(32)`, the `nonbinary_codebook`
three-shift-cyclic GF(32) mother-matrix construction + `gf_rank`, and `nonbinary_v10_fftqspa.
decode_error_domain` (GF(32) FFT-QSPA, Bob-only). No new field/decoder science.

**Context**: V27 selected (block_len=1024, m1=6 shared, m2 in {194,200,202}). V28 materializes
that split as real GF(32) parity-check matrices + two-layer sequential decode so V29 can run
the retrospective finite-code gate on frozen V25 holdout.

**Alternatives considered**:
- Use `decode_nonbinary_fft_qspa`: rejected — it internally enforces the N1 n=64 family and
  rejects V28's n=1024 matrices; the lower-level `decode_error_domain` is the correct reuse.
- New GF(32) decoder: rejected — the pinned FFT-QSPA already exists and is verified.

**Consequences**:
- Structural + noiseless decode verified (both layers, all 3 sources recover x exactly);
  controlled-error is fail-closed (never a false success). 11 T0/T1 tests pass.
- Honest finding: the V27 split is a sparse high-rate code; under uniform QSC prior, iterative
  error correction is limited (decoder reports `converged_no_syndrome`). The limiter is the
  split, not the decoder (proven on m=32/n=64 proper code). V29 measures real FER.
- Terminal state only `engineering_ready_for_retrospective_gate`; no FER/qualification/promotion.
  Evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/
  run_01/` (v28_config, v28_evidence, gate, RUN_MANIFEST, verify). Local commit, no push.

## 2026-08-20 — V29 finite-gate FAIL; V30 projective-safe successor drafted

**Decision**: Close V29 with canonical run_02 as a user-authorized
irreversible-threshold failure. It contains 9 persisted 1M blocks, exact/tag
count 1, 8 failures, and maximum possible 92/100<95. The terminal is
`v29_finite_gate_fail`; `readonly_verify.json` is `ok=true` and the FER is
observed-prefix-only. Retain run_01 as superseded 0-call
`implementation_blocked`; do not rerun or tune V29.

**Context**: The V28R finite graph audit found 15 L1 support groups, maximum
group multiplicity 69, 303 duplicate projective classes, 922 columns in
duplicate classes, and 1107 guaranteed proportional-column/weight-2 pairs.
Thus this particular finite matrix has `d_min<=2`.

**Decision boundary**: This is a V28R finite matrix-construction defect, not a
closure of the channel-informed GF32×GF32 route. The original V28 ACCEPT is
superseded by V28R engineering evidence and does not claim FER.

**Historical pre-P103 state**: The original V30
`formal-nonbinary-ldpc-v30-projective-safe-finite-graph-gate`
`FROZEN_P102_ACCEPTED` state was superseded by V30R
`DRAFT_PENDING_P103_FREEZE_REVIEW`; implementation/execution was blocked at
that time, and no DE, matrix construction, validation block, or decoder call
had started. The later P103 ACCEPT entry at the top records the current
`FROZEN_P103_ACCEPTED` state and authorization boundary. V31 fresh
time-separated qualification follows only after V30 PASS; V32 integration
follows V31.

## 2026-08-20 — V30R bounded cycle-cancellation revision (historical pre-P103 state)

**Decision**: Supersede the original V30 `P102 ACCEPTED` packet with a V30R
revision before implementation or execution. At the time of this entry, the
state was `DRAFT_PENDING_P103_FREEZE_REVIEW` and P103 was the only release
gate; the later P103 ACCEPT entry records the current state.

**Frozen packet semantics**:
- Each selected allocation may produce at most one
  `balanced-projective` packet and one `PEG-projective-cycle-cancelled` packet;
  with at most two selected allocations, the global packet cap is four.
- M1 marks a failed allocation ineligible only after all 12 registered calls
  are persisted. Only a global terminal may interrupt the registered calls.
- M3 screens fixed blocks `0..19` for every registered packet. A screen failure
  removes only that packet. After the complete screen, only the single
  top-ranked eligible packet runs fixed confirmation blocks `20..69`; its
  failure is global `finite_graph_fail` and no fallback packet runs.

**Bounded graph/label rule**:
- A duplicate projective key/proportional column is the 4-cycle FRC failure and
  must be zero. Ordinary 4-cycles are allowed and only counted for topology or
  ranking.
- For each column, reject duplicate-key labels first; among remaining fixed
  `nonzero_cycle` candidates, compute exact newly closed degenerate Tanner-6
  cycles and choose minimal `(degenerate_6_new, ratio_index)`. Nonzero counts
  are allowed and retained as aggregate evidence.
- Tanner-8 is topology/girth diagnostics only. No all-4/6/8 FRC catalog,
  random label search, or candidate rejection list is required. Standard
  variable-side ACE is not used because `d_v=2`.

**Consequences**: V30R retains the V25/V26 channel and V27/V29 leakage/data
boundaries, but narrows cycle cancellation to an executable,
literature-aligned bounded rule. No code, DE, finite decoding, scientific
output, archive, commit, or push is authorized before P103 ACCEPT.

**V30R input binding**: V25 authority is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
plus
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`;
V26 canonical is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
(manifest/M0/verify); V28R canonical is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
(config/evidence/manifest/verify).
The source IDs/delays are `type2_1M_20260121_184040/-50 ps/1M`,
`type2_1p5M_20260121_183806/+50 ps/1p5M`, and
`type2_2M_20260121_183657/+50 ps/2M`, with matching
`v13r3fresh_pairs_20260816/<source_id>/pairs.parquet` paths. The field is
`GF2mField.create(32)` with `0b100101`, V28R field_id
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, and
zero-based `ratio_index`.

**V30R deterministic graph binding**: balanced uses columns in order and
lexicographic supports minimizing
`(occupancy_after,max_check_degree_after,sumsq_after,a,b)`. PEG uses the prior
support check-multigraph edge distance `d_check(a,b)`, defines Tanner path
length `d(a,b)=2*d_check(a,b)`, and minimizes
`(component_flag,distance_cost,max_check_degree_after,sumsq_after,a,b)` with
local Tanner score `d+2`; projective uniqueness is label-stage-only. Tanner-6
counts contain only the current column and use the canonical tuple
`min((j,a,k1,c,k2,b),(j,b,k2,c,k1,a))`; L1 and each L2 source use independent
state. M1 is 72 screen plus at most 60 confirmation calls, with complete 30-call
confirmation for each selected allocation and allocation-local failure.

---

### 2026-08-21: V31 deterministic finite-graph redesign — ARCHIVED_PARTIAL closeout audit addendum (Change A, A10)

**Decision**: Close V31 as `ARCHIVED_PARTIAL` via additive closeout audit addendum `docs/nbldpc-v31-closeout-audit-addendum-20260821.md`. The authoritative evidence is additive `run_02` (`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_02/`); `run_01` (`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`) is preserved byte-identical but superseded for all lifecycle and interpretation claims. No V31 rerun, reseeding, or graph tuning is performed.

**Context — why ARCHIVED_PARTIAL**: V31 executed n=1024 complete (300/300 blocks: 100 per source 1M/1p5M/2M) and reached `finite_graph_fail` (exact 0/300, tag 0/300, syndrome 0.00, L2 always `converged_no_syndrome`, zero false accepts). n=2048 executed only 14 blocks from 1M (1p5M/2M not executed). Therefore:

```
V31: ARCHIVED_PARTIAL
n=1024: 300/300, finite_graph_fail
n=2048: 14 blocks from 1M only
original both-n execution: incomplete
global PASS under original contract: impossible
bounded-prefix contingency: post hoc
```

A global PASS under the original both-n (n=1024 + n=2048) contract was impossible once the complete n=1024 failure was observed.

**Post-hoc submission timing**: The original submission closed on a `finite_graph_fail` terminal without distinguishing the bounded-prefix nature. The independent audit on 2026-08-21 identified that the 1M 14-block n=2048 prefix was not a pre-registered design contingency but a closeout-time bounded-prefix contingency added post hoc to document the consistent `converged_no_syndrome` mode. The correction is additive and is recorded in the new addendum and in `run_02` verifier v2 evidence; `run_01` is superseded precisely because it omitted the persisted PEG evidence limitation.

**Why n=1024 negative retained**: The 300-block n=1024 result is a complete, verifier-recomputed (`ok=true`, `problems=[]`, 13015 s wall) bounded negative for the tested deterministic `QC-cyclic-projective` family (full-rank, occupancy 9 at n=1024 / 18 at n=2048, zero duplicate/proportional keys) at fixed `m1=16` on the F03 GF32+GF32 V25 channel (field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, `HEAD c8d2acab`). L2 progress without convergence is real; the failure is isolated to the finite graph/decoder conversion layer and does not negate V25/V26/V27 or the entire GF32+GF32 route.

**Why no V31 rerun**: V31 is an immutable executed gate (M1 60/60 PASS, M2 PEG rank-deficient hard reject, M3 QC 0/300). Rerunning with the same deterministic constructions would reproduce the same rank deficiency and syndrome non-convergence; any tuning would violate the no-rerun/no-tuning discipline for a completed gate. The addendum therefore corrects only the closeout wording and lifecycle, not the science.

**Why V32 finite-DE bridge instead of graph/seed tuning**: Graph-local tuning (degree/PEG label/seed search) would re-search the same finite conversion layer that V31 isolated as failing, without testing whether the empirical channel itself supports a finite leakage budget at these lengths. V32 (`formal-nonbinary-ldpc-v32-finite-de-bridge`) is pre-registered to test the upstream hypothesis first: whether a channel-informed finite-DE bridge at n=1024 can recover a feasible split before any new finite graph is constructed. If that bridge fails, graph tuning is moot; if it passes, a new graph change can be built on a validated budget. This ordering preserves the V25/V26 channel scope and avoids speculative finite-graph search.

**What is corrected (4 rows)**: `fully executed -> partially executed`; `pre-registered bounded contingency -> post-hoc closeout contingency`; `complete finite-graph gate -> n=1024 complete plus n=2048 prefix`; `verifier proves all evidence -> verifier proves persisted evidence with PEG replay limitation`.

**Verifier v2 evidence (authoritative run_02, run_01 superseded)**: `run_02` block coverage n=1024 300/300 + n=2048 14×1M; exact 0/300, tag 0/300, false_accept 0; syndrome 0.00 (`converged_no_syndrome`); runtime 13015 s; QC matrix full-rank occupancy 9/18; input/code binding field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, `H` from V25 `data_inventory.json`/`split_manifest.json`, `m1=16`, `HEAD c8d2acab`; PEG limitation exact text `verifier proves persisted evidence with PEG replay limitation` (PEG rank-deficient, no M3 blocks, verifier attests only persisted rejection audit); strict replay/tamper `ok=true`, `recomputed_terminal=finite_graph_fail`, zero mismatches. run_01 is preserved but superseded because it omitted the persisted PEG evidence limitation.

**Consequences**: V31 remains `finite_graph_fail` but as `ARCHIVED_PARTIAL` (n=1024 complete plus n=2048 prefix, post-hoc contingency). The prior report `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` is preserved, not rewritten. No qualification, promotion, V32 result, or complete n=2048 completion is implied. A successor V32 finite-DE bridge requires a new user-authorized OpenSpec change with fresh roots; any finite-code successor after that also requires a new change. Evidence roots `run_02` (authoritative) and `run_01` (superseded) remain immutable; no push was performed.

---

### 2026-08-23: V32 finite-DE bridge + operating-point audit correction — durable closeout (ACCEPTED)

**Decision**: Close the V32 arc with four accepted artifacts. (1) The V32 finite-DE bridge raw record (`nbldpc_v32_finite_de_bridge/run_01`, B0 6/6; B1–B4 0/60; B5 read-only import; exact-once, no resume) is retained byte-identical as valid evidence, but its persisted terminal `finite_graph_decoder_mismatch` is NOT accepted as a scientific attribution. (2) Main review verdict `EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE` stands (`docs/nbldpc-v32-main-review-verdict-20260822.md`). (3) The first operating-point audit (`formal-nonbinary-ldpc-v32-operating-point-consistency-audit`, commits 60117174→dda3503e out of order) is annotated `post_hoc_exploratory_only / not_formal_pre_registered_gate / numerical_outputs_retained / scientific_terminal_superseded_pending_correction`; its numbers are retained, its attribution superseded. (4) The correction change `formal-nonbinary-ldpc-v32-operating-point-audit-correction` (freeze 59ba0236, impl 0765d893, evidence 29a5dafe, verifier-fix 3110cb0e) is ACCEPTED with candidate terminal `audit_corrected_rate_aligned_de_required` and archived.

**Reason**: Arm B1 was not a matched empirical-joint control. Its generator law Q_B1 (Alice uniform + Bernoulli(raw_ser) + uniform nonzero delta mod 1024) differs from the V25 empirical posterior law P(A,B)=N_ab/total and places positive mass on zero-support cells (analytic q_mass_on_p_zero_cells ≈ 0.239468/0.254127/0.255348 per source), making full E_Q[-log2 P] infinite. B1's active divergence therefore cannot attribute anything to the fixed QC graph or the V28R decoder. Corrected semantics (independently recomputed, R2 bit-exact): B2 `l2_errors_final=1024` is a not-run sentinel; B3/B4 improve-but-no-syndrome (~250→~179 mean L2 errors), never "divergent". Dual-law feasibility: the empirical-P budget is nominally feasible only (pure-syndrome gaps +180–187 bits; verbatim +244–251 bits; no finite-length/DE/fixed-graph/decoder claim); the original Q_B1 law is information-theoretically infeasible at the current allocation (H_Q(B|A) ≈ 3.1921/3.3626/3.3773 bits/symbol ⇒ required ≈ 3269–3458 bits vs pure syndrome 1000–1040 bits).

**Verifier semantic guards (fix 3110cb0e, ACCEPT)**: `full_expected_nll="infinity"` iff q_mass_on_p_zero_cells>0, otherwise the JSON-safe finite analytic value; minimal explicit run-root guardrail (protected old roots/subpaths, repo/results/diagnostics roots rejected; frozen v2 root or fake-runner workspace roots allowed); verify_manifest field-level guards (schema/lifecycle/flags/implementation identity/output list/frozen-block equality) with execution-time binding (never compared against current HEAD/CLI).

**Consequences**: Do not attribute B1 divergence to the fixed QC graph or V28R decoder; do not cite `finite_graph_decoder_mismatch` as an accepted root cause anywhere. The next authorized question is exactly: under the V25 empirical joint P(A,B), F03/A02 allocation, and V31 actual layer rates (L1 0.984375 ×3 sources; L2 0.8203125/0.814453125/0.8125), does the corresponding ensemble DE converge for all three sources and both layers? A candidate change (`formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic`) exists as `DRAFT_PENDING_FREEZE_REVIEW` only; DE execution requires a frozen OpenSpec plus explicit authorization. Fixed-graph/decoder/NB-Polar successor selection remains undecided. No qualification, promotion, push, or sibling-checkout access occurred; all old evidence roots remain byte-identical.

---

### 2026-09-04: 双 PRIVATE 仓 remote 解耦采用 A 方案并冻结审计链

**Decision**: 采用 A 方案：原仓改名成为 Release 仓，新建 Comparison 仓。白名单加 4 项残留 B1 扩展放行（短标识 1b7055c / df01f068 / 7d9a77f / 6a58adb，日期与保护态见审计链），两处待推 push 保持未推。PR#1 已 MERGED（be62938，2026-09-04）。历史内容不迁移验收。已批准的脏态书面豁免归档，保持不动。

**Context**: 两仓分离前需冻结可审计的 remote 与分支终态，避免交叉可见与未授权迁移；残留项与待推项按白名单逐项审计放行。

**Alternatives considered**:
- 全量迁移历史内容：拒绝，不迁移验收。

**Consequences**: 两仓各自 origin 指向自家新址，legacy-origin 只读保留旧 URL；互不可见列为发布前必检；审计链唯一源为 `openspec/changes/repo-remote-decoupling` 三件套；后续引用以审计链为准，不记录临时盘点数字。

---

### 2026-09-05: V72P2D5 GF32 rate-mother plan frozen, no implementation or execution

**Decision**: Freeze `formal-ir-v72p2d5-gf32-rate-mother-plan` as `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` (commit `c3499522`, 5 docs +540 lines, zero production `.py` change). Select V31 QC-cyclic-projective `build_layer` (`nonbinary_v31.py:624`) as the sole baseline with per-layer single `M_max=1000` build + `H[:k]` prefix disclosure; keep Lane-C as backup; veto V36/V35. Freeze the prior contract (`P1=sum_u2 P_F`, `P2=P_F/P1`, production `q@P`, oracle-L2 diagnostic-only, `lambda*=137.3823795883264` as sole adapter delta, floor dual-track `1e-300/1e-15`), the `rows=ceil(N*CE*f/5)` table (n=1024: `f=1.0 782/686 tot1468`, `1.05 821/720`, `1.1 860/755`, `1.2 938/823`), and the G0/G1/G2 gates with G2 n=256 as the sole life-death experiment (PASS = `f=1.2` end-to-end >=90% + monotonic + oracle>=APP; FAIL `<50%` route-dead / `50-90%` budget-insufficient both abandon n=1024 real).

**Context**: D4R2 selected model F (`d=1024, U=[5,5], GF32, N=1024`; `CE_L1=3.814742 / CE_L2_oracle=3.347605 / CE_joint=7.162347`) and proved `MODEL_BUDGET_MISMATCH` for the old 216 rows (gap 6254 bits / 1251 rows / 6.79x). D5 answers 6 frozen questions (prior/budget/constructor/mother/synthetic-gate/kill-experiment) without writing code, running any decoder, reading VAL, or creating `run_01`.

**Alternatives considered**:
- V36 incremental (+32 rows, row-weight 10-14) / V35 (192->224 hardcoded): rejected — too dense / hardcoded for 700-1000-row regime.
- V28 small-m constructors / V54 PEG-like incremental without audit: rejected as baseline — unverified at large m / missing rank audit; V28 kept as small-matrix reference, Lane-C as backup only.
- Old 216-row real experiment: prohibited — `MODEL_BUDGET_MISMATCH` ban stands.

**Consequences**: No apply before D5-T8 independent Plan Review ACCEPT (incl OQ1 per-layer `M_max` interpretation / OQ2 90% line decision); any decoder/VAL/n=1024 real execution still needs an independent `EXECUTE_AUTH`. Frozen thresholds/row table must not be relaxed in apply; implementation ambiguity stops to planner/OpenSpec revision on a new SHA.

---

### 2026-09-05: V72P2D5-R1 plan revision PASS, no code no execution

**Decision**: Revise `formal-ir-v72p2d5-gf32-rate-mother-plan` per review (commit `836e151c`, exactly 5 D5 plan files, zero production `.py` change, no `run_01`, Review PASS, `HEAD == origin` ahead 0). Durable deltas: `M_max=1000` is D5 synthetic cap only (not production sufficiency); OQ2 four-state `QUALIFIED/INCONCLUSIVE/CURRENT_CONFIGURATION_FAILED/BLOCKED`, `ROUTE_DEAD` deleted; probability axis `(Alice,Bob)` `axis0` summation; per-prefix 13-item structural gate + minimum 5-item PASS; M0 two-stage natural prefix (non-hypothesis) + deterministic row ordering without decoder; seeds frozen L1 `2026090501` / L2 `2026090502` / G0 `510..517` / G1 `600..699` / G2 `1000..1199`, search banned; oracle non-hard-gate diagnostic-only `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC`; P0 preflight n=64 2 blocks, G1 `<=900s` / G2 `<=3600s` / single-call 120s / RSS `<2GiB`, calls G1 `APP100x2+oracle20x2` / G2 `APP200x3+oracle40x3`; metric `exact_failure_fraction` not FER; lifecycle three-false, no single authorization across G0/G1/G2.

**Context**: R1 answers review OQ1/OQ2 without execution; residual is `M AGENT_PROJECT_MEMORY.md` + `M docs/decision-log.md` + untracked baseline, uncommitted by design.

**Alternatives considered**:
- 90% death-line / `ROUTE_DEAD`: rejected — replaced by four-state verdicts.
- `M_max=1000` as production sufficiency: rejected — synthetic cap only.
- Oracle as hard gate / FER metric: rejected — diagnostic-only / `exact_failure_fraction`.

**Consequences**: Apply still gated by D5-T8 independent Plan Review ACCEPT + independent `EXECUTE_AUTH`; frozen seeds/budgets/call-counts/metric must not be relaxed in apply.

---

### 2026-09-05: coder-fast completion must chain reviewer-go (one-time exception R1 836e151c)

**Decision**: Every coder-fast COMPLETE must be followed by an independent read-only reviewer-go review. Plan-only or zero-production-code is not a skip reason. Any skip requires explicit user approval and dual recording in `AGENT_PROJECT_MEMORY.md` + `docs/decision-log.md`.

**Context**: V72P2D5 R1 push (commit `836e151c`) was pushed without post-commit reviewer review under explicit user approval on 2026-09-05. Read-only check confirms neither `docs/research-cycle-sop.md` (only generic "independent review" in §6 step 7 / §10 Pre-RESULT, zero coder-fast/reviewer-go mentions) nor `AGENTS.md` (only §6 line 180 `/implement-change` pipeline description, no mandatory chaining clause) states the explicit rule.

**Alternatives considered**:
- Directly patch SOP/AGENTS.md now: rejected — workflow-rule changes must go through an OpenSpec change; this entry only persists the rule and proposes wording.

**Consequences**: Schedule reviewer-go after every coder-fast COMPLETE (pre-push or post-commit make-up). Future skips without user approval are violations, not precedents. Proposed SOP patch (via OpenSpec): add mandatory "coder-fast → reviewer-go 必接" clause to `docs/research-cycle-sop.md` §6/§10 and mirror in `AGENTS.md` §3/§10.
## 2026-09-06 — Git identity removed from the default execution gate

- Decision: for this single-user local research repository, commit IDs are
  provenance and recovery aids, not execution capabilities.
- Default Pre-EXECUTE now checks intended branch, scoped file cleanliness,
  frozen scientific inputs/thresholds/command, focused tests, explicit user
  authorization, and output non-overwrite state.
- Rejected default: `HEAD == origin == implementation SHA`, stale-SHA grep,
  self-referential acceptance commits, checksums, and generic watchdog systems.
- Exact revision locking remains available only for a named concrete
  multi-writer, destructive, release, or evidence-integrity risk.
- Scientific review, failure retention, additive outputs, leakage/undetected
  semantics, and independent Pre-RESULT review are unchanged.
- Independent review is milestone-based, not required after every docs-only
  commit or tiny unchanged-scope fix. Existing packets inherit this decision;
  Git-identity clauses are non-binding absent a stated concrete risk.

---

### 2026-09-06: Main-plan roadmap shifted version-number → deliverable (docs only, no new decision)

**Decision**: Record `openspec/project.md` § Roadmap as the durable main-plan
roadmap (D1–D6 plus nearest milestone). No behavior, architecture, prompt,
tool-semantic, or workflow rule is changed by this entry; no new OpenSpec
change is opened for the project.md edit itself.

**Context**: A 2026-09-06 read-only review (no code change, no decoder run,
no CAL/VAL/raw read) found NB-LDPC kernels, layered decoding, and historical
results reusable, but two different-natured gaps remaining: rate/finite-length
validation in the new domain, and the full input→scan→report chain. The
roadmap therefore organizes by six deliverables (D1 D5 input-to-result loop;
D2 new-domain single-point NB-IR; D3 honest `reconciled_net` report interface;
D4 fixed-`d` `tau` scan then `d`×`tau`; D5 parallel security qualification;
D6 best-point plus holdout) instead of version numbers.

**Nearest milestone**: one real ttbin session at fixed dimension producing a
`tau` scan table backed by real NB-LDPC decoding; security-measurement
interface advanced in parallel, dimension widened after.

**Consequences**: Frozen order STRUCTURE → G0 → P0 → G1 → G2 and all V72
scopes/thresholds unchanged; P0/G1/G2 remain unexecuted. Future work cites
`openspec/project.md` for roadmap placement; this entry adds no freeze,
authorization, or scientific verdict.

---

### 2026-09-07: V72P2D5 unauthorized G1 output disposed VOID_RETAINED_IN_PLACE (docs only)

**Decision**: Dispose `workspace/v72p2d5_g1/20260906_r1/` (4 files,
`decoder_calls=440`) as `VOID_RETAINED_IN_PLACE`. Retained unmodified as
forensic evidence of a test-isolation defect; permanently barred from citation
as a G1 result, a performance measurement, or evidence about the NB-LDPC
method. No delete, no move, no rename, no rerun, no authorization change.

**Context**: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` returned
`PRE_RESULT_REVIEW_FAIL` on the single blocker PR16 — the G1 formal root existed
while `g1_execution_authorized=false` and `next_gate=P0_PACKET_REVIEW`. Cause is
incident I09 (tests called `run_g1_synthetic(authorized=True)` without fake
decoder / injected arrays / tmp `out_dir`, so once the Model-F artifact existed
the production decoder bound and the default writer hit the formal root).
Model-F artifact content itself passed PR01-PR15 and PR17-PR23. The isolation
repair is complete and evidenced (165 collected / 165 passed).

**Alternatives considered**:
- Delete the four files: rejected — irreversible, breaks the evidence chain.
- Move to a quarantine directory: rejected — violates incident I08
  (no move/rename/copy).

**Consequences**: All `*_execution_authorized` stay false; `next_gate` stays
`P0_PACKET_REVIEW`; no P0 authorization. PR16 is addressed by record only —
clearance requires an independent Pre-RESULT re-review. A future authorized G1
run must use a new output root and must not reuse or compare against this one.

---

### 2026-09-07: V72P2D5 Model-F input result ACCEPTED (docs only, no authorization)

**Decision**: Accept the canonical Model-F CAL-TRAIN input at
`workspace/v72p2d5_model_f_input/20260907_r1/` as the P0/G1/G2 prior input.
Record acceptance at the cycle level; the artifact's own `status` stays
`MODEL_F_INPUT_CANDIDATE` because rewriting a file inside a protected
immutable root is forbidden and the loader accepts both values.

**Context**: Implementation accepted; Pre-EXECUTE R2 PASS after the PX11 path
fix; exactly one authorized `prepare` plus one `verify` executed 2026-09-07
(authorization consumed); Pre-RESULT R1 FAILed on the single blocker PR16;
the unauthorized G1 root was dispositioned `VOID_RETAINED_IN_PLACE`; the
independent Pre-RESULT R2 returned PASS with C01-C11 all PASS and `195 passed`.

**Material caveat**: PR16 was cleared BY RECORD, not by condition. R1's PR16
was the formal check "formal roots absent"; that condition is still not met —
`workspace/v72p2d5_g1/20260906_r1/` exists. R2 reinterpreted PR16 by its
intent (unauthorized numbers must not enter the result chain) and judged that
intent closed by the disposition. Deletion and quarantine-move were both
explicitly rejected by the user.

**Alternatives considered**:
- Flip the artifact `status` to `ACCEPTED`: rejected — would require rewriting
  inside a protected immutable root.
- Hold acceptance until PR16 is physically cleared: rejected — that would
  require reversing an explicit user decision and adds no scientific
  protection to the Model-F claim.

**Consequences**: All nine `*_execution_authorized` stay `false`;
`scientific_promotion` stays `false`; `next_gate` stays `P0_PACKET_REVIEW`.
P0 is not authorized. Residual risks carried into the P0 packet: `R-R1`
production-side bare-authorized defaults unchanged, recurrence guard is
test-side only, so future P0/G1/G2 packets must re-verify isolation before any
authorization; `R-R2` `M24`/`P12` no longer assert global formal-root absence,
so an unexpected new formal output relies on per-test snapshot comparison
rather than a global gate.

---

### 2026-09-07: V72P2D5 P0 cost preflight ACCEPTED as cost measurement only (docs only, no authorization)

**Decision**: Accept the second authorized P0 invocation at
`workspace/v72p2d5_p0_cost/20260906_r1/` as `P0_RESULT_ACCEPTED` with scope
`COST_MEASUREMENT_ONLY`, recorded in
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_RESULT_ACCEPTANCE_R1.md`.
Acceptance of a cost measurement is not scientific promotion and grants no G1
authorization.

**Context**: Measured scalars transcribed verbatim from `results.json`:
phase `p0-cost`; block_length 64; f_list 1.0, 1.2; frozen_rows f=1.0 -> m1 49 /
m2 43 and f=1.2 -> m1 59 / m2 52; seeds 2026090510, 2026090511; decoder_calls
12; records 1.0 app 1.8862763999495655 / 360 / null, 1.0 oracle
1.04731999989599 / 180 / null, 1.2 app 3.459295800072141 / 360 / null, 1.2
oracle 1.671841400093399 / 180 / null; projected_g1_s 161.8241519993171;
projected_g2_s 485.47245599795133; projection_blocked false; passed true; run
wall (operator) 8.6278899 s, exit 0, stdout and stderr empty; decode-attributed
total 8.064733600011096 s against the 1440 s cap, no `RESOURCE_OVERRUN`.
Four-review chain landed by this packet: `P0_PRE_EXECUTE_REVIEW_R1.md`
`PRE_EXECUTE_REVIEW_PASS` with five open questions decided;
`LOADER_FIX_REVIEW_R1.md` `LOADER_FIX_REVIEW_PASS` for the Model-F consumer
path fix (`299416ae`); `P0_PRE_RESULT_REVIEW_R1.md` `P0_PRE_RESULT_REVIEW_PASS`
with limitations; `GUARD_REWORK_REVIEW_R1.md` `GUARD_REWORK_REVIEW_PASS` with
L1-L4. Authorization history: two P0 authorizations were issued; the first
(2026-09-07, `a71188fb`/`3ecaebb6`) was consumed with no run because the phase
refused in 0.376 s on a false missing-input message caused by the consumer
path defect; the second (`f1cdf970`/`b4696273`) produced this result; both are
consumed and neither is reusable.

**Alternatives considered**:
- Accept P0 as a correctness or qualification result: rejected — P0 records
  cost only; it grades nothing, and establishes no `exact_failure_fraction`,
  no FER, no leakage, no key rate, no net rate, and no qualification of
  NB-LDPC, the dv3 mother, the rate points, or Model-F.
- Treat `projected_g2_s` or `projection_blocked: false` as G2 permission:
  rejected — the projections are `per_call x {240, 720}` with no width or
  row-count scaling, so they grant G2 nothing.
- Create a G1 authorization in this packet: rejected — G1 stays unauthorized
  and unfrozen; freezing, review, and authorization belong to later packets.

**Consequences**: P0 establishes no correctness, no `exact_failure_fraction`,
no FER, no leakage, no key rate, no net rate, and no qualification; no
statement that G1 or G2 will pass, complete, or fit their budgets; no
authorization for anything. Seven limitations carried into the G1 packet, each
tagged `MUST_CARRY_INTO_G1_PACKET`: L1 (depth, top-level-only snapshot),
L2 (T1_23 narrowness), L3 (T1_22 live-fire by logic reading, not live red),
L4 (guard-rework `STATUS=63` superseded by 1969 porcelain lines / 1887
modified paths / `numstat` content changes 0), L-RSS (`rss_bytes` null on
Windows, 2 GiB reference unchecked), L-SCALE (projections carry no width or
row-count scaling; `projected_g2_s` and `projection_blocked: false` grant G2
nothing; `projected_g1_s` is a same-width call-count indication only), L-ITER
(all 12 decodes ran the full `MAX_ITER = 90`, a saturated upper bound; G1 must
budget at the cap and record exact/syndrome outcomes). All nine
`*_execution_authorized` stay `false`; `scientific_promotion` stays `false`;
`next_gate` moves `P0_PACKET_REVIEW -> G1_PACKET_REVIEW`; no authorization was
created. Next: freeze the G1 execution packet carrying every limitation, then
an independent Pre-EXECUTE review, then a separate explicit G1 authorization;
these may not be merged or reordered.

---

### 2026-09-07: V72P2D5 G1 readiness implementation-only acceptance and Pre-EXECUTE packet freeze (docs only, no authorization)

**Decision**: Accept the G1 readiness implementation at `cf61ee63` (predecessor `614aab9e`, spec/review `d47e7da1`) as implementation readiness only, recorded in `G1_IMPLEMENTATION_ACCEPTANCE_R1.md`; freeze `G1_PRE_EXECUTE_PACKET_R1.md` as `G1_PRE_EXECUTE_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`; move `next_gate` to `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`.

**Context**: Review chain — packet review PASS, readiness code review PASS (`G1_READINESS_CODE_REVIEW_PASS`), scope addendum PASS (`G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`, exact frozen three pytest files, `219 passed`), live Windows RSS positive. Accepted functionality: new root `workspace/v72p2d5_g1/20260907_r2`, Windows RSS ABI with 200-sample peak semantics, aggregate exact/syndrome/iteration/RSS fields, prospective signal, outcome precedence (seven labels, `passed` iff `G1_TREND_PASS`), fail-loud writers, no-subdirectory guard, test-only reachability/isolation. Scope is implementation readiness only; no decoder/G1 result, FER, leakage, key rate, qualification, or G2 claim. Real external-file Model-F sentinel and watchdog semantics stay mandatory in Pre-EXECUTE; acceptance grants no authorization. Disclosed boundaries carried: process-vs-entrypoint wall (operator outer wall controls 900 s classification); `app_iterations_max<=180` asserted not clamped; exception/timeout/refusal are operator-side labels; G1 is synthetic trend only.

**Consequences**: G1 remains unauthorized and unexecuted; G2 remains unauthorized. Frozen signal/outcomes/resources and the exact single-attempt command live in the packet. Next is the independent Pre-EXECUTE review (reviewer may not flip authorization or run G1), then a separate explicit user authorization. All nine authorizations stay false; promotion stays false.

---

### 2026-09-07: V72P2D5 G1 result acceptance — synthetic completed-no-signal failure (no pass, no rerun, bounded attribution only)

**Decision**: Accept the sole frozen G1 attempt in `workspace/v72p2d5_g1/20260907_r2` as `G1_RESULT_ACCEPTED` with scope `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`, outcome `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed: false`, recorded in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_RESULT_ACCEPTANCE_R1.md`.

**Context**: Evidence chain `cf61ee63 → 6494b623 → f4d577fb → 58c68961`; dual review (Pre-EXECUTE PASS + Pre-RESULT `G1_PRE_RESULT_REVIEW_PASS`, R01–R09 all PASS on internal coherence). Literals, identical across all four files: both f APP exact `0/100` (rate `0.0`, failure `1.0`), APP syndrome-ok `0`, oracle exact/syndrome `0`, `app_iterations_max 180` (cap `2×90`), APP iterations `18000 = 100×180`, oracle `1800 = 20×90`, `decoder_calls 440 = 400 + 40`, crashes/nonfinite `0`, wall `238.86517630005255 s <= 900` (operator outer `239.110 s`), RSS `115142656 < 2147483648`. Resource gates pass; signal FALSE (top APP exact `0`), so the terminal is a no-signal failure with `passed=false`. Exact/syndrome/oracle stay isolated; stored zeros are literal, never relabeled as FER, undetected success, correctness, or data quality. The single authorized attempt is consumed; no retry/resume/second attempt.

**Consequences**: Not trend pass, qualification, G2 readiness, method success, rerun permission, or reinterpretation of the formal record. All nine `*_execution_authorized` stay `false`; `scientific_promotion` stays `false`; G2 remains absent. `next_gate` moves `INDEPENDENT_G1_PRE_EXECUTE_REVIEW -> G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS`. Next is bounded failure attribution only under the D5 packet: no formal CLI phase, no formal-root write, no VOID-interior read, no G2, no real data.


---

### 2026-09-07: V72P2D5 G1 no-signal attribution (FINITE_LENGTH_DISCLOSURE_INSUFFICIENT, no code change, route decision)

**Decision**: Attribute the accepted G1 dual-zero to `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT` as the sole primary bucket, recorded in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_NO_SIGNAL_ATTRIBUTION_R1.md`; make no code change and return `G1_ATTRIBUTION_ROUTE_DECISION` for one next square-disclosure oracle probe (approve / reject / redirect).

**Context**: 29 development decoder calls (of 300; ~12.9 s wall; peak RSS 113790976 B): accepted Model-F actual CE is L1/L2 ~= 5.0/5.0 bits (uniform priors, I(A;B) ~= 0; counts mean cell 0.25 vs lambda* 137.38) vs frozen sizing constants 3.81/3.35, so frozen rows 49/43 and 59/52 sit below the Slepian-Wolf need 64/64 (f=1.0) and 77/77 (f=1.2). Paired controls on identical samples: APP 0/4 and oracle 0/4 with saturation (formal signature reproduced); full-disclosure H2[:52] control 0/4; doubled cap (180) still fails; decoy-prior probes converge exact=1 on all four frozen prefixes (decoder/graph healthy with signal); GF32 tables/syndrome/rank cross-match exactly. Decoder/APP-propagation/iteration/prefix hypotheses rejected as primary (prefix audit failures carried secondary).

**Consequences**: No OpenSpec/code diff (no implementation defect; frozen constants untouched; formal result unchanged). `next_gate` moves `G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS -> G1_ATTRIBUTION_ROUTE_DECISION`. No G1 rerun, no G2, no real data; all nine authorizations stay false; promotion stays false.

## 2026-09-08 V72P2D5 G1 wide attribution R2 (lambda-contract defect + candidate)

**Decision**: Supersede R1's `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT` as primary with `LAMBDA_APPLICATION_CONTRACT_DEFECT` (R1 bucket carried as downstream secondary); add review-ready nonformal candidate `build_f_model_concentration` + `prepare_model_f_prior_candidate` (additive only) under OpenSpec `v72p2d5-g1-information-recovery-r2`; move `next_gate` to `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`.

**Context**: 53 development decoder calls (~51 s wall; peak RSS 240963584 B; CAL-only, no VAL): frozen `lambda*=137.38` was selected as total per-column concentration (D4R2 `build_f`) but the accepted consumer applies it per cell (140,680 added/column vs 256 observed, 99.82% prior, MI 0.0004 bits vs 2.48 backoff). Same-counts backoff returns to the D4 family (joint 7.51 vs 7.16; held-out C1 7.162347 reproduces D4R2 exactly). Square probe (rank-64 mother, seed 2026090801): C0 oracle 0/4, C1 oracle-L2 4/4; C1 L2 at H2[:52] 2/4; C1 L1 fails at every disclosure including square (mass 0.096 below BP threshold, binding constraint). C2 held-out catastrophic (504.7); C3 dominated (7.34).

**Consequences**: Frozen functions/constants/seeds/thresholds/authorizations/accepted artifacts unchanged; production phases keep the frozen path. One pre-existing suite failure noted (`test_G1R01...` asserts absence of the accepted G1 root; stale since Sept-7 acceptance; untouched). No formal rerun, no G2, no push.

## 2026-09-08 V72P2D5 G1 R2 acceptance (additive backoff-prior candidate, no formal change)

**Decision**: Accept the independently reviewed R2 candidate (`G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`) as `G1_INFORMATION_RECOVERY_R2_ACCEPTED` with scope `ADDITIVE_NONFORMAL_BACKOFF_PRIOR_CANDIDATE`, terminal class `LAMBDA_APPLICATION_CONTRACT_DEFECT`, `formal_g1_result_changed: false`, `production_wiring_changed: false`, recorded in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`.

**Context**: Chain `88053563→a93106f5→21576add→1d4fa912`; like-for-like same-counts `10.0 → 7.51` (MI `0.0004 → 2.48` bits, truth mass `0.031 → 0.254`); three-call square confirmation (old 0/4 vs candidate oracle-L2 4/4); C1 L1 mass `0.096` fails everywhere including square (binding L1 question); C1 L2 recovers only at 52–64 rows (near-zero rate, not an operating point).

**Consequences**: Accepted Model-F/G1 artifacts, thresholds, seeds, authorizations unchanged; production keeps the frozen path. `next_gate` moves `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW -> G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS`. No G1 rerun, no G2, no qualification/promotion, no push.

## 2026-09-08 V72P2D5 G1 L1 discriminator (BP-threshold terminal, route-stop)

**Decision**: Close the L1 discriminator with terminal class `L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64`, recorded in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md`; set `next_gate` to `D5_ROUTE_STOP_REVIEW`.

**Context**: Prereg `f0e4a1c` before any score/call. CAL-only held-out L1 NLL selects E2 (`kap*≈62.10`, unanimous; mean 3.7717 vs E1/E3 3.8147); E1≡E3 bit-identical (backoff linearity under marginalization). Paired decoder (75 calls, 0 nonfinite, flags agree): n64 0/24 incl. square; n128/n256 nonzero-rate 0/4 everywhere; square-only partials 1/4, 2/4. Truth mass ~0.10–0.15 vs ~0.28 needed. No code justified; production untouched; four-file suite 259 passed.

**Consequences**: Stop n64 two-layer L1 recovery and block scaling; no G2; any successor is a new decoder/matrix change, not estimator work. Formal G1 negative result unchanged; all authorizations false; no push.

## 2026-09-08 V72P2D5 D5 route-stop acceptance (current-path stop, decomposition successor)

**Decision**: Accept `D5_ROUTE_STOP_REVIEW_PASS` as `D5_ROUTE_STOP_ACCEPTANCE_R1.md`: terminal `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`, reason `ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY`, scope exactly the current fixed high-five/low-five two-layer rate-mother/BP path.

**Context**: Independently reviewed chain R2 acceptance `247f8adc` → prereg `f0e4a1cf` → evidence/gate `d6fabf09`; review `D5_ROUTE_STOP_REVIEW_R1.md` landed unchanged (S01–S11 PASS, S12 advisory).

**Consequences**: GF32/NB-LDPC stays open; formal G1 stays accepted completed-no-signal (not rewritten); G2 unauthorized and absent; successor is the reversible 5+5 bit-partition decomposition discriminator (252 ordered partitions, CAL-only, bounded paired development decoder). `next_gate` moves `D5_ROUTE_STOP_REVIEW -> D5_DECOMPOSITION_SUCCESSOR_PREREG`. No push.

## 2026-09-08 V72P2D5 decomposition successor R1 (no N64 recovery, graph/mother route next)

**Decision**: Close the reversible-partition discriminator with terminal `DECOMPOSITION_NO_N64_RECOVERY`, recorded in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_R1.md`; no code/OpenSpec implementation (§4.6 not-strong branch).

**Context**: Prereg `e4d3af7` before scores/calls. 252 partitions CAL-only (chain err ≤ 8.88e-16; joint 7.162347 invariant; control reproduces c1 E1 3.814742); rank-1 IS the current mapping `(5,6,7,8,9)` m=(59,52). 192/600 dev calls (100.8 s, peak RSS 124219392 B, 0 crash/nonfinite/disagreement): APP exact 0/8 everywhere incl. square; oracle-L2 6/8 non-square + 8/8 square on rank-1 only (diagnostic). Evidence `workspace/d5_decomposition_successor_r1_c765e3010674/`; four-file suite 259 passed.

**Consequences**: Decomposition family exhausted without APP signal; next route `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL` by main-thread proposal (not authorized). Formal G1/Model-F/roots unchanged; all authorizations false; no push.

## 2026-09-09 V72P2D6 R1c-A3 post-run verifier rework (blocked run, topology claim forbidden)

**Decision**: Accept `D6_R1C_A3_PRE_RESULT_REVIEW_PASS_BLOCKED_RUN`: the R1c-A2 root solidifies as an implementation/structure-blocked development attempt with recomputed terminal `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`; stored `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` is preserved but unsupported and must not be cited.

**Context**: A2 verifier FAILs repaired via OpenSpec amendment (identity key +`n`; stage-separated canary/scaling-per-width/confirmation recompute; crash precedence with degree→invariant class; EMPTY confirmation label; stored+recomputed reported fail-closed). Forensics (read-only, zero decoder): 184 rows reconcile 104/40/40/0; 64 attempted degree crashes from degree-1 check rows in frozen T3/M1 graphs (integer proof + structure-only rebuild with negative controls; transport/precondition excluded). Corrected `--verify` once on the immutable root: exit 0, 15/15 PASS + agreement False. Focused 42/42; seven-file non-perf 323/323; v38 skipped (recorded).

**Consequences**: `next_gate` → `D6_GRAPH_MOTHER_R1C_A3_BLOCKED_AWAITING_MAIN_THREAD_ROUTE` (successor needs new OpenSpec + fresh authorization; nothing granted here). Exposed audit gap: structural eligibility gates `zero_rows` but never minimum check degree — candidate rule for any successor proposal. All authorizations false; G2 absent; no push.

## 2026-09-09 V72P2D6 R1c-A4 structure performance (READY, no run authorized)

**Decision**: Accept `D6_R1C_A4_PERFORMANCE_REVIEW_PASS`: scaling structure wall 10897.7 s → 2.5 s (≈4280×, pruned T2 + two-build replay, bit-identical science for dispatched arms); n64 outputs exactly equal at 21.0 s (was 42.2 s); RSS ≈ 90 MB; zero decoder calls. Final state `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` (structure path only).

**Context**: Profile-first (T2 ≥99.9% of scaling pools); three frozen optimizations (pruning, ≤2 constructions, overflow passthrough; T2 semantics untouched); equivalence proven against committed A2 evidence (n64 all-arms + T1/M1 at n128/n256 exact); fresh-root benchmark cold+warm after-side, cold before-side; before-warm-n256 disclosed unmeasured with seconds-level bound (zero gate impact at 1000×+ margin). Focused 51/51; seven-file non-perf 332/332.

**Consequences**: Any future D6 execution still needs its own OpenSpec + Pre-EXECUTE + explicit authorization — nothing granted. T2 semantics at n64 unchanged. All authorizations false; G2 absent; no push.

## 2026-09-10 V72P2D6 R1c-A5 validity closure, repair infeasibility, R1d readiness (eligible-only branch)

**Decision**: Accept `D6_R1C_A5_REVIEW_PASS_ELIGIBLE_ONLY_BRANCH` (implementation + validity reviews): the I1 check-degree invariant defect is proven and gated; admissible repair is structurally infeasible as frozen; the R1d package is recorded `NOT_AUTHORIZED`.

**Context**: Independent 144-cell matrix (own implementation; 132/132 main-thread cross-check, 51/51 recompute, replay all True): T3/T4/M1 carry degree-1 check rows at f1.2+square everywhere (M1 exactly at the zone-counting bound); T2 rank-deficient at every square (63/62, 123/122, 246/240); B0/B1 bounds recorded unmodified. Frozen eligible + A2 selection {B0,B1,T1,T3,M1} reproduced exactly. I1 landed (eligible-AND, dispatch guard, verify INFO/PASS-FAIL) with fake-only tests; builders byte-identical; historical root verify exit 0, 15/15 PASS, agreement False, mtimes intact. Repair study: 0/10 preregistered sandbox rules admissible (R3 fails everywhere; three identity non-repairs) with per-family infeasibility proofs + a 3-option `REQUIRES_MAIN_THREAD_RULING` menu, nothing landed. Focused 56/56; seven-file non-perf 90/90 (membership reconstructed and named).

**Consequences**: `next_gate` → `D6_GRAPH_MOTHER_R1C_A5_TRACK_A_COMPLETE_TRACK_B_PENDING`. R1d viable without a ruling only on the eligible-only {B0,B1,T1} branch — itself unauthorized here. All authorizations false; G2 absent; no push.

## 2026-09-10 V72P2D6 R1c-A6 exact-equivalent T2 acceleration (PASS, no NOT_MET)

**Decision**: Accept `D6_R1C_A6_REVIEW_PASS`: staged/vectorized/integer-encoded T2 (`_build_T2_support_fast`, reference intact, key/order frozen, no float) proven exactly equal at all seven gates; all performance targets met with ≥10x factors; A4 gains not regressed.

**Context**: Equivalence — T2 n64 live-vs-reference, n128/n256 vs replay-verified committed fixtures, per-variable traces, committed n64 rows byte-identical, eligible/selection unchanged, replay + seq==par, A4 guards green, sandbox-T2 gate vacuous (no sandbox T2 exists). Benchmark (fresh roots, cold+warm, A4 protocol): T2/layer n64 1.2 s (≤5, 34.5x), n128 26.6 s (≤90, 24.7x), n256 516.1/479.7 s (≤600, 19.9x); n64 all-8 1.5 s (≤8); fb-only 0.6/1.3 s vs A4 2.5/2.7 s; RSS ≈ 93 MB; zero decoder calls; no retry. Slow-task inventory measured (v38 T0 2.0 s, T1 812/810 s, orchestration 345/344 s, lane-A ≈40 s, helpers ≤46 ms; V30R 74.8/719.9 s cited, decoder-bound, not re-runnable). Focused 61/61 + slow n256 cell; seven-file non-perf 95/95.

**Consequences**: `next_gate` → `D6_GRAPH_MOTHER_R1C_A5A6_COMPLETE_AWAITING_MAIN_THREAD_RULING`. T2-at-n256 no longer breaches the chunk block on structure cost. Any future D6 execution still needs its own OpenSpec + Pre-EXECUTE + explicit authorization — nothing granted. All authorizations false; G2 absent; no push.

## 2026-09-10 V72P2D6 R1d Option C freeze (eligible-only {B0,B1,T1}, Pre-EXECUTE pending)

**Decision**: Main-thread ruling Option C accepted and frozen: no SC/M knob lift (A rejected: R2 degree-profile lift + selection re-freeze; B rejected: M-over-B identity weakening + re-freeze; both reopen repair research); SC/accumulator structurally inadmissible as frozen; R1d = {B0,B1,T1} with T2 rank-bound recorded only; no A2 call/root reuse; schema `r1d-v2` approved for new roots (historical A2 immutable, old schema).

**Context**: 22 distinct R1d structure cells (26 role-cells; 4 T1-n64 cells shared by canary+confirmation) proven ⊆ A5 valid subset (CSV read, zero decoder, 22/22 frozen+I1 pass, 0 conflicts; worst-case 552 ≤ 2500 calls). New OpenSpec change `v72p2d6-gf32-graph-mother-r1d-option-c` + `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md` + `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` (exact `--r1d` command, budgets, stop rules, no-reuse, claim ceiling). R1d NOT authorized, NOT executed; no R1d root exists.

**Consequences**: `next_gate` → `D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. Eligible-only `--r1d` implementation + focused tests + independent reviews next. All authorizations false; G2 absent; no push.

## 2026-09-10 V72P2D6 R1d Option C implementation + Pre-EXECUTE (PASS, awaiting explicit authorization)

**Decision**: Accept `D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (implementation review `D6_R1D_IMPLEMENTATION_REVIEW_PASS` first, zero rework rounds; this review grants no authorization).

**Context**: Eligible-only dispatch layer landed (mother module pure-append: `R1D_ARMS`, 22-cell `R1D_VALID_SUBSET`, arm/subset/live-I1 guard, T1-only fallback, schema-`r1d-v2` writer for new roots, 4-root named refusal; `--r1d` runner mode default-off with frozen default call shapes intact per the A4 pin). 13 focused R1d tests (all 12 packet properties + `--dry-structure` behavioral run) + full D6 file + seven-file non-perf suite: 356/356 green in a fresh task-owned basetemp. Perf-v38 skipped (scoped deps outside the v38 orchestration path; v38 file has zero v72p2d6 references). Independent subset re-derivation 22 == 22, 0 matrix-invalid, live spot-check pass. No R1d root exists; historical A2 header still old-schema, path git-clean; zero decoder calls throughout.

**Consequences**: R1d stays NOT authorized, NOT executed (`next_gate` unchanged: `D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`). Execution needs a separate explicit main-thread grant; mandatory Pre-RESULT review before any solidification. All authorizations false; G2 absent; no push.

## 2026-09-10 D7-A GF32 decoder ground-truth certification PASS (no production change)

**Decision**: Record D7_A_DECODER_CERTIFICATION_PASS. Historical row-layered FFT-QSPA kernel matches the independent oracle (tables exact; check-update worst 3.3e-16; tree posterior worst 6.7e-16; loopy per-sweep worst 7.2e-13; L1->L2 soft-APP bridge verified, final_beliefs log-domain, no double-softmax); all within tol 1e-10 with zero production diff and no trace hook.

**Context**: New oracle comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_decoder_certification.py + 14 tests (14/14); related v35/D5 files 204/204 combined; D6/field files 88 pass + 1 pre-existing unrelated CRLF-churn hash-pin failure (qldpc_reference.py, untouched). Tiny synthetic in-memory calls only; R1d still paused, G2 absent, all auth keys false, no push.

**Consequences**: next route D7_B_EASY_REGIME_PACKET_FREEZE readiness only (design, no execution). D7-B/C/D execution, R1d, G1, G2 all unauthorized. Evidence: docs/research_cycles/V72P2D7-GF32-DECODER-CERTIFICATION/ (PREREG/REPORT/REVIEW).

## 2026-09-10 D7-B easy-regime freeze, harness + independent Pre-EXECUTE (PASS, awaiting explicit authorization)

**Decision**: Accept `D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (implementation review `D7_B_IMPLEMENTATION_REVIEW_PASS` first, zero rework; neither grants authorization nor runs D7-B).

**Context**: R1+A1 frozen: 64 cells (4 tiers x 4 priors x seeds 2026091200..03), caps [1,2,4,8,16,32,90], 420-call global stop, 120/1500/1800(+30)s, <2GiB. TREE_6 is the literal A1 topology (rows [3,3,2], c0=[0,1,2]/[1,7,13], c1=[2,3,4]/[29,1,7], c2=[4,5]/[13,29]; V=9/E=8, var degs [1,1,2,1,2,1], rank 3); superseded R1 [2,3,2]/7-edge tuple impossible (7<8) and rejected by regression test, never dispatched. Tree-exact is dual message-passing vs 1024-projection cross-check (never 32^6, never production/FFT). Harness `formal_ir/v72p2d7_gf32_easy_regime.py` + 19 tests + gated runner; D7-A oracle reused, v35/D5 read-only. Qualification: py_compile clean; D7-B 19/19; D7-A 14/14; v35 25/25; field milestone 13/14 with the same pre-existing CRLF hash-pin failure (isolated). Live env: RSS 85139456 int; timeout.exe present, 3s rehearsal exit 124; out-of-repo reachability with repo-off-sys.path, sentinel, empty tempdir, zero scientific calls; fresh UUID target absent; unauthorized run refuses with no root. Tiny production contacts only (n=3 single-check k<=2 proxy check); `_EXECUTION_CONSUMED` false; no D7-B root.

**Consequences**: D7-B NOT authorized, NOT executed (`next_gate`: `D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`). Execution needs a separate verbatim user grant for one UUID; mandatory Pre-RESULT review before any result. R1d stays paused; G1/G2 unauthorized; no push.

## 2026-09-10 D7-B WSL launch rework + renewed Pre-EXECUTE (PASS, awaiting fresh explicit authorization)

**Decision**: Accept `D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS` (zero repair cycles) then `D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION` (grants nothing, generates no UUID). Spent UUID `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` stays exhausted; disposition `D7_B_PRE_EXECUTION_LAUNCH_BINDING_BLOCKED` retained as a launch defect with no terminal/count/result inferred.

**Context**: Zero-decoder probe proved the 5-step package-context cause (file-location load, package absent, top-level v35 fallback, relative import without parent). Repair is runner-local only (+4 lines: `<repo>/comparison_bench/src` from resolved `__file__`, insert-if-absent before core load); core/v35/D5/D7-A/field byte-unchanged; fallbacks still `except ModuleNotFoundError`-only. L01–L12 green (miniature original-failure capture; help/dry-run both cwds; 64 cells; src-only insertion; exact package v35 bind never called; fake-shadow refusal; unauthorized exit 3 pre-bind; 19+14 suites green; frozen contract; roots/auth unchanged). Full D7-B 31/31, D7-A 14/14, v35 milestone 25/25. WSL identity: venv python 3.12.3, NumPy 2.4.4, kernel 6.18.33.2-WSL2, GNU timeout 9.4, RSS 9416704, 3 s rehearsal exit 124; external binding probe reached the exact v35 callable with zero call/zero root. WSL-A1 addendum freezes shell-spelling-only command shape; no new UUID.

**Consequences**: Documented gate `D7_B_WSL_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` (docs only; `cycle_state.yaml` untouched, all keys factually unchanged). Any future run needs a fresh explicit user authorization naming one new UUID. R1d stays paused; G1/G2 unauthorized; no push.

## 2026-09-10 D7-B WSL R2 scoped result acceptance (RESOURCE_OVERRUN retained, hard-decision limits disclosed)

**Decision**: Accept the WSL R2 root (`c605d1e6-8577-4c52-a865-12500fc8c964`) as authentic, immutable and contract-faithful with the stored terminal `D7_B_RESOURCE_OVERRUN` retained. Accepted scope is exactly `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`: 64/64 exact+syndrome hard decisions at cap 1; 49 iteration-0 + 15 iteration-1; posterior tolerance failed (SINGLE max ~0.500, TREE max ~0.400 vs 1e-10) while MAP agreement passed; RSS null is telemetry unknown (WSL venv lacks psutil) with no measured breach and no `<2GiB` PASS claimed. `CONFIRMED`/`PARTIAL`, FER/leakage/key-rate/CAL-recovery/qualification/R1d/G2-permission/broad NB-LDPC conclusions are all refused.

**Context**: `D7_B_RESULT_ACCEPTANCE_R2.md` states packet §3's twelve points without reinterpretation; pre-result review `D7_B_PRE_RESULT_REVIEW_PASS_R2`; root read twice with identical names/sizes/mtimes (111/44743/1008/80/449); zero decoder calls, zero root/production edits, no VOID reads.

**Consequences**: `next_gate` → `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT` (zero-decoder soft-belief audit R1 next). All authorizations stay false; R1d/G1/G2 unauthorized; no push.

## 2026-09-10 D7-B early-exit soft-belief audit classification + independent review PASS (next route interface correction)

**Decision**: Classify the early-exit soft-belief evidence as `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT` (primary) + `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP` (secondary); independent review `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`.

**Context**: `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md` (E01–E12, zero decoder calls) with one review-§4 transcription correction (E06: 25 tractable it0 rows + 4 TREE PAIR it1 rows at 0.00689, total failures 29 unchanged; E05 stratification already correct); review `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md` re-verified 49/15 partition, v35 it0 return path, all consumers, and I1/I2/I3 split; R2 root five files unchanged; terminal stays `D7_B_RESOURCE_OVERRUN`.

**Consequences**: `next_gate` → `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL` (before D7-C) per §8 mixed/interface mapping. All authorizations stay false; R1d/D7-C/D/G1/G2 unauthorized; no push.

## 2026-09-11 D7-B layer-interface proposal PASS + D7-C bidirectional-oracle freeze/implementation/Pre-EXECUTE (no execution)

**Decision**: Accept `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING` (OpenSpec `v72p2d7-layer-interface-belief-provenance` + `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md`, commit `86f6baf6`): preferred alternative A exposes a `belief_provenance` enum `PRIOR_ONLY`/`CHECK_UPDATED`/`WARM_START_UNSPECIFIED` and makes cross-layer APP consumers fail closed unless `CHECK_UPDATED`; interface implementation is mandatory before any sequential/alternating/joint cross-layer APP route but not before D7-C; no historical result is reinterpreted; no v35 stopping change. Accept the D7-C R1+A1 freeze and its reviews (`D7_C_IMPLEMENTATION_REVIEW_PASS`, 0 rework / 20 tests; `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`).

**Context**: D7-B documented next route `D7_C_BIDIRECTIONAL_ORACLE_PACKET_FREEZE_INTERFACE_REWORK_DEFERRED`; consumer inventory 22 production/interface `final_beliefs` entries + V64 runner extension, sibling `nonbinary_v10_fftqspa.py` excluded. D7-C commits `0c304875` / `391fc6b0` / `ca00b234` plus a separately committed Pre-EXECUTE review (SHA not recorded here). Accepted H03 estimator `d5.prepare_model_f_prior_candidate` / `build_f_model_concentration` (`LAMBDA_STAR=137.3823795883264`, per-Bob-column total concentration); `prepare_model_f_prior` / `build_f_model` rejected (`LAMBDA_APPLICATION_CONTRACT_DEFECT`, per-cell pseudocount). Frozen matrix: n=64, seeds `2026091300..2026091315`, f `[1.0,1.2]`, L1 rows 49/59, L2 rows 43/52, D5-native mothers 49/2026090501 + 43/2026090502, 128 calls, budgets 120/1500/1800+30 s / <2 GiB, six scalar files, four direct `J` priors, no cross-layer belief flow.

**Consequences**: D7-C NOT authorized and NOT executed; all authorization false, no UUID, no `workspace/d7_c_bidirectional_oracle_*` root; D7-B R2 root `c605d1e6-8577-4c52-a865-12500fc8c964` immutable; R1d paused; G1/G2 unauthorized. `next_gate` `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; parallel state `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`. Mandatory Pre-RESULT review before any result publication; no push.

## 2026-09-11 D7-C result acceptance (bounded bidirectional-dependence diagnostic; route to D7-D schedule discriminator)

**Decision**: Accept the immutable D7-C run and independent review as `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC` per main-thread adjudication §0 of `D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`, recorded without reinterpretation in `D7_C_RESULT_ACCEPTANCE_R1.md`. Accepted scope: 128/128 frozen single-layer calls completed, finite and internally coherent; exact and syndrome agreed on all calls, 43/128 exact; f=1.0 L1 marginal/oracle `0/16 -> 10/16`, L2 `0/16 -> 1/16`; f=1.2 L1 `3/16 -> 16/16`, L2 `0/16 -> 13/16`; f=1.2 has `STRONG_ORACLE_LIFT` in both layers; run terminal `D7_C_BIDIRECTIONAL_DEPENDENCE` accepted as a bounded mechanism-classification result; no crash/nonfinite/resource/watchdog issue, RSS known and below 2 GiB; D7-C did not consume cross-layer returned beliefs and is not affected by the deferred D7-B APP-interface implementation. Route the next mainline stage to D7-D (isolate schedule only; do not implement alternating/joint BP).

**Context**: Scientific interpretation ceiling held verbatim — accepted that true other-layer symbols materially improve recovery under the frozen priors, matrices, decoder, disclosures, n=64 and 16 paired blocks; NOT accepted that an implementable alternating/joint decoder can generate that information, bootstrap from marginal priors, achieve FER, improve leakage/key rate, qualify the code, or generalize beyond this matrix; f=1.0 L2 remains effectively unrecovered even with oracle (1/16). Immutable evidence: sole UUID/root `94c0ea15-a786-4cb8-a991-6fec521cccae` (six files, zero subdirs, 282/23599/2709/1130/362/728 B), lifecycle authorize `b07b5441` → one invocation → revoke `d3bd3c8b` → result `b4ba2896`, independent Pre-RESULT `D7_C_PRE_RESULT_REVIEW_PASS_R1`, verifier `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_C_BIDIRECTIONAL_DEPENDENCE'}`. Four 2×2 paired counts (oracle_only/marginal_only/both/neither per stratum): f=1.0 L1 `10/0/0/6`, f=1.0 L2 `1/0/0/15`, f=1.2 L1 `13/0/3/0`, f=1.2 L2 `13/0/0/3` (each sums to 16; no `marginal_only` pair anywhere). Resources: outer wall `33.743` s, stored wall `32.631` s, max call `0.439` s, RSS `105172992` B, exit 0, timeout-124 false.

**Consequences**: `next_gate` → `D7_D_SCHEDULE_DISCRIMINATOR_PACKET_FREEZE`. D7-D is a readiness stage only — no D7-D root/UUID, no alternating/joint bootstrap, no FER/leakage/key-rate/CAL/qualification/promotion claim, and layer-interface implementation remains deferred and mandatory before any cross-layer APP route. All authorizations stay false; R1d/G1/G2 unauthorized; D7-C and D7-B roots immutable; no push.

## 2026-09-11 D7-D schedule-discriminator freeze/implementation/certification acceptance (readiness only, awaiting explicit authorization)

**Decision**: Accept the D7-D schedule-discriminator freeze, implementation, and flooding certification as READINESS ONLY, recorded with `D7_D_IMPLEMENTATION_REVIEW_PASS` and `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (commit `727bca7a`; pre-execute review doc uncommitted at review time). Neither review verdict grants authorization, generates a UUID, or runs anything.

**Context**: OpenSpec `v72p2d7-gf32-schedule-discriminator` + prereg/execution packet committed `3a05899`; discriminator module `v72p2d7_gf32_schedule_discriminator.py` + tests + runner `scripts/v72p2d7_gf32_schedule_discriminator.py` + flooding certification doc committed `43f07186`. Frozen matrix: 128 D7-C identities × schedules `[ROW_LAYERED, FLOODING]` = 256 calls, `call_idx` `2k-1`/`2k`, identical non-schedule inputs within each pair. Certification/reviews: F01–F08 flooding certification all PASS; S01–S22 all PASS (30-test suite). Regression scope: D7-A 14 / D5 165 / v35 25 green; D7-B scoped 29 green; D7-C raw 19 passed with the stale pre-execution `test_c19` invariant non-blocking (S20 scoped deselection; refresh as a separate scoped change). Environment unchanged (Python 3.12.3 / NumPy 2.4.4 / GNU timeout 9.4; venv-on-PATH adapter carry-forward).

**Consequences**: `next_gate` → `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. All authorizations false; no D7-D root/UUID; the 256 scientific calls remain unauthorized; layer-interface implementation still deferred and mandatory before any cross-layer APP route; R1d/G1/G2 unauthorized; no push. No FER/leakage/key-rate/qualification/promotion implications.

## 2026-09-11 D7-D bounded result acceptance (schedule effect inconclusive; route to BP provenance Alternative A)

**Decision**: Accept the reviewed D7-D run (UUID `64660d16-397d-4ef3-8454-3066d27c12c7`) as `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE` per §0 of `D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md`, recorded without reinterpretation in `D7_D_RESULT_ACCEPTANCE_R1.md` (Phase-A A01 independent recomputation: 0 discrepancies). Accepted facts: 256/256 paired calls completed; row-layered exact `43/128`, flooding exact `40/128`, layered-only `3`, flooding-only `0`, both `40`, neither `85`; no crash/nonfinite/watchdog; stored terminal `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; independent Pre-RESULT `D7_D_PRE_RESULT_REVIEW_PASS_R1`; budgets passed. The three layered-only identities are 26 (1.0/2026091306/L1_ORACLE_U2), 46 (1.0/2026091311/L1_ORACLE_U2) and 101 (1.2/2026091309/L1_MARGINAL).

**Context**: The frozen matrix establishes no preregistered flooding or layered advantage; `43 vs 40` and the three layered-only pairs are reported, not promoted into a schedule-superiority claim; schedule choice is not supported as the dominant explanation of the current failures. D7-C's accepted bidirectional oracle dependence remains the stronger route evidence but does not prove that alternating/joint BP can bootstrap. No FER, leakage, key rate, qualification, promotion, general schedule equivalence or general NB-LDPC conclusion. Eight strata labels (no advantage stratum): `EXACT_TIE_LOW, MIXED_SCHEDULE_EFFECT, EXACT_TIE_LOW, EXACT_TIE_LOW, EXACT_TIE_LOW, EXACT_TIE_HIGH, EXACT_TIE_LOW, EXACT_TIE_HIGH`. Immutable root: seven files 3164/57659/17690/1777/1546/455/290 B, whole-file read twice identical; lifecycle authorize `7a3f0d92` → one invocation → revoke `eba385bb` → result `63a69f57`; verifier `VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}`; outer wall 67.178 s, stored wall 65.945 s, max call 0.436 s, RSS 105304064 B. R1d becomes `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`; G1/G2 unauthorized; old D5/D6 checkboxes are historical accounting, not gates to dimension generalization.

**Consequences**: `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE` has no frozen automatic successor; this ruling selects Alternative A (explicit belief provenance plus fail-closed cross-layer consumers) as the next mainline action. `next_gate` → `BP_INTERFACE_PROVENANCE_IMPLEMENTATION`. No forced sweep (Alternative B), warm-start mechanism, alternating/joint decoder or scientific decoder run is authorized. Dimension/bw expansion waits for a working provenance-safe fixed-dimension mechanism and, for more than two layers, a separate mathematical/leakage contract. All authorizations stay false; D7-D/D7-C/D7-B roots immutable; no D7-E work; no push.

## 2026-09-11 NB-Polar documents initialized; hybrid APP-transfer draft archived

**Decision**: Establish NB-Polar as an independent successor track in
D:/Code/HD-QKD_Polar_Comparison-nbpolar with status
PLAN_CANDIDATE / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED.
The canonical planning set is docs/nbpolar/ plus OpenSpec change
formal-ir-nbpolar-mvp. Keep this Comparison checkout as the owner of
NB-LDPC history, accepted D5–D7 evidence, and cross-project decisions.

**Context**: The former live change formal-ir-future-nbpolar-app-transfer
coupled a proposed NB-Polar upper layer to the unresolved NB-LDPC lower layer
and its APP/provenance contract. That coupling would make a decoder failure
hard to attribute to prior, algorithm, implementation, or topology. The new
plan freezes a native GF32 q-ary Polar MVP (polynomial basis, primitive
polynomial 37, explicit 2×2 kernel, normalized symbol metrics, source SC,
static disclosure, one final universal tag) and separates oracle, synthetic,
and real-data gates.

**Disposition**: Move the old proposal, design, tasks, and spec unchanged to
openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/
with an archive record. Preserve dated V32/V33/Route B-lite references as
historical provenance; they are not current implementation requirements.

**Consequences**: No NB-Polar code, decoder, benchmark result, real-data run,
leakage/security claim, qualification, promotion, or push is authorized by
this entry. D7-E remains the active Comparison gate. The next action is
independent review of the Phase 0–2 packet in the sibling worktree; only
after its gates pass may implementation begin.

## 2026-09-11 BP interface provenance Alternative A implemented + reviews PASS (route to D7-E packet freeze)

**Decision**: Accept the layer-interface belief-provenance Alternative A implementation (commit `654fa299`, OpenSpec delta `5483dd8`) as complete and independently reviewed: `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS` and `D7_BP_INTERFACE_READINESS_REVIEW_PASS`. Mark BP-01…BP-05, BP-07, BP-08 complete; BP-06 is complete only as a frozen non-implementation boundary (`WARM_START_DEFERRED`); `layer_interface_implementation` = `IMPLEMENTED_ALTERNATIVE_A_FAIL_CLOSED`.

**Context**: Alternative A only (B/C absent): v35 producer exposes the additive defaulted `belief_provenance` field, D5 `_decode_block` and the active cross-layer consumers carry/guard it, and conditioned cross-layer APP fails closed unless provenance is exactly `CHECK_UPDATED`. No hard-decision/numerical/stopping drift; no warm-start implementation; no historical result recomputed. Reviews verified failure matrix, enum mapping, tests and protected roots; no real artifact/decoder run in this packet.

**Consequences**: `next_gate` → `D7_E_PROVENANCE_SAFE_CROSS_LAYER_DISCRIMINATOR_PACKET_FREEZE`, `d7e_state` = `NOT_FROZEN_NOT_AUTHORIZED`. R1d remains optional/paused (`PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`); G1/G2 remain unauthorized; dimension/bw expansion stays gated. No scientific execution. External-push observation to `nbpolar-origin/codex/nbpolar-phase0` is noted as not performed by the WSL operator. D6 latent arity fix/migration (and its fail-closed guard) is required under a new scoped change before any D6 rerun (see `docs/troubleshooting.md`). All authorizations stay false; no push.

## 2026-09-11 D7-E frozen + dual-reviewed awaiting explicit authorization; D6 R1d compat repaired, R1d optional/paused (no execution)

**Decision**: Record D7-E provenance-safe cross-layer discriminator as frozen at `f82804f6` (OpenSpec `v72p2d7-provenance-safe-cross-layer-discriminator`, prereg + execution packet; 192 slots = 128 mandatory + up to 64 transfer, row-layered-only, `CHECK_UPDATED`-only transfer, estimator hard contract), implemented (25 focused tests green) and dual-reviewed (`D7_E_IMPLEMENTATION_REVIEW_PASS`, `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` — grants nothing). State `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; all authorizations false; no UUID; no roots; nothing executed. Record D6 R1d BP-provenance compat repair zero-decoder (commits `9563c36f`/`6fc3d893`/`da359ec5`; R05/R06 PASS) with prior R1d Pre-EXECUTE stale/superseded; R1d stays `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`, not a mainline gate. G1/G2 unauthorized.

**Context**: Track A repaired the five-vs-six `_decode_block` arity with fail-closed provenance and renewed readiness review; Track B froze the bidirectional single-pass transfer discriminator. No scientific conclusions; no FER/leakage/key-rate/qualification/promotion claim.

**Consequences**: Next gate is explicit authorization of D7-E under a separate packet; no D7-E/R1d/G1/G2 execution is authorized by this entry; no push.

## 2026-09-11 D7-E WSL RSS telemetry rework A2 complete (telemetry-only; no execution)

**Decision**: Accept the telemetry-only RSS rework as complete: OpenSpec delta + addendum `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md` (freeze `becf60f`), implementation `9e09538` (VmHWM-only fail-closed reader, 15 `test_a2_*`), dual-reviewed (`D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2` + `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` with single live E09 `VmHWM 96484 kB → 98803712 B`). State → `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`; all authorizations false; attempts/completed zero; no UUID/root; nothing executed; no push.

**Context**: WSL `ru_maxrss` disagreed with VmHWM by GiBs, making E09 non-deterministic; the frozen A2 rule reads peak RSS only from `/proc/self/status` VmHWM. The prior user authorization is not reusable — a later execution needs a fresh explicit authorization referencing RSS A2.

**Consequences**: R1d stays paused/optional (not a mainline gate); G1/G2 unauthorized; no D7-E/R1d/G1/G2 execution authorized by this entry.

## 2026-09-11 D7-E accepted as directional cross-layer transfer diagnostic; route to D7-F reverse-order freeze

**Decision**: Accept the immutable D7-E result under the narrow scope
`D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`
(`docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_RESULT_ACCEPTANCE_R1.md`).
A01 independently recomputed the four strata from committed scalars and confirmed the packet §1
ruling exactly: 192/192 calls, 64/64 transfer eligible+invoked, f=1.0 both directions 0/16–0/16,
f=1.2 L1_TO_L2 control 0/16 transfer 3/16 (`AMBIGUOUS_TRANSFER_EFFECT`), f=1.2 L2_TO_L1 control 3/16
transfer 7/16 with four transfer-only and zero control-only (`STRONG_TRANSFER_LIFT`), terminal
`D7_E_L2_TO_L1_TRANSFER_LIFT`; integrity `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP` with the
original `BLOCKED` review retained.

**Context**: Permitted inference is direction-dependent useful transfer, strongest L2_TO_L1 at f=1.2,
for this frozen synthetic contract only. Unsupported: general success, FER/leakage/key-rate,
qualification, real-data, alternating-convergence proof, R1d/G1/G2 permission.

**Consequences**: `next_gate` → `D7_F_REVERSE_ORDER_PACKET_FREEZE`; D7-F tests whether the lift
survives as complete two-layer recovery in reverse order, with no feedback cycle yet
(cavity/extrinsic still missing). All authorizations stay false; no push.

## 2026-09-11 D7-F accepted as reverse-order regression diagnostic; route to D7-G extrinsic contract proposal

**Decision**: Accept the immutable D7-F result under the narrow scope
`D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`
(`docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/D7_F_RESULT_ACCEPTANCE_R1.md`).
Phase-A independently recomputed the paired tables from committed scalars and confirmed the packet
§1.1 ruling exactly: 128/128 calls with zero blocked/retry/crash/nonfinite/watchdog; f=1.0 forward
and reverse both-exact 0/16; f=1.2 forward both-exact 2/16 (seeds 1302/1304), reverse 0/16;
table candidate_only 0 / reference_only 2 / both 0 / neither 14; forward source exact 3 and target
exact 3 overlapping on only 2 identities; reverse source L2 exact 0 while target L1 exact 7;
terminal `D7_F_REVERSE_ORDER_REGRESSION` internally consistent.

**Context**: Permitted inference is that a single sequential reversal does not convert the D7-E
directional target lift into complete two-layer recovery under this frozen contract. Unsupported:
L2→L1-useless claim, alternating-impossibility, general NB-LDPC failure, FER/leakage/key-rate,
qualification, R1d/G1/G2 permission.

**Consequences**: `next_gate` → `D7_G_EXTRINSIC_CONTRACT_PROPOSAL`; D7-G specifies a code-factor
extrinsic-message contract next, feedback still out. All authorizations stay false; no push.
## 2026-09-13 D7 root-cause and route reset R1 - implementation authorized (no execution)

**Decision**: Open `formal-ir-d7-root-cause-and-route-reset` per packet `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`. Historical evidence retained byte-identical. D7-F terminal `D7_F_REVERSE_ORDER_REGRESSION` is a historical single-graph n=16 paired label (candidate-only 0 / reference-only 2 / both 0 / neither 14 at f=1.2; exact two-sided McNemar p=0.5), not an immutable general mechanism fact. G2 remains pending (`G2_PENDING_NOT_FAILED_NOT_SKIPPED_NOT_SUPERSEDED`), four-state preserved, runtime `G2_RUNTIME_UNVERIFIED`; P0's 485 s projection is not a reliable G2 estimate. Zero production decoder/CAL/VAL/G1/multi-graph/G2/D7-H execution.

**Context**: branch `formal-ir-v72p1-addendum-clean`; phases A-F only; X1-X4 and D7-H dormant pending exact command, fresh root, budget, stop rules, explicit authorization, Pre-EXECUTE review, and independent Pre-RESULT review.

**Consequences**: implementation candidate only; all execution/promotion authorizations remain false; lifecycle terminal `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`; no push.

## 2026-09-14 — D10 R1 readiness rejected pending connected full-rank construction

**Decision**: Accept the independent D10 readiness review as verified evidence,
but elevate finding F4 to a main-thread scientific blocker. Do not authorize
the frozen D10 R1 L1 batch. Its 18 profiled Tanner graphs have 9--68 connected
components, largest-component fractions 0.039--0.297, and several GF32 ranks
below `m`; therefore an arm comparison would not isolate variable-degree mix.

**Consequences**: retain R1 evidence and seeds; open D10 connectivity/rank R2 as
implementation/readiness work only. R2 must use one deterministic constructor
family for both arms, preserve exact degree tables and original graph seeds,
require one Tanner component, structural check-covering rank `m`, and GF32 row
rank `m` before any decoder binding, and stop without seed search if any cell
fails. All decoder execution remains unauthorized.

## 2026-09-14 — D10 R2 connectivity/full-rank readiness accepted

**Decision**: Accept R201--R212 and independent R211
`EVIDENCE_ACCESS: VERIFIED / PASS`. All original 18 cells now have one Tanner
component, structural rank `m`, GF32 rank `m`, deterministic replay, and zero
seed replacements. No ceremonial test duplication is required.

**Consequences**: terminal
`D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`;
issue one conditional n64→n128→n256 EXPLORE batch packet. This acceptance is
not execution authorization and does not revive D7-H.

### 2026-09-14: Accept D13 L055 decoder-ladder readiness (no execution)

**Decision**: Accept `D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION` after D1301-D1310 (D1310 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker). Grants no execution; predecessor D12 L055 selection stays immutable with 88 successes excluded and never pooled.

**Context**: 56 frozen L055 failures recomputed (n128 30 / n256 26, all iter90 converged_no_syndrome CHECK_UPDATED, undetected 0); replay/bindings/gates-ranking/terminals verified, binders accepted unchanged (no tuning, no new decoder); 16/16 tests rerun; PLAN_ONLY byte-deterministic with decoder 0; D12 root untouched; future root `workspace/d13_l055_decoder_ladder_5c41b416-…` absent. Records in `docs/research_cycles/V72P2D13-L055-LADDER/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d13-l055-decoder-ladder/`.

**Alternatives considered**:
- Authorize D13 batch now: rejected — readiness grants no execution; needs separate explicit grant.
- Tune decoder or broaden lambda/graphs now: rejected — frozen diagnostic reuses accepted binders only.

**Consequences**: Future batch (if granted) is EXPLORE (224 calls). Claim ceiling synthetic L1 decoder diagnostic only; no ensemble-optimality/forward/L2/FER/leakage/SKR/real-data/qualification/promotion/D7-H/commit/push.
### 2026-09-14: Accept D13 MODEST result; reset prior and rate validity before another decoder route

**Decision**: Accept the independently reviewed D13 Batch A1 result as
`D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`. RL360 alpha=1 rescued 3/56,
RL360 alpha=0.7 rescued 1/56, and flooding-360 rescued 0/56. Close the decoder
ladder without selecting an arm or authorizing a rerun.

**Validity correction**: The legacy D5 synthetic entrypoints still select
`prepare_model_f_prior`, despite the accepted
`LAMBDA_APPLICATION_CONTRACT_DEFECT`; X4 bridges directly to that G2 entrypoint.
Therefore `G2_CURRENT_CONFIGURATION_FAILED` remains an accurate description of
the executed legacy configuration but is superseded as evidence about n=256
finite-length feasibility. Preserve the original root and add a corrigendum;
do not rewrite history. The stronger claim that uniform prior is the only
possible cause of 0/120 is not accepted because other decoder/code failures can
also yield zero recovery.

**Next route**: `D14_SCIENTIFIC_VALIDITY_RESET_R1` — first preserve the
uncommitted D8–D13 milestone in scoped local commits, then switch P0/G1/G2
synthetic production selection to the already accepted concentration-backoff
candidate with an end-to-end selection test, and independently recompute L1/L2
generator entropy, nominal-vs-effective rate factors, and per-block information
load. No decoder batch or real-data run is authorized. D7-H remains closed
because its transfer mechanism is downstream of an unresolved channel/rate
 calibration and D13 showed no material decoder-dynamics rescue.
### 2026-09-14: Record D14 G2 prior-configuration corrigendum (docs only, no execution)

**Decision**: Record the additive G2/X4 inference-scope corrigendum
(`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`,
D14 VR-C) with append-only pointers in D5 `G1_WIDE_ATTRIBUTION_R2.md` §10, D7
`OPERATOR_RETURN_R1.md` §10, both `cycle_state.yaml` files, and the project memory.
Root `workspace/v72p2d5_g2/20260906_r1` stays preserved unchanged (4 files, 1320/1320
calls); literal grade `G2_CURRENT_CONFIGURATION_FAILED` is retained for the executed
rejected per-cell-prior configuration (`run_g2_synthetic` → `prepare_model_f_prior`);
that result is invalid as n=256 finite-length feasibility / route-closure evidence;
supersession covers the scientific inference only, not the recorded execution; no
unique-cause claim for all failures.

**Context**: D14 Scientific Validity Reset R1 Phase C (docs only, no decoder, no
execution, no commit/push).

**Alternatives considered**:
- Rewrite historical grades/records: rejected — frozen records stay byte-identical;
  correction is additive only.

**Consequences**: Future G2 citations must carry the rejected-configuration scope;
Phase P (prior-selection correction) and Phase R (no-decoder calibration audit) proceed
on the reviewed corrigendum basis.

### 2026-09-14: Accept D14 Scientific Validity Reset R1 complete (calibrated batch ready, unauthorized)

**Decision**: Accept D14 R1 S/P/C/R/N + final review (`EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker) with terminal `D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`. The frozen N calibrated discriminator batch remains unauthorized; no route decision, no D7-H, no FER/SKR/qualification/promotion claim.

**Context**: S: 4 local commits on `278fdf07` (`55ab6de`/`5f4b121`/`43308b8`/`ccc33eb`), 70 paths, 0 workspace/results/outputs, no push (origin `d98db0e`); group1 deferred, group5 STOPPED (mixed hunks, §3 compliance). P: 5 hunks (+7/-5) switching P0/G1/G2 to accepted `prepare_model_f_prior_candidate`/`build_f_model_concentration`, signatures/bodies untouched, D14P 4/4. C: additive G2/X4 corrigendum (VR-C-03 a–e), root `workspace/v72p2d5_g2/20260906_r1` untouched, grade literal retained with rejected-configuration scope. R: audit root `workspace/v72p2d14_rate_audit/20260914_r1/` (9 files); entropy joint 7.5094403148 / L1 4.2867204302 / L2 3.2227198846 reproduced (4dp, Δ≤1.8e-15); factor-triple mismatch (+0.003/+0.001/+0.003) retained, never copied; D12 24/432/221/0 + D11 120/720/0 undetected joins; 10/10 tests; single corrective rerun disclosed in log (inputs unchanged). N: prereg Choice A (entropy-derived m_L1=110, 550 disclosed, 1.00237; n128 only; 288 calls; seeds/root absent, runner absent). Records: `docs/research_cycles/D14_VALIDITY_RESET/` (inventory + prereg + log + readiness); OpenSpec `openspec/changes/v72p2d14-scientific-validity-reset/`.

**Alternatives considered**:
- Authorize N batch now: rejected — readiness grants no execution; needs separate explicit grant + DECIDE Pre-EXECUTE/Pre-RESULT.
- Rewrite history or stage group5 partial hunks: rejected — additive correction only; group5 stays STOPPED.
- Revive D7-H: rejected — downstream of unresolved calibration; N contributes one baseline pair only.

**Consequences**: Next gate is a separate explicit N batch grant only. Claim ceiling stays synthetic diagnostic; real-data/formal/route-closing/publication work remains DECIDE-gated.

### 2026-09-15: Clarify D14 N gate — implement runner before execution authorization

**Decision**: Accept D14-FINAL and its scientific preregistration, but correct
the next-gate wording: `scripts/v72p2d14_discriminator_development.py` is
explicitly absent, so the N batch is not operationally executable yet. The next
task is implementation/readiness `D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1`;
only after its independent review may the main thread issue the one-shot
288-call authorization.

**Process classification**: The bounded, synthetic, fresh-root N batch is
`EXPLORE` under AGENTS.md §1.2. Its stored machine terminal may route the next
investment descriptively, but the main-thread route decision remains separate
and does not turn implementation or execution into DECIDE. D7-H remains closed.

**Group5**: mixed decision-log/memory hunks do not invalidate the four existing
algorithm commits. Split them only by explicit content headers or exclude them;
never stage the mixed files wholesale. No push is authorized.

### 2026-09-14: Accept D14N calibrated L1/L2 discriminator readiness (no execution)

**Decision**: Accept `D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION` after N201-N210 (N210 `EVIDENCE_ACCESS: VERIFIED` / `PASS`, no blocker) + Freeze Amendment A1. Grants no execution; N batch unauthorized; no route decision; no D7-H.

**Context**: 18/18 admission with amended cells (L045 2^17+3^93 / L055 2^29+3^81 at m_L1=110), 22/22 tests, PROFILE 288-plan, refusal RC=2, decoder/scientific 0, future root `workspace/v72p2d14_discriminator/20260914_r1` absent. Pre-code STOP on m110/m118 contradiction (zero writes) → adjudication A → recompute → retry green. Records in `docs/research_cycles/D14_VALIDITY_RESET/D14N_READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/`; scoped commit `4b11d60` (9 paths), no push; group5 entries excluded uncommitted.

**Alternatives considered**:
- Authorize N batch now: rejected — readiness grants no execution; needs separate explicit grant + Pre-EXECUTE/Pre-RESULT.
- Adopt m=118 check strings: rejected — destroys Choice A calibration (1.0753 vs 1.00237).
- Stage group5 mixed hunks: rejected — split-by-header or exclude only.

**Consequences**: Next gate is separate explicit N batch authorization only. Claim ceiling stays synthetic n128 diagnostic; real-data/formal/route-closing/publication work remains DECIDE-gated.
### 2026-09-15: Block D14N execution authorization — authorized runner branch is unimplemented

**Decision**: Do not accept
`D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION` and do not
issue the 288-call A1 grant. In the persisted CLI, an authorized `--n14-batch`
falls through to an unconditional `SystemExit` stating that production adapters
belong to a later change. Thus the frozen command cannot execute the batch.

**Scope**: The amended m=110 arithmetic, 18/18 graph admission, 288-record plan,
gates, PROFILE_ONLY, refusal ordering, and zero-call evidence remain accepted.
Only operational execution readiness is blocked. N210 omitted a fake-injected
authorized-true-branch test, so its PASS does not cover this missing path.

**Next gate**: `D14N_AUTHORIZED_PATH_COMPLETION_R2`, implementation-only. Add
the smallest production binding/dispatch/writer path and prove it with fake
adapters and scratch roots; zero production decoder calls. Scientific inputs,
thresholds and budgets may not change. D7-H remains closed.
### 2026-09-14: Accept D14N R2 authorized-path completion close (path ready, no execution)

**Decision**: Accept `D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION` after R201-R207 (R207 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker). Execution path ready; real N batch still unauthorized; no route decision; no D7-H.

**Context**: R201 froze APP←L055 CHECK_UPDATED source + stale ≤26/m=118 correction. R202-R206 replaced authorized SystemExit with binder + orchestrator + writer. R207 proved no-SystemExit, fake 288/288, verifier 288/0, root absent, zero production, refusal RC=2, 14/14 adapters. Records in `docs/research_cycles/D14_VALIDITY_RESET/D14N_READINESS_R1.md` §7 + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/` §9 + R2 spec; scoped commit `3f874bb` (8 paths), no push; d5 + group5 hunks excluded uncommitted.

**Alternatives considered**:
- Authorize real N batch now: rejected — path readiness grants no execution; needs separate explicit grant + Pre-EXECUTE/Pre-RESULT.
- Stage d5/group5 mixed hunks: rejected — split-by-header or exclude only.

**Consequences**: Next gate is separate explicit N batch authorization only. Claim ceiling stays synthetic n128 diagnostic; real-data/formal/route-closing/publication work remains DECIDE-gated.
### 2026-09-15: Accept D14N R2 execution path; freeze one N-A1 EXPLORE batch

**Decision**: Accept `D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION`
as `D14N_R2_EXECUTION_PATH_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` after the
independent VERIFIED PASS_WITH_FINDINGS review. The authorized CLI path now
contains exactly one batch-orchestrator call and one never-overwrite writer;
the fake true branch completed 288/288 calls, setup 32, six files and verifier
PASS with zero production calls.

**Authorization boundary**: Acceptance grants no run. A separate user grant is
required for `D14N_CALIBRATED_DISCRIMINATOR_BATCH_A1`. Pre-dispatch must
reconfirm the uncommitted D5 P-wiring still selects the candidate prior at all
three synthetic entrypoints and that `APP_SOURCE_PROFILE == "L055"`.

**Scope**: One synthetic EXPLORE batch, n128 only, 288 calls, fresh root, no
retry/repair/seed search. Result routing is evidence for a later main-thread
decision; it does not self-revive D7-H or authorize real data.
### 2026-09-14: Accept D14N Batch A1 reviewed evidence-only result (calibrated discriminator)

**Decision**: Accept `D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` as the evidence-only close of the single authorized D14N Batch A1 run. Stored terminal `N_ROUTE_L1_CONSTRUCTION` stands; no route acceptance, retry, repair or rerun is granted.

**Context**: 288/288 calls, 32/32 setup, budgets PASS (wall 170.990/1800, per-call-max 0.928/120, RSS 137207808<2GiB); 18/18 admission (amended cells); exact 80 = syndrome 80, undetected 0 (L045 3 / L055 7 / APP joint 7 / ORACLE 63); APP←L055, 216 CHECK_UPDATED + 72 ORACLE ungraded; predicates L1-ADEQUATE FALSE / ORACLE TRUE / JOINT FALSE; Model-F unchanged. Batch-end review `EVIDENCE_ACCESS: VERIFIED` / PASS with no blocker. Full record in `docs/research_cycles/D14_VALIDITY_RESET/EXPLORATION_LOG.md`; root `workspace/v72p2d14_discriminator/20260914_r1` (6 files).

**Alternatives considered**:
- Route acceptance or promotion: rejected — N_ROUTE_L1_CONSTRUCTION terminal is evidence-only by frozen design.
- Retry/repair/rerun or second run: rejected — grant consumed, single-pass identities verified.

**Consequences**: Next gate is main-thread route decision only. Claim ceiling stays synthetic calibrated discriminator; no FER/leakage/SKR/forward/L2/real-data/qualification/D7-H claim; no commit/push authorized. Interpretation (not a claim): at calibrated effective≈1.0 disclosure, L055 L1 exact 42/72 (D12 CE-rate) → 7/72, so the D12 advantage was a rate artifact.
### 2026-09-15: Accept D14N evidence; defer L1-vs-L2 route pending matched-margin curve

**Decision**: Accept the D14N Batch A1 artifacts and independent VERIFIED PASS
as `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`. Retain the literal
stored terminal `N_ROUTE_L1_CONSTRUCTION`, but do not promote it to the
main-thread investment decision.

**Reason**: L1 L055 was tested at effective disclosure about 1.002, whereas L2
ORACLE retained about 1.261. The observed 7/72 versus 63/72 therefore combines
layer behavior with a large margin difference. At n=128, near-capacity failure
cannot distinguish inadequate L1 construction from ordinary finite-length
backoff. L055 still exceeded L045 7/72 versus 3/72, so the earlier statement
that the D12 advantage "was a rate artifact" is superseded: its absolute D12
success level was rate-dependent, but its relative advantage has not been
disproved.

**Next route**: D15 implementation/readiness for a paired, same-effective-margin
single-layer curve at three points. No new degree search, APP alternation,
D7-H, real data or route closure before that curve is reviewed.
### 2026-09-15: Accept D15 finite-length margin curve readiness (no execution)
- Decision: accept D15 readiness D1501-D1510, terminal `D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; batch unauthorized; no route decision; no D7-H.
- Context: 9-cell margin curve (L1 m110/114/118 + L2 m83/86/89), 36/36 admission, 25/25 tests, fake 288/288, refusal RC=2, decoder 0, D15-R1510 VERIFIED PASS_WITH_FINDINGS, commit 614a0e81 no push.
- Alternatives rejected: authorize batch now (needs separate explicit grant); rerun trusted reviewer evidence (trust rule forbids ceremonial duplication).
- Consequences: future D15 batch requires separate explicit authorization; invalid inferences (§2 rejections) remain barred; group5/d5 hunks stay excluded uncommitted.
- 2026-09-15 main-thread decision: accept D15 margin-curve readiness as
  `D15_MARGIN_CURVE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` after
  D15-R1510 VERIFIED PASS_WITH_FINDINGS, no blocker. The paired factor gaps are
  below 0.004 at all three points; 36/36 graphs admitted; fake 288/288 and
  verifier passed; production calls remain zero. Authorize nothing by this
  acceptance. Next gate is the separate one-shot D15 Batch A1 EXPLORE grant.
### 2026-09-15: Accept D15 Batch A1 reviewed evidence-only result (margin ambiguous)
- Decision: accept D15 Batch A1 close as `D15_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; stored terminal `MARGIN_CURVE_AMBIGUOUS` stands; no route acceptance, retry, repair or rerun is granted.
- Context: single authorized run, root `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2` (6 files, hashes match); EXIT 0; 288/288 calls, 46/46 setup, budgets PASS; 36/36 admission; exact 61 = syndrome 61, undetected 0 (L045 0/6/19; L055 1/13/22; L2-ORACLE 0/0/0); monotonic all arms; WEAKx7 + MIDDLEx2, ADEQUATE none; L2-ORACLE-zero evidence-only; batch-end review VERIFIED PASS_WITH_FINDINGS, no blocker; Model-F unchanged. Full record in `docs/research_cycles/V72P2D15-MARGIN-CURVE/EXPLORATION_LOG.md`.
- Alternatives rejected: route acceptance/promotion (ambiguous terminal is evidence-only by frozen design); retry/repair/rerun or second run (grant consumed, single-pass identities verified).
- Consequences: next gate is main-thread route decision only; claim ceiling stays synthetic matched-margin diagnostic; no FER/leakage/SKR/forward/real-data/qualification/promotion/D7-H claim; no commit/push authorized.
- 2026-09-15 main-thread decision: accept D15 Batch A1 reviewed evidence as
  `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR`. Retain
  `MARGIN_CURVE_AMBIGUOUS`; do not select L1 or L2 investment yet. L1 responds
  monotonically and reaches 19/32 (L045) / 22/32 (L055) at m118, while L2
  true-conditioned oracle remains 0/32 at m83/m86/m89. The minimum next test is
  one paired point: L1 m125 (625 bits, factor 1.1390555) and L2 m94 (470 bits,
  factor 1.1393714), gap 0.00031594. If L055 becomes adequate while L2 remains
  weak, route to L2 degree design; otherwise preserve the symmetric outcome.
  D7-H remains closed because oracle-layer failure precedes transfer design.
### 2026-09-15: Accept D16 matched-backoff discriminator readiness (no execution)
- Decision: accept D16 readiness D1601-D1609 + terminal-string alignment + scoped re-verify, terminal `D16_MATCHED_BACKOFF_READY_AWAITING_EXPLICIT_AUTHORIZATION`; batch unauthorized; no route decision; no D7-H.
- Context: predecessor D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR; one-point n128 factor ≈1.139 (gap 0.0003159373731645); 12/12 admission; seeds 4001-4012 + 4101-4108 frozen; 96/22 plan; no-APP; six terminals aligned to packet string D16_MATCHED_BACKOFF_SUFFICIENT; 26/26 tests; fake 96/96 + verifier; refusal RC=2; decoder 0; future root absent; R1608 VERIFIED PASS_WITH_FINDINGS + R1608A PASS; commit a0260907 no push. Refs: docs/research_cycles/V72P2D16-MATCHED-BACKOFF/READINESS_R1.md + EXPLORATION_LOG.md; OpenSpec openspec/changes/v72p2d16-matched-backoff-discriminator/.
- Alternatives rejected: authorize batch now (needs separate explicit grant); rerun trusted reviewer evidence (trust rule forbids ceremonial duplication).
- Consequences: future D16 batch requires separate explicit authorization; D15/d5/group5 excluded hunks stay uncommitted carried.
- 2026-09-15 main-thread decision: accept D16 matched-backoff readiness as
  `D16_MATCHED_BACKOFF_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  Evidence: exact factor gap 0.00031593737316448767; 12/12 admission; frozen
  96/22 plan; 26/26 tests; fake 96/96 + verifier; refusal rc2; R1608 VERIFIED
  PASS_WITH_FINDINGS and terminal-label R1608A PASS; production calls zero.
  This acceptance authorizes nothing. Next gate is one-shot D16 Batch A1.
### 2026-09-15: Replace direct D16 route gate with asymptotic-to-finite scaling

**Decision**: Withdraw the unconsumed D16 Batch A1 execution packet before any
run. Retain D16's m125/m94 point as a held-out validation point, but freeze its
predicted outcome interval before authorizing it. Route first to
`D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1`.

**Rationale**: The scientifically ordered pipeline is current empirical channel
→ ensemble DE threshold/degree profile → finite-length scaling/backoff for a
stated target error probability → finite graph/decoder validation. D10–D16 had
been using finite graphs to infer the backoff without an explicit model. D15
showed monotone margin response but could not distinguish construction from
finite-length proximity to threshold. Another unmodeled point would remain
post-hoc evidence.

**Scope correction**: V26 f=1.3 convergence remains valid ancestor evidence,
not a transferable threshold for the current Model-F candidate and all three
L1/L2 ensembles. D8/D9 cover current-channel L1 DE partially; current-channel
L2 DV3 asymptotic behavior is missing. D17 must close that gap and fit a modest
empirical finite-length model. Graph/trapping/rank effects remain residuals to
validate, not a universal analytic correction.

**D7-H**: remains closed. Alternating transfer is downstream of single-layer
threshold/backoff and cannot substitute for an L2 oracle code that has not yet
crossed its finite-length operating region.
### 2026-09-15: Accept D17 asymptotic-finite scaling readiness (no execution)
- Decision: accept D17 readiness A01-A05 + D01 + B/C/D02-D06 + D07, terminal `D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`; DE batch + fit + D16 prediction all unauthorized; no route decision; D7-H closed.
- Context: channel identity EXACT (candidate generator, H_L1/H_L2, floor/no-renorm, P1/P2 + true-U1 oracle); DE-transfer map (V26 kernel + D9 adapter reuse; f1.3 numerics do NOT transfer); finite table F1-F19/H1-3 with compatibility classes (APP/joint excluded; L2-ORACLE L2-model-only); D16 holdout locked (banned seeds 4001-4012/4101-4108, root absent, blank schema); frozen 15-pt DE grid (L045 m106-122 / L055 m116-126 capped / L2 m89-109, seeds 2026094201..08, 240 calls, V26 60/1e-4/20); probit law + ladder/downgrade/MODEL_NOT_IDENTIFIABLE + logistic-descriptive + epsilon 0.10/0.01 inversion; 30/30 tests; PROFILE_ONLY rc=0 + refusal rc=2; DE/decoder 0; future roots (DE + D16) absent; D07 VERIFIED PASS_WITH_FINDINGS (first-run fixes in-scope); scoped local commit 73c6275b (10 paths) no push; d5/group5 hunks EXCLUDED uncommitted (carried). Refs: docs/research_cycles/V72P2D17-DESCALING/READINESS_R1.md + EXPLORATION_LOG.md; OpenSpec openspec/changes/v72p2d17-asymptotic-finite-scaling/.
- Alternatives rejected: authorize DE batch/fit/D16 prediction now (needs separate explicit grant); rerun trusted D07 evidence (trust rule forbids ceremonial duplication).
- Consequences: future DE batch requires separate explicit authorization with frozen grid/seeds/budgets; D16 stays held out with prediction frozen first; claim ceiling synthetic DE + finite-fit diagnostic; no FER/SKR/qualification/promotion/real-data/D7-H claim.
### 2026-09-15: D17 DE Batch A1 engineering-blocked (0/240) — evidence retained, awaiting fix-or-standdown decision
- Decision: close single authorized D17 DE Batch A1 as `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION`; no fit/D16-prediction/D16/route authorized; no repair/rerun under consumed grant.
- Context: root `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718` (6 files, hashes match); EXIT 0 fail-closed; plan 240 validated, 0/240 calls, setup 4/12, budgets unbreached; `DE_CALL_FAILED@0 TypeError tuple-not-callable` (production bind passes D9 `load_l1_channel` tuple as sampler; `build_l1_sampler` never invoked; fakes never exercised production bind); D16 blank; Model-F unchanged; no decoder/CAL/VAL/real-data. Review `D17-DE-B1-REVIEW` VERIFIED PASS (STOP correct) with B1 unusable-evidence, B2 zero-call bind-validation gap, N1 L2-oracle dispatch gap, N2/N3 notes. Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Alternatives rejected: repair/rerun under same grant (grant consumed at command start, single-pass rule); batch-end review of DE evidence as complete (0/240 cannot meet packet §7 terminal).
- Consequences: next gate is main-thread decision only — authorize fix+rerun packet with explicit repair scope (incl. N1 L2 dispatch + B2 bind validation) or stand down Batch A1; claim ceiling stays synthetic DE diagnostic; no FER/SKR/qualification/promotion/real-data/D7-H claim; no commit/push.
### 2026-09-15: Accept D17 DE repair R2 (REPAIR_CLOSE) + Batch A2 reviewed evidence-only result (240/240 DE_COMPLETE)
- Decision: accept R2 repair close and single authorized fresh-rerun Batch A2 as `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`; no fit/D16-prediction/D16/route authorized; no rerun/repair under consumed A1+A2 grants.
- Context: R2 L1 tuple→sampler + L2 per-entry oracle dispatch, frozen 15-pt grid/seeds/pops/V26/budgets/banned-D16 unchanged (R204), 37/37 tests, `D17-R2-REPAIR` VERIFIED REPAIR_CLOSE, zero scientific calls in repair. A2 root `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24` (6 files, hashes match); EXIT 0; 240/240 calls, setup 4/12, budgets PASS; A2 plan byte-identical to A1; S_pop 139/240; clean DE_BRACKET all three profiles (delta_DE L045 0.24452956979862517 / L055 0.30312331979862517 / L2 0.5468113653656221); A1 immutable; D16 blank; Model-F unchanged. Review `D17-A2-REVIEW` VERIFIED PASS_WITH_FINDINGS, no blocker (N1/N2 non-blocking). Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Alternatives rejected: fit/scaling prediction or D16 authorization now (needs separate explicit grant with frozen intervals first); second run/retry/repair under A2 grant (single-pass rule); route acceptance/promotion (evidence-only by frozen design).
- Consequences: next gate is scaling-fit decision under separate authorization only; claim ceiling stays synthetic DE diagnostic; no FER/leakage/SKR/forward/real-data/qualification/promotion/D7-H claim; no commit/push.
### 2026-09-15: Accept D17 scaling-fit A3 reviewed result (predictions frozen, D16 unauthorized)
- Decision: accept single authorized scaling-fit A3 as `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`; 3 D16 outcome-BLANK predictions frozen; no D16/fit-claim/route authorized; no rerun under consumed A3 grant.
- Context: root `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95` (8 files, hashes match); EXIT 0; wall 255.08/300, RSS ~0.097GiB, violations []; DE/decoder/CAL/VAL 0; 96 clusters (48/30/18); L045 one-param α=14.5378 [10.0,21.752] / L055 two-param α=4.5973 [3.1623,5.6234] β=-1.075 [-1.5,-0.575] / L2 one-param α=5.0845 [3.4974,6.8786]; backoffs diagnostic; predictions L045 p0.8516 [0.6157,0.9744] / L055 p0.9616 [0.8899,0.9955] / L2 p0.3121 [0.0,0.5] all BLANK; D16 absent; verifier 96/0 PASS. Review `D17-A3-REVIEW` VERIFIED PASS_WITH_FINDINGS, no blocker (N1/N2/N3 non-blocking). Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Alternatives rejected: D16 authorization or fit-claim/route acceptance now (needs separate explicit grant); second completion/retry/tuning under A3 grant (single-pass rule); rerun trusted reviewer evidence (trust rule).
- Consequences: next gate is D16 authorization (separate) only; claim ceiling stays synthetic scaling-fit diagnostic; no D16/decoder/route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim; no commit/push.
### 2026-09-15: Accept D16 held-out scaling validation B1 reviewed result (partial falsification, evidence-only)
- Decision: accept single authorized D16 B1 run as `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`; frozen-band verdicts L045 NOT_FALSIFIED / L055 FALSIFIED (below 0.8899) / L2 NOT_FALSIFIED stand as evidence only; no route acceptance, retry, refit or rerun is granted.
- Context: 96-call run EXIT 0; exact 61 = syndrome 61, undetected 0 (L045 25/32 [7,6,7,5]; L055 27/32 [7,7,6,7]; L2-ORACLE 9/32 [3,1,2,3]); predictions predated run ~33min, byte-identical + all-BLANK; legacy `D16_L2_DEGREE_SIGNAL` secondary only. Review `D16-B1-REVIEW` VERIFIED PASS, no blocker. Full record in `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md` (+ pointer in D17 log).
- Alternatives rejected: route acceptance/promotion or interpretation of partial falsification (evidence-only by frozen design); retry/refit/rerun or D17-model-change (grant consumed, single-pass rule); D7-H/real-data/claim extension (out of scope).
- Consequences: next gate is main-thread route decision only; claim ceiling stays synthetic held-out diagnostic; no FER/leakage/SKR/qualification/promotion/real-data/D7-H claim; no commit/push.

## 2026-09-15 — Route from D16 held-out validation to L2 ensemble DE

- Accepted `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`:
  L045 25/32 and L2-ORACLE 9/32 were inside their frozen D17 bands; L055 27/32
  was below its frozen latent-p band and remains registered `FALSIFIED`.
- The L055 miss is not relabelled, but it is not evidence of L1 construction
  failure: recovery was high and consistent across four graphs. At the matched
  point L2 remains materially weaker and its DV3 ensemble has never received
  the current-channel degree search already performed for L1.
- Route decision: pause L1 tuning; run a bounded current-channel L2
  true-conditioned ensemble DE search (D18), then finite-graph validation of
  any selected ensemble. Do not revive D7-H or APP before single-layer L2 is
  inside its operating region.
- Forward methodology: future held-outs must distinguish uncertainty in latent
  `p_success` from predictive uncertainty of an observed binomial count. This
  does not retroactively alter D16's preregistered verdict.
### 2026-09-15: Accept D18 L2 ensemble DE readiness (no execution; sweep unauthorized)
- Decision: accept D18 readiness E01-E08 as `D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; route pause-L1/optimize-L2 ensemble stands, followed by finite L2 validation of any selected ensemble only. Sweep unauthorized; no route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim; no commit/push.
- Context: 21 candidates (DV3 control mandatory) + feasibility 105/105 + DV3 baseline 0.5468113653656221; Stage-S 168 (21x{94,104}x4301..04x4000) + Stage-C 320 (32-overlap, 288 new, 456 total); eligibility <=0.5077488653656221 + rank + one winner; terminals incl. BASELINE_DRIFT; seeds 4301..4308 frozen; future root `workspace/d18_l2_ensemble_de_98abed5a-...` absent; budgets <=456/<=16/1800s/300s/2GiB/1-proc; 26/26 tests; PROFILE_ONLY + refusal rc=2; DE/decoder 0; E08 VERIFIED PASS_WITH_FINDINGS (D17 3 fails environmental). L055 FALSIFIED preserved (mild miss 27/32 [7,7,6,7]); methodology amendment latent-band vs predictive-interval forward-only with descriptive tails T(p_lo)=0.273/T(p_hi)=3.3e-07, D16 NOT recomputed. Refs: `docs/research_cycles/V72P2D18-L2ENSEMBLE/` (parallel creation); OpenSpec `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`.
- Alternatives rejected: authorize sweep now (needs separate explicit grant); resume L1 tuning or revive D7-H/APP before L2 operating region (route adjudication); recompute/relabel D16 verdict under new interval (preregistration immutable); FER/route/real-data claim on readiness alone.
- Consequences: next gate is one-shot D18 sweep authorization only; claim ceiling stays synthetic DE readiness; E09 scope records no commit (commit explicitly NOT permitted this session).
### 2026-09-15: Accept D18 L2 ensemble DE Sweep A1 reviewed evidence-only result (winner lam_d2_0.20_d3_0.80; route decision pending)
- Decision: accept the single authorized one-shot Sweep A1 as `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; machine terminal `D18_L2_DE_SELECT_ONE_ENSEMBLE`; evidence-only — no route/optimality/finite-L2 acceptance; one-shot grant consumed; no rerun/repair/manual substitution.
- Context: root `workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901` (6 files, sha256 match); EXIT 0, 15:50:36–15:58:27Z; 456/456 unique calls (S 168 + C-new 288; 32 overlaps reused, never rerun), setup 4/16, wall 466.36/1800, per-call-max 2.815/300, RSS 286371840<2GiB, violations []; Stage-S selected `[0.15, 0.20, 0.25, DV3]` by the frozen rank (six-way tie at S94=S104=4 + worst-H 3.089393128245247e-296 resolved by pre-registered id ASC); selected brackets lo89/hi94 `delta_DE=0.35149886536562214` <= `0.5077488653656221`; DV3 lo94/hi99 `delta_DE=0.5468113653656221` reproduced, `baseline_drift=false`; 3 eligible; winner `lam_d2_0.20_d3_0.80` (id ASC; 0.15 has max_dc 5); read-only verifier PASS/0. Review `D18-A1-REVIEW` VERIFIED PASS_WITH_FINDINGS, no blocker (N1 RSS placeholder + setup constant, N2 saturation, N3 thin command_log, N4 rank-4..6 screen-indistinguishable). Refs: `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`.
- Alternatives rejected: second/adaptive stage, manual candidate substitution, rerun or repair under the consumed grant (single-pass rule); promoting the winner to route/finite-L2 acceptance or an optimality claim now (evidence-only; N4 screen tie); reviving L1 tuning/D7-H/APP before the L2 operating region (D16 route adjudication).
- Consequences: next gate is the main-thread route decision only (registered follow-on per D16 adjudication: finite L2 validation if a candidate advances); claim ceiling stays synthetic current-channel L2 ensemble DE diagnostic; no finite L2/decoder/APP/L1/real-data/FER/leakage/SKR/qualification/promotion/D7-H claim; no commit/push.

## 2026-09-16 — Advance D18 L2 winner to paired finite validation

- Accepted D18 reviewed result: L020, L025 and L015 shared
  `delta_DE=0.35149886536562214`; the frozen max-check-degree then ID rule
  selected `lam_d2_0.20_d3_0.80`. DV3 reproduced its D17 threshold exactly.
- Decision: validate only L020 versus DV3 at the discriminating m/n=94/128
  point, first at n128 and conditionally at n256, using fresh paired blocks and
  six graphs per width. Near-tie candidates are not reopened.
- This advances a candidate for synthetic finite L2 testing only; it makes no
  optimality, FER, real-data, APP, or route-closure claim.
### 2026-09-16: D19 L2 finite-ensemble validation readiness STOP (frozen-seed x constructor-trajectory BLOCKED, no ready terminal)
- Decision: record genuine STOP with NO ready terminal; `D19_L2_FINITE_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION` must NOT be issued under frozen seeds. ONE pending main-thread decision: amend frozen n256 DV3 seed set under a new packet amendment (fresh disjointness + 24-graph re-profile + re-review) OR formally accept `D19_L2_FINITE_ENGINEERING_BLOCKED` as the D19 outcome. No commit/push; no D19 execution.
- Context: frozen n256 DV3 graph seed 2026094408 deterministically fails construction (`no eligible check placement at variable 255 socket 2`) with accepted D10-R2 constructor; 23/24 admit (n128 12/12); reviewer `D19-BLOCKER-REVIEW` VERIFIED PASS confirmed frozen-seed x constructor-trajectory STOP (not table/implementation defect; arithmetic + sockets verified; five identical-multiset siblings admit); no replacement/search applied (forbidden); D19 module/runner/tests 33/33 + PROFILE_ONLY 24 attempted/23 admitted/192 plan/0 calls/root absent + refusal rc2 as untracked-additive artifacts; F08 root `workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b` absent; zero decoder/DE calls. Refs: `docs/research_cycles/V72P2D19-L2FINITE/` (parallel creation); `openspec/changes/v72p2d19-l2-finite-ensemble-validation/`; packet `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`.
- Alternatives rejected: issue ready terminal under frozen seeds (frozen-seed violation); replace/search seed within current packet (forbidden without amendment); D19 execution on 23/24 partial set (breaks frozen paired design).
- Consequences: claim ceiling stays synthetic finite L2 readiness; no FER/leakage/SKR/route/qualification/promotion/real-data/D7-H claim; next gate is main-thread amend-vs-accept decision only.
### 2026-09-18: D19 finite-ensemble execution terminal AMBIGUOUS (supersedes BLOCKED-as-terminal suggestion)
- Decision: record D19 finite-ensemble execution terminal AMBIGUOUS (n128 M=19/48 exact-only; n256 unentered), explicitly superseding the prior BLOCKED-as-terminal suggestion; batch-end PASS; grant closed with no rerun permitted.
- Context: terminal `D19_L2_FINITE_AMBIGUOUS`; n128 96/96 calls exact-only M=19/48 AMBIGUOUS with undetected=0 isolated; n256 0 calls (conditional n256-iff-POSITIVE closed); CAL Model-F input only; batch-end reviewer-go PASS B1-B7. Evidence root `workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b` + log `docs/research_cycles/V72P2D19-L2FINITE/EXPLORATION_LOG.md`.
- Alternatives rejected: retain BLOCKED as D19 terminal (superseded by executed AMBIGUOUS outcome); rerun/repair under closed grant.
- Consequences: no FER/leakage/SKR/promotion/route-closure claim; next gate is main-thread route decision only.
### 2026-09-18: G6 first real-data DECIDE terminal NO_USEFUL_RECOVERY
- Decision: record G6 first real-data DECIDE terminal NO_USEFUL_RECOVERY (L020-n128, 2M-tail 128 blocks, 0 accepted, undetected 0, reconciled_net 0, beta negative derived-only).
- Context: single authorized invocation under PREREG_AND_AUTH (F-pop/F-op/F-dec/F-gate/F-bud frozen); reviewer-go Pre-RESULT PASS; main-thread ACCEPTED. Full record in `docs/research_cycles/V72P3G6-REAL-CONFIRM/`.
- Alternatives rejected: any SKR/qualification/promotion/generalization claim; retry/repair/rerun under consumed grant.
- Consequences: no SKR/qualification/promotion; single invocation, grant consumed; route signal: existence unproven on disjoint session → next decision is rate-adaptation-vs-family-change, new packet required.
### 2026-09-18: D-R7-01 ADOPT-m100: R8 located 92|96 transition (88/92 FAIL 0/0 structural, 96 PASS 8/8); m100 = 8-row cushion above real-failed m94, m96 parked as edge.
### 2026-09-18: FIRST_REAL_RECOVERY_CONDITIONAL m100/P-1p5M 128→1 accepted undetected-0 net-140; existence-only (overrides reviewer no-entry suggestion: FIRST real-data recovery in project history is a milestone, not routine); next R10 same-session control to split prior-match vs code-at-edge.
### 2026-09-18: R9 SOLIDIFIED as FIRST_REAL_RECOVERY_CONDITIONAL (existence-only, 128→1/1/0 net-140; V72P3R9-CONFIRM/RESULT+INDEPENDENT_ACCEPTANCE).
### 2026-09-18: R10 FROZEN (window 1983..2046 after V55-hit at 1982, contrast ≥5 vs ≤2, run NOT granted); RULING-2 waiver precedent extended to R9b-D5 (absence-tests invalidated by authorized executions, roots retained).
### 2026-09-18: R10 CTRL SOLIDIFIED 1/128 in-session == R9 1/128 cross-session → prior-match CLOSED (caveat PPLN-vs-Type2 setup confound); ROUTE to rate-adaptive/new-family track.
### 2026-09-18: R11 ADAPTIVE_LIFT diagnostic 87-vs-1 (lift 86, undetected 0, net NEGATIVE -78392, S0=0 new-mother effect); gate to fresh-pool confirmation (T6) earned; no promotion claim.
### 2026-09-18: R13 PIVOT (0/90 near-miss, residuals structural 21+, cap-peg⇔fail, S1-worsens-65/90); S3 rejected by frozen rule; route → R14 regime survey for positive-net operating regime.
### 2026-09-18: G7 ROUTE verdict STOP-positive-net on surveyed regimes (m/n<0.5 vs ≳0.63 contradiction, Â-free); adaptive parked characterized (79-87/128, net-negative); escapes quantified (2.5× quieter regime OR 2×-better code); SKR work blocked until net-positive.
### 2026-09-18: R16 net-convention correction (n-based net_secret_bits added, old frozen; recomputed nets R9 −71552 / R11 −27752 / R12 −33232); G7-STOP central bound WITHDRAWN (k double-charge), route ALIVE as efficiency battle; terminals unchanged.
### 2026-09-18: G8-S0 done (H_A 4.2867/3.2227 incl D17-6dp pipeline proof; H_B worst 3.6925; H_C worst 3.6869); SANITY_STOP overridden (caliber cause); 1.023/1.875 gate SUPERSEDED (k-based, n-based bar H<3.0); HELD pending R18 V25/V19 anchor comparability; S1 not authorized.
### 2026-09-18: R18 V-INCOMPATIBLE-CONDITIONING accepted (units OK; V25 0.81 needs per-source ±1-concentrated data + richer conditioning, untransferable; F1-marginal capped 3.69 measured); S1-marginal REJECTED; route F3-conditional/F2-control via R19.
### 2026-09-18: R20 PRIOR-HELPS (uniform 0/128 resid-97.0 vs modelF 1/128; paired mean Δ+10.64, modelF-better 123/128; P9 sign-typo corrected: improved≡Δ>0; prior line REOPENED → S1 shift-prior test justified; R17c NO-GAIN recorded alongside (warm harmful, subset result)).
### 2026-09-18: R17 NO-GAIN (warm 27 vs cold 87; strict subset 0/60/0; warm-start family DEAD as mechanism — carried beliefs trap decoder; S2→exhausted 52).
### 2026-09-18: R21 NO-DAMP-GAIN both arms (0.5/0.8 trajectories outcome-identical to S1 1.0; only accept-iters + 1-2 residual wiggles differ; decoder-hyperparameter line CLOSED: iters-300 dead, warm harmful, damping inert).
### 2026-09-18: S1 SHIFT-HELPS (shift 2/128, paired mean Δ-15.0, 127/128 improved; eps frozen 1e-4 via CV table; prior line PRODUCTIVE — uniform 0 → modelF 1 → shift 2).
### 2026-09-18: R22 PREDICTOR-DEAD (best lost-free rule saves 480-800 bits vs 1500 bar; residuals fully overlapped; abort line closed pending new signals).
### 2026-09-19: R23 INCONCLUSIVE-BY-CEILING (6×16/16 double saturation, iters-0 everywhere; literal DEAD would assert unsupported non-scaling; stage-2 charter BLOCKED; weak-prior re-test required; oracle-vs-real chasm downgraded to suggestive (confounded)).
### 2026-09-19: R23b DEAD-floor (0.65 weak 0/16+0/16, below-both-edges; verifier arm-predicate bug fixed (b) + re-verify 0 violations, no rerun; 0.72-extension separately authorized).
### 2026-09-19: R23b-0.72 DEAD-floor (0/16+0/16 weak, below-both-edges; SCOPE BREACH 64/8 vs granted 32/4 (UNION-plan missed check, self-reported STOP); r72 half admitted, r65 repeat annotated zero-info; envelope AMENDED 96/12 consumed-closed; runner hard-gated until delta-only+argv-log+re-review).
### 2026-09-19: R24 NO-FLOOD-GAIN (flooding 2/128 @34/106 identical to S1-layered; outcome-identity 128/128 with iters/residual micro-divergence; decoder-mechanism line FULLY CLOSED: iters dead, warm harmful, damping inert, schedule inert).
### 2026-09-19: G8 brief-gate APPLIED (S0 H_B worst 3.6925 > 1.875 → falsification branch per brief §6: seals STAND, route ③ Cascade-FIRST, ① NOT done); gate arithmetic SUPERSEDED note (1.023/1.875 k-based withdrawn like G7-STOP; n-based bar H<3.0 also fails at 3.69 — conclusion survives under either gate); v49 tables = V25-line evidence already covered by R18 (NOT new numbers; no superseding H_B/DE-edge produced).
### 2026-09-19: G8-§8 ACCEPTED (falsification accepted: H_B 3.6925 kills 3.5-bit-recoverable claim; Cascade-on-U2 VOIDED (interactive compresses f only: H=3.69 → net ≈−88 ideal/−112…−135, Â≈0.7 assumed); (J) joint h(U1|B,U2)<1.3 / (S) ≥3 planes h_i<0.55 teed as zero-cost table reads; R25b HELD (not as frozen); both-fail → INFORMATION-CLOSURE escalates to acquisition level).
### 2026-09-19: (J)/(S) MEASURED → both DEAD: raw joint 5.0771 (=3.6978+1.3793, chain 8.9e-16) > bar 5.0 (f=1.1) with memorization-bias upward-only (holdout blocked: 47% mass rule-less, no A/B/C fill-in — inf/cherry-pick/pessimism all rejected); planes NATURAL 0.857-0.891 (dir-agree ≤0.003), 0/10 <0.55; Gray absent flagged as residual caveat; INFORMATION-CLOSURE per brief §8 (acquisition-level decision; 1/2/3 no more rounds; R25b stays HELD-voided).
### 2026-09-19: V80-S0 ACCEPTED (GO): per-source H_full ≤1.0 verified zero-diffs (max 0.86246 2M-VAL); design frozen n=256/m-grid 24–31/f=1.3/tag64/q-TBD; ban carried; V70R1 out-of-scope; independent review PASS; main-thread ACCEPTED S0→S1 GO.
### 2026-09-19: V80 q-prior (Mitra arXiv:2305.00956 full-text via ar5iv): NB-MLC key-rate peaks at small a=3-4 (neither a=1 nor a=q); JRDO objective (1-E)R embraces FER~5% as optimum; V26 F03-GF32+GF32@f=1.3-30/30 narrow pass is isomorphic; PRIMARY GF(32)^2-layered, SECONDARY direct-q1024, TERTIARY a=3-4 refinements deferred; dv_max discrepancy flagged (Mitra VN 2-5 vs program dv_max<=40) for S1-freeze; IEEE-11440984 still paywalled (S2S 429), downgraded to nice-to-have (Kasai in-repo + R11 staged success cover rate-adaptivity).
### 2026-09-19: V80-S1 seeds 4501/4502 REJECTED (exact collision with D19 block range, operator scan gap); re-pick + quoted-proof required before Pre-EXECUTE; S2S IEEE-11440984 retry 429 again — paywalled retrieval DEFERRED indefinitely (nice-to-have stands on Kasai in-repo + R11 staged success).
### 2026-09-19: S1-delta review FAIL (blocks execution): D5 REAL bug — SECONDARY q=1024 bound to (n,32) L1 sampler (shape-contract violation + wrong objective; 20/20 green because fakes never assert shape); rework = full-symbol (n,1024) joint sampler + (n,q) pre-call assert + hash disposition + flip/verifier/terminal regression tests; D4 test gap noted. Caught pre-execution by independent review.

### 2026-09-19: V80 S1 HOLD on F1/F2 blocking (no S2 advance)

**Decision**: HOLD — 禁止解释当前S1臂输出、禁止flip/S2/S3，直到F1/F2/F3修复+D5-delta独立复审+新授权重跑.

**Context**: 独立复审发现F1 PRIMARY 0/420 (L2上限0.83862, 正确m2≈54) + F2门不筛converged (伪pass 0.7506<1违SW界, SECONDARY max1.454注定fail) + 记录链缺口止于4438.

**Alternatives considered**:
- 把PRIMARY pass当结论进S2: rejected — 伪通过.
- 就地改runner热修续跑: rejected — 需D5-delta复审+新授权+新root, PRIMARY 420不可回收.

**Consequences**: HOLD持续; 下一步planner fix plan已落盘S1_FIX_PLAN_20260919.md (F1-ACC/F2-ACC/F3-ACC/G-D5R/G-RERUN); 执行会话需对账+保留现场不删根; 本条目不授权执行.

### 2026-09-20: V80 S1 rerun stopped and batch closed (user-authorized)

**Decision**: Halt the S1 rerun and close the batch (option: 立即停 + 关批), per user authorization.

**Context**: SECONDARY m24 0/24 combined (screen 0/14 + confirm 0/10); remaining 61 confirm slots ≈5 h near-zero value; halt executed with quiescence verified 6×60s empty; raw gate, uninterpretted: PRIMARY f_ens=1.1375228736333134 n=32 pass=true sw=0, SECONDARY null/0/false, flip withheld.

**Alternatives considered**:
- Finish the grid: rejected — cost/value (≈5 h for near-zero-value slots).
- Silent resume-later: rejected — requires a new grant.

**Consequences**: Batch closed pending batch-end review; PRIMARY raw gate noted without interpretation; claim ceiling pending; no S2/S3 authorization; pre-S2 items: P1 status-label defect (rows hardcode status="ok", 0/539 overrun labels; [2026-09-20 wording: 超时返回后停机 — run_once checks dt AFTER the call returns (~runner.py:646) then halts subsequent calls, NOT hard preemptive; old-root 9 rows >300 s stay 0-overrun-labelled, fix is prospective only]) + P1 fix deferred, P3 reproducibility concern.

### 2026-09-20: V80 f-accounting convention frozen (whole-frame with tag + superframe n=1024)

**Decision**: Freeze the f-accounting convention: whole-frame f WITH tag + superframe n=1024 (user-approved).

**Context**: Audit P4 found three coexisting f conventions (layer-local, whole-frame tagless, whole-frame with tag); n=256 with-tag can never reach f≤1.3 (tag alone ≈0.30).

**Alternatives considered**:
- Leave the convention unfrozen: rejected — S2/S3 targets unjudgeable.
- n=256 single-frame with-tag target: rejected — unreachable per P4.

**Consequences**: PROGRAM_PLAN §1.1-1.3 arithmetic updated; S2/S3 targets rebound to the frozen convention; PA-aware Tauz deferred as S3 alternative; this entry authorizes nothing.

### 2026-09-20: V80 S1 batch closed; BER-1 fixed and BER-2 cleared by G-REPRO (pending re-review)

**Decision**: Close the V80 S1 batch (rerun halt accepted 2026-09-20); record BER-1 status-label fix and G-REPRO BER-2 clearance as pre-S2 gates pending independent re-review verdict. No S2 entry authorized.

**Context**: Batch-end review PASS_WITH_FINDINGS closed the batch (final ledger PRIMARY 420 / SECONDARY 119 / SETUP 12 / TOTAL 539; SECONDARY m24 0/24; 61 confirm slots abandoned); BER-1 fixed (honest `_row` status, `_validate_partial` completed==n_ok+n_overrun, suite 54+6, hash unchanged; [2026-09-20 wording: 超时返回后停机, NOT hard preemptive; old rows NOT retroactively relabelled; resuming the old root (same hash) does NOT substitute for a new grant + historical-label handling]); G-REPRO PASS (m2=47 10/10 converged, f_layer 1.1373-1.1379, f_super 1.22457); f-convention frozen (whole-frame with tag + superframe n=1024).

**Alternatives considered**:
- Authorize S2 entry on G-REPRO PASS alone: rejected — BER-1 re-verify and independent re-review verdict still outstanding.
- Map the S2 gate to layer-unit f=1.1375 without tag accounting: rejected — S2 prereg must map the layer-unit gate basis (m2=47, f=1.1375) to the frozen whole-frame+tag superframe accounting.

**Consequences**: S1 batch closed; S2 prereg must carry the layer-to-whole-frame+tag mapping; IEEE 11440984 full text still needed [gap]; this entry authorizes no execution.

### 2026-09-20: V80 review corrections applied; S2 entry packet frozen (NOT granted)

**Decision**: Applied the 5 review wording corrections; froze S2_ENTRY_PACKET G-S2ENTRY + prompt; independent review PASS with no blocking issues.

**Context**: S1 accepted as diagnostic-batch close only (G-REPRO m47 10/10, dual-seed 5/5, range 0.00056; SECONDARY m24 0/24); closes the "(pending re-review)" qualifier on the 2026-09-20 batch-closed entry.

**Alternatives considered**:
- Entering S2 now: rejected — needs fresh grant + Pre-EXECUTE + §4 evidence.
- Treating headroom/FER math as success evidence: rejected — budget-accommodating only.

**Consequences**: S2 gated, not authorized; S1 claim ceiling stays synthetic DE-ensemble only; no FER/SKR/qualification/promotion; no push.

### 2026-09-20: IEEE 11440984 full text retrieved (user-supplied PDF)

**Decision**: Close the acquisition gap.

**Context**: 8-function SciVerse exhaustion then user PDF (sha256 579bd831…); key numbers captured (GF(2) 1.8577 → GF(128) 1.0661 @ R=0.5/n=20000/FFT-BP-200/FER≈75% snapshot; shortening+puncturing not blind; PEG H; λ/ρ not stated).

**Alternatives considered**:
- Keep gap open: rejected — user supplied.

**Consequences**: LITERATURE_QPRIOR updated, PROGRAM_PLAN §2.2 synced; existence-evidence only, not S2 design input; PDF not committed.

### 2026-09-20: Zotero library scan attempted — offline (retry needs desktop)

**Decision**: Record the offline probe; no new references obtained.

**Context**: Probe RC=7 both endpoints (Zotero desktop/API unreachable).

**Alternatives considered**:
- Treat as no-library-evidence: rejected — probe failure is environmental, not a collection result.

**Consequences**: Single retry step recorded (Zotero desktop open + local API allowed); ZOTERO_SCAN_20260920.md holds details; no new references obtained.

---

### 2026-09-20: S2 V1 FER campaign FAIL-early-stop; V2 triggered per frozen packet

**Decision**: Record V1 FAIL-early-stop as raw machine verdict (4/4 groups failed; 16 decodes; 0 successes; wall 186 s; f_super 1.2246 pass, FER gate fail); trigger V2 single shot per packet §3 (no re-seed, no threshold change, no arm hopping).

**Context**: Diagnostic PLUMBING-SANE (p=0 ladder: p=0 iter1 exact, p=0.005 iter2 exact, p=0.02 miscorrection, p=0.05 fails incl. zero-codeword control) → leading non-conclusive explanation = finite-length weakness of frozen λ={2:1} (regular dv=2; low-weight codewords); decoder budget secondary (most frames lock wrong early, not at cap). No conclusion beyond this; V2 pending.

**Alternatives considered**:
- Skip V2 straight to fallback review: rejected — packet freezes V2 single shot on V1 FAIL.
- Rerun/re-seed V1: rejected — frozen no-retry rule.

**Consequences**: V2 (construct seed 2026096101/trials 100, four_cycles<1158 else fails closed; frame seeds 2026096301+idx) running now; V2 FAIL ⇒ no S3 + fallback review; S2/S3 remain unauthorized beyond frozen arms; no FER/qualification claim beyond machine verdict.
---

### 2026-09-20: S2 constructor implementation defects found (user read-only review) — attribution paused, rework ordered

**Decision**: Preserve V1/V2 raw failures; pause causal attribution and S3; order = fix v10 PEG edge selection/girth/trials → deterministic tests → independent re-review → re-frozen experiment (λ unchanged; channel/prior explicitly matched).

**Context**: Two concrete implementation defects (edge selection; trials semantics) + interpretation scope corrections (PLUMBING-SANE too broad; proxy H=0.534 vs target 0.8069 ⇒ f_super=1.2246 is budget mapping, not measured efficiency; 1158→1140 confounded by seed change). Full record in `docs/research_cycles/V80-NBLDPC-JAN21/S2_CONSTRUCTOR_DEFECT_REVIEW_20260920.md`.

**Alternatives considered**:
- Continue λ/variant exploration on unfixed constructor: rejected — implementation defects would masquerade as algorithm failure.
- Retroactively declare dv=2 failure: rejected — not established.

**Consequences**: Constructor fix task running; campaign executor pins will change (new actual four_cycles); S2b experiment needs re-frozen packet + review; no S3; no FER/qualification claim.

### 2026-09-20: S2b FAIL-early-stop (fixed constructor, entropy-matched channel) — raw retained; triage opened, attribution paused

**Decision**: Record raw machine verdict FAIL (4/4 groups; 16/16 frames converged_no_syndrome at iterations 5–17; wall 12.7 s; gate(a) FER fail, gate(b) f_super 1.2246 pass); open observation-level triage per user mandate: stopping-rule study (no-early-stop / loosened streak) and p-ladder with differential codeword weight; dv-distribution feasibility check separately; NO causal attribution yet.

**Context**: Constructor fix verified (four_cycles=0/min_girth=6/rank=47); channel+prior entropy-matched QSC p*=0.081; S2b single arm; failure mode is a fast wrong-lock (converged_no_syndrome), distinct from max-iter exhaustion; earlier review corrections still in force (hard-decision streak ≠ soft convergence; weight unmeasured until now). Full record in `docs/research_cycles/V80-NBLDPC-JAN21/S2B_RESULT_20260920.md`.

**Alternatives considered**:
- Declare dv=2 as cause: rejected — attribution paused per user review.
- Extend/rerun campaign: rejected — early-stop terminal, no rerun rule.

**Consequences**: Triage studies running; V1/V2/S2b raw failures retained; no S3; no qualification/FER claim beyond machine verdicts.

### 2026-09-20/21: S2c three-arm empirical-channel campaign FAIL-early-stop (0/3 arms); batch-end review PASS; fallback options memo issued

**Decision**: Record raw machine verdicts (L-A frame FER 7/16, L-B 13/16, L-C 16/16; group 4/4 each; f_super 1.2246 budget-pass; no continuations, budgets interior); close the S2c batch with the independent batch-end review (PASS; claim ceiling = "0/3 arms meet the group FER bar under finite-length n=256/m₂=47/genie-u1/empirical-channel"; no S3 authorization); route decision deferred to user with the fallback options memo (ranked O4→O2→O1; O3 piggyback; O5 parallel S3-level; O6 last).

**Context**: Decisive empirical-channel test after constructor fixes (wiring defect caught and fixed pre-launch, zero execution wasted); stopping-rule and dv evaluations previously closed; failure mode = finite-length gap at n=256 (per-frame success nowhere near the 98.7% group-rule requirement), genie-u1 upper bound. Full records in `docs/research_cycles/V80-NBLDPC-JAN21/S2C_RESULT_20260920.md`, `S2C_BATCH_END_REVIEW_20260920.md`, `S2_FALLBACK_OPTIONS_20260920.md`.

**Alternatives considered**:
- Declare route dead: rejected — options O1/O2/O4 unexplored.
- S3 now: rejected — gate unmet, ceiling.

**Consequences**: O4+O2 diagnostic study running; O1 scoping done; no S3; no qualification; user route review pending; records/commits consolidated.

### 2026-09-20/21: O4+O2 lambda study done — {2:1} best on empirical channel; m=50 redundancy-sensitive; O1 (n=1024) becomes leading arm

**Decision**: Record observations (N=64 paired frames/arm, empirical channel, genie-u1): A47 {2:1} m47 33/64 CI [0.396,0.634]; B47 {2:0.5,3:0.5} 10/64; C47 {3:1} 0/64; A50 {2:1} m50 56/64 CI [0.772,0.935]; paired A50⊇A47 (A47-only 0 / A50-only 23); group-ref A50 9/16 (still ≫ gate); ordering A50>A47>B47>C47 with non-overlapping CIs (observation, no winner declared); O2 alone insufficient; per memo ranking O1 becomes the leading next arm (n=1024).

**Context**: QSC-vs-empirical λ ranking reversal (earlier 16-frame sample too small); redundancy sensitivity (+3 rows: +36pp frame success); no causal claims.

**Alternatives considered**:
- Declare λ winner: rejected — observation only pending route review.
- Skip to S3: rejected — gate unmet.

**Consequences**: O1 packet planning started; lambda study raw committed; no S3; no qualification; user route review pending.

### 2026-09-21: O1 n=1024 — A208 first S2-level PASS on the empirical channel (A188 FAIL); margin-sensitive; batch-end review PASS_WITH_FINDINGS

**Decision**: record machine verdicts — A208 (m=208, R=0.7969): 60/60 exact, FER 0.0, f_super=1.294947≤1.3, DE-covered (precheck converged, 36 iters) ⇒ frozen gates met; A188 (m=188, R=0.8164): FAIL-early-stop FER 4/14≈28.6%. Close the O1 batch with the independent batch-end review (PASS_WITH_FINDINGS; OBR-1 fixed by incident line; OBR-2 note-only). Claim ceiling: synthetic + genie-u1 (D1) + single-code acceptance unit + single seed-block + D_blind=0; headroom 4.31 bits so any blind disclosure fails gate (b); no S3/qualification.

**Context**: post-constructor-fix chain (S2c n=256 FAIL → lambda study {2:1} best + redundancy-sensitive → O1 n=1024); +20 rows flips A188→A208 outcome.

**Alternatives considered**:
- Declare route dead: rejected — first pass obtained.
- Generalize to S3: rejected — ceiling.
- Rerun/tune now: rejected — no rerun rule; replication is a new packet.

**Consequences**: pending user review; candidate next steps (not authorized): multi-seed-block replication packet; L1 construction planning to retire genie-u1; blind-surcharge budgeting; no S3 entry yet.

### 2026-09-21: O1R replication both arms PASS (pooled 0/480, two construction instances girth 8 & 6); batch-end review PASS

**Decision**: record — R1 240/240, R2 240/240, pooled 0/480 exact, FER 0.0; both gates met (fails≤12 AND f_super 1.294947≤1.3); no early-stop, no resumes; accept the O1R batch as closed (evidence-only replication; claim ceiling unchanged: genie-u1 D1, synthetic, single-code semantics, D_blind=0 with 4.31-bit headroom, no S3).

**Context**: R2 pre-run pin STOP (girth 6 vs 8) honored → planner Amendment (fc0/rank-full/twice gated; girth recorded-not-gated; pre-committed seed, no tuning); amendment review PASS; batch-end review PASS (ORBR-1..3; ORBR-4 non-blocking).

**Alternatives considered**:
- rerun/tune (rejected — no rerun rule; replication clean)
- generalize beyond ceiling (rejected).

**Consequences**: next queue — L1 construction planning (retire genie-u1 within the shared m_total≤208 budget) + blind surcharge budgeting; no S3; no qualification.

### 2026-09-21: P0 reduced-m L2 probes both PASS (A202 0/240, A200 2/240) — L1 budget channel de-risked; no auto-proceed

**Decision**: record — P0 (genie-u1; paired seeds shared with O1R; n=1024 λ={2:1}): A202 (m=202, f_super 1.25976) 240/240 FER 0.0 PASS; A200 (m=200, f_super 1.24803) 2/240 fails (idx 42, 202; max-iter 300) FER 0.833% PASS; both gates met; batch-end review PASS_WITH_FINDINGS (P0BR-01/02 non-blocking). §7 rule honored: no auto-proceed; A202 PASS ⇒ L1 MAY proceed at m₂≤202; A200 PASS ⇒ m₁=8 option viable (m₂=200); L1 build remains a main-thread decision.

**Context**: L1 memo constraint m₁+m₂≤208, m₁≥6 capacity floor; P0 was the cheapest decisive pre-arm before any L1 spend.

**Alternatives considered**:
- auto-start L1 build (rejected per §7)
- run extra m points (rejected — no decision value, packet restricted arms)

**Consequences**: L1 build planning may proceed (main-thread decision); blind-surcharge budgeting still queued; no S3; no qualification; claim ceiling unchanged (genie-u1, synthetic, single-code semantics, D_blind=0).
