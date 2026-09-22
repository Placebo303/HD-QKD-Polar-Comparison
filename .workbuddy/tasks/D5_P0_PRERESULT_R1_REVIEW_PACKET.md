# TASK PACKET — D5-P0-PRERESULT-R1: independent Pre-RESULT review of the P0 run

Target executor: an **independent** reviewer session. You did not run P0, write
the P0 packet, or execute any earlier D5 task packet. Re-derive from the
artifacts; do not accept any prior claim on faith, including §3 below.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD `b4696273`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Under review: `workspace/v72p2d5_p0_cost/20260906_r1/` (4 files) and
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_OPERATOR_RETURN_R2.md`,
  `P0_AUTHORIZATION_RECORD_R2.md`, `P0_EXECUTION_PACKET_ADDENDUM_A1.md`
- Governing frozen packet: `.../P0_EXECUTION_PACKET.md` (must be byte-identical)
- Role: read-only review. Authorization: **false**.
- Deliverable: exactly ONE new file (§7). No commit. No push.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run P0, G1, or G2. **The P0 authorization is consumed.** Re-running the
   phase is forbidden regardless of what you find.
2. Run any decoder. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
3. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
4. Modify, delete, move, rename, overwrite, normalize, or hash anything under
   `workspace/`. **The P0 output root is evidence — read-only.** A pytest
   `--basetemp` directory of your own is the only thing you may create there.
5. Let `workspace/v72p2d5_g2/20260906_r1` come into existence.
6. Change any `cycle_state.yaml` value, authorize anything, accept anything,
   or promote anything.
7. Edit any `.py`, any existing `.md`, or any OpenSpec file.
8. `git add`, `git commit`, `git push`, `git reset`, `git stash`,
   `git checkout`, `git clean`, `git rebase`, `git revert`,
   `git add --renormalize`.
9. Fix anything. You report; you do not repair.

Record anything you cannot check as `NOT_VERIFIABLE` with the reason.

---

## 1. What is being decided

One authorized P0 cost-preflight invocation completed on the frozen command and
wrote four files. Decide: **is this result fit to be accepted as the P0
outcome, and does it support proceeding to a G1 packet?**

P0 is a cost preflight. It establishes no correctness, no rate-point
performance, no FER, no leakage, no key rate. A PASS here means the cost was
measured and honestly recorded — nothing more.

## 2. Verify lifecycle and provenance

- The frozen `P0_EXECUTION_PACKET.md` is byte-identical to its state at
  `b27f31da`.
- Across `f1cdf970` and `b4696273`, the net change to `cycle_state.yaml` is
  zero, and the only key touched was `p0_cost_execution_authorized`
  (`false` → `true` → `false`).
- All nine `*_execution_authorized` are `false` now; `next_gate` is unchanged;
  `scientific_promotion` is `false`.
- Exactly one invocation occurred; no rerun, no second root, no partial
  leftovers.
- The authorization record carries the user's verbatim authorization, the
  frozen command, the watchdog command, and the STEP 2' reachability output.
- No `workspace/` artifact other than the P0 root was created or modified;
  Model-F, G0, G0-recovery, G1 and structure roots are unchanged.

## 3. Verify the result against the frozen contract

Recompute from `results.json`; do not copy the operator's numbers.

- Output root contains exactly `results.json`, `table.csv`, `report.md`,
  `execution_summary.json`, and nothing else.
- `phase`, `block_length`, `f_list`, `seeds`, `frozen_rows` match the frozen
  packet: width 64; `f` `{1.0, 1.2}`; seeds `2026090510`, `2026090511`;
  `m1` `{49, 59}`; `m2` `{43, 52}`.
- `decoder_calls` equals the frozen 12, and is consistent with the record
  structure.
- The four records cover `f` × `kind` exactly once each.
- `projected_g1_s` and `projected_g2_s` are reproducible from the recorded
  wall times and the frozen call counts, using the formula in the source.
- `projection_blocked` follows the `> 3600 s` rule.
- Whether the four files agree with each other (`table.csv`, `report.md`,
  `execution_summary.json` vs `results.json`).
- Whether any forbidden content leaked into the outputs: raw rows, matrices,
  priors, beliefs, syndromes, absolute paths, checksums.

## 4. Assess three findings raised by the packet author

These were observed read-only by the author. **Verify each independently and
decide its significance yourself; do not adopt the author's framing.**

- **F1 — `rss_bytes` is `null` in all four records.** The frozen packet lists
  RSS among the recorded quantities and sets a 2 GiB reference; the operator
  could not compare. Determine why it is null, whether the frozen contract is
  therefore unmet, and whether that is a blocking defect for accepting P0, a
  recorded limitation, or immaterial to a wall-time preflight.

- **F2 — `projected_g2_s` may be structurally unsound.** The projection is
  `per_call × call_count`, with `per_call` derived from `n=64` blocks, while G2
  runs `n=256` with roughly four times the rows. Determine whether the
  projection scales with block width or row count at all. If it does not, state
  what `projected_g2_s` and `projection_blocked: false` actually license, and
  whether `projected_g1_s` (same width as P0) stands on firmer ground. Say
  explicitly whether the G2 projection may be relied upon for any decision.

- **F3 — every decode appears to have run to the iteration cap.** The app
  records show 360 iterations and the oracle records 180, against
  `MAX_ITER = 90`. Work out how many decode calls each record aggregates and
  whether the per-call iteration count is exactly the cap. If it is, state what
  that does and does not imply — P0 records no exactness, so this is not a
  failure result — and whether it is a cost signal that a G1 packet must take
  into account.

## 5. Assess claim discipline

Read `P0_OPERATOR_RETURN_R2.md` and judge whether it stays within P0's
boundary: does it record without interpreting; does it avoid FER, leakage, key
rate, method verdicts and G1/G2 readiness claims; is its `NOT_INTERPRETED`
section honest; does anything in it overstate what a cost preflight can show?

## 6. Static and test evidence

- `py_compile` on the two core modules and the two scripts.
- Run the three focused test files with a fresh `--basetemp` under
  `workspace/`. Report the literal summary line and every failing test id.
  Known and non-blocking: `test_T1_22_openspec_history_zero_mod` fails because
  the worktree carries line-ending-only differences (zero content change).
  **Any other failure is a finding.**
- Re-stat the protected roots afterwards and confirm nothing changed.

## 7. Deliverable

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_PRE_RESULT_REVIEW_R1.md`

Numbered checks with `PASS` / `FAIL` / `NOT_VERIFIABLE`; recomputed values
inline; the F1/F2/F3 assessments with your own reasoning; a pre/post stat
snapshot; an explicit statement of what you did and did not execute; and a
closing verdict.

Verdict, exactly one of:

- `P0_PRE_RESULT_REVIEW_PASS` — the P0 result is fit for acceptance. State any
  conditions and any limitation that must be carried forward into the G1
  packet. State plainly that this is not an acceptance, not a G1
  authorization, and not a scientific qualification.
- `P0_PRE_RESULT_REVIEW_FAIL` — name the blocking finding and the single
  decision required from the main thread.

State the strongest claim the evidence supports, and list what is explicitly
not claimed: no FER, no leakage, no key rate, no qualification, no method
verdict, no prediction about G1 or G2 outcomes.

## 8. Report back

In your message: the verdict, a brief per-check table, your F1/F2/F3
conclusions in one or two lines each, the recomputed projections, the literal
pytest line, and this line if it is still true:

「P0 结果仅为记录，未接受；G1 未授权；next_gate 仍为 P0_PACKET_REVIEW。」
