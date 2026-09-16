# TASK PACKET — D5-P0-PREEXECUTE-R1: independent Pre-EXECUTE review of the P0 packet

Target executor: an **independent** reviewer session. You did not write the P0
execution packet, the Model-F implementation, or any prior D5 task packet. Do
not accept any prior verdict on faith; re-derive from the source.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD `b27f31da`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Under review:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_EXECUTION_PACKET.md`
- Role: read-only review. Authorization in this task: **false**.
- Deliverable: exactly ONE new file (§7). No commit. No push.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run any decoder.
2. Execute P0, G1, or G2. The only `--phase` invocation permitted is the single
   guarded refusal check in §5, and only under the guards stated there.
3. Run `scripts/v72p2d5_prepare_model_f_input.py` at all. Its authorization was
   consumed on 2026-09-07; replay is forbidden.
4. Read CAL / VAL / raw parquet rows. `pandas.read_parquet` is forbidden.
   pyarrow **metadata** is allowed.
5. Create, delete, move, rename, copy, normalize, hash, or open-for-write
   anything under `workspace/`, except a pytest `--basetemp` directory you
   create for §6. `stat`, `json.load`, and
   `numpy.load(allow_pickle=False)` are allowed.
6. Let `workspace/v72p2d5_p0_cost/20260906_r1` or
   `workspace/v72p2d5_g2/20260906_r1` come into existence. If either appears at
   any point, STOP immediately and report.
7. Change ANY `*_execution_authorized`, `next_gate`, or any other
   `cycle_state.yaml` value. **Authorizing P0 is not yours to do.**
8. Edit any `.py`, any existing `.md`, any OpenSpec file, `docs/decision-log.md`,
   or `AGENT_PROJECT_MEMORY.md`.
9. `git add`, `git commit`, `git push`, `git reset`, `git stash`,
   `git checkout --`, `git clean`, `git rebase`, `git revert`.
10. Write `RESULT_SUMMARY.md`, `OPERATOR_RETURN.md`, or any `run_01`.
11. Fix anything you find. You report; you do not repair.

If you cannot complete a check, record it as `NOT_VERIFIABLE` with the reason.
Do not guess and do not silently substitute a weaker check.

---

## 1. What is being decided

`P0_EXECUTION_PACKET.md` freezes an intended P0 cost-preflight run. It has not
been reviewed and P0 is not authorized. Your review is the last gate before an
authorization act that the user alone may perform.

You must decide two things:

- **Is the frozen packet faithful to the source and to the accepted plan?**
- **What is the answer to each of its five open questions?**

A PASS from you does not authorize P0. It states that the packet is fit to be
authorized, and records the decisions the run must then obey.

## 2. Verify the frozen parameters against the source

For every row of the packet's P03 parameter table, verify it against the actual
code. Do not copy the packet's own numbers as evidence for themselves.

Source of truth:
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
(constants near lines 45–84; `run_p0_cost_phase` near 1948;
`run_p0_cost_synthetic` near 2416; `is_phase_authorized` near 115),
`scripts/v72p2d5_gf32_rate_mother.py`, and
`openspec/changes/v72p2d5-p0-g1-g2-production-path/design.md` §1–§5.

Check at minimum: block width; the `f` set; `m1`/`m2` prefix values and that
they follow `ceil(n*CE*f/5)` with the stated `CE_L1_MEAN` and
`CE_L2_ORACLE_MEAN`; builder `k_min`; graph seeds; block seeds; the decoder-call
arithmetic; decoder configuration; the prior source and `LAMBDA_STAR`; the
output root, file set and no-overwrite behaviour; the projection formulas and
the `projection_blocked` threshold; the single-call budget; the metric naming.

Report each as `AGREE` / `DISAGREE` / `NOT_VERIFIABLE`, with the source
location for each. Any `DISAGREE` on a scientific input is a blocking finding.

## 3. Verify the defect fix that P0 depends on

The whole reason this change exists is that `_run_rate_scan` and
`run_p0_cost_phase` previously decoded every `f` with the same full matrices.
Verify **in the code** that each `f` now decodes with its own
`H1_mother[:m1(f)]` / `H2_mother[:m2(f)]`, sliced from the same mother before
any decode call, in construction order, with no row reordering.

Also verify the L1-then-L2 order, that L2 is attempted even when L1 fails, and
that the oracle path is diagnostic only and never gates a verdict.

## 4. Verify the authorization chain

- Confirm `is_phase_authorized` is the single choke point and that `p0-cost`
  maps to `p0_cost_execution_authorized`.
- Confirm the CLI refuses with exit 3 before any construction, loader import,
  decode, or write while that key is `false`.
- Confirm `run_p0_cost_synthetic` refuses on `authorized=False`, and state
  exactly what it does on `authorized=True` with no injected arguments —
  including which decoder it binds and which root it writes to. This is
  residual risk `R-R1`; judge whether the packet describes it honestly.
- Read the current `cycle_state.yaml` and confirm all nine authorizations are
  `false` and `next_gate` is `P0_PACKET_REVIEW`.

## 5. Guarded refusal check (optional, once, or skip)

You may verify the refusal empirically, at most once:

1. Stat the P0 and G2 roots; both must be absent.
2. Confirm in `cycle_state.yaml` that `p0_cost_execution_authorized: false`.
3. Run `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`.
   It must print a refusal and exit 3.
4. Immediately re-stat both roots; both must still be absent.

If step 2 does not hold, do NOT run step 3. If step 4 shows either root
appeared, STOP and report a critical finding. You may skip this check entirely
and mark it `NOT_ATTEMPTED`; skipping is not a failure.

## 6. Static and test evidence

- `py_compile` on
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`,
  `scripts/v72p2d5_gf32_rate_mother.py`,
  `scripts/v72p2d5_prepare_model_f_input.py`.
