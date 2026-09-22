# D7/BP belief-provenance interface — independent readiness review R1

**Verdict**: `D7_BP_INTERFACE_READINESS_REVIEW_PASS`

**Revision reviewed**: `654fa2996dabe8d37536b1f1b72c8a7e6a90adc1`
(`feat(d7): add fail-closed belief provenance for cross-layer APP`, 2026-09-11
10:16:19 +0800, 22 files, +725/−22) against the frozen OpenSpec
`openspec/changes/v72p2d7-layer-interface-belief-provenance/` at `5483dd87`
and packet `.workbuddy/tasks/D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md` A18.

**Reviewer**: separate context from the implementation reviewer
(`D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_R1` = PASS). Review-only: the only file
written is this document. No commit, no push, no production decoder/real-data
execution, no evidence-root content read (metadata only). Tiny in-memory
fixtures were used for independent runtime checks.

## 0. Verdict, scope, independence

- All eight readiness checks (Alternative A; numerical/stopping invariance;
  fail-closed inventory; warm-start refusal; isolation; tests; authorization;
  next-work gate) pass on the reviewed revision, apart from two recorded
  non-blocking discrepancies that require main-thread action (§8): a
  Windows-side NBPolar exchange-copy push of `654fa299`, and one dormant
  cross-layer consumer outside the frozen inventory
  (`scripts/v72p2d6_graph_mother_development.py`).
- Methods: full diff/forensics `5483dd8..654fa299`; source inspection of every
  producer/consumer site; read-only baseline extraction
  (`git archive 5483dd8 | tar -x -C /tmp/d7bp_readiness_base`); independent
  11-scenario numerical dump comparison baseline vs HEAD
  (`/tmp/d7bp_equiv_dump.py`); independent runtime refusal checks on tiny
  in-memory fixtures (`/tmp/d7bp_warm_refusal_check.py`); four-tier test
  reproduction with fresh task-owned basetemps and `-p no:cacheprovider`;
  protected-root metadata scans (names/sizes/mtime only); git reflog/remote
  inspection.
- Review doc context sources: frozen proposal/design/tasks/spec; A17
  implementation review (including its non-blocking notes); D7-B/C/D
  `cycle_state.yaml`; D7-D acceptance doc; decision log entries through
  2026-09-11.

## 1. Alternative A boundary (check 1)

Exactly Alternative A is implemented; B/C and warm-start propagation are absent.

- Exact enum, no extras: `BELIEF_PROVENANCE_PRIOR_ONLY`,
  `BELIEF_PROVENANCE_CHECK_UPDATED`, `BELIEF_PROVENANCE_WARM_START_UNSPECIFIED`;
  `BELIEF_PROVENANCE_TOKENS` is exactly these three
  (v35 L521–529). `PRIOR_ONLY_CURRENT_BELIEF` is explicitly a diagnostic
  record label, not a token (v35 L530–532); PV-10 asserts non-membership.
- No Alternative B (forced/computed extra sweep): no new decoder parameters,
  no loop-bound change (`for it in range(1, max_iter + 1)` unchanged), no
  `min_sweeps`/forced-sweep path, no stopping change. The guard *refuses*
  instead of computing a conditioned APP (v35 L540–552).
- No Alternative C (unconditional fallback + label-only rule): the migrated
  consumers raise `UnconditionedBeliefProvenanceError` before the mixer; the
  silent `prior @ P` path is removed at every accepted inventory site.
- No warm-start propagation mechanism: `decode_row_layered_fftqspa` has no
  provenance input parameter; every warm-seeded return is
  `WARM_START_UNSPECIFIED`; nothing upgrades it. The token is produced and
  refused only (guard path), never consumed as evidence.

## 2. Numerical / stopping invariance (check 2)

Diff `5483dd8..654fa299` inspection (all v35 hunks):

