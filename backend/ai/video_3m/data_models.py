"""
Shared data classes (dataclasses) for the 3M Video Analysis pipeline.
All detectors and engines communicate through these typed contracts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Video Processing
# ---------------------------------------------------------------------------

@dataclass
class VideoFragment:
    index: int
    path: str
    start_sec: float
    end_sec: float
    duration_sec: float


@dataclass
class VideoMetadata:
    duration_sec: float
    fps: float
    width: int
    height: int
    total_fragments: int


# ---------------------------------------------------------------------------
# Mindful
# ---------------------------------------------------------------------------

@dataclass
class MindfulResult:
    gaze_score: float = 0.0            # 0-100
    posture_score: float = 0.0         # 0-100
    silence_quality_score: float = 0.0 # 0-100
    mindful_score: float = 0.0         # weighted composite 0-100
    gaze_on_task_ratio: float = 0.0    # fraction [0,1]
    reflection_periods: List[Tuple[float, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Meaningful
# ---------------------------------------------------------------------------

@dataclass
class SeatingEvent:
    timestamp_sec: float
    formation: str  # "rows" | "circle" | "groups"


@dataclass
class TalkTimeRatio:
    teacher_pct: float = 0.0
    student_pct: float = 0.0
    silence_pct: float = 0.0
    meets_standard: bool = False
    deviation: float = 0.0


@dataclass
class MovementResult:
    active_zone_ratio: float = 0.0   # fraction [0,1]
    teacher_movement_score: float = 0.0  # 0-100


@dataclass
class MeaningfulResult:
    seating_score: float = 0.0
    teacher_movement_score: float = 0.0
    talk_time_score: float = 0.0
    question_type_score: float = 0.0
    meaningful_score: float = 0.0
    seating_formations: List[SeatingEvent] = field(default_factory=list)
    active_zone_ratio: float = 0.0
    talk_time_ratio: Optional[TalkTimeRatio] = None
    discussion_groups_count: int = 0   # number of detected student clusters


# ---------------------------------------------------------------------------
# Joyful
# ---------------------------------------------------------------------------

@dataclass
class ExpressionResult:
    positive_expression_ratio: float = 0.0  # [0,1]
    expression_score: float = 0.0           # 0-100
    aha_moments: List[float] = field(default_factory=list)  # timestamps


@dataclass
class HeatmapResult:
    grid: List[List[float]] = field(default_factory=list)  # 20x15 density grid
    collaboration_score: float = 0.0
    clusters: List[dict] = field(default_factory=list)


@dataclass
class JoyfulResult:
    expression_score: float = 0.0
    acoustic_score: float = 0.0
    collaboration_score: float = 0.0
    risk_taking_score: float = 0.0
    joyful_score: float = 0.0
    heatmap_data: List[List[float]] = field(default_factory=list)
    aha_moments: List[float] = field(default_factory=list)
    laughter_events: List[float] = field(default_factory=list)
    applause_events: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Audio Engine
# ---------------------------------------------------------------------------

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # assigned after diarization


@dataclass
class TranscriptResult:
    segments: List[TranscriptSegment] = field(default_factory=list)
    full_text: str = ""
    language: str = "id"


@dataclass
class DiarizationSegment:
    start: float
    end: float
    speaker: str  # e.g. "SPEAKER_00"


@dataclass
class DiarizationResult:
    segments: List[DiarizationSegment] = field(default_factory=list)
    teacher_speaker: Optional[str] = None  # identified teacher speaker label


@dataclass
class NLPResult:
    prompting_count: int = 0
    command_count: int = 0
    question_type_score: float = 0.0  # 0-100
    detected_prompting: List[str] = field(default_factory=list)
    detected_commands: List[str] = field(default_factory=list)


@dataclass
class AcousticResult:
    energy_level: float = 0.0          # normalized [0,1]
    acoustic_score: float = 0.0        # 0-100
    laughter_events: List[float] = field(default_factory=list)
    applause_events: List[float] = field(default_factory=list)
    laughter_frequency: float = 0.0    # events per minute
    applause_frequency: float = 0.0


@dataclass
class AudioResult:
    transcript: Optional[TranscriptResult] = None
    diarization: Optional[DiarizationResult] = None
    nlp: Optional[NLPResult] = None
    acoustic: Optional[AcousticResult] = None
    talk_time: Optional[TalkTimeRatio] = None


# ---------------------------------------------------------------------------
# Fragment & Aggregation
# ---------------------------------------------------------------------------

@dataclass
class FragmentAnalysis:
    fragment: VideoFragment
    mindful: MindfulResult
    meaningful: MeaningfulResult
    joyful: JoyfulResult


@dataclass
class AggregatedResult:
    # Composite 3M scores
    mindful_score: float = 0.0
    meaningful_score: float = 0.0
    joyful_score: float = 0.0
    overall_3m_score: float = 0.0

    # Mindful sub-scores
    gaze_score: float = 0.0
    posture_score: float = 0.0
    silence_quality_score: float = 0.0

    # Meaningful sub-scores
    seating_score: float = 0.0
    talk_time_score: float = 0.0
    question_type_score: float = 0.0
    teacher_movement_score: float = 0.0

    # Joyful sub-scores
    expression_score: float = 0.0
    acoustic_score: float = 0.0
    collaboration_score: float = 0.0
    risk_taking_score: float = 0.0

    # Talk-time breakdown
    teacher_talk_pct: float = 0.0
    student_talk_pct: float = 0.0
    silence_pct: float = 0.0
    meets_dl_standard: bool = False
    active_zone_ratio: float = 0.0

    # Timeline & events
    timeline_data: List[dict] = field(default_factory=list)
    heatmap_data: List[List[float]] = field(default_factory=list)
    aha_moments: List[float] = field(default_factory=list)
    laughter_events: List[float] = field(default_factory=list)
    applause_events: List[float] = field(default_factory=list)
    seating_transitions: List[dict] = field(default_factory=list)

    # Video metadata
    video_duration_sec: float = 0.0
    total_fragments: int = 0
    discussion_groups_count: int = 0   # max detected discussion groups


# ---------------------------------------------------------------------------
# Triangulation
# ---------------------------------------------------------------------------

@dataclass
class PlannedActivity:
    activity_type: str   # "group_discussion" | "mindful_reflection" | etc.
    description: str
    planned_duration_min: Optional[float] = None


@dataclass
class LessonPlan:
    activities: List[PlannedActivity] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class TriangulationItem:
    activity: str
    planned: bool
    detected: bool
    status: str          # "success" | "misalignment" | "not_detected"
    evidence: str = ""
    recommendation: str = ""


@dataclass
class TriangulationResult:
    items: List[TriangulationItem] = field(default_factory=list)
    alignment_score: float = 0.0


# ---------------------------------------------------------------------------
# Evidence Clips
# ---------------------------------------------------------------------------

@dataclass
class EvidenceClipData:
    clip_path: str
    clip_name: str
    start_sec: float
    end_sec: float
    clip_type: str    # "best_practice" | "improvement"
    aspect: str       # "mindful" | "meaningful" | "joyful"
    description: str
    score: float
    job_id: str = ""
