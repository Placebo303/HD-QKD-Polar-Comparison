# P1 Stage-1 rescue disclosure — main-thread finding (2026-09-26)

Status: **independent PASS_WITH_FINDINGS; main accepts the modeled arithmetic correction only**. Read-only inspection of the accepted P1 `rows.json` and `p1_stage1_runner.py`; no decoder or data execution, no original artifact edits.

## Finding

The P1 Stage-2 loop **models disclosure** of eight additional GF(32) check rows for **every Stage-1 non-exact frame**, then cold decodes it. Under that frozen nested-protocol accounting model, the 40-bit rescue cost is incurred for `attempted = stage1_fails`, regardless of the rescue outcome. The stored helper `expected_leak_for(n_rescued)` and packet F7 instead use `rescued/240`. This undercounts any failed rescue within that model. The trigger set uses simulator `exact_match`; this is not an observed wire transcript or a demonstrated deployable verification protocol.

| arm | attempted | rescued | final fail | stored E (bits/frame) | attempt-charged E | stored f_exp | diagnostic corrected f_exp | stored f_eff | diagnostic corrected f_eff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P1S1-R1 | 84 | 83 | 1/240 | 1077.833333 | 1078 | 1.264255374 | 1.264450867 | 1.284195686 | 1.284391180 |
| P1S1-R2 | 138 | 138 | 0/240 | 1087 | 1087 | 1.275007507 | 1.275007507 | 1.275007507 | 1.275007507 |

Calculation: `E_attempt=1064+40·attempted/240`, `f_exp=E_attempt/852.544`, `f_eff=f_exp+4.785675·final_fails/240`. The R1 difference is `40/240 = 0.1666667` bit per frame, or `0.000195493331` in both f ratios; headroom falls from 30.4767 to 30.31 bits. The P1 mechanical outcome (84 attempts, 83 rescued; 138/138 on R2) and its fail/pass gate pattern do not change: R1 still fails zero-final-error gate, R2 still misses the 21.5-bit headroom gate with 21.31 bits. These are accepted **modeled synthetic accounting corrections**, not edits to the frozen P1 results or a new route decision.

## Independent review and acceptance

An independent `luna_worker` recomputed both arms from the stored summary counts and P1 source rules: **PASS_WITH_FINDINGS**. It confirmed attempted=84/rescued=83/F=1 on R1 and 138/138/F=0 on R2, all E/f/headroom numbers above, and unchanged gate patterns (R1 Fail/Pass/Pass; R2 Pass/Pass/Fail). Its finding is that no actual wire/transcript event was recorded and the trigger was selected by simulator `exact_match`. Main-thread acceptance is limited to the corrected arithmetic **within this frozen synthetic model**. Old artifacts stay unchanged; no new scientific route or real-data disclosure acceptance follows.

The M3-b successor freezes attempt-charged disclosure and requires a fake test where one rescue fails. Its paired comparison must distinguish the historical R1 `f_exp/f_eff` from this accepted modeled correction. This finding does not establish any real-data `leak_EC` ledger or SKR.