- The only hunk touching existing control flow is the two-line refactor
  `warm_seeded = warm_beliefs is not None and warm_beliefs.shape == (n, q)`;
  `if warm_seeded:` — semantically identical to the previous inline `if`
  (pure single evaluation of the pre-existing predicate, no side effects).
- Every other v35 hunk is an additive constant/class/function or the appended
  `belief_provenance` field. No change to `x_hat`, syndrome computation,
  `iterations`, `status`, `final_beliefs`, stopping, damping, floor (1e-15),
  renormalization, or the message recurrence. `decode_flooding_fftqspa`
  and `decode_damped_row_layered_fftqspa` (delegating) are additive-only.
- Producer token map verified at all return sites: cold it0 early exit →
  `PRIOR_ONLY`; cold in-loop after a full sweep → `CHECK_UPDATED`; cold final
  after `max_iter >= 1` → `CHECK_UPDATED`, after `max_iter < 1` →
  `PRIOR_ONLY`; any warm-seeded return (it0/in-loop/final) →
  `WARM_START_UNSPECIFIED`; flooding returns (both sites, first follows a full
  check round since the loop starts `it=1`) → `CHECK_UPDATED`. No other return
  sites exist.
- Independent byte-equivalence spot-check (not relying on the A17 run): two
  separate processes loaded baseline `5483dd8` v35 and HEAD v35 and dumped 11
  scenarios (it0 early exit, 1-sweep convergence, 2-sweep non-converged,
  `max_iter=0` cold, warm it0/warm it≥1, flooding converged/max-iter, damped
  it0/sweep, multi-row) × 6 compared fields (`x_hat` values, `syndrome_ok`,
  `iterations`, `status`, `final_beliefs` exact values, runtime container
  types). **0 field mismatches**; the only delta is the new token, exactly the
  three enum values. This corroborates A17's 54-array comparison.
- `_decode_block` (`v72p2d5` L1026–1060) appends provenance after the existing
  five elements (seventh when `return_syndrome=True`); first five positions
  unchanged; all 5 in-module callers updated. One dormant out-of-allowlist
  caller is arity-broken — recorded in §8.2, not a numerical drift.

## 3. Fail-closed inventory (check 3)

Independently enumerated accepted inventory; every site carries the shared
guard `require_check_updated_provenance` (accepts only exactly
`CHECK_UPDATED`) before any mixer / L2 prior / softmax-beliefs use:

| # | Site | Guard evidence (HEAD) |
|---|---|---|
| 1 | v35 producers (5 returns: flooding ×2, row-layered it0/in-loop/final) | token population only; producers are not consumers |
| 2 | D5 `_decode_block` | carries `get("belief_provenance")` as appended element (L1054, L1059); 5 in-module callers updated |
| 3 | D5 `historical_g0_decoder`, `_bound_hist`, `bind_historical_decoder` | additive `"belief_provenance"` key (L1112, L1668–1669, L2511); keys preserved |
| 4 | D5 `_run_layered_block` | guard L1378–1380 immediately after `_decode_block`, before `q` (L1383) and `app_fed_l2_prior` (L1388); single `app_fed_l2_prior` call site in module |
| 5 | `v72p2d3_gf32_contrast.py` `run_g_layer` | provenance carried from both branches; fallback labeled `PRIOR_ONLY`; dict + `belief_label` (L669–728); `run_real_contrast` guard L1361 before `softmax_beliefs_history` L1366 / `build_l2_prior_from_l1` L1367 |
| 6 | `methods/nbldpc_shell_adapter.py` | guard L256 before `q = softmax_beliefs(res_l1.final_beliefs)` L260 and `get_l1_app_prior_l2` L265 |
| 7 | `scripts/execute_v64_fresh_verify.py` | guard L190 before q L194 / prior L198 |
| 8 | v45/v46/v47/v48/v50/v51/v52/v53/v54/v55 | guard at L1049/1169/1094/1173/1457/1339/1221/1268/1317/1431, each 4 lines before the decoder-derived `q = softmax_beliefs(...)` at L1053/1173/1098/1177/1461/1343/1225/1272/1321/1435 |

