# CURRENT_TASK.md

## Current Task

The active implementation change is
`openspec/changes/implement-formal-nonbinary-ldpc/`. Its N0 deterministic
GF(2^m) backend/preflight, N1 structural codebook, and N2 bounded FFT-QSPA
feasibility/accounting slices are complete.

## Scope

- Keep agent rules centralized in `AGENTS.md`
- Keep durable decisions in `docs/decision-log.md`
- Keep reusable failures and fixes in `docs/troubleshooting.md`
- Use `openspec/` for any substantial change
- Use `docs/openspec-phase0-reconciliation-20260725.md` as the current
  evidence/archival matrix for the five historical changes that remain active.
- Use the archived final selection record at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/` and its
  merged canonical spec before interpreting the bounded result.
- Use `openspec/changes/implement-formal-cascade-and-ldpc/` before changing
  comparison behavior: it upgrades only formal Cascade/LDPC candidates, not
  Polar or a three-method ranking.

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked
- If a request changes behavior, architecture, prompt rules, tool semantics, or workflow rules, create/update an OpenSpec change first

## Current Status

- `final-ir-method-selection` is archived; its merged canonical spec is
  `openspec/specs/final-ir-method-selection/spec.md`.
- The five historical IR changes have implementation/report artifacts, but all
  remain active because their Phase-0 evidence gaps are unresolved. See the
  reconciliation matrix for change-specific blockers.
- Cascade-lite remains the preferred executable non-Polar candidate;
  Layered LDPC remains a control baseline; qLDPC remains reference-only.
- Historical Polar imports are not frame-identical confirmation evidence.
- Phase 2 is locked at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`:
  d=1024, frame length 64, dataset raw SER [0.20, 0.30), with 60 tuning and
  60 confirmation frames from group-disjoint dataset IDs. Source and split
  hashes verify through `lock_final_ir_data --verify`.
- The original Phase-3 files in `20260725_v1/` are excluded from every
  decision; `invalid_run_notice.json` records the non-reviewed tuning grid.
  The Phase-2 lock files in that directory remain authoritative and read-only.
- The authoritative Phase-3 evidence is additive `20260725_v2/`, which uses
  the v1 lock manifest and exact same frames. It froze Cascade `[12,6,24,13]`,
  4 passes, seeded-random gray and LDPC parity 1.0, 50 iterations,
  bsc-estimated/uniform gray before confirmation. Confirmation retained all
  60 attempts per candidate: Cascade 60 verified successes; LDPC 59.
- Phase 4 audit is authoritative at `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v4_audit/`; v3 is superseded by its additive notice after a generic decision-branch repair.
  It verifies the 60 identical locked confirmation keys, frozen corrected-grid configurations, retained statuses and aggregate denominators, and recorded lock hashes. The exact two-sided paired p-value is 1.0 for the single Cascade-only success, so the required decision is `no_decision`, not a winner. Leakage remains method-specific and unranked. The non-numerical Route A field gate fails because the comparison schema lacks the documented universal-hash proof-interface fields.

## Next Step

Phase 5 code/doc hardening is complete: the data-lock selection unit test is
file-free, the authoritative lock and v4 audit have read-only verification
commands, and the Phase-3 runner requires a new output directory and records
its immutable pre-run plan before tuning. `python -m py_compile` passed for
the five new modules; focused unittest passed 7/7; and safe comparison pytest
passed 22/22 with `test_evidence_package.py` excluded because it still uses a
fixed tracked path. The external basetemp tore down normally in this pass.

The final completion audit and archive are complete for
`final-ir-method-selection`. Do not infer a winner: the authoritative v4 audit
remains `no_decision` at p=1 with a failing non-numerical Route A gate. Keep
the five historical IR changes active until their own written evidence gaps are
closed through separate work.

## Next Step

Formal shared-core Phases 1--2 are implemented in
`comparison_bench/src/comparison_bench/formal_ir/`: six-artifact/status
validation, pinned-LDPC fail-closed preflight, 64-pair provenance validation,
locked-seed Toeplitz verification, and canonical secrecy-checked transcripts.
`test_formal_verification.py` and `test_cascade_formal.py` passed 11/11;
no qualification outputs were created. Phase 3 now provides additive,
protocol-faithful `cascade_formal_v1` with fixed passes, cached look-back,
resource caps, locked Toeplitz verification, and secrecy-checked public
events. Next implement codebook-backed `ldpc_formal_v1`, then independent
synthetic and locked real-frame qualification. Existing lite results stay lite;
Polar and formal three-method comparison require a later change.

