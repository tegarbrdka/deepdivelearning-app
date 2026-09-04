"""
ReportGenerator — creates visualizations and exportable reports
from evaluation metrics for academic publication.

Generates:
- Confusion matrix heatmaps (PNG)
- Scatter plots: CV score vs Observer score
- Bland-Altman plots
- Processing time bar charts
- LaTeX tables
- Summary CSV
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from backend.ai.video_3m.evaluation.metrics import (
    ConfusionMatrixResult,
    CorrelationResult,
    EvaluationMetrics,
    ProcessingTimeResult,
)


class ReportGenerator:
    """
    Generates publication-ready figures and tables from evaluation results.
    All plots use matplotlib (non-interactive Agg backend).
    """

    def __init__(self, output_dir: str = "backend/uploads/evaluation_reports"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_full_report(
        self,
        report,  # FullEvaluationReport
        report_id: str = "eval",
    ) -> dict:
        """
        Generate all plots and tables. Returns dict of file paths.

        Args:
            report: FullEvaluationReport from EvaluationEngine
            report_id: prefix for output filenames
        """
        report_dir = os.path.join(self.output_dir, report_id)
        os.makedirs(report_dir, exist_ok=True)

        files = {}

        # 1. Confusion matrices
        cm_dir = os.path.join(report_dir, "confusion_matrices")
        os.makedirs(cm_dir, exist_ok=True)
        for cm in report.confusion_matrices:
            path = self.plot_confusion_matrix(cm, cm_dir)
            files[f"cm_{cm.component}"] = path

        # 2. Scatter plots
        scatter_dir = os.path.join(report_dir, "scatter_plots")
        os.makedirs(scatter_dir, exist_ok=True)
        for corr in report.correlations:
            path = self.plot_scatter(corr, scatter_dir)
            files[f"scatter_{corr.component}"] = path

        # 3. Bland-Altman plots
        ba_dir = os.path.join(report_dir, "bland_altman")
        os.makedirs(ba_dir, exist_ok=True)
        for corr in report.correlations:
            path = self.plot_bland_altman(corr, ba_dir)
            files[f"ba_{corr.component}"] = path

        # 4. Processing time chart
        if report.processing_times:
            path = self.plot_processing_times(
                report.processing_times,
                os.path.join(report_dir, "processing_times.png"),
            )
            files["processing_times"] = path

        # 5. LaTeX tables
        latex_path = os.path.join(report_dir, "latex_tables.tex")
        self.export_latex(report, latex_path)
        files["latex_tables"] = latex_path

        # 6. Summary CSV
        csv_path = os.path.join(report_dir, "summary.csv")
        self.export_summary_csv(report, csv_path)
        files["summary_csv"] = csv_path

        # 7. Correlation summary chart (all components)
        if report.correlations:
            path = self.plot_correlation_summary(
                report.correlations,
                os.path.join(report_dir, "correlation_summary.png"),
            )
            files["correlation_summary"] = path

        return files

    # ------------------------------------------------------------------
    # Individual plot methods
    # ------------------------------------------------------------------

    def plot_confusion_matrix(
        self,
        cm_result: ConfusionMatrixResult,
        output_dir: str,
    ) -> str:
        """Plot confusion matrix as a heatmap."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(6, 5))

        matrix = np.array(cm_result.matrix)
        labels = cm_result.labels

        im = ax.imshow(matrix, cmap="Blues", aspect="auto")
        plt.colorbar(im, ax=ax)

        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        ax.set_xlabel("Prediksi Sistem (CV)")
        ax.set_ylabel("Ground Truth (Observer)")
        ax.set_title(
            f"Confusion Matrix — {cm_result.component}\n"
            f"Akurasi: {cm_result.accuracy:.2%} | "
            f"F1: {cm_result.f1_score:.3f} | "
            f"κ: {cm_result.cohen_kappa:.3f}"
        )

        # Annotate cells
        for i in range(len(labels)):
            for j in range(len(labels)):
                val = matrix[i][j]
                color = "white" if val > matrix.max() / 2 else "black"
                ax.text(j, i, str(val), ha="center", va="center", color=color,
                        fontweight="bold", fontsize=12)

        plt.tight_layout()
        safe_name = cm_result.component.lower().replace(" ", "_")
        path = os.path.join(output_dir, f"cm_{safe_name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_scatter(
        self,
        corr: CorrelationResult,
        output_dir: str,
    ) -> str:
        """Scatter plot: CV score vs Observer score with regression line."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(6, 5))

        # We don't have raw data in CorrelationResult, so this is a template
        # that will be called with extended data from the benchmark runner.
        # For now, show summary info.
        ax.text(
            0.5, 0.5,
            f"Pearson r = {corr.pearson_r:.3f} (p={corr.pearson_p:.4f})\n"
            f"Spearman ρ = {corr.spearman_rho:.3f}\n"
            f"MAE = {corr.mae:.2f}\n"
            f"RMSE = {corr.rmse:.2f}\n"
            f"N = {corr.n_samples}",
            ha="center", va="center",
            transform=ax.transAxes,
            fontsize=12,
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
        )
        ax.set_title(f"Korelasi — {corr.component}")
        ax.set_xlabel("Skor Observer (Ground Truth)")
        ax.set_ylabel("Skor Sistem (CV)")

        plt.tight_layout()
        safe_name = corr.component.lower().replace(" ", "_")
        path = os.path.join(output_dir, f"scatter_{safe_name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_scatter_with_data(
        self,
        y_true: list,
        y_pred: list,
        component: str,
        output_path: str,
    ) -> str:
        """Scatter plot with actual data points and regression line."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(6, 5))

        ax.scatter(y_true, y_pred, alpha=0.6, edgecolors="navy", s=50)

        # Regression line
        if len(y_true) >= 2:
            z = np.polyfit(y_true, y_pred, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(y_true), max(y_true), 100)
            ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2,
                    label=f"y = {z[0]:.2f}x + {z[1]:.2f}")

        # Perfect agreement line
        all_vals = list(y_true) + list(y_pred)
        mn, mx = min(all_vals), max(all_vals)
        ax.plot([mn, mx], [mn, mx], "k:", alpha=0.4, label="Perfect Agreement")

        from scipy.stats import pearsonr
        r, p_val = pearsonr(y_true, y_pred)

        ax.set_xlabel("Skor Observer (Ground Truth)", fontsize=11)
        ax.set_ylabel("Skor Sistem (CV)", fontsize=11)
        ax.set_title(f"{component}\nr = {r:.3f}, p = {p_val:.4f}, N = {len(y_true)}")
        ax.legend(fontsize=9)

        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_bland_altman(
        self,
        corr: CorrelationResult,
        output_dir: str,
    ) -> str:
        """Bland-Altman plot template showing limits of agreement."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 5))

        ax.axhline(y=corr.mean_diff, color="blue", linestyle="-",
                    label=f"Mean Diff = {corr.mean_diff:.2f}")
        ax.axhline(y=corr.upper_loa, color="red", linestyle="--",
                    label=f"+1.96 SD = {corr.upper_loa:.2f}")
        ax.axhline(y=corr.lower_loa, color="red", linestyle="--",
                    label=f"-1.96 SD = {corr.lower_loa:.2f}")

        ax.set_xlabel("Rata-rata (Observer + CV) / 2")
        ax.set_ylabel("Selisih (CV − Observer)")
        ax.set_title(f"Bland-Altman Plot — {corr.component}")
        ax.legend(fontsize=9)

        plt.tight_layout()
        safe_name = corr.component.lower().replace(" ", "_")
        path = os.path.join(output_dir, f"ba_{safe_name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_bland_altman_with_data(
        self,
        y_true: list,
        y_pred: list,
        component: str,
        output_path: str,
    ) -> str:
        """Bland-Altman plot with actual data points."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)

        means = (y_true + y_pred) / 2.0
        diffs = y_pred - y_true
        mean_diff = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1))

        fig, ax = plt.subplots(figsize=(6, 5))

        ax.scatter(means, diffs, alpha=0.6, edgecolors="navy", s=50)
        ax.axhline(y=mean_diff, color="blue", linestyle="-",
                    label=f"Mean = {mean_diff:.2f}")
        ax.axhline(y=mean_diff + 1.96 * std_diff, color="red", linestyle="--",
                    label=f"+1.96 SD = {mean_diff + 1.96 * std_diff:.2f}")
        ax.axhline(y=mean_diff - 1.96 * std_diff, color="red", linestyle="--",
                    label=f"-1.96 SD = {mean_diff - 1.96 * std_diff:.2f}")

        ax.set_xlabel("Rata-rata (Observer + CV) / 2", fontsize=11)
        ax.set_ylabel("Selisih (CV − Observer)", fontsize=11)
        ax.set_title(f"Bland-Altman — {component} (N={len(y_true)})")
        ax.legend(fontsize=9)

        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_processing_times(
        self,
        times: List[ProcessingTimeResult],
        output_path: str,
    ) -> str:
        """Bar chart of processing times per pipeline stage."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        stages = [t.stage for t in times]
        means = [t.mean_sec for t in times]
        stds = [t.std_sec for t in times]

        fig, ax = plt.subplots(figsize=(8, 5))
        x = range(len(stages))
        bars = ax.bar(x, means, yerr=stds, capsize=5,
                       color=["#3498db", "#e74c3c", "#2ecc71", "#f39c12",
                              "#9b59b6", "#1abc9c"][:len(stages)],
                       edgecolor="white", linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(stages, rotation=30, ha="right")
        ax.set_ylabel("Waktu (detik)")
        ax.set_title("Benchmark Waktu Pemrosesan per Stage Pipeline")

        # Add value labels on bars
        for bar, mean, std in zip(bars, means, stds):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + std + 0.5,
                    f"{mean:.1f}s", ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def plot_correlation_summary(
        self,
        correlations: List[CorrelationResult],
        output_path: str,
    ) -> str:
        """Bar chart comparing Pearson r across all components."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        components = [c.component for c in correlations]
        rs = [c.pearson_r for c in correlations]
        significant = [c.pearson_p < 0.05 for c in correlations]

        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["#2ecc71" if s else "#e74c3c" for s in significant]

        x = range(len(components))
        bars = ax.barh(x, rs, color=colors, edgecolor="white", linewidth=0.5)

        ax.set_yticks(x)
        ax.set_yticklabels(components)
        ax.set_xlabel("Pearson r")
        ax.set_title("Korelasi per Komponen (Hijau = p < 0.05)")
        ax.axvline(x=0, color="black", linewidth=0.5)

        # Add value labels
        for i, (bar, r) in enumerate(zip(bars, rs)):
            ax.text(r + 0.02 if r >= 0 else r - 0.05,
                    i, f"{r:.3f}", va="center", fontsize=9)

        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def export_latex(self, report, output_path: str) -> str:
        """Export all metrics as LaTeX tables."""
        sections = []

        # Title
        sections.append("% ===== Tabel Evaluasi 3M Pipeline =====\n")

        # Correlation table
        if report.correlations:
            sections.append(
                EvaluationMetrics.format_latex_table(report.correlations)
            )
            sections.append("\n")

        # Confusion matrices
        for cm in report.confusion_matrices:
            sections.append(
                EvaluationMetrics.format_confusion_latex(cm)
            )
            sections.append("\n")

        # Inter-rater table
        if report.inter_rater:
            sections.append(self._format_inter_rater_latex(report.inter_rater))

        content = "\n".join(sections)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def export_summary_csv(self, report, output_path: str) -> str:
        """Export summary metrics as CSV."""
        import csv

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Section 1: Confusion Matrix Summary
            writer.writerow(["=== Confusion Matrix Summary ==="])
            writer.writerow(["Component", "Accuracy", "Precision", "Recall",
                             "F1", "Cohen's Kappa"])
            for cm in report.confusion_matrices:
                writer.writerow([
                    cm.component, cm.accuracy, cm.precision,
                    cm.recall, cm.f1_score, cm.cohen_kappa,
                ])
            writer.writerow([])

            # Section 2: Correlation Summary
            writer.writerow(["=== Correlation Summary ==="])
            writer.writerow(["Component", "N", "Pearson r", "p-value",
                             "Spearman rho", "MAE", "RMSE"])
            for c in report.correlations:
                writer.writerow([
                    c.component, c.n_samples, c.pearson_r, c.pearson_p,
                    c.spearman_rho, c.mae, c.rmse,
                ])
            writer.writerow([])

            # Section 3: Processing Times
            if report.processing_times:
                writer.writerow(["=== Processing Times ==="])
                writer.writerow(["Stage", "Mean (s)", "Std (s)", "Min (s)", "Max (s)"])
                for pt in report.processing_times:
                    writer.writerow([
                        pt.stage, f"{pt.mean_sec:.2f}", f"{pt.std_sec:.2f}",
                        f"{pt.min_sec:.2f}", f"{pt.max_sec:.2f}",
                    ])

        return output_path

    def _format_inter_rater_latex(
        self, inter_rater: list,
    ) -> str:
        """Format inter-rater reliability as LaTeX table."""
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Inter-Rater Reliability}",
            r"\label{tab:interrater}",
            r"\begin{tabular}{lccc}",
            r"\hline",
            r"\textbf{Komponen} & \textbf{N Raters} & "
            r"\textbf{Cohen's $\kappa$} & \textbf{ICC} \\",
            r"\hline",
        ]
        for ir in inter_rater:
            kappa_str = f"{ir.cohens_kappa:.3f}" if ir.cohens_kappa else "—"
            icc_str = f"{ir.icc:.3f}" if ir.icc else "—"
            lines.append(
                f"{ir.component} & {ir.n_raters} & {kappa_str} & {icc_str} \\\\"
            )
        lines.extend([r"\hline", r"\end{tabular}", r"\end{table}"])
        return "\n".join(lines)
