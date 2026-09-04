"""
Ground Truth Annotation models for 3M Pipeline evaluation.

Stores human observer annotations for validation against CV pipeline outputs.
Used to compute confusion matrices, correlation metrics, and inter-rater reliability
for the research paper.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class GroundTruthAnnotation(Base):
    """
    Per-fragment ground truth annotation by a human observer.
    
    Each row corresponds to ONE fragment of ONE video, labeled by ONE observer.
    Multiple observers can annotate the same fragment to measure inter-rater
    reliability (Cohen's Kappa / ICC).
    """
    __tablename__ = "ground_truth_annotations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        String(64),
        ForeignKey("video_analysis_jobs.job_id"),
        index=True,
        nullable=False,
    )
    fragment_index = Column(Integer, nullable=False)
    annotator_name = Column(String(128), nullable=False)  # e.g. "Observer A"

    # ── Mindful Ground Truth ────────────────────────────────────────────
    # Fraction of students visually on-task (looking at teacher/board/task)
    gaze_on_task_ratio = Column(Float, nullable=True)        # [0.0 – 1.0]
    # Fraction of students with engaged posture (upright/leaning forward)
    posture_engaged_ratio = Column(Float, nullable=True)     # [0.0 – 1.0]
    # Observer's overall mindful score for this fragment
    mindful_score_gt = Column(Float, nullable=True)          # [0 – 100]

    # ── Meaningful Ground Truth ─────────────────────────────────────────
    # Dominant seating formation observed
    seating_formation = Column(String(32), nullable=True)    # "rows"|"groups"|"circle"
    # Was teacher moving among students? (in "active zone")
    teacher_in_active_zone = Column(Boolean, nullable=True)
    # Observer's estimate of teacher talk percentage
    teacher_talk_pct_gt = Column(Float, nullable=True)       # [0 – 100]
    # Observer's overall meaningful score for this fragment
    meaningful_score_gt = Column(Float, nullable=True)       # [0 – 100]

    # ── Joyful Ground Truth ─────────────────────────────────────────────
    # Fraction of students showing positive expressions (smiling, laughing)
    positive_expression_ratio = Column(Float, nullable=True) # [0.0 – 1.0]
    # Number of hand-raises observed in this fragment
    hand_raise_count = Column(Integer, nullable=True)
    # Observer's overall joyful score for this fragment
    joyful_score_gt = Column(Float, nullable=True)           # [0 – 100]

    # ── Overall Observer Assessment ─────────────────────────────────────
    overall_focus_score = Column(Float, nullable=True)       # [0 – 100]
    overall_comfort_score = Column(Float, nullable=True)     # [0 – 100]
    overall_3m_score_gt = Column(Float, nullable=True)       # [0 – 100]

    # Optional free-text notes by observer
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    job = relationship("VideoAnalysisJob")


class EvaluationReport(Base):
    """
    Stores computed evaluation metrics for a single benchmark run.
    """
    __tablename__ = "evaluation_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        String(64),
        ForeignKey("video_analysis_jobs.job_id"),
        index=True,
        nullable=True,
    )
    # If null, this is a batch evaluation across multiple jobs
    report_type = Column(String(32), default="single")  # "single" | "batch"

    # Discrete classification metrics (JSON)
    confusion_matrices = Column(JSON, nullable=True)
    classification_reports = Column(JSON, nullable=True)

    # Continuous correlation metrics (JSON)
    correlation_metrics = Column(JSON, nullable=True)

    # Inter-rater reliability (JSON)
    inter_rater_metrics = Column(JSON, nullable=True)

    # Processing time benchmark (JSON)
    processing_times = Column(JSON, nullable=True)

    # Summary statistics
    total_fragments_evaluated = Column(Integer, default=0)
    total_annotators = Column(Integer, default=0)

    # Full report data (JSON blob)
    full_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
