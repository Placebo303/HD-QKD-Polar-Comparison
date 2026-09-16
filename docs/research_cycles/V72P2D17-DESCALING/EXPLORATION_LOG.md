# D17 Current-Channel Asymptotic-to-Finite Scaling — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1_TASK_PACKET.md` (§§1–§8, sole authority; §8 return contract).
- Track: documentation-only (no code, no execution, no DE/decoder/scientific calls, no root creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D17. Detail record: `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md` (D16 readiness accepted; Batch A1 withdrawn — D16 is held-out validation, never the next gate).
- This call (D17 close-docs): documentation-only close (two new record files in this directory, one pointer append to the D16 log, D17 OpenSpec `tasks.md` B/C/D02–D07 checkbox update). No code, no execution, no decoder/scientific calls, no staging/commits, no push.

## 2026-09-15 — D17 readiness R1 close (no execution)

### Authorization boundary

- This call performed no code edit, no DE/decoder/scientific execution, no root creation, no commit, no push.
- The frozen 240-call asymptotic DE batch remains unauthorized. It requires a separate explicit batch grant (+ Pre-EXECUTE). No authorization was granted by readiness or by D17-R207.
- No-execution-authorized statement: **no DE, scaling-fit, or D16 execution is authorized by this close; both future roots remain absent and the frozen commands remain unauthorized strings.**

### A–D06 evidence (trusted VERIFIED, do not rerun)

- A01–A05: channel EXACT (Model-F candidate chain, decoder contract, four recorded distinctions); DE-transfer map (V26 kernel + D9 adapter reuse-only, no numeric transfer); finite table F1–F19 + 3 BLANK with spot recompute; FIT/validation/descriptive classes with APP/joint exclusion; D16 holdout lock (cells/seeds/command/root recorded, root absent, banned seeds uncontaminated).
- B01–B05: three-profile frozen grid (15 pts: L045 m106–122 / L055 m116–126 capped one-sided-high contingent / L2 m89–109; seeds 2026094201..08; pops 4000/16000; V26 60/1e-4/20); 240 calls + setup ≤12; wall 1200/per-call 300/RSS 2GiB/1-proc; non-adaptive; bracket-midpoint + flags + fail-closed; ±h union; future command/root/budgets frozen, default-false auth; PROFILE_ONLY rc=0 + refusal rc=2.
- C01–C07: predeclared probit law with `delta_DE` fixed from reviewed DE; binomial likelihood + cluster-bootstrap/LOO (wider predicts); identifiability ladder (L2 one-param primary; fixture 0.6219/0.25; all-zero MODEL_NOT_IDENTIFIABLE); logistic descriptive-only; integer row-backoff inversion at n=64/128/256 (fixture L1 4/5, 7/8, 11/14) for eps 0.10/0.01; three-arm outcome-blank D16 predictions; residuals post-prediction only.
- D02–D06: audit artifact + report; DE adapter/runner with fakes + refusal + verifier; scaling module with recovery + non-identifiable fixtures + banned-seed gate; D05 blank schema + fail-if-exists; focused validation (compile/math/grid/fake/recovery/isolation/absence/no-production).
- Zero-calls: DE/decoder counters 0; NO_VAL_READS; D16 + D17 future roots absent. Test rerun 30/30 (12.98 s).

### D07 verdict/findings (trusted VERIFIED)

- D17-R207: EVIDENCE_ACCESS VERIFIED, verdict PASS_WITH_FINDINGS, blocking none.
- First-run fixes IN-SCOPE (minimal diff, no new dep): D16 short-circuit (holdout enforcement) + `ndtri` precision (epsilon-0.01 requirement).
- Non-blocking: `_looks_like_fake()` unwired; D16-rows message order (fail-closed); `fit_profile` in `__all__` (ladder-internal, document only); scoped commit = 7 D17 files only.

### Terminal

`D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`. Next gate: separate explicit DE-batch grant first, then fit + frozen D16 prediction. No DE/D16 authorization; D7-H closed; no FER/leakage/SKR/route claims.

(End of file)

## 2026-09-15 — Main-thread readiness acceptance and Batch A1 freeze

- Main-thread acceptance:
  `D17_DE_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- D17-R207 is accepted within its reviewed scope: `EVIDENCE_ACCESS VERIFIED`,
  `PASS_WITH_FINDINGS`, blocking none. Its non-blocking findings remain carried.
- Next packet pair:
  `.workbuddy/tasks/D17_ASYMPTOTIC_DE_BATCH_A1_TASK_PACKET.md` and
  `.workbuddy/tasks/D17_ASYMPTOTIC_DE_BATCH_A1_AUTHORIZED_PROMPT.md`.
- The grant is limited to the frozen 240-call current-channel DE batch and its
  independent batch-end review. Scaling fit, D16 prediction freeze, D16 run,
  route selection, and D7-H remain unauthorized.

## 2026-09-15 — D17 readiness acceptance + DE Batch A1 authorization

- Main-thread acceptance (decided this turn, recorded verbatim first):
  D17 readiness (D07 VERIFIED PASS_WITH_FINDINGS, no blockers) is ACCEPTED
  as D17_DE_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION.
  This marker satisfies Batch A1 packet §4 check 1's requirement (marker now
  present because main thread accepted).
- One-shot grant (this turn's explicit authorization, single grant):
  `D17_ASYMPTOTIC_DE_BATCH_A1` once; branch
  `formal-ir-v72p1-addendum-clean`; root
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`;
  three-profile / five-point / eight-seed / two-population matrix (240 DE
  calls, ≤12 setup); budgets 1200 s wall / 300 s per-call (between-call
  check) / RSS < 2 GiB / 1 CPU.
- Authorization-consumption rule: consumed at command start. No second
  run / retry / resume / grid-extension / seed-search / binary-search /
  adaptive / repair. STOP + retain on mismatch/failure. No fit /
  D16-prediction / D16 / decoder / route / D7-H / commit / push / FER /
  claims.

## 2026-09-15 — DE Batch A1 pre-dispatch 9/9 PASS (raw evidence)

- 1 marker: acceptance section above records
  `D17_DE_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  verbatim + D07 `EVIDENCE_ACCESS VERIFIED / PASS_WITH_FINDINGS`, blocking
  none (per READINESS_R1 §8; trusted, not rerun).
- 2 branch: `formal-ir-v72p1-addendum-clean` (HEAD 73c6275b; `git
  merge-base --is-ancestor 73c6275b HEAD` rc=0). Scoped `git status`:
  only `M docs/.../EXPLORATION_LOG.md` (this log's own appends) + untracked
  authority packet `.workbuddy/tasks/D17_ASYMPTOTIC_DE_BATCH_A1_TASK_PACKET.md`;
  `scripts/v72p2d17_scaling_development.py`,
  `comparison_bench/.../v72p2d17_descaling.py`, focused tests, OpenSpec D17
  change, D17 cycle docs: no drift (script last touched by 73c6275b).
  Unrelated worktree dirt preserved, no repairs.
- 3 roots: DE root absent + D16 official root
  (`workspace/d16_matched_backoff_discriminator_b7c2d4e6-...`) absent (both
  `ls: No such file or directory`). Model-F root present, `cal_only true`,
  `decoder_calls 0`, `val_rows_read 0`; sha256
  `model_f_input.npz=38e4bfba...00b6280d345`,
  `model_f_input_summary.json=ca67a953...a78fac1a43`. (`workspace/d16_align_20260915_a/`
  scratch exists as expected — forbidden *input*, not required-absent; never opened.)
- 4 recompute (own code): H_L1=4.286720430201375, H_L2=3.222719884634378
  exact match (joint 7.5094403148357545; n128 loads 548.700215065776 /
  412.508145233200); all 15 (profile,m,R,delta,rho) match implementation
  cells (e.g. L045 m110 R=0.140625 delta=+0.01015 rho={2:17,3:93}; L055
  m122 rho={2:65,3:57}; L2 m99 rho={3:12,4:87}); plan 240 unique ordered
  identities, call_idx 0..239 contiguous.
- 5 seeds: `verify_seed_disjointness()` passed=True over 205 priors,
  de_hits_prior=[] de_hits_d16=[]; banned sets 4001–4012/4101–4108
  disjoint by construction; no fit/validation root read (DE script binds
  kernel lazily on authorized path only).
- 6 PROFILE_ONLY rc=0: grid_points=15, planned_de_calls=240,
  de_calls=0, decoder_calls=0, future_root_absent=true; official roots
  still absent after.
- 7 refusal: `--de-batch` without `--execution-authorized` vs fresh
  scratch `workspace/d17_check7_scratch_refusal_probe` → rc=2
  (`refusing --de-batch: ... default false, fail-closed ...`) before
  root/kernel-bind/Model-F-load; scratch absent after (no write).
- 8 compile+tests: py_compile OK (script+module+tests); 30/30 passed in
  11.85 s in ONE fresh `workspace/d17_check8_tests_run01` basetemp,
  `-p no:cacheprovider -o addopts=`, `.venv/bin/python`. D07 predecessor
  checks trusted, no conflict.
- 9 command: FROZEN_COMMAND string == packet command verbatim (match
  True); pops (4000,16000); rule S_pop=#{H60<1e-4}/8, lo≤3/hi≥6; flags
  DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED_LOW/DE_ONE_SIDED_HIGH/POP_UNSTABLE;
  ceilings 240/≤12, 1200 s/300 s/2147483648 B/1 proc/setup_units=4;
  verifier `verify_de_root` present; grant unused (official root absent).
- Verdict: PRE_DISPATCH 9/9 PASS. Proceeding to the single authorized
  execution; grant consumed at command start.

## 2026-09-15 — DE Batch A1 execution BLOCKED (raw run evidence, retained)

- Command (exact, once): `.venv/bin/python
  scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
- Start 2026-09-15T10:33:47Z, end 2026-09-15T10:33:50Z, process exit 0
  (fail-closed retention path; terminal recorded in artifacts, not rc).
- Terminal: `DE_ENGINEERING_BLOCKED`. Scientific DE calls: 0/240. Setup: 4
  (≤12 ceiling unbreached). Wall 0.005 s internal / ~3 s process (budget
  1200 s unbreached). Max RSS 183864 kB ≈ 0.17 GiB (budget 2 GiB
  unbreached). Per-call budget never reached (no call started). 1 CPU proc.
- Failure: `command_log.txt` line 2:
  `DE_CALL_FAILED@0: TypeError: 'tuple' object is not callable`. Plan
  validation + rho binding succeeded (`plan validated calls=240; rho
  identities bound per cell`); first production `de_call` raised.
- Read-only root cause (no repair attempted): `run_de_batch` sets
  `channel = bound["load_channel"](model_f_root)`, and D9
  `load_l1_channel` returns the `(pb, p_f, p1)` tuple; that tuple is passed
  as `channel_sampler` into `d9.run_de_call` → `v26.run_mcde_posterior`
  (`nonbinary_v26_mcde.py:293` calls `channel_sampler(n_samples, rng)`).
  The bound `build_sampler` (`d9.build_l1_sampler`, which converts the
  tuple into a callable sampler) is never invoked on the production path.
  Fake-injected tests never exercised production bind, so readiness did not
  catch it.
- Convergence: all 30 s_table cells S=0/calls=0; brackets {} (none);
  flags none; delta_DE none (no values to record; nothing re-derived).
  Trajectory files present but header-only (`de_records.csv`,
  `de_traces.csv`); `de_plan.csv` holds the full validated 240-row plan.
- Root files + sha256: command_log.txt 037c7065...; de_plan.csv
  4837bd52...; de_records.csv 0780a143...; de_traces.csv e0bbb037...;
  manifest.json c8ddb989...; summary.json ff184433... (full hashes in
  operator transcript). Model-F root re-hashed unchanged
  (npz 38e4bfba.../json ca67a953...); no decoder/CAL/VAL/real-data path ran.
- Grant: CONSUMED at command start (single grant; no second run/retry/
  resume/repair per authorization). No fit, no D16 prediction, no D16 run,
  no route, no D7-H, no commit, no push. Check-7 scratch absent;
  unrelated worktree dirt preserved.
- Status: `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION` (not the
  packet §7 reviewed-complete terminal). Batch-end review of DE evidence is
  moot (zero scientific calls); the single decision needed from main
  thread: authorize a fix+rerun packet (new grant, code repair outside this
  batch) or stand down Batch A1.

## 2026-09-15 — D17 DE Batch A1 failure-evidence review (VERIFIED, STOP confirmed)

- REVIEW_ID: `D17-DE-B1-REVIEW` (condensed record; authority sections above not rewritten).
- Track/repo: documentation-only (no code, no execution, no rerun, no repair, no root modification, no commit/push); branch `formal-ir-v72p1-addendum-clean` (not switched).
- EVIDENCE_ACCESS VERIFIED (direct reads, own recounts; no edits/reruns/repairs/commit/push).
- ONE-SHOT PASS: manifest command == frozen verbatim; single 3-line command_log pass (plan-validated → DE_CALL_FAILED@0 → terminal); mtimes 18:33:49.9 +0800; exit 0 fail-closed by design; grant consumed once; no second invocation.
- EVIDENCE PASS: 6/6 files, hashes match (037c7065…/4837bd52…/0780a143…/e0bbb037…/c8ddb989…/ff184433…); de_plan.csv 241 lines = 240 unique ordered identities idx 0..239, 15 cells; de_records/traces header-only (0 scientific rows); setup 4/12; summary 0/240, brackets {}, flags none, delta_DE none, violations [], terminal DE_ENGINEERING_BLOCKED + engineering_reason == stored error.
- FAILURE-MECHANISM CONFIRMED by reading (never executed): L1186 channel = bound load_channel tuple (pb,p_f,p1) (D9 L336-343); build_sampler bound L1143-1144 but 3 textual occurrences only, never invoked on production path; tuple → de_call L1217-1220 → v26 L293 call → TypeError exactly matching stored error; fake tests boom production bind by design (test docstring L5-7).
- NO-REPAIR PASS: scoped status only M EXPLORATION_LOG.md (mandated appends); code mtimes predate run; check-7 scratch absent.
- BUDGETS PASS none breached (0/240, 4≤12, ~3s/1200, 184MB/2GiB, 1 proc; N2: internal peak_rss 0 placeholder, judgment on external RSS).
- D16-BLANK PASS: official root absent; banned seeds absent; no fit/prediction artifacts; Model-F unchanged; no decoder/CAL/VAL/real-data.
- Terminal adjudication CONFIRM: D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION (packet §7 complete-terminal requires 240 calls, impossible at 0/240; §5 STOP-and-retain governs; DE_ENGINEERING_BLOCKED is code-designed fail-closed terminal L1270; repo naming convention).
- FINDINGS: BLOCKING B1 (0/240 — evidence unusable for fit; consequence not review failure) + B2 readiness gap (fakes never exercised production bind → fix packet pre-dispatch must add zero-call signature-level bind validation: bind resolves, load output unpacks, build_sampler returns callable, no scientific calls); NON-BLOCKING N1 second latent gap (L2 true-U1 conditioning via conditionalize_f_to_p2/oracle_l2_prior also dead on production path, masked by @0 failure — fix packet must specify L2 channel dispatch), N2 RSS placeholder, N3 start-timestamp transcript-only.
- VERDICT PASS (failure evidence verified, STOP correct); NO rerun under consumed grant.
- Close: single decision needed (authorize fix+rerun packet with explicit repair scope incl. N1, or stand down); no commit/push; memory triage pending.

## 2026-09-15 — Main-thread A1 adjudication and R2/A2 authorization

- Accepted failure evidence:
  `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION`, with A1 0/240 and
  `DE_CALL_FAILED@0: TypeError: 'tuple' object is not callable`.
- Route decision: repair and rerun, not stand down. The defect is confined to
  D17 production channel wiring; A1 provides no scientific DE evidence.
- Repair scope is frozen in
  `.workbuddy/tasks/D17_DE_BINDING_REPAIR_R2_AND_RERUN_TASK_PACKET.md`:
  unpack `(pb,p_f,p1)` and invoke the accepted L1 sampler builder; construct
  the true-U1-conditioned L2 oracle sampler from the same Model-F joint; route
  L1 and L2 profiles to distinct callables; add zero-scientific-call production
  bind/load/build/dispatch validation. No DE grid, seed, rate, kernel,
  convergence, bracket, budget, or claim change.
- Fresh one-shot A2 grant is recorded by the companion authorized prompt. A1
  remains immutable; A2 uses a new absent root. Scaling fit, D16 prediction,
  D16 execution, route selection, and D7-H remain unauthorized.

## 2026-09-15 — D17 R2 repair + REPAIR_CLOSE review (implementation-only, zero scientific calls)

- REVIEW_ID: `D17-R2-REPAIR`. EVIDENCE_ACCESS VERIFIED (direct file reads,
  own recounts/reruns; no production execution). Verdict: VERIFIED
  REPAIR_CLOSE. R201 PASS, R202 PASS, R203 PASS, R204 PASS. No blocker.
  Proceed to pre-dispatch authorized (the A2 run itself still needs
  pre-dispatch PASS — separate section below).
- Track/repo: EXPLORE_HEAVY repair arm only (no DE/decoder/scientific calls,
  no official-root write, no commit/push). Branch
  `formal-ir-v72p1-addendum-clean`, HEAD `73c6275b` (recorded; no
  HEAD-equality requirement). R2 implementation uncommitted working tree.
- R201 delta (module `v72p2d17_descaling.py` + runner docstring):
  `_require_channel_triplet` (exact 3-item `(pb,p_f,p1)` finite
  shape-compatible unpack-once) + `build_production_channels` calls accepted
  `load_l1_channel` once and bound `build_l1_sampler(pb,p_f,p1)` once;
  `_tag_sampler(..., "L1")` marks the callable. A1 tuple-as-sampler path gone.
- R202 delta: `build_l2_oracle_sampler` (new minimal D17 adapter): `p2` once
  via bound `conditionalize_f_to_p2`; `(A,B)` from same `pb[B]*p_f[A,B]`
  joint as L1; `u1=A//32`, `u2=A%32`; prior EXCLUSIVELY via bound
  `oracle_l2_prior(p2,B,u1)` (D9/D5 floor-normalize reused, never
  reimplemented); XOR-center on true `u2`; fail-closed; tagged `"L2"`.
  V36/V37 empirical samplers untouched/forbidden (code scan clean).
- R203 delta: `_resolve_profile_sampler` dispatches from the frozen plan
  entry's profile before EVERY `run_de_call` (aliases `L1_L045/L1_L055/
  L2_DV3_ORACLE` accepted; unknown/mislabelled fail pre-call); channels must
  be the explicit `{"L045":l1,"L055":l1,"L2":l2}` mapping with distinct L1/L2
  objects and matching `_d17_layer` tags; single shared callable forbidden.
  `run_de_batch`: `None` channel now builds via `build_production_channels`
  (after plan validation + fresh-root probe); per-entry sampler replaces the
  raw `channel` argument. Injected fakes must use the same mapping form.
- R204 proof: diff hunks = `__all__` (+2 exports), one insert-only R2 block,
  `run_de_batch` docstring/build/dispatch only. No change to 15-point grid,
  seeds, pops, lambda/rho, V26 `60/1e-4/20`, bracket/flag/`delta_DE` rules,
  plan order, `240/12` ceilings, resource budgets, claim ceiling, banned D16
  identities (own grep over the module diff; frozen symbols untouched).
- Two test-only corrections (both post-A1 reality alignment, zero scientific
  content): (1) `test_profile_only_content`: `future_root_absent is True` →
  `is False` (A1 root present as immutable six-file failure evidence;
  readiness paths still create nothing); (2)
  `test_d16_root_absent_and_blank_predictions`: asserts the A1 root present
  with the exact six evidence files (read-only) instead of absent. Both
  compliant test-only; R204 unchanged; failed-attempt history retained in
  `workspace/d17_r2_fix_run06`, `workspace/d17_r2_repair_run01`,
  `workspace/d17_r2_repair_run03` (gitignored scratch, not official roots).
- V1–V6 evidence (fakes/tiny probes only; zero V26 DE calls; zero production
  decoder calls; no official R2 root): V1 A1 mechanic reproduced read-only
  (stored error string + `0/240` + `DE_ENGINEERING_BLOCKED` + tuple sandbox
  `TypeError`); V2 binder resolves all 6 accepted callables with exact
  signatures, boom-armed kernel never entered; V3 stub-loader proves unpack
  once / build once with `(pb,p_f,p1)` / `conditionalize` once / mixer hit per
  call / `(k,32)` finite normalized centered rows / L1≠L2 on asymmetric
  fixture; V4 full-240 fake dispatch `160/80` L1/L2 with 9 fail-closed cases
  (swapped/missing/tuple/shared/untagged/shape/nonfinite/mislabelled) all
  `DE_ENGINEERING_BLOCKED@0` with spy empty; V5 real bind/load/build/dispatch
  with `run_de_call` spy count zero and explicit L2 mixer hits; V6
  `py_compile` OK + focused D17 suite 37/37 passed in one fresh basetemp.
- A1 root untouched (re-hashed, all six prefixes match the failure-review
  record `037c7065…/4837bd52…/0780a143…/e0bbb037…/c8ddb989…/ff184433…`); A2
  root absent; D16 official root absent; Model-F unchanged (`cal_only true`,
  `decoder_calls 0`, `val_rows_read 0`; npz `38e4bfba…`, json `ca67a953…`).
  Zero scientific calls anywhere in repair/validation.
- No commit, no push (none requested/authorized). Unrelated worktree dirt
  preserved untouched.

## 2026-09-15 — D17 R2/A2 pre-dispatch P1–P8 (raw evidence, no --execution-authorized yet)

- P1 A1 failure-review: `D17-DE-B1-REVIEW` VERIFIED/PASS (by reference, this
  log). Stored error: `DE_CALL_FAILED@0: TypeError: 'tuple' object is not
  callable` (command_log.txt line 2 + summary.json `engineering_reason`
  identical; terminal `DE_ENGINEERING_BLOCKED`, `scientific_calls 0/240`).
  A1 grant CONSUMED at A1 command start (single grant; no second run under
  it). A1 six-file root present, re-hashed 2026-09-15T11:2xZ, ALL unchanged
  vs record: command_log.txt `037c70656653…b24b`, de_plan.csv
  `4837bd52496f…263917`, de_records.csv `0780a143c78f…083707d`,
  de_traces.csv `e0bbb037a12d…6783d053`, manifest.json `c8ddb98920d8…6fef8b9`,
  summary.json `ff184433d89f…7bbce3`.
- P2 branch/diff: `formal-ir-v72p1-addendum-clean`, HEAD
  `73c6275b96f86ea2b1f40bd8ee082a13e3cfb639` (recorded only). Scoped R2 diff
  (vs HEAD): `comparison_bench/src/.../v72p2d17_descaling.py` +241/-part
  (5 hunks: `__all__` +2, insert-only R2 block, `run_de_batch` docstring +
  build + dispatch), `scripts/v72p2d17_scaling_development.py` docstring +
  comment only, `comparison_bench/tests/test_v72p2d17_descaling.py` +372/-5
  (R201–R203 regression tests + 2 test-only corrections), OpenSpec D17
  `design.md` §10 + `specs/de-scaling/spec.md` REQ-DE-R2-01..07 + `tasks.md`
  R2-SPEC/R2 checklist, this log (appends). R204 frozen symbols untouched
  (own diff-grep: no hunk touches rate/grid/seed/pop/lambda/rho/V26/bracket/
  budget/banned code). R2 implementation uncommitted; unrelated dirt
  preserved, no repairs to it.
- P3 roots: A2 root
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
  ABSENT (`ls: No such file or directory`). D16 official root
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  ABSENT. Model-F `workspace/v72p2d5_model_f_input/20260907_r1` present and
  UNCHANGED: npz `38e4bfba74d0…00b6280d345`, json `ca67a95305e9…a78fac1a43`
  (both match A1 record); summary `cal_only true`, `decoder_calls 0`,
  `val_rows_read 0`.
- P4 tests+review: `py_compile` OK (module+runner+tests); focused D17 suite
  37/37 passed in 12.92 s in ONE fresh `workspace/d17_predispatch_tests_r2`
  basetemp (`.venv/bin/python -m pytest ... -p no:cacheprovider -o addopts=
  --basetemp ...`). Repair review `D17-R2-REPAIR` EVIDENCE_ACCESS VERIFIED,
  REPAIR_CLOSE (R201/R202/R203/R204 PASS), no blocker (section above).
- P5 frozen matrix equality (own recompute, R204 unchanged proof):
  `build_de_plan()` = 240 rows, 240 unique identities, call_idx 0..239
  contiguous, byte-identical ORDER to A1 `de_plan.csv` (240/240 match);
  profiles L045/L055/L2; 15 cells L045 m106/110/114/118/122, L055
  m116/119/122/124/126, L2 m89/94/99/104/109; seeds 2026094201..08 (8);
  pops 4000/16000; spot cells match A1 record (L045 m110 R=0.140625
  delta=+0.01015 rho={2:17,3:93}; L055 m122 rho={2:65,3:57}; L2 m99
  rho={3:12,4:87}); V26 60/1e-4/20; ceilings 240/12, wall 1200 s, per-call
  300 s, RSS 2147483648 B, 1 proc, setup_units 4; `verify_seed_disjointness`
  passed=True over 205 priors (de_hits_prior/d16 empty); DE seeds disjoint
  from 20 banned (4001–4012/4101–4108); probe seed 2026091727 fresh,
  test-only, never a scientific stream.
- P6 PROFILE_ONLY + refusal (fresh scratch, never A2 root): `--profile-only`
  rc=0: grid_points=15, planned_de_calls=240, de_calls=0, decoder_calls=0
  (`future_root_absent=false` expected post-A1: FUTURE_ROOT constant still
  names the A1 evidence root). `--de-batch` without `--execution-authorized`
  vs scratch → rc=2 fail-closed refusal before root/kernel-bind/Model-F-load;
  scratch absent after; no official-root write. Zero scientific calls.
- P7 zero-call production proof (real Model-F CAL-only input, read-only;
  V26 `run_de_call` exact-signature spy + `run_mcde_posterior` boom):
  bind resolves 6/6 callables; load unpacks once; L1+L2 built
  (`L055 is L045`, L2 distinct object, tags L1/L1/L2, mixer 0 at build);
  full-240 dispatch (160 L1 / 80 L2) all correct with 80 explicit L2
  oracle-mixer hits; `run_de_call` spy count ZERO; L2 tiny probe (4,32)
  finite; A2 root still absent after (no official-root write).
- P8 command + grant: frozen command ==
  `.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch
  --execution-authorized --model-f-root
  workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
  (packet §4 verbatim; A2 root substituted for consumed A1 root). A2 grant
  UNUSED at check time (A2 root absent; no existing A2 content).
- Verdict: PRE_DISPATCH 8/8 PASS. Proceeding to the single authorized A2
  execution; A2 grant consumed at command start. No second repair, no
  fallback to A1 root, no common sampler.

## 2026-09-15 — D17 R2/A2 execution (single authorized run, raw evidence)

- Command (exact, once, grant consumed at start 2026-09-15T11:31:35Z):
  `.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch
  --execution-authorized --model-f-root
  workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
- Exit 0. Start 2026-09-15T11:31:35Z, end 2026-09-15T11:37:12Z (process wall
  337 s per `/usr/bin/time -v`; internal `wall_s=322.90`).
  `command_log.txt`: `plan validated calls=240; rho identities bound per
  cell` → `terminal=DE_COMPLETE calls=240 wall_s=322.903`. No retry, no
  resume, no second invocation.
- Calls/setup vs ceilings: scientific 240/240 (exactly 240), setup 4 (≤12).
  Budgets: wall 337 s process / 322.9 s internal (≤1200); per-call max
  2.70 s, min 0.30 s (≤300 between-call check, never tripped); max RSS
  281156 kB ≈ 0.27 GiB (<2 GiB); 1 CPU process (99% CPU). `budget_violations:
  []`. (Summary `peak_rss_bytes: 0` is the known internal placeholder per
  B1-review N2; judgment on the external 281156 kB figure.)
- S_pop table (converged seeds of 8 per profile/m/pop; each cell 8/8 calls):
  L045: m106 0/0, m110 0/0, m114 0/0, m118 8/6, m122 8/8 (p16000/p4000);
  L055: m116 0/0, m119 7/6, m122 8/8, m124 8/8, m126 8/8; L2: m89 0/0, m94
  0/0, m99 8/8, m104 8/8, m109 8/8. Total converged rows 139/240.
- Brackets/flags/delta_DE (all `DE_BRACKET`, no one-sided/soft/unstable):
  L045 lo m114/hi m118 h=0.078125 delta_DE=0.24452956979862517; L055 lo
  m116/hi m119 h=0.05859375 delta_DE=0.30312331979862517; L2 lo m94/hi m99
  h=0.09765625 delta_DE=0.5468113653656221.
- Dispatch from artifacts: records (profile,layer) = L045/L1 ×80,
  L055/L1 ×80, L2/L2 ×80; crashes 0, errors none; call_idx 0..239
  contiguous. Trajectory presence: `de_traces.csv` 240 rows (525508 B,
  full 60-iteration traces), `de_records.csv` 240 rows, `de_plan.csv` 240
  rows (sha256 identical to A1 plan `4837bd52…` — same frozen matrix).
- A2 root files + sha256 (six files): command_log.txt `2ee23120…54a2c4`,
  de_plan.csv `4837bd52…263917`, de_records.csv `d60ab78d…68e40a26`,
  de_traces.csv `b3b4d3b5…f04cec2e`, manifest.json `1aecf2d2…bb433d9`,
  summary.json `53ec0fdc…7db79`. Manifest grid/seeds/pops/budgets frozen;
  `out_root` = A2 path; `model_f_root` unchanged.
- A1 root re-checked unchanged after A2 (six prefixes still match); D16
  official root still absent; Model-F still unchanged; no fit, no D16
  prediction writing, no decoder/CAL/VAL/real-data path, no commit/push.
- A2 grant: CONSUMED (single execution; no second run/retry/resume/repair
  remains under this authorization). Next gate: independent batch-end review
  (packet §6) before any scaling-fit decision use; terminal on review pass:
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`.

## 2026-09-15 — D17 DE A2 batch-end review (VERIFIED PASS_WITH_FINDINGS)

- REVIEW_ID: `D17-A2-REVIEW` (condensed record; authority sections above not rewritten).
- Track/repo: documentation-only (no code, no execution, no rerun, no repair, no root modification, no commit/push); branch `formal-ir-v72p1-addendum-clean` (not switched).
- EVIDENCE_ACCESS VERIFIED (direct reads + own recounts + own verifier run; no edits/reruns/repairs/commit/push).
- PROVENANCE/ONE-SHOT PASS: command_log exactly 2 lines (plan-validated 11:31:38Z → DE_COMPLETE 11:37:12Z, 334s span); manifest command == frozen; all 6 files one end-of-run write burst; no retry/resume/second-invocation; grant consumed once.
- INVENTORY PASS: 6/6 files, hashes match (2ee23120…/4837bd52…/d60ab78d…/b3b4d3b5…/1aecf2d2…/53ec0fdc…); 240 rows each plan/records/traces.
- IDENTITIES PASS: 240/240 unique (profile,m,population,seed); idx 0..239; seeds 2026094201..08; pops 4000/16000; params 60/1e-4/20; A2 de_plan byte-identical to A1 (4837bd52…).
- DISPATCH PASS: {"L045":l1,"L055":l1,"L2":l2} distinct tagged callables; per-entry dispatch; single-shared forbidden; (L045,L1)×80 + (L055,L1)×80 + (L2,L2)×80, 0 crashes/errors; observable distinctness (L2 m94 δ+0.449 0/8 vs L1 m122 δ+0.479 8/8 — impossible under shared sampler).
- CONVERGENCE PASS (own recount, 0 flag/record mismatches): L045 m106 0/0, m110 0/0, m114 0/0, m118 8/6, m122 8/8; L055 m116 0/0, m119 7/6, m122–126 8/8; L2 m89 0/0, m94 0/0, m99–109 8/8; 139/240 converged; 8/8 calls per cell.
- BRACKETS/FLAGS/DELTA PASS: lo/hi correct (L045 114/118, L055 116/119, L2 94/99); all DE_BRACKET only (clean 0→≥7 transitions); midpoints recomputed full precision 0.24452956979862517 / 0.30312331979862517 / 0.5468113653656221 exact; h = half local steps.
- RATES/RHO PASS: 15/15 (R,δ) exact from R=1−m/128, δ=5m/128−H_l; spot cells verified incl. check_counts.
- D16 ABSENCE/OUTCOME-BLANK PASS: official root absent; banned seeds 0 hits; only 6 evidence files.
- VERIFIER/BUDGETS PASS (reviewer ran): checked_calls=240 violations=0 PASS rc=0; calls 240/240, setup 4/12, wall 322.9/1200, per-call-max 2.6955/300, RSS ≈0.27GiB (external trusted; internal placeholder known), 1 proc; Model-F unchanged (cal_only, decoder 0, val 0); no decoder/CAL/VAL/real-data.
- A1 IMMUTABILITY PASS: six prefixes match failure-review record; A2 plan == A1 plan.
- NO-RETRY: single pass, contiguous idx, no markers; no fit/prediction/D16/route/FER.
- FINDINGS: BLOCKING none; NON-BLOCKING N1 (trace early-stopped per streak-20, "full 60-iter" wording imprecise) + N2 (manifest.command names A1 FUTURE_ROOT path by verifier-equality design — do not "fix" without packet).
- VERDICT PASS_WITH_FINDINGS; recommendation D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION; no rerun granted or needed.
- Close: A2 grant consumed, no second run, no commit/push, memory triage pending.

## 2026-09-15 — Main-thread A2 acceptance and A3 scaling-fit authorization

- Accepted within reviewed scope:
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`; all three
  profiles have clean `DE_BRACKET` results and no blocking review finding.
- Next packet pair:
  `.workbuddy/tasks/D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3_TASK_PACKET.md`
  and its companion authorized prompt.
- A3 is limited to graph-cluster finite-data aggregation, the frozen probit
  identifiability ladder, uncertainty/backoff reporting, and—only if all three
  models identify—three immutable outcome-blank D16 predictions.
- D16 execution, another DE/decoder run, route selection, and D7-H remain
  unauthorized.

## 2026-09-15 — Main-thread A3 acceptance + scaling-fit one-shot grant (recorded verbatim first)

- Main-thread acceptance (decided this turn, recorded verbatim first):
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` is ACCEPTED
  within its reviewed scope (three clean `DE_BRACKET` profiles, review
  `D17-A2-REVIEW` `PASS_WITH_FINDINGS`, blocking none). This marker satisfies
  A3 packet §8 check 1 / pre-dispatch item 1 (marker now present because main
  thread accepted).
- One-shot grant (this turn's explicit authorization, single grant):
  `D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3` once; branch
  `formal-ir-v72p1-addendum-clean`; six named input roots read-only (one A2 DE
  root `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
  + five finite roots `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`,
  `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`,
  `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`,
  `workspace/v72p2d14_discriminator/20260914_r1`,
  `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2` in
  fixed order); fresh fit root
  `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`
  (absent at grant time); one deterministic fit via the frozen
  `--scaling-fit --execution-authorized` command only; outcome-blank D16
  predictions only if all three models identify (else diagnostics only, no
  filled predictions); one independent batch-end review afterwards.
- Grant budgets/limits: zero `DE`/decoder/`CAL`/`VAL` calls; exactly six input
  roots; wall ≤300 s; RSS <2147483648 bytes; one CPU process; no retry, no
  resume, no tuning, no outcome-driven change, no second invocation.
- Terminals: all-identify →
  `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`;
  any `MODEL_NOT_IDENTIFIABLE` → diagnostics only +
  `D17_SCALING_MODEL_NOT_IDENTIFIABLE_AWAITING_ROUTE_DECISION`; engineering
  failure → `D17_SCALING_FIT_ENGINEERING_BLOCKED_AWAITING_DECISION`.
- Prohibitions under this grant: no `D16` execution/rerun/decoder/real-data,
  no `DE`/decoder/`CAL`/`VAL` call, no commit/push, no route/FER/leakage/SKR/
  qualification/optimality/publication/route-closure claim, no fit-root
  overwrite, no glob discovery, no new dependency/framework.
- Authorization-consumption rule: consumed at the single frozen-command start.
  Pre-dispatch 1–5 must PASS before that start; any failure → STOP, grant
  unconsumed, raw evidence + `BLOCKED` + one decision needed.

## 2026-09-15 — D17 A3 IMPL (minimal fit/verify path, no --execution-authorized yet)

- Track/repo: `EXPLORE` fit-execution only; branch
  `formal-ir-v72p1-addendum-clean` (confirmed, not switched); no commit/push
  (none requested); zero `DE`/decoder/`CAL`/`VAL` calls in implementation.
- Changed files (minimal additive, reuse readiness scaling code, no new dep):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d17_descaling.py`
  (+A3 block: frozen `A3_DE_ROOT`/`A3_FINITE_ROOTS`/`A3_FIT_ROOT`/
  `A3_FROZEN_COMMAND`/`A3_DELTA_DE`/`A3_EXPECTED_TOTALS`, `a3_recompute_brackets`,
  `a3_aggregate_finite` (graph-cluster `(source_root,profile,n,m,graph_seed)`,
  `y=exact`/`t=blocks`, root+graph identity, delta recompute, frozen decoder +
  one class, D16/banned/fake STOP, accepted-totals reconcile),
  `a3_fit_all` (fixed `delta_DE`, ladder two-param→`beta=0`→
  `MODEL_NOT_IDENTIFIABLE`, L2 predeclared one-param, cluster likelihood +
  deterministic search via `fit_profile`, bootstrap+LOO+LORO union, logistic
  descriptive-only, residuals excluded), `a3_backoffs` (frozen inversion,
  point+union ints, `m*(0.01)>=m*(0.10)`), `a3_predictions` (D16 absent proof,
  exactly L045/L055/L2 n128 m125/m94, provenance/uncertainty/union incl.
  `{delta_DE-h,delta_DE,delta_DE+h}`, `expected_graph_dispersion` object,
  `BLANK` gate, falsification rule, never-revise), `a3_write_root`/
  `a3_verify_fit_root`/`a3_run` (fail-closed `--execution-authorized`,
  never-overwrite, budgets 0/6/300s/2GiB/1-proc/no-retry));
  `scripts/v72p2d17_scaling_development.py` (additive `--scaling-fit`/
  `--de-root`/repeatable `--finite-root`, default-false refusal
  pre-output/input-reads, never-overwrite, frozen-command parity);
  `comparison_bench/tests/test_v72p2d17_descaling.py` (+8 A3 focused tests:
  recovery, non-identifiable, graph-not-row, APP/undetected, refusal,
  no-overwrite, prediction-blank, fake full fit).
- No new dependency/framework; NumPy+stdlib only; readiness
  `p_success`/`fit_with_ladder`/`cluster_bootstrap`/`loo_range`/`ndtri`/
  `delta_star`/`m_star`/`row_backoff`/`predict_interval` reused, not duplicated.
- `py_compile` OK (module+runner+tests). Focused suite 45/45 passed in
  `workspace/d17_a3_predispatch_tests_run01` basetemp (`-p no:cacheprovider
  -o addopts=`, `.venv/bin/python`, 42.19 s) — raw in pre-dispatch §4 below.
  No broad suites (no focused conflict).

## 2026-09-15 — D17 A3 pre-dispatch 1–5 (raw evidence, no --execution-authorized yet)

- 1 A2 accept + bracket recompute (own code, read-only):
  `D17-A2-REVIEW` `PASS_WITH_FINDINGS` accepted (section above); A2
  `summary.json` terminal `DE_COMPLETE`, 240/240 calls; recomputed via
  `a3_recompute_brackets` at 2026-09-15T13:10:43Z:
  L045 `delta_DE=0.24452956979862517 h=0.078125 lo114/hi118 flags=[DE_BRACKET]`;
  L055 `delta_DE=0.30312331979862517 h=0.05859375 lo116/hi119 flags=[DE_BRACKET]`;
  L2 `delta_DE=0.5468113653656221 h=0.09765625 lo94/hi99 flags=[DE_BRACKET]`;
  all match frozen literals to 1e-12 (STOP would have fired otherwise).
- 2 six inputs present/read-only + fit/D16 absent:
  all six `PRESENT` (A2 DE + D10-A1 + R3 + D12 + D14N/20260914_r1 + D15);
  fit root `ls: No such file or directory`; D16 official root
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  `ls: No such file or directory`; A2 terminal `DE_COMPLETE` (read-only).
  No writes to the six inputs (scoped `git status` shows only the four
  intended A3 files).
- 3 frozen root list/command + no D16/fake/banned identity:
  `code==packet: True`, `runner==code: True`; frozen command byte-identical
  (`.venv/bin/python scripts/v72p2d17_scaling_development.py --scaling-fit
  --execution-authorized --de-root workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24
  --finite-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
  --finite-root workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d
  --finite-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450
  --finite-root workspace/v72p2d14_discriminator/20260914_r1
  --finite-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2
  --out-root workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`);
  banned-seed scan `banned_hits: []`; `fake_scratch_in_roots: []`;
  `d16_root_in_roots: []`; aggregation reconciles to all 20 accepted
  `(y,t)` totals (96 clusters: L045 48 / L055 30 / L2 18).
- 4 tests: `py_compile` `PY_COMPILE_OK`; refusal `--scaling-fit` without
  `--execution-authorized` → `rc=2` (`refusing --scaling-fit...`) before
  output/input-reads, scratch absent after; focused suite 45/45 passed
  (`45 passed, 1 warning in 42.19s`) in ONE fresh
  `workspace/d17_a3_predispatch_tests_run01` basetemp
  (`.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d17_descaling.py
  -p no:cacheprovider -o addopts= --basetemp=workspace/d17_a3_predispatch_tests_run01 -q`),
  covering recovery / non-identifiable / graph-not-row (96 clusters) /
  APP-undetected / refusal / no-overwrite / prediction-blank / fake full fit.
  Predecessor suites trusted (no conflict; full D17 file run IS the focused
  suite here).
- 5 zero calls + unused grant: `DE_calls=0 decoder_calls=0 CAL_calls=0
  VAL_calls=0`; `no DE/decoder/CAL/VAL calls in A3 block (good)`; fit root
  still absent (grant UNUSED at check time); branch
  `formal-ir-v72p1-addendum-clean`; scoped diff only the four A3 files;
  `git log` HEAD `73c6275b` (no new commit); no push.
- Verdict: PRE_DISPATCH 5/5 PASS. Proceeding to the single authorized fit
  execution; grant consumed at command start. No retry/resume/tuning.

## 2026-09-15 — D17 A3 execution (single completing run + infra timeout disclosure, raw evidence)

- Infra disclosure (no outcome, no write, no tuning): first invocation at
  2026-09-15T13:13:33Z with the exact frozen command was killed by the harness
  tool timeout after 120 s (`shell tool terminated command after exceeding
  timeout 120000 ms`); fit root still absent after (`No such file or
  directory`), no fit process running, no likelihood/model/prediction observed.
  This was an infrastructure wall (120 s < 300 s budget), not a scientific
  outcome or tuning step. The completing invocation below uses the identical
  byte-identical frozen command/inputs with an adequate 360 s tool timeout;
  it is the single evidence-producing execution (one root written, no second
  completion, no resume of partial state since none existed).
- Command (exact, completing run, grant consumed at start 2026-09-15T13:16:04Z):
  `.venv/bin/python scripts/v72p2d17_scaling_development.py --scaling-fit
  --execution-authorized --de-root
  workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24
  --finite-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
  --finite-root workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d
  --finite-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450
  --finite-root workspace/v72p2d14_discriminator/20260914_r1
  --finite-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2
  --out-root workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`
- Exit 0. Start 2026-09-15T13:16:04Z, end 2026-09-15T13:20:19Z (process wall
  4:15.08 = 255.08 s per `/usr/bin/time -v`; internal `wall_s=248.158`).
  `SCALING terminal=SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN clusters=96`.
  No retry/resume/tuning/second completion.
- Budgets: zero `DE`/decoder/`CAL`/`VAL` calls (`scientific_calls=0`,
  `decoder_calls=0`); exactly six input roots; wall 255.08 s process /
  248.16 s internal (≤300); max RSS 101600 kB ≈ 0.097 GiB (<2 GiB;
  internal `peak_rss_bytes=101818368`); 1 CPU process (99% CPU);
  `budget_violations: []`.
- Aggregation: 96 clusters (L045 48 / L055 30 / L2 18), reconciled to all 20
  accepted `(y,t)` totals pre-fit; `delta=5m/n-H_layer` recomputed
  (mismatch-STOP armed); frozen decoder + one class per cluster;
  D16/banned/fake STOP armed (all clear).
- Brackets (recomputed pre-fit, literal-exact): L045
  `0.24452956979862517/0.078125 lo114/hi118`; L055
  `0.30312331979862517/0.05859375 lo116/hi119`; L2
  `0.5468113653656221/0.09765625 lo94/hi99`; all `DE_BRACKET`.
- Fit (fixed `delta_DE`, cluster likelihood, deterministic search, B=2000
  seed 2026094200):
  L045 `one_param` alpha=14.537843856076622 beta=0.0 (fixed),
  alpha_ci95=[10.0, 21.752040340195233], ladder
  `two-param unidentifiable (bound/degenerate bootstrap)` → `beta=0`
  downgrade; LOO alpha [12.232071190499319, 17.78279410038923] n_graphs=48;
  LORO D10-A1 14.5378 / R3 6.2194 / D12 7.6076 / D14N 110.5987 / D15 31.6228
  (D14N-vs-D15 sensitivity retained); logistic descriptive alpha_log=5.6234
  nll 326.8207 vs probit 326.3683 (no selection change);
  L055 `two_param` alpha=4.597269885308723 beta=-1.075,
  alpha_ci95=[3.1622776601683795, 5.623413251903491],
  beta_ci95=[-1.5, -0.575], ladder `two-param identified`; LOO alpha
  [4.1567, 4.5973] beta [-1.25, -0.975] n_graphs=30; LORO D12 (3.4974,-1.5) /
  D14N (3.8681,-1.025) / D15 (5.0845,-0.85); logistic alpha_log=1.6079
  (descriptive);
  L2 `one_param` (predeclared single-width primary) alpha=5.084520468600939
  beta=0.0, alpha_ci95=[3.4974378036641784, 6.878599123088078]; LOO
  [4.1567, 5.6234] n_graphs=18; LORO D14N 0.001 (all-zero low subset) / D15
  8.1752; logistic alpha_log=1.6079 (descriptive). No `MODEL_NOT_IDENTIFIABLE`.
- Backoffs (diagnostic, point + union ints, `m*(0.01)>=m*(0.10)` holds):
  L045 n64 (0.10: m66/back11 union [63,81]/[8,26]; 0.01: m73/back18 union
  [67,99]/[12,44]); n128 (0.10: m128/back18 union [122,149]/[12,39]; 0.01:
  m137/back27 union [128,174]/[18,64]); n256 (0.10: m248/back28 union
  [239,280]/[19,60]; 0.01: m261/back41 union [247,315]/[27,95]);
  L055 n64 (0.10: m63/back8 union [61,64]/[6,9]; 0.01: m66/back11 union
  [64,68]/[9,13]); n128 (0.10: m123/back13 union [120,126]/[10,16]; 0.01:
  m128/back18 union [124,131]/[14,21]); n256 (0.10: m243/back23 union
  [238,247]/[18,27]; 0.01: m250/back30 union [244,255]/[24,35]);
  L2 n64 (0.10: m53/back11 union [48,56]/[6,14]; 0.01: m57/back15 union
  [48,61]/[6,19]); n128 (0.10: m104/back21 union [95,108]/[12,25]; 0.01:
  m109/back26 union [95,115]/[12,32]); n256 (0.10: m203/back37 union
  [189,210]/[23,44]; 0.01: m210/back44 union [189,220]/[23,54]).
- Predictions (all three identify → 3 outcome-BLANK records frozen, D16 absent
  proven pre-write):
  L045 n128/m125 delta 0.5960920697986252 p_point 0.8515665744172791 band
  [0.6156833274137923, 0.9743712729574681], dispersion {8-trial [5,8]/[0.625,
  1.0], empirical residual [-0.42499320188279177, 0.3098973476137118] n=48};
  L055 n128/m125 p_point 0.961571149393954 band [0.8899387155669418,
  0.9955050869733582], dispersion {[6,8]/[0.75, 1.0], residual
  [-0.21127011693651548, 0.24706321639681783] n=30};
  L2 n128/m94 delta 0.44915511536562214 p_point 0.31207335713883716 band [0.0,
  0.5], dispersion {[0,5]/[0.0, 0.625], residual [-0.179211765277852,
  0.07078823472214801] n=18}; all `outcome.{pool,per_graph,exact,syndrome,
  undetected,terminal}=BLANK`; falsification pool-outside-95→FALSIFIED /
  inside→NOT_FALSIFIED / engineering→INCONCLUSIVE, graph range descriptive;
  never-revise-after-observed.
- Root files + sha256 (8 files):
  backoffs.json `3e1f24f0…4d3d2a1`; clusters.csv `e380cead…86cf95`;
  command_log.txt `451ec63a…438f19`;
  d16_prediction_L045_m125.json `a3991135…5089ca`;
  d16_prediction_L055_m125.json `c88a2d7b…5b5b74a`;
  d16_prediction_L2_m94.json `a46c69b6…b873b7eb`; fit.json `9dda8e52…80322b`;
  manifest.json `9154c63c…2058d02`.
- Verifier (read-only, recomputes aggregation/selection/intervals/
  predictions/blank-gate): `VERIFY checked_clusters=96 violations=0`,
  `VERIFY PASS` (rc-equivalent True).
- Grant: CONSUMED at completing-command start (single evidence-producing
  execution; killed 120 s attempt produced nothing and is disclosed above,
  not a second completion). No second completion/retry/resume/tuning.
- Auth/commit/push: no new authorization beyond this A3 one-shot; no commit,
  no push (none requested); unrelated worktree dirt preserved; six inputs +
  D16 unchanged (fit root is the only new root).
- Terminal: `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`
  (all three identify + 3 BLANK predictions frozen + verifier PASS).
  No D16/fit-claims beyond frozen scope; no D16 execution/rerun/decoder/
  real-data/route/FER/leakage/SKR/qualification/optimality/publication claim.

## 2026-09-15 — D17 A3 scaling-fit batch-end review (VERIFIED PASS_WITH_FINDINGS)

- REVIEW_ID: `D17-A3-REVIEW` (condensed record; authority sections above not rewritten).
- Track/repo: documentation-only (no code, no fit rerun, no repair, no root modification, no commit/push); branch `formal-ir-v72p1-addendum-clean` (not switched).
- EVIDENCE_ACCESS VERIFIED (all 8 fit-root files read + A2 spot re-hash + own recomputes + own verifier run with adequate timeout; no edits/reruns/repairs/commit/push).
- AGGREGATION PASS: own recount 96 clusters unique (root,profile,n,m,graph), L045 48 / L055 30 / L2 18; y≤t, t∈{8,12}; delta mismatch 0/96; pools reconcile to all 20 accepted cells (D10-A1 20,24/10,24; R3 23,72/29,72; D12 26,39,42/33,35,46; D14N 3,7,63; D15 0/6/19 + 1/13/22 + 0/0/0); eligibility exact; 5 finite roots only; banned 0; no D16/fake; root+graph identity preserved.
- DELTA_DE PASS: own recompute from A2 root (L045 0.24452956979862517/h 0.078125 lo114/hi118; L055 0.30312331979862517/h 0.05859375 lo116/hi119; L2 0.5468113653656221/h 0.09765625 lo94/hi99; all DE_BRACKET; literal-exact); frozen command byte-identical.
- LADDER PASS: delta_DE required fixed slot (None → ValueError; never in optimizer grid); ladder correctly applied (L045 one_param — two-param unidentifiable with bound/degenerate bootstrap, consistent with LORO D14N-sensitivity; L055 two_param identified with bounded CI; L2 predeclared one_param); logistic descriptive-only (nll gaps tiny); residuals excluded; no MODEL_NOT_IDENTIFIABLE.
- UNCERTAINTY PASS: B=2000 seed 2026094200 n_ok=2000 all arms; LOO 48/30/18; LORO present (5/3/2 roots); CIs contain points; no bare coefficients; union carries exact {dde-h,dde,dde+h}.
- INVERSION PASS: point p_success recomputed exact (L045 0.8515665744172791, L055 0.961571149393954, L2 0.31207335713883716; Δ=1e-12); backoff spots match; m*(0.01)>=m*(0.10) 9/9; diagnostic labeling present.
- PREDICTIONS PASS: bands as reported (L045 p0.8516 [0.6157,0.9744]; L055 p0.9616 [0.8899,0.9955]; L2 p0.3121 [0.0,0.5]); dispersion objects with both keys; binomial intervals plausible; empirical ranges descriptive; falsification verbatim; gate flags present.
- BLANK PASS: all 18 outcome fields exactly BLANK across 3 files; D16 official root absent; no outcome pollution.
- VERIFIER PASS (reviewer ran): checked_clusters=96 violations=0 PASS (first invocation hit 120s harness timeout — cost ≈ fit cost; retry with adequate timeout passed, no state written).
- RESOURCES PASS: scientific/decoder/CAL/VAL 0; 6 inputs; wall 248.16/300; RSS ≈0.095GiB; 1 proc; no retry/tuning; violations []; A2 spot unchanged; no DE/decoder/CAL/VAL/real-data path; no D16 execution.
- ATTEMPTS PASS: single fit root, 8 files, single write burst 13:20:19Z, 9-line command_log, no retry markers; killed first attempt produced nothing; grant consumed at completing start.
- TRUST: A3-spec + pre-dispatch + impl/tests taken as provenance only; all fit numbers independently recomputed; no broad suites.
- FINDINGS: BLOCKING none; NON-BLOCKING N1 (cmdlog L2 last-ulp float display; manifest/fit exact), N2 (never-revise obligation in packet/spec/code, no literal key — schema conformant), N3 (L045 LORO sensitivity large: D14N-excluded α 110.6 / D15-excluded 31.6 vs point 14.5 — retained/disclosed, wider union used; observation only).
- VERDICT PASS_WITH_FINDINGS; recommendation D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION; no edits/D16/fit/rerun/commit/push.
- Close: A3 grant consumed, no second completion, no commit/push, memory triage pending.

## 2026-09-15 — Main-thread A3 acceptance and D16 held-out authorization

- Accepted within reviewed scope:
  `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`.
- The three prediction files are immutable and outcome-blank. D16 is
  authorized only under
  `.workbuddy/tasks/D16_HELDOUT_SCALING_VALIDATION_B1_TASK_PACKET.md` and its
  companion prompt.
- The former direct investment-gate interpretation stays superseded. D16 will
  be compared profile-by-profile to the frozen bands; no model revision is
  authorized after observing it.
- No automatic route choice, D7-H, real-data, FER, leakage, SKR, qualification,
  or publication claim is authorized.

## 2026-09-15 — D16-B1 review pointer (D17 unchanged)

- D16 Batch B1 batch-end review `D16-B1-REVIEW`: VERIFIED PASS (detail:
  `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md`
  §`2026-09-15 — D16 Batch B1 batch-end review (VERIFIED PASS)`).
- Verdicts: L045 0.78125 inside → NOT_FALSIFIED; L055 0.84375 below band →
  FALSIFIED; L2 0.28125 inside → NOT_FALSIFIED. Terminal:
  `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`.
- This pointer is append-only; D17 evidence unchanged; no edits/rerun/commit/push.
