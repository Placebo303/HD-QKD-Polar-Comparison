# Design — D14N Calibrated L1/L2 Discriminator (readiness, N201)

Frozen authority: `.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md`
§2 (transcribed verbatim where quoted) + `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
§2–§8 (accepted preregistration — transcribed exactly, not reinterpreted).
Track: `EXPLORE` (implementation/readiness now; future batch `EXPLORE`).
D7-H is explicitly out of scope (prereg §10).

## 1. Width and arms (prereg §3, verbatim substance)

- Width: **n=128 only**. D12 showed no `SPLIT_WIDTH_CONFLICT` (both widths
  preferred L055), so width is not the routing variable; the n128 load gradient
  (r=-0.64) is present; n256 extension belongs to a later packet, not this
  discriminator. n256 is explicitly out of scope.
- L1 CONTROL (frozen control): L045 degree profile, edge-fraction λ2=0.45,
  realized at frozen m_L1=110 (see §2) via the frozen D9 realization rule (as
  audited by D12-R1210).
- L1 challenger: L055 degree profile, λ2=0.55, same m_L1=110, same rule.
  This re-tests L055-vs-L045 at the calibrated rate; it is NOT a rerun of D12
  (D12 ran CE-f1.2, m=118).
- L1 shared contract (D12 verbatim unless noted): connectivity-first constructor
  `build_degree_sequence_peg`; A1–A6 admission before decoder binding;
  `COEFF_SEED = v10_seed(f"d10:coeff:128:{graph_seed}")`; Model-F CAL-only L1
  prior chain (candidate chain); GF32/poly37; decoder `max_iter=90` /
  `damping_alpha=1.0` / cold. Exact (n2,n3,E) counts are emitted by the future
  runner's PROFILE_ONLY plan from the frozen rule + frozen seeds and verified at
  review — they are NOT hand-computed in this freeze (no guessing).
- L2 diagnostic (never gating): frozen D11 DV3 shape at n128 — m=104, E=384,
  checks `3^32+4^72`, connectivity-first, A1–A6, same coefficient/prior/decoder
  contract — on fresh seeds §3. Kept at the D11 shape (not entropy-derived
  m=83) so the D11 bottleneck vocabulary (O≥18 / O≤6) stays comparable; creating
  a new untested L2 family would violate "smallest".
  - L2 APP: shared DV3 L2 APP decoder on the forward-transfer beliefs.
  - L2 ORACLE: same L2 graph/block with the accepted true-L1 (true-U1)
    conditional prior, once per graph/block, shared diagnostically, EXCLUDED
    from all grading and all routing gates.
  - L2 load context (descriptive only): n128 L2 load = 412.50815 bits;
    DV3 disclosed = 520 bits → effective ≈1.26058 (over-disclosed by
    construction, conservative toward detecting L2-code failure).

## 2. Rate math (prereg §4, stated — not recomputed)

- H_L1 = 4.286720430201375 (R-reproduced, provenance `entropy.json`).
- Entropy load n128: 128 × H_L1 = 548.700215065776 bits.
- Frozen m_L1 = ceil(548.700215065776/5) = **110 checks**; disclosed = 550 bits;
  effective factor = 550/548.700215065776 = **1.00237**.
- Contrast recorded (not used): CE-f1.0 rows would be ceil(128×3.814742/5)=98,
  disclosed 490 bits, effective 0.89302 — the under-disclosure this freeze refuses.
- Choice A (prereg §2): rates/rows are derived from the ACTUAL generator entropy;
  the generator is NOT changed (accepted CAL-only Model-F artifact
  `workspace/v72p2d5_model_f_input/20260907_r1`).

## 3. Degree cells, seeds, pairing, calls (prereg §3–§6)

Degree cells (frozen D12 cells for n128 — verified MATCH, proposal §verification):

| arm | n2 | n3 | E | check allocation |
|---|---|---|---|---|
| L045 control | 71 | 57 | 313 | `2^41+3^77` |
| L055 challenger | 83 | 45 | 301 | `2^53+3^65` |

L2 DV3 (frozen D11 shape at n128 — verified MATCH): m=104, E=384, variables all
degree 3, checks `3^32+4^72` (32+72=104=m; 32·3+72·4=384=E=128·3).

Seeds (fresh; absence re-confirmed, proposal §verification):

- L1 graphs: `2026093401..06` (6 fresh).
- L2 graphs: `2026093501..06` (6 fresh).
- Blocks: `2026093601..12` (12 fresh paired block seeds, sampled with the
  accepted D8–D12 block helper from the CAL-only Model-F artifact only).
- Pairing: L1-graph-i pairs with L2-graph-i (i=1..6); each pair × 12 blocks =
  72 cells. The same 12 blocks feed L045-L1, L055-L1, L2-APP, and L2-ORACLE
  (fully paired; L045/L055 discordances computed paired per D12).

Call list (exact; total 288 decoder calls):

| # | Arm | Identities | Calls |
|---|---|---|---|
| 1 | L1 CONTROL (L045) | 6 graphs × 12 blocks | 72 |
| 2 | L1 L055 | 6 graphs × 12 blocks | 72 |
| 3 | L2 APP (shared DV3) | 6 pairs × 12 blocks | 72 |
| 4 | L2 ORACLE (true-L1 prior; diagnostic, ungraded) | 6 pairs × 12 blocks | 72 |
| **Total** | | | **288** |

- Setup units: ≤26 (= 12 graph constructions + 12 block samples + 2 plan/manifest).
- Metric isolation: exact primary; syndrome-valid separate; L1-source-exact /
  L2-target-exact / joint-both-exact distinct; `undetected` isolated, never merged
  into success/FER. Fail-close: every non-oracle transfer provenance must be
  `CHECK_UPDATED`; uniform/prior-only fallback forbidden.
- Batch sizing rationale: 288 calls is the minimum carrying 6-graph seed
  variation (multi-seed default where variability could confound) with 12 paired
  blocks per graph — only large enough to route the next investment (§5).

## 4. Reuse map (import unchanged, duplication rejected)

Base path for all module entries:
`comparison_bench/src/comparison_bench/formal_ir/`.

(a) D11 forward-app pattern (plan/dispatch/transfer/oracle — N202/N204 donors):

- `v72p2d7_gf32_cross_layer_discriminator.py:603`
  `transfer_prior_l1_to_l2(joint, bob, q1)`; direction dispatch
  `build_transfer_prior`:623; `check_source_eligibility`:528 (pure scalar gate).
- `v72p2d5_gf32_rate_mother.py:961` `canonical_source_q` +
  `:354` `app_fed_l2_prior` via `:978` `canonical_transfer_l2_prior`
  (canonical `q @ P` implementation); `:1403` `_run_layered_block`
  (accepted one-block L1→L2 layered pattern: fail-closed L1 gate, mixer, L2
  decode, optional oracle — transfer path `:1445–:1467`, oracle `:1468–:1472`).
- Oracle (D6-chain, diagnostic-only): `v72p2d5_gf32_rate_mother.py:379`
  `oracle_l2_prior` (canonical import; consumed at `:1469`); references
  `v35_algorithm_development.py:432` `get_conditional_posterior_l2` and D7-C
  `v72p2d7_gf32_bidirectional_oracle.py:487` `condition_prior_qn` + `:514`
  `decoder_prior`.

(b) D5/D7 canonical transfer/provenance/oracle (N204/N205 donors):

- Provenance token/guard: `v35_algorithm_development.py:524`
  `BELIEF_PROVENANCE_CHECK_UPDATED = "CHECK_UPDATED"` (+`:519–:530` contract,
  `:540` `require_check_updated_provenance`, `:536`
  `UnconditionedBeliefProvenanceError`); D5 alias
  `v72p2d5_gf32_rate_mother.py:1396` `_require_check_updated_provenance`;
  D7 delegate `v72p2d7_gf32_cross_layer_discriminator.py:504`
  `require_check_updated`.
- q/APP helpers: `v72p2d7_gf32_cross_layer_discriminator.py:556`
  `softmax_source_q`; D5 `:949` `_softmax_rows`; D5 `:354` canonical
  implementation N imports; `v72p2d5_gf32_rate_mother.py:2480-2507`
  `prepare_model_f_prior_candidate` / `build_f_model_concentration`
  (candidate chain, frozen `LAMBDA_STAR=137.3823795883263870`); `:309-321`
  `marginalize_f_to_p1`; `:346-351` `_floor_renorm` (`DECODER_FLOOR=1e-15`
  at `:48`); `:873-911` `sample_matched_block`.
- Decoder bind: `v35_algorithm_development.py:781`
  `decode_row_layered_fftqspa` (cold, row-layered, `max_iter=90`,
  `damping_alpha=1.0`, `warm_beliefs=None`) via D7-E lazy-bind shape
  `v72p2d7_gf32_cross_layer_discriminator.py:666`
  `bind_row_layered_decoders`; `:139-157` `syndrome_of_gf32`.

(c) D12 finite-L1 pattern (degree cells/plan/gates — N202/N203/N205 donors):

- `v72p2d10_mixed_degree_l1.py:241` `build_degree_sequence_peg`;
  `:628` `structural_record` (A1–A5 dict `:681–:691`); `:726` `build_graph`
  with A6 replay (`:755–:764`); `:457` `structural_rank`; `:545`
  `gf32_row_rank` (poly 37); `:584` `coefficient_seed` +
  `:589` `coefficients_for_edges` + `:602` `dense_from_edges`;
  `:855` `dispatch_l1` (admission before decoder binding; `:189`
  `StructureNotAdmitted`); R3 seeds/cells/plan
  `v72p2d10_r3_fresh_scaling.py:79–:87,90–:103`.
- Frozen coefficient rule: `COEFF_SEED =
  v10_seed(f"d10:coeff:128:{graph_seed}")`, one uniform nonzero GF32 draw per
  edge in sorted order; same rule all arms.

(d) D14 rate-audit helpers (rate-math provenance — N202 donor):

- `v72p2d14_rate_calibration_audit.py` (entropy/rate math provenance for the
  Choice-A values stated in §2); thin runner
  `scripts/v72p2d14_rate_calibration_audit.py`.

(e) R2 construction/admission constants (N203 donor):

- R2 contract constants `Q=32`, `POLY=37`, `MODEL_F_INPUT_ROOT`,
  `DECODER_MAX_ITER=90`, `DAMPING_ALPHA=1.0`; field/prior constants D5
  `:39` (`Q=32`), `:46` (`LAMBDA_STAR`), `:85`
  (`MODEL_F_INPUT_FORMAL_ROOT`), `:90–:91` (`MAX_ITER=90`,
  `DAMPING_ALPHA=1.0`).

Duplication-rejection statement: N203+ MUST import every helper above unchanged
and route all transfer/provenance/oracle/admission semantics through them. Any
reimplementation of message semantics (transfer mixer, q extraction, provenance
token/guard, oracle conditioning, floor/renorm order, A1–A6 predicates,
coefficient stream) or any copy of decoder/GF32 kernels is explicitly rejected;
N code is limited to the frozen plan (seeds, cells, call order, gates,
terminals), the runner/verifier wiring, and output accounting. One construction
path per frozen arm family.

## 5. Gates, routing, terminals (prereg §7 verbatim logic)

Reuse of the D11/D12 gate vocabulary on the 72-cell pools:

- `L1-ADEQUATE(L055)` iff exact ≥18/72 AND ≥5/6 graphs have ≥2 exact AND no
  engineering/resource violation (D12 STABLE reuse).
- `ORACLE-ADEQUATE` iff O ≥18/72 (D11 clause reuse).
- `L2-JOINT-GOOD` iff J (APP joint-both-exact pooled) ≥9/72 (D11 J_M≥9 reuse).
- L045 pooled exact + paired L055-only/L045-only discordances reported
  descriptively (D12 MATERIAL-style), never gating the route.

Routing (first match wins):

1. Engineering/resource violation → `N_ROUTE_BLOCKED_ENGINEERING` (no routing claim).
2. NOT `L1-ADEQUATE` → **`N_ROUTE_L1_CONSTRUCTION`** (next investment: L1
   construction/degree-profile work at the calibrated rate).
3. `L1-ADEQUATE` AND NOT `L2-JOINT-GOOD` AND NOT `ORACLE-ADEQUATE`
   (D11 L2-code-bottleneck pattern, O≤6) → **`N_ROUTE_L2_DEGREE`** (next
   investment: L2 degree design).
4. `L1-ADEQUATE` AND `ORACLE-ADEQUATE` AND NOT `L2-JOINT-GOOD` →
   **`N_TRANSFER_BOTTLENECK_RECORDED`** (forward-transfer question recorded;
   D7-H NOT revived — see §7).
5. `L1-ADEQUATE` AND `L2-JOINT-GOOD` → **`N_ROUTE_SCALE_VALIDATION`** (both
   layers adequate at the calibrated rate; next step is a separately
   preregistered scale/validation packet, still no auto execution).
6. Else → `N_ROUTE_AMBIGUOUS` (no investment claim; escalate to planner).

Six routing terminals: `N_ROUTE_L1_CONSTRUCTION`, `N_ROUTE_L2_DEGREE`,
`N_TRANSFER_BOTTLENECK_RECORDED`, `N_ROUTE_SCALE_VALIDATION`,
`N_ROUTE_AMBIGUOUS`, `N_ROUTE_BLOCKED_ENGINEERING`. L045 discordances are
descriptive only (N205: unit-test every boundary and priority collision).

## 6. Runner, root, command, budgets (prereg §8)

- Future runner `scripts/v72p2d14_discriminator_development.py` (later change;
  no N code under this change's readiness scope beyond N201–N210 wiring) SHALL:
  default `--execution-authorized` false with refusal before root
  creation/decoder binding/Model-F load; offer `--profile-only` (all 12 graphs
  A1–A6 + 288-identity plan + root-absent proof, zero decoder calls) and
  `--verify` (read-only fail-closed recomputation) paths; add `--n14-batch`.
  Default-false batch refusal MUST occur before output creation, decoder
  binding, or Model-F load (packet N206).
- Frozen fresh root: `workspace/v72p2d14_discriminator/20260914_r1/`
  (proven absent; never overwritten; six-file shape mirroring D11/D12:
  `command_log`, `decoder_records`, `graph_records`, `arm_summary`, `manifest`,
  `summary`; future `batch_id == d14-discriminator-v1`, verifier rejects all else).
- Frozen exact command (unauthorized — verbatim prereg §8 string; the runner
  belongs to a later authorized change reusing the D11/D12 runners per VR-N-03):

```text
.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/v72p2d14_discriminator/20260914_r1
```

- Frozen budgets (within proposal N ceilings: 120 s/call, ≤3600 s, <2 GiB,
  ≤720 calls, D10–D12 class): ≤288 decoder calls; ≤26 setup units; ≤1800 s wall
  total; ≤120 s per call; RSS <2147483648 B; one process; CPU-only; no
  retry/resume/repair/seed search/tuning. Ceiling breach → STOP as out-of-scope,
  re-scope, never tune.

## 7. Claim ceiling; D7-H (prereg §9–§10)

- Synthetic diagnostic only. This packet routes the next investment (L1
  construction vs L2 degree design) and makes no FER, leakage, SKR, real-data,
  qualification, promotion, optimality, or route-closure claim. It grants no
  execution.
- D7-H is NOT revived by this packet. Per packet §7 it may be reconsidered only
  after calibrated single-layer AND forward baselines show that alternating
  transfer addresses the remaining bottleneck. This batch contributes ONE such
  baseline pair and is alone insufficient — even a `N_TRANSFER_BOTTLENECK_RECORDED`
  terminal only records the question and returns to the planner.
- Terminal: `READY_AWAITING_EXPLICIT_AUTHORIZATION` — root absent, unauthorized,
  execution false.

## 8. Freeze Amendment A1 (main-thread adjudicated — retain + supersede, 2026-09-14)

Corrigendum pattern: the accepted prereg
`docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md` is NOT
edited. This section retains it and supersedes exactly the items listed in
§8.3–§8.5 below. Authority: main-thread adjudication on the N task packet §2
STOP rule (frozen L1 check-allocation vs frozen m_L1 mismatch).

### 8.1 Mismatch evidence (triggering the STOP)

- Frozen L1 degree cells transcribed in §3 (L045 71/57/313 `2^41+3^77`; L055
  83/45/301 `2^53+3^65`) are D12 m=118 cells: check-node counts sum to 118
  (41+77=118; 53+65=118), not the frozen m_L1=110 (§2).
- Socket cross-check at m=118 closes on the same E: L045 41·2+77·3=82+231=313;
  L055 53·2+65·3=106+195=301 — i.e. these are the m=118 floor/ceil
  allocations of the same edge totals (b=E−2·118: 313−236=77; 301−236=65).
- Constructor probe (reported by main thread): m=110 refuses these
  allocations, m=118 accepts — consistent with the arithmetic above.
- Prereg §3 stated exact (n2,n3,E) are emitted by PROFILE_ONLY, never
  hand-computed; the freeze nevertheless carried the D12 check-allocation
  strings verbatim, which is where the m=118 values entered.

### 8.2 Adjudication (implement exactly)

- (A) ADOPTED: variable counts (n2/n3/E) derive from λ2 apportionment over
  n=128 variables — m-independent — so they STAND: L045 71/57/E313; L055
  83/45/E301. Check allocation re-derives from (E, m=110) floor/ceil per the
  frozen D9 rule: L045 `2^17+3^93`; L055 `2^29+3^81` (min dc 2, consistent
  with mixed arms). Full re-derivation in §8.3; planner recompute CONFIRMS
  the adopted cells (no BLOCKED).
- (B) REJECTED with rationale to record: setting m_L1=118 to fit the old
  check strings would disclose 118·5=590 bits, effective
  590/548.700215065776=1.07527≈1.0753, destroying accepted Choice A
  (550/548.700215065776=1.00237, effective≈1.0) — the entire point of the N
  discriminator. Rate math (§2) and Choice A are unchanged.

### 8.3 Re-derived cells with full D9-rule arithmetic (planner recompute — CONFIRMED)

Frozen D9 rule applied (read-only recompute, no execution):
variable side `edge_to_node` L_d=(λ_d/d)/Σ(λ_j/j) → largest-remainder to
n=128 → E=Σn_d·d; check side concentrated floor/ceil at m with a+b=m and
floor·a+ceil·b=E (b=E−floor·m).

Variable side (m-independent — STANDS):

- L045 (λ2=0.45 edge-fraction, λ={2:0.45,3:0.55}):
  0.45/2=0.225; 0.55/3=0.1833333333; Σ=0.4083333333;
  L2=0.225/0.4083333333=0.5510204082; L3=0.4489795918;
  ×128: n2*=70.5306122449, n3*=57.4693877551;
  floors 70+57=127, remainder 1; fractions 0.5306>0.4694 → +1 to deg-2 →
  **n2=71, n3=57**; E=71·2+57·3=142+171=**313**. STANDS.
- L055 (λ2=0.55, λ={2:0.55,3:0.45}):
  0.55/2=0.275; 0.45/3=0.15; Σ=0.425;
  L2=0.275/0.425=0.6470588235; L3=0.15/0.425=0.3529411765;
  ×128: n2*=82.8235294118, n3*=45.1764705882;
  floors 82+45=127, remainder 1; fractions 0.8235>0.1765 → +1 to deg-2 →
  **n2=83, n3=45**; E=83·2+45·3=166+135=**301**. STANDS.

Check side (re-derived at frozen m_L1=110, min dc 2):

- L045: dc_avg=313/110=2.8454545455; floor 2 / ceil 3;
  b=313−2·110=313−220=**93**, a=110−93=**17** → **`2^17+3^93**;
  verify 17+93=110=m; 17·2+93·3=34+279=313=E. ADOPTED (supersedes `2^41+3^77`).
