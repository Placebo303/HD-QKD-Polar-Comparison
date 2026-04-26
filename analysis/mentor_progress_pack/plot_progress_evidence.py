from __future__ import annotations

import argparse
from pathlib import Path
import sys
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.mentor_progress_pack.utils_progress_pack import DEFAULT_DATA_ROOT, PackContext, now_stamp, read_csv_if_exists

warnings.filterwarnings("ignore", message="This figure includes Axes that are not compatible with tight_layout")
from analysis.mentor_progress_pack.utils_progress_pack import build_reports, write_markdown


def add_footer(fig: plt.Figure, source: str, script_name: str) -> None:
    fig.text(0.01, 0.01, f"source: {source} | script: {script_name} | generated: {now_stamp()}", fontsize=8)


def save_dual(fig: plt.Figure, stem: str, source: str, ctx: PackContext) -> None:
    add_footer(fig, source, ctx.script_name)
    png_path = ctx.figures_dir / f"{stem}.png"
    pdf_path = ctx.figures_dir / f"{stem}.pdf"
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(png_path, dpi=220)
    fig.savefig(pdf_path)
    plt.close(fig)
    ctx.log("OK", f"wrote figure: {png_path}")
    ctx.log("OK", f"wrote figure: {pdf_path}")


def placeholder(stem: str, title: str, reason: str, source: str, ctx: PackContext) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.6, title, ha="center", va="center", fontsize=14, weight="bold")
    ax.text(0.5, 0.4, reason, ha="center", va="center", fontsize=11)
    save_dual(fig, stem, source, ctx)


def render_table_figure(df: pd.DataFrame, stem: str, title: str, source: str, ctx: PackContext, max_rows: int = 12) -> None:
    show = df.head(max_rows).copy()
    fig_h = max(3.5, 0.5 * (len(show) + 2))
    fig, ax = plt.subplots(figsize=(12, fig_h))
    ax.axis("off")
    ax.set_title(title)
    table = ax.table(cellText=show.astype(str).values, colLabels=show.columns.tolist(), loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.2)
    save_dual(fig, stem, source, ctx)


