# D7-D operator return R1 (unaccepted; Pre-RESULT review required)

- Status: **NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED**. This file is
  uncommitted and makes no scientific claim and no acceptance decision.
- One authorized invocation consumed and revoked. Authorization commit
  `7a3f0d922edb0a7e9a851ce482dc4c8648b80766`; revocation commit
  `eba385bb8a2294ae6940597d7bb37e3295df7946` (created before any root content
  was interpreted).
- UUID `64660d16-397d-4ef3-8454-3066d27c12c7`; root
  `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7/`
  is immutable from process exit onward (all seven files written 2026-09-11
  07:30:05 +0800 before the process returned).

## 1. Lifecycle and process evidence

- Exact child argv (JSON list as launched, `timeout` → `python` via the
  reviewed venv-on-PATH adapter; `PYTHONPATH` absent):

```json
["timeout", "-k", "30", "1800", "python",
 "scripts/v72p2d7_gf32_schedule_discriminator.py",
 "--model-f-root", "workspace/v72p2d5_model_f_input/20260907_r1",
 "--out-root", "workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7"]
```

- Invocation count: **1** (no relaunch). Exit code **0**; `timeout_124: false`.
- Harness `/tmp/d7d_exec_harness.py`; PIDs: harness 384750, `timeout` child
  384751, scientific `python` grandchild 384752. `manifest.json` records
  `"pid": 384752`, matching the harness-observed scientific process.
- Start 2026-09-11 07:28:58 +0800 / 2026-09-10 23:28:58Z; end 2026-09-11
  07:30:05 +0800 / 2026-09-10 23:30:05Z. Harness outer wall
  **67.17821956600528 s**.
- `manifest.json` start/end: `2026-09-10T23:28:59Z` / `2026-09-10T23:30:05Z`.
- Child stdout: `terminal=D7_D_SCHEDULE_EFFECT_INCONCLUSIVE out=workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7`
  (single line). Child stderr: empty. Harness error: `null`.
- Python resolution: `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`
  (CPython 3.12.3, NumPy 2.4.4); `PYTHONPATH` absent in ambient env and removed
  from the child.
- `manifest.json` `authorization_consumed: true`, `retries: 0`, `reruns: 0`,
  `resumes: 0`.
- Scientific attempt classification: **CONSUMED** — 256 decoder attempts are
  evidenced in `decoder_records.csv` (256 completed records with statuses);
  `NOT_VERIFIABLE` does not apply. Authorization remains revoked and is never
  restored.

## 2. Root inventory (complete, no partial state)

Exactly seven files, zero subdirectories:

| File | Bytes | mtime (+0800) |
|------|-------|---------------|
| `manifest.json` | 3164 | 2026-09-11 07:30:05.509 |
| `decoder_records.csv` | 57659 | 2026-09-11 07:30:05.515 |
| `paired_schedule.csv` | 17690 | 2026-09-11 07:30:05.517 |
| `stratum_summary.csv` | 1777 | 2026-09-11 07:30:05.519 |
| `summary.json` | 1546 | 2026-09-11 07:30:05.521 |
| `report.md` | 455 | 2026-09-11 07:30:05.523 |
| `command_log.txt` | 290 | 2026-09-11 07:30:05.525 |

No missing files; no honest-partial condition applies.

## 3. Frozen matrix, order and scheduled/invoked/missing/duplicate counts

- Scheduled 256; attempted/invoked 256; completed 256; remaining 0; missing 0;
  duplicates 0 (`decoder_records.csv` has exactly 256 unique `call_idx` 1..256).
- Parity: odd `call_idx` = `ROW_LAYERED`, even = `FLOODING` (all 256 verified).
- Identity coverage: each schedule covers identities 1..128 exactly once
  (128 + 128); each `call_idx` maps to `identity_idx` via `2k-1`/`2k` (verified).
- Frozen matrix recomputation from the manifest constants (16 seeds × 2 f ×
  4 conditions, rows 49/59/43/52): **0 mismatches**.
- Order: `for f in [1.0,1.2]: for seed in 2026091300..2026091315: for condition
  in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]: ROW_LAYERED;
  FLOODING`. First call (1, 1.0, 2026091300, L1_MARGINAL, ROW_LAYERED, 49);
  last call (256, 1.2, 2026091315, L2_ORACLE_U1, FLOODING, 52).
- `summary.json`: `calls_attempted=256`, `calls_completed=256`,
  `calls_remaining=0`, `stop_terminal=""`.

## 4. Paired exact and syndrome-only counts (all 128 identities)

