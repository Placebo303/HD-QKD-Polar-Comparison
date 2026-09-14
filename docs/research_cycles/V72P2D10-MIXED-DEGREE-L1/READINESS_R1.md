# D10 mixed-degree L1 finite discriminator — heavy R1 readiness

Status: `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION` (F01–F12
complete; grants no execution; creates no root; the frozen future L1 batch
still requires a separate explicit authorization).
Track: readiness/design only; the frozen future L1 batch is `EXPLORE_HEAVY` and
requires a separate explicit authorization.
Authority: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_FINITE_READINESS_R1_TASK_PACKET.md`
(§2 isolation, §3 graph/coefficient requirements, §4 experiment design, §5
allowed files, §6 F01–F12, §7 routing, §8 STOP, §9 return).
Predecessor: `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`.
Branch: `formal-ir-v72p1-addendum-clean` (not switched; no commit, no push).
Scope of this record: F01–F10 (F01–F05 design freeze; F06–F10 implementation,
focused tests and pre-decoder profile). Production decoder calls: **0**.
Scientific L1 calls: **0**. DE calls: **0**. CAL/VAL/raw/real-data contact:
**0**. Root created: **none**. Authorization flags: all false.
Change: `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/`.
independent_review_verdict: PASS_WITH_FINDINGS
independent_review_artifact: docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/INDEPENDENT_REVIEW_R1.md
f12_correction: F2 applied (replacement seeds 2026092210..2026092215 enumerated in design/spec; scoped re-review RESOLVED/PASS)
carried_findings: F1_F3_F4_F5
future_root_absent: true
authorization_flags: all false
next_gate: D10_MIXED_DEGREE_L1_BATCH_EXPLICIT_AUTHORIZATION
memory_triage: DEFERRED_UNTIL_ACCEPTED_TRIAGE

## F01 — Accepted D9 evidence (read-only; no DE rerun)

Artifacts read only:

- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/READINESS_R1.md`:
  `:25` accepted_terminal `D9_DE_CALIBRATION_SELECT_ONE`; `:26`
  accepted_candidate `lam_d2_0.45_d3_0.55`; `:27` main_route_decision
  `D10_MIXED_DEGREE_L1_FINITE_READINESS`; `:31-37` batch root,
  `batch_calls: 96`, `batch_setup: 4`, review `PASS_WITH_FINDINGS`.
- `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/EXPLORATION_LOG.md`:
  `:314-334` per-candidate S4000/S16000 and per-seed failure lists; `:353-368`
  stored terminal/eligible set/rank; `:430-450` independent batch-end review;
  `:452-469` main-thread acceptance (`:468` lifecycle
  `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`).
- D9 root `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/`:
  - `summary.json`: `terminal = D9_DE_CALIBRATION_SELECT_ONE`,
    `terminal_reason = null`, `winner_candidate_id = lam_d2_0.45_d3_0.55`,
    `eligible_candidate_ids = ["lam_d2_0.45_d3_0.55"]`,
    `baseline_stability = stable_unconverged`, `semantics_pass = true`,
    `graph_valid = true`, `de_calls = 96`, `refusal_count = 0`, `wall_s =
    118.61216687600245`, `peak_rss_bytes = 274210816`;
    `claim_ceiling` (raw): "calibration-contract evidence under the frozen
    CAL-only Model-F channel and decoder contract; no
    finite-length/FER/leakage/SKR/qualification/promotion/real-data claim; a
    selection authorizes only the next finite-length synthetic task packet and
    does not revive D7-H".
  - `candidate_summary.csv` (4 candidate rows), stability columns
    `s4000_f12,s16000_f12`: DV3 `0,0` `stable_unconverged`/`eligible=False`;
    0.45 `8,8` `stable_converged`/`eligible=True`; 0.50 `7,8`
    `stability_ambiguous`/`eligible=False`; 0.55 `6,4` `stable_unconverged`/
    `eligible=False`.
  - `de_records.csv`: 96 rows, `call_idx` 0..95; independent recount of
    `converged` at f1.2 reproduces S4000/S16000 = DV3 0/0, 0.45 8/8, 0.50 7/8,
    0.55 6/4.
  - `manifest.json`: budgets (`max_de_calls: 96`, `max_setup_calls: 12`,
    `per_call_s: 300`, `wall_s: 1200`, `rss_bytes: 2147483648`, `processes: 1`,
    `retry/resume/adaptive_stop: false`), `l1_only: true`, field q=32/poly37.

