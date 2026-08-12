# V7 Successor Ladder Report — All Routes Non-Ready (`ladder_exhausted`)

- **Change**: `formal-nonbinary-ldpc-v7-successor-ladder`
- **Date**: 2026-08-04
- **HEAD**: `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344` (no commits during the
  ladder; all route artifacts are untracked files or `workspace/` packages)

## Frozen Ladder Rules

- Ordered route ladder: **R1A -> R1B -> R2 -> R3**; one route at a time; stop
  at the first development-ready route.
- Per route: engineering T0-T3 + independent acceptance, then one **sacrificed
  4+4 canary** (plan -> read-only review -> execute exactly once -> strict
  read-only replay exactly once).
- Canary gate: **0/4 verified success in either stratum** -> `failed_canary`
  -> freeze the route and advance. Otherwise 16+16 sacrificed development ->
  readiness gate (**>=15/16 per stratum, zero forbidden statuses, strict
  replay, disclosure <=8.75 bits/symbol excluding the tag, median <=120
  s/frame**) -> stop at first ready.
- No rerun, no tuning, no confirmation, no real data, no N4, no official
  `comparison_bench/outputs_comparison/formal_ir_methods/` v7 output root.

## Route Table

| Route | Identity | Engineering tiers + acceptance | Canary per-stratum verified success | Gate result | Key evidence files | Package location |
|---|---|---|---|---|---|---|
| R1A | `nbldpc_formal_v7_r1a_mr0` — GF(1024) n=256 (2,3) mother, m=170, flooding FFT-QSPA | T0 19 / T1 64 / T2 11 / T3 97 — ACCEPTED | 0.20: 0/4, 0.30: 0/4 | `failed_canary` (0/4 both strata), frozen | `v7_r1a_engineering_acceptance.json`, `v7_r1a_canary_plan_evidence.json`, `v7_r1a_canary_execution_addendum.json` | `workspace/nbldpc_v7_r1a_canary_af8ff2e751cf433ba74deb74bbe1deba/canary_plan` |
| R1B | `nbldpc_formal_v7_r1b_mr1` — one multiplicative repetition of the R1A mother (rate 1/6) | T0 15 / T1 76 / T2 17 / T3 119 — ACCEPTED | 0.20: 3/4, 0.30: 0/4 | `failed_canary` (p=.30 tail 0/4), frozen | `v7_r1b_engineering_acceptance.json`, `v7_r1b_canary_plan_evidence.json`, `v7_r1b_canary_execution_addendum.json` | `workspace/nbldpc_v7_r1b_canary_a209a853f5e34de69bf930deb60d5673/canary_plan` |
| R2 | `nbldpc_formal_v7_r2_qsc_de` — QSC density-evolution ensemble, n=1024, checks 321/458, DE validated vs published BSC/BEC vectors | T0 32 / T1 100 / T2 24 / T3 142 — ACCEPTED | 0.20: 0/4, 0.30: 0/4 | `failed_canary` (0/4 both strata), frozen | `v7_r2_engineering_acceptance.json`, `v7_r2_canary_plan_evidence.json`, `v7_r2_canary_execution_addendum.json` | `workspace/nbldpc_v7_r2_canary_d6c752a0772043768a1ca88a1ca63ed3/canary_plan` |
| R3 | `nbldpc_formal_v7_r3_gf32x2` — GF(32)xGF(32) two-layer EMS nm=32 (exact min-sum), reversible 10-bit split, layer-0-first with conditional layer-1 priors, m0=m1=404/558 | T0 19 / T1 105 / T2 33 / T3 179 — ACCEPTED (10/10 independent review PASS) | 0.20: 0/4, 0.30: 0/4 | `failed_canary` (0/4 both strata), frozen | `v7_r3_engineering_acceptance.json`, `v7_r3_canary_plan_evidence.json`, `v7_r3_canary_execution_addendum.json` | `workspace/nbldpc_v7_r3_canary_d006ec637ecb4b1e9463a7f4462eebf3/canary_plan` |

## Per-Route Records

### R1A — `nbldpc_formal_v7_r1a_mr0` (mother, rate ~1/3)

GF(1024) n=256 deterministic (2,3) PEG mother with m=170 checks
(168 degree-3 + 2 degree-4, syndrome 1700 bits), flooding FFT-QSPA primary,
max_iter 100. Engineering accepted: T0 19 / T1 64 / T2 11 / T3 97, independent
review 7/7 PASS with 3 non-blocking notes. Sacrificed 4+4 canary executed
exactly once (exit 0, 111.0 s) and strict-replayed exactly once (exit 0,
108.8 s): per-stratum verified success {0.20: 0, 0.30: 0}, 8/8
`decode_failed` at max_iter=100, zero forbidden statuses, verification never
invoked. Canary gate FIRES on both strata -> `failed_canary`; 16+16
development not eligible; route frozen.

### R1B — `nbldpc_formal_v7_r1b_mr1` (one multiplicative repetition, rate 1/6)

