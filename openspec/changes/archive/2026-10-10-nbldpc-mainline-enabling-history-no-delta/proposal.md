# NB-LDPC mainline enabling

Reduce repeated check-node transformations in the formal 1024-symbol NB-LDPC path so a power-sufficient real-calibrated comparison can fit a practical time budget, while preserving messages, disclosure and decoding decisions.

Initial scope is implementation and focused mathematical equivalence only, not a decoder experiment. User authorized parallel P3 on 2026-10-05. No decoder/DE/raw/benchmark execution, scientific performance acceptance, publication or push is granted by this initial contract. Later decoder experiments require target-effect/MDE before their packet and applicable execution gates.

One change and one append-only route log own the enabling route. Start with the existing FFT-QSPA check-node operations; do not adopt a different numerical reduction, fastmath or decoder algorithm. GF32 microprobe histories remain stopped.
