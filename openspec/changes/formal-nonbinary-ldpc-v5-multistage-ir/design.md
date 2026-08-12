# Design: formal-nonbinary-ldpc-v5-multistage-ir

## Overview

v4 left eight p=.30 confirmation frames `decode_failed` after a single 40→48
extension.  This change pre-registers four independent synthetic
qualification routes — A (three-level 40→48→56 IR), B (nested-prefix mother
redesign), C (stronger bounded decoders), D (list/ADMM post-processing) —
executed strictly in order, stopping at the first promotion.  Every route
reuses the v4 qualification machinery shape: one plan, one execution, one
strict read-only replay, eight artifacts, identity/seed freshness, readiness
63/64 per stratum, promotion 128/128 per stratum, diagnostic exclusion, and
no-overwrite immutability.

## Goals

1. Earn synthetic promotion for a nonbinary LDPC method (128/128 at p=.20 and
   p=.30) using only fresh pre-registered data.
2. Attribute the p=.30 tail gap to a concrete, bounded improvement (more
   redundancy levels; better mother code; stronger decoder; post-processing).
3. Keep every route immutable, replayable, and free of oracles, truth, or
   confirmation-driven tuning.

## Constraints

- v1-v4 sources, plans, data, policies, results, seeds, and artifacts are
  frozen; v5 is additive only.
- No external decoder/codebook dependency.  q=1024, n=64, GF(1024)
  polynomial-basis field, MSB-first syndrome/tag mapping, 703-bit Toeplitz
  seeds, 64-bit tags, two-bit stage decisions (00 accept / 01 extend /
  10 reject; 11 reserved) — unchanged from v4.
- Deterministic caps per route: workers 1, checks <= 56, row weight <= 8,
  stage iterations <= 12, decoder stages <= 3, verification attempts <= 3,
  dense message storage <= 24 MiB.  Wall time is monitoring-only.
- Route sequence and stop rules are frozen (R1): B/C/D run only when every
  earlier route is non-promoted; the change stops at the first promotion.
- N4, sidecars, `.ttbin`, real-data and comparison claims remain locked.

## Technical Approach

### 0. Shared qualification runtime

A new parameterized runtime `formal_ir/nonbinary_v5_runtime.py` hosts the
plan/execute/replay/verification engine that v4 proved: canonical plan
schema, PCG64 frame generation, identity overlap proof, development seed
binding, conditional confirmation materialization, selection ranking, eight
artifacts, provenance, forbidden-diagnostic scans, and strict read-only
replay.  Each route passes its own frozen configuration: run ID, method ID,
roots, caps, codebook builder, policy list, prefix ladder, verification
attempt cap, and epsilon policy.  Route cores (`nonbinary_v5a_multistage.py`,
`nonbinary_v5b_mother.py`, `nonbinary_v5c_decoders.py`,
`nonbinary_v5d_post.py`) stay pure in-memory and public-input-only, matching
the v4 core/qualification split.  The runtime is a new module; v4 modules are
not modified.

### 1. Route A — 56-row mother and three-level IR (`nbldpc_formal_v5a_multistage`)

**Mother code (NBLDPC5A).**  Rows 0..47 are the exact frozen v3 `NBLDPC3`
rows (same masks, shifts, coefficient salt, coefficient derivation).  Rows
48..55 are one new 8-row extension block with:

- block `a=6`, `mask6 = (0,1,2,3,4,5)` (6 edges, row weight 6 <= 8);
- shifts `s6 = (s6[0..7])` with `s6[6], s6[7]` defined (needed by the
  v3 blocks a=1,2 whose masks include columns 6,7);
- coefficients `1 + SHA256(ASCII("NBLDPC5A|coef|{salt}|{row}|{col}")) mod 1023`.

Frozen search (deterministic, bounded, run once at build time; results are
recorded in the canonical manifest and never re-searched):

1. Enumerate `s6` lexicographically over `(Z/8)^8`; accept the first tuple
   satisfying the disjoint-shift-difference condition against every v3 block
   `a` with `mask_a`: `{s6[b] - s_a[b] mod 8 : b in mask_a}` has all distinct
   values (for each `a` in 0..5).  This condition is exactly what keeps every
   pair of rows sharing at most one column position, so the 56-row matrix
   still has **zero four-cycles** (verified again by the structural checker).
