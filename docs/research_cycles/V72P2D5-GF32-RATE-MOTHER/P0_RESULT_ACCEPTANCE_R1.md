# P0 Result Acceptance R1 — V72P2D5-GF32-RATE-MOTHER

## A01 Status

`P0_RESULT_ACCEPTED`, scope `COST_MEASUREMENT_ONLY`.

P0 is accepted as a cost measurement only. No correctness, rate, or
qualification claim is made.

## A02 Pre-state

- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `860ebbff`, `ahead 11` of `origin/formal-ir-v72p1-addendum-clean`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate at packet start `next_gate: P0_PACKET_REVIEW`
- Cycle dir untracked at packet start (exactly 4, nothing else):
  - `GUARD_REWORK_REVIEW_R1.md`
  - `LOADER_FIX_REVIEW_R1.md`
  - `P0_PRE_EXECUTE_REVIEW_R1.md`
  - `P0_PRE_RESULT_REVIEW_R1.md`
- Formal roots at packet start:
  - `workspace/v72p2d5_p0_cost/20260906_r1` — exists, 4 files
    (`execution_summary.json`, `report.md`, `results.json`, `table.csv`)
  - `workspace/v72p2d5_g1/20260906_r1` — exists, 4 files
    (`execution_summary.json`, `report.md`, `results.json`, `table.csv`)
  - `workspace/v72p2d5_g2/20260906_r1` — ABSENT
  - `workspace/v72p2d5_g0/20260905_r2` — exists, 4 files
    (`execution_summary.json`, `report.md`, `results.json`, `table.csv`)
  - `workspace/v72p2d5_g0_recovery/20260906_r1` — exists, 4 files
    (`execution_summary.json`, `report.md`, `results.json`, `table.csv`)
  - `workspace/v72p2d5_model_f_input/20260907_r1` — exists, 2 files
    (`model_f_input.npz`, `model_f_input_summary.json`)
- Authorization pre-state: all nine `*_execution_authorized` are `false`;
  `scientific_promotion: false`.

## A03 What was measured

What P0 measured (verbatim from
`workspace/v72p2d5_p0_cost/20260906_r1/results.json`):

| item | value |
| --- | --- |
| phase | `p0-cost` |
| block_length | 64 |
| f_list | 1.0, 1.2 |
| frozen_rows | f=1.0 → m1 49 / m2 43; f=1.2 → m1 59 / m2 52 |
| seeds | 2026090510, 2026090511 |
| decoder_calls | 12 |
| records (f / kind / wall_s / iterations / rss_bytes) | 1.0 app 1.8862763999495655 / 360 / null · 1.0 oracle 1.04731999989599 / 180 / null · 1.2 app 3.459295800072141 / 360 / null · 1.2 oracle 1.671841400093399 / 180 / null |
| projected_g1_s | 161.8241519993171 |
| projected_g2_s | 485.47245599795133 |
| projection_blocked | false |
| passed | true |
| run wall (operator) | 8.6278899 s, exit 0, stdout and stderr empty |
| decode-attributed total | 8.064733600011096 s against the 1440 s cap → no `RESOURCE_OVERRUN` |

## A04 What is not established

What P0 does NOT establish. Transcribe this list verbatim; it is the point
of the whole document:

- No correctness result. P0 records cost only; it grades nothing.
- No `exact_failure_fraction`, no FER, no leakage, no key rate, no net rate.
- No qualification of NB-LDPC, the dv3 mother, the rate points, or Model-F.
- No statement that G1 or G2 will pass, complete, or fit their budgets.
- No authorization for anything.

## A05 Carried limitations

Carried limitations. All of these must appear in the accepted record and be
carried into the G1 packet:

- `L1 (depth)` — `_snapshot_dir` sees top-level files only; nested writes under a formal root are invisible to the guards. Before G1/G2 produce output the G1 packet must either make the snapshot recursive or add an explicit no-subdirectory invariant, and must state which it takes. — `MUST_CARRY_INTO_G1_PACKET`
- `L2 (T1_23 narrowness)` — the recurrence guard catches only `assert not … .exists()` with a root or literal token in the same assert; `os.path.exists`, `is_dir`/`is_file`, alternate operators, indirect variables, and non-assert enforcement bypass it. Do not cite it as a general absence-assertion ban; the primary protection is the per-test invariance assert. — `MUST_CARRY_INTO_G1_PACKET`
- `L3 (T1_22 live-fire)` — red-on-content-change is established by reading the parser logic, not by a live mutation demonstration. If the G1 packet relies on T1_22 as a freeze proof, cite the logic, not a live red run. — `MUST_CARRY_INTO_G1_PACKET`
- `L4 (record correction)` — the guard-rework report's `STATUS=63` figure is superseded by the measured 1969 porcelain lines / 1887 modified paths / `numstat` content changes 0. No correctness impact; corrected here so future reviewers do not chase a phantom clean tree. — `MUST_CARRY_INTO_G1_PACKET`
- `L-RSS` — Windows has no `resource` module, so `rss_bytes` is `null` in every P0 record. The 2 GiB reference could not be checked. G1 must rebuild an RSS measurement or explicitly drop the RSS budget with reasons. — `MUST_CARRY_INTO_G1_PACKET`
- `L-SCALE` — the G1/G2 projections are `per_call × {240, 720}` with no width or row-count scaling. G2 runs at width 256 with roughly four times the rows, so `projected_g2_s` and `projection_blocked: false` carry **no** permission for G2. `projected_g1_s` is a same-width call-count indication only. — `MUST_CARRY_INTO_G1_PACKET`
- `L-ITER` — every one of the 12 decodes ran the full `MAX_ITER = 90` (app 360 = 2 seeds × 2 layers × 90; oracle 180 = 2 seeds × 1 × 90). Nothing converged early. P0 checks no correctness, so this is not a failure, but the cost signal is a saturated upper bound. G1 must budget at the cap and must record exact/syndrome outcomes so "ran to cap" and "failed to converge" can be told apart. — `MUST_CARRY_INTO_G1_PACKET`

## A06 Review chain

Review chain to record (all four now landed by this packet):

- `P0_PRE_EXECUTE_REVIEW_R1.md` — `PRE_EXECUTE_REVIEW_PASS`, five open questions decided.
- `LOADER_FIX_REVIEW_R1.md` — `LOADER_FIX_REVIEW_PASS`; the Model-F consumer path fix (`299416ae`) after the first P0 authorization was consumed with no run.
- `P0_PRE_RESULT_REVIEW_R1.md` — `P0_PRE_RESULT_REVIEW_PASS` with limitations.
- `GUARD_REWORK_REVIEW_R1.md` — `GUARD_REWORK_REVIEW_PASS` with L1–L4.

## A07 Authorization history

Authorization history to record: two P0 authorizations were issued. The
first (2026-09-07, `a71188fb`/`3ecaebb6`) was consumed with no run — the phase
refused in 0.376 s on a false missing-input message caused by the consumer path
defect. The second (`f1cdf970`/`b4696273`) produced this result. Both are
consumed; neither is reusable.

## A08 Lifecycle effect

- All nine authorizations stay `false`.
- `scientific_promotion` stays `false`.
- `next_gate` moves `P0_PACKET_REVIEW → G1_PACKET_REVIEW`.
- Acceptance of a cost measurement is not scientific promotion and grants no G1
  authorization.

## A09 Next step

Next step — freeze the G1 execution packet carrying every A05 limitation,
then an independent Pre-EXECUTE review, then a separate explicit G1
authorization. These may not be merged or reordered. G1 is neither frozen nor
authorized by this packet.