- Runtime verification (independent, tiny fixtures): `PRIOR_ONLY` from a real
  producer it0 result and literal `WARM_START_UNSPECIFIED`, `None`, absent,
  `"BOGUS"`, `""`, `0` all raise before the mixer with mixer-call count 0;
  `CHECK_UPDATED` passes. Guard precedence over `q`/L2 confirmed by source and
  by PV-08.
- Static inventory test covers all 13 mixer paths + D5 `_run_layered_block`
  with a 10-line lookback; A17 additionally verified by in-memory mutation
  that removing any guard makes it fail (I confirmed the matcher/guard
  relationship by source inspection).
- A17 coverage caveats judged (all non-blocking): PV-14 is source-text rather
  than `sys.modules`; adequate for the narrow frozen contract. PV-06's `"l2"`
  counter is never incremented; "before L2 decode" still rests on the guard's
  position (immediately after `_decode_block`) plus the mixer spy, which I
  verified. PV-07 lacks the literal `WARM_START_UNSPECIFIED` parameter; I
  independently verified that refusal at runtime. The guard is therefore
  independently established.
- Beyond the frozen inventory: `scripts/v72p2d6_graph_mother_development.py`
  is an unguarded cross-layer APP consumer and is currently arity-broken
  (§8.2). It is not fail-closed by the new contract; it is dormant (D6
  execution unauthorized) and outside the A10 allowlist, so this could not be
  fixed in-scope.

## 4. Warm-start refusal (check 4)

- No inference from `iterations`: warm-seeded returns carry
  `WARM_START_UNSPECIFIED` for it0 and it≥1 alike (PV-04; my dump reproduces
  both), and cold it0 stays `PRIOR_ONLY`.
- A warm-seeded return without carried provenance is refused at the
  conditioned consumer: my direct `_run_layered_block` call with a literal
  `WARM_START_UNSPECIFIED` result raised
  `UnconditionedBeliefProvenanceError` with mixer count 0 (same shared guard
  branch as PV-06/07, `!= CHECK_UPDATED`).
- `WARM_START_UNSPECIFIED` has no positive consumer anywhere in the diff: it
  is produced by the producer and refused by the guard. BP-06 non-
  implementation is respected (`WARM_START_DEFERRED` closeout remains an
  A19 bookkeeping item).

## 5. Isolation / no real artifacts or decoder run (check 5)

- Commit content: 22 files, all source/test/script paths on the A10
  allowlist; zero paths under `results/`, `workspace/`,
  `comparison_bench/outputs_comparison/`, docs, or OpenSpec; no UUID anywhere
  in the diff.
- Tier logs/tests use tiny in-memory fixtures: the BP suite decodes only
  `_TINY_H` (1×2) fixtures; affected D7 suites use fake decoders; the BP
  test module self-asserts absence of real-root bindings (PV-12). Static scan
  of the new/changed test files found no `longrun_*`/`minrerun_*`/`routeA_*`,
  `--phase`, real/raw/parquet reads, or production execution binding.
- Protected roots (metadata only): D7-B
  `workspace/d7_b_easy_regime_c605d1e6-...` (dir mtime 2026-09-10 20:33),
  D7-C `..._94c0ea15-...` (2026-09-11 00:33), D7-D `..._64660d16-...`
  (2026-09-11 07:30), `workspace/v72p2d5_model_f_input/20260907_r1`
  (2026-09-07), plus G0/G1/D6-repair roots: **no file newer than the
  implementation commit (10:16:19) in any of them**, also after all of my
  test runs. No decoder execution beyond the tiny synthetic unit fixtures.
- My own temporary artifacts (disclosed, not evidence): `/tmp/d7bp_*` and a
  fresh `workspace/d7bp_readiness_r1_bt` basetemp (plus pre-existing
  `workspace/bp_r1_tmp_d3*` left by A17).

## 6. Tests and coverage (check 6)