2. Fix that `s6*`; enumerate `salt` from 0 upward; accept the first salt such
   that the 56-row matrix has GF(1024) rank 56 and passes the pair-proxy
   check.  (The 48-row prefix keeps v3's rank 48 automatically.)

Canonical `NBLDPC5A` bytes: magic + compact header (v3 construction
reference, `mask6`, `s6*`, `salt*`, coefficient derivation, field spec,
prefixes 32/40/48/56) + all 56 rows as 16-bit big-endian GF(1024) symbols.
Manifest records per-prefix rank/cycle/degree/pair-proxy plus
`canonical_sha256`; a verifier reconstructs everything deterministically and
fails closed on mismatch.  The codebook module also serves as the frozen
reference for Route C if Route B is never promoted.

**State machine (warm, three levels).**  Prefix ladder: p=.20 `32→40`
(two levels), p=.30 `40→48→56` (three levels).  Each stage runs at most 12
complete ascending-row layered FFT-QSPA iterations (lambda .75), then:
`syndrome_consistent` -> locked 64-bit Toeplitz verification; success
terminates `verified_success`; a failed tag with an unused extension level
triggers warm extension; `decode_failed` with an unused level triggers warm
extension; any integrity/input/codebook/resource status terminates without
retry.  Warm extension keeps ordered old edge messages, initializes new-row
messages uniform, reconstructs every belief from the Bob prior times all
active messages, recomputes every extrinsic, and scans the complete active
graph.  Only the last level ends in accept/reject without extension.

**Policies.**

- `nbldpc_v5a_ir56` (candidate): p=.20 two-level 32→40, p=.30 three-level
  40→48→56, warm retention; at most 3 verification attempts per frame.
- `nbldpc_v5a_ir48` (control): p=.20 two-level 32→40, p=.30 two-level 40→48,
  warm retention; at most 2 verification attempts — v4-equivalent behavior
  under the v5a identity and fresh data, providing the same-data baseline.

**Accounting.**  Initial syndrome 320 (p=.20) / 400 (p=.30) key-dependent
bits; each 8-row extension 80 bits; each emitted tag 64 key-dependent bits;
each 703-bit seed and each 2-bit decision public control.  A failed tag stays
charged.  `outcome_epsilon_ec = 2^-64` for an accepting tag; registered
per-frame `protocol_epsilon_ec_bound = 2^-63` for ir48 and `2^-62` for ir56
(union bound over at most 2 / 3 independent attempts).

**Data roots (v5a).**  development p=.20 `202607720000`, p=.30
`202607730000`; confirmation p=.20 `202607740000`, p=.30 `202607750000`.
64 development frames per stratum, 128 confirmation frames per stratum;
frame generation order pinned as in v4 (Alice integers, error mask, nonzero
error, masked XOR).  Run ID `20260731_v5a_nbldpc_multistage_synthetic`.

### 2. Route B — nested-prefix mother redesign (`nbldpc_formal_v5b_mother`)

**Search domain (frozen).**  A 56-row mother with **7 blocks x 8 rows** and
nested prefixes 32/40/48/56.  Block masks are frozen templates
`((0,1,2,3,4,5), (0,1,2,3,6,7), (0,1,4,5,6,7), (0,2,4,6), (1,3,5,7),
(0,1,2,3,4,5), (0,2,4,6))` (row weights 6,6,6,4,4,6,4 — no full-column
block).  For each block `a` in order, its 8 shifts are enumerated
lexicographically over `(Z/8)^8`; the first tuple is accepted whose
disjoint-shift-difference condition holds against every already-fixed block
(keeping zero four-cycles for every prefix).  Coefficients use
`1 + SHA256(ASCII("NBLDPC5B|coef|{salt}|{a}|{b}")) mod 1023`; `salt` is
enumerated from 0 and the first salt whose every prefix 32/40/48/56 has full
GF(1024) rank and passes pair-proxy is accepted.

**Distance-spectrum proxy (frozen).**  For the accepted (shifts, salt)
candidate, compute exact low-weight syndrome collision counts: weight-2
(`C(64,2) = 2016` column pairs) and weight-3 (`C(64,3) = 41664` triples)
over the 56-row matrix.  If the first accepted candidate is not the unique
minimum of `(w2_collisions, w3_collisions)` among the first `K=8` acceptable
(salt, shifts) candidates, the minimal one is selected; ties break by the
smallest `construction_seed`.  The proxy targets the p=.30 tail by preferring
mothers with fewer short-weight codewords.

Canonical `NBLDPC5B` bytes/manifest/verifier mirror NBLDPC5A with its own
magic, templates, accepted shifts/salt, proxy scores, and
`canonical_sha256`.  Route B reuses the Route-A policy structure (ir56 /
ir48) and the identical three-level warm state machine, with its own run ID
`20260731_v5b_nbldpc_mother_synthetic` and roots development
`202607760000`/`202607770000`, confirmation `202607780000`/`202607790000`.
If Route B is promoted, Route C is not run.

### 3. Route C — stronger bounded decoders (`nbldpc_formal_v5c_decoder`)

Frozen on one 56-row codebook: Route B's `NBLDPC5B` if Route B ran and is
non-promoted, otherwise Route A's `NBLDPC5A` (the choice is fixed when the
Route C plan is frozen, before any Route C data).  Two decoder policies,
both inside the three-level IR framework (p=.20 32→40, p=.30 40→48→56, warm
retention):

