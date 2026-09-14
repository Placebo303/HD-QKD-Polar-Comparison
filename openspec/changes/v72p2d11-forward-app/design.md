# D11 Canonical Forward APP Integration — Design

Frozen authority: `.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md`
§2 (transcribed verbatim where quoted). Track: implementation/readiness now;
future batch `EXPLORE_HEAVY`. D7-H is explicitly out of scope.

## 1. Widths and dispatch

Widths: n128 first; n256 only if n128 is `D11_FORWARD_SIGNAL`.

## 2. L1 reuse and replay hard gate (per width)

Six graph pairs and 12 paired blocks per width. Reuse the accepted R3 L1
graph seeds and blocks so L1 results must replay exactly:

- n128 L1 graphs `2026092401..06`, blocks `2026092601..12`;
- n256 L1 graphs `2026092501..06`, blocks `2026092701..12`.

L1 replay is a hard validity gate: per-graph exact vectors must equal R3
n128 MIX `[4,4,2,5,3,5]`, CONTROL all zero; n256 MIX `[6,3,5,5,6,4]`,
CONTROL all zero. A mismatch is engineering-blocked and stops before
interpretation.

Evidence (read-only, never pooled): R3 Batch A1 log
`docs/research_cycles/V72P2D10-R3-FRESH-SCALING/EXPLORATION_LOG.md`
(n128 `M=23 C=0` per-pair MIX `[4,4,2,5,3,5]` DV3 zeros; n256 `M=29 C=0`
per-pair MIX `[6,3,5,5,6,4]` DV3 zeros; terminal
`D10_R3_WIDE_L1_SIGNAL_REPRODUCED`).

## 3. Shared L2 graphs

Create one shared connected/full-rank DV3 L2 graph per pair:

- n128 L2 seeds `2026092801..06`, rows m=104, E=384, variables all degree 3,
  checks `3^32 + 4^72`;
- n256 L2 seeds `2026092901..06`, rows m=208, E=768, variables all degree 3,
  checks `3^64 + 4^144`.

Arithmetic closure (admission must re-verify, not hand-trust): n128
`32+72=104=m`, `32·3+72·4=384=E=128·3`; n256 `64+144=208=m`,
`64·3+144·4=768=E=256·3`. Socket balance holds by construction.

Use the accepted connectivity-first constructor, A1–A6, frozen coefficient
rule, GF32/poly37, Model-F prior chain, max_iter=90/damping=1.0/cold and the
canonical CHECK_UPDATED provenance/q/APP helpers (reuse map §5; import
unchanged, no reimplementation of message semantics).

## 4. Three-branch design

The only treatment difference is L1 degree profile:

- CONTROL: DV3 L1 → the shared DV3 L2 APP decoder;
- MIX: λ2=0.45 mixed L1 → the same shared DV3 L2 APP decoder;
- ORACLE: the same L2 graph/block with the accepted true-L1 conditional
  prior, run once per graph/block and shared diagnostically across both arms.

Per width: 72 L1+L2 paired cells. Scientific calls are 72 CONTROL L1 +
72 CONTROL L2 + 72 MIX L1 + 72 MIX L2 + 72 shared ORACLE L2 = 360.
Maximum 720. Exact, syndrome-valid, L1 source exact, L2 target exact and
joint both-exact must remain distinct. Fail closed unless every non-oracle
transfer provenance is `CHECK_UPDATED`; uniform/prior-only fallback is
forbidden.

## 5. Reuse map (D1102 audit — import unchanged, duplication rejected)

Base path for all entries:
`comparison_bench/src/comparison_bench/formal_ir/`.

(a) L1→L2 forward transfer (message/provenance semantics):

- `v72p2d7_gf32_cross_layer_discriminator.py:603`
  `transfer_prior_l1_to_l2(joint, bob, q1)` —
  `P_transfer(U2|B) = sum_u1 q1(u1) P(U2|B,u1)`, `(n,32)`, single
  accepted floor/renorm applied once. Direction-dispatched entry
  `build_transfer_prior`:623; reverse leg `transfer_prior_l2_to_l1`:613
  (not invoked by D11; D7-H closed).
- `v72p2d7_gf32_cross_layer_discriminator.py:528`
  `check_source_eligibility(...)` — pure scalar gate; transfer invoked only
  on `(eligible, ELIGIBLE)` (source crash/nonfinite/shape/provenance blocks
  are recorded non-invocations, never replacements).
- `v72p2d5_gf32_rate_mother.py:961` `canonical_source_q` +
  `v72p2d5_gf32_rate_mother.py:354` `app_fed_l2_prior` via `:978`
  `canonical_transfer_l2_prior` — canonical `q @ P` implementation the
  frozen D7 chain is held consistent against.
