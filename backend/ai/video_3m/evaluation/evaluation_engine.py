"""
EvaluationEngine — orchestrates the full evaluation of CV pipeline outputs
against human observer ground truth annotations.

Usage:
    engine = EvaluationEngine(db_session)
    report = engine.evaluate_job("job-id-here")
    # or batch:
    report = engine.evaluate_batch(["job-1", "job-2", ...])
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.ai.video_3m.evaluation.metrics import (
    ConfusionMatrixResult,
    CorrelationResult,
    EvaluationMetrics,
    InterRaterResult,
    ProcessingTimeResult,
)


@dataclass
class FullEvaluationReport:
    """Complete evaluation report for one or more video analysis jobs."""
    job_ids: List[str] = field(default_factory=list)
    total_fragments: int = 0
    total_annotators: int = 0

    # Per-component results
    confusion_matrices: List[ConfusionMatrixResult] = field(default_factory=list)
    correlations: List[CorrelationResult] = field(default_factory=list)
    inter_rater: List[InterRaterResult] = field(default_factory=list)
    processing_times: List[ProcessingTimeResult] = field(default_factory=list)

    # Summary statistics
    mean_pearson_r: float = 0.0
    mean_f1: float = 0.0
    mean_kappa: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "job_ids": self.job_ids,
            "total_fragments": self.total_fragments,
            "total_annotators": self.total_annotators,
            "confusion_matrices": [
                {
                    "component": cm.component,
                    "labels": cm.labels,
                    "matrix": cm.matrix,
                    "accuracy": cm.accuracy,
                    "precision": cm.precision,
                    "recall": cm.recall,
                    "f1_score": cm.f1_score,
                    "cohen_kappa": cm.cohen_kappa,
                    "classification_report": cm.classification_report,
                }
                for cm in self.confusion_matrices
            ],
            "correlations": [
                {
                    "component": c.component,
                    "pearson_r": c.pearson_r,
                    "pearson_p": c.pearson_p,
                    "spearman_rho": c.spearman_rho,
                    "spearman_p": c.spearman_p,
                    "mae": c.mae,
                    "rmse": c.rmse,
                    "n_samples": c.n_samples,
                    "mean_diff": c.mean_diff,
                    "std_diff": c.std_diff,
                    "upper_loa": c.upper_loa,
                    "lower_loa": c.lower_loa,
                }
                for c in self.correlations
            ],
            "inter_rater": [
                {
                    "component": ir.component,
                    "n_raters": ir.n_raters,
                    "cohens_kappa": ir.cohens_kappa,
                    "icc": ir.icc,
                    "agreement_pct": ir.agreement_pct,
                }
                for ir in self.inter_rater
            ],
            "processing_times": [
                {
                    "stage": pt.stage,
                    "mean_sec": pt.mean_sec,
                    "std_sec": pt.std_sec,
                    "min_sec": pt.min_sec,
                    "max_sec": pt.max_sec,
                }
                for pt in self.processing_times
            ],
            "summary": {
                "mean_pearson_r": self.mean_pearson_r,
                "mean_f1": self.mean_f1,
                "mean_kappa": self.mean_kappa,
            },
        }


class EvaluationEngine:
    """
    Orchestrates evaluation by:
    1. Loading CV results from DB (VideoFragment3M)
    2. Loading ground truth annotations (GroundTruthAnnotation)
    3. Pairing them per fragment
    4. Computing all metrics via EvaluationMetrics
    5. Returning a FullEvaluationReport
    """

    def __init__(self, db_session=None):
        self._db = db_session
        self._metrics = EvaluationMetrics()

    def evaluate_job(self, job_id: str) -> FullEvaluationReport:
        """Evaluate a single completed job against its ground truth annotations."""
        return self.evaluate_batch([job_id])

    def evaluate_batch(self, job_ids: List[str]) -> FullEvaluationReport:
        """Evaluate multiple jobs against their ground truth annotations."""
        from backend.models.db_models import VideoFragment3M
        from backend.models.ground_truth_models import GroundTruthAnnotation

        # ── 1. Load data ──────────────────────────────────────────────
        all_fragments = []
        all_annotations = []

        for job_id in job_ids:
            fragments = (
                self._db.query(VideoFragment3M)
                .filter(VideoFragment3M.job_id == job_id)
                .order_by(VideoFragment3M.fragment_index)
                .all()
            )
            annotations = (
                self._db.query(GroundTruthAnnotation)
                .filter(GroundTruthAnnotation.job_id == job_id)
                .all()
            )
            all_fragments.extend(fragments)
            all_annotations.extend(annotations)

        if not all_fragments or not all_annotations:
            return FullEvaluationReport(
                job_ids=job_ids,
                total_fragments=len(all_fragments),
            )

        # ── 2. Group annotations by (job_id, fragment_index) ──────────
        # For each fragment, pick the first annotator's data as primary GT.
        # If multiple annotators exist, also compute inter-rater.
        gt_map: Dict[str, dict] = {}  # key = "job_id:fragment_index"
        annotator_groups: Dict[str, Dict[str, list]] = {}  # for inter-rater

        annotator_names = set()
        for ann in all_annotations:
            key = f"{ann.job_id}:{ann.fragment_index}"
            annotator_names.add(ann.annotator_name)
            if key not in gt_map:
                gt_map[key] = {
                    "gaze_on_task_ratio": ann.gaze_on_task_ratio,
                    "posture_engaged_ratio": ann.posture_engaged_ratio,
                    "seating_formation": ann.seating_formation,
                    "teacher_in_active_zone": ann.teacher_in_active_zone,
                    "positive_expression_ratio": ann.positive_expression_ratio,
                    "hand_raise_count": ann.hand_raise_count,
                    "mindful_score_gt": ann.mindful_score_gt,
                    "meaningful_score_gt": ann.meaningful_score_gt,
                    "joyful_score_gt": ann.joyful_score_gt,
                    "overall_3m_score_gt": ann.overall_3m_score_gt,
                    "teacher_talk_pct_gt": ann.teacher_talk_pct_gt,
                }

            # Track all annotators for inter-rater
            if key not in annotator_groups:
                annotator_groups[key] = {}
            annotator_groups[key][ann.annotator_name] = ann

        # ── 3. Build paired arrays ────────────────────────────────────
        # CV predictions vs Ground Truth
        pairs = self._build_pairs(all_fragments, gt_map)

        # ── 4. Compute metrics ────────────────────────────────────────
        report = FullEvaluationReport(
            job_ids=job_ids,
            total_fragments=len(pairs),
            total_annotators=len(annotator_names),
        )

        # 4a. Confusion matrices (discrete components)
        report.confusion_matrices = self._compute_confusion_matrices(pairs)

        # 4b. Correlation metrics (continuous components)
        report.correlations = self._compute_correlations(pairs)

        # 4c. Inter-rater reliability (if multiple annotators)
        if len(annotator_names) > 1:
            report.inter_rater = self._compute_inter_rater(
                all_annotations, annotator_names,
            )

        # 4d. Summary statistics
        if report.correlations:
            valid_r = [c.pearson_r for c in report.correlations if c.n_samples >= 3]
            report.mean_pearson_r = round(
                sum(valid_r) / len(valid_r), 4
            ) if valid_r else 0.0

        if report.confusion_matrices:
            f1s = [cm.f1_score for cm in report.confusion_matrices]
            kappas = [cm.cohen_kappa for cm in report.confusion_matrices]
            report.mean_f1 = round(sum(f1s) / len(f1s), 4) if f1s else 0.0
            report.mean_kappa = round(
                sum(kappas) / len(kappas), 4
            ) if kappas else 0.0

        return report

    # ------------------------------------------------------------------
    # Evaluate from raw data (no DB) — used by benchmark_runner
    # ------------------------------------------------------------------

    def evaluate_from_data(
        self,
        cv_fragments: List[dict],
        gt_fragments: List[dict],
    ) -> FullEvaluationReport:
        """
        Evaluate using in-memory data dicts (no DB required).
        Each dict must have keys matching the paired data format.
        """
        pairs = []
        for cv, gt in zip(cv_fragments, gt_fragments):
            pairs.append({"cv": cv, "gt": gt})

        report = FullEvaluationReport(
            total_fragments=len(pairs),
        )
        report.confusion_matrices = self._compute_confusion_matrices(pairs)
        report.correlations = self._compute_correlations(pairs)

        if report.correlations:
            valid_r = [c.pearson_r for c in report.correlations if c.n_samples >= 3]
            report.mean_pearson_r = round(
                sum(valid_r) / len(valid_r), 4
            ) if valid_r else 0.0

        if report.confusion_matrices:
            f1s = [cm.f1_score for cm in report.confusion_matrices]
            report.mean_f1 = round(sum(f1s) / len(f1s), 4) if f1s else 0.0

        return report

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_pairs(self, fragments, gt_map) -> List[dict]:
        """Pair CV fragment results with ground truth by (job_id, index)."""
        pairs = []
        for frag in fragments:
            key = f"{frag.job_id}:{frag.fragment_index}"
            if key not in gt_map:
                continue  # no ground truth for this fragment

            gt = gt_map[key]
            cv = {
                "gaze_score": frag.gaze_score,
                "posture_score": frag.posture_score,
                "mindful_score": frag.mindful_score,
                "seating_formation": frag.seating_formation,
                "teacher_movement_score": frag.teacher_movement_score,
                "meaningful_score": frag.meaningful_score,
                "expression_score": frag.expression_score,
                "joyful_score": frag.joyful_score,
                "active_zone_ratio": frag.active_zone_ratio,
                "teacher_talk_pct": frag.teacher_talk_pct,
            }
            pairs.append({"cv": cv, "gt": gt})

        return pairs

    def _compute_confusion_matrices(
        self, pairs: List[dict],
    ) -> List[ConfusionMatrixResult]:
        """Compute confusion matrices for all discrete components."""
        results = []

        # 1. Seating Formation (rows / groups / circle)
        seating_true = []
        seating_pred = []
        for p in pairs:
            gt_seat = p["gt"].get("seating_formation")
            cv_seat = p["cv"].get("seating_formation")
            if gt_seat and cv_seat:
                seating_true.append(gt_seat)
                seating_pred.append(cv_seat)

        if len(seating_true) >= 2:
            results.append(self._metrics.confusion_matrix(
                seating_true, seating_pred,
                component="Seating Formation",
                labels=["rows", "groups", "circle"],
            ))

        # 2. Gaze On-Task (binarized: ≥0.5 → on-task)
        gaze_true = []
        gaze_pred = []
        for p in pairs:
            gt_gaze = p["gt"].get("gaze_on_task_ratio")
            cv_gaze = p["cv"].get("gaze_score")
            if gt_gaze is not None and cv_gaze is not None:
                gaze_true.append(gt_gaze)
                gaze_pred.append(cv_gaze / 100.0)  # normalize to [0,1]

        if len(gaze_true) >= 2:
            results.append(self._metrics.binarize_and_evaluate(
                gaze_true, gaze_pred,
                component="Gaze On-Task",
                threshold=0.5,
                positive_label="On-Task",
                negative_label="Off-Task",
            ))

        # 3. Posture Engaged (binarized: ≥0.5 → engaged)
        posture_true = []
        posture_pred = []
        for p in pairs:
            gt_post = p["gt"].get("posture_engaged_ratio")
            cv_post = p["cv"].get("posture_score")
            if gt_post is not None and cv_post is not None:
                posture_true.append(gt_post)
                posture_pred.append(cv_post / 100.0)

        if len(posture_true) >= 2:
            results.append(self._metrics.binarize_and_evaluate(
                posture_true, posture_pred,
                component="Posture Engaged",
                threshold=0.5,
                positive_label="Engaged",
                negative_label="Not Engaged",
            ))

        # 4. Teacher in Active Zone (binary)
        tz_true = []
        tz_pred = []
        for p in pairs:
            gt_tz = p["gt"].get("teacher_in_active_zone")
            cv_azr = p["cv"].get("active_zone_ratio")
            if gt_tz is not None and cv_azr is not None:
                tz_true.append("Active" if gt_tz else "Static")
                tz_pred.append("Active" if cv_azr > 0.5 else "Static")

        if len(tz_true) >= 2:
            results.append(self._metrics.confusion_matrix(
                tz_true, tz_pred,
                component="Teacher Active Zone",
                labels=["Static", "Active"],
            ))

        return results

    def _compute_correlations(
        self, pairs: List[dict],
    ) -> List[CorrelationResult]:
        """Compute correlation metrics for all continuous score components."""
        results = []

        # Define continuous component mappings: (name, gt_key, cv_key, scale_factor)
        component_map = [
            ("Gaze Score", "gaze_on_task_ratio", "gaze_score", 100.0),
            ("Posture Score", "posture_engaged_ratio", "posture_score", 100.0),
            ("Mindful Score", "mindful_score_gt", "mindful_score", 1.0),
            ("Meaningful Score", "meaningful_score_gt", "meaningful_score", 1.0),
            ("Expression Score", "positive_expression_ratio", "expression_score", 100.0),
            ("Joyful Score", "joyful_score_gt", "joyful_score", 1.0),
            ("Overall 3M Score", "overall_3m_score_gt", "mindful_score", 1.0),
            # Note: overall_3m_score is computed from aggregation, not per-fragment
            ("Teacher Talk %", "teacher_talk_pct_gt", "teacher_talk_pct", 1.0),
        ]

        for name, gt_key, cv_key, scale in component_map:
            y_true = []
            y_pred = []
            for p in pairs:
                gt_val = p["gt"].get(gt_key)
                cv_val = p["cv"].get(cv_key)
                if gt_val is not None and cv_val is not None:
                    # Scale GT to match CV range (both should be 0-100)
                    y_true.append(gt_val * scale)
                    y_pred.append(cv_val)

            if len(y_true) >= 3:
                results.append(self._metrics.correlation(y_true, y_pred, name))

        return results

    def _compute_inter_rater(
        self,
        annotations,
        annotator_names: set,
    ) -> List[InterRaterResult]:
        """Compute inter-rater reliability for continuous scores."""
        results = []

        # Group annotations by fragment
        fragment_map: Dict[str, Dict[str, object]] = {}
        for ann in annotations:
            key = f"{ann.job_id}:{ann.fragment_index}"
            if key not in fragment_map:
                fragment_map[key] = {}
            fragment_map[key][ann.annotator_name] = ann

        # Only use fragments that have annotations from ALL raters
        all_rater_names = sorted(annotator_names)
        common_keys = [
            k for k, v in fragment_map.items()
            if all(r in v for r in all_rater_names)
        ]

        if len(common_keys) < 2:
            return results

        # Continuous components for inter-rater
        ir_components = [
            ("Mindful Score (GT)", "mindful_score_gt", True),
            ("Meaningful Score (GT)", "meaningful_score_gt", True),
            ("Joyful Score (GT)", "joyful_score_gt", True),
            ("Overall 3M Score (GT)", "overall_3m_score_gt", True),
            ("Seating Formation (GT)", "seating_formation", False),
        ]

        for name, attr, is_continuous in ir_components:
            ratings = {}
            for rater in all_rater_names:
                vals = []
                for key in common_keys:
                    ann = fragment_map[key][rater]
                    val = getattr(ann, attr, None)
                    if val is None:
                        break
                    vals.append(val)
                else:
                    ratings[rater] = vals

            if len(ratings) >= 2:
                results.append(
                    self._metrics.inter_rater_agreement(
                        ratings, name, is_continuous,
                    )
                )

        return results