Claim ceiling recorded: DE-only calibration/ensemble-screen evidence; no
decoder/FER/leakage/SKR/qualification/promotion/real-data claim; lambda2 0.50
was not promoted despite lower AUT_30 because it failed the frozen 8/8 rule.

Pointer note (non-blocking): the D10 packet §"read first" refers to
`candidate_summary.csv` "N2 columns"; that CSV has no N2 columns. The N2
cross-check was performed against `summary.json` `graph.cells` (f1.2 cells),
which carries `n2/n3/E`, plus the D9 `design.md` §5 table.

## F02 — Builder inventory and selection

Full table with path:line and rejection reasons: `design.md` §2. Result: no
existing builder honors an arbitrary exact variable-degree sequence *and* exact
check-degree counts (B1 `nonbinary_v10_peg.peg_construct:276-458` takes
`lambda`/`rho` and re-derives counts; B2
`nonbinary_v7_r3_codebook._construct:191-230` takes explicit degrees but is
`_N=1024`-bound and has no exact check counts; B3–B7 are regular/DV3/support
constructors). Selected **B8**, one minimal deterministic degree-sequence PEG
`build_degree_sequence_peg` in the D10 `formal_ir` module, reusing read-only
`nonbinary_v10_peg._tie_pick` (`:265-273`), `._bfs_distance` (`:461-475`),
`._ace_score` (`:478-495`) and `nonbinary_v10_common.v10_seed` (`:340-349`).

## F03 — Frozen degree tables, seeds, coefficients, blocks, call order, gates

Exact f1.2 realizations (L1), transcribed from D9 `design.md` §5 (`:244-259`)
and cross-checked read-only against the D9 root `summary.json` `graph.cells`:

| arm | n | m | n2 | n3 | E | check alloc | min/max dc |
|---|---|---|---|---|---|---|---|
| `PEG_DV3_MATCHED` | 64 | 59 | 0 | 64 | 192 | `3^44 + 4^15` | 3/4 |
| `PEG_DV3_MATCHED` | 128 | 118 | 0 | 128 | 384 | `3^88 + 4^30` | 3/4 |
| `PEG_DV3_MATCHED` | 256 | 236 | 0 | 256 | 768 | `3^176 + 4^60` | 3/4 |
| `PEG_DV23_LAM2_045` | 64 | 59 | 35 | 29 | 157 | `2^20 + 3^39` | 2/3 |
| `PEG_DV23_LAM2_045` | 128 | 118 | 71 | 57 | 313 | `2^41 + 3^77` | 2/3 |
| `PEG_DV23_LAM2_045` | 256 | 236 | 141 | 115 | 627 | `2^81 + 3^155` | 2/3 |

Read-only in-memory cross-check (2026-09-14; no file written): `v10.node_view_counts`
and `v37.calculate_node_degree_counts` agree with each other and with the D9
root `graph.cells` `n2/n3/E` on all six cells; `v10.check_degree_counts` over
the exact m-fraction allocation reproduces the six check allocations exactly.

Graph seeds (fresh; absent from `docs/`, `openspec/`, `scripts/`, `.workbuddy/`,
`comparison_bench/src`, `comparison_bench/tests`, `analysis/`, top-level
`*.md`): n64 `2026092201..2026092203`; n128 `2026092204..2026092206`; n256
`2026092207..2026092209`. Block seeds (fresh, same scan): n64
`2026092301..2026092308`; n128 `2026092311..2026092318`; n256
`2026092321..2026092328`. Coefficient rule:
`v10_seed(f"d10:coeff:{width}:{graph_seed}")` -> `default_rng` -> one
`integers(1, 32)` per edge in sorted `(variable, check)` order, uniform nonzero
GF32, same rule both arms.

