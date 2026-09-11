# D7/BP belief-provenance interface — independent implementation review R1

**Verdict**: `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS`

**Revision reviewed**: `654fa299` (`feat(d7): add fail-closed belief provenance for cross-layer APP`, 22 files, +725/−22) against the frozen OpenSpec at `5483dd8` and packet `.workbuddy/tasks/D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md` §5 A11–A16.
**Reviewer**: independent (did not write the implementation). No file edits, no commits, no push, no production decoder/real-data execution; protected roots inspected at metadata level only.

## 0. Scope and independence

- Scope: producer mapping (BP-01), D5 plumbing/fail-closed guard (BP-02/03), live and historical consumers (BP-04), labeling seam (BP-05), warm-start boundary (BP-06), D7-C independence (BP-08), PV-01–PV-14 (A15), tier evidence (A16), allowlist/scope (A10).
- Methods:
  - full source and diff inspection of all 22 changed files;
  - runtime reproduction of tiers with fresh basetemps and `-p no:cacheprovider`;
  - read-only baseline extraction `git archive 5483dd8 | tar -x -C /tmp/bp_baseline` for byte-equivalence and pre-existing-failure proof;
  - in-memory mutation of the static-inventory matcher (no file edits);
  - metadata-only scans of protected roots (`find -newermt`, dir mtimes).
- Not run: any production decoder path, `longrun_*`/`minrerun_*`/`routeA_*`, `--phase`, Model-F/CAL/VAL/real/raw reads, any commit or push.

## 1. Producer mapping (BP-01 / A11)

Source: `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py` (diff `5483dd8..654fa299`).

Constants and guard: `BELIEF_PROVENANCE_{PRIOR_ONLY,CHECK_UPDATED,WARM_START_UNSPECIFIED}`, `BELIEF_PROVENANCE_TOKENS`, `PRIOR_ONLY_CURRENT_BELIEF`, `UnconditionedBeliefProvenanceError`, `require_check_updated_provenance`, `belief_diagnostic_label` (new, around L519–566). `DecoderResult` gains `belief_provenance: Optional[str] = None` appended after the six existing fields (`Optional` already imported).

Every `DecoderResult` construction site (5 total; no others repo-wide in this module) was inspected:

| Return site | Seed | Token | Verified |
|---|---|---|---|
| row-layered initial-syndrome return (`iterations == 0`) | cold | `PRIOR_ONLY` | yes |
| row-layered in-loop return after a full sweep (`iterations = it >= 1`) | cold | `CHECK_UPDATED` | yes |
| row-layered final return after `max_iter` sweeps | cold, `max_iter >= 1` | `CHECK_UPDATED` | yes |
| row-layered final return | cold, `max_iter < 1` | `PRIOR_ONLY` | yes (runtime `max_iter=0` check) |
| all three row-layered returns above | warm-seeded | `WARM_START_UNSPECIFIED` | yes (it0 and it1) |
| flooding in-loop return (first return follows a full check round; loop starts `it=1`) | n/a | `CHECK_UPDATED` | yes |
| flooding final return | n/a | `CHECK_UPDATED` | yes |
| `decode_damped_row_layered_fftqspa` | delegates | passes producer result through | yes |

- `warm_seeded = warm_beliefs is not None and warm_beliefs.shape == (n, q)` is a pure single evaluation of the pre-existing predicate; the old `if` had identical semantics and no side effects. No explicit-provenance parameter exists, so every warm-seeded return is `WARM_START_UNSPECIFIED` — consistent with BP-06 (no warm-start propagation) and with "never inferred from `iterations`".
- No change to `x_hat`, syndrome, iterations, status, beliefs, stopping, damping, normalization, or the recurrence. Independently confirmed against baseline: a two-process dump of 9 scenarios (it0, 1-sweep, 2-sweep max-iter, damped, non-converged max-iter, warm it0/it1, flooding converged/max-iter) compared 54 arrays (all five existing fields, dtype+values, plus runtime type) between `5483dd8` and HEAD — **byte-identical**; the only delta is the appended field with the exact expected tokens.
- Positional construction compatibility: dataclass field order is exactly the old six + `belief_provenance`, default `None`; legacy positional construction verified in PV-05 and independently.