Aggregates: `layered_exact=43`, `flooding_exact=40`, `layered_only_exact=3`,
`flooding_only_exact=0`, `both_exact=40`, `neither_exact=85`. Syndrome-only
analogues: `layered_only_syndrome_ok=3`, `flooding_only_syndrome_ok=0`,
`both_syndrome_ok=40`, `neither_syndrome_ok=85`. `layered_only_exact` identities
are 26 (1.0/2026091306/L1_ORACLE_U2), 46 (1.0/2026091311/L1_ORACLE_U2) and 101
(1.2/2026091309/L1_MARGINAL). Pair flag recomputation from `decoder_records.csv`:
0 mismatches. `iteration_diff`, `check_update_diff`/`edge_update_diff` and
`wall_ratio` are non-empty for all 128 pairs; `iteration_diff` is 0 for 85 pairs
and non-zero for 43.

Table columns: identity_idx, f, seed, condition, layered_exact, flooding_exact,
layered_only_exact, flooding_only_exact, both_exact, neither_exact,
layered_only_syndrome_ok, flooding_only_syndrome_ok, both_syndrome_ok,
neither_syndrome_ok, iteration_diff, wall_ratio (flooding/layered).

| 1 | 1.0 | 2026091300 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.8348915523203967 |
| 2 | 1.0 | 2026091300 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0501387366365382 |
| 3 | 1.0 | 2026091300 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0286607049629133 |
| 4 | 1.0 | 2026091300 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.879948951261141 |
| 5 | 1.0 | 2026091301 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0372331131657957 |
| 6 | 1.0 | 2026091301 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9456773084884779 |
| 7 | 1.0 | 2026091301 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9001105684911769 |
| 8 | 1.0 | 2026091301 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9902136476533363 |
| 9 | 1.0 | 2026091302 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9857369545083181 |
| 10 | 1.0 | 2026091302 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 2.0691700307980136 |
| 11 | 1.0 | 2026091302 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9888817581679146 |
| 12 | 1.0 | 2026091302 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.984170737165773 |
| 13 | 1.0 | 2026091303 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9891872920447589 |
| 14 | 1.0 | 2026091303 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0165654840042613 |
| 15 | 1.0 | 2026091303 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0384291130938945 |
| 16 | 1.0 | 2026091303 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9546396010815319 |
| 17 | 1.0 | 2026091304 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9463522480513451 |
| 18 | 1.0 | 2026091304 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.7432289265085394 |
| 19 | 1.0 | 2026091304 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9956856876617987 |
| 20 | 1.0 | 2026091304 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9824328855374977 |
| 21 | 1.0 | 2026091305 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.940783613280081 |
| 22 | 1.0 | 2026091305 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9867371632930537 |
| 23 | 1.0 | 2026091305 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.956396438503961 |
| 24 | 1.0 | 2026091305 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.950368559667423 |
| 25 | 1.0 | 2026091306 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9862852589185872 |
| 26 | 1.0 | 2026091306 | L1_ORACLE_U2 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 56 | 2.5574145962351094 |
| 27 | 1.0 | 2026091306 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9911792870355234 |
| 28 | 1.0 | 2026091306 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 1.6962356481719572 |
| 29 | 1.0 | 2026091307 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9805129426117805 |
| 30 | 1.0 | 2026091307 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 2.1087468348648497 |
| 31 | 1.0 | 2026091307 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0217717709857586 |
| 32 | 1.0 | 2026091307 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9926871508941129 |
| 33 | 1.0 | 2026091308 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9776210848787232 |
| 34 | 1.0 | 2026091308 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9926817786502921 |
| 35 | 1.0 | 2026091308 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9865575136521703 |
| 36 | 1.0 | 2026091308 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9889929984157 |
| 37 | 1.0 | 2026091309 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9834859629351678 |
| 38 | 1.0 | 2026091309 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.6915515412280828 |
| 39 | 1.0 | 2026091309 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9776164449483085 |
| 40 | 1.0 | 2026091309 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.974628128963161 |
| 41 | 1.0 | 2026091310 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9918558940431567 |
| 42 | 1.0 | 2026091310 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 16 | 2.91354517872991 |
| 43 | 1.0 | 2026091310 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.990735422350055 |
| 44 | 1.0 | 2026091310 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9607205882653213 |
| 45 | 1.0 | 2026091311 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9903149626912563 |
| 46 | 1.0 | 2026091311 | L1_ORACLE_U2 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 80 | 8.730447342721881 |
| 47 | 1.0 | 2026091311 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9814127615436308 |
| 48 | 1.0 | 2026091311 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.006702105116291 |
| 49 | 1.0 | 2026091312 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9914866490785409 |
| 50 | 1.0 | 2026091312 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.9538381914128118 |
| 51 | 1.0 | 2026091312 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.00154303755534 |
| 52 | 1.0 | 2026091312 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0070072645898767 |
| 53 | 1.0 | 2026091313 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9952746754205479 |
| 54 | 1.0 | 2026091313 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 2.581212090606103 |
| 55 | 1.0 | 2026091313 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9813030003296868 |
| 56 | 1.0 | 2026091313 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9903357096844343 |
| 57 | 1.0 | 2026091314 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9853089096581016 |
| 58 | 1.0 | 2026091314 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 1.6220217070248932 |
| 59 | 1.0 | 2026091314 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9902756330059287 |
| 60 | 1.0 | 2026091314 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9981769109377746 |
| 61 | 1.0 | 2026091315 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9912676935026081 |
| 62 | 1.0 | 2026091315 | L1_ORACLE_U2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9855252600657188 |
| 63 | 1.0 | 2026091315 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0152151650252412 |
| 64 | 1.0 | 2026091315 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9730667484021999 |
| 65 | 1.2 | 2026091300 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9717681268216889 |
| 66 | 1.2 | 2026091300 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 1.6593554603338867 |
| 67 | 1.2 | 2026091300 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0008912126231402 |
| 68 | 1.2 | 2026091300 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 13 | 1.568433396853866 |
| 69 | 1.2 | 2026091301 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9852458499206376 |
| 70 | 1.2 | 2026091301 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.437085011946238 |
| 71 | 1.2 | 2026091301 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9860255193911128 |
| 72 | 1.2 | 2026091301 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 1.9840106127620634 |
| 73 | 1.2 | 2026091302 | L1_MARGINAL | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 9 | 1.9680324341968314 |
| 74 | 1.2 | 2026091302 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.647795265713808 |
| 75 | 1.2 | 2026091302 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9746794322090587 |
| 76 | 1.2 | 2026091302 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.648361580975942 |
| 77 | 1.2 | 2026091303 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9971394519649643 |
| 78 | 1.2 | 2026091303 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.5794974809937428 |
| 79 | 1.2 | 2026091303 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9730160554809313 |
| 80 | 1.2 | 2026091303 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9772933502668992 |
| 81 | 1.2 | 2026091304 | L1_MARGINAL | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 6 | 1.8185924370824826 |
| 82 | 1.2 | 2026091304 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 2.0073910149024776 |
| 83 | 1.2 | 2026091304 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.987798399935176 |
| 84 | 1.2 | 2026091304 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | 1.8916677417709729 |
| 85 | 1.2 | 2026091305 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9719917125723637 |
| 86 | 1.2 | 2026091305 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 66 | 8.88504440555696 |
| 87 | 1.2 | 2026091305 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9832995780514752 |
| 88 | 1.2 | 2026091305 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 13 | 1.822475225841628 |
| 89 | 1.2 | 2026091306 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9745906646055674 |
| 90 | 1.2 | 2026091306 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.465220732018039 |
| 91 | 1.2 | 2026091306 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9933782272529001 |
| 92 | 1.2 | 2026091306 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 2.0000072797534445 |
| 93 | 1.2 | 2026091307 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9956458404352041 |
| 94 | 1.2 | 2026091307 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.8892745478814361 |
| 95 | 1.2 | 2026091307 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0127161324467548 |
| 96 | 1.2 | 2026091307 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 6 | 1.9260013803668934 |
| 97 | 1.2 | 2026091308 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.985602839838371 |
| 98 | 1.2 | 2026091308 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.722415693872085 |
| 99 | 1.2 | 2026091308 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9986606022262937 |
| 100 | 1.2 | 2026091308 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 6 | 1.6273713838297048 |
| 101 | 1.2 | 2026091309 | L1_MARGINAL | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 10 | 1.1060112995575955 |
| 102 | 1.2 | 2026091309 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 1.2591834955670718 |
| 103 | 1.2 | 2026091309 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9636949243325148 |
| 104 | 1.2 | 2026091309 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9966809591778751 |
| 105 | 1.2 | 2026091310 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9929694533761735 |
| 106 | 1.2 | 2026091310 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.3573443981876088 |
| 107 | 1.2 | 2026091310 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9989436437772906 |
| 108 | 1.2 | 2026091310 | L2_ORACLE_U1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9974597380317323 |
| 109 | 1.2 | 2026091311 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.965366154713094 |
| 110 | 1.2 | 2026091311 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.9821390969940529 |
| 111 | 1.2 | 2026091311 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9873084598572919 |
| 112 | 1.2 | 2026091311 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 7 | 1.6681578521862703 |
| 113 | 1.2 | 2026091312 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9826089776529199 |
| 114 | 1.2 | 2026091312 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 1.3091150434248817 |
| 115 | 1.2 | 2026091312 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0045260555476525 |
| 116 | 1.2 | 2026091312 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 4 | 1.807374076049222 |
| 117 | 1.2 | 2026091313 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9808172581997708 |
| 118 | 1.2 | 2026091313 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 2.0285068809125892 |
| 119 | 1.2 | 2026091313 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 1.0205981933759956 |
| 120 | 1.2 | 2026091313 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 18 | 2.0351203185652813 |
| 121 | 1.2 | 2026091314 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9742888153067735 |
| 122 | 1.2 | 2026091314 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 2 | 1.7119157419556525 |
| 123 | 1.2 | 2026091314 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9701417282172575 |
| 124 | 1.2 | 2026091314 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 1.736354373867143 |
| 125 | 1.2 | 2026091315 | L1_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9758603126230949 |
| 126 | 1.2 | 2026091315 | L1_ORACLE_U2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 11 | 2.4919577712798873 |
| 127 | 1.2 | 2026091315 | L2_MARGINAL | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0.9890599150353774 |
| 128 | 1.2 | 2026091315 | L2_ORACLE_U1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 18 | 2.065982828640741 |

