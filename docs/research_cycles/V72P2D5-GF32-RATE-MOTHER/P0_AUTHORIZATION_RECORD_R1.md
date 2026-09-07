# P0 execution authorization record R1 — 2026-09-07

Authority: user, explicit, in the executing session.
Verbatim authorization: "我现在明确授权执行 P0：授权对冻结的 p0-cost 命令进行且仅进行一次调用， 授权由"尝试"消耗而非由"成功"消耗；不许重试、不许重跑、不许改任何参数， 不许碰 G1 和 G2。"

Scope: exactly ONE invocation of the frozen P0 command. Consumed by the
attempt, not by success. No retry, no rerun, no parameter change, no G1, no G2.

Frozen command:
`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`

Operator watchdog (OQ-P0-2), applied to that command:
`timeout -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
Rehearsal verified on this machine: `timeout -k 30 3 ... -> exit 124`.

Governing decisions from `P0_PRE_EXECUTE_REVIEW_R1.md`:
- OQ-P0-1: decode-attributed total cap 1440 s, record-only, no abort; breach is
  recorded as `RESOURCE_OVERRUN`.
- OQ-P0-2: 1500 s outer process-tree guard, command above.
- OQ-P0-3: P0 PASS is independent of `projection_blocked`; a blocked projection
  gates G2 only, never G1; G1 is judged separately by
  `projected_g1_s <= 900 s`.
- OQ-P0-4: pre-flip isolation evidence reproduced fresh in this session.
- OQ-P0-5: a partial or failed root is retained in place as VOID and never
  reused; the authorization is consumed by the attempt; non-finite output is
  a FAIL.

Fresh pre-flip evidence (this session):

E1 — roots stat (p0_cost absent, g2 absent, g1 4 files, model_f_input 2 files 208467/752):
```
E1-START
ROOT workspace/v72p2d5_p0_cost/20260906_r1 exists False
ROOT workspace/v72p2d5_g2/20260906_r1 exists False
ROOT workspace/v72p2d5_g1/20260906_r1 exists True
   execution_summary.json 267 1788719732911457700
   report.md 146 1788719732911457700
   results.json 2593 1788719732909954400
   table.csv 126 1788719732909954400
ROOT workspace/v72p2d5_model_f_input/20260907_r1 exists True
   model_f_input.npz 208467 1788718027043698800
   model_f_input_summary.json 752 1788718027043698800
E1-END
```
Branch at E1 time: `formal-ir-v72p1-addendum-clean`, HEAD `b27f31da`.

E2 — nine authorizations false, gate intact:
```
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:8:structure_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:11:g0_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:12:g0_recovery_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:24:p0_cost_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:25:g1_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:26:g2_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:27:synthetic_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:28:real_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:29:formal_execution_authorized: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:30:scientific_promotion: false
docs\research_cycles\V72P2D5-GF32-RATE-MOTHER\cycle_state.yaml:42:next_gate: P0_PACKET_REVIEW
```

E3 — CLI refuses while unauthorized:
```
phase 'p0-cost' is not authorized; refusing before any work
exit=3
E3-RECHECK-START
ROOT workspace/v72p2d5_p0_cost/20260906_r1 exists False
ROOT workspace/v72p2d5_g2/20260906_r1 exists False
E3-RECHECK-END
```

E4 — test isolation (195 passed, zero failures):
```
........................................................................ [ 36%]
........................................................................ [ 73%]
...................................................                      [100%]
195 passed, 1 warning in 23.82s
E4-RECHECK-START
ROOT workspace/v72p2d5_p0_cost/20260906_r1 exists False
ROOT workspace/v72p2d5_g2/20260906_r1 exists False
E4-RECHECK-END
```

E5 — compile clean:
```
COMPILE_OK
```

E6 — clean tracked tree (nothing before the marker):
```
---MODIFIED-ABOVE---
```

Watchdog rehearsal (GNU timeout from Git for Windows; Windows timeout.exe does
not implement `-k`/124 semantics):
```
exit=124 (124 expected)
```

Post-run obligation: `p0_cost_execution_authorized` returns to `false`
immediately after the single attempt, whatever the outcome.
