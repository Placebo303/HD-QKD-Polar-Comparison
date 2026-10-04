# Independent acceptance — GF(32) MRB reachability diagnostic

Batch: `c4fab9ba-ead1-4c64-8d0b-82177ace721c`  
Operator: `reach_operator`  
Independent reviewer: `faithful_scope` (reviewer != operator)  
Main disposition: accepted, within the finite synthetic claim ceiling below.

## P6 review

The reviewer independently read the five retained machine artifacts and used the saved NPZ vectors to recompute all 192 frames. Checks covered each original-belief stable-ascending reliability permutation; the augmented GF(32) RREF and rank; the 76 free coordinates; `D_free`; raw-free-base syndrome validity; unique truth reconstruction; and the saved CSV/NPZ graph, frame, and seed mappings. The recomputed rows, per-graph counts, full histogram summaries, and total matched the persisted result. This was vector-level recomputation, not a check of stored booleans alone.

The accepted aggregate is 146 exact-and-syndrome-valid outputs at `D_free=0`, 46 raw-syndrome-fail outputs all at `D_free>=2`, no `D_free=1`, and zero syndrome-valid-wrong outputs. Per-graph exact/fail counts in frozen seed order are `26/6, 23/9, 24/8, 25/7, 22/10, 26/6`. For the 46 failures, descriptive `D_free` range/median/mean are `6..36 / 21 / 20.5`.

The reviewer also reconciled 192 BP calls, zero OSD/candidate calls, 49,920 disclosed syndrome bits, zero tag bits, `verification=NOT_IMPLEMENTED`, `undetected=NOT_MEASURED`, zero resource markers/violations, recorded cost scope and the 6,402,852-byte NPZ. Wall and RSS values retain the packet's stated measurement limits.

## Disposition and limits

P6: **PASS**. Main acceptance is limited to the frozen synthetic diagnostic: for the 46 observed syndrome-fail frames, truth is outside each frame's actual order-0/1 MRB free-coordinate set. It does not establish global code distance, a decoder performance gain, FER, `f_eff`, SKR, throughput, security, qualification, publication, or a route decision. This batch's dispatch authorization is consumed; this closeout creates no additional execution authority.