## 2. Plumbing and fail-closed boundary (BP-02/BP-03 / A12)

- `_decode_block` (`v72p2d5_gf32_rate_mother.py`): reads `get("belief_provenance")` (dict get / getattr with default), appends it to the returned tuple after the optional `observed_syn`, preserving key/element order. All 5 in-module call sites were updated (L1374, L1389, L1397, L1721, L2103); no other production caller of `_decode_block` exists.
- Three adapter dicts are key-additive: `historical_g0_decoder`, the `_bound_hist` closure, `bind_historical_decoder` all add `"belief_provenance": getattr(result, "belief_provenance", None)`; no key removed or renamed.
- `_run_layered_block` calls the shared guard immediately after `_decode_block` and **before** `q` construction / `app_fed_l2_prior` / any L2 decode. The guard accepts only exactly `CHECK_UPDATED`; `PRIOR_ONLY`, missing, `None`, unknown, empty and `WARM_START_UNSPECIFIED` all raise `UnconditionedBeliefProvenanceError` naming consumer and token. Independently reproduced the `WARM_START_UNSPECIFIED` refusal by direct call.
- The guard is the single shared implementation in v35; D5 imports it lazily (layout-tolerant) so importing the D5 module does not import the historical decoder.
- Bypass scan: `app_fed_l2_prior` has exactly one call site in D5 (inside the guarded block); the static inventory test covers 13 accepted consumer files plus D5 and, by in-memory mutation of each file's lines (guard removed), was verified to **fail** on every missing guard (check-the-check). Runtime refusal tests use mixer spies; PV-06b uses a real producer it0 result, not only a hand-built dict.

## 3. Consumers and historical modules (BP-04 / A13)

- `v72p2d3_gf32_contrast.py`: provenance carried from both fake and production branches of `run_g_layer`; the `np.log(prior_p)` fallback is labeled `PRIOR_ONLY` by construction; output dict gains `belief_provenance` plus `belief_label` (the BP-05 diagnostic seam); `run_real_contrast` refuses before `q = softmax_beliefs_history(...)` / `build_l2_prior_from_l1`. `run_l1_stage` returns that dict, so the recombination reads a real provenance.
- `methods/nbldpc_shell_adapter.py`: guard inserted after the L1 decode, before `softmax_beliefs(res_l1.final_beliefs)` / `get_l1_app_prior_l2`; single cross-layer site.
- `scripts/execute_v64_fresh_verify.py`: guard inserted at the single L1→L2 site before `softmax_beliefs` / `get_l1_app_prior_l2`.
- Historical v45–v55 (10 modules, exactly the proposal rows 9–18): each has exactly one `softmax_beliefs(<decoder result>.final_beliefs)` → mixer site; each received the same fail-closed guard at that entry with a comment that future reactivation needs its own OpenSpec. No recomputation, no reinterpretation, no other unguarded decoder-belief path in those modules (fake-runner branches build synthetic beliefs, not decoder returns). They were not rerun.
- No historical output/artifact was rewritten: the commit contains no `results/`, `workspace/`, or `comparison_bench/outputs_comparison/` path; content diffs of tracked outputs are empty (926 dirty output-path entries are stat-only, e.g. `_tmp_cli_check` blobs unchanged between index and worktree); no tracked output file anywhere has mtime after the entry HEAD; no file inside the D7-A/B/C/D or Model-F roots has mtime after 2026-09-11 08:35.

## 4. PV matrix (A15)

Tier-1 run (fresh `/tmp` basetemp, `-p no:cacheprovider`): `comparison_bench/tests/test_v72p2d7_bp_belief_provenance.py` → **23 passed**. `py_compile` of all 15 touched source/script files and package import of the main interface modules → OK.