## 5. Eight strata and stored terminal

| idx | f | layer | condition | blocks | layered_exact | flooding_exact | layered_only | flooding_only | both | neither | label |
|-----|---|-------|-----------|--------|---------------|----------------|--------------|---------------|------|---------|-------|
| 1 | 1.0 | L1 | L1_MARGINAL | 16 | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 2 | 1.0 | L1 | L1_ORACLE_U2 | 16 | 10 | 8 | 2 | 0 | 8 | 6 | MIXED_SCHEDULE_EFFECT |
| 3 | 1.0 | L2 | L2_MARGINAL | 16 | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 4 | 1.0 | L2 | L2_ORACLE_U1 | 16 | 1 | 1 | 0 | 0 | 1 | 15 | EXACT_TIE_LOW |
| 5 | 1.2 | L1 | L1_MARGINAL | 16 | 3 | 2 | 1 | 0 | 2 | 13 | EXACT_TIE_LOW |
| 6 | 1.2 | L1 | L1_ORACLE_U2 | 16 | 16 | 16 | 0 | 0 | 16 | 0 | EXACT_TIE_HIGH |
| 7 | 1.2 | L2 | L2_MARGINAL | 16 | 0 | 0 | 0 | 0 | 0 | 16 | EXACT_TIE_LOW |
| 8 | 1.2 | L2 | L2_ORACLE_U1 | 16 | 13 | 13 | 0 | 0 | 13 | 3 | EXACT_TIE_HIGH |

