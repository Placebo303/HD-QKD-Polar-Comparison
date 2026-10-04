## Historical implemented scope — formal-nonbinary-ldpc-v5-multistage-ir

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md -->

### R1: Sequenced routes with stop-on-success

The change SHALL define four ordered routes — A (three-level 40→48→56 IR on
the v3-derived 56-row mother), B (redesigned nested-prefix mother code), C
(improved FFT-QSPA / EMS decoders), D (list/ADMM post-processing) — each an
independent synthetic qualification.  Route A SHALL run unconditionally;
routes B, C, D SHALL run only when every earlier route is non-promoted.  The
change SHALL stop at the first promoted route and SHALL NOT run later routes
after a promotion.  If all four routes are non-promoted, the change SHALL
terminate with four immutable non-promoted packages.

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md -->

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

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md -->

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