| PV | Test(s) | Result |
|---|---|---|
| PV-01 | `test_pv_01_...` (it0 → PRIOR_ONLY, floor/renorm identity) | pass |
| PV-02 | `test_pv_02_...` (≥1 sweep → CHECK_UPDATED, beliefs differ from log-prior) | pass |
| PV-03 | `test_pv_03_...` (flooding first return CHECK_UPDATED) | pass |
| PV-04 | `test_pv_04_...` (warm it0/it1 → WARM_START_UNSPECIFIED, never inferred) | pass |
| PV-05 | `test_pv_05_...` (field appended/default None, positional compat, exact floor path, ≤1e-12 vs independent D7-A `row_layered_reference`); additionally verified byte-identical against baseline (54 arrays) | pass |
| PV-06/06b | refusal on PRIOR_ONLY before mixer+L2 spies; real-producer it0 refusal | pass |
| PV-07/07b | missing/None/unknown/`""`/`0`, legacy `SimpleNamespace` refusal; mixer spy 0 | pass |
| PV-08 | no q reaches the mixer when beliefs are absent and provenance is prior-only | pass |
| PV-09 | CHECK_UPDATED pass-through reproduces `q @ P` (≤1e-12) | pass |
| PV-10 | `PRIOR_ONLY_CURRENT_BELIEF` label; not a token; hard decision never upgrades it | pass |
| PV-11 | `_decode_block` tuple, three adapter dicts, d3 dict path + label, `_bound_hist` key | pass |
| PV-12 | legacy schema/no real-root reads (self-scan) | pass |
| PV-13 | hard-decision-only consumer unaffected | pass |
| PV-14 | oracle has no interface symbols; interface files never reference the oracle | pass |
| inventory | 13 paths + D5, guard within window; mutation causes failure | pass |

Non-blocking coverage notes: (a) PV-07's parametrization does not include the literal `WARM_START_UNSPECIFIED` (its refusal was verified independently at runtime and follows the same `!= CHECK_UPDATED` branch); (b) the PV-06 spy's `"l2"` counter is never incremented, so "before L2 decode" rests on guard position plus the mixer spy; (c) PV-14 is a source-text (not runtime `sys.modules`) import-graph check; it detects direct references in both directions and is adequate for the accepted narrow contract.

## 5. Tier evidence and isolated-failure adjudication (A16)

Independently reproduced (fresh basetemps, `-p no:cacheprovider`):

- **Tier 1** — BP/PV file: 23 passed. (plus py_compile/import, above)
- **Tier 2 (affected consumers)** — `test_v72p2d5` 165, `test_v72p2d3` 62, `test_v64_instrumentation` 12, `test_v52` 12, `test_v53` 14 → **265 passed, 0 failed**. Note: the d3 tests require a task basetemp under `workspace/` (they assert synthetic outputs stay under `workspace/`); a `/tmp` basetemp produces 5 spurious location failures, not code failures.
- **Tier 3** — D7-A `test_v72p2d7_gf32_decoder_certification`: 14 passed. D7-C `test_v72p2d7_gf32_bidirectional_oracle`: 19 passed / 1 failed. D7-B+ D7-D (`easy_regime` + `schedule_discriminator`): 57 passed / 4 failed. Total **90 passed / 5 failed**.
- **Tier 4 (milestone, v45–v48)** — **134 passed / 5 failed**.

Adjudication of the 10 isolated failures (all IDs also fail identically at baseline `5483dd8` extracted read-only; no skip/xFAIL/delete was used):