- `v72p2d5_gf32_rate_mother.py:1403` `_run_layered_block` — the accepted
  one-block L1→L2 layered pattern D11 mirrors (fail-closed L1 gate, then
  mixer, then L2 decode, then optional oracle): transfer-invoked path
  `:1445–:1467`, oracle path `:1468–:1472`.

(b) CHECK_UPDATED provenance emission/check:

- `v35_algorithm_development.py:524`
  `BELIEF_PROVENANCE_CHECK_UPDATED = "CHECK_UPDATED"` (token definition;
  `:519–:530` contract: labels a BP APP approximation that incorporated
  check messages, not a calibrated exact posterior) and `:540`
  `require_check_updated_provenance(provenance, *, consumer)` with `:536`
  `UnconditionedBeliefProvenanceError` refusal type.
- `v72p2d5_gf32_rate_mother.py:1396` `_require_check_updated_provenance`
  (lazy v35 bind; D5-layer alias).
- `v72p2d7_gf32_cross_layer_discriminator.py:504`
  `require_check_updated` (delegates to the accepted D5 helper, never to
  the `:158` literal) and `:162`/`d7c` current-belief record labels
  (`CHECK_UPDATED_CURRENT_BELIEF` is iterations-derived, never a provenance
  token).

(c) q/APP helpers:

- `v72p2d7_gf32_cross_layer_discriminator.py:556` `softmax_source_q`
  (transient source APP: rowwise softmax of one CHECK_UPDATED current log
  belief, `(n,32)`); D7-C `v72p2d7_gf32_bidirectional_oracle.py:523`
  `_softmax_rows`; D5 `v72p2d5_gf32_rate_mother.py:949` `_softmax_rows`.
- `v45_l1_app_soft_transfer.py:382` `softmax_beliefs` and `:358`
  `get_l1_app_prior_l2` (treatment `Σ q(u1) P(U2|B,u1)` formulation
  reference); D5 `:354` is the canonical implementation D11 imports.

(d) D6-chain oracle — accepted true-L1 conditional prior (diagnostic-only):

- `v35_algorithm_development.py:432` `get_conditional_posterior_l2`
  (original counts-domain `P(U2|B=b,U1=u1_true)`; cf. V38 correction
  history: complete `bob` must be passed, never a partial slice).
- `v72p2d5_gf32_rate_mother.py:379` `oracle_l2_prior`
  (accepted Model-F p2-domain successor; **canonical import for D11**;
  consumed by `_run_layered_block` at `:1469`).
- `v72p2d7_gf32_bidirectional_oracle.py:487` `condition_prior_qn`
  (`L2_ORACLE_U1` branch `:507–:510`) + `:514` `decoder_prior`
  (single frozen floor) — the D7-C oracle-condition formulation reference.

Construction / admission / decoder-path reuse (D10 R2/R3, per R3 R302
contract and packet D1103):

- Connectivity-first constructor:
  `v72p2d10_mixed_degree_l1.py:241` `build_degree_sequence_peg`
  (Phase A seeded spanning backbone + Phase B shared R1 PEG/ACE fill; one
  deterministic attempt per seed, no replacement seeds).
- A1–A5: `v72p2d10_mixed_degree_l1.py:628` `structural_record`
  (admission dict `:681–:691`: A1 exact degrees/socket balance, A2 simple
  graph + min degree, A3 single component, A4 structural rank m, A5 GF32
  rank m); A6 deterministic replay inside `:726` `build_graph`
  (`:755–:764`, edge-list + coefficient-stream equality).
- Rank primitives: `:457` `structural_rank` (Kuhn, fixed order),
  `:545` `gf32_row_rank` (poly 37).
- Frozen coefficient rule: `:584` `coefficient_seed`
  (`v10_seed("d10:coeff:{width}:{graph_seed}")`) + `:589`
  `coefficients_for_edges` (one uniform nonzero GF32 draw per edge in
  sorted `(v,c)` order); matrix assembly `:602` `dense_from_edges`.
- L1 dispatch: `:855` `dispatch_l1` (admission gate before decoder
  binding; non-admitted graph raises via `:189`
  `StructureNotAdmitted`); R3 seeds/cells/plan:
  `v72p2d10_r3_fresh_scaling.py:79–:87` (`GRAPH_SEEDS`/`BLOCK_SEEDS`),
  `:90–:103` (`DEGREE_TABLE`), R2 contract constants `:92–:94`
  (`Q=32`, `POLY=37`, `MODEL_F_INPUT_ROOT`) and `:154–:155`
  (`DECODER_MAX_ITER=90`, `DAMPING_ALPHA=1.0`).
