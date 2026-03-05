#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def load_joint_counts_sparse_from_metrics(metrics_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    framed = payload.get("framed")
    if not isinstance(framed, dict):
        return []
    value = framed.get("joint_counts_sparse")
    return value if isinstance(value, list) else []


def build_joint_dense_from_sparse(*, dimension: int, joint_counts_sparse: list[dict[str, Any]]) -> np.ndarray:
    d = int(dimension)
    if d <= 0:
        raise ValueError("dimension must be > 0")
    j = np.zeros((d, d), dtype=np.float64)
    for entry in joint_counts_sparse:
        try:
            i = int(entry.get("i"))
            b = int(entry.get("j"))
            c = float(entry.get("count"))
        except Exception:
            continue
        if i < 0 or i >= d or b < 0 or b >= d:
            continue
        if (not math.isfinite(c)) or c <= 0.0:
            continue
        j[i, b] += c
    return j


def compute_joint_information_stats(joint_counts: np.ndarray) -> dict[str, float]:
    j = np.asarray(joint_counts, dtype=np.float64)
    if j.ndim != 2 or j.shape[0] != j.shape[1]:
        raise ValueError("joint_counts must be square [d,d]")
    d = int(j.shape[0])
    tot = float(np.sum(j))
    if tot <= 0.0:
        raise ValueError("joint total count must be positive")
    p_ab = j / tot
    p_a = np.sum(p_ab, axis=1)
    p_b = np.sum(p_ab, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_pa = np.where(p_a > 0.0, np.log2(p_a), 0.0)
        h_a = -float(np.sum(p_a * log_pa))
    # H(A|B) = -sum_ab p(a,b) log p(a|b)
    h_cond = 0.0
    for b in range(d):
        pb = float(p_b[b])
        if pb <= 0.0:
            continue
        pab_col = p_ab[:, b]
        with np.errstate(divide="ignore", invalid="ignore"):
            pa_given_b = np.where(pab_col > 0.0, pab_col / pb, 0.0)
            log_cond = np.where(pa_given_b > 0.0, np.log2(pa_given_b), 0.0)
        h_cond += -float(np.sum(pab_col * log_cond))
    i_ab = h_a - h_cond
    log2d = math.log2(float(d)) if d > 1 else 0.0
    r_sw = 1.0 - (h_cond / log2d) if log2d > 0.0 else 0.0
    return {
        "H_A_bpc": float(h_a),
        "H_A_given_B_bpc": float(h_cond),
        "I_AB_bpc": float(i_ab),
        "log2d": float(log2d),
        "r_sw": float(r_sw),
        "sum_counts": float(tot),
    }


def build_route1_rate_list(*, r_sw: float, max_tries: int = 12) -> list[float]:
    tries = max(1, int(max_tries))
    tail = [0.60, 0.50, 0.40]
    main_limit = max(0, tries - len(tail))
    start = min(0.98, float(r_sw) + 0.03)
    end = float(r_sw) - 0.16
    vals: list[float] = []
    cur = start
    while cur >= end - 1e-12 and len(vals) < main_limit:
        vals.append(float(round(cur, 6)))
        cur -= 0.02
    vals.extend(tail)
    out: list[float] = []
    seen: set[float] = set()
    for v in vals:
        vv = float(max(0.01, min(0.99, v)))
        key = float(round(vv, 6))
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
        if len(out) >= tries:
            break
    return out


def compute_beta_eff(*, i_ab_bpc: float | None, chi_bpc: float | None, delta_fk_bpc: float | None, pie_bpc: float | None) -> float | None:
    if i_ab_bpc is None or pie_bpc is None:
        return None
    try:
        iab = float(i_ab_bpc)
        pie = float(pie_bpc)
        chi = float(chi_bpc or 0.0)
        dlt = float(delta_fk_bpc or 0.0)
    except Exception:
        return None
    if (not math.isfinite(iab)) or iab <= 0.0:
        return None
    if (not math.isfinite(pie)) or (not math.isfinite(chi)) or (not math.isfinite(dlt)):
        return None
    return float((pie + chi + dlt) / iab)
