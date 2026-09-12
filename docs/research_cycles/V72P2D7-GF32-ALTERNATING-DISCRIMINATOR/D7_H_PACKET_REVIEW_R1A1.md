# D7-H packet review R1A1 (independent packet-freeze review)

- Authority: `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md` §4 A02
  ("Add `D7_H_PACKET_REVIEW_R1A1.md`, whose independent reviewer checks: ...") under
  §2 (freeze correction ruling) and §5 (frozen contract); freeze pair
  `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md` §0.
- Reviewer constraints honored: review-only; this document is the only file written; no
  decoder call, no Model-F/CAL/VAL/real read, no `--phase`, no workspace root/UUID created,
  no commit, no push. Root `AGENTS.md` (reviewer must not edit; Pre-EXECUTE/Pre-RESULT
  semantics) read first.
- Branch/HEAD: `git rev-parse --abbrev-ref HEAD` = `formal-ir-v72p1-addendum-clean`;
  `git rev-parse HEAD` = `46141fcc0a7391c014dcd22e1c99372e951a7aed`, matching the frozen
  basis HEAD `46141fcc` of the packet/prereg/proposal.

## Artifacts under review (untracked drafts, corrected freeze set) and mtimes

| Path | mtime (2026, +0800) | git state |
|---|---|---|
| `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_TASK_PACKET.md` | 09-13 00:32:46 | `??` untracked |
| `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_PROMPT.md` | 09-13 00:32:58 | `??` untracked |
| `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/D7_H_PREREG_R1.md` | 09-13 00:26:15 | `??` untracked |
| `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/cycle_state.yaml` | 09-13 00:24:28 | `??` untracked |
| `openspec/changes/v72p2d7-alternating-discriminator/design.md` | 09-13 00:23:31 | `??` untracked |
| `openspec/changes/v72p2d7-alternating-discriminator/proposal.md` | 09-13 00:27:42 | `??` untracked |
| `openspec/changes/v72p2d7-alternating-discriminator/tasks.md` | 09-13 00:24:55 | `??` untracked |
| `.../specs/alternating-cross-layer-discriminator/spec.md` | 09-13 00:25:38 | `??` untracked |
| `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/cycle_state.yaml` (D7-G linkage) | 09-12 19:15:19 | ` M`, diff `4 0` additive |

All corrected-freeze mtimes post-date the R1A1 authority packet (09-12 19:37). The R1A1
correction rewrote the freeze set in place; the R1 draft itself is not recoverable from
git (untracked, never committed) — see observation O4.

## Check 1 — gating / call arithmetic / coverage / syndrome-once, R1A1-consistent in ALL artifacts — PASS

- STAGE 0 only unconditional mandatory call:
  packet L83 `STAGE 0  SOURCE_L1_MARGINAL            (only unconditional mandatory call; shared)`;
  prereg L48 `STAGE 0  cold decode L1 marginal                         (only unconditional mandatory call)`;
  proposal L22 same; design L15 `(only unconditional mandatory call; shared)`; spec L6
  `the only unconditional mandatory call, covering all identities`.
- STAGE 1 gated on STAGE 0, STAGE 2 gated on STAGE 1:
  packet L92-93 `STAGE 1  FORWARD_L1_TO_L2              (gated on STAGE 0; reference endpoint) / invoked only if STAGE 0 yields finite, shape-valid, non-crashed, exact CHECK_EXTRINSIC`;
  L100-102 `STAGE 2  BACKWARD_L2_TO_L1             (gated on STAGE 1; candidate endpoint) / invoked only if STAGE 1 yields ... exact CHECK_EXTRINSIC`;
  prereg L50/L53; proposal L23-24; design L11-12/L24-25/L31-32; spec L8-10.
- Blocked stage = non-invocation, cascade, never synthesized/replaced/retried/resumed;
  iteration-0 `NO_CHECK_EVIDENCE` blocks; source hard exact not a gate:
  packet L86-90 `NO_CHECK_EVIDENCE (including iteration-0 hard/syndrome success) / ... => blocked non-invocation; all downstream stages for that identity are blocked, never synthesized, replaced, retried, or resumed. ... Source hard exact is not an eligibility gate.`;
  identical substance prereg L110-114, proposal L79-83, design L18-22/L60-64, spec L43-50.
