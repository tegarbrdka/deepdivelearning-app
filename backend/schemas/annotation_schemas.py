"""
Pydantic schemas for ground truth annotation API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Input Schemas ─────────────────────────────────────────────────────────────

class AnnotationCreate(BaseModel):
    """Create a single ground truth annotation for one fragment."""
    job_id: str
    fragment_index: int = Field(ge=0)
    annotator_name: str = Field(min_length=1, max_length=128)

    # Mindful
    gaze_on_task_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    posture_engaged_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    mindful_score_gt: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Meaningful
    seating_formation: Optional[str] = Field(None, pattern=r"^(rows|groups|circle)$")
    teacher_in_active_zone: Optional[bool] = None
    teacher_talk_pct_gt: Optional[float] = Field(None, ge=0.0, le=100.0)
    meaningful_score_gt: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Joyful
    positive_expression_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    hand_raise_count: Optional[int] = Field(None, ge=0)
    joyful_score_gt: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Overall
    overall_focus_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overall_comfort_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overall_3m_score_gt: Optional[float] = Field(None, ge=0.0, le=100.0)

    notes: Optional[str] = None


class BulkAnnotationUpload(BaseModel):
    """Upload multiple annotations at once (from JSON)."""
    annotations: List[AnnotationCreate]


# ── Response Schemas ──────────────────────────────────────────────────────────

class AnnotationResponse(BaseModel):
    id: int
    job_id: str
    fragment_index: int
    annotator_name: str

    gaze_on_task_ratio: Optional[float] = None
    posture_engaged_ratio: Optional[float] = None
    mindful_score_gt: Optional[float] = None

    seating_formation: Optional[str] = None
    teacher_in_active_zone: Optional[bool] = None
    teacher_talk_pct_gt: Optional[float] = None
    meaningful_score_gt: Optional[float] = None

    positive_expression_ratio: Optional[float] = None
    hand_raise_count: Optional[int] = None
    joyful_score_gt: Optional[float] = None

    overall_focus_score: Optional[float] = None
    overall_comfort_score: Optional[float] = None
    overall_3m_score_gt: Optional[float] = None

    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnnotationsListResponse(BaseModel):
    job_id: str
    total: int
    annotations: List[AnnotationResponse]


# ── Evaluation Report Schemas ─────────────────────────────────────────────────

class ConfusionMatrixItem(BaseModel):
    component: str  # e.g. "seating_formation", "gaze_on_task"
    labels: List[str]
    matrix: List[List[int]]
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cohen_kappa: float


class CorrelationItem(BaseModel):
    component: str  # e.g. "mindful_score", "gaze_score"
    pearson_r: float
    pearson_p: float
    spearman_rho: float
    spearman_p: float
    mae: float
    rmse: float
    n_samples: int


class ProcessingTimeItem(BaseModel):
    stage: str
    mean_sec: float
    std_sec: float
    min_sec: float
    max_sec: float


class EvaluationReportResponse(BaseModel):
    job_id: Optional[str] = None
    report_type: str = "single"
    total_fragments: int = 0
    total_annotators: int = 0

    confusion_matrices: List[ConfusionMatrixItem] = []
    correlations: List[CorrelationItem] = []
    processing_times: List[ProcessingTimeItem] = []

    # Summary
    overall_agreement_kappa: Optional[float] = None
    mean_correlation: Optional[float] = None

    created_at: Optional[datetime] = None
