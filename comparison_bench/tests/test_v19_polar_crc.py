import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.v19_polar_crc import build_crc_info_bits, choose_crc16, crc_check


def test_crc_check_matches_helper():
    rng = np.random.default_rng(1)
    for k in (32, 64, 128):
        payload = [int(x) for x in rng.integers(0, 2, size=k - 16)]
        crc = choose_crc16(payload)
        assert crc_check(payload + crc) is True


def test_build_crc_info_bits():
    rng = np.random.default_rng(2)
    k = 100
    payload = rng.integers(0, 2, size=k - 16, dtype=np.int8)
    info = build_crc_info_bits(payload, k)
    assert info.shape == (k,)
    assert crc_check(info) is True
    assert np.array_equal(info[:k - 16], payload)