- Decoder: `v35_algorithm_development.py:781`
  `decode_row_layered_fftqspa` (cold, row-layered, `max_iter=90`,
  `damping_alpha=1.0`, `warm_beliefs=None`), via the D7-E lazy-bind shape
  `v72p2d7_gf32_cross_layer_discriminator.py:666`
  `bind_row_layered_decoders` (SOURCE/TARGET roles; D11 uses the forward
  role pair only).
- Field/prior constants: D5 `v72p2d5_gf32_rate_mother.py:39` (`Q=32`),
  `:46` (`LAMBDA_STAR`), `:48` (`DECODER_FLOOR=1e-15`), `:85`
  (`MODEL_F_INPUT_FORMAL_ROOT`), `:90–:91`
  (`MAX_ITER=90`, `DAMPING_ALPHA=1.0`); D7-C
  `v72p2d7_gf32_bidirectional_oracle.py:53–:81` (operating-point
  constants; D11 widths/seeds/rows come from this design, not D7-C).

Duplication-rejection statement: D11 (D1103+) must import every helper
above unchanged and route all transfer/provenance/oracle/admission
semantics through them. Any reimplementation of message semantics
(transfer mixer, q extraction, provenance token/guard, oracle
conditioning, floor/renorm order, A1–A6 predicates, coefficient stream)
is explicitly rejected; D11 code is limited to the frozen plan (seeds,
cells, call order, gates, terminals), the runner/verifier wiring, and
output accounting.

## 6. Absence scan (raw output, 2026-09-14)

Repo-wide search for `20260928|20260929|7c1878b5` returned exactly 3
matches, all inside the authorizing packet itself
(`.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md`
lines 29, 31, 79). No code, config, test, workspace root, or output
references the 12 L2 seeds or the future-root UUID — no collision.
Direct read probe of
`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`:
no such path (absent). STOP-on-collision condition not triggered.

## 7. Gates, priority, terminals

For each width let `J_M,J_C` be pooled joint both-exact counts; `O`
pooled L2 oracle exact; and `J_Mg,J_Cg` per graph.

`D11_FORWARD_SIGNAL(w)` iff: `J_M>=9`; `J_M-J_C>=6`; MIX wins on ≥4/6
graph pairs; ≥3/6 MIX graphs have `J_Mg>=1`; `J_C<=3`; `O>=18`; all 72
MIX and 72 CONTROL transfers are CHECK_UPDATED; no engineering/resource
violation.

`D11_TRANSFER_BOTTLENECK(w)` iff MIX L1 exact ≥18, `J_M<=3`, and `O>=18`.
`D11_L2_CODE_BOTTLENECK(w)` iff `O<=6`. Otherwise
`D11_FORWARD_AMBIGUOUS(w)`. These are mutually prioritized in order:
engineering block, L2-code bottleneck, forward signal, transfer
bottleneck, ambiguous. Report paired discordances and conditional target
success descriptively; they do not override the gate.

Terminals (packet §2 verbatim labels):

- n128 forward signal, n256 forward signal →
  `D11_FORWARD_APP_WIDE_RECOVERY`;
- n128 signal, n256 transfer/L2/ambiguous → corresponding
  `D11_N256_TRANSFER_BOTTLENECK`, `D11_N256_L2_CODE_BOTTLENECK`, or
  `D11_N256_FORWARD_AMBIGUOUS`;
- n128 stop → corresponding `D11_N128_TRANSFER_BOTTLENECK`,
  `D11_N128_L2_CODE_BOTTLENECK`, or `D11_N128_FORWARD_AMBIGUOUS`;
- explicit engineering/resource blocked terminal otherwise.

Count reading (flagged for D1110 confirmation): the "six terminals" are
the six width-qualified stop terminals (3 × n256 + 3 × n128) above, plus
the `D11_FORWARD_APP_WIDE_RECOVERY` success terminal and the
engineering/resource blocked catch-all. No label is added, renamed, or
dropped relative to the packet.

## 8. Future root, budgets, claim ceiling

Future root:
`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`
(absent, §6). Budgets: ≤720 scientific calls; ≤64 setup units; ≤2400 s
wall; ≤120 s/call; RSS <2147483648 B; one process; no
retry/resume/repair/seed search/tuning.

Claim ceiling: synthetic two-layer forward diagnostic only; no FER,
leakage, SKR, real-data, qualification, promotion, optimality or D7-H
claim.

## 9. Rationale

R3 proved the L1 signal is real and reproducible on fresh graphs at two
widths (MIX 23/72 and 29/72 vs DV3 0/72). The next orthogonal question is
whether that signal survives one canonical forward APP integration with
the L2 target held fixed (shared DV3 graph per pair removes L2-topology
confound between arms), while the shared oracle separates L2-code
ceiling from transfer loss. Conditional n256 dispatch spends the second
width only if n128 shows a forward signal.
