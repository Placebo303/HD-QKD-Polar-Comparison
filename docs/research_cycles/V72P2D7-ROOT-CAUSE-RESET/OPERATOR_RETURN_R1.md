# D7 root-cause and route-reset R1 — operator return

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md` (R1)
- Branch: `formal-ir-v72p1-addendum-clean` (recorded, not switched)
- Lifecycle terminal: `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`
- Return type: `COMPLETE` (Phases A–F; X1–X4 and D7-H not run)

## 1. Completed acceptance IDs

- **A01** seven objectives and claim ceiling recorded in `proposal.md`.
- **A02** historical evidence retained byte-identical; corrections additive.
- **A03** cycle state created; initial terminal was
  `IMPLEMENTATION_IN_PROGRESS / EXECUTION_NOT_AUTHORIZED`, now the F05
  candidate terminal.
- **A04** D7-F corrigendum added (`D7_F_CORRIGENDUM_R1.md` and
  decision-log entry): historical single-graph n=16 paired label
  (candidate-only 0 / reference-only 2 / both 0 / neither 14; exact
  two-sided McNemar p = 0.5), not a general mechanism fact.
- **A05** G2 recorded pending (`G2_STATUS_NOTE_R1.md`, cycle state,
  proposal); not failed, skipped, or superseded.
- **B01** `canonical_source_q` and `canonical_transfer_l2_prior` exposed in
  the D5 module; `_run_layered_block` uses the canonical source conversion
  and the same `app_fed_l2_prior` implementation the wrapper exposes.
- **B02** deterministic same-input fixture and comparison harness
  (`compare_same_input`, `g1_layered_capture`) asserting equality of L1
  input prior, `q`, L2 transfer prior, both syndromes, decoded target, and
  per-layer counters between the legacy-G1-compatible and D7 paths.
- **B03** provenance matrix covered: exact `CHECK_UPDATED`, missing key,
  explicit `None`, `PRIOR_ONLY`, unknown token, valid zero-iteration
  prior-only return; all non-`CHECK_UPDATED` cross-layer consumption fails
  closed before mixer and before the L2 decoder on both paths.
- **B04** first-mismatch localization implemented (tensor, flat index or
  mapping key, both values, max abs diff). No mismatch occurred under the
  frozen comparison contract; no compensation or tuning was applied.
- **B05** G1 evidence schema extended additively: per-layer exact,
  syndrome-valid, iteration, provenance, and transfer-invoked/blocked
  counts; existing keys, filenames, and existing column order preserved.
  `_run_layered_block` keeps its default fail-closed raise contract
  (keyword-only `on_blocked_transfer="raise"`); the evidence scan records a
  blocked transfer as a non-invocation with no mixer and no L2 decode.
- **B06** no-write probe `probe_historical_decoder_provenance` added;
  historical resolution only when no decoder is injected; no root, no
  writes, no phase; A–F tests inject fakes only.
- **C01–C07** frozen multi-graph runner implemented (module + CLI):
  three graph pairs; block seeds `2026091300..2026091315`; n=64 with f=1.2
  primary (rows 59/52) and f=1.0 sanity (49/43); four arms plus
  forward/reverse joint outcomes; accepted Model-F input; `max_iter=90`,
  `damping_alpha=1.0`; one fresh `workspace/` root with the seven frozen
  files, never overwritten; raw paired discordant counts per graph and f
  with exact two-sided McNemar p and Wilson 95% intervals as descriptive
  diagnostics; terminal vocabulary frozen and scope-tagged.
- **D01–D05** bounded ladder implemented (90 / 360 / existing flooding),
  per-arm exact/syndrome/residual/posterior/changed fields, tiny
  exact-enumeration cross-checked against brute force, scope enforcement
  (f=1.2 and frozen seeds only), labeled `STRONG_REFERENCE_DIAGNOSTIC`.
- **E01** G2 reconciled with the accepted D5 plan: matrix matches;
  `run_g2_phase` now records `wall_seconds` and run `peak_rss_bytes`;
  `_grade_g2` rejects wall > 3600 s or RSS >= 2 GiB (None peak blocks);
  `write_g2_evidence` carries the new fields additively.
- **E02** four-state grading preserved; no `ROUTE_DEAD` wording revived.
- **E03** fake-runner tests added for the exact matrix, budget accounting,
  additive output, per-layer metrics, and no accidental decoder call.
- **E04** `G2_RUNTIME_UNVERIFIED` recorded; no runtime estimate claimed.
- **F01–F05** T0/T1 executed with fake decoders and fresh basetemps;
  results below; review entrypoint and manifest prepared.

## 2. Changed-file manifest (scoped)

Modified (tracked):

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  (+278 / −33 vs HEAD; all of it this task)
- `docs/decision-log.md` (this task appended exactly one 7-line entry at
  EOF; the file already carried pre-existing uncommitted changes in the
  worktree — 52 insertions — which were not touched)

New (untracked):

- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/proposal.md`
- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/design.md`
- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/tasks.md`
- `openspec/changes/formal-ir-d7-root-cause-and-route-reset/specs/d7-root-cause-and-route-reset/spec.md`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/cycle_state.yaml`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/D7_F_CORRIGENDUM_R1.md`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_STATUS_NOTE_R1.md`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/OPERATOR_RETURN_R1.md`
- `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/REVIEW_ENTRYPOINT.md`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
- `comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py`
- `scripts/v72p2d7_consistency_multigraph.py`

