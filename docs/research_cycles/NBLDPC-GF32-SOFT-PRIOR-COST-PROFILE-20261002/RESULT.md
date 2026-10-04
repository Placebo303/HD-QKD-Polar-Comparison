# EXPLORE — accepted posthoc cost profile

Main accepts independent R5 numerical review with one non-blocking resource-accounting finding. UUID `90dcb594-6672-4395-a161-348e7ce74e6c`, root `workspace/gf32_softprior_cost_90dcb594/`; status **POSTHOC_COUNTERFACTUAL_PROFILE_COMPLETE**. One authorized execution, exit 0, no rerun/repair/resume. Seven focused fake tests, compile/T0/dry-run and immediate output absence passed. Operator census_scope owned the exact packet command (synchronous exec chunk3915de); independent census_review did not operate it.

This reuses accepted parent diagnostics without new sampling or decoding. Parents remain separate: rescue UUID31dca97b-808c-4205-ac01-7c5ab7b9e9b5, control155/192; replica UUIDcbe151fe-25f7-4990-8895-858091467e2b, control142/192. Their original classifications remain unchanged. All k branches are counted, and selection uses the original-prior score among syndrome-valid candidates, with frozen ties; truth is used only for subsequent evaluation.

| Parent | k | Candidate exact /192 | Gain | Logical calls | Iterations | Stored call-wall sum (s) | Ratio to own baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rescue | 1 | 158 | +3 | 229 | 7604 | 46.837513 | 1.677258 |
| rescue | 2 | 159 | +4 | 266 | 10851 | 66.802174 | 2.392195 |
| rescue | 3 | 163 | +8 | 303 | 13912 | 85.644256 | 3.066933 |
| rescue | 6 | 167 | +12 | 414 | 23591 | 145.031110 | 5.193585 |
| replica | 1 | 145 | +3 | 242 | 9746 | 58.614562 | 1.780917 |
| replica | 2 | 148 | +6 | 292 | 14005 | 84.205280 | 2.558453 |
| replica | 3 | 149 | +7 | 342 | 18427 | 110.728513 | 3.364322 |
| replica | 6 | 156 | +14 | 492 | 31393 | 188.752185 | 5.734955 |

Baseline iterations/call-wall: rescue4519/27.925050s, replica5461/32.912581s. All rows have observed selected syndrome-valid-wrong0; this is not certification. Independent review recomputed all1536 pair rows, per-graph/paired outcomes, ranking, scoring, pointer/vector choices and costs; k6 matches all192 accepted candidate pointers in each parent.

Costs above are counterfactual sums of the original recorded calls, **not measured pruned-run wall, throughput or RSS**. The profile itself made two parent reads and zero decoder/sampler/search/graph-build calls. Its checkpoint wall0.098881s and high-water RSS35,180,544B are replay resources only. Reported artifact_bytes474,049B is the first-pass size; execution-terminal four files, before review/closeout log appends, measured474,262B (+213B from final metadata/log writes), independently below5MiB. Preserve raw artifacts; do not describe the reported field as final size or a finalization-time gate.

Disclosure49,920bits per parent/per-k METHOD (260bits/frame once), internal branch increment0, tag0; do not sum disclosures across counterfactual variants. Verification NOT_IMPLEMENTED, undetected NOT_MEASURED. No fresh holdout, pooled denominator, FER/f_eff/SKR, significance, causal, real-data, n256/N2048, qualification, promotion, publication, security or route claim.

## Acceleration recommendation (planning only)

Top2 retains only4/12 and6/14 added recoveries; top3 retains8/12 and7/14. This does not support assuming that pruning to2–3 branches preserves most full-branch benefit. Insert a small, separately frozen synthetic hotspot measurement before further costly mechanism sweeps. The accepted decoder already tests syndrome initially and after each full sweep. Its FWHT is NumPy-vectorized, while row/edge/message and iteration loops remain Python; matching iteration/wall ratios do not rule out kernel overhead.

First measure a fixed small set spanning baseline successes, failures and rescue calls, separating import/JIT warm-up from steady-state timing. Optimize only a measured hotspot, preserving full six-branch original-prior selection, numerical behavior and disclosure. Acceptance must compare vectors/selection, syndrome-valid versus wrong, score/tie behavior and iterations, then wall/RSS. Do not set a speedup claim before measurement. Adaptive first-valid stopping changes selection semantics and needs a separate hypothesis and valid-wrong check. Parallel restart may reduce wall while retaining total compute and increasing memory; account for both. This recommendation authorizes no new execution by itself.

No commit/push/merge/add/archive. Independent acceptance and project-memory triage accompany closeout.