The reviewed OpenSpec now freezes the exact Toeplitz convention and locked
per-frame seeds; Cascade FIFO/re-entry state machine and caps; 64-symbol,
four-rate deterministic LDPC codebooks and pinned `ldpc==2.4.1` parameters;
calibration-only `p_hat`; six-artifact/status/provenance contracts; and exact
synthetic plus fresh `bw100`/`bw120` real promotion gates. The shared Phase
1--2 task items are checked; algorithm and qualification tasks remain open. A
method may finish as `non_promoted`, but lite cannot
substitute for it in a future formal Polar comparison.

Phase 4 is complete. `ldpc_formal_v1` now has deterministic manifest-backed
four-rate codebooks, sacrificed-calibration-only frozen `p_hat`/rate selection,
MSB-first syndrome reconciliation, the exact pinned serial BpOsd configuration,
syndrome consistency, locked Toeplitz verification, transcript-safe disclosure
accounting, and fail-closed status handling without fallback. The revised
constructor probe succeeds on installed `ldpc==2.4.1`; a real-backend
single-error frame completed as `verified_success`. Calibration provenance now
hashes the source plus dataset, ordered unique sacrificed frame keys, mapping,
and dimension; confirmation recomputes that hash and validates every per-plane
count, `p_hat`, and selected rate. The public runner exposes no decoder or
preflight test seam. Focused formal tests passed 18/18 and the safe comparison
suite excluding fixed-path `test_evidence_package.py` passed 40/40 with the
TemporaryDirectory-backed 40-codebook test enabled outside the Windows sandbox.
No qualification output had been generated at Phase-4 completion.

Formal synthetic v1 remains excluded as a partial pre-execution run. Synthetic
v2 is now also non-authoritative diagnostics: its declared Alice seed
`2026072501` and frame-order seed `2026072531` were unused, while undeclared
Alice seeds `2026072502..2505` generated its batches. Its observed Cascade/LDPC
counts therefore confer no promotion. Phase 5 checkboxes are reopened.

Formal synthetic Phase 5 is complete at additive
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
The immutable v3 package verified read-only with 128 outcomes: Cascade passed
both strata (32/32 at p=.01 and 32/32 at p=.02) and is synthetically
promoted; LDPC recorded 29/32 and 14/32 respectively and is synthetically
`non_promoted`. All 21 retained failures were `verify_failed`; there were no
unclassified/internal/provenance/accounting failures. This does not authorize
retuning, lite substitution, real qualification, Polar adaptation, or a
three-method ranking. Phase 6 remains the next gated work.

## Formal IR Phase 6--7 Verified Status

Phase 6 is complete for the only eligible real method. The invalid real v1
lock received only additive `invalid_lock_notice.json` (SHA256
`9f9d72f6c1e39467f08b86a514851b78a8aaf6a8ef2fb1f869b22f60e980d556`);
its original plan
`3fd15043dc6e43c0eb4365e5ebaf57990dfc917eff908ef26d3804cbcaea07ab`
and lock
`aec7ffa3cdcb471748e6c41920cfa82b9df1dc4745d85c4ce66456f9fce904c9`
remain unchanged, with zero formal method calls.

