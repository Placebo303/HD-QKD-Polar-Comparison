# D5-ROUTE-STOP-REVIEW-R1 — independent closure review of the current D5 path

## 0. Role and possible verdicts

Independently determine whether evidence justifies stopping the **current D5
two-layer GF32 rate-mother/BP operating path** before G2.

Return exactly one:

- `D5_ROUTE_STOP_REVIEW_PASS` — close the scoped D5 path and return long-term
  direction to the main thread; or
- `D5_ROUTE_STOP_REVIEW_FAIL` — evidence/semantics do not support the proposed
  closure; identify the smallest missing discriminator or correction.

This review does not stop GF32, NB-LDPC, Model-F research, alternative graph or
decoder work, or the whole roadmap. It cannot authorize G2 or a successor.

## 1. Baseline

- Repo `D:/Code/HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Expected HEAD `d6fabf09`
- R2 acceptance `247f8adc`
- Preregistration `f0e4a1cf`
- L1 evidence/gate `d6fabf09`
- Report `G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md`
- Evidence root `workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/`
- Current gate `D5_ROUTE_STOP_REVIEW`
- Accepted formal G1 result remains
  `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`
- G2 absent; all execution authorizations false

## 2. Hard prohibitions

- No formal G1 rerun/resume, CLI `--phase`, G2, real IR, or n=1024 run.
- No VAL read/use. CAL-TRAIN only where needed for independent recomputation.
- No formal-root write/hash/delete/move/rename/overwrite; no VOID-G1 read.
- No code/test/OpenSpec/state/log/memory/existing-report edit.
- No repair, route implementation, authorization, or result acceptance.
- No push/reset/stash/checkout/clean/rebase/revert/amend/normalization.

Only one persistent file:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_ROUTE_STOP_REVIEW_R1.md`

A unique nonformal `workspace/d5_route_stop_review_r1_<uuid>/` may hold review
scripts/results and must be safely removed afterward.

## 3. Review matrix

### S01 — preregistration integrity

Verify `f0e4a1cf` is a single prereg file committed before new scores/calls.
Compare every estimator, endpoint, seed, disclosure point, scaling rule, budget,
stop rule, and terminal class against the executed scripts/results. List every
deviation and judge whether disclosed before interpretation.

### S02 — CAL-only estimator selection

Independently recompute the four held-out folds for E1/E2/E3 from canonical
CAL-TRAIN only. Require zero VAL access. Verify:

- formulas and sufficient statistics;
- grid and fold identities;
- E1=E3 algebraic identity at equal concentration;
- E2 `kappa*=62.10169418915616` selected independently in all four folds;
- mean/SE and 0.01 tie-band arithmetic;
- E2 selection uses held-out L1 NLL, never decoder success;
- CAL information statement `5 - 3.771651` is correctly scoped.

Do not call E2 globally optimal beyond the preregistered estimator/grid family.

### S03 — decoder evidence and accounting

Audit all 75 calls against JSON/scripts/command log:

- paired seeds and one-axis comparisons;
- n64 disclosure `{49,59,64}`;
- n128 `{98,118,128}` and n256 `{196,236,256}`;
- exact, syndrome, iterations, nonfinite, wall, RSS;
- independent exact/syndrome recomputation 75/75;
- no formal G2 identities/roots/thresholds;
- total calls/resources within budget.

Resolve any duplicate/reused call accounting without double-counting.

### S04 — fresh bounded confirmation

In the review-owned nonformal root, rerun at most 12 development calls with
explicitly injected estimator, matrix, decoder, and output:

1. E2 n64 at m=59 and m=64 on two preregistered seeds;
2. E2 n256 at m=236 and m=256 on the same two corresponding seeds;
3. independently recompute exact and syndrome;
4. specifically reproduce or falsify the reported n256 m236
   syndrome-ok/exact-false event for seed 2026090601.

Use <=120 s watchdog per call and RSS <2 GiB. No CLI or formal path. Record
literal results. A deterministic mismatch with persisted evidence is blocking.

### S05 — undetected-type semantic isolation