- `nbldpc_v5c_sched` — probability-domain FFT-QSPA with a frozen damping
  schedule per 12-iteration stage: lambda `0.5` for iterations 1..4, `0.75`
  for 5..8, `0.90` for 9..12 (applies at every stage; deterministic, no
  oracle).
- `nbldpc_v5c_ems` — LLR-domain EMS with truncated `nm=64`-symbol messages,
  min-sum check updates with the frozen correction factor `alpha=0.8`, and
  the same per-stage iteration cap; messages sorted deterministically;
  syndrome-consistency checked on the decoded hard vector as usual.

Both keep public-input-only signatures, the exact `syndrome_consistent`
semantics, the same verification/tag/decision accounting, and the
`protocol_epsilon_ec_bound = 2^-62` (three attempts).  A pure in-memory
equivalence test proves `nbldpc_v5c_sched` with the constant lambda .75
matches v4 warm behavior on identical inputs.  Run ID
`20260731_v5c_nbldpc_decoder_synthetic`; roots development
`202607800000`/`202607810000`, confirmation `202607820000`/`202607830000`.

### 4. Route D — bounded list/ADMM post-processing (`nbldpc_formal_v5d_post`)

Frozen on the best previous outcome: the Route-C promoted policy if C was
promoted (change stops there, so D is never run); otherwise the best
non-promoted decoder/codebook from A/B/C as fixed at Route D plan freeze —
concretely the FFT-QSPA or scheduled decoder on the frozen 56-row codebook,
three-level IR.  Post-processing applies only to frames ending `decode_failed`
after the last stage:

1. **List stage (one round, bounded).**  From the final-stage beliefs, rank
   the 64 variables by belief uncertainty (difference between top two
   probabilities) and take the `L=2` least certain variables; form the `8^2=64`
   candidate vectors by replacing those two symbols with their top-8
   belief symbols (including the argmax baseline), check each against the
   already-disclosed syndrome; the first syndrome-consistent candidate is
   submitted to the locked Toeplitz verification (subject to the
   verification-attempt cap).
2. **ADMM stage (one run, bounded).**  If no list candidate is
   syndrome-consistent, run one deterministic GF(q) ADMM/proximal decoder:
   symbol-indicator relaxation with check-polytope alternating projections,
   fixed `rho=1.0`, at most `50` iterations, deterministic initial point from
   the final-stage priors; a syndrome-consistent output is submitted to the
   locked verification.

Post-processing adds **no syndrome disclosure** (syndrome is already public);
leakage accounting charges only tags/seeds/decisions exactly as in the other
routes.  Belief rankings and candidate indices are transient and excluded
from all artifacts.  Run ID `20260731_v5d_nbldpc_post_synthetic`; roots
development `202607840000`/`202607850000`, confirmation
`202607860000`/`202607870000`.

### 5. Freshness, gates, artifacts (all routes)

- Route plan binds development seeds only: one record per frame per policy
  stage slot actually reachable (ir48: 2 slots; ir56/sched/ems: 3 slots);
  unused slots stay explicitly unused.  Confirmation material is
  unmaterialized until readiness.
