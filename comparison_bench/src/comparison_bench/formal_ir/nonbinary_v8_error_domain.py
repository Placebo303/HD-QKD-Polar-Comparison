"""V8 error-domain syndrome and reconstruction helpers (additive reference layer).

Contract (frozen in the V8 change spec):

- Alice holds ``x``, Bob holds ``y``, Alice publishes the syndrome ``s = H*x``.
- The error is ``e = x + y`` (characteristic two: addition == XOR == subtraction).
- Bob derives ``d = s + H*y = H*x + H*y = H*(x+y) = H*e`` and decodes ``e``
  under a QSC error prior centered at zero; then ``x_hat = y + e_hat``.

This module is pure stdlib + numpy and imports ONLY ``GF2mField`` from the
accepted field tables (``nonbinary_field``).  It never imports or calls any
V1-V7 FFT/FWHT/check-update/decoder module and never receives a production
runner.  All entry points fail closed: invalid symbols, invalid matrices,
wrong lengths and out-of-domain values raise ``ValueError``.
"""
from __future__ import annotations

from numbers import Integral
from typing import Any, Sequence

from .nonbinary_field import GF2mField

__all__ = [
    "validate_symbols",
    "validate_matrix",
    "mul_sum_syndrome",
    "error_vector",
    "error_domain_syndrome",
    "reconstruct_x",
    "error_domain_equivalence",
]


def validate_symbols(symbols: Any, q: int, *, expected: int | None = None) -> tuple[int, ...]:
    """Fail-closed symbol validation: returns a tuple of in-domain ints.

    Rejects bools, non-Integral values, symbols outside ``[0, q)`` and (when
    ``expected`` is given) vectors of the wrong length.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2:
        raise ValueError("unsupported GF(q) domain")
    q = int(q)
    try:
        values = tuple(symbols)
    except TypeError as exc:
        raise ValueError("symbols must be an iterable") from exc
    if expected is not None and len(values) != int(expected):
        raise ValueError("symbols have wrong length")
    if any(isinstance(value, bool) or not isinstance(value, Integral) or not 0 <= int(value) < q
           for value in values):
        raise ValueError("symbol outside pinned field domain")
    return tuple(int(value) for value in values)


def validate_matrix(matrix: Any, n: int) -> tuple[tuple[int, ...], ...]:
    """Fail-closed rectangular matrix validation with exactly ``n`` columns.

    Rejects non-iterable rows, rows with non-Integral or bool entries, rows of
    the wrong width and a non-rectangular (jagged) collection.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("matrix width must be a positive integer")
    n = int(n)
    try:
        rows = tuple(tuple(row) for row in matrix)
    except TypeError as exc:
        raise ValueError("matrix must be rectangular") from exc
    if not rows:
        raise ValueError("matrix must have at least one row")
    if any(len(row) != n for row in rows):
        raise ValueError("matrix width does not match n")
    if any(isinstance(value, bool) or not isinstance(value, Integral) for row in rows for value in row):
        raise ValueError("matrix coefficients must be integers")
    return tuple(tuple(int(value) for value in row) for row in rows)


def mul_sum_syndrome(field: GF2mField, matrix: Any, symbols: Any) -> tuple[int, ...]:
    """``H*x`` by direct field add/mul over the pinned field, row order kept.

    Coefficient domain is enforced fail-closed by the field's own mul
    validation (out-of-domain coefficients raise ``ValueError``).
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    vector = validate_symbols(symbols, field.q)
    rows = validate_matrix(matrix, len(vector))
    result: list[int] = []
    for row in rows:
        total = 0
        for coefficient, symbol in zip(row, vector):
            total = field.add(total, field.mul(coefficient, symbol))
        result.append(total)
    return tuple(result)


def error_vector(field: GF2mField, x: Any, y: Any) -> tuple[int, ...]:
    """``e = x + y`` elementwise (characteristic-two addition)."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    left = validate_symbols(x, field.q)
    right = validate_symbols(y, field.q, expected=len(left))
    return tuple(field.add(a, b) for a, b in zip(left, right))


def error_domain_syndrome(syndrome: Any, hy: Any) -> tuple[int, ...]:
    """``d = s + H*y`` elementwise (characteristic-two addition).

    Both operands are plain tuples of non-negative integers of equal length;
    the XOR of two in-domain values stays closed in ``[0, 2^m)`` so no field
    argument is needed here.
    """
    def _check(values: Any, name: str) -> tuple[int, ...]:
        try:
            out = tuple(values)
        except TypeError as exc:
            raise ValueError(f"{name} must be an iterable") from exc
        if any(isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0
               for value in out):
            raise ValueError(f"{name} entries must be non-negative integers")
        return tuple(int(value) for value in out)

    left = _check(syndrome, "syndrome")
    right = _check(hy, "hy")
    if len(left) != len(right):
        raise ValueError("syndrome and H*y have different lengths")
    return tuple(a ^ b for a, b in zip(left, right))


def reconstruct_x(y: Any, e_hat: Any) -> tuple[int, ...]:
    """``x_hat = y + e_hat`` elementwise; raises on length mismatch."""
    def _check(values: Any, name: str) -> tuple[int, ...]:
        try:
            out = tuple(values)
        except TypeError as exc:
            raise ValueError(f"{name} must be an iterable") from exc
        if any(isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0
               for value in out):
            raise ValueError(f"{name} entries must be non-negative integers")
        return tuple(int(value) for value in out)

    left = _check(y, "y")
    right = _check(e_hat, "e_hat")
    if len(left) != len(right):
        raise ValueError("y and e_hat have different lengths")
    return tuple(a ^ b for a, b in zip(left, right))


def error_domain_equivalence(field: GF2mField, matrix: Any, syndrome: Any,
                             x: Any, y: Any) -> dict:
    """Verify the frozen error-domain algebra identity on one (x, y, H, s).

    Returns::

        {
          "direct_syndrome": H*(x+y),          # mul_sum_syndrome(H, error_vector)
          "split_syndrome":  H*x + H*y,        # elementwise XOR of the two syndromes
          "derived_d":       s + H*y,          # Bob's derived error syndrome
          "equivalent":      direct == split == derived,
        }
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    left = validate_symbols(x, field.q)
    right = validate_symbols(y, field.q, expected=len(left))
    s = validate_symbols(syndrome, field.q)
    rows = validate_matrix(matrix, len(left))
    hx = mul_sum_syndrome(field, rows, left)
    hy = mul_sum_syndrome(field, rows, right)
    if len(s) != len(hx):
        raise ValueError("syndrome length does not match matrix row count")
    direct = mul_sum_syndrome(field, rows, error_vector(field, left, right))
    split = tuple(field.add(a, b) for a, b in zip(hx, hy))
    derived = tuple(field.add(a, b) for a, b in zip(s, hy))
    return {
        "direct_syndrome": direct,
        "split_syndrome": split,
        "derived_d": derived,
        "equivalent": direct == split == derived,
    }