Verify the n256 event is recorded exactly as development
`syndrome_ok=true`, `exact=false`, never as recovery, pass, FER, or formal
undetected rate. Confirm aggregation/classification keeps exact and syndrome
separate. One event cannot estimate a probability.

### S06 — terminal-class calibration

Assess `L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64` narrowly:

- allowed meaning: none of the preregistered honest estimators recovered any of
  four paired n64 blocks at any tested disclosure through square;
- disallowed meaning: mathematical proof of a universal BP threshold, failure
  of every estimator, or impossibility for all n64 GF32 codes.

If the report uses stronger language such as “honest optimum,” interpret it
only within the frozen three-estimator/grid family or mark a wording finding.

### S07 — block-scaling conclusion

Verify nonzero-rate n128/n256 results are 0/4 at every tested point and square
partials are 1/4 then 2/4. Determine whether this supports stopping further
scaling **within D5**, while explicitly not proving larger blocks or different
graphs/decoders impossible.

### S08 — route-stop scope

PASS closure must be exactly:

```text
D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED
reason: ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY
```

Consequences:

- do not execute frozen G2 under the current path;
- do not rerun/tune formal G1;
- retain all evidence and negative outcomes;
- do not proceed to target n=1024 on this path;
- next work requires a fresh successor proposal changing a named algorithmic
  component, not another estimator/disclosure/seed tweak.

Explicit non-consequences:

- no route-wide rejection of GF32, NB-LDPC, finite-field BP, Model-F, larger
  blocks, alternative graph/mother, decoder schedule, or single-layer design;
- no statement about real FER, leakage, key rate, or security.

### S09 — alternative explanation audit

Review whether any still-plausible explanation would make current G2
informative enough to justify running despite G1 failure. Consider:

- n64 finite-size artifact;
- graph-family/prefix defect;
- layered L1 bottleneck while L2 is healthier;
- alternative BP schedule/initialization;
- estimator family limitations.

These can motivate successors but do not automatically rescue frozen G2.
State whether one missing in-scope discriminator is necessary before closure.

### S10 — lifecycle and evidence preservation

Verify commits/manifests, all authorizations false, promotion false, G2 absent,
formal G1 and other protected roots unchanged, scoped diff empty, no push, and
pre/post snapshots identical.

### S11 — regression status

Run the exact four-file D5 suite with a fresh basetemp:

- `test_v72p2d5_gf32_rate_mother.py`
- `test_v72p2d5_model_f_input.py`
- `test_v72p2d4_cal_gf32_model_rate_audit.py`
- `test_v72p2d4r2_cal_gf32_model_rate_audit.py`

Use `-p no:cacheprovider`; require zero failures. Record the literal summary
and remove only review-owned temp paths.

### S12 — successor handoff quality

Without designing or implementing the successor, identify which component the
evidence most strongly says a new proposal must change. Rank at most three:

- two-layer decomposition/L1 bottleneck;
- graph/mother construction and short-block topology;
- BP schedule/decoder dynamics;
- channel-model representation;
- block geometry.

This ranking is advisory for the main thread and cannot authorize work.

## 4. Verdict criteria

PASS requires S01–S11 all pass and no missing discriminator that can change the
scoped closure. S12 may be advisory.

FAIL if prereg was violated materially, CAL selection used VAL/decoder outcome,
fresh deterministic checks contradict evidence, exact/syndrome were conflated,
route-stop scope overreaches, current G2 remains scientifically informative
under the unchanged path, tests fail, or evidence roots drift.

## 5. Report and return

Create only `D5_ROUTE_STOP_REVIEW_R1.md` with S01–S12 table, CAL arithmetic,
75-call audit, fresh <=12-call results, undetected-type event treatment,
terminal-class calibration, closure scope/non-scope, alternative explanations,
successor component ranking, tests, root/lifecycle equality, findings, and final
verdict.

Do not commit or push.

Return verdict; S01–S12 counts; fresh-call table; closure statement; strongest
evidence; overclaim corrections; successor ranking; four-file pytest line;
protected-root equality; prohibition checklist; sole report path.

End exactly:

`D5 当前两层 rate-mother/BP 路径停止候选已完成独立评审；这不否定 GF32/NB-LDPC 主线，也不授权 G2 或任何后继执行。`

