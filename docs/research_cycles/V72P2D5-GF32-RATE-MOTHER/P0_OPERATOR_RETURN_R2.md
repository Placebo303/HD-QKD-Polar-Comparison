# P0 operator return R2 — second authorized invocation, 2026-09-07

Verbatim command:
`"C:\Program Files\Git\usr\bin\timeout.exe" -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
(GNU timeout from Git for Windows; working kill-guard rehearsed this session:
`-k 30 3 ... -> exit=124`. Bare `timeout` on this host is Windows timeout.exe
and does not implement `-k`/124 semantics.)

Exit code: `0`
Wall time: `8.6278899 s` (operator-measured process wall, `Get-Date` delta)

Literal stdout:
```
(empty — 0 bytes)
```

Literal stderr:
```
(empty — 0 bytes)
```

Output root `workspace/v72p2d5_p0_cost/20260906_r1` (created by this run; absent
before it, confirmed by pre-flip E1/E3/E4 stats):
```
Name                   Length LastWriteTime
execution_summary.json    267 2026/9/7 18:09:17
report.md                 227 2026/9/7 18:09:17
results.json             1197 2026/9/7 18:09:17
table.csv                 186 2026/9/7 18:09:17
```

Literal scalars (`results.json` / `execution_summary.json` / `report.md`):
- `decoder_calls`: 12
- per-record `f` / `kind` / `wall_s` / `iterations` / `rss_bytes`:
  - f=1.0, kind=app, wall_s=1.8862763999495655, iterations=360, rss_bytes=null
  - f=1.0, kind=oracle, wall_s=1.04731999989599, iterations=180, rss_bytes=null
  - f=1.2, kind=app, wall_s=3.459295800072141, iterations=360, rss_bytes=null
  - f=1.2, kind=oracle, wall_s=1.671841400093399, iterations=180, rss_bytes=null
- `projected_g1_s`: 161.8241519993171
- `projected_g2_s`: 485.47245599795133
- `projection_blocked`: false
- `passed`: true
- (also recorded, not cost scalars: `block_length`: 64,
  `f_list`: [1.0, 1.2], `frozen_rows`: {1.0: {m1: 49, m2: 43},
  1.2: {m1: 59, m2: 52}}, `seeds`: [2026090510, 2026090511])

Resource accounting (OQ-P0-1 / OQ-P0-2):
- Decode-attributed total `sum(records[].wall_s)` =
  1.8862763999495655 + 1.04731999989599 + 3.459295800072141 + 1.671841400093399
  = 8.064733600011096 s against the 1440 s cap. No single record exceeds 120 s
  (max 3.459295800072141 s). `RESOURCE_OVERRUN`: NO.
- Peak RSS against the 2 GiB reference: not assessable — all records carry
  `rss_bytes: null` (this platform run recorded no RSS). No claim is made.
- Watchdog did not fire (exit 0, wall 8.63 s << 1500 s guard).

Post-run state: `p0_cost_execution_authorized` returned to `false` before any
analysis or writing; all nine `*_execution_authorized` false,
`scientific_promotion: false`, `next_gate: P0_PACKET_REVIEW` unchanged.
New P0 root contents were not touched after the run (stat/list/read only).

## NOT_INTERPRETED

No conclusion is drawn about correctness, rate points, FER, leakage, key rate,
the method, or G1/G2 readiness. The numbers above are recorded literally as
cost evidence only. Acceptance requires an independent Pre-RESULT review; G1
remains unauthorized.
