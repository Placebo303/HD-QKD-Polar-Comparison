# Synthetic iteration-cap diagnostic delta

## Requirement: default-preserving capped decoder

The soft-marginal synthetic block decoder SHALL retain `max_iter=300` when no optional override is supplied. A caller that explicitly supplies `max_iter=250` SHALL pass 250 to `decode_error_domain_posterior` and record the actual value in the returned row. The sampler, prior, graph, streak and exact-match semantics SHALL not change.

## Requirement: paired, bounded M3D arms

The M3D CLI SHALL use the two accepted M3-a graph artifacts, the M3-b 2M synthetic bundle and the exact selected 16 Stage-1 seed indices per arm in PACKET.md. It SHALL run cold m=200 Stage 1 only, with no Stage-2 call. It SHALL retain separate arm outputs, prior M3-b outcome/iteration/wall for each selected seed, new exact/undetected/wall/iterations, and the selection-stratum label. It SHALL refuse non-fresh or escaped output roots before inputs/decoder calls and SHALL never write old M3-b or protected roots.

## Requirement: claim ceiling

A completed M3D batch MAY describe only targeted Stage-1 call-cost changes for the selected synthetic seeds on two fixed graph instances. Because the sample deliberately balances known successes and failures, it SHALL NOT present a 240-frame FER or overall throughput estimate, real-data FER, a universal graph advantage, a deployable verification protocol, actual leakage/f or SKR. A later real test on the M3C 2M eval frames SHALL be labeled development reuse rather than independent validation.
