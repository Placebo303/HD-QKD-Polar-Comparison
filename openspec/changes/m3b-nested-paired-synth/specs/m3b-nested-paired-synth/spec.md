# M3-b paired synthetic diagnostic

## Requirements

1. The adapter SHALL use only the accepted M3-a arm-1/arm-2 graph artifacts, map them to the corresponding P1 R1/R2 construction seed labels, and enforce the frozen structural pins before the first decoder call.
2. The adapter SHALL use the existing P1 Stage-1 and cold-rescue decoder semantics with the frozen 2M synthetic channel, 240 seeds `2026096401..2026096640`, stream `o1_blk:{seed}`, max_iter 300 and exact-match success. It SHALL NOT open `.ttbin` or real/private data.
3. Each new arm SHALL write to a fresh additive M3-b root and identify its graph as standalone A200+8 loaded twice from one stored M3-a artifact. Historical P1 A208 labels and a false claim of two new PEG constructions SHALL NOT appear as claims about the new graph. Existing P1 default execution and results SHALL remain unchanged.
4. The result SHALL separate Stage-1 failures, rescue attempts, final failures, undetected, per-arm modeled disclosure and wall/RSS. Added 40-bit rescue disclosure SHALL be charged on every attempt, not just a successful rescue. It SHALL compare matched frame IDs to the existing P1 arm without pooling instances or inferring a real-data, route-closing, SKR or publication claim.
5. Production decode SHALL require both explicit execution flags and the recorded Pre-EXECUTE PASS. Fake tests SHALL inject fake constructors/decoders; they SHALL NOT enter the production decoder path.