No other tracked file was modified by this task. The other 11 content-diff
files in the worktree and all pre-existing untracked content are unrelated
and untouched. No commit was created; nothing was pushed.

## 3. Exact tests/commands and results

All runs from the repository root with the repo venv; every `--basetemp`
is a fresh additive `workspace/v72p2d7_r1_*` root created for that run.
Command form:

```text
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace root> <files>
```

| # | Files | Result |
|---|-------|--------|
| T0a | `py_compile` on the modified D5 module, the new module, the new CLI | exit 0 |
| T0b/T1 | `test_v72p2d7_r1_consistency_multigraph.py` (new) | **36 passed** |
| T1a | `test_v72p2d7_bp_belief_provenance.py` + `test_v72p2d7_gf32_decoder_certification.py` + new file | **73 passed** |
| T1b | `test_v72p2d5_gf32_rate_mother.py` | **165 passed** |
| T1c | `test_v72p2d5_model_f_input.py` | **32 passed** |
| T1d | `test_v72p2d6_gf32_graph_mother.py` | **62 passed** |
| T1e | `test_v72p2d7_gf32_alternating_discriminator.py` | **32 passed** |

Pre-existing out-of-scope failures observed while broadening the check
(unchanged by this task; each asserts the absence of an accepted historical
root or stale authorization state, not code paths this change touches):

- `test_v72p2d7_gf32_cross_layer_discriminator.py::test_x05...` (accepted
  D7-E root exists; test expects none) — 39 others pass.
- `test_v72p2d7_gf32_reverse_order_discriminator.py::test_r01...` (accepted
  D7-F root exists) — 40 others pass.
- `test_v72p2d7_gf32_schedule_discriminator.py` x2 (accepted D7-D root
  exists) — 28 others pass.
- `test_v72p2d7_gf32_easy_regime.py` x2 (accepted D7-B root exists) —
  29 others pass.
- `test_v72p2d7_gf32_bidirectional_oracle.py::test_c19...` (D7-C state has
  `decoder_executed: true`) — 19 others pass.
- `test_v72p2d7_gf32_extrinsic_contract.py::test_ext_06...` (D7-H module
  now exists) — 47 others pass.

Also note a pre-existing cross-file import-layout fragility: running
`test_v72p2d5_*` and `test_v72p2d7_*` files in some single-invocation orders
fails at collection on the repo's dual `comparison_bench` namespace layouts.
The focused T1 protocol above uses per-group invocations, and the new test
module avoids any global `sys.path` mutation.

## 4. Production decoder / CAL / VAL call counts

