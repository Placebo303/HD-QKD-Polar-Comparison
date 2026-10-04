# Spec: formal-nonbinary-ldpc-v5-multistage-ir

## Requirements

### R1: Sequenced routes with stop-on-success

The change SHALL define four ordered routes — A (three-level 40→48→56 IR on
the v3-derived 56-row mother), B (redesigned nested-prefix mother code), C
(improved FFT-QSPA / EMS decoders), D (list/ADMM post-processing) — each an
independent synthetic qualification.  Route A SHALL run unconditionally;
routes B, C, D SHALL run only when every earlier route is non-promoted.  The
change SHALL stop at the first promoted route and SHALL NOT run later routes
after a promotion.  If all four routes are non-promoted, the change SHALL
terminate with four immutable non-promoted packages.

### R2: Route A — 56-row mother and three-level IR

`nbldpc_formal_v5a_multistage` SHALL reconstruct the exact v3 `NBLDPC3`
48-row codebook and append one deterministic 8-row extension block
(mask 0..7, frozen shifts, frozen coefficient salt) to form a 56-row mother
with ordered prefixes 32/40/48/56.  The 56-row and 48-row matrices SHALL have
full GF(1024) rank, zero four-cycles, minimum column degree >= 2, and pass the
pair-proxy check.  Canonical bytes, manifest, and a reconstruction verifier
SHALL be frozen before any development data exists.

Policies SHALL be exactly:
- `nbldpc_v5a_ir56` (candidate): p=.20 two-level 32→40, p=.30 three-level
  40→48→56, warm state retention across every extension;
- `nbldpc_v5a_ir48` (control): p=.20 two-level 32→40, p=.30 two-level 40→48,
  warm retention — equivalent v4 behavior under the v5a identity.

Each stage SHALL run at most 12 complete ascending-row layered FFT-QSPA
iterations (lambda .75).  A stage SHALL extend only after `decode_failed` or
`syndrome_consistent` followed by a failed independent 64-bit Toeplitz tag.
Warm extension SHALL retain ordered old edge messages, initialize new-row
messages uniformly, and reconstruct every belief from the Bob prior times all
active messages.  No Alice truth, serialized state, or third extension exists.
Control SHALL never extend.

### R3: Route B — nested-prefix mother redesign

`nbldpc_formal_v5b_mother` SHALL use a deterministic 56-row mother code with
nested ordered prefixes 40/48/56 (and 32 for the p=.20 stratum), constructed
by a frozen search domain and selected by a frozen structural proxy aimed at
the p=.30 tail distance spectrum (full GF(1024) rank at every prefix, zero
four-cycles, minimum degree >= 2, pair-proxy, and a low-weight-syndrome
collision score).  The search domain, proxy, tie-break rule, canonical bytes,
manifest, and verifier SHALL be frozen before any development data exists.
The route SHALL reuse the Route-A policy structure (ir56 candidate, ir48
control) against this mother.

### R4: Route C — stronger bounded decoders

