# Proposal — V72P2D6 GF32 graph/mother successor (bounded development)

Change: `v72p2d6-gf32-graph-mother-successor`
Predecessor gate: `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`
Packet: `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_HEAVY_R1_TASK_PACKET.md` (frozen)

## 1. What

A strictly single-axis successor experiment: keep the accepted D5 scientific
contract fixed (decomposition `A = 32*U1 + U2`, E2 total-concentration/backoff
prior, row budgets, historical row-layered FFT-QSPA GF32 decoder with cold
start / `max_iter=90` / `damping=1.0`, L1-then-APP-L2 schedule, exact/syndrome
semantics, seeds-by-role) and change only the finite GF32 parity-check
graph/mother. Eight frozen arms: two controls (`B0` native D5, `B1` D5 support
with the D6 common coefficient stream), four degree-3 topologies
(`T1` PEG, `T2` cycle-greedy, `T3` SC width 4, `T4` SC width 8), two
accumulator/MET finite-feasible arms (`M1` forest-MAX, `M2` forest-HALF).
Decoder-blind structural gating selects at most 6 decoder arms; an n=64
canary on disjoint confirmation seeds decides confirmation; conditional
development-width scaling (n=128/n=256) runs only on total n=64 no-signal.

## 2. Why

D5 closed two hypotheses with accepted terminals: the fixed two-layer
rate-mother/BP path completed with no signal (G1), and all 252 reversible 5+5
bit partitions left the mapping decoder-blind optimal with APP exact `0/8` at
n=64 (`DECOMPOSITION_NO_N64_RECOVERY`). The remaining vertical mainline
question before any decoder-dynamics work is whether a structurally different
nested short-block mother recovers useful APP decoding signal.

## 3. Scope (frozen)

- New standalone module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  that reuses (imports, never copies) D5 arithmetic/prior/sampler/decoder
  adapter/audit helpers; new test file; one development script
  `scripts/v72p2d6_graph_mother_development.py`; D6 cycle documents; one UUID
  development root.
- n=64 canary (seeds `2026091000..03`), disjoint n=64 confirmation
  (`2026091010..25`), conditional scaling canaries (`2026091100..03`).
  Budgets: 2500 decoder calls, 12 h wall, 120 s per-call watchdog, RSS < 2 GiB,
  no retries.
- Terminals: `D6_GRAPH_STRONG_N64_RECOVERY`,
  `D6_GRAPH_PARTIAL_N64_SIGNAL`, `D6_GRAPH_N64_SIGNAL_INVALID`,
  `D6_GRAPH_STRONG_SCALING_RECOVERY`, `D6_GRAPH_PARTIAL_SCALING_SIGNAL`,
  `D6_GRAPH_SQUARE_ONLY_DIAGNOSTIC`,
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`,
  `D6_GRAPH_IMPLEMENTATION_OR_RESOURCE_BLOCKED`.

## 4. Non-goals (hard prohibitions)

No CLI `--phase`; no formal G1 rerun/resume/recovery; no VOID-G1 reads; no G2;
no VAL/real/raw data; no parquet outside CAL-TRAIN 702..1725 (D6 reads none —
prior comes only from the accepted Model-F artifact); no edits under `src/`,
`experiments/`, `tools/`; no D5 production wiring/constant/result/authorization
changes; no graph/block/coefficient/decoder/row search or tuning; no ensemble,
protograph/MET optimizer, DE project, or reusable graph framework; no frozen
cell retry; no push/force/reset/checkout/stash/clean/amend/rebase/EOL
normalization; no scientific acceptance by operator or reviewer (reviewed
candidate terminal only); no decoder-dynamics follow-up in this change.
