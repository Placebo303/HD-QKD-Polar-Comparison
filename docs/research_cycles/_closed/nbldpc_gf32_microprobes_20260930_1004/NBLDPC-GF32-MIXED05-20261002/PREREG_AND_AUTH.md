# EXPLORE — weaker single-variable prior bias

UUID `20297614-3e4e-4d14-a70b-d74237e5ddd4`; root `workspace/gf32_mixed05_20297614`; branch `formal-ir-v72p1-addendum-clean`. Authority and unchanged input, disclosure, artifacts, budget, ownership/testing/dispatch clauses M1/M3–M5 in sister `../NBLDPC-GF32-RANK2-FALLBACK-20261002/PREREG_AND_AUTH.md` are retained explicitly, with the deltas below. This is a separate EXPLORE batch, not an extra arm or extension of rank2. One attempt, no rerun/repair/resume/pooling/ranking or route/promotion.

## D1 Separate input

Same accepted six H/PMF/GF32/N128 and192 keys; namespace `gf32-softprior-mixed05-v1`, fresh seeds disjoint from all historical exclusions and sister rank2. Original default reference decoder BP90/alpha1/cold/warmNone for ALL arms. No new source family or lambda scan.

## D2 Sole changed factor and paired selection

Baseline shared once. Baseline syndrome-valid passes through both methods. For each baseline syndrome-fail, select SAME rank1 variable from ORIGINAL baseline CHECK_UPDATED beliefs/active set using accepted entropy/tie rule. Control runs six accepted one-hot cold branches, guesses[0,1,3,7,15,31]. Candidate runs all six cold branches with selected raw prior row `q_g(a)=0.5*pi_original(a)+0.5*1[a=g]`; pi_original is that unchanged normalized RAW prior row, before decoder flooring. Other rows unchanged. Decoder's existing floor1e-15/row normalization then applies equally to both arms. No rank2 or message continuation. Lambda .5 is frozen to test substantial weakening of the intervention; no oracle-selected lambda.

For each guess index, order control→mixed for even frame index, mixed→control for odd frame index. Recompute own syndrome; each method chooses its valid branch by ORIGINAL effective-prior sum-log score and1e-12/lowest original branch-index tie; no valid branch uses shared baseline fallback. Truth enters only AFTER independent method choices. Run all six branches, not an early truth-based stop. Retain all actual returned vectors, priors/selection/map evidence and each method's chosen call pointer.

## D3 Costs/classification and boundaries

Physical calls=192+12F <=2496; each method's logical cost=192+6F, shared baseline counted once. Increment=selected mixed exact minus selected one-hot exact; losses also reported, no monotonicity assumption. M3 descriptive flags apply to this increment and six graph deltas, with baseline range only used as diagnostic floor/ceiling. Selected/raw syndrome-valid-wrong are separate; failed calls/status stay observable. Same1200s/1GiB/20MiB caps, single-pass STOP retention and independent batch-end review. Typical792 calls is only an estimate based on historical F=50, not measured cost or guaranteed completion.

Production NOT_DISPATCHED until M5 gates/main dispatch. Exact command:

`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_mechanism_pair --mechanism mixed05 --execute --out-root workspace/gf32_mixed05_20297614`

Read-only planned-seed evidence and exact15 exclusion pointers are explicitly retained from sister rank2 packet's final section. This plan has192 unique seeds, no mutual/historical collision; only seed arithmetic has occurred, not frame draws or production.

Independent `mechanism_freeze_review` PASS on2026-10-02, no required changes; scope is packet/OpenSpec only. Main accepts the freeze and authorizes implementation by `correction_mechanism_read`, not production; focused tests/main dispatch and independent batch-end result review remain outstanding.

2026-10-02 main dispatch under retained literal user grant: frozen implementation,14fake tests/compile/T0/dry/scoped-root checks passed; independent core pre-read plus M4/M5 final short confirmation PASS. Production exact command above DISPATCHED conditionally after rank2 owned process exits and no concrete shared-code numerical blocker is discovered. Recheck this root absent and intended branch before its one launch; no parallelBP, retries/repairs/resume/tuning or selfaccept. This has separate192 seeds/root and its own batch-end review; rank2 outcome does not change lambda/inputs/thresholds.

Closeout2026-10-02:one-shot consumed/exit0/session96703/PID50587;independentactualfull_eff_tests PASS_WITH_FINDINGS. Corrected authoritative RESULT/IA accepted:baseline144 inside[39,153],control161/candidate153,delta−8,INCREMENT_NOT_ESTABLISHED. Retainedrawmachine CONTROL_RANGE_UNINFORMATIVE usedwrongcontrol-field predicate; terminal-only,error doesnotaffectinputs/branches/choices/cost. Currentprocess was completed withoutrewrite/rerun; futurecodefix cannot reviveconsumedgrant. Actualterminalbytes3901813 vsreported3901395 beforeappend. No default/route/qualification promotion.