`nbldpc_formal_v5c_decoder` SHALL compare, inside the three-level IR
framework and on one frozen 56-row codebook (Route B's mother if B exists and
is non-promoted, otherwise Route A's), exactly two pre-registered decoder
policies:
- log-domain FFT-QSPA with a fixed damping schedule;
- EMS with truncated nm-symbol messages (nm frozen) and bounded complexity.
Both SHALL keep the public-input-only boundary, deterministic iteration caps,
and exact syndrome-consistency semantics.  The codebook identity SHALL be
frozen in the route plan before any development data exists.

### R5: Route D — bounded list/ADMM post-processing

`nbldpc_formal_v5d_post` SHALL apply post-processing only to frames left
`decode_failed` by the best frozen decoder and frozen codebook.  Post-
processing SHALL be: (1) bounded list search over the top-K belief-symbol
candidates (K frozen, at most one list round), each candidate checked against
the already-disclosed syndrome; then (2) if no list candidate is
syndrome-consistent, one bounded GF(q) ADMM/proximal run (frozen iteration
cap).  Any syndrome-consistent candidate SHALL then go through the ordinary
locked Toeplitz verification.  Post-processing SHALL add no syndrome
disclosure and SHALL respect the frozen verification-attempt cap.

### R6: Fresh isolated data per route

Every route SHALL use its own fixed PCG64 development/confirmation roots
(64 development frames per stratum, 128 confirmation frames per stratum) and
SHALL prove zero overlap of roots, frame IDs, array hashes, atomic keys, and
Toeplitz seed IDs against all locally discoverable formal evidence.  The plan
SHALL bind development seeds only.  Confirmation material SHALL remain
wholly unmaterialized until the route reaches readiness (63/64 in both
development strata); after readiness the selected policy's complete
confirmation material SHALL be atomically created, freshness-checked, and
frozen before the first confirmation decode.  A route's confirmation data
SHALL NOT be used to select, tune, or modify any policy.

### R7: Promotion, artifacts, replay, stop boundary

Each route SHALL be planned once, executed at most once, and strictly
read-only replayed at most once, producing the v4 eight artifacts under a
route-specific run ID.  Promotion SHALL require 128/128 verified successes
independently at p=.20 and p=.30, full denominators, zero prohibited
failures, exact leakage/transcript reconstruction, complete hash DAG, and
strict replay.  The claim SHALL be zero observed failures in the registered
samples and SHALL NOT state FER=0.

No formal artifact or transcript SHALL contain residual counts/indices,
posterior summaries, messages, cycle indicators, decision hashes, Alice
truth, error locations, or decoded candidate lists.  Wall time SHALL be
monitoring-only.  Deterministic caps (workers, checks <= 56, row weight <= 8,
stage iterations <= 12, decoder stages <= 3, verification attempts <= 3,
dense message bytes) SHALL bound every route; an interrupted execution SHALL
remain incomplete/invalid.  Non-promotion of a route SHALL forbid its rerun
or tuning and SHALL leave N4, sidecars, `.ttbin`, real-data claims, and
comparison claims locked.

## Behavior

The qualification lifecycle per route: create one no-overwrite plan that
embeds the frozen codebook identity, policies, roots, caps, seeds, freshness
proof, and provenance; review the plan without decoding; execute once;
invoke strict read-only replay once.  Development runs every policy on all
128 development frames; selection ranks eligible policies lexicographically
(negative minimum per-stratum successes, negative total successes,
key-dependent disclosure, public-control bits, interaction rounds, decoder
iterations, policy SHA256); readiness stops the route at 63/64 or better in
both strata without confirmation.  Promotion requires the confirmation gate
and terminal `promoted=true`; otherwise `promoted=false` with all failures
retained `decode_failed` (or the allowed whitelist statuses) and zero
prohibited statuses.

## Acceptance Criteria

- A1: The four routes are pre-registered with frozen identities, data roots,
  policies, caps, and gates; later routes execute only on earlier
  non-promotion; the change stops at the first promotion.
- A2: Route A's 56-row mother reconstructs v3 rows 0..47 exactly, appends the
  frozen 8-row block, and every prefix 32/40/48/56 satisfies the frozen
  structural contract; ir56 uses three levels at p=.30 and two at p=.20; ir48
  never extends.
- A3: Route B's mother is selected by the frozen proxy within the frozen
  search domain; its canonical identity and verifier are immutable.
- A4: Route C compares exactly the two frozen decoder policies on one frozen
  codebook; complexity and iteration bounds hold; no truth or oracle enters.
- A5: Route D's list and ADMM stages are bounded, add no syndrome disclosure,
  and every candidate passes the locked tag before success.
- A6: Every executed route proves identity/seed freshness, runs plan/execute/
  replay at most once each, reports `promoted` consistently with the frozen
  128/128 gate, and keeps all artifacts free of forbidden diagnostics.
- A7: Non-promoted routes are immutable; no rerun, confirmation tuning, N4,
  sidecar, `.ttbin`, real-data, or comparison claim is made from them.