1. `test_v72p2d7_gf32_bidirectional_oracle.py::test_c19_...` — root-absence part was converted to lifecycle-aware snapshot invariance (names + file sizes of existing D7-C roots; workspace listing and Model-F metadata unchanged), which passes. Residual failure is a stale authorization snapshot: `decoder_executed` (and then `result_created`) is `True` in the D7-C cycle state after the legitimate, accepted D7-C run, while the test expects `False`. **Accepted as isolation, not a blocking defect**: the conversion used exactly the mechanism A16 names for known stale root-absence tests; the remaining assertion is not a root-absence assertion (A16 does not authorize converting it), completing it would weaken an authorization tripwire, and reverting the converted part would restore a more-stale assertion without benefit. The failure remains honestly red and pre-existing. Scope note: this D7-C test-file edit sits at the edge of BP-affected scope and should be attributed to D7-C lifecycle housekeeping in the next reconciliation; it does not touch D7-C logic.
2. `test_v72p2d7_gf32_easy_regime.py::test_launch_l04_...` and `..._l12_...`; `test_v72p2d7_gf32_schedule_discriminator.py::test_f08_...` and `::test_s21_...` — pure stale root-absence assertions against the accepted D7-B R2 and D7-D roots. Correctly **not** converted (outside BP-affected scope) and validly isolated with baseline proof.
3. v45–v48 CLI/overwrite-guard failures (`test_t10_cli_no_fake_option`, `test_t10_cli_sha_rejects`, `test_cli_guards` ×3) — caused by pre-existing accepted `run_01` output roots: the CLIs refuse overwrite (`J7`) before reaching the asserted SHA/authorization message. Not root-absence tests, not BP-affected, and each fails identically at baseline; valid isolation.

## 6. No-retroactivity, independence, and scope

- Commit file list (22) maps exactly onto the A10 allowlist: v35, the ten named v45–v55 modules, v72p2d5, v72p2d3, shell adapter, V64 runner, and directly corresponding tests. No frozen `src/`, `experiments/`, `tools/`, sibling `nonbinary_v10_fftqspa.py`, OpenSpec spec/proposal/design/tasks, docs, or evidence path is in the commit.
- D7-A/C/D scientific modules are untouched; only their test files changed: D7-A test fakes gained an explicit `CHECK_UPDATED` (test-only, proposal row 24) and the D7-C C19 conversion above.
- D7-C independence (PV-14): the oracle module imports only stdlib + numpy at module level; no interface symbol appears in it, and no touched interface file references the oracle.
- Protected roots: D7-A/B/C/D root dir mtimes (2026-09-10 20:33, 2026-09-11 00:33, 07:30) all precede the commit (2026-09-11 10:16); no file inside them, the Model-F root, `results/`, or `outputs_comparison/` has mtime after the entry HEAD.
- Working-copy state of all 22 committed files matches the commit (clean). No push: `654fa299` is not an ancestor of `origin/formal-ir-v72p1-addendum-clean`.

## 7. Discrepancies

1. **Working-tree V35 report regression (not part of this commit)**. `docs/v35-algorithm-development-report.md` currently holds the rejected `NB_CANDIDATE_DEVELOPMENT_READY` rewrite again (mtime 2026-09-11 10:28:58, i.e. *after* `654fa299` at 10:16). The A08 reconciliation review had verified this diff empty at commit time. This contradicts packet A06's end state, is unrelated to the BP interface commit, and must be re-restored before any future stage/commit touches `docs/`. Flagged for main-thread action; not blocking this verdict.
2. C19 residual stale state assertion and the D7-C test-file scope edge (section 5.1).
3. Non-blocking test-coverage notes in section 4 (PV-07 WARM_START parametrization, dead PV-06 `l2` counter, PV-14 text-only check).
4. The 926 dirty `outputs_comparison` entries are stat-only (content blobs identical); only 3 files in the whole worktree have content diffs, all unrelated to this commit (`docs/research-cycle-sop.md`, the V35 report above, a workspace evidence fixture). No historical output content was rewritten.

## 8. Verdict restatement

`D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS`

The producer tokens are exact at every return site, the field is additive and numerically inert (byte-identical baseline comparison), all active and dormant cross-layer APP entries are guarded before prior construction, the PV-01–PV-14 matrix and the narrow static inventory pass, scope is the A10 allowlist, and no retroactive or protected-root change exists. All ten observed test failures are pre-existing at `5483dd8`; the C19 partial conversion is an acceptable, honest isolation. No scoped rework is required. The V35 working-tree regression in §7.1 is a pre-existing/independent docs-state issue the main thread must resolve before any future docs staging; it does not affect this commit's content.