Call order: width (conditional) -> control then candidate -> graph seed
ascending -> block seed ascending; paired identical blocks sampled once per
`(width, block_seed)` by `sample_matched_block`. Structural gates G1–G10
frozen in `design.md` §5.

## F04 — Thresholds, progression, claim ceiling

`POSITIVE(w)`: `S_g(MIX)>=3` for all 3 graphs AND `E_g(MIX)>=2` for >=2 graphs
AND `S_pool(MIX)>=12` AND `E_pool(MIX)>=6` AND `S_pool(DV3)<=3` AND
`E_pool(DV3)<=1`. `NEGATIVE(w)`: `E_pool(MIX)<=2` AND `S_pool(MIX)<=4`.
Otherwise `AMBIGUOUS(w)` (not pooled-only, no single rescued block).
Progression: n64 -> n128 -> n256, each next width dispatched only under
POSITIVE of the previous. Full ceiling 144 scientific L1 calls; no L2 budget
consumption. Terminals/routing and claim ceiling: `design.md` §6–§7 (packet
§7): reproducible candidate -> separate L2/APP proposal (D7-H not revived);
n64-only -> finite-size signal; no advantage -> close the `{2,3}` realization;
engineering block -> no algorithm conclusion. No L2/APP, FER/leakage/SKR/
qualification/promotion/real-data claim.

## F05 — OpenSpec, future root/command, budgets

Created (docs/design only):

- `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/{proposal.md,design.md,tasks.md,specs/mixed-degree-l1-finite-discriminator/spec.md}`;
- `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md` (this file);
- `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/EXPLORATION_LOG.md`;
- one `docs/decision-log.md` entry.

Fresh future root UUID `b2dd13e4-6600-4e27-90df-5c9038cf2c34`: verified ABSENT
at `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`; the
literal UUID is absent from the scanned source directories at freeze time.

Exact future command (left absent and unauthorized):

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
```

Budgets: <=144 scientific L1 calls; <=44 setup units (18 graph constructions +
24 block samplings + 2 fixed); wall <=1800 s; per-call <=120 s checked
between/after calls; RSS <2 GiB strict; single process; no
retry/resume/seed-search/adaptive-stop.

## F06–F10 — Implementation, tests, profile and frozen-match check (2026-09-14)

Implemented within the allowed files only (no commit, no push, no branch
switch; unrelated dirty files preserved):

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  — B8 `build_degree_sequence_peg` (reuses read-only
  `nonbinary_v10_peg._tie_pick/_bfs_distance/_ace_score` and
  `nonbinary_v10_common.v10_seed`; one attempt per seed; fails loud on count
  sequences that cannot satisfy socket balance), structural gates G1–G6 plus
  reported G7–G9 diagnostics, coefficient rule, frozen degree tables, plan,
  thresholds, progression/terminal routing, injected-decoder `execute_plan` /
  `dispatch_l1`, profile and root refusal.
- `scripts/v72p2d10_mixed_degree_l1_development.py` — `--batch` (refused while
  `BATCH_AUTHORIZED` is false; production decoder injected only by this
  runner), `--verify` (read-only recomputation, zero skip, zero decoder
  calls) and `--profile-only` (stdout only); six-file root, root refusal,
  budgets, single process, no retry/resume/seed search/adaptive stop.
- `comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py` — 26 focused
  fake/tiny tests.

F06: the six f1.2 degree cells were re-verified read-only against the D9 root
`summary.json` `graph.cells` (`n`/`m`/`n2`/`n3`/`E` all match; cross-check
`D9_CROSSCHECK_OK`).

F09 focused tests (fresh task-owned basetemp, no cache provider):

```text
.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py \
  -p no:cacheprovider -o addopts= \
  --basetemp=workspace/d10_f08_f09_tests_9e4d2c71-6b3f-4a58-9c0d-7e21f4b8a6d3 -q
