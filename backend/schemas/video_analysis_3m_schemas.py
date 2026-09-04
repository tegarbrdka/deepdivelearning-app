"""
Pydantic schemas for the 3M Video Analysis API.
"""
from __future__ import annotations
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Upload / Job
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_duration_min: float
    rpp_uploaded: bool


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: Optional[str] = None
    progress: float
    video_name: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

class MindfulSubScores(BaseModel):
    gaze_score: float
    posture_score: float
    silence_quality_score: float


class MeaningfulSubScores(BaseModel):
    seating_score: float
    talk_time_score: float
    question_type_score: float
    teacher_movement_score: float


class JoyfulSubScores(BaseModel):
    expression_score: float
    acoustic_score: float
    collaboration_score: float
    risk_taking_score: float


class ScoresResponse(BaseModel):
    mindful: float
    meaningful: float
    joyful: float
    overall: float
    mindful_sub: MindfulSubScores
    meaningful_sub: MeaningfulSubScores
    joyful_sub: JoyfulSubScores


class TalkTimeResponse(BaseModel):
    teacher_pct: float
    student_pct: float
    silence_pct: float
    meets_dl_standard: bool
    deviation: float


# ---------------------------------------------------------------------------
# Full result
# ---------------------------------------------------------------------------

class AnalysisResultResponse(BaseModel):
    job_id: str
    video_name: Optional[str] = None
    scores: ScoresResponse
    talk_time: TalkTimeResponse
    recommendations: List[dict]
    has_triangulation: bool
    created_at: Optional[datetime] = None
    aha_moments: List[float] = []
    laughter_events: List[float] = []
    applause_events: List[float] = []
    seating_transitions: List[dict] = []

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineFragmentResponse(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    label: str
    mindful: float
    meaningful: float
    joyful: float
    seating_formation: Optional[str] = None
    active_zone_ratio: Optional[float] = None
    teacher_talk_pct: Optional[float] = None
    student_talk_pct: Optional[float] = None


class TimelineResponse(BaseModel):
    job_id: str
    fragments: List[TimelineFragmentResponse]


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

class HeatmapResponse(BaseModel):
    job_id: str
    grid_width: int
    grid_height: int
    heatmap: List[List[float]]
    clusters: List[dict]
    discussion_groups_count: int = 0


# ---------------------------------------------------------------------------
# Evidence clips
# ---------------------------------------------------------------------------

class EvidenceClipResponse(BaseModel):
    id: int
    clip_name: Optional[str] = None
    clip_url: str
    start_sec: float
    end_sec: float
    clip_type: str
    aspect: str
    description: Optional[str] = None
    score: float

    class Config:
        from_attributes = True


class EvidenceClipsResponse(BaseModel):
    job_id: str
    clips: List[EvidenceClipResponse]


# ---------------------------------------------------------------------------
# Triangulation
# ---------------------------------------------------------------------------

class TriangulationItemResponse(BaseModel):
    activity: str
    planned: bool
    detected: bool
    status: str
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


class TriangulationResponse(BaseModel):
    job_id: str
    alignment_score: float
    items: List[TriangulationItemResponse]


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class HistoryItemResponse(BaseModel):
    job_id: str
    video_name: Optional[str] = None
    status: str
    mindful_score: Optional[float] = None
    meaningful_score: Optional[float] = None
    joyful_score: Optional[float] = None
    overall_3m_score: Optional[float] = None
    teacher_talk_pct: Optional[float] = None
    student_talk_pct: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[HistoryItemResponse]


# ---------------------------------------------------------------------------
# Lesson plan upload
# ---------------------------------------------------------------------------

class PlannedActivityResponse(BaseModel):
    activity_type: str
    description: str
    planned_duration_min: Optional[float] = None


class LessonPlanUploadResponse(BaseModel):
    lesson_plan_id: int
    file_name: str
    activities: List[PlannedActivityResponse]
