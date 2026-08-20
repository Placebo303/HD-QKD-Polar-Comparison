"""V28R finite GF(32) engineering.

The V28R contract is intentionally narrow: deterministic degree-two finite
matrices, the accepted V10 FFT-QSPA decoder, and a Bob-only empirical
L1->L2 posterior call.  It does not run DE, FER, qualification, or promotion.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import nonbinary_codebook as cb
from . import nonbinary_v10_fftqspa as qspa
from .nonbinary_field import GF2mField, get_field_spec

Q, N, M1, M2_MAX = 32, 1024, 6, 202
SOURCE_M2 = {"1M": 194, "1p5M": 200, "2M": 202}
SOURCE_H_TOTAL = {
    "1M": 0.024280547 + 0.776757278,
    "1p5M": 0.025199497 + 0.800366555,
    "2M": 0.025662049 + 0.806900673,
}
SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
SOURCE_DELAY_PS = {"1M": -50, "1p5M": 50, "2M": 50}
SOURCE_N_PAIRS = {"1M": 512000, "1p5M": 708352, "2M": 933120}
SEED_L1, SEED_L2 = 2026082001, 2026082002
TAG_BITS, DEFAULT_MAX_ITER = 64, 30
P_NOISELESS, P_CONTROLLED = 1e-3, 0.2
TERMINAL_READY = "engineering_ready_for_retrospective_gate"

__all__ = [
    "Q", "N", "M1", "M2_MAX", "SOURCE_M2", "SOURCE_H_TOTAL", "SOURCE_IDS",
    "SEED_L1", "SEED_L2", "TAG_BITS", "frozen_v28_config", "build_matrices",
    "layer_matrix", "compute_syndrome", "decode_layer", "decode_error_domain_posterior",
    "decode_two_layer", "decode_two_layer_sequential_empirical", "tag64", "leakage_bits",
    "run_v28_evidence", "verify_v28",
]


def frozen_v28_config() -> dict[str, Any]:
    return {
        "schema": "nbldpc_v28r_frozen_config_v2", "q": Q, "n": N, "m1": M1,
        "m2_max": M2_MAX,
        "sources": {
            label: {"source_id": SOURCE_IDS[label], "delay_used_ps": SOURCE_DELAY_PS[label],
                    "n_pairs": SOURCE_N_PAIRS[label], "m2": m2, "h_total": SOURCE_H_TOTAL[label]}
            for label, m2 in SOURCE_M2.items()
        },
        "seed_l1": SEED_L1, "seed_l2": SEED_L2,
        "topology": "v28r_degree2_ordered_pair_graph",
        "l1_pair_order": "lexicographic_15_pairs_repeated_68_then_(0,1),(0,2),(1,3),(4,5)",
        "l2_pair_order": "simple_circulant_offsets_k1_to_k5_k_then_i_dedup_then_opposite_matching_prefix",
        "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
        "coefficient_call": "_coefficient(q, seed, variable_index, endpoint_slot)",
        "tag_bits": TAG_BITS, "tag_method": "sha256(bytes(x1)||bytes(x2))[:8]",
        "field_id": get_field_spec(Q).field_id,
        "factorization": "F03_natural_MSB_to_LSB_GF32_plus_GF32",
        "posterior_semantics": "V26_train_P(U_i|B,source,delay,U_<i)_centered_on_Bob",
        "sequential_semantics": "Bob-only_L1_then_L2_conditioned_on_returned_x1_hat",
        "p_noiseless": P_NOISELESS, "p_controlled": P_CONTROLLED,
        "max_iter": DEFAULT_MAX_ITER,
        "forbidden": ["DE", "MC-DE", "FER", "qualification", "promotion", "holdout", "raw_ttbin"],
    }


# --------------------------- deterministic pair graphs -------------------
def _l1_pairs(m: int, n: int) -> list[tuple[int, int]]:
    if (m, n) == (6, 1024):
        lex = [(i, j) for i in range(6) for j in range(i + 1, 6)]
        return lex * 68 + [(0, 1), (0, 2), (1, 3), (4, 5)]
    if m < 2:
        raise ValueError("degree-two graph requires m >= 2")
    return [tuple(sorted((j % m, (j + 1) % m))) for j in range(n)]


def _l2_pairs(m: int, n: int) -> list[tuple[int, int]]:
    if m < 2 or n < 1:
        raise ValueError("invalid L2 graph dimensions")
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for k in range(1, 6):
        for i in range(m):
            pair = tuple(sorted((i, (i + k) % m)))
            if pair[0] != pair[1] and pair not in seen:
                seen.add(pair)
                pairs.append(pair)
    if n <= len(pairs):
        return pairs[:n]
    rem = n - len(pairs)
    matching = [(i, i + m // 2) for i in range(m // 2)]
    if rem > len(matching):
        raise ValueError("opposite matching cannot supply requested columns")
    return pairs + matching[:rem]


def _pairs(layer: str, m: int, n: int) -> list[tuple[int, int]]:
    return _l1_pairs(m, n) if layer == "L1" else _l2_pairs(m, n)


def _build_pair_matrix(q: int, seed: int, m: int, n: int,
                       pairs: Sequence[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    if len(pairs) != n:
        raise ValueError(f"pair list length {len(pairs)} != n={n}")
    rows = [[0] * n for _ in range(m)]
    for j, (a, b) in enumerate(pairs):
        if not (0 <= a < b < m):
            raise ValueError(f"invalid pair {(a, b)} at column {j}")
        rows[a][j] = cb._coefficient(q, seed, j, 0)
        rows[b][j] = cb._coefficient(q, seed, j, 1)
    return tuple(tuple(row) for row in rows)


def build_matrices(config: Mapping[str, Any] | None = None) -> tuple[tuple, dict[str, tuple]]:
    """Return shared L1 and an independently-built L2 matrix per source."""
    config = config or frozen_v28_config()
    q, n, m1 = int(config["q"]), int(config["n"]), int(config["m1"])
    h1 = _build_pair_matrix(q, int(config["seed_l1"]), m1, n, _pairs("L1", m1, n))
    h2 = {}
    for source, sinfo in config["sources"].items():
        m2 = int(sinfo["m2"])
        h2[source] = _build_pair_matrix(q, int(config["seed_l2"]), m2, n, _pairs("L2", m2, n))
    return h1, h2


def layer_matrix(h2_by_source: Mapping[str, tuple], source: str,
                 config: Mapping[str, Any] | None = None) -> tuple:
    """Select a source-specific L2 matrix; row-prefix input is rejected."""
    if not isinstance(h2_by_source, Mapping):
        raise TypeError("V28R requires source-specific L2 matrices; row-prefix is forbidden")
    return tuple(h2_by_source[source])


# ----------------------------- decoder bindings ---------------------------
def compute_syndrome(field: GF2mField, matrix: Any, symbols: Any) -> list[int]:
    return qspa.syndrome_of(field, matrix, symbols)


def decode_layer(field: GF2mField, y: Sequence[int], matrix: Any, s_x: Sequence[int],
                 p: float, max_iter: int = DEFAULT_MAX_ITER) -> dict[str, Any]:
    """QSC compatibility wrapper; production V28R uses empirical posteriors."""
    return qspa.decode_error_domain(y, matrix, s_x, p, field, int(max_iter))


def decode_error_domain_posterior(field: GF2mField, y: Sequence[int], matrix: Any,
                                  s_x: Sequence[int], prior_error: Any,
                                  max_iter: int = DEFAULT_MAX_ITER, *, streak: int = 3,
                                  rss_watcher: Any = None) -> dict[str, Any]:
    """Use V10 FFT-QSPA with per-variable ``P(E_i)``; fail closed on syndrome."""
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2 or not isinstance(field, GF2mField):
        raise ValueError("matrix/field invalid")
    m, n, q = dense.shape[0], dense.shape[1], field.q
    yv, sv = [int(v) for v in y], [int(v) for v in s_x]
    if len(yv) != n or len(sv) != m:
        raise ValueError("y/s_x dimensions do not match matrix")
    prior = np.asarray(prior_error, dtype=np.float64)
    if prior.shape != (n, q):
        raise ValueError(f"prior_error must have shape {(n, q)}")
    for v in yv + sv:
        field.mul(1, v)
    h_y = qspa.syndrome_of(field, dense, yv)
    _, add = qspa._tables(field)
    s_e = [int(add[a, b]) for a, b in zip(sv, h_y)]
    result = qspa.decode_fftqspa(prior, dense, s_e, field, int(max_iter),
                                 streak=int(streak), rss_watcher=rss_watcher)
    if result.get("e_hat") is None:
        result.update({"x_hat": None, "syndrome_ok": False, "reconstruction_ok": False,
                       "prior_shape": list(prior.shape)})
        return result
    xhat = [int(add[a, b]) for a, b in zip(yv, result["e_hat"])]
    syndrome_ok = qspa.syndrome_of(field, dense, xhat) == sv
    result.update({"x_hat": xhat, "syndrome_ok": bool(syndrome_ok),
                   "reconstruction_ok": bool(result.get("status") == qspa.STATUS_SUCCESS and syndrome_ok),
                   "prior_shape": list(prior.shape)})
    return result


def _center_rows(field: GF2mField, rows: Any, bob: Sequence[int]) -> np.ndarray:
    arr, bv = np.asarray(rows, dtype=np.float64), np.asarray(bob, dtype=np.int64)
    if arr.shape != (len(bv), field.q):
        raise ValueError("posterior rows must have shape (n,q)")
    _, add = qspa._tables(field)
    out = np.empty_like(arr)
    for i, y in enumerate(bv.tolist()):
        out[i] = arr[i, add[int(y), np.arange(field.q)]]
    return out


def _join_f03(x1: Sequence[int], x2: Sequence[int]) -> np.ndarray:
    a, b = np.asarray(x1, dtype=np.int64), np.asarray(x2, dtype=np.int64)
    if a.shape != b.shape:
        raise ValueError("F03 layer lengths differ")
    return ((a & 31) << 5) | (b & 31)


def decode_two_layer_sequential_empirical(field: GF2mField, b_obs: Sequence[int],
                                          y1: Sequence[int], y2: Sequence[int],
                                          s1: Sequence[int], s2: Sequence[int], source: str,
                                          adapter: Any, *, config: Mapping[str, Any] | None = None,
                                          max_iter: int | None = None) -> dict[str, Any]:
    """Bob-only adapter calls: L1(B), decode, then L2(B, returned x1_hat)."""
    config = config or frozen_v28_config()
    h1, h2map = build_matrices(config)
    h2 = layer_matrix(h2map, source, config)
    n = int(config["n"])
    b, a1, a2 = (np.asarray(v, dtype=np.int64) for v in (b_obs, y1, y2))
    if any(v.shape != (n,) for v in (b, a1, a2)):
        raise ValueError("Bob/source arrays must have length n")
    it = int(max_iter if max_iter is not None else config.get("max_iter", DEFAULT_MAX_ITER))
    rows1 = adapter.posterior_rows("L1", b)
    r1 = decode_error_domain_posterior(field, a1.tolist(), h1, s1,
                                       _center_rows(field, rows1, a1), it)
    if r1.get("status") != qspa.STATUS_SUCCESS or not r1.get("reconstruction_ok"):
        r2 = {"status": "not_run", "reason": "L1_failed_or_syndrome_check_failed",
              "x_hat": None, "reconstruction_ok": False, "syndrome_ok": False}
        return {"layer_order": ["L1", "L2"], "L1": r1, "L2": r2,
                "x1_hat": r1.get("x_hat"), "x2_hat": None,
                "alice_truth_used": False, "l2_conditioning": "not_run"}
    x1_hat = r1.get("x_hat")
    if x1_hat is None:
        raise RuntimeError("successful L1 returned no x1_hat")
    # This argument is deliberately the actual decoder return, not Alice data.
    rows2 = adapter.posterior_rows("L2", b, x1_hat)
    r2 = decode_error_domain_posterior(field, a2.tolist(), h2, s2,
                                       _center_rows(field, rows2, a2), it)
    return {"layer_order": ["L1", "L2"], "L1": r1, "L2": r2,
            "x1_hat": x1_hat, "x2_hat": r2.get("x_hat"),
            "alice_truth_used": False, "l2_conditioning": "returned_L1_x1_hat"}


def decode_two_layer(field: GF2mField, y1: Sequence[int], y2: Sequence[int],
                     s1: Sequence[int], s2: Sequence[int], source: str,
                     p1: float = P_NOISELESS, p2: float = P_NOISELESS,
                     max_iter: int = DEFAULT_MAX_ITER,
                     config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Sequential QSC helper retained for compatibility, not production evidence."""
    config = config or frozen_v28_config()
    h1, h2map = build_matrices(config)
    r1 = decode_layer(field, y1, h1, s1, p1, max_iter)
    if r1.get("status") != qspa.STATUS_SUCCESS or not r1.get("reconstruction_ok"):
        r2 = {"status": "not_run", "x_hat": None, "reconstruction_ok": False}
    else:
        r2 = decode_layer(field, y2, layer_matrix(h2map, source, config), s2, p2, max_iter)
    return {"layer_order": ["L1", "L2"], "L1": r1, "L2": r2,
            "x1_hat": r1.get("x_hat"), "x2_hat": r2.get("x_hat"), "alice_truth_used": False}


