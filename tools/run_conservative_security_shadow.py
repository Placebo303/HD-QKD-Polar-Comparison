#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from _security_audit_common import ensure_output_dir, h2, load_candidate_frame, monotonic_increasing, tol_for_values, write_summary


EPS_PE = 1e-10
EPS_SEC = 1e-10
EPS_COR = 1e-12


def _pe_margin(n: float, eps: float) -> float:
    if not math.isfinite(n) or n <= 0:
        return float('nan')
    return math.sqrt(max(0.0, math.log(2.0 / eps) / (2.0 * n)))


def _chi_from_error(d: int, e: float) -> float:
    ee = min(max(float(e), 1e-12), 1.0 - 1e-12)
    return float(h2(ee) + ee * math.log2(max(1, int(d) - 1))) if int(d) > 1 else 0.0


def _row_shadow_v1(row: pd.Series) -> tuple[float, float, dict[str, float]]:
    d = int(row['dimension'])
    rate = float(row['coincidence_rate_hz']) if pd.notna(row['coincidence_rate_hz']) else float('nan')
    n = float(row['n_pairs_actual']) if pd.notna(row['n_pairs_actual']) else float('nan')
    iab = float(row['IAB_or_proxy']) if pd.notna(row['IAB_or_proxy']) else float('nan')
    leak_proxy = float(row['leak_ec_bits_or_proxy']) if pd.notna(row['leak_ec_bits_or_proxy']) else float('nan')
    base_vis = float(row['visibility_assumed']) if pd.notna(row.get('visibility_assumed')) else 0.95
    base_e = max(0.0, min(0.5, (1.0 - base_vis) / 2.0))
    obs_e = row['raw_ser'] if pd.notna(row.get('raw_ser')) else row['map_ser']
    obs_e = float(obs_e) if pd.notna(obs_e) else base_e
    margin = _pe_margin(n, EPS_PE)
    e_shadow = min(0.499, max(base_e, obs_e + (margin if math.isfinite(margin) else 0.0)))
    chi_shadow = _chi_from_error(d, e_shadow)
    delta_fk = float('nan') if (not math.isfinite(n) or n <= 0) else 4.0 * math.sqrt(math.log2(2.0 / EPS_SEC) / n) + 2.0 * math.log2(2.0 / EPS_COR) / n
    leak_shadow = float('nan')
    if math.isfinite(iab):
        leak_shadow = (1.20 * max(0.0, leak_proxy if math.isfinite(leak_proxy) else 0.0)) + 0.02 * math.log2(max(2, d))
    usable_fraction = 1.0
    if pd.notna(row.get('clean_pair_fraction')):
        usable_fraction = min(1.0, max(0.0, float(row['clean_pair_fraction'])))
    elif pd.notna(row.get('frame_diag_available')) and int(float(row['frame_diag_available'])) != 1:
        usable_fraction = 0.9
    pie = float('nan')
    if math.isfinite(iab) and math.isfinite(leak_shadow) and math.isfinite(chi_shadow) and math.isfinite(delta_fk):
        pie = max(0.0, usable_fraction * (iab - leak_shadow - chi_shadow - delta_fk))
    skr = pie * rate if math.isfinite(pie) and math.isfinite(rate) else float('nan')
    return pie, skr, {
        'chi_E_shadow_v1': chi_shadow,
        'delta_fk_shadow_v1': delta_fk,
        'leak_ec_shadow_v1': leak_shadow,
        'usable_fraction_shadow_v1': usable_fraction,
    }


