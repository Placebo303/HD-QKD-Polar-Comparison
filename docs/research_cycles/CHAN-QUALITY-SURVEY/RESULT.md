# CHAN-QUALITY-SURVEY — RESULT (DECIDE, operator record)

- **Track**: **DECIDE** (real-data channel characterization; `AGENTS.md` §1.2 matrix).
- **Branch**: `formal-ir-v72p1-addendum-clean`; execution HEAD `23183c73fd4b1597f2c42a6e9b06fa2de4402b9c` (per both arm logs' Pre-EXECUTE).
- **What this batch is**: a real-data **channel characterization with zero correction measured**. Both arms ran **zero decoders**. No FER, efficiency, leakage, f, SKR, method comparison, or "works anywhere" claim exists in this batch.
- **Review status**: the independent batch-end review (`INDEPENDENT_ACCEPTANCE.md`, packet §13 CQ-01…CQ-11) is **still outstanding**. Nothing in this record is promoted until that review passes.
- **Machine authority**: Arm A root `workspace/cq_15d6f160/` (`CQ-20a.json`, `CQ-20b.json`, `CQ-20c.json`, `CQ-20d.json`, `CQ-12_NON_EXECUTION.json`, `CQ-13a_NON_EXECUTION.json`, `CQ-13b_NON_EXECUTION.json`, `ARM_A_SUMMARY.md`, `EXECUTION_LOG.md`); Arm B root `workspace/cq_4af91a87/` (`ArmB/CQ-J21a/CQ-J21b/CQ-J21c.json` under per-source subroots, `ArmB/ARM_B_SUMMARY.md`, `EXECUTION_LOG.md`). Every number below is transcribed from those files.

## 1. Frozen scope actually executed

Arm A executed exactly the four 1.20-Type0 groups (`500K` CQ-20a, `1M` CQ-20b, `1_5M` CQ-20c, `2M` CQ-20d) at `dimension=1024`, `bin_width_ps=200`, `frame_bins=1024` (IMPOSED-CONVENTION), with the header-validated `1↔5` pair and the pairing offset derived per group by correlation auto-alignment under the frozen A1/R1 chain. No grid scan. CQ-12 (excluded), CQ-13a/b (deferred) were retained as non-execution records with zero data contact.

Arm B executed the three Jan-21 Type2 sources (CQ-J21a `1M`, CQ-J21b `1p5M`, CQ-J21c `2M`) over the M0 VAL+HOLD eval region with the frozen pairing and geometry reused verbatim (equality-asserted against R1: offsets, pair counts, 60/20/20 boundaries, eval superframe counts).

## 2. Arm A results

### 2.1 Terminal status

| gid | group | status | peak_to_bg (gate 100) |
|---|---|---|---|
| CQ-20a | 500K | OK | 224.76 pass |
| CQ-20b | 1M | OK | 123.09 pass |
| CQ-20c | 1_5M | REFUSED-alignment | 85.01 BLOCKED |
| CQ-20d | 2M | REFUSED-alignment | 58.73 BLOCKED |

REFUSE reason string (both groups): `REFUSED-REFUSED: CQ-20c/d: alignment blocked_low_peak_to_bg: STOP-BLOCKED: alignment has not passed acceptance; pairing/histogram/entropy must not run (no fallback permitted).` (gid substituted per group). Argmax bin was 8191 (−50 ps) for all four groups, but the −50 value was NOT adopted for CQ-20c/d (never borrowed); no pairing/framing/metrics ran there. **Both REFUSEs are terminal under this packet; a rerun would require a new packet.**

### 2.2 OK groups

CQ-20a (500K): derived offset **−50 ps** (bin 8191); total/clean pairs **37079 / 37072** (remainder 7, frames 37037); `ser` **0.24239318**; ±1 mass `0: 0.75760682, +1: 0.23939901, −1: 0.00299417` (asymmetry +0.236405); `|signed|` quantiles q50/90/95/99/100 = 0/1/1/1/1; Gray popcount `{0: 0.75760682, 1: 0.24239318, 2..10: 0.0}`; plane rates LSB→MSB `[0.11965904, 0.06193353, 0.03137139, 0.01448533, 0.00736405, 0.00366854, 0.00199612, 0.00107898, 0.00051252, 0.00032369]` (monotone); 6-block SER 0.23535125–0.24550898 (stable); H(U1|B)=0.02402211, H(U2|U1B)=0.76687736, H(A|B)=0.79089947 (plug-in, support 2151); wall 34.85 s, peak RSS 0.23 GiB.

CQ-20b (1M): derived offset **−50 ps** (bin 8191); total/clean pairs **65012 / 64994** (remainder 18, frames 64917); `ser` **0.24609964**; ±1 mass `0: 0.75390036, +1: 0.24086839, −1: 0.00523125` (asymmetry +0.235637); quantiles 0/1/1/1/1; Gray popcount `{0: 0.75390036, 1: 0.24609964, 2..10: 0.0}`; plane rates LSB→MSB `[0.12447303, 0.05997477, 0.03140290, 0.01550912, 0.00740068, 0.00390805, 0.00193864, 0.00090778, 0.00040004, 0.00018463]` (monotone); 6-block SER 0.24351519–0.24852290 (stable); H(U1|B)=0.02439743, H(U2|U1B)=0.79518146, H(A|B)=0.81957888 (support 2345); wall 85.32 s, peak RSS 0.34 GiB.

Both OK groups: `expected_planes_flipped_per_error` = 1.0 both routes (diag route 0.9999999999999999, popcount route 1.0).

### 2.3 The central negative

The legacy expectation did **not** reproduce. The legacy-`v1` value is `ser = 0.098260` at the frozen geometry (`dimension=1024`, `bin_width_ps=200`) for the 1M group, measured under the legacy-`v1` pairing rule and an older pipeline. The frozen-chain measurement of that **same** 1M group (CQ-20b) is `ser = 0.246100`; the other OK group (CQ-20a) measures `ser = 0.242393`. **Both land inside Jan-21's 23.9–25.4% band. The legacy value did not reproduce under the frozen chain; the documented differences are the pairing rule and the pipeline; cause beyond that is not established. The Coincidences window is explicitly not among them: the loader consumes the raw event stream and pairs at 200 ps itself (`m0_realframe_runner.py:86` `COIN_WINDOW_PS = 200`; pairing call `:154`).** This was the falsifiable expectation the packet set (F-q), and the answer is no — a legitimate, informative outcome per the packet.

Reuse note: the alignment step was reusable from the frozen chain with no existing file modified; the only addition was a small read-only header validator in the new additive runner.

## 3. Arm B results

Command identity (all three sources): `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=<repo-root> /usr/bin/time -v timeout 600 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.cq_channel_survey_armB --source {1M|1p5M|2M} --root workspace/cq_4af91a87/ArmB/CQ-J21{a|b|c} --execute-real --execution-authorized`, one process per source, sequential. Exit code 0 on all three.

CQ-J21a (1M): wall outer 77.9 s / runner-internal 77.0 s (`wall_s` 76.98254512); peak RSS 368544 kB = 0.35 GiB; superframes **205**, remainder **407** symbols dropped; provenance offset −50 (= R1), n_pairs_total 525831 (= R1), n_pairs_eval 210327; `ser` **0.23856707**; ±1 mass `0: 0.76143293, +1: 0.23716654, −1: 0.00140053` (+1-dominant, asymmetry +0.23576601); Gray popcount `{0: 0.76143293, 1: 0.23856707, 2..10: 0.0}`; plane-rate diagonal LSB→MSB `[0.11992188, 0.05989425, 0.02939691, 0.01467226, 0.00744093, 0.00359184, 0.00201982, 0.00092416, 0.00050495, 0.00020008]`, off-diagonals all 0.0; 6-block SER 0.2366–0.2402; H(U1|B)=0.02415075, H(U2|U1B)=0.77422846, H(A|B)=0.79837921 (support 2304); `expected_planes_flipped_per_error` 1.0 / 1.0, derivation: Σ plane_rates = 0.2385670732 = ser ⇒ 1.0.

CQ-J21b (1p5M): wall runner-internal 200.0 s (`wall_s` 200.00797474; outer `/usr/bin/time` output lost, see §6); peak RSS 0.476 GiB; superframes **287**, remainder **405**; offset +50 (= R1), n_pairs_total 735780 (= R1), n_pairs_eval 294293; `ser` **0.25433839**; ±1 mass `0: 0.74566161, +1: 0.00112628, −1: 0.25321211` (−1-dominant, asymmetry −0.25208583); Gray popcount `{0: 0.74566161, 1: 0.25433839, 2..10: 0.0}`; plane diagonal LSB→MSB `[0.12776636, 0.06330303, 0.03196116, 0.01593804, 0.00799965, 0.00392326, 0.00186125, 0.00083365, 0.00051380, 0.00023819]`, off-diagonals all 0.0; 6-block SER 0.2509–0.2564; H(U1|B)=0.02422924, H(U2|U1B)=0.79928241, H(A|B)=0.82351165 (support 2326); `expected_planes_flipped_per_error` 1.0 / 1.0, derivation: Σ plane_rates = 0.2543383874 = ser ⇒ 1.0.

CQ-J21c (2M): wall outer 187.6 s / runner-internal 186.5 s (`wall_s` 186.50523331); peak RSS 645204 kB = 0.62 GiB; superframes **383**, remainder **529**; offset +50 (= R1), n_pairs_total 982182 (= R1), n_pairs_eval 392721; `ser` **0.25375836**; ±1 mass `0: 0.74624164, +1: 0.00143807, −1: 0.25232029` (−1-dominant, asymmetry −0.25088222); Gray popcount `{0: 0.74624164, 1: 0.25375836, 2..10: 0.0}`; plane diagonal LSB→MSB `[0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055, 0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438]`, off-diagonals all 0.0; 6-block SER 0.2499–0.2560; H(U1|B)=0.02491156, H(U2|U1B)=0.80076697, H(A|B)=0.82567853 (support 2468); `expected_planes_flipped_per_error` 1.0 / 1.0, derivation: diag-sum 0.25375836325065276 = ser ⇒ 1.0, co-matrix max off-diagonal 0.0 exactly.

Observed ±1 direction asymmetry: +1-dominant on CQ-J21a (offset −50), −1-dominant on CQ-J21b/c (offset +50) — **its sign follows the per-source offset sign**.

## 4. Combined finding (headline)

Across the **five captures actually measured** (three Jan-21 sources plus the two Arm A groups that reached OK):

- `ser` spans **0.23856707–0.25433839** (≈ 0.24–0.25).
- `expected_planes_flipped_per_error` equals **1.0 in every case** (both routes; Arm A diag route 0.9999999999999999, i.e. 1.0 to float precision).
- The co-error off-diagonals are **exactly zero** in every case.
- The Gray popcount mass lies **only on {0, 1} and never on 2 or more** in every case.
- The monotone MSB→LSB ladder holds in every case, with LSB share of SER: CQ-J21a 50.27%, CQ-J21c 50.09%, CQ-J21b 50.24%, CQ-20a 49.37%, CQ-20b 50.58% — against the earlier 10 dB reference of 48.7% at SER 0.077 (packet F-g).

Consequence, stated as a **channel-structure finding, not a method result**: the plane components of this channel show zero observed cross-plane co-error with single-plane-flip structure — co-error off-diagonals exactly zero, Gray popcount mass confined to {0, 1}, `expected_planes_flipped_per_error` 1.0 — with the detection-floor caveat that about a million pairs with zero double-plane errors exclude only multi-plane rates above roughly 1e-6, so rare doubles below the detection floor are not excluded. **A GF(32) nonbinary code is therefore modeling structure the channel does not have, and a per-plane rate-adaptive binary treatment is the structurally indicated one.** The plane rates span roughly three orders of magnitude (e.g. ≈674× on CQ-20b, ≈370× on CQ-20a), with the LSB plane carrying about half of all errors — so a uniform per-plane rate is not viable.

**This does not establish that any method corrects well at any signal error rate.** It is a channel characterization with zero correction measured. Arm A and Arm B both ran zero decoders.

## 5. Negatives

- **No measured easier operating point among the five captures; the unmeasured groups supply no evidence of one on recorded grounds.** The five measured captures all sit at `ser` ≈ 0.24–0.25. The unused groups do not provide one: the four Type0 groups measure the same band (the two that reached OK; the two REFUSEs yielded no frozen-chain SER); the two SHG groups were declared out of scope (never assessed in this repository, and the stated `cw` pump implies a multi-pair higher-noise regime); the 1.12 group remains excluded on its recorded grounds (measured-wrong 3 s tag, 29.9999524 s span quarantine). The "easier data first" strategy therefore has no purchase in this data — which the packet already anticipated as a legitimate outcome (§1).
- The two Type0 groups that REFUSED (CQ-20c, CQ-20d) produced **no frozen-chain symbol error rate**.
- No method was decoded, so **no correction, frame-error, efficiency, leakage or key figure exists from this batch**.

## 6. Process deviations

- Arm B loaded `nonbinary_v25_gate` as an **isolated single file by path rather than as a package**, because a normal package import executes `formal_ir/__init__.py`, which pulls in correction machinery and would trip the packet's own zero-decoder gate. Functions were used verbatim with no copies. Deviation in mechanism, no deviation in the numbers.
- Arm B's outer resource-capture (`/usr/bin/time -v`) output for CQ-J21b was **lost to a tool-side wait timeout**; the runner's internal wall (200.0 s) and peak-RSS (0.476 GiB) record was retained instead and no rerun was performed, per the no-rerun rule.
- Arm A's first header validator assumed the channel-plan keys were at the **top level** of the configuration, but they live under **`measurements`**. The validator was corrected (additive runner only, no frozen file touched), and the fail-closed behaviour worked as intended: a retained REFUSE (superseded attempt-1 record, deleted from the fresh root with the event retained in the log) rather than a misread.

## 7. Claim ceiling (packet §11, verbatim — binds this record, the review, and any citation)

> These are channel characterization measurements only. This batch establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO method comparison; NO selection of a "best" group as a favourable subset; and NO claim that any method works anywhere. Arm A measures channel characterization only, with zero correction. A lower symbol error rate does not imply that any method corrects. The legacy `0.098260` value is an expectation under a different pipeline and pairing rule (F-q, F-n), never a result, and must not be carried forward as one. No Type0 group may be presented as representative of the experiment's operating conditions. Any later "works on easier data" claim requires its own packet and must report the quality axis alongside, never the favourable subset alone. The Arm A quality axis exists precisely so that a later favourable-subset claim cannot be circular: no group may be promoted on these numbers without a new packet, a new authorization, and an uncertainty statement the present batch does not provide.

Arm-A-specific prohibitions restated: no Type0 group may be presented as representative of the experiment's operating conditions; a lower symbol error rate may not be inferred to imply that any method corrects; `0.098260` may never be carried forward as a result. Any later "works on easier data" claim requires its own packet and must report the quality axis alongside, never a favourable subset alone.
