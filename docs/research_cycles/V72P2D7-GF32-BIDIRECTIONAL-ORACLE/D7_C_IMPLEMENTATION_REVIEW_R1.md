# D7-C implementation review R1

Verdict: D7_C_IMPLEMENTATION_REVIEW_PASS

## 0. Scope and independence

- Independent implementation review of commit `391fc6b0` (three new files)
  against the frozen R1+A1 contract: `D7_C_PREREG_R1.md`,
  `D7_C_EXECUTION_PACKET_R1.md`, all four OpenSpec planning files, task packet
  R1 §5–§9 and A1 §A1.4 (A1 wins on conflict), `cycle_state.yaml`.
- Branch `formal-ir-v72p1-addendum-clean`; `git diff --name-only
  0c304875..391fc6b0` is exactly the three new files.
- Independence: reviewer run by a different agent instance than the
  implementer. Zero decoder binding, zero Model-F binary content read, zero
  production decoder call, zero authorized run, zero root/UUID creation.
  Protected roots inspected by names/sizes/mtime only. The only repository
  write is this document; reviewer scratch artifacts live in
  `/tmp/opencode/d7c_review/`.
- Reviewer-side execution: full new suite re-run, D7-A/D7-B alone,
  4-file and 3-file collection, direct `py_compile`, independent literal-tensor
  prior recomputation from prereg §6 (own reference code), fake 128-call loop
  with reviewer-owned joint/blocks/mothers, verifier isolation with
  decoder/Model-F/mother/estimator callables poisoned, self-consistent
  truncation experiment, protected-metadata snapshot diff.

## 1. Frozen constants, estimator and geometry

| Item | Contract | Implementation evidence | Verified |
|---|---|---|---|
| Estimator | `d5.prepare_model_f_prior_candidate(counts_ab, p_b)` | call at `v72p2d7...py:448`; `_ESTIMATOR_ID` L158 | yes; `inspect.signature` default `lam == LAMBDA_STAR` |
| Rejected estimator | `prepare_model_f_prior`/`build_f_model` never called | grep: no call sites; only `..._candidate`/`..._concentration` | yes |
| `LAMBDA_STAR` | 137.3823795883264 | L78; equals D5 L46 | yes |
| Model-F root | `workspace/v72p2d5_model_f_input/20260907_r1` | L57; equals D5 `MODEL_F_INPUT_FORMAL_ROOT` L85 | yes |
| n | 64 | L54, identity `n` | yes |
| Seeds | 2026091300..2026091315 | L64; first/last identities checked | yes |
| f | `(1.0, 1.2)` | L59 | yes |
| L1/L2 rows | 49/59, 43/52 | L60–61 | yes |
| Graph seeds | 2026090501 / 2026090502 | L65–66 | yes |
| Mother call | `build_dv3_nested_support(64,64,49,2026090501)` + `assign_gf32_coefficients(sup,2026090501,None,64)`; (43 / ...502) | L364–372 | yes; byte-equal to D5 `build_dv3_nested_mother(64,64,49,2026090501,None)` / `(64,64,43,2026090502,None)` |
| Decoder | cold, `max_iter=90`, `damping_alpha=1.0` | L80–81; bind L1197–1199 → D5 L2453–2475 (`warm_beliefs=None`, `field=None`) | yes |
| Floor | `DECODER_FLOOR = 1e-15` | L79 | yes |
| Terminal strings/priority | R1 §10 T1–T11 | L95–110 | exact match |
| Labels | two tokens only | L119–121 | exact match |

## 2. Prior and pairing independent recomputation

Reviewer reference code (`/tmp/opencode/d7c_review/prior_ref.py`) was written
from prereg §6 and compared to `condition_prior_qn` / `decoder_prior`:

- literal joint `(32,32,7)` with a zero-mass u1-plane, block of 7 positions:
  all four priors max|diff| = 0.00e+00 vs reference; every column sums to 1.
- zero-mass oracle slices: reference columns u1_true=5 -> uniform 1/32;
  implementation identical (function `_normalized_oracle_slice` L475–484).
- boundary: `decoder_prior(qn)` == `max(qn.T,1e-15)` row-renormalized, exact
  (atol 0); positive entries, rows sum 1; one-hot marginal yields
  `1 - 31*1e-15/(1+31*1e-15)` and min 1e-15 (single floor at boundary,
  `decoder_prior` L514–516; no other floor/clip in source).
