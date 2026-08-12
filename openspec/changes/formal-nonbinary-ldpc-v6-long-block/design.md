# Design: Formal Nonbinary LDPC v6 Long-Block Development

## Decision

Keep the alphabet fixed at `GF(1024)` and change the block-length regime from
64 to 1024 symbols.  Implement one boring baseline: variable-node degree two,
check-concentrated deterministic PEG construction, and the already understood
layered FFT-QSPA family.  Do not implement three new decoder families at once.

For a q-ary symmetric channel,

`H_q(p) = h2(p) + p*log2(q-1)` bits/symbol.

At q=1024 this is approximately 2.72 bits/symbol at p=.20 and 3.88 at p=.30.
The two frozen syndrome sizes disclose 3.125 and 4.6875 bits/symbol,
respectively, before verification.  They are intentionally conservative
development points while remaining materially closer to the Slepian-Wolf
scale than the v5 final 560/64 = 8.75 bits/symbol.

## Scientific Basis

- Müller et al., [Efficient Information Reconciliation for High-Dimensional
  QKD](https://arxiv.org/abs/2307.02225), directly studies nonbinary LDPC on
  q-ary symmetric HD-QKD channels and reports near-Slepian-Wolf operation.
- Müller et al., [Information Reconciliation for HD-QKD using Nonbinary LDPC
  Codes](https://arxiv.org/abs/2305.08631), explicitly motivates
  density-evolution degree optimization for large alphabets.
- Kasai et al., [Multiplicatively Repeated Non-Binary LDPC
  Codes](https://arxiv.org/abs/1004.5367), and the 2025 QKD adaptation
  [Martinez-Mateo and Elkouss](https://link.springer.com/article/10.1140/epjqt/s40507-025-00376-9)
  make `(2,k)` mother codes plus multiplicative repetition the reserved second
  route if the long-block baseline is still weak.
- The public [Lcrypto FFT-QSPA repository](https://github.com/Lcrypto/BP-decoder-for-NB_LDPC-codes)
  contains flooding/layered NB-LDPC examples up to q=1024.  Its MATLAB/MEX
  implementation and unclear reuse license make it an optional independent
  oracle, not a dependency or copy source.
- A faithful nonbinary proximal-ADMM decoder requires the embeddings and
  three-variable check decomposition described in
  [Wang and Bai](https://arxiv.org/abs/2201.00370).  That is not a small patch
  to the v5 bitwise relaxation, so it remains outside this milestone.

## Codebook Contract

Create two separate fixed-rate matrices rather than nested row prefixes:

| Stratum | q | n | m | Rate | Variable degree | Check degrees |
|---|---:|---:|---:|---:|---:|---|
| p=.20 | 1024 | 1024 | 320 | .6875 | exactly 2 | 6 or 7 |
| p=.30 | 1024 | 1024 | 480 | .53125 | exactly 2 | 4 or 5 |

For each matrix, process columns in ascending order.  The first edge chooses
a minimum-degree check using a domain-separated SHA256 tie-break.  The second
edge uses breadth-first PEG expansion to maximize local girth, then minimum
check degree, then the same tie-break.  Parallel edges are forbidden.
Nonzero GF coefficients are derived independently from SHA256 and reduced to
`1..1023`.  Construction is deterministic and has no unbounded search.

Canonical bytes include a new magic, q/n/m, field identity, construction
version, seed, sorted row entries, and coefficients.  The manifest records
SHA256, GF rank, edge count, degree histograms, parallel-edge count, four-cycle
count, and reconstruction parameters.  Full row rank is required.

## Decoder Contract

Reuse the accepted field arithmetic and Walsh-Hadamard convolution semantics
without modifying old modules.  The v6 module owns n=1024 storage and SHALL:

1. form q-ary symmetric priors from Bob symbols and frozen p;
2. run ascending-row layered FFT-QSPA with lambda=.75;
3. normalize every message, reject NaN/Inf/negative mass, and fail closed on
   an all-zero normalization constant;
4. check the complete syndrome after every full iteration;
5. stop at syndrome consistency or 50 iterations;
6. invoke the existing locked Toeplitz verification only after consistency.

Dense message memory is bounded by the exact edge count (2048).  Production
execution is workers=1.  Tests use tiny graphs or an explicit fake runner and
must never enter an official output root.

## Oracle Strategy

The internal oracle is exhaustive posterior enumeration on very small GF(4)
and GF(8) graphs.  It checks field operations, coefficient permutations,
single-check convolution, syndrome orientation, and hard-decision consistency.
This is sufficient for the first implementation milestone and avoids a new
runtime.  A manually supplied JSON fixture from Lcrypto/MATLAB may be added
later only if its provenance and license permit; test success cannot depend on
MATLAB, MEX binaries, GitHub availability, or copied source.

## Development Lifecycle

The implementation ends at engineering acceptance.  A separately reviewed
plan may then use new synthetic roots and sacrificed data, with no confirmation
rows.  The development report must compare v6 against a v5 diagnostic replay
only by frozen aggregate metrics; it must not modify or relabel v5 evidence.

Possible next decisions after development are:

- continue to a fresh v6 qualification change;
- increase n to 4096 if the waterfall improves but a tail remains;
- open a multiplicatively repeated `(2,3)` mother-code change;
- open a GF(32)xGF(32) nonbinary multilevel change if q=1024 complexity is the
  limiting factor.

## Risks and Controls

- **Runtime:** n grows 16x.  Start at n=1024, workers=1, and benchmark one
  deterministic frame before authorizing a development batch.
- **Memory:** q=1024 messages are large.  Assert a calculated allocation cap
  before allocating and report peak estimated bytes.
- **False confidence:** tiny oracle parity proves implementation semantics,
  not p=.30 performance.  No qualification language is allowed here.
- **Dirty worktree:** acceptance hashes an explicit file manifest and checks
  frozen directories, rather than treating unrelated user files as v6 scope.

## Simpler Alternative

The lazier option is n=1024 with a purely random degree-2 matrix.  PEG adds
only one bounded constructor and directly targets short-cycle risk, so this
proposal keeps PEG but defers density evolution and repetition.