- L055: dc_avg=301/110=2.7363636364; floor 2 / ceil 3;
  b=301−2·110=301−220=**81**, a=110−81=**29** → **`2^29+3^81**;
  verify 29+81=110=m; 29·2+81·3=58+243=301=E. ADOPTED (supersedes `2^53+3^65`).

Old-string cross-check (confirms the m=118 diagnosis, not reused):
L045 `2^41+3^77`: 41+77=118; 82+231=313=E; b=313−236=77.
L055 `2^53+3^65`: 53+65=118; 106+195=301=E; b=301−236=65.

Effective-disclosure check (option-B rejection arithmetic):
m=110 → 550/548.700215065776=1.0023688≈**1.00237** (Choice A, unchanged);
m=118 → 590/548.700215065776=1.0752686≈**1.0753** (rejected).

### 8.4 Setup-32 ruling and PROFILE scope (supersedes §3/§6 setup line)

- Prereg/design "≤26 (= 12 graph constructions + 12 block samples +
  2 plan/manifest)" counted distinct graph *seeds* (6 L1 + 6 L2 = 12),
  conflating shared-seed profiles: each of the 6 L1 seeds builds TWO
  distinct degree-profile objects (L045 + L055).
- Amended setup: **≤32 = 18 built objects (6 L045 + 6 L055 at the 6 shared
  L1 seeds + 6 L2) + 12 block samples + 2 fixed (plan/manifest)**.
- PROFILE scope: **18 graphs over 12 seeds** (6 L1 seeds × 2 profiles + 6 L2
  seeds × 1 profile). PROFILE_ONLY SHALL construct all 18, prove A1–A6 on
  each, and emit the amended mixed-degree counts + the 288-identity plan
  with zero decoder calls and no future-root write.
- All other budgets unchanged: ≤288 decoder calls; ≤1800 s wall total;
  ≤120 s per call; RSS <2147483648 B; one process; CPU-only; no
  retry/resume/repair/seed search/tuning.

### 8.5 Unchanged items (explicit)

Thresholds, gates, routing priority, six terminals, seeds and pairing, rate
math (H_L1/load/m=110/disclosed-550/1.00237), 288-call list (72×4), prior /
decoder / coefficient / admission contract, metric isolation
(`undetected` never merged), L2 DV3 shape (m=104/E=384/`3^32+4^72`), frozen
root/command, claim ceiling (synthetic diagnostic, no FER/leakage/SKR/
real-data/qualification/promotion/optimality/route-closure claim, no
execution), D7-H out of scope, n=128 only. N202–N210 retry on the amended
freeze; no new seeds, no threshold edits.
