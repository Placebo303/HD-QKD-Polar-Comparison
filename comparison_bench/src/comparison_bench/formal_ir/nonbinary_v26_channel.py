"""V26 layer-conditional posterior channel adapter.

Builds the per-layer posterior-message population
``P(U_i | B, source, delay, U_<i)`` from V25 train ``N_ab``
(``channel_counts.npz``) / C04 source-delta assumption, for the two frozen
V26 architectures A01 (F01 natural: GF512 + GF2) and A02 (F03 natural:
GF32 + GF32).  Used as the ``posterior`` channel population injection into the
V26 MC-DE extension (``nonbinary_v26_mcde``).

Semantics (V26 design section 1):
- ``(A,B)`` sampled from the train joint ``P(A,B)`` = N_ab / total.
- L1: ``P(U1=u|B) = sum_{a: L1(a)=u} P(A=a|B)``.
- L2: ``P(U2=u|B,U1) = sum_{a: L1(a)=U1,L2(a)=u} P(A=a|B) / sum_{a: L1(a)=U1} P(A=a|B)``.
- posterior recentered on the true layer symbol (additive/GF-XOR model, so the
  true symbol maps to index 0), matching the MC-DE error-domain convention.
- Three sources kept independent; +-1 directions preserved; 1M/1p5M/2M
  populations never merged.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .nonbinary_v25_gate import (Q as V25_Q, FACTORIZATIONS, F_LAYER_ORDER,
                                 conditional_entropy_bits, split_label)

__all__ = [
    "V26_LAYERS", "V26_FACT", "WIDTH", "Q", "SOURCES_ORDER", "SOURCE_METADATA",
    "load_channel_counts", "ChannelAdapter", "build_adapter", "adapter_entropy_bits",
]


#: V26 frozen architectures -> layer id order (MSB first), matching V25 F01/F03.
V26_FACT = {"A01": "F01", "A02": "F03"}
V26_LAYERS = {"A01": ["L1", "L2"], "A02": ["L1", "L2"]}
#: symbol domain size per (fact, layer) in the frozen factorization.
Q = {"A01": {"L1": 512, "L2": 2}, "A02": {"L1": 32, "L2": 32}}
#: layer width in bits = log2(q) (used for the per-bit rate construction).
WIDTH = {"A01": {"L1": 9, "L2": 1}, "A02": {"L1": 5, "L2": 5}}
#: frozen source order (matches V25 SOURCES dict order).
SOURCES_ORDER = [
    "type2_1M_20260121_184040",
    "type2_1p5M_20260121_183806",
    "type2_2M_20260121_183657",
]

#: Frozen per-source metadata: human label, sidecar ``delay_used_ps`` (the
#: *existing* delay configuration, never re-estimated; V25 freeze decision
#: 2026-08-18 records -50/+50/+50) and the pairs.parquet row count used as the
#: operating N (V25 design section 6).  Explicitly records the source <-> delay
#: mapping that otherwise only lives implicitly inside the source id string.
SOURCE_METADATA = {
    "type2_1M_20260121_184040": {
        "label": "1M", "delay_used_ps": -50, "n_pairs": 512000,
    },
    "type2_1p5M_20260121_183806": {
        "label": "1p5M", "delay_used_ps": 50, "n_pairs": 708352,
    },
    "type2_2M_20260121_183657": {
        "label": "2M", "delay_used_ps": 50, "n_pairs": 933120,
    },
}

#: default channel_counts.npz (V25 run_04; additive reference root).
DEFAULT_COUNTS = Path(
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
)
#: fallback roots to locate a V25 channel_counts.npz if run_04 absent.
_FALLBACK_ROOTS = [
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818",
]


def _n_ab_keys():
    # channel_counts.npz keys are f"{sid}_N_ab_train_N_ab_train"
    return [f"{sid}_N_ab_train_N_ab_train" for sid in SOURCES_ORDER]


def load_channel_counts(path: str | Path | None = None) -> dict[str, np.ndarray]:
    """Load per-source train ``N_ab`` from a V25 channel_counts.npz.

    Falls back to any existing run root's channel_counts.npz if ``path`` is not
    given.  Raises FileNotFoundError if no file can be located.
    """
    if path is None:
        cand = DEFAULT_COUNTS
        if not Path(cand).exists():
            for root in _FALLBACK_ROOTS:
                r = Path(root)
                if not r.exists():
                    continue
                for sub in sorted(r.iterdir()):
                    if sub.is_dir() and (sub / "channel_counts.npz").exists():
                        cand = sub / "channel_counts.npz"
                        break
                if Path(cand).exists():
                    break
        path = cand
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"channel_counts.npz not found: {path}")
    d = np.load(path)
    out: dict[str, np.ndarray] = {}
    for sid in SOURCES_ORDER:
        key = next((k for k in d.files if k.startswith(sid + "_N_ab_train")), None)
        if key is None:
            raise KeyError(f"no train N_ab for source {sid} in {path}: keys={list(d.files)}")
        out[sid] = np.asarray(d[key], dtype=np.float64)
    return out


def P_A_given_B(N: np.ndarray) -> np.ndarray:
    """P(A=a|B=b) = N_ab[a,b]/colsum(b); column-normalized over a."""
    col = N.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(N, col, out=np.zeros_like(N), where=col > 0)
    return P


class ChannelAdapter:
    """Per-source, per-layer conditional posterior model.

    Holds the precomputed per-``B`` (and per-``B,U1`` for L2) posterior rows so
    that MC-DE can cheaply draw ``n_samples`` centered channel rows.
    """

    def __init__(self, *, fact_id: str, source: str, N_ab: np.ndarray):
        self.fact_id = fact_id
        self.source = source
        md = SOURCE_METADATA.get(source)
        self.source_label = md["label"] if md else source
        self.delay_used_ps = int(md["delay_used_ps"]) if md else None
        self.n_pairs = int(md["n_pairs"]) if md else None
        self.N_ab = np.asarray(N_ab, dtype=np.float64)
        self.P_ab = self.N_ab / self.N_ab.sum()
        self.P_a_gb = P_A_given_B(self.N_ab)  # (1024, 1024) row=label A, col=B
        self._build_layer_tables()
        # marginal P(B) and P(B,U1) for entropy
        self.p_b = self.N_ab.sum(axis=0) / self.N_ab.sum()
        self._build_entropy()

    # ------------------------------------------------------------------ #
    def _layers_for_a(self) -> dict[str, np.ndarray]:
        """Layer value per label a (0..1023) for this factorization (natural)."""
        aa = np.arange(V25_Q, dtype=np.int64)
        # split_label default labeling is L01_natural when labeling param unused
        return split_label(aa, self.fact_id, "L01_natural")

    def _build_layer_tables(self) -> None:
        lid0 = F_LAYER_ORDER[self.fact_id][0]
        # L1 domain size = q of first layer
        q1 = Q_by_fact_layer(self.fact_id, lid0)
        layers = self._layers_for_a()
        u1 = layers[lid0].astype(np.int64)  # (1024,)
        # P(U1|B): rows L1-domain, cols B -> (q1, 1024)
        # accumulate by adding P(A=a|B) over a grouped by u1
        self.p_u1_gb = np.zeros((q1, V25_Q), dtype=np.float64)
        for a in range(V25_Q):
            self.p_u1_gb[u1[a], :] += self.P_a_gb[a, :]
        # layer 2 (if any)
        order = F_LAYER_ORDER[self.fact_id]
        if len(order) >= 2:
            lid1 = order[1]
            q2 = Q_by_fact_layer(self.fact_id, lid1)
            u2 = layers[lid1].astype(np.int64)
            # joint P(U1,U2|B) -> (q1, q2, B) via full joint P(A|B) accumulation
            self.pjoint_gb = np.zeros((q1, q2, V25_Q), dtype=np.float64)
            for a in range(V25_Q):
                self.pjoint_gb[u1[a], u2[a], :] += self.P_a_gb[a, :]
            # marginal P(U1|B) already = p_u1_gb
            self.q1, self.q2 = q1, q2
        else:
            self.pjoint_gb = None
            self.q2 = None
        self.layers = layers
        self.lids = order
        self.q1 = q1

    # ------------------------------------------------------------------ #
    def _build_entropy(self) -> None:
        """Compute H(U_i|B,U_<i) in bits/symbol from the adapter model."""
        H = {}
        p_b = self.p_b
        # L1: H(U1|B)
        m1 = self.p_u1_gb  # (q1, 1024)
        h1 = 0.0
        for b in range(V25_Q):
            if p_b[b] <= 0:
                continue
            col = m1[:, b]
            col = col[col > 0]
            if col.size:
                h1 += p_b[b] * float(-np.sum(col * np.log2(col)))
        H["L1"] = float(h1)
        if self.pjoint_gb is not None:
            # P(B,U1) marginal
            pu1_b = self.p_u1_gb  # (q1,1024) P(U1|B)
            # P(B,U1) = pu1_b[u1,b] * P(B=b)
            h2 = 0.0
            for b in range(V25_Q):
                if p_b[b] <= 0:
                    continue
                pb = p_b[b]
                for u1 in range(self.q1):
                    pbu1 = pu1_b[u1, b] * pb
                    if pbu1 <= 0:
                        continue
                    norm = pu1_b[u1, b]
                    row = self.pjoint_gb[u1, :, b] / norm
                    row = row[row > 0]
                    if row.size:
                        h2 += pbu1 * float(-np.sum(row * np.log2(row)))
            H["L2"] = float(h2)
        self.H_bits = H
        self.total_H = float(sum(H.values()))

    # ------------------------------------------------------------------ #
    def layer_posterior_gb(self, lid: str) -> np.ndarray:
        """Non-centered posterior table over B.

        L1 -> (q1, 1024) P(U1|B).  L2 -> (q1, q2, 1024) P(U2|B,U1).
        """
        if lid == "L1":
            return self.p_u1_gb
        if lid == "L2":
            return self.pjoint_gb
        raise KeyError(lid)

    def posterior_rows(self, lid: str, b_arr: np.ndarray,
                       u1_arr: np.ndarray | None = None) -> np.ndarray:
        """Return non-centered posterior rows ``(n, q_layer)`` for sampled true
        (B) and (for L2) true U1."""
        if lid == "L1":
            return self.p_u1_gb.T[b_arr]  # (n, q1)
        # L2: index [u1, :, b] normalized by P(U1|B) -> conditional P(U2|B,U1)
        rows = np.empty((b_arr.shape[0], self.q2), dtype=np.float64)
        for i in range(b_arr.shape[0]):
            norm = self.p_u1_gb[u1_arr[i], b_arr[i]]
            rows[i] = self.pjoint_gb[u1_arr[i], :, b_arr[i]] / norm if norm > 0 else 0.0
            if norm <= 0:
                rows[i, 0] = 1.0
        return rows

    def make_channel_sampler(self, lid: str):
        """Return a ``sampler(n, rng) -> (n, q_layer)`` callable that samples
        ``(A,B)`` from the train joint and returns the true-symbol-centered
        posterior population for this layer.  Used as the MC-DE channel."""
        u1 = self.layers["L1"].astype(np.int64)
        u2 = self.layers["L2"].astype(np.int64) if self.lids[-1] == "L2" else None
        Pflat = self.P_ab.ravel()
        q_layer = Q_by_fact_layer(self.fact_id, lid)
        p_u1_gb = self.p_u1_gb
        pjoint = self.pjoint_gb
        idx512 = np.arange(1024, dtype=np.int64)

        def sampler(n: int, rng: np.random.Generator):
            pick = rng.choice(Pflat.size, size=n, p=Pflat)
            a = (pick // 1024).astype(np.int64)
            b = (pick % 1024).astype(np.int64)
            u1_true = u1[a]
            if lid == "L1":
                rows = p_u1_gb.T[b]  # (n, q1)
                true_val = u1_true
            else:
                rows = np.empty((n, q_layer), dtype=np.float64)
                for i in range(n):
                    norm = p_u1_gb[u1_true[i], b[i]]
                    rows[i] = pjoint[u1_true[i], :, b[i]] / norm if norm > 0 else 0.0
                    if norm <= 0:
                        rows[i, 0] = 1.0
                true_val = u2[a]
            # center by true symbol (XOR/GF-add): out[i,j] = rows[i, j XOR true]
            out = np.empty_like(rows)
            for i in range(n):
                tv = true_val[i]
                out[i] = rows[i, idx512[:q_layer] ^ tv]
            return out
        return sampler

    def center(self, lid: str, rows: np.ndarray, true_sym: np.ndarray) -> np.ndarray:
        """Re-center posterior rows so true symbol maps to index 0 (XOR/GF-add).

        ``out[i, j] = rows[i, j XOR true_sym[i]]`` for j in 0..q-1.
        """
        q = rows.shape[1]
        rows = np.asarray(rows, dtype=np.float64)
        true_sym = np.asarray(true_sym, dtype=np.int64) & (q - 1)
        out = np.empty_like(rows)
        idx = (np.arange(q)[None, :] ^ true_sym[:, None])  # j XOR true
        for i in range(rows.shape[0]):
            out[i] = rows[i, idx[i]]
        return out


def Q_by_fact_layer(fact_id: str, lid: str) -> int:
    """Symbol-domain size for a (fact, layer) from the frozen factorization."""
    domain, width, bits = FACTORIZATIONS[fact_id]["layers"][lid]
    return 2 ** width


def build_adapter(counts: Mapping[str, np.ndarray], *, fact_id: str,
                  source: str) -> ChannelAdapter:
    return ChannelAdapter(fact_id=fact_id, source=source, N_ab=counts[source])


def adapter_entropy_bits(adapter: "ChannelAdapter") -> dict[str, float]:
    return dict(adapter.H_bits)