The unique real v2 Cascade package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`
contains exactly seven top-level artifacts and passes its strict read-only
verifier. Its SHA256 chain is: plan
`ef0c496d4679c8a790fa6715fca010c65bbe80dbcc9fb1a640139750e8f87161`,
lock `fea6d1e9912415c37f78393ef7d5e5e9bae156531bc9e6bd9a07936c41a09348`,
outcomes `d3ef26555e19fa58d74e40ccc9dc253e27db058a1b79720e77ab265f652c01f0`,
transcript `f95478b529f13871846400395d97b9d8a4f1948ddd30859a16dd7f66074a34c8`,
codebook manifest
`e8fbbd2ca195c8aa6d4a2ca8c821c2f8bb0eb73e6830ac85fff4558ef329738c`,
run manifest
`42d18066cc13740fd4367430b0319020ec4b943e5c01bf43f4df0759257ce172`,
and report
`750aaebf4919aa9a66383e6e4bf2d441efd718324ebca564157e6607d2b21e1b`.
The exact preflight passed 29 tests with exit 0 and output hash
`8760383422fb96ce6b8d644333e52064287e394f2827f57459bc110ded0a7a7c`.
All 60 requested frames were attempted, denominator-included, independently
verified, and `verified_success`; the verification union bound is
`3.2526065174565133e-18`, with zero unclassified/internal/provenance/accounting
failures. `cascade_formal_v1` is therefore promoted only for the locked real
domain `d=1024`, 64 symbols, bw120, frame SER `[0.20,0.30)`.

Synthetic v3 still promotes Cascade at 32/32 in both strata. LDPC remains
synthetically non-promoted at 29/32 and 14/32 and was not run on real data.
Phase 7 read-only verification passed for synthetic v3 and real v2; the safe
non-formal regression passed 22/22 in 0.66 s; `git diff --check` exited 0
apart from known ACL/LF warnings; frozen `src/`, `experiments/`, `tools/`, and
`results/` diffs were empty; and the independent audit result was PASS.

The active change is technically ready for archive review but is not archived.
Memory triage and the actual archive action remain pending.

## Next Step

Create a new LDPC-improvement OpenSpec change. LDPC must earn fresh synthetic
and real promotion before any frame-identical Polar/Cascade/LDPC comparison is
created. Do not substitute a lite method or tune on confirmation data.

## Archive Complete

`implement-formal-cascade-and-ldpc` is archived at
`openspec/changes/archive/2026-07-25-implement-formal-cascade-and-ldpc/`.
Its canonical merged specification is
`openspec/specs/formal-ir-methods/spec.md`. Final method state:
`cascade_formal_v1` is promoted by synthetic v3 and the bounded real v2
qualification; `ldpc_formal_v1` is synthetically `non_promoted` and had no
real run.

The next change must be a new LDPC-improvement OpenSpec change; it has not yet
been created. Do not begin a direct frame-identical Polar/Cascade/LDPC
comparison until LDPC earns fresh synthetic and real promotion.

## Nonbinary LDPC N0 Status (2026-07-26)

`nbldpc_formal_v1` now has a deterministic internal polynomial-basis GF(2^m)
contract for q=2 through q=1024, canonical field IDs, strict integer symbol
validation, and a read-only fail-closed preflight. Unsupported q returns
`unsupported_domain`; an expected field-ID mismatch returns
`backend_unavailable`; no external backend, decoder, or lower-q fallback is
used. Focused nonbinary plus existing qLDPC-reference tests passed 15/15, and
the selected formal/qLDPC regression passed 22/22.

N1 now adds one deterministic n=64, 32-row mother matrix with exact 16/24/32
prefix codebooks, pinned GF(q) rank, canonical bytes, golden codebook/manifest
hashes, and reconstruction-based fail-closed verification. Focused tests pass
22/22 and the selected formal/nonbinary/qLDPC regression passes 29/29.

N2 now adds a truth-isolated full-message FFT-QSPA decoder, q-ary symmetric
priors, GF(q) coset syndrome semantics, bounded q=1024 execution, MSB-first
mapping, locked Toeplitz wrapper, and exact syndrome/tag/public-control
accounting. N0-N2 plus qLDPC tests pass 35/35; selected formal regressions pass
17 with 2 skipped.

This is bounded engineering feasibility only. It proves no general
correction, FER/performance, calibration, synthetic/real qualification,
promotion, output, production readiness, or comparison eligibility. The next
task is planner-owned N3 pre-registration: freeze development/confirmation
data and separation, claim domain, one global policy, metrics/gates, resource
and stop rules, additive artifacts, invalid-run handling, and a strict
read-only verifier. Do not generate data or execute qualification yet.

# Nonbinary N3 outcome (2026-07-26)

`nbldpc_formal_v1` N3 is complete as an immutable **non-promoted** synthetic
package. N4 real-data work, confirmation tuning, and reruns are forbidden.
Official strict verification is failed/unverifiable because whole-worktree git
status drifted after execution; diagnostic replay is not a substitute.

## Nonbinary v2 Final Outcome (2026-07-26)

The successor package at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
was planned once, executed once, and strictly replay-verified. The verifier
returned `verified=True`, `run_status=non_promoted_development`,
`promoted=False`.

The selected tempered+damped QC48 policy (margin 8, max_iter 10, checks 32/40)
achieved only 0/24 at p=.20 and 5/24 at p=.30 versus the frozen 22/24
development-readiness floor. Confirmation was therefore not generated or
executed. Stop: no rerun, confirmation tuning, N4, sidecar access, `.ttbin`
processing, FER claim, or real-data claim.

## Nonbinary v3 Final Outcome (2026-07-30)

The covered-layered successor is complete at
`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic/`.
Its plan, execute, and strict read-only replay each ran exactly once. The
selected layered-l075 margin-8 policy passed development readiness at 23/24
for p=.20 and 24/24 for p=.30. Sealed confirmation achieved 32/32 and 30/32,
with zero prohibited failures, but the frozen gate required 31/32 in both
strata. The verifier returned `verified=True`, `run_status=completed`,
`promoted=False`.

This task ends at immutable synthetic non-promotion. Do not rerun or tune it.
N4, sidecar access, and real `.ttbin` processing remain forbidden until a
successor earns fresh synthetic promotion and a new OpenSpec change is
approved.

## Nonbinary v4 IR Final Outcome (2026-07-31)

`formal-nonbinary-ldpc-v4-incremental-redundancy` completed its one authorized
synthetic run at
`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
The sole strict replay returned `verified=True`, `run_status=completed`, and
`promoted=False`.

