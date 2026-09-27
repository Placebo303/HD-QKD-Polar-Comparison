import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2f_campaign as b2f,
)


def _decode(monkeypatch, *, max_iter=None):
    n, m = 8, 3
    bundle = {
        "g1": np.full((32, 1024), 1.0 / 32),
        "g2": np.full((32, 32, 1024), 1.0 / 32),
    }
    observed = {}

    def sample(_bundle, size, _rng):
        assert size == n
        return np.arange(n), np.zeros(n, dtype=np.int64), np.zeros(
            n, dtype=np.int64)

    monkeypatch.setattr(b2f.s2c, "empirical_triple_sampler", sample)
    monkeypatch.setattr(
        b2f.peg, "sparse_to_dense",
        lambda triples, size, rows, field: np.zeros((rows, size),
                                                     dtype=np.uint8))
    monkeypatch.setattr(
        b2f.fftqspa, "syndrome_of",
        lambda field, dense, x: [0] * len(x))

    def decode_kernel(field, y, dense, syndrome, prior, iterations):
        observed["max_iter"] = iterations
        return {
            "status": "success",
            "iterations": 7,
            "reconstruction_ok": True,
            "x_hat": np.zeros(n, dtype=np.int64),
        }

    monkeypatch.setattr(b2f.v28, "decode_error_domain_posterior",
                        decode_kernel)
    kwargs = {} if max_iter is None else {"max_iter": max_iter}
    result = b2f.decode_block_marginal(
        {"triples": [(0, 0, 1)], "n": n, "m": m},
        2026096401, bundle, n, m, **kwargs)
    return result, observed


def test_omitted_max_iter_keeps_frozen_300_default(monkeypatch):
    result, observed = _decode(monkeypatch)

    assert observed["max_iter"] == 300
    assert result["max_iter"] == 300
    assert result["exact_match"] is True


def test_explicit_250_reaches_kernel_and_is_returned(monkeypatch):
    result, observed = _decode(monkeypatch, max_iter=250)

    assert observed["max_iter"] == 250
    assert result["max_iter"] == 250
    assert result["exact_match"] is True


@pytest.mark.parametrize("value", [0, -1, True, 250.0])
def test_invalid_max_iter_refuses(value):
    with pytest.raises(b2f.Refusal):
        b2f.decode_block_marginal(
            {"triples": [], "n": 8, "m": 3}, 2026096401, {}, 8, 3,
            max_iter=value)