- Run, with a fresh basetemp under `workspace/` (e.g.
  `workspace/v72p2d5_p0_preexec_r1_<tag>`):
  `comparison_bench/tests/test_v72p2d5_model_f_input.py`,
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`,
  `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`.
  Report the literal summary line and every failing test id. Reference value
  for orientation only, not a pass condition: `195 passed`.
- Re-stat the protected roots afterwards; confirm nothing changed and that P0
  and G2 are still absent.

## 7. Decide the five open questions

The packet's P07 carries `OQ-P0-1` .. `OQ-P0-5` unanswered. For each, return
either:

- `DECIDED` — state the decision, the reasoning, and exactly what the run and
  its operator must do differently as a result; or
- `REVISE_REQUIRED` — state what is missing and what must change in the packet.

You are deciding these, not deferring them. Guidance on what each must settle:

- `OQ-P0-1` total wall cap: a concrete number or an explicit "no cap, record
  the overrun", plus whether breach aborts or is merely recorded.
- `OQ-P0-2` watchdog: a concrete outer guard the operator can actually apply,
  or an explicit finding that none is required and why.
- `OQ-P0-3` `projection_blocked`: whether P0 still passes when
  `projected_g2_s > 3600`, and precisely which downstream stage it blocks.
- `OQ-P0-4` pre-authorization isolation evidence: name the exact checks that
  must be produced immediately before authorization, given `R-R1`.
- `OQ-P0-5` failure disposition: what happens to a partial output root and to
  the consumed authorization on crash, hang, or non-finite output.

If you judge that deciding one of these requires information you cannot obtain
read-only, return `REVISE_REQUIRED` for it and say what is needed.

## 8. Deliverable

Create exactly one file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_PRE_EXECUTE_REVIEW_R1.md`

Include: numbered checks with `PASS` / `FAIL` / `NOT_VERIFIABLE`; the P03
parameter verification table with per-row `AGREE`/`DISAGREE` and source
locations; the defect-fix finding; the authorization-chain finding; the
refusal-check result or `NOT_ATTEMPTED`; compile and test evidence; a pre/post
stat snapshot of the protected roots; the five open-question decisions; an
explicit statement of what you did and did not execute; and a closing verdict
block.

Your verdict must be exactly one of:

- `PRE_EXECUTE_REVIEW_PASS` — the packet is fit for authorization, with all
  five open questions `DECIDED`. State plainly that this is not itself an
  authorization, that `p0_cost_execution_authorized` remains `false`, and that
  only the user may flip it.
- `PRE_EXECUTE_REVIEW_FAIL` — name the blocking findings and the single set of
  changes required before re-review.

State the strongest claim your evidence supports and list what is explicitly
not claimed: no FER, no leakage, no SKR, no qualification, no method verdict,
no prediction that P0 will pass.

Do not create any other file. Do not commit. Do not push. Do not change
`cycle_state.yaml`. Do not authorize P0.

## 9. Report back

In your message (not in the file): the verdict, a brief per-check table, the
five open-question decisions in one line each, the literal pytest line, any
`DISAGREE` rows, and this line if and only if it is still true:

「P0 未授权、未执行；正式根仍不存在；next_gate 仍为 P0_PACKET_REVIEW。」