Development selected warm incremental redundancy at 64/64 for p=.20 and 63/64
for p=.30. Confirmation was 128/128 and 120/128, respectively, with eight
retained p=.30 `decode_failed` rows and zero prohibited failures. The terminal
gate is therefore A3. Do not rerun, tune, build N4, access sidecars, or process
real `.ttbin`.

The next permissible work is planner-only exploration of a fresh synthetic
successor. It must use new roots and freeze its code/rate/decoder change before
new development data; the current confirmation rows may diagnose the route but
must not be used as tuning data.

## NBLDPC v5 Routes A and B Final Outcomes (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Routes A and B, each
planned once and executed once (512 outcomes each, `run_status=completed`,
readiness true, `promoted=False`).

- Route A `20260731_v5a_nbldpc_multistage_synthetic`: p=.20 128/128, p=.30
  127/128 (one tail miss).
- Route B `20260731_v5b_nbldpc_mother_synthetic`: NBLDPC5B mother with zero
  w2/w3 syndrome collisions; p=.20 128/128, p=.30 127/128 (one tail miss).
- Both strict read-only replay attempts were blocked by external-session git
  HEAD drift after plan creation (`71bda20d`→`3a5d96a` for A,
  `3a5d96a`→`4dd6b7e` for B); source/CLI/contract hashes all still match. See
  the two 2026-08-01 decision-log entries.

Both packages are immutable non-promotion evidence; no rerun or confirmation
tuning is authorized. Route C was next (codebook identity fixed to NBLDPC5B,
roots 202607800000-202607830000, run ID
`20260731_v5c_nbldpc_decoder_synthetic`) and has completed; see the Route C
section below.

## NBLDPC v5 Route C Final Outcome (2026-08-01)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route C once:
`20260731_v5c_nbldpc_decoder_synthetic` (NBLDPC5B codebook identity, dual
policies `nbldpc_v5c_sched` / `nbldpc_v5c_ems`, roots
202607800000-202607830000), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained tail miss) —
  the same p=.30 tail pattern as Routes A and B.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` was unchanged by the replay.

The Route C package is immutable non-promotion evidence; no rerun or
confirmation tuning is authorized. Route D is next
(`20260731_v5d_nbldpc_post_synthetic`, roots 202607840000-202607870000,
list stage L=2 + one ADMM run per task 1.6; implementation starts at
task 7.1).

## NBLDPC v5 Route D Final Outcome (2026-08-02)

Change `formal-nonbinary-ldpc-v5-multistage-ir` executed Route D once:
`20260731_v5d_nbldpc_post_synthetic` (NBLDPC5B via v5c delegation, dual
policies `nbldpc_v5d_sched_post` / `nbldpc_v5d_ems_post`, list L=2 x top-8
+ ADMM rho=1.0 post-processing), `run_status=completed`, readiness true,
`promoted=False`.

- Promotion gates: p=.20 128/128, p=.30 127/128 (one retained
  confirmation-frame `decode_failed`) — the same p=.30 tail pattern as
  Routes A, B, C.
- The pre-registered strict read-only replay completed once and returned
  `{'verified': True, 'run_status': 'completed', 'promoted': False}`;
  `git status --porcelain` unchanged.
- Implementation corrections recorded: x-update prior sign and per-bit
  parity-relaxation z-projection (q=4 brute-force verified; see
  decision-log 2026-08-02 and module docstring).

With all four routes non-promoted, the v5 multistage change **terminates**
per task 7.4 with four immutable non-promoted packages
(20260731_v5a/v5b/v5c/v5d_nbldpc_*_synthetic). No rerun, tuning, N4,
sidecar, `.ttbin`, real-data, or comparison claim is authorized. A
successor must be a new OpenSpec change with fresh development and
confirmation data.
