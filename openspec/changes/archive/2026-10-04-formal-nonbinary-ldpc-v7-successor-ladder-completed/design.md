# Design: Formal Nonbinary LDPC v7 Successor Ladder

## Evidence and Ranking Rationale

The direct HD-QKD studies by Müller et al. model reconciliation as coding on a
q-ary symmetric channel and report degree distributions optimized through
density evolution ([2024 paper](https://arxiv.org/abs/2307.02225),
[conference version](https://arxiv.org/abs/2305.08631)). This is the strongest
match to the project channel, but implementing a trustworthy optimizer is a
larger step than changing the mother ensemble.

Kasai et al. construct rate-compatible low-rate codes by multiplicatively
repeating a `(2,3)` nonbinary mother and decode them with nearly the mother's
complexity ([paper](https://arxiv.org/abs/1004.5367)). Martinez-Mateo and
Elkouss show the broader `(2,k)` construction is simple and inherently
rate-adaptive for QKD ([2025 paper](https://link.springer.com/article/10.1140/epjqt/s40507-025-00376-9)).
Although that application is CV-QKD rather than this project's q-ary DV
channel, R1 is the cheapest controlled test of the selected successor.

R3 follows nonbinary multilevel reconciliation and joint rate/degree design
ideas reported in [informed NB-LDPC QKD design](https://link.springer.com/article/10.1007/s11128-024-04343-8),
but is ranked third because layer conditioning and leakage reconstruction add
new semantics.

## Shared Automatic State Machine

For each subroute:

1. implement pure core, deterministic construction, oracle vectors, and
   fail-closed guards;
2. pass T0/T1, fake lifecycle/replay T2, and v5/v6 regression T3;
3. prepare one fresh 4+4 canary plan;
4. stop for a read-only plan audit performed by a distinct reviewer context;
5. execute exactly once and strict-replay exactly once;
6. if either stratum is 0/4, freeze `failed_canary` and advance;
7. otherwise prepare fresh 16+16 sacrificed development, audit, execute once,
   and replay once;
8. if the development-ready definition passes, freeze `ready` and stop the
   entire ladder; otherwise freeze `non_ready` and advance.

No frame, seed, array, plan, or output is reused between subroutes. An internal
exception finalizes a non-ready evidence package; it does not silently retry.

## R1: Multiplicatively Repeated GF(1024) Codes

### R1A Mother

- identity `nbldpc_formal_v7_r1a_mr0`;
- GF(1024), n=256 variables, `(dv,dc)=(2,3)`, nominal rate 1/3;
- deterministic PEG mother, nonzero SHA256-derived coefficients, full GF rank;
- flooding FFT-QSPA as the literature-reference schedule and layered FFT-QSPA
  as a frozen same-code diagnostic; max_iter=100, damping .75, workers=1;
- syndrome disclosure approximately `10*(n-k)` plus an invoked 64-bit tag.

### R1B One Repetition

R1B runs only if R1A canary is 0/4 in either stratum.

- identity `nbldpc_formal_v7_r1b_mr1`;
- exact R1A mother construction under a new identity and fresh data;
- one multiplicative repetition per variable using deterministic nonzero
  GF(1024) multipliers and independently derived q-ary observations;
- effective rate 1/6; repeated evidence is combined into the variable prior,
  not represented as a second dense Tanner graph;
- the public transcript records multiplier identities/control but never raw or
  corrected symbols.

R1B is the last low-rate repetition point because further repetition would
exceed the frozen 8.75-bit/symbol disclosure ceiling.

## R2: QSC-Informed GF(1024) Code

- identity `nbldpc_formal_v7_r2_qsc_de`;
- GF(1024), n=1024;
- separate p=.20 and p=.30 fixed-rate codebooks;
- target syndrome fractions start from `1.15*H_q(p)/10`, rounded upward to a
  whole check count;
- a bounded, deterministic population search evaluates at most 32 candidate
  variable-degree distributions using q-ary density-evolution threshold proxy;
- degrees are limited to 2..8; mean check degree <=12; deterministic PEG turns
  the selected distribution into a full-rank matrix;
- layered FFT-QSPA, max_iter=100, fixed schedule selected before any canary.

If the exact density-evolution equations cannot be independently tested against
published/small-field vectors, the route stops `implementation_blocked`; a
hand-invented score must not be called density evolution.

## R3: GF(32)xGF(32) Multilevel Code

- identity `nbldpc_formal_v7_r3_gf32x2`;
- each natural GF(1024) symbol is reversibly split into high and low 5-bit
  natural words; mapping is frozen and exhaustively round-tripped;
- two GF(32) codes of n=1024; layer 0 is decoded first, layer 1 priors may use
  only Bob data, public model data, and verified layer-0 output;
- a frame is successful only when both layers are syndrome-consistent and the
  final reconstructed 10-bit symbols pass one 64-bit Toeplitz tag;
- all layer syndromes count as key-dependent disclosure; failed layer-0 frames
  do not invoke layer 1 or verification;
- EMS with deterministic `nm=32` is primary; exact FFT-QSPA is the small-field
  oracle and fallback is forbidden in production.

## Freshness and Output Policy

All development packages live under fresh explicit `workspace/` UUID roots.
The automatic ladder must prove absence of any v7 directory under
`comparison_bench/outputs_comparison/formal_ir_methods/`. Only plans reviewed
as ready may execute. Every execute and replay count is exactly one.

## Expected Interpretation

R1 is most likely to produce convergence quickly but may be inefficient. R2 is
most likely to produce a scientifically competitive efficiency if correctly
implemented. R3 is most likely to reduce runtime/memory, but success depends on
the conditional layer model. These are hypotheses; none is a promised success
rate.

