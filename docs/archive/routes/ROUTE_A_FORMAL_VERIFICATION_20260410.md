# Route A Formal Verification Note (2026-04-10)

Formal correctness v1 uses:
- verification_protocol_id = `uhv1_per_block`
- verification_family = `universal_hash`
- verification_scope = `per_block`
- verification_seed_policy = `deterministic_public_from_point_id_layer_id_block_index`
- verification_public_message_rule = `tag_bits_revealed`

Current field split:
- `verification_bits_used_actual` and `lambda_ver_bits_actual` are the universal-hash verification leakage
- `verification_bits_used_actual_legacy_crc` and `lambda_ver_bits_legacy_crc` remain legacy compare fields
- `epsilon_EC_empirical` is the empirical undetected-error rate from replay
- `epsilon_EC_bound` is the universal-hash union bound used for correctness budgeting
- `decoder_fail_rate_oracle` is kept separate and is not used as `epsilon_EC`

Current claim boundary:
- correctness-side verification accounting is formalized for Route A
- only `epsilon_EC_bound` enters `eps_cor_total`
- this remains a correctness-interface formalization, not a strict full Zhong 2015 or Niu 2016 proof instantiation
