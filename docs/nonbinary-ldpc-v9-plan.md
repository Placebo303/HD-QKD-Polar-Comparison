# Nonbinary LDPC V9 Plan: GF(1024) Ensemble to Long Superframes

Date: 2026-08-04

## Decision

Proceed with one gated route rather than another decoder ladder:

```text
V9A full-vector GF(1024) MC-DE
  -> V9B n=4096 finite bridge
  -> V9C n=16384 bridge
  -> V9C n=32768 canary and development
  -> STOP before qualification
```

V8-60 established that the full-vector method and corrected rate algebra can
reproduce a cited q=4 QSC reference. It did not establish a GF(1024) threshold
or finite-length FER. V9A must do that bridge before a new codebook exists.

## Gates

| Stage | Frozen advance gate |
|---|---|
| V9A robust DE | one reviewed/once-executed/replayed package; conservative thresholds >=.22/.32 |
| V9A target DE | >=.215 at p=.20 and >=.32 at p=.30; failure selects robust and marks efficiency_target_not_met |
| V9B n=4096 4+4 | >=3/4 verified each stratum, forbidden=0, exact disclosure, median <=2h, RSS <=3GiB |
| V9C n=16384 4+4 | >=3/4 each, forbidden=0, exact disclosure, median <=8h, RSS <=3GiB |
| V9C n=32768 4+4 | >=3/4 each, forbidden=0, exact disclosure, median <=16h, hard timeout 24h, RSS <=3GiB |
| V9C n=32768 16+16 | >=15/16 each, forbidden=0, strict replay, median <=24h, RSS <=3GiB |

Target f=1.08 is preferred, but only per stratum where V9A target DE passes.
Otherwise the route uses robust f=1.15 and records
`efficiency_target_not_met`. Robust DE failure stops all finite-length work.
The p=.20 target gate is .215, below its approximate f=1.08 capacity threshold
.21827, so the target remains scientifically feasible; p=.30 target stays .32.

Check counts are always computed as
`ceil(f * H_q(p) * n)` with
`H_q=[h2(p)+p log2(q-1)]/log2(q)`; rounded counts in discussion are not code
constants. Rho must satisfy the harmonic edge-perspective rate equation.

V9A plan-only freezes all four searches/budgets/seeds/targets, receives an
independent read-only review, executes deterministically exactly once including
multi-seed validation, and strict-replays exactly once. Failure cannot be tuned
or rerun.

Every n>1024 input is a provenance-bound constituent superframe: n=4096 uses
4, n=16384 uses 16, and n=32768 uses 32 ordered disjoint 1024-symbol frames,
with no cross-stage reuse. Every finite GF(1024) matrix has `rank(H)=m` before
plan preparation; a rank-deficient graph is rebuilt within its frozen bound or
stops.

## Scientific Protections

- one Bob observation plus explicitly counted public information only;
- error-domain layered log-FFT-SPA, no Alice truth or fallback;
- deterministic irregular PEG/ACE-or-equivalent graphs and nonzero GF labels;
- each n=32768 superframe binds 32 ordered disjoint 1024-symbol constituents;
- V9C uses one fixed rate per stratum and only syndrome plus fixed tag;
- every scientific package is prepare/review/one execute/one replay;
- failed packages are retained, never tuned or rerun.

V9C freezes `m=ceil(f*H_q(p)*n)` separately for p=.20/.30. Syndrome leakage is
exactly `L_recon=10*m` bits; the fixed correctness tag is separately 64 bits,
so `L_total=10*m+64`. These are hard caps. V9 forbids puncturing, shortening,
adaptive stages, informative indices/control, or any other reconciliation
payload. Blind rate adaptation is deferred to a separate V10 change.

## Authorization Boundary

The OpenCode packet may autonomously advance through V9C when each gate passes.
It must stop at the first failed gate and must stop after the n=32768
development decision even on success. Qualification, confirmation, real/N4,
promotion, and formal comparison require a new OpenSpec change.
