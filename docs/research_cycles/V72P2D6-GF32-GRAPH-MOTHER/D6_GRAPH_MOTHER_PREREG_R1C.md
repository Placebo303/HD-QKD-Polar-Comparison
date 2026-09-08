# D6 graph/mother — preregistration R1c addendum (parallel-only revision)

Status: `FROZEN_PREREG_R1C`. R1 §§4–9 frozen semantics carry forward verbatim;
this addendum only permits parallel execution mechanics. R1b PASS is void;
void roots `d6_graph_mother_r1_923a25897087495ab4605870e561f3cc` (144 rows,
zero L2-APP) and `d6_graph_mother_r1_e8ee45a4669c4738bf7e96d926ba7e5c` are
quarantined with zero reuse. R1c uses fresh root
`workspace/d6_graph_mother_r1c_<uuid>/`.

## §4–§6 carry-forward (no change)

- Decomposition `A = 32*U1 + U2`; E2 prior `LAMBDA_STAR = 137.3823795883264`,
  CAL-only artifact, floors `1e-300`/`1e-15`, probability-domain transfer.
- GF32 poly 37; `bind_historical_decoder` cold start `max_iter=90`,
  `damping_alpha=1.0`; L1→APP-L2, oracle diagnostic only.
- Exact/syndrome separation; one sample per `(n,block_seed)` byte-identical
  across arms.
- Row budgets n64/n128/n256 per R1 §4 table; B0/B1/T1–T4/M1/M2 per R1 §5;
  common coefficients `202609120100+n` / `202609120200+n`.
- Structural gates §6: full `audit_prefix` + exact girth BFS
  (`NOT_COMPUTED` only when acyclic) + row max/sumsq + M DSU rank + replay +
  no-parallel-edge + overflow; eligibility per-prefix both layers; blind
  freeze B0+B1+best-2-T+both-M (max 6) + best-T/best-M fallbacks before any
  decoder call.

## §7 R1c implementation paths (additive)

Allowed: `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
(T2 incremental cache only),
`comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (parallel
equivalence),
`scripts/v72p2d6_graph_mother_development.py` (parallel pool + chunking),
D6 OpenSpec/cycle documents, one UUID root
`workspace/d6_graph_mother_r1c_<uuid>/`, final append-only
`docs/decision-log.md` + `AGENT_PROJECT_MEMORY.md`, D5 `cycle_state.yaml`
linkage + `next_gate` only. Beliefs chain at 61767ca2 preserved
(`invoke` transient `"beliefs": res.get("beliefs")`).

## §8 R1c bounded execution (parallel mechanics only)

- Seeds/budgets/rules identical to R1 §8: canary 4 / confirmation 16 /
  scaling 4; 2500 calls / 12 h / 120 s / <2 GiB / no retry.
- Workers: 18 full (20 cores, leave 2) iff `18 * peak_rss_estimate < 2 GiB`
  (void-measured ~88.5 MB → ~1.59 GB, fits); else 14/12/8 by measured RSS,
  chosen count + reason logged. Main process single-thread generates all
  `(n,seed)` blocks before dispatch; workers receive read-only copies.
- Structure `arm x layer` parallel (ProcessPoolExecutor); deterministic
  assembly in ARMS order; replay equality per task.
- T2: incremental `(four,mpair,incidence,rmax,rsumsq,stup)` with
  `pair_counts` + `pair_to_cols` + O(1) degree update + support reuse;
  adjacency bit-sets for affected scan; no girth inside loop (final audit
  per §6).
- Decoder cells parallel across cells; intra-cell L1→APP dependency
  sequential on assigned worker; each counted invocation logs PID/wall/RSS;
  watchdog 120 s poll + terminate/respawn per worker; no retry.
- Chunking: each phase chunk wall <1.5 h (<5400 s), same UUID root, append
  mode; stop before exceeding call/wall budgets; only task-owned processes
  terminated.

## §9 Evidence (unchanged file set)

`manifest.json`, `structure_records.csv`, `selected_arms.json`,
`decoder_records.csv`, `summary.json`, `command_log.txt` + scalar-ID
provenance. Independent `verify_command` recomputation. Pre-RESULT read-only
except its own file. Post-call fixes limited to evidence/report arithmetic.

## Prereg witness (R1c)

Branch `formal-ir-v72p1-addendum-clean`, starting HEAD `4792247d`
(R1b reviews accepted, code 61767ca2). No decoder call under R1c before
R1c implementation-review PASS + Pre-EXECUTE PASS. No `--phase`/G1/VOID/G2/
VAL/real. No D5/auth/src-experiments-tools change. No search/retry/push.
