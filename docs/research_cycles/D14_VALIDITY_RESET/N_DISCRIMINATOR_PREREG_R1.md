# N — Paired L1/L2 Calibrated Discriminator Prereg R1 (frozen, unauthorized)

- Authority: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md` §7 (Phase N)
  + §9 (return); `openspec/changes/v72p2d14-scientific-validity-reset/design.md` §5;
  `specs/validity-reset/spec.md` §VR-N; `tasks.md` N1.
- Track: `EXPLORE` (synthetic diagnostic preregistration; docs only).
- Branch: `formal-ir-v72p1-addendum-clean` (no switch).
- Status: `READY_AWAITING_EXPLICIT_AUTHORIZATION` — grants no execution.
  **Contingent**: R evidence used here is the R-run output of 20260914_r1; the
  final independent review (R3/N2/F) is still pending. This freeze becomes
  consumable only after that review passes; any review FAIL blocks it.
- This call: docs only. No code, no execution, no decoder/real-data calls
  (decoder calls 0), no commit, no push.

## 1. Evidence basis (ONLY this; all values recomputed, never copied)

R root `workspace/v72p2d14_rate_audit/20260914_r1/` (`report.md`, `entropy.json`,
`rate_rows.csv`, `crosscheck.json`):

- Generator entropy (accepted candidate chain
  `prepare_model_f_prior_candidate`/`build_f_model_concentration`,
  `LAMBDA_STAR=137.3823795883263870`; floor-then-log `max(p,1e-300)`, no renorm;
  axes `p_f(Alice=1024,Bob=1024)`, `A=32*U1+U2`; bits/symbol):
  joint **7.5094403148**, L1 **H_L1=4.286720430201375**, L2 **H_L2=3.222719884634378**.
  Reproduced at 4dp vs hypotheses (dL1=+0.000020, dL2=+0.000020).
- Frozen rows verified: P0/G1 n64 49/59 + 43/52; G2 n256 196/215/235 + 172/189/206;
  `rows = ceil(n*CE*f/5)` with frozen CE L1=3.814742 / L2=3.347605 (D4 frozen CE,
  D4R2 outer-F TEST means).
- Factor-triple status: hypothesis triple (0.890/0.979/1.068) MISMATCHES the
  recomputed effective L1 factors (n256: 0.8930195/0.9795877/1.0707122;
  deltas +0.003/+0.001/+0.003). The triple has **no predecessor record** and is
  **never copied** into this freeze; retained as an open calibration note only.
- Per-block: 24 D12 identities (432 calls, 221 exact, 0 undetected isolated);
  120 D11 rows (720 calls, 0 undetected isolated). Load gradients n128 r=-0.64,
  n256 r=-0.75, with load-vs-success separation (`I<=disclosed` never sufficient).
- Context (not evidence for any frozen value): P-impl complete (P0/G1/G2 select
  the candidate chain, 4 focused tests pass, legacy retained); C-impl complete
  (G2/X4 corrigendum recorded, rejected-config scope, grade retained).

## 2. Rate/row-vs-generator choice (frozen): CHOICE A — entropy-derived rows, NO generator change

- **Frozen choice**: rates/rows are derived from the ACTUAL generator entropy
  (§1). The generator is NOT changed.
- **Why**:
  1. The generator is the accepted CAL-only Model-F artifact
     (`workspace/v72p2d5_model_f_input/20260907_r1/`); changing it would break
     comparability with all D8–D13 evidence and force re-validation of the
     accepted concentration-backoff chain.
  2. R evidence shows the frozen CE constants understate the actual L1 load by
     ~11.9% (effective factor 0.89302 at f1.0 — CE rows would bake
     under-disclosure into the discriminator and confound code/decoder failure
     with insufficient disclosure).
  3. At entropy-derived f=1.0 (disclosed ≈ load, effective ≈1.0024), residual
     failure attributes to finite-length construction/code/decoder — exactly the
     signal the L1-vs-L2 routing decision needs.

## 3. Frozen arms (n128 only)

- Width: **n=128 only**. D12 showed no `SPLIT_WIDTH_CONFLICT` (both widths
  preferred L055), so width is not the routing variable; the n128 load gradient
  (r=-0.64) is present; n256 extension belongs to a later packet, not this
  discriminator. n256 is explicitly out of scope.
- L1 CONTROL (frozen control): L045 degree profile, edge-fraction λ2=0.45,
  realized at frozen m_L1=110 (see §4) via the frozen D9 realization rule (as
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
  contract — on fresh seeds §5. Kept at the D11 shape (not entropy-derived
  m=83) so the D11 bottleneck vocabulary (O≥18 / O≤6) stays comparable; creating
  a new untested L2 family would violate "smallest".
  - L2 APP: shared DV3 L2 APP decoder on the forward-transfer beliefs.
  - L2 ORACLE: same L2 graph/block with the accepted true-L1 (true-U1)
    conditional prior, once per graph/block, shared diagnostically, EXCLUDED
    from all grading and all routing gates.
  - L2 load context (descriptive only): n128 L2 load = 412.50815 bits;
    DV3 disclosed = 520 bits → effective ≈1.26058 (over-disclosed by
    construction, conservative toward detecting L2-code failure).

## 4. Frozen rate math (L1)

- H_L1 = 4.286720430201375 (R-reproduced, provenance `entropy.json`).
- Entropy load n128: 128 × H_L1 = 548.700215065776 bits.
- Frozen m_L1 = ceil(548.700215065776/5) = **110 checks**; disclosed = 550 bits;
  effective factor = 550/548.700215065776 = **1.00237**.
- Contrast recorded (not used): CE-f1.0 rows would be ceil(128×3.814742/5)=98,
  disclosed 490 bits, effective 0.89302 — the under-disclosure this freeze refuses.

## 5. Frozen seeds (fresh; absence-proven) + pairing

- L1 graphs: `2026093401..06` (6 fresh).
- L2 graphs: `2026093501..06` (6 fresh).
- Blocks: `2026093601..12` (12 fresh paired block seeds, sampled with the
  accepted D8–D12 block helper from the CAL-only Model-F artifact only).
- Absence proof (this call): content search for `20260934|20260935|20260936|
  20260937|v72p2d14_discriminator` over the repo returns no files; direct read
  of the frozen root path returns `File not found`. These ranges sit outside all
  used ranges (D11: 2026092401..2906; D12: 2026093001..3312); no reuse, no seed
  search.
- Pairing: L1-graph-i pairs with L2-graph-i (i=1..6); each pair × 12 blocks =
  72 cells. The same 12 blocks feed L045-L1, L055-L1, L2-APP, and L2-ORACLE
  (fully paired; L045/L055 discordances computed paired per D12).

## 6. Frozen call list (exact; total 288 decoder calls)

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
  blocks per graph — only large enough to route the next investment (§7).

## 7. Preregistered thresholds (decision rule for L1-vs-L2 routing; priority order)

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
   D7-H NOT revived — see §10).
5. `L1-ADEQUATE` AND `L2-JOINT-GOOD` → **`N_ROUTE_SCALE_VALIDATION`** (both
   layers adequate at the calibrated rate; next step is a separately
   preregistered scale/validation packet, still no auto execution).
6. Else → `N_ROUTE_AMBIGUOUS` (no investment claim; escalate to planner).

## 8. Frozen root, command, budgets

- Frozen fresh root: `workspace/v72p2d14_discriminator/20260914_r1/`
  (proven absent §5; never overwritten; six-file shape mirroring D11/D12:
  `command_log`, `decoder_records`, `graph_records`, `arm_summary`, `manifest`,
  `summary`; future `batch_id == d14-discriminator-v1`, verifier rejects all else).
- Frozen exact command (unauthorized; the runner belongs to a later authorized
  change reusing the D11/D12 runners per VR-N-03 — no N code under this change):

```text
.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/v72p2d14_discriminator/20260914_r1
```

- The future runner SHALL: default `--execution-authorized` false with refusal
  before root creation/decoder binding/Model-F load; offer `--profile-only`
  (all 12 graphs A1–A6 + 288-identity plan + root-absent proof, zero decoder
  calls) and `--verify` (read-only fail-closed recomputation) paths.
- Frozen budgets (within proposal N ceilings: 120 s/call, ≤3600 s, <2 GiB,
  ≤720 calls, D10–D12 class): ≤288 decoder calls; ≤26 setup units; ≤1800 s wall
  total; ≤120 s per call; RSS <2147483648 B; one process; CPU-only; no
  retry/resume/repair/seed search/tuning. Ceiling breach → STOP as out-of-scope,
  re-scope, never tune.

## 9. Claim ceiling

Synthetic diagnostic only. This packet routes the next investment (L1
construction vs L2 degree design) and makes no FER, leakage, SKR, real-data,
qualification, promotion, optimality, or route-closure claim. It grants no
execution.

## 10. D7-H (no auto revival; reconsideration conditions only)

D7-H is NOT revived by this packet. Per packet §7 it may be reconsidered only
after calibrated single-layer AND forward baselines show that alternating
transfer addresses the remaining bottleneck. This batch contributes ONE such
baseline pair and is alone insufficient — even a `N_TRANSFER_BOTTLENECK_RECORDED`
terminal only records the question and returns to the planner.

## 11. Terminal

`READY_AWAITING_EXPLICIT_AUTHORIZATION` — root absent, unauthorized, execution
false. Next: N2 independent review, then the final review (§VR-S-03: any FAIL
blocks its phase).
