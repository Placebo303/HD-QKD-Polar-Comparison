# Decoder-free GF32 train-source mapping — result

2026-09-30 · DECIDE · batch UUID `6f821d0b-71e3-46c1-ae84-2da374edbcc2`  
Terminal: **`DESCRIPTIVE_MAPPING_COMPLETE`**, independently reviewed and
accepted by the main thread within the limits below.

## Execution and input gates

The frozen one-shot command completed on the historical V25 2026-01-21
documented-train count arrays. Provenance and NPZ header admission both passed;
the three logical members were `(1024,1024)`, float64, C-order. All count values
were finite, nonnegative integers and each source total matched its frozen
train-pair count. The mapping used axis 0 = Alice, axis 1 = Bob, natural F03
`E1=((A>>5)&31) XOR ((B>>5)&31)`. Sources were processed separately; no pooled
statistics, fitted prior, frame list, or conditional array was exported.

The execution took `0.197906 s` within the 60-second cap and peak RSS was
`46,235,648` bytes within the 1-GiB cap. The exact command and gate/resource
record are in `workspace/gf32_source_map_6f821d0b/manifest.json`.

## Per-source results

Only `E1` bins 1, 3, 7, 15 and 31 were nonzero in all three sources; every
other nonzero-symbol bin was zero. `TV_B` is the error-count-weighted mean of
the per-Bob-column nonzero-symbol TV defined in the frozen packet.

| Source | N | n_zero / n_nonzero; p_zero | E1 counts `(0,1,3,7,15,31)` | H(E1) | H(E1\|B) | I(E1;B) | TV, nonzero E1 | TV_B | Error-bearing B columns; `<5 / <20` errors |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1M | 307,200 | 304965 / 2235; 0.992724609375 | (304965, 1130, 591, 294, 151, 69) | 0.0752830656242 | 0.0242805468187 | 0.0510025188055 | 0.840095258714 | 0.967741935484 | 41; 10 / 10 |
| 1p5M | 424,960 | 421657 / 3303; 0.9922275037650602 | (421657, 1734, 831, 430, 196, 112) | 0.0794635706064 | 0.0251994968779 | 0.0542640737286 | 0.838709677419 | 0.967741935484 | 43; 12 / 12 |
| 2M | 559,872 | 555444 / 4428; 0.9920910493827161 | (555444, 2295, 1126, 557, 304, 146) | 0.0808048495574 | 0.0256620487969 | 0.0551428007606 | 0.838709677419 | 0.967741935484 | 51; 20 / 20 |

Each source had 1,024 observed Bob columns. The reviewer found singleton
nonzero-`E1` support in every error-bearing Bob column (41/41, 43/43, and
51/51, respectively), consistent with the observed `TV_B=30/31`. These are
empirical properties of the stored aggregates; the low counts make the
conditional distributions sparse.

## Independent review and interpretation

The independent Pre-RESULT reviewer recomputed each source from the authorized
count inputs, row by row over Alice and all Bob columns. All 32 bins, source
totals and frozen formulas matched the operator artifact to maximum absolute
difference `<=1e-12`. The reviewer also confirmed the provenance roles, paths,
split ratios, input profiles, resource limits and three-file output root.
Twenty-six fake-only tests passed during the implementation review. No decoder,
scientific retry or repair was used.

The accepted conclusion is limited to source-specific descriptive statistics
for these historical documented-train aggregates. The provenance is
`DOCUMENTED_TRAIN_ROLE_CONSISTENT`: saved records do not preserve frame
boundaries or bind the historical writer command/version to the NPZ bytes, so
the raw split was not independently reconstructed. The empirical, sparse
statistics establish no sampling confidence, stationarity, causal mechanism,
qualified prior, or transfer to the 2026-01-23 Model-F CAL domain. They are not
FER, SKR, decoder-performance, mechanism-gain, qualification, publication, or
route-decision results.

The user's grant “可以继续下一步” authorized this one bounded mapping after
the required reviews and is consumed. The main thread noted a possible future
question—testing fixed-graph labels at a source-faithful, distinguishable
synthetic operating point—but that suggestion is not accepted by this result,
not frozen, and not authorized for execution. A successor requires a new packet
and explicit authorization.

Artifacts: `workspace/gf32_source_map_6f821d0b/manifest.json`,
`source_summary.json`, and append-only `RESULT_LOG.md`. No commit, push, or merge.