- Identity overlap proof covers roots, frame IDs, array SHA256, atomic keys,
  and Toeplitz seed IDs against every discoverable plan/policy manifest under
  `comparison_bench/outputs_comparison/formal_ir_methods/` (excluding the
  plan's own directory).
- Selection ranking (eligible policies only): negative minimum per-stratum
  verified successes, negative total successes, total key-dependent
  disclosure, total public-control bits, total interaction rounds
  (stage-decision count), total decoder iterations, policy SHA256.
- Readiness = 63/64 or better independently in both strata; otherwise the
  route stops `non_promoted_development` without confirmation.
- Promotion = 128/128 independently in both strata, full denominators, zero
  prohibited statuses (whitelist only `verified_success`, `verify_failed`,
  `decode_failed`, `aborted_resource_limit`), exact accounting/transcript
  reconstruction, complete hash DAG, strict read-only replay.  Claim wording:
  zero observed failures in the registered samples; never FER=0.
- Probe before each route's plan: fixed non-qualification seed
  `202607719999` (route A), p=.30, production first stage plus forced warm
  extensions through the highest prefix; records operational timing and
  deterministic work/memory facts only; cannot tune any frozen value.

## Alternatives Considered

- **Rerun v4 with more iterations**: rejected — v4 is frozen, and iteration
  scaling is exactly what the user ruled out ("而非只增加迭代次数").
- **Single change with free-form tuning**: rejected — violates the
  pre-registration and immutable-evidence rules; each route is a sealed
  experiment.
- **8-column extension block for Route A**: rejected — a full-column block
  would share >= 2 columns with the v3 all-column block and force nonzero
  four-cycle counts; the 6-column mask with disjoint shift differences
  preserves zero four-cycles exactly.
- **True log-domain FFT-QSPA**: rejected as not well-defined (FWHT is not
  linear over logs); replaced by the fixed-schedule FFT-QSPA and EMS, which
  are the two real, bounded alternatives.
- **External EMS/ADMM libraries**: rejected — no new dependencies; bounded
  pure-Python implementations keep the evidence self-contained.

## Impacted Files / Modules

- Add `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5_runtime.py`
  (shared plan/execute/replay engine).
- Add `nonbinary_v5a_codebook.py` (NBLDPC5A), `nonbinary_v5a_multistage.py`
  (core), Route A qualification wrapper, CLI
  `cli/run_formal_nonbinary_v5a_qualification.py`, tests.
- Add `nonbinary_v5b_mother.py` (NBLDPC5B search), Route B wrapper/CLI/tests.
- Add `nonbinary_v5c_decoders.py`, Route C wrapper/CLI/tests.
- Add `nonbinary_v5d_post.py`, Route D wrapper/CLI/tests.
- Documentation: `AGENT_HANDOFF.md`, `CURRENT_TASK.md`, `docs/decision-log.md`,
  `AGENT_PROJECT_MEMORY.md` after each executed route.
- Frozen baseline `src/`, `experiments/`, `tools/`, `results/`, v1-v4
  sources/artifacts: untouched.

## Risks and Mitigations

- **Route A search cost**: shift enumeration is combinatorial but the
  disjoint-difference condition prunes early; salt search is expected to
  accept within the first few candidates (random 8 rows are almost surely
  independent over GF(1024)); total build time bounded and run once, with the
  accepted values frozen in the manifest.  Mitigation: search runs in the
  main-thread acceptance phase (T0), never inside qualification.
- **Route A may still miss 128/128** (8 extra checks may not close the tail):
  expected — that is why routes B/C/D exist; evidence stays immutable and
  diagnostic.
- **Route B search cost**: bounded by K=8 full-proxy candidates; w2/w3
  collision counts are computed once per acceptable candidate.
- **EMS numerical stability**: LLR-domain min-sum with correction factor is
  deterministic and bounded; the equivalence test pins the FFT-QSPA baseline.
- **ADMM complexity**: bounded to one run of 50 iterations per
  already-failing frame; implemented with plain NumPy; deterministic.
- **Engine parameterization risk**: the shared runtime is exercised by each
  route's T0-T3 suite (fake runners, tiny-math state transitions, layered
  tamper rejection, complete fake qualification and strict fake replay) before
  any real plan is created.
- **Run time**: Route A execution is expected in the 3,000-10,000 s range
  (v4 took 3,384 s for 384 outcomes); monitoring-only, with declared caps and
  no time-based status changes.
