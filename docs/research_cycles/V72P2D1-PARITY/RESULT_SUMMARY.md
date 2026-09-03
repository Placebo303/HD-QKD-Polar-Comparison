# V72P2D1-PARITY result summary (P8 archive, accepted close)

Cycle: V72P2D1-PARITY. Implementation/accepted plan SHA:
07744ccf3095eaa35b4c457005e268fb5ff52c41 (base ba0df2d3bea4147574e0b8224480f45c93505178,
branch formal-ir-v72p1-addendum-clean). Pre-EXECUTE PASS, Pre-RESULT PASS;
evidence: EXECUTION_PACKET.md / REVIEW_VERDICT.md / four terminal files below.
DESCRIPTIVE_ONLY. No FER / SKR / information-limit / qualification / promotion claim.

Scope: one invocation, single non-fresh diagnostic block VAL1726-1729
(session 20260123_1M_600k_0dB, registry v71_data_registry.json schema v71_data_v1,
data_sha 84d62779, CAL702..1725 shared prior), arm A (original mother) once then
arm B (degree-2 parity-column-permuted mother, col_map[1204:10239]=1204+permutation(9035)
rng=default_rng(20260902), diagnostic-only seed) once, A-then-B serial.
Invocation 240.17s (budget 1800s); A 118.97s / B 114.14s (budget 600s each,
no overrun). Authorization consumed; no rerun, no third layout, no other block, no V73.

## A/B result table (arm-level, from table.csv / results.json)

| arm | status | ckpt | iters | elapsed_s | bit | sym | syndrome+tag+control | leak_IR | total_public | accepted | exact | undetected | oracle |
|---|---|---:|---:|---:|---:|---:|---|---|---:|---|---|---|---|
| A | LADDER_EXHAUSTED | 72 | 334 | 118.97 | 3100 | 620 | 9036+64+71 | 9100 | 9171 | false | false | false | false |
| B | LADDER_EXHAUSTED | 72 | 321 | 114.14 | 3100 | 620 | 9036+64+71 | 9100 | 9171 | false | false | false | false |

Overall: COMPLETED, fatal_error null. 0 protocol-accepted, 0 verified-exact,
0 undetected (isolated, never merged into success).

## Baseline reproduction (A vs V72P2 block0)

baseline_diffs (A_measured vs block0): checkpoints 72/72, iterations 334/334,
status LADDER_EXHAUSTED, bit 3100/3100, sym 620/620, syndrome 9036/9036,
tag 64/64, control 71/71; lambda 221.22162910704503 exact-equal;
CE 7.135005172802673 within 1e-12 (here bitwise equal). Gate passed, B ran.
Mechanical M1-M7 pass: 9036x10240 nnz49620, check-degree {4:1,5:4594,6:4441},
deg2 9035 both arms; four-cycles 1196/1196, collisions 1194/1194
(graph-isomorphic under column permutation; recomputed, not hand-filled).

## Metering (disclosure accounting)

Per arm: 9036 syndrome + 64 tag = 9100 leak_IR bits; 71 CONTINUE control bits;
9171 total modelled public bits. f_model_relative 1.2455097837734634,
f_public_model_relative 1.2552274974710365 (both arms; denominator = selected
CAL-CV cross-entropy 7.135005172802673, failed attempts included).
ACK/header/authentication/transport excluded. No secret-key yield claim.

## D1-D8 boundary (per-checkpoint wrapper scalars, 72 ckpts x 2 arms)

Scalars only; no full prior / matrix / per-bit LLR / per-edge messages stored.
All 72 checkpoints both arms: D1 syndrome-recompute match, mismatch_rows 0;
D2 vs-Bob sym_errors 0, sym_match true; D3 vs-Bob bit_errors 0;
D4 APP finite, max_abs A 0.79999..0.80044 / B 0.78804..0.80020;
D5 c2v finite, iters in {4,5}, final residual A 4.5e-08..9.8e-07 /
B 5.3e-08..1.0e-06; D6 f2b/app flips 0/0; D7 deg2/rest bit errors 0/0,
mean_abs_app_deg2 ~0.4714..0.4720 both arms; D8 Alice-vs-Bob 3100 bit / 620 sym
constant, oracle_exact false, undetected false.

## Reading

On this single non-fresh block, the layout permutation alone did not move the
ladder outcome: both arms LADDER_EXHAUSTED with identical error counts and
disclosure (iteration counts differ 334 vs 321, outcome/status identical).
Single-block descriptive observation only; not generalizable, not a method verdict.

Artifacts: comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/
exactly four files (manifest.json / results.json / table.csv / report.md).
No raw symbols / syndrome bytes / fitted matrix / per-bit arrays published;
reproduction IDs and command recorded in manifest, not permission to rerun.