# ----------------------------- evidence + verifier ------------------------
def tag64(x1_hat: Sequence[int] | None, x2_hat: Sequence[int] | None) -> str:
    payload = (bytes(int(v) & 0xFF for v in x1_hat) if x1_hat is not None else b"")
    payload += (bytes(int(v) & 0xFF for v in x2_hat) if x2_hat is not None else b"")
    return hashlib.sha256(payload).digest()[:8].hex()


def leakage_bits(m_total: int, q: int = Q, tag_bits: int = TAG_BITS) -> int:
    return int(m_total) * int(round(math.log2(q))) + int(tag_bits)


def _gen_block(seed: int, n: int, q: int) -> list[int]:
    r = random.Random(seed)
    return [r.randrange(q) for _ in range(n)]


def _inject_errors(x: Sequence[int], positions: Sequence[int], q: int, seed: int) -> list[int]:
    y, r = list(map(int, x)), random.Random(seed)
    for p in positions:
        y[int(p)] ^= r.randrange(1, q)  # GF(2^5) additive operation
    return y


def _representative_positions(matrix: Any) -> list[int]:
    d, n = np.asarray(matrix, dtype=np.int64), np.asarray(matrix).shape[1]
    return [p for p in dict.fromkeys([0, n // 4, n // 2, 3 * n // 4, n - 1])
            if np.count_nonzero(d[:, p]) > 0][:4]


class _SyntheticAdapter:
    def __init__(self, source: str):
        self.source, self.source_label, self.delay_used_ps = source, source, None
        self.calls: list[tuple[str, np.ndarray, Any]] = []

    def posterior_rows(self, lid: str, b: np.ndarray, u1: Sequence[int] | None = None) -> np.ndarray:
        b = np.asarray(b, dtype=np.int64)
        self.calls.append((lid, b.copy(), None if u1 is None else list(u1)))
        out = np.full((len(b), 32), 1e-12, dtype=np.float64)
        symbols = ((b >> 5) & 31) if lid == "L1" else (b & 31)
        out[np.arange(len(b)), symbols] = 1.0
        return out / out.sum(axis=1, keepdims=True)


class _RecordingAdapter:
    def __init__(self, base: Any):
        self.base, self.calls = base, []
        for k in ("source", "source_label", "delay_used_ps", "n_pairs", "fact_id"):
            if hasattr(base, k):
                setattr(self, k, getattr(base, k))

    def posterior_rows(self, lid: str, b: np.ndarray, u1: Sequence[int] | None = None) -> np.ndarray:
        self.calls.append((lid, np.asarray(b, dtype=np.int64).copy(), None if u1 is None else list(map(int, u1))))
        return self.base.posterior_rows(lid, b, u1)


def _load_adapters(config: Mapping[str, Any]) -> dict[str, Any]:
    from .nonbinary_v26_channel import build_adapter, load_channel_counts
    counts = load_channel_counts()
    return {label: build_adapter(counts, fact_id="F03", source=sinfo["source_id"])
            for label, sinfo in config["sources"].items() if "source_id" in sinfo}


def _matrix_summary(config: Mapping[str, Any]) -> dict[str, Any]:
    n, m1 = int(config["n"]), int(config["m1"])
    l1 = _pairs("L1", m1, n)
    l1_degrees = Counter(v for p in l1 for v in p)
    result = {"L1": {"shape": [m1, n], "edges": 2 * len(l1), "unique_pairs": len(set(l1)),
                      "row_degree_hist": {str(k): v for k, v in Counter(l1_degrees.values()).items()},
                      "column_degree_hist": {"2": n}}}
    result["L2"] = {}
    for label, si in config["sources"].items():
        p = _pairs("L2", int(si["m2"]), n)
        degrees = Counter(v for x in p for v in x)
        result["L2"][label] = {"shape": [int(si["m2"]), n], "edges": 2 * len(p),
                                "unique_pairs": len(set(p)),
                                "row_degree_hist": {str(k): v for k, v in Counter(degrees.values()).items()},
                                "column_degree_hist": {"2": n}}
    return result


def _expected_manifest(config: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Build the canonical manifest from config plus persisted evidence.

    The writer and verifier intentionally share this schema so a manifest field
    cannot silently drift from the evidence contract.
    """
    sources = []
    for label, item in evidence["sources"].items():
        no = item["noiseless"]
        ce = item["controlled"]
        sources.append({
            "label": label,
            "source_id": item.get("source_id"),
            "delay_used_ps": item.get("delay_used_ps"),
            "n_pairs": item.get("n_pairs"),
            "m1": item["m1"], "m2": item["m2"], "m_total": item["m_total"],
            "leak_bits": item["leak_bits"], "f": item["f"],
            "noiseless_L1_ok": no["L1_ok"], "noiseless_L2_ok": no["L2_ok"],
            "noiseless_L1_status": no["L1_status"], "noiseless_L2_status": no["L2_status"],
            "controlled_fail_closed_only": ce["fail_closed_only"],
            "controlled_L1_status": ce["L1_status"], "controlled_L2_status": ce["L2_status"],
            "controlled_L1_reconstruction_ok": ce["L1_reconstruction_ok"],
            "controlled_L2_reconstruction_ok": ce["L2_reconstruction_ok"],
            "tag64_hex": item["tag64_hex"],
        })
    return {
        "schema": "nbldpc_v28r_run_manifest_v2",
        "terminal_state": evidence["terminal_state"],
        "run_role": "v28r_candidate_engineering_smoke",
        "matrix_contract": _matrix_summary(config),
        "topology": config["topology"],
        "coefficient_call": config["coefficient_call"],
        "posterior_semantics": config["posterior_semantics"],
        "sequential_semantics": config["sequential_semantics"],
        "tag_method": config["tag_method"],
        "posterior_source": evidence.get("posterior_source"),
        "holdout_read": evidence["holdout_read"],
        "raw_ttbin_read": evidence["raw_ttbin_read"],
        "alice_truth_in_decoder": evidence.get("alice_truth_in_decoder"),
        "sources": sources,
    }


def run_v28_evidence(root: str | Path, config: Mapping[str, Any] | None = None,
                     adapters: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run synthetic/noiseless plus fixed controlled smoke only."""
    root, config = Path(root), (config or frozen_v28_config())
    root.mkdir(parents=True, exist_ok=True)
    field = GF2mField.create(int(config["q"]))
    h1, h2map = build_matrices(config)
    used_default_empirical = adapters is None
    if adapters is None:
        loaded = _load_adapters(config) if all("source_id" in x for x in config["sources"].values()) else {}
        adapters = {label: loaded.get(label, _SyntheticAdapter(label)) for label in config["sources"]}
    (root / "v28_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    out = {}
    for idx, (source, si) in enumerate(config["sources"].items()):
        adapter = adapters[source]
        if "source_id" in si and getattr(adapter, "source", si["source_id"]) != si["source_id"]:
            raise ValueError(f"{source}: source binding mismatch")
        if "source_id" in si and getattr(adapter, "delay_used_ps", si.get("delay_used_ps")) != si.get("delay_used_ps"):
            raise ValueError(f"{source}: delay binding mismatch")
        h2 = layer_matrix(h2map, source, config)
        x1, x2 = _gen_block(SEED_L1 * 1000 + idx, int(config["n"]), int(config["q"])), _gen_block(SEED_L2 * 1000 + idx, int(config["n"]), int(config["q"]))
        s1, s2 = compute_syndrome(field, h1, x1), compute_syndrome(field, h2, x2)
        rnl = decode_two_layer_sequential_empirical(field, _join_f03(x1, x2), x1, x2, s1, s2, source, adapter, config=config)
        p1, p2 = _representative_positions(h1), _representative_positions(h2)
        y1, y2 = _inject_errors(x1, p1, int(config["q"]), 777 + idx), _inject_errors(x2, p2, int(config["q"]), 877 + idx)
        rce = decode_two_layer_sequential_empirical(field, _join_f03(y1, y2), y1, y2, s1, s2, source, adapter, config=config)
        mtotal = int(config["m1"]) + int(si["m2"])
        leak = leakage_bits(mtotal, int(config["q"]))
        f = leak / (int(config["n"]) * float(si["h_total"]))
        out[source] = {
            "source_id": si.get("source_id"), "delay_used_ps": si.get("delay_used_ps"), "n_pairs": si.get("n_pairs"),
            "m1": int(config["m1"]), "m2": int(si["m2"]), "m_total": mtotal, "leak_bits": leak, "f": f,
            "noiseless": {"L1_status": rnl["L1"].get("status"), "L2_status": rnl["L2"].get("status"),
                          "L1_ok": rnl["L1"].get("x_hat") == x1 and bool(rnl["L1"].get("reconstruction_ok")),
                          "L2_ok": rnl["L2"].get("x_hat") == x2 and bool(rnl["L2"].get("reconstruction_ok")),
                          "layer_order": rnl["layer_order"], "l2_conditioning": rnl.get("l2_conditioning")},
            "controlled": {"fail_closed_only": True, "positions_l1": p1, "positions_l2": p2,
                           "L1_status": rce["L1"].get("status"), "L2_status": rce["L2"].get("status"),
                           "L1_reconstruction_ok": bool(rce["L1"].get("reconstruction_ok")),
                           "L2_reconstruction_ok": bool(rce["L2"].get("reconstruction_ok")),
                           "L2_not_run_after_L1_failure": rce["L1"].get("status") != qspa.STATUS_SUCCESS and rce["L2"].get("status") == "not_run"},
            "layer_order": ["L1", "L2"], "tag64_hex": tag64(rnl.get("x1_hat"), rnl.get("x2_hat")),
            "tag_bits": tag64(rnl.get("x1_hat"), rnl.get("x2_hat")), "x1": x1, "x2": x2,
            "x1_hat": rnl.get("x1_hat"), "x2_hat": rnl.get("x2_hat"), "s1": s1, "s2": s2,
        }
    ready = all(x["noiseless"]["L1_ok"] and x["noiseless"]["L2_ok"] for x in out.values())
    terminal = TERMINAL_READY if ready else "engineering_not_ready"
    posterior_source = (
        "V26_ChannelAdapter_train_model"
        if used_default_empirical and all("source_id" in x for x in config["sources"].values())
        else ("synthetic_adapter" if used_default_empirical else "explicit_adapter")
    )
    evidence = {"schema": "nbldpc_v28r_evidence_v2", "terminal_state": terminal,
                "posterior_source": posterior_source,
                "holdout_read": False, "raw_ttbin_read": False, "alice_truth_in_decoder": False, "sources": out}
    gate = {"status": terminal, "detail": "V28R engineering smoke only; controlled stage is fail-closed diagnostics; no FER/qualification/promotion"}
    (root / "v28_evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (root / "gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    manifest = _expected_manifest(config, evidence)
    (root / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"status": terminal, "evidence_root": str(root), "gate": gate, "sources": out}


def _contract_problems(matrix: Any, layer: str, m: int, n: int, q: int, seed: int) -> list[str]:
    d, ps = np.asarray(matrix, dtype=np.int64), _pairs("L1" if layer == "L1" else "L2", m, n)
    if d.shape != (m, n):
        return [f"{layer}: shape mismatch"]
    problems = []
    for j, pair in enumerate(ps):
        if tuple(np.flatnonzero(d[:, j]).tolist()) != pair:
            problems.append(f"{layer}: pair mismatch at {j}")
        for slot, row in enumerate(pair):
            if int(d[row, j]) != cb._coefficient(q, seed, j, slot):
                problems.append(f"{layer}: coefficient mismatch at {j}/{slot}")
    if Counter(int(np.count_nonzero(d[:, j])) for j in range(n)) != Counter({2: n}):
        problems.append(f"{layer}: column degree != 2")
    expected_degrees = Counter(v for p in ps for v in p)
    expected_row_hist = Counter(expected_degrees.values())
    if Counter(int(np.count_nonzero(d[i, :])) for i in range(m)) != expected_row_hist:
        problems.append(f"{layer}: row degree histogram mismatch")
    frozen_unique = (layer == "L1" and (m, n) == (6, 1024)) or (layer == "L2" and n == 1024)
    expected_unique = 15 if layer == "L1" and (m, n) == (6, 1024) else n
    if frozen_unique and len(set(ps)) != expected_unique:
        problems.append(f"{layer}: pair uniqueness mismatch")
    return problems


def _canonical_config_problems(config: Mapping[str, Any]) -> list[str]:
    """Check that a source-bound config is the frozen V28R config, not a new run."""
    if not all("source_id" in info for info in config.get("sources", {}).values()):
        return []
    frozen = frozen_v28_config()
    problems = []
    for key in (
        "q", "n", "m1", "m2_max", "seed_l1", "seed_l2", "field_id",
        "topology", "coefficient_derivation", "coefficient_call", "tag_method",
        "l1_pair_order", "l2_pair_order", "factorization",
    ):
        if config.get(key) != frozen.get(key):
            problems.append(f"canonical config mismatch: {key}")
    if config.get("sources") != frozen.get("sources"):
        problems.append("canonical config mismatch: sources")
    return problems


def verify_v28(evidence_root: str | Path) -> dict[str, Any]:
    """Independent structural + empirical replay verifier; persists its JSON."""
    root = Path(evidence_root)
    config = json.loads((root / "v28_config.json").read_text(encoding="utf-8"))
    evidence = json.loads((root / "v28_evidence.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    gate = json.loads((root / "gate.json").read_text(encoding="utf-8"))
    canonical = all("source_id" in info for info in config.get("sources", {}).values())
    problems = _canonical_config_problems(config)
    field, q, n = GF2mField.create(int(config["q"])), int(config["q"]), int(config["n"])
    h1, h2map = build_matrices(config)
    problems.extend(_contract_problems(h1, "L1", int(config["m1"]), n, q, int(config["seed_l1"])))
    if cb.gf_rank(h1, field) != int(config["m1"]):
        problems.append("L1 rank mismatch")
    for src, si in config["sources"].items():
        h2 = layer_matrix(h2map, src, config)
        problems.extend(_contract_problems(h2, "L2", int(si["m2"]), n, q, int(config["seed_l2"])))
        if cb.gf_rank(h2, field) != int(si["m2"]):
            problems.append(f"{src}: rank mismatch")
    if config.get("tag_method") != "sha256(bytes(x1)||bytes(x2))[:8]":
        problems.append("tag contract mismatch")
    if evidence.get("holdout_read") is not False or evidence.get("raw_ttbin_read") is not False:
        problems.append("raw/holdout boundary violated")
    try:
        expected_manifest = _expected_manifest(config, evidence)
        if manifest != expected_manifest:
            problems.append("persisted manifest does not exactly match expected manifest")
    except (KeyError, TypeError, ValueError) as exc:
        problems.append(f"manifest cannot be reconstructed: {exc}")
    if gate.get("status") != evidence.get("terminal_state") or manifest.get("terminal_state") != evidence.get("terminal_state"):
        problems.append("gate/manifest/evidence terminal mismatch")
    if canonical and evidence.get("posterior_source") != "V26_ChannelAdapter_train_model":
        problems.append("canonical evidence is not marked as V26 empirical posterior")
    if canonical:
        try:
            adapters = _load_adapters(config)
        except (FileNotFoundError, KeyError) as exc:
            problems.append(f"canonical V26 adapter unavailable: {exc}")
            adapters = {}
    else:
        try:
            loaded = _load_adapters(config)
            adapters = {src: loaded.get(src, _SyntheticAdapter(src)) for src in config["sources"]}
        except (FileNotFoundError, KeyError):
            adapters = {src: _SyntheticAdapter(src) for src in config["sources"]}
    manifest_by_src = {v.get("label"): v for v in manifest.get("sources", [])}
    for src, si in config["sources"].items():
        s = evidence.get("sources", {}).get(src)
        if not s:
            problems.append(f"missing source {src}"); continue
        if s.get("source_id") != si.get("source_id") or s.get("delay_used_ps") != si.get("delay_used_ps"):
            problems.append(f"{src}: source/delay binding mismatch")
        leak = leakage_bits(int(config["m1"]) + int(si["m2"]), q)
        f = leak / (n * float(si["h_total"]))
        if s.get("leak_bits") != leak or abs(float(s.get("f", 0)) - f) > 1e-12 or f >= 1.3:
            problems.append(f"{src}: leakage mismatch")
        if tag64(s.get("x1_hat"), s.get("x2_hat")) != s.get("tag64_hex", s.get("tag_bits")):
            problems.append(f"{src}: tag mismatch")
        x1, x2 = s.get("x1"), s.get("x2")
        if not isinstance(x1, list) or not isinstance(x2, list) or len(x1) != n or len(x2) != n:
            problems.append(f"{src}: synthetic block mismatch"); continue
        h2 = layer_matrix(h2map, src, config)
        if compute_syndrome(field, h1, x1) != s.get("s1") or compute_syndrome(field, h2, x2) != s.get("s2"):
            problems.append(f"{src}: syndrome evidence mismatch")
        c = s.get("controlled", {})
        if c.get("fail_closed_only") is not True:
            problems.append(f"{src}: controlled semantics mismatch")
        if c.get("L1_status") != qspa.STATUS_SUCCESS and c.get("L2_status") != "not_run":
            problems.append(f"{src}: L2 was run after failed L1")
        if src not in adapters:
            problems.append(f"{src}: no bound posterior adapter available")
            continue
        adapter = adapters[src]
        if canonical and (getattr(adapter, "source", None) != si.get("source_id") or
                          getattr(adapter, "delay_used_ps", None) != si.get("delay_used_ps")):
            problems.append(f"{src}: adapter source/delay binding mismatch")
        rec = _RecordingAdapter(adapter)
        replay = decode_two_layer_sequential_empirical(field, _join_f03(x1, x2), x1, x2, s["s1"], s["s2"], src, rec, config=config)
        if replay["L1"].get("status") != qspa.STATUS_SUCCESS or replay["L2"].get("status") != qspa.STATUS_SUCCESS:
            problems.append(f"{src}: empirical replay failed")
        if len(rec.calls) != 2 or rec.calls[0][0] != "L1" or rec.calls[1][0] != "L2":
            problems.append(f"{src}: posterior call order mismatch")
        elif rec.calls[1][2] != replay.get("x1_hat"):
            problems.append(f"{src}: L2 did not receive returned x1_hat")
        mi = manifest_by_src.get(src)
        if mi is None or mi.get("source_id") != si.get("source_id") or mi.get("delay_used_ps") != si.get("delay_used_ps"):
            problems.append(f"{src}: manifest binding mismatch")
    ok = not problems and evidence.get("terminal_state") == TERMINAL_READY
    result = {"schema": "nbldpc_v28r_readonly_verify_v2", "ok": bool(ok), "problems": problems,
              "recomputed_terminal": TERMINAL_READY if ok else "engineering_not_ready",
              "persisted_terminal": evidence.get("terminal_state"), "matrix_rebuilt": True,
              "sequential_empirical_replayed": True, "holdout_read": False, "raw_ttbin_read": False}
    (root / "readonly_verify.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