- All eight labels recompute by the frozen first-match rules (0 mismatches);
  no stratum is incomplete; flooding-advantage strata 0; layered-advantage
  strata 0.
- Stored run terminal: **`D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`**; independently
  recomputed from the frozen priority list as identical.
- `summary.json` records the same terminal and the eight labels; `report.md`
  and `command_log.txt` repeat the terminal and `calls_completed: 256`.

## 6. Iterations, node/edge work, crashes, nonfinite, status and mismatches

- Statuses: `converged_exact` 83, `converged_no_syndrome` 173; crash records 0;
  nonfinite records 0; watchdog timeouts 0.
- Iterations: total 16465 (ROW_LAYERED 8021, FLOODING 8444); min 2, max 90;
  iteration-0 records 0. Iteration counts are reported as descriptive
  work-normalized quantities only; no winner is inferred from them.
- Work arithmetic (all 256 records): `check_node_updates == rows × iterations`
  and `check_edge_updates == disclosed-row-degree-sum × iterations` with
  manifest sums L1 49→147/59→177, L2 43→129/52→156; **0 mismatches**.
  Totals: node updates ROW_LAYERED 395067 / FLOODING 417423; edge updates
  1185201 / 1252269.
- Exact/syndrome mismatch arithmetic: `exact != (symbol_errors == 0)` 0
  records; `syndrome_ok` with `unsatisfied_checks > 0` 0 records; `exact` true
  with `syndrome_ok` false 0 records. Exact and syndrome-only remain separate
  fields; no merging.
