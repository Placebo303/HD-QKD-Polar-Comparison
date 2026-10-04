# Route A Bit-Plane Interface (2026-04-14)

This note fixes the Route A bit-plane Polar-IR interface used by the current correctness-formal replay line.

## Symbol To Bit-Plane Mapping

- Input symbols are integer bin indices in `[0, dimension - 1]`.
- `dimension` must be a power of two.
- `bits_per_symbol = log2(dimension)`.
- `layer_idx = 0` is the most-significant bit plane.
- `layer_idx = bits_per_symbol - 1` is the least-significant bit plane.
- The implemented extraction rule is:

```text
bit(layer_idx) = (symbol >> (bits_per_symbol - 1 - layer_idx)) & 1
```

The implementation source is `bit_layer_from_symbols()` in `tools/_security_round_common.py`.

## Replay Interface

Route A replay is block-based inside each bit plane. Each replay block is identified by `point_id`, `loss_db`, `dimension`, `bin_width_ps`, `layer_id`, and `block_index`.

For correctness formalization, every replayed block invokes the same verification interface:

- `verification_protocol_id = uhv1_per_block`
- `verification_family = universal_hash`
- `verification_scope = per_block`
- `verification_seed_policy = deterministic_public_from_point_id_layer_id_block_index`
- `verification_public_message_rule = tag_bits_revealed`
- `verification_tag_bits = 32` by default

Legacy CRC fields remain for comparison only. They are not the formal `epsilon_EC_bound` source.

## Leakage And Correctness Fields

Block-level leakage is organized as:

```text
total_leak_ec_bits = syndrome_bits_revealed + verification_bits_used_actual
```

Point-level verification leakage is:

```text
lambda_ver_bits_actual = sum(verification_bits_used_actual over invoked blocks)
```

With fixed tag bits:

```text
lambda_ver_bits_actual = verification_invoked_block_count * verification_tag_bits
```

The empirical replay audit line is:

```text
epsilon_EC_empirical = undetected_error_count_empirical / verification_invoked_block_count
```

The proof-side correctness bound line is:

```text
epsilon_EC_bound = min(1, verification_invoked_block_count * 2^(-verification_tag_bits))
```

Only `epsilon_EC_bound` enters the composable correctness budget fields `eps_cor_total` and `eps_cor_from_epsilon_EC`. `epsilon_EC_empirical` and `decoder_fail_rate_oracle` are audit quantities only.

## Result Line Boundary

Safe claim:

```text
Route A correctness-side verification interface formalized under current calibrated actual-IR finite-key shadow.
```

Unsafe claim for the current implementation:

```text
strict Zhong 2015 / full Niu 2016 proof instantiation completed
```

The current line still lacks the full protocol-observable interface required to claim strict Zhong/Niu coverage. Route C and non-BSC Route B-lite changes are outside this interface document.