Exact R1A mother under a new identity plus one multiplicative repetition per
variable with deterministic nonzero GF(1024) multipliers, prior-combining
decoder, same 1700-bit syndrome + 64-bit tag. Engineering accepted: T0 15 /
T1 76 / T2 17 / T3 119. Sacrificed 4+4 canary executed exactly once (exit 0,
59.3 s) and strict-replayed exactly once (exit 0, 59.6 s): per-stratum
verified success {0.20: 3, 0.30: 0}, 5 `decode_failed` at max_iter=100 (3
`verified_success` in p=.20), zero forbidden statuses. Multiplicative
repetition improved p=.20 (3/4 vs R1A 0/4) but did not close the p=.30 tail.
Canary gate FIRES on p=.30 -> `failed_canary`; 16+16 development not eligible;
route frozen.

### R2 — `nbldpc_formal_v7_r2_qsc_de` (QSC density-evolution ensemble)

q-ary density evolution validated independently against published vectors
(q=2 BSC (3,6) ~0.084; BEC (3,6)=0.429438, (3,4)=0.647426, (4,8)=0.383441,
(4,6)=0.506132; q=4 exhaustive checks), bounded search <=32 candidate
distributions (degrees 2..8, mean check degree <=12), per-stratum n=1024 PEG
codebooks with 321 (p=.20) / 458 (p=.30) checks, layered FFT-QSPA max_iter
100. One frozen-vector correction recorded ((3,4) mislabel). Engineering
accepted: T0 32 / T1 100 / T2 24 / T3 142. Sacrificed 4+4 canary executed
exactly once (exit 0, 1311.2 s ~21.9 min) and strict-replayed exactly once
(exit 0, 1308.5 s): per-stratum verified success {0.20: 0, 0.30: 0}, 8/8
`decode_failed` at max_iter=100, zero forbidden statuses, verification never
invoked. Canary gate FIRES on both strata -> `failed_canary`; 16+16
development not eligible; route frozen.

### R3 — `nbldpc_formal_v7_r3_gf32x2` (GF(32)xGF(32) multilevel)

Each natural GF(1024) symbol reversibly split into high/low 5-bit words
(exhaustively round-tripped, split roundtrip SHA256
`4716bf82...`); two GF(32) n=1024 codes with m0=m1=404/558 checks (syndrome
2020/2790 bits per layer, 4040/5580 bits total; per-symbol key-dependent
disclosure excluding the tag 3.945 / 5.449 bits, both below the frozen 8.75
ceiling); layer-0 decoded first with layer-1 priors formed ONLY from
Bob/public/verified layer-0 output; joint 64-bit Toeplitz tag; two-layer
flooding damped EMS nm=32 (=q, the EXACT min-sum GF(32) check update,
validated exhaustively), max_iter 100, no fallback, FFT-QSPA oracle test-only.
Engineering accepted: T0 19 / T1 105 / T2 33 / T3 179, independent review
10/10 PASS. Canary plan staged and read-only reviewed
READY-FOR-SINGLE-EXECUTION; a minimal canary-only authorization edit applied
(run() + CLI + 2 tests; post-edit source hashes
`dd8ebe41...`/`68a17e92...`/`ad603eab...`); plan re-created in the same
directory with fresh 10303-bit seed records (file SHA256
`43379354...fca2`). Sacrificed 4+4 canary executed exactly once (exit 0,
668.8 s) and strict-replayed exactly once (exit 0, 663.4 s): per-stratum
verified success {0.20: 0, 0.30: 0}, 8/8 `decode_failed` at max_iter=100
(layer-0 failed on every frame), zero forbidden statuses, verification never
invoked, 24 transcript events (3/frame). Canary gate FIRES on both strata ->
`failed_canary`; route frozen. The 16+16 development eligibility was not
claimed; per the frozen rule the canary gate must not fire for eligibility.

## Ladder Conclusion

- **First development-ready route**: NONE.
- **`ladder_exhausted`**: TRUE — all four routes (R1A, R1B, R2, R3) are
  `failed_canary`; no route reached the 16+16 development stage or the
  readiness gate.
- **Artifact retention**: every failed canary package is frozen immutably at
  its `workspace/nbldpc_v7_r1a/r1b/r2/r3_canary_*/canary_plan` root; every
  engineering acceptance JSON, canary plan evidence JSON, and canary execution
  addendum is retained under this change's `evidence/` directory.
- **Output boundary**: no official
  `comparison_bench/outputs_comparison/formal_ir_methods/` v7 directory exists
  before or after any route (recursive v7 scans clean).
- **No rerun / tuning / confirmation / real data**: every canary executed
  exactly once and strict-replayed exactly once; no reruns, no tuning, no
  confirmation material, no real data, no N4, no sidecar access.
- **Disclosure ceilings**: all routes' canary plans were development-role only
  (0 confirmation frames) with per-symbol disclosure below the frozen
  ceiling where measurable (R2 3.135/4.473, R3 3.945/5.449 bits/symbol
  excluding the tag).
- **Forbidden-status scans**: clean across all routes — only `decode_failed`
  (and `verified_success` for the 3 R1B p=.20 frames) observed; zero forbidden
  statuses (decoder_error, codebook_invalid, invalid_input,
  unsupported_domain, aborted_resource_limit, verify_failed) in any route.

## Stop Statement

- No fourth route is invented, and R4 (proximal-ADMM) was never authorized in
  this ladder.
- Any successor must be a **NEW OpenSpec change** with fresh development and
  confirmation data, new roots, and its code/rate/decoder change frozen before
  new development data.
- The current canary/confirmation rows are **not tuning data**; they are
  immutable non-ready evidence.
- Qualification, promotion, and comparison eligibility claims remain
  unauthorized for every v7 route.
