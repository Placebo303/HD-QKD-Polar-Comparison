from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v19_channel as ch


def test_channel_constants():
    assert len(ch.V17_PER_PLANE_ERROR) == 10
    assert abs(ch.H_FULL_Q1024 - 0.549955) < 1e-9


def test_build_qsc_w():
    import numpy as np
    w = ch.build_qsc_w(16, 0.038)
    assert w.shape == (16,)
    assert abs(float(w.sum()) - 1.0) < 1e-12
    assert abs(float(w[0]) - 0.962) < 1e-12
    assert abs(float(w[1]) - 0.038 / 15.0) < 1e-12


def test_folded_entropy():
    h = ch.folded_entropy_bits(16)
    # V18-B2 folded q=16 channel entropy is ~0.3829.
    assert abs(h - 0.3829) < 2e-3


def test_f_plain_rate_060():
    h = ch.folded_entropy_bits(16)
    f = ch.f_plain_qary(rate=0.60, q=16, h_bits=h)
    assert abs(f - 4.1785) < 0.02


def test_channel_doc():
    doc = ch.build_channel_doc(q_small=16)
    assert doc["schema"] == "nbldpc_v19_channel_v1"
    assert len(doc["folded_w"]) == 16
    assert "folded_w" in doc


def test_lsb_public_capacity_bound():
    d0 = ch.lsb_public_capacity_f(public_lsb_planes=0)
    d1 = ch.lsb_public_capacity_f(public_lsb_planes=1)
    # Disclosing LSBs adds public bits, so capacity-ideal f is not below 1.0.
    assert d0["ideal_f_full"] >= 1.0 - 1e-9
    assert d1["public_bits_per_symbol"] == 1.0
    assert d1["residual_high_plane_entropy_bits_per_symbol"] < d0["residual_high_plane_entropy_bits_per_symbol"]


def test_build_high_plane_w():
    import numpy as np
    w0 = ch.build_high_plane_w(public_lsb_planes=0)
    assert w0.shape == (1024,)
    assert abs(float(w0.sum()) - 1.0) < 1e-9
    w1 = ch.build_high_plane_w(public_lsb_planes=1)
    assert w1.shape == (512,)
    assert abs(float(w1.sum()) - 1.0) < 1e-9
    assert ch.symbol_entropy_bits(w1) < ch.symbol_entropy_bits(w0)
