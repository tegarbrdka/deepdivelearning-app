"""
Unit tests for the 3M evaluation metrics and engine.

Tests cover:
- Confusion matrix computation
- Binarized classification
- Correlation metrics (Pearson, Spearman, MAE, RMSE)
- Bland-Altman statistics
- Inter-rater reliability (ICC, Cohen's κ)
- LaTeX table generation
- EvaluationEngine.evaluate_from_data()
"""
import pytest
import math
from typing import List


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_seating_data():
    """Sample seating formation predictions vs ground truth."""
    return {
        "y_true": ["rows", "groups", "groups", "circle", "rows", "groups",
                    "circle", "groups", "rows", "groups"],
        "y_pred": ["rows", "groups", "rows", "circle", "rows", "groups",
                    "groups", "groups", "rows", "circle"],
    }


@pytest.fixture
def sample_continuous_data():
    """Sample continuous scores: ground truth vs CV prediction."""
    return {
        "y_true": [75.0, 82.0, 60.0, 91.0, 45.0, 70.0, 88.0, 55.0, 78.0, 65.0],
        "y_pred": [72.0, 80.0, 58.0, 85.0, 50.0, 68.0, 90.0, 52.0, 75.0, 62.0],
    }


@pytest.fixture
def sample_binary_data():
    """Sample gaze on-task ratios for binarized evaluation."""
    return {
        "y_true": [0.9, 0.8, 0.3, 0.7, 0.6, 0.2, 0.95, 0.4, 0.85, 0.1],
        "y_pred": [0.85, 0.75, 0.4, 0.65, 0.55, 0.25, 0.9, 0.35, 0.8, 0.15],
    }


@pytest.fixture
def sample_inter_rater_data():
    """Sample ratings from 3 raters for inter-rater reliability."""
    return {
        "Observer A": [75.0, 82.0, 60.0, 91.0, 45.0],
        "Observer B": [72.0, 85.0, 58.0, 88.0, 48.0],
        "Observer C": [78.0, 80.0, 62.0, 90.0, 43.0],
    }


# ---------------------------------------------------------------------------
# Test EvaluationMetrics
# ---------------------------------------------------------------------------