Reproduced independently with fresh basetemps and `-p no:cacheprovider`
(exact A17 counts and failure IDs matched):

| Tier | Command scope | Result |
|---|---|---|
| 1 | `test_v72p2d7_bp_belief_provenance.py` | **23 passed** (19 test functions; PV-01…PV-14 + inventory all present) |
| 2 | affected consumers, combined runs: `test_v72p2d5`+`test_v64_instrumentation`+`test_v52`+`test_v53` = **203 passed**; `test_v72p2d3` = **62 passed** (per-file split 165/12/12/14 as in A17) | **265 passed, 0 failed** |
| 3 | combined `test_v72p2d7_gf32_decoder_certification`+`test_v72p2d7_gf32_bidirectional_oracle` = **33 passed / 1 failed**; combined `easy_regime`+`schedule_discriminator` = **57 passed / 4 failed** (per-file split 14; 19/1; 57/4 as in A17) | **90 passed / 5 failed** |
| 4 | v45–v48 | **134 passed / 5 failed** |

- Failing IDs exactly as adjudicated by A17: C19
  (`test_c19_protected_root_lifecycle_and_g2_r1d_absence`), easy-regime
  `test_launch_l04_*`/`test_launch_l12_*`, schedule-discriminator
  `test_f08_*`/`test_s21_*`, and v45×2/v46/v47/v48 CLI-guard tests.
- Pre-existing adjudication is sound: the D7-B/C/D roots and the D7-C
  `decoder_executed: true` fact already existed at `5483dd8` (I verified the
  tracked `cycle_state.yaml` at the baseline), so both the root-absence and
  the stale-authorization assertions fail there; the CLI-guard tests fail on
  pre-existing accepted `run_01` roots. The C19 edit converts only the
  root-absence part to lifecycle-aware snapshot invariance (the mechanism A16
  names); its residual authorization tripwire stays honestly red. No
  skip/xFAIL/delete was added anywhere (diff scan).
- Scope edge (A17 §5.1): the C19 test-file edit is D7-C lifecycle
  housekeeping at the edge of BP scope; it touches no D7-C logic. Accepted.

## 7. Authorization and next-work gate (checks 7–8)

- D7-B/C/D `cycle_state.yaml`: all execution/synthetic/real authorization keys
  `false`; `scientific_promotion: false`; `g1_authorized/g2_authorized:
  false`; `r1d_state: R1D_PAUSED_...`. The `true` entries
  (`decoder_executed`, `result_created`, `d7b_r2_accepted`, etc.) are
  recorded facts of accepted runs, not authority.
- No new UUID in this packet; no D7-E artifacts anywhere (`docs/`,
  `.workbuddy/tasks/`, states); D7-E is not frozen or authorized. The
  authoritative route in the D7-D state/acceptance doc is
  `BP_INTERFACE_PROVENANCE_IMPLEMENTATION`, and the packet's A19/A20 only
  opens a D7-E *packet freeze* after both reviews PASS. D7-D acceptance doc:
  "no frozen automatic successor … No D7-E work, … or authorized here"
  (decision-log 3425 same). R1d remains optional/paused; G1/G2 unauthorized.
- Push: **no push to `origin`** — `origin/formal-ir-v72p1-addendum-clean`
  remains at `d98db0e2` (ancestor of HEAD), and the BP implementation path is
  absent from the origin tree. One Windows-side push of `654fa299` to
  `nbpolar-origin/codex/nbpolar-phase0` exists and is recorded in §8.1; the
  "No push" claims in the packet, A17 review, and accepted docs should be
  scoped accordingly before any A19/A20 record is published.

## 8. Discrepancies

