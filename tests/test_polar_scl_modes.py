from pathlib import Path

import numpy as np
import pytest

from src.reconciliation.cpp_scl_wrapper import PolarSCLDecoder
from src.reconciliation.real_polar_sc_rescue import polar_encode_non_systematic


@pytest.fixture(scope="module")
def decoder() -> PolarSCLDecoder:
    return PolarSCLDecoder(
        repo_root=Path(__file__).resolve().parents[1],
        force_rebuild=True,
        lib_stem="ca_scl_test_modes",
    )


def _encoded_llrs(u_rows: np.ndarray, magnitude: float = 12.0) -> np.ndarray:
    n_log = int(np.log2(u_rows.shape[1]))
    x_rows = np.stack(
        [polar_encode_non_systematic(row.astype(np.int8), n_log) for row in u_rows]
    )
    return np.where(x_rows == 0, magnitude, -magnitude).astype(np.float32)


def test_plain_scl_recovers_arbitrary_information_and_frozen_values(
    decoder: PolarSCLDecoder,
) -> None:
    n, k, frames = 16, 4, 3
    mask = np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1], dtype=np.uint8)
    frozen = np.array(
        [
            [1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0],
            [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0],
        ],
        dtype=np.uint8,
    )
    information = np.array([[1, 0, 1, 1], [0, 1, 1, 0], [1, 1, 0, 1]], dtype=np.uint8)
    u_rows = frozen.copy()
    u_rows[:, mask.astype(bool)] = information

    decoded = decoder.decode_batch_frozen_plain(
        n, k, frames, mask, frozen, _encoded_llrs(u_rows)
    )

    np.testing.assert_array_equal(decoded, information)


def test_plain_scl_uses_minimum_metric_while_legacy_ca_scl_can_misselect(
    decoder: PolarSCLDecoder,
) -> None:
    n, k = 8, 2
    mask = np.array([0, 0, 0, 0, 0, 0, 1, 1], dtype=np.uint8)
    frozen = np.array([[1, 0, 1, 1, 0, 1, 0, 0]], dtype=np.uint8)
    information = np.array([[1, 1]], dtype=np.uint8)
    u_rows = frozen.copy()
    u_rows[:, mask.astype(bool)] = information
    llrs = _encoded_llrs(u_rows, magnitude=10.0)

    plain = decoder.decode_batch_frozen_plain(n, k, 1, mask, frozen, llrs)
    legacy_ca = decoder.decode_batch_frozen(n, k, 1, mask, frozen, llrs)

    np.testing.assert_array_equal(plain, information)
    np.testing.assert_array_equal(legacy_ca, np.zeros_like(information))


def test_plain_scl_rejects_invalid_n_and_nonfinite_or_nonbinary_inputs(
    decoder: PolarSCLDecoder,
) -> None:
    with pytest.raises(ValueError, match="power of two"):
        decoder.decode_batch_frozen_plain(
            6, 1, 1, np.array([1, 0, 0, 0, 0, 0]), np.zeros((1, 6)), np.zeros((1, 6))
        )

    mask = np.array([0, 0, 0, 1], dtype=np.uint8)
    frozen = np.zeros((1, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="finite"):
        decoder.decode_batch_frozen_plain(4, 1, 1, mask, frozen, [[0.0, np.nan, 0.0, 0.0]])
    with pytest.raises(ValueError, match="mask must be binary"):
        decoder.decode_batch_frozen_plain(4, 1, 1, [0, 0, 0, 2], frozen, np.zeros((1, 4)))
    with pytest.raises(ValueError, match="frozen_values must be binary"):
        decoder.decode_batch_frozen_plain(4, 1, 1, mask, [[0, 0, 2, 0]], np.zeros((1, 4)))
