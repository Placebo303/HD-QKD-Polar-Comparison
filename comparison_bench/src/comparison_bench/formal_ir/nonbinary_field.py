"""Pinned polynomial-basis GF(2^m) contract for ``nbldpc_formal_v1``."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from numbers import Integral
from typing import Any


METHOD = "nbldpc_formal_v1"
BACKEND_ID = "internal_polynomial_basis_gf2m"
BACKEND_VERSION = "1"
_POLYNOMIALS = {
    1: 0b11, 2: 0b111, 3: 0b1011, 4: 0b10011, 5: 0b100101,
    6: 0b1000011, 7: 0b10000011, 8: 0b100011101,
    9: 0b1000010001, 10: 0b10000001001,
}


@dataclass(frozen=True)
class FieldSpec:
    method: str
    backend_id: str
    backend_version: str
    q: int
    m: int
    primitive_polynomial: int
    basis: str
    symbol_encoding: str
    field_id: str


def _field_id(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


def get_field_spec(q: int) -> FieldSpec:
    """Return the immutable pinned specification; unsupported dimensions raise ValueError."""
    if isinstance(q, bool) or not isinstance(q, Integral):
        raise ValueError("unsupported GF(q) domain")
    q = int(q)
    if q < 2 or q > 1024 or q & (q - 1):
        raise ValueError("unsupported GF(q) domain")
    m = q.bit_length() - 1
    payload = {
        "method": METHOD, "backend_id": BACKEND_ID, "backend_version": BACKEND_VERSION,
        "q": q, "m": m, "primitive_polynomial": _POLYNOMIALS[m],
        "basis": "polynomial", "symbol_encoding": "unsigned_coefficient_integer_lsb_x_to_the_i",
    }
    return FieldSpec(**payload, field_id=_field_id(payload))


class GF2mField:
    """Small deterministic scalar arithmetic backend; symbols are integers in [0, q)."""

    def __init__(self, spec: FieldSpec):
        self.spec = spec
        self.q, self.m, self.primitive_polynomial = spec.q, spec.m, spec.primitive_polynomial
        self._exp, self._log = self._build_tables()

    @classmethod
    def create(cls, q: int) -> "GF2mField":
        return cls(get_field_spec(q))

    def _build_tables(self) -> tuple[tuple[int, ...], tuple[int, ...]]:
        exp: list[int] = []
        log = [-1] * self.q
        value = 1
        for index in range(self.q - 1):
            if value <= 0 or value >= self.q or log[value] != -1:
                raise ValueError("primitive polynomial does not generate a complete nonzero cycle")
            exp.append(value)
            log[value] = index
            value <<= 1
            if value & self.q:
                value ^= self.primitive_polynomial
            value &= self.q - 1
        if value != 1 or any(index < 0 for index in log[1:]):
            raise ValueError("primitive polynomial does not generate a complete nonzero cycle")
        return tuple(exp), tuple(log)

    def _symbol(self, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError("GF symbol outside pinned field domain")
        value = int(value)
        if not 0 <= value < self.q:
            raise ValueError("GF symbol outside pinned field domain")
        return value

    def add(self, left: int, right: int) -> int:
        return self._symbol(left) ^ self._symbol(right)

    sub = add

    def mul(self, left: int, right: int) -> int:
        left, right = self._symbol(left), self._symbol(right)
        if not left or not right:
            return 0
        return self._exp[(self._log[left] + self._log[right]) % (self.q - 1)]

    def inverse(self, value: int) -> int:
        value = self._symbol(value)
        if not value:
            raise ValueError("zero has no multiplicative inverse")
        return self._exp[(-self._log[value]) % (self.q - 1)]

    @property
    def nonzero_cycle(self) -> tuple[int, ...]:
        return self._exp


def _check_field(field: GF2mField) -> dict[str, bool]:
    q = field.q
    symbols = range(q)
    identity = all(field.add(value, 0) == value and field.mul(value, 1) == value and field.mul(value, 0) == 0 for value in symbols)
    inverses = all(field.mul(value, field.inverse(value)) == 1 for value in range(1, q))
    probes = tuple(dict.fromkeys((0, 1, q - 1, *field.nonzero_cycle[::max(1, (q - 1) // 15)])))
    distributive = all(field.mul(left, field.add(right, third)) == field.add(field.mul(left, right), field.mul(left, third)) for left in probes for right in probes for third in probes)
    bounds = all(0 <= field.add(left, right) < q and 0 <= field.mul(left, right) < q for left in probes for right in probes)
    return {"cycle": len(field.nonzero_cycle) == q - 1 and len(set(field.nonzero_cycle)) == q - 1, "identities": identity, "inverses": inverses, "distributivity": distributive, "symbol_bounds": bounds}


def preflight_nonbinary_field(q: int, *, expected_field_id: str | None = None) -> dict[str, Any]:
    """Read-only deterministic N0 preflight, returning only ``ok`` on every check."""
    try:
        spec = get_field_spec(q)
    except (KeyError, TypeError, ValueError):
        return {"status": "unsupported_domain", "method": METHOD, "requested_q": q, "backend": BACKEND_ID}
    try:
        field = GF2mField(spec)
        checks = _check_field(field)
        repeatable = get_field_spec(spec.q).field_id == spec.field_id
        if expected_field_id is not None and expected_field_id != spec.field_id:
            return {"status": "backend_unavailable", "method": METHOD, "requested_q": spec.q, "field": asdict(spec), "checks": checks, "reason": "expected_field_id_mismatch"}
        if not all(checks.values()) or not repeatable:
            return {"status": "backend_unavailable", "method": METHOD, "requested_q": spec.q, "field": asdict(spec), "checks": checks, "repeatable_field_id": repeatable, "reason": "arithmetic_or_metadata_check_failed"}
        return {"status": "ok", "method": METHOD, "requested_q": spec.q, "field": asdict(spec), "checks": checks, "repeatable_field_id": repeatable}
    except (ArithmeticError, TypeError, ValueError):
        return {"status": "backend_unavailable", "method": METHOD, "requested_q": spec.q, "backend": BACKEND_ID}