def _row_shadow_v2(row: pd.Series, paper_target: str) -> tuple[float | None, float | None, dict[str, float | str]]:
    d = int(row['dimension'])
    rate = float(row['coincidence_rate_hz']) if pd.notna(row['coincidence_rate_hz']) else float('nan')
    n = float(row['n_pairs_actual']) if pd.notna(row['n_pairs_actual']) else float('nan')
    iab = float(row['IAB_or_proxy']) if pd.notna(row['IAB_or_proxy']) else float('nan')
    beta = float(row['beta_or_proxy']) if pd.notna(row['beta_or_proxy']) else float('nan')
    map_ser = float(row['map_ser']) if pd.notna(row['map_ser']) else float('nan')
    raw_ser = float(row['raw_ser']) if pd.notna(row['raw_ser']) else map_ser
    clean_pair_fraction = float(row['clean_pair_fraction']) if pd.notna(row.get('clean_pair_fraction')) else float('nan')
    base_vis = float(row['visibility_assumed']) if pd.notna(row.get('visibility_assumed')) else 0.95
    base_e = max(0.0, min(0.5, (1.0 - base_vis) / 2.0))

    if paper_target == 'zhong_2015':
        margin = _pe_margin(n, EPS_PE)
        e_shadow = min(0.499, max(base_e, max(map_ser, raw_ser) + (margin if math.isfinite(margin) else 0.0)))
        chi_shadow = _chi_from_error(d, e_shadow)
        delta_fk = float('nan') if (not math.isfinite(n) or n <= 0) else 5.0 * math.sqrt(math.log2(2.0 / EPS_SEC) / n) + 3.0 * math.log2(2.0 / EPS_COR) / n
        beta_eff = min(0.95, beta) if math.isfinite(beta) else 0.90
        usable_fraction = min(1.0, max(0.0, clean_pair_fraction)) if math.isfinite(clean_pair_fraction) else 0.9
        pie = float('nan')
        if math.isfinite(iab) and math.isfinite(delta_fk):
            pie = max(0.0, usable_fraction * (beta_eff * iab - chi_shadow - delta_fk))
        skr = pie * rate if math.isfinite(pie) and math.isfinite(rate) else float('nan')
        return pie, skr, {
            'shadow_v2_model_tag': 'zhong_like_explicit_beta_iab',
            'chi_E_shadow_v2': chi_shadow,
            'delta_fk_shadow_v2': delta_fk,
            'usable_fraction_shadow_v2': usable_fraction,
            'beta_shadow_v2': beta_eff,
        }

    # niu_2016: partial only; explicit block reason if required observables are missing.
    required_missing = []
    if not math.isfinite(clean_pair_fraction):
        required_missing.append('single_pair_fraction_proxy_missing')
    required_missing.extend(['decoy_state_PE_missing', 'conjugate_basis_stats_missing', 'composable_proof_constants_protocol_specific_missing'])
    margin = _pe_margin(n, EPS_PE)
    e_shadow = min(0.499, max(base_e, max(map_ser, raw_ser) + 2.0 * (margin if math.isfinite(margin) else 0.0))) if math.isfinite(raw_ser) or math.isfinite(map_ser) else base_e
    chi_shadow = _chi_from_error(d, e_shadow)
    delta_fk = float('nan') if (not math.isfinite(n) or n <= 0) else 8.0 * math.sqrt(math.log2(2.0 / EPS_SEC) / n) + 4.0 * math.log2(2.0 / EPS_COR) / n
    beta_eff = min(0.90, beta) if math.isfinite(beta) else 0.85
    usable_fraction = min(1.0, max(0.0, clean_pair_fraction)) if math.isfinite(clean_pair_fraction) else float('nan')
    if required_missing:
        return float('nan'), float('nan'), {
            'shadow_v2_model_tag': 'niu_like_blocked_partial',
            'v2_blocked_reason': ';'.join(required_missing),
            'chi_E_shadow_v2': chi_shadow,
            'delta_fk_shadow_v2': delta_fk,
            'beta_shadow_v2': beta_eff,
            'usable_fraction_shadow_v2': usable_fraction,
        }
    pie = max(0.0, usable_fraction * (beta_eff * iab - chi_shadow - delta_fk)) if math.isfinite(iab) and math.isfinite(usable_fraction) and math.isfinite(delta_fk) else float('nan')
    skr = pie * rate if math.isfinite(pie) and math.isfinite(rate) else float('nan')
    return pie, skr, {
        'shadow_v2_model_tag': 'niu_like_partial',
        'v2_blocked_reason': '',
        'chi_E_shadow_v2': chi_shadow,
        'delta_fk_shadow_v2': delta_fk,
        'beta_shadow_v2': beta_eff,
        'usable_fraction_shadow_v2': usable_fraction,
    }