**Zero.** Every decoder in every A–F test is an injected fake; the
production bind (`bind_row_layered_decoders` / `bind_historical_decoder`)
is monkeypatched to fail in the tests that would otherwise reach it; the
B06 probe was only called with injected fakes; no Model-F loader was
entered (monkeypatched in the runner tests); no CAL/VAL parquet was read;
history G1/G2/D7-H were not executed. No output root outside fresh
`workspace/v72p2d7_r1_*` test roots was created.

## 5. First-principles equivalence finding (B02/B04)

On identical in-memory graph, block, priors, and injected decoder returns,
the legacy-G1-compatible and D7 transfer paths form:

- `q` (source posterior-to-probability): **bitwise identical**
  (`max_abs_diff == 0`);
- target syndromes, decoded targets, per-layer counters: **exactly equal**;
- L1 input prior and L2 transfer prior: **equal within float64
  reassociation**, measured `max_abs_diff` across three independent
  fixtures in `[6.9e-18, 2.1e-17]`, far below the frozen `atol=1e-12`.

The formulas are algebraically identical (`P2` normalization before vs
after indexing, and einsum layout order, are the only differences). No
first unequal value occurred under the frozen contract, so B04's STOP did
not trigger and no tuning was applied.

Boundary noted (not part of the comparison): historical G1 used the
`build_f_model` estimator while D7 uses `build_f_model_concentration`. The
equivalence claim is conditional on identical input priors, exactly as
B02 specifies.

## 6. Remaining dormant phases and exact authorization needs

- **X1 consistency probe** (read-only): needs
  `x1_consistency_probe_authorized: true` in the cycle state and the exact
  command `python scripts/v72p2d7_consistency_multigraph.py --consistency`;
  zero decoder calls, zero writes.
- **X2 multi-graph exploratory batch**: needs Pre-EXECUTE review, explicit
  user authorization, a fresh `workspace/d7_r1_multigraph_<uuid>` root,
  `--model-f-root workspace/v72p2d5_model_f_input/20260907_r1`, an
  operator-recorded wall budget, and the exact CLI command; production
  decoder calls are then allowed, maximum 384.
- **X3 failed-block reference ladder**: production decoder calls; authorize
  separately or explicitly together with X2 after its maximum call count is
  known; only frozen f=1.2 failing blocks, no seed replacement.
- **X4 G2**: sole n=256 length discriminator; separate explicit
  authorization and independent Pre-RESULT review; do not bundle with
  X2/X3.
- **D7-H**: outside execution scope until X2–X4 evidence is reviewed and
  the main thread makes a new route decision.

No execution phase may review or accept its own results.

## 7. Commit / push

No commits were created for this task; nothing was pushed. Changes remain
in the worktree for independent review.

## 8. Protected outputs

No historical G1/D7 manifest, summary, table, report, authorization
record, frozen `src/`, `experiments/`, or historical `tools/` file was
modified. Model-F artifacts were not read by tests. The accepted
`workspace/` roots were not touched (several pre-existing stale-absence
tests in the D7 suite fail for exactly that pre-existing world state).

## 9. Delta note — post-return correction (2026-09-13, main-thread authorized)

- A04's D7-F discordant direction was corrected to candidate-only
  (reverse-only) 0 / reference-only (forward-only) 2 / both 0 / neither 14
  against the immutable D7-F `stratum_summary.csv` (row 2:
  `candidate_only=0, reference_only=2`). The wrong direction originated in
  packet §4 and was copied into the candidate artifacts.
- No code, test, or historical-evidence file changed; no execution occurred;
  no commit or push was made.

## 10. Additive pointer — G2 prior-configuration corrigendum (D14 VR-C, docs only)

> This section is append-only (2026-09-14, D14 C-impl). No line above is
> rewritten. The G2/X4 inference-scope corrigendum is recorded in
> `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`:
> root `workspace/v72p2d5_g2/20260906_r1` preserved unchanged (4 files,
> 1320/1320 calls); literal grade `G2_CURRENT_CONFIGURATION_FAILED` retained
> as the accurate description of the executed rejected per-cell-prior
> configuration (X4 → `run_g2_synthetic` → `prepare_model_f_prior`); that
> result is invalid as n=256 finite-length feasibility / route-closure
> evidence; supersession covers the scientific inference only, not the
> recorded execution; no unique-cause claim.