- Belief diagnostics: all rows labeled `CHECK_UPDATED_CURRENT_BELIEF`
  (`beliefs_conditioned=True`; no iteration-0 `PRIOR_ONLY` row); scalar
  `belief_max_prob` range 0.403067..1.000000, `belief_mean_entropy` range
  0.000000..4.343407 bits. These are current-belief diagnostics, not posterior
  or APP claims.

## 7. Walls, RSS, watchdog and budget comparison

- Per-call wall: min 0.009717 s, median 0.316909093 s (interpolated; upper-middle order statistic 0.318371 s), max 0.435832 s; sum
  65.945069 s. `summary.json` `stored_wall_s = 65.94506893705693` (equals the
  record sum), limit 1500 s → **no overrun**.
- Outer GNU `timeout -k 30 1800`: wall 67.17821956600528 s, exit 0,
  `timeout_124 false` → **no outer watchdog**.
- Per-call watchdog: max 0.435832 s vs 120 s; `watchdog_timeouts=0`.
- RSS: all 256 records `rss_bytes=105304064`; `summary.json` peak
  105304064 B < 2147483648 B → **no RSS stop**. (Environmental note: the
  gate-time bash-sandbox probe reported a constant inflated `ru_maxrss`
  1257320 KiB while `/proc` VmHWM was ~10 MB; the scientific process recorded
  its own in-process stdlib value, 105.3 MB, which is the frozen measurement.)
- `retries=0`, `reruns=0`, `resumes=0`; one invocation only.

## 8. Schedule-only identity proof and scalar-payload disclosure

- Scalar non-schedule inputs (f, seed, condition, layer, rows, n) are equal
  within every one of the 128 identity pairs: **0 mismatches**. The frozen
  implementation computes block, prior, mother prefix and syndrome once per
  identity and dispatches both schedules on the same objects (array-level byte
  equality pinned by the frozen S03 test); raw arrays are not persisted, so
  array-level equality is not independently re-verifiable from the seven scalar
  files — this limitation is stated honestly.
- `decoder_records.csv` fields (25): call_idx, identity_idx, schedule, f, seed,
  condition, layer, rows, n, exact, syndrome_ok, iterations, status, finite,
  symbol_errors, unsatisfied_checks, wall_s, rss_bytes, check_node_updates,
  check_edge_updates, belief_max_prob, belief_mean_true_p, belief_mean_entropy,
  beliefs_conditioned, current_belief_label.
- `paired_schedule.csv` fields (23): identity_idx, f, seed, condition, layer,
  rows, n, layered_exact, flooding_exact, layered_only_exact,
  flooding_only_exact, both_exact, neither_exact, layered_syndrome_ok,
  flooding_syndrome_ok, layered_only_syndrome_ok, flooding_only_syndrome_ok,
  both_syndrome_ok, neither_syndrome_ok, iteration_diff, check_update_diff,
  edge_update_diff, wall_ratio.
- Scalar-payload scan: no posterior/APP/belief-vector/symbol-vector/
  syndrome-vector/digest fields; no raw beliefs, symbols, priors, syndromes,
  block vectors or digests persisted. No cross-layer APP and no cross-layer
  returned beliefs; the layer interface remains
  `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP` and was not touched.

## 9. Nonclaims

**NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED.** No result publication,
solidification, commit or scientific conclusion is made here. Schedule
classifications are route discriminators, not FER or success-rate estimates.
This return establishes no FER, leakage, reconciliation efficiency, key rate,
protocol recovery, cross-layer APP viability, interface acceptance, code
qualification, R1d/G1/G2 readiness, promotion or general GF32/NB-LDPC result.
Oracle conditions remain counterfactual diagnostics and are not disclosure or
protocol recovery. The stored terminal is internal to the frozen contract and
requires independent Pre-RESULT recomputation before any acceptance step.

## 10. Verifier invocation (read-only, exactly once)

```text
$ PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python scripts/v72p2d7_gf32_schedule_discriminator.py --verify workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7
VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}
exit=0
```

- Invoked once; no retry. The verifier calls no decoder and loads no Model-F.
- Root names/sizes/mtime identical before and after verify
  (`ROOT_BYTES_MTIME_UNCHANGED`); the verify was read-only.
- Verifier limitations: it recomputes pairing, paired counts, all eight strata,
  work arithmetic and the terminal from the seven scalar files; it does not
  re-execute decoders or re-derive raw arrays.
