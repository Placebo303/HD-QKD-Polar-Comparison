# Design

Freeze saved C[a,b] paths, axes, alphabet and source roles before calculation. Resolve full-symbol versus u1/u2 reduction and historical budget applicability. Empirical unsmoothed counts are a descriptive diagnostic, not a deployment prior or fresh holdout.

For each complete Alice bit order compute H_k=H(A_bit_k|B, previous Alice bits), information-density moments V_k and H(A|B); check sum H_k=H(A|B). Distinguish marginal BSC entropy, H(single Alice bit|full Bob) and chain entropy. Independently recompute with grouped-entropy differences, without calling the primary routine.

Finite-length scenarios expose N, epsilon allocation, approximation, clipping and rounding in bits/block. Conditional channels are not generic BSCs; theoretical dispersion is not a measured LDPC/Polar gap. Joint variance is not an independent sum of plane variances. Correct-prefix analysis does not measure error propagation. Do not reuse 1104 bits as an absolute budget across N or sources.

H_A_bits=N*H(A); kept_bits=H_A_bits-L_EC_bits; Y_bits=kept_bits-tag_bits-kept_bits*p_fail; f_expected=(L_EC_bits+tag_bits+kept_bits*p_fail)/(N*H(A|B)). Disclosure and failure values are explicit assumptions until measured on appropriate disjoint data. P1 establishes no empirical f/FER/security result.

New code belongs in comparison_bench, outputs in a fresh workspace root. No baseline/output edits, historical body rewriting, checksums, transactions or generic runner framework. Code, focused math tests and compact evidence form one scoped milestone commit.

After P1 arithmetic acceptance, implementation-only P2 builds conditional bit-prior tables and a soft-syndrome adapter boundary. It invokes no decoder and establishes no performance. Tables keep Bob's complete natural symbol as the column key; Alice bit labels use the declared natural/Gray bijection and complete order. Unobserved Bob/prefix combinations return an explicitly flagged uninformative prior rather than invented certainty. The receiver's prior-query API has no Alice truth argument.
