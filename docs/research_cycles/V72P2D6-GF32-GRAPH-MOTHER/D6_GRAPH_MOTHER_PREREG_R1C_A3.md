# D6 graph/mother — preregistration R1c-A3 (post-run verifier + terminal rework)

Status: `FROZEN_PREREG_R1C_A3`. R1 §§4–6/§8 science freeze carries forward
verbatim (arms/seeds/rows/prior/decoder/mother/selection/scientific terminal
thresholds unchanged). R1c mechanics + R1c-A1/A2 carry forward except the
verifier/classifier corrections below. The sole R1c-A2 §8 authorization is
consumed; this prereg authorizes zero decoder calls, zero `--phase`, zero
G1/G2/VAL/real, zero new scientific samples. Immutable root:

`workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`

Existing A2 evidence stays tied to commit `15f1de79`. A2 Pre-RESULT verdict
`D6_R1C_A2_PRE_RESULT_REVIEW_FAIL` stands; solidification stays blocked until
the A3 Pre-RESULT re-review (A3-06) passes.

## A3-00 amendment authority

The A2 contract ("any FAIL → VERIFY FAIL" over an n-agnostic semantic key) is
amended here via OpenSpec, not by silent patch. The corrected verifier keeps
the 15 mechanical checks but with corrected keys/stages (§V-A3-1…V-A3-4), and
reports stored vs recomputed terminal side-by-side (§V-A3-8). Terminal
disagreement is fail-closed at the *decision* layer (recomputed governs;
topology solidification forbidden; Pre-RESULT must route BLOCKED), not at the
mechanical exit code — so A3-05 stays a mechanical gate and A3-06 stays the
semantic gate. Without this split A3-05 would self-block and A3-06/07 would be
dead text; the split is frozen here explicitly.

## Frozen post-run rules (packet §3, eight items)

1. Scientific semantic identity is `(n, arm, seed, point, mode)`; `call_idx`
   remains independently continuous (`1..N`).
2. Canary recomputation uses only `n=64` rows with canary seeds
   (`2026091000..03`), points `f1.2`/`square`. Per-arm
   `f12_exact/f12_iter/sq_exact` with per-cell
   `app = (L1.exact and L2-APP.exact)`; a missing L2-APP mode (skipped
   placeholder, never persisted by flush) counts as `app=False`. Compared
   exactly against `summary.canary`.
3. Scaling recomputation uses only scaling seeds (`2026091100..03`), grouped
   separately by `n=128` and `n=256`, points `f1.2`/`square`. It reproduces:
   fallback dispatch (`best_T`/`best_M` from `selected_arms.json` must equal
   the dispatched scaling arms), per-width `sig`, per-width advancing via
   frozen `select_advancement` in width order 128→256 (stop-at-first-
   signaling-width), confirmation width, and terminal inputs.
4. Confirmation recomputation uses only confirmation seeds (`2026091010..25`)
   at the selected width. An empty confirmation stage is labeled
   `EMPTY_NOT_EVIDENCE` (INFO) and must not be presented as observed
   zero-crash safety: verifier asserts empty stage ⇔ empty
   `confirmation_counts` with zero tallies, and labels it EMPTY.
5. Any counted (`call_idx>=0`) attempted-cell crash (`crash=True`) or
   nonfinite (`finite!=True`) result has blocking precedence over every
   recovery/no-recovery scientific label. `call_idx=-1` placeholders are not
   attempted cells (flush never persists them; verifier ignores them
   defensively).
6. `ValueError('Check node requires degree >= 2')` is classified from the
   immutable evidence as an implementation/structure invariant failure unless
   a preregistered scientific outcome explicitly allowed that row. Recomputed
   terminal `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`. Other attempted
   crash/nonfinite → `D6_GRAPH_ATTEMPTED_CELL_INVALID`. Neither supports a
   topology-no-recovery claim.
7. The verifier is pure read-only over an arbitrary supplied root. It never
   rewrites summary/manifest to force agreement. Proven by a
   hash-before/after test on all six files.
8. The verifier prints both `stored-terminal` (from `summary.json`) and
   `recomputed-terminal` (A3 rules) plus `terminal-agreement True/False`.
   Disagreement is fail-closed per A3-00 (recomputed governs).

## A3-02 forensic plan (before code; fresh non-formal root; no decoder)

