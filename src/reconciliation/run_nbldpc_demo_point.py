#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(REPO_ROOT))

from src.qkd_io.ttbin_pipeline import compute_ttbin_metrics, read_ttbin_events


@dataclass
class _TT:
    TimeTag: np.ndarray
    Ch: np.ndarray


def _parse_point(value: str) -> tuple[int, int]:
    parts = [x.strip() for x in str(value).split(',')]
    if len(parts) != 2:
        raise ValueError(f'invalid point format: {value}')
    return int(parts[0]), int(parts[1])


def _find_point_dir_from_master(master_csv: Path, d: int, bw: int) -> Path | None:
    p = REPO_ROOT / 'results' / 'archive' / 'workspace_override_points' / f'd{int(d)}_bw{int(bw)}'
    return p if p.exists() else None


def _fallback_find_point_dir(d: int, bw: int) -> Path | None:
    p = REPO_ROOT / 'results' / 'archive' / 'workspace_override_points' / f'd{int(d)}_bw{int(bw)}'
    return p if p.exists() else None


def _resolve_override_ttbin() -> Path:
    v = str(os.getenv('HDQKD_TTBIN_FILE_OVERRIDE') or '').strip()
    if not v:
        raise FileNotFoundError('HDQKD_TTBIN_FILE_OVERRIDE is not set')
    p = Path(v)
    if not p.exists() or p.suffix.lower() != '.ttbin':
        raise FileNotFoundError(f'ttbin file not found: {p}')
    return p


def _build_resolved_config(ttbin_file: Path, d: int, bw: int, ch_a: int, ch_b: int) -> dict[str, Any]:
    return {
        'dimension': int(d),
        'ttbin': {
            'file': str(ttbin_file),
            'channels': {'A': int(ch_a), 'B': int(ch_b), 'sync': None},
            'pairing': {'coin_window_ps': int(max(1, bw)), 'offset_ps': 0, 'policy': 'nearest_unique'},
            'framing': {'bin_width_ps': int(bw), 'frame_bins': int(d), 'align': 'sync', 'postselect': '1click_each'},
        },
        'reconciliation': {'block_symbols': 512, 'rates': [0.95, 0.90, 0.85, 0.80, 0.75]},
    }


def _load_artifacts(d: int, bw: int, master_csv: Path) -> dict[str, Path]:
    point_dir = REPO_ROOT / 'results' / 'archive' / 'workspace_override_points' / f'd{int(d)}_bw{int(bw)}'
    attempt_dir = point_dir / 'results' / 'attempt_0'
    metrics_dir = attempt_dir / 'ttbin_parsing'
    metrics_dir.mkdir(parents=True, exist_ok=True)

    ttbin_file = _resolve_override_ttbin()
    ch_a = int(str(os.getenv('HDQKD_TTBIN_CH_A_OVERRIDE') or '1'))
    ch_b = int(str(os.getenv('HDQKD_TTBIN_CH_B_OVERRIDE') or '5'))

    resolved_cfg = _build_resolved_config(ttbin_file=ttbin_file, d=int(d), bw=int(bw), ch_a=ch_a, ch_b=ch_b)
    resolved_path = attempt_dir / 'resolved_config.json'
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(json.dumps(resolved_cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    metrics_path = metrics_dir / 'ttbin_metrics.json'
    if not metrics_path.exists():
        events = read_ttbin_events(ttbin_file)
        mcfg = {
            'channels': {'A': int(ch_a), 'B': int(ch_b), 'sync': None},
            'pairing': {'coin_window_ps': int(max(1, bw)), 'offset_ps': 0, 'policy': 'nearest_unique'},
            'framing': {'bin_width_ps': int(bw), 'frame_bins': int(d), 'align': 'sync', 'postselect': '1click_each'},
        }
        metrics = compute_ttbin_metrics(events=events, cfg=mcfg)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')

    (point_dir / 'point_summary.json').write_text(json.dumps({'chosen_attempt': 'attempt_0'}, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'point_dir': point_dir,
        'attempt_dir': attempt_dir,
        'resolved_config': resolved_path,
        'metrics': metrics_path,
    }


def _load_resolved_config(arts: dict[str, Path]) -> dict[str, Any]:
    p = arts.get('resolved_config')
    if p is None or not p.exists():
        raise FileNotFoundError('resolved_config.json not found')
    return json.loads(p.read_text(encoding='utf-8'))


def _read_ttbin_timetags(ttbin_path: Path, raw_ch0_id: int = 1, raw_ch1_id: int = 5) -> _TT:
    events = read_ttbin_events(ttbin_path)
    time_ps = np.asarray(events.time_ps, dtype=np.int64)
    channel = np.asarray(events.channel, dtype=np.int64)
    if events.event_type is not None:
        valid = np.asarray(events.event_type, dtype=np.int64) == 0
    else:
        valid = np.ones(time_ps.shape, dtype=bool)

    m0 = valid & (channel == int(raw_ch0_id))
    m1 = valid & (channel == int(raw_ch1_id))
    t0 = time_ps[m0]
    t1 = time_ps[m1]

    tt = np.concatenate([t0, t1]).astype(np.int64, copy=False)
    ch = np.concatenate([np.zeros(t0.size, dtype=np.int64), np.ones(t1.size, dtype=np.int64)])
    if tt.size:
        idx = np.argsort(tt, kind='mergesort')
        tt = tt[idx]
        ch = ch[idx]
    return _TT(TimeTag=tt, Ch=ch)


def _bin_indices_sorted_for_binwidth(tt: _TT, bin_width_ps: int) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    bw = int(max(1, bin_width_ps))
    t = np.asarray(tt.TimeTag, dtype=np.int64)
    ch = np.asarray(tt.Ch, dtype=np.int64)
    b0 = np.sort(np.floor_divide(t[ch == 0], bw).astype(np.int64, copy=False))
    b1 = np.sort(np.floor_divide(t[ch == 1], bw).astype(np.int64, copy=False))
    return b0, b1, {'n0': int(b0.size), 'n1': int(b1.size), 'bin_width_ps': int(bw)}


def _pairs_from_sorted_bins(b0_sorted: np.ndarray, b1_sorted: np.ndarray, dimension: int) -> tuple[np.ndarray, dict[str, Any]]:
    d = int(max(2, dimension))
    b0 = np.asarray(b0_sorted, dtype=np.int64)
    b1 = np.asarray(b1_sorted, dtype=np.int64)

    i = 0
    j = 0
    out_a = []
    out_b = []
    while i < b0.size and j < b1.size:
        f0 = int(b0[i] // d)
        f1 = int(b1[j] // d)
        if f0 == f1:
            out_a.append(int(b0[i] % d))
            out_b.append(int(b1[j] % d))
            i += 1
            j += 1
        elif f0 < f1:
            i += 1
        else:
            j += 1

    if out_a:
        pairs = np.column_stack([
            np.asarray(out_a, dtype=np.int64),
            np.asarray(out_b, dtype=np.int64),
        ])
    else:
        pairs = np.empty((0, 2), dtype=np.int64)
    return pairs, {'n_pairs': int(pairs.shape[0])}


if __name__ == '__main__':
    raise SystemExit('run_nbldpc_demo_point is helper-only in release build')