def _summarize(df: pd.DataFrame, *, pie_col: str, skr_col: str, label: str, paper_target: str) -> list[str]:
    lines = [f'label: {label}', f'paper_target: {paper_target}', f'point_count: {len(df)}']
    large_bw = df[df['bin_width_ps'] >= 120].copy()
    large_d = df[df['dimension'] >= 1024].copy()
    def _mean_drop(cur: pd.Series, new: pd.Series) -> float:
        valid = pd.notna(cur) & pd.notna(new) & (cur > 0)
        if not valid.any():
            return float('nan')
        return float(((cur[valid] - new[valid]) / cur[valid]).mean())
    lines.append(f'large_bw_mean_pie_drop_frac: {_mean_drop(large_bw["PIE_practical"], large_bw[pie_col]):.6f}')
    lines.append(f'large_bw_mean_skr_drop_frac: {_mean_drop(large_bw["SKR_measured_bps"], large_bw[skr_col]):.6f}')
    lines.append(f'large_d_mean_pie_drop_frac: {_mean_drop(large_d["PIE_practical"], large_d[pie_col]):.6f}')
    lines.append(f'large_d_mean_skr_drop_frac: {_mean_drop(large_d["SKR_measured_bps"], large_d[skr_col]):.6f}')

    lines.append('optimum_shift_by_loss:')
    for loss_db, sl in df.groupby('loss_db'):
        cur_best = sl.loc[pd.to_numeric(sl['SKR_measured_bps'], errors='coerce').idxmax()]
        if sl[skr_col].notna().any():
            new_best = sl.loc[pd.to_numeric(sl[skr_col], errors='coerce').idxmax()]
            lines.append(f"  - loss={int(loss_db)} current_best=(d={int(cur_best['dimension'])},bw={int(cur_best['bin_width_ps'])}) shadow_best=(d={int(new_best['dimension'])},bw={int(new_best['bin_width_ps'])})")
        else:
            lines.append(f"  - loss={int(loss_db)} shadow_best=UNAVAILABLE")

    bw_trend_preserved = 0
    bw_trend_flattened = 0
    d_trend_preserved = 0
    d_trend_flattened = 0
    for (loss_db, dimension), sl in df.groupby(['loss_db', 'dimension']):
        sl = sl.sort_values('bin_width_ps')
        cur = [float(v) for v in sl['PIE_practical'].tolist() if pd.notna(v)]
        new = [float(v) for v in sl[pie_col].tolist() if pd.notna(v)]
        cur_up = monotonic_increasing(cur)
        new_up = monotonic_increasing(new)
        if cur_up and new_up:
            bw_trend_preserved += 1
        elif cur_up and not new_up:
            bw_trend_flattened += 1
    for (loss_db, bw), sl in df.groupby(['loss_db', 'bin_width_ps']):
        sl = sl.sort_values('dimension')
        cur = [float(v) for v in sl['SKR_measured_bps'].tolist() if pd.notna(v)]
        new = [float(v) for v in sl[skr_col].tolist() if pd.notna(v)]
        cur_up = monotonic_increasing(cur)
        new_up = monotonic_increasing(new)
        if cur_up and new_up:
            d_trend_preserved += 1
        elif cur_up and not new_up:
            d_trend_flattened += 1
    lines.append(f'bw_trend_preserved_slice_count: {bw_trend_preserved}')
    lines.append(f'bw_trend_flattened_or_reversed_slice_count: {bw_trend_flattened}')
    lines.append(f'd_trend_preserved_slice_count: {d_trend_preserved}')
    lines.append(f'd_trend_flattened_or_reversed_slice_count: {d_trend_flattened}')
    lines.append(f'overall_bw_trend_effect: {'flattened' if bw_trend_flattened > 0 else 'preserved'}')
    lines.append(f'overall_d_trend_effect: {'flattened' if d_trend_flattened > 0 else 'preserved'}')
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description='Run conservative security shadow recomputation.')
    ap.add_argument('--input-dirs', nargs='+', required=True)
    ap.add_argument('--paper-target', choices=['zhang_2013', 'zhong_2015', 'niu_2016'], required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))

    df = pd.concat([load_candidate_frame(Path(p)) for p in args.input_dirs], ignore_index=True)
    v1_pie = []
    v1_skr = []
    v1_meta_rows = []
    v2_pie = []
    v2_skr = []
    v2_meta_rows = []
    for _, row in df.iterrows():
        pie1, skr1, meta1 = _row_shadow_v1(row)
        v1_pie.append(pie1)
        v1_skr.append(skr1)
        v1_meta_rows.append(meta1)
        pie2, skr2, meta2 = _row_shadow_v2(row, args.paper_target)
        v2_pie.append(pie2)
        v2_skr.append(skr2)
        v2_meta_rows.append(meta2)
    df['PIE_conservative_v1'] = v1_pie
    df['SKR_conservative_v1_bps'] = v1_skr
    df['PIE_conservative_v2'] = v2_pie
    df['SKR_conservative_v2_bps'] = v2_skr
    for key in ['chi_E_shadow_v1','delta_fk_shadow_v1','leak_ec_shadow_v1','usable_fraction_shadow_v1']:
        df[key] = [m.get(key, np.nan) for m in v1_meta_rows]
    for key in ['shadow_v2_model_tag','v2_blocked_reason','chi_E_shadow_v2','delta_fk_shadow_v2','beta_shadow_v2','usable_fraction_shadow_v2']:
        df[key] = [m.get(key, np.nan) for m in v2_meta_rows]

    base_cols = [
        'loss_db','dimension','bin_width_ps','bw_bucket','map_ser','raw_ser','layers_success_best','best_hard_PIE','IAB_or_proxy','beta_or_proxy',
        'leak_ec_bits_or_proxy','chi_E','delta_fk','PIE_practical','SKR_measured_bps','n_pairs_actual','frame_diag_available','clean_pair_fraction',
        'PIE_conservative_v1','SKR_conservative_v1_bps','chi_E_shadow_v1','delta_fk_shadow_v1','leak_ec_shadow_v1','usable_fraction_shadow_v1',
        'PIE_conservative_v2','SKR_conservative_v2_bps','shadow_v2_model_tag','v2_blocked_reason','chi_E_shadow_v2','delta_fk_shadow_v2','beta_shadow_v2','usable_fraction_shadow_v2'
    ]
    df[base_cols].to_csv(output_dir / 'conservative_shadow_v1_point_table.csv', index=False)
    df[base_cols].to_csv(output_dir / 'conservative_shadow_v2_point_table.csv', index=False)

    v1_lines = ['input_dirs:', *[f'  - {p}' for p in args.input_dirs], *_summarize(df, pie_col='PIE_conservative_v1', skr_col='SKR_conservative_v1_bps', label='conservative_shadow_v1', paper_target=args.paper_target)]
    v2_lines = ['input_dirs:', *[f'  - {p}' for p in args.input_dirs], *_summarize(df, pie_col='PIE_conservative_v2', skr_col='SKR_conservative_v2_bps', label='conservative_shadow_v2', paper_target=args.paper_target)]
    if args.paper_target == 'niu_2016':
        blocked = df['v2_blocked_reason'].dropna()
        v2_lines.append('niu_v2_blocked_reason_examples:')
        if len(blocked):
            for txt in sorted(set(str(x) for x in blocked.tolist())):
                v2_lines.append(f'  - {txt}')
        else:
            v2_lines.append('  - none')
    write_summary(output_dir / 'conservative_shadow_v1_summary.txt', v1_lines)
    write_summary(output_dir / 'conservative_shadow_v2_summary.txt', v2_lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
