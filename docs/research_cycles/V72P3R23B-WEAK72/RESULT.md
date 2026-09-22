# R23b-0.72 RESULT — V72P3R23B-WEAK72 (DEAD-floor, descriptive)

Terminal: DEAD-floor (descriptive) per main-thread acceptance — NOT a non-scaling assertion. Synthetic-only; no scaling claim asserted.

## Execution evidence (X-ev, operator-attested, quoted)
- SINGLE invocation covering 64 rows (UNION-plan breach): r72 `1024:r72 0/16` + `128:r72 0/16` (granted probe, verify PASS); r65 repeat 0/16 + 0/16 DETERMINISTIC-REPEAT (bit-identical excl wall_s/call_idx, zero new information).
- Undetected 0; exit 0.
- Wall ~269 s + RSS ~213 MB (OPERATOR-ATTESTED).
- Actual 64 sci + 8 setup vs granted 32/4 for this probe -> ENVELOPE AMENDED to 96/12 CONSUMED-CLOSED (prior 0.65: 32/4 + actual 0.72 invocation: 64/8; both grants closed, no further calls under either).
- Gate: r72 literal DEAD (0 <= 2, gap +0) recorded AS DEAD-floor descriptive (below-both-edges at 0.72 too; NOT a non-scaling assertion).
- Truth seeds 4917-4948 fresh/disjoint confirmed.

## Provenance
- Zero replacement / retune; graphs identical-rebuild (4803/4804 + 4813/4814).
- Prior read-only (Model-F npz mtime unchanged).
- Decode ORACLE-free 64/64; synthetic truth only (no real data).
- R23b-0.65 root untouched: `workspace/r23b_weak_73ef80ff-332e-4569-870f-cae33c41a89f`.
- Protected paths clean; no commit / push.

## Manifest-command-STALENESS note (open fix, not done here)
- Manifest `command` field holds the FROZEN_COMMAND constant, not the actual argv; `out_root` + `conditional_r72` + `command_log` are correct.
- Runner must log actual argv going forward.

## Scratch roots
- 0.65: `workspace/r23b_weak_73ef80ff-332e-4569-870f-cae33c41a89f` (untouched).
- 0.72: `workspace/r23b_weak72_20d6d124-fd4f-4dbe-9b6f-5ad0ca6629b1` (this invocation).

## Ceiling
- Synthetic-only. DEAD-floor is descriptive of this 0.72 weak-prior probe (0/16 + 0/16, below-both-edges); it asserts no scaling, FER, leakage, SKR, qualification, or real-data claim.

## Acceptance block
- Extension grant single-consumption: structurally one invocation but wrong scope (UNION 64/8 vs granted 32/4) — SCOPE BREACH, self-reported STOP.
- Pre-EXECUTE Q1-Q6 occurred with missed UNION check (root cause recorded: `--include-r72` returns UNION plan incl r65-repeat; precondition did not assert len(plan) == 32).
- Batch-end reviewer-go: PASS-WITH breach-CONCUR.
- Main-thread: ACCEPTED DEAD-floor-0.72 + breach closed per ruling (envelope AMENDED 96/12 consumed-closed).
