# Method Notes

## polar_existing

Reads frozen Polar output files and maps available leakage, raw error, and success fields into the comparison CSV. A successful read is reported as `method_status=ok`; fields absent from the source remain `NaN` and are listed in `notes`.

## cascade_lite

This path runs an internal simplified Cascade-lite baseline for synthetic benchmarking. It maps symbols to bits, performs deterministic multi-pass block parity comparison with recursive bisection on mismatched blocks, flips located Bob bits, verifies frames, and reports leakage as disclosed parity bits plus verification bits. It is not a full Cascade transcript implementation.

## layered_ldpc_lite

The current executable baseline uses `ldpc.BpOsdDecoder` for synthetic benchmarking when available. It splits q-ary symbols into independent bit planes, discloses fixed sparse syndromes, decodes syndrome deltas per plane, verifies frames, and reports real frame counters and leakage as syndrome bits plus verification bits. Failed experimental fallback paths must not be marked `ok`.

## qldpc_reference

The current implementation runs a synthetic/offline q-ary syndrome reference approximation and reports it as `method_status=reference`. It may also read a configured reference result file; only a file that explicitly declares `method_status=ok` is mapped to `ok`. The offline approximation is not a full qLDPC end-to-end decoder.