- Minimum 32 / maximum 96, no stale counts:
  packet L109-111 `1 unconditional mandatory call per identity (STAGE 0; 32 identities → minimum 32 actual calls) plus up to 2 gated calls per identity ... Maximum `32 × 3 = 96` decoder calls`;
  prereg L139-141; proposal L27-29; design L46-48; spec L27-29.
  Targeted grep over the eight freeze-set files for `exactly three decoder|three decoder|64 mandatory|2 mandatory|two mandatory|STAGE 1 is mandatory|STAGE 1 mandatory` found only
  design L10 `Per (f, seed), up to three decoder calls: STAGE 0 is the only unconditional` — the correct upper bound, not stale wording. No residual `192/128 mandatory` hits.
- Coverage = complete three-stage chains; ONE complete-chain count + blocked-at-stage1/blocked-at-stage2; `COVERAGE_BLOCKED` <12/16:
  packet L163-166 `fewer than 12/16 identities have a complete chain (all three stages invoked and finite/shape-valid). Both endpoints share the chain, so one complete-chain coverage count is recorded per f, plus explicit blocked-at-stage1 and blocked-at-stage2 counts.`;
  repeated packet L251-253, prereg L124-127, design L113-115, spec L94-98, proposal label list L87.
- Per-invocation designated-syndrome statement (L1 twice across STAGE 0/STAGE 2; STAGE 1
  outgoing extrinsic removes its entire incoming prior including STAGE 0's L1 evidence):
  packet L147-151, prereg L106-109, proposal L75-78, design L72-76, spec L56-59 — e.g.
  `Each decode invocation consumes its designated syndrome once; L1 is decoded twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic removes its entire incoming prior, including STAGE 0's L1 evidence, before STAGE 2 consumes L1 syndrome again.`
- Required new tests-proof item present in every "must prove / demonstrate" list:
  packet L152-157 `(e) the returned prior is invariant to the removed STAGE 0 incoming-message component while remaining sensitive to STAGE 1's own check evidence.`;
  prereg L115-120 (e) same; design L77-82 (e) same; spec L63-71 `SHALL demonstrate ... invariant to the removed STAGE 0 incoming-message component while remaining sensitive to STAGE 1's own check evidence`; proposal L123-127 ALT-03 same.

## Check 2 — D7-G contract supports exactly two transfers; minimality; posterior forbidden — PASS (one non-blocking citation defect, O1)

- Three-stage chain consumes only explicit `CHECK_EXTRINSIC`: packet L94/L103
  `q1_ext = softmax(extrinsic_log_beliefs of STAGE 0)      # CHECK_EXTRINSIC only` and
  `q2_ext = softmax(extrinsic_log_beliefs of STAGE 1)       # CHECK_EXTRINSIC only`; helper
  `require_check_extrinsic_for_transfer` (packet L140-141, prereg L97-99, design L57-58, spec L36-37).
  This is the certified D7-G interface: acceptance L9 `L_code_ext = L_post − log(p_in)` with
  `NO_CHECK_EVIDENCE`/`CHECK_EXTRINSIC`/`WARM_START_UNSPECIFIED` (L10-13) and helper unwired
  from production (L13); review R1 §5 confirms helper-only explicit finite shape-correct
  `CHECK_EXTRINSIC` acceptance.
- Minimality: packet §4 L75-78 `the smallest alternating schedule that is no longer blocked is
  exactly two transfers: one forward L1→L2, then one backward L2→L1. No third transfer is
  implied by any accepted contract`; prereg L63-70; proposal L33-40; design L40-43. The
  `>2-stage` block is verbatim in D7-F prereg §2/B04 (`>2-stage alternating stays blocked
  pending a cavity/extrinsic-message contract capable of excluding returned syndrome evidence;
  D7-F encodes no such contract`) and equivalently in D7-E acceptance (`Multi-round
  alternating therefore remains blocked pending a verifiable extrinsic/cavity contract`),
  with D7-E prereg L243 `CHECK_UPDATED allows exactly one transfer call;`.
- Posterior back-transfer explicitly forbidden: packet L57 `Posterior back-transfer explicitly
  forbidden`, L142-146 `The backward prior is a function of L2's code-factor extrinsic only,
  never L2's posterior ... No target posterior is fed back, blended, multiplied, or reused.`;
  prereg L104-105; proposal L46/L72-74; design L69-71/L142-143; spec L54-61.

## Check 3 — endpoint pairing on identical (f,seed); AND-only; syndrome separate — PASS

- packet L97 `REFERENCE both_layers_exact = L1_exact AND L2_exact`; L106 `CANDIDATE
  both_layers_exact = L2_exact AND L1_return_exact`; L246-250 `arm_pairs.csv holds one row per
  reference/candidate arm pair per (f,seed) with shared-identity pins (f/seed/block/H/syndrome/decoder config) ... L1/L2/L1_return exact/syndrome separately`.
- prereg L71-74; proposal L18-19 `the candidate is compared on the same seeds against the
  single-pass forward reference`; design L110-112 `one row per reference/candidate pair per (f,seed) with shared-identity pins ... exact/syndrome separately`; spec L15-22.
- Syndrome separation/isolation also in the verifier scope: packet L263-264 `exact/syndrome
  isolation, both-layer AND rules, per-invocation designated-syndrome accounting`; design L119-120.

## Check 4 — no-returned-evidence claim limited to the certified extrinsic contract — PASS

- packet §14 L313-318 `Alternating classifications are route discriminators, not FER estimates.
  No result of D7-H may be described as protocol recovery, leakage, reconciliation-efficiency,
  key-rate, CAL/real-data, qualification, promotion, R1d, G1/G2, or general GF32/NB-LDPC
  performance. ... supports no alternating-convergence claim.`
- prereg L58-59 `It does not claim calibrated posterior, alternating convergence, leakage,
  protocol recovery, or Bob-only FER.`; L198-204 same nonclaim block.
- proposal L107-115 non-goals; design L138-146 alternatives table (`Posterior-based transfer`
  rejected, `>2-stage / iterate to convergence` blocked, oracle forbidden).
- Grep for `calibrated|convergence|FER|leakage|recovery` across the freeze set produced only
  negations/limits plus proposal L36 describing the accepted D7-F result. The cavity claim is
  exactly the D7-G-certified one (explicit `CHECK_EXTRINSIC` only; no reconstructed prior).

## Check 5 — labels(5), ten-terminal first-match, resources complete — PASS (O4 on "unchanged")

- 5 labels in first-match order: packet L163-172 (`COVERAGE_BLOCKED`, `ALTERNATING_REGRESSION`
  `reference_only >= 2 and candidate_only == 0`, `STRONG_ALTERNATING_LIFT` `candidate_only >= 4
  and reference_only == 0`, `WEAK_ALTERNATING_LIFT` `candidate_only > reference_only`,
  `NO_ALTERNATING_LIFT`); prereg L124-132; proposal L87-88; spec L93-98.
- 10 terminals first-applicable: packet L180-190 (`D7_H_PRE_EXECUTION_BLOCKED`, `..._WATCHDOG_TIMEOUT_VOID`,
  `..._NONFINITE_OR_CRASH_BLOCKED`, `..._RESOURCE_OVERRUN`, `..._INCOMPLETE_MATRIX_BLOCKED`,
  `..._PROVENANCE_COVERAGE_BLOCKED`, `..._ALTERNATING_STRONG_LIFT`, `..._ALTERNATING_WEAK_LIFT`,
  `..._ALTERNATING_REGRESSION`, `..._NO_USEFUL_ALTERNATING_LIFT`) `No automatic successor is encoded.`;
  same set/order prereg L133-138, proposal L89-94, spec L99-104.
- Resources: packet L196-209 `hard cap 96 decoder calls (minimum 32: STAGE 0 only); sequential
  only; no concurrency/retry/rerun/resume. / Per-call watchdog 120 s. / Stored scientific wall
  <=1500 s. / Outer GNU timeout `1800` plus `-k 30`. / `.venv/bin/python` only. / ... VmHWM (unit
  exactly kB ...) strict `< 2 GiB`, fail-closed. / One fresh identifier; target fresh direct
  child workspace/d7_h_alternating_discriminator_<uuid>/, no overwrite, no subdirectories;
  exactly seven scalar text files plus an independent read-only verifier.` — identical in
  prereg L139-148, proposal L95-99, design L100-124, spec L105-114.
- "Unchanged from R1" is not literally diffable: the R1 draft was overwritten in place and has
  no git history (O4). I verified the complete resource/label/terminal set against the R1A1 §5
  frozen contract (B03-B05) instead; every element matches, and no artifact carries any stale
  count or superseded label/terminal.

## Check 6 — frozen scientific content unchanged — PASS

- packet §6 L118-127 = prereg §3 L78-87 = proposal L55-62 = design L86-93 = spec L75-82:
  `f order [1.0, 1.2]`; `Seeds 2026091300..2026091315, ascending, exactly 16 per f`; `n=64`;
  L1 rows 49/59, L2 rows 43/52; `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and `(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1`; `GF(32) poly 37, cold start, max_iter=90,
  damping 1.0` — verbatim identical to D7-F prereg L65-74 (the accepted predecessor matrix).
- Estimator: packet L129-134 `only through prepare_model_f_prior_candidate / build_f_model_concentration
  (per-Bob-column (counts[:,b] + lambda*p_global)/(n_b[b] + lambda)). The historical build_f_model
  counts + lambda per-cell rule is forbidden; static and behavioral tests must fail if it is
  referenced.` Same in prereg L89-93, proposal L63-66, design L94-98, spec L79-82. Independently
  checked against code: `v72p2d5_gf32_rate_mother.py` defines `build_f_model_concentration` as the
  per-Bob-column concentration backoff and `build_f_model` as the legacy `counts + lam` per-cell
  rule; the freeze's names and prohibition are correct.
- Seven-file schema/names identical in packet L233-242, design L102-105, with per-file semantics
  in packet L244-258, design L107-124; all seven names match (`manifest.json`,
  `decoder_records.csv`, `arm_pairs.csv`, `stratum_summary.csv`, `summary.json`, `report.md`,
  `command_log.txt`).

## Check 7 — authorization state — PASS

- `cycle_state.yaml` L2-13, L24-29 (quoted): `state: D7_H_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`,
  `plan_revision: R1A1`, `plan_accepted: false`, `implementation_authorized: false`,
  `d7h_execution_authorized: false`, `decoder_executed: false`, `result_created: false`,
  `formal_execution_authorized: false`, `synthetic_execution_authorized: false`,
  `real_execution_authorized: false`, `scientific_promotion: false`,
  `d7h_execution_attempts: 0`, `d7h_execution_completed: 0`, `d7h_implementation_review: NOT_PERFORMED`,
  `d7h_pre_execute_review: NOT_PERFORMED`, `d7h_pre_result_review: NOT_PERFORMED`,
  `d7h_result_accepted: false`, `d7h_accepted_scope: NONE`; no identifier/root key exists.
- R1A1 revision notes present at packet L3, prompt L6, prereg L3.
- No implementation claim: freeze packet L272 `implementation NOT authorized here`, §12
  `all later gates, NONE authorized now`; tasks.md L25-38 H01-H06 all `[ ] ... NOT AUTHORIZED`
  (H05 execute, H06 Pre-RESULT + acceptance); state `d7h_readiness_state: D7_H_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`.
- On-disk absence: `find workspace -maxdepth 1 -name 'd7_h_*'` → empty; `ls` of the three
  frozen planned paths
  (`comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_alternating_discriminator.py`,
  `comparison_bench/tests/test_v72p2d7_gf32_alternating_discriminator.py`,
  `scripts/v72p2d7_gf32_alternating_discriminator.py`) → `No such file or directory` for all
  three; repo-wide `find` for `*d7_h*`/`*D7_H*` returned only the four `.workbuddy` task files
  and the prereg; UUID regex scan over the freeze set → no match.

## Check 8 — no commit-policy self-contradiction — PASS

- packet L21 `No commit is authorized by this freeze itself; the corrected-freeze commit is
  authorized separately by `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md`.`;
  prompt L6 `本对的 R1A1 修正与修正后冻结的提交由该包授权；本冻结自身不 commit。`;
  R1A1 packet L99 `PASS → commit the corrected freeze, including the packet pair, OpenSpec,
  prereg/state, packet review, and D7-G linkage.` No artifact claims a commit is impossible;
  the freeze labels itself as not the committing actor while the R1A1 flow commits it.

## Check 9 — scope of edits — PASS

Commands and literal results:

- `git status --short -- <freeze-set paths>` →
  ` M docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/cycle_state.yaml` plus `??` for the
  four `.workbuddy` task files, the alternating cycle directory, and the OpenSpec change
  directory. `git check-ignore` on the paths → no ignore rule (force-add not currently needed).
- `git diff HEAD --numstat -- .../V72P2D7-GF32-EXTRINSIC-CONTRACT/cycle_state.yaml` → `4 0`
  (exactly the four additive D7-H linkage lines, verified by reading the hunk:
  `+d7h_packet_frozen: true`, `+d7h_packet_doc: ...`, `+d7h_prereg_doc: ...`,
  `+d7h_state: D7_H_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`).
- `find . -path ./.git -prune -o -type f -newermt "2026-09-12 19:37" -print | sort` → only the
  eight freeze-set files plus the two R1A1 authority files. No other repo path changed after the
  R1A1 packet was created.
- `find comparison_bench/src comparison_bench/tests scripts src experiments tools -newermt "2026-09-12 19:00" -type f` → empty. (With the wider window `-newermt "2026-09-12 00:00"`,
  only three unrelated `__pycache__/*.pyc` files from 00:23 Sep 12 — D7-G oracle test caches —
  matched; no source, test, or script file.)
- `find workspace/d7_e_cross_layer_discriminator_faa5dc1c-... workspace/d7_f_reverse_order_discriminator_b6d62184-... -newermt "2026-09-12 00:00" -type f | wc -l` → `0`; no
  `workspace/d7_h_*` and no `workspace/d7_g_*` root exists. Accepted D7-E/F result roots and the
  frozen `src/`, `experiments/`, `tools/` are untouched.
- Pre-existing unrelated dirty/EOL worktree mass (`git status --short` shows many `M` entries
  across docs/configs/outputs; sample numstat for files like
  `comparison_bench/src/comparison_bench/__init__.py` is empty) was not touched; all such code
  files predate the D7-H window (mtimes 09-10/09-11).

## Non-blocking observations

- **O1 — citation defect (not blocking):** freeze packet L66-68 and prereg L63-65 attribute the
  ">2-stage alternating stays blocked ..." warning to `D7-E prereg §9`. D7-E prereg §9 is
  "Nonclaim boundaries" and does not contain that sentence; the quoted sentence is verbatim in
  D7-F prereg §2/B04, and the D7-E accepted equivalent lives in `D7_E_RESULT_ACCEPTANCE_R1.md`
  ("Multi-round alternating therefore remains blocked pending a verifiable extrinsic/cavity
  contract"). The minimality argument itself is supported (D7-E one-transfer acceptance + D7-F
  §2/B04 + D7-G cavity contract). Suggest correcting the pointer at the next docs touch.
- **O2 — phase ID mismatch (not blocking):** freeze packet §12 numbers H01..H05 (H05 = Pre-RESULT
  + acceptance) while `tasks.md` numbers H01..H06 (H05 execute, H06 Pre-RESULT + acceptance).
  All steps are unauthorized in both; align IDs when implementation is authorized.
- **O3 — state-file completeness (not blocking):** `cycle_state.yaml` records
  `d7h_max_decoder_calls: 96` but no machine-readable minimum; the min-32 rule is stated in
  every narrative artifact. Consider adding `d7h_min_decoder_calls: 32` at the next state touch.
- **O4 — "unchanged from R1 draft" evidence limit:** the R1 draft was overwritten in place and
  is untracked, so a literal before/after diff is impossible. Completeness/self-consistency was
  verified against the R1A1 §5 frozen contract; the residual "unchanged" claim rests on the
  R1A1 revision notes and the absence of any stale count/terminology. Not a defect of the
  artifacts themselves.
- **O5 — R1A1 note wording (not blocking):** packet L3 / prereg L3 say "the R1A1 packet
  authorizes the corrected freeze commit only — implementation and execution remain unauthorized."
  The R1A1 packet does authorize Phase B implementation after the freeze commit (L15), so the
  sentence is stage-scoped shorthand; every in-artifact statement about *this freeze* ("NOT
  authorized here", H01-H06) remains correct. Reword if the sentence is ever quoted outside the
  freeze context.
- **O6 — D7-G `next_gate` label:** the D7-G `cycle_state.yaml` still reads
  `next_gate: D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE` although the D7-H packet is now
  frozen (`d7h_packet_frozen: true`). Advancing it was outside the authorized additive linkage;
  record for the next authorized D7-G touch.
- **O7 — prereg revision label:** prereg L10 status remains `FROZEN_PREREG_R1` while
  `cycle_state.yaml` L3 carries `plan_revision: R1A1`; the R1A1 note at prereg L3 makes the
  relationship explicit. Cosmetic.

## Verdict

`D7_H_PACKET_REVIEW_PASS_R1A1`

No blocking issue found in checks 1-9; observations O1-O7 are non-blocking. This review covers
the freeze packet only and authorizes nothing: no D7-H implementation, execution, promotion,
R1d, G1, or G2. Per R1A1 §4 A02, the corrected freeze (packet pair, OpenSpec, prereg/state,
this review, D7-G linkage) may now be committed by the R1A1 flow; no push.
