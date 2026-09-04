"""
Evaluation metrics for the 3M Computer Vision pipeline.

Computes confusion matrices, classification reports, correlation metrics,
and inter-rater reliability statistics for validating CV outputs against
human observer ground truth annotations.

Designed for use in education research papers — all outputs are formatted
for academic publication (LaTeX tables, APA-style reporting).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ConfusionMatrixResult:
    """Result of a confusion matrix computation for one discrete component."""
    component: str
    labels: List[str]
    matrix: List[List[int]]  # rows=true, cols=predicted
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    cohen_kappa: float = 0.0
    classification_report: str = ""  # text report from sklearn


@dataclass
class CorrelationResult:
    """Result of correlation analysis for one continuous component."""
    component: str
    pearson_r: float = 0.0
    pearson_p: float = 1.0
    spearman_rho: float = 0.0
    spearman_p: float = 1.0
    mae: float = 0.0
    rmse: float = 0.0
    n_samples: int = 0
    # For Bland-Altman
    mean_diff: float = 0.0
    std_diff: float = 0.0
    upper_loa: float = 0.0  # limits of agreement
    lower_loa: float = 0.0


@dataclass
class InterRaterResult:
    """Inter-rater reliability between multiple observers."""
    component: str
    n_raters: int = 0
    cohens_kappa: float = 0.0  # pairwise, averaged
    icc: float = 0.0  # intraclass correlation coefficient
    agreement_pct: float = 0.0  # simple % agreement


@dataclass
class ProcessingTimeResult:
    """Timing benchmark for a pipeline stage."""
    stage: str
    times_sec: List[float] = field(default_factory=list)

    @property
    def mean_sec(self) -> float:
        return float(np.mean(self.times_sec)) if self.times_sec else 0.0

    @property
    def std_sec(self) -> float:
        return float(np.std(self.times_sec)) if self.times_sec else 0.0

    @property
    def min_sec(self) -> float:
        return float(np.min(self.times_sec)) if self.times_sec else 0.0

    @property
    def max_sec(self) -> float:
        return float(np.max(self.times_sec)) if self.times_sec else 0.0


# ---------------------------------------------------------------------------
# Metrics Calculator
# ---------------------------------------------------------------------------

class EvaluationMetrics:
    """
    Stateless utility class that computes all evaluation metrics.

    Methods accept raw arrays and return typed result objects.
    All heavy dependencies (sklearn, scipy) are imported lazily.
    """

    # ------------------------------------------------------------------
    # Discrete (classification) metrics
    # ------------------------------------------------------------------

    @staticmethod
    def confusion_matrix(
        y_true: List[str],
        y_pred: List[str],
        component: str,
        labels: Optional[List[str]] = None,
    ) -> ConfusionMatrixResult:
        """
        Compute confusion matrix + classification report for a discrete
        classification component (e.g. seating formation, on-task/off-task).
        """
        from sklearn.metrics import (
            confusion_matrix as sk_cm,
            accuracy_score,
            precision_recall_fscore_support,
            cohen_kappa_score,
            classification_report,
        )

        if labels is None:
            labels = sorted(set(y_true) | set(y_pred))

        cm = sk_cm(y_true, y_pred, labels=labels)
        acc = accuracy_score(y_true, y_pred)
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="weighted", zero_division=0,
        )
        kappa = cohen_kappa_score(y_true, y_pred)
        report = classification_report(
            y_true, y_pred, labels=labels, zero_division=0,
        )

        return ConfusionMatrixResult(
            component=component,
            labels=labels,
            matrix=cm.tolist(),
            accuracy=round(acc, 4),
            precision=round(p, 4),
            recall=round(r, 4),
            f1_score=round(f1, 4),
            cohen_kappa=round(kappa, 4),
            classification_report=report,
        )

    @staticmethod
    def binarize_and_evaluate(
        y_true_continuous: List[float],
        y_pred_continuous: List[float],
        component: str,
        threshold: float = 0.5,
        positive_label: str = "Engaged",
        negative_label: str = "Not Engaged",
    ) -> ConfusionMatrixResult:
        """
        Binarize continuous scores using a threshold, then compute
        confusion matrix. Useful for gaze on-task and posture metrics.
        """
        labels = [negative_label, positive_label]
        y_true_bin = [
            positive_label if v >= threshold else negative_label
            for v in y_true_continuous
        ]
        y_pred_bin = [
            positive_label if v >= threshold else negative_label
            for v in y_pred_continuous
        ]
        return EvaluationMetrics.confusion_matrix(
            y_true_bin, y_pred_bin, component, labels,
        )

    # ------------------------------------------------------------------
    # Continuous (regression/correlation) metrics
    # ------------------------------------------------------------------

    @staticmethod
    def correlation(
        y_true: List[float],
        y_pred: List[float],
        component: str,
    ) -> CorrelationResult:
        """
        Compute Pearson r, Spearman ρ, MAE, RMSE, and Bland-Altman
        statistics for a continuous score component.
        """
        from scipy.stats import pearsonr, spearmanr
        from sklearn.metrics import mean_absolute_error

        arr_true = np.array(y_true, dtype=float)
        arr_pred = np.array(y_pred, dtype=float)
        n = len(arr_true)

        if n < 3:
            return CorrelationResult(component=component, n_samples=n)

        # Pearson
        pr, pp = pearsonr(arr_true, arr_pred)
        # Spearman
        sr, sp = spearmanr(arr_true, arr_pred)
        # MAE
        mae = mean_absolute_error(arr_true, arr_pred)
        # RMSE
        rmse = float(np.sqrt(np.mean((arr_true - arr_pred) ** 2)))

        # Bland-Altman
        diffs = arr_pred - arr_true
        mean_diff = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
        upper_loa = mean_diff + 1.96 * std_diff
        lower_loa = mean_diff - 1.96 * std_diff

        return CorrelationResult(
            component=component,
            pearson_r=round(float(pr), 4),
            pearson_p=round(float(pp), 6),
            spearman_rho=round(float(sr), 4),
            spearman_p=round(float(sp), 6),
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            n_samples=n,
            mean_diff=round(mean_diff, 4),
            std_diff=round(std_diff, 4),
            upper_loa=round(upper_loa, 4),
            lower_loa=round(lower_loa, 4),
        )

    # ------------------------------------------------------------------
    # Inter-rater reliability
    # ------------------------------------------------------------------

    @staticmethod
    def inter_rater_agreement(
        ratings: Dict[str, List],
        component: str,
        is_continuous: bool = True,
    ) -> InterRaterResult:
        """
        Compute inter-rater reliability from multiple annotators.

        Args:
            ratings: dict mapping annotator_name → list of ratings
                     (one per fragment, same order)
            component: name of the scored component
            is_continuous: if True, compute ICC; if False, compute Cohen's κ
        """
        rater_names = list(ratings.keys())
        n_raters = len(rater_names)

        if n_raters < 2:
            return InterRaterResult(component=component, n_raters=n_raters)

        if is_continuous:
            # ICC (two-way random, single measures, consistency)
            icc = EvaluationMetrics._compute_icc(ratings)
            return InterRaterResult(
                component=component,
                n_raters=n_raters,
                icc=round(icc, 4),
            )
        else:
            # Pairwise Cohen's κ, averaged
            from sklearn.metrics import cohen_kappa_score
            kappas = []
            for i in range(n_raters):
                for j in range(i + 1, n_raters):
                    r1 = ratings[rater_names[i]]
                    r2 = ratings[rater_names[j]]
                    k = cohen_kappa_score(r1, r2)
                    kappas.append(k)

            avg_kappa = float(np.mean(kappas)) if kappas else 0.0

            # Simple agreement %
            all_pairs_agree = 0
            all_pairs_total = 0
            for i in range(n_raters):
                for j in range(i + 1, n_raters):
                    r1 = ratings[rater_names[i]]
                    r2 = ratings[rater_names[j]]
                    agrees = sum(a == b for a, b in zip(r1, r2))
                    all_pairs_agree += agrees
                    all_pairs_total += len(r1)

            agreement_pct = (
                (all_pairs_agree / all_pairs_total * 100)
                if all_pairs_total > 0 else 0.0
            )

            return InterRaterResult(
                component=component,
                n_raters=n_raters,
                cohens_kappa=round(avg_kappa, 4),
                agreement_pct=round(agreement_pct, 2),
            )

    @staticmethod
    def _compute_icc(ratings: Dict[str, List]) -> float:
        """
        ICC(2,1) — two-way random, single measures, consistency.
        Implementation follows Shrout & Fleiss (1979).
        """
        rater_names = list(ratings.keys())
        n_subjects = len(ratings[rater_names[0]])
        k = len(rater_names)

        if n_subjects < 2 or k < 2:
            return 0.0

        # Build rating matrix: subjects × raters
        data = np.array([ratings[r] for r in rater_names], dtype=float).T
        # data shape: (n_subjects, k)

        n = data.shape[0]
        grand_mean = np.mean(data)

        # Sum of squares
        ss_rows = k * np.sum((np.mean(data, axis=1) - grand_mean) ** 2)
        ss_cols = n * np.sum((np.mean(data, axis=0) - grand_mean) ** 2)
        ss_total = np.sum((data - grand_mean) ** 2)
        ss_error = ss_total - ss_rows - ss_cols

        # Mean squares
        ms_rows = ss_rows / (n - 1) if n > 1 else 0
        ms_error = ss_error / ((n - 1) * (k - 1)) if (n > 1 and k > 1) else 0
        ms_cols = ss_cols / (k - 1) if k > 1 else 0

        # ICC(2,1) = (MS_rows - MS_error) / (MS_rows + (k-1)*MS_error + k*(MS_cols - MS_error)/n)
        denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
        if denom == 0:
            return 0.0

        icc = (ms_rows - ms_error) / denom
        return max(-1.0, min(1.0, icc))

    # ------------------------------------------------------------------
    # Utility: format for LaTeX
    # ------------------------------------------------------------------

    @staticmethod
    def format_latex_table(
        correlations: List[CorrelationResult],
        caption: str = "Korelasi Skor Sistem vs Observasi Manual",
    ) -> str:
        """Generate a LaTeX table from correlation results."""
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            f"\\caption{{{caption}}}",
            r"\label{tab:correlation}",
            r"\begin{tabular}{lcccccc}",
            r"\hline",
            r"\textbf{Komponen} & \textbf{N} & \textbf{Pearson $r$} & "
            r"\textbf{$p$} & \textbf{Spearman $\rho$} & \textbf{MAE} & "
            r"\textbf{RMSE} \\",
            r"\hline",
        ]
        for c in correlations:
            p_str = f"{c.pearson_p:.4f}" if c.pearson_p >= 0.0001 else "<0.0001"
            lines.append(
                f"{c.component} & {c.n_samples} & {c.pearson_r:.3f} & "
                f"{p_str} & {c.spearman_rho:.3f} & {c.mae:.2f} & "
                f"{c.rmse:.2f} \\\\"
            )
        lines.extend([
            r"\hline",
            r"\end{tabular}",
            r"\end{table}",
        ])
        return "\n".join(lines)

    @staticmethod
    def format_confusion_latex(
        cm_result: ConfusionMatrixResult,
        caption: Optional[str] = None,
    ) -> str:
        """Generate a LaTeX table from a confusion matrix."""
        labels = cm_result.labels
        matrix = cm_result.matrix
        n = len(labels)

        if caption is None:
            caption = f"Confusion Matrix — {cm_result.component}"

        col_spec = "l" + "c" * n
        header_labels = " & ".join([f"\\textbf{{{l}}}" for l in labels])

        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{tab:cm_{cm_result.component.lower().replace(' ', '_')}}}",
            f"\\begin{{tabular}}{{{col_spec}}}",
            r"\hline",
            f"& {header_labels} \\\\",
            r"\hline",
        ]

        for i, label in enumerate(labels):
            row_vals = " & ".join(str(v) for v in matrix[i])
            lines.append(f"\\textbf{{{label}}} & {row_vals} \\\\")

        lines.extend([
            r"\hline",
            r"\end{tabular}",
            "",
            f"Akurasi: {cm_result.accuracy:.2%}, "
            f"F1: {cm_result.f1_score:.4f}, "
            f"$\\kappa$: {cm_result.cohen_kappa:.4f}",
            r"\end{table}",
        ])
        return "\n".join(lines)
