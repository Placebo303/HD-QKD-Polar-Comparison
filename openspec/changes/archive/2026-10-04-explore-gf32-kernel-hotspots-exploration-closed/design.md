# Minimal design

One new CLI, required fake-injected source_reader/decoder, production bindings only --execute; fixed source18 calls, two plain rounds plus stdlib cProfile round. Reconstruct exact cold inputs and require saved round-trip before accepting timings. Source prior/scoring/kernel untouched. Use pstats self/cumulative function table, additive small files, no framework/caching/hashes. Frozen caps and STOP retention per packet H1–H5; resource checkpoint and terminal file sizes explicitly bounded in interpretation.