1. **NBPolar exchange-copy push of the reviewed commit (record/posture
   discrepancy; requires main-thread disposition).**
   `.git/logs/refs/remotes/nbpolar-origin/codex/nbpolar-phase0` records
   `0000… → 654fa2996dabe8d37536b1f1b72c8a7e6a90adc1 … update by push` at
   2026-09-11 10:49:38 +0800; `.git/logs/refs/heads/codex/nbpolar-phase0`
   records branch creation from `654fa299` at 10:48:42; linked worktree
   `HD-QKD_Polar_Comparison-nbpolar` (gitdir `D:/Code/...`) was checked out
   10:48:44; `.git/config` gained the branch-tracking section at 10:49:38.
   No push to `origin` (above). The push was executed from the Windows host
   (repo config `http.sslBackend = openssl` is unsupported by the WSL git
   here — my `git ls-remote` fails with that error, and all historical
   successful pushes share this signature), most consistent with a
   principal/orchestrator-side NBPolar exchange snapshot rather than the
   WSL packet operator; it cannot be conclusively attributed from repository
   evidence. It published no evidence roots and changed no authorization
   state, so per `AGENTS.md` §1.1 it is non-blocking for interface readiness.
   **Required action**: before A19/A20 publish any "no push" statement,
   either (a) record the NBPolar exchange-copy action and scope the no-push
   language to `origin`/operator (recommended if intentional), or (b) if
   unintended, treat as a packet-posture failure, remediate, and re-issue A18.
2. **`scripts/v72p2d6_graph_mother_development.py` — dormant unguarded
   cross-layer consumer, now arity-broken (required follow-up before any D6
   rerun).** The D6 heavy worker (L104, L126) unpacks
   `core._decode_block(...)` into 5 names, while `_decode_block` now returns
   6 (7 with syndrome): every decode cell raises `ValueError: too many values
   to unpack` and is recorded as `crash`, so the D6 route currently fails
   stop before its unguarded L1→L2 path (`pr2 = d5.app_fed_l2_prior(p2, bob,
   q)`, L791) could feed `prior @ P`. The script is outside the frozen
   inventory (proposal rows 1–24) and the A10 allowlist; D6 execution is
   unauthorized/dormant. If the arity were "repaired" without adding the
   guard, the E09 hazard would return. **Required action**: guard or
   explicitly block this entry (small OpenSpec scope extension) before any
   authorized D6 rerun; record as a known gap in the D7-E packet freeze.
3. A17 coverage caveats (PV-14 source-text; dead PV-06 `l2` counter; PV-07
   lacks the literal warm token): informational only; warm-token refusal,
   guard-before-mixer position, and inventory guard placement independently
   re-verified here.
4. C19 residual stale authorization assertion (pre-existing; honest red;
   convert in the next D7-C lifecycle touch). D7-C test-file scope edge as
   in A17 §5.1; no D7-C logic touched.
5. **V35 working-tree regression still present** (unresolved A06 item,
   re-verified): `docs/v35-algorithm-development-report.md` (mtime
   2026-09-11 11:16:45, i.e., after the commit) still holds the rejected
   `NB_CANDIDATE_DEVELOPMENT_READY` rewrite, `git diff` 65+/89− against
   HEAD. It is not part of `654fa299`; it must be restored to the
   entry-HEAD content before any A19/A20 docs staging and must not be swept
   into the closeout commit.
6. Stale state fields are expected pre-A19 sequencing: D7-B `next_gate`
   still points at the D7-C packet freeze and D7-D `next_gate` at the
   BP interface; A19 owns the post-review updates. Not a defect.

## 9. Verdict restatement

`D7_BP_INTERFACE_READINESS_REVIEW_PASS`

Alternative A is exactly implemented; the producer tokens are exact and
numerically inert (independent baseline byte-equivalence, 0 mismatches);
every accepted-inventory cross-layer entry fails closed unless exactly
`CHECK_UPDATED` (independent runtime refusals, mixer never reached); warm
starts are refused and never inferred; the reviewed commit published no
real artifacts or decoder runs; the four test tiers reproduce A17's counts
and pre-existing failures; and the authorization/next-work gates are intact
with the two recordable discrepancies above (NBPolar exchange-copy push;
dormant D6 heavy-script gap) requiring main-thread action but not blocking
this interface acceptance.