def heatmap_from_matrix(df: pd.DataFrame, value_col: str, stem: str, title: str, source: str, ctx: PackContext, cmap: str = "Greys") -> None:
    if df.empty or value_col not in df.columns:
        placeholder(stem, title, f"missing data for {value_col}", source, ctx)
        return
    pivot = df.pivot(index="d", columns="bw", values=value_col).sort_index().sort_index(axis=1)
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap=cmap)
    ax.set_title(title)
    ax.set_xlabel("bw (ps)")
    ax.set_ylabel("d")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([int(v) for v in pivot.columns], rotation=45)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([int(v) for v in pivot.index])
    fig.colorbar(im, ax=ax)
    save_dual(fig, stem, source, ctx)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--output-root", default="")
    args = ap.parse_args()

    data_root = Path(args.data_root).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    ctx = PackContext.create(Path(__file__).name, data_root=data_root, output_root=output_root)

    tables_dir = ctx.tables_dir
    coverage = read_csv_if_exists(tables_dir / "loss_directory_coverage.csv")
    matrix = read_csv_if_exists(tables_dir / "fullgrid_20db_matrix.csv")
    contamination = read_csv_if_exists(tables_dir / "contamination_summary_by_d.csv")
    bw_scan = read_csv_if_exists(tables_dir / "bw_scan_keypoints.csv")
    threshold = read_csv_if_exists(tables_dir / "threshold_sensitivity_summary.csv")
    claim = read_csv_if_exists(tables_dir / "canonical_claim_boundary_table.csv")
    compare = read_csv_if_exists(tables_dir / "v1_v2_compare_table.csv")
    reps = read_csv_if_exists(tables_dir / "representative_points_for_next_step.csv")
    completeness = read_csv_if_exists(tables_dir / "canonical_field_completeness.csv")

    figures_written = 0
    reports_written = 0

    if not coverage.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(coverage))
        width = 0.2
        ax.bar(x - 1.5 * width, coverage["n_total_result_dirs"], width, label="total")
        ax.bar(x - 0.5 * width, coverage["n_refresh_dirs"], width, label="refresh")
        ax.bar(x + 0.5 * width, coverage["n_canonicalized_dirs"], width, label="canonicalized")
        ax.bar(x + 1.5 * width, coverage["n_dirs_with_all_three"], width, label="all_three")
        ax.set_title("Loss Directory Coverage")
        ax.set_xlabel("loss (dB)")
        ax.set_ylabel("directory count")
        ax.set_xticks(x)
        ax.set_xticklabels(coverage["loss_db"].astype(str).tolist())
        ax.legend()
        save_dual(fig, "fig01_loss_coverage_bar", "loss_directory_coverage.csv", ctx)
    else:
        placeholder("fig01_loss_coverage_bar", "Loss Directory Coverage", "missing coverage table", "loss_directory_coverage.csv", ctx)
    figures_written += 1

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    boxes = [
        (0.08, 0.55, "sidecar", "a_eff/b_eff\nseq_pair_stats\noccupancy_filter_summary"),
        (0.33, 0.55, "Polar", "polar_e2e_results_refresh\npolar_diag_summary\npolar_layer_metrics"),
        (0.58, 0.55, "refresh", "claim tags\nthreshold tags\nnuisance tags"),
        (0.83, 0.55, "canonical package", "tables\nfigures\nreports"),
    ]
    for x, y, head, body in boxes:
        ax.text(x, y, f"{head}\n\n{body}", ha="center", va="center", bbox=dict(boxstyle="round", facecolor="white"))
    for x0, x1 in ((0.17, 0.25), (0.42, 0.5), (0.67, 0.75)):
        ax.annotate("", xy=(x1, 0.55), xytext=(x0, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.set_title("Pipeline Status Schematic")
    save_dual(fig, "fig02_pipeline_status_schematic", "file_presence_manifest.csv", ctx)
    figures_written += 1

    if matrix.empty:
        placeholder("fig03_20db_output_availability_heatmap", "20 dB Output Availability", "missing 20 dB matrix", "fullgrid_20db_matrix.csv", ctx)
    else:
        fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
        for ax, col, title in zip(axes, ["has_e2e", "has_diag", "has_layer"], ["E2E", "Diag", "Layer"]):
            pivot = matrix.pivot(index="d", columns="bw", values=col).sort_index().sort_index(axis=1)
            im = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="Greys", vmin=0, vmax=1)
            ax.set_title(title)
            ax.set_xlabel("bw (ps)")
            ax.set_xticks(np.arange(len(pivot.columns)))
            ax.set_xticklabels([int(v) for v in pivot.columns], rotation=45)
            if ax is axes[0]:
                ax.set_ylabel("d")
                ax.set_yticks(np.arange(len(pivot.index)))
                ax.set_yticklabels([int(v) for v in pivot.index])
        fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8)
        save_dual(fig, "fig03_20db_output_availability_heatmap", "fullgrid_20db_matrix.csv", ctx)
    figures_written += 1

    heatmap_from_matrix(matrix, "frame_diag_available", "fig04_frame_diag_available_heatmap", "20 dB Frame Diagnostics Availability", "fullgrid_20db_matrix.csv", ctx)
    figures_written += 1

    if contamination.empty:
        placeholder("fig05_clean_vs_ambiguous_pairs", "Clean vs Ambiguous Pairs", "missing contamination summary", "contamination_summary_by_d.csv", ctx)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(contamination))
        clean = pd.to_numeric(contamination["mean_clean_pair_fraction"], errors="coerce").fillna(0)
        amb = 1 - clean
        ax.bar(x, clean, label="clean")
        ax.bar(x, amb, bottom=clean, label="ambiguous")
        ax.set_xticks(x)
        ax.set_xticklabels(contamination["d"].astype(int).astype(str))
        ax.set_xlabel("d")
        ax.set_ylabel("pair fraction")
        ax.set_title("Clean vs Ambiguous Pairs")
        ax.legend()
        save_dual(fig, "fig05_clean_vs_ambiguous_pairs", "contamination_summary_by_d.csv", ctx)
    figures_written += 1

    if contamination.empty:
        placeholder("fig06_contamination_source_breakdown", "Contamination Source Breakdown", "missing contamination summary", "contamination_summary_by_d.csv", ctx)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(contamination))
        cross = pd.to_numeric(contamination["mean_cross_frame_fraction"], errors="coerce").fillna(0)
        am = pd.to_numeric(contamination["mean_A_multi_fraction"], errors="coerce").fillna(0)
        bm = pd.to_numeric(contamination["mean_B_multi_fraction"], errors="coerce").fillna(0)
        both = pd.to_numeric(contamination["mean_both_multi_frame_fraction"], errors="coerce").fillna(0)
        ax.bar(x, cross, label="cross_frame")
        ax.bar(x, am, bottom=cross, label="A_multi")
        ax.bar(x, bm, bottom=cross + am, label="B_multi")
        ax.bar(x, both, bottom=cross + am + bm, label="both_multi")
        ax.set_xticks(x)
        ax.set_xticklabels(contamination["d"].astype(int).astype(str))
        ax.set_xlabel("d")
        ax.set_ylabel("frame fraction")
        ax.set_title("Contamination Source Breakdown")
        ax.legend()
        save_dual(fig, "fig06_contamination_source_breakdown", "contamination_summary_by_d.csv", ctx)
    figures_written += 1

    if matrix.empty:
        placeholder("fig07_both_multi_vs_performance", "Both-Multi vs Performance", "missing 20 dB matrix", "fullgrid_20db_matrix.csv", ctx)
    else:
        fig, ax = plt.subplots(figsize=(8, 5))
        x = pd.to_numeric(matrix["both_multi_frame_fraction"], errors="coerce")
        y = pd.to_numeric(matrix["PIE_practical"], errors="coerce")
        c = pd.to_numeric(matrix["d"], errors="coerce")
        scatter = ax.scatter(x, y, c=c, s=35)
        ax.set_xlabel("both_multi_frame_fraction")
        ax.set_ylabel("PIE_practical")
        ax.set_title("Both-Multi vs Performance")
        fig.colorbar(scatter, ax=ax, label="d")
        save_dual(fig, "fig07_both_multi_vs_performance", "fullgrid_20db_matrix.csv", ctx)
    figures_written += 1

    for d_value, stem in ((2048, "fig08_bw_scan_d2048"), (4096, "fig09_bw_scan_d4096")):
        sub = bw_scan[bw_scan["d"] == d_value]
        if sub.empty:
            placeholder(stem, f"BW Scan d={d_value}", "missing bw scan data", "bw_scan_keypoints.csv", ctx)
        else:
            fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
            axes[0].plot(sub["bw"], sub["PIE_practical"], marker="o", label="PIE_practical")
            axes[0].plot(sub["bw"], sub["SKR"], marker="s", label="SKR")
            axes[0].set_ylabel("performance")
            axes[0].set_title(f"BW Scan d={d_value}")
            axes[0].legend()
            axes[1].plot(sub["bw"], sub["raw_ser"], marker="o", label="raw_ser")
            axes[1].plot(sub["bw"], sub["min_capacity"], marker="s", label="min_capacity")
            axes[1].plot(sub["bw"], sub["weakest_margin_to_0.1"], marker="^", label="margin_to_0.1")
            axes[1].set_xlabel("bw (ps)")
            axes[1].set_ylabel("explainers")
            axes[1].legend()
            save_dual(fig, stem, "bw_scan_keypoints.csv", ctx)
        figures_written += 1

    if matrix.empty:
        placeholder("fig10_explainer_metric_comparison", "Explainer Metric Comparison", "missing 20 dB matrix", "fullgrid_20db_matrix.csv", ctx)
    else:
        numeric = matrix[["peak_to_bg", "raw_ser", "min_capacity", "weakest_margin_to_0.1", "PIE_practical", "SKR"]].apply(pd.to_numeric, errors="coerce")
        metrics = ["peak_to_bg", "raw_ser", "min_capacity", "weakest_margin_to_0.1"]
        pie_corr = [numeric[m].corr(numeric["PIE_practical"]) for m in metrics]
        skr_corr = [numeric[m].corr(numeric["SKR"]) for m in metrics]
        x = np.arange(len(metrics))
        width = 0.35
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(x - width / 2, pie_corr, width, label="corr_with_PIE")
        ax.bar(x + width / 2, skr_corr, width, label="corr_with_SKR")
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=20)
        ax.set_ylabel("Pearson correlation")
        ax.set_title("Explainer Metric Comparison")
        ax.legend()
        save_dual(fig, "fig10_explainer_metric_comparison", "fullgrid_20db_matrix.csv", ctx)
    figures_written += 1

    target = threshold[(threshold["d"].isin([2048, 4096])) & (threshold["bw"] == 30)] if not threshold.empty else pd.DataFrame()
    if target.empty:
        placeholder("fig11_threshold_sensitivity_keypoints", "Threshold Sensitivity Keypoints", "missing threshold keypoints", "threshold_sensitivity_summary.csv", ctx)
    else:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=False)
        for ax, d_value in zip(axes, [2048, 4096]):
            sub = target[target["d"] == d_value].sort_values("threshold_ps")
            ax.plot(sub["threshold_ps"], sub["PIE_practical"], marker="o", label="PIE_practical")
            ax.plot(sub["threshold_ps"], sub["SKR"], marker="s", label="SKR")
            ax.plot(sub["threshold_ps"], sub["layers_success_best"], marker="^", label="layers_success_best")
            ax.set_title(f"d={d_value}, bw=30")
            ax.set_xlabel("threshold_ps")
            ax.legend()
        save_dual(fig, "fig11_threshold_sensitivity_keypoints", "threshold_sensitivity_summary.csv", ctx)
    figures_written += 1

    if coverage.empty:
        placeholder("fig12_canonicalization_by_loss", "Canonicalization by Loss", "missing coverage table", "loss_directory_coverage.csv", ctx)
    else:
        fig, ax = plt.subplots(figsize=(9, 5))
        ratio = coverage["n_canonicalized_dirs"] / coverage["n_total_result_dirs"].replace(0, np.nan)
        ax.bar(coverage["loss_db"].astype(str), ratio.fillna(0))
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("loss (dB)")
        ax.set_ylabel("canonicalized / total")
        ax.set_title("Canonicalization by Loss")
        save_dual(fig, "fig12_canonicalization_by_loss", "loss_directory_coverage.csv", ctx)
    figures_written += 1

    fig13_source = "canonical_claim_boundary_table.csv; canonical_field_completeness.csv" if not completeness.empty else "canonical_claim_boundary_table.csv"
    render_table_figure(claim, "fig13_field_layer_summary_table", "Field Layer Summary", fig13_source, ctx)
    figures_written += 1

    if claim.empty:
        placeholder("fig14_claim_boundary_summary", "Claim Boundary Summary", "missing claim table", "canonical_claim_boundary_table.csv", ctx)
    else:
        summary = pd.DataFrame(
            {
                "can_say_now": claim[claim["can_be_claimed_now"].isin(["yes", "partial"])]["field_name"].tolist(),
                "cannot_say_now": ["unconditional security result", "default rule fully frozen", "pairing_v2 safe everywhere"] + [""] * max(0, len(claim) - 3),
            }
        )
        render_table_figure(summary, "fig14_claim_boundary_summary", "Claim Boundary Summary", "canonical_claim_boundary_table.csv", ctx, max_rows=8)
    figures_written += 1

    if compare.empty:
        placeholder("fig15_v1_v2_delta_heatmap", "v1 vs v2 Delta Heatmap", "missing v1/v2 compare table", "v1_v2_compare_table.csv", ctx)
    else:
        delta = compare[compare["metric_name"] == "PIE_practical"].copy()
        if delta.empty:
            placeholder("fig15_v1_v2_delta_heatmap", "v1 vs v2 Delta Heatmap", "no PIE delta rows", "v1_v2_compare_table.csv", ctx)
        else:
            heatmap_from_matrix(delta.rename(columns={"delta_abs": "delta"}), "delta", "fig15_v1_v2_delta_heatmap", "v1 vs v2 Delta PIE Heatmap", "v1_v2_compare_table.csv", ctx, cmap="coolwarm")
    figures_written += 1

    if compare.empty:
        placeholder("fig16_v1_v2_representative_table", "v1 vs v2 Representative Table", "missing compare table", "v1_v2_compare_table.csv", ctx)
    else:
        wide = compare[compare["metric_name"].isin(["PIE_practical", "SKR", "raw_ser"])].pivot_table(
            index=["d", "bw", "pairing_path_tag_v1", "pairing_path_tag_v2"],
            columns="metric_name",
            values=["value_legacy_v1", "value_pairing_v2", "delta_abs"],
            aggfunc="first",
        )
        wide.columns = ["_".join([str(v) for v in col if v]) for col in wide.columns]
        render_table_figure(wide.reset_index(), "fig16_v1_v2_representative_table", "v1 vs v2 Representative Table", "v1_v2_compare_table.csv", ctx, max_rows=10)
    figures_written += 1

    if compare.empty:
        placeholder("fig17_smoke_test_path_table", "Smoke Test Path Table", "missing compare table", "v1_v2_compare_table.csv", ctx)
    else:
        path_table = compare[["d", "bw", "pairing_path_tag_v1", "pairing_path_tag_v2"]].drop_duplicates().sort_values(["d", "bw"])
        render_table_figure(path_table, "fig17_smoke_test_path_table", "Smoke Test Path Table", "v1_v2_compare_table.csv", ctx, max_rows=12)
    figures_written += 1

    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.axis("off")
    steps = [
        (0.15, "1. freeze legacy_v1 reference"),
        (0.5, "2. small-scope pairing_v2 validation"),
        (0.85, "3. decide package exposure of v1/v2"),
    ]
    for x, label in steps:
        ax.text(x, 0.5, label, ha="center", va="center", bbox=dict(boxstyle="round", facecolor="white"))
    for x0, x1 in ((0.25, 0.4), (0.6, 0.75)):
        ax.annotate("", xy=(x1, 0.5), xytext=(x0, 0.5), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.set_title("Next Step Route")
    save_dual(fig, "fig18_next_step_route", "representative_points_for_next_step.csv", ctx)
    figures_written += 1

    render_table_figure(reps, "fig19_representative_points_matrix", "Representative Points Matrix", "representative_points_for_next_step.csv", ctx, max_rows=12)
    figures_written += 1

    report_md, ppt_md = build_reports(matrix, threshold, compare)
    write_markdown(report_md, ctx.reports_dir / "mentor_progress_evidence_report.md", ctx)
    reports_written += 1
    write_markdown(ppt_md, ctx.reports_dir / "mentor_progress_ppt_ready.md", ctx)
    reports_written += 1

    ctx.summary(
        tables_written=0,
        figures_written=figures_written,
        reports_written=reports_written,
        representative_points=int(reps.shape[0]) if not reps.empty else 0,
        used_existing_results_only=True,
        performed_new_small_scope_runs=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