- swapped-axis negative controls on a clean second tensor: L1-vs-L2 marginal,
  wrong-u oracle axes and layer-transposed oracle all differ >1e-6 (matches
  C04 and the reviewer's own arithmetic).
- marginal/oracle pair sharing: reviewer `prepare_inputs` + `execute_calls`
  with reviewer-owned `(32,32,1024)` joint, blocks and fake mothers produced
  exactly 128 calls; for each `(i, i+1)` and `(i+2, i+3)` pair the H prefix,
  syndrome and block are array-equal and only the prior differs; dispatched
  priors are `(64, 32)`, strictly positive.
- axis conventions match prereg: `J[u1,u2,b]`, L1 marginal `sum_u2` (axis=1),
  L2 marginal `sum_u1` (axis=0), `L2_ORACLE_U1` uses
  `j[u1,:,bob].T` (L509–510 comment documents advanced-index layout).

## 3. Call matrix and evidence semantics

- `frozen_identities()` (L318–338) returns exactly 128 tuples
  `(call_idx 1..128, f, seed, condition, layer, rows, n=64)` in the frozen
  order `for f: for seed: 4 conditions`; boundaries verified (call 1 =
  f1.0/seed 2026091300/L1_MARGINAL/49; call 64 f1.0 L2_ORACLE_U1; call 65
  f1.2 L1_MARGINAL/59; call 128 f1.2/seed 2026091315/L2_ORACLE_U1/52);
  128 unique keys.
- No early-success stop, no replacement, one decode per identity: loop
  L657–697 dispatches each identity once; reviewer captured 128 decodes /
  128 identities; `stop` only on watchdog/crash/resource.
- 16 sampler calls independent of f: `prepare_inputs` samples once per seed
  into `blocks` (L458–461); the call loop reads `blocks[seed]` and never
  re-samples or keys by f.
- exact/syndrome recompute: `exact = array_equal(x_hat, x_true)` (L581);
  `observed = d5._gf32_syndrome(h_prefix, x_hat)` and
  `unsatisfied = count(observed != syndrome)` (L582–584);
  `syndrome_ok = reported AND unsatisfied == 0` (L584). `exact` is never
  set/upgraded from syndrome anywhere; paired rows count `exact` only, with
  separate `paired_syndrome_*` fields (L765–783).
- `symbol_errors` / `unsatisfied_checks` (L585, L583) match prereg §9.
- labels: `conditioned = iterations > 0`; label =
  `CHECK_UPDATED_CURRENT_BELIEF` iff conditioned else
  `PRIOR_ONLY_CURRENT_BELIEF` (L591–592); no other label token; the only
  posterior/APP occurrences are the verifier's forbidden-token check
  (L1071–1072).
- persistence: writer emits only `RECORD_FIELDS`/`PAIRED_FIELDS`
  (L125–141) plus manifest/summary/report/command; `write_root` refuses
  unknown fields and non-scalars (L905–921); no block/prior/syndrome/belief
  vectors written. C07 additionally proves block vectors absent.
- no `final_beliefs -> other layer` path: `final_beliefs` appears only in
  result parsing (L537/L543) and `_belief_diagnostics` (L559–570); no prior,
  APP or cross-layer consumer. Module imports only stdlib+numpy+D5 (L24–47);
  no interface-rework import.

## 4. Stratum classification and terminal priority

- `classify_stratum` (L737–748) reproduces R1 §10 exactly and in order:
  strong requires `oracle_only >= 4` AND `marginal_only <= 1` AND
  `oracle_exact >= 4` AND zero crash/nonfinite; then
  `oracle_exact <= 1 AND marginal_exact <= 1`; then `marginal_exact >= 12`;
  else ambiguous. Boundary probes at 3/4, 1/2, 11/12 and the strong-over-
  marginal precedence verified (C09; reviewer read + test rerun).
- incomplete strata: `complete` requires 16 marginal + 16 oracle records and
  zero crash/nonfinite (L791–798); otherwise label is `""` with partial
  counts (never fabricated). Nonfinite call blocks the label (C09).
- `classify_terminal` (L844–871) enforces T1–T11 first-applicable order:
  pre-block, watchdog, crash, resource, incomplete, then T6 =
  any f with strong L1 AND strong L2, T7 strong L1 only, T8 strong L2 only,
  T9 any marginal stratum, T10 all four no-recovery, T11 mixed. Cross-f
  strong-L1+strong-L2 case correctly yields mixed, not T6.
- all labels recorded under a higher terminal: paired rows are computed from
  whatever records exist before terminal selection (L1291–1292); completed
  strata keep labels, incomplete keep `""`.

## 5. Budgets, guards, six-file writer and verifier

- budgets L83–88: 128 cap, per-call 120 s, stored 1500 s, outer 1800 s + 30 s
  grace, RSS < 2 GiB. `execute_calls` enforces in order watchdog > crash >
  resource (L688–694), sequential single loop, no retry/replace/resume.
- RSS: stdlib `resource.getrusage(RUSAGE_SELF).ru_maxrss` × 1024
  (`get_rss_bytes` L275–294), `_probe_rss_valid` rejects None/nonfinite/non-
  positive (L297–311); run blocks pre-call on invalid probe (L1271–1276) and
  on existing target (L1267–1268); no psutil, no new dependency.
- six-file writer `write_root` (L942–984): exactly `SIX_FILES` L123–124,
  refuses existing root, refuses a directory containing subdirectories,
  refuses unknown/non-scalar record fields; no subdirectories created.
- CSV schema exactly prereg §9: `RECORD_FIELDS` L125–131 and
  `PAIRED_FIELDS` L132–141 match the prereg lists field-for-field and order.
- verifier `verify_root` (L1119–1190) is read-only and recomputes from the
  six files: file set, no subdirs, manifest frozen constants
  (L1003–1039), positional identity/schema semantics (L1042–1097), paired
  rows (L1160–1167), terminal (L1168–1171), calls_completed, strata and
  stored_wall. Reviewer poisoned `bind_historical_decoder`,
  `_load_model_f_input_or_blocked`, `build_dv3_nested_support` and
  `prepare_model_f_prior_candidate` to raise: `verify_root` still returned
  `ok=True` — no decoder/Model-F/estimator reachability. C16 confirms
  duplicate, missing/unpaired, tampered exact/syndrome/paired/terminal/
  manifest and extra-file detection; reviewer swap of two records at equal
  count was detected by identity mismatch.

## 6. Isolation and CLI

- Core import L36–47 is package-first with a sibling-file fallback; no
  module-level file I/O or decoder bind; `_EXECUTION_CONSUMED` is set only
  when the production bind succeeds (L1283–1286).
- Runner L19–34 binds repo-local source from `__file__` (external cwd safe);
  `main` L50–97: `--help` exits in argparse; `--dry-run` prints the frozen
  128 identities with no state/Model-F/decoder/root (L56–64); root-shape
  refusal is pure (L68–73); unauthorized state refuses (L79–81);
  `--model-f-root` must equal the frozen root before any run (L85–87);
  `run_bidirectional_oracle` re-checks authorization (L1265) before target
  existence (L1267) and Model-F load (prepare_inputs L441–449).
- `validate_production_out_root` (L237–254) requires a direct fresh child of
  `workspace/` named `d7_c_bidirectional_oracle_<uuid>`; protected
  formal/outputs trees refused (L257–268). DI/qualification temp roots are
  intentionally exempt and documented (L240–242); the CLI always validates.
- frozen future command shape
  (`timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py
  --model-f-root workspace/... --out-root workspace/d7_c_bidirectional_oracle_<uuid>`)
  is accepted by the parser and gated as above.

## 7. Test-quality spot check (C01–C20)

| Test | Core assertion (not vacuous) |
|---|---|
| C01 | identity boundary dicts at 1/4/64/65/128, unique keys, condition order, rows/n |
| C02 | 16 sampler events before first decode, once per seed, f-pair priors array-equal |
| C03 | all four formulas vs literal stack references; zero-mass uniform fallback |
| C04 | four wrong-axis variants differ >1e-6 from correct priors |
| C05 | boundary values vs `max/T` reference; monkeypatched `_floor_renorm` count == 128; single call site in source |
| C06 | `build_mother` byte-equals D5 `build_dv3_nested_mother`; per-call H prefix equality |
| C07 | all six files free of block vectors; oracle truth changes only oracle prior |
| C08 | pair H/syndrome array-equal, priors differ, shapes, no `warm_beliefs` |
| C09 | every threshold boundary, precedence, incomplete/nonfinite label suppression |
| C10 | T1–T11 priority matrix + run-path L1/L2/none/marginal terminals |
| C11 | 128 calls exactly; crash at 40 -> 40 records, status `crash:`, no retry |
| C12 | 120.0 vs 120.0001; 1500.0 vs 1500.001; RSS == 2 GiB -> resource stop |
| C13 | 123456 KiB -> bytes; invalid probes block with zero events and no root |
| C14 | iteration 0/3 labels and flags on all 128 records; forbidden tokens absent |
| C15 | exact six-file set, no subdirs, no overwrite, extra/non-scalar field refusal |
| C16 | 8 tamper variants (dup/missing/scalar/syndrome/paired/terminal/manifest/extra) |
| C17 | help/dry-run from repo and external cwd; unauthorized CLI rc 3, no root |
| C18 | external-cwd sentinel reaches exactly 1 decoder call, 0 loader, no root |
| C19 | workspace and Model-F metadata unchanged; G2/R1d/D7-C absent; auth false |
| C20 | py_compile + D7-A 14 / D5 165 / D7-B 29 (two stale root-glob tests excluded) |

## 8. Scope, dirt and regression re-verification

- `git show --stat 391fc6b0` = the 3 new files only (1321 + 1039 + 101);
  `git diff --name-only 0c304875..391fc6b0` identical. No existing module,
  test, doc or script modified.
- Worktree: no dirty entry for the three new files. `git diff
  --ignore-cr-at-eol --name-only` lists exactly three pre-existing
  content-dirty files (`docs/research-cycle-sop.md` mtime 19:05,
  `docs/v35-algorithm-development-report.md` 20:07,
  `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`
  04:57, all before the 23:17 implementation commit); the remaining ~1965
  entries are CRLF-only. No clean/reset/stash used.
- Reviewer rerun:
  `.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py
  -q -p no:cacheprovider --basetemp=/tmp/opencode/d7c_review/bt_new`
  -> `20 passed` (58.39 s).
- D7-B alone -> `2 failed, 29 passed` (24.24 s); both failures are the
  pre-existing `test_launch_l04...` / `test_launch_l12...` root-glob asserts
  against the accepted D7-B R2 root `c605d1e6...`; neither imports D7-C.
- D7-A alone -> `14 passed`. D5 is asserted `165 passed` inside C20.
- Combined-collection claim reproduced: 4-file run -> `199 collected,
  1 error`; the same 2-file/3-file run without the new module -> `179
  collected, 1 error`, `ModuleNotFoundError: No module named
  'comparison_bench.formal_ir'` -> pre-existing namespace collision.
- `py_compile` of the three files -> OK.

## 9. Protected-state checks

- `workspace/` listing and Model-F / D7-B R2 / G0 / G1 / D6 file
  (name,size,mtime) snapshots byte-identical before/after all reviewer runs.
- No `workspace/d7_c_bidirectional_oracle_*` root; no reviewer-created root
  anywhere in the repository (scratch only in `/tmp`).
- `workspace/v72p2d5_g2` and `workspace/d6_graph_mother_r1d_*` absent; no new
  UUID in any D7-C artifact (only the D7-B provenance UUID appears).
- `cycle_state.yaml`: no UUID, no attempts/results fields;
  `d7c_execution_authorized`, `decoder_executed`, `result_created`,
  `formal/synthetic/real_execution_authorized`, `g1/g2_authorized` all false.

## 10. Non-blocking observations

1. Per-call watchdog is post-hoc: a call exceeding 120 s is recorded and the
   run stops, but a call that never returns is only bounded by the outer
   1800 s GNU timeout. This satisfies the frozen stop semantics; hard in-call
   interruption is not required by R1 and would need signals/threads.
2. `_EXECUTION_CONSUMED` is set after `bind_historical_decoder()` returns; a
   bind-time exception leaves the in-process one-shot guard unset. The
   `cycle_state.yaml` key remains the authoritative single-use gate.
3. `verify_root` accepts a fully self-consistent truncated root terminalized
   `D7_C_INCOMPLETE_CALL_MATRIX` (reviewer demonstration: 96 records with
   rewritten paired/summary -> `ok=True`). `T_INCOMPLETE` is unreachable from
   the run loop; the verifier is an internal-consistency checker by contract,
   so this is not a defect, but it cannot detect a forged-but-consistent
   truncation.
4. The verifier recomputes terminal/strata/calls_completed/stored_wall but
   not every secondary `summary.json` field (`peak_rss_bytes`,
   `calls_remaining`, `watchdog_timeouts`, `stop_terminal`).
5. `openspec/.../tasks.md` checkboxes remain unchecked after T2–T4; only
   T0/T1 were in the planning commit, and T5–T7 are future. Closeout should
   update them (docs-only).
6. C20 excludes the two stale D7-B launch tests (root-glob asserts) and
   asserts `29 passed`; the fully green D7-B suite is not reachable while the
   accepted R2 root exists. This matches H12 "PASS or exact unrelated
   baseline isolated".

## 11. Blocking assessment

No blocking defect found. All 10 mandatory review areas match the frozen
R1+A1 contract; C01–C20 are real, non-vacuous and green; the independent
literal-tensor recomputation deviates from the implementation by 0.00e+00;
the reviewer-side fake 128-call run reproduces the frozen order and pairing
semantics; verifier isolation and protected-state immutability hold. The
observations in section 10 are documented limitations of the frozen design or
non-scientific bookkeeping, none of which can alter a D7-C numerical or
scientific conclusion. This review records no decoder execution and grants no
authorization; the Pre-EXECUTE review and explicit user authorization remain
separate mandatory gates.
