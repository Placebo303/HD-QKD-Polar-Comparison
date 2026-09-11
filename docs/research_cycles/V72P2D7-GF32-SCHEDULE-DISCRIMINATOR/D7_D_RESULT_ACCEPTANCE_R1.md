# D7-D result acceptance R1 — schedule-discriminator invocation `64660d16-397d-4ef3-8454-3066d27c12c7`

Scope: scoped acceptance documentation only. Zero decoder calls, zero reruns,
zero root edits, zero production-code edits. Main-thread adjudication (§0 of
`D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md`) is applied without
reinterpretation.

## Baseline (verified before writing)

- Branch: `formal-ir-v72p1-addendum-clean`; entry HEAD `63a69f57`
  (`result(d7-d): record one reviewed schedule-discriminator invocation`).
- Root
  `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7/`:
  exactly seven files, zero subdirectories —
  `manifest.json` (3164 B), `decoder_records.csv` (57659 B),
  `paired_schedule.csv` (17690 B), `stratum_summary.csv` (1777 B),
  `summary.json` (1546 B), `report.md` (455 B), `command_log.txt` (290 B);
  all mtime 2026-09-11 07:30:05 +0800 (epoch 1789083005).
  Read twice (task start/end); names/sizes/mtimes/sha256 identical; nothing
  modified.
- Sole D7-D UUID `64660d16-397d-4ef3-8454-3066d27c12c7`; the only
  `workspace/d7_d_schedule_discriminator_*` root.
- Lifecycle commits (local-only): authorize `7a3f0d92` → exactly one
  invocation → revoke `eba385bb` → result `63a69f57`.
- Review/verify tokens: independent Pre-RESULT
  `D7_D_PRE_RESULT_REVIEW_PASS_R1` (R01–R20, internal coherence only); sole
  read-only verifier output
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}`
  (exit 0).
- `cycle_state.yaml` (pre-acceptance): `d7d_execution_authorized: false`,
  attempts/completed `1/1`, `decoder_executed: true`, `result_created: true`,
  `scientific_promotion: false`, `d7d_pre_result_review:
  D7_D_PRE_RESULT_REVIEW_PASS_R1`,
  `next_gate: INDEPENDENT_D7_D_RESULT_ACCEPTANCE_R1`.
- R1d/G1/G2 unauthorized; protected D7-C/D7-B/Model-F roots unchanged; no push.

## Main-thread adjudication (§0, transcribed without reinterpretation)

Accept the reviewed D7-D run only as:

`D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`

The accepted facts are limited to the single UUID
`64660d16-397d-4ef3-8454-3066d27c12c7`: 256/256 paired calls completed;
row-layered exact `43/128`, flooding exact `40/128`, layered-only `3`,
flooding-only `0`, both `40`, neither `85`; no crash/nonfinite/watchdog;
stored terminal `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; independent Pre-RESULT
`D7_D_PRE_RESULT_REVIEW_PASS_R1`; budgets passed.

Interpretation boundary:

- the frozen matrix establishes no preregistered flooding or layered advantage;
- `43 vs 40` and three layered-only pairs are reported, not promoted into a
  schedule-superiority claim;
- schedule choice is not supported as the dominant explanation of the current
  failures;
- D7-C's accepted bidirectional oracle dependence remains the stronger route
  evidence, but it does not prove that alternating/joint BP can bootstrap;
- no FER, leakage, key rate, qualification, promotion, general schedule
  equivalence or general NB-LDPC conclusion;
- R1d becomes `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`; it is not
  authorized or executed here;
- G1/G2 remain unauthorized; old D5/D6 checkboxes are historical accounting,
  not mandatory gates to future dimension generalization.

The next mainline action is Alternative A of the accepted layer-interface
proposal: explicit belief provenance plus fail-closed cross-layer consumers.
No forced extra sweep (Alternative B), warm-start mechanism, alternating/joint
decoder or scientific decoder run is authorized by this packet.

## Independent recomputation (Phase-A A01)

