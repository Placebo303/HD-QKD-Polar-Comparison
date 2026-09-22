# D7-B independent Pre-RESULT review R2 (separate reviewer context)

Review mode: separate pass after revocation. Sources read: ONLY the new R2
root (`workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`),
the frozen D7-B contracts/code (`D7_B_EXECUTION_PACKET_R1.md`,
`D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`, `D7_B_PREREG_R1.md`, runner +
core + v35 read-only), the authorization record R2, and lifecycle commits.
The operator return was NOT used as evidence; every number below was
recomputed from the root CSV/JSON (or from git objects / read-only probes).
Nothing was edited; only this file is created. Zero decoder calls; root
untouched (sizes/mtimes identical across two reads; see R18).

## Recomputed root facts (from CSV/JSON, not from summary)

- Five files, zero subdirectories; sizes: command_log 111, decoder_records
  44743, manifest 1008, report 80, summary 449 (identical on re-read).
- CSV: 448 data rows, 30 columns; (tier,prior,seed,cap) uniqueness 448/448.
  Tiers {SINGLE_CHECK_D3,TREE_6,CYCLE_8,FULL_RANK_64}; priors
  {P99,P90,P60,PAIR}; seeds {2026091200..2026091203}; caps [1,2,4,8,16,32,90].
- Invoked 64 (all cap 1), NOT_NEEDED_AFTER_EXACT 384; 64+384=448.
- Invoked exact 64/64, syndrome_ok 64/64, status converged_exact 64/64,
  finite False 0, unsat nonzero 0, sym_err nonzero 0, crash strings 0.
- First-exact-cap: 64/64 cells at cap 1.
- Tractable post_err: SINGLE max 0.50033 / min 1.16e-16; TREE max 0.39966 /
  min 0.00689; CYCLE/FULL none stored; map_agree False 0.
- Walls: max per-call 0.00431 s; stored run wall 4.97012 s; harness outer wall
  5.396 s; exit 0; not 124. RSS column empty on all 64 invoked rows.
- Verifier (sole run, observed): `VERIFY_OK {'ok': True, 'problems': [],
  'records': 448, 'invoked': 64, 'terminal': 'D7_B_RESOURCE_OVERRUN'}`,
  exit 0.

## R01–R18

- R01 PASS: fresh §0 verbatim present in the R2 record; old UUID
  `0f1ad3ec-...` absent from the new root and cycle state, its R1 lifecycle
  (authorize `ce52ac5` / revoke `9e41e0d`, blocked disposition) immutable;
  exactly one R2 lifecycle (authorize `0327c65` → 1 invocation → revoke
  `3fe63ef`).
- R02 PASS: child argv equals the WSL-A1 frozen shape with the sole new UUID;
  no added args/PYTHONPATH/pipes. `command_log.txt` inner text
  (`scripts/... --out-root workspace/...<uuid>`) matches the runner's
  `sys.argv`-join convention. Harness PATH setup is interpreter resolution
  only (R1 equivalence), not an argv change.
- R03 PASS: root was absent before launch and after the auth commit; five
  files exactly as frozen; zero subdirectories; complete run (not partial),
  honestly so (exit 0 + full 448-row matrix).
- R04 PASS: manifest tiers/priors/seeds/caps/TREE_6-A1 (`[3,3,2]`,
  c0/c1/c2/coeffs literal) and budgets (420 / 120 s / 1500 s / 1800 s /
  2 GiB / 1e-10 / 1e-12) all match the frozen prereg/packet.
- R05 PASS: invoked 64 ≤ 420; 30-column schema intact; (tier,prior,seed,cap)
  unique 448/448; verifier independently confirms records 448 / invoked 64.
- R06 PASS: caps ascend per cell; only cap-1 invoked; exact at cap 1 in all
  64 cells; remainder `NOT_NEEDED_AFTER_EXACT` — early-stop semantics correct.
- R07 PASS: scheduled 64 / invoked 64 / not-needed 384 / budget-not-reached 0
  reconcile (64+384=448; 64 ≤ 420 so `budget_exhausted: false` correct).
- R08 PASS: exact/syndrome/iterations/unsatisfied/symbol-error accounting
  recomputed above matches stored rows (64/64 exact+syndrome, zero unsat /
  sym_err, all finite, all `converged_exact`).
- R09 PASS: tractable posterior maxima exceed 1e-10 on both exact tiers while
  MAP agrees everywhere; stored `tractable_violation: true` is the correct
  flag (violation disclosed, not hidden).
- R10 PASS: zero crashes, zero nonfinite, single status value; stored
  `crash_nonfinite: false` correct.
- R11 PASS: terminal independently recomputed as `D7_B_RESOURCE_OVERRUN`:
  null-RSS rows force `resource_overrun: true` under frozen T1–T9 priority,
  outranking the tractable-violation signal; stored terminal/flags agree.
- R12 PASS: `confirmed: false`, `partial: false`, `p99_fail: false` — no
  confirmation or partial predicate fires; P60/PAIR rows are exact and
  non-vetoing per frozen rule (no veto observed or required).
- R13 PASS: per-call max 0.00431 s ≤ 120 s; stored run wall 4.97 s ≤ 1500 s;
  outer wall 5.40 s ≤ 1830 s and ≥ stored wall; exit 0 with 124 flag false;
  `watchdog_timeout: false` consistent.
- R14 PASS: zero known RSS values (venv lacks psutil — pre-documented
  environment fact); the correct frozen mapping is the resource terminal, not
  a `<2GiB` comparison against unknown values. No hidden overrun.
- R15 PASS: scalar-only payload confirmed — zero CSV cells contain vector
  syntax (`[`, `;`, or >64-char payloads); `d_xhat/d_post/d_unsat` empty;
  proxy is `CAP_PREFIX_PROXY`; manifest/summary/report/command_log scalar;
  no forbidden Model-F/CAL/VAL/real/raw/VOID/formal content.
- R16 PASS: exactly one verifier invocation with the recorded VERIFY_OK
  outcome; verifier limits disclosed in the return (consistency-only,
  non-decoder, no pass conversion).
- R17 PASS: authorization false after revocation; single invocation only;
  no `--phase`/R1d/G1/G2 and no prohibited data/root activity; no retry or
  replacement UUID.
- R18 PASS: root read twice with identical names/sizes/mtimes; protected
  roots unchanged
  (`v72p2d5_g0/20260905_r2`, `v72p2d5_g1/20260907_r2`,
  `comparison_bench/outputs_comparison`, `results` — sizes/mtimes match
  pre-run record); lifecycle commits `0327c65`/`3fe63ef` local-only, no push
  performed.

## Verdict

`D7_B_PRE_RESULT_REVIEW_PASS_R2`

Consistency review only: the invocation, root, accounting, terminal mapping,
and lifecycle are internally coherent and contract-faithful. No scientific
pass, FER, leakage, key-rate, or qualification conclusion is made or implied.
Acceptance remains with the main thread (`INDEPENDENT_D7_B_RESULT_ACCEPTANCE_R2`).

(End of file — uncommitted; created solely by the reviewer context.)
