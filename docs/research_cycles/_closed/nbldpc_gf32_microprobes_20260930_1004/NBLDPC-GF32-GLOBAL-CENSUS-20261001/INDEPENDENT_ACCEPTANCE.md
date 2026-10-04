# Independent C4 review and main acceptance

**Batch UUID:** `f4a0ff0d-b538-4fed-bb2d-41c398daa3fb`  
**Track:** EXPLORE  
**Independent C4 verdict:** `PASS_WITH_FINDING`  
**Main acceptance:** `RESOURCE_UNIT_CORRECTED_POST_HOC`

Earlier packet text that listed C4 or main acceptance as pending described the pre-execution state and is superseded by this completed artifact review and main decision.

The independent reviewer matched the six selected source matrices and their constructor lineage, the check-graph edge endpoints and multiplicities, all degree vectors, the full normalized-Laplacian spectra, residuals, all 51 cuts per graph, Fiedler ordering, and the source maps against the actual census artifacts. The reviewer found no discrepancy in the structural outputs. Rank-52 provenance was reused from the accepted upstream source review; this census independently recomputed connectedness by BFS. No graph was constructed and no decoder was run.

The verified `lambda2` values span 0.33070588646908367–0.37988434088535816. The per-graph sweep conductances are exactly `9/32`, `8/31`, `1/4`, `35/127`, `8/31`, and `35/127`. No `FIEDLER_DEGENERATE` flag was present; the recorded eigensystem residuals were within the frozen `1e-10` tolerance.

**Finding — RSS units.** The original run's sampler returned Linux/WSL `ru_maxrss` without conversion, while the result fields labeled the values as bytes. Linux reports `ru_maxrss` in KiB. The saved raw pre-final maximum `30128` is therefore 30,851,072 B; the saved final value `33072` is 33,865,728 B (32.296875 MiB). The corrected observed high-water value is below the frozen 1 GiB resource limit. However, the original in-run guard compared KiB to a byte limit and did not enforce the stated byte cap with correct units. Main accepts this finding as a post-hoc resource-unit correction for the completed one-shot observation, not as proof that the original guard was correctly scaled.

The code's default RSS conversion was subsequently fixed and its conversion was checked with a mocked raw value of 33,072 KiB. No census rerun, repair, continuation, source change, or output rewrite followed. The original `manifest.json` and `census.json` remain untouched; the original log checkpoint is preserved above, with this adjudication appended at EOF.

Main accepts only the six-graph `DESCRIPTIVE_STRUCTURE_ONLY` census with this resource correction. It does not establish a decoder or graph-construction benefit, minimum distance, FER, causal mechanism, real-channel performance, or route decision. No new execution authority is created.
