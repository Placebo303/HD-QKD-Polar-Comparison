# D7-C result acceptance R1 — bidirectional-oracle invocation `94c0ea15-a786-4cb8-a991-6fec521cccae`

Scope: scoped acceptance documentation only. Zero decoder calls, zero reruns,
zero root edits, zero production-code edits. Main-thread adjudication (§0 of
`D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`) is
applied without reinterpretation.

## Baseline (verified before writing)

- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `b4ba2896`
  (`result(d7-c): record one reviewed bidirectional-oracle invocation`).
- Root `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae/`:
  exactly six files, zero subdirectories —
  `command_log.txt` (282 B), `decoder_records.csv` (23599 B),
  `manifest.json` (2709 B), `paired_summary.csv` (1130 B),
  `report.md` (362 B), `summary.json` (728 B).
  Read twice (task start/end); names/sizes/mtimes identical; nothing modified.
- Sole D7-C UUID `94c0ea15-a786-4cb8-a991-6fec521cccae`; the only
  `workspace/d7_c_bidirectional_oracle_*` root. No D7-D root or UUID.
- Lifecycle commits (local-only): authorize `b07b5441` → exactly one
  invocation → revoke `d3bd3c8b` → result `b4ba2896`.
- Review/verify tokens: independent Pre-RESULT
  `D7_C_PRE_RESULT_REVIEW_PASS_R1` (R01–R20, internal coherence only); sole
  read-only verifier output
  `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_C_BIDIRECTIONAL_DEPENDENCE'}`
  (exit 0).
- `cycle_state.yaml` (pre-acceptance): `d7c_execution_authorized: false`,
  attempts/completed `1/1`, `decoder_executed: true`, `result_created: true`,
  `scientific_promotion: false`,
  `next_gate: INDEPENDENT_D7_C_RESULT_ACCEPTANCE_R1`.
- R1d/G1/G2 absent, all authorization false; protected roots (`results`,
  `comparison_bench/outputs_comparison`) unchanged.

## Main-thread adjudication (§0, transcribed without reinterpretation)

Accept the immutable D7-C run and independent review as:

`D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`

Accepted scope:

- 128/128 frozen single-layer calls completed, finite and internally coherent;
- exact and syndrome agreed on all calls; 43/128 exact;
- f=1.0: L1 marginal/oracle `0/16 -> 10/16`; L2 `0/16 -> 1/16`;
- f=1.2: L1 `3/16 -> 16/16`; L2 `0/16 -> 13/16`;
- f=1.2 has `STRONG_ORACLE_LIFT` in both layers;
- run terminal `D7_C_BIDIRECTIONAL_DEPENDENCE` is accepted as a bounded
  mechanism-classification result;
- no crash/nonfinite/resource/watchdog issue; RSS known and below 2 GiB;
- D7-C did not consume cross-layer returned beliefs and is not affected by the
  deferred D7-B APP-interface implementation.

Scientific interpretation ceiling:

- accepted: true other-layer symbols materially improve recovery under the
  frozen priors, matrices, decoder, disclosures, n=64 and 16 paired blocks;
- not accepted: that an implementable alternating/joint decoder can generate
  that information, bootstrap from marginal priors, achieve FER, improve
  leakage/key rate, qualify the code, or generalize beyond this matrix;
- f=1.0 L2 remains effectively unrecovered even with oracle (1/16), showing
  disclosure/finite-length difficulty remains alongside cross-layer dependence.

The next mainline stage is D7-D: isolate schedule only. Do not implement
alternating/joint BP yet. Layer-interface provenance implementation remains
mandatory before any future cross-layer APP route.

## Paired 2×2 counts (as stored; recomputed, agree)

Each stratum is 16 seed-paired blocks; `oracle_only + marginal_only + both +
neither = 16`.

f=1.0 L1 — marginal `L1_MARGINAL` vs oracle `L1_ORACLE_U2`:

| marginal_exact | oracle_exact | oracle_only | marginal_only | both | neither |
|---|---|---|---|---|---|
| 0 | 10 | 10 | 0 | 0 | 6 |

f=1.0 L2 — marginal `L2_MARGINAL` vs oracle `L2_ORACLE_U1`:

| marginal_exact | oracle_exact | oracle_only | marginal_only | both | neither |
|---|---|---|---|---|---|
| 0 | 1 | 1 | 0 | 0 | 15 |

f=1.2 L1 — marginal `L1_MARGINAL` vs oracle `L1_ORACLE_U2`:

| marginal_exact | oracle_exact | oracle_only | marginal_only | both | neither |
|---|---|---|---|---|---|
| 3 | 16 | 13 | 0 | 3 | 0 |

f=1.2 L2 — marginal `L2_MARGINAL` vs oracle `L2_ORACLE_U1`:

| marginal_exact | oracle_exact | oracle_only | marginal_only | both | neither |
|---|---|---|---|---|---|
| 0 | 13 | 13 | 0 | 0 | 3 |

## Resource facts

- Outer harness wall `33.74325648800004` s; stored scientific wall
  `32.63112180600365` s (limit 1500 s); max per-call wall
  `0.43867251399933593` s (limit 120 s).
- RSS `105172992` B (`peak_rss_bytes`, known, finite, positive) below
  `2147483648` B.
- Process exit `0`; timeout-124 flag `false`; no crash/nonfinite/watchdog
  event (`crash_count` 0, `nonfinite_count` 0, `watchdog_timeouts` 0).
- Verifier: `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_C_BIDIRECTIONAL_DEPENDENCE'}`,
  exit 0; root six files unchanged after verify.

## Not authorized / not established

No alternating/joint decoder bootstrap, no FER, leakage, key-rate, CAL,
qualification or scientific-promotion claim follows from this acceptance.
D7-D is not executed and no D7-D root/UUID exists; interface implementation
remains deferred and mandatory before any cross-layer APP route; R1d, G1 and
G2 remain unauthorized; no push.

Next gate: `D7_D_SCHEDULE_DISCRIMINATOR_PACKET_FREEZE` (D7-D isolates schedule
only; do not implement alternating/joint BP).