class TestConfusionMatrix:
    def test_basic_confusion_matrix(self, sample_seating_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.confusion_matrix(
            sample_seating_data["y_true"],
            sample_seating_data["y_pred"],
            component="Seating Formation",
            labels=["rows", "groups", "circle"],
        )

        assert result.component == "Seating Formation"
        assert len(result.labels) == 3
        assert len(result.matrix) == 3
        assert len(result.matrix[0]) == 3
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.f1_score <= 1.0
        assert -1.0 <= result.cohen_kappa <= 1.0
        assert result.classification_report != ""

    def test_perfect_classification(self):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        y = ["rows", "groups", "circle", "rows", "groups"]
        result = EvaluationMetrics.confusion_matrix(y, y, "Perfect")

        assert result.accuracy == 1.0
        assert result.f1_score == 1.0
        assert result.cohen_kappa == 1.0

    def test_binarize_and_evaluate(self, sample_binary_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.binarize_and_evaluate(
            sample_binary_data["y_true"],
            sample_binary_data["y_pred"],
            component="Gaze On-Task",
            threshold=0.5,
        )

        assert result.component == "Gaze On-Task"
        assert "Engaged" in result.labels
        assert "Not Engaged" in result.labels
        assert 0.0 <= result.accuracy <= 1.0


class TestCorrelation:
    def test_basic_correlation(self, sample_continuous_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.correlation(
            sample_continuous_data["y_true"],
            sample_continuous_data["y_pred"],
            component="Mindful Score",
        )

        assert result.component == "Mindful Score"
        assert result.n_samples == 10
        assert 0.9 <= result.pearson_r <= 1.0  # highly correlated data
        assert result.pearson_p < 0.05
        assert result.mae > 0
        assert result.rmse > 0
        assert result.rmse >= result.mae  # RMSE ≥ MAE always

    def test_bland_altman_stats(self, sample_continuous_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.correlation(
            sample_continuous_data["y_true"],
            sample_continuous_data["y_pred"],
            component="Test",
        )

        # Mean diff should reflect that predictions are slightly lower
        assert isinstance(result.mean_diff, float)
        assert isinstance(result.std_diff, float)
        # Upper LOA > Lower LOA
        assert result.upper_loa > result.lower_loa

    def test_perfect_correlation(self):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        y = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = EvaluationMetrics.correlation(y, y, "Perfect")

        assert abs(result.pearson_r - 1.0) < 0.001
        assert result.mae == 0.0
        assert result.rmse == 0.0

    def test_too_few_samples(self):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.correlation([1.0, 2.0], [1.5, 2.5], "Small")
        # Should return with n_samples=2 and default values
        assert result.n_samples == 2


class TestInterRater:
    def test_icc_computation(self, sample_inter_rater_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.inter_rater_agreement(
            sample_inter_rater_data,
            component="Mindful Score",
            is_continuous=True,
        )

        assert result.n_raters == 3
        assert result.icc > 0.5  # should be high for similar ratings

    def test_discrete_inter_rater(self):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        ratings = {
            "A": ["rows", "groups", "circle", "groups", "rows"],
            "B": ["rows", "groups", "circle", "rows", "rows"],
        }
        result = EvaluationMetrics.inter_rater_agreement(
            ratings, "Seating", is_continuous=False,
        )

        assert result.n_raters == 2
        assert -1.0 <= result.cohens_kappa <= 1.0
        assert 0.0 <= result.agreement_pct <= 100.0

    def test_single_rater(self):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        result = EvaluationMetrics.inter_rater_agreement(
            {"A": [1, 2, 3]}, "Test", is_continuous=True,
        )
        assert result.n_raters == 1
        assert result.icc == 0.0


class TestLatexOutput:
    def test_correlation_latex_table(self, sample_continuous_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        corr = EvaluationMetrics.correlation(
            sample_continuous_data["y_true"],
            sample_continuous_data["y_pred"],
            "Mindful Score",
        )
        latex = EvaluationMetrics.format_latex_table([corr])

        assert r"\begin{table}" in latex
        assert "Mindful Score" in latex
        assert r"\end{table}" in latex

    def test_confusion_matrix_latex(self, sample_seating_data):
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics

        cm = EvaluationMetrics.confusion_matrix(
            sample_seating_data["y_true"],
            sample_seating_data["y_pred"],
            "Seating",
            ["rows", "groups", "circle"],
        )
        latex = EvaluationMetrics.format_confusion_latex(cm)

        assert r"\begin{table}" in latex
        assert "rows" in latex


# ---------------------------------------------------------------------------
# Test EvaluationEngine (in-memory evaluation)
# ---------------------------------------------------------------------------

class TestEvaluationEngine:
    def test_evaluate_from_data(self):
        from backend.ai.video_3m.evaluation.evaluation_engine import EvaluationEngine

        engine = EvaluationEngine()

        cv_fragments = [
            {
                "gaze_score": 85.0,
                "posture_score": 70.0,
                "mindful_score": 75.0,
                "seating_formation": "groups",
                "teacher_movement_score": 80.0,
                "meaningful_score": 72.0,
                "expression_score": 60.0,
                "joyful_score": 65.0,
                "active_zone_ratio": 0.7,
                "teacher_talk_pct": 35.0,
            },
            {
                "gaze_score": 60.0,
                "posture_score": 55.0,
                "mindful_score": 58.0,
                "seating_formation": "rows",
                "teacher_movement_score": 40.0,
                "meaningful_score": 45.0,
                "expression_score": 50.0,
                "joyful_score": 48.0,
                "active_zone_ratio": 0.3,
                "teacher_talk_pct": 60.0,
            },
            {
                "gaze_score": 92.0,
                "posture_score": 88.0,
                "mindful_score": 90.0,
                "seating_formation": "circle",
                "teacher_movement_score": 95.0,
                "meaningful_score": 88.0,
                "expression_score": 80.0,
                "joyful_score": 82.0,
                "active_zone_ratio": 0.9,
                "teacher_talk_pct": 30.0,
            },
        ]

        gt_fragments = [
            {
                "gaze_on_task_ratio": 0.80,
                "posture_engaged_ratio": 0.75,
                "mindful_score_gt": 78.0,
                "seating_formation": "groups",
                "teacher_in_active_zone": True,
                "teacher_talk_pct_gt": 33.0,
                "meaningful_score_gt": 74.0,
                "positive_expression_ratio": 0.55,
                "joyful_score_gt": 62.0,
                "overall_3m_score_gt": 72.0,
            },
            {
                "gaze_on_task_ratio": 0.55,
                "posture_engaged_ratio": 0.50,
                "mindful_score_gt": 55.0,
                "seating_formation": "rows",
                "teacher_in_active_zone": False,
                "teacher_talk_pct_gt": 65.0,
                "meaningful_score_gt": 42.0,
                "positive_expression_ratio": 0.45,
                "joyful_score_gt": 45.0,
                "overall_3m_score_gt": 48.0,
            },
            {
                "gaze_on_task_ratio": 0.90,
                "posture_engaged_ratio": 0.85,
                "mindful_score_gt": 88.0,
                "seating_formation": "circle",
                "teacher_in_active_zone": True,
                "teacher_talk_pct_gt": 28.0,
                "meaningful_score_gt": 85.0,
                "positive_expression_ratio": 0.75,
                "joyful_score_gt": 80.0,
                "overall_3m_score_gt": 85.0,
            },
        ]

        report = engine.evaluate_from_data(cv_fragments, gt_fragments)

        assert report.total_fragments == 3
        assert len(report.confusion_matrices) > 0
        assert len(report.correlations) > 0

        # Check confusion matrix for seating
        seating_cm = next(
            (cm for cm in report.confusion_matrices if "Seating" in cm.component),
            None,
        )
        assert seating_cm is not None
        assert seating_cm.accuracy == 1.0  # all seating predictions match

    def test_report_to_dict(self):
        from backend.ai.video_3m.evaluation.evaluation_engine import (
            EvaluationEngine, FullEvaluationReport,
        )

        report = FullEvaluationReport(
            job_ids=["test-123"],
            total_fragments=5,
        )
        d = report.to_dict()

        assert isinstance(d, dict)
        assert d["job_ids"] == ["test-123"]
        assert d["total_fragments"] == 5


# ---------------------------------------------------------------------------
# Test PipelineTimer
# ---------------------------------------------------------------------------

class TestPipelineTimer:
    def test_context_manager(self):
        import time
        from backend.ai.video_3m.evaluation.benchmark_timer import PipelineTimer

        timer = PipelineTimer()

        with timer.stage("test_stage"):
            time.sleep(0.05)

        results = timer.get_results()
        assert len(results) == 1
        assert results[0].stage == "test_stage"
        assert results[0].mean_sec >= 0.04  # at least ~40ms

    def test_start_stop(self):
        import time
        from backend.ai.video_3m.evaluation.benchmark_timer import PipelineTimer

        timer = PipelineTimer()
        timer.start("manual_stage")
        time.sleep(0.05)
        elapsed = timer.stop()

        assert elapsed >= 0.04
        report = timer.get_report()
        assert "manual_stage" in report

    def test_multiple_stages(self):
        from backend.ai.video_3m.evaluation.benchmark_timer import PipelineTimer

        timer = PipelineTimer()
        timer.record("stage_a", 1.5)
        timer.record("stage_a", 2.0)
        timer.record("stage_b", 3.0)

        report = timer.get_report()
        assert report["stage_a"]["mean_sec"] == 1.75
        assert report["stage_a"]["n_runs"] == 2
        assert report["stage_b"]["mean_sec"] == 3.0

    def test_reset(self):
        from backend.ai.video_3m.evaluation.benchmark_timer import PipelineTimer

        timer = PipelineTimer()
        timer.record("x", 1.0)
        timer.reset()

        assert timer.get_total_time() == 0.0
        assert len(timer.get_results()) == 0


# ---------------------------------------------------------------------------
# Test ReportGenerator (output file generation)
# ---------------------------------------------------------------------------

class TestReportGenerator:
    def test_export_summary_csv(self, tmp_path, sample_continuous_data, sample_seating_data):
        from backend.ai.video_3m.evaluation.evaluation_engine import FullEvaluationReport
        from backend.ai.video_3m.evaluation.metrics import EvaluationMetrics
        from backend.ai.video_3m.evaluation.report_generator import ReportGenerator

        report = FullEvaluationReport(
            total_fragments=10,
            correlations=[
                EvaluationMetrics.correlation(
                    sample_continuous_data["y_true"],
                    sample_continuous_data["y_pred"],
                    "Mindful Score",
                ),
            ],
            confusion_matrices=[
                EvaluationMetrics.confusion_matrix(
                    sample_seating_data["y_true"],
                    sample_seating_data["y_pred"],
                    "Seating",
                    ["rows", "groups", "circle"],
                ),
            ],
        )

        gen = ReportGenerator(str(tmp_path))
        csv_path = str(tmp_path / "summary.csv")
        gen.export_summary_csv(report, csv_path)

        assert os.path.exists(csv_path)
        with open(csv_path, "r") as f:
            content = f.read()
        assert "Mindful Score" in content
        assert "Seating" in content


import os
