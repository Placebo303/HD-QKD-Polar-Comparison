# D7-B easy-regime — proposal (R1 + A1 correction)

## What

Freeze and implement a development-calibration harness that asks whether the
certified historical row-layered GF32 FFT-QSPA decoder (`decode_row_layered_fftqspa`,
damping 1.0, cold start) exhibits a deterministic, finite, resource-bounded
region of correct behavior as prior ambiguity and graph size/loopy structure
increase from analytically tractable fixtures to a full-rank n=64
high-disclosure graph. No D7-B scientific execution in this task; stop at
independent Pre-EXECUTE readiness.

## Why

D7-A (`D7_A_DECODER_CERTIFICATION_PASS`) removed the foundational-correctness
blocker (1024/1024 products, check-SP to 3.3e-16, tree to 6.7e-16, per-sweep
recurrences, discriminating negative controls, log-domain `final_beliefs`,
correct D5 softmax/L1→L2 APP). The next mainline question is a clear,
reproducible operating region under progressively harder fully-synthetic
conditions. D7-B is that calibration; it is not a protocol benchmark.

## Scope

In scope: OpenSpec freeze, `D7_B_PREREG_R1.md`, `D7_B_EXECUTION_PACKET_R1.md`,
minimal deterministic harness (`v72p2d7_gf32_easy_regime.py`), focused tests
(`test_v72p2d7_gf32_easy_regime.py`), runner script
(`scripts/v72p2d7_gf32_easy_regime.py`), fake/unit qualification, independent
implementation review, independent Pre-EXECUTE review, scoped local commits.

Out of scope: D7-B scientific run, R1d, D7-C/D, formal G1/G2, Cascade, Model-F /
CAL / VAL / real / raw / formal / VOID content reads, `--phase`, production
v35/D5 edits, trace hooks, schedule/damping changes, graph search, flooding,
push.

## Decision question and claim ceiling

Question: does the certified decoder show a deterministic finite
resource-bounded region of correct behavior across the frozen 64-cell matrix?

May establish: existence/absence of a tested easy region; first failing tier;
failure mode (nonfinite/crash, syndrome-only, wrong fixed point, oscillation
proxy, iteration exhaustion); agreement with exact posterior/MAP on tractable
fixtures. May not establish: FER, leakage, efficiency, key rate,
qualification, CAL recoverability, R1d value, flooding superiority, G2
readiness, general NB-LDPC viability.

## R1/A1 binding

R1 packet `D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
binds fully except §3.3 item 2. A1 addendum
`D7_B_EASY_REGIME_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md` supersedes
only that item (row degrees [2,3,2] → [3,3,2], literal incidence/coeffs).
A1 takes precedence on conflict. Prior R1 STOP is recorded as a
packet-specification feasibility defect; it consumed zero authorization, zero
commits, zero decoder calls, zero roots, zero observations.
