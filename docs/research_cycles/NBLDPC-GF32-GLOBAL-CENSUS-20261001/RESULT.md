# Fixed DV2 check-graph global census — result

**Track:** EXPLORE  
**Batch:** `f4a0ff0d-b538-4fed-bb2d-41c398daa3fb`  
**Execution status:** `COMPLETE` (one attempt, six graphs)  
**Main acceptance:** `RESOURCE_UNIT_CORRECTED_POST_HOC` after independent C4 `PASS_WITH_FINDING`  
**Machine root:** `workspace/gf32_global_f4a0ff0d/`

## Input and method

The single frozen command read only the six control-DV2 `H_constructor` matrices from the accepted degree-admitted source batch `a9352bc1-ae56-443b-ae93-9dcfa85d4229`. Its NPZ identity was batch UUID `a9352bc1-ae56-443b-ae93-9dcfa85d4229`, contract `NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md`, namespace `gf32-degree-admitted-v1`, and `graph_input_kind=admitted_source`. The separate constructor-lineage UUID is `a9a18abe-3547-4d16-aa50-1f7150182f31`.

The six selected source matrix indices for graph IDs 2026093901–2026093906 were 0, 2, 4, 6, 9, and 11. Graph 2026093905 used attempt `j=1` and construction seed `2560859716`; the other five used `j=0` and their graph ID as construction seed. The full source maps remain in `census.json`.

Each 52×128 matrix was reduced by nonzero support to a 52-check-node undirected multigraph: each source column is a retained edge ID, and parallel columns contribute multiplicity to adjacency. GF(32) coefficient values were not interpreted as real edge weights. The actual input shape, symbol range 0–31, degree-2 variable columns, and check profile (degree 4×4 and 5×48; 256 incidences) were rechecked. Rank 52 is reused from the accepted upstream A5 evidence. Connectedness was rechecked by BFS for all six supports.

For each graph the census recorded the complete normalized-Laplacian spectrum, `lambda2`, `lambda3-lambda2`, residual `max(abs(Lnorm @ U - U * lambda[None, :]))`, and all 51 Fiedler sweep cuts. The Fiedler order uses `u2/sqrt(d)`, with the preregistered sign and tie conventions. No graph was flagged `FIEDLER_DEGENERATE`.

| Graph ID | λ₂ | λ₃−λ₂ | φ_sweep | Best k / subset size | Cut | Volume S / complement |
|---|---:|---:|---:|---:|---:|---:|
| 2026093901 | 0.33070588646908367 | 0.06919357076642968 | 9/32 | 26 / 26 | 36 | 128 / 128 |
| 2026093902 | 0.3514695579621831 | 0.0249075480461583 | 8/31 | 27 / 27 | 32 | 132 / 124 |
| 2026093903 | 0.36330773595948074 | 0.02099221386583272 | 1/4 | 26 / 26 | 32 | 128 / 128 |
| 2026093904 | 0.35590454881279493 | 0.0343556002570381 | 35/127 | 26 / 26 | 35 | 127 / 129 |
| 2026093905 | 0.37988434088535816 | 0.026806186158516765 | 8/31 | 27 / 27 | 32 | 132 / 124 |
| 2026093906 | 0.34902588787693223 | 0.0269647835921229 | 35/127 | 26 / 26 | 35 | 129 / 127 |

The exact 51-cut sweep rows, adjacency matrices, degrees, complete spectra, source maps, and residuals are retained in `census.json`. This is a finite structural description of these six fixed supports. `phi_sweep` is an upper bound on global minimum conductance, not a certificate of the global minimum cut or expansion. The census says nothing about FER, decoder performance, minimum distance, causal benefit, real-channel behavior, or route choice.

## Resources and RSS correction

The single command exited successfully and completed all six graphs with no census STOP. Recorded wall time was 0.056596156 s. The final first-pass artifact-size checkpoint was 481,627 B; the final three files total 482,203 B. Both are below the 2 MiB cap. Decoder, graph-construction, label-search, and OSD calls were zero; new disclosure was zero.

The original run used the pre-fix `_rss_bytes()` implementation. On Linux/WSL it stored `resource.getrusage(RUSAGE_SELF).ru_maxrss` raw in fields labeled bytes, although Linux reports that high-water value in KiB. The pre-final maximum raw sample 30,128 therefore means 30,851,072 B. The final raw sample 33,072 means 33,865,728 B = 32.296875 MiB, below the 1 GiB cap. The original runtime guard compared KiB values to a byte limit and was therefore mis-scaled; this post-hoc conversion establishes the observed resource value for this one attempt, not that the original in-run guard enforced the byte cap correctly.

After the attempt, `_rss_bytes()` was minimally corrected to multiply Linux/WSL `ru_maxrss` by 1024; a focused mocked-unit test passed. The census was not rerun, and the original `manifest.json` and `census.json` remain unchanged, including their raw values and original byte labels. The independent C4 review and main-thread acceptance record the correction and its limit.