Recomputed read-only from the seven scalar files (stdlib script under
`/tmp/opencode/`, root never written; no decoder, no Model-F load, no
verifier re-run). Result: **0 discrepancies with §0** — 256 unique calls
(`call_idx` 1..256, parity odd `ROW_LAYERED` / even `FLOODING`, each schedule
covering identities 1..128 exactly once, `2k-1`/`2k` mapping);
all 128 non-schedule inputs (`f, seed, condition, layer, rows, n`)
pair-identical; `exact = (symbol_errors == 0)` for all 256, `syndrome_ok` never
with `unsatisfied_checks > 0`, exact-true/syndrome-false = 0; crash 0,
nonfinite 0, watchdog 0; statuses `converged_exact` 83 / `converged_no_syndrome`
173; work arithmetic `check_node_updates = rows × iterations` and
`check_edge_updates = disclosed-degree-sum × iterations` with 0 mismatches
(iteration-0 records 0); all 128 paired rows and all eight stratum labels
recompute exactly; terminal T1–T10 recomputes to
`D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; root read twice identical; all
authorization keys false. Compact recomputation record (`problems: []`,
`ok: true`): records 256, pairs 128, aggregates
`layered_exact 43 / flooding_exact 40 / layered_only 3 / flooding_only 0 /
both 40 / neither 85` (syndrome-only `3/0/40/85`), layered-only identities
`[26, 46, 101]`, labels `[EXACT_TIE_LOW, MIXED_SCHEDULE_EFFECT, EXACT_TIE_LOW,
EXACT_TIE_LOW, EXACT_TIE_LOW, EXACT_TIE_HIGH, EXACT_TIE_LOW, EXACT_TIE_HIGH]`,
iterations `{ROW_LAYERED 8021, FLOODING 8444}`, node updates
`{395067, 417423}`, edge updates `{1185201, 1252269}`, stored wall
`65.94506893705693` s, max call `0.4358317470032489` s, RSS `105304064` B,
outer wall `67.17821956600528` s, flooding/layered-advantage strata `0/0`,
stratum-complete `true`, statuses `{converged_exact 83, converged_no_syndrome
173}`, seven-file sizes `{command_log 290, decoder_records 57659, manifest
3164, paired_schedule 17690, report 455, stratum_summary 1777, summary 1546}`.
No artifact was repaired.

## Paired table (exact and syndrome-only kept separate)

128 identities; `layered_only + flooding_only + both + neither = 128`.

| pair statistic | exact | syndrome-only |
|---|---|---|
| layered | 43 | 43 |
| flooding | 40 | 40 |
| layered-only | 3 | 3 |
| flooding-only | 0 | 0 |
| both | 40 | 40 |
| neither | 85 | 85 |

Three layered-only identities: 26 (1.0/2026091306/L1_ORACLE_U2), 46
(1.0/2026091311/L1_ORACLE_U2), 101 (1.2/2026091309/L1_MARGINAL).

## Eight strata (labels with counts; `blocks = 16`)

| # | f | layer | condition | L exact | F exact | lo | fo | both | neither | label |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0 | L1 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 2 | 1.0 | L1 | L1_ORACLE_U2 | 10 | 8 | 2 | 0 | 8 | 6 | MIXED_SCHEDULE_EFFECT |
| 3 | 1.0 | L2 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 4 | 1.0 | L2 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 15 | EXACT_TIE_LOW |
| 5 | 1.2 | L1 | L1_MARGINAL | 3 | 2 | 1 | 0 | 2 | 13 | EXACT_TIE_LOW |
| 6 | 1.2 | L1 | L1_ORACLE_U2 | 16 | 16 | 0 | 0 | 16 | 0 | EXACT_TIE_HIGH |
| 7 | 1.2 | L2 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 8 | 1.2 | L2 | L2_ORACLE_U1 | 13 | 13 | 0 | 0 | 13 | 3 | EXACT_TIE_HIGH |

Flooding-advantage strata 0; layered-advantage strata 0; no stratum incomplete.

## Resource facts

- Outer harness wall `67.17821956600528` s (GNU `timeout -k 30 1800`;
  limit 1800 s + 30 s grace; exit 0, `timeout_124 false`); stored scientific
  wall `65.94506893705693` s (limit 1500 s; equals the record sum).
- Max per-call wall `0.4358317470032489` s (limit 120 s); median
  `0.316909093` s (interpolated).
- RSS `105304064` B (`peak_rss_bytes`, known, finite, positive) below
  `2147483648` B.
- Iterations total 16465 (ROW_LAYERED 8021, FLOODING 8444), min 2, max 90;
  check-node updates ROW_LAYERED 395067 / FLOODING 417423; check-edge updates
  1185201 / 1252269; `retries=0`, `reruns=0`, `resumes=0`.
- Verifier:
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}`,
  exit 0; root seven files unchanged after verify.

## Supported / unsupported claims

- Supported: per-stratum route classifications from the frozen five labels;
  one bounded run terminal; per-identity paired exact/syndrome outcomes;
  work-normalized descriptive differences; internal coherence of the single
  invocation.
- Unsupported: any schedule-superiority claim; FER, leakage,
  reconciliation-efficiency, key-rate or protocol-recovery estimate;
  cross-layer APP viability; interface acceptance; code qualification;
  promotion; R1d/G1/G2 readiness; general schedule equivalence or general
  NB-LDPC conclusion; dominance of schedule choice as the failure explanation.
  Classifications are route discriminators, not success-rate or FER estimates.

## Successor

`D7_D_SCHEDULE_EFFECT_INCONCLUSIVE` has **no frozen automatic successor**.
This main-thread ruling selects Alternative A (explicit belief provenance plus
fail-closed cross-layer consumers) as the next mainline action. No D7-E work,
forced sweep, warm-start mechanism or alternating/joint decoder is performed
or authorized here. R1d remains
`PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE` and is not a mainline
gate; G1/G2 remain unauthorized. No push.

Next gate: `BP_INTERFACE_PROVENANCE_IMPLEMENTATION`.