Script `workspace/a3_forensic_<uuid>/forensic_reconstruct.py` (task-owned
temp, uncommitted) reads only the six files plus structure/code evidence.
Report `D6_GRAPH_MOTHER_FORENSIC_R1C_A3.md` covers: uniqueness under old vs
corrected keys; exact duplicate groups under old key; counts by
`(n,arm,seed,point,mode)`; attempted/crash/nonfinite/error counts by width
and arm; canary / scaling-n128 / scaling-n256 / confirmation partitions;
selection/advancement/stop-width recomputation; stored vs recomputed terminal
under A3 rules; degree-failure source attribution:
(a) integer min-degree proof from `(zero_rows, row_degree_max,
row_degree_sumsq)` scalar evidence; (b) single-arm structure-only rebuild
(`build_support`, no decoder) for arms where (a) is inconclusive;
(c) transport/precondition exclusion via arm-perfect crash correlation +
same-pool success of other arms + `determinism_ok`. If the source stays
indistinguishable, label `NOT_VERIFIABLE` and keep the terminal blocked. No
guessing.

## A3-03 implementation scope (smallest correction)

Only `scripts/v72p2d6_graph_mother_development.py` (verifier path: corrected
key, stage-separated recomputation, crash-precedence + degree helper,
stored/recomputed reporting, EMPTY confirmation label) and
`comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (10 fake tests
below). No execution-generation change; no shared-helper change (mother
module untouched, so execution behavior is unchanged by construction). No
historical artifact edits.

Tests (`test_r1c_a3_*`, explicit fakes, fresh `tmp_path`, no real decoder):

1. `n_identity`: same arm/seed/point/mode at n128+n256 unique with `n`.
2. `true_duplicate_fails`: identical-`n` duplicate → VERIFY False.
3. `canary_isolation`: scaling rows cannot contaminate canary recompute.
4. `scaling_stages_ordered`: n128/n256 independently reconstructed in order.
5. `empty_confirmation_not_safety`: empty confirmation labeled EMPTY, not
   observed safety.
6. `crash_overrides_topology`: attempted crash/nonfinite → blocked
   recomputed terminal, overriding topology-no-recovery.
7. `placeholders_ignored`: `call_idx=-1` rows are not crashes/calls.
8. `disagreement_fail_closed`: stored/recomputed disagreement → agreement
   False with recomputed governing.
9. `a2_fixture_old_fail_new_classify`: tiny faithful A2-pattern fixture
   reproduces both old FAILs (n-agnostic key) before the fix logic and the
   corrected classification after it.
10. `verify_readonly`: six-file hashes identical before/after verify.

## A3-04/05/06/07 + A4 routing

- A3-04: `py_compile` (script + test file), focused D6 tests, seven-file
  non-perf regression (eight-file suite minus perf-v38; v38 skipped, recorded).
  Independent code review (own file, reviewer edits only it); at most one
  implement→review round-trip, else STOP. Commits: (1) prereg/OpenSpec
  [this file + `R1C_parallel_revision.md` A3 delta + `tasks.md` A3/A4 tasks],
  (2) implementation+tests+forensic report, (3) independent review. No push.
- A3-05: after review PASS, exactly once
  `python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b --verify`
  (read-only, zero decoder calls). Capture output+exit. FAIL → STOP, no patch,
  no rerun.
- A3-06: independent read-only `D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A3.md`;
  verdicts `…_PASS_BLOCKED_RUN` (expected: degree failures invalidate the
  scientific terminal; solidifies as implementation/structure-blocked attempt,
  never topology evidence), `…_PASS_SCIENTIFIC_RESULT`, or `…_FAIL` (blocks
  everything). No verdict authorizes rerun/successor.
- A3-07: FAIL → evidence stays uncommitted/immutable, report, stop.
  PASS_* → append-only operator-return correction (never erase original
  failure/stored terminal) + `D6_GRAPH_MOTHER_RESULT_R1C_A3.md`
  (stored vs recomputed, strongest allowed claim) + one scoped evidence
  commit (`git add -f` six files + operator return + A2 FAIL + A3
  review/result/forensic + state + append-only memory/log). Auth stays false,
  G2 absent, no accepted-result mark, no push.
- A4 starts only after A3 closeout commits, fully separate track (§10).

## Stop rules

Any task ambiguity → STOP, return to main thread. Any production-code test
failure → STOP (no mixed-version evidence). Reviewer blocking finding →
single rework max, else STOP. Forbidden: decoder/retry/second root/`--phase`/
G1/G2/VAL/real/six-file-root edits/science-param changes/broad-stage/clean/
reset/push; V35/perf-v38/CRLF dirt left untouched, exact-path staging only.