# 26 passed (T0/T1)
```

`py_compile` OK on the module, the runner and the test file.

F09 `--profile-only` (real builders, no decoder, no root; total wall
0.481 s; 18/18 graphs `status=ok`, `admitted=True`; seed replacements 0;
frozen-seed failures 0):

| width | arm | wall s (3 seeds) | rank | components | largest frac | N2 | 4-cycles | girth |
|---|---|---|---|---|---|---|---|---|
| 64 | `PEG_DV3_MATCHED` | 0.0149/0.0063/0.0058 | 58/58/59 | 16/15/17 | 0.125/0.141/0.125 | 0 | 148/137/174 | 4 |
| 64 | `PEG_DV23_LAM2_045` | 0.0050/0.0046/0.0046 | 59/58/58 | 9/11/9 | 0.281/0.250/0.297 | 35 | 60/54/49 | 4 |
| 128 | `PEG_DV3_MATCHED` | 0.0174/0.0168/0.0171 | 118/118/118 | 32/35/33 | 0.125/0.086/0.094 | 0 | 325/369/333 | 4 |
| 128 | `PEG_DV23_LAM2_045` | 0.0141/0.0135/0.0134 | 118/118/116 | 19/19/21 | 0.141/0.156/0.117 | 71 | 102/107/98 | 4 |
| 256 | `PEG_DV3_MATCHED` | 0.0626/0.0615/0.0631 | 233/233/235 | 67/68/64 | 0.051/0.039/0.039 | 0 | 690/685/617 | 4 |
| 256 | `PEG_DV23_LAM2_045` | 0.0541/0.0529/0.0534 | 234/235/234 | 37/36/42 | 0.078/0.059/0.066 | 141 | 207/203/210 | 4 |

Reported diagnostics for the batch-end review (never repaired, no gate uses
them): min check degree 3 (DV3) / 2 (mixed); degree-2 cycle-rank lower bound 0
in every graph (`N2 <= m-1`); girth 4 in every graph; rank below `m` in
several graphs (e.g. 58/59, 116/118, 233–235/236); the capacity-constrained
PEG leaves 9–68 connected components with largest-component fraction
0.039–0.297. The pre-decoder seed-replacement clause was not used.

F10 frozen-match check (read-only): `FROZEN_COMMAND_MATCH=True`;
runner defaults `--model-f-root` == `workspace/v72p2d5_model_f_input/20260907_r1`
and `--out-root` required; budgets 144/44/1800 s/120 s/2147483648 B;
`BATCH_AUTHORIZED=False`; future root
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` ABSENT.
Tasks `tasks.md` F06–F10 marked `[x]`; F11–F12 remain open.

## State

F01–F10 complete (design freeze, implementation, focused tests, pre-decoder
profile and frozen-match check). No production decoder call, no scientific L1
call, no decoder dispatch, no root, no commit, no push; all authorization
flags false. Next: F11 one independent reviewer-go review of graph
mathematics, isolation, decoder-entry boundary, thresholds and the frozen
command; then at most one scoped non-scientific correction (F12) and the
`D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION` marker. The
future L1 batch still requires
`D10_MIXED_DEGREE_L1_SEPARATE_EXPLICIT_AUTHORIZATION`.

## 2026-09-14 — main-thread readiness decision

`REVISE_REQUIRED_CONNECTIVITY_AND_RANK`; the R1 batch is not authorized.
The independent review and its tests are accepted as trustworthy. Its F4
evidence is elevated from a non-blocking interpretation caveat to a scientific
readiness blocker: every profiled Tanner graph is fragmented (9--68 connected
components; largest-component fraction 0.039--0.297), and several parity-check
matrices have rank below `m`. A decoder comparison on these graphs would not
isolate the forced variable-degree profile; it would also compare different
component decompositions and effective constraint ranks.

The R1 implementation and all evidence are retained. No seed replacement,
decoder run, output-root creation, or authorization is permitted from this
readiness record. The successor is
`.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md`.

## 2026-09-14 — main-thread R2 acceptance

`D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The traceable independent R211 `EVIDENCE_ACCESS: VERIFIED / PASS` is accepted
without duplicating its tests. All 18 frozen cells pass A1--A6 with one Tanner
component, structural rank `m`, GF32 rank `m`, zero seed replacements and zero
decoder/scientific calls. N1--N3 are non-blocking as reviewed. This accepts
readiness only and grants no execution. Next packet:
`.workbuddy/tasks/D10_MIXED_DEGREE_L1_BATCH_A1_TASK_PACKET.md`.
